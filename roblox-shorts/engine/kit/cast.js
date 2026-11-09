// EP01 cast presets (R6 humans). The 5-second test uses GRANDPA, GRANDMA and the Grandpa gnome (gnome.js).
//   makeCharacter('grandpa', { face: 'content' })  -> avatar root (metres unless units: 'stud')
import { makeAvatar, SKIN, rig, setFace, setPose, POSES } from './avatar.js';
import { OUTFITS, HAIR, PARTS, faceRects } from './clothing.js';
import { hairMat, hairCapGeo, hatGroup } from './accessories.js';
import { drawFace, FACE_RES } from './faces.js';
import { THREE, cached, keyOf, mesh, group, canvas, canvasTex, makeRng, hash32, rgba, shade, clumpGeo, claimMat } from './util.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

export const CAST = {
  // Older styling: white hair (bald crown + puffy side tufts), 3D walrus moustache, soft grey brows, round gold glasses,
  // navy cardigan over a blue check shirt, grey trousers, tartan slippers. The gnome wears the same blue for its coat.
  grandpa: { skin: SKIN.elder, outfit: OUTFITS.grandpaCardigan, face: 'neutral', faceOverlays: { wrinkles: true, brows: '#e4e0e8' },
    accessories: [{ type: 'hair', style: 'grandpa', color: HAIR.white }, { type: 'moustache', color: HAIR.white }, { type: 'glasses', style: 'round', color: '#c9a24e' }] },
  // Grey bun, round rose-gold glasses, rose cardigan over a floral blouse with pearls, plum skirt, slippers.
  grandma: { skin: SKIN.peach, outfit: OUTFITS.grandmaCardigan, face: 'neutral', faceOverlays: { wrinkles: true, blush: '#ff7f8f' },
    accessories: [{ type: 'hair', style: 'bun', color: HAIR.silver }, { type: 'glasses', style: 'round', color: '#d98aa8' }] },
  // Script variants (flashback Grandpa, the narrator at 71)
  grandpaFlashback: { skin: SKIN.elder, outfit: OUTFITS.grandpaFlashback, faceOverlays: { wrinkles: true, brows: '#e4e0e8' },
    accessories: [{ type: 'hair', style: 'grandpa', color: HAIR.white }, { type: 'moustache', color: HAIR.white }, { type: 'hat', style: 'fishing', color: '#6f7342' }] },
  heroOld: { skin: SKIN.salmon, outfit: { shirt: { style: 'cardigan', color: '#d9a52c', trim: '#b98a1e', buttons: '#6b4a2a', inner: { color: '#efe6d2' } }, pants: OUTFITS.grandpaFlashback.pants },
    faceOverlays: { wrinkles: true, freckles: true, brows: '#cfcbd2' }, accessories: [{ type: 'hair', style: 'grandpa', color: HAIR.grey }, { type: 'moustache', color: HAIR.grey }, { type: 'hat', style: 'fishing', color: '#6f7342' }] },
  // EP01 hero (11): mustard hoodie, messy brown hair, freckles.
  hero: { skin: SKIN.salmon, outfit: OUTFITS.heroHoodie, faceOverlays: { freckles: true }, accessories: [{ type: 'hair', style: 'messy', color: HAIR.brown }, { type: 'hood', color: '#d9a52c' }] },
  heroBarefoot: { skin: SKIN.salmon, outfit: { shirt: OUTFITS.heroHoodie.shirt, pants: { ...OUTFITS.heroHoodie.pants, shoes: { style: 'barefoot' } } }, faceOverlays: { freckles: true }, accessories: [{ type: 'hair', style: 'messy', color: HAIR.brown }, { type: 'hood', color: '#d9a52c' }] },
  // Theo (6): oversized blue pyjamas, x0.85.
  theo: { skin: SKIN.light, scale: 0.85, outfit: OUTFITS.theoPyjamas, accessories: [{ type: 'hair', style: 'short', color: HAIR.blond }] },
  mom: { skin: SKIN.peach, outfit: OUTFITS.momSweater, accessories: [{ type: 'hair', style: 'bob', color: HAIR.ginger }] },
  dad: { skin: SKIN.light, outfit: OUTFITS.dadPlaid, faceOverlays: { stubble: true }, accessories: [{ type: 'hair', style: 'short', color: HAIR.darkBrown }] },
};
export function makeCharacter(name, extra = {}) {
  const c = CAST[name]; if (!c) throw new Error('unknown cast member ' + name);
  return castAvatar({ name, ...c, ...extra, faceOverlays: { ...(c.faceOverlays || {}), ...(extra.faceOverlays || {}) } });
}

// =====================================================================================================================
// EP01 full episode: new cast + variants (ASSETS.md "CREATURES + CAST"). Existing members above are unchanged: a spec
// without any of the options below goes straight to makeAvatar (same object, same result).
//   Options understood by makeCharacter / castAvatar on top of makeAvatar's:
//     hand: 'sleeve' (top level or outfit.shirt.hand)  sleeves run to the end of the arm box (sleeves swallow the hands)
//     mud: { knees: 0..1, feet: 0..1 } (or outfit.pants.mud)   brown blotches on the knee band and the feet
//     outfit.pants.shoes.pattern (style 'socks')                striped socks painted over the sock band (h = band height)
//     outfit.shirt.print / outfit.pants.print = { motif: 'hearts'|'whales'|'rockets', color, color2, density, size }
//     accessories: extra types 'pigtails' { color, ribbon }, 'ears' { size }, 'beard' { color, moustache }, 'cap' { color, band }
//     face: any FACES name or an EXTRA_FACES name ('wink');  pose: a POSES name or pose object (applied once)
// =====================================================================================================================
const PI_ = Math.PI, DEG_ = PI_ / 180;
const EXTRA_ACC = ['pigtails', 'ears', 'beard', 'cap'];
const sleeveOutfit = (o) => ({ ...o, shirt: { ...o.shirt, hand: 0 } });

// ---------------- extra faces (same line weights as faces.js: drawn on top of the neutral face + overlays) ----------
export const EXTRA_FACES = {
  // wink: the character's left eye (viewer's right) closed as the ^^ arc, the other eye the base oval, smile arc
  wink(g, ov) {
    drawFace(g, 'neutral', ov);
    g.save(); g.globalCompositeOperation = 'destination-out'; g.beginPath(); g.ellipse(316, 242, 30, 41, 0, 0, 2 * PI_); g.fill(); g.restore();
    g.strokeStyle = '#141414'; g.lineWidth = 10; g.lineCap = 'round'; g.beginPath(); g.arc(316, 262, 28, 200 * DEG_, 340 * DEG_); g.stroke();
    g.lineWidth = 5; g.beginPath(); g.moveTo(342, 252); g.lineTo(352, 244); g.stroke();
  },
};
export function faceTextureEx(name, overlays = {}, res = FACE_RES) {
  if (!EXTRA_FACES[name]) return null;
  return cached(keyOf('faceEx', name, overlays, res), () => { const c = canvas(res), g = c.getContext('2d'); g.scale(res / 512, res / 512); EXTRA_FACES[name](g, overlays); return canvasTex(c, { srgb: true, aniso: 8 }); });
}
// setFace that also knows the EXTRA_FACES (use it wherever a shot may show 'wink'); instant swap, per-avatar material.
export function setFaceEx(root, name, overlays) {
  if (!EXTRA_FACES[name]) return setFace(root, name, overlays);
  const R = rig(root); if (!R.face) return; const tex = faceTextureEx(name, overlays || root.userData.faceOverlays || {});
  if (R.face.material.map !== tex) { let m = R.face.material; if (m.userData.owner !== R.face.uuid) { m = m.clone(); m.userData = { owner: R.face.uuid }; R.face.material = m; } m.map = tex; }
  root.userData.face = name;
}

// ---------------- extra accessories (head-local studs, like accessories.js) ----------------
const _place = (geo, pos, rot = [0, 0, 0], sc = [1, 1, 1]) => { const m = new THREE.Matrix4().compose(new THREE.Vector3(...pos), new THREE.Quaternion().setFromEuler(new THREE.Euler(rot[0], rot[1], rot[2], 'YXZ')), new THREE.Vector3(...(typeof sc === 'number' ? [sc, sc, sc] : sc))); const g = geo.index ? geo.toNonIndexed() : geo.clone(); g.applyMatrix4(m); return g; };
const _merge = (list) => { const g = mergeGeometries(list.map((x) => { const y = x.index ? x.toNonIndexed() : x; for (const k of Object.keys(y.attributes)) if (!['position', 'normal', 'uv'].includes(k)) y.deleteAttribute(k); return y; })); g.computeBoundingSphere(); return g; };
const _clumpAt = (anchor, yaw, pitch, R, L, bend = 0, curl = 0, seg = 14) => _place(clumpGeo(R, L, bend, curl, seg), anchor, [-pitch, yaw, 0]);
const accMat = (color, rough = 0.45) => cached(keyOf('castAccMat', color, rough), () => new THREE.MeshStandardMaterial({ color, roughness: rough, metalness: 0 }));
const EXTRA = {
  // Two side pigtails with ribbon bows over a smooth cap and a short fringe (cousinKid, theoGranddaughter).
  pigtails(head, s) {
    const geo = cached(keyOf('castPigtailsGeo', s.seed || 1), () => {
      const r = makeRng(hash32('pigtails', s.seed || 1)), L = [hairCapGeo({ front: 0.36, side: 0.04, back: -0.2, thick: 0.085, lump: 0.14, seed: 21 })];
      for (let i = 0; i < 6; i++) { const x = -0.4 + i * 0.16; L.push(_clumpAt([x, 0.52, 0.43], 0.25 * (i - 2.5) * 0.3, PI_ * 0.17 + r() * 0.05, 0.13, 0.22 + r() * 0.05, 0.15, 0)); }
      for (const sg of [1, -1]) { L.push(_clumpAt([sg * 0.62, 0.22, -0.14], sg * (PI_ / 2 + 0.35), PI_ * 0.22, 0.17, 0.5, sg * 0.18, 0.05, 18)); L.push(_clumpAt([sg * 0.66, 0.08, -0.2], sg * (PI_ / 2 + 0.5), PI_ * 0.16, 0.14, 0.42, sg * 0.1, 0.1, 16)); }
      return _merge(L);
    });
    const G = new THREE.Group(); G.name = 'pigtails'; mesh(geo, hairMat(s.color || '#e8c24a', 0.46), { parent: G, name: 'hair' });
    const bow = cached('castBowGeo', () => _merge([_place(new THREE.SphereGeometry(0.1, 16, 12), [0, 0.07, 0], [0, 0, 0.6], [1.3, 0.55, 0.5]), _place(new THREE.SphereGeometry(0.1, 16, 12), [0, -0.07, 0], [0, 0, -0.6], [1.3, 0.55, 0.5]), _place(new THREE.SphereGeometry(0.06, 12, 10), [0, 0, 0.0], [0, 0, 0], [1, 1, 1])]));
    for (const sg of [1, -1]) mesh(bow, accMat(s.ribbon || '#e05a8a', 0.4), { parent: G, name: 'ribbon', pos: [sg * 0.7, 0.24, -0.16], rot: [0, sg * 1.25, 0] });
    head.add(G); return G;
  },
  // Sticking-out half-disc ears on the drum sides (young Dad: the plant for Dad's ears); skin coloured.
  ears(head, s) {
    const skin = head.getObjectByName('headMesh').material; const R = (s.size || 0.35) * 0.62;
    const geo = cached(keyOf('castEarGeo', R), () => { const sh = new THREE.Shape(); sh.moveTo(0, -R); sh.absarc(0, 0, R, -PI_ / 2, PI_ / 2, false); sh.lineTo(0, -R); const g = new THREE.ExtrudeGeometry(sh, { depth: 0.05, bevelEnabled: true, bevelThickness: 0.025, bevelSize: 0.025, bevelSegments: 3, curveSegments: 20 }); g.translate(0, 0, -0.025); g.computeVertexNormals(); return g; });
    const inner = cached(keyOf('castEarInGeo', R), () => { const sh = new THREE.Shape(); const r = R * 0.6; sh.moveTo(0, -r); sh.absarc(0.02, 0, r, -PI_ / 2, PI_ / 2, false); sh.lineTo(0, -r); return new THREE.ShapeGeometry(sh, 16); });
    const G = new THREE.Group(); G.name = 'ears'; const inM = accMat(shade('#' + skin.color.getHexString(THREE.SRGBColorSpace), 0.8), 0.55);
    for (const sg of [1, -1]) { const e = group('ear' + (sg > 0 ? 'L' : 'R'), G, [sg * 0.55, 0.02, -0.04]); e.rotation.y = sg > 0 ? -0.35 : PI_ + 0.35; mesh(geo, skin, { parent: e, name: 'earMesh' }); mesh(inner, inM, { parent: e, name: 'earInner', pos: [0.02, 0, 0.052], cast: false }); }
    head.add(G); return G;
  },
  // Chunky clump beard from ear to ear, below the mouth (Theo at 40+); optional walrus moustache.
  beard(head, s) {
    const geo = cached(keyOf('castBeardGeo', !!s.moustache, s.length || 1), () => {
      const r = makeRng(hash32('beard', 3)), L = [], len = s.length || 1;
      for (let i = 0; i <= 14; i++) { const a = -PI_ * 0.62 + (i / 14) * PI_ * 1.24, side = Math.abs(a) / (PI_ * 0.62); const y = -0.47 + side * 0.48; const rad = 0.61;
        L.push(_clumpAt([Math.sin(a) * rad, y, Math.cos(a) * rad], a, PI_ * (0.12 + 0.12 * side), 0.1 + 0.05 * side, (0.26 + 0.2 * (1 - side)) * len + r() * 0.06, (r() - 0.5) * 0.2, 0.18 * (1 - side), 14)); }
      for (let i = 0; i < 5; i++) { const a = -0.5 + i * 0.25; L.push(_clumpAt([Math.sin(a) * 0.5, -0.56, Math.cos(a) * 0.5], a, PI_ * 0.06, 0.13, 0.3 * len + r() * 0.08, (r() - 0.5) * 0.3, 0.12, 14)); }
      if (s.moustache) for (const sg of [1, -1]) for (let k = 0; k < 3; k++) L.push(_clumpAt([sg * (0.06 + k * 0.085), -0.14 - k * 0.014, 0.635 - k * 0.035], sg * (0.65 + k * 0.32), PI_ * (0.24 + k * 0.06), 0.085 - k * 0.012, 0.13 + k * 0.035, sg * 0.2, 0.06));
      return _merge(L);
    });
    return mesh(geo, hairMat(s.color || '#cfcbd2', 0.5), { parent: head, name: 'beard' });
  },
  // Beanie-style cap without the pompom (the world-montage grandkid).
  cap(head, s) { const G = hatGroup({ style: 'beanie', color: s.color || '#d0242a', band: s.band || null }); for (const c of [...G.children]) if (c.geometry && c.geometry.type === 'IcosahedronGeometry') G.remove(c); G.name = 'cap'; head.add(G); return G; },
};

// ---------------- painted overlays on the outfit atlases (mud, striped socks, prints) ----------------
function overlayMaterial(base, part, key, painter) {
  return cached(keyOf('castOverlayMat', base.uuid, part, key), () => {
    const src = base.map.image, P = PARTS[part], ppu = src.width / (2 * P.w + 2 * P.d), c = canvas(src.width, src.height), g = c.getContext('2d'); g.drawImage(src, 0, 0);
    const R = faceRects(P.w, P.h, P.d);
    for (const f of ['nx', 'pz', 'px', 'nz', 'py', 'ny']) { const [rx, ry, fw, fh] = R[f]; g.save(); g.setTransform(ppu, 0, 0, ppu, rx * ppu, ry * ppu); g.beginPath(); g.rect(0, 0, fw, fh); g.clip(); painter(g, f, fw, fh, part); g.restore(); }
    const m = base.clone(); m.map = canvasTex(c); m.userData = {}; return m;
  });
}
function applyOverlay(root, parts, key, painter) { for (const p of parts) { const o = root.getObjectByName(p); if (o && o.material && o.material.map) o.material = overlayMaterial(o.material, p, key, painter); } }
function splat(g, x, y, rx, ry, color, alpha, r) { g.globalAlpha = alpha; g.fillStyle = color; g.beginPath(); const n = 14, ph = r() * 6; for (let i = 0; i <= n; i++) { const a = (i / n) * 2 * PI_, k = 0.8 + 0.25 * Math.sin(a * 3 + ph) + 0.12 * r(); const px = x + Math.cos(a) * rx * k, py = y + Math.sin(a) * ry * k; i ? g.lineTo(px, py) : g.moveTo(px, py); } g.closePath(); g.fill(); g.globalAlpha = 1; }
function mudPainter({ knees = 0.8, feet = 0.6, color = '#4a2e1c' } = {}, side) {
  return (g, f, w, h, part) => {
    const r = makeRng(hash32('mud', part, f)); const vertical = !['py', 'ny'].includes(f);
    if (f === 'ny') { if (feet > 0) splat(g, w / 2, h / 2, w * 0.7, h * 0.7, color, 0.75 * feet, r); return; }
    if (!vertical) return;
    const frontU = f === 'pz' ? null : f === 'nx' ? w : f === 'px' ? 0 : null; const back = f === 'nz';
    if (knees > 0 && !back) { const n = Math.round(10 * knees); for (let i = 0; i < n; i++) { const x = frontU == null ? w * (0.15 + 0.7 * r()) : Math.abs(frontU - r() * w * 0.55); const y = 0.82 + r() * 0.42; splat(g, x, y, 0.06 + r() * 0.13, 0.05 + r() * 0.1, r() < 0.3 ? '#2e1c10' : color, (0.45 + 0.3 * r()) * knees, r); }
      for (let i = 0; i < 6 * knees; i++) { g.globalAlpha = 0.5 * knees; g.fillStyle = '#7a5a3c'; g.beginPath(); g.arc(w * r(), 0.75 + r() * 0.6, 0.012 + r() * 0.015, 0, 2 * PI_); g.fill(); } g.globalAlpha = 1; }
    if (feet > 0) { g.globalAlpha = 0.72 * feet; const gr = g.createLinearGradient(0, h - 0.42, 0, h); gr.addColorStop(0, 'rgba(74,46,28,0)'); gr.addColorStop(0.45, color); gr.addColorStop(1, '#2e1c10'); g.fillStyle = gr; g.fillRect(-1, h - 0.42, w + 2, 0.45); g.globalAlpha = 1;
      for (let i = 0; i < 8 * feet; i++) splat(g, r() * w, h - 0.35 - r() * 0.3, 0.025 + r() * 0.04, 0.02 + r() * 0.035, color, 0.6 * feet, r); }
  };
}
function sockPainter(sh) {
  const band = sh.h ?? 0.3, pat = sh.pattern || {}, per = pat.period || 0.1;
  return (g, f, w, h) => { if (f === 'py' || f === 'ny') return; const top = h - band; g.fillStyle = pat.color || '#5a8ad8'; for (let y = top + 0.07; y < h - 0.05; y += per) g.fillRect(-1, y, w + 2, per * 0.5);
    g.fillStyle = 'rgba(0,0,0,0.12)'; g.fillRect(-1, top + 0.055, w + 2, 0.012); const gr = g.createLinearGradient(0, top, 0, h); gr.addColorStop(0, 'rgba(255,255,255,0.08)'); gr.addColorStop(1, 'rgba(0,0,0,0.12)'); g.fillStyle = gr; g.fillRect(-1, top, w + 2, band); };
}
const MOTIF = {
  hearts(g, x, y, s, c) { g.fillStyle = c; g.beginPath(); g.moveTo(x, y + s * 0.45); g.bezierCurveTo(x - s * 0.9, y - s * 0.1, x - s * 0.45, y - s * 0.75, x, y - s * 0.3); g.bezierCurveTo(x + s * 0.45, y - s * 0.75, x + s * 0.9, y - s * 0.1, x, y + s * 0.45); g.fill(); },
  whales(g, x, y, s, c, c2) { g.fillStyle = c; g.beginPath(); g.ellipse(x, y, s * 0.6, s * 0.36, 0, 0, 2 * PI_); g.fill(); g.beginPath(); g.moveTo(x - s * 0.5, y); g.lineTo(x - s * 0.95, y - s * 0.35); g.lineTo(x - s * 0.8, y + s * 0.05); g.lineTo(x - s * 0.95, y + s * 0.3); g.closePath(); g.fill();
    g.fillStyle = c2 || '#ffffff'; g.beginPath(); g.ellipse(x + s * 0.05, y + s * 0.15, s * 0.4, s * 0.14, 0, 0, PI_); g.fill(); g.fillStyle = '#141414'; g.beginPath(); g.arc(x + s * 0.32, y - s * 0.06, s * 0.06, 0, 2 * PI_); g.fill();
    g.strokeStyle = c; g.lineWidth = s * 0.08; g.lineCap = 'round'; g.beginPath(); g.moveTo(x + s * 0.15, y - s * 0.4); g.lineTo(x + s * 0.15, y - s * 0.62); g.moveTo(x + s * 0.15, y - s * 0.55); g.lineTo(x + s * 0.02, y - s * 0.7); g.moveTo(x + s * 0.15, y - s * 0.55); g.lineTo(x + s * 0.28, y - s * 0.7); g.stroke(); },
  rockets(g, x, y, s, c, c2) { g.save(); g.translate(x, y); g.rotate(-0.6); g.fillStyle = c2 || '#e4572e'; g.beginPath(); g.moveTo(-s * 0.18, s * 0.25); g.lineTo(-s * 0.38, s * 0.55); g.lineTo(-s * 0.1, s * 0.45); g.closePath(); g.fill(); g.beginPath(); g.moveTo(s * 0.18, s * 0.25); g.lineTo(s * 0.38, s * 0.55); g.lineTo(s * 0.1, s * 0.45); g.closePath(); g.fill();
    g.fillStyle = c; g.beginPath(); g.ellipse(0, 0, s * 0.2, s * 0.5, 0, 0, 2 * PI_); g.fill(); g.fillStyle = c2 || '#e4572e'; g.beginPath(); g.moveTo(-s * 0.17, -s * 0.28); g.quadraticCurveTo(0, -s * 0.75, s * 0.17, -s * 0.28); g.closePath(); g.fill();
    g.fillStyle = '#9fd0ff'; g.beginPath(); g.arc(0, -s * 0.02, s * 0.08, 0, 2 * PI_); g.fill(); g.fillStyle = '#ffb347'; g.beginPath(); g.moveTo(-s * 0.1, s * 0.5); g.lineTo(0, s * 0.78); g.lineTo(s * 0.1, s * 0.5); g.closePath(); g.fill(); g.restore(); },
};
function printPainter(pr, { handBand = 0, shoeBand = 0, part } = {}) {
  const s = pr.size || 0.15, step = 0.42 / Math.sqrt(pr.density || 1);
  return (g, f, w, h, pn) => {
    if (f === 'py' || f === 'ny') return; const r = makeRng(hash32('print', pn, f, pr.motif)); const limit = h - (pn.startsWith('arm') ? handBand : pn.startsWith('leg') ? shoeBand : 0) - s * 0.6;
    for (let y = s * 0.7 + (f.length % 2) * step * 0.3; y < limit; y += step) for (let x = ((y / step) % 2 ? step / 2 : 0) + s * 0.3; x < w + step; x += step) { const jx = x + (r() - 0.5) * step * 0.35, jy = y + (r() - 0.5) * step * 0.3; if (jy > limit) continue; g.globalAlpha = pr.alpha ?? 0.92; MOTIF[pr.motif](g, jx, jy, s * (0.85 + 0.3 * r()), pr.color || '#ffffff', pr.color2); }
    g.globalAlpha = 1;
  };
}

// ---------------- the builder ----------------
export function castAvatar(spec) {
  const shirt0 = spec.outfit?.shirt, pants0 = spec.outfit?.pants;
  const sleeve = spec.hand === 'sleeve' || shirt0?.hand === 'sleeve';
  const mud = spec.mud || pants0?.mud || null;
  const socks = pants0?.shoes?.style === 'socks' && pants0.shoes.pattern ? pants0.shoes : null;
  const prints = [shirt0?.print ? ['shirt', shirt0.print] : null, pants0?.print ? ['pants', pants0.print] : null].filter(Boolean);
  const extraAcc = (spec.accessories || []).filter((a) => EXTRA_ACC.includes(a.type));
  const extraFace = EXTRA_FACES[spec.face] ? spec.face : null;
  if (!sleeve && !mud && !socks && !prints.length && !extraAcc.length && !extraFace && !spec.pose && !spec.badge) return makeAvatar(spec); // the original path
  const o = { ...spec };
  if (sleeve) { o.outfit = { ...o.outfit, shirt: { ...shirt0, hand: 0 } }; delete o.hand; }
  if (extraAcc.length) o.accessories = spec.accessories.filter((a) => !EXTRA_ACC.includes(a.type));
  if (extraFace) o.face = 'neutral';
  const root = makeAvatar(o); const head = root.getObjectByName('head');
  for (const a of extraAcc) EXTRA[a.type](head, a, root);
  const handBand = sleeve ? 0 : (o.outfit?.shirt?.hand ?? 0.36), shoeBand = o.outfit?.pants?.shoes?.h ?? 0.3;
  for (const [which, pr] of prints) applyOverlay(root, which === 'shirt' ? ['torso', 'armL', 'armR'] : ['legL', 'legR'], keyOf('print', pr, handBand, shoeBand), printPainter(pr, { handBand, shoeBand }));
  if (socks) applyOverlay(root, ['legL', 'legR'], keyOf('socks', socks), sockPainter(socks));
  if (mud) applyOverlay(root, ['legL', 'legR'], keyOf('mud', mud), mudPainter(mud));
  if (extraFace) setFaceEx(root, extraFace);
  if (spec.pose) setPose(root, typeof spec.pose === 'string' ? POSES[spec.pose] : spec.pose);
  if (spec.badge) addBadge6(root, typeof spec.badge === 'object' ? spec.badge : {});
  return root;
}

// ---------------- Theo's "6" birthday badge ----------------
// makeBadge6({ size: 0.45, color, rim, text }) -> Group in STUDS (badge face toward +z); addBadge6(avatar, { at: [x, y] })
// pins it on the chest (hips-local studs; default the character's left chest), real size kept whatever the avatar scale.
export function makeBadge6({ size = 0.45, color = '#f2c230', rim = '#d0242a', text = '6' } = {}) {
  const Mt = cached(keyOf('badgeMats', color, rim, text), () => {
    const N = 256, c = canvas(N), g = c.getContext('2d'), R = N / 2;
    g.fillStyle = rim; g.beginPath(); g.arc(R, R, R, 0, 2 * PI_); g.fill();
    const gr = g.createRadialGradient(R * 0.8, R * 0.75, 4, R, R, R * 0.84); gr.addColorStop(0, shade(color, 1.25)); gr.addColorStop(0.7, color); gr.addColorStop(1, shade(color, 0.85)); g.fillStyle = gr; g.beginPath(); g.arc(R, R, R * 0.82, 0, 2 * PI_); g.fill();
    g.strokeStyle = shade(rim, 0.7); g.lineWidth = 4; g.beginPath(); g.arc(R, R, R * 0.82, 0, 2 * PI_); g.stroke();
    g.fillStyle = '#141414'; g.font = 'bold 170px "DejaVu Sans", Arial, sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(text, R, R + 8);
    for (let k = 0; k < 12; k++) { const a = (k / 12) * 2 * PI_; g.fillStyle = '#ffffff'; g.globalAlpha = 0.85; g.beginPath(); g.arc(R + Math.cos(a) * R * 0.91, R + Math.sin(a) * R * 0.91, 5, 0, 2 * PI_); g.fill(); } g.globalAlpha = 1;
    return { face: new THREE.MeshPhysicalMaterial({ map: canvasTex(c), roughness: 0.3, clearcoat: 1, clearcoatRoughness: 0.05 }), edge: new THREE.MeshStandardMaterial({ color: '#c8c8d0', roughness: 0.3, metalness: 0.9 }) };
  });
  const r = size / 2, G = new THREE.Group(); G.name = 'badge6';
  const cap = cached(keyOf('badgeCap', r), () => { const g = new THREE.SphereGeometry(r * 2.2, 40, 10, 0, 2 * PI_, 0, Math.asin(1 / 2.2)); g.rotateX(PI_ / 2); g.translate(0, 0, -r * 2.2 * Math.cos(Math.asin(1 / 2.2))); const p = g.attributes.position, uv = g.attributes.uv; for (let i = 0; i < p.count; i++) uv.setXY(i, 0.5 + p.getX(i) / (2 * r), 0.5 + p.getY(i) / (2 * r)); g.computeVertexNormals(); return g; });
  const rimG = cached(keyOf('badgeRim', r), () => { const g = new THREE.CylinderGeometry(r, r, 0.03, 40, 1, true); g.rotateX(PI_ / 2); return g; });
  mesh(rimG, Mt.edge, { parent: G, name: 'badgeEdge', pos: [0, 0, 0.015] }); mesh(cap, Mt.face, { parent: G, name: 'badgeFace', pos: [0, 0, 0.03] });
  return G;
}
export function addBadge6(avatar, { at = [0.52, 1.6], size = 0.45, tilt = -8 } = {}) {
  const R = rig(avatar); const b = makeBadge6({ size }); const bs = R.body.scale.x || 1; b.scale.setScalar(1 / bs); b.position.set(at[0], at[1], 0.505); b.rotation.z = tilt * DEG_; R.hips.add(b); return b;
}

// Seated characters: a sit pose expects a seat top at 1.5 studs for a full-size avatar. A shrunk one (grandmaShort,
// heroOldShort, kids) must be lifted so its hips rest on the same seat and its feet dangle: returns that lift in METRES
// (add it to the root's y). seatTop in studs.
// Extra poses for the shrink beats (degrees, like POSES): sitDangle = a smaller body on a full-size seat, lower legs
// hanging off the front edge, hands lost in the sleeves on the lap; sitSunk = slumped back into a deep chair.
export const CAST_POSES = { sitDangle: { legLx: 58, legRx: 66, armLx: 28, armRx: 24, armLz: -4, armRz: -4, neckX: 4 }, sitSunk: { legLx: 70, legRx: 76, bodyX: -10, armLx: 30, armRx: 30, neckX: 8 } };
export function seatOffset(avatar, seatTop = 1.5) { const bs = rig(avatar).body.scale.x || 1; return (seatTop - 1.5 * bs) * 0.32; }

// ---------------- the new cast ----------------
const KID_PJ = (color, pat, extra = {}) => ({ shirt: { style: 'pyjama', color, pattern: pat, piping: extra.piping || '#ffffff', buttons: '#ffffff', hand: 0.2, ...(extra.shirt || {}) }, pants: { style: 'pyjama', color, pattern: pat, piping: extra.piping || '#ffffff', shoes: { style: 'socks', color: extra.socks || '#e9e4f2', h: 0.24 }, ...(extra.pants || {}) } });
Object.assign(CAST, {
  // Jump-cut shrinks (s07 / s96): scale 0.8 / 0.85 (bible exception: the story says so), sleeves swallow the hands.
  grandmaShort: { ...CAST.grandma, scale: 0.8, outfit: sleeveOutfit(OUTFITS.grandmaCardigan) },
  heroOldShort: { ...CAST.heroOld, scale: 0.85, outfit: sleeveOutfit(CAST.heroOld.outfit) },
  // Dawn variants: the hero barefoot with muddy knees and feet; Theo in striped socks; Theo asleep.
  heroMuddy: { ...CAST.heroBarefoot, mud: { knees: 0.8, feet: 0.6 } },
  theoSocks: { ...CAST.theo, outfit: { ...OUTFITS.theoPyjamas, pants: { ...OUTFITS.theoPyjamas.pants, shoes: { style: 'socks', color: '#f4f2ee', pattern: { type: 'stripes', color: '#5a8ad8', period: 0.1 }, h: 0.45 } } } },
  theoAsleep: { ...CAST.theo, face: 'sleeping' },
  theoBadge: { ...CAST.theo, badge: true },
  // World montage: a generic grandkid (orange skin, green tee, red beanie-style cap, sneakers).
  grandkid: { skin: SKIN.orange, outfit: OUTFITS.plainKid, face: 'content', accessories: [{ type: 'hair', style: 'short', color: HAIR.darkBrown }, { type: 'cap', color: '#d0242a', band: '#a81a20' }] },
  // Sepia flashbacks: the hero aged 5 (x0.75, rocket pyjamas), asleep.
  heroKid5: { skin: SKIN.salmon, scale: 0.75, face: 'sleeping', faceOverlays: { freckles: true },
    outfit: KID_PJ('#2c3e7a', { type: 'stars', color: '#f2c84a', density: 5, size: 0.05 }, { piping: '#f2c84a', shirt: { print: { motif: 'rockets', color: '#e8e4f0', color2: '#e4572e', density: 1.1, size: 0.2 } }, pants: { print: { motif: 'rockets', color: '#e8e4f0', color2: '#e4572e', density: 1.0, size: 0.2 } } }),
    accessories: [{ type: 'hair', style: 'messy', color: HAIR.brown }] },
  // 1960s (B&W): Grandpa young (dark hair + moustache, no glasses, no wrinkles, same navy cardigan) and Dad as a boy.
  grandpaYoung: { skin: SKIN.elder, outfit: OUTFITS.grandpaCardigan, faceOverlays: { brows: '#3a2416' }, accessories: [{ type: 'hair', style: 'short', color: HAIR.darkBrown }, { type: 'moustache', color: '#3a2416' }] },
  dadKid: { skin: SKIN.light, scale: 0.75, face: 'sleeping', outfit: KID_PJ('#eef0f4', { type: 'stripes', color: '#6f8fc8', period: 0.2 }, { piping: '#6f8fc8' }), accessories: [{ type: 'hair', style: 'short', color: HAIR.darkBrown }, { type: 'ears', size: 0.35 }] },
  // 1990s (sepia): a little girl with pigtails in a floral nightie.
  cousinKid: { skin: SKIN.peach, scale: 0.75, face: 'sleeping', faceOverlays: { blush: '#ff8f9f' },
    outfit: { shirt: { style: 'tee', color: '#f2c6d6', pattern: { type: 'floral', color: '#d8649a', color2: '#f2cf6a', density: 10, size: 0.06 }, sleeves: 'long', hand: 0.2, trim: '#e7a6c0' }, pants: { style: 'skirt', color: '#f2c6d6', pattern: { type: 'floral', color: '#d8649a', color2: '#f2cf6a', density: 10, size: 0.06 }, skirtLen: 1.62, hem: '#e7a6c0', stockings: SKIN.peach, shoes: { style: 'barefoot' } } },
    accessories: [{ type: 'pigtails', color: '#b0783a', ribbon: '#e05a8a' }] },
  // Epilogue: the narrator's granddaughter (~7, family freckles, dark bob, lilac heart pyjamas) and, in the newest photo,
  // Theo's granddaughter (blond pigtails, blue whale-print pyjamas, waving).
  granddaughter: { skin: SKIN.salmon, scale: 0.85, face: 'sideGlance', faceOverlays: { freckles: true },
    outfit: KID_PJ('#b9a2e0', null, { piping: '#f4eefc', socks: '#f4eefc', shirt: { print: { motif: 'hearts', color: '#f08ab0', density: 2.2, size: 0.12 } }, pants: { print: { motif: 'hearts', color: '#f08ab0', density: 2.2, size: 0.12 } } }),
    accessories: [{ type: 'hair', style: 'bob', color: HAIR.darkBrown }] },
  theoGranddaughter: { skin: SKIN.light, scale: 0.75, face: 'openSmile', pose: 'wave',
    outfit: KID_PJ('#6f9ee0', null, { piping: '#e9f2ff', shirt: { print: { motif: 'whales', color: '#3e5f9a', color2: '#e9f2ff', density: 1.6, size: 0.17 } }, pants: { print: { motif: 'whales', color: '#3e5f9a', color2: '#e9f2ff', density: 1.6, size: 0.17 } } }),
    accessories: [{ type: 'pigtails', color: HAIR.blond, ribbon: '#7fb8f0' }] },
  // The new family's parents (background only): blond mum in a teal cardigan, dad in a rust tee, khakis, glasses.
  theoMom: { skin: SKIN.light, outfit: { shirt: { style: 'cardigan', color: '#2f8a8c', trim: '#24706f', buttons: '#f4ead8', inner: { color: '#f4efe8', collar: false } }, pants: { style: 'jeans', color: '#5a6a96', shoes: { style: 'sneakers', color: '#f2eee8', color2: '#ffffff' } } },
    faceOverlays: { blush: '#ff9a9a' }, accessories: [{ type: 'hair', style: 'bob', color: HAIR.blond }] },
  theoDad: { skin: SKIN.light, outfit: { shirt: { style: 'tee', color: '#b8502e' }, pants: { style: 'trousers', color: '#b6a47c', belt: '#4a3020', shoes: { style: 'shoes', color: '#3a2a22' } } },
    faceOverlays: { stubble: '#8a6a4a' }, accessories: [{ type: 'hair', style: 'short', color: '#a07a44' }, { type: 'glasses', style: 'thick', color: '#1e1a1e' }] },
  // Mom / Dad night variants (move night: dressing gown, pyjamas).
  momNight: { skin: SKIN.peach, outfit: { shirt: { style: 'cardigan', color: '#d88aa8', trim: '#c07090', buttons: '#f4ead8', open: true, inner: { color: '#f4eef6', pattern: { type: 'dots', color: '#b9a2e0', density: 10, size: 0.03 }, collar: false } }, pants: { style: 'pyjama', color: '#f4eef6', pattern: { type: 'dots', color: '#b9a2e0', density: 10, size: 0.03 }, shoes: { style: 'slippers', color: '#e8c0d0', h: 0.24 } } },
    accessories: [{ type: 'hair', style: 'bob', color: HAIR.ginger }] },
  dadNight: { skin: SKIN.light, outfit: { shirt: { style: 'tee', color: '#8a8e98' }, pants: { style: 'pyjama', color: '#3a4a6a', pattern: { type: 'plaid', color: '#1a2030', period: 0.36, alpha: 0.5 }, shoes: { style: 'slippers', color: '#5a3a2a', h: 0.24 } } },
    faceOverlays: { stubble: true }, accessories: [{ type: 'hair', style: 'short', color: HAIR.darkBrown }] },
});

// Theo at any age (photo series s90-s93): scale 0.85 (7-10) -> 1.0 (14+); hair blond -> brown -> grey -> bald with white
// side tufts at 60+; clump beard from 40 (brown-grey, then grey); clothes per decade (tee, hoodie, flannel, sweater,
// cardigan). theoAt(age, extra) -> avatar (extra is merged like makeCharacter's).
export function theoAt(age = 7, extra = {}) {
  const a = age, scale = a <= 10 ? 0.85 : a >= 14 ? 1 : 0.85 + (0.15 * (a - 10)) / 4;
  const hair = a >= 60 ? { type: 'hair', style: 'grandpa', color: HAIR.white } : { type: 'hair', style: a < 14 ? 'short' : 'messy', color: a < 14 ? HAIR.blond : a < 35 ? '#9a6a34' : a < 50 ? '#7a6656' : HAIR.grey };
  const acc = [hair]; if (a >= 40) acc.push({ type: 'beard', color: a < 55 ? '#7a6656' : '#d9d6de', length: a < 55 ? 0.8 : 1.1 });
  const outfit = a < 12 ? { shirt: { style: 'tee', color: a < 9 ? '#5a8ad8' : '#d8573e', print: { motif: 'whales', color: '#e9f2ff', color2: '#3e5f9a', density: 0.5, size: 0.3 } }, pants: { style: 'shorts', color: '#d8c49a', shoes: { style: 'sneakers', color: '#e9e4f2', color2: '#ffffff' } } }
    : a < 20 ? { shirt: { style: 'hoodie', color: '#3a8a5a', trim: '#2e6e48', strings: '#f2ead8' }, pants: { style: 'jeans', color: '#3d4f7a', shoes: { style: 'sneakers', color: '#2a2a32', color2: '#ffffff' } } }
    : a < 33 ? { shirt: { style: 'shirt', color: '#3a5a8a', pattern: { type: 'plaid', color: '#14202e', period: 0.36, alpha: 0.55 }, buttons: '#2a1a1a' }, pants: { style: 'jeans', color: '#3a4060', shoes: { style: 'shoes', color: '#4a3020' } } }
    : a < 55 ? { shirt: { style: 'sweater', color: '#8a5a3a', trim: '#6e462c' }, pants: { style: 'trousers', color: '#5a5a62', belt: '#2a1a10', shoes: { style: 'shoes', color: '#3a2a22' } } }
    : { shirt: { style: 'cardigan', color: '#5a6a8a', trim: '#4a5872', buttons: '#d8c09a', inner: { color: '#efe6d2', buttons: '#ffffff' } }, pants: { style: 'trousers', color: '#6e6a74', belt: '#3a2416', shoes: { style: 'slippers', color: '#3a5a8a', h: 0.26 } } };
  const ov = { ...(a >= 40 ? { wrinkles: true } : {}), ...(a >= 60 ? { brows: '#e4e0e8' } : {}), ...(extra.faceOverlays || {}) };
  return castAvatar({ name: 'theo' + a, skin: SKIN.light, scale, outfit, face: 'grin', accessories: acc, ...extra, faceOverlays: ov });
}
