// sam_expressions — Sam's 24 expression presets in a 6x4 grid, each with a small acting pose and a label.
import { begin, doc, studio, title, caption, bust, cell, labelBar } from './common.js';
import { SHEET_ORDER } from '../face.js';

// arm acting for the bust (only shoulders / hands near the face read in a bust)
export const ACT = {
  happy: { armL: 24, armR: 24 },
  starstruck: { armL: 18, armR: 18, foreL: 196, foreR: 196, handL: 'fist', handR: 'fist' },
  shocked: { armL: 40, armR: 40, foreL: 60, foreR: 60 },
  scared: { armL: 22, armR: 22, foreL: 190, foreR: 190, handL: 'fist', handR: 'fist' },
  panic: { armL: 150, armR: 150, foreL: 25, foreR: 25 },
  angry: { armL: 14, armR: 14, handL: 'fist', handR: 'fist' },
  guilty: { armR: 140, foreR: 60, armL: 10 },
  confused: { armR: 140, foreR: 60, armL: 10 },
  scream: { armL: 165, armR: 165, foreL: 15, foreR: 15 },
  laugh: { armL: 18, armR: 18, foreL: -50, foreR: -50, handL: 'fist', handR: 'fist' },
  cry: { armL: 4, armR: 4 },
  sly: { armR: 20, foreR: 205, handR: 'fist', armL: 8 },
  determined: { armR: 40, foreR: 120, handR: 'fist', armL: 10, handL: 'fist' },
  disgusted: { armL: 35, armR: 35, foreL: 150, foreR: 150 },
  dizzy: { armL: 34, armR: 34 },
  love: { armL: 20, armR: 20, foreL: 200, foreR: 200, handL: 'fist', handR: 'fist' },
  relieved: { armR: 16, foreR: 210, armL: 8 },
  nervous: { armL: 16, armR: 16, foreL: 214, foreR: 214, handL: 'fist', handR: 'fist' },
  bored: { armL: 4, armR: 4 },
  evil: { armL: 18, armR: 18, foreL: 212, foreR: 212 },
  sleepy: { armL: 4, armR: 4 },
  smug: { armL: 8, armR: 8 },
  deadpan: { armL: 6, armR: 6 },
  neutral: { armL: 8, armR: 8 },
};
export default function make() {
  begin();
  let s = studio({ horizon: 1080, glow: false });
  s += title(48, 64, 'SAM — 24 EXPRESSION PRESETS', { size: 38 }) + caption(1872, 62, 'face.js  ·  any eyes × brows × mouth + add-ons', { anchor: 'end', size: 20, color: '#6B6890' });
  const cols = 6, rows = 4, x0 = 40, y0 = 92, gx = 16, gy = 14;
  const cw = (1920 - x0 * 2 - gx * (cols - 1)) / cols, ch = (1080 - y0 - 24 - gy * (rows - 1)) / rows;
  SHEET_ORDER.forEach((e, i) => {
    const c = i % cols, r = Math.floor(i / cols), x = x0 + c * (cw + gx), y = y0 + r * (ch + gy);
    const inner = bust('sam', x + cw / 2, y + 112, 126, { face: e, pose: ACT[e] || {} }) + labelBar(x, y + ch - 36, cw, 36, e.toUpperCase(), { size: 21 });
    s += cell(x, y, cw, ch, inner, { r: 18 });
  });
  return doc(s);
}
