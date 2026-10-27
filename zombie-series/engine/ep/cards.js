// Motion-graphics cards, the store blueprint and the crossing plan.
import { W, H, INK, PAL, glow, g, rect, circle, ellipse, line, poly, path, text, ink, rng, zombie } from '../lib.js';
import { icon, smallCaps, big } from '../scenes.js';
import { clamp, lerp, ease, easeOut, back, ramp, f1, cam, push, bang, rings, label, alarmClock, keyring, radioProp } from './kit.js';
import { SH } from './shots_in.js';

const W2 = W / 2;
const cream = () => rect(0, 0, W, H, { fill: PAL.cream });
const dark = () => rect(0, 0, W, H, { fill: PAL.card });
const pop = (inner, age, { x = W2, y = H / 2, d = 0.3, from = 0.7 } = {}) => {
  const k = back(age / d); if (k <= 0.001) return '';
  return g(inner, { transform: `translate(${x} ${y}) scale(${(from + (1 - from) * k).toFixed(3)}) translate(${-x} ${-y})`, opacity: f1(clamp(age / (d * 0.6)) * 100) / 100 });
};
const slideIn = (inner, age, dy = 30) => { const k = easeOut(age / 0.35); if (k <= 0.001) return ''; return g(inner, { transform: `translate(0 ${f1((1 - k) * dy)})`, opacity: f1(clamp(k * 1.4) * 100) / 100 }); };
const tag = (txt, x, y, w = 300, rot = -3) => g(rect(x - w / 2, y - 40, w, 76, { fill: PAL.tag }) + text(x, y + 16, txt, { fontFamily: 'Rubik', fontWeight: 900, fontSize: 52, fill: PAL.card, textAnchor: 'middle', letterSpacing: 4 }), { transform: `rotate(${rot} ${x} ${y})` });

const ICONS = {
  zombie: (x, y) => zombie({ x, y: y + 160, s: 0.75, outfit: 'cashier', tilt: -8 }),
  clock: (x, y) => icon.clock(x, y, 1.4),
  door: (x, y) => g(rect(x - 80, y - 120, 160, 240, { fill: '#8E3B2F', ...ink(6) }) + rect(x - 60, y + 10, 120, 24, { rx: 8, fill: '#C9C3B5', ...ink(4) }) + rect(x - 50, y - 132, 100, 22, { fill: '#C9CDD0', ...ink(4) }), { filter: 'url(#wobbleSoft)' }),
  release: (x, y) => g(rect(x - 120, y - 120, 240, 240, { rx: 20, fill: '#D5D9DC', ...ink(6) }) + rect(x - 30, y - 70, 60, 140, { rx: 14, fill: PAL.red, ...ink(5) }) + text(x, y + 105, 'PUSH', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 28, fill: INK, textAnchor: 'middle' }), { filter: 'url(#wobbleSoft)' }),
  magnet: (x, y) => g(path(`M${x - 90} ${y - 100} v120 a90 90 0 0 0 180 0 v-120 h-60 v120 a30 30 0 0 1 -60 0 v-120 z`, { fill: PAL.red, ...ink(6) }) + rect(x - 90, y - 130, 60, 40, { fill: '#C9CDD0', ...ink(5) }) + rect(x + 30, y - 130, 60, 40, { fill: '#C9CDD0', ...ink(5) }), { filter: 'url(#wobbleSoft)' }),
  bolt: (x, y) => g(path(`M${x + 20} ${y - 140} L${x - 70} ${y + 20} h60 l-30 120 l110 -170 h-60 z`, { fill: PAL.yellow, ...ink(6) }), { filter: 'url(#wobbleSoft)' }),
  exit: (x, y) => g(rect(x - 150, y - 60, 300, 120, { rx: 12, fill: '#3DBE6A', ...ink(6) }) + text(x, y + 26, 'EXIT', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 76, fill: '#EFFFF2', textAnchor: 'middle' }), { filter: 'url(#wobbleSoft)' }),
  snow: (x, y) => g([0, 60, 120].map((a) => line(x - Math.cos(a * Math.PI / 180) * 110, y - Math.sin(a * Math.PI / 180) * 110, x + Math.cos(a * Math.PI / 180) * 110, y + Math.sin(a * Math.PI / 180) * 110, { stroke: '#5E8FB5', strokeWidth: 18, strokeLinecap: 'round' })).join(''), { filter: 'url(#wobbleSoft)' }),
  note: (x, y) => text(x, y + 60, '♫', { fontFamily: 'Rubik', fontSize: 200, fill: '#F3EBDD', textAnchor: 'middle' }),
};

SH.card = (T, tg, lt, p, D) => {
  const k = p.kind;
  if (k === 'problem') {
    let s = cream() + pop(ICONS[p.icon || 'zombie'](W2, 300), lt - 0.05, { y: 300 });
    s += slideIn(smallCaps(W2, 560, `PROBLEM ${p.n}`, 34), lt - 0.15) + slideIn(big(W2, 700, p.title, 140), lt - 0.25) + slideIn(smallCaps(W2, 790, p.sub, 36, INK), lt - 0.4);
    if (p.countdown) { const left = 19 * 60 - Math.floor(lt * 7); s += pop(g(rect(W2 - 170, 840, 340, 110, { rx: 14, fill: '#2B1D21', ...ink(4) }) + text(W2, 920, `${Math.floor(left / 60)}:${String(((left % 60) + 60) % 60).padStart(2, '0')}`, { fontFamily: 'Rubik', fontWeight: 900, fontSize: 80, fill: '#FF6A5A', textAnchor: 'middle' })), lt - 0.5, { y: 895 }); }
    if (p.stamp) s += pop(g(rect(W2 + 160, 360, 520, 150, { rx: 14, fill: 'none', stroke: '#2F7A4F', strokeWidth: 14 }) + text(W2 + 420, 470, p.stamp, { fontFamily: 'Rubik', fontWeight: 900, fontSize: 110, fill: '#2F7A4F', textAnchor: 'middle', letterSpacing: 6 }), { transform: `rotate(-10 ${W2 + 420} 435)`, opacity: 0.9 }), lt - 0.2, { x: W2 + 420, y: 435, from: 2.0, d: 0.25 });
    return cam(s, { s: push(lt, D, [1.0, 1.03]) });
  }
  if (k === 'rule') {
    let s = dark();
    const kk = ramp(lt, 0.0, 0.18), sc = kk < 1 ? lerp(1.8, 1, kk) : 1 + 0.04 * Math.exp(-(lt - 0.18) * 8) * Math.sin((lt - 0.18) * 40);
    s += g(tag(`RULE ${p.n}`, W2, 330), { transform: `translate(${W2} 330) scale(${sc.toFixed(3)}) translate(${-W2} -330)`, opacity: f1(clamp(kk * 3) * 100) / 100 });
    p.lines.forEach((L, i) => { s += slideIn(big(W2, 560 + i * 160, L, 130, '#F3EBDD'), lt - 0.5 - i * 0.35); });
    s += pop(ICONS[p.icon || 'note'](W2, 860), lt - 1.0, { y: 900 });
    return cam(s, { s: push(lt, D, [1.0, 1.03]) });
  }
  if (k === 'fact') {
    let s = cream();
    s += slideIn(smallCaps(W2, 200, 'FACT', 30, PAL.red), lt - 0.05);
    s += pop(ICONS[p.icon](W2 - 520, 520), lt - 0.15, { x: W2 - 520, y: 520 });
    s += pop(big(W2 + 160, 600, p.big, Math.min(300, 1700 / Math.max(2, p.big.length))), lt - 0.25, { x: W2 + 160, y: 520 }) + slideIn(smallCaps(W2 + 160, 690, p.unit, 52, INK), lt - 0.4);
    s += slideIn(smallCaps(W2, 840, p.note, 32, INK), lt - 0.6) + slideIn(text(W2, 920, `Source: ${p.src}`, { fontFamily: 'Rubik', fontWeight: 500, fontSize: 22, fill: '#8E8576', textAnchor: 'middle' }), lt - 0.8);
    return cam(s, { s: push(lt, D, [1.0, 1.03]) });
  }
  if (k === 'day') {
    let s = dark() + pop(big(W2, 560, `DAY ${p.n}`, 200, '#F3EBDD'), lt - 0.05, { y: 500 }) + slideIn(smallCaps(W2, 660, p.title, 40, PAL.tag), lt - 0.3);
    return cam(s, { s: push(lt, D, [1.0, 1.04]) });
  }
  if (k === 'supplies') {
    let s = cream() + smallCaps(W2, 150, `SUPPLIES  ·  DAY ${p.day}`, 40, INK);
    p.rows.forEach(([name, val, note], i) => {
      const y = 330 + i * 230;
      s += slideIn(text(420, y, name, { fontFamily: 'Rubik', fontWeight: 700, fontSize: 38, fill: '#6B5F55' }) + text(1500, y, val, { fontFamily: 'Rubik', fontWeight: 900, fontSize: 62, fill: name === 'Batteries' ? PAL.red : INK, textAnchor: 'end' }) + (note ? text(1500, y + 54, note, { fontFamily: 'Rubik', fontWeight: 800, fontSize: 24, fill: PAL.red, textAnchor: 'end', letterSpacing: 3 }) : '') + line(420, y + 90, 1500, y + 90, { stroke: '#D9CDB2', strokeWidth: 3 }), lt - 0.15 - i * 0.25);
    });
    if (p.told) s += pop(g(rect(1200, 880, 420, 100, { rx: 14, fill: 'none', stroke: PAL.red, strokeWidth: 8 }) + label(1410, 948, 'TOLD TO DALE', 40, PAL.red), { transform: 'rotate(-6 1410 930)' }), lt - 0.8, { x: 1410, y: 930, from: 1.8, d: 0.25 });
    return cam(s, { s: push(lt, D, [1.0, 1.03]) });
  }
  if (k === 'backpack') {
    let s = cream() + smallCaps(W2, 150, 'BACKPACK  ·  DAY 6', 40, INK);
    s += g(path('M560 360 q0 -120 140 -120 h120 q140 0 140 120 v520 q0 60 -60 60 h-280 q-60 0 -60 -60 z', { fill: '#7A3B33', ...ink(7) }) + rect(600, 520, 320, 200, { rx: 30, fill: '#8E4A40', ...ink(5) }), { filter: 'url(#wobbleSoft)' });
    p.items.forEach((it, i) => { s += slideIn(text(1080, 420 + i * 160, it, { fontFamily: 'Rubik', fontWeight: 900, fontSize: 54, fill: i === 2 ? PAL.red : INK }), lt - 0.3 - i * 0.55); });
    return cam(s, { s: push(lt, D, [1.0, 1.03]) });
  }
  if (k === 'rules' || k === 'promise_rules') {
    let s = dark();
    const R = [['THEY HEAR. THEY DON\'T SEE.'], ['MUSIC IS A DINNER BELL.'], ['COUNT THE RADIOS.'], ['NEVER TELL ANYONE WHAT YOU HAVE.']];
    s += smallCaps(W2, 150, k === 'rules' ? 'WHAT YOU KNOW  ·  DAY 7' : 'THIS WEEK', 36, '#B9AE97');
    for (let i = 0; i < 4; i++) {
      const y = 290 + i * 190, shown = k === 'promise_rules' ? lt > 1.2 + i * 0.25 : i < p.show, cur = k === 'rules' && i === p.show - 1;
      s += g(rect(250, y - 50, 230, 70, { fill: shown ? PAL.tag : '#3A3236' }) + text(365, y + 4, `RULE ${i + 1}`, { fontFamily: 'Rubik', fontWeight: 900, fontSize: 40, fill: PAL.card, textAnchor: 'middle', letterSpacing: 3 }), { transform: `rotate(-2 365 ${y})`, opacity: k === 'promise_rules' ? f1(clamp((lt - 1.2 - i * 0.25) * 4) * 100) / 100 : 1 });
      const txt = k === 'promise_rules' ? '? ? ?' : shown ? R[i][0] : '';
      if (txt) s += (cur ? slideIn : (x) => x)(text(540, y + 10, txt, { fontFamily: 'Rubik', fontWeight: 900, fontSize: 56, fill: cur ? '#F3EBDD' : '#B9AE97' }), lt - 0.1);
    }
    return cam(s, { s: push(lt, D, [1.0, 1.03]) });
  }
  if (k === 'schedule') {
    let s = cream() + smallCaps(W2, 160, 'FRESHWAY · DAILY SCHEDULE', 36, INK);
    s += line(260, 560, 1660, 560, ink(8)) + label(260, 620, '6:59', 36, '#6B5F55') + label(1660, 620, '7:00', 44, PAL.red);
    const items = [['💡', 'LIGHTS ON'], ['♫', 'MUSIC ON'], ['🔓', 'DOORS UNLOCK']];
    items.forEach(([ic, t], i) => {
      const x = 640 + i * 420, a = lt - 0.2 - i * 0.7;
      s += pop(g(circle(x, 420, 90, { fill: i === 2 ? PAL.red : PAL.yellow, ...ink(6) }) + text(x, 450, i === 0 ? 'ON' : i === 1 ? '♫' : 'OPEN', { fontFamily: 'Rubik', fontWeight: 900, fontSize: i === 1 ? 90 : 46, fill: INK, textAnchor: 'middle' })), a, { x, y: 420 })
        + slideIn(label(x, 760, t, 40, INK), a - 0.1);
    });
    return cam(s, { s: push(lt, D, [1.0, 1.03]) });
  }
  if (k === 'comment') {
    let s = rect(0, 0, W, H, { fill: '#F2EEE6' });
    s += pop(g(rect(360, 300, 1200, 420, { rx: 30, fill: '#FFFFFF', ...ink(5) }) + circle(470, 410, 50, { fill: PAL.phones, ...ink(4) }) + text(560, 400, '@you', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 34, fill: INK }) + text(560, 440, 'just now', { fontFamily: 'Rubik', fontWeight: 500, fontSize: 24, fill: '#8E8576' })
      + text(440, 540, 'What would you have thrown?', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 54, fill: INK }) + text(440, 630, '♥  1.2K      REPLY', { fontFamily: 'Rubik', fontWeight: 600, fontSize: 30, fill: '#6B5F55' })), lt - 0.1, { y: 510 });
    return s;
  }
  if (k === 'twowaves') {
    let s = dark();
    const wave = (y, col, delay, amp) => { let o = ''; for (let i = 0; i < 70; i++) { const tt = lt - delay, a = tt > 0 && tt < 2.0 ? amp * Math.abs(Math.sin(tt * 13 + i * 0.6) * Math.sin(tt * 5 + i * 0.27)) : 0.04; o += rect(260 + i * 20, y - a * 110, 10, a * 220 + 4, { rx: 5, fill: col }); } return o; };
    s += label(260, 300, 'YOUR RADIO', 34, '#F2A73B', 'start', 5) + wave(420, '#F2A73B', 0.2, 1.0);
    s += slideIn(label(260, 640, 'BEHIND YOU · 0.3 S LATER', 34, '#8FB3D5', 'start', 5), lt - 1.4) + (lt > 1.4 ? wave(760, '#8FB3D5', 1.7, 0.5) : '');
    return s;
  }
  if (k === 'end') {
    let s = dark();
    s += pop(big(W2, 480, 'DAY 8', 200, '#F3EBDD'), lt - 0.2, { y: 420 });
    s += slideIn(smallCaps(W2, 590, 'EPISODE 2  ·  THE MALL', 44, PAL.tag), lt - 0.7);
    s += slideIn(smallCaps(W2, 680, 'WHO SETS THE ALARM?', 30, '#B9AE97'), lt - 1.3);
    s += pop(g(rect(W2 - 220, 780, 440, 110, { rx: 16, fill: PAL.red, ...ink(4) }) + text(W2, 852, 'SUBSCRIBE', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 52, fill: '#FFF', textAnchor: 'middle', letterSpacing: 4 })), lt - 2.0, { y: 835 });
    if (lt > D - 0.8) s += rect(0, 0, W, H, { fill: '#000', opacity: f1(ease(ramp(lt, D - 0.8, D)) * 100) / 100 });
    return s;
  }
  return cream();
};

// ---------- the blueprint (day 1) and the plan (day 6) ----------
SH.map = (T, tg, lt, p, D) => {
  let s = rect(0, 0, W, H, { fill: '#EDE3CC' }) + rect(0, 0, W, H, { fill: 'url(#graph)' });
  const X = 260, Y = 150, w = 1400, h = 760;
  const lbl = (x, y, t, col = INK, size = 20) => text(x, y, t, { fontFamily: 'Rubik', fontWeight: 800, fontSize: size, fill: col, textAnchor: 'middle', letterSpacing: 2 });
  if (p.mode === 'blueprint') {
    s += label(260, 100, 'FRESHWAY · FACILITY MANUAL · FLOOR PLAN', 28, INK, 'start', 4);
    let m = rect(X, Y, w, h, { fill: '#F7EFDC', ...ink(7) });
    const rv = { aisles: 0, exits: 1, doors: 2, firezoom: 3 }[p.reveal] ?? 0;
    // aisles draw in one by one
    for (let i = 0; i < 14; i++) { const k = rv > 0 ? 1 : clamp((lt - 0.2 - i * 0.08) * 4); m += rect(X + 200 + i * 75, Y + 200, 36, 380 * k, { fill: '#D9CDB2', ...ink(3) }) + (k > 0.9 ? lbl(X + 218 + i * 75, Y + 190, String(i + 1), '#6B5F55', 16) : ''); }
    m += rect(X + 20, Y + 20, 330, 110, { fill: '#C8D8DE', ...ink(4) }) + lbl(X + 185, Y + 70, 'STOCKROOM'), m += rect(X + 30, Y + 82, 150, 40, { fill: '#9DB6C8', ...ink(3) }) + lbl(X + 105, Y + 110, 'FREEZER', '#3E6E9A', 14);
    m += rect(X + w - 260, Y + 20, 230, 110, { fill: '#E3D6C1', ...ink(4) }) + lbl(X + w - 145, Y + 85, 'OFFICE');
    m += circle(X + w - 200, Y + 75, 12, { fill: PAL.zSkin, ...ink(3) }) + circle(X + 140, Y + 102, 9, { fill: PAL.zSkin, ...ink(2) }) + circle(X + 160, Y + 98, 9, { fill: PAL.zSkin, ...ink(2) }) + circle(X + 120, Y + 98, 9, { fill: PAL.zSkin, ...ink(2) });
    m += rect(X, Y + h - 110, w, 110, { fill: '#CFE3EA', ...ink(5) }) + lbl(X + w / 2, Y + h - 45, 'FRONT ENTRANCE · STEEL SHUTTERS', '#3E6E9A', 24);
    m += rect(X + w - 520, Y + 560, 180, 80, { fill: '#E9E2CF', ...ink(3) }) + lbl(X + w - 430, Y + 608, 'SECURITY', '#6B5F55', 16);
    if (rv >= 1) {
      const a = rv > 1 ? 1 : lt;
      m += slideIn(rect(X + 380, Y - 30, 240, 40, { fill: '#9AA0A6', ...ink(4) }) + lbl(X + 500, Y - 2, 'LOADING DOCK', '#2B2F33', 16), a - 0.6);
      m += slideIn(rect(X + w - 30, Y + 250, 34, 110, { fill: '#3DBE6A', ...ink(4) }) + lbl(X + w + 90, Y + 312, 'FIRE EXIT', '#2E7D4F', 20), a - 1.2);
      m += slideIn(rect(X + 680, Y + 40, 70, 70, { fill: '#7E786C', ...ink(4) }) + lbl(X + 715, Y + 135, 'ROOF LADDER', '#6B5F55', 14), a - 2.0);
    }
    if (rv >= 2) {
      const a = rv > 2 ? 9 : lt;
      m += slideIn(g(rect(X + 200, Y + h - 150, w - 400, 30, { fill: 'url(#graph)', stroke: '#6B5F55', strokeWidth: 3 })), a - 0.3);
      m += slideIn(lbl(X + 500, Y - 40, 'ROLL-UP DOOR', '#6B5F55', 14), a - 1.0);
      m += slideIn(g(rect(X + w - 70, Y + 260, 30, 90, { fill: '#C9CDD0', ...ink(3) }) + lbl(X + w - 140, Y + 240, 'MAGLOCK', PAL.red, 16)), a - 1.8);
    }
    s += g(m, { filter: 'url(#wobbleSoft)' });
    if (rv === 3) s += rings(X + w - 13, Y + 305, tg, { color: PAL.red, max: 160, period: 1.2 });
    const zoom = rv === 3 ? { s: lerp(1.0, 1.9, ease(lt / D)), cx: X + w - 13, cy: Y + 305 } : { s: push(lt, D, [1.0, 1.04]) };
    return cam(s, zoom);
  }
  // the plan: from the roof ladder at the back, across the lot, to the mall's side door
  s += label(260, 100, 'THE PLAN · DAY 6', 28, INK, 'start', 4);
  let m = '';
  m += rect(200, 650, 520, 320, { fill: '#F7EFDC', ...ink(6) }) + lbl(460, 820, 'FRESHWAY', INK, 40);
  m += rect(1280, 120, 460, 300, { fill: '#E3D6C1', ...ink(6) }) + lbl(1510, 280, 'BROOKFIELD MALL', INK, 30);
  m += rect(200, 470, 1540, 150, { fill: '#D9D2C2', stroke: '#8E8576', strokeWidth: 3, strokeDasharray: '14 10' }) + lbl(970, 560, 'PARKING LOT', '#8E8576', 26);
  const r = rng(8);
  const rv = { lot: 0, decoys: 1, route: 2, staffdoor: 3 }[p.reveal] ?? 0;
  const drift = rv >= 1 ? ease(ramp(lt, 0.8, D)) * (rv === 1 ? 1 : 0) + (rv >= 2 ? 1 : 0) : 0;
  for (let i = 0; i < 70; i++) { const x0 = 260 + r() * 1300, y0 = 480 + r() * 130; m += circle(lerp(x0, 1650 + (i % 6) * 14, drift * (rv === 3 ? 0 : 0.85)), lerp(y0, 600 + (i % 5) * 14, drift * (rv === 3 ? 0 : 0.6)), 9, { fill: PAL.zSkin, ...ink(2) }); }
  if (rv >= 1 && rv < 3) { m += alarmClock(1700, 640, 0.35, {}); m += rings(1700, 640, tg, { color: PAL.red, max: 200, period: 1.0 }); }
  if (rv >= 2) {
    const k = rv === 2 ? ease(ramp(lt, 0.2, D * 0.8)) : 1;
    m += path(`M700 680 C800 600 1000 520 ${lerp(700, 1280, k)} ${lerp(680, 400, k)}`, { fill: 'none', stroke: INK, strokeWidth: 7, strokeDasharray: '4 16', strokeLinecap: 'round' });
    m += g(rect(930, 400, 200, 60, { rx: 8, fill: '#FBF6EA', ...ink(4) }) + lbl(1030, 440, '80 M · 90 S', INK, 24), { opacity: f1(k * 100) / 100 });
  }
  if (rv === 3) {
    m += circle(720, 820, 30, { fill: PAL.red, ...ink(5) }) + rings(720, 820, tg, { color: PAL.red, max: 120, period: 0.9 });
    m += g(rect(740, 860, 220, 50, { rx: 8, fill: PAL.red, ...ink(4) }) + lbl(850, 895, 'STAFF DOOR', '#FFF', 22), {});
  }
  m += circle(700, 680, 24, { fill: PAL.red, ...ink(5) }) + rect(560, 700, 110, 46, { rx: 8, fill: PAL.red, ...ink(4) }) + lbl(615, 732, 'YOU', '#FFF', 26);
  s += g(m, { filter: 'url(#wobbleSoft)' });
  return cam(s, { s: push(lt, D, [1.0, 1.05]), cx: 960, cy: 560 });
};

// ---------- episode title card (cold open ends on it) ----------
SH.ep_title = (T, tg, lt, p, D) => {
  let s = rect(0, 0, W, H, { fill: '#0E0C0C' });
  const on = (x) => (x > 0.05 && x < 0.12) || (x > 0.2 && x < 0.26) || x > 0.38;
  const k = on(lt) ? 1 : 0.08, gl = 0.85 + 0.15 * Math.sin(tg * 50) * (lt < 1 ? 1 : 0.2);
  s += glow(W2, 480, 300, '#F08A24', 0.28 * k * gl);
  s += text(W2, 520, 'LAST LIGHT', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 190, letterSpacing: 18, fill: k > 0.5 ? '#F7E3C8' : '#3A302A', textAnchor: 'middle' });
  const k2 = ease(ramp(lt, 0.9, 1.6));
  s += g(smallCaps(W2, 640, 'EPISODE 1  ·  THE NIGHT SHIFT', 38, '#EDB344') + smallCaps(W2, 700, 'ZOMBIE OUTBREAK: 30 DAYS LOCKED INSIDE A SUPERMARKET', 22, '#8E8576'), { opacity: k2.toFixed(2) });
  s += rect(0, 0, W, H, { fill: '#000', opacity: f1(ease(ramp(lt, D - 0.7, D)) * 100) / 100 });
  return s;
};
