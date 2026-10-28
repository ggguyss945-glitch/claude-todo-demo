// Small math / easing / RNG helpers shared by every module.
export const clamp = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
export const lerp = (a, b, t) => a + (b - a) * t;
export const prog = (t, a, b) => (b === a ? (t >= b ? 1 : 0) : clamp((t - a) / (b - a)));
export const smooth = (x) => { x = clamp(x); return x * x * (3 - 2 * x); };
export const easeInOut = (x) => { x = clamp(x); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
export const easeOut = (x) => { x = clamp(x); return 1 - Math.pow(1 - x, 3); };
export const easeIn = (x) => { x = clamp(x); return x * x * x; };
export const easeInOutSine = (x) => -(Math.cos(Math.PI * clamp(x)) - 1) / 2;
export const easeOutQuint = (x) => 1 - Math.pow(1 - clamp(x), 5);
export const easeInOutQuint = (x) => { x = clamp(x); return x < 0.5 ? 16 * x ** 5 : 1 - Math.pow(-2 * x + 2, 5) / 2; };

// deterministic hash -> [0,1)
export function hash(...a) {
  let h = 2166136261 >>> 0;
  for (const v of a) {
    let x = Math.floor(v * 1000003) | 0;
    h ^= x; h = Math.imul(h, 16777619) >>> 0;
    h ^= h >>> 13; h = Math.imul(h, 0x5bd1e995) >>> 0; h ^= h >>> 15;
  }
  return (h >>> 0) / 4294967296;
}

export function rng(seed) {
  let s = (seed >>> 0) || 1;
  return () => { s = (Math.imul(s ^ (s >>> 15), 0x2c1b3c6d) + 0x6d2b79f5) >>> 0; s ^= s + Math.imul(s ^ (s >>> 7), s | 61); return ((s ^ (s >>> 14)) >>> 0) / 4294967296; };
}

// smooth 1D value noise in [-1,1]
export function noise1(x, seed = 0) {
  const i = Math.floor(x), f = x - i;
  const a = hash(i, seed) * 2 - 1, b = hash(i + 1, seed) * 2 - 1;
  return lerp(a, b, smooth(f));
}

// handheld camera shake: sum of octaves
export function shake(t, seed, amp = 1) {
  return amp * (noise1(t * 0.9, seed) * 0.6 + noise1(t * 2.3, seed + 7) * 0.3 + noise1(t * 5.1, seed + 13) * 0.1);
}

// piecewise keyframes: [[t, value], ...] with easing between keys
export function keys(t, ks, ease = easeInOut) {
  if (t <= ks[0][0]) return ks[0][1];
  for (let i = 0; i < ks.length - 1; i++) {
    const [ta, va] = ks[i], [tb, vb] = ks[i + 1];
    if (t <= tb) {
      const e = (ks[i + 1][2] || ease)(prog(t, ta, tb));
      if (Array.isArray(va)) return va.map((v, j) => lerp(v, vb[j], e));
      return lerp(va, vb, e);
    }
  }
  return ks[ks.length - 1][1];
}
