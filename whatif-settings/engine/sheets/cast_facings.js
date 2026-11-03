// cast_facings — QA sheet: up to three characters in five facings (front, 3/4, side, 3/4 back, back). ?ids=lily,mom,dad
import { begin, doc, studio, toon, caption } from './common.js';
export default function make(q = {}) {
  begin();
  const ids = (q.ids || 'lily,mom,dad').split(',');
  const F = ['front', 'three-quarter-right', 'side-right', 'tq-back-left', 'back'];
  let s = studio({ horizon: 800 });
  ids.forEach((id, r) => {
    const fl = 330 + r * 350;
    F.forEach((f, i) => { s += toon(id, { x: 200 + i * 380, y: fl, s: 0.88, facing: f, face: q.face || 'neutral' }); });
  });
  s += caption(960, 1060, F.join('   ·   '), { size: 18 });
  return doc(s);
}
