// Episode shot templates: roof, parking lot, mall, POV across the lot, the run back, camp, radio and prop close-ups.
import { W, H, INK, PAL, glow, hero, zombie, crowd, grade, g, rect, circle, ellipse, line, poly, path, text, ink, layer, rng } from '../lib.js';
import { clamp, lerp, ease, easeOut, easeIn, back, ramp, wob, f1, keys, autoBlink, cam, push, shake, nightTint, screenGlow, darkness,
  letterbox, quote, bang, rings, hudAt, sleeve, mitt, radioProp, keyring, alarmClock, label, set } from './kit.js';
import * as S from './sets.js';
import { SH, capsAt } from './shots_in.js';
import { aisle } from '../scenes.js';

const blurred = (key, make) => layer(key + '_soft', () => g(make(), { filter: 'url(#softS)' }));
const tintOf = (time) => (time === 'night' ? nightTint(0.55) : time === 'sunset' ? grade('dusk') : '');

// ---------- roof ----------
SH.roof = (T, tg, lt, p, D) => {
  const time = p.time || 'sunset';
  let s = set(`roof_${time}`, () => S.roofSet({ time }));
  const hp = p.hero;
  if (hp === 'hatch') { const up = easeOut(ramp(lt, 0.2, 2.2)); s += g(hero({ x: 820, y: lerp(1180, 960, up), s: 1.2, pose: 'climb', expr: 'worried', facing: 1, look: 0.5, blink: autoBlink(lt) }), {}) + poly([[700, 900], [940, 900], [980, 1000], [660, 1000]], { fill: '#3A3836', opacity: 0.0 }); }
  if (hp === 'edge') s += hero({ x: 520, y: 760, s: 1.0, pose: 'stand', expr: 'worried', facing: 1, look: 0.2, blink: autoBlink(lt), breathe: 0.01 * Math.sin(tg * 2.2) });
  if (hp === 'cart') {
    const x = lerp(300, 900, ease(lt / Math.max(D, 0.1)));
    s += hero({ x, y: 960, s: 1.25, pose: 'push', expr: 'determined', facing: 1, look: 0.3 });
    s += g(rect(x + 120, 760, 230, 130, { rx: 8, fill: 'none', ...ink(7) }) + Array.from({ length: 10 }, (_, i) => rect(x + 135 + (i % 5) * 42, 770 + Math.floor(i / 5) * 48, 38, 44, { rx: 6, fill: [PAL.red, PAL.yellow, PAL.green][i % 3], ...ink(3) })).join('') + circle(x + 150, 935, 20, { fill: INK }) + circle(x + 320, 935, 20, { fill: INK }), { filter: 'url(#wobbleSoft)' });
  }
  if (hp === 'backpack') { const u = 78; s += rect(820 - 0.95 * u, 960 - 4.3 * u, 1.9 * u, 2.3 * u, { rx: 20, fill: '#7A3B33', ...ink(5) }); s += hero({ x: 820, y: 960, s: 1.3, pose: 'stand', expr: 'determined', facing: 1, look: 0.4, blink: autoBlink(lt), breathe: 0.012 * Math.sin(tg * 2.2), extra: line(820 - 0.35 * u, 960 - 4.1 * u, 820 - 0.42 * u, 960 - 2.3 * u, { stroke: '#5A2A24', strokeWidth: 14, strokeLinecap: 'round' }) + line(820 + 0.35 * u, 960 - 4.1 * u, 820 + 0.42 * u, 960 - 2.3 * u, { stroke: '#5A2A24', strokeWidth: 14, strokeLinecap: 'round' }) }); }
  if (hp === 'throw') {
    const ph = (lt % 1.1) / 1.1;
    s += hero({ x: 820, y: 960, s: 1.3, pose: ph < 0.5 ? 'throw' : 'point', expr: 'determined', facing: 1, look: 0.6 });
    for (let i = 0; i < 3; i++) { const k = ((lt - i * 1.1) / 1.6); if (k > 0 && k < 1) s += alarmClock(lerp(940, 1700 - i * 120, k), lerp(720, 600, k) - Math.sin(k * Math.PI) * 300, lerp(0.35, 0.12, k), {}); }
  }
  if (hp === 'ladder') { const dn = ease(ramp(lt, 0.3, D)); s += hero({ x: 1820, y: lerp(900, 1180, dn), s: 1.1, pose: 'climb', expr: 'worried', facing: -1, look: -0.3 }); }
  s += tintOf(time);
  if (time === 'night') s += screenGlow(1450, 300, 120, 80, '#FFD98A', 0.0);
  if (time === 'sunset') s += screenGlow(420, 480, 500, 340, '#FFC98A', 0.35);
  if (p.mall && time === 'night') s += glow(1060 + 6 * 0.95 * 80 + 30, 200 + 95 * 0.95 + 25, 40, '#FFD98A', 0.6);
  return cam(s, { s: push(lt, D, [1.0, 1.06]), cx: 960, cy: 600 }) + hudAt(p.hud);
};

// ---------- the parking lot, wide from above ----------
const CROWD = (() => { const r = rng(77), a = []; for (let i = 0; i < 160; i++) a.push({ x: 60 + r() * 1800, y: 520 + r() * 470, ph: r() * 6.28, c: Math.floor(r() * 9), sp: 0.7 + r() * 0.6 }); return a.sort((p, q) => p.y - q.y); })();
SH.lot = (T, tg, lt, p, D) => {
  const time = p.time || (p.mode === 'dawn' ? 'sunset' : 'night');
  let s = set(`lot_${time}`, () => S.lotSet({ time }));
  const corner = [1820, 560];
  const cols = ['#8C8C86', '#2E3D55', '#3B3F48', '#C76A83', '#7C6A8E', '#8A7A4E', '#6FA3A6', '#A65F4A', '#596471'];
  const mv = p.mode === 'empty' ? ease(lt / D) : p.mode === 'dying' ? 1 : p.mode === 'return' ? 1 - ease(lt / D) * 0.6 : 0;
  const turnK = p.mode === 'turn' ? ease(ramp(lt, 0.3, D)) : (p.mode === 'empty' || p.mode === 'dying') ? 1 : p.mode === 'return' ? 0 : 0;
  let crowdS = '';
  for (const c of CROWD) {
    const tx = lerp(c.x, corner[0] - 200 + (c.x % 300), mv * 0.85), ty = lerp(c.y, corner[1] + 40 + (c.y % 200) * 0.6, mv * 0.85);
    const sc = 0.12 + (ty - 500) / 500 * 0.16, u = 60 * sc;
    const walk = mv > 0 && mv < 1 ? Math.sin(tg * 5 * c.sp + c.ph) * 6 : 0;
    const lean = lerp((c.ph - 3) * 3, 14, turnK) + walk;
    crowdS += g(rect(tx - 0.6 * u, ty - 4.2 * u, 1.2 * u, 2.1 * u, { rx: 0.25 * u, fill: cols[c.c], stroke: INK, strokeWidth: 2.5 }) + line(tx - 0.25 * u, ty - 2.2 * u, tx - 0.3 * u, ty, { stroke: INK, strokeWidth: 3 }) + line(tx + 0.25 * u, ty - 2.2 * u, tx + 0.3 * u, ty, { stroke: INK, strokeWidth: 3 })
      + circle(tx, ty - 5.15 * u, u, { fill: PAL.zSkin, stroke: INK, strokeWidth: 2.5 }), { transform: `rotate(${f1(lean)} ${f1(tx)} ${f1(ty)})` });
  }
  s += crowdS;
  if (p.decoys) {
    const n = p.mode === 'dying' ? Math.max(0, 6 - Math.floor(lt / D * 6.5)) : p.decoys;
    for (let i = 0; i < n; i++) s += rings(corner[0] - 120 - i * 60, corner[1] + 20 + (i % 2) * 40, tg + i * 0.3, { color: '#FFE27A', max: 200, period: 1.0, op: 0.7, width: 5 });
  }
  if (p.mode === 'count') {
    const k = ease(ramp(lt, 0.2, D - 0.5)), n = Math.round(k * (p.count || 212));
    s += g(rect(1480, 860, 380, 150, { rx: 14, fill: '#FBF6EA', ...ink(5) }) + label(1670, 950, String(n), 90, PAL.red) + label(1670, 995, 'COUNTED', 18, '#6B5F55', 'middle', 6), { filter: 'url(#wobbleSoft)' });
  }
  s += time === 'night' ? nightTint(0.6) : time === 'sunset' ? grade('dusk') + screenGlow(420, 300, 600, 300, '#FFC98A', 0.3) : '';
  if (p.mode === 'dawn') s += screenGlow(960, 200, 900, 300, '#F2C6A8', 0.35);
  for (const lx of [300, 980, 1660]) if (time === 'night') s += glow(lx, 470, 70, '#FFB866', 0.6) + screenGlow(lx, 900, 200, 80, '#FFB866', 0.18, 'softS');
  return cam(s, { s: push(lt, D, [1.0, 1.06]), cx: 960, cy: 600 }) + hudAt(p.hud);
};

// ---------- Brookfield Mall across the street ----------
SH.mall = (T, tg, lt, p, D) => {
  const time = p.time || 'sunset';
  let s = set(`mallwide_${time}`, () => g(S.sky(time) + S.cityBand(time) + S.mallFacade({ time, x: 380, y: 150, k: 1.5 }) + rect(0, 780, W, 300, { fill: time === 'night' ? '#2E323C' : '#5E616A' }), { filter: 'url(#wobble)' }));
  const wx = 380 + 30 * 1.5 + 6 * 80 * 1.5 + 28 * 1.5, wy = 150 + 95 * 1.5 + 25 * 1.5;   // centre of the lit window
  if (p.empty) {
    // inside the window: a desk lamp on a timer, an empty chair
    s += g(rect(wx - 40, wy - 36, 80, 72, { fill: '#F6D79A' }) + rect(wx - 30, wy + 6, 60, 8, { fill: '#7A5C40' }) + line(wx + 16, wy + 6, wx + 10, wy - 16, { stroke: INK, strokeWidth: 3 }) + poly([[wx + 2, wy - 16], [wx + 20, wy - 16], [wx + 24, wy - 26], [wx - 2, wy - 26]], { fill: '#E9B93E', stroke: INK, strokeWidth: 2 }) + rect(wx - 26, wy - 4, 16, 18, { fill: '#5E6B78', stroke: INK, strokeWidth: 2 }), {});
  }
  const lightOn = p.light !== 'off';
  if (lightOn) s += glow(wx, wy, 70, '#FFD98A', 0.65 + 0.05 * Math.sin(tg * 2));
  s += tintOf(time);
  if (p.dream) s += screenGlow(wx, wy, 700, 500, '#FFD9A0', 0.35) + rect(0, 0, W, H, { fill: '#FFE7C2', opacity: 0.12 });
  const z = p.zoom ?? 0;
  const target = lerp(1.0, 3.2, z), from = z >= 1 ? 2.4 : 1.0;
  return cam(s, { s: z ? lerp(from, target, ease(lt / D)) : push(lt, D, [1.0, 1.05]), cx: z ? wx : 960, cy: z ? wy : 500 });
};

SH.skyline = (T, tg, lt, p, D) => {
  let s = set('skyline', () => S.skyline());
  for (let i = 0; i < 3; i++) { const k = ((tg * 0.15 + i / 3) % 1); s += ellipse(1520 + i * 40, 250 - k * 180, 40 + k * 90, 30 + k * 60, { fill: '#F2F0EA', opacity: f1((1 - k) * 0.8 * 100) / 100, filter: 'url(#softS)' }); }
  return cam(s, { s: push(lt, D, [1.0, 1.05]), cx: 1300, cy: 500 }) + hudAt({ day: 1, time: '11:42 AM', noise: 0, place: 'FRESHWAY · ROOF' });
};

// ---------- the cart off the roof ----------
SH.cart = (T, tg, lt, p, D) => {
  let s = set('cart_side', () => {
    let o = S.sky('day') + S.cityBand('day');
    o += rect(0, 300, 760, 640, { fill: '#B7AE9C', ...ink(6) }) + rect(0, 280, 780, 40, { fill: '#8C8578', ...ink(5) }) + rect(0, 940, W, 140, { fill: '#5E616A' });
    o += rect(120, 420, 520, 200, { fill: '#3E6E5A', ...ink(5) }) + text(380, 545, 'FRESHWAY', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 70, fill: '#F5EFE0', textAnchor: 'middle', letterSpacing: 6 });
    return g(o, { filter: 'url(#wobble)' });
  });
  const ph = p.phase;
  if (ph === 'push') {
    const x = lerp(250, 640, ease(lt / D));
    s += hero({ x: x - 200, y: 282, s: 0.8, pose: 'push', expr: 'determined', facing: 1, look: 0.3 });
    s += g(rect(x - 60, 180, 150, 90, { rx: 8, fill: 'none', ...ink(6) }) + Array.from({ length: 6 }, (_, i) => rect(x - 50 + (i % 3) * 46, 186 + Math.floor(i / 3) * 40, 40, 38, { rx: 5, fill: [PAL.red, PAL.yellow, PAL.green][i % 3], ...ink(2) })).join('') + circle(x - 40, 274, 12, { fill: INK }) + circle(x + 70, 274, 12, { fill: INK }), { filter: 'url(#wobbleSoft)' });
  } else {
    const fall = easeIn(ramp(lt, 0.0, 0.55)), hit = lt > 0.55;
    const cx = lerp(720, 980, ramp(lt, 0, 0.55)), cy = lerp(220, 900, fall), rot = lerp(0, 120, ramp(lt, 0, 0.55));
    if (!hit) s += g(rect(-75, -45, 150, 90, { rx: 8, fill: 'none', ...ink(6) }) + Array.from({ length: 6 }, (_, i) => rect(-65 + (i % 3) * 46, -40 + Math.floor(i / 3) * 40, 40, 38, { rx: 5, fill: [PAL.red, PAL.yellow, PAL.green][i % 3], ...ink(2) })).join(''), { transform: `translate(${f1(cx)} ${f1(cy)}) rotate(${f1(rot)})`, filter: 'url(#wobbleSoft)' });
    else {
      const k = easeOut(ramp(lt, 0.55, 1.6));
      s += g(path('M880 940 l60 -60 l90 10 l70 -40 l40 90 z', { fill: 'none', ...ink(7) }), { filter: 'url(#wobbleSoft)' });
      for (let i = 0; i < 18; i++) { const a = -Math.PI * (0.1 + 0.8 * (i / 18)), d = k * (120 + (i * 37) % 260); s += rect(980 + Math.cos(a) * d * 1.6, 930 + Math.sin(a) * d * (1 - k) * 1.2 + k * 10, 34, 40, { rx: 5, fill: [PAL.red, PAL.yellow, PAL.green][i % 3], ...ink(3), transform: `rotate(${f1(i * 40 * k)} ${f1(980 + Math.cos(a) * d * 1.6)} 930)` }); }
      s += ellipse(980, 940, 260 * k + 40, 70 * k + 10, { fill: '#C9C3B5', opacity: f1((1 - k) * 0.6 * 100) / 100, filter: 'url(#softS)' });
      s += bang('CRASH!', 1260, 620, lt - 0.55, { size: 190, life: 1.8 });
    }
  }
  return cam(s, { s: ph === 'push' ? push(lt, D, [1.0, 1.04]) : 1.0, ...shake(tg, ph === 'crash' && lt > 0.55 && lt < 1.1 ? 1.4 : 0) }) + hudAt({ day: 4, time: '3:33 PM', noise: ph === 'crash' && lt > 0.55 ? 5 : 2, place: 'FRESHWAY · ROOF' });
};

// ---------- the loading dock from outside ----------
SH.dockout = (T, tg, lt, p, D) => {
  let s = set('dockout', () => S.dockExterior());
  const leave = p.mode === 'leave' ? ease(lt / D) : 0;
  for (let i = 0; i < 14; i++) {
    const x0 = 820 + (i % 7) * 120 + (i > 6 ? 60 : 0), y0 = 860 + (i > 6 ? 110 : 0);
    const x = lerp(x0, x0 + 900, leave), lean = p.mode === 'turn' ? lerp(0, -10, ease(ramp(lt, 0.2, 1.0))) : 10;
    s += zombie({ x, y: y0, s: 0.78, outfit: ['cashier', 'jogger', 'shopper', 'park', 'nurse', 'janitor', 'guard'][i % 7], tilt: lean + 4 * Math.sin(tg + i), look: p.mode === 'leave' ? 0.8 : -0.6, pose: p.mode === 'turn' ? 'reach' : 'stand', facing: p.mode === 'leave' ? 1 : -1, filter: false });
  }
  s += grade('dusk');
  return cam(s, { s: push(lt, D, [1.0, 1.06]), cx: 1100 }) + hudAt({ day: 4, time: p.mode === 'leave' ? '3:34 PM' : '3:17 PM', noise: p.mode === 'leave' ? 4 : 3, place: 'FRESHWAY · LOADING DOCK' });
};

// ---------- POV across the lot ----------
SH.povlot = (T, tg, lt, p, D) => {
  const ph = p.phase;
  let s;
  if (ph === 'ladder') {
    s = set('pov_wall', () => { let o = rect(0, 0, W, H, { fill: '#6E675C' }); for (let y = 0; y < H; y += 50) for (let x = (y / 50) % 2 ? -60 : 0; x < W; x += 120) o += rect(x, y, 120, 50, { fill: 'none', stroke: '#5E584E', strokeWidth: 3 }); return g(o, { filter: 'url(#wobble)' }); });
    const dy = (lt * 240) % 220;
    for (let i = -1; i < 6; i++) s += rect(560, i * 220 + dy, 800, 26, { rx: 8, fill: '#9C968A', ...ink(5) });
    s += rect(540, 0, 30, H, { fill: '#8C867A', ...ink(5) }) + rect(1350, 0, 30, H, { fill: '#8C867A', ...ink(5) });
    const grip = (Math.sin(lt * 4) + 1) / 2;
    s += g(sleeve('M300 1080 L640 700 L760 760 L560 1080 Z') + mitt(700, 700 - grip * 60, -10, 1.1) + sleeve('M1620 1080 L1280 640 L1160 700 L1360 1080 Z') + mitt(1220, 640 + grip * 60, 10, 1.1), { filter: 'url(#wobbleSoft)' });
    s += nightTint(0.75);
  } else if (ph === 'mall') {
    s = set('pov_mall', () => g(S.sky('night') + S.cityBand('night') + S.mallFacade({ time: 'night', x: 520, y: 220, k: 1.1 }) + rect(0, 700, W, 380, { fill: '#2E323C' }), { filter: 'url(#wobble)' }));
    s += glow(520 + 30 * 1.1 + 6 * 88 + 30, 220 + 95 * 1.1 + 28, 50, '#FFD98A', 0.7) + nightTint(0.5);
  } else {
    // between parked cars
    s = set('pov_cars', () => {
      let o = S.sky('night') + S.cityBand('night') + rect(0, 520, W, 560, { fill: '#30343E' });
      for (let x = -100; x < W; x += 220) o += line(x, 1080, x + 160, 560, { stroke: '#E9E2C8', strokeWidth: 4, opacity: 0.3 });
      o += path('M-40 1080 L-40 520 Q120 470 380 520 L460 700 L460 1080 Z', { fill: '#3A4252', ...ink(7) }) + rect(40, 560, 300, 120, { rx: 20, fill: '#1E2433', ...ink(5) });
      o += path('M1960 1080 L1960 500 Q1760 450 1500 510 L1420 700 L1420 1080 Z', { fill: '#5C3A33', ...ink(7) }) + rect(1560, 545, 320, 120, { rx: 20, fill: '#1E2433', ...ink(5) });
      o += rect(760, 560, 420, 180, { rx: 30, fill: '#4A5060', ...ink(6) }) + rect(820, 520, 300, 70, { rx: 20, fill: '#1E2433', ...ink(5) });
      return g(o, { filter: 'url(#wobble)' });
    });
    s += crowd({ x0: 1300, x1: 1900, y: 610, rows: 2, n: 12, s: 0.18, seed: 5, spread: 20, t: tg });
    s += rings(1760, 560, tg, { color: '#FFE27A', max: 160, period: 1.0, op: 0.6, width: 4 });
    if (ph === 'pass' || ph === 'freeze') {
      const k = ph === 'pass' ? ease(ramp(lt, 0.6, 6.6)) : 0;
      if (ph === 'pass') s += zombie({ x: lerp(-200, 2200, k), y: 1500, s: 3.0, outfit: 'jogger', tilt: 10 + 6 * Math.sin(tg * 4.6), look: -0.2, sway: Math.sin(tg * 4.6) * 3 });
    }
    s += nightTint(0.55) + glow(1660, 470, 70, '#FFB866', 0.5);
    if (ph === 'walk') s += g(sleeve('M0 1080 L260 860 L420 940 L300 1080 Z') + mitt(330, 880, -20, 1.1), { filter: 'url(#wobbleSoft)' });
  }
  const bob = ph === 'walk' ? Math.sin(lt * 5) * 8 : ph === 'freeze' || ph === 'pass' ? 0 : Math.sin(lt * 3) * 4;
  s += darkness(0.5, 0.5, 0.65, 0.75, 'pld');
  s = cam(s, { s: 1.04, x: wob(tg * 0.7, 1) * 5, y: bob });
  // Dale's lines in the POV come as quoted radio text
  let q = '';
  for (const L of T.voice.lines) if (L.who === 'DALE' && tg >= L.start && tg < L.start + L.dur + 0.4) q = L.text;
  return s + letterbox() + (q ? quote(q, H - 82) : '') + (q ? '' : capsAt(T, tg));
};

// ---------- Freshway from the lot: someone on the roof ----------
SH.freshroof = (T, tg, lt, p, D) => {
  let s = set('freshroof', () => {
    let o = S.sky('night') + rect(0, 420, W, 660, { fill: '#2C303A' });
    o += rect(160, 300, 1600, 520, { fill: '#5A5E68', ...ink(6) }) + rect(160, 300, 1600, 120, { fill: '#2F4A40', ...ink(6) });
    o += text(960, 385, 'FRESHWAY', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 84, fill: '#3A4A44', textAnchor: 'middle', letterSpacing: 8 });
    o += rect(260, 470, 1400, 330, { fill: '#6E6A60', ...ink(6) });
    o += rect(1180, 230, 200, 74, { fill: '#4A4A50', ...ink(5) });
    return g(o, { filter: 'url(#wobble)' });
  });
  s += screenGlow(1000, 200, 260, 160, '#8FA6C8', 0.35);
  if (p.mode !== 'hatch') {
    const fx = 1000, fy = 302, k = 2.2;   // a man on the roof edge: cap, jacket, radio held up
    let fig = circle(fx, fy - 62 * k, 15 * k, { fill: '#0E1016' }) + rect(fx - 20 * k, fy - 64 * k, 40 * k, 9 * k, { rx: 3, fill: '#0E1016' }) + rect(fx - 18 * k, fy - 48 * k, 36 * k, 48 * k, { rx: 9 * k, fill: '#0E1016' });
    fig += line(fx + 14 * k, fy - 40 * k, fx + 26 * k, fy - 64 * k, { stroke: '#0E1016', strokeWidth: 8 * k, strokeLinecap: 'round' }) + rect(fx + 20 * k, fy - 82 * k, 12 * k, 22 * k, { rx: 3, fill: '#0E1016' }) + line(fx + 28 * k, fy - 82 * k, fx + 28 * k, fy - 100 * k, { stroke: '#0E1016', strokeWidth: 3 });
    s += fig + circle(fx + 26 * k, fy - 78 * k, 3 * k, { fill: PAL.red }) + glow(fx + 26 * k, fy - 78 * k, 12 * k, PAL.red, 0.6 + 0.3 * Math.sin(tg * 8));
  } else {
    const k = ease(ramp(lt, 0.15, 0.4));
    s += poly([[1200, 230], [1360, 230], [1360, lerp(150, 230, k)], [1200, lerp(150, 230, k)]], { fill: '#4A4A50', ...ink(4) });
  }
  s += nightTint(0.5) + screenGlow(960, 200, 600, 200, '#3A4A6A', 0.3);
  const c = p.mode === 'figure_close' ? { s: lerp(2.0, 2.3, ease(lt / D)), cx: 1030, cy: 220 } : p.mode === 'hatch' ? { s: 2.2, cx: 1250, cy: 240 } : { s: push(lt, D, [1.0, 1.08]), cx: 1000, cy: 400 };
  return cam(s, c) + (p.mode === 'hatch' ? bang('CLANG!', 1300, 420, lt - 0.35, { size: 150, life: 1.2 }) : '');
};

// ---------- running back ----------
SH.run = (T, tg, lt, p, D) => {
  let s = set('runwall', () => S.staffWall({}));
  const x = lerp(-100, 1500, ease(lt / D)), ph = tg * 9;
  s += crowd({ x0: -200, x1: lerp(-150, 600, lt / D), y: 1000, rows: 2, n: 8, s: 0.6, seed: 4, spread: 20, t: tg, arms: true });
  s += hero({ x, y: 1000, s: 1.3, pose: Math.sin(ph) > 0 ? 'run' : 'walk', expr: 'scared', facing: 1, look: -0.5, tilt: -6 });
  for (let i = 0; i < 4; i++) s += line(x - 160 - i * 30, 700 + i * 40, x - 300 - i * 30, 700 + i * 40, { stroke: '#E9E2C8', strokeWidth: 5, opacity: 0.6, strokeLinecap: 'round' });
  s += nightTint(0.6);
  return cam(s, { s: 1.05, x: -lt * 40, ...shake(tg, 0.3) }) + hudAt({ day: 7, time: '2:06 AM', noise: 5, place: 'FRESHWAY · PARKING LOT' });
};

// ---------- the staff door ----------
SH.staffdoor = (T, tg, lt, p, D) => {
  const mode = p.mode;
  if (mode === 'inside') {
    let s = rect(0, 0, W, H, { fill: '#14161C' }) + rect(500, 80, 920, 1000, { fill: '#3A3F46', ...ink(6) }) + rect(560, 140, 800, 940, { fill: '#4A5058', ...ink(5) });
    const thud = Math.max(0, Math.sin(lt * 4.2)) ** 6;
    s += hero({ x: 960, y: 1250, s: 2.2, pose: 'scared', expr: 'scared', facing: 1, look: 0.2, blink: autoBlink(lt) });
    s += nightTint(0.6) + screenGlow(960, 200, 500, 200, '#3A4A6A', 0.4) + bang('BANG!', 1500, 380, (lt % 1.5) - 0.3, { size: 120, life: 0.7 });
    return cam(s, { s: 1.02, ...shake(tg, thud * 1.2) });
  }
  let s = set('staffwall', () => S.staffWall({}));
  if (mode === 'arrive') s += hero({ x: lerp(300, 820, ease(ramp(lt, 0, 1.2))), y: 990, s: 1.35, pose: lt < 1.2 ? 'run' : 'reach', expr: 'scared', facing: 1, look: 0.4 });
  if (mode === 'keys' || mode === 'turn') {
    s = rect(0, 0, W, H, { fill: '#6E747A' }) + rect(0, 0, W, H, { fill: '#7E858C', ...ink(6) });
    s += rect(1060, 380, 220, 340, { rx: 20, fill: '#C9C3B5', ...ink(7) }) + circle(1170, 520, 40, { fill: '#8E8A80', ...ink(5) }) + rect(1160, 490, 20, 60, { fill: INK });
    const trem = mode === 'keys' ? Math.sin(tg * 30) * 4 : 0, turn = mode === 'turn' ? ease(ramp(lt, 0.1, 0.5)) * 90 : 0;
    s += g(keyring(900, 470, 1.6, tg, 0.6), { transform: `translate(${f1(trem)} ${f1(trem * 0.5)}) rotate(${f1(turn * 0.3)} 1170 520)` });
    s += g(sleeve('M0 1080 L640 520 L760 620 L300 1080 Z') + mitt(800, 540, -20, 1.4), { transform: `translate(${f1(trem)} 0)`, filter: 'url(#wobbleSoft)' });
    if (mode === 'keys') for (let i = 0; i < 3; i++) s += g(zombie({ x: 200 + i * 220, y: 1500, s: 2.2, outfit: ['jogger', 'shopper', 'park'][i], tilt: 10, look: 0.6, filter: false }), { opacity: f1(clamp(lt / 6 * (1 + i * 0.3)) * 0.55 * 100) / 100 });
    if (mode === 'turn') s += bang('CLICK', 1400, 360, lt - 0.45, { size: 100, life: 1.0 });
    s = g(s, { filter: 'url(#wobbleSoft)' });
  }
  s += nightTint(0.55);
  return cam(s, { s: push(lt, D, [1.0, 1.06]), ...shake(tg, mode === 'keys' ? 0.2 : 0) }) + hudAt(p.hud || { day: 7, time: '2:07 AM', noise: 4, place: 'FRESHWAY · STAFF DOOR' });
};

// ---------- camp in aisle 9 ----------
SH.camp = (T, tg, lt, p, D) => {
  const time = p.time || 'night';
  let s = set('camp', () => S.campAisle());
  const hp = p.hero;
  const lantern = (x, y) => g(rect(x - 30, y - 80, 60, 80, { rx: 10, fill: '#2E2E2E', ...ink(4) }) + rect(x - 20, y - 70, 40, 56, { rx: 6, fill: '#FFE7A8', ...ink(3) }) + path(`M${x - 22} ${y - 80} q22 -30 44 0`, { fill: 'none', ...ink(4) }), { filter: 'url(#wobbleSoft)' });
  s += lantern(1220, 860);
  if (hp === 'sit' || hp === 'radio' || hp === 'laugh') s += hero({ x: 1400, y: 930, s: 1.6, pose: hp === 'radio' || hp === 'laugh' ? 'radio' : 'sit', expr: hp === 'laugh' ? 'smile' : 'neutral', facing: -1, look: -0.4, blink: autoBlink(lt), tilt: hp === 'laugh' ? 6 * Math.sin(tg * 3) : 0, breathe: 0.01 * Math.sin(tg * 2.2), extra: hp === 'radio' || hp === 'laugh' ? radioProp(1400 - 0.6 * 96, 930 - 4.4 * 96, 0.5, { on: true }) : '' });
  if (hp === 'lie') s += g(ellipse(860, 830, 160, 40, { fill: '#3E6E9A', ...ink(5) }) + circle(740, 805, 40, { fill: PAL.skin, ...ink(5) }) + path('M705 790 q35 -40 75 -5', { fill: PAL.hair, ...ink(4) }), { filter: 'url(#wobbleSoft)' });
  if (hp === 'wake') s += hero({ x: 1420, y: 880, s: 1.3, pose: 'scared', expr: 'neutral', facing: -1, look: 0, blink: keys(lt, [[0, 1], [0.6, 0]], 0.3) });
  if (hp === 'tent') s += hero({ x: 1400, y: 880, s: 1.3, pose: 'point', expr: 'smile', facing: -1, look: -0.6, blink: autoBlink(lt) });
  if (p.sign) s += g(rect(1260, 170, 260, 70, { rx: 8, fill: '#FBF6EA', ...ink(4) }) + label(1390, 215, 'SLEEPS 2', 28, PAL.red), { transform: `rotate(-4 1390 205)`, filter: 'url(#wobbleSoft)' });
  if (time === 'night') s += nightTint(0.8, '#2A2238') + screenGlow(1250, 760, 560, 360, '#FFB866', 0.28) + screenGlow(1220, 800, 110, 90, '#FFE7A8', 0.55, 'softS') + screenGlow(1400, 700, 240, 320, '#FFB866', 0.3);
  else if (time === 'morning') s += nightTint(0.45, '#6E6A8A') + screenGlow(200, 300, 600, 400, '#E8D8C8', 0.25);
  return cam(s, { s: push(lt, D, [1.0, 1.06]), cx: 1100, cy: 600 }) + hudAt(p.hud);
};

// ---------- the walkie-talkie ----------
SH.radio = (T, tg, lt, p, D) => {
  if (p.mode === 'belt') {
    let s = rect(0, 0, W, H, { fill: '#2E3246' }) + rect(0, 0, W, H, { fill: PAL.jacket, opacity: 0.7 });
    s += rect(0, 560, W, 120, { fill: '#2A2522', ...ink(6) }) + rect(0, 680, W, 400, { fill: PAL.jeans });
    const click = ramp(lt, D - 0.35, D - 0.2);
    s += radioProp(960, 700, 1.5, { on: click > 0, led: click > 0 ? '#7FD36B' : '#3A3D42' });
    s += nightTint(0.28) + screenGlow(960, 500, 500, 400, '#6A7A9A', 0.3) + (click > 0 ? screenGlow(915, 490, 90, 90, '#7FD36B', 0.7, 'softS') : '');
    return cam(s, { s: push(lt, D, [1.0, 1.08]), cy: 560 });
  }
  let s = rect(0, 0, W, H, { fill: '#12141B' }) + blurred('camp', () => S.campAisle()) + nightTint(0.88, '#2A2238');
  // radio in the foreground, speech waveform beside it
  const talking = T.voice.lines.some((L) => L.who === 'DALE' && tg >= L.start + 0.1 && tg < L.start + L.dur - 0.1);
  s += radioProp(620, 720, 1.9, { on: true, led: talking ? (p.scared ? '#FFB13A' : PAL.red) : '#7FD36B' });
  if (talking) s += screenGlow(563, 454, 80, 80, PAL.red, 0.7, 'softS');
  let wave = '';
  for (let i = 0; i < 48; i++) { const a = talking ? (0.25 + 0.75 * Math.abs(Math.sin(tg * 13 + i * 0.7) * Math.sin(tg * 5.3 + i * 0.31))) : 0.05; wave += rect(900 + i * 20, 540 - a * 120, 10, a * 240, { rx: 5, fill: '#F2A73B', opacity: 0.9 }); }
  if (p.echo) for (let i = 0; i < 48; i++) { const tt = tg - 0.3, a = talking ? (0.15 + 0.4 * Math.abs(Math.sin(tt * 13 + i * 0.7) * Math.sin(tt * 5.3 + i * 0.31))) : 0.03; wave += rect(900 + i * 20, 800 - a * 80, 10, a * 160, { rx: 5, fill: '#8FB3D5', opacity: 0.7 }); }
  s += wave + label(900, 380, p.who === 'dale' ? 'DALE · CH 3' : 'CH 3', 30, '#F2A73B', 'start', 4);
  if (p.echo) s += label(900, 700, 'BEHIND YOU', 26, '#8FB3D5', 'start', 4);
  s += screenGlow(620, 600, 500, 500, '#3A4A6A', 0.25);
  return cam(s, { s: push(lt, D, [1.0, 1.04]) });
};

// ---------- prop close-ups ----------
SH.prop = (T, tg, lt, p, D) => {
  const it = p.item;
  if (it === 'clock') {
    let s = blurred('aisle_night', () => aisle({ night: true, seed: 5 }).s) + rect(0, 640, W, 60, { fill: '#8E877A', ...ink(5) });
    const mode = p.mode || 'still';
    const ring = mode === 'ring' || mode === 'ring_close' ? 1 : mode === 'ring_stop' ? 1 - ease(ramp(lt, D * 0.55, D * 0.62)) : 0;
    s += alarmClock(960, 520, 1.6, { ring, t: tg, tape: true, time: [2, mode === 'ring_stop' ? 48 : 31] });
    s += nightTint(0.72) + screenGlow(960, 470, 300, 240, '#FFE27A', 0.06 + 0.1 * ring);
    return cam(s, { s: mode === 'ring_close' ? lerp(1.2, 1.5, ease(lt / D)) : push(lt, D, [1.0, 1.08]), cy: 520, ...shake(tg, ring * 0.12) });
  }
  if (it === 'keys') {
    let s = rect(0, 0, W, H, { fill: p.mode === 'mystery' ? '#0C0E14' : '#2A2E3A' });
    s += keyring(960, 380, 1.9, tg, p.mode === 'shake' ? 1.6 : 0.5);
    if (p.mode !== 'mystery') s += g(sleeve('M0 1080 L700 520 L820 620 L320 1080 Z') + mitt(860, 420, -20, 1.4), { filter: 'url(#wobbleSoft)' });
    s += p.mode === 'mystery' ? darkness(0.5, 0.4, 0.45, 0.95, 'kd') + screenGlow(960, 420, 400, 300, '#F2A73B', 0.15) : nightTint(0.55);
    return cam(s, { s: push(lt, D, [1.0, 1.08]), cy: 480, ...shake(tg, p.mode === 'shake' ? 0.35 : 0) });
  }
  if (it === 'wallclock') {
    let s = set('office', () => S.office());
    const mm = 41 + Math.floor(lt), ma = (mm / 60) * 2 * Math.PI - Math.PI / 2, ha = ((6 % 12) / 12 + mm / 720) * 2 * Math.PI - Math.PI / 2;
    s += line(760, 290, 760 + Math.cos(ha) * 48, 290 + Math.sin(ha) * 48, ink(9)) + line(760, 290, 760 + Math.cos(ma) * 72, 290 + Math.sin(ma) * 72, ink(6));
    s += nightTint(0.45, '#6E6A8A');
    return cam(s, { s: lerp(2.4, 2.7, ease(lt / D)), cx: 760, cy: 300 });
  }
  if (it === 'batteries') {
    let palm = sleeve('M0 1080 L520 760 L720 900 L380 1080 Z') + path('M640 800 q120 -150 360 -140 q170 10 220 120 q20 90 -90 140 q-230 70 -420 -40 z', { fill: PAL.skin, ...ink(7) });
    for (const [fx, fy, fr] of [[1150, 690, -40], [1230, 760, -20], [1260, 850, 0], [1230, 930, 20]]) palm += g(rect(-28, -100, 56, 150, { rx: 28, fill: PAL.skin, ...ink(6) }), { transform: `translate(${fx} ${fy}) rotate(${fr + 70})` });
    palm += path('M700 760 q-60 -90 -10 -160 q40 -40 70 10 q20 60 0 140', { fill: PAL.skin, ...ink(6) });
    let s = rect(0, 0, W, H, { fill: '#1E222C' }) + g(palm, { filter: 'url(#wobbleSoft)' });
    for (const [x, r] of [[860, -12], [1040, 8]]) s += g(rect(-34, -110, 68, 200, { rx: 12, fill: '#2E2E2E', ...ink(5) }) + rect(-34, 40, 68, 50, { fill: '#C9A43A' }) + rect(-12, -126, 24, 18, { fill: '#B9B4A6', ...ink(3) }) + text(0, -20, 'AA', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 28, fill: '#F2F2EE', textAnchor: 'middle' }), { transform: `translate(${x} 610) rotate(${r})`, filter: 'url(#wobbleSoft)' });
    s += nightTint(0.55) + screenGlow(960, 560, 360, 260, '#FFE7A8', 0.2);
    return cam(s, { s: push(lt, D, [1.0, 1.08]), cy: 600 }) + hudAt({ day: 5, time: '2:32 AM', noise: 2, place: 'FRESHWAY · AISLE 9' });
  }
  if (it === 'clocks6') {
    let s = rect(0, 0, W, H, { fill: '#C9C2AE' }) + rect(0, 720, W, 40, { fill: '#8E877A', ...ink(5) }) + rect(0, 760, W, 320, { fill: '#B3A88E' });
    for (let i = 0; i < 6; i++) s += alarmClock(300 + i * 264, 560, 0.95, { time: [2, p.set ? 1 + i : 0], ring: 0 });
    s += g(rect(830, 690, 260, 90, { rx: 10, fill: '#FBF6EA', ...ink(4) }) + label(960, 752, '$4.99', 52, PAL.red), { filter: 'url(#wobbleSoft)' });
    if (p.set) for (let i = 0; i < 6; i++) s += g(rect(240 + i * 264, 400, 120, 50, { rx: 8, fill: '#2B1D21', ...ink(3) }) + label(300 + i * 264, 436, `2:0${i + 1}`, 30, '#FFE27A'), { opacity: f1(clamp((lt - i * 0.35) * 3) * 100) / 100 });
    s += nightTint(0.35, '#6E6A8A');
    return cam(s, { s: push(lt, D, [1.0, 1.06]), cy: 560 }) + hudAt({ day: 6, time: '2:10 PM', noise: 0, place: 'FRESHWAY · AISLE 11' });
  }
  if (it === 'fridge') {
    let s = rect(0, 0, W, H, { fill: '#3A3F46' });
    const off = ramp(lt, D - 0.6, D - 0.45);
    for (let i = 0; i < 4; i++) s += rect(120 + i * 430, 140, 400, 800, { fill: off ? '#3E5260' : '#CFE3EA', ...ink(6) }) + rect(140 + i * 430, 180, 360, 20, { fill: '#8E9499' }) + Array.from({ length: 4 }, (_, k) => rect(150 + i * 430, 280 + k * 160, 340, 14, { fill: '#9DB6C8', ...ink(2) })).join('');
    s += label(960, 110, 'DAIRY · CHILLED', 40, '#F2F2EE', 'middle', 6);
    s = g(s, { filter: 'url(#wobbleSoft)' }) + (off ? nightTint(0.6) : screenGlow(960, 540, 900, 500, '#E9F4F8', 0.2));
    return cam(s, { s: push(lt, D, [1.0, 1.05]) }) + hudAt({ day: 4, time: '3:16 PM', noise: 0 });
  }
  if (it === 'exit_sign') {
    let s = rect(0, 0, W, H, { fill: '#07090D' });
    const blink = Math.sin(tg * 6) > 0 || lt > 1.0;
    s += rect(660, 340, 600, 220, { rx: 16, fill: blink ? '#3DBE6A' : '#1E3A28', ...ink(7) }) + label(960, 490, 'EXIT', 150, blink ? '#EFFFF2' : '#2E4A36', 'middle', 10);
    if (blink) s += glow(960, 450, 400, '#7CFF9A', 0.5);
    const left = 90 * 60 - Math.floor(lt * 1.0);
    s += g(rect(760, 640, 400, 120, { rx: 12, fill: '#2B1D21', ...ink(4) }) + label(960, 722, `${Math.floor(left / 60)}:${String(left % 60).padStart(2, '0')}`, 72, '#FFE27A'), { opacity: f1(clamp((lt - 0.8) * 3) * 100) / 100 });
    return cam(s, { s: push(lt, D, [1.0, 1.06]) }) + hudAt({ day: 4, time: '3:16 PM', noise: 1 });
  }
  return '';
};

SH.black = (T, tg, lt, p, D) => rect(0, 0, W, H, { fill: '#000' });
