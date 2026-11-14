// Builds every set and the cast; exposes per-frame state helpers.
import * as THREE from 'three';
import * as TX from './tex.js';
import * as P from './props.js';
import { makeCharacter, POSES, mat, cyl, box } from './chars.js';
import { rng } from './util.js';

export const SURV = new THREE.Vector3(60, 0, 0);    // surveillance room origin
export const OFFICE = new THREE.Vector3(120, 0, 0); // manager office origin
export const BOOTH = new THREE.Vector3(180, 0, 0);  // mugshot photo booth

export const CAST_DEF = {
  player: { outfit: 'player', face: { skin: '#dcae8e', hair: '#3b2a1d', hairStyle: 'short', beard: 'goatee', beardColor: '#3a2416', eye: '#4a3a2a', smile: 0.35, seed: 11, age: 0.35 }, glasses: 'pink' },
  dealer: { outfit: 'dealer', face: { skin: '#e9c3ab', hairStyle: 'bald', eye: '#7090a8', brow: 0.6, seed: 21, age: 0.45, widthK: 0.95 }, headH: 1.12, headW: 0.9, cuffs: true },
  dealer2: { outfit: 'dealer', face: { skin: '#dfae8e', hair: '#18110c', hairStyle: 'short', eye: '#3a2a1a', seed: 22, age: 0.2 }, cuffs: true },
  pit: { outfit: 'pit', face: { skin: '#dfb496', hair: '#16100a', hairStyle: 'slick', eye: '#4a3a2a', seed: 24, smile: 0.2 } },
  guard: { outfit: 'guard', face: { skin: '#80553a', hair: '#0e0a08', hairStyle: 'buzz', eye: '#20140c', lip: '#5a3028', seed: 31 }, glasses: 'sun', build: 1.08 },
  guard2: { outfit: 'guard', face: { skin: '#dcb594', hair: '#141414', hairStyle: 'buzz', eye: '#2a2a2a', seed: 32 }, glasses: 'sun', build: 1.05 },
  guard3: { outfit: 'pit', face: { skin: '#e3bc9c', hair: '#1a1410', hairStyle: 'short', eye: '#3a3a3a', seed: 33 } },
  manager: { outfit: 'manager', face: { skin: '#e8c4a4', hair: '#2a2018', hairStyle: 'buzz', eye: '#2a1c10', seed: 41, age: 0.5, smile: -0.4, browRaise: -0.5 }, glasses: 'reading' },
  operator: { outfit: 'operator', face: { skin: '#d9b39a', hairStyle: 'bald', beard: 'full', beardColor: '#8f877e', eye: '#4a4a4a', seed: 51, age: 0.75 } },
  operator2: { outfit: 'operator', face: { skin: '#e2c2aa', hairStyle: 'bald', eye: '#2a2a2a', seed: 52, age: 0.4 }, glasses: 'sun' },
  topHat: { clothes: { kind: 'jacket', top: '#5a3a22', sleeve: '#5a3a22', pants: '#3a2a1a', shoes: '#1a1008', shirt: '#d8c8a8' }, hat: 'top', face: { skin: '#e2b896', hair: '#7a3a1a', hairStyle: 'short', beard: 'full', beardColor: '#a04a20', seed: 61 } },
  ladyRed: { female: true, dress: '#c8241c', clothes: { kind: 'dress', top: '#c8241c', sleeve: '#e6b896', pants: '#c8241c' }, face: { skin: '#e6b896', hair: '#5a2a14', hairStyle: 'long', female: true, lip: '#c03a3a', seed: 62, makeup: 1 } },
  ladyGreen: { female: true, dress: '#1e6a5a', skirtLong: true, clothes: { kind: 'dress', top: '#1e6a5a', sleeve: '#1e6a5a', pants: '#1e6a5a' }, face: { skin: '#e8c0a0', hair: '#e8e0d0', hairStyle: 'bun', female: true, age: 0.85, smile: 0.5, seed: 63 } },
  blondBlue: { clothes: { kind: 'hoodie', top: '#2a5ab0', sleeve: '#2a5ab0', pants: '#202838' }, face: { skin: '#e8c4a8', hair: '#e0c070', hairStyle: 'short', seed: 64 } },
  redShirt: { clothes: { kind: 'tee', top: '#c0302a', sleeve: '#c0302a', pants: '#2a3a5a' }, face: { skin: '#c8946a', hair: '#1a1410', hairStyle: 'short', seed: 65 } },
  mugDealer: { clothes: { kind: 'tank', top: '#121212', sleeve: '#d9a888', pants: '#1a1a2a' }, bareArms: true, face: { skin: '#d9a888', hair: '#141010', hairStyle: 'slick', eye: '#2a2a2a', seed: 71 }, glasses: 'sun', build: 1.15 },
  mugWheel: { clothes: { kind: 'jacket', top: '#7a4a24', sleeve: '#7a4a24', pants: '#4a2a14', shirt: '#e8d8c0' }, hat: 'top', face: { skin: '#e8c0a4', hair: '#b85a2a', hairStyle: 'short', beard: 'full', beardColor: '#c05a28', seed: 72 } },
  mugCard: { female: true, dress: '#1aa0a0', clothes: { kind: 'zigzag', top: '#1a9a9a', sleeve: '#1a9a9a', pants: '#1a9a9a' }, face: { skin: '#e8c0a0', hair: '#c8784a', hairStyle: 'short', female: true, seed: 73 } },
};

const CROWD_LOOKS = [
  { clothes: { kind: 'tee', top: '#c0302a', sleeve: '#c0302a', pants: '#2a3a5a' } },
  { clothes: { kind: 'suit', top: '#2a4aa0', sleeve: '#2a4aa0', pants: '#1a2a5a', tie: 'plain', tieColor: '#c0a030' } },
  { clothes: { kind: 'hoodie', top: '#e0e0e0', sleeve: '#e0e0e0', pants: '#3a3a3a', print: '#c03030' } },
  { clothes: { kind: 'jacket', top: '#7a5a3a', sleeve: '#7a5a3a', pants: '#3a2a1a' }, hat: 'top' },
  { female: true, dress: '#d0302a', clothes: { kind: 'dress', top: '#d0302a', sleeve: '#d0302a', pants: '#d0302a' } },
  { clothes: { kind: 'tee', top: '#3a8ad0', sleeve: '#e0b090', pants: '#e0d0b0' }, bareArms: true },
  { clothes: { kind: 'suit', top: '#101014', sleeve: '#101014', pants: '#101014', tie: 'stripe' } },
  { female: true, dress: '#e0a030', clothes: { kind: 'dress', top: '#e0a030', sleeve: '#e0a030', pants: '#e0a030' } },
  { clothes: { kind: 'shirt', top: '#e8e8e8', sleeve: '#e8e8e8', pants: '#5a5a5a', under: '#e8e8e8' } },
  { clothes: { kind: 'hoodie', top: '#2a7a3a', sleeve: '#2a7a3a', pants: '#1a1a1a' } },
  { female: true, dress: '#1e6a5a', clothes: { kind: 'dress', top: '#1e6a5a', sleeve: '#1e6a5a', pants: '#1e6a5a' } },
  { clothes: { kind: 'jacket', top: '#a07a50', sleeve: '#a07a50', pants: '#4a3a2a', shirt: '#f0f0f0' } },
];
const SKINS = ['#e8c0a0', '#c8946a', '#8a5a3a', '#f0d0b8', '#d8a882', '#6a4430'];
const HAIRS = ['#1a1410', '#5a3a1a', '#e0c070', '#8a8a86', '#b85a2a', '#2a1a10', '#e8e0d0'];
const STYLES = ['short', 'slick', 'buzz', 'bald', 'curly', 'short'];

export function buildWorld(scene, Q) {
  const W = { scene, Q, cast: {}, crowd: [], props: {}, sets: {}, dyn: {} };
  // ------------------------------------------------------------ casino ---
  const casino = new THREE.Group();
  casino.name = 'casino';
  scene.add(casino);
  W.sets.casino = casino;
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), new THREE.MeshStandardMaterial({ map: TX.carpetTexture(), roughness: 0.95 }));
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  casino.add(floor);
  const wallTex = TX.wallTexture();
  const wallMat = new THREE.MeshStandardMaterial({ map: wallTex, roughness: 0.9 });
  const mkWall = (w, h, x, z, ry) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), wallMat);
    m.position.set(x, h / 2, z);
    m.rotation.y = ry;
    m.receiveShadow = true;
    casino.add(m);
    return m;
  };
  mkWall(20, 5, 0, -4.2, 0);
  mkWall(20, 5, 9, 2, -Math.PI / 2);
  mkWall(20, 5, -9, 2, Math.PI / 2);
  mkWall(20, 5, 0, 9, Math.PI);
  const ceil = new THREE.Mesh(new THREE.PlaneGeometry(20, 20), mat('#05070c', { rough: 1 }));
  ceil.rotation.x = Math.PI / 2;
  ceil.position.y = 4.4;
  casino.add(ceil);
  // wainscot rail along back wall
  const rail = new THREE.Mesh(box(20, 0.06, 0.06), mat('#2a3a7a', { rough: 0.5 }));
  rail.position.set(0, 1.0, -4.17);
  casino.add(rail);

  const table = P.makeTable();
  casino.add(table);
  W.props.table = table;
  W.props.wheel = table.userData.wheel;

  const board = P.makeBoard();
  board.position.set(0.95, 0.35, -2.45);
  board.rotation.y = -0.12;
  casino.add(board);
  W.props.board = board;
  const neon = P.neonStrip(3.4);
  neon.position.set(0.38, 0.55, -2.4);
  casino.add(neon);
  const rings = P.makeRings();
  rings.position.set(0.06, 1.13, -1.42);
  casino.add(rings);
  W.props.rings = rings;

  W.props.chandeliers = [];
  for (const [kind, x, y, z, s] of [['ornate', 0.1, 3.25, -1.25, 1.15], ['drum', -1.75, 3.05, -2.1, 0.95],
    ['drum', 2.4, 3.2, -1.4, 0.95], ['drumOrnate', -0.4, 3.35, 1.0, 1.1], ['drum', -3.3, 3.1, 1.5, 0.9],
    ['drum', 3.4, 3.1, 2.6, 0.9], ['ornate', -2.6, 3.4, -3.0, 0.9], ['drum', 1.0, 3.3, 4.6, 0.9]]) {
    const ch = P.makeChandelier(kind, s);
    ch.position.set(x, y, z);
    casino.add(ch);
    W.props.chandeliers.push(ch);
  }
  // TV on the back wall
  const tvC = document.createElement('canvas');
  tvC.width = 512; tvC.height = 300;
  W.dyn.tvCanvas = tvC;
  W.dyn.tvTex = TX.toTex(tvC);
  const tv = P.makeTV(W.dyn.tvTex, 1.35, 0.78);
  tv.position.set(-1.0, 2.78, -4.05);
  tv.rotation.x = 0.12;
  casino.add(tv);
  // plants
  for (const [x, z, sd, s] of [[-0.7, -3.6, 1, 1.15], [1.95, -3.55, 2, 1.1], [-2.4, -3.5, 3, 1.0], [3.4, -3.5, 4, 1.1],
    [-5.0, -3.5, 5, 1.0], [5.2, -3.6, 6, 1.0]]) {
    const pl = P.makePlant(sd, s);
    pl.position.set(x, 0, z);
    casino.add(pl);
  }
  // slot machines: bank on the back-left and right wall
  W.props.slots = [];
  for (let i = 0; i < 5; i++) {
    const sm = P.makeSlotMachine(i + 1);
    sm.position.set(-6.2 + i * 0.78, 0, -3.75);
    casino.add(sm);
    W.props.slots.push(sm);
  }
  for (let i = 0; i < 4; i++) {
    const sm = P.makeSlotMachine(i + 7);
    sm.position.set(8.55, 0, -1.5 + i * 0.8);
    sm.rotation.y = -Math.PI / 2;
    casino.add(sm);
  }
  // establishing-shot corner: painting + slot bank (front-left area of the room)
  const painting = new THREE.Group();
  const pframe = new THREE.Mesh(box(1.5, 1.2, 0.08), mat('#5a3a1a', { rough: 0.5, metal: 0.3 }));
  painting.add(pframe);
  W.dyn.paintCanvas = document.createElement('canvas');
  W.dyn.paintCanvas.width = 512; W.dyn.paintCanvas.height = 400;
  W.dyn.paintTex = TX.toTex(W.dyn.paintCanvas);
  const pimg = new THREE.Mesh(new THREE.PlaneGeometry(1.36, 1.06), new THREE.MeshStandardMaterial({ map: W.dyn.paintTex, roughness: 0.6, emissive: '#202020', emissiveMap: W.dyn.paintTex }));
  pimg.position.z = 0.045;
  painting.add(pimg);
  painting.position.set(-3.6, 2.8, 8.95);
  painting.rotation.y = Math.PI;
  casino.add(painting);
  for (let i = 0; i < 3; i++) {
    const sm = P.makeSlotMachine(i + 12);
    sm.position.set(-3.05 - i * 0.78, 0, 8.6);
    sm.rotation.y = Math.PI;
    casino.add(sm);
  }
  // background roulette tables
  W.props.bgTables = [];
  for (const [x, z, ry] of [[-3.1, -1.9, 0.5], [3.3, -2.0, -0.4], [-4.2, 4.6, 1.4], [-2.2, 6.6, 0.2], [3.8, 5.5, -1.2]]) {
    const t2 = P.makeTable({ layoutTex: W.props.table.children[0].material.map });
    t2.position.set(x, 0, z);
    t2.rotation.y = ry;
    t2.scale.setScalar(0.95);
    casino.add(t2);
    W.props.bgTables.push(t2);
  }
  // bar along the right side of the room
  const bar = P.makeBar();
  bar.position.set(-0.4, 0, 7.75);
  bar.rotation.y = Math.PI;
  casino.add(bar);
  W.props.bar = bar;
  // dome camera on the ceiling above the table
  const dome = P.makeDomeCam();
  dome.position.set(0.0, 4.36, 0.6);
  casino.add(dome);
  W.props.dome = dome;
  // claw machine in the far corner
  const claw = P.makeClawMachine();
  claw.position.set(4.6, 0, 3.4);
  claw.rotation.y = -Math.PI / 2 + 0.4;
  casino.add(claw);
  W.props.claw = claw;
  // chairs
  W.props.chairs = {};
  for (const [name, x, z, ry] of [['player', 0, 1.98, Math.PI], ['left', -1.08, 0.35, Math.PI / 2], ['right', 1.08, -0.15, -Math.PI / 2],
    ['left2', -1.08, -0.45, Math.PI / 2], ['right2', 1.08, 0.75, -Math.PI / 2]]) {
    const c = P.makeChair();
    c.position.set(x, 0, z);
    c.rotation.y = ry + Math.PI;
    casino.add(c);
    W.props.chairs[name] = c;
  }
  // rake
  const rake = P.makeRake();
  rake.visible = false;
  casino.add(rake);
  W.props.rake = rake;
  // chips container (rebuilt per shot)
  W.props.chipRoot = new THREE.Group();
  casino.add(W.props.chipRoot);

  // ------------------------------------------------------------ lights ---
  const L = {};
  L.hemi = new THREE.HemisphereLight('#3a52b0', '#2a140c', 0.6);
  scene.add(L.hemi);
  L.key = new THREE.SpotLight('#ffe2b8', 11, 14, 0.62, 0.55, 1.3);
  L.key.position.set(0.1, 3.6, -0.3);
  L.key.target.position.set(0, 0.8, 0.0);
  L.key.castShadow = true;
  L.key.shadow.mapSize.set(Q.shadow, Q.shadow);
  L.key.shadow.bias = -0.0004;
  L.key.shadow.normalBias = 0.02;
  scene.add(L.key, L.key.target);
  L.dealerFill = new THREE.PointLight('#ffd0a0', 2.2, 6, 1.6);
  L.dealerFill.position.set(0.2, 2.6, -0.6);
  scene.add(L.dealerFill);
  L.wallWash = new THREE.PointLight('#3a62e0', 3.2, 9, 1.4);
  L.wallWash.position.set(-1.0, 3.0, -2.6);
  scene.add(L.wallWash);
  L.wallWash2 = new THREE.PointLight('#4a5ae0', 2.6, 9, 1.4);
  L.wallWash2.position.set(2.5, 2.6, -3.0);
  scene.add(L.wallWash2);
  L.room = [];
  for (const [x, z] of [[-3.0, 1.2], [2.8, 3.4], [-3.4, 5.6]]) {
    const pl = new THREE.PointLight('#ffcf90', 3.0, 9, 1.4);
    pl.position.set(x, 2.8, z);
    scene.add(pl);
    L.room.push(pl);
  }
  // cool rim light from behind the dealer: separates silhouettes from the dark room
  L.rim = new THREE.DirectionalLight('#6a8cff', 0.55);
  L.rim.position.set(-1.5, 3.5, -6);
  L.rim.target.position.set(0, 1, 1);
  scene.add(L.rim, L.rim.target);
  W.lights = L;

  // ------------------------------------------------------------- cast ---
  for (const [name, def] of Object.entries(CAST_DEF)) {
    const c = makeCharacter({ name, ...def, seed: def.face?.seed || 1 });
    c.root.visible = false;
    scene.add(c.root);
    W.cast[name] = c;
  }
  const r = rng(99);
  for (let i = 0; i < 26; i++) {
    const look = CROWD_LOOKS[i % CROWD_LOOKS.length];
    const fem = !!look.female;
    const face = {
      skin: SKINS[Math.floor(r() * SKINS.length)], hair: HAIRS[Math.floor(r() * HAIRS.length)],
      hairStyle: fem ? (r() < 0.5 ? 'long' : 'bun') : STYLES[Math.floor(r() * STYLES.length)],
      beard: !fem && r() < 0.35 ? (r() < 0.5 ? 'full' : 'stubble') : 'none', female: fem, seed: 200 + i, smile: r() * 0.6, age: r(),
    };
    const c = makeCharacter({ name: 'crowd' + i, ...look, face, seed: 200 + i, glasses: !fem && r() < 0.15 ? 'sun' : null, scale: 0.92 + r() * 0.14 });
    c.root.visible = false;
    scene.add(c.root);
    W.crowd.push(c);
  }

  // ------------------------------------------------- surveillance room ---
  const surv = new THREE.Group();
  surv.position.copy(SURV);
  scene.add(surv);
  W.sets.surv = surv;
  const sFloor = new THREE.Mesh(new THREE.PlaneGeometry(14, 14), mat('#14161c', { rough: 0.9 }));
  sFloor.rotation.x = -Math.PI / 2;
  surv.add(sFloor);
  const sWallM = mat('#0e1418', { rough: 0.9 });
  for (const [w, x, z, ry] of [[14, 0, -3.2, 0], [14, -4.5, 0, Math.PI / 2], [14, 4.5, 0, -Math.PI / 2], [14, 0, 5, Math.PI]]) {
    const wl = new THREE.Mesh(new THREE.PlaneGeometry(w, 4), sWallM);
    wl.position.set(x, 2, z);
    wl.rotation.y = ry;
    surv.add(wl);
  }
  const sCeil = new THREE.Mesh(new THREE.PlaneGeometry(14, 14), mat('#0a0c10', { rough: 1 }));
  sCeil.rotation.x = Math.PI / 2;
  sCeil.position.y = 3.2;
  surv.add(sCeil);
  const mw = P.makeMonitorWall(9, 5, 1.0);
  mw.group.position.set(0, 0.85, -2.6);
  surv.add(mw.group);
  W.props.monitors = mw.screens;
  // desk running along the monitor wall
  const desk = new THREE.Mesh(box(7.5, 0.06, 1.0), new THREE.MeshStandardMaterial({ map: TX.woodTexture('#b8a078', 5, 0.25), roughness: 0.6 }));
  desk.position.set(0, 0.76, -1.6);
  surv.add(desk);
  const deskFront = new THREE.Mesh(box(7.5, 0.74, 0.05), mat('#1a1c20'));
  deskFront.position.set(0, 0.37, -1.12);
  surv.add(deskFront);
  W.props.keyboards = [];
  for (const x of [-1.6, 0.0, 1.6]) {
    const kb = P.makeKeyboard();
    kb.position.set(x, 0.8, -1.45);
    kb.rotation.x = 0.06;
    surv.add(kb);
    W.props.keyboards.push(kb);
  }
  const papers = new THREE.Mesh(box(0.3, 0.01, 0.4), mat('#e8e8e8'));
  papers.position.set(0.9, 0.795, -1.5);
  papers.rotation.y = 0.3;
  surv.add(papers);
  for (const x of [-1.7, 0.0, 1.7]) {
    const ch = P.makeChair();
    ch.position.set(x, 0, -0.75);
    surv.add(ch);
  }
  // ceiling lights (bright irregular discs)
  W.props.survLamps = [];
  for (let i = 0; i < 6; i++) {
    const lamp = new THREE.Mesh(new THREE.CircleGeometry(0.16, 7), new THREE.MeshBasicMaterial({ color: new THREE.Color(3, 3.2, 3.6) }));
    lamp.rotation.x = Math.PI / 2;
    lamp.position.set(-3 + i * 1.2, 3.18, -0.6 + (i % 2) * 0.3);
    surv.add(lamp);
    W.props.survLamps.push(lamp);
  }
  const sl = new THREE.SpotLight('#cfe0ff', 7, 9, 0.9, 0.8, 1.5);
  sl.position.set(SURV.x, 3.1, SURV.z + 0.5);
  sl.target.position.set(SURV.x, 0.8, SURV.z - 1.5);
  scene.add(sl, sl.target);
  const sl2 = new THREE.PointLight('#a0b8ff', 3.5, 8, 1.4);
  sl2.position.set(SURV.x, 1.6, SURV.z - 1.6);
  scene.add(sl2);
  W.lights.surv = [sl, sl2];

  // ------------------------------------------------------------ office ---
  const office = new THREE.Group();
  office.position.copy(OFFICE);
  scene.add(office);
  W.sets.office = office;
  const panelMat = new THREE.MeshStandardMaterial({ map: TX.woodPanelTexture(), roughness: 0.55 });
  const oWall = new THREE.Mesh(new THREE.PlaneGeometry(8, 4), panelMat);
  oWall.position.set(0, 2, -1.6);
  office.add(oWall);
  const oFloor = new THREE.Mesh(new THREE.PlaneGeometry(8, 8), mat('#2a1a10'));
  oFloor.rotation.x = -Math.PI / 2;
  office.add(oFloor);
  const oDesk = new THREE.Mesh(box(2.0, 0.08, 0.9), new THREE.MeshStandardMaterial({ map: TX.woodTexture('#5a2a10', 7, 0.4), roughness: 0.45 }));
  oDesk.position.set(0, 0.78, 0.35);
  office.add(oDesk);
  const plaque = new THREE.Mesh(box(0.4, 0.06, 0.02), new THREE.MeshStandardMaterial({ color: '#c8a050', metalness: 0.8, roughness: 0.3 }));
  plaque.position.set(0, 0.84, 0.78);
  office.add(plaque);
  const oChair = new THREE.Mesh(box(0.7, 1.1, 0.15), mat('#2a1810', { rough: 0.5 }));
  oChair.position.set(0, 1.0, -0.55);
  office.add(oChair);
  const ol = new THREE.SpotLight('#ffb070', 9, 7, 0.8, 0.7, 1.4);
  ol.position.set(OFFICE.x + 0.3, 2.9, OFFICE.z + 1.6);
  ol.target.position.set(OFFICE.x, 1.4, OFFICE.z - 1.0);
  scene.add(ol, ol.target);
  W.lights.office = [ol];

  // ----------------------------------------------------- mugshot booth ---
  const booth = new THREE.Group();
  booth.position.copy(BOOTH);
  scene.add(booth);
  W.sets.booth = booth;
  const [lc, lg] = TX.canvas(512, 512);
  lg.fillStyle = '#7a7a78'; lg.fillRect(0, 0, 512, 512);
  lg.fillStyle = '#4a4a48';
  for (let y = 16; y < 512; y += 34) lg.fillRect(0, y, 512, 5);
  TX.noiseFill(lg, 512, 512, 0, 10, 8, 1);
  const lineup = new THREE.Mesh(new THREE.PlaneGeometry(3, 3), new THREE.MeshStandardMaterial({ map: TX.toTex(lc), roughness: 0.9 }));
  lineup.position.set(0, 1.5, -0.6);
  booth.add(lineup);
  const bl = new THREE.DirectionalLight('#ffffff', 2.6);
  bl.position.set(BOOTH.x + 0.6, 2.4, BOOTH.z + 2.5);
  bl.target.position.set(BOOTH.x, 1.4, BOOTH.z);
  scene.add(bl, bl.target);
  W.lights.booth = [bl];
  return W;
}

// casino TV screen: stylised blue chip-layout graphic
export function drawTV(W, t) {
  const c = W.dyn.tvCanvas, g = c.getContext('2d');
  const w = c.width, h = c.height;
  const grd = g.createLinearGradient(0, 0, 0, h);
  grd.addColorStop(0, '#1a3a8a'); grd.addColorStop(1, '#2a6a9a');
  g.fillStyle = grd;
  g.fillRect(0, 0, w, h);
  g.save();
  g.translate(w / 2, h * 0.2);
  const off = (t * 40) % 60;
  g.strokeStyle = '#e8f0ff';
  g.lineWidth = 3;
  for (let i = -6; i <= 6; i++) {
    g.beginPath(); g.moveTo(i * 40, 0); g.lineTo(i * 110, h); g.stroke();
  }
  for (let j = 0; j < 7; j++) {
    const y = ((j * 60 + off) / 420) ** 1.6 * h;
    g.beginPath(); g.moveTo(-w, y); g.lineTo(w, y); g.stroke();
  }
  g.restore();
  const cols = ['#c02a2a', '#2a2a2a', '#3a5ad0'];
  for (let i = 0; i < 9; i++) {
    const x = 60 + ((i * 97) % 420), y = 80 + ((i * 53) % 160);
    const hh = 30 + (i % 4) * 22;
    g.fillStyle = cols[i % 3];
    g.fillRect(x, y - hh, 34, hh);
    g.fillStyle = 'rgba(255,255,255,0.7)';
    for (let k = 0; k < hh; k += 8) g.fillRect(x + 4, y - hh + k, 8, 3);
  }
  g.fillStyle = '#5a7a4a';
  g.fillRect(0, h - 40, w, 40);
  W.dyn.tvTex.needsUpdate = true;
}

export function drawPainting(W) {
  const c = W.dyn.paintCanvas, g = c.getContext('2d');
  g.fillStyle = '#1a2a2a'; g.fillRect(0, 0, 512, 400);
  g.fillStyle = '#2a6a3a'; g.fillRect(40, 250, 440, 120);
  g.fillStyle = '#0e0e0e';
  for (const x of [130, 300]) { g.fillRect(x, 120, 70, 160); g.beginPath(); g.arc(x + 35, 100, 26, 0, Math.PI * 2); g.fillStyle = '#c8a080'; g.fill(); g.fillStyle = '#0e0e0e'; }
  for (let i = 0; i < 6; i++) { g.fillStyle = ['#c02020', '#e8e8e8', '#2040c0'][i % 3]; g.fillRect(220 + i * 18, 200 - i * 10, 14, 60 + i * 10); }
  W.dyn.paintTex.needsUpdate = true;
}
