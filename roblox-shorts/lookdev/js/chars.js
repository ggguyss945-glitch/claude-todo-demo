// Characters: garden gnome (sculpted, glazed ceramic, big glossy eyes), brass lantern, R6 Roblox kid.
import { THREE, rng, canvas, paint, tex, fbm, rbox, mesh, std, phys, glowSprite, knitTextures, clamp } from './lib.js';

// ------------------------------------------------------------------ shared shapes
// teardrop clump: unit sphere stretched along -y into a tapered, slightly bent strand
function clumpGeo(R, L, bend = 0, seg = 18) {
  const g = new THREE.SphereGeometry(1, seg, Math.round(seg * 0.75)), p = g.attributes.position;
  for (let i = 0; i < p.count; i++) {
    let x = p.getX(i), y = p.getY(i), z = p.getZ(i);
    if (y < 0) { const t = -y; x *= 1 - 0.78 * t * t; z *= 1 - 0.78 * t * t; y = -t * L / R; }
    x *= R; z *= R; y *= R;
    const t = clamp(-y / L); x += bend * t * t * L; z += Math.abs(bend) * 0.5 * t * t * L;
    p.setXYZ(i, x, y, z);
  }
  g.computeVertexNormals(); return g;
}
// strand bump texture (vertical strands along sphere v)
function strandBump() {
  if (strandBump.c) return strandBump.c;
  const c = paint(256, 256, (u, v) => { const s = 0.5 + 0.5 * Math.sin(u * 2 * Math.PI * 22 + fbm(u * 4, v * 4, 3, 4, 2) * 6); const l = 90 + 140 * s * (0.7 + 0.3 * fbm(u * 30, v * 6, 2, 30, 5)); return [l, l, l]; });
  strandBump.c = tex(c, { srgb: false }); return strandBump.c;
}
// painted eye: sclera + iris + pupil + painted catchlights. u=0.25 faces +z.
function eyeTexture(iris = '#3b6fb0', ring = '#16243f', irisR = 0.23) {
  const key = iris + ring + irisR; eyeTexture.m = eyeTexture.m || new Map();
  if (eyeTexture.m.has(key)) return eyeTexture.m.get(key);
  const W = 1024, H = 512, cx = W * 0.25, cy = H * 0.5, ir = irisR / (2 * Math.PI) * W; // irisR in radians
  const c = canvas(W, H), g = c.getContext('2d');
  const sg = g.createRadialGradient(cx, cy, ir * 0.5, cx, cy, W * 0.3); sg.addColorStop(0, '#fbf7f2'); sg.addColorStop(0.7, '#efe6e4'); sg.addColorStop(1, '#d9c3c6');
  g.fillStyle = sg; g.fillRect(0, 0, W, H);
  // faint veins
  g.strokeStyle = 'rgba(200,90,100,0.18)'; g.lineWidth = 2; const r = rng(3);
  for (let i = 0; i < 14; i++) { const a = r() * 6.28; let x = cx + Math.cos(a) * ir * 3.2, y = cy + Math.sin(a) * ir * 1.6; g.beginPath(); g.moveTo(x, y); for (let k = 0; k < 5; k++) { x += (cx - x) * 0.18 + (r() - 0.5) * 18; y += (cy - y) * 0.18 + (r() - 0.5) * 12; g.lineTo(x, y); } g.stroke(); }
  g.save(); g.translate(cx, cy); g.scale(1, 2); // v spans pi, u spans 2pi -> stretch y by 2
  const ig = g.createRadialGradient(0, 0, ir * 0.2, 0, 0, ir); ig.addColorStop(0, '#f0d27a'); ig.addColorStop(0.32, iris); ig.addColorStop(0.85, iris); ig.addColorStop(1, ring);
  g.fillStyle = ig; g.beginPath(); g.arc(0, 0, ir, 0, 6.28); g.fill();
  g.strokeStyle = 'rgba(255,255,255,0.18)'; g.lineWidth = 1.5; for (let i = 0; i < 48; i++) { const a = i / 48 * 6.28; g.beginPath(); g.moveTo(Math.cos(a) * ir * 0.42, Math.sin(a) * ir * 0.42); g.lineTo(Math.cos(a) * ir * 0.9, Math.sin(a) * ir * 0.9); g.stroke(); }
  g.fillStyle = '#05040a'; g.beginPath(); g.arc(0, 0, ir * 0.44, 0, 6.28); g.fill();
  g.fillStyle = 'rgba(255,255,255,0.96)'; g.beginPath(); g.ellipse(-ir * 0.32, -ir * 0.34, ir * 0.2, ir * 0.17, 0, 0, 6.28); g.fill();
  g.fillStyle = 'rgba(255,255,255,0.7)'; g.beginPath(); g.arc(ir * 0.3, ir * 0.3, ir * 0.08, 0, 6.28); g.fill();
  g.restore();
  const t = tex(c, { wrap: false }); eyeTexture.m.set(key, t); return t;
}

// ------------------------------------------------------------------ lantern
export function makeLantern({ lit = true, power = 1, lights = true } = {}) {
  const L = new THREE.Group(); L.name = 'lantern';
  const brass = phys('#b8873a', { metalness: 0.85, roughness: 0.32, clearcoat: 0.3 });
  const dark = phys('#3a2a1a', { metalness: 0.6, roughness: 0.45 });
  mesh(new THREE.CylinderGeometry(0.11, 0.12, 0.035, 24), brass, 0, 0.0175, 0, { parent: L });
  mesh(new THREE.CylinderGeometry(0.095, 0.11, 0.02, 24), dark, 0, 0.045, 0, { parent: L });
  for (let i = 0; i < 4; i++) { const a = i * Math.PI / 2 + Math.PI / 4; mesh(new THREE.BoxGeometry(0.018, 0.2, 0.018), brass, Math.cos(a) * 0.085, 0.145, Math.sin(a) * 0.085, { parent: L, rot: [0, -a, 0] }); }
  const glassMat = new THREE.MeshPhysicalMaterial({ color: '#ffe2a8', emissive: lit ? '#ffb347' : '#000000', emissiveIntensity: lit ? 1.6 * power : 0, roughness: 0.15, transparent: true, opacity: lit ? 0.92 : 0.35, transmission: 0, depthWrite: false });
  const glass = mesh(new THREE.CylinderGeometry(0.078, 0.078, 0.19, 24, 1, true), glassMat, 0, 0.145, 0, { parent: L, cast: false });
  glass.renderOrder = 2;
  if (lit) {
    const fl = mesh(new THREE.SphereGeometry(0.028, 16, 12), new THREE.MeshBasicMaterial({ color: new THREE.Color('#fff1c8').multiplyScalar(6 * power) }), 0, 0.13, 0, { parent: L, cast: false, scale: [1, 1.9, 1] });
    fl.layers.enable(1);
    mesh(new THREE.CylinderGeometry(0.012, 0.014, 0.05, 8), std('#f3ead6', 0.6), 0, 0.075, 0, { parent: L, cast: false });
  }
  mesh(new THREE.ConeGeometry(0.125, 0.085, 4, 1), brass, 0, 0.285, 0, { parent: L, rot: [0, Math.PI / 4, 0] });
  mesh(new THREE.SphereGeometry(0.022, 12, 8), brass, 0, 0.335, 0, { parent: L });
  mesh(new THREE.TorusGeometry(0.06, 0.009, 8, 24), brass, 0, 0.39, 0, { parent: L });
  if (lit) {
    const gs = glowSprite('#ffb54d', 0.9 * power, 0.55, 0, 0.15, 0, L); gs.name = 'lanternGlow';
    const gs2 = glowSprite('#ffd890', 0.35 * power, 0.9, 0, 0.14, 0, L);
    if (lights) { const pl = new THREE.PointLight('#ffad55', 1.6 * power, 7, 2); pl.position.set(0, 0.15, 0); pl.name = 'lanternLight'; L.add(pl); L.userData.light = pl; }
  }
  return L;
}

// ------------------------------------------------------------------ gnome
// opts: hat, coat, beard(bool), glasses(bool), hair (grandma curls), iris, lod (1 full, 0.5 far), lantern {lit, power}
export function makeGnome(o = {}) {
  const P = Object.assign({ hat: '#c4212b', coat: '#2f58c4', belt: '#4a2614', boots: '#3a2015', skin: '#f2b097', nose: '#ef8f7e', cheek: '#ee7d84',
    beard: true, beardColor: '#f4f0e8', glasses: false, hair: false, iris: '#3c6fb4', lod: 1, lantern: { lit: true, power: 1 }, seed: 1, hatBend: 0.32,
    lidDrop: 0.32, gaze: null, smile: false, glossy: 0.8 }, o);
  const G = new THREE.Group(); G.name = 'gnome';
  const S = P.lod >= 1 ? 1 : 0.55, seg = (n) => Math.max(8, Math.round(n * S));
  const ceramic = (c, rough = 0.42, cc = P.glossy) => phys(c, { roughness: rough, clearcoat: cc, clearcoatRoughness: 0.18 });
  const skinM = ceramic(P.skin, 0.5, P.glossy * 0.6), coatM = ceramic(P.coat, 0.5, P.glossy * 0.7), hatM = ceramic(P.hat, 0.38, P.glossy);
  const beardM = phys(P.beardColor, { roughness: 0.55, clearcoat: P.glossy * 0.4, clearcoatRoughness: 0.3, bumpMap: strandBump(), bumpScale: 1.2 });
  const bootM = ceramic(P.boots, 0.35, P.glossy), beltM = ceramic(P.belt, 0.45, P.glossy * 0.6), gold = phys('#d4a440', { metalness: 0.9, roughness: 0.3 });
  // boots
  for (const s of [-1, 1]) mesh(new THREE.SphereGeometry(1, seg(28), seg(18)), bootM, s * 0.21, 0.12, 0.08, { parent: G, scale: [0.2, 0.14, 0.3] });
  // coat body (lathe)
  const prof = [[0, 0.1], [0.5, 0.1], [0.56, 0.16], [0.53, 0.24], [0.5, 0.45], [0.48, 0.7], [0.44, 0.88], [0.36, 1.0], [0.22, 1.08], [0, 1.1]].map(([r, y]) => new THREE.Vector2(r, y));
  const body = new THREE.LatheGeometry(prof, seg(48)); body.computeVertexNormals();
  mesh(body, coatM, 0, 0, 0, { parent: G });
  mesh(new THREE.TorusGeometry(0.535, 0.03, 10, seg(48)), ceramic(shade(P.coat, 0.7), 0.5), 0, 0.165, 0, { parent: G, rot: [Math.PI / 2, 0, 0] }); // hem roll
  mesh(new THREE.CylinderGeometry(0.505, 0.51, 0.1, seg(48)), beltM, 0, 0.5, 0, { parent: G });
  mesh(rbox(0.2, 0.15, 0.05, 0.02), gold, 0, 0.5, 0.5, { parent: G });
  mesh(rbox(0.12, 0.07, 0.06, 0.01), beltM, 0, 0.5, 0.505, { parent: G });
  // arms (sleeve capsule from shoulder to hand) + hands
  const arm = (s, hand) => {
    const sh = new THREE.Vector3(s * 0.38, 0.93, 0.02), d = hand.clone().sub(sh), len = d.length();
    const sl = mesh(new THREE.CapsuleGeometry(0.13, Math.max(0.01, len - 0.18), 6, seg(16)), coatM, 0, 0, 0, { parent: G });
    sl.position.copy(sh).addScaledVector(d, 0.45); sl.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d.clone().normalize());
    mesh(new THREE.TorusGeometry(0.12, 0.035, 8, 20), ceramic(shade(P.coat, 0.75)), 0, 0, 0, { parent: G }).position.copy(sh).addScaledVector(d, 0.86);
    const hm = mesh(new THREE.SphereGeometry(0.12, seg(18), seg(12)), skinM, hand.x, hand.y, hand.z, { parent: G }); hm.scale.set(1, 1.05, 0.95);
    return hm;
  };
  const handR = new THREE.Vector3(0.36, 0.86, 0.46), handL = new THREE.Vector3(-0.42, 0.5, 0.22);
  arm(1, handR); arm(-1, handL);
  if (P.lantern) { const L = makeLantern(P.lantern); L.position.set(handR.x + 0.02, handR.y - 0.5, handR.z + 0.06); G.add(L); G.userData.lantern = L;
    // bail wire from hand to lantern ring
    mesh(new THREE.CylinderGeometry(0.006, 0.006, 0.12, 6), phys('#b8873a', { metalness: 0.8, roughness: 0.3 }), handR.x + 0.02, handR.y - 0.1, handR.z + 0.06, { parent: G, cast: false }); }
  // head
  const head = new THREE.Group(); head.position.set(0, 1.37, 0.03); G.add(head); G.userData.head = head;
  mesh(new THREE.SphereGeometry(0.42, seg(48), seg(36)), skinM, 0, 0, 0, { parent: head, scale: [1, 0.96, 0.94] });
  for (const s of [-1, 1]) mesh(new THREE.SphereGeometry(0.13, seg(20), seg(14)), ceramic(P.cheek, 0.5, P.glossy * 0.5), s * 0.22, -0.06, 0.3, { parent: head, scale: [1, 0.8, 0.62] });
  mesh(new THREE.SphereGeometry(0.155, seg(32), seg(24)), ceramic(P.nose, 0.4, P.glossy * 0.7), 0, -0.04, 0.42, { parent: head, scale: [1, 0.92, 0.88] });
  for (const s of [-1, 1]) mesh(new THREE.SphereGeometry(0.06, seg(14), seg(10)), skinM, s * 0.405, -0.02, 0.0, { parent: head, scale: [0.6, 1.2, 0.9] }); // ears
  // eyes
  const eyeM = new THREE.MeshPhysicalMaterial({ map: eyeTexture(P.iris), roughness: 0.25, clearcoat: 1, clearcoatRoughness: 0.03 });
  const eyes = [];
  for (const s of [-1, 1]) {
    const e = new THREE.Group(); e.position.set(s * 0.145, 0.085, 0.33); head.add(e);
    const ball = mesh(new THREE.SphereGeometry(0.105, seg(40), seg(28)), eyeM, 0, 0, 0, { parent: e, cast: false });
    ball.userData.isEye = true; eyes.push(ball);
    // upper lid: a shell slightly larger than the ball, cut to the top part; rotated forward to drop over the eye
    const lid = mesh(new THREE.SphereGeometry(0.113, seg(32), seg(16), 0, Math.PI * 2, 0, Math.PI * 0.5), skinM, 0, 0, 0, { parent: e });
    lid.rotation.x = P.lidDrop; lid.rotation.z = -s * 0.12;
    const low = mesh(new THREE.SphereGeometry(0.111, seg(32), seg(10), 0, Math.PI * 2, Math.PI * 0.78, Math.PI * 0.22), skinM, 0, 0, 0, { parent: e }); low.rotation.x = -0.25;
  }
  G.userData.eyes = eyes;
  G.userData.look = (worldTarget) => { for (const b of eyes) { b.parent.updateWorldMatrix(true, false); b.lookAt(worldTarget); } };
  // brows: bushy clumps
  const browM = beardM;
  for (const s of [-1, 1]) for (let k = 0; k < 4; k++) {
    const t = k / 3, b = mesh(clumpGeo(0.06 - t * 0.012, 0.11, s * 0.4, seg(14)), browM, s * (0.07 + t * 0.15), 0.21 - t * 0.02 + Math.sin(t * 3) * 0.015, 0.34 - t * 0.06, { parent: head });
    b.rotation.set(0.2, 0, s * (1.2 + t * 0.4));
  }
  if (P.smile) { const sm = new THREE.TorusGeometry(0.07, 0.014, 8, 20, Math.PI * 0.8); mesh(sm, ceramic('#a33a4a', 0.4), 0, -0.2, 0.37, { parent: head, rot: [0.2, 0, Math.PI * 1.1] }); }
  // beard + moustache
  if (P.beard) {
    const r = rng(P.seed * 7 + 3);
    const rows = [ { y: -0.12, z: 0.27, W: 0.37, n: 7, L: 0.34, R: 0.11 }, { y: -0.3, z: 0.33, W: 0.33, n: 6, L: 0.4, R: 0.12 },
                   { y: -0.5, z: 0.36, W: 0.25, n: 5, L: 0.36, R: 0.115 }, { y: -0.68, z: 0.36, W: 0.13, n: 3, L: 0.3, R: 0.1 } ];
    mesh(new THREE.SphereGeometry(1, seg(32), seg(24)), beardM, 0, -0.42, 0.24, { parent: head, scale: [0.36, 0.42, 0.2] }); // core filler
    for (const [ri, row] of rows.entries()) for (let i = 0; i < row.n; i++) {
      const th = row.n === 1 ? 0 : (i / (row.n - 1)) * 2 - 1, x = th * row.W + (r() - 0.5) * 0.03;
      const g = clumpGeo(row.R * (0.9 + r() * 0.2), row.L * (0.85 + r() * 0.3), -th * 0.35 + (r() - 0.5) * 0.25, seg(18));
      const m = mesh(g, beardM, x, row.y + (1 - th * th) * 0.04 * (ri === 0 ? -1 : 1), row.z + (1 - th * th) * 0.09 - Math.abs(th) * 0.04, { parent: head });
      m.rotation.set(-0.18 - ri * 0.05, th * 0.35, -th * 0.18);
    }
    // moustache: two swooping lobes + curled tips
    for (const s of [-1, 1]) {
      const m = mesh(clumpGeo(0.085, 0.2, 0, seg(18)), beardM, s * 0.09, -0.15, 0.44, { parent: head }); m.rotation.set(0.35, 0, s * 1.15);
      const t = mesh(clumpGeo(0.05, 0.1, s * 0.6, seg(12)), beardM, s * 0.26, -0.24, 0.38, { parent: head }); t.rotation.set(0.3, 0, s * 0.3);
    }
    // side hair below hat
    for (const s of [-1, 1]) for (let k = 0; k < 3; k++) { const m = mesh(clumpGeo(0.085, 0.2, s * 0.3, seg(14)), beardM, s * (0.36 - k * 0.02), 0.08 - k * 0.04, -0.1 - k * 0.12, { parent: head }); m.rotation.set(0, 0, s * 0.25); }
  }
  if (P.hair) { // grandma: soft grey curls at the sides and back
    const hm = phys(P.hairColor || '#d9d4e2', { roughness: 0.6, clearcoat: 0.3, bumpMap: strandBump(), bumpScale: 0.6 });
    const pts = [[-0.36, 0.0, 0.12], [0.36, 0.0, 0.12], [-0.4, -0.08, -0.08], [0.4, -0.08, -0.08], [-0.3, -0.12, -0.28], [0.3, -0.12, -0.28], [0, -0.1, -0.38], [-0.16, -0.16, -0.36], [0.16, -0.16, -0.36]];
    for (const [x, y, z] of pts) mesh(new THREE.TorusGeometry(0.065, 0.045, 10, seg(18)), hm, x, y, z, { parent: head, rot: [Math.random() * 0.5, Math.atan2(x, z), 0.3] });
  }
  if (P.glasses) { // round gold glasses resting low on the nose
    const gm = phys('#d8b04a', { metalness: 0.9, roughness: 0.25 });
    const lensM = new THREE.MeshPhysicalMaterial({ color: '#ffffff', roughness: 0.05, transparent: true, opacity: 0.12, clearcoat: 1, depthWrite: false });
    const gl = new THREE.Group(); gl.position.set(0, 0.02, 0.49); gl.rotation.x = 0.12; head.add(gl);
    for (const s of [-1, 1]) { mesh(new THREE.TorusGeometry(0.12, 0.013, 10, 40), gm, s * 0.15, 0, -0.045 * 1, { parent: gl, cast: false });
      mesh(new THREE.CircleGeometry(0.115, 32), lensM, s * 0.15, 0, -0.045, { parent: gl, cast: false });
      const arm = mesh(new THREE.CylinderGeometry(0.009, 0.009, 0.5, 6), gm, s * 0.29, 0.02, -0.29, { parent: gl, cast: false }); arm.rotation.set(Math.PI / 2, 0, 0); }
    const br = mesh(new THREE.TorusGeometry(0.045, 0.012, 8, 16, Math.PI), gm, 0, 0.0, -0.03, { parent: gl, cast: false });
    G.userData.glasses = gl;
  }
  // hat: tall cone with a soft droop toward the back, rolled brim
  const hat = new THREE.Group(); hat.position.set(0, 0.14, -0.02); hat.rotation.x = -0.16; head.add(hat);
  const hp = []; const HH = P.hatH || 1.45;
  for (let i = 0; i <= 24; i++) { const t = i / 24; hp.push(new THREE.Vector2(0.47 * Math.pow(1 - t, 0.82) * (1 + 0.05 * Math.sin(t * 3.1)), t * HH)); }
  const hg = new THREE.LatheGeometry(hp, seg(56)), pp = hg.attributes.position;
  for (let i = 0; i < pp.count; i++) { const y = pp.getY(i), t = y / HH; let x = pp.getX(i), z = pp.getZ(i);
    const fold = 1 + 0.035 * Math.sin(Math.atan2(z, x) * 5 + t * 4) * Math.sin(t * Math.PI);
    x *= fold; z *= fold; z -= P.hatBend * t * t * t * HH; x += P.hatBend * 0.25 * t * t * t * HH;
    pp.setXYZ(i, x, y - P.hatBend * 0.35 * t * t * t * t * HH, z); }
  hg.computeVertexNormals(); mesh(hg, hatM, 0, 0, 0, { parent: hat });
  mesh(new THREE.TorusGeometry(0.465, 0.045, 12, seg(56)), hatM, 0, 0.02, 0, { parent: hat, rot: [Math.PI / 2, 0, 0] });
  if (P.hatDots) { const dm = ceramic(P.hatDots, 0.4); const rr = rng(5); for (let i = 0; i < 14; i++) { const t = 0.1 + rr() * 0.6, a = rr() * 6.28, rad = 0.47 * Math.pow(1 - t, 0.82) * 1.01;
      const dz = -P.hatBend * t * t * t * HH; mesh(new THREE.SphereGeometry(0.035 * (1 - t * 0.6), 10, 8), dm, Math.cos(a) * rad + P.hatBend * 0.25 * t * t * t * HH, t * HH, Math.sin(a) * rad + dz, { parent: hat, scale: [1, 1, 0.4], rot: [0, -a + Math.PI / 2, 0] }); } }
  G.userData.height = 1.37 + 0.14 + HH * 0.92;
  return G;
}
function shade(hex, k) { const c = new THREE.Color(hex); c.multiplyScalar(k); return '#' + c.getHexString(); }

// ------------------------------------------------------------------ R6 kid
// Classic R6: torso 2x2x1, arms/legs 1x2x1, rounded-cylinder head 1.2. Face is a 2D decal.
function robloxHeadGeo() {
  const p = [], r = 0.6, h = 0.6, b = 0.22;
  p.push(new THREE.Vector2(0, -h));
  for (let i = 0; i <= 8; i++) { const a = -Math.PI / 2 + i / 8 * Math.PI / 2; p.push(new THREE.Vector2(r - b + Math.cos(a) * b, -h + b + Math.sin(a) * b)); }
  for (let i = 0; i <= 8; i++) { const a = i / 8 * Math.PI / 2; p.push(new THREE.Vector2(r - b + Math.cos(a) * b, h - b + Math.sin(a) * b)); }
  p.push(new THREE.Vector2(0, h));
  const g = new THREE.LatheGeometry(p, 48); g.computeVertexNormals(); return g;
}
export function faceTexture(kind = 'wonder', freckles = true) {
  const W = 1024, H = 512, c = canvas(W, H), g = c.getContext('2d');
  // canvas maps onto a 150deg front band of the head; x centre = W/2
  const cx = W / 2, ey = H * 0.42;
  g.lineCap = 'round'; g.lineJoin = 'round';
  const eye = (x, y, rx, ry) => { g.fillStyle = '#0b0b0f'; g.beginPath(); g.ellipse(x, y, rx, ry, 0, 0, 6.28); g.fill(); g.fillStyle = '#ffffff'; g.beginPath(); g.ellipse(x - rx * 0.32, y - ry * 0.42, rx * 0.34, ry * 0.22, 0, 0, 6.28); g.fill(); };
  if (kind === 'wonder' || kind === 'soft') {
    eye(cx - 95, ey, 30, 44); eye(cx + 95, ey, 30, 44);
    g.strokeStyle = '#2a1408'; g.lineWidth = 14; // raised brows
    g.beginPath(); g.moveTo(cx - 140, ey - 82); g.quadraticCurveTo(cx - 100, ey - 112, cx - 55, ey - 92); g.stroke();
    g.beginPath(); g.moveTo(cx + 55, ey - 92); g.quadraticCurveTo(cx + 100, ey - 112, cx + 140, ey - 82); g.stroke();
    if (kind === 'wonder') { g.fillStyle = '#3a0d12'; g.beginPath(); g.ellipse(cx, ey + 125, 22, 27, 0, 0, 6.28); g.fill(); g.fillStyle = '#b8343f'; g.beginPath(); g.ellipse(cx, ey + 133, 12, 11, 0, 0, 6.28); g.fill(); }
    else { g.strokeStyle = '#2a0d0a'; g.lineWidth = 12; g.beginPath(); g.moveTo(cx - 48, ey + 112); g.quadraticCurveTo(cx, ey + 150, cx + 48, ey + 112); g.stroke(); }
  }
  if (freckles) { g.fillStyle = 'rgba(150,60,40,0.55)'; const r = rng(4); for (const s of [-1, 1]) for (let i = 0; i < 7; i++) { g.beginPath(); g.arc(cx + s * (120 + r() * 70), ey + 65 + r() * 35, 5 + r() * 3, 0, 6.28); g.fill(); } }
  const t = tex(c, { wrap: false }); return t;
}
// shirt/hoodie front texture
function hoodieTexture(base = '#d9a52c') {
  const kn = knitTextures(base, 30).map, W = 512, c = canvas(W, W), g = c.getContext('2d');
  g.drawImage(kn, 0, 0, W, W); g.drawImage(kn, 0, 0, W / 2, W / 2); // fleece
  g.strokeStyle = 'rgba(70,40,5,0.45)'; g.lineWidth = 6; g.fillStyle = 'rgba(0,0,0,0.06)';
  g.beginPath(); g.moveTo(110, 300); g.lineTo(402, 300); g.lineTo(440, 440); g.lineTo(72, 440); g.closePath(); g.fill(); g.stroke(); // kangaroo pocket
  g.fillStyle = 'rgba(80,45,10,0.5)'; g.fillRect(0, 470, W, 42); // ribbed hem
  g.strokeStyle = 'rgba(90,50,10,0.35)'; g.lineWidth = 2; for (let x = 0; x < W; x += 10) { g.beginPath(); g.moveTo(x, 472); g.lineTo(x, 512); g.stroke(); }
  g.strokeStyle = '#f2ead8'; g.lineWidth = 7; g.beginPath(); g.moveTo(215, 20); g.lineTo(205, 170); g.stroke(); g.beginPath(); g.moveTo(297, 20); g.lineTo(307, 170); g.stroke(); // drawstrings
  g.fillStyle = '#c9c1ae'; g.fillRect(199, 168, 14, 22); g.fillRect(301, 168, 14, 22);
  g.strokeStyle = 'rgba(80,45,10,0.4)'; g.lineWidth = 8; g.beginPath(); g.moveTo(150, 0); g.quadraticCurveTo(256, 90, 362, 0); g.stroke(); // neck
  return tex(c, { wrap: false });
}
function pyjamaTexture(base = '#7d8ee8', star = '#f6e7a2') {
  const W = 256, c = paint(W, W, (u, v) => { const s = 0.92 + 0.08 * fbm(u * 10, v * 10, 3, 10, 2); const st = (Math.floor(u * 8) % 2) ? 1 : 0.9; const b = new THREE.Color(base); return [b.r * 255 * s * st, b.g * 255 * s * st, b.b * 255 * s * st]; });
  const g = c.getContext('2d'), r = rng(8); g.fillStyle = star;
  for (let i = 0; i < 14; i++) { const x = r() * W, y = r() * W, R = 7 + r() * 4; g.beginPath(); for (let k = 0; k < 10; k++) { const a = k * Math.PI / 5 - Math.PI / 2, rr = k % 2 ? R * 0.45 : R; g.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); } g.closePath(); g.fill(); }
  return tex(c);
}
export function makeKid(o = {}) {
  const P = Object.assign({ skin: '#e9a27c', hoodie: '#d9a52c', pj: '#7d8ee8', hair: '#5a3418', face: 'wonder' }, o);
  const K = new THREE.Group(); K.name = 'kid';
  const skin = std(P.skin, 0.5), hood = std(P.hoodie, 0.85, 0, { bumpMap: knitTextures(P.hoodie, 30).bump ? tex(knitTextures(P.hoodie, 30).bump, { srgb: false }) : null, bumpScale: 0.6 });
  // torso (front face carries the hoodie print). RoundedBox groups: px nx py ny pz nz
  const torsoMats = [hood, hood, hood, hood, std('#ffffff', 0.85, 0, { map: hoodieTexture(P.hoodie), color: '#ffffff' }), hood];
  const torso = new THREE.Mesh(rbox(2, 2, 1, 0.06), torsoMats); torso.position.set(0, 3, 0); torso.castShadow = torso.receiveShadow = true; K.add(torso);
  const pj = std('#ffffff', 0.8, 0, { map: pyjamaTexture(P.pj) });
  for (const s of [-1, 1]) mesh(rbox(0.98, 2, 0.98, 0.05), pj, s * 0.5, 1, 0, { parent: K });
  // arms: sleeve + cuff + hand; pivot at shoulder so poses rotate cleanly
  const arms = [];
  for (const s of [-1, 1]) { const a = new THREE.Group(); a.position.set(s * 1.5, 3.85, 0); K.add(a);
    mesh(rbox(0.98, 1.55, 0.98, 0.06), hood, 0, -0.67, 0, { parent: a });
    mesh(rbox(1.0, 0.16, 1.0, 0.05), std(shade(P.hoodie, 0.78), 0.9), 0, -1.48, 0, { parent: a });
    mesh(rbox(0.94, 0.42, 0.94, 0.06), skin, 0, -1.76, 0, { parent: a }); arms.push(a); }
  K.userData.arms = arms;
  // hood bunched behind the neck
  mesh(new THREE.TorusGeometry(0.52, 0.2, 12, 32, Math.PI * 1.25), hood, 0, 4.05, -0.05, { parent: K, rot: [Math.PI / 2, 0, -Math.PI * 0.125 + Math.PI], scale: [1, 0.85, 1] });
  mesh(new THREE.SphereGeometry(0.55, 24, 16), hood, 0, 4.25, -0.5, { parent: K, scale: [1.1, 0.75, 0.55] });
  // head
  const head = new THREE.Group(); head.position.set(0, 4.6, 0); K.add(head); K.userData.head = head;
  mesh(robloxHeadGeo(), skin, 0, 0, 0, { parent: head });
  const faceM = new THREE.MeshStandardMaterial({ map: faceTexture(P.face), transparent: true, roughness: 0.5, polygonOffset: true, polygonOffsetFactor: -2, depthWrite: false });
  const band = new THREE.CylinderGeometry(0.603, 0.603, 0.98, 64, 1, true, -Math.PI * 5 / 12, Math.PI * 10 / 12);
  mesh(band, faceM, 0, 0.02, 0, { parent: head, cast: false });
  // messy hair accessory: cap + tufts (smooth UGC style)
  const hairM = phys(P.hair, { roughness: 0.5, clearcoat: 0.25, bumpMap: strandBump(), bumpScale: 0.8 });
  mesh(new THREE.SphereGeometry(0.69, 40, 24, 0, Math.PI * 2, 0, Math.PI * 0.52), hairM, 0, 0.2, -0.03, { parent: head, scale: [1, 0.95, 1] });
  const r = rng(12);
  for (let i = 0; i < 16; i++) { const a = (i / 16) * Math.PI * 2, front = Math.cos(a - Math.PI / 2) > 0.6; // skip the face front
    const tilt = 0.5 + r() * 0.5, R = 0.17 + r() * 0.05, L = 0.32 + r() * 0.15;
    const m = mesh(clumpGeo(R, L, (r() - 0.5) * 0.4, 14), hairM, Math.sin(a) * 0.55, front ? 0.42 : 0.28 + r() * 0.1, Math.cos(a) * 0.55, { parent: head });
    m.rotation.set(Math.cos(a) * (front ? 2.0 : tilt * 1.5) + Math.PI * 0, 0, -Math.sin(a) * tilt * 1.6); if (front) m.rotation.x = 1.9 + r() * 0.3; }
  for (let i = 0; i < 6; i++) { const m = mesh(clumpGeo(0.15, 0.35, (r() - 0.5) * 0.5, 14), hairM, (r() - 0.5) * 0.7, 0.62 + r() * 0.08, (r() - 0.5) * 0.6, { parent: head }); m.rotation.set(Math.PI + (r() - 0.5) * 1.2, r() * 6, (r() - 0.5) * 1.2); }
  // fringe over forehead
  for (let i = 0; i < 4; i++) { const x = -0.33 + i * 0.22, m = mesh(clumpGeo(0.15, 0.3, (i - 1.5) * 0.15, 14), hairM, x, 0.47, 0.42, { parent: head }); m.rotation.set(0.55, 0, (i - 1.5) * 0.2); }
  return K;
}
