// FX + caption sheet: starbursts, speed lines, sparkles, confetti, shock ring, flash, glitch, and caption modes.
import { starburst, speedLines, sparkles, confetti, shockRing, flash, glitch, godRays } from '../fx.js';
import { caption } from '../caption.js';
import { dayCard } from '../ui.js';
import { street } from '../sets.js';
import { Defs, rect, text, g, f, FONT, path, rrPath } from '../ui_style.js';

const cell = (d, x, y, w, h, inner, label, bg) => {
  const clip = d.clip(path(rrPath(x, y, w, h, 24)));
  return g(rect(x, y, w, h, { fill: bg || d.lin(['#2E86F8', '#8CCBFB']) }) + inner, { clipPath: clip }) +
    path(rrPath(x, y, w, h, 24), { fill: 'none', stroke: '#1E2347', strokeWidth: 4 }) +
    text(x + 18, y + h - 18, label, { fontFamily: FONT.ui, fontWeight: 900, fontSize: 24, fill: '#FFFFFF', stroke: '#1E2347', strokeWidth: 6, paintOrder: 'stroke' });
};
const sub = (x, y, s, inner) => `<g transform="translate(${x} ${y}) scale(${s})">${inner}</g>`;

export default () => {
  const d = new Defs();
  let s = rect(0, 0, 1920, 1080, { fill: '#DDE3F5' });
  const W3 = 616, H3 = 336, gx = 16, gy = 16;
  const X = (i) => 16 + i * (W3 + gx), Y = (j) => 16 + j * (H3 + gy);
  // 1 starburst + DAY 7 card (the act-change slam)
  s += cell(d, X(0), Y(0), W3, H3, sub(X(0), Y(0), 0.32, speedLines({ cx: 960, cy: 540, count: 46, r0: 380, r1: 1500, t: 0.2, width: 26 }) + starburst({ cx: 960, cy: 540, r: 560, points: 14, fill: '#FF5A3A', seed: 7 }) + dayCard({ cx: 960, cy: 560, day: 7, scale: 1.05 })), 'starburst + radial speed lines + DAY 7');
  // 2 confetti + god rays (success)
  s += cell(d, X(1), Y(0), W3, H3, sub(X(1), Y(0), 0.32, godRays({ cx: 960, cy: 620, rot: 8, op: 0.5 }) + confetti({ cx: 960, cy: 700, t: 0.42, count: 90, seed: 3, size: 40 }) + caption('{APPLIED!|green}', { y: 560, size: 150 })), 'god rays + confetti (gears inside)');
  // 3 sparkles + shock ring
  s += cell(d, X(2), Y(0), W3, H3, sub(X(2), Y(0), 0.32, sparkles({ x: 200, y: 120, w: 1520, h: 840, count: 30, t: 0.7, size: 40 }) + shockRing(960, 540, 520, 0.45, '#FFFFFF', 40) + shockRing(960, 540, 520, 0.25, '#FFE36A', 30)), 'sparkles + shock rings');
  // 4 directional speed lines (whip) + flash
  s += cell(d, X(0), Y(1), W3, H3, sub(X(0), Y(1), 0.32, speedLines({ mode: 'dir', angle: 0, count: 50, width: 14, t: 0.4, seed: 2 }) + flash({ color: '#FFFFFF', mode: 'screen' }, 0.5)), 'whip speed lines + flash frame (p .5)', d.lin(['#8A5CF2', '#5E3CC8']));
  // 5 glitch slices over the street
  s += cell(d, X(1), Y(1), W3, H3, sub(X(1), Y(1), 0.32, glitch(street({}).svg, { seed: 153, bands: 6, amount: 130, t: 0.2 })), 'glitch slices (any content)');
  // 6 solid red flash frame
  s += cell(d, X(2), Y(1), W3, H3, sub(X(2), Y(1), 0.32, street({}).svg + flash({ color: '#D10C25', mode: 'solid', peak: 0.85 }, 0.08)), 'solid flash frame #D10C25 (act change)');
  // captions row
  const capBg = d.lin(['#63D255', '#4CBF45']);
  s += cell(d, X(0), Y(2), W3, H3, sub(X(0), Y(2), 0.32, caption('Your {GRAVITY|cyan}', { y: 540, size: 130 }, 1)), 'caption: keyword colour', capBg);
  s += cell(d, X(1), Y(2), W3, H3, sub(X(1), Y(2), 0.32, caption('Set {REALITY|yellow} to', { y: 540, size: 120, mode: 'type', chars: 14 })), 'caption: typewriter + block cursor', d.lin(['#1F2A5A', '#141C40']));
  s += cell(d, X(2), Y(2), W3, H3, sub(X(2), Y(2), 0.32, caption('{AAAAAH!|red}', { y: 540, size: 150, mode: 'scream', t: 0.31 }, 1) + caption('pop p=.5', { y: 860, size: 70 }, 0.5)), 'caption: scream shake · pop-in', capBg);
  return { w: 1920, h: 1080, svg: `<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">${d}${s}</svg>` };
};
