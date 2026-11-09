// EP01 full episode, PART 1 (s01-s24, 0-26.55 s): the rule, the world montage, Grandpa, the flashback lap.
// Owner of the builder keys listed in episodes/ep01/timeline.json `parts[0].builders_owned` (board: episodes/ep01/board.md).
//
// The first six builders below are the APPROVED 5-second test, moved here unchanged from engine/episodes/ep01_test5.js
// (sky_to_street, porch_couple, grandma_cu, poof_swing, gnome_hero, lawn_stare). Only these lines differ from that file:
// the import paths (one folder deeper), the removed top-level fetch of test5_timeline.json, and evT(), which reads the
// frame rate from ctx.fps instead of the test timeline (both are 60). Their params in timeline.json are the test's params.
// Do not change these six builders without the owner's approval; add new builders to BUILDERS below them.
//
// NEW_BUILDERS (below the approved six) holds the rest of part 1: grandma_armchair, glasses_dawn, agent_board, keepoff_sign,
// nextdoor_plastic, kennel_hole, gate_bonk, family_hands, hero_taps_hat, goodnight_window, gnome_blink_night,
// fb_grandpa_walk, fb_flashlight, fb_slippers, fb_lap (these three also render part 4's callbacks s61-s63, params.callback_of),
// fb_wink, fb_big_ones. Per-shot deviations from the board numbers are commented at each builder.
// Every builder: { build(ctx), update(ctx, t), quality? } - pure functions of t, seeded, no Math.random (engine/README.md).
import * as THREE from 'three';
import * as sets from '../../kit/sets.js';
import * as K from '../../kit/chars.js';
import { makeRng, hash32 } from '../../core/random.js';
import { springStep } from '../../core/anim.js';
// Kits for the builders written after the approved six (s06-s08, s10-s24); the approved builders do not use them.
import * as C from './common.js';
import * as SE from '../../kit/sets_ep01.js';
import * as I from '../../kit/interiors.js';
import * as X from '../../kit/fx_ep01.js';
import * as CR from '../../kit/creatures.js';

const S = sets.STUD;                 // 1 stud = 0.32 m
const DEG = Math.PI / 180;
const V3 = (a) => new THREE.Vector3(a[0], a[1], a[2]);
const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
const smooth = (x) => { const u = clamp01(x); return u * u * (3 - 2 * u); };
const outExpo = (x) => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * clamp01(x)));
const outQuad = (x) => 1 - (1 - clamp01(x)) * (1 - clamp01(x));
// Event time inside a shot (seconds from the shot start), from the timeline's events[] (episode seconds).
const evT = (ctx, word) => { const e = (ctx.params.events || []).find((x) => x.word === word); return e ? e.frame / ctx.fps - ctx.shot.f0 / ctx.fps : null; };
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

// =====================================================================================================================
// PART 1, the rest (s06-s08, s10-s24): the world montage, Grandpa, the goodnight blink, the sepia flashback lap.
// Every number comes from the shot's timeline params (camera block, events with frames, cast faces); the look follows
// the approved six (warm keys on faces, TF sparkles in night shots, the bible's grade presets). Pure functions of t.
// =====================================================================================================================
const Y_AX = new THREE.Vector3(0, 1, 0);
const ev = (ctx, k, fb = null) => C.evT(ctx, k, fb);
const W3 = (p) => (p.isVector3 ? p.clone() : new THREE.Vector3(p[0], p[1] ?? 0, p[2]));
const hflat = (v) => { const o = v.clone(); o.y = 0; return o.normalize(); };
const yawOf = (d) => Math.atan2(d.x, d.z);   // rotation.y that turns an object's +z onto the horizontal direction d
const lerp = (a, b, k) => a + (b - a) * k;
const outBack = (x, s = 1.7) => { const u = clamp01(x) - 1; return 1 + (s + 1) * u * u * u + s * u * u; };
const sparks = (ctx, center, size, count, seed, o = {}) => { const s = sets.sparkles(ctx, { ...SPARK, center: W3(center).toArray(), size, count, seed, ...o }); ctx.add(s); return s; };
const faceOf = (ctx, i = 0, fb = 'content') => { const c = ctx.params.cast && ctx.params.cast[i]; const f = c && c.face; return f ? String(f).split(/\s*->\s*/) : [fb]; };
// Camera from a shot's board numbers around `subject` (metres): `base` = horizontal direction from the subject to a yaw-0
// camera, yaw (deg) turns it about +Y; dist (studs, horizontal), height (studs above `ground`, metres), pitch (deg, + up).
// aimY (metres) overrides the pitch: the target sits at the subject at that height.
function boardCam(subject, c, { base = [0, 0, 1], ground = 0, aimY = null, fov = null } = {}) {
  const b = hflat(W3(base)).applyAxisAngle(Y_AX, (c.yaw_deg || 0) * DEG); const s = W3(subject);
  const pos = new THREE.Vector3(s.x, 0, s.z).addScaledVector(b, c.dist_studs * S); pos.y = ground + c.height_studs * S;
  const tgt = new THREE.Vector3(s.x, 0, s.z); tgt.y = aimY ?? pos.y + c.dist_studs * S * Math.tan((c.pitch_deg || 0) * DEG);
  return { pos: pos.toArray(), target: tgt.toArray(), fov: fov ?? c.fov ?? 70 };
}
// A soft warm key from the camera's upper front-left onto a face (bible rule 10 / test review defect 2).
function faceKey(ctx, at, { cd = 2.4, color = '#ffc49a', d = 0.9 } = {}) {
  const B = sets.camBasis(ctx); const p = W3(at).addScaledVector(B.fwd, -0.75 * d).addScaledVector(B.right, -0.6 * d).add(new THREE.Vector3(0, 0.6 * d, 0));
  return ctx.add(ctx.lights.point({ color, intensity: cd, pos: p.toArray(), decay: 2 }));
}
// Solve one arm angle so the hand reaches target.y, then slide the avatar in xz so the hand lands on the target.
function reachTo(av, side, pose, key, target, { lo = -30, hi = 175, move = true } = {}) {
  const T = W3(target); const hs = K.handSocket(av, side); const hand = () => { K.setPose(av, pose); av.updateMatrixWorld(true); return hs.getWorldPosition(new THREE.Vector3()); };
  for (let i = 0; i < 26; i++) { const m = (lo + hi) / 2; pose[key] = m; const h = hand(); if (h.y > T.y) hi = m; else lo = m; }
  pose[key] = (lo + hi) / 2; const h = hand(); if (move) { av.position.x += T.x - h.x; av.position.z += T.z - h.z; av.updateMatrixWorld(true); }
  return pose[key];
}
// Rotate a group about a pivot (group-local coordinates of its parent) by Euler angles.
function pivotRot(g, pivot, rx, ry, rz) { g.rotation.set(rx, ry, rz); const p = pivot.clone(); g.position.copy(pivot).sub(p.applyEuler(g.rotation)); }
// A sepia flashback night on our 2010s lawn (s19-s24 and part 4's callbacks): the night lawn preset, then the sepia grade.
function sepiaLight(ctx, H, o = {}) {
  const rig = H.ep01.light(ctx, { skyPreset: GALAXY_LOW, skyOpts: { intensity: 1.4 }, window: { n: 2, cd: 2.4, color: '#ffd9a0', maxD: 14 }, ...o });
  ctx.post.set(sets.postPreset('sepia', { exposure: o.exposure ?? 1.12 })); return rig;
}
// Grandma's knitting (s06/s07): a pink swatch on two needles and a lilac yarn ball (studs).
function knitting(ctx) {
  return ctx.cache('ep01p1:knitting', () => {
    const P = new sets.Parts();
    P.box('plastic:#e46a8f', 1.15, 0.14, 0.8, [0, 0.07, 0], null, { bevel: 0.05 }); for (let i = 0; i < 4; i++) P.box('plastic:#c84a72', 1.12, 0.03, 0.06, [0, 0.15, -0.3 + i * 0.2]);
    for (const s of [-1, 1]) P.bar('metal:#c9c4cc', [s * 0.15, 0.16, -0.25], [s * 0.15 + 0.9 * s, 0.32, 0.55], 0.05, 0.05);
    P.add('plastic:#9a6ad0', new THREE.SphereGeometry(0.34, 16, 12), [0.85, 0.3, -0.2]); P.bar('plastic:#9a6ad0', [0.6, 0.2, -0.15], [0.3, 0.16, 0.0], 0.04, 0.04);
    return studWrap(P.build(sets.M, { name: 'knitting', receive: true }));
  }).clone(true);
}
// A KEEP OFF THE LAWN AFTER DARK post sign (studs prop, metres wrapper), sized per shot.
function keepOffSign(ctx, { postH = 5.2, w = 4.4, h = 3.0 } = {}) {
  return ctx.cache('ep01p1:keepoff:' + [postH, w, h].join(','), () => { const P = new sets.Parts(); const b = sets.props.addPostSign(P, { lines: ['KEEP OFF', 'THE LAWN', 'AFTER DARK'], w, h, postH }); const g = P.build(sets.M, { name: 'keepOffPosts', cast: true, receive: true }); const r = new THREE.Group(); r.add(g, b); return studWrap(r); }).clone(true);
}
// Grandpa's worn lap path (s22/s63): a flattened-grass loop with a kink toward the house under `kink` (lot-plane metres).
function lapTexture(ctx, key, pts) {
  return ctx.cache('ep01p1:lapTex:' + key, () => {
    const N = 1024, c = document.createElement('canvas'); c.width = c.height = N; const g = c.getContext('2d'); g.clearRect(0, 0, N, N);
    g.lineCap = g.lineJoin = 'round';
    const path = () => { g.beginPath(); pts.forEach(([u, v], i) => (i ? g.lineTo(u * N, v * N) : g.moveTo(u * N, v * N))); g.closePath(); };
    g.strokeStyle = 'rgba(214,226,150,0.42)'; g.lineWidth = 46; path(); g.stroke();      // flattened blades: paler, sheen
    g.strokeStyle = 'rgba(240,248,190,0.30)'; g.lineWidth = 22; path(); g.stroke();
    const r = makeRng(hash32('ep01p1', 'lapStreaks')); g.strokeStyle = 'rgba(70,90,40,0.25)'; g.lineWidth = 2;   // combed streaks along the loop
    for (let i = 0; i < pts.length; i++) { const [u0, v0] = pts[i], [u1, v1] = pts[(i + 1) % pts.length]; for (let k = 0; k < 3; k++) { const o = (r() - 0.5) * 30; g.beginPath(); g.moveTo(u0 * N + o, v0 * N + o * 0.3); g.lineTo(u1 * N + o, v1 * N + o * 0.3); g.stroke(); } }
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; t.userData.persistent = true; return t;
  });
}

const NEW_BUILDERS = {
  // s06 "First, your grandma gets" / s07 "shorter." - Grandma's rose wingback armchair, day interior, MS at the seated head
  // (h 3.6, d 7.5, yaw -15, pitch -4: the room's armchairMS view). s07 is the jump cut on the same set-up: grandmaShort
  // (x0.8, sleeves over her hands), feet dangling off the rug, face wonder; her knitting has slid down onto the rug.
  grandma_armchair: {
    build(ctx) {
      const p = ctx.params; const short = p.phase === 'short';
      const R = I.grandmaRoom(ctx); ctx.add(R); const A = R.userData.anchors;
      const gm = K.makeCharacter(short ? 'grandmaShort' : 'grandma', { face: faceOf(ctx, 0, short ? 'wonder' : 'content')[0] }); cleanGlasses(gm);
      gm.position.set(A.seat[0], A.seat[1] - 1.5 * S + (short ? K.seatOffset(gm, 1.5) : 0), A.seat[2] + (short ? -0.12 * S : 0)); gm.rotation.y = A.seatYaw || 0;
      const pose = short ? { ...K.CAST_POSES.sitDangle, bodyX: -6, neckX: 8, neckZ: -4 } : { ...K.POSES.sit, armLx: 52, armRx: 52, armLz: -14, armRz: -14, neckX: -6, neckY: 4 };
      K.setPose(gm, pose); ctx.add(gm);
      const kn = knitting(ctx);
      if (!short) { const body = gm.getObjectByName('body'); body.add(kn); kn.scale.setScalar(1); kn.position.set(0, 2.55, 1.05); kn.rotation.set(0.05, 0.2, 0); }
      else { kn.position.set(A.rug[0] + 0.55 * S, A.rug[1] - 0.06, A.rug[2] - 0.6 * S); kn.rotation.set(0, -0.5, 0.02); ctx.add(kn); }
      ctx.camera.set(R.userData.views.armchairMS).push(p.camera.move.Z);
      if (p.camera.drift && p.camera.drift.crane_studs) ctx.camera.crane(p.camera.drift.crane_studs * S);
      ctx.shared.rig = I.interiorDay(ctx, { room: R });
      faceKey(ctx, [A.seat[0], A.seat[1] + 2.6 * S, A.seat[2] + 0.2], { cd: 1.2, color: '#ffd8b8', d: 1.2 });
      // low warm fill from the lens side at lap height: the plum skirt / leg fronts face the lens and read as black boxes
      // under the window key from above (test review defect 3); the lamp-warm fill keeps them plum
      { const v = R.userData.views.armchairMS; const cp = W3(v.pos), st = W3(A.seat); const fp = st.clone().lerp(cp, 0.55); fp.y = st.y + 0.1; fp.addScaledVector(hflat(cp.clone().sub(st)).applyAxisAngle(Y_AX, Math.PI / 2), -0.35);
        ctx.add(ctx.lights.point({ color: '#ffd6bc', intensity: short ? 2.2 : 2.6, pos: fp.toArray(), decay: 2 })); }
      ctx.shared.gm = gm; ctx.shared.pose = pose;
    },
    update(ctx, t) { K.setPose(ctx.shared.gm, { ...ctx.shared.pose, ...K.breath(t) }); },
  },

  // s08 "One morning, a gnome is wearing her glasses." - pink dawn on Grandma's lawn (the porch couple's bungalow): the
  // Grandma gnome stands new by the path, facing her house, round glasses tilted 8 deg; the grandkid kneels at her side,
  // reaches from 6.30 (0.3 s) and on "glasses" straightens them (8 frames outBack) + the s03 star glint on the lens.
  // Camera from her front (between her and the house), 25 deg round, high 18 deg down, the sunrise sky across the street.
  glasses_dawn: {
    quality: { shadows: 'pcfsoft' },
    build(ctx) {
      const p = ctx.params; const c = p.camera;
      const set = sets.buildLot(ctx, { seed: 'ep01', hero: { house: PORCH_HOUSE, closeup: true } }); ctx.add(set);
      const L = set.userData.lots.find((l) => l.hero); const gate = W3(L.gate), steps = W3(L.steps);
      const toHouse = hflat(steps.clone().sub(gate)); const side = new THREE.Vector3(-toHouse.z, 0, toHouse.x);
      const gp = gate.clone().addScaledVector(toHouse, 3.0 * S).addScaledVector(side, -2.4 * S); gp.y = 0;
      // scale cheated x1.35 (bible 2.6 #6): she is the subject of an MS at 6 studs, the kneeling kid must not dwarf her
      const g = K.makeGnome('grandma', { lantern: false, wear: 0.05 }); g.scale.multiplyScalar(1.35); g.position.copy(gp); g.rotation.y = yawOf(toHouse); ctx.add(g); softenBeard(g);
      ctx.add(sets.contactShadow(ctx, { pos: gp.toArray(), radius: 0.34, opacity: 0.4 }));
      // the glasses: tilt pivot = the bridge between the two rims (head-local), 8 deg until the event
      const gl = g.getObjectByName('gnomeGlasses'); const rims = gl.children.filter((m) => m.geometry && m.geometry.type === 'TorusGeometry');
      const piv = rims.reduce((a, m) => a.add(m.position), new THREE.Vector3()).multiplyScalar(1 / rims.length); ctx.shared.gl = { g: gl, piv };
      g.updateWorldMatrix(true, true); const eyes = eyesOf(g);
      // camera: from her front, yaw 25 toward the path side, high (h 4.5, d 6, about 18 deg down), aimed just over her
      // hat so her face sits a little under the centre and the kneeling kid's head in the upper third
      const cam = boardCam(gp, c, { base: toHouse.toArray().map((v, i) => (i === 1 ? 0 : v)), aimY: eyes.y + 0.75 * S }); const camBase = { ...cam };
      ctx.camera.set(cam).push(c.move.Z).crane((c.drift?.crane_studs ?? 0) * S).rollBy(c.roll ? c.roll.deg[1] - c.roll.deg[0] : 0);
      const camP = W3(cam.pos); const toCam = hflat(camP.clone().sub(gp)); const camSide = Math.sign(toCam.dot(side)) || 1;
      // the grandkid kneels BESIDE her on screen-left (same depth, 2.5 studs off the sight line), turned to her; his
      // near arm (armR) reaches across to the glasses
      const kid = K.makeCharacter('grandkid', { face: faceOf(ctx, 1, 'content')[0] }); ctx.add(kid);
      const fwd = toCam.clone().negate(); const scrR = new THREE.Vector3(-fwd.z, 0, fwd.x); void camSide;
      kid.position.copy(gp).addScaledVector(scrR, -2.5 * S).addScaledVector(fwd, 0.35 * S); kid.position.y = 0;
      kid.rotation.y = yawOf(gp.clone().sub(kid.position));
      const lensW = gl.localToWorld(piv.clone()); const reachPt = lensW.clone().addScaledVector(hflat(kid.position.clone().sub(gp)), 0.06 * S);
      const pReach = { bodyX: 10, legLx: -90, legRx: -90, lift: -1.45, armLx: 26, armLz: -6, armRz: -8, neckX: -12, neckY: -18, armRx: 60 };   // head turned a little to the lens so his ^^ face reads
      reachTo(kid, 'R', pReach, 'armRx', reachPt, { lo: 10, hi: 150 });
      // re-aim a third of the way toward the kid (after the reach solve placed him) so his head is inside the frame
      { const tg = W3(camBase.target), kh = kid.position.clone(); kh.y = tg.y; const t2 = tg.clone().lerp(kh, 0.32); ctx.camera.set({ target: t2.toArray() }); }
      const pRest = { ...pReach, armRx: 22, armRz: -4 };
      ctx.shared.kid = kid; ctx.shared.kp = { pRest, pReach, t0: (6.30 * ctx.fps - ctx.shot.f0) / ctx.fps };
      // light: P4 dawn, sun low from across the street (rims + long shadows), warm fill on the faces
      ctx.shared.rig = sets.dawn(ctx, { set, sun: { az: 168, el: 10 }, hemiIntensity: 1.25, postOpts: { exposure: 2.05, grade: { tint: 12, highlights: '#ffdcd0', highlightsAmount: 0.25 } } });
      faceKey(ctx, eyes.clone().add(new THREE.Vector3(0, 0.1, 0)), { cd: 2.2, color: '#ffd7b8', d: 1.1 });
      ctx.shared.te = ev(ctx, 'glasses', 1.567);
      const lensNear = rims.map((m) => gl.localToWorld(m.position.clone())).sort((a, b) => a.distanceTo(camP) - b.distanceTo(camP))[0];
      ctx.shared.glint = starGlint(ctx, { pos: lensNear, t0: ctx.shared.te, peak: 120, rot: 25, color: '#fff4e4' }); ctx.add(ctx.shared.glint);
      // dew: small warm glints in the grass between her and the lens, and the TF air
      ctx.shared.dew = sparks(ctx, gp.clone().lerp(camP, 0.35).setY(0.06), [2.2, 0.08, 1.4], 12, 's08dew', { px: [16, 34], colors: ['#fff6e8', '#ffe6c8', '#ffffff'], drift: [0.005, 0.015], brightness: 1.7 });
      ctx.shared.fx = sparks(ctx, eyes.clone().lerp(camP, 0.4), [1.6, 1.0, 0.8], 5, 's08', { colors: ['#fff2e0', '#ffe2c4', '#f4e6ff'] });
      ctx.shared.g = g;
    },
    update(ctx, t) {
      const s = ctx.shared; K.gnomeIdle(s.g, t, { seed: 'gmGnome', amp: 0.4 });
      const u = (t - s.te) * 60 / 8; const tilt = 8 * DEG * (u <= 0 ? 1 : 1 - outBack(u, 2.2));
      pivotRot(s.gl.g, s.gl.piv, 0, 0, tilt);
      const k = smooth((t - s.kp.t0) / 0.3); const nudge = t > s.te ? 3 * Math.exp(-(t - s.te) * 9) * Math.sin((t - s.te) * 30) : 0;
      const P = {}; for (const key of Object.keys(s.kp.pReach)) P[key] = lerp(s.kp.pRest[key] ?? 0, s.kp.pReach[key], k); P.armRz += nudge;
      K.setPose(s.kid, P);
      s.glint.update(t); s.dew.update(t); s.fx.update(t);
    },
  },

  // s10 "Houses here come with ancestors." - our house by day: the agent board by the path, two family gnomes posing either
  // side of it like agents (turned 20 deg to the lens), Grandpa small in his bed behind. h 4.8, d 9, yaw 10, fov 60; the
  // target is the COMES WITH ANCESTORS line, so the +26 % push ends with it filling the centre (out of the caption band).
  agent_board: {
    quality: { shadows: 'pcfsoft' },
    build(ctx) {
      const p = ctx.params; const c = p.camera;
      const H = SE.heroLot(ctx, { tod: 'day', gnomes: ['bedFront0', 'bedFront1'] }); ctx.add(H); const sp = H.ep01.spots;   // only the bed gnomes: the two agents are the lawn's
      const B = W3(sp.board); const textY = B.y - 1.0 * S;           // board 3.1-6.1 studs; the third line sits ~1 stud under its centre
      // The board stands 4.6 studs behind the pickets, so a d-9 camera is outside the fence: it looks in through the open
      // gateway (leaf hidden), 2.6 studs out on the sidewalk, h 4.8, at the COMES WITH ANCESTORS line (yaw ~37 instead of 10).
      const G = W3(sp.gate); if (H.ep01.gate) H.ep01.gate.visible = false;
      const cam = { pos: [G.x + 1.5 * S, c.height_studs * S, G.z + 2.6 * S], target: [B.x, textY, B.z], fov: c.fov }; ctx.camera.set(cam).push(c.move.Z).truck((c.drift?.truck_studs ?? 0) * S);
      const toCam = hflat(W3(cam.pos).sub(B));
      // the two "agents" stand where the END frame (after the +26 % push) has them either side of the board, in the lower
      // third under its two bottom corners: rays through those screen points down to the lawn (no guessing in studs)
      ctx.camera.apply(0); const zEnd = 1 + c.move.Z; const onLawn = (nx, ny) => { const o = ctx.cam.position.clone(); const d = new THREE.Vector3(nx / zEnd, ny / zEnd, 0.5).unproject(ctx.cam).sub(o).normalize(); return o.addScaledVector(d, -o.y / d.y); };
      const ag = [[-1, 1, -0.4, -0.66], [1, 3, 0.5, -0.62]].map(([s, v, nx, ny]) => { const f = K.makeFamilyGnome(v, { lantern: 0, wear: 0.1 }); f.position.copy(onLawn(nx, ny)); f.position.y = 0;
        f.rotation.y = yawOf(hflat(W3(cam.pos).sub(f.position))) - s * 20 * DEG; ctx.add(f); ctx.add(sets.contactShadow(ctx, { pos: f.position.toArray(), radius: 0.26, opacity: 0.35 })); return f; });
      ctx.shared.rig = SE.heroLight(ctx, H);
      ag.forEach((f) => { f.updateWorldMatrix(true, true); });
      faceKey(ctx, eyesOf(ag[0]).lerp(eyesOf(ag[1]), 0.5), { cd: 1.5, color: '#fff0dc', d: 1.6 });
      ctx.shared.ag = ag; ctx.shared.gp = H.ep01.gnomes.grandpa;
    },
    update(ctx, t) { ctx.shared.ag.forEach((f, i) => K.gnomeIdle(f, t, { seed: 'agent' + i, amp: 0.5 })); if (ctx.shared.gp) K.gnomeIdle(ctx.shared.gp, t, { seed: 'gpDay' }); },
  },

  // s11 "You never step on a lawn after dark." - sunset street, low (h 1.6, d 7, yaw -20, pitch +6): the KEEP OFF THE LAWN
  // AFTER DARK sign in the left-centre foreground, the grandkid hopping stone to stone up a garden path toward his porch
  // (0.45 s hops), and on "dark" the lit windows' curtains snap shut, nearest first, 0.12 s apart (fx_ep01.curtainCascade).
  keepoff_sign: {
    quality: { shadows: 'pcfsoft' },
    build(ctx) {
      const p = ctx.params; const c = p.camera;
      const T = SE.ep01Street(ctx, { tod: 'dusk' }); ctx.add(T); const L = T.userData.lots.find((l) => l.id === 'A2');
      const gate = W3(L.gate), steps = W3(L.steps); const toHouse = hflat(steps.clone().sub(gate)); const side = new THREE.Vector3(-toHouse.z, 0, toHouse.x);
      // The kid hops up A2's path toward his porch: start 9 studs in (or earlier on a short path), end at the steps.
      const Ls = steps.distanceTo(gate) / S; const hops = Math.ceil(ctx.shot.duration / 0.45); const k0 = Math.max(5.5, Math.min(9.0, Ls - 1.2 - hops * 0.9));
      const HOP = 0.9; const kA = gate.clone().addScaledVector(toHouse, k0 * S).setY(1.6 * S), kB = kA.clone().addScaledVector(toHouse, hops * HOP * S);
      // Camera: low (h 1.6, pitch +6, fov 70) on A2's lawn behind the pickets. "Curtains snap shut DOWN THE STREET, window by
      // window" needs a look along the row of houses, so the board's yaw (-20 off the path, one window in view) is opened up:
      // a deterministic search over lens spots on the lawn and yaws keeps the most lit front windows (5) in the END frame (after
      // the +15 % push) with the kid in frame for the whole shot, as close as the windows allow (the board's d 7 gives one window).
      T.updateMatrixWorld(true); const sc = T.scale.x || 1; const winsW = (T.userData.windows || []).filter((w) => w.lit && w.face === 'front').map((w) => W3(w.pos).divideScalar(sc).applyMatrix4(T.matrixWorld));
      const pc = new THREE.PerspectiveCamera(c.fov, 1080 / 1920, 0.05, 400); const lim = 0.9 / (1 + c.move.Z);
      const aim = (P, lk) => { const tt = P.clone().addScaledVector(lk, c.dist_studs * S); tt.y = P.y + c.dist_studs * S * Math.tan(c.pitch_deg * DEG); return tt; };
      let best = null; const zEnd = 1 + c.move.Z;
      for (let a = 0.8; a <= 3.6; a += 1.4) for (let b = -17; b <= 17; b += 1) for (let yd = -85; yd <= 85; yd += 5) {
        const P = gate.clone().addScaledVector(toHouse, a * S).addScaledVector(side, b * S); P.y = c.height_studs * S; const lk = hflat(toHouse.clone().applyAxisAngle(Y_AX, yd * DEG));
        pc.position.copy(P); pc.lookAt(aim(P, lk)); pc.updateMatrixWorld(true);
        const nw = winsW.filter((v) => { const q = v.clone().project(pc); return q.z < 1 && Math.abs(q.x) < lim && Math.abs(q.y) < lim; }).length;
        const qa = kA.clone().project(pc), qb = kB.clone().project(pc); if (qa.z >= 1 || qb.z >= 1) continue;
        const xa = qa.x, xb = qb.x * zEnd;   // NDC on screen (the end frame is zoomed by the push)
        if (Math.min(xa, xb) < 0.0 || Math.max(xa, xb) > 0.66 || Math.max(Math.abs(qa.y), Math.abs(qb.y * zEnd)) > 0.7) continue;   // right of the sign, inside the frame
        const dk = P.distanceTo(kA.clone().lerp(kB, 0.5)) / S; if (dk < 7 || dk > 20) continue;
        const sc2 = Math.min(nw, 6) * 10 - Math.max(0, dk - 9) * 2.2 - Math.abs(b) * 0.1 - Math.abs(xa + xb - 0.6) * 3;
        if (!best || sc2 > best.sc) best = { sc: sc2, P, lk, nw, yd, a, b, dk };
      }
      if (!best) { const P = gate.clone().addScaledVector(toHouse, 0.5 * S).addScaledVector(side, 1.2 * S); P.y = c.height_studs * S; const lk = hflat(toHouse.clone().applyAxisAngle(Y_AX, -20 * DEG)); best = { P, lk, nw: 0 }; }
      const camP = best.P, look = best.lk; const tgt = aim(camP, look);
      ctx.camera.set({ pos: camP.toArray(), target: tgt.toArray(), fov: c.fov }).push(c.move.Z).truck((c.drift?.truck_studs ?? 0) * S);
      // the sign: 6.6 studs out from the lens, left of centre, turned to the lens (the kid stays right of it)
      ctx.camera.apply(0); const ray = new THREE.Vector3(-0.45, 0, 0.5).unproject(ctx.cam).sub(ctx.cam.position); ray.y = 0; ray.normalize();
      const sg = keepOffSign(ctx, { postH: 4.4, w: 2.2, h: 1.9 }); sg.position.copy(camP).addScaledVector(ray, (6.6 * S) / Math.max(0.3, ray.dot(look))); sg.position.y = 0; sg.rotation.y = yawOf(look.clone().negate()) - 0.18; ctx.add(sg);
      const kid = K.makeCharacter('grandkid', { face: 'grin' }); kid.rotation.y = yawOf(toHouse); ctx.add(kid);
      ctx.shared.kid = { av: kid, p0: kA.clone().setY(0), dir: toHouse, period: 0.45, stride: HOP * S };
      // a warm sunset fill that rides with him from the lens side (his back faces us; without it he is a black cut-out)
      ctx.shared.kidKey = ctx.add(ctx.lights.point({ color: '#ffc6a0', intensity: 2.6, pos: [0, 0, 0], decay: 2 })); ctx.shared.kidKeyOff = hflat(camP.clone().sub(kA)).multiplyScalar(1.8 * S).add(new THREE.Vector3(0, 3.4 * S, 0));
      ctx.shared.rig = sets.dusk(ctx, { set: T, postOpts: { exposure: 2.0 } });
      ctx.shared.cur = X.curtainCascade(ctx, T, { t0: ev(ctx, 'dark', 1.352), n: 6, gap: 0.12 }); ctx.add(ctx.shared.cur.group);
      faceKey(ctx, sg.position.clone().add(new THREE.Vector3(0, 3.4 * S, 0)), { cd: 1.2, color: '#ffd2a8', d: 1.4 });
      ctx.shared.fx = sparks(ctx, camP.clone().lerp(tgt, 0.6).setY(1.6), [3.0, 1.6, 2.0], 4, 's11', { colors: ['#ffe2c4', '#fff0e0', '#ffd0b0'] });
    },
    update(ctx, t) {
      const s = ctx.shared, k = s.kid; const ph = t / k.period; const n = Math.floor(ph), f = ph - n;
      const hopY = 0.55 * S * Math.sin(Math.PI * f); const along = (n + smooth(f)) * k.stride;
      k.av.position.copy(k.p0).addScaledVector(k.dir, along); k.av.position.y = hopY;
      const air = Math.sin(Math.PI * f);
      K.setPose(k.av, { armLz: 50 + 25 * air, armRz: 50 + 25 * air, armLx: 10, armRx: 10, legLx: 18 * air, legRx: -10 * air, bodyX: 6, neckX: -4 });
      s.kidKey.position.copy(k.av.position).add(s.kidKeyOff);
      s.cur.update(t); s.fx.update(t);
    },
  },

  // s12 "Next door, the gnomes are plastic." - next door by day (heroLot lot A2): three glossy plastic gnomes in a row facing
  // the street with $4.99 stickers, the REX kennel, a hose reel; REX lies chewing the nearest one's hat (it is knocked over
  // into his mouth); on "plastic" a bigger bite squashes the hat 15 % for 6 frames (the SQUEAK). nextDoorMS view.
  nextdoor_plastic: {
    quality: { shadows: 'pcfsoft' },
    build(ctx) {
      const p = ctx.params; const c = p.camera;
      const H = SE.heroLot(ctx, { tod: 'day' }); ctx.add(H); const nd = H.ep01.nextDoor;
      const g0 = nd.gnomes[0]; const base = g0.position.clone();
      const toStreet = new THREE.Vector3(0, 0, 1).applyAxisAngle(Y_AX, (c.yaw_deg || 0) * DEG); const camR0 = new THREE.Vector3(toStreet.z, 0, -toStreet.x);
      const dDir = camR0.clone().multiplyScalar(-Math.cos(55 * DEG)).addScaledVector(toStreet, -Math.sin(55 * DEG)).normalize(); // dog: left and behind, facing 3/4 to the lens
      // the dog in its chew pose: where is its mouth relative to its root?
      const dog = CR.makeDog(); CR.dogAt(dog, 0, { pose: 'chew' }); dog.updateMatrixWorld(true);
      const mz = dog.getObjectByName('dogMuzzle').getWorldPosition(new THREE.Vector3()); // root at the origin facing +z
      // knock the gnome over toward the dog until its hat tip is at mouth height
      const top = 0.62; const th = Math.acos(clamp01((mz.y - 0.02) / top)); const axis = new THREE.Vector3().crossVectors(Y_AX, dDir).normalize();
      const piv = new THREE.Group(); piv.position.copy(base); g0.parent.remove(g0); g0.position.set(0, 0, 0); piv.add(g0); piv.quaternion.setFromAxisAngle(axis, th); ctx.add(piv);
      const tip = base.clone().add(new THREE.Vector3(0, top, 0).applyAxisAngle(axis, th));
      dog.rotation.y = yawOf(dDir.clone().negate()); const mzW = mz.clone().applyAxisAngle(Y_AX, dog.rotation.y); dog.position.set(tip.x - mzW.x, 0, tip.z - mzW.z); ctx.add(dog);
      ctx.add(sets.contactShadow(ctx, { pos: [dog.position.x, 0, dog.position.z], radius: 0.5, opacity: 0.3 }));
      const subj = dog.position.clone().lerp(nd.gnomes[1].position, 0.72); const cam = boardCam(subj, c); ctx.camera.set(cam).push(c.move.Z).truck((c.drift?.truck_studs ?? 0) * S);
      ctx.shared.rig = SE.heroLight(ctx, H, { postOpts: { exposure: 1.28 } });
      faceKey(ctx, tip.clone().add(new THREE.Vector3(0, 0.15, 0)), { cd: 1.2, color: '#fff0dc', d: 1.5 });
      const hat = g0.getObjectByName('gnomeHat'); ctx.shared.hat = { o: hat, s0: hat.scale.clone() }; ctx.shared.dog = dog; ctx.shared.te = ev(ctx, 'plastic', 1.113);
    },
    update(ctx, t) {
      const s = ctx.shared; const u = t - s.te; const f = u * 60;
      const bite = f >= 0 && f < 6 ? 1 : f >= 6 ? Math.exp(-(f - 6) / 4) * Math.cos((f - 6) * 0.9) : 0;
      CR.dogAt(s.dog, t, { pose: { ...CR.DOG_POSES.chew, neck: 25 + 7 * Math.max(0, bite) }, chew: true, wag: 1 });
      const q = 1 - 0.15 * bite; s.hat.o.scale.set(s.hat.s0.x * (1 + 0.07 * bite), s.hat.s0.y * q, s.hat.s0.z * (1 + 0.07 * bite));
    },
  },

  // s13 "Their dog went down a hole." - top-down (h 9, fov 50) over next door's lawn: the empty REX kennel at the top, the
  // red lead running down into the neat round hole; the camera trucks 3.2 studs along the lead (linear, the whole shot) and
  // ends with the hole centred; on "hole" the lead gives one small tug toward it. Day, sun el 30 (longer shadows).
  kennel_hole: {
    quality: { shadows: 'pcfsoft' },
    build(ctx) {
      const p = ctx.params; const c = p.camera;
      const H = SE.heroLot(ctx, { tod: 'day' }); ctx.add(H); const nd = H.ep01.nextDoor;
      const hole = W3(nd.holeW), ring = W3(nd.ringW); const u = hflat(ring.clone().sub(hole)); // screen-up = toward the kennel
      const d = (c.drift?.truck_studs ?? 3.2) * S, h = c.height_studs * S, dur = ctx.shot.duration;
      const ctr = (t) => hole.clone().addScaledVector(u, d * (1 - clamp01(t / dur)));
      ctx.camera.set({ pos: (t, o) => (o || new THREE.Vector3()).copy(ctr(t)).add(new THREE.Vector3(0, h, 0)).addScaledVector(u, -0.002), target: (t, o) => (o || new THREE.Vector3()).copy(ctr(t)), fov: c.fov }).push(c.move.Z);
      ctx.shared.rig = SE.heroLight(ctx, H, { sun: { el: 30 }, postOpts: { exposure: 1.35 } });
      ctx.shared.nd = nd; ctx.shared.te = ev(ctx, 'hole', 0.862);
    },
    update(ctx, t) { ctx.shared.nd.tug(t, ctx.shared.te); },
  },

  // s14 "Your gnome can't walk out of its garden." - night, low at gnome eye level from the street side of the open gate
  // (h 1.4, d 5.5, yaw 0, pitch +3, fov 60): family gnome 0 toddles down the path toward the lens (0.1-stud hops at
  // 2.5 Hz, +-8 deg roll, unlit lantern swinging), and on "garden" bonks the property line: ripple rings, 12-sparkle burst,
  // 4 px shake for 0.3 s; it springs back 0.15 stud, wobbling.
  gate_bonk: {
    build(ctx) {
      const p = ctx.params; const c = p.camera;
      const H = SE.heroLot(ctx, { tod: 'night', gate: 1.45, board: false }); ctx.add(H); const sp = H.ep01.spots; const G0 = W3(sp.gate); G0.y = 0;
      const g = K.makeFamilyGnome(0, { lantern: 0, lod: 'hero', wear: 0.12 }); softenBeard(g); g.rotation.y = 0; ctx.add(g);
      const cam = boardCam(G0, c); ctx.camera.set(cam).push(c.move.Z);
      const tb = ev(ctx, 'garden', 1.295);
      ctx.shared.rig = H.ep01.light(ctx, { skyPreset: GALAXY_LOW, skyOpts: { intensity: 1.6 }, window: { n: 2, cd: 2.4, color: '#ffd9a0', maxD: 14 }, subject: { pos: [G0.x, 1.1 * S, G0.z - 0.8 * S], cd: 0.9, color: '#ffd9b0' } });
      faceKey(ctx, [G0.x, 1.3 * S, G0.z - 0.6 * S], { cd: 0.8, color: '#ffc49a', d: 0.9 });
      const PL = X.propertyLine(ctx, { a: [G0.x - 3.2 * S, G0.z], b: [G0.x + 3.2 * S, G0.z] }); PL.bonk(tb, [G0.x, 1.15 * S, G0.z]); ctx.add(PL.group);
      ctx.camera.shake({ t0: tb, dur: 0.3, px: 4, rot: 0.3, pos: 0, freq: 14 });
      ctx.shared.fx = sparks(ctx, [G0.x, 1.6 * S, G0.z + 1.4 * S], [2.4, 1.2, 1.6], 7, 's14');
      ctx.shared.s = { g, G0, tb, z0: G0.z - 3.35 * S, zc: G0.z - 0.42 * S, lan: g.getObjectByName('lantern'), PL };
    },
    update(ctx, t) {
      const s = ctx.shared.s; const g = s.g; const k = clamp01(t / s.tb); const h = K.gnomeHop(Math.min(t, s.tb), 0, { height: 0.1, freq: 2.5, roll: 8 });
      let z = lerp(s.z0, s.zc, k), y = h.y * S, roll = h.roll, pitch = 0, swing = 16 * Math.sin(2 * Math.PI * 2.5 * t + 1.2);
      if (t >= s.tb) { const u = t - s.tb; const back = 0.15 * S * (1 - Math.exp(-u * 9) * Math.cos(u * 14)); z = s.zc - back; y = 0.05 * S * Math.max(0, Math.sin(Math.PI * Math.min(1, u / 0.18)));
        roll = 9 * Math.exp(-u * 4) * Math.sin(u * 21); pitch = -10 * Math.exp(-u * 7) * Math.sin(u * 16 + 0.4); swing = 32 * Math.exp(-u * 3) * Math.sin(u * 13 + 0.3); }
      g.position.set(s.G0.x, y, z); g.rotation.set(pitch * DEG, 0, roll * DEG);
      if (s.lan) s.lan.rotation.x = swing * DEG;
      K.setGnomeGaze(g, 0, 4);
      s.PL.update(t); ctx.shared.fx.update(t);
    },
  },

  // s15 "Only family can carry it out." - the same gate, slightly high (h 3.6, d 5, yaw 20, pitch -12, fov 65): a grown-up's
  // plaid arms, outlined in soft gold, carry the gnome out through the gate; it crosses the line on "family" (the curtain
  // parts in a gold flash with 10 gold sparkles) and the gate swings shut behind them on "out" (6 frames) and latches.
  family_hands: {
    build(ctx) {
      const p = ctx.params; const c = p.camera;
      const H = SE.heroLot(ctx, { tod: 'night', gate: 1.45, board: false }); ctx.add(H); const sp = H.ep01.spots; const G0 = W3(sp.gate); G0.y = 0;
      const dad = K.makeCharacter('dad', { face: 'content' }); ctx.add(dad);
      const g = K.makeFamilyGnome(0, { lantern: 0, lod: 'hero', wear: 0.12 }); softenBeard(g); ctx.add(g);
      const tf = ev(ctx, 'family', 0.267), to = ev(ctx, 'out', 0.962);
      const v0 = 5.5, ta = 0.55, tau = 0.35; const xs = (t) => (t < ta ? v0 * t : v0 * ta + v0 * tau * (1 - Math.exp(-(t - ta) / tau)));
      const spd = (t) => (t < ta ? 1 : Math.exp(-(t - ta) / tau)); const off = -xs(tf); const zMid = G0.z + (xs(ctx.shot.duration * 0.55) + off) * S;
      // the board's yaw 20 / h 3.6 / pitch -12, 1.3 studs further back (he walks 3 studs toward the lens), aimed at the carried gnome
      const cam = boardCam([G0.x - 0.15 * S, 0, zMid], { ...c, dist_studs: c.dist_studs + 1.3 }); cam.target[1] = 2.6 * S; ctx.camera.set(cam).push(c.move.Z);
      ctx.shared.rig = H.ep01.light(ctx, { skyPreset: GALAXY_LOW, skyOpts: { intensity: 1.6 }, window: { n: 2, cd: 2.4, color: '#ffd9a0', maxD: 14 }, subject: { pos: [G0.x, 2.6 * S, G0.z + 0.6 * S], cd: 1.0, color: '#ffd9b0' } });
      faceKey(ctx, [G0.x, 2.7 * S, G0.z + 0.8 * S], { cd: 1.0, color: '#ffc49a', d: 1.0 });
      // the walk: the gnome (held 2.1 studs ahead of Dad's root) crosses the line at tf; Dad is clear of the leaf by `to`
      // brisk walk (5.5 studs/s) that settles after 0.55 s: the gnome is on the line at tf, Dad's back is past it by `to`
      ctx.shared.w = { dad, g, G0, zg: (t) => (xs(t) + off) * S, xs, spd };
      const PL = X.propertyLine(ctx, { a: [G0.x - 3.2 * S, G0.z], b: [G0.x + 3.2 * S, G0.z] }); PL.part(tf, [G0.x, 2.6 * S, G0.z]); ctx.add(PL.group);
      const GO = X.goldOutline(ctx, [dad.getObjectByName('armL'), dad.getObjectByName('armR'), g], { t0: 0, peak: 0.85, hold: 0.55, sparkles: 8 }); ctx.add(GO.group);
      ctx.shared.PL = PL; ctx.shared.GO = GO; ctx.shared.gate = { leaf: H.ep01.gate, a0: 1.45, to };
      ctx.shared.fx = sparks(ctx, [G0.x, 2.4 * S, G0.z + 1.2 * S], [2.2, 1.4, 1.4], 6, 's15');
    },
    update(ctx, t) {
      const s = ctx.shared, w = s.w; const z = w.G0.z + w.zg(t);
      w.dad.position.set(w.G0.x - 0.15 * S, 0, z - 2.15 * S); w.dad.rotation.y = 0;
      const walk = K.walkCycle(w.xs(t) / 5.5, { period: 0.62, legs: 30 * (0.25 + 0.75 * w.spd(t)), holdArms: true });
      K.setPose(w.dad, { ...walk, armLx: 80, armRx: 80, armLz: -13, armRz: -13, neckX: -10 }); w.dad.updateMatrixWorld(true);
      w.g.position.copy(w.dad.localToWorld(new THREE.Vector3(0, 2.15, 2.0))); w.g.rotation.set(0, 0, 0.6 * DEG * Math.sin(t * 7));
      const leaf = s.gate.leaf; if (leaf) { const u = (t - s.gate.to) * 60 / 6; leaf.rotation.y = u <= 0 ? s.gate.a0 : u < 1 ? s.gate.a0 * (1 - u * u) : -0.04 * Math.exp(-(u - 1) * 1.2) * Math.sin((u - 1) * 2.6); }
      K.setGnomeGaze(w.g, 0, 2);
      s.PL.update(t); s.GO.update(t); s.fx.update(t);
    },
  },

  // s16 "My grandpa turned last spring." - spring day, our front garden (tapHat view: h 3, d 7, yaw 35, fov 70, roll +1):
  // the hero (11, mustard hoodie) kneels in the tulips beside Grandpa gnome, standing in his spot under the hero's window
  // and facing it; he points and taps the hat with one finger on "grandpa" (6 frames): the hat tip wobbles +-6 deg (spring).
  hero_taps_hat: {
    quality: { shadows: 'pcfsoft' },
    build(ctx) {
      const p = ctx.params; const c = p.camera;
      const H = SE.heroLot(ctx, { tod: 'day', board: false }); ctx.add(H); const sp = H.ep01.spots; const B = W3(sp.bed0); const g = H.ep01.gnomes.grandpa;
      g.scale.multiplyScalar(1.3);   // scale cheat (bible 2.6 #6): his hat is what gets tapped, it must read next to the kneeling boy
      // yaw -35 instead of +35: the porch column 2.6 studs right of the window fills a +35 view (sets README)
      const cam = boardCam(B, { ...c, yaw_deg: -Math.abs(c.yaw_deg) }); const camP = W3(cam.pos);
      ctx.camera.set(cam).push(c.move.Z).rollBy(c.roll ? c.roll.deg[1] - c.roll.deg[0] : 0);
      g.updateWorldMatrix(true, true); const hat = g.getObjectByName('gnomeHat');
      // the real tip: the highest hat vertex in world space (the hat is bent, its bounding-box centre is not the tip)
      const tip = new THREE.Vector3(0, -1e9, 0); { const v = new THREE.Vector3(); hat.traverse((m) => { if (!m.isMesh || !m.geometry.attributes.position) return; const P = m.geometry.attributes.position; for (let i = 0; i < P.count; i += 1) { v.fromBufferAttribute(P, i).applyMatrix4(m.matrixWorld); if (v.y > tip.y) tip.copy(v); } }); } tip.y -= 0.02;
      // the hero kneels on the lawn edge of the bed, to the gnome's left on screen, turned toward it and a little to the lens
      const toCam = hflat(camP.clone().sub(B)); const camR = new THREE.Vector3(-toCam.z, 0, toCam.x);   // screen-right
      ctx.camera.set({ target: W3(cam.target).addScaledVector(camR, -0.9 * S).toArray() });
      const hero = K.makeCharacter('hero', { face: faceOf(ctx, 0, 'grin')[0] }); ctx.add(hero);
      hero.position.copy(B).addScaledVector(camR, -2.1 * S).addScaledVector(toCam, 0.9 * S); hero.position.y = 0; hero.rotation.y = yawOf(B.clone().sub(hero.position)) + 0.5;
      // turned 0.5 rad toward the lens so his grin reads; the right arm reaches across to the true hat tip
      const pTap = { bodyX: 18, legLx: -90, legRx: -90, lift: -1.45, armLx: 24, armLz: -8, armRz: -10, neckX: -4, neckY: 22, armRx: 90 };
      reachTo(hero, 'R', pTap, 'armRx', tip.clone().add(new THREE.Vector3(0, 0.02, 0)), { lo: 30, hi: 175 });
      ctx.shared.hero = hero; ctx.shared.pTap = pTap; ctx.shared.te = ev(ctx, 'grandpa', 0.168);
      ctx.shared.hat = { o: hat, r0: hat.rotation.clone() }; ctx.shared.g = g;
      ctx.shared.rig = SE.heroLight(ctx, H, { postOpts: { exposure: 1.3 } });
      hero.updateWorldMatrix(true, true); faceKey(ctx, hero.getObjectByName('head').getWorldPosition(new THREE.Vector3()), { cd: 1.2, color: '#ffe8d0', d: 1.4 });
    },
    update(ctx, t) {
      const s = ctx.shared; const f = (t - s.te) * 60;
      const hover = f < -3 ? 6 : f < 0 ? 6 * (-f / 3) : f < 3 ? 6 * (f / 3) : 6;    // finger hovers 6 deg up, taps the hat tip on the word, lifts
      K.setPose(s.hero, { ...s.pTap, armRx: s.pTap.armRx + hover });
      const u = t - s.te - 3 / 60; const wob = u > 0 ? 6 * DEG * Math.exp(-u * 4.5) * Math.sin(2 * Math.PI * 3.2 * u) : 0;
      s.hat.o.rotation.set(s.hat.r0.x + wob * 0.6, s.hat.r0.y, s.hat.r0.z + wob);
      K.gnomeIdle(s.g, t, { seed: 'gpSpring' });
    },
  },

  // s17 "I say goodnight," - night, the hero's own bedroom (hero11 era): OTS, he waves through the glass (armR 160, +-15
  // deg at 2 Hz); below in the flowerbed Grandpa gnome looks up, lit by the window spill; the view outside is darker than
  // the room (bedroomNight P2).
  goodnight_window: {
    build(ctx) {
      const p = ctx.params; const c = p.camera;
      const H = SE.heroLot(ctx, { tod: 'night', board: false, theoRoom: { era: 'hero11', lit: true, curtains: 'open' } }); ctx.add(H);
      const g = H.ep01.gnomes.grandpa; const sill = W3(H.ep01.spots.theoSill); const v = H.ep01.views.room_otsWindow;
      // room frame (studs; origin on the floor at the window wall, +z out through the glass): the sets owner's s17 view
      // room_otsWindow sits at [1.5, 5.7, -4.8] in it (interiors.js), so its origin is recovered from that view
      const O = W3(v.pos).sub(new THREE.Vector3(1.5 * S, 5.7 * S, -4.8 * S)); const R = (x, y, z) => O.clone().add(new THREE.Vector3(x * S, y * S, z * S));
      // the hero at the glass, 1.4 studs left of the window centre (screen-right of the sight line to Grandpa), facing out
      const hero = K.makeCharacter('hero', { face: 'grin' }); hero.position.copy(R(-1.5, 0, -0.95)); hero.rotation.y = 0; ctx.add(hero);
      K.setPose(hero, { armLx: 128, neckX: -14 }); hero.updateWorldMatrix(true, true); const head = hero.getObjectByName('head').getWorldPosition(new THREE.Vector3());
      const hand = K.handSocket(hero, 'L').getWorldPosition(new THREE.Vector3()); void hand;
      // OTS from behind his left shoulder, 4.6 studs back and above his head (h 7.4 instead of 4.9: from eye level the sill
      // hides the flowerbed right under the glass, and at d 2.2 his R6 shoulders fill the frame)
      const cp = R(1.5, 7.4, -5.6);
      // Grandpa: x1.25 and, if needed, slid out from the wall until his eyes clear the sill from the lens (bible 2.6 #6)
      // ... and slid to the left half of the bed (room x +0.9): seen past the boy's left arm, not through his body
      g.scale.multiplyScalar(1.25); g.position.x = R(0.9, 0, 0).x; g.updateWorldMatrix(true, true); let E = eyesOf(g);
      // the deep inner window board hides everything less than ~0.2 NDC above the glass bottom: slide him out (whole
      // 0.25-stud steps, deterministic) until his eyes are clear of it with the camera aimed at the lower window
      const tgt = R(-0.6, 3.2, 0.8); const pc = new THREE.PerspectiveCamera(c.fov, 1080 / 1920, 0.05, 400); pc.position.copy(cp); pc.lookAt(tgt); pc.updateMatrixWorld(true);
      const ndcY = (v) => v.clone().project(pc).y; const sillY = ndcY(new THREE.Vector3(E.x, sill.y, sill.z));
      for (let i = 0; i < 24 && ndcY(E) < sillY + 0.24; i++) { g.position.z += 0.25 * S; g.updateWorldMatrix(true, true); E = eyesOf(g); }
      const need = E.z;
      ctx.camera.set({ pos: cp.toArray(), target: tgt.toArray(), fov: c.fov }).push(c.move.Z);
      // bible P2, with the hemisphere a notch down and the glass darker so the lawn reads as night through it
      ctx.shared.rig = I.bedroomNight(ctx, { set: H, lamp: 4, hemiIntensity: 1.45, lanternOutside: { pos: [E.x - 0.15, E.y + 0.5, E.z - 0.25], cd: 2.6 } });
      H.ep01.theo.glass.material.opacity = 0.7;
      gazeAt(g, head);
      faceKey(ctx, head.clone().add(new THREE.Vector3(0, -0.15, 0)), { cd: 1.0, color: '#ffd9c0', d: 1.0 });
      ctx.shared.fx = sparks(ctx, cp.clone().lerp(tgt, 0.35), [1.6, 1.2, 1.0], 9, 's17');
      ctx.shared.hero = hero; ctx.shared.g = g;
    },
    // he waves (+-15 deg at 2 Hz) with his NEAR arm (board: armR 160): from behind his left shoulder the right arm is hidden
    // by his head / off the frame edge, and an arm straight up points at this high lens; raised forward to the glass
    // (armLx 128) the hand reads against the upper panes, above Grandpa
    update(ctx, t) { K.setPose(ctx.shared.hero, { armLx: 128, armLz: 8 + 15 * Math.sin(2 * Math.PI * 2 * t), neckX: -14, neckY: 8, neckZ: 4 }); K.gnomeIdle(ctx.shared.g, t, { seed: 'gpNight', amp: 0.3 }); ctx.shared.fx.update(t); },
  },

  // s18 "and he blinks." - close on Grandpa gnome from below (h 0.9, d 1.6, yaw -15, pitch 14), gaze up 20 at the lit
  // window, warm window-spill key from above; on "blinks" his lids close for exactly 2 frames + the TIK glint as they reopen.
  gnome_blink_night: {
    build(ctx) {
      const p = ctx.params; const c = p.camera;
      const H = SE.heroLot(ctx, { tod: 'night', bed: 'grandpa', lantern: 0 }); ctx.add(H); const g = H.ep01.gnomes.grandpa; const B = W3(H.ep01.spots.bed0);
      softenBeard(g); g.updateWorldMatrix(true, true);
      const eyes = eyesOf(g); const fwd = new THREE.Vector3(Math.sin(g.rotation.y), 0, Math.cos(g.rotation.y));
      const lan = g.getObjectByName('lantern').getWorldPosition(new THREE.Vector3()); const gl = new THREE.Vector3(-fwd.z, 0, fwd.x); const lanSide = Math.sign(lan.clone().sub(eyes).dot(gl)) || 1;
      const nose = eyes.clone().addScaledVector(fwd, 0.05 * S); nose.y -= 0.12 * S;
      const dir = fwd.clone().applyAxisAngle(Y_AX, lanSide * Math.abs(c.yaw_deg) * DEG);
      const pos = nose.clone().addScaledVector(dir, c.dist_studs * S); pos.y = c.height_studs * S;
      const tgt = eyes.clone().add(new THREE.Vector3(0, 0.05 * S, 0)); const hd = Math.hypot(tgt.x - pos.x, tgt.z - pos.z); tgt.y = pos.y + hd * Math.tan(c.pitch_deg * DEG);
      ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: c.fov }).push(c.move.Z);
      const camYaw = Math.atan2(tgt.x - pos.x, -(tgt.z - pos.z)) / DEG;
      ctx.shared.rig = H.ep01.light(ctx, { skyPreset: GALAXY_LOW, skyOpts: { intensity: 2.0 }, moon: { az: camYaw + 14, el: 52, size: 8, style: 'tf' }, hemiIntensity: 1.0, key: { intensity: 0.45 },
        window: { n: 1, cd: 2.4, color: '#ffd9a0', maxD: 10 }, postOpts: { exposure: 1.3, grade: { temperature: -4, tint: 6 } } });
      // the window spill: warm, from above and in front (the lit glass is over his head)
      ctx.add(ctx.lights.point({ color: '#ffc08a', intensity: 3.0, pos: nose.clone().addScaledVector(fwd, -0.35).add(new THREE.Vector3(0, 0.75, 0)).addScaledVector(dir, 0.35).toArray(), decay: 2 }));
      ctx.add(ctx.lights.sun({ color: '#8a90ff', intensity: 0.7, pos: nose.clone().addScaledVector(fwd, -6).addScaledVector(gl, -lanSide * 5).add(new THREE.Vector3(0, 4, 0)).toArray(), target: nose.toArray(), shadow: false }));
      K.setGnomeGaze(g, 0, 20);
      const tb = ev(ctx, 'blinks', 0.325); const T = X.blinkTik(ctx, g, { t0: tb }); ctx.add(T.group);
      ctx.shared.b = { g, tb, T }; ctx.shared.fx = sparks(ctx, nose.clone().lerp(pos, 0.45), [0.9, 0.9, 0.35], 8, 's18', { drift: [0.02, 0.05] });
      void B;
    },
    update(ctx, t) { const b = ctx.shared.b; K.gnomeIdle(b.g, t, { seed: 'hero' }); K.setGnomeLids(b.g, K.gnomeBlink(t, [b.tb])); b.T.update(t); ctx.shared.fx.update(t); },
  },

  // s19 "For 60 years, he walked our lawn at nine," - sepia flashback (2010s lot): human Grandpa (navy cardigan, walrus
  // moustache, gold glasses, tartan slippers) strolls our dark lawn left to right with his flashlight on, past the KEEP OFF
  // sign; the house with lit windows behind him. Follow truck 7 studs (he walks 7 studs: centred), +12 % push.
  fb_grandpa_walk: {
    build(ctx) {
      const p = ctx.params; const c = p.camera;
      const H = SE.heroLot(ctx, { tod: 'night', era: '2010s', keepOff: false, gnomes: ['bedFront0', 'bedFront1', 'lawn2'] }); ctx.add(H); const sp = H.ep01.spots; const G0 = W3(sp.gate); G0.y = 0;
      const dist = (c.drift?.truck_studs ?? 7) * S, dur = ctx.shot.duration; const zW = G0.z - 10.0 * S; const x0 = G0.x - 5.2 * S;
      const gp = K.makeCharacter('grandpa', { face: faceOf(ctx, 0, 'content')[0] }); gp.rotation.y = Math.PI / 2; ctx.add(gp);
      const fl = CR.makeFlashlight({ on: 1, light: false }); CR.holdFlashlight(gp, fl, { axis: 'forward' });
      // the sign: on the lawn beside the path, behind his walk line, facing the street
      const sg = keepOffSign(ctx, { postH: 6.2, w: 4.6, h: 3.1 }); sg.position.set(G0.x - 1.0 * S, 0, zW - 3.0 * S); sg.rotation.y = 0.12; ctx.add(sg);
      // 3/4 front (yaw 20 toward his walk) so his decal face reads; the follow is a pure +x track (truck 7 studs)
      const cam = boardCam([x0 + 0.6 * S, 0, zW], { ...c, yaw_deg: 20 }); const P0 = W3(cam.pos), T0 = W3(cam.target);
      ctx.camera.set({ pos: (t, o) => (o || new THREE.Vector3()).copy(P0).add(new THREE.Vector3(dist * t / dur, 0, 0)), target: (t, o) => (o || new THREE.Vector3()).copy(T0).add(new THREE.Vector3(dist * t / dur, 0, 0)), fov: c.fov }).push(c.move.Z);
      ctx.shared.rig = sepiaLight(ctx, H, { subject: { pos: [x0 + dist / 2, 3.6 * S, zW], cd: 1.0, color: '#ffe6c8' } });
      const Bm = X.flashlightBeam(ctx, { torch: fl, t0: -1, length: 8, angle: 16, cd: 3, opacity: 0.16 }); ctx.add(Bm.group);
      ctx.shared.w = { gp, fl, Bm, x0, zW, v: dist / dur };
    },
    update(ctx, t) {
      const w = ctx.shared.w; const x = w.x0 + w.v * t; w.gp.position.set(x, 0, w.zW);
      const wc = K.walkCycle(t, { period: 1.0, legs: 25, holdArms: true }); K.setPose(w.gp, { ...wc, armLx: -wc.legLx * 0.8, armRx: 40, armRz: 4, neckY: -42, neckX: -4 });   // head turned to the lens: his face reads in a profile walk
      w.gp.updateMatrixWorld(true); CR.aimFlashlight(w.fl, new THREE.Vector3(x + 3.6 * S, 0, w.zW + 0.6 * S)); w.gp.updateMatrixWorld(true);
      CR.setFlashlight(w.fl, 1); w.Bm.update(t);
    },
  },

  // s20 "flashlight," (and part 4's s61 callback) - insert: Grandpa's hand clicks the flashlight on (the event frame) and the
  // beam blooms across the wet grass. h 3.2, d 2.0, yaw 60, pitch -10, fov 45, +25 % push. Sepia.
  fb_flashlight: {
    build(ctx) {
      const p = ctx.params; const c = p.camera;
      const H = SE.heroLot(ctx, { tod: 'night', era: '2010s', keepOff: false }); ctx.add(H); const sp = H.ep01.spots; const G0 = W3(sp.gate); G0.y = 0;
      const at = new THREE.Vector3(G0.x - 1.5 * S, 0, G0.z - 7.0 * S);
      const gp = K.makeCharacter('grandpa', { face: 'content' }); gp.position.copy(at); gp.rotation.y = Math.PI / 2; ctx.add(gp);
      K.setPose(gp, { armRx: 66, armRz: 6, armLx: 4, neckX: -14 }); gp.updateMatrixWorld(true);
      const fl = CR.makeFlashlight({ on: 0, light: false }); CR.holdFlashlight(gp, fl, { axis: 'forward' }); gp.updateMatrixWorld(true);
      const spot = at.clone().add(new THREE.Vector3(4.2 * S, 0, 0.9 * S)); CR.aimFlashlight(fl, spot); gp.updateMatrixWorld(true);
      const hand = K.handSocket(gp, 'R').getWorldPosition(new THREE.Vector3());
      // yaw 60 measured from his facing direction (+x) round to his torch side: the hand in 3/4 profile, the beam running
      // screen-right down onto the grass; target a third of the way along the beam so the hand sits left of centre
      const aimP = hand.clone().lerp(spot, 0.1); aimP.y = hand.y - 0.12 * S; /* the gripping arm end in frame, not just the torch */ const cam = boardCam(hand, { ...c, yaw_deg: 90 - c.yaw_deg, dist_studs: c.dist_studs + 1.2 }, { base: [0, 0, 1], aimY: aimP.y }); cam.target = [aimP.x, aimP.y, aimP.z];
      ctx.camera.set(cam).push(c.move.Z);
      const tc = ev(ctx, 'flashlight', 1 / 60);
      ctx.shared.rig = sepiaLight(ctx, H, { subject: { pos: hand.toArray(), cd: 0.6, color: '#ffe6c8' } });
      const Bm = X.flashlightBeam(ctx, { torch: fl, t0: tc, length: 8, angle: 18, cd: 4, opacity: 0.2, motes: 8 }); ctx.add(Bm.group);
      ctx.shared.dew = sparks(ctx, hand.clone().lerp(spot, 0.75).setY(0.05), [1.6, 0.06, 0.9], 9, 's20dew', { px: [14, 30], colors: ['#fff6e8', '#ffffff', '#ffe8c8'], drift: [0.004, 0.012], brightness: 1.8 });
      ctx.shared.f = { fl, Bm, tc };
    },
    update(ctx, t) {
      const f = ctx.shared.f; const on = t >= f.tc ? 1 : 0; CR.setFlashlight(f.fl, on); f.Bm.update(t);
      const k = on ? clamp01((t - f.tc) / 0.12) : 0; f.Bm.cone.material.uniforms.uA.value = on ? 0.2 * 2.4 * (0.4 + 0.6 * k) : 0;   // dark before the click frame
      ctx.shared.dew.visible = on > 0; ctx.shared.dew.update(t); ctx.shared.dew.children.forEach((s) => { s.material.opacity *= k; });
    },
  },

  // s21 "slippers," (and part 4's s62 callback) - ground-level insert: tartan slippers step onto the wet grass in the torch
  // beam; the near slipper lands 6 frames after the cut (s21) / on the event frame in the callback (the sound's STEP_WET
  // times), dew glints spray. h 0.4, d 2.4, yaw 80, pitch +2, fov 45, +20 % push. Sepia.
  fb_slippers: {
    build(ctx) {
      const p = ctx.params; const c = p.camera;
      const H = SE.heroLot(ctx, { tod: 'night', era: '2010s', keepOff: false, gnomes: ['bedFront0', 'bedFront1'] }); ctx.add(H); const sp = H.ep01.spots; const G0 = W3(sp.gate); G0.y = 0;
      const te = ev(ctx, 'slippers', 1 / 60); const tl = p.callback_of ? te : te + 5 / 60;    // landing time
      const period = 1.0, v = 3.4 * S;                                                          // studs/s, matching legs 25
      const xl = G0.x - 4.0 * S, zW = G0.z - 7.0 * S;                                          // where the body is at landing (on the grass, clear of the stones)
      const gp = K.makeCharacter('grandpa', { face: 'content' }); gp.rotation.y = Math.PI / 2; ctx.add(gp);
      const fl = CR.makeFlashlight({ on: 1, light: false }); CR.holdFlashlight(gp, fl, { axis: 'forward' });
      const foot = new THREE.Vector3(xl + 0.85 * S, 0, zW + 0.5 * S);                            // the near (right) slipper at landing
      // ground level (h 0.4), 80 deg off his walk on the street side, following him (truck at his 3.4 studs/s): both
      // slippers scissor in the lower middle over the wet grass, the near one lands on the event; 5 studs out so the two
      // legs fit the 9:16 width at fov 45 with grass round them (at the board's 2.4 one leg fills the frame as a grey box)
      const cdir = new THREE.Vector3(Math.cos(c.yaw_deg * DEG), 0, Math.sin(c.yaw_deg * DEG)); const D = 6.6 * S;
      const mid = (t, o) => (o || new THREE.Vector3()).set(xl + v * (t - tl) + 0.1 * S, 0, zW + 0.15 * S);
      ctx.camera.set({ pos: (t, o) => mid(t, o).addScaledVector(cdir, D).setY((c.height_studs + 0.25) * S), target: (t, o) => mid(t, o).setY(0.95 * S), fov: c.fov }).push(c.move.Z);   // +0.25 stud: the slippers clear the near grass blades
      ctx.shared.rig = sepiaLight(ctx, H, { subject: { pos: [foot.x, 0.6 * S, foot.z], cd: 0.6, color: '#ffe6c8' } });
      const Bm = X.flashlightBeam(ctx, { torch: fl, t0: -1, length: 7, angle: 22, cd: 9, opacity: 0.22, motes: 6 }); ctx.add(Bm.group);
      const burst = sets.burst(ctx, { pos: [foot.x + 0.1 * S, 0.12 * S, foot.z + 0.1 * S], t0: tl, dur: 0.35, count: 12, spread: 0.35, px: [10, 26], ring: false, core: false, colors: ['#ffffff', '#fff2dc', '#ffe6c8'], brightness: 2.0, gravity: -0.6, seed: 's21dew' }); ctx.add(burst);
      ctx.shared.dew = sparks(ctx, [foot.x + 0.6 * S, 0.05, foot.z + 0.4 * S], [2.4, 0.05, 1.2], 12, 's21dewg', { px: [12, 28], colors: ['#fff6e8', '#ffffff'], drift: [0.003, 0.01], brightness: 1.8 });
      ctx.shared.w = { gp, fl, Bm, burst, xl, zW, v, tl, period };
    },
    update(ctx, t) {
      const w = ctx.shared.w; const x = w.xl + w.v * (t - w.tl); w.gp.position.set(x, 0, w.zW);
      // the near (right) leg is at its forward extreme at landing: phase so sin = -1 for legL (legR = +25 forward) at tl
      const ph = (t - w.tl) / w.period - 0.25; const wc = K.walkCycle(t, { period: w.period, legs: 25, holdArms: true, phase: -w.tl / w.period - 0.25 }); void ph;
      const sN = Math.abs(Math.sin(2 * Math.PI * ((t - w.tl) / w.period - 0.25)));
      const lift = -2 * (1 - Math.cos(25 * DEG)) * Math.pow(sN, 3);                             // the body settles as the front heel lands
      K.setPose(w.gp, { ...wc, armLx: -wc.legLx * 0.8, armRx: 40, armRz: 4, lift }); w.gp.updateMatrixWorld(true);
      CR.aimFlashlight(w.fl, new THREE.Vector3(x + 1.25 * S, 0, w.zW + 0.6 * S)); w.gp.updateMatrixWorld(true);   // the pool just ahead of the slippers
      CR.setFlashlight(w.fl, 1); w.Bm.update(t); w.burst.update(t); ctx.shared.dew.update(t);
    },
  },

  // s22 "one lap," (and part 4's s63 callback) - top-down over our lawn (lapTop view, h 34, fov 45, roll +4): Grandpa's worn
  // lap path, a faint flattened-grass loop with his flashlight dot travelling round it; the loop has a kink, a dent toward
  // the house under his window (the rewatch clue for 70.9 s). The house edge along the top of frame. Sepia.
  fb_lap: {
    build(ctx) {
      const p = ctx.params; const c = p.camera;
      const H = SE.heroLot(ctx, { tod: 'night', era: '2010s', keepOff: true }); ctx.add(H); const sp = H.ep01.spots; const v = H.ep01.views.lapTop;
      // the sets owner's lapTop view as is (part 4's s64 cranes down from it into the kink). bed0's window is left of
      // centre in it, so the kink sits upper LEFT of centre (board note: upper right; sliding the view to move it shows
      // the end of the house instead of a house edge along the top)
      ctx.camera.set(v).push(c.move.Z).rollBy(c.roll ? c.roll.deg[1] - c.roll.deg[0] : 0);
      // the loop in lot-plane metres: an oval round the middle of the lawn, a dent toward the house under bed0's window
      const ctr0 = W3(v.target); ctr0.y = 0; const B = W3(sp.bed0); const ctr = ctr0.clone(); ctr.x = lerp(ctr0.x, B.x, 0.12);
      const rx = 5.9 * S, rz = 6.0 * S; const cz = ctr0.z + 0.4 * S;
      const pts3 = []; const N = 96;
      for (let i = 0; i < N; i++) {
        const a = (i / N) * Math.PI * 2; let x = ctr.x + Math.cos(a) * rx, z = cz + Math.sin(a) * rz;
        const kx = B.x + 1.4 * S; const dk = Math.pow(Math.max(0, 1 - Math.abs(x - kx) / (1.3 * S)), 1.6) * (z < cz ? 1 : 0); z = lerp(z, Math.min(z, B.z + 2.2 * S), dk); pts3.push(new THREE.Vector3(x, 0, z));
      }
      const curve = new THREE.CatmullRomCurve3(pts3, true, 'catmullrom', 0.5);
      const ext = 18 * S; const toUV = (q) => [(q.x - (ctr.x - ext)) / (2 * ext), (q.z - (cz - ext)) / (2 * ext)];
      const tex = lapTexture(ctx, 'v3', curve.getSpacedPoints(160).map(toUV));
      const plane = new THREE.Mesh(new THREE.PlaneGeometry(2 * ext, 2 * ext), new THREE.MeshStandardMaterial({ map: tex, transparent: true, depthWrite: false, roughness: 0.6, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }));
      plane.rotation.x = -Math.PI / 2; plane.position.set(ctr.x, 0.02, cz); plane.renderOrder = 2; ctx.add(plane);
      // tiny Grandpa walking the loop (clockwise seen from above), his beam spot 1.4 studs ahead
      const gp = K.makeCharacter('grandpa', { face: 'content' }); ctx.add(gp);
      const fl = CR.makeFlashlight({ on: 1, light: false }); CR.holdFlashlight(gp, fl, { axis: 'forward' });
      const L = curve.getLength(); const kinkU = (() => { let best = 0, bd = 1e9; for (let i = 0; i <= 200; i++) { const q = curve.getPointAt(i / 200); const d = q.distanceTo(new THREE.Vector3(B.x, 0, B.z)); if (d < bd) { bd = d; best = i / 200; } } return best; })();
      const dot = sets.lightPool(ctx, { pos: [0, 0.03, 0], radius: 1.1 * S, color: '#ffe8c0', opacity: 0.85 }); ctx.add(dot);
      const dotGlow = sets.glow(ctx, { pos: [0, 0.1, 0], color: '#fff0d0', px: 46, opacity: 0.9 }); ctx.add(dotGlow);
      ctx.shared.rig = sepiaLight(ctx, H, { exposure: 1.2 });
      ctx.shared.l = { curve, L, gp, fl, dot, dotGlow, u0: (kinkU + 0.62) % 1, v: 3.4 * S };
    },
    update(ctx, t) {
      const l = ctx.shared.l; const u = (l.u0 - (l.v * t) / l.L + 1) % 1; const q = l.curve.getPointAt(u); const tan = l.curve.getTangentAt(u).negate();
      l.gp.position.set(q.x, 0, q.z); l.gp.rotation.y = yawOf(tan);
      const wc = K.walkCycle(t, { period: 1.0, legs: 25, holdArms: true }); K.setPose(l.gp, { ...wc, armLx: -wc.legLx * 0.8, armRx: 40 });
      const ua = (u - (1.4 * S) / l.L + 1) % 1; const a = l.curve.getPointAt(ua); l.dot.position.set(a.x, 0.03, a.z); l.dotGlow.position.set(a.x, 0.12, a.z);
      l.gp.updateMatrixWorld(true); CR.aimFlashlight(l.fl, a); CR.setFlashlight(l.fl, 1);
    },
  },

  // s23 "checking for moles, he'd say," - CU from below (h 3.9, d 2.8, yaw -10, pitch +8): Grandpa holds the flashlight
  // under his chin like a ghost story (warm under-light #fff1d0 2.5 cd), face talk, and winks on "he'd" (decal swap). Sepia.
  fb_wink: {
    build(ctx) {
      const p = ctx.params; const c = p.camera;
      const H = SE.heroLot(ctx, { tod: 'night', era: '2010s', keepOff: false, gnomes: ['bedFront0', 'bedFront1'] }); ctx.add(H); const sp = H.ep01.spots; const G0 = W3(sp.gate); G0.y = 0;
      const at = new THREE.Vector3(G0.x - 2.0 * S, 0, G0.z - 6.0 * S);
      const faces = faceOf(ctx, 0, 'talk'); const gp = K.makeCharacter('grandpa', { face: faces[0] }); gp.position.copy(at); gp.rotation.y = 0; ctx.add(gp);
      // ghost-story torch: the right arm comes forward and in (armRz -36) so the hand sits centred just under the chin,
      // 0.6 studs below it; the torch points up at his face (solve armRx for the height, Grandpa stays put)
      const head = gp.getObjectByName('head'); gp.updateMatrixWorld(true); const face = head.getWorldPosition(new THREE.Vector3());
      const pT = { armRx: 90, armRz: -36, armLx: 6, neckX: 6 }; reachTo(gp, 'R', pT, 'armRx', face.clone().add(new THREE.Vector3(0, -1.05 * S, 0)), { lo: 40, hi: 150, move: false }); K.setPose(gp, pT); gp.updateMatrixWorld(true);
      const fl = CR.makeFlashlight({ on: 1, light: false }); CR.holdFlashlight(gp, fl, { axis: 'forward' }); gp.updateMatrixWorld(true);
      CR.aimFlashlight(fl, head.localToWorld(new THREE.Vector3(0, -0.1, 0.45))); gp.updateMatrixWorld(true);
      // CU from below (h 3.9, pitch about +6): 3.4 studs to the head centre (2.8 to the face), target under the chin so
      // the face sits in the upper 40 % with the glowing torch under it
      const cam = boardCam([face.x, 0, face.z], { ...c, dist_studs: c.dist_studs + 0.6 }, { base: [0, 0, 1], aimY: face.y - 0.38 * S }); ctx.camera.set(cam).push(c.move.Z).rollBy(c.roll ? c.roll.deg[1] - c.roll.deg[0] : 0);
      ctx.shared.rig = sepiaLight(ctx, H, { hemiIntensity: 0.26, exposure: 1.0, key: { intensity: 0.18 }, window: { n: 1, cd: 1.0, color: '#ffd9a0', maxD: 14 } });
      // the under-light (board: point #fff1d0 2.5 cd): at the torch lens, under and in front of the chin
      const lens = CR.flashlightRay(fl).origin; ctx.add(ctx.lights.point({ color: '#fff1d0', intensity: 1.5, pos: face.clone().add(new THREE.Vector3(0, -0.88 * S, 0.78 * S)).toArray(), decay: 2 }));   // just under the chin: a steep bottom-up falloff
      ctx.add(sets.glow(ctx, { pos: lens.toArray(), color: '#fff2d8', px: 110, opacity: 0.6 }));
      ctx.shared.w = { gp, fl, faces, tw: ev(ctx, "he'd", 0.87) };
    },
    update(ctx, t) { const w = ctx.shared.w; K.setFaceEx(w.gp, t >= w.tw && w.faces[1] ? w.faces[1] : w.faces[0]); CR.setFlashlight(w.fl, 1, { cd: 0 }); },
  },

  // s24 "big ones." - MS (h 4.4, d 7, yaw 8, pitch -2): Grandpa snaps his arms wide like a fisherman's tall tale (armLz /
  // armRz 80, 8 frames outBack from the cut), eyebrows up (wonder); the torch rides the arm, its beam swinging sideways. Sepia.
  fb_big_ones: {
    build(ctx) {
      const p = ctx.params; const c = p.camera;
      const H = SE.heroLot(ctx, { tod: 'night', era: '2010s', keepOff: false, gnomes: ['bedFront0', 'bedFront1', 'lawn3'] }); ctx.add(H); const sp = H.ep01.spots; const G0 = W3(sp.gate); G0.y = 0;
      const at = new THREE.Vector3(G0.x - 2.0 * S, 0, G0.z - 6.8 * S);   // 0.8 studs further up the lawn than s23: the lens backs off with him and stays inside the pickets
      const gp = K.makeCharacter('grandpa', { face: faceOf(ctx, 0, 'wonder')[0] }); gp.position.copy(at); gp.rotation.y = 0; ctx.add(gp);
      const fl = CR.makeFlashlight({ on: 1, light: false }); CR.holdFlashlight(gp, fl, { axis: 'arm' });
      const cam = boardCam([at.x, 0, at.z], { ...c, dist_studs: c.dist_studs + 0.8 }, { base: [0, 0, 1] }); ctx.camera.set(cam).push(c.move.Z);   // d +0.8: both hands stay inside the 9:16 frame at the end of the push
      ctx.shared.rig = sepiaLight(ctx, H, { subject: { pos: [at.x, 4.4 * S, at.z], cd: 1.4, color: '#ffe6c8' } });
      const Bm = X.flashlightBeam(ctx, { torch: fl, t0: -1, length: 8, angle: 16, cd: 3, opacity: 0.16 }); ctx.add(Bm.group);
      ctx.shared.w = { gp, fl, Bm };
    },
    update(ctx, t) {
      const w = ctx.shared.w; const u = outBack(t / (8 / 60), 1.9);
      const P0 = { armLx: 30, armRx: 38, armLz: 6, armRz: 6, neckX: 0 }, P1 = { armLx: 76, armRx: 76, armLz: 40, armRz: 40, neckX: 6, neckZ: 3 };   // "THIS big": arms out and forward, both hands inside the frame
      const P = {}; for (const k of new Set([...Object.keys(P0), ...Object.keys(P1)])) P[k] = lerp(P0[k] || 0, P1[k] || 0, u);
      K.setPose(w.gp, P); w.gp.updateMatrixWorld(true); CR.setFlashlight(w.fl, 1); w.Bm.update(t);
    },
  },
};

export const PART = 1;
export const builders = { ...BUILDERS, ...NEW_BUILDERS };
