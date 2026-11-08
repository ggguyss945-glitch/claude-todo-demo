// Character-kit QA sheets (stills): node tools/render.js engine/kit/_chars_qa.js <outdir> times=0.5,2.5,... quality=final
// One 2 s shot per sheet (shot i starts at 2i); render each at t = 2i + 0.5. Sheets: turnaround (Grandpa, Grandma, hero), gnome turnaround
// + variants, faces, elder faces, poses, gnome close-ups (night lit / dusk unlit / blink), lineup (scale), cast in context.
import * as THREE from 'three';
import * as kit from './chars.js';

const S = kit.STUD;
const GRADE = {
  night: { temperature: -18, tint: 8, contrast: 1.05, pivot: 0.4, saturation: 1.12, shadows: '#1a1446', shadowsAmount: 0.3, highlights: '#c8c4ff', highlightsAmount: 0.25, balance: 0, outBlack: '#000000', outWhite: '#c4c3fc' },
  bedroom: { temperature: -6, tint: 14, contrast: 0.95, saturation: 1.08, shadows: '#5a1e3a', shadowsAmount: 0.35, highlights: '#e0c8f8', highlightsAmount: 0.2, outBlack: '#140507', outWhite: '#e7d4fc' },
  dusk: { temperature: 22, tint: 4, saturation: 1.15, shadows: '#2a0d18', shadowsAmount: 0.3, highlights: '#ffd2a0', highlightsAmount: 0.25, outBlack: '#0c0304', outWhite: '#f2d4b0' },
  day: { temperature: 2, saturation: 1.05, outBlack: '#0a0604', outWhite: '#f6f2e6' },
};
const BASE_POST = { toneMapping: 'aces', exposure: 1.0, aa: 'msaa', msaaSamples: 4, dither: true, bloom: { enabled: true, strength: 0.12, radius: 0.35, threshold: 1.2, knee: 0.5 },
  glow: { enabled: false }, dof: { enabled: false }, vignette: { enabled: false }, grade: { enabled: true, ...GRADE.bedroom } };

// ---------------- helpers ----------------
function label(text, h = 0.12, color = '#ffffff') {
  const c = document.createElement('canvas'); c.width = 512; c.height = 96; const g = c.getContext('2d');
  g.font = 'bold 54px sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.lineWidth = 10; g.strokeStyle = '#000'; g.strokeText(text, 256, 50); g.fillStyle = color; g.fillText(text, 256, 50);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, transparent: true, depthWrite: false, toneMapped: false })); s.scale.set(h * 512 / 96, h, 1); s.renderOrder = 20; return s;
}
function backdrop(ctx, { top = '#9a96b8', bottom = '#4e4a66', z = -4, w = 40, h = 40, y = 0 } = {}) {
  const c = document.createElement('canvas'); c.width = 8; c.height = 256; const g = c.getContext('2d'); const gr = g.createLinearGradient(0, 0, 0, 256); gr.addColorStop(0, top); gr.addColorStop(1, bottom); g.fillStyle = gr; g.fillRect(0, 0, 8, 256);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: t })); m.position.set(0, y, z); ctx.add(m); return m;
}
function studio(ctx, { grade = 'day', exposure = 1.0 } = {}) {   // neutral sheet light (judge colours); in-context sheets use P1
  ctx.add(ctx.lights.hemi('#ece8ff', '#5a4a52', 1.15));
  ctx.add(ctx.lights.sun({ color: '#fff4ea', intensity: 1.45, pos: [-6, 9, 10], target: [0, 1, 0], shadow: false }));
  ctx.post.set({ ...BASE_POST, exposure, grade: { enabled: true, ...GRADE[grade] } });
}
function headOnly(face, overlays, skin, accessories = []) {
  const head = new THREE.Group();
  head.add(new THREE.Mesh(kit.headGeo(), new THREE.MeshStandardMaterial({ color: skin, roughness: 0.52 })));
  const fm = new THREE.MeshStandardMaterial({ map: kit.faceTexture(face, overlays), transparent: true, roughness: 0.55, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2, depthWrite: false });
  const f = new THREE.Mesh(kit.faceBandGeo(), fm); f.renderOrder = 1; head.add(f);
  for (const a of accessories) kit.addAccessory(head, a);
  const root = new THREE.Group(); root.scale.setScalar(S); root.add(head); return root;
}
function nightLawn(ctx, { grade = 'night', hemi = 1.3, exposure = 1.05, ground = true } = {}) {
  const grass = ctx.tex.grass({ seed: 3, color: '#3f7a46', dark: '#24493a', light: '#6aa06a', repeat: [30, 30] });
  if (ground) { const gr = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshStandardMaterial({ ...grass.mat, roughness: 1 })); gr.rotation.x = -Math.PI / 2; gr.receiveShadow = true; ctx.add(gr); }
  const sky = ctx.tex.starSky({ seed: 9, width: 2048, stops: [[-1, '#05041a'], [0, '#1a0f3a'], [0.25, '#120a30'], [0.7, '#050318'], [1, '#020210']], stars: 2600, nebula: 0.3 });
  ctx.add(ctx.tex.skyDome(sky, { radius: 200, fog: false }));
  // a house wall far behind with warm windows (motif: lit child's window)
  const brick = ctx.tex.brick({ seed: 4, color: '#5a2f3a', mortarColor: '#8c8094', repeat: [4, 2] });
  const house = new THREE.Mesh(new THREE.BoxGeometry(9, 4.5, 4), new THREE.MeshStandardMaterial({ ...brick.mat, roughness: 0.9 })); house.position.set(0.5, 2.25, -6.5); ctx.add(house);
  const winM = new THREE.MeshStandardMaterial({ color: '#ffd9a0', emissive: '#ffb860', emissiveIntensity: 2.2 });
  for (const [x, y] of [[-1.6, 1.2], [1.4, 1.2], [-1.6, 3.2], [1.4, 3.2]]) { const w = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 1.25), winM); w.position.set(x, y, -4.49); ctx.add(w); }
  const fenceM = new THREE.MeshStandardMaterial({ color: '#e4def0', roughness: 0.7 });
  for (let i = -16; i <= 16; i++) { const p = new THREE.Mesh(new THREE.BoxGeometry(0.11, 1.1, 0.05), fenceM); p.position.set(i * 0.24, 0.55, -3.0); ctx.add(p); }
  ctx.add(ctx.lights.hemi('#8a90ff', '#241a3a', hemi));
  ctx.add(ctx.lights.sun({ color: '#b4b8ff', intensity: 1.4, pos: [-4, 6, 5], target: [0, 0.3, 0], shadow: false }));
  ctx.setFog({ color: '#06051a', density: 0.012 * 2 });
  ctx.post.set({ ...BASE_POST, exposure, grade: { enabled: true, ...GRADE[grade] } });
}
function duskLawn(ctx) {
  const grass = ctx.tex.grass({ seed: 3, color: '#4f8a3e', dark: '#2f5a30', light: '#8ab86a', repeat: [30, 30] });
  const gr = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshStandardMaterial({ ...grass.mat, roughness: 1 })); gr.rotation.x = -Math.PI / 2; gr.receiveShadow = true; ctx.add(gr);
  const sky = ctx.tex.starSky({ seed: 2, width: 1024, stops: [[-1, '#3a2a30'], [0, '#e0884a'], [0.12, '#c8705a'], [0.4, '#6a5a8a'], [1, '#2a2a5a']], stars: 0, nebula: 0 });
  ctx.add(ctx.tex.skyDome(sky, { radius: 200, fog: false }));
  ctx.add(ctx.lights.hemi('#8a7cc0', '#4a2a20', 0.9));
  ctx.add(ctx.lights.sun({ color: '#ff9a50', intensity: 2.2, pos: [-5, 1.2, 4], target: [0, 0.3, 0], shadow: true, size: 2, mapSize: 1024, radius: 3 }));
  ctx.add(ctx.lights.sun({ color: '#ffd8b0', intensity: 0.6, pos: [3, 5, 6], target: [0, 0.3, 0], shadow: false }));
  ctx.post.set({ ...BASE_POST, exposure: 1.0, bloom: { enabled: true, strength: 0.15, threshold: 1.1, radius: 0.4 }, grade: { enabled: true, ...GRADE.dusk } });
}
const look = (ctx, pos, target, fov) => ctx.camera.set({ pos, target, fov });

// ---------------- sheets ----------------
const SHEETS = {
  turnaround(ctx) {
    studio(ctx); backdrop(ctx, { z: -6, y: 3 });
    const rows = ['grandpa', 'grandma', 'hero'], yaws = [0, -40, -90];
    rows.forEach((name, r) => yaws.forEach((yaw, c) => {
      const a = kit.makeCharacter(name, { shadow: false }); a.position.set((c - 1) * 1.25, (2 - r) * 2.05, 0); a.rotation.y = yaw * Math.PI / 180; ctx.add(a);
      if (c === 0) { const l = label(name, 0.16); l.position.set(-1.25, (2 - r) * 2.05 + 1.95, 0.5); ctx.add(l); }
    }));
    look(ctx, [0, 2.95, 44], [0, 2.95, 0], 9.6);
  },
  gnomeTurn(ctx) {
    studio(ctx); backdrop(ctx, { z: -3, y: 1 });
    const yaws = [0, -40, -90, 180];
    yaws.forEach((yaw, i) => { const g = kit.makeGnome('grandpa', { shadow: false, lantern: 1 }); g.position.set((i - 1.5) * 0.42, 0.78, 0); g.rotation.y = yaw * Math.PI / 180; ctx.add(g); });
    const vars = [kit.makeGnome('grandma', { shadow: false }), kit.makePlasticGnome({ shadow: false }), kit.makeGnome('grandpaFishing', { shadow: false }), kit.makeGnome('narrator', { shadow: false })];
    vars.forEach((g, i) => { g.position.set((i - 1.5) * 0.42, 0.0, 0); g.rotation.y = -0.35; ctx.add(g); });
    const names = ['grandma', 'plastic', 'fishing', 'narrator']; names.forEach((n, i) => { const l = label(n, 0.06); l.position.set((i - 1.5) * 0.42, -0.06, 0.3); ctx.add(l); });
    look(ctx, [0, 0.62, 16], [0, 0.62, 0], 12.5);
  },
  faces(ctx) {
    studio(ctx); backdrop(ctx, { z: -3, y: 0, top: '#5f6fb8', bottom: '#3a4686' });
    kit.FACES.forEach((f, i) => { const col = i % 4, row = Math.floor(i / 4); const h = headOnly(f, {}, kit.SKIN.salmon); h.position.set((col - 1.5) * 0.58, (2 - row) * 0.66, 0); h.rotation.y = (col - 1.5) * -0.08; ctx.add(h);
      const l = label(f, 0.07); l.position.set((col - 1.5) * 0.58, (2 - row) * 0.66 - 0.3, 0.3); ctx.add(l); });
    look(ctx, [0, -0.02, 24], [0, -0.02, 0], 9.6);
  },
  elderFaces(ctx) {
    studio(ctx); backdrop(ctx, { z: -3, y: 0, top: '#5f6fb8', bottom: '#3a4686' });
    const gp = kit.CAST.grandpa, gm = kit.CAST.grandma, he = kit.CAST.hero, faces = ['neutral', 'content', 'wonder', 'shock', 'sad', 'heartfelt'];
    faces.forEach((f, i) => {
      for (const [k, c] of [[0, gp], [1, gm], [2, he]]) { const h = headOnly(f, c.faceOverlays, c.skin, c.accessories.filter((a) => a.type !== 'hood')); h.position.set((k - 1) * 0.66, (2.5 - i) * 0.6, 0); h.rotation.y = (k - 1) * -0.25; ctx.add(h); }
      const l = label(f, 0.07); l.position.set(0, (2.5 - i) * 0.6 - 0.24, 0.4); ctx.add(l);
    });
    look(ctx, [0, 0.0, 26], [0, 0.0, 0], 8.4);
  },
  poses(ctx) {
    studio(ctx); backdrop(ctx, { z: -6, y: 3 });
    const list = ['stand', 'lookUp', 'point', 'hold', 'kneel', 'carry', 'run', 'sit', 'wave', 'shocked', 'sad', 'walk'];
    const who = ['grandpa', 'grandma', 'hero'];
    list.forEach((p, i) => { const col = i % 4, row = Math.floor(i / 4); const a = kit.makeCharacter(who[i % 3], { shadow: false, face: p === 'shocked' ? 'shock' : p === 'sad' ? 'sad' : p === 'wave' ? 'grin' : 'neutral' });
      kit.setPose(a, kit.POSES[p]); a.position.set((col - 1.5) * 1.3, (1 - row) * 2.25, 0); a.rotation.y = -0.45; ctx.add(a);
      const l = label(p, 0.13); l.position.set((col - 1.5) * 1.3, (1 - row) * 2.25 - 0.18, 0.6); ctx.add(l); });
    look(ctx, [0, 0.62, 64], [0, 0.62, 0], 9.0);
  },
  gnomeCU(ctx) {
    nightLawn(ctx);
    const g = kit.makeGnome('grandpa', { lantern: 1, lanternLight: true }); g.rotation.y = 0.18; ctx.add(g);
    kit.setLantern(g, 1); kit.setGnomeGaze(g, 4, 3);
    look(ctx, [0.15, 0.2, 1.4], [0.0, 0.3, 0], 38);
  },
  gnomeCUdusk(ctx) {
    duskLawn(ctx);
    const g = kit.makeGnome('grandpa', { lantern: 0 }); g.rotation.y = -0.25; ctx.add(g);
    look(ctx, [-0.08, 0.24, 0.95], [0.0, 0.33, 0], 38);
  },
  gnomeBlink(ctx) {
    nightLawn(ctx);
    const g = kit.makeGnome('grandpa', { lantern: 1, lanternLight: true }); g.rotation.y = 0.18; ctx.add(g); kit.setLantern(g, 1); kit.setGnomeLids(g, 1);
    look(ctx, [0.05, 0.27, 0.75], [0.0, 0.31, 0], 30);
  },
  lineup(ctx) {
    nightLawn(ctx, { hemi: 1.4, exposure: 1.1 });
    const a = kit.makeCharacter('grandpa'); a.position.set(-1.05, 0, -0.2); a.rotation.y = 0.3; ctx.add(a);
    const gs = [kit.makeGnome('grandpa', { lantern: 1 }), kit.makePlasticGnome(), ...[0, 1, 2, 3, 4, 5, 6, 7].map((i) => kit.makeFamilyGnome(i))];
    gs.forEach((g, i) => { const row = i < 5 ? 0 : 1, col = i < 5 ? i : i - 5; g.position.set(-0.45 + col * 0.42 + row * 0.2, 0, row * -0.75 + 0.2); g.rotation.y = 0.1 - col * 0.06; ctx.add(g); if (i === 0) kit.setLantern(g, 1); });
    look(ctx, [-0.05, 1.0, 8.6], [-0.05, 0.62, 0], 30);
  },
  cast(ctx) {
    nightLawn(ctx, { hemi: 1.3, exposure: 1.08 });
    const gp = kit.makeCharacter('grandpa', { face: 'content' }); gp.position.set(-0.5, 0, -0.7); gp.rotation.y = 0.35; kit.setPose(gp, kit.POSES.idle); ctx.add(gp);
    const gm = kit.makeCharacter('grandma', { face: 'neutral' }); gm.position.set(0.55, 0, -0.85); gm.rotation.y = -0.3; kit.setPose(gm, { armLx: 30, armRx: 30, armLz: -8, armRz: -8 }); ctx.add(gm);
    const g = kit.makeGnome('grandpa', { lantern: 1, lanternLight: true }); g.position.set(0.05, 0, 0.35); g.rotation.y = 0.05; ctx.add(g); kit.setLantern(g, 1);
    look(ctx, [0.0, 0.62, 3.2], [0.0, 0.85, 0], 50);
  },
};
SHEETS.gnomeNeutral = (ctx) => {
  ctx.add(ctx.lights.hemi('#f0ecff', '#6a5a60', 1.1));
  ctx.add(ctx.lights.sun({ color: '#fff4e8', intensity: 1.6, pos: [-3, 5, 6], target: [0, 0.4, 0], shadow: false }));
  ctx.post.set({ ...BASE_POST, exposure: 1.0, grade: { enabled: true, ...GRADE.day } });
  backdrop(ctx, { z: -3, y: 0.5, top: '#9a96b8', bottom: '#5a566e' });
  const g = kit.makeGnome('grandpa', { lantern: 1, shadow: false }); g.rotation.y = 0.3; ctx.add(g); kit.setLantern(g, 1);
  const g2 = kit.makeGnome('grandpa', { lantern: 0, shadow: false }); g2.position.set(0.5, 0, -0.4); g2.rotation.y = -0.9; ctx.add(g2);
  look(ctx, [0.1, 0.5, 1.6], [0.12, 0.38, 0], 36);
};
SHEETS.gnomeECU = (ctx) => {
  ctx.add(ctx.lights.hemi('#f0ecff', '#6a5a60', 1.1));
  ctx.add(ctx.lights.sun({ color: '#fff4e8', intensity: 1.6, pos: [-3, 5, 6], target: [0, 0.3, 0], shadow: false }));
  ctx.post.set({ ...BASE_POST, exposure: 1.0, grade: { enabled: true, ...GRADE.day } });
  backdrop(ctx, { z: -3, y: 0.5, top: '#9a96b8', bottom: '#5a566e' });
  const g = kit.makeGnome('grandpa', { lantern: 1, shadow: false }); g.rotation.y = 0.35; ctx.add(g); kit.setLantern(g, 1);
  look(ctx, [0.06, 0.29, 0.62], [0.02, 0.3, 0], 34);
};
// API smoke test (update(t) path): pose-to-pose, walk cycle, instant face swaps on ctx.instance() clones, gnome blink,
// stony head turn, lantern light-up. Stills at t = 0.25 / 0.5 (blink frame) / 1.5.
SHEETS.animTest = { build(ctx) {
  studio(ctx); backdrop(ctx, { z: -4, y: 1 });
  const A = ctx.instance('qaGrandpa', () => kit.makeCharacter('grandpa')), B = ctx.instance('qaGrandpa', () => kit.makeCharacter('grandpa'));
  A.position.set(-0.45, 0, 0); B.position.set(0.45, 0, -0.3); ctx.add(A, B);
  const g = kit.makeGnome('grandpa', { lantern: 0, lanternLight: true }); g.position.set(0.05, 0, 0.6); ctx.add(g);
  ctx.shared.qa = { A, B, g };
  look(ctx, [0, 0.9, 4.2], [0, 0.75, 0], 40);
}, update(ctx, t) {
  const { A, B, g } = ctx.shared.qa;
  kit.setPose(A, { ...kit.poseAt(t, [[0, 'stand'], [0.3, 'point'], [1.0, 'wave']], 0.15, 'outBack'), ...(t > 1.15 ? kit.waveCycle(t) : {}) });
  kit.setFace(A, kit.faceAt(t, [[0, 'neutral'], [0.3, 'wonder'], [1.0, 'grin']]));
  kit.setPose(B, kit.walkCycle(t)); kit.setFace(B, 'sad');
  kit.setGnomeLids(g, kit.gnomeBlink(t, [0.5]));
  kit.setGnomeHead(g, kit.gnomeHeadTurn(t, 0.6, 1.0, 0, 35));
  const L = kit.lanternLightUp(t, 1.2); kit.setLantern(g, L.level * kit.lanternFlicker(t), { halo: L.halo });
  kit.gnomeIdle(g, t);
} };
SHEETS.extraCast = (ctx) => {
  studio(ctx); backdrop(ctx, { z: -6, y: 2 });
  const names = ['theo', 'mom', 'dad', 'grandpaFlashback', 'heroOld'];
  names.forEach((n, i) => { for (const [r, yaw] of [[0, 0], [1, -35]]) { const a = kit.makeCharacter(n, { shadow: false, face: r ? 'content' : 'neutral' }); a.position.set((i - 2) * 1.1, (1 - r) * 2.1, 0); a.rotation.y = yaw * Math.PI / 180; ctx.add(a); }
    const l = label(n, 0.12); l.position.set((i - 2) * 1.1, -0.15, 0.5); ctx.add(l); });
  const hats = [{ type: 'hat', style: 'flatCap', color: '#5a4a3a' }, { type: 'hat', style: 'beanie', color: '#c8323a', band: '#f2ece0' }, { type: 'hat', style: 'fishing', color: '#6f7342' }];
  hats.forEach((h, i) => { const a = kit.makeCharacter('grandpa', { shadow: false, accessories: [{ type: 'hair', style: 'grandpa', color: '#eeeaf0' }, { type: 'moustache', color: '#eeeaf0' }, h] }); a.position.set((i - 1) * 1.3, -2.6, 0); a.rotation.y = -0.4; ctx.add(a); });
  look(ctx, [0, 0.75, 60], [0, 0.75, 0], 8.8);
};
const ORDER = ['gnomeNeutral', 'gnomeECU', 'turnaround', 'gnomeTurn', 'faces', 'elderFaces', 'poses', 'gnomeCU', 'gnomeCUdusk', 'gnomeBlink', 'lineup', 'cast', 'animTest', 'extraCast'];
export default {
  name: 'chars_qa', fps: 60, width: 1080, height: 1920, seed: 'chars-qa',
  quality: { shadows: 'pcfsoft' },
  shots: ORDER.map((n, i) => (typeof SHEETS[n] === 'function' ? { name: n, start: i * 2, end: i * 2 + 2, build(ctx) { SHEETS[n](ctx); }, update() {} } : { name: n, start: i * 2, end: i * 2 + 2, ...SHEETS[n] })),
};
