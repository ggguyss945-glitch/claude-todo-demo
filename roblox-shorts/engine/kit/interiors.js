// EP01 interiors (VISUAL_BIBLE §4.1, §4.2, §4.4, §5 P2): the old bedroom (the hero at 11 -> Theo now, plus the 1960s,
// 1990s and 2010s dressings), Grandma's living room, our hall on the night of the move, and the moving-truck cab insert,
// plus their light presets (interiorDay, bedroomNight, cabNight). API: engine/kit/README_EP01.md ("SETS" section).
//
//   import * as I from '../../kit/interiors.js';
//   const room = I.grandmaRoom(ctx); ctx.add(room);                 // Group in METRES, origin on the floor
//   ctx.camera.set(room.userData.views.armchairMS).push(0.18);       // named camera anchors (metres)
//   I.interiorDay(ctx, { room });                                    // light + post preset
//
// Rooms are built in STUDS (Parts batches, one mesh per material, every surface textured) inside a root scaled by STUD,
// like the suburb kit, so cameras, lights and anchors are in metres. The bedroom is special: `bedroomRoom()` returns the
// bare room in studs (room frame: origin on the floor at the inner face of the window wall, centred on the window, +Z
// out through the window, the room at z < 0). sets_ep01.heroLot() attaches it behind the hero bungalow's front window
// (the window over Grandpa's flowerbed, A1.bed0), so the same room is seen from inside and through the glass from outside.
// Everything is seeded and cached per worker (ctx.cache); each call returns a cheap clone. Pure functions of t.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { Parts, M, texMat, signTex, boxUV, planarUV, scaleUV, trs, makeRng, hash32, persistTree, shade, STUD, FONT, glowSpriteMat, TX } from './kitlib.js';
import * as P_ from './props.js';
import { postPreset, keyLight, camBasis } from './lighting.js';
import { sky as makeSky } from './sky.js';
import { noise3 } from '../core/random.js';

const PI = Math.PI, DEG = PI / 180;
const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);

// ------------------------------------------------------------------ canvas textures + material registry (shared with sets_ep01.js)
const _tc = new Map();
const _persistTex = (t) => { t.userData.persistent = true; return t; };
// Deterministic canvas texture, cached per worker. wrap: repeat; srgb: colour texture.
export function ctex(key, w, h, draw, { wrap = false, srgb = true, mips = true } = {}) {
  if (_tc.has(key)) return _tc.get(key);
  const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d'); draw(g, w, h);
  const t = new THREE.CanvasTexture(c); if (srgb) t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  if (wrap) t.wrapS = t.wrapT = THREE.RepeatWrapping; if (!mips) { t.generateMipmaps = false; t.minFilter = THREE.LinearFilter; }
  t.needsUpdate = true; _persistTex(t); t.userData.canvas = c; _tc.set(key, t); return t;
}
export const rgbaStr = (hex, a = 1, k = 1) => { const c = new THREE.Color(hex); return `rgba(${Math.round(Math.min(255, c.r * 255 * k))},${Math.round(Math.min(255, c.g * 255 * k))},${Math.round(Math.min(255, c.b * 255 * k))},${a})`; };
export const HAND = `bold italic 1px "DejaVu Sans", "Liberation Sans", sans-serif`; // no marker font offline: bold oblique sans
const font = (px, style = 'bold') => `${style} ${px}px ${FONT}`;

const _mc = new Map();
function persistMat(m) { m.userData.persistent = true; for (const k in m) if (m[k] && m[k].isTexture) _persistTex(m[k]); return m; }
// Extended material keys (fall back to kitlib M):
//   wp:<kind>:<#c>   wallpaper (fabric | stripe | floral | roses | plain) on a plaster micro-bump, roughness 0.9
//   floor:<#c>      glossy terracotta planks (TF, roughness 0.32)        ceil:<#c>   matte plaster ceiling
//   fab:<#c>        woven fabric (duvets, curtains, pillows), 0.95      rug:<#c>    shag / carpet
//   glow:<#c>:<k>   emissive, double-sided (lamp shades, LED, screens)  gloss:<#c>  glossy painted wood / enamel (0.35)
//   tex:<name>      a decal texture registered with decalMat()           net:<#c>   translucent net curtain
export function XM(key) {
  if (_mc.has(key)) return _mc.get(key);
  const [fam, a, b] = key.split(':'); let m = null;
  switch (fam) {
    case 'wp': m = new THREE.MeshStandardMaterial({ map: wallpaperTex(a, b), normalMap: TX.plaster({ color: '#808080', bump: 1, normal: 1.6, seed: 4 }).normalMap, normalScale: new THREE.Vector2(0.7, 0.7), roughness: 0.9 }); break;
    case 'floor': m = new THREE.MeshStandardMaterial({ ...TX.woodPlanks({ color: a || '#9f3305', planks: 5, joints: 1, gap: 0.008, gapColor: '#3a1206', variation: 0.16, grain: 0.9, gloss: 0.7, seed: 8 }).mat, roughness: 0.32 }); break;
    case 'ceil': m = new THREE.MeshStandardMaterial({ ...TX.plaster({ color: a || '#b28dc0', mottle: 0.04, speckle: 0.03, seed: 5 }).mat, roughness: 0.95 }); break;
    case 'fab': m = new THREE.MeshStandardMaterial({ ...TX.fabric({ color: a || '#a93298', threads: 64, contrast: 0.16, seed: 3 }).mat, roughness: 0.95 }); break;
    case 'rug': m = new THREE.MeshStandardMaterial({ ...TX.carpet({ color: a || '#e58fc2', seed: 6, fibre: 0.45 }).mat, roughness: 1 }); break;
    case 'glow': m = new THREE.MeshBasicMaterial({ color: new THREE.Color(a || '#fffee1').multiplyScalar(parseFloat(b || '2.5')), side: THREE.DoubleSide }); break;
    case 'gloss': m = new THREE.MeshStandardMaterial({ ...TX.woodPlanks({ color: a || '#efeee9', gapColor: a || '#efeee9', planks: 3, joints: 0, gap: 0, grain: 0.25, variation: 0.02, seed: 9, normal: 0.4 }).mat, roughness: 0.35 }); break;
    case 'net': m = new THREE.MeshStandardMaterial({ map: netTex(), color: a || '#ffffff', transparent: true, opacity: 0.85, roughness: 0.9, side: THREE.DoubleSide, depthWrite: false }); break;
    case 'tex': m = null; break; // decals must be registered with decalMat() before Parts.build
    default: break;
  }
  if (!m) return M(key);
  m.name = key; persistMat(m); _mc.set(key, m); return m;
}
// Register a decal material under 'tex:<name>' (map = canvas texture). basic: unlit (screens, LEDs).
export function decalMat(name, map, { basic = false, k = 1, roughness = 0.6, transparent = false, side = THREE.FrontSide, color = '#ffffff' } = {}) {
  const key = 'tex:' + name; if (_mc.has(key)) return _mc.get(key);
  const m = basic ? new THREE.MeshBasicMaterial({ map, color: new THREE.Color(color).multiplyScalar(k), transparent, side, toneMapped: true }) : new THREE.MeshStandardMaterial({ map, color, roughness, transparent, side });
  m.name = key; persistMat(m); _mc.set(key, m); return m;
}

// ------------------------------------------------------------------ wallpapers, posters, decals (canvas, our own designs)
export function wallpaperTex(kind = 'fabric', color = '#4958a0') {
  return ctex(`wp:${kind}:${color}`, 512, 512, (g, W, H) => {
    const r = makeRng(hash32('wp', kind, color)); g.fillStyle = color; g.fillRect(0, 0, W, H);
    if (kind === 'fabric') { // TF fabric wall: fine vertical weave + faint mottling
      for (let x = 0; x < W; x += 2) { g.fillStyle = rgbaStr('#ffffff', 0.025 + 0.025 * r()); g.fillRect(x, 0, 1, H); }
      for (let y = 0; y < H; y += 3) { g.fillStyle = rgbaStr('#000000', 0.02 + 0.02 * r()); g.fillRect(0, y, W, 1); }
    } else if (kind === 'stripe') { // 1960s rose stripe: wide rose bands, thin cream pinstripes
      for (let x = 0; x < W; x += 64) { g.fillStyle = rgbaStr(color, 1, 0.82); g.fillRect(x + 20, 0, 24, H); g.fillStyle = rgbaStr('#f4e8dc', 0.9); g.fillRect(x + 4, 0, 4, H); g.fillRect(x + 56, 0, 2, H); }
      for (let y = 0; y < H; y += 32) for (let x = 0; x < W; x += 64) { g.fillStyle = rgbaStr('#f4e8dc', 0.55); g.beginPath(); g.arc(x + 32, y + 16 + ((x / 64) % 2) * 16, 3, 0, PI * 2); g.fill(); }
    } else if (kind === 'floral' || kind === 'roses') { // 1990s yellow floral / Grandma's cream roses (half-drop repeat, wraps)
      const petal = kind === 'floral' ? ['#f6f0d8', '#f29a3a', '#e85a6a'] : ['#e46a8a', '#c8486a', '#f2a0b8']; const leaf = kind === 'floral' ? '#7a9a3a' : '#6f9a5a';
      const flower = (cx, cy, s) => { for (const [dx, dy] of [[0, 0], [W, 0], [-W, 0], [0, H], [0, -H]]) { const x = cx + dx, y = cy + dy;
        g.fillStyle = leaf; for (const a of [0.6, 2.4, 4.1]) { g.beginPath(); g.ellipse(x + Math.cos(a) * s * 1.3, y + Math.sin(a) * s * 1.3, s * 0.9, s * 0.4, a, 0, PI * 2); g.fill(); }
        g.fillStyle = petal[Math.floor(r() * petal.length)]; for (let k = 0; k < 5; k++) { const a = (k / 5) * PI * 2; g.beginPath(); g.ellipse(x + Math.cos(a) * s * 0.55, y + Math.sin(a) * s * 0.55, s * 0.55, s * 0.4, a, 0, PI * 2); g.fill(); }
        g.fillStyle = kind === 'floral' ? '#c86a1a' : '#8a2a4a'; g.beginPath(); g.arc(x, y, s * 0.28, 0, PI * 2); g.fill(); } };
      for (let j = 0; j < 4; j++) for (let i = 0; i < 4; i++) flower(i * 128 + 64 + (j % 2) * 64, j * 128 + 64, 13 + r() * 5);
      for (let k = 0; k < 40; k++) { g.fillStyle = rgbaStr(leaf, 0.5); g.beginPath(); g.arc(r() * W, r() * H, 3, 0, PI * 2); g.fill(); }
    }
    // baked soft shading noise (the Roblox texture look), always last
    for (let k = 0; k < 600; k++) { g.fillStyle = rgbaStr(r() < 0.5 ? '#000000' : '#ffffff', 0.025); g.fillRect(r() * W, r() * H, 6 + r() * 20, 2 + r() * 6); }
  }, { wrap: true });
}
function netTex() { // net curtain lace: fine mesh with a scalloped hem pattern
  return ctex('netLace', 256, 256, (g, W, H) => {
    g.fillStyle = 'rgba(255,255,255,0.55)'; g.fillRect(0, 0, W, H);
    g.strokeStyle = 'rgba(255,255,255,0.95)'; g.lineWidth = 1; for (let x = 0; x < W; x += 6) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, H); g.stroke(); } for (let y = 0; y < H; y += 6) { g.beginPath(); g.moveTo(0, y); g.lineTo(W, y); g.stroke(); }
    g.fillStyle = 'rgba(255,255,255,1)'; for (let y = 32; y < H; y += 64) for (let x = 32; x < W; x += 64) { for (let k = 0; k < 6; k++) { const a = (k / 6) * PI * 2; g.beginPath(); g.ellipse(x + Math.cos(a) * 9, y + Math.sin(a) * 9, 6, 3, a, 0, PI * 2); g.fill(); } }
  }, { wrap: true });
}
// Posters (our own designs, VISUAL_BIBLE §4.4 "TO THE STARS-style"): rocket, dinosaur, planets, a band, a cat.
export function posterTex(kind = 'rocket') {
  return ctex('poster:' + kind, 256, 352, (g, W, H) => {
    const r = makeRng(hash32('poster', kind));
    const bg = { rocket: '#1b2a6a', dino: '#2f7a4a', planets: '#2a1a5a', band: '#c8402a', cat: '#e8b0c8', race: '#f2c230' }[kind] || '#1b2a6a';
    g.fillStyle = bg; g.fillRect(0, 0, W, H); g.fillStyle = '#f4f0e8'; g.fillRect(0, 0, W, 10); g.fillRect(0, H - 10, W, 10); g.fillRect(0, 0, 10, H); g.fillRect(W - 10, 0, 10, H);
    if (kind === 'rocket' || kind === 'planets') for (let k = 0; k < 40; k++) { g.fillStyle = `rgba(255,255,230,${0.4 + 0.6 * r()})`; g.beginPath(); g.arc(14 + r() * (W - 28), 14 + r() * (H - 90), 1 + r() * 2, 0, PI * 2); g.fill(); }
    g.textAlign = 'center'; g.textBaseline = 'middle';
    if (kind === 'rocket') {
      g.save(); g.translate(W / 2, H * 0.45); g.rotate(-0.35);
      g.fillStyle = '#f4f0e8'; g.beginPath(); g.moveTo(0, -95); g.quadraticCurveTo(38, -40, 30, 50); g.lineTo(-30, 50); g.quadraticCurveTo(-38, -40, 0, -95); g.fill();
      g.fillStyle = '#d83a2a'; g.beginPath(); g.moveTo(0, -95); g.quadraticCurveTo(22, -72, 26, -55); g.lineTo(-26, -55); g.quadraticCurveTo(-22, -72, 0, -95); g.fill();
      g.fillStyle = '#5ac0e8'; g.beginPath(); g.arc(0, -15, 14, 0, PI * 2); g.fill(); g.strokeStyle = '#d83a2a'; g.lineWidth = 5; g.stroke();
      g.fillStyle = '#d83a2a'; for (const s of [-1, 1]) { g.beginPath(); g.moveTo(s * 28, 20); g.lineTo(s * 52, 62); g.lineTo(s * 26, 52); g.fill(); }
      g.fillStyle = '#f2a83a'; g.beginPath(); g.moveTo(-18, 52); g.quadraticCurveTo(0, 120, 18, 52); g.fill(); g.fillStyle = '#ffe27a'; g.beginPath(); g.moveTo(-9, 52); g.quadraticCurveTo(0, 92, 9, 52); g.fill();
      g.restore(); g.fillStyle = '#ffe27a'; g.font = font(30); g.fillText('BLAST OFF!', W / 2, H - 42);
    } else if (kind === 'dino') {
      g.fillStyle = '#a8e070'; g.beginPath(); g.ellipse(W / 2, H * 0.5, 70, 42, 0, 0, PI * 2); g.fill(); g.beginPath(); g.ellipse(W / 2 + 70, H * 0.33, 24, 18, 0, 0, PI * 2); g.fill();
      g.fillRect(W / 2 + 50, H * 0.33, 22, 60); g.beginPath(); g.moveTo(W / 2 - 60, H * 0.5); g.lineTo(W / 2 - 120, H * 0.62); g.lineTo(W / 2 - 55, H * 0.58); g.fill();
      for (const x of [-40, -10, 25, 45]) g.fillRect(W / 2 + x, H * 0.55, 14, 46); g.fillStyle = '#141414'; g.beginPath(); g.arc(W / 2 + 78, H * 0.31, 4, 0, PI * 2); g.fill();
      g.fillStyle = '#f2c230'; for (let k = 0; k < 6; k++) { g.beginPath(); g.moveTo(W / 2 - 50 + k * 18, H * 0.4 + Math.abs(k - 2.5) * 4); g.lineTo(W / 2 - 41 + k * 18, H * 0.32 + Math.abs(k - 2.5) * 4); g.lineTo(W / 2 - 32 + k * 18, H * 0.4 + Math.abs(k - 2.5) * 4); g.fill(); }
      g.fillStyle = '#f4f0e8'; g.font = font(32); g.fillText('DINO CLUB', W / 2, H - 42);
    } else if (kind === 'planets') {
      g.fillStyle = '#f2a83a'; g.beginPath(); g.arc(W * 0.4, H * 0.38, 54, 0, PI * 2); g.fill(); g.strokeStyle = '#f4e0b0'; g.lineWidth = 7; g.beginPath(); g.ellipse(W * 0.4, H * 0.38, 92, 20, -0.3, 0, PI * 2); g.stroke();
      g.fillStyle = '#5ac0e8'; g.beginPath(); g.arc(W * 0.75, H * 0.62, 22, 0, PI * 2); g.fill(); g.fillStyle = '#e86a8a'; g.beginPath(); g.arc(W * 0.22, H * 0.68, 14, 0, PI * 2); g.fill();
      g.fillStyle = '#f4f0e8'; g.font = font(30); g.fillText('SPACE CAMP', W / 2, H - 42);
    } else if (kind === 'band') {
      g.fillStyle = '#141414'; g.font = font(44); g.fillText('THE', W / 2, 70); g.fillText('MOLES', W / 2, 120); g.fillStyle = '#f2c230'; g.beginPath(); g.arc(W / 2, H * 0.62, 60, 0, PI * 2); g.fill(); g.fillStyle = '#141414'; g.font = font(22); g.fillText('LIVE TOUR 1994', W / 2, H - 40);
    } else if (kind === 'cat') {
      g.fillStyle = '#5a3a4a'; g.beginPath(); g.arc(W / 2, H * 0.48, 62, 0, PI * 2); g.fill(); for (const s of [-1, 1]) { g.beginPath(); g.moveTo(W / 2 + s * 55, H * 0.36); g.lineTo(W / 2 + s * 40, H * 0.2); g.lineTo(W / 2 + s * 18, H * 0.33); g.fill(); }
      g.fillStyle = '#f2c230'; for (const s of [-1, 1]) { g.beginPath(); g.arc(W / 2 + s * 22, H * 0.46, 9, 0, PI * 2); g.fill(); } g.fillStyle = '#5a3a4a'; g.font = font(28); g.fillText('HANG IN THERE', W / 2, H - 40);
    } else if (kind === 'race') {
      g.fillStyle = '#d83a2a'; g.fillRect(40, H * 0.45, W - 80, 40); g.fillRect(70, H * 0.38, W - 150, 30); g.fillStyle = '#141414'; for (const x of [80, W - 80]) { g.beginPath(); g.arc(x, H * 0.58, 20, 0, PI * 2); g.fill(); }
      g.font = font(34); g.fillText('VROOM', W / 2, H - 42);
    }
  });
}
// Wall clock face: lavender-white with Roman numerals (TF / AW motif). Hands are separate meshes.
export function clockFaceTex() {
  return ctex('clockFace', 256, 256, (g, W, H) => {
    g.fillStyle = '#f1ebff'; g.beginPath(); g.arc(W / 2, H / 2, W / 2, 0, PI * 2); g.fill();
    g.fillStyle = '#2a1a2a'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.font = font(24);
    const R = ['XII', 'I', 'II', 'III', 'IIII', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI'];
    R.forEach((s, i) => { const a = (i / 12) * PI * 2 - PI / 2; g.fillText(s, W / 2 + Math.cos(a) * 96, H / 2 + Math.sin(a) * 96); });
    for (let i = 0; i < 60; i++) { const a = (i / 60) * PI * 2; const r0 = i % 5 ? 116 : 110; g.fillRect(W / 2 + Math.cos(a) * r0 - 1, H / 2 + Math.sin(a) * r0 - 1, 2, 2); }
  });
}
// Framed photo contents (family snapshots, soft and abstract: two-three heads on a coloured ground).
function snapshotTex(i) {
  return ctex('snap:' + i, 128, 128, (g, W, H) => {
    const r = makeRng(hash32('snap', i)); const bgs = ['#8ab0d8', '#e8c890', '#a8c890', '#d8a0b0']; g.fillStyle = bgs[i % 4]; g.fillRect(0, 0, W, H);
    g.fillStyle = '#5a8a4a'; g.fillRect(0, H * 0.72, W, H * 0.28);
    const n = 1 + (i % 3); for (let k = 0; k < n; k++) { const x = W * (0.5 + (k - (n - 1) / 2) * 0.28); const hc = ['#f0c8a0', '#e8a07a', '#f4d0b0'][k % 3]; g.fillStyle = ['#c8402a', '#2a5ab8', '#d9a52c', '#7a3a8a'][(i + k) % 4]; g.fillRect(x - 14, H * 0.5, 28, 40); g.fillStyle = hc; g.fillRect(x - 11, H * 0.3, 22, 22); g.fillStyle = r() < 0.5 ? '#e8e4ec' : '#5a3a2a'; g.fillRect(x - 12, H * 0.28, 24, 7); }
  });
}

// ------------------------------------------------------------------ geometry helpers (studs)
// Axis-aligned rectangle facing n ([1,0,0] .. [0,0,-1]); one range is degenerate (the plane). UVs planar in tile units
// from absolute coordinates, so pieces of one wall (around a window hole) continue the pattern.
export function rect(P, key, n, xr, yr, zr, tile = 4) {
  let pts;
  if (n[2]) pts = [[xr[0], yr[0], zr[0]], [xr[1], yr[0], zr[0]], [xr[1], yr[1], zr[0]], [xr[0], yr[1], zr[0]]];
  else if (n[0]) pts = [[xr[0], yr[0], zr[0]], [xr[0], yr[0], zr[1]], [xr[0], yr[1], zr[1]], [xr[0], yr[1], zr[0]]];
  else pts = [[xr[0], yr[0], zr[0]], [xr[1], yr[0], zr[0]], [xr[1], yr[0], zr[1]], [xr[0], yr[0], zr[1]]];
  const a = new THREE.Vector3(...pts[0]), b = new THREE.Vector3(...pts[1]), c = new THREE.Vector3(...pts[2]);
  const nn = b.clone().sub(a).cross(c.clone().sub(a)); if (nn.dot(new THREE.Vector3(...n)) < 0) pts.reverse();
  const pos = [], nor = [], uv = [];
  for (const p of pts) { pos.push(...p); nor.push(...n); if (n[2]) uv.push(p[0] / tile, p[1] / tile); else if (n[0]) uv.push(p[2] / tile, p[1] / tile); else uv.push(p[0] / tile, p[2] / tile); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.setIndex([0, 1, 2, 0, 2, 3]);
  return P.add(key, g);
}
// Wall plane with rectangular holes: splits the rectangle into strips around each hole (holes in wall-plane coords).
export function wallWithHoles(P, key, n, u0, u1, v0, v1, c, holes = [], tile = 4) {
  // u along x for z-facing walls, along z for x-facing walls; v = y
  const put = (a0, a1, b0, b1) => { if (a1 - a0 < 1e-3 || b1 - b0 < 1e-3) return; if (n[2]) rect(P, key, n, [a0, a1], [b0, b1], [c, c], tile); else rect(P, key, n, [c, c], [b0, b1], [a0, a1], tile); };
  const hs = holes.slice().sort((p, q) => p[0] - q[0]); let u = u0;
  for (const [h0, h1, k0, k1] of hs) { put(u, h0, v0, v1); put(h0, h1, v0, k0); put(h0, h1, k1, v1); u = h1; }
  put(u, u1, v0, v1);
}
// Fabric drape: a plane (w x h) with vertical folds (curtains) displaced along +Z; gathered: fold amplitude.
function drapeGeo(w, h, { folds = 6, amp = 0.12, seed = 1, sag = 0 } = {}) {
  const g = new THREE.PlaneGeometry(w, h, Math.max(8, folds * 6), 6); const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i); const u = (x + w / 2) / w; p.setZ(i, amp * Math.sin(u * folds * 2 * PI + seed) + 0.03 * noise3(x * 2, y * 0.7, seed, seed) + sag * (1 - (y + h / 2) / h) ** 2); }
  g.computeVertexNormals(); scaleUV(g, w / 2, h / 2); return g;
}
// Puffy duvet / quilt: a subdivided box whose vertices get soft folds (sines + noise), sides drooping.
function duvetGeo(w, h, d, seed = 1, folds = 1) {
  const g = new THREE.BoxGeometry(w, h, d, Math.round(w * 4), 2, Math.round(d * 4)); const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i), z = p.getZ(i); const top = y > 0 ? 1 : 0.3;
    const f = folds * (0.07 * Math.sin(x * 2.1 + z * 0.8 + seed) + 0.05 * Math.sin(z * 3.3 - x * 0.6) + 0.06 * noise3(x * 0.9, z * 0.9, seed, seed));
    p.setY(i, y + f * top + (y > 0 ? 0.06 * Math.cos((z / d) * PI) : 0)); p.setX(i, x * (1 + 0.02 * noise3(z, y, seed + 1, seed))); p.setZ(i, z * (1 + (y < 0 ? 0.03 : 0)));
  }
  g.computeVertexNormals(); scaleUV(g, w / 2, d / 2); return g;
}
function pillowGeo(w, h, d, seed = 1) {
  const g = new THREE.SphereGeometry(1, 20, 12); const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i), z = p.getZ(i); const s = 1 + 0.06 * noise3(x * 2.5, y * 2.5, z * 2.5, seed); const sq = Math.pow(Math.abs(x), 3) * 0.25; p.setXYZ(i, x * s, y * s * (1 - sq), z * s); }
  g.computeVertexNormals(); g.scale(w / 2, h / 2, d / 2); scaleUV(g, w, d); return g;
}
const _sharedGeo = new Map();
const sharedGeo = (k, f) => { if (!_sharedGeo.has(k)) { const g = f(); g.userData.persistent = true; _sharedGeo.set(k, g); } return _sharedGeo.get(k).clone(); };

// ------------------------------------------------------------------ furniture (Parts, studs; origin on the floor, front = +Z)
// Window frame on the INNER face of a wall at z = 0 facing -Z (room side): thick white TF frame, sill board, curtain rod.
function addInnerWindowFrame(P, { x0, x1, y0, y1, trim = '#f1eee8' }) {
  const k = 'gloss:' + trim, w = x1 - x0;
  P.box(k, 0.6, y1 - y0 + 1.2, 0.28, [x0 - 0.3, (y0 + y1) / 2, -0.14]); P.box(k, 0.6, y1 - y0 + 1.2, 0.28, [x1 + 0.3, (y0 + y1) / 2, -0.14]);
  P.box(k, w + 1.8, 0.6, 0.3, [(x0 + x1) / 2, y1 + 0.3, -0.15]);
  P.box(k, w + 1.6, 0.22, 0.95, [(x0 + x1) / 2, y0 - 0.11, -0.45], null, { bevel: 0.05 }); P.box(k, w + 1.2, 0.45, 0.2, [(x0 + x1) / 2, y0 - 0.45, -0.12]);
  P.cyl('brass', 0.07, 0.07, w + 4.2, 8, [(x0 + x1) / 2, y1 + 0.95, -0.55], [0, 0, PI / 2]); for (const s of [-1, 1]) P.add('brass', new THREE.SphereGeometry(0.14, 10, 8), [(x0 + x1) / 2 + s * (w / 2 + 2.15), y1 + 0.95, -0.55]);
}
// Curtains hanging from the rod (state 'open' | 'half' | 'closed'); returns nothing (merged).
function addCurtains(P, { x0, x1, y0, y1, color = '#8a5aa0', state = 'open', seed = 1, floor = false }) {
  const w = x1 - x0, cx = (x0 + x1) / 2; const cover = state === 'closed' ? w / 2 + 0.05 : state === 'half' ? w * 0.28 : 0; const panel = 1.25 + cover;
  const top = y1 + 0.95, bot = floor ? 0.15 : y0 - 0.7; const h = top - bot;
  for (const s of [-1, 1]) {
    const inner = cx + s * (w / 2 - cover); const outer = cx + s * (w / 2 + 1.25); const pc = (inner + outer) / 2;
    P.add('fab:' + color, drapeGeo(panel, h, { folds: Math.round(panel * 2.6), amp: 0.12, seed: seed + s }), [pc, bot + h / 2, -0.62]);
    P.box('fab:' + shade(color, 0.85), 0.2, 0.2, 0.3, [inner - s * 0.05, top - 0.15, -0.62]); // ring heading
  }
  P.add('fab:' + shade(color, 0.8), drapeGeo(w + 3.0, 0.7, { folds: 9, amp: 0.06, seed: seed + 7 }), [cx, top - 0.05, -0.7]); // valance
}
function addNightstand(P, { color = '#f1eee8', drawers = '#3f5aa8' } = {}) {
  P.box('gloss:' + color, 1.7, 2.1, 1.5, [0, 1.05, 0], null, { bevel: 0.06 });
  for (const y of [0.6, 1.45]) { P.box('gloss:' + drawers, 1.45, 0.7, 0.06, [0, y, 0.76], null, { bevel: 0.03 }); P.add('brass', new THREE.SphereGeometry(0.08, 8, 6), [0, y, 0.82]); }
}
// Table lamp on a nightstand top (y = top): brass stem, base, cream drum shade (separate emissive shade mesh returned).
function addLamp(P, top, shadeKey = 'glow:#fffee1:2.5') {
  P.cyl('brass', 0.35, 0.42, 0.14, 16, [0, top + 0.07, 0]); P.cyl('brass', 0.05, 0.06, 1.35, 8, [0, top + 0.8, 0]);
  const sh = new THREE.CylinderGeometry(0.55, 0.72, 0.8, 24, 1, true); P.add(shadeKey, sh, [0, top + 1.6, 0]);
  return [0, top + 1.55, 0];
}
function addShelf(P, { w = 4.5, books = 9, seed = 1, toyCar = true, teddy = true } = {}) {
  const r = makeRng(hash32('shelf', seed)); P.box('wood:#7a4a2a', w, 0.18, 1.0, [0, 0, 0.5]); for (const s of [-1, 1]) P.box('black:#2a2a2e', 0.1, 0.6, 0.6, [s * (w / 2 - 0.4), -0.35, 0.3]);
  let x = -w / 2 + 0.3; const cols = ['#c8302a', '#f2c230', '#2f5ac8', '#2f8a4a', '#e86a2a', '#7a3a9a'];
  for (let i = 0; i < books && x < w * 0.15; i++) { const bw = 0.18 + r() * 0.14, bh = 0.85 + r() * 0.45; P.box('plastic:' + cols[i % cols.length], bw, bh, 0.75, [x + bw / 2, 0.09 + bh / 2, 0.5], [0, 0, i === books - 1 ? -0.25 : 0]); x += bw + 0.02; }
  if (toyCar) { const c = '#d83a2a'; P.box('plastic:' + c, 0.9, 0.3, 0.5, [w * 0.25, 0.3, 0.5], null, { bevel: 0.06 }); P.box('plastic:' + c, 0.5, 0.25, 0.45, [w * 0.23, 0.55, 0.5], null, { bevel: 0.05 }); for (const dx of [-0.3, 0.3]) for (const dz of [-0.24, 0.24]) P.cyl('black', 0.11, 0.11, 0.08, 10, [w * 0.25 + dx, 0.19, 0.5 + dz], [PI / 2, 0, 0]); }
  if (teddy) addTeddy(P, [w * 0.42, 0.09, 0.45], 0.8);
}
function addTeddy(P, at, s = 1, color = '#a8743a') {
  const k = 'rug:' + color; P.push(trs(at, [0, -0.3, 0], s));
  P.add(k, new THREE.SphereGeometry(0.42, 14, 10), [0, 0.45, 0], null, [1, 1.05, 0.9]); P.add(k, new THREE.SphereGeometry(0.32, 14, 10), [0, 1.08, 0.02]);
  for (const sx of [-1, 1]) { P.add(k, new THREE.SphereGeometry(0.12, 8, 6), [sx * 0.24, 1.33, 0]); P.add(k, new THREE.SphereGeometry(0.14, 8, 6), [sx * 0.42, 0.55, 0.12], null, [0.9, 1.4, 0.9]); P.add(k, new THREE.SphereGeometry(0.16, 8, 6), [sx * 0.22, 0.12, 0.2], null, [1, 0.8, 1.3]); }
  P.add('plastic:#e8c8a0', new THREE.SphereGeometry(0.13, 10, 8), [0, 1.02, 0.28], null, [1.2, 0.9, 0.8]); P.add('black', new THREE.SphereGeometry(0.05, 6, 4), [0, 1.07, 0.38]);
  for (const sx of [-1, 1]) P.add('black', new THREE.SphereGeometry(0.04, 6, 4), [sx * 0.12, 1.16, 0.28]);
  P.pop();
}
function addRug(P, { r = 2.6, color = '#e58fc2', at = [0, 0, 0], seed = 2 } = {}) {
  const g = new THREE.CylinderGeometry(r, r, 0.1, 48, 1); const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i); const a = Math.atan2(z, x), rr = Math.hypot(x, z); if (rr > r * 0.98) { const k = 1 + 0.05 * Math.sin(a * 23 + seed) + 0.03 * Math.sin(a * 41); p.setX(i, x * k); p.setZ(i, z * k); } if (p.getY(i) > 0) p.setY(i, 0.05 + 0.025 * noise3(x * 3, z * 3, seed, seed)); }
  g.computeVertexNormals(); planarUV(g, 2.5); P.add('rug:' + color, g, [at[0], 0.05 + at[1], at[2]]);
}
// Wall clock (TF motif): orange rim, lavender face, Roman numerals. Faces +Z. Returns hand meshes for setClock().
function clockMesh(r = 0.9) {
  const g = new THREE.Group(); g.name = 'wallClock';
  const P = new Parts(); P.cyl('gloss:#9c3703', r, r, 0.22, 40, [0, 0, 0], [PI / 2, 0, 0]); P.cyl('brass', r * 0.08, r * 0.08, 0.3, 8, [0, 0, 0.05], [PI / 2, 0, 0]);
  const face = new THREE.Mesh(new THREE.CircleGeometry(r * 0.86, 40), decalMat('clockFace', clockFaceTex(), { roughness: 0.4 })); face.position.z = 0.115; g.add(persistTree(P.build(XM, { name: 'clockBody' })), face);
  const handM = M('black:#1a141a');
  const mk = (len, w, name) => { const h = new THREE.Group(); h.name = name; const m = new THREE.Mesh(boxUV(w, len, 0.03, 1), handM); m.position.y = len / 2 - 0.08; h.add(m); h.position.z = 0.15; g.add(h); return h; };
  mk(r * 0.5, 0.09, 'hourHand'); mk(r * 0.72, 0.06, 'minuteHand'); return g;
}
export function setClock(clock, h, m, s = 0) { const hh = clock.getObjectByName('hourHand'), mm = clock.getObjectByName('minuteHand'); if (hh) hh.rotation.z = -((h % 12) + m / 60) / 12 * 2 * PI; if (mm) mm.rotation.z = -((m + s / 60) / 60) * 2 * PI; }

// Beds: built along X (head at -X), centred on the origin, floor y = 0. Return the sleeper anchor (studs, local).
function addBed(P, kind, o = {}) {
  const r = makeRng(hash32('bed', kind, o.seed || 1));
  if (kind === 'mattress') { // Theo: a bare mattress on the floor (striped ticking), pillow, a kicked-off blanket
    P.add('tex:ticking', new RoundedBoxGeometry(6.6, 0.75, 3.3, 3, 0.18), [0, 0.38, 0]);
    P.add('fab:#f2eef6', pillowGeo(1.9, 0.5, 1.4, 3), [-2.35, 0.95, 0]);
    P.add('fab:' + (o.blanket || '#4f7ac8'), duvetGeo(3.6, 0.22, 3.0, 5, 1.6), [1.25, 0.86, 0.1], [0, 0.08, 0.02]);
    P.add('fab:' + (o.blanket || '#4f7ac8'), drapeGeo(3.2, 0.7, { folds: 5, amp: 0.08, seed: 2 }), [1.3, 0.42, 1.68]); // hanging off the side
    return { head: [-2.35, 1.1, 0], body: [0.2, 0.95, 0], top: 0.76, len: 6.6, wid: 3.3 };
  }
  if (kind === 'carved') { // TF bed: carved dark headboard (vertical ridges), magenta duvet, white pillows, frilly skirt
    const wd = '#4a2414'; P.box('wood:' + wd, 7.4, 0.9, 4.8, [0, 0.75, 0]);
    P.box('fab:#f1e6f6', 7.2, 0.8, 4.6, [0, 1.55, 0], null, { bevel: 0.15 });
    P.add('fab:#d8c8e8', drapeGeo(7.5, 1.1, { folds: 30, amp: 0.07, seed: 4 }), [0, 0.6, 2.42]); P.add('fab:#d8c8e8', drapeGeo(7.5, 1.1, { folds: 30, amp: 0.07, seed: 5 }), [0, 0.6, -2.42], [0, PI, 0]);
    P.box('wood:' + wd, 0.45, 4.4, 5.2, [-3.85, 2.2, 0]); for (let i = 0; i < 9; i++) P.box('wood:' + shade(wd, 1.25), 0.2, 3.0, 0.22, [-3.6, 2.4, -2.0 + i * 0.5], null, { bevel: 0.06 });
    P.add('wood:' + wd, new THREE.CylinderGeometry(2.6, 2.6, 0.45, 24, 1, false, 0, PI), [-3.85, 4.4, 0], [0, 0, PI / 2], [1, 1, 0.35]);
    P.box('wood:' + wd, 0.4, 2.6, 5.0, [3.75, 1.3, 0]);
    for (const s of [-1, 1]) P.add('fab:#fbf6ff', pillowGeo(1.7, 0.6, 2.1, 7 + s), [-2.6, 2.2, s * 1.05]);
    P.add('fab:' + (o.duvet || '#a93298'), duvetGeo(5.0, 0.45, 4.9, 3, 1.2), [1.15, 2.05, 0]);
    return { head: [-2.6, 2.6, 0], body: [0.3, 2.4, 0], top: 2.4, len: 7.4, wid: 4.8 };
  }
  if (kind === 'small') { // the hero at 5: small light-wood bed, rocket duvet, round headboard
    const wd = '#c89058'; P.box('wood:' + wd, 6.0, 0.6, 3.8, [0, 0.55, 0]);
    P.box('fab:#f4f0f8', 5.8, 0.6, 3.6, [0, 1.15, 0], null, { bevel: 0.12 });
    P.add('wood:' + wd, new THREE.CylinderGeometry(1.9, 1.9, 0.35, 24, 1, false, 0, PI), [-3.05, 1.4, 0], [0, 0, PI / 2]); P.box('wood:' + wd, 0.35, 1.4, 3.8, [-3.05, 0.7, 0]);
    P.box('wood:' + wd, 0.3, 1.9, 3.8, [3.0, 0.95, 0]);
    P.add('fab:#fbf6ff', pillowGeo(1.5, 0.5, 2.6, 9), [-2.2, 1.6, 0]);
    P.add('tex:rocketDuvet', duvetGeo(4.1, 0.35, 3.9, 6, 1), [0.75, 1.52, 0]);
    return { head: [-2.2, 1.9, 0], body: [0.2, 1.7, 0], top: 1.45, len: 6.0, wid: 3.8 };
  }
  if (kind === 'iron') { // 1960s: enamelled iron bed (black tubes, brass knobs), white sheets, grey wool blanket
    const k = 'black:#202024'; for (const x of [-3.4, 3.4]) for (const z of [-1.9, 1.9]) { const hgt = x < 0 ? 4.0 : 3.0; P.cyl(k, 0.1, 0.1, hgt, 10, [x, hgt / 2, z]); P.add('brass', new THREE.SphereGeometry(0.17, 10, 8), [x, hgt + 0.1, z]); }
    for (const [x, hgt] of [[-3.4, 4.0], [3.4, 3.0]]) { P.cyl(k, 0.07, 0.07, 3.8, 8, [x, hgt - 0.2, 0], [PI / 2, 0, 0]); P.cyl(k, 0.07, 0.07, 3.8, 8, [x, 1.3, 0], [PI / 2, 0, 0]); for (let i = 1; i < 7; i++) P.cyl(k, 0.04, 0.04, hgt - 1.5, 6, [x, (hgt - 0.2 + 1.3) / 2, -1.9 + i * 0.55]); }
    for (const z of [-1.9, 1.9]) P.cyl(k, 0.07, 0.07, 6.8, 8, [0, 1.15, z], [0, 0, PI / 2]);
    P.box('fab:#f4f2ee', 6.6, 0.6, 3.6, [0, 1.5, 0], null, { bevel: 0.12 }); P.add('fab:#f8f6f2', pillowGeo(1.5, 0.5, 2.8, 4), [-2.4, 2.0, 0]);
    P.add('fab:#8a8a92', duvetGeo(4.4, 0.3, 3.9, 8, 0.8), [0.95, 1.9, 0]);
    return { head: [-2.4, 2.25, 0], body: [0.2, 2.1, 0], top: 1.8, len: 6.8, wid: 3.8 };
  }
  if (kind === 'bunk') { // 1990s: white bunk bed, ladder at the foot, floral quilts (the girl sleeps on top)
    const k = 'gloss:#f1eee8'; for (const x of [-3.4, 3.4]) for (const z of [-1.8, 1.8]) P.box(k, 0.35, 7.6, 0.35, [x, 3.8, z]);
    for (const y of [0.9, 4.6]) { for (const z of [-1.8, 1.8]) P.box(k, 6.8, 0.4, 0.25, [0, y, z]); for (const x of [-3.4, 3.4]) P.box(k, 0.25, 0.4, 3.6, [x, y, 0]); }
    P.box(k, 6.8, 0.25, 0.2, [0, 6.6, 1.8]); P.box(k, 6.8, 0.25, 0.2, [0, 6.6, -1.8]);
    for (let i = 0; i < 6; i++) P.box(k, 0.2, 0.15, 0.9, [3.75, 0.9 + i * 1.0, 1.0]); for (const z of [0.55, 1.45]) P.box(k, 0.2, 6.2, 0.15, [3.75, 3.4, z]);
    for (const y of [1.1, 4.8]) { P.box('fab:#f4f0f0', 6.5, 0.55, 3.4, [0, y + 0.27, 0], null, { bevel: 0.12 }); P.add('fab:#fbf6ff', pillowGeo(1.4, 0.45, 2.4, y), [-2.4, y + 0.75, 0]); P.add('tex:floralQuilt', duvetGeo(4.2, 0.3, 3.6, y * 3, 0.9), [0.9, y + 0.65, 0]); }
    return { head: [-2.4, 5.8, 0], body: [0.2, 5.6, 0], top: 5.35, len: 6.8, wid: 3.6, lowerHead: [-2.4, 2.1, 0] };
  }
  return null;
}
// Stack of taped, labelled moving boxes: columns of two along -Z from `at` = [x, y, z, yaw].
function addBoxes(P, labels, at, seed = 1) {
  const r = makeRng(hash32('boxes', seed)); let h = 0;
  labels.forEach((lab, i) => { const col = Math.floor(i / 2); if (i % 2 === 0) h = 0; const s = [2.2 + r() * 0.4, 1.6 + r() * 0.4, 2.0 + r() * 0.3];
    P.push(trs([at[0] + (r() - 0.5) * 0.3, h, at[2] - col * 2.7 + (r() - 0.5) * 0.3], [0, (r() - 0.5) * 0.25 + (at[3] || 0), 0])); P_.addCardboardBox(P, { size: s, label: lab }); P.pop(); h += s[1]; });
}
// Star nightlight projector (Theo): a small dark-blue dome with star holes on a white base. Returns its light anchor.
function addProjector(P, at) {
  P.push(trs(at)); P.cyl('gloss:#f1eee8', 0.45, 0.5, 0.25, 20, [0, 0.12, 0]);
  P.add('tex:projDome', new THREE.SphereGeometry(0.42, 20, 12, 0, PI * 2, 0, PI / 2), [0, 0.25, 0]); P.pop();
  return [at[0], at[1] + 0.5, at[2]];
}
// Projected stars on the ceiling (additive canvas card, a ring pattern around the projector axis).
function projectedStarsTex() {
  return ctex('projStars', 512, 512, (g, W, H) => {
    const r = makeRng(hash32('projStars')); g.clearRect(0, 0, W, H);
    const star = (x, y, s, a, col) => { g.save(); g.translate(x, y); g.rotate(a); g.fillStyle = col; g.beginPath(); for (let k = 0; k < 10; k++) { const rr = k % 2 ? s * 0.45 : s; const an = (k / 10) * PI * 2 - PI / 2; g.lineTo(Math.cos(an) * rr, Math.sin(an) * rr); } g.closePath(); g.fill(); g.restore(); };
    for (let k = 0; k < 70; k++) { const a = r() * PI * 2, d = 40 + Math.sqrt(r()) * 210; const x = W / 2 + Math.cos(a) * d, y = H / 2 + Math.sin(a) * d; const s = 6 + r() * 9; const fade = 1 - d / 260; g.globalAlpha = 0.35 + 0.65 * fade; star(x, y, s, r() * PI, r() < 0.6 ? '#fff2b0' : r() < 0.5 ? '#ffc8e8' : '#c8d8ff'); }
    g.globalAlpha = 1;
  });
}
function gloStarsGeo(n, area, seed) { // glow-in-the-dark star stickers (5-point), merged, lying in the XZ plane facing -Y
  const r = makeRng(hash32('glostars', seed)); const shape = new THREE.Shape(); for (let k = 0; k < 10; k++) { const rr = k % 2 ? 0.13 : 0.3; const an = (k / 10) * PI * 2; const x = Math.cos(an) * rr, y = Math.sin(an) * rr; if (k) shape.lineTo(x, y); else shape.moveTo(x, y); }
  const list = []; for (let i = 0; i < n; i++) { const g = new THREE.ShapeGeometry(shape); const s = 0.7 + r() * 0.8; g.rotateZ(r() * PI); g.scale(s, s, s); g.rotateX(PI / 2); g.translate(area[0] + r() * (area[1] - area[0]), 0, area[2] + r() * (area[3] - area[2])); list.push(g); }
  return list;
}

// ------------------------------------------------------------------ THE OLD BEDROOM (room frame, studs)
export const ROOM = { x0: -5.2, x1: 8.8, d: 12, h: 10, hole: [-2, 2, 1.6, 6.6], wallT: 0.6 };
export const ROOM_ERAS = {
  hero11: { wall: ['fabric', '#4958a0'], ceil: '#b28dc0', curtain: '#8a5aa0', bed: 'carved', bedAt: [-1.2, -7.85, -PI / 2], stickers: true, posters: ['rocket', 'dino', 'planets'], shelf: true, rug: '#e58fc2', nightstand: true, clock: true, toys: true },
  theo: { wall: ['fabric', '#4958a0'], ceil: '#b28dc0', curtain: '#8a5aa0', bed: 'mattress', bedAt: [0.6, -4.3, 0], projector: true, boxes: true, ghosts: true, rug: null, nightstand: false, clock: true, lampOnBox: true, blanket: '#4f7ac8' },
  hero5: { wall: ['fabric', '#4958a0'], ceil: '#b28dc0', curtain: '#8a5aa0', bed: 'small', bedAt: [0.6, -4.3, 0], stickers: true, posters: ['rocket', 'race'], shelf: true, rug: '#e58fc2', nightstand: true, clock: true, toys: true },
  dad60s: { wall: ['stripe', '#c98a92'], ceil: '#ece0d4', curtain: '#e8dcc8', bed: 'iron', bedAt: [0.6, -4.3, 0], posters: ['race'], shelf: true, rug: '#8a6a5a', nightstand: true, clock: true, floor: '#7a3a1a' },
  cousin90s: { wall: ['floral', '#e8c75a'], ceil: '#f2e8d4', curtain: '#e88aa8', bed: 'bunk', bedAt: [1.0, -9.6, 0], posters: ['band', 'cat'], shelf: true, rug: '#7ac0d8', nightstand: true, clock: true, toys: true },
  later: { wall: ['fabric', '#4958a0'], ceil: '#b28dc0', curtain: '#5a8ac0', bed: 'carved', bedAt: [-1.2, -7.85, -PI / 2], duvet: '#3a6ab8', stickers: false, posters: ['planets'], shelf: true, rug: '#7ac0d8', nightstand: true, clock: true },
};
function registerBedroomDecals() {
  decalMat('ticking', ctex('ticking', 256, 256, (g, W, H) => { g.fillStyle = '#ecebf2'; g.fillRect(0, 0, W, H); for (let x = 0; x < W; x += 32) { g.fillStyle = '#7a8ac8'; g.fillRect(x + 4, 0, 5, H); g.fillRect(x + 14, 0, 2, H); } for (let k = 0; k < 400; k++) { g.fillStyle = 'rgba(0,0,0,0.03)'; g.fillRect((k * 37) % W, (k * 91) % H, 8, 2); } }, { wrap: true }), { roughness: 0.9 });
  decalMat('rocketDuvet', ctex('rocketDuvet', 256, 256, (g, W, H) => { g.fillStyle = '#2f5ac8'; g.fillRect(0, 0, W, H); const r = makeRng(5); for (let k = 0; k < 30; k++) { g.fillStyle = '#ffe27a'; g.beginPath(); g.arc(r() * W, r() * H, 3 + r() * 3, 0, PI * 2); g.fill(); }
    for (const [x, y, a] of [[70, 80, -0.5], [190, 170, 0.4]]) { g.save(); g.translate(x, y); g.rotate(a); g.fillStyle = '#f4f0e8'; g.fillRect(-12, -30, 24, 50); g.beginPath(); g.moveTo(-12, -30); g.lineTo(0, -50); g.lineTo(12, -30); g.fill(); g.fillStyle = '#d83a2a'; g.fillRect(-20, 10, 8, 14); g.fillRect(12, 10, 8, 14); g.fillStyle = '#f2a83a'; g.beginPath(); g.moveTo(-8, 20); g.lineTo(0, 38); g.lineTo(8, 20); g.fill(); g.restore(); } }, { wrap: true }), { roughness: 0.95 });
  decalMat('floralQuilt', ctex('floralQuilt', 256, 256, (g, W, H) => { g.fillStyle = '#f0a0b8'; g.fillRect(0, 0, W, H); const r = makeRng(6); for (let k = 0; k < 36; k++) { const x = r() * W, y = r() * H; g.fillStyle = r() < 0.5 ? '#fff4e0' : '#c8486a'; for (let p = 0; p < 5; p++) { const a = (p / 5) * PI * 2; g.beginPath(); g.arc(x + Math.cos(a) * 6, y + Math.sin(a) * 6, 5, 0, PI * 2); g.fill(); } g.fillStyle = '#f2c230'; g.beginPath(); g.arc(x, y, 3, 0, PI * 2); g.fill(); } for (let x = 0; x < W; x += 64) { g.fillStyle = 'rgba(255,255,255,0.4)'; g.fillRect(x, 0, 2, H); g.fillRect(0, x, W, 2); } }, { wrap: true }), { roughness: 0.95 });
  decalMat('projDome', ctex('projDome', 128, 64, (g, W, H) => { g.fillStyle = '#2a3a8a'; g.fillRect(0, 0, W, H); const r = makeRng(8); for (let k = 0; k < 26; k++) { g.fillStyle = '#fff2b0'; g.beginPath(); g.arc(r() * W, r() * H, 2 + r() * 2, 0, PI * 2); g.fill(); } }, { wrap: true }), { roughness: 0.3 });
}
// Bare bedroom in STUDS (room frame), cached per worker; returns a clone with userData.anchors (room-local studs) and
// named parts: 'lampShade', 'projStars', 'gloStars', 'wallClock', 'roomCurtains'.
// o: { era: 'hero11' | 'theo' | 'hero5' | 'dad60s' | 'cousin90s' | 'later', curtains: 'open' | 'half' | 'closed', duvet, curtain }
export function bedroomRoom(ctx, o = {}) {
  const era = o.era || 'theo'; const E = { ...ROOM_ERAS[era], ...(o.curtain ? { curtain: o.curtain } : {}), ...(o.duvet ? { duvet: o.duvet } : {}) };
  const curtains = o.curtains || (era === 'theo' ? 'half' : 'open'); const key = 'ep01:bedroom:' + JSON.stringify({ era, E, curtains });
  return ctx.cache(key, () => {
    registerBedroomDecals();
    const R = ROOM; const [hx0, hx1, hy0, hy1] = R.hole; const P = new Parts(); const r = makeRng(hash32('bedroom', era));
    const wall = `wp:${E.wall[0]}:${E.wall[1]}`;
    // shell (inward faces): floor, ceiling, back, sides, window wall with the hole
    rect(P, 'floor:' + (E.floor || '#9f3305'), [0, 1, 0], [R.x0, R.x1], [0, 0], [-R.d, 0]);
    rect(P, 'ceil:' + E.ceil, [0, -1, 0], [R.x0, R.x1], [R.h, R.h], [-R.d, 0]);
    rect(P, wall, [0, 0, 1], [R.x0, R.x1], [0, R.h], [-R.d, -R.d]);
    rect(P, wall, [1, 0, 0], [R.x0, R.x0], [0, R.h], [-R.d, 0]); rect(P, wall, [-1, 0, 0], [R.x1, R.x1], [0, R.h], [-R.d, 0]);
    wallWithHoles(P, wall, [0, 0, -1], R.x0, R.x1, 0, R.h, 0, [[hx0, hx1, hy0, hy1]]);
    // skirting + a picture rail (white), cornice
    const sk = 'gloss:#f1eee8';
    P.box(sk, R.x1 - R.x0, 0.55, 0.16, [(R.x0 + R.x1) / 2, 0.27, -R.d + 0.08]); P.box(sk, R.x1 - R.x0, 0.55, 0.16, [(R.x0 + R.x1) / 2, 0.27, -0.08]);
    P.box(sk, 0.16, 0.55, R.d, [R.x0 + 0.08, 0.27, -R.d / 2]); P.box(sk, 0.16, 0.55, R.d, [R.x1 - 0.08, 0.27, -R.d / 2]);
    for (const [a, b, c, d] of [[R.x1 - R.x0, 0.3, 0.3, [(R.x0 + R.x1) / 2, R.h - 0.15, -R.d + 0.15]], [R.x1 - R.x0, 0.3, 0.3, [(R.x0 + R.x1) / 2, R.h - 0.15, -0.15]], [0.3, 0.3, R.d, [R.x0 + 0.15, R.h - 0.15, -R.d / 2]], [0.3, 0.3, R.d, [R.x1 - 0.15, R.h - 0.15, -R.d / 2]]]) P.box(sk, a, b, c, d);
    addInnerWindowFrame(P, { x0: hx0, x1: hx1, y0: hy0, y1: hy1 });
    // door (right wall, toward the back): interior door 7.5 x 4 with frame
    P.push(trs([R.x1 - 0.02, 0, -9.0], [0, -PI / 2, 0])); P.add('door:#8a5a3a', new THREE.PlaneGeometry(3.6, 7.2), [0, 3.6, 0.04]); for (const s of [-1, 1]) P.box(sk, 0.4, 7.6, 0.2, [s * 2.0, 3.8, 0.1]); P.box(sk, 4.4, 0.4, 0.2, [0, 7.6, 0.1]); P.add('brass', new THREE.SphereGeometry(0.16, 10, 8), [1.3, 3.5, 0.2]); P.pop();
    const A = { window: { center: [0, (hy0 + hy1) / 2, 0], sill: [0, hy0, -0.45], hole: R.hole, normal: [0, 0, 1] } };
    // bed
    const [bx, bz, byaw] = E.bedAt; P.push(trs([bx, 0, bz], [0, byaw, 0])); const bed = addBed(P, E.bed, { duvet: E.duvet, blanket: E.blanket, seed: 3 }); P.pop();
    const toRoom = (p) => new THREE.Vector3(...p).applyAxisAngle(new THREE.Vector3(0, 1, 0), byaw).add(new THREE.Vector3(bx, 0, bz)).toArray().map((v) => +v.toFixed(3));
    A.sleeper = { head: toRoom(bed.head), body: toRoom(bed.body), yaw: byaw, top: bed.top, bed: E.bed }; if (bed.lowerHead) A.sleeper.lowerHead = toRoom(bed.lowerHead);
    // nightstand + lamp (left of the window); or a lamp on a box (Theo)
    let lampPos = null;
    if (E.nightstand) { P.push(trs([-4.2, 0, -1.5])); addNightstand(P, {}); lampPos = addLamp(P, 2.1, 'tex:lampShade'); P.pop(); lampPos = [lampPos[0] - 4.2, lampPos[1], lampPos[2] - 1.5]; }
    // posters, clock, shelf, rug, stickers, toys
    const posters = E.posters || []; const pspots = [[[4.6, 5.8, -R.d + 0.05], 0], [[-2.6, 6.6, -R.d + 0.05], 0], [[R.x1 - 0.05, 6.6, -5.8], -PI / 2], [[R.x0 + 0.05, 6.0, -6.0], PI / 2]];
    posters.forEach((k, i) => { const [p, yaw] = pspots[i]; P.push(trs(p, [0, yaw, (r() - 0.5) * 0.06])); P.box('gloss:#f1eee8', 2.7, 3.7, 0.06, [0, 0, 0.03]); P.add('tex:poster:' + k, new THREE.PlaneGeometry(2.5, 3.45), [0, 0, 0.07]); P.pop(); decalMat('poster:' + k, posterTex(k), { roughness: 0.55 }); });
    if (E.ghosts) { // packed house: lighter rectangles where the posters were, bare picture hooks
      for (const [p, yaw] of pspots.slice(0, 3)) { P.push(trs(p, [0, yaw, 0])); P.add('wp:' + E.wall[0] + ':' + shade(E.wall[1], 1.22), new THREE.PlaneGeometry(2.6, 3.6), [0, 0, 0.02]); P.add('brass', new THREE.SphereGeometry(0.07, 6, 4), [0, 2.1, 0.05]); P.pop(); }
    }
    if (E.shelf) { P.push(trs([R.x1 - 0.02, 4.4, -2.6], [0, -PI / 2, 0])); addShelf(P, { seed: era.length, teddy: era !== 'dad60s' }); P.pop(); }
    if (E.rug) addRug(P, { r: 2.4, color: E.rug, at: [4.2, 0, -7.0], seed: 3 });
    if (E.toys) { P.add('plastic:#e8402a', new THREE.SphereGeometry(0.45, 16, 12), [5.6, 0.45, -6.2]); for (let i = 0; i < 5; i++) P.box('plastic:' + ['#f2c230', '#2f5ac8', '#d83a2a', '#2f8a4a', '#e86a2a'][i], 0.55, 0.55, 0.55, [1.6 + (i % 3) * 0.62, 0.28 + Math.floor(i / 3) * 0.55, -8.2 + (i % 2) * 0.1], [0, r() * 0.6, 0]); }
    if (E.boxes) { addBoxes(P, ['THEO', 'THEO', 'THEO', 'BOOKS', 'THEO'], [6.6, 0, -2.2, -PI / 2 + 0.1], 2); }
    if (E.lampOnBox) { P.push(trs([-3.9, 0, -1.6])); P_.addCardboardBox(P, { size: [1.9, 1.5, 1.7], label: 'THEO' }); lampPos = addLamp(P, 1.5, 'tex:lampShade'); P.pop(); lampPos = [lampPos[0] - 3.9, lampPos[1], lampPos[2] - 1.6]; }
    const root = new THREE.Group(); root.name = 'bedroom_' + era;
    _mc.set('tex:lampShade', persistMat(Object.assign(new THREE.MeshBasicMaterial({ color: new THREE.Color('#fffee1').multiplyScalar(2.4), side: THREE.DoubleSide }), { name: 'tex:lampShade' })));
    // curtains (separate group so a shot can swap the state)
    const C = new Parts(); addCurtains(C, { x0: hx0, x1: hx1, y0: hy0, y1: hy1, color: E.curtain, state: curtains, seed: era.length }); const cg = persistTree(C.build(XM, { name: 'roomCurtains' }));
    const g = persistTree(P.build(XM, { name: 'roomMesh' })); root.add(g, cg);
    g.traverse((m) => { if (m.isMesh && m.name === 'tex:lampShade') m.name = 'lampShade'; });
    // clock (motif) on the window wall, right of the window
    if (E.clock) { const ck = persistTree(clockMesh(0.85)); ck.position.set(5.2, 6.6, -0.12); ck.rotation.y = PI; setClock(ck, 9, 0); root.add(ck); A.clock = [5.2, 6.6, -0.2]; }
    // ceiling: glow-star stickers (emissive #e9f7a0 x0.6) or the projector's stars
    if (E.stickers) { const S = new Parts(); for (const gg of gloStarsGeo(22, [R.x0 + 1, R.x1 - 1, -R.d + 1, -1], 7)) S.add('glow:#e9f7a0:0.6', gg); const sg = persistTree(S.build(XM, { name: 'gloStars' })); sg.position.y = R.h - 0.02; root.add(sg); }
    if (E.projector) {
      const PP = new Parts(); A.nightlight = addProjector(PP, [-3.6, 0, -4.3]); root.add(persistTree(PP.build(XM, { name: 'projector' })));
      const m = new THREE.MeshBasicMaterial({ map: projectedStarsTex(), color: new THREE.Color('#ffffff').multiplyScalar(1.3), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide });
      persistMat(m); const st = new THREE.Mesh(new THREE.PlaneGeometry(13.5, 11.5), m); st.rotation.x = PI / 2; st.position.set(1.8, R.h - 0.04, -6.0); st.name = 'projStars'; st.renderOrder = 3; persistTree(st); root.add(st);
      const wm = m.clone(); wm.color = new THREE.Color('#ffffff').multiplyScalar(0.8); persistMat(wm); const sw = new THREE.Mesh(new THREE.PlaneGeometry(12, 7), wm); sw.position.set(1.8, 6.2, -R.d + 0.04); sw.name = 'projStars'; sw.renderOrder = 3; persistTree(sw); root.add(sw);
    }
    A.lamp = lampPos; A.bounds = [R.x0, R.x1, -R.d, 0, R.h];
    // camera anchors (room-local studs; heroLot converts them to metres): pos, target, fov
    const s = A.sleeper;
    A.views = {
      toWindow: { pos: [0.4, 3.0, -R.d + 2.6], target: [0, 3.6, 0], fov: 70 },                     // s66/s67: bed in the foreground, the window behind
      sleeperCU: { pos: [s.body[0] + 2.0, s.top + 0.9, s.body[2] - 3.4], target: [s.head[0] + 0.4, s.top + 0.4, s.head[2]], fov: 70 }, // s44 CU low
      fromBed: { pos: [0.2, 2.2, -R.d + 4.2], target: [0, 4.0, 0], fov: 70 },                      // s55 / s71: sleeper low in frame, window above
      sleeperHigh: { pos: [s.head[0] + 1.2, s.top + 3.2, s.head[2] - 1.0], target: [s.head[0], s.top + 0.3, s.head[2]], fov: 70 }, // s72 CU high
      otsWindow: { pos: [1.2, 4.9, -2.6], target: [-0.4, 3.2, 3.0], fov: 70 },                    // s17 OTS: a figure at the window, the lawn below
    };
    root.userData.anchors = JSON.parse(JSON.stringify(A)); root.userData.era = era;
    return root;
  }).clone(true);
}

// ------------------------------------------------------------------ helpers: studs-room -> metres root with views
function wrapRoom(inner, A, name) {
  const root = new THREE.Group(); root.name = name; const w = new THREE.Group(); w.scale.setScalar(STUD); w.add(inner); root.add(w);
  const toM = (p) => p.map((v) => +(v * STUD).toFixed(4)); const views = {};
  for (const [k, v] of Object.entries(A.views || {})) views[k] = { pos: toM(v.pos), target: toM(v.target), fov: v.fov };
  const anchors = {}; for (const [k, v] of Object.entries(A)) if (k !== 'views') anchors[k] = Array.isArray(v) && typeof v[0] === 'number' ? toM(v) : v;
  root.userData = { views, anchors, stud: STUD }; return root;
}

// ------------------------------------------------------------------ GRANDMA'S LIVING ROOM (day)
// Room 18 x 14 x 12 studs (x -9..9, z -14..0 toward the camera side open, back wall at z = -14), window on the left wall
// with net curtains and daylight, rose wingback armchair facing +Z at (0, 0, -7.5), shag rug, standard lamp, side table
// with teacup + knitting basket, framed photos and a cuckoo clock on rose wallpaper, skirting, terracotta planks.
function addArmchair(P, { color = '#c8607a' } = {}) { // wingback: seat top 1.5, high back, rolled arms; faces +Z
  const k = 'fab:' + color, kd = 'fab:' + shade(color, 0.82);
  P.add(k, new RoundedBoxGeometry(4.2, 1.0, 3.6, 3, 0.3), [0, 1.0, 0.2]);                  // seat cushion, top 1.5
  P.add(kd, new RoundedBoxGeometry(4.0, 0.6, 3.4, 2, 0.15), [0, 0.35, 0.1]);                // base
  P.add(k, new RoundedBoxGeometry(4.2, 4.6, 0.9, 3, 0.35), [0, 3.1, -1.6], [-0.08, 0, 0]);  // high back
  for (const s of [-1, 1]) {
    P.add(k, new RoundedBoxGeometry(0.9, 2.6, 2.4, 3, 0.35), [s * 2.0, 3.6, -1.0], [0, s * 0.25, 0]);        // wings
    P.add(k, new RoundedBoxGeometry(0.85, 1.3, 3.6, 3, 0.3), [s * 2.15, 1.85, 0.15]);                         // arm block
    P.add(k, new THREE.CylinderGeometry(0.55, 0.55, 3.7, 20), [s * 2.2, 2.45, 0.15], [PI / 2, 0, 0]);          // rolled arm
    P.add(kd, new THREE.CircleGeometry(0.56, 20), [s * 2.2, 2.45, 2.01]);
    for (const z of [-1.3, 1.6]) P.cyl('wood:#4a2414', 0.12, 0.08, 0.5, 8, [s * 1.7, 0.1, z]);
  }
  P.add(kd, drapeGeo(4.1, 0.5, { folds: 16, amp: 0.05, seed: 3 }), [0, 0.2, 1.92]);
  return { seat: [0, 1.5, 0.3], seatTop: 1.5 };
}
function addStandardLamp(P, shadeKey = 'tex:standardShade') {
  P.cyl('brass', 0.6, 0.7, 0.18, 20, [0, 0.09, 0]); P.cyl('brass', 0.07, 0.07, 7.6, 8, [0, 3.9, 0]);
  P.add(shadeKey, new THREE.CylinderGeometry(0.85, 1.25, 1.4, 28, 1, true), [0, 8.1, 0]); P.add('fab:#e8dcc0', new THREE.TorusGeometry(1.25, 0.05, 6, 28), [0, 7.4, 0], [PI / 2, 0, 0]);
  return [0, 7.9, 0];
}
function addSideTable(P) { // the porch-dressing pieces (part1) rebuilt here: side table, teacup, knitting basket with yarn balls
  const w = 'wood:#7a4a28'; P.box(w, 1.6, 0.16, 1.6, [0, 2.2, 0], null, { bevel: 0.04 }); for (const [x, z] of [[-0.65, -0.65], [0.65, -0.65], [-0.65, 0.65], [0.65, 0.65]]) P.box(w, 0.16, 2.15, 0.16, [x, 1.07, z]);
  P.box(w, 1.4, 0.1, 1.4, [0, 0.6, 0]);
  P.cyl('plastic:#f4f0ea', 0.36, 0.36, 0.05, 20, [0.1, 2.31, 0.1]); P.cyl('plastic:#f4f0ea', 0.22, 0.16, 0.32, 18, [0.1, 2.5, 0.1]); P.cyl('plastic:#c86f93', 0.225, 0.225, 0.05, 18, [0.1, 2.6, 0.1]);
  P.add('plastic:#f4f0ea', new THREE.TorusGeometry(0.09, 0.03, 6, 12), [0.34, 2.5, 0.1], [0, 0, 0]);
  P.cyl('wood:#a0703a', 0.55, 0.45, 0.55, 16, [2.3, 0.28, 0.3]); for (const [x, z, c] of [[-0.15, 0.1, '#c84a6a'], [0.18, -0.05, '#7d9be8'], [0.02, -0.2, '#f2cf6a']]) P.add('rug:' + c, new THREE.SphereGeometry(0.22, 12, 8), [2.3 + x, 0.62, 0.3 + z]);
  P.bar('metal:#c9c4cc', [2.2, 0.6, 0.4], [2.6, 1.2, 0.1], 0.04, 0.04); P.bar('metal:#c9c4cc', [2.4, 0.6, 0.45], [2.0, 1.15, 0.2], 0.04, 0.04);
}
function addCuckooClock(P) { // faces +Z, origin = wall point at its centre
  const w = 'wood:#5a3018'; P.box(w, 1.6, 1.8, 0.6, [0, 0, 0.3]); P.add(w, new THREE.ConeGeometry(1.25, 0.8, 4), [0, 1.25, 0.3], [0, PI / 4, 0], [1.05, 1, 0.5]);
  P.box('wood:#7a4a28', 0.5, 0.45, 0.1, [0, 0.65, 0.62]); P.add('tex:clockFace', new THREE.CircleGeometry(0.45, 24), [0, -0.1, 0.61]);
  for (const s of [-1, 1]) { P.bar('brass', [s * 0.3, -0.9, 0.3], [s * 0.3, -2.4 - (s > 0 ? 0.4 : 0), 0.3], 0.03, 0.03); P.add('wood:#3a2010', new THREE.CylinderGeometry(0.13, 0.13, 0.6, 8), [s * 0.3, -2.7 - (s > 0 ? 0.4 : 0), 0.3]); }
  P.bar('brass', [0, -0.9, 0.35], [0, -2.0, 0.35], 0.04, 0.02); P.add('brass', new THREE.CircleGeometry(0.22, 16), [0, -2.1, 0.37]);
  for (const s of [-1, 1]) P.add('stem:#3f7a32', new THREE.SphereGeometry(0.2, 8, 6), [s * 0.55, 0.85, 0.62], null, [1.4, 0.5, 0.3]);
}
function addFrames(P, list) { // [[x, y, z, w, h, yaw, i], ...] framed snapshots
  for (const [x, y, z, w, h, yaw, i] of list) { P.push(trs([x, y, z], [0, yaw, 0])); P.box('gloss:' + (i % 2 ? '#c9a040' : '#5a3018'), w + 0.3, h + 0.3, 0.12, [0, 0, 0.06]); P.add('tex:snap:' + i, new THREE.PlaneGeometry(w, h), [0, 0, 0.13]); decalMat('snap:' + i, snapshotTex(i), { roughness: 0.4 }); P.pop(); }
}
function daylightTex() { // the garden seen through net curtains: bright sky, a hedge and a tree, soft
  return ctex('daylightView', 256, 256, (g, W, H) => {
    const gr = g.createLinearGradient(0, 0, 0, H); gr.addColorStop(0, '#bcd8f4'); gr.addColorStop(0.55, '#e8f0f6'); gr.addColorStop(0.6, '#8ab070'); gr.addColorStop(1, '#5a8a4a'); g.fillStyle = gr; g.fillRect(0, 0, W, H);
    g.fillStyle = '#4f7a3a'; g.beginPath(); g.arc(W * 0.7, H * 0.42, 50, 0, PI * 2); g.fill(); g.fillRect(W * 0.68, H * 0.42, 8, 60); g.fillStyle = '#6a9a4a'; g.fillRect(0, H * 0.56, W, 22);
  });
}
export function grandmaRoom(ctx, o = {}) {
  const key = 'ep01:grandmaRoom:' + JSON.stringify(o);
  const inner = ctx.cache(key, () => {
    const P = new Parts(); const W0 = -9, W1 = 9, D = 14, H = 12; const wall = 'wp:roses:#f2e2cc';
    rect(P, 'floor:#9f3305', [0, 1, 0], [W0, W1], [0, 0], [-D, 4]); rect(P, 'ceil:#f4ece0', [0, -1, 0], [W0, W1], [H, H], [-D, 4]);
    rect(P, wall, [0, 0, 1], [W0, W1], [0, H], [-D, -D]); rect(P, wall, [-1, 0, 0], [W1, W1], [0, H], [-D, 4]);
    const hole = [-10.5, -4.5, 3.2, 9.0]; wallWithHoles(P, wall, [1, 0, 0], -D, 4, 0, H, W0, [hole]); // window on the left wall (z range)
    const sk = 'gloss:#f1eee8'; P.box(sk, W1 - W0, 0.7, 0.16, [0, 0.35, -D + 0.08]); P.box(sk, 0.16, 0.7, D + 4, [W0 + 0.08, 0.35, -D / 2 + 2]); P.box(sk, 0.16, 0.7, D + 4, [W1 - 0.08, 0.35, -D / 2 + 2]);
    P.box('wood:#6a3a1e', W1 - W0, 0.3, 0.3, [0, 8.6, -D + 0.15]); // dado / picture rail
    // window (left wall): frame, sill, daylight card behind, net curtains + drapes
    P.push(trs([W0, 0, 0], [0, PI / 2, 0])); // wall frame: x' = -z (along the wall), z' = into the room
    const [z0, z1, y0, y1] = hole; const cx = -(z0 + z1) / 2, ww = z1 - z0;
    for (const s of [-1, 1]) P.box(sk, 0.6, y1 - y0 + 1.2, 0.3, [cx + s * (ww / 2 + 0.3), (y0 + y1) / 2, 0.15]); P.box(sk, ww + 1.8, 0.6, 0.3, [cx, y1 + 0.3, 0.15]); P.box(sk, ww + 1.6, 0.25, 1.0, [cx, y0 - 0.12, 0.45]);
    P.box(sk, 0.14, y1 - y0, 0.12, [cx, (y0 + y1) / 2, -0.25]); P.box(sk, ww, 0.14, 0.12, [cx, (y0 + y1) / 2 + 0.6, -0.25]);
    P.add('tex:daylight', new THREE.PlaneGeometry(ww + 2, y1 - y0 + 2), [cx, (y0 + y1) / 2, -1.2]);
    P.add('net:#ffffff', drapeGeo(ww + 0.4, y1 - y0 + 0.4, { folds: 14, amp: 0.05, seed: 2 }), [cx, (y0 + y1) / 2, 0.3]);
    for (const s of [-1, 1]) P.add('fab:#b84a6a', drapeGeo(1.6, H - 1.2, { folds: 4, amp: 0.14, seed: 3 + s }), [cx + s * (ww / 2 + 0.9), (H - 1.2) / 2 + 0.2, 0.55]);
    P.cyl('brass', 0.07, 0.07, ww + 4.4, 8, [cx, y1 + 1.0, 0.55], [0, 0, PI / 2]);
    P.pop();
    decalMat('daylight', daylightTex(), { basic: true, k: 1.6 });
    // furniture
    P.push(trs([0.5, 0, -7.5])); const ac = addArmchair(P, {}); P.pop();
    addRug(P, { r: 3.6, color: '#c88aa8', at: [0.5, 0, -4.2], seed: 5 });
    P.push(trs([-3.6, 0, -6.8])); addSideTable(P); P.pop();
    P.push(trs([4.4, 0, -9.5])); const lamp = addStandardLamp(P); P.pop();
    _mc.set('tex:standardShade', persistMat(Object.assign(new THREE.MeshBasicMaterial({ color: new THREE.Color('#ffefcc').multiplyScalar(1.9), side: THREE.DoubleSide }), { name: 'tex:standardShade' })));
    decalMat('clockFace', clockFaceTex(), { roughness: 0.4 }); P.push(trs([-1.8, 7.0, -D + 0.02])); addCuckooClock(P); P.pop();
    addFrames(P, [[2.6, 6.3, -D + 0.02, 1.6, 1.2, 0, 0], [4.7, 6.8, -D + 0.02, 1.2, 1.5, 0, 1], [3.6, 4.6, -D + 0.02, 1.4, 1.0, 0, 2], [6.2, 5.2, -D + 0.02, 1.0, 1.2, 0, 3], [W1 - 0.02, 6.0, -6.5, 1.8, 1.4, -PI / 2, 1]]);
    // a cabinet with a radio and a vase on the right, a footstool, a plant
    P.push(trs([7.4, 0, -11.8])); P.box('wood:#6a3a1e', 3.0, 3.2, 1.6, [0, 1.6, 0], null, { bevel: 0.06 }); for (const s of [-1, 1]) P.add('brass', new THREE.SphereGeometry(0.1, 8, 6), [s * 0.3, 2.0, 0.82]); P.box('wood:#8a5a2e', 1.5, 0.9, 0.9, [-0.5, 3.65, 0], null, { bevel: 0.08 }); P.add('tex:clockFace', new THREE.CircleGeometry(0.25, 16), [-0.2, 3.65, 0.46]);
    P.add('plastic:#5a9ac8', new THREE.LatheGeometry([[0, 0], [0.3, 0], [0.4, 0.4], [0.22, 0.9], [0.28, 1.1], [0, 1.1]].map(([x, y]) => new THREE.Vector2(x, y)), 14), [0.9, 3.2, 0]); for (let i = 0; i < 4; i++) P.add('tulip:' + ['#e85a7a', '#f2c230', '#f4f0ea', '#e85a7a'][i], new THREE.SphereGeometry(0.2, 8, 6), [0.9 + Math.cos(i * 1.6) * 0.25, 4.6 + (i % 2) * 0.2, Math.sin(i * 1.6) * 0.25]); P.pop();
    P.push(trs([3.3, 0, -3.3])); P.add('fab:#8a3a5a', new RoundedBoxGeometry(1.8, 1.1, 1.4, 3, 0.25), [0, 0.75, 0]); for (const [x, z] of [[-0.7, -0.5], [0.7, -0.5], [-0.7, 0.5], [0.7, 0.5]]) P.cyl('wood:#4a2414', 0.08, 0.06, 0.3, 6, [x, 0.12, z]); P.pop();
    P.push(trs([-7.2, 0, -12.0])); P_.addPotPlant(P, { seed: 4, blossom: '#e0485a' }); P.pop();
    const inner = new THREE.Group(); inner.name = 'grandmaRoom'; inner.add(persistTree(P.build(XM, { name: 'roomMesh' })));
    inner.traverse((m) => { if (m.isMesh && m.name === 'tex:standardShade') m.name = 'lampShade'; });
    const A = { seat: [0.5, ac.seatTop, -7.2], seatYaw: 0, lamp: [4.4, lamp[1], -9.5], window: [W0, 6.1, -7.5], windowNormal: [1, 0, 0], rug: [0.5, 0.1, -4.2], table: [-3.6, 2.3, -6.8] };
    // s06/s07: MS eye at the seated head, h 3.6, d 7.5, yaw -15 (camera toward +Z from the chair, turned 15 deg)
    const head = [0.5, 4.3, -7.2]; const yaw = -15 * DEG, dist = 7.5; const cp = [head[0] + Math.sin(yaw) * dist, 3.6, head[2] + Math.cos(yaw) * dist];
    A.views = { armchairMS: { pos: cp, target: [head[0], head[1] - 1.2, head[2]], fov: 70 }, armchairCU: { pos: [head[0] - 0.6, 4.2, head[2] + 3.2], target: [head[0], 4.1, head[2]], fov: 70 }, wide: { pos: [2.5, 6.0, 3.5], target: [-0.5, 3.0, -8], fov: 70 } };
    inner.userData.anchors = A; return inner;
  });
  const c = inner.clone(true); return wrapRoom(c, c.userData.anchors, 'grandmaRoom');
}

// ------------------------------------------------------------------ OUR HALL (the night of the move)
// Narrow hall 8 studs wide (x -4..4), the front door at the far end (z = -12) facing +Z: dark red, a 4-pane glass panel
// at head height with the night garden behind it; the wall clock above the left boxes (hands at 9:00 via setClock),
// the hero's rolled sleeping bag on a mat, three boxes marked THEO, coat hooks with a mustard hoodie, a runner rug, bare
// picture hooks (packed house).
function nightGardenTex() {
  return ctex('nightGardenView', 256, 256, (g, W, H) => {
    const gr = g.createLinearGradient(0, 0, 0, H); gr.addColorStop(0, '#05041a'); gr.addColorStop(0.55, '#1a1648'); gr.addColorStop(0.62, '#2a3a5a'); gr.addColorStop(1, '#1a2a3a'); g.fillStyle = gr; g.fillRect(0, 0, W, H);
    const r = makeRng(3); for (let k = 0; k < 60; k++) { g.fillStyle = `rgba(255,255,255,${0.3 + 0.6 * r()})`; g.fillRect(r() * W, r() * H * 0.5, 1.5, 1.5); }
    g.fillStyle = '#c8c4e8'; for (let x = 6; x < W; x += 14) { g.fillRect(x, H * 0.66, 6, 30); } g.fillRect(0, H * 0.7, W, 4); // picket fence
    const lg = g.createRadialGradient(W * 0.8, H * 0.45, 2, W * 0.8, H * 0.45, 40); lg.addColorStop(0, 'rgba(255,214,150,1)'); lg.addColorStop(1, 'rgba(255,214,150,0)'); g.fillStyle = lg; g.fillRect(0, 0, W, H); g.fillStyle = '#ffe2b0'; g.beginPath(); g.arc(W * 0.8, H * 0.45, 4, 0, PI * 2); g.fill();
  });
}
function doorPanelTex(color = '#7a1f1a') { // front door with a 4-pane glass panel at head height (panes are transparent)
  return ctex('hallDoor:' + color, 192, 384, (g, W, H) => {
    const c = new THREE.Color(color); const col = (k) => `rgb(${Math.round(Math.min(255, c.r * 255 * k))},${Math.round(Math.min(255, c.g * 255 * k))},${Math.round(Math.min(255, c.b * 255 * k))})`;
    g.fillStyle = col(1); g.fillRect(0, 0, W, H); for (let y = 0; y < H; y += 2) { g.fillStyle = `rgba(0,0,0,${0.03 + 0.03 * Math.sin(y * 0.37)})`; g.fillRect(0, y, W, 2); }
    g.clearRect(30, 40, 60, 60); g.clearRect(102, 40, 60, 60); g.clearRect(30, 110, 60, 60); g.clearRect(102, 110, 60, 60);
    for (const [x, y, w, h] of [[24, 200, 66, 150], [102, 200, 66, 150]]) { g.fillStyle = col(0.62); g.fillRect(x, y, w, 7); g.fillRect(x, y, 7, h); g.fillStyle = col(1.3); g.fillRect(x, y + h - 7, w, 7); g.fillRect(x + w - 7, y, 7, h); }
  });
}
export function hall(ctx, o = {}) {
  const key = 'ep01:hall:' + JSON.stringify(o);
  const inner = ctx.cache(key, () => {
    const P = new Parts(); const X0 = -4, X1 = 4, Z0 = -12, Z1 = 6, H = 12; const wall = 'wp:fabric:#c8b8d8';
    rect(P, 'floor:#8a3a14', [0, 1, 0], [X0, X1], [0, 0], [Z0, Z1]); rect(P, 'ceil:#ece4f0', [0, -1, 0], [X0, X1], [H, H], [Z0, Z1]);
    const dz = Z0, dw = 4, dh = 7.5; wallWithHoles(P, wall, [0, 0, 1], X0, X1, 0, H, dz, [[-dw / 2, dw / 2, 0, dh]]);
    rect(P, wall, [1, 0, 0], [X0, X0], [0, H], [Z0, Z1]); rect(P, wall, [-1, 0, 0], [X1, X1], [0, H], [Z0, Z1]);
    const sk = 'gloss:#f1eee8'; for (const x of [X0 + 0.08, X1 - 0.08]) P.box(sk, 0.16, 0.6, Z1 - Z0, [x, 0.3, (Z0 + Z1) / 2]); P.box(sk, X1 - X0, 0.6, 0.16, [0, 0.3, Z0 + 0.08]);
    for (const s of [-1, 1]) P.box(sk, 0.5, dh + 0.5, 0.3, [s * (dw / 2 + 0.25), (dh + 0.5) / 2, dz + 0.15]); P.box(sk, dw + 1.0, 0.5, 0.3, [0, dh + 0.25, dz + 0.15]);
    // front door (separate textured plane with alpha holes for the glass) + glass + the night garden card behind
    decalMat('hallDoor', doorPanelTex(o.door || '#7a1f1a'), { roughness: 0.5, transparent: false }); _mc.get('tex:hallDoor').alphaTest = 0.5;
    P.add('tex:hallDoor', new THREE.PlaneGeometry(dw, dh), [0, dh / 2, dz + 0.02]); P.add('brass', new THREE.SphereGeometry(0.18, 10, 8), [1.4, 3.6, dz + 0.18]); P.box('brass', 0.6, 0.15, 0.08, [0, 4.8, dz + 0.06]);
    P.box('gloss:' + shade(o.door || '#7a1f1a', 0.85), 0.12, 2.9, 0.08, [0, 6.0, dz + 0.04]); P.box('gloss:' + shade(o.door || '#7a1f1a', 0.85), dw - 1.0, 0.12, 0.08, [0, 6.0, dz + 0.04]);
    P.add('tex:nightGarden', new THREE.PlaneGeometry(dw + 3, dh + 3), [0, dh / 2, dz - 1.5]); decalMat('nightGarden', nightGardenTex(), { basic: true, k: 0.9 });
    // runner rug, the mat, sleeping bag (rolled), three THEO boxes, coat hooks + mustard hoodie, bare picture hooks
    P.add('rug:#8a3a5a', new RoundedBoxGeometry(3.2, 0.08, 12, 2, 0.04), [0, 0.05, -3.5]); for (let i = 0; i < 12; i++) P.box('rug:#e8c8a0', 3.0, 0.09, 0.15, [0, 0.06, -9.2 + i * 1.0]);
    P.box('rug:#5a4a3a', 2.6, 0.1, 1.6, [0, 0.06, dz + 1.3]);
    P.add('fab:#2f6ab8', new THREE.CylinderGeometry(0.75, 0.75, 2.6, 24), [-1.9, 0.78, dz + 2.6], [0, 0, PI / 2]); for (const s of [-1, 1]) P.add('black:#1a1a1e', new THREE.TorusGeometry(0.78, 0.06, 6, 24), [-1.9 + s * 0.8, 0.78, dz + 2.6], [0, PI / 2, 0]); P.add('fab:#f2c230', new THREE.CircleGeometry(0.7, 20), [-0.58, 0.78, dz + 2.6], [0, PI / 2, 0]);
    addBoxes(P, ['THEO', 'THEO', 'THEO'], [2.4, 0, dz + 2.3, -0.15], 4);
    for (let i = 0; i < 4; i++) P.box('brass', 0.12, 0.12, 0.45, [X0 + 0.25, 6.4, -6 + i * 1.1]); P.box('wood:#6a3a1e', 0.2, 0.5, 4.8, [X0 + 0.12, 6.4, -4.4]);
    P.push(trs([X0 + 0.55, 6.2, -5.0], [0, PI / 2, 0])); P.add('fab:#d9a52c', drapeGeo(1.8, 3.2, { folds: 4, amp: 0.15, seed: 9 }), [0, -1.4, 0]); P.add('fab:#d9a52c', new THREE.SphereGeometry(0.55, 12, 8), [0, 0.1, 0], null, [1.2, 0.8, 0.6]); P.pop();
    for (const [z, y] of [[-8, 7.5], [-1, 8.0], [2.5, 6.8]]) P.add('brass', new THREE.SphereGeometry(0.07, 6, 4), [X1 - 0.05, y, z]);
    P.add('wp:fabric:#d6c8e4', new THREE.PlaneGeometry(2.4, 3.0), [X1 - 0.03, 6.2, -1], [0, -PI / 2, 0]);
    const inner = new THREE.Group(); inner.name = 'hall'; inner.add(persistTree(P.build(XM, { name: 'hallMesh' })));
    // ceiling lamp (glass bowl, emissive) + the clock
    const lp = new THREE.Mesh(new THREE.SphereGeometry(0.9, 20, 10, 0, PI * 2, PI / 2, PI / 2), XM('glow:#fff0d0:1.6')); lp.position.set(0, H - 0.05, -4); lp.name = 'ceilingLamp'; inner.add(persistTree(lp));
    const ck = persistTree(clockMesh(1.0)); ck.position.set(-1.8, 9.2, dz + 0.14); inner.add(ck); setClock(ck, 8, 59, 59);
    const A = { clock: [-1.8, 9.2, dz + 0.3], door: [0, 3.75, dz], sleepingBag: [-1.9, 0.8, dz + 2.6], boxes: [2.4, 1.0, dz + 2.3], lamp: [0, H - 1.0, -4] };
    // s26: INS h 6.5, d 3.0, pitch -15, fov 50 (clock above, the bag and boxes below by the door)
    A.views = { clockINS: { pos: [-0.6, 6.5, dz + 9.0], target: [-0.3, 4.2, dz], fov: 50 }, hallWide: { pos: [0, 5.2, Z1 - 1], target: [0, 3.5, dz], fov: 70 } };
    inner.userData.anchors = A; return inner;
  });
  const c = inner.clone(true); const root = wrapRoom(c, c.userData.anchors, 'hall'); root.userData.clock = c.getObjectByName('wallClock');
  root.ep01 = { clock: c.getObjectByName('wallClock'), setClock: (h, m, s) => setClock(c.getObjectByName('wallClock'), h, m, s),
    // minute hand ticks from 8:59:59 onto XII at t0 (1-frame step with a 3-frame spring overshoot), as on "nine"
    tickToNine: (t, t0) => { const u = (t - t0) * 60; const s = u < 0 ? 59 : 60 + (u < 4 ? 0.6 * Math.sin(u / 4 * PI) * Math.exp(-u / 3) : 0); setClock(c.getObjectByName('wallClock'), 8, 59, s); } };
  return root;
}

// ------------------------------------------------------------------ TRUCK CAB INSERT (s48)
// Dashboard (dark plastic), a red 7-segment LED clock "11:52" with a 1 Hz colon, the steering wheel with a yellow sticky
// note "LEAVE 6 AM", windscreen showing the night street (a painted card, darker than the cab). Origin = cab floor centre,
// driver faces -Z (toward the windscreen).
function sevenSegTex(text, colon = true) {
  return ctex('7seg:' + text + colon, 256, 96, (g, W, H) => {
    g.fillStyle = '#0a0204'; g.fillRect(0, 0, W, H);
    const seg = { 0: 'abcdef', 1: 'bc', 2: 'abged', 3: 'abgcd', 4: 'fgbc', 5: 'afgcd', 6: 'afgedc', 7: 'abc', 8: 'abcdefg', 9: 'abcdfg' };
    const dig = (x, d, on = true) => { const w = 34, h = 64, t = 8, y = 16; const S = { a: [x + t, y, w - 2 * t, t], b: [x + w - t, y + t, t, h / 2 - t], c: [x + w - t, y + h / 2, t, h / 2 - t], d: [x + t, y + h - t, w - 2 * t, t], e: [x, y + h / 2, t, h / 2 - t], f: [x, y + t, t, h / 2 - t], g: [x + t, y + h / 2 - t / 2, w - 2 * t, t] };
      for (const k of 'abcdefg') { const lit = on && (seg[d] || '').includes(k); g.fillStyle = lit ? '#ff3a28' : 'rgba(255,58,40,0.08)'; g.fillRect(...S[k]); } };
    const [hh, mm] = text.split(':'); const xs = [20, 66, 140, 186]; [hh[0], hh[1], mm[0], mm[1]].forEach((d, i) => dig(xs[i], d, !(i === 0 && d === '0')));
    if (colon) { g.fillStyle = '#ff3a28'; g.fillRect(118, 34, 9, 9); g.fillRect(118, 60, 9, 9); }
  });
}
function stickyTex(text = 'LEAVE 6 AM') {
  return ctex('sticky:' + text, 256, 256, (g, W, H) => {
    g.fillStyle = '#f7e04a'; g.fillRect(0, 0, W, H); g.fillStyle = 'rgba(0,0,0,0.08)'; g.fillRect(0, 0, W, 26);
    g.save(); g.translate(W / 2, H / 2 + 10); g.rotate(-0.06); g.fillStyle = '#1a1414'; g.textAlign = 'center'; g.textBaseline = 'middle';
    const [a, ...b] = text.split(' '); g.font = `bold italic 78px ${FONT}`; g.fillText(a, 0, -42); g.font = `bold italic 70px ${FONT}`; g.fillText(b.join(' '), 0, 46); g.lineWidth = 6; g.beginPath(); g.moveTo(-90, 92); g.lineTo(96, 86); g.strokeStyle = '#c8281a'; g.stroke(); g.restore();
  });
}
function cabStreetTex() {
  return ctex('cabStreet', 512, 256, (g, W, H) => {
    const gr = g.createLinearGradient(0, 0, 0, H); gr.addColorStop(0, '#020214'); gr.addColorStop(0.5, '#0c0a2a'); gr.addColorStop(0.62, '#1a1a30'); gr.addColorStop(1, '#0e0e18'); g.fillStyle = gr; g.fillRect(0, 0, W, H);
    const r = makeRng(9); for (let k = 0; k < 80; k++) { g.fillStyle = `rgba(255,255,255,${0.2 + 0.5 * r()})`; g.fillRect(r() * W, r() * H * 0.4, 1.5, 1.5); }
    for (let i = 0; i < 5; i++) { const x = 40 + i * 110, w = 80, h = 50 + r() * 30, y = H * 0.6 - h; g.fillStyle = '#1e1c3a'; g.fillRect(x, y, w, h); g.beginPath(); g.moveTo(x - 8, y); g.lineTo(x + w / 2, y - 26); g.lineTo(x + w + 8, y); g.fill(); g.fillStyle = r() < 0.6 ? '#ffcf80' : '#2a2a48'; g.fillRect(x + 12, y + 14, 16, 18); g.fillStyle = r() < 0.5 ? '#ffcf80' : '#2a2a48'; g.fillRect(x + 50, y + 14, 16, 18); }
    for (const x of [70, 300, 470]) { const lg = g.createRadialGradient(x, H * 0.38, 1, x, H * 0.38, 40); lg.addColorStop(0, 'rgba(255,200,120,0.95)'); lg.addColorStop(1, 'rgba(255,200,120,0)'); g.fillStyle = lg; g.fillRect(x - 40, H * 0.38 - 40, 80, 80); g.fillStyle = '#0a0a12'; g.fillRect(x - 2, H * 0.4, 4, H * 0.3); }
    g.fillStyle = '#e8b422'; for (let x = 0; x < W; x += 60) g.fillRect(x, H * 0.85, 30, 4);
  });
}
export function truckCab(ctx, o = {}) {
  const inner = ctx.cache('ep01:truckCab:' + JSON.stringify(o), () => {
    const P = new Parts(); const dk = 'plastic:#2a2830', W = 9;
    P.box(dk, W, 2.4, 2.6, [0, 3.0, -3.2], null, { bevel: 0.2 }); P.box(dk, W, 0.8, 1.4, [0, 4.4, -3.9], [-0.3, 0, 0], { bevel: 0.15 });
    P.box('plastic:#1a181e', 2.6, 1.2, 0.3, [-2.2, 4.05, -2.55], [-0.35, 0, 0], { bevel: 0.08 }); // instrument binnacle
    for (const x of [-2.9, -1.5]) P.add('tex:clockFace', new THREE.CircleGeometry(0.45, 20), [x, 4.1, -2.38], [-0.35, 0, 0]);
    P.box('plastic:#1a181e', 2.2, 0.9, 0.2, [1.4, 3.75, -1.95], [-0.2, 0, 0], { bevel: 0.05 }); // clock/radio panel
    for (let i = 0; i < 4; i++) P.cyl('metal:#5a5a62', 0.12, 0.12, 0.15, 10, [0.6 + i * 0.5, 3.35, -1.85], [PI / 2 - 0.2, 0, 0]);
    P.box('plastic:#3a3640', W, 0.3, 4, [0, 0.15, -1]); // floor
    // windscreen frame + glass + the street card beyond
    for (const s of [-1, 1]) P.box(dk, 0.5, 4.6, 0.5, [s * (W / 2 - 0.25), 6.6, -4.4], [0.25 * 0, 0, 0]); P.box(dk, W, 0.5, 0.6, [0, 9.0, -4.6]);
    P.add('tex:cabStreet', new THREE.PlaneGeometry(W * 2.6, 9), [0, 6.8, -14]); decalMat('cabStreet', cabStreetTex(), { basic: true, k: 0.75 }); decalMat('clockFace', clockFaceTex(), { roughness: 0.4 });
    // steering wheel (driver left), column
    P.push(trs([-2.2, 4.0, -1.6], [-1.05, 0, 0])); P.add('black:#16161a', new THREE.TorusGeometry(1.25, 0.14, 10, 36)); for (const a of [0, 2.1, 4.2]) P.bar('black:#16161a', [0, 0, 0], [Math.cos(a) * 1.2, Math.sin(a) * 1.2, 0], 0.18, 0.1); P.cyl('black:#16161a', 0.35, 0.35, 0.3, 16, [0, 0, 0], [PI / 2, 0, 0]);
    P.add('tex:sticky', new THREE.PlaneGeometry(0.85, 0.85), [0.15, -0.55, 0.2], [0, 0, 0.12]); P.pop(); decalMat('sticky', stickyTex(o.note || 'LEAVE 6 AM'), { roughness: 0.8 });
    P.cyl('black:#16161a', 0.18, 0.2, 2.0, 10, [-2.2, 3.3, -2.3], [-1.05, 0, 0]);
    // seat backs (foreground, blurred out of frame), a coffee cup in the holder, a map
    P.add('fab:#4a4a58', new RoundedBoxGeometry(3.4, 4.2, 1.0, 3, 0.3), [-2.2, 3.6, 3.6]); P.cyl('plastic:#f4f0ea', 0.22, 0.17, 0.5, 14, [0.6, 3.15, -1.5]); P.cyl('plastic:#3a2a1a', 0.23, 0.23, 0.06, 14, [0.6, 3.42, -1.5]);
    P.add('tex:mapCard', new THREE.PlaneGeometry(1.6, 1.1), [3.0, 4.42, -3.6], [-PI / 2 + 0.3, 0, 0.2]); decalMat('mapCard', ctex('mapCard', 128, 96, (g, W2, H2) => { g.fillStyle = '#efe6cc'; g.fillRect(0, 0, W2, H2); g.strokeStyle = '#c8402a'; g.lineWidth = 3; g.beginPath(); g.moveTo(10, 80); g.bezierCurveTo(40, 20, 80, 70, 118, 14); g.stroke(); g.strokeStyle = '#5a8ac0'; g.lineWidth = 2; for (let i = 0; i < 6; i++) { g.beginPath(); g.moveTo(0, i * 16); g.lineTo(W2, i * 16 + 10); g.stroke(); } }), { roughness: 0.8 });
    const inner = new THREE.Group(); inner.name = 'truckCab'; inner.add(persistTree(P.build(XM, { name: 'cabMesh' })));
    // LED clock: two textures (colon on/off) swapped at 1 Hz
    const led = new THREE.Mesh(new THREE.PlaneGeometry(1.7, 0.64), decalMat('led:on:' + (o.time || '11:52'), sevenSegTex(o.time || '11:52', true), { basic: true, k: 2.2 }));
    decalMat('led:off:' + (o.time || '11:52'), sevenSegTex(o.time || '11:52', false), { basic: true, k: 2.2 });
    led.position.set(1.4, 3.78, -1.83); led.rotation.x = -0.2; led.name = 'ledClock'; inner.add(persistTree(led));
    const glass = new THREE.Mesh(new THREE.PlaneGeometry(W - 1, 4.2), new THREE.MeshStandardMaterial({ color: '#202848', transparent: true, opacity: 0.22, roughness: 0.05, metalness: 0.3, depthWrite: false })); glass.position.set(0, 6.6, -4.45); glass.rotation.x = -0.25; inner.add(persistTree(glass));
    const A = { led: [1.4, 3.78, -1.83], note: [-2.05, 3.5, -1.4], wheel: [-2.2, 4.0, -1.6], windscreen: [0, 6.6, -4.5] };
    // s48: INS h 3.6, d 1.6, yaw -10, pitch -8, fov 45: the LED clock and the sticky note together
    A.views = { clockINS: { pos: [0.2, 5.2, 2.6], target: [-0.2, 3.7, -1.7], fov: 45 }, ledECU: { pos: [1.6, 4.1, 0.2], target: [1.4, 3.78, -1.83], fov: 45 } };
    inner.userData.anchors = A; return inner;
  });
  const c = inner.clone(true); const root = wrapRoom(c, c.userData.anchors, 'truckCab');
  const led = c.getObjectByName('ledClock'); const tm = o.time || '11:52';
  root.ep01 = { led, update(t, T = t) { led.material = XM((Math.floor(T * 1) % 2 === 0 ? 'tex:led:on:' : 'tex:led:off:') + tm); } };
  return root;
}

// ------------------------------------------------------------------ LIGHT PRESETS (VISUAL_BIBLE §5)
// Common: returns rig = { hemi, key, lights: [...], update(t) }; sets the post preset (fog off: interiors).
function worldOf(root, p) { root.updateMatrixWorld(true); return new THREE.Vector3(...p).applyMatrix4(root.matrixWorld); }
function haloSprite(pos, color, size, opacity = 0.55) { const s = new THREE.Sprite(glowSpriteMat('ep01halo:' + color, { color, intensity: 1.2, opacity, falloff: 2.2 })); s.position.copy(pos); s.scale.set(size, size, 1); s.name = 'halo'; return s; }
// interiorDay(ctx, { room }) - Grandma's room: hemi #ffe8d0 / #6a4a3a 1.1, window key #fff3e0 2.0 from upper front-left
// (soft, no shadow), standard-lamp practical 2 cd, post 'day'.
export function interiorDay(ctx, o = {}) {
  const rig = { lights: [], update: () => {} }; const room = o.room;
  rig.hemi = ctx.add(ctx.lights.hemi('#ffe8d0', '#6a4a3a', o.hemiIntensity ?? 1.1));
  rig.key = ctx.add(keyLight(ctx, { color: '#fff3e0', intensity: o.key ?? 2.0, el: 40, side: 0.6 }));
  if (room && room.userData.anchors) {
    const A = room.userData.anchors; const S = room.userData.stud ? 1 : 1;
    if (A.lamp) { const p = new THREE.Vector3(...A.lamp); rig.lights.push(ctx.add(ctx.lights.point({ color: '#ffe0b0', intensity: o.lamp ?? 2, pos: p.toArray(), decay: 2 }))); ctx.add(haloSprite(p, '#ffe6c0', 0.9, 0.35)); }
    if (A.window) { const w = new THREE.Vector3(...A.window); const n = new THREE.Vector3(...(A.windowNormal || [1, 0, 0])); rig.lights.push(ctx.add(ctx.lights.point({ color: '#fff3e0', intensity: o.window ?? 6, pos: w.clone().addScaledVector(n, 0.9).toArray(), decay: 2 }))); void S; }
  }
  ctx.post.set(postPreset('day', o.postOpts || {})); return rig;
}
// bedroomNight(ctx, { set | room, lamp: cd (3-5), moon: true, lanternOutside: false | { pos, cd }, nightlight: cd, glass })
// Bible P2: hemi #b9a8ff / #5a2a4a 1.3, key #e8deff 1.0 from upper front-left, the bedside lamp 3-5 cd + halo,
// moonlight #9aa6ff at 0.4x through the window, optional warm lantern spill (#ffb85c 2 cd) outside the window, the
// galaxy sky through the glass, post 'bedroom'. The window view is kept darker than the room (inside glass look).
// `set` = a heroLot (uses its Theo room) or `room` = any root carrying userData.anchors in metres.
export function bedroomNight(ctx, o = {}) {
  const rig = { lights: [], update: () => {} }; const H = o.set && o.set.ep01 ? o.set.ep01 : null;
  const A = H ? H.room : (o.room ? o.room.userData.anchors : null);
  rig.sky = makeSky(ctx, { preset: o.skyPreset || 'galaxy', moon: o.moonDisc ?? { az: -20, el: 28, size: 7, style: 'tf' } }); ctx.add(rig.sky);
  rig.hemi = ctx.add(ctx.lights.hemi('#b9a8ff', '#5a2a4a', o.hemiIntensity ?? 1.3));
  rig.key = ctx.add(keyLight(ctx, { color: '#e8deff', intensity: o.key ?? 1.0, el: 45, side: 0.55 }));
  if (A) {
    if (A.lamp && o.lamp !== 0 && o.lamp !== false) { const p = new THREE.Vector3(...A.lamp); rig.lamp = ctx.add(ctx.lights.point({ color: '#ffe6c0', intensity: o.lamp ?? 4, pos: p.toArray(), decay: 2 })); rig.lights.push(rig.lamp); ctx.add(haloSprite(p, '#fff0d0', 0.8, 0.4)); }
    if (A.nightlight && o.nightlight !== 0) { const p = new THREE.Vector3(...A.nightlight); rig.night = ctx.add(ctx.lights.point({ color: '#ffd8f0', intensity: o.nightlight ?? 2.5, pos: p.toArray(), decay: 2 })); rig.lights.push(rig.night); ctx.add(haloSprite(p, '#ffe0f4', 0.5, 0.5)); }
    const win = A.windowWorld || A.window?.center; const n = new THREE.Vector3(...(A.windowNormal || A.window?.normal || [0, 0, 1]));
    if (win && o.moon !== false) { const w = new THREE.Vector3(...win); rig.moon = ctx.add(ctx.lights.sun({ color: '#9aa6ff', intensity: 0.4 * (o.key ?? 1.0) * (o.moonK ?? 1), pos: w.clone().addScaledVector(n, 12).add(new THREE.Vector3(0, 9, 0)).toArray(), target: w.clone().addScaledVector(n, -3).toArray(), shadow: false })); }
    if (win && o.lanternOutside) { const lo = o.lanternOutside === true ? {} : o.lanternOutside; const p = lo.pos ? new THREE.Vector3(...lo.pos) : new THREE.Vector3(...win).addScaledVector(n, 1.0).add(new THREE.Vector3(0, -0.5, 0)); rig.lantern = ctx.add(ctx.lights.point({ color: '#ffb85c', intensity: lo.cd ?? 2, pos: p.toArray(), decay: 2 })); rig.lights.push(rig.lantern); }
  }
  if (H && H.setGlass) H.setGlass(o.glass || 'inside');
  ctx.post.set(postPreset('bedroom', o.postOpts || {})); return rig;
}
// cabNight(ctx, { cab }) - s48: dashboard LED glow 1 cd #ff5040 + #ffd9a0 street spill through the windscreen, hemi
// #8a90ff 0.6, post 'night'.
export function cabNight(ctx, o = {}) {
  const rig = { lights: [], update: () => {} }; const A = o.cab ? o.cab.userData.anchors : null;
  rig.hemi = ctx.add(ctx.lights.hemi('#8a90ff', '#2a1a3a', o.hemiIntensity ?? 0.6));
  rig.key = ctx.add(keyLight(ctx, { color: '#b4b8ff', intensity: 0.6, el: 50, side: 0.5 }));
  if (A) {
    const led = new THREE.Vector3(...A.led); rig.lights.push(ctx.add(ctx.lights.point({ color: '#ff5040', intensity: o.led ?? 1, pos: led.clone().add(new THREE.Vector3(0, 0.1, 0.25)).toArray(), decay: 2 })));
    const ws = new THREE.Vector3(...A.windscreen); rig.lights.push(ctx.add(ctx.lights.point({ color: '#ffd9a0', intensity: o.street ?? 2.2, pos: ws.clone().add(new THREE.Vector3(-0.6, 0.3, -1.2)).toArray(), decay: 2 })));
  }
  ctx.post.set(postPreset('night', { exposure: 1.15, ...(o.postOpts || {}) })); return rig;
}
export { wrapRoom, clockMesh, addBed, addCurtains, addInnerWindowFrame, drapeGeo, duvetGeo, pillowGeo, addRug, addTeddy, addShelf, addNightstand, addLamp, addBoxes };
