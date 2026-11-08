// Demo episode (4 s): a night lawn, a blocky R6 placeholder avatar holding a glowing lantern, soft shadows, fog and
// ground mist, slow camera push, DOF on the subject, bloom halo, dreamy glow, vignette and a lavender night grade.
// Two shots share one cached set to exercise shot switching. Units: metres (1 Roblox stud ~ 0.32 m).
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

const S = 0.32; // stud
const std = (color, o = {}) => new THREE.MeshStandardMaterial({ color, roughness: 0.55, metalness: 0, ...o });

function faceTexture() {
  const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d');
  g.fillStyle = '#111'; for (const x of [88, 168]) { g.beginPath(); g.ellipse(x, 104, 15, 26, 0, 0, Math.PI * 2); g.fill(); }
  g.strokeStyle = '#111'; g.lineWidth = 12; g.lineCap = 'round'; g.beginPath(); g.arc(128, 128, 62, 0.22 * Math.PI, 0.78 * Math.PI); g.stroke();
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
}

// Placeholder R6 avatar: torso 2x2x1, arms/legs 1x2x1, rounded head, decal face. Limbs pivot at shoulders/hips.
function buildAvatar() {
  const root = new THREE.Group(); root.name = 'avatar';
  const box = (w, h, d) => new RoundedBoxGeometry(w * S, h * S, d * S, 3, 0.06 * S);
  const skin = std('#f5cd30', { roughness: 0.5 }), shirt = std('#2f7fd0', { roughness: 0.6 }), pants = std('#5e7f2f', { roughness: 0.65 });
  const mesh = (g, m) => { const o = new THREE.Mesh(g, m); o.castShadow = true; o.receiveShadow = true; return o; };
  const torso = mesh(box(2, 2, 1), shirt); torso.position.y = 3 * S; root.add(torso);
  const head = new THREE.Group(); head.position.y = 4 * S; root.add(head);
  const hm = mesh(new RoundedBoxGeometry(1.25 * S, 1.2 * S, 1.2 * S, 4, 0.3 * S), skin); hm.position.y = 0.62 * S; head.add(hm);
  const face = new THREE.Mesh(new THREE.PlaneGeometry(1.1 * S, 1.1 * S), new THREE.MeshStandardMaterial({ map: faceTexture(), transparent: true, roughness: 0.6, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2 }));
  face.position.set(0, 0.6 * S, 0.601 * S); head.add(face);
  const limb = (x, y, m, name) => { const g = new THREE.Group(); g.name = name; g.position.set(x * S, y * S, 0); const o = mesh(box(1, 2, 1), m); o.position.y = -1 * S; g.add(o); root.add(g); return g; };
  const armL = limb(-1.5, 4, skin, 'armL'), armR = limb(1.5, 4, skin, 'armR'), legL = limb(-0.5, 2, pants, 'legL'), legR = limb(0.5, 2, pants, 'legR');
  armR.children[0].castShadow = false; // the lantern hangs from this arm: don't let it shadow the torso
  root.userData.parts = { torso, head, armL, armR, legL, legR };
  return root;
}

function buildLantern(ctx) {
  const g = new THREE.Group(); g.name = 'lantern';
  const metal = std('#2a2733', { roughness: 0.35, metalness: 0.6 });
  const glass = new THREE.MeshStandardMaterial({ color: '#ffe7b0', emissive: '#ffb347', emissiveIntensity: 9, roughness: 0.2 });
  const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.085, 0.05, 12), metal); cap.position.y = 0.12; g.add(cap);
  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.085, 0.085, 0.03, 12), metal); base.position.y = -0.09; g.add(base);
  const core = new THREE.Mesh(new THREE.CylinderGeometry(0.065, 0.065, 0.17, 16), glass); core.position.y = 0.015; g.add(core);
  for (let k = 0; k < 4; k++) { const bar = new THREE.Mesh(new THREE.BoxGeometry(0.012, 0.2, 0.012), metal); const a = (k / 4) * Math.PI * 2 + Math.PI / 4; bar.position.set(Math.cos(a) * 0.072, 0.015, Math.sin(a) * 0.072); g.add(bar); }
  const handle = new THREE.Mesh(new THREE.TorusGeometry(0.045, 0.007, 6, 16, Math.PI), metal); handle.position.y = 0.15; g.add(handle);
  g.traverse((o) => { if (o.isMesh) o.castShadow = false; });
  // halo card: soft additive glow that reads as Roblox-style light bloom even before post bloom
  const halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: ctx.tex.radialGlow({ falloff: 2.6 }), color: '#ffb35c', blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, opacity: 0.55 }));
  halo.scale.setScalar(0.9); halo.position.y = 0.015; g.add(halo);
  const light = ctx.lights.point({ color: '#ffb766', intensity: 3.2, pos: [0, 0.015, 0], distance: 0, decay: 2, shadow: true, mapSize: 512, bias: -0.004, radius: 6, near: 0.08, far: 12 });
  g.add(light); g.userData.light = light; g.userData.halo = halo; g.userData.core = glass;
  return g;
}

function pine(ctx, h, rng) {
  const g = new THREE.Group(); const leaf = std('#1c3a34', { roughness: 0.9 }), bark = std('#3a2418', { roughness: 0.95 });
  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.08 * h, 0.12 * h, 0.35 * h, 7), bark); trunk.position.y = 0.17 * h; g.add(trunk);
  for (let k = 0; k < 4; k++) { const c = new THREE.Mesh(new THREE.ConeGeometry((0.42 - k * 0.08) * h, 0.38 * h, 8), leaf); c.position.y = (0.38 + k * 0.2) * h; c.rotation.y = rng() * 6; g.add(c); }
  g.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  return g;
}

// The shared set (cached per worker; shots get transform-clones).
function buildSet(ctx) {
  const { tex } = ctx; const set = new THREE.Group(); set.name = 'lawnSet'; const rng = ctx.rngFor('lawnSet');
  const grass = tex.grass({ seed: 3, color: '#3f7a46', dark: '#24493a', light: '#6aa06a', repeat: [26, 26] });
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), new THREE.MeshStandardMaterial({ ...grass.mat, roughness: 1 }));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; set.add(ground);
  // picket fence behind the subject
  const fenceM = std('#e4def0', { roughness: 0.7 });
  for (let i = -14; i <= 14; i++) { const p = new THREE.Mesh(new RoundedBoxGeometry(0.11, 0.9, 0.05, 2, 0.015), fenceM); p.position.set(i * 0.22, 0.45, -3.2); p.castShadow = p.receiveShadow = true; set.add(p); }
  for (const y of [0.3, 0.68]) { const r = new THREE.Mesh(new THREE.BoxGeometry(6.4, 0.07, 0.04), fenceM); r.position.set(0, y, -3.24); r.receiveShadow = true; set.add(r); }
  // pines and a house far away in the fog, with warm windows
  for (const [x, z, h] of [[-3.2, -5.5, 3.2], [3.6, -6.5, 3.8], [-6.5, -10, 4.4], [7, -12, 5], [1.5, -14, 4.6]]) { const t = pine(ctx, h, rng); t.position.set(x, 0, z); set.add(t); }
  const brick = tex.brick({ seed: 4, color: '#5a2f3a', mortarColor: '#8c8094', repeat: [3, 2] });
  const house = new THREE.Mesh(new THREE.BoxGeometry(7, 4, 5), new THREE.MeshStandardMaterial({ ...brick.mat, roughness: 0.9 })); house.position.set(-2, 2, -18); house.receiveShadow = true; set.add(house);
  const roof = new THREE.Mesh(new THREE.ConeGeometry(5.2, 2.2, 4, 1), std('#2b2638', { roughness: 0.8 })); roof.position.set(-2, 5.1, -18); roof.rotation.y = Math.PI / 4; roof.scale.set(1, 1, 0.75); set.add(roof);
  const winM = new THREE.MeshStandardMaterial({ color: '#ffd9a0', emissive: '#ffb860', emissiveIntensity: 2.2 });
  for (const [x, y] of [[-4, 1.4], [0, 1.4], [-4, 3], [0, 3]]) { const w = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 1.1), winM); w.position.set(x, y, -15.49); set.add(w); }
  // night sky (stays visible through the fog)
  const sky = tex.starSky({ seed: 9, width: 2048, stops: [[-1, '#05041a'], [0, '#2a2766'], [0.25, '#13113f'], [0.7, '#07061f'], [1, '#020210']], stars: 3000, nebula: 0.35 });
  set.add(tex.skyDome(sky, { radius: 300, fog: false }));
  return set;
}

// Shared light rig + post look for both shots.
function nightRig(ctx) {
  const { scene, lights } = ctx;
  ctx.add(lights.hemi('#8f8ff0', '#3a2448', 1.1));
  ctx.add(lights.sun({ color: '#aab2ff', intensity: 1.7, pos: [-5, 8, 6], target: [0, 0, -1], size: 6, mapSize: 2048, radius: 4, bias: -0.0005, normalBias: 0.03 }));
  ctx.setFog({ color: '#1d1b45', density: 0.04, height: { base: 0, falloff: 3.0, density: 0.16, color: '#6c6cc0', max: 0.55 } });
  ctx.post.set({
    toneMapping: 'aces', exposure: 1.15,
    bloom: { enabled: true, strength: 0.55, radius: 0.62, threshold: 1.1, knee: 0.6 },
    glow: { enabled: true, amount: 0.16, radius: 0.8, mode: 'screen', tint: '#c9b8ff' },
    vignette: { enabled: true, amount: 0.32, size: 0.42, softness: 0.65, roundness: 0.5, color: '#07051a' },
    grade: { enabled: true, temperature: -6, tint: 10, contrast: 1.05, saturation: 1.12, lift: [0.035, 0.015, 0.06], gain: [1.0, 0.97, 1.04],
      shadows: '#4b2a6e', shadowsAmount: 0.45, highlights: '#ffd2b0', highlightsAmount: 0.3, balance: 0.05, outWhite: '#efe4ff' },
    dof: { enabled: true, focus: 'auto', aperture: 16, maxBlur: 22, range: 0.15, quality: 'med' },
  });
}

function posePlaceholder(av, t, rng) {
  const P = av.userData.parts;
  const breath = Math.sin(t * 2 * Math.PI * 0.28);
  P.torso.scale.set(1 + breath * 0.008, 1 + breath * 0.012, 1 + breath * 0.008);
  P.head.rotation.y = 0.25 * Math.sin(t * 0.6) - 0.1; P.head.rotation.x = -0.05;
  P.armR.rotation.set(-0.42 + Math.sin(t * 1.3) * 0.015, 0, 0.06); P.armL.rotation.set(0.05, 0, -0.06);
}

function sparkles(ctx, n, center, spread) {
  const g = new THREE.Group(); const map = ctx.tex.sparkle({ points: 6, sharpness: 16 }); const rng = ctx.rng.fork('spark');
  for (let i = 0; i < n; i++) {
    const s = new THREE.Sprite(new THREE.SpriteMaterial({ map, color: rng() < 0.5 ? '#e9dcff' : '#ffe2c4', blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }));
    s.userData = { p: new THREE.Vector3(center[0] + (rng() - 0.5) * spread[0], center[1] + (rng() - 0.5) * spread[1], center[2] + (rng() - 0.5) * spread[2]), ph: rng() * 6.28, sp: 0.6 + rng() * 0.8, sz: 0.035 + rng() * 0.04, dr: new THREE.Vector3((rng() - 0.5) * 0.12, 0.05 + rng() * 0.1, (rng() - 0.5) * 0.1) };
    g.add(s);
  }
  g.userData.update = (t) => g.children.forEach((s) => { const d = s.userData; s.position.copy(d.p).addScaledVector(d.dr, t); const tw = 0.5 + 0.5 * Math.sin(t * d.sp * 3 + d.ph); s.scale.setScalar(d.sz * (0.6 + 0.6 * tw)); s.material.opacity = 0.35 + 0.65 * tw; s.material.rotation = d.ph + t * 0.3; });
  return g;
}

function stage(ctx) {
  ctx.add(ctx.instance('lawnSet', buildSet));
  nightRig(ctx);
  const av = buildAvatar(); av.position.set(0, 0, 0); av.rotation.y = 0.35; ctx.add(av);
  const lantern = buildLantern(ctx); av.userData.parts.armR.add(lantern); lantern.position.set(0, -2.0 * S - 0.12, 0.0); lantern.rotation.x = 0.42;
  const sp = sparkles(ctx, 10, [0.2, 1.1, 0.6], [2.6, 1.4, 1.6]); ctx.add(sp);
  return { av, lantern, sp };
}

export default {
  name: 'demo', fps: 60, width: 1080, height: 1920, seed: 'demo-1',
  quality: { shadows: 'pcfsoft' },
  shots: [
    {
      name: 'wide_push', start: 0, end: 2.4,
      build(ctx) {
        ctx.shared.demo = stage(ctx);
        ctx.camera.set({ pos: [0.55, 1.05, 4.3], target: [0.05, 1.0, 0], fov: 42 })
          .push(0.19, { mode: 'dolly' }).handheld({ rot: 0.25, pos: 0.006, freq: 0.5 });
        ctx.camera.focus(ctx.shared.demo.av.userData.parts.head);
      },
      update(ctx, t) {
        const { av, lantern, sp } = ctx.shared.demo;
        posePlaceholder(av, t, ctx.rng); sp.userData.update(t);
        const flick = 1 + 0.06 * ctx.anim.wobble(t, 'flicker', 7, 1) ; lantern.userData.light.intensity = 3.2 * flick; lantern.userData.core.emissiveIntensity = 9 * flick;
      },
    },
    {
      name: 'close_low', start: 2.4, end: 4.0,
      build(ctx) {
        ctx.shared.demo = stage(ctx);
        ctx.camera.set({ pos: [1.0, 0.55, 2.35], target: [0.26, 1.06, 0.05], fov: 40 })
          .push(0.19, { mode: 'zoom' }).orbit(-6).handheld({ rot: 0.2, pos: 0.004, freq: 0.5 }).shake({ t0: 0.0, dur: 0.35, rot: 0.6, pos: 0.006, freq: 16 });
        ctx.camera.focus(ctx.shared.demo.lantern);
        ctx.post.set({ dof: { aperture: 20, maxBlur: 26 }, bloom: { strength: 0.7 } });
      },
      update(ctx, t) {
        const { av, lantern, sp } = ctx.shared.demo;
        posePlaceholder(av, t + 2.4, ctx.rng); sp.userData.update(t + 2.4);
        const flick = 1 + 0.06 * ctx.anim.wobble(t + 2.4, 'flicker', 7, 1); lantern.userData.light.intensity = 3.2 * flick; lantern.userData.core.emissiveIntensity = 9 * flick;
        ctx.post.params.flash.amount = 0.35 * Math.max(0, 1 - t / 0.12); // tiny flash-in on the cut (transition test)
      },
    },
  ],
};
