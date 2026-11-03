// cast_expressions — every other character in four key expressions.
import { begin, doc, studio, title, caption, bust, cell, labelBar, nameTag, CAST } from './common.js';
import { ACT } from './sam_expressions.js';

export const KEYS = {
  lily: ['scream', 'laugh', 'cry', 'sly'],
  mom: ['smug', 'evil', 'angry', 'shocked'],
  dad: ['deadpan', 'panic', 'laugh', 'confused'],
  pickles: ['deadpan', 'disgusted', 'smug', 'shocked'],
  briggs: ['talk', 'skeptic', 'sleepy', 'shocked'],
  kevin: ['smug', 'sly', 'angry', 'scared'],
};
const LABEL = { talk: 'LECTURING', deadpan: 'DEADPAN' };
const CAT_ACT = { shocked: { armL: 40, armR: 40 }, disgusted: { armR: 30 } };
export default function make() {
  begin();
  let s = studio({ horizon: 1080, glow: false });
  s += title(48, 64, 'CAST — KEY EXPRESSIONS', { size: 38 }) + caption(1872, 62, 'same face kit, scaled per head', { anchor: 'end', size: 20, color: '#6B6890' });
  const ids = ['lily', 'mom', 'dad', 'pickles', 'briggs', 'kevin'];
  const x0 = 40, y0 = 96, bg = 36, gx = 12, rowH = 322, headH = 40;
  const bw = (1920 - x0 * 2 - bg) / 2, cw = (bw - gx * 3) / 4, ch = rowH - headH - 14;
  ids.forEach((id, k) => {
    const bx = x0 + (k % 2) * (bw + bg), by = y0 + Math.floor(k / 2) * rowH;
    s += nameTag(bx + 90, by + 16, CAST[id].name, CAST[id].color, { size: 24 });
    KEYS[id].forEach((e, j) => {
      const x = bx + j * (cw + gx), y = by + headH;
      const hp = id === 'pickles' ? 118 : id === 'lily' ? 126 : 124;
      const cy = id === 'pickles' ? y + 112 : id === 'kevin' ? y + 112 : y + 106;
      const pose = id === 'pickles' ? CAT_ACT[e] || {} : { ...(ACT[e] || {}), ...(id === 'dad' && !['panic'].includes(e) ? { armR: 26, foreR: 112 } : {}), ...(id === 'lily' && e === 'scream' ? { armL: 138, armR: 138, foreL: 40, foreR: 40 } : {}) };
      const inner = bust(id, x + cw / 2, cy, hp, { face: e, pose }) + labelBar(x, y + ch - 34, cw, 34, LABEL[e] || e.toUpperCase(), { size: 20 });
      s += cell(x, y, cw, ch, inner, { r: 18 });
    });
  });
  return doc(s);
}
