// Look-dev library: seeded noise, procedural canvas textures, geometry + material helpers.
// Units: 1 world unit = 1 Roblox stud. Everything is procedural (no external assets).
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

// ---------------------------------------------------------------- random + noise
export function rng(seed = 1) {
  let s = seed >>> 0 || 1;
  return () => { s ^= s << 13; s >>>= 0; s ^= s >> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; };
}
function hash2(x, y, seed) {
  let h = (x * 374761393 + y * 668265263 + seed * 1442695041) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177); h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
}
const fade = (t) => t * t * (3 - 2 * t);
// tileable value noise (period p in lattice cells)
export function vnoise(x, y, p = 256, seed = 0) {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
  const m = (v) => ((v % p) + p) % p;
  const a = hash2(m(xi), m(yi), seed), b = hash2(m(xi + 1), m(yi), seed);
  const c = hash2(m(xi), m(yi + 1), seed), d = hash2(m(xi + 1), m(yi + 1), seed);
  const u = fade(xf), v = fade(yf);
  return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
}
export function fbm(x, y, oct = 4, p = 256, seed = 0) {
  let s = 0, a = 0.5, f = 1, n = 0;
  for (let i = 0; i < oct; i++) { s += a * vnoise(x * f, y * f, p * f, seed + i * 17); n += a; a *= 0.5; f *= 2; }
  return s / n;
}
// 3D value noise (not tileable) for vertex displacement
export function vnoise3(x, y, z, seed = 0) {
  const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z);
  const xf = fade(x - xi), yf = fade(y - yi), zf = fade(z - zi);
  const h = (i, j, k) => hash2(xi + i + (zi + k) * 7919, yi + j, seed + (zi + k) * 31);
  const l = (a, b, t) => a + (b - a) * t;
  return l(l(l(h(0, 0, 0), h(1, 0, 0), xf), l(h(0, 1, 0), h(1, 1, 0), xf), yf),
           l(l(h(0, 0, 1), h(1, 0, 1), xf), l(h(0, 1, 1), h(1, 1, 1), xf), yf), zf);
}

// ---------------------------------------------------------------- canvas helpers
export function canvas(w, h = w) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
const hexRGB = (hex) => { const c = new THREE.Color(hex); return [c.r * 255, c.g * 255, c.b * 255]; };
// per-pixel painter: f(u,v,x,y) -> [r,g,b] or [r,g,b,a]
export function paint(w, h, f) {
  const c = canvas(w, h), g = c.getContext('2d'), id = g.createImageData(w, h), d = id.data;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const r = f(x / w, y / h, x, y), i = (y * w + x) * 4;
    d[i] = r[0]; d[i + 1] = r[1]; d[i + 2] = r[2]; d[i + 3] = r.length > 3 ? r[3] : 255;
  }
  g.putImageData(id, 0, 0); return c;
}
export function tex(c, { srgb = true, repeat = [1, 1], wrap = true, aniso = 8 } = {}) {
  const t = new THREE.CanvasTexture(c);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  if (wrap) { t.wrapS = t.wrapT = THREE.RepeatWrapping; }
  t.repeat.set(repeat[0], repeat[1]); t.anisotropy = aniso; t.needsUpdate = true;
  return t;
}
const mixc = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));

const _cache = new Map();
const cached = (key, fn) => { if (!_cache.has(key)) _cache.set(key, fn()); return _cache.get(key); };

// ---------------------------------------------------------------- material textures
// Roblox "Grass": fine noisy blades. Returns {map, bump}. One tile = 8 studs.
export function grassTextures(base = '#4f8f3a') {
  return cached('grass' + base, () => {
    const N = 512, b = hexRGB(base), dk = mixc(b, [10, 30, 10], 0.55), lt = mixc(b, [190, 230, 120], 0.25);
    const c = paint(N, N, (u, v) => { const n = fbm(u * 16, v * 16, 4, 16, 3), m = fbm(u * 64, v * 64, 2, 64, 9);
      const t = clamp(0.25 + 0.9 * n * m); return mixc(dk, lt, t); });
    const g = c.getContext('2d'), r = rng(7);
    for (let i = 0; i < 9000; i++) { // blades
      const x = r() * N, y = r() * N, l = 3 + r() * 7, a = -Math.PI / 2 + (r() - 0.5) * 1.2, s = r();
      g.strokeStyle = s < 0.5 ? `rgba(${dk.map(Math.round)},0.55)` : `rgba(${lt.map(Math.round)},0.45)`;
      g.lineWidth = 1 + r() * 1.2; g.beginPath(); g.moveTo(x, y); g.lineTo(x + Math.cos(a) * l, y + Math.sin(a) * l); g.stroke();
    }
    const bump = canvas(N); // bump from luminance of colour canvas
    const bd = c.getContext('2d').getImageData(0, 0, N, N).data, bg = bump.getContext('2d'), bi = bg.createImageData(N, N);
    for (let i = 0; i < bd.length; i += 4) { const l = (bd[i] + bd[i + 1] + bd[i + 2]) / 3; bi.data[i] = bi.data[i + 1] = bi.data[i + 2] = l; bi.data[i + 3] = 255; }
    bg.putImageData(bi, 0, 0);
    return { map: c, bump };
  });
}
// Brick with mortar. bricks: 4 per row across 1 tile, 10 rows. One tile = 8 studs.
export function brickTextures(base = '#8a3a2c', mortar = '#a59a92') {
  return cached('brick' + base, () => {
    const N = 512, rows = 12, cols = 4, bh = N / rows, bw = N / cols, mw = 4, r = rng(11);
    const b = hexRGB(base), mo = hexRGB(mortar);
    const shade = []; for (let i = 0; i < rows * cols * 2; i++) shade.push(0.78 + r() * 0.4);
    const map = paint(N, N, (u, v, x, y) => {
      const row = Math.floor(y / bh), off = (row % 2) * bw / 2, xx = (x + off) % N, col = Math.floor(xx / bw);
      const ex = xx - col * bw, ey = y - row * bh;
      const m = ex < mw || ey < mw;
      const n = fbm(u * 40, v * 40, 3, 40, 5);
      if (m) return mixc(mo, [60, 55, 55], n * 0.5);
      const s = shade[(row * cols + col) % shade.length] * (0.85 + 0.3 * n);
      return [b[0] * s, b[1] * s, b[2] * s];
    });
    const bump = paint(N, N, (u, v, x, y) => {
      const row = Math.floor(y / bh), off = (row % 2) * bw / 2, xx = (x + off) % N, col = Math.floor(xx / bw);
      const ex = xx - col * bw, ey = y - row * bh, m = ex < mw || ey < mw;
      const n = fbm(u * 60, v * 60, 3, 60, 8); const l = m ? 40 : 170 + n * 70; return [l, l, l];
    });
    return { map, bump };
  });
}
// Clapboard siding: horizontal boards, 10 per tile (tile = 8 studs).
export function sidingTextures(base = '#d8cfb8') {
  return cached('siding' + base, () => {
    const N = 512, n = 10, bh = N / n, b = hexRGB(base);
    const map = paint(N, N, (u, v, x, y) => { const e = (y % bh) / bh, g = fbm(u * 6, v * 80, 3, 6, 4);
      let s = 0.9 + 0.12 * g - (e > 0.88 ? 0.35 : 0) + e * 0.06; return [b[0] * s, b[1] * s, b[2] * s]; });
    const bump = paint(N, N, (u, v, x, y) => { const e = (y % bh) / bh; const l = 60 + 180 * e - (e > 0.9 ? 160 : 0); return [l, l, l]; });
    return { map, bump };
  });
}
export function shingleTextures(base = '#3b3540') {
  return cached('shingle' + base, () => {
    const N = 512, rows = 14, cols = 9, rh = N / rows, cw = N / cols, b = hexRGB(base), r = rng(21);
    const sh = []; for (let i = 0; i < 400; i++) sh.push(0.75 + r() * 0.45);
    const map = paint(N, N, (u, v, x, y) => { const row = Math.floor(y / rh), off = (row % 2) * cw * 0.5, xx = (x + off) % N, col = Math.floor(xx / cw);
      const e = (y % rh) / rh, ex = (xx % cw) / cw, s = sh[(row * cols + col) % 400] * (0.8 + 0.25 * fbm(u * 50, v * 50, 2, 50, 2));
      const k = (e > 0.85 ? 0.45 : 1) * (ex < 0.04 ? 0.5 : 1) * (0.85 + e * 0.25); return [b[0] * s * k, b[1] * s * k, b[2] * s * k]; });
    const bump = paint(N, N, (u, v, x, y) => { const row = Math.floor(y / rh), off = (row % 2) * cw * 0.5, xx = (x + off) % N;
      const e = (y % rh) / rh, ex = (xx % cw) / cw; const l = (e > 0.85 || ex < 0.04) ? 30 : 120 + e * 120; return [l, l, l]; });
    return { map, bump };
  });
}
// Wood: planks along u. tile = 4 studs
export function woodTextures(base = '#7a3a1c', planks = 4) {
  return cached('wood' + base + planks, () => {
    const N = 512, b = hexRGB(base), ph = N / planks, r = rng(5); const sh = []; for (let i = 0; i < 64; i++) sh.push(0.8 + r() * 0.35);
    const map = paint(N, N, (u, v, x, y) => { const p = Math.floor(y / ph), e = (y % ph) / ph;
      const g = fbm(u * 3 + p * 3.1, v * 60, 4, 3, 12 + p), ring = 0.5 + 0.5 * Math.sin(g * 30);
      let s = sh[p % 64] * (0.82 + 0.25 * ring) * (e < 0.04 || e > 0.97 ? 0.45 : 1); return [b[0] * s, b[1] * s, b[2] * s]; });
    const bump = paint(N, N, (u, v, x, y) => { const e = (y % ph) / ph, g = fbm(u * 3, v * 60, 3, 3, 12); const l = (e < 0.04 || e > 0.97) ? 20 : 140 + 80 * g; return [l, l, l]; });
    return { map, bump };
  });
}
// Concrete slabs (sidewalk). tile = 8 studs, joints every 4 studs.
export function concreteTextures(base = '#9a9aa2') {
  return cached('conc' + base, () => {
    const N = 512, b = hexRGB(base);
    const map = paint(N, N, (u, v, x, y) => { const j = (x % 256 < 3) || (y % 256 < 3); const n = fbm(u * 24, v * 24, 4, 24, 31);
      const sp = vnoise(x * 0.9, y * 0.9, 512, 4) > 0.93 ? 0.8 : 1; const s = (0.86 + 0.24 * n) * sp * (j ? 0.55 : 1); return [b[0] * s, b[1] * s, b[2] * s]; });
    const bump = paint(N, N, (u, v, x, y) => { const j = (x % 256 < 3) || (y % 256 < 3); const l = j ? 30 : 150 + 60 * fbm(u * 40, v * 40, 3, 40, 2); return [l, l, l]; });
    return { map, bump };
  });
}
export function asphaltTextures(base = '#3a3a44') {
  return cached('asph' + base, () => {
    const N = 512, b = hexRGB(base);
    const map = paint(N, N, (u, v, x, y) => { const n = fbm(u * 20, v * 20, 4, 20, 41), g = hash2(x, y, 3); const s = 0.8 + 0.3 * n + (g > 0.97 ? 0.35 : g < 0.03 ? -0.25 : 0); return [b[0] * s, b[1] * s, b[2] * s]; });
    const bump = paint(N, N, (u, v, x, y) => { const g = hash2(x, y, 3); const l = 128 + (g - 0.5) * 120; return [l, l, l]; });
    return { map, bump };
  });
}
export function soilTextures(base = '#4a2e22') {
  return cached('soil' + base, () => {
    const N = 256, b = hexRGB(base);
    const map = paint(N, N, (u, v, x, y) => { const n = fbm(u * 12, v * 12, 4, 12, 51), c = vnoise(u * 40, v * 40, 40, 3); const s = 0.6 + 0.7 * n * (0.7 + 0.5 * c); return [b[0] * s, b[1] * s, b[2] * s]; });
    const bump = paint(N, N, (u, v) => { const l = 255 * fbm(u * 30, v * 30, 3, 30, 8); return [l, l, l]; });
    return { map, bump };
  });
}
// Knit/fleece fabric: rows of small V stitches. tile = 1 face.
export function knitTextures(base = '#d4a12a', scale = 24) {
  return cached('knit' + base + scale, () => {
    const N = 256, b = hexRGB(base);
    const map = paint(N, N, (u, v, x, y) => { const cx = (u * scale) % 1, cy = (v * scale * 1.4) % 1;
      const st = 1 - Math.abs((cx < 0.5 ? cx : 1 - cx) * 2 - cy) * 1.4; const n = fbm(u * 8, v * 8, 3, 8, 6);
      const s = 0.82 + 0.16 * clamp(st) + 0.1 * n; return [b[0] * s, b[1] * s, b[2] * s]; });
    const bump = paint(N, N, (u, v) => { const cx = (u * scale) % 1, cy = (v * scale * 1.4) % 1; const st = 1 - Math.abs((cx < 0.5 ? cx : 1 - cx) * 2 - cy) * 1.4; const l = 255 * clamp(st); return [l, l, l]; });
    return { map, bump };
  });
}
// Leaves / bush foliage
export function leafTextures(base = '#2f5a2a') {
  return cached('leaf' + base, () => {
    const N = 256, b = hexRGB(base), c = paint(N, N, (u, v) => { const n = fbm(u * 10, v * 10, 4, 10, 61); const s = 0.5 + 0.9 * n; return [b[0] * s, b[1] * s, b[2] * s]; });
    const g = c.getContext('2d'), r = rng(9);
    for (let i = 0; i < 900; i++) { const x = r() * N, y = r() * N, a = r() * 6.28, s = 4 + r() * 6, l = r();
      g.fillStyle = `rgba(${mixc(b, l < 0.5 ? [0, 0, 0] : [200, 255, 160], l < 0.5 ? 0.5 : 0.25).map(Math.round)},0.7)`;
      g.beginPath(); g.ellipse(x, y, s, s * 0.45, a, 0, 6.28); g.fill(); }
    const bump = paint(N, N, (u, v) => { const l = 255 * fbm(u * 24, v * 24, 3, 24, 4); return [l, l, l]; });
    return { map: c, bump };
  });
}

// ---------------------------------------------------------------- sprites
export function glowTexture() {
  return cached('glow', () => { const N = 256, c = canvas(N), g = c.getContext('2d'), gr = g.createRadialGradient(N / 2, N / 2, 0, N / 2, N / 2, N / 2);
    gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.12, 'rgba(255,255,255,0.55)'); gr.addColorStop(0.35, 'rgba(255,255,255,0.16)');
    gr.addColorStop(0.7, 'rgba(255,255,255,0.03)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, N, N);
    return tex(c, { wrap: false }); });
}
// soft 6-to-8-point "snowflake" glint (Tooth Fairies ambient sparkle)
export function sparkleTexture(points = 6) {
  return cached('spark' + points, () => { const N = 256, c = canvas(N), g = c.getContext('2d'); g.translate(N / 2, N / 2);
    const core = g.createRadialGradient(0, 0, 0, 0, 0, N * 0.18); core.addColorStop(0, 'rgba(255,255,255,1)'); core.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = core; g.beginPath(); g.arc(0, 0, N * 0.18, 0, 6.28); g.fill();
    for (let i = 0; i < points; i++) { g.save(); g.rotate(i * Math.PI * 2 / points); const L = i % 2 ? N * 0.32 : N * 0.46;
      const gr = g.createLinearGradient(0, 0, L, 0); gr.addColorStop(0, 'rgba(255,255,255,0.95)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
      g.fillStyle = gr; g.beginPath(); g.moveTo(0, -N * 0.02); g.lineTo(L, 0); g.lineTo(0, N * 0.02); g.closePath(); g.fill(); g.restore(); }
    return tex(c, { wrap: false }); });
}
export function moonTexture() {
  return cached('moon', () => { const N = 512, R = N * 0.47;
    const c = paint(N, N, (u, v, x, y) => { const dx = (x - N / 2) / R, dy = (y - N / 2) / R, d = Math.hypot(dx, dy);
      if (d > 1) return [0, 0, 0, 0];
      const n = fbm(u * 5, v * 5, 5, 5, 77), cr = fbm(u * 14 + 3, v * 14, 3, 14, 13);
      let s = 0.78 + 0.22 * n - (cr > 0.62 ? (cr - 0.62) * 1.2 : 0) - (n < 0.4 ? 0.14 : 0); // maria
      const limb = Math.pow(1 - d * d, 0.12); s *= 0.8 + 0.2 * limb;
      const a = clamp((1 - d) * R / 1.5); return [255 * s, 250 * s, 255 * s, 255 * a]; });
    return tex(c, { wrap: false }); });
}

// ---------------------------------------------------------------- geometry helpers
// Box whose UVs are in studs/tile on every face (for tiled world materials)
export function boxUV(w, h, d, tile = 8) {
  const g = new THREE.BoxGeometry(w, h, d), uv = g.attributes.uv;
  const dims = [[d, h], [d, h], [w, d], [w, d], [w, h], [w, h]];
  for (let f = 0; f < 6; f++) for (let k = 0; k < 4; k++) { const i = f * 4 + k; uv.setXY(i, uv.getX(i) * dims[f][0] / tile, uv.getY(i) * dims[f][1] / tile); }
  return g;
}
export const rbox = (w, h, d, r = 0.08, seg = 3) => new RoundedBoxGeometry(w, h, d, seg, Math.min(r, w / 2 - 1e-3, h / 2 - 1e-3, d / 2 - 1e-3));
export { mergeGeometries };

export function mesh(geo, mat, x = 0, y = 0, z = 0, { cast = true, receive = true, parent = null, rot = null, scale = null } = {}) {
  const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = cast; m.receiveShadow = receive;
  if (rot) m.rotation.set(rot[0], rot[1], rot[2]); if (scale) (Array.isArray(scale) ? m.scale.set(...scale) : m.scale.setScalar(scale));
  if (parent) parent.add(m); return m;
}
// Standard tiled material
export function tiledMat({ map, bump, color = '#ffffff', rough = 0.85, metal = 0, bumpScale = 1.5, repeat = [1, 1], emissive = null }) {
  const m = new THREE.MeshStandardMaterial({ color, roughness: rough, metalness: metal });
  if (map) { m.map = tex(map, { repeat }); }
  if (bump) { m.bumpMap = tex(bump, { srgb: false, repeat }); m.bumpScale = bumpScale; }
  if (emissive) m.emissive = new THREE.Color(emissive);
  return m;
}
export const std = (color, rough = 0.6, metal = 0, extra = {}) => new THREE.MeshStandardMaterial({ color, roughness: rough, metalness: metal, ...extra });
export const phys = (color, opt = {}) => new THREE.MeshPhysicalMaterial({ color, roughness: 0.4, ...opt });

export function glowSprite(color, size, opacity = 1, x = 0, y = 0, z = 0, parent = null) {
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTexture(), color, transparent: true, opacity, depthWrite: false, blending: THREE.AdditiveBlending, fog: false }));
  s.scale.set(size, size, 1); s.position.set(x, y, z); s.renderOrder = 10; if (parent) parent.add(s); return s;
}
export { THREE, clamp, mixc, hexRGB };
