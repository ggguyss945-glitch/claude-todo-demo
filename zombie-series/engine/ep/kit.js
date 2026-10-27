// Shared helpers for episode shots: timing curves, camera, overlays, props that recur across sets.
import { W, H, INK, PAL, glow, caption, soundCaption, hud, g, rect, circle, ellipse, line, poly, path, text, ink, layer } from '../lib.js';

export const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const lerp = (a, b, k) => a + (b - a) * k;
export const ease = (k) => { k = clamp(k); return k * k * (3 - 2 * k); };
export const easeOut = (k) => 1 - Math.pow(1 - clamp(k), 3);
export const easeIn = (k) => Math.pow(clamp(k), 3);
export const back = (k) => { k = clamp(k); const c = 1.9; return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); };
export const ramp = (t, a, b) => clamp((t - a) / (b - a));
export const wob = (t, seed = 0) => Math.sin(t * 1.7 + seed) * 0.6 + Math.sin(t * 3.1 + seed * 2.3) * 0.3 + Math.sin(t * 5.3 + seed * 0.7) * 0.1;
export const f1 = (n) => Math.round(n * 10) / 10;
export const keys = (t, ks, d = 0.1) => { let v = ks[0][1]; for (let i = 1; i < ks.length; i++) v = lerp(v, ks[i][1], ease(ramp(t, ks[i][0], ks[i][0] + d))); return v; };
export const blinkAt = (t, times, d = 0.14) => { for (const b of times) { const k = (t - b) / d; if (k > 0 && k < 1) return Math.sin(Math.PI * k); } return 0; };
// blinks every few seconds at a pseudo-random rhythm
export const autoBlink = (t, seed = 0) => { const p = 3.1 + (seed % 3) * 0.7, ph = (t + seed * 1.3) % p; return ph < 0.14 ? Math.sin(Math.PI * ph / 0.14) : 0; };

export function cam(inner, { s = 1, x = 0, y = 0, cx = W / 2, cy = H / 2, r = 0 } = {}) {
  return g(inner, { transform: `translate(${f1(cx + x)} ${f1(cy + y)}) rotate(${f1(r)}) scale(${s.toFixed(4)}) translate(${-cx} ${-cy})` });
}
// slow push over the whole shot; push = [from, to]
export const push = (lt, D, p = [1, 1.06]) => lerp(p[0], p[1], ease(lt / D));
export const shake = (t, amp, seed = 1) => ({ x: wob(t * 9, seed) * 12 * amp, y: wob(t * 9, seed + 1) * 8 * amp });

export const nightTint = (op = 0.82, fill = '#1F2940') => rect(0, 0, W, H, { fill, opacity: op, style: 'mix-blend-mode:multiply' });
export const screenGlow = (cx, cy, rx, ry, color, op, soft = 'soft') => ellipse(cx, cy, rx, ry, { fill: color, opacity: f1(op * 100) / 100, filter: `url(#${soft})`, style: 'mix-blend-mode:screen' });
export const darkness = (cx = 0.5, cy = 0.5, r = 0.62, op = 0.8, id = 'vd') =>
  `<radialGradient id="${id}" cx="${cx}" cy="${cy}" r="${r}"><stop offset="0.3" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="${op}"/></radialGradient>` + rect(0, 0, W, H, { fill: `url(#${id})` });

export function letterbox() {
  return rect(0, 0, W, 130, { fill: '#000' }) + rect(0, H - 130, W, 130, { fill: '#000' })
    + text(60, 82, 'POV', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 30, fill: '#E8E1D2', letterSpacing: 6, opacity: 0.85 }) + circle(150, 72, 10, { fill: '#D65632' });
}
export const soundCap = (s, y = H - 62) => soundCaption(s, { y });
export const quote = (s, y = H - 82) => text(W / 2, y, `“${s}”`, { fontFamily: 'Rubik', fontStyle: 'italic', fontWeight: 500, fontSize: 36, fill: '#F2A73B', textAnchor: 'middle' });

// comic onomatopoeia that punches in and shakes
export function bang(word, x, y, age, { size = 150, rot = -8, fill = '#FFE27A', life = 1.4 } = {}) {
  if (age < 0 || age > life) return '';
  const k = back(age / 0.18), fade = 1 - ramp(age, life - 0.3, life);
  return g(text(x, y, word, { fontFamily: 'Bangers, Impact', fontSize: size, fill, stroke: '#2B1D21', strokeWidth: size * 0.08, paintOrder: 'stroke', textAnchor: 'middle', letterSpacing: 3 }),
    { transform: `translate(${x} ${y}) rotate(${f1(rot + 3 * Math.sin(age * 40))}) scale(${(0.5 + 0.5 * k).toFixed(3)}) translate(${-x} ${-y})`, opacity: f1(fade * 100) / 100 });
}

// expanding sound rings (the world's main signal: sound travels, the dead follow it)
export function rings(x, y, t, { color = PAL.red, n = 3, max = 220, period = 1.2, width = 6, dash = '14 10', op = 0.85 } = {}) {
  let s = '';
  for (let i = 0; i < n; i++) {
    const k = ((t / period + i / n) % 1 + 1) % 1;
    s += circle(x, y, 20 + k * max, { fill: 'none', stroke: color, strokeWidth: width, strokeDasharray: dash, opacity: f1(op * (1 - k) * 100) / 100 });
  }
  return s;
}

export const hudAt = (p, noise) => (p && p.day !== undefined ? hud({ theme: 'price', day: p.day, time: p.time, noise: noise ?? p.noise ?? 1, place: p.place }) : '');

// ---------- props ----------
export const sleeve = (d) => path(d, { fill: PAL.jacket, ...ink(7) });
export const mitt = (cx, cy, rot, k = 1, fill = PAL.skin) => g(path(`M${-60 * k} ${-30 * k} C${-60 * k} ${-90 * k} ${50 * k} ${-95 * k} ${60 * k} ${-35 * k} L${62 * k} ${35 * k} C${50 * k} ${80 * k} ${-55 * k} ${80 * k} ${-60 * k} ${30 * k} Z`, { fill, ...ink(7) })
  + path(`M${-60 * k} ${-5 * k} C${-110 * k} ${-20 * k} ${-115 * k} ${-75 * k} ${-75 * k} ${-70 * k}`, { fill, ...ink(7) }), { transform: `translate(${f1(cx)} ${f1(cy)}) rotate(${f1(rot)})` });

export function radioProp(x, y, k = 1, { led = '#7FD36B', on = false, rot = 0 } = {}) {
  let s = line(x + 22 * k, y - 120 * k, x + 22 * k, y - 210 * k, { ...ink(14 * k) }) + circle(x + 22 * k, y - 214 * k, 9 * k, { fill: INK });
  s += rect(x - 55 * k, y - 130 * k, 110 * k, 250 * k, { rx: 18 * k, fill: '#2E2E30', ...ink(6) });
  s += rect(x - 38 * k, y - 105 * k, 76 * k, 58 * k, { rx: 6 * k, fill: on ? '#B7D99A' : '#5E6B52', ...ink(4) });
  if (on) s += text(x, y - 66 * k, 'CH 3', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 22 * k, fill: '#2B3A22', textAnchor: 'middle' });
  for (let i = 0; i < 5; i++) s += line(x - 32 * k, y - 20 * k + i * 16 * k, x + 32 * k, y - 20 * k + i * 16 * k, { stroke: '#151516', strokeWidth: 6 * k, strokeLinecap: 'round' });
  s += circle(x - 30 * k, y - 140 * k, 9 * k, { fill: led, ...ink(3) });
  if (on) s += glow(x - 30 * k, y - 140 * k, 26 * k, led, 0.8);
  s += rect(x + 55 * k, y - 60 * k, 12 * k, 60 * k, { rx: 4, fill: '#444', ...ink(3) });
  return g(s, { transform: rot ? `rotate(${rot} ${x} ${y})` : undefined, filter: 'url(#wobbleSoft)' });
}

export function keyring(x, y, k = 1, t = 0, swing = 1) {
  let s = circle(x, y, 26 * k, { fill: 'none', stroke: '#B9B4A6', strokeWidth: 7 * k });
  // 14 keys hang from the bottom of the ring, fanned a little, each swinging on its own
  for (let i = 0; i < 14; i++) {
    const spread = (i - 6.5) * 6.5, a = (90 + spread * 0.55) * Math.PI / 180, len = (78 + (i % 4) * 14) * k;
    const col = ['#C9A43A', '#B9B4A6', '#D8C27A', '#9C9890'][i % 4];
    const sw = spread + swing * 9 * Math.sin(t * 2.3 + i * 0.7);
    s += g(circle(0, 10 * k, 15 * k, { fill: col, ...ink(3) }) + circle(0, 10 * k, 5 * k, { fill: INK }) + rect(-8 * k, 20 * k, 16 * k, len, { rx: 4 * k, fill: col, ...ink(3) })
      + path(`M${8 * k} ${20 * k + len * 0.62} h${9 * k} v${8 * k} h${-9 * k} M${8 * k} ${20 * k + len * 0.82} h${6 * k}`, { fill: 'none', stroke: INK, strokeWidth: 3 }),
      { transform: `translate(${f1(x + Math.cos(a) * 24 * k)} ${f1(y + Math.sin(a) * 24 * k)}) rotate(${f1(-sw)})` });
  }
  return g(s, { filter: 'url(#wobbleSoft)' });
}

export function alarmClock(x, y, k = 1, { ring = 0, t = 0, tape = false, face = '#F2F0EA', time = null } = {}) {
  const j = ring ? 4 * Math.sin(t * 70) * ring : 0;
  let s = '';
  s += line(x - 40 * k, y + 50 * k, x - 56 * k, y + 78 * k, ink(8 * k)) + line(x + 40 * k, y + 50 * k, x + 56 * k, y + 78 * k, ink(8 * k));
  s += circle(x, y, 70 * k, { fill: PAL.red, ...ink(6) }) + circle(x, y, 56 * k, { fill: face, ...ink(4) });
  for (let i = 0; i < 12; i++) { const a = i * Math.PI / 6; s += line(x + Math.cos(a) * 46 * k, y + Math.sin(a) * 46 * k, x + Math.cos(a) * 52 * k, y + Math.sin(a) * 52 * k, { stroke: INK, strokeWidth: 3 }); }
  const [hh, mm] = time || [2, 31];
  const ma = (mm / 60) * 2 * Math.PI - Math.PI / 2, ha = ((hh % 12) / 12 + mm / 720) * 2 * Math.PI - Math.PI / 2;
  s += line(x, y, x + Math.cos(ha) * 28 * k, y + Math.sin(ha) * 28 * k, ink(6)) + line(x, y, x + Math.cos(ma) * 42 * k, y + Math.sin(ma) * 42 * k, ink(4));
  const bell = (bx, side) => g(path(`M${-28 * k} ${10 * k} Q${-28 * k} ${-26 * k} 0 ${-26 * k} Q${28 * k} ${-26 * k} ${28 * k} ${10 * k} Z`, { fill: '#C9C3B5', ...ink(5) }),
    { transform: `translate(${f1(bx)} ${f1(y - 70 * k)}) rotate(${f1(side * 25 + (ring ? side * 10 * Math.sin(t * 60) : 0))})` });
  s += bell(x - 46 * k, -1) + bell(x + 46 * k, 1) + line(x, y - 70 * k, x, y - 92 * k, ink(5)) + circle(x, y - 96 * k, 8 * k, { fill: '#C9C3B5', ...ink(4) });
  if (tape) s += g(rect(-120 * k, -22 * k, 240 * k, 44 * k, { fill: '#D9C79A', opacity: 0.85, stroke: '#8E7F5A', strokeWidth: 2 }), { transform: `translate(${x} ${y + 40 * k}) rotate(-6)` });
  if (ring) for (const side of [-1, 1]) for (let r = 0; r < 3; r++) s += path(`M${x + side * (100 + r * 26) * k} ${y - 80 * k} q${side * 18 * k} ${40 * k} 0 ${80 * k}`, { fill: 'none', stroke: '#FFE27A', strokeWidth: 6 * k, strokeLinecap: 'round', opacity: f1((0.4 + 0.6 * Math.abs(Math.sin(t * 9 + r))) * ring * 100) / 100 });
  return g(s, { transform: j ? `translate(${f1(j)} 0)` : undefined, filter: 'url(#wobbleSoft)' });
}

export const label = (x, y, s, size = 26, fill = INK, anchor = 'middle', ls = 2) => text(x, y, s, { fontFamily: 'Rubik', fontWeight: 800, fontSize: size, letterSpacing: ls, fill, textAnchor: anchor });

// lower-third name tag for introducing a character
export function nameTag(x, y, s, age) {
  const k = back(age / 0.35); if (k <= 0.01) return '';
  const w = 26 * s.length + 60;
  return g(rect(x, y, w, 64, { rx: 6, fill: '#FBF6EA', ...ink(4) }) + rect(x, y, 14, 64, { rx: 4, fill: PAL.red, ...ink(4) }) + label(x + 34, y + 43, s, 30, INK, 'start', 3),
    { transform: `translate(${f1((1 - k) * -60)} 0)`, opacity: f1(clamp(k) * 100) / 100, filter: 'url(#wobbleSoft)' });
}

// sets are static: draw them once per key as a baked layer
export const set = (key, make) => layer(key, make);
