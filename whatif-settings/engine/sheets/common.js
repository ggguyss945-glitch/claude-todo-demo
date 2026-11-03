// common.js — shared layout pieces for model sheets: studio backdrop, name tags, captions, framing.
import { W, H, g, rect, path, ellipse, text, ramp, glowPaint, grad, stroke, tone, rrect, resetDefs, defsSvg, uid, addDef, f1, FONT_DISPLAY, FONT_UI, label } from '../style.js';
import { toon, CAST, toonHeadY, toonHeight } from '../cast.js';

export { W, H };
export function begin() { resetDefs(); }
export function doc(content, { w = W, h = H } = {}) {
  return { w, h, svg: `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${defsSvg()}${content}</svg>` };
}
// soft studio gradient: cool wall, horizon line, lighter floor, a gentle key glow (no vignette: corners match)
export function studio({ horizon = 760, top = '#E9EDFA', mid = '#DCE2F4', floorTop = '#E4E8F6', floorBot = '#D2D8EC', glow = true, w = W, h = H } = {}) {
  let s = rect(0, 0, w, horizon, { fill: ramp([top, mid]) });
  s += rect(0, horizon, w, h - horizon, { fill: ramp([floorTop, floorBot]) });
  s += rect(0, horizon - 2, w, 4, { fill: tone(mid, -0.03), opacity: 0.6 });
  if (glow) s += ellipse(w / 2, horizon - 160, w * 0.42, 420, { fill: glowPaint('#FFFFFF', 0.55) });
  return s;
}
// pill name tag with a colour chip
// Lilita One advance widths (per 1000 em), measured from assets/fonts/lilita.ttf
const LILITA = { A: 655, B: 594, C: 561, D: 616, E: 493, F: 472, G: 621, H: 644, I: 429, J: 462, K: 620, L: 435, M: 907, N: 648, O: 696, P: 570, Q: 706, R: 590, S: 531, T: 502, U: 628, V: 661, W: 953, X: 683, Y: 615, Z: 563,
  0: 639, 1: 406, 2: 525, 3: 528, 4: 598, 5: 524, 6: 575, 7: 500, 8: 570, 9: 565, ' ': 188, '.': 229, '-': 525, "'": 301, '!': 287, '?': 584, '&': 667 };
export const textWidth = (str, size, ls = 0) => [...str.toUpperCase()].reduce((w, c) => w + ((LILITA[c] ?? 600) / 1000) * size + ls, 0);
export function nameTag(x, y, name, color, { size = 30 } = {}) {
  const th = size * 1.55, chip = th * 0.48, pad = th * 0.5, gap = size * 0.34;
  const tw = pad + chip + gap + textWidth(name, size, 1) + pad * 0.9;
  const x0 = x - tw / 2;
  let s = path(rrect(x0, y - th / 2, tw, th, th / 2), { fill: grad('#FFFFFF', 'v', { up: 0, down: 0.05 }), stroke: stroke(color), strokeWidth: 3, strokeLinejoin: 'round' });
  s += ellipse(x0 + pad + chip / 2 - th * 0.06, y, chip / 2, chip / 2, { fill: grad(color, 'd'), stroke: stroke(color), strokeWidth: 2 });
  s += text(x0 + pad + chip + gap - th * 0.06, y + size * 0.36, name, { fontFamily: FONT_DISPLAY, fontSize: size, fill: stroke(color), textAnchor: 'start', letterSpacing: 1 });
  return s;
}
export function title(x, y, s, { size = 54, color = '#2A2346', anchor = 'start' } = {}) {
  return text(x, y, s, { fontFamily: FONT_DISPLAY, fontSize: size, fill: color, textAnchor: anchor, letterSpacing: 1 });
}
export function caption(x, y, s, { size = 22, color = '#4A4668', anchor = 'middle', weight = 800 } = {}) {
  return text(x, y, s, { fontFamily: FONT_UI, fontWeight: weight, fontSize: size, fill: color, textAnchor: anchor, letterSpacing: 0.5 });
}
// a rounded cell that clips its content; returns markup
export function cell(x, y, w, h, inner, { r = 22, fill = '#FFFFFF', bg = null, line = '#C9CFE6' } = {}) {
  const id = uid('cell');
  addDef(id, `<clipPath id="${id}"><path d="${rrect(x, y, w, h, r)}"/></clipPath>`);
  const back = bg || path(rrect(x, y, w, h, r), { fill: ramp([tone(fill, 0.0), tone(fill, -0.035)]) });
  return g(back + inner, { clipPath: `url(#${id})` }) + path(rrect(x, y, w, h, r), { fill: 'none', stroke: line, strokeWidth: 2.5 });
}
// white label strip at the bottom of a cell
export function labelBar(x, y, w, h, s, { size = 24, color = '#2A2346' } = {}) {
  return rect(x, y, w, h, { fill: '#FFFFFF' }) + rect(x, y, w, 2.5, { fill: '#C9CFE6' }) + text(x + w / 2, y + h / 2 + size * 0.36, s, { fontFamily: FONT_DISPLAY, fontSize: size, fill: color, textAnchor: 'middle', letterSpacing: 1.5 });
}
// bust framing: place a toon so its head centre lands at (cx, cy) with head height hpx
export function bust(id, cx, cy, hpx, o = {}) {
  const spec = CAST[id];
  const hh = spec.dims.head.h;
  const s = hpx / hh;
  const hy = toonHeadY(id);
  return toon(id, { ...o, x: cx, y: cy - hy * s, s, shadow: false, props: o.props || (id === 'kevin' ? { L: null } : undefined) });
}
export { toon, CAST, toonHeadY, toonHeight, label };
