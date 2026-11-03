// motion.js — the time-math kit of engine v3. Every function is a pure function of its arguments (no Math.random,
// no Date, no hidden state), so any frame can be rendered alone, in any order, on any worker, and comes out identical.
//
//   ease.*            easings on u in 0..1 (in/out/inOut x quad/cubic/quart/quint/expo/sine/back/elastic, plus outBackS(s))
//   clamp/lerp/seg    basics; seg(t, a, b) = progress of t through [a, b], clamped to 0..1
//   track(keys)       keyframe track: [[t, value, ease?], ...] -> fn(t). Values: number | number[] | '#hex' | object of those
//   snaps(keys, o)    pose-to-pose: at each key time start moving to that value over o.dur (default 6 frames), then hold
//   step(keys)        hold/step track: the value of the last key <= t (strings, presets, booleans)
//   spring(t, f, z)   unit step response of a damped spring (0 -> 1 with overshoot), f in Hz, z = damping ratio
//   follow(fn, t, o)  spring-lagged copy of a signal fn(t) (stateless: re-simulates a short window ending at t)
//   noise1d/noise2d   seeded smooth value noise in -1..1
//   pop / popKw       UI and caption pop curves (0.6 -> 1.05 -> 1 in 3 frames; keyword 0.85 -> 1.16 -> 1 in 6 frames)
//   squash(t, o)      damped squash-and-stretch pulse -> {sx, sy} (volume preserving)
//   shake(t, events)  trauma shake: sum of A * exp(-dt/decay) * noise -> {x, y, r}
//   hash(str)         32-bit FNV-1a, for seeds derived from names

export const FPS = 60;
export const clamp = (v, a = 0, b = 1) => (v < a ? a : v > b ? b : v);
export const lerp = (a, b, u) => a + (b - a) * u;
export const seg = (t, a, b) => (b === a ? (t >= b ? 1 : 0) : clamp((t - a) / (b - a)));
export const invLerp = (a, b, v) => (b === a ? 0 : (v - a) / (b - a));
export const remap = (v, a, b, c, d) => lerp(c, d, clamp(invLerp(a, b, v)));
export const frames = (n, fps = FPS) => n / fps;
export const round = (n, k = 1000) => Math.round(n * k) / k;

export function hash(str) {
  let h = 2166136261 >>> 0;
  const s = String(str);
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
  return h >>> 0;
}
/** mulberry32 seeded PRNG -> () => 0..1 */
export function rng(seed) {
  let a = (typeof seed === 'string' ? hash(seed) : seed >>> 0) || 1;
  return () => {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
/** one stateless random number in 0..1 for an integer lattice point (seed, i, j) */
export function rand(seed, i = 0, j = 0) {
  let h = (Math.imul(seed | 0, 0x27d4eb2d) ^ Math.imul(i | 0, 0x165667b1) ^ Math.imul(j | 0, 0x9E3779B1)) >>> 0;
  h = Math.imul(h ^ (h >>> 15), 0x85ebca6b) >>> 0;
  h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35) >>> 0;
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

// ---------- easings ----------
const PI = Math.PI;
const backIn = (u, s = 1.70158) => u * u * ((s + 1) * u - s);
const backOut = (u, s = 1.70158) => 1 + (s + 1) * (u - 1) ** 3 + s * (u - 1) ** 2;
export const ease = {
  linear: (u) => u,
  inQuad: (u) => u * u, outQuad: (u) => 1 - (1 - u) ** 2, inOutQuad: (u) => (u < 0.5 ? 2 * u * u : 1 - (-2 * u + 2) ** 2 / 2),
  inCubic: (u) => u ** 3, outCubic: (u) => 1 - (1 - u) ** 3, inOutCubic: (u) => (u < 0.5 ? 4 * u ** 3 : 1 - (-2 * u + 2) ** 3 / 2),
  inQuart: (u) => u ** 4, outQuart: (u) => 1 - (1 - u) ** 4, inOutQuart: (u) => (u < 0.5 ? 8 * u ** 4 : 1 - (-2 * u + 2) ** 4 / 2),
  inQuint: (u) => u ** 5, outQuint: (u) => 1 - (1 - u) ** 5, inOutQuint: (u) => (u < 0.5 ? 16 * u ** 5 : 1 - (-2 * u + 2) ** 5 / 2),
  inExpo: (u) => (u <= 0 ? 0 : 2 ** (10 * u - 10)),
  outExpo: (u) => (u >= 1 ? 1 : 1 - 2 ** (-10 * u)),
  inOutExpo: (u) => (u <= 0 ? 0 : u >= 1 ? 1 : u < 0.5 ? 2 ** (20 * u - 10) / 2 : (2 - 2 ** (-20 * u + 10)) / 2),
  inSine: (u) => 1 - Math.cos((u * PI) / 2), outSine: (u) => Math.sin((u * PI) / 2), inOutSine: (u) => -(Math.cos(PI * u) - 1) / 2,
  inBack: (u) => backIn(u), outBack: (u) => backOut(u), outBackBig: (u) => backOut(u, 2.6),
  inOutBack: (u) => { const s = 1.70158 * 1.525; return u < 0.5 ? ((2 * u) ** 2 * ((s + 1) * 2 * u - s)) / 2 : ((2 * u - 2) ** 2 * ((s + 1) * (u * 2 - 2) + s) + 2) / 2; },
  outElastic: (u) => (u <= 0 ? 0 : u >= 1 ? 1 : 2 ** (-10 * u) * Math.sin((u * 10 - 0.75) * ((2 * PI) / 3)) + 1),
  inElastic: (u) => (u <= 0 ? 0 : u >= 1 ? 1 : -(2 ** (10 * u - 10)) * Math.sin((u * 10 - 10.75) * ((2 * PI) / 3))),
  outBounce: (u) => {
    const n = 7.5625, d = 2.75;
    if (u < 1 / d) return n * u * u;
    if (u < 2 / d) return n * (u -= 1.5 / d) * u + 0.75;
    if (u < 2.5 / d) return n * (u -= 2.25 / d) * u + 0.9375;
    return n * (u -= 2.625 / d) * u + 0.984375;
  },
  // anticipation: dips back ~10% before travelling (wind-up), lands without overshoot
  anticipate: (u) => (u < 0.3 ? -0.1 * ease.outSine(u / 0.3) : -0.1 + 1.1 * ease.outCubic((u - 0.3) / 0.7)),
  // hold-then-jump (for stepped / "on twos" looks): use step tracks instead where possible
  hold: (u) => (u >= 1 ? 1 : 0),
  snap: (u) => (u > 0 ? 1 : 0),
};
/** custom back overshoot amount: outBackS(2.2)(u) */
export const outBackS = (s) => (u) => backOut(u, s);
/** resolve an easing given by name, function or undefined (-> fallback) */
export function easeFn(e, fallback = 'inOutSine') {
  if (typeof e === 'function') return e;
  return ease[e] || ease[fallback] || ease.linear;
}

// ---------- colours ----------
const hexRgb = (h) => {
  h = h.replace('#', ''); if (h.length === 3) h = h.split('').map((c) => c + c).join('');
  const n = parseInt(h.slice(0, 6), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
};
const rgbHex = (c) => '#' + c.map((v) => Math.round(clamp(v, 0, 255)).toString(16).padStart(2, '0')).join('').toUpperCase();
const lin = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
const gam = (v) => 255 * (v <= 0.0031308 ? 12.92 * v : 1.055 * v ** (1 / 2.4) - 0.055);
/** colour mix in linear light (no muddy midpoints) */
export function mixHex(a, b, u) {
  const A = hexRgb(a).map(lin), B = hexRgb(b).map(lin);
  return rgbHex(A.map((v, i) => gam(v + (B[i] - v) * u)));
}

// ---------- generic interpolation ----------
const isHex = (v) => typeof v === 'string' && /^#[0-9a-fA-F]{3,8}$/.test(v);
export function mixValue(a, b, u) {
  if (typeof a === 'number' && typeof b === 'number') return a + (b - a) * u;
  if (isHex(a) && isHex(b)) return u <= 0 ? a : u >= 1 ? b : mixHex(a, b, u);
  if (Array.isArray(a) && Array.isArray(b)) return a.map((v, i) => mixValue(v, b[i] ?? v, u));
  if (a && b && typeof a === 'object' && typeof b === 'object') {
    const out = { ...a };
    for (const k of Object.keys(b)) out[k] = k in a ? mixValue(a[k], b[k], u) : b[k];
    return out;
  }
  return u < 1 ? a : b;    // strings, booleans: step at the end of the segment
}

/** keyframe track. keys: [[t, value, ease?], ...] sorted by t; ease on key i shapes the segment that ARRIVES at key i.
 *  Values are numbers, arrays, hex colours or plain objects of those (object keys merge forward: a key may give only
 *  some fields, the rest carry over from the previous key). Before the first key -> first value, after the last -> last.
 *  o.ease: default easing ('inOutSine'); o.log: interpolate log(value) (use for zoom). Returns fn(t). */
export function track(keys, o = {}) {
  if (!Array.isArray(keys) || !keys.length) return () => o.default;
  const ks = keys.map((k) => (Array.isArray(k) ? k : [k.t, k.v, k.ease]));
  // carry object fields forward so every key is complete
  for (let i = 1; i < ks.length; i++) {
    const p = ks[i - 1][1], c = ks[i][1];
    if (p && c && typeof p === 'object' && !Array.isArray(p) && typeof c === 'object' && !Array.isArray(c)) ks[i] = [ks[i][0], { ...p, ...c }, ks[i][2]];
  }
  const def = o.ease || 'inOutSine', LOG = !!o.log;
  const enc = (v) => (LOG && typeof v === 'number' ? Math.log(Math.max(1e-6, v)) : v);
  const dec = (v) => (LOG && typeof v === 'number' ? Math.exp(v) : v);
  return (t) => {
    if (t <= ks[0][0]) return ks[0][1];
    const n = ks.length;
    if (t >= ks[n - 1][0]) return ks[n - 1][1];
    let lo = 0, hi = n - 1;
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (ks[m][0] <= t) lo = m; else hi = m; }
    const a = ks[lo], b = ks[hi];
    const u = easeFn(b[2], def)((t - a[0]) / (b[0] - a[0] || 1));
    return dec(mixValue(enc(a[1]), enc(b[1]), u));
  };
}
/** evaluate a value that may be a constant, a function of t, or a keyframe list */
export function isKeys(v) { return Array.isArray(v) && v.length > 0 && Array.isArray(v[0]) && typeof v[0][0] === 'number' && v[0].length >= 2; }
export function val(v, t, o) {
  if (typeof v === 'function') return v(t);
  if (isKeys(v)) return track(v, o)(t);
  return v;
}

/** pose-to-pose track: keys [[t, value, ease?, dur?], ...]. The value holds until a key's time, then moves to the key's
 *  value over dur (default o.dur = 6 frames) with ease (default o.ease = 'outBack'), then holds. Object values merge
 *  forward (a key may set only armR). Before the first key -> o.from (or the first value). */
export function snaps(keys, o = {}) {
  const dur0 = o.dur ?? 6 / FPS, e0 = o.ease || 'outBack';
  const ks = (keys || []).map((k) => (Array.isArray(k) ? k : [k.t, k.v, k.ease, k.dur]));
  if (!ks.length) return () => o.from;
  const full = [];
  let prev = o.from !== undefined ? o.from : ks[0][1];
  for (const [t, v, e, d] of ks) {
    const merged = prev && v && typeof prev === 'object' && !Array.isArray(prev) && typeof v === 'object' && !Array.isArray(v) ? { ...prev, ...v } : v;
    full.push({ t, from: prev, to: merged, e: easeFn(e, e0), d: d ?? dur0 });
    prev = merged;
  }
  return (t) => {
    let i = -1;
    for (let k = 0; k < full.length; k++) if (full[k].t <= t) i = k; else break;
    if (i < 0) return full[0].from;
    const K = full[i];
    // a key that starts before the previous move ended blends from where that move was at K.t
    let from = K.from;
    if (i > 0) { const P = full[i - 1]; if (K.t < P.t + P.d) from = mixValue(P.from, P.to, P.e(clamp((K.t - P.t) / P.d))); }
    return mixValue(from, K.to, K.e(clamp((t - K.t) / K.d)));
  };
}

/** step / hold track: [[t, value], ...] -> value of the last key with key.t <= t (before the first: o.before ?? first). */
export function step(keys, o = {}) {
  const ks = (keys || []).map((k) => (Array.isArray(k) ? k : [k.t, k.v]));
  return (t) => {
    let v = o.before !== undefined ? o.before : ks.length ? ks[0][1] : undefined;
    for (const k of ks) { if (k[0] <= t) v = k[1]; else break; }
    return v;
  };
}
/** index and time of the last step key <= t (for "something changed at time X" accents) */
export function lastKey(keys, t) {
  let idx = -1;
  for (let i = 0; i < keys.length; i++) { if (keys[i][0] <= t) idx = i; else break; }
  return idx < 0 ? { i: -1, t: -Infinity, v: undefined } : { i: idx, t: keys[idx][0], v: keys[idx][1] };
}

// ---------- springs ----------
/** unit step response of a damped harmonic oscillator, released at t = 0: 0 -> 1 (overshoot when damping < 1).
 *  freq in Hz (natural), damping ratio z. t < 0 -> 0. */
export function spring(t, freq = 3, z = 0.4) {
  if (t <= 0) return 0;
  const w = 2 * PI * freq;
  if (z < 1) {
    const wd = w * Math.sqrt(1 - z * z);
    return 1 - Math.exp(-z * w * t) * (Math.cos(wd * t) + ((z * w) / wd) * Math.sin(wd * t));
  }
  return 1 - Math.exp(-w * t) * (1 + w * t);       // critically damped
}
/** damped impulse (0 -> peak -> wobble -> 0), handy for recoils and settles; peak normalised to ~1 */
export function wobble(t, freq = 3, z = 0.35) {
  if (t <= 0) return 0;
  const w = 2 * PI * freq, wd = w * Math.sqrt(Math.max(1e-4, 1 - z * z));
  return Math.exp(-z * w * t) * Math.sin(wd * t);
}
/** spring-lagged copy of a signal: integrates x'' = w^2 (fn(t) - x) - 2 z w x' over [t - window, t] from rest at
 *  fn(t - window). Stateless and deterministic; window >= 4/(z w) makes the start-up error vanish (~1%).
 *  fn may return a number or an array of numbers. o: {freq Hz = 2, damping = 0.35, window s, dt = 1/240} */
export function follow(fn, t, o = {}) {
  const f = o.freq ?? 2, z = o.damping ?? 0.35, dt = o.dt ?? 1 / 240;
  const w = 2 * PI * f, win = o.window ?? Math.min(2, 4.6 / (z * w));
  const n = Math.max(1, Math.ceil(win / dt));
  const t0 = t - n * dt;
  const v0 = fn(t0);
  if (typeof v0 === 'number') {
    let x = v0, v = 0;
    for (let i = 1; i <= n; i++) {
      const target = fn(t0 + i * dt);
      v += (w * w * (target - x) - 2 * z * w * v) * dt;     // semi-implicit Euler
      x += v * dt;
    }
    return x;
  }
  const x = v0.slice(), v = v0.map(() => 0);
  for (let i = 1; i <= n; i++) {
    const target = fn(t0 + i * dt);
    for (let k = 0; k < x.length; k++) { v[k] += (w * w * (target[k] - x[k]) - 2 * z * w * v[k]) * dt; x[k] += v[k] * dt; }
  }
  return x;
}

// ---------- noise ----------
const fade = (u) => u * u * u * (u * (u * 6 - 15) + 10);
/** smooth value noise, -1..1, period-free; x in "cycles" (multiply seconds by Hz) */
export function noise1d(x, seed = 0) {
  const i = Math.floor(x), u = fade(x - i);
  return lerp(rand(seed, i) * 2 - 1, rand(seed, i + 1) * 2 - 1, u);
}
/** fractal noise: octaves of noise1d, normalised to about -1..1 */
export function fbm1d(x, seed = 0, oct = 3) {
  let s = 0, a = 1, n = 0;
  for (let k = 0; k < oct; k++) { s += a * noise1d(x * 2 ** k, seed + k * 101); n += a; a *= 0.5; }
  return s / n;
}
export function noise2d(x, y, seed = 0) {
  const i = Math.floor(x), j = Math.floor(y), u = fade(x - i), v = fade(y - j);
  const a = rand(seed, i, j), b = rand(seed, i + 1, j), c = rand(seed, i, j + 1), d = rand(seed, i + 1, j + 1);
  return lerp(lerp(a, b, u), lerp(c, d, u), v) * 2 - 1;
}
/** per-frame white jitter in -1..1 (changes every frame, deterministic): nervous tremble, scream shake */
export function jitter(t, seed = 0, fps = FPS) { return rand(seed, Math.round(t * fps)) * 2 - 1; }

// ---------- pops ----------
/** standard pop: 0.6 -> 1.05 -> 1 over n frames (default 3) starting at t0. Returns scale (0 before t0 if o.hide). */
export function pop(t, t0 = 0, o = {}) {
  const n = o.frames ?? 3, fps = o.fps ?? FPS, a = o.from ?? 0.6, peak = o.peak ?? 1.05;
  const u = (t - t0) * fps / n;
  if (u < 0) return o.hide ? 0 : a;
  if (u >= 1) return 1;
  const k = 0.62;
  return u < k ? lerp(a, peak, ease.outCubic(u / k)) : lerp(peak, 1, ease.inOutSine((u - k) / (1 - k)));
}
/** keyword pop: 0.85 -> 1.16 -> 1 over 6 frames */
export const popKw = (t, t0 = 0, o = {}) => pop(t, t0, { frames: 6, from: 0.85, peak: 1.16, ...o });
/** big UI pop (toasts, cards): 0.35 -> 1.12 -> 0.97 -> 1 over n frames (default 8) */
export function popBig(t, t0 = 0, o = {}) {
  const n = o.frames ?? 8, u = (t - t0) * (o.fps ?? FPS) / n;
  if (u < 0) return o.hide ? 0 : 0.35;
  if (u >= 1) return 1;
  if (u < 0.45) return lerp(0.35, 1.12, ease.outCubic(u / 0.45));
  if (u < 0.72) return lerp(1.12, 0.97, ease.inOutSine((u - 0.45) / 0.27));
  return lerp(0.97, 1, ease.inOutSine((u - 0.72) / 0.28));
}

// ---------- squash & stretch ----------
/** damped squash pulse released at t0: amount > 0 squashes (wider, shorter), < 0 stretches. Volume preserving.
 *  o: {freq = 4 Hz, damping = 0.45}. Returns {sx, sy}. */
export function squash(t, t0, amount = 0.1, o = {}) {
  const d = wobble(t - t0, o.freq ?? 4, o.damping ?? 0.45) * amount;
  const sy = 1 - d;
  return { sx: 1 / Math.sqrt(Math.max(0.2, sy)), sy };
}
/** stretch along a velocity: k = speed factor (0..1) -> {sx, sy} stretched along the motion axis (vertical) */
export function stretch(k, max = 0.08) { const s = 1 + clamp(k) * max; return { sx: 1 / Math.sqrt(s), sy: s }; }
/** combine squash pulses from a list of times: [[t, amount], ...] */
export function squashes(t, list = [], o = {}) {
  let sx = 1, sy = 1;
  for (const [t0, a] of list) { if (t < t0 || t > t0 + 1.2) continue; const q = squash(t, t0, a, o); sx *= q.sx; sy *= q.sy; }
  return { sx, sy };
}

// ---------- shake ----------
/** trauma shake. events: [{t, amp = 22 px, decay = 0.08 s, freq = 28 Hz, rot = 0 deg, seed}] -> {x, y, r}.
 *  Each event: A * exp(-(t - t0)/decay) * noise(freq * (t - t0)); dies after ~6 decays. */
export function shake(t, events = [], seed = 0) {
  let x = 0, y = 0, r = 0;
  for (let i = 0; i < events.length; i++) {
    const e = events[i], t0 = e.t ?? 0, dt = t - t0, dec = e.decay ?? 0.08;
    if (dt < 0 || dt > dec * 7) continue;
    const env = (e.amp ?? 22) * Math.exp(-dt / dec), f = e.freq ?? 28, s = (e.seed ?? seed) + i * 977;
    x += env * noise1d(dt * f, s + 1); y += env * noise1d(dt * f, s + 2) * (e.yk ?? 0.8);
    r += (e.rot ?? 0) * Math.exp(-dt / dec) * noise1d(dt * f, s + 3);
  }
  return { x, y, r };
}

// ---------- misc ----------
/** time remap for "lag"/stepped motion: holds of n frames (t - t mod hold) */
export const stepTime = (t, hold = 2 / FPS) => t - (((t % hold) + hold) % hold);
/** ping-pong 0..1..0 over a period */
export const pingpong = (t, period = 1) => { const u = (((t / period) % 1) + 1) % 1; return u < 0.5 ? u * 2 : 2 - u * 2; };
/** smooth sine oscillation with phase from a seed: osc(t, Hz, seed) in -1..1 */
export const osc = (t, hz = 1, seed = 0) => Math.sin(2 * PI * (hz * t + rand(seed, 7)));
/** bell(t, a, b, e): 0 outside [a, b], 1 in the middle, eased edges of length e */
export function bell(t, a, b, e = 0.1, fn = ease.inOutSine) {
  if (t <= a || t >= b) return 0;
  return Math.min(fn(clamp((t - a) / e)), fn(clamp((b - t) / e)));
}
