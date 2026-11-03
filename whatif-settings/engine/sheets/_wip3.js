import { begin, doc, studio, toon, caption, bust } from './common.js';
import { posePreset } from '../cast.js';
import { rect, path } from '../style.js';
export default function make(q = {}) {
  begin();
  let s = rect(0, 0, 1920, 1080, { fill: '#3B3470' });
  const nl = { tint: { color: '#5562A4', k: 0.55 }, light: { color: '#CFE8FF', k: 0.85, from: 'phone' }, props: { R: 'phoneBack' }, legs: false };
  s += toon('sam', { x: 330, y: 1000, s: 2.2, pose: posePreset('bedSit', 'sam'), face: { preset: 'neutral', look: [0, 3] }, ...nl });
  s += path('M0 880Q330 850 660 880L700 1080L-40 1080Z', { fill: '#4C63C8' });
  s += toon('sam', { x: 960, y: 1060, s: 2.2, pose: posePreset('phoneLap', 'sam'), face: 'scared', ...nl });
  s += rect(1300, 0, 620, 1080, { fill: '#E9EDFA' });
  s += toon('sam', { x: 1610, y: 1040, s: 2.0, face: 'ish', pose: posePreset('shrug', 'sam') });
  return doc(s);
}
