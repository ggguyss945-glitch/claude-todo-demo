// Channel branding stills, rendered with the film's own cast, sets and grade.
// Loaded only with ?brand=1. The shots sit past the end of the film (t >= 200):
//   200: square logo, the hero with a director's clapperboard
//   210: banner group portrait (2048x1152), the middle left clear for the channel name
//   211: the same banner with the cast hidden (a clean plate for the depth-of-field composite)
//   220: first-video thumbnail (2160x3840): the teacher looms over the hero with his 100
//   221: the same thumbnail without the two leads (plate for the depth-of-field composite)
import * as THREE from 'three';
import { POSES, EXPR } from './chars.js';
import { V3, placeChar, handQuat, palmAt, local, look } from './anim.js';
import { SHOTS } from './shots.js';
import { X, seatedWriter } from './stage.js';
import { canvas, toTex } from './tex.js';

export const BRAND = { name: 'POLYWIT' };

// a film slate: black board with chalk lines, striped fixed bar, striped clapper stick hinged at the left
function clapperboard() {
  const g = new THREE.Group();
  const BW = 0.30, BH = 0.235, T = 0.012;
  const [c, x] = canvas(1200, 940);
  x.fillStyle = '#17171b'; x.fillRect(0, 0, 1200, 940);
  x.strokeStyle = 'rgba(240,240,232,0.92)'; x.lineWidth = 7;
  const line = (a, b, cc, d) => { x.beginPath(); x.moveTo(a, b); x.lineTo(cc, d); x.stroke(); };
  line(40, 330, 1160, 330); line(40, 560, 1160, 560); line(40, 760, 1160, 760); line(420, 330, 420, 760); line(800, 330, 800, 760);
  x.fillStyle = '#f2efe6'; x.textAlign = 'center';
  x.font = '230px "Lilita One"'; x.fillText(BRAND.name, 600, 270);
  x.font = '64px "Lilita One"';
  x.fillText('SCENE', 230, 400); x.fillText('TAKE', 610, 400); x.fillText('ROLL', 980, 400);
  x.font = '150px "Lilita One"';
  x.fillText('01', 230, 530); x.fillText('01', 610, 530); x.fillText('A', 980, 530);
  x.font = '64px "Lilita One"'; x.textAlign = 'left';
  x.fillText('DIRECTOR', 70, 680); x.fillText('STORY', 70, 870);
  x.fillStyle = '#ff3b3f'; x.font = '96px "Lilita One"';
  x.fillText('YOU', 470, 690); x.fillText('PERFECT SCORE', 470, 880);
  const faceMat = new THREE.MeshStandardMaterial({ map: toTex(c), roughness: 0.85 });
  const dark = new THREE.MeshStandardMaterial({ color: '#141418', roughness: 0.7 });
  const board = new THREE.Mesh(new THREE.BoxGeometry(BW, BH, T), [dark, dark, dark, dark, faceMat, dark]);
  board.castShadow = true; g.add(board);
  // striped bars
  const [sc, sx] = canvas(1024, 160);
  sx.fillStyle = '#f4f4f0'; sx.fillRect(0, 0, 1024, 160);
  sx.fillStyle = '#121216';
  for (let i = -2; i < 12; i++) { sx.beginPath(); sx.moveTo(i * 110, 160); sx.lineTo(i * 110 + 55, 160); sx.lineTo(i * 110 + 115, 0); sx.lineTo(i * 110 + 60, 0); sx.closePath(); sx.fill(); }
  const stripe = new THREE.MeshStandardMaterial({ map: toTex(sc), roughness: 0.6 });
  const barGeo = new THREE.BoxGeometry(BW, 0.042, T * 1.15);
  const bar = new THREE.Mesh(barGeo, [dark, dark, dark, dark, stripe, dark]);
  bar.position.y = BH / 2 + 0.021; bar.castShadow = true; g.add(bar);
  const hinge = new THREE.Group(); hinge.position.set(-BW / 2, BH / 2 + 0.042, 0); g.add(hinge);
  const stick = new THREE.Mesh(barGeo, [dark, dark, dark, dark, stripe, dark]);
  stick.position.set(BW / 2, 0.021, 0.001); stick.castShadow = true; hinge.add(stick);
  hinge.rotation.z = 0.42; // open, about to clap
  const pin = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, T * 1.6, 12), new THREE.MeshStandardMaterial({ color: '#9a9aa2', metalness: 0.8, roughness: 0.3 }));
  pin.rotation.x = Math.PI / 2; pin.position.set(-BW / 2 + 0.012, BH / 2 + 0.042, 0); g.add(pin);
  g.userData = { BW, BH };
  return g;
}

// deep navy backdrop with soft low-poly facets (the red ring is added in the 2D finishing pass)
function logoBackdrop() {
  const N = 2048;
  const [c, x] = canvas(N, N);
  const grd = x.createRadialGradient(N / 2, N * 0.42, 40, N / 2, N / 2, N * 0.72);
  grd.addColorStop(0, '#34508c'); grd.addColorStop(0.55, '#1d2c58'); grd.addColorStop(1, '#0c1430');
  x.fillStyle = grd; x.fillRect(0, 0, N, N);
  // facets: a jittered triangle grid, each triangle a touch lighter or darker
  let s = 7; const r = () => ((s = (s * 16807) % 2147483647) / 2147483647);
  const G = 11, P = [];
  for (let j = 0; j <= G; j++) for (let i = 0; i <= G; i++) P.push([i * N / G + (i % G ? (r() - 0.5) * 120 : 0), j * N / G + (j % G ? (r() - 0.5) * 120 : 0)]);
  for (let j = 0; j < G; j++) for (let i = 0; i < G; i++) {
    const a = P[j * (G + 1) + i], b = P[j * (G + 1) + i + 1], cc = P[(j + 1) * (G + 1) + i], d = P[(j + 1) * (G + 1) + i + 1];
    for (const tri of [[a, b, d], [a, d, cc]]) {
      const v = r();
      x.fillStyle = v < 0.5 ? `rgba(255,255,255,${0.012 + v * 0.05})` : `rgba(0,0,20,${0.02 + (v - 0.5) * 0.12})`;
      x.beginPath(); x.moveTo(...tri[0]); x.lineTo(...tri[1]); x.lineTo(...tri[2]); x.closePath(); x.fill();
    }
  }
  return new THREE.Mesh(new THREE.PlaneGeometry(2.4, 2.4), new THREE.MeshBasicMaterial({ map: toTex(c), toneMapped: false }));
}

export async function addBrandShots(world) {
  const ff = new FontFace('Lilita One', 'url(fonts/LilitaOne.ttf)'); document.fonts.add(await ff.load());
  const scene = world.scene;
  const slate = clapperboard(); slate.visible = false; scene.add(slate);
  const back = logoBackdrop(); back.visible = false; scene.add(back);
  X.all.push(slate, back); // hidden again at the start of every frame
  const C = world.cast;
  const HX = 0.3, HZ = -2.5; // hero spot for the logo, in front of the whiteboard

  // ---- 200: logo
  SHOTS.push({
    t0: 200, t1: 205, set: 'class', vignette: 0.2, warm: 0.2,
    cam: () => ({ p: [HX, 1.62, HZ + 1.6], l: [HX, 1.405, HZ], fov: 31 }), // just above eye level: the flat-top hair reads; head clear of the ring
    setup: (Wd, t) => {
      const h = C.you;
      placeChar(h, HX, HZ, 0, POSES.stand);
      back.visible = true; back.position.set(HX, 1.3, HZ - 0.75);
      // slate held up at chest height, tipped a little toward the light
      slate.visible = true;
      slate.position.copy(local(h, 0.02, 1.12, 0.3));
      slate.rotation.set(-0.08, 0.0, 0.06); slate.updateMatrixWorld(true);
      const { BW, BH } = slate.userData;
      const edge = (sx, sy) => V3(sx * BW / 2, sy * BH / 2, 0).applyMatrix4(slate.matrixWorld);
      // hands grip the two lower sides of the board, thumbs in front
      palmAt(h, 'l', edge(1.02, -0.35).add(V3(0.015, 0, -0.01)), handQuat(h, [0.2, 1, 0.15], [-1, 0, 0.3]), 1, local(h, 0.6, 0.6, -0.3), 0.75);
      palmAt(h, 'r', edge(-1.02, -0.35).add(V3(-0.015, 0, -0.01)), handQuat(h, [-0.2, 1, 0.15], [1, 0, 0.3]), 1, local(h, -0.6, 0.6, -0.3), 0.75);
      look(h, V3(HX + 0.02, 1.62, HZ + 1.6), 1, 1);
      h.expr = 'grin';
    },
  });

  // ---- 210/211: banner group portrait
  // the safe area every device shows (1235x338 of 2048x1152) spans x = CX -1.4 .. +1.4 m and
  // y = 1.20 .. 1.96 m at the cast's depth: the hero and the teacher sit inside it either side of
  // the name, the smartest kid and the principal stand further out for the desktop/TV widths
  const Z = -2.25, CX = 0.3;
  const spots = {
    smart: [CX - 1.88, Z - 0.35, 0.3], you: [CX - 1.08, Z, 0.16],
    teacher: [CX + 1.08, Z, -0.18], principal: [CX + 1.88, Z - 0.35, -0.28],
  };
  const banner = (empty) => (Wd, t) => {
    if (empty) return;
    const [sx, sz, sh] = spots.smart, [yx, yz, yh] = spots.you, [tx, tz, th] = spots.teacher, [px, pz, ph] = spots.principal;
    const camP = V3(CX, 1.62, 2.15);
    // the hero shows off his 100
    const h = C.you; placeChar(h, yx, yz, yh, POSES.stand);
    const pg = X.pDone.group; pg.visible = true;
    pg.position.copy(local(h, 0.0, 1.25, 0.3)); pg.rotation.set(Math.PI / 2 - 0.12, 0, 0);
    pg.rotateOnWorldAxis(V3(0, 1, 0), yh); pg.updateMatrixWorld(true);
    const pc = (u, v) => V3(u * 0.105, 0.002, v * 0.1485).applyMatrix4(pg.matrixWorld);
    // hands behind the lower corners so the red 100 at the top stays clear
    palmAt(h, 'l', pc(0.98, 0.5).add(V3(0, 0, -0.012)), handQuat(h, [0.15, 1, 0], [0, 0, 1]), 1, local(h, 0.6, 0.7, -0.3), 0.85);
    palmAt(h, 'r', pc(-0.98, 0.5).add(V3(0, 0, -0.012)), handQuat(h, [-0.15, 1, 0], [0, 0, 1]), 1, local(h, -0.6, 0.7, -0.3), 0.85);
    look(h, camP, 1, 1); h.expr = 'grin';
    // the teacher isn't convinced
    const T_ = C.teacher; placeChar(T_, tx, tz, th, POSES.armsCrossed);
    look(T_, h.J.head.getWorldPosition(V3()).add(V3(0.1, 0.05, 0)), 0.85, 1); T_.expr = 'suspicious';
    // the principal, hands behind his back, amused
    const Pn = C.principal; placeChar(Pn, px, pz, ph, POSES.handsBack);
    look(Pn, camP, 0.9, 1); Pn.expr = 'smile';
    // the smartest kid peers at the 100
    const sm = C.smart; placeChar(sm, sx, sz, sh, POSES.stand);
    look(sm, pc(0, -0.5), 0.9, 1); sm.expr = 'surprised';
  };
  const bannerCam = () => ({ p: [CX, 1.62, 2.15], l: [CX, 1.58, Z], fov: 33 });
  SHOTS.push({ t0: 210, t1: 211, set: 'class', vignette: 0.12, cam: bannerCam, setup: banner(false) });
  SHOTS.push({ t0: 211, t1: 212, set: 'class', vignette: 0.12, cam: bannerCam, setup: banner(true) });

  // ---- 220/221: thumbnail for "Perfect Score"
  // the hero at a front-row desk holding up his 100, shocked, eyes on the viewer; the teacher right behind
  // him with arms crossed; the class behind them all turned to stare. The lower half of the paper is
  // left clear for the "CHEATER?" stamp added in the finishing pass
  EXPR.thumbShock = { browRaise: 2.1, eyeOpen: 1.7, irisK: 0.7, mouthOpen: 1.6, smile: -0.15 };
  EXPR.thumbAngry = { frown: 1.5, eyeOpen: 0.82, smile: -0.7, mouthOpen: 0.3 };
  const seats = world.class.seats;
  const seatAt = (ci, ri) => seats.find((q) => q.ci === ci && q.ri === ri);
  const HS = seatAt(2, 0);
  const watchers = [[1, 1, 3], [1, 2, 6], [2, 1, 9], [2, 2, 12], [3, 1, 1], [3, 2, 14], [1, 3, 5], [2, 3, 8], [0, 1, 11], [0, 2, 16]];
  const rim = new THREE.SpotLight('#fff0dc', 14, 6, 0.6, 0.6, 1.5);
  rim.position.set(HS.x - 0.7, 2.7, HS.z + 1.7); scene.add(rim); scene.add(rim.target); X.all.push(rim);
  // soft key from the camera side so the hero's face, the focal point, is the brightest thing in frame
  const key = new THREE.SpotLight('#fff3e4', 9, 5, 0.45, 0.8, 1.5);
  key.position.set(HS.x + 0.55, 1.95, HS.z - 1.7); scene.add(key); scene.add(key.target); X.all.push(key);
  const thumbCam = () => ({ p: [HS.x + 0.1, 1.1, HS.z - 1.18], l: [HS.x + 0.05, 1.22, HS.z + 0.3], fov: 58 });
  const thumb = (leads) => (Wd, t) => {
    const camP = V3(...thumbCam().p);
    const h = C.you;
    const headOf = (c) => c.J.head.getWorldPosition(V3()).add(V3(0, 0.1, 0));
    if (leads) {
      h.faceRes = 2048; C.teacher.faceRes = 1280;
      seatedWriter(h, HS.x, HS.z, Math.PI, null, null, t, 1, { write: false, leftHand: false });
      // he holds up his paper, the red 100 facing the viewer
      const pg = X.pDone.group; pg.visible = true;
      pg.position.copy(local(h, 0.0, 0.97, 0.34));
      pg.rotation.set(Math.PI / 2 - 0.16, 0, 0); pg.rotateOnWorldAxis(V3(0, 1, 0), Math.PI - 0.05);
      pg.updateMatrixWorld(true);
      const pc = (u, v) => V3(u * 0.105, 0.002, v * 0.1485).applyMatrix4(pg.matrixWorld);
      palmAt(h, 'l', pc(0.98, 0.45).add(V3(0, 0, 0.012)), handQuat(h, [0.15, 1, 0], [0, 0, 1]), 1, local(h, 0.6, 0.7, -0.3), 0.85);
      palmAt(h, 'r', pc(-0.98, 0.45).add(V3(0, 0, 0.012)), handQuat(h, [-0.15, 1, 0], [0, 0, 1]), 1, local(h, -0.6, 0.7, -0.3), 0.85);
      look(h, camP, 1, 1); h.expr = 'thumbShock';
      // the teacher right behind him, arms crossed, glaring down at him
      const T_ = C.teacher;
      placeChar(T_, HS.x + 0.32, HS.z + 0.42, Math.PI - 0.22, { ...POSES.armsCrossed, spine: [0.22, 0, 0], neck: [0.1, 0, 0] });
      look(T_, headOf(h), 1, 1); T_.expr = 'thumbAngry';
      rim.visible = true; rim.target.position.copy(headOf(h)); rim.target.updateMatrixWorld();
      key.visible = true; key.target.position.copy(h.J.head.getWorldPosition(V3()).add(V3(0, 0.08, 0))); key.target.updateMatrixWorld();
    }
    // the class stares at the hero
    const faces = ['surprised', 'shocked', 'suspicious', 'surprised', 'worried', 'shocked', 'suspicious', 'surprised', 'shocked', 'worried'];
    watchers.forEach(([ci, ri, k], i) => {
      const st = seatAt(ci, ri), kid = world.kids[k];
      seatedWriter(kid, st.x, st.z, Math.PI, X.kidPapers[i], null, t, i * 1.37 + 0.5, { write: false });
      kid.J.spine.rotation.y += (st.x > HS.x ? -0.25 : st.x < HS.x ? 0.25 : 0);
      look(kid, V3(HS.x, 1.12, HS.z), 1, 1); kid.expr = faces[i];
    });
  };
  SHOTS.push({ t0: 220, t1: 221, set: 'class', vignette: 0.3, sat: 1.2, cam: thumbCam, setup: thumb(true) });
  SHOTS.push({ t0: 221, t1: 222, set: 'class', vignette: 0.3, sat: 1.2, cam: thumbCam, setup: thumb(false) });
}
