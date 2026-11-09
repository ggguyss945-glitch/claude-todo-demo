// EP01 creatures + held props (ASSETS.md "CREATURES + CAST"):
//   the GIANT STAR-NOSED MOLES (second hero creature) + the shared MOUND FIELD, next door's dog REX, Theo's stuffed whale,
//   Grandpa's flashlight. (Theo's "6" badge and every new human live in cast.js; theoAt / badge are re-exported here.)
//
//   import * as C from '../../kit/creatures.js'
//   const m = C.makeMole({ scale: 1, seed: 3 });            // root in metres (content in studs), mound centred at the origin, facing +z
//   update: C.animateMole(m, t, { rise: 0.1, unfurl: 0.4, eyesOn: 0.5, flash: 0.9, recoil: 1.3, sink: 1.8 })
//      or:  C.setMole(m, { t, rise, open, recoil, sniff, emerge, eyes, flash, look })   (all pure functions of t)
//   const f = C.moleField(ctx, { center, size, yaw }); f.add(...); f.rise(i, t0); f.travel(i, path, t0, speed); ... f.update(t)
//   const d = C.makeDog(); C.dogAt(d, t, { pose: 'lie', chew: true })
//   const w = C.stuffedWhale(); C.holdWhale(theo, w, 'hug')
//   const fl = C.makeFlashlight(); C.holdFlashlight(grandpa, fl); C.setFlashlight(fl, 1)
//
// VISUAL_BIBLE §2.6 (creature rules: sculpted, glossy, out-detailed, cute silhouette + creepy details, never frozen),
// §3.2 (moles: 2-4 studs/s bulge wave, tentacles wriggle +-10 deg at 2-3 Hz, recoil = 0.15 s spring snap, sink = 0.5 s
// deflate, eyes wink out pair by pair). Deterministic: seeded, no Math.random; every animation is a pure function of t.
// Geometry/materials/textures are cached per worker (persistent); per-instance state (tentacle geometry, eye level
// materials) is owned per mesh (clones from ctx.instance() get their own copy on first use).
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { STUD, DEG, cached, keyOf, mesh, group, makeRoot, canvas, canvasTex, makeRng, hash32, noise3, clamp, lerp, smooth, shade, mix, rgba, shadowBlob, ownMat } from './util.js';
import { M, TILE } from './kitlib.js';
import { radialGlow, sparkle as sparkleTex, fbm as fbmTile, dirt as dirtTex, fabric as fabricTex, normalFromHeight } from '../core/textures.js';
import { noise2 } from '../core/random.js';
import * as anim from '../core/anim.js';
import { rig, handSocket, headGeo, faceBandGeo } from './avatar.js';
import { atlasUV, faceRects } from './clothing.js';
export { theoAt, makeBadge6, addBadge6 } from './cast.js';

const PI = Math.PI;
const V3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const sat = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
const gauss = (x) => Math.exp(-x * x);

// ------------------------------------------------------------------ small shared helpers
function xform(geo, pos = [0, 0, 0], rot = [0, 0, 0], scale = [1, 1, 1], order = 'XYZ') {
  const m = new THREE.Matrix4().compose(V3(...pos), new THREE.Quaternion().setFromEuler(new THREE.Euler(rot[0], rot[1], rot[2], order)), V3(...(typeof scale === 'number' ? [scale, scale, scale] : scale)));
  geo.applyMatrix4(m); return geo;
}
const strip = (g, keep = ['position', 'normal', 'uv']) => { for (const k of Object.keys(g.attributes)) if (!keep.includes(k)) g.deleteAttribute(k); return g; };
const mergeList = (list, keep) => mergeGeometries(list.map((x) => strip(x.index ? x.toNonIndexed() : x, keep)));
// Constant on-screen size sprite (output pixels of the 1080x1920 frame; same convention as fx.js / common.pxSprite).
function pxSprite(mat, px = 20) {
  const s = new THREE.Sprite(mat); s.userData.px = px; s.frustumCulled = false;
  s.onBeforeRender = function (r, sc, cam) { const k = (this.userData.px * 2) / (1920 * cam.projectionMatrix.elements[5]); const w = this.parent ? this.parent.getWorldScale(_ws) : _ws.set(1, 1, 1); this.scale.set(k / w.x, k / w.y, 1); this.updateMatrixWorld(); };
  return s;
}
const _ws = new THREE.Vector3();
const addMat = (map, color, o = {}) => new THREE.SpriteMaterial({ map, color, blending: THREE.AdditiveBlending, depthWrite: false, depthTest: true, transparent: true, fog: false, sizeAttenuation: false, ...o });
// Smooth normals welded across UV seams (sphere / lathe seams would otherwise show).
function smoothNormals(g) {
  const pos = g.attributes.position, n = pos.count, idx = g.index ? g.index.array : null, T = idx ? idx.length : n;
  const kk = (i) => Math.round(pos.getX(i) * 2e4) + ',' + Math.round(pos.getY(i) * 2e4) + ',' + Math.round(pos.getZ(i) * 2e4);
  const keys = new Array(n), acc = new Map(); for (let i = 0; i < n; i++) { keys[i] = kk(i); if (!acc.has(keys[i])) acc.set(keys[i], [0, 0, 0]); }
  const a = V3(), b = V3(), c = V3(), e1 = V3(), e2 = V3();
  for (let t = 0; t < T; t += 3) { const i0 = idx ? idx[t] : t, i1 = idx ? idx[t + 1] : t + 1, i2 = idx ? idx[t + 2] : t + 2;
    a.fromBufferAttribute(pos, i0); b.fromBufferAttribute(pos, i1); c.fromBufferAttribute(pos, i2); e1.subVectors(b, a); e2.subVectors(c, a); e1.cross(e2);
    for (const i of [i0, i1, i2]) { const v = acc.get(keys[i]); v[0] += e1.x; v[1] += e1.y; v[2] += e1.z; } }
  const nr = new Float32Array(n * 3); for (let i = 0; i < n; i++) { const v = acc.get(keys[i]), l = Math.hypot(v[0], v[1], v[2]) || 1; nr[i * 3] = v[0] / l; nr[i * 3 + 1] = v[1] / l; nr[i * 3 + 2] = v[2] / l; }
  g.setAttribute('normal', new THREE.BufferAttribute(nr, 3)); return g;
}
// Lathe around the z axis: profile [[r, z], ...] (z from back to front); fy flattens vertically.
function zLathe(prof, seg = 48, fy = 1) {
  const g = new THREE.LatheGeometry(prof.map(([r, z]) => new THREE.Vector2(r, z)), seg); g.rotateX(PI / 2); // lathe y -> +z
  g.scale(1, fy, 1); return smoothNormals(g);
}
// Tapered swept tube along points (claws, fins).
function taperTube(pts, r0, r1, radial = 12, tubular = 16, capTip = true) {
  const curve = new THREE.CatmullRomCurve3(pts.map((p) => V3(...p)), false, 'centripetal');
  const g = new THREE.TubeGeometry(curve, tubular, 1, radial, false), p = g.attributes.position, C = V3();
  for (let i = 0; i <= tubular; i++) { const t = i / tubular; curve.getPointAt(t, C); let r = lerp(r0, r1, Math.pow(t, 0.8)); if (capTip && t > 0.85) r *= Math.sqrt(Math.max(0, 1 - ((t - 0.85) / 0.15) ** 2)) * 0.9 + 0.1 * (1 - t); for (let j = 0; j <= radial; j++) { const k = i * (radial + 1) + j; p.setXYZ(k, C.x + (p.getX(k) - C.x) * r, C.y + (p.getY(k) - C.y) * r, C.z + (p.getZ(k) - C.z) * r); } }
  return smoothNormals(g);
}
function dataTex(data, size, srgb, wrap = true) {
  const t = new THREE.DataTexture(data, size, size, THREE.RGBAFormat, THREE.UnsignedByteType);
  t.wrapS = t.wrapT = wrap ? THREE.RepeatWrapping : THREE.ClampToEdgeWrapping; t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearMipmapLinearFilter; t.generateMipmaps = true;
  t.anisotropy = 8; t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace; t.needsUpdate = true; t.userData.persistent = true; return t;
}

// ==================================================================================================================
//  MOLES
// ==================================================================================================================
// Size / variation presets for "dozens": scale = whole creature (1 = lawn mound 3 studs across); hue/tint per preset.
export const MOLE_PRESETS = {
  lawn: { scale: 1 },                          // the standard lawn mound (3.0 x 0.75 studs)
  small: { scale: 0.72, snout: '#ea96aa' },    // young ones in the crowd
  runt: { scale: 0.58, snout: '#f0a2b4' },
  old: { scale: 1.15, snout: '#d97f96', fur: '#2e2630' },
  big: { scale: 1.8 },                          // "BIG ones": the hero snout cheat (bible 2.6 #6)
  giant: { scale: 2.4 },                        // a monster-sized one for a single frame-filling shot
};
const MOLE_DEFAULTS = { scale: 1, seed: 1, lod: 'hero', mound: true, crumbs: true, blades: true, claws: true, body: true, snout: '#f6a2b0', fur: '#322c3a', eyeColor: '#ffa416', shadow: true };
const LODS = { hero: { tub: 14, rad: 10, blades: 240, crumbs: 36, grid: 56 }, mid: { tub: 10, rad: 7, blades: 110, crumbs: 24, grid: 40 }, low: { tub: 6, rad: 5, blades: 0, crumbs: 12, grid: 24 } };

// --- mound shape (studs, scale 1): an elongated dome 3.0 across x 0.75 high, the head pushes out at the front (+z)
const MOUND = { Rx: 1.42, Rz: 1.56, H: 0.82 };
const HEAD_AT = { y: 0.12, z: 0.72 }; // head centre in mound space (emerge 0: the head stays under the turf, eyes + snout break it)
function moundHeight(x, z, seed) {
  const r = Math.hypot(x / MOUND.Rx, z / MOUND.Rz); if (r >= 1) return 0;
  const lump = 1 + 0.14 * noise3(x * 1.6, 0.3, z * 1.6, seed) + 0.06 * noise3(x * 4.2, 1.7, z * 4.2, seed + 3);
  const crest = Math.pow(1 - r * r, 1.55) * (1 + 0.12 * Math.exp(-((z + 0.25) ** 2) * 2)); // crest a little behind the middle
  return MOUND.H * crest * lump;
}
// Eye centre in mound space at emerge 0 (from the head sculpt), used to cut the eye holes.
const EYE_M = { get x() { return eyeFrame().c.x; }, get y() { return HEAD_AT.y + eyeFrame().c.y; }, get z() { return HEAD_AT.z + eyeFrame().c.z; } };
// Crack polylines radiating from near the crest (avoid the front opening).
function moundCracks(seed) {
  const r = makeRng(hash32('moleCracks', seed)), n = 3 + Math.floor(r() * 3), out = [];
  for (let i = 0; i < n; i++) {
    let a = (i / n) * 2 * PI + r() * 0.9 + 0.4; if (Math.abs(((a % (2 * PI)) + 2 * PI) % (2 * PI) - 0) < 0.55 || Math.abs(((a % (2 * PI)) + 2 * PI) % (2 * PI) - 2 * PI) < 0.55) a += 0.9; // keep off +z
    const pts = [[(r() - 0.5) * 0.35, (r() - 0.5) * 0.35 - 0.15]]; const L = 0.55 + r() * 0.55, segs = 4;
    for (let k = 1; k <= segs; k++) { const d = (L * k) / segs, j = (r() - 0.5) * 0.35; pts.push([pts[0][0] + Math.sin(a + j) * d, pts[0][1] + Math.cos(a + j) * d]); }
    out.push({ pts, w: 0.05 + r() * 0.035 });
  }
  return out;
}
function distSeg(px, pz, ax, az, bx, bz) { const vx = bx - ax, vz = bz - az, l2 = vx * vx + vz * vz; const u = l2 > 0 ? sat(((px - ax) * vx + (pz - az) * vz) / l2) : 0; return [Math.hypot(px - ax - vx * u, pz - az - vz * u), u]; }

// Turf material: the lawn's own grass texture, mapped in WORLD xz (tile = TILE.lawn studs) so mounds and the field match
// the lawn anywhere; `soil` attribute mixes in dark wet soil (lower roughness), `turfAlpha` fades the rim into the lawn.
export function turfMaterial({ tile = TILE.lawn, soilScale = 3.2, wet = 0.45 } = {}) {
  return cached(keyOf('ep01TurfMat', tile, soilScale, wet), () => {
    const L = M('lawn');
    const D = dirtTex({ color: '#4c3020', dark: '#1e120a', pebble: '#6a5644', pebbles: 140, seed: 11, normal: 3 });
    const m = new THREE.MeshStandardMaterial({ map: L.map, normalMap: L.normalMap, normalScale: L.normalScale ? L.normalScale.clone() : new THREE.Vector2(1, 1), roughnessMap: L.roughnessMap,
      roughness: 1, color: L.color.clone(), vertexColors: true, transparent: true, depthWrite: true, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1 });
    m.onBeforeCompile = (sh) => {
      sh.uniforms.uTile = { value: tile * STUD }; sh.uniforms.uSoilMap = { value: D.map }; sh.uniforms.uSoilScale = { value: soilScale }; sh.uniforms.uWet = { value: wet };
      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', '#include <common>\nattribute float soil;\nattribute float turfAlpha;\nvarying float vSoil;\nvarying float vTurfA;\nvarying vec2 vWUv;\nuniform float uTile;')
        .replace('#include <fog_vertex>', '#include <fog_vertex>\n{ vec4 wq = modelMatrix * vec4(transformed, 1.0); vWUv = wq.xz / uTile; vMapUv = vWUv; vNormalMapUv = vWUv; vRoughnessMapUv = vWUv; }\nvSoil = soil; vTurfA = turfAlpha;');
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', '#include <common>\nuniform sampler2D uSoilMap;\nuniform float uSoilScale;\nuniform float uWet;\nvarying float vSoil;\nvarying float vTurfA;\nvarying vec2 vWUv;')
        .replace('#include <map_fragment>', '#include <map_fragment>\n{ vec3 sc = texture2D(uSoilMap, vWUv * uSoilScale).rgb; float k = clamp(vSoil, 0.0, 1.0); diffuseColor.rgb = mix(diffuseColor.rgb, sc * 1.15, k); diffuseColor.a *= clamp(vTurfA, 0.0, 1.0); }')
        .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\nroughnessFactor = mix(roughnessFactor, uWet, clamp(vSoil, 0.0, 1.0) * 0.9);');
    };
    m.customProgramCacheKey = () => 'ep01turf';
    return m;
  });
}
// Dark soil lumps (crumbs) material + geometry.
const crumbMat = () => cached('ep01CrumbMat', () => { const D = dirtTex({ color: '#4c3020', dark: '#1e120a', pebble: '#6a5644', pebbles: 140, seed: 11, normal: 3 }); return new THREE.MeshStandardMaterial({ map: D.map, normalMap: D.normalMap, roughness: 0.78, color: '#ffffff' }); });
const crumbGeo = () => cached('ep01CrumbGeo', () => { const g = new THREE.IcosahedronGeometry(1, 1); const p = g.attributes.position; for (let i = 0; i < p.count; i++) { const v = V3(p.getX(i), p.getY(i), p.getZ(i)); const k = 1 + 0.28 * noise3(v.x * 2.1, v.y * 2.1, v.z * 2.1, 5); p.setXYZ(i, v.x * k, v.y * k * 0.72, v.z * k); } g.computeVertexNormals(); return g; });
// Grass blade (same shape as props.grassBlades) + material.
const bladeGeo = () => cached('ep01BladeGeo', () => {
  const g = new THREE.BufferGeometry(); const P = [-0.032, 0, 0, 0.032, 0, 0, -0.02, 0.5, 0.06, 0.02, 0.5, 0.06, 0, 1, 0.2];
  g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3)); g.setIndex([0, 1, 2, 1, 3, 2, 2, 3, 4, 0, 2, 1, 1, 2, 3, 2, 4, 3]);
  g.setAttribute('color', new THREE.Float32BufferAttribute([0.78, 0.78, 0.78, 0.78, 0.78, 0.78, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 1.12, 1.12, 1.12], 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(Array.from({ length: 5 }, () => [0, 0.97, 0.24]).flat(), 3)); return g;
});
const bladeMat = () => cached('ep01BladeMat', () => new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.9 }));

// Mound geometry (cached per seed/lod): position, normal, uv, soil, turfAlpha, color.
function moundGeometry(seed, lod) {
  return cached(keyOf('ep01MoundGeo', seed, lod), () => {
    const N = LODS[lod].grid, ext = 1.62; const g = new THREE.PlaneGeometry(ext * 2, ext * 2, N, N); g.rotateX(-PI / 2);
    const p = g.attributes.position, n = p.count, soil = new Float32Array(n), alpha = new Float32Array(n), col = new Float32Array(n * 3);
    const cracks = moundCracks(seed);
    for (let i = 0; i < n; i++) {
      const x = p.getX(i), z = p.getZ(i); let h = moundHeight(x, z, seed); let s = 0;
      const r = Math.hypot(x / MOUND.Rx, z / MOUND.Rz);
      // cracks: a 3-5 split turf, wet soil inside, the lips a touch raised
      for (const c of cracks) for (let k = 1; k < c.pts.length; k++) { const [d, u] = distSeg(x, z, c.pts[k - 1][0], c.pts[k - 1][1], c.pts[k][0], c.pts[k][1]); const w = c.w * (1 - 0.55 * ((k - 1 + u) / (c.pts.length - 1))); if (d < w * 2.2) { const core = 1 - smooth(w * 0.45, w, d); s = Math.max(s, core * smooth(1.0, 0.75, r)); h += (core > 0 ? -0.06 * core : 0) + 0.018 * Math.exp(-(((d - w * 1.25) / (w * 0.5)) ** 2)) * smooth(1.0, 0.7, r); } }
      // the front opening where the snout breaks the turf: a torn soil ring, turf pressed down inside it
      const ex = x / 0.36, ez = (z - (HEAD_AT.z + 0.52)) / 0.3, e = Math.hypot(ex, ez);
      if (e < 1.5) { s = Math.max(s, smooth(0.55, 0.9, e) * smooth(1.5, 1.05, e)); h = Math.min(h, lerp(0.1, h, smooth(0.75, 1.3, e))) + 0.035 * Math.exp(-(((e - 1.08) / 0.18) ** 2)); }
      // eye holes: the reflectors sit in two round, soil-ringed holes in the turf
      for (const sg of [1, -1]) { const d = Math.hypot(x - sg * EYE_M.x, z - EYE_M.z) / (EYE.r * 1.25); if (d < 1.9) { s = Math.max(s, smooth(0.7, 1.0, d) * smooth(1.9, 1.15, d)); h = Math.min(h, lerp(EYE_M.y - 0.03, h, smooth(0.85, 1.4, d))) + 0.03 * Math.exp(-(((d - 1.2) / 0.22) ** 2)); } }
      // torn rim: a broken soil band where the turf lifts off the lawn
      const rimN = 0.5 + 0.5 * noise3(x * 3.1, 2.2, z * 3.1, seed + 9); s = Math.max(s, smooth(0.8, 0.9, r) * smooth(1.0, 0.92, r) * smooth(0.45, 0.75, rimN) * 0.85);
      p.setY(i, Math.max(0, h)); soil[i] = s; alpha[i] = smooth(1.06, 0.93, r);
      const ao = (1 - 0.22 * smooth(0.7, 1.0, r)) * (1 - 0.35 * s); col[i * 3] = ao; col[i * 3 + 1] = ao; col[i * 3 + 2] = ao;
    }
    g.setAttribute('soil', new THREE.BufferAttribute(soil, 1)); g.setAttribute('turfAlpha', new THREE.BufferAttribute(alpha, 1)); g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    g.computeVertexNormals(); const nn = g.attributes.normal; for (let i = 0; i < n; i++) { const k = 0.62 + 0.38 * Math.pow(Math.max(0, nn.getY(i)), 1.5); col[i * 3] *= k; col[i * 3 + 1] *= k; col[i * 3 + 2] *= k; }
    g.computeBoundingSphere(); g.userData.cracks = cracks; return g;
  });
}

// --- textures: velvet fur strands, snout (blush + Eimer's-organ dots), reflector (hex cube-corner cells)
const furTex = () => cached('ep01FurTex', () => {
  const S = 256, r = makeRng(77), h = new Float32Array(S * S), base = fbmTile(S, 8, 3, 7);
  for (let i = 0; i < S * S; i++) h[i] = base[i] * 0.4;
  for (let k = 0; k < 5200; k++) { const x0 = r() * S, y0 = r() * S, L = 4 + r() * 7, a = PI / 2 + (r() - 0.5) * 0.5, v = 0.35 + r() * 0.65; for (let s = 0; s < L; s += 0.5) { const x = Math.floor(x0 + Math.cos(a) * s + S) % S, y = Math.floor(y0 + Math.sin(a) * s + S) % S; h[y * S + x] = Math.max(h[y * S + x], v * (1 - s / L)); } }
  const nm = normalFromHeight(h, S, 1.6); const col = new Uint8Array(S * S * 4);
  for (let i = 0; i < S * S; i++) { const v = 0.82 + 0.3 * h[i] + 0.12 * (base[i] - 0.5); col[i * 4] = col[i * 4 + 1] = col[i * 4 + 2] = Math.round(sat(v) * 255); col[i * 4 + 3] = 255; }
  return { normal: dataTex(nm, S, false), map: dataTex(col, S, true) };
});
const snoutTex = () => cached('ep01SnoutTex', () => {
  const S = 256, r = makeRng(31), h = new Float32Array(S * S), col = new Uint8Array(S * S * 4), mott = fbmTile(S, 6, 3, 9);
  for (let k = 0; k < 900; k++) { const cx = r() * S, cy = r() * S, rad = 1.6 + r() * 1.6; for (let dy = -3; dy <= 3; dy++) for (let dx = -3; dx <= 3; dx++) { const d = Math.hypot(dx, dy) / rad; if (d > 1) continue; const x = (Math.floor(cx) + dx + S) % S, y = (Math.floor(cy) + dy + S) % S; h[y * S + x] = Math.max(h[y * S + x], Math.sqrt(1 - d * d)); } }
  for (let i = 0; i < S * S; i++) { const v = 0.9 + 0.16 * (mott[i] - 0.5) - 0.1 * h[i]; const pk = [1.0, 0.86, 0.9]; col[i * 4] = Math.round(sat(v * pk[0]) * 255); col[i * 4 + 1] = Math.round(sat(v * pk[1]) * 255); col[i * 4 + 2] = Math.round(sat(v * pk[2]) * 255); col[i * 4 + 3] = 255; }
  return { normal: dataTex(normalFromHeight(h, S, 2.2), S, false), map: dataTex(col, S, true) };
});
// Nostril disc map (planar, clamp): two dark nostrils, a rosy centre, a darker rim.
const discTex = () => cached('ep01DiscTex', () => {
  const N = 256, c = canvas(N), g = c.getContext('2d'); const gr = g.createRadialGradient(N / 2, N / 2, 4, N / 2, N / 2, N / 2);
  gr.addColorStop(0, '#f8c6d0'); gr.addColorStop(0.6, '#f0a8b8'); gr.addColorStop(1, '#ec9fb2'); g.fillStyle = gr; g.fillRect(0, 0, N, N);
  // fleshy radial creases (they also break up any 'face' read), then two small slit nostrils close together
  for (let k = 0; k < 22; k++) { const a = (k / 22) * 2 * PI; g.strokeStyle = 'rgba(150,50,80,0.28)'; g.lineWidth = 3; g.beginPath(); g.moveTo(N / 2 + Math.cos(a) * N * 0.16, N / 2 + Math.sin(a) * N * 0.16); g.lineTo(N / 2 + Math.cos(a) * N * 0.49, N / 2 + Math.sin(a) * N * 0.49); g.stroke(); }
  for (const s of [-1, 1]) { const x = N / 2 + s * N * 0.06, y = N * 0.5; g.save(); g.translate(x, y); g.rotate(s * 0.25); const ng = g.createRadialGradient(0, 0, 1, 0, 0, N * 0.05); ng.addColorStop(0, '#4a1020'); ng.addColorStop(0.65, '#8a3048'); ng.addColorStop(1, 'rgba(200,100,130,0)'); g.fillStyle = ng; g.beginPath(); g.ellipse(0, 0, N * 0.016, N * 0.045, 0, 0, 2 * PI); g.fill(); g.restore(); }
  const r = makeRng(5); for (let i = 0; i < 260; i++) { const a = r() * 2 * PI, d = Math.sqrt(r()) * N * 0.48; g.fillStyle = rgba('#ffffff', 0.08 + r() * 0.12); g.beginPath(); g.arc(N / 2 + Math.cos(a) * d, N / 2 + Math.sin(a) * d, 1.2 + r() * 1.6, 0, 2 * PI); g.fill(); }
  return canvasTex(c, { srgb: true });
});
// Bike-reflector eye: hexagonal cube-corner cells (7 across), each split in 3 rhombi of different brightness with a hot
// centre, inside a round bezel. Used as map AND emissive map.
export const reflectorTexture = () => cached('ep01ReflectorTex', () => {
  const N = 512, c = canvas(N), g = c.getContext('2d'), R = N / 2; g.fillStyle = '#2a1404'; g.fillRect(0, 0, N, N);
  g.save(); g.beginPath(); g.arc(R, R, R * 0.97, 0, 2 * PI); g.clip();
  const across = 7, w = (2 * R) / across, hr = w / Math.sqrt(3); // hex radius (pointy-top)
  for (let row = -1; row <= across + 1; row++) for (let col = -1; col <= across + 1; col++) {
    const cx = col * w + (row % 2 ? w / 2 : 0), cy = row * hr * 1.5; const d = Math.hypot(cx - R, cy - R) / R; if (d > 1.1) continue;
    const corners = Array.from({ length: 6 }, (_, k) => [cx + hr * Math.cos(PI / 6 + (k * PI) / 3), cy + hr * Math.sin(PI / 6 + (k * PI) / 3)]);
    const shades = ['#ffcf5a', '#e68a10', '#b85a06'];
    for (let q = 0; q < 3; q++) { const a = corners[(q * 2) % 6], b = corners[(q * 2 + 1) % 6], e = corners[(q * 2 + 2) % 6]; g.fillStyle = shades[q]; g.beginPath(); g.moveTo(cx, cy); g.lineTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.lineTo(e[0], e[1]); g.closePath(); g.fill(); }
    const hg = g.createRadialGradient(cx, cy, 0, cx, cy, hr * 0.75); hg.addColorStop(0, 'rgba(255,248,210,0.95)'); hg.addColorStop(0.35, 'rgba(255,214,120,0.45)'); hg.addColorStop(1, 'rgba(255,190,80,0)'); g.fillStyle = hg; g.beginPath(); g.arc(cx, cy, hr * 0.8, 0, 2 * PI); g.fill();
    g.strokeStyle = 'rgba(70,30,4,0.85)'; g.lineWidth = 2.2; g.beginPath(); corners.forEach(([x, y], k) => (k ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath(); g.stroke();
  }
  const vg = g.createRadialGradient(R, R, R * 0.55, R, R, R); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(40,14,0,0.55)'); g.fillStyle = vg; g.fillRect(0, 0, N, N);
  g.restore(); g.strokeStyle = '#1a0a02'; g.lineWidth = N * 0.04; g.beginPath(); g.arc(R, R, R * 0.96, 0, 2 * PI); g.stroke();
  return canvasTex(c, { srgb: true });
});

// --- materials (shared, cached; the eye material is per instance because its level animates)
const furMat = (color) => cached(keyOf('ep01FurMat', color), () => { const T = furTex(); return new THREE.MeshPhysicalMaterial({ color, map: T.map, normalMap: T.normal, normalScale: new THREE.Vector2(0.45, 0.45), roughness: 0.72, sheen: 1, sheenRoughness: 0.36, sheenColor: new THREE.Color('#d0c8f4'), vertexColors: true }); });
const fleshPlainMat = (color) => cached(keyOf('ep01FleshPlain', color), () => new THREE.MeshPhysicalMaterial({ color, roughness: 0.48, sheen: 0.6, sheenColor: new THREE.Color('#ffc0d0'), emissive: new THREE.Color('#6e2438'), clearcoat: 0.4, clearcoatRoughness: 0.3, vertexColors: true }));
const fleshMat = (color) => cached(keyOf('ep01FleshMat', color), () => { const T = snoutTex(); return new THREE.MeshPhysicalMaterial({ color, map: T.map, normalMap: T.normal, normalScale: new THREE.Vector2(0.6, 0.6), roughness: 0.46, sheen: 0.6, sheenRoughness: 0.5, sheenColor: new THREE.Color('#ffc0d0'), emissive: new THREE.Color('#6e2438'), emissiveIntensity: 1, clearcoat: 0.45, clearcoatRoughness: 0.28, vertexColors: true }); });
const discMat = (color) => cached(keyOf('ep01DiscMat', color), () => new THREE.MeshPhysicalMaterial({ color: mix(color, '#ffffff', 0.25), map: discTex(), normalMap: snoutTex().normal, normalScale: new THREE.Vector2(0.4, 0.4), roughness: 0.42, sheen: 0.6, sheenColor: new THREE.Color('#ffc0d0'), emissive: new THREE.Color('#401018'), clearcoat: 0.5, clearcoatRoughness: 0.25 }));
const clawMat = () => cached('ep01ClawMat', () => new THREE.MeshPhysicalMaterial({ color: '#efe2c6', roughness: 0.28, clearcoat: 1, clearcoatRoughness: 0.08, vertexColors: true }));
const palmMat = () => cached('ep01PalmMat', () => new THREE.MeshPhysicalMaterial({ color: '#c98a90', map: snoutTex().map, normalMap: snoutTex().normal, normalScale: new THREE.Vector2(0.5, 0.5), roughness: 0.55, sheen: 0.5, sheenColor: new THREE.Color('#f0c0c8') }));
const capMat = () => cached('ep01EyeCapMat', () => new THREE.MeshPhysicalMaterial({ color: '#ffffff', roughness: 0.04, clearcoat: 1, clearcoatRoughness: 0.02, transparent: true, opacity: 0.16, depthWrite: false }));
function eyeMaterial(color) {
  const m = new THREE.MeshPhysicalMaterial({ color: '#5a3410', map: reflectorTexture(), emissive: new THREE.Color(color), emissiveMap: reflectorTexture(), emissiveIntensity: 0, roughness: 0.22, metalness: 0.1, clearcoat: 1, clearcoatRoughness: 0.03 });
  // fake retro-reflection: emissive *= 0.4 + 0.6 * max(0, N.toCamera)^4
  m.onBeforeCompile = (sh) => { sh.fragmentShader = sh.fragmentShader.replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance *= 0.4 + 0.6 * pow(max(dot(normal, normalize(vViewPosition)), 0.0), 4.0);'); };
  m.customProgramCacheKey = () => 'ep01moleEye'; return m;
}

// --- head, snout, eyes, paws, body geometry (studs; head-local: snout faces +z)
const HEAD_PROF = [[0, -0.62], [0.2, -0.58], [0.31, -0.5], [0.41, -0.36], [0.47, -0.18], [0.475, 0.0], [0.45, 0.14], [0.41, 0.24], [0.35, 0.33], [0.28, 0.42], [0.22, 0.5], [0.185, 0.555], [0.17, 0.585], [0.1, 0.6], [0, 0.605]];
const HEAD_FY = 0.84;
function profR(z) { for (let i = 1; i < HEAD_PROF.length; i++) { const [r0, z0] = HEAD_PROF[i - 1], [r1, z1] = HEAD_PROF[i]; if (z >= z0 && z <= z1) return r0 + (r1 - r0) * (z - z0) / (z1 - z0 || 1); } return 0; }
const EYE = { x: 0.3, z: 0.21, r: 0.11 };
function eyeFrame() { // centre + outward axis of the left eye (+x) on the head surface
  const R = profR(EYE.z), y = HEAD_FY * Math.sqrt(Math.max(0, R * R - EYE.x * EYE.x)), dR = (profR(EYE.z + 0.01) - profR(EYE.z - 0.01)) / 0.02;
  const nrm = V3(2 * EYE.x, (2 * y) / (HEAD_FY * HEAD_FY), -2 * R * dR).normalize();
  const axis = nrm.clone().lerp(V3(0, 0.1, 1).normalize(), 0.45).normalize(); // turned toward the front: reflectors face what they look at
  return { c: V3(EYE.x, y, EYE.z), axis };
}
const headGeoMole = () => cached('ep01MoleHeadGeo', () => {
  const g = zLathe(HEAD_PROF, 56, HEAD_FY); const p = g.attributes.position, nm = g.attributes.normal, col = new Float32Array(p.count * 3); const { c } = eyeFrame();
  for (let i = 0; i < p.count; i++) { // slight sculpt: brow ridges over the eyes, cheek pads, shading AO at the eye sockets and muzzle
    const x = p.getX(i), y = p.getY(i), z = p.getZ(i); let k = 1;
    const dEye = Math.min(Math.hypot(x - c.x, y - c.y, z - c.z), Math.hypot(x + c.x, y - c.y, z - c.z));
    k += 0.05 * Math.exp(-(((dEye - 0.15) / 0.05) ** 2)) * (y > c.y - 0.02 ? 1 : 0.3);
    k += 0.03 * noise3(x * 6, y * 6, z * 6, 3);
    p.setXYZ(i, x * k, y * k, z); const ao = 1 - 0.45 * Math.exp(-(((dEye - 0.1) / 0.06) ** 2)) - 0.2 * smooth(0.45, 0.6, z) * (1 - smooth(0.0, 0.1, Math.abs(y) + Math.abs(x) * 0.2));
    col[i * 3] = col[i * 3 + 1] = col[i * 3 + 2] = sat(ao * (0.88 + 0.12 * sat(nm.getY(i) * 0.5 + 0.5)));
  }
  g.setAttribute('color', new THREE.BufferAttribute(col, 3)); return smoothNormals(g);
});
// Disc (nostril pad): a shallow dome; muzzle ring: fleshy collar between fur and disc.
const discGeo = () => cached('ep01MoleDiscGeo', () => { const g = new THREE.SphereGeometry(0.192, 44, 18, 0, 2 * PI, 0, PI * 0.5); g.rotateX(PI / 2); g.scale(1, 1, 0.26); const p = g.attributes.position, uv = g.attributes.uv; for (let i = 0; i < p.count; i++) uv.setXY(i, 0.5 + p.getX(i) / 0.36, 0.5 + p.getY(i) / 0.36); return g; });
const muzzleGeo = () => cached('ep01MoleMuzzleGeo', () => { const g = zLathe([[0.172, -0.07], [0.19, -0.03], [0.185, 0.01], [0.168, 0.04], [0.15, 0.05]], 40, 1); const col = new Float32Array(g.attributes.position.count * 3).fill(0.95); g.setAttribute('color', new THREE.BufferAttribute(col, 3)); return g; });
const eyeDomeGeo = () => cached('ep01MoleEyeGeo', () => { const g = new THREE.SphereGeometry(EYE.r, 40, 14, 0, 2 * PI, 0, PI * 0.5); g.rotateX(PI / 2); g.scale(1, 1, 0.5); const p = g.attributes.position, uv = g.attributes.uv; for (let i = 0; i < p.count; i++) uv.setXY(i, 0.5 + p.getX(i) / (2 * EYE.r), 0.5 + p.getY(i) / (2 * EYE.r)); g.computeVertexNormals(); return g; });
const eyeCapGeo = () => cached('ep01MoleEyeCapGeo', () => { const g = new THREE.SphereGeometry(EYE.r * 1.07, 32, 12, 0, 2 * PI, 0, PI * 0.5); g.rotateX(PI / 2); g.scale(1, 1, 0.62); return g; });
const eyeLidGeo = () => cached('ep01MoleLidGeo', () => { const g = new THREE.TorusGeometry(EYE.r * 1.02, 0.03, 10, 40); const col = new Float32Array(g.attributes.position.count * 3).fill(0.7); g.setAttribute('color', new THREE.BufferAttribute(col, 3)); return g; });
// Huge digging paw: broad palm turned outward + 5 long ivory claws (studs; paw-local: claws point +z, palm faces +x)
const pawGeos = () => cached('ep01MolePawGeo', () => {
  const palm = new THREE.SphereGeometry(1, 28, 20); xform(palm, [0, 0, 0.03], [0, 0, 0], [0.21, 0.075, 0.2]);
  const wrist = zLathe([[0, -0.45], [0.14, -0.4], [0.16, -0.22], [0.15, -0.06], [0.12, 0.02], [0, 0.04]], 24, 0.75);
  const col = new Float32Array(wrist.attributes.position.count * 3).fill(0.85); wrist.setAttribute('color', new THREE.BufferAttribute(col, 3));
  const claws = [];
  for (let k = 0; k < 5; k++) { const a = (k - 2) * 0.24, x0 = (k - 2) * 0.075, L = 0.21 + 0.06 * (1 - Math.abs(k - 2) / 2); const dx = Math.sin(a), dz = Math.cos(a); const P0 = [x0, 0.0, 0.15];
    const g = taperTube([P0, [x0 + dx * L * 0.45, 0.012, 0.15 + dz * L * 0.45], [x0 + dx * L * 0.8, -0.03, 0.15 + dz * L * 0.8], [x0 + dx * L, -0.1, 0.15 + dz * L * 0.95]], 0.04, 0.004, 10, 14); claws.push(g); }
  const cg = mergeList(claws); const cc = new Float32Array(cg.attributes.position.count * 3); const cp = cg.attributes.position; for (let i = 0; i < cp.count; i++) { const v = 0.62 + 0.4 * smooth(0.16, 0.36, cp.getZ(i)); cc[i * 3] = v; cc[i * 3 + 1] = v * 0.97; cc[i * 3 + 2] = v * 0.92; } cg.setAttribute('color', new THREE.BufferAttribute(cc, 3));
  return { palm, wrist, claws: cg };
});
const bodyGeo = () => cached('ep01MoleBodyGeo', () => { const g = zLathe([[0, -1.2], [0.35, -1.12], [0.55, -0.9], [0.66, -0.55], [0.68, -0.2], [0.6, 0.12], [0.46, 0.32], [0, 0.42]], 40, 0.82); const col = new Float32Array(g.attributes.position.count * 3); const p = g.attributes.position, n = g.attributes.normal; for (let i = 0; i < p.count; i++) { const v = 0.8 + 0.2 * sat(n.getY(i) * 0.5 + 0.5); col[i * 3] = col[i * 3 + 1] = col[i * 3 + 2] = v; } g.setAttribute('color', new THREE.BufferAttribute(col, 3)); return g; });

// --- tentacles: 22 rays (11 per side) round the nostril disc; one merged mesh per mole whose vertices are rewritten
// every frame (curl / unfurl / wriggle / recoil), so it reads as a single soft, sculpted star.
function tentacleLayout(seed) {
  const r = makeRng(hash32('moleRays', seed)), out = [];
  for (const s of [1, -1]) for (let k = 0; k < 11; k++) {
    const th = ((k + 0.5) / 11) * PI; // from top (0) to bottom (PI) on this side
    let L = 0.3 + 0.04 * Math.sin((k / 10) * PI); if (k === 9) L = 0.24; if (k === 10) L = 0.15; L *= 0.9 + r() * 0.2;
    out.push({ ang: [s * Math.sin(th), Math.cos(th)], L, root: 0.043 + (k === 10 ? -0.01 : 0) + (r() - 0.5) * 0.006, tilt: (14 + r() * 14) * DEG, ph: r() * 2 * PI, ph2: r() * 2 * PI, f: 2.2 + r() * 0.8, bias: (r() - 0.5) * 34 * DEG, side: (r() - 0.5) * 16 * DEG, rings: 9 + r() * 4 });
  }
  return out;
}
function tentacleGeometry(lod) {
  const { tub: T, rad: R } = LODS[lod], perV = (T + 1) * (R + 1), N = 22, pos = new Float32Array(N * perV * 3), nor = new Float32Array(N * perV * 3), uv = new Float32Array(N * perV * 2), col = new Float32Array(N * perV * 3), idx = [];
  for (let t = 0; t < N; t++) { const o = t * perV; for (let i = 0; i <= T; i++) for (let j = 0; j <= R; j++) { const k = o + i * (R + 1) + j; uv[k * 2] = j / R; uv[k * 2 + 1] = i / T; const v = 0.86 + 0.24 * (i / T); col[k * 3] = Math.min(1.12, v); col[k * 3 + 1] = Math.min(1.12, v * 1.02); col[k * 3 + 2] = Math.min(1.12, v * 1.03); }
    for (let i = 0; i < T; i++) for (let j = 0; j < R; j++) { const a = o + i * (R + 1) + j, b = a + R + 1; idx.push(a, b, a + 1, a + 1, b, b + 1); } }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('normal', new THREE.BufferAttribute(nor, 3)); g.setAttribute('uv', new THREE.BufferAttribute(uv, 2)); g.setAttribute('color', new THREE.BufferAttribute(col, 3)); g.setIndex(idx);
  g.boundingSphere = new THREE.Sphere(V3(0, 0, 0.2), 0.8); return g;
}
const _d = V3(), _b = V3(), _w = V3(), _er = V3(), _ez = V3(0, 0, 1), _C = V3(), _N = V3();
function writeTentacles(geo, layout, lod, { t = 0, open = 1, recoil = 0, sniff = 0, wriggle = 1 }) {
  const { tub: T, rad: R } = LODS[lod], perV = (T + 1) * (R + 1), P = geo.attributes.position.array, Nn = geo.attributes.normal.array, r0 = 0.132;
  const closed = 132 * DEG, opened = 30 * DEG;
  for (let q = 0; q < layout.length; q++) {
    const L0 = layout[q], o = q * perV; const [ax, ay] = L0.ang; _er.set(ax, ay, 0);
    let th = lerp(closed, opened, open) + L0.bias * open; th += wriggle * 10 * DEG * Math.sin(2 * PI * L0.f * t + L0.ph) * (0.35 + 0.65 * sat(open));
    th += recoil * 70 * DEG; th += sniff * 9 * DEG * Math.sin(2 * PI * 7.5 * t + L0.ph * 0.5);
    const psi = L0.side + wriggle * 7 * DEG * Math.sin(2 * PI * (L0.f * 0.63) * t + L0.ph2);
    const L = L0.L * (1 - 0.18 * recoil);
    _d.copy(_er).multiplyScalar(Math.cos(L0.tilt)).addScaledVector(_ez, Math.sin(L0.tilt)).normalize();
    _b.copy(_ez).multiplyScalar(Math.cos(L0.tilt)).addScaledVector(_er, -Math.sin(L0.tilt)).normalize();
    _w.crossVectors(_d, _b).normalize(); const b2 = _b.clone().multiplyScalar(Math.cos(psi)).addScaledVector(_w, Math.sin(psi)); const w2 = _d.clone().cross(b2).normalize();
    const rx = _er.x * r0, ry = _er.y * r0;
    for (let i = 0; i <= T; i++) {
      const u = i / T, uu = 1 - Math.pow(1 - u, 1.35); const s = uu * L, phi = th * uu;
      if (Math.abs(th) < 1e-4) _C.set(rx + _d.x * s, ry + _d.y * s, _d.z * s);
      else { const kA = L / th; _C.set(rx + kA * (Math.sin(phi) * _d.x + (1 - Math.cos(phi)) * b2.x), ry + kA * (Math.sin(phi) * _d.y + (1 - Math.cos(phi)) * b2.y), kA * (Math.sin(phi) * _d.z + (1 - Math.cos(phi)) * b2.z)); }
      _N.copy(_d).multiplyScalar(-Math.sin(phi)).addScaledVector(b2, Math.cos(phi));
      const tipR = 0.024; let rr = lerp(L0.root, tipR, Math.pow(uu, 0.8)) * (1 + 0.14 * Math.sin(uu * PI) + 0.06 * Math.sin(uu * L0.rings * 2 * PI) * (1 - uu)); const tipS = 0.86; if (uu > tipS) rr = tipR * Math.sqrt(Math.max(0, 1 - ((uu - tipS) / (1 - tipS)) ** 2)) + 0.002;
      if (i === T) rr = 0.0015;
      for (let j = 0; j <= R; j++) {
        const a = (j / R) * 2 * PI, ca = Math.cos(a), sa = Math.sin(a), k = (o + i * (R + 1) + j) * 3, fl = 0.93;
        P[k] = _C.x + rr * (ca * _N.x * fl + sa * w2.x); P[k + 1] = _C.y + rr * (ca * _N.y * fl + sa * w2.y); P[k + 2] = _C.z + rr * (ca * _N.z * fl + sa * w2.z);
        let nx = ca * _N.x / fl + sa * w2.x, ny = ca * _N.y / fl + sa * w2.y, nz = ca * _N.z / fl + sa * w2.z; const l = Math.hypot(nx, ny, nz) || 1; Nn[k] = nx / l; Nn[k + 1] = ny / l; Nn[k + 2] = nz / l;
      }
    }
  }
  geo.attributes.position.needsUpdate = true; geo.attributes.normal.needsUpdate = true;
}

// --- crumbs (instanced soil lumps at the rim, popping off the crest while the mound rises)
function crumbLayout(seed, n) { return cached(keyOf('ep01CrumbLayout', seed, n), () => crumbLayout0(seed, n)); }
function crumbLayout0(seed, n) {
  const r = makeRng(hash32('moleCrumbs', seed)), out = [];
  for (let i = 0; i < n; i++) { const a = r() * 2 * PI, rr = 0.84 + r() * 0.3; let x = Math.sin(a) * MOUND.Rx * rr, z = Math.cos(a) * MOUND.Rz * rr; if (z > 0.6 && Math.abs(x) < 0.7) { z += 0.25; } const s = 0.028 + r() * r() * 0.05 + (r() < 0.12 ? 0.025 : 0); out.push({ x, z, s, y: moundHeight(x, z, seed), rot: [r() * PI, r() * PI, r() * PI], delay: r() * 0.18, c: 0.75 + r() * 0.45, sx: (r() - 0.5) * 0.4, sz: (r() - 0.5) * 0.4 }); }
  return out;
}
const _m4 = new THREE.Matrix4(), _q = new THREE.Quaternion(), _e = new THREE.Euler(), _p = V3(), _s = V3();
function writeCrumbs(im, layout, tau) { // tau: seconds since the rise started (Infinity = settled)
  for (let i = 0; i < layout.length; i++) {
    const c = layout[i]; const u = (tau - c.delay) / 0.42; let x = c.x, z = c.z, y = c.y + c.s * 0.35, k = 1;
    if (u < 0) { k = 0; } else if (u < 1) { const sx = c.sx, sz = c.sz; x = lerp(sx, c.x, u); z = lerp(sz, c.z, u); y = lerp(0.6, c.y + c.s * 0.35, u) + 0.55 * 4 * u * (1 - u); k = Math.min(1, u * 4); } else if (u < 1.35) { y += 0.04 * Math.abs(Math.sin((u - 1) / 0.35 * PI)) * (1.35 - u) / 0.35; }
    _e.set(c.rot[0] + (u < 1 ? u * 4 : 4), c.rot[1], c.rot[2]); _q.setFromEuler(_e); _p.set(x, y, z); _s.setScalar(c.s * Math.max(0.0001, k));
    _m4.compose(_p, _q, _s); im.setMatrixAt(i, _m4);
  }
  im.instanceMatrix.needsUpdate = true;
}

// --- build
const _moleState = new WeakMap();
export function makeMole(opts = {}) {
  const preset = typeof opts === 'string' ? MOLE_PRESETS[opts] || {} : opts.preset ? MOLE_PRESETS[opts.preset] || {} : {};
  const P = { ...MOLE_DEFAULTS, ...preset, ...(typeof opts === 'string' ? {} : opts) }; const lod = P.lod; const Ld = LODS[lod];
  const seed = typeof P.seed === 'number' ? P.seed : hash32('mole', P.seed) % 9973;
  const root = makeRoot('mole', P.units); root.userData.kit = 'mole'; root.userData.moleSeed = seed; root.userData.moleLod = lod; root.userData.moleScale = P.scale;
  const body = group('moleBody', root); body.scale.setScalar(P.scale);
  const fm = furMat(P.fur);
  // mound
  if (P.mound) {
    const mg = group('mound', body);
    mesh(moundGeometry(seed, lod), turfMaterial(), { parent: mg, name: 'moundTurf', cast: false, order: 1 });
    if (P.blades && Ld.blades) { // grass tufts riding on the dome (avoiding cracks and the opening)
      const geo = moundGeometry(seed, lod), cracks = geo.userData.cracks, r = makeRng(hash32('moleBlades', seed)); const im = new THREE.InstancedMesh(bladeGeo(), bladeMat(), Ld.blades); im.name = 'moundBlades';
      const C3 = [new THREE.Color('#3b6e33'), new THREE.Color('#4f8a44'), new THREE.Color('#76a860')], c = new THREE.Color(); let k = 0, tries = 0;
      while (k < Ld.blades && tries < Ld.blades * 6) { tries++; const x = (r() - 0.5) * 2 * MOUND.Rx, z = (r() - 0.5) * 2 * MOUND.Rz; const rr = Math.hypot(x / MOUND.Rx, z / MOUND.Rz); if (rr > 0.95) continue;
        if (Math.hypot(x / 0.62, (z - HEAD_AT.z - 0.18) / 0.62) < 1.15) continue; let bad = false; for (const cr of cracks) for (let q = 1; q < cr.pts.length; q++) if (distSeg(x, z, cr.pts[q - 1][0], cr.pts[q - 1][1], cr.pts[q][0], cr.pts[q][1])[0] < cr.w * 2) bad = true; if (bad) continue;
        const y = moundHeight(x, z, seed) - 0.01, h = (0.12 + 0.2 * r() * r()) * (1 - 0.4 * rr), w = 0.8 + r() * 0.8;
        _m4.compose(V3(x, y, z), _q.setFromEuler(_e.set((r() - 0.5) * 0.6, r() * 2 * PI, (r() - 0.5) * 0.5, 'YXZ')), V3(w, h, w)); im.setMatrixAt(k, _m4); const tc = r(); c.copy(tc < 0.5 ? C3[0] : C3[1]).lerp(tc < 0.5 ? C3[1] : C3[2], tc < 0.5 ? tc * 2 : (tc - 0.5) * 2).multiplyScalar(0.92); im.setColorAt(k, c); k++; }
      im.count = k; im.instanceMatrix.needsUpdate = true; if (im.instanceColor) im.instanceColor.needsUpdate = true; im.castShadow = false; im.frustumCulled = false; mg.add(im);
    }
    if (P.crumbs && Ld.crumbs) { const im = new THREE.InstancedMesh(crumbGeo(), crumbMat(), Ld.crumbs); im.name = 'moundCrumbs'; im.castShadow = false; im.frustumCulled = false; const r = makeRng(hash32('crumbCol', seed)); const c = new THREE.Color(); for (let i = 0; i < Ld.crumbs; i++) { const v = 0.7 + r() * 0.5; im.setColorAt(i, c.setRGB(v, v * 0.95, v * 0.9)); } im.instanceColor.needsUpdate = true; mg.add(im); }
  }
  // upper body (emerge pivot): head + paws + chest
  const up = group('moleUpper', body, [0, HEAD_AT.y, HEAD_AT.z]);
  const head = group('moleHead', up); const hf = mesh(headGeoMole(), fm, { parent: head, name: 'headFur' }); hf.visible = P.headFur !== false;
  const sn = group('snout', head, [0, -0.02, 0.6]);
  mesh(muzzleGeo(), fleshPlainMat(P.snout), { parent: sn, name: 'snoutMuzzle', pos: [0, 0, -0.02] });
  mesh(discGeo(), discMat(P.snout), { parent: sn, name: 'snoutDisc', pos: [0, 0, -0.035] });
  const tg = tentacleGeometry(lod); const tm = mesh(tg, fleshMat(P.snout), { parent: sn, name: 'tentacles' }); tg.userData.owner = tm.uuid; tm.frustumCulled = false;
  writeTentacles(tg, tentacleLayout(seed), lod, { t: 0, open: 1 });
  const ef = eyeFrame(); const em = eyeMaterial(P.eyeColor); const q = new THREE.Quaternion();
  for (const [nm, s] of [['L', 1], ['R', -1]]) {
    const c = V3(ef.c.x * s, ef.c.y, ef.c.z), ax = V3(ef.axis.x * s, ef.axis.y, ef.axis.z); q.setFromUnitVectors(V3(0, 0, 1), ax);
    const eg = group('eye' + nm, head); eg.position.copy(c).addScaledVector(ax, -0.012); eg.quaternion.copy(q);
    const d = mesh(eyeDomeGeo(), nm === 'L' ? em : eyeMaterial(P.eyeColor), { parent: eg, name: 'eyeDome' + nm, cast: false }); d.material.userData.owner = d.uuid; d.material.userData.eyeColor = P.eyeColor;
    mesh(eyeCapGeo(), capMat(), { parent: eg, name: 'eyeCap' + nm, cast: false, order: 3 });
    mesh(eyeLidGeo(), fm, { parent: eg, name: 'eyeLid' + nm, pos: [0, 0, 0.004], cast: false });
    const halo = pxSprite(addMat(radialGlow({ falloff: 1.7 }), new THREE.Color(P.eyeColor).multiplyScalar(1.1), { opacity: 0 }), 20); halo.name = 'eyeHalo' + nm; halo.position.set(0, 0, 0.07); halo.renderOrder = 12; halo.userData.axis = true; eg.add(halo);
    const gl = pxSprite(addMat(sparkleTex({ points: 4, sharpness: 22, core: 0.6 }), new THREE.Color('#fff2cc').multiplyScalar(2.2), { opacity: 0 }), 0); gl.name = 'eyeGlint' + nm; gl.position.set(0, 0, 0.08); gl.renderOrder = 13; gl.visible = false; eg.add(gl);
  }
  if (P.claws) {
    const pg = pawGeos();
    for (const [nm, s] of [['L', 1], ['R', -1]]) {
      const pw = group('paw' + nm, up, [s * 0.5, -0.12, 0.42]);
      mesh(pg.wrist, fm, { parent: pw, name: 'pawWrist' + nm }); mesh(pg.palm, palmMat(), { parent: pw, name: 'pawPalm' + nm }); mesh(pg.claws, clawMat(), { parent: pw, name: 'pawClaws' + nm });
    }
  }
  if (P.body) mesh(bodyGeo(), fm, { parent: up, name: 'moleTorso', pos: [0, -0.18, -0.75] });
  if (P.shadow && P.mound) { const sb = shadowBlob(3.3 * P.scale, 3.5 * P.scale, 0.3); sb.name = 'moleShadow'; root.add(sb); }
  _moleState.set(root, { tm, layout: tentacleLayout(seed), lod });
  setMole(root, {});
  return root;
}
function moleState(root) {
  let s = _moleState.get(root); const tm = root.getObjectByName('tentacles');
  if (!s || s.tm !== tm) { // a clone (ctx.instance): own a copy of the tentacle geometry
    if (tm && tm.geometry.userData.owner !== tm.uuid) { tm.geometry = tm.geometry.clone(); tm.geometry.userData.owner = tm.uuid; }
    s = { tm, layout: tentacleLayout(root.userData.moleSeed || 1), lod: root.userData.moleLod || 'hero' }; _moleState.set(root, s);
  }
  return s;
}
// Pose a mole (all fields optional; pure function of the values):
//   t        seconds (drives the wriggle, breathing and sniff)      rise    mound 0 flat .. 1 up (overshoot ok)
//   open     tentacles 0 closed bud .. 1 open (unfurl)              recoil  0..1 snout snapped back, rays clenched
//   sniff    0..1 quick sniffing flutter                           emerge  -1 hidden, 0 snout+eyes (default), 0.5 peek (head + claws), 1 out to the shoulders
//   eyes     reflector level 0 dark .. 1 lit                        flash   0..1 reflector flash (star glint sweep)
//   look     [yawDeg, pitchDeg] head aim                             wriggle amplitude multiplier (1)
//   crumbs   seconds since the rise started (crumb pop; default: settled)   breathe 1 (mound + head idle so it is never frozen)
export function setMole(root, o = {}) {
  const st = moleState(root); const t = o.t ?? 0, rise = o.rise ?? 1, open = o.open ?? 1, recoil = o.recoil ?? 0, sniff = o.sniff ?? 0, emerge = o.emerge ?? 0, eyes = o.eyes ?? 1, flash = o.flash ?? 0, breathe = o.breathe ?? 1;
  const look = o.look || [0, 0]; const seedPh = (root.userData.moleSeed || 1) * 0.37;
  const mg = root.getObjectByName('mound');
  if (mg) { const b = 1 + breathe * 0.018 * Math.sin(2 * PI * 0.65 * t + seedPh); const ry = Math.max(0.002, rise * b); mg.scale.set(0.72 + 0.28 * Math.min(1.1, rise), ry, 0.72 + 0.28 * Math.min(1.1, rise)); mg.visible = rise > 0.001;
    const cr = mg.getObjectByName('moundCrumbs'); if (cr) writeCrumbs(cr, crumbLayout(root.userData.moleSeed || 1, cr.count), o.crumbs ?? 99); }
  const sbl = root.getObjectByName('moleShadow'); if (sbl) { sbl.visible = rise > 0.02; sbl.scale.setScalar(Math.max(0.001, Math.min(1, rise))); }
  // upper body: emerge path + recoil + idle bob; sinks with the mound
  const up = root.getObjectByName('moleUpper');
  const e = emerge; const ey = e < 0 ? lerp(HEAD_AT.y, HEAD_AT.y - 0.7, -e) : e < 0.5 ? lerp(HEAD_AT.y, HEAD_AT.y + 0.38, e / 0.5) : lerp(HEAD_AT.y + 0.38, HEAD_AT.y + 0.78, (e - 0.5) / 0.5);
  const ez = e < 0 ? lerp(HEAD_AT.z, HEAD_AT.z - 0.3, -e) : e < 0.5 ? lerp(HEAD_AT.z, HEAD_AT.z + 0.42, e / 0.5) : lerp(HEAD_AT.z + 0.42, HEAD_AT.z + 0.62, (e - 0.5) / 0.5);
  const sinkY = (1 - Math.min(1, rise)) * -1.0;
  up.position.set(anim.wobble(t, seedPh + 3, 0.4, 0.006 * breathe), ey + sinkY + breathe * 0.006 * Math.sin(2 * PI * 0.65 * t + seedPh + 0.8) - 0.04 * recoil, ez - 0.14 * recoil);
  const ek = e > 0 ? Math.min(1, e * 2) : 0; up.rotation.set(-(look[1] * (0.3 + 0.7 * ek) + 10 * ek + 4 * recoil) * DEG + breathe * 0.012 * Math.sin(2 * PI * 0.5 * t + seedPh), (look[0] * (0.3 + 0.7 * ek) + breathe * (1 + 2 * ek) * anim.wobble(t, seedPh, 0.35, 1)) * DEG, breathe * (0.6 + 1.2 * ek) * DEG * Math.sin(2 * PI * 0.31 * t + seedPh));
  for (const s of ['L', 'R']) { // paws: flat on the turf either side of the snout, claws hooked over the rim (peek); flex while out
    const pw = root.getObjectByName('paw' + s); if (!pw) continue; const sg = s === 'L' ? 1 : -1; const pe = sat((e - 0.1) / 0.4), po = sat((e - 0.5) / 0.5); pw.visible = e > 0.12;
    const flex = 0.08 * Math.sin(2 * PI * 0.9 * t + (sg > 0 ? 0 : 1.7));
    pw.position.set(sg * lerp(0.36, 0.5, pe), lerp(-0.6, -0.34, pe) - 0.06 * po, lerp(0.05, 0.42, pe));
    pw.rotation.set(lerp(-0.6, 0.18, pe) + flex * pe + 0.25 * po, sg * lerp(0.15, 0.42, pe), sg * lerp(0.05, 0.22, pe)); }
  const tor = root.getObjectByName('moleTorso'); if (tor) tor.visible = e > 0.7;
  const sn = root.getObjectByName('snout'); if (sn) { sn.position.z = 0.6 - 0.05 * recoil + 0.012 * sniff * Math.sin(2 * PI * 7.5 * t); sn.scale.setScalar(1 - 0.06 * recoil); }
  writeTentacles(st.tm.geometry, st.layout, st.lod, { t, open, recoil, sniff, wriggle: o.wriggle ?? 1 });
  setMoleEyes(root, eyes, { flash, t });
}
// Eyes: level 0 dark .. 1 lit (emissive x4 with the retro-reflection falloff + a 15-25 px halo); flash 0..1 = the
// reflector flash (x2.5 emissive + a 4-point star glint per eye, the right eye trailing the left by 0.06 s).
export function setMoleEyes(root, level = 1, { flash = 0, t = 0 } = {}) {
  for (const nm of ['L', 'R']) {
    const d = root.getObjectByName('eyeDome' + nm); if (!d) continue; if (d.material.userData.owner !== d.uuid) { const c = d.material.userData.eyeColor || '#ffa416'; d.material = eyeMaterial(c); d.material.userData = { owner: d.uuid, eyeColor: c }; } d.material.emissiveIntensity = 3.2 * level * (1 + 1.6 * flash);
    const h = root.getObjectByName('eyeHalo' + nm); if (h) { h.material = h.material.userData.owner === h.uuid ? h.material : Object.assign(h.material.clone(), { userData: { owner: h.uuid } }); h.material.opacity = 0.95 * level * (1 + 0.5 * flash); h.userData.px = 18 + 10 * level + 30 * flash; h.visible = level > 0.01; }
    const gl = root.getObjectByName('eyeGlint' + nm); if (gl) { const f = nm === 'L' ? flash : flash * (flash > 0 ? 0.85 : 0); gl.visible = f > 0.01; if (gl.visible) { gl.material = gl.material.userData.owner === gl.uuid ? gl.material : Object.assign(gl.material.clone(), { userData: { owner: gl.uuid } }); gl.material.opacity = Math.min(1, f * 1.4); gl.material.rotation = (nm === 'L' ? 0.2 : 0.5) + f * 0.6; gl.userData.px = 120 * f; } }
  }
}
// ---- time curves (pure functions of t; t0 = event time in shot seconds) ----
export const moleRise = (t, t0, dur = 0.5) => (t0 == null ? 1 : t < t0 ? 0 : anim.ease.outBack(Math.min(1, (t - t0) / dur)));
export const moleUnfurl = (t, t0, dur = 0.3) => (t0 == null ? 1 : t < t0 ? 0 : anim.ease.outBack(Math.min(1, (t - t0) / dur)));
// Recoil from light: snap back in 0.15 s with a spring overshoot, then hold (0 -> ~1).
export const moleRecoil = (t, t0, { hold = 1, freq = 3.2, zeta = 0.32 } = {}) => (t0 == null || t < t0 ? 0 : anim.springStep(t - t0, freq, zeta) * hold);
// Sink: the mound deflates over `dur` (inQuad) and settles; eyes wink out in 2 frames at t0 + offEye.
export const moleSink = (t, t0, dur = 0.5) => (t0 == null || t < t0 ? 1 : 1 - anim.ease.inQuad(Math.min(1, (t - t0) / dur)));
export const eyesOn = (t, t0, frames = 3, fps = 60) => (t0 == null ? 1 : t < t0 ? 0 : Math.min(1, ((t - t0) * fps + 1) / frames));
export const eyesOff = (t, t0, frames = 2, fps = 60) => (t0 == null || t < t0 ? 1 : Math.max(0, 1 - ((t - t0) * fps + 1) / frames));
// Reflector flash: 0 -> 1 in 3 frames, gone by 0.25 s (TF glint curve).
export const reflectorFlash = (t, t0, dur = 0.25) => { if (t0 == null || t < t0) return 0; const f = (t - t0) * 60; return f < 3 ? (f + 1) / 4 : Math.max(0, Math.pow(1 - (f - 3) / (dur * 60 - 3), 1.6)); };
// One-call cue sheet. cue = { rise, riseDur, unfurl, eyesOn, eyesOff, flash, recoil, sink, sinkDur, sniff: [t0, t1], emerge: [[t, v], ...] (springy), look: [yaw, pitch] }
export function animateMole(m, t, cue = {}) {
  const sinkK = moleSink(t, cue.sink, cue.sinkDur ?? 0.5);
  const rise = moleRise(t, cue.rise, cue.riseDur ?? 0.5) * sinkK;
  let eyes = eyesOn(t, cue.eyesOn) * eyesOff(t, cue.eyesOff ?? (cue.sink != null ? cue.sink + 0.12 : null));
  // default: with an unfurl cue the head waits under the turf and pushes the snout out just before it opens ("the turf splits")
  const em = cue.emerge ? anim.springKeys(t, cue.emerge, cue.emergeFreq ?? 2.4, 0.55) : cue.unfurl != null ? anim.springKeys(t, [[-1e3, -0.6], [cue.unfurl - 0.06, 0]], 3, 0.6) : 0;
  const sniff = cue.sniff ? anim.pulse(t, cue.sniff[0], 0.08, Math.max(0, cue.sniff[1] - cue.sniff[0] - 0.16), 0.08) : 0;
  setMole(m, { t, rise, open: moleUnfurl(t, cue.unfurl), recoil: moleRecoil(t, cue.recoil), sniff, emerge: em - (1 - sinkK) * 0.6, eyes, flash: reflectorFlash(t, cue.flash), look: cue.look, crumbs: cue.rise != null ? t - cue.rise : 99 });
}

// ==================================================================================================================
//  MOUND FIELD: many moles as bulges travelling under one shared, displaced turf sheet
// ==================================================================================================================
// moleField(ctx, { center: [x, z] (m, world), size: [w, d] (studs), yaw (rad), res (128 hero lawn / 64 neighbour), seed,
//                  heads: 'snout' | 'eyes' | false (what rides at each bulge front), lod: 'mid', height: [0.6, 0.9] })
// Every API call registers an event at build time; update(t) evaluates everything as a pure function of t.
//   const i = f.add({ at: [x, z], scale, height, head, face: [x, z] | yaw })   a mole (index); world metres; face = point it looks at
//   f.rise(i, t0, dur=0.5)      mound pushes up, soil crumbs pop             f.sink(i, t0, dur=0.5)   deflate + turf settles
//   f.travel(i, path, t0, speed=3)  path [[x,z],...] world m, speed studs/s (Catmull)   f.stopAt(i, [x,z], radius m)
//   f.swallow(i, target, t0, { depth })  GULP: turf rises round target like a closing mouth, target sinks 6 frames, seals
//   f.pushBack([x,z], r0, r1, t0, dur=0.5)  tide: every bulge within r1 is pushed out to r1 (+ its offset)
//   f.eyes(i, tOn, tOff)   f.recoil(i, t0)   f.update(t)   f.heightAt([x,z], t) (metres)   f.moles[i].head (a makeMole group)
export function moleField(ctx, o = {}) {
  const center = o.center || [0, 0], size = o.size || [36, 22], yaw = o.yaw || 0, res = o.res || 128, fseed = typeof o.seed === 'number' ? o.seed : hash32('field', o.seed || 'f') % 997;
  const G = new THREE.Group(); G.name = 'moleField'; G.position.set(center[0], o.y || 0, center[1]); G.rotation.y = yaw; G.updateMatrixWorld(true);
  const inv = new THREE.Matrix4().copy(G.matrixWorld).invert();
  const toLocal = (p) => { const v = V3(p[0], 0, p[1]).applyMatrix4(inv); return [v.x / STUD, v.z / STUD]; }; // world m -> field studs
  const S = group('fieldStuds', G); S.scale.setScalar(STUD);
  const nx = Math.max(8, Math.round(res * Math.min(1, size[0] / Math.max(size[0], size[1])))), nz = Math.max(8, Math.round(res * Math.min(1, size[1] / Math.max(size[0], size[1]))));
  const geo = new THREE.PlaneGeometry(size[0], size[1], nx, nz); geo.rotateX(-PI / 2);
  const NV = geo.attributes.position.count; const soil = new Float32Array(NV), alpha = new Float32Array(NV), col = new Float32Array(NV * 3).fill(1);
  geo.setAttribute('soil', new THREE.BufferAttribute(soil, 1)); geo.setAttribute('turfAlpha', new THREE.BufferAttribute(alpha, 1)); geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
  const turf = mesh(geo, turfMaterial(), { parent: S, name: 'fieldTurf', cast: false, order: 1 }); turf.frustumCulled = false;
  const H = new Float32Array(NV), dx = size[0] / nx, dz = size[1] / nz, x0 = -size[0] / 2, z0 = -size[1] / 2;
  const crackN = new Float32Array(NV); for (let i = 0; i < NV; i++) { const x = geo.attributes.position.getX(i), z = geo.attributes.position.getZ(i); crackN[i] = 1 - Math.abs(noise2(x * 0.9, z * 0.9, fseed) * 2); }
  const moles = [], pushes = [], swallows = [];
  const hRange = o.height || [0.6, 0.9];
  const F = {
    group: G, moles, turf,
    add({ at = [0, 0], scale = 1, height = null, head = o.heads ?? 'snout', seed = null, face = null, yaw: wy = null } = {}) {
      const i = moles.length, r = makeRng(hash32('fieldMole', fseed, i)); const p = toLocal(at);
      let h0 = [0, 1]; if (face) { const q = toLocal(face); const l = Math.hypot(q[0] - p[0], q[1] - p[1]) || 1; h0 = [(q[0] - p[0]) / l, (q[1] - p[1]) / l]; } else if (wy != null) { h0 = [Math.sin(wy - yaw), Math.cos(wy - yaw)]; }
      const m = { i, at: p, h0, scale, height: height ?? lerp(hRange[0], hRange[1], r()), ph: r() * 6.28, path: null, t0: 0, speed: 3, rise: null, sink: null, stop: null, eyesOn: null, eyesOff: null, recoil: null, head: null };
      if (head) { const hm = makeMole({ scale: scale * 0.85, seed: seed ?? 100 + i, lod: o.lod || 'mid', mound: false, claws: false, body: false, shadow: false, headFur: false }); hm.name = 'fieldMole' + i; if (head === 'eyes') { const sn = hm.getObjectByName('snout'); sn.visible = false; } G.add(hm); m.head = hm; }
      moles.push(m); return i;
    },
    rise(i, t0, dur = 0.5) { moles[i].rise = [t0, dur]; return F; },
    sink(i, t0, dur = 0.5) { moles[i].sink = [t0, dur]; return F; },
    eyes(i, tOn = null, tOff = null) { moles[i].eyesOn = tOn; moles[i].eyesOff = tOff; return F; },
    recoil(i, t0) { moles[i].recoil = t0; return F; },
    travel(i, path, t0 = 0, speed = 3) { const m = moles[i]; const pts = path.map(toLocal); if (pts.length === 1) pts.unshift(m.at); const curve = new THREE.CatmullRomCurve3(pts.map(([x, z]) => V3(x, 0, z)), false, 'centripetal'); m.path = curve; m.len = curve.getLength(); m.t0 = t0; m.speed = speed; m.at = pts[0]; m.sStop = null; if (m.stop) F.stopAt(i, m.stopW[0], m.stopW[1]); return F; },
    stopAt(i, c, radius) { const m = moles[i]; m.stopW = [c, radius]; const cl = toLocal(c), rr = radius / STUD; m.stop = [cl, rr]; if (m.path) { const N = 200; m.sStop = null; for (let k = 0; k <= N; k++) { const s = (k / N) * m.len, q = m.path.getPointAt(s / m.len); if (Math.hypot(q.x - cl[0], q.z - cl[1]) <= rr + 0.85 * m.scale) { m.sStop = s; break; } } } return F; },
    swallow(i, target, t0, { depth = 2.2, radius = 0.85 } = {}) { const obj = target && target.isObject3D ? target : null; const wp = obj ? [obj.position.x, obj.position.z] : target; swallows.push({ i, c: toLocal(wp), t0, obj, y0: obj ? obj.position.y : 0, depth: depth * STUD, R: radius }); return F; },
    pushBack(c, r0, r1, t0, dur = 0.5) { pushes.push({ c: toLocal(c), r0: r0 / STUD, r1: r1 / STUD, t0, dur }); return F; },
    // world-metre height of the turf at a point (for placing props on it)
    heightAt(p, t) { F.update(t); const [x, z] = toLocal(p); const ix = Math.round((x - x0) / dx), iz = Math.round((z - z0) / dz); if (ix < 0 || iz < 0 || ix > nx || iz > nz) return 0; return H[iz * (nx + 1) + ix] * STUD; },
    update,
  };
  // mole kinematics (field studs): position, heading, height factor, state flags
  function stateAt(m, t) {
    let x = m.at[0], z = m.at[1], hx = m.h0[0], hz = m.h0[1], moving = false, stopped = false, tStop = null;
    if (m.path) { let s = Math.max(0, Math.min(m.len, m.speed * (t - m.t0))); if (m.sStop != null) { tStop = m.t0 + m.sStop / m.speed; if (s >= m.sStop) { s = m.sStop; stopped = true; } } moving = t > m.t0 && s < m.len && !stopped; const u = Math.max(0, Math.min(1, s / m.len)); const q = m.path.getPointAt(u), tg = m.path.getTangentAt(Math.min(0.999, Math.max(0.001, u))); x = q.x; z = q.z; hx = tg.x; hz = tg.z; const l = Math.hypot(hx, hz) || 1; hx /= l; hz /= l; }
    let hk = 1;
    for (const pb of pushes) { if (t < pb.t0) continue; const u = anim.ease.outCubic(Math.min(1, (t - pb.t0) / pb.dur)); const vx = x - pb.c[0], vz = z - pb.c[1], d = Math.hypot(vx, vz) || 1e-3; if (d < pb.r1 + 1.5) { const target = Math.max(d, pb.r1 + Math.max(0, d - pb.r0) * 0.5 + 0.4 * m.scale); const nd = lerp(d, target, u); x = pb.c[0] + (vx / d) * nd; z = pb.c[1] + (vz / d) * nd; hk *= 1 - 0.35 * Math.sin(PI * Math.min(1, u)); if (u < 1) { hx = vx / d; hz = vz / d; } } }
    let rise = m.rise ? (t < m.rise[0] ? 0 : anim.ease.outBack(Math.min(1, (t - m.rise[0]) / m.rise[1]))) : 1;
    let sinkK = 1; if (m.sink && t >= m.sink[0]) sinkK = 1 - anim.ease.inQuad(Math.min(1, (t - m.sink[0]) / m.sink[1]));
    let flat = 1; if (stopped) flat = 0.72 + 0.28 * Math.exp(-(t - tStop) * 7) * Math.cos((t - tStop) * 20);
    for (const sw of swallows) if (sw.i === m.i && t >= sw.t0 - 0.05) hk *= Math.max(0, 1 - (t - sw.t0 + 0.05) / 0.1); // the bulge becomes the mouth
    return { x, z, hx, hz, moving, stopped, tStop, rise, sinkK, k: rise * sinkK * hk * flat };
  }
  function addGauss(cx, cz, hx, hz, sf, sb, sw, h) { // asymmetric gaussian bulge (front sf, back sb, width sw)
    const R = 3 * Math.max(sf, sb, sw); const i0 = Math.max(0, Math.floor((cx - R - x0) / dx)), i1 = Math.min(nx, Math.ceil((cx + R - x0) / dx)), j0 = Math.max(0, Math.floor((cz - R - z0) / dz)), j1 = Math.min(nz, Math.ceil((cz + R - z0) / dz));
    for (let j = j0; j <= j1; j++) for (let i = i0; i <= i1; i++) { const k = j * (nx + 1) + i, vx = x0 + i * dx - cx, vz = z0 + j * dz - cz; const a = vx * hx + vz * hz, b = -vx * hz + vz * hx; const sa = a > 0 ? sf : sb; const e = (a * a) / (sa * sa) + (b * b) / (sw * sw); if (e < 9) H[k] += h * Math.exp(-e); }
  }
  function addRidge(ax, az, bx, bz, h, w) { // raised trench ridge along a segment (max-combined)
    const R = 3 * w; const i0 = Math.max(0, Math.floor((Math.min(ax, bx) - R - x0) / dx)), i1 = Math.min(nx, Math.ceil((Math.max(ax, bx) + R - x0) / dx)), j0 = Math.max(0, Math.floor((Math.min(az, bz) - R - z0) / dz)), j1 = Math.min(nz, Math.ceil((Math.max(az, bz) + R - z0) / dz));
    for (let j = j0; j <= j1; j++) for (let i = i0; i <= i1; i++) { const k = j * (nx + 1) + i; const [d] = distSeg(x0 + i * dx, z0 + j * dz, ax, az, bx, bz); const v = h * Math.exp(-(d * d) / (w * w)); if (v > R2[k]) R2[k] = v; }
  }
  const R2 = new Float32Array(NV);
  function update(t) {
    H.fill(0); R2.fill(0);
    for (const m of moles) {
      const s = stateAt(m, t); m.state = s; const sc = m.scale;
      const wob = 1 + 0.06 * Math.sin(2 * PI * 1.3 * t + m.ph);
      if (s.k > 0.002) { const lumpy = 1 + 0.12 * noise2(s.x * 0.5 + m.ph, s.z * 0.5, fseed + 7); addGauss(s.x, s.z, s.hx, s.hz, (s.moving ? 0.62 : 0.78) * sc * (s.stopped ? 0.8 : 1), (s.moving ? 1.05 : 0.8) * sc, 0.8 * sc * (s.stopped ? 1.18 : 1), m.height * sc * s.k * wob * lumpy); }
      // sink settle: a shallow dip that relaxes
      if (m.sink && t > m.sink[0] + m.sink[1]) { const u = t - m.sink[0] - m.sink[1]; addGauss(s.x, s.z, 1, 0, 0.7 * sc, 0.7 * sc, 0.7 * sc, -0.05 * sc * Math.exp(-u * 3) * Math.cos(u * 9)); }
      if (m.path && t > m.t0) { // trench ridge over the last 3 s of travel
        const tA = Math.max(m.t0, t - 3), step = 0.1; let prev = null;
        for (let tau = tA; tau <= t + 1e-6; tau += step) { const q = stateAt(m, tau); if (prev && (Math.abs(q.x - prev.x) + Math.abs(q.z - prev.z) > 0.01)) { const age = t - tau; const h = 0.25 * sc * Math.pow(Math.max(0, 1 - age / 3), 1.5) * Math.min(prev.rise, q.rise); if (h > 0.004) addRidge(prev.x, prev.z, q.x, q.z, h, 0.32 * sc); } prev = q; }
      }
    }
    for (const sw of swallows) { // GULP
      const u = t - sw.t0; if (u < -0.02) { if (sw.obj) { sw.obj.position.y = sw.y0; sw.obj.visible = true; } continue; }
      // lips rise round the target (0-0.12 s), close over it like a mouth (0.12-0.24 s), then the dome deflates to a low seal
      const R = sw.R; let ringR, ringH, bump;
      if (u < 0.12) { const a = Math.max(0, u + 0.02) / 0.14; ringR = R * 1.1; ringH = 0.72 * anim.ease.outQuad(a); bump = 0.05 * a; }
      else if (u < 0.24) { const a = (u - 0.12) / 0.12; ringR = R * (1.1 - 0.85 * anim.ease.inQuad(a)); ringH = 0.72 * (1 - 0.6 * a); bump = 0.05 + 0.4 * a; }
      else { const v = u - 0.24; ringR = R * 0.25; ringH = 0.29 * Math.exp(-v * 14); bump = 0.14 + 0.31 * Math.exp(-v * 5.5) + 0.05 * Math.exp(-v * 5) * Math.sin(v * 24); }
      const [cx, cz] = sw.c; const Rr = 2.6 * R; const i0 = Math.max(0, Math.floor((cx - Rr - x0) / dx)), i1 = Math.min(nx, Math.ceil((cx + Rr - x0) / dx)), j0 = Math.max(0, Math.floor((cz - Rr - z0) / dz)), j1 = Math.min(nz, Math.ceil((cz + Rr - z0) / dz));
      for (let j = j0; j <= j1; j++) for (let i = i0; i <= i1; i++) { const k = j * (nx + 1) + i; const d = Math.hypot(x0 + i * dx - cx, z0 + j * dz - cz); if (ringH > 0) H[k] += ringH * Math.exp(-(((d - ringR) / (0.5 * R)) ** 2)) * (d < ringR ? 0.85 : 1); if (bump > 0) H[k] += bump * Math.exp(-((d / (0.95 * R)) ** 2)); }
      if (sw.obj) { const a = sat((u - 0.1) / (6 / 60)); sw.obj.position.y = sw.y0 - sw.depth * anim.ease.inQuad(a); sw.obj.visible = a < 0.999; }
    }
    const pa = geo.attributes.position, na = geo.attributes.normal;
    for (let k = 0; k < NV; k++) { const h = Math.max(H[k], R2[k]); H[k] = h; pa.setY(k, h); alpha[k] = smooth(0.006, 0.05, h); }
    for (let j = 0; j <= nz; j++) for (let i = 0; i <= nx; i++) {
      const k = j * (nx + 1) + i; const hl = H[j * (nx + 1) + Math.max(0, i - 1)], hr = H[j * (nx + 1) + Math.min(nx, i + 1)], hd = H[Math.max(0, j - 1) * (nx + 1) + i], hu = H[Math.min(nz, j + 1) * (nx + 1) + i];
      const ux = -(hr - hl) / (2 * dx), uz = -(hu - hd) / (2 * dz); const l = Math.hypot(ux, 1, uz); na.setXYZ(k, ux / l, 1 / l, uz / l);
      const slope = Math.hypot(ux, uz), hn = H[k] / 0.75;
      soil[k] = Math.min(1, smooth(0.42, 0.7, hn) * smooth(0.86, 0.95, crackN[k]) + 0.75 * smooth(0.55, 1.1, slope) * smooth(0.72, 0.93, crackN[k]));
      const c = (1 - 0.45 * smooth(0.1, 0.8, slope)) * (1 + 0.14 * smooth(0.3, 0.8, hn) * (1 - smooth(0.1, 0.5, slope))) * (1 - 0.3 * soil[k]); col[k * 3] = col[k * 3 + 1] = col[k * 3 + 2] = c;
    }
    pa.needsUpdate = true; na.needsUpdate = true; geo.attributes.soil.needsUpdate = true; geo.attributes.turfAlpha.needsUpdate = true; geo.attributes.color.needsUpdate = true;
    // heads ride at the bulge fronts
    for (const m of moles) {
      // the head rides just inside the bulge front: eyes level with the turf, the star nose out at the foot of the slope
      if (!m.head) continue; const s = m.state; const sc = m.scale; const hs = sc * 0.85, ef = eyeFrame(); const fx = s.x + s.hx * 0.35 * sc, fz = s.z + s.hz * 0.35 * sc;
      const Hat = (x, z) => { const ix = Math.round((x - x0) / dx), iz = Math.round((z - z0) / dz); return ix >= 0 && iz >= 0 && ix <= nx && iz <= nz ? H[iz * (nx + 1) + ix] : 0; };
      const he = Hat(fx + s.hx * ef.c.z * hs, fz + s.hz * ef.c.z * hs), hsn = Hat(fx + s.hx * 0.6 * hs, fz + s.hz * 0.6 * hs);
      let ry = he + 0.015 - (HEAD_AT.y + ef.c.y) * hs; const snoutY = ry + (HEAD_AT.y - 0.02) * hs; if (snoutY < hsn + 0.06 * sc) ry += hsn + 0.06 * sc - snoutY;
      const k = s.k; m.head.visible = k > 0.05;
      m.head.position.set((fx - s.hx * HEAD_AT.z * hs) * STUD, (ry - (1 - Math.min(1, k)) * 0.7 * sc) * STUD, (fz - s.hz * HEAD_AT.z * hs) * STUD);
      m.head.rotation.y = Math.atan2(s.hx, s.hz);
      const rec = Math.max(m.recoil != null ? moleRecoil(t, m.recoil) : 0, s.stopped ? moleRecoil(t, s.tStop) : 0);
      const ev = eyesOn(t, m.eyesOn) * eyesOff(t, m.eyesOff ?? (m.sink ? m.sink[0] + 0.1 : null));
      setMole(m.head, { t: t + m.ph, rise: Math.min(1, k + 0.2), open: 1, recoil: rec, sniff: s.moving ? 0.4 : 0, emerge: 0, eyes: ev, breathe: 1 });
    }
  }
  if (o.count) { // convenience: N moles scattered over the field, risen at t = 0
    const r = makeRng(hash32('fieldScatter', fseed)); for (let i = 0; i < o.count; i++) { const lx = (r() - 0.5) * size[0] * 0.8, lz = (r() - 0.5) * size[1] * 0.8; const w = V3(lx * STUD, 0, lz * STUD).applyMatrix4(G.matrixWorld); F.add({ at: [w.x, w.z], scale: 0.75 + r() * 0.5 }); }
  }
  update(0); return F;
}

// ==================================================================================================================
//  NEXT DOOR'S DOG (REX): a Roblox-built beagle
// ==================================================================================================================
// makeDog({ coat, patch, ears, collar, head: 0.8, units }) -> root (metres), studs inside, faces +z, feet at y 0.
// Parts: dogBody, dogHead (neck pivot), dogEarL/R (hinged at the top), dogTail, dogLeg{FL,FR,BL,BR} (hip pivots),
// collar + `leadSocket` (attach the lead there). Poses: 'stand' 'sit' 'lie' 'chew'; dogAt(dog, t, { pose, chew, wag }).
const DOG_DEFAULTS = { coat: '#c98a4a', patch: '#f2ece2', ears: '#6a3a1e', saddle: '#5a3420', collar: '#d0242a', head: 0.8 };
function paintBox(name, w, h, d, painter, ppu = 128) {
  return cached(keyOf('ep01DogAtlas', name, w, h, d), () => {
    const AW = 2 * w + 2 * d, AH = h + d, c = canvas(AW * ppu, AH * ppu), g = c.getContext('2d'), R = faceRects(w, h, d);
    for (const f of ['nx', 'pz', 'px', 'nz', 'py', 'ny']) { const [rx, ry, fw, fh] = R[f]; g.save(); g.setTransform(ppu, 0, 0, ppu, rx * ppu, ry * ppu); g.beginPath(); g.rect(0, 0, fw, fh); g.clip(); painter(g, f, fw, fh); g.restore(); }
    return canvasTex(c);
  });
}
function blotch(g, x, y, rx, ry, color, seed, a = 1) { const r = makeRng(seed); g.fillStyle = color; g.globalAlpha = a; g.beginPath(); const n = 18; for (let i = 0; i <= n; i++) { const t = (i / n) * 2 * PI, k = 1 + 0.18 * Math.sin(t * 3 + r() * 6) * 0.6 + (r() - 0.5) * 0.12; const px = x + Math.cos(t) * rx * k, py = y + Math.sin(t) * ry * k; i ? g.lineTo(px, py) : g.moveTo(px, py); } g.closePath(); g.fill(); g.globalAlpha = 1; }
function furStrokes(g, w, h, color, n, seed, a = 0.12) { const r = makeRng(seed); g.strokeStyle = color; g.lineWidth = 0.012; g.globalAlpha = a; for (let i = 0; i < n; i++) { const x = r() * w, y = r() * h, L = 0.04 + r() * 0.05; g.beginPath(); g.moveTo(x, y); g.lineTo(x + (r() - 0.5) * 0.02, y + L); g.stroke(); } g.globalAlpha = 1; }
function dogMaterials(P) {
  return cached(keyOf('ep01DogMats', P), () => {
    const std = (map, rough = 0.62) => new THREE.MeshStandardMaterial({ map, roughness: rough, metalness: 0 });
    // body 1.1 (x) x 1.0 (y) x 2.2 (z): tan coat, dark saddle on the back, white chest + belly
    const body = paintBox('body' + JSON.stringify(P), 1.1, 1.0, 2.2, (g, f, w, h) => {
      g.fillStyle = P.coat; g.fillRect(-1, -1, w + 2, h + 2);
      if (f === 'py') { blotch(g, w / 2, h * 0.55, w * 0.55, h * 0.36, P.saddle, 3); }
      if (f === 'px' || f === 'nx') { blotch(g, w * 0.55, -0.05, w * 0.42, 0.42, P.saddle, f === 'px' ? 5 : 6); g.fillStyle = P.patch; g.beginPath(); g.moveTo(-0.1, h); g.bezierCurveTo(w * 0.3, h * 0.62, w * 0.7, h * 0.7, w + 0.1, h * 0.75); g.lineTo(w + 0.1, h + 0.1); g.lineTo(-0.1, h + 0.1); g.fill(); }
      if (f === 'pz') { g.fillStyle = P.patch; g.beginPath(); g.moveTo(w * 0.18, -0.02); g.bezierCurveTo(w * 0.3, h * 0.5, w * 0.7, h * 0.5, w * 0.82, -0.02); g.lineTo(w + 0.1, h + 0.1); g.lineTo(-0.1, h + 0.1); g.fill(); }
      if (f === 'nz') { blotch(g, w / 2, 0.05, w * 0.48, 0.3, P.saddle, 8); }
      if (f === 'ny') { g.fillStyle = P.patch; g.fillRect(-1, -1, w + 2, h + 2); }
      furStrokes(g, w, h, '#2a1408', 90, f.length * 7 + 1);
      if (f !== 'py' && f !== 'ny') { const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, 'rgba(255,255,255,0.08)'); gr.addColorStop(1, 'rgba(40,10,0,0.16)'); g.fillStyle = gr; g.fillRect(-1, -1, w + 2, h + 2); }
    });
    const legF = paintBox('legF' + JSON.stringify(P), 0.35, 0.7, 0.35, (g, f, w, h) => { g.fillStyle = P.patch; g.fillRect(-1, -1, w + 2, h + 2); if (f !== 'ny') { g.fillStyle = P.coat; g.globalAlpha = f === 'py' ? 1 : 0.9; g.fillRect(-1, -1, w + 2, f === 'py' ? h + 2 : h * 0.28); g.globalAlpha = 1; } if (f !== 'py' && f !== 'ny') { g.fillStyle = 'rgba(60,30,20,0.35)'; for (let k = 1; k < 3; k++) g.fillRect(k * w / 3 - 0.006, h - 0.07, 0.012, 0.07); g.fillStyle = 'rgba(40,10,0,0.18)'; g.fillRect(-1, h - 0.03, w + 2, 0.03); } furStrokes(g, w, h, '#3a2010', 12, 4); });
    const legB = paintBox('legB' + JSON.stringify(P), 0.35, 0.7, 0.35, (g, f, w, h) => { g.fillStyle = P.coat; g.fillRect(-1, -1, w + 2, h + 2); if (f !== 'py') { g.fillStyle = P.patch; g.fillRect(-1, h * 0.55, w + 2, h); } if (f !== 'py' && f !== 'ny') { g.fillStyle = 'rgba(60,30,20,0.35)'; for (let k = 1; k < 3; k++) g.fillRect(k * w / 3 - 0.006, h - 0.07, 0.012, 0.07); } furStrokes(g, w, h, '#3a2010', 12, 5); });
    const ear = paintBox('ear' + JSON.stringify(P), 0.14, 0.52, 0.34, (g, f, w, h) => { g.fillStyle = P.ears; g.fillRect(-1, -1, w + 2, h + 2); const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, 'rgba(0,0,0,0.15)'); gr.addColorStop(1, 'rgba(255,220,180,0.1)'); g.fillStyle = gr; g.fillRect(-1, -1, w + 2, h + 2); furStrokes(g, w, h, '#1a0a04', 20, 9, 0.2); });
    const tail = paintBox('tail' + JSON.stringify(P), 0.16, 0.16, 0.5, (g, f, w, h) => { g.fillStyle = P.coat; g.fillRect(-1, -1, w + 2, h + 2); if (f === 'nz') { g.fillStyle = P.patch; g.fillRect(-1, -1, w + 2, h + 2); } else if (f !== 'pz') { g.fillStyle = P.patch; if (f === 'py' || f === 'ny') g.fillRect(-1, h * 0.65, w + 2, h); else g.fillRect(w * 0.62, -1, w, h + 2); } });
    // muzzle 0.42 x 0.28 x 0.24 (white, black nose block on top, mouth line + pink tongue on the front)
    const muzzle = paintBox('muzzle' + JSON.stringify(P), 0.42, 0.28, 0.24, (g, f, w, h) => {
      g.fillStyle = P.patch; g.fillRect(-1, -1, w + 2, h + 2);
      if (f === 'pz') { g.strokeStyle = '#141414'; g.lineWidth = 0.022; g.lineCap = 'round'; g.beginPath(); g.moveTo(w / 2, h * 0.18); g.lineTo(w / 2, h * 0.45); g.stroke(); g.beginPath(); g.arc(w / 2 - 0.055, h * 0.45, 0.055, 0, PI); g.stroke(); g.beginPath(); g.arc(w / 2 + 0.055, h * 0.45, 0.055, 0, PI); g.stroke();
        g.fillStyle = '#e2405a'; g.beginPath(); g.moveTo(w / 2 + 0.005, h * 0.52); g.lineTo(w / 2 + 0.095, h * 0.52); g.lineTo(w / 2 + 0.095, h * 0.86); g.arc(w / 2 + 0.05, h * 0.86, 0.045, 0, PI); g.closePath(); g.fill(); g.strokeStyle = '#141414'; g.lineWidth = 0.014; g.stroke(); g.strokeStyle = 'rgba(120,10,30,0.6)'; g.beginPath(); g.moveTo(w / 2 + 0.05, h * 0.56); g.lineTo(w / 2 + 0.05, h * 0.8); g.stroke();
        g.fillStyle = 'rgba(90,50,30,0.5)'; for (const [x, y] of [[0.1, 0.35], [0.14, 0.5], [0.09, 0.55], [0.32, 0.35], [0.28, 0.5], [0.33, 0.55]]) { g.beginPath(); g.arc(x, y * h / 0.5 * 0.5, 0.008, 0, 2 * PI); g.fill(); } }
    });
    const headTex = cached(keyOf('ep01DogHeadTex', P), () => { const N = 256, c = canvas(N), g = c.getContext('2d'); g.fillStyle = P.coat; g.fillRect(0, 0, N, N); const r = makeRng(12); g.strokeStyle = 'rgba(40,20,5,0.12)'; g.lineWidth = 1.2; for (let i = 0; i < 500; i++) { const x = r() * N, y = r() * N; g.beginPath(); g.moveTo(x, y); g.lineTo(x + (r() - 0.5) * 2, y + 3 + r() * 4); g.stroke(); } return canvasTex(c, { wrap: true }); });
    return { body: std(body), legF: std(legF), legB: std(legB), ear: std(ear, 0.7), tail: std(tail), muzzle: std(muzzle, 0.58), head: std(headTex, 0.6),
      nose: new THREE.MeshPhysicalMaterial({ color: '#1a1214', roughness: 0.18, clearcoat: 1, clearcoatRoughness: 0.05 }),
      collar: new THREE.MeshStandardMaterial({ color: P.collar, roughness: 0.45 }), tag: new THREE.MeshStandardMaterial({ color: '#e0b43a', roughness: 0.28, metalness: 0.85 }), ring: new THREE.MeshStandardMaterial({ color: '#c8c8d0', roughness: 0.3, metalness: 0.9 }) };
  });
}
// Dog face decal (on the drum's face band): ^^ eyes with little lashes, a soft white blaze, rosy cheeks.
function dogFaceTex(P, eyes = 'content') {
  return cached(keyOf('ep01DogFace', P.patch, eyes), () => {
    const N = 1024, c = canvas(N), g = c.getContext('2d'); g.scale(N / 512, N / 512);
    g.fillStyle = rgba(P.patch, 0.95); g.beginPath(); g.moveTo(236, 120); g.bezierCurveTo(232, 220, 196, 300, 176, 512); g.lineTo(336, 512); g.bezierCurveTo(316, 300, 280, 220, 276, 120); g.closePath(); g.fill();
    for (const x of [168, 344]) { const gr = g.createRadialGradient(x, 330, 0, x, 330, 44); gr.addColorStop(0, 'rgba(255,120,130,0.35)'); gr.addColorStop(1, 'rgba(255,120,130,0)'); g.fillStyle = gr; g.fillRect(x - 50, 280, 100, 100); }
    g.strokeStyle = '#141414'; g.lineCap = 'round'; g.lineWidth = 12;
    if (eyes === 'content') { for (const x of [184, 328]) { g.beginPath(); g.arc(x, 262, 30, 200 * DEG, 340 * DEG); g.stroke(); } }
    else { for (const x of [184, 328]) { g.fillStyle = '#141414'; g.beginPath(); g.ellipse(x, 250, 22, 30, 0, 0, 2 * PI); g.fill(); g.fillStyle = '#ffffff'; g.beginPath(); g.arc(x - 7, 238, 7, 0, 2 * PI); g.fill(); } }
    g.lineWidth = 6; for (const [x, s] of [[184, -1], [328, 1]]) { g.beginPath(); g.moveTo(x + s * 26, 250); g.lineTo(x + s * 38, 238); g.stroke(); }
    return canvasTex(c);
  });
}
export function makeDog(opts = {}) {
  const P = { ...DOG_DEFAULTS, ...opts }; const Mt = dogMaterials({ coat: P.coat, patch: P.patch, ears: P.ears, saddle: P.saddle, collar: P.collar });
  const root = makeRoot('dog', P.units); root.userData.kit = 'dog';
  const rb = (w, h, d, r = 0.06) => cached(keyOf('ep01DogBox', w, h, d, r), () => atlasUV(new RoundedBoxGeometry(w, h, d, 3, r), w, h, d));
  const body = group('dogBody', root); const torso = group('dogTorso', body, [0, 1.2, 0]);
  mesh(rb(1.1, 1.0, 2.2), Mt.body, { parent: torso, name: 'dogTorsoMesh' });
  for (const [nm, x, z, mt] of [['FL', 0.3, 0.78, Mt.legF], ['FR', -0.3, 0.78, Mt.legF], ['BL', 0.3, -0.8, Mt.legB], ['BR', -0.3, -0.8, Mt.legB]]) { const hp = group('dogLeg' + nm, torso, [x, -0.5, z]); mesh(rb(0.35, 0.7, 0.35, 0.05), mt, { parent: hp, name: 'dogLegMesh' + nm, pos: [0, -0.35, 0] }); }
  const neck = group('dogNeck', torso, [0, 0.38, 1.0]); const hs = P.head / 1.2;
  const head = group('dogHead', neck, [0, 0.42 * hs / 0.667, 0.22]); head.scale.setScalar(hs);
  mesh(headGeo(), Mt.head, { parent: head, name: 'dogHeadMesh' });
  const fm = new THREE.MeshStandardMaterial({ map: dogFaceTex(P), transparent: true, roughness: 0.55, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2, depthWrite: false });
  mesh(faceBandGeo(), fm, { parent: head, name: 'dogFace', cast: false, order: 1 }).userData.claimed = true;
  const mz = group('dogMuzzle', head, [0, -0.24, 0.62]); mesh(rb(0.42 / hs * 0.9, 0.28 / hs * 0.9, 0.24 / hs * 0.9, 0.05), Mt.muzzle, { parent: mz, name: 'dogMuzzleMesh' });
  mesh(cached('ep01DogNose', () => { const g = new THREE.SphereGeometry(0.12, 24, 16); g.scale(1.15, 0.72, 0.8); return g; }), Mt.nose, { parent: mz, name: 'dogNose', pos: [0, 0.13, 0.17] });
  for (const [nm, s] of [['L', 1], ['R', -1]]) { const ep = group('dogEar' + nm, head, [s * 0.62, 0.38, -0.05]); mesh(rb(0.14 / hs, 0.52 / hs, 0.34 / hs, 0.05), Mt.ear, { parent: ep, name: 'dogEarMesh' + nm, pos: [s * 0.08 / hs, -0.24 / hs, 0] }); ep.rotation.z = s * 0.18; }
  const tl = group('dogTail', torso, [0, 0.35, -1.08]); mesh(rb(0.16, 0.16, 0.5, 0.05), Mt.tail, { parent: tl, name: 'dogTailMesh', pos: [0, 0, -0.22] }); tl.rotation.x = 0.75;
  const col = group('collar', neck, [0, 0.12, 0.05]); const cg = cached('ep01DogCollar', () => { const g = new THREE.TorusGeometry(0.4, 0.07, 10, 36); g.rotateX(PI / 2); g.scale(1, 1, 0.85); return g; }); mesh(cg, Mt.collar, { parent: col, name: 'collarBand' }); col.rotation.x = 0.55;
  mesh(cached('ep01DogTag', () => { const g = new THREE.CylinderGeometry(0.08, 0.08, 0.025, 20); g.rotateX(PI / 2); return g; }), Mt.tag, { parent: col, name: 'collarTag', pos: [0, -0.1, 0.36] });
  const ls = group('leadSocket', col, [0, 0.06, -0.4]); mesh(cached('ep01DogRing', () => new THREE.TorusGeometry(0.06, 0.015, 8, 20)), Mt.ring, { parent: ls, name: 'leadRing' });
  root.add(shadowBlob(1.9, 3.0, 0.32));
  setDogPose(root, 'stand'); return root;
}
export const DOG_POSES = {
  stand: {},
  sit: { bodyPitch: 23.5, lift: -0.27, legF: -23.5, legB: 66.5, neck: -16 },
  lie: { lift: -0.52, legF: 90, legB: -90, neck: -4 },
  chew: { lift: -0.52, legF: 90, legB: -90, neck: 25 },
};
// setDogPose(dog, name | { bodyPitch, lift, legF, legB, neck, headYaw, headRoll, tail, ears }) - degrees / studs
export function setDogPose(root, p) {
  const P = typeof p === 'string' ? DOG_POSES[p] || {} : p; const f = (n) => root.getObjectByName(n);
  const torso = f('dogTorso'); torso.rotation.x = -(P.bodyPitch || 0) * DEG; torso.position.y = 1.2 + (P.lift || 0); torso.position.z = P.liftZ || 0;
  for (const n of ['FL', 'FR']) f('dogLeg' + n).rotation.x = -(P.legF || 0) * DEG + (P.bodyPitch || 0) * DEG * 0;
  for (const n of ['BL', 'BR']) f('dogLeg' + n).rotation.x = -(P.legB || 0) * DEG;
  if (P.legSplay) { f('dogLegFL').rotation.z = P.legSplay * DEG; f('dogLegFR').rotation.z = -P.legSplay * DEG; }
  const nk = f('dogNeck'); nk.rotation.set((P.neck || 0) * DEG, (P.headYaw || 0) * DEG, (P.headRoll || 0) * DEG, 'YXZ');
  const tl = f('dogTail'); tl.rotation.set(0.75 + (P.tailLift || 0) * DEG, (P.tail || 0) * DEG, 0, 'YXZ');
  for (const [n, s] of [['L', 1], ['R', -1]]) { const e = f('dogEar' + n); e.rotation.set((P.ears || 0) * DEG * 0.5, 0, s * (0.18 + (P.earsOut || 0) * DEG)); }
  return root;
}
// Pure function of t: pose + tail wag (+-25 deg at 6 Hz) + chew bob (2 Hz) + breathing + floppy ears (lag behind the head).
export function dogAt(root, t, { pose = 'stand', chew = pose === 'chew', wag = 1, wagFreq = 6, look = [0, 0], blink = null } = {}) {
  const base = { ...(typeof pose === 'string' ? DOG_POSES[pose] : pose) };
  const bob = chew ? 6 * Math.sin(2 * PI * 2 * t) + 3 * Math.sin(2 * PI * 4 * t + 0.6) : 0;
  base.neck = (base.neck || 0) + bob + (look[1] || 0); base.headYaw = (base.headYaw || 0) + (look[0] || 0) + (chew ? 4 * Math.sin(2 * PI * 1 * t) : 0); base.headRoll = (base.headRoll || 0) + (chew ? 5 * Math.sin(2 * PI * 2 * t + 1.1) : 0);
  base.tail = wag * 25 * Math.sin(2 * PI * wagFreq * t); base.tailLift = 6 * Math.sin(2 * PI * 0.5 * t);
  base.ears = -bob * 1.4 + 6 * anim.jiggle(t % 0.5, 0, 1, 3, 6); base.earsOut = chew ? 4 * Math.sin(2 * PI * 2 * t - 0.9) : 0;
  setDogPose(root, base);
  const torso = root.getObjectByName('dogTorso'); torso.scale.set(1, 1 + 0.012 * Math.sin(2 * PI * 0.9 * t), 1);
  return root;
}

// ==================================================================================================================
//  THEO'S STUFFED WHALE (grey-blue plush)
// ==================================================================================================================
const WHALE_PROF = [[0, -0.66], [0.05, -0.645], [0.07, -0.57], [0.105, -0.46], [0.16, -0.32], [0.23, -0.16], [0.3, 0.02], [0.35, 0.2], [0.372, 0.35], [0.36, 0.48], [0.315, 0.58], [0.23, 0.655], [0.12, 0.69], [0, 0.7]];
const whaleBend = (z) => (z < -0.12 ? 0.23 * Math.pow((-z - 0.12) / 0.54, 2) : 0); // the tail curls up
function whaleTexture(color, belly) {
  return cached(keyOf('ep01WhaleTex', color, belly), () => {
    const W = 512, Hh = 512, c = canvas(W, Hh), g = c.getContext('2d'); g.fillStyle = color; g.fillRect(0, 0, W, Hh);
    // lathe u: 0 = bottom (belly, after the z-lathe flip), 0.5 = top; v: 0 tail .. 1 nose
    const band = (u0, u1, col) => { g.fillStyle = col; g.fillRect(u0 * W, 0, (u1 - u0) * W, Hh); };
    g.save(); g.beginPath(); g.rect(0, Hh * 0.12, W, Hh * 0.82); g.clip();
    band(0, 0.17, belly); band(0.83, 1, belly);
    g.strokeStyle = rgba(shade(belly, 0.72), 0.75); g.lineWidth = 5; for (const u of [-0.11, -0.055, 0, 0.055, 0.11]) { const x = ((u + 1) % 1) * W; g.beginPath(); g.moveTo(x, Hh * 0.22); g.lineTo(x, Hh * 0.86); g.stroke(); if (u === 0) { g.beginPath(); g.moveTo(W, Hh * 0.22); g.lineTo(W, Hh * 0.86); g.stroke(); } }
    g.restore();
    g.setLineDash([10, 8]); g.strokeStyle = rgba(shade(color, 0.55), 0.8); g.lineWidth = 3; for (const u of [0.18, 0.82]) { g.beginPath(); g.moveTo(u * W, Hh * 0.1); g.lineTo(u * W, Hh * 0.96); g.stroke(); } g.setLineDash([]);
    // stitched smile near the nose on each side (u 0.2 / 0.8)
    g.strokeStyle = '#2a2e3a'; g.lineWidth = 5; g.lineCap = 'round'; for (const u of [0.19, 0.81]) { g.beginPath(); g.moveTo(u * W, Hh * 0.8); g.quadraticCurveTo((u + (u < 0.5 ? 0.035 : -0.035)) * W, Hh * 0.86, u * W, Hh * 0.92); g.stroke(); }
    // plush mottling
    const r = makeRng(4); for (let i = 0; i < 1800; i++) { g.fillStyle = rgba(r() < 0.5 ? '#ffffff' : '#000000', 0.03 + r() * 0.03); g.fillRect(r() * W, r() * Hh, 2 + r() * 3, 2 + r() * 3); }
    const t = canvasTex(c, { wrap: true }); return t;
  });
}
export function stuffedWhale(opts = {}) {
  const P = { color: '#7f93ad', belly: '#dfe6ee', length: 1.4, units: 'm', ...opts };
  const Mt = cached(keyOf('ep01WhaleMats', P.color, P.belly), () => { const F = fabricTex({ color: '#808080', threads: 128, contrast: 0.3, fuzz: 0.2, seed: 7, repeat: [6, 3] });
    return { body: new THREE.MeshPhysicalMaterial({ map: whaleTexture(P.color, P.belly), normalMap: F.normalMap, normalScale: new THREE.Vector2(0.18, 0.18), roughness: 0.9, sheen: 0.7, sheenRoughness: 0.6, sheenColor: new THREE.Color(mix(P.color, '#ffffff', 0.6)) }),
      fin: new THREE.MeshPhysicalMaterial({ color: shade(P.color, 0.88), normalMap: F.normalMap, normalScale: new THREE.Vector2(0.2, 0.2), roughness: 0.92, sheen: 0.6, sheenColor: new THREE.Color(mix(P.color, '#ffffff', 0.5)) }),
      eye: new THREE.MeshPhysicalMaterial({ color: '#141418', roughness: 0.12, clearcoat: 1, clearcoatRoughness: 0.03 }), spout: new THREE.MeshPhysicalMaterial({ color: '#cfe4f4', roughness: 0.8, sheen: 0.6, sheenColor: new THREE.Color('#ffffff') }) }; });
  const root = makeRoot('whale', P.units); const k = P.length / 1.4; const w = group('whaleBody', root); w.scale.setScalar(k);
  const geo = cached('ep01WhaleGeo2', () => { const g = new THREE.LatheGeometry(WHALE_PROF.map(([r, y]) => new THREE.Vector2(r, y)), 56, 0, 2 * PI); g.rotateX(PI / 2); g.rotateZ(PI); g.scale(1, 0.86, 1); const p = g.attributes.position; for (let i = 0; i < p.count; i++) { const z = p.getZ(i), y = p.getY(i); p.setY(i, (y < 0 ? y * (1 - 0.14 * smooth(-0.3, 0.4, z)) : y) + whaleBend(z)); } return smoothNormals(g); });
  mesh(geo, Mt.body, { parent: w, name: 'whaleMesh' });
  const finG = cached('ep01WhaleFin2', () => { const g = new THREE.SphereGeometry(1, 24, 14); g.scale(0.075, 0.032, 0.17); const p = g.attributes.position; for (let i = 0; i < p.count; i++) { const z = p.getZ(i); p.setX(i, p.getX(i) * (1 - 0.45 * smooth(-0.17, 0.17, -z))); } g.translate(0, 0, -0.1); g.computeVertexNormals(); return g; });
  for (const s of [1, -1]) { const f = mesh(finG, Mt.fin, { parent: w, name: 'whaleFin' + (s > 0 ? 'L' : 'R'), pos: [s * 0.3, -0.16, 0.26] }); f.rotation.set(0.35, s * 0.55, s * -0.75); f.scale.set(1.5, 1, 1.4); }
  const flukeG = cached('ep01WhaleFluke2', () => { const g = new THREE.SphereGeometry(1, 24, 12); g.scale(0.19, 0.032, 0.095); const p = g.attributes.position; for (let i = 0; i < p.count; i++) { const x = p.getX(i); p.setZ(i, p.getZ(i) - 0.06 * Math.pow(Math.max(0, x / 0.19), 2)); } g.translate(0.15, 0, 0); g.computeVertexNormals(); return g; });
  const tail = group('whaleTail', w, [0, whaleBend(-0.62) + 0.01, -0.62]); tail.rotation.x = -0.5;
  for (const s of [1, -1]) { const f = mesh(flukeG, Mt.fin, { parent: tail, name: 'whaleFluke' + (s > 0 ? 'L' : 'R') }); f.rotation.set(0, s > 0 ? -0.4 : PI + 0.4, s * 0.12); }
  const eg = cached('ep01WhaleEye2', () => { const g = new THREE.SphereGeometry(0.058, 20, 14); g.scale(1, 1, 0.55); return g; });
  const hl = cached('ep01WhaleEyeHi', () => new THREE.SphereGeometry(0.016, 10, 8)); const hm = cached('ep01WhaleEyeHiM', () => new THREE.MeshBasicMaterial({ color: '#f4f2ff' }));
  for (const s of [1, -1]) { const e = group('whaleEye' + (s > 0 ? 'L' : 'R'), w, [s * 0.335, 0.1, 0.43]); e.rotation.y = s * 1.15; mesh(eg, Mt.eye, { parent: e, name: 'whaleEyeBall' }); mesh(hl, hm, { parent: e, name: 'whaleEyeHi', pos: [-0.012 * s, 0.02, 0.03], cast: false }); }
  const spout = cached('ep01WhaleSpout', () => { const L = []; for (let k = 0; k < 4; k++) { const a = (k / 4) * 2 * PI; const c = new THREE.SphereGeometry(0.045, 12, 10); c.scale(0.7, 1.5, 0.7); c.rotateZ(Math.sin(a) * 0.5); c.rotateX(Math.cos(a) * 0.5); c.translate(Math.sin(a) * 0.03, 0.06, Math.cos(a) * 0.03); L.push(c); } const st = new THREE.CylinderGeometry(0.02, 0.025, 0.08, 10); st.translate(0, 0.0, 0); L.push(st); return mergeList(L); });
  mesh(spout, Mt.spout, { parent: w, name: 'whaleSpout', pos: [0, 0.31, 0.28], rot: [-0.25, 0, 0] });
  return root;
}
// Attach the whale to an avatar: 'hug' (across the chest, both arms round it: use pose 'hug' / 'carry'), 'hand'
// (dangling from the right hand by a fin), 'underArm' (tucked under the left arm), 'asleep' (cuddled, on the side).
export function holdWhale(avatar, whale, mode = 'hug') {
  const R = rig(avatar); const bs = R.body.scale.x || 1; // the avatar rig is in studs: the whale's own studs (unit root scale), real size kept
  const put = (parent, pos, rot) => { whale.scale.setScalar(1 / bs); whale.position.set(...pos); whale.rotation.set(...rot); parent.add(whale); };
  if (mode === 'hug') put(R.hips, [0, 1.2, 0.86], [0.12, PI / 2 - 0.3, 0.1]);
  else if (mode === 'underArm') put(R.hips, [1.18, 1.28, 0.12], [0.2, 0.08, -0.25]);
  else if (mode === 'asleep') put(R.hips, [-0.05, 1.1, 0.82], [0.45, PI / 2 + 0.35, -0.4]);
  else put(handSocket(avatar, 'R'), [0, -0.12, 0.5], [-0.9, 0, 0.1]);
  return whale;
}

// ==================================================================================================================
//  GRANDPA'S FLASHLIGHT
// ==================================================================================================================
// makeFlashlight({ on, light: true | cd (18), angle (22 deg) }) -> root (studs inside a group; metres root). Beam along local -y when
// held (holdFlashlight parents it to the hand socket so the beam runs down the arm, the Roblox tool grip: arm raised =
// beam forward, arm down = beam at the lawn). Parts: torchBody, torchHead, torchLens, torchGlow, torchLight (SpotLight).
export function makeFlashlight(opts = {}) {
  const P = { on: 0, light: true, cd: 18, angle: 22, color: '#fff1d0', ...opts };
  const Mt = cached('ep01TorchMats', () => {
    const N = 128, c = canvas(N, N), g = c.getContext('2d'); g.fillStyle = '#b8261e'; g.fillRect(0, 0, N, N); for (let y = 0; y < N; y += 16) { g.fillStyle = 'rgba(0,0,0,0.28)'; g.fillRect(0, y, N, 5); g.fillStyle = 'rgba(255,255,255,0.12)'; g.fillRect(0, y + 6, N, 3); }
    const tex = canvasTex(c, { wrap: true }); tex.repeat.set(3, 1);
    return { rubber: new THREE.MeshPhysicalMaterial({ color: '#ffffff', map: tex, roughness: 0.55, clearcoat: 0.25, clearcoatRoughness: 0.4 }), chrome: new THREE.MeshStandardMaterial({ color: '#d8dbe2', roughness: 0.18, metalness: 1 }), black: new THREE.MeshStandardMaterial({ color: '#1c1a1e', roughness: 0.6 }),
      reflector: new THREE.MeshStandardMaterial({ color: '#fff6e0', roughness: 0.1, metalness: 1 }) };
  });
  const root = makeRoot('flashlight', P.units); const tb = group('torch', root); // studs; beam along +z inside `torch`
  const body = cached('ep01TorchBody', () => { const g = new THREE.CylinderGeometry(0.105, 0.11, 0.56, 28, 1); g.rotateX(PI / 2); return g; });
  mesh(body, Mt.rubber, { parent: tb, name: 'torchBody', pos: [0, 0, -0.04] });
  const head = cached('ep01TorchHead', () => { const g = new THREE.LatheGeometry([[0.11, -0.12], [0.12, -0.08], [0.16, 0.02], [0.175, 0.08], [0.18, 0.1], [0.168, 0.11], [0.15, 0.1]].map(([r, y]) => new THREE.Vector2(r, y)), 32); g.rotateX(PI / 2); return g; });
  mesh(head, Mt.chrome, { parent: tb, name: 'torchHead', pos: [0, 0, 0.3] });
  const refl = cached('ep01TorchRefl', () => { const g = new THREE.CylinderGeometry(0.15, 0.06, 0.08, 28, 1, true); g.rotateX(-PI / 2); return g; });
  mesh(refl, Mt.reflector, { parent: tb, name: 'torchReflector', pos: [0, 0, 0.36] });
  const lensM = new THREE.MeshStandardMaterial({ color: '#f4f0e6', emissive: new THREE.Color(P.color), emissiveIntensity: 0, roughness: 0.08, transparent: true, opacity: 0.92 });
  mesh(cached('ep01TorchLens', () => new THREE.CircleGeometry(0.152, 32)), lensM, { parent: tb, name: 'torchLens', pos: [0, 0, 0.405], cast: false }).userData.owner = null;
  mesh(cached('ep01TorchCap', () => { const g = new THREE.CylinderGeometry(0.1, 0.112, 0.07, 24); g.rotateX(PI / 2); return g; }), Mt.black, { parent: tb, name: 'torchCap', pos: [0, 0, -0.355] });
  mesh(cached('ep01TorchSwitch', () => new RoundedBoxGeometry(0.07, 0.05, 0.12, 2, 0.02)), Mt.black, { parent: tb, name: 'torchSwitch', pos: [0, 0.115, 0.08] });
  mesh(cached('ep01TorchLoop', () => new THREE.TorusGeometry(0.045, 0.012, 8, 16)), Mt.chrome, { parent: tb, name: 'torchLoop', pos: [0, 0, -0.4], rot: [0, PI / 2, 0] });
  const glow = pxSprite(addMat(radialGlow({ falloff: 2.0 }), new THREE.Color(P.color).multiplyScalar(1.6), { opacity: 0 }), 60); glow.name = 'torchGlow'; glow.position.set(0, 0, 0.43); glow.renderOrder = 12; tb.add(glow);
  if (P.light) { const sp = new THREE.SpotLight(P.color, 0, 0, P.angle * DEG, 0.55, 2); sp.name = 'torchLight'; sp.userData.cd = typeof P.light === 'number' ? P.light : P.cd; sp.position.set(0, 0, 0.42); const tg = new THREE.Object3D(); tg.name = 'torchTarget'; tg.position.set(0, 0, 4); tb.add(tg); sp.target = tg; tb.add(sp); }
  setFlashlight(root, P.on); return root;
}
// on: 0..1 (1 frame click = pass 0 then 1); cd overrides the spot intensity.
export function setFlashlight(root, on = 1, { cd = null, glowPx = null } = {}) {
  const lens = root.getObjectByName('torchLens'); if (lens) { const m = lens.material.userData.owner === lens.uuid ? lens.material : (lens.material = Object.assign(lens.material.clone(), { userData: { owner: lens.uuid } })); m.emissiveIntensity = 3.2 * on; }
  const gl = root.getObjectByName('torchGlow'); if (gl) { if (gl.material.userData.owner !== gl.uuid) gl.material = Object.assign(gl.material.clone(), { userData: { owner: gl.uuid } }); gl.material.opacity = 0.9 * on; gl.userData.px = glowPx ?? 70; gl.visible = on > 0.01; }
  const sp = root.getObjectByName('torchLight'); if (sp) { sp.intensity = (cd ?? sp.userData.cd ?? 6) * on; sp.visible = on > 0.001; }
  return root;
}
// Parent to an avatar's hand: axis 'arm' (beam runs down the arm: raise the arm to aim it) or 'forward' (beam along the
// hand's +z: arm hanging, torch pointing ahead). Returns the flashlight.
export function holdFlashlight(avatar, torch, { side = 'R', axis = 'arm' } = {}) {
  const hs = handSocket(avatar, side); torch.scale.setScalar(1 / (rig(avatar).body.scale.x || 1)); torch.position.set(0, -0.12, 0.0);
  if (axis === 'arm') torch.rotation.set(PI / 2, 0, 0); else torch.rotation.set(0, 0, 0);
  const tb = torch.getObjectByName('torch'); tb.position.set(0, 0, axis === 'arm' ? 0.05 : 0.12);
  hs.add(torch); return torch;
}
// Aim a held flashlight at a world point (e.g. up at the chin for the ghost-story face, or at a spot on the lawn):
// rotates the torch inside the hand socket so its beam points there. Call after setPose (pure: same pose -> same aim).
export function aimFlashlight(torch, worldPoint) {
  const par = torch.parent; if (!par) return torch; par.updateWorldMatrix(true, false); torch.updateWorldMatrix(false, false);
  const from = torch.getWorldPosition(V3()), dir = V3(...(worldPoint.isVector3 ? worldPoint.toArray() : worldPoint)).sub(from).normalize();
  const qp = new THREE.Quaternion(); par.getWorldQuaternion(qp); const qw = new THREE.Quaternion().setFromUnitVectors(V3(0, 0, 1), dir);
  torch.quaternion.copy(qp.invert().multiply(qw)); const tb = torch.getObjectByName('torch'); if (tb) tb.position.set(0, 0, 0.1); return torch;
}
// World-space beam origin + direction (for fx beams / pools): call after the scene's matrices are updated.
export function flashlightRay(torch) { const lens = torch.getObjectByName('torchLens'); lens.updateWorldMatrix(true, false); const o = lens.getWorldPosition(V3()); const d = V3(0, 0, 1).transformDirection(lens.matrixWorld); return { origin: o, dir: d }; }
