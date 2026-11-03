// Hook UI kit (S00 + S01-L001): every new component of ui2.js / ui.js extensions in several states.
// arg '' -> UI sheet 2560x1440 (render at scale 1.5 -> 3840x2160, renders/ui_hook_kit.png)
// arg 'fx' -> FX / captions / montage sheet 1920x1080 (renders/ui_hook_fx.png)
import * as U from '../ui.js';
import * as U2 from '../ui2.js';
import { ripple, sunFlare, whiteout, crackedGlass, scrollStreaks, speedLines, sparkles, godRays, shockRing, boxBlur } from '../fx.js';
import { caption, captionsFromWords, CAP_Y } from '../caption.js';
import { street, bedroom, wrap } from '../sets.js';
import { Defs, rect, text, g, f, FONT, path, rrPath, line } from '../ui_style.js';

const at = (x, y, s, svg) => `<g transform="translate(${f(x)} ${f(y)}) scale(${s})">${svg}</g>`;
const label = (x, y, s, sub = '') => text(x, y, `${s}${sub ? `<tspan fill="#7A80A8" font-weight="800">  ${sub}</tspan>` : ''}`, { fontFamily: FONT.ui, fontWeight: 900, fontSize: 22, fill: '#2A2F5A', letterSpacing: 1.5 });
const tag = (x, y, s, o = {}) => text(x, y, s, { fontFamily: FONT.ui, fontWeight: 900, fontSize: o.size || 17, fill: o.fill || '#4A5080', textAnchor: o.anchor || 'middle', ...(o.stroke ? { stroke: o.stroke, strokeWidth: 5, paintOrder: 'stroke', strokeLinejoin: 'round' } : {}) });
function cell(d, x, y, w, h, inner, bg) {
  const clip = d.clip(path(rrPath(x, y, w, h, 22)));
  return g(rect(x, y, w, h, { fill: bg || d.lin(['#F4F6FD', '#DCE3F6']) }) + inner, { clipPath: clip }) +
    path(rrPath(x, y, w, h, 22), { fill: 'none', stroke: '#B4BEE0', strokeWidth: 2.5 });
}
/** a 1920x1080 frame shrunk into a cell */
const frameAt = (x, y, k, svg) => `<g transform="translate(${f(x)} ${f(y)}) scale(${k})"><svg width="1920" height="1080" viewBox="0 0 1920 1080" overflow="hidden">${svg}</svg></g>`;

function uiSheet() {
  const KW = 2560, KH = 1440, d = new Defs();
  let s = rect(0, 0, KW, KH, { fill: d.lin(['#E6EBFA', '#CDD6F0']) });
  s += rect(0, 0, KW, KH, { fill: d.pattern(48, 48, `<circle cx="24" cy="24" r="2" fill="#B9C3E4"/>`) });

  // ---------------- row A: phone POV states + inside the app + app icon ----------------
  s += label(30, 44, 'PHONE POV', "Sam's hand · thumb tap / press / drag · glare · rattle · night glow");
  const SKY = d.lin(['#5FA8FB', '#BFE0FD']), NIGHT = d.lin(['#2A2466', '#4C4C9A']);
  const pc = [
    { bg: SKY, cap: 'home · new app pops · rattle', ph: { screen: U2.homeScreen({ newApp: 0.62, wiggle: { t: 0.03, amp: 7 } }), bg: 'none', thumb: { x: 560, y: 1060, press: 0 }, shake: { amp: 9, t: 0.013 } } },
    { bg: SKY, cap: 'notification · tap OPEN', ph: { screen: U2.homeScreen({ newApp: 1 }) + rect(0, 0, 720, 1480, { fill: '#0B0E2A', opacity: 0.35 }) + at(20, 150, 0.79, U2.notifyCard({ x: 0, y: 0, rattle: 0.6, t: 0.02 })), bg: 'none', thumb: { x: 600, y: 290, press: 0.8 } } },
    { bg: SKY, cap: 'Dog size · drag (press .7)', ph: (() => { const sc = U2.dogSizeScreen({ v: 0.62, grab: 1 }); return { screen: U2.appScreen({ time: '4:05', crumb: 'Settings › {World|purple} › {Pets|pink}', content: sc.svg }), thumb: { x: sc.knob[0] + 14, y: sc.knob[1] + 26, press: 0.7 } }; })() },
    { bg: NIGHT, cap: 'Brightness · night glow', ph: (() => { const sc = U2.brightnessScreen({ v: 0.2, grab: 1, t: 0.2 }); return { screen: U2.appScreen({ time: '2:13', crumb: 'Settings › {Display|purple}', content: sc.svg }), thumb: { x: sc.knob[0] + 14, y: sc.knob[1] + 26, press: 0.5 }, glow: 0.9 }; })() },
  ];
  pc.forEach((c, i) => {
    const x = 30 + i * 279, y = 64, w = 265, h = 520;
    s += cell(d, x, y, w, h, U2.phone({ x: x + w / 2 - 6, y: y + 246, s: 0.27, rot: -6, ...c.ph }) + tag(x + w / 2, y + h - 14, c.cap, { fill: '#FFFFFF', stroke: '#1E2347', size: 18 }), c.bg);
  });
  // inside the app: zoom-through end frame + brightness fills the screen
  s += label(1160, 44, 'INSIDE THE APP', 'edge .6 · Brightness v .45 / .97');
  const inA = U2.insideApp(at(560, 250, 1, U2.settingCard({ x: 0, y: 0, w: 800, cat: 'gravity', value: 'Moon', v: 0.1, bubble: 'MOON · 0.16 g', iconL: 'moon', iconR: 'planet', stops: ['Moon', 'Earth', 'Jupiter'], grab: 0.6 })) + at(560, 700, 1, U.row({ x: 0, y: 0, w: 800, cat: 'volume', kind: 'toggle', k: 1 })), { header: true, edge: 0.6, crumb: 'Settings › {World|purple} › {Gravity|purple}' });
  const TW = 446, TH = 251;
  s += cell(d, 1160, 64, TW, TH, frameAt(1160, 64, TW / 1920, inA));
  s += cell(d, 1622, 64, TW, TH, frameAt(1622, 64, TW / 1920, U2.brightnessFull({ v: 0.45, t: 0.4 })));
  s += cell(d, 2084, 64, TW, TH, frameAt(2084, 64, TW / 1920, U2.brightnessFull({ v: 0.97, t: 0.4 })));
  s += label(1160, 352, 'APP ICON', 'glow · badge · shine · spin · zoom-safe (size 900 crop)');
  let ic = '';
  [[1250, 80, {}], [1400, 110, { glow: 0.8 }], [1580, 130, { badge: 1, glow: 0.4 }], [1770, 130, { shine: 0.45, rot: 20 }]].forEach(([x, r, o]) => { ic += U2.appIcon({ cx: x, cy: 470, size: r, ...o }); });
  ic += U2.appIcon({ cx: 2330, cy: 560, size: 900, glow: 0.5, rot: 8 });
  s += cell(d, 1160, 366, 1370, 218, ic, d.lin(['#3B2A86', '#5A46C8']));

  // ---------------- row B: undo button, history, odometer, pill + tags, notification ----------------
  s += label(30, 640, 'UNDO BUTTON', 'crack 0 / .5 / 1 · fall .35 / .7');
  let ub = '';
  [[0, 0, 130, 730], [0.5, 0, 325, 730], [1, 0, 520, 730], [1, 0.35, 200, 850], [1, 0.7, 450, 850]].forEach(([c, fl, cx, cy]) => {
    ub += U2.undoButton({ cx: 30 + cx, cy, scale: 0.38, crack: c, fall: fl, fallDist: 260, seed: 7 });
    ub += tag(30 + cx, fl ? 985 : 790, fl ? `fall ${fl}` : `crack ${c}`);
  });
  s += cell(d, 30, 660, 650, 340, ub);
  s += label(700, 640, 'UNDO HISTORY', 'scroll 0 / fast 205');
  s += cell(d, 700, 660, 520, 340, at(712, 670, 0.3, U2.undoHistory({ x: 0, y: 0, w: 800, h: 1040, scroll: 0 })) +
    at(966, 670, 0.3, U2.undoHistory({ x: 0, y: 0, w: 800, h: 1040, scroll: 205.4, speed: 140 })), d.lin(['#2A3470', '#1A2250']));
  s += label(1240, 640, 'ODOMETER', '1 / 87.6 / 412');
  s += cell(d, 1240, 660, 470, 340, at(1252, 676, 0.47, U2.counter({ x: 0, y: 0, value: 1 })) + at(1482, 676, 0.47, U2.counter({ x: 0, y: 0, value: 87.62, speed: 300 })) +
    at(1367, 828, 0.47, U2.counter({ x: 0, y: 0, value: 412 })));
  s += label(1730, 640, 'PILL · DEFAULT TAGS');
  s += cell(d, 1730, 660, 360, 340, at(1748, 676, 0.6, U.timerPill({ x: 0, y: 0, text: '1:00', red: true, label: 'FACTORY RESET', frac: 1, pulse: 0.6 })) +
    at(1748, 762, 0.6, U.timerPill({ x: 0, y: 0, text: '0:41', red: true, label: 'FACTORY RESET', frac: 41 / 60, pulse: 0.2 })) +
    U.nameTag({ variant: 'default', cx: 1820, y: 852, size: 0.56, swing: -8, string: 60 }) + U.nameTag({ variant: 'default', cx: 1990, y: 852, size: 0.56, swing: 7, string: 60, flicker: 0.5 }), d.lin(['#C9D0E2', '#B3BCD6']));
  s += label(2110, 640, 'NOTIFICATION', 'rattle 0 / 1');
  s += cell(d, 2110, 660, 420, 340, at(2124, 690, 0.455, U2.notifyCard({ x: 0, y: 0 })) + at(2124, 846, 0.455, U2.notifyCard({ x: 0, y: 0, rattle: 1, t: 0.011 })), d.lin(['#3B2A86', '#5A46C8']));

  // ---------------- row C: terms, page stack, I AGREE + toast, DAY flip ----------------
  s += label(30, 1056, 'TERMS', 'page 1 / flick .5 / page 4,812 readable (highlight .7)');
  s += cell(d, 30, 1076, 760, 340, at(44, 1086, 0.39, U.terms({ x: 0, y: 0, w: 640, h: 820, checked: false })) +
    at(298, 1086, 0.39, U.terms({ x: 0, y: 0, w: 640, h: 820, flick: 0.5 })) + at(552, 1086, 0.39, U.terms({ x: 0, y: 0, w: 640, h: 820, finePrint: true, highlight: 0.7, checked: true })), d.lin(['#2A3470', '#1A2250']));
  s += label(810, 1056, 'PAGES STACK', '600 / 4,812');
  const ceil = 1076 + 40;
  s += cell(d, 810, 1076, 300, 340, at(810, 1076, 1, '') + U2.pageStack({ cx: 880, base: 1400, n: 600, w: 110, th: 0.18, depth: 16 }) +
    U2.pageStack({ cx: 1020, base: 1400, n: 4812, w: 120, th: 0.07, depth: 18, wobble: 1, t: 0.3 }) + line(810, ceil, 1110, ceil, { stroke: '#7A84AA', strokeWidth: 3, strokeDasharray: '10 8' }) + tag(960, ceil - 10, 'ceiling', { size: 15 }));
  s += label(1130, 1056, 'I AGREE · TOAST', 'press .55 + ripple .4');
  s += cell(d, 1130, 1076, 560, 340, at(1142, 1090, 0.4, U2.agreeButton({ cx: 330, cy: 160, w: 640, h: 184, glow: 0.6 })) +
    at(1414, 1090, 0.4, U2.agreeButton({ cx: 330, cy: 160, w: 640, h: 184, press: 0.55, ripple: 0.4, R: 700 })) +
    at(1146, 1290, 0.5, U2.welcomeToast({ x: 0, y: 0, glow: 1, t: 0.2, life: 0.7 })), d.lin(['#2A3470', '#1A2250']));
  s += label(1710, 1056, 'DAY CARD FLIP', 'day 1 · flip .25 · flip .7 · 6 → 7 at .5');
  s += cell(d, 1710, 1076, 820, 340, U.dayCard({ cx: 1812, cy: 1246, day: 1, scale: 0.37, gearRot: 4 }) + U.dayCard({ cx: 2018, cy: 1246, day: 1, flip: 0.25, scale: 0.37, gearRot: 10 }) +
    U.dayCard({ cx: 2224, cy: 1246, day: 1, flip: 0.7, scale: 0.37, gearRot: 16 }) + U.dayCard({ cx: 2430, cy: 1246, day: 6, flip: 0.5, scale: 0.37, gearRot: 22 }));
  return { w: KW, h: KH, svg: `<svg xmlns="http://www.w3.org/2000/svg" width="${KW}" height="${KH}" viewBox="0 0 ${KW} ${KH}">${d}${s}</svg>` };
}

function fxSheet() {
  const d = new Defs();
  let s = rect(0, 0, 1920, 1080, { fill: '#DDE3F5' });
  const W3 = 616, H3 = 336, X = (i) => 16 + i * (W3 + 16), Y = (j) => 16 + j * (H3 + 16), K = W3 / 1920;
  const box = (i, j, frame, lab) => {
    const x = X(i), y = Y(j), clip = d.clip(path(rrPath(x, y, W3, H3, 24)));
    return g(frameAt(x, y, K, frame), { clipPath: clip }) + path(rrPath(x, y, W3, H3, 24), { fill: 'none', stroke: '#1E2347', strokeWidth: 4 }) +
      text(x + 18, y + H3 - 18, lab, { fontFamily: FONT.ui, fontWeight: 900, fontSize: 24, fill: '#FFFFFF', stroke: '#1E2347', strokeWidth: 6, paintOrder: 'stroke' });
  };
  const st = street({}).svg;
  // 1 I AGREE sub-boom: the button and the frame-wide ripple
  s += box(0, 0, st + rect(0, 0, 1920, 1080, { fill: '#0B1030', opacity: 0.25 }) + ripple({ cx: 960, cy: 560, squash: 0.62 }, 0.42) + U2.agreeButton({ cx: 960, cy: 560, press: 0.3, ripple: 0.5, R: 900 }), 'ripple boom + I AGREE (press .3, ripple .5)');
  // 2 sun flare + god rays (the moon flaring into a sun)
  const night = street({ night: 1 }).svg;
  s += box(1, 0, night + sunFlare({ cx: 1420, cy: 230, r: 100, k: 0.85, t: 0.4, rays: true }), 'sun flare + god rays (k .85)');
  // 3 white blow-out
  s += box(2, 0, bedroom({ blanket: 'sit', sun: 1 }).svg + whiteout({ cx: 1500, cy: 300 }, 0.42), 'white blow-out (k .42)');
  // 4 cracked glass over the app
  s += box(0, 1, U2.insideApp(U2.undoButton({ cx: 960, cy: 560, scale: 1.6, crack: 0.8 }), { header: true }) + crackedGlass({ cx: 1060, cy: 470, r: 900, k: 0.75, seed: 5 }), 'cracked glass k .75 + UNDO crack .8');
  // 5 fast scroll: history blur + streaks + directional speed lines
  s += box(1, 1, U2.insideApp(U2.undoHistory({ x: 560, y: 90, w: 800, h: 960, scroll: 120.3, speed: 160 })) + scrollStreaks({ x: 560, y: 250, w: 800, h: 800, speed: 40, t: 0.2 }) +
    speedLines({ mode: 'dir', angle: 90, count: 26, width: 8, t: 0.3, op: 0.35, color: '#FFFFFF' }), 'fast UI scroll: blur + streaks');
  // 6 fan montage
  s += box(2, 1, U2.insideApp('', { glare: 0.4 }) + U2.fanMontage({ p: 0.8 }), 'sliders + toggles fan out (p .8)');
  // 7 DAY 1 slam
  s += box(0, 2, rect(0, 0, 1920, 1080, { fill: d.lin(['#2E86F8', '#8CCBFB']) }) + U2.daySlam({ cx: 960, cy: 540, day: 1, p: 0.42, t: 0.3 }), 'DAY 1 slam (p .42, just after the hit)');
  // 8 captions from word timings (S00-L001)
  const words = [['What', 0.05, 0.22], ['if', 0.22, 0.32], ['real', 0.32, 0.55], ['life', 0.55, 0.8], ['had', 0.8, 0.95], ['a', 0.95, 1.02], ['SETTINGS', 1.02, 1.62], ['menu?', 1.62, 2.0]].map(([w, t0, t1]) => ({ w, t0, t1 }));
  const caps = captionsFromWords(words);
  let c8 = rect(0, 0, 1920, 1080, { fill: d.lin(['#63D255', '#4CBF45']) });
  caps.forEach((c, i) => { c8 += caption(c.markup, { y: 230 + i * 240, size: 120 }, 1) + text(1880, 260 + i * 240, `${c.t0.toFixed(2)}-${c.t1.toFixed(2)} s`, { fontFamily: FONT.ui, fontWeight: 900, fontSize: 44, fill: '#FFFFFF', textAnchor: 'end', stroke: '#1E2347', strokeWidth: 8, paintOrder: 'stroke' }); });
  s += box(1, 2, c8, 'captionsFromWords: 1-3 words, auto keyword');
  // 9 caption modes: SYS typewriter + Dad's scream
  s += box(2, 2, rect(0, 0, 1920, 1080, { fill: d.lin(['#1F2A5A', '#141C40']) }) + caption('Factory {RESET|red} in one', { y: 360, size: 110, mode: 'type', chars: 20 }) +
    caption('Who turned on the {SUN|yellow}?!', { y: 700, size: 130, mode: 'scream', t: 0.37 }, 1), 'caption: SYS typewriter · scream');
  return { w: 1920, h: 1080, svg: `<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">${d}${s}</svg>` };
}

export default (arg = '') => (arg === 'fx' ? fxSheet() : uiSheet());
