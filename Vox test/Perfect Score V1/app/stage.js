// Staging shared by the shots: shot-only props, the hero's movable desk (story
// continuity), seated classmates, the teacher at his desk. All pure functions of t.
import * as THREE from 'three';
import { POSES, blendPose, armIK, headLook, setGrip, SEAT_H, SIT_Y, STAND_Y, walkPose, strideLength } from './chars.js';
import { V3, clock, holdObj, setWorldMatrix, writeWith, placeChar, seated, handQuat, palmAt, local, look, curve, clamp, lerp, prog, easeInOut, smooth } from './anim.js';
import { CLASS, SEAT_BACK, HALL, OFFICE, HOME, BED, BED2, portraitTex } from './world.js';
import * as P from './props.js';
import { makePaper, paperWorld } from './paper.js';
import { noise1, hash, easeOut } from './util.js';

export const X = { all: [] };
export let W = null, C = null, K = null, PR = null;
const reg = (o, parent) => { (parent || W.scene).add(o); X.all.push(o); o.visible = false; return o; };

export function initStage(world) {
  W = world; C = world.cast; K = world.kids; PR = world.props;
  // ---- papers
  X.p1 = makePaper({ kind: 'test', name: 'Adam', hand: 0 }); reg(X.p1.group);
  X.pDone = makePaper({ kind: 'test', name: 'Adam', hand: 1 }); X.pDone.setState({ score: 1, ticks: 6 }); reg(X.pDone.group);
  X.pStack = []; // papers 2..5 share the graded texture
  for (let i = 0; i < 4; i++) { const m = new THREE.Mesh(X.pDone.mesh.geometry, X.pDone.mesh.material); m.castShadow = m.receiveShadow = true; const gr = new THREE.Group(); gr.add(m); reg(gr); X.pStack.push(gr); }
  X.pFinal = makePaper({ kind: 'final', name: 'Adam', hand: 2 }); reg(X.pFinal.group);
  X.pRetake = makePaper({ kind: 'retake', name: 'Adam', hand: 3 }); reg(X.pRetake.group);
  X.pSmart = makePaper({ kind: 'final', name: 'Omar', hand: 4 }); X.pSmart.setState({ bonus: 0, answers: 1, ticks: 3, score: 1, scoreText: '78' }); reg(X.pSmart.group);
  X.pGirl = makePaper({ kind: 'test', name: 'Maryam', hand: 5 }); X.pGirl.setState({ score: 1, scoreText: '92', ticks: 5 }); reg(X.pGirl.group);
  X.kidTest = makePaper({ kind: 'test', name: 'Sam', hand: 6 }); X.kidTest.setState({ answers: 0.55 });
  X.kidFinal = makePaper({ kind: 'final', name: 'Sam', hand: 7 }); X.kidFinal.setState({ answers: 0.45, bonus: 0 });
  X.kidPapers = []; X.kidPencils = [];
  for (let i = 0; i < 20; i++) {
    const m = new THREE.Mesh(X.kidTest.mesh.geometry, X.kidTest.mesh.material); m.castShadow = m.receiveShadow = true;
    const gr = new THREE.Group(); gr.add(m); reg(gr); X.kidPapers.push(gr);
    X.kidPencils.push(reg(P.pencil()));
  }
  // smart kid photo clipped to his paper
  {
    const tex = portraitTex({ skin: '#e9c4a4', hair: '#4a2c18', hairStyle: 'slick', seed: 606 }, 'Omar K.', null);
    const ph = new THREE.Mesh(new THREE.PlaneGeometry(0.06, 0.0714), new THREE.MeshStandardMaterial({ map: tex, roughness: 0.6, polygonOffset: true, polygonOffsetFactor: -4 }));
    ph.rotation.x = -Math.PI / 2; ph.position.set(-0.055, 0.0012, -0.1); ph.rotation.z = 0.08;
    X.pSmart.group.add(ph);
    const clip = new THREE.Mesh(new THREE.BoxGeometry(0.008, 0.002, 0.03), new THREE.MeshStandardMaterial({ color: '#c8c8cc', metalness: 0.9, roughness: 0.25 }));
    clip.position.set(-0.055, 0.002, -0.135); X.pSmart.group.add(clip);
  }
  // pens and pencils
  X.heroPencil = reg(P.pencil());
  X.redPen = reg(P.redPen());
  X.carryStack = reg(P.stackOfPapers(10, 21));
  X.examSlam = reg(P.stackOfPapers(34, 22));
  X.mug = PR.mug;
  // office search props
  X.bagO = reg(P.backpack('#b82020'));
  X.pcase = reg(P.pencilCase('#1c3a6a'));
  X.bottle = reg(P.waterBottle());
  X.nb1 = reg(P.notebook('#2a5a9a', 0.014)); X.nb2 = reg(P.notebook('#2a8a5a', 0.012));
  X.envelope = reg(P.envelope('FINAL EXAM — RETAKE'));
  X.stamp = reg(P.rubberStamp());
  X.retakePencil = reg(P.pencil());
  X.heroFrame = reg(P.framedPicture(portraitTex({ skin: '#c99a74', hair: '#1c120c', seed: 101 }, 'Adam R.', 'STUDENT OF THE YEAR'), 0.42, 0.5, '#3a2410'));
  X.dadPhone = PR.phone;
  // office wall clock (time-lapse shot)
  X.officeClock = P.wallClock(); X.officeClock.position.set(OFFICE.x1 - 0.02, 2.3, 1.2); X.officeClock.rotation.y = -Math.PI / 2; W.sets.office.group.add(X.officeClock);
  // spare chair for the hero's front desk (tucked under the moving desk otherwise)
  X.heroDeskChairTuck = true;
  // classroom CCTV feed rendered for the principal's monitor
  X.feedRT = new THREE.WebGLRenderTarget(768, 480);
  X.feedRT.texture.colorSpace = THREE.SRGBColorSpace;
  X.feedCam = new THREE.PerspectiveCamera(58, 768 / 480, 0.05, 30);
}

export function hideShotProps() { for (const o of X.all) o.visible = false; }
const show = (o) => { o.visible = true; return o; };

// ------------------------------------------------------------ hero desk ---
export const FWD_PATH = curve([[0, 1.0], [-0.12, 0.62], [-0.62, 0.3], [-0.75, -0.2], [-0.75, -1.05], [-0.85, -2.0], [-1.05, -2.6]]);
export const BACK_PATH = curve([[-1.05, -2.6], [-0.88, -2.05], [-0.75, -1.2], [-0.75, 1.6], [-0.7, 2.75], [-0.35, 3.3], [0, 3.6]]);
const FL = FWD_PATH.getLength(), BL = BACK_PATH.getLength();
// segments of the two moves (time-compressed across the cuts)
export const MOVE = {
  f1: [17.62, 18.95, 0, 1.3], f2: [18.95, 19.95, FL - 1.4, FL],
  b1: [75.85, 77.02, 0, 1.25], b2: [77.02, 78.05, BL - 1.45, BL],
};
function segS(t, [ta, tb, s0, s1], accel) {
  const k = clamp((t - ta) / (tb - ta));
  // accel: start at rest, leave at speed; decel: arrive at rest
  const f = accel ? (2 * k * k - k * k * k) : 1 - (1 - k) * (1 - k) * (1 + k);
  return s0 + (s1 - s0) * f;
}
// where the hero's desk is at story time t, and how it is being moved
export function heroDeskState(t) {
  const st = (path, s, mode, dir, seg) => {
    const L = path.getLength();
    const u = clamp(s / L);
    const p = path.getPointAt(u);
    const dt = 0.02;
    return { x: p.x, z: p.z, yaw: Math.PI + Math.sin(s * 2.1) * 0.035 * (mode === 'sit' ? 0 : 1), mode, s, dir, seg };
  };
  if (t < MOVE.f1[0]) return { x: 0, z: 1.0, yaw: Math.PI, mode: 'sit', spot: 'orig' };
  if (t < MOVE.f2[0]) return st(FWD_PATH, segS(t, MOVE.f1, true), 'push', -1, MOVE.f1);
  if (t < MOVE.f2[1]) return st(FWD_PATH, segS(t, MOVE.f2, false), 'push', -1, MOVE.f2);
  if (t < MOVE.b1[0]) return { x: -1.05, z: -2.6, yaw: Math.PI, mode: 'sit', spot: 'front' };
  if (t < MOVE.b2[0]) return st(BACK_PATH, segS(t, MOVE.b1, true), 'pushB', 1, MOVE.b1);
  if (t < MOVE.b2[1]) return st(BACK_PATH, segS(t, MOVE.b2, false), 'pushB', 1, MOVE.b2);
  return { x: 0, z: 3.6, yaw: Math.PI, mode: 'sit', spot: 'back' };
}
export function placeHeroUnit(t) {
  const d = heroDeskState(t);
  const desk = PR.heroDesk, chair = PR.heroChair, bag = PR.heroBag;
  desk.position.set(d.x, 0, d.z); desk.rotation.set(0, d.yaw, 0);
  desk.updateMatrixWorld(true);
  // chair: pulled out (sitting) or tucked under the desk (moving) - in desk-local coords
  const sitting = d.mode === 'sit';
  const cz = sitting ? -SEAT_BACK : -0.2;
  const cp = V3(0, 0, cz).applyMatrix4(desk.matrixWorld);
  chair.position.copy(cp); chair.rotation.set(0, d.yaw, 0);
  chair.updateMatrixWorld(true);
  // bag hangs on the chair back
  const bp = V3(0, 0.27, -0.33).applyMatrix4(chair.matrixWorld);
  bag.position.copy(bp); bag.rotation.set(-0.08, d.yaw + Math.PI, 0);
  bag.visible = true;
  return d;
}
export function heroSeatOf(d) {
  // seat (hips) position for a desk state
  const yaw = d.yaw;
  return { x: d.x - Math.sin(yaw) * SEAT_BACK, z: d.z - Math.cos(yaw) * SEAT_BACK, heading: yaw };
}

// --------------------------------------------------------------- seats ---
// classmates: every seat except the hero's; the smart kid has a fixed seat
export function seatAssignments() {
  if (X.seatMap) return X.seatMap;
  const map = [];
  let k = 0;
  W.class.seats.forEach((s, i) => {
    if (s.hero) return;
    if (s.ci === 3 && s.ri === 1) { map.push({ seat: s, ch: C.smart, idx: i }); return; }
    map.push({ seat: s, ch: K[k], idx: i, kid: k }); k++;
  });
  // Maryam (kid1, in a hijab) sits on your left
  const nb = map.find((m) => m.seat.ci === 1 && m.seat.ri === 2), m1 = map.find((m) => m.ch === K[1]);
  if (nb && m1 && nb !== m1) { const c = nb.ch; nb.ch = m1.ch; m1.ch = c; }
  X.seatMap = map;
  return map;
}
export function kidSeatOf(name) { return seatAssignments().find((m) => m.ch === C[name] || m.ch.name === name); }
const KID_SEAT_H = SEAT_H * 0.9;

// a pencil tip that wanders over a sheet like handwriting (continuous in t)
export function scribbleLocal(t, seed, amp = 1) {
  const ph = t * 0.21 + seed * 0.37;
  const x = 0.06 * Math.sin(2 * Math.PI * ph) + 0.004 * Math.sin(t * 21 + seed);
  const z = -0.02 + 0.045 * Math.sin(t * 0.13 + seed * 1.7) + 0.002 * Math.sin(t * 17 + seed * 3);
  const lift = Math.max(0, Math.sin(t * 3.1 + seed * 5)) * 0.004;
  return V3(x * amp, 0.0006 + lift, z);
}

// seated student writing at a desk; returns handy points
export function seatedWriter(ch, x, z, heading, paperObj, pencilObj, t, seed, o = {}) {
  const pose = seated(o.pose || POSES.sitDesk, ch, o.seatH ?? KID_SEAT_H);
  placeChar(ch, x, z, heading, pose);
  // paper on the desk in front, page top away from the writer
  const deskZ = 0.42;
  if (paperObj) {
    const pp = local(ch, 0.02 + (hash(seed, 2) - 0.5) * 0.04, 0.661, deskZ - 0.02);
    paperObj.position.copy(pp); paperObj.rotation.set(0, heading + Math.PI + (hash(seed, 3) - 0.5) * 0.2, 0);
    paperObj.visible = true; paperObj.updateMatrixWorld(true);
  }
  let tip = null;
  if (o.write !== false && paperObj && pencilObj) {
    tip = o.tip ? o.tip : scribbleLocal(t, seed, o.amp ?? 1).applyMatrix4(paperObj.matrixWorld);
    pencilObj.visible = true;
    writeWith(ch, 'r', pencilObj, tip, 1, 0, local(ch, -0.5, 0.75, -0.2));
  }
  // left hand rests flat on the desk beside the sheet
  if (o.leftHand !== false) palmAt(ch, 'l', local(ch, 0.16, 0.668, deskZ - 0.05), handQuat(ch, [-0.3, 0, 1], [0, -1, 0]), 1, local(ch, 0.6, 0.6, -0.3), 0.15);
  return { tip };
}

export function stageKids(t, o = {}) {
  const map = seatAssignments();
  const paperTex = o.paper === 'final' ? X.kidFinal.mesh.material : X.kidTest.mesh.material;
  map.forEach((m, i) => {
    const { seat, ch } = m;
    if (o.skip && o.skip.includes(ch)) return;
    const paper = X.kidPapers[i];
    paper.children[0].material = paperTex;
    const mode = typeof o.mode === 'function' ? o.mode(m, i) : (o.mode || 'write');
    const seed = i * 1.37 + 0.5;
    if (mode === 'crane') {
      // turned round in the seat, straining to see the hero's paper at the back
      const k = o.craneK ? o.craneK(m, i) : 1;
      const pose = seated({ ...POSES.sitDesk, spine: [lerp(0.16, -0.05, k), lerp(0, 0.75, k) * (seat.x <= 0.01 ? -1 : 1), 0], neck: [0, 0, 0] }, ch, KID_SEAT_H);
      placeChar(ch, seat.x, seat.z, Math.PI, pose);
      paper.position.copy(local(ch, 0.02, 0.661, 0.4)); paper.rotation.set(0, 0, 0); paper.visible = true;
      const sd = seat.x <= 0.01 ? -1 : 1; // turning towards +x (right hand back) or -x (left hand back)
      const back = sd < 0 ? 'r' : 'l', front = sd < 0 ? 'l' : 'r';
      palmAt(ch, front, local(ch, -sd * 0.16, 0.668, 0.37), handQuat(ch, [sd * 0.3, 0, 1], [0, -1, 0]), 1, local(ch, -sd * 0.6, 0.6, -0.2), 0.15);
      palmAt(ch, back, local(ch, sd * 0.13, KID_SEAT_H + 0.385, -0.2), handQuat(ch, [sd * 0.2, -0.4, -1], [0, -1, 0]), k, local(ch, sd * 0.7, 0.7, 0.1), 0.6);
      // right arm hooks over the chair back when turned
      if (o.target) look(ch, o.target, k, 0.9);
      ch.expr = k > 0.5 ? (hash(i, 4) < 0.5 ? 'surprised' : 'focus') : 'neutral';
      return;
    }
    const wr = mode === 'write' || mode === 'look';
    seatedWriter(ch, seat.x, seat.z, Math.PI, paper, X.kidPencils[i], t, seed, { write: wr, amp: mode === 'look' ? 0.2 : 1 });
    if (mode === 'write') {
      const tipP = scribbleLocal(t, seed).applyMatrix4(paper.matrixWorld);
      const glance = smooth(clamp((noise1(t * 0.35, seed * 9) - 0.55) * 5));
      look(ch, tipP, 1 - glance * 0.6, 0.8);
      if (glance > 0.01) ch.look = [ch.look[0], ch.look[1] * (1 - glance) - glance * 0.6];
    } else if (mode === 'look' && o.target) {
      const w = o.lookW ? o.lookW(m, i) : 1;
      const tipP = scribbleLocal(t, seed, 0.2).applyMatrix4(paper.matrixWorld);
      look(ch, tipP, 1, 0.8);
      look(ch, o.target, w, 0.9);
      if (o.expr) ch.expr = o.expr(m, i, w);
    } else if (mode === 'groan') {
      const k = o.groanK ? o.groanK(m, i) : 1;
      const pose = seated(blendPose(POSES.sitDesk, POSES.slump, k), ch, KID_SEAT_H);
      ch.setPose(pose); ch.idle(clock.t);
      palmAt(ch, 'l', local(ch, 0.16, 0.668, 0.37), handQuat(ch, [-0.3, 0, 1], [0, -1, 0]), 1 - k, null, 0.15);
      ch.expr = k > 0.3 ? 'worried' : 'neutral';
    }
  });
}

// teacher seated at his desk; hands resting or holding the red pen
export function teacherAtDesk(t, o = {}) {
  const T = C.teacher;
  const td = CLASS.tDesk;
  const pose = seated(o.pose || POSES.sitDesk, T, 0.48);
  placeChar(T, td.x + (o.dx || 0), td.z - 0.58, o.heading || 0, pose);
  if (o.hands !== false) {
    palmAt(T, 'l', local(T, 0.2, 0.775, 0.38), handQuat(T, [-0.25, 0, 1], [0, -1, 0]), 1, null, 0.2);
    palmAt(T, 'r', local(T, -0.2, 0.775, 0.38), handQuat(T, [0.25, 0, 1], [0, -1, 0]), 1, null, 0.2);
  }
  return T;
}

// the classroom in its default state at story time t
export function stageClass(t, o = {}) {
  W.class.seats.forEach((s) => (s.desk.visible = s.chair.visible = true));
  const d = placeHeroUnit(o.deskT ?? t);
  if (o.kids !== false) stageKids(t, o.kidsOpt || {});
  // whiteboard text depends on story time
  boardFor(t);
  PR.classClock.userData.set(10, 10 + t * 0.05, (t * 1) % 60);
  return d;
}
let lastBoard = '';
function boardFor(t) {
  const key = t < 22.8 ? 'test' : 'final';
  if (key === lastBoard) return;
  lastBoard = key;
  PR.board.userData.write((g, Wd, Hd) => {
    g.fillStyle = '#1c3a8a';
    g.font = 'italic bold 110px "Liberation Sans"';
    if (key === 'test') {
      g.fillText('Unit Test — Chapter 6', 90, 170);
      g.font = 'italic 70px "Liberation Sans"'; g.fillStyle = '#16161c';
      g.fillText('• No talking', 110, 300); g.fillText('• Show your working', 110, 400);
    } else {
      g.fillStyle = '#c0201a'; g.font = 'bold 150px "Liberation Sans"';
      g.fillText('FINAL EXAM', 90, 200);
      g.font = 'italic 70px "Liberation Sans"'; g.fillStyle = '#16161c';
      g.fillText('60 minutes  •  Bonus: +10', 110, 330);
      g.strokeStyle = '#c0201a'; g.lineWidth = 10; g.beginPath(); g.moveTo(90, 230); g.lineTo(1000, 230); g.stroke();
    }
  });
}
export { show };
