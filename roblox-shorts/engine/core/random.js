// Seeded randomness and noise. Never use Math.random in episodes: every value must be a pure function of
// (seed, time) so that interleaved workers, resumed renders and stills all produce identical frames.

// 32-bit string/number hash (FNV-1a + avalanche).
export function hash32(...parts) {
  let h = 0x811c9dc5;
  for (const p of parts) {
    const s = typeof p === 'string' ? p : String(p);
    for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193); }
    h ^= 0x7f; h = Math.imul(h, 0x01000193);
  }
  h ^= h >>> 16; h = Math.imul(h, 0x85ebca6b); h ^= h >>> 13; h = Math.imul(h, 0xc2b2ae35); h ^= h >>> 16;
  return h >>> 0;
}

// Integer hash of up to 4 ints -> [0,1). Stateless; use for per-index / per-cell randomness.
export function hashFloat(a = 0, b = 0, c = 0, d = 0) {
  let h = Math.imul(a | 0, 0x27d4eb2d) ^ Math.imul(b | 0, 0x165667b1) ^ Math.imul(c | 0, 0x9e3779b1) ^ Math.imul(d | 0, 0x85ebca77);
  h ^= h >>> 15; h = Math.imul(h, 0x2c1b3c6d); h ^= h >>> 12; h = Math.imul(h, 0x297a2d39); h ^= h >>> 15;
  return (h >>> 0) / 4294967296;
}

// Seeded PRNG (sfc32). rng() -> [0,1). Extra helpers hang off the function.
export function makeRng(seed = 1) {
  let a = hash32('a', seed), b = hash32('b', seed), c = hash32('c', seed), d = hash32('d', seed);
  const rng = () => {
    a >>>= 0; b >>>= 0; c >>>= 0; d >>>= 0;
    let t = (a + b) | 0; a = b ^ (b >>> 9); b = (c + (c << 3)) | 0; c = (c << 21) | (c >>> 11);
    d = (d + 1) | 0; t = (t + d) | 0; c = (c + t) | 0;
    return (t >>> 0) / 4294967296;
  };
  for (let i = 0; i < 12; i++) rng();
  rng.range = (lo, hi) => lo + (hi - lo) * rng();
  rng.int = (lo, hi) => Math.floor(lo + (hi - lo + 1) * rng()); // inclusive
  rng.pick = (arr) => arr[Math.floor(rng() * arr.length)];
  rng.sign = () => (rng() < 0.5 ? -1 : 1);
  rng.chance = (p) => rng() < p;
  rng.gauss = () => { let u = 0, v = 0; while (u === 0) u = rng(); v = rng(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
  rng.shuffle = (arr) => { for (let i = arr.length - 1; i > 0; i--) { const j = Math.floor(rng() * (i + 1)); [arr[i], arr[j]] = [arr[j], arr[i]]; } return arr; };
  rng.fork = (label) => makeRng(hash32(seed, label));
  return rng;
}

// ---- gradient noise (seeded) ----
const _perms = new Map();
function perm(seed) {
  let p = _perms.get(seed);
  if (p) return p;
  const r = makeRng(seed); const base = new Uint8Array(256);
  for (let i = 0; i < 256; i++) base[i] = i;
  for (let i = 255; i > 0; i--) { const j = Math.floor(r() * (i + 1)); const t = base[i]; base[i] = base[j]; base[j] = t; }
  p = new Uint8Array(512); for (let i = 0; i < 512; i++) p[i] = base[i & 255];
  _perms.set(seed, p); return p;
}
const fade = (t) => t * t * t * (t * (t * 6 - 15) + 10);
const lerp = (a, b, t) => a + (b - a) * t;
function grad1(h, x) { return (h & 1 ? -1 : 1) * (1 + (h & 7)) / 8 * x; }
function grad2(h, x, y) { const g = h & 7; const u = g < 4 ? x : y, v = g < 4 ? y : x; return ((g & 1) ? -u : u) + ((g & 2) ? -2 * v : 2 * v) * 0.5; }
function grad3(h, x, y, z) { const g = h & 15; const u = g < 8 ? x : y; const v = g < 4 ? y : (g === 12 || g === 14 ? x : z); return ((g & 1) ? -u : u) + ((g & 2) ? -v : v); }

// Perlin noise, output roughly in [-1,1].
export function noise1(x, seed = 0) {
  const p = perm(seed); const X = Math.floor(x); const xf = x - X; const xi = X & 255;
  return lerp(grad1(p[xi], xf), grad1(p[xi + 1], xf - 1), fade(xf)) * 2;
}
export function noise2(x, y, seed = 0) {
  const p = perm(seed); const X = Math.floor(x), Y = Math.floor(y); const xf = x - X, yf = y - Y; const xi = X & 255, yi = Y & 255;
  const u = fade(xf), v = fade(yf);
  const aa = p[p[xi] + yi], ab = p[p[xi] + yi + 1], ba = p[p[xi + 1] + yi], bb = p[p[xi + 1] + yi + 1];
  return lerp(lerp(grad2(aa, xf, yf), grad2(ba, xf - 1, yf), u), lerp(grad2(ab, xf, yf - 1), grad2(bb, xf - 1, yf - 1), u), v);
}
export function noise3(x, y, z, seed = 0) {
  const p = perm(seed); const X = Math.floor(x), Y = Math.floor(y), Z = Math.floor(z);
  const xf = x - X, yf = y - Y, zf = z - Z; const xi = X & 255, yi = Y & 255, zi = Z & 255;
  const u = fade(xf), v = fade(yf), w = fade(zf);
  const A = p[xi] + yi, AA = p[A] + zi, AB = p[A + 1] + zi, B = p[xi + 1] + yi, BA = p[B] + zi, BB = p[B + 1] + zi;
  return lerp(
    lerp(lerp(grad3(p[AA], xf, yf, zf), grad3(p[BA], xf - 1, yf, zf), u), lerp(grad3(p[AB], xf, yf - 1, zf), grad3(p[BB], xf - 1, yf - 1, zf), u), v),
    lerp(lerp(grad3(p[AA + 1], xf, yf, zf - 1), grad3(p[BA + 1], xf - 1, yf, zf - 1), u), lerp(grad3(p[AB + 1], xf, yf - 1, zf - 1), grad3(p[BB + 1], xf - 1, yf - 1, zf - 1), u), v), w);
}
// Fractal sums. octaves, lacunarity 2, gain 0.5 by default; normalised to roughly [-1,1].
export function fbm1(x, seed = 0, oct = 4, lac = 2, gain = 0.5) { let s = 0, a = 1, n = 0, f = 1; for (let i = 0; i < oct; i++) { s += a * noise1(x * f, seed + i * 31); n += a; a *= gain; f *= lac; } return s / n; }
export function fbm2(x, y, seed = 0, oct = 4, lac = 2, gain = 0.5) { let s = 0, a = 1, n = 0, f = 1; for (let i = 0; i < oct; i++) { s += a * noise2(x * f, y * f, seed + i * 31); n += a; a *= gain; f *= lac; } return s / n; }
export function fbm3(x, y, z, seed = 0, oct = 4, lac = 2, gain = 0.5) { let s = 0, a = 1, n = 0, f = 1; for (let i = 0; i < oct; i++) { s += a * noise3(x * f, y * f, z * f, seed + i * 31); n += a; a *= gain; f *= lac; } return s / n; }

// Tileable 2D noise with period (px, py) in lattice units (for textures).
export function tileNoise2(x, y, px, py, seed = 0) {
  const p = perm(seed); const X = Math.floor(x), Y = Math.floor(y); const xf = x - X, yf = y - Y;
  const x0 = ((X % px) + px) % px, x1 = (x0 + 1) % px, y0 = ((Y % py) + py) % py, y1 = (y0 + 1) % py;
  const h = (i, j) => p[(p[i & 255] + j) & 511];
  const u = fade(xf), v = fade(yf);
  return lerp(lerp(grad2(h(x0, y0), xf, yf), grad2(h(x1, y0), xf - 1, yf), u), lerp(grad2(h(x0, y1), xf, yf - 1), grad2(h(x1, y1), xf - 1, yf - 1), u), v);
}
export function tileFbm2(x, y, px, py, seed = 0, oct = 4, gain = 0.5) {
  let s = 0, a = 1, n = 0, f = 1;
  for (let i = 0; i < oct; i++) { s += a * tileNoise2(x * f, y * f, px * f, py * f, seed + i * 31); n += a; a *= gain; f *= 2; }
  return s / n;
}

// Install a seeded Math.random so stray library calls stay deterministic (reset per shot build).
let _orig = null;
export function seedMathRandom(seed) {
  if (!_orig) _orig = Math.random;
  const r = makeRng(seed); Math.random = r;
}
