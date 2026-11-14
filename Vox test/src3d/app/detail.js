// V3 set dressing: everything that adds density and depth to the sets
// (architecture, light shafts, dust, background life, clutter).
import * as THREE from 'three';
import * as TX from './tex.js';
import * as P from './props.js';
import { mat, cyl, box, makeCharacter, POSES } from './chars.js';
import { SURV, OFFICE } from './world.js';
import { rng, hash } from './util.js';

// additive light shaft: bright near the source, fading down and at grazing edges
export function lightCone(radiusTop, radiusBottom, height, color = '#ffd9a0', intensity = 0.16) {
  const geo = new THREE.CylinderGeometry(radiusTop, radiusBottom, height, 32, 8, true);
  geo.translate(0, -height / 2, 0);
  const m = new THREE.ShaderMaterial({
    uniforms: { uColor: { value: new THREE.Color(color) }, uI: { value: intensity }, uH: { value: height } },
    vertexShader: `varying float vY; varying vec3 vN; varying vec3 vV;
      uniform float uH;
      void main(){ vY = -position.y / uH; vec4 wp = modelMatrix * vec4(position,1.0);
        vN = normalize(mat3(modelMatrix) * normal); vV = normalize(cameraPosition - wp.xyz);
        gl_Position = projectionMatrix * viewMatrix * wp; }`,
    fragmentShader: `varying float vY; varying vec3 vN; varying vec3 vV; uniform vec3 uColor; uniform float uI;
      void main(){ float edge = pow(abs(dot(normalize(vN), normalize(vV))), 1.6);
        float fall = pow(1.0 - clamp(vY,0.0,1.0), 1.7);
        gl_FragColor = vec4(uColor * uI * edge * fall, 1.0); }`,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
  });
  const mesh = new THREE.Mesh(geo, m);
  mesh.renderOrder = 10;
  mesh.castShadow = false;
  mesh.receiveShadow = false;
  return mesh;
}

function dust(n, w, h, d, seed = 3) {
  const r = rng(seed);
  const pos = new Float32Array(n * 3);
  const base = [];
  for (let i = 0; i < n; i++) {
    base.push([(r() - 0.5) * w, r() * h, (r() - 0.5) * d, r() * 100]);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const [c, cg] = TX.canvas(32, 32);
  const grd = cg.createRadialGradient(16, 16, 0, 16, 16, 16);
  grd.addColorStop(0, 'rgba(255,240,210,1)'); grd.addColorStop(1, 'rgba(255,240,210,0)');
  cg.fillStyle = grd; cg.fillRect(0, 0, 32, 32);
  const m = new THREE.PointsMaterial({ size: 0.012, map: TX.toTex(c), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: 0.55, sizeAttenuation: true });
  const pts = new THREE.Points(g, m);
  pts.userData.update = (t) => {
    for (let i = 0; i < n; i++) {
      const [x, y, z, ph] = base[i];
      pos[i * 3] = x + Math.sin(t * 0.21 + ph) * 0.08;
      pos[i * 3 + 1] = y + Math.sin(t * 0.13 + ph * 1.7) * 0.06;
      pos[i * 3 + 2] = z + Math.cos(t * 0.17 + ph) * 0.08;
    }
    g.attributes.position.needsUpdate = true;
  };
  return pts;
}

function wineGlass() {
  const pts = [];
  const prof = [[0, 0], [0.032, 0], [0.033, 0.004], [0.005, 0.01], [0.004, 0.09], [0.012, 0.1], [0.034, 0.125], [0.038, 0.16], [0.036, 0.19]];
  for (const [x, y] of prof) pts.push(new THREE.Vector2(x, y));
  const g = new THREE.LatheGeometry(pts, 14);
  return new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: '#dfe8f0', roughness: 0.05, metalness: 0.1, transparent: true, opacity: 0.45 }));
}

function stool() {
  const g = new THREE.Group();
  const seat = new THREE.Mesh(cyl(0.2, 0.18, 0.08, 14), mat('#5a1a14', { rough: 0.5 }));
  seat.position.y = 0.78;
  g.add(seat);
  const pole = new THREE.Mesh(cyl(0.025, 0.025, 0.74, 8), new THREE.MeshStandardMaterial({ color: '#b8b8c0', metalness: 0.9, roughness: 0.25 }));
  pole.position.y = 0.38;
  g.add(pole);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.15, 0.012, 6, 16), pole.material);
  ring.rotation.x = Math.PI / 2;
  ring.position.y = 0.3;
  g.add(ring);
  const base = new THREE.Mesh(cyl(0.18, 0.2, 0.03, 14), pole.material);
  base.position.y = 0.015;
  g.add(base);
  return g;
}

function officeChair(col = '#1a1a1e') {
  const g = new THREE.Group();
  const m = mat(col, { rough: 0.6 });
  const seat = new THREE.Mesh(box(0.5, 0.08, 0.48), m);
  seat.position.y = 0.48;
  g.add(seat);
  const back = new THREE.Mesh(box(0.46, 0.62, 0.07), m);
  back.position.set(0, 0.85, -0.22);
  back.rotation.x = -0.12;
  g.add(back);
  const pole = new THREE.Mesh(cyl(0.03, 0.03, 0.4, 8), mat('#555', { metal: 0.6, rough: 0.3 }));
  pole.position.y = 0.25;
  g.add(pole);
  for (let i = 0; i < 5; i++) {
    const leg = new THREE.Mesh(box(0.04, 0.03, 0.3), pole.material);
    leg.position.set(Math.sin((i / 5) * Math.PI * 2) * 0.15, 0.05, Math.cos((i / 5) * Math.PI * 2) * 0.15);
    leg.rotation.y = (i / 5) * Math.PI * 2;
    g.add(leg);
  }
  return g;
}

function mug(col) {
  const g = new THREE.Group();
  const m = mat(col, { rough: 0.4 });
  const body = new THREE.Mesh(cyl(0.04, 0.036, 0.1, 12), m);
  body.position.y = 0.05;
  g.add(body);
  const h = new THREE.Mesh(new THREE.TorusGeometry(0.025, 0.007, 6, 10, Math.PI), m);
  h.position.set(0.045, 0.05, 0);
  h.rotation.z = -Math.PI / 2;
  g.add(h);
  return g;
}

export function addDetails(W, scene) {
  const casino = W.sets.casino;
  const upd = [];
  // ------------------------------------------------------------ architecture
  const panelMat = new THREE.MeshStandardMaterial({ color: '#0a1230', roughness: 0.6 });
  const moldMat = new THREE.MeshStandardMaterial({ color: '#c8a050', metalness: 0.7, roughness: 0.35, emissive: '#1a1004' });
  const walls = [[0, -4.18, 0, 20], [8.98, 2, -Math.PI / 2, 20], [-8.98, 2, Math.PI / 2, 20], [0, 8.98, Math.PI, 20]];
  for (const [x, z, ry, len] of walls) {
    const g = new THREE.Group();
    g.position.set(x, 0, z);
    g.rotation.y = ry;
    const wain = new THREE.Mesh(box(len, 0.95, 0.04), panelMat);
    wain.position.set(0, 0.475, 0.02);
    g.add(wain);
    for (let i = -len / 2 + 0.6; i < len / 2; i += 1.2) {
      const pnl = new THREE.Mesh(box(0.95, 0.62, 0.02), panelMat);
      pnl.position.set(i, 0.48, 0.05);
      g.add(pnl);
      const sconceZ = new THREE.Group();
      if (Math.round((i + len / 2) / 1.2) % 4 === 1) {
        const plate = new THREE.Mesh(box(0.12, 0.22, 0.03), moldMat);
        plate.position.set(i, 2.25, 0.03);
        g.add(plate);
        const shade = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.1, 0.16, 10, 1, true), new THREE.MeshBasicMaterial({ color: new THREE.Color(1.7, 1.3, 0.8), side: THREE.DoubleSide }));
        shade.position.set(i, 2.4, 0.13);
        g.add(shade);
        const glow = lightCone(0.1, 0.5, 1.2, '#ffcc88', 0.07);
        glow.rotation.x = Math.PI;
        glow.position.set(i, 2.48, 0.13);
        g.add(glow);
      }
    }
    const rail = new THREE.Mesh(box(len, 0.05, 0.07), moldMat);
    rail.position.set(0, 0.97, 0.05);
    g.add(rail);
    const base = new THREE.Mesh(box(len, 0.12, 0.06), mat('#1a0e08'));
    base.position.set(0, 0.06, 0.05);
    g.add(base);
    const crown = new THREE.Mesh(box(len, 0.14, 0.12), moldMat);
    crown.position.set(0, 4.32, 0.06);
    crown.userData.ceiling = true;
    g.add(crown);
    casino.add(g);
  }
  // pilasters along the back wall
  for (const x of [-6.6, -3.9, -1.55, 4.4, 7.2]) {
    const col = new THREE.Group();
    const shaft = new THREE.Mesh(box(0.36, 4.0, 0.2), mat('#14204a', { rough: 0.5 }));
    shaft.position.y = 2.1;
    col.add(shaft);
    for (const y of [0.12, 4.15]) {
      const cap = new THREE.Mesh(box(0.46, 0.18, 0.26), moldMat);
      cap.position.y = y;
      col.add(cap);
    }
    for (let k = -1; k <= 1; k++) {
      const flute = new THREE.Mesh(box(0.04, 3.6, 0.02), mat('#0a1230'));
      flute.position.set(k * 0.1, 2.1, 0.105);
      col.add(flute);
    }
    col.position.set(x, 0, -4.08);
    casino.add(col);
  }
  // coffered ceiling with recessed downlights
  const ceilingGrp = new THREE.Group();
  casino.add(ceilingGrp);
  W.props.ceiling = ceilingGrp;
  const coffer = mat('#0a0c14', { rough: 0.9 });
  for (let x = -8; x <= 8; x += 2) {
    const beam = new THREE.Mesh(box(0.14, 0.22, 18), coffer);
    beam.position.set(x, 4.29, 2.4);
    ceilingGrp.add(beam);
  }
  for (let z = -4; z <= 9; z += 2) {
    const beam = new THREE.Mesh(box(18, 0.22, 0.14), coffer);
    beam.position.set(0, 4.29, z);
    ceilingGrp.add(beam);
  }
  const dlMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(1.8, 1.6, 1.3) });
  for (let x = -7; x <= 7; x += 2) for (let z = -3; z <= 8; z += 2) {
    if (Math.abs(x) < 1.5 && z > -2 && z < 2) continue;
    const dl = new THREE.Mesh(new THREE.CircleGeometry(0.07, 12), dlMat);
    dl.rotation.x = Math.PI / 2;
    dl.position.set(x, 4.385, z);
    ceilingGrp.add(dl);
  }
  // ------------------------------------------------------------- chandeliers
  const crystal = new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 0.05, metalness: 0.2, emissive: '#6a5a40', transparent: true, opacity: 0.9 });
  W.props.chandeliers.forEach((ch, ci) => {
    const s = ch.scale.x;
    const r = rng(ci + 40);
    const ring = ch.children.find((c) => c.geometry && c.geometry.type === 'TorusGeometry');
    const nDrops = 22;
    for (let i = 0; i < nDrops; i++) {
      const a = (i / nDrops) * Math.PI * 2;
      const rad = (0.38 + (i % 2) * 0.05);
      const drop = new THREE.Mesh(new THREE.OctahedronGeometry(0.013, 0), crystal);
      drop.scale.y = 2.2;
      drop.position.set(Math.cos(a) * rad, -0.14 - r() * 0.06 - (i % 2) * 0.04, Math.sin(a) * rad);
      ch.add(drop);
    }
    const cone = lightCone(0.35, 1.6, 2.6, '#ffd9a8', 0.075);
    cone.position.y = -0.1;
    ch.add(cone);
  });
  // spot shaft over the hero table
  const tableShaft = lightCone(0.18, 1.55, 3.4, '#ffe6c0', 0.06);
  tableShaft.position.set(0.1, 4.0, -0.2);
  casino.add(tableShaft);
  W.props.tableShaft = tableShaft;
  const motes = dust(900, 6, 3.4, 8, 5);
  motes.position.set(0, 0.6, 0.5);
  casino.add(motes);
  upd.push((t) => motes.userData.update(t));
  // ---------------------------------------------------------------- the table
  const T = P.TABLE;
  const tray = new THREE.Group();
  const trayBody = new THREE.Mesh(box(0.62, 0.05, 0.16), mat('#1a1a1e', { rough: 0.5 }));
  tray.add(trayBody);
  const cols = ['#c41e1e', '#2a4fb0', '#1a1a1a', '#2a8a3a', '#e0c040', '#c41e1e', '#2a4fb0', '#f0f0f0'];
  for (let i = 0; i < 8; i++) {
    const rowStack = new THREE.Mesh(new THREE.CylinderGeometry(0.031, 0.031, 0.13, 12), new THREE.MeshStandardMaterial({ color: cols[i], roughness: 0.4 }));
    rowStack.rotation.x = Math.PI / 2;
    rowStack.position.set(-0.27 + i * 0.077, 0.03, 0);
    tray.add(rowStack);
  }
  tray.position.set(0.42, T.H + 0.02, -1.42);
  casino.add(tray);
  // table limits placard
  const [lc, lg] = TX.canvas(256, 160);
  lg.fillStyle = '#101010'; lg.fillRect(0, 0, 256, 160);
  lg.strokeStyle = '#c8a050'; lg.lineWidth = 6; lg.strokeRect(6, 6, 244, 148);
  lg.fillStyle = '#e8d090'; lg.textAlign = 'center';
  lg.font = 'bold 30px "Liberation Serif"'; lg.fillText('ROULETTE', 128, 52);
  lg.font = '24px "Liberation Sans"'; lg.fillText('MIN $10', 128, 92); lg.fillText('MAX $5,000', 128, 126);
  const placard = new THREE.Mesh(new THREE.PlaneGeometry(0.2, 0.125), new THREE.MeshBasicMaterial({ map: TX.toTex(lc), color: new THREE.Color(1.3, 1.3, 1.3) }));
  placard.position.set(-0.45, T.H + 0.08, -1.45);
  placard.rotation.x = -0.3;
  casino.add(placard);
  const stand = new THREE.Mesh(box(0.21, 0.135, 0.02), mat('#c8a050', { metal: 0.7, rough: 0.3 }));
  stand.position.set(-0.45, T.H + 0.078, -1.462);
  stand.rotation.x = -0.3;
  casino.add(stand);
  // drink cup holders on the rail
  for (const [x, z] of [[-0.78, 0.6], [0.78, 0.1], [-0.78, -0.3], [0.78, 0.9]]) {
    const h = new THREE.Mesh(cyl(0.045, 0.04, 0.03, 12, 1, true), new THREE.MeshStandardMaterial({ color: '#c0c0c8', metalness: 0.9, roughness: 0.25, side: THREE.DoubleSide }));
    h.position.set(x, T.H + 0.06, z);
    casino.add(h);
  }
  // wheel diamonds (ball deflectors) on the track
  const wh = W.props.wheel.group;
  const dm = new THREE.MeshStandardMaterial({ color: '#d8c890', metalness: 0.85, roughness: 0.25 });
  for (let i = 0; i < 8; i++) {
    const a = (i / 8) * Math.PI * 2;
    const d = new THREE.Mesh(new THREE.OctahedronGeometry(0.012, 0), dm);
    d.scale.set(1.0, 0.5, 2.0);
    d.position.set(Math.sin(a) * P.TABLE.wheel.r * 1.04, 0.083, Math.cos(a) * P.TABLE.wheel.r * 1.04);
    d.rotation.y = a;
    wh.add(d);
  }
  // ------------------------------------------------------- background life
  const r = rng(77);
  const bgPeople = [];
  W.props.bgTables.forEach((tb, ti) => {
    const seats = [[-0.98, 0.3, Math.PI / 2], [0.98, -0.2, -Math.PI / 2], [-0.98, -0.5, Math.PI / 2], [0.0, 2.05, Math.PI]];
    seats.forEach(([x, z, ry], si) => {
      if (hash(ti, si) < 0.35) return;
      const c = makeCharacter({
        name: `bg${ti}_${si}`, scale: 0.95 + r() * 0.08, seed: 400 + ti * 10 + si,
        clothes: { kind: ['tee', 'shirt', 'hoodie', 'suit'][si % 4], top: ['#3a5a8a', '#8a3a3a', '#d8d8d8', '#2a2a2a', '#5a7a3a'][(ti + si) % 5], sleeve: null, pants: '#22262e', under: '#151515' },
        face: { skin: ['#e8c0a0', '#c8946a', '#8a5a3a', '#f0d0b8'][(ti + si) % 4], hair: ['#1a1410', '#5a3a1a', '#c8a060', '#8a8a86'][(ti * 3 + si) % 4], hairStyle: ['short', 'buzz', 'slick', 'bald'][(ti + si * 2) % 4], seed: 400 + ti * 10 + si },
      });
      c.clothes = null;
      const chair = P.makeChair();
      const grp = new THREE.Group();
      grp.add(c.root);
      c.root.position.set(x, 0, z);
      c.root.rotation.y = ry;
      c.setPose(POSES.sitTable);
      chair.position.set(x * 1.0, 0, z);
      chair.rotation.y = ry + Math.PI;
      grp.add(chair);
      tb.add(grp);
      bgPeople.push(c);
    });
    const dealer = makeCharacter({ name: `bgdealer${ti}`, outfit: 'dealer', seed: 500 + ti, cuffs: true,
      face: { skin: ['#e8c0a0', '#d8a882', '#f0d0b8'][ti % 3], hair: '#1a1410', hairStyle: ti % 2 ? 'short' : 'bun', female: ti % 2 === 0, seed: 500 + ti } });
    dealer.root.position.set(0.02, 0, -1.78);
    dealer.setPose(POSES.dealer);
    tb.add(dealer.root);
    bgPeople.push(dealer);
    const pile = P.chipPile([{ x: 0, z: 0, n: 6 + ti }, { x: 0.08, z: 0.03, n: 4, color: P.REDC }], 60 + ti);
    pile.position.set(-0.2, P.TABLE.H, 0.3);
    tb.add(pile);
  });
  upd.push((t) => bgPeople.forEach((c) => { if (c.root.parent && c.root.parent.visible !== false) { c.setPose(c.name && c.name.startsWith('bgdealer') ? POSES.dealer : POSES.sitTable); c.idle(t); } }));
  // bar: stools, glasses, bartender
  const bar = W.props.bar;
  for (let i = 0; i < 7; i++) {
    const st = stool();
    st.position.set(-2.1 + i * 0.7, 0, 0.75);
    bar.add(st);
  }
  for (let i = 0; i < 9; i++) {
    const wg = wineGlass();
    wg.position.set(-2.2 + i * 0.52 + (i % 2) * 0.1, 1.15, 0.18 - (i % 3) * 0.08);
    bar.add(wg);
  }
  const bartender = makeCharacter({ name: 'bartender', outfit: 'dealer', seed: 610, cuffs: true,
    clothes: { kind: 'vest', top: '#1a1a1a', sleeve: '#f2f0ea', pants: '#111', shoes: '#000', bowtie: '#101010' },
    face: { skin: '#d8a882', hair: '#2a1a10', hairStyle: 'slick', seed: 610, smile: 0.3 } });
  bartender.root.position.set(0.8, 0, -0.55);
  bartender.root.rotation.y = 0;
  bartender.setPose({ ...POSES.dealer, rShoulder: [-0.6, 0, -0.3], rElbow: [-1.4, 0, 0] });
  bar.add(bartender.root);
  upd.push((t) => { bartender.setPose({ ...POSES.dealer, rShoulder: [-0.6 + Math.sin(t * 2) * 0.1, 0, -0.3], rElbow: [-1.4, 0, 0] }); bartender.idle(t); });
  // stools in front of the slot bank, slot top lights chase
  W.props.slots.forEach((sm, i) => {
    const st = stool();
    st.position.set(0, 0, 0.75);
    st.scale.setScalar(0.85);
    sm.add(st);
    const bulbs = [];
    for (let k = 0; k < 6; k++) {
      const b = new THREE.Mesh(new THREE.SphereGeometry(0.018, 6, 4), new THREE.MeshBasicMaterial({ color: new THREE.Color(2.5, 1.8, 0.6) }));
      b.position.set(-0.3 + k * 0.12, 1.88, 0.24);
      sm.add(b);
      bulbs.push(b);
    }
    upd.push((t) => bulbs.forEach((b, k) => { const on = (Math.floor(t * 8) + k + i) % 3 === 0; b.material.color.setRGB(on ? 3.0 : 0.5, on ? 2.2 : 0.35, on ? 0.7 : 0.1); }));
  });
  // more palms
  for (const [x, z, sd] of [[8.3, -3.5, 7], [-8.3, -3.4, 8], [8.3, 8.3, 9], [2.9, 8.4, 10]]) {
    const pl = P.makePlant(sd, 1.15);
    pl.position.set(x, 0, z);
    casino.add(pl);
  }
  // ------------------------------------------------------- surveillance room
  const surv = W.sets.surv;
  const deskTop = 0.79;
  const clutter = [
    () => { const m = mug('#c03a2a'); m.position.set(-1.0, deskTop, -1.25); return m; },
    () => { const m = mug('#f0f0f0'); m.position.set(1.15, deskTop, -1.3); return m; },
    () => { const ph = P.makePhone(); ph.rotation.z = Math.PI / 2; ph.position.set(2.2, deskTop + 0.03, -1.45); return ph; },
  ];
  clutter.forEach((f) => surv.add(f()));
  for (const x of [-2.4, -0.8, 0.9, 2.6]) {
    const bind = new THREE.Mesh(box(0.06, 0.3, 0.24), mat(['#1a3a8a', '#8a1a1a', '#1a6a3a', '#3a3a3a'][Math.abs(Math.round(x)) % 4], { rough: 0.6 }));
    bind.position.set(x, deskTop + 0.15, -1.95);
    surv.add(bind);
  }
  for (const x of [-1.2, 0.5, 2.0]) {
    const joy = new THREE.Group();
    const base = new THREE.Mesh(box(0.16, 0.04, 0.12), mat('#202024'));
    const stick = new THREE.Mesh(cyl(0.008, 0.008, 0.09, 6), mat('#101010'));
    stick.position.y = 0.06;
    const knob = new THREE.Mesh(new THREE.SphereGeometry(0.02, 8, 6), mat('#c01010'));
    knob.position.y = 0.11;
    joy.add(base, stick, knob);
    joy.position.set(x, deskTop + 0.02, -1.35);
    surv.add(joy);
  }
  const lampArm = new THREE.Group();
  const lb = new THREE.Mesh(cyl(0.07, 0.08, 0.03, 12), mat('#1a1a1a'));
  const la = new THREE.Mesh(cyl(0.01, 0.01, 0.4, 6), mat('#2a2a2a'));
  la.position.set(0, 0.2, 0);
  la.rotation.z = 0.4;
  const lh = new THREE.Mesh(new THREE.ConeGeometry(0.07, 0.12, 12, 1, true), new THREE.MeshStandardMaterial({ color: '#1a1a1a', side: THREE.DoubleSide }));
  lh.position.set(-0.16, 0.38, 0);
  lh.rotation.z = 2.4;
  lampArm.add(lb, la, lh);
  lampArm.position.set(-2.8, deskTop, -1.5);
  surv.add(lampArm);
  // ceiling cable trays + racks behind
  for (let i = 0; i < 3; i++) {
    const rack = new THREE.Mesh(box(0.6, 2.0, 0.6), mat('#16181c', { rough: 0.5 }));
    rack.position.set(3.6, 1.0, 0.6 + i * 0.7);
    surv.add(rack);
    for (let k = 0; k < 8; k++) {
      const led = new THREE.Mesh(box(0.02, 0.02, 0.01), new THREE.MeshBasicMaterial({ color: k % 3 ? new THREE.Color(0.2, 2.0, 0.4) : new THREE.Color(2.5, 0.6, 0.1) }));
      led.position.set(3.29, 0.5 + k * 0.18, 0.5 + i * 0.7);
      surv.add(led);
    }
  }
  const survMotes = dust(500, 6, 2.6, 4, 9);
  survMotes.position.set(0, 0.5, -0.5);
  surv.add(survMotes);
  upd.push((t) => survMotes.userData.update(t));
  for (const lamp of W.props.survLamps) {
    const c2 = lightCone(0.16, 0.9, 2.4, '#cfe0ff', 0.05);
    c2.position.copy(lamp.position);
    surv.add(c2);
  }
  // --------------------------------------------------------------- office
  const office = W.sets.office;
  const shelf = new THREE.Group();
  const frame = new THREE.Mesh(box(1.4, 2.2, 0.35), mat('#3a1a08', { rough: 0.5 }));
  shelf.add(frame);
  for (let k = 0; k < 4; k++) {
    for (let b = 0; b < 12; b++) {
      const bk = new THREE.Mesh(box(0.06 + hash(k, b) * 0.04, 0.3 + hash(b, k) * 0.08, 0.24), mat(['#6a1a10', '#1a3a5a', '#2a4a2a', '#8a6a3a', '#3a2a4a'][(k + b) % 5], { rough: 0.7 }));
      bk.position.set(-0.6 + b * 0.105, -0.85 + k * 0.52, 0.06);
      shelf.add(bk);
    }
  }
  shelf.position.set(-1.6, 1.1, -1.4);
  office.add(shelf);
  const papers = new THREE.Mesh(box(0.32, 0.015, 0.42), mat('#f0f0ea'));
  papers.position.set(0.5, 0.83, 0.4);
  papers.rotation.y = -0.2;
  office.add(papers);
  const penCup = new THREE.Mesh(cyl(0.04, 0.04, 0.11, 10), mat('#2a2a2a', { metal: 0.4 }));
  penCup.position.set(-0.6, 0.875, 0.5);
  office.add(penCup);
  for (let k = 0; k < 3; k++) {
    const pen = new THREE.Mesh(cyl(0.005, 0.005, 0.16, 6), mat(['#1a1a8a', '#000', '#8a1a1a'][k]));
    pen.position.set(-0.6 + (k - 1) * 0.015, 0.93, 0.5);
    pen.rotation.z = (k - 1) * 0.2;
    office.add(pen);
  }
  const phoneBase = new THREE.Mesh(box(0.2, 0.06, 0.22), mat('#141416', { rough: 0.4 }));
  phoneBase.position.set(0.55, 0.85, 0.15);
  office.add(phoneBase);
  const deskLamp = new THREE.Group();
  const dlBase = new THREE.Mesh(cyl(0.08, 0.09, 0.03, 12), new THREE.MeshStandardMaterial({ color: '#b08a40', metalness: 0.8, roughness: 0.3 }));
  const dlPole = new THREE.Mesh(cyl(0.012, 0.012, 0.42, 8), dlBase.material);
  dlPole.position.y = 0.21;
  const dlShade = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.13, 0.15, 14, 1, true), new THREE.MeshStandardMaterial({ color: '#1a5a2a', emissive: '#203a10', side: THREE.DoubleSide }));
  dlShade.position.y = 0.42;
  deskLamp.add(dlBase, dlPole, dlShade);
  deskLamp.position.set(-0.75, 0.82, 0.2);
  office.add(deskLamp);
  return { update: (t) => upd.forEach((f) => f(t)) };
}
