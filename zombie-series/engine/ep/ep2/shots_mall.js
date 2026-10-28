// Episode 2 shot templates outside and in the mall: the blinking window, the storm, the crossing in the rain,
// the side door, the atrium, the escalator, Bright Tech, Nora, the drone. Also Nora at the staff door.
import { W, H, INK, PAL, glow, hero, zombie, crowd, grade, g, rect, circle, ellipse, line, poly, path, text, ink, layer, rng, walkPose, runPose } from '../../lib.js';
import { clamp, lerp, ease, easeOut, easeIn, back, ramp, wob, f1, autoBlink, cam, push, shake, nightTint, screenGlow, darkness,
  letterbox, quote, bang, rings, hudAt, sleeve, mitt, radioProp, label, set } from '../kit.js';
import { SH, CLOSE_BG, capsAt } from '../shots_in.js';
import * as S from '../sets.js';
import * as S2 from './sets2.js';
import { nora, NORA } from './chars.js';
import { aisle } from '../../scenes.js';

const W2 = W / 2;
const blurred = (key, make) => layer(key + '_soft', () => g(make(), { filter: 'url(#softS)' }));
const sfxAt = (T, name, t0, t1) => (T.sfx || []).filter((x) => x.name === name && x.t >= t0 - 0.01 && x.t < t1).map((x) => x.t);

// lightning: a double flicker that starts just before each thunder sound and fades
function flash(T, tg, { far = 0.45 } = {}) {
  let k = 0;
  for (const x of T.sfx || []) {
    if (x.name !== 'thunder') continue;
    const a = tg - x.t + 0.12; if (a < 0 || a > 1.2) continue;
    const env = (a < 0.06 ? a / 0.06 : Math.exp(-(a - 0.06) * 5)) * (a > 0.1 && a < 0.16 ? 0.35 : 1);
    k = Math.max(k, env * (x.p && x.p.far ? far : 1));
  }
  return k;
}
const flashLayer = (k, col = '#E8F0FF') => (k > 0.01 ? rect(0, 0, W, H, { fill: col, opacity: f1(k * 0.55 * 100) / 100, style: 'mix-blend-mode:screen' }) : '');
// rain streaks: a deterministic field that falls with time; heavier = more and longer
function rain(tg, { n = 140, len = 70, slant = 14, op = 0.45, speed = 1900, seed = 3, col = '#C9D8E8', w = 3 } = {}) {
  const r = rng(seed); let s = '';
  for (let i = 0; i < n; i++) {
    const x0 = r() * (W + 300) - 150, ph = r(), v = speed * (0.8 + r() * 0.4);
    const y = ((ph * (H + 200) + tg * v) % (H + 200)) - 100, x = x0 + (y / H) * slant * 3;
    s += line(x, y, x - slant, y + len * (0.7 + r() * 0.6), { stroke: col, strokeWidth: w, strokeLinecap: 'round', opacity: op });
  }
  return s;
}
const splashes = (tg, y0, y1, n = 26, seed = 8) => {
  const r = rng(seed); let s = '';
  for (let i = 0; i < n; i++) { const x = r() * W, y = y0 + r() * (y1 - y0), p = r() * 0.6 + 0.4, k = ((tg * 2.6 / p + r()) % 1); s += ellipse(x, y, 4 + k * 22, 1.5 + k * 6, { fill: 'none', stroke: '#C9D8E8', strokeWidth: 2, opacity: f1((1 - k) * 60) / 100 }); }
  return s;
};

// ---------- the mall window from the roof: steady, then blinking S.O.S. ----------
const SOS = [0.22, 0.22, 0.22, 0.66, 0.66, 0.66, 0.22, 0.22, 0.22];
function sosOn(t) {
  // one round of the pattern: each mark lit for its length, 0.22 s between marks, 0.5 s between letters, 1.4 s rest
  let c = 0;
  const cycle = SOS.reduce((a, d, i) => a + d + (i === 2 || i === 5 ? 0.5 : i === 8 ? 1.4 : 0.22), 0);
  t = ((t % cycle) + cycle) % cycle;
  for (let i = 0; i < SOS.length; i++) {
    if (t < c + SOS[i]) return t >= c;
    c += SOS[i] + (i === 2 || i === 5 ? 0.5 : i === 8 ? 1.4 : 0.22);
    if (t < c) return false;
  }
  return false;
}
SH.mallwin = (T, tg, lt, p, D) => {
  let s = set('mallwide_night', () => g(S.sky('night') + S.cityBand('night') + S.mallFacade({ time: 'night', x: 380, y: 150, k: 1.5 }) + rect(0, 780, W, 300, { fill: '#2E323C' }), { filter: 'url(#wobble)' }));
  const wx = 380 + 30 * 1.5 + 6 * 80 * 1.5 + 28 * 1.5, wy = 150 + 95 * 1.5 + 25 * 1.5;
  const blinking = p.mode === 'blink', on = !blinking || lt < 0.5 ? true : sosOn(lt - 0.5);
  if (!on) s += rect(wx - 42, wy - 37.5, 84, 75, { fill: '#1E2433' });
  s += nightTint(0.55);
  if (on) s += glow(wx, wy, 70, '#FFD98A', 0.7 + 0.04 * Math.sin(tg * 2)) + screenGlow(wx, wy, 220, 160, '#FFD98A', 0.12);
  // the roof parapet in the foreground keeps us on Freshway
  s += rect(0, 990, W, 90, { fill: '#2A2A30', ...ink(5) });
  const c = blinking ? { s: lerp(2.0, 2.25, ease(lt / D)), cx: wx, cy: wy + 30 } : { s: lerp(1.15, 1.8, ease(lt / D)), cx: lerp(960, wx, ease(lt / D)), cy: lerp(540, wy + 40, ease(lt / D)) };
  return cam(s, c) + hudAt(p.hud);
};

// ---------- the storm comes in ----------
SH.storm = (T, tg, lt, p, D) => {
  const fl = flash(T, tg);
  if (p.mode === 'clouds') {
    let s = set('roof_day', () => S.roofSet({ time: 'day' }));
    const dk = ease(ramp(lt, 0, D * 0.8));
    s += rect(0, 0, W, H, { fill: '#3A4250', opacity: f1((0.25 + 0.4 * dk) * 100) / 100, style: 'mix-blend-mode:multiply' });
    // a cloud bank rolling over the mall from the right
    let cl = '';
    const r = rng(14);
    for (let i = 0; i < 16; i++) { const x = 2300 - (lt * 70 + i * 140) % 2900 + r() * 100, y = 60 + r() * 260, rr = 140 + r() * 160; cl += ellipse(x, y, rr * 1.6, rr * 0.7, { fill: ['#4A5262', '#3E4656', '#565E6E'][i % 3], ...ink(4) }); }
    s += g(cl, { filter: 'url(#wobbleSoft)', opacity: f1((0.6 + 0.4 * dk) * 100) / 100 }) + flashLayer(fl);
    if (fl > 0.2) s += path('M1500 120 L1460 260 L1500 270 L1440 420', { fill: 'none', stroke: '#F3F6FF', strokeWidth: 8, strokeLinejoin: 'round', opacity: f1(fl * 100) / 100 });
    s += rain(tg, { n: Math.round(40 * dk), op: 0.3, len: 50 });
    return cam(s, { s: push(lt, D, [1.0, 1.06]), cx: 1200, cy: 500 }) + hudAt(p.hud);
  }
  // the crowd in the lot, standing in the downpour, faces up
  let s = set('lot_storm', () => g(S.sky('night') + S.cityBand('night') + rect(0, 420, W, 660, { fill: '#30343E' }), { filter: 'url(#wobble)' }));
  s += rect(0, 0, W, 430, { fill: '#2A3140', opacity: 0.6 });
  const r = rng(31);
  let cr = '';
  for (let i = 0; i < 46; i++) {
    const x = r() * W, y = 520 + r() * 520, k = 0.25 + (y - 520) / 520 * 0.75;
    cr += zombie({ x, y, s: k, outfit: ['cashier', 'jogger', 'shopper', 'park', 'nurse', 'guard', 'janitor'][i % 7], tilt: -8 + 4 * Math.sin(tg * 0.6 + i), look: 0.1 * Math.sin(i), filter: false, up: 0.9 });
  }
  s += cr;
  s += nightTint(0.62) + splashes(tg, 560, 1060, 40) + rain(tg, { n: 170, op: 0.5, len: 80 }) + flashLayer(fl);
  return cam(s, { s: push(lt, D, [1.0, 1.06]), cx: 960, cy: 620 });
};

// ---------- POV: across the lot in the rain ----------
SH.povstorm = (T, tg, lt, p, D) => {
  const ph = p.phase || 'walk', fl = flash(T, tg);
  let s = set('pov_storm', () => {
    let o = S.sky('night') + S.cityBand('night') + S.mallFacade({ time: 'night', x: 620, y: 230, k: 0.9, lit: false }) + rect(0, 620, W, 460, { fill: '#2A2E38' });
    for (let x = -100; x < W; x += 220) o += line(x, 1080, x + 160, 620, { stroke: '#E9E2C8', strokeWidth: 4, opacity: 0.25 });
    o += path('M-40 1080 L-40 640 Q120 600 340 640 L420 780 L420 1080 Z', { fill: '#3A4252', ...ink(7) }) + rect(30, 670, 280, 110, { rx: 20, fill: '#1E2433', ...ink(5) });
    return g(o, { filter: 'url(#wobble)' });
  });
  s += rect(0, 0, W, 620, { fill: '#2A3140', opacity: 0.5 });
  const walkX = ph === 'walk' ? lt * 30 : ph === 'crowd' ? 200 + lt * 60 : 0;
  // the dead standing in the rain, faces up; nearer ones bigger
  const r = rng(ph === 'pass' ? 61 : 17);
  let z = '';
  const N = ph === 'walk' ? 10 : 14;
  const rows = [];
  for (let i = 0; i < N; i++) rows.push({ x: r() * 2200 - 140, y: 640 + r() * (ph === 'walk' ? 120 : 330), o: ['cashier', 'jogger', 'shopper', 'park', 'nurse', 'guard', 'janitor'][i % 7], ph: r() * 6 });
  rows.sort((a, b) => a.y - b.y);
  for (const q of rows) {
    const k = 0.35 + (q.y - 640) / 330 * 1.1, x = q.x - walkX * k;
    z += zombie({ x, y: q.y + 60 * k, s: k, outfit: q.o, tilt: -8 + 4 * Math.sin(tg * 0.5 + q.ph), look: 0, filter: false, sway: 1.5 * Math.sin(tg * 0.6 + q.ph), up: 0.9 });
  }
  s += z;
  if (ph === 'bottle' || ph === 'freeze') {
    const k = ph === 'bottle' ? easeOut(ramp(lt, Math.max(0, D - 0.6), D + 2.0)) : 1;
    const bx = lerp(980, 1500, k), by = lerp(880, 820, k), rot = k * 900;
    s += g(rect(-60, -22, 120, 44, { rx: 20, fill: '#9FC6D9', opacity: 0.85, ...ink(4) }) + rect(60, -12, 26, 24, { rx: 5, fill: PAL.blue, ...ink(3) }), { transform: `translate(${f1(bx)} ${f1(by)}) rotate(${f1(rot)})`, filter: 'url(#wobbleSoft)' });
    if (ph === 'freeze') s += zombie({ x: 520, y: 1650, s: 2.8, outfit: 'shopper', tilt: -10 + 2 * Math.sin(tg * 0.6), look: 0.3 * ease(ramp(lt, 0.3, 1.2)), sway: 0.6 * Math.sin(tg * 0.5), up: lerp(0.9, 0.3, ease(ramp(lt, 0.3, 1.2))) });
  }
  if (ph === 'pass') {
    // one of them right beside you; you slide past it
    const k = ease(ramp(lt, 0.2, D));
    s += zombie({ x: lerp(1500, 1180, k), y: 1700, s: 3.2, outfit: 'jogger', tilt: -10 + 2 * Math.sin(tg * 0.7), look: 0, sway: 0.8 * Math.sin(tg * 0.5), up: 0.9 });
    s += path(`M${f1(lerp(1500, 1180, k) - 40)} 820 q-6 60 0 120`, { fill: 'none', stroke: '#C9D8E8', strokeWidth: 6, opacity: 0.6 });   // rain running down its face
  }
  s += nightTint(0.5) + splashes(tg, 680, 1060, 34) + rain(tg, { n: 190, op: 0.55, len: 90, slant: 18 }) + flashLayer(fl);
  if (ph === 'walk') s += g(sleeve('M0 1080 L240 880 L400 960 L290 1080 Z') + mitt(320, 900, -20, 1.1), { filter: 'url(#wobbleSoft)' });
  s += darkness(0.5, 0.5, 0.65, 0.65, 'psd');
  const bob = ph === 'pass' || ph === 'freeze' ? Math.sin(lt * 3) * 3 : Math.sin(lt * 4.4) * 8;
  s = cam(s, { s: 1.05, x: wob(tg * 0.7, 1) * 5 - (ph === 'pass' ? ease(lt / D) * 80 : 0), y: bob });
  return s + letterbox() + capsAt(T, tg);
};

// ---------- the mall's side door ----------
SH.malldoor = (T, tg, lt, p, D) => {
  const fl = flash(T, tg);
  let s = set('mallsidedoor', () => S2.mallSideDoor());
  const brk = p.mode === 'broken' ? -10 : typeof p.at === 'number' ? p.at : (sfxAt(T, 'glass_break', tg - lt - 0.1, tg - lt + D)[0] ?? 1e9) - (tg - lt);
  const dry = p.mode === 'broken';
  // the chain on the doors
  let ch = '';
  for (let i = 0; i < 22; i++) { const x = lerp(470, 1030, i / 21), y = 535 + 18 * Math.sin(i * 0.8); ch += ellipse(x, y, 16, 10, { fill: 'none', stroke: '#8E9499', strokeWidth: 8, transform: `rotate(${i % 2 ? 60 : -30} ${f1(x)} ${f1(y)})` }); }
  s += g(ch + rect(720, 560, 70, 76, { rx: 12, fill: '#C9A43A', ...ink(4) }) + path('M735 560 V530 Q755 500 775 530 V560', { fill: 'none', stroke: '#8E9499', strokeWidth: 10 }), { filter: 'url(#wobbleSoft)' });
  const broken = lt >= brk, a = lt - brk;
  if (!broken) s += path('M1160 300 L1440 820 M1200 820 L1450 320', { stroke: '#9FB8C4', strokeWidth: 6, opacity: 0.2 });
  else {
    // the pane is gone: a dark hole into the mall, shards on the ground and in the air
    s += rect(1120, 250, 360, 610, { fill: '#0E1118' });
    s += poly([[1120, 250], [1220, 250], [1150, 360], [1120, 420]], { fill: '#3A4656', ...ink(3) }) + poly([[1480, 860], [1380, 860], [1440, 760], [1480, 700]], { fill: '#3A4656', ...ink(3) });
    const r = rng(9);
    for (let i = 0; i < 26; i++) {
      const ang = -Math.PI * (0.15 + r() * 0.9), sp = 300 + r() * 700, tt = Math.min(a, 1.2);
      const x = 1300 + Math.cos(ang) * sp * tt * (1 - tt * 0.3), y = 560 + Math.sin(ang) * sp * tt + 900 * tt * tt;
      const yy = Math.min(y, 880 + r() * 120), sz = 10 + r() * 26;
      s += poly([[x, yy - sz], [x + sz * 0.7, yy + sz * 0.3], [x - sz * 0.4, yy + sz * 0.5]], { fill: '#BFD3E6', opacity: 0.85, stroke: INK, strokeWidth: 2, transform: `rotate(${f1(i * 47 + a * 200)} ${f1(x)} ${f1(yy)})` });
    }
    if (!dry) s += bang('KRA-KOOM!', 1260, 330, a, { size: 150, life: 1.3, rot: -6 });
  }
  s += dry ? nightTint(0.7) : nightTint(0.55) + rain(tg, { n: 150, op: 0.5, len: 80 }) + splashes(tg, 870, 1070, 24) + flashLayer(fl);
  if (dry) {
    // the two of you slipping out through the hole, toward the lot
    const k = ease(lt / D);
    s += nora({ x: lerp(1300, 1700, k), y: 1080, s: 1.6, pose: walkPose(tg * 6), expr: 'worried', facing: 1, look: 0.3 });
    s += hero({ x: lerp(1120, 1520, k), y: 1100, s: 1.65, pose: walkPose(tg * 6 + 2), expr: 'worried', facing: 1, look: 0.3 });
  } else {
    // your arm and the hammer: it rises for the swing, then snaps forward through the glass
    const raise = broken ? 0 : ease(ramp(lt, brk - 0.9, brk - 0.12)), hitK = broken ? easeOut(ramp(lt, brk, brk + 0.12)) * (1 - ease(ramp(lt, brk + 0.5, brk + 1.4))) : 0;
    const hx = lerp(lerp(1560, 1640, raise), 1380, hitK), hy = lerp(lerp(860, 600, raise), 640, hitK), ang = lerp(lerp(-30, -75, raise), 10, hitK);
    s += g(sleeve(`M1960 1180 L${f1(hx - 40)} ${f1(hy + 60)} L${f1(hx + 90)} ${f1(hy + 160)} L1960 980 Z`)
      + g(rect(-12, -230, 24, 250, { rx: 8, fill: '#8E5B3A', ...ink(5) }) + rect(-70, -270, 140, 54, { rx: 10, fill: '#5E6670', ...ink(5) }) + path('M70 -262 q40 -10 50 -40', { fill: 'none', stroke: '#5E6670', strokeWidth: 16, strokeLinecap: 'round' }), { transform: `translate(${f1(hx)} ${f1(hy)}) rotate(${f1(ang)})` })
      + mitt(hx + 10, hy + 10, ang + 20, 1.05), { filter: 'url(#wobbleSoft)' });
  }
  return cam(s, { s: push(lt, D, [1.0, 1.06]), cx: 1150, cy: 560, ...shake(tg, broken && a < 0.5 ? 1.2 * (1 - a * 2) : 0) }) + hudAt(p.hud);
};

// ---------- the atrium ----------
function fountainCrowd(tg, cx, cy, k, n = 30, seed = 23) {
  const r = rng(seed), out = [];
  for (let i = 0; i < n; i++) {
    const a = r() * Math.PI * 2, rr = 1 + r() * 0.35, x = cx + Math.cos(a) * 430 * k * rr, y = cy + Math.sin(a) * 110 * k * rr;
    out.push({ x, y, o: ['shopper', 'guard', 'cashier', 'jogger', 'park', 'nurse', 'pretzel', 'suit'][i % 8], ph: r() * 6, s: (0.5 + (y - cy + 110 * k) / (220 * k) * 0.25) * k });
  }
  out.sort((a, b) => a.y - b.y);
  return out.map((q) => zombie({ x: q.x, y: q.y, s: q.s, outfit: q.o, tilt: -6 + 6 * Math.sin(tg * 0.5 + q.ph), look: 0.2 * Math.sin(tg * 0.3 + q.ph), sway: 1.4 * Math.sin(tg * 0.6 + q.ph), filter: false })).join('');
}
SH.atrium = (T, tg, lt, p, D) => {
  const mode = p.mode || 'wide', fl = flash(T, tg);
  if (mode === 'skylight') {
    let s = rect(0, 0, W, H, { fill: '#2A3448' });
    const r = rng(19);
    for (let i = 0; i < 14; i++) { const x = ((r() * 2600 + tg * (30 + r() * 30)) % 2600) - 340, y = r() * 900; s += ellipse(x, y, 260 + r() * 200, 90 + r() * 70, { fill: ['#3A4458', '#323C50', '#46506A'][i % 3], opacity: 0.9 }); }
    s += flashLayer(fl, '#DDE6FF') + set('skylight', () => S2.skylight());
    for (let i = 0; i < 22; i++) { const x = (i * 97) % W, ph = (tg * 0.35 + i * 0.37) % 1, y0 = ph * 1300 - 200; s += path(`M${x} ${f1(y0)} q8 40 -2 80 t4 80`, { fill: 'none', stroke: '#9FB8D0', strokeWidth: 5, opacity: 0.45, strokeLinecap: 'round' }); }
    s += splashes(tg, 0, 980, 70, 4) + rain(tg, { n: 60, op: 0.2, len: 30, slant: 0, speed: 900 });
    s += nightTint(0.35);
    return cam(s, { s: push(lt, D, [1.0, 1.08]), cy: 420 });
  }
  if (mode === 'after') {
    // the storm is over: low evening sun through the glass roof, long shafts of light, the dead gone still
    let s = set('atrium', () => S2.atrium()) + fountainCrowd(tg * 0.5, 960, 975, 1.0, 30);
    s += nightTint(0.5, '#5A4A6A');
    for (const [x, w, o] of [[420, 160, 0.16], [880, 220, 0.2], [1380, 180, 0.14]]) s += poly([[x, 0], [x + w, 0], [x + w + 260, H], [x + 140, H]], { fill: '#F2B88A', opacity: o, style: 'mix-blend-mode:screen', filter: 'url(#softS)' });
    s += screenGlow(960, 60, 900, 160, '#F2B88A', 0.3);
    return cam(s, { s: push(lt, D, [1.0, 1.06]), cx: 960, cy: 560 }) + hudAt(p.hud);
  }
  let s = set('atrium', () => S2.atrium());
  // rain sheeting down the glass roof
  s += g(rain(tg, { n: 50, op: 0.35, len: 40, slant: 4, speed: 600 }), { clipPath: 'url(#roofclip)' }) + '<clipPath id="roofclip"><rect x="0" y="0" width="1920" height="150"/></clipPath>';
  if (mode === 'fountain') s += fountainCrowd(tg, 960, 975, 1.0, 30);
  else s += fountainCrowd(tg, 960, 975, 1.0, 12, 5);
  s += nightTint(0.6) + screenGlow(960, 80, 900, 160, '#6A7A9A', 0.3) + flashLayer(fl * 0.8, '#DDE6FF');
  if (mode === 'climb') {
    // you, small, on the balcony of this level, walking along the railing
    const lv = p.level || 2, y = { 2: 640, 3: 470, 4: 300 }[lv], k = ease(lt / D);
    const cfg = { 2: { hx: [560, 900], cx: [700, 900] }, 3: { hx: [520, 820], cx: [380, 520] } }[lv] || { hx: [700, 1150], cx: [820, 1080] };
    if (lv === 2) s += g(Array.from({ length: 6 }, (_, i) => { const bx = 600 + i * 58, by = 600 + (i % 2) * 8; return circle(bx, by, 20, { fill: '#B5652F', ...ink(3) }) + circle(bx - 14, by - 18, 8, { fill: '#B5652F', ...ink(2) }) + circle(bx + 14, by - 18, 8, { fill: '#B5652F', ...ink(2) }) + circle(bx - 6, by - 2, 2.5, { fill: INK }) + circle(bx + 6, by - 2, 2.5, { fill: INK }); }).join(''), { filter: 'url(#wobbleSoft)' });
    if (lv === 3) s += g(rect(180, 360, 120, 150, { fill: '#E9B93E', ...ink(3) }) + rect(192, 372, 96, 80, { fill: '#3A2A3A' }) + circle(240, 405, 18, { fill: PAL.zSkin, ...ink(2) }) + label(240, 476, 'COMING', 16, INK) + label(240, 498, 'SOON', 19, PAL.red), { filter: 'url(#wobbleSoft)' });
    s += hero({ x: lerp(cfg.hx[0], cfg.hx[1], k), y: y - 12, s: 0.42, pose: walkPose(tg * 6), expr: 'worried', facing: 1, look: 0.2 });
    const c = { s: 2.0, cx: lerp(cfg.cx[0], cfg.cx[1], k), cy: y - 90 };
    return cam(s, c) + hudAt(p.hud || MALLHUD(lv));
  }
  const c = mode === 'fountain' ? { s: lerp(1.5, 1.62, ease(lt / D)), cx: 960, cy: 900 } : { s: push(lt, D, [1.0, 1.06]), cx: 960, cy: 520 };
  return cam(s, c) + hudAt(p.hud);
};
const MALLHUD = (lv) => ({ day: 10, time: '2:38 PM', noise: 1, place: `BROOKFIELD MALL · LEVEL ${lv}` });
CLOSE_BG.mall = () => blurred('atrium', () => S2.atrium()) + nightTint(0.55);

// ---------- the stopped escalator ----------
SH.escalator = (T, tg, lt, p, D) => {
  const mode = p.mode || 'side', fl = flash(T, tg);
  if (mode === 'pov') {
    let s = set('esc_pov', () => S2.escalatorPov());
    const clank = sfxAt(T, 'escalator_clank', tg - lt - 0.1, tg - lt + D)[0] ?? 1e9, a = tg - clank;
    const dip = a > 0 ? Math.exp(-a * 5) * Math.sin(a * 30) : 0;
    s += nightTint(0.62) + flashLayer(fl * 0.9, '#DDE6FF') + darkness(0.5, 0.4, 0.6, 0.7, 'esd');
    s = cam(s, { s: lerp(1.05, 1.3, ease(lt / D)), cy: 500, x: wob(tg * 0.7, 2) * 4, y: Math.sin(lt * 3.4) * 7 + dip * 14 });
    s += bang('CLANK', 1320, 420, a, { size: 110, life: 0.9, fill: '#E8E1D2' });
    return s + letterbox() + capsAt(T, tg);
  }
  if (mode === 'feet') {
    let s = rect(0, 0, W, H, { fill: '#3A4250' });
    const step = (y, k) => poly([[200, y], [1720, y], [1720 + 80 * k, y + 120 * k], [200 - 80 * k, y + 120 * k]], { fill: '#9AA3A8', ...ink(5) }) + rect(200 - 80 * k, y + 120 * k, 1520 + 160 * k, 130 * k, { fill: '#6E767B', ...ink(5) })
      + line(200, y, 1720, y, { stroke: '#E9B93E', strokeWidth: 14 }) + Array.from({ length: 30 }, (_, i) => line(240 + i * 50, y + 10, 230 + i * 52, y + 110 * k, { stroke: '#7E868C', strokeWidth: 4 })).join('');
    s += g(step(120, 1) + step(370, 1) + step(620, 1) + step(870, 1), { filter: 'url(#wobble)' });
    // bolts along the edge where the step is held
    for (const y of [180, 430, 680, 930]) for (const x of [260, 1660]) s += circle(x, y, 14, { fill: '#C9CDD0', ...ink(3) });
    // a sneaker on the edge, lifting to the next step
    const ph = (lt % 2.2) / 2.2, up = ease(ramp(ph, 0.1, 0.6)), yS = lerp(760, 520, up) - Math.sin(up * Math.PI) * 60;
    const shoe = (x, y) => g(path('M-130 0 Q-140 -70 -60 -80 L60 -70 Q150 -40 150 10 Q150 40 100 40 H-110 Q-140 40 -130 0 Z', { fill: '#2B2F3A', ...ink(6) }) + path('M-120 26 H140', { stroke: '#F2F0EA', strokeWidth: 16 }) + rect(-150, -260, 120, 200, { rx: 30, fill: PAL.jeans, ...ink(6) }), { transform: `translate(${x} ${y})`, filter: 'url(#wobbleSoft)' });
    s += shoe(1520, yS) + shoe(380, lerp(1010, 760, ease(ramp(ph, 0.55, 1))) - Math.sin(ease(ramp(ph, 0.55, 1)) * Math.PI) * 60);
    s += nightTint(0.55) + screenGlow(960, 300, 800, 300, '#6A7A9A', 0.25);
    return cam(s, { s: push(lt, D, [1.0, 1.05]), cy: 600 });
  }
  let s = set('esc_side', () => S2.escalatorSide());
  if (p.two) {
    // coming down: both on the steps, shoes in hand, slow
    const k = ease(lt / D), q = (t) => [lerp(1150, 420, t), lerp(334, 830, t)];
    const [nx, ny] = q(clamp(k * 0.8 + 0.05)), [hx, hy] = q(clamp(k * 0.8 - 0.07));
    s += nora({ x: nx, y: ny, s: 0.95, pose: walkPose(tg * 4), expr: 'worried', facing: -1, look: -0.2, tilt: 4 });
    s += hero({ x: hx, y: hy, s: 1.0, pose: walkPose(tg * 4 + 2), expr: 'worried', facing: -1, look: -0.2, tilt: 4 });
  } else s += hero({ x: 420, y: 960, s: 1.05, pose: 'stand', expr: 'worried', facing: 1, look: 0.6, blink: autoBlink(lt, 3), breathe: 0.01 * Math.sin(tg * 2.2) });
  s += nightTint(0.6) + screenGlow(1300, 160, 700, 200, '#6A7A9A', 0.3) + flashLayer(fl * 0.6, '#DDE6FF');
  return cam(s, { s: push(lt, D, [1.0, 1.07]), cx: 700, cy: 600 }) + hudAt(p.hud);
};

// ---------- Bright Tech ----------
const lantern = (x, y, k = 1) => g(rect(x - 30 * k, y - 80 * k, 60 * k, 80 * k, { rx: 10 * k, fill: '#2E2E2E', ...ink(4) }) + rect(x - 20 * k, y - 70 * k, 40 * k, 56 * k, { rx: 6 * k, fill: '#FFE7A8', ...ink(3) }) + path(`M${x - 22 * k} ${y - 80 * k} q${22 * k} ${-30 * k} ${44 * k} 0`, { fill: 'none', ...ink(4) }), { filter: 'url(#wobbleSoft)' });
const lampLit = '<defs><filter id="lampLit2" x="-20%" y="-20%" width="140%" height="140%"><feColorMatrix type="matrix" values="0.82 0 0 0 0.05 0 0.68 0 0 0.03 0 0 0.55 0 0.03 0 0 0 1 0"/></filter></defs>';
SH.brighttech = (T, tg, lt, p, D) => {
  const mode = p.mode || 'front', fl = flash(T, tg);
  const flick = 0.9 + 0.06 * Math.sin(tg * 7.3) + 0.04 * Math.sin(tg * 13.1);
  if (mode === 'front') {
    let s = set('bright_front', () => S2.brightFront()) + lantern(1520, 680, 1.4);
    s += nightTint(0.7) + screenGlow(1520, 610, 260, 200, '#FFD98A', 0.55 * flick) + glow(1520, 610, 60, '#FFE7A8', 0.6 * flick) + flashLayer(fl * 0.5, '#DDE6FF');
    return cam(s, { s: push(lt, D, [1.0, 1.08]), cx: 1200, cy: 520 }) + hudAt(p.hud);
  }
  if (mode === 'inside') {
    let s = set('bright_inside', () => S2.brightInside()) + lantern(960, 900, 1.3);
    s += nightTint(0.84, '#2A2238') + screenGlow(960, 830, 520, 300, '#FFB866', 0.4 * flick) + flashLayer(fl * 0.4, '#DDE6FF');
    return cam(s, { s: lerp(1.0, 1.1, ease(lt / D)), cx: 960, cy: 620, x: wob(tg * 0.4, 2) * 6 });
  }
  if (mode === 'camp') {
    let s = set('bright_camp', () => S2.brightCamp());
    s += nightTint(0.75, '#2A2238') + screenGlow(1300, 900, 600, 300, '#FFB866', 0.25 * flick) + screenGlow(560, 300, 300, 200, '#3E6E9A', 0.25);
    return cam(s, { s: push(lt, D, [1.0, 1.07]), cx: 900, cy: 560 });
  }
  // lantern: Nora (and you) on the floor around the lantern
  let s = blurred('bright_inside', () => S2.brightInside()) + nightTint(0.86, '#2A2238');
  s += rect(0, 820, W, 260, { fill: '#3A3440', opacity: 0.6 }) + lantern(960, 1010, 1.3);
  let figs = '';
  figs += nora({ x: p.two ? 620 : 700, y: 1060, s: 2.0, pose: 'sit', expr: p.two ? 'neutral' : 'serious', facing: 1, look: 0.4, blink: autoBlink(lt, 4), breathe: 0.01 * Math.sin(tg * 2.0), tilt: 2 * Math.sin(tg * 0.7) });
  if (p.two) figs += hero({ x: 1320, y: 1060, s: 2.05, pose: 'sit', expr: 'neutral', facing: -1, look: -0.4, blink: autoBlink(lt, 2), breathe: 0.01 * Math.sin(tg * 2.2) });
  if (p.day) figs += g(rect(-150, -70, 300, 130, { rx: 8, fill: '#2E4A6E', ...ink(5) }) + rect(-150, -70, 300, 40, { fill: '#3E6E9A', ...ink(4) }) + label(0, -40, 'SKYHAWK', 26, '#F7F2E6'), { transform: 'translate(1100 920) rotate(-6)', filter: 'url(#wobbleSoft)' });
  s += lampLit + g(figs, { filter: 'url(#lampLit2)' });
  s += screenGlow(960, 920, 640, 380, '#FFB866', 0.4 * flick) + glow(960, 955, 60, '#FFE7A8', 0.7 * flick);
  return cam(s, { s: push(lt, D, [1.0, 1.06]), cx: 960, cy: 720 }) + hudAt(p.hud);
};

// ---------- Nora ----------
const NORA_BG = {
  brighttech: () => blurred('bright_inside', () => S2.brightInside()) + nightTint(0.82, '#2A2238') + screenGlow(1450, 760, 520, 360, '#FFB866', 0.34),
  store: () => blurred('aisle_night', () => aisle({ night: true, seed: 5 }).s) + nightTint(0.88),
};
SH.nora = (T, tg, lt, p, D) => {
  const mode = p.mode || 'close', flick = 0.9 + 0.06 * Math.sin(tg * 7.3);
  if (mode === 'behind') {
    // over your shoulder: the back of your head, the cold nozzle against your neck
    let s = NORA_BG.brighttech();
    s += hero({ x: 820, y: 1700, s: 3.0, pose: 'stand', expr: 'neutral', facing: 1, look: 0, blink: 0, filter: true, back: true, breathe: 0.004 * Math.sin(tg * 5) });
    s += g(path('M1920 380 Q1500 420 1240 600 Q1120 690 1060 740', { fill: 'none', stroke: INK, strokeWidth: 44, strokeLinecap: 'round' }) + path('M1920 380 Q1500 420 1240 600 Q1120 690 1060 740', { fill: 'none', stroke: '#2B2B2B', strokeWidth: 30, strokeLinecap: 'round' })
      + g(rect(-70, -28, 140, 56, { rx: 10, fill: '#3A3A3A', ...ink(6) }), { transform: 'translate(1040 752) rotate(35)' }), { filter: 'url(#wobbleSoft)', transform: `translate(${f1(lerp(160, 0, easeOut(ramp(lt, 0, 0.35))))} ${f1(lerp(-60, 0, easeOut(ramp(lt, 0, 0.35))))})` });
    s += screenGlow(1000, 760, 120, 80, '#BFE3F2', 0.35 * ease(ramp(lt, 0.3, 0.6)), 'softS');
    return cam(s, { s: push(lt, D, [1.0, 1.05]), cx: 960, cy: 560, ...shake(tg, lt < 0.5 ? 0.15 : 0) });
  }
  if (mode === 'reveal') {
    let s = NORA_BG.brighttech();
    const nu = 60 * 1.9 * 0.93, ex = 1240 - 1.05 * nu, ey = 1080 - 4.05 * nu + 0.45 * nu;
    let figs = nora({ x: 1240, y: 1080, s: 1.9, pose: 'extinguisher', expr: 'serious', facing: -1, look: -0.4, blink: autoBlink(lt, 4), breathe: 0.01 * Math.sin(tg * 2.6),
      extra: g(rect(-48, -120, 96, 240, { rx: 34, fill: PAL.red, ...ink(6) }) + rect(-26, -152, 52, 40, { fill: '#2B2B2B', ...ink(4) }) + rect(-40, -50, 80, 50, { fill: '#FBF6EA', ...ink(3) })
        + path('M0 -150 Q-60 -190 -150 -170', { fill: 'none', stroke: '#2B2B2B', strokeWidth: 16, strokeLinecap: 'round' }) + rect(-190, -186, 50, 30, { rx: 8, fill: '#2B2B2B', ...ink(3) }), { transform: `translate(${f1(ex)} ${f1(ey)}) rotate(-62)` }) });
    figs += hero({ x: 520, y: 1160, s: 1.8, pose: { a: 'stand', b: 'handsup', k: ease(ramp(lt, 0.1, 0.6)) }, expr: 'scared', facing: 1, look: 0.5, blink: autoBlink(lt, 1) });
    s += lampLit + g(figs, { filter: 'url(#lampLit2)' }) + screenGlow(1500, 760, 400, 300, '#FFB866', 0.25 * flick);
    return cam(s, { s: push(lt, D, [1.0, 1.06]), cx: 960, cy: 560 });
  }
  if (mode === 'window') {
    let s = set('nora_window', () => {
      let o = S.sky('night') + rect(0, 520, W, 560, { fill: '#2C303A' }) + rect(1200, 380, 560, 220, { fill: '#5A5E68', ...ink(5) }) + rect(1200, 380, 560, 60, { fill: '#2F4A40', ...ink(5) }) + label(1480, 425, 'FRESHWAY', 34, '#3A4A44', 'middle', 6);
      o += rect(0, 0, 200, H, { fill: '#2A303A', ...ink(5) }) + rect(1880, 0, 40, H, { fill: '#2A303A' }) + rect(0, 920, W, 160, { fill: '#2A303A', ...ink(5) });
      return g(o, { filter: 'url(#wobble)' });
    });
    if (p.crowd) {
      const r = rng(44); let cr = '';
      for (let i = 0; i < 90; i++) { const x = 220 + r() * 1660, y = 640 + r() * 260, u = 60 * (0.08 + (y - 640) / 260 * 0.08); cr += rect(x - 0.6 * u, y - 4.2 * u, 1.2 * u, 2.1 * u, { rx: 0.25 * u, fill: ['#8C8C86', '#2E3D55', '#7C6A8E', '#A65F4A'][i % 4], stroke: INK, strokeWidth: 2 }) + circle(x, y - 5.15 * u, u, { fill: PAL.zSkin, stroke: INK, strokeWidth: 2 }); }
      s += g(cr, { filter: 'url(#wobbleSoft)' });
    }
    const alarmOn = (tg % 3) < 1.6;
    s += nightTint(0.5) + screenGlow(1420, 470, 70, 50, '#FFE27A', alarmOn ? 0.2 : 0.05);
    if (p.bag) s += g(rect(250, 860, 150, 70, { rx: 10, fill: '#7FD36B', ...ink(4) }) + label(325, 905, 'SOUR', 22, '#E05AA0'), { filter: 'url(#wobbleSoft)', transform: 'rotate(-4 325 895)' });
    if (!p.empty) s += nora({ x: 620, y: 1240, s: 2.2, pose: 'hug', expr: 'sad', facing: 1, look: 0.9, blink: autoBlink(lt, 3), breathe: 0.01 * Math.sin(tg * 2.0) });
    s += screenGlow(640, 500, 300, 300, '#3A4A6A', 0.3);
    return cam(s, { s: push(lt, D, [1.0, 1.06]), cx: 900, cy: 520 }) + hudAt(p.hud);
  }
  if (mode === 'radio') {
    let s = NORA_BG.brighttech();
    const talking = T.voice.lines.some((L) => L.who === 'NORA' && tg >= L.start + 0.05 && tg < L.start + L.dur - 0.05);
    const dale = T.voice.lines.some((L) => L.who === 'DALE' && tg >= L.start + 0.1 && tg < L.start + L.dur - 0.1);
    const u = 60 * 2.5 * 0.93;
    if (dale) { let wv = ''; for (let i = 0; i < 26; i++) { const a = 0.25 + 0.75 * Math.abs(Math.sin(tg * 13 + i * 0.7) * Math.sin(tg * 5.3 + i * 0.31)); wv += rect(1300 + i * 20, 420 - a * 90, 10, a * 180, { rx: 5, fill: '#F2A73B', opacity: 0.85 }); } s += wv + label(1300, 300, 'DALE · CH 4', 28, '#F2A73B', 'start', 4); }
    s += nora({ x: 960, y: 1330, s: 2.5, pose: 'talkie', expr: talking ? 'serious' : 'neutral', facing: 1, look: -0.2, blink: autoBlink(lt, 4), breathe: 0.01 * Math.sin(tg * 2.4), tilt: 1.2 * Math.sin(tg * 0.8),
      extra: radioProp(960 + 0.98 * u + 6, 1330 - 4.05 * u - 0.62 * u + 70, 0.62, { on: true, led: p.broken ? '#7FD36B' : talking ? PAL.red : '#7FD36B', rot: 8 }) });
    if (p.broken) {
      // the talk button on the side, taped over and cracked
      const bx = 960 + 0.98 * u + 6 + 0.62 * 61, by = 1330 - 4.05 * u - 0.62 * u + 70 - 0.62 * 30;
      s += g(rect(bx - 14, by - 40, 34, 60, { fill: '#D9C79A', opacity: 0.9, ...ink(3) }) + path(`M${bx - 6} ${by - 30} l14 18 l-10 10 l14 16`, { fill: 'none', stroke: PAL.red, strokeWidth: 4 }), { filter: 'url(#wobbleSoft)' });
      s += g(rect(1240, 300, 300, 80, { rx: 12, fill: '#FBF6EA', ...ink(4) }) + label(1390, 352, 'TALK: BROKEN', 30, PAL.red), { opacity: f1(clamp((lt - 0.6) * 3) * 100) / 100, transform: 'rotate(4 1390 340)', filter: 'url(#wobbleSoft)' });
    }
    return cam(s, { s: push(lt, D, [1.0, 1.05]), cx: 960, cy: 520 });
  }
  // close-up with an expression; bg brighttech (default) or store
  let s = (NORA_BG[p.bg] || NORA_BG.brighttech)();
  const talking = T.voice.lines.some((L) => L.who === 'NORA' && tg >= L.start + 0.05 && tg < L.start + L.dur - 0.05);
  const expr = p.expr || 'serious', mouth = talking && expr !== 'shock' && Math.sin(tg * 15) > 0.2 ? 'whisper' : expr;
  const nx = 960 + (p.x ?? [-230, 0, 230][Math.floor(tg - lt) % 3]);
  s += nora({ x: nx, y: 1360, s: 2.6, pose: expr === 'shock' ? 'scared' : 'stand', expr: talking ? (Math.sin(tg * 15) > 0.3 ? mouth : expr) : expr, facing: 1, look: p.look ?? -0.15 + 0.06 * Math.sin(tg * 0.6),
    blink: autoBlink(lt, 4), breathe: 0.011 * Math.sin(tg * 2.4), tilt: 1.2 * Math.sin(tg * 0.85) });
  if (p.bg !== 'store') s += screenGlow(nx + 290, 640, 420, 380, '#FFD9A0', 0.18 * flick);
  return cam(s, { s: push(lt, D, expr === 'shock' ? [1.02, 1.12] : [1.0, 1.05]), cx: nx, cy: 520 });
};

// ---------- the drone ----------
const droneProp = (x, y, k = 1, t = 0, lit = true) => {
  let s = '';
  for (const [dx, dy] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) {
    s += line(x, y, x + dx * 150 * k, y + dy * 60 * k, { stroke: INK, strokeWidth: 22 * k, strokeLinecap: 'round' }) + line(x, y, x + dx * 150 * k, y + dy * 60 * k, { stroke: '#3A3F46', strokeWidth: 12 * k, strokeLinecap: 'round' });
    s += ellipse(x + dx * 150 * k, y + dy * 60 * k - 12 * k, 90 * k, 16 * k, { fill: '#C9CDD0', opacity: 0.45, ...ink(3) }) + circle(x + dx * 150 * k, y + dy * 60 * k - 10 * k, 12 * k, { fill: '#2B2F33', ...ink(3) });
  }
  s += rect(x - 70 * k, y - 36 * k, 140 * k, 72 * k, { rx: 24 * k, fill: '#E9E5DC', ...ink(5) }) + rect(x - 40 * k, y - 20 * k, 80 * k, 22 * k, { rx: 8 * k, fill: '#3E6E9A', ...ink(3) });
  if (lit) s += circle(x - 60 * k, y + 30 * k, 7 * k, { fill: Math.sin(t * 8) > 0 ? PAL.red : '#5A2A24' }) + circle(x + 60 * k, y + 30 * k, 7 * k, { fill: Math.sin(t * 8) > 0 ? '#7FD36B' : '#2A4A24' });
  return g(s, { filter: 'url(#wobbleSoft)' });
};
const speakerProp = (x, y, k = 1) => g(rect(-60 * k, -40 * k, 120 * k, 80 * k, { rx: 30 * k, fill: '#E07A3A', ...ink(5) }) + circle(0, 0, 26 * k, { fill: '#2B2F33', ...ink(4) }) + circle(0, 0, 10 * k, { fill: '#6E767B' }) + rect(-20 * k, -62 * k, 40 * k, 24 * k, { rx: 6, fill: '#8E9499', ...ink(3) }), { transform: `translate(${f1(x)} ${f1(y)})`, filter: 'url(#wobbleSoft)' });
const notes = (x, y, tg, n = 5, col = '#FFE27A') => { let s = ''; for (let i = 0; i < n; i++) { const k = ((tg * 0.6 + i / n) % 1); s += text(x + Math.sin(k * 6 + i) * 60 + (i - n / 2) * 30, y - k * 220, i % 2 ? '♪' : '♫', { fontFamily: 'Rubik', fontSize: 60, fill: col, opacity: f1((1 - k) * 90) / 100, textAnchor: 'middle' }); } return s; };
SH.drone = (T, tg, lt, p, D) => {
  const mode = p.mode || 'box', flick = 0.9 + 0.06 * Math.sin(tg * 7.3);
  if (mode === 'box' || mode === 'clip') {
    let s = blurred('bright_inside', () => S2.brightInside()) + nightTint(0.8, '#2A2238') + rect(0, 700, W, 380, { fill: '#B3A88E' }) + line(0, 700, W, 700, ink(5));
    if (mode === 'box') {
      const open = ease(ramp(lt, 0.3, 1.4));
      s += g(rect(560, 460, 800, 420, { fill: '#2E4A6E', ...ink(7) }) + rect(560, 460, 800, 90, { fill: '#3E6E9A', ...ink(5) }) + label(960, 520, 'SKYHAWK MINI', 52, '#F7F2E6', 'middle', 6) + label(960, 610, '4K · 30 MIN FLIGHT · 2 KM RANGE', 24, '#BFD3E6', 'middle', 4)
        + droneProp(960, 760, 0.9, tg, false), { filter: 'url(#wobbleSoft)' });
      s += g(poly([[560, 460], [1360, 460], [1360 - 40, lerp(460, 140, open)], [600, lerp(460, 140, open)]], { fill: '#24405E', ...ink(6) }), { filter: 'url(#wobbleSoft)' });
      s += g(path('M300 1100 L560 820 Q620 770 680 810 L720 860 L500 1100 Z', { fill: NORA.hoodie, ...ink(7) }) + ellipse(640, 800, 64, 52, { fill: NORA.skin, ...ink(6) })
        + path('M1620 1100 L1360 820 Q1300 770 1240 810 L1200 860 L1420 1100 Z', { fill: NORA.hoodie, ...ink(7) }) + ellipse(1280, 800, 64, 52, { fill: NORA.skin, ...ink(6) }), { filter: 'url(#wobbleSoft)', transform: `translate(0 ${f1(-open * 30)})` });
    } else {
      const clip = sfxAt(T, 'tok', tg - lt, tg - lt + D)[0] ?? (tg - lt + D - 0.4), k = ease(ramp(tg, clip - 1.2, clip));
      s += droneProp(960, 620, 1.4, tg, true) + speakerProp(960, lerp(980, 720, k), 1.4);
      s += bang('CLIP', 1300, 560, tg - clip, { size: 90, life: 0.9, fill: '#F3EBDD' });
      s += g(sleeve('M1920 1100 L1300 860 L1200 960 L1560 1100 Z') + mitt(1140, lerp(1080, 820, k), -10, 1.2, NORA.skin), { filter: 'url(#wobbleSoft)' });
    }
    s += screenGlow(1300, 760, 700, 400, '#FFB866', 0.3 * flick);
    return cam(s, { s: push(lt, D, [1.0, 1.06]), cy: 620 });
  }
  // the lot at night: the drone and its song pulling the crowd away
  let s = set('lot_night', () => S.lotSet({ time: 'night' }));
  const fly = mode === 'fly' ? ease(lt / D) : 0.6 + 0.4 * ease(lt / D);
  const dx = lerp(300, 1700, fly), dy = 380 + 30 * Math.sin(tg * 1.3);
  const cols = ['#8C8C86', '#2E3D55', '#3B3F48', '#C76A83', '#7C6A8E', '#8A7A4E', '#6FA3A6', '#A65F4A', '#596471'];
  const r = rng(77);
  let cr = '';
  const follow = mode === 'fly' ? ease(ramp(lt, 1.6, D)) * 0.35 : 0.35 + ease(lt / D) * 0.5;
  for (let i = 0; i < 160; i++) {
    const x0 = 60 + r() * 1800, y0 = 520 + r() * 470, ph = r() * 6.28, c = cols[Math.floor(r() * 9)];
    const tx = lerp(x0, 1650 + (x0 % 260), follow), ty = lerp(y0, 560 + (y0 % 160), follow * 0.6);
    const sc = 0.12 + (ty - 500) / 500 * 0.16, u = 60 * sc, walk = follow > 0.02 ? Math.sin(tg * 5 + ph) * 6 : 0;
    const lean = Math.atan2(dy - ty, dx - tx) * 180 / Math.PI * 0.12 + walk;
    cr += g(rect(tx - 0.6 * u, ty - 4.2 * u, 1.2 * u, 2.1 * u, { rx: 0.25 * u, fill: c, stroke: INK, strokeWidth: 2.5 }) + line(tx - 0.25 * u, ty - 2.2 * u, tx - 0.3 * u, ty, { stroke: INK, strokeWidth: 3 }) + line(tx + 0.25 * u, ty - 2.2 * u, tx + 0.3 * u, ty, { stroke: INK, strokeWidth: 3 })
      + circle(tx, ty - 5.15 * u, u, { fill: PAL.zSkin, stroke: INK, strokeWidth: 2.5 }), { transform: `rotate(${f1(lean)} ${f1(tx)} ${f1(ty)})` });
  }
  s += cr + nightTint(0.6);
  for (const lx of [300, 980, 1660]) s += glow(lx, 470, 70, '#FFB866', 0.6);
  const far = p.far ? 0.55 : 1, ddx = p.far ? 1780 : dx, ddy = p.far ? 300 + 20 * Math.sin(tg * 1.3) : dy;
  s += droneProp(ddx, ddy, 0.45 * far, tg, true) + speakerProp(ddx, ddy + 34 * far, 0.45 * far) + rings(ddx, ddy + 30 * far, tg, { color: '#FFE27A', max: 260 * far, period: 0.9, op: 0.7, width: 5 }) + notes(ddx, ddy - 30, tg, 5);
  s += screenGlow(ddx, ddy, 160 * far, 120 * far, '#FFE27A', 0.25);
  s = cam(s, { s: push(lt, D, [1.0, 1.06]), cx: lerp(900, 1100, fly), cy: 600 });
  if (p.battery) {
    // the phone's flight app: battery draining over the shot
    const pct = Math.round(lerp(p.battery[0], p.battery[1], ease(lt / D))), low = pct <= 15, blink = low && Math.sin(tg * 9) > 0;
    s += g(rect(1560, 840, 320, 170, { rx: 22, fill: '#1E1F22', ...ink(5) }) + rect(1580, 860, 280, 130, { rx: 12, fill: '#20324A' }) + label(1720, 900, 'SKYHAWK', 20, '#BFD3E6', 'middle', 4)
      + rect(1610, 920, 200, 46, { rx: 8, fill: 'none', stroke: '#F2F2EE', strokeWidth: 4 }) + rect(1810, 932, 10, 22, { fill: '#F2F2EE' })
      + rect(1616, 926, 188 * pct / 100, 34, { rx: 5, fill: low ? (blink ? PAL.red : '#7A2A22') : '#7FD36B' }) + label(1710, 954, `${pct}%`, 26, '#FFFFFF'), { filter: 'url(#wobbleSoft)' });
  }
  return s + hudAt(p.hud);
};

// ---------- staff door with Nora (episode 2) ----------
const staffdoor1 = SH.staffdoor;
SH.staffdoor = (T, tg, lt, p, D) => {
  if (!p.nora) return staffdoor1(T, tg, lt, p, D);
  if (p.mode === 'inside') {
    // inside, backs to the door, catching their breath; quiet this time
    let s = rect(0, 0, W, H, { fill: '#14161C' }) + rect(500, 80, 920, 1000, { fill: '#3A3F46', ...ink(6) }) + rect(560, 140, 800, 940, { fill: '#4A5058', ...ink(5) });
    const br = Math.sin(tg * 3.2);
    s += hero({ x: 760, y: 1240, s: 2.0, pose: 'stand', expr: 'worried', facing: 1, look: 0.4, blink: autoBlink(lt, 1), breathe: 0.02 * br });
    s += nora({ x: 1180, y: 1240, s: 2.0, pose: 'stand', expr: 'worried', facing: -1, look: -0.3, blink: autoBlink(lt, 4), breathe: 0.02 * Math.sin(tg * 3.4 + 1) });
    s += nightTint(0.6) + screenGlow(960, 200, 500, 200, '#3A4A6A', 0.4);
    return cam(s, { s: push(lt, D, [1.0, 1.05]) }) + hudAt(p.hud);
  }
  let s = set('staffwall', () => S.staffWall({}));
  // they run in and settle: the stride blends into standing / reaching for the lock instead of snapping
  const k = ease(ramp(lt, 0, 1.4)), st = ease(ramp(lt, 1.15, 1.65));
  s += nora({ x: lerp(160, 640, k), y: 990, s: 1.3, pose: { a: runPose(tg * 11), b: 'stand', k: st }, expr: 'scared', facing: 1, look: 0.4, tilt: -6 * (1 - st) });
  s += hero({ x: lerp(300, 820, k), y: 990, s: 1.35, pose: { a: runPose(tg * 11 + 1.3), b: 'reach', k: st }, expr: 'scared', facing: 1, look: 0.4, tilt: -6 * (1 - st) });
  s += nightTint(0.55);
  return cam(s, { s: push(lt, D, [1.0, 1.06]) }) + hudAt(p.hud);
};

// ---------- Dale's voice over the stockroom doors (he's right behind them) ----------
const radio1 = SH.radio;
SH.radio = (T, tg, lt, p, D) => {
  if (p.mode !== 'doors') return radio1(T, tg, lt, p, D);
  let s = blurred('stockdoors', () => S2.stockDoors()) + nightTint(p.night ? 0.86 : 0.5, p.night ? '#1F2940' : '#3A3850');
  const talking = T.voice.lines.some((L) => L.who === 'DALE' && tg >= L.start + 0.1 && tg < L.start + L.dur - 0.1);
  let wv = '';
  for (let i = 0; i < 40; i++) { const a = talking ? 0.25 + 0.75 * Math.abs(Math.sin(tg * 13 + i * 0.7) * Math.sin(tg * 5.3 + i * 0.31)) : 0.05; wv += rect(560 + i * 20, 540 - a * 110, 10, a * 220, { rx: 5, fill: '#F2A73B', opacity: 0.9 }); }
  s += wv + label(560, 380, 'DALE · CH 3 · BEHIND THESE DOORS', 28, '#F2A73B', 'start', 4);
  s += radioProp(300, 900, 1.2, { on: true, led: talking ? PAL.red : '#7FD36B', rot: -8 }) + (talking ? screenGlow(265, 735, 60, 60, PAL.red, 0.6, 'softS') : '');
  return cam(s, { s: push(lt, D, [1.0, 1.05]), cy: 540 });
};
