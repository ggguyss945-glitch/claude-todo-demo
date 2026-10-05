// Shot list, timed to the narration (script/words.json). Each shot: set, camera(t)
// and setup(world, t). Hands are driven by the objects they hold (object paths are
// authoritative), so props never float or pop.
import * as THREE from 'three';
import { POSES, blendPose, armIK, headLook, setGrip, SEAT_H, SIT_Y, STAND_Y, walkPose } from './chars.js';
import { V3, clock, holdObj, setWorldMatrix, writeWith, writingHandQuat, placeChar, seated, handQuat, palmAt, local, walkChar, curve, poseAt, look, camKeys, handheld, orbitCam, crossArms, handsBehind, clamp, lerp, prog, easeInOut, smooth } from './anim.js';
import { CLASS, SEAT_BACK, HALL, OFFICE, HOME, BED, BED2 } from './world.js';
import { X, W, C, K, PR, initStage, hideShotProps, placeHeroUnit, heroDeskState, heroSeatOf, stageClass, stageKids, seatAssignments, kidSeatOf, seatedWriter, teacherAtDesk, scribbleLocal, MOVE, FWD_PATH, BACK_PATH, show } from './stage.js';
import { paperWorld, PW, PH } from './paper.js';
import { easeOut, easeIn, noise1, hash } from './util.js';
import { drawCCTV, tcString } from './overlay.js';

export const SHOTS = [];
const S = (t0, t1, set, cam, setup, extra = {}) => SHOTS.push({ t0, t1, set, cam, setup, ...extra });
export function findShot(t) {
  for (const s of SHOTS) if (t >= s.t0 && t < s.t1) return s;
  return t < SHOTS[0].t0 ? SHOTS[0] : SHOTS[SHOTS.length - 1];
}
const ck = camKeys;
const OC = (t, target, yaw, pitch, dist, fov, extra = {}) => ({ ...orbitCam(target, yaw, pitch, dist, fov, extra), t });
const K3 = (t, p, l, fov = 40, extra = {}) => ({ t, p, l, fov, ...extra });
const Q = new THREE.Quaternion();
const E = (x, y, z) => new THREE.Quaternion().setFromEuler(new THREE.Euler(x, y, z));

// ---------------------------------------------------------------- frame ---
export async function initShots(world) {
  initStage(world);
  // the principal's monitor HUD (drawn over the CCTV feed / report canvas)
  const mon = world.props.monitor;
  X.monHud = mon.userData.screen;
}
export function resetFrame(world, t, shot) {
  clock.t = t;
  for (const k in world.cast) { const c = world.cast[k]; c.root.visible = false; c.resetFace(); c.J.neck.visible = true; c.J.head.visible = true; }
  for (const c of world.kids) { c.root.visible = false; c.resetFace(); }
  hideShotProps();
  // movable set props back to their defaults
  const pr = world.props;
  pr.officeDoor.userData.open(0); pr.officeInDoor.userData.open(0);
  pr.mug.position.set(CLASS.tDesk.x + 0.48, 0.76, CLASS.tDesk.z - 0.12); pr.mug.rotation.set(0, 0.6, 0);
  pr.waitChair.position.set(60.15, 0, 1.9); pr.waitChair.rotation.set(0, Math.PI, 0);
  pr.examChair.position.set(OFFICE.table.x, 0, OFFICE.table.z + 0.45); pr.examChair.rotation.set(0, Math.PI, 0);
  pr.pChair.position.set(OFFICE.desk.x, 0, OFFICE.desk.z - 0.75); pr.pChair.rotation.set(0, 0, 0); pr.pChair.visible = true;
  pr.tChair.position.set(CLASS.tDesk.x, 0, CLASS.tDesk.z - 0.62); pr.tChair.rotation.set(0, 0, 0);
  pr.phone.position.set(HOME.x - 1.25, 0.618, HOME.z0 + 0.6); pr.phone.rotation.set(0, 0.4, 0);
  pr.sideTable.position.set(HOME.x - 1.25, 0, HOME.z0 + 0.6);
  pr.examStack.visible = true;
  pr.examTable.visible = pr.examChair.visible = t >= 53.1 || shot.set !== 'office';
  X.officeClock.userData.set(10, 10, 0);
}
export function finishFrame(world, t, shot, camera) {
  for (const c of [...Object.values(world.cast), ...world.kids]) {
    if (!c.root.visible) continue;
    if (c.armsMode === 'cross') crossArms(c); else if (c.armsMode === 'behind') handsBehind(c);
  }
  for (const k in world.cast) { const c = world.cast[k]; if (c.root.visible) c.applyFace(c.isBlink(t)); }
  for (const c of world.kids) if (c.root.visible) c.applyFace(c.isBlink(t));
}

// ----------------------------------------------------------- shared bits ---
const T = () => C.teacher, HERO = () => C.you, PRIN = () => C.principal;
const heroHead = (d) => { const s = heroSeatOf(d); return V3(s.x, 1.18, s.z); };
// hero seated at his (movable) desk; paper + pencil
function heroAtDesk(t, d, paper, o = {}) {
  const st = heroSeatOf(d);
  const h = HERO();
  const r = seatedWriter(h, st.x, st.z, st.heading, paper ? paper.group : null, o.pencil === false ? null : X.heroPencil, t, 7.7, { seatH: SEAT_H * 0.9, write: o.write, tip: o.tip, amp: o.amp, leftHand: o.leftHand });
  if (paper) paper.group.visible = true;
  if (o.write !== false && o.pencil !== false) X.heroPencil.visible = true;
  return { st, h, ...r };
}
// a pencil resting on the desk to the right of the sheet (when not in hand)
function pencilOnDesk(pencil, ch, dx = -0.2, dz = 0.42) {
  pencil.visible = true;
  pencil.position.copy(local(ch, dx, 0.664, dz));
  pencil.quaternion.copy(ch.root.quaternion).multiply(E(Math.PI / 2, 0, 0.3)).multiply(E(0, 0, 0));
  pencil.rotation.set(Math.PI / 2, 0, ch.root.rotation.y + 0.3, 'YXZ');
  pencil.updateMatrixWorld(true);
}
function rightPalmOnDesk(ch, dx = -0.18, dz = 0.36, y = 0.668) {
  palmAt(ch, 'r', local(ch, dx, y, dz), handQuat(ch, [0.3, 0, 1], [0, -1, 0]), 1, local(ch, -0.6, 0.6, -0.3), 0.2);
}
// object that follows a smooth key path of positions + quaternions
function keyed(obj, t, ks) {
  let a = ks[0], b = ks[ks.length - 1], k = 0;
  if (t <= ks[0].t) { a = b = ks[0]; }
  else if (t >= b.t) { a = b; }
  else for (let i = 0; i < ks.length - 1; i++) if (t <= ks[i + 1].t) { a = ks[i]; b = ks[i + 1]; k = (b.ease || easeInOut)(prog(t, a.t, b.t)); break; }
  obj.visible = true;
  obj.position.lerpVectors(a.p, b.p, k);
  obj.quaternion.slerpQuaternions(a.q, b.q, k);
  obj.updateMatrixWorld(true);
}
const lift = (v, h) => v.clone().add(V3(0, h, 0));
// writing tool matrix (pose of a pen/pencil whose tip is at tipW, held for writing by ch)
function toolPoseAt(ch, L, tool, tipW, tilt = 0) {
  const hq = writingHandQuat(ch, L, tilt);
  const hold = tool.userData.hold;
  const tipInWrist = tool.userData.tip.clone().applyMatrix4(hold);
  const wrist = tipW.clone().sub(tipInWrist.applyQuaternion(hq));
  const m = new THREE.Matrix4().compose(wrist, hq, V3(1, 1, 1)).multiply(hold);
  const p = V3(), q = new THREE.Quaternion(), s = V3();
  m.decompose(p, q, s);
  return { p, q };
}
const shakeCam = (c, t, t0, amp = 0.03, dur = 0.35) => {
  const k = clamp(1 - (t - t0) / dur) * (t >= t0 ? 1 : 0);
  if (k <= 0) return c;
  const s = amp * k * k;
  c.p = [c.p[0] + Math.sin(t * 91) * s, c.p[1] + Math.sin(t * 77 + 1) * s, c.p[2] + Math.sin(t * 83 + 2) * s * 0.5];
  return c;
};
// palm-down hand pose that carries a flat sheet pinched at its near edge (right hand)
const PAPER_HOLD_R = (() => {
  // paper local: X right, Y up (normal), Z down the page. Wrist frame: -Y fingers, +Z palm, thumb -X (right hand).
  // the hand pinches the right edge of the sheet, thumb on top; the sheet extends to the hand's left
  const m = new THREE.Matrix4().makeBasis(V3(0, 1, 0), V3(-1, 0, 0), V3(0, 0, 1));
  m.setPosition(0.0, -0.105, 0.03);
  return m;
})();
// paper (group) pose from the hand: paper = wrist * hold; paper centre offset so the hand pinches the right edge
function paperHoldMatrix(L = 'r') {
  const m = new THREE.Matrix4();
  // paper axes in wrist frame: X_p (page right) = +Y_w (towards the wrist), Y_p (page normal) = -X_w for the right hand (thumb up), Z_p = X × Y
  const xp = V3(0, 1, 0), yp = L === 'r' ? V3(-1, 0, 0) : V3(1, 0, 0);
  const zp = new THREE.Vector3().crossVectors(xp, yp);
  m.makeBasis(xp, yp, zp);
  // pinch point at the fingertips; the page centre is half a width further along -X_p (away from the wrist)
  const pinch = V3(0, -0.11, 0.025);
  const centre = pinch.clone().add(xp.clone().multiplyScalar(-(PW / 2 - 0.015))).add(zp.clone().multiplyScalar(0.06));
  m.setPosition(centre);
  return m;
}
const PAPER_GRIP_R = paperHoldMatrix('r').clone().invert();
const PAPER_GRIP_L = paperHoldMatrix('l').clone().invert();
// put a hand on a sheet whose group is at its current pose
function handOnPaper(ch, L, paperGroup, w = 1) {
  if (w <= 0) return;
  paperGroup.updateWorldMatrix(true, false);
  const m = paperGroup.matrixWorld.clone().multiply(L === 'r' ? PAPER_GRIP_R : PAPER_GRIP_L);
  const p = V3(), q = new THREE.Quaternion(), s = V3();
  m.decompose(p, q, s);
  armIK(ch, L, p, { hand: q, w, pole: local(ch, L === 'r' ? -0.7 : 0.7, 0.4, -0.3) });
  setGrip(ch, L, 0.45 * w + 0.25 * (1 - w));
}
// paper pose that a hand would give it (inverse of handOnPaper): for carrying
function paperFromHand(ch, L, paperGroup) {
  const wr = ch.J[L + 'Wrist'];
  wr.updateWorldMatrix(true, false);
  setWorldMatrix(paperGroup, wr.matrixWorld.clone().multiply(paperHoldMatrix(L)));
}

// =================================================================== SHOTS ===
// S1a 0.00-1.80  POV: the teacher writes a red 100 on your paper
{
  const t0 = 0, t1 = 1.8;
  S(t0, t1, 'class', (t) => handheld(ck(t, [K3(0, [0.0, 1.25, 1.36], [0.04, 0.66, 0.92], 50), K3(1.8, [0.01, 1.2, 1.3], [0.04, 0.66, 0.92], 47)]), t, 0.6, 3), (Wd, t) => {
    const d = stageClass(t, { kidsOpt: { mode: 'write' } });
    const { h } = heroAtDesk(t, d, X.p1, { write: false, pencil: false });
    h.J.neck.visible = false; // POV: we are the hero
    pencilOnDesk(X.heroPencil, h, -0.22, 0.36);
    rightPalmOnDesk(h, -0.12, 0.27);
    // red 100: pen approaches 0-0.25, draws 0.25-1.6, lifts after
    const k = prog(t, 0.25, 1.6);
    X.p1.setState({ score: k, ticks: 6 });
    const T_ = T();
    placeChar(T_, 0.5, 1.1, -Math.PI / 2, { ...POSES.stand, spine: [0.72, 0.15, 0], neck: [0, 0, 0], hipsZ: -0.1, lShoulder: [-0.3, 0, 0.2], lElbow: [-0.6, 0, 0] });
    X.p1.group.updateMatrixWorld(true);
    let tipL = X.p1.scoreTip(k);
    if (t < 0.25) tipL = lift(X.p1.scoreTip(0), 0.06 * (1 - easeOut(prog(t, 0, 0.25))));
    if (t > 1.6) tipL = lift(X.p1.scoreTip(1), 0.05 * easeOut(prog(t, 1.6, 1.8)));
    const tip = tipL.applyMatrix4(X.p1.group.matrixWorld);
    show(X.redPen);
    writeWith(T_, 'r', X.redPen, tip, 1, 0.1, local(T_, -0.7, 0.9, 0.1));
    palmAt(T_, 'l', local(T_, 0.2, 0.672, 0.32), handQuat(T_, [-0.2, 0, 1], [0, -1, 0]), 1, null, 0.2);
    look(T_, tip, 1, 0.8);
    T_.expr = 'focus';
  }, { blur: (t) => (t > 0.25 && t < 1.6 ? 3 : 0) });
}
// S1b 1.80-3.10  your face: a proud grin; the teacher straightens and moves on
const TEACH_WALK1 = curve([[0.5, 1.1], [0.72, 0.7], [0.75, -0.6], [0.4, -2.3], [-0.3, -3.3]]);
{
  S(1.8, 3.1, 'class', (t) => ck(t, [OC(1.8, [0, 1.28, 1.38], 212, 2, 1.3, 42), OC(3.1, [0, 1.28, 1.38], 206, 3, 1.15, 40)]), (Wd, t) => {
    const d = stageClass(t, { kidsOpt: { mode: 'write' } });
    X.p1.setState({ score: 1, ticks: 6 });
    const { h } = heroAtDesk(t, d, X.p1, { write: false, pencil: false });
    pencilOnDesk(X.heroPencil, h, -0.22, 0.36);
    rightPalmOnDesk(h, -0.12, 0.27);
    const T_ = T();
    if (t < 2.05) {
      const k = easeInOut(prog(t, 1.8, 2.05));
      placeChar(T_, 0.5, 1.1, -Math.PI / 2, blendPose({ ...POSES.stand, spine: [0.72, 0.15, 0], hipsZ: -0.1 }, POSES.stand, k));
    } else walkChar(T_, TEACH_WALK1, t, 2.05, 4.75, POSES.stand);
    T_.expr = 'neutral';
    look(h, t < 2.4 ? X.p1.group.position.clone() : V3(0.7, 1.6, 0.3), 1, 0.9);
    h.expr = t < 2.3 ? 'smile' : 'grin';
  });
}
// S2a 3.10-4.85  wide: the classroom in the sun, everyone writing
{
  S(3.1, 4.85, 'class', (t) => ck(t, [K3(3.1, [3.75, 2.75, 4.25], [-0.9, 0.85, -1.4], 52), K3(4.85, [3.45, 2.6, 3.75], [-0.9, 0.85, -1.5], 50)], (x) => x), (Wd, t) => {
    const d = stageClass(t, { kidsOpt: { mode: 'write' } });
    X.p1.setState({ score: 1, ticks: 6 });
    const { h } = heroAtDesk(t, d, X.p1, { write: true });
    h.expr = 'smile';
    walkChar(T(), TEACH_WALK1, t, 2.05, 4.75, POSES.stand);
  });
}
// S2b 4.85-6.60  the teacher turns and points the red pen at you; the class turns to look
{
  S(4.85, 6.6, 'class', (t) => ck(t, [K3(4.85, [-0.78, 1.98, -3.95], [-0.05, 1.05, 1.36], 36), K3(5.3, [-0.78, 1.98, -3.95], [-0.02, 1.15, 1.36], 33), K3(5.9, [-0.78, 1.98, -3.95], [0.0, 1.24, 1.36], 9.5, { ease: easeInOut }), K3(6.6, [-0.78, 1.98, -3.95], [0.0, 1.24, 1.36], 8.8)]), (Wd, t) => {
    const hero = V3(0, 1.15, 1.42);
    const turn = (m, i) => smooth(prog(t, 5.3 + hash(i, 7) * 0.35, 5.75 + hash(i, 7) * 0.35));
    const d = stageClass(t, { kidsOpt: { mode: (m, i) => 'look', target: hero, lookW: turn, expr: (m, i, w) => (w > 0.5 ? 'surprised' : 'neutral') } });
    X.p1.setState({ score: 1, ticks: 6 });
    const { h } = heroAtDesk(t, d, X.p1, { write: t < 5.6, amp: 0.4 });
    const up = smooth(prog(t, 5.6, 5.95));
    look(h, V3(-0.3, 1.55, -3.3), up, 0.9);
    h.expr = up > 0.4 ? 'shocked' : 'focus';
    const T_ = T();
    placeChar(T_, -0.3, -3.3, 0.06, POSES.stand);
    // raise the right arm and aim the pen at the hero
    const k = easeInOut(prog(t, 5.05, 5.45));
    const sh = local(T_, -0.2, 1.47, 0.0);
    const dir = hero.clone().sub(sh).normalize();
    const wrist = sh.clone().add(dir.clone().multiplyScalar(0.5));
    const hq = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().lookAt(V3(0, 0, 0), dir.clone().negate(), V3(0, 1, 0)));
    // build a hand frame: fingers (-Y) along dir, palm (+Z) facing down/in
    const fy = dir.clone().negate();
    const pz = V3(0.3, -1, 0).sub(dir.clone().multiplyScalar(V3(0.3, -1, 0).dot(dir))).normalize();
    const px = new THREE.Vector3().crossVectors(fy, pz);
    const hq2 = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(px, fy, pz));
    armIK(T_, 'r', wrist, { hand: hq2, w: k, pole: local(T_, -0.6, 1.0, -0.5) });
    setGrip(T_, 'r', 0.75);
    // pen in the fist, pointing along the arm
    const penM = new THREE.Matrix4().compose(T_.J.rWrist.getWorldPosition(V3()), T_.J.rWrist.getWorldQuaternion(new THREE.Quaternion()), V3(1, 1, 1));
    penM.multiply(new THREE.Matrix4().compose(V3(-0.012, -0.075, 0.025), E(0, 0, 0), V3(1, 1, 1)));
    show(X.redPen); setWorldMatrix(X.redPen, penM);
    look(T_, hero, 1, 0.9);
    T_.expr = k > 0.5 ? 'angry' : 'suspicious';
  });
}
// S3 6.60-8.90  "Your first perfect score, nobody notices." the teacher drops it and walks on
const TEACH_WALK3 = curve([[0.62, -0.6], [0.62, 1.0], [0.68, 2.7]]);
{
  const drop = { t: 7.32, land: 7.62 };
  const restP = V3(0.08, 0.6625, 1.0);
  S(6.6, 8.9, 'class', (t) => ck(t, [K3(6.6, [0.42, 2.05, -1.45], [0.22, 0.8, 1.25], 50), K3(8.9, [0.4, 2.0, -1.3], [0.2, 0.8, 1.3], 48)], (x) => x), (Wd, t) => {
    const d = stageClass(t, { kidsOpt: { mode: 'write' } });
    const { h } = heroAtDesk(t, d, null, { write: false, pencil: false });
    pencilOnDesk(X.heroPencil, h, -0.22, 0.36);
    rightPalmOnDesk(h, -0.12, 0.27);
    const T_ = T();
    walkChar(T_, TEACH_WALK3, t, 6.2, 9.0, POSES.stand);
    // left hand carries the stack against the chest
    const stackM = local(T_, 0.12, 1.1, 0.24);
    X.carryStack.visible = true; X.carryStack.position.copy(stackM); X.carryStack.rotation.set(0.25, T_.root.rotation.y, 0, 'YXZ'); X.carryStack.updateMatrixWorld(true);
    palmAt(T_, 'l', local(T_, 0.12, 1.085, 0.22), handQuat(T_, [-1, 0, 0.2], [0, 1, 0]), 1, null, 0.3);
    // the paper: carried by the right hand, released above the desk, floats down
    const pg = X.pDone.group; pg.visible = true;
    if (t < drop.t) {
      // carried flat beside him; reaching out towards the desk from 7.0
      const reach = easeInOut(prog(t, 6.95, drop.t));
      const carry = local(T_, -0.26, 0.98, 0.3);
      const target = V3(0.12, 0.78, 1.0);
      const p = carry.clone().lerp(target, reach);
      pg.position.copy(p);
      pg.rotation.set(0, T_.root.rotation.y + Math.PI / 2 + reach * (Math.PI / 2 - 0.1), 0);
      pg.updateMatrixWorld(true);
      T_.J.spine.rotation.y += -0.35 * reach; T_.J.spine.rotation.x += 0.25 * reach;
      handOnPaper(T_, 'r', pg, 1);
    } else {
      const k = prog(t, drop.t, drop.land);
      const from = V3(0.12, 0.78, 1.0);
      const p = from.clone().lerp(restP, easeIn(k));
      p.x += Math.sin(k * Math.PI) * 0.03;
      pg.position.copy(p);
      pg.rotation.set(Math.sin(k * Math.PI * 2) * 0.06 * (1 - k), Math.PI - 0.1 + (1 - k) * 0.12, Math.sin(k * Math.PI) * 0.05);
      pg.updateMatrixWorld(true);
      const rel = 1 - easeInOut(prog(t, drop.t, drop.t + 0.3));
      T_.J.spine.rotation.y += -0.35 * rel; T_.J.spine.rotation.x += 0.25 * rel;
    }
    look(T_, V3(0.6, 1.5, 3.5), 1, 0.4); // he never looks at you
    look(h, pg.position, 1, 0.9);
    h.expr = t > 7.7 ? 'smile' : 'neutral';
  });
}
// S4 8.90-10.50 "Anyone can have a good day." along the row: you and Maryam with her 92
{
  S(8.9, 10.5, 'class', (t) => ck(t, [OC(8.9, [-1.5, 1.2, 1.36], 152, 3, 1.35, 38), OC(10.5, [-1.5, 1.2, 1.36], 156, 3, 1.25, 36)], (x) => x), (Wd, t) => {
    const nb = kidSeatOf('kid1');
    const d = stageClass(t, { kidsOpt: { mode: 'write', skip: [nb.ch] } });
    X.pDone.group.visible = true;
    const { h } = heroAtDesk(t, d, X.pDone, { write: false, pencil: false });
    pencilOnDesk(X.heroPencil, h, -0.22, 0.36);
    rightPalmOnDesk(h, -0.12, 0.27);
    look(h, X.pDone.group.position, 1, 0.9);
    h.expr = 'smile';
    // Maryam lifts her 92, looks at it, shrugs with a smile at you
    const g = nb.ch;
    seatedWriter(g, nb.seat.x, nb.seat.z, Math.PI, X.pGirl.group, null, t, 3, { write: false });
    const lift_ = easeInOut(prog(t, 9.05, 9.55));
    if (lift_ > 0) {
      const base = local(g, 0.0, 0.661, 0.38);
      const up = local(g, -0.02, 0.98, 0.3);
      const pg = X.pGirl.group;
      pg.position.lerpVectors(base, up, lift_);
      pg.rotation.set(-1.15 * lift_, Math.PI + g.root.rotation.y * 0 + 0, 0, 'YXZ');
      pg.rotation.set(-1.15 * lift_, 0, 0, 'YXZ');
      pg.updateMatrixWorld(true);
      handOnPaper(g, 'r', pg, smooth(prog(t, 8.9, 9.1)));
    }
    const glance = smooth(prog(t, 9.6, 9.95));
    look(g, X.pGirl.group.position, 1 - glance, 0.9);
    look(g, V3(0, 1.15, 1.42), glance, 0.9);
    g.expr = glance > 0.5 ? 'happy' : 'smile';
    g.J.spine.rotation.z += Math.sin(prog(t, 9.6, 10.0) * Math.PI) * 0.06; // shrug
  });
}
// S5a 10.50-12.60 top-down: your second and third hundred land on the first
function stackDrops(t, drops) {
  // drops: [{paper, t, from, to, rot}] - each paper slides in from the right and settles
  const T_ = T();
  placeChar(T_, 0.62, 0.95, -Math.PI / 2, { ...POSES.stand, spine: [0.35, 0, 0], hipsZ: -0.05 });
  palmAt(T_, 'l', local(T_, 0.12, 1.08, 0.24), handQuat(T_, [-1, 0, 0.2], [0, 1, 0]), 1, null, 0.3);
  X.carryStack.visible = true; X.carryStack.position.copy(local(T_, 0.12, 1.095, 0.26)); X.carryStack.rotation.set(0.2, T_.root.rotation.y, 0, 'YXZ'); X.carryStack.updateMatrixWorld(true);
  let handW = 0, handPaper = null;
  for (const dr of drops) {
    const k = prog(t, dr.t - 0.3, dr.t);
    const pg = dr.paper; pg.visible = t >= dr.t - 0.45;
    const from = V3(0.36, 0.83, 0.86), to = dr.to;
    const e = easeInOut(k);
    pg.position.lerpVectors(from, to, e);
    pg.position.y += Math.sin(e * Math.PI) * 0.03;
    pg.rotation.set(0, lerp(0.7, dr.rot, e), 0);
    pg.updateMatrixWorld(true);
    // hand holds the sheet until it lands, then lets go
    const w = t < dr.t ? smooth(prog(t, dr.t - 0.45, dr.t - 0.3)) : 1 - smooth(prog(t, dr.t, dr.t + 0.22));
    if (w > handW) { handW = w; handPaper = pg; }
  }
  if (handPaper) handOnPaper(T_, 'r', handPaper, handW);
  return T_;
}
{
  S(10.5, 12.6, 'class', (t) => ck(t, [K3(10.5, [0.02, 1.62, 1.14], [0.02, 0.66, 0.99], 34), K3(12.6, [0.02, 1.5, 1.12], [0.02, 0.66, 0.99], 33)]), (Wd, t) => {
    const d = stageClass(t, { kidsOpt: { mode: 'write' } });
    const { h } = heroAtDesk(t, d, X.pDone, { write: false, pencil: false });
    pencilOnDesk(X.heroPencil, h, -0.24, 0.3);
    rightPalmOnDesk(h, -0.14, 0.22);
    stackDrops(t, [
      { paper: X.pStack[0], t: 11.08, to: V3(0.015, 0.6635, 1.04), rot: 0.07 },
      { paper: X.pStack[1], t: 11.56, to: V3(-0.03, 0.665, 1.03), rot: -0.05 },
    ]);
  });
}
// S5b 12.60-13.80 the teacher grading at his desk stops, looks up over his glasses at you
{
  S(12.6, 13.8, 'class', (t) => ck(t, [OC(12.6, [-2.1, 1.36, -3.45], 25, 4, 1.35, 40), OC(13.8, [-2.1, 1.38, -3.45], 22, 3, 1.15, 38)]), (Wd, t) => {
    const d = stageClass(t, { kidsOpt: { mode: 'write' } });
    heroAtDesk(t, d, X.pDone, { write: true });
    const T_ = teacherAtDesk(t, { hands: false });
    // grading a sheet with the red pen until he notices
    const pg = X.pStack[2]; pg.visible = true;
    pg.position.copy(local(T_, 0.0, 0.762, 0.5)); pg.rotation.set(0, Math.PI, 0); pg.updateMatrixWorld(true);
    const stop = smooth(prog(t, 12.95, 13.2));
    const tipL = V3(0.05 * Math.sin(t * 7), 0.0006 + 0.02 * stop, -0.05 + 0.01 * Math.sin(t * 3));
    const tip = tipL.applyMatrix4(pg.matrixWorld);
    show(X.redPen);
    writeWith(T_, 'r', X.redPen, tip, 1, 0, local(T_, -0.7, 0.6, -0.2));
    palmAt(T_, 'l', local(T_, 0.2, 0.775, 0.42), handQuat(T_, [-0.25, 0, 1], [0, -1, 0]), 1, null, 0.2);
    const up = smooth(prog(t, 13.05, 13.45));
    look(T_, tip, 1 - up, 0.9);
    look(T_, V3(0, 1.15, 1.42), up, 0.95);
    T_.J.head.rotation.x += 0.12 * up; // chin down, eyes up over the glasses
    T_.look = [T_.look[0], -0.75 * up + T_.look[1] * (1 - up)];
    T_.expr = up > 0.5 ? 'suspicious' : 'focus';
  });
}
// S6a 13.80-15.10 "He doesn't say a word." slow sip, eyes fixed on you
{
  S(13.8, 15.1, 'class', (t) => ck(t, [OC(13.8, [-2.1, 1.38, -3.45], 12, 2, 0.95, 36), OC(15.1, [-2.1, 1.39, -3.45], 10, 2, 0.85, 34)], (x) => x), (Wd, t) => {
    const d = stageClass(t, { kidsOpt: { mode: 'write' } });
    heroAtDesk(t, d, X.pDone, { write: true });
    const T_ = teacherAtDesk(t, { hands: false, pose: { ...POSES.sitDesk, spine: [0.05, 0, 0] } });
    palmAt(T_, 'l', local(T_, 0.2, 0.775, 0.42), handQuat(T_, [-0.25, 0, 1], [0, -1, 0]), 1, null, 0.2);
    // mug: desk -> mouth -> held
    const mg = X.mug;
    const deskP = mg.position.clone();
    const mouth = local(T_, -0.04, 1.27 + 0.06 * smooth(prog(t, 14.5, 14.8)) * (1 - smooth(prog(t, 14.95, 15.1))), 0.17);
    const k = easeInOut(prog(t, 13.95, 14.5));
    const p = deskP.clone().lerp(mouth, k);
    mg.position.copy(p);
    mg.rotation.set(-0.5 * smooth(prog(t, 14.45, 14.75)) * (1 - smooth(prog(t, 14.9, 15.1))), T_.root.rotation.y + Math.PI / 2, 0, 'YXZ');
    mg.updateMatrixWorld(true);
    const reach = smooth(prog(t, 13.8, 13.95));
    if (!mg.userData.hold) mg.userData.hold = new THREE.Matrix4().compose(V3(0.05, -0.06, 0.056), E(0, 0, Math.PI / 2), V3(1, 1, 1));
    holdObj(T_, 'r', mg, Math.max(reach, 0.999 * (t > 13.95 ? 1 : reach)), { pole: local(T_, -0.6, 0.5, -0.3) });
    setGrip(T_, 'r', 0.7);
    look(T_, V3(-1.05, 1.15, -2.2).set(0, 1.15, 1.42), 1, 0.95);
    T_.expr = 'suspicious';
  });
}
// S6b 15.10-16.75 "He just keeps an eye on you." his point of view, a slow zoom onto you
{
  S(15.1, 16.75, 'class', (t) => ck(t, [K3(15.1, [-2.08, 1.42, -3.4], [0.0, 1.22, 1.36], 22), K3(16.75, [-2.06, 1.42, -3.36], [0.0, 1.23, 1.36], 9.5)], (x) => smooth(x)), (Wd, t) => {
    const d = stageClass(t, { kidsOpt: { mode: 'write' } });
    const { h } = heroAtDesk(t, d, X.pDone, { write: true });
    h.expr = 'focus';
    // his glasses frame the shot edge: teacher hidden (we are him)
  }, { vignette: 0.6 });
}
// S7a 16.75-17.62 "By your fifth in a row" - number five lands on the pile
{
  S(16.75, 17.62, 'class', (t) => ck(t, [K3(16.75, [0.02, 1.45, 1.12], [0.02, 0.66, 0.99], 33), K3(17.62, [0.02, 1.38, 1.1], [0.02, 0.66, 0.99], 32)]), (Wd, t) => {
    const d = stageClass(t, { kidsOpt: { mode: 'write' } });
    const { h } = heroAtDesk(t, d, X.pDone, { write: false, pencil: false });
    pencilOnDesk(X.heroPencil, h, -0.24, 0.3);
    rightPalmOnDesk(h, -0.14, 0.22);
    for (const [i, p, r] of [[0, V3(0.015, 0.6635, 1.04), 0.07], [1, V3(-0.03, 0.665, 1.03), -0.05], [2, V3(0.0, 0.6665, 1.035), 0.02]]) {
      const pg = X.pStack[i]; pg.visible = true; pg.position.copy(p); pg.rotation.set(0, r, 0); pg.updateMatrixWorld(true);
    }
    stackDrops(t, [{ paper: X.pStack[3], t: 17.2, to: V3(-0.01, 0.668, 1.04), rot: 0.1 }]);
  });
}
// pushing the desk: hero behind the tucked chair (forward) or in front of the desk (back)
function heroPushing(t, d) {
  const h = HERO();
  if (!d.seg) { t = t < 50 ? MOVE.f2[1] - 1e-4 : MOVE.b2[1] - 1e-4; d = heroDeskState(t); }
  const desk = PR.heroDesk, chair = PR.heroChair;
  desk.updateMatrixWorld(true); chair.updateMatrixWorld(true);
  const s = h.scale;
  const cad = 1.15 * s / (4 * 0.3 * s);
  const phase = cad * (t - d.seg[0]) + (d.seg === MOVE.f2 || d.seg === MOVE.b2 ? 0.37 : 0);
  // speed from the segment curve
  const d2 = heroDeskState(t + 1 / 120);
  const v = Math.hypot(d2.x - d.x, d2.z - d.z) * 120;
  const amp = clamp(v / (1.15 * s), 0, 1);
  const lean = { ...POSES.stand, spine: [0.42, 0, 0] };
  if (d.mode === 'push') {
    const p = V3(0, 0, -0.86).applyMatrix4(desk.matrixWorld);
    placeChar(h, p.x, p.z, d.yaw, amp > 0.02 ? blendPose(lean, walkPose(phase, amp, lean), clamp(amp * 4)) : lean);
    h.J.spine.rotation.x = 0.42;
    for (const [L, sx] of [['l', 0.17], ['r', -0.17]]) {
      // hands on the chair's back rail (chair local), fingers forward over the top
      const grip = V3(sx, 0.785, -0.215).applyMatrix4(chair.matrixWorld);
      palmAt(h, L, grip, handQuat(h, [0, -0.6, 1], [0, -1, -0.2]), 1, local(h, L === 'l' ? 0.6 : -0.6, 0.6, -0.4), 0.55);
    }
  } else {
    const p = V3(0, 0, 0.72).applyMatrix4(desk.matrixWorld);
    placeChar(h, p.x, p.z, d.yaw - Math.PI, amp > 0.02 ? blendPose(lean, walkPose(phase, amp, lean), clamp(amp * 4)) : lean);
    h.J.spine.rotation.x = 0.42;
    for (const [L, sx] of [['l', 0.2], ['r', -0.2]]) {
      const grip = V3(sx, 0.668, 0.2).applyMatrix4(desk.matrixWorld);
      palmAt(h, L, grip, handQuat(h, [0, -0.2, 1], [0, -1, 0]), 1, local(h, L === 'l' ? 0.6 : -0.6, 0.6, -0.4), 0.3);
    }
  }
  look(h, V3(d.x, 0.8, d.z - 1.5 * (d.mode === 'push' ? 1 : -1)), 0.6, 0.5);
  return h;
}
// S7b 17.62-18.95 you push your desk out of your row and up the aisle
{
  S(17.62, 18.95, 'class', (t) => ck(t, [K3(17.62, [-2.2, 1.5, -1.3], [-0.35, 0.9, 0.75], 40), K3(18.95, [-2.25, 1.48, -1.4], [-0.62, 0.9, 0.2], 40)], (x) => x), (Wd, t) => {
    const d = stageClass(t, { kidsOpt: { mode: 'look', target: V3(heroDeskState(t).x, 1.0, heroDeskState(t).z + 0.8), lookW: (m, i) => smooth(prog(t, 17.7 + hash(i, 3) * 0.6, 18.1 + hash(i, 3) * 0.6)) } });
    // the stack of graded papers rides on the desk
    X.pDone.group.visible = true; PR.heroDesk.updateMatrixWorld(true);
    setWorldMatrix(X.pDone.group, PR.heroDesk.matrixWorld.clone().multiply(new THREE.Matrix4().compose(V3(0, 0.6625, -0.04), E(0, 0, 0), V3(1, 1, 1))));
    const h = heroPushing(t, d);
    h.expr = 'worried';
  });
}
// S7c 18.95-20.40 ...right next to his. The desk arrives beside the teacher's desk
{
  S(18.95, 20.4, 'class', (t) => ck(t, [OC(18.95, [-1.05, 0.9, -2.45], 232, 32, 2.4, 46), OC(20.4, [-1.05, 0.95, -2.45], 236, 30, 2.25, 44)], (x) => x), (Wd, t) => {
    const d = stageClass(t, { deskT: Math.min(t, MOVE.f2[1] - 1e-4), kidsOpt: { mode: 'look', target: V3(-1.05, 1.0, -2.0), lookW: () => 0.8 } });
    X.pDone.group.visible = true; PR.heroDesk.updateMatrixWorld(true);
    setWorldMatrix(X.pDone.group, PR.heroDesk.matrixWorld.clone().multiply(new THREE.Matrix4().compose(V3(0, 0.6625, -0.04), E(0, 0, 0), V3(1, 1, 1))));
    const h = heroPushing(t, d);
    h.expr = 'worried';
    const T_ = teacherAtDesk(t, { hands: false, pose: { ...POSES.sitDesk, ...POSES.armsCrossed, hipsY: SIT_Y, lHip: POSES.sitDesk.lHip, rHip: POSES.sitDesk.rHip, lKnee: POSES.sitDesk.lKnee, rKnee: POSES.sitDesk.rKnee, lAnkle: POSES.sitDesk.lAnkle, rAnkle: POSES.sitDesk.rAnkle, spine: [-0.05, 0, 0] } });
    look(T_, V3(d.x, 1.3, d.z + 0.6), 1, 0.9);
    T_.J.head.rotation.x += Math.sin(prog(t, 19.7, 20.1) * Math.PI) * 0.18; // a single nod
    T_.expr = 'stern';
  });
}
// S8a 20.40-21.45 at the front: you write, then look up...
{
  S(20.4, 21.45, 'class', (t) => ck(t, [OC(20.4, [-1.05, 1.15, -2.3], 150, 12, 1.5, 40), OC(21.45, [-1.05, 1.17, -2.3], 152, 10, 1.35, 38)], (x) => x), (Wd, t) => {
    const d = stageClass(t, { kidsOpt: { mode: 'write' } });
    const { h } = heroAtDesk(t, d, X.pDone, { write: true });
    const up = smooth(prog(t, 21.0, 21.3));
    look(h, V3(-2.1, 1.35, -3.5), up, 0.95);
    h.expr = up > 0.5 ? 'worried' : 'focus';
    const T_ = teacherAtDesk(t, { hands: false, pose: { ...POSES.sitDesk, spine: [0.25, 0, 0] } });
    palmAt(T_, 'l', local(T_, 0.2, 0.775, 0.42), handQuat(T_, [-0.25, 0, 1], [0, -1, 0]), 1, null, 0.2);
    palmAt(T_, 'r', local(T_, -0.05, 1.12, 0.3), handQuat(T_, [0.2, 1, 0.2], [0, 0, 1]), 1, local(T_, -0.4, 0.75, 0.3), 0.85);
    look(T_, V3(-1.05, 1.15, -2.2), 1, 0.95);
    T_.expr = 'suspicious';
  });
}
// S8b 21.45-22.80 ...he's already watching. Chin on his fist, unblinking
{
  S(21.45, 22.8, 'class', (t) => ck(t, [OC(21.45, [-2.1, 1.36, -3.45], 40, 2, 1.25, 38), OC(22.8, [-2.1, 1.37, -3.45], 38, 2, 1.05, 34)], (x) => x), (Wd, t) => {
    const d = stageClass(t, { kidsOpt: { mode: 'write' } });
    heroAtDesk(t, d, X.pDone, { write: false });
    const T_ = teacherAtDesk(t, { hands: false, pose: { ...POSES.sitDesk, spine: [0.3, 0.25, 0] } });
    palmAt(T_, 'l', local(T_, 0.22, 0.775, 0.42), handQuat(T_, [-0.25, 0, 1], [0, -1, 0]), 1, null, 0.2);
    // fist under the chin (elbow on the desk)
    const chin = local(T_, 0.0, 0.0, 0.0); T_.J.head.updateWorldMatrix(true, false);
    const cw = V3(0, 0.0, 0.11 * T_.scale).applyMatrix4(T_.J.head.matrixWorld);
    palmAt(T_, 'r', cw.add(V3(0, -0.035, 0)), handQuat(T_, [0.05, 1, 0.3], [0.3, 0, -1]), 1, local(T_, -0.15, 0.5, 0.5), 0.95);
    look(T_, V3(-1.05, 1.15, -2.2), 1, 1.0);
    T_.blinkOff = true;
    T_.expr = 'suspicious';
  });
}
// S9a 22.80-24.60 "the hardest exam of the year" - the stack slams down
{
  const slam = 23.42;
  S(22.8, 24.6, 'class', (t) => shakeCam(ck(t, [OC(22.8, [-2.05, 1.2, -3.25], 20, 5, 2.0, 46), OC(24.6, [-2.05, 1.22, -3.25], 24, 4, 1.85, 44)], (x) => x), t, slam, 0.022), (Wd, t) => {
    const d = stageClass(t, { kidsOpt: { mode: (m, i) => (t > 23.9 ? 'groan' : 'write'), groanK: (m, i) => smooth(prog(t, 23.9 + hash(i, 5) * 0.3, 24.4 + hash(i, 5) * 0.3)) } });
    X.pFinal.setState({ answers: 0, bonus: 0, name: 1 });
    heroAtDesk(t, d, X.pFinal, { write: false, pencil: false });
    const T_ = T();
    placeChar(T_, CLASS.tDesk.x, CLASS.tDesk.z - 0.45, 0, { ...POSES.stand, spine: [0.2 + 0.2 * smooth(prog(t, 23.0, slam)), 0, 0] });
    PR.examStack.visible = false;
    const st = X.examSlam;
    const restP = V3(CLASS.tDesk.x + 0.02, 0.76, CLASS.tDesk.z - 0.05);
    const upP = local(T_, 0.0, 1.18, 0.36);
    let p;
    if (t < slam) { const k = prog(t, 22.8, slam); p = upP.clone().lerp(restP, k < 0.55 ? -0.25 * Math.sin(k / 0.55 * Math.PI) * 0.4 : easeIn((k - 0.55) / 0.45)); if (k < 0.55) p.y = upP.y + 0.06 * Math.sin(k / 0.55 * Math.PI); }
    else { p = restP.clone(); p.y += Math.max(0, Math.sin((t - slam) * 30) * 0.008 * Math.exp(-(t - slam) * 12)); }
    st.visible = true; st.position.copy(p); st.rotation.set(0, -0.05, 0); st.updateMatrixWorld(true);
    // both hands on the sides of the stack until shortly after the slam
    const w = 1 - smooth(prog(t, slam + 0.3, slam + 0.6));
    for (const [L, sx] of [['l', 0.115], ['r', -0.115]]) {
      const g = V3(sx, 0.03, 0).applyMatrix4(st.matrixWorld);
      palmAt(T_, L, g, handQuat(T_, [L === 'l' ? -0.2 : 0.2, -0.3, 1], [L === 'l' ? -1 : 1, 0, 0]), w, local(T_, L === 'l' ? 0.6 : -0.6, 0.6, -0.4), 0.3);
    }
    look(T_, V3(0, 1.0, 0.5), 1, 0.5);
    T_.expr = t > slam ? 'stern' : 'neutral';
  });
}
// S9b 24.60-27.15 the exam paper; the camera drifts down to the BONUS question
{
  S(24.6, 27.15, 'class', (t) => ck(t, [K3(24.6, [-1.14, 1.3, -2.36], [-1.08, 0.661, -2.68], 48), K3(25.65, [-1.14, 1.24, -2.38], [-1.08, 0.661, -2.58], 46), K3(27.15, [-1.13, 1.12, -2.4], [-1.08, 0.661, -2.52], 42)]), (Wd, t) => {
    const d = stageClass(t, { kidsOpt: { mode: 'write', paper: 'final' } });
    X.pFinal.setState({ answers: prog(t, 24.6, 26.6) * 0.98, bonus: 0, name: 1 });
    const { h } = heroAtDesk(t, d, X.pFinal, { write: true });
    h.J.neck.visible = false; // point of view
    // pencil follows the answers being written
    X.pFinal.group.updateMatrixWorld(true);
    const tip = X.pFinal.writeTip('ans', prog(t, 24.6, 26.6) * 0.98).applyMatrix4(X.pFinal.group.matrixWorld);
    writeWith(h, 'r', X.heroPencil, tip, 1, 0, local(h, -0.5, 0.75, -0.2));
  });
}
// S10 27.15-28.35 "You solve it." the bonus answer pours out, then gets boxed
{
  S(27.15, 28.35, 'class', (t) => ck(t, [K3(27.15, [-1.13, 1.1, -2.4], [-1.08, 0.661, -2.51], 42), K3(28.35, [-1.13, 1.05, -2.42], [-1.08, 0.661, -2.51], 40)]), (Wd, t) => {
    const d = stageClass(t, { kidsOpt: { mode: 'write', paper: 'final' } });
    const kb = prog(t, 27.2, 27.92), kx = prog(t, 27.95, 28.25);
    X.pFinal.setState({ answers: 1, bonus: kb, bonusBox: kx, name: 1 });
    const { h } = heroAtDesk(t, d, X.pFinal, { write: true });
    h.J.neck.visible = false; // point of view
    X.pFinal.group.updateMatrixWorld(true);
    let tipL = t < 27.95 ? X.pFinal.writeTip('bonus', kb) : X.pFinal.boxTip(kx);
    if (t > 28.25) tipL = lift(X.pFinal.boxTip(1), 0.03 * prog(t, 28.25, 28.35));
    const tip = tipL.applyMatrix4(X.pFinal.group.matrixWorld);
    writeWith(h, 'r', X.heroPencil, tip, 1, 0, local(h, -0.5, 0.75, -0.2));
    h.expr = 'focus';
  }, { blur: () => 4 });
}
// S11 28.35-30.25 "And now, this can't be ignored." the pen drops, the teacher shoots up
{
  const drop = 28.85, stand = 29.15;
  S(28.35, 30.25, 'class', (t) => shakeCam(ck(t, [OC(28.35, [-2.1, 1.35, -3.45], 15, 0, 1.7, 42), OC(29.1, [-2.1, 1.35, -3.45], 15, 0, 1.7, 42), OC(30.25, [-2.1, 1.55, -3.5], 15, -4, 1.95, 44)]), t, stand + 0.12, 0.015), (Wd, t) => {
    const d = stageClass(t, { kidsOpt: { mode: 'write', paper: 'final' } });
    X.pFinal.setState({ answers: 1, bonus: 1, bonusBox: 1, name: 1, ticks: 3 });
    heroAtDesk(t, d, null, { write: false, pencil: false });
    const T_ = T();
    const sk = easeInOut(prog(t, stand, stand + 0.35));
    const sitP = { ...POSES.sitDesk, hipsY: SIT_Y + (0.48 - SEAT_H) };
    placeChar(T_, CLASS.tDesk.x, CLASS.tDesk.z - 0.58 - 0.12 * sk, 0, blendPose(sitP, { ...POSES.stand, spine: [0.15, 0, 0] }, sk));
    PR.tChair.position.z = CLASS.tDesk.z - 0.62 - 0.35 * easeOut(prog(t, stand, stand + 0.5));
    PR.tChair.rotation.y = 0.25 * easeOut(prog(t, stand, stand + 0.5));
    // the hero's exam on his desk, facing him
    const pg = X.pFinal.group; pg.visible = true;
    pg.position.set(CLASS.tDesk.x + 0.02, 0.761, CLASS.tDesk.z + 0.05); pg.rotation.set(0, Math.PI, 0); pg.updateMatrixWorld(true);
    const bonusTip = V3(0.0, 0.0006, 0.08).applyMatrix4(pg.matrixWorld);
    const pen = X.redPen; pen.visible = true;
    if (t < drop) {
      const tip = bonusTip.clone().add(V3(0.02 * Math.sin(t * 6), 0.012, 0));
      writeWith(T_, 'r', pen, tip, 1, 0, local(T_, -0.7, 0.6, -0.2));
    } else {
      // pen falls from the frozen hand, bounces and rolls
      const from = toolPoseAt(T_, 'r', pen, bonusTip.clone().add(V3(0.02 * Math.sin(drop * 6), 0.012, 0)));
      const rest = { p: V3(CLASS.tDesk.x - 0.08, 0.767, CLASS.tDesk.z + 0.02), q: E(Math.PI / 2, 0, 1.2) };
      const k = prog(t, drop, drop + 0.32);
      const pos = from.p.clone().lerp(rest.p, k);
      pos.y = lerp(from.p.y, rest.p.y, easeIn(k)) + (k >= 1 ? Math.max(0, Math.sin((t - drop - 0.32) * 22) * 0.012 * Math.exp(-(t - drop - 0.32) * 9)) : 0);
      pen.position.copy(pos); pen.quaternion.slerpQuaternions(from.q, rest.q, easeIn(k)); pen.updateMatrixWorld(true);
      // the hand stays frozen where the pen was, then rises with him
      const frozen = 1 - smooth(prog(t, stand, stand + 0.25));
      const dummy = new THREE.Object3D(); dummy.userData = { tip: pen.userData.tip, hold: pen.userData.hold };
      writeWith(T_, 'r', dummy, bonusTip.clone().add(V3(0.02 * Math.sin(drop * 6), 0.03, 0)), frozen, 0, local(T_, -0.7, 0.6, -0.2));
      pen.position.copy(pos); pen.quaternion.slerpQuaternions(from.q, rest.q, easeIn(k)); pen.updateMatrixWorld(true);
    }
    palmAt(T_, 'l', local(T_, 0.22, 0.775, 0.42), handQuat(T_, [-0.25, 0, 1], [0, -1, 0]), 1 - sk, null, 0.2);
    const upLook = smooth(prog(t, stand + 0.2, stand + 0.6));
    look(T_, bonusTip, 1 - upLook, 0.95);
    look(T_, V3(-1.05, 1.15, -2.2), upLook, 0.95);
    T_.expr = t > drop - 0.05 ? 'shocked' : 'focus';
  });
}
// S12 30.25-32.05 the corridor: you walk to the principal's door; it opens
const HALL_WALK = curve([[30.05, -18.55], [30.02, -19.6], [30.0, -20.85]]);
{
  S(30.25, 32.05, 'hall', (t) => {
    const wk = HALL_WALK.getPointAt(clamp((t - 30.0) / 2.2));
    return ck(t, [K3(30.25, [30.38, 1.5, -17.15], [30.0, 1.15, -21.5], 44), K3(32.05, [30.32, 1.48, -19.0], [30.0, 1.2, -21.9], 44)], (x) => x);
  }, (Wd, t) => {
    const h = HERO();
    walkChar(h, HALL_WALK, t, 30.0, 32.2, POSES.stand);
    h.expr = 'worried';
    // backpack on his back
    h.J.spine.updateWorldMatrix(true, false);
    setWorldMatrix(X.bagO, h.J.spine.matrixWorld.clone().multiply(new THREE.Matrix4().compose(V3(0, 0.12, -0.2), E(0.05, Math.PI, 0), V3(1, 1, 1))));
    X.bagO.visible = true;
    PR.officeDoor.userData.open(1.35 * easeInOut(prog(t, 31.35, 31.95)));
  });
}
// S13a 32.05-33.00 top-down: the principal opens your bag and takes out a notebook
const DESK_O = OFFICE.desk;
function principalSearching(t, o = {}) {
  const Pn = PRIN();
  placeChar(Pn, DESK_O.x, DESK_O.z - 0.62, 0, { ...POSES.stand, spine: [0.55, 0, 0], hipsZ: -0.08 });
  Pn.expr = 'suspicious';
  return Pn;
}
{
  const bagP = V3(59.82, 0.77, -1.3);
  S(32.05, 33.0, 'office', (t) => ck(t, [OC(32.05, [59.95, 1.05, -1.45], 0, 30, 2.05, 46), OC(33.0, [59.97, 1.05, -1.45], 4, 30, 1.95, 45)]), (Wd, t) => {
    const Pn = principalSearching(t);
    const bag = X.bagO; bag.visible = true;
    bag.position.copy(bagP); bag.rotation.set(0, 0.25, 0); bag.updateMatrixWorld(true);
    bag.userData.open(1.6 * easeInOut(prog(t, 32.2, 32.55)));
    // notebook: from inside the bag to the right
    const nb = X.nb1;
    const inBag = V3(59.82, 1.12, -1.33), out = V3(60.22, 0.775, -1.2);
    const k = easeInOut(prog(t, 32.55, 32.95));
    nb.visible = t > 32.5;
    nb.position.lerpVectors(inBag, out, k); nb.position.y += Math.sin(k * Math.PI) * 0.08;
    nb.rotation.set((1 - k) * -Math.PI / 2, 0.15 * k, 0); nb.updateMatrixWorld(true);
    // left hand holds the bag flap open, right hand moves the notebook
    const flapW = smooth(prog(t, 32.15, 32.25));
    palmAt(Pn, 'l', V3(59.74, 1.2, -1.45), handQuat(Pn, [0.3, -0.5, 1], [0, -1, 0]), flapW, null, 0.4);
    const nw = t < 32.5 ? smooth(prog(t, 32.3, 32.5)) : 1 - smooth(prog(t, 32.95, 33.0));
    palmAt(Pn, 'r', nb.position.clone().add(V3(0.06, 0.016, 0)), handQuat(Pn, [-0.3, -0.4, 1], [0, -1, 0]), nw, null, 0.5);
    look(Pn, bagP, 1, 0.8);
  });
}
// S13b 33.00-33.85 the pencil case comes out and opens
{
  S(33.0, 33.85, 'office', (t) => ck(t, [OC(33.0, [59.97, 1.0, -1.42], 4, 32, 1.75, 45), OC(33.85, [60.0, 1.0, -1.42], 8, 33, 1.65, 44)]), (Wd, t) => {
    const Pn = principalSearching(t);
    const bag = X.bagO; bag.visible = true;
    bag.position.set(59.82, 0.775, -1.3); bag.rotation.set(0, 0.25, 0); bag.updateMatrixWorld(true); bag.userData.open(1.6);
    X.nb1.visible = true; X.nb1.position.set(60.22, 0.775, -1.2); X.nb1.rotation.set(0, 0.15, 0);
    const pc = X.pcase; pc.visible = true;
    const k = easeInOut(prog(t, 33.0, 33.35));
    pc.position.lerpVectors(V3(59.83, 1.12, -1.32), V3(60.02, 0.775, -1.42), k); pc.position.y += Math.sin(k * Math.PI) * 0.07;
    pc.rotation.set(0, Math.PI / 2 - 0.1, 0); pc.updateMatrixWorld(true);
    pc.userData.open(2.0 * easeInOut(prog(t, 33.4, 33.65)));
    palmAt(Pn, 'r', pc.position.clone().add(V3(0.0, 0.055, 0.02)), handQuat(Pn, [0, -0.5, 1], [0, -1, 0]), t < 33.4 ? 1 : 1 - smooth(prog(t, 33.4, 33.5)), null, 0.5);
    // the left hand flips the lid open
    const lidW = smooth(prog(t, 33.35, 33.45)) * (1 - smooth(prog(t, 33.68, 33.8)));
    palmAt(Pn, 'l', pc.position.clone().add(V3(0.0, 0.06 + 0.06 * prog(t, 33.4, 33.65), -0.03)), handQuat(Pn, [0, -0.5, 1], [0, -1, 0.3]), lidW, null, 0.4);
    look(Pn, pc.position, 1, 0.8);
  });
}
// S13c 33.85-35.50 even the label on your water bottle: peeled off, inspected
{
  S(33.85, 35.5, 'office', (t) => ck(t, [OC(33.85, [60.03, 1.52, -1.85], 12, 2, 1.15, 40), OC(35.5, [60.03, 1.52, -1.85], 10, 2, 0.95, 36)], (x) => x), (Wd, t) => {
    const Pn = PRIN();
    placeChar(Pn, DESK_O.x, DESK_O.z - 0.62, 0, { ...POSES.stand, spine: [0.05, 0, 0] });
    const b = X.bottle; b.visible = true;
    const hold = local(Pn, 0.06, 1.28, 0.33);
    b.position.copy(hold); b.rotation.set(0.15, Pn.root.rotation.y + 0.4, -0.2, 'YXZ'); b.updateMatrixWorld(true);
    b.userData.peel(0.85 * easeInOut(prog(t, 34.15, 35.25)));
    const bq = handQuat(Pn, [-0.9, 0, 0.4], [0.3, 0, 1]);
    palmAt(Pn, 'l', V3(0, 0.07, 0).applyMatrix4(b.matrixWorld).add(V3(0.0, 0, 0).applyQuaternion(b.quaternion)).add(local(Pn, 0.05, 0, -0.04).sub(Pn.root.position)), bq, 1, null, 0.75);
    // right fingers pinch the curling label edge and pull it away
    const pk = prog(t, 34.15, 35.25);
    const edge = V3(Math.sin(0.4 + pk * 2.6) * 0.06, 0.1, Math.cos(0.4 + pk * 2.6) * 0.06).applyMatrix4(b.matrixWorld);
    palmAt(Pn, 'r', edge.add(local(Pn, -0.03, 0, 0.02).sub(Pn.root.position)), handQuat(Pn, [0.6, 0.3, 0.8], [0.5, 0, -1]), smooth(prog(t, 33.95, 34.15)), local(Pn, -0.6, 0.8, -0.3), 0.6);
    look(Pn, b.position, 1, 0.95);
    Pn.expr = 'suspicious';
  });
}
// S14a 35.50-37.05 the classroom camera replays on the principal's monitor
function renderFeed(t, feedT) {
  const scn = W.scene, rnd = W.renderer;
  const vis = {}; for (const k in W.sets) vis[k] = W.sets[k].group.visible;
  for (const k in W.sets) W.sets[k].group.visible = k === 'class';
  // stage the classroom at the replayed moment (the final exam)
  const d = stageClass(feedT, { kidsOpt: { mode: 'write', paper: 'final' } });
  X.pFinal.setState({ answers: 1, bonus: prog(feedT, 27.2, 27.92), bonusBox: 0, name: 1 });
  const { h } = heroAtDesk(feedT, d, X.pFinal, { write: true });
  const T_ = teacherAtDesk(feedT, {});
  look(T_, V3(-1.05, 1.15, -2.2), 1, 0.9);
  for (const c of [...W.kids, ...Object.values(W.cast)]) if (c.root.visible) c.applyFace(false);
  const cam = X.feedCam;
  cam.position.set(CLASS.x1 - 0.35, 2.85, CLASS.z1 - 0.4); cam.lookAt(-1.2, 0.8, -2.0);
  const env = scn.environmentIntensity; scn.environmentIntensity = W.sets.class.env;
  rnd.setRenderTarget(X.feedRT); rnd.render(scn, cam); rnd.setRenderTarget(null);
  scn.environmentIntensity = env;
  for (const k in W.sets) W.sets[k].group.visible = vis[k];
  // clear the classroom staging
  for (const c of [...W.kids, ...Object.values(W.cast)]) { c.root.visible = false; c.resetFace(); }
  hideShotProps();
}
function drawFeedHud(t, rewind) {
  const sc = PR.monitor.userData.screen;
  const g = sc.g, w = sc.c.width, hgt = sc.c.height;
  // feed image is the render target; the HUD plane sits on top
  if (!X.hudPlane) {
    const hp = new THREE.Mesh(new THREE.PlaneGeometry(0.52, 0.325), new THREE.MeshBasicMaterial({ map: sc.tex, transparent: true }));
    hp.position.set(0, 0.33, 0.0192); PR.monitor.add(hp); X.hudPlane = hp;
  }
  X.hudPlane.visible = true;
  g.clearRect(0, 0, w, hgt);
  g.save();
  g.font = 'bold 44px "DejaVu Sans"'; g.fillStyle = '#f4f4f4'; g.strokeStyle = '#000'; g.lineWidth = 6;
  g.strokeText('CAM 3  •  ROOM 8B', 40, 70); g.fillText('CAM 3  •  ROOM 8B', 40, 70);
  const tc = 9 * 3600 + 41 * 60 + 12 + (rewind ? -(t - 35.5) * 40 : 0);
  g.font = '44px "DejaVu Sans"'; g.textAlign = 'right';
  g.strokeText(tcString(tc), w - 40, 70); g.fillText(tcString(tc), w - 40, 70);
  g.textAlign = 'left';
  if (rewind) { g.font = 'bold 90px "DejaVu Sans"'; g.strokeText('◀◀', 40, hgt - 50); g.fillText('◀◀', 40, hgt - 50); }
  g.fillStyle = Math.floor(t * 2) % 2 ? '#ff2a2a' : 'rgba(255,40,40,0.25)'; g.beginPath(); g.arc(w - 70, hgt - 80, 18, 0, Math.PI * 2); g.fill();
  g.restore();
  sc.tex.needsUpdate = true;
}
{
  S(35.5, 37.05, 'office', (t) => ck(t, [K3(35.5, [60.78, 1.3, -2.48], [60.55, 1.1, -1.52], 36), K3(37.05, [60.72, 1.25, -2.15], [60.55, 1.1, -1.52], 32)]), (Wd, t) => {
    renderFeed(t, 27.6 - (t - 35.5) * 1.6);
    PR.monitor.userData.useRT(X.feedRT.texture);
    drawFeedHud(t, true);
    const Pn = PRIN();
    placeChar(Pn, DESK_O.x, DESK_O.z - 0.75, 0.35, seated(POSES.sitDesk, Pn, 0.5));
    palmAt(Pn, 'l', local(Pn, 0.22, 0.785, 0.45), handQuat(Pn, [-0.25, 0, 1], [0, -1, 0]), 1, null, 0.2);
    palmAt(Pn, 'r', local(Pn, -0.22, 0.785, 0.45), handQuat(Pn, [0.25, 0, 1], [0, -1, 0]), 1, null, 0.2);
    look(Pn, V3(60.55, 1.1, -1.52), 1, 0.9);
    Pn.expr = 'focus';
    const T_ = T();
    placeChar(T_, 59.35, -1.95, 0.75, { ...POSES.stand, spine: [0.15, 0, 0] }); crossArms(T_);
    look(T_, V3(60.55, 1.1, -1.52), 1, 0.9);
    T_.expr = 'focus';
  }, { cctv: () => 0 });
}
// S14b 37.05-39.60 side by side: your answers vs the smartest kid's
{
  S(37.05, 39.6, 'office', (t) => ck(t, [OC(37.05, [59.9, 0.775, -1.38], 0, 62, 0.55, 40), OC(38.15, [59.92, 0.775, -1.38], 0, 62, 0.55, 40), OC(38.9, [60.1, 0.775, -1.45], 0, 65, 0.4, 38), OC(39.6, [60.1, 0.775, -1.45], 0, 66, 0.38, 37)]), (Wd, t) => {
    X.pFinal.setState({ answers: 1, bonus: 1, bonusBox: 1, name: 1, ticks: 3, score: 1 });
    const a = X.pFinal.group, b = X.pSmart.group;
    a.visible = b.visible = true;
    a.position.set(59.86, 0.775, -1.36); a.rotation.set(0, 0.03, 0); a.updateMatrixWorld(true);
    b.position.set(60.1, 0.7752, -1.37); b.rotation.set(0, -0.04, 0); b.updateMatrixWorld(true);
    const Pn = PRIN();
    placeChar(Pn, DESK_O.x, DESK_O.z - 0.62, 0, { ...POSES.stand, spine: [0.6, 0, 0], hipsZ: -0.08 });
    // red pen tip hops between matching answers on the two sheets
    const line = Math.floor(clamp((t - 37.1) / 0.42, 0, 5.99));
    const f = ((t - 37.1) / 0.42) % 1;
    const onA = line % 2 === 0;
    const sheet = onA ? a : b;
    const qi = Math.floor(line / 2);
    const tl = V3(-0.04, 0.012 + 0.02 * Math.sin(f * Math.PI), -0.1 + qi * 0.03 + 0.012).applyMatrix4(sheet.matrixWorld);
    show(X.redPen);
    writeWith(Pn, 'r', X.redPen, tl, 1, 0.2, local(Pn, -0.6, 0.8, -0.3));
    palmAt(Pn, 'l', local(Pn, 0.25, 0.785, 0.38), handQuat(Pn, [-0.25, 0, 1], [0, -1, 0]), 1, null, 0.2);
    look(Pn, tl, 1, 0.9);
  });
}
// S15 39.60-40.45 "Nothing." principal and teacher exchange a look
{
  S(39.6, 40.45, 'office', (t) => ck(t, [OC(39.6, [60.2, 1.62, -2.3], 0, 2, 2.15, 42), OC(40.45, [60.2, 1.62, -2.3], 4, 2, 2.0, 40)], (x) => x), (Wd, t) => {
    const Pn = PRIN();
    placeChar(Pn, DESK_O.x - 0.05, DESK_O.z - 0.75, 0, seated(POSES.sitDesk, Pn, 0.5));
    palmAt(Pn, 'l', local(Pn, 0.22, 0.785, 0.45), handQuat(Pn, [-0.25, 0, 1], [0, -1, 0]), 1, null, 0.2);
    palmAt(Pn, 'r', local(Pn, -0.22, 0.785, 0.45), handQuat(Pn, [0.25, 0, 1], [0, -1, 0]), 1, null, 0.2);
    const T_ = T();
    placeChar(T_, 60.55, -2.55, -0.25, POSES.stand); crossArms(T_);
    look(Pn, V3(60.55, 1.78, -2.5), 1, 0.95);
    look(T_, V3(59.95, 1.45, -2.1), 1, 0.95);
    Pn.J.head.rotation.y += Math.sin(prog(t, 39.85, 40.45) * Math.PI * 2) * 0.16; // slow head shake
    Pn.expr = 'worried'; T_.expr = 'stern';
  });
}
// S16 40.45-42.70 "No notes, no signals, no copying." the report on the monitor
function drawReport(t) {
  const sc = PR.monitor.userData.screen;
  const g = sc.g, w = sc.c.width, hgt = sc.c.height;
  g.fillStyle = '#050a06'; g.fillRect(0, 0, w, hgt);
  for (let y = 0; y < hgt; y += 4) { g.fillStyle = 'rgba(40,255,90,0.035)'; g.fillRect(0, y, w, 2); }
  g.fillStyle = '#4dff7a'; g.shadowColor = '#4dff7a'; g.shadowBlur = 18;
  g.textAlign = 'center';
  g.font = 'bold 56px "DejaVu Sans Mono"';
  g.fillText('INVESTIGATION REPORT', w / 2, 90);
  g.font = '36px "DejaVu Sans Mono"'; g.fillText('STUDENT: ADAM R.  CLASS: 8B', w / 2, 145);
  g.fillRect(60, 170, w - 120, 4);
  g.textAlign = 'left';
  const rows = [['HIDDEN NOTES', 40.49], ['SIGNALS', 41.13], ['COPYING', 41.77]];
  rows.forEach(([lab, ts], i) => {
    const y = 250 + i * 110;
    const k = prog(t, ts - 0.1, ts + 0.15);
    if (k <= 0) return;
    g.fillStyle = '#4dff7a'; g.font = 'bold 62px "DejaVu Sans Mono"';
    const txt = lab.slice(0, Math.ceil(lab.length * k));
    g.fillText(txt, 90, y);
    if (t > ts + 0.2) {
      g.fillStyle = '#ff4a3a'; g.shadowColor = '#ff4a3a';
      g.fillText('✗ NONE', w - 360, y);
      g.shadowColor = '#4dff7a';
    } else { g.fillText('.'.repeat(1 + Math.floor(t * 8) % 4), w - 360, y); }
  });
  if (t > 42.2) { g.fillStyle = '#4dff7a'; g.font = 'bold 48px "DejaVu Sans Mono"'; g.textAlign = 'center'; g.fillText('RESULT: NO EVIDENCE', w / 2, hgt - 50); g.textAlign = 'left'; }
  g.shadowBlur = 0;
  sc.tex.needsUpdate = true;
}
{
  S(40.45, 42.7, 'office', (t) => ck(t, [OC(40.45, [60.55, 1.08, -1.52], 205, 8, 1.5, 34), OC(42.7, [60.55, 1.08, -1.52], 205, 8, 1.36, 33)], (x) => x), (Wd, t) => {
    PR.monitor.userData.useCanvas();
    PR.pChair.visible = false;
    if (X.hudPlane) X.hudPlane.visible = false;
    drawReport(t);
  }, { bloom: 0.7 });
}
// S17 42.70-44.40 "But nobody believes you." you wait alone; behind you they shake their heads
{
  S(42.7, 44.4, 'office', (t) => ck(t, [K3(42.7, [60.42, 1.28, 2.62], [60.15, 1.45, -0.45], 34), K3(44.4, [60.38, 1.3, 2.5], [60.15, 1.47, -0.45], 31)], (x) => x), (Wd, t) => {
    const h = HERO();
    const ch = PR.waitChair;
    placeChar(h, ch.position.x, ch.position.z, Math.PI, seated(POSES.slump, h, ch.userData.seatH));
    palmAt(h, 'l', local(h, 0.1, 0.6, 0.3), handQuat(h, [-0.3, -0.2, 1], [0, -1, 0]), 1, null, 0.3);
    palmAt(h, 'r', local(h, -0.1, 0.6, 0.3), handQuat(h, [0.3, -0.2, 1], [0, -1, 0]), 1, null, 0.3);
    h.expr = 'sad';
    const Pn = PRIN(), T_ = T();
    placeChar(Pn, 59.88, -0.45, 0.25, POSES.stand); handsBehind(Pn);
    placeChar(T_, 60.43, -0.4, -0.3, POSES.stand); crossArms(T_);
    look(Pn, V3(60.43, 1.65, -0.4), 1, 0.9); look(T_, V3(59.88, 1.65, -0.45), 1, 0.9);
    Pn.J.head.rotation.y += Math.sin(prog(t, 42.9, 43.9) * Math.PI * 2) * 0.14;
    T_.J.head.rotation.y += Math.sin(prog(t, 43.2, 44.2) * Math.PI * 2) * 0.12;
    Pn.expr = 'stern'; T_.expr = 'stern';
  }, { sat: 0.95 });
}
// S18 44.40-46.05 "Your parents get a phone call." at home the phone buzzes; dad answers
{
  const pick = 45.0;
  S(44.4, 46.05, 'home', (t) => ck(t, [K3(44.4, [89.92, 1.5, 2.2], [89.55, 1.12, -0.6], 44), K3(45.05, [89.92, 1.5, 2.15], [89.55, 1.15, -0.6], 44), K3(46.05, [89.85, 1.55, 1.85], [89.55, 1.4, -0.6], 42)], (x) => x), (Wd, t) => {
    const ph = PR.phone;
    ph.userData.draw((g, w, hgt) => {
      g.fillStyle = '#0c1a2a'; g.fillRect(0, 0, w, hgt);
      g.fillStyle = '#fff'; g.font = 'bold 36px "Liberation Sans"'; g.textAlign = 'center';
      g.fillText('Westbrook School', w / 2, 160); g.font = '26px "Liberation Sans"'; g.fillText('incoming call…', w / 2, 205);
      g.fillStyle = '#2ac85a'; g.beginPath(); g.arc(w / 2 + 80, hgt - 110, 42, 0, Math.PI * 2); g.fill();
      g.fillStyle = '#e83a3a'; g.beginPath(); g.arc(w / 2 - 80, hgt - 110, 42, 0, Math.PI * 2); g.fill();
      const pulse = 0.5 + 0.5 * Math.sin(t * 12);
      g.strokeStyle = `rgba(42,200,90,${pulse})`; g.lineWidth = 6; g.beginPath(); g.arc(w / 2 + 80, hgt - 110, 54 + pulse * 10, 0, Math.PI * 2); g.stroke();
    });
    const dad = C.dad, mom = C.mom;
    PR.sideTable.position.set(89.62, 0, 0.25);
    placeChar(dad, 89.5, -0.42, 0.12, POSES.stand);
    const rest = { p: V3(89.62, 0.618, 0.25), q: E(0, 0.4, 0) };
    // buzzing on the table, then lifted to the ear
    const ear = local(dad, -0.13, 1.6, 0.05);
    dad.J.head.updateWorldMatrix(true, false);
    const earQ = dad.root.quaternion.clone().multiply(E(0, Math.PI / 2, Math.PI / 2 - 0.25)).multiply(E(0.0, 0, 0));
    const k = easeInOut(prog(t, pick + 0.12, pick + 0.62));
    if (t < pick + 0.12) {
      const bz = (Math.floor(t * 2.4) % 2 === 0) ? Math.sin(t * 160) * 0.003 : 0;
      ph.position.set(rest.p.x + bz, rest.p.y, rest.p.z); ph.quaternion.copy(rest.q);
    } else {
      ph.position.lerpVectors(rest.p, ear, k); ph.position.y += Math.sin(k * Math.PI) * 0.06;
      ph.quaternion.slerpQuaternions(rest.q, earQ, k);
    }
    ph.updateMatrixWorld(true);
    const reach = t < pick + 0.12 ? smooth(prog(t, pick - 0.3, pick + 0.12)) : 1;
    if (!ph.userData.holdEar) ph.userData.holdEar = new THREE.Matrix4().compose(V3(0.0, -0.075, 0.025), E(Math.PI / 2, 0, 0), V3(1, 1, 1));
    holdObj(dad, 'r', ph, reach, { pole: local(dad, -0.6, 0.6, -0.4) });
    setGrip(dad, 'r', 0.6);
    dad.J.spine.rotation.x += 0.35 * (1 - k) * reach;
    look(dad, t < pick + 0.4 ? ph.position : V3(90.3, 1.2, -1.7), 1, 0.9);
    dad.expr = t > pick + 0.5 ? 'worried' : 'neutral';
    dad.talk = t > pick + 0.75 ? 0.5 + 0.5 * Math.sin(t * 17) : 0;
    placeChar(mom, 89.95, HOME.z0 + 0.62, 0.15, seated(POSES.sit, mom, 0.53));
    palmAt(mom, 'l', local(mom, 0.1, 0.6, 0.32), handQuat(mom, [-0.3, 0, 1], [0, -1, 0]), 1, null, 0.3);
    palmAt(mom, 'r', local(mom, -0.06, 1.2, 0.18), handQuat(mom, [0.2, 1, 0.2], [0, 0, 1]), smooth(prog(t, 45.3, 45.7)), null, 0.2);
    look(mom, dad.J.head.getWorldPosition(V3()), 1, 0.9);
    mom.expr = t > 45.3 ? 'worried' : 'neutral';
  });
}
// S19 46.05-47.60 CANCELLED: the stamp slams onto your 100
{
  const hit = 46.94;
  S(46.05, 47.6, 'office', (t) => shakeCam(ck(t, [K3(46.05, [60.0, 1.22, -1.2], [60.0, 0.775, -1.4], 40), K3(47.6, [60.0, 1.16, -1.22], [60.0, 0.775, -1.4], 38)]), t, hit, 0.02), (Wd, t) => {
    const pg = X.pFinal.group; pg.visible = true;
    pg.position.set(60.0, 0.775, -1.4); pg.rotation.set(0, 0.02, 0); pg.updateMatrixWorld(true);
    X.pFinal.setState({ answers: 1, bonus: 1, bonusBox: 1, name: 1, ticks: 3, score: 1, stamp: t >= hit ? 1 : 0 });
    const Pn = PRIN();
    placeChar(Pn, DESK_O.x, DESK_O.z - 0.62, 0, { ...POSES.stand, spine: [0.45, 0, 0], hipsZ: -0.06 });
    const st = X.stamp; st.visible = true;
    const contact = V3(60.0, 0.7755, -1.43);
    const up = V3(60.03, 1.0, -1.5);
    let p;
    if (t < hit) { const k = prog(t, 46.35, hit); p = up.clone().lerp(contact, easeIn(k)); if (t < 46.35) p = up.clone().add(V3(0, 0.04 * (1 - prog(t, 46.05, 46.35)), 0)); }
    else { const k = prog(t, hit + 0.18, hit + 0.45); p = contact.clone().lerp(up, easeOut(k)); }
    st.position.copy(p); st.rotation.set(0, -0.22, 0); st.updateMatrixWorld(true);
    holdObj(Pn, 'r', st, 1, { pole: local(Pn, -0.6, 0.8, -0.4) });
    setGrip(Pn, 'r', 0.75);
    palmAt(Pn, 'l', local(Pn, 0.28, 0.785, 0.35), handQuat(Pn, [-0.25, 0, 1], [0, -1, 0]), 1, null, 0.2);
  }, { blur: (t) => (t > 46.7 && t < 46.97 ? 6 : 0) });
}
// S20 47.60-50.25 "By lunch, the whole school is whispering" - the corridor stares
const HALL_WALK2 = curve([[30.15, -5.6], [30.1, -7.4], [30.1, -9.3]]);
const WHISPER = [
  // [kid index, x, z, heading, role]  pairs either side of the walkway
  [3, 29.15, -7.4, 0.9, 'talk'], [5, 29.45, -7.95, 0.2, 'listen'],
  [7, 30.95, -8.3, -0.9, 'talk'], [9, 30.65, -8.85, -0.25, 'listen'],
  [11, 29.2, -10.4, 0.6, 'talk'], [12, 29.55, -10.95, 0.1, 'listen'], [13, 30.85, -10.9, -0.5, 'stare'], [14, 30.55, -11.7, -0.2, 'stare'],
];
function hallKids(t, heroPos, o = {}) {
  for (const [ki, x, z, hd, role] of WHISPER) {
    const ch = K[ki];
    placeChar(ch, x, z, hd, POSES.stand);
    const partner = WHISPER.find((w) => w !== WHISPER.find((q) => q[0] === ki) && Math.abs(w[2] - z) < 0.7 && (w[4] === 'listen' || w[4] === 'talk'));
    if (role === 'talk') {
      // leans to the friend's ear with a cupped hand
      ch.J.spine.rotation.x += 0.12; ch.J.spine.rotation.z += 0.08;
      const fr = partner ? K[partner[0]] : null;
      if (fr) {
        fr.root.updateMatrixWorld(true);
        const earP = local(fr, 0.12, 1.42 * fr.scale, 0.0);
        look(ch, earP, 1, 0.5);
        palmAt(ch, 'r', local(ch, -0.03, 1.35 * ch.scale, 0.2), handQuat(ch, [0, 1, 0.3], [-1, 0, 0.2]), 1, local(ch, -0.5, 0.6, 0), 0.35);
      }
      ch.talk = 0.5 + 0.5 * Math.sin(t * 15 + ki);
      // and glance at the hero
      const gl = smooth(clamp((Math.sin(t * 1.3 + ki) - 0.3) * 3));
      look(ch, heroPos, gl * 0.7, 0.9);
    } else {
      look(ch, heroPos, 1, 0.9);
      ch.expr = role === 'stare' ? 'suspicious' : 'surprised';
    }
  }
}
{
  S(47.6, 50.25, 'hall', (t) => {
    const k = clamp((t - 47.3) / 3.3);
    const p = HALL_WALK2.getPointAt(k * k * (3 - 2 * k));
    return { p: [p.x + 0.35, 1.75, p.z - 3.6], l: [p.x, 1.25, p.z + 0.4], fov: 50 };
  }, (Wd, t) => {
    const h = HERO();
    const wk = walkChar(h, HALL_WALK2, t, 47.3, 50.6, POSES.stand);
    h.J.neck.rotation.x += 0.35; h.J.spine.rotation.x += 0.08;
    h.expr = 'sad';
    h.J.spine.updateWorldMatrix(true, false);
    setWorldMatrix(X.bagO, h.J.spine.matrixWorld.clone().multiply(new THREE.Matrix4().compose(V3(0, 0.12, -0.2), E(0.05, Math.PI, 0), V3(1, 1, 1))));
    X.bagO.visible = true;
    hallKids(t, V3(wk.pos.x, 1.3, wk.pos.z));
  });
}
// S21 50.25-51.30 "Cheater." close on your face, the world tilted
{
  S(50.25, 51.3, 'hall', (t) => ck(t, [K3(50.25, [30.14, 1.64, -10.0], [30.1, 1.62, -9.3], 32, { roll: 0.1 }), K3(51.3, [30.13, 1.63, -9.85], [30.1, 1.62, -9.3], 28, { roll: 0.13 })], (x) => x), (Wd, t) => {
    const h = HERO();
    placeChar(h, 30.1, -9.3, Math.PI, POSES.stand);
    h.J.neck.rotation.x += 0.2;
    h.expr = 'sad';
    h.look = [0.3, 0.5];
    X.bagO.visible = true;
    h.J.spine.updateWorldMatrix(true, false);
    setWorldMatrix(X.bagO, h.J.spine.matrixWorld.clone().multiply(new THREE.Matrix4().compose(V3(0, 0.12, -0.2), E(0.05, Math.PI, 0), V3(1, 1, 1))));
    hallKids(t, V3(30.1, 1.3, -9.3));
  }, { sat: 0.85, vignette: 0.6 });
}
// S22 51.30-53.15 "So the principal makes a decision." at the window, he turns
{
  S(51.3, 53.15, 'office', (t) => ck(t, [K3(51.3, [61.1, 1.62, -2.85], [60.0, 1.55, -2.45], 40), K3(53.15, [61.0, 1.6, -2.82], [60.0, 1.58, -2.45], 36)], (x) => x), (Wd, t) => {
    const Pn = PRIN();
    placeChar(Pn, 60.0, -2.5, Math.PI, POSES.handsBack);
    const k = easeInOut(prog(t, 51.95, 52.6));
    Pn.J.spine.rotation.y -= 0.35 * k;
    Pn.J.neck.rotation.y -= 0.5 * k; Pn.J.head.rotation.y -= 0.6 * k;
    Pn.look = [0.6 * k, 0];
    Pn.expr = k > 0.5 ? 'stern' : 'neutral';
  }, { bloom: 0.55 });
}
// S23a 53.15-54.60 "A brand new exam" - the sealed envelope slides across to you
const TABLE = OFFICE.table;
function heroAtTable(t, o = {}) {
  const h = HERO();
  const seat = V3(TABLE.x, 0, TABLE.z + 0.45);
  placeChar(h, seat.x, seat.z, Math.PI, seated(o.pose || POSES.sitDesk, h, PR.examChair.userData.seatH));
  return h;
}
{
  S(53.15, 54.6, 'office', (t) => ck(t, [K3(53.15, [60.58, 0.96, 0.75], [60.0, 0.74, 0.92], 36), K3(54.6, [60.55, 0.97, 0.82], [60.0, 0.74, 0.95], 34)], (x) => x), (Wd, t) => {
    const h = heroAtTable(t);
    palmAt(h, 'l', local(h, 0.17, 0.728, 0.3), handQuat(h, [-0.3, 0, 1], [0, -1, 0]), 1, null, 0.2);
    palmAt(h, 'r', local(h, -0.17, 0.728, 0.3), handQuat(h, [0.3, 0, 1], [0, -1, 0]), 1, null, 0.2);
    h.expr = 'worried';
    look(h, V3(60.0, 0.73, 0.9), 1, 0.9);
    const Pn = PRIN();
    placeChar(Pn, TABLE.x + 0.05, TABLE.z - 0.62, 0, { ...POSES.stand, spine: [0.5, 0, 0], hipsZ: -0.06 });
    const env = X.envelope; env.visible = true;
    const k = easeInOut(prog(t, 53.35, 54.05));
    env.position.set(TABLE.x + 0.02, 0.721 + 0.02 * (1 - prog(t, 53.15, 53.35)), lerp(TABLE.z - 0.14, TABLE.z + 0.06, k)); env.rotation.set(0, 0.04, 0); env.updateMatrixWorld(true);
    const w = 1 - smooth(prog(t, 54.1, 54.4));
    palmAt(Pn, 'r', env.position.clone().add(V3(0.0, 0.016, -0.12)), handQuat(Pn, [0.1, -0.15, 1], [0, -1, 0]), w, local(Pn, -0.6, 0.6, -0.4), 0.15);
    look(Pn, V3(60.0, 1.15, 1.35), 1, 0.9);
    Pn.expr = 'stern';
  });
}
// S23b 54.60-57.50 alone in his office, three teachers watching your every move
function examRoom(t, o = {}) {
  const h = heroAtTable(t);
  const pg = X.pRetake.group; pg.visible = true;
  pg.position.copy(local(h, 0.0, 0.721, 0.42)); pg.rotation.set(0, 0, 0); pg.updateMatrixWorld(true);
  X.envelope.visible = true; X.envelope.position.set(TABLE.x + 0.28, 0.721, TABLE.z - 0.08); X.envelope.rotation.set(0, 0.5, 0);
  const T_ = T(), T2 = C.teacher2, T3 = C.teacher3, Pn = PRIN();
  placeChar(T_, 59.3, 0.55, 0.85, o.tPose || POSES.armsCrossed);
  placeChar(T2, 60.72, 0.45, -0.75, o.t2Pose || POSES.handsBack);
  placeChar(T3, 60.62, 2.0, Math.PI + 0.3, o.t3Pose || POSES.armsCrossed);
  placeChar(Pn, 60.0, -2.15, 0, POSES.armsCrossed);
  const focus = pg.position.clone().add(V3(0, 0.05, 0));
  for (const c of [T_, T2, T3]) { look(c, focus, 1, 0.9); c.expr = 'stern'; }
  look(Pn, V3(60, 1.1, 1.35), 1, 0.9); Pn.expr = 'stern';
  return { h, pg, T_, T2, T3, Pn };
}
{
  S(54.6, 57.5, 'office', (t) => {
    const a = lerp(0.62, 1.08, easeInOut(prog(t, 54.6, 57.5)));
    const r = 2.45;
    return { p: [TABLE.x + 0.1 + Math.sin(a) * r, lerp(2.25, 2.1, prog(t, 54.6, 57.5)), TABLE.z - 0.2 + Math.cos(a) * r], l: [TABLE.x + 0.1, 0.95, TABLE.z + 0.1], fov: 56 };
  }, (Wd, t) => {
    const lean = smooth(prog(t, 56.2, 56.8));
    const { h, pg, T3 } = examRoom(t, { t3Pose: blendPose(POSES.armsCrossed, { ...POSES.armsCrossed, spine: [0.35, 0, 0] }, lean) });
    X.pRetake.setState({ answers: 0, name: 1 });
    // pencil lies beside the paper; hands rest
    pencilOnDesk(X.retakePencil, h, -0.2, 0.36); X.retakePencil.position.y = 0.724;
    palmAt(h, 'l', local(h, 0.17, 0.728, 0.3), handQuat(h, [-0.3, 0, 1], [0, -1, 0]), 1, null, 0.2);
    palmAt(h, 'r', local(h, -0.12, 0.728, 0.28), handQuat(h, [0.3, 0, 1], [0, -1, 0]), 1, null, 0.2);
    look(h, pg.position, 1, 0.9);
    h.expr = 'worried';
  });
}
// S24 57.50-58.85 "You pick up your pencil."
function retakePencilRest(h) {
  const p = local(h, -0.2, 0.7245, 0.36);
  const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI / 2, h.root.rotation.y + 0.3, 0, 'YXZ'));
  q.setFromEuler(new THREE.Euler(0, 0, 0)); // rebuilt below
  const e = new THREE.Euler(Math.PI / 2, 0, h.root.rotation.y + 0.3, 'YXZ');
  return { p, q: new THREE.Quaternion().setFromEuler(e) };
}
{
  S(57.5, 58.85, 'office', (t) => ck(t, [K3(57.5, [60.0, 1.32, 1.2], [60.0, 0.725, 0.88], 48), K3(58.85, [60.0, 1.28, 1.16], [60.0, 0.725, 0.88], 46)], (x) => x), (Wd, t) => {
    const { h, pg } = examRoom(t);
    X.pRetake.setState({ answers: 0, name: 1 });
    palmAt(h, 'l', local(h, 0.17, 0.728, 0.3), handQuat(h, [-0.3, 0, 1], [0, -1, 0]), 1, null, 0.2);
    h.J.neck.visible = false; // point of view
    const pen = X.retakePencil; pen.visible = true;
    const rest = retakePencilRest(h);
    pg.updateMatrixWorld(true);
    const firstTip = X.pRetake.writeTip('ans', 0).applyMatrix4(pg.matrixWorld).add(V3(0, 0.012, 0));
    const writeP = toolPoseAt(h, 'r', pen, firstTip);
    // reach (hand comes to the resting pencil), grab, lift into a writing grip
    const reach = smooth(prog(t, 57.65, 58.0));
    const k = easeInOut(prog(t, 58.05, 58.55));
    pen.position.lerpVectors(rest.p, writeP.p, k); pen.position.y += Math.sin(k * Math.PI) * 0.025;
    pen.quaternion.slerpQuaternions(rest.q, writeP.q, k); pen.updateMatrixWorld(true);
    holdObj(h, 'r', pen, reach, { pole: local(h, -0.5, 0.75, -0.2) });
    setGrip(h, 'r', 0.25 + 0.3 * reach);
    look(h, pen.position, 1, 0.9);
    h.expr = 'calm';
  });
}
// S25a 58.85-60.00 "Twenty minutes later" - the wall clock races
{
  S(58.85, 60.0, 'office', (t) => ck(t, [K3(58.85, [62.25, 2.28, 1.2], [63.0, 2.3, 1.2], 34), K3(60.0, [62.4, 2.3, 1.2], [63.0, 2.3, 1.2], 30)], (x) => x), (Wd, t) => {
    const k = easeInOut(prog(t, 58.95, 59.85));
    const mins = 10 + 20 * k;
    X.officeClock.userData.set(10, mins, (mins * 60) % 60);
  }, { blur: (t) => (t > 59.0 && t < 59.8 ? 5 : 0) });
}
// S25b 60.00-61.00 "you put it down." finished paper; the pencil goes down
{
  S(60.0, 61.0, 'office', (t) => ck(t, [K3(60.0, [60.0, 1.3, 1.18], [60.0, 0.725, 0.88], 48), K3(61.0, [60.0, 1.3, 1.2], [60.0, 0.725, 0.88], 48)], (x) => x), (Wd, t) => {
    const { h, pg } = examRoom(t);
    X.pRetake.setState({ answers: 1, bonus: 1, bonusBox: 1, name: 1 });
    h.J.neck.visible = false; // point of view
    palmAt(h, 'l', local(h, 0.17, 0.728, 0.3), handQuat(h, [-0.3, 0, 1], [0, -1, 0]), 1, null, 0.2);
    const pen = X.retakePencil; pen.visible = true;
    pg.updateMatrixWorld(true);
    const lastTip = X.pRetake.boxTip(1).applyMatrix4(pg.matrixWorld);
    const from = toolPoseAt(h, 'r', pen, lastTip);
    const rest = retakePencilRest(h);
    const k = easeInOut(prog(t, 60.12, 60.5));
    pen.position.lerpVectors(from.p, rest.p, k); pen.position.y += Math.sin(k * Math.PI) * 0.03;
    pen.quaternion.slerpQuaternions(from.q, rest.q, k); pen.updateMatrixWorld(true);
    const rel = 1 - smooth(prog(t, 60.5, 60.75));
    holdObj(h, 'r', pen, rel, { pole: local(h, -0.5, 0.75, -0.2) });
    if (rel < 1) palmAt(h, 'r', local(h, -0.12, 0.728, 0.28), handQuat(h, [0.3, 0, 1], [0, -1, 0]), 1 - rel, null, 0.2);
    h.J.spine.rotation.x -= 0.12 * smooth(prog(t, 60.5, 60.95)); // sits back
    look(h, t < 60.6 ? pen.position : V3(59.3, 1.6, 0.55), 1, 0.9);
    h.expr = 'calm';
  });
}
// S26 61.00-64.35 they grade it right in front of you: three red ticks
function graderAt(t) {
  const T_ = T();
  return T_;
}
{
  S(61.0, 62.45, 'office', (t) => ck(t, [OC(61.0, [60.0, 1.15, 0.85], 60, 12, 2.4, 46), OC(62.45, [60.0, 1.15, 0.85], 56, 12, 2.2, 44)], (x) => x), (Wd, t) => {
    const k = smooth(prog(t, 61.0, 61.6));
    const { h, pg, T_, T2, T3 } = examRoom(t, { tPose: { ...POSES.stand, spine: [0.45 * k, 0, 0] }, t2Pose: { ...POSES.handsBack, spine: [0.2 * k, 0, 0] }, t3Pose: { ...POSES.armsCrossed, spine: [0.3 * k, 0, 0] } });
    X.pRetake.setState({ answers: 1, bonus: 1, bonusBox: 1, name: 1, ticks: 0 });
    // teacher moves to the table edge opposite you and uncaps the pen
    placeChar(T_, TABLE.x - 0.1, TABLE.z - 0.55, 0, { ...POSES.stand, spine: [0.5 * k, 0, 0], hipsZ: -0.05 * k });
    pg.updateMatrixWorld(true);
    const tip = X.pRetake.tickTip(0).applyMatrix4(pg.matrixWorld).add(V3(0, 0.06 * (1 - k) + 0.015, 0));
    show(X.redPen);
    writeWith(T_, 'r', X.redPen, tip, 1, 0.15, local(T_, -0.7, 0.6, -0.2));
    look(T_, pg.position, 1, 0.9); T_.expr = 'focus';
    palmAt(h, 'l', local(h, 0.17, 0.728, 0.3), handQuat(h, [-0.3, 0, 1], [0, -1, 0]), 1, null, 0.2);
    palmAt(h, 'r', local(h, -0.12, 0.728, 0.28), handQuat(h, [0.3, 0, 1], [0, -1, 0]), 1, null, 0.2);
    pencilOnDesk(X.retakePencil, h, -0.2, 0.36); X.retakePencil.position.y = 0.724;
    look(h, pg.position, 1, 0.9); h.expr = 'calm';
  });
}
const TICK_T = [[62.55, 62.85], [63.05, 63.35], [63.55, 63.85]];
function ticksAt(t) {
  let k = 0;
  TICK_T.forEach(([a, b], i) => { if (t >= a) k = i + prog(t, a, b); });
  return k;
}
{
  S(62.45, 64.35, 'office', (t) => ck(t, [K3(62.45, [60.02, 1.06, 1.2], [60.04, 0.725, 0.93], 40), K3(64.35, [60.02, 1.02, 1.16], [60.04, 0.725, 0.93], 37)], (x) => x), (Wd, t) => {
    const { h, pg, T_ } = examRoom(t, { tPose: { ...POSES.stand, spine: [0.5, 0, 0], hipsZ: -0.05 } });
    placeChar(T_, TABLE.x - 0.1, TABLE.z - 0.55, 0, { ...POSES.stand, spine: [0.5, 0, 0], hipsZ: -0.05 });
    const tk = ticksAt(t);
    X.pRetake.setState({ answers: 1, bonus: 1, bonusBox: 1, name: 1, ticks: tk });
    pg.updateMatrixWorld(true);
    // between ticks the pen lifts and travels down to the next answer
    let tipL;
    const i = TICK_T.findIndex(([a, b]) => t < b + 0.2);
    if (i < 0) tipL = lift(X.pRetake.tickTip(2.999), 0.02);
    else {
      const [a, b] = TICK_T[i];
      if (t < a) { const prev = i === 0 ? lift(X.pRetake.tickTip(0), 0.015) : lift(X.pRetake.tickTip(i - 0.001), 0.012); const nxt = X.pRetake.tickTip(i); tipL = prev.clone().lerp(nxt, easeInOut(prog(t, i === 0 ? 62.45 : TICK_T[i - 1][1], a))); tipL.y += 0.012 * Math.sin(prog(t, i === 0 ? 62.45 : TICK_T[i - 1][1], a) * Math.PI); }
      else if (t <= b) tipL = X.pRetake.tickTip(i + prog(t, a, b) * 0.999);
      else tipL = lift(X.pRetake.tickTip(i + 0.999), 0.012 * prog(t, b, b + 0.2));
    }
    const tip = tipL.applyMatrix4(pg.matrixWorld);
    show(X.redPen);
    writeWith(T_, 'r', X.redPen, tip, 1, 0.15, local(T_, -0.7, 0.6, -0.2));
    palmAt(h, 'l', local(h, 0.17, 0.728, 0.3), handQuat(h, [-0.3, 0, 1], [0, -1, 0]), 1, null, 0.2);
    palmAt(h, 'r', local(h, -0.12, 0.728, 0.28), handQuat(h, [0.3, 0, 1], [0, -1, 0]), 1, null, 0.2);
    pencilOnDesk(X.retakePencil, h, -0.2, 0.36); X.retakePencil.position.y = 0.724;
  });
}
// S27 64.35-65.80 "One hundred." the red 100, circled
{
  S(64.35, 65.8, 'office', (t) => ck(t, [K3(64.35, [60.05, 0.99, 1.08], [60.04, 0.721, 0.86], 34), K3(65.8, [60.05, 0.93, 1.0], [60.04, 0.721, 0.86], 32)]), (Wd, t) => {
    const { h, pg, T_ } = examRoom(t);
    placeChar(T_, TABLE.x - 0.1, TABLE.z - 0.55, 0, { ...POSES.stand, spine: [0.5, 0, 0], hipsZ: -0.05 });
    const k = prog(t, 64.38, 65.2);
    X.pRetake.setState({ answers: 1, bonus: 1, bonusBox: 1, name: 1, ticks: 3, score: k });
    pg.updateMatrixWorld(true);
    let tipL = X.pRetake.scoreTip(k);
    if (t > 65.2) tipL = lift(X.pRetake.scoreTip(1), 0.04 * easeOut(prog(t, 65.2, 65.5)));
    const tip = tipL.applyMatrix4(pg.matrixWorld);
    show(X.redPen);
    writeWith(T_, 'r', X.redPen, tip, 1, 0.15, local(T_, -0.7, 0.6, -0.2));
    palmAt(h, 'l', local(h, 0.17, 0.728, 0.3), handQuat(h, [-0.3, 0, 1], [0, -1, 0]), 1, null, 0.2);
    palmAt(h, 'r', local(h, -0.12, 0.728, 0.28), handQuat(h, [0.3, 0, 1], [0, -1, 0]), 1, null, 0.2);
    pencilOnDesk(X.retakePencil, h, -0.2, 0.36); X.retakePencil.position.y = 0.724;
  }, { blur: (t) => (t > 64.38 && t < 65.2 ? 3 : 0) });
}
// S28 65.80-67.30 "The room goes silent." everyone frozen
{
  S(65.8, 67.3, 'office', (t) => ck(t, [K3(65.8, [62.05, 1.95, 2.55], [60.0, 1.0, 0.55], 46), K3(67.3, [61.85, 1.85, 2.3], [60.0, 1.0, 0.6], 44)], (x) => x), (Wd, t) => {
    const { h, pg, T_, T2, T3, Pn } = examRoom(t, { tPose: { ...POSES.stand, spine: [0.1, 0, 0] }, t2Pose: POSES.stand, t3Pose: POSES.stand });
    X.pRetake.setState({ answers: 1, bonus: 1, bonusBox: 1, name: 1, ticks: 3, score: 1 });
    placeChar(T_, TABLE.x - 0.1, TABLE.z - 0.58, 0, { ...POSES.stand, spine: [0.08, 0, 0] });
    show(X.redPen);
    const tip = X.pRetake.scoreTip(1).applyMatrix4(pg.matrixWorld).add(V3(0.02, 0.09, -0.05));
    writeWith(T_, 'r', X.redPen, tip, 1, 0.4, local(T_, -0.7, 0.6, -0.2));
    for (const c of [T_, T2, T3]) { look(c, h.J.head.getWorldPosition(V3()), 1, 0.95); c.expr = 'shocked'; }
    Pn.expr = 'surprised';
    look(Pn, h.J.head.getWorldPosition(V3()), 1, 0.9);
    palmAt(h, 'l', local(h, 0.17, 0.728, 0.3), handQuat(h, [-0.3, 0, 1], [0, -1, 0]), 1, null, 0.2);
    palmAt(h, 'r', local(h, -0.12, 0.728, 0.28), handQuat(h, [0.3, 0, 1], [0, -1, 0]), 1, null, 0.2);
    pencilOnDesk(X.retakePencil, h, -0.2, 0.36); X.retakePencil.position.y = 0.724;
    h.expr = 'calm';
    look(h, V3(59.9, 1.6, 0.3), 1, 0.9);
  });
}
// S29 67.30-68.85 "Because you were never cheating." your calm smile
{
  S(67.3, 68.85, 'office', (t) => ck(t, [OC(67.3, [60.0, 1.25, 1.3], 162, 6, 1.1, 32), OC(68.85, [60.0, 1.25, 1.3], 166, 6, 0.95, 30)], (x) => x), (Wd, t) => {
    const { h, T_ } = examRoom(t);
    placeChar(T_, TABLE.x - 0.1, TABLE.z - 0.58, 0, POSES.stand);
    palmAt(h, 'l', local(h, 0.17, 0.728, 0.3), handQuat(h, [-0.3, 0, 1], [0, -1, 0]), 1, null, 0.2);
    palmAt(h, 'r', local(h, -0.12, 0.728, 0.28), handQuat(h, [0.3, 0, 1], [0, -1, 0]), 1, null, 0.2);
    look(h, V3(59.8, 1.62, 0.35), 1, 0.9);
    h.expr = t > 67.9 ? 'proud' : 'calm';
  }, { warm: 0.9 });
}
// S30a 68.85-70.60 every single night: you, a desk lamp, a pile of books
{
  S(68.85, 70.6, 'bedroom', (t) => ck(t, [K3(68.85, [BED.x - 0.44, 1.0, BED.z0 + 0.08], [BED.x - 0.4, 1.12, BED.z0 + 0.75], 60), K3(70.6, [BED.x - 0.44, 1.02, BED.z0 + 0.09], [BED.x - 0.4, 1.13, BED.z0 + 0.75], 56)], (x) => x), (Wd, t) => {
    const h = HERO();
    const seat = V3(BED.x - 0.4, 0, BED.z0 + 0.8);
    // a notebook open on the desk; he writes
    const nbP = X.p1.group; // reuse a sheet as the open notebook page
    X.p1.setState({ answers: 0.6 + 0.4 * prog(t, 68.85, 70.6), score: 0, ticks: 0, name: 1 });
    seatedWriter(h, seat.x, seat.z, Math.PI, nbP, X.heroPencil, t, 11, { seatH: PR.homeChair.userData.seatH, write: true });
    nbP.position.y = 0.7215; nbP.updateMatrixWorld(true);
    const tip = scribbleLocal(t, 11).applyMatrix4(nbP.matrixWorld);
    writeWith(h, 'r', X.heroPencil, tip, 1, 0, local(h, -0.5, 0.75, -0.2));
    look(h, tip, 1, 0.9);
    h.expr = 'focus';
    PR.alarm.userData.set(11, 48, (t * 1) % 60);
  }, { warm: 0.4, sat: 1.05 });
}
// S30b/c 70.60-72.65 while everyone else was on their phones
function phoneKid(t, ch, o) {
  const B = BED2;
  const sc = ch.scale;
  if (o.lying) {
    placeChar(ch, B.x, B.z0 + 0.25 + 1.79 * sc, 0, { ...POSES.stand, lShoulder: [0, 0, 0.15], rShoulder: [0, 0, -0.15] });
    ch.root.rotation.set(-Math.PI / 2, 0, 0); ch.root.position.y = 0.66; ch.root.updateMatrixWorld(true);
  } else {
    placeChar(ch, B.x, B.z0 + 0.35, 0, { ...POSES.sit, spine: [-0.28, 0, 0], neck: [0.3, 0, 0], lHip: [-1.45, 0, 0.08], rHip: [-1.45, 0, -0.08], lKnee: [0.15, 0, 0], rKnee: [0.15, 0, 0] });
    ch.root.position.y = 0.58 - (SIT_Y - 0.18) * sc; ch.root.updateMatrixWorld(true);
  }
  const ph = PR.phone2; ph.visible = true;
  ph.userData.draw((g, w, hgt) => {
    const grd = g.createLinearGradient(0, 0, 0, hgt); grd.addColorStop(0, '#2a5ad8'); grd.addColorStop(1, '#c83a8a');
    g.fillStyle = grd; g.fillRect(0, 0, w, hgt);
    const off = (t * 900) % 300;
    for (let i = -1; i < 4; i++) { g.fillStyle = 'rgba(255,255,255,0.85)'; g.fillRect(20, i * 300 - off + 60, w - 40, 200); g.fillStyle = 'rgba(0,0,0,0.25)'; g.fillRect(36, i * 300 - off + 80, 60, 60); }
  });
  // phone held in front of the face, screen towards the eyes
  ch.J.head.updateWorldMatrix(true, false);
  const eye = V3(0, 0.15 * sc, 0.1 * sc).applyMatrix4(ch.J.head.matrixWorld);
  const fwd = V3(0, 0, 1).transformDirection(ch.J.head.matrixWorld);
  const up = V3(0, 1, 0).transformDirection(ch.J.head.matrixWorld);
  const pp = eye.clone().addScaledVector(fwd, 0.3).addScaledVector(up, -0.05);
  ph.position.copy(pp);
  // phone local: screen faces +y; point it back at the face, long side along the head's up
  const m = new THREE.Matrix4().makeBasis(up.clone().cross(fwd).normalize(), fwd.clone().negate(), up.clone().negate());
  ph.quaternion.setFromRotationMatrix(m);
  ph.updateMatrixWorld(true);
  const pq = ph.quaternion.clone();
  for (const [L, dx] of (o.lying ? [['r', 0.03], ['l', -0.03]] : [['r', 0.0]])) {
    const gp = V3(dx * 0.9, -0.004, 0.035).applyMatrix4(ph.matrixWorld);
    palmAt(ch, L, gp, pq.clone().multiply(E(Math.PI / 2, 0, L === 'r' ? 0.3 : -0.3)), 1, local(ch, L === 'r' ? -0.5 : 0.5, 0.6, -0.3), 0.55);
  }
  if (!o.lying) palmAt(ch, 'l', local(ch, 0.16, ch.root.position.y + 0.42 * sc, 0.3), handQuat(ch, [-0.2, 0, 1], [0, -1, 0]), 1, null, 0.3);
  ch.J.rFingers.thumb.rotation.x = -0.4 + 0.25 * Math.sin(t * 9);
  ch.look = [0, 0.15];
  const Lt = W.sets.bedroom2.phoneLight; Lt.position.copy(pp).addScaledVector(fwd, -0.06); Lt.intensity = 0.45 + 0.08 * Math.sin(t * 7);
  ch.expr = 'neutral';
}
{
  S(70.6, 71.65, 'bedroom2', (t) => ck(t, [OC(70.6, [BED2.x, 0.8, BED2.z0 + 0.3], 90, 32, 0.9, 44, { roll: -Math.PI / 2 }), OC(71.65, [BED2.x, 0.8, BED2.z0 + 0.3], 98, 34, 0.82, 42, { roll: -Math.PI / 2 })], (x) => x), (Wd, t) => {
    phoneKid(t, K[2], { lying: true });
  }, { sat: 1.0 });
  S(71.65, 72.65, 'bedroom2', (t) => ck(t, [OC(71.65, [BED2.x, 1.3, BED2.z0 + 0.45], 48, 6, 1.15, 42), OC(72.65, [BED2.x, 1.3, BED2.z0 + 0.45], 54, 6, 1.05, 40)], (x) => x), (Wd, t) => {
    phoneKid(t, K[8], { lying: false });
  }, { sat: 1.0 });
}
// S31a 72.65-74.00 the principal apologises: a handshake
{
  S(72.65, 74.0, 'office', (t) => ck(t, [OC(72.65, [61.0, 1.38, 1.0], 270, 6, 2.6, 44), OC(74.0, [61.0, 1.38, 1.0], 276, 6, 2.4, 42)], (x) => x), (Wd, t) => {
    const h = HERO(), Pn = PRIN();
    placeChar(h, 61.02, 1.36, Math.PI, POSES.stand);
    placeChar(Pn, 61.0, 0.62, 0, POSES.stand);
    const pump = Math.sin((t - 72.95) * Math.PI * 2 * 2.2) * 0.025 * smooth(prog(t, 72.95, 73.1)) * (1 - smooth(prog(t, 73.6, 73.75)));
    const meet = V3(61.0, 1.0 + pump, 0.99);
    const k = smooth(prog(t, 72.65, 72.95));
    // palms face each other, thumbs up
    palmAt(Pn, 'r', meet.clone().add(V3(-0.012, 0, -0.02)), handQuat(Pn, [0.25, 0, 1], [1, 0.1, 0]), k, local(Pn, -0.5, 0.6, -0.3), 0.6);
    palmAt(h, 'r', meet.clone().add(V3(0.012, 0, 0.02)), handQuat(h, [0.25, 0, 1], [1, 0.1, 0]), k, local(h, -0.5, 0.6, -0.3), 0.6);
    Pn.J.spine.rotation.x += 0.12 * Math.sin(prog(t, 73.0, 73.6) * Math.PI); // slight bow
    look(Pn, h.J.head.getWorldPosition(V3()), 1, 0.9);
    look(h, Pn.J.head.getWorldPosition(V3()), 1, 0.9);
    Pn.expr = t < 73.1 ? 'worried' : 'smile';
    Pn.talk = t > 72.75 && t < 73.6 ? 0.5 + 0.5 * Math.sin(t * 16) : 0;
    h.expr = 'smile';
    const T_ = T(), T2 = C.teacher2;
    placeChar(T_, 59.6, 0.2, 0.9, POSES.stand); placeChar(T2, 59.9, -0.25, 0.7, POSES.handsBack);
    look(T_, meet, 1, 0.8); look(T2, meet, 1, 0.8); T_.expr = 'smile'; T2.expr = 'smile';
  });
}
// S31b 74.00-75.85 your portrait goes up on the wall of honor
{
  const slot = () => W.anchors.honorSlot;
  S(74.0, 75.85, 'hall', (t) => ck(t, [K3(74.0, [30.05, 1.75, -14.3], [31.4, 1.5, -16.4], 48), K3(75.85, [30.35, 1.7, -14.9], [31.55, 1.55, -16.5], 44)], (x) => x), (Wd, t) => {
    const s = slot();
    const Pn = PRIN(), h = HERO();
    placeChar(Pn, 31.0, -16.55, Math.PI / 2, POSES.stand);
    placeChar(h, 30.15, -15.75, 2.0, POSES.stand);
    const fr = X.heroFrame; fr.visible = true;
    const held = V3(31.3, 1.25, -16.55);
    const k = easeInOut(prog(t, 74.15, 74.75));
    fr.position.lerpVectors(held, s, k); fr.rotation.set(0, -Math.PI / 2, 0); fr.updateMatrixWorld(true);
    const w = 1 - smooth(prog(t, 74.85, 75.15));
    for (const [L, dz] of [['l', -0.235], ['r', 0.235]]) {
      // the frame's local x runs along world -z here; hands on its sides
      const g = V3(L === 'l' ? 0.235 : -0.235, 0.0, 0.01).applyMatrix4(fr.matrixWorld);
      palmAt(Pn, L, g, handQuat(Pn, [L === 'l' ? -0.3 : 0.3, 0.5, 1], [L === 'l' ? -1 : 1, 0, 0]), w, local(Pn, L === 'l' ? 0.6 : -0.6, 0.6, -0.3), 0.3);
    }
    look(Pn, fr.position, 1, 0.9); Pn.expr = 'smile';
    look(h, fr.position, 1, 0.9); h.expr = t > 74.8 ? 'happy' : 'smile';
  });
}
// S32a 75.85-77.02 and your desk gets moved again...
{
  S(75.85, 77.02, 'class', (t) => ck(t, [K3(75.85, [-3.05, 2.55, 3.95], [-0.9, 0.8, -1.4], 50), K3(77.02, [-2.95, 2.5, 3.8], [-0.8, 0.8, -0.6], 50)], (x) => x), (Wd, t) => {
    const d = stageClass(t, { kidsOpt: { mode: 'look', target: V3(heroDeskState(t).x, 1.0, heroDeskState(t).z), lookW: () => 0.8 } });
    X.pDone.group.visible = true; PR.heroDesk.updateMatrixWorld(true);
    setWorldMatrix(X.pDone.group, PR.heroDesk.matrixWorld.clone().multiply(new THREE.Matrix4().compose(V3(0, 0.6625, -0.04), E(0, 0, 0), V3(1, 1, 1))));
    const h = heroPushing(t, d);
    h.expr = 'happy';
    const T_ = T();
    placeChar(T_, -0.6, -3.35, 0.15, POSES.stand);
    // points to the back of the room with a smile
    const k = smooth(prog(t, 76.0, 76.35));
    const sh = local(T_, 0.2, 1.47, 0);
    const dir = V3(0, 1.2, 3.6).sub(sh).normalize();
    const fy = dir.clone().negate();
    const pz = V3(-0.3, -1, 0).sub(dir.clone().multiplyScalar(V3(-0.3, -1, 0).dot(dir))).normalize();
    const hq = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(new THREE.Vector3().crossVectors(fy, pz), fy, pz));
    armIK(T_, 'l', sh.clone().add(dir.multiplyScalar(0.52)), { hand: hq, w: k, pole: local(T_, 0.6, 1.0, -0.4) });
    setGrip(T_, 'l', 0.7);
    look(T_, V3(d.x, 1.2, d.z), 1, 0.9);
    T_.expr = 'grin';
  });
}
// S32b 77.02-78.25 ...to the very back.
{
  S(77.02, 78.25, 'class', (t) => ck(t, [OC(77.02, [-0.15, 0.95, 3.15], 265, 14, 2.4, 46), OC(78.25, [-0.1, 0.95, 3.4], 262, 14, 2.3, 44)], (x) => x), (Wd, t) => {
    const d = stageClass(t, { deskT: Math.min(t, MOVE.b2[1] - 1e-4), kidsOpt: { mode: 'look', target: V3(heroDeskState(Math.min(t, MOVE.b2[1] - 1e-4)).x, 1.0, heroDeskState(Math.min(t, MOVE.b2[1] - 1e-4)).z), lookW: () => 0.7 } });
    X.pDone.group.visible = true; PR.heroDesk.updateMatrixWorld(true);
    setWorldMatrix(X.pDone.group, PR.heroDesk.matrixWorld.clone().multiply(new THREE.Matrix4().compose(V3(0, 0.6625, -0.04), E(0, 0, 0), V3(1, 1, 1))));
    const h = heroPushing(t, d);
    h.expr = 'happy';
  });
}
// S33 78.25-81.00 This time, so nobody can copy you - the whole class cranes back
{
  S(78.25, 81.0, 'class', (t) => ck(t, [K3(78.25, [0.14, 1.62, 4.5], [-0.12, 1.0, 1.0], 50), K3(81.0, [0.12, 1.55, 4.38], [-0.14, 1.0, 1.0], 48)], (x) => x), (Wd, t) => {
    const heroP = V3(0, 0.9, 3.75);
    const crane = (m, i) => smooth(prog(t, 78.5 + hash(i, 11) * 1.0, 79.1 + hash(i, 11) * 1.0));
    const d = stageClass(t, { kidsOpt: { mode: 'crane', target: heroP, craneK: crane } });
    X.pDone.group.visible = true;
    const { h } = heroAtDesk(t, d, X.pDone, { write: true });
    const up = smooth(prog(t, 79.9, 80.3));
    look(h, V3(0, 1.3, 2.5), up * 0.6, 0.9);
    h.expr = up > 0.5 ? 'smile' : 'focus';
    const T_ = T();
    placeChar(T_, -0.5, -3.3, 0.12, POSES.stand); crossArms(T_);
    look(T_, V3(0, 1.2, 3.8), 1, 0.9);
    T_.J.head.rotation.y += Math.sin(prog(t, 79.6, 80.8) * Math.PI * 2) * 0.12;
    T_.expr = 'grin';
  });
}
