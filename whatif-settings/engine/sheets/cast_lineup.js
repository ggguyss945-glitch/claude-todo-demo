// cast_lineup — all seven characters side by side on a soft studio gradient, name tags, contact shadows.
import { begin, doc, studio, nameTag, title, caption, toon, CAST } from './common.js';

const LINEUP = [
  { id: 'sam', x: 185, face: 'happy', pose: { armR: 14, armL: 30, foreL: 120, handL: 'thumbs' } },
  { id: 'lily', x: 432, face: 'laugh', pose: { armL: 150, armR: 150, foreL: 20, foreR: 20, pigL: -14, pigR: 14 } },
  { id: 'mom', x: 690, face: 'smug', pose: { armL: 16, armR: 36, foreR: 118, pony: -16 }, props: { R: 'labeler' } },
  { id: 'dad', x: 962, face: 'deadpan' },
  { id: 'pickles', x: 1196, face: 'deadpan', pose: { tail: -6 } },
  { id: 'briggs', x: 1428, face: 'neutral', pose: { armL: 28, foreL: 150, handL: 'point', armR: 6 } },
  { id: 'kevin', x: 1680, face: 'smug', pose: { armL: 34, foreL: -78, handL: 'fist', armR: 10, foreR: -4 }, props: { L: null, R: 'blower' } },
];
export default function make() {
  begin();
  const floor = 905, s0 = 1.42;
  let s = studio({ horizon: 770 });
  s += title(70, 92, 'WHAT IF REAL LIFE HAD A SETTINGS MENU?', { size: 46, color: '#2A2346' }) + caption(72, 132, 'CAST LINEUP  ·  MODEL SHEET v1', { anchor: 'start', size: 22, color: '#6B6890' });
  for (const c of LINEUP) {
    const sc = c.id === 'lily' ? s0 * 0.98 : c.id === 'pickles' ? s0 * 0.9 : s0;
    s += toon(c.id, { x: c.x, y: floor, s: sc, face: c.face, pose: c.pose, props: c.props });
  }
  for (const c of LINEUP) s += nameTag(c.x, floor + 92, CAST[c.id].name, CAST[c.id].color, { size: 28 });
  return doc(s);
}
