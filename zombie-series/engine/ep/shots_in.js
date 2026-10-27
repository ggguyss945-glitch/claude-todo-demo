// Episode shot templates, inside the store. Each template is (T, tg, lt, p, D) -> SVG markup, where lt is the
// time inside the shot, D its duration and p the shot's parameters from the script.
import { W, H, INK, PAL, glow, hero, zombie, grade, g, rect, circle, ellipse, line, poly, path, text, ink, layer } from '../lib.js';
import { aisle, at } from '../scenes.js';
import { clamp, lerp, ease, easeOut, easeIn, back, ramp, wob, f1, keys, blinkAt, autoBlink, cam, push, shake, nightTint, screenGlow, darkness,
  letterbox, soundCap, quote, bang, rings, hudAt, sleeve, mitt, radioProp, keyring, alarmClock, label, nameTag, set } from './kit.js';
import * as S from './sets.js';

export const SH = {};
const W2 = W / 2;
let AISLES = {};
const aisleOf = (night) => (AISLES[night] ||= aisle({ night, seed: 5 }));
const bgAisle = (mode) => set(`aisle_${mode}`, () => aisleOf(mode !== 'day').s);
const blurred = (key, make) => layer(key + '_soft', () => g(make(), { filter: 'url(#softS)' }));
const exitSign = () => glow(960, 395, 90, '#7CFF9A', 0.5) + rect(925, 380, 70, 26, { fill: '#3DBE6A', stroke: INK, strokeWidth: 2 }) + text(960, 400, 'EXIT', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 18, fill: '#EFFFF2', textAnchor: 'middle' });
const tintFor = (mode) => ({ day: 0, dawn: 0.45, night: 0.86, dark: 0.93 })[mode] ?? 0.86;
const tintColor = (mode) => (mode === 'dawn' ? '#6E6A8A' : '#1F2940');

// the four dead from the night shift, by name
const WHO = { darlene: 'cashier', mike: 'guard', milk: 'shopper', gary: 'suit', jogger: 'jogger', park: 'park', nurse: 'nurse', janitor: 'janitor' };

// ---------- the aisle, any time of day ----------
SH.aisle = (T, tg, lt, p, D) => {
  const mode = p.mode || 'night', A = aisleOf(mode !== 'day');
  let s = bgAisle(mode === 'day' ? 'day' : 'night');
  if (p.clock12) s += alarmClock(1350, 470, 0.32, { ring: mode === 'night' ? 1 : 0, t: tg, tape: true });
  const Z = {
    four_turn: [[1250, 2.6, 'cashier', 12, 1], [1060, 3.4, 'suit', -6, 1], [760, 3.9, 'shopper', 8, 1], [1400, 4.6, 'guard', -10, 1]],
    four_line: [[640, 0.75, 'cashier', 10, 0], [900, 0.95, 'guard', -8, 0], [1160, 0.85, 'shopper', 6, 0], [1420, 1.2, 'suit', -6, 0]],
    three_walk_away: [[1150, 1.1, 'cashier', 12, 2], [880, 1.4, 'guard', -6, 2], [1320, 1.8, 'shopper', 8, 2]],
  }[p.zombies] || [];
  Z.forEach(([x, Zd, o, tl, mv], i) => {
    let zd = Zd, look = -0.5;
    if (mv === 1) look = lerp(-0.5, 0.9, ease(ramp(lt, 0.3 + i * 0.25, 1.6 + i * 0.25)));
    if (mv === 2) { zd = Zd + lt * 0.35; look = 0.6; }
    const q = at(A, x + (mv === 2 ? lt * 30 : 0), zd), walk = mv === 2 ? Math.sin(tg * 5 + i) * 6 : 0;
    s += zombie({ x: q.x, y: q.y, s: 1.4 * q.k, outfit: o, tilt: tl + 3 * Math.sin(tg * 0.9 + i) + walk, look, sway: 1.5 * Math.sin(tg * 0.7 + i * 2) + walk * 0.3, back: mv === 2 });
  });
  if (p.hero) {
    const hp = p.hero, h = at(A, hp.x ?? 760, hp.Zd ?? 0.1);
    s += hero({ x: h.x, y: h.y, s: 1.45 * h.k, pose: hp.pose || 'stand', expr: hp.expr || 'neutral', facing: hp.facing || 1, look: (hp.look ?? 0.3) + 0.1 * Math.sin(tg * 0.6), blink: autoBlink(lt, 2), breathe: 0.009 * Math.sin(tg * 2.2) });
  }
  // lights: day mode can black out on a word
  const out = typeof p.blackout === 'number' ? p.blackout : null;   // '@word' params arrive as shot-local seconds
  if (mode === 'day') { if (out !== null && lt > out) s += nightTint(lerp(0, 0.92, ease(ramp(lt, out, out + 0.12)))) + exitSign(); }
  else s += nightTint(tintFor(mode), tintColor(mode)) + exitSign();
  if (mode === 'night' && p.clock12) s += screenGlow(1350, 470, 90, 70, '#FFE27A', 0.25 + 0.15 * Math.sin(tg * 18));
  s = cam(s, { s: push(lt, D, p.push || [1.0, 1.07]), cx: 980, cy: 520 });
  return s + hudAt(p.hud);
};

// ---------- close-ups of the dead ----------
function closeBg(bg) {
  if (bg === 'lot_sunset') return set('zc_lot_sunset', () => S.sky('sunset') + S.cityBand('sunset') + rect(0, 760, W, 320, { fill: '#6A6066' }));
  if (bg === 'stock') return blurred('stock_open', () => S.stockroom({ open: true }));
  if (bg === 'aisle') return blurred('aisle_night', () => aisleOf(true).s);
  return set('zc_exit', () => {
    let s = rect(0, 0, W, H, { fill: '#2E3646' });
    for (let i = 0; i < 4; i++) s += rect(160 + i * 410, 120, 380, 760, { fill: '#4A6578', ...ink(5) }) + rect(180 + i * 410, 150, 340, 120, { fill: '#6E8FA3', opacity: 0.5 });
    s += rect(0, 860, W, 220, { fill: '#3B4048' }) + rect(880, 95, 160, 56, { fill: '#3DBE6A', ...ink(3) }) + text(960, 136, 'EXIT', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 38, fill: '#EFFFF2', textAnchor: 'middle' });
    return g(s, { filter: 'url(#wobble)' });
  });
}
SH.zclose = (T, tg, lt, p, D) => {
  const bg = p.bg || 'exit';
  let s = closeBg(bg);
  const who = p.who || ['milk', 'darlene', 'mike'];
  const pos = [[560, 1150, -10, 1.7], [1000, 1180, 8, 1.9], [1440, 1170, -6, 1.65]];
  who.forEach((w, i) => {
    const [x, y, tl, k] = pos[i], lag = i * 0.12;
    const look = p.look === 'turn' ? lerp(-0.75, 0.05, ease(ramp(lt - lag, 0.35, 1.9))) : 0.05 * Math.sin(tg * 0.5 + i);
    s += zombie({ x, y, s: k, outfit: WHO[w] || w, tilt: tl + 2 * Math.sin(tg + i), look, sway: 1.2 * Math.sin(tg * 0.8 + i) });
  });
  if (bg === 'lot_sunset') s += grade('dusk') + screenGlow(420, 480, 500, 300, '#FFC98A', 0.25);
  else { s += nightTint(0.55); if (bg === 'exit') s += glow(960, 120, 300, '#7CFF9A', 0.25); }
  return cam(s, { s: push(lt, D, [1.0, 1.05]) }) ;
};
SH.zname = (T, tg, lt, p, D) => {
  let s = closeBg('aisle');
  const o = WHO[p.who] || 'cashier';
  s += zombie({ x: 960, y: 1300, s: 2.5, outfit: o, tilt: -8 + 3 * Math.sin(tg * 0.8), look: 0.1 * Math.sin(tg * 0.6), sway: 1.5 * Math.sin(tg * 0.7) });
  s += nightTint(0.6) + screenGlow(700, 300, 400, 300, '#FFF2C4', 0.12);
  s = cam(s, { s: push(lt, D, [1.02, 1.08]), cy: 500 });
  return s + nameTag(120, 820, p.label, lt - 0.15);
};

// ---------- Gary ----------
SH.gary = (T, tg, lt, p, D) => {
  const mode = p.mode || 'stand';
  const tag = (x, y, k) => {
    const u = 60 * k, cx = x + 0.1 * u, top = y - 4.2 * u;
    return rect(cx + 0.08 * u, top + 0.5 * u, 0.95 * u, 0.46 * u, { rx: 10, fill: '#FBF6EA', ...ink(5) })
      + text(cx + 0.555 * u, top + 0.75 * u, 'GARY', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 0.22 * u, fill: INK, textAnchor: 'middle' })
      + text(cx + 0.555 * u, top + 0.89 * u, 'MANAGER', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 0.1 * u, fill: '#B5452F', textAnchor: 'middle', letterSpacing: 2 });
  };
  const clip = (x, y, u, rot = -8) => g(rect(-0.32 * u, -0.45 * u, 0.64 * u, 0.86 * u, { rx: 6, fill: '#B58759', ...ink(5) }) + rect(-0.26 * u, -0.32 * u, 0.52 * u, 0.68 * u, { fill: '#F7F2E6', ...ink(3) }) + rect(-0.12 * u, -0.52 * u, 0.24 * u, 0.12 * u, { fill: '#8A8F96', ...ink(3) }), { transform: `translate(${f1(x)} ${f1(y)}) rotate(${rot})` });
  if (mode === 'stand') {
    let s = blurred('aisle_night', () => aisleOf(true).s) + nightTint(0.85);
    const x = 900, y = 1150, k = 2.3, u = 60 * k;
    s += zombie({ x, y, s: k, outfit: 'suit', tilt: -10 + 5 * Math.sin(tg * 0.8), look: 0.15, sway: 2 * Math.sin(tg * 0.6), extra: tag(x, y, k) + clip(x + 0.85 * u, y - 2.4 * u, u) });
    s += screenGlow(560, 300, 500, 300, '#FFF2C4', 0.1);
    s = cam(s, { s: push(lt, D, [1.0, 1.07]), cx: 980, cy: 480 });
    return s + (p.label ? nameTag(120, 820, 'GARY · STORE MANAGER', lt - 0.1) : '');
  }
  if (mode === 'walk') {
    const A = aisleOf(true); let s = bgAisle('night');
    const q = at(A, 980 + lt * 10, 0.35 + lt * 0.32), wk = Math.sin(tg * 4.6) * 5;
    s += zombie({ x: q.x, y: q.y, s: 1.4 * q.k, outfit: 'suit', tilt: -6 + wk, back: true, sway: wk * 0.3, extra: clip(q.x + 0.9 * 84 * q.k, q.y - 2.4 * 84 * q.k, 84 * q.k, 10) });
    s += nightTint(0.86) + exitSign();
    return cam(s, { s: push(lt, D, [1.0, 1.05]), cx: 980, cy: 520 });
  }
  // at the office door window: 'window' (deadpan stare) or 'bang' (7:00 sharp)
  let s = set('officeDoor_day', () => S.officeDoor({ dawn: true }));
  const bangK = mode === 'bang' ? Math.abs(Math.sin(lt * 5.5)) : 0;
  let face = zombie({ x: 960, y: 900 + bangK * 6, s: 1.5, outfit: 'suit', tilt: -6 + 3 * Math.sin(tg), look: 0.05, pose: mode === 'bang' ? 'bang' : 'stand', extra: tag(960, 900, 1.5) });
  s += `<clipPath id="win"><rect x="770" y="230" width="380" height="300" rx="6"/></clipPath>` + g(rect(770, 230, 380, 300, { fill: '#6E7378' }) + face, { clipPath: 'url(#win)' });
  s += rect(770, 230, 380, 300, { rx: 6, fill: '#D9DCD6', opacity: 0.35, ...ink(6) });
  if (mode === 'bang') s += bang('BANG!', 1420, 330, (lt % 0.9) - 0.0, { size: 120, life: 0.8 }) + bang('BANG!', 520, 420, ((lt + 0.45) % 0.9), { size: 100, rot: 8, life: 0.8 });
  s = cam(s, { s: push(lt, D, [1.0, 1.06]), cy: 420, ...(mode === 'bang' ? shake(tg, bangK * 0.4) : {}) });
  return s + hudAt(mode === 'bang' ? { day: 5, time: '7:00 AM', noise: 3, place: 'FRESHWAY · OFFICE' } : { day: 0, time: '7:05 AM', noise: 0, place: 'FRESHWAY · OFFICE' });
};

// ---------- hero close-ups on many backgrounds ----------
const HC_BG = {
  aisle_dark: () => blurred('aisle_night', () => aisleOf(true).s) + nightTint(0.9),
  aisle_dawn: () => blurred('aisle_night', () => aisleOf(true).s) + nightTint(0.55, '#6E6A8A'),
  aisle_day: () => blurred('aisle_day', () => aisleOf(false).s),
  stock_dark: () => blurred('stock_open', () => S.stockroom({ open: true })) + nightTint(0.85),
  camp: () => blurred('camp', () => S.campAisle()) + nightTint(0.78, '#3A2A3A') + screenGlow(1300, 760, 520, 360, '#FFC97A', 0.35),
  roof_sunset: () => blurred('roof_sunset', () => S.roofSet({ time: 'sunset' })),
  roof_day: () => blurred('roof_day', () => S.roofSet({ time: 'day' })),
  lot_night: () => blurred('lot_night', () => S.lotSet({ time: 'night' })) + nightTint(0.6),
  dark: () => rect(0, 0, W, H, { fill: '#0C0E14' }) + screenGlow(700, 380, 500, 300, '#3A4A6A', 0.5),
};
SH.hclose = (T, tg, lt, p, D) => {
  const bgk = p.bg || 'aisle_dark';
  let s = (HC_BG[bgk] || HC_BG.aisle_dark)();
  const sit = p.mode === 'sit', y = sit ? 1440 : 1340;
  const prop = p.prop;
  const pose = prop === 'radio_mouth' || prop === 'phone' ? 'radio' : prop === 'radio' ? 'radio' : prop === 'binder' || prop === 'peaches' ? 'carry' : p.flashlight ? 'flashlight' : (p.expr === 'scared' ? 'scared' : 'stand');
  const look = p.look ?? 0;
  const lookK = typeof look === 'number' ? look + 0.08 * Math.sin(tg * 0.7) : 0;
  let extra = '';
  const u = 60 * 2.6, hx = 960 + 0.42 * u, hy = y - 4.05 * u + 0.2 * u;
  if (prop === 'phone') extra += g(rect(-48, -88, 96, 176, { rx: 14, fill: '#1E1F22', ...ink(5) }) + rect(-40, -78, 80, 150, { rx: 8, fill: '#BFE3F2' }), { transform: `translate(${hx + 60} ${hy + 150}) rotate(-12)` });
  if (prop === 'radio') extra += radioProp(hx - 30, hy + 40, 0.75, { on: true, led: '#7FD36B' });
  if (prop === 'radio_mouth') extra += radioProp(960 + 1.25 * u, y - 4.55 * u, 0.62, { on: true, led: PAL.red, rot: -14 });
  if (prop === 'binder') extra += g(rect(-170, -110, 340, 220, { rx: 10, fill: '#3E6E9A', ...ink(6) }) + rect(-150, -90, 140, 180, { fill: '#F7F2E6', ...ink(3) }) + rect(10, -90, 140, 180, { fill: '#F7F2E6', ...ink(3) }) + text(-80, -40, 'FACILITY', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 18, fill: INK, textAnchor: 'middle' }) + text(-80, -14, 'MANUAL', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 18, fill: INK, textAnchor: 'middle' }), { transform: `translate(960 ${y - 2.8 * u})` });
  if (prop === 'peaches') extra += g(rect(-50, -60, 100, 120, { rx: 12, fill: '#E9B93E', ...ink(5) }) + rect(-50, -20, 100, 40, { fill: '#F3EEDF', ...ink(3) }) + text(0, 8, 'PEACHES', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 16, fill: INK, textAnchor: 'middle' }) + line(30, -60, 60, -160, ink(6)), { transform: `translate(${960 + 0.3 * u} ${y - 3.0 * u})` });
  const expr = p.expr || 'neutral';
  s += hero({ x: 960, y, s: 2.6, pose, expr, facing: 1, look: lookK, blink: autoBlink(lt, 1), tilt: 1.3 * Math.sin(tg * 0.85), breathe: 0.011 * Math.sin(tg * 2.4), hold: p.flashlight ? 'flashlight' : undefined, aim: -20, extra });
  if (prop === 'phone') s += screenGlow(hx + 40, hy + 40, 260, 260, '#BFE3F2', 0.4);
  if (p.warm || bgk === 'camp') s += screenGlow(1250, 600, 420, 380, '#FFD9A0', 0.2);
  if (p.flashlight) s += screenGlow(1500, 300, 360, 260, '#FFF2C4', 0.35);
  if (bgk === 'roof_sunset') s += screenGlow(300, 400, 600, 400, '#FFC98A', 0.28);
  s = cam(s, { s: push(lt, D, [1.0, 1.05]), cx: 960, cy: 520 });
  return s + hudAt(p.hud);
};

// ---------- stockroom ----------
SH.stock = (T, tg, lt, p, D) => {
  const open = p.freezer === 'open';
  let s = set(open ? 'stock_open' : 'stock_closed', () => S.stockroom({ open }));
  if (p.peas) s += g(rect(1655, 720, 90, 60, { rx: 6, fill: '#6F8F4E', ...ink(4) }) + text(1700, 758, 'PEAS', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 18, fill: '#F3EEDF', textAnchor: 'middle' }), { filter: 'url(#wobbleSoft)' });
  if (p.phone) s += rect(1450, 740, 60, 22, { rx: 4, fill: '#1E1F22', ...ink(3) }) + rect(1456, 743, 48, 14, { fill: '#BFE3F2' });
  const hp = p.hero;
  if (hp === 'place') s += hero({ x: 1380 + lt * 4, y: 790, s: 1.2, pose: 'crouch', expr: 'worried', facing: 1, look: 0.5, blink: autoBlink(lt), breathe: 0.01 * Math.sin(tg * 2.2) });
  if (hp === 'climb') { const up = ease(ramp(lt, 0.1, D)); s += hero({ x: 560, y: lerp(770, 560, up), s: 1.0, pose: 'climb', expr: 'determined', facing: -1, look: -0.2, blink: autoBlink(lt) }); }
  if (hp === 'top') s += rect(588, 118, 444, 20, { rx: 4, fill: '#3E6E9A', ...ink(4) }) + g(hero({ x: 0, y: 0, s: 0.62, pose: 'stand', expr: 'worried', facing: 1, look: 0.6, blink: autoBlink(lt), breathe: 0.01 * Math.sin(tg * 2.2) }), { transform: 'translate(960 120) rotate(-90)' });
  const dark = p.view === 'top_dark';
  s += nightTint(dark ? 0.93 : 0.82);
  if (open) s += screenGlow(1490, 560, 300, 320, '#BFE3F2', dark ? 0.32 : 0.45) + screenGlow(1480, 760, 260, 60, '#BFE3F2', 0.5, 'softS');
  if (p.phone) s += screenGlow(1480, 740, 70, 40, '#BFE3F2', 0.8, 'softS');
  s += screenGlow(935, 62, 120, 60, '#F6EBC0', 0.5);
  if (p.label) s += g(rect(240, 200, 260, 60, { rx: 6, fill: PAL.yellow, ...ink(4) }) + label(370, 240, p.label, 24), { opacity: f1(clamp((lt - 0.3) * 3) * 100) / 100, filter: 'url(#wobbleSoft)' });
  const fv = p.view === 'freezer_open';
  s = cam(s, fv ? { s: lerp(1.45, 1.55, ease(lt / D)), cx: 1480, cy: 560 } : { s: push(lt, D, dark ? [1.0, 1.04] : [1.0, 1.06]), cx: 960, cy: 500 });
  return s + hudAt(p.hud);
};

// POV from the top of the shelving: the floor below, the open freezer, the dead walking in
SH.povshelf = (T, tg, lt, p, D) => {
  const ph = p.phase;
  let s = set('pov_floor', () => {
    let o = rect(0, 0, W, H, { fill: '#8F8A7E' });
    for (let i = 0; i < 14; i++) o += line(-200 + i * 180, 0, -600 + i * 260, H, { stroke: '#7E796E', strokeWidth: 3 });
    for (let i = 0; i < 8; i++) o += line(0, 120 + i * 130, W, 160 + i * 130, { stroke: '#7E796E', strokeWidth: 3 });
    // freezer doorway seen from above (top right), and a box stack on the left
    o += poly([[1300, 120], [1760, 120], [1700, 430], [1360, 430]], { fill: '#5E7F99', ...ink(6) }) + poly([[1700, 430], [1900, 380], [1900, 80], [1760, 120]], { fill: '#D5D9DC', ...ink(6) });
    o += rect(80, 80, 360, 260, { fill: '#B58759', ...ink(5) }) + rect(120, 380, 240, 180, { fill: '#C49A6C', ...ink(5) });
    return g(o, { filter: 'url(#wobble)' });
  });
  const ringOn = ph !== 'wait' && ph !== 'slam';
  if (ringOn) s += rings(1530, 280, tg, { color: '#BFE3F2', max: 260, period: 0.9, op: 0.6 });
  // the dead, from above: shoulders + head, arms forward
  const top = (x, y, rot, o, look = 0) => {
    const c = { cashier: '#8C8C86', guard: '#2E3D55', shopper: '#7C6A8E' }[o];
    let f = ellipse(0, 0, 105, 60, { fill: c, ...ink(5) }) + line(-75, -15, -90, -120, ink(16)) + line(75, -15, 90, -120, ink(16)) + circle(-90, -126, 20, { fill: PAL.zSkin, ...ink(4) }) + circle(90, -126, 20, { fill: PAL.zSkin, ...ink(4) });
    f += circle(0, -9, 56, { fill: PAL.zSkin, ...ink(5) }) + path('M-30 -20 Q0 -44 30 -20', { fill: 'none', stroke: PAL.zSkinDark, strokeWidth: 8, opacity: 0.6 });
    if (look) f += g(ellipse(-12, -10, 8, 9, { fill: PAL.zEye }) + ellipse(14, -8, 8, 9, { fill: PAL.zEye }) + ellipse(2, 12, 7, 9, { fill: '#2A2522' }), { opacity: f1(look * 100) / 100 });
    return g(f, { transform: `translate(${f1(x)} ${f1(y)}) rotate(${f1(rot)})` });
  };
  const walkers = { enter: [0, 1, 2], stop: [0, 1, 2], pass: [0, 1, 2], drop: [2] }[ph] || [];
  const path3 = [[[-160, 900], [700, 760], [1420, 360]], [[-300, 700], [500, 640], [1480, 320]], [[-420, 980], [600, 900], [1500, 420]]];
  const prog = (i) => {
    if (ph === 'enter') return clamp((lt - i * 0.9) / 7.5) * 0.55;
    if (ph === 'stop') return i === 0 ? 0.55 + 0.04 * ease(ramp(lt, 0, 1.2)) : 0.55 + clamp(lt / 6) * 0.35;
    if (ph === 'pass') return i === 0 ? 0.6 + clamp(lt / 4) * 0.4 : 0.9 + clamp(lt / 4) * 0.1;
    if (ph === 'drop') return 0.82;
    return 0;
  };
  for (const i of walkers) {
    const k = prog(i); if (k <= 0 || k >= 1) continue;
    const [a, b, c] = path3[i], seg = k < 0.5 ? [a, b, k * 2] : [b, c, (k - 0.5) * 2];
    const x = lerp(seg[0][0], seg[1][0], seg[2]), y = lerp(seg[0][1], seg[1][1], seg[2]);
    const lookUp = ph === 'stop' && i === 0 ? ease(ramp(lt, 1.6, 2.6)) * (1 - ease(ramp(lt, 4.8, 5.6))) : 0;
    s += top(x, y, Math.atan2(c[1] - a[1], c[0] - a[0]) * 180 / Math.PI + 90 + 6 * Math.sin(tg * 5 + i), ['cashier', 'guard', 'shopper'][i], lookUp);
  }
  s += nightTint(0.62) + screenGlow(1520, 300, 360, 260, '#BFE3F2', ringOn ? 0.6 : 0.4) + screenGlow(1200, 520, 600, 300, '#BFE3F2', 0.18);
  // our hands on the shelf edge, above the letterbox
  let hands = rect(-20, 820, W + 40, 140, { fill: '#3E6E9A', ...ink(6) }) + rect(-20, 800, W + 40, 26, { fill: '#2F5577', ...ink(4) }) + sleeve('M0 960 L200 780 L460 840 L380 960 Z') + sleeve('M1920 960 L1720 780 L1460 840 L1540 960 Z');
  hands += mitt(380, 800, 10, 1.15) + mitt(1540, 800, -10, 1.15);
  s += g(hands, { filter: 'url(#wobbleSoft)' });
  s += darkness(0.6, 0.4, 0.75, 0.6, 'pvd');
  let camo = { s: 1.04 + 0.01 * Math.sin(tg * 0.7), x: wob(tg * 0.8, 3) * 6, y: wob(tg * 0.7, 4) * 5 };
  if (ph === 'drop') { const k = easeIn(ramp(lt, 0.4, 0.95)); camo = { s: 1.04 + k * 0.6, x: 0, y: -k * 500 }; }
  s = cam(s, camo);
  if (ph === 'drop' && lt > 0.95) s += rect(0, 0, W, H, { fill: '#05070C', opacity: f1(clamp(1 - (lt - 0.95) * 2) * 100) / 100 });
  if (ph === 'slam') s = povSlam(tg, lt);
  return s + letterbox() + capsAt(T, tg);
};
function povSlam(tg, lt) {
  let s = set('stock_open', () => S.stockroom({ open: true })) + nightTint(0.85);
  const k = easeOut(ramp(lt, 0.1, 0.38));
  s += poly([[1680, 224], [lerp(1930, 1680, k), lerp(190, 224, k)], [lerp(1930, 1680, k), lerp(825, 769, k)], [1680, 769]], { fill: '#D5D9DC', ...ink(6) });
  s += g(sleeve('M1920 1080 L1700 820 L1560 900 L1700 1080 Z') + mitt(1640, 760 + (1 - k) * 60, -20, 1.2), { filter: 'url(#wobbleSoft)' });
  s += screenGlow(1490, 560, 300 * (1 - k * 0.9), 320 * (1 - k * 0.9), '#BFE3F2', 0.45 * (1 - k));
  return cam(s, { s: 1.5, cx: 1480, cy: 540, ...shake(tg, k > 0.95 && lt < 0.7 ? 1 : 0) });
}
// sound captions belong to BEAT items; the timeline hands them over as T.caps
export const capsAt = (T, tg) => {
  let s = '';
  for (const c of T.caps || []) if (tg >= c[0] && tg < c[1]) s += soundCap(c[2]);
  return s;
};

// ---------- the phone ----------
SH.phone = (T, tg, lt, p, D) => {
  let s = rect(0, 0, W, H, { fill: '#0E1016' }) + blurred('stock_open', () => S.stockroom({ open: true })) + nightTint(0.92);
  const k = 1.4;
  let ph = rect(-190, -360, 380, 720, { rx: 46, fill: '#1E1F22', ...ink(7) }) + rect(-168, -330, 336, 660, { rx: 30, fill: p.ui === 'alarm' ? '#10141C' : '#20324A' });
  ph += text(0, -250, p.ui === 'alarm' ? 'Alarm' : '2:44', { fontFamily: 'Rubik', fontWeight: p.ui === 'alarm' ? 800 : 500, fontSize: p.ui === 'alarm' ? 40 : 110, fill: '#F2F2EE', textAnchor: 'middle' });
  ph += text(-140, -300, 'No Service', { fontFamily: 'Rubik', fontWeight: 600, fontSize: 18, fill: '#C9D8E6' }) + rect(70, -316, 56, 22, { rx: 5, fill: 'none', stroke: '#F2F2EE', strokeWidth: 3 }) + rect(74, -312, 17, 14, { fill: PAL.red }) + text(140, -298, '31%', { fontFamily: 'Rubik', fontWeight: 700, fontSize: 16, fill: '#F2F2EE' });
  if (p.ui === 'alarm') {
    const on = ease(ramp(lt, D - 0.9, D - 0.6));
    ph += rect(-150, -150, 300, 170, { rx: 22, fill: '#1E2533' }) + text(-120, -40, '2:50', { fontFamily: 'Rubik', fontWeight: 500, fontSize: 84, fill: '#F2F2EE' }) + text(-118, 0, 'AM · Alarm', { fontFamily: 'Rubik', fontWeight: 600, fontSize: 20, fill: '#9AA8BA' });
    ph += rect(60, -90, 90, 50, { rx: 25, fill: on > 0.5 ? '#3DBE6A' : '#3A4150' }) + circle(lerp(85, 125, on), -65, 21, { fill: '#F2F2EE' });
    ph += rect(-150, 60, 300, 120, { rx: 22, fill: '#1E2533', opacity: 0.6 }) + text(-120, 135, '7:00', { fontFamily: 'Rubik', fontWeight: 500, fontSize: 60, fill: '#5C6575' });
  } else {
    ph += text(0, -170, 'Tuesday, March 4', { fontFamily: 'Rubik', fontWeight: 500, fontSize: 24, fill: '#C9D8E6', textAnchor: 'middle' });
    ph += rect(-150, -100, 300, 110, { rx: 18, fill: '#2C4462', opacity: 0.9 }) + text(-130, -55, 'MOM', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 18, fill: '#F2F2EE' }) + text(-130, -25, 'call me when you get this', { fontFamily: 'Rubik', fontWeight: 500, fontSize: 17, fill: '#C9D8E6' });
  }
  s += g(ph, { transform: `translate(960 560) scale(${k}) rotate(${f1(-4 + 1.5 * Math.sin(tg * 0.6))})`, filter: 'url(#wobbleSoft)' });
  s += g(sleeve('M200 1080 L620 820 L800 900 L640 1080 Z') + mitt(760, 860, -30, 1.3), { filter: 'url(#wobbleSoft)' });
  s += screenGlow(960, 520, 500, 600, '#7FB3D5', 0.22);
  if (p.ui === 'alarm' && lt > D - 0.7) s += mitt(1090, 470, -60, 0.9);
  return cam(s, { s: push(lt, D, [1.0, 1.04]), x: wob(tg * 0.6, 2) * 6, y: wob(tg * 0.5, 5) * 5 });
};

// ---------- the walk-in freezer ----------
SH.freezer = (T, tg, lt, p, D) => {
  if (p.view === 'diagram') {
    let s = rect(0, 0, W, H, { fill: PAL.cream });
    s += label(W2, 150, 'WALK-IN FREEZER WALL', 40, INK, 'middle', 6);
    const L = [['STEEL', 520, 60, '#B7BBBE'], ['FOAM · 4 IN', 600, 420, '#E9D89A'], ['STEEL', 1040, 60, '#B7BBBE']];
    for (const [n, x, w, c] of L) s += rect(x, 220, w, 520, { fill: c, ...ink(6) }) + label(x + w / 2, 790, n, 26, INK);
    for (let i = 0; i < 24; i++) s += circle(640 + (i % 6) * 60, 270 + Math.floor(i / 6) * 120, 18, { fill: '#F2E4A8', ...ink(2) });
    const k = clamp(lt / 1.8);
    for (let r = 0; r < 4; r++) { const x = lerp(200, 900, clamp(k * 1.2 - r * 0.15)), op = x < 600 ? 0.9 : Math.max(0, 0.9 - (x - 600) / 300); s += path(`M${x} 360 q30 120 0 240`, { fill: 'none', stroke: PAL.red, strokeWidth: 10, strokeLinecap: 'round', opacity: f1(op * 100) / 100 }); }
    s += label(260, 500, 'SOUND', 28, PAL.red) + label(1400, 500, k > 0.7 ? 'SILENCE' : '', 28, '#3E6E9A');
    return g(s, { filter: 'url(#wobbleSoft)' }) + '';
  }
  let s = set('freezer_door', () => {
    let o = rect(0, 0, W, H, { fill: '#C9CDD0' });
    for (let x = 0; x < W; x += 90) o += line(x, 0, x, H, { stroke: '#B2B7BB', strokeWidth: 4 });
    o += rect(560, 140, 800, 940, { fill: '#D5D9DC', ...ink(7) }) + rect(1390, 420, 60, 300, { rx: 22, fill: '#8E9499', ...ink(6) });
    o += rect(1460, 200, 300, 160, { rx: 12, fill: '#2B2F33', ...ink(5) });
    return g(o, { filter: 'url(#wobble)' });
  });
  s += `<clipPath id="fwin"><rect x="760" y="260" width="400" height="320" rx="14"/></clipPath>`;
  let inside = rect(760, 260, 400, 320, { fill: '#5E7F99' });
  inside += zombie({ x: 880, y: 900, s: 1.3, outfit: 'guard', tilt: 8 + 2 * Math.sin(tg), look: 0.2, dim: 0.4 }) + zombie({ x: 1060, y: 940, s: 1.35, outfit: 'cashier', tilt: -6, look: -0.2, dim: 0.4 });
  if (p.view === 'window_face') inside += zombie({ x: 960, y: 1200, s: 2.3, outfit: 'shopper', tilt: -4, look: 0, extra: '' }) + mitt(820, 380, 160, 0.9, PAL.zSkin) + mitt(1100, 390, 200, 0.9, PAL.zSkin);
  s += g(inside + rect(760, 260, 400, 320, { fill: '#E9F4F8', opacity: 0.35 }), { clipPath: 'url(#fwin)' });
  s += rect(760, 260, 400, 320, { rx: 14, fill: 'none', ...ink(7) });
  for (let i = 0; i < 9; i++) s += path(`M${770 + i * 45} 270 q20 30 0 60`, { fill: 'none', stroke: '#FFFFFF', strokeWidth: 5, opacity: 0.5 });
  s += text(1610, 300, p.temp || '-18°C', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 64, fill: '#8FE3FF', textAnchor: 'middle' }) + glow(1610, 280, 120, '#8FE3FF', 0.35);
  s += nightTint(0.6) + screenGlow(960, 420, 300, 240, '#BFE3F2', 0.35);
  const thump = p.view === 'window_face' ? Math.exp(-Math.max(0, lt - 1.2) * 8) * (lt > 1.2 ? 1 : 0) : 0;
  return cam(s, { s: push(lt, D, [1.0, 1.06]), cy: 420, ...shake(tg, thump * 0.8) }) + (thump > 0.05 ? bang('THUMP', 1500, 820, lt - 1.2, { size: 110, life: 0.9 }) : '');
};

// ---------- the manager's office ----------
SH.office = (T, tg, lt, p, D) => {
  const v = p.view, time = p.time, hudP = { day: 0, time, noise: p.noise ?? 1, place: 'FRESHWAY · OFFICE' };
  if (v === 'door_close' || v === 'door_out' || v === 'lockout') {
    let s = set(v === 'door_out' ? 'officeDoor_dawn' : 'officeDoor_night', () => S.officeDoor({ dawn: v === 'door_out' }));
    s += `<clipPath id="win2"><rect x="770" y="230" width="380" height="300" rx="6"/></clipPath>`;
    s += g(rect(770, 230, 380, 300, { fill: '#8A8F8A' }) + zombie({ x: 960, y: 980, s: 1.6, outfit: 'suit', tilt: -6 + 3 * Math.sin(tg), look: 0, back: v !== 'lockout', filter: false }) + rect(770, 230, 380, 300, { fill: '#E2E6E0', opacity: v === 'lockout' ? 0.3 : 0.45 }), { clipPath: 'url(#win2)' });
    s += rect(770, 230, 380, 300, { rx: 6, fill: 'none', ...ink(6) });
    if (v === 'door_close') { const k = ease(ramp(lt, 0.3, 1.3)); s = s + poly([[680, 150], [lerp(400, 680, k), 110], [lerp(400, 680, k), 900], [680, 860]], { fill: '#1E1A1A', opacity: f1((1 - k) * 0.85 * 100) / 100 }); }
    if (v === 'lockout') s += g(sleeve('M1920 1080 L1350 760 L1250 860 L1600 1080 Z') + mitt(1190, 690, -50, 1.0) + rect(1140, 655, 60, 14, { fill: '#C9A43A', ...ink(3) }), { filter: 'url(#wobbleSoft)' });
    s += v === 'door_out' ? nightTint(0.45, '#6E6A8A') : nightTint(v === 'lockout' ? 0.3 : 0.85);
    return cam(s, { s: push(lt, D, [1.0, 1.06]), cy: 450 }) + hudAt(v === 'door_close' ? { day: 0, time: '2:33 AM', noise: 1, place: 'FRESHWAY · OFFICE' } : hudP);
  }
  if (v === 'panel' || v === 'switch') {
    let s = rect(0, 0, W, H, { fill: '#C9C0AA' }) + rect(420, 120, 1080, 900, { rx: 30, fill: '#9AA0A6', ...ink(8) }) + rect(420, 120, 1080, 150, { rx: 30, fill: '#7C8288', ...ink(6) });
    s += label(960, 220, 'STORE SCHEDULE', 64, '#F2F2EE', 'middle', 6);
    const flip = p.state === 'flip' ? ease(ramp(lt, D - 0.65, D - 0.35)) : 0;
    s += label(700, 520, 'OPEN', 60, flip < 0.5 ? '#2F7A4F' : '#6B6F74') + label(1220, 520, 'CLOSED', 60, flip >= 0.5 ? PAL.red : '#6B6F74');
    s += rect(820, 600, 280, 120, { rx: 60, fill: '#3A3D42', ...ink(6) }) + circle(lerp(880, 1040, flip), 660, 48, { fill: '#E9E5DC', ...ink(5) });
    s += label(960, 860, 'AUTO OPEN 7:00 · DOORS · LIGHTS', 30, '#2B2F33');
    s += circle(560, 860, 16, { fill: flip < 0.5 ? '#9CFF8A' : '#3A3D42', ...ink(3) });
    if (v === 'switch') s += g(sleeve(`M1920 1080 L${f1(1240 + lerp(-150, 0, flip))} 820 L${f1(1160 + lerp(-150, 0, flip))} 940 L1640 1080 Z`) + mitt(lerp(890, 1050, flip) + 40, 640, -70, 1.1), { filter: 'url(#wobbleSoft)' });
    s = g(s, { filter: 'url(#wobbleSoft)' }) + nightTint(0.55, '#6E6A8A');
    return cam(s, { s: push(lt, D, v === 'switch' ? [1.18, 1.25] : [1.0, 1.06]), cy: 560 }) + hudAt(hudP);
  }
  if (v === 'socks') {
    let s = rect(0, 0, W, H, { fill: '#6F757C' });
    for (let i = 0; i < 40; i++) s += rect((i * 397) % W, 100 + (i * 211) % 900, 50, 4, { fill: '#5E646B' });
    const shoe = (x, y) => path(`M${x} ${y} q0 -60 60 -70 l120 -10 q50 0 60 40 l10 40 z`, { fill: '#3A2E26', ...ink(6) }) + line(x + 30, y - 40, x + 150, y - 50, { stroke: '#7A6050', strokeWidth: 4 });
    s += g(shoe(180, 900) + shoe(380, 930), { filter: 'url(#wobbleSoft)' }) + label(360, 990, 'SHOES OFF', 26, '#D9D2C2', 'middle', 4);
    const foot = (x, ph) => {
      const k = (Math.sin(lt * 2.4 + ph) + 1) / 2, y = 760 - k * 60, heel = k > 0.5 ? -8 : 10;
      return g(path(`M${x - 40} -40 L${x - 30} ${y - 90} L${x + 40} ${y - 90} L${x + 50} -40 Z`, { fill: PAL.jeans, ...ink(6) })
        + g(path('M-50 -90 h90 v40 q120 -10 140 40 q10 40 -40 50 h-190 q-30 0 -30 -40 z', { fill: '#A8A39A', ...ink(6) }) + path('M-50 -40 h90', { stroke: '#8E8A80', strokeWidth: 6 }), { transform: `translate(${x} ${y}) rotate(${heel})` }), {});
    };
    s += g(foot(1060, 0) + foot(1420, Math.PI), { filter: 'url(#wobbleSoft)' });
    s += nightTint(0.5, '#6E6A8A');
    return cam(s, { s: push(lt, D, [1.0, 1.05]), x: lt * 10 }) + hudAt(hudP);
  }
  if (v === 'keys_belt' || v === 'keys_take') {
    let s = rect(0, 0, W, H, { fill: '#3B3F48' }) + rect(0, 380, W, 70, { fill: '#2A2522', ...ink(6) }) + rect(860, 365, 200, 100, { rx: 10, fill: '#C9A43A', ...ink(6) });
    s += rect(0, 450, W, 630, { fill: '#30333B' }) + line(960, 450, 960, 1080, { stroke: '#22252B', strokeWidth: 6 });
    const lift = v === 'keys_take' ? ease(ramp(lt, 0.4, D - 0.3)) : 0;
    s += keyring(1300, 470 - lift * 260, 1.4, tg, v === 'keys_take' ? 0.15 : 1);
    if (v === 'keys_take') s += g(sleeve('M1920 0 L1500 300 L1420 220 L1700 0 Z') + mitt(1330, 360 - lift * 260, 170, 1.0), { transform: `translate(0 ${f1(-lift * 10)})`, filter: 'url(#wobbleSoft)' });
    s = g(s, { filter: 'url(#wobbleSoft)' }) + nightTint(0.5, '#6E6A8A');
    return cam(s, { s: push(lt, D, [1.0, 1.08]), cx: 1300, cy: 500 }) + hudAt(hudP);
  }
  // wide office and its moments
  let s = set('office', () => S.office());
  const clockAng = (time) => { const m = /(\d+):(\d+)/.exec(time || '6:52'); return [+m[1], +m[2]]; };
  const [hh, mm] = clockAng(time);
  const ma = (mm / 60) * 2 * Math.PI - Math.PI / 2, ha = ((hh % 12) / 12 + mm / 720) * 2 * Math.PI - Math.PI / 2;
  s += line(760, 290, 760 + Math.cos(ha) * 48, 290 + Math.sin(ha) * 48, ink(9)) + line(760, 290, 760 + Math.cos(ma) * 72, 290 + Math.sin(ma) * 72, ink(6));
  const blastK = v === 'blast' || v === 'cable' ? 1 : 0;
  const turn = v === 'blast' ? ease(ramp(lt, 0.15, 0.4)) : v === 'cable' || v === 'cable_pulled' ? 1 : 0;
  // Gary behind the desk, facing the clock; the music makes him turn
  s += zombie({ x: 800, y: 700, s: 1.55, outfit: 'suit', tilt: lerp(-4, 14, turn) + 2 * Math.sin(tg * 0.8), back: turn < 0.5, look: 0.9, sway: 1.2 * Math.sin(tg * 0.6) });
  s += rect(430, 640, 760, 70, { fill: '#9B6E45', ...ink(6) });
  const heroAt = { door: [250, 'stand', 'worried'], sneak1: [520 + lt * 30, 'sneak', 'worried'], sneak2: [1010 + lt * 25, 'sneak', 'scared'], panel: [1560, 'reach', 'determined'] }[p.hero];
  if (heroAt) s += hero({ x: heroAt[0], y: 1000, s: 1.4, pose: heroAt[1], expr: heroAt[2], facing: 1, look: p.hero === 'sneak2' ? -0.5 : 0.4, blink: autoBlink(lt, 3), breathe: 0.01 * Math.sin(tg * 2.4) });
  if (v === 'cable' || v === 'cable_pulled') {
    const pulled = v === 'cable_pulled' ? 1 : ease(ramp(lt, D - 0.5, D));
    s += hero({ x: 1700, y: 1000, s: 1.4, pose: 'push', expr: 'determined', facing: -1, look: -0.3 });
    s += path(`M1800 760 C${1780 - pulled * 120} 800 ${1700 - pulled * 200} 860 ${1650 - pulled * 240} ${880 - pulled * 30}`, { fill: 'none', stroke: INK, strokeWidth: 12 });
  }
  if (p.path) {
    const k = ease(ramp(lt, 0.3, 2.2));
    s += path('M300 900 Q600 950 900 930 T1560 880', { fill: 'none', stroke: PAL.yellow, strokeWidth: 8, strokeDasharray: '4 18', strokeLinecap: 'round', opacity: f1(k * 100) / 100 });
    s += circle(800, 600, 260, { fill: 'none', stroke: PAL.red, strokeWidth: 6, strokeDasharray: '16 12', opacity: f1(ease(ramp(lt, 1.6, 2.4)) * 0.8 * 100) / 100 }) + label(800, 330, "ARM'S REACH", 26, PAL.red);
  }
  if (blastK) {
    s += rings(980, 70, tg, { color: '#FFE27A', max: 700, period: 0.45, width: 14, dash: '30 14', op: 1 }) + rings(1700, 740, tg + 0.2, { color: '#FFE27A', max: 300, period: 0.45, width: 10, op: 1 });
    for (let i = 0; i < 8; i++) { const k = ((tg * 0.9 + i / 8) % 1); s += text(980 + Math.cos(i * 1.7) * k * 700, 160 + k * 520, ['♪', '♫'][i % 2], { fontFamily: 'Rubik', fontSize: 130, fill: '#FFE27A', stroke: INK, strokeWidth: 6, paintOrder: 'stroke', opacity: f1((1 - k * 0.7) * 100) / 100 }); }
  }
  if (v === 'speaker') s += screenGlow(1700, 755, 140, 60, '#9CFF8A', 0.6 + 0.3 * Math.sin(tg * 6), 'softS');
  s += nightTint(0.42, '#6E6A8A') + screenGlow(1345, 300, 300, 260, '#BFE3C8', 0.25);
  const camo = v === 'speaker' ? { s: lerp(2.2, 2.5, ease(lt / D)), cx: 1700, cy: 740 } : v === 'cable' ? { s: 1.25, cx: 1500, cy: 700, ...shake(tg, 0.5) } : v === 'cable_pulled' ? { s: 1.25, cx: 1500, cy: 700 } : v === 'blast' ? { s: push(lt, D, [1.0, 1.04]), ...shake(tg, 0.7) } : { s: push(lt, D, [1.0, 1.05]) };
  return cam(s, camo) + hudAt(hudP);
};

// ---------- the front doors ----------
SH.doors = (T, tg, lt, p, D) => {
  let s = set('doors_out', () => S.doorsOutside({ dawn: true }));
  const surge = p.mode === 'surge' ? 1 : 0, press = p.mode === 'calm' ? 0 : 1;
  // the crowd outside, front row pressed to the glass
  for (let i = 0; i < 9; i++) {
    const x = 600 + i * 90 + 10 * Math.sin(i * 7), y = lerp(760, 1000, press) + 30 * Math.sin(i * 3.1);
    s += zombie({ x, y: y + surge * 20 * Math.sin(tg * 9 + i), s: lerp(0.8, 1.15, press), outfit: ['cashier', 'jogger', 'shopper', 'park', 'nurse', 'janitor', 'guard', 'suit', 'shopper'][i], tilt: (i % 2 ? 8 : -8) + 3 * Math.sin(tg + i), look: 0.05 * Math.sin(tg + i), pose: press ? 'reach' : 'stand', filter: false });
  }
  if (press) for (let i = 0; i < 12; i++) s += mitt(600 + i * 64, 560 + 40 * Math.sin(i * 2.3) + surge * 10 * Math.sin(tg * 12 + i), 90 + 20 * Math.sin(i), 0.55, PAL.zSkin);
  s += set('doors_in', () => S.doorsInside());
  s += rect(910, 250, 100, 46, { rx: 8, fill: '#2B1D21', ...ink(3) }) + text(960, 282, p.locked === false ? 'OPEN' : 'LOCKED', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 18, fill: p.locked === false ? '#9CFF8A' : '#FF6A5A', textAnchor: 'middle' });
  s += nightTint(0.4, '#6E6A8A') + screenGlow(960, 520, 520, 420, '#F2C6A8', 0.25);
  if (surge) s += bang('BOOM!', 1500, 330, lt - 0.3, { size: 150, life: 1.6 });
  return cam(s, { s: push(lt, D, [1.0, 1.05]), ...shake(tg, surge * (0.6 + 0.4 * Math.sin(tg * 3))) }) + hudAt(p.hud);
};

// ---------- security desk and the radio dock ----------
SH.dock = (T, tg, lt, p, D) => {
  let s = set('security', () => S.securityDesk());
  const take = p.mode === 'take' ? ease(ramp(lt, 0.5, D - 0.4)) : 0;
  s += g(S.dockBase(960, 600, 1.0), { filter: 'url(#wobbleSoft)' });
  s += radioProp(875, 560 - take * 300, 0.62, { on: false, led: '#7FD36B' });
  s += circle(875, 640, 6, { fill: '#7FD36B' }) + circle(1045, 640, 6, { fill: '#3A3D42' });
  if (p.mode === 'take') s += g(sleeve(`M0 1080 L${f1(700)} ${f1(560 - take * 300)} L${f1(800)} ${f1(660 - take * 300)} L260 1080 Z`) + mitt(830, 520 - take * 300, -30, 0.9), { filter: 'url(#wobbleSoft)' });
  if (p.mode === 'close') s += g(rect(980, 520, 130, 70, { fill: 'none', stroke: PAL.yellow, strokeWidth: 8, strokeDasharray: '12 10', opacity: f1(ease(ramp(lt, 0.8, 1.2)) * 100) / 100 }), {});
  const c = p.mode === 'wide' ? { s: push(lt, D, [1.0, 1.05]) } : { s: lerp(1.7, 1.8, ease(lt / D)), cx: 960, cy: 560 };
  return cam(s, c) + hudAt(p.hud || { day: 1, time: '11:20 AM', noise: 0, place: 'FRESHWAY · SECURITY' });
};

// ---------- the fire exit and its barricade ----------
SH.exitdoor = (T, tg, lt, p, D) => {
  const stage = p.stage || 'bare', push_ = p.push ? Math.max(0, Math.sin(lt * 3.2)) : 0;
  let s = p.push ? S.fireExit({ stage, open: push_ * 0.6 }) : set(`fire_${stage}`, () => S.fireExit({ stage }));
  if (p.push) for (let i = 0; i < 3; i++) s += mitt(1200, 330 + i * 140, 180, 0.6 * push_ + 0.01, PAL.zSkin);
  if (p.slide) s = g(s, { transform: `translate(${f1(-12 * ease(ramp(lt, 0.2, 0.6)) - 12 * ease(ramp(lt, 1.6, 2.0)))} 0)` });
  const locked = !(p.unlockfx && lt > 1.0) && !p.dark;
  s += circle(1040, 167, 9, { fill: locked ? '#FF4B3A' : '#9CFF8A', ...ink(2) }) + glow(1040, 167, 24, locked ? '#FF4B3A' : '#9CFF8A', 0.8);
  if (p.unlockfx) s += g(rect(820, 600, 280, 80, { rx: 10, fill: '#2B1D21', ...ink(4) }) + label(960, 652, lt > 1.0 ? 'UNLOCKED' : 'LOCKED', 34, lt > 1.0 ? '#9CFF8A' : '#FF6A5A'), { opacity: f1(clamp((lt - 0.2) * 3) * 100) / 100 });
  if (p.hero === 'carry') s += hero({ x: 300 + lt * 120, y: 1000, s: 1.4, pose: 'carry', expr: 'determined', facing: 1, look: 0.3, extra: rect(300 + lt * 120 - 80, 1000 - 4.2 * 84, 160, 110, { rx: 30, fill: '#B88A4E', ...ink(5) }) });
  if (p.hero === 'proud') s += hero({ x: 330, y: 1010, s: 1.45, pose: 'hips', expr: 'smile', facing: 1, look: 0.4, blink: autoBlink(lt), breathe: 0.012 * Math.sin(tg * 2.2) });
  if (p.outside) s += g(rect(1380, 160, 480, 620, { rx: 12, fill: '#2B3446', ...ink(6) }) + text(1620, 210, 'OUTSIDE', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 26, fill: '#9AA8BA', textAnchor: 'middle', letterSpacing: 4 })
    + zombie({ x: 1520, y: 760, s: 0.8, outfit: 'jogger', tilt: 8, look: -0.6, filter: false }) + zombie({ x: 1700, y: 770, s: 0.85, outfit: 'park', tilt: -6, look: -0.5, filter: false }), {});
  if (p.dark) s += nightTint(0.9) + glow(960, 92, 200, '#FF6A5A', 0.35) + screenGlow(960, 500, 400, 400, '#3A4A6A', 0.3);
  else s += nightTint(0.25, '#6E6A8A');
  if (p.clunk) s += bang('CLUNK!', 1430, 300, lt - 0.1, { size: 140, life: 1.3 });
  if (p.push) s += bang('THUD!', 1480, 600, (lt % 1.0) - 0.05, { size: 110, life: 0.6, rot: 6 });
  return cam(s, { s: push(lt, D, [1.0, 1.05]), ...shake(tg, push_ * 0.5) }) + hudAt(p.hud || (p.dark ? { day: 4, time: '3:17 PM', noise: p.push ? 4 : 2, place: 'FRESHWAY · FIRE EXIT' } : null));
};

// ---------- montage beats while you build the wall ----------
SH.montage = (T, tg, lt, p, D) => {
  let s = blurred('stock_open', () => S.stockroom({ open: true })) + nightTint(0.3, '#6E6A8A');
  const w = p.what, x = lerp(200, 1500, lt / D);
  const item = {
    dogfood: rect(-80, -60, 160, 110, { rx: 30, fill: '#B88A4E', ...ink(5) }) + text(0, 8, 'WOOF', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 26, fill: '#7A4A22', textAnchor: 'middle' }),
    water: Array.from({ length: 12 }, (_, i) => rect(-150 + (i % 4) * 75, -170 + Math.floor(i / 4) * 85, 66, 80, { rx: 12, fill: '#BFDDEB', ...ink(3) })).join(''),
    chairs: [0, 1, 2].map((i) => g(path('M-60 0 h120 l10 -90 h-140 z', { fill: '#F2F0EA', ...ink(5) }) + rect(-60, -160, 120, 70, { rx: 10, fill: '#F2F0EA', ...ink(5) }), { transform: `translate(0 ${-i * 40})` })).join(''),
    cart: rect(-130, -120, 260, 140, { rx: 10, fill: 'none', ...ink(7) }) + Array.from({ length: 10 }, (_, i) => rect(-110 + (i % 5) * 46, -110 + Math.floor(i / 5) * 50, 40, 46, { rx: 6, fill: [PAL.red, PAL.yellow, PAL.green][i % 3], ...ink(3) })).join('') + circle(-90, 50, 22, { fill: INK }) + circle(90, 50, 22, { fill: INK }),
  }[w];
  const pose = w === 'water' || w === 'cart' ? 'push' : 'carry';
  const hx = w === 'water' || w === 'cart' ? x - 220 : x;
  s += hero({ x: hx, y: 1010, s: 1.5, pose, expr: 'determined', facing: 1, look: 0.4, blink: autoBlink(lt), tilt: Math.sin(tg * 6) * 2 });
  s += g(item, { transform: `translate(${f1(x + (w === 'dogfood' ? 30 : w === 'chairs' ? 170 : 0))} ${w === 'chairs' ? 900 : w === 'dogfood' ? 790 : 830})${w === 'chairs' ? ' scale(0.8)' : ''}`, filter: 'url(#wobbleSoft)' });
  // the time-lapse clock in the corner
  const ang = tg * 4;
  s += g(circle(1700, 180, 90, { fill: '#F4F0E6', ...ink(6) }) + line(1700, 180, 1700 + Math.cos(ang) * 70, 180 + Math.sin(ang) * 70, ink(6)) + line(1700, 180, 1700 + Math.cos(ang / 12) * 45, 180 + Math.sin(ang / 12) * 45, ink(8)), { filter: 'url(#wobbleSoft)' });
  const time = w === 'cart' ? '3:28 PM' : ['1:10 PM', '4:40 PM', '9:15 PM'][['dogfood', 'water', 'chairs'].indexOf(w)];
  return cam(s, { s: push(lt, D, [1.0, 1.04]) }) + hudAt({ day: w === 'cart' ? 4 : 1, time, noise: 1, place: w === 'cart' ? 'FRESHWAY · STOCKROOM' : 'FRESHWAY · FIRE EXIT' });
};
