// 60 s test: every shot is a function of time. frame(T, tg) returns the full SVG for global time tg.
import { W, H, INK, PAL, defs, finish, grade, glow, hero, zombie, crowd, caption, soundCaption, hud, watermark,
  g, rect, circle, ellipse, line, poly, path, text, ink, rng } from './lib.js';
import { aisle, at, icon, smallCaps, big, cream } from './scenes.js';

// ---------- helpers ----------
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, k) => a + (b - a) * k;
const ease = (k) => { k = clamp(k); return k * k * (3 - 2 * k); };
const easeOut = (k) => 1 - Math.pow(1 - clamp(k), 3);
const back = (k) => { k = clamp(k); const c = 1.9; return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); };
const ramp = (t, a, b) => clamp((t - a) / (b - a));
const wob = (t, seed = 0) => Math.sin(t * 1.7 + seed) * 0.6 + Math.sin(t * 3.1 + seed * 2.3) * 0.3 + Math.sin(t * 5.3 + seed * 0.7) * 0.1;
const f1 = (n) => Math.round(n * 10) / 10;
function cam(inner, { s = 1, x = 0, y = 0, cx = W / 2, cy = H / 2, r = 0 } = {}) {
  return g(inner, { transform: `translate(${f1(cx + x)} ${f1(cy + y)}) rotate(${f1(r)}) scale(${s.toFixed(4)}) translate(${-cx} ${-cy})` });
}
const blinkAt = (t, times, d = 0.14) => { for (const b of times) { const k = (t - b) / d; if (k > 0 && k < 1) return Math.sin(Math.PI * k); } return 0; };
const wrap = (inner, seed, boil) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}">${defs(seed, boil)}${inner}</svg>`;

// ---------- overlays ----------
function narratorWord(T, tg) {
  for (const L of T.voice.lines) {
    if (tg < L.start - 0.02 || tg > L.start + L.dur + 0.15) continue;
    const ws = L.words;
    for (let i = ws.length - 1; i >= 0; i--) {
      const ts = L.start + ws[i].t - 0.03;
      if (tg >= ts) {
        const te = i + 1 < ws.length ? L.start + ws[i + 1].t - 0.03 : L.start + L.dur + 0.15;
        if (tg <= te) return { w: ws[i].w.replace(/[.,!?]$/, ''), age: tg - ts };
      }
    }
  }
  return null;
}
function captions(T, tg, { y = 870 } = {}) {
  const w = narratorWord(T, tg); if (!w) return '';
  const k = 0.86 + 0.14 * easeOut(w.age / 0.08);
  return g(caption(w.w, { y }), { transform: `translate(${W / 2} ${y}) scale(${k.toFixed(3)}) translate(${-W / 2} ${-y})` });
}
function hudIn(T, tg, opts) {
  const k = back(ramp(tg, T.events.hud_in, T.events.hud_in + 0.45));
  if (k <= 0.001) return '';
  return g(hud(opts), { transform: `translate(0 ${f1((1 - k) * -170)})` });
}

// ---------- reusable props ----------
function paBox(x, y, k, on, flip) {
  let s = rect(x - 70 * k, y - 95 * k, 140 * k, 190 * k, { rx: 10 * k, fill: '#8E9196', ...ink(5) });
  for (let i = 0; i < 4; i++) s += line(x - 45 * k, y - 65 * k + i * 16 * k, x + 45 * k, y - 65 * k + i * 16 * k, { stroke: '#4B4F55', strokeWidth: 4 * k });
  s += text(x, y + 10 * k, 'PA', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 26 * k, fill: '#2C2F33', textAnchor: 'middle' });
  s += rect(x - 26 * k, y + 28 * k, 52 * k, 50 * k, { rx: 6 * k, fill: '#3A3D42', ...ink(4) });
  const ang = lerp(-28, 28, flip);
  s += g(rect(x - 7 * k, y + 22 * k, 14 * k, 34 * k, { rx: 5 * k, fill: '#D9D4C8', ...ink(3) }), { transform: `rotate(${f1(ang)} ${f1(x)} ${f1(y + 53 * k)})` });
  s += circle(x + 46 * k, y + 52 * k, 9 * k, { fill: on ? '#FF4B3A' : '#5A2A26', ...ink(3) });
  if (on) s += glow(x + 46 * k, y + 52 * k, 26 * k, '#FF4B3A', 0.8);
  return s;
}
const sleeve = (d) => path(d, { fill: PAL.jacket, ...ink(7) });
const mitt = (cx, cy, rot, k = 1) => g(path(`M${-60 * k} ${-30 * k} C${-60 * k} ${-90 * k} ${50 * k} ${-95 * k} ${60 * k} ${-35 * k} L${62 * k} ${35 * k} C${50 * k} ${80 * k} ${-55 * k} ${80 * k} ${-60 * k} ${30 * k} Z`, { fill: PAL.skin, ...ink(7) })
  + path(`M${-60 * k} ${-5 * k} C${-110 * k} ${-20 * k} ${-115 * k} ${-75 * k} ${-75 * k} ${-70 * k}`, { fill: PAL.skin, ...ink(7) }), { transform: `translate(${f1(cx)} ${f1(cy)}) rotate(${f1(rot)})` });
const letterbox = (label = true) => rect(0, 0, W, 130, { fill: '#000' }) + rect(0, H - 130, W, 130, { fill: '#000' })
  + (label ? text(60, 82, 'POV', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 30, fill: '#E8E1D2', letterSpacing: 6, opacity: 0.85 }) + circle(150, 72, 10, { fill: '#D65632' }) : '');
const nightTint = (op = 0.82) => rect(0, 0, W, H, { fill: '#1F2940', opacity: op, style: 'mix-blend-mode:multiply' });
function beam(from, to, spread = 0.2, op = 0.5, pool = 1, poolOp = 1) {
  const a = Math.atan2(to[1] - from[1], to[0] - from[0]), d = Math.hypot(to[0] - from[0], to[1] - from[1]) * 1.25;
  const far = (o) => [from[0] + Math.cos(a + o) * d, from[1] + Math.sin(a + o) * d];
  return poly([from, far(-spread), far(spread)], { fill: 'url(#beam)', style: 'mix-blend-mode:screen', opacity: op })
    + ellipse(to[0], to[1], 170 * pool, 140 * pool, { fill: '#FFF2C4', opacity: (0.55 * poolOp).toFixed(2), filter: 'url(#soft)', style: 'mix-blend-mode:screen' })
    + ellipse(to[0], to[1], 90 * pool, 80 * pool, { fill: '#FFF2C4', opacity: (0.3 * poolOp).toFixed(2), filter: 'url(#softS)', style: 'mix-blend-mode:screen' });
}
const exitSign = () => glow(960, 395, 90, '#7CFF9A', 0.5) + rect(925, 380, 70, 26, { fill: '#3DBE6A', stroke: INK, strokeWidth: 2 }) + text(960, 400, 'EXIT', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 18, fill: '#EFFFF2', textAnchor: 'middle' });
let AISLE = null; const aisleNight = () => (AISLE ||= aisle({ night: true, seed: 5 }));

// ---------- shots ----------
const SHOTS = {};

SHOTS.pov_open = (T, tg, lt) => {
  const E = T.events, A = aisleNight();
  let s = A.s;
  // the dead: enter the far end after the PA starts, walk toward the speaker, stop after the click
  const zs = [[1030, 'cashier', 0.0, 12], [830, 'suit', 0.5, -8], [1230, 'shopper', 0.9, 6]];
  let nearFace = [1020, 560];
  zs.forEach(([x, o, delay, tl], i) => {
    const kIn = ramp(lt, E.steps_start + delay, E.steps_start + delay + 1.2);
    if (kIn <= 0) return;
    let Zd = lerp(4.6, 1.15 + i * 0.35, ease(ramp(lt, E.steps_start + delay, E.steps_stop)));
    if (i === 0) Zd -= 0.4 * ease(ramp(lt, E.last_step - 0.1, E.last_step + 0.35));   // one more step
    if (i === 0) { const q0 = at(A, x, Zd); nearFace = [q0.x + 10, q0.y - 5.15 * 60 * 1.4 * q0.k]; }
    const q = at(A, x, Zd);
    const walk = lt < E.steps_stop ? Math.sin(lt * 5.5 + i) * 5 : 0;
    s += g(zombie({ x: q.x, y: q.y, s: 1.4 * q.k, outfit: o, tilt: tl + walk, look: -0.4 + 0.3 * i, sway: walk * 0.4 }), { opacity: f1(kIn * 10) / 10 });
  });
  s += exitSign();
  // ceiling speaker glows while the PA talks
  const paOn = lt > E.pa_start - 0.2 && lt < E.pa_cut;
  s += ellipse(700, 170, 60, 22, { fill: '#C8C8C0', ...ink(5) }) + ellipse(700, 170, 38, 12, { fill: '#555', opacity: 0.6 });
  s += nightTint(0.8);
  if (paOn) {
    s += glow(700, 180, 80, '#FFB866', 0.55 + 0.15 * Math.sin(lt * 20));
    for (let r = 0; r < 3; r++) s += path(`M${640 - r * 30} ${215 + r * 22} Q700 ${255 + r * 30} ${760 + r * 30} ${215 + r * 22}`, { fill: 'none', stroke: '#FFB866', strokeWidth: 5, opacity: 0.6 - r * 0.15 });
  }
  // flashlight: explore the shelves, then snap to the far end, then onto the nearest one
  let tx = lt < 3.4 ? lerp(520, 1450, ease(lt / 3.4)) : lerp(1450, nearFace[0], ease(ramp(lt, 3.4, 4.1)));
  let ty = lt < 3.4 ? 520 + 60 * Math.sin(lt * 1.3) : lerp(520, nearFace[1] + 40, ease(ramp(lt, 3.4, 4.1)));
  if (lt > 4.1) { tx = nearFace[0]; ty = nearFace[1] + 40 - 40 * ease(ramp(lt, E.last_step, E.last_step + 0.4)); }
  const tremble = lt > E.switch ? 6 : 2;
  const to = [tx + wob(lt * 4, 1) * tremble, ty + wob(lt * 4, 2) * tremble];
  const lens = [1250 + wob(lt, 3) * 10, 830 + wob(lt, 4) * 8];
  s += beam(lens, to, 0.16, 0.38, 1.2, 0.45);
  // left hand reaches the PA box on the shelf end and flips it off
  const flip = ramp(lt, E.switch - 0.05, E.switch + 0.06);
  let fg = paBox(330, 600, 1.25, lt < E.switch, flip);
  const reach = ease(ramp(lt, E.switch - 1.3, E.switch - 0.1));
  const hx = lerp(150, 330, reach), hy = lerp(1150, 700, reach);
  fg += sleeve(`M-80 1080 L${f1(hx - 70)} ${f1(hy + 40)} L${f1(hx + 60)} ${f1(hy + 110)} L120 1080 Z`) + mitt(hx, hy + 40, -20, 0.95);
  // right hand + flashlight
  const ang = Math.atan2(to[1] - lens[1], to[0] - lens[0]) * 180 / Math.PI;
  fg += sleeve(`M1700 1080 L${f1(lens[0] + 80)} ${f1(lens[1] + 70)} L${f1(lens[0] + 190)} ${f1(lens[1] - 30)} L1880 1080 Z`);
  fg += g(rect(0, -32, 230, 64, { rx: 20, fill: '#2C2C2C', ...ink(6) }) + rect(-28, -42, 52, 84, { rx: 12, fill: '#C9A43A', ...ink(6) }) + ellipse(-30, 0, 10, 30, { fill: '#FFF6D8' }), { transform: `translate(${f1(lens[0])} ${f1(lens[1])}) rotate(${f1(ang + 180)}) translate(-24 0) rotate(180) translate(-206 0)` });
  fg += mitt(lens[0] + 120, lens[1] + 30, -15, 1.0);
  s += g(fg, { filter: 'url(#wobbleSoft)' });
  s += `<radialGradient id="povDark" cx="0.53" cy="0.52" r="0.62"><stop offset="0.3" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.75"/></radialGradient>` + rect(0, 0, W, H, { fill: 'url(#povDark)' });
  const shake = 1 + (lt > E.steps_start ? 1.5 : 0) - (lt > E.switch ? 1.2 : 0);
  s = cam(s, { s: 1.06 + 0.02 * ease(lt / 9.5), x: wob(lt * 0.9, 5) * 7 * shake, y: wob(lt * 0.8, 6) * 5 * shake, r: wob(lt * 0.5, 7) * 0.4 });
  // POV grammar: letterbox, no HUD, sound captions
  s += letterbox();
  const pa = T.voice.pa; let said = [];
  for (const w of pa.words) if (lt >= E.pa_start + w.t - 0.03 && lt < E.pa_cut + 0.6) said.push(w.w);
  if (said.length) s += text(W / 2, H - 82, `“${said.join(' ')}${lt > E.pa_cut ? '—' : ''}”`, { fontFamily: 'Rubik', fontStyle: 'italic', fontWeight: 500, fontSize: 34, fill: '#F2A73B', textAnchor: 'middle' });
  const sc = [[0.3, 1.6, 'fridges humming'], [1.6, 2.75, 'PA chime'], [E.steps_start + 0.5, E.switch, 'footsteps. a lot of them.'], [E.switch, E.switch + 0.8, 'click'],
    [E.switch + 0.8, E.last_step, 'the footsteps stop'], [E.last_step, 9.55, 'one more step. close.']];
  for (const [a, b, l] of sc) if (lt >= a && lt < b) s += soundCaption(l, { y: said.length && lt < E.pa_cut + 0.6 ? H - 36 : H - 62 });
  return s + finish({ vignette: 0.6, grain: 0.16 });
};

function aisleScene(T, tg, lt, { pose = 'flashlight', hold = 'flashlight', expr = 'scared', look = 0.5, zLook = -0.5, zSnap = 0, blink = 0, noise = 1, push = [1, 1.06], hudOn = false, time = '2:14 AM', flicker = 0, paBoxOn = false }) {
  const A = aisleNight(); let s = A.s;
  const zs = [[1250, 2.6, 'cashier', 12], [1060, 3.4, 'suit', -6], [760, 3.9, 'shopper', 8], [1400, 4.6, 'guard', -10]];
  zs.forEach(([x, Zd, o, tl], i) => {
    const q = at(A, x, Zd);
    s += zombie({ x: q.x, y: q.y, s: 1.4 * q.k, outfit: o, tilt: tl + 3 * Math.sin(tg * 0.9 + i) + zSnap * 18, look: lerp(zLook, 0.9, zSnap), sway: 1.5 * Math.sin(tg * 0.7 + i * 2) });
  });
  const h = at(A, 640, 0.05);
  let H_ = '';
  if (paBoxOn) H_ += paBox(450, 650, 0.9, false, 1);
  const hu = 60 * 1.45 * h.k;
  const x = paBoxOn ? 590 : h.x;
  if (hold === 'flashlight') {
    const hx1 = x + 1.45 * hu, hy1 = h.y - 3.45 * hu, T1 = [990, 500];
    H_ += hero({ x, y: h.y, s: 1.45 * h.k, pose, expr, hold, aim: Math.atan2(T1[1] - hy1, T1[0] - hx1) * 180 / Math.PI, facing: 1, look, blink, breathe: 0.006 * Math.sin(tg * 2.2) });
  } else H_ += hero({ x, y: h.y, s: 1.45 * h.k, pose, expr, facing: -1, look, blink, breathe: 0.006 * Math.sin(tg * 2.2) });
  s += H_;
  s += nightTint(0.86) + exitSign();
  if (hold === 'flashlight' && flicker < 0.5) {
    const hx0 = x + 1.45 * hu, hy0 = h.y - 3.45 * hu, Tt = [990, 500], a = Math.atan2(Tt[1] - hy0, Tt[0] - hx0);
    s += beam([hx0 + Math.cos(a) * 0.7 * hu, hy0 + Math.sin(a) * 0.7 * hu], Tt, 0.2, 0.6);
    s += ellipse(x + 60, h.y - 300, 260, 340, { fill: '#FFF2C4', opacity: 0.16, filter: 'url(#soft)', style: 'mix-blend-mode:screen' });
  }
  s = cam(s, { s: lerp(push[0], push[1], ease(lt / 4.5)), cx: 980, cy: 520 });
  if (flicker >= 0.5) s += rect(0, 0, W, H, { fill: '#05070C', opacity: 0.75 });
  if (hudOn) s += hud({ theme: 'price', day: 0, time, noise, place: 'FRESHWAY · AISLE 7' });
  return s;
}

SHOTS.aisle_frozen = (T, tg, lt) => aisleScene(T, tg, lt, { pose: 'reach', hold: null, expr: 'scared', look: 0.45, blink: blinkAt(lt, [1.6]), push: [1.0, 1.07], paBoxOn: true }) + captions(T, tg) + watermark() + finish();

function zombieClose(T, tg, lt, { look, tiltK = 0, shake = 0, ring = 0 }) {
  let s = rect(0, 0, W, H, { fill: '#2E3646' });
  for (let i = 0; i < 4; i++) s += rect(160 + i * 410, 120, 380, 760, { fill: '#4A6578', ...ink(5) }) + rect(180 + i * 410, 150, 340, 120, { fill: '#6E8FA3', opacity: 0.5 });
  s += rect(0, 860, W, 220, { fill: '#3B4048' });
  s += glow(960, 140, 220, '#7CFF9A', 0.45) + rect(880, 95, 160, 56, { fill: '#3DBE6A', ...ink(3) }) + text(960, 136, 'EXIT', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 38, fill: '#EFFFF2', textAnchor: 'middle' });
  s = g(s, { filter: 'url(#wobble)' });
  const zs = [[560, 1150, 'shopper', -10, 1.7], [1000, 1180, 'cashier', 8, 1.9], [1440, 1170, 'guard', -6, 1.65]];
  zs.forEach(([x, y, o, tl, k], i) => {
    const lag = i * 0.12;
    s += zombie({ x, y, s: k, outfit: o, tilt: tl + tiltK * (i % 2 ? -16 : 16) + 2 * Math.sin(tg + i), look: look(lt - lag), sway: 1.2 * Math.sin(tg * 0.8 + i) });
  });
  s += rect(0, 0, W, H, { fill: '#1F2940', opacity: 0.55, style: 'mix-blend-mode:multiply' });
  s += glow(960, 120, 300, '#7CFF9A', 0.25);
  if (ring) {
    const k = easeOut(ring);
    s += g(text(1650, 330, 'RRRING!', { fontFamily: 'Bangers, Impact', fontSize: 120, fill: '#FFE27A', stroke: '#2B1D21', strokeWidth: 10, paintOrder: 'stroke', textAnchor: 'middle' }),
      { transform: `translate(1650 300) rotate(${f1(-8 + 4 * Math.sin(tg * 40))}) scale(${(0.6 + 0.4 * k).toFixed(3)}) translate(-1650 -300)` });
  }
  return cam(s, { s: 1.0 + 0.05 * ease(lt / 2.5), x: shake * wob(tg * 9, 1) * 12, y: shake * wob(tg * 9, 2) * 8 });
}
SHOTS.zombies_turn = (T, tg, lt) => zombieClose(T, tg, lt, { look: (t) => lerp(-0.75, 0.05, ease(ramp(t, 0.35, 1.9))) }) + captions(T, tg) + watermark() + finish({ vignette: 1 });

function heroClose(T, tg, lt, { expr = 'scared', look = 0, blink = 0, tilt = 0, s = 1, shake = 0, warm = false, flicker = 0, bgNight = true }) {
  const A = aisleNight();
  let bg = g(A.s, { filter: 'url(#softS)' });
  bg += nightTint(warm ? 0.7 : 0.88);
  let ch = hero({ x: 960, y: 1340, s: 2.6, pose: expr === 'scared' ? 'scared' : 'stand', expr, facing: 1, look, blink, tilt, breathe: 0.005 * Math.sin(tg * 2.4) });
  let sc = bg + ch;
  sc += glow(640, 380, 260, warm ? '#FFD9A0' : '#FFF2C4', warm ? 0.28 : 0.1);
  sc = cam(sc, { s, cx: 960, cy: 520, x: shake * wob(tg * 10, 3) * 14, y: shake * wob(tg * 10, 4) * 10 });
  if (flicker) sc += rect(0, 0, W, H, { fill: '#05070C', opacity: 0.78 });
  return sc;
}
SHOTS.hero_where = (T, tg, lt) => {
  const b = T.events.boom_where - T.shots.find((x) => x.name === 'hero_where').start;
  const look = lt < 0.5 ? -0.35 : lt < 1.0 ? 0.35 : -0.05;
  const kick = Math.max(0, 1 - Math.abs(lt - b) / 0.35) * (lt > b ? 1 : 0);
  return heroClose(T, tg, lt, { expr: 'scared', look, blink: blinkAt(lt, [0.15]), s: 1 + 0.06 * ease(ramp(lt, b - 0.05, b + 0.15)), shake: kick * 1.5 }) + captions(T, tg) + watermark() + finish({ vignette: 1 });
};

SHOTS.exterior = (T, tg, lt) => {
  const r = rng(31);
  let s = rect(0, 0, W, 560, { fill: '#2E3A55' });
  for (let i = 0; i < 70; i++) s += circle(r() * W, r() * 300, 1 + r() * 2, { fill: '#F3EBDD', opacity: 0.5 + r() * 0.5 });
  s += circle(1620, 150, 52, { fill: '#F1E9D2' }) + circle(1600, 140, 52, { fill: '#2E3A55', opacity: 0.25 });
  for (let x = 0; x < W; x += 110) { const h = 120 + r() * 200; s += rect(x, 560 - h, 100, h, { fill: '#1E2638', ...ink(3) }); }
  s += rect(160, 260, 1600, 470, { fill: '#C9BFA7', ...ink(6) }) + rect(160, 260, 1600, 110, { fill: '#3E6E5A', ...ink(6) });
  s += text(960, 340, 'FRESHWAY', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 84, fill: '#F5EFE0', textAnchor: 'middle', letterSpacing: 8 });
  s += rect(1430, 290, 270, 54, { rx: 8, fill: '#B5452F', ...ink(4) }) + text(1565, 327, 'OPEN 24 HOURS', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 24, fill: '#FFF', textAnchor: 'middle', letterSpacing: 1 });
  const rattle = 2 * Math.sin(tg * 37) * (Math.sin(tg * 1.3) > 0.6 ? 1 : 0);
  let sh = rect(260, 400, 1400, 330, { fill: '#9C988C', ...ink(6) });
  for (let y = 412; y < 730; y += 16) sh += path(`M260 ${y} Q960 ${y + 16 * (1 - Math.abs(y - 560) / 170)} 1660 ${y}`, { fill: 'none', stroke: '#6E6A60', strokeWidth: 3 });
  s += g(sh, { transform: `translate(0 ${f1(rattle)})` });
  s += rect(0, 730, W, 350, { fill: '#4A4E58' });
  for (let x = -200; x < W + 200; x += 260) s += line(x, 1080, x + 120, 760, { stroke: '#E9E2C8', strokeWidth: 6, opacity: 0.5 });
  s += rect(1600, 840, 260, 120, { rx: 30, fill: '#7A3B33', ...ink(6) }) + rect(1640, 800, 170, 60, { rx: 20, fill: '#9FB3C2', ...ink(5) }) + circle(1650, 965, 30, { fill: INK }) + circle(1810, 965, 30, { fill: INK });
  s = g(s, { filter: 'url(#wobble)' });
  s += crowd({ x0: 280, x1: 1640, y: 760, rows: 3, n: 24, s: 0.48, seed: 7, spread: 26, t: tg, lean: 3 });
  s += crowd({ x0: 120, x1: 1500, y: 900, rows: 2, n: 14, s: 0.62, seed: 8, spread: 24, t: tg + 2, lean: 2 });
  s += grade('night');
  s += line(80, 1080, 80, 520, { stroke: INK, strokeWidth: 14 }) + rect(60, 506, 90, 22, { fill: '#FFB866', ...ink(4) });
  s += glow(105, 535, 55, '#FFB866', 0.75) + ellipse(240, 1010, 300, 80, { fill: '#FFB866', opacity: 0.22, filter: 'url(#soft)', style: 'mix-blend-mode:screen' });
  s += glow(1565, 316, 60, '#FF6A4A', 0.4 + 0.1 * Math.sin(tg * 3));
  s = cam(s, { s: 1.08, x: lerp(40, -40, ease(lt / 5)), y: 10 });
  return s + hudIn(T, tg, { theme: 'price', day: 0, time: '2:14 AM', noise: 0, place: 'FRESHWAY · PARKING LOT' }) + captions(T, tg) + watermark() + finish({ vignette: 1 });
};

SHOTS.shutter_hands = (T, tg, lt) => {
  let s = rect(0, 0, W, H, { fill: '#9C988C' });
  const vib = (Math.sin(tg * 1.9) > 0.3 ? 3 : 0.6) * Math.sin(tg * 41);
  let sh = '';
  for (let y = 0; y < 760; y += 30) sh += path(`M0 ${y} Q960 ${y + 26 * Math.sin(y / 120)} ${W} ${y}`, { fill: 'none', stroke: '#6E6A60', strokeWidth: 5 });
  sh += path('M0 760 Q960 700 1920 770 L1920 800 Q960 740 0 790 Z', { fill: '#5E5A52', ...ink(6) });
  s += g(sh, { transform: `translate(0 ${f1(vib)})` });
  s += rect(0, 790, W, 290, { fill: '#CFC2A6' });
  for (let x = -100; x < W + 100; x += 160) s += line(x, 790, x + (x - 960) * 0.5, 1080, { stroke: '#BDB096', strokeWidth: 3 });
  s = g(s, { filter: 'url(#wobble)' });
  const hand = (x, rot, k, ph) => {
    const dy = 40 + 30 * Math.sin(tg * 2.1 + ph), dx = 18 * Math.sin(tg * 3.3 + ph * 2), rr = rot + 7 * Math.sin(tg * 2.7 + ph);
    const fing = `M${-30 * k} ${110 * k} l${-14 * k} ${46 * k} M0 ${118 * k} l${-4 * k} ${52 * k} M${30 * k} ${112 * k} l${8 * k} ${48 * k} M${55 * k} ${95 * k} l${22 * k} ${40 * k}`;
    return g(path(`M0 0 c${-40 * k} ${20 * k} ${-50 * k} ${70 * k} ${-30 * k} ${110 * k} c${20 * k} ${30 * k} ${70 * k} ${30 * k} ${90 * k} ${-5 * k} c${20 * k} ${-40 * k} ${10 * k} ${-90 * k} ${-60 * k} ${-105 * k}`, { fill: PAL.zSkin, ...ink(7) })
      + path(fing, { fill: 'none', stroke: PAL.zSkin, strokeWidth: 26 * k, strokeLinecap: 'round' }) + path(fing, { fill: 'none', stroke: INK, strokeWidth: 4, strokeLinecap: 'round', opacity: 0.6 }),
      { transform: `translate(${f1(x + dx)} ${f1(730 + dy)}) rotate(${f1(rr)})`, filter: 'url(#wobbleSoft)' });
  };
  [[260, -10, 0.9, 0], [560, 8, 1, 1.3], [900, -4, 1.05, 2.2], [1300, -6, 0.85, 3.1], [1640, 12, 0.95, 4.4]].forEach((a) => { s += hand(...a); });
  s += grade('night') + rect(0, 0, W, 700, { fill: '#10141F', opacity: 0.35, style: 'mix-blend-mode:multiply' }) + ellipse(960, 785, 1000, 55, { fill: '#FFB866', opacity: 0.3, filter: 'url(#soft)', style: 'mix-blend-mode:screen' });
  s = cam(s, { s: lerp(1.04, 1.12, ease(lt / 3.7)), cy: 760 });
  return s + hud({ theme: 'price', day: 0, time: '2:14 AM', noise: 0, place: 'FRESHWAY · FRONT' }) + captions(T, tg) + watermark() + finish({ vignette: 1 });
};

SHOTS.gary = (T, tg, lt) => {
  const A = aisleNight(); let s = g(A.s, { filter: 'url(#softS)' });
  const x = 900, y = 1150, k = 2.3, u = 60 * k;
  const cx = x + 0.1 * u, top = y - 4.2 * u;
  const tag = rect(cx + 0.08 * u, top + 0.5 * u, 0.95 * u, 0.46 * u, { rx: 10, fill: '#FBF6EA', ...ink(5) })
    + text(cx + 0.555 * u, top + 0.75 * u, 'GARY', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 0.22 * u, fill: INK, textAnchor: 'middle' })
    + text(cx + 0.555 * u, top + 0.89 * u, 'MANAGER', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 0.1 * u, fill: '#B5452F', textAnchor: 'middle', letterSpacing: 2 });
  const badge = circle(cx - 0.36 * u, top + 1.25 * u, 0.2 * u, { fill: PAL.yellow, ...ink(4) })
    + text(cx - 0.36 * u, top + 1.22 * u, 'ASK ME', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 0.055 * u, fill: INK, textAnchor: 'middle' })
    + text(cx - 0.36 * u, top + 1.31 * u, 'ABOUT DEALS', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 0.04 * u, fill: INK, textAnchor: 'middle' });
  const clip = g(rect(-0.32 * u, -0.45 * u, 0.64 * u, 0.86 * u, { rx: 6, fill: '#B58759', ...ink(5) }) + rect(-0.26 * u, -0.32 * u, 0.52 * u, 0.68 * u, { fill: '#F7F2E6', ...ink(3) }) + rect(-0.12 * u, -0.52 * u, 0.24 * u, 0.12 * u, { fill: '#8A8F96', ...ink(3) }), { transform: `translate(${f1(x + 0.85 * u)} ${f1(y - 2.4 * u)}) rotate(-8)` });
  s += zombie({ x, y, s: k, outfit: 'suit', tilt: -10 + 5 * Math.sin(tg * 0.8), look: 0.15, sway: 2 * Math.sin(tg * 0.6), extra: tag + badge + clip });
  s = g(A.s, { filter: 'url(#softS)' }) + nightTint(0.85) + s.slice(g(A.s, { filter: 'url(#softS)' }).length);
  s += beam([120, 1080], [1000, 520], 0.24, 0.3, 1.9, 0.38);
  s = cam(s, { s: lerp(1.0, 1.08, ease(lt / 3.4)), cx: 980, cy: 480 });
  return s + hud({ theme: 'price', day: 0, time: '2:15 AM', noise: 1, place: 'FRESHWAY · AISLE 7' }) + captions(T, tg) + watermark() + finish({ vignette: 1 });
};

SHOTS.hero_deadpan = (T, tg, lt) => {
  const st = T.events.pizz_sting - T.shots.find((x) => x.name === 'hero_deadpan').start;
  const look = lerp(-0.45, 0.0, ease(ramp(lt, st - 0.05, st + 0.1)));
  return heroClose(T, tg, lt, { expr: 'neutral', look, blink: blinkAt(lt, [0.9, st + 0.55], 0.18), warm: true, s: 1.0 + 0.03 * ease(lt / 2.7) })
    + hud({ theme: 'price', day: 0, time: '2:15 AM', noise: 1, place: 'FRESHWAY · AISLE 7' }) + captions(T, tg) + watermark() + finish({ vignette: 0.9 });
};

SHOTS.counting = (T, tg, lt) => {
  const A = aisleNight(); let s = g(A.s, { filter: 'url(#softS)' });
  // stacked cans, upturned crate, lantern
  const r = rng(77); let cans = '';
  for (let row = 0; row < 4; row++) for (let i = 0; i < 6 - row; i++) {
    const x = 1180 + i * 92 + row * 46, y = 1000 - row * 104;
    cans += rect(x, y - 100, 84, 100, { rx: 10, fill: [PAL.red, PAL.yellow, PAL.green][Math.floor(r() * 3)], ...ink(5) }) + rect(x, y - 68, 84, 36, { fill: '#F3EEDF', ...ink(3) });
  }
  s += g(cans, { filter: 'url(#wobbleSoft)' });
  s += g(rect(560, 900, 300, 150, { fill: '#B58759', ...ink(6) }) + line(560, 950, 860, 950, ink(4)) + line(560, 1000, 860, 1000, ink(4)), { filter: 'url(#wobbleSoft)' });
  const lx = 980, ly = 1010, fl = 0.9 + 0.1 * Math.sin(tg * 13) * Math.sin(tg * 7);
  s += g(rect(lx - 40, ly - 110, 80, 110, { rx: 12, fill: '#2E2E2E', ...ink(5) }) + rect(lx - 28, ly - 95, 56, 70, { rx: 8, fill: '#FFE7A8', ...ink(3) }) + path(`M${lx - 30} ${ly - 110} q30 -40 60 0`, { fill: 'none', ...ink(5) }), { filter: 'url(#wobbleSoft)' });
  const clip = g(rect(-55, -75, 110, 150, { rx: 8, fill: '#B58759', ...ink(5) }) + rect(-45, -58, 90, 118, { fill: '#F7F2E6', ...ink(3) }) + line(-32, -30, 30, -30, { stroke: '#8E8576', strokeWidth: 3 }) + line(-32, -10, 22, -10, { stroke: '#8E8576', strokeWidth: 3 }) + line(-32, 10, 30, 10, { stroke: '#8E8576', strokeWidth: 3 }), { transform: 'translate(905 735) rotate(-14)' });
  s += hero({ x: 710, y: 1012, s: 1.25, pose: 'crouch', expr: 'neutral', facing: 1, look: 0.55, tilt: 6, blink: blinkAt(lt, [1.8, 3.6]), breathe: 0.006 * Math.sin(tg * 1.8), extra: clip });
  s += rect(0, 0, W, H, { fill: '#2A2A3A', opacity: 0.5, style: 'mix-blend-mode:multiply' });
  s += glow(lx, ly - 60, 330 * fl, '#FFC97A', 0.55) + glow(lx, ly - 60, 120, '#FFE7A8', 0.6);
  s = cam(s, { s: lerp(1.0, 1.06, ease(lt / 4.1)), cx: 900, cy: 760 });
  return s + hud({ theme: 'price', day: 0, time: '2:20 AM', noise: 0, place: 'FRESHWAY · AISLE 7' }) + captions(T, tg) + watermark() + finish({ vignette: 0.9 });
};

SHOTS.inventory = (T, tg, lt) => {
  const E = T.events; let s = cream();
  s += smallCaps(W / 2, 150, 'SUPPLIES  ·  DAY 0', 40, INK);
  const row = (y, label, value, items, t0, color = INK, stamp = '') => {
    const k = back(ramp(tg, t0 - 0.12, t0 + 0.25)); if (k <= 0.001) return '';
    let o = text(420, y, label, { fontFamily: 'Rubik', fontWeight: 700, fontSize: 34, fill: '#6B5F55' }) + text(1500, y, value, { fontFamily: 'Rubik', fontWeight: 900, fontSize: 56, fill: color, textAnchor: 'end' });
    items.forEach((it, i) => { const kk = back(ramp(tg, t0 + i * 0.04, t0 + i * 0.04 + 0.25)); if (kk > 0.01) o += g(it, { transform: `translate(${450 + i * 105} ${y + 110}) scale(${kk.toFixed(3)})` }); });
    o += stamp;
    return g(o, { transform: `translate(0 ${f1((1 - k) * 30)})`, opacity: clamp(k * 1.5).toFixed(2) });
  };
  const pr = E.problem_hit;
  const check = tg > pr ? g(path('M0 0 l20 22 l40 -48', { fill: 'none', stroke: '#2F7A4F', strokeWidth: 12, strokeLinecap: 'round', strokeLinejoin: 'round' }), { transform: `translate(1530 ${250 - 40}) scale(${back(ramp(tg, pr, pr + 0.3)).toFixed(3)})` }) : '';
  const cansIt = Array.from({ length: 10 }, (_, i) => icon.can(0, 0, 0.6, [PAL.red, PAL.yellow, PAL.green][i % 3]));
  const waterIt = Array.from({ length: 10 }, (_, i) => g(icon.water(0, 0, 0.55), { opacity: i < 7 ? 1 : 0.25 }));
  const battery = (full) => g(rect(-26, -50, 52, 100, { rx: 8, fill: '#F2F0EA', ...ink(5) }) + rect(-10, -62, 20, 14, { fill: '#2E2E2E', ...ink(3) }) + rect(-18, 50 - 8 - 84 * full, 36, 84 * full, { fill: full < 0.3 ? '#D65632' : '#7FB069' }), { filter: 'url(#wobbleSoft)' });
  const pulse = tg > pr ? 0.6 + 0.4 * Math.sin((tg - pr) * 9) : 1;
  const battIt = [battery(0.22), battery(0.12)].map((b) => g(b, { opacity: pulse.toFixed(2) }));
  s += row(250, 'Food', '9,000 cans', cansIt, E.item_cans, INK, check);
  s += row(520, 'Water', '38 gal', waterIt, E.item_water);
  s += row(790, 'Batteries', '2', battIt, E.item_batt, tg > pr ? '#D65632' : INK);
  s = cam(s, { s: lerp(1.0, 1.03, ease(ramp(tg, E.item_cans - 0.5, pr + 1.5))) });
  return s + captions(T, tg, { y: 1030 }) + finish({ vignette: 0.5, grain: 0.1 });
};

SHOTS.rule = (T, tg, lt) => {
  const E = T.events, L = T.voice.lines.find((l) => l.id === 'L11');
  const wt = (w) => L.start + L.words.find((x) => x.w.toLowerCase().replace(/[.,]/g, '') === w).t;
  let s = rect(0, 0, W, H, { fill: PAL.card });
  const k = ramp(tg, E.rule_slam - 0.1, E.rule_slam + 0.08), sc = k < 1 ? lerp(1.8, 1, k) : 1 + 0.04 * Math.exp(-(tg - E.rule_slam) * 8) * Math.sin((tg - E.rule_slam) * 40);
  s += g(g(rect(W / 2 - 150, 290, 300, 76, { fill: PAL.tag }) + text(W / 2, 346, 'RULE 1', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 52, fill: PAL.card, textAnchor: 'middle', letterSpacing: 4 }), { transform: `rotate(-3 ${W / 2} 330)` }),
    { transform: `translate(${W / 2} 330) scale(${sc.toFixed(3)}) translate(${-W / 2} -330)`, opacity: clamp(k * 3).toFixed(2) });
  const l1 = back(ramp(tg, wt('hear') - 0.25, wt('hear') + 0.05)), l2 = back(ramp(tg, wt('see') - 0.35, wt('see') + 0.05));
  if (l1 > 0.01) s += g(big(W / 2, 560, 'THEY HEAR.', 130, '#F3EBDD'), { opacity: clamp(l1).toFixed(2), transform: `translate(0 ${f1((1 - l1) * 30)})` });
  if (l2 > 0.01) s += g(big(W / 2, 720, "THEY DON'T SEE.", 130, '#F3EBDD'), { opacity: clamp(l2).toFixed(2), transform: `translate(0 ${f1((1 - l2) * 30)})` });
  const hb = Math.exp(-((tg - E.heart_start) % 0.9) * 6);
  s += g(icon.ear(W / 2 - 40, 880, 0.8), { transform: `translate(${W / 2} 880) scale(${(1 + 0.06 * hb).toFixed(3)}) translate(${-W / 2} -880)` });
  return s + captions(T, tg, { y: 1020 }) + finish({ vignette: 0.9, grain: 0.14 });
};

SHOTS.aisle_alarm = (T, tg, lt) => {
  const E = T.events;
  const noise = tg > E.ring ? 5 : 1;
  return aisleScene(T, tg, lt, { pose: 'flashlight', hold: 'flashlight', expr: 'worried', look: 0.5, blink: blinkAt(lt, [1.2, 3.3]), noise, push: [1.0, 1.1], hudOn: true, time: '2:31 AM' })
    + captions(T, tg) + watermark() + finish();
};
SHOTS.zombies_snap = (T, tg, lt) => {
  const s = zombieClose(T, tg, lt, { look: (t) => lerp(0.05, 0.95, easeOut(ramp(t, 0.0, 0.14))), tiltK: easeOut(ramp(lt, 0, 0.14)), shake: 0.8, ring: ramp(lt, 0, 0.12) });
  const blinkRed = Math.sin(tg * 18) > 0;
  return s + hud({ theme: 'price', day: 0, time: '2:31 AM', noise: blinkRed ? 5 : 4, place: 'FRESHWAY · AISLE 7' }) + captions(T, tg) + watermark() + finish({ vignette: 1 });
};
SHOTS.hero_alarm = (T, tg, lt) => {
  const E = T.events, f = [E.flicker1, E.flicker2].some((x) => tg > x && tg < x + 0.09);
  const look = lerp(0.0, 0.6, ease(ramp(lt, 0.3, 1.6)));
  return heroClose(T, tg, lt, { expr: 'scared', look, blink: 0, s: lerp(1.0, 1.2, ease(lt / 2.3)), shake: 0.25, flicker: f ? 1 : 0 })
    + hud({ theme: 'price', day: 0, time: '2:31 AM', noise: Math.sin(tg * 18) > 0 ? 5 : 4, place: 'FRESHWAY · AISLE 7' }) + captions(T, tg) + watermark() + finish({ vignette: 1 });
};

SHOTS.title = (T, tg, lt) => {
  const E = T.events;
  let s = rect(0, 0, W, H, { fill: '#0E0C0C' });
  const on = (x) => (x > 0.05 && x < 0.12) || (x > 0.2 && x < 0.26) || x > 0.38;
  const k = on(lt) ? 1 : 0.08;
  const gl = 0.85 + 0.15 * Math.sin(tg * 50) * (lt < 1 ? 1 : 0.2);
  s += glow(W / 2, 480, 300, '#F08A24', 0.28 * k * gl);
  s += text(W / 2, 520, 'LAST LIGHT', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 190, letterSpacing: 18, fill: k > 0.5 ? '#F7E3C8' : '#3A302A', textAnchor: 'middle', opacity: 1 });
  const k2 = ease(ramp(lt, 0.9, 1.6));
  s += g(smallCaps(W / 2, 640, 'EPISODE 1  ·  THE NIGHT SHIFT', 38, '#EDB344') + smallCaps(W / 2, 700, 'ZOMBIE OUTBREAK: 30 DAYS LOCKED INSIDE A SUPERMARKET', 22, '#8E8576'), { opacity: k2.toFixed(2) });
  if (tg > E.silence) s += rect(0, 0, W, H, { fill: '#000', opacity: ease(ramp(tg, E.silence + 0.7, T.dur)).toFixed(2) });
  return s + finish({ vignette: 0.9, grain: 0.16 });
};

export function frame(T, tg) {
  const sh = T.shots.find((x) => tg >= x.start && tg < x.end) || T.shots[T.shots.length - 1];
  const boil = 7 + (Math.floor(tg * 6) % 3) * 13;    // hand-drawn line boil at 6 fps
  return wrap(SHOTS[sh.name](T, tg, tg - sh.start), 5, boil);
}
export const SHOT_NAMES = Object.keys(SHOTS);
