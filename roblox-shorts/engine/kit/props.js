// Suburb props, built in STUDS, origin on the ground at the prop's footprint centre, front = +Z.
// Two ways to use every prop:
//   addMailbox(P, opts)          -> merges into a Parts batch P (kitlib.Parts) at P's current transform (cheapest:
//                                   a whole lot of props becomes one mesh per material)
//   mailbox(opts)                -> a standalone THREE.Group in studs (wrap in a group scaled by STUD, or use kit.place()).
// Emissive parts that must switch on/off on a beat (lamp glass, lanterns, gate leaves) are returned as separate objects.
// VISUAL_BIBLE §4.1-4.3: studless Roblox parts, every surface textured, detailed props, black Victorian lamps, white
// picket fences and gates, black mailboxes, tulip flowerbeds, round flower bushes, stepping stones, pines.
import { THREE, Parts, M, texMat, signTex, plaqueTex, boxUV, planarUV, scaleUV, trs, makeRng, hash32, persistTree, range, pick, shade, STUD } from './kitlib.js';
import { noise3 } from '../core/random.js';

const PI = Math.PI;
const group = (P, name, o) => persistTree(P.build(M, { name, ...o }));

// ------------------------------------------------------------------ street lamp (black Victorian)
// height 13-14 (VISUAL_BIBLE §2.7). heads: 1 (PN) or 2 (TF double). Returns { lightPos: [x,y,z] studs (local), glass: [...] }.
// The glass is NOT merged (it is a separate Mesh per head, emissive #ffd9a0 x4) so lamps can switch off one by one.
export function addStreetLamp(P, { height = 13.5, heads = 1, glassKey = 'emissive:#ffd9a0:4' } = {}) {
  const H = height, k = 'black:#141418';
  const base = new THREE.LatheGeometry([[0, 0], [0.8, 0], [0.8, 0.3], [0.62, 0.45], [0.55, 1.4], [0.42, 1.75], [0.3, 2.0], [0.3, 2.3], [0, 2.3]].map(([x, y]) => new THREE.Vector2(x, y)), 12);
  P.add(k, base);
  P.cyl(k, 0.19, 0.24, H - 4.4, 10, [0, 2.3 + (H - 4.4) / 2, 0]);
  for (const y of [2.35, 3.2, H - 2.4]) P.cyl(k, 0.33, 0.33, 0.18, 12, [0, y, 0]);
  const heads_ = [];
  if (heads === 1) {
    P.box(k, 2.6, 0.13, 0.13, [0, H - 3.3, 0]); for (const s of [-1, 1]) P.add(k, new THREE.SphereGeometry(0.16, 8, 6), [s * 1.3, H - 3.3, 0]);
    heads_.push([0, H - 1.35, 0]);
  } else {
    P.box(k, 4.2, 0.18, 0.18, [0, H - 2.55, 0]); for (const s of [-1, 1]) { P.cyl(k, 0.07, 0.07, 1.0, 6, [s * 1.6, H - 3.0, 0], [0, 0, s * 0.6]); heads_.push([s * 2.1, H - 1.7, 0]); }
    P.add(k, new THREE.SphereGeometry(0.28, 10, 8), [0, H - 2.2, 0]);
  }
  const glass = [];
  for (const [x, y, z] of heads_) {
    P.cyl(k, 0.55, 0.42, 0.18, 4, [x, y - 0.8, z], [0, PI / 4, 0]);
    for (let i = 0; i < 4; i++) { const a = (i / 4) * PI * 2; P.box(k, 0.09, 1.45, 0.09, [x + Math.cos(a) * 0.5, y, z + Math.sin(a) * 0.5], [0, -a, 0]); }
    P.add(k, new THREE.ConeGeometry(0.9, 0.7, 4), [x, y + 1.05, z], [0, PI / 4, 0]);
    P.add(k, new THREE.SphereGeometry(0.15, 8, 6), [x, y + 1.5, z]);
    const g = new THREE.Mesh(new THREE.CylinderGeometry(0.6, 0.42, 1.35, 4), M(glassKey)); g.rotation.y = PI / 4;
    g.position.set(x, y, z).applyMatrix4(P.top); g.name = 'lampGlass'; glass.push(g);
  }
  return { lightPos: heads_[0], heads: heads_, glass };
}
export function streetLamp(o = {}) { const P = new Parts(); const r = addStreetLamp(P, o); const g = group(P, 'streetLamp'); r.glass.forEach((m) => g.add(m)); g.userData.lightPos = r.lightPos; g.userData.heads = r.heads; return g; }

// ------------------------------------------------------------------ mailbox (black, rounded top, red flag)
export function addMailbox(P, { color = '#17171c', post = '#5a3a22', flagUp = false } = {}) {
  P.box('wood:' + post, 0.4, 3.4, 0.4, [0, 1.7, 0]);
  P.box('wood:' + post, 0.5, 0.15, 1.2, [0, 3.35, 0]);
  P.box('black:' + color, 0.95, 0.55, 1.9, [0, 3.7, 0], null, { bevel: 0.04 });
  const top = new THREE.CylinderGeometry(0.475, 0.475, 1.9, 14, 1, false, 0, PI); P.add('black:' + color, top, [0, 3.97, 0], [PI / 2, PI / 2, 0]);
  P.box('black:' + shade(color, 0.7), 0.9, 0.95, 0.06, [0, 3.95, 0.96]);
  P.box('plastic:#c8282a', 0.06, 0.18, 0.9, [0.52, flagUp ? 4.5 : 3.9, -0.35], [flagUp ? 0 : PI / 2, 0, 0]);
  P.box('plastic:#c8282a', 0.06, 0.4, 0.3, [0.52, flagUp ? 4.85 : 3.9, flagUp ? -0.35 : 0.2]);
}
export function mailbox(o) { const P = new Parts(); addMailbox(P, o); return group(P, 'mailbox'); }

// ------------------------------------------------------------------ picket fence + gate
// Runs along X from -length/2..+length/2 at z = 0, pickets facing +Z. gate: { at: x, width: 4 } leaves a gap with
// posts; the gate leaf is returned separately (hinge on the -X post, opening toward -Z), so it can swing/latch.
export function addPicketFence(P, { length = 32, height = 3.5, spacing = 0.72, gate = null, color = '#efeee9', postEvery = 8 } = {}) {
  const k = 'trim:' + color, x0 = -length / 2, x1 = length / 2; const gx = gate ? gate.at : 1e9, gw = gate ? gate.width ?? 4 : 0;
  const picket = (x) => { P.box(k, 0.46, height - 0.3, 0.12, [x, (height - 0.3) / 2, 0]); P.add(k, new THREE.ConeGeometry(0.33, 0.42, 4), [x, height - 0.09, 0], [0, PI / 4, 0], [1, 1, 0.26]); };
  const segs = gate ? [[x0, gx - gw / 2 - 0.35], [gx + gw / 2 + 0.35, x1]] : [[x0, x1]];
  for (const [a, b] of segs) {
    if (b - a < 0.5) continue;
    for (const y of [0.9, height - 0.95]) P.box(k, b - a, 0.38, 0.2, [(a + b) / 2, y, -0.16]);
    const n = Math.max(1, Math.floor((b - a) / spacing)); for (let i = 0; i <= n; i++) picket(a + ((b - a) * i) / n);
    for (let x = a; x <= b + 0.01; x += Math.max(postEvery, (b - a) / Math.max(1, Math.round((b - a) / postEvery)))) { P.box(k, 0.6, height + 0.2, 0.6, [x, (height + 0.2) / 2, -0.2]); P.box(k, 0.8, 0.2, 0.8, [x, height + 0.3, -0.2]); }
  }
  let leaf = null;
  if (gate) {
    for (const s of [-1, 1]) { P.box(k, 0.75, height + 0.6, 0.75, [gx + s * (gw / 2 + 0.38), (height + 0.6) / 2, -0.15]); P.add(k, new THREE.SphereGeometry(0.42, 12, 8), [gx + s * (gw / 2 + 0.38), height + 0.95, -0.15]); }
    const G = new Parts(); const w = gw - 0.1;
    for (const y of [0.9, height - 0.95]) G.box(k, w, 0.36, 0.18, [w / 2, y, -0.14]);
    G.box(k, Math.hypot(w, height - 1.85) , 0.3, 0.16, [w / 2, height / 2, -0.15], [0, 0, Math.atan2(height - 1.85, w)]);
    const n = Math.round(w / spacing); for (let i = 0; i <= n; i++) { const x = 0.25 + ((w - 0.5) * i) / n; G.box(k, 0.44, height - 0.5, 0.12, [x, (height - 0.5) / 2 + 0.15, 0]); G.add(k, new THREE.ConeGeometry(0.31, 0.4, 4), [x, height - 0.15, 0], [0, PI / 4, 0], [1, 1, 0.26]); }
    G.box('black:#1d1d22', 0.25, 0.3, 0.25, [w - 0.3, height - 1.4, 0.12]); // latch
    leaf = persistTree(G.build(M, { name: 'gate' }));
    leaf.applyMatrix4(P.top.clone().multiply(trs([gx - gw / 2 + 0.05, 0, 0])));
    leaf.userData.hinge = true; // rotate leaf.rotation.y (about its hinge) to open: +0..1.9 rad
  }
  return { gate: leaf };
}
export function picketFence(o = {}) { const P = new Parts(); const r = addPicketFence(P, o); const g = group(P, 'picketFence'); if (r.gate) g.add(r.gate); g.userData.gate = r.gate ? r.gate.name : null; return g; }

// ------------------------------------------------------------------ flowers
// Tulip: lathe cup on a stem with two leaves. ~1.3 studs tall. Merged per colour into P.
const _tulipCup = (() => { let g = null; return () => g || (g = new THREE.LatheGeometry([[0, 0], [0.13, 0.03], [0.19, 0.14], [0.18, 0.3], [0.11, 0.42], [0.06, 0.38]].map(([x, y]) => new THREE.Vector2(x, y)), 7)); })();
const _fixedRng = makeRng(7);
export function addTulip(P, x, z, { color = '#d8283a', h = 1.05, lean = [0, 0], r = _fixedRng } = {}) {
  P.cyl('stem', 0.035, 0.045, h, 5, [x + lean[0] * h * 0.5, h / 2, z + lean[1] * h * 0.5], [lean[1], 0, -lean[0]]);
  P.add('tulip:' + color, _tulipCup().clone(), [x + lean[0] * h, h - 0.05, z + lean[1] * h], [0, r() * PI, 0], [1.05, 1.05, 1.05]);
  for (const s of [-1, 1]) P.add('stem:#356d2c', new THREE.SphereGeometry(1, 6, 4), [x + s * 0.1, 0.25, z], [0, r() * PI, s * 0.35], [0.09, 0.32, 0.03]);
}
// Daisy / small lawn flower (white petals, yellow centre): 0.35 tall, cheap.
export function addDaisy(P, x, z, { color = '#f4f0ea', centre = '#f2c230', r = _fixedRng } = {}) {
  P.cyl('stem', 0.02, 0.025, 0.32, 4, [x, 0.16, z]);
  P.add('tulip:' + color, new THREE.CylinderGeometry(0.13, 0.13, 0.025, 8), [x, 0.33, z], [r() * 0.4, r() * PI, 0]);
  P.add('tulip:' + centre, new THREE.SphereGeometry(0.05, 6, 4), [x, 0.35, z]);
}
// Flowerbed: raised soil strip (dirt texture) with stone or brick edging and rows of tulips (and an optional bush).
// Bed is `length` along X, `depth` along Z, centred at origin. Returns nothing (all merged).
// gaps: [[x, z, r], ...] bed-local circles left free of tulips (a gnome's spot).
export function addFlowerbed(P, { length = 12, depth = 3, colors = ['#d8283a', '#f07ab0', '#f2c230', '#f4eee8'], density = 2.2, edging = 'stone', seed = 1, bushes = 0, bushColor = '#2f6a2c', blossom = '#e070c0', gaps = [] } = {}) {
  const r = makeRng(hash32('bed', seed));
  P.box('dirt', length, 0.35, depth, [0, 0.175, 0]);
  if (edging === 'stone') { const n = Math.round(length / 1.1); for (const z of [depth / 2 + 0.15]) for (let i = 0; i < n; i++) P.box('stone:#9b9389', 1.0, 0.45, 0.4, [-length / 2 + (i + 0.5) * (length / n), 0.22, z], [0, (r() - 0.5) * 0.08, 0], { bevel: 0.08 }); for (const s of [-1, 1]) P.box('stone:#9b9389', 0.4, 0.45, depth, [s * (length / 2 + 0.2), 0.22, 0], null, { bevel: 0.08 }); }
  else if (edging === 'brick') { P.box('brick:#8a3a2c', length + 0.6, 0.5, 0.35, [0, 0.25, depth / 2 + 0.17]); }
  const n = Math.round(length * depth * density / 3); const cols = Math.max(1, Math.round(length / 0.8)); const rows = Math.max(1, Math.round(n / cols));
  for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) {
    const x = -length / 2 + 0.5 + ((length - 1) * (i + 0.5 * (j % 2))) / cols + (r() - 0.5) * 0.25; const z = -depth / 2 + 0.5 + ((depth - 1) * (j + 0.5)) / rows + (r() - 0.5) * 0.25;
    if (x > length / 2 - 0.3 || gaps.some(([gx, gz, gr]) => (x - gx) ** 2 + (z - gz) ** 2 < gr * gr)) continue;
    P.push(trs([0, 0.35, 0])); addTulip(P, x, z, { color: pick(r, colors), h: 0.55 + r() * 0.3, lean: [(r() - 0.5) * 0.12, (r() - 0.5) * 0.12], r }); P.pop();
  }
  for (let b = 0; b < bushes; b++) { const x = bushes === 1 ? length / 2 - 1.8 : -length / 2 + 1.4 + ((length - 2.8) * b) / (bushes - 1); P.push(trs([x, 0.3, -depth * 0.1])); addBush(P, { radius: 1.2 + r() * 0.3, color: bushColor, blossom, seed: seed * 7 + b }); P.pop(); }
}

// ------------------------------------------------------------------ vegetation
// Round bush: noise-displaced sphere with foliage texture, optional blossom dots (TF round flower bushes).
export function addBush(P, { radius = 1.5, color = '#2f6a2c', blossom = null, blossoms = 16, seed = 1, squash = 0.85 } = {}) {
  const r = makeRng(hash32('bush', seed)); const g = new THREE.SphereGeometry(1, 18, 12); const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i), z = p.getZ(i); const n = noise3(x * 1.7 + seed, y * 1.7, z * 1.7, seed) * 0.22 + noise3(x * 4, y * 4, z * 4, seed + 5) * 0.06; const s = 1 + n; p.setXYZ(i, x * s, Math.max(-0.35, y) * s, z * s); }
  g.computeVertexNormals(); scaleUV(g, (2 * PI * radius) / 3, (PI * radius) / 3);
  P.add('bush:' + color, g, [0, radius * squash * 0.65, 0], null, [radius, radius * squash, radius]);
  if (blossom) for (let i = 0; i < blossoms; i++) {
    const th = r() * PI * 2, ph = 0.25 + r() * 0.9; const v = [Math.cos(th) * Math.sin(ph + 0.5), Math.cos(ph + 0.5), Math.sin(th) * Math.sin(ph + 0.5)];
    P.add('tulip:' + blossom, new THREE.SphereGeometry(0.14 + r() * 0.06, 6, 4), [v[0] * radius * 1.02, radius * squash * 0.65 + v[1] * radius * squash, v[2] * radius * 1.02]);
  }
}
export function bush(o) { const P = new Parts(); addBush(P, o); return group(P, 'bush'); }

// Pine: stacked noisy cones (VISUAL_BIBLE §4.3: 18-30 studs). Keep one tree style per shot.
export function addPine(P, { height = 24, seed = 1, color = '#244a35', tiers = 6 } = {}) {
  const r = makeRng(hash32('pine', seed)); const H = height;
  P.cyl('bark', 0.35 * H / 24, 0.6 * H / 24, H * 0.3, 7, [0, H * 0.15, 0]);
  for (let k = 0; k < tiers; k++) {
    const u = k / (tiers - 1); const rad = (0.28 - 0.2 * u) * H * (0.9 + r() * 0.2), h = H * (0.3 - 0.08 * u), y = H * (0.18 + 0.66 * u);
    const g = new THREE.ConeGeometry(1, 1, 11, 3); const p = g.attributes.position;
    for (let i = 0; i < p.count; i++) { const x = p.getX(i), yy = p.getY(i), z = p.getZ(i); const rr = Math.hypot(x, z); const n = noise3(x * 2.3 + k, yy * 2, z * 2.3, seed + k) * 0.28; const droop = yy < -0.45 ? -0.12 * rr : 0; p.setXYZ(i, x * (1 + n), yy + droop + n * 0.1, z * (1 + n)); }
    g.computeVertexNormals(); scaleUV(g, (2 * PI * rad) / 3, Math.hypot(rad, h) / 3);
    P.add('pine:' + color, g, [0, y + h / 2, 0], [0, r() * PI, 0], [rad, h, rad]);
  }
}
export function pine(o) { const P = new Parts(); addPine(P, o); return group(P, 'pine'); }
// Leafy (blob) tree: trunk + clustered displaced spheres.
export function addLeafyTree(P, { height = 20, seed = 1, color = '#2f5e2a' } = {}) {
  const r = makeRng(hash32('leafy', seed)); const H = height;
  P.cyl('bark', 0.45 * H / 20, 0.75 * H / 20, H * 0.5, 8, [0, H * 0.25, 0]);
  for (let i = 0; i < 6; i++) { const a = (i / 6) * PI * 2 + r(), d = i === 0 ? 0 : H * 0.18; P.push(trs([Math.cos(a) * d, H * (0.48 + 0.12 * r()) - H * 0.12, Math.sin(a) * d])); addBush(P, { radius: H * (0.2 + 0.06 * r()), color, seed: seed * 13 + i, squash: 0.9 }); P.pop(); }
}

// Grass blades for close-ups: one InstancedMesh of tapered, bent blades with per-instance colour (studs).
// area [w, d] centred at origin; avoid: [[x, z, r], ...] circles kept clear (paths, flowerbeds, the gnome's feet).
export function grassBlades({ area = [16, 12], count = 6000, height = [0.18, 0.42], color = '#4f8a44', dark = '#3b6e33', light = '#76a860', seed = 1, avoid = [], feather = 0.7 } = {}) {
  const key = 'blades' + JSON.stringify(arguments[0] || {}); if (_bladeCache.has(key)) return _bladeCache.get(key).clone();
  const g = new THREE.BufferGeometry();
  // 2-segment blade: base width 0.08, tip at y = 1, bent forward along +z by the instance rotation
  // both windings (FrontSide): a DoubleSide material would flip the normal on back faces and render them black
  const P = [-0.032, 0, 0, 0.032, 0, 0, -0.02, 0.5, 0.06, 0.02, 0.5, 0.06, 0, 1, 0.2];
  g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3)); g.setIndex([0, 1, 2, 1, 3, 2, 2, 3, 4, 0, 2, 1, 1, 2, 3, 2, 4, 3]);
  g.setAttribute('color', new THREE.Float32BufferAttribute([0.78, 0.78, 0.78, 0.78, 0.78, 0.78, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 1.12, 1.12, 1.12], 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(Array.from({ length: 5 }, () => [0, 0.97, 0.24]).flat(), 3)); // up-facing: blades shade like the lawn
  const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.9 });
  const im = new THREE.InstancedMesh(g, mat, count); im.name = 'grassBlades';
  const r = makeRng(hash32('blades', seed)); const m = new THREE.Matrix4(); const c = new THREE.Color(); const C = [new THREE.Color(dark), new THREE.Color(color), new THREE.Color(light)];
  let k = 0, tries = 0;
  while (k < count && tries < count * 4) {
    tries++; const x = (r() - 0.5) * area[0], z = (r() - 0.5) * area[1];
    if (avoid.some(([ax, az, ar]) => (x - ax) ** 2 + (z - az) ** 2 < ar * ar)) continue;
    // feathered squircle patch: density and blade height fall off toward the edge (no visible patch border)
    const e = Math.pow(Math.pow(Math.abs((2 * x) / area[0]), 4) + Math.pow(Math.abs((2 * z) / area[1]), 4), 0.25); const keep = 1 - Math.min(1, Math.max(0, (e - feather) / (1 - feather))); if (r() > keep * keep) continue;
    const h = (height[0] + (height[1] - height[0]) * r() * r()) * (0.45 + 0.55 * keep); const w = 0.8 + r() * 0.8;
    m.compose(new THREE.Vector3(x, 0, z), new THREE.Quaternion().setFromEuler(new THREE.Euler((r() - 0.5) * 0.5, r() * PI * 2, (r() - 0.5) * 0.4, 'YXZ')), new THREE.Vector3(w, h, w));
    im.setMatrixAt(k, m); const t = r(); c.copy(t < 0.5 ? C[0] : C[1]).lerp(t < 0.5 ? C[1] : C[2], t < 0.5 ? t * 2 : (t - 0.5) * 2); im.setColorAt(k, c); k++;
  }
  im.count = k; im.instanceMatrix.needsUpdate = true; if (im.instanceColor) im.instanceColor.needsUpdate = true; im.computeBoundingSphere(); im.receiveShadow = true;
  persistTree(im); _bladeCache.set(key, im); return im.clone();
}
const _bladeCache = new Map();

// ------------------------------------------------------------------ path, steps, garden bits
// Stepping stones along a polyline [[x,z], ...] (irregular flat flagstones, ~1.6 studs, every `step`).
export function addSteppingStones(P, pts, { size = 1.6, step = 2.2, seed = 1 } = {}) {
  const r = makeRng(hash32('stones', seed)); let carry = 0.6;
  for (let i = 0; i < pts.length - 1; i++) {
    const [ax, az] = pts[i], [bx, bz] = pts[i + 1]; const L = Math.hypot(bx - ax, bz - az);
    for (let d = carry; d < L; d += step) {
      const u = d / L, x = ax + (bx - ax) * u + (r() - 0.5) * 0.3, z = az + (bz - az) * u + (r() - 0.5) * 0.3; const rad = size / 2 * (0.85 + r() * 0.3);
      const g = new THREE.CylinderGeometry(1, 1.04, 1, 9); const p = g.attributes.position; const jit = Array.from({ length: 10 }, () => 0.82 + r() * 0.3);
      for (let k = 0; k < p.count; k++) { const a = Math.atan2(p.getZ(k), p.getX(k)); const rr = Math.hypot(p.getX(k), p.getZ(k)); if (rr > 0.01) { const j = jit[Math.round(((a + PI) / (2 * PI)) * 9) % 9]; p.setX(k, p.getX(k) * j); p.setZ(k, p.getZ(k) * j * 0.85); } }
      g.computeVertexNormals(); g.scale(rad, 0.16, rad); g.rotateY(r() * PI); g.translate(x, 0.02, z); planarUV(g, 3); P.add('flag:#8f8981', g);
      carry = d + step - L;
    }
  }
}
// Worn dirt patch on a lawn: flat decal (dirt texture, soft noisy alpha edge). size in studs.
export function addDirtPatch(P, x, z, { size = 3, seed = 1, rot = 0 } = {}) { P.add('dirtPatch', planarUV(new THREE.PlaneGeometry(size, size * 0.7).rotateX(-PI / 2), 4), [x, 0.015 + (seed % 7) * 0.002, z], [0, rot, 0]); }
// Wall lantern (porch light): black box lantern on a bracket; glass emissive (separate Mesh, returned).
export function addWallLantern(P, { glassKey = 'emissive:#ffc98a:3' } = {}) {
  const k = 'black:#16161a';
  P.box(k, 0.6, 1.2, 0.12, [0, 0, 0.06]); P.box(k, 0.14, 0.14, 0.7, [0, 0.1, 0.4]);
  P.box(k, 0.75, 0.1, 0.75, [0, -0.45, 0.85]); P.add(k, new THREE.ConeGeometry(0.62, 0.45, 4), [0, 0.62, 0.85], [0, PI / 4, 0]); P.add(k, new THREE.SphereGeometry(0.1, 6, 4), [0, 0.9, 0.85]);
  for (const [x, z] of [[-0.32, 0.53], [0.32, 0.53], [-0.32, 1.17], [0.32, 1.17]]) P.box(k, 0.07, 0.95, 0.07, [x, 0.02, z]);
  const glass = new THREE.Mesh(new THREE.BoxGeometry(0.58, 0.85, 0.58), M(glassKey)); glass.position.set(0, 0.02, 0.85).applyMatrix4(P.top); glass.name = 'lanternGlass';
  return { glass, lightPos: new THREE.Vector3(0, 0.02, 1.1).applyMatrix4(P.top).toArray() };
}
// Rocking chair (PN porch): wood, spindle back, curved rockers. Faces +Z.
export function addRockingChair(P, { color = '#7a4a28' } = {}) {
  const k = 'wood:' + color;
  P.box(k, 2.0, 0.2, 1.9, [0, 1.6, 0]);
  for (const s of [-1, 1]) { P.box(k, 0.2, 4.2, 0.2, [s * 0.95, 2.6, -0.95], [-0.12, 0, 0]); P.box(k, 0.18, 1.5, 0.18, [s * 0.95, 0.85 + 0.75, 0.85]); P.box(k, 0.22, 0.14, 2.0, [s * 0.95, 2.55, 0.0]); }
  for (let i = 0; i < 5; i++) P.box(k, 0.12, 2.4, 0.1, [-0.6 + i * 0.3, 2.95, -1.05], [-0.12, 0, 0]);
  P.box(k, 2.1, 0.3, 0.2, [0, 4.55, -1.2], [-0.12, 0, 0]);
  // rockers: arcs of short boxes in the y-z plane (centre of curvature above the chair)
  for (const s of [-1, 1]) { const R = 4.6, cy = R + 0.12, n = 6, a0 = -0.38, a1 = 0.38; for (let i = 0; i < n; i++) { const a = a0 + ((a1 - a0) * (i + 0.5)) / n; P.box(k, 0.2, 0.22, (2 * R * (a1 - a0)) / n / 2 + 0.05, [s * 0.95, cy - R * Math.cos(a), 0.1 + R * Math.sin(a)], [-a, 0, 0]); } }
}
// Striped deck chair (EP01 frame 1 / epilogue): folding wood frame + striped canvas sling. Faces +Z (sitter looks +Z).
// Seat low point ~1.1 studs, back top 3.7: an R6 avatar (5.2) or a 2-stud gnome both read sitting in it.
export function addDeckChair(P, { stripes = ['#ece4d4', '#3f74c8'], frame = '#a9733e', n = 7 } = {}) {
  const k = 'wood:' + frame, W = 1.15;
  for (const s of [-1, 1]) {
    P.bar(k, [s * W, 0, 1.6], [s * W, 3.7, -1.6], 0.2, 0.16);          // main side rails (front foot -> back top)
    P.bar(k, [s * (W - 0.22), 0, -2.0], [s * (W - 0.22), 1.75, 0.25], 0.18, 0.14); // rear legs
    P.bar(k, [s * W, 1.35, 0.95], [s * W, 1.25, 0.15], 0.16, 0.12);     // seat-front bracket
  }
  P.bar(k, [-W - 0.1, 0.25, 1.38], [W + 0.1, 0.25, 1.38], 0.16, 0.16); P.bar(k, [-W - 0.1, 3.62, -1.5], [W + 0.1, 3.62, -1.5], 0.18, 0.18);
  P.bar(k, [-W, 1.38, 0.95], [W, 1.38, 0.95], 0.16, 0.16); P.bar(k, [-W + 0.2, 0.15, -1.95], [W - 0.2, 0.15, -1.95], 0.14, 0.14);
  // sling: back panel (top bar -> sag point) and seat panel (sag point -> front bar), striped across X
  const top = [3.5, -1.42], sag = [1.05, 0.05], front = [1.32, 0.9]; const sw = (2 * W - 0.2) / n;
  for (let i = 0; i < n; i++) {
    const x = -W + 0.1 + (i + 0.5) * sw, key = 'plastic:' + stripes[i % stripes.length];
    P.bar(key, [x, top[0], top[1]], [x, sag[0], sag[1]], sw + 0.01, 0.06); P.bar(key, [x, sag[0], sag[1]], [x, front[0], front[1]], sw + 0.01, 0.06);
  }
}
// Hose reel with a green coiled hose.
export function addHoseReel(P, { color = '#2f8a3a' } = {}) {
  for (const s of [-1, 1]) P.box('metal:#4a4e55', 0.15, 1.6, 1.2, [s * 0.7, 0.8, 0]);
  P.cyl('metal:#4a4e55', 0.15, 0.15, 1.5, 8, [0, 1.0, 0], [0, 0, PI / 2]);
  for (let i = 0; i < 5; i++) { const g = new THREE.TorusGeometry(0.62 - i * 0.02, 0.11, 6, 18); g.rotateY(PI / 2); P.add('plastic:' + color, g, [-0.48 + i * 0.24, 1.0, 0]); }
}
// Dog kennel (next door's lawn): red plank walls, shingle gable roof, dark arched opening, name board.
export function addKennel(P, { color = '#b0482e', name = '' } = {}) {
  P.box('wood:' + color, 3.2, 2.6, 3.6, [0, 1.3, 0]);
  const roof = 1.4; for (const s of [-1, 1]) P.box('shingle:#3a3036', 2.25, 0.18, 4.1, [s * 0.95, 2.6 + roof / 2, 0], [0, 0, -s * Math.atan2(roof, 1.7)]);
  const gab = new THREE.BufferGeometry(); gab.setAttribute('position', new THREE.Float32BufferAttribute([-1.6, 0, 0, 1.6, 0, 0, 0, roof, 0], 3)); gab.setAttribute('uv', new THREE.Float32BufferAttribute([0, 0, 0.8, 0, 0.4, 0.35], 2)); gab.computeVertexNormals();
  P.add('wood:' + color, gab.clone(), [0, 2.6, 1.81]); P.add('wood:' + color, gab, [0, 2.6, -1.81], [0, PI, 0]);
  P.add('black:#07060a', new THREE.CircleGeometry(0.75, 16, 0, PI), [0, 1.0, 1.82]); P.box('black:#07060a', 1.5, 1.0, 0.02, [0, 0.5, 1.82]);
}
// Fire hydrant (red).
export function addHydrant(P, { color = '#c8282a' } = {}) {
  P.add('plastic:' + color, new THREE.LatheGeometry([[0, 0], [0.55, 0], [0.55, 0.2], [0.4, 0.3], [0.4, 1.6], [0.48, 1.7], [0.42, 1.85], [0.3, 2.1], [0.12, 2.25], [0, 2.3]].map(([x, y]) => new THREE.Vector2(x, y)), 12));
  for (const s of [-1, 1]) P.cyl('plastic:' + color, 0.16, 0.16, 0.45, 8, [s * 0.5, 1.15, 0], [0, 0, PI / 2]);
  P.cyl('plastic:' + shade(color, 0.8), 0.2, 0.2, 0.3, 8, [0, 1.1, 0.45], [PI / 2, 0, 0]);
}
// Wheelie bin.
export function addTrashBin(P, { color = '#2f5a3a' } = {}) {
  P.box('plastic:' + color, 1.9, 3.1, 1.9, [0, 1.75, 0], null, { bevel: 0.08 }); P.box('plastic:' + shade(color, 0.8), 2.1, 0.22, 2.2, [0, 3.38, -0.05], null, { bevel: 0.05 });
  for (const s of [-1, 1]) P.cyl('black', 0.3, 0.3, 0.2, 10, [s * 0.75, 0.3, -1.0], [0, 0, PI / 2]);
}
// Terracotta pot with a ball plant (porches).
export function addPotPlant(P, { color = '#b25a32', leaves = '#2f6a2c', blossom = null, seed = 1 } = {}) {
  P.add('plastic:' + color, new THREE.LatheGeometry([[0, 0], [0.55, 0], [0.75, 1.1], [0.85, 1.15], [0.85, 1.35], [0, 1.35]].map(([x, y]) => new THREE.Vector2(x, y)), 12));
  P.push(trs([0, 1.0, 0])); addBush(P, { radius: 0.85, color: leaves, blossom, blossoms: 8, seed }); P.pop();
}
// Dandelion (clock): stem + seed puff (white). puff=false gives the yellow flower. Burst the puff with fx.burst().
export function addDandelion(P, { height = 1.2, puff = true, seed = 1 } = {}) {
  const r = makeRng(hash32('dand', seed));
  P.cyl('stem:#4d8a3a', 0.03, 0.04, height, 5, [0, height / 2, 0]);
  if (!puff) { P.add('tulip:#f2c230', new THREE.SphereGeometry(0.22, 10, 6), [0, height, 0], null, [1, 0.5, 1]); return; }
  P.add('plastic:#d9d0b8', new THREE.SphereGeometry(0.08, 8, 6), [0, height, 0]);
  for (let i = 0; i < 46; i++) { const th = r() * PI * 2, ph = Math.acos(2 * r() - 1); const v = new THREE.Vector3(Math.sin(ph) * Math.cos(th), Math.cos(ph), Math.sin(ph) * Math.sin(th)); const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), v);
    const g = new THREE.CylinderGeometry(0.006, 0.006, 0.34, 3); g.translate(0, 0.17, 0); g.applyQuaternion(q); g.translate(0, height, 0); P.add('plastic:#efeae0', g);
    const t = new THREE.SphereGeometry(0.035, 5, 3); t.translate(v.x * 0.35, height + v.y * 0.35, v.z * 0.35); P.add('tulip:#f6f2ea', t); }
}

// ------------------------------------------------------------------ signs
// Estate-agent board: white post with an arm and a hanging board (our own text; VISUAL_BIBLE §4.1 sign style).
// Returns the board mesh (separate so a SOLD sticker can be added on the beat).
export function addAgentBoard(P, { lines = ['FOR SALE'], header = '', w = 4.2, h = 3.0 } = {}) {
  const k = 'trim:#f1efe9'; P.box(k, 0.35, 7.0, 0.35, [0, 3.5, 0]); P.box(k, w + 0.6, 0.3, 0.3, [w / 2 + 0.1, 6.7, 0]);
  for (const s of [0.4, w - 0.2]) P.box('black:#222', 0.06, 0.5, 0.06, [s, 6.35, 0]);
  const tex = signTex(lines, header, { w: 512, h: Math.round((512 * h) / w) }); const face = texMat('sign:' + header + '|' + lines.join('|'), tex), edge = M('trim:#f1efe9');
  const g = boxUV(w, h, 0.12, 1); fixBoxFaceUV(g); const board = new THREE.Mesh(g, [edge, edge, edge, edge, face, edge]); // back plain: seen from the house the text must not read mirrored
  board.position.set(w / 2 + 0.1, 6.1 - h / 2, 0).applyMatrix4(P.top); board.quaternion.setFromRotationMatrix(P.top); board.name = 'agentBoard';
  return board;
}
// Yard / town sign on two black posts (AW "TOWN LAW" style).
export function addPostSign(P, { lines = ['KEEP OFF', 'THE LAWN', 'AFTER DARK'], header = '', w = 5, h = 3.6, postH = 7 } = {}) {
  for (const s of [-1, 1]) P.box('black:#1a1a1e', 0.3, postH, 0.3, [s * (w / 2 - 0.5), postH / 2, -0.12]);
  const tex = signTex(lines, header, { w: 512, h: Math.round((512 * h) / w) });
  const g = boxUV(w, h, 0.15, 1); fixBoxFaceUV(g); const edge = M('trim:#f1efe9');
  const board = new THREE.Mesh(g, [edge, edge, edge, edge, texMat('sign:' + header + '|' + lines.join('|'), tex), edge]);
  board.position.set(0, postH - h / 2 - 0.2, 0).applyMatrix4(P.top); board.quaternion.setFromRotationMatrix(P.top); board.name = 'sign';
  return board;
}
// Box front/back faces with 0..1 UVs (for text boards).
function fixBoxFaceUV(g) { const uv = g.attributes.uv; for (const f of [4, 5]) { const o = f * 4; uv.setXY(o, f === 4 ? 0 : 1, 1); uv.setXY(o + 1, f === 4 ? 1 : 0, 1); uv.setXY(o + 2, f === 4 ? 0 : 1, 0); uv.setXY(o + 3, f === 4 ? 1 : 0, 0); } }
// House-number plaque mesh (front face textured).
export function plaque(text = '16', { w = 1.3, h = 1.0, bg = '#1d3a2c' } = {}) {
  const g = boxUV(w, h, 0.1, 1); fixBoxFaceUV(g);
  const m = new THREE.Mesh(g, [M('black:' + bg), M('black:' + bg), M('black:' + bg), M('black:' + bg), texMat('plaque:' + text + bg, plaqueTex(text, bg)), M('black:' + bg)]); m.name = 'plaque'; return m;
}

// ------------------------------------------------------------------ vehicles
// Blocky sedan (AW white sedan). Length along Z (front = +Z).
export function addCar(P, { color = '#e6e6ea', seed = 1 } = {}) {
  const k = 'plastic:' + color;
  P.box(k, 6.2, 1.7, 13.5, [0, 1.75, 0], null, { bevel: 0.35 });
  P.box(k, 5.6, 1.6, 7.0, [0, 3.3, -0.8], null, { bevel: 0.35 });
  P.box('glassDark:#1a2034', 5.66, 1.25, 6.4, [0, 3.35, -0.8]);
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) { P.cyl('black:#0e0e10', 1.05, 1.05, 0.8, 14, [sx * 2.85, 1.05, sz * 4.4], [0, 0, PI / 2]); P.cyl('metal:#9a9ca4', 0.55, 0.55, 0.84, 10, [sx * 2.86, 1.05, sz * 4.4], [0, 0, PI / 2]); }
  for (const sx of [-1, 1]) { P.box('emissive:#fff2d0:1.2', 1.1, 0.45, 0.1, [sx * 2.2, 2.0, 6.76]); P.box('emissive:#ff3020:0.8', 1.1, 0.45, 0.1, [sx * 2.2, 2.1, -6.76]); }
  P.box('metal:#7a7c84', 6.0, 0.4, 0.3, [0, 1.0, 6.8]); P.box('metal:#7a7c84', 6.0, 0.4, 0.3, [0, 1.0, -6.8]);
}

// Cardboard moving box with a marker label on its front (e.g. 'BALCONY GNOME', 'THEO'). size [w, h, d] studs.
export function addCardboardBox(P, { size = [2.4, 2, 2.4], label = '', tape = true } = {}) {
  const [w, h, d] = size; P.box('wood:#b4844f', w, h, d, [0, h / 2, 0], null, { bevel: 0.03 });
  if (tape) P.box('plastic:#c9a874', w * 0.25, 0.02, d + 0.02, [0, h + 0.005, 0]);
  if (label) { const key = 'boxLabel:' + label; texMat(key, signTex([label], '', { bg: '#c8996a', ink: '#1a1410', w: 512, h: 256 }), { roughness: 0.85 }); P.add(key, new THREE.PlaneGeometry(w * 0.86, h * 0.45), [0, h * 0.55, d / 2 + 0.012]); }
}
// Moving truck (EP01 §4.3): cab + 24 x 9 x 10 box with an open back, ramp, boxes inside. Front = +Z, back opening at -Z.
export function addMovingTruck(P, { color = '#e8e6e0', stripe = '#d0402a', boxes = ['BALCONY GNOME', 'THEO', 'KITCHEN', ''] } = {}) {
  const L = 24, W = 9, H = 10, y0 = 2.2, k = 'plaster:' + color; // fine micro-texture: no flat untextured parts (§4.1)
  P.box(k, W, 0.4, L, [0, y0 + 0.2, 0]); P.box(k, 0.3, H, L, [-W / 2 + 0.15, y0 + H / 2, 0]); P.box(k, 0.3, H, L, [W / 2 - 0.15, y0 + H / 2, 0]);
  P.box(k, W, 0.3, L, [0, y0 + H - 0.15, 0]); P.box(k, W, H, 0.3, [0, y0 + H / 2, L / 2 - 0.15]);
  for (const s of [-1, 1]) P.box('plastic:' + stripe, 0.05, 1.2, L - 1, [s * (W / 2 + 0.01), y0 + H * 0.62, 0]);
  P.box('porch:#7a6a5a', W - 0.6, 0.1, L - 0.6, [0, y0 + 0.42, 0]); // plank floor inside
  P.box(k, W - 0.4, 6.2, 7, [0, y0 + 3.4, L / 2 + 3.6], null, { bevel: 0.3 }); P.box('glassDark:#1a2034', W - 0.3, 2.4, 0.2, [0, y0 + 4.8, L / 2 + 7.05]);
  for (const s of [-1, 1]) P.box('glassDark:#1a2034', 0.1, 2.2, 3.2, [s * (W / 2 - 0.15), y0 + 4.7, L / 2 + 4.8]);
  for (const [z, n] of [[-L / 2 + 3.5, 2], [L / 2 - 4.5, 2], [L / 2 + 4.5, 2]]) for (const s of [-1, 1]) { P.cyl('black:#0e0e10', 1.6, 1.6, 1.2, 14, [s * (W / 2 - 0.4), 1.6, z], [0, 0, PI / 2]); P.cyl('metal:#9a9ca4', 0.8, 0.8, 1.24, 10, [s * (W / 2 - 0.4), 1.6, z], [0, 0, PI / 2]); void n; }
  P.box('emissive:#fff2d0:1.2', 1.4, 0.6, 0.1, [-W / 2 + 1.2, y0 + 1.2, L / 2 + 7.1]); P.box('emissive:#fff2d0:1.2', 1.4, 0.6, 0.1, [W / 2 - 1.2, y0 + 1.2, L / 2 + 7.1]);
  for (const s of [-1, 1]) P.box('emissive:#ff3020:0.8', 0.6, 1.2, 0.1, [s * (W / 2 - 0.6), y0 + 1.0, -L / 2 - 0.05]);
  // ramp from the open back to the ground
  const rl = Math.hypot(y0 + 0.4, 8); P.box('metal:#8a8c92', 4, 0.2, rl, [0, (y0 + 0.4) / 2, -L / 2 - 4], [-Math.atan2(y0 + 0.4, 8), 0, 0]);
  // boxes inside, labels toward the open back (-Z)
  boxes.forEach((lab, i) => { P.push(trs([(i % 2 ? 1.6 : -1.7), y0 + 0.45 + (i > 1 ? 2.05 : 0), -L / 2 + 3 + (i > 1 ? 0.3 : 0)], [0, PI, 0])); addCardboardBox(P, { label: lab }); P.pop(); });
}

// ------------------------------------------------------------------ registry for standalone building
// prop(name, opts) -> Group in studs. Names: streetLamp mailbox picketFence bush pine leafyTree flowerbed steppingStones
// wallLantern rockingChair deckChair hoseReel kennel hydrant trashBin potPlant dandelion agentBoard postSign car cardboardBox movingTruck
export function prop(name, o = {}) {
  const P = new Parts(); let extra = [];
  const F = { mailbox: addMailbox, bush: addBush, pine: addPine, leafyTree: addLeafyTree, flowerbed: addFlowerbed, rockingChair: addRockingChair, deckChair: addDeckChair, hoseReel: addHoseReel, kennel: addKennel, hydrant: addHydrant, trashBin: addTrashBin, potPlant: addPotPlant, dandelion: addDandelion, car: addCar, cardboardBox: addCardboardBox, movingTruck: addMovingTruck };
  if (name === 'streetLamp') return streetLamp(o);
  if (name === 'picketFence') return picketFence(o);
  if (name === 'steppingStones') addSteppingStones(P, o.points || [[0, -4], [0, 4]], o);
  else if (name === 'wallLantern') extra = [addWallLantern(P, o).glass];
  else if (name === 'agentBoard') extra = [addAgentBoard(P, o)];
  else if (name === 'postSign') extra = [addPostSign(P, o)];
  else if (F[name]) F[name](P, o); else throw new Error('unknown prop ' + name);
  const g = group(P, name); extra.forEach((e) => g.add(persistTree(e))); return g;
}
export { STUD, range, pick };
