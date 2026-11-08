// Suburb sets: parametric houses, front lots and a whole street, built in STUDS inside a root scaled by STUD (0.32),
// so everything a shot touches (camera, lights, slots, fog) is in metres. VISUAL_BIBLE §4.1-4.3, §2.7 (scale chart).
//
//   const set = buildStreet(ctx, { seed: 'ep01', hero: { side: 'A', index: 0, closeup: true } });
//   ctx.add(set);                                   // cached per worker; each call returns a cheap clone
//   const { slots, lamps, views } = set.userData;   // slots/lamps in metres (set-root space), views = camera presets
//   kit.place(gnome, slots.find(s => s.name === 'A0.bed0'));  // gnome on the lawn, facing its house
//
// Layout (studs): road along X, centre z = 0, top y = -0.4; kerbs to y = 0; sidewalks 6 wide; side A lots front line at
// z = -zFront (houses face +Z), side B mirrored (houses face -Z). Lot frame: origin at the property line (fence) centre,
// +Z toward the street, house front wall at z = -lawnDepth.
import { THREE, Parts, M, texMat, plaqueTex, prismGeo, boxUV, trs, makeRng, hash32, persistTree, pick, range, shade, STUD } from './kitlib.js';
import * as P_ from './props.js';

const PI = Math.PI;

// ------------------------------------------------------------------ palettes (albedo; the night grade tints them)
export const PALETTE = {
  siding: ['#d9cfb5', '#9fae8c', '#c8a557', '#9a9488', '#e2e0da', '#9a3b32', '#7d8ea3', '#4f63a8'],
  brick: ['#7a3528', '#8a4a36', '#6e3036'],
  roof: ['#35343c', '#3d3330', '#2c3038', '#463734'],
  door: ['#6b1f1a', '#5a2a1a', '#2a4a3a', '#24304a', '#7a2a20'],
  shutter: ['#3b4347', '#2f3a30', '#4a2024', '#1f2a40'],
  curtain: ['#c85a4a', '#d9b25a', '#8a5aa0', '#5a8ac0', '#e0e0d0'],
  tulips: [['#d8283a', '#f07ab0', '#f2c230', '#f4eee8'], ['#f07ab0', '#b04ad0', '#f4eee8'], ['#d8283a', '#f2c230'], ['#f05a8a', '#f7a8d0', '#ffffff']],
  blossom: ['#e070c0', '#f0a0c8', '#b070e0', '#f4f0f0'],
};

// ------------------------------------------------------------------ roof (gable), in a frame where the ridge runs along X
// len along X, span along Z, origin at the wall-top centre. Gable caps use wallKey; slabs use roofKey (shingles).
function addGableRoof(P, { len, span, roofH, thick = 0.55, ohEave = 1.4, ohGable = 1.1, wallKey, roofKey, trimKey, ridge = true }) {
  P.add(wallKey, prismGeo(len, span, roofH, 6));
  const a = Math.atan2(roofH, span / 2); const t0 = -0.35, t1 = (span / 2 + ohEave) / Math.cos(a);
  for (const s of [1, -1]) {
    const dir = new THREE.Vector3(0, -Math.sin(a), s * Math.cos(a)), n = new THREE.Vector3(0, Math.cos(a), s * Math.sin(a));
    const c = new THREE.Vector3(0, roofH, 0).addScaledVector(dir, (t0 + t1) / 2).addScaledVector(n, thick / 2);
    P.box(roofKey, len + 2 * ohGable, thick, t1 - t0, c.toArray(), [s * a, 0, 0]);
    const e = new THREE.Vector3(0, roofH, 0).addScaledVector(dir, t1);
    P.box(trimKey, len + 2 * ohGable, 0.75, 0.28, [0, e.y - 0.1, e.z + s * 0.05]);
    for (const xs of [-1, 1]) { const rc = c.clone().addScaledVector(n, 0.12); P.box(trimKey, 0.3, thick + 0.35, t1 - t0, [xs * (len / 2 + ohGable - 0.12), rc.y, rc.z], [s * a, 0, 0]); }
  }
  if (ridge) P.box(roofKey.replace(/:.*/, '') + ':' + shade(roofKey.split(':')[1] || '#35343c', 0.8), len + 2 * ohGable + 0.1, 0.45, 1.3, [0, roofH + thick * 0.95, 0]);
}

// ------------------------------------------------------------------ window (wall frame: wall surface z = 0, outward +Z)
function addWindow(P, w, H) {
  const { x, y, ww, wh } = w; const tk = 'trim:' + H.trimColor;
  if (w.lit) P.add(`win:${w.tone}:${H.curtain}:${w.variant}:${w.intensity ?? H.winIntensity}`, new THREE.PlaneGeometry(ww, wh), [x, y, 0.05]);
  else P.add('glassDark', new THREE.PlaneGeometry(ww, wh), [x, y, 0.05]);
  P.box(tk, 0.55, wh + 1.0, 0.32, [x - ww / 2 - 0.27, y, 0.16]); P.box(tk, 0.55, wh + 1.0, 0.32, [x + ww / 2 + 0.27, y, 0.16]);
  P.box(tk, ww + 1.6, 0.65, 0.42, [x, y + wh / 2 + 0.32, 0.21]); P.box(tk, ww + 1.3, 0.32, 0.85, [x, y - wh / 2 - 0.16, 0.42]);
  P.box(tk, ww, 0.24, 0.16, [x, y, 0.1]);
  const cols = H.panes === 6 ? 3 : 2; for (let i = 1; i < cols; i++) P.box(tk, 0.14, wh, 0.13, [x - ww / 2 + (ww * i) / cols, y, 0.1]);
  if (H.panes === 6) for (const yy of [y + wh / 4, y - wh / 4]) P.box(tk, ww, 0.12, 0.12, [x, yy, 0.1]);
  if (H.shutterColor && w.face === 'front') for (const s of [-1, 1]) {
    P.add('shutter:' + H.shutterColor, new THREE.PlaneGeometry(1.5, wh + 0.5), [x + s * (ww / 2 + 1.35), y, 0.13]);
    P.box('plastic:' + shade(H.shutterColor, 0.8), 1.5, wh + 0.5, 0.1, [x + s * (ww / 2 + 1.35), y, 0.06]);
  }
  if (w.planter) { P.box('wood:#6a3a22', ww + 0.6, 0.7, 0.8, [x, y - wh / 2 - 0.75, 0.5]); for (let i = 0; i < 7; i++) P.add('tulip:' + w.planter, new THREE.SphereGeometry(0.2, 6, 4), [x - ww / 2 + 0.4 + (ww - 0.8) * i / 6, y - wh / 2 - 0.3, 0.5 + ((i % 2) - 0.5) * 0.3]); }
}

// ------------------------------------------------------------------ house
// Returns info in the house frame (origin = front wall centre at ground, +Z = street): windows, door, lanterns, porch,
// and the separate meshes (lantern glass) that the caller parents to the same frame.
export const HOUSE_DEFAULTS = {
  type: 'bungalow', width: 26, depth: 20, wall: 'siding', wallColor: '#d9cfb5', roofColor: '#35343c', trimColor: '#efeee9',
  doorColor: '#6b1f1a', shutterColor: '#3b4347', roof: 'side', roofH: null, porch: 'center', porchDepth: 6, porchWidth: 12,
  foundation: 1.6, sill: 2.6, storeyH: 10, panes: 4, doorX: 0, lit: 0.6, tone: 'warm', curtain: '#c85a4a', winIntensity: 2.3,
  number: '16', chimney: true, seed: 1, deck: '#a8743a', windowXs: null, pinkWindow: -1, planters: false,
};
export function addHouse(P, o = {}) {
  const H = { ...HOUSE_DEFAULTS, ...o }; const r = makeRng(hash32('house', H.seed));
  const w = H.width, d = H.depth, F = H.foundation, storeys = H.type === 'twoStorey' ? 2 : 1, wallTop = F + storeys * H.storeyH;
  const roofH = H.roofH ?? (H.roof === 'front' ? w * 0.36 : d * (storeys === 2 ? 0.36 : 0.33));
  const wallKey = (H.wall === 'brick' ? 'brick:' : 'siding:') + H.wallColor, roofKey = 'shingle:' + H.roofColor, tk = 'trim:' + H.trimColor;
  // body
  P.box('stone:#8d857b', w + 0.6, F, d + 0.6, [0, F / 2, -d / 2]);
  P.box(wallKey, w, wallTop - F, d, [0, (F + wallTop) / 2, -d / 2]);
  if (H.wall === 'siding') for (const xs of [-1, 1]) for (const zz of [0, -d]) P.box(tk, 0.7, wallTop - F, 0.7, [xs * (w / 2 - 0.25), (F + wallTop) / 2, zz + (zz === 0 ? -0.25 : 0.25)]);
  P.box(tk, w + 0.3, 0.9, 0.3, [0, wallTop - 0.45, 0.05]); P.box(tk, w + 0.3, 0.9, 0.3, [0, wallTop - 0.45, -d - 0.05]);
  // roof
  if (H.roof === 'front') { P.push(trs([0, wallTop, -d / 2], [0, PI / 2, 0])); addGableRoof(P, { len: d, span: w, roofH, wallKey, roofKey, trimKey: tk }); P.pop(); }
  else { P.push(trs([0, wallTop, -d / 2])); addGableRoof(P, { len: w, span: d, roofH, wallKey, roofKey, trimKey: tk }); P.pop(); }
  if (H.chimney) { const cx = w / 2 - 4.2, ch = roofH + 3.5; P.box('brick:#6e3a30', 2.6, ch, 2.6, [cx, wallTop + ch / 2 - 0.5, -d * 0.62]); P.box(tk, 3.1, 0.45, 3.1, [cx, wallTop + ch - 0.3, -d * 0.62]); }
  if (H.roof === 'front' && storeys === 1) { // attic vent window in the front gable (TF)
    P.add('glassDark', new THREE.PlaneGeometry(2.4, 2.4), [0, wallTop + roofH * 0.38, 0.06]); P.box(tk, 3.2, 3.2, 0.25, [0, wallTop + roofH * 0.38, 0.0]);
  }
  // windows
  const wx = H.windowXs ?? [-w * 0.29, w * 0.29]; const wins = []; let vi = 0;
  const addW = (face, x, floor, extra = {}) => {
    const y = F + floor * H.storeyH + H.sill + 2.5; const lit = Array.isArray(H.lit) ? !!H.lit[wins.length] : r() < H.lit;
    const win = { face, x, y, ww: 4, wh: 5, lit, tone: wins.length === H.pinkWindow ? 'pink' : H.tone, variant: vi++ % 3, planter: H.planters && floor === 0 && face === 'front' && r() < 0.5 ? pick(r, PALETTE.blossom) : null, ...extra };
    wins.push(win); return win;
  };
  for (const x of wx) addW('front', x, 0);
  if (storeys === 2) for (const x of [-w * 0.29, 0, w * 0.29]) addW('front', x, 1);
  for (const face of ['left', 'right']) for (let f = 0; f < storeys; f++) addW(face, -d * 0.45, f);
  for (const win of wins) {
    if (win.face === 'front') addWindow(P, win, H);
    else { const s = win.face === 'left' ? -1 : 1; P.push(trs([s * w / 2, 0, 0], [0, s * PI / 2, 0])); addWindow(P, { ...win, x: -win.x * s }, H); P.pop(); }
  }
  // door
  const dx = H.doorX; texMat('plaque:' + H.number, plaqueTex(H.number));
  P.add('door:' + H.doorColor, new THREE.PlaneGeometry(4, 7.5), [dx, F + 3.75, 0.1]); P.box('doorEdge:' + H.doorColor, 4.1, 7.6, 0.2, [dx, F + 3.8, 0.0]);
  P.box(tk, 0.65, 8.3, 0.4, [dx - 2.35, F + 4.15, 0.2]); P.box(tk, 0.65, 8.3, 0.4, [dx + 2.35, F + 4.15, 0.2]); P.box(tk, 6.0, 0.75, 0.5, [dx, F + 8.3, 0.25]);
  P.add('brass', new THREE.SphereGeometry(0.2, 10, 8), [dx + 1.45, F + 3.6, 0.32]); P.box('brass', 0.3, 0.9, 0.08, [dx + 1.45, F + 3.6, 0.15]);
  P.add('plaque:' + H.number, new THREE.PlaneGeometry(1.2, 0.9), [dx + 3.6, F + 6.2, 0.12]); P.box('black:#1d3a2c', 1.3, 1.0, 0.1, [dx + 3.6, F + 6.2, 0.05]);
  P.box('plastic:#5a3a2a', 3.2, 0.06, 1.5, [dx, F + 0.03, 1.2]);
  // porch
  const pd = H.porch === 'none' ? 0 : H.porchDepth; const extras = []; const lanterns = []; let px0 = dx - H.porchWidth / 2, px1 = dx + H.porchWidth / 2;
  if (H.porch === 'full') { px0 = -w / 2 - 0.3; px1 = w / 2 + 0.3; }
  const stepW = 5, nSteps = Math.max(2, Math.ceil(F / 0.7)), rise = F / nSteps;
  if (H.porch !== 'none') {
    const pw = px1 - px0, pcx = (px0 + px1) / 2;
    const porchTop = Math.min(F + 9.6, wallTop - 0.3), beamY = porchTop - 1.7;
    P.box('porch:' + H.deck, pw, 0.5, pd, [pcx, F - 0.25, pd / 2]); P.box('stone:#8d857b', pw - 0.2, F - 0.5, pd - 0.3, [pcx, (F - 0.5) / 2, pd / 2 - 0.1]);
    P.box(tk, pw + 0.1, 0.35, 0.3, [pcx, F - 0.2, pd + 0.05]);
    const nCol = H.porch === 'full' ? Math.max(2, Math.round(pw / 7) + 1) : 2; const colXs = [];
    for (let i = 0; i < nCol; i++) colXs.push(px0 + 0.6 + ((pw - 1.2) * i) / (nCol - 1));
    for (const x of colXs) { P.box(tk, 1.25, 0.6, 1.25, [x, F + 0.3, pd - 0.65]); P.box(tk, 0.85, beamY - F - 1.1, 0.85, [x, (F + 0.6 + beamY - 0.5) / 2, pd - 0.65]); P.box(tk, 1.25, 0.5, 1.25, [x, beamY - 0.25, pd - 0.65]); }
    P.box(tk, pw, 1.0, 1.0, [pcx, beamY + 0.5, pd - 0.65]);
    for (const x of [px0 + 0.6, px1 - 0.6]) P.box(tk, 0.9, 1.0, pd, [x, beamY + 0.5, pd / 2]);
    P.box(tk, pw, 0.2, pd, [pcx, beamY + 1.0, pd / 2]); // ceiling
    if (H.porch === 'full') { // shed roof from the wall to the beam
      const L = Math.hypot(pd + 1.0, porchTop - (beamY + 1.0)), b = Math.atan2(porchTop - (beamY + 1.0), pd + 1.0);
      P.box(roofKey, pw + 1.2, 0.45, L, [pcx, (porchTop + beamY + 1.0) / 2 + 0.3, (pd + 1.0) / 2], [b, 0, 0]);
      P.box(tk, pw + 1.2, 0.6, 0.25, [pcx, beamY + 1.15, pd + 1.0]);
    } else { // small front gable over the centre porch
      P.push(trs([pcx, beamY + 1.0, pd / 2 + 0.2], [0, PI / 2, 0])); addGableRoof(P, { len: pd + 0.4, span: pw, roofH: pw * 0.3, ohEave: 0.8, ohGable: 0.6, wallKey: tk, roofKey, trimKey: tk, ridge: false }); P.pop();
    }
    // railings (front, both sides of the step opening; sides of the porch)
    const rail = (xa, za, xb, zb) => {
      const L = Math.hypot(xb - xa, zb - za); if (L < 0.6) return; const ang = Math.atan2(xb - xa, zb - za);
      P.push(trs([xa, F, za], [0, ang, 0]));
      P.box(tk, 0.32, 0.3, L, [0, 3.1, L / 2]); P.box(tk, 0.28, 0.25, L, [0, 0.45, L / 2]);
      const n = Math.floor(L / 0.62); for (let i = 1; i < n; i++) P.box(tk, 0.2, 2.5, 0.2, [0, 1.8, (L * i) / n]);
      P.pop();
    };
    const zr = pd - 0.65; const sx0 = dx - stepW / 2 - 0.3, sx1 = dx + stepW / 2 + 0.3;
    const cols = colXs.slice().sort((a, b) => a - b);
    for (let i = 0; i < cols.length - 1; i++) { let a = cols[i] + 0.45, b = cols[i + 1] - 0.45; if (b < sx0 || a > sx1) rail(a, zr, b, zr); else { if (sx0 - a > 0.6) rail(a, zr, sx0, zr); if (b - sx1 > 0.6) rail(sx1, zr, b, zr); } }
    for (const x of [px0 + 0.6, px1 - 0.6]) rail(x, 0.4, x, zr - 0.45);
    // wall lanterns beside the door, potted plants by the steps, rocking chair on full porches
    for (const s of H.porch === 'full' ? [-1, 1] : [-1]) { P.push(trs([dx + s * 3.3, F + 5.6, 0])); const L = P_.addWallLantern(P); P.pop(); extras.push(L.glass); lanterns.push(L.lightPos); }
    for (const s of [-1, 1]) { P.push(trs([dx + s * (stepW / 2 + 1.1), F, pd - 1.4])); P_.addPotPlant(P, { seed: H.seed * 3 + s, blossom: r() < 0.5 ? pick(r, PALETTE.blossom) : null }); P.pop(); }
    if (H.porch === 'full') { P.push(trs([px0 + 3.8, F, pd * 0.5], [0, 0.35, 0])); P_.addRockingChair(P); P.pop(); }
  } else { // door hood + stoop (TF brick house)
    P.push(trs([dx, F + 8.7, 0.9], [0, PI / 2, 0])); addGableRoof(P, { len: 2.2, span: 6.2, roofH: 1.8, ohEave: 0.3, ohGable: 0.1, wallKey: tk, roofKey, trimKey: tk, ridge: false }); P.pop();
    for (const s of [-1, 1]) P.box(tk, 0.35, 1.2, 1.6, [dx + s * 2.9, F + 8.1, 0.8]);
    P.push(trs([dx + 3.3, F + 5.6, 0])); const L = P_.addWallLantern(P); P.pop(); extras.push(L.glass); lanterns.push(L.lightPos);
  }
  // steps (wood on porches, concrete stoop otherwise)
  const sk = H.porch === 'none' ? 'concrete' : 'porch:' + H.deck;
  for (let j = 1; j < nSteps; j++) { const top = F - j * rise; P.box(sk, stepW, top, 1.15, [dx, top / 2, pd + 1.15 * (j - 1) + 0.575]); }
  if (H.porch !== 'none') for (const s of [-1, 1]) P.box(tk, 0.3, F, (nSteps - 1) * 1.15 + 0.2, [dx + s * (stepW / 2 + 0.15), F / 2 - 0.1, pd + ((nSteps - 1) * 1.15) / 2]);
  const stepsEnd = pd + (nSteps - 1) * 1.15;
  return { H, F, wallTop, ridge: wallTop + roofH, windows: wins, door: [dx, F, 0.3], lanterns, extras, porch: { depth: pd, x0: px0, x1: px1, deckY: F, stepsEnd, stepX: dx, stepW } };
}

// ------------------------------------------------------------------ lot (front garden)
// Lot frame: origin at the property line centre (fence), +Z = street; house front at z = -lawnDepth.
// detail: 'hero' (grass blades + daisies around the hero bed, dense tulips), 'full', 'low' (no tulips, fewer props).
export const LOT_DEFAULTS = { lotW: 36, lawnDepth: 22, detail: 'full', fence: true, path: 'stones', beds: 'windows', mailbox: true, extras: [], seed: 1, gnomes: 2, backTrees: 1 };
export function addLot(P, o = {}, house = {}) {
  const L = { ...LOT_DEFAULTS, ...o }; const r = makeRng(hash32('lot', L.seed)); const out = { slots: [], extras: [], lanterns: [], windows: [] };
  const hz = -L.lawnDepth; const hx = house.offsetX ?? 0;
  // house
  P.push(trs([hx, 0, hz])); const info = addHouse(P, house); P.pop();
  const toLot = (p) => [p[0] + hx, p[1], p[2] + hz];
  info.extras.forEach((m) => out.extras.push(m)); // already in the lot frame (built with P's transform stack)
  out.lanterns = info.lanterns; out.house = info;
  out.windows = info.windows.map((w) => ({ face: w.face, lit: w.lit, tone: w.tone, pos: w.face === 'front' ? toLot([w.x, w.y, 0.1]) : toLot([(w.face === 'left' ? -1 : 1) * (info.H.width / 2 + 0.1), w.y, w.x]) }));
  const doorX = hx + info.porch.stepX, stepsZ = hz + info.porch.stepsEnd;
  // fence + gate (aligned with the path)
  const gateX = doorX; let gate = null;
  if (L.fence) { P.push(trs([0, 0, -0.4])); gate = P_.addPicketFence(P, { length: L.lotW - 0.2, gate: { at: gateX, width: 4 } }).gate; P.pop(); if (gate) out.extras.push(gate); }
  // path: stepping stones (or a concrete walk) from the gate to the steps
  if (L.path === 'stones') P_.addSteppingStones(P, [[gateX, -0.8], [gateX + (r() - 0.5) * 3, (stepsZ - 0.8) / 2], [doorX, stepsZ + 0.5]], { seed: L.seed });
  else if (L.path === 'walk') P.box('concrete', 3.6, 0.08, -stepsZ - 0.4, [gateX, 0.04, stepsZ / 2 - 0.2]);
  // flowerbeds under the front ground-floor windows that are not behind a porch
  const beds = [];
  if (L.beds) for (const w of info.windows.filter((w) => w.face === 'front' && w.y < info.F + 10)) {
    const x = hx + w.x; if (info.porch.depth > 0 && x > hx + info.porch.x0 - 1 && x < hx + info.porch.x1 + 1) continue;
    const len = 9, dep = 3.2, bz = hz + info.porch.depth * 0 + 0.6 + dep / 2;
    P.push(trs([x, 0, bz]));
    if (L.detail === 'low') { P.box('dirt', len, 0.3, dep, [0, 0.15, 0]); P_.addBush(P, { radius: 1.4, seed: L.seed * 5 + beds.length, blossom: pick(r, PALETTE.blossom), blossoms: 10 }); }
    else P_.addFlowerbed(P, { length: len, depth: dep, colors: pick(r, PALETTE.tulips), density: L.detail === 'hero' ? 3.2 : 2.0, seed: L.seed * 11 + beds.length, bushes: L.detail === 'hero' ? 0 : 1, blossom: pick(r, PALETTE.blossom), gaps: [[beds.length ? 0.8 : -0.8, -0.2, 1.15]] });
    P.pop(); beds.push({ x, z: bz, len, dep, window: w });
  }
  // bushes by the house corners / steps, side-yard tree
  for (const s of [-1, 1]) { P.push(trs([hx + s * (info.H.width / 2 - 1.5), 0, hz + 1.6])); P_.addBush(P, { radius: 1.6 + r() * 0.5, seed: L.seed * 7 + s, blossom: r() < 0.5 ? pick(r, PALETTE.blossom) : null }); P.pop(); }
  // mailbox at the kerb side of the sidewalk, next to the gate
  if (L.mailbox) { P.push(trs([gateX + 3.2, 0, 5.2], [0, 0, 0])); P_.addMailbox(P); P.pop(); }
  // extras
  for (const e of L.extras) {
    if (e === 'hoseReel') { P.push(trs([hx + info.H.width / 2 + 2.2, 0, hz - 3], [0, -PI / 2, 0])); P_.addHoseReel(P); P.pop(); }
    else if (e === 'kennel') { P.push(trs([hx - L.lotW * 0.3, 0, hz * 0.45], [0, 0.4, 0])); P_.addKennel(P); P.pop(); }
    else if (e === 'trashBin') { P.push(trs([hx + info.H.width / 2 + 2.5, 0, hz + 2])); P_.addTrashBin(P); P.pop(); }
    else if (e === 'hydrant') { P.push(trs([gateX - 6, 0, 5.0])); P_.addHydrant(P); P.pop(); }
    else if (e === 'leafyTree') { P.push(trs([hx - L.lotW * 0.36, 0, hz * 0.55])); P_.addLeafyTree(P, { height: 20 + r() * 6, seed: L.seed }); P.pop(); }
    else if (e === 'pineFront') { P.push(trs([hx - L.lotW * 0.38, 0, hz * 0.6])); P_.addPine(P, { height: 20 + r() * 6, seed: L.seed }); P.pop(); }
    else if (e && e.board) { P.push(trs([gateX - 6.5, 0, -2.2])); out.extras.push(P_.addAgentBoard(P, e.board)); P.pop(); }
    else if (e && e.sign) { P.push(trs([gateX + 7, 0, -2.0])); out.extras.push(P_.addPostSign(P, e.sign)); P.pop(); }
  }
  // back-yard pines (dark silhouettes against the sky)
  for (let i = 0; i < L.backTrees; i++) { P.push(trs([hx + (r() - 0.5) * L.lotW * 0.8, 0, hz - info.H.depth - 6 - r() * 10])); P_.addPine(P, { height: 24 + r() * 8, seed: L.seed * 13 + i }); P.pop(); }
  // hero close-up detail: blades and daisies are added by the street builder (instanced); record the area
  // ---- slots (lot frame, studs; yaw: 0 = facing +Z/street, PI = facing the house)
  const S = (name, kind, x, y, z, yaw, extra = {}) => out.slots.push({ name, kind, local: [x, y, z], yaw, ...extra });
  beds.forEach((b, i) => S('bed' + i, 'gnome', b.x + (i ? 0.8 : -0.8), 0.35, b.z - 0.2, PI, { onBed: true, window: i }));
  beds.forEach((b, i) => S('bedFront' + i, 'gnome', b.x, 0, b.z + b.dep / 2 + 1.3, PI, { window: i }));
  const lawnSpots = [[-L.lotW * 0.27, hz * 0.45], [L.lotW * 0.24, hz * 0.55], [gateX - 3.2, -3.2], [L.lotW * 0.3, -4.5]];
  lawnSpots.forEach(([x, z], i) => S('lawn' + i, 'gnome', x, 0, z, PI + (r() - 0.5) * 0.08));
  S('porchDoor', 'char', doorX, info.F, hz + 2.4, 0); S('porchSteps', 'char', doorX, 0, stepsZ + 1.2, 0);
  S('porchSide', 'char', hx + (info.porch.x0 + info.porch.x1) / 2 + (info.porch.x1 - info.porch.x0) * 0.3, info.F, hz + info.porch.depth * 0.55, 0.3);
  S('lawnMid', 'char', doorX + 5, 0, hz * 0.5, 0); S('gateIn', 'char', gateX, 0, -2.0, PI); S('gateOut', 'char', gateX, 0, 2.5, PI);
  S('windowLook', 'char', beds[0] ? beds[0].x : doorX - 7, 0, (beds[0] ? beds[0].z + beds[0].dep / 2 : hz) + 2.6, PI);
  out.beds = beds; out.gateX = gateX; out.doorX = doorX; out.stepsZ = stepsZ; out.F = info.F; out.ridge = info.ridge;
  return out;
}

// ------------------------------------------------------------------ street
export const STREET_DEFAULTS = {
  seed: 'street', lotsPerSide: 6, lotW: 36, lawnDepth: 22, roadW: 26, sidewalkW: 6, sideB: true, extend: 160,
  lampSpacing: 36, lampHeight: 13.5, treeStyle: 'pine', forest: true, detailRadius: 2,
  hero: { side: 'A', index: 0, closeup: false, house: {}, lot: {} },
  houses: {},      // per-lot overrides: { 'A0': { house: {...}, lot: {...} } }
};
function lotStyle(r, side, i, seed) {
  const brick = r() < 0.3, twoStorey = r() < 0.45;
  return {
    house: {
      type: twoStorey ? 'twoStorey' : 'bungalow', wall: brick ? 'brick' : 'siding', wallColor: brick ? pick(r, PALETTE.brick) : pick(r, PALETTE.siding),
      roofColor: pick(r, PALETTE.roof), doorColor: pick(r, PALETTE.door), shutterColor: r() < 0.75 ? pick(r, PALETTE.shutter) : null,
      roof: !twoStorey && r() < 0.35 ? 'front' : 'side', porch: twoStorey ? (r() < 0.7 ? 'full' : 'center') : (brick && r() < 0.5 ? 'none' : 'center'),
      panes: r() < 0.5 ? 6 : 4, curtain: pick(r, PALETTE.curtain), number: String(2 + 2 * i + (side === 'B' ? 1 : 0) + 10), chimney: r() < 0.6,
      width: twoStorey ? 26 + Math.round(r() * 2) : 24 + Math.round(r() * 3), depth: 20, lit: 0.55, pinkWindow: r() < 0.15 ? 0 : -1, planters: r() < 0.3,
      seed: hash32(seed, side, i) % 10007, offsetX: Math.round((r() - 0.5) * 3),
    },
    lot: { extras: [r() < 0.3 ? 'hoseReel' : null, r() < 0.25 ? 'trashBin' : null, r() < 0.2 ? 'leafyTree' : null].filter(Boolean), path: r() < 0.65 ? 'stones' : 'walk', backTrees: 1 + (r() < 0.5 ? 1 : 0) },
  };
}
// Build (or fetch from the per-worker cache) a whole street. Returns a clone: Group scaled by STUD.
export function buildStreet(ctx, opts = {}) {
  const o = { ...STREET_DEFAULTS, ...opts, hero: { ...STREET_DEFAULTS.hero, ...(opts.hero || {}) } };
  const key = 'kit:street:' + JSON.stringify(o);
  return ctx.instance(key, () => streetFactory(o));
}
function streetFactory(o) {
  const root = new THREE.Group(); root.name = 'suburbStreet'; root.scale.setScalar(STUD);
  const r = makeRng(hash32('street', o.seed));
  const zFront = o.roadW / 2 + 0.6 + o.sidewalkW; const n = o.lotsPerSide; const xLot = (i) => (i - (n - 1) / 2) * o.lotW;
  const L = n * o.lotW + 2 * o.extend; const meta = { slots: [], lamps: [], lots: [], windows: [], lanterns: [], views: {}, stud: STUD, zFront, roadW: o.roadW };
  // ---- ground: road, kerbs, sidewalks, lawns (one merged batch)
  const G = new Parts();
  G.box('asphalt', L, 0.6, o.roadW + 1.2, [0, -0.7, 0]);
  for (const s of [-1, 1]) {
    G.box('kerb', L, 0.55, 0.6, [0, -0.275, s * (o.roadW / 2 + 0.3)]);
    G.box('concrete', L, 0.4, o.sidewalkW, [0, -0.2, s * (o.roadW / 2 + 0.6 + o.sidewalkW / 2)]);
    const gd = o.lawnDepth + 70; G.box('lawn', L, 0.5, gd, [0, -0.25, s * (zFront + gd / 2)]);
  }
  for (let x = -L / 2 + 4; x < L / 2; x += 8) G.box('line:#e8b422', 3, 0.04, 0.32, [x, -0.38, 0]);
  for (const s of [-1, 1]) for (let x = -L / 2 + 6; x < L / 2; x += 12) G.box('asphalt:#3a3a42', 0.15, 0.03, 0.6, [x, -0.385, s * (o.roadW / 2 - 0.4)]); // gutter seams
  root.add(persistTree(G.build(M, { name: 'ground' })));
  // ---- lots
  const sides = o.sideB ? ['A', 'B'] : ['A'];
  for (const side of sides) for (let i = 0; i < n; i++) {
    const id = side + i; const st = lotStyle(r, side, i, o.seed); const isHero = o.hero && o.hero.side === side && o.hero.index === i;
    const dist = o.hero && o.hero.side === side ? Math.abs(i - o.hero.index) : 99;
    const detail = isHero ? (o.hero.closeup ? 'hero' : 'full') : dist <= o.detailRadius || (side !== o.hero?.side && Math.abs(i - (o.hero?.index ?? 0)) <= 1) ? 'full' : 'low';
    const ov = o.houses[id] || {}; const heroOv = isHero ? o.hero : {};
    const house = { ...st.house, ...(ov.house || {}), ...(heroOv.house || {}) }; const lot = { ...st.lot, ...(ov.lot || {}), ...(heroOv.lot || {}), detail, seed: hash32(o.seed, id) % 10007, lotW: o.lotW, lawnDepth: o.lawnDepth };
    const P = new Parts(); const info = addLot(P, lot, house);
    const g = persistTree(P.build(M, { name: 'lot_' + id })); info.extras.forEach((e) => { persistTree(e); g.add(e); });
    g.children.forEach((c) => { if (c.name === 'gate') c.name = 'gate_' + id; if (c.name === 'lanternGlass') c.name = 'lantern_' + id; });
    const yaw = side === 'A' ? 0 : PI, ox = xLot(i), oz = side === 'A' ? -zFront : zFront; g.position.set(ox, 0, oz); g.rotation.y = yaw; root.add(g);
    const toW = (p) => { const c = Math.cos(yaw), s = Math.sin(yaw); return [(ox + p[0] * c + p[2] * s) * STUD, p[1] * STUD, (oz - p[0] * s + p[2] * c) * STUD]; };
    for (const s of info.slots) meta.slots.push({ name: id + '.' + s.name, kind: s.kind, lot: id, pos: toW(s.local).map((v) => +v.toFixed(4)), yaw: +(yaw + s.yaw).toFixed(4), onBed: !!s.onBed });
    meta.lanterns.push(...info.lanterns.map((p) => ({ lot: id, pos: toW(p) })));
    meta.windows.push(...info.windows.map((w) => ({ lot: id, face: w.face, lit: w.lit, tone: w.tone, pos: toW(w.pos) })));
    meta.lots.push({ id, side, index: i, origin: toW([0, 0, 0]), yaw, houseFront: toW([0, 0, -o.lawnDepth]), door: toW([info.doorX, info.F, -o.lawnDepth + 0.3]), steps: toW([info.doorX, 0, info.stepsZ]), gate: toW([info.gateX, 0, -0.4]), deckY: info.F * STUD, ridge: info.ridge * STUD, beds: info.beds.map((b) => ({ pos: toW([b.x, 0.35, b.z]), len: b.len * STUD, dep: b.dep * STUD })), hero: isHero });
    // hero close-up detail: instanced grass blades + daisies around the first bed and the path
    if (isHero && o.hero.closeup) {
      const b = info.beds[0] || { x: info.doorX - 8, z: -o.lawnDepth + 2.2, len: 9, dep: 3.2 };
      const cx = b.x + 2, cz = b.z + 6.5;
      const blades = P_.grassBlades({ area: [26, 16], count: 9000, seed: hash32(o.seed, 'blades') % 997 });
      const bl = new THREE.Group(); bl.add(blades); bl.position.set(cx, 0, cz); bl.name = 'heroBlades';
      // keep blades off the flowerbeds, the path and the house
      cullBlades(blades, (x, z) => { const wx = x + cx, wz = z + cz; return info.beds.some((bb) => Math.abs(wx - bb.x) < bb.len / 2 + 0.5 && Math.abs(wz - bb.z) < bb.dep / 2 + 0.5) || (Math.abs(wx - info.gateX) < 1.6 && wz > info.stepsZ) || wz < -o.lawnDepth + 0.3; });
      g.add(bl);
      const D = new Parts(); const dr = makeRng(hash32(o.seed, 'daisy'));
      for (let k = 0; k < 70; k++) { const x = cx + (dr() - 0.5) * 26, z = cz + (dr() - 0.5) * 16; if (info.beds.some((bb) => Math.abs(x - bb.x) < bb.len / 2 + 0.6 && Math.abs(z - bb.z) < bb.dep / 2 + 0.6) || z < -o.lawnDepth + 0.5 || Math.abs(x - info.gateX) < 2) continue; P_.addDaisy(D, x, z, { r: dr, color: dr() < 0.8 ? '#f4f0ea' : '#f2c230' }); }
      g.add(persistTree(D.build(M, { name: 'heroDaisies' })));
    }
  }
  // ---- street lamps (black Victorian), staggered on both sides; glass + halo + pool kept per lamp for light cascades
  let li = 0;
  for (const side of ['A', 'B']) {
    const z = (side === 'A' ? -1 : 1) * (o.roadW / 2 + 1.6); const off = side === 'A' ? o.lotW / 2 - 4 : o.lampSpacing / 2 + o.lotW / 2 - 4;
    for (let x = -L / 2 + 20 + (off % o.lampSpacing); x < L / 2 - 20; x += o.lampSpacing) {
      const LP = new Parts(); const res = P_.addStreetLamp(LP, { height: o.lampHeight }); const lg = persistTree(LP.build(M, { name: 'lamp_' + li }));
      res.glass.forEach((m) => lg.add(persistTree(m)));
      lg.position.set(x, 0, z); lg.rotation.y = side === 'A' ? 0 : PI; root.add(lg);
      const head = [x * STUD, (res.lightPos[1]) * STUD, z * STUD];
      meta.lamps.push({ name: 'lamp_' + li, side, pos: [x * STUD, 0, z * STUD], head: head.map((v) => +v.toFixed(4)) }); li++;
    }
  }
  // ---- forest backdrop (pines behind the back yards), merged
  if (o.forest) {
    const F = new Parts(); const fr = makeRng(hash32(o.seed, 'forest'));
    for (const s of o.sideB ? [-1, 1] : [-1]) for (let x = -L / 2; x < L / 2; x += 9 + fr() * 6) { F.push(trs([x, 0, s * (zFront + o.lawnDepth + 48 + fr() * 30)])); P_.addPine(F, { height: 26 + fr() * 12, seed: Math.floor(fr() * 1e6), tiers: 5 }); F.pop(); }
    root.add(persistTree(F.build(M, { name: 'forest' })));
  }
  // ---- views (camera presets, metres), around the hero lot
  const hero = meta.lots.find((l) => l.hero) || meta.lots[0]; meta.views = heroViews(hero, meta, o);
  root.userData = JSON.parse(JSON.stringify(meta));
  return root;
}
// Remove blade instances where reject(x, z) (blade-local coords) is true.
function cullBlades(im, reject) {
  const m = new THREE.Matrix4(), p = new THREE.Vector3(), c = new THREE.Color(); let k = 0;
  for (let i = 0; i < im.count; i++) { im.getMatrixAt(i, m); p.setFromMatrixPosition(m); if (reject(p.x, p.z)) continue; if (k !== i) { im.setMatrixAt(k, m); if (im.instanceColor) { im.getColorAt(i, c); im.setColorAt(k, c); } } k++; }
  im.count = k; im.instanceMatrix.needsUpdate = true; if (im.instanceColor) im.instanceColor.needsUpdate = true; im.computeBoundingSphere();
}
// Camera presets for the hero lot (metres). fov is vertical (70 = Roblox default).
function heroViews(h, meta, o) {
  const S = STUD, dirZ = h.yaw === 0 ? 1 : -1; // +1: street is toward +Z from the lot
  const [ox, , oz] = h.origin, [dx, dy, dz] = h.door, bed = h.beds[0];
  const v = (pos, target, fov) => ({ pos: pos.map((x) => +x.toFixed(3)), target: target.map((x) => +x.toFixed(3)), fov });
  const views = {
    // high wide along the street, gnomes on the lawns in the foreground (PN #2 / TF #93 feel)
    streetWide: v([ox + 26 * S, 26 * S, oz + dirZ * 30 * S], [ox - 40 * S, 3 * S, oz - dirZ * 22 * S], 60),
    // eye-level wide of the hero lawn from the sidewalk
    lawn: v([ox + 4 * S, 6.5 * S, oz + dirZ * 7 * S], [dx - 2 * S, 7 * S, dz + dirZ * 3 * S], 70),
    // on the porch, toward the door (character slot porchDoor)
    porch: v([dx + 7.5 * S, h.deckY + 5.2 * S, dz + dirZ * 7.5 * S], [dx - 1 * S, h.deckY + 4.2 * S, dz], 70),
    // from the porch out to the street: gnomes facing the camera, fence, lamps, houses across
    porchOut: v([dx - 2 * S, h.deckY + 4.8 * S, dz + dirZ * 1.5 * S], [dx + 4 * S, 3 * S, oz + dirZ * 10 * S], 70),
  };
  if (bed) {
    const [bx, by, bz] = bed.pos;
    // lawn close-up at gnome eye level (1.4 studs) behind the grandpa slot: bed, wall, lit window above
    views.gnomeCU = v([bx + 3.5 * S, 2.2 * S, bz + dirZ * 7.5 * S], [bx - 0.6 * S, 2.6 * S, bz - dirZ * 0.2 * S], 60);
    // reverse: the gnome's face, the lawn, fence and street behind
    views.gnomeFace = v([bx - 0.8 * S, 2.0 * S, bz - dirZ * 1.0 * S], [bx - 0.6 * S, 1.5 * S, bz + dirZ * 3 * S], 70);
  }
  return views;
}

// ------------------------------------------------------------------ convenience sets
// A single lawn (hero lot + its neighbours + the street and the houses across): cheaper than a full street.
export function buildLot(ctx, o = {}) { return buildStreet(ctx, { lotsPerSide: 3, extend: 120, ...o, hero: { side: 'A', index: 1, ...(o.hero || {}) } }); }
// Lawn close-up set: the hero lot with grass blades, daisies, dense tulips, stepping stones, porch steps and a lit
// bedroom window over the grandpa bed; the rest of the street is there for reverse angles.
export function buildLawnCloseup(ctx, o = {}) {
  return buildStreet(ctx, { lotsPerSide: 3, extend: 120, ...o, hero: { side: 'A', index: 1, closeup: true, house: { lit: [1, 1, 0, 1], foundation: 1.0, sill: 1.6, porch: 'center', ...(o.hero?.house || {}) }, ...(o.hero || {}) } });
}

// ------------------------------------------------------------------ helpers for shots
// Put an object on a slot (slots are in set-root metres; pass the set if it was moved/rotated).
export function place(obj, slot, set = null) {
  const p = new THREE.Vector3(...slot.pos); let yaw = slot.yaw;
  if (set) { set.updateMatrixWorld(true); const s = set.scale.x; p.divideScalar(s).applyMatrix4(set.matrixWorld); yaw += set.rotation.y; }
  obj.position.copy(p); obj.rotation.y = yaw; return obj;
}
export const slotsOf = (set, filter = {}) => set.userData.slots.filter((s) => (!filter.kind || s.kind === filter.kind) && (!filter.lot || s.lot === filter.lot) && (!filter.name || s.name.includes(filter.name)));
export const slot = (set, name) => set.userData.slots.find((s) => s.name === name);
export const lot = (set, id) => set.userData.lots.find((l) => l.id === id);
