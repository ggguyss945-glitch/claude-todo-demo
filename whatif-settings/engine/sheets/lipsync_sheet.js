// lipsync_sheet — Sam and Mom with the five visemes (closed, small, E, A, O).
import { begin, doc, studio, title, caption, bust, cell, labelBar, nameTag, CAST } from './common.js';
import { VISEMES } from '../face.js';
import { rect } from '../style.js';

const NAMES = { v_closed: ['CLOSED', 'M · B · P · rest'], v_small: ['SMALL', 'quiet · consonants'], v_E: ['E', 'EE · S · T · teeth'], v_A: ['A', 'AH · loud, low'], v_O: ['O', 'OO · W · round'] };
export default function make() {
  begin();
  let s = studio({ horizon: 1080, glow: false });
  s += title(48, 64, 'LIP-SYNC — 5 VISEMES', { size: 38 }) + caption(1872, 62, 'hold each shape 3-8 frames · fall back to the beat’s expression mouth between words', { anchor: 'end', size: 20, color: '#6B6890' });
  const ids = ['sam', 'mom'];
  const x0 = 170, y0 = 100, gx = 18, rowH = 476;
  const cw = (1920 - x0 - 40 - gx * 4) / 5, ch = rowH - 22;
  ids.forEach((id, r) => {
    const y = y0 + r * rowH;
    s += nameTag(90, y + ch / 2, CAST[id].name, CAST[id].color, { size: 24 });
    VISEMES.forEach((v, j) => {
      const x = x0 + j * (cw + gx);
      const face = { eyes: id === 'mom' ? 'bean' : 'bean', brows: 'neutral', mouth: v };
      const inner = bust(id, x + cw / 2, y + 196, 236, { face, pose: { armL: 8, armR: 8 } })
        + rect(x, y + ch - 70, cw, 70, { fill: '#FFFFFF' }) + rect(x, y + ch - 70, cw, 2.5, { fill: '#C9CFE6' })
        + title(x + cw / 2, y + ch - 34, NAMES[v][0], { size: 28, anchor: 'middle' }) + caption(x + cw / 2, y + ch - 11, NAMES[v][1], { size: 16, color: '#7A7698' });
      s += cell(x, y, cw, ch, inner, { r: 20 });
    });
  });
  return doc(s);
}
