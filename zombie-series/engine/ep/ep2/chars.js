// Episode 2 cast: Nora (15, auburn hair, teal hoodie, freckles) and Leo's photo face.
import { INK, PAL, g, rect, circle, ellipse, line, path, ink, body } from '../../lib.js';

const f = (n) => Math.round(n * 10) / 10;
export const NORA = { hair: '#A4472C', hairDark: '#7E3220', hoodie: '#3E8E86', hoodieDark: '#2F6E68', skin: '#F3E3D3', freckle: '#C98A6A' };

function noraFace({ cx, cy, u, look = 0, expr = 'neutral', blink = 0 }) {
  const ex = cx + look * 0.3 * u, sp = 0.44 * u;
  const eyeH = { shock: 0.2, scared: 0.19, surprised: 0.18, sad: 0.12, serious: 0.11, smirk: 0.11, determined: 0.1 }[expr] ?? 0.13;
  const eo = Math.max(0.08, 1 - blink);
  let s = '';
  for (const side of [-1, 1]) {
    const x = ex + side * sp / 2;
    s += ellipse(x, cy, 0.105 * u, (eyeH + 0.03) * u * eo, { fill: INK });
    if (eo > 0.5) s += circle(x + 0.03 * u, cy - 0.06 * u, 0.03 * u, { fill: '#FFF' });
    s += path(`M${f(x + side * 0.08 * u)} ${f(cy - (eyeH + 0.02) * u * eo)} l${f(side * 0.07 * u)} ${f(-0.06 * u)}`, { fill: 'none', stroke: INK, strokeWidth: 3, strokeLinecap: 'round' });   // a lash flick
  }
  // brows in hair colour, shaped per expression: [inner dy, outer dy] in u (negative = up)
  const B = { neutral: [-0.3, -0.31], serious: [-0.25, -0.31], sad: [-0.37, -0.27], shock: [-0.42, -0.4], scared: [-0.4, -0.33], surprised: [-0.4, -0.38],
    worried: [-0.36, -0.29], determined: [-0.24, -0.33], smirk: [-0.28, -0.3], whisper: [-0.32, -0.3] }[expr] || [-0.3, -0.31];
  for (const side of [-1, 1]) {
    const x = ex + side * sp / 2, inner = expr === 'smirk' && side === 1 ? -0.38 : B[0];
    s += line(x - side * 0.08 * u, cy + inner * u, x + side * 0.1 * u, cy + B[1] * u, { stroke: NORA.hairDark, strokeWidth: 0.07 * u, strokeLinecap: 'round' });
  }
  // freckles
  for (const side of [-1, 1]) for (const [dx, dy] of [[0, 0], [0.09, 0.05], [-0.06, 0.08]]) s += circle(ex + side * (0.36 + dx) * u, cy + (0.2 + dy) * u, 0.022 * u, { fill: NORA.freckle });
  const my = cy + 0.48 * u, mx = ex + look * 0.05 * u;
  s += {
    neutral: line(mx - 0.09 * u, my, mx + 0.09 * u, my, ink(4)),
    serious: path(`M${f(mx - 0.12 * u)} ${f(my + 0.01 * u)} q${f(0.12 * u)} ${f(-0.02 * u)} ${f(0.24 * u)} ${f(0.02 * u)}`, { fill: 'none', ...ink(4) }),
    sad: path(`M${f(mx - 0.12 * u)} ${f(my + 0.05 * u)} Q${f(mx)} ${f(my - 0.06 * u)} ${f(mx + 0.12 * u)} ${f(my + 0.05 * u)}`, { fill: 'none', ...ink(4) }),
    shock: ellipse(mx, my + 0.03 * u, 0.08 * u, 0.12 * u, { fill: INK }),
    scared: ellipse(mx, my + 0.02 * u, 0.08 * u, 0.1 * u, { fill: INK }),
    surprised: ellipse(mx, my + 0.02 * u, 0.06 * u, 0.08 * u, { fill: INK }),
    worried: path(`M${f(mx - 0.13 * u)} ${f(my + 0.03 * u)} q${f(0.07 * u)} ${f(-0.06 * u)} ${f(0.13 * u)} 0 t${f(0.13 * u)} 0`, { fill: 'none', ...ink(4) }),
    determined: line(mx - 0.13 * u, my, mx + 0.11 * u, my - 0.02 * u, ink(5)),
    smirk: path(`M${f(mx - 0.1 * u)} ${f(my + 0.01 * u)} q${f(0.12 * u)} ${f(0.04 * u)} ${f(0.22 * u)} ${f(-0.07 * u)}`, { fill: 'none', ...ink(4) }),
    whisper: ellipse(mx, my, 0.05 * u, 0.05 * u, { fill: INK }),
  }[expr] ?? '';
  return s;
}

// (x, y) is the ground point, like hero(); s=1 is the hero's scale, Nora is drawn a little smaller
export function nora({ x, y, s = 1, pose = 'stand', expr = 'neutral', look = 0, facing = 1, blink = 0, tilt = 0, breathe = 0, extra = '', hood = false, filter = true, behind = '' }) {
  const u = 60 * s * 0.93;
  const B = body({ x, y, u, pose, torsoFill: NORA.hoodie, torsoDark: NORA.hoodieDark, facing, skin: NORA.skin });
  const cy = y - 5.25 * u + B.dr, cx = x + ((pose === 'run' || (pose && pose.a === 'runA')) ? 0.25 * u * facing : 0);
  // long hair falls behind the shoulders: drawn before the body
  const back = path(`M${f(cx - 1.02 * u)} ${f(cy - 0.1 * u)} C${f(cx - 1.25 * u)} ${f(cy + 0.9 * u)} ${f(cx - 1.05 * u)} ${f(cy + 1.75 * u)} ${f(cx - 0.6 * u)} ${f(cy + 1.95 * u)}
    L${f(cx + 0.6 * u)} ${f(cy + 1.95 * u)} C${f(cx + 1.05 * u)} ${f(cy + 1.75 * u)} ${f(cx + 1.25 * u)} ${f(cy + 0.9 * u)} ${f(cx + 1.02 * u)} ${f(cy - 0.1 * u)} Z`, { fill: NORA.hair, ...ink(5) });
  // hood bunched behind the neck
  const hoodS = path(`M${f(x - 0.62 * u)} ${f(B.neckY + 0.05 * u)} Q${f(x)} ${f(B.neckY - 0.35 * u)} ${f(x + 0.62 * u)} ${f(B.neckY + 0.05 * u)} Q${f(x)} ${f(B.neckY + 0.45 * u)} ${f(x - 0.62 * u)} ${f(B.neckY + 0.05 * u)} Z`, { fill: NORA.hoodieDark, ...ink(5) });
  const strings = line(x - 0.16 * u, B.neckY + 0.2 * u, x - 0.2 * u, B.neckY + 0.75 * u, { stroke: '#E8E1D2', strokeWidth: 0.05 * u, strokeLinecap: 'round' })
    + line(x + 0.16 * u, B.neckY + 0.2 * u, x + 0.2 * u, B.neckY + 0.7 * u, { stroke: '#E8E1D2', strokeWidth: 0.05 * u, strokeLinecap: 'round' });
  let h = circle(cx, cy, u, { fill: NORA.skin, ...ink(6) });
  // hair: centre part with side-swept bangs
  h += path(`M${f(cx - 1.0 * u)} ${f(cy + 0.15 * u)} C${f(cx - 1.08 * u)} ${f(cy - 1.15 * u)} ${f(cx + 1.08 * u)} ${f(cy - 1.2 * u)} ${f(cx + 1.0 * u)} ${f(cy + 0.15 * u)}
    L${f(cx + 0.82 * u)} ${f(cy - 0.2 * u)} C${f(cx + 0.55 * u)} ${f(cy - 0.45 * u)} ${f(cx + 0.2 * u)} ${f(cy - 0.62 * u)} ${f(cx + 0.02 * u)} ${f(cy - 0.78 * u)}
    C${f(cx - 0.25 * u)} ${f(cy - 0.5 * u)} ${f(cx - 0.6 * u)} ${f(cy - 0.42 * u)} ${f(cx - 0.84 * u)} ${f(cy - 0.18 * u)} Z`, { fill: NORA.hair, ...ink(5) });
  h += path(`M${f(cx + 0.02 * u)} ${f(cy - 0.95 * u)} q${f(-0.05 * u)} ${f(0.1 * u)} 0 ${f(0.17 * u)}`, { fill: 'none', stroke: NORA.hairDark, strokeWidth: 3 });
  if (hood) h += path(`M${f(cx - 1.12 * u)} ${f(cy + 0.4 * u)} C${f(cx - 1.3 * u)} ${f(cy - 1.45 * u)} ${f(cx + 1.3 * u)} ${f(cy - 1.45 * u)} ${f(cx + 1.12 * u)} ${f(cy + 0.4 * u)} L${f(cx + 0.95 * u)} ${f(cy + 0.3 * u)} C${f(cx + 1.0 * u)} ${f(cy - 1.05 * u)} ${f(cx - 1.0 * u)} ${f(cy - 1.05 * u)} ${f(cx - 0.95 * u)} ${f(cy + 0.3 * u)} Z`, { fill: NORA.hoodie, ...ink(5) });
  h += noraFace({ cx, cy, u, look: look || facing * 0.2, expr, blink });
  const head = tilt ? g(h, { transform: `rotate(${tilt} ${f(cx)} ${f(cy + u)})` }) : h;
  const bodyT = breathe ? `translate(${f(x)} ${f(y)}) scale(1 ${f(1 + breathe)}) translate(${f(-x)} ${f(-y)})` : undefined;
  const backT = tilt ? g(back, { transform: `rotate(${tilt * 0.6} ${f(cx)} ${f(cy + u)})` }) : back;
  return g(behind + backT + B.s + hoodS + strings + head + extra, { filter: filter ? 'url(#wobbleSoft)' : undefined, transform: bodyT });
}

// Leo in the photo: 9, gap-toothed grin, a red cap pushed back
export function leoFace(cx, cy, u) {
  let s = circle(cx, cy, u, { fill: PAL.skin, ...ink(6) });
  s += path(`M${f(cx - 1.0 * u)} ${f(cy - 0.1 * u)} C${f(cx - 1.0 * u)} ${f(cy - 1.3 * u)} ${f(cx + 1.0 * u)} ${f(cy - 1.3 * u)} ${f(cx + 1.0 * u)} ${f(cy - 0.1 * u)} Z`, { fill: PAL.red, ...ink(5) })
    + path(`M${f(cx + 0.3 * u)} ${f(cy - 0.35 * u)} q${f(0.7 * u)} ${f(-0.1 * u)} ${f(1.1 * u)} ${f(0.15 * u)}`, { fill: '#A8402A', ...ink(5) });
  s += path(`M${f(cx - 0.9 * u)} ${f(cy - 0.15 * u)} q${f(0.3 * u)} ${f(-0.25 * u)} ${f(0.6 * u)} ${f(-0.05 * u)} q${f(0.25 * u)} ${f(-0.2 * u)} ${f(0.5 * u)} 0`, { fill: NORA.hair, ...ink(4) });
  for (const side of [-1, 1]) s += ellipse(cx + side * 0.24 * u, cy + 0.05 * u, 0.1 * u, 0.13 * u, { fill: INK }) + circle(cx + side * 0.24 * u + 0.03 * u, cy - 0.01 * u, 0.03 * u, { fill: '#FFF' });
  for (const side of [-1, 1]) for (const [dx, dy] of [[0, 0], [0.08, 0.05]]) s += circle(cx + side * (0.42 + dx) * u, cy + (0.28 + dy) * u, 0.022 * u, { fill: NORA.freckle });
  s += path(`M${f(cx - 0.28 * u)} ${f(cy + 0.4 * u)} Q${f(cx)} ${f(cy + 0.78 * u)} ${f(cx + 0.28 * u)} ${f(cy + 0.4 * u)} Z`, { fill: '#5A2A2A', ...ink(4) })
    + rect(cx - 0.12 * u, cy + 0.4 * u, 0.09 * u, 0.1 * u, { fill: '#FFF' }) + rect(cx + 0.04 * u, cy + 0.4 * u, 0.09 * u, 0.1 * u, { fill: '#FFF' });
  return s;
}
