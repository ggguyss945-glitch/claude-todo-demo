// THE HERO CREATURE: Grandpa as a garden gnome (VISUAL_BIBLE §2.6, §2.7, §3.2), plus the cheap plastic variant and
// generic family gnomes. Sculpted, not boxes: displaced lathes / spheres / swept tubes / merged clumps, glazed-ceramic
// MeshPhysicalMaterial (roughness 0.28, clearcoat 1, clearcoatRoughness 0.12) with painted wear (mottling, chips of
// white bisque, dirt at the base) and baked vertex ambient occlusion. Height 2.0 studs with the hat (0.38x an R6).
//
//   const g = makeGnome('grandpa', { lantern: 0 })   // preset name or options (see GNOME_PRESETS / DEFAULTS)
//   setGnomeLids(g, closed01); setGnomeGaze(g, yawDeg, pitchDeg); setGnomeHead(g, yawDeg, pitchDeg, rollDeg)
//   setLantern(g, level)  (0 unlit, 1 lit, >1 boosted)   lanternLightUp(t, t0) -> level;  gnomeBlink(t, times, opts) -> 0..1
//   gnomeHeadTurn(t, t0, dur, fromDeg, toDeg) -> yaw with the stony stepped jitter;  gnomeHop(t, t0) -> { y, roll }
// Geometry + materials are cached per worker (keyed by options); each call returns a cheap clone.
import { THREE, STUD, DEG, cached, keyOf, mesh, group, makeRoot, clumpGeo, canvas, canvasTex, makeRng, hash32, noise3, clamp, lerp, smooth, shade, mix, saturate, rgba, ownMat, shadowBlob } from './util.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { fbm as fbmTile, radialGlow } from '../core/textures.js';
import { hashFloat } from '../core/random.js';
import * as anim from '../core/anim.js';

// ---------------- presets ----------------
export const GNOME_DEFAULTS = {
  material: 'ceramic',            // 'ceramic' (glazed) | 'plastic' (cheap: matte by default, dead eyes, sticker)
  finish: null,                   // plastic only: 'matte' (default) | 'glossy' (bible: roughness 0.15)
  lod: 'hero',                    // 'hero' | 'mid' (street gnomes) | 'low'
  height: 2.0,                    // studs, with the hat
  hat: { style: 'pointed', color: '#c8221c', height: 1.12, bendSide: 0.36, bendBack: 0.2, dots: null },
  coat: '#2c5ea8', belt: '#3a2214', buckle: '#d9aa45', boots: '#4a2a18', buttons: '#d9aa45',
  skin: '#f0b49a', nose: '#e8836e', cheek: '#ec7f7c',
  beard: 'full',                  // 'full' | 'walrus' (moustache only) | 'short' | 'none'
  beardColor: '#f4f1ea', brows: true,
  eyes: { iris: '#3d78c8', size: 1.06, style: 'glossy', open: 0.6 }, // style 'glossy' | 'dead'
  mouth: 'teeth',                 // 'teeth' (tiny fixed grin, the uncanny detail) | 'smile' | 'none'
  crack: true,                    // hairline crack across the left temple (uncanny detail)
  glasses: null,                  // e.g. '#d4a64a'
  apron: null,                    // e.g. '#efe6d6'
  hair: null,                     // 'curls' (grandma) colour via hairColor
  hairColor: '#d9d6e0',
  arms: 'lanternSide',            // 'lanternSide' | 'lanternFront'
  lantern: 0,                     // initial level (0 = unlit). false = no lantern
  lanternLight: false,            // true (0.7 cd at level 1) or a number of cd: a point light - only on the few lanterns nearest camera
  sticker: null,                  // plastic: price text, e.g. '$4.99'
  base: false,                    // moulded base plinth (plastic default true)
  wear: 0.35, age: 0,              // chips / dirt amount; age 0..1 = faded paint + moss (epilogue)
  seed: 1,
};
export const GNOME_PRESETS = {
  // EP01 hero: red pointed hat, big white beard + walrus moustache, Grandpa's navy cardigan colour for the coat.
  grandpa: {},
  // Script build sheet variant: olive fishing hat with lures, red coat, walrus moustache only.
  grandpaFishing: { hat: { style: 'fishing', color: '#6f7342' }, coat: '#b8261e', beard: 'walrus' },
  // Frame-1 gnome (the narrator's own): fishing hat, mustard coat, grey moustache.
  narrator: { hat: { style: 'fishing', color: '#6f7342' }, coat: '#d9a52c', beard: 'walrus', beardColor: '#cfcbd2', seed: 4 },
  // Grandma: lavender hat, rose coat, apron, round glasses, grey curls, no beard (line 03 "wearing her GLASSES").
  grandma: { hat: { style: 'pointed', color: '#9b86d8', height: 1.0, bendSide: -0.3, bendBack: 0.16 }, coat: '#c86f93', beard: 'none', glasses: '#d4a64a', apron: '#f1e9da', hair: 'curls', cheek: '#f08a9a', mouth: 'smile', eyes: { iris: '#6a4fb0' }, seed: 2, crack: false },
  plastic: { material: 'plastic', lod: 'low', lantern: false, hat: { style: 'pointed', color: '#18c4bc', height: 1.02, bendSide: 0.12, bendBack: 0.06 }, coat: '#ffd21f', boots: '#2a1a12', beard: 'full', eyes: { style: 'dead' }, mouth: 'smile', crack: false, sticker: '$4.99', base: true, wear: 0 },
};
// Generic family gnomes for other lawns (6-8 variants): hat colours, coats, beards, glasses, aprons.
export const FAMILY_GNOMES = [
  { hat: { color: '#c8221c' }, coat: '#2c5ea8', seed: 11 },
  { hat: { color: '#2f8a4a', bendSide: -0.3 }, coat: '#b8261e', beardColor: '#dcdbe2', glasses: '#c9a04a', seed: 12 },
  { hat: { color: '#8a5ad0', height: 0.95, bendSide: 0.22, dots: '#f4e9c8' }, coat: '#2f8a4a', beard: 'short', apron: '#efe6d6', seed: 13 },
  { hat: { color: '#2a6fd0', bendSide: -0.42, bendBack: 0.1 }, coat: '#d9a52c', beard: 'walrus', seed: 14 },
  { hat: { color: '#e06a1c', height: 1.2 }, coat: '#6e3a8c', beard: 'full', glasses: '#2a2a2a', seed: 15 },
  { hat: { color: '#d84a7a', bendSide: 0.2 }, coat: '#2b8c8c', beard: 'none', hair: 'curls', apron: '#f7f1e6', glasses: '#d4a64a', mouth: 'smile', seed: 16 },
  { hat: { style: 'fishing', color: '#4f6a3a' }, coat: '#8a2a2a', beard: 'walrus', seed: 17 },
  { hat: { color: '#1f3f8a', bendSide: 0.3, dots: '#ffffff' }, coat: '#c8221c', beard: 'full', apron: '#e8dcc8', seed: 18 },
];

function resolve(o = {}) {
  const base = typeof o === 'string' ? GNOME_PRESETS[o] || {} : o;
  const preset = typeof o === 'string' ? {} : (o.preset ? GNOME_PRESETS[o.preset] || {} : {});
  const P = { ...GNOME_DEFAULTS, ...preset, ...base };
  P.hat = { ...GNOME_DEFAULTS.hat, ...(preset.hat || {}), ...(base.hat || {}) };
  P.eyes = { ...GNOME_DEFAULTS.eyes, ...(preset.eyes || {}), ...(base.eyes || {}) };
  if (P.material === 'plastic') { if (base.base == null && preset.base == null) P.base = true; P.finish = P.finish || 'matte'; }
  return P;
}

// ---------------- textures: glaze with wear ----------------
const TS = 512;
function wearFields(seed) {
  return cached(keyOf('gnomeWearFields', seed), () => {
    const mottle = fbmTile(TS, 6, 4, hash32('mottle', seed) & 0xffff), chipsN = fbmTile(TS, 36, 3, hash32('chips', seed) & 0xffff), fine = fbmTile(TS, 64, 2, hash32('fine', seed) & 0xffff);
    const moss = fbmTile(TS, 12, 4, hash32('moss', seed) & 0xffff);
    return { mottle, chipsN, fine, moss };
  });
}
const CHIP_T = (wear) => 0.86 - 0.08 * wear;
// colour map: base colour with mottling, speckles, chips of white bisque (dark rim), optional fade + moss
export function glazeMap(color, { wear = 0.5, age = 0, seed = 1, plastic = false } = {}) {
  return cached(keyOf('glazeMap', color, wear, age, seed, plastic), () => {
    const F = wearFields(seed), c = canvas(TS), g = c.getContext('2d'), id = g.createImageData(TS, TS), d = id.data;
    const base = new THREE.Color(); base.setStyle(age > 0 ? saturate(color, 1 - 0.45 * age) : color, THREE.NoColorSpace);
    const B = [base.r * 255, base.g * 255, base.b * 255], bisque = [239, 230, 218], mossC = [92, 120, 52];
    const thr = CHIP_T(wear);
    for (let i = 0; i < TS * TS; i++) {
      let k = plastic ? 0.97 + 0.06 * F.fine[i] : 0.9 + 0.2 * F.mottle[i] + (F.fine[i] > 0.8 ? -0.06 : 0);
      if (age > 0) k *= 1 + 0.12 * age;
      let r = B[0] * k, gg = B[1] * k, b = B[2] * k;
      if (!plastic && wear > 0) {
        const cv = F.chipsN[i];
        if (cv > thr) { const e = clamp((cv - thr) / 0.012); r = lerp(r * 0.72, bisque[0], e); gg = lerp(gg * 0.72, bisque[1], e); b = lerp(b * 0.72, bisque[2], e); }
        else if (cv > thr - 0.015) { const e = (cv - thr + 0.015) / 0.015 * 0.25; r *= 1 - e; gg *= 1 - e; b *= 1 - e; }
      }
      if (age > 0 && F.moss[i] > 0.62 - 0.12 * age) { const e = clamp((F.moss[i] - 0.62 + 0.12 * age) / 0.06) * age; r = lerp(r, mossC[0] * (0.8 + 0.4 * F.fine[i]), e); gg = lerp(gg, mossC[1] * (0.8 + 0.4 * F.fine[i]), e); b = lerp(b, mossC[2], e); }
      const j = i * 4; d[j] = clamp(r, 0, 255); d[j + 1] = clamp(gg, 0, 255); d[j + 2] = clamp(b, 0, 255); d[j + 3] = 255;
    }
    g.putImageData(id, 0, 0); return canvasTex(c, { wrap: true, repeat: [2, 2] });
  });
}
// R = clearcoat (0 on chips), G = roughness (0.28 glaze, 0.85 bisque)
export function wearMask({ wear = 0.5, seed = 1 } = {}) {
  return cached(keyOf('gnomeWearMask', wear, seed), () => {
    const F = wearFields(seed), c = canvas(TS), g = c.getContext('2d'), id = g.createImageData(TS, TS), d = id.data, thr = CHIP_T(wear);
    for (let i = 0; i < TS * TS; i++) { const chip = wear > 0 && F.chipsN[i] > thr; const j = i * 4; d[j] = chip ? 0 : 255; d[j + 1] = chip ? 217 : 71 + 18 * F.fine[i]; d[j + 2] = 0; d[j + 3] = 255; }
    g.putImageData(id, 0, 0); return canvasTex(c, { wrap: true, srgb: false, repeat: [2, 2] });
  });
}
function strandBump() { // grooves along v (beard / hair strands)
  return cached('gnomeStrandBump', () => {
    const W = 512, H = 256, c = canvas(W, H), g = c.getContext('2d'), r = makeRng(5); g.fillStyle = '#808080'; g.fillRect(0, 0, W, H);
    for (let i = 0; i < 160; i++) { const x = r() * W, w = 1.5 + r() * 3, l = r() < 0.5; g.fillStyle = l ? 'rgba(255,255,255,0.35)' : 'rgba(0,0,0,0.4)'; g.beginPath(); g.moveTo(x, 0); g.bezierCurveTo(x + 8, H * 0.3, x - 8, H * 0.7, x + 3, H); g.lineTo(x + 3 + w, H); g.bezierCurveTo(x - 8 + w, H * 0.7, x + 8 + w, H * 0.3, x + w, 0); g.fill(); }
    return canvasTex(c, { wrap: true, srgb: false, repeat: [3, 1] });
  });
}
// painted eye on a sphere (u = 0.25 faces +z): sclera with a pinkish rim + veins, iris, pupil, painted catchlights
export function eyeTexture(iris = '#3d78c8', irisR = 0.34, seed = 3) {
  return cached(keyOf('gnomeEye', iris, irisR, seed), () => {
    const W = 2048, H = 1024, c = canvas(W, H), g = c.getContext('2d'), cx = W * 0.25, cy = H * 0.5, ppr = W / (2 * Math.PI), ir = irisR * ppr;
    const sg = g.createRadialGradient(cx, cy, ir * 0.8, cx, cy, ppr * 1.35); sg.addColorStop(0, '#fffdf8'); sg.addColorStop(0.55, '#f7ece6'); sg.addColorStop(0.82, '#ebc0bc'); sg.addColorStop(1, '#c97a7c');
    g.fillStyle = '#c97a7c'; g.fillRect(0, 0, W, H); g.fillStyle = sg; g.fillRect(0, 0, W, H);
    const r = makeRng(seed); g.lineCap = 'round';
    for (let i = 0; i < 26; i++) { const a = r() * Math.PI * 2; let x = cx + Math.cos(a) * ppr * 1.25, y = cy + Math.sin(a) * ppr * 1.25; g.strokeStyle = `rgba(190,60,70,${0.16 + r() * 0.16})`; g.lineWidth = 2 + r() * 2.5;
      g.beginPath(); g.moveTo(x, y); for (let k = 0; k < 7; k++) { x += (cx - x) * 0.13 + (r() - 0.5) * 26; y += (cy - y) * 0.13 + (r() - 0.5) * 26; g.lineTo(x, y); if (Math.hypot(x - cx, y - cy) < ir * 1.15) break; } g.stroke(); }
    const ig = g.createRadialGradient(cx, cy, ir * 0.15, cx, cy, ir); ig.addColorStop(0, '#f0c860'); ig.addColorStop(0.36, shade(iris, 1.25)); ig.addColorStop(0.7, iris); ig.addColorStop(0.9, shade(iris, 0.55)); ig.addColorStop(1, '#0a1022');
    g.fillStyle = ig; g.beginPath(); g.arc(cx, cy, ir, 0, Math.PI * 2); g.fill();
    for (let i = 0; i < 90; i++) { const a = (i / 90) * Math.PI * 2 + r() * 0.03; g.strokeStyle = `rgba(255,255,255,${0.1 + r() * 0.16})`; g.lineWidth = 2; g.beginPath(); g.moveTo(cx + Math.cos(a) * ir * 0.45, cy + Math.sin(a) * ir * 0.45); g.lineTo(cx + Math.cos(a) * ir * (0.8 + r() * 0.15), cy + Math.sin(a) * ir * (0.8 + r() * 0.15)); g.stroke(); }
    g.fillStyle = '#040306'; g.beginPath(); g.arc(cx, cy, ir * 0.43, 0, Math.PI * 2); g.fill();
    g.fillStyle = 'rgba(255,255,255,0.97)'; g.beginPath(); g.ellipse(cx - ir * 0.34, cy - ir * 0.36, ir * 0.24, ir * 0.2, -0.4, 0, Math.PI * 2); g.fill();
    g.fillStyle = 'rgba(255,255,255,0.75)'; g.beginPath(); g.arc(cx + ir * 0.33, cy + ir * 0.3, ir * 0.08, 0, Math.PI * 2); g.fill();
    return canvasTex(c, { wrap: false, aniso: 8 });
  });
}
function stickerTexture(text) {
  return cached(keyOf('sticker', text), () => {
    const c = canvas(256, 128), g = c.getContext('2d'); g.fillStyle = '#ffffff'; g.fillRect(0, 0, 256, 128); g.strokeStyle = '#e0261e'; g.lineWidth = 10; g.strokeRect(8, 8, 240, 112);
    g.fillStyle = '#e0261e'; g.font = 'bold 66px sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(text, 128, 70); g.fillStyle = '#9a9aa2'; g.font = 'bold 18px sans-serif'; g.fillText('SALE  •  GARDEN', 128, 24);
    return canvasTex(c);
  });
}

// ---------------- materials ----------------
function ceramic(color, P, { rough = 0.28, cc = 1, ccr = 0.12, bump = null, bumpScale = 1, wear = P.wear } = {}) {
  const plastic = P.material === 'plastic';
  return cached(keyOf('gnomeMat', color, P.material, P.finish, rough, wear, P.age, P.seed % 3, !!bump, bumpScale), () => {
    if (plastic) {
      const glossy = P.finish === 'glossy';
      return new THREE.MeshPhysicalMaterial({ color: '#ffffff', map: glazeMap(saturate(color, 1.25), { plastic: true, seed: P.seed % 3 }), vertexColors: true, roughness: glossy ? 0.15 : 0.52, clearcoat: glossy ? 0.6 : 0, clearcoatRoughness: 0.2, bumpMap: bump, bumpScale });
    }
    const mask = wearMask({ wear, seed: P.seed % 3 });
    return new THREE.MeshPhysicalMaterial({ color: '#ffffff', map: glazeMap(color, { wear, age: P.age, seed: P.seed % 3 }), vertexColors: true, roughness: rough / 0.28, roughnessMap: mask,
      clearcoat: cc * (1 - 0.6 * P.age), clearcoatRoughness: ccr + 0.25 * P.age, clearcoatMap: mask, bumpMap: bump, bumpScale });
  });
}

// ---------------- geometry helpers ----------------
const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const SEG = (P, n) => Math.max(8, Math.round(n * (P.lod === 'hero' ? 1 : P.lod === 'mid' ? 0.6 : 0.4)));
function xf(geo, pos = [0, 0, 0], rot = [0, 0, 0], scale = [1, 1, 1], order = 'XYZ') {
  const g = geo; const m = new THREE.Matrix4().compose(V3(...pos), new THREE.Quaternion().setFromEuler(new THREE.Euler(rot[0], rot[1], rot[2], order)), V3(...(typeof scale === 'number' ? [scale, scale, scale] : scale)));
  g.applyMatrix4(m); return g;
}
const strip = (g) => { for (const k of Object.keys(g.attributes)) if (!['position', 'normal', 'uv'].includes(k)) g.deleteAttribute(k); return g; };
const merge = (list) => mergeGeometries(list.map((x) => strip(x.index ? x.toNonIndexed() : x)));
// clump pointing along (yaw, pitch): pitch 0 = down, PI/2 = outward along yaw (0 = +z), PI = up
function clump(anchor, yaw, pitch, R, L, bend = 0, curl = 0, seg = 14, taper = 0.85) { return xf(clumpGeo(R, L, bend, curl, seg, taper), anchor, [-pitch, yaw, 0], [1, 1, 1], 'YXZ'); }
// Analytic sphere occlusion: ao = 1 - k * sum (R/d)^2 * max(0, n.dir)
function bakeAO(geo, occ = [], { dirt = true, k = 0.9, base = 1, tint = null } = {}) {
  const p = geo.attributes.position, n = geo.attributes.normal, N = p.count, col = new Float32Array(N * 3), P = V3(), Nn = V3(), D = V3();
  const T = tint ? new THREE.Color(tint) : null;
  for (let i = 0; i < N; i++) {
    P.fromBufferAttribute(p, i); Nn.fromBufferAttribute(n, i);
    let o = 0; for (const s of occ) { D.subVectors(s.c, P); const d = Math.max(D.length(), s.r * 0.6); const c = Nn.dot(D) / d; if (c > 0 && d > s.r * 0.98) o += (s.k ?? 1) * (s.r * s.r) / (d * d) * c; }
    let a = base * (1 - clamp(o * k, 0, 0.6)) * (0.9 + 0.1 * clamp(Nn.y * 0.5 + 0.5)); // underside slightly darker
    let r = a, g = a, b = a;
    if (dirt && P.y < 0.22) { const e = smooth(0.22, 0.02, P.y) * (0.55 + 0.45 * (noise3(P.x * 14, P.y * 14, P.z * 14, 7) * 0.5 + 0.5)); r *= 1 - 0.35 * e; g *= 1 - 0.45 * e; b *= 1 - 0.55 * e; }
    if (T) { r *= T.r; g *= T.g; b *= T.b; }
    col[i * 3] = r; col[i * 3 + 1] = g; col[i * 3 + 2] = b;
  }
  geo.setAttribute('color', new THREE.BufferAttribute(col, 3)); return geo;
}
function lathe(prof, seg) { const g = new THREE.LatheGeometry(prof.map(([r, y]) => new THREE.Vector2(r, y)), seg); return g; }
function profR(prof, y) { for (let i = 1; i < prof.length; i++) { const [r0, y0] = prof[i - 1], [r1, y1] = prof[i]; if ((y >= y0 && y <= y1) || (y <= y0 && y >= y1)) return y1 === y0 ? Math.max(r0, r1) : r0 + (r1 - r0) * (y - y0) / (y1 - y0); } return 0; }
// tapered swept tube along points (sleeves, tentacles...)
function taperTube(pts, r0, r1, radial = 16, tubular = 24) {
  const curve = new THREE.CatmullRomCurve3(pts.map((p) => V3(...p)), false, 'centripetal');
  const g = new THREE.TubeGeometry(curve, tubular, 1, radial, false), p = g.attributes.position, C = V3();
  for (let i = 0; i <= tubular; i++) { const t = i / tubular; curve.getPointAt(t, C); const r = lerp(r0, r1, t) * (1 + 0.08 * Math.sin(t * Math.PI)); for (let j = 0; j <= radial; j++) { const k = i * (radial + 1) + j; p.setXYZ(k, C.x + (p.getX(k) - C.x) * r, C.y + (p.getY(k) - C.y) * r, C.z + (p.getZ(k) - C.z) * r); } }
  return smoothNormals(g);
}

// Smooth normals welded across UV seams (sphere / lathe seams would otherwise show as shading lines)
function smoothNormals(g) {
  const pos = g.attributes.position, n = pos.count, idx = g.index ? g.index.array : null, T = idx ? idx.length : n;
  const keyOf3 = (i) => Math.round(pos.getX(i) * 2e4) + ',' + Math.round(pos.getY(i) * 2e4) + ',' + Math.round(pos.getZ(i) * 2e4);
  const keys = new Array(n), acc = new Map(); for (let i = 0; i < n; i++) { keys[i] = keyOf3(i); if (!acc.has(keys[i])) acc.set(keys[i], [0, 0, 0]); }
  const a = V3(), b = V3(), c = V3(), e1 = V3(), e2 = V3();
  for (let t = 0; t < T; t += 3) { const i0 = idx ? idx[t] : t, i1 = idx ? idx[t + 1] : t + 1, i2 = idx ? idx[t + 2] : t + 2;
    a.fromBufferAttribute(pos, i0); b.fromBufferAttribute(pos, i1); c.fromBufferAttribute(pos, i2); e1.subVectors(b, a); e2.subVectors(c, a); e1.cross(e2);
    for (const i of [i0, i1, i2]) { const v = acc.get(keys[i]); v[0] += e1.x; v[1] += e1.y; v[2] += e1.z; } }
  const nr = new Float32Array(n * 3); for (let i = 0; i < n; i++) { const v = acc.get(keys[i]), l = Math.hypot(v[0], v[1], v[2]) || 1; nr[i * 3] = v[0] / l; nr[i * 3 + 1] = v[1] / l; nr[i * 3 + 2] = v[2] / l; }
  g.setAttribute('normal', new THREE.BufferAttribute(nr, 3)); return g;
}
// A sculpted lock (beard / moustache / brow strand bundle): a tube along a curve, fat near the root and tapering to a
// point, its cross-section flattened along `flat` axis and fluted into `ridges` strands.
function lockGeo(pts, R0, { flat = 0.62, flatAxis = [0, 0, 1], ridges = 4, ridgeAmp = 0.16, belly = 0.25, tipPow = 0.85, radial = 16, tubular = 30 } = {}) {
  const curve = new THREE.CatmullRomCurve3(pts.map((q) => V3(...q)), false, 'centripetal');
  const g = new THREE.TubeGeometry(curve, tubular, 1, radial, false), p = g.attributes.position, C = V3(), O = V3(), F = V3(...flatAxis).normalize();
  for (let i = 0; i <= tubular; i++) {
    const t = i / tubular; curve.getPointAt(t, C);
    const r = R0 * (t < belly ? 0.7 + 0.3 * Math.sin((t / belly) * Math.PI / 2) : Math.pow(Math.max(0, 1 - (t - belly) / (1 - belly)), tipPow)) + 0.0015;
    for (let j = 0; j <= radial; j++) {
      const k = i * (radial + 1) + j, ang = (j / radial) * Math.PI * 2;
      O.set(p.getX(k) - C.x, p.getY(k) - C.y, p.getZ(k) - C.z);
      const fl = 1 + ridgeAmp * (Math.pow(Math.abs(Math.cos(ang * ridges / 2)), 0.6) - 0.6);
      O.multiplyScalar(r * fl); const d = O.dot(F); O.addScaledVector(F, d * (flat - 1));
      p.setXYZ(k, C.x + O.x, C.y + O.y, C.z + O.z); g.attributes.uv.setXY(k, j / radial, t);
    }
  }
  return smoothNormals(g);
}

// ---------------- the body plan (studs, gnome space, feet at y 0, facing +z) ----------------
const COAT = [[0, 0.1], [0.33, 0.1], [0.37, 0.12], [0.4, 0.17], [0.415, 0.25], [0.42, 0.33], [0.41, 0.42], [0.385, 0.51], [0.345, 0.59], [0.29, 0.66], [0.22, 0.71], [0.12, 0.745], [0, 0.76]];
const coatDisp = (phi, y, seed) => 0.026 * Math.exp(-(((y - 0.3) / 0.13) ** 2)) * Math.max(0, Math.cos(phi)) ** 2 + 0.009 * Math.sin(phi * 7 + 0.5) * smooth(0.26, 0.1, y) + 0.005 * noise3(Math.sin(phi) * 3, y * 6, Math.cos(phi) * 3, seed);
const HEAD_C = V3(0, 0.985, 0.04), HEAD_R = 0.29, NECK = V3(0, 0.74, 0.03);
const ARMS = {
  lanternSide: { R: [[-0.25, 0.64, 0.02], [-0.42, 0.56, 0.08], [-0.43, 0.66, 0.22], [-0.4, 0.74, 0.28]], handR: [-0.395, 0.765, 0.3], L: [[0.25, 0.64, 0.02], [0.41, 0.52, 0.06], [0.38, 0.43, 0.2], [0.34, 0.41, 0.27]], handL: [0.325, 0.405, 0.3], lantern: [-0.395, 0.735, 0.3] },
  lanternFront: { R: [[-0.25, 0.64, 0.02], [-0.38, 0.5, 0.12], [-0.25, 0.4, 0.38], [-0.16, 0.38, 0.46]], handR: [-0.13, 0.375, 0.5], L: [[0.25, 0.64, 0.02], [0.38, 0.5, 0.12], [0.25, 0.4, 0.38], [0.16, 0.38, 0.46]], handL: [0.13, 0.375, 0.5], lantern: [0, 0.39, 0.52] },
};

function buildGnome(P) {
  const plastic = P.material === 'plastic', hero = P.lod === 'hero';
  const root = new THREE.Group(); root.name = 'gnomeModel';
  const body = group('gnomeBody', root), head = group('gnomeHead', body, [NECK.x, NECK.y, NECK.z]);
  const S = (n) => SEG(P, n), seed = P.seed;
  const r = makeRng(hash32('gnome', seed));
  const A = ARMS[P.arms] || ARMS.lanternSide;
  const eyeR = 0.1 * (P.eyes.size || 1) * (plastic ? 0.5 : 1), EYE = (s) => V3(s * 0.132, 0.995, 0.232);
  // occluders (gnome space, rest pose)
  const O = { head: { c: HEAD_C, r: HEAD_R }, brim: { c: V3(0, 1.16, -0.02), r: 0.3, k: 1.2 }, nose: { c: V3(0, 0.915, 0.345), r: 0.085 }, mous: { c: V3(0, 0.85, 0.37), r: 0.1, k: 1.3 },
    beard1: { c: V3(0, 0.78, 0.3), r: 0.2 }, beard2: { c: V3(0, 0.56, 0.38), r: 0.18 }, body1: { c: V3(0, 0.32, 0), r: 0.42 }, body2: { c: V3(0, 0.56, 0), r: 0.36 },
    armR: { c: V3(...A.R[1]), r: 0.09 }, armL: { c: V3(...A.L[1]), r: 0.09 }, eyeL: { c: EYE(1), r: eyeR }, eyeR: { c: EYE(-1), r: eyeR } };
  const hasBeard = P.beard === 'full' || P.beard === 'short';
  const add = (geo, mat, parent = body, occ = [], opts = {}) => { bakeAO(geo, occ, opts); if (parent === head) geo.translate(-NECK.x, -NECK.y, -NECK.z); return mesh(geo, mat, { parent, name: opts.name }); };
  const M = {
    coat: ceramic(P.coat, P), hat: ceramic(P.hat.color, P), skin: ceramic(P.skin, P, { rough: 0.32 }), nose: ceramic(P.nose, P, { rough: 0.26 }), cheek: ceramic(P.cheek, P, { rough: 0.32 }),
    boots: ceramic(P.boots, P, { rough: 0.24 }), belt: ceramic(P.belt, P, { rough: 0.3 }), gold: new THREE.MeshPhysicalMaterial({ color: P.buckle, metalness: plastic ? 0.2 : 0.85, roughness: 0.3, clearcoat: 0.5 }),
    beard: ceramic(P.beardColor, P, { rough: 0.34, bump: plastic ? null : strandBump(), bumpScale: 1.4 }), hair: ceramic(P.hairColor, P, { rough: 0.36, bump: strandBump(), bumpScale: 1 }),
    dark: ceramic('#3a1414', P, { rough: 0.3, wear: 0 }), teeth: ceramic('#f6f1e6', P, { rough: 0.25, wear: 0 }), lash: ceramic('#2a1a14', P, { rough: 0.35, wear: 0 }),
    apron: P.apron ? ceramic(P.apron, P) : null,
  };
  // ---- boots
  for (const s of [-1, 1]) { const g = new THREE.SphereGeometry(1, S(36), S(24)); const p = g.attributes.position; for (let i = 0; i < p.count; i++) { const y = p.getY(i); if (y < -0.35) p.setY(i, -0.35 - (y + 0.35) * 0.25); } smoothNormals(g);
    add(xf(g, [s * 0.155, 0.085, 0.2], [-0.12, s * 0.12, 0], [0.145, 0.09, 0.23]), M.boots, body, [O.body1], { name: 'boot' }); }
  // ---- coat (displaced lathe) + hem + belt + buttons
  { const g = lathe(COAT, S(96)); const p = g.attributes.position; for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i), z = p.getZ(i), rr = Math.hypot(x, z); if (rr < 1e-4) continue; const phi = Math.atan2(x, z), d = coatDisp(phi, y, seed); p.setXYZ(i, x / rr * (rr + d), y, z / rr * (rr + d)); }
    smoothNormals(g); add(g, M.coat, body, [O.beard1, O.beard2, O.head, O.armR, O.armL], { name: 'coat' }); }
  { const g = xf(new THREE.TorusGeometry(0.352, 0.026, S(10), S(96)), [0, 0.112, 0], [Math.PI / 2, 0, 0]); const p = g.attributes.position; for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i), z = p.getZ(i), rr = Math.hypot(x, z), phi = Math.atan2(x, z), d = coatDisp(phi, 0.12, seed); p.setXYZ(i, x / rr * (rr + d), y, z / rr * (rr + d)); } smoothNormals(g); add(g, ceramic(shade(P.coat, 0.82), P), body, [], { name: 'hem' }); }
  if (!P.apron) {
    const bp = []; for (let i = 0; i <= 6; i++) { const y = 0.322 + i * 0.013; bp.push([profR(COAT, y) + 0.016 + (i === 0 || i === 6 ? -0.008 : 0.004 * Math.sin(i / 6 * Math.PI)), y]); }
    const g = lathe(bp, S(96)), p = g.attributes.position; for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i), z = p.getZ(i), rr = Math.hypot(x, z), phi = Math.atan2(x, z), d = coatDisp(phi, y, seed); p.setXYZ(i, x / rr * (rr + d), y, z / rr * (rr + d)); }
    smoothNormals(g); add(g, M.belt, body, [O.beard2], { name: 'belt' });
    const fz = profR(COAT, 0.36) + coatDisp(0, 0.36, seed) + 0.03;
    const bk = new THREE.TorusGeometry(0.05, 0.016, 8, 4); add(xf(bk, [0, 0.361, fz], [0, 0, Math.PI / 4], [1.25, 0.95, 1]), M.gold, body, [], { name: 'buckle', dirt: false });
    for (const y of [0.2, 0.125]) { const by = profR(COAT, y) + coatDisp(0, y, seed); add(xf(new THREE.SphereGeometry(0.024, 12, 8), [0, y, by + 0.005], [0, 0, 0], [1, 1, 0.5]), ceramic(P.buttons, P), body, [], { dirt: false }); }
  } else {
    const ap = []; for (let i = 0; i <= 10; i++) { const y = 0.1 + i * 0.033; ap.push([profR(COAT, y) + 0.018, y]); }
    const g = new THREE.LatheGeometry(ap.map(([a, b]) => new THREE.Vector2(a, b)), S(48), -1.15, 2.3), p = g.attributes.position;
    for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i), z = p.getZ(i), rr = Math.hypot(x, z), phi = Math.atan2(x, z), d = coatDisp(phi, y, seed) + 0.006 * Math.sin(phi * 9) * smooth(0.3, 0.12, y); p.setXYZ(i, x / rr * (rr + d), y, z / rr * (rr + d)); }
    smoothNormals(g); const am = M.apron.clone(); am.side = THREE.DoubleSide; add(g, am, body, [O.beard2], { name: 'apron' });
    const band = []; for (let i = 0; i <= 4; i++) { const y = 0.42 + i * 0.012; band.push([profR(COAT, y) + 0.02, y]); } add(lathe(band, S(72)), M.apron, body, [], { name: 'apronBand' });
  }
  // ---- arms: tapered sleeves, cuffs, mitten hands
  for (const [side, pts, hand] of [['R', A.R, A.handR], ['L', A.L, A.handL]]) {
    add(taperTube(pts, 0.085, 0.066, S(18), S(20)), M.coat, body, [O.body2, O.body1], { name: 'sleeve' + side });
    const end = V3(...pts[pts.length - 1]), prev = V3(...pts[pts.length - 2]), dir = end.clone().sub(prev).normalize();
    const cuff = new THREE.TorusGeometry(0.066, 0.022, S(10), S(24)); const q = new THREE.Quaternion().setFromUnitVectors(V3(0, 0, 1), dir);
    cuff.applyQuaternion(q); cuff.translate(end.x, end.y, end.z); add(cuff, ceramic(shade(P.coat, 0.85), P), body, []);
    const h = xf(new THREE.SphereGeometry(0.066, S(24), S(16)), [0, 0, 0], [0, 0, 0], [1, 1.12, 0.92]); h.translate(...hand); add(h, M.skin, body, [O.body1], { name: 'hand' + side });
    const th = new THREE.SphereGeometry(0.027, S(14), S(10)); th.translate(hand[0] + (side === 'R' ? 0.05 : -0.05), hand[1] + 0.02, hand[2] + 0.03); add(th, M.skin, body, []);
  }
  // ---- head
  { const g = new THREE.SphereGeometry(HEAD_R, S(64), S(48)), p = g.attributes.position;
    for (let i = 0; i < p.count; i++) { let x = p.getX(i), y = p.getY(i), z = p.getZ(i); const f = Math.max(0, z / HEAD_R); x *= 1 + 0.06 * f * Math.max(0, -y / HEAD_R); y *= 0.97; z *= 0.98; p.setXYZ(i, x + HEAD_C.x, y + HEAD_C.y, z + HEAD_C.z); }
    smoothNormals(g); add(g, M.skin, head, [O.brim, O.nose, O.mous, O.eyeL, O.eyeR], { name: 'headMesh' }); }
  for (const s of [-1, 1]) { add(xf(new THREE.SphereGeometry(0.056, S(18), S(12)), [s * 0.285, 0.975, 0.02], [0, 0, 0], [0.55, 1.1, 0.9]), M.skin, head, [O.head, O.brim]); }
  if (!plastic) { for (const s of [-1, 1]) add(xf(new THREE.SphereGeometry(0.08, S(24), S(16)), [s * 0.17, 0.885, 0.258], [0, s * 0.3, 0], [1, 0.82, 0.7]), M.cheek, head, [O.nose, O.mous], { name: 'cheek' }); }
  { const g = new THREE.SphereGeometry(plastic ? 0.066 : 0.085, S(36), S(28)), p = g.attributes.position; for (let i = 0; i < p.count; i++) { const y = p.getY(i); p.setY(i, y * (y < 0 ? 1.12 : 1)); } smoothNormals(g);
    add(xf(g, [0, 0.912, plastic ? 0.33 : 0.345], [0, 0, 0], [1.06, 1, 0.94]), M.nose, head, [O.mous], { name: 'nose' }); }
  // ---- eyes: glossy domes with painted iris, upper lids that blink, lower lids, lash line
  const eyes = [];
  for (const s of [1, -1]) {
    const nm = s > 0 ? 'L' : 'R', ec = EYE(s);
    const eg = group('eye' + nm, head, [ec.x - NECK.x, ec.y - NECK.y, ec.z - NECK.z]); eg.rotation.y = s * 0.18;
    if (P.eyes.style === 'dead') { mesh(new THREE.SphereGeometry(0.036, 16, 12), cached('deadEyeMat', () => new THREE.MeshStandardMaterial({ color: '#0a0a0c', roughness: 0.65 })), { parent: eg, pos: [0, 0.005, 0.07], scale: [1, 1.15, 0.45], name: 'ball' + nm }); continue; }
    const em = cached(keyOf('gnomeEyeMat', P.eyes.iris), () => new THREE.MeshPhysicalMaterial({ map: eyeTexture(P.eyes.iris), roughness: 0.16, clearcoat: 1, clearcoatRoughness: 0.02 }));
    mesh(new THREE.SphereGeometry(eyeR, S(48), S(36)), em, { parent: eg, name: 'ball' + nm, cast: false, rot: [0, -s * 0.18, 0] });
    const lidPivot = group('lid' + nm, eg); lidPivot.userData.open = -(P.eyes.open ?? 0.6); lidPivot.userData.closed = 0.82; lidPivot.rotation.x = lidPivot.userData.open;
    const lid = new THREE.SphereGeometry(eyeR * 1.08, S(40), S(18), 0, Math.PI * 2, 0, Math.PI * 0.5); bakeAO(lid, [], { dirt: false }); mesh(lid, M.skin, { parent: lidPivot, name: 'upperLid' + nm });
    const lash = new THREE.TorusGeometry(eyeR * 1.083, 0.0062, 6, S(32), Math.PI); lash.rotateX(Math.PI / 2); bakeAO(lash, [], { dirt: false }); mesh(lash, M.lash, { parent: lidPivot, cast: false });
    const low = new THREE.SphereGeometry(eyeR * 1.06, S(40), S(8), 0, Math.PI * 2, Math.PI * 0.74, Math.PI * 0.26); bakeAO(low, [], { dirt: false }); mesh(low, M.skin, { parent: eg, name: 'lowerLid' + nm });
    eyes.push(nm);
  }
  // ---- brows: bushy locks over the eyes, peeking out under the brim
  if (P.brows && !plastic) { const bl = []; for (const s of [-1, 1]) { bl.push(lockGeo([[s * 0.045, 1.083, 0.318], [s * 0.11, 1.106, 0.314], [s * 0.18, 1.1, 0.285], [s * 0.235, 1.07, 0.235]], 0.034, { flat: 0.55, flatAxis: [0, 0.4, 1], ridges: 3, belly: 0.4, radial: S(14), tubular: S(20) }));
      bl.push(lockGeo([[s * 0.08, 1.09, 0.31], [s * 0.15, 1.115, 0.3], [s * 0.21, 1.1, 0.262]], 0.026, { flat: 0.55, flatAxis: [0, 0.4, 1], ridges: 3, radial: S(12), tubular: S(16) })); }
    add(merge(bl), M.beard, head, [O.brim], { name: 'brows', dirt: false }); }
  // ---- mouth (fixed: tiny grin with teeth = the uncanny detail; never animates)
  if (P.mouth !== 'none') {
    const my = P.beard === 'none' ? 0.85 : 0.8, mz = P.beard === 'none' ? 0.31 : 0.33;
    if (P.mouth === 'teeth' || P.mouth === 'smile') add(xf(new THREE.SphereGeometry(1, S(24), S(12)), [0, my, mz], [0.2, 0, 0], [0.07, 0.03, 0.025]), M.dark, head, [O.mous], { name: 'mouth', dirt: false });
    if (P.mouth === 'teeth') for (let k = -2; k <= 2; k++) add(xf(new THREE.BoxGeometry(0.02, 0.022, 0.012), [k * 0.023, my + 0.012 - Math.abs(k) * 0.003, mz + 0.022 - Math.abs(k) * 0.004], [0.2, 0, 0]), M.teeth, head, [], { dirt: false });
  }
  // ---- beard: one sculpted mass (elliptic cross-sections on a curved spine, big lock flutes + fine strands) + flowing
  // locks that break the silhouette (side locks from the cheeks, three wavy points at the bottom)
  if (hasBeard) {
    const short = P.beard === 'short', L = short ? 0.6 : 1;
    const yv = (v) => 0.9 - 0.6 * L * v, zb = (v) => lerp(0.13, 0.38, smooth(0, 1, v * 1.25)), th = (v) => lerp(0.25, 0.07, Math.pow(v, 1.1)),
      wv = (v) => (v < 0.28 ? lerp(0.24, 0.285, Math.sin((v / 0.28) * Math.PI / 2)) : lerp(0.285, 0.03, Math.pow((v - 0.28) / 0.72, 1.5)));
    const g = new THREE.SphereGeometry(1, S(88), S(72)), p = g.attributes.position;
    for (let i = 0; i < p.count; i++) {
      const ux = p.getX(i), uy = p.getY(i), uz = p.getZ(i), v = Math.acos(clamp(uy, -1, 1)) / Math.PI, ring = Math.hypot(ux, uz);
      const ca = ring > 1e-5 ? ux / ring : 0, sa = ring > 1e-5 ? uz / ring : 1;
      const w = wv(v), t = th(v); let X = w * ca, Y = yv(v), Z = zb(v) + t * (sa + 1) / 2 - (ca * ca) * 0.1 * smooth(0.1, 0.5, v);
      if (!plastic && sa > -0.35) {
        const flow = 0.45 * Math.sin(v * 4.2 + ca * 1.7);                     // the locks sway as they fall
        const big = Math.pow(Math.abs(Math.sin(Math.PI * (ca * 2.6 + flow))), 0.55); // ~5 big locks across the front
        const fine = Math.sin(Math.PI * (ca * 13 + flow * 2.2));             // strands inside each lock
        const amp = smooth(0.04, 0.16, v) * (1 - 0.6 * smooth(0.85, 1, v)) * smooth(-0.35, 0.1, sa);
        const nx = ca / Math.max(w, 1e-3), nz = sa / Math.max(t / 2, 1e-3), nl = Math.hypot(nx, nz) || 1, d = amp * (0.03 * (big - 0.62) + 0.005 * fine);
        X += d * nx / nl; Z += d * nz / nl;
        if (P.mouth !== 'none') Z -= 0.075 * Math.exp(-((X / 0.085) ** 2) - (((Y - 0.8) / 0.034) ** 2)); // mouth dent
      }
      Y += 0.008 * noise3(X * 9, Y * 9, Z * 9, seed);
      p.setXYZ(i, X, Y, Z);
    }
    smoothNormals(g); add(g, M.beard, head, [O.mous, O.nose, O.head, O.body2], { name: 'beard', dirt: false });
    if (!plastic) {
      const lk = [], q = (x, y, z) => [x, y, z];
      for (const s of [-1, 1]) {
        // side locks: from the cheek, down the beard edge, flicking outward
        lk.push(lockGeo([q(s * 0.255, 0.9, 0.19), q(s * 0.3, 0.78, 0.26), q(s * 0.3, 0.64, 0.31), q(s * 0.25, 0.53, 0.36), q(s * 0.27, 0.46, 0.38)], 0.072, { flatAxis: [s * 0.6, 0, 1], ridges: 4, radial: S(16), tubular: S(30) }));
        lk.push(lockGeo([q(s * 0.2, 0.84, 0.31), q(s * 0.235, 0.7, 0.37), q(s * 0.19, 0.57, 0.42), q(s * 0.15, 0.48, 0.44), q(s * 0.175, 0.42, 0.45)], 0.066, { ridges: 4, radial: S(16), tubular: S(30) }));
        // bottom points (wavy, slight curl forward)
        if (!short) lk.push(lockGeo([q(s * 0.11, 0.6, 0.4), q(s * 0.13, 0.48, 0.44), q(s * 0.1, 0.38, 0.46), q(s * 0.13, 0.31, 0.48), q(s * 0.17, 0.27, 0.51)], 0.07, { ridges: 4, radial: S(16), tubular: S(30) }));
      }
      lk.push(lockGeo(short ? [q(0, 0.62, 0.4), q(0.02, 0.55, 0.43), q(-0.02, 0.5, 0.45), q(0.01, 0.46, 0.47)] : [q(0, 0.58, 0.42), q(0.02, 0.45, 0.46), q(-0.03, 0.34, 0.48), q(0.0, 0.26, 0.5), q(0.04, 0.21, 0.53)], 0.078, { ridges: 5, radial: S(18), tubular: S(32) }));
      add(merge(lk), M.beard, head, [O.body2, O.body1], { name: 'beardLocks', dirt: false });
    }
  }
  if (P.beard !== 'none') { // walrus moustache: two big swooping lobes from under the nose, drooping, with a second layer
    const ml = [xf(new THREE.SphereGeometry(1, S(32), S(20)), [0, 0.86, 0.37], [0.3, 0, 0], [0.075, 0.042, 0.05])];
    for (const s of [-1, 1]) {
      ml.push(lockGeo([[s * 0.005, 0.868, 0.392], [s * 0.07, 0.862, 0.408], [s * 0.15, 0.836, 0.39], [s * 0.22, 0.79, 0.34], [s * 0.255, 0.745, 0.31]], plastic ? 0.05 : 0.058, { flat: 0.6, flatAxis: [0, 0.3, 1], ridges: plastic ? 0 : 5, belly: 0.3, radial: S(18), tubular: S(30) }));
      ml.push(lockGeo([[s * 0.02, 0.85, 0.38], [s * 0.09, 0.835, 0.39], [s * 0.16, 0.8, 0.37], [s * 0.2, 0.755, 0.34]], plastic ? 0.04 : 0.046, { flat: 0.6, flatAxis: [0, 0.3, 1], ridges: plastic ? 0 : 4, belly: 0.3, radial: S(16), tubular: S(24) }));
    }
    add(merge(ml), M.beard, head, [O.nose], { name: 'moustache', dirt: false });
  }
  // back hair below the hat brim (ear to ear round the back) / grandma curls
  if (!plastic) {
    const hl = [];
    if (P.hair === 'curls') { for (let k = 0; k < 11; k++) { const a = Math.PI * 0.4 + (k / 10) * Math.PI * 1.2, x = Math.sin(a) * 0.27, z = Math.cos(a) * 0.27 + 0.03; hl.push(xf(new THREE.TorusGeometry(0.045, 0.03, 8, S(16)), [x, 0.99 - (k % 2) * 0.04, z], [r() * 0.6, a, 0.4])); } add(merge(hl), M.hair, head, [O.brim], { name: 'curls', dirt: false }); }
    else if (P.beard !== 'none') { for (let k = 0; k < 9; k++) { const a = Math.PI * 0.45 + (k / 8) * Math.PI * 1.1, sx = Math.sin(a), cz = Math.cos(a), w = 0.012 * Math.sin(k * 2.1);
        hl.push(lockGeo([[sx * 0.262, 1.075, cz * 0.262 + 0.035], [sx * 0.29, 1.0, cz * 0.29 + 0.035], [sx * (0.3 + w), 0.93 - (k % 2) * 0.025, cz * (0.3 + w) + 0.035]], 0.062, { flat: 0.5, flatAxis: [sx, 0, cz], ridges: 3, belly: 0.35, radial: S(14), tubular: S(16) })); }
      add(merge(hl), M.beard, head, [O.brim], { name: 'backHair', dirt: false }); }
  }
  // crack: a hairline crack from under the brim across the left temple to the cheek
  if (P.crack && !plastic) {
    const pts = []; const rc = makeRng(hash32('crack', seed)); for (let i = 0; i <= 9; i++) { const t = i / 9, el = lerp(0.5, 0.02, t) + (rc() - 0.5) * 0.05, az = lerp(0.92, 0.78, t) + (rc() - 0.5) * 0.07; const R = HEAD_R * 1.003;
      pts.push(V3(HEAD_C.x + Math.sin(az) * Math.cos(el) * R, HEAD_C.y + Math.sin(el) * R * 0.97, HEAD_C.z + Math.cos(az) * Math.cos(el) * R * 0.98)); }
    const tg = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts, false, 'catmullrom', 0.1), 40, 0.0045, 5, false); add(tg, M.lash, head, [], { name: 'crack', dirt: false });
  }
  // ---- glasses
  if (P.glasses) {
    const gm = new THREE.MeshPhysicalMaterial({ color: P.glasses, metalness: 0.85, roughness: 0.25, clearcoat: 0.6 });
    const lm = new THREE.MeshPhysicalMaterial({ color: '#eef4ff', roughness: 0.05, transparent: true, opacity: 0.18, clearcoat: 1, depthWrite: false });
    const G = group('gnomeGlasses', head);
    for (const s of [-1, 1]) { const c = [s * 0.12 - NECK.x, 1.0 - NECK.y, 0.355 - NECK.z]; mesh(new THREE.TorusGeometry(eyeR * 1.22, 0.011, 8, 40), gm, { parent: G, pos: c, rot: [0, s * 0.2, 0], cast: false }); mesh(new THREE.CircleGeometry(eyeR * 1.2, 32), lm, { parent: G, pos: [c[0], c[1], c[2] - 0.004], rot: [0, s * 0.2, 0], cast: false, order: 2 });
      mesh(new THREE.CylinderGeometry(0.006, 0.006, 0.3, 6), gm, { parent: G, pos: [s * 0.25 - NECK.x, 1.01 - NECK.y, 0.2 - NECK.z], rot: [Math.PI / 2, s * 0.25, 0], cast: false }); }
    mesh(new THREE.TorusGeometry(0.03, 0.008, 6, 12, Math.PI), gm, { parent: G, pos: [0 - NECK.x, 1.02 - NECK.y, 0.37 - NECK.z], cast: false });
  }
  // ---- hat
  const hatG = group('gnomeHat', head, [0 - NECK.x, 1.1 - NECK.y, -0.005 - NECK.z]); hatG.rotation.set(-0.2, 0, 0.04 * Math.sign(P.hat.bendSide || 1));
  if (P.hat.style === 'fishing') {
    const crown = lathe([[0, 0.24], [0.15, 0.24], [0.25, 0.225], [0.3, 0.18], [0.33, 0.05], [0.345, 0.0], [0.34, -0.012], [0.33, -0.012]], S(64)), brim = lathe([[0.32, 0.0], [0.4, -0.03], [0.49, -0.08], [0.5, -0.09], [0.495, -0.1], [0.4, -0.045], [0.32, -0.015]], S(64));
    hatG.position.y = 1.12 - NECK.y; hatG.rotation.x = -0.12;
    for (const g of [crown, brim]) { smoothNormals(g); bakeAO(g, [], { dirt: false }); mesh(g, M.hat, { parent: hatG, name: 'hatPart' }); }
    const band = new THREE.CylinderGeometry(0.333, 0.345, 0.06, S(64), 1, true); band.translate(0, 0.035, 0); bakeAO(band, [], { dirt: false }); mesh(band, ceramic(shade(P.hat.color, 0.6), P), { parent: hatG });
    const lureM = new THREE.MeshPhysicalMaterial({ color: '#d9b24a', metalness: 0.7, roughness: 0.25, clearcoat: 1 }), lureM2 = new THREE.MeshPhysicalMaterial({ color: '#eceff4', metalness: 0.6, roughness: 0.2, clearcoat: 1 }), red = ceramic('#d8261e', P, { wear: 0 });
    for (const [a, m] of [[0.55, lureM], [-0.85, lureM2]]) { const x = Math.sin(a) * 0.35, z = Math.cos(a) * 0.35; mesh(new THREE.SphereGeometry(0.036, 14, 10), m, { parent: hatG, pos: [x, 0.035, z], rot: [0, a, 0.5], scale: [0.5, 1.25, 0.25] }); }
    const flyM = ceramic('#3f9ad8', P, { wear: 0 }), flyM2 = ceramic('#f2c84a', P, { wear: 0 });
    const fg1 = new THREE.ConeGeometry(0.022, 0.12, 10); bakeAO(fg1, [], { dirt: false }); mesh(fg1, flyM, { parent: hatG, pos: [0.04, 0.07, 0.35], rot: [0.3, 0, -0.9] });
    const fg2 = new THREE.ConeGeometry(0.018, 0.1, 10); bakeAO(fg2, [], { dirt: false }); mesh(fg2, flyM2, { parent: hatG, pos: [0.065, 0.06, 0.35], rot: [0.3, 0, -0.5] });
    const dg = new THREE.SphereGeometry(0.012, 8, 6); bakeAO(dg, [], { dirt: false }); mesh(dg, red, { parent: hatG, pos: [Math.sin(0.55) * 0.37, 0.025, Math.cos(0.55) * 0.37] });
  } else {
    const H = P.hat.height, R0 = 0.31, prof = [];
    for (let i = 0; i <= 44; i++) { const t = (i / 44) * 0.965; prof.push([R0 * Math.pow(1 - t, 0.82) * (1 + 0.07 * Math.sin(Math.PI * t)), t * H]); }
    prof.push([0.012, H * 0.985], [0, H]);
    const g = lathe(prof, S(80)), p = g.attributes.position, bs = P.hat.bendSide, bb = P.hat.bendBack, bdir = V3(bs, 0, -bb).normalize();
    for (let i = 0; i < p.count; i++) {
      let x = p.getX(i), y = p.getY(i), z = p.getZ(i); const t = y / H, rr = Math.hypot(x, z), dx = rr > 1e-5 ? x / rr : 0, dz = rr > 1e-5 ? z / rr : 0;
      const inner = Math.max(0, dx * bdir.x + dz * bdir.z);
      let k = 1 + (plastic ? 0 : 0.05 * Math.sin(t * H * 46) * Math.pow(inner, 1.5) * smooth(0.3, 0.45, t) * (1 - smooth(0.62, 0.8, t)) + 0.012 * noise3(x * 8, y * 6, z * 8, seed + 3));
      x *= k; z *= k;
      const B = Math.pow(Math.max(0, (t - 0.25) / 0.75), 2.2); x += bs * B; z -= bb * B; y -= 0.24 * Math.pow(Math.max(0, (t - 0.45) / 0.55), 3);
      p.setXYZ(i, x, y, z);
    }
    smoothNormals(g); bakeAO(g, [], { dirt: false }); mesh(g, M.hat, { parent: hatG, name: 'hatCone' });
    const brim = new THREE.TorusGeometry(R0 * 0.985, 0.05, S(16), S(80)); brim.rotateX(Math.PI / 2); brim.scale(1, 0.75, 1); brim.translate(0, 0.01, 0); bakeAO(brim, [], { dirt: false }); mesh(brim, M.hat, { parent: hatG, name: 'hatBrim' });
    if (P.hat.dots) { const dm = ceramic(P.hat.dots, P), rd = makeRng(seed + 5), dl = []; for (let i = 0; i < 16; i++) { const t = 0.08 + rd() * 0.62, a = rd() * Math.PI * 2, rad = R0 * Math.pow(1 - t, 0.82) * (1 + 0.07 * Math.sin(Math.PI * t)) * 1.0, B = Math.pow(Math.max(0, (t - 0.25) / 0.75), 2.2);
        dl.push(xf(new THREE.SphereGeometry(0.03 * (1 - t * 0.5), 10, 8), [Math.sin(a) * rad + bs * B, t * H - 0.24 * Math.pow(Math.max(0, (t - 0.45) / 0.55), 3), Math.cos(a) * rad - bb * B], [0, a, 0], [1, 1, 0.35])); }
      const dg = merge(dl); bakeAO(dg, [], { dirt: false }); mesh(dg, dm, { parent: hatG }); }
  }
  // ---- sticker (plastic)
  if (P.sticker) { const st = new THREE.Mesh(new THREE.PlaneGeometry(0.3, 0.15), new THREE.MeshStandardMaterial({ map: stickerTexture(P.sticker), roughness: 0.4, polygonOffset: true, polygonOffsetFactor: -2 })); st.position.set(0.12, P.base ? 0.04 : 0.2, P.base ? 0.505 : 0.43); st.rotation.set(-0.02, 0.22, -0.06); st.name = 'sticker'; body.add(st); }
  // ---- lantern in the right hand
  if (P.lantern !== false) { const L = buildLantern({ plastic }); L.position.set(...A.lantern); body.add(L); }
  if (P.base) { for (const c of body.children) c.position.y += 0.07; add(xf(new THREE.CylinderGeometry(0.46, 0.5, 0.07, S(48)), [0, 0.035, 0.04]), ceramic(plastic ? '#3a9a2a' : '#5c7a3a', P), body, [], { name: 'base', dirt: false }); }
  root.userData.kit = 'gnome'; root.userData.eyes = eyes; root.userData.height = P.height;
  return root;
}

// ---------------- lantern ----------------
// Origin at the ring (top); hangs downward (~0.32 stud). Brass roughness 0.35 metalness 0.7; glass emissive #ffb347.
export function buildLantern({ plastic = false, scale = 1 } = {}) {
  const L = new THREE.Group(); L.name = 'lantern';
  const brass = cached(keyOf('brass', plastic), () => plastic ? new THREE.MeshStandardMaterial({ color: '#2a2a2a', roughness: 0.5 }) : new THREE.MeshPhysicalMaterial({ color: '#b8873a', metalness: 0.7, roughness: 0.35, clearcoat: 0.3 }));
  const dark = cached('lanternDark', () => new THREE.MeshStandardMaterial({ color: '#3a2a1a', metalness: 0.5, roughness: 0.5 }));
  const c = (geo, m, pos, rot, name) => mesh(geo, m, { parent: L, pos, rot, name });
  c(cached('lanRing', () => new THREE.TorusGeometry(0.03, 0.006, 8, 24)), brass, [0, 0, 0], [0, 0, 0]);
  c(cached('lanKnob', () => new THREE.SphereGeometry(0.013, 12, 8)), brass, [0, -0.035, 0]);
  c(cached('lanRoof', () => new THREE.ConeGeometry(0.072, 0.05, 4, 1)), brass, [0, -0.065, 0], [0, Math.PI / 4, 0]);
  c(cached('lanRoofRim', () => new THREE.CylinderGeometry(0.058, 0.058, 0.01, 24)), dark, [0, -0.092, 0]);
  for (let i = 0; i < 4; i++) { const a = i * Math.PI / 2 + Math.PI / 4; c(cached('lanBar', () => new THREE.BoxGeometry(0.01, 0.13, 0.01)), brass, [Math.cos(a) * 0.05, -0.162, Math.sin(a) * 0.05], [0, -a, 0]); }
  const glassMat = new THREE.MeshPhysicalMaterial({ color: plastic ? '#e8c860' : '#ffe2a8', emissive: '#ffb347', emissiveIntensity: 0, roughness: 0.12, clearcoat: plastic ? 0 : 1, transparent: true, opacity: 0.6, depthWrite: false });
  const glass = c(cached('lanGlass', () => new THREE.CylinderGeometry(0.044, 0.044, 0.125, 24, 1, true)), glassMat, [0, -0.162, 0], [0, 0, 0], 'lanternGlass'); glass.renderOrder = 2; glass.castShadow = false;
  const flameMat = new THREE.MeshBasicMaterial({ color: new THREE.Color('#fff0c8'), transparent: true, opacity: 0 });
  const flame = c(cached('lanFlame', () => new THREE.SphereGeometry(0.016, 12, 10)), flameMat, [0, -0.17, 0], [0, 0, 0], 'lanternFlame'); flame.scale.set(1, 1.9, 1); flame.castShadow = false;
  c(cached('lanCandle', () => new THREE.CylinderGeometry(0.012, 0.013, 0.04, 10)), cached('candleMat', () => new THREE.MeshStandardMaterial({ color: '#f3ead6', roughness: 0.6 })), [0, -0.2, 0]);
  c(cached('lanBase', () => new THREE.CylinderGeometry(0.06, 0.066, 0.022, 24)), brass, [0, -0.236, 0]);
  c(cached('lanFoot', () => new THREE.CylinderGeometry(0.068, 0.07, 0.012, 24)), dark, [0, -0.252, 0]);
  const glowTex = radialGlow({ falloff: 2.4 });
  const halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color: '#ffb54d', transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending, fog: false }));
  halo.scale.set(0.9, 0.9, 1); halo.position.set(0, -0.165, 0); halo.renderOrder = 10; halo.name = 'lanternHalo'; L.add(halo);
  const core = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color: '#ffe2a0', transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending, fog: false }));
  core.scale.set(0.3, 0.36, 1); core.position.set(0, -0.165, 0); core.renderOrder = 11; core.name = 'lanternCore'; L.add(core);
  L.scale.setScalar(scale);
  return L;
}
// Light level: 0 unlit, 1 lit (glass emissive x6, point light userData.cd (0.7) cd, halo), >1 boosted (FWOOM 4-6). halo 0..1 = halo fade.
export function setLantern(obj, level = 1, { halo = 1, flicker = 1, light = true } = {}) {
  const L = obj.name === 'lantern' ? obj : obj.getObjectByName('lantern'); if (!L) return;
  const lv = Math.max(0, level) * flicker;
  const glass = L.getObjectByName('lanternGlass'), flame = L.getObjectByName('lanternFlame'), h = L.getObjectByName('lanternHalo'), core = L.getObjectByName('lanternCore');
  const gm = ownMat(glass); gm.emissiveIntensity = 6 * lv; gm.opacity = lv > 0 ? 0.88 : 0.55; gm.color.set(lv > 0 ? '#ffe2a8' : '#8a7448');
  const fm = ownMat(flame); fm.opacity = lv > 0 ? 1 : 0; fm.color.set('#fff0c8').multiplyScalar(lv > 0 ? 5 * Math.min(lv, 3) : 0);
  ownMat(h).opacity = 0.5 * Math.min(lv, 2) * halo; h.scale.setScalar(0.9 * (1 + 0.25 * Math.max(0, lv - 1)));
  ownMat(core).opacity = 0.7 * Math.min(lv, 2) * halo;
  const pl = L.getObjectByName('lanternLight'); if (pl) pl.intensity = light ? (pl.userData.cd ?? 0.7) * lv : 0;
  const pool = obj.getObjectByName('lanternPool'); if (pool) ownMat(pool).opacity = 0.22 * Math.min(lv, 2) * halo;
}
// Light-up beat (bible §3.2): emissive 0 -> 1 in 3 frames, 6-frame overshoot to 1.5, halo fades in over 0.2 s.
export function lanternLightUp(t, t0, fps = 60) { if (t < t0) return { level: 0, halo: 0 }; const f = (t - t0) * fps; const level = f < 3 ? f / 3 : f < 9 ? 1 + 0.5 * Math.sin(Math.PI * (f - 3) / 6) : 1; return { level, halo: anim.seg(t, t0, t0 + 0.2) }; }
export const lanternFlicker = (t, seed = 'lantern') => 1 + 0.06 * anim.wobble(t, seed, 7, 1);

// ---------------- factory + animation API ----------------
export function makeGnome(opts = {}, extra = {}) {
  const P = resolve(typeof opts === 'string' ? { ...GNOME_PRESETS[opts], ...extra, hat: { ...(GNOME_PRESETS[opts]?.hat || {}), ...(extra.hat || {}) }, eyes: { ...(GNOME_PRESETS[opts]?.eyes || {}), ...(extra.eyes || {}) } } : opts);
  const { shadow: _s, pool: _p, units: _u, lanternLight: _l, lantern: _lv, ...shape } = P;
  const shapeKey = keyOf('gnomeTpl', { ...shape, hasLantern: P.lantern !== false });
  const tpl = cached(shapeKey, () => buildGnome(P));
  const model = tpl.clone(true);
  const root = makeRoot('gnome', P.units || opts.units); root.userData.kit = 'gnome';
  const k = P.height / 2.0; model.scale.setScalar(k); root.add(model);
  if (P.shadow !== false) root.add(shadowBlob(1.15 * k, 1.0 * k, 0.4));
  if (P.lantern !== false) {
    const L = root.getObjectByName('lantern');
    if (P.lanternLight) { const pl = new THREE.PointLight('#ffb85c', 0, 0, 2); pl.name = 'lanternLight'; pl.userData.cd = typeof P.lanternLight === 'number' ? P.lanternLight : 0.7; pl.position.set(0, -0.165, 0); L.add(pl); }
    if (P.pool !== false) { const pm = new THREE.MeshBasicMaterial({ map: radialGlow({ falloff: 1.8 }), color: '#ffb870', transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending, polygonOffset: true, polygonOffsetFactor: -3 });
      const pool = new THREE.Mesh(new THREE.PlaneGeometry(3.4, 3.4), pm); pool.rotation.x = -Math.PI / 2; pool.position.set(L.position.x * k, 0.015, L.position.z * k); pool.name = 'lanternPool'; pool.renderOrder = 2; root.add(pool); }
    setLantern(root, typeof P.lantern === 'number' ? P.lantern : 0);
  }
  return root;
}
const G = (root, n) => root.getObjectByName(n);
// Eyelids: closed 0 (open) .. 1 (closed). The blink is a plot point: 2 frames closed (slow blink: 4).
export function setGnomeLids(root, closed = 0) { for (const nm of ['L', 'R']) { const l = G(root, 'lid' + nm); if (l) l.rotation.x = lerp(l.userData.open, l.userData.closed, clamp(closed)); } }
// Blink timeline: times [t0, ...]; frames closed per blink (2 default, 4 slow). slow=true adds a half-closed frame either side.
export function gnomeBlink(t, times, { frames = 2, slow = false, fps = 60 } = {}) {
  for (const t0 of [].concat(times)) { const f = Math.floor((t - t0) * fps + 1e-6); if (slow) { if (f === 0 || f === frames + 1) return 0.55; if (f >= 1 && f <= frames) return 1; } else if (f >= 0 && f < frames) return 1; }
  return 0;
}
// Gaze: rotate both eyeballs (degrees). Painted catchlights rotate with them (it is a statue).
export function setGnomeGaze(root, yaw = 0, pitch = 0) { for (const [nm, s] of [['L', 1], ['R', -1]]) { const b = G(root, 'ball' + nm); if (b) b.rotation.set(-pitch * DEG, -s * 0.18 + yaw * DEG, 0, 'YXZ'); } }
export function setGnomeHead(root, yaw = 0, pitch = 0, roll = 0) { const h = G(root, 'gnomeHead'); if (h) h.rotation.set(-pitch * DEG, yaw * DEG, roll * DEG, 'YXZ'); }
// Stony head turn (bible §3.2): inOutSine over dur with a 2-3° stepped jitter every 3 frames while moving.
export function gnomeHeadTurn(t, t0, dur, from, to, { jitter = 2.5, every = 3, fps = 60 } = {}) {
  const base = anim.tween(t, t0, t0 + dur, from, to, 'inOutSine'); if (t <= t0 || t >= t0 + dur) return base;
  const step = Math.floor((t - t0) * fps / every); return base + (hashFloat(step, 77) * 2 - 1) * jitter;
}
// Gate toddle (line 09): hops of 0.1 stud at 2.5 Hz with ±8° roll. Returns { y (studs), roll (deg) } to apply to the root.
export function gnomeHop(t, t0 = 0, { height = 0.1, freq = 2.5, roll = 8 } = {}) { if (t < t0) return { y: 0, roll: 0 }; const ph = (t - t0) * freq; return { y: height * Math.abs(Math.sin(Math.PI * ph)), roll: roll * Math.sin(Math.PI * ph) }; }
// Statue "breath": creatures are never frozen (bible §3.3) - a 1 Hz micro sway for idle shots.
export function gnomeIdle(root, t, { amp = 0.6, seed = 'gnome' } = {}) { const b = G(root, 'gnomeBody'); if (b) b.rotation.z = amp * DEG * anim.wobble(t, seed, 0.5, 1); }
export function makeFamilyGnome(i = 0, extra = {}) { const f = FAMILY_GNOMES[((i % FAMILY_GNOMES.length) + FAMILY_GNOMES.length) % FAMILY_GNOMES.length]; return makeGnome({ lod: 'mid', ...f, ...extra, hat: { ...(f.hat || {}), ...(extra.hat || {}) } }); }
export function makePlasticGnome(extra = {}) { return makeGnome({ ...GNOME_PRESETS.plastic, ...extra, hat: { ...GNOME_PRESETS.plastic.hat, ...(extra.hat || {}) }, eyes: { style: 'dead' } }); }
