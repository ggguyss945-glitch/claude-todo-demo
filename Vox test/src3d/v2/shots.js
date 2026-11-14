// Shot list: camera paths + staging for every cut of the original, timed to the
// voice-over. Each shot is a pure function of time (deterministic rendering).
import * as THREE from 'three';
import { POSES, blendPose, walkPose, makeGlasses, mat, cyl, box } from './chars.js';
import { TABLE, chipPile, chipStack, BLUE, REDC, makePhone, makeWalkie } from './props.js';
import { SURV, OFFICE } from './world.js';
import { prog, lerp, keys, easeInOut, easeOut, easeIn, smooth, shake, clamp, hash, easeInOutQuint } from './util.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);
const S2P = new THREE.Vector3(3.2, 0, 5.4), S2RY = -Math.PI / 2 - 0.35;
function s2Glasses() {
  const F = [Math.sin(S2RY), Math.cos(S2RY)], L = [Math.cos(S2RY), -Math.sin(S2RY)];
  return new THREE.Vector3(S2P.x + F[0] * 0.36 + L[0] * 0.14, 1.06, S2P.z + F[1] * 0.36 + L[1] * 0.14);
}
const SEAT = V(0, 0, 2.02);
const EYE = V(0, 1.27, 1.86);

// ------------------------------------------------------------ board state ---
const BOARD_TL = [
  [0, 'black'], [4.3, 'rolling'], [5.85, 'red'], [8.0, 'rolling'], [8.9, 'red'], [12.6, 'black'], [19.5, 'red'],
  [41.5, 'black'], [46.1, 'red'], [48.4, 'rolling'], [49.85, 'black'], [53.9, 'rolling'], [54.95, 'red'],
  [60.9, 'black'], [64.4, 'rolling'], [65.85, 'green'],
];
export function boardState(t) {
  let s = 'black';
  for (const [tt, st] of BOARD_TL) if (t >= tt) s = st;
  return s;
}
const RING_TL = [
  [0, ['red', 'red', null, 'red', null]], [5.85, ['red', 'red', 'red', 'red', null]], [7.4, ['red', null, null, null, null]],
  [8.9, [null, 'red', null, null, null]], [12.6, ['red', null, null, null, 'green']], [13.5, ['red', null, null, 'red', null]],
  [19.5, [null, null, 'red', null, null]], [41.5, ['red', 'red', 'green', 'red', null]], [46.1, [null, 'red', 'red', 'red', null]],
  [48.4, [null, 'red', 'green', 'red', null]], [63.8, ['green', 'red', null, null, null]], [65.85, ['red', null, null, null, null]],
  [66.6, ['red', null, null, null, null]],
];
function ringState(t) {
  let s = RING_TL[0][1];
  for (const [tt, st] of RING_TL) if (t >= tt) s = st;
  return s;
}

// ---------------------------------------------------------------- helpers ---
function hideHead(ch) { ch.J.neck.visible = false; }
function show(ch, x, z, ry, pose, y = 0) {
  ch.J.neck.visible = true;
  ch.root.visible = true;
  ch.root.position.set(x, y, z);
  ch.root.rotation.set(0, ry, 0);
  ch.setPose(pose);
  if (ch.headMesh) ch.headMesh.visible = true;
  if (ch.glasses) ch.glasses.visible = true;
}

// chips are rebuilt only when the layout key changes
let chipKey = '';
function chips(W, key, build) {
  if (key === chipKey) return;
  chipKey = key;
  const root = W.props.chipRoot;
  while (root.children.length) root.remove(root.children[0]);
  if (build) build(root);
}
function pileAt(root, x, z, spec, seed) {
  const p = chipPile(spec, seed);
  p.position.set(x, TABLE.H, z);
  root.add(p);
  return p;
}
const spot = (n) => TABLE.spots.find((s) => s.name === n);

// table-side seated players present for most casino shots
function sidePlayers(W, t) {
  const C = W.cast;
  show(C.topHat, -0.98, 0.35, Math.PI / 2, blendPose(POSES.sitTable, POSES.sit, 0.0));
  C.topHat.J.neck.rotation.y = 0.3 * Math.sin(t * 0.4);
  show(C.ladyRed, 0.98, -0.15, -Math.PI / 2, POSES.sitTable);
  show(C.blondBlue, -2.75, -1.35, 2.3, POSES.sitTable);
}

function crowdAround(W, t, opts = {}) {
  // 22 spectators standing around the hero table
  const n = opts.n ?? 22;
  for (let i = 0; i < W.crowd.length; i++) {
    const c = W.crowd[i];
    if (i >= n) { c.root.visible = false; continue; }
    const side = i % 2 ? 1 : -1;
    const k = Math.floor(i / 2);
    const row = k % 3 === 2 ? 1 : 0;
    const z = -0.9 + (k / 10) * 3.0 + hash(i, 4) * 0.2;
    const x = side * (1.12 + row * 0.55 + hash(i, 5) * 0.25);
    const ry = side > 0 ? -Math.PI / 2 + (hash(i, 6) - 0.5) * 0.6 : Math.PI / 2 + (hash(i, 6) - 0.5) * 0.6;
    const lean = row === 0 && hash(i, 7) < (opts.lean ?? 0.6);
    let pose = lean ? POSES.leanIn : (hash(i, 8) < 0.3 ? POSES.armsCrossed : POSES.stand);
    show(c, x, z, ry, pose);
    if (lean) c.J.neck.rotation.y = Math.sin(t * 0.7 + i) * 0.2;
  }
}

// camera-space POV arms (lavender sleeves, pale blocky hands)
let povRig = null;
function getPovRig(scene) {
  if (povRig) return povRig;
  povRig = new THREE.Group();
  const sleeve = mat('#6f6fd6', { rough: 0.85 });
  const hand = mat('#e8c4a8', { rough: 0.7 });
  povRig.userData.arms = [];
  for (const side of [-1, 1]) {
    const arm = new THREE.Group();
    const fore = new THREE.Mesh(cyl(0.05, 0.046, 0.5, 7), sleeve);
    fore.rotation.x = Math.PI / 2;
    fore.position.z = 0.25;
    arm.add(fore);
    const h = new THREE.Group();
    const palm = new THREE.Mesh(box(0.085, 0.035, 0.13), hand);
    palm.position.z = -0.06;
    h.add(palm);
    const thumb = new THREE.Mesh(box(0.024, 0.026, 0.065), hand);
    thumb.position.set(-side * 0.05, 0.008, -0.02);
    thumb.rotation.y = side * 0.5;
    h.add(thumb);
    arm.add(h);
    arm.userData.hand = h;
    povRig.add(arm);
    povRig.userData.arms.push(arm);
  }
  const gl = makeGlasses('pink', 1.0);
  povRig.add(gl);
  povRig.userData.glasses = gl;
  povRig.traverse((m) => { if (m.isMesh) { m.castShadow = false; m.receiveShadow = true; } });
  scene.add(povRig);
  return povRig;
}

// sparkles around the magic glasses
let sparkles = null;
function getSparkles(scene) {
  if (sparkles) return sparkles;
  sparkles = new THREE.Group();
  const m = new THREE.MeshBasicMaterial({ color: new THREE.Color(2.2, 1.9, 0.45) });
  for (let i = 0; i < 34; i++) {
    const s = new THREE.Mesh(new THREE.SphereGeometry(0.0065, 6, 4), m);
    sparkles.add(s);
  }
  scene.add(sparkles);
  return sparkles;
}
function updateSparkles(center, t, radius = 0.22, visible = true) {
  sparkles.visible = visible;
  sparkles.position.copy(center);
  sparkles.children.forEach((s, i) => {
    const a = hash(i, 1) * Math.PI * 2 + t * (0.5 + hash(i, 2));
    const r = radius * (0.5 + hash(i, 3));
    const y = (hash(i, 4) - 0.5) * radius * 1.4 + Math.sin(t * 2 + i) * 0.02;
    s.position.set(Math.cos(a) * r, y, Math.sin(a) * r * 0.6);
    const tw = 0.6 + 0.4 * Math.sin(t * 9 + i * 1.7);
    s.scale.setScalar(tw * (0.8 + hash(i, 5) * 0.9));
  });
}

let bang = null;
function getBang(scene) {
  if (bang) return bang;
  bang = new THREE.Group();
  const m = new THREE.MeshBasicMaterial({ color: new THREE.Color(3.2, 0.25, 0.2) });
  const bar = new THREE.Mesh(box(0.045, 0.2, 0.02), m);
  bar.position.y = 0.06;
  bar.rotation.z = -0.15;
  const dot = new THREE.Mesh(box(0.05, 0.05, 0.02), m);
  dot.position.set(-0.025, -0.1, 0);
  bang.add(bar, dot);
  scene.add(bang);
  return bang;
}

// handheld props that follow a character's hand
let walkie = null, phone = null;
function attach(scene, obj, ch, joint, off, rot) {
  ch.root.updateMatrixWorld(true);
  const j = ch.J[joint];
  obj.visible = true;
  const m = j.matrixWorld.clone().multiply(new THREE.Matrix4().compose(off, new THREE.Quaternion().setFromEuler(rot), V(1, 1, 1)));
  m.decompose(obj.position, obj.quaternion, obj.scale);
}

// paper sheet with mugshots (canvas built in main.js)
let paper = null, polaroid = null;

// ------------------------------------------------------------- defaults ---
export function stageDefault(W, t, cam) {
  const C = W.cast;
  for (const k in C) C[k].root.visible = false;
  for (const c of W.crowd) c.root.visible = false;
  if (povRig) povRig.visible = false;
  if (sparkles) sparkles.visible = false;
  if (bang) bang.visible = false;
  if (walkie) walkie.visible = false;
  if (phone) phone.visible = false;
  if (paper) paper.visible = false;
  if (polaroid) polaroid.visible = false;
  W.props.rake.visible = false;
  W.props.wheel.update(t);
  W.props.board.userData.draw(boardState(t), t * 5.0);
  W.props.rings.userData.set(ringState(t));
  // dealer at the wheel
  const dealer = t < 53.6 ? C.dealer : C.dealer2;
  show(dealer, 0.02, -1.78, 0, POSES.dealer);
  dealer.J.neck.rotation.y = Math.sin(t * 0.6) * 0.15;
  W.dealerNow = dealer;
  // chandeliers back to their home positions
  W.props.chandeliers.forEach((ch) => { if (ch.userData.home) ch.position.copy(ch.userData.home); else ch.userData.home = ch.position.clone(); });
  W.props.bgTables.forEach((tb) => { if (tb.userData.home) { tb.position.copy(tb.userData.home.p); tb.rotation.y = tb.userData.home.r; } else tb.userData.home = { p: tb.position.clone(), r: tb.rotation.y }; });
  W.extraPost = {};
  W.cctv = null;
}

// ---------------------------------------------------------------- shots ---
// cam(t) returns {p:[x,y,z], l:[x,y,z], fov, roll}
export const SHOTS = [
  // 1 — establishing: you, standing in the casino holding the glasses
  {
    t0: 0, t1: 1.333, set: 'casino', est: true,
    setup(W, t) {
      const C = W.cast;
      const tb = W.props.bgTables[2];
      tb.position.set(-4.5, 0, 3.75); tb.rotation.y = 2.25;
      const tb2 = W.props.bgTables[3];
      tb2.position.set(-4.25, 0, 6.35); tb2.rotation.y = Math.PI / 2;
      const tb3 = W.props.bgTables[4];
      tb3.position.set(-6.7, 0, 7.5); tb3.rotation.y = 0.3;
      show(C.player, -4.95, 6.9, Math.PI - 0.12, { ...POSES.stand, lShoulder: [-0.7, 0, 0.22], rShoulder: [-0.7, 0, -0.22], lElbow: [-1.25, 0, -0.25], rElbow: [-1.25, 0, 0.25] });
      C.player.glasses.visible = false;
      show(C.ladyRed, -3.8, 3.05, -0.85, POSES.sitTable);
      show(C.blondBlue, -6.0, 7.9, -2.4, POSES.sitTable);
      W.props.chandeliers[3].position.set(-5.85, 3.0, 4.25);
      W.props.chandeliers[4].position.set(-5.35, 3.35, 6.3);
      W.props.chandeliers[6].position.set(-3.2, 3.5, 8.0);
      const rig = getPovRig(W.scene);
      rig.visible = true;
      rig.userData.arms.forEach((a) => (a.visible = false));
      C.player.root.updateMatrixWorld(true);
      const hp = new THREE.Vector3(), hp2 = new THREE.Vector3();
      C.player.J.lWrist.localToWorld(hp.set(0, -0.08, 0));
      C.player.J.rWrist.localToWorld(hp2.set(0, -0.08, 0));
      rig.position.copy(hp).add(hp2).multiplyScalar(0.5);
      rig.rotation.set(0, Math.PI - 0.12, 0);
      rig.userData.glasses.position.set(0, 0, 0);
      rig.userData.glasses.rotation.set(0.3, 0, 0);
      rig.userData.glasses.scale.setScalar(1.0);
    },
    cam: (t) => ({ p: keys(t, [[0, [-4.85, 2.05, 1.55]], [1.333, [-4.88, 2.02, 1.9]]]), l: keys(t, [[0, [-5.0, 0.85, 7.2]], [1.333, [-5.05, 0.85, 7.2]]]), fov: 63 }),
  },
  // 2 — close on the glasses with sparkles
  {
    t0: 1.333, t1: 2.467, set: 'casino',
    setup(W, t) {
      const C = W.cast;
      show(C.player, S2P.x, S2P.z, S2RY, { ...POSES.stand, lShoulder: [-0.75, 0, 0.32], rShoulder: [-0.75, 0, -0.32], lElbow: [-1.2, 0, -0.42], rElbow: [-1.2, 0, 0.42] });
      C.player.glasses.visible = false;
      const rig = getPovRig(W.scene);
      rig.visible = true;
      rig.userData.arms.forEach((a) => (a.visible = false));
      const g = s2Glasses();
      rig.position.copy(g);
      rig.rotation.set(0, S2RY + Math.sin(t * 2) * 0.05, 0);
      rig.userData.glasses.position.set(0, 0, 0);
      rig.userData.glasses.rotation.set(0.15, 0, 0);
      rig.userData.glasses.scale.setScalar(1.0);
      getSparkles(W.scene);
      updateSparkles(g, t, 0.2);
      const tb2 = W.props.bgTables[3];
      tb2.position.set(S2P.x - 2.6, 0, S2P.z - 3.4); tb2.rotation.y = 0.9;
    },
    cam: (t) => {
      const lt = prog(t, 1.333, 2.467);
      const g = s2Glasses();
      const F = [Math.sin(S2RY), Math.cos(S2RY)], L = [Math.cos(S2RY), -Math.sin(S2RY)];
      const d = lerp(0.62, 0.58, lt);
      return { p: [g.x + F[0] * d - L[0] * 0.3, g.y + 0.2, g.z + F[1] * d - L[1] * 0.3], l: [g.x + L[0] * 0.02, g.y - 0.02, g.z + L[1] * 0.02], fov: 52, roll: -0.03 };
    },
  },
  // 3 — POV: putting the glasses on, push in on dealer + board, whip to the guards
  {
    t0: 2.467, t1: 7.467, set: 'casino', pov: true,
    setup(W, t, cam) {
      sidePlayers(W, t);
      const C = W.cast;
      chips(W, 'pov3', (root) => {
        pileAt(root, -0.75, 0.1, [{ x: 0, z: 0, n: 10 }, { x: 0.07, z: 0.02, n: 7 }], 3);
        pileAt(root, 0.72, -0.4, [{ x: 0, z: 0, n: 8 }, { x: 0.07, z: 0.0, n: 5 }], 4);
        pileAt(root, 0.15, 0.25, [{ x: 0, z: 0, n: 6 }], 5);
      });
      // guards waiting off to the right
      if (t > 6.3) {
        show(C.guard, 1.25, 1.0, -1.5, { ...POSES.stand, rShoulder: [-0.5, 0, -0.2], rElbow: [-1.2, 0, 0.3] });
        show(C.guard2, 2.05, 0.28, -1.35, POSES.handsBack);
      }
      // glasses rising into view, held by both hands
      const rig = getPovRig(W.scene);
      const k = prog(t, 2.467, 3.55);
      rig.visible = t < 3.6;
      if (rig.visible) {
        rig.position.copy(cam.position);
        rig.quaternion.copy(cam.quaternion);
        const e = easeInOut(k);
        const gy = lerp(-0.42, -0.005, e), gz = lerp(-0.42, -0.06, easeIn(k));
        const g = rig.userData.glasses;
        g.position.set(0.0, gy, gz);
        g.rotation.set(lerp(0.5, 0, e), 0, 0);
        g.scale.setScalar(1.25);
        rig.userData.arms.forEach((a, i) => {
          const side = i === 0 ? -1 : 1;
          a.visible = true;
          a.position.set(side * lerp(0.17, 0.115, e), gy - 0.05, gz + 0.02);
          a.rotation.set(lerp(-0.9, -0.2, e), side * -0.35, 0);
        });
        getSparkles(W.scene);
        const sp = new THREE.Vector3(0, gy, gz).applyQuaternion(cam.quaternion).add(cam.position);
        updateSparkles(sp, t, 0.22, t < 3.4);
      }
    },
    cam: (t) => {
      const p = keys(t, [[2.467, [0.0, 1.33, 1.95]], [3.7, [0.0, 1.33, 1.92]], [4.0, [-0.05, 1.45, 0.82], easeOut], [6.35, [0.0, 1.46, 0.7]], [6.85, [0.05, 1.52, 0.55], easeInOut], [7.467, [0.06, 1.52, 0.56]]]);
      const l = keys(t, [[2.467, [0.12, 1.08, -1.6]], [3.7, [0.15, 1.1, -1.6]], [4.0, [0.38, 1.3, -2.0], easeOut], [5.6, [0.48, 1.4, -2.0]], [6.35, [0.52, 1.42, -2.0]], [6.85, [1.2, 1.55, 0.72], easeInOutQuint], [7.467, [1.2, 1.55, 0.74]]]);
      const s = shake(t, 3, 0.012);
      return { p: [p[0] + s, p[1] + s * 0.5, p[2]], l, fov: t < 3.7 ? 64 : keys(t, [[3.7, 64], [4.0, 58], [6.35, 56], [6.85, 60]]), fill: t > 6.5 ? 1 : 0 };
    },
  },
  // 4 — POV low at the table: first bets, the rake
  {
    t0: 7.467, t1: 11.25, set: 'casino', pov: true,
    setup(W, t) {
      sidePlayers(W, t);
      const C = W.cast;
      show(C.player, SEAT.x, SEAT.z, Math.PI, POSES.sitTable);
      hideHead(C.player);
      const reach = keys(t, [[7.467, 1], [8.2, 1], [8.7, 0]]);
      C.player.setPose(blendPose(POSES.sitTable, { ...POSES.sitTable, rShoulder: [-1.25, 0.2, 0.1], rElbow: [-0.35, 0, 0] }, reach));
      const stage = t < 9.6 ? 'a' : 'b';
      chips(W, 'pov4' + stage, (root) => {
        const r = spot('red');
        pileAt(root, r.x + 0.02, r.z - 0.02, [{ x: 0, z: 0, n: 9 }, { x: 0.05, z: 0.03, n: 6 }], 7);
        pileAt(root, -0.72, 0.2, [{ x: 0, z: 0, n: 7 }, { x: 0.06, z: 0.03, n: 5 }], 8);
        pileAt(root, 0.72, -0.3, [{ x: 0, z: 0, n: 8 }], 9);
        pileAt(root, 0.0, 0.32, [{ x: 0, z: 0, n: 5 }], 10);
        if (stage === 'b') pileAt(root, 0.02, 1.12, [{ x: -0.05, z: 0, n: 8 }, { x: 0.04, z: 0.03, n: 6 }, { x: 0.0, z: -0.06, n: 4 }], 11);
      });
      // dealer rakes the winnings towards you
      const rk = prog(t, 9.6, 11.0);
      if (rk > 0 && rk < 1) {
        const rake = W.props.rake;
        rake.visible = true;
        rake.position.set(0.05, TABLE.H + 0.04, lerp(-1.6, -0.6, easeInOut(rk)));
        rake.rotation.set(0, 0, 0);
        W.dealerNow.setPose({ ...POSES.dealer, spine: [0.45, 0, 0], rShoulder: [-1.2, 0, -0.1], rElbow: [-0.2, 0, 0], lShoulder: [-1.2, 0, 0.1], lElbow: [-0.2, 0, 0] });
      }
    },
    cam: (t) => {
      const p = keys(t, [[7.467, [0.0, 1.14, 1.64]], [11.25, [0.0, 1.17, 1.58]]]);
      const s = shake(t, 4, 0.01);
      return { p: [p[0] + s, p[1], p[2]], l: keys(t, [[7.467, [0.0, 1.02, -1.5]], [9.0, [0.0, 1.06, -1.5]], [11.25, [0.02, 0.98, -1.4]]]), fov: 66 };
    },
  },
  // 5 — wheel close-up
  {
    t0: 11.25, t1: 12.6, set: 'casino',
    setup(W, t) { sidePlayers(W, t); },
    cam: (t) => {
      const a = lerp(-0.25, -0.1, prog(t, 11.25, 12.6));
      const R = 0.8;
      return { p: [Math.sin(a) * R, 1.42, -1.08 + Math.cos(a) * R], l: [0.0, 0.82, -1.14], fov: 52, roll: 0.05 };
    },
  },
  // 6 — POV: big stacks, suspicion starts, push in on the dealer
  {
    t0: 12.6, t1: 14.3, set: 'casino', pov: true,
    setup(W, t) {
      sidePlayers(W, t);
      const C = W.cast;
      show(C.player, SEAT.x, SEAT.z, Math.PI, POSES.sitTable);
      hideHead(C.player);
      chips(W, 'pov6', (root) => {
        const b = spot('black');
        pileAt(root, b.x, b.z - 0.05, [{ x: -0.045, z: 0, n: 30 }, { x: 0.045, z: 0.0, n: 28 }], 12);
        pileAt(root, -0.72, 0.2, [{ x: 0, z: 0, n: 7 }], 13);
        pileAt(root, 0.72, -0.3, [{ x: 0, z: 0, n: 8 }], 14);
      });
      W.dealerNow.J.neck.rotation.y = 0;
      W.dealerNow.J.head.rotation.x = 0.1;
    },
    cam: (t) => {
      const p = keys(t, [[12.6, [0.0, 1.2, 1.98]], [13.25, [0.0, 1.24, 1.75]], [13.55, [0.02, 1.38, 0.2], easeInOut], [14.3, [0.03, 1.4, 0.05]]]);
      const l = keys(t, [[12.6, [0.0, 1.05, -1.5]], [13.25, [0.0, 1.1, -1.6]], [13.55, [0.03, 1.38, -1.8], easeInOut], [14.3, [0.03, 1.38, -1.8]]]);
      return { p, l, fov: keys(t, [[12.6, 64], [13.55, 50]]) };
    },
  },
  // 7 — the dealer's face, the pit manager by the bar
  {
    t0: 14.3, t1: 19.533, set: 'casino',
    setup(W, t) {
      const C = W.cast;
      const d = W.dealerNow;
      show(d, 0.42, 4.3, 2.85, POSES.handsBack);
      d.J.neck.rotation.set(0.12, keys(t, [[14.3, 0.25], [15.0, -0.15], [17.3, -0.1], [17.6, 0.3], [18.4, 0.2], [19.0, -0.6]]), 0.1);
      const walk = prog(t, 18.0, 19.533);
      const px = lerp(0.62, 1.95, walk);
      show(C.pit, px, 6.95, walk > 0 ? Math.PI / 2 + 0.3 : Math.PI, walk > 0 ? walkPose(t * 0.9) : POSES.handOnHip);
      show(C.guard3, -0.6, 7.3, Math.PI, POSES.stand);
      C.guard3.root.visible = t > 18.0;
      const tb = W.props.bgTables[3];
      tb.position.set(0.4, 0, 6.15); tb.rotation.y = 1.45;
      // face light pulses: dealer face lit, then in shadow while the pit manager is shown, then lit again
      W.extraLights = { faceLight: keys(t, [[14.3, 1], [14.95, 1], [15.1, 0.04], [17.3, 0.04], [17.5, 1], [18.3, 1], [18.6, 0.2]], smooth) };
    },
    cam: (t) => {
      const p = keys(t, [[14.3, [0.62, 1.66, 3.55]], [17.4, [0.6, 1.64, 3.5]], [18.4, [0.62, 1.62, 3.52]], [19.533, [1.0, 1.45, 3.75]]]);
      const l = keys(t, [[14.3, [0.0, 1.32, 7.6]], [17.4, [0.0, 1.32, 7.6]], [18.4, [0.2, 1.32, 7.6]], [19.533, [1.9, 1.1, 7.2]]]);
      return { p, l, fov: 58 };
    },
  },
  // 8 — chips placed, sweep across the layout to the wheel
  {
    t0: 19.533, t1: 21.733, set: 'casino',
    setup(W, t) {
      sidePlayers(W, t);
      const C = W.cast;
      show(C.player, SEAT.x, SEAT.z, Math.PI, POSES.sitTable);
      hideHead(C.player);
      const k = easeInOut(prog(t, 19.55, 20.35));
      C.player.setPose(blendPose({ ...POSES.sitTable, rShoulder: [-1.15, 0.35, -0.1], rElbow: [-0.5, 0, 0], lShoulder: [-1.0, -0.3, 0.2], lElbow: [-0.7, 0, 0] },
        { ...POSES.sitTable, rShoulder: [-1.35, 0.25, 0.1], rElbow: [-0.15, 0, 0], lShoulder: [-1.2, -0.2, 0.25], lElbow: [-0.4, 0, 0] }, k));
      chips(W, 'pov8', (root) => {
        const r = spot('red');
        pileAt(root, r.x + 0.04, r.z - 0.02, [{ x: -0.03, z: 0, n: 14 }, { x: 0.04, z: 0.02, n: 12 }], 15);
        pileAt(root, 0.13, 0.05, [{ x: 0, z: 0, n: 6 }], 16);
      });
    },
    cam: (t) => {
      const p = keys(t, [[19.533, [-0.95, 1.55, 1.55]], [20.35, [-0.85, 1.5, 1.45]], [20.75, [0.1, 1.22, 0.35], easeInOut], [21.2, [0.05, 1.45, -0.42], easeInOut], [21.733, [0.02, 1.48, -0.45]]]);
      const l = keys(t, [[19.533, [-0.25, 0.8, 1.12]], [20.35, [-0.22, 0.8, 1.05]], [20.75, [0.08, 0.8, -0.15], easeInOut], [21.2, [0.0, 0.82, -1.06], easeInOut], [21.733, [0.0, 0.82, -1.08]]]);
      return { p, l, fov: 56, roll: keys(t, [[19.533, 0.75], [20.35, 0.8], [20.75, 0.6], [21.2, 0.15]]) };
    },
  },
  // 9 — POV: surveillance gets pinged (security guard with "!")
  {
    t0: 21.733, t1: 23.467, set: 'casino', pov: true,
    setup(W, t) {
      sidePlayers(W, t);
      const C = W.cast;
      show(C.guard, -0.95, -3.0, 0.25, POSES.walkie);
      walkie = walkie || (() => { const w = makeWalkie(); W.scene.add(w); return w; })();
      attach(W.scene, walkie, C.guard, 'rWrist', V(0, -0.1, 0.03), new THREE.Euler(0, 0, 0));
      const b = getBang(W.scene);
      b.visible = t > 21.85;
      C.guard.root.updateMatrixWorld(true);
      const hp = new THREE.Vector3();
      C.guard.J.head.localToWorld(hp.set(0.18, 0.36 + Math.sin(t * 6) * 0.015, 0));
      b.position.copy(hp);
      b.scale.setScalar(1.0 + 0.15 * Math.max(0, 1 - (t - 21.85) * 5));
      chips(W, 'pov9', (root) => {
        const r = spot('red');
        pileAt(root, r.x - 0.04, r.z - 0.08, [{ x: 0, z: 0, n: 18 }, { x: 0.07, z: -0.02, n: 16 }, { x: 0.03, z: 0.07, n: 10, color: REDC }], 17);
        pileAt(root, -0.75, 0.0, [{ x: 0, z: 0, n: 8 }], 18);
      });
    },
    cam: (t) => {
      const p = keys(t, [[21.733, [-0.05, 1.22, 1.8]], [23.467, [-0.12, 1.28, 1.25]]], smooth);
      const l = keys(t, [[21.733, [-0.15, 1.3, -1.9]], [23.467, [-0.45, 1.45, -2.2]]], smooth);
      return { p, l, fov: 60 };
    },
  },
  // 10 — the eye in the sky: dome camera, your reflection appears
  {
    t0: 23.467, t1: 25.5, set: 'casino', dome: true,
    setup(W, t) {
      W.domeReflect = clamp((t - 24.1) * 2.5);
    },
    cam: (t) => {
      const d = W_DOME;
      const p = keys(t, [[23.467, [d.x - 1.45, d.y - 0.32, d.z + 0.1]], [25.5, [d.x - 0.95, d.y - 0.26, d.z + 0.05]]], smooth);
      return { p, l: [d.x, d.y - 0.2, d.z], fov: 55 };
    },
  },
  // 11 — surveillance room, push into a monitor
  {
    t0: 25.5, t1: 27.3, set: 'surv',
    setup(W, t) {
      const C = W.cast;
      show(C.operator, SURV.x - 0.2, SURV.z - 0.85, Math.PI, POSES.typing);
      show(C.guard2, SURV.x - 2.6, SURV.z - 0.4, 0.6, POSES.handsBack);
    },
    cam: (t) => {
      const p = keys(t, [[25.5, [SURV.x - 2.1, 1.45, SURV.z + 1.2]], [27.0, [SURV.x - 1.55, 1.38, SURV.z + 0.6]], [27.3, [SURV.x - 0.2, 1.3, SURV.z - 1.7], easeIn]]);
      const l = keys(t, [[25.5, [SURV.x + 2.0, 1.4, SURV.z - 2.2]], [27.0, [SURV.x + 1.8, 1.35, SURV.z - 2.3]], [27.3, [SURV.x + 0.3, 1.3, SURV.z - 2.6]]]);
      return { p, l, fov: keys(t, [[25.5, 62], [27.0, 60], [27.3, 42]]) };
    },
  },
  // 12 — CCTV Cam 5: you at the table from above
  {
    t0: 27.3, t1: 28.2, set: 'casino', cctv: { cam: 'Cam 5', tc: (t) => 22 * 3600 + 9 * 60 + 16 + 0.3 + (t - 27.3) },
    setup(W, t) {
      sidePlayers(W, t);
      const C = W.cast;
      show(C.player, SEAT.x, SEAT.z, Math.PI, { ...POSES.sitTable, rShoulder: [-0.9, 0, -0.3], rElbow: [-0.9, 0.3, 0] });
      chips(W, 'cam5', (root) => {
        const b = spot('black');
        pileAt(root, b.x - 0.05, b.z - 0.15, [{ x: -0.04, z: 0, n: 12, color: REDC }, { x: 0.05, z: 0.0, n: 16 }, { x: 0.0, z: -0.07, n: 10 }], 19);
        pileAt(root, -0.7, 0.0, [{ x: 0, z: 0, n: 8 }], 20);
      });
    },
    cam: (t) => ({ p: [-1.6, 2.4, 0.5], l: [0.15, 1.0, 1.75], fov: 46, fill: 0.6 }),
  },
  // 13 — CCTV Cam 11: chips + hand, rewinding the tape
  {
    t0: 28.2, t1: 30.0, set: 'casino',
    cctv: {
      cam: 'Cam 11',
      tc: (t) => 22 * 3600 + 9 * 60 + 17 + (t < 28.6 ? lerp(13, 1, prog(t, 28.2, 28.6)) : 1 + (t - 28.6) * 9) / 30,
      rewind: (t) => t > 28.35 && t < 28.65,
    },
    setup(W, t) {
      const C = W.cast;
      show(C.player, SEAT.x, SEAT.z, Math.PI, POSES.sitTable);
      const reach = t < 28.6 ? keys(t, [[28.2, 1], [28.6, 0]]) : keys(t, [[28.6, 0], [29.4, 1]]);
      C.player.setPose(blendPose(POSES.sitTable, { ...POSES.sitTable, lShoulder: [-1.4, -0.35, 0.25], lElbow: [-0.1, 0, 0] }, reach));
      chips(W, 'cam11', (root) => {
        const b = spot('black');
        pileAt(root, b.x - 0.03, b.z - 0.05, [{ x: 0, z: 0, n: 11, color: REDC }], 21);
        pileAt(root, b.x + 0.12, b.z + 0.2, [{ x: 0, z: 0, n: 16 }, { x: 0.08, z: -0.03, n: 18 }, { x: -0.04, z: -0.09, n: 10, color: REDC }], 22);
      });
    },
    cam: (t) => ({ p: [-1.0, 1.15, 1.0], l: [0.1, 0.84, 1.24], fov: 46 }),
  },
  // 14 — the same feed seen as pixels on the CRT
  {
    t0: 30.0, t1: 30.42, set: 'casino', screen: true,
    setup(W, t) {
      SHOTS[12].setup(W, t);
    },
    cam: (t) => ({ p: [-1.0, 1.15, 1.0], l: [0.1, 0.84, 1.24], fov: lerp(36, 46, prog(t, 30.0, 30.42)), roll: 0.08 }),
  },
  // 15 — surveillance room: two operators lit by the monitors
  {
    t0: 30.42, t1: 32.233, set: 'surv',
    setup(W, t) {
      const C = W.cast;
      show(C.operator, SURV.x - 0.15, SURV.z - 0.85, Math.PI - 0.15, POSES.typing);
      show(C.operator2, SURV.x - 1.1, SURV.z - 0.75, 0.75, POSES.handsBack);
    },
    cam: (t) => {
      const p = keys(t, [[30.42, [SURV.x - 1.75, 1.05, SURV.z + 1.0]], [32.233, [SURV.x - 1.6, 1.08, SURV.z + 0.9]]]);
      const l = keys(t, [[30.42, [SURV.x + 0.4, 1.55, SURV.z - 2.0]], [32.233, [SURV.x + 0.6, 1.55, SURV.z - 2.0]]]);
      return { p, l, fov: 62, roll: -0.04 };
    },
  },
  // 16 — top view of the wheel
  {
    t0: 32.233, t1: 34.0, set: 'casino',
    setup(W, t) { sidePlayers(W, t); },
    cam: (t) => {
      const a = lerp(0.3, 0.05, prog(t, 32.233, 34.0));
      return { p: [0.38 + Math.sin(a) * 0.1, 2.6, -0.62], l: [0.07, 0.8, -1.1], fov: 52, roll: a };
    },
  },
  // 17 — fast move over the layout numbers
  {
    t0: 34.0, t1: 34.42, set: 'casino',
    setup(W, t) {
      chips(W, 'num17', (root) => {
        pileAt(root, 0.3, -0.75, [{ x: 0, z: 0, n: 5 }], 23);
        pileAt(root, -0.15, -0.3, [{ x: 0, z: 0, n: 3 }], 24);
      });
    },
    cam: (t) => {
      const k = prog(t, 34.0, 34.42);
      return { p: [lerp(0.1, 0.0, k), 1.22, lerp(-0.25, -0.12, k)], l: [lerp(0.0, -0.05, k), 0.8, lerp(-0.6, -0.45, k)], fov: 48, roll: 0.75 };
    },
  },
  // 18 — dealer rakes the stacks towards you (top-down)
  {
    t0: 34.42, t1: 36.5, set: 'casino',
    setup(W, t) {
      const C = W.cast;
      show(C.player, SEAT.x, SEAT.z, Math.PI, { ...POSES.sitTable, lShoulder: [-0.9, 0, 0.45], lElbow: [-0.6, 0, 0] });
      const k = easeInOut(prog(t, 34.6, 36.4));
      const rake = W.props.rake;
      rake.visible = t > 35.0;
      rake.position.set(0.32, TABLE.H + 0.035, lerp(-0.3, -0.05, k));
      rake.rotation.y = -0.45;
      chips(W, 'rake18' + (t > 35.0 ? 'b' : 'a'), (root) => {
        const b = spot('black');
        const dz = 0;
        pileAt(root, b.x - 0.2, b.z - 0.18 + dz, [{ x: 0, z: 0, n: 8 }], 25);
        pileAt(root, b.x - 0.08, b.z - 0.24, [{ x: 0, z: 0, n: 9, color: REDC }], 26);
        pileAt(root, b.x + 0.02, b.z - 0.16, [{ x: 0, z: 0, n: 7 }], 27);
        pileAt(root, b.x - 0.1, b.z - 0.08, [{ x: 0, z: 0, n: 10, color: REDC }], 28);
        if (t > 35.0) pileAt(root, b.x + 0.1, b.z - 0.32, [{ x: 0, z: 0, n: 8, color: REDC }], 29);
      });
    },
    cam: (t) => {
      const a = lerp(-0.1, 0.25, prog(t, 34.42, 36.5));
      return { p: [0.12, 1.45, 1.2], l: [-0.02, 0.8, 1.02], fov: 54, roll: 0.9 + a };
    },
  },
  // 19 — CCTV Cam 7: facial recognition on you
  {
    t0: 36.5, t1: 39.0, set: 'casino', faceTrack: true,
    cctv: { cam: 'Cam 7', tc: (t) => 22 * 3600 + 10 * 60 + 11 + 19 / 30 + (t - 36.5) },
    setup(W, t) {
      sidePlayers(W, t);
      const C = W.cast;
      show(C.player, SEAT.x, SEAT.z, Math.PI, POSES.sitTable);
      C.player.J.neck.rotation.set(keys(t, [[36.5, -0.1], [38.0, 0.15]]), keys(t, [[36.5, 0.2], [37.6, -0.15], [38.5, 0.3]]), 0);
    },
    cam: (t) => ({ p: keys(t, [[36.5, [-0.85, 1.56, 0.82]], [39, [-0.82, 1.56, 0.88]]]), l: [0.02, 1.12, 2.05], fov: 42, roll: 0.03, fill: 1 }),
  },
  // 20 — the suspect sheet held up in front of the Cam 7 monitor
  {
    t0: 39.0, t1: 40.233, set: 'surv', paper: true,
    setup(W, t) {},
    cam: (t) => ({ p: keys(t, [[39.0, [SURV.x + 0.36, 1.36, SURV.z - 1.3]], [40.233, [SURV.x + 0.38, 1.34, SURV.z - 1.5]]]), l: [SURV.x + 0.36, 1.3, SURV.z - 2.5], fov: 54 }),
  },
  // 21 — the operator compares the sheet with the screen
  {
    t0: 40.233, t1: 41.5, set: 'surv', paper: true,
    setup(W, t) {
      const C = W.cast;
      show(C.operator, SURV.x + 0.3, SURV.z - 0.72, Math.PI + 0.25, { ...POSES.typing, rShoulder: [-1.55, 0, -0.45], rElbow: [-0.45, 0, 0] });
      show(C.guard2, SURV.x - 0.9, SURV.z + 0.2, Math.PI / 2, POSES.handsBack);
    },
    cam: (t) => ({ p: keys(t, [[40.233, [SURV.x + 1.3, 1.05, SURV.z - 0.3]], [41.5, [SURV.x + 1.27, 1.06, SURV.z - 0.33]]]), l: [SURV.x + 0.05, 1.45, SURV.z - 2.3], fov: 62, roll: -0.08, fill: 0.5 }),
  },
  // 22 — top-down: a crowd gathers around the table
  {
    t0: 41.5, t1: 46.167, set: 'casino', topdown: true,
    setup(W, t) {
      const C = W.cast;
      sidePlayers(W, t);
      show(C.player, SEAT.x, SEAT.z, Math.PI, POSES.sitTable);
      crowdAround(W, t, { n: Math.round(lerp(14, 22, prog(t, 41.5, 44))) });
      show(C.guard, -0.6, -2.45, 0.3, POSES.handsBack);
      show(C.guard2, -1.2, -2.2, 0.5, POSES.handsBack);
      chips(W, 'top22', (root) => {
        const b = spot('black');
        pileAt(root, b.x, b.z - 0.05, [{ x: 0, z: 0, n: 10 }, { x: 0.06, z: 0, n: 8, color: REDC }], 30);
        pileAt(root, 0.1, -0.2, [{ x: 0, z: 0, n: 5 }], 31);
      });
    },
    cam: (t) => {
      const a = lerp(0.42, 0.32, prog(t, 41.5, 46.167));
      const h = lerp(9.6, 9.2, prog(t, 41.5, 46.167));
      return { p: [0.25, h, 0.05], l: [0.05, 0, -0.05], fov: 46, up: [Math.sin(a), 0, -Math.cos(a)] };
    },
  },
  // 23 — POV: the crowd copies your bets
  {
    t0: 46.167, t1: 50.733, set: 'casino', pov: true,
    setup(W, t) {
      const C = W.cast;
      show(C.player, SEAT.x, SEAT.z, Math.PI, POSES.sitTable);
      hideHead(C.player);
      show(C.ladyGreen, -0.98, 0.9, Math.PI / 2 + 0.6, { ...POSES.leanIn, lShoulder: [-1.4, 0, 0.1], rShoulder: [-1.0, 0, -0.3] });
      show(C.topHat, -1.0, 0.3, Math.PI / 2, POSES.leanIn);
      show(C.ladyRed, 0.98, -0.15, -Math.PI / 2, POSES.sitTable);
      crowdAround(W, t, { n: 18, lean: 0.9 });
      for (const i of [0, 2, 4]) W.crowd[i].root.visible = false;
      show(C.guard, -0.75, -2.35, 0.1, POSES.handsBack);
      show(C.guard3, 0.95, -1.95, -0.25, POSES.handsBack);
      chips(W, 'pov23' + (t > 47.6 ? 'b' : 'a'), (root) => {
        const b = spot('black');
        pileAt(root, b.x - 0.05, b.z - 0.05, [{ x: -0.04, z: 0, n: 18, color: REDC }, { x: 0.05, z: 0.02, n: 22, color: REDC }, { x: 0.0, z: -0.08, n: 15 }, { x: 0.1, z: -0.06, n: 12 }], 32);
        pileAt(root, 0.42, 1.0, [{ x: 0, z: 0, n: 8, color: REDC }, { x: 0.06, z: 0.03, n: 6, color: REDC }], 33);
        if (t > 47.6) pileAt(root, -0.22, 0.95, [{ x: 0, z: 0, n: 14, color: REDC }, { x: -0.06, z: 0.03, n: 10 }], 34);
        pileAt(root, -0.68, 0.1, [{ x: 0, z: 0, n: 9 }], 35);
        pileAt(root, 0.7, -0.4, [{ x: 0, z: 0, n: 9 }], 36);
      });
    },
    cam: (t) => {
      const p = keys(t, [[46.167, [0.0, 1.2, 1.82]], [50.733, [0.02, 1.24, 1.55]]], smooth);
      const s = shake(t, 23, 0.008);
      return { p: [p[0] + s, p[1], p[2]], l: keys(t, [[46.167, [0.05, 1.12, -1.6]], [50.733, [0.08, 1.2, -1.7]]], smooth), fov: 64 };
    },
  },
  // 24 — CCTV Cam 19: security swaps the dealer
  {
    t0: 50.733, t1: 56.9, set: 'casino',
    cctv: { cam: 'Cam 19', tc: (t) => 22 * 3600 + 10 * 60 + 13 + 17 / 30 + (t - 50.5) },
    setup(W, t) {
      const C = W.cast;
      sidePlayers(W, t);
      show(C.player, SEAT.x, SEAT.z, Math.PI, POSES.sitTable);
      crowdAround(W, t, { n: 20, lean: 0.4 });
      const old = C.dealer, nu = C.dealer2;
      // old dealer is led away to the left, new dealer walks in
      const out = prog(t, 51.6, 54.0);
      if (t < 54.2) {
        show(old, lerp(0.02, -1.6, easeIn(out)), lerp(-1.78, -2.6, out), out > 0 ? -1.3 : 0, out > 0 ? walkPose(t * 0.8) : POSES.dealer);
        show(C.guard2, lerp(-0.55, -2.0, easeIn(out)), lerp(-2.15, -2.9, out), out > 0 ? -1.4 : 0.5, out > 0 ? walkPose(t * 0.8 + 0.5) : { ...POSES.stand, rShoulder: [-0.9, 0, -0.4], rElbow: [-0.5, 0, 0] });
      } else { old.root.visible = false; }
      const inn = prog(t, 53.6, 55.6);
      if (t > 53.6) show(nu, lerp(-1.4, 0.02, easeOut(inn)), lerp(-2.7, -1.78, easeOut(inn)), inn < 1 ? 1.9 - inn * 1.9 : 0, inn < 1 ? walkPose(t * 0.8) : POSES.dealer);
      else nu.root.visible = false;
      show(C.guard, -0.95, -2.5, 0.4, POSES.handsBack);
      show(C.guard3, 1.35, -2.05, -0.5, POSES.handsBack);
      chips(W, 'cam19', (root) => {
        const b = spot('black');
        pileAt(root, b.x, b.z - 0.08, [{ x: -0.04, z: 0, n: 14, color: REDC }, { x: 0.05, z: 0.02, n: 18 }, { x: 0.0, z: -0.08, n: 12, color: REDC }], 37);
        pileAt(root, -0.6, 0.2, [{ x: 0, z: 0, n: 8 }], 38);
        pileAt(root, 0.62, -0.3, [{ x: 0, z: 0, n: 8 }], 39);
      });
    },
    cam: (t) => {
      if (t < 55.533) {
        const s = shake(t, 24, 0.01);
        return { p: [-2.55 + s, 3.15, 2.05], l: [-0.35, 1.0, -1.35], fov: 52 };
      }
      const k = easeInOut(prog(t, 55.533, 56.9));
      return { p: [lerp(-1.75, -1.15, k), lerp(2.7, 2.1, k), lerp(1.8, 1.4, k)], l: [lerp(-0.1, 0.05, k), 0.8, lerp(0.2, 0.6, k)], fov: lerp(52, 46, k) };
    },
  },
  // 25 — security radios management
  {
    t0: 56.9, t1: 58.067, set: 'surv',
    setup(W, t) {
      const C = W.cast;
      show(C.guard, SURV.x + 0.35, SURV.z + 0.35, 0.15, POSES.walkie);
      walkie = walkie || (() => { const w = makeWalkie(); W.scene.add(w); return w; })();
      attach(W.scene, walkie, C.guard, 'rWrist', V(0.0, -0.09, 0.04), new THREE.Euler(0, 0, 0.2));
    },
    cam: (t) => ({ p: keys(t, [[56.9, [SURV.x + 0.33, 1.66, SURV.z + 1.45]], [58.067, [SURV.x + 0.32, 1.66, SURV.z + 1.38]]]), l: [SURV.x + 0.38, 1.58, SURV.z + 0.3], fov: 44, fill: 1 }),
  },
  // 26 — the manager on the phone
  {
    t0: 58.067, t1: 59.4, set: 'office',
    setup(W, t) {
      const C = W.cast;
      show(C.manager, OFFICE.x, OFFICE.z - 0.35, 0, { ...POSES.phone, hipsY: 0.55, lHip: [-1.5, 0, 0], rHip: [-1.5, 0, 0], lKnee: [1.5, 0, 0], rKnee: [1.5, 0, 0], spine: [0.15, 0, 0], neck: [0.15, -0.1, 0.1] });
      phone = phone || (() => { const p = makePhone(); W.scene.add(p); return p; })();
      attach(W.scene, phone, C.manager, 'rWrist', V(0.0, -0.06, 0.03), new THREE.Euler(0, 0, 0));
    },
    cam: (t) => ({ p: keys(t, [[58.067, [OFFICE.x + 0.05, 1.38, OFFICE.z + 0.75]], [59.4, [OFFICE.x + 0.05, 1.38, OFFICE.z + 0.68]]]), l: [OFFICE.x, 1.3, OFFICE.z - 0.5], fov: 48 }),
  },
  // 27 — Cam 7 again
  {
    t0: 59.4, t1: 60.9, set: 'casino', faceTrack: true,
    cctv: { cam: 'Cam 7', tc: (t) => 22 * 3600 + 10 * 60 + 11 + 28 / 30 + (t - 59.5) },
    setup(W, t) {
      sidePlayers(W, t);
      const C = W.cast;
      show(C.player, SEAT.x, SEAT.z, Math.PI, POSES.sitTable);
      C.player.J.neck.rotation.set(0.25, keys(t, [[59.4, -0.4], [60.9, -0.1]]), 0);
      crowdAround(W, t, { n: 20, lean: 0.4 });
    },
    cam: (t) => ({ p: [-0.98, 1.56, 1.02], l: [-0.02, 1.12, 2.05], fov: 42, roll: 0.02, fill: 1 }),
  },
  // 28 — top-down crowd again
  {
    t0: 60.9, t1: 63.8, set: 'casino', topdown: true,
    setup(W, t) { SHOTS[21].setup(W, 46); },
    cam: (t) => {
      const a = lerp(0.3, 0.22, prog(t, 60.9, 63.8));
      return { p: [0.2, 9.0, 0.05], l: [0.05, 0, -0.05], fov: 46, up: [Math.sin(a), 0, -Math.cos(a)] };
    },
  },
  // 29 — POV: GREEN! the streak can't be luck
  {
    t0: 63.8, t1: 68.967, set: 'casino', pov: true,
    setup(W, t) {
      SHOTS[22].setup(W, t);
      const C = W.cast;
      show(C.guard2, -1.35, -2.1, 0.4, POSES.handsBack);
      chips(W, 'pov29', (root) => {
        pileAt(root, 0.42, 1.12, [{ x: 0, z: 0, n: 30, color: REDC }, { x: 0.07, z: 0.02, n: 34, color: REDC }, { x: 0.02, z: -0.07, n: 26, color: REDC }, { x: 0.09, z: -0.08, n: 22, color: REDC }], 40);
        pileAt(root, -0.05, 0.85, [{ x: 0, z: 0, n: 16, color: REDC }, { x: 0.06, z: 0.03, n: 12 }], 41);
        pileAt(root, -0.68, 0.1, [{ x: 0, z: 0, n: 9 }], 42);
        pileAt(root, 0.7, -0.4, [{ x: 0, z: 0, n: 9 }], 43);
      });
    },
    cam: (t) => {
      const p = keys(t, [[63.8, [0.0, 1.18, 1.82]], [68.967, [0.03, 1.22, 1.5]]], smooth);
      const s = shake(t, 29, 0.008);
      return { p: [p[0] + s, p[1], p[2]], l: keys(t, [[63.8, [0.04, 1.1, -1.6]], [68.967, [0.06, 1.18, -1.7]]], smooth), fov: 64 };
    },
  },
  // 30 — your photo joins the suspect sheet
  {
    t0: 68.967, t1: 71.133, set: 'surv', paper: true, polaroid: true,
    setup(W, t) {},
    cam: (t) => ({ p: keys(t, [[68.967, [SURV.x + 0.3, 1.32, SURV.z - 1.05]], [71.133, [SURV.x + 0.3, 1.3, SURV.z - 1.2]]]), l: [SURV.x + 0.3, 1.12, SURV.z - 2.4], fov: 54 }),
  },
  // 31 — security congratulates you and asks you to stop
  {
    t0: 71.133, t1: 76.6, set: 'casino', handshake: true,
    setup(W, t) {
      const C = W.cast;
      sidePlayers(W, t);
      crowdAround(W, t, { n: 12, lean: 0.8 });
      show(C.ladyGreen, -0.95, 2.35, Math.PI / 2 + 0.6, { ...POSES.leanIn, hipsY: 0.9 });
      const g = C.guard;
      let pose = POSES.stand;
      const shakeK = prog(t, 71.6, 72.2) * (1 - prog(t, 73.2, 73.6));
      const raise = prog(t, 73.4, 73.9) * (1 - prog(t, 75.7, 76.1));
      const point = prog(t, 75.8, 76.3);
      pose = blendPose(pose, { ...POSES.stand, rShoulder: [-0.95, 0.1, -0.15], rElbow: [-0.45, 0, 0] }, easeInOut(shakeK));
      pose = blendPose(pose, { ...POSES.stand, lShoulder: [-0.4, 0, 0.95], lElbow: [-1.6, 0, 0], lWrist: [0, 0.5, 0] }, easeInOut(raise));
      pose = blendPose(pose, { ...POSES.stand, lShoulder: [-1.45, 0, 0.7], lElbow: [-0.1, 0, 0] }, easeInOut(point));
      show(g, 0.62, 3.05, 0.05 + 0.3 * point, pose);
      g.J.neck.rotation.set(0, Math.sin(t * 0.9) * 0.1 + raise * 0.15, raise * 0.18 * Math.sin(t * 2));
      g.J.spine.rotation.z = raise * 0.08;
      // your hand reaching in for the handshake
      const rig = getPovRig(W.scene);
      rig.visible = shakeK > 0;
      rig.userData.glasses.visible = false;
    },
    cam: (t) => {
      const turn = easeIn(prog(t, 76.1, 76.6)) * 0.6;
      const s = shake(t, 31, 0.01);
      return { p: [0.7 + s, 1.6, 4.08], l: [lerp(0.6, 2.4, turn), lerp(1.52, 1.3, turn), lerp(3.0, 3.6, turn)], fov: 58, fill: 0.45 };
    },
  },
  // 32 — the camera pans across the floor to the claw machine
  {
    t0: 76.6, t1: 79.1, set: 'casino', claw: true,
    setup(W, t) {
      sidePlayers(W, t);
      const C = W.cast;
      show(C.guard, 0.62, 3.05, 0.35, { ...POSES.stand, lShoulder: [-1.45, 0, 0.7], lElbow: [-0.1, 0, 0] });
    },
    cam: (t) => {
      const c = W_CLAW;
      const k = easeInOut(prog(t, 76.6, 77.9));
      const d = easeOut(prog(t, 77.6, 79.1));
      return { p: [lerp(0.7, 2.35, d), lerp(1.6, 1.5, d), lerp(4.08, 4.55, d)], l: [lerp(2.4, c.x, k), lerp(1.3, 1.15, k), lerp(3.6, c.z, k)], fov: lerp(58, 50, d) };
    },
  },
];

export let W_DOME = V(0, 0, 0), W_CLAW = V(0, 0, 0);
export function setAnchors(dome, claw) { W_DOME = dome; W_CLAW = claw; }

export function findShot(t) {
  for (let i = SHOTS.length - 1; i >= 0; i--) if (t >= SHOTS[i].t0) return SHOTS[i];
  return SHOTS[0];
}

export function registerPaper(p, pol) { paper = p; polaroid = pol; }
export function getPaper() { return { paper, polaroid }; }
export { getPovRig };
