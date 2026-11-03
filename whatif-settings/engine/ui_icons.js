// Glyph set for the REALITY SETTINGS app. Each glyph is drawn in a 100x100 box centred on (0,0) (-50..50),
// as chunky rounded shapes in one colour (default white) so it reads at phone size. glyph(name, color) -> svg.
import { f, rrPath, circle, rect, path, poly, line, ellipse, gearPath, st, text, FONT } from './ui_style.js';

const R = (x, y, w, h, r, fill) => path(rrPath(x, y, w, h, r), { fill });

const G = {
  brightness: (c) => {
    let s = circle(0, 0, 19, { fill: c });
    for (let i = 0; i < 8; i++) {
      const a = (i * 45 * Math.PI) / 180;
      s += line(Math.cos(a) * 29, Math.sin(a) * 29, Math.cos(a) * 41, Math.sin(a) * 41, st(c, 9));
    }
    return s;
  },
  volume: (c) => path('M-38 -13H-22L-4 -30V30L-22 13H-38Z', { fill: c, ...st(c, 6) }) +
    path('M9 -14Q17 0 9 14', { fill: 'none', ...st(c, 8) }) + path('M20 -26Q35 0 20 26', { fill: 'none', ...st(c, 8) }),
  mute: (c) => path('M-38 -13H-22L-4 -30V30L-22 13H-38Z', { fill: c, ...st(c, 6) }) +
    line(12, -14, 38, 14, st(c, 9)) + line(38, -14, 12, 14, st(c, 9)),
  gravity: (c) => // Newton's apple dropping toward a planet horizon, with motion dashes
    path('M-46 46Q0 16 46 46Z', { fill: c }) +
    path('M0 -22C-7 -28 -22 -26 -22 -10C-22 4 -12 12 -5 12Q0 10 5 12C12 12 22 4 22 -10C22 -26 7 -28 0 -22Z', { fill: c }) +
    path('M0 -22Q2 -32 8 -36', { fill: 'none', ...st(c, 5) }) + path('M6 -30Q16 -40 24 -32Q14 -24 6 -30Z', { fill: c }) +
    line(-30, -40, -30, -26, st(c, 6)) + line(30, -18, 30, -4, st(c, 6)),
  subtitles: (c) => path(rrPath(-40, -28, 80, 56, 13), { fill: 'none', ...st(c, 8) }) +
    R(-27, -6, 30, 9, 4.5, c) + R(8, -6, 19, 9, 4.5, c) + R(-27, 9, 18, 9, 4.5, c) + R(-4, 9, 31, 9, 4.5, c),
  speed: (c) => path('M-40 -26L-4 0L-40 26Z', { fill: c, ...st(c, 8) }) + path('M0 -26L36 0L0 26Z', { fill: c, ...st(c, 8) }),
  language: (c) => // speech bubble with "Aa"
    path('M-38 -30H38Q44 -30 44 -24V14Q44 20 38 20H-6L-22 34V20H-38Q-44 20 -44 14V-24Q-44 -30 -38 -30Z', { fill: 'none', ...st(c, 7) }) +
    text(0, 11, 'Aa', { fill: c, fontFamily: FONT.ui, fontWeight: 900, fontSize: 36, textAnchor: 'middle' }),
  graphics: (c) => path(rrPath(-40, -30, 80, 54, 10), { fill: 'none', ...st(c, 8) }) +
    path('M-30 16L-10 -6L2 6L12 -4L30 16Z', { fill: c, ...st(c, 5) }) + circle(18, -16, 6, { fill: c }) +
    R(-14, 30, 28, 8, 4, c),
  difficulty: (c) => // friendly skull
    path('M0 -38C-24 -38 -36 -22 -36 -4C-36 10 -28 16 -22 18V30Q-22 34 -18 34H18Q22 34 22 30V18C28 16 36 10 36 -4C36 -22 24 -38 0 -38Z', { fill: c }) +
    ellipse(-13, -4, 9, 10, { fill: 'var(--hole, #000)', opacity: 0.85 }) + ellipse(13, -4, 9, 10, { fill: 'var(--hole, #000)', opacity: 0.85 }) +
    path('M0 8L-5 16H5Z', { fill: 'var(--hole, #000)', opacity: 0.85 }) +
    line(-8, 26, -8, 34, { stroke: 'var(--hole, #000)', strokeWidth: 3, opacity: 0.7 }) + line(8, 26, 8, 34, { stroke: 'var(--hole, #000)', strokeWidth: 3, opacity: 0.7 }),
  weather: (c) => {
    let s = circle(12, -12, 15, { fill: c, opacity: 0.85 });
    for (let i = 0; i < 6; i++) {
      const a = ((-150 + i * 40) * Math.PI) / 180;
      s += line(12 + Math.cos(a) * 22, -12 + Math.sin(a) * 22, 12 + Math.cos(a) * 30, -12 + Math.sin(a) * 30, { ...st(c, 6), opacity: 0.85 });
    }
    return s + path('M-26 30H24Q38 30 38 16Q38 3 25 2Q22 -12 7 -12Q-6 -12 -10 0Q-12 -1 -16 -1Q-30 -1 -31 12Q-40 14 -40 22Q-40 30 -26 30Z', { fill: c });
  },
  parental: (c) => // shield with keyhole
    path('M0 -40L34 -28V0C34 20 18 34 0 42C-18 34 -34 20 -34 0V-28Z', { fill: c }) +
    circle(0, -4, 9, { fill: 'var(--hole, #000)', opacity: 0.8 }) + path('M-5 0L-8 20H8L5 0Z', { fill: 'var(--hole, #000)', opacity: 0.8 }),
  developer: (c) => path('M-18 -26L-40 0L-18 26', { fill: 'none', ...st(c, 9) }) + path('M18 -26L40 0L18 26', { fill: 'none', ...st(c, 9) }) +
    line(7, -32, -7, 32, st(c, 8)),
  reset: (c) => path('M-26 -16A32 32 0 1 0 -4 -31', { fill: 'none', ...st(c, 9) }) + path('M-10 -46L8 -31L-10 -16Z', { fill: c, ...st(c, 4) }) +
    circle(0, 1, 7, { fill: c }),
  check: (c) => path('M-30 2L-10 22L32 -22', { fill: 'none', ...st(c, 13) }),
  close: (c) => line(-22, -22, 22, 22, st(c, 12)) + line(22, -22, -22, 22, st(c, 12)),
  lock: (c) => path('M-20 -6V-18A20 20 0 0 1 20 -18V-6', { fill: 'none', ...st(c, 10) }) + R(-30, -8, 60, 46, 10, c) +
    circle(0, 10, 7, { fill: 'var(--hole, #000)', opacity: 0.75 }) + rect(-3, 12, 6, 12, { fill: 'var(--hole, #000)', opacity: 0.75, rx: 3 }),
  unlock: (c) => path('M-20 -6V-20A20 20 0 0 1 18 -28', { fill: 'none', ...st(c, 10) }) + R(-30, -8, 60, 46, 10, c),
  gear: (c) => path(gearPath(0, 0, 44, 34, 9, -90, 0.52), { fill: c }) + circle(0, 0, 14, { fill: 'var(--hole, #000)', opacity: 0.9 }),
  clock: (c) => circle(0, 0, 36, { fill: 'none', ...st(c, 9) }) + path('M0 -20V0L14 10', { fill: 'none', ...st(c, 8) }),
  warning: (c) => path('M0 -38L40 32H-40Z', { fill: c, ...st(c, 10) }) + R(-5, -16, 10, 28, 5, 'var(--hole, #000)') + circle(0, 22, 6, { fill: 'var(--hole, #000)' }),
  arrow: (c) => path('M-34 0H28M10 -20L30 0L10 20', { fill: 'none', ...st(c, 11) }),
  chevron: (c) => path('M-12 -24L12 0L-12 24', { fill: 'none', ...st(c, 12) }),
  cat: (c) => path('M-34 -36L-14 -18Q0 -22 14 -18L34 -36L36 6C36 26 20 38 0 38C-20 38 -36 26 -36 6Z', { fill: c }) +
    ellipse(-13, 2, 5, 6, { fill: 'var(--hole, #000)' }) + ellipse(13, 2, 5, 6, { fill: 'var(--hole, #000)' }) + path('M-4 14H4L0 18Z', { fill: 'var(--hole, #000)' }),
  user: (c) => circle(0, -14, 18, { fill: c }) + path('M-34 38C-34 16 -18 8 0 8C18 8 34 16 34 38Z', { fill: c }),
  download: (c) => path('M0 -36V12M-20 -8L0 12L20 -8', { fill: 'none', ...st(c, 10) }) + R(-34, 24, 68, 11, 5.5, c),
  sparkle: (c) => path('M0 -40Q5 -5 40 0Q5 5 0 40Q-5 5 -40 0Q-5 -5 0 -40Z', { fill: c }),
  moon: (c) => path('M10 -36A38 38 0 1 0 36 10A30 30 0 1 1 10 -36Z', { fill: c }),
  feather: (c) => path('M30 -38C-6 -36 -28 -6 -30 30L-36 40M-30 30C-2 30 22 8 30 -38', { fill: c, ...st(c, 6) }),
  weight: (c) => // the classic cartoon weight: a trapezoid with a ring on top
    circle(0, -26, 11, { fill: 'none', ...st(c, 8) }) + path('M-22 -12H22L38 38H-38Z', { fill: c, ...st(c, 6) }) +
    text(0, 26, 'T', { fill: 'var(--hole, #000)', fontFamily: FONT.title, fontSize: 34, textAnchor: 'middle', opacity: 0.8 }),
  planet: (c) => circle(0, 0, 30, { fill: c }) + path('M-28 -9H28M-30 6H30', { fill: 'none', stroke: 'var(--hole, #000)', strokeWidth: 5, opacity: 0.45 }) +
    ellipse(0, 0, 48, 14, { fill: 'none', ...st(c, 6), transform: 'rotate(-18)' }),
  globe: (c) => circle(0, 0, 36, { fill: 'none', ...st(c, 8) }) + ellipse(0, 0, 15, 36, { fill: 'none', ...st(c, 6) }) + line(-36, 0, 36, 0, st(c, 6)),
  bounce: (c) => circle(18, -22, 15, { fill: c }) + path('M-40 34Q-28 -16 -14 34Q-4 0 6 34', { fill: 'none', ...st(c, 6), strokeDasharray: '2 10' }) + rect(-44, 36, 88, 8, { rx: 4, fill: c }),
  anvil: (c) => G.weight(c),
  turtle: (c) => path('M-30 10Q-30 -24 0 -24Q30 -24 30 10Z', { fill: c }) + circle(36, 0, 9, { fill: c }) + R(-26, 8, 12, 14, 5, c) + R(14, 8, 12, 14, 5, c),
  rabbit: (c) => ellipse(-8, -26, 7, 18, { fill: c }) + ellipse(8, -26, 7, 18, { fill: c }) + circle(0, 6, 26, { fill: c }),
  sunSmall: (c) => circle(0, 0, 14, { fill: c }) + [0, 1, 2, 3, 4, 5, 6, 7].map((i) => { const a = i * Math.PI / 4; return line(Math.cos(a) * 22, Math.sin(a) * 22, Math.cos(a) * 32, Math.sin(a) * 32, st(c, 7)); }).join(''),
  sunBig: (c) => G.brightness(c),
  volLow: (c) => path('M-30 -13H-14L4 -30V30L-14 13H-30Z', { fill: c, ...st(c, 6) }),
  bell: (c) => path('M0 -38C-20 -38 -28 -20 -28 -4V12L-36 22H36L28 12V-4C28 -20 20 -38 0 -38Z', { fill: c }) + circle(0, 30, 8, { fill: c }),
  play: (c) => path('M-20 -30L30 0L-20 30Z', { fill: c, ...st(c, 8) }),
  pause: (c) => R(-26, -30, 18, 60, 6, c) + R(8, -30, 18, 60, 6, c),
};

export const GLYPHS = Object.keys(G);

/** glyph(name, color, hole) -> svg in a 100 box around 0,0. 'hole' colours cut-out details (eyes, keyholes). */
export function glyph(name, color = '#FFFFFF', hole = '#1B2347') {
  const fn = G[name];
  if (!fn) return text(0, 16, '?', { fill: color, fontFamily: FONT.ui, fontWeight: 900, fontSize: 50, textAnchor: 'middle' });
  return fn(color).split('var(--hole, #000)').join(hole);
}
