// actor.js — a living cast member: cast.toon() plus the always-on acting layer of engine v3 (bible 1.3, 3.2).
//
//   actor(id, o, t, ctx) -> svg      (inside a shot use ctx.actor(id, o), which passes t and ctx for you)
//
// Everything in o may be a constant, a function of local time t, or keyframes (see motion.js):
//   x, y, s          position (feet, world px) and scale         numbers | track keys [[t, v, ease?], ...]
//   facing           yaw: 'front' | 'tq-left' | ... | degrees   number/name | track keys (degrees) -> smooth turn
//   pose             partial pose object | pose keys [[t, {armR: 150, foreR: 30}, ease?, dur?], ...]
//                    pose keys are pose-to-pose: hold, then snap to the key over dur (default 6 frames, outBack)
//   face             preset | {preset, eyes, mouth, ...} | step keys [[t, face, accent?], ...] (instant swaps,
//                    each change gets a 3-frame squash accent; accent 0 on a key disables it, a number scales it)
//   look / lookAt    pupil offset [dx, dy] (face units, about +-5) | a world point [x, y] to look at (any may be keys)
//   saccade          eye-dart amplitude (0 = off; nervous characters dart every 0.3-0.8 s)
//   add, props       toon add-ons / props, constant or step keys
//   talk             voice role ('SAM') or line id ('S00-L006') to lip-sync, or {visemes:[[t, v]], words} in local time
//   blink            true (default) | false | {every: [1.5, 5.5], seed}; blinks are 4-6 frames, skipped on closed/star eyes
//   idle             amplitude of the idle layer (1 = default; 0 = statue): breathing, head bob, arm sway, hair drift
//   nervous, panic   0..1: per-frame tremble (1-3 px, 4-8 px) and eye darts
//   squash           [[t, amount], ...] damped squash pulses about the feet (+ squash, - stretch)
//   lurch            [[t, k = 1.25], ...]: grow toward the lens in 2 frames, settle over 8 (shouted words)
//   overlap          true: forearms/hands lag the pose by 2 frames, hair/ponytail/pigtails/tail follow on springs
//   ground           world y of the floor: draws a detached contact shadow that shrinks as the actor jumps
//   opacity, seed, shadow
import { toon, toonHeadY } from '../cast.js';
import { yawOf } from '../rig.js';
import { resolve as resolveFace } from '../face.js';
import { contactShadow } from '../style.js';
import { FPS, clamp, lerp, val, isKeys, snaps, step, lastKey, follow, rand, jitter, hash, ease, squashes } from './motion.js';
import { openness } from './lipsync.js';

const BLINKABLE = new Set(['ring', 'bean', 'half', 'angry', 'pin', 'teary', 'squint']);
const r3 = (n) => Math.round(n * 1000) / 1000;
const r2 = (n) => Math.round(n * 100) / 100;

// ---------- blinks ----------
/** blink state at global time gt: 0 open, 1 half, 2 closed. One blink per 3.5 s cell at a seeded offset
 *  (intervals ~1.5-5.5 s), 4-6 frames long, 12% of them doubled. */
export function blinkState(gt, seed = 1, o = {}) {
  const fps = o.fps ?? FPS, cell = o.cell ?? 3.5;
  const c = Math.floor(gt / cell);
  for (const k of [c, c - 1]) {
    const t0 = k * cell + 0.75 + rand(seed, k, 1) * (cell - 1.5);
    const n = 4 + Math.floor(rand(seed, k, 2) * 3);              // 4..6 frames
    const dbl = rand(seed, k, 3) < 0.12;
    for (const tb of dbl ? [t0, t0 + (n + 7) / fps] : [t0]) {
      const fr = Math.floor((gt - tb) * fps + 1e-6);
      if (fr >= 0 && fr < n) return fr === 0 || fr === n - 1 ? 1 : 2;
    }
  }
  return 0;
}
function blinkFace(e, state) {
  if (!state) return e;
  const out = { ...e };
  const mod = (type, per) => {
    if (!BLINKABLE.has(type)) return per;
    if (state === 2) return { ...(per || {}), type: 'closed' };
    const lid = Math.max(per?.lid ?? e.lid ?? (type === 'half' ? -0.08 : -1), 0.3);
    return { ...(per || {}), type, lid, tilt: per?.tilt ?? e.tilt ?? 0 };
  };
  const tl = e.eyeL?.type || e.eyes, tr = e.eyeR?.type || e.eyes;
  if (!BLINKABLE.has(tl) && !BLINKABLE.has(tr)) return e;
  out.eyeL = mod(tl, e.eyeL); out.eyeR = mod(tr, e.eyeR);
  return out;
}

// ---------- saccades ----------
function saccade(gt, seed, amp, fps) {
  if (!amp) return [0, 0];
  const cell = 0.55, c = Math.floor(gt / cell);
  const jitterT = (k) => k * cell + rand(seed, k, 11) * 0.25;           // dart time inside the cell
  const tgt = (k) => { const a = rand(seed, k, 12) * Math.PI * 2, r = amp * (0.4 + 0.6 * rand(seed, k, 13)); return [Math.cos(a) * r, Math.sin(a) * r * 0.6]; };
  let k = c; if (gt < jitterT(c)) k = c - 1;
  const t0 = jitterT(k), u = clamp((gt - t0) * fps / 2);              // 2-frame move
  const a = tgt(k - 1), b = tgt(k);
  return [lerp(a[0], b[0], u), lerp(a[1], b[1], u)];
}

// ---------- accents ----------
// expression-change squash table, per frame since the change (bible: 2-frame head squash 0.95)
const ACCENT = [[1.035, 0.95], [0.99, 1.02], [1, 1]];
function lurchK(t, list, fps) {
  let k = 1;
  for (const e of list) {
    const [t0, amt = 1.25] = Array.isArray(e) ? e : [e];
    const dt = (t - t0) * fps;
    if (dt < 0 || dt > 14) continue;
    const up = dt < 2 ? ease.outQuad(dt / 2) : 1 - ease.inOutSine(clamp((dt - 2) / 8));
    k *= 1 + (amt - 1) * up;
  }
  return k;
}

const facingOf = (v) => (typeof v === 'string' ? yawOf(v) : v);
function faceAt(o, t) {
  if (isKeys(o.face)) {
    const lk = lastKey(o.face, t);
    const v = lk.i < 0 ? o.face[0][1] : lk.v;
    return { spec: v, changedAt: lk.i > 0 ? lk.t : -Infinity, accent: lk.i > 0 ? (o.face[lk.i][2] ?? 1) : 0 };
  }
  return { spec: val(o.face, t), changedAt: -Infinity, accent: 0 };
}
function stepOrVal(v, t) { return isKeys(v) ? step(v)(t) : val(v, t); }

/** compute every parameter the actor will be drawn with (exported for debugging and for shots that need the
 *  head position, e.g. to anchor a punch-in or a sweat drop). */
export function actorState(id, o = {}, t = 0, ctx = {}) {
  const fps = ctx.fps ?? FPS, gt = ctx.gt ?? t, seed = o.seed ?? hash(id) % 100000;
  const idle = o.idle ?? 1;
  const xF = (tt) => val(o.x ?? 960, tt), yF = (tt) => val(o.y ?? 900, tt), sF = (tt) => val(o.s ?? 1, tt);
  let x = xF(t), y = yF(t);
  const s = sF(t);
  // pose: object or pose keys; forearms and hands lag 2 frames (overlap)
  const poseFn = isKeys(o.pose) ? snaps(o.pose, { dur: o.poseDur ?? 6 / fps, ease: o.poseEase || 'outBack', from: o.poseFrom || {} }) : (tt) => val(o.pose, tt) || {};
  const pose = { ...poseFn(t) };
  if (o.overlap !== false && isKeys(o.pose)) {
    const lag = poseFn(t - (o.lag ?? 2) / fps);
    for (const k of ['foreL', 'foreR', 'handL', 'handR']) if (lag[k] !== undefined) pose[k] = lag[k];
  }
  // idle layer: breathing, bob, arm sway, head drift (phases per character; global time so cuts stay continuous)
  const ph = (k) => rand(seed, 50 + k) * Math.PI * 2;
  const breathe = idle * 0.006 * Math.sin(2 * Math.PI * 0.5 * gt + ph(0));
  pose.bob = (pose.bob || 0) + idle * 1.4 * Math.sin(2 * Math.PI * 0.5 * gt + ph(0) + 1.2);
  pose.armL = (pose.armL ?? 8) + idle * 2.2 * Math.sin(2 * Math.PI * 0.31 * gt + ph(1));
  pose.armR = (pose.armR ?? 8) + idle * 2.2 * Math.sin(2 * Math.PI * 0.27 * gt + ph(2));
  pose.head = (pose.head || 0) + idle * 0.9 * Math.sin(2 * Math.PI * 0.19 * gt + ph(3));
  // nervous / panic tremble (per-frame, 1-3 px / 4-8 px in screen px)
  const nerv = val(o.nervous ?? 0, t), panic = val(o.panic ?? 0, t);
  if (nerv || panic) {
    const amp = nerv * 2 + panic * 6;
    x += jitter(gt, seed + 1, fps) * amp; y += jitter(gt, seed + 2, fps) * amp * 0.5;
  }
  // face: expression track, blink, lip-sync
  const fa = faceAt(o, t);
  let e = resolveFace(fa.spec || 'neutral');
  const talking = o.talk ? (ctx.mouth ? ctx.mouth(o.talk, t) : null) : null;
  if (talking) {
    e = { ...e, mouth: talking, m: o.talkScale ?? 1, mouthDX: 0, mouthTilt: 0 };
    pose.head += (o.talkNod ?? 1.2) * openness(talking);
  }
  const bl = o.blink === false ? 0 : blinkState(gt, seed + 7, { fps, ...(typeof o.blink === 'object' ? o.blink : {}) });
  e = blinkFace(e, bl);
  // eyes: look / lookAt / saccades
  let look = null;
  if (o.lookAt) {
    const P = val(o.lookAt, t);
    if (P) {
      const hx = x, hy = y + toonHeadY(id) * s, dx = P[0] - hx, dy = P[1] - hy, L = Math.hypot(dx, dy) || 1;
      const k = Math.min(1, L / 160) * (o.lookAmp ?? 5);
      look = [(dx / L) * k, (dy / L) * k * 0.8];
    }
  } else if (o.look) look = val(o.look, t);
  const sacc = saccade(gt, seed + 9, (o.saccade ?? 0) + nerv * 2.2 + panic * 3, fps);
  if (sacc[0] || sacc[1]) look = [(look ? look[0] : e.look?.[0] || 0) + sacc[0], (look ? look[1] : e.look?.[1] || 0) + sacc[1]];
  // hair and tail follow-through on springs, driven by head motion
  if (o.overlap !== false && idle >= 0) {
    const hh = -toonHeadY(id);
    const leanF = (tt) => { const p = poseFn(tt); return ((p.lean || 0) + (p.head || 0)) * Math.PI / 180; };
    const hxF = (tt) => xF(tt) / Math.max(0.05, sF(tt)) + hh * Math.sin(leanF(tt));
    const hyF = (tt) => yF(tt) / Math.max(0.05, sF(tt)) - (poseFn(tt).bob || 0);
    const moving = isKeys(o.x) || isKeys(o.y) || isKeys(o.pose) || typeof o.x === 'function' || typeof o.y === 'function';
    let lat = 0, vert = 0;
    if (moving) {
      const sig = (tt) => [hxF(tt), hyF(tt)];
      const lagd = follow(sig, t, { freq: o.hairFreq ?? 1.9, damping: o.hairDamping ?? 0.33, window: 1.4, dt: 1 / 180 });
      const now = sig(t);
      lat = clamp((lagd[0] - now[0]) * 0.55, -28, 28); vert = clamp((lagd[1] - now[1]) * 0.7, -24, 24);
    }
    const g = o.hair ?? 1, drift = idle * 3 * Math.sin(2 * Math.PI * 0.4 * gt + ph(4));
    if (pose.pony !== undefined || id === 'mom') pose.pony = (pose.pony || 0) + g * (lat * 1.2 + drift);
    if (id === 'lily') { pose.pigL = (pose.pigL || 0) + g * (vert + lat + drift); pose.pigR = (pose.pigR || 0) + g * (vert - lat - drift); }
    if (id === 'pickles') pose.tail = (pose.tail || 0) + g * (lat * 0.8) + idle * 7 * Math.sin(2 * Math.PI * 0.35 * gt + ph(5));
  }
  // body squash: expression accent, squash pulses, lurch, breathing
  let sx = 1 - breathe * 0.5, sy = 1 + breathe;
  const acc = fa.accent === true ? 1 : +fa.accent || 0;
  if (acc && o.accent !== false) {
    const fr = Math.floor((t - fa.changedAt) * fps + 1e-6);
    if (fr >= 0 && fr < ACCENT.length) { const a = (o.accentAmount ?? 1) * acc; sx *= 1 + (ACCENT[fr][0] - 1) * a; sy *= 1 + (ACCENT[fr][1] - 1) * a; }
  }
  if (o.squash) { const q = squashes(t, (typeof o.squash === 'function' ? o.squash(t) : o.squash) || [], o.squashOpts); sx *= q.sx; sy *= q.sy; }
  let k = 1;
  if (o.lurch) k = lurchK(t, o.lurch, fps);
  return {
    id, x, y, s, k, sx: sx * k, sy: sy * k, facing: facingOf(val(o.facing ?? 'front', t)), pose, face: e, look,
    add: stepOrVal(o.add, t), props: stepOrVal(o.props, t), talking, blink: bl, headY: y + toonHeadY(id) * s * sy * k,
  };
}

/** draw the actor. See the header for options. */
export function actor(id, o = {}, t = 0, ctx = {}) {
  const st = actorState(id, o, t, ctx);
  const ground = o.ground !== undefined ? val(o.ground, t) : null;
  const body = toon(id, {
    x: st.x, y: st.y, s: st.s, facing: st.facing, pose: st.pose, face: st.face, look: st.look || undefined,
    add: st.add || undefined, props: st.props || undefined, shadow: ground !== null ? false : o.shadow,
  });
  let out = body;
  if (Math.abs(st.sx - 1) > 1e-4 || Math.abs(st.sy - 1) > 1e-4) {
    const X = st.x, Y = st.y;
    out = `<g transform="translate(${r2(X)} ${r2(Y)}) scale(${r3(st.sx)} ${r3(st.sy)}) translate(${r2(-X)} ${r2(-Y)})">${body}</g>`;
  }
  if (ground !== null && o.shadow !== false) {
    const h = Math.max(0, ground - st.y);
    out = contactShadow(st.x, ground + 2 * st.s, 70 * st.s, 10 * st.s, { op: 0.3, h: h / Math.max(0.2, st.s) }) + out;
  }
  const op = o.opacity !== undefined ? val(o.opacity, t) : 1;
  if (op < 1) out = `<g opacity="${r3(Math.max(0, op))}">${out}</g>`;
  return out;
}
