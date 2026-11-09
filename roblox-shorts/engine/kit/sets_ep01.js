// EP01 sets (VISUAL_BIBLE §4.1-4.4, §5; ASSETS.md "SETS"): our front garden by time of day and era (heroLot), next door
// (lot A2: plastic gnomes, the REX kennel, the lead into THE HOLE), the moving truck (open / closed / leaving, cargo dome
// light, roller door, rear POV rig), the SOLD sticker, the epilogue back garden (bench, deck chair, garden table, the
// granddaughter's lit window), the phone and the yearly Polaroid series (photos rendered from the 3D set into textures).
// API with examples: engine/kit/README_EP01.md ("SETS" section).
//
//   import * as S from '../../kit/sets_ep01.js';
//   const H = S.heroLot(ctx, { tod: 'night', bed: 'empty', truck: 'open' }); ctx.add(H);   // Group in METRES
//   ctx.camera.set(H.ep01.views.emptySpot).push(0.2);                                     // named camera anchors
//   S.heroLight(ctx, H);                                                                    // the tod's preset + room glow
//   update(ctx, t) { H.ep01.update(t); }                                                    // sticker, truck, LED...
//
// heroLot wraps sets.buildLawnCloseup(ctx, { seed: 'ep01' }) (the house of the approved s05/s09: lot A1, bungalow,
// mustard siding, purple curtains) and cuts a real hole in the front wall at the bedroom window over Grandpa's bed
// (A1.bed0): behind the glass sits the real room (interiors.bedroomRoom), so the same room works from inside and outside.
// Root layout: root (metres, identity) > [ set (the cached street clone, studs, scaled by STUD), metre-space extras
// (gnomes, truck, lights) ]. root.userData = the street's userData (slots, lots, lamps, windows, views) + ep01 anchors,
// so sets.place / lighting presets / practicals work on the root exactly as on a plain street.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import * as sets from './sets.js';
import * as K from './chars.js';
import { Parts, M, texMat, signTex, boxUV, planarUV, trs, makeRng, hash32, persistTree, shade, STUD, FONT, glassSheenTex, glowSpriteMat, TX } from './kitlib.js';
import { addHouse } from './suburb.js';
import * as P_ from './props.js';
import * as I from './interiors.js';
import { noise3 } from '../core/random.js';

const PI = Math.PI, DEG = PI / 180, S = STUD;
const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
const V3 = (a) => new THREE.Vector3(a[0], a[1], a[2]);
const outBack = (x) => { const c1 = 1.70158, c3 = c1 + 1; const u = clamp01(x) - 1; return 1 + c3 * u * u * u + c1 * u * u; };
const outCubic = (x) => 1 - Math.pow(1 - clamp01(x), 3);
const outQuad = (x) => 1 - (1 - clamp01(x)) * (1 - clamp01(x));
const r3 = (v) => v.toArray().map((x) => +x.toFixed(4));
const XM = I.XM;

// ------------------------------------------------------------------ geometry surgery on the cached street (cached per worker)
function nonIndexed(g) { return g.index ? g.toNonIndexed() : g.clone(); }
// Copy triangles of `g` for which keep(a, b, c, n) is true (a/b/c = vertex positions, n = face normal); returns
// { geo, removed: [{ p: [3 Vector3], uv: [3 Vector2] }] }.
function filterTris(g, keep) {
  const s = nonIndexed(g); const pos = s.attributes.position, nor = s.attributes.normal, uv = s.attributes.uv;
  const P = [], N = [], U = [], removed = []; const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3(), n = new THREE.Vector3();
  for (let i = 0; i < pos.count; i += 3) {
    a.fromBufferAttribute(pos, i); b.fromBufferAttribute(pos, i + 1); c.fromBufferAttribute(pos, i + 2); n.copy(b).sub(a).cross(c.clone().sub(a)).normalize();
    if (keep(a, b, c, n)) { for (let k = 0; k < 3; k++) { P.push(pos.getX(i + k), pos.getY(i + k), pos.getZ(i + k)); N.push(nor.getX(i + k), nor.getY(i + k), nor.getZ(i + k)); U.push(uv ? uv.getX(i + k) : 0, uv ? uv.getY(i + k) : 0); } }
    else removed.push({ p: [a.clone(), b.clone(), c.clone()], uv: uv ? [0, 1, 2].map((k) => new THREE.Vector2(uv.getX(i + k), uv.getY(i + k))) : null });
  }
  const o = new THREE.BufferGeometry(); o.setAttribute('position', new THREE.Float32BufferAttribute(P, 3)); o.setAttribute('normal', new THREE.Float32BufferAttribute(N, 3)); o.setAttribute('uv', new THREE.Float32BufferAttribute(U, 2));
  o.computeBoundingSphere(); o.computeBoundingBox(); s.dispose(); return { geo: o, removed };
}
// Append quads [corners CCW from the front, normal, uv(x, y)] to a non-indexed geometry.
function appendQuads(geo, quads) {
  const P = Array.from(geo.attributes.position.array), N = Array.from(geo.attributes.normal.array), U = Array.from(geo.attributes.uv.array);
  for (const { c, n, uv } of quads) for (const k of [0, 1, 2, 0, 2, 3]) { P.push(...c[k]); N.push(...n); U.push(...uv(c[k])); }
  const o = new THREE.BufferGeometry(); o.setAttribute('position', new THREE.Float32BufferAttribute(P, 3)); o.setAttribute('normal', new THREE.Float32BufferAttribute(N, 3)); o.setAttribute('uv', new THREE.Float32BufferAttribute(U, 2));
  o.computeBoundingSphere(); o.computeBoundingBox(); geo.dispose(); return o;
}
// Front wall of the house (siding mesh, lot-local studs): remove the body box's front face and rebuild it around the
// window hole, keeping the original UV mapping (fitted from the removed face) so the boards line up.
function holeySidingGeo(geo, hole, zFace, wallTop) {
  const [x0, x1, y0, y1] = hole;
  const { geo: g, removed } = filterTris(geo, (a, b, c, n) => !(n.z > 0.9 && Math.abs(a.z - zFace) < 1e-3 && Math.abs(b.z - zFace) < 1e-3 && Math.abs(c.z - zFace) < 1e-3 && Math.max(a.y, b.y, c.y) <= wallTop + 1e-3));
  const vs = removed.flatMap((t) => t.p.map((p, i) => ({ p, uv: t.uv[i] })));
  const xs = vs.map((v) => v.p.x), ys = vs.map((v) => v.p.y); const XL = Math.min(...xs), XR = Math.max(...xs), YB = Math.min(...ys), YT = Math.max(...ys);
  const vA = vs.find((v) => Math.abs(v.p.x - XL) < 1e-3 && Math.abs(v.p.y - YB) < 1e-3), vB = vs.find((v) => Math.abs(v.p.x - XR) < 1e-3 && Math.abs(v.p.y - YT) < 1e-3);
  const au = (vB.uv.x - vA.uv.x) / (XR - XL), av = (vB.uv.y - vA.uv.y) / (YT - YB); const uvf = (p) => [vA.uv.x + (p[0] - XL) * au, vA.uv.y + (p[1] - YB) * av];
  const q = (xa, xb, ya, yb) => ({ c: [[xa, ya, zFace], [xb, ya, zFace], [xb, yb, zFace], [xa, yb, zFace]], n: [0, 0, 1], uv: uvf });
  return appendQuads(g, [q(XL, x0, YB, YT), q(x1, XR, YB, YT), q(x0, x1, YB, y0), q(x0, x1, y1, YT)]);
}
function stripWindowGeo(geo, hole, zFace) {
  const [x0, x1, y0, y1] = hole;
  return filterTris(geo, (a, b, c, n) => { const cx = (a.x + b.x + c.x) / 3, cy = (a.y + b.y + c.y) / 3, cz = (a.z + b.z + c.z) / 3; return !(n.z > 0.9 && Math.abs(cz - zFace) < 0.2 && cx > x0 - 1e-3 && cx < x1 + 1e-3 && cy > y0 - 1e-3 && cy < y1 + 1e-3); }).geo;
}
const persistGeo = (g) => { g.userData.persistent = true; return g; };

// ------------------------------------------------------------------ small textures / decals
function soldTex() {
  return I.ctex('soldSticker', 512, 192, (g, W, H) => {
    g.clearRect(0, 0, W, H); const rr = (x, y, w, h, r) => { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); };
    g.fillStyle = '#d01818'; rr(6, 6, W - 12, H - 12, 34); g.fill(); g.strokeStyle = '#f6f3ee'; g.lineWidth = 10; rr(22, 22, W - 44, H - 44, 24); g.stroke();
    g.fillStyle = '#f6f3ee'; g.font = `bold 118px ${FONT}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('SOLD', W / 2, H / 2 + 6);
  }, { mips: true });
}
function priceStickerTex(text = '$4.99') {
  return I.ctex('price:' + text, 128, 96, (g, W, H) => { g.fillStyle = '#f7f2e4'; g.beginPath(); g.ellipse(W / 2, H / 2, W / 2 - 2, H / 2 - 2, 0, 0, PI * 2); g.fill(); g.strokeStyle = '#d01818'; g.lineWidth = 5; g.stroke(); g.fillStyle = '#d01818'; g.font = `bold 34px ${FONT}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(text, W / 2, H / 2 + 2); });
}
// Soil ring left by Grandpa (pale flattened disc, darker rim, two boot dents); hole = sunken dark soil with a lip.
function soilTex(kind) {
  return I.ctex('soil2:' + kind, 256, 256, (g, W, H) => {
    const r = makeRng(hash32('soil', kind)); g.clearRect(0, 0, W, H); const c = W / 2;
    if (kind === 'ring' || kind === 'ringFresh') { // flattened soil where he stood: slightly paler and smoother, a pressed rim, two boot soles
      const base = kind === 'ring' ? [92, 68, 48] : [84, 60, 42];
      const gr = g.createRadialGradient(c, c, 10, c, c, c); gr.addColorStop(0, `rgba(${base},0.95)`); gr.addColorStop(0.66, `rgba(${base},0.9)`); gr.addColorStop(0.8, 'rgba(58,38,24,0.75)'); gr.addColorStop(0.9, 'rgba(70,46,30,0.35)'); gr.addColorStop(1, 'rgba(70,46,30,0)'); g.fillStyle = gr; g.fillRect(0, 0, W, H);
      for (let k = 0; k < 900; k++) { const a = r() * PI * 2, d = Math.sqrt(r()) * c * 0.78; const l = r() < 0.5; g.fillStyle = l ? `rgba(170,140,110,${0.12 + 0.18 * r()})` : `rgba(50,32,20,${0.12 + 0.2 * r()})`; const s = 1 + r() * 3; g.fillRect(c + Math.cos(a) * d, c + Math.sin(a) * d, s, s); }
      if (kind === 'ring') for (const [sx, dy, rot] of [[-1, -14, -0.22], [1, 16, 0.14]]) { // boot soles (one a half step ahead): toe + heel, tread lines, soft
        g.save(); g.translate(c + sx * 34, c + dy); g.rotate(rot); g.fillStyle = 'rgba(56,36,22,0.42)';
        g.beginPath(); g.ellipse(0, -13, 12, 19, 0, 0, PI * 2); g.fill(); g.beginPath(); g.ellipse(0, 20, 10, 11, 0, 0, PI * 2); g.fill();
        g.strokeStyle = 'rgba(30,18,10,0.35)'; g.lineWidth = 2; for (let y = -28; y < 30; y += 6) { if (y > 4 && y < 9) continue; g.beginPath(); g.moveTo(-8, y); g.lineTo(8, y); g.stroke(); } g.restore(); }
    } else { // hole
      const gr = g.createRadialGradient(c, c, 4, c, c, c); gr.addColorStop(0, '#120a06'); gr.addColorStop(0.55, '#1a0f08'); gr.addColorStop(0.72, '#3a2414'); gr.addColorStop(0.82, '#6a4a30'); gr.addColorStop(1, 'rgba(106,74,48,0)'); g.fillStyle = gr; g.fillRect(0, 0, W, H);
      const ig = g.createLinearGradient(0, c - 60, 0, c + 10); ig.addColorStop(0, 'rgba(90,60,36,0.6)'); ig.addColorStop(1, 'rgba(90,60,36,0)'); g.fillStyle = ig; g.beginPath(); g.arc(c, c, c * 0.55, PI, 2 * PI); g.fill();
    }
  });
}
function decalDisc(key, tex, r, { y = 0.01, order = 2 } = {}) {
  const m = I.decalMat(key, tex, { roughness: 0.95, transparent: true }); m.depthWrite = false; m.polygonOffset = true; m.polygonOffsetFactor = -3; m.polygonOffsetUnits = -3;
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(2 * r, 2 * r), m); mesh.rotation.x = -PI / 2; mesh.position.y = y; mesh.renderOrder = order; mesh.name = key; return persistTree(mesh);
}
function crumbsGeo(r, n, seed, h = 0.12) { // a lip of soil crumbs around a ring of radius r (studs)
  const rng = makeRng(hash32('crumbs', seed)); const list = [];
  for (let i = 0; i < n; i++) { const a = rng() * PI * 2, d = r * (0.95 + rng() * 0.35); const s = 0.05 + rng() * 0.09; const g = new THREE.IcosahedronGeometry(s, 0); g.scale(1, 0.6 + rng() * 0.4, 1); g.translate(Math.cos(a) * d, s * 0.4 + rng() * h * 0.3, Math.sin(a) * d); list.push(g); }
  return list;
}

// ------------------------------------------------------------------ the moving truck (metres)
// movingTruck(ctx, { mode: 'open' | 'closed' | 'leaving', dome: true, boxes, t0 (leave start, s), vmax: 6, accel: 3 })
// -> Group (metres). Faces +Z locally (cab at +Z, open back at -Z), like props.movingTruck. Children: 'truckDrive'
// (everything that moves), wheels 'wheel0..5', 'balconyBox' (separate, with hinged flaps 'flapL'/'flapR'),
// 'cargoDome' (+ a 1.5 cd point light 'cargoLight'), 'rollerDoor'. ep01.update(t) drives the leaving motion.
export const TRUCK = { L: 24, W: 9, H: 10, y0: 2.2, wheelR: 1.6, wheelZ: [-8.5, 7.5, 16.5] };
function balconyBoxTpl(ctx) {
  return ctx.cache('ep01:balconyBox', () => {
    const g = new THREE.Group(); g.name = 'balconyBox'; const P = new Parts(); P_.addCardboardBox(P, { size: [3.0, 2.2, 2.6], label: 'BALCONY GNOME', tape: false }); g.add(persistTree(P.build(M, { name: 'boxBody' })));
    for (const s of [-1, 1]) { const f = new THREE.Group(); f.name = s < 0 ? 'flapL' : 'flapR'; f.position.set(s * 1.5, 2.2, 0); const F = new Parts(); F.box('wood:#b4844f', 1.5, 0.04, 2.6, [-s * 0.75, 0.02, 0]); F.box('plastic:#c9a874', 0.4, 0.05, 2.62, [-s * 1.3, 0.03, 0]); f.add(persistTree(F.build(M, { name: 'flap' }))); g.add(f); }
    return g;
  });
}
function wheelTpl(ctx) {
  return ctx.cache('ep01:truckWheel', () => {
    const P = new Parts(); P.cyl('black:#0e0e10', 1.6, 1.6, 1.2, 20, [0, 0, 0], [0, 0, PI / 2]); P.cyl('metal:#9a9ca4', 0.8, 0.8, 1.24, 14, [0, 0, 0], [0, 0, PI / 2]);
    for (let i = 0; i < 5; i++) { const a = (i / 5) * PI * 2; P.cyl('metal:#5a5c64', 0.1, 0.1, 1.3, 6, [0, Math.cos(a) * 0.5, Math.sin(a) * 0.5], [0, 0, PI / 2]); }
    return persistTree(P.build(M, { name: 'wheel' }));
  });
}
export function movingTruck(ctx, o = {}) {
  const mode = o.mode || 'open'; const { L, W, H, y0 } = TRUCK; const layout = o.layout || (mode === 'leaving' ? 'aisle' : 'stack');
  const body = ctx.cache('ep01:truckBody:' + (mode === 'open' ? 'ramp' : 'noramp') + ':' + layout, () => {
    const P = new Parts(); P_.addMovingTruck(P, { boxes: [] }); P.byKey.delete('black:#0e0e10'); P.byKey.delete('metal:#9a9ca4'); if (mode !== 'open') P.byKey.delete('metal:#8a8c92');
    // the cargo stack near the open back (labels out of the back), roller-door drum, dome lamp housing
    (layout === 'aisle' ? [['FRAGILE', -3.0, 0, -9.6, 0.04], ['', 3.0, 0, -9.8, -0.06], ['', -3.1, 2.05, -9.5, 0.1], ['THEO', 3.0, 2.05, -9.7, -0.12], ['KITCHEN', -3.0, 0, -6.9, 0.0], ['BOOKS', 3.0, 0, -7.0, 0.05], ['THEO', -3.0, 2.05, -6.8, -0.08], ['', 3.1, 4.1, -9.6, 0.15], ['LAMPS', -3.0, 0, -4.2, 0.02], ['', 3.0, 0, -4.3, -0.04]]
      : [['FRAGILE', -3.0, 0, -10.4, 0.06], ['', 3.0, 0, -10.5, -0.1], ['', -3.1, 2.05, -10.3, 0.12], ['THEO', -1.8, 0, -7.0, 0.1], ['KITCHEN', 1.9, 0, -6.8, -0.08], ['BOOKS', -1.7, 2.05, -7.1, 0.06], ['LAMPS', 1.7, 2.05, -6.6, 0.2], ['THEO', 0.1, 0, -4.2, 0.0]]).forEach(([lab, x, y, z, a]) => { P.push(trs([x, y0 + 0.45 + y, z], [0, PI + a, 0])); P_.addCardboardBox(P, { size: [2.6, 2.05, 2.4], label: lab }); P.pop(); });
    P.box('fab:#5a7ac8', 2.2, 4.2, 1.2, [-3.2, y0 + 2.6, 2.0], [0, 0.2, 0.05]); // a wrapped mattress against the wall
    P.cyl('metal:#c8c8cc', 0.55, 0.55, W - 0.7, 16, [0, y0 + H - 0.75, -L / 2 + 0.6], [0, 0, PI / 2]); // roller-door drum (door up)
    for (const s of [-1, 1]) P.box('metal:#9a9ca4', 0.25, H - 0.6, 0.3, [s * (W / 2 - 0.35), y0 + H / 2, -L / 2 + 0.2]); // door rails
    P.cyl('metal:#8a8c92', 0.5, 0.5, 0.15, 14, [0, y0 + H - 0.35, -9.2]);
    return persistTree(P.build(XM, { name: 'truckBody', cast: true, receive: true }));
  });
  const root = new THREE.Group(); root.name = 'movingTruck'; const sc = new THREE.Group(); sc.scale.setScalar(S); root.add(sc);
  const drive = new THREE.Group(); drive.name = 'truckDrive'; sc.add(drive); drive.add(body.clone(true));
  const wheels = []; TRUCK.wheelZ.forEach((z, i) => [-1, 1].forEach((s, j) => { const w = wheelTpl(ctx).clone(true); w.name = 'wheel' + (i * 2 + j); w.position.set(s * (W / 2 - 0.4), TRUCK.wheelR, z); drive.add(w); wheels.push(w); }));
  // separate BALCONY GNOME box on top of the stack, label out of the back, turned 30 deg toward the house side (+X)
  let bb = null; if (o.balconyBox ?? (layout === 'stack')) { bb = balconyBoxTpl(ctx).clone(true); bb.position.set(-0.3, y0 + 0.45 + 4.15, -7.0); bb.rotation.y = PI + 0.5; drive.add(bb); } // label out of the back, turned toward the house side (local -X)
  // cargo dome light: emissive dome + a 1.5 cd point light (cast no shadow)
  const domeOn = o.dome !== false; const dome = new THREE.Mesh(new THREE.SphereGeometry(0.45, 16, 8, 0, PI * 2, PI / 2, PI / 2), domeOn ? XM('glow:#fff2d8:3') : M('plastic:#e8e4dc')); dome.position.set(0, y0 + H - 0.42, -9.2); dome.name = 'cargoDome'; drive.add(persistTree(dome));
  let light = null; if (domeOn) { light = new THREE.PointLight('#fff0d0', o.domeCd ?? 1.5, 0, 2); light.name = 'cargoLight'; light.position.set(0, y0 + H - 1.2, -9.2); drive.add(light);
    const halo = new THREE.Sprite(glowSpriteMat('ep01dome', { color: '#fff0d0', intensity: 1, opacity: 0.4 })); halo.position.copy(dome.position); halo.scale.set(2.2, 2.2, 1); halo.name = 'cargoHalo'; drive.add(halo); }
  // roller door down (closed / leaving at dawn keeps it open by default: o.door)
  const door = o.door ?? (mode === 'closed' ? 'down' : 'up');
  if (door === 'down') { const D = new Parts(); for (let i = 0; i < 14; i++) D.box('plaster:#e2e0d8', W - 0.7, 0.68, 0.12, [0, y0 + 0.75 + i * 0.68, -L / 2 + 0.25], null, { bevel: 0.03 }); D.box('metal:#5a5c64', 1.2, 0.3, 0.2, [0, y0 + 1.2, -L / 2 + 0.1]); const dg = persistTree(D.build(XM, { name: 'rollerDoor' })); drive.add(dg); }
  // leaving: 0 -> vmax studs/s at `accel`, from t0 (shot seconds); forward = local +Z (cab first)
  const t0 = o.t0 ?? 0, vmax = o.vmax ?? 6, acc = o.accel ?? 3; const tA = vmax / acc;
  const dist = (t) => { const u = t - t0; if (mode !== 'leaving' || u <= 0) return 0; return u < tA ? 0.5 * acc * u * u : 0.5 * acc * tA * tA + vmax * (u - tA); };
  root.ep01 = {
    drive, wheels, balconyBox: bb, dome, light, dist,
    update(t) { const s = dist(t); drive.position.z = s; const a = s / TRUCK.wheelR; for (const w of wheels) w.rotation.x = a; drive.position.y = mode === 'leaving' && t > t0 ? 0.03 * Math.sin(t * 23) * Math.min(1, (t - t0) * 2) : 0; },
    // rear POV rig (s88): camera inside the cargo bay looking out of the open back; follows the truck. Returns ShotCamera specs.
    // yaw: degrees, + turns the view toward the house side of a parked truck (local -X); back: studs inside the opening.
    povCamera({ height = 5.6, back = 8.5, pitch = -4, fov = 70, side = 0, yaw = 12 } = {}) {
      const loc = (t, x, z, y = height) => { root.updateMatrixWorld(true); return new THREE.Vector3(x, y, z + dist(t)).multiplyScalar(S).applyMatrix4(root.matrixWorld); };
      const zc = -L / 2 + back; const a = yaw * DEG; const look = 20 * Math.tan(pitch * DEG);
      return { pos: (t, out) => (out || new THREE.Vector3()).copy(loc(t, side, zc)), target: (t, out) => (out || new THREE.Vector3()).copy(loc(t, side - 20 * Math.sin(a), zc - 20 * Math.cos(a), height + look)), fov };
    },
    // the open back (centre of the opening) in world metres at time t, e.g. a camera target for s29
    backCenter(t = 0) { root.updateMatrixWorld(true); return new THREE.Vector3(0, y0 + H * 0.45, -L / 2 + dist(t)).multiplyScalar(S).applyMatrix4(root.matrixWorld); },
  };
  root.ep01.update(0); return root;
}
// Park a truck at the kerb of a side-A lot: the open back `backOffset` studs from the gate (default 8 to the left, -X),
// cab toward -X, so the open back is seen through the open gate and the ramp runs along the road past the gate.
// Returns the truck.
export function parkTruck(truck, set, lotId = 'A1', { backOffset = -8 } = {}) {
  const L = sets.lot(set, lotId); const roadW = set.userData.roadW || 26; const gx = L.gate[0] / S;
  const cx = gx + backOffset - TRUCK.L / 2, cz = -(roadW / 2) + TRUCK.W / 2 + 0.6;
  truck.position.set(cx * S, -0.4 * S, cz * S); truck.rotation.y = -PI / 2; return truck;
}

// ------------------------------------------------------------------ SOLD sticker (on an agent board mesh)
// soldSticker(board, { t0 }) adds a red rounded 'SOLD' decal diagonally on the board's front; it slaps on at t0 (shot
// seconds): scale 1.3 -> 1 in 4 frames (outBack). t0 = -1: already on. Returns the sticker (sticker.update(t)).
export function soldSticker(board, { t0 = -1, w = 3.3, h = 1.24, angle = 0.26 } = {}) {
  const m = I.decalMat('soldSticker', soldTex(), { roughness: 0.45, transparent: true }); m.polygonOffset = true; m.polygonOffsetFactor = -2;
  const s = new THREE.Mesh(new THREE.PlaneGeometry(w, h), m); s.name = 'soldSticker'; s.position.set(0.05, 0.05, 0.075); s.rotation.z = angle; s.renderOrder = 3; board.add(persistTree(s));
  s.update = (t) => { const f = (t - t0) * 60; s.visible = t0 < 0 || f >= 0; if (!s.visible) return; const k = t0 < 0 ? 1 : 1.3 - 0.3 * outBack(f / 4); s.scale.set(k, k, 1); };
  s.update(0); return s;
}

// ------------------------------------------------------------------ HERO LOT
const POINTED = [0, 1, 2, 3, 4, 5, 7];
const FAMILY_SLOTS = ['bedFront0', 'lawn0', 'lawn1', 'lawn2', 'lawn3', 'bedFront1']; // variants as part1 lawn_stare (POINTED[(2 + k) % 7])
const ERA_DEF = {
  now: { board: true, keepOff: true, bed: 'grandpa', room: 'theo', tree: 0.85, gnomes: FAMILY_SLOTS },
  '2010s': { board: false, keepOff: true, bed: 'none', room: 'hero5', tree: 0.72, toys: true, gnomes: ['bedFront0', 'lawn0', 'lawn2', 'lawn3', 'bedFront1'] },
  '1990s': { board: false, keepOff: true, bed: 'none', room: 'cousin90s', tree: 0.6, gnomes: ['lawn0', 'lawn2', 'lawn3', 'bedFront1'] },
  '1960s': { board: false, keepOff: false, bed: 'none', room: 'dad60s', tree: 0.42, gate: '#6f8fb0', gnomes: ['lawn0', 'lawn3'] },
};
// Repaint by decade for the epilogue years (siding, door) and curtain/tulip colours per year (photos).
const REPAINT = [[0, '#c8a557', '#7a2a20'], [10, '#9fae8c', '#2a4a3a'], [25, '#d9cfb5', '#6b1f1a'], [40, '#7d8ea3', '#24304a'], [52, '#e2e0da', '#5a2a1a']];
const YEAR_CURTAINS = ['#8a5aa0', '#c85a4a', '#5a8ac0', '#d9b25a', '#8a5aa0', '#e0e0d0', '#5a8a6a'];
const YEAR_TULIPS = [['#d8283a', '#f07ab0', '#f2c230', '#f4eee8'], ['#f07ab0', '#b04ad0', '#f4eee8'], ['#d8283a', '#f2c230'], ['#f05a8a', '#f7a8d0', '#ffffff'], ['#f2c230', '#e86a2a', '#f4eee8']];
export const yearLook = (year = 0) => { let r = REPAINT[0]; for (const x of REPAINT) if (year >= x[0]) r = x; return { siding: r[1], door: r[2], curtain: YEAR_CURTAINS[Math.floor(year / 7) % YEAR_CURTAINS.length], tulips: YEAR_TULIPS[Math.floor(year / 3) % YEAR_TULIPS.length], tree: Math.min(1.5, 0.85 + 0.65 * (year / 60)) }; };

// heroLot(ctx, o) -> root (metres). Options (defaults depend on era; see ERA_DEF):
//   tod: 'night' | 'day' | 'dusk' | 'dawn'                    era: 'now' | '2010s' | '1990s' | '1960s'
//   year: 0..60 (epilogue: repaint, grown tree, curtains, tulips, mossy Grandpa: age year/60)
//   bed: 'grandpa' | 'grandpaBack' | 'empty' | 'plastic' | 'hole' | 'none'     lantern: Grandpa's lantern level (0)
//   gnomes: true | false | [slot names] (family gnomes, lanterns: level)        shiftBedFront0: true (1.5 studs to the path)
//   truck: false | 'open' | 'closed' | 'leaving' (+ truckOpts)                    board: bool, sold: null | t0 | -1
//   keepOff: bool    bricks: true (dog-tooth brick edging in front of Grandpa's bed; ep01.bricks[] can be jostled)
//   theoRoom: { era, lit, curtains, curtain } | false (the real room behind the window)    roomGlow: true (room lights)
//   nextDoor: true | { hole, plastics: 3 } | false     tree: scale override      toys: bool (2010s porch toys)
export function heroLot(ctx, o = {}) {
  const era = o.era || 'now'; const E = { ...ERA_DEF[era] }; const tod = o.tod || 'night'; const year = o.year ?? 0; const Y = yearLook(year);
  const set = sets.buildLawnCloseup(ctx, { seed: 'ep01' }); const lotId = 'A1'; const lotG = set.getObjectByName('lot_' + lotId); const L = sets.lot(set, lotId);
  const root = new THREE.Group(); root.name = 'ep01HeroLot'; root.add(set); const xm = new THREE.Group(); xm.name = 'ep01Extras'; root.add(xm);
  const lotPos = lotG.position.clone(); const toLot = (m) => V3(m).divideScalar(S).sub(lotPos); const toWorldM = (p) => V3(p).add(lotPos).multiplyScalar(S);
  const ep = { set, lot: lotG, lotId, tod, era, year, gnomes: { family: {} }, updates: [] };
  // ---- the window over Grandpa's bed (bed0): hole + reveal + glass + the room
  const bedSlot = sets.slot(set, lotId + '.bed0'); const winW = set.userData.windows.filter((w) => w.lot === lotId && w.face === 'front').sort((a, b) => Math.abs(a.pos[0] - bedSlot.pos[0]) - Math.abs(b.pos[0] - bedSlot.pos[0]))[0];
  const wl = toLot(winW.pos); const zFace = wl.z - 0.1; const hole = [wl.x - 2, wl.x + 2, wl.y - 2.5, wl.y + 2.5]; const F = L.deckY / S; const wallTop = F + 10;
  const sid = lotG.children.find((c) => c.isMesh && c.name.startsWith('siding:'));
  const holeGeo = ctx.cache('ep01:sidingHole:' + sid.name, () => persistGeo(holeySidingGeo(sid.geometry, hole, zFace, wallTop)));
  sid.geometry = holeGeo;
  for (const m of lotG.children.filter((c) => c.isMesh && (c.name.startsWith('win:') || c.name === 'glassDark'))) {
    const g2 = ctx.cache('ep01:winStrip:' + m.name, () => persistGeo(stripWindowGeo(m.geometry, hole, zFace + 0.05))); m.geometry = g2;
  }
  const winGlow = lotG.children.find((c) => c.name === 'winGlow' && Math.abs(c.position.x - wl.x) < 0.6);
  const reveal = ctx.cache('ep01:reveal', () => { const P = new Parts(); const k = 'trim:#efeee9'; const [x0, x1, y0, y1] = hole, z0 = zFace, z1 = zFace - I.ROOM.wallT;
    I.rect(P, k, [0, 1, 0], [x0, x1], [y0, y0], [z1, z0], 1); I.rect(P, k, [0, -1, 0], [x0, x1], [y1, y1], [z1, z0], 1); I.rect(P, k, [1, 0, 0], [x0, x0], [y0, y1], [z1, z0], 1); I.rect(P, k, [-1, 0, 0], [x1, x1], [y0, y1], [z1, z0], 1);
    return persistTree(P.build(M, { name: 'windowReveal' })); });
  lotG.add(reveal.clone());
  const glassMat = new THREE.MeshStandardMaterial({ color: '#a8b0e8', transparent: true, opacity: 0.16, roughness: 0.05, metalness: 0.1, emissive: '#ffffff', emissiveMap: glassSheenTex(), emissiveIntensity: 0.05, depthWrite: false });
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(4, 5), glassMat); glass.position.set(wl.x, wl.y, zFace + 0.012); glass.name = 'theoGlass'; glass.renderOrder = 4; lotG.add(glass);
  // warm haze on the glass when the room is lit (keeps the approved 'lit window' read from the street; additive)
  const hazeMat = new THREE.MeshBasicMaterial({ map: I.ctex('glassHaze2', 128, 160, (g, W, H) => { const gr = g.createRadialGradient(W / 2, H * 0.35, 4, W / 2, H * 0.45, W * 0.75); gr.addColorStop(0, 'rgba(255,228,180,0.85)'); gr.addColorStop(0.6, 'rgba(255,196,130,0.55)'); gr.addColorStop(1, 'rgba(255,170,100,0.35)'); g.fillStyle = gr; g.fillRect(0, 0, W, H); }), color: new THREE.Color('#ffb070'), transparent: true, opacity: 0.0, blending: THREE.AdditiveBlending, depthWrite: false });
  const haze = new THREE.Mesh(new THREE.PlaneGeometry(4, 5), hazeMat); haze.position.set(wl.x, wl.y, zFace + 0.02); haze.renderOrder = 5; haze.name = 'theoHaze'; lotG.add(haze);
  const roomEra = o.theoRoom === false ? null : { era: E.room, lit: tod !== 'day' && tod !== 'dawn', curtains: undefined, ...(o.theoRoom || {}) };
  if (year > 0 && roomEra && !(o.theoRoom && o.theoRoom.era)) roomEra.era = 'later';
  let room = null; const roomAnch = {};
  if (roomEra) {
    room = I.bedroomRoom(ctx, { era: roomEra.era, curtains: roomEra.curtains, curtain: roomEra.curtain || (year > 0 ? Y.curtain : undefined) });
    room.position.set(wl.x, F, zFace - I.ROOM.wallT); lotG.add(room); const A = room.userData.anchors;
    const rw = (p) => r3(V3(p).add(room.position).add(lotPos).multiplyScalar(S));
    roomAnch.lamp = A.lamp ? rw(A.lamp) : null; roomAnch.nightlight = A.nightlight ? rw(A.nightlight) : null; roomAnch.windowWorld = rw([0, (hole[2] + hole[3]) / 2 - F, 0]); roomAnch.windowNormal = [0, 0, 1];
    roomAnch.sleeper = { head: rw(A.sleeper.head), body: rw(A.sleeper.body), yaw: A.sleeper.yaw, top: A.sleeper.top, bed: A.sleeper.bed }; if (A.clock) roomAnch.clock = rw(A.clock);
    roomAnch.views = {}; for (const [k, v] of Object.entries(A.views)) roomAnch.views[k] = { pos: rw(v.pos), target: rw(v.target), fov: v.fov };
    roomAnch.bounds = A.bounds; roomAnch.era = roomEra.era;
  } else { glassMat.color.set('#121528'); glassMat.opacity = 0.92; } // no room: plain dark glass
  // room glow lights (exterior shots): warm ceiling spill + Theo's nightlight; bedroomNight() switches them off
  const glowL = []; if (room && o.roomGlow !== false) {
    const gp = V3([wl.x + 1.5, F + 7.5, zFace - 6]).add(lotPos).multiplyScalar(S); const pl = new THREE.PointLight('#ffb878', 0, 0, 2); pl.position.copy(gp); pl.name = 'roomGlow'; xm.add(pl); glowL.push(pl);
    if (roomAnch.nightlight) { const nl = new THREE.PointLight('#ffc8e8', 0, 0, 2); nl.position.copy(V3(roomAnch.nightlight)); nl.name = 'nightlightGlow'; xm.add(nl); glowL.push(nl); }
  }
  const shadeOff = M('plastic:#e8e0cc'); const shadeOn = XM('tex:lampShade');
  const theo = {
    glass, haze, room, winGlow, lights: glowL, level: 0,
    setLevel(k) { this.level = k; const ext = this.interior ? 0 : 1; if (glowL[0]) glowL[0].intensity = 12.0 * k * ext; if (glowL[1]) glowL[1].intensity = 1.6 * k * ext; for (const l of glowL) l.visible = l.intensity > 0; // invisible lights cost nothing hazeMat.opacity = (o.haze ?? 0.85) * k * ext; if (winGlow) winGlow.visible = k > 0.05;
      if (room) room.traverse((m) => { if (m.name === 'lampShade') m.material = k > 0.05 ? shadeOn : shadeOff; if (m.name === 'projStars') m.visible = k > 0.05; });
      const w = root.userData.windows && root.userData.windows.find((x) => x.lot === lotId && Math.abs(x.pos[0] - winW.pos[0]) < 0.05 && x.face === 'front'); if (w) w.lit = k > 0.05; },
    // interior shots: the exterior room glow (warm fill + glass haze) is switched off; bedroomNight() lights the room
    setInterior(on = true) { this.interior = on; this.setLevel(this.level); },
    setGlass(mode = 'outside') { const G = { outside: ['#a8b0e8', 0.16, 0.05], inside: ['#1a1640', 0.42, 0.02], dark: ['#121528', 0.86, 0.06], day: ['#c8d4f0', 0.3, 0.08], photo: ['#d8e0f4', 0.12, 0.04] }[mode] || ['#a8b0e8', 0.16, 0.05]; glassMat.color.set(G[0]); glassMat.opacity = G[1]; glassMat.emissiveIntensity = G[2]; if (mode === 'inside') hazeMat.opacity = 0; },
  };
  ep.theo = theo; ep.room = roomAnch; ep.setTheoWindow = (k) => theo.setLevel(k);
  // ---- dressing in the lot frame (studs)
  const D = new Parts(); const extrasL = [];
  const bedL = toLot(bedSlot.pos); const bed = L.beds[0]; const bedLot = toLot(bed.pos); const bedLen = bed.len / S, bedDep = bed.dep / S;
  // brick edging in front of Grandpa's bed (dog-tooth, separate meshes: ep01.bricks)
  const bricks = []; if (o.bricks !== false) {
    const bg = new THREE.Group(); bg.name = 'brickEdging'; const geo = ctx.cache('ep01:brickGeo3', () => persistGeo(boxUV(0.7, 0.34, 0.3, 1.0, 0.03))); const bm = M('plaster:#c0643f');
    const n = 15, zb = bedLot.z + bedDep / 2 + 0.55; for (let i = 0; i < n; i++) { const b = new THREE.Mesh(geo, bm); b.position.set(bedLot.x - bedLen / 2 + 0.35 + (i * (bedLen - 0.7)) / (n - 1), 0.04, zb); b.rotation.set(0, 0, PI / 4 + (hash32('brick', i) % 7 - 3) * 0.02); b.name = 'brick' + i; b.castShadow = true; bg.add(b); bricks.push(b); }
    lotG.add(bg);
  }
  ep.bricks = bricks;
  // the KEEP OFF sign beside the gate, the agent board by the path (+ SOLD sticker)
  const gateL = toLot(L.gate); let signMesh = null, board = null, sticker = null;
  if (o.keepOff ?? E.keepOff) { D.push(trs([gateL.x + 7, 0, -2.0])); signMesh = P_.addPostSign(D, { lines: ['KEEP OFF', 'THE LAWN', 'AFTER DARK'] }); D.pop(); extrasL.push(signMesh); }
  if (o.board ?? E.board) { D.push(trs([gateL.x - 6.5, 0, -5.0])); board = P_.addAgentBoard(D, { header: 'FOR SALE', lines: ['3 BED · BIG GARDEN', 'COMES WITH ANCESTORS'] }); D.pop(); extrasL.push(board);
    if (o.sold != null) { sticker = soldSticker(board, { t0: o.sold }); ep.updates.push((t) => sticker.update(t)); } }
  ep.sign = signMesh; ep.board = board; ep.sticker = sticker;
  // a leafy tree in the front-right corner that grows with the years (era / year scale)
  const treeS = o.tree ?? (year > 0 ? Y.tree : E.tree);
  if (treeS > 0) { const tree = ctx.cache('ep01:heroTree', () => { const P = new Parts(); P_.addLeafyTree(P, { height: 21, seed: 5 }); return persistTree(P.build(M, { name: 'heroTree', cast: true, receive: true })); }).clone(); tree.position.set(13.2, 0, -5.6); tree.scale.setScalar(treeS); tree.rotation.y = 0.6; lotG.add(tree); }
  // 2010s: the hero's toys on the porch (ball, toy truck, bucket and spade)
  if (o.toys ?? E.toys) { const py = F; D.add('plastic:#e8402a', new THREE.SphereGeometry(0.42, 14, 10), [2.6, py + 0.42, -17.6]); D.box('plastic:#f2c230', 1.2, 0.5, 0.7, [-2.8, py + 0.35, -18.2], [0, 0.4, 0], { bevel: 0.08 }); D.box('plastic:#f2c230', 0.6, 0.45, 0.65, [-3.1, py + 0.8, -18.3], [0, 0.4, 0], { bevel: 0.06 }); for (const [dx, dz] of [[-0.4, -0.3], [0.4, -0.3], [-0.4, 0.3], [0.4, 0.3]]) D.cyl('black', 0.13, 0.13, 0.12, 10, [-2.8 + dx, py + 0.13, -18.2 + dz], [PI / 2, 0, 0.4]); D.cyl('plastic:#2f8ad8', 0.32, 0.25, 0.55, 14, [3.6, py + 0.28, -18.6]); }
  // Grandpa's spot: soil ring / hole / sticker
  const spot = new THREE.Group(); spot.name = 'grandpaSpot'; spot.position.set(bedL.x, 0.355, bedL.z); lotG.add(spot);
  const bedKind = o.bed ?? E.bed;
  if (bedKind === 'empty' || bedKind === 'plastic' || bedKind === 'grandpaBack') spot.add(decalDisc('soilRing' + (bedKind === 'grandpaBack' ? 'Fresh' : ''), soilTex(bedKind === 'grandpaBack' ? 'ringFresh' : 'ring'), 0.9));
  if (bedKind === 'hole') { spot.add(decalDisc('soilHole', soilTex('hole'), 0.85)); const C = new Parts(); for (const g of crumbsGeo(0.62, 46, 3)) C.add('dirt', g); spot.add(persistTree(C.build(M, { name: 'crumbs' })));
    const st = new THREE.Mesh(new THREE.PlaneGeometry(0.5, 0.38), I.decalMat('price:$4.99', priceStickerTex('$4.99'), { roughness: 0.7, transparent: true })); st.rotation.set(-PI / 2 + 0.08, 0, 0.5); st.position.set(0.55, 0.03, 0.62); st.name = 'priceSticker'; spot.add(persistTree(st)); }
  // ---- gnomes (metres)
  const gn = ep.gnomes; const addShadow = (pos, r = 0.24, op = 0.4) => xm.add(sets.contactShadow(ctx, { pos, radius: r, opacity: op }));
  if (bedKind === 'grandpa' || bedKind === 'grandpaBack') { const g = K.makeGnome('grandpa', { lantern: o.lantern ?? 0, wear: 0.12, age: year > 0 ? clamp01(year / 60) : 0, ...(o.grandpa || {}) }); sets.place(g, bedSlot); xm.add(g); addShadow(bedSlot.pos, 0.24, 0.45); gn.grandpa = g; }
  if (bedKind === 'plastic') { const g = K.makePlasticGnome({ finish: 'glossy' }); sets.place(g, bedSlot); g.rotation.y += 0.25; xm.add(g); addShadow(bedSlot.pos, 0.24, 0.4); gn.plastic = g; }
  const famSlots = o.gnomes === false ? [] : Array.isArray(o.gnomes) ? o.gnomes : E.gnomes;
  famSlots.forEach((n) => { const k = FAMILY_SLOTS.indexOf(n); const s0 = sets.slot(set, lotId + '.' + n); if (!s0) return; const s = { ...s0, pos: s0.pos.slice() };
    if (n === 'bedFront0' && o.shiftBedFront0 !== false) s.pos[0] += 1.5 * S;
    const f = K.makeFamilyGnome(POINTED[(2 + (k < 0 ? 0 : k)) % POINTED.length], { lantern: o.lanterns ?? 0, lod: 'mid', age: year > 0 ? clamp01(year / 80) : 0 }); sets.place(f, s); xm.add(f); addShadow(s.pos, 0.26, 0.4); gn.family[n] = f; });
  // ---- era: gate colour (1960s), repaint by year, tulips + other curtains per year
  const gateLeaf = lotG.getObjectByName('gate_' + lotId); ep.gate = gateLeaf;
  if (E.gate && gateLeaf) gateLeaf.traverse((m) => { if (m.isMesh) m.material = M('trim:' + E.gate); });
  if (gateLeaf && o.gate) gateLeaf.rotation.y = o.gate; // open angle (rad, 0..1.9): the leaf swings into the garden
  if (year > 0) {
    for (const m of lotG.children) if (m.isMesh) {
      if (m.name.startsWith('siding:')) m.material = M('siding:' + Y.siding);
      else if (m.name.startsWith('door:')) m.material = M('door:' + Y.door); else if (m.name.startsWith('doorEdge:')) m.material = M('doorEdge:' + Y.door);
      else if (m.name.startsWith('win:')) { const p = m.name.split(':'); p[2] = Y.curtain; m.material = M(p.join(':')); }
      else if (m.name.startsWith('tulip:') && m.position.y === 0) { const i = (hash32(m.name) % 97) % Y.tulips.length; m.material = M('tulip:' + Y.tulips[i]); }
    }
  }
  // ---- next door (lot A2): plastic gnomes facing the street, the REX kennel, hose reel, the red lead into THE HOLE
  if (o.nextDoor !== false) Object.assign(ep, dressNextDoor(ctx, set, xm, { ...(typeof o.nextDoor === 'object' ? o.nextDoor : {}) }));
  // ---- merge the lot dressing
  const dg = persistTree(D.build(M, { name: 'ep01Dressing', cast: true, receive: true })); extrasL.forEach((e) => dg.add(persistTree(e))); lotG.add(dg);
  // ---- truck at the kerb
  if (o.truck) { const tr = movingTruck(ctx, { mode: o.truck, ...(o.truckOpts || {}) }); parkTruck(tr, set, lotId, o.truckOpts || {}); xm.add(tr); ep.truck = tr; ep.updates.push((t) => tr.ep01.update(t)); }
  // ---- userData (street + ep01 anchors), views
  root.userData = JSON.parse(JSON.stringify(set.userData)); root.userData.lots = root.userData.lots.map((l) => ({ ...l }));
  ep.spots = heroSpots(set, lotId, { bedSlot, winW, wl, lotPos, bricks, board, ep });
  ep.views = { ...heroViews(ep.spots, ep), ...(roomAnch.views ? Object.fromEntries(Object.entries(roomAnch.views).map(([k, v]) => ['room_' + k, v])) : {}), ...(ep.nextDoorViews || {}) };
  root.userData.ep01 = { spots: ep.spots, views: ep.views, room: roomAnch };
  ep.update = (t) => { for (const f of ep.updates) f(t); };
  ep.light = (ctx2, opts = {}) => heroLight(ctx2, root, opts);
  root.ep01 = ep;
  // default light state of Theo's window by time of day
  theo.setLevel(roomEra && roomEra.lit ? (o.roomLevel ?? 1) : 0); theo.setGlass(tod === 'day' || tod === 'dawn' ? 'day' : roomEra && roomEra.lit ? 'outside' : 'dark');
  return root;
}
// Named points (metres, world, root at the origin).
function heroSpots(set, lotId, { bedSlot, winW, wl, lotPos, bricks, board, ep }) {
  const Lt = sets.lot(set, lotId); const W = (p) => r3(V3(p).add(lotPos).multiplyScalar(S));
  const sp = { bed0: bedSlot.pos, bed0Yaw: bedSlot.yaw, theoWindow: r3(V3(winW.pos).add(new THREE.Vector3(0, 0, -0.1 * S))), theoSill: W([wl.x, wl.y - 2.5, wl.z + 0.2]), gate: Lt.gate, door: Lt.door, steps: Lt.steps, houseFront: Lt.houseFront };
  if (bricks.length) { const b = bricks[Math.floor(bricks.length / 2)].position; sp.bricks = W([b.x, b.y, b.z]); }
  if (board) { const bp = board.getWorldPosition(new THREE.Vector3()); void bp; sp.board = W([board.position.x, board.position.y, board.position.z]); }
  if (ep.truck) { const tb = ep.truck.ep01.backCenter(0); sp.truckBack = r3(tb); sp.ramp = r3(tb.clone().add(new THREE.Vector3(4 * S, -1.6 * S, 0))); }
  for (const n of ['bedFront0', 'bedFront1', 'lawn0', 'lawn1', 'lawn2', 'lawn3', 'porchSteps', 'gateIn', 'gateOut', 'windowLook', 'lawnMid']) { const s = sets.slot(set, lotId + '.' + n); if (s) sp[n] = s.pos; }
  return sp;
}
// Camera anchors for the hero lot (metres): { pos, target, fov } usable directly in ctx.camera.set(...).
// yaw: degrees, 0 = camera on the street side of the subject looking at the house (-Z), + = toward +X (the path).
function orbitView(subject, { dist, height, yaw = 0, fov = 70, aim = null }) {
  const c = V3(subject); const a = yaw * DEG; const pos = new THREE.Vector3(c.x + Math.sin(a) * dist * S, height * S, c.z + Math.cos(a) * dist * S); const tgt = aim ? V3(aim) : c;
  return { pos: r3(pos), target: r3(tgt), fov };
}
function heroViews(sp, ep) {
  const up = (p, dy, dx = 0, dz = 0) => [p[0] + dx * S, p[1] + dy * S, p[2] + dz * S];
  const B = sp.bed0, Wn = sp.theoWindow; const v = {};
  if (sp.board) v.boardMS = orbitView(sp.board, { dist: 7.2, height: 5.6, yaw: 10, fov: 60, aim: up(sp.board, -0.2, 0.2) });          // s10 (camera just outside the fence, above the pickets)
  v.tapHat = orbitView(B, { dist: 7, height: 3.0, yaw: 35, fov: 70, aim: up(B, 2.2, 0.4, 0.6) });                                      // s16 (window in the top third)
  v.emptySpot = { pos: r3(V3(up(B, 3.2, 0, 4.1))), target: r3(V3(up(B, 0.15, 0, 0.2))), fov: 60 };                                      // s27 (pitch -38: ring centred, sill across the top)
  v.runOut = { pos: r3(V3(up(sp.steps, 0.5, 0.4, 9.5))), target: r3(V3(up(sp.door, 2.6))), fov: 70 };                                   // s28 ground level
  // NB: the porch column stands 2.6 studs right of this window: keep outside views of Theo's window at yaw <= 0 (camera
  // on the far side from the porch), or it fills the right of the frame.
  v.theoWindowOut = orbitView(up(Wn, -1.0), { dist: 8.0, height: 4.6, yaw: -18, fov: 70, aim: up(Wn, -0.7) });                       // s45 / s68 / s69
  v.theoWindowHigh = orbitView(up(Wn, -1.5), { dist: 6.5, height: 7.0, yaw: -10, fov: 70, aim: up(Wn, -1.4) });
  v.profileWS = { pos: r3(V3(up(B, 4.5, 18, 5))), target: r3(V3(up(B, 2.6, 0, 5.5))), fov: 65 };                                         // s46
  v.bedKneel = orbitView(B, { dist: 7, height: 3.0, yaw: -25, fov: 70, aim: up(B, 2.0, 0.3, 0.6) });                                   // s50
  v.bedLow = orbitView(B, { dist: 2.5, height: 0.8, yaw: -25, fov: 70, aim: up(B, 0.7) });                                             // s51
  v.moundsLow = orbitView(B, { dist: 10, height: 0.6, yaw: 0, fov: 70, aim: up(B, 2.4, 0, -1) });                                      // s52
  v.tulipsCU = orbitView(up(B, 0, -1.6), { dist: 1.8, height: 0.6, yaw: -20, fov: 60, aim: up(B, 0.6, -1.6) });                        // s53
  if (sp.bricks) v.bricksCU = orbitView(sp.bricks, { dist: 2.0, height: 0.7, yaw: 15, fov: 60, aim: up(sp.bricks, 0.3) });              // s54
  v.highWS = orbitView(B, { dist: 14, height: 10, yaw: -30, fov: 65, aim: up(B, 0, 0, 3) });                                            // s56
  v.standGuard = { pos: r3(V3(up(B, 4.7, -5.5, -0.4))), target: r3(V3(up(B, 3.0, 1.2, 7))), fov: 70 };                                 // s57 (truck behind him)
  v.kneelLow = orbitView(B, { dist: 7, height: 2.2, yaw: -30, fov: 70, aim: up(B, 2.0, 0, 0.8) });                                     // s73
  v.quietWide = orbitView(B, { dist: 24, height: 7.0, yaw: -10, fov: 60, aim: up(B, 3.0) });                                            // s81
  v.dawnLow = orbitView(sp.steps, { dist: 12, height: 0.8, yaw: 15, fov: 70, aim: up(sp.door, 3.0, -2) });                              // s82
  v.lapTop = { pos: r3(V3(up(sp.gate, 34, -1.5, -10.5))), target: r3(V3(up(sp.gate, 0, -1.5, -10.52))), fov: 45 };                        // s22 / s63 top-down (house at the top)
  v.streetWS = { pos: r3(V3(up(sp.gate, 5.5, -1, 30))), target: r3(V3(up(sp.gate, 5.2, -6, -14))), fov: 60 };                             // s25 (truck back in the left third)
  v.fromTruckTele = { pos: r3(V3(up(sp.gate, 4.0, -9, 14))), target: r3(V3(up(B, 1.2))), fov: 25 };                                     // s89
  v.photo = { pos: r3(V3(up(B, 4.6, 1.4, 12.5))), target: r3(V3(up(B, 3.1, 1.5, 0))), fov: 45 };                                         // the yearly photo framing
  v.gnomeCU = orbitView(B, { dist: 1.6, height: 0.9, yaw: -20, fov: 70, aim: up(B, 1.7) });                                            // s18-like
  if (sp.truckBack) { v.gateTruck = { pos: r3(V3(up(sp.gate, 0.7, 0.6, -1.8))), target: r3(V3(sp.truckBack).add(new THREE.Vector3(0, 0.6, 0))), fov: 70 }; v.ramp = { pos: r3(V3(sp.ramp).add(new THREE.Vector3(0, 6.5 * S, 0.01))), target: sp.ramp, fov: 50 }; } // s29 / s49
  return v;
}

// ------------------------------------------------------------------ NEXT DOOR (lot A2)
// Adds to the street clone `set`: in the A2 lot frame (studs) the REX kennel, hose reel, the lead and THE HOLE; in metres
// (group xm) the plastic gnomes facing the street. Returns { nextDoor: { gnomes, lead, hole, kennel, dogSpot, update } }.
function leadTex() { return I.ctex('leadRed', 64, 16, (g, W, H) => { g.fillStyle = '#c8241c'; g.fillRect(0, 0, W, H); for (let x = 0; x < W; x += 8) { g.fillStyle = 'rgba(0,0,0,0.18)'; g.fillRect(x, 0, 3, H); } }, { wrap: true }); }
export function dressNextDoor(ctx, set, xm, o = {}) {
  const id = o.lot || 'A2'; const lotG = set.getObjectByName('lot_' + id); const lotPos = lotG.position.clone(); const toW = (p) => V3(p).add(lotPos).multiplyScalar(S);
  const P = new Parts();
  // kennel 'REX' with a name board, a bowl, a chewed ball
  const kx = 10.8, kz = -12.6, ka = -0.35; P.push(trs([kx, 0, kz], [0, ka, 0])); P_.addKennel(P, {}); P.box('trim:#f1efe9', 1.6, 0.6, 0.08, [0, 2.95, 1.84]); P.add('tex:rexBoard', new THREE.PlaneGeometry(1.45, 0.48), [0, 2.95, 1.885]);
  P.cyl('metal:#b8bcc8', 0.42, 0.32, 0.25, 16, [1.9, 0.13, 1.6]); P.add('plastic:#2f8ad8', new THREE.SphereGeometry(0.3, 12, 8), [-1.8, 0.3, 2.4]); P.pop();
  I.decalMat('rexBoard', signTex(['REX'], '', { w: 256, h: 96 }), { roughness: 0.6 });
  P.push(trs([15.6, 0, -17.2], [0, -PI / 2.4, 0])); P_.addHoseReel(P); P.pop();
  // the lead: from the kennel's ring (front-left corner) across the lawn into the hole (tube on a Catmull curve)
  const ring = new THREE.Vector3(-1.2, 0.35, 1.85).applyAxisAngle(new THREE.Vector3(0, 1, 0), ka).add(new THREE.Vector3(kx, 0, kz));
  const holeAt = new THREE.Vector3(o.holeX ?? 8.4, 0, o.holeZ ?? -5.4);
  const pts = [ring, ring.clone().add(new THREE.Vector3(-0.2, -0.25, 0.6)), new THREE.Vector3(9.9, 0.07, -9.8), new THREE.Vector3(8.9, 0.07, -8.0), new THREE.Vector3(9.2, 0.07, -6.6), holeAt.clone().add(new THREE.Vector3(0.1, 0.06, -0.42)), holeAt.clone().add(new THREE.Vector3(0, -0.6, -0.1))];
  const curve = new THREE.CatmullRomCurve3(pts, false, 'catmullrom', 0.4);
  const leadG = ctx.cache('ep01:leadGeo:' + id, () => persistGeo(new THREE.TubeGeometry(curve, 120, 0.075, 8, false)));
  const leadM = I.decalMat('lead', leadTex(), { roughness: 0.45 }); const lead = new THREE.Mesh(leadG, leadM); lead.name = 'redLead'; lead.castShadow = true;
  const leadGrp = new THREE.Group(); leadGrp.name = 'leadGroup'; leadGrp.add(lead); lotG.add(leadGrp);
  P.box('brass', 0.12, 0.12, 0.3, [ring.x, ring.y, ring.z]); // the ring on the kennel
  // THE HOLE: a neat round hole 0.9 stud across, black-brown interior, a lip of crumbs
  const hole = new THREE.Group(); hole.name = 'theHole'; hole.position.copy(holeAt); hole.add(decalDisc('neatHole', soilTex('hole'), 0.62, { y: 0.012 }));
  const C = new Parts(); for (const g of crumbsGeo(0.47, 30, 9, 0.08)) C.add('dirt', g); hole.add(persistTree(C.build(M, { name: 'crumbs' }))); lotG.add(hole);
  const grp = persistTree(P.build(XM, { name: 'nextDoorDressing', cast: true, receive: true })); lotG.add(grp);
  // plastic gnomes in a row facing the STREET (decorations), metres
  const gnomes = []; const n = o.plastics ?? 3; for (let i = 0; i < n; i++) { const g = K.makePlasticGnome({ finish: 'glossy' }); const p = toW([3.9 + i * 1.7, 0, -8.6 - (i === 1 ? 0.25 : 0)]); g.position.copy(p); g.rotation.y = (i - 1) * 0.08; xm.add(g); xm.add(sets.contactShadow(ctx, { pos: p.toArray(), radius: 0.24, opacity: 0.35 })); gnomes.push(g); }
  const dogSpot = r3(toW([2.4, 0, -7.4])); const holeW = r3(toW([holeAt.x, 0, holeAt.z])); const kennelW = r3(toW([kx, 0, kz])); const ringW = r3(toW(ring.toArray()));
  const tugDir = holeAt.clone().sub(new THREE.Vector3(9.2, 0, -6.6)).normalize();
  const nd = { gnomes, lead: leadGrp, hole, kennel: kennelW, dogSpot, holeW, ringW,
    // s13: the lead gives one small tug toward the hole at t0 (0.1 stud, spring)
    tug(t, t0) { const u = t - t0; const d = u < 0 ? 0 : 0.1 * (1 - Math.exp(-u * 14) * Math.cos(u * 30)); leadGrp.position.copy(tugDir).multiplyScalar(d); } };
  const up = (p, dy, dx = 0, dz = 0) => [p[0] + dx * S, p[1] + dy * S, p[2] + dz * S]; const row = r3(toW([5.6, 0, -8.6]));
  const views = {
    nextDoorMS: orbitView(row, { dist: 8.5, height: 4.0, yaw: -12, fov: 65, aim: up(row, 1.3, 1.0, -1.2) }),                               // s12
    kennelTop: { pos: r3(V3(up(ringW, 9, 0, 0.01))), target: up(ringW, 0), fov: 50 },                                                      // s13 start (kennel at the top)
    holeTop: { pos: r3(V3(up(holeW, 9, 0, 0.01))), target: up(holeW, 0), fov: 50 },                                                       // s13 end (hole centred)
    nextDoorNight: orbitView(row, { dist: 8.0, height: 4.0, yaw: -15, fov: 65, aim: up(row, 1.0, 1.5, -1.5) }),                           // s41
  };
  return { nextDoor: nd, nextDoorViews: views };
}

// ------------------------------------------------------------------ light helper for heroLot
// heroLight(ctx, root, { tod, ...preset opts }) -> rig. Night: nightLawn (window practical included); day: sets.day
// (shot quality { shadows: 'pcfsoft' }); dusk: sets.dusk (windows lit); dawn: sets.dawn. Theo's room glow follows tod.
export function heroLight(ctx, root, o = {}) {
  const ep = root.ep01; const tod = o.tod || ep.tod; const { tod: _t, ...rest } = o; let rig;
  // front-lit defaults for our side of the street (side A houses face +Z): the kit's day sun (az -40) back-lights every
  // front lawn; exposures calibrated with stats.py on the QA stills (day / dawn / dusk targets of VISUAL_BIBLE section 5)
  const po = (e) => ({ ...(rest.postOpts || {}), exposure: (rest.postOpts && rest.postOpts.exposure) ?? e });
  if (tod === 'day') rig = sets.day(ctx, { set: root, ...rest, sun: { az: 160, el: 45, ...(rest.sun || {}) }, postOpts: po(1.15) });
  else if (tod === 'dawn') rig = sets.dawn(ctx, { set: root, ...rest, sun: { az: 150, el: 12, ...(rest.sun || {}) }, postOpts: po(1.7) });
  else if (tod === 'dusk') { rig = sets.dusk(ctx, { set: root, ...rest, postOpts: po(1.65) }); }
  else rig = sets.nightLawn(ctx, { set: root, ...rest });
  if ((tod === 'day' || tod === 'dawn') && ep.theo.level > 0 && o.keepRoom !== true) { ep.theo.setLevel(0); ep.theo.setGlass('day'); }
  return rig;
}


// ------------------------------------------------------------------ OUR STREET (every lawn's gnome and lantern)
// ep01Street(ctx, o) -> root (metres): sets.buildStreet(ctx, { seed: 'ep01', lotsPerSide: 6, hero: { side: 'A', index: 3 } })
// (the street of the approved s01) + one or two gnomes per lawn facing their houses, placed exactly like part1's
// streetGnomes() (same seeds: the s01 layout), Grandpa in the hero bed; `heroLike: true` (default) restyles our house
// (A3) like heroLot's bungalow (mustard siding, purple curtains, door 14), which s01 never shows. Lanterns: `lanterns`
// level for all, and ep01.gnomes = [{ g, lot, slot, pos, dist }] (sorted by distance from our gate) for the cascade.
// o: { tod, lanterns: 0, heroLike: true, truck: false | mode, truckOpts, nextDoorLot: 'A4', skip: [] }
export const HERO_HOUSE = { type: 'bungalow', width: 26, wall: 'siding', wallColor: '#c8a557', roofColor: '#2c3038', doorColor: '#7a2a20', shutterColor: null, roof: 'side', porch: 'center', porchWidth: 11, panes: 4, curtain: '#8a5aa0', number: '14', chimney: true, lit: [1, 1, 0, 1], foundation: 1.0, sill: 1.6, offsetX: 0 };
const STREET_POINTED = [0, 1, 2, 3, 4, 5, 7];
export function ep01Street(ctx, o = {}) {
  const heroIdx = 3; const heroId = 'A' + heroIdx; const nd = o.nextDoorLot || 'A' + (heroIdx + 1);
  const set = sets.buildStreet(ctx, { seed: 'ep01', lotsPerSide: 6, hero: { side: 'A', index: heroIdx, ...(o.heroLike === false ? {} : { house: HERO_HOUSE, lot: { extras: ['hoseReel'], path: 'stones' } }) } });
  const root = new THREE.Group(); root.name = 'ep01Street'; root.add(set); const xm = new THREE.Group(); root.add(xm);
  const r = makeRng(hash32('ep01t5', 'streetGnomes2')); let k = 0; const hero = set.userData.lots.find((l) => l.id === heroId); const list = [];
  for (const l of set.userData.lots) {
    const dist = Math.abs(l.index - hero.index); const lod = l.side === 'A' && dist <= 1 ? 'mid' : 'low';
    const names = l.side === 'A' ? (l.id === heroId ? ['bed0', 'lawn2', 'lawn3'] : ['bed0', 'lawn0', 'lawn3']) : ['bed0', 'lawn2'];
    for (const n of names) {
      const s = sets.slot(set, l.id + '.' + n); if (!s || (o.skip || []).includes(s.name)) continue;
      const plastic = l.id === nd && o.plasticNextDoor !== false;
      const g = l.id === heroId && n === 'bed0' ? K.makeGnome('grandpa', { lantern: o.lanterns ?? 0, lod: 'mid' }) : plastic ? K.makePlasticGnome({ finish: 'glossy' }) : K.makeFamilyGnome(STREET_POINTED[k % STREET_POINTED.length], { lod, lantern: o.lanterns ?? 0 });
      if (!(l.id === heroId && n === 'bed0') && !plastic) k++; else if (plastic) k++;
      sets.place(g, s); const jit = (r() - 0.5) * 0.1; g.rotation.y += jit; if (plastic) g.rotation.y = s.yaw + Math.PI; // next door's face the street
      xm.add(g); list.push({ g, lot: l.id, slot: s.name, pos: s.pos, plastic });
    }
  }
  const gate = V3(hero.gate); list.forEach((e) => { e.dist = V3(e.pos).distanceTo(gate); }); list.sort((a, b) => a.dist - b.dist);
  const ep = { set, gnomes: list, heroId, updates: [], grandpa: list.find((e) => e.lot === heroId && e.slot.endsWith('.bed0'))?.g };
  if (o.truck) { const tr = movingTruck(ctx, { mode: o.truck, ...(o.truckOpts || {}) }); parkTruck(tr, set, heroId, o.truckOpts || {}); xm.add(tr); ep.truck = tr; ep.updates.push((t) => tr.ep01.update(t)); }
  root.userData = JSON.parse(JSON.stringify(set.userData)); const up = (p, dy, dx = 0, dz = 0) => [p[0] + dx * S, p[1] + dy * S, p[2] + dz * S];
  ep.views = { ...set.userData.views,
    aerial: { pos: up(hero.gate, 46, 30, 30), target: up(hero.gate, 0, -6, -10), fov: 55 },                          // s43: our street from high above, rings on every lawn
    alongLawns: { pos: up(hero.gate, 6.5, 22, 4), target: up(hero.gate, 2.0, -26, -9), fov: 60 },                    // s35 / s40: along the front lawns, gnome backs
  };
  root.userData.ep01 = { views: ep.views }; ep.update = (t) => { for (const f of ep.updates) f(t); }; root.ep01 = ep;
  if (o.tod === 'day' || o.tod === 'dawn') sets.setWindows(set, 'off');
  return root;
}

// ------------------------------------------------------------------ BACK GARDEN (epilogue, dusk -> blue hour -> night)
// backGarden(ctx, { tod: 'dusk' | 'blueHour' | 'night', windowLit: true, table: true }) -> root (metres) with
// userData.views / anchors and ep01 { releaseDandelion, window, update, light(ctx) }.
// Layout (studs): the back of a two-storey sage house facing +Z (wall at z = 0), the granddaughter's ground-floor
// window (pink-warm, curtains open, a star nightlight) at x = -8.7; the striped deck chair facing that window at z = 10;
// the garden bench at (6, 0, 9) facing the house; the teak garden table at (13, 0, 8.6) beside it; lawn with dandelion
// clocks, a flowerbed along the house, a low white fence at z = 30 and pines behind.
function girlRoomTex() {
  return I.ctex('girlRoom', 128, 160, (g, W, H) => {
    const gr = g.createLinearGradient(0, 0, 0, H); gr.addColorStop(0, '#ffe8f2'); gr.addColorStop(0.5, '#f7b8d4'); gr.addColorStop(1, '#c86a98'); g.fillStyle = gr; g.fillRect(0, 0, W, H);
    const rg = g.createRadialGradient(W * 0.68, H * 0.62, 2, W * 0.68, H * 0.62, W * 0.55); rg.addColorStop(0, 'rgba(255,248,220,0.95)'); rg.addColorStop(1, 'rgba(255,248,220,0)'); g.fillStyle = rg; g.fillRect(0, 0, W, H);
    g.fillStyle = '#fff4c0'; g.save(); g.translate(W * 0.68, H * 0.62); g.beginPath(); for (let k = 0; k < 10; k++) { const r = k % 2 ? 4 : 9; const a = (k / 10) * PI * 2 - PI / 2; g.lineTo(Math.cos(a) * r, Math.sin(a) * r); } g.fill(); g.restore();
    g.fillStyle = 'rgba(140,60,110,0.35)'; g.fillRect(W * 0.08, H * 0.7, W * 0.5, H * 0.3); g.fillStyle = 'rgba(255,255,255,0.5)'; g.fillRect(W * 0.1, H * 0.66, W * 0.18, H * 0.06);
    for (let k = 0; k < 12; k++) { g.fillStyle = 'rgba(255,255,220,0.8)'; g.fillRect(8 + ((k * 37) % (W - 16)), 10 + ((k * 23) % 50), 2, 2); }
    for (const s of [0, 1]) { const x0 = s ? W * 0.84 : 0; for (let x = 0; x < W * 0.16; x++) { const f = 0.75 + 0.25 * Math.sin((x / (W * 0.16)) * PI * 4 + s); g.fillStyle = `rgb(${Math.round(240 * f)},${Math.round(160 * f)},${Math.round(200 * f)})`; g.fillRect(x0 + x, 0, 1, H); } }
    g.fillStyle = '#c8508a'; g.fillRect(0, 0, W, 6);
  });
}
function addBench(P) { // slatted garden bench (teak), seat top 1.5, faces +Z, 6 wide
  const w = 'wood:#8a5a32', W = 6.4;
  for (let i = 0; i < 4; i++) P.box(w, W, 0.14, 0.42, [0, 1.45, -0.75 + i * 0.5], null, { bevel: 0.03 });
  P.push(trs([0, 1.5, -1.05], [-0.22, 0, 0])); for (let i = 0; i < 3; i++) P.box(w, W, 0.38, 0.12, [0, 0.55 + i * 0.6, 0], null, { bevel: 0.03 }); P.pop();
  for (const s of [-1, 1]) { const x = s * (W / 2 - 0.25); P.box(w, 0.3, 1.4, 0.3, [x, 0.7, 0.7]); P.box(w, 0.3, 3.4, 0.3, [x, 1.7, -1.1], [-0.22, 0, 0]); P.box(w, 0.32, 0.18, 2.1, [x, 2.45, -0.1]); P.box(w, 0.25, 0.9, 0.25, [x, 1.95, 0.75]); P.box(w, 0.25, 0.25, 1.9, [x, 0.4, -0.15]); }
  return { seats: [[-1.6, 1.5, -0.1], [1.6, 1.5, -0.1]] };
}
function addGardenTable(P) { // slatted teak top 8 x 5, roughness 0.5; a mug and reading glasses on it. Origin floor, top at y 2.6
  const w = 'wood:#9a6232'; for (let i = 0; i < 7; i++) P.box(w, 8, 0.16, 0.66, [0, 2.52, -2.1 + i * 0.7], null, { bevel: 0.03 });
  for (const [x, z] of [[-3.5, -2.0], [3.5, -2.0], [-3.5, 2.0], [3.5, 2.0]]) P.box(w, 0.32, 2.45, 0.32, [x, 1.22, z]); for (const z of [-2.0, 2.0]) P.box(w, 7.2, 0.25, 0.2, [0, 2.25, z]); for (const x of [-3.5, 3.5]) P.box(w, 0.2, 0.25, 4.0, [x, 2.25, 0]);
  P.cyl('plastic:#d9a52c', 0.3, 0.27, 0.62, 16, [2.6, 2.91, 1.2]); P.add('plastic:#d9a52c', new THREE.TorusGeometry(0.17, 0.05, 6, 12), [2.92, 2.92, 1.2], [0, 0, 0]); P.cyl('plastic:#3a2010', 0.27, 0.27, 0.03, 14, [2.6, 3.2, 1.2]);
  const gk = 'metal:#c9a04a'; for (const s of [-1, 1]) P.add(gk, new THREE.TorusGeometry(0.2, 0.03, 6, 18), [3.0 + s * 0.24, 2.63, -1.0], [-PI / 2, 0, 0]); P.bar(gk, [2.96, 2.63, -1.0], [3.04, 2.63, -1.0], 0.04, 0.03); for (const s of [-1, 1]) P.bar(gk, [3.0 + s * 0.44, 2.63, -1.0], [3.0 + s * 0.5, 2.63, -2.0], 0.03, 0.03);
  return { top: 2.6, pile: [-0.8, 2.61, 0.1] };
}
export function backGarden(ctx, o = {}) {
  const tod = o.tod || 'dusk'; const key = 'ep01:backGarden';
  const tpl = ctx.cache(key, () => {
    const root = new THREE.Group(); root.name = 'backGarden'; root.scale.setScalar(S); const P = new Parts(); const r = makeRng(hash32('backGarden'));
    P.box('lawn', 220, 0.5, 200, [0, -0.25, 40]);
    // the house (back wall faces +Z): two-storey, sage siding, a back door with a hood, the girl's window lit pink
    const Hh = addHouse(P, { type: 'twoStorey', width: 30, depth: 22, wall: 'siding', wallColor: '#9fae8c', roofColor: '#3d3330', doorColor: '#2a4a3a', shutterColor: '#2f3a30', porch: 'none', doorX: 5.5, lit: [1, 0, 0, 1, 0, 0, 0, 0, 0], pinkWindow: 0, tone: 'warm', curtain: '#f0a0c8', winIntensity: 2.0, number: '7', chimney: true, seed: 31, windowXs: [-8.7, 12.5] });
    // flowerbed along the house, pots by the door, a bird bath, a hose
    P.push(trs([-8.7, 0, 2.0])); P_.addFlowerbed(P, { length: 9, depth: 2.6, colors: ['#f07ab0', '#f2c230', '#f4eee8', '#d8283a'], density: 2.4, seed: 41, gaps: [] }); P.pop();
    for (const [x, s] of [[2.6, 1], [8.6, 2]]) { P.push(trs([x, 0, 2.2])); P_.addPotPlant(P, { seed: s, blossom: s === 1 ? '#e070c0' : null }); P.pop(); }
    P.push(trs([-17, 0, 14])); P.cyl('stone:#b8b0a4', 0.35, 0.5, 2.6, 12, [0, 1.3, 0]); P.cyl('stone:#b8b0a4', 1.4, 0.9, 0.5, 18, [0, 2.75, 0]); P.cyl('emissive:#a8c8f0:0.4', 1.2, 1.2, 0.05, 18, [0, 2.96, 0]); P.pop();
    // dandelions (clocks + yellow) in the lawn, not near the chair's release dandelion
    for (let i = 0; i < 22; i++) { const x = -20 + r() * 44, z = 4 + r() * 22; if (Math.hypot(x + 8.7, z - 10) < 2.5 || Math.hypot(x - 6, z - 9) < 4 || Math.hypot(x - 13, z - 8.6) < 5) continue; P.push(trs([x, 0, z])); P_.addDandelion(P, { height: 0.9 + r() * 0.5, puff: r() < 0.6, seed: i + 3 }); P.pop(); }
    for (let i = 0; i < 70; i++) { const x = -26 + r() * 52, z = 3 + r() * 26; P_.addDaisy(P, x, z, { r, color: r() < 0.85 ? '#f4f0ea' : '#f2c230' }); }
    for (let i = 0; i < 3; i++) P_.addDirtPatch(P, -14 + i * 13 + r() * 4, 16 + r() * 8, { size: 2 + r() * 2, seed: i + 2, rot: r() * PI });
    // low white fence (3 high) at z = 30 with a gate, pines behind, a shed at the left back
    P.push(trs([0, 0, 30])); P_.addPicketFence(P, { length: 80, height: 3.0 }); P.pop();
    for (let i = 0; i < 16; i++) { const x = -60 + i * 8 + r() * 4; const low = Math.abs(x + 8.7) < 18; P.push(trs([x, 0, (low ? 50 : 40) + r() * 20])); P_.addPine(P, { height: low ? 13 + r() * 5 : 22 + r() * 12, seed: 50 + i }); P.pop(); } // lower behind the deck chair: the moon rises over them (s97)
    P.push(trs([-22, 0, 20], [0, 0.4, 0])); P.box('wood:#6a4a3a', 7, 6, 6, [0, 3, 0]); P.box('shingle:#3d3330', 8, 0.4, 7, [0, 6.3, 0], [0, 0, 0.12]); P.add('door:#5a3a2a', new THREE.PlaneGeometry(2.4, 4.6), [1.6, 2.3, 3.02]); P.pop();
    // the striped deck chair facing the window (EP01 frame-1 prop), the bench, the table
    P.push(trs([-8.7, 0, 10.0], [0, PI, 0])); P_.addDeckChair(P, {}); P.pop();
    P.push(trs([6.0, 0, 9.0], [0, PI, 0])); const bench = addBench(P); P.pop();
    P.push(trs([13.0, 0, 8.6], [0, PI + 0.1, 0])); const table = addGardenTable(P); P.pop();
    const g = persistTree(P.build(M, { name: 'gardenMesh', cast: true, receive: true })); root.add(g);
    Hh.extras.forEach((e) => root.add(persistTree(e)));
    // the girl's window: custom pink-warm room card (curtains open, the star nightlight)
    const girlMat = I.decalMat('girlRoom', girlRoomTex(), { basic: true, k: 2.0 }); g.traverse((m) => { if (m.isMesh && m.name.startsWith('win:pink')) m.material = girlMat; });
    const rel = new THREE.Group(); rel.name = 'releaseDandelion'; const RP = new Parts(); P_.addDandelion(RP, { height: 1.35, puff: true, seed: 77 }); rel.add(persistTree(RP.build(M, { name: 'dandelionMesh' }))); rel.position.set(-6.6, 0, 9.0); root.add(rel);
    // anchors (studs -> metres in the clone wrapper below)
    const wyGirl = Hh.windows[0].y; const rot = (p, a, c) => { const v = new THREE.Vector3(...p).applyAxisAngle(new THREE.Vector3(0, 1, 0), a).add(new THREE.Vector3(...c)); return v.toArray(); };
    const A = {
      window: [-8.7, wyGirl, 0.1], windowNormal: [0, 0, 1], chairSeat: [-8.7, 1.15, 10.25], chairYaw: PI, release: [-6.6, 1.35, 9.0],
      benchSeatL: rot(bench.seats[0], PI, [6, 0, 9]), benchSeatR: rot(bench.seats[1], PI, [6, 0, 9]), benchYaw: PI,
      tableTop: rot([0, table.top, 0], PI + 0.1, [13, 0, 8.6]), pile: rot(table.pile, PI + 0.1, [13, 0, 8.6]), door: [5.5, 4.5, 0.2],
    };
    root.userData.anchorsStud = A; return root;
  });
  const set = tpl.clone(true); const root = new THREE.Group(); root.name = 'ep01BackGarden'; root.add(set); const xm = new THREE.Group(); root.add(xm);
  const A0 = set.userData.anchorsStud; const m = (p) => p.map((v) => +(v * S).toFixed(4)); const A = {}; for (const [k, v] of Object.entries(A0)) A[k] = Array.isArray(v) ? m(v) : v;
  const up = (p, dy, dx = 0, dz = 0) => [p[0] + dx * S, p[1] + dy * S, p[2] + dz * S];
  const head = up(A.benchSeatL, 2.8); const yaw = -15 * DEG; // s95/s96 = the s06 numbers (h 3.6, d 7.5, yaw -15) toward the seated head; the bench faces -Z
  const views = {
    tableTop: { pos: up(A.pile, 10.5, -1.2, 0.01), target: up(A.pile, 0, -1.2), fov: 45 },                                                      // s90
    phoneECU: { pos: up(A.benchSeatL, 2.1, 0.3, -2.4), target: up(A.benchSeatL, 1.4, 0, -1.0), fov: 50 },                        // s91 (phone in his hand)
    otsPhone: { pos: up(A.benchSeatL, 4.4, 0.8, 0.9), target: up(A.benchSeatL, 1.2, 0.1, -1.2), fov: 45 },                       // s92
    benchCU: { pos: up(head, 0.6, -0.7, -2.6), target: up(head, 0.1), fov: 70 },                                                // s94
    benchMS: { pos: [head[0] + Math.sin(yaw) * 7.5 * S, 3.6 * S, head[2] - Math.cos(yaw) * 7.5 * S], target: up(head, -1.2), fov: 70 },  // s95 / s96
    windowReverse: { pos: up(A.window, -1.7, 0, 1.2), target: up(A.chairSeat, 2.4), fov: 62 },                                   // s97 (from the girl's window toward the chair)
    gardenWide: { pos: [6 * S, 9 * S, 34 * S], target: [-2 * S, 3 * S, 2 * S], fov: 60 },
  };
  root.userData = { views, anchors: A, stud: S, slots: [], lots: [], lamps: [], windows: [{ lot: 'BG', face: 'front', lit: o.windowLit !== false, tone: 'pink', pos: A.window }], lanterns: [] };
  if (o.windowLit === false) set.traverse((x) => { if (x.isMesh && x.material && x.material.name === 'tex:girlRoom') x.material = M('glassDark'); });
  const ep = { set, tod, release: set.getObjectByName('releaseDandelion'), anchors: A, views };
  ep.light = (ctx2, lo = {}) => backGardenLight(ctx2, root, { tod, ...lo });
  ep.update = () => {};
  root.ep01 = ep; return root;
}
// Light for the back garden: dusk (sun el 5 from the side, warm window), blueHour (sky blue hour, sun just set, window
// spill stronger), night (galaxy + TF moon, window spill 2.8 cd: the loop-matched s97 end).
export function backGardenLight(ctx, root, o = {}) {
  const tod = o.tod || 'dusk'; const A = root.userData.anchors; const win = V3(A.window).add(new THREE.Vector3(0, -0.2, 0.5));
  let rig;
  if (tod === 'dusk') rig = sets.dusk(ctx, { set: null, sun: { az: o.sunAz ?? 75, el: 7 }, hemiIntensity: 2.0, postOpts: { exposure: 1.75 }, ...o.preset });
  else if (tod === 'blueHour') rig = sets.dusk(ctx, { set: null, skyPreset: 'blueHour', hemi: ['#8a9ad8', '#3a2a40', 1.9], sun: { color: '#ff9a70', intensity: 0.9, az: 75, el: 2 }, sunDisc: false, postOpts: { exposure: 1.55 }, ...o.preset });
  else rig = sets.nightStreet(ctx, { set: null, moon: o.moon ?? { az: 166, el: 30, size: 8, style: 'tf' }, hemiIntensity: 1.6, postOpts: { exposure: 1.4 }, ...o.preset });
  rig.window = ctx.add(ctx.lights.point({ color: '#ffc8a0', intensity: o.windowCd ?? (tod === 'night' ? 3.5 : 2.0), pos: win.toArray(), decay: 2 }));
  return rig;
}

// ------------------------------------------------------------------ YEARLY PHOTOS (render-to-texture), POLAROIDS, PHONE
// photoTexture(ctx, year, o) -> { texture, canvas, year }: the hero lot in spring daylight `year` years after the move,
// Grandpa gnome aged year/60 (moss, faded paint), Theo at 6 + year beside him, this year's tulips and curtains. Rendered
// ONCE per worker into a 512 x 512 canvas (cached): HDR render target -> ACES + a light print look -> readback.
// o: { size: 512, person: (age) => avatar root in metres, look: { warm, lift, sat }, blink: 0..1, girl: bool, exposure }
export const PHOTO_YEARS = [1, 5, 10, 16, 25, 33, 40, 52, 60];
export const photoLabel = (year) => (year === 1 ? '1st spring' : String(year));
// Fallback "Theo at age N" (the cast owner's theoAt(age) replaces it when it exists): kid pyjamas -> plaid shirt ->
// cardigan; blond -> grey -> bald with a grey beard at 66.
export function theoAtFallback(age) {
  if (typeof K.theoAt === 'function') return K.theoAt(age);
  if (age <= 12) return K.makeCharacter('theo', { scale: 0.85 + 0.15 * clamp01((age - 6) / 6), face: 'grin' });
  const grey = age >= 50; const bald = age >= 62; const acc = [];
  if (!bald) acc.push({ type: 'hair', style: 'short', color: grey ? '#c8c4cc' : age > 40 ? '#b89a58' : '#e2c46a' });
  if (age >= 45) acc.push({ type: 'moustache', color: grey ? '#d8d4dc' : '#9a7a40' });
  const outfit = age < 25 ? K.CAST.dad.outfit : age < 50 ? K.CAST.dad.outfit : K.CAST.heroOld.outfit;
  return K.makeCharacter('theo', { scale: 1, outfit, accessories: acc, face: 'grin', faceOverlays: age >= 40 ? { wrinkles: true } : {} });
}
function photoShader() {
  return new THREE.ShaderMaterial({
    uniforms: { tDiffuse: { value: null }, exposure: { value: 1.0 }, warm: { value: 0.06 }, lift: { value: 0.07 }, sat: { value: 0.88 } },
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }',
    fragmentShader: `uniform sampler2D tDiffuse; uniform float exposure, warm, lift, sat; varying vec2 vUv;
      vec3 aces(vec3 x){ const float a=2.51, b=0.03, c=2.43, d=0.59, e=0.14; return clamp((x*(a*x+b))/(x*(c*x+d)+e), 0.0, 1.0); }
      void main(){ vec3 c = texture2D(tDiffuse, vUv).rgb * exposure; c = aces(c);
        float l = dot(c, vec3(0.2126, 0.7152, 0.0722)); c = mix(vec3(l), c, sat); c += vec3(warm, warm * 0.4, -warm * 0.6);
        c = lift * vec3(1.0, 0.92, 0.82) + c * (1.0 - lift); vec2 q = vUv - 0.5; c *= 1.0 - 0.22 * dot(q, q) * 2.0;
        c = pow(clamp(c, 0.0, 1.0), vec3(1.0 / 2.2)); gl_FragColor = vec4(c, 1.0); }`,
    depthTest: false, depthWrite: false,
  });
}
export function photoTexture(ctx, year, o = {}) {
  const key = 'ep01:photo:' + year + ':' + JSON.stringify({ ...o, person: undefined });
  return ctx.cache(key, () => {
    const size = o.size || 512; const R = ctx.renderer; const scene = new THREE.Scene(); scene.background = null;
    const H = heroLot(ctx, { tod: 'day', year, era: 'now', board: false, keepOff: false, truck: false, bed: 'grandpa', nextDoor: false, theoRoom: { era: 'later', lit: false }, roomGlow: false, gnomes: ['lawn0', 'lawn1', 'bedFront1'] });
    scene.add(H); sets.setWindows(H, 'off');
    const g = H.ep01.gnomes.grandpa; if (g) { K.setGnomeHead(g, o.headYaw ?? 150, 4, 0); K.setGnomeGaze(g, 0, 2); if (o.blink) K.setGnomeLids(g, o.blink); } // he looks back over his shoulder for the photo
    H.ep01.theo.setGlass('photo');
    const age = 6 + year; const person = (o.person || theoAtFallback)(age); const sp = H.ep01.spots; const bp = V3(sp.bed0);
    person.position.set(bp.x + 3.0 * S, 0, bp.z + 1.2 * S); person.rotation.y = -0.15; if (K.setPose) K.setPose(person, { armRz: age < 13 ? 150 : 25, armRx: age < 13 ? 0 : -20, neckY: -8 }); scene.add(person);
    if (o.girl) { const girl = K.makeCharacter('theo', { scale: 0.75, face: 'openSmile' }); const w = V3(sp.theoWindow); girl.position.set(w.x + 0.15, (H.ep01.room.bounds ? 1.0 * S : 0.32) + 0.0, w.z - 1.1 * S); girl.rotation.y = 0; K.setPose(girl, { armRz: 150 }); scene.add(girl); }
    // daylight rig (no shadows), the day sky, light haze
    const sky = sets.sky(ctx, { preset: 'day' }); scene.add(sky);
    scene.add(new THREE.HemisphereLight('#bcd4ff', '#5a4a30', 1.15)); const sun = new THREE.DirectionalLight('#fff3e0', 2.6); sun.position.set(bp.x - 14, 18, bp.z + 22); sun.target.position.copy(bp); scene.add(sun, sun.target);
    const fill = new THREE.PointLight('#fff0e0', 2.5, 0, 2); fill.position.set(bp.x + 1.2, 1.6, bp.z + 2.6); scene.add(fill);
    const bounce = new THREE.PointLight('#fff4e8', 3.0, 0, 2); bounce.position.copy(V3(sp.theoWindow)).add(new THREE.Vector3(0.3, 0.4, -1.4)); scene.add(bounce); // daylight inside the room
    const vw = H.ep01.views.photo; const cam = new THREE.PerspectiveCamera(vw.fov, 1, 0.05, 900); cam.position.copy(V3(vw.pos)); cam.lookAt(V3(vw.target)); cam.updateMatrixWorld(true);
    const rt = new THREE.WebGLRenderTarget(size, size, { type: THREE.HalfFloatType, samples: 4 }); const rt2 = new THREE.WebGLRenderTarget(size, size, { type: THREE.UnsignedByteType });
    const prev = R.getRenderTarget(); const prevAuto = R.autoClear; const prevCol = R.getClearColor(new THREE.Color()); const prevA = R.getClearAlpha(); const prevSM = R.shadowMap.enabled;
    R.shadowMap.enabled = false; R.autoClear = true; R.setClearColor('#000000', 1);
    R.setRenderTarget(rt); R.clear(); R.render(scene, cam);
    const q = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), photoShader()); q.frustumCulled = false; q.material.uniforms.tDiffuse.value = rt.texture; q.material.uniforms.exposure.value = o.exposure ?? 1.05; const qs = new THREE.Scene(); qs.add(q); const oc = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    R.setRenderTarget(rt2); R.render(qs, oc); const px = new Uint8Array(size * size * 4); R.readRenderTargetPixels(rt2, 0, 0, size, size, px);
    R.setRenderTarget(prev); R.autoClear = prevAuto; R.setClearColor(prevCol, prevA); R.shadowMap.enabled = prevSM;
    rt.dispose(); rt2.dispose(); q.geometry.dispose(); q.material.dispose(); sky.traverse((x) => { if (x.geometry && !x.geometry.userData.persistent) x.geometry.dispose(); });
    const c = document.createElement('canvas'); c.width = c.height = size; const g2 = c.getContext('2d'); const id = g2.createImageData(size, size);
    for (let y = 0; y < size; y++) id.data.set(px.subarray((size - 1 - y) * size * 4, (size - y) * size * 4), y * size * 4);
    g2.putImageData(id, 0, 0);
    const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8; tex.userData.persistent = true;
    return { texture: tex, canvas: c, year };
  });
}
// Polaroid card (3.5 x 4.2 studs): white border, thick bottom margin with the hand-written label. Returns a Mesh in METRES
// (front = +Z, origin at the card centre). Cached texture per year.
export function polaroidTex(ctx, year, o = {}) {
  const ph = photoTexture(ctx, year, o.photo || {}); const label = o.label ?? photoLabel(year);
  return I.ctex('polaroid:' + year + ':' + label + ':' + JSON.stringify(o.photo || {}), 350, 420, (g, W, H) => {
    g.fillStyle = '#f6f2ea'; g.fillRect(0, 0, W, H); const r = makeRng(hash32('pol', year)); for (let k = 0; k < 300; k++) { g.fillStyle = `rgba(0,0,0,${0.015 + 0.02 * r()})`; g.fillRect(r() * W, r() * H, 2, 2); }
    g.drawImage(ph.canvas, 20, 20, 310, 310); g.strokeStyle = 'rgba(0,0,0,0.12)'; g.lineWidth = 2; g.strokeRect(20, 20, 310, 310);
    g.save(); g.translate(W / 2, 376); g.rotate(-0.04 + (r() - 0.5) * 0.04); g.fillStyle = '#2a2450'; g.font = `bold italic 40px ${FONT}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(label, 0, 0); g.restore();
  });
}
export function polaroid(ctx, year, o = {}) {
  const t = polaroidTex(ctx, year, o); const w = 3.5 * S, h = 4.2 * S; const g = new THREE.BoxGeometry(w, h, 0.03 * S);
  const front = I.decalMat('polaroid:' + year + ':' + (o.label ?? photoLabel(year)) + ':' + JSON.stringify(o.photo || {}), t, { roughness: 0.55 }); const paper = M('plastic:#ece6da');
  const m = new THREE.Mesh(g, [paper, paper, paper, paper, front, paper]); m.name = 'polaroid_' + year; return m;
}
// A pile of Polaroids dropping one by one onto a table (s90): stack(ctx, years, { at: [x,y,z] metres, t0s, dur 0.28 })
// -> Group with update(t): each card falls from 0.5 m with a spin, outQuad, landing at a seeded angle on the pile.
export function polaroidStack(ctx, years, { at = [0, 0, 0], t0s = null, dur = 0.28, height = 0.5 } = {}) {
  const grp = new THREE.Group(); grp.name = 'polaroidStack'; const r = makeRng(hash32('stack', years.join(',')));
  const cards = years.map((y, i) => { const c = polaroid(ctx, y); const land = { x: (r() - 0.5) * 0.3, z: (r() - 0.5) * 0.24, a: (r() - 0.5) * 1.1, y: i * 0.012 }; c.userData.land = land; c.userData.t0 = t0s ? t0s[i] : -1; grp.add(c); return c; });
  grp.position.set(...at);
  grp.update = (t) => { for (const c of cards) { const L = c.userData.land; const u = c.userData.t0 < 0 ? 1 : (t - c.userData.t0) / dur; c.visible = u >= 0; if (!c.visible) continue; const k = outQuad(u);
    c.position.set(L.x * k + (1 - k) * 0.08, L.y + 0.004 + (1 - k) * height, L.z * k); c.rotation.set(-PI / 2 + (1 - k) * 0.5, 0, L.a + (1 - k) * 1.4); } };
  grp.update(1e9); return grp;
}
// Phone (1.0 x 2.0 studs, black rounded body, bezel): the screen is an emissive gallery strip of photos (atlas); swipe
// slides the next photo in from the right in 8 frames (outCubic). phone(ctx, { photos: [years], name: 'Theo' })
// -> Group in METRES (screen faces +Z, origin at the phone centre) with ep01.swipe(t, [t0...]) and ep01.show(i).
function phoneAtlasTex(ctx, years, name) {
  return I.ctex('phoneAtlas:' + years.join(',') + name, 384 * years.length, 768, (g, W, H) => {
    years.forEach((y, i) => {
      const x0 = i * 384; g.fillStyle = '#0c0c10'; g.fillRect(x0, 0, 384, H);
      g.fillStyle = '#f4f2f8'; g.font = `bold 26px ${FONT}`; g.textBaseline = 'middle'; g.textAlign = 'left'; g.fillText('9:41', x0 + 22, 30); g.textAlign = 'right'; g.fillText('100%', x0 + 362, 30);
      g.fillStyle = '#d9a52c'; g.beginPath(); g.arc(x0 + 46, 92, 24, 0, PI * 2); g.fill(); g.fillStyle = '#0c0c10'; g.font = `bold 26px ${FONT}`; g.textAlign = 'center'; g.fillText(name[0], x0 + 46, 93);
      g.fillStyle = '#f4f2f8'; g.textAlign = 'left'; g.font = `bold 28px ${FONT}`; g.fillText(name, x0 + 84, 84); g.fillStyle = '#9a98a8'; g.font = `22px ${FONT}`; g.fillText(y === years[years.length - 1] ? 'just now' : `spring, year ${y}`, x0 + 84, 112);
      const ph = photoTexture(ctx, y).canvas; g.drawImage(ph, x0 + 6, 160, 372, 372);
      g.fillStyle = '#f4f2f8'; g.font = `bold 34px ${FONT}`; g.textAlign = 'left'; g.fillText('♥', x0 + 28, 580); g.fillText('↪', x0 + 92, 580);
      g.fillStyle = '#c8c6d4'; g.font = `24px ${FONT}`; g.fillText(y === 60 ? 'Grandpa says hi' : 'same flowerbed', x0 + 28, 630);
      g.fillStyle = '#3a3846'; g.fillRect(x0 + 132, 740, 120, 6);
    });
  });
}
export function phone(ctx, o = {}) {
  const years = o.photos || [60]; const name = o.name || 'Theo'; const n = years.length;
  const body = ctx.cache('ep01:phoneBody', () => { const P = new Parts(); P.add('black:#141418', new RoundedBoxGeometry(1.0, 2.0, 0.1, 4, 0.12)); P.box('metal:#3a3a44', 0.3, 0.06, 0.02, [0.2, 0.86, -0.06]); P.cyl('glassDark', 0.08, 0.08, 0.02, 12, [-0.28, 0.82, -0.06], [PI / 2, 0, 0]); return persistTree(P.build(M, { name: 'phoneBody' })); });
  const tex = phoneAtlasTex(ctx, years, name).clone(); tex.userData.persistent = false; tex.repeat.set(1 / n, 1); // per-shot clone (shares the GPU source) tex.offset.set(0, 0); tex.needsUpdate = true;
  const scr = new THREE.MeshBasicMaterial({ map: tex, color: new THREE.Color(1.2, 1.2, 1.2) }); const screen = new THREE.Mesh(new THREE.PlaneGeometry(0.92, 1.84), scr); screen.position.z = 0.052; screen.name = 'phoneScreen';
  const inner = new THREE.Group(); inner.add(body.clone(), screen); inner.scale.setScalar(S); const root = new THREE.Group(); root.name = 'ep01Phone'; root.add(inner);
  root.ep01 = { screen, tex,
    show(i) { tex.offset.x = Math.max(0, Math.min(n - 1, i)) / n; },
    swipe(t, times = []) { let k = 0; for (const t0 of times) { const u = (t - t0) * 60 / 8; if (u >= 1) k += 1; else if (u > 0) k += outCubic(u); } tex.offset.x = Math.min(n - 1, k) / n; },
  };
  return root;
}
