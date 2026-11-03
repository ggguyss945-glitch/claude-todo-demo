// hook_a.js — hook shots A1-A5: the promise (S00-L001..L004).
//   A1_dogsize   phone POV on the street: the Dog size slider ticks 3 times, Tiny grows dog -> house size ("menu?")
//   A2_oneapp    "One app.": the REALITY SETTINGS icon lands on hit 2, then flies at the lens (zoomThrough into A3)
//   A3_treeflip  the tree flips roots-up next to Kevin, frozen mid leaf-blow (the 1.17 s voice-gap gag)
//   A4_control   "Total control.": the DAY card flips 1 -> 7 while settings rows fan out across the frame
//   A5_noundo    "No undo.": the big UNDO button cracks on "undo" and falls off the bottom (music drop)
// Times come from the voice lines (ctx.line(...).at(word)) with the built timeline's values as fallbacks, so the
// shots follow a rebuilt timeline. Every visual event registers an SFX cue (see _sfx below).
import { street, flipTree, STREET } from '../sets.js';
import * as U from '../ui.js';
import * as U2 from '../ui2.js';
import { FONT, Defs, text, rect, circle, ellipse, path, poly, g, esc, rrPath, gearPath, shade, ink } from '../ui_style.js';
import { sparkle, speedLines, shockRing, starburst } from '../fx.js';
import { clamp, lerp, seg, ease, spring, wobble, rng, noise1d } from '../anim/motion.js';

// =====================================================================================================================
// shared helpers (private: names starting with _ are not registered as shots)
// =====================================================================================================================
const r2 = (n) => Math.round(n * 100) / 100, r3 = (n) => Math.round(n * 1000) / 1000;
const NUN = (size, weight = 900, fill = '#FFFFFF', extra = {}) => ({ fontFamily: FONT.ui, fontWeight: weight, fontSize: size, fill, ...extra });

// sync points (ms into the clip) of the sfx_map.json variants used here: a cue's t is the clip START, chosen so the
// sound's sync point lands on the visual frame (ev). Synthesised names (dog_woof, page_flip, ...) sync at 0.
const SYNC = {
  ui_tap: [2.5, 2.5, 30, 7.5, 7.5, 7.5], ui_select: [10, 10, 22.5, 30, 45], slider_tick: [2.5, 7.5, 12.5, 12.5, 10],
  slider_drag: [5, 7.5, 7.5, 7.5, 10], toggle: [37.5, 12.5, 12.5, 20, 12.5, 35], notif_ping: [5, 2.5, 12.5, 17.5, 2.5, 7.5],
  success_chime: [2.5, 7.5, 15, 10, 10, 7.5], whoosh_short: [250, 270, 277.5, 275, 337.5, 347.5], swish: [47.5, 65, 60, 130, 125, 17.5],
  impact_hit: [7.5, 140, 42.5, 2.5], bonk: [17.5, 17.5, 22.5, 20], boing: [45, 5, 10, 15, 15, 7.5, 7.5, 15, 7.5],
  slide_whistle_up: [55, 50, 32.5, 35], slide_whistle_down: [37.5, 35, 37.5, 35], cartoon_pop: [10, 22.5, 10, 10, 7.5, 10, 12.5, 10, 140],
  zip: [170, 115], glass_crack: [137.5, 92.5, 215], glass_break: [10, 10, 5], stamp: [10, 10, 7.5, 15], magic_shimmer: [2.5, 1515, 5, 10],
  popup_whoosh: [207.5, 115, 87.5, 135, 240, 10],
};
/** register an SFX cue whose sync point hits local time tEv. o: {db (level hint vs the -18 LUFS reference), note} */
function _sfx(ctx, name, v, tEv, o = {}) {
  const tbl = SYNC[name], sm = tbl ? tbl[v % tbl.length] : 0;
  ctx.cue(name, tEv - sm / 1000, { v, ev: r3(ctx.start + tEv), sync_ms: sm, ...o });
}
/** the app background (deep navy, warm glow under the top, faint gear watermark) oversized for camera moves */
function _appBg(o = {}) {
  const pad = 160;
  return `<g transform="translate(${-pad} ${-pad})">${U2.appBg(1920 + pad * 2, 1080 + pad * 2, { rot: o.rot || 0, glow: o.glow, top: o.top, bot: o.bot })}</g>`;
}
/** soft wedge rays behind a hero element (toy-plastic sunburst: alternating lighter wedges, no blend modes) */
function _rays(cx, cy, n, R, rot, color, op) {
  let s = '';
  for (let i = 0; i < n; i++) {
    const a0 = ((i / n) * 360 + rot) * Math.PI / 180, a1 = a0 + (Math.PI / n) * 0.9;
    s += poly([[cx, cy], [cx + Math.cos(a0) * R, cy + Math.sin(a0) * R], [cx + Math.cos(a1) * R, cy + Math.sin(a1) * R]], { fill: color, opacity: op });
  }
  return s;
}
/** a burst of 4-point sparkles flying out of (cx, cy) and fading, u = seconds since the burst */
function _burst(cx, cy, u, o = {}) {
  const dur = o.dur ?? 0.45;
  if (u <= 0 || u >= dur) return '';
  const R = rng(o.seed ?? 3), n = o.n ?? 10, k = u / dur, e = ease.outCubic(k);
  let s = '';
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2 + (R() - 0.5) * 0.6, dist = (o.r ?? 160) * (0.55 + R() * 0.6) * e;
    const sz = (o.size ?? 26) * (0.6 + R() * 0.7) * (1 - k * 0.7);
    s += sparkle(cx + Math.cos(a) * dist, cy + Math.sin(a) * dist * (o.squashY ?? 1), sz, i % 3 ? '#FFFFFF' : '#FFF2A8', 1 - k, u * 200 * (R() - 0.5));
  }
  return s;
}

/** toy-plastic dust puffs: solid cream blobs that fly out along the ground, swell, then shrink away (no transparency
 *  soup), u = seconds since the impact */
function _puffs(cx, cy, u, o = {}) {
  const dur = o.dur ?? 0.45;
  if (u <= 0 || u >= dur) return '';
  const R = rng(o.seed ?? 5), n = o.n ?? 7, k = u / dur, e = ease.outCubic(k), d = new Defs();
  const fill = d.lin(['#FFF8EA', o.color || '#E6D6BA']), line = ink(o.color || '#E6D6BA', 0.6, 0.5);
  let s = '';
  for (let i = 0; i < n; i++) {
    const side = i % 2 ? 1 : -1, a = (0.1 + 0.8 * R()) * Math.PI / 2;
    const dist = (o.r ?? 140) * (0.5 + 0.6 * R()) * e;
    const x = cx + side * Math.cos(a) * dist, y = cy - Math.sin(a) * dist * (o.lift ?? 0.35);
    const rr = (o.size ?? 26) * (0.7 + 0.6 * R()) * Math.sin(Math.PI * Math.min(1, k * 1.15 + 0.08));
    if (rr > 0.5) s += circle(x, y, rr, { fill, stroke: line, strokeWidth: 2.5 });
  }
  return d + s;
}

// =====================================================================================================================
// A1 — phone POV, Dog size: Tiny grows in 3 steps on the slider ticks ("What if real life had a SETTINGS menu?")
// =====================================================================================================================
const STREET_DAY = () => street({ split: true, liveTree: 'kevin' });
const A1_CAM = { x: 590, y: 40, z: 1.22 };          // x <= 590: the near layer ends at world x 2400
const A1_DOG = { x: 1229, y: 792 };
const A1_PHONE = { x: 1370, y: 560, s: 0.58, rot: -8 };
const A1_V = [0.06, 0.4, 0.72, 1.0];                // slider value per state
const A1_S = [0.5, 1.18, 1.98, 3.15];                // Tiny's scale per state (3.15: the head leaves the top of the frame)
const A1_WORD = ['SMALL', 'BIG', 'HUGE', 'HOUSE'];    // value bubble
const A1_MULT = ['×1', '×4', '×9', '×20'];             // card value (top right)
// Kevin's mailbox (near layer, x 1660): cut out of the layer (the hole is refilled with clean sidewalk from 300 px to the
// right: the slab seams repeat every 150 px) and its silhouette redrawn at MX, clear of the hand and under Tiny's paw
const A1_MBOX = { x0: 1598, x1: 1732, y0: 620, y1: 852, base: 836, cx: 1660, MX: 1484 };

/** the Dog size screen (SCREEN space) with our own bubble / value words (same layout as ui2.dogSizeScreen) */
function _dogScreen(v, grab, st, bk) {
  let s = text(36, 300, 'PETS', NUN(26, 900, U.UI.dim, { letterSpacing: 3 }));
  const card = { x: 24, y: 326, w: U2.SCREEN.w - 48, cat: 'dog', value: `{${A1_MULT[st]}|orange}`, v, grab, bubble: A1_WORD[st], bubbleK: bk, bubbleSize: 42, stops: ['Tiny', 'Big', 'HOUSE'], sub: 'Applies to: {Tiny|pink} (next door)' };
  s += U2.settingCard(card);
  s += U.row({ x: 24, y: 792, w: U2.SCREEN.w - 48, cat: 'trees', label: 'Tree direction', icon: 'tree', color: '#3FB24A', value: 'Up' });
  s += U.row({ x: 24, y: 918, w: U2.SCREEN.w - 48, kind: 'toggle', cat: 'birds', label: 'Birdsong', icon: 'bird', color: '#17C2A0', k: 1 });
  s += U.row({ x: 24, y: 1044, w: U2.SCREEN.w - 48, cat: 'gravity', value: 'Earth' });
  s += U.row({ x: 24, y: 1170, w: U2.SCREEN.w - 48, cat: 'weather', value: 'Sunny' });
  return { svg: s, knob: U2.settingCardKnob(card) };
}

export function A1_dogsize(ctx) {
  const t = ctx.t, L = ctx.line('S00-L001');
  const tTap = L ? L.at('What') : 0.35, tDrag = L ? L.at('real') : 0.87;
  const tS = [L ? L.at('life') : 1.43, L ? L.at('SETTINGS') : 2.23, L ? L.at('menu') : 2.79].map((x) => x - 2 / 60);   // snaps lead the word by 2 frames
  const tEnd = L ? L.word(-1).t1 : 3.36, tWoof = Math.min(ctx.dur - 0.22, tEnd + 0.05);
  const stAt = (tt) => (tt >= tS[2] ? 3 : tt >= tS[1] ? 2 : tt >= tS[0] ? 1 : 0);
  const st = stAt(t);

  // ---- SFX
  _sfx(ctx, 'swish', 0, 0.06, { db: -8, note: 'phone rises into frame' });
  _sfx(ctx, 'ui_tap', 3, tTap, { note: 'thumb lands on the Dog size knob' });
  _sfx(ctx, 'slider_drag', 1, tDrag, { db: -6, note: 'drag starts against the detent' });
  tS.forEach((ts, i) => {
    _sfx(ctx, 'slider_tick', 4, ts + 1 / 60, { note: `detent ${i + 1}: ${A1_WORD[i + 1]}` });
    if (i < 2) _sfx(ctx, 'boing', [5, 8][i], ts + 0.12, { db: -4, note: 'growth settles (overshoot peak)' });
  });
  _sfx(ctx, 'slide_whistle_up', 0, tS[1] + 0.02, { db: -5, note: 'Tiny keeps growing (HUGE -> HOUSE)' });
  _sfx(ctx, 'impact_hit', 0, tS[2] + 2 / 60, { note: 'house size: the ground thumps' });
  _sfx(ctx, 'bonk', 3, tS[2] + 0.04, { db: -3, note: "Kevin's mailbox gets squashed" });
  _sfx(ctx, 'dog_woof', 0, tWoof, { size: 'giant', note: 'synth: house-size Tiny barks once (pitched down)' });

  // ---- Tiny's size: spring to each step (overshoot reads as the growth 'boing')
  // closed form per segment: from the previous target to the next one
  const dogS = (tt) => {
    let s = A1_S[0];
    for (let i = 0; i < 3; i++) if (tt >= tS[i]) s = A1_S[i] + (A1_S[i + 1] - A1_S[i]) * spring(tt - tS[i], i === 2 ? 3.6 : 4.5, i === 2 ? 0.38 : 0.42);
    return s;
  };
  const s = dogS(t);

  // ---- camera: push 4%, shake on every growth step, 1.15x punch toward Tiny on "menu?"
  const cam = ctx.cam({
    x: A1_CAM.x, y: A1_CAM.y, z: A1_CAM.z, push: 0.04, drift: 5,
    shake: [{ t: tS[0] + 1 / 60, amp: 9 }, { t: tS[1] + 1 / 60, amp: 13 }, { t: tS[2] + 2 / 60, amp: 30, decay: 0.09 }],
    punch: [{ t: tS[2] + 1 / 60, k: 1.15, at: [600, 330], in: 3, settle: 0.32, keep: 0.06 }],
  });

  // ---- Tiny: happy -> excited -> starstruck -> (2-frame shock) -> excited, tail wags faster each step, a giant woof
  const wagHz = [2.4, 3.4, 4.6, 5.8];
  // wag phase = integral of the rate (no pops when the rate steps up)
  let ph = 0, last = 0;
  for (let i = 0; i < 3; i++) { const te = Math.min(t, tS[i]); if (te > last) { ph += (te - last) * wagHz[i]; last = te; } }
  if (t > last) ph += (t - last) * wagHz[stAt(t)];
  const wag = 0.85 * Math.sin(2 * Math.PI * ph);
  const barking = t >= tWoof - 0.02 && t < tWoof + 0.2;
  const face = [[0, 'happy'], [tS[0], 'excited'], [tS[1], 'starstruck'], [tS[2], 'shocked'], [tS[2] + 3 / 60, 'excited', 0],
    [tWoof - 0.02, { preset: 'excited', mouth: 'o' }, 0.6], [tWoof + 0.2, 'excited', 0]];
  const dog = ctx.actor('tiny', {
    x: A1_DOG.x, y: A1_DOG.y, s, lod: s, facing: 'front', face, tailWag: 0,
    // curious head tilt while the thumb drags against the first detent, ears up for the bark
    pose: () => ({ wag, tongue: barking ? 0.4 : 1.1 + 0.25 * st, ears: barking ? 70 : undefined,
      head: barking ? -6 : t < tS[0] ? 11 * ease.outBack(seg(t, tDrag, tDrag + 0.16), 1.6) : 0 }),
    squash: [[tS[0] + 0.12, 0.07], [tS[1] + 0.12, 0.08], [tS[2] + 0.16, 0.1], [tWoof, -0.05]],
  });

  // ---- Kevin's mailbox: moved out of the near layer (silhouette only) and drawn in front of Tiny; the house-size paw
  // comes down on it and it flattens toward its base, the red flag pops off
  const set = ctx.memo('hook_a/street', STREET_DAY);
  const near = set.layers.find((l) => l.name === 'near').svg;
  const mb = A1_MBOX, tCrush = tS[2] + 0.04, b = mb.base, cx = mb.cx;
  const crush = t < tCrush ? 0 : spring(t - tCrush, 5.5, 0.5);
  const sy = 1 - 0.74 * crush, sx = 1 + 0.42 * crush;
  const sil = `M${cx - 52} ${b - 202}H${cx + (crush ? 46 : 64)}V${b - 110}H${cx + 13}V${b + 3}H${cx - 13}V${b - 110}H${cx - 52}Z`;   // no flag once it flew off
  const clips = `<defs><clipPath id="a1nb"><path clip-rule="evenodd" d="M-3000 -3000H5000V5000H-3000Z M${mb.x0} ${mb.y0}H${mb.x1}V${mb.y1}H${mb.x0}Z"/></clipPath>`
    + `<clipPath id="a1pt"><rect x="${mb.x0 - 3}" y="${mb.y0 - 3}" width="${mb.x1 - mb.x0 + 6}" height="${mb.y1 - mb.y0 + 6}"/></clipPath>`
    + `<clipPath id="a1mb"><path d="${sil}"/></clipPath></defs>`;
  const dx = mb.MX - cx;
  let mailbox = ellipse(mb.MX, b + 2, 46 * (1 + 0.6 * crush), 9, { fill: '#1A1430', opacity: 0.24 })
    + `<g transform="translate(${mb.MX} ${b}) scale(${r3(sx)} ${r3(sy)}) translate(${-mb.MX} ${-b}) translate(${dx} 0)"><g clip-path="url(#a1mb)">${near}</g></g>`;
  if (t >= tCrush) {
    // the flag flies off (parabola, spinning) and a puff of dust
    const u = t - tCrush, fx0 = mb.MX + 42, fy0 = b - 170;
    const fxp = fx0 + 260 * u, fyp = fy0 - 520 * u + 0.5 * 2600 * u * u;
    if (fyp < b + 40) mailbox += g(rect(-16, -8, 32, 16, { rx: 4, fill: '#FF4A3D', stroke: ink('#FF4A3D'), strokeWidth: 2 }) + rect(-5, 0, 10, 40, { rx: 3, fill: '#FF4A3D', stroke: ink('#FF4A3D'), strokeWidth: 2 }), { transform: `translate(${r2(fxp)} ${r2(fyp)}) rotate(${r2(u * 900)})` });
    mailbox += _puffs(mb.MX, b - 4, u, { n: 8, r: 150, size: 20, seed: 21, dur: 0.42 });
  }
  const nearCut = `<g clip-path="url(#a1nb)">${near}</g><g clip-path="url(#a1pt)"><g transform="translate(-300 0)">${near}</g></g>`;
  const tree = flipTree({ ...STREET.trees.kevin, angle: 0 });
  // growth sparkles round Tiny (world, depth .75)
  let fx = '';
  tS.forEach((ts, i) => { fx += _burst(A1_DOG.x, A1_DOG.y - 130 * A1_S[i + 1], t - ts, { n: 9 + i * 3, r: 120 + 110 * A1_S[i + 1], size: 22 + 8 * i, seed: 11 + i, dur: 0.5 }); });

  let world = cam.set(set, {
    skip: ['near'],
    insert: [
      { after: 'mid', depth: 0.75, svg: tree },
      { after: 'yard', depth: 0.75, svg: dog + fx },
      { after: 'top', depth: 1, svg: nearCut },
      { after: 'top', depth: 1, svg: mailbox },      // on the sidewalk, in front of Tiny
    ],
  });
  // close-up depth: the street is a touch soft behind the phone; on "menu?" focus racks to Tiny
  const soft = lerp(1.7, 0.5, seg(t, tS[2], tS[2] + 0.25));
  const d = new Defs();
  let out = clips + d + `<g filter="${d.blur(r2(soft), 0.02)}">${world}</g>`;

  // ---- the phone (screen space, handheld): rises in on frame 0, jolts with every growth step
  const rise = 1 - ease.outBack(seg(t, 0, 0.24), 1.4);
  const jolt = tS.reduce((a, ts, i) => a + (t > ts ? wobble(t - ts, 6, 0.4) * [6, 9, 16][i] : 0), 0);
  const P = {
    x: A1_PHONE.x + 3 * noise1d(ctx.gt * 0.6, 41), y: A1_PHONE.y + 120 * rise + 3 * noise1d(ctx.gt * 0.5, 42) + jolt,
    s: A1_PHONE.s, rot: A1_PHONE.rot - 5 * rise + 0.5 * noise1d(ctx.gt * 0.4, 43),
  };
  // slider: holds near 'Tiny', creeps against each detent, snaps (outBack) on the tick
  const vAt = (tt) => {
    let v = A1_V[0];
    for (let i = 0; i < 3; i++) {
      const t0 = i === 0 ? tDrag : tS[i - 1] + 0.12;
      if (tt >= t0 && tt < tS[i]) v = A1_V[i] + 0.035 * ease.inOutSine(seg(tt, t0, tS[i]));
      if (tt >= tS[i]) v = lerp(A1_V[i] + 0.035, A1_V[i + 1], ease.outBack(seg(tt, tS[i], tS[i] + 5 / 60), 1.6));
    }
    return clamp(v, 0, 1.02);
  };
  const v = vAt(t);
  const grab = seg(t, tTap, tTap + 4 / 60);
  const bk = t < tTap ? 0 : seg(t, st === 0 ? tTap : tS[st - 1], (st === 0 ? tTap : tS[st - 1]) + 8 / 60);
  const scr = _dogScreen(Math.min(1, v), grab, st, bk);
  // thumb: hovers below the knob, lands on "What", holds (press .7) and drags with the knob
  const [kx, ky] = scr.knob, hov = 1 - ease.outCubic(seg(t, tTap - 0.2, tTap));
  const press = t < tTap ? 0 : t < tTap + 3 / 60 ? 1 : lerp(1, 0.7, seg(t, tTap + 3 / 60, tTap + 0.15));
  const thumb = { x: kx + 14 + 70 * hov, y: ky + 26 + 150 * hov, press };
  out += cam.screen(U2.phone({ ...P, screen: U2.appScreen({ time: '4:05', crumb: 'Settings › {World|purple} › {Pets|pink}', content: scr.svg }), thumb }), { shake: true });
  // tap ring on the knob, ticks flash a ring too
  const kp = U2.phonePoint(P, kx, ky);
  out += cam.screen(U.tapRing(kp[0], kp[1], seg(t, tTap, tTap + 0.3)), { shake: true });
  tS.forEach((ts) => { out += cam.screen(U.tapRing(kp[0], kp[1], seg(t, ts, ts + 0.26), '#FFE0B0'), { shake: true }); });
  return out;
}

// =====================================================================================================================
// A2 — "One app.": the app icon lands on hit 2, a badge pops on "One", it flies at the lens on "app"
// =====================================================================================================================
const A2_RECT = [660, 240, 600, 600, 130];    // the zoomThrough rect of A3's tin (icon face at the window start)

export function A2_oneapp(ctx) {
  const t = ctx.t, L = ctx.line('S00-L002');
  const tHit = (ctx.T.sync?.H2 ?? 3.76) - ctx.start;                 // 0.093
  const tOne = L ? L.at('One') : 0.143, tApp = L ? L.at('app') : 0.423;
  const tZ = ctx.dur - (ctx.T.shots[ctx.index + 1]?.tin?.dur ?? 0.133);   // zoomThrough window start (local)
  const [rx, ry, rw] = A2_RECT, cx0 = rx + rw / 2, cy0 = ry + rw / 2;

  _sfx(ctx, 'swish', 3, tHit - 0.01, { db: -6, note: 'icon flies in from depth' });
  _sfx(ctx, 'impact_hit', 2, tHit, { note: 'icon lands on hit 2 (with the music hit)' });
  _sfx(ctx, 'notif_ping', 1, tOne + 0.02, { db: -3, note: 'red badge "1" pops on "One"' });
  _sfx(ctx, 'whoosh_short', 0, tZ + 0.06, { note: 'flies at the lens / zoom through the icon (peak mid-zoom)' });

  // icon size: flies in from far (0 -> hit), lands with an overshoot, breathes, then rushes the lens on "app"
  let size;
  if (t < tHit) size = lerp(150, 360, ease.inCubic(seg(t, -1 / 60, tHit)));
  else if (t < tApp) size = 330 + 30 * spring(t - tHit, 5, 0.35) + 14 * seg(t, tHit, tApp);
  else size = lerp(330 + 30 * spring(tApp - tHit, 5, 0.35) + 14, rw, ease.inOutCubic(seg(t, tApp, tZ)));
  if (t >= tZ) size = rw;
  const fly = seg(t, tApp, tZ), cyH = cy0 - 68;                       // holds above the caption, centres for the zoom
  const cy = t < tHit ? lerp(cyH + 60, cyH, ease.outCubic(seg(t, -2 / 60, tHit))) : lerp(cyH, cy0, ease.inOutCubic(fly));
  const rot = (t < tHit ? lerp(-24, 0, ease.outCubic(seg(t, -2 / 60, tHit))) : 0);
  const gearRot = 40 * t + 260 * ease.inCubic(fly);

  // background: purple app glow, slow rays, radial speed lines while it rushes the lens
  const cam = ctx.cam({ push: 0.05, drift: 6, shake: [{ t: tHit, amp: 16 }] });
  const d = new Defs();
  const glowF = d.rad([[0, '#FFB070', 0.32], [0.6, '#FF7A3D', 0.1], [1, '#FF7A3D', 0]]);
  let out = cam.layer(_appBg({ top: '#5440C4', bot: '#1E1656', glow: '#FF8A4D', rot: t * 8 }) + _rays(960, 540, 18, 1600, t * 14, '#FFFFFF', 0.045), 0.4);
  out += d + cam.layer(circle(960, cy, 560 + 200 * fly, { fill: glowF }), 0.7);
  if (fly > 0.05) out += speedLines({ cx: 960, cy: 540, count: 34, seed: 17, t: t * 1.4, op: 0.55 * ease.inCubic(fly), r0: 380 + 200 * fly, r1: 1500, width: 14 });
  // impact ring + starburst flash behind the icon on the hit
  out += shockRing(960, cyH, 520, seg(t, tHit, tHit + 0.32), '#FFE0B0', 22);
  const sb = seg(t, tHit - 1 / 60, tHit + 0.3);
  if (sb > 0 && sb < 1) out += g(starburst({ cx: 960, cy: cyH, r: 300, points: 16, fill: '#FF9A4D', core: '#FFE36A', seed: 4, fadeOut: true }, sb), { opacity: 0.85 });
  // the icon (screen space so it sits exactly on the zoomThrough rect at the window start)
  let icon = U2.appIcon({ cx: 960, cy, size, rot: gearRot, glow: 0.9, shine: seg(t, tHit + 0.04, tHit + 0.36) });
  // badge "1" pops on "One" (drawn here so it can pop with overshoot)
  const bp = seg(t, tOne - 1 / 60, tOne + 7 / 60);
  if (bp > 0) {
    const br = size * 0.17, bx = 960 - size / 2 + size - size * 0.06, by = cy - size / 2 + size * 0.06;
    const dd = new Defs();
    let b = circle(bx, by + br * 0.1, br, { fill: '#7A0A1C' });
    b += circle(bx, by, br, { fill: dd.lin(['#FF7A7E', U.UI.red, '#D41E3A']), stroke: '#FFFFFF', strokeWidth: br * 0.2 });
    b += text(bx, by + br * 0.42, '1', { fontFamily: FONT.title, fontSize: br * 1.2, fill: '#FFFFFF', textAnchor: 'middle' });
    icon += dd + (bp >= 1 ? b : popInSimple(b, bx, by, bp));
  }
  if (rot) icon = g(icon, { transform: `rotate(${r2(rot)} 960 ${r2(cy)})` });
  out += cam.screen(icon, { shake: true });
  // the portal follows the icon face (the timeline also gives tin.rect, which wins)
  ctx.portal([960 - size / 2, cy - size / 2, size, size, size * 0.22]);
  return out;
}
function popInSimple(svg, cx, cy, p) {
  const k = p < 0.45 ? lerp(0.3, 1.25, ease.outCubic(p / 0.45)) : lerp(1.25, 1, ease.inOutSine(seg(p, 0.45, 1)));
  return `<g transform="translate(${r2(cx)} ${r2(cy)}) scale(${r3(k)}) translate(${r2(-cx)} ${r2(-cy)})">${svg}</g>`;
}

// =====================================================================================================================
// A3 — the tree flips roots-up; Kevin frozen mid leaf-blow, deadpan -> shocked on the BONK
// =====================================================================================================================
const A3_CAM = { x: 800, y: 10, z: 1.7 };             // near-layer right edge 960 + 800 + 960/1.7 = 2325 < 2400
const A3_KEVIN = { x: 1330, y: 792, s: 0.66 };       // left of the set's mailbox (near layer, screen x ~790)

export function A3_treeflip(ctx) {
  const t = ctx.t;
  const tCard = 0.06, tTap = 0.24, tRip = 0.31, tLand = 0.6;
  _sfx(ctx, 'ui_select', 0, tCard + 0.04, { db: -4, note: 'Tree direction card pops in the corner' });
  _sfx(ctx, 'ui_tap', 4, tTap, { note: 'Up -> Down' });
  _sfx(ctx, 'toggle', 4, tTap + 0.02, { db: -3 });
  _sfx(ctx, 'cartoon_pop', 0, tRip, { note: 'roots pop out of the lawn' });
  _sfx(ctx, 'zip', 0, (tRip + tLand) / 2, { note: 'the tree swings over' });
  _sfx(ctx, 'bonk', 0, tLand, { note: 'the crown hits the lawn' });
  _sfx(ctx, 'cartoon_pop', 2, tLand + 0.26, { db: -10, note: 'soil clods land' });
  _sfx(ctx, 'cartoon_pop', 5, tLand + 0.36, { db: -12, note: 'soil clods bounce' });

  // camera: lands from the zoomThrough still moving (zoom + roll settle), slight tilt, slow push, shake on the BONK
  const cam = ctx.cam({
    keys: [[-0.14, { x: A3_CAM.x + 40, y: A3_CAM.y - 24, z: A3_CAM.z * 1.14, r: -4.5 }], [0, { x: A3_CAM.x + 16, y: A3_CAM.y - 8, z: A3_CAM.z * 1.045, r: -2.6 }, 'linear'],
      [0.26, { x: A3_CAM.x, y: A3_CAM.y, z: A3_CAM.z, r: -1.4 }, 'outCubic'], [ctx.dur, { x: A3_CAM.x - 14, y: A3_CAM.y, z: A3_CAM.z * 1.03, r: -1.0 }, 'inOutSine']],
    drift: 4, shake: [{ t: tLand, amp: 20, decay: 0.08 }],
  });

  // the tree: shiver, rip out with a hop, swing over, land on its crown (squash), soil clods drop
  const T = STREET.trees.kevin;
  const shiver = t > tRip - 0.07 && t < tRip ? 4 * Math.sin(t * 120) : 0;
  const fl = seg(t, tRip, tLand);
  const angle = 180 * ease.inOutCubic(fl) + (t >= tLand ? -9 * wobble(t - tLand, 3.4, 0.35) : 0) + shiver;
  const hop = 150 * Math.sin(Math.PI * fl) * (t < tLand ? 1 : 0);
  const roots = seg(t, tRip - 0.02, tRip + 0.12);
  let tree = flipTree({ ...T, angle, hop, roots, soil: t > tLand - 0.08 ? t - (tLand - 0.08) : 0 });
  if (t >= tLand) {
    const q = wobble(t - tLand, 5, 0.4);
    tree = `<g transform="translate(${T.x} ${T.base}) scale(${r3(1 + 0.08 * q)} ${r3(1 - 0.1 * q)}) translate(${-T.x} ${-T.base})">${tree}</g>`;
  }
  // dust puffs where the crown lands
  const puff = _puffs(T.x, T.base + 6, t - tLand, { n: 9, r: 230, size: 26, seed: 77, dur: 0.5, color: '#DCC7A2' });
  // Kevin: frozen mid-blow (statue), deadpan; shocked take on the BONK
  const kev = ctx.actor('kevin', {
    x: A3_KEVIN.x, y: A3_KEVIN.y, s: A3_KEVIN.s, facing: 'tq-left', idle: 0, blink: false, nervous: 0.35,   // the blower hums
    face: [[0, 'deadpan'], [tLand + 1 / 60, 'surprised'], [tLand + 3 / 60, 'shocked', 0]],
    pose: { armL: 28, foreL: 14, armR: 12, foreR: 30, lean: -2 },
    squash: [[tLand + 1 / 60, -0.06]],
  });
  // leaves blowing out of the nozzle (frozen Kevin keeps the blower running)
  const leaves = _leafStream(t, A3_KEVIN);
  let out = cam.set(ctx.memo('hook_a/street', STREET_DAY), {
    insert: [{ after: 'mid', depth: 0.75, svg: tree + puff }, { after: 'yard', depth: 0.75, svg: kev + leaves }],
  });
  // the corner card: Tree direction  [Up | Down]
  out += cam.screen(_treeCard(t, tCard, tTap));
  return out;
}
/** leaves streaming out of the blower nozzle to the left, looping, deterministic */
function _leafStream(t, K) {
  const nx = K.x - 166 * K.s, ny = K.y - 26 * K.s;        // nozzle tip (world), measured on a 1:1 still
  let s = '';
  const R = rng(91), cols = ['#F2A51C', '#E5693A', '#9BCB3C', '#F6C445'];
  for (let i = 0; i < 12; i++) {
    const ph = R(), sp = 0.55 + R() * 0.3, u = ((t / sp + ph) % 1 + 1) % 1;
    const x = nx - 20 - 380 * u - 30 * R(), y = ny - 4 - 70 * Math.sin(Math.PI * u) * (0.5 + R()) + 12 * Math.sin(u * 11 + i);
    const sz = 9 + R() * 6, rot = (t * 500 + i * 47) % 360;
    s += path(`M0 ${-sz}Q${sz * 0.8} 0 0 ${sz}Q${-sz * 0.8} 0 0 ${-sz}Z`, { fill: cols[i % 4], stroke: ink(cols[i % 4]), strokeWidth: 1.5, opacity: r2(Math.min(1, (1 - u) * 3)), transform: `translate(${r2(x)} ${r2(y)}) rotate(${r2(rot)})` });
  }
  return s;
}
/** the "Tree direction" mini card (screen space, top-left): chips Up / Down; pops at t0, switches at t1 */
function _treeCard(t, t0, t1) {
  const p = seg(t, t0, t0 + 8 / 60);
  if (p <= 0) return '';
  const x = 56, y = 54, w = 470, h = 236, d = new Defs();
  let s = path(rrPath(x, y + 8, w, h, 30), { fill: '#080C24', opacity: 0.85 });
  s += path(rrPath(x, y, w, h, 30), { fill: d.lin(['#2E3A7C', '#1D2758']), stroke: '#0A0F2C', strokeWidth: 3 });
  s += path(rrPath(x + 26, y + 7, w - 52, 8, 4), { fill: '#FFFFFF', opacity: 0.14 });
  s += U.iconTile('tree', x + 58, y + 56, 64, '#3FB24A');
  s += text(x + 104, y + 70, 'Tree direction', NUN(36, 900, '#FFFFFF'));
  const pick = t >= t1 ? 1 : 0;
  s += U.chips({ x: x + 22, y: y + 104, w: w - 44, h: 112, pick, pickK: pick ? seg(t, t1, t1 + 7 / 60) : undefined, options: [{ label: 'Up', icon: 'tree' }, { label: 'Down', icon: 'treeFlip' }] });
  // tap ring on the Down chip
  s += U.tapRing(x + 22 + (w - 44) * 0.75, y + 160, seg(t, t1, t1 + 0.3));
  return popInCard(d + s, x + w / 2, y + h / 2, p, { x, y, w, h });
}
function popInCard(svg, cx, cy, p, b) {
  if (p >= 1) return svg;
  const k = p < 0.45 ? lerp(0.4, 1.12, ease.outCubic(p / 0.45)) : p < 0.72 ? lerp(1.12, 0.97, ease.inOutSine((p - 0.45) / 0.27)) : lerp(0.97, 1, ease.outCubic((p - 0.72) / 0.28));
  const fl = p < 0.5 ? (1 - seg(p, 0.15, 0.5)) * 0.5 : 0;
  return `<g opacity="${r2(clamp(p / 0.3))}" transform="translate(${r2(cx)} ${r2(cy)}) scale(${r3(k)}) translate(${r2(-cx)} ${r2(-cy)})">${svg}${fl > 0.01 ? path(rrPath(b.x, b.y, b.w, b.h, 30), { fill: '#FFFFFF', opacity: r2(fl) }) : ''}</g>`;
}

// =====================================================================================================================
// A4 — "Total control.": DAY card flips 1 -> 7 (lands on "control"), the settings fan out, fast push 8%
// =====================================================================================================================
export function A4_control(ctx) {
  const t = ctx.t, L = ctx.line('S00-L003');
  const tHit = (ctx.T.sync?.H3 ?? 5.606) - ctx.start;              // 0.106
  const tTot = L ? L.at('Total') : 0.156, tCtl = L ? L.at('control') : 0.516;
  const nF = 6, fd = (tCtl - tTot) / nF;                              // six flips between "Total" and "control"
  const fanT0 = -0.06, fanT1 = 0.92;

  _sfx(ctx, 'swish', 0, 0.0, { db: -6, note: 'cut: the DAY card drops in from above the lens' });
  _sfx(ctx, 'cartoon_pop', 7, tHit, { db: -4, note: 'DAY card lands on hit 3' });
  for (let i = 0; i < nF; i++) _sfx(ctx, 'page_flip', 0, tTot + i * fd, { db: -6, note: `DAY ${i + 1} -> ${i + 2}` });
  _sfx(ctx, 'success_chime', 0, tCtl, { note: 'DAY 7 lands on "control"' });
  // the fan's own events (from the same layout as ui2.fanMontage): toggles flip, sliders land, rows pop
  const ev = _fanEvents(fanT0, fanT1);
  ev.toggles.slice(0, 3).forEach((tt, i) => _sfx(ctx, 'toggle', [2, 4, 1][i], tt, { db: -5, note: 'fan toggle flips on' }));
  ev.sliders.slice(0, 1).forEach((tt) => _sfx(ctx, 'slider_tick', 2, tt, { db: -6, note: 'fan slider lands' }));
  ev.pops.filter((_, i) => i % 4 === 1).slice(0, 3).forEach((tt, i) => _sfx(ctx, 'cartoon_pop', [3, 4, 5][i], tt, { db: -12, note: 'fan rows pop in' }));

  const cam = ctx.cam({ keys: [[0, { z: 1.0, y: 10 }], [ctx.dur, { z: 1.08, y: -6 }, 'inOutSine']], drift: 5, shake: [{ t: tHit, amp: 12 }, { t: tCtl, amp: 8 }] });
  const d = new Defs();
  let out = cam.layer(_appBg({ glow: '#FF8A4D', rot: t * 10 }), 0.3);
  out += d + cam.layer(_rays(960, 470, 20, 1700, -t * 18, '#FFFFFF', 0.04) + circle(960, 470, 640, { fill: d.rad([[0, '#FF9A4D', 0.3], [1, '#FF9A4D', 0]]) }), 0.5);
  // settings rows and sliders fan out from below the frame
  const fp = ease.outCubic(seg(t, fanT0, fanT1));
  out += cam.layer(U2.fanMontage({ cx: 960, p: fp, seed: 7 }), 0.8);
  // DAY card: slams down onto the hit (1.45 -> 1, already on frame 0), split-flaps 1 -> 7, punches on "control"
  const slam = t < tHit ? lerp(1.45, 1, ease.inQuad(seg(t, 0, tHit))) : 1 - 0.07 * wobble(t - tHit, 4.2, 0.4);
  let day = 1, flip;
  for (let i = 0; i < nF; i++) { const a = tTot + i * fd; if (t >= a) { day = i + 1; flip = seg(t, a, a + fd); } }
  if (t >= tCtl) { day = 7; flip = undefined; }
  const punch = t >= tCtl ? 1 + 0.14 * wobble(t - tCtl, 3.2, 0.42) : 1;
  out += cam.layer(_burst(960, 452, t - tCtl, { n: 16, r: 470, size: 36, seed: 5, dur: 0.6 }) + shockRing(960, 452, 520, seg(t, tCtl, tCtl + 0.35), '#FFE0B0', 20)
    + shockRing(960, 452, 420, seg(t, tHit, tHit + 0.3), '#FFFFFF', 16), 1);
  const card = U.dayCard({ cx: 960, cy: 452, day, next: day + 1, flip: flip !== undefined && flip < 1 ? flip : undefined, scale: 0.8 * punch * slam, gearRot: t * 50 + (t >= tCtl ? 30 * ease.outCubic(seg(t, tCtl, tCtl + 0.3)) : 0) });
  out += cam.layer(card, 1);
  return out;
}
/** replicate ui2.fanMontage's item order to time the montage's SFX (toggles flip, sliders land, rows pop) of the items
 *  that are not hidden behind the DAY card */
function _fanEvents(t0, t1, o = {}) {
  const count = o.count ?? 16, R = rng(o.seed ?? 7), rings = [760, 1060, 1360], per = [4, 6, 6], items = [];
  let i = 0;
  rings.forEach((rad, ri) => {
    for (let j = 0; j < per[ri] && i < count; j++, i++) {
      const n = per[ri], u = n === 1 ? 0.5 : j / (n - 1), span = [44, 50, 54][ri];
      const kindR = R(); R();
      items.push({ ri, a: lerp(-span, span, u) + (R() - 0.5) * 5, kind: kindR < 0.35 ? 'toggle' : kindR < 0.6 ? 'slider' : 'value' });
      R();
    }
  });
  items.sort((A, B) => Math.abs(A.a) - Math.abs(B.a) || A.ri - B.ri);
  // p(t) = outCubic(seg(t, t0, t1)); invert numerically
  const tOf = (p) => { let lo = t0, hi = t1; for (let k = 0; k < 30; k++) { const m = (lo + hi) / 2; if (ease.outCubic(seg(m, t0, t1)) < p) lo = m; else hi = m; } return (lo + hi) / 2; };
  const out = { toggles: [], sliders: [], pops: [] };
  items.forEach((it, k) => {
    const st0 = (k / items.length) * 0.6;
    if (it.ri > 0 && Math.abs(it.a) < 13) return;          // behind the DAY card: no sound for what nobody sees
    out.pops.push(tOf(st0 + 0.4 * 0.35));
    if (it.kind === 'toggle') out.toggles.push(tOf(st0 + 0.4 * 0.62));
    if (it.kind === 'slider') out.sliders.push(tOf(st0 + 0.4 * 0.9));
  });
  out.toggles.sort((a, b) => a - b); out.sliders.sort((a, b) => a - b); out.pops.sort((a, b) => a - b);
  return out;
}

// =====================================================================================================================
// A5 — "No undo.": the big UNDO button cracks on "undo", splits and falls off the bottom; deadpan, locked + drift
// =====================================================================================================================
export function A5_noundo(ctx) {
  const t = ctx.t, L = ctx.line('S00-L004');
  const tHit = (ctx.T.sync?.H4 ?? 6.991) - ctx.start;              // 0.108
  const tUndo = L ? L.at('undo') : 0.348;
  const tCrack1 = tUndo + 0.2, tFall0 = tUndo + 0.17, tFall1 = tFall0 + 0.32;
  const tBonk = Math.min(ctx.dur - 0.08, tFall1 + 0.0);

  _sfx(ctx, 'swish', 2, 0.01, { db: -7, note: 'cut: the UNDO button drops in' });
  _sfx(ctx, 'stamp', 2, tHit, { db: -4, note: 'UNDO button slams in on hit 4' });
  _sfx(ctx, 'glass_crack', 0, tUndo, { note: 'cracks on "undo" (music drops here)' });
  _sfx(ctx, 'glass_break', 1, tFall0 + 0.02, { db: -9, note: 'the halves split' });
  _sfx(ctx, 'slide_whistle_down', 2, tFall0 + 0.04, { db: -3, note: 'falls off the bottom' });
  _sfx(ctx, 'bonk', 1, tBonk, { note: 'lands off-screen, just before the A6 glitch' });

  const cam = ctx.cam({ push: 0.02, drift: 4, shake: [{ t: tUndo, amp: 7, decay: 0.07 }] });
  const d = new Defs();
  let out = cam.layer(_appBg({ glow: '#5A8CFF', rot: t * 4 }), 0.3);
  out += d + cam.layer(circle(960, 470, 560, { fill: d.rad([[0, '#5AB8FF', 0.22], [1, '#5AB8FF', 0]]) }), 0.6);
  // the app header (we are inside REALITY SETTINGS, History)
  out += cam.layer(U.logo(120, 132, 46, { rot: t * 20 }) + text(186, 148, `REALITY <tspan fill="${U.UI.orange}">SETTINGS</tspan>`, { fontFamily: FONT.title, fontSize: 58, fill: '#FFFFFF', letterSpacing: 1 })
    + text(188, 190, U.rich('Settings › {History|purple}'), NUN(28, 800, U.UI.sub)), 0.9);
  // the button: slams in on the hit (scale 1.35 -> 1), idles with a soft glow, cracks, splits, falls with rotation
  const slam = t < tHit ? lerp(1.3, 1, ease.inQuad(seg(t, 0, tHit))) : 1 - 0.06 * wobble(t - tHit, 4, 0.4);
  const crack = seg(t, tUndo, tCrack1);
  const fall = seg(t, tFall0, tFall1);
  const btn = U2.undoButton({ cx: 960, cy: 470, w: 460, h: 156, crack, fall, fallDist: 900, rot: 38, scale: 1.6 * slam, seed: 7 });
  out += cam.layer(btn, 1);
  // impact flash on the crack point
  out += cam.layer(shockRing(960 + 20, 455, 220, seg(t, tUndo, tUndo + 0.25), '#FFFFFF', 14), 1);
  return out;
}
