// Props: gold coins (single, piles, flights), pouches, bread, scale, broom, parasol, chest, tents...
import * as THREE from 'three';
import { toon, gold, mk, outline, fxLayer } from './toon.js';
import { canvas, toTex } from './tex.js';
import { hash, clamp } from './util.js';

const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);

// ---------------------------------------------------------------- coins
let coinFace = null;
function coinFaceTex(silver) {
  const [c, g] = canvas(256, 256);
  const base = silver ? '#d8dce2' : '#ffcf4a', dark = silver ? '#8a9098' : '#b07a10', hi = silver ? '#ffffff' : '#fff0a8';
  g.fillStyle = base; g.fillRect(0, 0, 256, 256);
  g.strokeStyle = dark; g.lineWidth = 14; g.beginPath(); g.arc(128, 128, 112, 0, Math.PI * 2); g.stroke();
  g.lineWidth = 5; g.beginPath(); g.arc(128, 128, 88, 0, Math.PI * 2); g.stroke();
  // a simple eight-point star in the middle and a ring of dots
  g.fillStyle = dark;
  for (let i = 0; i < 2; i++) { g.save(); g.translate(128, 128); g.rotate(i * Math.PI / 4); g.fillRect(-34, -34, 68, 68); g.restore(); }
  g.fillStyle = base; g.beginPath(); g.arc(128, 128, 24, 0, Math.PI * 2); g.fill();
  g.fillStyle = dark; for (let i = 0; i < 16; i++) { const a = i / 16 * Math.PI * 2; g.beginPath(); g.arc(128 + Math.cos(a) * 100, 128 + Math.sin(a) * 100, 4, 0, Math.PI * 2); g.fill(); }
  g.fillStyle = hi; g.globalAlpha = 0.5; g.beginPath(); g.ellipse(95, 85, 40, 22, -0.6, 0, Math.PI * 2); g.fill();
  return toTex(c, { aniso: 8 });
}
export const COIN_R = 0.032;
export function coinGeometry() { return new THREE.CylinderGeometry(COIN_R, COIN_R, 0.006, 24); }
let _gm = null, _sm = null;
export function coinMats() {
  if (!_gm) {
    const ft = coinFaceTex(false), st = coinFaceTex(true);
    const g = gold({ rough: 0.22, glow: 0.8, env: 1.8 }), gf = gold({ rough: 0.22, glow: 0.8, env: 1.8, map: ft });
    // coins read as bright yellow gold even in shade
    for (const m of [g, gf]) m.emissive.set('#b8820e');
    const s = new THREE.MeshStandardMaterial({ color: '#dde2ea', metalness: 1, roughness: 0.25 }), sf = new THREE.MeshStandardMaterial({ color: '#ffffff', metalness: 1, roughness: 0.25, map: st });
    _gm = [g, gf, gf]; _sm = [s, sf, sf];
  }
  return { gold: _gm, silver: _sm };
}

// a pool of instanced coins that the shots place every frame
export class CoinPool {
  constructor(parent, n, silver = false, scale = 1) {
    const geo = coinGeometry(); if (scale !== 1) geo.scale(scale, scale, scale);
    this.mesh = new THREE.InstancedMesh(geo, coinMats()[silver ? 'silver' : 'gold'], n);
    this.mesh.castShadow = true; this.mesh.receiveShadow = true;
    this.mesh.frustumCulled = false;
    this.n = n; this.used = 0;
    this.m = new THREE.Matrix4(); this.q = new THREE.Quaternion(); this.e = new THREE.Euler(); this.sc = new THREE.Vector3(1, 1, 1);
    parent.add(this.mesh);
    this.clear();
  }
  clear() { this.used = 0; this.mesh.count = 0; }
  add(p, rx, ry, rz, s = 1) {
    if (this.used >= this.n) return;
    this.e.set(rx, ry, rz); this.q.setFromEuler(this.e); this.sc.setScalar(s);
    this.m.compose(p, this.q, this.sc);
    this.mesh.setMatrixAt(this.used++, this.m);
    this.mesh.count = this.used; this.mesh.instanceMatrix.needsUpdate = true;
  }
  // heap of coins on the ground, centred at c (radius r, height h)
  heap(c, r, h, n, seed = 1, s = 1) {
    for (let i = 0; i < n; i++) {
      const a = hash(seed, i) * Math.PI * 2, d = Math.sqrt(hash(seed, i + 0.5)) * r;
      const y = Math.max(0, h * (1 - d / r)) * (0.75 + 0.25 * hash(seed, i + 0.7)) + 0.003;
      this.add(V(c.x + Math.cos(a) * d, c.y + y, c.z + Math.sin(a) * d), (hash(seed, i + 1) - 0.5) * 1.4, hash(seed, i + 2) * 6.3, (hash(seed, i + 3) - 0.5) * 1.4, s);
    }
  }
  // coins scattered flat on the ground in a rectangle
  scatter(x0, x1, z0, z1, n, y = 0.003, seed = 3, s = 1) {
    for (let i = 0; i < n; i++) this.add(V(x0 + (x1 - x0) * hash(seed, i), y, z0 + (z1 - z0) * hash(seed, i + 0.3)), (hash(seed, i + 1) - 0.5) * 0.25, hash(seed, i + 2) * 6.3, (hash(seed, i + 4) - 0.5) * 0.25, s);
  }
  // ballistic coins: each launched at t0 from o with velocity v, tumbling; lands and lies flat
  flight(t, list, ground = 0) {
    for (const c of list) {
      const dt = t - c.t0;
      if (dt < 0) continue;
      const tl = c.v.y / 9.8 + Math.sqrt(Math.max(0, (c.v.y * c.v.y) / 96.04 + 2 * (c.o.y - ground - 0.003) / 9.8));
      const tt = Math.min(dt, tl);
      const p = V(c.o.x + c.v.x * tt, c.o.y + c.v.y * tt - 4.9 * tt * tt, c.o.z + c.v.z * tt);
      if (dt < tl) this.add(p, c.spin.x * tt + c.r0, c.spin.y * tt, c.spin.z * tt, c.s || 1);
      else this.add(V(p.x, ground + 0.003, p.z), (hash(c.seed, 1) - 0.5) * 0.2, hash(c.seed, 2) * 6.3, 0, c.s || 1);
    }
  }
}
// a spray of coins thrown from o toward dir
export function throwCoins(n, t0, o, dir, speed, spread, seed, s = 1) {
  const list = [];
  const d = dir.clone().normalize();
  for (let i = 0; i < n; i++) {
    const r = (k) => hash(seed, i * 3.1 + k) - 0.5;
    const v = d.clone().multiplyScalar(speed * (0.8 + 0.4 * (r(1) + 0.5))).add(V(r(2), r(3) + 0.25, r(4)).multiplyScalar(spread));
    list.push({ t0: t0 + (r(5) + 0.5) * 0.18, o: o.clone().add(V(r(6), r(7), r(8)).multiplyScalar(0.12)), v, r0: r(9) * 3,
      spin: V(r(10) * 22, r(11) * 10, r(12) * 18), seed: seed * 100 + i, s });
  }
  return list;
}

// ---------------------------------------------------------------- small props
function clothTex(base, stripe) {
  const [c, g] = canvas(128, 128); g.fillStyle = base; g.fillRect(0, 0, 128, 128);
  if (stripe) { g.fillStyle = stripe; g.fillRect(0, 50, 128, 10); g.fillRect(0, 70, 128, 4); }
  for (let i = 0; i < 300; i++) { g.fillStyle = `rgba(0,0,0,${Math.random() * 0.05})`; g.fillRect(Math.random() * 128, Math.random() * 128, 2, 2); }
  return toTex(c, { aniso: 4 });
}
export function pouch(color = '#8a3a2a', size = 1) {
  const g = new THREE.Group();
  const prof = [[0.0, 0.0], [0.07, 0.01], [0.105, 0.05], [0.11, 0.1], [0.085, 0.15], [0.04, 0.18], [0.035, 0.19], [0.06, 0.23], [0.05, 0.25]].map(([r, y]) => new THREE.Vector2(r * size, y * size));
  mk(new THREE.LatheGeometry(prof, 20), toon('#ffffff', { map: clothTex(color, '#e8c24a'), lift: 0.06 }), g, { outline: 4 });
  mk(new THREE.TorusGeometry(0.04 * size, 0.009 * size, 6, 16), gold(), g, { pos: [0, 0.19 * size, 0], rot: [Math.PI / 2, 0, 0], outline: 2.5 });
  const cm = coinMats().gold;
  for (let i = 0; i < 4; i++) mk(coinGeometry(), cm, g, { pos: [(i - 1.5) * 0.02 * size, 0.24 * size, (i % 2) * 0.01], rot: [0.5 + i * 0.3, i, 0.2], scale: size * 0.9, outline: false });
  return g;
}
export function broom() {
  const g = new THREE.Group();
  mk(new THREE.CylinderGeometry(0.014, 0.014, 1.25, 8), toon('#a87a48'), g, { pos: [0, 0.62, 0], outline: 3 });
  const b = mk(new THREE.ConeGeometry(0.11, 0.32, 12), toon('#d8b46a'), g, { pos: [0, 0.0, 0], rot: [Math.PI, 0, 0], scale: [1, 1, 0.45], outline: 3.5 });
  mk(new THREE.TorusGeometry(0.05, 0.012, 6, 14), toon('#8a3a2a'), g, { pos: [0, 0.14, 0], rot: [Math.PI / 2, 0, 0], scale: [1.2, 0.6, 1], outline: 2 });
  return g; // origin at the bristle tips' centre; handle along +y
}
export function bowl(color = '#a8643a') {
  const prof = [[0.0, 0.0], [0.07, 0.0], [0.12, 0.03], [0.14, 0.08], [0.13, 0.085], [0.11, 0.035], [0.0, 0.02]].map(([r, y]) => new THREE.Vector2(r, y));
  return mk(new THREE.LatheGeometry(prof, 24), toon(color, { side: THREE.DoubleSide }), null, { outline: 3 });
}
export function flatbread(r = 0.13) {
  const m = mk(new THREE.CylinderGeometry(r, r * 0.97, 0.03, 20), toon('#d8a45a', { lift: 0.04 }), null, { outline: 2.5 });
  return m;
}
export function loaf() {
  const m = mk(new THREE.SphereGeometry(0.1, 16, 12), toon('#c98a42', { lift: 0.05 }), null, { scale: [1.4, 0.7, 0.9], outline: 3 });
  for (let i = 0; i < 3; i++) mk(new THREE.BoxGeometry(0.02, 0.012, 0.12), toon('#f0d090'), m, { pos: [(i - 1) * 0.045, 0.085, 0], rot: [0, 0.4, 0], outline: false });
  return m;
}
// chalk price board: draw(text) repaints it
export function priceBoard(w = 0.6, h = 0.42) {
  const g = new THREE.Group();
  const [c, ctx] = canvas(512, 360);
  const tex = toTex(c, { aniso: 8 });
  mk(new THREE.BoxGeometry(w + 0.06, h + 0.06, 0.03), toon('#7a4e2a'), g, { outline: 3.5 });
  mk(new THREE.PlaneGeometry(w, h), toon('#ffffff', { map: tex, lift: 0.12 }), g, { pos: [0, 0, 0.017], outline: false, cast: false });
  g.userData.draw = (fn) => {
    ctx.fillStyle = '#2a3a32'; ctx.fillRect(0, 0, 512, 360);
    for (let i = 0; i < 400; i++) { ctx.fillStyle = `rgba(255,255,255,${Math.random() * 0.05})`; ctx.fillRect(Math.random() * 512, Math.random() * 360, 3, 2); }
    ctx.strokeStyle = ctx.fillStyle = '#f4f0e4'; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    fn(ctx);
    tex.needsUpdate = true;
  };
  return g;
}
// two-pan balance: userData.set(angle)
export function balance() {
  const g = new THREE.Group();
  const brass = gold({ color: '#d8a640', rough: 0.35, glow: 0.15 });
  mk(new THREE.CylinderGeometry(0.1, 0.12, 0.04, 20), toon('#5a3a22'), g, { pos: [0, 0.02, 0], outline: 3 });
  mk(new THREE.CylinderGeometry(0.012, 0.012, 0.42, 10), brass, g, { pos: [0, 0.25, 0], outline: 2.5 });
  const beam = new THREE.Group(); beam.position.set(0, 0.46, 0); g.add(beam);
  mk(new THREE.BoxGeometry(0.5, 0.015, 0.015), brass, beam, { outline: 2.5 });
  mk(new THREE.SphereGeometry(0.022, 12, 10), brass, g, { pos: [0, 0.47, 0], outline: 2 });
  const pans = [];
  for (const sd of [-1, 1]) {
    const pan = new THREE.Group(); g.add(pan);
    const plate = mk(new THREE.CylinderGeometry(0.1, 0.07, 0.02, 20, 1, true), brass, pan, { pos: [0, 0, 0], outline: 2.5 });
    mk(new THREE.CircleGeometry(0.07, 20).rotateX(-Math.PI / 2), brass, pan, { pos: [0, -0.009, 0], outline: false });
    const strings = [];
    for (let k = 0; k < 3; k++) {
      const s = mk(new THREE.CylinderGeometry(0.002, 0.002, 1, 4), toon('#2a2018'), pan, { outline: false });
      strings.push([s, k]);
    }
    pans.push({ pan, sd, strings });
  }
  g.userData.pans = pans;
  g.userData.set = (ang) => {
    beam.rotation.z = ang;
    for (const p of pans) {
      const ex = p.sd * 0.24 * Math.cos(ang), ey = 0.46 + p.sd * 0.24 * Math.sin(ang);
      p.pan.position.set(ex, ey - 0.2, 0);
      for (const [s, k] of p.strings) {
        const a = (k / 3) * Math.PI * 2;
        const top = V(0, 0.2, 0), bot = V(Math.cos(a) * 0.09, 0.0, Math.sin(a) * 0.09);
        s.position.copy(top).add(bot).multiplyScalar(0.5);
        s.scale.set(1, top.distanceTo(bot), 1);
        s.quaternion.setFromUnitVectors(V(0, 1, 0), top.clone().sub(bot).normalize());
      }
    }
  };
  g.userData.set(0);
  return g;
}
export function goldStaff(h = 1.9) {
  const g = new THREE.Group();
  const m = gold({ rough: 0.25 });
  mk(new THREE.CylinderGeometry(0.022, 0.026, h, 10), m, g, { pos: [0, h / 2, 0], outline: 3 });
  mk(new THREE.SphereGeometry(0.06, 14, 12), m, g, { pos: [0, h + 0.03, 0], outline: 3 });
  mk(new THREE.ConeGeometry(0.035, 0.14, 10), m, g, { pos: [0, h + 0.14, 0], outline: 2.5 });
  return g;
}
// royal parasol with a gold bird on top
export function parasol() {
  const g = new THREE.Group();
  mk(new THREE.CylinderGeometry(0.02, 0.02, 2.6, 8), gold({ rough: 0.3 }), g, { pos: [0, 1.3, 0], outline: 3 });
  const [c, x] = canvas(512, 128);
  x.fillStyle = '#c4202c'; x.fillRect(0, 0, 512, 128);
  x.fillStyle = '#f2c24a'; for (let i = 0; i < 16; i++) x.fillRect(i * 32, 0, 14, 128);
  x.fillStyle = '#f2c24a'; x.fillRect(0, 108, 512, 20);
  const dome = mk(new THREE.SphereGeometry(0.95, 32, 12, 0, Math.PI * 2, 0, Math.PI * 0.42), toon('#ffffff', { map: toTex(c), side: THREE.DoubleSide, lift: 0.08 }), g, { pos: [0, 2.15, 0], scale: [1, 0.55, 1], outline: 4 });
  for (let i = 0; i < 24; i++) {
    const a = (i / 24) * Math.PI * 2;
    mk(new THREE.SphereGeometry(0.035, 8, 6), gold(), g, { pos: [Math.cos(a) * 0.9, 2.15 + 0.13, Math.sin(a) * 0.9], outline: false });
  }
  // falcon
  const b = new THREE.Group(); b.position.set(0, 2.72, 0); g.add(b);
  const gm = gold({ rough: 0.25 });
  mk(new THREE.SphereGeometry(0.08, 12, 10), gm, b, { scale: [0.8, 1, 1.3], outline: 2.5 });
  mk(new THREE.SphereGeometry(0.05, 12, 10), gm, b, { pos: [0, 0.09, 0.07], outline: 2.5 });
  mk(new THREE.ConeGeometry(0.02, 0.05, 6), gm, b, { pos: [0, 0.08, 0.13], rot: [Math.PI / 2, 0, 0], outline: 2 });
  for (const sd of [-1, 1]) mk(new THREE.SphereGeometry(0.06, 10, 8), gm, b, { pos: [sd * 0.08, 0.03, -0.02], scale: [0.5, 0.9, 1.5], rot: [0.3, 0, sd * 0.5], outline: 2.5 });
  return g;
}
export function chest() {
  const g = new THREE.Group();
  const wood = toon('#8a5228'), band = gold({ color: '#d0a040', rough: 0.35, glow: 0.12 });
  mk(new THREE.BoxGeometry(0.8, 0.42, 0.5), wood, g, { pos: [0, 0.21, 0], outline: 4 });
  // the inside: dark wooden walls facing inwards (seen from a camera inside the chest)
  const inner = toon('#3a2010', { side: THREE.BackSide });
  const hide = new THREE.MeshBasicMaterial({ visible: false });
  mk(new THREE.BoxGeometry(0.72, 0.4, 0.42), [inner, inner, hide, inner, inner, inner], g, { pos: [0, 0.22, 0], outline: false, cast: false });
  for (const x of [-0.3, 0.3]) mk(new THREE.BoxGeometry(0.06, 0.43, 0.51), band, g, { pos: [x, 0.21, 0], outline: 2.5 });
  const lid = new THREE.Group(); lid.position.set(0, 0.42, -0.25); g.add(lid);
  mk(new THREE.CylinderGeometry(0.25, 0.25, 0.8, 20, 1, false, 0, Math.PI), wood, lid, { pos: [0, 0, 0.25], rot: [0, 0, Math.PI / 2], scale: [1, 1, 0.5], outline: 4 });
  for (const x of [-0.3, 0.3]) mk(new THREE.CylinderGeometry(0.255, 0.255, 0.06, 20, 1, false, 0, Math.PI), band, lid, { pos: [x, 0, 0.25], rot: [0, 0, Math.PI / 2], scale: [1, 1, 0.5], outline: 2 });
  mk(new THREE.BoxGeometry(0.1, 0.12, 0.03), band, g, { pos: [0, 0.38, 0.26], outline: 2 });
  g.userData.lid = lid;
  return g;
}
export function moth() {
  const g = new THREE.Group();
  const m = toon('#9a8e80', { side: THREE.DoubleSide });
  mk(new THREE.SphereGeometry(0.02, 10, 8), toon('#6e6458'), g, { scale: [0.8, 0.8, 2.2], outline: 1.5 });
  const wings = [];
  for (const sd of [-1, 1]) {
    const w = new THREE.Group(); g.add(w);
    const shape = new THREE.Shape(); shape.moveTo(0, 0); shape.quadraticCurveTo(0.09, 0.06, 0.08, -0.02); shape.quadraticCurveTo(0.05, -0.07, 0, -0.02);
    const geo = new THREE.ShapeGeometry(shape); geo.rotateX(-Math.PI / 2); if (sd < 0) geo.scale(-1, 1, 1);
    mk(geo, m, w, { outline: false });
    wings.push([w, sd]);
  }
  g.userData.flap = (t) => { for (const [w, sd] of wings) w.rotation.z = sd * Math.sin(t * 52) * 0.9; };
  return g;
}
export function lantern(color = '#ffb85a') {
  const g = new THREE.Group();
  const metal = new THREE.MeshStandardMaterial({ color: '#3a2a18', metalness: 0.6, roughness: 0.4 });
  mk(new THREE.CylinderGeometry(0.1, 0.07, 0.24, 8, 1, true), new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 2.2, side: THREE.DoubleSide }), g, { outline: false, cast: false });
  mk(new THREE.ConeGeometry(0.13, 0.12, 8), metal, g, { pos: [0, 0.18, 0], outline: 2.5 });
  mk(new THREE.CylinderGeometry(0.075, 0.09, 0.04, 8), metal, g, { pos: [0, -0.14, 0], outline: 2.5 });
  mk(new THREE.CylinderGeometry(0.004, 0.004, 0.6, 4), metal, g, { pos: [0, 0.54, 0], outline: false });
  return g;
}
export function rope(a, b, sag = 0.3, r = 0.012, color = '#a8865a') {
  const mid = a.clone().add(b).multiplyScalar(0.5); mid.y -= sag;
  const curve = new THREE.QuadraticBezierCurve3(a, mid, b);
  return mk(new THREE.TubeGeometry(curve, 24, r, 5), toon(color), null, { outline: false });
}
// little triangle bunting along a rope
export function bunting(a, b, n, sag, colors) {
  const g = new THREE.Group();
  g.add(rope(a, b, sag, 0.008, '#e8e0d0'));
  for (let i = 1; i < n; i++) {
    const t = i / n;
    const p = a.clone().lerp(b, t); p.y -= sag * 4 * t * (1 - t);
    const tri = new THREE.Shape(); tri.moveTo(-0.14, 0); tri.lineTo(0.14, 0); tri.lineTo(0, -0.3);
    const m = mk(new THREE.ShapeGeometry(tri), toon(colors[i % colors.length], { side: THREE.DoubleSide, lift: 0.1 }), g, { outline: false });
    m.position.copy(p); m.lookAt(p.clone().add(new THREE.Vector3(b.z - a.z, 0, a.x - b.x)));
  }
  return g;
}
export function campfire() {
  const g = new THREE.Group();
  const log = toon('#5a3a22');
  for (let i = 0; i < 4; i++) mk(new THREE.CylinderGeometry(0.05, 0.05, 0.7, 8), log, g, { pos: [0, 0.06, 0], rot: [Math.PI / 2, i * Math.PI / 4, 0.15], outline: 3 });
  for (let i = 0; i < 9; i++) { const a = i / 9 * Math.PI * 2; mk(new THREE.DodecahedronGeometry(0.09, 0), toon('#8a8478'), g, { pos: [Math.cos(a) * 0.42, 0.05, Math.sin(a) * 0.42], outline: 2.5 }); }
  const flames = [];
  for (let i = 0; i < 3; i++) {
    const f = new THREE.Mesh(new THREE.ConeGeometry(0.16 - i * 0.04, 0.6 - i * 0.12, 10), new THREE.MeshBasicMaterial({ color: ['#ff7a1a', '#ffb43a', '#fff0a0'][i], transparent: true, opacity: 0.92 - i * 0.1, depthWrite: false }));
    f.position.y = 0.3 - i * 0.03; g.add(f); flames.push(f);
  }
  flames.forEach((f) => f.layers.set(2));
  const light = new THREE.PointLight('#ff9a40', 9, 9, 1.6); light.position.set(0, 0.55, 0); light.castShadow = true; light.shadow.mapSize.set(1024, 1024); g.add(light);
  g.userData.tick = (t) => {
    flames.forEach((f, i) => { const k = 1 + Math.sin(t * (9 + i * 3) + i) * 0.12 + Math.sin(t * 17.3 + i * 2) * 0.06; f.scale.set(1 / Math.sqrt(k), k, 1 / Math.sqrt(k)); f.rotation.y = t * (1 + i); });
    light.intensity = 9 * (0.9 + Math.sin(t * 13) * 0.06 + Math.sin(t * 7.7) * 0.05);
  };
  return g;
}
export function tent(color = '#e8dcc0', stripe = '#b8402a', w = 2.4, d = 2.2, h = 1.9) {
  const g = new THREE.Group();
  const [c, x] = canvas(256, 256); x.fillStyle = color; x.fillRect(0, 0, 256, 256); x.fillStyle = stripe; for (let i = 0; i < 6; i++) x.fillRect(i * 44, 0, 16, 256);
  const geo = new THREE.ConeGeometry(Math.max(w, d) / 1.6, h, 4, 1, true); geo.rotateY(Math.PI / 4);
  mk(geo, toon('#ffffff', { map: toTex(c), side: THREE.DoubleSide, lift: 0.05 }), g, { pos: [0, h / 2, 0], scale: [w / Math.max(w, d), 1, d / Math.max(w, d)], outline: 4.5 });
  mk(new THREE.CylinderGeometry(0.03, 0.03, h + 0.3, 6), toon('#6a4a2a'), g, { pos: [0, (h + 0.3) / 2, 0], outline: 2.5 });
  return g;
}
