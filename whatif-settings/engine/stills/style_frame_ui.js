// Style frame: the sunny street with REALITY SETTINGS open on Gravity -> Moon, the "Change applied" toast, a caption,
// and the gag proven in-world: Sam and Pickles floating, loose props drifting up. Characters come from the cast agent's
// cast.js (imported read-only); if it is missing the frame still renders without them.
import * as U from '../ui.js';
import { street, wrap } from '../sets.js';
import { caption } from '../caption.js';
import { sparkles, speedLines } from '../fx.js';
import { Defs, g, f, circle, ellipse, path, st, shade, ink, contact } from '../ui_style.js';

async function cast() {
  try {
    const c = await import('../cast.js'), sty = await import('../style.js');
    return { toon: c.toon, reset: sty.resetDefs, defs: sty.defsSvg };
  } catch (e) { return null; }
}
const floatLines = (x, y, w) => [0, 1].map((i) => path(`M${f(x - w / 2 + i * 10)} ${f(y + i * 16)}q${f(w / 4)} -10 ${f(w / 2)} 0t${f(w / 2)} 0`, { fill: 'none', ...st('#FFFFFF', 5), opacity: 0.75 - i * 0.25 })).join('');

export default async () => {
  const set = street({});
  const d = new Defs();
  let s = set.svg;
  // ground ellipses under lifted things (bible: soft ground ellipses, no cast shadows)
  s += contact(540, 856, 70, 11, 0.16) + contact(880, 800, 50, 8, 0.12) + contact(330, 812, 34, 6, 0.12);
  // floating props: a ball, leaves, sprinkler droplets drifting up off Kevin's lawn
  const ball = (x, y, r, c) => circle(x, y, r, { fill: d.lin([shade(c, 0.07), shade(c, -0.07)]), stroke: ink(c), strokeWidth: 4 }) +
    path(`M${f(x - r)} ${f(y)}Q${f(x)} ${f(y + r * 0.5)} ${f(x + r)} ${f(y)}`, { fill: 'none', stroke: ink(c), strokeWidth: 3, opacity: 0.6 }) +
    path(`M${f(x - r * 0.6)} ${f(y - r * 0.35)}A${f(r * 0.7)} ${f(r * 0.7)} 0 0 1 ${f(x - r * 0.05)} ${f(y - r * 0.7)}`, { fill: 'none', ...st('#FFFFFF', r * 0.14), opacity: 0.55 });
  s += ball(330, 560, 36, '#F2443A') + floatLines(330, 612, 56);
  const leaf = (x, y, r, c, rot) => g(path('M0 -22C14 -14 16 8 0 22C-16 8 -14 -14 0 -22Z', { fill: d.lin([shade(c, 0.06), shade(c, -0.06)]), stroke: ink(c), strokeWidth: 3 }) + path('M0 -16V16', { stroke: shade(c, -0.12), strokeWidth: 2.5 }), { transform: `translate(${x} ${y}) rotate(${rot}) scale(${r})` });
  s += leaf(1030, 300, 1.2, '#7ACC2E', 30) + leaf(760, 230, 1.0, '#FFAE1F', -20) + leaf(1110, 470, 0.9, '#4BC240', 70) + leaf(190, 380, 1.1, '#FF8A3D', -40);
  for (const [x, y, r] of [[1180, 640, 9], [1225, 600, 7], [1262, 650, 8], [1300, 610, 6], [1150, 580, 6]]) s += ellipse(x, y, r * 0.8, r, { fill: d.lin(['#E8F7FF', '#7FD0FF']), stroke: '#3D8FD6', strokeWidth: 2 });
  // characters
  const C = await cast();
  if (C) {
    C.reset();
    const sam = C.toon('sam', { x: 0, y: 0, s: 1.45, face: 'starstruck', pose: { armL: 150, armR: 140, foreL: 20, foreR: 30, legL: 18, legR: -12, lean: -4 } });
    const cat = C.toon('pickles', { x: 0, y: 0, s: 1.0, face: 'deadpan', pose: { tail: 20 } });
    s += C.defs();
    s += g(sam, { transform: 'translate(540 760) rotate(-7)' }) + floatLines(540, 790, 120);
    s += g(cat, { transform: 'translate(880 560) rotate(16)' }) + floatLines(880, 584, 80);
  }
  // upward drift lines + sparkles: the world just got lighter
  s += sparkles({ x: 300, y: 180, w: 760, h: 520, count: 12, seed: 9, t: 1.1, size: 20 });
  // camera: a gentle 8% push (the shot is mid-move); the UI layer stays screen-locked above it
  s = g(s, { transform: 'translate(860 240) scale(1.08) translate(-860 -240)' });
  // the app: open on Gravity, Moon picked
  const panelRows = [
    { kind: 'chips', pick: 0 },
    { kind: 'sliderBare', v: 0.06, bubble: 'MOON · 0.16 g', stops: ['Moon', 'Earth', 'Jupiter'], iconL: 'moon', iconR: 'planet' },
    { label: 'Keep pets grounded', icon: 'cat', color: '#5C6B9E', kind: 'toggle', on: false },
  ];
  const ps = 0.86, pw = 760, px = 1920 - 36 - pw * ps;
  s += g(U.panel({ x: 0, y: 0, w: pw, rows: panelRows, subtitle: 'Settings › World › {Gravity|purple}' }), { transform: `translate(${f(px)} 36) scale(${ps})` });
  // toast, just popped (ring still fading)
  s += U.toast({ x: 400, y: 40, title: 'Change applied', sub: 'Gravity → {Moon} · 0.16 g', life: 0.85 }, 0.9);
  // caption
  s += caption('Gravity: {MOON.|orange}', {}, 1);
  return { w: 1920, h: 1080, svg: wrap(d + s) };
};
