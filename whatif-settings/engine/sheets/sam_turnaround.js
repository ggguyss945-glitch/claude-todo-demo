// sam_turnaround — Sam in front, three-quarter, side and back views (same pose, same scale).
import { begin, doc, studio, title, caption, toon, labelBar } from './common.js';
import { rect, path } from '../style.js';

export const VIEWS = [
  { facing: 'front', label: 'FRONT' },
  { facing: 'three-quarter-right', label: 'THREE-QUARTER' },
  { facing: 'side-right', label: 'SIDE' },
  { facing: 'back', label: 'BACK' },
];
export function turnaround(id, { name, faces = 'neutral', s = 2.0, floor = 940, xs = [300, 740, 1180, 1620] } = {}) {
  let out = '';
  // construction guides: head-height bands (very light) so proportions can be checked
  VIEWS.forEach((v, i) => { out += toon(id, { x: xs[i], y: floor, s, facing: v.facing, face: faces, pose: { armL: 8, armR: 8 } }); });
  VIEWS.forEach((v, i) => { out += caption(xs[i], floor + 70, v.label, { size: 26, color: '#4A4668' }); });
  return out;
}
export default function make(q = {}) {
  begin();
  const id = q.id || 'sam';
  let s = studio({ horizon: 800 });
  const floor = 930, sc = +(q.s || 1.95);
  // proportion guides at head heights
  for (let k = 0; k <= 3; k++) s += rect(80, floor - k * 112 * sc - 1, 1760, 2, { fill: '#B9C1DE', opacity: k ? 0.55 : 0 });
  s += title(70, 92, id === 'sam' ? 'SAM — TURNAROUND' : id.toUpperCase() + ' — TURNAROUND', { size: 46 }) + caption(72, 132, '3.1 HEADS TALL  ·  HEAD ≈ TORSO WIDTH  ·  KEY LIGHT UPPER-LEFT', { anchor: 'start', size: 22, color: '#6B6890' });
  s += turnaround(id, { s: sc, floor, faces: q.face || 'neutral' });
  void path;
  return doc(s);
}
