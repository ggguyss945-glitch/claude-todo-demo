// hook_b.js — hook shots A6-A10 + B1: the Day 7 flash-forward (factory reset street, Mom and Dad flickering into
// DEFAULT mannequins, Sam's "In my defense..." to camera, the 1 -> 412 counter, "...Ish.") and the UNDO HISTORY rewind
// with lavender flash-forwards and a tape stop.
// Plan per shot: docs/HOOK_BOARD.md rows A6-A10, B1 and episodes/hook/SHOTS.md (times). Engine: engine/anim/README.md.
//
// SFX cues (same convention as hook_a.js): _sfx(ctx, name, v, tEv, o) registers ctx.cue(name, t, {v, ev, sync_ms, ...o})
// with t = the clip START (local s), chosen so the sfx_map variant's sync point lands on the visual frame tEv; ev is
// that frame in global s. Hints in o: db (level vs the -18 LUFS map level), dur (trim / loop length in s), note.
// counter_tick is not in sfx_map (the integration stage synthesizes it; sync 0).
import { streetReset, resetSky, resetGrade, RESET, street, kitchen, classroom } from '../sets.js';
import * as U from '../ui.js';
import * as U2 from '../ui2.js';
import { boxBlur, scrollStreaks, sparkle } from '../fx.js';
import { FONT, text, rect, g, path, rrPath, Defs, poly } from '../ui_style.js';
import { seg, ease, clamp, lerp, rand } from '../anim/motion.js';
import { posePreset, reach, toonHeadY } from '../cast.js';
import { anticPose } from '../anim/actor.js';

// ---------- shared helpers (names starting with _ are not registered as shots) ----------
const FPS = 60, FR = 1 / FPS;
const r2 = (n) => Math.round(n * 100) / 100;
const RESET_SET = () => streetReset({ t: 0, glitch: false });

// sync points (ms into the clip) of the audio/sfx_map.json variants used here
const SYNC = {
  glitch: [70, 7.5, 32.5, 12.5], impact_hit: [7.5, 140, 42.5, 2.5], sub_boom: [2.5, 22.5, 252.5, 57.5], countdown_beep: [7.5, 17.5, 7.5, 5],
  cartoon_pop: [10, 22.5, 10, 10, 7.5, 10, 12.5, 10, 140], power_down: [7.5, 5, 67.5, 87.5], stamp: [10, 10, 7.5, 15],
  swish: [47.5, 65, 60, 130, 125, 17.5], whoosh_short: [250, 270, 277.5, 275, 337.5, 347.5, 277.5, 812.5, 637.5, 710, 737.5],
  popup_whoosh: [207.5, 115, 87.5, 135, 240, 10], error_buzz: [2.5, 2.5, 2.5, 7.5, 7.5, 2.5, 7.5], vhs_rewind: [7.5, 7.5, 10, 7.5],
  whoosh_long: [327.5, 2562.5], slider_tick: [2.5, 7.5, 12.5, 12.5, 10], tape_stop: [52.5, 87.5, 7.5],
};
/** register an SFX cue whose sync point hits local time tEv (call unconditionally: cues are collected at the shot start) */
function _sfx(ctx, name, v, tEv, o = {}) {
  const tbl = SYNC[name], sm = tbl ? tbl[v % tbl.length] : 0;
  ctx.cue(name, tEv - sm / 1000, { v, ev: Math.round((ctx.start + tEv) * 1000) / 1000, sync_ms: sm, ...o });
}

/** the Day 7 loading bar: one continuous fill over the whole flash-forward (global time), so it never jumps at a cut */
const _barPct = (gt) => { const u = seg(gt, 7.7, 20.4); return 78 + 17 * (1 - (1 - u) * (1 - u)); };
/** the alarm beams sweep back and forth (resetGrade's t turns them by t*90 deg) */
const _beamT = (gt) => 0.5 + 0.55 * Math.sin(2 * Math.PI * 0.42 * gt);
/** the red alert tint pulses with the siren (0.82..1) */
const _tint = (gt) => 0.82 + 0.18 * (0.5 + 0.5 * Math.sin(2 * Math.PI * 0.9 * gt));

/** streetReset drawn through the camera with the per-frame sky / grade; o.insert: extra inserts (after 'near' = in front
 *  of the street, under the red grade), o.after: drawn above the grade */
function _resetWorld(ctx, cam, o = {}) {
  const set = ctx.memo('hook_b/reset', RESET_SET);
  const gt = ctx.gt;
  const ins = [{ after: 'defs2', depth: 0.08, svg: resetSky({ pct: _barPct(gt), t: gt }) }, ...(o.insert || [])];
  ins.push({ after: 'near', depth: 0, svg: resetGrade({ t: _beamT(gt), tint: o.tint ?? _tint(gt) }) });
  for (const a of o.after || []) ins.push({ after: 'top', ...a });
  return cam.set(set, { skip: ['sky', 'grade'], insert: ins });
}

/** de-rezzed cubes floating up off the street (world layer, global time so they continue across cuts) */
function _cubes(gt, o = {}) {
  const n = o.n ?? 16, x0 = o.x0 ?? -200, x1 = o.x1 ?? 2120, y0 = o.y0 ?? 900, rise = o.rise ?? 620, seed = o.seed ?? 5;
  const cols = ['#FF3B3B', '#FF2BD6', '#FFB070', '#8A5CF2'];
  const d = new Defs();
  let s = '';
  for (let i = 0; i < n; i++) {
    const sp = 40 + rand(seed, i, 1) * 70, life = (gt * sp / rise + rand(seed, i, 2)) % 1;
    const x = x0 + rand(seed, i, 3) * (x1 - x0) + 30 * Math.sin(gt * 0.9 + i), y = y0 - life * rise;
    const bs = (14 + rand(seed, i, 4) * 26) * (o.k ?? 1), c = cols[i % 4];
    const op = Math.min(1, life * 6) * Math.min(1, (1 - life) * 4);
    if (op < 0.02) continue;
    const rot = rand(seed, i, 5) * 90 + gt * (rand(seed, i, 6) < 0.5 ? -50 : 50);
    s += g(rect(-bs / 2, -bs / 2, bs, bs, { fill: d.grad(c), rx: 3 }) + rect(-bs / 2 + 3, -bs / 2 + 3, bs - 6, bs * 0.16, { fill: '#FFFFFF', opacity: 0.45, rx: 2 }),
      { transform: `translate(${r2(x)} ${r2(y)}) rotate(${r2(rot)})`, opacity: r2(op * 0.9) });
  }
  return String(d) + s;
}

/** horizontal RGB band glitch of a composed (screen-space) string: re-drawn copies, never <use> (Chromium caveat) */
function _bands(svg, t, seed, o = {}) {
  const n = o.bands ?? 4, amt = o.amount ?? 70, cell = Math.floor(t * 30);
  let out = svg;
  for (let i = 0; i < n; i++) {
    const by = (o.y0 ?? 60) + rand(seed + cell, i, 1) * (o.h ?? 900), bh = 16 + rand(seed + cell, i, 2) * 90;
    const dx = (rand(seed + cell, i, 3) - 0.5) * 2 * amt, tint = rand(seed + cell, i, 4) < 0.5 ? '#FF2BD6' : '#33E8FF';
    const id = `hbband${seed % 9973}_${cell}_${i}`;
    out += `<clipPath id="${id}"><rect x="-40" y="${r2(by)}" width="2000" height="${r2(bh)}"/></clipPath>`;
    out += `<g clip-path="url(#${id})"><g transform="translate(${r2(dx)} 0)">${svg}</g>${rect(-40, by, 2000, bh, { fill: tint, opacity: 0.16 })}</g>`;
    out += rect(-40, by, 2000, 3, { fill: dx > 0 ? '#33E8FF' : '#FF2BD6', opacity: 0.85 }) + rect(-40, by + bh - 3, 2000, 3, { fill: dx > 0 ? '#FF2BD6' : '#33E8FF', opacity: 0.85 });
  }
  return out;
}

// ---------- the 1:00 countdown (pops on "minute" in A6, then rides the top-left corner, one tick per second) ----------
function _pillT(ctx) { const L = ctx.line('S00-L005'); return ctx.start + (L ? L.at('minute') : 1.87); }
const _timerText = (rem) => { const s = Math.max(0, Math.ceil(rem - 1e-6)); return s >= 60 ? '1:00' : `0:${String(s).padStart(2, '0')}`; };
function _pillSvg(gt, tp, o = {}) {
  const rem = 60 - (gt - tp), el = gt - tp;
  const ph = el - Math.floor(el), bump = el >= 1 ? 1 + 0.09 * Math.exp(-ph / 0.07) : 1;
  const pulse = 0.5 + 0.5 * Math.sin(2 * Math.PI * 1.0 * gt);
  return { svg: U.timerPill({ x: 0, y: 0, label: 'FACTORY RESET', text: _timerText(rem), red: true, frac: clamp(rem / 60), pulse, shake: o.shake }, o.p), bump };
}
/** the corner pill (screen space, top-left), with a small bump on every second and a soft tick cue per second */
function _cornerPill(ctx, o = {}) {
  const tp = _pillT(ctx);
  for (let k = 1; k <= 14; k++) {
    const tg = tp + k;
    if (tg >= ctx.start - 1e-6 && tg < ctx.end - 1e-6) _sfx(ctx, 'countdown_beep', 0, tg - ctx.start, { db: -12, note: 'corner timer second tick (quiet tension tick)' });
  }
  const P = _pillSvg(ctx.gt, tp);
  const sc = (o.s ?? 0.62) * P.bump, x = o.x ?? 34, y = o.y ?? 30;
  return g(P.svg, { transform: `translate(${x} ${y}) scale(${r2(sc * 1000) / 1000})` });
}

/** world point under screen point S for a camera framing {x, y, z} (depth 1, no roll) */
const _w = (F, sx, sy) => [960 + (F.x || 0) + (sx - 960) / F.z, 540 + (F.y || 0) + (sy - 540) / F.z];

// red emergency light on characters in front of the reset street (palette remaps, no filters)
const RED_LOOK = { tint: { color: '#F2A2A8', k: 0.28, mode: 'multiply' }, light: { color: '#FF6A70', k: 0.55, from: 'right' } };

// =====================================================================================================================
// A6 — Day 7 wide: the loading-bar sky, Mom and Dad panicking small, SYS "Factory reset in one minute." The 1:00 pill
// pops on "minute"; a sub boom and a red pulse on "reset".
// =====================================================================================================================
export function A6_day7wide(ctx) {
  const t = ctx.t, L = ctx.line('S00-L005');
  const tReset = L ? L.at('reset') : 0.91, tMin = L ? L.at('minute') : 1.87, tOne = L ? L.at('one') : 1.63;
  _sfx(ctx, 'glitch', 0, 0, { dur: 0.6, note: 'glitch cut in (music slam-back)' });
  _sfx(ctx, 'impact_hit', 1, 0, { note: 'cut impact under the glitch' });
  _sfx(ctx, 'sub_boom', 1, tReset, { dur: 2.5, note: "red pulse on 'reset'" });
  _sfx(ctx, 'countdown_beep', 1, tMin, { note: "1:00 pill pops on 'minute'" });
  _sfx(ctx, 'cartoon_pop', 2, tMin + 1 * FR, { db: -6, note: 'pill pop ring' });
  const cam = ctx.cam({
    keys: [[0, { x: 0, y: 14, z: 1.0 }], [ctx.dur, { x: 6, y: 2, z: 1.03 }, 'inOutSine']],
    shake: [{ t: 0, amp: 18, decay: 0.08 }, { t: tReset, amp: 11, decay: 0.09 }, { t: tMin, amp: 7, decay: 0.07 }],
    drift: 5,
  });
  // Mom and Dad on the sidewalk: flailing at the sky, a take on "reset", turning to the pill on "minute"
  const flail = (ph, a = 1) => (tt) => ({
    armL: 150 + 22 * a * Math.sin(2 * Math.PI * 2.6 * tt + ph), foreL: 20 + 25 * Math.sin(2 * Math.PI * 2.6 * tt + ph + 1),
    armR: 150 + 22 * a * Math.sin(2 * Math.PI * 2.6 * tt + ph + Math.PI), foreR: 20 + 25 * Math.sin(2 * Math.PI * 2.6 * tt + ph + 2.4),
    handL: 'open', handR: 'open', lean: 2 * Math.sin(2 * Math.PI * 1.3 * tt + ph),
  });
  const pillAt = [960, 432];
  const mom = ctx.actor('mom', {
    x: RESET.mom.x, y: RESET.mom.y, s: RESET.mom.s, facing: [[0, 20], [tMin, 0]],
    face: [[0, 'scared'], [tReset, 'panic'], [tMin, 'shocked']], pose: flail(0), panic: 0.45,
    lookAt: [[0, [700, 120]], [tReset, [1100, 80]], [tMin, [960, 300]]],
  });
  const dad = ctx.actor('dad', {
    x: RESET.dad.x, y: RESET.dad.y, s: RESET.dad.s, facing: [[0, -20], [tMin, 0]], props: { R: null },
    face: [[0, 'panic'], [tReset + 2 * FR, 'scream'], [tMin + 2 * FR, 'shocked']], pose: flail(1.7, 0.9), panic: 0.5,
    lookAt: [[0, [1300, 100]], [tReset, [900, 80]], [tMin, [960, 300]]],
  });
  let s = _resetWorld(ctx, cam, { insert: [
    { after: 'mid', depth: 0.75, svg: _cubes(ctx.gt, { n: 18, seed: 5 }) },
    { after: 'near', depth: 1, svg: mom + dad },
  ] });
  // red alarm pulse on "reset" (screen-sized, normal blending)
  const rp = t >= tReset ? Math.exp(-(t - tReset) / 0.18) : 0;
  if (rp > 0.01) s += rect(-40, -40, 2000, 1160, { fill: '#FF1E3C', opacity: r2(0.32 * rp) });
  // the 1:00 pill pops on "minute" (8 frames, overshoot), then pulses
  if (t >= tMin) {
    const p = seg(t, tMin, tMin + 8 / 60);
    const P = _pillSvg(ctx.gt, _pillT(ctx), { p, shake: { amp: 4 * Math.exp(-(t - tMin) / 0.15), t } });
    s += cam.screen(g(P.svg, { transform: `translate(${pillAt[0] - 154} ${pillAt[1] - 57}) scale(1.1)` }), { shake: true });
  }
  return s;
}

// =====================================================================================================================
// A7 — Mom and Dad flicker into grey DEFAULT mannequins (3 flickers), the tags pop, a rumble builds into the A8 slam.
// =====================================================================================================================
// cut in on the first flicker frame (cut on the impact), two more flickers, then each locks; tags pop on the lock
const A7_F = { mom: [[0.0, 0.05], [0.22, 0.29], [0.40, 99]], dad: [[0.017, 0.067], [0.24, 0.31], [0.48, 99]] };
const A7_TAG = { mom: 0.58, dad: 0.68 };
const _isM = (who, t) => A7_F[who].some(([a, b]) => t >= a && t < b);
export function A7_mannequins(ctx) {
  const t = ctx.t;
  _sfx(ctx, 'glitch', 1, A7_F.mom[0][0], { dur: 0.15, note: 'flicker 1' });
  _sfx(ctx, 'glitch', 2, A7_F.mom[1][0], { dur: 0.15, note: 'flicker 2' });
  _sfx(ctx, 'power_down', 0, A7_F.mom[2][0], { note: 'Mom locks into a mannequin' });
  _sfx(ctx, 'power_down', 2, A7_F.dad[2][0], { note: 'Dad locks into a mannequin' });
  _sfx(ctx, 'stamp', 0, A7_TAG.mom, { note: 'DEFAULT tag (Mom)' });
  _sfx(ctx, 'stamp', 3, A7_TAG.dad, { note: 'DEFAULT tag (Dad)' });
  _sfx(ctx, 'cartoon_pop', 7, A7_TAG.dad + 3 * FR, { db: -8, note: 'tag pop (double pop under the stamp)' });
  const F0 = { x: 0, y: 147, z: 2.2 };
  const shakes = [
    { t: A7_F.mom[0][0], amp: 10 }, { t: A7_F.mom[1][0], amp: 10 }, { t: A7_F.mom[2][0], amp: 14 }, { t: A7_F.dad[2][0], amp: 12 },
    { t: 0.96, amp: 2.5, decay: 0.1 }, { t: 1.03, amp: 3.5, decay: 0.1 }, { t: 1.09, amp: 5, decay: 0.1 }, { t: 1.14, amp: 6, decay: 0.1 },
  ];
  const cam = ctx.cam({ keys: [[0, F0], [ctx.dur, { x: 0, y: 150, z: 2.2 * 1.035 }, 'inOutSine']], shake: shakes, drift: 4 });
  const people = ['mom', 'dad'].map((who) => {
    const R = RESET[who], sg = who === 'mom' ? 1 : -1, ph = who === 'mom' ? 0 : 1.9;
    const M = (tt) => (_isM(who, tt) ? 1 : 0);
    const panicPose = (tt) => ({
      armL: 138 + 20 * Math.sin(2 * Math.PI * 2.8 * tt + ph), foreL: 30 + 20 * Math.sin(2 * Math.PI * 2.8 * tt + ph + 1),
      armR: 138 + 20 * Math.sin(2 * Math.PI * 2.8 * tt + ph + Math.PI), foreR: 30 + 20 * Math.sin(2 * Math.PI * 2.8 * tt + ph + 2.2),
      handL: 'open', handR: 'open',
    });
    const stiff = { armL: 12, foreL: 6, armR: 12, foreR: 6, handL: 'flat', handR: 'flat', head: 0, lean: 0 };
    return ctx.actor(who, {
      x: R.x, y: R.y, s: R.s, props: who === 'dad' ? { R: null } : undefined,
      facing: (tt) => (M(tt) ? 0 : 22 * sg),
      mannequin: M,
      pose: (tt) => (M(tt) ? stiff : panicPose(tt)),
      face: (tt) => (M(tt) ? 'blank' : tt < A7_F[who][0][0] ? 'scared' : tt < A7_F[who][1][0] ? 'panic' : 'scream'),
      idle: _isM(who, t) ? 0 : 1, panic: (tt) => (M(tt) ? 0 : 0.55), blink: false, accent: false,
      lookAt: [[0, [R.x + 160 * sg, 420]]],
    });
  }).join('');
  // DEFAULT tags hang from the neck (anchor just under the head), pop + damped swing
  let tags = '';
  for (const who of ['mom', 'dad']) {
    const R = RESET[who], t0 = A7_TAG[who];
    if (t < t0) continue;
    const p = seg(t, t0, t0 + 7 / 60), dt = t - t0;
    const swing = (who === 'mom' ? 1 : -1) * 16 * Math.exp(-dt / 0.35) * Math.cos(2 * Math.PI * 2.1 * dt);
    const ny = R.y + (toonHeadY(who) + 60) * R.s;
    tags += U.defaultTag({ cx: R.x, y: ny, string: 44, size: 0.5, swing, sub: 'factory settings' }, p);
  }
  let world = _resetWorld(ctx, cam, { insert: [
    { after: 'mid', depth: 0.75, svg: _cubes(ctx.gt, { n: 18, seed: 5 }) },
    { after: 'near', depth: 1, svg: people },
  ], after: [{ depth: 1, svg: tags }] });
  // flicker frames: 2-frame RGB band slices of the world
  const fl = [...A7_F.mom.map((x) => x[0]), A7_F.dad[2][0]].some((a) => t >= a && t < a + 2 * FR);
  if (fl) world = _bands(world, t, 71, { bands: 4, amount: 60 });
  return world + _cornerPill(ctx);
}

// =====================================================================================================================
// A8 — Sam to camera, close-up, the reset street blurred behind in red light: "In my defense... I only changed ONE
// thing." Nervous -> forced grin and one finger on "ONE" (punch-in 1.12x); the sweat drop grows through the line.
// =====================================================================================================================
export function A8_samdefense(ctx) {
  const t = ctx.t, L = ctx.line('S00-L006');
  const w = (k, d) => (L ? L.at(k) : d);
  const tIn = w('In', 0.22), tDef = w('defense', 0.64), tI = w('I', 1.78), tOnly = w('only', 2.0), tCh = w('changed', 2.32), tOne = w('ONE', 3.04), tThing = w('thing', 3.29);
  const defEnd = L ? L.word('defense').t1 : 1.46;
  const tGulp = defEnd + 0.1;
  _sfx(ctx, 'swish', 0, tIn - 2 * FR, { db: -10, note: 'hands up, palms out' });
  _sfx(ctx, 'cartoon_pop', 6, tGulp, { db: -4, note: 'sweat bloop (the drop swells in the pause)' });
  _sfx(ctx, 'swish', 2, tI - 2 * FR, { db: -12, note: 'hand to chest' });
  _sfx(ctx, 'whoosh_short', 0, tOne - FR, { db: -4, note: "punch-in on 'ONE'" });
  _sfx(ctx, 'cartoon_pop', 3, tOne + 2 * FR, { db: -8, note: 'finger up ding' });
  const F0 = { x: -40, y: -30, z: 1.5 }, S = 2.3;
  const head0 = _w(F0, 960, 372);
  const SX = head0[0], SY = head0[1] - toonHeadY('sam') * S;
  const cam = ctx.cam({
    keys: [[0, F0], [ctx.dur, { x: -40, y: -36, z: 1.5 * 1.05 }, 'inOutSine']],
    punch: [{ t: tOne - FR, k: 1.12, at: [960, 330], settle: 0.25, keep: 0.035 }],
    shake: [{ t: 0, amp: 20, decay: 0.08 }, { t: tOne, amp: 6, decay: 0.06 }],
    drift: 5, dolly: 1,
  });
  const P0 = { armL: 6, foreL: 128, armR: 6, foreR: 128, handL: 'fist', handR: 'fist', lean: 0 };
  const Pdef = { armL: 30, foreL: 122, armR: 30, foreR: 122, handL: 'open', handR: 'open', lean: -2, head: -2 };
  const Pdef2 = { armL: 26, foreL: 108, armR: 26, foreR: 108, handL: 'open', handR: 'open', lean: -1, head: 2 };
  const Pgulp = { armL: 12, foreL: 100, armR: 12, foreR: 100, handL: 'open', handR: 'open', lean: 1, head: 0 };
  const chest = reach('sam', 'R', [6, toonHeadY('sam') + 104]);
  const Pme = { armR: chest.arm, foreR: chest.fore, handR: 'flat', armL: 10, foreL: 24, handL: 'fist', lean: 0, head: -2 };
  const Pch = { armL: 40, foreL: 104, armR: 40, foreR: 104, handL: 'open', handR: 'open', lean: 1, head: 3 };
  const Pone = { ...posePreset('pointUp', 'sam'), lean: -2, head: -3 };
  const pose = [[0, P0], ...anticPose(tIn - FR, P0, Pdef), [tDef, Pdef2, 'outBack', 8 / 60], [tGulp - 0.04, Pgulp, 'inOutSine', 10 / 60],
    ...anticPose(tI - FR, Pgulp, Pme), ...anticPose(tCh, Pme, Pch), ...anticPose(tOne - 2 * FR, Pch, Pone)];
  const sweat = (tt) => {
    const k = clamp(tt / Math.max(0.1, tOne));
    const bl = tt >= tGulp ? 0.25 * Math.exp(-(tt - tGulp) / 0.08) * (tt < tGulp + 0.2 ? 1 : 0) : 0;
    return { sweat: tt >= tOne ? 2 : 1, sweatK: 0.15 + 0.85 * k, sweatSize: 0.8 + 0.22 * k + bl };
  };
  const sam = ctx.actor('sam', {
    x: SX, y: SY, s: S, facing: [[0, -8], [tI, 4], [tOne, 0]], talk: 'S00-L006',
    face: [[0, 'nervous'], [tDef, { preset: 'nervous', look: [-4, -1] }], [tGulp, 'scared'], [tI, { preset: 'nervous', look: [0, 0] }],
      [tCh, { preset: 'guilty', look: [4, 2] }], [tOne, 'forcedGrin']],
    pose, add: sweat, nervous: [[0, 0.55], [tOne, 0.3]], lurch: [[tOne, 1.07]], squash: [[tGulp, 0.05]],
    blink: { seed: 3 }, ...RED_LOOK,
  });
  const bg = _resetWorld(ctx, cam, { insert: [{ after: 'mid', depth: 0.75, svg: _cubes(ctx.gt, { n: 14, seed: 9 }) }] });
  let s = boxBlur(bg, { x: -60, y: -60, w: 2040, h: 1200, sdx: 7, sdy: 7 });
  s += cam.layer(sam, 1);
  return s + _cornerPill(ctx);
}

// =====================================================================================================================
// A9 — SYS "Changes made by you: four hundred and twelve." The odometer beside Sam's head ticks 1..9, then rolls to
// 412 and lands on "twelve" (error buzz, shake); Sam's eyes follow it, he sinks, the sweat doubles, then guilty eyes.
// =====================================================================================================================
function _a9Value(t, tR0, tYou, tLand) {
  if (t < tR0) return { v: 1, show: 1, speed: 0 };
  if (t < tYou) {
    const u = seg(t, tR0, tYou), v = 1 + 8 * Math.pow(u, 1.6), k = Math.floor(v + 1e-9), fr = v - k;
    return { v, show: k + ease.outCubic(clamp((fr - 0.72) / 0.28)), speed: 0 };
  }
  if (t < tLand) {
    const D = tLand - tYou, u = seg(t, tYou, tLand), c = 0.046;
    const v = 9 + 403 * (c * u + (1 - c) * u * u * u), dv = 403 * (c + 3 * (1 - c) * u * u) / D;
    return { v, show: v, speed: dv };
  }
  return { v: 412, show: 412, speed: 0 };
}
export function A9_counter412(ctx) {
  const t = ctx.t, L = ctx.line('S00-L007');
  const w = (k, d) => (L ? L.at(k) : d);
  const tCh = w('Changes', 0.2), tYou = w('you', 1.36), tFour = w('four', 1.86), tHun = w('hundred', 2.16), tLand = w('twelve', 2.72);
  const tPop = 0.05, tR0 = 0.42;
  _sfx(ctx, 'popup_whoosh', 1, tPop + 2 * FR, { note: 'counter card pops beside Sam' });
  _sfx(ctx, 'cartoon_pop', 0, tPop + 3 * FR, { db: -6 });
  for (let k = 2; k <= 9; k++) {          // the slow ticks 1..9: one counter_tick per wheel landing
    const u = Math.pow((k - 1) / 8, 1 / 1.6), tk = tR0 + u * (tYou - tR0);
    _sfx(ctx, 'counter_tick', 0, tk, { n: k, note: 'odometer tick (synth)' });
  }
  _sfx(ctx, 'countdown_beep', 3, tYou, { dur: r2(tLand - tYou), note: 'fast roll 9 -> 412, accelerating: ramp rate/pitch up into the land' });
  _sfx(ctx, 'error_buzz', 0, tLand, { note: "counter lands on 412 on 'twelve'" });
  _sfx(ctx, 'impact_hit', 0, tLand, { db: -8, dur: 1.2, note: 'land thump under the buzz' });
  _sfx(ctx, 'cartoon_pop', 6, tHun + 2 * FR, { db: -6, note: 'sweat doubles (bloop)' });
  const F0 = { x: 180, y: -20, z: 1.32 }, S = 2.2;
  const head0 = _w(F0, 600, 400);
  const SX = head0[0], SY = head0[1] - toonHeadY('sam') * S;
  const cam = ctx.cam({
    keys: [[0, F0], [ctx.dur, { x: 188, y: -24, z: 1.32 * 1.045 }, 'inOutSine']],
    shake: [{ t: tPop + 2 * FR, amp: 5, decay: 0.06 }, { t: tLand, amp: 16, decay: 0.08 }],
    drift: 5, dolly: 1,
  });
  // counter card (screen space): pops at tPop, rolls, lands with a red flash and a bump
  const CS = 1.28, cw = U2.counterSize({}).w * CS, ch = 276 * CS, cx = 1150, cy = 175;
  const V = _a9Value(t, tR0, tYou, tLand);
  const digitsAt = [cx + cw / 2, cy + (92 + 75) * CS];
  const lookW = cam.toWorld(digitsAt, 1);
  const sam = ctx.actor('sam', {
    x: SX, y: (tt) => SY + 18 * ease.inOutSine(seg(tt, tYou, tLand)) - 6 * ease.outBack(seg(tt, tLand, tLand + 0.2)), s: S,
    facing: [[0, 6], [tPop + 0.1, 22], [tLand + 0.08, -12]], lookAmp: 7,
    face: [[0, 'nervous'], [tPop + 2 * FR, 'shocked'], [tPop + 0.16, 'nervous'], [tYou, 'scared'], [tHun, 'panic'], [tLand, 'shocked'], [tLand + 0.1, 'guilty']],
    lookAt: (tt) => (tt < tPop + 2 * FR ? [SX + 40, SY - 600] : tt < tLand + 0.1 ? lookW : [SX - 500, SY - 330]),
    pose: [[0, { armL: 10, foreL: 30, armR: 10, foreR: 30, handL: 'open', handR: 'open' }],
      [tYou, { armL: 14, foreL: 70, armR: 14, foreR: 70, handL: 'fist', handR: 'fist', shrug: 0.3, head: 2 }, 'outBack', 8 / 60],
      [tHun, { armL: 18, foreL: 110, armR: 18, foreR: 110, handL: 'fist', handR: 'fist', shrug: 0.6, head: 4 }, 'outBack', 8 / 60],
      [tLand + 0.1, { armL: 10, foreL: 40, armR: 10, foreR: 40, handL: 'open', handR: 'open', shrug: 0.2, head: -3 }, 'outBack', 10 / 60]],
    add: (tt) => ({ sweat: tt >= tHun ? 2 : 1, sweatK: 0.3 + 0.7 * seg(tt, tYou, tLand), sweatSize: 0.86 + 0.2 * seg(tt, tCh, tLand) + (tt >= tHun && tt < tHun + 0.12 ? 0.22 * (1 - seg(tt, tHun, tHun + 0.12)) : 0) }),
    nervous: [[0, 0.5], [tYou, 0.8], [tLand + 0.1, 0.35]], squash: [[tLand, 0.07]], blink: { seed: 5 }, ...RED_LOOK,
  });
  const bg = _resetWorld(ctx, cam, { insert: [{ after: 'mid', depth: 0.75, svg: _cubes(ctx.gt, { n: 14, seed: 13 }) }] });
  let s = boxBlur(bg, { x: -60, y: -60, w: 2040, h: 1200, sdx: 7, sdy: 7 });
  s += cam.layer(sam, 1);
  if (t >= tPop) {
    const p = seg(t, tPop, tPop + 8 / 60);
    const land = t >= tLand ? t - tLand : -1;
    const bump = land >= 0 ? 1 + 0.16 * Math.exp(-land / 0.09) * Math.cos(2 * Math.PI * 3 * land) : 1;
    let card = U2.counter({ x: 0, y: 0, value: V.show, speed: V.speed, label: 'Changes made by {you|orange}:' }, p);
    if (land >= 0) {
      const fl = Math.exp(-land / 0.22), cwi = U2.counterSize({}).w;
      card += path(rrPath(0, 0, cwi, 276, 42), { fill: '#FF2B45', opacity: r2(0.38 * fl + 0.06) });
      card += path(rrPath(-6, -6, cwi + 12, 288, 46), { fill: 'none', stroke: '#FF4A5E', strokeWidth: 8, opacity: r2(0.9 * fl + 0.25) });
    }
    const sc = CS * bump, ox = cx + cw / 2, oy = cy + ch / 2;
    s += cam.screen(g(card, { transform: `translate(${r2(ox)} ${r2(oy)}) scale(${r2(sc * 1000) / 1000}) translate(${r2(-cw / CS / 2)} ${r2(-ch / CS / 2)})` }), { shake: true });
  }
  return s + _cornerPill(ctx);
}

// =====================================================================================================================
// A10 — SAM "...Ish." Tiny shrug, half-lid guilty eyes; deadpan hold with the music cut (one slow blink).
// =====================================================================================================================
export function A10_ish(ctx) {
  const t = ctx.t, L = ctx.line('S00-L008');
  const tIsh = L ? L.at('Ish') : 0.21, tEnd = L ? L.word('Ish').t1 : 0.8;
  const tShrug = tIsh - 3 * FR, tStare = tEnd + 0.25, tBlink = tEnd + 0.62;
  _sfx(ctx, 'swish', 0, tShrug + 3 * FR, { db: -16, note: 'tiny shrug (optional, keep almost silent: deadpan, music is cut)' });
  const F0 = { x: -260, y: -20, z: 1.42 }, S = 2.15;
  const head0 = _w(F0, 960, 392);
  const SX = head0[0], SY = head0[1] - toonHeadY('sam') * S;
  const cam = ctx.cam({ keys: [[0, F0], [ctx.dur, { x: -258, y: -21, z: 1.42 * 1.012 }, 'inOutSine']], drift: 2, dolly: 1 });
  const sh = (k) => posePreset('shrug', 'sam', { k });
  const ish = { preset: 'ish' };
  const sam = ctx.actor('sam', {
    x: SX, y: SY, s: S, facing: [[0, -6], [tStare, 0]], talk: 'S00-L008',
    face: [[0, ish, 0], [tShrug, ish, 0.6], [tStare, { preset: 'ish', look: [0, 1] }, 0], [tBlink, { preset: 'ish', eyes: 'closed', look: [0, 1] }, 0], [tBlink + 5 * FR, { preset: 'ish', look: [0, 1] }, 0]],
    pose: [[0, sh(0)], [tShrug, sh(1), 'outBack', 7 / 60], [tEnd + 0.05, sh(0.72), 'inOutSine', 14 / 60]],
    add: { sweat: 1, sweatK: 0.9, sweatSize: 1.05 }, blink: false, nervous: 0.12, idle: 0.6, ...RED_LOOK,
  });
  const bg = _resetWorld(ctx, cam, { insert: [{ after: 'mid', depth: 0.75, svg: _cubes(ctx.gt, { n: 14, seed: 17 }) }] });
  let s = boxBlur(bg, { x: -60, y: -60, w: 2040, h: 1200, sdx: 7, sdy: 7 });
  s += cam.layer(sam, 1);
  return s + _cornerPill(ctx);
}

// =====================================================================================================================
// B1 — N "Let's scroll back... seven days." The UNDO HISTORY panel scrolls 412 changes back (DAY 7 -> DAY 1) over a
// lavender rewind of the street (the reset un-breaks into the normal street), 2-3-frame lavender flash-forwards of later
// set pieces, VHS scanlines and OSD, a tape-stop deceleration and a freeze on DAY 1.
// =====================================================================================================================
const B1 = { engage: 0.0, go: 0.28, stop: 2.6, items: 0 };
const HIST_END = U2.historyDayAt(1);                         // DAY 1 header at the top when the tape stops
// scroll position table: velocity ramps up (0.28-0.95), cruises, then decelerates linearly (tape stop) to 0 at B1.stop
const B1_TAB = (() => {
  const n = 2000, a = B1.go, b = B1.stop, out = new Float64Array(n + 1);
  const vel = (u) => (u < 0.25 ? ease.inOutSine(u / 0.25) : u < 0.62 ? 1 : Math.pow(1 - (u - 0.62) / 0.38, 2.2));
  let acc = 0; const vs = [];
  for (let i = 0; i <= n; i++) { vs.push(vel(i / n)); }
  for (let i = 0; i <= n; i++) { out[i] = acc; if (i < n) acc += (vs[i] + vs[i + 1]) / 2; }
  for (let i = 0; i <= n; i++) out[i] /= acc;
  return { n, a, b, out };
})();
function _b1Scroll(t) {
  const jog = 1.4 * ease.inOutSine(seg(t, B1.engage, B1.go));
  if (t <= B1.go) return jog;
  const T = B1_TAB, u = clamp((t - T.a) / (T.b - T.a)) * T.n, i = Math.min(T.n - 1, Math.floor(u)), fr = u - i;
  return 1.4 + (HIST_END - 1.4) * (T.out[i] + (T.out[i + 1] - T.out[i]) * fr);
}
function _b1TimeAt(sc) {          // first time the scroll reaches sc (bisection on the monotone table)
  let lo = 0, hi = B1.stop;
  for (let k = 0; k < 40; k++) { const m = (lo + hi) / 2; if (_b1Scroll(m) < sc) lo = m; else hi = m; }
  return hi;
}
const B1_FLASH = [{ t: 0.80, n: 3, set: 'lawn' }, { t: 1.30, n: 3, set: 'class' }, { t: 1.80, n: 2, set: 'kitchen' }];
const LAV = (d, k = 1) => rect(-60, -60, 2040, 1200, { fill: '#8D72E8', opacity: r2(0.42 * k) }) + rect(-60, -60, 2040, 1200, { fill: d.rad([[0.45, '#1C1045', 0], [1, '#1C1045', 0.6]], 0.5, 0.5, 0.75) });
function _flashSet(ctx, which) {
  if (which === 'lawn') {
    const set = ctx.memo('hook_b/street_day', () => street({ split: true }));
    const cam = ctx.cam({ keys: [[0, { x: 430, y: 110, z: 1.5 }]], drift: 0, blur: false, ghost: false });
    const d = new Defs();
    let gold = poly([[1104, 700], [1700, 700], [1730, 808], [1080, 808]], { fill: d.lin(['#FFE45C', '#F2A81A']) });
    gold += rect(1104, 702, 596, 10, { fill: '#FFFFFF', opacity: 0.45 });
    for (let i = 0; i < 9; i++) gold += sparkle(1120 + i * 66, 722 + (i % 3) * 26, 9 + (i % 2) * 7, '#FFFFFF', 0.95, i * 20);
    const kev = ctx.actor('kevin', { x: 1400, y: 798, s: 1.05, facing: 'tq-left', face: 'smug', pose: { armL: 150, foreL: 10, handL: 'open' }, t: 0 });
    return cam.set(set, { insert: [{ after: 'yard', depth: 0.75, svg: String(d) + gold + kev }] });
  }
  if (which === 'class') {
    const set = ctx.memo('hook_b/classroom', () => classroom({}));
    const cam = ctx.cam({ keys: [[0, { x: 0, y: 0, z: 1.05 }]], drift: 0, blur: false, ghost: false });
    const bri = ctx.actor('briggs', { x: 1380, y: 800, s: 1.55, facing: 'tq-left', face: 'shocked', pose: { armR: 150, foreR: 20, handR: 'open' }, t: 0 });
    const lily = ctx.actor('lily', { x: 700, y: 820, s: 1.5, facing: 'tq-right', face: 'laugh', t: 0 });
    return cam.set(set, { insert: [{ after: 'mid', depth: 1, svg: bri + lily }] });
  }
  const set = ctx.memo('hook_b/kitchen', () => kitchen({ tableY: 800 }));
  const cam = ctx.cam({ keys: [[0, { x: 0, y: 0, z: 1.02 }]], drift: 0, blur: false, ghost: false });
  const dad = ctx.actor('dad', { x: 1290, y: 930, s: 1.55, facing: 'tq-left', face: 'happy', props: { L: null, R: null }, pose: { armR: 150, foreR: 25, handR: 'open' }, t: 0 });
  const mom = ctx.actor('mom', { x: 520, y: 930, s: 1.55, facing: 'tq-right', face: 'skeptic', t: 0 });
  let s = cam.set(set, { insert: [{ after: 'light', depth: 1, svg: mom + dad }] });
  s += U.toast({ x: 560, y: 60, title: 'Subtitles: Honest', sub: 'Everyone says what they {mean}', icon: 'check' });
  return s;
}
function _vhs(d, t, o = {}) {
  // frame-sized scanlines + a rolling tracking band + OSD (normal blending only)
  const lines = d.pattern(8, 8, rect(0, 0, 8, 3, { fill: '#0A0620', opacity: 0.5 }));
  let s = rect(-40, -40, 2000, 1160, { fill: lines, opacity: o.lines ?? 0.18 });
  const by = ((t * 0.9 + 0.15) % 1) * 1240 - 120;
  s += rect(-40, by, 2000, 46, { fill: d.lin([[0, '#FFFFFF', 0], [0.5, '#E9E0FF', 0.22], [1, '#FFFFFF', 0]]) });
  for (let i = 0; i < 6; i++) s += rect(-40 + rand(41, Math.floor(t * 30), i) * 1900, by + 8 + i * 6, 60 + rand(42, Math.floor(t * 30), i) * 240, 3, { fill: '#FFFFFF', opacity: 0.35 });
  return s;
}
function _osd(label, on = true) {
  if (!on) return '';
  const st = { fontFamily: FONT.ui, fontWeight: 900, fontSize: 54, fill: '#FFFFFF', stroke: '#160C3A', strokeWidth: 8, paintOrder: 'stroke', letterSpacing: 4 };
  return text(70, 112, label, st);
}
export function B1_rewind(ctx) {
  const t = ctx.t;     // B1.stop (2.6) sits on the end of 'days' (S00-L009 ends 2.617 s into the shot)
  const sc = _b1Scroll(t), speed = (_b1Scroll(t) - _b1Scroll(t - FR)) * FPS;
  // cues: engage, take-off whoosh, one detent per day header passing, the flash-forwards, the tape stop
  _sfx(ctx, 'vhs_rewind', 3, 0, { note: 'rewind engage on the glitch cut' });
  _sfx(ctx, 'whoosh_long', 0, 0.62, { db: -6, note: 'scroll takes off (peak)' });
  for (const day of [6, 5, 4, 3, 2]) _sfx(ctx, 'slider_tick', 4, _b1TimeAt(U2.historyDayAt(day) - 0.2), { db: -4, note: `DAY ${day} header passes` });
  for (const F of B1_FLASH) _sfx(ctx, 'glitch', 2, F.t, { dur: 0.12, db: -4, note: `flash-forward (${F.set})` });
  _sfx(ctx, 'tape_stop', 0, B1.stop, { note: 'tape stop clunk: the list freezes on DAY 1' });
  _sfx(ctx, 'slider_tick', 4, B1.stop, { note: 'DAY 1 lands' });
  // background: the street rewinding through the week, zooming back, graded lavender: the Day 7 reset street (its bar
  // draining) -> the normal day street (after the first flash-forward) -> the 2:13 a.m. night street (after the last
  // one), where the tape stops; the lavender lifts during the stop so the freeze reads as night (C1 follows)
  const camB = ctx.cam({ keys: [[0, { x: -60, y: 10, z: 1.36 }], [B1.go, { x: -60, y: 10, z: 1.32 }], [B1.stop, { x: 20, y: 0, z: 1.0 }, 'inOutSine'], [ctx.dur + 1, { x: 20, y: 0, z: 1.0 }]], drift: 0, blur: false, ghost: false });
  const d = new Defs();
  const sw1 = B1_FLASH[0].t + B1_FLASH[0].n * FR, sw2 = B1_FLASH[2].t + B1_FLASH[2].n * FR;
  let bgw;
  if (t < sw1) {
    const set = ctx.memo('hook_b/reset', RESET_SET);
    bgw = camB.set(set, { skip: ['sky', 'grade'], insert: [{ after: 'defs2', depth: 0.08, svg: resetSky({ pct: lerp(95, 58, seg(t, 0, sw1)), t: -t * 3 }) }, { after: 'near', depth: 0, svg: resetGrade({ t: 0.5, tint: lerp(1, 0.4, seg(t, 0, sw1)) }) }] });
  } else if (t < sw2) {
    const set = ctx.memo('hook_b/street_day', () => street({ split: true }));
    bgw = camB.set(set, {});
  } else {
    const set = ctx.memo('hook_b/street_night', () => street({ split: true, night: 1 }));
    bgw = camB.set(set, {});
  }
  const lav = t < sw2 ? 1 : lerp(0.75, 0.3, ease.inOutSine(seg(t, B1.stop - 0.4, B1.stop)));
  const bgBlur = Math.min(10, 2 + Math.abs(speed) * 0.02);
  let s = boxBlur(bgw, { x: -60, y: -60, w: 2040, h: 1200, sdx: 1, sdy: bgBlur });
  s += String(d) + LAV(d, lav);
  s += scrollStreaks({ x: 0, y: 0, w: 1920, h: 1080, speed: speed * 98 / 60 * 0.35, seed: 31, t, color: '#E9E0FF', count: 16 });
  // the panel (screen-locked) with a 1-2 px VHS jitter while it runs
  const jit = t < B1.stop ? 1.5 * Math.sin(t * 71) : 0;
  const pop = seg(t, -0.05, 0.08);
  s += g(U2.undoHistory({ x: 580, y: 84, w: 760, h: 912, scroll: sc, speed }, pop), { transform: `translate(0 ${r2(jit)})` });
  // OSD: blinking rewind arrows while it runs; STOP square after the tape stop
  const running = t < B1.stop;
  s += _vhs(d, t, { lines: running ? 0.16 : 0.12 });
  s += running ? _osd('◀◀  REWIND', Math.floor(t * 4) % 2 === 0) : _osd('■  STOP');
  s += text(1850, 112, running ? `DAY ${U2.historyItems()[Math.min(418, Math.floor(sc + 0.2))].day}` : 'DAY 1', { fontFamily: FONT.ui, fontWeight: 900, fontSize: 54, fill: '#FFFFFF', stroke: '#160C3A', strokeWidth: 8, paintOrder: 'stroke', textAnchor: 'end', letterSpacing: 3 });
  // the flash-forwards: 2-3 frames of a later set piece, full frame, lavender, with tracking bands
  for (const F of B1_FLASH) {
    if (t >= F.t && t < F.t + F.n * FR) {
      const dd = new Defs();
      let fl = _flashSet(ctx, F.set) + String(dd) + LAV(dd, 0.6) + _vhs(dd, t + 0.4, { lines: 0.22 });
      fl = _bands(fl, t, 90 + F.n, { bands: 3, amount: 40 });
      s += fl + _osd('▶▶');
    }
  }
  // tape stop: the picture sags (vertical squash) over the last 0.25 s of the deceleration and stays sagged in the freeze
  const sag = seg(t, B1.stop - 0.25, B1.stop);
  if (sag > 0) s = g(s, { transform: `translate(0 ${r2(540 * 0.012 * sag)}) scale(1 ${r2(1 - 0.012 * sag) })` });
  return s;
}
