// Character kit: shared helpers (canvas textures, persistent caches, mesh/material helpers, seeded noise).
// Kit units: 1 unit = 1 Roblox stud. Builders return a root Group scaled by STUD (0.32 m) unless { units: 'stud' }.
import * as THREE from 'three';
import { makeRng, hash32, noise3, fbm3 } from '../core/random.js';

export { THREE, makeRng, hash32, noise3, fbm3 };
export const STUD = 0.32;
export const DEG = Math.PI / 180;
export const clamp = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
export const lerp = (a, b, t) => a + (b - a) * t;
export const smooth = (a, b, x) => { const u = clamp((x - a) / (b - a)); return u * u * (3 - 2 * u); };

// ---------------- persistent caches (survive the engine's per-shot disposal) ----------------
const _cache = new Map();
export function persist(res) {
  if (!res) return res;
  if (res.isObject3D) { res.traverse((o) => { if (o.geometry) persist(o.geometry); if (o.material) [].concat(o.material).forEach(persist); }); return res; }
  res.userData = Object.assign(res.userData || {}, { persistent: true });
  if (res.isMaterial) for (const k in res) { const v = res[k]; if (v && v.isTexture) v.userData = Object.assign(v.userData || {}, { persistent: true }); }
  return res;
}
// cached(key, fn): build once per worker; textures / geometries / materials returned are marked persistent.
export function cached(key, fn) {
  if (_cache.has(key)) return _cache.get(key);
  const v = fn();
  if (v && (v.isTexture || v.isMaterial || v.isBufferGeometry || v.isObject3D)) persist(v);
  else if (v && typeof v === 'object') for (const k in v) { const x = v[k]; if (x && (x.isTexture || x.isMaterial || x.isBufferGeometry)) persist(x); }
  _cache.set(key, v); return v;
}
export const keyOf = (...a) => a.map((x) => (typeof x === 'object' ? JSON.stringify(x) : String(x))).join('|');

// ---------------- canvas ----------------
export function canvas(w, h = w) { const c = document.createElement('canvas'); c.width = Math.max(1, Math.round(w)); c.height = Math.max(1, Math.round(h)); return c; }
export function canvasTex(c, { srgb = true, wrap = false, repeat = null, aniso = 8, mips = true } = {}) {
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  if (wrap) t.wrapS = t.wrapT = THREE.RepeatWrapping; else t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
  if (repeat) t.repeat.set(repeat[0], repeat[1]);
  t.anisotropy = aniso; t.generateMipmaps = mips; t.minFilter = mips ? THREE.LinearMipmapLinearFilter : THREE.LinearFilter;
  t.needsUpdate = true; t.userData.persistent = true;
  return t;
}
// Colour helpers (display-space hex strings)
export function hex(c) { return '#' + new THREE.Color(c).getHexString(); }
export function rgb(c) { const k = new THREE.Color(); k.setStyle(c, THREE.NoColorSpace); return [k.r * 255, k.g * 255, k.b * 255]; }
export function rgba(c, a) { const [r, g, b] = rgb(c); return `rgba(${r | 0},${g | 0},${b | 0},${a})`; }
// shade(c, k): k < 1 darkens, k > 1 lightens toward white (display space)
export function shade(c, k) {
  const [r, g, b] = rgb(c);
  const f = (v) => (k <= 1 ? v * k : v + (255 - v) * (k - 1));
  return '#' + [f(r), f(g), f(b)].map((v) => Math.round(clamp(v, 0, 255)).toString(16).padStart(2, '0')).join('');
}
export function mix(a, b, t) { const A = rgb(a), B = rgb(b); return '#' + A.map((v, i) => Math.round(v + (B[i] - v) * t).toString(16).padStart(2, '0')).join(''); }
export function saturate(c, k) { const col = new THREE.Color(); col.setStyle(c, THREE.NoColorSpace); const hsl = {}; col.getHSL(hsl); col.setHSL(hsl.h, clamp(hsl.s * k), hsl.l); return '#' + col.getHexString(THREE.NoColorSpace); }

// A small tileable grey noise canvas used as a fabric / plastic grain pattern (drawn with low alpha).
export function grainCanvas(size = 96, seed = 7, contrast = 1) {
  return cached('grain' + size + '_' + seed + '_' + contrast, () => {
    const c = canvas(size), g = c.getContext('2d'), id = g.createImageData(size, size), r = makeRng(seed);
    const L = new Float32Array(size * size); for (let i = 0; i < L.length; i++) L[i] = r();
    // blur once for a softer weave
    for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
      let s = 0; for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) s += L[((y + dy + size) % size) * size + ((x + dx + size) % size)];
      const v = clamp(0.5 + (s / 9 - 0.5) * 2.2 * contrast) * 255, i = (y * size + x) * 4; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 255;
    }
    g.putImageData(id, 0, 0); return { canvas: c };
  }).canvas;
}

// ---------------- mesh / material helpers ----------------
export function mesh(geo, mat, { pos, rot, scale, parent, name, cast = true, receive = true, order } = {}) {
  const m = new THREE.Mesh(geo, mat);
  if (pos) m.position.set(pos[0], pos[1], pos[2]);
  if (rot) m.rotation.set(rot[0], rot[1], rot[2], rot[3] || 'XYZ');
  if (scale != null) (typeof scale === 'number' ? m.scale.setScalar(scale) : m.scale.set(scale[0], scale[1], scale[2]));
  if (name) m.name = name; m.castShadow = cast; m.receiveShadow = receive; if (order != null) m.renderOrder = order;
  if (parent) parent.add(m); return m;
}
export function group(name, parent, pos) { const g = new THREE.Group(); g.name = name || ''; if (pos) g.position.set(pos[0], pos[1], pos[2]); if (parent) parent.add(g); return g; }
// Cached materials (shared, persistent): treat as read-only.
export const stdMat = (color, rough = 0.55, extra = {}) => cached(keyOf('std', color, rough, extra), () => new THREE.MeshStandardMaterial({ color, roughness: rough, metalness: 0, ...extra }));
export const physMat = (color, opts = {}) => cached(keyOf('phys', color, opts), () => new THREE.MeshPhysicalMaterial({ color, roughness: 0.4, ...opts }));

// Bake a matrix into a geometry clone (keeps the cache original intact).
export function baked(geo, { pos = [0, 0, 0], rot = [0, 0, 0], scale = [1, 1, 1] } = {}) {
  const g = geo.clone(); const m = new THREE.Matrix4().compose(new THREE.Vector3(...pos), new THREE.Quaternion().setFromEuler(new THREE.Euler(...rot)), new THREE.Vector3(...(typeof scale === 'number' ? [scale, scale, scale] : scale)));
  g.applyMatrix4(m); return g;
}

// Teardrop "clump" (UGC hair / beard strand): unit sphere stretched along -y into a tapered, bent tip.
// R radius of the root ball, L length of the tail, bend sideways (x) as a fraction of L, curl forward (z).
export function clumpGeo(R, L, bend = 0, curl = 0, seg = 16, taper = 0.8) {
  const g = new THREE.SphereGeometry(1, seg, Math.max(6, Math.round(seg * 0.75))), p = g.attributes.position;
  for (let i = 0; i < p.count; i++) {
    let x = p.getX(i), y = p.getY(i), z = p.getZ(i);
    if (y < 0) { const t = -y; const k = 1 - taper * Math.pow(t, 1.6); x *= k; z *= k; y = -t * L / R; }
    x *= R; z *= R; y *= R;
    const t = clamp(-y / L); x += bend * t * t * L; z += curl * t * t * L;
    p.setXYZ(i, x, y, z);
  }
  g.computeVertexNormals(); return g;
}

// Vertex-colour baking: per-vertex multiplier from a function f(worldPos, normal) -> [r,g,b] (0..1).
export function bakeVertexColors(geo, f) {
  const p = geo.attributes.position, n = geo.attributes.normal, N = p.count, col = new Float32Array(N * 3);
  const P = new THREE.Vector3(), Nn = new THREE.Vector3();
  for (let i = 0; i < N; i++) { P.fromBufferAttribute(p, i); Nn.fromBufferAttribute(n, i); const c = f(P, Nn); col[i * 3] = c[0]; col[i * 3 + 1] = c[1]; col[i * 3 + 2] = c[2]; }
  geo.setAttribute('color', new THREE.BufferAttribute(col, 3)); return geo;
}

// Soft contact-shadow blob (the bible's fake contact shadow: radial gradient, opacity 0.3-0.4, 1.2x footprint).
export function shadowBlobTexture() {
  return cached('shadowBlob', () => {
    const N = 128, c = canvas(N), g = c.getContext('2d'), gr = g.createRadialGradient(N / 2, N / 2, 0, N / 2, N / 2, N / 2);
    gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(0.45, 'rgba(0,0,0,0.75)'); gr.addColorStop(0.8, 'rgba(0,0,0,0.18)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = gr; g.fillRect(0, 0, N, N); return canvasTex(c, { srgb: false });
  });
}
export function shadowBlob(w, d, opacity = 0.36, color = '#1a0f22') {
  const m = new THREE.MeshBasicMaterial({ map: shadowBlobTexture(), color, transparent: true, opacity, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -4 });
  const s = new THREE.Mesh(new THREE.PlaneGeometry(w, d), m); s.rotation.x = -Math.PI / 2; s.position.y = 0.01; s.name = 'shadowBlob'; s.renderOrder = 1; s.castShadow = false; s.receiveShadow = false;
  return s;
}

// Root wrapper: content in studs, root scaled to metres unless units === 'stud'.
export function makeRoot(name, units = 'm') { const r = new THREE.Group(); r.name = name; if (units !== 'stud') r.scale.setScalar(STUD); return r; }

// Per-instance material: materials are shared by ctx.instance() clones; before mutating one (face swap, lantern
// level), make sure this mesh owns its copy. Ownership is tracked by mesh uuid (clones get new uuids).
export function ownMat(meshObj) {
  const m = meshObj.material;
  if (m.userData.owner !== meshObj.uuid) { const c = m.clone(); c.userData = { owner: meshObj.uuid }; meshObj.material = c; return c; }
  return m;
}
export function claimMat(meshObj) { meshObj.material.userData.owner = meshObj.uuid; return meshObj.material; }
