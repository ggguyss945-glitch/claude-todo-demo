import * as U from '../ui.js';
import { Defs, rect } from '../ui_style.js';
export default () => {
  const d = new Defs();
  let s = rect(0, 0, 1920, 1080, { fill: d.lin(['#2E86F8', '#8CCBFB']) });
  s += U.panel({ x: 1100, y: 40, w: 760, tabs: ['WORLD', 'PEOPLE', 'TIME'], rows: [
    { cat: 'brightness', value: '70%' }, { cat: 'volume', kind: 'toggle', on: true },
    { cat: 'gravity', kind: 'slider', selected: true, value: 'Moon', v: 0.06, bubble: 'MOON 0.16g', stops: ['Moon', 'Earth', 'Jupiter'] },
    { cat: 'subtitles', kind: 'toggle', on: false }, { cat: 'parental', kind: 'locked' } ] });
  s += U.toast({ x: 60, y: 60, sub: 'Gravity → {Moon}', life: 0.6 });
  s += U.changeNote({ x: 60, y: 230 });
  s += U.toggle({ x: 80, y: 400, k: 0 }) + U.toggle({ x: 260, y: 400, k: 0.5 }) + U.toggle({ x: 440, y: 400, k: 1 });
  s += U.timerPill({ x: 640, y: 390 }) + U.timerPill({ x: 640, y: 520, red: true, text: '00:09', pulse: 0.6 });
  s += U.dial({ cx: 300, cy: 760, r: 220, n: 60, frac: 0.75 });
  s += U.muteBadge({ cx: 640, cy: 760 });
  s += U.lockBadge({ x: 760, y: 700 });
  s += U.emojiBubble({ x: 700, y: 860, emojis: ['angry', 'scream', 'exclaim'] });
  return { w: 1920, h: 1080, svg: `<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">${d}${s}</svg>` };
};
