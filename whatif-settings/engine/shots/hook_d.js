// hook_d.js — hook shots C10-C17 + D1: the first proof gag and the button (S00-L017..L023 + S01-L001).
//   C10_welcome     SYS "Welcome to Reality Settings!": the toast drops onto the Gotta Catch downbeat over the night street,
//                   gear badges pop above the roofs, the gear glows on "Settings", the install bar fills
//   C11_proveit     SAM "Prove it.": mid-yawn stretch in bed (phone-lit), then bored half-lids
//   C12_brightness  POV in bed: the thumb opens Brightness, the card pops, a snap zoom into the slider fills the frame
//   C13_slide       "Slide it up.": the big thumb drags the sun knob 20% -> 35% (the sun icon swells), the riser starts
//   C14_sunrise     "Just a little.": the moon flares into a sun on "little", the room blows out white, the birds wake
//   C15_dadsun      DAD "Who turned on the SUN?!": Sam's door bangs open, Dad in pyjamas shields his eyes, lurch on SUN
//   C16_phonelower  "That's not the PHONE's brightness.": Sam slowly lowers the phone, star eyes fade to fear
//   C17_planet      "That's the planet's.": one continuous zoom out from the sunlit house to space (the street shrinks
//                   into the glowing town on Earth), deadpan hold, one tiny tweet in space
//   D1_day1         N "Day one.": the DAY 1 card slams in (cardSlam transition, impact at +0.12 s), toggle flicks on "one"
// Times come from the voice lines (ctx.line(id).at(word)) and T.sync, with the built timeline's values as fallbacks.
// Every visual event registers an SFX cue (see _sfx; same convention as hook_a.js / hook_b.js).
import { bedroom, BEDROOM, bedroomSun, bird, street, STREET } from '../sets.js';
import { hallway, hallwaySun, HALL, space, spaceGlow, SPACE } from '../sets2.js';
import * as U from '../ui.js';
import * as U2 from '../ui2.js';
import { FONT, Defs, text, rect, circle, ellipse, path, poly, line, g, rrPath, gearPath, shade, ink, st } from '../ui_style.js';
import { sparkle, sparkles, speedLines, shockRing, starburst, sunFlare, whiteout, boxBlur } from '../fx.js';
import { clamp, lerp, seg, ease, rng } from '../anim/motion.js';
import { posePreset } from '../cast.js';
import { PAL, stroke as lineOf } from '../style.js';
import { anticPose } from '../anim/actor.js';

// =====================================================================================================================
// shared helpers (private: names starting with _ are not registered as shots)
// =====================================================================================================================
const FPS = 60, FR = 1 / FPS;
const r2 = (n) => Math.round(n * 100) / 100, r3 = (n) => Math.round(n * 1000) / 1000;
// ui_style attrs() rounds every NUMERIC attribute to 0.1, so an animated opacity passed as a number moves in 10 % steps;
// pass animated opacities as strings (attrs keeps strings verbatim)
const op3 = (v) => String(r3(clamp(v)));
const NUN = (size, weight = 900, fill = '#FFFFFF', extra = {}) => ({ fontFamily: FONT.ui, fontWeight: weight, fontSize: size, fill, ...extra });
const LIL = (size, fill = '#FFFFFF', extra = {}) => ({ fontFamily: FONT.title, fontSize: size, fill, ...extra });

// sync points (ms into the clip) of the audio/sfx_map.json variants used here: a cue's t is the clip START, chosen so
// the sound's sync point lands on the visual frame (ev, global s). Synthesised names (flash_whoomp, ...) sync at 0.
const SYNC = {
  ui_tap: [2.5, 2.5, 30, 7.5, 7.5, 7.5], ui_select: [10, 10, 22.5, 30, 45], ui_confirm: [2.5, 7.5], slider_tick: [2.5, 7.5, 12.5, 12.5, 10],
  slider_drag: [5, 7.5, 7.5, 7.5, 10], toggle: [37.5, 12.5, 12.5, 20, 12.5, 35], notif_ping: [5, 2.5, 12.5, 17.5, 2.5, 7.5, 7.5],
  success_chime: [2.5, 7.5, 15, 10, 10, 7.5], popup_whoosh: [207.5, 115, 87.5, 135, 240, 10], magic_shimmer: [2.5, 1515, 5, 10],
  whoosh_short: [250, 270, 277.5, 275, 337.5, 347.5, 277.5, 812.5, 637.5, 710, 737.5], whoosh_long: [327.5, 2562.5],
  swish: [47.5, 65, 60, 130, 125, 17.5], impact_hit: [7.5, 140, 42.5, 2.5], sub_boom: [2.5, 22.5, 252.5, 57.5], riser: [1390, 1525, 3175, 2805, 13745, 2512.5],
  cartoon_pop: [10, 22.5, 10, 10, 7.5, 10, 12.5, 10, 140], door_slam: [110, 10, 2.5], slide_whistle_down: [37.5, 35, 37.5, 35],
  morning_birds: [32.5, 30, 10], boing: [45, 5, 10, 15, 15, 7.5, 7.5, 15, 7.5], yawn: [240, 57.5, 32.5],
};
/** register an SFX cue whose sync point hits local time tEv (call unconditionally: cues are collected at the shot start).
 *  o: {db (level hint vs the -18 LUFS map level), dur (trim in s), note} */
function _sfx(ctx, name, v, tEv, o = {}) {
  const tbl = SYNC[name], sm = tbl ? tbl[v % tbl.length] : 0;
  ctx.cue(name, tEv - sm / 1000, { v, ev: r3(ctx.start + tEv), sync_ms: sm, ...o });
}
/** a word's local start (or the fallback when the line is missing) */
const _at = (L, w, d, n = 0) => (L && L.word(w, n) ? L.at(w, n) : d);
const _end = (L, d) => (L && L.words.length ? L.words[L.words.length - 1].t1 : d);
/** a timeline sync point in local time */
const _sync = (ctx, k, d) => (ctx.T.sync && ctx.T.sync[k] !== undefined ? ctx.T.sync[k] - ctx.start : d);

/** camera offset {x, y} that puts world point P (on a layer of depth d) at screen point S at zoom z (no roll) */
const _frame = (P, z, S = [960, 540], d = 1) => ({ x: (P[0] - 960 - (S[0] - 960) / z) / d, y: (P[1] - 540 - (S[1] - 540) / z) / d, z });
/** numeric pose blend (non-number fields come from b once u passes 0.5) */
function _lerpPose(a, b, u) {
  const o = {};
  for (const k of new Set([...Object.keys(a), ...Object.keys(b)])) {
    const x = a[k], y = b[k];
    o[k] = typeof x === 'number' && typeof y === 'number' ? lerp(x, y, u) : (u < 0.5 ? (x ?? y) : (y ?? x));
  }
  return o;
}
/** a decaying 0..1 pulse: rises over `up` s from t0, then decays exp(-dt/tau) */
const _pulse = (t, t0, tau = 0.12, up = 1 / 60) => (t < t0 ? 0 : t < t0 + up ? (t - t0) / up : Math.exp(-(t - t0 - up) / tau));
/** draw fn(tt) a few times over the last `shutter` frames (oldest first, opacity 1, 1/2, 1/3 ... = an equal average):
 *  the camera's ghosting for compositions that cam.render() does not cover (screen-scaled layers) */
function _ghost(fn, t, n, shutter = 0.6) {
  if (n <= 1) return fn(t);
  let out = '';
  for (let k = 0; k < n; k++) {
    const tt = t - (shutter / FPS) * (1 - k / (n - 1));
    out += k === 0 ? fn(tt) : `<g opacity="${r3(1 / (k + 1))}">${fn(tt)}</g>`;
  }
  return out;
}
/** a burst of 4-point sparkles flying out of (cx, cy) and fading; u = seconds since the burst */
function _burst(cx, cy, u, o = {}) {
  const dur = o.dur ?? 0.45;
  if (u <= 0 || u >= dur) return '';
  const R = rng(o.seed ?? 3), n = o.n ?? 10, k = u / dur, e = ease.outCubic(k);
  let s = '';
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2 + (R() - 0.5) * 0.6, dist = (o.r ?? 160) * (0.55 + R() * 0.6) * e;
    const sz = (o.size ?? 26) * (0.6 + R() * 0.7) * (1 - k * 0.7);
    s += sparkle(cx + Math.cos(a) * dist, cy + Math.sin(a) * dist, sz, i % 3 ? '#FFFFFF' : (o.alt || '#FFF2A8'), 1 - k, u * 200 * (R() - 0.5));
  }
  return s;
}

// character looks (palette remaps from cast.js; no filters)
const NIGHT_TINT = { color: '#5562A4', k: 0.55 }, NIGHT_LIGHT = { color: '#CFE8FF', k: 0.85, from: 'phone' };
const SUN_TINT = { color: '#FFF3DC', k: 0.16 }, SUN_LIGHT = { color: '#FFF8E0', k: 0.5, from: 'right' };

// ---------- the bedroom ----------
// the set with the 'sit' blanket and the branch outside; per frame the window view (windowSun, also at sun 0) is
// inserted at the wall's depth (0.75) instead of the set's own far layer (0.3), so the moon / sun never slides behind
// the wall when the camera frames the window
const BED_SET = () => bedroom({ blanket: 'sit', clock: '2:13', birds: true });
const BIRD_COLS = [['#4FA8F0', '#FFE6C4'], ['#FFC23D', '#FFF2C8'], ['#F2645A', '#FFE0CC']];
/** the three birds on the branch, each with its own state {awake, sing, flap, notes} (functions of the bird index) */
function _birds(stt, night) {
  let s = '';
  BEDROOM.birds.forEach(([x, y, dir], i) => {
    const b = stt(i);
    s += bird(x, y, b.flap || 0, { s: 1.15, dir, color: BIRD_COLS[i][0], belly: BIRD_COLS[i][1], awake: b.awake ?? 0, sing: b.sing ?? 0, notes: b.notes || 0, night, seed: i + 1 });
  });
  return s;
}
/** bedroom through the camera. o: sun 0..1, sam (actor svg), birds (svg), phoneGlow (keep the set's phone light) */
function _bedWorld(ctx, cam, o = {}) {
  const set = ctx.memo('hook_d/bed', BED_SET);
  const sun = clamp(o.sun ?? 0), L = bedroomSun(sun, { birds: true });
  // (inserts after a skipped layer are dropped with it, so the view hangs off 'defs', the first layer)
  const ins = [{ after: 'defs', depth: 0.75, svg: L[0].svg }];
  if (o.birds) ins.push({ after: 'defs', depth: 0.75, svg: o.birds });
  if (o.sam) ins.push({ after: 'mid', depth: 0.75, svg: o.sam });
  ins.push({ after: 'near', depth: 0.75, svg: L[1].svg }, { after: 'near', depth: 0, svg: L[2].svg });
  for (const a of o.after || []) ins.push({ after: 'top', ...a });
  const skip = ['far', 'birds', 'grade'];
  if (o.phoneGlow === false) skip.push('phone');
  return cam.set(set, { skip, insert: ins });
}
const SAM_BED = { x: BEDROOM.sam.x, y: BEDROOM.sam.y, s: BEDROOM.sam.s, legs: false, props: { R: 'phoneBack' } };

// =====================================================================================================================
// C10 — SYS "Welcome to Reality Settings!" The toast drops in on the Gotta Catch downbeat over the night street (C9's
// camera lands on C10_F0, so the cut is invisible), a settings wave sweeps the houses, gear badges pop over the three
// roofs, the gear glows on "Settings" and the install bar fills by the end of the line.
// =====================================================================================================================
const C10_F0 = { x: -330, y: -46, z: 1.12 };
const C10_BADGES = [[265, 318, 0], [808, 352, 1], [1370, 392, 2]];      // on the roofs (mid layer, depth .75) + stagger
const NIGHT_STREET = () => street({ night: 1, split: true });
export function C10_welcome(ctx) {
  const t = ctx.t, L = ctx.line('S00-L017');
  const tLand = _sync(ctx, 'TOAST', 0.15);                               // the music downbeat
  const tSet = _at(L, 'Settings', 1.27), tEnd = _end(L, 1.70);
  const tDrop = tLand - 0.115;                                           // the toast's drop starts 7 frames earlier
  const tB = C10_BADGES.map((b) => tLand + 0.1 + b[2] * 0.07), tLife = [tLand + 0.12, tEnd - 0.06];
  // ---- SFX
  _sfx(ctx, 'popup_whoosh', 1, tLand, { note: 'toast drops in (peak on the land)' });
  _sfx(ctx, 'success_chime', 0, tLand, { note: 'toast lands on the Gotta Catch downbeat' });
  _sfx(ctx, 'magic_shimmer', 0, tLand + 0.03, { db: -8, note: 'settings wave sweeps the street' });
  tB.forEach((tb, i) => _sfx(ctx, 'cartoon_pop', [0, 2, 4][i], tb, { db: -6, note: `gear badge pops over roof ${i + 1}` }));
  _sfx(ctx, 'magic_shimmer', 2, tSet, { db: -4, note: "the gear glows on 'Settings'" });
  _sfx(ctx, 'ui_confirm', 0, tLife[1], { db: -8, note: 'install bar full' });
  _sfx(ctx, 'swish', 4, 1.36, { db: -12, note: 'badges pop away' });
  // ---- camera: gentle push toward Sam's house, a small thump on the land
  const cam = ctx.cam({
    keys: [[0, C10_F0], [ctx.dur, { x: C10_F0.x - 20, y: C10_F0.y - 4, z: C10_F0.z * 1.045 }, 'inOutSine']],
    shake: [{ t: tLand, amp: 7, decay: 0.07 }, { t: tSet, amp: 3, decay: 0.06 }], drift: 5,
  });
  // gear badges above the roofs (world, depth .75): pop, spin, then pop away
  let badges = '';
  C10_BADGES.forEach(([bx, by], i) => {
    const tb = tB[i];
    if (t < tb) return;
    const p = seg(t, tb, tb + 8 * FR), out = ease.inBack(seg(t, 1.36 + i * 0.03, 1.36 + i * 0.03 + 7 * FR));
    if (out >= 1) return;
    const k = (1 - out) * (p < 1 ? ease.outBack(p) : 1), bob = 5 * Math.sin(2 * Math.PI * 1.6 * (t - tb));
    const chk = circle(28, 28, 16, { fill: U.UI.green, stroke: ink(U.UI.green), strokeWidth: 3 }) + path('M18 28L25 35L38 20', { fill: 'none', ...st('#FFFFFF', 5.5) });
    badges += g(circle(0, 0, 64, { fill: '#FFB070', opacity: 0.25 }) + U.logo(0, 0, 40, { rot: (t - tb) * 120, glow: false }) + chk,
      { transform: `translate(${r2(bx)} ${r2(by + bob)}) scale(${r3(Math.max(0.001, k))})` });
    badges += _burst(bx, by, t - tb, { n: 8, r: 90, size: 16, seed: 20 + i, dur: 0.38 });
  });
  // the street (C9's camera eases into C10_F0 by the cut, so the move is continuous) + the settings wave on the downbeat
  let world = cam.set(ctx.memo('hook_d/night_street', NIGHT_STREET), { insert: [{ after: 'near', depth: 0.75, svg: badges }] });
  const wv = seg(t, tLand, tLand + 0.5);
  if (wv > 0 && wv < 1) {
    const d = new Defs(), wx = lerp(-300, 2300, ease.inOutSine(wv)), op = Math.sin(Math.PI * wv);
    world += rect(wx - 260, -40, 520, 1160, { fill: d.lin([[0, '#7FE8FF', 0], [0.5, '#BFF6FF', 0.34 * op], [1, '#7FE8FF', 0]], 'h') });
    world += String(d) + sparkles({ x: wx - 420, y: 220, w: 360, h: 560, count: 10, seed: 41, t: t * 3, size: 20, colors: ['#FFFFFF', '#BFF6FF'] });
  }
  // ---- the toast (screen space): drops from above, crosses its place on the downbeat, overshoots, settles
  const S = 1.22, sub = 'Every setting. For {real life|orange}.';
  const w = U2.welcomeToastWidth({ sub }), x0 = 960 - (w * S) / 2, yRest = 64;
  if (t >= tDrop) {
    const u = seg(t, tDrop, tDrop + 0.3), e = ease.outBack(u), y = lerp(-230, yRest, e);
    const sq = t >= tLand ? 0.07 * Math.exp(-(t - tLand) / 0.06) * Math.cos(2 * Math.PI * 7 * (t - tLand)) : 0;
    const gl = clamp(0.55 + 0.45 * seg(t, tLand, tLand + 0.2) + 0.5 * _pulse(t, tSet, 0.25, 3 * FR));
    const life = ease.inOutSine(seg(t, tLife[0], tLife[1]));
    let toast = U2.welcomeToast({ x: 0, y: 0, sub, t, glow: gl, slide: 1, life });
    // the gear's glow burst on "Settings": ring + sparkles round the logo (toast space)
    const ix = 74, iy = 72, gu = t - tSet;
    if (gu > 0 && gu < 0.5) toast += shockRing(ix, iy, 190, gu / 0.45, '#FFE0B0', 12) + _burst(ix, iy, gu, { n: 9, r: 150, size: 20, seed: 9 });
    const cx = x0 + (w * S) / 2, cy = y + 72 * S;
    // squash about the toast centre on the land (scaleX up, scaleY down)
    const k = S * (1 + sq), ky = S * (1 - sq);
    world += cam.screen(g(toast, { transform: `translate(${r2(cx)} ${r2(cy)}) scale(${r3(k)} ${r3(ky)}) translate(${r2(-w / 2)} -72)` }), { shake: true });
  }
  return world;
}

// =====================================================================================================================
// C11 — SAM "Prove it." Mid-yawn: one arm stretched up, head back, eyes shut, the "Prove" yawned out; on "it" the arm
// drops and he settles into bored half-lids at the phone. Phone-lit night look.
// =====================================================================================================================
export function C11_proveit(ctx) {
  const t = ctx.t, L = ctx.line('S00-L018');
  const tP = _at(L, 'Prove', 0.2), tIt = _at(L, 'it', 0.76), tEnd = _end(L, 1.53);
  const tDrop = tIt - 0.1;
  _sfx(ctx, 'swish', 5, 0.02, { db: -12, note: 'blanket rustle under the stretch (cut transient)' });
  _sfx(ctx, 'swish', 2, tDrop + 4 * FR, { db: -8, note: 'stretching arm flops down' });
  _sfx(ctx, 'boing', 6, tDrop + 7 * FR, { db: -16, note: 'tiny mattress spring as he slumps' });
  _sfx(ctx, 'yawn', 1, tP - 0.04, { db: -16, pitch_st: 4, note: 'optional: library yawn pitched up 4 st under the yawned "Prove" (the VO carries it)' });
  const F0 = _frame([BEDROOM.sam.x, 500], 2.0, [960, 436], 0.75);
  const cam = ctx.cam({ keys: [[0, F0], [ctx.dur, { ...F0, x: F0.x + 3, z: F0.z * 1.03 }, 'inOutSine']], drift: 3 });
  // the yawned "Prooove": keep the mouth round (v_A / v_E -> v_O) inside that word, normal lip-sync on "it"
  const yawnTalk = L ? { words: L.words, dur: L.end, visemes: L.visemes.map(([tt, vv]) => [tt, tt < tIt - 0.02 && (vv === 'v_A' || vv === 'v_E') ? 'v_O' : vv]) } : 'S00-L018';
  const base = posePreset('bedSit', 'sam');
  const Pyawn = { ...base, armL: 150, foreL: -16, handL: 'fist', head: -7, lean: -6, shrug: 0.5 };
  const Pyawn2 = { ...base, armL: 156, foreL: -24, handL: 'fist', head: -9, lean: -8, shrug: 0.7 };
  const Pbored = { ...base, head: 4, lean: -2, shrug: 0 };
  const Pbored2 = { ...base, head: 6, lean: -1, shrug: 0.15 };
  const pose = [[0, Pyawn], [tP, Pyawn2, 'inOutSine', 0.4], ...anticPose(tDrop, Pyawn2, Pbored, { wind: 3, dur: 8 }), [tEnd - 0.1, Pbored2, 'inOutSine', 0.25]];
  const sam = ctx.actor('sam', {
    ...SAM_BED, facing: [[0, -6], [tIt, 6]],
    face: [[0, { preset: 'yawn' }], [tP, { preset: 'yawn', brows: 'flat' }, 0], [tIt, { preset: 'bored', look: [1.5, 3.2] }], [tEnd + 0.06, { preset: 'bored', lid: 0.22, look: [2, 3.6] }, 0.5]],
    talk: yawnTalk, talkScale: 1.1, pose, squash: [[tDrop + 6 * FR, 0.05]],
    tint: NIGHT_TINT, light: NIGHT_LIGHT, blink: { seed: 11 },
  });
  return _bedWorld(ctx, cam, { sun: 0, sam, birds: _birds(() => ({ awake: 0 }), 1) });
}

// =====================================================================================================================
// C12 — N "You open Brightness." POV in bed: the Display list, the thumb taps Brightness ("open"), the card pops, and on
// "Brightness" a 7-frame snap zoom into the slider hands over to the full-frame Brightness page (it grows out of the
// phone's slider along the same zoom, crossfading inside the ghosted frames).
// =====================================================================================================================
const C12_P = { x: 1010, y: 600, s: 0.6, rot: -5 };                     // the POV phone of hook_c (C3/C4/C8)
const BRIGHT_UI = { x: 150, y: 660, w: 1620, endR: 58 };                 // the full-frame slider (rail centre y)
const _brightKnob = (v) => U2.bigSliderKnob({ ...BRIGHT_UI, v });
const BRIGHT_V0 = 0.2;
/** the full-frame Brightness page (frame space): app header, title + sub on the left, the sun icon on the right swelling
 *  and spinning with v, the big sun-knob slider with a value bubble, stops. Leaves 860-1080 free for the POV caption. */
function _brightPage(v, t, o = {}) {
  const d = new Defs();
  let c = '';
  // title block
  c += text(150, 368, 'Brightness', LIL(118, '#FFFFFF', { stroke: '#0B1030', strokeWidth: 10, paintOrder: 'stroke', strokeLinejoin: 'round' }));
  c += text(156, 430, U.rich('Applies to: {everything|orange}'), NUN(40, 800, U.UI.sub));
  // the sun icon (grows with v; o.flare adds a hot pulse)
  const sx = 1420, sy = 330, sr = (78 + 110 * v) * (1 + 0.08 * (o.flare || 0)), fl = o.flare || 0;
  c += circle(sx, sy, sr * 2.7, { fill: d.rad([[0, '#FFE36A', 0.5 * v + 0.12 + 0.3 * fl], [1, '#FFE36A', 0]]) });
  for (let i = 0; i < 12; i++) {
    const a = (i / 12) * Math.PI * 2 + t * 0.7 + v * 1.5, r0 = sr * 1.22, r1 = sr * (1.55 + 0.4 * v + 0.15 * fl);
    c += line(sx + Math.cos(a) * r0, sy + Math.sin(a) * r0, sx + Math.cos(a) * r1, sy + Math.sin(a) * r1, { ...st(i % 2 ? '#FFF3B0' : '#FFD43B', sr * 0.17) });
  }
  c += circle(sx, sy + sr * 0.08, sr, { fill: '#B8650A', opacity: 0.45 });
  c += circle(sx, sy, sr, { fill: d.lin(['#FFF8C4', '#FFD43B', '#FFA21F']), stroke: ink('#FFC23D'), strokeWidth: 5 });
  c += ellipse(sx - sr * 0.32, sy - sr * 0.42, sr * 0.36, sr * 0.15, { fill: '#FFFFFF', opacity: 0.85, transform: `rotate(-25 ${r2(sx - sr * 0.32)} ${r2(sy - sr * 0.42)})` });
  // a little face on the sun icon (it is about to become real)
  c += circle(sx - sr * 0.3, sy - sr * 0.02, sr * 0.08, { fill: '#7A3A00' }) + circle(sx + sr * 0.3, sy - sr * 0.02, sr * 0.08, { fill: '#7A3A00' });
  c += path(`M${r2(sx - sr * 0.22)} ${r2(sy + sr * 0.22)}Q${r2(sx)} ${r2(sy + sr * 0.42)} ${r2(sx + sr * 0.22)} ${r2(sy + sr * 0.22)}`, { fill: 'none', ...st('#7A3A00', sr * 0.07) });
  // the slider (bubble = value) + stops
  c += U2.bigSlider({ ...BRIGHT_UI, v, iconL: 'sunSmall', iconR: 'sunBig', iconLs: 0.5, iconRs: 0.62, color: '#FFB21F', color2: '#FFF3A0', knobR: 92, railH: 64, knob: 'sun', rot: t * 40, ticks: 10, grab: o.grab ?? 0,
    bubble: `${Math.round(v * 100)}%`, bubbleSize: 50, bubbleK: o.bubbleK ?? 1, stops: ['Night', 'Day', 'MAX'], stopSize: 34 });
  let s = U2.insideApp(c, { t, time: '2:13', header: true, crumb: 'Settings › {Display|purple}', glare: 0.5, bg: { glow: '#FFC23D' } });
  if (o.wash > 0.004) s += rect(-20, -20, 1960, 1120, { fill: d.rad([[0, '#FFF6D8', o.wash], [1, '#FFE9B0', o.wash * 0.4]], 0.74, 0.3, 0.9) });
  return d + s;
}
/** the Display list on the phone screen (SCREEN space, below the header): Brightness row (pressed with k) + 3 rows */
function _displayList(press = 0) {
  let s = text(36, 300, 'DISPLAY', NUN(26, 900, U.UI.dim, { letterSpacing: 3 }));
  s += U.row({ x: 24, y: 326, w: U2.SCREEN.w - 48, cat: 'sun', label: 'Brightness', icon: 'brightness', color: '#FFAE1F', value: '{20%|yellow}', selected: press > 0 });
  if (press > 0) s += path(rrPath(24, 326, U2.SCREEN.w - 48, 104, 30), { fill: '#FFFFFF', opacity: op3(0.18 * press) });
  s += U.row({ x: 24, y: 452, w: U2.SCREEN.w - 48, kind: 'toggle', cat: 'bedtime', label: 'Night mode', icon: 'moon', color: '#5C5CE0', k: 1 });
  s += U.row({ x: 24, y: 578, w: U2.SCREEN.w - 48, cat: 'weather', value: 'Clear' });
  s += U.row({ x: 24, y: 704, w: U2.SCREEN.w - 48, cat: 'volume', kind: 'toggle', k: 0 });
  s += U.row({ x: 24, y: 830, w: U2.SCREEN.w - 48, cat: 'gravity', value: 'Earth' });
  return s;
}
/** the night bedroom seen past the phone (POV), framed and blurred like hook_c's C3/C8 (window + moon right of the
 *  phone), plus the blanket over the knees in the lower left (the same shape as hook_c's) */
function _povRoom(ctx, z = 1) {
  const set = ctx.memo('hook_d/bed', BED_SET);
  const cam = ctx.cam({ keys: [[0, { x: 330, y: -30, z: 1.12 * z }]], drift: 0, blur: false, ghost: false });
  const L = bedroomSun(0, { birds: true });
  let s = cam.set(set, { skip: ['far', 'birds', 'grade', 'blanket'], insert: [{ after: 'defs', depth: 0.75, svg: L[0].svg }, { after: 'defs', depth: 0.75, svg: _birds(() => ({ awake: 0 }), 1) }, { after: 'near', depth: 0, svg: L[2].svg }] });
  s = boxBlur(s, { x: -60, y: -60, w: 2040, h: 1200, sdx: 7, sdy: 7 });
  const d = new Defs(), bl = '#2F4FB8';
  const body = 'M-80 1180L-80 930C40 820 250 760 430 790C600 820 700 900 760 1000C790 1060 800 1120 800 1180Z';
  let kn = path(body, { fill: d.lin([shade(bl, 0.07), shade(bl, -0.1)], 'd'), stroke: ink(bl), strokeWidth: 6, strokeLinejoin: 'round' });
  kn += g(rect(-100, 740, 920, 460, { fill: d.pattern(150, 120, path(gearPath(36, 36, 19, 13, 8, 0, 0.5), { fill: '#5A7AE0', opacity: 0.5 }) + circle(36, 36, 6, { fill: bl })) }), { clipPath: d.clip(path(body)) });
  kn += path('M60 900C180 830 320 806 450 822', { fill: 'none', ...st('#FFFFFF', 14), opacity: 0.18 });
  kn += path('M200 1100C300 1010 470 980 620 1040', { fill: 'none', ...st(shade(bl, -0.18), 10), opacity: 0.4 });
  kn += ellipse(560, 960, 380, 170, { fill: d.rad([[0, '#9FE0FF', 0.28], [1, '#9FE0FF', 0]]) });
  return s + String(d) + g(kn, { transform: `translate(${r2(-40 * (z - 1))} ${r2(60 * (z - 1))}) ` });
}
/** the hand-held phone at night (POV): the hand and bezel darkened by a navy veil with a hole for the screen */
function _nightPhone(P, screen, thumb) {
  let s = U2.phone({ ...P, screen, thumb, glow: 0.85, glowColor: '#BFE3FF' });
  // a slight violet night wash over the hand and the phone body only (big rect minus the screen, evenodd)
  const sw = U2.SCREEN.w * P.s, sh = U2.SCREEN.h * P.s, inner = rrPath(-sw / 2, -sh / 2, sw, sh, U2.SCREEN.r * P.s);
  s += `<g transform="translate(${r2(P.x)} ${r2(P.y)}) rotate(${P.rot || 0})"><path fill-rule="evenodd" d="M-2400 -2400H2400V2400H-2400Z${inner}" fill="#2A2660" opacity="0.12"/></g>`;
  return s;
}
export function C12_brightness(ctx) {
  const t = ctx.t, L = ctx.line('S00-L019');
  const tOpen = _at(L, 'open', 0.32), tBr = _at(L, 'Brightness', 0.64);
  const tTap = tOpen + 2 * FR, tCard = tTap + 4 * FR, tSnap = tBr - 3 * FR, nSnap = 7;
  _sfx(ctx, 'swish', 0, 0.03, { db: -10, note: 'phone lifts into view (cut transient)' });
  _sfx(ctx, 'ui_tap', 3, tTap, { note: 'thumb taps the Brightness row' });
  _sfx(ctx, 'popup_whoosh', 2, tCard + 3 * FR, { db: -4, note: 'Brightness card pops' });
  _sfx(ctx, 'whoosh_short', 2, tSnap + 2 * FR, { db: -2, note: 'snap zoom into the slider (peak mid-snap)' });
  _sfx(ctx, 'ui_select', 0, tSnap + nSnap * FR, { db: -6, note: 'the full-frame page lands' });
  const P = { ...C12_P, rot: C12_P.rot };
  // phone screen state
  const scrAt = (tt) => {
    if (tt < tCard) {
      const pr = tt >= tTap ? Math.sin(Math.PI * seg(tt, tTap - 2 * FR, tTap + 6 * FR)) : 0;
      const mv = ease.inOutCubic(seg(tt, tTap + 3 * FR, tTap + 14 * FR));
      return { svg: U2.appScreen({ time: '2:13', crumb: 'Settings › {Display|purple}', content: _displayList(pr) }), thumb: { x: lerp(470, 600, mv), y: lerp(384 + 30 * (1 - seg(tt, 0, tTap)), 900, mv), press: pr } };
    }
    const B = U2.brightnessScreen({ v: BRIGHT_V0, grab: 0, t: tt, night: 1 });
    const pp = seg(tt, tCard, tCard + 8 * FR);
    // the thumb lifts off the row and drifts down out of the card's way (no jump)
    const mv = ease.inOutCubic(seg(tt, tTap + 3 * FR, tTap + 14 * FR));
    return { svg: U2.appScreen({ time: '2:13', crumb: 'Settings › {Display|purple} › {Brightness|yellow}', content: B.svg }), thumb: { x: lerp(470, 600, mv), y: lerp(384, 900, mv) + 40 * seg(tt, tTap + 14 * FR, tTap + 0.45), press: 0 }, card: pp };
  };
  // phone knob (frame) and the full page knob: the snap carries one onto the other
  const card = { x: 24, y: 326, w: U2.SCREEN.w - 48, v: BRIGHT_V0 };
  const kS = U2.settingCardKnob(card), kP = U2.phonePoint(P, kS[0], kS[1]), kF = _brightKnob(BRIGHT_V0);
  const railP = (416 * P.s), railF = 1344, Z1 = railF / railP;
  const snapE = (tt) => ease.outExpo(seg(tt, tSnap, tSnap + nSnap * FR));
  // one composed frame at time tt (used directly, or several times for the ghosted snap frames)
  const F = (tt) => {
    const e = snapE(tt), z = Math.exp(Math.log(Z1) * e), rr = -P.rot * e;
    const at = [lerp(kP[0], kF[0], e), lerp(kP[1], kF[1], e)];
    const push = 1 + 0.025 * ease.inOutSine(seg(tt, 0, tSnap));               // slow push before the snap
    let s = '';
    if (e < 0.999) {
      s += _povRoom(ctx, push * Math.exp(Math.log(Z1) * e * 0.35));
      const S = scrAt(tt);
      let ph = _nightPhone(P, S.svg, S.thumb);
      if (S.card !== undefined && S.card < 1) {
        // the card's pop ring over the screen (screen-space approximation of settingCard's popIn)
        const cc = U2.phonePoint(P, U2.SCREEN.w / 2, 516), pp = S.card;
        ph += shockRing(cc[0], cc[1], 360 * P.s * 1.3, pp, '#FFFFFF', 10);
      }
      const m = `translate(${r2(at[0])} ${r2(at[1])}) rotate(${r2(rr)}) scale(${r3(z * push)}) translate(${r2(-kP[0])} ${r2(-kP[1])})`;
      s += g(ph, { transform: m });
    }
    // the full page grows out of the phone's slider along the same zoom
    const a = e < 0.999 ? seg(e, 0.55, 0.93) : 1;
    if (a > 0) {
      const k2 = z / Z1, m2 = `translate(${r2(at[0])} ${r2(at[1])}) rotate(${r2(rr + P.rot)}) scale(${r3(k2)}) translate(${r2(-kF[0])} ${r2(-kF[1])})`;
      const page = rect(-2600, -2200, 7120, 5480, { fill: U.UI.navy1 }) + _brightPage(BRIGHT_V0, tt, { bubbleK: seg(tt, tSnap + nSnap * FR, tSnap + nSnap * FR + 8 * FR) });
      s += g(page, { transform: m2, opacity: a < 1 ? op3(a) : undefined });
    }
    return s;
  };
  const inSnap = t >= tSnap && t < tSnap + nSnap * FR;
  if (inSnap) return _ghost(F, t, 4, 0.45);
  if (t < tSnap) return F(t);
  // after the snap: the page alone with a slow push toward the knob and a soft settle
  const cam = ctx.cam({ keys: [[tSnap + nSnap * FR, { x: 0, y: 0, z: 1 }], [ctx.dur + 0.2, { x: 0, y: 0, z: 1.035 }, 'inOutSine']], drift: 2,
    shake: [{ t: tSnap + nSnap * FR, amp: 6, decay: 0.06 }] });
  return cam.layer(_brightPage(BRIGHT_V0, t, { bubbleK: seg(t, tSnap + nSnap * FR, tSnap + nSnap * FR + 8 * FR) }), 1);
}

// =====================================================================================================================
// C13 — "Slide it up." The big thumb lands on the sun knob, drags it 20% -> 35% (a tick every 5%), the sun icon swells;
// punch-in on "up"; the riser for the flare starts here.
// =====================================================================================================================
/** a big POV thumb (frame space), mitten-shaped like ui2.phone()'s: the tip at `tip`, the thumb running back to its
 *  root at `root`, the heel of the palm and the hoodie cuff behind it (mostly off the lower right of the frame) */
function _bigThumb(tip, o = {}) {
  const d = new Defs(), skin = PAL.skinCool, ln = lineOf(skin), sw = 9, press = clamp(o.press || 0);
  const root = o.root || [tip[0] + 640, tip[1] + 250], R1 = o.r1 ?? 106, R2 = (o.r2 ?? 92) * (1 + 0.06 * press);
  const dx = tip[0] - root[0], dy = tip[1] - root[1], D = Math.hypot(dx, dy) || 1, ux = dx / D, uy = dy / D, nx = -uy, ny = ux;
  const knu = [root[0] + dx * 0.5 - nx * 22, root[1] + dy * 0.5 - ny * 22];
  const cap = (a, b, ra, rb) => {
    const ex = b[0] - a[0], ey = b[1] - a[1], LL = Math.hypot(ex, ey) || 1, vx = ex / LL, vy = ey / LL, px = -vy, py = vx;
    return `M${r2(a[0] + px * ra)} ${r2(a[1] + py * ra)}L${r2(b[0] + px * rb)} ${r2(b[1] + py * rb)}A${r2(rb)} ${r2(rb)} 0 0 0 ${r2(b[0] - px * rb)} ${r2(b[1] - py * rb)}L${r2(a[0] - px * ra)} ${r2(a[1] - py * ra)}A${r2(ra)} ${r2(ra)} 0 0 0 ${r2(a[0] + px * ra)} ${r2(a[1] + py * ra)}Z`;
  };
  const ell = (cx, cy, rx, ry, rot) => {
    const a = (rot * Math.PI) / 180, c = Math.cos(a), sn = Math.sin(a), P = (u, v) => `${r2(cx + u * c - v * sn)} ${r2(cy + u * sn + v * c)}`;
    return `M${P(-rx, 0)}A${r2(rx)} ${r2(ry)} ${r2(rot)} 1 0 ${P(rx, 0)}A${r2(rx)} ${r2(ry)} ${r2(rot)} 1 0 ${P(-rx, 0)}Z`;
  };
  const prox = cap(root, knu, R1 + 12, R1), dist = cap(knu, tip, R1 - 6, R2);
  const palm = ell(root[0] + 120, root[1] + 150, 250, 190, -24);
  const fill = d.lin([shade(skin, 0.05), shade(skin, -0.08)], 'd'), hood = PAL.samHoodie;
  let s = '';
  if (press > 0.02) s += ellipse(tip[0] - 10, tip[1] + 12, R2 * 1.3, R2 * 0.95, { fill: '#0A0F2A', opacity: op3(0.25 * press) });
  // hoodie cuff behind the palm, running off the lower right corner
  s += path(cap([root[0] + 520, root[1] + 520], [root[0] + 230, root[1] + 260], 260, 240), { fill: d.lin([shade(hood, 0.04), shade(hood, -0.08)], 'd'), stroke: lineOf(hood), strokeWidth: sw });
  for (const dd of [palm, prox, dist]) s += path(dd, { fill: ln, stroke: ln, strokeWidth: sw * 2, strokeLinejoin: 'round' });
  for (const dd of [palm, prox, dist]) s += path(dd, { fill });
  // knuckle crease, a gloss strip along the upper edge of the thumb, a soft sheen on the palm
  const ang = Math.atan2(tip[1] - knu[1], tip[0] - knu[0]), na = ang - Math.PI / 2;
  s += path(`M${r2(knu[0] + Math.cos(na) * R1 * 0.72)} ${r2(knu[1] + Math.sin(na) * R1 * 0.72)}Q${r2(knu[0] + Math.cos(ang) * 24 + Math.cos(na) * 20)} ${r2(knu[1] + Math.sin(ang) * 24 + Math.sin(na) * 20)} ${r2(knu[0] + Math.cos(na) * 8)} ${r2(knu[1] + Math.sin(na) * 8)}`, { fill: 'none', stroke: ln, strokeWidth: 6, strokeLinecap: 'round', opacity: 0.6 });
  const g0 = [knu[0] - Math.cos(ang) * 40 + Math.cos(na) * R1 * 0.52, knu[1] - Math.sin(ang) * 40 + Math.sin(na) * R1 * 0.52];
  const g1 = [tip[0] - Math.cos(ang) * R2 * 0.55 + Math.cos(na) * R2 * 0.48, tip[1] - Math.sin(ang) * R2 * 0.55 + Math.sin(na) * R2 * 0.48];
  s += path(`M${r2(g0[0])} ${r2(g0[1])}L${r2(g1[0])} ${r2(g1[1])}`, { fill: 'none', stroke: '#FFFFFF', strokeWidth: 20, strokeLinecap: 'round', opacity: 0.42 });
  s += path(ell(root[0] + 60, root[1] + 70, 110, 60, -24), { fill: '#FFFFFF', opacity: 0.16 });
  if (o.light) s += path(dist, { fill: '#FFF2C0', opacity: op3(0.25 * o.light) });
  return d + s;
}
export function C13_slide(ctx) {
  const t = ctx.t, L = ctx.line('S00-L020');
  const tSl = _at(L, 'Slide', 0.15), tUp = _at(L, 'up', 0.91);
  const tLand = 0.1, tD0 = tSl + 3 * FR, tD1 = tUp + 3 * FR, V1 = 0.35;
  const flare = _sync(ctx, 'FLARE', 1.953);
  const vAt = (tt) => {
    if (tt < tD0) return BRIGHT_V0;
    const u = seg(tt, tD0, tD1);
    return lerp(BRIGHT_V0, V1, ease.inOutSine(u)) + 0.012 * Math.sin(Math.PI * seg(tt, tD1 - 0.08, tD1 + 0.12));
  };
  // ticks every 5 %: the time the value crosses 25, 30, 35
  const crossT = (vv) => { let lo = tD0, hi = tD1; for (let k = 0; k < 30; k++) { const m = (lo + hi) / 2; if (vAt(m) < vv) lo = m; else hi = m; } return hi; };
  _sfx(ctx, 'whoosh_short', 0, tLand - FR, { db: -10, note: 'thumb sweeps in' });
  _sfx(ctx, 'ui_tap', 2, tLand, { note: 'thumb lands on the sun knob (grab)' });
  _sfx(ctx, 'slider_drag', 1, tD0, { db: -4, note: 'drag starts' });
  [0.25, 0.3, 0.35].forEach((vv, i) => _sfx(ctx, 'slider_tick', 2 + (i % 2), crossT(vv - 0.0005), { note: `${Math.round(vv * 100)}% detent` }));
  _sfx(ctx, 'riser', 0, flare, { db: -2, note: 'riser into the moon flare (peak on FLARE, in C14)' });
  _sfx(ctx, 'magic_shimmer', 3, tD1, { db: -12, note: 'the sun icon glints at 35%' });
  const cam = ctx.cam({
    keys: [[0, { x: 0, y: 0, z: 1.035 }], [ctx.dur, { x: 10, y: 4, z: 1.075 }, 'inOutSine']],
    punch: [{ t: tUp - FR, k: 1.07, at: [960, 560], settle: 0.28 }], drift: 2,
  });
  const v = vAt(t), kn = _brightKnob(v);
  const grab = t < tLand ? 0 : ease.outBack(seg(t, tLand, tLand + 6 * FR));
  const wash = 0.18 * seg(v, BRIGHT_V0, V1) + 0.06 * seg(t, tD1, ctx.dur);
  let s = cam.layer(_brightPage(v, t, { grab, flare: _pulse(t, tD1, 0.2, 4 * FR), wash }), 1);
  // the thumb: in from the right (8 frames, outCubic), presses on the land, follows the knob
  const e = ease.outCubic(seg(t, tLand - 8 * FR, tLand));
  const tipRest = [kn[0] + 46, kn[1] + 52];
  const tip = [lerp(2050, tipRest[0], e), lerp(1000, tipRest[1], e)];
  const press = t < tLand ? 0 : 0.55 + 0.45 * _pulse(t, tLand, 0.12, 2 * FR);
  if (e > 0) {
    let th = _bigThumb(tip, { press, light: seg(v, 0.2, 0.35) });
    if (t >= tLand && t < tLand + 0.3) th += U.tapRing(kn[0], kn[1], seg(t, tLand, tLand + 0.3), '#FFF3B0');
    s += cam.layer(th, 1);
  }
  return s;
}

// =====================================================================================================================
// C14 — "Just a little." The window: the moon swells on "Just", fills on "a", and flares into a sun on "little" (FLARE):
// white flash, god rays, the sky turns day, the room blows out white then settles sunny; the birds pop awake and sing;
// Sam (left) turns to the window with star eyes.
// =====================================================================================================================
const C14_F0 = _frame([1120, 420], 1.27, [960, 540], 0.75);
function _c14Sun(t, tJ, tA, tF) {
  if (t < tJ) return 0.02 * seg(t, 0, tJ);
  if (t < tF - 2 * FR) return lerp(0.02, 0.2, ease.inQuad(seg(t, tJ, tF - 2 * FR)));
  if (t < tF + 5 * FR) return lerp(0.2, 0.97, ease.outCubic(seg(t, tF - 2 * FR, tF + 5 * FR)));
  if (t < tF + 0.14) return 0.97 + 0.03 * seg(t, tF + 5 * FR, tF + 0.14);
  // the eyes adjust: blown-out white clears to sunny in 8 frames (bedroomSun's overlay opacities are quantised to 0.1
  // steps by attrs(), so they must only change during fast moves)
  return lerp(1, 0.74, ease.outCubic(seg(t, tF + 0.14, tF + 0.14 + 8 * FR)));
}
export function C14_sunrise(ctx) {
  const t = ctx.t, L = ctx.line('S00-L020');
  const tJ = _at(L, 'Just', 0.15), tA = _at(L, 'a', 0.45), tF = _sync(ctx, 'FLARE', 0.687);
  const tWake = [tF + 0.16, tF + 0.21, tF + 0.26], tSing = tF + 0.42;
  _sfx(ctx, 'impact_hit', 1, tF, { note: 'the moon flares into a sun (riser peak lands here)' });
  _sfx(ctx, 'flash_whoomp', 0, tF, { note: 'synth: flash whoomp on the white-out' });
  _sfx(ctx, 'magic_shimmer', 1, tF, { db: -4, note: 'bright magic sweep (peak on the flare)' });
  _sfx(ctx, 'whoosh_short', 3, tF + 2 * FR, { db: -6, note: 'bright whoosh: light floods the room' });
  tWake.forEach((tw, i) => _sfx(ctx, 'cartoon_pop', [1, 5, 7][i], tw, { db: -8, note: `bird ${i + 1} pops awake` }));
  _sfx(ctx, 'morning_birds', 2, tSing, { db: -4, dur: 1.2, note: 'the birds start to sing (tweets over the bed)' });
  _sfx(ctx, 'magic_shimmer', 3, tF + 0.1, { db: -10, note: "Sam's star eyes twinkle" });
  _sfx(ctx, 'swish', 1, tF + 1 * FR, { db: -10, note: 'Sam whips round to the window' });
  const sun = _c14Sun(t, tJ, tA, tF);
  const cam = ctx.cam({
    keys: [[0, C14_F0], [ctx.dur, { x: C14_F0.x + 70, y: C14_F0.y - 20, z: C14_F0.z * 1.13 }, 'inOutSine']],
    punch: [{ t: tF - FR, k: 1.1, at: [1290, 360], settle: 0.35, keep: 0.04 }],
    shake: [{ t: tF, amp: 16, decay: 0.09 }], drift: 4,
  });
  // the birds: asleep, then each pops awake (3 frames apart), flaps, sings with notes
  const birds = _birds((i) => {
    const aw = seg(t, tWake[i], tWake[i] + 4 * FR);
    return { awake: aw, flap: aw > 0 && aw < 1 ? 1 : t > tSing ? 0.5 + 0.5 * Math.sin(2 * Math.PI * 5 * (t + i * 0.13)) : 0, sing: t > tSing ? 0.5 + 0.5 * Math.sin(2 * Math.PI * 4.2 * (t + i * 0.21)) : 0, notes: t > tSing ? (t - tSing) * 0.9 + 0.01 : 0 };
  }, 1 - seg(sun, 0.1, 0.55));
  const lit = t >= tF;
  const sam = ctx.actor('sam', {
    ...SAM_BED, facing: [[0, -4], [tF - 3 * FR, -4], [tF + 2 * FR, 26]],
    face: [[0, { preset: 'neutral', look: [0, 3] }], [tJ, { preset: 'neutral', look: [3, 2] }, 0], [tF, 'shocked'], [tF + 0.14, 'starstruck']],
    pose: [[0, posePreset('bedSit', 'sam')], [tF, { ...posePreset('bedSit', 'sam'), lean: -7, head: -6, shrug: 0.6 }, 'outBack', 5 * FR]],
    lurch: [[tF + 0.14, 1.08]], squash: [[tF, -0.06]],
    tint: (tt) => (tt >= tF ? SUN_TINT : NIGHT_TINT), light: (tt) => (tt >= tF ? SUN_LIGHT : NIGHT_LIGHT), blink: { seed: 12 },
  });
  let s = _bedWorld(ctx, cam, { sun, sam, birds, phoneGlow: sun < 0.4 });
  // the flare (screen space at the sun's screen position): lens flare + rays, and the white flash
  const sp = cam.toScreen([BEDROOM.moon.x, BEDROOM.moon.y], 0.75);
  // the flare: a glow swelling with the moon (to 0.25), then up to full over 3 frames and settling to 0.55 (continuous)
  const fk = t < tF - 2 * FR ? 0.25 * seg(t, tJ, tF - 2 * FR) : lerp(0.25, 1, clamp((t - tF + 2 * FR) / (3 * FR))) * (0.55 + 0.45 * Math.exp(-Math.max(0, t - tF) / 0.25));
  if (fk > 0.02) s += sunFlare({ cx: sp[0], cy: sp[1], r: 70 + 40 * fk, k: fk, t, rays: t >= tF });
  // white flash: exponential decay offset so it reaches exactly 0 (~0.45 s after the flare) instead of popping off
  const wk = t >= tF - FR ? 0.95 * Math.max(0, Math.exp(-Math.max(0, t - tF - FR) / 0.12) - 0.02) / 0.98 * clamp((t - tF + FR) / (2 * FR)) : 0;
  if (wk > 0) s += whiteout({ cx: sp[0], cy: sp[1] }, wk);
  return s;
}

// =====================================================================================================================
// C15 — DAD "Who turned on the SUN?!" The hallway: Sam's door bangs open on the cut, light floods out; Dad in pyjamas
// recoils, shields his eyes and shouts; lurch, punch-in and shake on "SUN".
// =====================================================================================================================
function _doorOpen(t) {
  if (t < 0) return 0.22;
  const u = seg(t, 0, 6 * FR);
  if (t < 6 * FR) return lerp(0.22, 0.95, ease.inQuad(u));
  const dt = t - 6 * FR;
  return 0.88 + 0.07 * Math.exp(-dt / 0.12) * Math.cos(2 * Math.PI * 3.2 * dt);
}
export function C15_dadsun(ctx) {
  const t = ctx.t, L = ctx.line('S00-L021');
  const tWho = _at(L, 'Who', 0.2), tTurn = _at(L, 'turned', 0.52), tOn = _at(L, 'on', 1.08), tSun = _at(L, 'SUN', 1.64), tEnd = _end(L, 2.4);
  const tBang = 6 * FR;
  _sfx(ctx, 'door_slam', 0, tBang, { note: "Sam's door bangs open against the wall (on the cut)" });
  _sfx(ctx, 'flash_whoomp', 0, tBang - FR, { db: -6, note: 'synth: light floods the hall' });
  _sfx(ctx, 'swish', 1, 0.12, { db: -8, note: 'Dad flinches, arm up to shield his eyes' });
  _sfx(ctx, 'swish', 3, tTurn - 2 * FR, { db: -10, note: 'Dad shakes his fist' });
  _sfx(ctx, 'whoosh_short', 2, tSun, { db: -6, note: "punch-in on 'SUN'" });
  _sfx(ctx, 'impact_hit', 2, tSun + FR, { db: -14, note: "low thump under the 'SUN' shake" });
  _sfx(ctx, 'swish', 0, tEnd + 0.04, { db: -12, note: 'arm flops after the shout' });
  const door = Math.round(_doorOpen(t) * 50) / 50;
  const set = ctx.memo(`hook_d/hall_${door}`, () => hallway({ door }));
  // <= 0.74: hallwaySun's blow-out rect stays at opacity 0 (its opacity is quantised to 0.1 steps)
  const sun = Math.min(0.74, 0.42 + 0.27 * ease.outCubic(seg(t, 0, tBang + 4 * FR)) + 0.03 * Math.sin(2 * Math.PI * 1.3 * t) * seg(t, 0.3, 0.8) + 0.02 * _pulse(t, tSun, 0.3, 3 * FR));
  const SL = hallwaySun(sun, { door });
  const D = HALL.dad;
  const F0 = _frame([905, 488], 1.22);
  const cam = ctx.cam({
    keys: [[0, F0], [ctx.dur, { x: F0.x - 12, y: F0.y - 6, z: F0.z * 1.05 }, 'inOutSine']],
    punch: [{ t: tSun - FR, k: 1.14, at: [790, 420], settle: 0.3, keep: 0.05 }],
    shake: [{ t: tBang, amp: 12, decay: 0.07 }, { t: tSun, amp: 24, decay: 0.09 }, { t: tSun + 0.3, amp: 6, decay: 0.08 }], drift: 4,
  });
  const shield = posePreset('shieldEyes', 'dad', { facing: 'tq-right' });
  const P0 = { ...shield, armL: 46, foreL: 96, handL: 'open', lean: -6 };           // recoil, palm up against the glare
  const Pwho = { ...shield, armL: 92, foreL: 22, handL: 'open', lean: -2 };           // "who?!" palm out to the side
  const Pjab = { ...shield, armL: 74, foreL: 62, handL: 'fist', lean: 2 };            // fist shake at chest height
  const Pon = { ...shield, armL: 98, foreL: 34, handL: 'fist', lean: 1 };
  const Psun = { ...shield, armL: 128, foreL: -38, handL: 'open', lean: 5, head: -4 }; // flung up and out on "SUN"
  const Pafter = { ...shield, armL: 58, foreL: 56, handL: 'fist', lean: 0 };
  const pose = [[0, { ...shield, armL: 20, foreL: 20, handL: 'open', lean: 4 }], [3 * FR, P0, 'outBack', 5 * FR], [tWho - 2 * FR, Pwho, 'outBack', 6 * FR],
    ...anticPose(tTurn, Pwho, Pjab, { wind: 3, dur: 6 }), [tOn, Pon, 'outBack', 6 * FR], ...anticPose(tSun - FR, Pon, Psun, { wind: 4, dur: 6 }), [tEnd + 0.04, Pafter, 'inOutSine', 10 * FR]];
  const dad = ctx.actor('dad', {
    x: (tt) => D.x - 18 * ease.outCubic(seg(tt, 0, 0.2)), y: D.y, s: D.s, outfit: 'pyjamas', facing: 'tq-right',
    face: [[0, { preset: 'squint', mouth: 'gritted' }], [tWho, 'shout'], [tSun, { preset: 'scream', brows: 'angry' }], [tEnd + 0.05, { preset: 'squint', mouth: 'gritted' }]],
    talk: 'S00-L021', pose, lurch: [[tSun, 1.22]], squash: [[2 * FR, 0.08], [tSun, -0.05]], nervous: 0.25, blink: false,
    tint: SUN_TINT, light: { ...SUN_LIGHT, k: 0.55 },
  });
  const shadow = ellipse(D.x - 10, D.y + 6, 110 * D.s, 14 * D.s, { fill: '#1A1430', opacity: 0.22 });
  return cam.set(set, { skip: ['grade'], insert: [
    { after: 'far', depth: 1, svg: SL[0].svg }, { after: 'mid', depth: 1, svg: SL[1].svg }, { after: 'mid', depth: 1, svg: shadow + dad },
    { after: 'near', depth: 1, svg: SL[2].svg }, { after: 'near', depth: 0, svg: SL[3].svg },
  ] });
}

// =====================================================================================================================
// C16 — "That's not the PHONE's brightness." Sam in the sunlit bed slowly lowers the phone; the star eyes fade to fear
// (swap on "PHONE's"), the eyes slide to the window on "brightness", sweat, a gulp.
// =====================================================================================================================
export function C16_phonelower(ctx) {
  const t = ctx.t, L = ctx.line('S00-L022');
  const tNot = _at(L, 'not', 0.47), tPh = _at(L, "PHONE's", 0.79), tBr = _at(L, 'brightness', 1.27), tEnd = _end(L, 1.91);
  const tGulp = Math.min(ctx.dur - 0.18, tEnd + 0.06);
  _sfx(ctx, 'magic_shimmer', 3, 0.02, { db: -10, note: 'star eyes twinkle (cut transient)' });
  _sfx(ctx, 'slide_whistle_down', 0, 0.3, { db: -12, note: 'soft: the phone slowly lowers' });
  _sfx(ctx, 'cartoon_pop', 6, tPh + 2 * FR, { db: -6, note: 'sweat drop bloops out (fear swap)' });
  _sfx(ctx, 'swish', 2, tBr - 2 * FR, { db: -12, note: 'eyes / head slide to the window' });
  _sfx(ctx, 'cartoon_pop', 6, tBr + 0.1, { db: -9, note: 'a second sweat drop bloops out' });
  _sfx(ctx, 'cartoon_pop', 3, tGulp, { db: -8, note: 'gulp' });
  const F0 = _frame([BEDROOM.sam.x, 505], 1.92, [800, 448], 0.75);
  const cam = ctx.cam({ keys: [[0, F0], [ctx.dur, { ...F0, x: F0.x + 8, z: F0.z * 1.05 }, 'inOutSine']], drift: 3 });
  const Pup = { ...posePreset('phoneUp', 'sam'), lean: -2, head: -2 };
  const Plow = _lerpPose(posePreset('phoneChest', 'sam'), posePreset('phoneLap', 'sam'), 0.45);
  const lowU = (tt) => ease.inOutSine(seg(tt, 0.18, 1.75));
  const pose = (tt) => ({ ..._lerpPose(Pup, { ...Plow, lean: -4, head: 3 }, lowU(tt)), shrug: 0.5 * seg(tt, tPh, tPh + 0.2) });
  const face = (tt) => {
    if (tt < tPh) return { preset: 'starstruck', to: 'scared', k: 0.55 * ease.inQuad(seg(tt, tNot, tPh)) };
    const look = tt < tBr ? [0, -1.5] : tt < tGulp ? [5, -2] : [1, -1];
    return { preset: 'scared', look };
  };
  const sam = ctx.actor('sam', {
    ...SAM_BED, facing: [[0, 0], [tBr, 0], [tBr + 6 * FR, 14], [tGulp, 14], [tGulp + 8 * FR, 4]],
    face: (tt) => face(tt), pose, squash: [[tPh, 0.05], [tGulp, 0.06]],
    add: (tt) => (tt >= tPh ? { sweat: tt >= tBr + 0.1 ? 2 : 1, sweatK: clamp(0.2 + 0.8 * seg(tt, tPh, tEnd)), sweatSize: 0.9 + 0.2 * seg(tt, tPh, tEnd) } : {}),
    nervous: (tt) => (tt >= tPh ? 0.45 : 0), blink: { seed: 4 }, tint: SUN_TINT, light: SUN_LIGHT,
  });
  const sun = 0.74;                                                      // = C14's settled sun
  const birds = _birds((i) => ({ awake: 1, flap: 0.4 + 0.4 * Math.sin(2 * Math.PI * 5 * (ctx.gt + i * 0.13)), sing: 0.5 + 0.5 * Math.sin(2 * Math.PI * 4.2 * (ctx.gt + i * 0.21)), notes: ctx.gt * 0.9 }), 0);
  // star-eye twinkles burst off his head on the cut (world, Sam's depth)
  const tw = _burst(BEDROOM.sam.x, 440, t + 0.12, { n: 9, r: 230, size: 22, seed: 16, dur: 0.5 });
  return _bedWorld(ctx, cam, { sun, sam, birds, phoneGlow: false, after: tw ? [{ depth: 0.75, svg: tw }] : [] });
}

// =====================================================================================================================
// C17 — "That's the planet's." One continuous zoom out (0.43 s, landing on "planet's"): the sunlit house front shrinks
// into the glowing town on Earth (the street frame is scaled with the space camera, so the move never jumps), then a
// deadpan hold in space with one side of Earth glowing like a lamp; one tiny tweet.
// =====================================================================================================================
const DAY_STREET = () => street({ split: true });
const C17_STREET_CAM = { x: -620, y: -20, z: 1.7 };                       // Sam's house front, framed on the window
const C17_ZS0 = 14;                                                        // space zoom at which the street frame = the town
function _c17Zoom(t, t0, t1) {
  // log-space zoom from ZS0 to 1 with an in-out shape (accelerates off the house, settles into space on the word)
  const u = seg(t, t0, t1), e = u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2;
  return { z: Math.exp(Math.log(C17_ZS0) * (1 - e)), e, u };
}
export function C17_planet(ctx) {
  const t = ctx.t, L = ctx.line('S00-L023');
  const tPl = _at(L, "planet's", 0.73);
  const t0 = 0.3, t1 = tPl, tTweet = Math.min(ctx.dur - 0.5, 1.86);
  _sfx(ctx, 'swish', 3, t0 + 2 * FR, { db: -6, note: 'the zoom out takes off' });
  _sfx(ctx, 'whoosh_long', 0, t0 + (t1 - t0) * 0.45, { db: -2, note: 'zoom out to space (peak at the fastest frame) into silence' });
  _sfx(ctx, 'sub_boom', 2, t1, { db: -10, note: "soft space swell as the planet lands on 'planet's'" });
  _sfx(ctx, 'morning_birds', 2, tTweet, { db: -10, dur: 0.28, note: 'ONE tiny tweet in space (trim to a single chirp)' });
  const set = ctx.memo('hook_d/space', () => space({}));
  const day = ctx.memo('hook_d/day_street', DAY_STREET);
  const H0 = [SPACE.house.x, SPACE.house.y];
  const F = (tt) => {
    const Z = _c17Zoom(tt, t0, t1);
    // after the landing: a 1.5 % drift-push and slow ray turn
    const hold = seg(tt, t1, ctx.dur);
    const z = Z.z * (1 + 0.016 * ease.inOutSine(hold));
    // the house travels from the frame centre to its natural place at z 1 as the zoom lands
    const S = [lerp(960, H0[0], Z.e), lerp(540, H0[1], Z.e)];
    const fr = _frame(H0, z, S);
    const cam = ctx.cam({ keys: [[0, fr]], drift: 0, ghost: false, blur: false, shake: [{ t: t1, amp: 4, decay: 0.08 }] });
    const glow = spaceGlow(1, { t: tt });
    let s = cam.set(set, { insert: [{ after: 'mid', depth: 1, svg: glow[0].svg }] });
    // the tiny tweet: a little note pops out of the glowing town and floats up
    const nu = tt - tTweet;
    if (nu > 0 && nu < 0.7) {
      const hp = cam.toScreen(H0, 1), k = ease.outBack(seg(nu, 0, 8 * FR)), op = 1 - seg(nu, 0.45, 0.7);
      s += g(path('M0 0V-24L15 -29V-5', { fill: 'none', ...st('#B0701A', 4) }) + ellipse(-4, 0, 7, 5.4, { fill: '#FFD43B', stroke: '#B0701A', strokeWidth: 2.4, transform: 'rotate(-20)' }) + ellipse(11, -5, 7, 5.4, { fill: '#FFD43B', stroke: '#B0701A', strokeWidth: 2.4, transform: 'rotate(-20 11 -5)' }),
        { transform: `translate(${r2(hp[0] + 34 + 14 * nu)} ${r2(hp[1] - 40 - 70 * nu)}) scale(${r3(Math.max(0.01, k * 1.1))})`, opacity: op3(op) });
    }
    // the street frame, scaled about the house's screen point with the space zoom, masked to a soft disc that closes in
    const q = Z.z / C17_ZS0;
    if (q > 0.1) {
      const pushIn = 1 + 0.02 * ease.inOutSine(seg(tt, 0, t0));
      const P = [STREET.samWindow.cx + 40, STREET.samWindow.cy - 60];
      const sc = ctx.cam({ keys: [[0, _frame(P, C17_STREET_CAM.z * pushIn, [960, 540], 0.75)]], drift: 0, ghost: false, blur: false });
      const pw = [960, 540];
      let st0 = sc.set(day, {});
      // the sun is on (at 2:13 a.m.): a hot sun right above the roof, wedge rays, a warm wash, sparkle motes
      const d = new Defs();
      for (let i = 0; i < 14; i++) {
        const a0 = ((i / 14) * 180 + tt * 10) * Math.PI / 180, a1 = a0 + Math.PI / 14 * 0.5, R = 2200;
        st0 += poly([[1180, -60], [1180 + Math.cos(a0) * R, -60 + Math.sin(a0) * R], [1180 + Math.cos(a1) * R, -60 + Math.sin(a1) * R]], { fill: '#FFF6D0', opacity: 0.16 });
      }
      st0 += rect(-60, -60, 2040, 1200, { fill: d.rad([[0, '#FFFFFF', 0.9], [0.3, '#FFF3C0', 0.55], [1, '#FFE08A', 0]], 0.61, -0.06, 0.85) });
      st0 += sunFlare({ cx: 1180, cy: -60, r: 170, k: 1, t: tt, rays: false, ghosts: false });
      st0 += sparkles({ x: 0, y: 0, w: 1920, h: 760, count: 14, seed: 77, t: tt * 2, size: 24 });
      const Rm = lerp(1450, 540, ease.outCubic(seg(Z.e, 0, 0.3)));
      const op = clamp((q - 0.1) / 0.13);                                    // gone by z 1.4, before the landing
      const mid = `c17m${Math.round(Rm)}`;
      const mask = `<defs><radialGradient id="${mid}g" gradientUnits="userSpaceOnUse" cx="${r2(pw[0])}" cy="${r2(pw[1])}" r="${r2(Rm)}"><stop offset="0.55" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient><mask id="${mid}" maskUnits="userSpaceOnUse" x="-200" y="-200" width="2320" height="1480"><rect x="-200" y="-200" width="2320" height="1480" fill="url(#${mid}g)"/></mask></defs>`;
      const hp = cam.toScreen(H0, 1);
      s += String(d) + mask + `<g opacity="${r3(op)}"><g transform="translate(${r2(hp[0])} ${r2(hp[1])}) scale(${r3(q)}) translate(${r2(-pw[0])} ${r2(-pw[1])})"><g mask="url(#${mid})">${st0}</g></g></g>`;
    }
    return s;
  };
  // ghost copies while the zoom is fast (the frame corners move > 25 px/frame)
  const zr = Math.abs(Math.log(_c17Zoom(t, t0, t1).z) - Math.log(_c17Zoom(t - FR, t0, t1).z));
  const n = zr > 0.06 ? Math.min(6, 3 + Math.round(zr * 12)) : 0;
  return n ? _ghost(F, t, n, 0.6) : F(t);
}

// =====================================================================================================================
// D1 — N "Day one." The DAY 1 card slams in (the cardSlam transition scales the frame 1.35 -> 1 with the white hit at
// +0.12 s; the card itself drops from 1.7x onto the same frame), starburst, rings, sparkles; the Day 1 toggle flicks on
// with "one" and the volume sticker wobbles.
// =====================================================================================================================
export function D1_day1(ctx) {
  const t = ctx.t, L = ctx.line('S01-L001');
  const tImp = _sync(ctx, 'DAY1', 0.12), tOne = _at(L, 'one', 0.487), tDay = _at(L, 'Day', 0.207);
  _sfx(ctx, 'whoosh_short', 0, tImp - 2 * FR, { db: -4, note: 'card fly-in (peak two frames before the impact, on the slam-in)' });
  _sfx(ctx, 'impact_hit', 0, tImp, { note: 'DAY 1 card slam (Average Duck Face downbeat on this frame)' });
  _sfx(ctx, 'sub_boom', 3, tImp, { db: -4, note: 'slam sub' });
  _sfx(ctx, 'magic_shimmer', 2, tImp + 0.06, { db: -12, note: 'sparkles round the card' });
  _sfx(ctx, 'toggle', 1, tOne + 2 * FR, { note: "the Day 1 toggle flicks on with 'one'" });
  _sfx(ctx, 'boing', 4, tOne + 5 * FR, { db: -10, note: 'volume sticker wobbles' });
  const cam = ctx.cam({ keys: [[0, { x: 0, y: 0, z: 1 }], [ctx.dur, { x: 0, y: -6, z: 1.035 }, 'inOutSine']], drift: 2,
    punch: [{ t: tOne + FR, k: 1.05, at: [960, 520], settle: 0.25 }] });
  const d = new Defs(), col = U.DAY_COLORS[0];
  // background: Day 1 blue, soft rotating wedges, a vignette
  let bg = rect(-80, -80, 2080, 1240, { fill: d.lin([shade(col, 0.06), shade(col, -0.12)]) });
  for (let i = 0; i < 16; i++) {
    const a0 = ((i / 16) * 360 + t * 14) * Math.PI / 180, a1 = a0 + Math.PI / 16 * 0.9, R = 1600;
    bg += poly([[960, 520], [960 + Math.cos(a0) * R, 520 + Math.sin(a0) * R], [960 + Math.cos(a1) * R, 520 + Math.sin(a1) * R]], { fill: '#FFFFFF', opacity: 0.07 });
  }
  bg += String(d) + rect(-80, -80, 2080, 1240, { fill: d.rad([[0.45, '#0B3A78', 0], [1, '#0B3A78', 0.45]], 0.5, 0.48, 0.75) });
  // the card: drops from 1.7x and lands on the impact frame, squash 0.92 -> 1.05 -> 1
  let k;
  if (t < tImp) k = lerp(1.7, 1, ease.inCubic(seg(t, -0.02, tImp)));
  else if (t < tImp + 0.05) k = lerp(1, 0.92, ease.outQuad(seg(t, tImp, tImp + 0.05)));
  else if (t < tImp + 0.13) k = lerp(0.92, 1.05, ease.inOutSine(seg(t, tImp + 0.05, tImp + 0.13)));
  else k = lerp(1.05, 1, ease.inOutSine(seg(t, tImp + 0.13, tImp + 0.26)));
  const cx = 960, cy = 500, after = t - tImp, CS = 1.16;
  let fx = '';
  if (after < 0) fx += speedLines({ cx, cy, count: 40, r0: 420, r1: 1500, t: t * 2, width: 22, op: 0.7 });
  else {
    fx += speedLines({ cx, cy, count: 44, r0: 380, r1: 1600, t, width: 26, op: 0.85 * (1 - 0.6 * seg(after, 0.15, 0.6)) });
    fx += starburst({ cx, cy, r: 600, points: 14, fill: '#FFB21F', core: '#FFF3B0', seed: 6, rot: t * 6 }, seg(after, 0, 0.3));
    fx += shockRing(cx, cy, 1150, seg(after, 0, 0.33), '#FFFFFF', 34) + shockRing(cx, cy, 880, seg(after, 0.04, 0.38), col, 24);
    fx += sparkles({ x: cx - 700, y: cy - 420, w: 1400, h: 840, count: 18, seed: 8, t, size: 34 });
  }
  const tog = t < tOne + 2 * FR ? 0 : ease.outBack(seg(t, tOne + 2 * FR, tOne + 8 * FR));
  const wob = t > tOne + 5 * FR ? 6 * Math.exp(-(t - tOne - 5 * FR) / 0.18) * Math.sin(2 * Math.PI * 5 * (t - tOne - 5 * FR)) : 0;
  const tilt = t < tImp ? -14 : lerp(-8, -3, ease.outCubic(seg(after, 0, 0.36))) + wob * 0.3;
  const card = U.dayCard({ cx, cy, day: 1, scale: k * CS, gearRot: t * 40, tilt, toggleK: tog });
  return bg + cam.layer(fx + card, 1);
}
