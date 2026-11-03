// UI kit sheet: every REALITY SETTINGS element on one page. Designed at 2560x1440 (render at scale 1.5 -> 3840x2160).
import * as U from '../ui.js';
import { Defs, rect, text, g, f, FONT } from '../ui_style.js';

const KW = 2560, KH = 1440;
const at = (x, y, s, svg) => `<g transform="translate(${f(x)} ${f(y)}) scale(${s})">${svg}</g>`;
const label = (x, y, s, sub = '') => text(x, y, `${s}${sub ? `<tspan fill="#7A80A8" font-weight="800">  ${sub}</tspan>` : ''}`, { fontFamily: FONT.ui, fontWeight: 900, fontSize: 22, fill: '#2A2F5A', letterSpacing: 1.5 });

export default () => {
  const d = new Defs();
  let s = rect(0, 0, KW, KH, { fill: d.lin(['#E6EBFA', '#CDD6F0']) });
  s += rect(0, 0, KW, KH, { fill: d.pattern(48, 48, `<circle cx="24" cy="24" r="2" fill="#B9C3E4"/>`) });
  // column A: the whole app panel with all twelve categories
  const rows = [
    { cat: 'brightness', value: '100%' },
    { cat: 'volume', kind: 'toggle', on: true },
    { cat: 'gravity', kind: 'slider', h: 284, selected: true, value: 'Moon', v: 0.07, iconL: 'moon', iconR: 'planet', bubble: 'MOON · 0.16 g', stops: ['Moon', 'Earth', 'Jupiter'] },
    { cat: 'subtitles', kind: 'toggle', on: false },
    { cat: 'speed', value: '2x' },
    { cat: 'language', value: '{Cat|pink}' },
    { cat: 'graphics', value: 'Ultra' },
    { cat: 'difficulty', value: '{Hard|red}' },
    { cat: 'weather', value: 'Sunny' },
    { cat: 'parental', kind: 'locked' },
    { cat: 'developer', value: 'Off' },
    { cat: 'reset', value: '{Danger|red}' },
  ];
  s += label(40, 46, 'APP PANEL', '12 categories');
  s += at(40, 64, 0.69, U.panel({ x: 0, y: 0, w: 760, tabs: ['WORLD', 'PEOPLE', 'TIME'], rows }));
  // column B
  const bx = 620;
  s += label(bx, 46, 'TOGGLE', 'knob rolls + overshoots');
  [0, 0.3, 0.55, 0.8, 1].forEach((k, i) => { s += at(bx + i * 128, 74, 0.82, U.toggle({ x: 0, y: 0, k })); });
  s += label(bx, 186, 'SLIDER', 'end icons · gear knob · value bubble');
  s += U.slider({ x: bx, y: 330, w: 640, v: 0.62, bubble: 'JUPITER · 2.5 g', stops: ['Moon', 'Earth', 'Jupiter'] });
  s += label(bx, 456, 'TOAST', 'with life bar');
  s += U.toast({ x: bx, y: 472, title: 'Change applied', sub: 'Gravity → {Moon} · 0.16 g', life: 0.65 });
  s += label(bx, 636, 'USER-CHANGE NOTIFICATION');
  s += at(bx, 652, 0.8, U.changeNote({ x: 0, y: 0, user: 'LilyRoar', setting: 'GRAVITY', value: 'Bouncy', avatar: '#FF5FA8' }));
  s += at(bx, 742, 0.8, U.changeNote({ x: 0, y: 0, user: 'Kevin', setting: 'WEATHER', value: 'Rain', avatar: '#2FAE55', cat: 'weather' }));
  s += label(bx, 856, 'CONFIRMATION POP-UP');
  s += at(bx, 930, 0.74, U.confirm({ cx: 400, cy: 220, w: 800, press: 0.6, hot: 'yes' }));
  s += label(bx, 1316, 'POP-IN', 'p .12 → 1: overshoot + ring');
  [0.12, 0.3, 0.45, 0.65, 1].forEach((p, i) => { s += U.muteBadge({ cx: bx + 60 + i * 126, cy: 1384, r: 38, label: '' }, p); });
  // column C
  const cx = 1330;
  s += label(cx, 46, 'TERMS &amp; CONDITIONS');
  s += at(cx, 64, 0.74, U.terms({ x: 0, y: 0, w: 660, h: 820, checked: true }));
  s += label(cx, 700, 'PATCH NOTES');
  s += at(cx, 716, 0.7, U.patchNotes({ x: 0, y: 0, w: 720 }));
  s += label(cx, 1112, 'INSTALL / PROGRESS');
  s += at(cx, 1128, 0.64, U.install({ x: 0, y: 0, w: 880, v: 0.62, t: 0.1 }));
  s += label(cx, 1296, 'FLOATING SUBTITLES');
  s += at(cx, 1330, 0.8, U.subtitle({ cx: 330, y: 0, text: '[aggressive leaf blowing]', speaker: 'KEVIN', tailX: 520 }));
  // column D
  const dx = 1980;
  s += label(dx, 46, 'WORLD-SPACE DIAL');
  s += U.dial({ cx: dx + 270, cy: 240, r: 165, n: 46, frac: 46 / 60 });
  s += label(dx, 446, 'CORNER PILL', 'turns red at 0:10');
  s += at(dx, 462, 0.82, U.timerPill({ x: 0, y: 0, text: '00:46' }));
  s += at(dx + 288, 462, 0.82, U.timerPill({ x: 0, y: 0, text: '00:09', red: true, pulse: 0.7 }));
  s += label(dx, 600, 'DAY CARD', 'gear · tile · 7 pips');
  s += U.dayCard({ cx: dx + 150, cy: 800, day: 2, scale: 0.4, gearRot: 6 });
  s += U.dayCard({ cx: dx + 420, cy: 800, day: 7, scale: 0.4, gearRot: -4 });
  s += label(dx, 1000, 'LOCK', 'shakes on a denied tap');
  s += at(dx + 10, 1060, 0.85, U.lockBadge({ x: 0, y: 0 }));
  s += label(dx, 1140, 'MUTE BADGE · EMOJI BUBBLE');
  s += U.muteBadge({ cx: dx + 70, cy: 1240, r: 56 });
  s += U.emojiBubble({ x: dx + 160, y: 1176, emojis: ['angry', 'scream', 'exclaim'], size: 70 });
  s += U.emojiBubble({ x: dx + 160, y: 1320, emojis: ['skull', 'heart', 'question'], size: 50, tail: 'br' });
  return { w: KW, h: KH, svg: `<svg xmlns="http://www.w3.org/2000/svg" width="${KW}" height="${KH}" viewBox="0 0 ${KW} ${KH}">${d}${s}</svg>` };
};
