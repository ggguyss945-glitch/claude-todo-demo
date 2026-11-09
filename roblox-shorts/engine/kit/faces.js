// Decal face system (VISUAL_BIBLE §2.5). Faces are drawn on a transparent canvas in the bible's 512x512 coordinate
// frame (x = 256 face centre, y = 0 head top, y = 512 head bottom) at FACE_RES (default 1024, i.e. 2x) so close-ups at
// 1080p stay crisp. The texture maps onto a band that hugs the front 140 degrees of the R6 drum head (see avatar.js).
//
//   faceTexture('grin', { overlays }) -> cached THREE.CanvasTexture (persistent)
//   FACES                             -> list of expression names (+ ALIASES)
//   drawFace(g2d, name, overlays)     -> draw into any 2D context already scaled to the 512 frame
import { THREE, cached, canvas, canvasTex, keyOf, makeRng, rgba } from './util.js';

export const FACE_RES = 1024;
export const INK = '#141414', RED = '#d01818', TEETH = '#f1ecff', TONGUE = '#e2405a', TEAR = '#8fd0ff', LILAC = '#c9b3ff';

// Canonical expressions (bible table #1-15) + extras used by the episode.
export const FACES = ['neutral', 'wonder', 'shock', 'grin', 'openSmile', 'content', 'angry', 'sad', 'heartfelt', 'sleeping', 'sideGlance',
  'horrified', 'sob', 'wetEyes', 'smirk', 'talk', 'blank', 'worriedSmile', 'determined'];
export const ALIASES = { smile: 'neutral', default: 'neutral', o: 'wonder', huh: 'wonder', surprise: 'shock', redO: 'shock', teeth: 'grin', laugh: 'openSmile',
  excited: 'openSmile', happy: 'content', cosy: 'content', cross: 'angry', worried: 'sad', worry: 'sad', guilt: 'sad', tender: 'heartfelt', asleep: 'sleeping',
  suspicious: 'sideGlance', thinking: 'sideGlance', terror: 'horrified', scream: 'horrified', cry: 'sob', panic: 'sob', tears: 'wetEyes', mischief: 'smirk',
  speaking: 'talk', closed: 'neutral' };
export const resolveFace = (n) => (FACES.includes(n) ? n : ALIASES[n] || 'neutral');

// ---------------- primitives (512 frame) ----------------
const W = 512;
function ln(g, w = 11, c = INK) { g.strokeStyle = c; g.lineWidth = w; g.lineCap = 'round'; g.lineJoin = 'round'; }
function oval(g, x, y, rx, ry, fill = INK) { g.fillStyle = fill; g.beginPath(); g.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2); g.fill(); }
const D2R = Math.PI / 180;
function arc(g, x, y, r, a0, a1, w = 11, c = INK) { ln(g, w, c); g.beginPath(); g.arc(x, y, r, a0 * D2R, a1 * D2R); g.stroke(); }
function seg(g, x0, y0, x1, y1, w = 12, c = INK) { ln(g, w, c); g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke(); }
function quad(g, x0, y0, cx, cy, x1, y1, w = 8, c = INK) { ln(g, w, c); g.beginPath(); g.moveTo(x0, y0); g.quadraticCurveTo(cx, cy, x1, y1); g.stroke(); }
const EL = 196, ER = 316, EY = 240; // eye centres
function baseEyes(g, rx = 20, ry = 36, dx = 0, dy = 0) { oval(g, EL + dx, EY + dy, rx, ry); oval(g, ER + dx, EY + dy, rx, ry); }
function smileArc(g, cx = 256, cy = 300, r = 70, a0 = 35, a1 = 145, w = 11) { arc(g, cx, cy, r, a0, a1, w); }
// D-shaped open mouth: flat top (x0..x1 at yTop), curved bottom down to yBot
function dPath(g, x0, x1, yTop, yBot) { const cx = (x0 + x1) / 2, hw = (x1 - x0) / 2; g.beginPath(); g.moveTo(x0, yTop); g.lineTo(x1, yTop); g.bezierCurveTo(x1, yTop + (yBot - yTop) * 0.9, cx + hw * 0.55, yBot, cx, yBot); g.bezierCurveTo(cx - hw * 0.55, yBot, x0, yTop + (yBot - yTop) * 0.9, x0, yTop); g.closePath(); }
function upBrows(g, y = 175, w = 8) { quad(g, EL - 26, y + 8, EL, y - 10, EL + 26, y + 6, w); quad(g, ER - 26, y + 6, ER, y - 10, ER + 26, y + 8, w); }

// ---------------- expressions ----------------
const DRAW = {
  neutral(g) { baseEyes(g); smileArc(g); },
  blank(g) { baseEyes(g); },
  wonder(g) { baseEyes(g); upBrows(g, 175, 8); oval(g, 256, 345, 9, 12); },
  shock(g) {
    baseEyes(g, 22, 40); upBrows(g, 165, 8);
    oval(g, 256, 350, 18, 24, RED); ln(g, 6); g.beginPath(); g.ellipse(256, 350, 18, 24, 0, 0, Math.PI * 2); g.stroke();
  },
  grin(g) {
    baseEyes(g);
    dPath(g, 190, 322, 305, 385); g.fillStyle = TEETH; g.fill();
    g.save(); g.clip(); ln(g, 5); for (let x = 190 + 22; x < 322; x += 22) { g.beginPath(); g.moveTo(x, 305); g.lineTo(x, 390); g.stroke(); }
    seg(g, 190, 345, 322, 345, 4); g.restore();
    dPath(g, 190, 322, 305, 385); ln(g, 8); g.stroke();
  },
  openSmile(g) {
    baseEyes(g);
    dPath(g, 190, 322, 305, 385); g.fillStyle = INK; g.fill();
    g.save(); g.clip(); oval(g, 256, 392, 52, 34, TONGUE); g.restore();
    dPath(g, 190, 322, 305, 385); ln(g, 8); g.stroke();
  },
  content(g) { arc(g, EL, 268, 28, 200, 340, 10); arc(g, ER, 268, 28, 200, 340, 10); smileArc(g); },
  angry(g) { baseEyes(g, 20, 34, 0, 4); seg(g, 160, 188, 222, 214, 12); seg(g, 352, 188, 290, 214, 12); seg(g, 226, 345, 286, 345, 11); },
  determined(g) { baseEyes(g, 20, 34, 0, 4); seg(g, 162, 192, 222, 210, 11); seg(g, 350, 192, 290, 210, 11); arc(g, 256, 300, 50, 55, 125, 10); },
  sad(g) { baseEyes(g, 19, 33, 0, 6); seg(g, 166, 214, 222, 188, 11); seg(g, 346, 214, 290, 188, 11); arc(g, 256, 385, 45, 200, 340, 11); },
  worriedSmile(g) { baseEyes(g, 19, 33, 0, 6); seg(g, 166, 210, 222, 190, 10); seg(g, 346, 210, 290, 190, 10); arc(g, 256, 312, 46, 50, 130, 10); },
  heartfelt(g) { // tender: open soft eyes (no lashes, the lid line clear of the iris), soft brows raised at the inner end, symmetric smile
    for (const x of [EL, ER]) {
      oval(g, x, 248, 24, 27, LILAC); oval(g, x, 252, 12, 15, INK); oval(g, x - 6, 243, 5, 5.5, '#ffffff'); oval(g, x + 7, 259, 2.5, 3, '#ffffff');
      g.save(); g.beginPath(); g.ellipse(x, 248, 24, 27, 0, 0, Math.PI * 2); ln(g, 4); g.stroke(); g.restore();
      quad(g, x - 28, 224, x, 204, x + 28, 224, 7);
      const s = x < 256 ? -1 : 1; quad(g, x + s * 30, 190, x + s * 4, 178, x - s * 22, 170, 7);
    }
    arc(g, 256, 304, 58, 45, 135, 10);
  },
  sleeping(g) {
    for (const x of [EL, ER]) { arc(g, x, 236, 25, 20, 160, 10); const s = x < 256 ? -1 : 1; seg(g, x + s * 22, 252, x + s * 30, 262, 5); seg(g, x + s * 8, 260, x + s * 10, 271, 5); }
    oval(g, 256, 340, 8, 9);
  },
  sideGlance(g) {
    for (const x of [EL, ER]) {
      g.save(); g.beginPath(); g.rect(x - 60, EY - 36 + 24, 120, 100); g.clip(); oval(g, x + 18, EY, 20, 36); g.restore();
      seg(g, x - 24, EY - 12, x + 40, EY - 12, 9);
    }
    seg(g, 262, 340, 306, 336, 10);
  },
  horrified(g) {
    for (const x of [EL, ER]) { oval(g, x, 236, 34, 44, '#ffffff'); g.beginPath(); g.ellipse(x, 236, 34, 44, 0, 0, Math.PI * 2); ln(g, 7); g.stroke(); oval(g, x, 240, 6, 7); }
    // crazed brows
    ln(g, 9); g.beginPath(); g.moveTo(150, 176); g.lineTo(178, 160); g.lineTo(200, 172); g.lineTo(228, 150); g.stroke();
    g.beginPath(); g.moveTo(362, 176); g.lineTo(334, 160); g.lineTo(312, 172); g.lineTo(284, 150); g.stroke();
    g.beginPath(); g.ellipse(256, 372, 52, 64, 0, 0, Math.PI * 2); g.fillStyle = '#2a0608'; g.fill();
    g.save(); g.clip(); oval(g, 256, 430, 46, 30, TONGUE); g.fillStyle = TEETH; g.fillRect(200, 304, 112, 22); ln(g, 3); for (let x = 214; x < 312; x += 16) { g.beginPath(); g.moveTo(x, 304); g.lineTo(x, 326); g.stroke(); } g.restore();
    g.beginPath(); g.ellipse(256, 372, 52, 64, 0, 0, Math.PI * 2); ln(g, 8); g.stroke();
  },
  sob(g) {
    ln(g, 12); g.beginPath(); g.moveTo(170, 214); g.lineTo(220, 240); g.lineTo(170, 266); g.stroke();
    g.beginPath(); g.moveTo(342, 214); g.lineTo(292, 240); g.lineTo(342, 266); g.stroke();
    g.beginPath(); g.moveTo(222, 312); g.lineTo(290, 312); g.lineTo(312, 392); g.lineTo(200, 392); g.closePath(); g.fillStyle = RED; g.fill(); ln(g, 8); g.stroke();
    for (const [x, y, s] of [[372, 180, 1], [392, 214, 0.75]]) { g.fillStyle = TEAR; g.beginPath(); g.moveTo(x, y - 22 * s); g.quadraticCurveTo(x + 14 * s, y, x, y + 12 * s); g.quadraticCurveTo(x - 14 * s, y, x, y - 22 * s); g.fill(); }
  },
  wetEyes(g) {
    baseEyes(g, 22, 37);
    for (const x of [EL, ER]) { oval(g, x - 7, 226, 7, 9, '#ffffff'); oval(g, x + 6, 250, 3, 4, '#ffffff'); }
    seg(g, 166, 210, 222, 192, 9); seg(g, 346, 210, 290, 192, 9);
    g.fillStyle = TEAR; for (const x of [EL + 10, ER - 12]) { g.beginPath(); g.moveTo(x, 274); g.quadraticCurveTo(x + 10, 290, x, 300); g.quadraticCurveTo(x - 10, 290, x, 274); g.fill(); }
    arc(g, 256, 380, 34, 205, 335, 9);
  },
  smirk(g) {
    oval(g, EL, EY, 20, 36);
    g.save(); g.beginPath(); g.rect(ER - 40, EY - 10, 80, 80); g.clip(); oval(g, ER, EY, 20, 36); g.restore(); seg(g, ER - 26, EY - 10, ER + 26, EY - 10, 9);
    quad(g, EL - 26, 190, EL, 168, EL + 26, 184, 8);
    ln(g, 11); g.beginPath(); g.moveTo(222, 338); g.quadraticCurveTo(272, 356, 318, 318); g.stroke();
  },
  talk(g) { baseEyes(g); dPath(g, 214, 298, 318, 368); g.fillStyle = INK; g.fill(); g.save(); g.clip(); oval(g, 256, 374, 30, 18, TONGUE); g.restore(); },
};

// ---------------- overlays ----------------
// overlays: { freckles, blush, wrinkles, stubble, moustache: '#hex', brows: '#hex' (bushy brows when the expression has none),
//             browColor (recolour expression brows), lashes }
const HAS_BROWS = new Set(['wonder', 'shock', 'angry', 'determined', 'sad', 'worriedSmile', 'horrified', 'wetEyes', 'smirk']);
function drawUnder(g, o) {
  if (o.blush) { const c = typeof o.blush === 'string' ? o.blush : '#ff6f7d'; for (const x of [168, 344]) { const gr = g.createRadialGradient(x, 300, 0, x, 300, 46); gr.addColorStop(0, rgba(c, 0.32)); gr.addColorStop(1, rgba(c, 0)); g.fillStyle = gr; g.fillRect(x - 50, 250, 100, 100); } }
  if (o.freckles) { const r = makeRng(41); g.fillStyle = rgba('#b8573c', 0.42); for (const s of [-1, 1]) for (let i = 0; i < 7; i++) { g.beginPath(); g.arc(256 + s * (82 + r() * 52), 282 + r() * 18 - (i % 2) * 6, 3.4 + r() * 1.6, 0, Math.PI * 2); g.fill(); } }
  if (o.stubble) { const r = makeRng(9); g.fillStyle = rgba(typeof o.stubble === 'string' ? o.stubble : '#3a2a22', 0.38); for (let i = 0; i < 420; i++) { const a = r() * Math.PI, rr = 60 + r() * 62, x = 256 + Math.cos(a) * rr * 1.25, y = 300 + Math.sin(a) * rr * 0.95; if (y < 300) continue; g.fillRect(x, y, 2.4, 2.4); } }
  if (o.wrinkles) { // crow's feet + smile folds: soft, thin, never compete with the black line weight
    const c = typeof o.wrinkles === 'string' ? o.wrinkles : 'rgba(110,50,40,0.38)'; ln(g, 3.5, c);
    for (const s of [-1, 1]) { const x = 256 + s * 104; for (const [dy, len] of [[-12, 16], [0, 19], [12, 15]]) { g.beginPath(); g.moveTo(x, 236 + dy * 0.6); g.lineTo(x + s * len, 236 + dy * 1.4); g.stroke(); } }
    for (const s of [-1, 1]) { g.beginPath(); g.moveTo(256 + s * 96, 284); g.quadraticCurveTo(256 + s * 108, 320, 256 + s * 92, 352); g.stroke(); }
  }
}
function drawOver(g, o, name) {
  if (o.brows && !HAS_BROWS.has(name) && !['sleeping', 'content', 'sob', 'heartfelt'].includes(name)) { // soft bushy brows (elders)
    const r = makeRng(5); for (const s of [-1, 1]) { const x0 = 256 + s * 30, x1 = 256 + s * 92;
      for (let i = 0; i < 26; i++) { const t = i / 25, x = x0 + (x1 - x0) * t, y = 186 - Math.sin(t * Math.PI) * 9 + (r() - 0.5) * 5; ln(g, 7, o.brows); g.beginPath(); g.moveTo(x, y + 5); g.lineTo(x + s * 9, y - 5); g.stroke(); }
      ln(g, 3, 'rgba(60,50,60,0.45)'); g.beginPath(); g.moveTo(x0, 192); g.quadraticCurveTo((x0 + x1) / 2, 178, x1, 190); g.stroke(); }
  }
  if (o.moustache) { // walrus moustache decal (CG Dad style): bushy lobes over the top of the mouth
    const c = o.moustache, r = makeRng(17);
    g.save(); g.beginPath(); g.moveTo(256, 290);
    g.bezierCurveTo(300, 270, 350, 280, 362, 330); g.bezierCurveTo(352, 344, 330, 332, 318, 346); g.bezierCurveTo(300, 330, 280, 346, 256, 334);
    g.bezierCurveTo(232, 346, 212, 330, 194, 346); g.bezierCurveTo(182, 332, 160, 344, 150, 330); g.bezierCurveTo(162, 280, 212, 270, 256, 290); g.closePath();
    g.fillStyle = c; g.fill(); g.clip();
    for (let i = 0; i < 140; i++) { const x = 150 + r() * 212, y = 280 + r() * 60; ln(g, 2.2, 'rgba(90,80,100,0.28)'); g.beginPath(); g.moveTo(x, y); g.lineTo(x + (x - 256) * 0.08, y + 12); g.stroke(); }
    g.restore(); ln(g, 4, 'rgba(70,60,80,0.55)'); g.beginPath(); g.moveTo(256, 290); g.bezierCurveTo(300, 270, 350, 280, 362, 330); g.moveTo(256, 290); g.bezierCurveTo(212, 270, 162, 280, 150, 330); g.stroke();
  }
}

export function drawFace(g, name, o = {}) {
  name = resolveFace(name);
  drawUnder(g, o);
  DRAW[name](g);
  drawOver(g, o, name);
}

// Cached face texture (persistent). Same key -> same texture, so swapping faces is just `material.map = tex`.
export function faceTexture(name = 'neutral', overlays = {}, res = FACE_RES) {
  name = resolveFace(name);
  return cached(keyOf('face', name, overlays, res), () => {
    const c = canvas(res), g = c.getContext('2d'); const k = res / W; g.scale(k, k);
    drawFace(g, name, overlays);
    return canvasTex(c, { srgb: true, aniso: 8 });
  });
}

// Debug / sheet helper: a labelled board with every face on skin colour.
export function faceBoardCanvas(skin = '#e8a07a', overlays = {}, cols = 4, cell = 256) {
  const n = FACES.length, rows = Math.ceil(n / cols), c = canvas(cols * cell, rows * cell), g = c.getContext('2d');
  FACES.forEach((f, i) => { const x = (i % cols) * cell, y = Math.floor(i / cols) * cell; g.save(); g.translate(x, y); g.fillStyle = skin; g.fillRect(4, 4, cell - 8, cell - 8); g.scale(cell / W, cell / W); drawFace(g, f, overlays); g.restore();
    g.fillStyle = '#000'; g.font = 'bold 18px sans-serif'; g.fillText(f, x + 10, y + 26); });
  return c;
}
export { THREE };
