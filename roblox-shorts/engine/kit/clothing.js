// 2D painted clothing (VISUAL_BIBLE §2.2-2.3): a shirt texture wrapped on the torso + both arms, a pants texture on both
// legs, painted in the Roblox-shirt manner (flat base, pattern, details, then baked shading: collar shadow, armpit
// darkening, soft diagonal folds, a darker hem gradient, a lighter cuff band). One canvas atlas per box part.
//
// Atlas layout of a box w x h x d (studs), PPU px per stud:  [ -x | front +z | +x | back -z ]  (height h)
//                                                             [    | top +y   |    | bottom -y ]  (height d)
// The strip order keeps the vertical edges continuous, so patterns wrap around the box. `atlasUV(geo, w, h, d)`
// assigns matching UVs to a RoundedBoxGeometry (each of its 6 sides is a contiguous block of triangles).
//
//   const tex = outfitTextures({ shirt: {...}, pants: {...}, skin })  -> { torso, armL, armR, legL, legR } (materials)
import { THREE, cached, canvas, canvasTex, keyOf, makeRng, hash32, rgba, shade, mix, grainCanvas, clamp } from './util.js';

export const PPU = 176; // px per stud (bible: >= 128; close-ups at 1080p want more)
export const SKIN = { salmon: '#e8a07a', orange: '#f49134', coral: '#e96e57', light: '#ebc284', pale: '#e8e8e8', peach: '#f0b48e', tan: '#c98a5a', brown: '#8d5a3b', deep: '#5e3a28', elder: '#eab48f' };
export const HAIR = { brown: '#5a3418', darkBrown: '#3a2416', blond: '#e8c24a', ginger: '#d8642a', black: '#1e1a1e', grey: '#bdb8c2', silver: '#d9d6de', white: '#eeeaf0' };

// Part boxes (studs) and the world y of their top edge when the rig is at rest (for pattern alignment).
export const PARTS = { torso: { w: 2, h: 2, d: 1, top: 4 }, armL: { w: 1, h: 2, d: 1, top: 4 }, armR: { w: 1, h: 2, d: 1, top: 4 }, legL: { w: 1, h: 2, d: 1, top: 2 }, legR: { w: 1, h: 2, d: 1, top: 2 } };

export function faceRects(w, h, d) {
  return { nx: [0, 0, d, h], pz: [d, 0, w, h], px: [d + w, 0, d, h], nz: [2 * d + w, 0, w, h], py: [d, h, w, d], ny: [2 * d + w, h, w, d] };
}
export function atlasUV(geo, w, h, d) {
  const p = geo.attributes.position, uv = geo.attributes.uv, n = p.count, per = n / 6, AW = 2 * w + 2 * d, AH = h + d;
  const sides = ['px', 'nx', 'py', 'ny', 'pz', 'nz'];
  for (let i = 0; i < n; i++) {
    const s = sides[Math.min(5, Math.floor(i / per))], x = clamp(p.getX(i), -w / 2, w / 2), y = clamp(p.getY(i), -h / 2, h / 2), z = clamp(p.getZ(i), -d / 2, d / 2);
    let hx, vy;
    if (s === 'px') { hx = d + w + (d / 2 - z); vy = h / 2 - y; }
    else if (s === 'nx') { hx = z + d / 2; vy = h / 2 - y; }
    else if (s === 'pz') { hx = d + (x + w / 2); vy = h / 2 - y; }
    else if (s === 'nz') { hx = 2 * d + w + (w / 2 - x); vy = h / 2 - y; }
    else if (s === 'py') { hx = d + (x + w / 2); vy = h + (z + d / 2); }
    else { hx = 2 * d + w + (x + w / 2); vy = h + (d / 2 - z); }
    uv.setXY(i, hx / AW, 1 - vy / AH);
  }
  uv.needsUpdate = true; return geo;
}

// ---------------- small tiles ----------------
function knitTile() { // V-stitch knit rows, used as a pattern (colour) and as a bump map
  return cached('knitTile', () => {
    const N = 64, c = canvas(N), g = c.getContext('2d'); g.fillStyle = '#808080'; g.fillRect(0, 0, N, N);
    const cols = 8, rows = 8, cw = N / cols, rh = N / rows;
    for (let r = 0; r < rows; r++) for (let k = 0; k < cols; k++) {
      const x = k * cw, y = r * rh;
      for (const s of [-1, 1]) { const gr = g.createLinearGradient(x + cw / 2, y, x + cw / 2 + s * cw / 2, y + rh); gr.addColorStop(0, '#e8e8e8'); gr.addColorStop(1, '#5a5a5a');
        g.fillStyle = gr; g.beginPath(); g.moveTo(x + cw / 2, y + rh); g.lineTo(x + cw / 2 + s * cw * 0.48, y + rh * 0.05); g.lineTo(x + cw / 2 + s * cw * 0.12, y + rh * 0.05); g.closePath(); g.fill(); }
      g.fillStyle = '#3a3a3a'; g.fillRect(x + cw / 2 - 0.6, y, 1.2, rh);
    }
    return { canvas: c };
  }).canvas;
}
export function knitBumpTexture() { return cached('knitBumpTex', () => canvasTex(knitTile(), { srgb: false, wrap: true })); }

// ---------------- painting context ----------------
// Each face is painted in stud units: (0,0) = the face's top-left as seen from outside, x right, y down.
function paintAtlas(partName, P, spec, painter) {
  const { w, h, d, top } = P, AW = 2 * w + 2 * d, AH = h + d, ppu = spec.ppu || PPU;
  const c = canvas(AW * ppu, AH * ppu), g = c.getContext('2d');
  const R = faceRects(w, h, d);
  for (const face of ['nx', 'pz', 'px', 'nz', 'py', 'ny']) {
    const [rx, ry, fw, fh] = R[face];
    g.save(); g.setTransform(ppu, 0, 0, ppu, rx * ppu, ry * ppu); g.beginPath(); g.rect(0, 0, fw, fh); g.clip();
    const side = partName.endsWith('L') ? 1 : partName.endsWith('R') ? -1 : 0; // L parts sit at +x
    const F = { g, face, part: partName, w: fw, h: fh, top, hx0: rx, ppu,
      front: face === 'pz', back: face === 'nz', topFace: face === 'py', bottom: face === 'ny', sideFace: face === 'px' || face === 'nx',
      outer: side !== 0 && ((side > 0 && face === 'px') || (side < 0 && face === 'nx')), inner: side !== 0 && ((side > 0 && face === 'nx') || (side < 0 && face === 'px')),
      rng: makeRng(hash32(partName, face, spec.seed || 1)) };
    painter(F);
    g.restore();
  }
  return c;
}
const isArm = (F) => F.part.startsWith('arm'), isLeg = (F) => F.part.startsWith('leg'), isTorso = (F) => F.part === 'torso';
const wy = (F, v) => F.top - v; // world y (studs) of face-local v (vertical faces)

// ---------------- patterns ----------------
function fill(F, color) { F.g.fillStyle = color; F.g.fillRect(-1, -1, F.w + 2, F.h + 2); }
function pattern(F, pat, x0 = 0, y0 = 0, x1 = F.w, y1 = F.h) {
  if (!pat || !pat.type) return; const g = F.g; g.save(); g.beginPath(); g.rect(x0, y0, x1 - x0, y1 - y0); g.clip();
  const vertical = !F.topFace && !F.bottom;
  if (pat.type === 'stripes') { // horizontal stripes aligned in world y (continue across torso and arms)
    const per = pat.period || 0.2; g.fillStyle = pat.color;
    if (vertical) for (let v = -per * 2; v < F.h + per; v += 0.01) { const yw = wy(F, v); if (Math.floor(yw / (per / 2)) % 2 === 0) g.fillRect(-1, v, F.w + 2, 0.0105); }
    else g.fillRect(-1, -1, F.w + 2, F.h + 2);
  } else if (pat.type === 'plaid' || pat.type === 'tartan' || pat.type === 'check') {
    const per = pat.period || (pat.type === 'check' ? 0.16 : 0.34), bw = per * (pat.type === 'check' ? 0.5 : 0.36);
    const yy = (v) => (vertical ? wy(F, v) : v), hx = (u) => F.hx0 + u;
    g.globalAlpha = pat.alpha ?? (pat.type === 'check' ? 0.35 : 0.5); g.fillStyle = pat.color;
    for (let u = 0; u < F.w; u += 0.004) { const k = ((hx(u) % per) + per) % per; if (k < bw) g.fillRect(u, -1, 0.0045, F.h + 2); }
    for (let v = -0.01; v < F.h + 0.01; v += 0.004) { const k = ((yy(v) % per) + per) % per; if (k < bw) g.fillRect(-1, v, F.w + 2, 0.0045); }
    if (pat.color2) { g.globalAlpha = 0.85; g.fillStyle = pat.color2; for (let u = 0; u < F.w; u += 0.004) { const k = ((hx(u) % per) + per) % per; if (Math.abs(k - per * 0.68) < 0.008) g.fillRect(u, -1, 0.0045, F.h + 2); }
      for (let v = 0; v < F.h; v += 0.004) { const k = ((yy(v) % per) + per) % per; if (Math.abs(k - per * 0.68) < 0.008) g.fillRect(-1, v, F.w + 2, 0.0045); } }
    g.globalAlpha = 1;
  } else if (pat.type === 'stars' || pat.type === 'dots' || pat.type === 'floral') {
    const r = makeRng(hash32('pat', F.part, F.face, pat.type)), n = Math.round((pat.density || 14) * F.w * F.h);
    for (let i = 0; i < n; i++) { const x = r() * F.w, y = r() * F.h, s = (pat.size || 0.06) * (0.8 + r() * 0.4);
      if (pat.type === 'dots') { g.fillStyle = pat.color; g.beginPath(); g.arc(x, y, s, 0, Math.PI * 2); g.fill(); }
      else if (pat.type === 'stars') { g.fillStyle = pat.color; star(g, x, y, s, r() * 1.2); }
      else { for (let k = 0; k < 5; k++) { const a = k / 5 * Math.PI * 2 + r(); g.fillStyle = pat.color; g.beginPath(); g.ellipse(x + Math.cos(a) * s * 0.6, y + Math.sin(a) * s * 0.6, s * 0.55, s * 0.35, a, 0, Math.PI * 2); g.fill(); }
        g.fillStyle = pat.color2 || '#f4d25a'; g.beginPath(); g.arc(x, y, s * 0.3, 0, Math.PI * 2); g.fill(); }
    }
  }
  g.restore();
}
function star(g, x, y, R, rot = 0) { g.beginPath(); for (let k = 0; k < 10; k++) { const a = rot + k * Math.PI / 5 - Math.PI / 2, r = k % 2 ? R * 0.45 : R; g.lineTo(x + Math.cos(a) * r, y + Math.sin(a) * r); } g.closePath(); g.fill(); }
function grain(F, alpha = 0.1, src = null) { const g = F.g, pat = g.createPattern(src || grainCanvas(96, 7), 'repeat'); const m = new DOMMatrix().scale(1 / F.ppu * 1.5); pat.setTransform(m); g.save(); g.globalAlpha = alpha; g.globalCompositeOperation = 'overlay'; g.fillStyle = pat; g.fillRect(-1, -1, F.w + 2, F.h + 2); g.restore(); }
function knit(F, alpha = 0.32, x0 = 0, y0 = 0, x1 = F.w, y1 = F.h) { const g = F.g, pat = g.createPattern(knitTile(), 'repeat'); pat.setTransform(new DOMMatrix().scale(0.5 / 64)); g.save(); g.beginPath(); g.rect(x0, y0, x1 - x0, y1 - y0); g.clip(); g.globalAlpha = alpha; g.globalCompositeOperation = 'overlay'; g.fillStyle = pat; g.fillRect(-1, -1, F.w + 2, F.h + 2); g.restore(); }
function rib(F, y0, y1, color, alpha = 0.35) { const g = F.g; g.fillStyle = color; g.fillRect(-1, y0, F.w + 2, y1 - y0); g.strokeStyle = rgba('#000000', alpha * 0.5); g.lineWidth = 0.012; for (let u = 0.02; u < F.w; u += 0.045) { g.beginPath(); g.moveTo(u, y0); g.lineTo(u, y1); g.stroke(); } g.fillStyle = rgba('#000000', 0.12); g.fillRect(-1, y0, F.w + 2, 0.018); }
function button(F, x, y, r, color) { const g = F.g; g.fillStyle = shade(color, 0.6); g.beginPath(); g.arc(x, y + r * 0.12, r, 0, Math.PI * 2); g.fill(); g.fillStyle = color; g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2); g.fill();
  g.fillStyle = rgba('#000000', 0.4); for (const [dx, dy] of [[-0.3, -0.3], [0.3, -0.3], [-0.3, 0.3], [0.3, 0.3]]) { g.beginPath(); g.arc(x + dx * r, y + dy * r, r * 0.13, 0, Math.PI * 2); g.fill(); }
  g.fillStyle = rgba('#ffffff', 0.35); g.beginPath(); g.arc(x - r * 0.35, y - r * 0.35, r * 0.25, 0, Math.PI * 2); g.fill(); }
function stroke(F, color, lw, pts, close = false) { const g = F.g; g.strokeStyle = color; g.lineWidth = lw; g.lineCap = 'round'; g.lineJoin = 'round'; g.beginPath(); pts.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); if (close) g.closePath(); g.stroke(); }
function poly(F, color, pts) { const g = F.g; g.fillStyle = color; g.beginPath(); pts.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath(); g.fill(); }

// ---------------- baked shading ----------------
function shading(F, o = {}) {
  const g = F.g;
  if (F.topFace || F.bottom) { if (F.bottom) { g.fillStyle = rgba('#000000', 0.25); g.fillRect(-1, -1, F.w + 2, F.h + 2); } return; }
  // hem gradient: 10-15% darker toward the bottom
  const hg = g.createLinearGradient(0, F.h * 0.45, 0, F.h); hg.addColorStop(0, rgba('#000000', 0)); hg.addColorStop(1, rgba('#1a0a14', o.hem ?? 0.14)); g.fillStyle = hg; g.fillRect(-1, F.h * 0.45, F.w + 2, F.h * 0.56);
  // top light (key from above) on every vertical face
  const tg = g.createLinearGradient(0, 0, 0, 0.35); tg.addColorStop(0, rgba('#ffffff', 0.08)); tg.addColorStop(1, rgba('#ffffff', 0)); g.fillStyle = tg; g.fillRect(-1, 0, F.w + 2, 0.36);
  if (isTorso(F) && (F.front || F.back)) { // collar shadow under the head
    const cg = g.createRadialGradient(F.w / 2, -0.05, 0.05, F.w / 2, -0.05, 0.62); cg.addColorStop(0, rgba('#1a0814', 0.34)); cg.addColorStop(1, rgba('#1a0814', 0)); g.fillStyle = cg; g.fillRect(0, 0, F.w, 0.7);
  }
  if ((isTorso(F) && F.sideFace) || (isArm(F) && F.inner)) { // armpit darkening
    const ag = g.createLinearGradient(0, 0, 0, 0.9); ag.addColorStop(0, rgba('#1a0814', 0.3)); ag.addColorStop(1, rgba('#1a0814', 0)); g.fillStyle = ag; g.fillRect(-1, 0, F.w + 2, 0.9);
  }
  if (isLeg(F) && F.inner) { const ag = g.createLinearGradient(0, 0, 0, 0.7); ag.addColorStop(0, rgba('#1a0814', 0.25)); ag.addColorStop(1, rgba('#1a0814', 0)); g.fillStyle = ag; g.fillRect(-1, 0, F.w + 2, 0.7); }
  // soft diagonal folds (alpha 0.15-0.25)
  const r = F.rng, n = o.folds ?? (isTorso(F) ? 4 : 2);
  g.save(); g.filter = `blur(${Math.round(F.ppu * 0.018)}px)`;
  for (let i = 0; i < n; i++) {
    const x = r() * F.w, y = 0.3 + r() * (F.h - 0.6), L = 0.25 + r() * 0.35, a = (isArm(F) || isLeg(F) ? 0.15 : 0.6) * (r() < 0.5 ? -1 : 1) + (r() - 0.5) * 0.4;
    for (const [dx, col, al] of [[0, '#1a0814', 0.13 + r() * 0.08], [0.035, '#ffffff', 0.05]]) {
      g.strokeStyle = rgba(col, al); g.lineWidth = 0.04 + r() * 0.02; g.lineCap = 'round';
      g.beginPath(); g.moveTo(x + dx, y); g.quadraticCurveTo(x + Math.sin(a) * L * 0.5 + 0.02 + dx, y + L * 0.5, x + Math.sin(a) * L + dx, y + Math.cos(a) * L); g.stroke();
    }
  }
  g.restore();
}

// ---------------- shirts ----------------
// spec: { style, color, pattern, inner: {color, pattern}, sleeves: 'long'|'short', hand: 0.38, skin, collar, buttons, pocket, trim, knit, necklace }
function shirtPainter(spec) {
  const S = Object.assign({ style: 'tee', color: '#2d8a05', sleeves: 'long', hand: 0.36, skin: SKIN.salmon }, spec);
  const trim = S.trim || shade(S.color, 0.82), knitted = S.knit ?? ['cardigan', 'sweater'].includes(S.style);
  return (F) => {
    const g = F.g;
    // arms: skin hand band / short sleeves
    if (isArm(F)) {
      const sleeveEnd = S.sleeves === 'short' ? 0.72 : S.sleeves === 'three' ? 1.35 : F.h - S.hand;
      if (F.topFace) { fill(F, S.color); pattern(F, S.pattern); if (knitted) knit(F); return; }
      if (F.bottom) { fill(F, S.hand > 0 || S.sleeves !== 'long' ? S.skin : S.color); shading(F); return; }
      fill(F, S.skin);
      // skin: soft plastic shading
      const sg = g.createLinearGradient(0, sleeveEnd, 0, F.h); sg.addColorStop(0, rgba('#000000', 0.08)); sg.addColorStop(1, rgba('#000000', 0)); g.fillStyle = sg; g.fillRect(-1, sleeveEnd, F.w + 2, F.h);
      g.save(); g.beginPath(); g.rect(-1, -1, F.w + 2, sleeveEnd + 1); g.clip();
      fill(F, S.color); pattern(F, S.pattern); if (S.style === 'hoodie' || S.style === 'pyjama') grain(F, 0.12); if (knitted) knit(F);
      if (S.style === 'cardigan' || S.style === 'sweater' || S.style === 'hoodie') rib(F, sleeveEnd - 0.17, sleeveEnd, trim);
      else if (S.style === 'pyjama' && S.piping) { g.fillStyle = S.piping; g.fillRect(-1, sleeveEnd - 0.07, F.w + 2, 0.045); }
      else if (S.style === 'shirt' || S.style === 'blazer') { g.fillStyle = rgba('#000000', 0.12); g.fillRect(-1, sleeveEnd - 0.2, F.w + 2, 0.012); g.fillStyle = rgba('#ffffff', 0.1); g.fillRect(-1, sleeveEnd - 0.19, F.w + 2, 0.18); }
      if (S.cuff) { g.fillStyle = S.cuff; g.fillRect(-1, sleeveEnd - 0.16, F.w + 2, 0.16); }
      // lighter cuff band + sleeve shading
      g.fillStyle = rgba('#ffffff', 0.07); g.fillRect(-1, sleeveEnd - 0.14, F.w + 2, 0.12);
      shading(F, { hem: 0.1 });
      g.restore();
      g.fillStyle = rgba('#1a0814', 0.22); g.fillRect(-1, sleeveEnd - 0.005, F.w + 2, 0.022); // sleeve edge line
      return;
    }
    // torso
    fill(F, S.color); pattern(F, S.pattern);
    if (S.style === 'hoodie' || S.style === 'pyjama') grain(F, 0.12); else grain(F, 0.06);
    if (knitted) knit(F);
    if (F.topFace || F.bottom) { shading(F); return; }
    const cx = F.w / 2;
    if (S.style === 'cardigan' || S.style === 'blazer') {
      const inner = S.inner || { color: '#f2ece0' };
      if (F.front) {
        const vy = S.style === 'blazer' ? 1.05 : (S.vDepth ?? 0.95), open = S.open ?? (S.style === 'blazer');
        // inner shirt in the V (and below it if open)
        g.save(); g.beginPath(); if (open) { g.moveTo(cx - 0.42, 0); g.lineTo(cx + 0.42, 0); g.lineTo(cx + 0.2, F.h + 0.1); g.lineTo(cx - 0.2, F.h + 0.1); }
        else { g.moveTo(cx - 0.46, -0.01); g.lineTo(cx + 0.46, -0.01); g.lineTo(cx, vy); } g.closePath(); g.clip();
        fill(F, inner.color); if (inner.pattern) pattern(F, inner.pattern); grain(F, 0.06);
        if (inner.collar !== false) { poly(F, shade(inner.color, 1.05), [[cx - 0.36, 0], [cx - 0.02, 0.06], [cx - 0.16, 0.24]]); poly(F, shade(inner.color, 1.05), [[cx + 0.36, 0], [cx + 0.02, 0.06], [cx + 0.16, 0.24]]);
          stroke(F, rgba('#1a0814', 0.35), 0.014, [[cx - 0.36, 0], [cx - 0.16, 0.24], [cx - 0.02, 0.06]]); stroke(F, rgba('#1a0814', 0.35), 0.014, [[cx + 0.36, 0], [cx + 0.16, 0.24], [cx + 0.02, 0.06]]); }
        if (inner.buttons) for (let y = 0.34; y < (open ? F.h : vy) - 0.05; y += 0.3) button(F, cx, y, 0.028, inner.buttons);
        if (S.necklace) { for (let k = -7; k <= 7; k++) { const t = k / 7, x = cx + t * 0.3, y = 0.06 + (1 - t * t) * 0.3; const gg = g.createRadialGradient(x - 0.01, y - 0.01, 0.002, x, y, 0.03); gg.addColorStop(0, '#ffffff'); gg.addColorStop(1, S.necklace); g.fillStyle = gg; g.beginPath(); g.arc(x, y, 0.028, 0, Math.PI * 2); g.fill(); } }
        g.fillStyle = rgba('#1a0814', 0.2); g.fillRect(-1, 0, F.w + 2, 0.08);
        g.restore();
        // V edges: placket band
        const band = S.style === 'blazer' ? 0.0 : 0.075, bc = S.trim || shade(S.color, 0.9);
        if (open) { for (const s of [-1, 1]) { stroke(F, rgba('#1a0814', 0.4), 0.02, [[cx + s * 0.42, 0], [cx + s * 0.2, F.h]]);
            if (S.style === 'blazer') { poly(F, shade(S.color, 0.88), [[cx + s * 0.42, 0], [cx + s * 0.62, 0.05], [cx + s * 0.36, 0.62], [cx + s * 0.3, 0.55]]); stroke(F, rgba('#1a0814', 0.35), 0.014, [[cx + s * 0.62, 0.05], [cx + s * 0.36, 0.62]]); }
            else { g.save(); g.fillStyle = bc; g.beginPath(); g.moveTo(cx + s * 0.42, 0); g.lineTo(cx + s * (0.42 + band), 0); g.lineTo(cx + s * (0.2 + band), F.h); g.lineTo(cx + s * 0.2, F.h); g.closePath(); g.fill(); g.restore(); }
          }
          if (S.style !== 'blazer') for (let y = 0.6; y < F.h - 0.25; y += 0.33) button(F, cx - 0.31 + y * 0.11 - 0.04, y, 0.034, S.buttons || '#6b4a2a');
        } else {
          for (const s of [-1, 1]) { g.fillStyle = bc; g.beginPath(); g.moveTo(cx + s * 0.46, -0.01); g.lineTo(cx + s * (0.46 + band), -0.01); g.lineTo(cx + s * band * 0.5, vy + band); g.lineTo(cx, vy); g.closePath(); g.fill(); }
          g.fillStyle = bc; g.fillRect(cx - band / 2, vy, band, F.h - vy); stroke(F, rgba('#1a0814', 0.3), 0.012, [[cx, vy], [cx, F.h]]);
          for (let y = vy + 0.12; y < F.h - 0.2; y += 0.26) button(F, cx, y, 0.038, S.buttons || '#6b4a2a');
        }
        if (S.pocket !== false && S.style === 'cardigan') for (const s of [-1, 1]) { const px = cx + s * 0.6; g.fillStyle = rgba('#1a0814', 0.12); g.fillRect(px - 0.24, 1.32, 0.48, 0.42); rib(F, 1.3, 1.38, S.trim || shade(S.color, 0.85)); g.save(); g.beginPath(); g.rect(px - 0.24, 1.3, 0.48, 0.44); g.clip(); g.restore(); stroke(F, rgba('#1a0814', 0.3), 0.012, [[px - 0.24, 1.3], [px - 0.24, 1.74], [px + 0.24, 1.74], [px + 0.24, 1.3]]); }
      }
      if (S.style === 'cardigan') rib(F, F.h - 0.2, F.h, S.trim || shade(S.color, 0.85));
      if (S.style === 'blazer' && F.front) for (const s of [-1, 1]) stroke(F, rgba('#1a0814', 0.3), 0.014, [[cx + s * 0.75, 1.35], [cx + s * 0.4, 1.38]]);
    } else if (S.style === 'hoodie') {
      if (F.front) {
        // kangaroo pocket
        poly(F, rgba('#1a0814', 0.06), [[0.38, 1.12], [1.62, 1.12], [1.78, 1.78], [0.22, 1.78]]); stroke(F, rgba('#1a0814', 0.35), 0.02, [[0.22, 1.78], [0.38, 1.12], [1.62, 1.12], [1.78, 1.78]]);
        stroke(F, rgba('#1a0814', 0.25), 0.012, [[0.42, 1.2], [1.58, 1.2]]);
        // neckline + drawstrings
        stroke(F, rgba('#1a0814', 0.35), 0.035, [[0.52, 0.0], [0.7, 0.16], [1.3, 0.16], [1.48, 0.0]]);
        for (const s of [-1, 1]) { stroke(F, S.strings || '#f2ead8', 0.035, [[cx + s * 0.16, 0.16], [cx + s * 0.18, 0.62]]); g.fillStyle = shade(S.strings || '#f2ead8', 0.8); g.fillRect(cx + s * 0.18 - 0.03, 0.6, 0.06, 0.09); }
      }
      if (F.back) { poly(F, rgba('#1a0814', 0.12), [[0.35, 0], [1.65, 0], [1.4, 0.55], [0.6, 0.55]]); stroke(F, rgba('#1a0814', 0.3), 0.02, [[0.35, 0], [0.6, 0.55], [1.4, 0.55], [1.65, 0]]); }
      rib(F, F.h - 0.18, F.h, trim);
    } else if (S.style === 'pyjama' || S.style === 'shirt') {
      if (F.front) {
        const pc = S.piping || shade(S.color, 0.8);
        stroke(F, rgba('#1a0814', 0.3), 0.014, [[cx + 0.05, 0.28], [cx + 0.05, F.h]]);
        for (let y = 0.42; y < F.h - 0.1; y += 0.34) button(F, cx + 0.02, y, 0.035, S.buttons || '#f4efe6');
        // collar points
        for (const s of [-1, 1]) { poly(F, shade(S.color, 1.08), [[cx + s * 0.5, -0.01], [cx + s * 0.02, 0.06], [cx + s * 0.3, 0.32]]); stroke(F, S.style === 'pyjama' ? pc : rgba('#1a0814', 0.35), 0.022, [[cx + s * 0.5, -0.01], [cx + s * 0.3, 0.32], [cx + s * 0.02, 0.06]]); }
        if (S.pocket) { const px = cx + 0.52; g.fillStyle = rgba('#1a0814', 0.07); g.fillRect(px - 0.18, 0.5, 0.36, 0.38); stroke(F, rgba('#1a0814', 0.3), 0.012, [[px - 0.18, 0.5], [px - 0.18, 0.88], [px + 0.18, 0.88], [px + 0.18, 0.5], [px - 0.18, 0.5]]); }
      }
      if (S.style === 'shirt' && S.tucked) { g.fillStyle = S.belt || '#3a2416'; g.fillRect(-1, F.h - 0.16, F.w + 2, 0.16); if (F.front) { g.fillStyle = '#d6b45a'; g.fillRect(cx - 0.09, F.h - 0.15, 0.18, 0.14); g.fillStyle = S.belt || '#3a2416'; g.fillRect(cx - 0.05, F.h - 0.12, 0.1, 0.08); } }
    } else if (S.style === 'sweater') {
      if (F.front || F.back) { stroke(F, trim, 0.09, [[0.55, 0.0], [0.72, 0.12], [1.28, 0.12], [1.45, 0.0]]); }
      rib(F, F.h - 0.18, F.h, trim);
    } else if (S.style === 'tee') {
      if (F.front || F.back) stroke(F, trim, 0.06, [[0.6, 0.0], [0.78, 0.12], [1.22, 0.12], [1.4, 0.0]]);
      if (S.logo && F.front) { g.fillStyle = S.logo; star(g, cx, 0.9, 0.3, 0); }
    }
    if (S.suspenders && (F.front || F.back)) for (const s of [-1, 1]) { stroke(F, S.suspenders, 0.1, [[cx + s * 0.5, 0], [cx + s * 0.45, F.h]]); if (F.front) { g.fillStyle = '#c9c2b0'; g.fillRect(cx + s * 0.45 - 0.07, F.h - 0.2, 0.14, 0.1); } }
    shading(F);
  };
}

// ---------------- pants ----------------
// spec: { style: 'trousers'|'jeans'|'pyjama'|'skirt'|'shorts', color, pattern, shoes: {style, color, color2, pattern}, skin, belt, stockings, skirtLen }
function pantsPainter(spec) {
  const S = Object.assign({ style: 'trousers', color: '#3b3f58', skin: SKIN.salmon }, spec);
  const sh = Object.assign({ style: 'shoes', color: '#3a2a22', color2: '#f2ece0', h: 0.3 }, S.shoes || {});
  return (F) => {
    const g = F.g, shoeTop = F.h - sh.h;
    if (F.topFace) { fill(F, S.color); return; }
    if (F.bottom) { fill(F, sh.style === 'barefoot' ? S.skin : sh.style === 'sneakers' ? sh.color2 : shade(sh.color, 0.55)); return; }
    const isSkirt = S.style === 'skirt', legEnd = isSkirt ? (S.skirtLen ?? 1.15) : S.style === 'shorts' ? 0.85 : shoeTop;
    // under-layer (stockings / skin) for skirts and shorts
    if (legEnd < shoeTop) { fill(F, S.stockings || S.skin); const sg = g.createLinearGradient(0, legEnd, 0, shoeTop); sg.addColorStop(0, rgba('#000000', 0.18)); sg.addColorStop(1, rgba('#000000', 0)); g.fillStyle = sg; g.fillRect(-1, legEnd, F.w + 2, shoeTop - legEnd); }
    g.save(); g.beginPath(); g.rect(-1, -1, F.w + 2, legEnd + 1); g.clip();
    fill(F, S.color); pattern(F, S.pattern); grain(F, S.style === 'jeans' ? 0.2 : 0.1);
    if (S.style === 'jeans') { g.strokeStyle = rgba('#f0c060', 0.6); g.lineWidth = 0.012; g.setLineDash([0.03, 0.02]); if (F.outer) { g.beginPath(); g.moveTo(F.w * 0.5, 0); g.lineTo(F.w * 0.5, legEnd); g.stroke(); } g.setLineDash([]); }
    if (!isSkirt) {
      if (F.outer) stroke(F, rgba('#1a0814', 0.25), 0.014, [[F.w * 0.5, 0.1], [F.w * 0.5, legEnd]]);
      if (F.front && S.style !== 'pyjama') { stroke(F, rgba('#ffffff', 0.12), 0.03, [[F.w * 0.5, 0.35], [F.w * 0.5, legEnd - 0.05]]); stroke(F, rgba('#1a0814', 0.12), 0.012, [[F.w * 0.5 + 0.02, 0.35], [F.w * 0.5 + 0.02, legEnd - 0.05]]); }
      if (F.front && S.style !== 'pyjama') { const s = F.part === 'legL' ? 1 : -1; const xo = s > 0 ? F.w : 0; stroke(F, rgba('#1a0814', 0.3), 0.016, [[xo - s * 0.34, 0.16], [xo - s * 0.06, 0.55]]); }
      if (S.belt) { g.fillStyle = S.belt; g.fillRect(-1, 0, F.w + 2, 0.14); g.fillStyle = rgba('#000000', 0.25); g.fillRect(-1, 0.13, F.w + 2, 0.015); }
      if (S.style === 'pyjama' && S.piping) { g.fillStyle = S.piping; g.fillRect(-1, legEnd - 0.08, F.w + 2, 0.045); }
      if (S.style === 'shorts') { g.fillStyle = rgba('#1a0814', 0.25); g.fillRect(-1, legEnd - 0.02, F.w + 2, 0.02); }
      // cuff break above the shoe
      g.fillStyle = rgba('#1a0814', 0.18); g.fillRect(-1, legEnd - 0.06, F.w + 2, 0.06);
    } else {
      // A-line skirt: vertical soft pleats + hem
      for (let u = 0.12; u < F.w; u += 0.24) { const gr = g.createLinearGradient(u - 0.12, 0, u + 0.12, 0); gr.addColorStop(0, rgba('#1a0814', 0)); gr.addColorStop(0.5, rgba('#1a0814', 0.12)); gr.addColorStop(1, rgba('#1a0814', 0)); g.fillStyle = gr; g.fillRect(u - 0.12, 0.25, 0.24, legEnd); }
      g.fillStyle = S.hem || shade(S.color, 0.8); g.fillRect(-1, legEnd - 0.07, F.w + 2, 0.07);
      if (S.belt) { g.fillStyle = S.belt; g.fillRect(-1, 0, F.w + 2, 0.12); }
    }
    shading(F, { folds: 2, hem: 0.12 });
    g.restore();
    // shoes
    g.save(); g.beginPath(); g.rect(-1, shoeTop, F.w + 2, F.h - shoeTop + 1); g.clip();
    if (sh.style === 'barefoot') { fill(F, S.skin); if (F.front) for (let k = 1; k < 5; k++) stroke(F, rgba('#6a2a20', 0.35), 0.014, [[k * 0.2, F.h - 0.1], [k * 0.2, F.h]]); }
    else if (sh.style === 'socks') { fill(F, sh.color); stroke(F, rgba('#000000', 0.15), 0.02, [[0, shoeTop + 0.05], [F.w, shoeTop + 0.05]]); }
    else {
      fill(F, sh.color); if (sh.pattern) pattern(F, sh.pattern);
      const sole = sh.style === 'sneakers' ? sh.color2 : shade(sh.color, 0.5);
      g.fillStyle = sole; g.fillRect(-1, F.h - (sh.style === 'slippers' ? 0.06 : 0.08), F.w + 2, 0.1);
      if (sh.style === 'shoes' && F.front) { for (let k = 0; k < 3; k++) stroke(F, rgba('#f2ece0', 0.7), 0.016, [[0.36, shoeTop + 0.07 + k * 0.05], [0.64, shoeTop + 0.07 + k * 0.05]]); }
      if (sh.style === 'sneakers' && F.outer) { stroke(F, sh.color2, 0.03, [[0.2, F.h - 0.1], [0.5, shoeTop + 0.06], [0.8, F.h - 0.1]]); }
      if (sh.style === 'slippers') { g.fillStyle = rgba('#ffffff', 0.22); g.fillRect(-1, shoeTop, F.w + 2, 0.05); }
      const hg = g.createLinearGradient(0, shoeTop, 0, F.h); hg.addColorStop(0, rgba('#ffffff', 0.12)); hg.addColorStop(1, rgba('#000000', 0.1)); g.fillStyle = hg; g.fillRect(-1, shoeTop, F.w + 2, F.h);
      g.fillStyle = rgba('#000000', 0.3); g.fillRect(-1, shoeTop, F.w + 2, 0.014);
    }
    g.restore();
  };
}

// ---------------- materials ----------------
// outfitMaterials({ shirt, pants, skin }) -> { torso, armL, armR, legL, legR } (cached, persistent; read-only)
export function outfitMaterials(o = {}) {
  const skin = o.skin || SKIN.salmon;
  const shirt = Object.assign({ skin }, o.shirt || {}), pants = Object.assign({ skin }, o.pants || {});
  const out = {};
  for (const part of ['torso', 'armL', 'armR']) out[part] = cached(keyOf('shirtMat', part, shirt), () => partMaterial(part, shirt, shirtPainter(shirt), shirt.knit ?? ['cardigan', 'sweater'].includes(shirt.style)));
  for (const part of ['legL', 'legR']) out[part] = cached(keyOf('pantsMat', part, pants), () => partMaterial(part, pants, pantsPainter(pants), false));
  return out;
}
function partMaterial(part, spec, painter, knitBump) {
  const P = PARTS[part], c = paintAtlas(part, P, spec, painter);
  const m = new THREE.MeshStandardMaterial({ map: canvasTex(c), roughness: spec.rough ?? (knitBump ? 0.72 : 0.64), metalness: 0 });
  if (knitBump) { const b = knitBumpTexture().clone(); b.repeat.set((2 * P.w + 2 * P.d) * 2, (P.h + P.d) * 2); b.needsUpdate = true; b.userData.persistent = true; m.bumpMap = b; m.bumpScale = spec.bumpScale ?? 1.2; }
  return m;
}
// Paint any shirt / pants spec to a canvas atlas (for sheets and debugging).
export function shirtAtlasCanvas(part, spec) { return paintAtlas(part, PARTS[part], Object.assign({ skin: SKIN.salmon }, spec), part.startsWith('leg') ? pantsPainter(spec) : shirtPainter(spec)); }

// ---------------- outfit presets ----------------
export const OUTFITS = {
  heroHoodie: { shirt: { style: 'hoodie', color: '#d9a52c', trim: '#b98a1e', strings: '#f2ead8' }, pants: { style: 'jeans', color: '#3d4f7a', shoes: { style: 'sneakers', color: '#e9e4f2', color2: '#ffffff' } } },
  theoPyjamas: { shirt: { style: 'pyjama', color: '#7d9be8', pattern: { type: 'stars', color: '#f6e7a2', density: 9, size: 0.06 }, piping: '#e9efff', buttons: '#ffffff', hand: 0.18 }, pants: { style: 'pyjama', color: '#7d9be8', pattern: { type: 'stars', color: '#f6e7a2', density: 9, size: 0.06 }, piping: '#e9efff', shoes: { style: 'socks', color: '#e9e4f2', h: 0.24 } } },
  grandpaCardigan: { shirt: { style: 'cardigan', color: '#2f4f8c', trim: '#26407a', buttons: '#c9a36a', inner: { color: '#e8ecf4', pattern: { type: 'check', color: '#8fa6d6', period: 0.14 }, buttons: '#ffffff' } },
    pants: { style: 'trousers', color: '#6e6a74', belt: '#3a2416', shoes: { style: 'slippers', color: '#8a2a2a', pattern: { type: 'tartan', color: '#1f3a2a', color2: '#e8c05a', period: 0.22 }, h: 0.26 } } },
  grandpaFlashback: { shirt: { style: 'cardigan', color: '#7a4a2a', trim: '#5e381f', buttons: '#d8c09a', inner: { color: '#efe6d2', buttons: '#ffffff' } },
    pants: { style: 'trousers', color: '#5c5a48', belt: '#2a1a10', shoes: { style: 'slippers', color: '#8a2a2a', pattern: { type: 'tartan', color: '#1f3a2a', color2: '#e8c05a', period: 0.22 }, h: 0.26 } } },
  grandmaCardigan: { shirt: { style: 'cardigan', color: '#c86f93', trim: '#a8587a', buttons: '#f4ead8', open: true, necklace: '#f3eee6', inner: { color: '#f4efe8', pattern: { type: 'floral', color: '#b9a2e0', color2: '#f2cf6a', density: 12, size: 0.05 }, collar: true } },
    pants: { style: 'skirt', color: '#6e5a8c', skirtLen: 1.42, stockings: '#e2b9a0', shoes: { style: 'slippers', color: '#b05a7a', h: 0.24 } } },
  momSweater: { shirt: { style: 'sweater', color: '#5e8c5a', trim: '#4c7448' }, pants: { style: 'jeans', color: '#4a5a86', shoes: { style: 'shoes', color: '#2a2024' } } },
  dadPlaid: { shirt: { style: 'shirt', color: '#a8231e', pattern: { type: 'plaid', color: '#1a0c10', period: 0.36, alpha: 0.62 }, buttons: '#2a1a1a' }, pants: { style: 'jeans', color: '#3a4060', shoes: { style: 'shoes', color: '#4a3020' } } },
  plainKid: { shirt: { style: 'tee', color: '#2d8a05' }, pants: { style: 'trousers', color: '#1e1e26', shoes: { style: 'sneakers', color: '#1e1e26', color2: '#ffffff' } } },
};
