// hook_c.js — hook shots C1-C9: 2:13 a.m. (S00-L010..L016) and the ripple.
//   C1_bedtime      bedroom wide at night, the 2:13 clock, Sam wide awake on his phone; "2:13 A.M." card
//   C2_supposedly   close on Sam's phone-lit face: deadpan stare at the phone, one slow blink
//   C3_appappears   phone POV in bed: the phone buzzes twice, the SETTINGS notification drops in, "Downloaded: never",
//                   the REALITY SETTINGS icon pops into the empty slot on "downloaded"
//   C4_terms        POV: the tap opens the app, the Terms & Conditions card pops, 4,812 PAGES slams on "conditions"
//   C5_pagestack    bedroom wide: pages pour out of the phone into a tower that climbs (the camera tilts up with it)
//                   and THUNKs into the ceiling on "pages"; the odometer rolls to 4,812 with the number words
//   C6_squint       close-up: Sam reads page one, squinting, eyes scanning line by line; punch-in on "every"
//   C7_flick        the half-second flick: pages riffle past, page 4,812 holds readable for exactly 3 frames, then
//                   flies off to "All 4,812 pages read · reading time 0.5 s"
//   C8_agree        POV: the big green I AGREE; the thumb hovers, lifts and presses on "AGREE" (music drop before it)
//   C9_ripple       the sub boom: a white ring + grid wave through the room, snap zoom-out to the house, snap
//                   zoom-out to the street (windows flicker on to the music's boot-up boops)
// Plan: docs/HOOK_BOARD.md rows C1-C9, times: episodes/hook/SHOTS.md. Word times come from the voice lines
// (ctx.line(id).word(w)) with the built timeline's values as fallbacks, so the shots follow a rebuilt timeline.
//
// SFX cues (same convention as hook_a.js / hook_b.js): _sfx(ctx, name, v, tEv, o) registers
// ctx.cue(name, t, {v, ev, sync_ms, ...o}) with t = the clip START (local s), chosen so the sfx_map variant's sync point
// lands on the visual frame tEv; ev is that frame in global s. Hints in o: db (level vs the -18 LUFS map level),
// dur (trim length in s), note. Synthesised names (page_flip, page_riffle, counter_tick, dog_woof) sync at 0.
import { bedroom, BEDROOM, street, STREET, twinkle, nightify } from '../sets.js';
import * as U from '../ui.js';
import * as U2 from '../ui2.js';
import { glyph } from '../ui_icons.js';
import { sparkle, sparkles, shockRing, boxBlur, scrollStreaks } from '../fx.js';
import { FONT, Defs, text, rect, circle, ellipse, path, poly, g, esc, rrPath, gearPath, shade, ink, textW, popIn, st, line } from '../ui_style.js';
import { clamp, lerp, seg, ease, rand, track } from '../anim/motion.js';
import { posePreset } from '../cast.js';
import { frameOn } from '../anim/camera.js';

// =====================================================================================================================
// shared helpers (private: only exported functions are registered as shots)
// =====================================================================================================================
const FPS = 60, FR = 1 / FPS, TAU = Math.PI * 2;
const r2 = (n) => Math.round(n * 100) / 100, r3 = (n) => Math.round(n * 1000) / 1000;
/** opacity as a STRING with 3 decimals: ui_style.attrs() rounds numeric attributes to 0.1, which makes fades step */
const O = (v) => String(Math.round(Math.max(0, Math.min(1, v)) * 1000) / 1000);
const NUN = (size, weight = 900, fill = '#FFFFFF', extra = {}) => ({ fontFamily: FONT.ui, fontWeight: weight, fontSize: size, fill, ...extra });
const LIL = (size, fill = '#FFFFFF', extra = {}) => ({ fontFamily: FONT.title, fontSize: size, fill, ...extra });

// sync points (ms into the clip) of the audio/sfx_map.json variants used here
const SYNC = {
  ui_tap: [2.5, 2.5, 30, 7.5, 7.5, 7.5], ui_confirm: [2.5, 7.5], ui_select: [10, 10, 22.5, 30, 45],
  notif_ping: [5, 2.5, 12.5, 17.5, 2.5, 7.5, 7.5], phone_vibrate: [25, 7.5, 20], magic_shimmer: [2.5, 1515, 5, 10],
  popup_whoosh: [207.5, 115, 87.5, 135, 240, 10], whoosh_short: [250, 270, 277.5, 275, 337.5, 347.5, 277.5, 812.5, 637.5, 710, 737.5],
  whoosh_long: [327.5, 2562.5], swish: [47.5, 65, 60, 130, 125, 17.5], slide_whistle_up: [55, 50, 32.5, 35],
  slide_whistle_down: [37.5, 35, 37.5, 35], sub_boom: [2.5, 22.5, 252.5, 57.5], bass_drop: [67.5, 2.5],
  impact_hit: [7.5, 140, 42.5, 2.5], clock_tick: [10, 10, 7.5, 30], cartoon_pop: [10, 22.5, 10, 10, 7.5, 10, 12.5, 10, 140],
  bonk: [17.5, 17.5, 22.5, 20], boing: [45, 5, 10, 15, 15, 7.5, 7.5, 15, 7.5], glitch: [70, 7.5, 32.5, 12.5],
  stamp: [10, 10, 7.5, 15], toggle: [37.5, 12.5, 12.5, 20, 12.5, 35], success_chime: [2.5, 7.5, 15, 10, 10, 7.5],
  zip: [170, 115], reverse_cymbal: [1525, 1390, 3175],
};
/** register an SFX cue whose sync point hits local time tEv (call unconditionally: cues are collected at the shot start) */
function _sfx(ctx, name, v, tEv, o = {}) {
  const tbl = SYNC[name], sm = tbl ? tbl[v % tbl.length] : 0;
  ctx.cue(name, tEv - sm / 1000, { v, ev: r3(ctx.start + tEv), sync_ms: sm, ...o });
}
/** local start / end of a word of a voice line, with the built timeline's value as fallback */
function _w(ctx, id, word, fb, n = 0) { const L = ctx.line(id); const w = L && L.word(word, n); return w ? w.t0 : fb; }
function _we(ctx, id, word, fb, n = 0) { const L = ctx.line(id); const w = L && L.word(word, n); return w ? w.t1 : fb; }
/** local frame index inside the shot (exact integer: frame-snapped holds) */
const _lf = (ctx) => ctx.frame - Math.round(ctx.start * FPS);
/** damped bump 1 + a e^(-u/d) cos(...) after t0 (UI landings) */
const _bump = (t, t0, a = 0.12, d = 0.09, hz = 3) => (t < t0 ? 1 : 1 + a * Math.exp(-(t - t0) / d) * Math.cos(TAU * hz * (t - t0)));

// ---------- sets ----------
const _bed = (ctx) => ctx.memo('hook_c/bedroom{clock:2:13,blanket:sit}', () => bedroom({ clock: '2:13', blanket: 'sit' }));
const _street = (ctx) => ctx.memo('hook_c/street{night:1,split:true}', () => street({ night: 1, split: true }));

// ---------- Sam in bed (night look: violet tint + phone light from below) ----------
const NIGHT_TINT = { color: '#5562A4', k: 0.55 };
const _plight = (k = 0.85) => ({ color: '#CFE8FF', k: r3(k), from: 'phone' });
/** phone-screen flicker on the face: a short brightening after each scroll tap (local times) */
const _flicker = (taps, base = 0.85) => (tt) => { let k = base; for (const tp of taps) if (tt >= tp) k += 0.14 * Math.exp(-(tt - tp) / 0.12); return _plight(Math.min(1, k)); };
function _sam(ctx, o = {}) {
  const B = BEDROOM.sam;
  return ctx.actor('sam', { x: B.x, y: B.y, s: B.s, legs: false, props: { R: 'phoneBack' }, pose: posePreset('bedSit', 'sam'), tint: NIGHT_TINT, light: _plight(), blink: { seed: 21 }, ...o });
}

// ---------- ambient life in the bedroom ----------
const LIGHTS = [[-300, 64], [-120, 92], [60, 104], [240, 102], [420, 88], [600, 70], [780, 62], [960, 72], [1140, 74]];
const LCOL = ['#FFD36A', '#FF8FB0', '#7FE0FF', '#B7FF8A'];
/** the string lights breathe (soft halos on their own phases; plain alpha, depth .75) */
function _lightLife(gt) {
  const d = new Defs();
  let s = '';
  LIGHTS.forEach(([lx, ly], i) => {
    const k = 0.5 + 0.5 * Math.sin(TAU * (0.45 + 0.07 * (i % 3)) * gt + i * 1.9);
    s += circle(lx, ly + 18, 40, { fill: d.rad([[0, LCOL[i % 4], 0.5], [1, LCOL[i % 4], 0]]), opacity: O(0.12 + 0.4 * k) });
  });
  return String(d) + s;
}
/** stars twinkling in the window (far layer, the wall masks them) */
function _windowStars(gt) {
  const { x, y, w, h } = BEDROOM.window;
  let s = '';
  for (let i = 0; i < 9; i++) {
    const px = x + 30 + rand(77, i, 1) * (w - 60), py = y + 24 + rand(77, i, 2) * h * 0.55;
    const k = Math.max(0, Math.sin(TAU * (0.6 + rand(77, i, 3) * 0.9) * gt + rand(77, i, 4) * 6.3));
    if (k > 0.05) s += sparkle(px, py, 5 + 7 * k, '#FFFFFF', 0.45 + 0.55 * k, gt * 30);
  }
  return s;
}
/** the night vignette in SCREEN space (the sets' 'grade' layers are depth 0, which cam.set still scales by the zoom:
 *  under 1x they shrink into a visible box, so every shot here skips them and draws this instead) */
function _vig(color = '#120C2E', a = 0.5) {
  const d = new Defs();
  return String(d) + rect(-40, -40, 2000, 1160, { fill: d.rad([[0.55, color, 0], [1, color, a]], 0.5, 0.5, 0.75) });
}
/** the bedroom through the camera: window stars, breathing string lights, Sam (after 'mid', under the blanket) and
 *  extra inserts, plus the screen-space night vignette; o.skip / o.only pass through to cam.set */
function _bedWorld(ctx, cam, o = {}) {
  const gt = ctx.gt;
  const ins = [{ after: 'far', depth: 0.3, svg: _windowStars(gt) }, { after: 'mid', depth: 0.75, svg: _lightLife(gt) }];
  if (o.sam) ins.push({ after: 'mid', depth: 0.75, svg: o.sam });
  for (const i of o.insert || []) ins.push(i);
  return cam.set(_bed(ctx), { insert: ins, skip: [...(o.skip || []), 'grade'], only: o.only }) + _vig();
}
/** close-up depth of field (bible 1.6: DOF only in close-ups): the room behind blurred, Sam + blanket + light crisp */
function _bedClose(ctx, cam, sam, o = {}) {
  const gt = ctx.gt, set = _bed(ctx);
  const back = cam.set(set, { only: ['far', 'mid'], insert: [{ after: 'far', depth: 0.3, svg: _windowStars(gt) }, { after: 'mid', depth: 0.75, svg: _lightLife(gt) }, ...(o.back || [])] });
  const front = cam.set(set, { only: ['blanket', 'light', 'phone', 'near'], insert: [{ after: 'defs', depth: 0.75, svg: sam }, ...(o.front || [])] });
  const b = o.blur ?? 6;
  return boxBlur(back, { x: -60, y: -60, w: 2040, h: 1200, sdx: b, sdy: b }) + front + _vig('#120C2E', 0.42);
}

// ---------- POV pieces ----------
/** the blanket over Sam's knees, filling the lower left of a POV frame (screen space, toy plastic, gear pattern) */
function _knees(dx = 0, dy = 0) {
  const d = new Defs(), bl = '#2F4FB8';
  const body = `M-80 1180L-80 930C40 820 250 760 430 790C600 820 700 900 760 1000C790 1060 800 1120 800 1180Z`;
  let s = path(body, { fill: d.lin([shade(bl, 0.07), shade(bl, -0.1)], 'd'), stroke: ink(bl), strokeWidth: 6, strokeLinejoin: 'round' });
  s += g(rect(-100, 740, 920, 460, { fill: d.pattern(150, 120, path(gearPath(36, 36, 19, 13, 8, 0, 0.5), { fill: '#5A7AE0', opacity: 0.5 }) + circle(36, 36, 6, { fill: bl }) + twinkle(108, 92, 10, '#7F9CF0', 0.5)) }), { clipPath: d.clip(path(body)) });
  s += path('M60 900C180 830 320 806 450 822', { fill: 'none', ...st('#FFFFFF', 14), opacity: 0.18 });
  s += path('M200 1100C300 1010 470 980 620 1040', { fill: 'none', ...st(shade(bl, -0.18), 10), opacity: 0.4 });
  // the phone's light on the blanket
  s += ellipse(560, 960, 380, 170, { fill: d.rad([[0, '#9FE0FF', 0.28], [1, '#9FE0FF', 0]]) });
  return String(d) + g(s, { transform: `translate(${r2(dx)} ${r2(dy)})` });
}
/** the night bedroom behind a POV phone: blurred, framed on the window side */
function _povBack(ctx, cam) {
  return boxBlur(_bedWorld(ctx, cam, {}), { x: -60, y: -60, w: 2040, h: 1200, sdx: 7, sdy: 7 });
}
/** a slight violet night wash over the POV hand + phone body (plain alpha; the lit screen is drawn on top again) */
const _nightWash = (k = 0.18) => rect(-60, -60, 2040, 1200, { fill: '#2A2660', opacity: k });

// the REALITY SETTINGS icon slot on homeScreen (12th tile) in SCREEN space
const ICON = (() => { const cols = 4, tile = 118, gx = (U2.SCREEN.w - cols * tile) / (cols + 1); return [gx + tile / 2 + 3 * (tile + gx), 170 + tile / 2 + 2 * 196]; })();

/** 4,812 PAGES sticker (the terms() sticker look), centred on (x, y), scale k, rotation rot */
function _pagesSticker(x, y, k = 1, rot = -7) {
  const d = new Defs();
  let s = path(rrPath(-150, -78, 300, 156, 34), { fill: shade(U.UI.orange2, -0.18), transform: 'translate(0 8)' });
  s += path(rrPath(-150, -78, 300, 156, 34), { fill: d.lin(['#FFB070', U.UI.orange, U.UI.orange2]), stroke: '#FFFFFF', strokeWidth: 7 });
  s += path(rrPath(-150, -78, 300, 156, 34), { fill: 'none', stroke: ink(U.UI.orange), strokeWidth: 3 });
  s += text(0, 16, '4,812', LIL(82, '#FFFFFF', { textAnchor: 'middle', stroke: ink(U.UI.orange), strokeWidth: 8, paintOrder: 'stroke', strokeLinejoin: 'round' }));
  s += text(0, 56, 'PAGES', NUN(30, 900, '#FFF2E0', { textAnchor: 'middle', letterSpacing: 4 }));
  return String(d) + g(s, { transform: `translate(${r2(x)} ${r2(y)}) rotate(${r2(rot)}) scale(${r3(k)})` });
}

// =====================================================================================================================
// C1 — "Bedtime." The bedroom at night, wide: the 2:13 clock glowing, Sam sitting up under the blanket, wide awake and
// phone-lit. A "2:13 A.M." card pops top left; on "Bedtime." Sam's eyes dart up to us (caught), then back to the phone.
// =====================================================================================================================
function _timeCard(x, y, p) {
  const d = new Defs(), w = 318, h = 104;
  let s = U.glassCard(d, x, y, w, h, 34);
  s += circle(x + 58, y + 52, 34, { fill: d.rad([[0, '#FFE9A6', 0.35], [1, '#FFE9A6', 0]]) });
  s += g(glyph('moon', '#FFE9A6'), { transform: `translate(${x + 58} ${y + 54}) scale(0.62)` });
  s += text(x + 100, y + 76, '2:13', LIL(64, '#FFFFFF', { letterSpacing: 1 }));
  s += text(x + 108 + textW('2:13', 64, 'lil'), y + 74, 'A.M.', NUN(32, 900, '#FF6A85', { letterSpacing: 1 }));
  return popIn(String(d) + s, x + w / 2, y + h / 2, p, { bbox: { x, y, w, h, r: 34 }, ringGrow: 40 });
}
export function C1_bedtime(ctx) {
  const t = ctx.t, dur = ctx.dur;
  const tBed = _w(ctx, 'S00-L010', 'Bedtime', 0.5);
  const tCard = 0.1, tLook = tBed + 0.06, tBack = tBed + 0.5;
  _sfx(ctx, 'clock_tick', 1, 0.0, { db: -4, note: 'cut: the 2:13 clock ticks (12 O\'Clock Magic first note on the cut too)' });
  _sfx(ctx, 'cartoon_pop', 2, tCard + 3 * FR, { db: -6, note: '2:13 A.M. card pops' });
  _sfx(ctx, 'ui_tap', 3, tBed - 0.18, { db: -14, note: 'Sam scrolls (phone light flickers)' });
  _sfx(ctx, 'ui_tap', 4, tBack + 0.12, { db: -14, note: 'scroll tap' });
  const cam = ctx.cam({ keys: [[0, { x: 0, y: 14, z: 1.0 }], [dur, { x: 8, y: 4, z: 1.04 }, 'inOutSine']], drift: 4 });
  const sam = _sam(ctx, {
    face: [[0, { preset: 'neutral', look: [0, 4] }], [tLook, { preset: 'surprised', look: [-1, -2] }], [tBack, { preset: 'neutral', look: [0, 4] }, 0.5]],
    light: _flicker([tBed - 0.18, tBack + 0.12]), facing: [[0, 0], [tLook, -6], [tBack, 0]],
  });
  let s = _bedWorld(ctx, cam, { sam });
  // the bedside clock breathes red (it is 2:13)
  const C = BEDROOM.clock, cp = cam.toScreen([C.x, C.y], 0.75), ck = 0.5 + 0.5 * Math.sin(TAU * 1.0 * ctx.gt);
  const d = new Defs();
  s += String(d) + circle(cp[0], cp[1], 70 * cam.state.z, { fill: d.rad([[0, '#FF3B5C', 0.3], [1, '#FF3B5C', 0]]), opacity: O(0.4 + 0.6 * ck) });
  s += cam.screen(_timeCard(56, 48, t < tCard ? 0 : seg(t, tCard, tCard + 9 * FR)));
  return s;
}

// =====================================================================================================================
// C2 — "Supposedly." Close on Sam's phone-lit face: deadpan stare at the phone, one slow blink, the screen light flickers
// as he scrolls.
// =====================================================================================================================
export function C2_supposedly(ctx) {
  const t = ctx.t, dur = ctx.dur;
  const tSup = _w(ctx, 'S00-L010', 'Supposedly', 0.113);
  const tBlink = tSup + 0.36, taps = [0.02, tSup + 0.62];
  _sfx(ctx, 'ui_tap', 4, taps[0], { db: -12, note: 'cut: scroll tap, the screen light jumps' });
  _sfx(ctx, 'ui_tap', 3, taps[1], { db: -14, note: 'scroll tap' });
  const F = frameOn([826, 520], 2.3, [930, 470]);
  const cam = ctx.cam({ keys: [[0, F], [dur, { ...F, y: F.y - 4, z: F.z * 1.03 }, 'inOutSine']], drift: 3 });
  const dp = (o = {}) => ({ preset: 'deadpan', look: [0, 4.5], ...o });
  const sam = _sam(ctx, {
    face: [[0, dp(), 0], [tBlink, dp({ eyes: 'half' }), 0], [tBlink + 2 * FR, dp({ eyes: 'closed' }), 0], [tBlink + 6 * FR, dp({ eyes: 'half' }), 0], [tBlink + 8 * FR, dp(), 0]],
    blink: false, light: _flicker(taps), idle: 0.6, facing: 4,
  });
  return _bedClose(ctx, cam, sam, { blur: 5 });
}

// =====================================================================================================================
// C3 — "An app you never downloaded." Phone POV in bed: the phone double-buzzes in Sam's hand (rattle + shake), the
// SETTINGS notification drops in on "app", "Downloaded: never" gets a marker on "never", and the REALITY SETTINGS icon
// pops into the empty home-screen slot on "downloaded" (shimmer, sparkles, punch-in). The thumb moves to it at the end.
// =====================================================================================================================
const POV_PHONE = { x: 1010, y: 600, s: 0.6, rot: -5 };
export function C3_appappears(ctx) {
  const t = ctx.t, dur = ctx.dur;
  const tApp = _w(ctx, 'S00-L011', 'app', 0.313), tNever = _w(ctx, 'S00-L011', 'never', 0.793), tDl = _w(ctx, 'S00-L011', 'downloaded', 1.193);
  const tBz = 0.03, tThumb = Math.max(tDl + 0.55, dur - 0.36);
  // phone_vibrate[1] is a double buzz: 0-0.42 s and 0.52-0.96 s into the clip
  const buzzK = (tt) => { const u = tt - tBz, w = (a, b) => clamp(Math.min((u - a) / (2 * FR), (b - u) / (3 * FR))); return Math.max(w(0, 0.42), w(0.52, 0.96)); };
  _sfx(ctx, 'phone_vibrate', 1, tBz, { note: 'double buzz: the phone rattles in his hand (cut transient)' });
  _sfx(ctx, 'popup_whoosh', 2, tApp + 5 * FR, { db: -4, note: 'notification drops in' });
  _sfx(ctx, 'notif_ping', 0, tApp + 5 * FR, { note: "notification lands on 'app'" });
  _sfx(ctx, 'cartoon_pop', 4, tNever, { db: -8, note: "marker on 'Downloaded: never'" });
  _sfx(ctx, 'cartoon_pop', 7, tDl, { db: -4, note: "the icon pops into the empty slot on 'downloaded'" });
  _sfx(ctx, 'magic_shimmer', 2, tDl + FR, { note: 'icon shimmer + sparkles' });
  _sfx(ctx, 'swish', 3, tDl + 0.5 + 4 * FR, { db: -8, note: 'the notification is swiped away' });
  _sfx(ctx, 'swish', 1, tThumb + 0.12, { db: -12, note: 'thumb moves to the new icon' });
  const P = POV_PHONE, iconF = U2.phonePoint(P, ICON[0], ICON[1]);
  const shake = [{ t: tBz, amp: 7, decay: 0.16, freq: 30 }, { t: tBz + 0.52, amp: 8, decay: 0.16, freq: 30 }, { t: tDl, amp: 5, decay: 0.07 }];
  const camB = ctx.cam({ keys: [[0, { x: 330, y: -30, z: 1.12 }], [dur, { x: 344, y: -36, z: 1.15 }, 'inOutSine']], drift: 5, shake });
  const camF = ctx.cam({ keys: [[0, { z: 1.0 }], [dur, { x: 12, y: -6, z: 1.04 }, 'inOutSine']], drift: 0, shake, punch: [{ t: tDl, k: 1.07, at: iconF, settle: 0.3 }] });
  // the phone: rattle amplitude follows the buzzes; the home screen gets the icon on "downloaded"
  const bk = buzzK(t);
  const kIcon = t < tDl ? 0 : seg(t, tDl, tDl + 10 * FR);
  const scr = U2.homeScreen({ time: '2:13', newApp: kIcon, t, badge: 1, glow: 0.6 + 0.3 * Math.sin(TAU * 1.5 * t), wiggle: { t, amp: 4 * bk } });
  let sparks = '';
  if (t >= tDl && t < tDl + 0.9) {
    const u = seg(t, tDl, tDl + 0.9);
    sparks = sparkles({ x: ICON[0] - 120, y: ICON[1] - 130, w: 240, h: 240, count: 9, seed: 31, t: t * 1.4, size: 30 * (1 - u * 0.5) });
    sparks = g(sparks, { opacity: O(Math.sin(Math.PI * Math.min(1, u * 1.6)) * 0.95 + 0.05) });
  }
  const th = t < tThumb ? { x: 670, y: 1210, press: 0 } : (() => {
    const u = ease.inOutCubic(seg(t, tThumb, tThumb + 0.24));
    return { x: lerp(670, ICON[0] + 16, u), y: lerp(1210, ICON[1] + 34, u), press: 0 };
  })();
  const ph = U2.phone({ ...P, screen: scr + sparks, glow: 0.85 + 0.15 * bk, thumb: th, shake: bk > 0 ? { amp: 9 * bk, t, freq: 26 } : 0, t });
  let s = _povBack(ctx, camB);
  s += camF.layer(_knees(), 1);
  s += camF.layer(ph, 1);
  // the notification drops in from the top on "app" (rattling with the second buzz) and is swiped away after the icon
  // lands, before the thumb reaches for the icon
  const tOut = tDl + 0.5;
  if (t >= tApp - 2 * FR && t < tOut + 8 * FR) {
    const u = seg(t, tApp - 2 * FR, tApp + 7 * FR), uo = seg(t, tOut, tOut + 8 * FR);
    const y = lerp(-240, 40, ease.outBack(u)) - 330 * ease.inBack(uo);
    const nx = 1010 - 430;
    let card = U2.notifyCard({ x: nx, y, w: 860, title: 'SETTINGS', sub: 'for {real life|orange}', note: 'Downloaded: never', time: 'now', rattle: Math.max(bk, 0.25 * (1 - seg(t, tApp, tApp + 0.4))), t });
    if (t >= tNever) {
      // a marker pill pops over "Downloaded: never" (covers the original small print, redraws it bold)
      const mk = ease.outBack(seg(t, tNever, tNever + 6 * FR)), mw = textW('Downloaded: never', 26, 'n900') + 34;
      const mx = nx + 196 + 8, my = y + 150, cx = mx + mw / 2, cy = my + 17;
      const pill = path(rrPath(mx, my, mw, 34, 17), { fill: '#FFE14D', stroke: '#C99A12', strokeWidth: 2.5 }) + text(cx, my + 25, 'Downloaded: never', NUN(26, 900, '#3A2A08', { textAnchor: 'middle' }));
      card += g(pill, { transform: `translate(${r2(cx)} ${r2(cy)}) scale(${r3(Math.max(0.01, mk * _bump(t, tNever + 6 * FR, 0.08, 0.08)))}) translate(${r2(-cx)} ${r2(-cy)})` });
    }
    s += camF.layer(card, 1);
  }
  return s;
}

// =====================================================================================================================
// C4 — "First, the terms and conditions." POV: the thumb taps the new icon on the cut, the app zooms open, the Terms &
// Conditions card pops on "First"; the title pulses on "terms"; the 4,812 PAGES sticker slams on "conditions". At the
// end the phone starts to tremble and paper edges peek out of the top of the screen (into C5's page pour).
// =====================================================================================================================
const C4_PHONE = { x: 980, y: 566, s: 0.84, rot: -3 };     // a closer POV than C3 (the screen fills the frame)
const TERMS_BOX = { x: 22, y: 236, w: 676, h: 1000 };
export function C4_terms(ctx) {
  const t = ctx.t, dur = ctx.dur;
  const tFirst = _w(ctx, 'S00-L012', 'First', 0.197), tTerms = _w(ctx, 'S00-L012', 'terms', 0.867), tCond = _w(ctx, 'S00-L012', 'conditions', 1.427);
  const tTap = 0.03, tOpen = 0.1, tPop = tFirst - 6 * FR, tSlam = tCond + 4 * FR, tSpill = dur - 0.42;
  const spills = [tSpill, tSpill + 0.1, tSpill + 0.19, tSpill + 0.27, tSpill + 0.34];
  _sfx(ctx, 'ui_tap', 3, tTap, { note: 'cut: thumb taps the new icon' });
  _sfx(ctx, 'ui_select', 1, tOpen, { db: -6, note: 'the app zooms open' });
  _sfx(ctx, 'popup_whoosh', 0, tFirst + 2 * FR, { note: "Terms & Conditions card pops on 'First'" });
  _sfx(ctx, 'cartoon_pop', 3, tTerms, { db: -10, note: "title pulse on 'terms'" });
  _sfx(ctx, 'stamp', 3, tSlam, { note: "4,812 PAGES sticker slams on 'conditions'" });
  _sfx(ctx, 'impact_hit', 3, tSlam, { db: -10, dur: 0.6, note: 'sticker slam weight' });
  spills.forEach((ts, i) => { if (i % 2 === 0) _sfx(ctx, 'page_flip', 0, ts, { db: -4 - i, note: 'synth: a sheet shoots out of the screen' }); });
  _sfx(ctx, 'whoosh_short', 0, dur, { db: -6, note: 'paper whoosh peaking on the C5 cut (pages pour out)' });
  const P = C4_PHONE, B = TERMS_BOX;
  const stkS = [B.x + B.w - 156, B.y + 150 + (B.h - 340) * 0.6], stk = U2.phonePoint(P, stkS[0], stkS[1]), ttl = U2.phonePoint(P, B.x + 300, B.y + 76);
  const shake = [{ t: tTap, amp: 4, decay: 0.06 }, { t: tSlam, amp: 12, decay: 0.08 }];
  const camB = ctx.cam({ keys: [[0, { x: 300, y: -10, z: 1.2 }], [dur, { x: 310, y: -16, z: 1.23 }, 'inOutSine']], drift: 5, shake });
  const camF = ctx.cam({ keys: [[0, { z: 1.0 }], [dur, { x: 8, y: -8, z: 1.04 }, 'inOutSine']], drift: 0, shake,
    punch: [{ t: tTerms, k: 1.05, at: ttl, settle: 0.25, keep: 0 }, { t: tSlam, k: 1.07, at: stk, settle: 0.3, keep: 0.02 }] });
  // screen: home (icon pressed) -> the app zooms open from the icon -> terms card (+ the sticker slam)
  const press = t < tTap + 0.1 ? clamp(Math.min(seg(t, 0, tTap), 1 - seg(t, tTap + 0.04, tTap + 0.1))) : 0;
  let scr;
  if (t < tOpen) scr = U2.homeScreen({ time: '2:13', newApp: 1, t: t + 2.27, badge: 1, glow: 0.8 });
  else {
    const k = ease.outCubic(seg(t, tOpen, tOpen + 9 * FR));
    let app = U2.appScreen({ time: '2:13', crumb: 'Settings › {Terms|purple}', content: t < tPop ? '' : U.terms({ ...B, sticker: false, page: 1 }, seg(t, tPop, tPop + 9 * FR)) });
    if (t >= tCond) {
      const u = seg(t, tCond, tSlam), kk = t < tSlam ? lerp(2.4, 0.92, ease.inQuad(u)) : 1 - 0.08 * Math.exp(-(t - tSlam) / 0.07) * Math.cos(TAU * 5 * (t - tSlam));
      app += _pagesSticker(stkS[0], stkS[1], kk, lerp(-24, -7, ease.outCubic(u)));
    }
    scr = k >= 1 ? app : U2.homeScreen({ time: '2:13', newApp: 1, t: t + 2.27, badge: 1 }) + g(app, { transform: `translate(${r2(ICON[0])} ${r2(ICON[1])}) scale(${r3(lerp(0.14, 1, k))}) translate(${r2(-ICON[0])} ${r2(-ICON[1])})`, opacity: O(clamp(k * 3)) });
  }
  if (press > 0) scr += U.tapRing(ICON[0], ICON[1], seg(t, tTap, tTap + 0.25), '#FFFFFF');
  // the end: the phone trembles and sheets shoot out of the screen, up and out of the frame (into C5's pour)
  const rk = seg(t, tSpill - 0.1, tSpill + 0.1);
  const th = t < tTap + 0.16 ? { x: ICON[0] + 8 * (1 - press), y: ICON[1] + 18, press } : (() => {
    const u = ease.inOutCubic(seg(t, tTap + 0.16, tTap + 0.5));
    return { x: lerp(ICON[0] + 8, 668, u), y: lerp(ICON[1] + 18, 1250, u), press: 0 };
  })();
  const ph = U2.phone({ ...P, screen: scr, glow: 0.85, thumb: th, shake: rk > 0 ? { amp: 6 * rk, t, freq: 22 } : 0, buzz: false, t });
  let s = _povBack(ctx, camB);
  s += camF.layer(ph, 1);
  let sh = '';
  spills.forEach((ts, i) => {
    if (t < ts) return;
    const u = seg(t, ts, ts + 0.3), e = ease.inQuad(u), [px, py] = U2.phonePoint(P, 200 + ((i * 197) % 330), 520 + ((i * 131) % 200));
    const x = px + (i % 2 ? 1 : -1) * 260 * e, y = py - 1100 * e, k = lerp(0.62, 1.05, e);
    sh += g(_sheet(0, 0, k, i + 3), { transform: `translate(${r2(x)} ${r2(y)}) rotate(${r2((i % 2 ? 1 : -1) * (8 + 40 * e))})` });
  });
  if (sh) s += camF.layer(sh, 1);
  return s;
}

/** one loose sheet of fine print (centred at x, y; scale k; seed for the line lengths) */
function _sheet(x, y, k = 1, seed = 1) {
  const d = new Defs(), w = 220, h = 280;
  let s = path(rrPath(-w / 2, -h / 2, w, h, 12), { fill: d.lin(['#FFFFFF', '#E6EBF7']), stroke: '#9AA6CC', strokeWidth: 3 });
  for (let i = 0; i < 9; i++) s += rect(-w / 2 + 22, -h / 2 + 30 + i * 25, (w - 44) * (0.55 + 0.45 * rand(seed, i, 7)), 8, { rx: 4, fill: '#AEB7D3' });
  return String(d) + g(s, { transform: `translate(${r2(x)} ${r2(y)}) scale(${r3(k)})` });
}

// =====================================================================================================================
// C5 — "Four thousand, eight hundred and twelve pages." Bedroom wide: pages pour out of the phone in arcs onto a tower
// that grows beside Sam on the bed; the camera tilts up with it; the odometer rolls with the number words (4,000 on
// "thousand", 4,800 on "hundred", 4,812 on "twelve"); on "pages" the tower THUNKs into the ceiling (crack, plaster dust,
// shake). Sam's eyes ride up with the top, scared -> shocked.
// =====================================================================================================================
const STK = { cx: 1332, base: 872, w: 236, depth: 40 };   // on the floor right of the bed, in front of the window wall
STK.top = BEDROOM.ceilY + 30;                       // tower top at full height (its top face reaches the moulding)
STK.th = (STK.base - STK.top) / 4812;               // px per page
const PHONE_W = [846, 630];                         // the phone in Sam's hands (world)
/** paper at night: violet-graded like the room (colour-mapped, no blend modes) */
const _nightPaper = (svg, tag) => nightify(svg, 0.42, tag);
/** the tower of pages (world, depth .75): n pages, top pinned at `top` */
function _tower(n, top, wob, gt) {
  return _nightPaper(U2.pageStack({ cx: STK.cx, base: STK.base, n, w: STK.w, th: (STK.base - top) / n, wobble: wob, t: gt, depth: STK.depth, seed: 11 }), 'pg');
}
/** for later bedroom shots (continuity: the tower stays in the room after C5): the full-height tower as a cam.set
 *  insert. o.night 0..1 (0.42 = the 2:13 a.m. grade, 0 = daylight), o.wobble. Exported with a leading underscore so
 *  frame.js does not register it as a shot. */
export function _pageTowerInsert(gt = 0, o = {}) {
  const svg = U2.pageStack({ cx: STK.cx, base: STK.base, n: 4812, w: STK.w, th: STK.th, wobble: o.wobble ?? 0.2, t: gt, depth: STK.depth, seed: 11 });
  const k = o.night ?? 0.42;
  return { after: 'blanket', depth: 0.75, svg: k > 0 ? nightify(svg, k, 'pt' + Math.round(k * 100)) : svg };
}
function _c5Times(ctx) {
  const id = 'S00-L013';
  return { four: _w(ctx, id, 'Four', 0.203), th: _w(ctx, id, 'thousand', 0.523), eight: _w(ctx, id, 'eight', 1.223), hun: _w(ctx, id, 'hundred', 1.483),
    tw: _w(ctx, id, 'twelve', 1.963), pg: _w(ctx, id, 'pages', 2.443), thE: _we(ctx, id, 'thousand', 1.003), hunE: _we(ctx, id, 'hundred', 1.803), twE: _we(ctx, id, 'twelve', 2.443) };
}
export function C5_pagestack(ctx) {
  const t = ctx.t, dur = ctx.dur, K = _c5Times(ctx);
  const t0 = 0.04, tHit = K.pg;
  // counter value (follows the number words) and tower height fraction (accelerates into the ceiling on "pages")
  const V = track([[0, 1], [K.four - 0.02, 1], [K.thE - 0.05, 4000, 'inOutSine'], [K.eight, 4000], [K.hunE - 0.05, 4800, 'inOutSine'], [K.tw, 4800], [K.twE - 0.04, 4812, 'outCubic']]);
  const Hf = track([[t0, 0], [K.thE, 0.45, 'outCubic'], [K.hunE, 0.74, 'inOutSine'], [tHit, 1, 'inQuad']]);
  const hfAt = (tt) => (tt >= tHit ? 1 : Hf(tt));
  const v = V(t), hf = hfAt(t);
  const after = t - tHit, comp = after >= 0 ? 18 * Math.exp(-after / 0.11) * Math.abs(Math.sin(TAU * 4.2 * after)) : 0;
  const n = Math.max(1, 4812 * hf), top = STK.base - n * STK.th + comp;
  // --- sound
  _sfx(ctx, 'whoosh_short', 0, t0 + 0.02, { db: -2, note: 'cut: the first sheets burst out of the phone' });
  _sfx(ctx, 'page_riffle', 0, t0, { dur: K.thE - t0, note: 'synth: pages pouring (accelerating riffle)' });
  _sfx(ctx, 'whoosh_short', 1, K.th + 0.05, { db: -4, note: "paper whoosh on 'thousand'" });
  _sfx(ctx, 'page_riffle', 0, K.eight, { dur: K.hunE - K.eight, note: 'synth: second pour' });
  _sfx(ctx, 'whoosh_short', 2, K.hun + 0.05, { db: -4, note: "paper whoosh on 'hundred'" });
  _sfx(ctx, 'whoosh_short', 3, K.tw + 0.05, { db: -4, note: "paper whoosh on 'twelve'" });
  _sfx(ctx, 'slide_whistle_up', 1, tHit - 1.43 + 0.05, { db: -3, note: 'the tower rises; clip end lands on the ceiling hit' });
  _sfx(ctx, 'cartoon_pop', 2, K.four, { db: -6, note: 'page counter pops' });
  _sfx(ctx, 'counter_tick', 0, K.thE - 0.05, { note: 'synth: odometer lands on 4,000' });
  _sfx(ctx, 'counter_tick', 0, K.hunE - 0.05, { note: 'synth: odometer lands on 4,800' });
  _sfx(ctx, 'counter_tick', 0, K.twE - 0.04, { note: 'synth: odometer lands on 4,812' });
  _sfx(ctx, 'bonk', 3, tHit, { note: "THUNK: the tower hits the ceiling on 'pages'" });
  _sfx(ctx, 'impact_hit', 2, tHit, { db: -6, dur: 1.2, note: 'ceiling impact weight' });
  // --- camera: start on Sam + the phone, tilt up with the tower top, settle wide on the ceiling hit (Sam's face stays
  // above the 'mid' caption band, left of centre)
  const cam = ctx.cam({
    keys: [[0, { x: 220, y: 24, z: 1.0 }], [K.thE + 0.1, { x: 210, y: -50, z: 0.93 }, 'inOutSine'], [K.hunE + 0.15, { x: 180, y: -120, z: 0.82 }, 'inOutSine'],
      [tHit + 0.06, { x: 150, y: -165, z: 0.725 }, 'inOutSine'], [dur, { x: 146, y: -168, z: 0.735 }, 'inOutSine']],
    drift: 4, shake: [{ t: tHit, amp: 18, decay: 0.09 }],
  });
  // --- Sam: eyes ride up with the tower, leans back
  const bs = posePreset('bedSit', 'sam');
  const sam = _sam(ctx, {
    face: [[0, { preset: 'surprised', look: [1, 3] }], [K.th, 'shocked'], [K.hun, 'scared'], [tHit, 'shocked', 1.4], [tHit + 0.3, 'scared']],
    lookAt: (tt) => (tt < K.four ? [PHONE_W[0] + 100, PHONE_W[1] + 40] : [STK.cx, Math.min(STK.base - 160, STK.base - 4812 * hfAt(tt) * STK.th)]), lookAmp: 5,
    pose: [[0, bs], [K.th, { ...bs, lean: -6, head: -5 }], [K.hun, { ...bs, lean: -9, head: -9 }], [tHit, { ...bs, lean: -12, head: -12, shrug: 0.6 }, 'outBack', 5 * FR]],
    add: [[0, {}], [K.hun, { sweat: 1, sweatK: 0.4 }], [tHit, { sweat: 2, sweatK: 0.8 }]],
    nervous: [[0, 0], [K.hun, 0.4], [tHit, 0.8]], squash: [[tHit, 0.06]], facing: [[0, 0], [K.th, 10]],
    light: _flicker([t0, K.eight, K.tw]),
  });
  // --- the tower + sheets in flight (world, depth .75), on the floor in front of the wall
  const tower = _tower(n, top, 0.25 + 0.5 * seg(t, K.hun, tHit), ctx.gt);
  let fly = '';
  const rate = 26, life = 0.32;
  for (let i = 0; ; i++) {
    const ti = t0 + i / rate;
    if (ti > tHit - life - 0.02 || ti > t) break;        // every sheet lands before the ceiling hit
    const u = (t - ti) / life;
    if (u >= 1) continue;
    const yTop = STK.base - 4812 * hfAt(ti + life) * STK.th;
    const x0 = PHONE_W[0] + (rand(5, i, 1) - 0.5) * 40, y0 = PHONE_W[1];
    const x1 = STK.cx + (rand(5, i, 2) - 0.5) * 120, y1 = yTop - 10;
    const e = ease.outQuad(u), arc = 120 + 0.3 * Math.max(0, y0 - y1);
    const x = lerp(x0, x1, e), y = lerp(y0, y1, e) - arc * 4 * u * (1 - u);
    fly += g(_sheet(0, 0, lerp(0.3, 0.42, u), i), { transform: `translate(${r2(x)} ${r2(y)}) rotate(${r2((rand(5, i, 3) - 0.5) * 80 + u * 260 * (i % 2 ? 1 : -1))}) scale(1 ${r3(0.6 + 0.4 * Math.abs(Math.cos(u * 5 + i)))})` });
  }
  fly = _nightPaper(fly, 'fl');
  // --- ceiling hit: crack lines on the ceiling above the tower, plaster dust puffing out and drifting down
  let hit = '';
  if (after >= 0) {
    const k = seg(after, 0, 0.12), cy = BEDROOM.ceilY - 12;
    const cr = [[[0, 0], [-60, -24], [-110, -18], [-170, -46]], [[0, 0], [50, -30], [96, -26], [150, -58]], [[0, 0], [-14, -40], [10, -84]], [[0, 0], [30, 14], [80, 6]]];
    for (const P of cr) {
      const dd = P.map((q, j) => (j ? 'L' : 'M') + r2(STK.cx + q[0] * k) + ' ' + r2(cy + q[1] * k)).join('');
      hit += path(dd, { fill: 'none', ...st('#1E1844', 7), opacity: 0.8 }) + path(dd, { fill: 'none', ...st('#8E84C8', 2.5), opacity: 0.8, transform: 'translate(2 -2)' });
    }
    for (let i = 0; i < 16; i++) {
      const sx = rand(9, i, 3) < 0.5 ? -1 : 1, sp = 90 + 230 * rand(9, i, 2), u = after;
      const px = STK.cx + sx * (STK.w * 0.35 + sp * (1 - Math.exp(-u / 0.22))), py = cy + 14 + 30 * (1 - Math.exp(-u / 0.2)) + 150 * u * u + 30 * rand(9, i, 5);
      const r = (12 + 18 * rand(9, i, 4)) * (0.6 + 0.8 * seg(u, 0, 0.3)), op = 0.7 * (1 - seg(u, 0.25, 0.95));
      if (op > 0.02) hit += circle(px, py, r, { fill: rand(9, i, 6) < 0.5 ? '#B9B0E0' : '#9E94D2', opacity: O(op) });
    }
  }
  let s = _bedWorld(ctx, cam, { sam, insert: [{ after: 'blanket', depth: 0.75, svg: tower + fly }, { after: 'near', depth: 0.75, svg: hit }] });
  // --- the page counter (screen, top left): pops on "Four", rolls with the words, bumps on "pages"
  if (t >= K.four - 2 * FR) {
    const p = seg(t, K.four - 2 * FR, K.four + 7 * FR), b = _bump(t, tHit, 0.14, 0.09), sc = 0.66 * b;
    const sp = Math.abs(V(t + 1 / 120) - V(t - 1 / 120)) * 60;
    const cs = U2.counter({ x: 0, y: 0, value: v, digits: 4, label: '{Pages|orange} to read:', speed: sp }, p);
    s += cam.screen(g(cs, { transform: `translate(56 44) scale(${r3(sc)})` }), { shake: true });
  }
  return s;
}

// =====================================================================================================================
// C6 — "So you read every word..." Close-up: Sam holds the phone close and squints at page one, his eyes scanning the
// lines (saccades left to right, snapping back); a "Page 1 of 4,812" pill pops on "read"; punch-in 1.08 and a
// determined face on "every"; on "word" he squints harder (sweat). The tower looms out of focus behind him.
// =====================================================================================================================
export function C6_squint(ctx) {
  const t = ctx.t, dur = ctx.dur, id = 'S00-L014';
  const tRead = _w(ctx, id, 'read', 0.593), tEvery = _w(ctx, id, 'every', 0.993), tWord = _w(ctx, id, 'word', 1.473);
  _sfx(ctx, 'page_flip', 0, 0.02, { db: -4, note: 'synth: cut: he flips to page one' });
  _sfx(ctx, 'cartoon_pop', 2, tRead + 2 * FR, { db: -8, note: "'Page 1 of 4,812' pill pops" });
  _sfx(ctx, 'whoosh_short', 6, tEvery, { db: -10, note: "punch-in on 'every'" });
  _sfx(ctx, 'ui_select', 0, tWord + 2 * FR, { db: -10, note: "the pill bumps on 'word' (still page 1)" });
  const F = frameOn([830, 520], 2.2, [820, 460]);
  const headS = [820, 380];
  const cam = ctx.cam({ keys: [[0, F], [dur, { ...F, x: F.x + 6, z: F.z * 1.035 }, 'inOutSine']], drift: 3, punch: [{ t: tEvery - FR, k: 1.08, at: headS, settle: 0.25, keep: 0.04 }] });
  // reading saccades: 3 steps right per line (0.1 s each), snap back left; a line every ~0.38 s
  const scan = (tt) => { const ln = 0.38, ph = ((tt + 0.05) % ln) / ln, k = Math.min(3, Math.floor(ph * 4)); return -3.6 + k * 2.4; };
  const up = posePreset('phoneUp', 'sam'), close = { ...up, armR: up.armR - 6, foreR: up.foreR - 8 };
  const sam = _sam(ctx, {
    face: [[0, { preset: 'squint' }], [tEvery, { preset: 'determined' }], [tWord, { preset: 'squint', add: { sweat: 1, sweatK: 0.5 } }]],
    look: (tt) => [scan(tt), 3.2], blink: { seed: 23 },
    pose: [[0, up], [tEvery - 2 * FR, close, 'outBack', 6 * FR]],
    // the head follows the eyes along each line (a small yaw sweep, snapping back at the line break)
    facing: (tt) => (tt < tEvery ? 6 : 1) + 1.4 * scan(tt), nervous: [[0, 0], [tWord, 0.3]], light: _flicker([0.02, tWord]),
  });
  // the tower behind him, out of focus
  const tower = _tower(4812, STK.top, 0.2, ctx.gt);
  let s = _bedClose(ctx, cam, sam, { blur: 6, back: [{ after: 'mid', depth: 0.75, svg: tower }] });
  // "Page 1 of 4,812" pill beside the phone (screen)
  if (t >= tRead) {
    const p = seg(t, tRead, tRead + 8 * FR), b = _bump(t, tWord, 0.16, 0.08);
    const d = new Defs(), w = 330, h = 78, x = 1130, y = 610;
    let pill = path(rrPath(x, y + 6, w, h, 39), { fill: '#070A1C', opacity: 0.6 }) + path(rrPath(x, y, w, h, 39), { fill: d.lin([U.UI.navy2, U.UI.navy1]), stroke: '#070A1C', strokeWidth: 3.5 });
    pill += text(x + w / 2, y + 52, U.rich('Page {1|white} of {4,812|orange}'), NUN(34, 900, U.UI.sub, { textAnchor: 'middle' }));
    pill = popIn(String(d) + pill, x + w / 2, y + h / 2, p, { bbox: { x, y, w, h, r: 39 }, ringGrow: 30 });
    s += cam.screen(g(pill, { transform: `translate(${x + w / 2} ${y + h / 2}) scale(${r3(b)}) translate(${-(x + w / 2)} ${-(y + h / 2)})` }));
  }
  return s;
}

// =====================================================================================================================
// C7 — "...in half a second." The terms page, full frame. One flick: the sheets riffle up and away in a blur, the page
// number racing; page 4,812 lands and holds, crisp and readable, for exactly 3 frames (tiny ding); then it flies off too,
// revealing "All 4,812 pages read · Reading time: 0.5 s" (check pops).
// =====================================================================================================================
const PAGE = { x: 560, y: 60, w: 800, h: 866 };
/** a generic fine-print page (page n): header, grey line bars, footer "Page n of 4,812"; x, y = top-left */
function _page(n, o = {}) {
  const { x = PAGE.x, y = PAGE.y, w = PAGE.w, h = PAGE.h } = o, d = new Defs(), R = (i, j) => rand(1000 + n, i, j);
  let s = '';
  if (o.under !== false) for (let i = 2; i >= 1; i--) s += path(rrPath(x + i * 7, y + i * 7, w, h, 20), { fill: shade('#E6EBF7', -0.04 * i), stroke: '#9AA6CC', strokeWidth: 2.5 });
  s += path(rrPath(x, y, w, h, 20), { fill: d.lin(['#FFFFFF', '#EEF2FB']), stroke: '#9AA6CC', strokeWidth: 3 });
  const pad = 46;
  s += text(x + pad, y + 70, n === 1 ? 'SECTION 1.1.1 — DEFINITIONS' : `SECTION ${Math.max(1, Math.ceil(n / 4)).toLocaleString('en-US')}.${(n % 9) + 1} — MORE RULES`, NUN(30, 900, '#3A4470', { letterSpacing: 0.5 }));
  s += path(rrPath(x + pad, y + 88, w - pad * 2, 3, 1.5), { fill: '#C3CBE3' });
  let ly = y + 118, i = 0;
  while (ly < y + h - 96) {
    if (R(i, 1) < 0.13) { ly += 20; i++; continue; }
    s += path(rrPath(x + pad, ly, (w - pad * 2) * (0.55 + 0.45 * R(i, 2)), 12, 6), { fill: '#B4BCD8' });
    ly += 30; i++;
  }
  s += text(x + w / 2, y + h - 36, U.rich(`Page {${n.toLocaleString('en-US')}|navy} of {4,812|navy}`, { navy: '#3A4470' }), NUN(28, 800, '#7A84AA', { textAnchor: 'middle' }));
  return String(d) + s;
}
export function C7_flick(ctx) {
  const t = ctx.t, dur = ctx.dur, id = 'S00-L015', lf = _lf(ctx);
  const tHalf = _w(ctx, id, 'half', 0.397), tSec = _w(ctx, id, 'second', 0.957);
  const fHold = Math.round(tSec * FPS) + 1, tF0 = tHalf - 0.03, tF1 = fHold / FPS, tOn = (fHold + 3) / FPS;   // hold = frames fHold..fHold+2
  const hold = lf >= fHold && lf <= fHold + 2;
  _sfx(ctx, 'page_flip', 0, 0.02, { db: -6, note: 'synth: cut on page one' });
  _sfx(ctx, 'swish', 0, tF0 + 2 * FR, { note: 'the flick' });
  _sfx(ctx, 'page_riffle', 0, tF0, { dur: tF1 - tF0, note: 'synth: 4,812 pages riffle past in half a second (accelerating then braking)' });
  _sfx(ctx, 'whoosh_short', 3, tF0 + 0.2, { db: -6, note: 'riffle whoosh' });
  _sfx(ctx, 'notif_ping', 3, tF1, { db: -8, note: 'a tiny ding on the 3 readable frames of page 4,812' });
  _sfx(ctx, 'swish', 2, tOn + 2 * FR, { db: -2, note: 'page 4,812 flies off' });
  _sfx(ctx, 'toggle', 4, tOn + 0.16, { db: -4, note: 'the check pops: all pages read' });
  _sfx(ctx, 'success_chime', 5, tOn + 0.2, { db: -8, note: 'smug little success' });
  // camera: locked (drift 0) so the hold is truly still; kick on the flick, settle exactly on the hold, push after
  const cam = ctx.cam({
    keys: [[0, { x: 0, y: 0, z: 1.0 }], [tF0, { y: 0, z: 1.02 }], [tF0 + 0.1, { y: -26, z: 1.05 }, 'outCubic'], [tF1, { y: 0, z: 1.06 }, 'inOutSine'],
      [tOn, { y: 0, z: 1.06 }], [tOn + 0.14, { y: 14, z: 1.03 }, 'outCubic'], [dur, { y: 4, z: 1.06 }, 'inOutSine']],
    drift: 0,
  });
  let s = U2.appBg(1920, 1080, { rot: ctx.gt * 4 });
  s = `<g transform="translate(-90 -60) scale(1.1)">${s}</g>`;
  if (t < tF0) {
    s += cam.layer(_page(1), 1);
  } else if (t < tF1 || hold) {
    if (hold) {
      s += cam.layer(U.termsPage({ ...PAGE, page: '4,812', of: '4,812', highlight: 1 }) + _pageUnder(), 1);
      s += cam.layer(sparkle(PAGE.x + PAGE.w - 70, PAGE.y + 470, 22, '#FFFFFF', 0.9, 15), 1);
    } else {
      // the riffle: the page number races (ease in-out), a new sheet leaves every frame, the leaving sheets blur upward
      const u = seg(t, tF0, tF1), pn = Math.max(2, Math.min(4811, Math.round(1 + 4811 * ease.inOutCubic(u))));
      const sp = Math.sin(Math.PI * u);
      let under = _page(pn + 1, { under: true });
      let fly = '';
      for (let j = 0; j < 4; j++) {
        const age = ((t - tF0) * FPS + j) % 4 / 4, yy = -1300 * ease.inQuad(age), rot = -10 * age;
        fly += g(_page(Math.max(1, pn - j), { under: false }), { transform: `translate(${r2(PAGE.x + PAGE.w / 2)} ${r2(PAGE.y + PAGE.h / 2 + yy)}) rotate(${r2(rot)}) translate(${-(PAGE.x + PAGE.w / 2)} ${-(PAGE.y + PAGE.h / 2)})`, opacity: O(1 - age * 0.5) });
      }
      s += cam.layer(under, 1);
      s += boxBlur(cam.layer(fly, 1), { x: 0, y: -40, w: 1920, h: 1160, sdx: 0, sdy: 8 + 34 * sp });
      s += scrollStreaks({ x: PAGE.x - 40, y: 0, w: PAGE.w + 80, h: 1080, speed: 10 + 50 * sp, seed: 41, t, color: '#FFFFFF', count: 16 });
      // the thumb's flick: a bright swipe arc up the right side of the page for the first 8 frames
      const fk = seg(t, tF0, tF0 + 8 * FR);
      if (fk < 1) {
        const a0 = Math.max(0, fk - 0.45), a1 = fk, P = (u) => [lerp(1420, 1300, u) + 90 * Math.sin(Math.PI * u), lerp(940, 120, u)];
        let dd = '';
        for (let i = 0; i <= 10; i++) { const q = P(lerp(a0, a1, i / 10)); dd += (i ? 'L' : 'M') + r2(q[0]) + ' ' + r2(q[1]); }
        s += path(dd, { fill: 'none', ...st('#FFFFFF', 26 * (1 - fk) + 6), opacity: O(0.85 * (1 - fk * 0.6)) });
      }
    }
  } else {
    // "then on": page 4,812 flies off up-left (moving from the first frame after the hold), the end card pops
    const u = seg(t, tOn - FR, tOn + 7 * FR);
    if (u < 1) {
      const e = ease.inQuad(u);
      s += cam.layer(g(U.termsPage({ ...PAGE, page: '4,812', of: '4,812', highlight: 1 }), { transform: `translate(${r2(-900 * e)} ${r2(-1100 * e)}) rotate(${r2(-24 * e)} 960 500)` }), 1);
    }
    s += cam.layer(_doneCard(t - tOn - 0.1, ctx.gt), 1);
  }
  return s;
}
function _pageUnder() { return ''; }
/** "All 4,812 pages read" end card (frame space, centred), lt = seconds since it starts popping */
function _doneCard(lt, gt) {
  if (lt < 0) return '';
  const d = new Defs(), w = 900, h = 300, x = 960 - w / 2, y = 330;
  let s = U.glassCard(d, x, y, w, h, 56);
  const ck = seg(lt, 0.06, 0.06 + 7 * FR), ckS = ck < 1 ? ease.outBack(ck) : _bump(lt, 0.06 + 7 * FR, 0.1, 0.08);
  s += g(circle(0, 0, 70, { fill: d.lin(['#6BF29A', U.UI.green, shade(U.UI.green, -0.12)]), stroke: ink(U.UI.green), strokeWidth: 5 }) + g(glyph('check', '#FFFFFF'), { transform: 'scale(1.2)' }), { transform: `translate(${x + 140} ${y + h / 2}) scale(${r3(Math.max(0, ckS))})` });
  s += text(x + 250, y + 132, 'All {4,812|orange} pages read'.replace(/\{([^|}]+)\|orange\}/, `<tspan fill="${U.UI.orange}">$1</tspan>`), LIL(64, '#FFFFFF', { letterSpacing: 1 }));
  s += text(x + 252, y + 200, U.rich('Reading time: {0.5 seconds|orange}'), NUN(38, 900, U.UI.sub));
  // twinkles round the edge (never over the text)
  [[x + 30, y - 18, 26], [x + w - 60, y - 26, 20], [x + w + 18, y + 70, 18], [x - 22, y + h - 40, 22], [x + w * 0.55, y + h + 22, 18], [x + 70, y + h + 18, 14]].forEach(([sx, sy, r], i) => {
    const k = 0.4 + 0.6 * Math.max(0, Math.sin(TAU * 1.3 * gt + i * 1.7));
    s += sparkle(sx, sy, r * k, i % 2 ? '#FFF4B0' : '#FFFFFF', 0.5 + 0.5 * k, gt * 40);
  });
  return popIn(String(d) + s, 960, y + h / 2, seg(lt, 0, 9 * FR), { bbox: { x, y, w, h, r: 56 }, ringGrow: 50 });
}

// =====================================================================================================================
// C8 — "...and press I AGREE." POV: the last page and the big green I AGREE fill the phone; the push creeps toward the
// button; the thumb slides over on "press", lifts (anticipation) on "I" and presses on "AGREE" (PRESS). The music has
// dropped out 0.25 s before (designed silence): only the voice and the tap.
// =====================================================================================================================
const C8_PHONE = { x: 990, y: 548, s: 0.64, rot: -3 };
const BTN = { cx: 360, cy: 905, w: 640, h: 200 };
export function C8_agree(ctx) {
  const t = ctx.t, dur = ctx.dur, id = 'S00-L016';
  const tPress = _w(ctx, id, 'press', 0.463), tI = _w(ctx, id, 'I', 0.943), tAg = _w(ctx, id, 'AGREE', 1.103);
  _sfx(ctx, 'cartoon_pop', 0, 0.03 + 3 * FR, { db: -6, note: 'cut: the I AGREE button pops onto the page' });
  _sfx(ctx, 'swish', 1, tPress + 0.08, { db: -14, note: "thumb slides in under the button on 'press'" });
  _sfx(ctx, 'ui_tap', 2, tAg, { note: "PRESS: big tap on 'AGREE'" });
  _sfx(ctx, 'ui_confirm', 0, tAg + FR, { db: -4, note: 'the button confirms (sub boom follows on the C9 cut)' });
  const P = C8_PHONE, bF = U2.phonePoint(P, BTN.cx, BTN.cy), pressPt = [604, BTN.cy + 12];
  const kF = (k) => ({ x: (bF[0] - 960) * k, y: (bF[1] - 540) * k });
  const shake = [{ t: tAg, amp: 6, decay: 0.06 }];
  const cam = ctx.cam({ keys: [[0, { ...kF(0), z: 1.0 }], [tAg, { ...kF(0.5), z: 1.06 }, 'inOutSine'], [dur, { ...kF(0.6), z: 1.075 }, 'outCubic']], drift: 0, shake });
  const camB = ctx.cam({ keys: [[0, { x: 320, y: -10, z: 1.12 }], [dur, { x: 326, y: -14, z: 1.14 }, 'inOutSine']], drift: 4, shake });
  // thumb: resting low right -> slides in under the button's right end on "press" -> lifts on "I" -> presses on "AGREE"
  // (it lands right of the label, so I AGREE stays readable up to the press)
  const tx = track([[0, 680], [tPress, 680], [tPress + 0.3, 650, 'inOutCubic'], [tI, 646], [tI + 0.1, 626, 'outCubic'], [tAg, pressPt[0], 'inCubic']]);
  const ty = track([[0, 1320], [tPress, 1320], [tPress + 0.3, 1100, 'inOutCubic'], [tI - 0.04, 1096], [tI + 0.1, 1040, 'outCubic'], [tAg - 3 * FR, 960, 'inCubic'], [tAg, pressPt[1]]]);
  const press = seg(t, tAg - 2 * FR, tAg + FR);
  const bend = t < tI ? 1 : lerp(1, 1.25, seg(t, tI, tI + 0.1)) * (1 - 0.25 * press);
  const pBtn = seg(t, 0.03, 0.03 + 9 * FR);
  const d = new Defs();
  let content = U.termsPage({ x: 40, y: 250, w: 640, h: 400, page: '4,812', of: '4,812', highlight: 1 });
  content += text(52, 706, U.rich('Page {4,812|white} of {4,812|orange}'), NUN(34, 900, U.UI.sub));
  content += String(d) + path(rrPath(52, 728, 46, 46, 12), { fill: d.lin([U.UI.navy3, U.UI.navy2]), stroke: U.UI.rimHi, strokeWidth: 3 }) + g(glyph('check', U.UI.green), { transform: 'translate(75 751) scale(0.4)' });
  content += text(112, 764, 'I have read all of it', NUN(32, 800, '#FFFFFF'));
  content += U2.agreeButton({ ...BTN, press, ripple: t > tAg ? seg(t, tAg, tAg + 0.5) : 0, glow: 0.7 + 0.3 * seg(t, tI, tAg), t: ctx.gt, R: 900 }, pBtn);
  content += text(360, 1068, 'By pressing, you agree to everything. Forever.', NUN(22, 800, U.UI.dim, { textAnchor: 'middle' }));
  const scr = U2.appScreen({ time: '2:13', crumb: 'Settings › {Terms|purple}', content });
  const ph = U2.phone({ ...P, screen: scr, glow: 0.9 + 0.3 * press, thumb: { x: tx(t), y: ty(t), press, bend }, handShift: [0, 140], t });
  let s = _povBack(ctx, camB);
  s += cam.layer(_knees(-40, 40), 1);
  s += cam.layer(ph, 1);
  if (t >= tAg) {
    const pp = U2.phonePoint(P, pressPt[0], pressPt[1]), u = seg(t, tAg, tAg + 0.2);
    s += cam.layer(shockRing(pp[0], pp[1], lerp(50, 380, ease.outCubic(u)), u, '#C8FFD9', 16), 1);
  }
  return s;
}

// =====================================================================================================================
// C9 — The ripple. The sub boom (flash in): a white ring and a cyan grid wave leave the phone and sweep the bedroom
// (Sam jolts: shocked take); snap zoom-out: we land outside on the house front at night, the ring blasting out of Sam's
// window across the lawn; snap zoom-out to the street wide: the ring crosses the whole street, the windows flicker on
// in three waves on the music's boot-up boops, the street lamp surges, a distant dog barks.
// =====================================================================================================================
/** cyan grid lines inside the ring band [r - bw, r] around (cx, cy), fading inward; squash flattens the whole band
 *  (and its grid) vertically into a floor-like ellipse */
function _gridBand(cx, cy, r, bw, o = {}) {
  if (r <= 4) return '';
  const d = new Defs(), sq = o.squash ?? 1, step = o.step ?? 90, col = o.color || '#8FF8FF';
  const r0 = Math.max(1, r - bw);
  const el = (R) => `M${r2(cx - R)} ${r2(cy)}a${r2(R)} ${r2(R)} 0 1 0 ${r2(2 * R)} 0a${r2(R)} ${r2(R)} 0 1 0 ${r2(-2 * R)} 0Z`;
  const clip = d.clip(path(el(r) + el(r0), { clipRule: 'evenodd' }));
  let ln = '';
  const x0 = Math.floor((cx - r) / step) * step, x1 = cx + r, y0 = Math.floor((cy - r) / step) * step, y1 = cy + r;
  for (let x = x0; x <= x1; x += step) ln += `M${x} ${r2(y0)}V${r2(y1)}`;
  for (let y = y0; y <= y1; y += step) ln += `M${r2(x0)} ${y}H${r2(x1)}`;
  const fade = d.rad([[0, col, 0], [Math.max(0, 1 - bw / r), col, 0], [1, col, 1]], cx, cy, r, 'userSpaceOnUse');
  const body = g(path(ln, { fill: 'none', stroke: fade, strokeWidth: o.w ?? 4, opacity: O(o.op ?? 0.8) }), { clipPath: clip });
  return String(d) + (sq === 1 ? body : g(body, { transform: `translate(0 ${r2(cy)}) scale(1 ${r3(sq)}) translate(0 ${r2(-cy)})` }));
}
/** expanding shock rings from c (world): rings [{t0, R, life, ez}] -> {ring, band} (soft fill, cyan band, white edge;
 *  string opacities so the fades are smooth) */
function _ringWave(c, t, rings, sq, o = {}) {
  let ring = '', band = '';
  for (const { t0, R, life, ez = ease.outCubic } of rings) {
    const q = seg(t, t0, t0 + life);
    if (q <= 0 || q >= 1) continue;
    const e = ez(q), r = R * e, a = 1 - q, bw = lerp(o.bw0 ?? 160, o.bw1 ?? 40, e);
    ring += ellipse(c[0], c[1], r, r * sq, { fill: '#BFF7FF', opacity: O(a * 0.1) });
    ring += ellipse(c[0], c[1], Math.max(0, r - bw * 0.5), Math.max(0, (r - bw * 0.5) * sq), { fill: 'none', stroke: '#BFF7FF', strokeWidth: r2(bw), opacity: O(a * 0.3) });
    ring += ellipse(c[0], c[1], r, r * sq, { fill: 'none', stroke: '#FFFFFF', strokeWidth: r2(lerp(o.w0 ?? 16, o.w1 ?? 5, e)), opacity: O(Math.min(1, a * 1.3)) });
    band += _gridBand(c[0], c[1], r, o.band ?? 300, { squash: sq, step: o.step ?? 70, op: 0.85 * a, w: 4 });
  }
  return { ring, band };
}
// windows of the night street (world rects at depth .75): three groups that flicker on with the boot-up boops
// (left to right with the ring: Sam's second window + attic, the blue house, Kevin's)
const WIN = [
  [[236, 494, 76, 96], [234, 336, 60, 60, 30]],
  [[670, 518, 90, 90], [770, 518, 70, 90]],
  [[1160, 428, 170, 92], [1380, 428, 210, 92]],
];
function _windowsLit(k3) {
  const d = new Defs();
  let s = '';
  WIN.forEach((grp, gi) => {
    const k = k3[gi];
    if (k <= 0.01) return;
    for (const [x, y, w, h, rr = 5] of grp) {
      s += circle(x + w / 2, y + h / 2, Math.max(w, h) * 1.1, { fill: d.rad([[0, '#FFD98A', 0.55], [1, '#FFD98A', 0]]), opacity: O(k) });
      s += path(rrPath(x, y, w, h, rr), { fill: d.lin(['#FFF4CC', '#FFC96A']), opacity: O(k) });
      s += rect(x + w / 2 - 3, y, 6, h, { fill: '#C9B8E8', opacity: O(k * 0.8) }) + rect(x, y + h / 2 - 3, w, 6, { fill: '#C9B8E8', opacity: O(k * 0.8) });
    }
  });
  return String(d) + s;
}
export function C9_ripple(ctx) {
  const t = ctx.t, dur = ctx.dur, gt = ctx.gt;
  // stage times: A bedroom [0, tA), snap out; B house [tB, tC), snap out; C street [tC, dur]
  const tA = 0.42, tB = tA + 7 * FR, tC = 1.0, zIn = 8 * FR;
  // the music plan's boot-up boops (Gotta Catch src 1.595 / 1.795 / 1.995, entry src 1.56 at local 1.068)
  const gotta = (ctx.T.music || []).find((m) => m.id === 'gotta');
  const b0 = gotta ? gotta.at - ctx.start + (1.595 - gotta.src[0]) : 1.103;
  const boops = [b0, b0 + 0.2, b0 + 0.4];
  _sfx(ctx, 'sub_boom', 0, 0, { dur: 3.0, note: 'cut (flash): THE sub boom of the I AGREE press' });
  _sfx(ctx, 'bass_drop', 1, 0, { db: -3, note: 'bass dive under the boom' });
  _sfx(ctx, 'impact_hit', 0, 0, { db: -8, dur: 1.0, note: 'transient layer on the flash frame' });
  _sfx(ctx, 'whoosh_long', 0, 0.16, { db: -2, note: 'shockwave: the ring leaves the phone' });
  _sfx(ctx, 'glitch', 2, 0.1, { db: -10, dur: 0.4, note: 'the grid wave crackles through the room' });
  _sfx(ctx, 'whoosh_short', 4, tA + 4 * FR, { note: 'snap zoom-out 1 (room -> house)' });
  _sfx(ctx, 'boing', 3, tB + 0.08, { db: -8, note: 'the house jolts as the ring blasts out of the window' });
  _sfx(ctx, 'whoosh_short', 5, tC + 4 * FR, { note: 'snap zoom-out 2 (house -> street)' });
  _sfx(ctx, 'dog_woof', 0, b0 + 0.28, { db: -10, size: 'small', distant: true, note: 'synth: a distant dog barks as the ring passes Kevin\'s' });
  _sfx(ctx, 'power_down', 0, tC + 0.24, { db: -14, note: 'street lamp surges (tiny buzz)' });
  let s = '';
  if (t < tB) {
    // --- A: the bedroom. The ring leaves the phone; the camera snaps out from tA
    const cam = ctx.cam({ keys: [[0, { x: 0, y: 10, z: 1.0 }], [tA, { x: 0, y: 0, z: 1.03 }], [tB, { x: 0, y: -30, z: 0.72 }, 'inExpo']], drift: 0,
      shake: [{ t: 0, amp: 26, decay: 0.1 }, { t: 0.12, amp: 10, decay: 0.08 }] });
    const sam = _sam(ctx, { face: [[0, 'shocked'], [2 * FR, { preset: 'shocked', mouth: 'v_O' }], [0.22, 'scared']], squash: [[0, 0.1]], nervous: 0.8,
      pose: [[0, posePreset('bedSit', 'sam')], [FR, { ...posePreset('bedSit', 'sam'), lean: -10, head: -8, shrug: 0.8 }, 'outBack', 5 * FR]], light: _plight(1) });
    const c = PHONE_W;
    const W1 = _ringWave(c, t, [{ t0: -0.02, R: 2300, life: 0.62 }, { t0: 0.1, R: 2300, life: 0.62 }, { t0: 0.22, R: 2300, life: 0.62 }], 0.85, { band: 260, step: 80 });
    s += _bedWorld(ctx, cam, { sam, insert: [{ after: 'mid', depth: 0.75, svg: W1.band }, { after: 'near', depth: 0.75, svg: W1.ring }] });
    // white-hot core on the phone in the first frames
    const cp = cam.toScreen(c, 0.75), ck = 1 - seg(t, 0, 0.25);
    if (ck > 0) { const d = new Defs(); s += String(d) + circle(cp[0], cp[1], 260 * cam.state.z, { fill: d.rad([[0, '#FFFFFF', 0.95 * ck], [0.4, '#BFF7FF', 0.5 * ck], [1, '#BFF7FF', 0]]) }); }
    return s;
  }
  // --- B and C: the night street (one camera: snap out from the window to the house, later to the street wide)
  // the street framing lands between the wide and C10's opening framing (hook_d C10_F0 {x -330, y -46, z 1.12}) and
  // eases into it by the cut, so C9 -> C10 reads as one continuous move
  const SW = STREET.samWindow, Fw = frameOn([SW.cx, SW.cy], 5.0), Fh = { x: -660, y: -30, z: 1.75 }, Fs = { x: -250, y: -44, z: 1.04 }, F10 = { x: -330, y: -46, z: 1.12 };
  const cam = ctx.cam({
    keys: [[tB, Fw], [tB + zIn, Fh, 'outExpo'], [tC, { ...Fh, x: Fh.x + 6, z: Fh.z * 1.02 }, 'inOutSine'], [tC + zIn, Fs, 'outExpo'], [dur, F10, 'inOutSine']],
    drift: 0, shake: [{ t: tB + 0.06, amp: 16, decay: 0.09 }, { t: tC + zIn, amp: 9, decay: 0.08 }],
  });
  // three rings leave Sam's window: one as we land on the house, one through it, one as we snap out to the street
  const c = [SW.cx, SW.cy], SQ = 0.5;
  const rings = [tB - 0.04, tB + 0.2, tC - 0.02].map((t0, i) => ({ t0, R: [900, 1400, 2600][i], life: [0.6, 0.8, 1.0][i], ez: i === 2 ? ease.outQuad : ease.outCubic }));
  const W2 = _ringWave(c, t, rings, SQ), ringSvg = W2.ring, band = W2.band;
  // window flicker (power surge): each group flicks on (3 frames on, 2 dim, on) at its boop, then fades back to the
  // night before the cut
  const k3 = boops.map((b) => {
    const u = t - b;
    if (u < 0) return 0;
    const fl = u < 3 * FR ? 1 : u < 5 * FR ? 0.25 : 1;
    return fl * (1 - seg(u, 0.1, 0.24));
  });
  // Sam's own window: blasts white as the first ring leaves it, then settles back to its warm light
  const wk = 1 - seg(t, tB, tB + 0.35);
  const d = new Defs();
  const sw = wk > 0 ? circle(SW.cx, SW.cy, 140, { fill: d.rad([[0, '#FFFFFF', 0.95 * wk], [0.5, '#BFF7FF', 0.6 * wk], [1, '#BFF7FF', 0]]) }) + path(rrPath(SW.x, SW.y, SW.w, SW.h, 5), { fill: '#FFFFFF', opacity: O(wk) }) : '';
  // the street lamp surges once when the last ring passes it
  const lk = t > tC + 0.2 ? 1 - seg(t, tC + 0.2, tC + 0.5) : 0;
  const lamp = lk > 0 ? circle(STREET.lamp.x, STREET.lamp.y + 8, 170, { fill: d.rad([[0, '#FFFBE0', 0.85 * lk], [1, '#FFF0B8', 0]]) }) : '';
  s += cam.set(_street(ctx), { skip: ['grade'], insert: [{ after: 'mid', depth: 0.75, svg: String(d) + _windowsLit(k3) + sw + band }, { after: 'near', depth: 1, svg: lamp }, { after: 'near', depth: 0.75, svg: ringSvg }] });
  s += _vig('#0C0A26', 0.5);
  return s;
}
