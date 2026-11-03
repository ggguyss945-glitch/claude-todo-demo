import { begin, doc, studio, toon, caption, bust } from './common.js';
import { posePreset } from '../cast.js';
import { rect, path } from '../style.js';
export default function make(q = {}) {
  begin();
  let s = studio({ horizon: 700 });
  // mannequins
  [0, 0.5, 1].forEach((k, i) => { s += toon('mom', { x: 120 + i * 190, y: 470, s: 0.95, mannequin: k, face: 'scared' }); s += toon('dad', { x: 700 + i * 200, y: 470, s: 0.95, mannequin: k, face: 'scared' }); });
  // dad pyjamas
  s += toon('dad', { x: 1380, y: 470, s: 0.95, outfit: 'pyjamas', face: 'deadpan' });
  s += toon('dad', { x: 1620, y: 470, s: 0.95, outfit: 'pyjamas', face: 'shout', pose: posePreset('shieldEyes', 'dad'), tint: { color: '#FFF3DC', k: 0.18 }, light: { color: '#FFF8E0', k: 0.55, from: 'left' } });
  s += toon('dad', { x: 1820, y: 470, s: 0.95, outfit: 'pyjamas', facing: 'tq-left', face: 'shout', pose: posePreset('shieldEyes', 'dad', { facing: 'tq-left' }) });
  // sam night
  s += rect(0, 560, 760, 520, { fill: '#3B3470' });
  s += toon('sam', { x: 200, y: 1000, s: 1.15, legs: false, pose: posePreset('bedSit', 'sam'), props: { R: 'phoneBack' }, face: { preset: 'neutral', look: [0, 3] }, tint: { color: '#5562A4', k: 0.55 }, light: { color: '#CFE8FF', k: 0.85, from: 'phone' } });
  s += path('M40 950Q200 925 360 950L380 1080L20 1080Z', { fill: '#4C63C8' });
  s += toon('sam', { x: 560, y: 1060, s: 1.15, legs: false, pose: posePreset('phoneUp', 'sam'), props: { R: 'phoneBack' }, face: 'squint', tint: { color: '#5562A4', k: 0.55 }, light: { color: '#CFE8FF', k: 0.85, from: 'phone' } });
  // sam extras
  const xs = [860, 1060, 1260, 1460, 1660, 1860];
  [0, 0.35, 0.65, 1].forEach((k, i) => { s += bust('sam', xs[i], 700, 120, { face: { preset: 'starstruck', to: 'scared', k } }); });
  s += bust('sam', xs[4], 700, 120, { face: 'yawn', pose: posePreset('yawnCover', 'sam') });
  s += bust('sam', xs[5], 700, 120, { face: 'squint' });
  [0, 0.5, 1].forEach((k, i) => { s += bust('sam', xs[i], 940, 120, { face: { preset: 'nervous', add: { sweatK: k, sweatSize: 1 + k * 0.6 } } }); });
  s += toon('sam', { x: 1460, y: 1060, s: 0.62, face: 'ish', pose: posePreset('shrug', 'sam') });
  s += toon('sam', { x: 1660, y: 1060, s: 0.62, face: 'forcedGrin', pose: posePreset('pointUp', 'sam') });
  s += toon('sam', { x: 1860, y: 1060, s: 0.62, face: 'yawn', pose: posePreset('yawnStretch', 'sam') });
  return doc(s);
}
