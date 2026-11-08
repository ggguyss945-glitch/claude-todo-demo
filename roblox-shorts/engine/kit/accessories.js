// Accessories (VISUAL_BIBLE §2.4): chunky, smooth-shaded UGC meshes in head-local studs (head centre at the origin,
// drum radius 0.6, height ±0.6, face toward +z). Rigid, no secondary motion.
//   hair:      'messy' (EP01 hero), 'short', 'grandpa' (bald crown + puffy side tufts), 'bun' (grandma), 'bob'
//   glasses:   'round' (thin metal rims), 'thick' (plastic rims)
//   hat:       'fishing' (olive bucket hat with lures), 'flatCap', 'beanie'
//   moustache: 'walrus' (3D, like CG's Hank); a decal moustache also exists (faces.js overlays.moustache)
//   hood:      bunched hood behind the neck (hoodies); attaches to the torso
// addAccessory(headGroup, { type, style, color, ... }, { hips }) adds the mesh(es) and returns the group.
import { THREE, cached, keyOf, mesh, group, clumpGeo, canvas, canvasTex, makeRng, hash32, shade, rgba, clamp } from './util.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

// ---------------- materials ----------------
function strandMap(color) { // lengthwise streaks along v (clump and cap UVs run root -> tip)
  return cached(keyOf('strandMap', color), () => {
    const W = 256, H = 256, c = canvas(W, H), g = c.getContext('2d'), r = makeRng(hash32('strand', color));
    g.fillStyle = color; g.fillRect(0, 0, W, H);
    for (let i = 0; i < 90; i++) { const x = r() * W, w = 1 + r() * 4, dark = r() < 0.55; g.fillStyle = rgba(dark ? shade(color, 0.62) : shade(color, 1.35), 0.12 + r() * 0.22); g.fillRect(x, 0, w, H); g.fillRect(x - W, 0, w, H); }
    const gr = g.createLinearGradient(0, 0, 0, H); gr.addColorStop(0, rgba('#ffffff', 0.08)); gr.addColorStop(0.6, rgba('#000000', 0)); gr.addColorStop(1, rgba('#000000', 0.18)); g.fillStyle = gr; g.fillRect(0, 0, W, H);
    return canvasTex(c, { wrap: true });
  });
}
export const hairMat = (color, rough = 0.46) => cached(keyOf('hairMat', color, rough), () => new THREE.MeshStandardMaterial({ color: '#ffffff', map: strandMap(color), roughness: rough, metalness: 0 }));
const plainMat = (color, rough = 0.5, extra = {}) => cached(keyOf('accMat', color, rough, extra), () => new THREE.MeshStandardMaterial({ color, roughness: rough, metalness: 0, ...extra }));
const metalMat = (color) => cached(keyOf('accMetal', color), () => new THREE.MeshStandardMaterial({ color, roughness: 0.3, metalness: 0.85 }));

// ---------------- geometry helpers ----------------
function place(geo, pos, rot = [0, 0, 0], scale = [1, 1, 1]) {
  const m = new THREE.Matrix4().compose(new THREE.Vector3(...pos), new THREE.Quaternion().setFromEuler(new THREE.Euler(rot[0], rot[1], rot[2], 'YXZ')), new THREE.Vector3(...(typeof scale === 'number' ? [scale, scale, scale] : scale)));
  const g = geo.index ? geo.toNonIndexed() : geo.clone(); g.applyMatrix4(m); return g;
}
const merge = (list) => { const g = mergeGeometries(list.map((x) => { const y = x.index ? x.toNonIndexed() : x; for (const k of Object.keys(y.attributes)) if (!['position', 'normal', 'uv'].includes(k)) y.deleteAttribute(k); return y; })); g.computeBoundingSphere(); return g; };
// cap shell over the head top (sphere segment), squashed to hug the drum
function capGeo(R = 0.68, theta = 0.52, sy = 0.8, seg = 40) { return new THREE.SphereGeometry(R, seg, Math.round(seg * 0.5), 0, Math.PI * 2, 0, Math.PI * theta); }
// a clump pointing in direction (yaw, pitch) from an anchor; tip length L
function clumpAt(anchor, yaw, pitch, R, L, bend = 0, curl = 0, seg = 14, roll = 0) {
  // clumpGeo tail runs along -y; rotate so -y points along the requested direction
  const g = clumpGeo(R, L, bend, curl, seg);
  return place(g, anchor, [-pitch, yaw, roll]); // pitch 0 = tail down, PI/2 = outward along yaw (0 = +z), PI = up
}

// ---------------- hair ----------------
const HAIRS = {
  // EP01 hero: one big asymmetric spiky silhouette that reads from behind at 30 px (bible §2.4)
  messy(r) {
    const L = [place(capGeo(0.665, 0.5, 1, 40), [0, 0.12, -0.03], [-0.18, 0, 0], [1.02, 0.82, 1.04])];
    for (let i = 0; i < 18; i++) { // ring of downward/outward clumps around sides + back (skip the face)
      const a = (i / 18) * Math.PI * 2 + 0.17; const front = Math.cos(a) > 0.55; if (front) continue;
      const x = Math.sin(a) * 0.6, z = Math.cos(a) * 0.6;
      L.push(clumpAt([x * 0.95, 0.36 + r() * 0.08, z * 0.95], a, Math.PI * (0.3 + r() * 0.16), 0.17 + r() * 0.04, 0.3 + r() * 0.18, (r() - 0.5) * 0.4, 0.1));
    }
    for (let i = 0; i < 9; i++) { // spikes on top, leaning back-right (asymmetric)
      const a = r() * Math.PI * 2, rr = 0.15 + r() * 0.3;
      L.push(clumpAt([Math.sin(a) * rr, 0.6, Math.cos(a) * rr - 0.05], Math.PI - 0.6 + (r() - 0.5) * 1.6, Math.PI * (0.78 + r() * 0.12), 0.16 + r() * 0.04, 0.34 + r() * 0.22, (r() - 0.5) * 0.5, 0));
    }
    L.push(clumpAt([0.18, 0.62, -0.1], 2.4, Math.PI * 0.7, 0.2, 0.6, 0.35, 0.15)); // the big signature spike
    for (let i = 0; i < 5; i++) { const x = -0.38 + i * 0.19; L.push(clumpAt([x, 0.5, 0.42], 0.25 * (i - 2) * 0.4 + 0.4, Math.PI * 0.18 + r() * 0.08, 0.15, 0.32 + r() * 0.08, 0.25, 0)); } // fringe sweeping to one side
    return L;
  },
  short(r) {
    const L = [place(capGeo(0.655, 0.47, 1, 40), [0, 0.14, -0.02], [-0.14, 0, 0], [1.02, 0.78, 1.04])];
    for (let i = 0; i < 6; i++) { const x = -0.34 + i * 0.14; L.push(clumpAt([x, 0.52, 0.4], 0.5, Math.PI * 0.16, 0.13, 0.2, 0.3, 0)); }
    for (let i = 0; i < 12; i++) { const a = (i / 12) * Math.PI * 2; if (Math.cos(a) > 0.5) continue; L.push(clumpAt([Math.sin(a) * 0.6, 0.3, Math.cos(a) * 0.6], a, Math.PI * 0.28, 0.13, 0.2, 0, 0)); }
    return L;
  },
  // Grandpa: bald crown (the skin head shows) + puffy tufts above the ears and a band round the back (CG Hank)
  grandpa(r) {
    const L = [];
    for (let i = 0; i < 15; i++) { // horseshoe band from ear to ear round the back, at ear height
      const a = Math.PI * 0.42 + (i / 14) * Math.PI * 1.16; const x = Math.sin(a) * 0.6, z = Math.cos(a) * 0.6;
      L.push(clumpAt([x * 1.0, 0.16 + r() * 0.06, z * 1.0], a, Math.PI * (0.4 + r() * 0.15), 0.16 + r() * 0.03, 0.18 + r() * 0.1, (r() - 0.5) * 0.3, 0));
    }
    for (const s of [-1, 1]) for (let k = 0; k < 4; k++) { // the puffy side tufts
      const a = s * (Math.PI * 0.5 + 0.08 * k); L.push(clumpAt([Math.sin(a) * 0.62, 0.2 + k * 0.05, Math.cos(a) * 0.62 - 0.05 * k], a, Math.PI * (0.38 + 0.08 * k), 0.17, 0.26 + r() * 0.08, s * 0.25, -0.1));
    }
    for (let i = 0; i < 3; i++) L.push(clumpAt([(r() - 0.5) * 0.3, 0.6, -0.1 + r() * 0.2], r() * 6, Math.PI * 0.5, 0.05, 0.22, 0.2, 0)); // a few wisps on top
    return L;
  },
  // Grandma: waved cap + a round bun at the top-back + soft side waves over the ears
  bun(r) {
    const L = [place(capGeo(0.675, 0.56, 1, 44), [0, 0.1, -0.03], [-0.12, 0, 0], [1.02, 0.86, 1.05])];
    for (let i = 0; i < 8; i++) { const a = -Math.PI * 0.42 + (i / 7) * Math.PI * 0.84; L.push(clumpAt([Math.sin(a) * 0.52, 0.5, Math.cos(a) * 0.52], a + Math.PI, Math.PI * 0.42, 0.14, 0.28, 0.15 * Math.sign(a), 0)); } // waves swept back from the face
    for (const s of [-1, 1]) for (let k = 0; k < 3; k++) L.push(clumpAt([s * 0.64, 0.12 - k * 0.1, 0.12 - k * 0.14], s * Math.PI * 0.5, Math.PI * 0.15, 0.15, 0.16, 0, 0)); // side waves over the ears
    const bun = new THREE.SphereGeometry(0.34, 32, 20); L.push(place(bun, [0, 0.66, -0.36], [0.4, 0, 0], [1, 0.82, 1]));
    const wrap = new THREE.TorusGeometry(0.3, 0.07, 10, 36); L.push(place(wrap, [0, 0.6, -0.33], [Math.PI / 2 + 0.4, 0, 0], [1, 1, 1]));
    for (let i = 0; i < 6; i++) { const a = (i / 6) * Math.PI * 2; L.push(clumpAt([Math.sin(a) * 0.22, 0.86, -0.36 + Math.cos(a) * 0.2], a, Math.PI * 0.3, 0.1, 0.14, 0.2, 0)); }
    return L;
  },
  bob(r) {
    const L = [place(capGeo(0.68, 0.55, 1, 44), [0, 0.1, -0.02], [-0.1, 0, 0], [1.03, 0.85, 1.05])];
    for (let i = 0; i < 16; i++) { const a = (i / 16) * Math.PI * 2; if (Math.cos(a) > 0.62) continue; L.push(clumpAt([Math.sin(a) * 0.64, 0.3, Math.cos(a) * 0.64], a, Math.PI * 0.08, 0.2, 0.4 + r() * 0.06, 0, 0.08)); }
    for (let i = 0; i < 5; i++) L.push(clumpAt([-0.36 + i * 0.18, 0.52, 0.42], 0.3, Math.PI * 0.2, 0.15, 0.28, 0.2, 0));
    return L;
  },
};
export const HAIR_STYLES = Object.keys(HAIRS);
export const hairGeo = (style, seed = 1) => cached(keyOf('hairGeo', style, seed), () => merge(HAIRS[style](makeRng(hash32('hair', style, seed)))));

// ---------------- glasses ----------------
export function glassesGroup({ style = 'round', color = '#c9a24e', lens = true, y = 0.04, x = 0.17, r = 0.155, z = 0.67 } = {}) {
  const G = new THREE.Group(); G.name = 'glasses';
  const thick = style === 'thick', tube = thick ? 0.04 : 0.022;
  const m = thick ? plainMat(color, 0.35) : metalMat(color);
  const rimG = cached(keyOf('rim', r, tube), () => new THREE.TorusGeometry(r, tube, 10, 48));
  for (const s of [-1, 1]) {
    mesh(rimG, m, { pos: [s * x, y, z], rot: [0, s * 0.16, 0], parent: G, cast: false });
    if (lens) { const lm = cached('lensMat', () => new THREE.MeshPhysicalMaterial({ color: '#e8f0ff', roughness: 0.05, transparent: true, opacity: 0.16, clearcoat: 1, depthWrite: false }));
      mesh(cached(keyOf('lens', r), () => new THREE.CircleGeometry(r, 40)), lm, { pos: [s * x, y, z - 0.005], rot: [0, s * 0.16, 0], parent: G, cast: false, order: 2 }); }
    // temple arm running back to the ear
    const armG = cached(keyOf('temple', tube), () => new THREE.BoxGeometry(tube * 1.2, tube * 1.2, 0.72));
    mesh(armG, m, { pos: [s * (x + r + 0.04), y + 0.02, z - 0.38], rot: [0, s * 0.12, 0], parent: G, cast: false });
  }
  mesh(cached(keyOf('bridge', tube), () => new THREE.TorusGeometry(0.035, tube * 0.8, 8, 16, Math.PI)), m, { pos: [0, y + 0.02, z + 0.01], parent: G, cast: false });
  return G;
}

// ---------------- hats ----------------
function lathe(pts, seg = 48) { const g = new THREE.LatheGeometry(pts.map(([r, y]) => new THREE.Vector2(r, y)), seg); g.computeVertexNormals(); return g; }
export function hatGroup({ style = 'fishing', color = '#6f7342', band = null, lures = true, seed = 3 } = {}) {
  const G = new THREE.Group(); G.name = 'hat';
  const fabric = plainMat(color, 0.78), bandM = plainMat(band || shade(color, 0.62), 0.7);
  if (style === 'fishing') {
    const crown = cached('fishCrown', () => lathe([[0, 0.5], [0.3, 0.5], [0.5, 0.47], [0.6, 0.38], [0.66, 0.1], [0.69, 0.0], [0.68, -0.02], [0.66, -0.02]]));
    const brim = cached('fishBrim', () => lathe([[0.64, 0.0], [0.8, -0.06], [0.98, -0.16], [1.0, -0.18], [0.99, -0.2], [0.8, -0.09], [0.64, -0.03]]));
    mesh(crown, fabric, { parent: G }); mesh(brim, fabric, { parent: G });
    mesh(cached('fishBand', () => new THREE.CylinderGeometry(0.665, 0.69, 0.12, 48, 1, true)), bandM, { pos: [0, 0.07, 0], parent: G });
    // stitching rings on the brim
    const st = plainMat(shade(color, 0.75), 0.8); for (const rr of [0.78, 0.9]) mesh(cached(keyOf('stitch', rr), () => new THREE.TorusGeometry(rr, 0.008, 6, 64)), st, { pos: [0, -0.06 - (rr - 0.78) * 0.85, 0], rot: [Math.PI / 2, 0, 0], parent: G, cast: false });
    if (lures) { // our own lures: two spoons, a feather fly, a hook
      const r = makeRng(seed);
      const spoonG = cached('spoon', () => new THREE.SphereGeometry(0.07, 16, 10));
      const spoon = (a, c1) => { const x = Math.sin(a) * 0.69, z = Math.cos(a) * 0.69; const s = mesh(spoonG, cached(keyOf('lureM', c1), () => new THREE.MeshStandardMaterial({ color: c1, roughness: 0.25, metalness: 0.6 })), { pos: [x, 0.07, z], rot: [0, a, 0.5], scale: [0.5, 1.25, 0.25], parent: G, cast: false });
        mesh(cached('lureDot', () => new THREE.SphereGeometry(0.022, 10, 8)), plainMat('#d8261e', 0.3), { pos: [x * 1.04, 0.05, z * 1.04], parent: G, cast: false }); return s; };
      spoon(0.6, '#d9b24a'); spoon(-0.9, '#e8e8f0');
      const fx = Math.sin(0.1) * 0.7, fz = Math.cos(0.1) * 0.7; // feather fly
      mesh(cached('fly', () => new THREE.ConeGeometry(0.045, 0.24, 10)), plainMat('#3f9ad8', 0.6), { pos: [fx, 0.14, fz], rot: [0.3, 0, -0.9], parent: G, cast: false });
      mesh(cached('fly2', () => new THREE.ConeGeometry(0.035, 0.2, 10)), plainMat('#f2c84a', 0.6), { pos: [fx + 0.05, 0.12, fz], rot: [0.3, 0, -0.5], parent: G, cast: false });
      mesh(cached('hook', () => new THREE.TorusGeometry(0.05, 0.008, 6, 16, Math.PI * 1.4)), metalMat('#c8c8d0'), { pos: [Math.sin(-0.3) * 0.7, 0.0, Math.cos(-0.3) * 0.7], rot: [0, -0.3, 1.2], parent: G, cast: false });
    }
    G.position.set(0, 0.42, -0.02); G.rotation.x = -0.08;
  } else if (style === 'flatCap') {
    mesh(cached('capTop', () => new THREE.SphereGeometry(0.7, 40, 20, 0, Math.PI * 2, 0, Math.PI * 0.5)), fabric, { scale: [1, 0.32, 1.08], pos: [0, 0, -0.03], parent: G });
    mesh(cached('capVisor', () => new THREE.CylinderGeometry(0.52, 0.52, 0.04, 32, 1, false, -Math.PI * 0.5, Math.PI)), fabric, { pos: [0, -0.02, 0.38], scale: [1.05, 1, 0.75], parent: G });
    mesh(cached('capBtn', () => new THREE.SphereGeometry(0.05, 12, 8)), fabric, { pos: [0, 0.22, 0.05], parent: G });
    G.position.set(0, 0.5, 0.02); G.rotation.x = 0.1;
  } else if (style === 'beanie') {
    mesh(cached('beanieDome', () => new THREE.SphereGeometry(0.68, 40, 24, 0, Math.PI * 2, 0, Math.PI * 0.55)), fabric, { scale: [1, 0.9, 1], parent: G });
    mesh(cached('beanieCuff', () => new THREE.TorusGeometry(0.66, 0.1, 12, 48)), bandM, { rot: [Math.PI / 2, 0, 0], pos: [0, -0.05, 0], parent: G });
    mesh(cached('pompom', () => new THREE.IcosahedronGeometry(0.16, 2)), bandM, { pos: [0, 0.66, 0], parent: G });
    G.position.set(0, 0.32, 0);
  }
  return G;
}

// ---------------- moustache (3D walrus) ----------------
export const moustacheGeo = (seed = 2) => cached(keyOf('moustacheGeo', seed), () => {
  const r = makeRng(seed), L = [];
  for (const s of [-1, 1]) for (let k = 0; k < 4; k++) L.push(clumpAt([s * (0.05 + k * 0.1), -0.09 - k * 0.012, 0.64 - k * 0.035], s * (0.5 + k * 0.25), Math.PI * (0.2 + k * 0.05), 0.11 - k * 0.008, 0.18 + k * 0.04, s * 0.2, 0.1));
  return merge(L);
});

// ---------------- hood (bunched behind the neck) ----------------
export const hoodGeo = () => cached('hoodGeo', () => {
  const t = new THREE.TorusGeometry(0.6, 0.24, 14, 36, Math.PI * 1.3); const a = place(t, [0, 2.05, -0.12], [Math.PI / 2, 0, Math.PI * 0.85], [1.05, 0.85, 1]);
  const b = place(new THREE.SphereGeometry(0.6, 28, 18), [0, 2.2, -0.52], [0, 0, 0], [1.15, 0.62, 0.45]);
  return merge([a, b]);
});

// ---------------- dispatcher ----------------
export function addAccessory(head, spec, ctx = {}) {
  const type = spec.type || 'hair';
  if (type === 'hair') { const m = mesh(hairGeo(spec.style || 'short', spec.seed || 1), hairMat(spec.color || '#5a3418', spec.rough ?? 0.46), { parent: head, name: 'hair' }); return m; }
  if (type === 'glasses') { const g = glassesGroup(spec); head.add(g); return g; }
  if (type === 'hat') { const g = hatGroup(spec); head.add(g); return g; }
  if (type === 'moustache') { return mesh(moustacheGeo(spec.seed || 2), hairMat(spec.color || '#eeeaf0', 0.5), { parent: head, name: 'moustache' }); }
  if (type === 'hood') { const parent = ctx.hips || head; return mesh(hoodGeo(), cached(keyOf('hoodMat', spec.color), () => new THREE.MeshStandardMaterial({ color: spec.color || '#d9a52c', roughness: 0.7 })), { parent, name: 'hood' }); }
  throw new Error('unknown accessory ' + type);
}
