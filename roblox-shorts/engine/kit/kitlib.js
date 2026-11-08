// Suburb night kit: shared helpers. Units: the kit BUILDS IN STUDS (1 unit = 1 Roblox stud) inside groups scaled
// by STUD (0.32 m), so lights, fog densities, camera distances and slots stay in metres (VISUAL_BIBLE §1, §9).
//   - extra procedural textures the engine lacks (clapboard siding, asphalt, fieldstone, shutter louvres) built the
//     same way as core/textures.js (seeded, tileable, cached, persistent DataTextures);
//   - canvas decals (lit window interiors, doors, number plaques, signs), deterministic;
//   - the material library `M(key)` (Roblox-material look, every surface textured, studless);
//   - `Parts`: collects boxes/cylinders/... per material and merges them into ONE mesh per material
//     (a whole house is ~10 draw calls, which keeps SwiftShader fast).
// Everything here is cached per worker and marked persistent: shot cleanup never disposes it.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import * as TX from '../core/textures.js';
import { makeRng, hash32 } from '../core/random.js';

export { THREE, TX, makeRng, hash32, RoundedBoxGeometry };
export const STUD = 0.32;
export const deg = (d) => (d * Math.PI) / 180;
const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
const smooth = (t) => t * t * (3 - 2 * t);

// ------------------------------------------------------------------ texture plumbing (mirrors core/textures.js)
const _tc = new Map();
function persist(t) { t.userData.persistent = true; return t; }
function dataTex(data, w, h, srgb) {
  const t = new THREE.DataTexture(data, w, h, THREE.RGBAFormat, THREE.UnsignedByteType);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearMipmapLinearFilter; t.generateMipmaps = true;
  t.anisotropy = 8; t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace; t.needsUpdate = true; return persist(t);
}
function rgbTex(rgb, w, h = w) { const d = new Uint8Array(w * h * 4); for (let i = 0, j = 0; i < w * h; i++, j += 3) { d[i * 4] = clamp01(rgb[j]) * 255; d[i * 4 + 1] = clamp01(rgb[j + 1]) * 255; d[i * 4 + 2] = clamp01(rgb[j + 2]) * 255; d[i * 4 + 3] = 255; } return dataTex(d, w, h, true); }
function grayTex(g, w, h = w) { const d = new Uint8Array(w * h * 4); for (let i = 0; i < w * h; i++) { const v = clamp01(g[i]) * 255; d[i * 4] = d[i * 4 + 1] = d[i * 4 + 2] = v; d[i * 4 + 3] = 255; } return dataTex(d, w, h, false); }
function bundle(name, p, build) {
  const key = name + JSON.stringify(p); if (_tc.has(key)) return _tc.get(key);
  const b = build(p); const out = { ...b, mat: { map: b.map, normalMap: b.normalMap, roughnessMap: b.roughnessMap, normalScale: new THREE.Vector2(1, 1) } };
  if (!b.roughnessMap) delete out.mat.roughnessMap; if (!b.normalMap) delete out.mat.normalMap;
  _tc.set(key, out); return out;
}
const { hexRgb, fbm, valueNoise, stretchNoise, normalFromHeight } = TX;

// Clapboard (lap) siding: horizontal boards, a dark overlap line under each board, a light-to-dark ramp, fine grain.
// One tile = `boards` boards (default tile 6 studs, 10 boards -> 0.6-stud boards, VISUAL_BIBLE §4.2).
export const siding = (o = {}) => bundle('siding', { size: 512, seed: 1, color: '#d9cfb5', boards: 10, grain: 1, normal: 3.2, ...o }, (p) => {
  const S = p.size, r = makeRng(p.seed); const base = hexRgb(p.color); const bh = S / p.boards;
  const grainN = stretchNoise(S, 3, 160, p.seed), fine = stretchNoise(S, 12, 384, p.seed + 3), low = fbm(S, 4, 3, p.seed + 7);
  const tones = Array.from({ length: p.boards }, () => 1 + (r() - 0.5) * 0.07);
  const rgb = new Float32Array(S * S * 3), h = new Float32Array(S * S), rough = new Float32Array(S * S);
  for (let y = 0; y < S; y++) {
    const k = Math.floor(y / bh), e = (y - k * bh) / bh; // e: 0 = top of the board (under the lap above), 1 = bottom edge
    const ramp = 0.8 + 0.2 * smooth(clamp01(e * 1.6)); const lip = e > 0.9 ? 0.55 + 0.45 * clamp01((1 - e) / 0.1) : 1;
    for (let x = 0; x < S; x++) {
      const i = y * S + x; const g = (grainN[i] - 0.5) * 0.12 * p.grain + (fine[i] - 0.5) * 0.08 * p.grain + (low[i] - 0.5) * 0.06;
      const v = tones[k] * ramp * lip * (1 + g);
      rgb[i * 3] = base[0] * v; rgb[i * 3 + 1] = base[1] * v; rgb[i * 3 + 2] = base[2] * v;
      h[i] = e * 0.85 - (e > 0.92 ? 0.6 : 0) + g * 0.3; rough[i] = 0.72 + (fine[i] - 0.5) * 0.12;
    }
  }
  return { size: S, map: rgbTex(rgb, S), normalMap: dataTex(normalFromHeight(h, S, p.normal), S, S, false), roughnessMap: grayTex(rough, S) };
});

// Asphalt: dark aggregate with light/dark speckles, low-frequency wear patches and tar seams.
export const asphalt = (o = {}) => bundle('asphalt', { size: 512, seed: 1, color: '#4a4a52', speckle: 0.35, normal: 2.5, ...o }, (p) => {
  const S = p.size; const base = hexRgb(p.color); const low = fbm(S, 4, 5, p.seed), mid = fbm(S, 24, 2, p.seed + 3), sp = valueNoise(S, 256, p.seed + 5), sp2 = valueNoise(S, 192, p.seed + 9);
  const rgb = new Float32Array(S * S * 3), h = new Float32Array(S * S), rough = new Float32Array(S * S);
  for (let i = 0; i < S * S; i++) {
    const peb = sp[i] > 0.78 ? (sp[i] - 0.78) * 4 : 0, pit = sp2[i] < 0.18 ? (0.18 - sp2[i]) * 4 : 0;
    const v = 0.82 + (low[i] - 0.5) * 0.35 + (mid[i] - 0.5) * 0.12 + peb * p.speckle - pit * 0.25;
    rgb[i * 3] = base[0] * v; rgb[i * 3 + 1] = base[1] * v; rgb[i * 3 + 2] = base[2] * v * 1.02;
    h[i] = 0.5 + peb * 0.5 - pit * 0.5 + (mid[i] - 0.5) * 0.1; rough[i] = 0.92 - peb * 0.2;
  }
  return { size: S, map: rgbTex(rgb, S), normalMap: dataTex(normalFromHeight(h, S, p.normal), S, S, false), roughnessMap: grayTex(rough, S) };
});

// Fieldstone / flagstone: tileable jittered Voronoi stones with mortar joints (foundations, stepping stones, edging).
export const fieldstone = (o = {}) => bundle('fieldstone', { size: 512, seed: 1, color: '#8d857b', mortarColor: '#4f4842', cells: 5, mortar: 0.06, variation: 0.22, normal: 4, ...o }, (p) => {
  const S = p.size, r = makeRng(p.seed), N = p.cells; const base = hexRgb(p.color), mc = hexRgb(p.mortarColor);
  const pts = [], tone = [];
  for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) { pts.push([(i + 0.15 + r() * 0.7) / N, (j + 0.15 + r() * 0.7) / N]); const t = 1 + (r() - 0.5) * p.variation * 2; const hue = (r() - 0.5) * 0.08; tone.push([t * (1 + hue), t, t * (1 - hue)]); }
  const n1 = fbm(S, 16, 3, p.seed + 1), n2 = valueNoise(S, 128, p.seed + 2);
  const rgb = new Float32Array(S * S * 3), h = new Float32Array(S * S), rough = new Float32Array(S * S);
  for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) {
    const u = x / S, v = y / S, ci = Math.floor(u * N), cj = Math.floor(v * N); let d1 = 9, d2 = 9, id = 0;
    for (let dj = -1; dj <= 1; dj++) for (let di = -1; di <= 1; di++) {
      const ii = (ci + di + N) % N, jj = (cj + dj + N) % N; const q = pts[jj * N + ii];
      // wrapped neighbour: shift its feature point by a whole tile so the pattern tiles seamlessly
      const dx = u - (q[0] + Math.floor((ci + di) / N)), dy = v - (q[1] + Math.floor((cj + dj) / N));
      const d = Math.hypot(dx, dy); if (d < d1) { d2 = d1; d1 = d; id = jj * N + ii; } else if (d < d2) d2 = d;
    }
    const i = y * S + x; const edge = (d2 - d1) * N; const m = clamp01((edge - p.mortar) / 0.08);
    const t = tone[id]; const nv = 0.85 + n1[i] * 0.3 + (n2[i] - 0.5) * 0.12;
    for (let k = 0; k < 3; k++) rgb[i * 3 + k] = m > 0 ? base[k] * t[k] * nv * (0.75 + 0.25 * m) : mc[k] * (0.8 + n2[i] * 0.3);
    h[i] = m * (0.6 + 0.25 * Math.sqrt(m)) + (n1[i] - 0.5) * 0.25 * m; rough[i] = m > 0 ? 0.82 + n2[i] * 0.12 : 0.97;
  }
  return { size: S, map: rgbTex(rgb, S), normalMap: dataTex(normalFromHeight(h, S, p.normal), S, S, false), roughnessMap: grayTex(rough, S) };
});

// Shutter louvres: horizontal slats with a frame (one shutter per texture, 1 x 2.5 aspect).
export const louvre = (o = {}) => bundle('louvre', { w: 128, h: 320, seed: 1, color: '#3b4347', slats: 16, normal: 3, ...o }, (p) => {
  const W = p.w, H = p.h; const base = hexRgb(p.color); const grain = stretchNoise(Math.max(W, H), 4, 64, p.seed);
  const rgb = new Float32Array(W * H * 3), hgt = new Float32Array(W * H);
  const fr = 0.1 * W, inner = (H - 2 * fr) / p.slats;
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const i = y * W + x; const inFrame = x < fr || x > W - fr || y < fr || y > H - fr;
    let v, hh;
    if (inFrame) { v = 1.05; hh = 1; }
    else { const e = ((y - fr) % inner) / inner; v = 0.62 + 0.45 * e - (e > 0.9 ? 0.3 : 0); hh = e * 0.7; }
    v *= 1 + (grain[(y % W) * W + (x % W)] - 0.5) * 0.08;
    rgb[i * 3] = base[0] * v; rgb[i * 3 + 1] = base[1] * v; rgb[i * 3 + 2] = base[2] * v; hgt[i] = hh;
  }
  // normalFromHeight needs a square field: louvres only need the colour map (slats are painted with baked shading).
  return { size: W, map: rgbTex(rgb, W, H) };
});

// ------------------------------------------------------------------ canvas decals (deterministic, cached)
function canvasTex(key, w, h, draw, { srgb = true, wrap = false } = {}) {
  if (_tc.has(key)) return _tc.get(key);
  const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d'); draw(g, w, h);
  const t = new THREE.CanvasTexture(c); if (srgb) t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  if (wrap) t.wrapS = t.wrapT = THREE.RepeatWrapping; t.needsUpdate = true; persist(t); _tc.set(key, t); return t;
}
export const FONT = '"DejaVu Sans", "Liberation Sans", Arial, sans-serif'; // no Montserrat offline: closest bold geometric-ish sans

// Lit window interior seen through the glass: warm room gradient, a ceiling-lamp hot spot, curtains with folds at both
// sides and a hint of furniture. Used as the map of an HDR MeshBasicMaterial (colour = tint x intensity).
// tone: 'warm' (#ffd9a0 rooms), 'pink' (TF pink-lit room), 'cool' (TV-blue), 'dim'.
export function windowInteriorTex(tone = 'warm', curtain = '#c85a4a', variant = 0) {
  return canvasTex(`win:${tone}:${curtain}:${variant}`, 128, 160, (g, W, H) => {
    const T = { warm: ['#fff3dc', '#ffd9a0', '#d79a5c'], pink: ['#ffe4f2', '#f7a8d0', '#c0608f'], cool: ['#e2e8ff', '#a9b8ff', '#5d6ab8'], dim: ['#c8a070', '#9a6a40', '#5a3a22'] }[tone] || ['#fff3dc', '#ffd9a0', '#d79a5c'];
    const gr = g.createLinearGradient(0, 0, 0, H); gr.addColorStop(0, T[0]); gr.addColorStop(0.45, T[1]); gr.addColorStop(1, T[2]); g.fillStyle = gr; g.fillRect(0, 0, W, H);
    const lx = W * (0.35 + 0.3 * ((variant * 0.37) % 1)); const rg = g.createRadialGradient(lx, H * 0.18, 2, lx, H * 0.18, W * 0.7);
    rg.addColorStop(0, 'rgba(255,255,255,0.75)'); rg.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = rg; g.fillRect(0, 0, W, H);
    // furniture hint (shelf / bed head / lamp silhouette), always soft and low contrast
    g.fillStyle = 'rgba(70,35,20,0.28)';
    if (variant % 3 === 0) g.fillRect(W * 0.18, H * 0.62, W * 0.64, H * 0.4);
    else if (variant % 3 === 1) { g.fillRect(W * 0.55, H * 0.35, W * 0.3, H * 0.65); g.fillRect(W * 0.58, H * 0.42, W * 0.24, 3); g.fillRect(W * 0.58, H * 0.55, W * 0.24, 3); }
    else { g.beginPath(); g.ellipse(W * 0.32, H * 0.72, W * 0.2, H * 0.08, 0, 0, Math.PI * 2); g.fill(); g.fillRect(W * 0.3, H * 0.5, 4, H * 0.22); }
    // curtains: fabric panels with vertical folds, gathered at the sides
    const cc = new THREE.Color(curtain); const cs = (k) => `rgb(${Math.round(cc.r * 255 * k)},${Math.round(cc.g * 255 * k)},${Math.round(cc.b * 255 * k)})`;
    for (const side of [0, 1]) {
      const x0 = side ? W * 0.76 : 0, cw = W * 0.24;
      for (let x = 0; x < cw; x++) { const f = 0.78 + 0.22 * Math.sin((x / cw) * Math.PI * 5 + side); g.fillStyle = cs(f); g.fillRect(x0 + x, 0, 1, H); }
    }
    g.fillStyle = cs(0.55); g.fillRect(0, 0, W, 7); // valance
  });
}
// Faint sky reflection for dark glass (emissive map at low intensity): a diagonal sheen.
export function glassSheenTex() {
  return canvasTex('glassSheen', 64, 64, (g, W, H) => {
    g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
    const gr = g.createLinearGradient(0, 0, W, H); gr.addColorStop(0, 'rgba(120,130,200,0.0)'); gr.addColorStop(0.38, 'rgba(150,160,230,0.55)'); gr.addColorStop(0.5, 'rgba(90,100,170,0.15)'); gr.addColorStop(0.62, 'rgba(150,160,230,0.4)'); gr.addColorStop(1, 'rgba(60,60,120,0.0)');
    g.fillStyle = gr; g.fillRect(0, 0, W, H);
  });
}
// Six-panel front door (front face only; edges use the plain colour).
export function doorTex(color = '#6b1f1a') {
  return canvasTex('door:' + color, 192, 384, (g, W, H) => {
    const c = new THREE.Color(color); const col = (k) => `rgb(${Math.round(Math.min(255, c.r * 255 * k))},${Math.round(Math.min(255, c.g * 255 * k))},${Math.round(Math.min(255, c.b * 255 * k))})`;
    g.fillStyle = col(1); g.fillRect(0, 0, W, H);
    for (let y = 0; y < H; y += 2) { g.fillStyle = `rgba(0,0,0,${0.03 + 0.03 * Math.sin(y * 0.37) * Math.sin(y * 0.11)})`; g.fillRect(0, y, W, 2); }
    const panels = [[0.14, 0.06, 0.32, 0.16], [0.54, 0.06, 0.32, 0.16], [0.14, 0.28, 0.32, 0.3], [0.54, 0.28, 0.32, 0.3], [0.14, 0.66, 0.32, 0.28], [0.54, 0.66, 0.32, 0.28]];
    for (const [x, y, w, h] of panels) {
      const X = x * W, Y = y * H, PW = w * W, PH = h * H, b = 7;
      g.fillStyle = col(0.62); g.fillRect(X, Y, PW, b); g.fillRect(X, Y, b, PH);
      g.fillStyle = col(1.28); g.fillRect(X, Y + PH - b, PW, b); g.fillRect(X + PW - b, Y, b, PH);
      g.fillStyle = col(0.9); g.fillRect(X + b, Y + b, PW - 2 * b, PH - 2 * b);
    }
  });
}
// House-number plaque: white bold digits on a dark plaque with a light border (TF "16").
export function plaqueTex(text = '16', bg = '#1d3a2c') {
  return canvasTex('plaque:' + text + bg, 128, 96, (g, W, H) => {
    g.fillStyle = bg; g.fillRect(0, 0, W, H); g.strokeStyle = '#efe9dc'; g.lineWidth = 6; g.strokeRect(6, 6, W - 12, H - 12);
    g.fillStyle = '#f4efe4'; g.font = `bold 58px ${FONT}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(String(text), W / 2, H / 2 + 3);
  });
}
// Sign board: bold sans, black on white, optional red header (VISUAL_BIBLE §4.1). lines: ['KEEP OFF', 'THE LAWN', ...].
export function signTex(lines = ['FOR SALE'], header = '', { bg = '#f6f3ee', ink = '#141414', red = '#d01818', w = 512, h = 384 } = {}) {
  return canvasTex('sign:' + header + '|' + lines.join('|') + bg + w + h, w, h, (g, W, H) => {
    g.fillStyle = bg; g.fillRect(0, 0, W, H); g.strokeStyle = '#1a1a1a'; g.lineWidth = 10; g.strokeRect(5, 5, W - 10, H - 10);
    const rows = (header ? 1 : 0) + lines.length; const lh = Math.min(96, (H - 40) / rows); let y = (H - lh * rows) / 2 + lh / 2;
    g.textAlign = 'center'; g.textBaseline = 'middle';
    const fit = (txt, size) => { g.font = `bold ${size}px ${FONT}`; let s = size; while (g.measureText(txt).width > W - 48 && s > 12) { s -= 2; g.font = `bold ${s}px ${FONT}`; } };
    if (header) { fit(header, Math.round(lh * 0.8)); g.fillStyle = red; g.fillText(header, W / 2, y); y += lh; }
    for (const l of lines) { fit(l, Math.round(lh * 0.72)); g.fillStyle = ink; g.fillText(l, W / 2, y); y += lh; }
  });
}
// Irregular soft blob (alpha map, 0..1 UV): worn lawn patches.
export function blobAlphaTex() {
  return canvasTex('blobAlpha', 128, 128, (g, W, H) => {
    const id = g.createImageData(W, H); const n = fbm(128, 4, 4, 31);
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) { const dx = (x - W / 2) / (W / 2), dy = (y - H / 2) / (H / 2); const d = Math.hypot(dx, dy) + (n[y * 128 + x] - 0.5) * 0.7; const a = clamp01((0.85 - d) / 0.3); const i = (y * W + x) * 4; id.data[i] = id.data[i + 1] = id.data[i + 2] = a * 255; id.data[i + 3] = 255; }
    g.putImageData(id, 0, 0);
  }, { srgb: false });
}
// Soft ring sprite (bursts, ripples).
export function ringTex() {
  return canvasTex('ring', 256, 256, (g, W, H) => {
    const gr = g.createRadialGradient(W / 2, H / 2, W * 0.3, W / 2, H / 2, W * 0.5);
    gr.addColorStop(0, 'rgba(255,255,255,0)'); gr.addColorStop(0.55, 'rgba(255,255,255,0.9)'); gr.addColorStop(0.7, 'rgba(255,255,255,0.5)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = gr; g.fillRect(0, 0, W, H);
  }, { srgb: false });
}
// Moon disc with maria and craters (alpha outside the disc). Tinted by the material colour.
export function moonTex() {
  return canvasTex('moon', 512, 512, (g, W, H) => {
    const N = 512, R = N * 0.48; const id = g.createImageData(N, N); const d = id.data;
    const n1 = fbm(N, 6, 5, 77), n2 = fbm(N, 20, 3, 13), cr = valueNoise(N, 48, 5);
    for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
      const dx = (x - N / 2) / R, dy = (y - N / 2) / R, r2 = dx * dx + dy * dy; const i = (y * N + x) * 4;
      if (r2 > 1) { d[i + 3] = 0; continue; }
      const k = y * N + x; let s = 0.74 + 0.3 * n1[k] - (n1[k] < 0.45 ? 0.16 : 0) + (n2[k] - 0.5) * 0.12 - (cr[k] > 0.8 ? (cr[k] - 0.8) * 0.9 : 0) + (cr[k] < 0.08 ? 0.12 : 0);
      s *= 0.78 + 0.22 * Math.pow(1 - r2, 0.25); const a = clamp01((1 - Math.sqrt(r2)) * R / 1.5);
      d[i] = d[i + 1] = d[i + 2] = clamp01(s) * 255; d[i + 3] = a * 255;
    }
    g.putImageData(id, 0, 0);
  });
}

// ------------------------------------------------------------------ geometry
// Box with UVs in tile units on every face (tile in studs), so world-scaled textures line up on any size.
export function boxUV(w, h, d, tile = 4, bevel = 0) {
  const g = bevel > 0 ? new RoundedBoxGeometry(w, h, d, 2, Math.min(bevel, w / 2 - 1e-3, h / 2 - 1e-3, d / 2 - 1e-3)) : new THREE.BoxGeometry(w, h, d);
  const pos = g.attributes.position, nor = g.attributes.normal, uv = g.attributes.uv;
  for (let i = 0; i < pos.count; i++) { // planar projection by the dominant normal axis (works for bevelled boxes too)
    const x = pos.getX(i), y = pos.getY(i), z = pos.getZ(i), nx = Math.abs(nor.getX(i)), ny = Math.abs(nor.getY(i)), nz = Math.abs(nor.getZ(i));
    if (ny >= nx && ny >= nz) uv.setXY(i, (x + w / 2) / tile, (z + d / 2) / tile);
    else if (nx >= nz) uv.setXY(i, (z + d / 2) / tile, (y + h / 2) / tile);
    else uv.setXY(i, (x + w / 2) / tile, (y + h / 2) / tile);
  }
  return g;
}
// Gable prism: triangular cross-section (base `depth` along z, apex `height` up), extruded `len` along x.
// Caps at x = +-len/2 are the gable ends (UVs in tile units). Sloped faces are usually hidden under roof slabs.
export function prismGeo(len, depth, height, tile = 6) {
  const hx = len / 2, hz = depth / 2; const P = [], N = [], U = [], I = [];
  const quad = (a, b, c, d, n, uvs) => { const o = P.length / 3; for (const v of [a, b, c, d]) P.push(...v); for (let k = 0; k < 4; k++) N.push(...n); U.push(...uvs); I.push(o, o + 1, o + 2, o, o + 2, o + 3); };
  const tri = (a, b, c, n, uvs) => { const o = P.length / 3; for (const v of [a, b, c]) P.push(...v); for (let k = 0; k < 3; k++) N.push(...n); U.push(...uvs); I.push(o, o + 1, o + 2); };
  const sl = Math.hypot(hz, height); const nz = height / sl, ny = hz / sl;
  tri([hx, 0, hz], [hx, 0, -hz], [hx, height, 0], [1, 0, 0], [depth / tile, 0, 0, 0, hz / tile, height / tile]);
  tri([-hx, 0, -hz], [-hx, 0, hz], [-hx, height, 0], [-1, 0, 0], [0, 0, depth / tile, 0, hz / tile, height / tile]);
  quad([-hx, 0, hz], [hx, 0, hz], [hx, height, 0], [-hx, height, 0], [0, ny, nz], [0, 0, len / tile, 0, len / tile, sl / tile, 0, sl / tile]);
  quad([hx, 0, -hz], [-hx, 0, -hz], [-hx, height, 0], [hx, height, 0], [0, ny, -nz], [0, 0, len / tile, 0, len / tile, sl / tile, 0, sl / tile]);
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3)); g.setAttribute('normal', new THREE.Float32BufferAttribute(N, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(U, 2)); g.setIndex(I);
  return g;
}
// Planar UVs for any geometry (top-down XZ by default), in tile units. Use for decks, stones, ground pieces.
export function planarUV(g, tile = 4, axis = 'y') {
  const p = g.attributes.position, uv = g.attributes.uv || new THREE.BufferAttribute(new Float32Array(p.count * 2), 2);
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i), z = p.getZ(i); if (axis === 'y') uv.setXY(i, x / tile, z / tile); else if (axis === 'z') uv.setXY(i, x / tile, y / tile); else uv.setXY(i, z / tile, y / tile); }
  g.setAttribute('uv', uv); return g;
}
// Scale the existing 0..1 UVs of a primitive (cylinders, spheres) to tile units: u * uLen/tile, v * vLen/tile.
export function scaleUV(g, su, sv) { const uv = g.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) * su, uv.getY(i) * sv); return g; }

const _m4 = new THREE.Matrix4(), _q = new THREE.Quaternion(), _e = new THREE.Euler(), _v = new THREE.Vector3(), _s = new THREE.Vector3();
export function trs(pos, rot, scl) {
  pos = pos || [0, 0, 0]; rot = rot || [0, 0, 0]; scl = scl ?? [1, 1, 1];
  _e.set(rot[0] || 0, rot[1] || 0, rot[2] || 0, 'YXZ'); _q.setFromEuler(_e);
  const s = typeof scl === 'number' ? [scl, scl, scl] : scl; return new THREE.Matrix4().compose(_v.set(pos[0], pos[1], pos[2]), _q, _s.set(s[0], s[1], s[2]));
}

// Parts: collect geometry per material key; build() merges each key into one mesh. Transforms nest via push/pop.
export class Parts {
  constructor() { this.byKey = new Map(); this.stack = [new THREE.Matrix4()]; }
  get top() { return this.stack[this.stack.length - 1]; }
  push(m) { this.stack.push(this.top.clone().multiply(m)); return this; }
  pop() { this.stack.pop(); return this; }
  // add(key, geometry, pos, rot, scale): geometry is consumed (transformed in place).
  add(key, g, pos, rot, scl) {
    const m = this.top.clone(); if (pos || rot || scl) m.multiply(trs(pos, rot, scl));
    g.applyMatrix4(m); if (!this.byKey.has(key)) this.byKey.set(key, []); this.byKey.get(key).push(g); return this;
  }
  // box(key, w, h, d, pos, rot, {tile, bevel}): a box with world-tiled UVs (tile defaults to the material's tile).
  box(key, w, h, d, pos, rot, o = {}) { return this.add(key, boxUV(w, h, d, o.tile ?? tileOf(key), o.bevel ?? 0), pos, rot); }
  // bar(key, a, b, w, t): a box of cross-section w x t from point a to point b (frames, rails, legs).
  bar(key, a, b, w, t, o = {}) {
    const A = new THREE.Vector3(...a), B = new THREE.Vector3(...b), d = B.clone().sub(A); const L = d.length();
    const g = boxUV(w, t, L, o.tile ?? tileOf(key), o.bevel ?? 0); g.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), d.normalize()));
    g.translate((A.x + B.x) / 2, (A.y + B.y) / 2, (A.z + B.z) / 2); return this.add(key, g);
  }
  cyl(key, rTop, rBot, h, seg, pos, rot, o = {}) { const g = new THREE.CylinderGeometry(rTop, rBot, h, seg, 1, !!o.open); scaleUV(g, (2 * Math.PI * Math.max(rTop, rBot)) / (o.tile ?? tileOf(key)), h / (o.tile ?? tileOf(key))); return this.add(key, g, pos, rot, o.scale); }
  // Merge into a Group (one Mesh per key). mats: fn(key) -> Material. shadows: {cast, receive}.
  build(mats = M, { cast = false, receive = false, name = 'parts' } = {}) {
    const grp = new THREE.Group(); grp.name = name;
    for (const [key, list] of this.byKey) {
      const geo = mergeList(list); if (!geo) continue;
      const mesh = new THREE.Mesh(geo, mats(key)); mesh.name = key; mesh.castShadow = cast; mesh.receiveShadow = receive; grp.add(mesh);
    }
    return grp;
  }
}
export function mergeList(list) {
  if (!list.length) return null;
  const anyNonIndexed = list.some((g) => !g.index);
  const clean = list.map((g) => {
    let h = anyNonIndexed && g.index ? g.toNonIndexed() : g;
    for (const k of Object.keys(h.attributes)) if (k !== 'position' && k !== 'normal' && k !== 'uv') h.deleteAttribute(k);
    if (!h.attributes.uv) h.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(h.attributes.position.count * 2), 2));
    if (!h.attributes.normal) h.computeVertexNormals();
    h.morphAttributes = {}; return h;
  });
  const out = mergeGeometries(clean, false); clean.forEach((g) => g.dispose()); list.forEach((g) => g.dispose());
  out.computeBoundingSphere(); out.computeBoundingBox(); return out;
}

// ------------------------------------------------------------------ material library
// Tile sizes (studs per texture repeat) per material family; Parts.box() builds UVs with these.
export const TILE = { siding: 6, brick: 4, shingle: 6, stone: 4, flag: 3, porch: 6, deck: 6, trim: 4, grass: 8, lawn: 12, dirt: 4, concrete: 6, kerb: 6, asphalt: 16, plaster: 4, bark: 3, pine: 3, bush: 3, wood: 4, metal: 4, line: 2 };
export const tileOf = (key) => TILE[key.split(':')[0]] ?? 4;
const _mats = new Map();
const std = (o) => persist(new THREE.MeshStandardMaterial({ roughness: 0.6, metalness: 0, ...o }));
// M(key) -> cached material. Keys: 'family' or 'family:#colour' (colour = albedo, display hex). Families:
//   siding brick shingle stone flag porch deck trim grass lawn dirt concrete kerb asphalt line plaster bark pine bush wood
//   door shutter glassDark win (warm|pink|cool|dim, + curtain colour as 3rd field) metal brass black plastic emissive
//   tulip stem leafy paper plaque sign (built by props) basic
export function M(key) {
  if (_mats.has(key)) return _mats.get(key);
  const [fam, a, b, c] = key.split(':'); let m;
  switch (fam) {
    case 'siding': m = std({ ...siding({ color: a || '#d9cfb5', seed: hash32(a || 's') % 97 }).mat, roughness: 0.75 }); break;
    case 'brick': m = std({ ...TX.brick({ color: a || '#7a3528', mortarColor: b || '#a89c94', rows: 9, cols: 4, seed: 3 }).mat, roughness: 0.9 }); break;
    case 'shingle': m = std({ ...TX.roofShingles({ color: a || '#3b3a44', rows: 8, tabs: 4, seed: 5 }).mat, roughness: 0.85 }); break;
    case 'stone': m = std({ ...fieldstone({ color: a || '#8d857b', cells: 5, seed: 2 }).mat, roughness: 0.85 }); break;
    case 'flag': m = std({ ...fieldstone({ color: a || '#9b958c', mortarColor: '#3d3a33', cells: 3, mortar: 0.04, seed: 8 }).mat, roughness: 0.8 }); break;
    case 'porch': case 'deck': m = std({ ...TX.woodPlanks({ color: a || '#a8743a', planks: 8, joints: 2, gloss: 0.4, seed: 4 }).mat, roughness: 0.62 }); break;
    case 'wood': m = std({ ...TX.woodPlanks({ color: a || '#7a4a2a', planks: 5, joints: 1, gloss: 0.45, seed: 6 }).mat, roughness: 0.65 }); break;
    case 'trim': m = std({ ...TX.woodPlanks({ color: a || '#efeee9', gapColor: a || '#efeee9', planks: 4, joints: 0, gap: 0.0, grain: 0.35, variation: 0.03, seed: 7, normal: 0.6 }).mat, roughness: 0.55 }); break;
    case 'grass': case 'lawn': m = std({ ...TX.grass({ color: a || '#5c9550', dark: b || '#386334', light: c || '#86b46c', seed: 3, blades: 11000, normal: 2.2 }).mat, roughness: 1 }); break;
    case 'dirt': m = std({ ...TX.dirt({ color: a || '#5a3a26', dark: '#2e1c10', seed: 2 }).mat, roughness: 0.97 }); break;
    case 'concrete': m = std({ ...TX.concrete({ color: a || '#aaa8a2', mottle: 0.1, seams: 1, seamColor: '#6c6a66', seed: 3 }).mat, roughness: 0.85 }); break;
    case 'kerb': m = std({ ...TX.concrete({ color: a || '#b5b3ad', mottle: 0.08, seams: 0, seed: 4 }).mat, roughness: 0.82 }); break;
    case 'asphalt': m = std({ ...asphalt({ color: a || '#4a4a52' }).mat, roughness: 0.92 }); break;
    case 'line': m = std({ ...TX.plaster({ color: a || '#e8b422', mottle: 0.1, speckle: 0.08, seed: 9 }).mat, roughness: 0.7 }); break;
    case 'plaster': m = std({ ...TX.plaster({ color: a || '#d8d0c4', seed: 2 }).mat, roughness: 0.9 }); break;
    case 'bark': m = std({ ...TX.woodPlanks({ color: a || '#3b2618', planks: 12, joints: 0, gap: 0, grain: 2, rings: 3, seed: 11, normal: 3 }).mat, roughness: 0.95 }); break;
    case 'pine': m = std({ ...TX.grass({ color: a || '#244a35', dark: '#10261a', light: '#3f6e48', blades: 14000, seed: 12, normal: 3 }).mat, roughness: 0.95 }); break;
    case 'bush': case 'leafy': m = std({ ...TX.grass({ color: a || '#2f6a2c', dark: '#173c18', light: '#5f9a48', blades: 9000, seed: 13, normal: 3 }).mat, roughness: 0.9 }); break;
    case 'door': { const t = doorTex(a || '#6b1f1a'); m = std({ map: t, roughness: 0.5 }); break; }
    case 'doorEdge': m = std({ color: a || '#6b1f1a', roughness: 0.55 }); break;
    case 'shutter': m = std({ map: louvre({ color: a || '#3b4347' }).map, roughness: 0.6 }); break;
    case 'glassDark': m = std({ color: a || '#121528', roughness: 0.12, metalness: 0.1, emissive: '#ffffff', emissiveMap: glassSheenTex(), emissiveIntensity: 0.06 }); break;
    case 'win': { // lit window interior (HDR basic material). key 'win:warm:<curtain>:<variant>:<intensity>'
      const tone = a || 'warm'; const tint = { warm: '#ffd9a0', pink: '#f7a8d0', cool: '#b8c4ff', dim: '#ffb870' }[tone] || '#ffd9a0';
      const parts = key.split(':'); const inten = parseFloat(parts[4] ?? '2.3');
      m = persist(new THREE.MeshBasicMaterial({ map: windowInteriorTex(tone, b || '#c85a4a', +(c || 0)), color: new THREE.Color(tint).multiplyScalar(inten) })); break;
    }
    case 'metal': m = std({ color: a || '#2a2a30', roughness: 0.4, metalness: 0.35 }); break;
    case 'black': m = std({ color: a || '#17171c', roughness: 0.38, metalness: 0.15 }); break;
    case 'brass': m = std({ color: a || '#c9a040', roughness: 0.32, metalness: 0.55 }); break;
    case 'plastic': m = std({ color: a || '#d8d8d8', roughness: 0.5 }); break;
    case 'emissive': { const i = parseFloat(b || '4'); m = persist(new THREE.MeshBasicMaterial({ color: new THREE.Color(a || '#ffd9a0').multiplyScalar(i) })); break; }
    case 'tulip': m = std({ color: a || '#d8283a', roughness: 0.45, emissive: a || '#d8283a', emissiveIntensity: 0.04 }); break;
    case 'stem': m = std({ color: a || '#3f7a32', roughness: 0.6 }); break;
    case 'basic': m = persist(new THREE.MeshBasicMaterial({ color: a || '#ffffff' })); break;
    case 'dirtPatch': m = std({ ...TX.dirt({ color: '#5e4430', dark: '#33231a', seed: 5 }).mat, roughness: 0.97, alphaMap: blobAlphaTex(), transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }); delete m.roughnessMap; break;
    default: m = std({ color: a || '#ff00ff' });
  }
  m.name = key; _mats.set(key, m); return m;
}
// A material built from a texture with a custom key (signs, plaques). Cached.
export function texMat(key, map, o = {}) { if (_mats.has(key)) return _mats.get(key); const m = std({ map, roughness: 0.6, ...o }); m.name = key; _mats.set(key, m); return m; }

// Additive glow sprite material (halos on lamps, lanterns, windows). Cached by key; shared, never mutate.
export function glowSpriteMat(key, { color = '#ffd9a0', intensity = 1, opacity = 0.5, falloff = 2.4 } = {}) {
  const k = 'glowSprite:' + key; if (_mats.has(k)) return _mats.get(k);
  const m = persist(new THREE.SpriteMaterial({ map: TX.radialGlow({ falloff }), color: new THREE.Color(color).multiplyScalar(intensity), opacity, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: true }));
  m.name = k; _mats.set(k, m); return m;
}
// Additive ground-decal material (light pools).
export function poolMat(key, { color = '#ffb870', opacity = 0.32, falloff = 1.6 } = {}) {
  const k = 'pool:' + key; if (_mats.has(k)) return _mats.get(k);
  const m = persist(new THREE.MeshBasicMaterial({ map: TX.radialGlow({ falloff }), color, opacity, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4 }));
  m.name = k; _mats.set(k, m); return m;
}
// Flat quad on the XZ plane covering [x0,x1]x[z0,z1] at height y, UVs of a radial decal of radius R centred at (cx, cz).
export function decalQuad(x0, x1, z0, z1, y, R, cx = 0, cz = 0) {
  const P = [x0, y, z0, x1, y, z0, x1, y, z1, x0, y, z1]; const U = []; for (let i = 0; i < 4; i++) U.push((P[i * 3] - cx + R) / (2 * R), (P[i * 3 + 2] - cz + R) / (2 * R));
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(U, 2));
  g.setAttribute('normal', new THREE.Float32BufferAttribute([0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0], 3)); g.setIndex([0, 2, 1, 0, 3, 2]); return g;
}

// ------------------------------------------------------------------ small utils
// Seeded variation helpers.
export const pick = (r, arr) => arr[Math.floor(r() * arr.length) % arr.length];
export const range = (r, a, b) => a + (b - a) * r();
// Shade a hex colour by k (display space).
export function shade(hex, k) { const c = new THREE.Color(hex); c.r = Math.min(1, c.r * k); c.g = Math.min(1, c.g * k); c.b = Math.min(1, c.b * k); return '#' + c.getHexString(); }
// Mark a whole tree persistent (geometry, materials, textures) so a cached set survives shot cleanup.
export function persistTree(o) { o.traverse((x) => { if (x.geometry) persist(x.geometry); if (x.material) [].concat(x.material).forEach((m) => { persist(m); for (const k in m) if (m[k] && m[k].isTexture) persist(m[k]); }); }); return o; }
