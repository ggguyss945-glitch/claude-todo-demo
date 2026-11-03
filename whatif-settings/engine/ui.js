// REALITY SETTINGS: the in-world app of "What If Real Life Had a SETTINGS MENU?".
// Visual identity (ours, deliberately not iOS/Android): chunky toy-plastic glass panels in deep navy with a bevelled
// periwinkle rim, a diagonal glass sheen, an orange gear logo that matches Sam's hoodie gear, 3D "lipped" rows and
// buttons, gear-shaped toggle knobs that roll and overshoot, and orange-to-amber fills. Rounded heavy type (Nunito 900,
// Lilita One for numbers/titles). Every component is a pure function (opts, p) -> SVG string, 1920x1080 space, where
// p in 0..1 is the entry progress (pop with overshoot + flash ring over 4-10 frames); p >= 1 or undefined = settled.
import {
  W, H, FONT, Defs, f, clamp, lerp, seg, esc, ease, rng, shade, mix, ink, g, rect, circle, ellipse, line, poly, path, text,
  tr, st, rrPath, gearPath, arcPath, starPts, popIn, textW,
} from './ui_style.js';
import { glyph } from './ui_icons.js';

// ---------- theme ----------
export const UI = {
  ink: '#090D22', navy0: '#0D1330', navy1: '#141C40', navy2: '#1F2A5A', navy3: '#2B3A78', row: '#273470', rowLo: '#1D2758',
  rim: '#36488A', rimHi: '#7590E6', text: '#FFFFFF', sub: '#B3C3F0', dim: '#7A8AC2',
  orange: '#FF7A3D', orange2: '#E4572A', orangeHi: '#FFB070', amber: '#FFC23D',
  green: '#2FD27C', red: '#FF4458', cyan: '#3CCBFF', purple: '#A779FF', pink: '#FF66B0', yellow: '#FFD43B',
};
/** keyword colours for UI text on navy (slightly lighter than the caption set so they hold on dark glass) */
export const KWUI = { yellow: '#FFD84A', red: '#FF5A5F', green: '#4BE58A', pink: '#FF7CC0', orange: '#FFA24D', cyan: '#5AD6FF', purple: '#B993FF', white: '#FFFFFF', sub: UI.sub };

export const CATS = {
  brightness: { label: 'Brightness', icon: 'brightness', color: '#FFAE1F' },
  volume: { label: 'Volume', icon: 'volume', color: '#25AEF2' },
  gravity: { label: 'Gravity', icon: 'gravity', color: '#8A5CF2' },
  subtitles: { label: 'Subtitles', icon: 'subtitles', color: '#17C2A0' },
  speed: { label: 'Playback speed', icon: 'speed', color: '#FF5596' },
  language: { label: 'Language', icon: 'language', color: '#3D7FEA' },
  graphics: { label: 'Graphics', icon: 'graphics', color: '#6DC52A' },
  difficulty: { label: 'Difficulty', icon: 'difficulty', color: '#F0474E' },
  weather: { label: 'Weather', icon: 'weather', color: '#3BAEFF' },
  parental: { label: 'Parental Controls', icon: 'parental', color: '#25BE66' },
  developer: { label: 'Developer options', icon: 'developer', color: '#5C6B9E' },
  reset: { label: 'Factory reset', icon: 'reset', color: '#E5303D' },
};

const NUN = (size, weight = 900, fill = UI.text, extra = {}) => ({ fontFamily: FONT.ui, fontWeight: weight, fontSize: size, fill, ...extra });
const LIL = (size, fill = UI.text, extra = {}) => ({ fontFamily: FONT.title, fontSize: size, fill, ...extra });

/** '{GRAVITY|purple} set to {Moon}' -> tspans; plain text stays in the base fill. */
export function rich(s, pal = KWUI, def = 'orange') {
  return String(s).split(/(\{[^}]+\})/).filter((x) => x !== '').map((part) => {
    const m = part.match(/^\{([^|}]+)(?:\|([^}]+))?\}$/);
    if (!m) return esc(part);
    return `<tspan fill="${pal[m[2]] || m[2] || pal[def]}">${esc(m[1])}</tspan>`;
  }).join('');
}
export const plain = (s) => String(s).replace(/\{([^|}]+)(?:\|[^}]+)?\}/g, '$1');

// ---------- shared builders ----------
/** the glass card every panel is made of: soft UI shadow, bevelled rim, glass body, diagonal sheen, top highlight */
export function glassCard(d, x, y, w, h, r, o = {}) {
  const rim = o.rim || UI.rim, top = o.top || UI.navy2, bot = o.bot || UI.navy1, b = o.bevel ?? 7;
  let s = '';
  if (o.shadow !== false) s += path(rrPath(x, y + 6, w, h, r), { fill: UI.ink, opacity: 0.85, filter: d.shadow(14, 20, 0.55) });
  s += path(rrPath(x, y, w, h, r), { fill: d.lin([[0, o.rimHi || UI.rimHi], [0.22, rim], [1, shade(rim, -0.1)]]) });
  s += path(rrPath(x + b, y + b, w - 2 * b, h - 2 * b, Math.max(4, r - b)), { fill: d.lin([top, bot]), opacity: o.glass ?? 0.97 });
  const clip = d.clip(path(rrPath(x + b, y + b, w - 2 * b, h - 2 * b, Math.max(4, r - b))));
  s += g(poly([[x, y], [x + w * 0.55, y], [x + w * 0.22, y + h], [x, y + h]], { fill: d.lin([[0, '#FFFFFF', 0.075], [1, '#FFFFFF', 0.0]], 'h') }) +
    poly([[x + w * 0.6, y], [x + w * 0.66, y], [x + w * 0.33, y + h], [x + w * 0.27, y + h]], { fill: '#FFFFFF', opacity: 0.03 }), { clipPath: clip });
  s += path(rrPath(x + b + 2, y + b + 2, w - 2 * b - 4, h - 2 * b - 4, Math.max(3, r - b - 2)), { fill: 'none', stroke: d.lin([[0, '#FFFFFF', 0.34], [Math.min(0.5, 40 / h), '#FFFFFF', 0.05], [1, '#FFFFFF', 0]]), strokeWidth: 2.5 });
  s += path(rrPath(x, y, w, h, r), { fill: 'none', stroke: '#070A1C', strokeWidth: 3.5 });
  return s;
}

/** gear logo badge: the app icon, matching the white gear on Sam's hoodie but in orange */
export function logo(cx, cy, r = 52, o = {}) {
  const d = new Defs();
  let s = '';
  if (o.glow !== false) s += circle(cx, cy, r * 1.25, { fill: UI.orange, opacity: 0.35, filter: d.blur(r * 0.3) });
  s += circle(cx, cy + r * 0.08, r, { fill: shade(UI.orange2, -0.14) });
  s += circle(cx, cy, r, { fill: d.lin(['#FFA766', UI.orange, UI.orange2]) });
  s += path(gearPath(cx, cy, r * 0.74, r * 0.57, 9, (o.rot || 0) - 90, 0.52), { fill: shade(UI.orange2, -0.2), transform: `translate(0 ${f(r * 0.05)})`, opacity: 0.5 });
  s += path(gearPath(cx, cy, r * 0.74, r * 0.57, 9, (o.rot || 0) - 90, 0.52), { fill: '#FFFFFF' });
  s += circle(cx, cy, r * 0.24, { fill: d.lin([UI.orange, UI.orange2]) });
  s += path(`M${f(cx - r * 0.62)} ${f(cy - r * 0.38)}A${f(r * 0.78)} ${f(r * 0.78)} 0 0 1 ${f(cx + r * 0.2)} ${f(cy - r * 0.8)}`, { fill: 'none', ...st('#FFFFFF', r * 0.1), opacity: 0.45 });
  s += circle(cx, cy, r, { fill: 'none', stroke: ink(UI.orange), strokeWidth: Math.max(2.5, r * 0.07) });
  return d + s;
}

/** coloured rounded-square icon tile with lip, gloss and a white glyph */
export function iconTile(name, cx, cy, size, color, o = {}) {
  const d = new Defs(), r = size * 0.3, x = cx - size / 2, y = cy - size / 2, lip = size * 0.075;
  let s = path(rrPath(x, y + lip, size, size, r), { fill: shade(color, -0.17) });
  s += path(rrPath(x, y, size, size, r), { fill: d.lin([shade(color, 0.08), shade(color, -0.04)]) });
  s += path(rrPath(x + size * 0.14, y + size * 0.07, size * 0.72, size * 0.12, size * 0.06), { fill: '#FFFFFF', opacity: 0.38 });
  const k = (size * 0.0058) * (o.glyphScale || 1);
  s += g(glyph(name, shade(color, -0.24), shade(color, -0.24)), { transform: tr(cx, cy + size * 0.04, k), opacity: 0.5 });
  s += g(glyph(name, '#FFFFFF', shade(color, -0.1)), { transform: tr(cx, cy, k) });
  if (o.ring) s += path(rrPath(x - o.ring, y - o.ring, size + o.ring * 2, size + lip + o.ring * 2, r + o.ring), { fill: 'none', stroke: '#FFFFFF', strokeWidth: o.ring * 1.2 });
  s += path(rrPath(x, y, size, size + lip, r), { fill: 'none', stroke: ink(color), strokeWidth: Math.max(2, size * 0.04) });
  return d + s;
}

/** chunky 3D button with a bottom lip; press 0..1 pushes the face down into the lip */
export function button(x, y, w, h, label, o = {}) {
  const d = new Defs(), tone = o.tone || UI.orange, press = clamp(o.press || 0), lip = h * 0.12, r = o.r ?? h * 0.34;
  const dy = press * lip * 0.85;
  let s = path(rrPath(x, y + lip, w, h, r), { fill: shade(tone, -0.2) });
  s += path(rrPath(x, y + dy, w, h, r), { fill: d.lin([shade(tone, 0.07), shade(tone, -0.05)]) });
  s += path(rrPath(x + h * 0.25, y + dy + h * 0.1, w - h * 0.5, h * 0.14, h * 0.07), { fill: '#FFFFFF', opacity: 0.36 });
  const fs = o.size || h * 0.42;
  s += text(x + w / 2, y + dy + h / 2 + fs * 0.36 + 2, esc(label), NUN(fs, 900, shade(tone, -0.3), { textAnchor: 'middle', opacity: 0.45 }));
  s += text(x + w / 2, y + dy + h / 2 + fs * 0.36, esc(label), NUN(fs, 900, o.textColor || '#FFFFFF', { textAnchor: 'middle', letterSpacing: 1 }));
  s += path(rrPath(x, y, w, h + lip, r), { fill: 'none', stroke: ink(tone), strokeWidth: 3.5 });
  if (o.ring) s += path(rrPath(x - 8, y - 8, w + 16, h + lip + 16, r + 8), { fill: 'none', stroke: '#FFFFFF', strokeWidth: 5, opacity: o.ring });
  return d + s;
}

// ---------- toggle ----------
/** chunky toggle; on=true/false, k = knob travel 0 (off) .. 1 (on), knob overshoots with easeOutBack and squashes */
export function toggle(o = {}, p) {
  const { x = 0, y = 0, w = 128, h = 70 } = o;
  const k = clamp(o.k ?? (o.on === false ? 0 : 1));
  const d = new Defs(), r = h / 2;
  const kk = ease.outBack(k, 2.4);
  const knobR = h * 0.4, x0 = x + r, x1 = x + w - r, kx = lerp(x0, x1, kk), ky = y + h / 2;
  const onCol = UI.orange;
  let s = path(rrPath(x - 4, y - 4 + 5, w + 8, h + 8, r + 4), { fill: '#070A1C', opacity: 0.8 });
  s += path(rrPath(x - 4, y - 4, w + 8, h + 8, r + 4), { fill: d.lin([UI.rimHi, UI.rim]) });
  s += path(rrPath(x, y, w, h, r), { fill: d.lin(['#080C22', '#18214A']) });
  if (k > 0) s += path(rrPath(x, y, w, h, r), { fill: d.lin([shade(onCol, 0.06), UI.orange2]), opacity: f(k * 100) / 100 });
  s += path(rrPath(x + 4, y + 3, w - 8, h * 0.28, h * 0.14), { fill: '#000000', opacity: 0.18 });
  // labels
  if (k > 0.05) s += text(x + r * 0.95, ky + h * 0.15, 'ON', NUN(h * 0.38, 900, '#FFFFFF', { textAnchor: 'middle', opacity: f(clamp(k * 1.4 - 0.4) * 100) / 100 }));
  if (k < 0.95) s += text(x + w - r * 0.95, ky + h * 0.15, 'OFF', NUN(h * 0.33, 900, UI.dim, { textAnchor: 'middle', opacity: f(clamp(1 - k * 1.4) * 100) / 100 }));
  // gear knob: rolls (rotates) as it travels, stretches mid-travel
  const stretch = 1 + 0.22 * Math.sin(Math.PI * clamp(kk));
  const rot = kk * 160;
  let kn = path(gearPath(0, knobR * 0.12, knobR * 1.08, knobR * 0.9, 10, rot, 0.5), { fill: '#0A0F2A', opacity: 0.35 });
  kn += path(gearPath(0, 0, knobR * 1.08, knobR * 0.9, 10, rot, 0.5), { fill: d.lin(['#FFFFFF', '#D7DFF5']), stroke: '#3C4370', strokeWidth: 2.5 });
  kn += circle(0, 0, knobR * 0.42, { fill: k > 0.5 ? d.lin([UI.orangeHi, UI.orange2]) : d.lin(['#8D9AC8', '#5E6C9F']) });
  kn += ellipse(-knobR * 0.35, -knobR * 0.45, knobR * 0.32, knobR * 0.16, { fill: '#FFFFFF', opacity: 0.9, transform: `rotate(-25 ${f(-knobR * 0.35)} ${f(-knobR * 0.45)})` });
  s += g(kn, { transform: `translate(${f(kx)} ${f(ky)}) scale(${f(stretch * 1000) / 1000} ${f((2 - stretch) * 1000) / 1000})` });
  s += path(rrPath(x - 4, y - 4, w + 8, h + 8, r + 4), { fill: 'none', stroke: '#070A1C', strokeWidth: 3 });
  return popIn(d + s, x + w / 2, y + h / 2, p, { bbox: { x: x - 4, y: y - 4, w: w + 8, h: h + 8, r: r + 4 }, ringGrow: 40 });
}

// ---------- slider ----------
/** slider with end icons, a gear knob and a value bubble. v 0..1; stops = labels under the rail; bubbleK pops the bubble */
export function slider(o = {}, p) {
  const { x = 0, y = 0, w = 600, iconL = 'feather', iconR = 'weight', bubble, stops, color = UI.orange, color2 = UI.amber } = o;
  const v = clamp(o.v ?? 0.5), d = new Defs();
  const rx0 = x + 80, rx1 = x + w - 80, rh = 28, cy = y;
  let s = '';
  // end icons in round sockets
  for (const [cx, ic] of [[x + 32, iconL], [x + w - 32, iconR]]) {
    s += circle(cx, cy + 4, 32, { fill: '#070A1C', opacity: 0.6 });
    s += circle(cx, cy, 32, { fill: d.lin([UI.navy3, UI.navy2]), stroke: '#070A1C', strokeWidth: 3 });
    s += g(glyph(ic, UI.sub, UI.navy2), { transform: tr(cx, cy, 0.4) });
  }
  s += path(rrPath(rx0 - 5, cy - rh / 2 - 5, rx1 - rx0 + 10, rh + 10, rh / 2 + 5), { fill: d.lin([UI.rim, UI.rimHi]) });
  s += path(rrPath(rx0, cy - rh / 2, rx1 - rx0, rh, rh / 2), { fill: d.lin(['#060A1E', '#141C44']) });
  const kx = lerp(rx0, rx1, v);
  if (v > 0) {
    s += path(rrPath(rx0, cy - rh / 2, Math.max(rh, kx - rx0 + rh / 2), rh, rh / 2), { fill: d.lin([color, color2], 'h') });
    s += path(rrPath(rx0 + 8, cy - rh / 2 + 5, Math.max(4, kx - rx0 - 10), 6, 3), { fill: '#FFFFFF', opacity: 0.45 });
  }
  if (stops) {
    stops.forEach((lab, i) => {
      const sx = lerp(rx0, rx1, stops.length === 1 ? 0.5 : i / (stops.length - 1));
      const near = Math.abs(sx - kx) < (rx1 - rx0) / (stops.length * 2);
      s += circle(sx, cy + rh / 2 + 22, near ? 6 : 5, { fill: near ? UI.orangeHi : UI.dim });
      if (!(near && bubble && o.bubbleBelow)) s += text(sx, cy + rh / 2 + 60, esc(lab), NUN(26, 900, near ? '#FFFFFF' : UI.dim, { textAnchor: 'middle' }));
    });
  }
  // gear knob
  const R = 36;
  s += path(gearPath(kx, cy + 5, R, R * 0.86, 12, v * 200, 0.5), { fill: '#070A1C', opacity: 0.45 });
  s += path(gearPath(kx, cy, R, R * 0.86, 12, v * 200, 0.5), { fill: d.lin(['#FFFFFF', '#D3DCF4']), stroke: '#3C4370', strokeWidth: 2.5 });
  s += circle(kx, cy, R * 0.42, { fill: d.lin([UI.orangeHi, UI.orange2]) });
  s += ellipse(kx - R * 0.3, cy - R * 0.45, R * 0.3, R * 0.14, { fill: '#FFFFFF', opacity: 0.9 });
  if (bubble) {
    const bk = clamp(o.bubbleK ?? 1);
    const below = !!o.bubbleBelow;
    const bw = textW(bubble, 34) + 52, bh = 64, by = below ? cy + R + 26 : cy - R - 30 - bh;
    const bx = clamp(kx - bw / 2, x - 10, x + w - bw + 10);
    let b = path(rrPath(bx, by + 6, bw, bh, bh / 2), { fill: shade(UI.orange2, -0.22) });
    b += below ? poly([[kx - 14, by + 2], [kx + 14, by + 2], [kx, by - 18]], { fill: UI.orangeHi, stroke: ink(UI.orange), strokeWidth: 3, strokeLinejoin: 'round' })
      : poly([[kx - 14, by + bh - 2], [kx + 14, by + bh - 2], [kx, by + bh + 18]], { fill: UI.orange2, stroke: ink(UI.orange), strokeWidth: 3, strokeLinejoin: 'round' });
    b += path(rrPath(bx, by, bw, bh, bh / 2), { fill: d.lin([UI.orangeHi, UI.orange, UI.orange2]) });
    b += path(rrPath(bx + 18, by + 7, bw - 36, 8, 4), { fill: '#FFFFFF', opacity: 0.4 });
    b += text(bx + bw / 2, by + bh / 2 + 12, esc(bubble), NUN(34, 900, '#FFFFFF', { textAnchor: 'middle', letterSpacing: 0.5 }));
    b += path(rrPath(bx, by, bw, bh, bh / 2), { fill: 'none', stroke: ink(UI.orange), strokeWidth: 3 });
    s += bk >= 1 ? b : popIn(b, kx, below ? by : by + bh, bk, { ring: false });
  }
  return popIn(d + s, x + w / 2, cy, p, { bbox: { x, y: cy - 40, w, h: 80, r: 40 }, ringGrow: 40 });
}

// ---------- rows ----------
/** default height of a row by kind */
export const rowH = (r) => r.h || ({ slider: 262, sliderBare: 196, chips: 172 }[r.kind] || 104);
/** one settings row. kind: 'value' | 'toggle' | 'slider' (label + slider, bubble below the knob) | 'sliderBare'
 *  (slider only, bubble above) | 'chips' (preset choices: options [{label, icon}], pick index) | 'locked'.
 *  cat = key of CATS (or give icon/label/color). */
export function row(o = {}, p) {
  const { x = 0, y = 0, w = 720, kind = 'value', selected = false } = o;
  const h = rowH(o);
  const c = { ...(CATS[o.cat] || { label: o.cat || 'Setting', icon: 'gear', color: UI.orange }), ...(o.label ? { label: o.label } : {}), ...(o.icon ? { icon: o.icon } : {}), ...(o.color ? { color: o.color } : {}) };
  const d = new Defs(), r = 30;
  const locked = kind === 'locked';
  let s = path(rrPath(x, y + 6, w, h, r), { fill: '#080C24', opacity: 0.9 });
  s += path(rrPath(x, y, w, h, r), { fill: selected ? d.lin(['#3C3F86', '#2B2E6C']) : d.lin([UI.row, UI.rowLo]) });
  s += path(rrPath(x + 24, y + 6, w - 48, 7, 3.5), { fill: '#FFFFFF', opacity: selected ? 0.16 : 0.1 });
  if (selected) {
    s += path(rrPath(x - 3, y - 3, w + 6, h + 6, r + 3), { fill: 'none', stroke: UI.orange, strokeWidth: 5, filter: d.glow(UI.orange, 9, 0.85) });
    s += path(rrPath(x - 3, y + 26, 10, Math.min(h - 52, 52), 5), { fill: UI.orangeHi });
  } else s += path(rrPath(x, y, w, h, r), { fill: 'none', stroke: '#0A0F2C', strokeWidth: 2.5 });
  const hasLabel = kind !== 'sliderBare' && kind !== 'chips';
  const tile = 70, ty = y + (kind === 'slider' ? 56 : h / 2);
  if (hasLabel) {
    s += g(iconTile(c.icon, x + 24 + tile / 2, ty - 3, tile, c.color), { opacity: locked ? 0.6 : 1 });
    const lx = x + 48 + tile;
    if (locked) {
      s += text(lx, ty - 2, esc(c.label), NUN(36, 900, UI.dim));
      s += g(glyph('lock', '#FFC23D', UI.navy1), { transform: tr(lx + 12, ty + 25, 0.26) });
      s += text(lx + 32, ty + 34, esc(o.lockText || 'Ask a parent'), NUN(26, 900, '#FFC23D'));
      const mx = x + w - 52;
      s += circle(mx, ty + 4, 30, { fill: '#5A3400', opacity: 0.6 });
      s += circle(mx, ty, 30, { fill: d.lin(['#FFE08A', '#FFC23D', '#E8920C']), stroke: ink('#F2A51C'), strokeWidth: 3 });
      s += g(glyph('lock', '#FFFFFF', '#B06A00'), { transform: tr(mx, ty + 1, 0.38) });
    } else s += text(lx, ty + 13, esc(c.label), NUN(38, 900, '#FFFFFF'));
  }
  if (kind === 'value' || kind === 'slider') {
    if (o.value) s += text(x + w - (kind === 'value' ? 64 : 30), ty + 12, rich(o.value), NUN(34, 900, UI.orangeHi, { textAnchor: 'end' }));
    if (kind === 'value') s += g(glyph('chevron', UI.dim), { transform: tr(x + w - 34, ty, 0.38) });
  }
  if (kind === 'toggle') s += toggle({ x: x + w - 26 - 124, y: ty - 33, w: 124, h: 66, k: o.k ?? (o.on === false ? 0 : 1) });
  if (kind === 'slider') s += slider({ x: x + 24, y: y + 136, w: w - 48, v: o.v, iconL: o.iconL, iconR: o.iconR, bubble: o.bubble, stops: o.stops, bubbleK: o.bubbleK, bubbleBelow: true });
  if (kind === 'sliderBare') s += slider({ x: x + 24, y: y + 112, w: w - 48, v: o.v, iconL: o.iconL, iconR: o.iconR, bubble: o.bubble, stops: o.stops, bubbleK: o.bubbleK });
  if (kind === 'chips') s += chips({ x: x + 20, y: y + 20, w: w - 40, h: h - 40, options: o.options, pick: o.pick ?? 0, pickK: o.pickK });
  return popIn(d + s, x + w / 2, y + h / 2, p, { bbox: { x, y, w, h, r }, ringGrow: 34 });
}

/** preset chips: big tappable choices (Moon / Earth / Jupiter / Bouncy). pickK 0..1 pops the picked chip. */
export function chips(o = {}) {
  const { x = 0, y = 0, w = 680, h = 132, pick = 0 } = o;
  const options = o.options || [{ label: 'Moon', icon: 'moon' }, { label: 'Earth', icon: 'globe' }, { label: 'Jupiter', icon: 'planet' }, { label: 'Bouncy', icon: 'bounce' }];
  const gap = 14, cw = (w - gap * (options.length - 1)) / options.length, d = new Defs();
  let s = '';
  options.forEach((op, i) => {
    const cx = x + i * (cw + gap), on = i === pick;
    let c = path(rrPath(cx, y + 6, cw, h, 24), { fill: '#070A1C', opacity: 0.7 });
    c += path(rrPath(cx, y, cw, h, 24), { fill: on ? d.lin([UI.orangeHi, UI.orange, UI.orange2]) : d.lin([UI.navy3, UI.navy2]), stroke: on ? ink(UI.orange) : '#0A0F2C', strokeWidth: 3 });
    c += path(rrPath(cx + 16, y + 6, cw - 32, 7, 3.5), { fill: '#FFFFFF', opacity: on ? 0.45 : 0.12 });
    c += g(glyph(op.icon, on ? '#FFFFFF' : UI.sub, on ? UI.orange2 : UI.navy2), { transform: tr(cx + cw / 2, y + h * 0.4, 0.5) });
    c += text(cx + cw / 2, y + h - 20, esc(op.label), NUN(28, 900, on ? '#FFFFFF' : UI.sub, { textAnchor: 'middle' }));
    if (on) c += circle(cx + cw - 18, y + 18, 16, { fill: UI.green, stroke: '#FFFFFF', strokeWidth: 3 }) + g(glyph('check', '#FFFFFF'), { transform: tr(cx + cw - 18, y + 18, 0.18) });
    s += on && o.pickK !== undefined ? popIn(c, cx + cw / 2, y + h / 2, o.pickK, { bbox: { x: cx, y, w: cw, h, r: 24 }, ringGrow: 30 }) : c;
  });
  return d + s;
}

// ---------- the app panel ----------
/** REALITY SETTINGS panel. rows: [{cat, kind, value, selected, on, k, v, bubble, stops, ...}]; rowP: per-row entry progress
 *  (array) for staggered reveals; tabs: ['WORLD','PEOPLE','TIME'] with active index. */
export function panel(o = {}, p) {
  const { x = 1080, y = 80, w = 760, rows = [], tabs, active = 0 } = o;
  const headH = 150, tabH = tabs ? 84 : 0, gap = 18;
  const rh = rowH;
  const rowsH = rows.reduce((a, r) => a + rh(r) + gap, 0);
  const h = o.h || headH + tabH + rowsH + 26;
  const d = new Defs();
  let s = glassCard(d, x, y, w, h, 46);
  // corner brackets: the "reality frame" accent
  for (const [cx, cy, sx, sy] of [[x + 20, y + 20, 1, 1], [x + w - 20, y + h - 20, -1, -1]]) {
    s += path(`M${f(cx)} ${f(cy + sy * 44)}V${f(cy + sy * 18)}Q${f(cx)} ${f(cy)} ${f(cx + sx * 18)} ${f(cy)}H${f(cx + sx * 44)}`, { fill: 'none', ...st(UI.orange, 6), opacity: 0.9 });
  }
  // header
  s += logo(x + 86, y + 78, 50, { rot: o.logoRot || 0 });
  s += text(x + 154, y + 84, `REALITY <tspan fill="${UI.orange}">SETTINGS</tspan>`, LIL(54, '#FFFFFF', { letterSpacing: 1 }));
  s += text(x + 156, y + 120, rich(o.subtitle || 'Signed in as {SAM|orange} · v7.0'), NUN(25, 800, UI.sub));
  const bx = x + w - 70, by = y + 78;
  s += circle(bx, by + 5, 32, { fill: '#070A1C', opacity: 0.7 });
  s += circle(bx, by, 32, { fill: d.lin([UI.navy3, UI.navy2]), stroke: '#070A1C', strokeWidth: 3 });
  s += g(glyph('close', UI.sub), { transform: tr(bx, by, 0.42) });
  s += path(rrPath(x + 34, y + headH - 6, w - 68, 4, 2), { fill: d.lin([[0, UI.orange, 0.9], [0.4, UI.rimHi, 0.5], [1, UI.rimHi, 0.0]], 'h') });
  let cy = y + headH + 14;
  if (tabs) {
    const tw = (w - 68 - (tabs.length - 1) * 12) / tabs.length;
    tabs.forEach((t, i) => {
      const tx = x + 34 + i * (tw + 12), on = i === active;
      s += path(rrPath(tx, cy + 4, tw, 56, 28), { fill: '#070A1C', opacity: 0.6 });
      s += path(rrPath(tx, cy, tw, 56, 28), { fill: on ? d.lin([UI.orangeHi, UI.orange, UI.orange2]) : d.lin([UI.navy3, UI.navy2]), stroke: on ? ink(UI.orange) : '#0A0F2C', strokeWidth: 3 });
      if (on) s += path(rrPath(tx + 18, cy + 6, tw - 36, 7, 3.5), { fill: '#FFFFFF', opacity: 0.4 });
      s += text(tx + tw / 2, cy + 38, esc(t), NUN(26, 900, on ? '#FFFFFF' : UI.sub, { textAnchor: 'middle', letterSpacing: 1.5 }));
    });
    cy += tabH;
  }
  const rowsSvg = rows.map((r, i) => {
    const rr = row({ ...r, x: x + 34, y: cy, w: w - 68 - 22 }, o.rowP ? o.rowP[i] : undefined);
    cy += rh(r) + gap;
    return rr;
  }).join('');
  s += rowsSvg;
  // scrollbar
  const sx = x + w - 30, sy0 = y + headH + tabH + 20, sy1 = y + h - 40;
  s += path(rrPath(sx - 5, sy0, 10, sy1 - sy0, 5), { fill: '#070A1C', opacity: 0.6 });
  const th = (sy1 - sy0) * (o.scrollFrac ?? 0.38), tpos = sy0 + (sy1 - sy0 - th) * (o.scroll ?? 0);
  s += path(rrPath(sx - 5, tpos, 10, th, 5), { fill: d.lin([UI.rimHi, UI.rim]) });
  return popIn(d + s, x + w / 2, y + h / 2, p, { bbox: { x, y, w, h, r: 46 } });
}
export function panelHeight(o) {
  return o.h || 150 + (o.tabs ? 84 : 0) + (o.rows || []).reduce((a, r) => a + rowH(r) + 18, 0) + 26;
}

// ---------- toast ----------
/** "Change applied" toast. tone colours the icon disc; life 0..1 draws the remaining-time bar. */
export function toast(o = {}, p) {
  const { x = 60, y = 60, title = 'Change applied', sub = 'Gravity → {Moon}', icon = 'check', tone = UI.green, check = true } = o;
  const h = 126, tw = textW(title, 42) + (check ? 58 : 0), sw = textW(plain(sub), 29, 'n800');
  const w = o.w || Math.max(tw, sw) + 128 + 54;
  const d = new Defs();
  let s = glassCard(d, x, y, w, h, h / 2);
  const ix = x + 66, iy = y + h / 2;
  s += circle(ix, iy, 52, { fill: tone, opacity: 0.35, filter: d.blur(10) });
  s += circle(ix, iy + 5, 42, { fill: shade(tone, -0.18) });
  s += circle(ix, iy, 42, { fill: d.lin([shade(tone, 0.1), shade(tone, -0.05)]) });
  s += path(`M${f(ix - 28)} ${f(iy - 14)}A32 32 0 0 1 ${f(ix + 6)} ${f(iy - 32)}`, { fill: 'none', ...st('#FFFFFF', 6), opacity: 0.4 });
  s += g(glyph(icon, '#FFFFFF', shade(tone, -0.1)), { transform: tr(ix, iy, 0.5) });
  s += circle(ix, iy, 42, { fill: 'none', stroke: ink(tone), strokeWidth: 3 });
  const tx = x + 128;
  s += text(tx, y + 60, esc(title), NUN(42, 900, '#FFFFFF'));
  if (check) {
    const cx = tx + textW(title, 42) + 30;
    s += g(glyph('check', UI.green), { transform: tr(cx, y + 46, 0.42) });
  }
  s += text(tx, y + 98, rich(sub), NUN(29, 800, UI.sub));
  if (o.life !== undefined) {
    s += path(rrPath(x + 120, y + h - 15, w - 190, 6, 3), { fill: '#070A1C', opacity: 0.6 });
    s += path(rrPath(x + 120, y + h - 15, Math.max(6, (w - 190) * clamp(o.life)), 6, 3), { fill: UI.orange });
  }
  return popIn(d + s, x + 66, y + h / 2, p, { bbox: { x, y, w, h, r: h / 2 }, ringGrow: 50 });
}
export const toastWidth = (o = {}) => o.w || Math.max(textW(o.title || 'Change applied', 42) + 58, textW(plain(o.sub || 'Gravity → Moon'), 29, 'n800')) + 182;

// ---------- confirmation pop-up ----------
/** confirm({cx, cy, title:'Set {GRAVITY|purple} to {MOON}?', body:[...], yes, no, hot:'yes', press}) */
export function confirm(o = {}, p) {
  const { cx = 960, cy = 520, w = 800, title = 'Set {GRAVITY|purple} to {MOON}?', body = ['Anything not nailed down will float.', 'Including you.'], yes = 'APPLY', no = 'CANCEL', icon = 'gravity', color = CATS.gravity.color } = o;
  const h = o.h || 350 + body.length * 46, x = cx - w / 2, y = cy - h / 2;
  const d = new Defs();
  let s = glassCard(d, x, y, w, h, 50);
  // icon medallion breaking out of the top edge
  s += circle(cx, y, 86, { fill: color, opacity: 0.35, filter: d.blur(16) });
  s += circle(cx, y + 6, 74, { fill: '#070A1C', opacity: 0.7 });
  s += circle(cx, y, 74, { fill: d.lin([UI.rimHi, UI.rim]), stroke: '#070A1C', strokeWidth: 3.5 });
  s += iconTile(icon, cx, y - 4, 104, color);
  s += text(cx, y + 136, rich(title), NUN(Math.min(52, (w - 80) / (textW(plain(title), 1) || 1)), 900, '#FFFFFF', { textAnchor: 'middle' }));
  body.forEach((b, i) => { s += text(cx, y + 196 + i * 44, rich(b), NUN(32, 800, UI.sub, { textAnchor: 'middle' })); });
  const bw = (w - 64 * 2 - 30) / 2, bh = 96, byy = y + h - bh - 54;
  s += button(x + 64, byy, bw, bh, no, { tone: '#4A5A92', press: o.hot === 'no' ? o.press : 0, textColor: '#E3E9FF' });
  s += button(x + 64 + bw + 30, byy, bw, bh, yes, { tone: UI.orange, press: o.hot !== 'no' ? o.press : 0, ring: o.hot !== 'no' && o.press ? (1 - o.press) : 0 });
  return popIn(d + s, cx, cy, p, { bbox: { x, y: y - 74, w, h: h + 74, r: 50 } });
}

// ---------- Terms & Conditions ----------
export function terms(o = {}, p) {
  const { x = 120, y = 100, w = 660, h = 820, pages = '48,213' } = o;
  const d = new Defs(), R = rng(o.seed || 5);
  let s = glassCard(d, x, y, w, h, 44);
  s += g(iconTile('subtitles', 0, 0, 70, '#5C6B9E'), { transform: tr(x + 76, y + 78) });
  s += text(x + 130, y + 76, 'Terms &amp; Conditions', NUN(Math.min(44, (w - 170) / textW('Terms & Conditions', 1)), 900, '#FFFFFF'));
  s += text(x + 132, y + 112, rich('Reality {v7.0|orange} · read every page'), NUN(Math.min(25, (w - 170) / textW('Reality v7.0 · read every page', 1, 'n800')), 800, UI.sub));
  // paper sheet with fine print (stacked pages behind)
  const px = x + 40, py = y + 150, pw = w - 100, ph = h - 340;
  for (let i = 3; i >= 1; i--) s += path(rrPath(px + i * 7, py + i * 7, pw, ph, 20), { fill: shade('#E6EBF7', -0.04 * i), stroke: '#9AA6CC', strokeWidth: 2 });
  s += path(rrPath(px, py, pw, ph, 20), { fill: d.lin(['#FFFFFF', '#E9EEF9']), stroke: '#9AA6CC', strokeWidth: 2.5 });
  s += text(px + 30, py + 50, 'SECTION 1.1.1 — DEFINITIONS', NUN(22, 900, '#3A4470'));
  let ly = py + 78;
  while (ly < py + ph - 26) {
    const para = R() < 0.16;
    if (para) { ly += 14; continue; }
    const lw = (pw - 60) * (0.55 + R() * 0.45);
    s += path(rrPath(px + 30, ly, lw, 8, 4), { fill: '#AEB7D3' });
    ly += 20;
  }
  // scrollbar with a microscopic thumb (the joke: it's that long)
  s += path(rrPath(x + w - 40, py, 12, ph, 6), { fill: '#070A1C', opacity: 0.6 });
  s += path(rrPath(x + w - 40, py + 4, 12, 3, 1.5), { fill: UI.orangeHi });
  // the page-count sticker
  const sx = x + w - 156, sy = py + ph * 0.6;
  let stk = path(rrPath(-150, -78, 300, 156, 34), { fill: shade(UI.orange2, -0.18), transform: 'translate(0 8)' });
  stk += path(rrPath(-150, -78, 300, 156, 34), { fill: d.lin(['#FFB070', UI.orange, UI.orange2]), stroke: '#FFFFFF', strokeWidth: 7 });
  stk += path(rrPath(-150, -78, 300, 156, 34), { fill: 'none', stroke: ink(UI.orange), strokeWidth: 3 });
  stk += text(0, 16, esc(pages), LIL(82, '#FFFFFF', { textAnchor: 'middle', stroke: ink(UI.orange), strokeWidth: 8, paintOrder: 'stroke', strokeLinejoin: 'round' }));
  stk += text(0, 56, 'PAGES', NUN(30, 900, '#FFF2E0', { textAnchor: 'middle', letterSpacing: 4 }));
  s += g(stk, { transform: `translate(${f(sx)} ${f(sy)}) rotate(-7)` });
  // footer: page count + checkbox + agree button
  const fy = y + h - 170;
  s += text(x + 44, fy + 30, rich(`Page {1|white} of {${pages}|orange}`), NUN(30, 900, UI.sub));
  s += path(rrPath(x + 44, fy + 58, 40, 40, 10), { fill: d.lin([UI.navy3, UI.navy2]), stroke: UI.rimHi, strokeWidth: 3 });
  if (o.checked) s += g(glyph('check', UI.green), { transform: tr(x + 64, fy + 78, 0.34) });
  s += text(x + 98, fy + 88, 'I have read all of it', NUN(28, 800, '#FFFFFF'));
  s += button(x + w - 300, fy + 40, 256, 88, 'I AGREE', { tone: UI.orange, press: o.press || 0 });
  return popIn(d + s, x + w / 2, y + h / 2, p, { bbox: { x, y, w, h, r: 44 } });
}

// ---------- Patch notes ----------
const TAGS = { NEW: UI.green, FIXED: '#2FA8F0', REMOVED: UI.red, KNOWN: '#F2A51C', NERF: UI.purple, BUFF: UI.pink };
export function patchNotes(o = {}, p) {
  const { x = 120, y = 100, w = 720, version = '7.0.2' } = o;
  const items = o.items || [
    { tag: 'NEW', text: 'Gravity slider ({Moon} → {Jupiter})' },
    { tag: 'FIXED', text: 'Mondays are now optional' },
    { tag: 'REMOVED', text: "Lily's volume" },
    { tag: 'KNOWN', text: 'The cat may start talking' },
  ];
  const h = 190 + items.length * 84;
  const d = new Defs();
  let s = glassCard(d, x, y, w, h, 44);
  // ribbon header
  s += path(rrPath(x + 30, y + 30, w - 60, 96, 30), { fill: d.lin([UI.orangeHi, UI.orange, UI.orange2]), stroke: ink(UI.orange), strokeWidth: 3.5 });
  s += path(rrPath(x + 54, y + 38, w - 108, 9, 4.5), { fill: '#FFFFFF', opacity: 0.4 });
  s += logo(x + 86, y + 78, 34, { glow: false });
  const vw = textW('v' + version, 28) + 36;
  const hfs = Math.min(52, (w - 138 - vw - 70) / (textW('PATCH NOTES', 1, 'lil') + 0.02));
  s += text(x + 138, y + 78 + hfs * 0.35, 'PATCH NOTES', LIL(hfs, '#FFFFFF', { stroke: ink(UI.orange), strokeWidth: 7, paintOrder: 'stroke', strokeLinejoin: 'round', letterSpacing: 1 }));
  s += path(rrPath(x + w - 54 - vw, y + 56, vw, 46, 23), { fill: UI.navy1, opacity: 0.85 });
  s += text(x + w - 54 - vw / 2, y + 88, esc('v' + version), NUN(28, 900, UI.orangeHi, { textAnchor: 'middle' }));
  items.forEach((it, i) => {
    const iy = y + 166 + i * 84, col = TAGS[it.tag] || UI.cyan;
    const tw = textW(it.tag, 24) + 34;
    let li = path(rrPath(x + 40, iy - 30, 150, 50, 16), { fill: d.lin([shade(col, 0.06), shade(col, -0.06)]), stroke: ink(col), strokeWidth: 3 });
    li += text(x + 115, iy + 3, esc(it.tag), NUN(24, 900, '#FFFFFF', { textAnchor: 'middle', letterSpacing: 1.5 }));
    li += text(x + 214, iy + 6 + 0, rich(it.text), NUN(Math.min(34, (w - 250) / (textW(plain(it.text), 1) || 1)), 900, '#FFFFFF'));
    if (i < items.length - 1) li += path(rrPath(x + 40, iy + 40, w - 80, 3, 1.5), { fill: UI.rimHi, opacity: 0.18 });
    s += o.itemP ? popIn(li, x + 115, iy, o.itemP[i], { ring: false }) : li;
    void tw;
  });
  return popIn(d + s, x + w / 2, y + h / 2, p, { bbox: { x, y, w, h, r: 44 } });
}

// ---------- install / progress bar ----------
/** install({x,y,w,label,v,t}) - t drives the stripe crawl (seconds) */
export function install(o = {}, p) {
  const { x = 520, y = 420, w = 880, label = 'Installing {Reality 7.0|orange}', sub = 'Downloading gravity…', eta = 'ETA 3 min' } = o;
  const v = clamp(o.v ?? 0.62), t = o.t || 0, h = 220, d = new Defs();
  let s = glassCard(d, x, y, w, h, 44);
  s += g(glyph('download', UI.orangeHi), { transform: tr(x + 66, y + 66, 0.42) });
  s += text(x + 104, y + 80, rich(label), NUN(40, 900, '#FFFFFF'));
  s += text(x + w - 46, y + 82, `${Math.round(v * 100)}%`, LIL(54, UI.orangeHi, { textAnchor: 'end' }));
  const bx = x + 44, by = y + 112, bw = w - 88, bh = 50;
  s += path(rrPath(bx - 5, by - 5, bw + 10, bh + 10, bh / 2 + 5), { fill: d.lin([UI.rim, UI.rimHi]) });
  s += path(rrPath(bx, by, bw, bh, bh / 2), { fill: d.lin(['#060A1E', '#141C44']) });
  const fw = Math.max(bh, bw * v);
  const stripes = d.pattern(56, 56, `<rect width="56" height="56" fill="none"/><path d="M-14 56L28 0H56L14 56Z" fill="#FFFFFF" opacity="0.2"/><path d="M42 56L84 0H112L70 56Z" fill="#FFFFFF" opacity="0.2"/>`, `patternTransform="translate(${f((t * 120) % 56)} 0)"`);
  s += path(rrPath(bx, by, fw, bh, bh / 2), { fill: d.lin([UI.orange2, UI.orange, UI.amber], 'h') });
  s += path(rrPath(bx, by, fw, bh, bh / 2), { fill: stripes });
  s += path(rrPath(bx + 14, by + 7, fw - 28, 9, 4.5), { fill: '#FFFFFF', opacity: 0.45 });
  s += circle(bx + fw - bh / 2, by + bh / 2, bh * 0.75, { fill: UI.amber, opacity: 0.5, filter: d.blur(10) });
  s += text(bx, y + h - 26, esc(sub), NUN(27, 800, UI.sub));
  s += text(x + w - 44, y + h - 26, esc(eta), NUN(27, 800, UI.dim, { textAnchor: 'end' }));
  return popIn(d + s, x + w / 2, y + h / 2, p, { bbox: { x, y, w, h, r: 44 } });
}

// ---------- corner countdown pill ----------
/** timerPill({x,y,text,label,red,pulse}) - red flips to alarm red; pulse 0..1 swells the glow (drive it per tick) */
export function timerPill(o = {}, p) {
  const { x = 60, y = 60, label = 'RESET IN', red = false } = o;
  const txt = o.text || '00:59', pulse = clamp(o.pulse || 0);
  const d = new Defs(), h = 104, tw = textW(txt, 62, 'lil'), w = 120 + Math.max(tw, textW(label, 20)) + 40;
  const body = red ? { top: '#FF5A5F', bot: '#C81E36', rim: '#FF8C8E', rimHi: '#FFD0D0' } : {};
  let s = '';
  if (red) s += path(rrPath(x - 10, y - 10, w + 20, h + 20, h / 2 + 10), { fill: UI.red, opacity: 0.35 + pulse * 0.45, filter: d.blur(12 + pulse * 10) });
  s += glassCard(d, x, y, w, h, h / 2, body);
  const ix = x + 54, iy = y + h / 2;
  s += circle(ix, iy, 34, { fill: red ? '#FFFFFF' : d.lin([UI.orangeHi, UI.orange2]), stroke: red ? '#8E0F22' : ink(UI.orange), strokeWidth: 3 });
  s += g(glyph('clock', red ? '#C81E36' : '#FFFFFF'), { transform: tr(ix, iy, 0.5) });
  s += text(x + 104, y + 36, esc(label), NUN(20, 900, red ? '#FFE3E3' : UI.sub, { letterSpacing: 2 }));
  s += text(x + 102, y + 88, esc(txt), LIL(62, red ? '#FFFFFF' : UI.orangeHi, red ? { stroke: '#8E0F22', strokeWidth: 6, paintOrder: 'stroke' } : {}));
  return popIn(d + s, x + w / 2, y + h / 2, p, { bbox: { x, y, w, h, r: h / 2 }, ringColor: red ? '#FFD0D0' : '#FFFFFF' });
}

// ---------- world-space countdown dial ----------
/** dial({cx,cy,r,n,frac,red,label,rot}) - a gear-rimmed countdown clock; frac 0..1 = arc left */
export function dial(o = {}, p) {
  const { cx = 960, cy = 420, r = 250, label = 'SECONDS', red = true } = o;
  const n = String(o.n ?? 60), frac = clamp(o.frac ?? 1), d = new Defs();
  const hot = red ? '#FF3B3B' : UI.orange, hot2 = red ? '#FF8A4A' : UI.amber;
  let s = circle(cx, cy, r * 1.08, { fill: hot, opacity: 0.45, filter: d.blur(r * 0.12) });
  s += path(gearPath(cx, cy + r * 0.04, r, r * 0.9, 30, (o.rot || 0), 0.5), { fill: '#05081A', opacity: 0.6 });
  s += path(gearPath(cx, cy, r, r * 0.9, 30, (o.rot || 0), 0.5), { fill: d.lin(red ? ['#5B1C3A', '#2A0C22'] : [UI.navy3, UI.navy1]), stroke: red ? '#170512' : '#070A1C', strokeWidth: r * 0.016 });
  s += circle(cx, cy, r * 0.86, { fill: d.rad(red ? [[0, '#3A0C1E'], [1, '#1A0614']] : [[0, UI.navy2], [1, UI.navy0]]), stroke: red ? '#FF6B6B' : UI.rimHi, strokeWidth: r * 0.02, strokeOpacity: 0.6 });
  // 60 ticks, lit up to frac
  for (let i = 0; i < 60; i++) {
    const a = (i / 60) * Math.PI * 2, big = i % 5 === 0;
    const r0 = r * (big ? 0.72 : 0.76), r1 = r * 0.82, lit = i / 60 < frac;
    s += line(cx + Math.sin(a) * r0, cy - Math.cos(a) * r0, cx + Math.sin(a) * r1, cy - Math.cos(a) * r1, { ...st(lit ? (red ? '#FF8A8A' : UI.orangeHi) : (red ? '#5A2A40' : UI.dim), big ? r * 0.024 : r * 0.012), opacity: lit ? 1 : 0.6 });
  }
  // progress arc
  s += circle(cx, cy, r * 0.64, { fill: 'none', stroke: red ? '#3A1028' : '#0A1030', strokeWidth: r * 0.075 });
  if (frac > 0.002) s += path(arcPath(cx, cy, r * 0.64, 0, Math.min(359.9, frac * 360)), { fill: 'none', stroke: d.lin([hot2, hot], 'v'), strokeWidth: r * 0.075, strokeLinecap: 'round', filter: d.glow(hot, r * 0.03, 0.8) });
  // numerals with gradient fill and dark stroke
  const fs = n.length > 2 ? r * 0.56 : r * 0.7;
  s += text(cx, cy + fs * 0.36, esc(n), LIL(fs, d.lin(red ? ['#FFD0A0', '#FF7A4A', '#E0201C'] : ['#FFF0B0', UI.amber, UI.orange]), { textAnchor: 'middle', stroke: red ? '#3A0612' : '#2A1206', strokeWidth: r * 0.035, paintOrder: 'stroke', strokeLinejoin: 'round' }));
  s += text(cx, cy + r * 0.5, esc(label), NUN(r * 0.085, 900, red ? '#FFB0B0' : UI.sub, { textAnchor: 'middle', letterSpacing: r * 0.012 }));
  s += path(`M${f(cx - r * 0.7)} ${f(cy - r * 0.35)}A${f(r * 0.8)} ${f(r * 0.8)} 0 0 1 ${f(cx - r * 0.1)} ${f(cy - r * 0.79)}`, { fill: 'none', ...st('#FFFFFF', r * 0.03), opacity: 0.22 });
  return popIn(d + s, cx, cy, p, { ring: 'circle', r: r * 0.95, ringGrow: r * 0.35, ringW: 16, ringColor: red ? '#FFB0B0' : '#FFFFFF' });
}

// ---------- user-change notification ----------
/** changeNote({x,y,user,setting,value,avatar,cat}) -> "LilyRoar changed GRAVITY → Bouncy" */
export function changeNote(o = {}, p) {
  const { x = 60, y = 60, user = 'LilyRoar', setting = 'GRAVITY', value = 'Bouncy', avatar = '#FF6FB0', cat = 'gravity' } = o;
  const c = CATS[cat] || CATS.gravity, set = shade(c.color, 0.14);
  const msg = `${user} changed ${setting} → ${value}`;
  const h = 100, w = o.w || textW(msg, 34) + 230;
  const d = new Defs();
  let s = glassCard(d, x, y, w, h, h / 2);
  const ax = x + 52, ay = y + h / 2;
  s += circle(ax, ay + 4, 34, { fill: shade(avatar, -0.2) });
  s += circle(ax, ay, 34, { fill: d.lin([shade(avatar, 0.08), shade(avatar, -0.05)]), stroke: ink(avatar), strokeWidth: 3 });
  s += text(ax, ay + 15, esc(user[0]), LIL(40, '#FFFFFF', { textAnchor: 'middle' }));
  s += circle(ax + 26, ay + 24, 10, { fill: UI.green, stroke: UI.navy1, strokeWidth: 4 });
  s += text(x + 104, ay + 12, `<tspan fill="${shade(avatar, 0.12)}">${esc(user)}</tspan><tspan fill="${UI.sub}"> changed </tspan><tspan fill="${set}">${esc(setting)}</tspan><tspan fill="${UI.sub}"> → </tspan><tspan fill="${UI.orangeHi}">${esc(value)}</tspan>`, NUN(34, 900, '#FFFFFF'));
  s += iconTile(c.icon, x + w - 54, ay - 2, 54, c.color);
  return popIn(d + s, x + 52, y + h / 2, p, { bbox: { x, y, w, h, r: h / 2 }, ringGrow: 40 });
}
export const changeNoteWidth = (o = {}) => o.w || textW(`${o.user || 'LilyRoar'} changed ${o.setting || 'GRAVITY'} → ${o.value || 'Bouncy'}`, 34) + 230;

// ---------- lock badge ----------
/** lockBadge({x,y,text,shake}) - big padlock medallion + "Ask a parent" pill (left edge at x, centred on y) */
export function lockBadge(o = {}, p) {
  const { x = 0, y = 0, label = 'Ask a parent', shake = 0 } = o;
  const d = new Defs(), tw = textW(label, 36), w = tw + 150, h = 84;
  let s = path(rrPath(x + 40, y - h / 2 + 6, w - 40, h, h / 2), { fill: '#060A1E', opacity: 0.7 });
  s += path(rrPath(x + 40, y - h / 2, w - 40, h, h / 2), { fill: d.lin([UI.navy3, UI.navy1]), stroke: '#FFC23D', strokeWidth: 4 });
  s += text(x + 118, y + 13, esc(label), NUN(36, 900, '#FFFFFF'));
  const lx = x + 50, R = 58;
  s += circle(lx, y + 6, R, { fill: '#6A3D00', opacity: 0.6 });
  s += circle(lx, y, R, { fill: d.lin(['#FFE08A', '#FFC23D', '#E8920C']), stroke: ink('#F2A51C'), strokeWidth: 4 });
  s += path(`M${f(lx - R * 0.6)} ${f(y - R * 0.4)}A${f(R * 0.7)} ${f(R * 0.7)} 0 0 1 ${f(lx + R * 0.1)} ${f(y - R * 0.72)}`, { fill: 'none', ...st('#FFFFFF', 6), opacity: 0.55 });
  s += g(glyph('lock', '#FFFFFF', '#B06A00'), { transform: tr(lx, y + 2, 0.74) });
  const rot = shake ? Math.sin(shake * Math.PI * 6) * 9 * (1 - shake) : 0;
  return popIn(d + g(s, { transform: `rotate(${f(rot)} ${f(lx)} ${f(y)})` }), lx, y, p, { ring: 'circle', r: R, ringGrow: 40, ringColor: '#FFE08A' });
}

// ---------- mute badge over a head ----------
export function muteBadge(o = {}, p) {
  const { cx = 0, cy = 0, r = 62, label = 'MUTED' } = o;
  const d = new Defs();
  let s = circle(cx, cy, r * 1.3, { fill: UI.red, opacity: 0.35, filter: d.blur(r * 0.25) });
  s += circle(cx, cy + r * 0.1, r, { fill: '#7A0A1C' });
  s += circle(cx, cy, r, { fill: d.lin(['#FF7A7E', UI.red, '#D41E3A']) });
  s += circle(cx, cy, r * 0.84, { fill: 'none', stroke: '#FFFFFF', strokeWidth: r * 0.09, opacity: 0.9 });
  s += g(glyph('mute', '#FFFFFF'), { transform: tr(cx, cy + 1, r * 0.0108) });
  s += path(`M${f(cx - r * 0.66)} ${f(cy - r * 0.36)}A${f(r * 0.75)} ${f(r * 0.75)} 0 0 1 ${f(cx - r * 0.05)} ${f(cy - r * 0.74)}`, { fill: 'none', ...st('#FFFFFF', r * 0.1), opacity: 0.45 });
  s += circle(cx, cy, r, { fill: 'none', stroke: ink(UI.red), strokeWidth: r * 0.06 });
  if (label) {
    const lw = textW(label, r * 0.36) + r * 0.6, ly = cy + r * 0.95;
    s += path(rrPath(cx - lw / 2, ly, lw, r * 0.56, r * 0.28), { fill: UI.navy1, stroke: '#FF8A8E', strokeWidth: 3 });
    s += text(cx, ly + r * 0.41, esc(label), NUN(r * 0.36, 900, '#FFFFFF', { textAnchor: 'middle', letterSpacing: 2 }));
  }
  return popIn(d + s, cx, cy, p, { ring: 'circle', r, ringGrow: r * 0.6, ringColor: '#FFC0C4' });
}

// ---------- floating real-life subtitles ----------
/** subtitle({cx,y,text,speaker,tailX}) - closed captions that float in the world next to their source */
export function subtitle(o = {}, p) {
  const { cx = 960, y = 200, speaker } = o;
  const txt = o.text || '[aggressive leaf blowing]';
  const fs = o.size || 40, spk = speaker ? speaker + ': ' : '';
  const tw = textW(spk, fs) + textW(plain(txt), fs, 'n800');
  const w = tw + 64, h = fs * 1.8, x = cx - w / 2;
  const d = new Defs();
  let s = path(rrPath(x, y, w, h, 16), { fill: '#05081A', opacity: 0.82 });
  if (o.tailX !== undefined) s += poly([[o.tailX - 16, y + h - 1], [o.tailX + 16, y + h - 1], [o.tailX + (o.tailDx || 0), y + h + 22]], { fill: '#05081A', opacity: 0.82 });
  // little CC tab: shows this is the Subtitles setting at work
  s += path(rrPath(x + 18, y - 22, 64, 34, 10), { fill: d.lin([shade(CATS.subtitles.color, 0.06), shade(CATS.subtitles.color, -0.06)]), stroke: ink(CATS.subtitles.color), strokeWidth: 2.5 });
  s += text(x + 50, y + 3, 'CC', NUN(22, 900, '#FFFFFF', { textAnchor: 'middle', letterSpacing: 1 }));
  s += text(x + 32, y + h / 2 + fs * 0.36, (spk ? `<tspan fill="${UI.orangeHi}" font-weight="900">${esc(spk)}</tspan>` : '') + rich(txt, KWUI, 'yellow'), NUN(fs, 800, '#FFFFFF'));
  return popIn(d + s, cx, y + h / 2, p, { bbox: { x, y, w, h, r: 16 }, ringGrow: 30 });
}

// ---------- emoji speech bubble ----------
const EMO = {
  face: (d, base = ['#FFE066', '#FFC21F', '#F59E0B']) => circle(0, 0, 46, { fill: d.lin(base), stroke: '#8A4A06', strokeWidth: 4 }) +
    ellipse(-18, -28, 14, 7, { fill: '#FFFFFF', opacity: 0.6, transform: 'rotate(-25 -18 -28)' }),
  angry: (d) => circle(0, 0, 46, { fill: d.lin(['#FF8A66', '#F2482F', '#C8261E']), stroke: '#6E0E0A', strokeWidth: 4 }) +
    ellipse(-18, -28, 14, 7, { fill: '#FFFFFF', opacity: 0.5, transform: 'rotate(-25 -18 -28)' }) +
    path('M-30 -16L-8 -6M30 -16L8 -6', { fill: 'none', ...st('#4A0806', 8) }) + circle(-15, 4, 6, { fill: '#4A0806' }) + circle(15, 4, 6, { fill: '#4A0806' }) +
    path('M-18 28Q0 14 18 28', { fill: 'none', ...st('#4A0806', 7) }),
  scream: (d) => EMO.face(d) + ellipse(-15, -10, 8, 11, { fill: '#FFFFFF', stroke: '#5A2A00', strokeWidth: 3 }) + circle(-15, -9, 4, { fill: '#2A1406' }) +
    ellipse(15, -10, 8, 11, { fill: '#FFFFFF', stroke: '#5A2A00', strokeWidth: 3 }) + circle(15, -9, 4, { fill: '#2A1406' }) +
    ellipse(0, 22, 12, 17, { fill: '#5A1020', stroke: '#5A2A00', strokeWidth: 3 }) + ellipse(0, 31, 7, 5, { fill: '#FF6B8A' }),
  laugh: (d) => EMO.face(d) + path('M-26 -12Q-16 -22 -6 -12M6 -12Q16 -22 26 -12', { fill: 'none', ...st('#5A2A00', 6) }) +
    path('M-28 6H28Q26 34 0 34Q-26 34 -28 6Z', { fill: '#5A1020', stroke: '#5A2A00', strokeWidth: 3.5, strokeLinejoin: 'round' }) + path('M-22 8H22V14H-22Z', { fill: '#FFFFFF' }) +
    ellipse(-36, 4, 6, 10, { fill: '#5AC8FA' }) + ellipse(36, 4, 6, 10, { fill: '#5AC8FA' }),
  cry: (d) => EMO.face(d) + path('M-24 -6Q-15 2 -6 -6M6 -6Q15 2 24 -6', { fill: 'none', ...st('#5A2A00', 5) }) +
    path('M-16 -2V40M16 -2V40', { fill: 'none', ...st('#5AC8FA', 10) }) + path('M-12 26Q0 18 12 26', { fill: 'none', ...st('#5A2A00', 6) }),
  cool: (d) => EMO.face(d) + path('M-38 -14H38L34 -2Q30 8 18 8Q8 8 4 -4H-4Q-8 8 -18 8Q-30 8 -34 -2Z', { fill: '#1E2140' }) +
    path('M-28 -10L-18 -10', { ...st('#FFFFFF', 3), opacity: 0.7 }) + path('M-16 24Q4 32 20 18', { fill: 'none', ...st('#5A2A00', 6) }),
  heart: (d) => path('M0 40C-30 18 -46 4 -46 -14C-46 -30 -34 -40 -21 -40C-10 -40 -3 -33 0 -26C3 -33 10 -40 21 -40C34 -40 46 -30 46 -14C46 4 30 18 0 40Z', { fill: d.lin(['#FF7A9A', '#F2335A', '#C81E46']), stroke: '#6E0A24', strokeWidth: 4, strokeLinejoin: 'round' }) +
    ellipse(-22, -22, 10, 6, { fill: '#FFFFFF', opacity: 0.65, transform: 'rotate(-35 -22 -22)' }),
  skull: (d) => path('M0 -42C-26 -42 -40 -24 -40 -4C-40 10 -32 18 -24 20V36Q-24 40 -20 40H20Q24 40 24 36V20C32 18 40 10 40 -4C40 -24 26 -42 0 -42Z', { fill: d.lin(['#FFFFFF', '#D9DEEC']), stroke: '#3A3F5C', strokeWidth: 4, strokeLinejoin: 'round' }) +
    ellipse(-15, -4, 10, 11, { fill: '#2A2E48' }) + ellipse(15, -4, 10, 11, { fill: '#2A2E48' }) + path('M0 10L-6 19H6Z', { fill: '#2A2E48' }) +
    path('M-10 30V40M0 30V40M10 30V40', { ...st('#3A3F5C', 3) }),
  question: () => text(0, 34, '?', LIL(104, '#FF9A1F', { textAnchor: 'middle', stroke: '#6E2A00', strokeWidth: 8, paintOrder: 'stroke', strokeLinejoin: 'round' })),
  exclaim: () => text(0, 34, '!', LIL(104, '#FF4A3D', { textAnchor: 'middle', stroke: '#5E0A06', strokeWidth: 8, paintOrder: 'stroke', strokeLinejoin: 'round' })),
  zzz: () => text(-10, 20, 'z', LIL(58, '#7FB2FF', { textAnchor: 'middle', stroke: '#1E2A60', strokeWidth: 6, paintOrder: 'stroke' })) + text(22, -8, 'z', LIL(40, '#7FB2FF', { textAnchor: 'middle', stroke: '#1E2A60', strokeWidth: 5, paintOrder: 'stroke' })),
  note: (d) => path('M-14 24V-30L26 -40V14', { fill: 'none', ...st('#3A2A80', 9) }) + ellipse(-24, 26, 14, 11, { fill: d.lin(['#A98BFF', '#6E4AE0']), stroke: '#3A2A80', strokeWidth: 4, transform: 'rotate(-20 -24 26)' }) +
    ellipse(16, 16, 14, 11, { fill: d.lin(['#A98BFF', '#6E4AE0']), stroke: '#3A2A80', strokeWidth: 4, transform: 'rotate(-20 16 16)' }),
  fire: (d) => path('M0 -44C8 -24 30 -16 30 10C30 30 16 42 0 42C-16 42 -30 30 -30 10C-30 -4 -22 -12 -16 -20C-14 -8 -8 -4 -4 -4C-6 -20 -4 -32 0 -44Z', { fill: d.lin(['#FFD23D', '#FF7A1F', '#E8381E']), stroke: '#7A1A06', strokeWidth: 4, strokeLinejoin: 'round' }) +
    path('M0 4C6 12 14 16 14 26C14 34 8 40 0 40C-8 40 -14 34 -14 26C-14 18 -6 14 0 4Z', { fill: '#FFF0A0' }),
};
export const EMOJI = Object.keys(EMO).filter((k) => k !== 'face');
/** draw one vector emoji (our own set) at cx,cy with size in px */
export function emoji(name, cx, cy, size = 80) {
  const d = new Defs();
  const fn = EMO[name] || EMO.question;
  return d + g(fn(d), { transform: tr(cx, cy, size / 100) }) + '';
}
/** emojiBubble({x,y,emojis,tail:'bl'|'br'|'b'}) - a white chat bubble that says only emoji (Lily, muted) */
export function emojiBubble(o = {}, p) {
  const { x = 0, y = 0, emojis = ['angry', 'scream', 'exclaim'], tail = 'bl', size = 82 } = o;
  const gap = size * 1.08, w = emojis.length * gap + size * 0.5, h = size * 1.5;
  const d = new Defs();
  let s = path(rrPath(x, y + 7, w, h, h * 0.42), { fill: '#1A2050', opacity: 0.35 });
  const tx = tail === 'br' ? x + w - h * 0.6 : tail === 'b' ? x + w / 2 : x + h * 0.6;
  const tdx = tail === 'br' ? 26 : tail === 'b' ? 0 : -26;
  const bub = `${rrPath(x, y, w, h, h * 0.42)}M${f(tx - 22)} ${f(y + h - 4)}L${f(tx + tdx)} ${f(y + h + 34)}L${f(tx + 22)} ${f(y + h - 4)}Z`;
  s += path(bub, { fill: d.lin(['#FFFFFF', '#E3E9F8']), stroke: '#3A4272', strokeWidth: 5, strokeLinejoin: 'round' });
  s += path(rrPath(x + h * 0.3, y + 10, w - h * 0.6, 10, 5), { fill: '#FFFFFF', opacity: 0.9 });
  s += path(rrPath(x - 2, y - 2, w + 4, h + 4, h * 0.42 + 2), { fill: 'none' });
  emojis.forEach((e, i) => { s += emoji(e, x + size * 0.25 + gap * (i + 0.5), y + h / 2, size); });
  return popIn(d + s, tx, y + h, p, { bbox: { x, y, w, h, r: h * 0.42 }, ringGrow: 34, ringColor: '#FFFFFF' });
}
export const emojiBubbleSize = (o = {}) => { const size = o.size || 82, n = (o.emojis || [1, 2, 3]).length; return { w: n * size * 1.08 + size * 0.5, h: size * 1.5 }; };

// ---------- DAY card (ours: a settings tile with a gear behind it and 7 progress pips) ----------
export const DAY_COLORS = ['#25AEF2', '#8A5CF2', '#17C2A0', '#3D7FEA', '#FF5596', '#25BE66', '#E5303D'];
export const DAY_ICONS = ['volume', 'gravity', 'subtitles', 'language', 'speed', 'parental', 'reset'];
/** dayCard({cx,cy,day,total,color,icon,gearRot,scale}) */
export function dayCard(o = {}, p) {
  const { cx = 960, cy = 520, day = 1, total = 7 } = o;
  const color = o.color || DAY_COLORS[(day - 1) % 7], icon = o.icon || DAY_ICONS[(day - 1) % 7];
  const sc = o.scale || 1, d = new Defs();
  const w = 460, h = 540, x = -w / 2, y = -h / 2, R = 48;
  let s = '';
  // gear behind (rotates), orange like the app logo; Day 7 turns it red
  const gcol = day === total ? UI.red : UI.orange;
  s += circle(0, 0, 330, { fill: gcol, opacity: 0.28, filter: d.blur(30) });
  s += path(gearPath(0, 10, 330, 286, 14, o.gearRot || 0, 0.55), { fill: shade(gcol, -0.2) });
  s += path(gearPath(0, 0, 330, 286, 14, o.gearRot || 0, 0.55), { fill: d.lin([shade(gcol, 0.08), shade(gcol, -0.06)]), stroke: ink(gcol), strokeWidth: 6 });
  s += circle(0, 0, 250, { fill: 'none', stroke: '#FFFFFF', strokeWidth: 8, opacity: 0.25 });
  // card frame (navy, the app's rim) and white face
  s += path(rrPath(x, y + 14, w, h, R), { fill: '#070A1C', opacity: 0.7 });
  s += path(rrPath(x, y, w, h, R), { fill: d.lin([UI.rimHi, UI.rim, UI.navy1]), stroke: '#070A1C', strokeWidth: 4 });
  s += path(rrPath(x + 14, y + 14, w - 28, h - 28, R - 12), { fill: d.lin(['#FFFFFF', '#E3E9F8']) });
  // header band
  const hb = 128;
  s += g(path(rrPath(x + 14, y + 14, w - 28, hb, [R - 12, R - 12, 0, 0]), { fill: d.lin([shade(color, 0.07), shade(color, -0.06)]) }) +
    path(rrPath(x + 40, y + 24, w - 80, 12, 6), { fill: '#FFFFFF', opacity: 0.38 }));
  s += line(x + 14, y + 14 + hb, x + w - 14, y + 14 + hb, { stroke: ink(color), strokeWidth: 4 });
  s += text(x + 44, y + 14 + hb / 2 + 26, 'DAY', LIL(78, '#FFFFFF', { stroke: ink(color), strokeWidth: 9, paintOrder: 'stroke', strokeLinejoin: 'round', letterSpacing: 3 }));
  s += g(toggle({ x: 0, y: 0, w: 116, h: 62, k: o.toggleK ?? 1 }), { transform: tr(x + w - 160, y + 14 + hb / 2 - 31) });
  // number with a chunky extrude
  const nfs = 300, ny = y + 14 + hb + 262;
  const num = String(day);
  for (let i = 6; i >= 1; i--) s += text(0, ny + i * 2.2, esc(num), LIL(nfs, shade(UI.navy2, -0.06), { textAnchor: 'middle' }));
  s += text(0, ny, esc(num), LIL(nfs, d.lin([UI.navy3, UI.navy1]), { textAnchor: 'middle', stroke: UI.navy0, strokeWidth: 4, paintOrder: 'stroke' }));
  s += text(-4, ny - 8, esc(num), LIL(nfs, 'none', { textAnchor: 'middle', stroke: '#FFFFFF', strokeWidth: 3, opacity: 0.18 }));
  // 7 pips
  const pw = 40, pg = 14, px0 = -((total * pw + (total - 1) * pg) / 2), py = y + h - 76;
  for (let i = 0; i < total; i++) {
    const pxx = px0 + i * (pw + pg), cur = i === day - 1, past = i < day - 1;
    if (cur) s += path(rrPath(pxx - 6, py - 6, pw + 12, pw + 12, 14), { fill: color, opacity: 0.45, filter: d.blur(6) });
    s += path(rrPath(pxx, py, pw, pw, 12), { fill: cur ? d.lin([shade(color, 0.08), shade(color, -0.06)]) : past ? shade(DAY_COLORS[i], 0.02) : '#D3DAEC', stroke: cur || past ? ink(cur ? color : DAY_COLORS[i]) : '#AAB4D2', strokeWidth: 3, opacity: past ? 0.75 : 1 });
    if (past) s += g(glyph('check', '#FFFFFF'), { transform: tr(pxx + pw / 2, py + pw / 2, 0.24) });
    if (cur) s += path(rrPath(pxx + 7, py + 5, pw - 14, 6, 3), { fill: '#FFFFFF', opacity: 0.5 });
  }
  // corner sticker: today's setting
  s += g(iconTile(icon, 0, 0, 120, color, { ring: 7 }), { transform: `translate(${f(x + w - 18)} ${f(y + 14 + hb + 30)}) rotate(12)` });
  s += path(rrPath(x, y, w, h, R), { fill: 'none', stroke: '#070A1C', strokeWidth: 4 });
  const inner = d + g(s, { transform: `translate(${f(cx)} ${f(cy)}) scale(${sc}) rotate(${f(o.tilt || 0)})` });
  return popIn(inner, cx, cy, p, { ring: 'circle', r: 300 * sc, ringGrow: 160 * sc, ringW: 18 });
}

// ---------- name tag (handy for multiplayer gags: who has the app) ----------
export function nameTag(o = {}, p) {
  const { cx = 0, y = 0, name = 'LilyRoar', color = '#FF6FB0' } = o;
  const w = textW(name, 34) + 50, h = 54, d = new Defs();
  let s = path(rrPath(cx - w / 2, y + 5, w, h, h / 2), { fill: '#060A1E', opacity: 0.5 });
  s += path(rrPath(cx - w / 2, y, w, h, h / 2), { fill: d.lin([UI.navy3, UI.navy1]), opacity: 0.92, stroke: color, strokeWidth: 3 });
  s += text(cx, y + 38, esc(name), NUN(34, 900, '#FFFFFF', { textAnchor: 'middle' }));
  return popIn(d + s, cx, y + h / 2, p, { bbox: { x: cx - w / 2, y, w, h, r: h / 2 }, ringGrow: 26 });
}

/** tap ripple: a finger/cursor press ring on a button (p 0..1) */
export function tapRing(cx, cy, p, color = '#FFFFFF') {
  if (p <= 0 || p >= 1) return '';
  const e = ease.outCubic(p);
  return circle(cx, cy, 18 + e * 70, { fill: 'none', stroke: color, strokeWidth: 10 * (1 - e) + 1, opacity: 1 - p }) +
    circle(cx, cy, 24 * (1 - e), { fill: color, opacity: 0.6 * (1 - p) });
}

export { W, H };
