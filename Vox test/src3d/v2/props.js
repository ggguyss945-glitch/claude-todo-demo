// Casino props, all built from primitives + canvas textures.
import * as THREE from 'three';
import * as TX from './tex.js';
import { mat, cyl, box } from './chars.js';
import { rng } from './util.js';

export const TABLE = {
  W: 1.36, L: 3.1, H: 0.8,
  grid: { cols: 3, rows: 12, x0: -0.39, z0: -0.62, cw: 0.26, ch: 0.112 },
  spots: [
    { name: 'red', x: -0.42, z: 1.06, r: 0.135, color: '#e0281e' },
    { name: 'black', x: 0.0, z: 1.2, r: 0.14, color: '#111111' },
    { name: 'green', x: 0.42, z: 1.06, r: 0.135, color: '#22b83a' },
  ],
  wheel: { x: 0.0, z: -1.08, r: 0.3 },
};

function stadiumShape(w, l, inset = 0) {
  const r = w / 2 - inset;
  const hl = l / 2 - w / 2;
  const s = new THREE.Shape();
  s.moveTo(-r, -hl);
  s.absarc(0, -hl, r, Math.PI, 0, false);
  s.lineTo(r, hl);
  s.absarc(0, hl, r, 0, Math.PI, false);
  s.closePath();
  return s;
}

export function makeTable(opts = {}) {
  const T = TABLE;
  const g = new THREE.Group();
  const layout = opts.layoutTex || TX.layoutTexture(T);
  // felt top: stadium shape, UV planar
  const feltGeo = new THREE.ShapeGeometry(stadiumShape(T.W, T.L, 0.0), 48);
  feltGeo.rotateX(-Math.PI / 2);
  const p = feltGeo.attributes.position;
  const uv = feltGeo.attributes.uv;
  for (let i = 0; i < p.count; i++) uv.setXY(i, (p.getX(i) + T.W / 2) / T.W, 1 - (p.getZ(i) + T.L / 2) / T.L);
  // note: ShapeGeometry is in XY before rotation; after rotateX(-90) shape y -> -z
  const felt = new THREE.Mesh(feltGeo, new THREE.MeshStandardMaterial({ map: layout, roughness: 0.95 }));
  felt.position.y = T.H;
  felt.receiveShadow = true;
  g.add(felt);
  // padded leather rail (extruded ring)
  const outer = stadiumShape(T.W + 0.22, T.L + 0.22);
  outer.holes.push(new THREE.Path(stadiumShape(T.W - 0.0, T.L - 0.0).getPoints(48)));
  const railGeo = new THREE.ExtrudeGeometry(outer, { depth: 0.07, bevelEnabled: true, bevelSize: 0.03, bevelThickness: 0.03, bevelSegments: 2, curveSegments: 24 });
  railGeo.rotateX(-Math.PI / 2);
  const rail = new THREE.Mesh(railGeo, new THREE.MeshStandardMaterial({ color: '#c0602e', roughness: 0.55, map: TX.leatherTexture('#c4642e') }));
  rail.position.y = T.H - 0.03;
  rail.castShadow = true; rail.receiveShadow = true;
  g.add(rail);
  // wooden apron + base
  const apronGeo = new THREE.ExtrudeGeometry(stadiumShape(T.W + 0.18, T.L + 0.18), { depth: 0.16, bevelEnabled: false, curveSegments: 24 });
  apronGeo.rotateX(-Math.PI / 2);
  const apron = new THREE.Mesh(apronGeo, mat('#4a2a16', { rough: 0.6 }));
  apron.position.y = T.H - 0.2;
  g.add(apron);
  const baseGeo = new THREE.ExtrudeGeometry(stadiumShape(T.W - 0.4, T.L - 0.5), { depth: 0.6, bevelEnabled: false, curveSegments: 16 });
  baseGeo.rotateX(-Math.PI / 2);
  const base = new THREE.Mesh(baseGeo, mat('#20242c', { rough: 0.7 }));
  g.add(base);
  // wheel
  const wheel = makeWheel();
  wheel.group.position.set(T.wheel.x, T.H, T.wheel.z);
  g.add(wheel.group);
  g.userData.wheel = wheel;
  g.traverse((m) => { if (m.isMesh) m.receiveShadow = true; });
  return g;
}

export function makeWheel() {
  const R = TABLE.wheel.r;
  const group = new THREE.Group();
  // outer wooden bowl (low poly, like the original)
  const bowl = new THREE.Mesh(cyl(R * 1.22, R * 1.3, 0.1, 16, 1, true), mat('#7a4a28', { rough: 0.5, extra: { side: THREE.DoubleSide } }));
  bowl.position.y = 0.04;
  group.add(bowl);
  const rimTop = new THREE.Mesh(new THREE.RingGeometry(R * 1.08, R * 1.22, 16, 1), mat('#6a3e20', { rough: 0.5 }));
  rimTop.rotation.x = -Math.PI / 2;
  rimTop.position.y = 0.09;
  group.add(rimTop);
  const lip = new THREE.Mesh(new THREE.TorusGeometry(R * 1.12, 0.022, 4, 16), mat('#5a321a', { rough: 0.5 }));
  lip.rotation.x = Math.PI / 2;
  lip.position.y = 0.092;
  group.add(lip);
  // ball track (slanted ring)
  const track = new THREE.Mesh(new THREE.CylinderGeometry(R * 1.08, R * 0.99, 0.035, 32, 1, true), mat('#9a6a3e', { rough: 0.45, extra: { side: THREE.DoubleSide } }));
  track.position.y = 0.072;
  group.add(track);
  const spin = new THREE.Group();
  spin.position.y = 0.055;
  group.add(spin);
  const ring = new THREE.Mesh(new THREE.CircleGeometry(R, 64), new THREE.MeshStandardMaterial({ map: TX.wheelRingTexture(), roughness: 0.4 }));
  ring.rotation.x = -Math.PI / 2;
  spin.add(ring);
  // pocket separators (little frets)
  const fretMat = mat('#d8c8a0', { metal: 0.6, rough: 0.3 });
  for (let i = 0; i < 37; i++) {
    const a = (i / 37) * Math.PI * 2 + Math.PI / 37;
    const f = new THREE.Mesh(box(0.004, 0.012, R * 0.22), fretMat);
    f.position.set(Math.sin(a) * R * 0.66, 0.006, -Math.cos(a) * R * 0.66);
    f.rotation.y = -a;
    spin.add(f);
  }
  const cone = new THREE.Mesh(new THREE.ConeGeometry(R * 0.55, 0.06, 24), mat('#8a5a30', { rough: 0.5 }));
  cone.position.y = 0.03;
  spin.add(cone);
  const gold = new THREE.MeshStandardMaterial({ color: '#d8a838', metalness: 0.9, roughness: 0.25, emissive: '#2a1800' });
  const post = new THREE.Mesh(cyl(0.012, 0.02, 0.09, 8), gold);
  post.position.y = 0.09;
  spin.add(post);
  for (let k = 0; k < 4; k++) {
    const arm = new THREE.Mesh(box(0.012, 0.012, R * 0.42), gold);
    arm.position.y = 0.11;
    arm.rotation.y = (k * Math.PI) / 2;
    arm.translateZ(R * 0.21);
    spin.add(arm);
    const knob = new THREE.Mesh(new THREE.SphereGeometry(0.012, 6, 4), gold);
    knob.position.copy(arm.position).add(new THREE.Vector3(Math.sin((k * Math.PI) / 2) * R * 0.21, 0, Math.cos((k * Math.PI) / 2) * R * 0.21));
    spin.add(knob);
  }
  const ball = new THREE.Mesh(new THREE.SphereGeometry(0.014, 12, 8), new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 0.15, emissive: '#555555' }));
  group.add(ball);
  group.traverse((m) => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } });
  return {
    group, spin, ball,
    update(t, speed = 1.2) {
      spin.rotation.y = -t * speed;
      // ball orbits the opposite way, slowly spiralling into the pocket ring
      const ph = (t % 7) / 7;
      const rr = R * (1.02 - 0.32 * Math.min(1, ph * 1.4));
      const ang = t * 3.6 * (1 - ph * 0.6);
      ball.position.set(Math.sin(ang) * rr, 0.07 + 0.01 * (1 - ph), Math.cos(ang) * rr);
    },
  };
}

// chip stack: one cylinder whose side texture repeats once per chip
const stackGeoCache = new Map();
export function chipStack(n, color = '#2a4fb0', label = '10', r = 0.04) {
  const h = 0.0075;
  const { side, top } = TX.chipTextures(color, label);
  const key = `${n}`;
  const sideTex = side.clone();
  sideTex.needsUpdate = true;
  sideTex.wrapS = sideTex.wrapT = THREE.RepeatWrapping;
  sideTex.repeat.set(1, n);
  const g = new THREE.CylinderGeometry(r, r, h * n, 24, 1, false);
  const m = new THREE.Mesh(g, [
    new THREE.MeshStandardMaterial({ map: sideTex, roughness: 0.45 }),
    new THREE.MeshStandardMaterial({ map: top, roughness: 0.4 }),
    new THREE.MeshStandardMaterial({ color, roughness: 0.5 }),
  ]);
  m.position.y = (h * n) / 2;
  m.castShadow = true;
  m.receiveShadow = true;
  const grp = new THREE.Group();
  grp.add(m);
  grp.userData.height = h * n;
  return grp;
}

export const BLUE = '#2a4fb0', REDC = '#c41e1e';

// a messy pile of stacks
export function chipPile(spec, seed = 1) {
  const r = rng(seed);
  const g = new THREE.Group();
  for (const s of spec) {
    const st = chipStack(s.n, s.color || BLUE, s.label || (s.color === REDC ? '50' : '10'), s.r || 0.04);
    st.position.set(s.x, 0, s.z);
    st.rotation.y = r() * Math.PI * 2;
    if (s.tilt) st.rotation.z = s.tilt;
    g.add(st);
  }
  return g;
}

// ------------------------------------------------------------- furniture ---
export function makeChair() {
  const g = new THREE.Group();
  const wood = mat('#4a2a14', { rough: 0.6 });
  const wick = new THREE.MeshStandardMaterial({ map: TX.wickerTexture(), roughness: 0.85 });
  const seat = new THREE.Mesh(box(0.46, 0.06, 0.44), wick);
  seat.position.y = 0.48;
  g.add(seat);
  const back = new THREE.Mesh(box(0.44, 0.5, 0.05), wick);
  back.position.set(0, 0.78, -0.2);
  back.rotation.x = -0.08;
  g.add(back);
  for (const [x, z] of [[-0.2, -0.19], [0.2, -0.19], [-0.2, 0.19], [0.2, 0.19]]) {
    const leg = new THREE.Mesh(box(0.04, 0.48, 0.04), wood);
    leg.position.set(x, 0.24, z);
    g.add(leg);
  }
  for (const x of [-0.22, 0.22]) {
    const post = new THREE.Mesh(box(0.045, 0.56, 0.045), wood);
    post.position.set(x, 0.78, -0.2);
    g.add(post);
  }
  g.traverse((m) => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } });
  return g;
}

// big ornate chandelier (white candle arms with scrolls under a green drum)
export function makeChandelier(kind = 'drum', s = 1) {
  const g = new THREE.Group();
  const lights = [];
  const metal = new THREE.MeshStandardMaterial({ color: '#d8d0c0', roughness: 0.4, metalness: 0.4 });
  const bulbMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(2.6, 2.1, 1.4) });
  const rod = new THREE.Mesh(cyl(0.008 * s, 0.008 * s, 1.6, 6), metal);
  rod.position.y = 0.8;
  g.add(rod);
  if (kind === 'drum' || kind === 'drumOrnate') {
    const shade = new THREE.Mesh(new THREE.CylinderGeometry(0.42 * s, 0.46 * s, 0.26 * s, 24, 1, true),
      new THREE.MeshStandardMaterial({ color: '#8fa63a', roughness: 0.8, side: THREE.DoubleSide, emissive: '#2a3a0c', emissiveIntensity: 1.0 }));
    shade.position.y = 0.05 * s;
    g.add(shade);
    const inner = new THREE.Mesh(new THREE.CylinderGeometry(0.415 * s, 0.455 * s, 0.25 * s, 24, 1, true),
      new THREE.MeshBasicMaterial({ color: new THREE.Color(0.9, 0.95, 0.45), side: THREE.BackSide }));
    inner.position.y = 0.05 * s;
    g.add(inner);
    for (const y of [0.18, -0.08]) {
      const rim = new THREE.Mesh(new THREE.TorusGeometry((y > 0 ? 0.42 : 0.46) * s, 0.008 * s, 4, 24), new THREE.MeshBasicMaterial({ color: new THREE.Color(2.2, 1.9, 1.2) }));
      rim.rotation.x = Math.PI / 2;
      rim.position.y = y * s;
      g.add(rim);
    }
  }
  const n = kind === 'ornate' ? 6 : 5;
  const armR = kind === 'ornate' ? 0.34 * s : 0.26 * s;
  const yArms = kind === 'ornate' ? -0.25 * s : -0.12 * s;
  const center = new THREE.Mesh(cyl(0.04 * s, 0.02 * s, 0.32 * s, 8), metal);
  center.position.y = yArms - 0.05 * s;
  g.add(center);
  const finial = new THREE.Mesh(new THREE.ConeGeometry(0.03 * s, 0.14 * s, 8), metal);
  finial.position.y = yArms - 0.26 * s;
  finial.rotation.x = Math.PI;
  g.add(finial);
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2;
    const x = Math.cos(a) * armR, z = Math.sin(a) * armR;
    const arm = new THREE.Mesh(new THREE.TorusGeometry(armR * 0.5, 0.009 * s, 4, 10, Math.PI), metal);
    arm.position.set(x * 0.5, yArms, z * 0.5);
    arm.rotation.y = -a;
    arm.rotation.x = Math.PI;
    g.add(arm);
    const cup = new THREE.Mesh(cyl(0.03 * s, 0.015 * s, 0.04 * s, 8), metal);
    cup.position.set(x, yArms + 0.02 * s, z);
    g.add(cup);
    const candle = new THREE.Mesh(cyl(0.013 * s, 0.013 * s, 0.12 * s, 6), new THREE.MeshStandardMaterial({ color: '#f4efe0', emissive: '#6a5a40' }));
    candle.position.set(x, yArms + 0.1 * s, z);
    g.add(candle);
    const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.02 * s, 8, 6), bulbMat);
    bulb.scale.y = 1.6;
    bulb.position.set(x, yArms + 0.18 * s, z);
    g.add(bulb);
    if (kind === 'ornate') {
      const shade = new THREE.Mesh(new THREE.ConeGeometry(0.05 * s, 0.07 * s, 8, 1, true), new THREE.MeshStandardMaterial({ color: '#f0e8d8', emissive: '#a08a60', side: THREE.DoubleSide }));
      shade.position.set(x, yArms + 0.2 * s, z);
      g.add(shade);
    }
    lights.push(bulb);
  }
  g.userData.bulbs = lights;
  return g;
}

export function makeRings() {
  // five glowing result rings floating over the table near the dealer
  const g = new THREE.Group();
  const ringMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(1.7, 1.7, 1.7) });
  const fills = {
    red: new THREE.MeshBasicMaterial({ map: TX.ringFillTexture('#d83a30'), color: new THREE.Color(1.15, 1.0, 1.0) }),
    green: new THREE.MeshBasicMaterial({ map: TX.ringFillTexture('#3aa83a'), color: new THREE.Color(1.0, 1.15, 1.0) }),
    black: new THREE.MeshBasicMaterial({ map: TX.ringFillTexture('#202020'), color: new THREE.Color(1.2, 1.2, 1.2) }),
  };
  const discs = [];
  for (let i = 0; i < 5; i++) {
    const r = new THREE.Mesh(new THREE.TorusGeometry(0.068, 0.0075, 6, 32), ringMat);
    r.position.x = i * 0.175;
    g.add(r);
    const d = new THREE.Mesh(new THREE.CircleGeometry(0.062, 24), fills.red);
    d.position.x = i * 0.175;
    d.position.z = -0.002;
    g.add(d);
    discs.push(d);
  }
  const bar = new THREE.Mesh(box(0.11, 0.012, 0.01), ringMat);
  bar.position.set(0.0, -0.12, 0);
  g.add(bar);
  g.userData.set = (states) => {
    states.forEach((s, i) => {
      discs[i].visible = !!s;
      if (s) discs[i].material = fills[s];
    });
  };
  return g;
}

export function makeBoard() {
  const b = TX.makeBoard();
  const g = new THREE.Group();
  const panel = new THREE.Mesh(box(1.0, 2.3, 0.06), [
    mat('#14502a'), mat('#14502a'), mat('#14502a'), mat('#14502a'),
    new THREE.MeshStandardMaterial({ map: b.tex, emissiveMap: b.emi, emissive: new THREE.Color(1.1, 1.1, 1.1), roughness: 0.85 }),
    mat('#14502a'),
  ]);
  panel.position.y = 1.15;
  g.add(panel);
  g.userData.draw = b.draw;
  return g;
}

export function neonStrip(h = 2.6) {
  const m = new THREE.Mesh(box(0.018, h, 0.018), new THREE.MeshBasicMaterial({ color: new THREE.Color(2.0, 2.0, 2.2) }));
  m.position.y = h / 2;
  return m;
}

export function makeTV(screenTex, w = 1.3, h = 0.76) {
  const g = new THREE.Group();
  const frame = new THREE.Mesh(box(w + 0.06, h + 0.06, 0.06), mat('#101010', { rough: 0.4 }));
  g.add(frame);
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: screenTex, color: new THREE.Color(1.25, 1.25, 1.35) }));
  scr.position.z = 0.032;
  g.add(scr);
  g.userData.screen = scr;
  return g;
}

export function makePlant(seed = 1, s = 1) {
  const g = new THREE.Group();
  const r = rng(seed);
  const pot = new THREE.Mesh(cyl(0.22 * s, 0.17 * s, 0.4 * s, 10), mat('#2a2018', { rough: 0.6 }));
  pot.position.y = 0.2 * s;
  g.add(pot);
  const leafMat = new THREE.MeshStandardMaterial({ color: '#1e5a2a', roughness: 0.7, side: THREE.DoubleSide, flatShading: true });
  for (let i = 0; i < 14; i++) {
    const a = r() * Math.PI * 2;
    const len = (0.7 + r() * 0.6) * s;
    const leaf = new THREE.Mesh(new THREE.PlaneGeometry(0.16 * s, len, 1, 4), leafMat);
    const pp = leaf.geometry.attributes.position;
    for (let k = 0; k < pp.count; k++) {
      const y = pp.getY(k) / len + 0.5;
      pp.setX(k, pp.getX(k) * Math.sin(Math.PI * Math.min(1, y * 1.05)) * 1.2);
      pp.setZ(k, -y * y * 0.35 * s);
    }
    leaf.geometry.computeVertexNormals();
    leaf.position.y = 0.4 * s + len * 0.45;
    leaf.rotation.y = a;
    leaf.rotation.x = -0.35 - r() * 0.5;
    leaf.geometry.translate(0, len * 0.0, 0);
    const pivot = new THREE.Group();
    pivot.position.y = 0.4 * s;
    pivot.rotation.y = a;
    leaf.position.set(0, len / 2, 0);
    leaf.rotation.set(0, 0, 0);
    const tilt = new THREE.Group();
    tilt.rotation.x = 0.3 + r() * 0.7;
    tilt.add(leaf);
    pivot.add(tilt);
    g.add(pivot);
  }
  return g;
}

export function makeSlotMachine(seed = 1) {
  const g = new THREE.Group();
  const body = new THREE.Mesh(box(0.7, 1.5, 0.6), mat('#1a2a5a', { rough: 0.4, metal: 0.3 }));
  body.position.y = 0.75;
  g.add(body);
  const top = new THREE.Mesh(box(0.72, 0.35, 0.5), new THREE.MeshStandardMaterial({ color: '#3a6ae0', emissive: '#2050d0', emissiveIntensity: 0.7 }));
  top.position.set(0, 1.68, -0.02);
  g.add(top);
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.55, 0.75), new THREE.MeshBasicMaterial({ map: TX.slotScreenTexture(seed), color: new THREE.Color(1.05, 1.05, 1.15) }));
  scr.position.set(0, 1.05, 0.305);
  scr.rotation.x = -0.12;
  g.add(scr);
  const ledge = new THREE.Mesh(box(0.7, 0.05, 0.25), mat('#c8c8d0', { metal: 0.6, rough: 0.3 }));
  ledge.position.set(0, 0.62, 0.38);
  g.add(ledge);
  const edge = new THREE.Mesh(box(0.02, 1.5, 0.02), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.5, 1.1, 2.2) }));
  edge.position.set(-0.36, 0.95, 0.3);
  g.add(edge);
  const edge2 = edge.clone();
  edge2.position.x = 0.36;
  g.add(edge2);
  return g;
}

export function makeBar() {
  const g = new THREE.Group();
  const counter = new THREE.Mesh(box(5.0, 1.1, 0.7), mat('#1c2a44', { rough: 0.5 }));
  counter.position.y = 0.55;
  g.add(counter);
  const topM = new THREE.Mesh(box(5.1, 0.06, 0.8), mat('#c8c8d8', { rough: 0.3, metal: 0.4 }));
  topM.position.y = 1.12;
  g.add(topM);
  const shelfMat = new THREE.MeshStandardMaterial({ color: '#e8e0d0', emissive: '#806a40', roughness: 0.4 });
  for (const y of [1.55, 1.95]) {
    const sh = new THREE.Mesh(box(4.6, 0.04, 0.25), shelfMat);
    sh.position.set(0, y, -0.9);
    g.add(sh);
  }
  const r = rng(12);
  const cols = ['#2a5a2a', '#6a2a1a', '#d8c070', '#1a1a1a', '#5a7ab0', '#c8e0e8'];
  for (let i = 0; i < 34; i++) {
    const shelfY = i < 17 ? 1.57 : 1.97;
    const x = -2.2 + (i % 17) * 0.27 + r() * 0.05;
    const h = 0.18 + r() * 0.12;
    const bot = new THREE.Mesh(cyl(0.035, 0.04, h, 8), new THREE.MeshStandardMaterial({ color: cols[Math.floor(r() * cols.length)], roughness: 0.15, metalness: 0.1, emissive: '#101010' }));
    bot.position.set(x, shelfY + h / 2, -0.9);
    g.add(bot);
    const neck = new THREE.Mesh(cyl(0.012, 0.012, 0.08, 6), bot.material);
    neck.position.set(x, shelfY + h + 0.04, -0.9);
    g.add(neck);
  }
  const back = new THREE.Mesh(box(5.2, 2.6, 0.1), mat('#13204a', { rough: 0.8 }));
  back.position.set(0, 1.3, -1.05);
  g.add(back);
  const light = new THREE.Mesh(box(4.6, 0.03, 0.03), new THREE.MeshBasicMaterial({ color: new THREE.Color(2.5, 2.2, 1.6) }));
  light.position.set(0, 2.3, -0.85);
  g.add(light);
  return g;
}

export function makeRake() {
  const g = new THREE.Group();
  const m = mat('#2a2a2e', { rough: 0.5 });
  const handle = new THREE.Mesh(box(0.035, 0.03, 1.2), m);
  handle.position.z = 0.6;
  g.add(handle);
  const head = new THREE.Mesh(box(0.36, 0.07, 0.035), m);
  head.position.z = 1.2;
  g.add(head);
  g.traverse((x) => { if (x.isMesh) x.castShadow = true; });
  return g;
}

export function makeDomeCam() {
  const g = new THREE.Group();
  const base = new THREE.Mesh(cyl(0.34, 0.34, 0.06, 8), mat('#2a2a2e', { rough: 0.5 }));
  g.add(base);
  const dome = new THREE.Mesh(new THREE.SphereGeometry(0.3, 10, 6, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2),
    new THREE.MeshStandardMaterial({ color: '#16161a', roughness: 0.12, metalness: 0.85, envMapIntensity: 3.0 }));
  dome.position.y = -0.03;
  g.add(dome);
  const led = new THREE.Mesh(new THREE.SphereGeometry(0.018, 8, 6), new THREE.MeshBasicMaterial({ color: new THREE.Color(4, 0.3, 0.2) }));
  led.position.set(-0.05, -0.17, 0.24);
  g.add(led);
  g.userData.dome = dome;
  return g;
}

export function makeKeyboard() {
  const g = new THREE.Group();
  const b = new THREE.Mesh(box(0.46, 0.025, 0.16), mat('#d8d8d0', { rough: 0.6 }));
  g.add(b);
  const keyM = mat('#eeeeea', { rough: 0.6 });
  for (let r = 0; r < 5; r++) for (let c = 0; c < 15; c++) {
    const k = new THREE.Mesh(box(0.024, 0.012, 0.024), keyM);
    k.position.set(-0.2 + c * 0.0285, 0.016, -0.06 + r * 0.029);
    g.add(k);
  }
  return g;
}

export function makeWalkie() {
  const g = new THREE.Group();
  const body = new THREE.Mesh(box(0.06, 0.15, 0.035), mat('#9a9aa0', { rough: 0.4, metal: 0.3 }));
  g.add(body);
  const ant = new THREE.Mesh(cyl(0.006, 0.006, 0.1, 6), mat('#202020'));
  ant.position.set(0.018, 0.12, 0);
  g.add(ant);
  const grill = new THREE.Mesh(box(0.045, 0.05, 0.004), mat('#5a5a60'));
  grill.position.set(0, 0.02, 0.019);
  g.add(grill);
  return g;
}

export function makePhone() {
  const g = new THREE.Group();
  const m = mat('#1a1a1c', { rough: 0.35 });
  const handle = new THREE.Mesh(box(0.04, 0.2, 0.04), m);
  g.add(handle);
  for (const y of [-0.1, 0.1]) {
    const cup = new THREE.Mesh(box(0.06, 0.05, 0.07), m);
    cup.position.set(0, y, 0.02);
    g.add(cup);
  }
  return g;
}

export function makeClawMachine() {
  const g = new THREE.Group();
  const ht = new THREE.MeshStandardMaterial({ map: TX.halftoneTexture(), roughness: 0.35, emissive: '#0a2a6a', emissiveIntensity: 0.6 });
  const htTop = new THREE.MeshStandardMaterial({ map: TX.halftoneTexture('#1a6ad8', '#2a8af0'), roughness: 0.35, emissive: '#1a50c0', emissiveIntensity: 0.9 });
  const plate = new THREE.MeshStandardMaterial({ map: TX.diamondPlateTexture(), roughness: 0.35, metalness: 0.5 });
  const metal = mat('#c8c8cc', { rough: 0.3, metal: 0.5 });
  const lower = new THREE.Mesh(box(1.0, 0.95, 0.85), ht);
  lower.position.y = 0.475;
  g.add(lower);
  const top = new THREE.Mesh(box(1.04, 0.2, 0.9), htTop);
  top.position.y = 2.0;
  g.add(top);
  // glass cabinet frame posts
  for (const [x, z] of [[-0.48, 0.4], [0.48, 0.4], [-0.48, -0.4], [0.48, -0.4]]) {
    const p = new THREE.Mesh(box(0.05, 1.0, 0.05), metal);
    p.position.set(x, 1.45, z);
    g.add(p);
  }
  const back = new THREE.Mesh(box(0.96, 1.0, 0.02), plate);
  back.position.set(0, 1.45, -0.4);
  g.add(back);
  const side = new THREE.Mesh(box(0.02, 1.0, 0.8), plate);
  side.position.set(-0.47, 1.45, 0);
  g.add(side);
  const glass = new THREE.Mesh(box(0.94, 0.98, 0.01), new THREE.MeshStandardMaterial({ color: '#a0c0ff', transparent: true, opacity: 0.12, roughness: 0.05 }));
  glass.position.set(0, 1.45, 0.41);
  g.add(glass);
  // chute + claw
  const chute = new THREE.Mesh(box(0.3, 0.3, 0.3), metal);
  chute.position.set(-0.3, 1.1, 0.25);
  g.add(chute);
  const gantry = new THREE.Mesh(box(0.2, 0.08, 0.2), metal);
  gantry.position.set(-0.15, 1.88, 0.05);
  g.add(gantry);
  const cable = new THREE.Mesh(box(0.025, 0.28, 0.025), metal);
  cable.position.set(-0.15, 1.7, 0.05);
  g.add(cable);
  for (const s of [-1, 1]) {
    const claw = new THREE.Mesh(new THREE.TorusGeometry(0.06, 0.012, 4, 8, Math.PI * 0.8), metal);
    claw.position.set(-0.15 + s * 0.045, 1.53, 0.05);
    claw.rotation.z = s > 0 ? -0.4 : Math.PI + 0.4;
    g.add(claw);
  }
  // gold plush prizes
  const prize = new THREE.MeshStandardMaterial({ color: '#e8c030', roughness: 0.6, emissive: '#3a2a00' });
  const r = rng(5);
  for (let i = 0; i < 9; i++) {
    const p = new THREE.Mesh(box(0.14 + r() * 0.06, 0.08, 0.12), prize);
    p.position.set(0.05 + r() * 0.35, 1.0 + r() * 0.18, -0.2 + r() * 0.45);
    p.rotation.set(r(), r() * 3, r());
    g.add(p);
  }
  const deflector = new THREE.Mesh(box(0.4, 0.5, 0.02), mat('#9aa0a8', { rough: 0.4 }));
  deflector.position.set(0.18, 1.55, -0.32);
  g.add(deflector);
  // control panel
  const panel = new THREE.Mesh(box(0.7, 0.14, 0.32), mat('#e8e8ec', { rough: 0.35 }));
  panel.position.set(0.12, 0.98, 0.52);
  panel.rotation.x = 0.25;
  g.add(panel);
  const stick = new THREE.Mesh(cyl(0.012, 0.012, 0.14, 6), metal);
  stick.position.set(-0.02, 1.1, 0.5);
  g.add(stick);
  const knob = new THREE.Mesh(new THREE.SphereGeometry(0.045, 10, 8), new THREE.MeshStandardMaterial({ color: '#e01818', roughness: 0.2, emissive: '#400000' }));
  knob.position.set(-0.02, 1.19, 0.5);
  g.add(knob);
  const door = new THREE.Mesh(box(0.28, 0.32, 0.02), plate);
  door.position.set(0.1, 0.35, 0.43);
  g.add(door);
  return g;
}

// wall of CRT monitors (surveillance room); returns {group, screens[]}
export function makeMonitorWall(cols = 7, rows = 5, curve = 0.5) {
  const g = new THREE.Group();
  const screens = [];
  const frameM = mat('#3a3e44', { rough: 0.6 });
  const cw = 0.62, rh = 0.5;
  const Rr = 4.0 / curve;
  for (let c = 0; c < cols; c++) {
    const a = (c - (cols - 1) / 2) * (cw / Rr);
    const col = new THREE.Group();
    col.position.set(Math.sin(a) * Rr, 0, Rr - Math.cos(a) * Rr);
    col.rotation.y = -a;
    for (let r = 0; r < rows; r++) {
      const m = new THREE.Group();
      const body = new THREE.Mesh(box(cw * 0.96, rh * 0.94, 0.45), frameM);
      body.position.z = -0.22;
      m.add(body);
      const scr = new THREE.Mesh(new THREE.PlaneGeometry(cw * 0.82, rh * 0.76), new THREE.MeshBasicMaterial({ color: new THREE.Color(1.2, 1.2, 1.3) }));
      scr.position.z = 0.012;
      m.add(scr);
      m.position.set((c - (cols - 1) / 2) * 0, r * rh, 0);
      m.rotation.x = (r - 1) * 0.08;
      col.add(m);
      screens.push(scr);
    }
    g.add(col);
  }
  return { group: g, screens };
}
