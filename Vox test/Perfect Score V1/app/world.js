// The sets: classroom, corridor, principal's office, living room, bedrooms.
// Each set lives at its own x offset and is shown alone; every set has a sun
// (directional light with shadows through real window openings) plus fills.
import * as THREE from 'three';
import * as P from './props.js';
import * as SX from './stex.js';
import { makeCharacter, POSES, SEAT_H } from './chars.js';
import { CAST_DEFS, classmateDef } from './cast.js';
import { makePaper } from './paper.js';
import { paintFace } from './faces.js';
import { canvas, toTex, noiseFill } from './tex.js';
import { rng } from './util.js';

const M = (color, rough = 0.8, extra = {}) => new THREE.MeshStandardMaterial({ color, roughness: rough, ...extra });
function add(parent, geo, mat, x, y, z, ry = 0) {
  const m = new THREE.Mesh(geo, mat);
  m.position.set(x, y, z); m.rotation.y = ry;
  m.castShadow = true; m.receiveShadow = true;
  parent.add(m);
  return m;
}
function place(parent, obj, x, y, z, ry = 0) { obj.position.set(x, y, z); obj.rotation.y = ry; parent.add(obj); return obj; }
function texRep(t, rx, ry) { const c = t.clone(); c.needsUpdate = true; c.wrapS = c.wrapT = THREE.RepeatWrapping; c.repeat.set(rx, ry); return c; }

// a wall along x or z with rectangular holes (windows/doors); built from boxes
function wallWithHoles(parent, axis, fixed, from, to, height, thick, holes, mat) {
  // axis 'x': wall runs along x at z = fixed; axis 'z': runs along z at x = fixed
  const segs = [];
  const sorted = [...holes].sort((a, b) => a.c - b.c);
  let cur = from;
  for (const h of sorted) {
    const a = h.c - h.w / 2, b = h.c + h.w / 2;
    if (a > cur) segs.push([cur, a, 0, height]);
    segs.push([a, b, 0, h.y0]);
    segs.push([a, b, h.y1, height]);
    cur = b;
  }
  if (cur < to) segs.push([cur, to, 0, height]);
  for (const [a, b, y0, y1] of segs) {
    if (y1 - y0 < 0.001 || b - a < 0.001) continue;
    const len = b - a, mid = (a + b) / 2;
    const geo = axis === 'x' ? new THREE.BoxGeometry(len, y1 - y0, thick) : new THREE.BoxGeometry(thick, y1 - y0, len);
    // wall UVs scaled to world metres so the texture keeps its size across pieces
    const uv = geo.attributes.uv, pos = geo.attributes.position;
    for (let i = 0; i < uv.count; i++) {
      const px = pos.getX(i) + (axis === 'x' ? mid : 0), pz = pos.getZ(i) + (axis === 'z' ? mid : 0), py = pos.getY(i) + (y0 + y1) / 2;
      uv.setXY(i, (axis === 'x' ? px : pz) / 2.4, py / height);
    }
    const m = new THREE.Mesh(geo, mat);
    if (axis === 'x') m.position.set(mid, (y0 + y1) / 2, fixed); else m.position.set(fixed, (y0 + y1) / 2, mid);
    m.castShadow = true; m.receiveShadow = true;
    parent.add(m);
  }
}

function floorPlane(parent, w, d, cx, cz, tex, rough = 0.6) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, d), new THREE.MeshStandardMaterial({ map: tex, roughness: rough, metalness: 0.0 }));
  m.rotation.x = -Math.PI / 2; m.position.set(cx, 0, cz); m.receiveShadow = true;
  parent.add(m);
  return m;
}
function ceiling(parent, w, d, cx, cz, h, tex) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, d), new THREE.MeshStandardMaterial({ map: tex, roughness: 0.9 }));
  m.rotation.x = Math.PI / 2; m.position.set(cx, h, cz); m.receiveShadow = true; m.castShadow = true;
  parent.add(m);
  return m;
}

// hazy beam from a window opening along the sun direction (additive, no depth write)
const shaftTex = (() => {
  let t = null;
  return () => {
    if (t) return t;
    const [c, g] = canvas(64, 256);
    const grd = g.createLinearGradient(0, 0, 0, 256);
    grd.addColorStop(0, 'rgba(255,240,210,0.55)'); grd.addColorStop(0.6, 'rgba(255,235,200,0.18)'); grd.addColorStop(1, 'rgba(255,230,190,0)');
    g.fillStyle = grd; g.fillRect(0, 0, 64, 256);
    t = toTex(c, { srgb: true });
    return t;
  };
})();
function sunShaft(parent, corners, dir, len, strength = 0.22) {
  // corners: 4 world points of the window opening (in order); extrude along dir
  const pts = corners.map((p) => p.clone());
  const far = pts.map((p) => p.clone().addScaledVector(dir, len));
  const pos = [], uv = [];
  for (let i = 0; i < 4; i++) {
    const a = pts[i], b = pts[(i + 1) % 4], c = far[(i + 1) % 4], d = far[i];
    pos.push(...a.toArray(), ...b.toArray(), ...c.toArray(), ...a.toArray(), ...c.toArray(), ...d.toArray());
    uv.push(0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv.map((v, i) => (i % 2 ? 1 - v : v)), 2));
  const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ map: shaftTex(), transparent: true, opacity: strength, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
  m.renderOrder = 5;
  parent.add(m);
  return m;
}

function makeSun(group, pos, target, intensity, color, box, mapSize = 4096) {
  const sun = new THREE.DirectionalLight(color, intensity);
  sun.position.copy(pos);
  sun.target.position.copy(target);
  sun.castShadow = true;
  sun.shadow.mapSize.set(mapSize, mapSize);
  Object.assign(sun.shadow.camera, { left: -box, right: box, top: box, bottom: -box, near: 0.5, far: 40 });
  sun.shadow.bias = -0.0003;
  sun.shadow.normalBias = 0.02;
  sun.shadow.radius = 3;
  group.add(sun, sun.target);
  return sun;
}

// -------------------------------------------------------------------------
export function buildWorld(scene) {
  const W = { sets: {}, cast: {}, kids: [], props: {}, anchors: {}, papers: {} };
  for (const k in CAST_DEFS) { W.cast[k] = makeCharacter(CAST_DEFS[k]); scene.add(W.cast[k].root); }
  for (let i = 0; i < 20; i++) { const ch = makeCharacter(classmateDef(i)); W.kids.push(ch); scene.add(ch.root); }
  buildClassroom(scene, W);
  buildHallway(scene, W);
  buildOffice(scene, W);
  buildHome(scene, W);
  buildBedrooms(scene, W);
  return W;
}

// ------------------------------------------------------------- classroom ---
export const CLASS = {
  x0: -4.6, x1: 4.6, z0: -4.2, z1: 4.6, h: 3.2,
  cols: [-3.0, -1.5, 0, 1.5, 3.0],
  rows: [-1.6, -0.3, 1.0, 2.3], // desk centres; seats are +0.42 behind (students face -z)
  heroCol: 2, heroRow: 2,
  front: new THREE.Vector3(-1.05, 0, -2.6), // hero desk next to the teacher's
  back: new THREE.Vector3(0, 0, 3.6),
  tDesk: new THREE.Vector3(-2.1, 0, -3.0),
  board: new THREE.Vector3(0.3, 1.55, -4.19),
};
export const SEAT_BACK = 0.42; // seat (hips) offset behind a desk centre

function buildClassroom(scene, W) {
  const g = new THREE.Group(); g.name = 'classroom';
  scene.add(g);
  const C = CLASS;
  const wallMat = new THREE.MeshStandardMaterial({ map: SX.schoolWall('#eadfc4', '#4f7a66', 0.34, [1, 1]), roughness: 0.85 });
  floorPlane(g, C.x1 - C.x0, C.z1 - C.z0, 0, (C.z0 + C.z1) / 2, SX.vinylTiles('#cfc3a6', 3, 4, [(C.x1 - C.x0) / 2, (C.z1 - C.z0) / 2]), 0.45);
  ceiling(g, C.x1 - C.x0, C.z1 - C.z0, 0, (C.z0 + C.z1) / 2, C.h, SX.ceilingTiles([(C.x1 - C.x0) / 0.6, (C.z1 - C.z0) / 0.6]));
  // left wall with three big windows (sun comes in from -x)
  const wins = [-2.5, 0.2, 2.9];
  wallWithHoles(g, 'z', C.x0 - 0.1, C.z0, C.z1, C.h, 0.2, wins.map((c) => ({ c, w: 1.9, y0: 0.9, y1: 2.65 })), wallMat);
  wins.forEach((c) => { const wu = P.windowUnit(1.9, 1.75, 'day', 3, 2); place(g, wu, C.x0 - 0.1, 1.775, c, Math.PI / 2); });
  wallWithHoles(g, 'z', C.x1 + 0.1, C.z0, C.z1, C.h, 0.2, [], wallMat);
  wallWithHoles(g, 'x', C.z0 - 0.1, C.x0 - 0.2, C.x1 + 0.2, C.h, 0.2, [], wallMat);
  wallWithHoles(g, 'x', C.z1 + 0.1, C.x0 - 0.2, C.x1 + 0.2, C.h, 0.2, [], wallMat);
  const dr = P.door('8B', '#8a5a32'); place(g, dr, C.x1, 0, 3.3, -Math.PI / 2); W.props.classDoor = dr;
  // front wall
  const wb = P.whiteboard(2.8, 1.15); place(g, wb, C.board.x, C.board.y, C.z0); W.props.board = wb;
  const clock = P.wallClock(); place(g, clock, 2.75, 2.55, C.z0 + 0.0); W.props.classClock = clock;
  place(g, P.posterBoard('periodic', 0.62, 0.85), -2.6, 1.85, C.z0 + 0.01);
  place(g, P.posterBoard('math', 0.5, 0.68), 2.6, 1.55, C.z0 + 0.01);
  place(g, P.posterBoard('reading', 0.5, 0.68), 3.5, 1.55, C.z0 + 0.01);
  // flag-like bunting of alphabet cards above the board
  for (let i = 0; i < 12; i++) {
    const [c, gg] = canvas(128, 160); gg.fillStyle = ['#e8743a', '#2a8a5a', '#1c5ab8', '#d8b24a'][i % 4]; gg.fillRect(0, 0, 128, 160);
    gg.fillStyle = '#fff'; gg.font = 'bold 96px "Liberation Sans"'; gg.textAlign = 'center'; gg.fillText('ABCDEFGHIJKL'[i], 64, 116);
    add(g, new THREE.PlaneGeometry(0.2, 0.25), M('#ffffff', 0.8, { map: toTex(c) }), -1.05 + i * 0.25, 2.62, C.z0 + 0.012);
  }
  // teacher desk + chair + clutter
  const td = P.teacherDesk(); place(g, td, C.tDesk.x, 0, C.tDesk.z); W.props.tDesk = td;
  const tch = P.officeChair(0.48, '#2a2a2e'); place(g, tch, C.tDesk.x, 0, C.tDesk.z - 0.62); W.props.tChair = tch;
  const mugT = P.mug('#f2f2ee', 'BEST TEACHER'); place(g, mugT, C.tDesk.x + 0.48, 0.76, C.tDesk.z - 0.12, 0.6); W.props.mug = mugT;
  const stack = P.stackOfPapers(14, 3); place(g, stack, C.tDesk.x - 0.45, 0.76, C.tDesk.z + 0.05, 0.1); W.props.paperStack = stack;
  const stack2 = P.stackOfPapers(30, 4); place(g, stack2, C.tDesk.x + 0.15, 0.76, C.tDesk.z + 0.12, -0.05); W.props.examStack = stack2;
  const books = P.notebook('#7a1c24', 0.03); place(g, books, C.tDesk.x - 0.25, 0.76, C.tDesk.z - 0.15, 0.3);
  place(g, P.plant(1.0), -4.05, 0, -3.7);
  // right wall: bookshelf + notice board; back wall: cubbies, poster, CCTV
  place(g, P.bookshelf(1.6, 1.9, 0.34, 3), C.x1 - 0.2, 0, -1.4, -Math.PI / 2);
  place(g, P.noticeBoard(1.5, 0.95, 5), C.x1 - 0.01, 1.65, 0.9, -Math.PI / 2);
  place(g, P.posterBoard('quote', 0.6, 0.82), 0, 1.85, C.z1 - 0.01, Math.PI);
  place(g, P.posterBoard('map', 0.9, 0.7), -2.2, 1.8, C.z1 - 0.01, Math.PI);
  place(g, P.bookshelf(1.2, 1.1, 0.34, 9), 2.4, 0, C.z1 - 0.2, Math.PI);
  place(g, P.trashBin(), 3.6, 0, C.z1 - 0.3);
  const cam = P.cctvCam(); place(g, cam, C.x1 - 0.25, 2.95, C.z1 - 0.25, -Math.PI * 0.78); W.props.cctv = cam;
  for (let i = 0; i < 3; i++) for (let j = 0; j < 2; j++) place(g, P.ceilingLight(1.3, 0.32), -2.6 + i * 2.6, C.h - 0.03, -2.2 + j * 3.6);
  // desks, chairs: a seat unit per column/row (desk at rows[r], chair 0.42 behind)
  W.class = { desks: [], chairs: [], seats: [] };
  C.cols.forEach((x, ci) => C.rows.forEach((z, ri) => {
    const desk = P.studentDesk(); place(g, desk, x, 0, z, Math.PI);
    const chair = P.studentChair(SEAT_H * 0.9, ['#2a5a8a', '#2a5a8a', '#3a7a5a'][(ci + ri) % 3]); place(g, chair, x, 0, z + SEAT_BACK, Math.PI);
    const hero = ci === C.heroCol && ri === C.heroRow;
    W.class.desks.push(desk); W.class.chairs.push(chair);
    W.class.seats.push({ x, z: z + SEAT_BACK, deskZ: z, ci, ri, hero, desk, chair });
    // clutter on desks: pencil case, notebook
    const r = rng(ci * 7 + ri * 13 + 1);
    if (!hero) {
      if (r() < 0.7) place(g, P.notebook(['#2a5a9a', '#9a2a3a', '#2a8a5a', '#d8a030'][Math.floor(r() * 4)]), x + (r() - 0.5) * 0.2, 0.66, z - 0.02, Math.PI + (r() - 0.5) * 0.4);
    }
  }));
  // the hero's own desk is a separate movable unit
  const hs = W.class.seats.find((s) => s.hero);
  W.props.heroDesk = hs.desk; W.props.heroChair = hs.chair;
  const hb = P.backpack('#b82020'); place(g, hb, hs.x + 0.32, 0, hs.z + 0.05, Math.PI * 0.6); W.props.heroBag = hb;
  // sun: low, from the windows (-x), slightly from the back so patches fall forward
  const sun = makeSun(g, new THREE.Vector3(-9.5, 6.4, 3.4), new THREE.Vector3(0, 0, -0.5), 3.0, '#ffe7c4', 7.5);
  const dir = new THREE.Vector3(0, 0, -0.5).sub(new THREE.Vector3(-9.5, 6.4, 3.4)).normalize();
  wins.forEach((c) => {
    const x = C.x0 - 0.02;
    const corners = [new THREE.Vector3(x, 2.62, c - 0.9), new THREE.Vector3(x, 2.62, c + 0.9), new THREE.Vector3(x, 0.93, c + 0.9), new THREE.Vector3(x, 0.93, c - 0.9)];
    sunShaft(g, corners, dir, 4.5, 0.16);
  });
  const hemi = new THREE.HemisphereLight('#e4ecff', '#8a7458', 0.7); g.add(hemi);
  const fills = [];
  for (const [x, z] of [[-1.5, -1.5], [1.8, 2.0], [1.5, -2.5]]) { const p = new THREE.PointLight('#fff2e0', 1.6, 9, 1.6); p.position.set(x, 2.9, z); g.add(p); fills.push(p); }
  W.sets.class = { group: g, sun, hemi, fills, env: 0.3, exposure: 1.0 };
}

// --------------------------------------------------------------- hallway ---
export const HALL = { x: 30, w: 3.4, z0: -22, z1: 2, h: 3.0, officeDoorZ: -21.9, honorZ: -16.5 };
function buildHallway(scene, W) {
  const g = new THREE.Group(); g.name = 'hallway';
  scene.add(g);
  const H = HALL, xl = H.x - H.w / 2, xr = H.x + H.w / 2;
  const wallMat = new THREE.MeshStandardMaterial({ map: SX.schoolWall('#efe6cf', '#2e5a7a', 0.36, [1, 1]), roughness: 0.85 });
  const fl = floorPlane(g, H.w, H.z1 - H.z0, H.x, (H.z0 + H.z1) / 2, SX.checkerTiles('#e2dccd', '#8a3a2a', [H.w / 1.0, (H.z1 - H.z0) / 1.0]), 0.25);
  fl.material.metalness = 0.05; fl.material.envMapIntensity = 1.4;
  ceiling(g, H.w, H.z1 - H.z0, H.x, (H.z0 + H.z1) / 2, H.h, SX.ceilingTiles([H.w / 0.6, (H.z1 - H.z0) / 0.6]));
  // right wall: windows onto the courtyard (sun from +x)
  const winZ = [-1, -4.2, -7.4, -10.6, -13.6];
  wallWithHoles(g, 'z', xr + 0.1, H.z0, H.z1, H.h, 0.2, winZ.map((c) => ({ c, w: 1.7, y0: 1.0, y1: 2.5 })), wallMat);
  winZ.forEach((c) => place(g, P.windowUnit(1.7, 1.5, 'day', 2, 2), xr + 0.1, 1.75, c, -Math.PI / 2));
  // left wall: lockers + classroom doors
  wallWithHoles(g, 'z', xl - 0.1, H.z0, H.z1, H.h, 0.2, [], wallMat);
  const lockCols = ['#2e6a8e', '#2e6a8e', '#8e2e3a'];
  [[-2.5, 8, 101], [-8.2, 8, 109], [-13.6, 6, 117]].forEach(([zc, n, st], i) => { place(g, P.lockerBank(n, lockCols[i % 3], st), xl + 0.23, 0, zc, Math.PI / 2); });
  [0.9, -5.6, -11.0].forEach((zc, i) => place(g, P.door(['8A', '8C', '9A'][i], '#8a5a32'), xl, 0, zc, Math.PI / 2));
  // end wall with the principal's door
  wallWithHoles(g, 'x', H.z0 - 0.1, xl - 0.2, xr + 0.2, H.h, 0.2, [{ c: H.x, w: 1.05, y0: 0, y1: 2.15 }], wallMat);
  const od = P.door('PRINCIPAL', '#5a3418'); place(g, od, H.x, 0, H.z0 + 0.0); W.props.officeDoor = od;
  { // glimpse of the office through the open door: warm wood room, lit
    const plankIn = new THREE.MeshStandardMaterial({ map: SX.plankWall('#b8682a', [1, 1]), roughness: 0.6, side: THREE.BackSide });
    const room = new THREE.Mesh(new THREE.BoxGeometry(3, 2.8, 3), plankIn); room.position.set(H.x, 1.4, H.z0 - 1.7); g.add(room);
    const fl2 = floorPlane(g, 3, 3, H.x, H.z0 - 1.7, SX.carpet('#5a6448', 9, [3, 3]), 0.95);
    const warm = new THREE.PointLight('#ffcf98', 6, 5, 1.5); warm.position.set(H.x + 0.6, 2.2, H.z0 - 1.4); g.add(warm);
    place(g, P.bookshelf(1.6, 2.1, 0.34, 61), H.x - 0.5, 0, H.z0 - 3.0);
  }
  wallWithHoles(g, 'x', H.z1 + 0.1, xl - 0.2, xr + 0.2, H.h, 0.2, [], wallMat);
  // wall of honor (right wall, between the last window and the office door)
  const plate = (() => {
    const [c, gg] = canvas(1024, 160);
    const grd = gg.createLinearGradient(0, 0, 0, 160); grd.addColorStop(0, '#f0d488'); grd.addColorStop(0.5, '#c89a3a'); grd.addColorStop(1, '#8a6420');
    gg.fillStyle = grd; gg.fillRect(0, 0, 1024, 160);
    gg.fillStyle = '#2a1a08'; gg.font = 'bold 92px "Liberation Serif"'; gg.textAlign = 'center'; gg.textBaseline = 'middle'; gg.fillText('WALL OF HONOR', 512, 84);
    return toTex(c);
  })();
  add(g, new THREE.PlaneGeometry(1.6, 0.25), M('#ffffff', 0.3, { map: plate, metalness: 0.6 }), xr - 0.01, 2.62, H.honorZ, -Math.PI / 2);
  W.honor = [];
  const honorFaces = [{ skin: '#e0b28c', hair: '#2e1e12', seed: 41 }, { skin: '#a8764e', hair: '#120c08', seed: 42, female: true, hijab: '#1d2846' }, { skin: '#f0d0b4', hair: '#6a4428', seed: 43 },
    { skin: '#c99a74', hair: '#1a120c', seed: 44, female: true, hijab: '#f2f2ee' }, { skin: '#8a5a3a', hair: '#120c08', seed: 45, hairStyle: 'buzz' }];
  for (let i = 0; i < 6; i++) {
    const col = i % 3, row = Math.floor(i / 3);
    const z = H.honorZ + (col - 1) * 0.62, y = 2.0 - row * 0.62;
    let tex;
    if (i === 4) tex = null; // the empty slot that the hero's portrait will fill
    else tex = portraitTex(honorFaces[i > 4 ? 4 : i], ['Sara M.', 'Yusuf A.', 'Leo P.', 'Maryam K.', '', 'Daniel O.'][i], 2018 + i);
    if (tex) { const f = P.framedPicture(tex, 0.42, 0.5, '#3a2410'); place(g, f, xr - 0.03, y, z, -Math.PI / 2); W.honor.push(f); }
    else W.anchors.honorSlot = new THREE.Vector3(xr - 0.03, y, z);
  }
  // benches + trophy shelf + notice board
  place(g, P.bench(1.6), xr - 0.3, 0, -18.6, -Math.PI / 2);
  place(g, P.noticeBoard(1.3, 0.85, 11), xl + 0.02, 1.6, -18.7, Math.PI / 2);
  place(g, P.plant(1.2), xr - 0.35, 0, H.z0 + 0.45);
  for (let i = 0; i < 8; i++) place(g, P.ceilingLight(1.2, 0.3), H.x, H.h - 0.03, 1 - i * 3, Math.PI / 2);
  const sun = makeSun(g, new THREE.Vector3(H.x + 9, 7, -6), new THREE.Vector3(H.x, 0, -10), 2.8, '#ffe6c0', 13);
  const dir = new THREE.Vector3(H.x, 0, -10).sub(new THREE.Vector3(H.x + 9, 7, -6)).normalize();
  winZ.forEach((c) => {
    const x = xr + 0.02;
    sunShaft(g, [new THREE.Vector3(x, 2.48, c - 0.82), new THREE.Vector3(x, 2.48, c + 0.82), new THREE.Vector3(x, 1.02, c + 0.82), new THREE.Vector3(x, 1.02, c - 0.82)], dir, 3.6, 0.14);
  });
  const hemi = new THREE.HemisphereLight('#e8eeff', '#7a5a48', 0.65); g.add(hemi);
  const fills = [];
  for (let i = 0; i < 4; i++) { const p = new THREE.PointLight('#fff0dc', 1.5, 8, 1.6); p.position.set(H.x, 2.8, -1 - i * 6); g.add(p); fills.push(p); }
  W.sets.hall = { group: g, sun, hemi, fills, env: 0.32, exposure: 1.0 };
}

export function portraitTex(face, name, year) {
  const [c, g] = canvas(420, 500);
  const grd = g.createLinearGradient(0, 0, 0, 420); grd.addColorStop(0, '#5a7a9a'); grd.addColorStop(1, '#2a3a4a');
  g.fillStyle = grd; g.fillRect(0, 0, 420, 420);
  // shoulders in uniform
  g.fillStyle = '#1d2846'; g.beginPath(); g.ellipse(210, 470, 190, 130, 0, 0, Math.PI * 2); g.fill();
  g.fillStyle = '#f3f3ef'; g.beginPath(); g.moveTo(170, 345); g.lineTo(250, 345); g.lineTo(210, 420); g.fill();
  g.fillStyle = '#7a1c24'; g.fillRect(203, 350, 14, 70);
  const f = paintFace({ young: 1, age: 0, ...face, hairStyle: face.hijab ? 'hijab' : (face.hairStyle || 'short') }, 448).canvas;
  g.drawImage(f, 80, 40, 260, 325);
  g.fillStyle = '#f4f0e6'; g.fillRect(0, 420, 420, 80);
  g.fillStyle = '#2a1a08'; g.font = 'bold 34px "Liberation Serif"'; g.textAlign = 'center'; g.fillText(name, 210, 462);
  g.font = '24px "Liberation Serif"'; g.fillText(year ? String(year) : '', 210, 490);
  noiseFill(g, 420, 500, 0, 6, 3, 1);
  return toTex(c);
}

// ---------------------------------------------------------------- office ---
export const OFFICE = { x: 60, x0: 57, x1: 63, z0: -3, z1: 3, h: 3.0, desk: new THREE.Vector3(60, 0, -1.4), table: new THREE.Vector3(60, 0, 0.9) };
function buildOffice(scene, W) {
  const g = new THREE.Group(); g.name = 'office';
  scene.add(g);
  const O = OFFICE;
  const plank = new THREE.MeshStandardMaterial({ map: SX.plankWall('#b8682a', [1, 1]), roughness: 0.6 });
  floorPlane(g, O.x1 - O.x0, O.z1 - O.z0, O.x, 0, SX.carpet('#5a6448', 9, [6, 6]), 0.95);
  ceiling(g, O.x1 - O.x0, O.z1 - O.z0, O.x, 0, O.h, SX.ceilingTiles([10, 10]));
  // back wall with a window behind the desk (sun from -z)
  wallWithHoles(g, 'x', O.z0 - 0.1, O.x0 - 0.2, O.x1 + 0.2, O.h, 0.2, [{ c: O.x, w: 2.0, y0: 0.95, y1: 2.55 }], plank);
  place(g, P.windowUnit(2.0, 1.6, 'day', 2, 1, '#e8e2d4'), O.x, 1.75, O.z0 - 0.1, 0);
  // venetian blinds (slats) half open
  for (let i = 0; i < 14; i++) { const s = add(g, new THREE.BoxGeometry(1.96, 0.006, 0.05), M('#f2ece0', 0.5), O.x, 2.5 - i * 0.075, O.z0 + 0.03); s.rotation.x = 0.55; }
  wallWithHoles(g, 'z', O.x0 - 0.1, O.z0, O.z1, O.h, 0.2, [], plank);
  wallWithHoles(g, 'z', O.x1 + 0.1, O.z0, O.z1, O.h, 0.2, [], plank);
  wallWithHoles(g, 'x', O.z1 + 0.1, O.x0 - 0.2, O.x1 + 0.2, O.h, 0.2, [], plank);
  const dr = P.door(null, '#5a3418'); place(g, dr, O.x1 - 1.0, 0, O.z1, Math.PI); W.props.officeInDoor = dr;
  // furniture
  const desk = P.bigDesk(); place(g, desk, O.desk.x, 0, O.desk.z, Math.PI); W.props.bigDesk = desk;
  const chair = P.officeChair(0.5, '#3a1a10'); place(g, chair, O.desk.x, 0, O.desk.z - 0.75); W.props.pChair = chair;
  const mon = P.computerMonitor(); place(g, mon, O.desk.x + 0.55, 0.77, O.desk.z - 0.12, Math.PI + 0.35); W.props.monitor = mon;
  place(g, P.keyboard(), O.desk.x + 0.3, 0.77, O.desk.z - 0.3, -0.2);
  place(g, P.mug('#1c3a5e', 'No.1 PRINCIPAL'), O.desk.x - 0.7, 0.77, O.desk.z - 0.2, 0.4);
  const lamp = P.deskLamp(); place(g, lamp, O.desk.x - 0.75, 0.77, O.desk.z + 0.15, Math.PI * 0.85);
  place(g, P.stackOfPapers(9, 8), O.desk.x - 0.35, 0.77, O.desk.z - 0.05, 0.2);
  place(g, P.bookshelf(1.8, 2.2, 0.36, 21), O.x0 + 0.2, 0, -0.9, Math.PI / 2);
  place(g, P.bookshelf(1.2, 2.2, 0.36, 31), O.x0 + 0.2, 0, 1.2, Math.PI / 2);
  place(g, P.plant(1.3), O.x1 - 0.45, 0, O.z0 + 0.45);
  place(g, P.plant(0.9), O.x0 + 0.45, 0, O.z0 + 0.4);
  // diplomas and a framed photo on the right wall
  for (let i = 0; i < 3; i++) {
    const [c, gg] = canvas(400, 300); gg.fillStyle = '#f4eedc'; gg.fillRect(0, 0, 400, 300); gg.strokeStyle = '#b8902a'; gg.lineWidth = 10; gg.strokeRect(14, 14, 372, 272);
    gg.fillStyle = '#2a1a08'; gg.font = 'bold 34px "Liberation Serif"'; gg.textAlign = 'center'; gg.fillText(['DIPLOMA', 'CERTIFICATE', 'AWARD'][i], 200, 100);
    gg.font = 'italic 22px "Liberation Serif"'; gg.fillText('in Education', 200, 150); gg.fillStyle = '#b8202a'; gg.beginPath(); gg.arc(320, 230, 24, 0, Math.PI * 2); gg.fill();
    place(g, P.framedPicture(toTex(c), 0.5, 0.38, '#2a1a10'), O.x1 - 0.02, 1.75 + (i === 1 ? 0.45 : 0), -1.2 + i * 0.75 - (i === 1 ? 0.75 : 0), -Math.PI / 2);
  }
  // exam table in the middle of the room (student faces the desk: -z)
  const tbl = P.smallTable(0.8, 0.6, 0.72); place(g, tbl, O.table.x, 0, O.table.z); W.props.examTable = tbl;
  const tchair = P.woodChair(SEAT_H * 0.92 + 0.02); place(g, tchair, O.table.x, 0, O.table.z + 0.45, Math.PI); W.props.examChair = tchair;
  // corner chair where the hero waits
  const wchair = P.woodChair(SEAT_H * 0.92 + 0.02); place(g, wchair, O.x0 + 0.7, 0, 2.2, Math.PI * 0.75); W.props.waitChair = wchair;
  const sun = makeSun(g, new THREE.Vector3(O.x - 2.5, 5.5, O.z0 - 7), new THREE.Vector3(O.x, 0, 0.5), 3.2, '#ffe2b8', 6);
  const dir = new THREE.Vector3(O.x, 0, 0.5).sub(new THREE.Vector3(O.x - 2.5, 5.5, O.z0 - 7)).normalize();
  sunShaft(g, [new THREE.Vector3(O.x - 0.98, 2.53, O.z0), new THREE.Vector3(O.x + 0.98, 2.53, O.z0), new THREE.Vector3(O.x + 0.98, 0.97, O.z0), new THREE.Vector3(O.x - 0.98, 0.97, O.z0)], dir, 4.0, 0.2);
  const hemi = new THREE.HemisphereLight('#ffe8d0', '#5a3a20', 0.6); g.add(hemi);
  const fills = [];
  for (const [x, z, i] of [[O.x + 1.5, 1.5, 1.4], [O.x - 1.8, 0, 1.2]]) { const p = new THREE.PointLight('#ffd8a8', i, 7, 1.6); p.position.set(x, 2.7, z); g.add(p); fills.push(p); }
  const lampLight = new THREE.PointLight('#ffcc88', 1.2, 2.5, 2); lampLight.position.set(O.desk.x - 0.75, 1.15, O.desk.z + 0.05); g.add(lampLight); fills.push(lampLight);
  W.sets.office = { group: g, sun, hemi, fills, env: 0.28, exposure: 1.0 };
}

// ------------------------------------------------------------------ home ---
export const HOME = { x: 90, x0: 87.5, x1: 92.5, z0: -2.5, z1: 2.5, h: 2.8 };
function buildHome(scene, W) {
  const g = new THREE.Group(); g.name = 'home';
  scene.add(g);
  const Hm = HOME;
  const paper = new THREE.MeshStandardMaterial({ map: SX.damask('#7a2a22', '#4e1612', [1, 1]), roughness: 0.85 });
  const woodFloor = (() => { const [c, gg] = canvas(1024, 1024); const r = rng(5); for (let i = 0; i < 8; i++) { gg.fillStyle = SX.shiftHex('#8a5a32', (r() - 0.5) * 30); gg.fillRect(0, i * 128, 1024, 128); gg.fillStyle = 'rgba(30,15,5,0.6)'; gg.fillRect(0, i * 128, 1024, 3); gg.fillRect(r() * 1024, i * 128, 3, 128); } noiseFill(gg, 1024, 1024, 0, 12, 6, 2); return toTex(c, { repeat: [2.5, 2.5] }); })();
  floorPlane(g, Hm.x1 - Hm.x0, Hm.z1 - Hm.z0, Hm.x, 0, woodFloor, 0.5);
  ceiling(g, Hm.x1 - Hm.x0, Hm.z1 - Hm.z0, Hm.x, 0, Hm.h, SX.solidTex('#efe8dc'));
  wallWithHoles(g, 'z', Hm.x0 - 0.1, Hm.z0, Hm.z1, Hm.h, 0.2, [{ c: 0.2, w: 1.3, y0: 0.9, y1: 2.25 }], paper);
  place(g, P.windowUnit(1.3, 1.35, 'day', 2, 2, '#f0ece2'), Hm.x0 - 0.1, 1.575, 0.2, Math.PI / 2);
  wallWithHoles(g, 'z', Hm.x1 + 0.1, Hm.z0, Hm.z1, Hm.h, 0.2, [], paper);
  wallWithHoles(g, 'x', Hm.z0 - 0.1, Hm.x0 - 0.2, Hm.x1 + 0.2, Hm.h, 0.2, [], paper);
  wallWithHoles(g, 'x', Hm.z1 + 0.1, Hm.x0 - 0.2, Hm.x1 + 0.2, Hm.h, 0.2, [], paper);
  // skirting + chair rail in wood
  for (const [axis, fixed, a, b] of [['x', Hm.z0 + 0.01, Hm.x0, Hm.x1], ['z', Hm.x1 - 0.01, Hm.z0, Hm.z1]]) {
    const len = b - a;
    add(g, axis === 'x' ? new THREE.BoxGeometry(len, 0.12, 0.03) : new THREE.BoxGeometry(0.03, 0.12, len), M('#3a2010', 0.5), axis === 'x' ? (a + b) / 2 : fixed, 0.06, axis === 'x' ? fixed : (a + b) / 2);
  }
  const sofa = P.sofa('#6e4a30'); place(g, sofa, Hm.x + 0.2, 0, Hm.z0 + 0.55); W.props.sofa = sofa;
  const st = P.sideTable(); place(g, st, Hm.x - 1.25, 0, Hm.z0 + 0.6); W.props.sideTable = st;
  const phone = P.smartphone(); place(g, phone, Hm.x - 1.25, 0.618, Hm.z0 + 0.6, 0.4); W.props.phone = phone;
  place(g, P.floorLamp(), Hm.x + 1.6, 0, Hm.z0 + 0.4);
  place(g, P.rug(2.6, 1.8), Hm.x + 0.1, 0, 0.3);
  const tv = P.tvCabinet(); place(g, tv, Hm.x + 0.1, 0, Hm.z1 - 0.3, Math.PI);
  place(g, P.plant(1.2), Hm.x1 - 0.4, 0, Hm.z1 - 0.4);
  // shelf with a flower pot and family photo (like the reference living room)
  add(g, new THREE.BoxGeometry(0.7, 0.04, 0.22), M('#4a2a14', 0.5), Hm.x - 0.6, 1.75, Hm.z0 + 0.11);
  const pot = P.plant(0.45); pot.scale.setScalar(0.55); place(g, pot, Hm.x - 0.75, 1.77, Hm.z0 + 0.12);
  const fam = P.framedPicture(portraitTex({ skin: '#c99a74', hair: '#1c120c', seed: 101 }, 'Adam', 2019), 0.2, 0.24, '#c8a04a'); fam.scale.setScalar(1); place(g, fam, Hm.x - 0.4, 1.9, Hm.z0 + 0.12, 0.15);
  const sun = makeSun(g, new THREE.Vector3(Hm.x - 8, 5.5, 2.5), new THREE.Vector3(Hm.x, 0, -0.3), 3.0, '#ffdcb0', 6);
  const dir = new THREE.Vector3(Hm.x, 0, -0.3).sub(new THREE.Vector3(Hm.x - 8, 5.5, 2.5)).normalize();
  sunShaft(g, [new THREE.Vector3(Hm.x0, 2.23, -0.43), new THREE.Vector3(Hm.x0, 2.23, 0.83), new THREE.Vector3(Hm.x0, 0.92, 0.83), new THREE.Vector3(Hm.x0, 0.92, -0.43)], dir, 3.5, 0.2);
  const hemi = new THREE.HemisphereLight('#ffe4cc', '#6a3020', 0.85); g.add(hemi);
  const fills = [];
  const lampL = new THREE.PointLight('#ffc880', 2.0, 5, 1.8); lampL.position.set(Hm.x + 1.6, 1.5, Hm.z0 + 0.45); g.add(lampL); fills.push(lampL);
  const f2 = new THREE.PointLight('#fff0dc', 2.6, 7, 1.6); f2.position.set(Hm.x - 0.3, 2.5, 0.2); g.add(f2); fills.push(f2);
  W.sets.home = { group: g, sun, hemi, fills, env: 0.28, exposure: 1.0 };
}

// -------------------------------------------------------------- bedrooms ---
export const BED = { x: 120, x0: 118, x1: 122, z0: -2, z1: 2, h: 2.7 };
export const BED2 = { x: 135, x0: 133, x1: 137, z0: -2, z1: 2, h: 2.7 };
function buildBedrooms(scene, W) {
  // hero's room: desk under a lamp at night
  {
    const g = new THREE.Group(); g.name = 'bedroom'; scene.add(g);
    const B = BED;
    const wall = new THREE.MeshStandardMaterial({ map: SX.schoolWall('#7a8aa8', '#4a5a7a', 0.0, [1, 1]), roughness: 0.9 });
    floorPlane(g, B.x1 - B.x0, B.z1 - B.z0, B.x, 0, SX.carpet('#4a4a5a', 4, [4, 4]), 0.95);
    ceiling(g, B.x1 - B.x0, B.z1 - B.z0, B.x, 0, B.h, SX.solidTex('#d8d8e0'));
    wallWithHoles(g, 'x', B.z0 - 0.1, B.x0 - 0.2, B.x1 + 0.2, B.h, 0.2, [{ c: B.x + 1.0, w: 1.0, y0: 1.0, y1: 2.1 }], wall);
    place(g, P.windowUnit(1.0, 1.1, 'night', 2, 2), B.x + 1.0, 1.55, B.z0 - 0.1, 0);
    wallWithHoles(g, 'z', B.x0 - 0.1, B.z0, B.z1, B.h, 0.2, [], wall);
    wallWithHoles(g, 'z', B.x1 + 0.1, B.z0, B.z1, B.h, 0.2, [], wall);
    wallWithHoles(g, 'x', B.z1 + 0.1, B.x0 - 0.2, B.x1 + 0.2, B.h, 0.2, [], wall);
    const desk = P.smallTable(1.1, 0.6, 0.72); place(g, desk, B.x - 0.4, 0, B.z0 + 0.35); W.props.homeDesk = desk;
    const ch = P.woodChair(SEAT_H * 0.92 + 0.02); place(g, ch, B.x - 0.4, 0, B.z0 + 0.8, Math.PI); W.props.homeChair = ch;
    const lamp = P.deskLamp(); place(g, lamp, B.x - 0.86, 0.72, B.z0 + 0.15, 0.6); W.props.homeLamp = lamp;
    const r = rng(9);
    for (let i = 0; i < 6; i++) place(g, P.notebook(['#2a5a9a', '#9a2a3a', '#2a8a5a', '#d8a030', '#5a2a5a', '#204a6a'][i], 0.025), B.x + 0.0 + (r() - 0.5) * 0.03, 0.72 + i * 0.026, B.z0 + 0.22, (r() - 0.5) * 0.3);
    const alarm = P.wallClock(); alarm.scale.setScalar(0.32); place(g, alarm, B.x + 0.0, 0.72 + 6 * 0.026 + 0.06, B.z0 + 0.2, -0.25); W.props.alarm = alarm;
    place(g, P.bed('#2a4a7a'), B.x + 1.2, 0, B.z1 - 1.05);
    place(g, P.posterBoard('periodic', 0.5, 0.68), B.x - 0.4, 1.7, B.z0 + 0.01);
    place(g, P.bookshelf(0.9, 1.2, 0.3, 44), B.x0 + 0.17, 0, 0.6, Math.PI / 2);
    const sun = makeSun(g, new THREE.Vector3(B.x + 3, 4, B.z0 - 6), new THREE.Vector3(B.x, 0, 0), 0.5, '#7088d0', 5, 2048); // moonlight
    const hemi = new THREE.HemisphereLight('#3a4a80', '#1a1a2a', 0.35); g.add(hemi);
    const lampL = new THREE.SpotLight('#ffd49a', 5, 4, 1.0, 0.6, 1.6);
    lampL.position.set(B.x - 0.72, 1.12, B.z0 + 0.38); lampL.target.position.set(B.x - 0.4, 0.72, B.z0 + 0.45);
    lampL.castShadow = true; lampL.shadow.mapSize.set(2048, 2048); lampL.shadow.bias = -0.0005;
    g.add(lampL, lampL.target);
    const glow = new THREE.PointLight('#ffc070', 0.9, 2.5, 2); glow.position.set(B.x - 0.65, 1.05, B.z0 + 0.62); g.add(glow);
    W.sets.bedroom = { group: g, sun, hemi, fills: [lampL, glow], env: 0.12, exposure: 1.05 };
  }
  // a classmate's room: lying in bed, face lit by a phone
  {
    const g = new THREE.Group(); g.name = 'bedroom2'; scene.add(g);
    const B = BED2;
    const wall = new THREE.MeshStandardMaterial({ map: SX.schoolWall('#8a7a9a', '#5a4a6a', 0.0, [1, 1]), roughness: 0.9 });
    floorPlane(g, B.x1 - B.x0, B.z1 - B.z0, B.x, 0, SX.carpet('#5a4a4a', 5, [4, 4]), 0.95);
    ceiling(g, B.x1 - B.x0, B.z1 - B.z0, B.x, 0, B.h, SX.solidTex('#d0d0d8'));
    wallWithHoles(g, 'x', B.z0 - 0.1, B.x0 - 0.2, B.x1 + 0.2, B.h, 0.2, [{ c: B.x - 1.0, w: 0.9, y0: 1.1, y1: 2.1 }], wall);
    place(g, P.windowUnit(0.9, 1.0, 'night', 2, 2), B.x - 1.0, 1.6, B.z0 - 0.1, 0);
    wallWithHoles(g, 'z', B.x0 - 0.1, B.z0, B.z1, B.h, 0.2, [], wall);
    wallWithHoles(g, 'z', B.x1 + 0.1, B.z0, B.z1, B.h, 0.2, [], wall);
    wallWithHoles(g, 'x', B.z1 + 0.1, B.x0 - 0.2, B.x1 + 0.2, B.h, 0.2, [], wall);
    const bd = P.bed('#7a3a4a'); place(g, bd, B.x, 0, B.z0 + 1.05, 0); W.props.bed2 = bd;
    const phone2 = P.smartphone(); g.add(phone2); W.props.phone2 = phone2;
    place(g, P.posterBoard('reading', 0.5, 0.68), B.x + 1.0, 1.7, B.z0 + 0.01);
    const sun = makeSun(g, new THREE.Vector3(B.x - 3, 4, B.z0 - 6), new THREE.Vector3(B.x, 0, 0), 0.45, '#7088d0', 5, 2048);
    const hemi = new THREE.HemisphereLight('#2a3a70', '#141420', 0.3); g.add(hemi);
    const phoneL = new THREE.PointLight('#a8c8ff', 0.5, 1.0, 2); g.add(phoneL);
    W.sets.bedroom2 = { group: g, sun, hemi, fills: [phoneL], env: 0.08, exposure: 1.05, phoneLight: phoneL };
  }
}
