// School, office and home props. Every prop is a THREE.Group built from simple
// low-poly pieces with painted canvas textures. Props that hands interact with
// carry `userData.hold` = the object's pose in the wrist frame of a holding hand
// (wrist local: -Y along the fingers, +Z out of the palm, thumb towards +X on the
// left hand / -X on the right hand).
import * as THREE from 'three';
import { canvas, toTex, noiseFill, woodTexture } from './tex.js';
import { mat, box, cyl } from './chars.js';
import * as SX from './stex.js';
import { rng, clamp } from './util.js';

const M = (color, rough = 0.7, metal = 0, extra = {}) => new THREE.MeshStandardMaterial({ color, roughness: rough, metalness: metal, ...extra });
function mesh(geo, material, x = 0, y = 0, z = 0, parent = null) {
  const m = new THREE.Mesh(geo, material);
  m.position.set(x, y, z);
  m.castShadow = true; m.receiveShadow = true;
  if (parent) parent.add(m);
  return m;
}
export function holdMatrix(pos, euler) {
  return new THREE.Matrix4().compose(new THREE.Vector3(...pos), new THREE.Quaternion().setFromEuler(new THREE.Euler(...euler)), new THREE.Vector3(1, 1, 1));
}

let _wl = null, _wd = null, _wm = null;
const WOOD_LIGHT = () => (_wl ||= M('#ffffff', 0.55, 0, { map: woodTexture('#c49460', 12, 0.45) }));
const WOOD_DARK = () => (_wd ||= M('#ffffff', 0.5, 0, { map: woodTexture('#6a3a1c', 14, 0.5) }));
const WOOD_MID = () => (_wm ||= M('#ffffff', 0.55, 0, { map: woodTexture('#9a6232', 15, 0.45) }));
const METAL = M('#3a3e44', 0.35, 0.7);
const CHROME = M('#c8ccd0', 0.18, 0.95);
const BLACK = M('#121212', 0.5);

// ------------------------------------------------------------ furniture ---
// student desk: user sits at -z facing +z; top centre at (0, topY, 0)
export function studentDesk() {
  const g = new THREE.Group();
  const topY = 0.66;
  mesh(box(0.64, 0.028, 0.46), WOOD_LIGHT(), 0, topY - 0.014, 0, g);
  const edge = mesh(box(0.646, 0.012, 0.466), M('#5a4a3a', 0.6), 0, topY - 0.031, 0, g);
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) mesh(box(0.028, topY - 0.04, 0.028), METAL, sx * 0.29, (topY - 0.04) / 2, sz * 0.2, g);
  for (const sx of [-1, 1]) mesh(box(0.024, 0.024, 0.4), METAL, sx * 0.29, 0.12, 0, g);
  mesh(box(0.56, 0.012, 0.15), METAL, 0, 0.555, 0.15, g); // book rack (far side only, clear of the knees)
  mesh(box(0.56, 0.08, 0.012), METAL, 0, 0.595, 0.225, g);
  g.userData.topY = topY;
  g.userData.size = [0.64, 0.46];
  return g;
}

// moulded plastic school chair, seat front towards +z
export function studentChair(seatH = 0.41, color = '#2a5a8a') {
  const g = new THREE.Group();
  const shell = M(color, 0.45);
  mesh(box(0.42, 0.025, 0.4), shell, 0, seatH - 0.012, 0.0, g);
  const back = mesh(box(0.42, 0.26, 0.022), shell, 0, seatH + 0.25, -0.215, g);
  back.rotation.x = -0.1;
  for (const sx of [-1, 1]) {
    for (const sz of [-1, 1]) mesh(cyl(0.011, 0.011, seatH - 0.02, 6), METAL, sx * 0.18, (seatH - 0.02) / 2, sz * 0.17, g);
    const up = mesh(cyl(0.011, 0.011, 0.36, 6), METAL, sx * 0.18, seatH + 0.16, -0.19, g);
    up.rotation.x = -0.1;
  }
  g.userData.seatH = seatH;
  return g;
}

// teacher's desk, user side at -z; top centre at (0, 0.76, 0)
export function teacherDesk() {
  const g = new THREE.Group();
  const W = 1.4, D = 0.72, Y = 0.76;
  mesh(box(W, 0.04, D), WOOD_MID(), 0, Y - 0.02, 0, g);
  mesh(box(W - 0.04, Y - 0.04, 0.03), WOOD_DARK(), 0, (Y - 0.04) / 2, D / 2 - 0.03, g); // modesty panel facing the class
  for (const sx of [-1, 1]) mesh(box(0.04, Y - 0.04, D - 0.04), WOOD_DARK(), sx * (W / 2 - 0.03), (Y - 0.04) / 2, 0, g);
  const ped = mesh(box(0.42, Y - 0.06, D - 0.08), WOOD_DARK(), W / 2 - 0.26, (Y - 0.06) / 2, 0, g);
  for (let i = 0; i < 3; i++) {
    mesh(box(0.38, 0.19, 0.01), WOOD_MID(), W / 2 - 0.26, 0.6 - i * 0.22, -D / 2 + 0.035, g);
    mesh(box(0.1, 0.014, 0.02), CHROME, W / 2 - 0.26, 0.62 - i * 0.22, -D / 2 + 0.025, g);
  }
  g.userData.topY = Y;
  return g;
}

export function officeChair(seatH = 0.48, color = '#1a1a1c') {
  const g = new THREE.Group();
  const leather = M(color, 0.45);
  mesh(box(0.5, 0.09, 0.48), leather, 0, seatH - 0.045, 0, g);
  const back = mesh(box(0.48, 0.62, 0.08), leather, 0, seatH + 0.36, -0.25, g);
  back.rotation.x = -0.12;
  mesh(cyl(0.03, 0.03, seatH - 0.14, 8), CHROME, 0, (seatH - 0.14) / 2 + 0.08, 0, g);
  for (let i = 0; i < 5; i++) {
    const a = (i / 5) * Math.PI * 2;
    const leg = mesh(box(0.04, 0.03, 0.3), METAL, Math.sin(a) * 0.14, 0.07, Math.cos(a) * 0.14, g);
    leg.rotation.y = a;
    mesh(new THREE.SphereGeometry(0.025, 6, 4), BLACK, Math.sin(a) * 0.28, 0.025, Math.cos(a) * 0.28, g);
  }
  for (const sx of [-1, 1]) {
    mesh(box(0.05, 0.03, 0.3), leather, sx * 0.27, seatH + 0.2, -0.02, g);
    mesh(box(0.03, 0.2, 0.03), METAL, sx * 0.27, seatH + 0.09, -0.08, g);
  }
  g.userData.seatH = seatH;
  return g;
}

// executive desk for the principal
export function bigDesk() {
  const g = new THREE.Group();
  const W = 1.9, D = 0.9, Y = 0.77;
  mesh(box(W, 0.05, D), WOOD_DARK(), 0, Y - 0.025, 0, g);
  mesh(box(W - 0.08, 0.004, D - 0.08), M('#2a3a2a', 0.8), 0, Y + 0.002, 0, g); // leather inlay (top at Y + 0.004)
  for (const sx of [-1, 1]) {
    mesh(box(0.55, Y - 0.05, D - 0.06), WOOD_DARK(), sx * (W / 2 - 0.3), (Y - 0.05) / 2, 0, g);
    for (let i = 0; i < 3; i++) {
      mesh(box(0.48, 0.18, 0.01), WOOD_MID(), sx * (W / 2 - 0.3), 0.6 - i * 0.22, D / 2 - 0.025, g);
      mesh(box(0.12, 0.016, 0.02), M('#c8a04a', 0.3, 0.8), sx * (W / 2 - 0.3), 0.62 - i * 0.22, D / 2 - 0.015, g);
    }
  }
  mesh(box(W - 1.2, 0.5, 0.03), WOOD_DARK(), 0, 0.45, D / 2 - 0.03, g);
  g.userData.topY = Y;
  return g;
}

export function smallTable(w = 0.8, d = 0.6, h = 0.72) {
  const g = new THREE.Group();
  mesh(box(w, 0.035, d), WOOD_MID(), 0, h - 0.018, 0, g);
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) mesh(box(0.045, h - 0.035, 0.045), WOOD_DARK(), sx * (w / 2 - 0.05), (h - 0.035) / 2, sz * (d / 2 - 0.05), g);
  g.userData.topY = h;
  return g;
}

export function woodChair(seatH = 0.46) {
  const g = new THREE.Group();
  mesh(box(0.44, 0.04, 0.42), WOOD_MID(), 0, seatH - 0.02, 0, g);
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) mesh(box(0.035, seatH - 0.04, 0.035), WOOD_DARK(), sx * 0.19, (seatH - 0.04) / 2, sz * 0.18, g);
  for (const sx of [-1, 1]) mesh(box(0.035, 0.46, 0.035), WOOD_DARK(), sx * 0.19, seatH + 0.23, -0.19, g);
  mesh(box(0.42, 0.12, 0.025), WOOD_MID(), 0, seatH + 0.38, -0.19, g);
  mesh(box(0.42, 0.05, 0.025), WOOD_MID(), 0, seatH + 0.18, -0.19, g);
  g.userData.seatH = seatH;
  return g;
}

export function bookshelf(w = 1.2, h = 1.9, d = 0.34, seed = 1) {
  const g = new THREE.Group();
  const wd = WOOD_DARK();
  mesh(box(w, h, 0.02), wd, 0, h / 2, -d / 2 + 0.01, g);
  for (const sx of [-1, 1]) mesh(box(0.03, h, d), wd, sx * (w / 2 - 0.015), h / 2, 0, g);
  const n = Math.round(h / 0.38);
  for (let i = 0; i <= n; i++) mesh(box(w, 0.025, d), wd, 0, 0.05 + i * (h - 0.08) / n, 0, g);
  for (let i = 0; i < n; i++) {
    const t = SX.bookSpines(seed + i).clone();
    t.needsUpdate = true;
    t.repeat.set(w / 2.2, 1); t.wrapS = THREE.RepeatWrapping; t.offset.x = (seed * 0.37 + i * 0.29) % 1;
    const bk = mesh(box(w - 0.07, (h - 0.08) / n - 0.05, d - 0.06), [M('#3a2a20'), M('#3a2a20'), M('#3a2a20'), M('#3a2a20'), M('#ffffff', 0.7, 0, { map: t }), M('#3a2a20')], 0, 0.05 + i * (h - 0.08) / n + ((h - 0.08) / n - 0.05) / 2 + 0.012, 0.0, g);
  }
  return g;
}

export function plant(h = 1.1) {
  const g = new THREE.Group();
  mesh(cyl(0.16, 0.12, 0.3, 10), M('#b0562a', 0.8), 0, 0.15, 0, g);
  mesh(cyl(0.15, 0.15, 0.02, 10), M('#3a2a1a', 1), 0, 0.29, 0, g);
  const leaf = M('#3a7a2e', 0.6, 0, { side: THREE.DoubleSide });
  const leaf2 = M('#2e6a26', 0.6, 0, { side: THREE.DoubleSide });
  const r = rng(Math.round(h * 100));
  for (let i = 0; i < 16; i++) {
    const a = r() * Math.PI * 2, tilt = 0.35 + r() * 0.7, len = 0.35 + r() * (h - 0.45);
    const lg = new THREE.PlaneGeometry(0.09, len);
    lg.translate(0, len / 2, 0);
    const l = mesh(lg, i % 2 ? leaf : leaf2, 0, 0.3, 0, g);
    l.rotation.set(0, a, 0);
    l.rotateX(tilt);
  }
  return g;
}

export function trashBin() {
  const g = new THREE.Group();
  mesh(cyl(0.15, 0.12, 0.36, 10, 1, true), M('#4a5a6a', 0.5, 0.3, { side: THREE.DoubleSide }), 0, 0.18, 0, g);
  mesh(cyl(0.12, 0.12, 0.01, 10), M('#3a4a5a'), 0, 0.005, 0, g);
  return g;
}

// ------------------------------------------------------------ wall items ---
export function wallClock() {
  const g = new THREE.Group();
  const [c, gg] = canvas(512, 512);
  gg.fillStyle = '#f6f4ee'; gg.beginPath(); gg.arc(256, 256, 256, 0, Math.PI * 2); gg.fill();
  gg.fillStyle = '#111'; gg.textAlign = 'center'; gg.textBaseline = 'middle'; gg.font = 'bold 54px "Liberation Sans"';
  for (let i = 1; i <= 12; i++) { const a = i / 12 * Math.PI * 2; gg.fillText(String(i), 256 + Math.sin(a) * 190, 256 - Math.cos(a) * 190); }
  for (let i = 0; i < 60; i++) { const a = i / 60 * Math.PI * 2; gg.fillRect(256 + Math.sin(a) * 236 - 2, 256 - Math.cos(a) * 236 - (i % 5 ? 6 : 12), 4, i % 5 ? 12 : 24); }
  noiseFill(gg, 512, 512, 0, 6, 3, 1);
  const face = mesh(new THREE.CircleGeometry(0.17, 32), M('#ffffff', 0.4, 0, { map: toTex(c) }), 0, 0, 0.022, g);
  const rim = mesh(new THREE.TorusGeometry(0.175, 0.016, 6, 32), M('#1a1a1a', 0.3, 0.4), 0, 0, 0.02, g);
  mesh(cyl(0.175, 0.175, 0.04, 32), M('#2a2a2a', 0.5), 0, 0, 0, g).rotation.x = Math.PI / 2;
  const glass = new THREE.Mesh(new THREE.CircleGeometry(0.17, 32), new THREE.MeshPhysicalMaterial({ color: '#ffffff', roughness: 0.05, transparent: true, opacity: 0.12 }));
  glass.position.z = 0.034; g.add(glass);
  const hand = (len, w, col, z) => {
    const p = new THREE.Group(); p.position.z = z; g.add(p);
    const hg = new THREE.BoxGeometry(w, len, 0.004); hg.translate(0, len / 2 - 0.02, 0);
    mesh(hg, M(col, 0.4), 0, 0, 0, p);
    return p;
  };
  const hh = hand(0.09, 0.014, '#111', 0.025), mm = hand(0.135, 0.01, '#111', 0.028), ss = hand(0.145, 0.004, '#c0201a', 0.031);
  mesh(cyl(0.01, 0.01, 0.01, 8), M('#c0201a'), 0, 0, 0.032, g).rotation.x = Math.PI / 2;
  g.userData.set = (h, m, s) => {
    hh.rotation.z = -((h % 12) + m / 60) / 12 * Math.PI * 2;
    mm.rotation.z = -(m + s / 60) / 60 * Math.PI * 2;
    ss.rotation.z = -Math.floor(s) / 60 * Math.PI * 2;
  };
  g.userData.set(10, 10, 0);
  return g;
}

export function framedPicture(tex, w = 0.6, h = 0.45, frameCol = '#2a1a10', depth = 0.03) {
  const g = new THREE.Group();
  const f = M(frameCol, 0.45);
  const b = 0.035;
  mesh(box(w + b * 2, b, depth), f, 0, h / 2 + b / 2, 0, g);
  mesh(box(w + b * 2, b, depth), f, 0, -h / 2 - b / 2, 0, g);
  mesh(box(b, h, depth), f, -w / 2 - b / 2, 0, 0, g);
  mesh(box(b, h, depth), f, w / 2 + b / 2, 0, 0, g);
  const pic = mesh(new THREE.PlaneGeometry(w, h), M('#ffffff', 0.6, 0, { map: tex }), 0, 0, -0.002, g);
  g.userData.pic = pic;
  return g;
}

export function posterBoard(kind, w = 0.5, h = 0.68) {
  const g = new THREE.Group();
  mesh(new THREE.PlaneGeometry(w, h), M('#ffffff', 0.8, 0, { map: SX.posterTexture(kind) }), 0, 0, 0.002, g);
  for (const sx of [-1, 1]) for (const sy of [-1, 1]) mesh(new THREE.SphereGeometry(0.008, 6, 4), M('#c02020', 0.4), sx * (w / 2 - 0.02), sy * (h / 2 - 0.02), 0.006, g);
  return g;
}

export function whiteboard(w = 2.8, h = 1.15) {
  const g = new THREE.Group();
  const wb = SX.whiteboardCanvas(1400, Math.round(1400 * h / w));
  SX.clearBoard(wb.g, wb.W, wb.H);
  const surf = mesh(new THREE.PlaneGeometry(w, h), M('#ffffff', 0.18, 0.05, { map: wb.tex }), 0, 0, 0.012, g);
  const fr = M('#b8bcc0', 0.3, 0.8);
  mesh(box(w + 0.06, 0.03, 0.03), fr, 0, h / 2 + 0.015, 0.012, g);
  mesh(box(w + 0.06, 0.03, 0.03), fr, 0, -h / 2 - 0.015, 0.012, g);
  mesh(box(0.03, h, 0.03), fr, -w / 2 - 0.015, 0, 0.012, g);
  mesh(box(0.03, h, 0.03), fr, w / 2 + 0.015, 0, 0.012, g);
  mesh(box(w * 0.8, 0.02, 0.08), fr, 0, -h / 2 - 0.04, 0.05, g); // marker tray
  const mk = (x, col) => { const m = mesh(cyl(0.009, 0.009, 0.13, 8), M(col, 0.4), x, -h / 2 - 0.02, 0.06, g); m.rotation.z = Math.PI / 2; };
  mk(-0.6, '#c02020'); mk(-0.4, '#1c3a8a'); mk(-0.25, '#111');
  const eraser = mesh(box(0.14, 0.04, 0.05), M('#2a2a2a'), 0.5, -h / 2 - 0.01, 0.06, g);
  g.userData.board = wb;
  g.userData.write = (fn) => { SX.clearBoard(wb.g, wb.W, wb.H); fn(wb.g, wb.W, wb.H); wb.tex.needsUpdate = true; };
  return g;
}

export function ceilingLight(w = 1.2, d = 0.3) {
  const g = new THREE.Group();
  mesh(box(w, 0.06, d), M('#dcdcd8', 0.5), 0, 0, 0, g);
  const p = new THREE.Mesh(new THREE.PlaneGeometry(w - 0.06, d - 0.06), new THREE.MeshBasicMaterial({ color: new THREE.Color(2.2, 2.15, 2.0) }));
  p.rotation.x = Math.PI / 2; p.position.y = -0.031; g.add(p);
  g.userData.panel = p;
  return g;
}

// ceiling-corner security camera (looking along +z, tilted down)
export function cctvCam() {
  const g = new THREE.Group();
  mesh(box(0.06, 0.12, 0.06), M('#e8e8e4', 0.4), 0, 0.06, -0.03, g);
  const head = new THREE.Group(); head.position.set(0, -0.0, 0.02); g.add(head);
  mesh(box(0.1, 0.09, 0.22), M('#f0f0ec', 0.35), 0, 0, 0.08, head);
  mesh(box(0.12, 0.012, 0.25), M('#d8d8d4', 0.4), 0, 0.05, 0.09, head);
  mesh(cyl(0.03, 0.03, 0.02, 12), M('#080808', 0.1, 0.5), 0, 0, 0.2, head).rotation.x = Math.PI / 2;
  const led = new THREE.Mesh(new THREE.SphereGeometry(0.008, 6, 4), new THREE.MeshBasicMaterial({ color: new THREE.Color(4, 0.2, 0.2) }));
  led.position.set(0.035, 0.03, 0.19); head.add(led);
  head.rotation.x = 0.45;
  g.userData.led = led;
  return g;
}

// door in a wall (front at +z): frame, slab with small window, handle, optional sign
export function door(signText = null, col = '#7a4a2a') {
  const g = new THREE.Group();
  const W = 0.95, H = 2.1;
  const fr = M('#e8e4dc', 0.5);
  mesh(box(0.08, H + 0.08, 0.14), fr, -W / 2 - 0.04, (H + 0.08) / 2, 0, g);
  mesh(box(0.08, H + 0.08, 0.14), fr, W / 2 + 0.04, (H + 0.08) / 2, 0, g);
  mesh(box(W + 0.16, 0.08, 0.14), fr, 0, H + 0.04, 0, g);
  const pivot = new THREE.Group(); pivot.position.set(-W / 2, 0, 0.0); g.add(pivot);
  const slab = new THREE.Group(); slab.position.set(W / 2, 0, 0); pivot.add(slab);
  const wood = M('#ffffff', 0.55, 0, { map: woodTexture(col, 31, 0.4) });
  mesh(box(W, H, 0.045), wood, 0, H / 2, 0, slab);
  const gl = new THREE.Mesh(new THREE.PlaneGeometry(0.22, 0.5), new THREE.MeshStandardMaterial({ color: '#a8c0d0', roughness: 0.1, metalness: 0.3, transparent: true, opacity: 0.55 }));
  gl.position.set(0.2, 1.5, 0.024); slab.add(gl);
  const gl2 = gl.clone(); gl2.position.z = -0.024; gl2.rotation.y = Math.PI; slab.add(gl2);
  for (const sz of [-1, 1]) {
    mesh(box(0.13, 0.02, 0.02), CHROME, W / 2 - 0.12, 1.02, sz * 0.05, slab);
    mesh(cyl(0.025, 0.025, 0.03, 10), CHROME, W / 2 - 0.08, 1.02, sz * 0.03, slab).rotation.x = Math.PI / 2;
  }
  if (signText) {
    const [c, gg] = canvas(512, 140);
    gg.fillStyle = '#1c2a4a'; gg.fillRect(0, 0, 512, 140);
    gg.strokeStyle = '#d8b24a'; gg.lineWidth = 8; gg.strokeRect(10, 10, 492, 120);
    gg.fillStyle = '#f0e8d0'; gg.font = 'bold 64px "Liberation Sans"'; gg.textAlign = 'center'; gg.textBaseline = 'middle';
    gg.fillText(signText, 256, 74);
    const sign = mesh(new THREE.PlaneGeometry(0.5, 0.137), M('#ffffff', 0.4, 0.1, { map: toTex(c) }), 0, 1.65, 0.026, slab);
  }
  g.userData.pivot = pivot;
  g.userData.open = (a) => { pivot.rotation.y = -a; };
  return g;
}

// rectangular window set into a wall (opening w x h); frame + mullions + glowing view
export function windowUnit(w, h, view = 'day', cols = 2, rows = 2, frameCol = '#f2f0ea') {
  const g = new THREE.Group();
  const fr = M(frameCol, 0.45);
  const t = 0.06;
  mesh(box(w, t, 0.16), fr, 0, h / 2 - t / 2, 0, g);
  mesh(box(w, t * 1.6, 0.22), fr, 0, -h / 2 + t * 0.8, 0.03, g); // sill
  mesh(box(t, h, 0.16), fr, -w / 2 + t / 2, 0, 0, g);
  mesh(box(t, h, 0.16), fr, w / 2 - t / 2, 0, 0, g);
  for (let i = 1; i < cols; i++) mesh(box(0.035, h, 0.08), fr, -w / 2 + (w * i) / cols, 0, 0, g);
  for (let i = 1; i < rows; i++) mesh(box(w, 0.035, 0.08), fr, 0, -h / 2 + (h * i) / rows, 0, g);
  const glow = view === 'night' ? new THREE.Color(0.55, 0.6, 0.9) : new THREE.Color(2.6, 2.6, 2.5);
  const out = new THREE.Mesh(new THREE.PlaneGeometry(w - 0.02, h - 0.02), new THREE.MeshBasicMaterial({ map: SX.outsideView(view), color: glow }));
  out.position.z = -0.06;
  g.add(out);
  g.userData.view = out;
  return g;
}

// ------------------------------------------------------------ hand props ---
// pencil along local Y: tip at -Y, eraser at +Y; length 0.175
export function pencil() {
  const g = new THREE.Group();
  const L = 0.15;
  const body = mesh(cyl(0.0036, 0.0036, L, 6), M('#f2c21a', 0.45), 0, 0.0125, 0, g);
  mesh(cyl(0.0037, 0.0037, 0.012, 6), M('#c8c8c0', 0.3, 0.8), 0, 0.0125 + L / 2 + 0.006, 0, g);
  mesh(cyl(0.0035, 0.0035, 0.012, 6), M('#e88a9a', 0.7), 0, 0.0125 + L / 2 + 0.018, 0, g);
  mesh(new THREE.ConeGeometry(0.0036, 0.022, 6), M('#e8c8a0', 0.8), 0, 0.0125 - L / 2 - 0.011, 0, g).rotation.x = Math.PI;
  mesh(new THREE.ConeGeometry(0.0012, 0.007, 6), M('#2a2a2a', 0.5), 0, 0.0125 - L / 2 - 0.0185, 0, g).rotation.x = Math.PI;
  g.userData.tip = new THREE.Vector3(0, 0.0125 - L / 2 - 0.022, 0);
  // writing grip in the right hand: pencil between thumb and fingertips, tip out past the fingers
  g.userData.hold = holdMatrix([-0.018, -0.118, 0.03], [-0.62, 0, 0.25]);
  g.userData.holdL = holdMatrix([0.018, -0.118, 0.03], [-0.62, 0, -0.25]);
  return g;
}

// red marker pen with cap posted on the back
export function redPen() {
  const g = new THREE.Group();
  mesh(cyl(0.0058, 0.0058, 0.125, 8), M('#d8d8d4', 0.35), 0, 0, 0, g);
  mesh(cyl(0.0065, 0.0065, 0.05, 8), M('#c81a1a', 0.35), 0, 0.055, 0, g);
  mesh(box(0.002, 0.04, 0.008), M('#c81a1a', 0.35), 0.0068, 0.05, 0, g);
  mesh(new THREE.ConeGeometry(0.0058, 0.016, 8), M('#d8d8d4', 0.35), 0, -0.07, 0, g).rotation.x = Math.PI;
  mesh(new THREE.ConeGeometry(0.0022, 0.008, 6), M('#e01818', 0.5), 0, -0.081, 0, g).rotation.x = Math.PI;
  g.userData.tip = new THREE.Vector3(0, -0.085, 0);
  g.userData.hold = holdMatrix([-0.018, -0.105, 0.03], [-0.62, 0, 0.25]);
  return g;
}

// school backpack (front at +z); userData.flap opens the top
export function backpack(col = '#b82020') {
  const g = new THREE.Group();
  const m = M(col, 0.75), dk = M(new THREE.Color(col).multiplyScalar(0.6).getStyle(), 0.8);
  mesh(box(0.32, 0.4, 0.17), m, 0, 0.2, 0, g);
  mesh(box(0.26, 0.18, 0.06), m, 0, 0.13, 0.11, g);
  mesh(box(0.26, 0.012, 0.012), M('#202020', 0.3, 0.6), 0, 0.22, 0.142, g); // pocket zip
  for (const sx of [-1, 1]) mesh(box(0.05, 0.36, 0.02), dk, sx * 0.09, 0.22, -0.095, g);
  mesh(box(0.08, 0.025, 0.06), dk, 0, 0.42, -0.03, g); // grab handle
  const flapPivot = new THREE.Group(); flapPivot.position.set(0, 0.4, -0.085); g.add(flapPivot);
  const flap = mesh(box(0.32, 0.02, 0.17), m, 0, 0.0, 0.085, flapPivot);
  const inside = mesh(box(0.29, 0.005, 0.14), M('#1a1a1a', 1), 0, 0.395, 0, g);
  g.userData.open = (a) => { flapPivot.rotation.x = -a; };
  g.userData.hold = holdMatrix([0, -0.11, 0.03], [Math.PI / 2, 0, 0]); // by the grab handle
  return g;
}

export function pencilCase(col = '#1c3a6a') {
  const g = new THREE.Group();
  const m = M(col, 0.7);
  mesh(box(0.2, 0.05, 0.07), m, 0, 0.025, 0, g);
  const lidPivot = new THREE.Group(); lidPivot.position.set(0, 0.05, -0.035); g.add(lidPivot);
  const lid = mesh(box(0.2, 0.015, 0.07), m, 0, 0.0, 0.035, lidPivot);
  mesh(box(0.19, 0.006, 0.006), M('#c8c8c8', 0.3, 0.8), 0, 0.006, 0.07, lidPivot);
  const inner = new THREE.Group(); g.add(inner);
  const cols = ['#f2c21a', '#2a6ac8', '#e84a3a', '#2a9a4a'];
  for (let i = 0; i < 4; i++) { const p = mesh(cyl(0.0035, 0.0035, 0.17, 6), M(cols[i], 0.5), -0.0 + 0, 0.04, -0.022 + i * 0.012, inner); p.rotation.z = Math.PI / 2; }
  mesh(box(0.04, 0.012, 0.02), M('#f0f0f0', 0.8), 0.06, 0.046, 0.02, inner);
  g.userData.open = (a) => { lidPivot.rotation.x = -a; };
  g.userData.hold = holdMatrix([0, -0.1, 0.035], [Math.PI / 2, 0, 0]);
  return g;
}

// water bottle with a wrap-around label that can peel off (userData.peel 0..1)
export function waterBottle() {
  const g = new THREE.Group();
  const plastic = new THREE.MeshPhysicalMaterial({ color: '#cfe8f4', roughness: 0.08, transparent: true, opacity: 0.55, metalness: 0.0 });
  mesh(cyl(0.034, 0.034, 0.19, 14), plastic, 0, 0.095, 0, g);
  mesh(cyl(0.022, 0.034, 0.04, 14), plastic, 0, 0.21, 0, g);
  mesh(cyl(0.017, 0.017, 0.025, 12), M('#1c5ab8', 0.4), 0, 0.243, 0, g);
  const water = mesh(cyl(0.031, 0.031, 0.15, 14), new THREE.MeshPhysicalMaterial({ color: '#9ad0f0', roughness: 0.05, transparent: true, opacity: 0.35 }), 0, 0.078, 0, g);
  const [c, gg] = canvas(512, 128);
  gg.fillStyle = '#1c5ab8'; gg.fillRect(0, 0, 512, 128);
  gg.fillStyle = '#ffffff'; gg.font = 'bold 54px "Liberation Sans"'; gg.textAlign = 'center'; gg.fillText('AQUA', 128, 82); gg.fillText('AQUA', 384, 82);
  gg.fillStyle = 'rgba(255,255,255,0.35)'; for (let i = 0; i < 8; i++) gg.fillRect(0, 10 + i * 2, 512, 1);
  const labTex = toTex(c);
  const labMat = new THREE.MeshStandardMaterial({ map: labTex, roughness: 0.5, side: THREE.DoubleSide });
  // label = static part + a peeling flap hinged at its edge
  const lab = new THREE.Mesh(new THREE.CylinderGeometry(0.0352, 0.0352, 0.07, 20, 1, true, 0, Math.PI * 2), labMat);
  lab.position.y = 0.1; g.add(lab);
  const flapPivot = new THREE.Group(); flapPivot.position.set(0, 0.1, 0); g.add(flapPivot);
  const flapGeo = new THREE.PlaneGeometry(0.09, 0.07, 6, 1);
  const flap = new THREE.Mesh(flapGeo, labMat); flapPivot.add(flap);
  flap.visible = false;
  g.userData.peel = (k) => {
    k = clamp(k);
    const peeled = k * Math.PI * 1.1;
    lab.geometry.dispose();
    lab.geometry = new THREE.CylinderGeometry(0.0352, 0.0352, 0.07, 20, 1, true, peeled, Math.PI * 2 - peeled);
    flap.visible = k > 0.001;
    // the flap: a strip of length = peeled arc, curling away from the bottle at the edge theta=peeled
    const len = 0.0352 * peeled;
    const p = flapGeo.attributes.position;
    for (let i = 0; i < p.count; i++) {
      const u = (Math.round((p.getX(i) / 0.09 + 0.5) * 6)) / 6; // 0..1 along the strip
      const s = u * len;
      const curl = 0.6 + k * 1.2; // the free end lifts off
      const ang = peeled - s / 0.0352 * 0.25;
      const rr = 0.0352 + s * Math.sin(curl * u) * 0.9;
      p.setX(i, Math.sin(ang) * rr);
      p.setZ(i, Math.cos(ang) * rr);
    }
    p.needsUpdate = true;
    flapGeo.computeVertexNormals();
  };
  g.userData.hold = holdMatrix([0.0, -0.085, 0.045], [Math.PI / 2, 0, 0]);
  return g;
}

export function notebook(col = '#2a5a9a', thick = 0.012) {
  const g = new THREE.Group();
  mesh(box(0.17, thick, 0.24), M(col, 0.6), 0, thick / 2, 0, g);
  mesh(box(0.165, thick * 0.7, 0.235), M('#f4f2ea', 0.9), 0.003, thick / 2, 0, g);
  mesh(box(0.01, thick * 1.05, 0.24), M(new THREE.Color(col).multiplyScalar(0.6).getStyle(), 0.6), -0.083, thick / 2, 0, g);
  g.userData.hold = holdMatrix([0.0, -0.09, 0.02], [Math.PI / 2, 0, 0]);
  return g;
}

export function envelope(text = 'FINAL EXAM') {
  const g = new THREE.Group();
  const [c, gg] = canvas(512, 362);
  gg.fillStyle = '#c8a46a'; gg.fillRect(0, 0, 512, 362);
  noiseFill(gg, 512, 362, 0, 14, 7, 1);
  gg.fillStyle = '#3a2410'; gg.font = 'bold 44px "Liberation Sans"'; gg.textAlign = 'center'; gg.fillText(text, 256, 150);
  gg.font = '28px "Liberation Sans"'; gg.fillText('SEALED — DO NOT OPEN', 256, 200);
  gg.strokeStyle = '#c81a1a'; gg.lineWidth = 6; gg.strokeRect(116, 230, 280, 70);
  gg.fillStyle = '#c81a1a'; gg.font = 'bold 36px "Liberation Sans"'; gg.fillText('CONFIDENTIAL', 256, 278);
  const top = M('#ffffff', 0.85, 0, { map: toTex(c) });
  mesh(box(0.25, 0.012, 0.35), [M('#c8a46a', 0.85), M('#c8a46a', 0.85), top, M('#b89458', 0.9), M('#c8a46a', 0.85), M('#c8a46a', 0.85)], 0, 0.006, 0, g).rotation.y = Math.PI / 2;
  return g;
}

export function rubberStamp() {
  const g = new THREE.Group();
  mesh(box(0.08, 0.012, 0.045), M('#7a1a1a', 0.6), 0, 0.006, 0, g);
  mesh(box(0.075, 0.02, 0.04), M('#5a3a1c', 0.5), 0, 0.022, 0, g);
  mesh(cyl(0.008, 0.01, 0.05, 8), M('#5a3a1c', 0.5), 0, 0.055, 0, g);
  mesh(new THREE.SphereGeometry(0.02, 10, 8), M('#2a1a10', 0.4), 0, 0.09, 0, g);
  g.userData.hold = holdMatrix([0, -0.07, 0.035], [-Math.PI / 2, 0, 0]);
  return g;
}

export function smartphone(screenFn = null) {
  const g = new THREE.Group();
  mesh(box(0.075, 0.009, 0.155), M('#1a1a1c', 0.25, 0.5), 0, 0.0045, 0, g);
  const [c, gg] = canvas(300, 620);
  const tex = toTex(c);
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.069, 0.146), new THREE.MeshBasicMaterial({ map: tex, color: new THREE.Color(1.15, 1.15, 1.15) }));
  scr.rotation.x = -Math.PI / 2; scr.position.y = 0.0092; g.add(scr);
  g.userData.screen = { c, g: gg, tex, mesh: scr };
  g.userData.draw = (fn) => { fn(gg, 300, 620); tex.needsUpdate = true; };
  g.userData.hold = holdMatrix([0.0, -0.085, 0.03], [Math.PI / 2, 0, 0]);
  return g;
}

export function deskLamp(on = true) {
  const g = new THREE.Group();
  const m = M('#1c3a2a', 0.35, 0.4);
  mesh(cyl(0.08, 0.09, 0.02, 14), m, 0, 0.01, 0, g);
  const arm = mesh(cyl(0.008, 0.008, 0.36, 6), CHROME, 0, 0.19, 0.02, g); arm.rotation.x = 0.15;
  const arm2 = mesh(cyl(0.008, 0.008, 0.25, 6), CHROME, 0, 0.4, 0.12, g); arm2.rotation.x = 1.0;
  const shade = mesh(new THREE.ConeGeometry(0.08, 0.12, 14, 1, true), new THREE.MeshStandardMaterial({ color: '#1c3a2a', roughness: 0.35, metalness: 0.4, side: THREE.DoubleSide }), 0, 0.43, 0.24, g);
  shade.rotation.x = -0.5;
  const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.03, 10, 8), new THREE.MeshBasicMaterial({ color: new THREE.Color(4, 3.4, 2.4) }));
  bulb.position.set(0, 0.39, 0.26); g.add(bulb);
  g.userData.bulb = bulb;
  g.userData.lightPos = new THREE.Vector3(0, 0.36, 0.27);
  return g;
}

export function mug(col = '#f2f2ee', text = 'BEST TEACHER') {
  const g = new THREE.Group();
  const [c, gg] = canvas(256, 96);
  gg.fillStyle = col; gg.fillRect(0, 0, 256, 96);
  gg.fillStyle = '#c81a1a'; gg.font = 'bold 20px "Liberation Sans"'; gg.textAlign = 'center'; gg.fillText(text, 64, 56);
  mesh(cyl(0.04, 0.036, 0.1, 14), M('#ffffff', 0.3, 0, { map: toTex(c) }), 0, 0.05, 0, g);
  mesh(cyl(0.035, 0.035, 0.002, 14), M('#3a1a08', 0.2), 0, 0.09, 0, g);
  const h = mesh(new THREE.TorusGeometry(0.026, 0.007, 6, 12, Math.PI), M(col, 0.3), -0.04, 0.05, 0, g);
  h.rotation.z = Math.PI / 2;
  return g;
}

export function stackOfPapers(n = 12, seed = 1) {
  const g = new THREE.Group();
  const r = rng(seed);
  for (let i = 0; i < n; i++) {
    const p = mesh(box(0.21, 0.0016, 0.297), M(i % 4 ? '#f4f2ec' : '#ecead8', 0.9), (r() - 0.5) * 0.008, 0.0008 + i * 0.0016, (r() - 0.5) * 0.008, g);
    p.rotation.y = (r() - 0.5) * 0.04;
  }
  return g;
}

// home furniture -----------------------------------------------------------
export function sofa(col = '#6a4a32') {
  const g = new THREE.Group();
  const m = M(col, 0.55);
  mesh(box(2.0, 0.42, 0.9), m, 0, 0.21, 0, g);
  mesh(box(2.0, 0.55, 0.22), m, 0, 0.62, -0.34, g);
  for (const sx of [-1, 1]) mesh(box(0.22, 0.3, 0.9), m, sx * 0.9, 0.57, 0, g);
  for (let i = 0; i < 3; i++) {
    const cu = mesh(box(0.52, 0.12, 0.62), M(col, 0.6), -0.53 + i * 0.53, 0.47, 0.06, g);
    const bc = mesh(box(0.52, 0.4, 0.12), M(col, 0.6), -0.53 + i * 0.53, 0.72, -0.2, g);
    bc.rotation.x = -0.12;
  }
  g.userData.seatH = 0.53;
  return g;
}
export function sideTable() {
  const g = new THREE.Group();
  mesh(cyl(0.28, 0.28, 0.035, 16), WOOD_MID(), 0, 0.6, 0, g);
  mesh(cyl(0.035, 0.05, 0.58, 8), WOOD_DARK(), 0, 0.3, 0, g);
  mesh(cyl(0.2, 0.22, 0.03, 12), WOOD_DARK(), 0, 0.015, 0, g);
  g.userData.topY = 0.618;
  return g;
}
export function floorLamp() {
  const g = new THREE.Group();
  mesh(cyl(0.16, 0.18, 0.03, 14), M('#2a2a2a', 0.4, 0.5), 0, 0.015, 0, g);
  mesh(cyl(0.012, 0.012, 1.5, 8), M('#b8a070', 0.3, 0.8), 0, 0.76, 0, g);
  const sh = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.25, 0.3, 16, 1, true), new THREE.MeshStandardMaterial({ color: '#f0e0c0', roughness: 0.8, side: THREE.DoubleSide, emissive: new THREE.Color('#f0c070'), emissiveIntensity: 0.6 }));
  sh.position.y = 1.55; g.add(sh);
  return g;
}
export function tvCabinet() {
  const g = new THREE.Group();
  mesh(box(1.3, 0.55, 0.45), WOOD_DARK(), 0, 0.3, 0, g);
  for (const sx of [-1, 1]) for (let i = 0; i < 2; i++) {
    mesh(box(0.6, 0.22, 0.01), WOOD_MID(), sx * 0.32, 0.18 + i * 0.25, 0.226, g);
    mesh(box(0.08, 0.02, 0.02), M('#c8a04a', 0.3, 0.8), sx * 0.32, 0.2 + i * 0.25, 0.235, g);
  }
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) mesh(cyl(0.02, 0.015, 0.06, 6), WOOD_DARK(), sx * 0.6, 0.0, sz * 0.18, g);
  g.userData.topY = 0.575;
  return g;
}
export function bed(sheet = '#3a5a8a') {
  const g = new THREE.Group();
  mesh(box(1.0, 0.3, 2.0), WOOD_DARK(), 0, 0.15, 0, g);
  mesh(box(0.96, 0.2, 1.96), M('#f0eee8', 0.9), 0, 0.4, 0, g);
  mesh(box(0.98, 0.08, 1.4), M(sheet, 0.85), 0, 0.53, 0.28, g);
  mesh(box(0.6, 0.12, 0.35), M('#f6f4ee', 0.9), 0, 0.56, -0.75, g);
  mesh(box(1.04, 0.9, 0.06), WOOD_DARK(), 0, 0.45, -1.0, g);
  return g;
}
export function rug(w = 2.6, d = 1.8) {
  const g = new THREE.Group();
  const r = mesh(new THREE.PlaneGeometry(w, d), M('#ffffff', 0.95, 0, { map: SX.rugTexture() }), 0, 0.006, 0, g);
  r.rotation.x = -Math.PI / 2;
  return g;
}

// school corridor items -------------------------------------------------------
export function lockerBank(n = 6, col = '#2e6a8e', start = 101) {
  const g = new THREE.Group();
  const W = 0.38 * n, H = 1.85, D = 0.45;
  const tex = SX.lockerTexture(col, n, start);
  const side = M(SX.shiftHex(col, -20), 0.4, 0.4);
  mesh(box(W, H, D), [side, side, side, side, M('#ffffff', 0.35, 0.4, { map: tex }), side], 0, H / 2 + 0.1, 0, g);
  mesh(box(W, 0.1, D - 0.04), M('#1a1a1a', 0.6), 0, 0.05, -0.02, g);
  return g;
}
export function bench(len = 1.6) {
  const g = new THREE.Group();
  mesh(box(len, 0.05, 0.36), WOOD_MID(), 0, 0.44, 0, g);
  for (const sx of [-1, 1]) mesh(box(0.05, 0.42, 0.3), METAL, sx * (len / 2 - 0.12), 0.21, 0, g);
  g.userData.seatH = 0.465;
  return g;
}
export function noticeBoard(w = 1.4, h = 0.9, seed = 3) {
  const g = new THREE.Group();
  const [c, gg] = canvas(700, 450);
  gg.fillStyle = '#b8864e'; gg.fillRect(0, 0, 700, 450);
  noiseFill(gg, 700, 450, 0, 30, seed, 2);
  const r = rng(seed);
  for (let i = 0; i < 9; i++) {
    const x = 20 + r() * 560, y = 20 + r() * 300, w2 = 90 + r() * 60, h2 = 110 + r() * 50;
    gg.save(); gg.translate(x + w2 / 2, y + h2 / 2); gg.rotate((r() - 0.5) * 0.12);
    gg.fillStyle = ['#f4f2ea', '#f8e888', '#a8d8f0', '#f4c8d8'][i % 4]; gg.fillRect(-w2 / 2, -h2 / 2, w2, h2);
    gg.fillStyle = 'rgba(30,30,40,0.6)'; for (let k = 0; k < 6; k++) gg.fillRect(-w2 / 2 + 10, -h2 / 2 + 18 + k * 14, w2 * (0.5 + r() * 0.4), 4);
    gg.fillStyle = '#c02020'; gg.beginPath(); gg.arc(0, -h2 / 2 + 6, 5, 0, Math.PI * 2); gg.fill();
    gg.restore();
  }
  mesh(box(w, h, 0.02), M('#ffffff', 0.9, 0, { map: toTex(c) }), 0, 0, 0, g);
  mesh(box(w + 0.06, h + 0.06, 0.015), M('#5a3a1c', 0.6), 0, 0, -0.008, g);
  return g;
}

export function computerMonitor(rtTex = null) {
  const g = new THREE.Group();
  mesh(box(0.56, 0.36, 0.035), M('#1a1a1c', 0.4, 0.2), 0, 0.33, 0, g);
  mesh(box(0.06, 0.16, 0.04), M('#1a1a1c', 0.4), 0, 0.1, -0.03, g);
  mesh(box(0.22, 0.015, 0.16), M('#1a1a1c', 0.4), 0, 0.008, -0.02, g);
  const [c, gg] = canvas(1024, 640);
  const tex = toTex(c);
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.52, 0.325), new THREE.MeshBasicMaterial({ map: rtTex || tex, color: new THREE.Color(1.05, 1.05, 1.05) }));
  scr.position.set(0, 0.33, 0.0185); g.add(scr);
  g.userData.screen = { c, g: gg, tex, mesh: scr };
  g.userData.useCanvas = () => { scr.material.map = tex; scr.material.needsUpdate = true; };
  g.userData.useRT = (t) => { scr.material.map = t; scr.material.needsUpdate = true; };
  return g;
}

export function keyboard() {
  const g = new THREE.Group();
  mesh(box(0.42, 0.018, 0.14), M('#1c1c1e', 0.5), 0, 0.009, 0, g);
  mesh(box(0.39, 0.006, 0.11), M('#2e2e32', 0.6), 0, 0.02, 0, g);
  return g;
}

export function trophy() {
  const g = new THREE.Group();
  const gold = M('#e0b040', 0.25, 0.9);
  mesh(box(0.1, 0.05, 0.1), M('#2a1a10', 0.5), 0, 0.025, 0, g);
  mesh(cyl(0.012, 0.02, 0.08, 8), gold, 0, 0.09, 0, g);
  mesh(cyl(0.05, 0.025, 0.08, 12), gold, 0, 0.17, 0, g);
  return g;
}

export function flagStand() { return new THREE.Group(); }
