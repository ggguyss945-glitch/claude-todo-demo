// _wip — scratch QA sheet (deleted when the hook cast is final)
import { begin, doc, studio, toon, caption } from './common.js';
export default function make(q = {}) {
  begin();
  let s = studio({ horizon: 760 });
  const row = (y, list) => list.forEach(([x, o, lab]) => { s += toon('tiny', { x, y, s: 1.2, ...o }); s += caption(x, y + 40, lab, { size: 16 }); });
  row(420, [[160, { face: 'neutral' }, 'sit front neutral'], [420, { face: 'happy', pose: { wag: 0.8 } }, 'happy wag'], [680, { face: 'excited', facing: 'tq-right' }, 'excited tq-right'],
    [940, { face: 'confused', facing: 'side-left' }, 'confused side-left'], [1200, { face: 'shocked' }, 'shocked'], [1460, { face: 'happy', facing: 'side-right' }, 'happy side-right'], [1720, { face: 'sad', facing: 'tq-left' }, 'sad tq-left']]);
  row(960, [[200, { posture: 'stand', face: 'happy', facing: 'side-right', pose: { wag: 0.6, legFL: 20, legHR: -15 } }, 'stand side-right'], [560, { posture: 'stand', face: 'excited', facing: 'tq-right' }, 'stand tq-right'],
    [880, { posture: 'stand', face: 'shocked' }, 'stand front'], [1200, { posture: 'stand', face: 'confused', facing: 'tq-left' }, 'stand tq-left'], [1600, { posture: 'stand', face: 'neutral', facing: 'side-left' }, 'stand side-left']]);
  return doc(s);
}
