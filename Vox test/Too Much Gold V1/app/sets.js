// The film's locations. Each builder returns { group, apply(t, shot), grade }.
//   market : a Cairo street of shops (gold / morning / day light)
//   desert : dunes, the pyramids, the Nile and Cairo on the horizon (sunrise / sunset)
//   void   : a dark showroom with one coin on a pedestal
//   camp   : the caravan's night camp
import * as THREE from 'three';
import { toon, gold, mk, fxLayer, LAYER } from './toon.js';
import { skyDome } from './world.js';
import * as TX from './stex.js';
import * as PR from './props.js';
import { makeCamel, makeCat } from './animals.js';
import { hash, clamp, lerp } from './util.js';

export const ORDER = ['test', 'market', 'desert', 'void', 'camp'];
export const BUILD = {};
const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);

function sunLight(group, color, intensity, size = 30, res = 4096) {
  const l = new THREE.DirectionalLight(color, intensity);
  l.castShadow = true;
  l.shadow.mapSize.set(res, res);
  const c = l.shadow.camera; c.left = -size; c.right = size; c.top = size; c.bottom = -size; c.near = 1; c.far = 500;
  l.shadow.bias = -0.0005; l.shadow.normalBias = 0.03; l.shadow.radius = 4;
  group.add(l, l.target);
  return l;
}
// box whose UVs are scaled by its size so textures tile at a constant density (tile = metres per texture)
function boxGeo(w, h, d, tile = 2) {
  const g = new THREE.BoxGeometry(w, h, d);
  const uv = g.getAttribute('uv');
  const dims = [[d, h], [d, h], [w, d], [w, d], [w, h], [w, h]];
  for (let f = 0; f < 6; f++) for (let k = 0; k < 4; k++) {
    const i = f * 4 + k;
    uv.setXY(i, uv.getX(i) * dims[f][0] / tile, uv.getY(i) * dims[f][1] / tile);
  }
  return g;
}
function shaft(parent, from, to, w, op, col = '#ffe2b0') {
  const len = from.distanceTo(to);
  const tex = TX.gradientTex([[0, 'rgba(255,255,255,0)'], [0.08, 'rgba(255,255,255,1)'], [0.6, 'rgba(255,255,255,0.45)'], [1, 'rgba(255,255,255,0)']]);
  const side = TX.gradientTex([[0, 'rgba(255,255,255,0)'], [0.5, 'rgba(255,255,255,1)'], [1, 'rgba(255,255,255,0)']], 4, 128, false);
  const mat = new THREE.ShaderMaterial({
    uniforms: { t1: { value: tex }, t2: { value: side }, col: { value: new THREE.Color(col) }, op: { value: op } },
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: 'uniform sampler2D t1, t2; uniform vec3 col; uniform float op; varying vec2 vUv; void main(){ float a = texture2D(t1, vec2(0.5, 1.0 - vUv.y)).a * texture2D(t2, vec2(vUv.x, 0.5)).a; gl_FragColor = vec4(col * a * op, 1.0); }',
    transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide,
  });
  const grp = new THREE.Group();
  for (const r of [0, Math.PI / 2]) {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, len), mat);
    m.rotation.y = r; m.position.y = -len / 2; grp.add(m);
  }
  grp.position.copy(from);
  grp.quaternion.setFromUnitVectors(V(0, -1, 0), to.clone().sub(from).normalize());
  fxLayer(grp);
  parent.add(grp);
  grp.userData.mat = mat;
  return grp;
}
// drifting dust motes (deterministic in time)
function dust(parent, box, n, col = '#fff0d0', size = 0.04, seed = 3) {
  const geo = new THREE.BufferGeometry();
  const base = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    base[i * 3] = lerp(box[0], box[1], hash(seed, i)); base[i * 3 + 1] = lerp(box[2], box[3], hash(seed, i + 0.3)); base[i * 3 + 2] = lerp(box[4], box[5], hash(seed, i + 0.6));
  }
  geo.setAttribute('position', new THREE.BufferAttribute(base.slice(), 3));
  const [c, g] = (() => { const cv = document.createElement('canvas'); cv.width = cv.height = 64; return [cv, cv.getContext('2d')]; })();
  const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.4, 'rgba(255,255,255,0.4)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  const tex = new THREE.CanvasTexture(c);
  const mat = new THREE.PointsMaterial({ color: col, size, map: tex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: 0.7, sizeAttenuation: true });
  const pts = new THREE.Points(geo, mat);
  pts.frustumCulled = false;
  fxLayer(pts);
  parent.add(pts);
  pts.userData.tick = (t) => {
    const p = geo.getAttribute('position');
    for (let i = 0; i < n; i++) {
      p.setXYZ(i, base[i * 3] + Math.sin(t * 0.3 + i) * 0.25 + t * 0.05, base[i * 3 + 1] + Math.sin(t * 0.5 + i * 1.7) * 0.15, base[i * 3 + 2] + Math.cos(t * 0.4 + i * 0.7) * 0.25);
    }
    p.needsUpdate = true;
  };
  return pts;
}

// ======================================================================= test
BUILD.test = (scene) => {
  const g = new THREE.Group(); g.position.set(-600, 0, 0); scene.add(g);
  mk(new THREE.PlaneGeometry(60, 60).rotateX(-Math.PI / 2), toon('#e0b98a'), g, { cast: false });
  skyDome(g, { top: '#3a6ec8', mid: '#8ab4e8', horizon: '#f6d6b0', sunDir: [0.4, 0.5, -0.6] });
  const s = sunLight(g, '#fff0d8', 2.1, 8, 2048); s.position.set(-588, 18, 10); s.target.position.set(-600, 0, 0);
  g.add(new THREE.HemisphereLight('#bcd4ff', '#c09060', 0.7));
  return { group: g, origin: V(-600, 0, 0), apply: () => { scene.fog = null; scene.environmentIntensity = 0.35; }, grade: { bloomThr: 1.0, bloom: 0.32, contrast: 1.1 } };
};


// puffy cartoon clouds: clusters of soft white balls, no outlines (they live on the FX layer)
function clouds(parent, list, color = '#ffffff', lift = 0.45) {
  const mat = toon(color, { lift, rough: 1 });
  mat.fog = false;
  const out = [];
  list.forEach(([x, y, z, s, seed]) => {
    const c = new THREE.Group(); c.position.set(x, y, z);
    const n = 5 + Math.floor(hash(seed, 1) * 3);
    for (let i = 0; i < n; i++) {
      const px = (i / (n - 1) - 0.5) * 2.4 * s, r = s * (0.55 + 0.45 * Math.sin((i / (n - 1)) * Math.PI)) * (0.8 + 0.3 * hash(seed, i));
      const m = new THREE.Mesh(new THREE.SphereGeometry(r, 20, 14), mat);
      m.position.set(px, r * 0.35 + hash(seed, i + 9) * s * 0.15, (hash(seed, i + 3) - 0.5) * s * 0.4); m.scale.set(1, 0.82, 0.55); c.add(m);
    }
    const base = new THREE.Mesh(new THREE.SphereGeometry(s * 1.5, 20, 12), mat); base.scale.set(1.0, 0.3, 0.4); base.position.y = s * 0.05; c.add(base);
    fxLayer(c); parent.add(c); out.push(c);
  });
  return out;
}
// a big glowing moon disc with a soft halo
function moonDisc(parent, pos, r) {
  const g = new THREE.Group(); g.position.copy(pos);
  const [c, x] = (() => { const cv = document.createElement('canvas'); cv.width = cv.height = 256; return [cv, cv.getContext('2d')]; })();
  x.fillStyle = '#f4f2ea'; x.beginPath(); x.arc(128, 128, 120, 0, Math.PI * 2); x.fill();
  x.fillStyle = 'rgba(190,196,214,0.55)'; for (const [a, b, rr] of [[90, 100, 22], [160, 150, 16], [120, 175, 12], [170, 85, 10]]) { x.beginPath(); x.arc(a, b, rr, 0, Math.PI * 2); x.fill(); }
  const disc = new THREE.Mesh(new THREE.CircleGeometry(r, 48), new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(c), color: new THREE.Color(1.15, 1.15, 1.2), fog: false, transparent: true }));
  g.add(disc);
  const hc = document.createElement('canvas'); hc.width = hc.height = 256; const hx = hc.getContext('2d');
  const gr = hx.createRadialGradient(128, 128, 0, 128, 128, 128);
  gr.addColorStop(0, 'rgba(255,255,255,0.35)'); gr.addColorStop(0.3, 'rgba(255,255,255,0.12)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  hx.fillStyle = gr; hx.fillRect(0, 0, 256, 256);
  const halo = new THREE.Mesh(new THREE.PlaneGeometry(r * 7, r * 7), new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(hc), color: '#9ab0ff', transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false }));
  halo.position.z = -0.5; g.add(halo);
  fxLayer(g); parent.add(g);
  return g;
}
// a mud-brick desert fortress with towers, crenellations, a gate and lit windows
function fortress(parent, pos, rotY = 0) {
  const g = new THREE.Group(); g.position.copy(pos); g.rotation.y = rotY; parent.add(g);
  const wall = toon('#ffffff', { map: TX.plaster('#c49a86', [1, 1], 21) }), dark = toon('#2a1a20');
  const lit = new THREE.MeshStandardMaterial({ color: '#ffcf7a', emissive: '#ffb04a', emissiveIntensity: 2.2 });
  mk(boxGeo(26, 7, 2, 3), wall, g, { pos: [0, 3.5, 0], outline: 5 });
  for (let x = -12.5; x <= 12.6; x += 1.6) mk(boxGeo(0.8, 0.9, 2.1, 1), wall, g, { pos: [x, 7.45, 0], outline: 4 });
  for (const [x, h, r] of [[-13, 11, 2.2], [13, 12, 2.4], [-4.5, 9.5, 1.8], [5, 10, 1.9]]) {
    mk(new THREE.CylinderGeometry(r * 0.9, r, h, 16), wall, g, { pos: [x, h / 2, 0.4], outline: 5 });
    for (let i = 0; i < 10; i++) { const a = i / 10 * Math.PI * 2; mk(boxGeo(0.7, 0.9, 0.7, 1), wall, g, { pos: [x + Math.cos(a) * r * 0.85, h + 0.45, 0.4 + Math.sin(a) * r * 0.85], rot: [0, -a, 0], outline: 3.5 }); }
    for (const y of [h * 0.45, h * 0.75]) mk(boxGeo(0.45, 0.8, 0.1, 1), lit, g, { pos: [x, y, 0.4 + r * 0.98], outline: 2.5 });
    const fl = mk(new THREE.PlaneGeometry(1.4, 0.8), toon('#c0282e', { side: THREE.DoubleSide, lift: 0.2 }), g, { pos: [x + 0.7, h + 2.2, 0.4], outline: 2 });
    mk(new THREE.CylinderGeometry(0.06, 0.06, 2.6, 6), dark, g, { pos: [x, h + 1.6, 0.4], outline: 2 });
  }
  mk(boxGeo(3.2, 4.2, 0.3, 1), dark, g, { pos: [0, 2.1, 1.05], outline: 4 });
  mk(new THREE.TorusGeometry(1.75, 0.35, 8, 20, Math.PI), wall, g, { pos: [0, 4.1, 1.1], outline: 4 });
  for (const x of [-8, -6.5, 7.5, 9]) mk(boxGeo(0.5, 0.9, 0.1, 1), lit, g, { pos: [x, 4.6, 1.02], outline: 2.5 });
  for (const x of [-2.2, 2.2]) { const pl = new THREE.PointLight('#ff9a40', 6, 9, 1.8); pl.position.set(x, 4.5, 2.2); g.add(pl); mk(new THREE.SphereGeometry(0.22, 10, 8), lit, g, { pos: [x, 4.5, 1.4], outline: 2 }); }
  return g;
}

// ======================================================================= market
export const MK = { half: 3.6, near: 9, far: -46 };
BUILD.market = (scene, W) => {
  const g = new THREE.Group(); scene.add(g);
  const A = (W.anchors.market = {});
  const H = MK.half;
  // ground: flagstones with a dusty centre
  mk(new THREE.PlaneGeometry(24, 90).rotateX(-Math.PI / 2), toon('#ffffff', { map: TX.flagstones('#d0ae7e', [5, 18]) }), g, { pos: [0, 0, -18], cast: false, outline: false });
  const walls = {
    a: toon('#ffffff', { map: TX.ablaq('#f2c886', '#d04a2a', [1, 1], 1) }),
    b: toon('#ffffff', { map: TX.ablaq('#eab878', '#2f5aa8', [1, 1], 2) }),
    c: toon('#ffffff', { map: TX.plaster('#7fb4cc', [1, 1], 3) }),
    d: toon('#ffffff', { map: TX.plaster('#e8956a', [1, 1], 4) }),
    e: toon('#ffffff', { map: TX.ablaq('#f6d6a0', '#b8322a', [1, 1], 5) }),
  };
  const dark = toon('#3a2214'), woodM = toon('#ffffff', { map: TX.wood('#8a5a30', [1, 1], 5) });
  const latticeM = toon('#ffffff', { map: TX.lattice('#8a5228') });
  const interior = toon('#5a3a22', { lift: 0.04 });
  const shelfM = toon('#ffffff', { map: TX.wood('#a06a38', [1, 1], 9, 2) });
  const AW = [['#c4302a', '#f2e6cc'], ['#2a5a9a', '#f2e6cc'], ['#2a7a4a', '#f2d24a'], ['#e0a020', '#f6ecd8'], ['#7a2a6a', '#f2d8a0']];

  function house(sd, z0, z1, h, wall, shop, seed) {
    const len = z0 - z1, cz = (z0 + z1) / 2, depth = 6, xf = sd * H;
    const hb = new THREE.Group(); g.add(hb);
    // upper storeys
    mk(boxGeo(depth, h - 3.0, len, 2.2), wall, hb, { pos: [xf + sd * depth / 2, 3.0 + (h - 3.0) / 2, cz], outline: 5 });
    // parapet lip and crenellations
    mk(boxGeo(depth + 0.2, 0.25, len + 0.1, 2), wall, hb, { pos: [xf + sd * depth / 2 - sd * 0.1, h + 0.12, cz], outline: 4.5 });
    for (let z = z1 + 0.35; z < z0 - 0.2; z += 0.9) mk(boxGeo(0.35, 0.4, 0.45, 1), wall, hb, { pos: [xf + sd * 0.15, h + 0.45, z], outline: 3.5 });
    // ground floor: piers at the ends, a recessed shop or a door between them
    const pier = 0.55;
    for (const z of [z0 - pier / 2, z1 + pier / 2]) mk(boxGeo(depth, 3.0, pier, 2.2), wall, hb, { pos: [xf + sd * depth / 2, 1.5, z], outline: 5 });
    const rec = shop ? 1.9 : 0.25;
    mk(boxGeo(depth - rec, 3.0, len - 2 * pier, 2.2), shop ? interior : wall, hb, { pos: [xf + sd * (rec + (depth - rec) / 2), 1.5, cz], outline: 4 });
    if (shop) {
      mk(boxGeo(rec, 0.04, len - 2 * pier, 2), shelfM, hb, { pos: [xf + sd * rec / 2, 0.02, cz], outline: false });   // floor
      for (const y of [1.3, 2.0]) mk(boxGeo(0.35, 0.05, len - 2 * pier - 0.1, 1), shelfM, hb, { pos: [xf + sd * (rec - 0.18), y, cz], outline: 3 });
      // awning
      const [c1, c2] = AW[seed % AW.length];
      const aw = mk(boxGeo(1.9, 0.035, len - 0.2, 4), toon('#ffffff', { map: TX.stripes(c1, c2, 8, false), lift: 0.1 }), hb, { pos: [xf - sd * 0.85, 2.9, cz], rot: [0, 0, sd * -0.28], outline: 4 });
      aw.material.map.wrapS = THREE.RepeatWrapping;
      for (const z of [z0 - 0.35, z1 + 0.35]) mk(new THREE.CylinderGeometry(0.035, 0.035, 2.65, 8), woodM, hb, { pos: [xf - sd * 1.72, 1.32, z], outline: 3 });
      // a lantern inside
      const lt = PR.lantern(); lt.position.set(xf + sd * 0.9, 2.5, cz); hb.add(lt);
      const pl = new THREE.PointLight('#ffb060', 1.8, 4.5, 1.8); pl.position.set(xf + sd * 0.9, 2.3, cz); hb.add(pl);
    } else {
      // arched wooden door
      const dz = cz + (hash(seed, 1) - 0.5) * (len - 3);
      mk(boxGeo(0.12, 2.3, 1.3, 1.5), woodM, hb, { pos: [xf - sd * 0.0, 1.15, dz], outline: 3.5 });
      mk(new THREE.CylinderGeometry(0.65, 0.65, 0.12, 20, 1, false, 0, Math.PI), woodM, hb, { pos: [xf, 2.3, dz], rot: [0, 0, Math.PI / 2], outline: 3.5 }).rotation.set(Math.PI / 2, 0, sd > 0 ? Math.PI / 2 : -Math.PI / 2);
      mk(new THREE.TorusGeometry(0.72, 0.09, 8, 20, Math.PI), wall, hb, { pos: [xf - sd * 0.06, 2.3, dz], rot: [0, Math.PI / 2, 0], outline: 3.5 });
      for (const y of [0.9, 1.6]) mk(new THREE.SphereGeometry(0.03, 8, 6), gold({ rough: 0.4 }), hb, { pos: [xf - sd * 0.08, y, dz + 0.4], outline: false });
    }
    // windows and lattice balconies on the upper floors
    const floors = Math.floor((h - 3.4) / 2.6);
    for (let f = 0; f < floors; f++) {
      const y = 4.4 + f * 2.6;
      const nW = Math.max(1, Math.floor(len / 2.6));
      for (let k = 0; k < nW; k++) {
        const z = z0 - (k + 0.5) * len / nW;
        if (hash(seed, f, k) < 0.45) {
          const mb = mk(boxGeo(0.55, 1.5, 1.2, 1.2), latticeM, hb, { pos: [xf - sd * 0.27, y, z], outline: 4 });
          mk(boxGeo(0.65, 0.12, 1.32, 1), woodM, hb, { pos: [xf - sd * 0.3, y + 0.8, z], outline: 3 });
          mk(boxGeo(0.65, 0.12, 1.32, 1), woodM, hb, { pos: [xf - sd * 0.3, y - 0.8, z], outline: 3 });
        } else {
          mk(boxGeo(0.06, 1.2, 0.75, 1), toon('#2a1a12'), hb, { pos: [xf - sd * 0.03, y, z], outline: 3 });
          mk(boxGeo(0.12, 0.08, 0.95, 1), wall, hb, { pos: [xf - sd * 0.06, y - 0.64, z], outline: 2.5 });
          if (hash(seed, k, f) < 0.4) mk(new THREE.CylinderGeometry(0.04, 0.04, 0.5, 4), toon('#2e7a4a'), hb, { pos: [xf - sd * 0.25, y - 0.45, z], rot: [Math.PI / 2, 0, 0], scale: [3, 1, 5], outline: 2.5 });
        }
      }
    }
    return { hb, xf, cz, len, sd };
  }
  // left (x<0) and right (x>0) sides: [z0, z1, height, wall, shop?, seed]
  const LEFT = [[12, 3.2, 8.6, 'a', 'cloth2', 1], [3.2, -3.0, 10.2, 'c', 'spice', 2], [-3.0, -9.2, 7.6, 'b', 'pottery', 3], [-9.2, -15.6, 9.4, 'd', 'changer', 4], [-15.6, -22.0, 11.5, 'e', null, 5], [-22.0, -29, 8.8, 'a', 'lamps', 6], [-29, -37, 10.5, 'c', null, 7], [-37, -46, 9.2, 'b', 'cloth', 8]];
  const RIGHT = [[12, 3.6, 9.6, 'd', 'cloth', 9], [3.6, -3.4, 8.0, 'e', 'lamps', 10], [-3.4, -9.6, 9.8, 'a', 'bread', 11], [-9.6, -16.0, 8.2, 'c', 'carpets', 12], [-16.0, -19.2, 10.8, 'b', null, 13], [-21.6, -28.0, 9.0, 'd', 'pottery', 14], [-28, -36, 11.2, 'e', null, 15], [-36, -46, 8.6, 'a', 'spice2', 16]];
  A.houses = {};
  for (const [list, sd] of [[LEFT, -1], [RIGHT, 1]]) for (const [z0, z1, h, w, shop, seed] of list) {
    const hs = house(sd, z0, z1, h, walls[w], shop, seed);
    if (shop) A.houses[shop + (sd < 0 ? 'L' : 'R') + Math.round(z0)] = hs;
    if (shop) goods(shop, hs);
  }
  // the alley on the right between z -19.2 and -21.6 (back wall, a lamp, the sleeping cat on a coin pile)
  mk(boxGeo(0.6, 9, 2.4, 2.2), walls.c, g, { pos: [H + 6.3, 4.5, -20.4], outline: 4 });
  mk(boxGeo(6.3, 0.05, 2.4, 2), toon('#ffffff', { map: TX.flagstones('#c4a070', [1, 1], 8) }), g, { pos: [H + 3.15, 0.01, -20.4], outline: false, cast: false });
  const cat = makeCat(); cat.position.set(H + 0.9, 0.16, -20.3); cat.rotation.y = -0.6; g.add(cat); A.cat = cat;
  A.alleyPile = V(H + 0.9, 0, -20.3);
  function goods(kind, hs) {
    const { hb, xf, cz, len, sd } = hs;
    const front = xf + sd * 0.25;
    const k = kind.replace(/\d/g, '');
    if (k === 'spice') {
      mk(boxGeo(0.9, 0.75, len - 1.4, 1), woodM, hb, { pos: [front, 0.375, cz], outline: 4 });
      const cols = ['#c8321e', '#e8901e', '#f2c41a', '#7a4a1e', '#5a8a2a', '#d85a2a', '#a8201a'];
      for (let i = 0; i < 7; i++) {
        const z = cz - (len - 1.8) / 2 + i * (len - 1.8) / 6;
        mk(new THREE.CylinderGeometry(0.2, 0.2, 0.08, 16), toon('#d8c8a0'), hb, { pos: [front, 0.79, z], outline: 2.5 });
        mk(new THREE.ConeGeometry(0.18, 0.28, 16), toon(cols[i], { lift: 0.08 }), hb, { pos: [front, 0.97, z], outline: 3 });
      }
      for (let i = 0; i < 3; i++) mk(new THREE.CylinderGeometry(0.22, 0.26, 0.6, 14), toon('#c8a46a'), hb, { pos: [xf + sd * 0.9, 0.3, cz - 1 + i], outline: 3.5 });
    } else if (k === 'bread') {
      A.bread = { front: V(front - sd * 0.1, 0, cz), sd };
      mk(boxGeo(0.95, 0.9, len - 1.6, 1), woodM, hb, { pos: [front, 0.45, cz], outline: 4 });
      for (let i = 0; i < 6; i++) for (let j = 0; j < 4; j++) {
        const fb = PR.flatbread(); fb.position.set(front + (j % 2 - 0.5) * 0.3, 0.92 + j * 0.03, cz - 1.5 + i * 0.6); fb.rotation.set((hash(i, j) - 0.5) * 0.15, 0, (hash(j, i) - 0.5) * 0.15); hb.add(fb);
      }
      // clay oven glowing at the back
      const ov = mk(new THREE.SphereGeometry(0.75, 20, 14, 0, Math.PI * 2, 0, Math.PI / 2), toon('#b8643a'), hb, { pos: [xf + sd * 1.3, 0.0, cz + 1.4], outline: 4.5 });
      mk(new THREE.CircleGeometry(0.28, 16), new THREE.MeshStandardMaterial({ color: '#ff8a2a', emissive: '#ff7a1a', emissiveIntensity: 2.4 }), hb, { pos: [xf + sd * 0.55, 0.32, cz + 1.4], rot: [0, -sd * Math.PI / 2, 0], outline: false });
      const ol = new THREE.PointLight('#ff8a3a', 2.5, 3.5, 1.8); ol.position.set(xf + sd * 0.4, 0.5, cz + 1.4); hb.add(ol);
      for (let i = 0; i < 5; i++) { const lf = PR.loaf(); lf.position.set(xf + sd * 1.65, 1.38, cz - 2 + i * 0.5); hb.add(lf); }
      const pb = PR.priceBoard(0.7, 0.5); pb.position.set(front - sd * 0.05, 1.45, cz - 1.0); pb.rotation.y = -sd * Math.PI / 2; hb.add(pb); A.priceBoard = pb;
      A.breadFront = V(front - sd * 0.55, 0, cz - 0.2);
    } else if (k === 'changer') {
      A.changer = { front: V(front, 0, cz), sd };
      mk(boxGeo(0.9, 0.82, 2.2, 1), toon('#ffffff', { map: TX.carpet('#7a1a2a', '#e8b84a', '#1c2a5a') }), hb, { pos: [front, 0.41, cz], outline: 4 });
      const bal = PR.balance(); bal.position.set(front - sd * 0.05, 0.82, cz - 0.15); bal.rotation.y = -sd * Math.PI / 2; hb.add(bal); A.balance = bal;
      for (let i = 0; i < 2; i++) { const cp = new PR.CoinPool(hb, 40); cp.mesh.name = 'stack'; for (let j = 0; j < 12 + i * 6; j++) cp.add(V(front + (i - 0.5) * 0.25, 0.83 + j * 0.0065, cz + 0.6), 0, j, 0); }
      const tl = mk(new THREE.PlaneGeometry(1.2, 0.6), toon('#ffffff', { map: TX.tally(0) }), hb, { pos: [xf + sd * 1.88, 1.75, cz - 0.9], rot: [0, -sd * Math.PI / 2, 0], outline: false, cast: false });
      A.tallyBoard = tl;
      for (const [y, z] of [[2.3, cz + 1], [2.3, cz - 1.6]]) mk(new THREE.PlaneGeometry(0.9, 1.3), toon('#ffffff', { map: TX.carpet('#1c4a7a', '#f0c24a', '#a8202a') }), hb, { pos: [xf + sd * 1.88, y, z], rot: [0, -sd * Math.PI / 2, 0], outline: false });
    } else if (k === 'cloth') {
      const cols = ['#c4302a', '#2a5a9a', '#f2c24a', '#2a7a4a', '#7a2a6a', '#e07a2a'];
      for (let i = 0; i < 6; i++) mk(new THREE.CylinderGeometry(0.13, 0.13, 1.1, 14), toon(cols[i], { lift: 0.08 }), hb, { pos: [front, 0.2 + (i % 3) * 0.27, cz - 1.2 + Math.floor(i / 3) * 0.9 + (i % 3) * 0.08], rot: [0, 0, Math.PI / 2], outline: 3.5 });
      for (let i = 0; i < 4; i++) mk(new THREE.PlaneGeometry(0.7, 1.6), toon('#ffffff', { map: TX.stripes(cols[(i + 2) % 6], '#f4ecd8', 6, true), side: THREE.DoubleSide, lift: 0.08 }), hb, { pos: [xf + sd * 0.6, 1.9, cz - 1.5 + i], rot: [0, Math.PI / 2, 0], outline: false });
    } else if (k === 'pottery') {
      for (let i = 0; i < 9; i++) {
        const h = 0.4 + hash(i, 4) * 0.5;
        const prof = [[0, 0], [0.12, 0], [0.2, 0.25], [0.18, 0.6], [0.1, 0.85], [0.11, 1.0]].map(([r, y]) => new THREE.Vector2(r * h * 1.4, y * h));
        mk(new THREE.LatheGeometry(prof, 18), toon(['#b8643a', '#c88a4a', '#9a4a2a'][i % 3]), hb, { pos: [front + sd * (i % 2) * 0.3, 0, cz - 2 + i * 0.5], outline: 3.5 });
      }
    } else if (k === 'lamps') {
      for (let i = 0; i < 7; i++) { const lt = PR.lantern(['#ffb85a', '#ff7a5a', '#7ad0ff', '#a0ff8a'][i % 4]); lt.position.set(xf - sd * 0.2, 2.2 + (i % 2) * 0.35, cz - 1.8 + i * 0.6); hb.add(lt); }
    } else if (k === 'carpets') {
      for (let i = 0; i < 3; i++) mk(new THREE.PlaneGeometry(1.1, 1.8), toon('#ffffff', { map: TX.carpet(['#a8202a', '#1c4a7a', '#2a6a3a'][i], '#f0c24a', ['#1c2c6a', '#a8202a', '#7a1a2a'][i]), side: THREE.DoubleSide }), hb, { pos: [front, 1.25, cz - 1.6 + i * 1.6], rot: [0, Math.PI / 2, 0], outline: false });
    }
  }
  // the mosque at the end of the street: dome on a drum, and a minaret with balconies
  const mq = new THREE.Group(); mq.position.set(-2, 0, -60); g.add(mq);
  const mw = toon('#ffffff', { map: TX.ablaq('#f0dab0', '#c4643c', [1, 1], 9) });
  mk(boxGeo(16, 12, 12, 3), mw, mq, { pos: [0, 6, 0], outline: 5 });
  mk(new THREE.CylinderGeometry(5.2, 5.2, 3, 24), mw, mq, { pos: [0, 13.5, 0], outline: 5 });
  mk(new THREE.SphereGeometry(5.2, 32, 18, 0, Math.PI * 2, 0, Math.PI / 2), toon('#ffffff', { map: TX.ablaq('#e6c48a', '#d8b070', [1, 1], 10, false) }), mq, { pos: [0, 15, 0], outline: 5 });
  mk(new THREE.ConeGeometry(0.3, 2.2, 8), gold({ rough: 0.35 }), mq, { pos: [0, 21.2, 0], outline: 3 });
  const mn = new THREE.Group(); mn.position.set(8.5, 0, 3); mq.add(mn);
  mk(new THREE.CylinderGeometry(1.5, 1.7, 16, 8), mw, mn, { pos: [0, 8, 0], outline: 5 });
  mk(new THREE.CylinderGeometry(2.1, 1.6, 0.6, 8), mw, mn, { pos: [0, 16.3, 0], outline: 4 });
  mk(new THREE.CylinderGeometry(1.15, 1.3, 7, 8), mw, mn, { pos: [0, 20, 0], outline: 4.5 });
  mk(new THREE.CylinderGeometry(1.6, 1.15, 0.5, 8), mw, mn, { pos: [0, 23.6, 0], outline: 4 });
  mk(new THREE.CylinderGeometry(0.75, 0.85, 3.5, 8), mw, mn, { pos: [0, 25.6, 0], outline: 4 });
  mk(new THREE.SphereGeometry(0.85, 16, 12), mw, mn, { pos: [0, 27.6, 0], scale: [1, 1.4, 1], outline: 4 });
  mk(new THREE.ConeGeometry(0.15, 1.6, 6), gold(), mn, { pos: [0, 29.4, 0], outline: 2.5 });
  // bunting and lanterns across the street
  const BC = ['#c4302a', '#f2c24a', '#2a5a9a', '#2a7a4a', '#f6ecd8'];
  for (const z of [6, -6.5, -18, -31]) g.add(PR.bunting(V(-H, 6.2 + hash(z, 1), z), V(H, 6.0 + hash(z, 2), z - 1.5), 14, 0.7, BC));
  for (const z of [1, -12.5, -25]) {
    const r = PR.rope(V(-H, 5.2, z), V(H, 5.2, z), 0.5, 0.01, '#5a4a3a'); g.add(r);
    const lt = PR.lantern(); lt.position.set(0.3, 4.32, z); g.add(lt);
  }
  // palms in pots at a few doors
  for (const [x, z] of [[-H + 0.5, -15.9], [H - 0.5, -9.9], [-H + 0.5, 3.0]]) {
    mk(new THREE.CylinderGeometry(0.35, 0.25, 0.6, 14), toon('#b8643a'), g, { pos: [x, 0.3, z], outline: 3.5 });
    for (let i = 0; i < 7; i++) { const a = i / 7 * Math.PI * 2; mk(new THREE.ConeGeometry(0.12, 1.4, 5), toon('#3a8a3a', { lift: 0.05 }), g, { pos: [x + Math.cos(a) * 0.35, 1.2, z + Math.sin(a) * 0.35], rot: [Math.sin(a) * 0.7, 0, -Math.cos(a) * 0.7], outline: 3 }); }
  }
  // sky, light, haze
  const sky = skyDome(g, { top: '#4a6ed0', mid: '#f0b48a', horizon: '#ffd9a0', sunDir: [0.5, 0.45, -0.75], sun: '#ffd28a', radius: 600 });
  const mClouds = clouds(g, [[-14, 34, -120, 7, 1], [18, 40, -150, 9, 2], [-4, 52, -200, 10, 3], [30, 30, -90, 6, 4], [-30, 44, -110, 8, 5], [8, 30, 60, 7, 6], [-20, 38, 90, 8, 7], [26, 46, 20, 7, 8], [-28, 42, -20, 7, 9]]);
  const sun = sunLight(g, '#ffc27a', 3.2, 34, 4096);
  const hemi = new THREE.HemisphereLight('#9ab4e8', '#c08050', 0.55); g.add(hemi);
  const fill = new THREE.DirectionalLight('#a8b8ff', 0.35); fill.position.set(-20, 15, 20); g.add(fill);
  const shafts = [
    shaft(g, V(H + 2, 11, -19.5), V(-1.5, 0, -14), 2.2, 0.32),
    shaft(g, V(H + 1, 10, -3.3), V(-1.2, 0, 1.5), 1.6, 0.24),
    shaft(g, V(-H - 1, 12, -9), V(1.2, 0, -5), 1.4, 0.18),
  ];
  const motes = dust(g, [-3.2, 3.2, 0.3, 5, -24, 6], 900, '#ffe6b8', 0.045, 5);
  const LIGHT = {
    gold: { sunPos: [26, 30, -34], sunCol: '#ffb460', sunI: 4.0, hemi: ['#6f8ee8', '#b8703a', 0.5], sky: ['#3a5ad0', '#f08a7a', '#ffc884'], sunDir: [0.5, 0.4, -0.75], fog: '#f0a882', shafts: 1, exposure: 1.0, cloud: '#e0a0c8' },
    morning: { sunPos: [-28, 24, 12], sunCol: '#ffd9a0', sunI: 3.3, hemi: ['#88aaf0', '#b07a50', 0.6], sky: ['#2a6ee0', '#8cc0f4', '#f4dcb8'], sunDir: [-0.6, 0.4, 0.3], fog: '#c8d8f0', shafts: 0.55, exposure: 1.0, cloud: '#fff4ec' },
    day: { sunPos: [18, 38, -20], sunCol: '#fff0d0', sunI: 3.9, hemi: ['#7aa8ff', '#b07a4a', 0.6], sky: ['#1656d6', '#3f8cf2', '#a8d6ff'], sunDir: [0.4, 0.6, -0.5], fog: '#bcd6f4', shafts: 0.8, exposure: 1.0, cloud: '#ffffff' },
  };
  return {
    group: g, sun, A,
    apply(t, shot) {
      const L = LIGHT[shot.light || 'gold'];
      sun.position.set(...L.sunPos); sun.target.position.set(0, 0, -10); sun.color.set(L.sunCol); sun.intensity = L.sunI;
      hemi.color.set(L.hemi[0]); hemi.groundColor.set(L.hemi[1]); hemi.intensity = L.hemi[2];
      sky.material.uniforms.top.value.set(L.sky[0]); sky.material.uniforms.mid.value.set(L.sky[1]); sky.material.uniforms.hor.value.set(L.sky[2]);
      sky.material.uniforms.sunDir.value.set(...L.sunDir).normalize(); sky.material.uniforms.sunCol.value.set(L.sunCol);
      scene.fog = new THREE.Fog(L.fog, 70, 260);
      for (const c of mClouds) c.children[0].material.color.set(L.cloud);
      scene.environmentIntensity = 0.3;
      for (const s of shafts) { s.visible = L.shafts > 0; s.userData.mat.uniforms.op.value = s.userData.base ?? (s.userData.base = s.userData.mat.uniforms.op.value); s.userData.mat.uniforms.op.value = s.userData.base * L.shafts * (shot.shafts ?? 1); s.userData.mat.uniforms.col.value.set(L.sunCol); }
      motes.userData.tick(t);
      cat.userData.breathe(t);
    },
    grade: { bloomThr: 1.0, bloom: 0.34, contrast: 1.16, sat: 1.3, shadow: [0.86, 0.9, 1.16], high: [1.08, 1.0, 0.9], vignette: 0.36, lineFar: 120 },
  };
};

// ======================================================================= desert
function dunes(size, seg, seed, flatZ = null) {
  const geo = new THREE.PlaneGeometry(size, size, seg, seg).rotateX(-Math.PI / 2);
  const p = geo.getAttribute('position');
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), z = p.getZ(i);
    let y = Math.sin(x * 0.021 + seed) * 3.2 + Math.sin(z * 0.017 + x * 0.008 + seed * 2) * 4.0 + Math.sin(x * 0.06 + z * 0.045) * 0.9 + Math.sin(x * 0.13 - z * 0.09 + seed) * 0.35;
    // flat bands (mesh-local z): [centre, half-width, ramp]
    for (const b of flatZ || []) { const k = clamp((Math.abs(z - b[0]) - b[1]) / b[2]); y *= k; }
    p.setY(i, y);
  }
  geo.computeVertexNormals();
  return geo;
}
export const DS = { origin: V(1000, 0, 0) };
BUILD.desert = (scene, W) => {
  const g = new THREE.Group(); g.position.copy(DS.origin); scene.add(g);
  const A = (W.anchors.desert = {});
  const sandM = toon('#ffffff', { map: TX.sand('#ecbd80', [70, 70]) });
  mk(dunes(900, 220, 1.3, [[200, 7, 30], [75, 26, 14]]), sandM, g, { pos: [0, -0.02, -200], cast: false, outline: false });
  // pyramids of Giza
  const pyrM = toon('#ffffff', { map: TX.pyramidBlocks('#dcaa66', [6, 6]) });
  for (const [x, z, b, h] of [[-70, -190, 118, 74], [55, -240, 108, 70], [-160, -260, 62, 40]]) {
    const geo = new THREE.ConeGeometry(b / Math.SQRT2, h, 4, 1); geo.rotateY(Math.PI / 4);
    mk(geo, pyrM, g, { pos: [x, h / 2 - 1, z], outline: 6 });
  }
  // the Nile with fields and palms, Cairo's domes and minarets on the horizon
  mk(new THREE.PlaneGeometry(1400, 22).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: '#3a7ab8', roughness: 0.15, metalness: 0.2 }), g, { pos: [0, 0.4, -125], cast: false, outline: false });
  mk(new THREE.PlaneGeometry(1400, 40).rotateX(-Math.PI / 2), toon('#7aa84a'), g, { pos: [0, 0.3, -125], cast: false, outline: false });
  const palmLeaf = toon('#2e7a3a', { lift: 0.05 }), trunk = toon('#8a6a42');
  for (let i = 0; i < 46; i++) {
    const x = -300 + i * 13 + hash(i, 3) * 8, z = -125 + (i % 2 ? 13 : -13) + hash(i, 5) * 4;
    const h = 7 + hash(i, 6) * 4;
    mk(new THREE.CylinderGeometry(0.25, 0.4, h, 6), trunk, g, { pos: [x, h / 2, z], rot: [0, 0, (hash(i, 7) - 0.5) * 0.25], outline: 3 });
    for (let k = 0; k < 6; k++) { const a = k / 6 * Math.PI * 2; mk(new THREE.ConeGeometry(0.35, 4.2, 4), palmLeaf, g, { pos: [x + Math.cos(a) * 1.6, h - 0.4, z + Math.sin(a) * 1.6], rot: [Math.sin(a) * 1.25, 0, -Math.cos(a) * 1.25], scale: [1, 1, 0.3], outline: 3 }); }
  }
  const cityM = toon('#e8cfa8');
  for (let i = 0; i < 26; i++) {
    const x = 120 + i * 11 + hash(i, 1) * 6, z = -300 - hash(i, 2) * 40;
    const w = 6 + hash(i, 3) * 10, h = 6 + hash(i, 4) * 12;
    mk(boxGeo(w, h, 8, 4), cityM, g, { pos: [x, h / 2, z], outline: 4 });
    if (i % 4 === 0) mk(new THREE.SphereGeometry(5, 16, 10, 0, Math.PI * 2, 0, Math.PI / 2), cityM, g, { pos: [x, h, z], outline: 4 });
    if (i % 5 === 2) { mk(new THREE.CylinderGeometry(0.9, 1.1, h + 22, 8), cityM, g, { pos: [x + 4, (h + 22) / 2, z + 3], outline: 4 }); mk(new THREE.ConeGeometry(1.2, 4, 8), cityM, g, { pos: [x + 4, h + 24, z + 3], outline: 3 }); }
  }
  // the caravan: camels (one royal with seat and parasol), attendants, people
  A.camels = [];
  for (let i = 0; i < 9; i++) {
    const royal = i === 2;
    const cm = makeCamel({ sacks: !royal, seat: royal, cloth: royal ? '#b8262e' : ['#26307a', '#7a3a1e', '#2b5e3a'][i % 3], cloth2: '#f2c24a', bridle: royal ? '#d9a521' : '#7a3a1e', fur: ['#d6a65e', '#c8944e', '#dcae6a'][i % 3] });
    scene.add(cm.root); cm.root.visible = false; A.camels.push(cm); (W.actors ||= []).push(cm.root);
    if (royal) { const par = PR.parasol(); par.position.set(-0.35, 1.95, -0.3); par.scale.setScalar(0.9); cm.body.add(par); A.parasol = par; }
  }
  A.staffs = [];
  for (let i = 0; i < 12; i++) { const s = PR.goldStaff(1.9); scene.add(s); s.visible = false; A.staffs.push(s); W.actors.push(s); }
  const sky = skyDome(g, { top: '#5a7ad8', mid: '#f4a682', horizon: '#ffd3a0', sunDir: [0.9, 0.08, -0.4], sun: '#ffd08a', sunSize: 0.9992, glow: 1.0, radius: 800 });
  const sun = sunLight(g, '#ffb470', 3.0, 40, 4096);
  const hemi = new THREE.HemisphereLight('#a0b8f0', '#d8905a', 0.6); g.add(hemi);
  const sandDust = dust(g, [-30, 40, 0.2, 3, -12, 12], 500, '#ffd8a0', 0.06, 9);
  const LIGHT = {
    sunrise: { sunDir: [0.9, 0.1, -0.42], sunCol: '#ffb874', sunI: 3.1, sky: ['#5a7ad8', '#f4a682', '#ffd3a0'], hemi: ['#a0b8f0', '#d8905a', 0.62], fog: '#f6c8a0', exposure: 1.0 },
    sunset: { sunDir: [-0.9, 0.07, -0.42], sunCol: '#ff9a5a', sunI: 3.0, sky: ['#3a3a8a', '#e0607a', '#ffb070'], hemi: ['#8a8ad8', '#c86a4a', 0.55], fog: '#e88a7a', exposure: 1.02 },
  };
  return {
    group: g, sun, A,
    apply(t, shot) {
      const L = LIGHT[shot.light || 'sunrise'];
      const d = V(...L.sunDir).normalize();
      const c = shot.lightCentre || V(0, 0, 0);
      sun.position.copy(DS.origin).add(c).addScaledVector(d, 150); sun.target.position.copy(DS.origin).add(c);
      sun.color.set(L.sunCol); sun.intensity = L.sunI;
      hemi.color.set(L.hemi[0]); hemi.groundColor.set(L.hemi[1]); hemi.intensity = L.hemi[2];
      const u = sky.material.uniforms; u.top.value.set(L.sky[0]); u.mid.value.set(L.sky[1]); u.hor.value.set(L.sky[2]); u.sunDir.value.copy(d); u.sunCol.value.set(L.sunCol);
      scene.fog = new THREE.Fog(L.fog, 90, 520);
      scene.environmentIntensity = 0.3;
      sandDust.userData.tick(t);
    },
    grade: { bloomThr: 0.92, bloom: 0.45, contrast: 1.14, sat: 1.28, shadow: [0.88, 0.9, 1.14], high: [1.08, 1.0, 0.9], vignette: 0.36, lineFar: 260 },
  };
};

// ======================================================================= void (the rarity showroom)
export const VD = { origin: V(2000, 0, 0) };
BUILD.void = (scene, W) => {
  const g = new THREE.Group(); g.position.copy(VD.origin); scene.add(g);
  const A = (W.anchors.void = {});
  mk(new THREE.CircleGeometry(30, 48).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: '#2a1838', roughness: 0.35, metalness: 0.1 }), g, { cast: false, outline: false });
  const back = mk(new THREE.SphereGeometry(40, 32, 16), new THREE.MeshBasicMaterial({ color: '#1a0e26', side: THREE.BackSide }), g, { cast: false, outline: false });
  back.layers.set(LAYER.FX);
  // pedestal: marble column with gold rings and a red velvet cushion
  const marble = toon('#ece4f0', { rough: 0.5 });
  mk(new THREE.CylinderGeometry(0.42, 0.5, 0.12, 32), marble, g, { pos: [0, 0.06, 0], outline: 5 });
  mk(new THREE.CylinderGeometry(0.28, 0.32, 1.0, 32), marble, g, { pos: [0, 0.62, 0], outline: 5 });
  mk(new THREE.CylinderGeometry(0.4, 0.36, 0.1, 32), marble, g, { pos: [0, 1.17, 0], outline: 5 });
  for (const y of [0.16, 1.1]) mk(new THREE.TorusGeometry(0.31, 0.025, 8, 32), gold({ rough: 0.3 }), g, { pos: [0, y, 0], rot: [Math.PI / 2, 0, 0], outline: 3 });
  mk(new THREE.BoxGeometry(0.5, 0.1, 0.5), toon('#a8102a', { rough: 0.95, lift: 0.08 }), g, { pos: [0, 1.27, 0], outline: 4.5 });
  for (const [x, z] of [[-0.25, -0.25], [0.25, -0.25], [-0.25, 0.25], [0.25, 0.25]]) mk(new THREE.SphereGeometry(0.03, 8, 6), gold(), g, { pos: [x, 1.3, z], outline: false });
  A.top = V(0, 1.325, 0);
  const spot = new THREE.SpotLight('#fff0d0', 70, 14, 0.32, 0.55, 1.4);
  spot.position.set(0, 7, 0.6); spot.target.position.set(0, 1.2, 0); spot.castShadow = true; spot.shadow.mapSize.set(2048, 2048);
  g.add(spot, spot.target);
  g.add(new THREE.HemisphereLight('#5a4a8a', '#1a0e20', 0.35));
  const rim = new THREE.DirectionalLight('#c08aff', 0.8); rim.position.set(-4, 3, -6); g.add(rim);
  const beam = shaft(g, V(0, 7, 0.6), V(0, 0, 0), 1.6, 0.5, '#fff0d0');
  const motes = dust(g, [-1.2, 1.2, 0.2, 5, -1.2, 1.2], 260, '#fff4d8', 0.03, 12);
  return {
    group: g, A,
    apply(t, shot) { scene.fog = null; scene.environmentIntensity = 0.5; motes.userData.tick(t); beam.userData.mat.uniforms.op.value = shot.beam ?? 0.5; },
    grade: { bloomThr: 0.85, bloom: 0.6, contrast: 1.1, sat: 1.15, vignette: 0.5, lineFar: 60 },
  };
};

// ======================================================================= camp (night)
export const CP = { origin: V(3000, 0, 0) };
BUILD.camp = (scene, W) => {
  const g = new THREE.Group(); g.position.copy(CP.origin); scene.add(g);
  const A = (W.anchors.camp = {});
  mk(dunes(500, 160, 4.1, [[60, 12, 25]]), toon('#ffffff', { map: TX.sand('#a98fa0', [50, 50], 6) }), g, { pos: [0, -0.02, -60], cast: false, outline: false });
  for (const [x, z, c, s] of [[-1.4, -6.4, '#e8dcc0', '#b8402a'], [3.6, -7.4, '#e0d0b0', '#26307a'], [-6.5, -9.5, '#d8c8a8', '#2b5e3a']]) { const tt = PR.tent(c, s); tt.position.set(x, 0, z); tt.rotation.y = hash(x, z) * 2; g.add(tt); }
  const fire = PR.campfire(); fire.position.set(0.15, 0, -1.9); g.add(fire); A.fire = fire;
  const ch = PR.chest(); ch.position.set(1.0, 0, 0.3); ch.rotation.y = 0.12; g.add(ch); A.chest = ch;
  A.moth = PR.moth(); scene.add(A.moth); A.moth.visible = false; (W.actors ||= []).push(A.moth);
  A.camels = [];
  for (const [x, z, r] of [[-3.4, -3.8, 0.9], [4.6, -3.6, -1.2], [-1.8, -10, 0.3]]) { const cm = makeCamel({ sacks: false, cloth: '#26307a' }); cm.root.position.set(x, 0, z); cm.root.rotation.y = r; cm.pose.sit = 1; g.add(cm.root); A.camels.push(cm); }
  const sky = skyDome(g, { top: '#0b1660', mid: '#2a3aa8', horizon: '#6a58c0', sunDir: [-0.15, 0.3, -1], sun: '#dfe6ff', sunSize: 0.99999, glow: 0.35, stars: true, radius: 400 });
  moonDisc(g, V(-26, 52, -160), 7);
  clouds(g, [[-60, 40, -170, 9, 11], [40, 48, -190, 11, 12], [-10, 70, -230, 12, 13], [80, 36, -140, 8, 14]], '#4a58b8', 0.25);
  fortress(g, V(-9, 0.8, -80), 0.1);
  const moon = sunLight(g, '#8ea4ff', 1.25, 20, 2048); moon.position.copy(CP.origin).add(V(-14, 28, -60)); moon.target.position.copy(CP.origin);
  g.add(new THREE.HemisphereLight('#4a5cc0', '#2a1c40', 0.6));
  for (const [x, z] of [[-0.4, -5.0], [2.6, -6.0]]) { mk(new THREE.CylinderGeometry(0.03, 0.03, 1.75, 6), toon('#5a3a22'), g, { pos: [x, 0.87, z - 0.12], outline: 2 }); const lt = PR.lantern('#ffb85a'); lt.position.set(x, 1.6, z); g.add(lt); const pl = new THREE.PointLight('#ffa850', 2.2, 5, 1.8); pl.position.set(x, 1.5, z + 0.3); g.add(pl); }
  const embers = dust(g, [-0.45, 0.75, 0.3, 3, -2.5, -1.3], 60, '#ffb060', 0.035, 21);
  return {
    group: g, A,
    apply(t) {
      scene.fog = new THREE.Fog('#28307a', 40, 260); scene.environmentIntensity = 0.18;
      fire.userData.tick(t); embers.userData.tick(t * 2.5);
      for (const cm of A.camels) cm.update(t);
    },
    grade: { bloomThr: 0.9, bloom: 0.45, contrast: 1.14, sat: 1.3, shadow: [0.86, 0.9, 1.2], high: [1.1, 0.98, 0.88], vignette: 0.45, exposure: 0.88, lineFar: 160 },
  };
};
