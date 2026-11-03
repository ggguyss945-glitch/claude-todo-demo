import * as U from '../ui.js';
import { Defs, rect } from '../ui_style.js';
export default () => {
  const d = new Defs();
  let s = rect(0, 0, 1920, 1080, { fill: d.lin(['#2E86F8', '#8CCBFB']) });
  s += U.confirm({ cx: 480, cy: 300, w: 760 });
  s += U.terms({ x: 900, y: 40, w: 560, h: 700 }) + U.iconTile('gravity', 100, 100, 90, U.CATS.gravity.color) + U.iconTile('planet', 200, 100, 90, '#E09040') + U.iconTile('weight', 300, 100, 90, '#5C6B9E') + U.iconTile('bounce', 400, 100, 90, '#FF5596');
  s += U.patchNotes({ x: 1480, y: 40, w: 420, items: [{ tag: 'NEW', text: 'Gravity slider' }, { tag: 'FIXED', text: 'Mondays optional' }, { tag: 'REMOVED', text: "Lily's volume" }] });
  s += U.install({ x: 60, y: 620, w: 800 });
  s += U.subtitle({ cx: 470, y: 900, text: '[aggressive leaf blowing]', speaker: 'KEVIN', tailX: 700 });
  s += U.dayCard({ cx: 1700, cy: 300, day: 3, scale: 0.5, gearRot: 8 });
  s += U.panel({ x: 1150, y: 560, w: 760, h: 520, subtitle: 'Settings › World › {Gravity|purple}', rows: [
    { kind: 'chips', pick: 0 }, { kind: 'sliderBare', v: 0.08, bubble: 'MOON · 0.16 g', stops: ['Moon', 'Earth', 'Jupiter'] } ] });
  return { w: 1920, h: 1080, svg: `<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">${d}${s}</svg>` };
};
