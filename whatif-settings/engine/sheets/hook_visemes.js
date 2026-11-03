// hook_visemes — lip-sync QA: the five visemes on every human, in three facings, each row on top of a different
// expression (eyes / brows / add-ons from the expression, mouth from the viseme): face: { preset, mouth: 'v_A' }.
import { begin, doc, studio, title, caption, bust, cell, nameTag, CAST } from './common.js';
import { VISEMES } from '../face.js';
import { rect } from '../style.js';

const ROWS = [['sam', 'scared'], ['lily', 'laugh'], ['mom', 'angry'], ['dad', 'panic'], ['briggs', 'skeptic'], ['kevin', 'smug']];
const FACINGS = [['front', 'FRONT'], ['tq-right', 'THREE-QUARTER'], ['side-right', 'SIDE']];
const SHORT = { v_closed: 'CLOSED', v_small: 'SMALL', v_E: 'E', v_A: 'A', v_O: 'O' };
export default function make() {
  begin();
  let s = studio({ horizon: 1080, glow: false });
  s += title(40, 56, 'LIP-SYNC QA — 5 VISEMES × 6 HUMANS × 3 FACINGS', { size: 32 }) + caption(1880, 54, 'face: { preset: EXPRESSION, mouth: VISEME }  ·  eyes, brows and add-ons stay from the expression', { anchor: 'end', size: 17, color: '#6B6890' });
  const x0 = 150, y0 = 104, gx = 6, gg = 22, rowH = 160;
  const cw = (1920 - x0 - 24 - gx * 12 - gg * 2) / 15, ch = rowH - 10;
  FACINGS.forEach(([f, lab], fi) => {
    const gx0 = x0 + fi * (5 * cw + 4 * gx + gg);
    s += caption(gx0 + (5 * cw + 4 * gx) / 2, y0 - 12, lab, { size: 18, color: '#4A4668' });
    VISEMES.forEach((v, vi) => { s += caption(gx0 + vi * (cw + gx) + cw / 2, 1068, SHORT[v], { size: 15, color: '#7A7698' }); });
  });
  ROWS.forEach(([id, ex], r) => {
    const y = y0 + r * rowH;
    s += nameTag(74, y + ch / 2 - 10, CAST[id].name.replace('MR. ', ''), CAST[id].color, { size: 17 }) + caption(74, y + ch / 2 + 26, ex, { size: 14, color: '#7A7698' });
    FACINGS.forEach(([f], fi) => {
      const gx0 = x0 + fi * (5 * cw + 4 * gx + gg);
      VISEMES.forEach((v, vi) => {
        const x = gx0 + vi * (cw + gx);
        const inner = bust(id, x + cw / 2 - (fi === 2 ? 22 : fi === 1 ? 6 : 0), y + 74, 104, { facing: f, face: { preset: ex, mouth: v }, pose: { armL: 8, armR: 8 } });
        s += cell(x, y, cw, ch, inner, { r: 12 });
      });
    });
  });
  void rect;
  return doc(s);
}
