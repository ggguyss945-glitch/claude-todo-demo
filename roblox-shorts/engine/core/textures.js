// Procedural, tileable, seeded textures (no downloaded assets). Every generator returns a bundle
// { map, normalMap, roughnessMap, height } of THREE.DataTextures (map in sRGB, others linear), cached by params and
// marked persistent so shot changes never regenerate or dispose them.
//   const t = tex.woodPlanks({ color: '#9f3305', planks: 6, seed: 2, repeat: [3, 3] });
//   new THREE.MeshStandardMaterial({ ...t.mat, roughness: 0.5 })   // t.mat = { map, normalMap, roughnessMap, normalScale }
// Sizes are powers of two; all patterns wrap seamlessly.
import * as THREE from 'three';
import { makeRng, hash32 } from './random.js';

let ANISO = 4;
export const setAnisotropy = (n) => (ANISO = n);
const cache = new Map();

// ---------------- low-level helpers ----------------
const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
const smooth = (t) => t * t * (3 - 2 * t);
export function hexRgb(h) { const c = new THREE.Color(); c.setStyle(h, THREE.NoColorSpace); return [c.r, c.g, c.b]; }
// Tileable value noise, `cells` lattice cells across the texture. Returns Float32Array(size*size) in [0,1].
export function valueNoise(size, cells, seed) {
  const r = makeRng(hash32('vn', seed, cells)); const L = new Float32Array(cells * cells); for (let i = 0; i < L.length; i++) L[i] = r();
  const out = new Float32Array(size * size); const s = cells / size;
  for (let y = 0; y < size; y++) {
    const fy = y * s, iy = Math.floor(fy), ty = smooth(fy - iy), y0 = (iy % cells) * cells, y1 = ((iy + 1) % cells) * cells;
    for (let x = 0; x < size; x++) {
      const fx = x * s, ix = Math.floor(fx), tx = smooth(fx - ix), x0 = ix % cells, x1 = (ix + 1) % cells;
      const a = L[y0 + x0], b = L[y0 + x1], c = L[y1 + x0], d = L[y1 + x1];
      out[y * size + x] = a + (b - a) * tx + (c - a + (d - c - b + a) * tx) * ty;
    }
  }
  return out;
}
// Tileable fBm in [0,1]. cells = lattice of the first octave.
export function fbm(size, cells, octaves = 4, seed = 0, gain = 0.5) {
  const out = new Float32Array(size * size); let amp = 1, norm = 0, c = cells;
  for (let o = 0; o < octaves && c <= size; o++) { const n = valueNoise(size, c, seed + o * 101); for (let i = 0; i < out.length; i++) out[i] += n[i] * amp; norm += amp; amp *= gain; c *= 2; }
  for (let i = 0; i < out.length; i++) out[i] /= norm;
  return out;
}
// Anisotropic tileable noise (cx cells across, cy cells down), for wood grain / streaks.
export function stretchNoise(size, cx, cy, seed) {
  const r = makeRng(hash32('sn', seed, cx, cy)); const L = new Float32Array(cx * cy); for (let i = 0; i < L.length; i++) L[i] = r();
  const out = new Float32Array(size * size);
  for (let y = 0; y < size; y++) {
    const fy = (y * cy) / size, iy = Math.floor(fy), ty = smooth(fy - iy), y0 = (iy % cy) * cx, y1 = ((iy + 1) % cy) * cx;
    for (let x = 0; x < size; x++) {
      const fx = (x * cx) / size, ix = Math.floor(fx), tx = smooth(fx - ix), x0 = ix % cx, x1 = (ix + 1) % cx;
      const a = L[y0 + x0], b = L[y0 + x1], c = L[y1 + x0], d = L[y1 + x1];
      out[y * size + x] = a + (b - a) * tx + (c - a + (d - c - b + a) * tx) * ty;
    }
  }
  return out;
}
// Normal map (tangent space, OpenGL / three.js convention) from a wrapped height field.
export function normalFromHeight(h, size, strength = 2) {
  const out = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y++) {
    const ym = ((y - 1 + size) % size) * size, yp = ((y + 1) % size) * size, yc = y * size;
    for (let x = 0; x < size; x++) {
      const xm = (x - 1 + size) % size, xp = (x + 1) % size;
      const dx = (h[yc + xp] - h[yc + xm]) * 0.5 * strength + (h[ym + xp] - h[ym + xm] + h[yp + xp] - h[yp + xm]) * 0.25 * strength;
      const dy = (h[yp + x] - h[ym + x]) * 0.5 * strength + (h[yp + xm] - h[ym + xm] + h[yp + xp] - h[ym + xp]) * 0.25 * strength;
      let nx = -dx, ny = -dy, nz = 1; const l = Math.hypot(nx, ny, nz); nx /= l; ny /= l; nz /= l;
      const i = (yc + x) * 4; out[i] = (nx * 0.5 + 0.5) * 255; out[i + 1] = (ny * 0.5 + 0.5) * 255; out[i + 2] = (nz * 0.5 + 0.5) * 255; out[i + 3] = 255;
    }
  }
  return out;
}
function dataTex(data, size, srgb) {
  const t = new THREE.DataTexture(data, size, size, THREE.RGBAFormat, THREE.UnsignedByteType);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearMipmapLinearFilter; t.generateMipmaps = true;
  t.anisotropy = ANISO; t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace; t.needsUpdate = true; t.userData.persistent = true;
  return t;
}
// Pack a float RGB buffer (0..1, length size*size*3) into an sRGB texture.
function rgbTex(rgb, size) { const d = new Uint8Array(size * size * 4); for (let i = 0, j = 0; i < size * size; i++, j += 3) { d[i * 4] = clamp01(rgb[j]) * 255; d[i * 4 + 1] = clamp01(rgb[j + 1]) * 255; d[i * 4 + 2] = clamp01(rgb[j + 2]) * 255; d[i * 4 + 3] = 255; } return dataTex(d, size, true); }
function grayTex(g, size) { const d = new Uint8Array(size * size * 4); for (let i = 0; i < size * size; i++) { const v = clamp01(g[i]) * 255; d[i * 4] = d[i * 4 + 1] = d[i * 4 + 2] = v; d[i * 4 + 3] = 255; } return dataTex(d, size, false); }

// Build (and cache) a bundle; apply repeat by cloning (clones share the GPU texture source).
function bundle(name, opts, build) {
  const { repeat, ...rest } = opts; const key = name + JSON.stringify(rest);
  let b = cache.get(key);
  if (!b) { b = build(rest); cache.set(key, b); }
  const rep = repeat ? (Array.isArray(repeat) ? repeat : [repeat, repeat]) : [1, 1];
  const out = { height: b.height, size: b.size };
  for (const k of ['map', 'normalMap', 'roughnessMap']) if (b[k]) { const t = rep[0] === 1 && rep[1] === 1 ? b[k] : b[k].clone(); t.repeat.set(rep[0], rep[1]); t.userData.persistent = true; out[k] = t; }
  out.mat = { map: out.map, normalMap: out.normalMap, roughnessMap: out.roughnessMap, normalScale: new THREE.Vector2(1, 1) };
  if (!out.roughnessMap) delete out.mat.roughnessMap;
  return out;
}
const jitter = (c, r, amt) => [c[0] * (1 + (r() - 0.5) * amt), c[1] * (1 + (r() - 0.5) * amt), c[2] * (1 + (r() - 0.5) * amt)];
// Draw a soft anti-aliased line into a float field with wrap-around.
function stroke(field, size, x0, y0, x1, y1, val, width = 1, op = 'max') {
  const len = Math.hypot(x1 - x0, y1 - y0); const n = Math.max(1, Math.ceil(len * 2));
  for (let i = 0; i <= n; i++) {
    const t = i / n, x = x0 + (x1 - x0) * t, y = y0 + (y1 - y0) * t, w = width * (1 - 0.6 * t);
    for (let dy = -Math.ceil(w); dy <= Math.ceil(w); dy++) for (let dx = -Math.ceil(w); dx <= Math.ceil(w); dx++) {
      const px = Math.floor(x + dx), py = Math.floor(y + dy); const d = Math.hypot(px + 0.5 - x, py + 0.5 - y); if (d > w + 0.5) continue;
      const a = clamp01(w + 0.5 - d); const idx = (((py % size) + size) % size) * size + (((px % size) + size) % size);
      field[idx] = op === 'max' ? Math.max(field[idx], val * a) : field[idx] + val * a;
    }
  }
}

// ---------------- generators ----------------
// Grass lawn: patchy green with thousands of short blade strokes. Roblox Grass-material feel.
export const grass = (o = {}) => bundle('grass', { size: 512, seed: 1, color: '#4f9e3b', dark: '#2f6a25', light: '#7cc25a', blades: 9000, normal: 2.5, ...o }, (p) => {
  const S = p.size, r = makeRng(p.seed); const base = hexRgb(p.color), dk = hexRgb(p.dark), lt = hexRgb(p.light);
  const patch = fbm(S, 4, 4, p.seed), mid = fbm(S, 32, 2, p.seed + 7);
  const hi = new Float32Array(S * S), lo = new Float32Array(S * S);
  const nb = Math.round(p.blades * (S * S) / (512 * 512));
  for (let i = 0; i < nb; i++) {
    const x = r() * S, y = r() * S, L = 3 + r() * 7 * (S / 512), a = -Math.PI / 2 + (r() - 0.5) * 1.2;
    stroke(r() < 0.55 ? hi : lo, S, x, y, x + Math.cos(a) * L, y + Math.sin(a) * L, 0.6 + 0.4 * r(), 0.7 * (S / 512) + 0.3);
  }
  const rgb = new Float32Array(S * S * 3), h = new Float32Array(S * S), rough = new Float32Array(S * S);
  for (let i = 0; i < S * S; i++) {
    const v = (patch[i] - 0.5) * 0.9 + (mid[i] - 0.5) * 0.4; let c = base.map((b, k) => b * (1 + v * 0.5));
    c = c.map((x, k) => x + (lt[k] - x) * hi[i] * 0.55); c = c.map((x, k) => x + (dk[k] - x) * lo[i] * 0.6);
    rgb[i * 3] = c[0]; rgb[i * 3 + 1] = c[1]; rgb[i * 3 + 2] = c[2];
    h[i] = 0.5 + hi[i] * 0.5 - lo[i] * 0.3 + (mid[i] - 0.5) * 0.3; rough[i] = 0.85 + 0.1 * patch[i];
  }
  return { size: S, height: h, map: rgbTex(rgb, S), normalMap: dataTex(normalFromHeight(h, S, p.normal), S, false), roughnessMap: grayTex(rough, S) };
});

// Wood planks (boards run along U). planks = boards across the tile; joints = end joints per board per tile.
export const woodPlanks = (o = {}) => bundle('wood', { size: 512, seed: 1, color: '#9f5a2e', variation: 0.25, planks: 5, joints: 1, gap: 0.012, gapColor: '#2a140a', grain: 1, rings: 9, gloss: 0.35, normal: 1.6, ...o }, (p) => {
  const S = p.size, r = makeRng(p.seed); const base = hexRgb(p.color), gapC = hexRgb(p.gapColor);
  const grainN = stretchNoise(S, 4, 64, p.seed), fine = stretchNoise(S, 16, 256, p.seed + 3), warp = fbm(S, 4, 3, p.seed + 5);
  const rows = p.planks, rowH = S / rows; const gapPx = Math.max(1, p.gap * S);
  const rowInfo = []; for (let k = 0; k < rows; k++) { const js = []; for (let j = 0; j < p.joints; j++) js.push(((j + r()) / p.joints) * S); rowInfo.push({ joints: js, tones: Array.from({ length: p.joints + 1 }, () => jitter(base, r, p.variation)), ph: r() * 10 }); }
  const rgb = new Float32Array(S * S * 3), h = new Float32Array(S * S), rough = new Float32Array(S * S);
  for (let y = 0; y < S; y++) {
    const k = Math.floor(y / rowH), ry = y - k * rowH, info = rowInfo[k];
    for (let x = 0; x < S; x++) {
      const i = y * S + x;
      let seg = 0, dj = 1e9; for (let j = 0; j < info.joints.length; j++) { const jx = info.joints[j]; if (x >= jx) seg = j + 1; dj = Math.min(dj, Math.abs(x - jx), S - Math.abs(x - jx)); }
      if (seg > info.joints.length - 1 && info.joints.length) seg = 0; // wrap: last segment continues the first
      const tone = info.tones[seg % info.tones.length];
      const g = Math.sin((ry / rowH + warp[i] * 0.8 + grainN[i] * 0.6 + info.ph + seg * 1.7) * p.rings * Math.PI) * 0.5 + 0.5;
      const streak = (fine[i] - 0.5) * 0.35 + (grainN[i] - 0.5) * 0.3;
      const shade = 1 + (g - 0.5) * 0.28 * p.grain + streak * p.grain;
      const edge = Math.min(ry, rowH - ry, dj); const inGap = edge < gapPx * 0.5 ? 1 : 0; const bevel = clamp01((edge - gapPx * 0.5) / (gapPx * 1.5));
      let c = tone.map((v) => v * shade * (0.85 + 0.15 * bevel));
      if (inGap) c = gapC;
      rgb[i * 3] = c[0]; rgb[i * 3 + 1] = c[1]; rgb[i * 3 + 2] = c[2];
      h[i] = inGap ? 0.35 : 0.62 + 0.3 * Math.sqrt(bevel) + (g - 0.5) * 0.06 + streak * 0.08; rough[i] = inGap ? 1 : clamp01(p.gloss + (fine[i] - 0.5) * 0.2 + (1 - g) * 0.08);
    }
  }
  return { size: S, height: h, map: rgbTex(rgb, S), normalMap: dataTex(normalFromHeight(h, S, p.normal), S, false), roughnessMap: grayTex(rough, S) };
});

// Brick, running bond. rows/cols = bricks per tile; mortar = fraction of brick height.
export const brick = (o = {}) => bundle('brick', { size: 512, seed: 1, color: '#7a3b2e', variation: 0.22, mortarColor: '#b9ad9e', rows: 8, cols: 4, mortar: 0.12, speckle: 0.25, normal: 4, ...o }, (p) => {
  const S = p.size, r = makeRng(p.seed); const base = hexRgb(p.color), mc = hexRgb(p.mortarColor);
  const bh = S / p.rows, bw = S / p.cols, m = bh * p.mortar; const tones = [];
  for (let k = 0; k < p.rows * p.cols; k++) tones.push(jitter(base, r, p.variation).map((v) => v * (0.9 + r() * 0.2)));
  const n1 = fbm(S, 16, 3, p.seed), n2 = valueNoise(S, 128, p.seed + 9), nm = fbm(S, 64, 2, p.seed + 4);
  const rgb = new Float32Array(S * S * 3), h = new Float32Array(S * S), rough = new Float32Array(S * S);
  for (let y = 0; y < S; y++) {
    const row = Math.floor(y / bh), ly = y - row * bh, off = row % 2 ? bw / 2 : 0;
    for (let x = 0; x < S; x++) {
      const i = y * S + x; const xx = (x + off) % S, col = Math.floor(xx / bw), lx = xx - col * bw;
      const ex = Math.min(lx, bw - lx), ey = Math.min(ly, bh - ly), e = Math.min(ex, ey) - m * 0.5;
      const t = tones[(row * p.cols + col) % tones.length];
      if (e < 0) { const v = 0.85 + nm[i] * 0.3; rgb[i * 3] = mc[0] * v; rgb[i * 3 + 1] = mc[1] * v; rgb[i * 3 + 2] = mc[2] * v; h[i] = 0.1 + nm[i] * 0.1; rough[i] = 0.95; continue; }
      const bev = clamp01(e / (m * 0.8)); const sp = (n2[i] - 0.5) * p.speckle, v = (0.88 + n1[i] * 0.24 + sp) * (0.8 + 0.2 * bev);
      rgb[i * 3] = t[0] * v; rgb[i * 3 + 1] = t[1] * v; rgb[i * 3 + 2] = t[2] * v;
      h[i] = 0.5 + 0.5 * Math.sqrt(bev) + (n1[i] - 0.5) * 0.15 + sp * 0.2; rough[i] = 0.8 + n2[i] * 0.15;
    }
  }
  return { size: S, height: h, map: rgbTex(rgb, S), normalMap: dataTex(normalFromHeight(h, S, p.normal), S, false), roughnessMap: grayTex(rough, S) };
});

// Plaster / stucco wall: subtle mottling plus fine bumpy micro-texture (Roblox Plaster / Fabric wallpaper).
export const plaster = (o = {}) => bundle('plaster', { size: 512, seed: 1, color: '#d8d0c4', mottle: 0.06, speckle: 0.05, bump: 1, normal: 2.5, ...o }, (p) => {
  const S = p.size; const base = hexRgb(p.color); const low = fbm(S, 4, 4, p.seed), fine = fbm(S, 64, 3, p.seed + 1), sp = valueNoise(S, 256, p.seed + 2);
  const rgb = new Float32Array(S * S * 3), h = new Float32Array(S * S), rough = new Float32Array(S * S);
  for (let i = 0; i < S * S; i++) {
    const v = 1 + (low[i] - 0.5) * 2 * p.mottle + (sp[i] - 0.5) * 2 * p.speckle;
    rgb[i * 3] = base[0] * v; rgb[i * 3 + 1] = base[1] * v; rgb[i * 3 + 2] = base[2] * v;
    h[i] = (fine[i] * 0.7 + sp[i] * 0.3) * p.bump; rough[i] = 0.85 + (fine[i] - 0.5) * 0.1;
  }
  return { size: S, height: h, map: rgbTex(rgb, S), normalMap: dataTex(normalFromHeight(h, S, p.normal), S, false), roughnessMap: grayTex(rough, S) };
});

// Woven fabric (plain weave). threads = threads per tile in each direction.
export const fabric = (o = {}) => bundle('fabric', { size: 512, seed: 1, color: '#a93298', threads: 96, contrast: 0.18, fuzz: 0.08, normal: 2, ...o }, (p) => {
  const S = p.size; const base = hexRgb(p.color); const per = S / p.threads; const low = fbm(S, 8, 3, p.seed), fz = valueNoise(S, 256, p.seed + 3), tv = stretchNoise(S, p.threads, 8, p.seed + 5), tu = stretchNoise(S, 8, p.threads, p.seed + 6);
  const rgb = new Float32Array(S * S * 3), h = new Float32Array(S * S), rough = new Float32Array(S * S);
  for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) {
    const i = y * S + x; const cx = Math.floor(x / per), cy = Math.floor(y / per); const fx = x / per - cx, fy = y / per - cy;
    const warpTop = (cx + cy) % 2 === 0; const prof = warpTop ? Math.sin(fx * Math.PI) : Math.sin(fy * Math.PI);
    const th = warpTop ? tv[i] : tu[i];
    const v = 1 + (prof - 0.6) * p.contrast + (th - 0.5) * 0.12 + (low[i] - 0.5) * 0.08 + (fz[i] - 0.5) * p.fuzz;
    rgb[i * 3] = base[0] * v; rgb[i * 3 + 1] = base[1] * v; rgb[i * 3 + 2] = base[2] * v; h[i] = prof * 0.8 + fz[i] * 0.2; rough[i] = 0.9;
  }
  return { size: S, height: h, map: rgbTex(rgb, S), normalMap: dataTex(normalFromHeight(h, S, p.normal), S, false), roughnessMap: grayTex(rough, S) };
});

// Carpet / shag: dense fibre speckle.
export const carpet = (o = {}) => bundle('carpet', { size: 512, seed: 1, color: '#e58fc2', fibre: 0.35, mottle: 0.1, normal: 3.5, ...o }, (p) => {
  const S = p.size, r = makeRng(p.seed); const base = hexRgb(p.color); const low = fbm(S, 6, 3, p.seed), mid = valueNoise(S, 128, p.seed + 1);
  const rgb = new Float32Array(S * S * 3), h = new Float32Array(S * S), rough = new Float32Array(S * S);
  for (let i = 0; i < S * S; i++) {
    const f = r(); const v = 1 + (f - 0.5) * p.fibre + (low[i] - 0.5) * 2 * p.mottle + (mid[i] - 0.5) * 0.15;
    rgb[i * 3] = base[0] * v; rgb[i * 3 + 1] = base[1] * v; rgb[i * 3 + 2] = base[2] * v; h[i] = f * 0.6 + mid[i] * 0.4; rough[i] = 1;
  }
  return { size: S, height: h, map: rgbTex(rgb, S), normalMap: dataTex(normalFromHeight(h, S, p.normal), S, false), roughnessMap: grayTex(rough, S) };
});

// Asphalt roof shingles (3-tab). rows/tabs per tile.
export const roofShingles = (o = {}) => bundle('shingles', { size: 512, seed: 1, color: '#3b3a40', variation: 0.18, rows: 8, tabs: 4, slot: 0.03, granule: 0.25, normal: 4, ...o }, (p) => {
  const S = p.size, r = makeRng(p.seed); const base = hexRgb(p.color); const rh = S / p.rows, tw = S / p.tabs; const tones = [];
  for (let k = 0; k < p.rows * p.tabs; k++) tones.push(jitter(base, r, p.variation));
  const gr = valueNoise(S, 256, p.seed + 1), low = fbm(S, 8, 3, p.seed + 2);
  const rgb = new Float32Array(S * S * 3), h = new Float32Array(S * S), rough = new Float32Array(S * S);
  for (let y = 0; y < S; y++) {
    const row = Math.floor(y / rh), ly = (y - row * rh) / rh, off = row % 2 ? tw / 2 : 0; // ly 0 = bottom edge (exposed butt), 1 = top (covered)
    for (let x = 0; x < S; x++) {
      const i = y * S + x; const xx = (x + off) % S, col = Math.floor(xx / tw), lx = (xx - col * tw) / tw;
      const slot = Math.min(lx, 1 - lx) < p.slot && ly < 0.55; const t = tones[(row * p.tabs + col) % tones.length];
      const shadow = ly < 0.08 ? 0.55 + ly / 0.08 * 0.45 : 1; const v = (0.85 + gr[i] * p.granule + (low[i] - 0.5) * 0.15) * shadow * (slot ? 0.35 : 1);
      rgb[i * 3] = t[0] * v; rgb[i * 3 + 1] = t[1] * v; rgb[i * 3 + 2] = t[2] * v;
      h[i] = slot ? 0 : 1 - ly * 0.6 + gr[i] * 0.1; rough[i] = 0.9;
    }
  }
  return { size: S, height: h, map: rgbTex(rgb, S), normalMap: dataTex(normalFromHeight(h, S, p.normal), S, false), roughnessMap: grayTex(rough, S) };
});

// Concrete / sidewalk. seams = joint lines at the tile edges (0 = none).
export const concrete = (o = {}) => bundle('concrete', { size: 512, seed: 1, color: '#9a9a96', mottle: 0.12, pores: 0.004, seams: 1, seamColor: '#5e5e5a', normal: 2, ...o }, (p) => {
  const S = p.size, r = makeRng(p.seed); const base = hexRgb(p.color), sc = hexRgb(p.seamColor); const low = fbm(S, 4, 5, p.seed), fine = valueNoise(S, 128, p.seed + 1);
  const pores = new Float32Array(S * S); const np = Math.round(S * S * p.pores);
  for (let k = 0; k < np; k++) { const x = r() * S, y = r() * S; stroke(pores, S, x, y, x + 0.01, y, 0.5 + 0.5 * r(), 0.6 + r() * 1.2); }
  const rgb = new Float32Array(S * S * 3), h = new Float32Array(S * S), rough = new Float32Array(S * S); const sw = Math.max(1, S * 0.006);
  for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) {
    const i = y * S + x; const seam = p.seams && (Math.min(x, S - 1 - x) < sw || Math.min(y, S - 1 - y) < sw);
    const v = 1 + (low[i] - 0.5) * 2 * p.mottle + (fine[i] - 0.5) * 0.1 - pores[i] * 0.35;
    const c = seam ? sc : base; rgb[i * 3] = c[0] * v; rgb[i * 3 + 1] = c[1] * v; rgb[i * 3 + 2] = c[2] * v;
    h[i] = seam ? 0 : 0.6 + fine[i] * 0.2 + low[i] * 0.2 - pores[i] * 0.4; rough[i] = 0.9 - low[i] * 0.1;
  }
  return { size: S, height: h, map: rgbTex(rgb, S), normalMap: dataTex(normalFromHeight(h, S, p.normal), S, false), roughnessMap: grayTex(rough, S) };
});

// Dirt / soil with clumps and pebbles.
export const dirt = (o = {}) => bundle('dirt', { size: 512, seed: 1, color: '#6b4a2f', dark: '#3b2717', pebble: '#8e7d68', pebbles: 260, normal: 3.5, ...o }, (p) => {
  const S = p.size, r = makeRng(p.seed); const base = hexRgb(p.color), dk = hexRgb(p.dark), pb = hexRgb(p.pebble);
  const low = fbm(S, 6, 5, p.seed), fine = valueNoise(S, 192, p.seed + 1); const peb = new Float32Array(S * S);
  const np = Math.round(p.pebbles * (S * S) / (512 * 512));
  for (let k = 0; k < np; k++) {
    const cx = r() * S, cy = r() * S, rad = (1.5 + r() * r() * 6) * (S / 512);
    for (let dy = -Math.ceil(rad); dy <= Math.ceil(rad); dy++) for (let dx = -Math.ceil(rad); dx <= Math.ceil(rad); dx++) {
      const d = Math.hypot(dx, dy) / rad; if (d > 1) continue; const idx = ((((Math.floor(cy) + dy) % S) + S) % S) * S + ((((Math.floor(cx) + dx) % S) + S) % S); peb[idx] = Math.max(peb[idx], Math.sqrt(1 - d * d));
    }
  }
  const rgb = new Float32Array(S * S * 3), h = new Float32Array(S * S), rough = new Float32Array(S * S);
  for (let i = 0; i < S * S; i++) {
    const m = clamp01((low[i] - 0.35) * 2.2); let c = [0, 1, 2].map((k) => dk[k] + (base[k] - dk[k]) * m); const v = 0.85 + fine[i] * 0.3;
    c = c.map((x, k) => x * v + (pb[k] * (0.8 + 0.4 * peb[i]) - x * v) * (peb[i] > 0 ? 0.9 : 0));
    rgb[i * 3] = c[0]; rgb[i * 3 + 1] = c[1]; rgb[i * 3 + 2] = c[2]; h[i] = low[i] * 0.5 + fine[i] * 0.2 + peb[i] * 0.6; rough[i] = peb[i] > 0 ? 0.7 : 0.97;
  }
  return { size: S, height: h, map: rgbTex(rgb, S), normalMap: dataTex(normalFromHeight(h, S, p.normal), S, false), roughnessMap: grayTex(rough, S) };
});

// Night (or any) sky, equirectangular (width = 2*height): vertical gradient stops [[elevation -1..1, '#hex'], ...],
// seeded stars (denser and brighter toward the zenith), optional nebula wisps. Use with skyDome() or as
// scene.background (texture.mapping = EquirectangularReflectionMapping is set).
export function starSky(o = {}) {
  const p = { width: 2048, seed: 1, stops: [[-1, '#000000'], [0, '#0b0c2a'], [0.35, '#05061a'], [1, '#000003']], stars: 2600, starColor: '#ffffff', twinkleTint: 0.25, nebula: 0, nebulaColors: ['#46134d', '#3a2988'], ...o };
  const key = 'sky' + JSON.stringify(p); if (cache.has(key)) return cache.get(key);
  const W = p.width, H = W / 2, r = makeRng(p.seed); const stops = p.stops.map(([e, c]) => [e, hexRgb(c)]).sort((a, b) => a[0] - b[0]);
  const rgb = new Float32Array(W * H * 3);
  const neb = p.nebula > 0 ? [fbm(H, 4, 5, p.seed + 1), fbm(H, 8, 4, p.seed + 2)] : null; const nc = p.nebulaColors.map(hexRgb);
  for (let y = 0; y < H; y++) {
    const e = (y / (H - 1)) * 2 - 1; let k = 0; while (k < stops.length - 2 && e > stops[k + 1][0]) k++;
    const [e0, c0] = stops[k], [e1, c1] = stops[Math.min(k + 1, stops.length - 1)]; const u = e1 === e0 ? 0 : smooth(clamp01((e - e0) / (e1 - e0)));
    for (let x = 0; x < W; x++) {
      const i = (y * W + x) * 3; let c = [c0[0] + (c1[0] - c0[0]) * u, c0[1] + (c1[1] - c0[1]) * u, c0[2] + (c1[2] - c0[2]) * u];
      if (neb && e > -0.1) { const j = y * H + (x % H); const a = clamp01((neb[0][j] - 0.45) * 3) * p.nebula * clamp01((e + 0.1) * 3), b = clamp01((neb[1][j] - 0.5) * 3) * p.nebula; c = c.map((v, q) => v + nc[0][q] * a + nc[1][q] * b * 0.6); }
      rgb[i] = c[0]; rgb[i + 1] = c[1]; rgb[i + 2] = c[2];
    }
  }
  const sc = hexRgb(p.starColor);
  for (let s = 0; s < p.stars; s++) {
    const e = Math.asin(r() * 2 - 1); if (e < -0.05) continue; // above the horizon only
    const y = ((e / (Math.PI / 2)) * 0.5 + 0.5) * (H - 1), x = r() * W; const b = Math.pow(r(), 3) * (0.5 + 0.5 * Math.sin(e)) + 0.12;
    const rad = 0.6 + Math.pow(r(), 6) * 1.8; const stretch = 1 / Math.max(0.15, Math.cos(e)); const tint = 1 - p.twinkleTint * r();
    for (let dy = -3; dy <= 3; dy++) for (let dx = -Math.ceil(3 * stretch); dx <= Math.ceil(3 * stretch); dx++) {
      const yy = Math.round(y) + dy; if (yy < 0 || yy >= H) continue; const xx = (((Math.round(x) + dx) % W) + W) % W;
      const d = Math.hypot(dx / stretch, dy) / rad; const a = Math.exp(-d * d * 1.5) * b; if (a < 0.003) continue;
      const i = (yy * W + xx) * 3; rgb[i] += sc[0] * a; rgb[i + 1] += sc[1] * a * tint; rgb[i + 2] += sc[2] * a;
    }
  }
  const d = new Uint8Array(W * H * 4); for (let i = 0; i < W * H; i++) { d[i * 4] = clamp01(rgb[i * 3]) * 255; d[i * 4 + 1] = clamp01(rgb[i * 3 + 1]) * 255; d[i * 4 + 2] = clamp01(rgb[i * 3 + 2]) * 255; d[i * 4 + 3] = 255; }
  const t = new THREE.DataTexture(d, W, H, THREE.RGBAFormat); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = THREE.RepeatWrapping; t.wrapT = THREE.ClampToEdgeWrapping;
  t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearMipmapLinearFilter; t.generateMipmaps = true; t.mapping = THREE.EquirectangularReflectionMapping; t.needsUpdate = true; t.userData.persistent = true;
  cache.set(key, t); return t;
}
// Big inverted sphere showing an equirect texture. fog:false keeps stars visible through scene fog.
export function skyDome(texture, { radius = 400, fog = false, intensity = 1, rotation = 0 } = {}) {
  const m = new THREE.MeshBasicMaterial({ map: texture, side: THREE.BackSide, fog, depthWrite: false, toneMapped: true, color: new THREE.Color(intensity, intensity, intensity) });
  const g = new THREE.SphereGeometry(radius, 64, 32); const mesh = new THREE.Mesh(g, m); mesh.rotation.y = rotation; mesh.renderOrder = -1000; mesh.frustumCulled = false; mesh.userData.isSky = true;
  return mesh;
}

// ---------------- small sprite textures (particles, glows) ----------------
// Soft radial glow (for halos, light pools, fake bloom cards). falloff: exponent of the gaussian-like profile.
export function radialGlow({ size = 128, falloff = 2.2, core = 0.0 } = {}) {
  const key = 'glow' + size + falloff + core; if (cache.has(key)) return cache.get(key);
  const d = new Uint8Array(size * size * 4); const c = (size - 1) / 2;
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const r = Math.hypot(x - c, y - c) / c; const a = r >= 1 ? 0 : Math.pow(1 - r, falloff) * (1 - core) + (r < 0.1 ? core : 0); const i = (y * size + x) * 4;
    d[i] = d[i + 1] = d[i + 2] = 255; d[i + 3] = clamp01(a) * 255;
  }
  const t = new THREE.DataTexture(d, size, size); t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearMipmapLinearFilter; t.generateMipmaps = true; t.needsUpdate = true; t.userData.persistent = true;
  cache.set(key, t); return t;
}
// N-point star glint (4 = twinkle cross, 6-8 = "snowflake" sparkle like the Roblox Sparkles texture).
export function sparkle({ size = 128, points = 6, sharpness = 18, core = 0.5 } = {}) {
  const key = 'spk' + size + points + sharpness + core; if (cache.has(key)) return cache.get(key);
  const d = new Uint8Array(size * size * 4); const c = (size - 1) / 2;
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const dx = (x - c) / c, dy = (y - c) / c; const r = Math.hypot(dx, dy); const a = Math.atan2(dy, dx);
    const ray = Math.pow(Math.abs(Math.cos((a * points) / 2)), sharpness) * Math.max(0, 1 - r) ** 1.5;
    const glow = Math.exp(-r * r * 30) * core + Math.exp(-r * r * 6) * 0.25 * core; const v = clamp01(ray + glow); const i = (y * size + x) * 4;
    d[i] = d[i + 1] = d[i + 2] = 255; d[i + 3] = v * 255;
  }
  const t = new THREE.DataTexture(d, size, size); t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearMipmapLinearFilter; t.generateMipmaps = true; t.needsUpdate = true; t.userData.persistent = true;
  cache.set(key, t); return t;
}

export function clearTextureCache() { for (const v of cache.values()) { if (v.isTexture) v.dispose(); else for (const k of ['map', 'normalMap', 'roughnessMap']) v[k]?.dispose(); } cache.clear(); }
