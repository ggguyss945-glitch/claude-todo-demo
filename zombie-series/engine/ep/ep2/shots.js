// Episode 2 shot templates inside Freshway: the POV walk to aisle 12, prop close-ups, the split map,
// the stockroom doors, the staff restroom, cards, Nora running. Mall and storm shots live in shots_mall.js.
import { W, H, INK, PAL, glow, hero, zombie, g, rect, circle, ellipse, line, poly, path, text, ink, layer, rng, walkPose, runPose } from '../../lib.js';
import { aisle, at, smallCaps, big } from '../../scenes.js';
import { clamp, lerp, ease, easeOut, easeIn, back, ramp, wob, f1, autoBlink, cam, push, shake, nightTint, screenGlow, darkness,
  letterbox, bang, rings, hudAt, sleeve, mitt, radioProp, alarmClock, label, set } from '../kit.js';
import { SH, HC_BG, capsAt } from '../shots_in.js';
import * as S2 from './sets2.js';
import * as S from '../sets.js';
import { nora, leoFace, NORA } from './chars.js';
import './shots_mall.js';

const W2 = W / 2;
const blurred = (key, make) => layer(key + '_soft', () => g(make(), { filter: 'url(#softS)' }));
let A12 = null;
const aisle12 = () => (A12 ||= aisle({ night: true, seed: 12, name: 'AISLE 12', sub: 'HOME · CLOCKS · BATTERIES' }));
const aisle12bg = () => set('aisle12_night', () => aisle12().s);

// times of a sound effect inside a window, from the timeline (pictures sync to the mix)
export const sfxAt = (T, name, t0, t1) => (T.sfx || []).filter((x) => x.name === name && x.t >= t0 - 0.01 && x.t < t1).map((x) => x.t);
// a hit envelope: 0 before t, jumps to 1 and decays
export const hit = (tg, t, decay = 6) => (tg >= t ? Math.exp(-(tg - t) * decay) : 0);
export const hits = (tg, ts, decay = 6) => ts.reduce((m, t) => Math.max(m, hit(tg, t, decay)), 0);

// ---------- POV: down aisle 12 at 2:31 ----------
SH.povaisle = (T, tg, lt, p, D) => {
  const ph = p.phase || 'walk';
  let s;
  if (ph === 'vent') {
    // looking up at the ceiling vent over the aisle: something behind the grate is looking back
    s = set('vent_ceiling', () => {
      let o = rect(0, 0, W, H, { fill: '#2A2E36' });
      for (let x = -200; x < W + 200; x += 240) o += line(x, 0, x + (x - W2) * 0.3, H, { stroke: '#22262D', strokeWidth: 4 });
      o += rect(560, 260, 800, 500, { rx: 14, fill: '#4A5058', ...ink(8) }) + rect(600, 300, 720, 420, { fill: '#0B0D11', ...ink(5) });
      for (let i = 0; i < 9; i++) o += rect(600, 318 + i * 44, 720, 22, { fill: '#5E6670', ...ink(3) });
      for (const [x, y] of [[590, 290], [1330, 290], [590, 730], [1330, 730]]) o += circle(x, y, 10, { fill: '#8E9499', ...ink(3) });
      return g(o, { filter: 'url(#wobble)' });
    });
    const eyes = typeof p.eyes === 'number' ? p.eyes : D - 1.6;
    const k = ease(ramp(lt, eyes, eyes + 0.5)), bl = autoBlink(lt + 0.7, 3);
    if (k > 0) for (const x of [902, 1018]) s += ellipse(x, 515, 22, 13 * Math.max(0.1, 1 - bl), { fill: '#F3EBDD', opacity: f1(k * 100) / 100 }) + circle(x + 4, 515, 7 * Math.max(0.1, 1 - bl), { fill: INK, opacity: f1(k * 100) / 100 });
    s += nightTint(0.5) + screenGlow(960, 500, 420, 260, '#5A6A8A', 0.2) + (k > 0 ? screenGlow(960, 515, 140, 40, '#F3EBDD', 0.12 * k, 'softS') : '');
    s += darkness(0.5, 0.48, 0.55, 0.85, 'vtd');
    s = cam(s, { s: lerp(1.0, 1.22, ease(lt / D)), cx: 960, cy: 510, x: wob(tg * 0.5, 2) * 4, y: wob(tg * 0.5, 3) * 3 });
    return s + letterbox() + capsAt(T, tg);
  }
  const A = aisle12();
  s = aisle12bg();
  // the clock sits on the end shelf, far down the aisle, then closer as we walk
  const ringing = ph === 'reach' ? (lt < (p.cut ?? 1.05) ? 1 : 0) : 1;
  const cq = at(A, 1180, 2.6), CK = 1.5 * cq.k;
  s += alarmClock(cq.x, cq.y - 470 * cq.k, CK, { ring: ringing, t: tg, tape: true });
  s += nightTint(0.88);
  if (ringing) s += rings(cq.x, cq.y - 470 * cq.k, tg, { color: '#FFE27A', max: 140, period: 0.8, op: 0.55, width: 4 }) + screenGlow(cq.x, cq.y - 470 * cq.k, 120, 90, '#FFE27A', 0.18 + 0.08 * Math.sin(tg * 18));
  // the torch beam we carry
  s += screenGlow(cq.x - 40, cq.y - 430 * cq.k, 420, 300, '#FFF2C4', 0.16) + screenGlow(960, 900, 700, 220, '#FFF2C4', 0.08);
  let c;
  const fx = cq.x, fy = cq.y - 470 * cq.k;   // the clock stays put on screen while the camera closes in
  if (ph === 'walk') { const k = ease(lt / D); c = { s: lerp(1.0, 1.7, k), cx: fx, cy: fy, x: wob(tg * 0.9, 1) * 6, y: Math.sin(lt * 4.6) * 9 }; }
  else if (ph === 'near') { const k = easeOut(lt / D); c = { s: lerp(1.75, 3.0, k), cx: fx, cy: fy, x: wob(tg * 0.9, 1) * 5, y: Math.sin(lt * 4.2) * 6 * (1 - k) }; }
  else c = { s: 3.4, cx: fx, cy: fy, x: wob(tg * 0.6, 1) * 3, y: wob(tg * 0.6, 2) * 3 };
  s = cam(s, c);
  if (ph === 'reach') {
    // our hand comes in from the lower right and presses the button on top of the clock
    const cut = p.cut ?? 1.05, k = easeOut(ramp(lt, 0.1, cut - 0.05)), press = ramp(lt, cut - 0.08, cut) * (1 - ramp(lt, cut + 0.25, cut + 0.6));
    const bx = fx + c.x, by = fy + c.y - 96 * CK * 3.4;   // the button, on screen
    const hx = lerp(1700, bx + 40, k), hy = lerp(1250, by - 10 + press * 16, k);
    s += g(sleeve(`M${f1(hx + 330)} 1250 L${f1(hx + 60)} ${f1(hy + 70)} L${f1(hx + 170)} ${f1(hy + 190)} L${f1(hx + 560)} 1250 Z`) + mitt(hx + 60, hy + 30, -38, 1.1), { filter: 'url(#wobbleSoft)' });
    s += bang('CLICK', fx - 380, by + 40, lt - cut, { size: 90, rot: -6, life: 0.8, fill: '#F3EBDD' });
  }
  s += darkness(0.5, 0.45, 0.6, 0.75, 'pad');
  return s + letterbox() + capsAt(T, tg) + hudAt(p.hud);
};

// ---------- prop close-ups ----------
const wrapperProp = (x, y, k = 1, rot = -12) => g(path(`M${-150 * k} ${-60 * k} L${-110 * k} ${-80 * k} L${110 * k} ${-70 * k} L${160 * k} ${-90 * k} L${150 * k} ${60 * k} L${110 * k} ${75 * k} L${-120 * k} ${70 * k} L${-160 * k} ${80 * k} Z`, { fill: '#7FD36B', ...ink(6) })
  + path(`M${-110 * k} ${-80 * k} L${-120 * k} ${70 * k} M${110 * k} ${-70 * k} L${110 * k} ${75 * k}`, { stroke: '#4E9A3E', strokeWidth: 5, fill: 'none' })
  + text(0, -8 * k, 'SOUR', { fontFamily: 'Bangers, Impact', fontSize: 58 * k, fill: '#F7F2E6', stroke: INK, strokeWidth: 3 * k, paintOrder: 'stroke', textAnchor: 'middle', letterSpacing: 3 })
  + text(0, 48 * k, 'WORMS', { fontFamily: 'Bangers, Impact', fontSize: 58 * k, fill: '#E05AA0', stroke: INK, strokeWidth: 3 * k, paintOrder: 'stroke', textAnchor: 'middle', letterSpacing: 3 })
  + path(`M${-90 * k} ${-40 * k} q30 -20 60 0 t60 0`, { fill: 'none', stroke: '#E9B93E', strokeWidth: 8 * k, strokeLinecap: 'round' }),
  { transform: `translate(${f1(x)} ${f1(y)}) rotate(${rot})`, filter: 'url(#wobbleSoft)' });

function drawing(x, y, k = 1) {
  // crayon drawing on lined paper: a girl, a man in a cap, you with orange headphones; three words underneath
  const cr = (d, col, w = 9) => path(d, { fill: 'none', stroke: col, strokeWidth: w * 1.7 * k, strokeLinecap: 'round', strokeLinejoin: 'round', opacity: 0.95 });
  let s = rect(-460 * k, -330 * k, 920 * k, 660 * k, { fill: '#FBF8EE', ...ink(5) });
  for (let i = 0; i < 9; i++) s += line(-460 * k, (-260 + i * 64) * k, 460 * k, (-260 + i * 64) * k, { stroke: '#BFD3E6', strokeWidth: 2 });
  s += line(-380 * k, -330 * k, -380 * k, 330 * k, { stroke: '#E9A0A0', strokeWidth: 3 });
  // the girl: auburn scribble hair, teal body
  const fig = (cx, col, head) => cr(`M${cx * k} ${-60 * k} L${(cx - 50) * k} ${80 * k} L${(cx + 50) * k} ${80 * k} Z`, col, 11) + cr(`M${(cx - 25) * k} ${80 * k} L${(cx - 35) * k} ${170 * k} M${(cx + 25) * k} ${80 * k} L${(cx + 35) * k} ${170 * k}`, '#3A3A3A', 9)
    + cr(`M${(cx - 40) * k} ${0} L${(cx - 90) * k} ${40 * k} M${(cx + 40) * k} ${0} L${(cx + 90) * k} ${40 * k}`, '#3A3A3A', 8) + head;
  const headC = (cx, r = 48) => cr(`M${(cx + r) * k} ${-110 * k} a${r * k} ${r * k} 0 1 1 -0.1 0`, '#E9A06A', 8) + circle((cx - 16) * k, -116 * k, 5 * k, { fill: '#2B2B2B' }) + circle((cx + 16) * k, -116 * k, 5 * k, { fill: '#2B2B2B' }) + cr(`M${(cx - 16) * k} ${-90 * k} q${16 * k} ${12 * k} ${32 * k} 0`, '#C0392B', 5);
  s += fig(-230, '#3E9E92', headC(-230) + cr(`M${-285 * k} ${-120 * k} q-10 ${70 * k} 10 ${110 * k} M${-180 * k} ${-130 * k} q20 ${70 * k} 0 ${110 * k} M${-270 * k} ${-150 * k} q${40 * k} ${-30 * k} ${80 * k} 0`, '#B8492A', 12));
  s += fig(0, '#3B4A6B', headC(0, 52) + cr(`M${-60 * k} ${-150 * k} h${120 * k} M${-40 * k} ${-150 * k} q${40 * k} ${-50 * k} ${80 * k} 0 M${60 * k} ${-150 * k} h${40 * k}`, '#2E5E3A', 11));
  s += fig(230, '#5E6B3A', headC(230) + cr(`M${180 * k} ${-130 * k} q${50 * k} ${-50 * k} ${100 * k} 0`, '#3A2A22', 12) + cr(`M${176 * k} ${-60 * k} q${54 * k} ${40 * k} ${108 * k} 0`, '#F08A24', 12) + circle(176 * k, -66 * k, 14 * k, { fill: '#F08A24', opacity: 0.9 }) + circle(284 * k, -66 * k, 14 * k, { fill: '#F08A24', opacity: 0.9 }));
  s += text(0, 270 * k, 'COME FIND ME', { fontFamily: 'Patrick Hand, Rubik', fontSize: 86 * k, fill: '#C0392B', textAnchor: 'middle', letterSpacing: 6, stroke: '#C0392B', strokeWidth: 1.5 });
  s += rect(-90 * k, -350 * k, 180 * k, 46 * k, { fill: '#D9C79A', opacity: 0.8 });
  return g(s, { transform: `translate(${f1(x)} ${f1(y)}) rotate(-2)`, filter: 'url(#wobbleSoft)' });
}

SH.prop2 = (T, tg, lt, p, D) => {
  const it = p.item;
  if (it === 'clock12') return SH.prop(T, tg, lt, { item: 'clock', mode: p.mode || 'still' }, D);
  const shelfBg = () => blurred('aisle12_night', () => aisle12().s) + rect(0, 700, W, 60, { fill: '#8E877A', ...ink(5) }) + rect(0, 760, W, 320, { fill: '#6E685E' });
  if (it === 'wrapper') {
    let s = shelfBg();
    s += alarmClock(1240, 420, 1.4, { tape: true, time: [2, 31] });
    s += wrapperProp(820, 670, 1.25, -10);
    s += nightTint(0.7) + screenGlow(880, 640, 420, 240, '#FFF2C4', 0.32) + screenGlow(820, 660, 220, 120, '#7FD36B', 0.12, 'softS');
    return cam(s, { s: push(lt, D, [1.05, 1.18]), cx: 860, cy: 620 }) + hudAt(p.hud);
  }
  if (it === 'bottle') {
    let s = blurred('camp', () => S.campAisle()) + nightTint(0.75, '#2A2238');
    const slosh = 6 * Math.sin(tg * 1.6);
    s += g(path('M840 260 h240 v60 q70 40 70 130 v470 q0 50 -50 50 h-280 q-50 0 -50 -50 v-470 q0 -90 70 -130 z', { fill: '#CFE3EA', opacity: 0.55, ...ink(7) })
      + path(`M772 ${820 + slosh} Q960 ${800 - slosh} 1148 ${820 + slosh} V960 q0 50 -50 50 h-276 q-48 0 -48 -50 Z`, { fill: '#5E9BC8', opacity: 0.85 })
      + rect(850, 200, 220, 70, { rx: 10, fill: PAL.blue, ...ink(5) }) + rect(790, 520, 340, 140, { fill: '#FBF6EA', ...ink(4) }) + label(960, 580, 'SPRING', 40, PAL.blue) + label(960, 632, '2 L', 40, INK)
      + path('M800 380 q-10 200 0 420', { fill: 'none', stroke: '#FFFFFF', strokeWidth: 14, opacity: 0.5, strokeLinecap: 'round' }), { filter: 'url(#wobbleSoft)' });
    s += screenGlow(1300, 600, 500, 400, '#FFB866', 0.25);
    return cam(s, { s: push(lt, D, [1.0, 1.08]), cy: 600 });
  }
  if (it === 'photo') {
    let s = blurred('bright_inside', () => S2.brightInside()) + nightTint(0.78, '#2A2238') + screenGlow(1400, 760, 600, 400, '#FFB866', 0.3);
    let ph = rect(-300, -340, 600, 680, { rx: 8, fill: '#FBF8EE', ...ink(6) }) + rect(-260, -300, 520, 500, { fill: '#9FC6D9', ...ink(4) });
    ph += path('M-260 120 Q-100 40 60 110 T260 90 V200 H-260 Z', { fill: '#7FA86A', ...ink(3) }) + rect(-120, 60, 240, 160, { rx: 30, fill: PAL.red, ...ink(4) });
    ph += leoFace(0, -60, 120) + text(0, 300, 'LEO · 9 · SUMMER', { fontFamily: 'Patrick Hand, Rubik', fontSize: 50, fill: '#3A3A3A', textAnchor: 'middle' });
    s += g(ph, { transform: `translate(960 520) rotate(${f1(-4 + 0.6 * Math.sin(tg * 0.9))})`, filter: 'url(#wobbleSoft)' });
    s += g(path('M360 1100 L640 760 Q700 700 760 740 L820 800 L560 1100 Z', { fill: NORA.hoodie, ...ink(7) }) + ellipse(700, 760, 70, 56, { fill: NORA.skin, ...ink(6) })
      + path('M1560 1100 L1300 780 Q1240 720 1180 760 L1120 820 L1380 1100 Z', { fill: NORA.hoodie, ...ink(7) }) + ellipse(1220, 780, 70, 56, { fill: NORA.skin, ...ink(6) }), { filter: 'url(#wobbleSoft)' });
    s += screenGlow(960, 460, 500, 360, '#FFD9A0', 0.18);
    return cam(s, { s: push(lt, D, [1.0, 1.08]), cy: 500 });
  }
  if (it === 'drawing') {
    const mode = p.mode || 'reveal';
    let s = shelfBg() + alarmClock(1500, 420, 1.1, { tape: true, time: [2, 33] }) + drawing(780, 470, 0.86);
    const sweep = mode === 'reveal' ? easeOut(ramp(lt, 0.1, 1.4)) : 1;
    s += nightTint(0.8) + screenGlow(lerp(1500, 780, sweep), 480, 560, 420, '#FFF2C4', lerp(0.1, 0.42, sweep));
    const c = mode === 'reveal' ? { s: push(lt, D, [1.0, 1.08]), cx: 900, cy: 480 } : mode === 'close' ? { s: lerp(1.3, 1.42, ease(lt / D)), cx: 780, cy: 400 } : { s: lerp(1.75, 2.05, ease(lt / D)), cx: 780, cy: 660 };
    return cam(s, c);
  }
  return '';
};

// ---------- the split store map ----------
SH.map2 = (T, tg, lt, p, D) => {
  let s = rect(0, 0, W, H, { fill: '#EDE3CC' }) + rect(0, 0, W, H, { fill: 'url(#graph)' });
  const X = 260, Y = 150, w = 1400, h = 760, mode = p.mode || 'split', show = p.show || 'none';
  const lbl = (x, y, t, col = INK, size = 20) => text(x, y, t, { fontFamily: 'Rubik', fontWeight: 800, fontSize: size, fill: col, textAnchor: 'middle', letterSpacing: 2 });
  s += label(260, 100, mode === 'pipes' ? 'FRESHWAY · WATER PIPES' : 'FRESHWAY · DAY 8 · WHO HAS WHAT', 28, INK, 'start', 4);
  let m = rect(X, Y, w, h, { fill: '#F7EFDC', ...ink(7) });
  const BACK = [X, Y, 560, 230];   // Dale's: the stockroom block with the freezer
  const dim = (show === 'back' || show === 'wall') ? 0.45 : 1;
  for (let i = 0; i < 14; i++) m += rect(X + 200 + i * 75, Y + 290, 36, 330, { fill: '#D9CDB2', ...ink(3) });
  m += rect(X + w - 260, Y + 20, 230, 110, { fill: '#E3D6C1', ...ink(4) }) + lbl(X + w - 145, Y + 85, 'OFFICE');
  m += rect(X, Y + h - 110, w, 110, { fill: '#CFE3EA', ...ink(5) }) + lbl(X + w / 2, Y + h - 45, 'FRONT ENTRANCE', '#3E6E9A', 24);
  m += rect(X + 40, Y + h - 260, 170, 110, { fill: '#D7E4D8', ...ink(4) }) + lbl(X + 125, Y + h - 198, 'RESTROOM', '#3E6E5A', 16);
  m += rect(BACK[0], BACK[1], BACK[2], BACK[3], { fill: '#C8D8DE', ...ink(5) }) + lbl(X + 280, Y + 80, 'STOCKROOM', INK, 26) + rect(X + 30, Y + 120, 180, 80, { fill: '#9DB6C8', ...ink(3) }) + lbl(X + 120, Y + 168, 'FREEZER', '#3E6E9A', 16);
  // the water wall: a row of blue bottles along the stockroom's edge
  let wall = '';
  for (let i = 0; i < 18; i++) wall += rect(X + 20 + i * 30, Y + BACK[3] - 2, 22, 34, { rx: 6, fill: '#5E9BC8', stroke: INK, strokeWidth: 2 });
  m += wall;
  m += rect(X + 420, Y + BACK[3] - 40, 120, 40, { fill: '#9AA0A6', ...ink(3) }) + lbl(X + 480, Y + BACK[3] - 14, 'DOORS', '#2B2F33', 14);
  s += g(m, { filter: 'url(#wobbleSoft)' });
  const appear = (age) => clamp(age * 3);
  if (mode === 'pipes') {
    // pipes from the restroom up the side wall and along the back into the stockroom
    const d = `M${X + 125} ${Y + h - 260} V${Y + 270} H${X + 300} V${Y + BACK[3] - 40}`;
    s += path(d, { fill: 'none', stroke: '#5E9BC8', strokeWidth: 16, strokeLinecap: 'round', strokeLinejoin: 'round', opacity: 0.9 }) + path(d, { fill: 'none', stroke: INK, strokeWidth: 3, strokeDasharray: '2 14' });
    const k = ((lt * 0.55) % 1), pts = [[X + 125, Y + h - 260], [X + 125, Y + 270], [X + 300, Y + 270], [X + 300, Y + BACK[3] - 40]];
    const segs = [pts[0][1] - pts[1][1], pts[2][0] - pts[1][0], pts[2][1] - pts[3][1]], tot = segs.reduce((a, b) => a + b, 0);
    let dd = k * tot, q = pts[0];
    if (dd < segs[0]) q = [pts[0][0], pts[0][1] - dd]; else if ((dd -= segs[0]) < segs[1]) q = [pts[1][0] + dd, pts[1][1]]; else { dd -= segs[1]; q = [pts[2][0], pts[2][1] - dd]; }
    s += rings(q[0], q[1], tg, { color: PAL.red, max: 60, period: 0.5, op: 0.8, width: 4, n: 2 }) + circle(q[0], q[1], 12, { fill: PAL.red, ...ink(3) });
    s += g(circle(X + 300, Y + 120, 30, { fill: '#3E6E9A', ...ink(4) }) + lbl(X + 300, Y + 128, 'D', '#FFF', 26), {}) + rings(X + 300, Y + 120, tg * 0.8, { color: '#3E6E9A', max: 90, period: 1.4, op: 0.5, width: 4, n: 2 });
    s += g(circle(X + 125, Y + h - 300, 26, { fill: PAL.phones, ...ink(4) }) + lbl(X + 125, Y + h - 292, 'YOU', '#FFF', 16), {});
    return cam(s, { s: push(lt, D, [1.0, 1.05]), cx: 760, cy: 560 });
  }
  // territory overlays
  const front = show === 'front' || show === 'both', backOn = show === 'back' || show === 'both' || show === 'wall';
  if (front) s += g(path(`M${X} ${Y + BACK[3] + 30} H${X + w} V${Y + h} H${X} Z M${X + BACK[2]} ${Y} H${X + w} V${Y + BACK[3] + 30} H${X + BACK[2]} Z`, { fill: PAL.phones, opacity: 0.22 }), { opacity: f1(appear(lt - 0.1) * 100) / 100 });
  if (backOn) s += g(rect(BACK[0], BACK[1], BACK[2], BACK[3] + 30, { fill: '#3E6E9A', opacity: 0.25 }), { opacity: f1(appear(lt - 0.1) * 100) / 100 });
  // the border line draws itself in
  const bk = show === 'none' ? ease(ramp(lt, 0.4, 2.0)) : 1;
  s += path(`M${X} ${Y + BACK[3] + 30} H${X + BACK[2]} V${Y}`, { fill: 'none', stroke: PAL.red, strokeWidth: 10, strokeDasharray: '26 14', strokeLinecap: 'round', pathLength: 100, strokeDashoffset: 0, opacity: f1(bk * 100) / 100 });
  const tagAt = (x, y, txt, col, age) => { const k = back(age / 0.3); return k <= 0.01 ? '' : g(rect(x - 110, y - 34, 220, 64, { rx: 12, fill: col, ...ink(4) }) + lbl(x, y + 10, txt, '#FFF', 30), { transform: `translate(${x} ${y}) scale(${f1((0.6 + 0.4 * k) * 100) / 100}) translate(${-x} ${-y})`, opacity: f1(clamp(k) * 100) / 100 }); };
  if (front) s += tagAt(X + 980, Y + 470, 'YOURS', PAL.phones, lt - 0.3);
  if (backOn) s += tagAt(X + 280, Y + 40 + 20, "DALE'S", '#3E6E9A', lt - 0.3);
  if (show === 'front') {
    s += g(rect(X + 830, Y + 520, 330, 170, { rx: 12, fill: '#FBF6EA', ...ink(4) }), { opacity: f1(appear(lt - 0.6) * 100) / 100 });
    ['14 AISLES', '8,000 CANS', "GARY'S OFFICE"].forEach((t, i) => { s += g(lbl(X + 995, Y + 568 + i * 46, t, INK, 30), { opacity: f1(appear(lt - 0.8 - i * 0.5) * 100) / 100 }); });
  }
  if (show === 'wall') s += g(rect(X + 10, Y + BACK[3] - 10, 560, 54, { fill: 'none', stroke: PAL.red, strokeWidth: 8, rx: 10 }) + rect(X + 120, Y + BACK[3] + 52, 340, 56, { rx: 10, fill: '#FBF6EA', ...ink(4) }) + lbl(X + 290, Y + BACK[3] + 92, 'ALL YOUR WATER', PAL.red, 34), { opacity: f1(appear(lt - 0.2) * 100) / 100 });
  if (show === 'both') {
    s += g(circle(X + 300, Y + 140, 30, { fill: '#3E6E9A', ...ink(4) }) + lbl(X + 300, Y + 149, 'D', '#FFF', 28) + circle(X + 900, Y + 560, 30, { fill: PAL.phones, ...ink(4) }) + lbl(X + 900, Y + 569, 'Y', '#FFF', 28), {});
    s += bang('?', X + 600, Y + 360, lt - 1.6, { size: 200, rot: 6, life: 99, fill: PAL.red });
  }
  const zoom = show === 'wall' ? { s: lerp(1.25, 1.45, ease(lt / D)), cx: X + 300, cy: Y + 220 } : show === 'back' ? { s: lerp(1.15, 1.3, ease(lt / D)), cx: X + 300, cy: Y + 160 } : { s: push(lt, D, [1.0, 1.05]), cx: 960, cy: 540 };
  return cam(s, zoom);
};

// ---------- the stockroom doors ----------
SH.stockdoors = (T, tg, lt, p, D) => {
  const mode = p.mode || 'jammed', night = mode === 'shadow';
  let s = set('stockdoors', () => S2.stockDoors());
  // what's behind the round windows
  const win = (cx) => `<clipPath id="sd${cx}"><circle cx="${cx}" cy="380" r="60"/></clipPath>`;
  s += win(779) + win(1141);
  if (mode === 'jammed' || mode === 'chain') {
    // pallets of bottled water pushed up against the far side
    const wall = (x0) => { let o = ''; for (let r = 0; r < 4; r++) for (let i = 0; i < 6; i++) o += rect(x0 - 90 + i * 40 - (r % 2) * 18, 322 + r * 30, 34, 28, { rx: 7, fill: '#5E9BC8', stroke: INK, strokeWidth: 2 }); return o; };
    s += g(wall(779), { clipPath: 'url(#sd779)' }) + g(wall(1141), { clipPath: 'url(#sd1141)' });
  }
  if (night) {
    // Dale's silhouette in the right window: cap, shoulders, the red LED of his radio
    const sway = 3 * Math.sin(tg * 0.7);
    s += g(circle(1141, 380, 62, { fill: '#4A5E7A' }) + circle(1141, 370, 36, { fill: '#6A82A0', opacity: 0.6 }), { clipPath: 'url(#sd1141)' });   // a lamp somewhere behind him
    s += g(circle(1141 + sway, 372, 30, { fill: '#090B0F' }) + rect(1105 + sway, 336, 74, 16, { rx: 6, fill: '#090B0F' }) + rect(1081 + sway, 400, 120, 60, { rx: 24, fill: '#090B0F' })
      + circle(1176 + sway, 410, 5, { fill: PAL.red }), { clipPath: 'url(#sd1141)' });
  }
  const thumps = sfxAt(T, 'thump_metal', tg - lt, tg - lt + D), th = hits(tg, thumps, 9);
  if (mode === 'chain') {
    // a chain wrapped through both handles, a padlock hanging from it
    const k = easeOut(ramp(lt, 0.2, 1.2)), sw = 6 * Math.sin(tg * 3) * (1 - ramp(lt, 1.5, 3));
    let ch = '';
    for (let i = 0; i < 16; i++) { const x = lerp(900, 1020, i / 15), y = 580 + 10 * Math.sin(i * 0.9); ch += ellipse(x, y, 13, 8, { fill: 'none', stroke: '#8E9499', strokeWidth: 7, transform: `rotate(${i % 2 ? 60 : -30} ${f1(x)} ${f1(y)})` }); }
    s += g(ch, { transform: `translate(0 ${f1((1 - k) * 260)})`, opacity: f1(clamp(k * 2) * 100) / 100 });
    s += g(rect(-30, 0, 60, 60, { rx: 10, fill: '#C9A43A', ...ink(4) }) + path('M-18 0 V-24 Q0 -46 18 -24 V0', { fill: 'none', stroke: '#8E9499', strokeWidth: 9 }), { transform: `translate(960 ${f1(640 + (1 - k) * 260)}) rotate(${f1(sw)})`, filter: 'url(#wobbleSoft)' });
    const lockT = sfxAt(T, 'lock_click', tg - lt, tg - lt + D)[0];
    if (lockT !== undefined) s += bang('CLICK', 1220, 700, tg - lockT, { size: 80, life: 0.9, fill: '#F3EBDD' });
    s += g(sleeve('M0 1100 L620 640 L740 740 L260 1100 Z') + mitt(780, 640, -24, 1.3) + sleeve('M1920 1100 L1300 660 L1180 760 L1660 1100 Z') + mitt(1140, 660, 24, 1.3), { filter: 'url(#wobbleSoft)', transform: `translate(0 ${f1(ease(ramp(lt, 1.4, 2.2)) * 260)})` });
  }
  s += night ? nightTint(0.88) + screenGlow(1141, 380, 90, 90, '#3A4A6A', 0.4) : nightTint(0.35, '#6E6A8A');
  const c = mode === 'shadow' ? { s: lerp(1.25, 1.45, ease(lt / D)), cx: 1100, cy: 420 } : { s: push(lt, D, [1.0, 1.06]), cx: 960, cy: 500, ...shake(tg, th * 0.8) };
  return cam(s, c) + (th > 0.05 ? '' : '') + hudAt(p.hud);
};

// ---------- the staff restroom ----------
SH.restroom = (T, tg, lt, p, D) => {
  const v = p.view || 'sink', t0 = tg - lt;
  if (v === 'sink') {
    let s = set('restroom', () => S2.restroom());
    s += hero({ x: 690, y: 905, s: 1.35, pose: 'reach', expr: 'neutral', facing: -1, look: -0.4, blink: autoBlink(lt, 2), breathe: 0.01 * Math.sin(tg * 2.2) });
    s += nightTint(0.3, '#6E7A8A') + screenGlow(960, 60, 600, 200, '#F6F1DE', 0.25);
    return cam(s, { s: push(lt, D, [1.0, 1.06]), cx: 800, cy: 540 }) + hudAt(p.hud);
  }
  if (v === 'faucet') {
    let s = set('faucet', () => S2.faucetClose());
    const coughs = sfxAt(T, 'pipe_cough', t0 - 0.5, t0 + D);
    // each cough: a spurt and a few drops; after the last one, a single drip
    for (const c of coughs) {
      const a = tg - c; if (a < 0 || a > 0.9) continue;
      const k = Math.exp(-a * 5), len = 220 * k;
      s += path(`M930 500 q${f1(10 * Math.sin(a * 40))} ${f1(len * 0.5)} ${f1(-6)} ${f1(len)}`, { fill: 'none', stroke: '#8FB8D0', strokeWidth: f1(30 * k + 4), strokeLinecap: 'round', opacity: 0.9 });
      for (let i = 0; i < 6; i++) { const dy = a * 900 * (0.6 + i * 0.1), dx = (i - 2.5) * 18 * a * 3; if (500 + dy < 820) s += ellipse(930 + dx, 520 + dy, 7, 11, { fill: '#8FB8D0', ...ink(2) }); }
      s += bang(c === coughs[0] ? 'KHH!' : 'PFT!', 1250, 380, a, { size: 110, life: 0.8, rot: 8, fill: '#E8E1D2' });
    }
    const last = coughs.length ? coughs[coughs.length - 1] : t0 + 99, da = tg - last - 1.0;
    if (da > 0) { const k = (da % 1.4) / 1.4; s += ellipse(930, lerp(505, 800, easeIn(k)), 8, 12, { fill: '#8FB8D0', ...ink(2), opacity: f1((1 - ramp(k, 0.85, 1)) * 100) / 100 }); }
    s += nightTint(0.3, '#6E7A8A');
    return cam(s, { s: push(lt, D, [1.0, 1.05]), cx: 900, cy: 560, ...shake(tg, hits(tg, coughs, 10) * 0.35) });
  }
  if (v === 'heater') {
    let s = set('heater', () => S2.heaterCloset());
    s += hero({ x: 1500, y: 1000, s: 1.4, pose: 'stand', expr: 'neutral', facing: -1, look: -0.5, blink: autoBlink(lt, 1), breathe: 0.01 * Math.sin(tg * 2.2) });
    s += nightTint(0.4, '#5A5470') + screenGlow(1300, 400, 500, 400, '#FFF2C4', 0.25);
    return cam(s, { s: push(lt, D, [1.0, 1.1]), cx: 980, cy: 520 });
  }
  if (v === 'drain') {
    let s = set('drain', () => S2.drainClose());
    const sq = sfxAt(T, 'valve_squeak', t0 - 0.5, t0 + D)[0] ?? t0 + 0.4, po = sfxAt(T, 'water_pour', t0 - 0.5, t0 + D)[0] ?? sq + 0.6;
    const turn = ease(ramp(tg, sq - 0.1, sq + 0.6)) * 90;
    s += g(rect(-90, -22, 180, 44, { rx: 18, fill: PAL.red, ...ink(5) }) + circle(0, 0, 20, { fill: '#C9A43A', ...ink(4) }), { transform: `translate(960 560) rotate(${f1(turn)})`, filter: 'url(#wobbleSoft)' });
    s += g(sleeve('M1920 1100 L1300 700 L1180 800 L1600 1100 Z') + mitt(1110, 590, 30 + turn * 0.3, 1.2), { filter: 'url(#wobbleSoft)', transform: `translate(${f1(ease(ramp(tg, sq + 0.8, sq + 1.5)) * 1000)} ${f1(ease(ramp(tg, sq + 0.8, sq + 1.5)) * 600)})` });
    if (tg > po) {
      const a = tg - po, clear = ease(ramp(a, 2.2, 3.4));
      const col = `rgb(${Math.round(lerp(140, 150, clear))},${Math.round(lerp(96, 190, clear))},${Math.round(lerp(52, 220, clear))})`;
      const k = ease(ramp(a, 0, 0.3)), wv = 6 * Math.sin(tg * 30);
      s += path(`M960 720 q${f1(wv)} 60 0 ${f1(120 * k)} V${f1(720 + 180 * k)}`, { fill: 'none', stroke: col, strokeWidth: 34, strokeLinecap: 'round', opacity: 0.92 });
      s += ellipse(960, 830, f1(240 * clamp(a / 3)), f1(36 * clamp(a / 3)), { fill: col, opacity: 0.8 });
      for (let i = 0; i < 4; i++) { const q = ((tg * 2.2 + i / 4) % 1); s += ellipse(960 + (i - 1.5) * 60 * q, 830 - 40 * Math.sin(q * Math.PI), 8, 10, { fill: col, opacity: f1((1 - q) * 80) / 100 }); }
    }
    s += nightTint(0.4, '#5A5470') + screenGlow(960, 560, 400, 300, '#FFF2C4', 0.2);
    return cam(s, { s: push(lt, D, [1.0, 1.06]), cx: 960, cy: 640 });
  }
  if (v === 'tanks') {
    let s = set('toilet', () => S2.toiletClose());
    const cl = sfxAt(T, 'lid_clunk', t0 - 0.5, t0 + D)[0] ?? t0 + 0.6;
    const up = ease(ramp(tg, cl - 0.5, cl - 0.05));
    // the water inside the open tank
    s += rect(690, 268, 540, 60, { rx: 10, fill: '#5E9BC8', opacity: f1(up * 85) / 100, ...ink(3) }) + path('M720 290 q60 -10 120 0 t120 0 t120 0 t120 0', { fill: 'none', stroke: '#DCEFFA', strokeWidth: 5, opacity: f1(up * 0.8 * 100) / 100 });
    const lx = 960 + up * 330, ly = 250 - up * 110;
    s += g(rect(-320, -34, 640, 68, { rx: 18, fill: '#F4F2EC', ...ink(7) }), { transform: `translate(${f1(lx)} ${f1(ly)}) rotate(${f1(up * 12)})`, filter: 'url(#wobbleSoft)' });
    s += g(sleeve(`M1960 1100 L${f1(lx + 250)} ${f1(ly + 10)} L${f1(lx + 380)} ${f1(ly + 90)} L1960 860 Z`) + mitt(lx + 270, ly + 10, 20, 1.15), { filter: 'url(#wobbleSoft)' });
    s += nightTint(0.3, '#6E7A8A');
    return cam(s, { s: push(lt, D, [1.0, 1.06]), cx: 980, cy: 470 });
  }
  if (v === 'pipes_dark') {
    let s = set('pipeswall', () => S2.pipesWall());
    const knocks = sfxAt(T, 'pipe_knock', t0 - 0.2, t0 + D), kk = hits(tg, knocks, 7);
    s = g(s, { transform: `translate(0 ${f1(kk * 6 * Math.sin(tg * 90))})` });
    s += nightTint(0.9) + screenGlow(700, 520, 520, 120, '#6A7A9A', 0.25);
    for (const k of knocks) { const a = tg - k; if (a > 0 && a < 1.6) s += rings(1360, 520, a, { color: '#8FB3D5', max: 260, period: 1.6, op: 0.8 * (1 - a / 1.6), width: 5, n: 1 }); }
    s += bang('TAP', 1500, 400, tg - (knocks[0] ?? 1e9), { size: 90, life: 0.9, fill: '#8FB3D5' });
    if (p.voice) {
      // while Dale's voice comes through, a faint wave rides along the middle pipe
      const L = T.voice.lines.find((x) => x.who === 'DALE' && tg >= x.start - 0.1 && tg < x.start + x.dur + 0.3);
      if (L) { let wv = ''; for (let i = 0; i < 40; i++) { const a = 0.3 + 0.7 * Math.abs(Math.sin(tg * 11 + i * 0.6) * Math.sin(tg * 4.1 + i * 0.3)); wv += rect(200 + i * 30, 520 - a * 50, 12, a * 100, { rx: 6, fill: '#8FB3D5', opacity: 0.55 }); } s += wv; }
    }
    return cam(s, { s: push(lt, D, [1.0, 1.08]), cx: 1100, cy: 540 });
  }
  return '';
};

// ---------- cards ----------
SH.card2 = (T, tg, lt, p, D) => {
  const k = p.kind;
  const pop = (inner, age, x = W2, y = H / 2) => { const kk = back(age / 0.3); if (kk <= 0.001) return ''; return g(inner, { transform: `translate(${x} ${y}) scale(${(0.7 + 0.3 * kk).toFixed(3)}) translate(${-x} ${-y})`, opacity: f1(clamp(age / 0.18) * 100) / 100 }); };
  if (k === 'morse') {
    let s = rect(0, 0, W, H, { fill: PAL.card }) + smallCaps(W2, 170, 'MORSE CODE', 34, '#B9AE97');
    const groups = [['S', [0, 0, 0]], ['O', [1, 1, 1]], ['S', [0, 0, 0]]], third = D / 3.2;
    groups.forEach(([L, marks], gi) => {
      const cx = 440 + gi * 520;
      marks.forEach((m, i) => {
        const a = lt - 0.15 - gi * third - i * 0.22, x = cx - 150 + i * 150;
        s += pop(m ? rect(x - 60, 470, 120, 50, { rx: 25, fill: PAL.tag }) : circle(x, 495, 28, { fill: PAL.tag }), a, x, 495);
      });
      s += pop(big(cx, 740, L, 200, '#F3EBDD'), lt - 0.5 - gi * third, cx, 680);
    });
    s += g(smallCaps(W2, 930, '· · ·   — — —   · · ·', 40, '#8E8576'), { opacity: f1(clamp((lt - D * 0.85) * 3) * 100) / 100 });
    return cam(s, { s: push(lt, D, [1.0, 1.03]) });
  }
  if (k === 'radios3') {
    let s = rect(0, 0, W, H, { fill: PAL.cream }) + smallCaps(W2, 160, 'RULE 3 · COUNT THE RADIOS', 36, INK);
    [['YOU', PAL.phones], ['DALE', '#3E6E9A'], ['NORA', NORA.hoodie]].forEach(([who, col], i) => {
      const x = 480 + i * 480, a = lt - 0.2 - i * 0.45;
      s += pop(g(radioProp(x, 600, 1.25, { on: true, led: i === 2 ? PAL.red : '#7FD36B' }) + rect(x - 120, 800, 240, 70, { rx: 14, fill: col, ...ink(4) }) + label(x, 848, who, 38, '#FFF')
        + circle(x - 150, 330, 44, { fill: i === 2 ? PAL.red : INK, ...ink(4) }) + label(x - 150, 348, String(i + 1), 50, '#FFF')), a, x, 600);
    });
    return cam(s, { s: push(lt, D, [1.0, 1.03]) });
  }
  if (k === 'clues') {
    let s = rect(0, 0, W, H, { fill: PAL.cream }) + smallCaps(W2, 160, 'WHAT DALE ASKED · EPISODE 1', 34, INK);
    const notes = ['HOW MANY OF YOU?', 'THE FREEZER?', 'THE ALARM?'], step = (D - 0.6) / 3;
    notes.forEach((n, i) => {
      const x = 420 + i * 540, y = 520, a = lt - 0.2 - i * step, rot = [-4, 3, -2][i];
      s += pop(g(rect(-230, -180, 460, 360, { fill: ['#FFE27A', '#FFD0A8', '#CFE8C0'][i], ...ink(5) }) + rect(-60, -200, 120, 40, { fill: '#D9C79A', opacity: 0.85 })
        + text(0, -40, `"${n}"`, { fontFamily: 'Patrick Hand, Rubik', fontSize: 50, fill: INK, textAnchor: 'middle' }) + radioProp(0, 120, 0.4, { on: true, led: PAL.red }), { transform: `translate(${x} ${y}) rotate(${rot})`, filter: 'url(#wobbleSoft)' }), a, x, y);
    });
    s += g(smallCaps(W2, 900, 'HE WAS LOOKING FOR SOMEONE', 40, PAL.red), { opacity: f1(clamp((lt - D + 1.0) * 3) * 100) / 100 });
    return cam(s, { s: push(lt, D, [1.0, 1.03]) });
  }
  if (k === 'trade') {
    let s = rect(0, 0, W, H, { fill: PAL.cream }) + smallCaps(W2, 160, "DALE'S PRICE LIST", 36, INK);
    const can = (x, y) => g(rect(-46, -62, 92, 124, { rx: 10, fill: PAL.red, ...ink(4) }) + rect(-46, -22, 92, 44, { fill: '#F3EEDF', ...ink(3) }) + ellipse(0, -62, 46, 12, { fill: '#C9C3B5', ...ink(3) }), { transform: `translate(${x} ${y})` });
    let cans = '';
    for (let i = 0; i < 20; i++) cans += can(300 + (i % 5) * 110, 380 + Math.floor(i / 5) * 140);
    s += g(cans, { filter: 'url(#wobbleSoft)', opacity: f1(clamp((lt - 0.1) * 3) * 100) / 100 });
    s += pop(text(1060, 620, '=', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 200, fill: INK, textAnchor: 'middle' }), lt - 0.6, 1060, 560);
    s += pop(g(path('M1330 300 h220 v70 q90 50 90 160 v330 q0 50 -50 50 h-300 q-50 0 -50 -50 v-330 q0 -110 90 -160 z', { fill: '#CFE3EA', ...ink(7) }) + path('M1250 640 Q1440 610 1630 640 V860 q0 50 -50 50 h-280 q-50 0 -50 -50 Z', { fill: '#5E9BC8', opacity: 0.8 })
      + rect(1340, 240, 200, 70, { rx: 10, fill: PAL.blue, ...ink(5) }) + label(1440, 560, '1 GAL', 54, INK)), lt - 0.9, 1440, 600);
    s += g(rect(1180, 870, 520, 110, { rx: 12, fill: '#F7E3C8', stroke: PAL.red, strokeWidth: 9 }) + label(1440, 945, 'TERRIBLE DEAL', 56, PAL.red), { transform: 'rotate(-6 1440 925)', opacity: f1(clamp((lt - D * 0.45) * 3) * 100) / 100 });
    return cam(s, { s: push(lt, D, [1.0, 1.03]) });
  }
  if (k === 'receipt') {
    let s = rect(0, 0, W, H, { fill: '#2A2630' }) + screenGlow(960, 560, 700, 500, '#FFB866', 0.2);
    let rc = path('M-300 -460 H300 V430 l-30 30 l-30 -30 l-30 30 l-30 -30 l-30 30 l-30 -30 l-30 30 l-30 -30 l-30 30 l-30 -30 l-30 30 l-30 -30 l-30 30 l-30 -30 l-30 30 l-30 -30 l-30 30 l-30 -30 l-30 30 l-30 -30 Z', { fill: '#F7F4EC', ...ink(6) });
    rc += text(0, -390, "NORA'S RULES", { fontFamily: 'Patrick Hand, Rubik', fontSize: 64, fill: '#3E8E86', textAnchor: 'middle' }) + line(-220, -360, 220, -360, { stroke: '#3E8E86', strokeWidth: 4 });
    const R = ['1. NEVER SLEEP ON', '   THE GROUND FLOOR', '2. SHOES OFF ON', '   THE ESCALATOR', '3. THE SOUR WORMS', '   ARE FOR LEO'];
    R.forEach((t, i) => { const a = lt - 0.4 - Math.floor(i / 2) * (D / 4); rc += g(text(-250, -270 + i * 70 + Math.floor(i / 2) * 30, t, { fontFamily: 'Patrick Hand, Rubik', fontSize: 50, fill: i >= 4 ? PAL.red : '#2B2B2B' }), { opacity: f1(clamp(a * 3) * 100) / 100 }); });
    rc += text(0, 360, 'BRIGHT TECH · TOTAL $0.00', { fontFamily: 'Rubik', fontWeight: 700, fontSize: 22, fill: '#8E8576', textAnchor: 'middle', letterSpacing: 2 });
    s += g(rc, { transform: `translate(960 560) rotate(${f1(-3 + 0.4 * Math.sin(tg * 0.8))}) scale(0.86)`, filter: 'url(#wobbleSoft)' });
    return cam(s, { s: push(lt, D, [1.0, 1.06]), cy: 500 });
  }
  return rect(0, 0, W, H, { fill: PAL.cream });
};

// ---------- hero close-ups on the new backgrounds ----------
HC_BG.stockdoors = () => blurred('stockdoors', () => S2.stockDoors()) + nightTint(0.35, '#6E6A8A');
HC_BG.brighttech = () => blurred('bright_inside', () => S2.brightInside()) + nightTint(0.75, '#2A2238') + screenGlow(1450, 700, 520, 380, '#FFB866', 0.3);
HC_BG.restroom = () => blurred('restroom', () => S2.restroom()) + nightTint(0.3, '#6E7A8A');
SH.hclose2 = (T, tg, lt, p, D) => SH.hclose(T, tg, lt, p.bg === 'brighttech' ? { ...p, warm: true } : p, D);

// ---------- Nora runs down aisle 12 toward the ringing clock ----------
SH.aisle2 = (T, tg, lt, p, D) => {
  const A = aisle12();
  let s = aisle12bg();
  const cq = at(A, 1180, 2.6);
  const ring = lt < (p.ringUntil ?? 1.4) ? 1 : 0;   // the alarm runs on into this shot, then she reaches it
  s += alarmClock(cq.x, cq.y - 470 * cq.k, 0.95 * cq.k, { ring, t: tg, tape: true });
  const k = ease(lt / Math.max(D, 0.1)), q = at(A, lerp(960, 1140, k), lerp(-0.25, 1.6, k));
  s += nora({ x: q.x, y: q.y, s: 1.45 * q.k, pose: runPose(tg * 11), expr: 'determined', facing: 1, look: 0, filter: true, tilt: 3 * Math.sin(tg * 11), back: true });
  s += nightTint(0.84) + rings(cq.x, cq.y - 470 * cq.k, tg, { color: '#FFE27A', max: 140, period: 0.8, op: 0.5 * ring, width: 4 }) + screenGlow(cq.x, cq.y - 470 * cq.k, 160, 120, '#FFE27A', 0.2 * ring);
  return cam(s, { s: push(lt, D, [1.05, 1.15]), cx: 1000, cy: 520 }) + hudAt(p.hud);
};
