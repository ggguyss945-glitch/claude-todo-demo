// Exam papers drawn on canvases. Everything a pen or pencil writes is a stroke
// with a known path, so the hand holding the pen can be driven by the exact point
// being drawn (penTip) and the ink appears exactly under the nib.
import * as THREE from 'three';
import { canvas, toTex, noiseFill } from './tex.js';
import { rng, clamp, lerp } from './util.js';

export const PW = 0.21, PH = 0.297; // A4 in metres
const CW = 1024, CH = 1448;

// ---------------------------------------------------------------- strokes ---
function polyLen(pts) { let L = 0; for (let i = 1; i < pts.length; i++) L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); return L; }
function ellipsePts(cx, cy, rx, ry, a0, turns, n = 48, wob = 0) {
  const out = [];
  for (let i = 0; i <= n; i++) {
    const a = a0 - (i / n) * turns * Math.PI * 2;
    const k = 1 + wob * (i / n);
    out.push([cx + Math.cos(a) * rx * k, cy + Math.sin(a) * ry * k]);
  }
  return out;
}
// the big red "100" with a circle round it, centred on (cx, cy), digit height h
function hundredStrokes(cx, cy, h) {
  const w = h * 0.55;
  const x1 = cx - w * 1.55, x2 = cx - w * 0.1, x3 = cx + w * 1.15;
  return [
    [[x1 - w * 0.28, cy - h * 0.28], [x1 - w * 0.05, cy - h * 0.44], [x1 + w * 0.08, cy - h * 0.5], [x1 + w * 0.06, cy + h * 0.5]],
    ellipsePts(x2, cy, w * 0.48, h * 0.5, -Math.PI / 2 - 0.15, 1.04, 40),
    ellipsePts(x3, cy, w * 0.48, h * 0.5, -Math.PI / 2 - 0.15, 1.04, 40),
    ellipsePts(cx - w * 0.1, cy + h * 0.02, w * 2.75, h * 0.92, -0.35, 1.08, 64, 0.06),
  ];
}
function tickStroke(x, y, s) {
  return [[x - s * 0.45, y - s * 0.05], [x - s * 0.1, y + s * 0.35], [x + s * 0.55, y - s * 0.6]];
}

// timeline of strokes with pen lifts between them: returns {pts, u, v, down} at progress k
function strokeTimeline(strokes) {
  const segs = [];
  let T = 0;
  strokes.forEach((s, i) => {
    if (i > 0) { const a = strokes[i - 1][strokes[i - 1].length - 1], b = s[0]; const d = Math.hypot(b[0] - a[0], b[1] - a[1]); segs.push({ lift: true, a, b, t0: T, t1: T + 40 + d * 0.5 }); T += 40 + d * 0.5; }
    const L = polyLen(s);
    segs.push({ lift: false, s, L, t0: T, t1: T + L }); T += L;
  });
  return { segs, T };
}
function pointOnPoly(s, d) {
  for (let i = 1; i < s.length; i++) {
    const l = Math.hypot(s[i][0] - s[i - 1][0], s[i][1] - s[i - 1][1]);
    if (d <= l || i === s.length - 1) { const k = l > 0 ? clamp(d / l) : 1; return [lerp(s[i - 1][0], s[i][0], k), lerp(s[i - 1][1], s[i][1], k)]; }
    d -= l;
  }
  return s[s.length - 1];
}
function drawPartial(g, tl, k) {
  const tt = k * tl.T;
  for (const sg of tl.segs) {
    if (sg.lift || tt <= sg.t0) continue;
    const d = Math.min(sg.L, tt - sg.t0);
    g.beginPath();
    g.moveTo(sg.s[0][0], sg.s[0][1]);
    let acc = 0;
    for (let i = 1; i < sg.s.length; i++) {
      const l = Math.hypot(sg.s[i][0] - sg.s[i - 1][0], sg.s[i][1] - sg.s[i - 1][1]);
      if (acc + l >= d) { const p = pointOnPoly(sg.s, d); g.lineTo(p[0], p[1]); break; }
      g.lineTo(sg.s[i][0], sg.s[i][1]); acc += l;
    }
    g.stroke();
  }
}
function tipOf(tl, k) {
  const tt = clamp(k) * tl.T;
  for (const sg of tl.segs) {
    if (tt > sg.t1) continue;
    const f = clamp((tt - sg.t0) / (sg.t1 - sg.t0));
    if (sg.lift) { const e = f * f * (3 - 2 * f); return { x: lerp(sg.a[0], sg.b[0], e), y: lerp(sg.a[1], sg.b[1], e), h: Math.sin(Math.PI * f) * 0.014 }; }
    const p = pointOnPoly(sg.s, f * sg.L);
    return { x: p[0], y: p[1], h: 0 };
  }
  const last = tl.segs[tl.segs.length - 1];
  const p = last.lift ? last.b : last.s[last.s.length - 1];
  return { x: p[0], y: p[1], h: 0 };
}

// red CANCELLED stamp with patchy ink, painted once
let _stamp = null;
function stampCanvas() {
  if (_stamp) return _stamp;
  const [c, g] = canvas(CW, CH);
  g.translate(CW * 0.5, CH * 0.42); g.rotate(-0.22);
  g.strokeStyle = '#c4121a'; g.lineWidth = 16; g.strokeRect(-380, -95, 760, 190);
  g.lineWidth = 5; g.strokeRect(-360, -76, 720, 152);
  g.fillStyle = '#c4121a'; g.font = 'bold 128px "Liberation Sans"'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillText('CANCELLED', 0, 8);
  g.globalCompositeOperation = 'destination-out';
  const r = rng(77);
  for (let i = 0; i < 1100; i++) { g.fillStyle = `rgba(0,0,0,${0.25 + r() * 0.55})`; g.fillRect(-390 + r() * 780, -100 + r() * 200, 3 + r() * 9, 2 + r() * 5); }
  _stamp = c;
  return c;
}

// ------------------------------------------------------------------ paper ---
const QUESTIONS = [
  ['1.  Solve for x:   3x + 7 = 22', 'x = 5'],
  ['2.  Simplify:   (2a³)(4a²)', '8a⁵'],
  ['3.  Area of a circle, r = 6 cm', '36π ≈ 113.1 cm²'],
  ['4.  Factorise:   x² − 9', '(x − 3)(x + 3)'],
  ['5.  15% of 240', '36'],
  ['6.  Solve:   2(x − 4) = x + 1', 'x = 9'],
];
const FINAL_Q = [
  ['1.  Solve:   5x − 3 = 2x + 12', 'x = 5'],
  ['2.  Expand:   (x + 4)(x − 2)', 'x² + 2x − 8'],
  ['3.  Gradient through (1,2), (4,11)', 'm = 3'],
];

export function makePaper(spec = {}) {
  const kind = spec.kind || 'test';
  const name = spec.name || 'Adam';
  const hand = spec.hand || 0; // handwriting variant
  const [c, g] = canvas(CW, CH);
  const tex = toTex(c, { aniso: 16 });
  const geo = new THREE.PlaneGeometry(PW, PH);
  geo.rotateX(-Math.PI / 2); // lies in the XZ plane, canvas top towards -Z
  const material = new THREE.MeshStandardMaterial({ map: tex, color: new THREE.Color(0.8, 0.8, 0.8), roughness: 0.92, side: THREE.FrontSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
  const meshP = new THREE.Mesh(geo, material);
  meshP.receiveShadow = true; meshP.castShadow = true;
  const group = new THREE.Group();
  group.add(meshP);
  const backG = new THREE.PlaneGeometry(PW, PH); backG.rotateX(Math.PI / 2);
  const back = new THREE.Mesh(backG, new THREE.MeshStandardMaterial({ color: new THREE.Color(0.78, 0.78, 0.76), roughness: 0.95 }));
  back.position.y = -0.0002; group.add(back);
  const qs = kind === 'final' || kind === 'retake' ? FINAL_Q : QUESTIONS;
  const qY0 = 390, qDY = kind === 'test' ? 150 : 140;
  const scoreC = [812, 250], scoreH = 110;
  const scoreTL = strokeTimeline(hundredStrokes(scoreC[0], scoreC[1], scoreH));
  const tickTLs = qs.map((q, i) => strokeTimeline([tickStroke(905, qY0 + i * qDY + 84, 46)]));
  const bonusTL = strokeTimeline([[[150, 1312], [560, 1312], [560, 1390], [150, 1390], [150, 1308]]]);
  const answerX = 150;

  // static paper (printed parts) cached once
  const [bc, bg] = canvas(CW, CH);
  (function printBase() {
    bg.fillStyle = '#f7f5ee'; bg.fillRect(0, 0, CW, CH);
    noiseFill(bg, CW, CH, 0, 7, 17 + hand, 2);
    bg.fillStyle = '#5a5a60'; bg.font = 'bold 26px "Liberation Sans"'; bg.textAlign = 'left';
    bg.fillText('WESTBROOK SCHOOL', 70, 80);
    bg.fillStyle = '#16161c'; bg.font = 'bold 50px "Liberation Sans"';
    bg.fillText(kind === 'test' ? 'MATHS — UNIT TEST' : kind === 'retake' ? 'FINAL EXAM — RETAKE' : 'FINAL EXAM', 70, 150);
    bg.font = '32px "Liberation Sans"'; bg.fillStyle = '#2a2a30';
    bg.fillText('Name:', 70, 235); bg.fillText('Class:  8B', 70, 300);
    bg.strokeStyle = '#8a8a90'; bg.lineWidth = 2;
    bg.beginPath(); bg.moveTo(170, 240); bg.lineTo(560, 240); bg.stroke();
    // score box
    bg.strokeStyle = '#2a2a30'; bg.lineWidth = 3; bg.strokeRect(640, 150, 340, 210);
    bg.font = 'bold 26px "Liberation Sans"'; bg.fillStyle = '#2a2a30'; bg.fillText('SCORE', 660, 186);
    bg.font = '34px "Liberation Sans"'; bg.fillText('/ 100', 870, 345);
    bg.fillStyle = '#16161c'; bg.font = '34px "Liberation Sans"';
    qs.forEach(([q], i) => {
      const y = qY0 + i * qDY;
      bg.fillText(q, 70, y);
      bg.strokeStyle = '#b8b8c0'; bg.lineWidth = 2;
      bg.beginPath(); bg.moveTo(120, y + 84); bg.lineTo(840, y + 84); bg.stroke();
    });
    if (kind === 'final' || kind === 'retake') {
      const y = 840;
      bg.fillStyle = '#fff6d8'; bg.fillRect(60, y, 904, 560);
      bg.strokeStyle = '#c8961e'; bg.lineWidth = 6; bg.strokeRect(60, y, 904, 560);
      bg.fillStyle = '#b07810'; bg.font = 'bold 50px "Liberation Sans"'; bg.fillText('★ BONUS QUESTION', 90, y + 70);
      bg.fillStyle = '#7a2a10'; bg.font = 'italic 28px "Liberation Serif"'; bg.fillText('(nobody has solved this one)', 590, y + 66);
      bg.fillStyle = '#16161c'; bg.font = '32px "Liberation Sans"';
      bg.fillText('A ladder 10 m long slides down a wall.', 90, y + 130);
      bg.fillText('Its foot moves at 1 m/s. How fast is the top', 90, y + 175);
      bg.fillText('falling when the foot is 6 m from the wall?', 90, y + 220);
      // a little diagram
      bg.strokeStyle = '#16161c'; bg.lineWidth = 4;
      bg.beginPath(); bg.moveTo(760, y + 250); bg.lineTo(760, y + 440); bg.lineTo(930, y + 440); bg.stroke();
      bg.beginPath(); bg.moveTo(760, y + 290); bg.lineTo(890, y + 440); bg.stroke();
      bg.font = 'italic 28px "Liberation Serif"'; bg.fillText('10 m', 830, y + 350); bg.fillText('6 m', 810, y + 475);
    }
  })();

  // handwritten answers (pencil): reveal left to right
  const hwFont = (sz) => `italic ${sz}px "Liberation Serif"`;
  const answers = qs.map(([, a]) => a);
  const bonusLines = ['x² + y² = 100  →  2x·x′ + 2y·y′ = 0', 'x = 6, y = 8, x′ = 1  →  12 + 16y′ = 0', 'y′ = −0.75 m/s'];
  function measureAll() {
    g.font = hwFont(46);
    const items = [];
    items.push({ text: name, x: 190, y: 228, w: g.measureText(name).width, size: 46, isName: true });
    answers.forEach((a, i) => items.push({ text: a, x: answerX + 20, y: qY0 + i * qDY + 74, w: g.measureText(a).width, size: 46 }));
    if (kind === 'final' || kind === 'retake') {
      g.font = hwFont(40);
      bonusLines.forEach((a, i) => items.push({ text: a, x: 120, y: 840 + 300 + i * 70 - (i === 2 ? -110 : 0) + (i === 2 ? 0 : 0), w: g.measureText(a).width, size: i === 2 ? 46 : 40, bonus: true }));
    }
    return items;
  }
  const items = measureAll();
  const nameItem = items[0];
  const ansItems = items.filter((x) => !x.isName && !x.bonus);
  const bonusItems = items.filter((x) => x.bonus);
  if (bonusItems.length) { bonusItems[2].y = 1365; bonusItems[2].x = 170; bonusItems[0].y = 1150; bonusItems[1].y = 1220; }

  function drawHand(it, k, col = '#3a3a44') {
    if (k <= 0) return;
    g.save();
    g.beginPath(); g.rect(it.x - 6, it.y - it.size, (it.w + 12) * k, it.size * 1.5); g.clip();
    g.fillStyle = col; g.font = hwFont(it.size);
    g.fillText(it.text, it.x, it.y);
    g.restore();
  }
  const red = (w) => { g.strokeStyle = 'rgba(214,18,22,0.92)'; g.lineWidth = w; g.lineCap = 'round'; g.lineJoin = 'round'; };

  let lastKey = '';
  function setState(st = {}) {
    const s = {
      name: st.name ?? 1, answers: st.answers ?? 1, ticks: st.ticks ?? 0, score: st.score ?? 0, scoreText: st.scoreText || '100',
      stamp: st.stamp ?? 0, bonus: st.bonus ?? 0, bonusBox: st.bonusBox ?? 0, smudge: st.smudge || 0,
    };
    const q = (v) => Math.round(v * 200) / 200;
    const key = [q(s.name), q(s.answers), q(s.ticks), q(s.score), s.scoreText, q(s.stamp), q(s.bonus), q(s.bonusBox)].join('|');
    if (key === lastKey) return;
    lastKey = key;
    g.drawImage(bc, 0, 0);
    drawHand(nameItem, s.name);
    // answers appear one after another as `answers` goes 0..1
    const n = ansItems.length;
    ansItems.forEach((it, i) => drawHand(it, clamp(s.answers * n - i)));
    if (bonusItems.length) {
      const nb = bonusItems.length;
      bonusItems.forEach((it, i) => drawHand(it, clamp(s.bonus * nb - i)));
      if (s.bonusBox > 0) { g.strokeStyle = '#3a3a44'; g.lineWidth = 5; g.lineCap = 'round'; drawPartial(g, bonusTL, s.bonusBox); }
    }
    red(9);
    tickTLs.forEach((tl, i) => { const k = clamp(s.ticks - i); if (k > 0) drawPartial(g, tl, k); });
    if (s.scoreText === '100') { red(11); drawPartial(g, scoreTL, s.score); }
    else if (s.score > 0) {
      g.save(); g.fillStyle = 'rgba(214,18,22,0.92)'; g.font = `italic bold 130px "Liberation Serif"`; g.textAlign = 'center';
      g.fillText(s.scoreText, scoreC[0], scoreC[1] + 48); g.restore();
      red(8); g.beginPath(); g.ellipse(scoreC[0], scoreC[1] + 5, 140, 92, -0.08, 0, Math.PI * 2); g.stroke();
    }
    if (s.stamp > 0) {
      g.save();
      g.globalAlpha = 0.88 * clamp(s.stamp * 1.5);
      g.drawImage(stampCanvas(), 0, 0);
      g.restore();
    }
    tex.needsUpdate = true;
  }
  setState({ answers: 1, name: 1 });

  // pen / pencil tip positions in paper-local metres (x right, z down the page, y up)
  const toLocal = (x, y, h = 0) => new THREE.Vector3((x / CW - 0.5) * PW, h + 0.0005, (y / CH - 0.5) * PH);
  function redTip(st) {
    if (st.scoreText === '100' && st.score > 0 && st.score < 1) { const p = tipOf(scoreTL, st.score); return toLocal(p.x, p.y, p.h); }
    const n = Math.floor(clamp(st.ticks || 0, 0, tickTLs.length - 1e-6));
    const p = tipOf(tickTLs[n], (st.ticks || 0) - n);
    return toLocal(p.x, p.y, p.h);
  }
  function scoreTip(k) { const p = tipOf(scoreTL, k); return toLocal(p.x, p.y, p.h); }
  function tickTip(k) {
    const n = Math.floor(clamp(k, 0, tickTLs.length - 1e-6));
    const p = tipOf(tickTLs[n], clamp(k - n)); return toLocal(p.x, p.y, p.h);
  }
  // pencil follows the reveal front of a handwritten line, bobbing with the letters
  function writeTip(listName, k) {
    const list = listName === 'bonus' ? bonusItems : listName === 'name' ? [nameItem] : ansItems;
    const n = list.length;
    const i = Math.min(n - 1, Math.floor(clamp(k) * n));
    const f = clamp(k * n - i);
    const it = list[i];
    const x = it.x + it.w * f;
    const y = it.y - it.size * 0.3 + Math.sin(f * it.w * 0.09) * it.size * 0.22;
    // pen lifts briefly between lines
    const h = (f < 0.04 || f > 0.97) && n > 1 ? 0.006 : 0;
    return toLocal(x, y, h);
  }
  function boxTip(k) { const p = tipOf(bonusTL, k); return toLocal(p.x, p.y, p.h); }

  return { group, mesh: meshP, setState, redTip, scoreTip, tickTip, writeTip, boxTip, toLocal, canvas: c, tex, kind };
}

// world position of a paper-local point
export function paperWorld(paper, local) {
  paper.group.updateWorldMatrix(true, false);
  return local.clone().applyMatrix4(paper.group.matrixWorld);
}
