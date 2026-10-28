// Drawing library for the series: SVG string builders in the Nobody Gets In-like style
// (flat fills, thick wobbly ink outline, paper grain, vignette). Every function returns SVG markup.

export const W = 1920, H = 1080;
export const INK = '#1E1A1A';

export const PAL = {
  paper: '#F5E6CC', cream: '#F7E3C8', card: '#1C1819', tag: '#EDB344',
  wall: '#D4D0BC', wallDark: '#BCBBAB', floor: '#DCCFB4', tile: '#CFC2A6',
  wood: '#B58759', brick: '#A75F40', night: '#2B3446',
  skin: '#F1ECE2', hair: '#3A2A22', jacket: '#5E6B3A', jacketDark: '#4A5530',
  phones: '#F08A24', jeans: '#2F3A4A', shoe: '#1E1A1A',
  zSkin: '#8F9C86', zSkinDark: '#6E7A67', zEye: '#3B403A', zPupil: '#DADDCB',
  red: '#D65632', blue: '#436799', yellow: '#E9B93E', green: '#6F8F4E',
};

export function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const f = (n) => Math.round(n * 10) / 10;
export const pts = (arr) => arr.map(([x, y]) => `${f(x)},${f(y)}`).join(' ');

export function attrs(o) {
  return Object.entries(o).filter(([, v]) => v !== undefined && v !== null)
    .map(([k, v]) => `${k.replace(/[A-Z]/g, (m) => '-' + m.toLowerCase())}="${v}"`).join(' ');
}
export const g = (inner, a = {}) => `<g ${attrs(a)}>${inner}</g>`;
export const rect = (x, y, w, h, a = {}) => `<rect ${attrs({ x: f(x), y: f(y), width: f(w), height: f(h), ...a })}/>`;
export const circle = (cx, cy, r, a = {}) => `<circle ${attrs({ cx: f(cx), cy: f(cy), r: f(r), ...a })}/>`;
export const ellipse = (cx, cy, rx, ry, a = {}) => `<ellipse ${attrs({ cx: f(cx), cy: f(cy), rx: f(rx), ry: f(ry), ...a })}/>`;
export const line = (x1, y1, x2, y2, a = {}) => `<line ${attrs({ x1: f(x1), y1: f(y1), x2: f(x2), y2: f(y2), ...a })}/>`;
export const poly = (p, a = {}) => `<polygon ${attrs({ points: pts(p), ...a })}/>`;
export const path = (d, a = {}) => `<path ${attrs({ d, ...a })}/>`;
export const text = (x, y, s, a = {}) => `<text ${attrs({ x: f(x), y: f(y), ...a })}>${s}</text>`;

export const ink = (w = 6) => ({ stroke: INK, strokeWidth: w, strokeLinejoin: 'round', strokeLinecap: 'round' });
export const filled = (fill, w = 6) => ({ fill, ...ink(w) });

// ---------- global defs: wobble, grain, vignette ----------
export function defs(seed = 7, boil = seed) {
  return `<defs>
  <filter id="wobble" x="-5%" y="-5%" width="110%" height="110%">
    <feTurbulence type="fractalNoise" baseFrequency="0.012" numOctaves="2" seed="${seed}" result="n"/>
    <feDisplacementMap in="SourceGraphic" in2="n" scale="5" xChannelSelector="R" yChannelSelector="G"/>
  </filter>
  <filter id="wobbleSoft" x="-5%" y="-5%" width="110%" height="110%">
    <feTurbulence type="fractalNoise" baseFrequency="0.02" numOctaves="1" seed="${boil + 3}" result="n"/>
    <feDisplacementMap in="SourceGraphic" in2="n" scale="2.5" xChannelSelector="R" yChannelSelector="G"/>
  </filter>
  <filter id="grain" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3" seed="${seed + 11}" stitchTiles="stitch"/>
    <feColorMatrix type="saturate" values="0"/>
    <feComponentTransfer><feFuncA type="table" tableValues="0 0.9"/></feComponentTransfer>
  </filter>
  <filter id="blotch" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.0035" numOctaves="3" seed="${seed + 21}"/>
    <feColorMatrix type="saturate" values="0"/>
  </filter>
  <filter id="soft" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="18"/></filter>
  <filter id="softS" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="6"/></filter>
  <filter id="capShadow" x="-20%" y="-40%" width="140%" height="180%">
    <feGaussianBlur in="SourceAlpha" stdDeviation="7" result="b"/>
    <feFlood flood-color="#000" flood-opacity="0.55"/><feComposite in2="b" operator="in" result="s"/>
    <feMerge><feMergeNode in="s"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <radialGradient id="vignette" cx="50%" cy="50%" r="72%">
    <stop offset="55%" stop-color="#1A1410" stop-opacity="0"/>
    <stop offset="100%" stop-color="#1A1410" stop-opacity="0.55"/>
  </radialGradient>
  <radialGradient id="lamp" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#FFE7A8" stop-opacity="0.9"/>
    <stop offset="100%" stop-color="#FFE7A8" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="beam" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="#FFF2C4" stop-opacity="0.85"/>
    <stop offset="100%" stop-color="#FFF2C4" stop-opacity="0.05"/>
  </linearGradient>
  <pattern id="graph" width="32" height="32" patternUnits="userSpaceOnUse">
    <path d="M32 0H0V32" fill="none" stroke="#B9AE97" stroke-width="1" opacity="0.6"/>
  </pattern>
</defs>`;
}

// ---------- static layers ----------
// A layer is markup that never changes between frames. Without a baker it is drawn inline; the frame
// renderer installs a baker that rasterizes it once and reuses the bitmap, which skips costly filters.
let BAKER = null;
export function setBaker(fn) { BAKER = fn; }
export function layer(key, make, box = { x: 0, y: 0, w: W, h: H }) { return BAKER ? BAKER(key, make, box) : make(); }

// paper grain + vignette on top of everything
export function finish({ vignette = 0.85, grain = 0.10 } = {}) {
  return g(layer('blotch', () => rect(0, 0, W, H, { filter: 'url(#blotch)' })), { opacity: 0.07, style: 'mix-blend-mode:multiply' })
    + g(layer('grain', () => rect(0, 0, W, H, { filter: 'url(#grain)' })), { opacity: grain, style: 'mix-blend-mode:multiply' })
    + rect(0, 0, W, H, { fill: 'url(#vignette)', opacity: vignette });
}

// time-of-day grade: multiply tint over the scene, then optional light pools (screen)
export function grade(kind) {
  const m = {
    day: null,
    dusk: ['#E9A88A', 0.30],
    night: ['#3A4C70', 0.62],
    dark: ['#1D2433', 0.78],
    emergency: ['#7A2A22', 0.45],
  }[kind];
  return m ? rect(0, 0, W, H, { fill: m[0], opacity: m[1], style: 'mix-blend-mode:multiply' }) : '';
}
export const glow = (cx, cy, r, color = '#FFE7A8', op = 0.8) =>
  `<ellipse cx="${cx}" cy="${cy}" rx="${r}" ry="${r * 0.8}" fill="${color}" opacity="${op}" filter="url(#soft)" style="mix-blend-mode:screen"/>`;

// ---------- characters ----------
// Proportions follow the reference: head = 2u tall, body below ~4.2u. (x, y) is the ground point.
function limb(x1, y1, x2, y2, w) { return line(x1, y1, x2, y2, { ...ink(w) }); }
function bent(x1, y1, xm, ym, x2, y2, w) {
  return path(`M${f(x1)} ${f(y1)} Q${f(xm)} ${f(ym)} ${f(x2)} ${f(y2)}`, { fill: 'none', ...ink(w) });
}

const POSES = {
  // arm targets relative to shoulder, leg targets relative to hip, in u
  stand: { la: [-0.8, 1.8], ra: [0.8, 1.8], ll: [-0.42, 2.2], rl: [0.42, 2.2] },
  walk: { la: [-0.9, 1.5], ra: [0.85, 1.55], ll: [-0.85, 2.15], rl: [0.75, 2.15] },
  run: { la: [-1.2, 0.9], ra: [1.1, 1.2], ll: [-1.2, 1.8], rl: [1.1, 2.0], kneeL: [-0.2, 1.3], kneeR: [0.9, 0.9] },
  scared: { la: [-0.9, -0.5], ra: [0.9, -0.5], ll: [-0.5, 2.2], rl: [0.5, 2.2] },
  flashlight: { la: [-0.8, 1.8], ra: [1.45, 0.6], ll: [-0.42, 2.2], rl: [0.42, 2.2] },
  point: { la: [-0.5, 1.75], ra: [1.6, -0.2], ll: [-0.42, 2.2], rl: [0.42, 2.2] },
  crouch: { drop: 0.95, la: [-0.2, 1.2], ra: [1.0, 1.1], ll: [-0.3, 1.25], rl: [0.45, 1.25], kneeL: [0.8, -0.3], kneeR: [1.05, -0.2] },
  reach: { la: [1.4, 0.5], ra: [1.5, 0.8], ll: [-0.42, 2.2], rl: [0.42, 2.2] },
  shush: { la: [-0.55, 1.75], ra: [0.35, -0.85], ll: [-0.42, 2.2], rl: [0.42, 2.2] },
  sneak: { drop: 0.25, la: [-1.05, 1.05], ra: [1.0, 0.95], ll: [-0.55, 2.0], rl: [0.5, 2.0] },
  climb: { la: [-0.7, -1.4], ra: [0.85, -1.0], ll: [-0.4, 2.2], rl: [0.55, 1.3], kneeR: [0.95, 0.6] },
  carry: { la: [-0.45, 0.85], ra: [0.5, 0.85], ll: [-0.6, 2.15], rl: [0.55, 2.15] },
  push: { la: [1.25, 0.8], ra: [1.4, 0.9], ll: [-0.95, 2.1], rl: [0.55, 2.15] },
  throw: { la: [-0.95, 1.3], ra: [1.05, -1.45], ll: [-0.65, 2.2], rl: [0.6, 2.2] },
  sit: { drop: 1.15, la: [-0.85, 1.55], ra: [0.85, 1.55], ll: [-0.75, 1.05], rl: [0.75, 1.05], kneeL: [-0.85, 0.25], kneeR: [0.85, 0.25] },
  radio: { la: [-0.8, 1.8], ra: [0.42, 0.2], ll: [-0.42, 2.2], rl: [0.42, 2.2] },
  talkie: { la: [-0.8, 1.8], ra: [0.98, -0.62], ll: [-0.42, 2.2], rl: [0.42, 2.2] },   // walkie-talkie held up at the cheek
  hips: { la: [-0.98, 1.05], ra: [0.98, 1.05], ll: [-0.5, 2.2], rl: [0.5, 2.2] },
  bang: { la: [-0.55, -1.2], ra: [0.6, -1.25], ll: [-0.42, 2.2], rl: [0.42, 2.2] },
  strideA: { la: [-0.95, 1.5], ra: [0.85, 1.55], ll: [-0.8, 2.15], rl: [0.7, 2.15], kneeL: [-0.35, 1.15], kneeR: [0.45, 1.1] },
  strideB: { la: [0.85, 1.55], ra: [-0.95, 1.5], ll: [0.7, 2.15], rl: [-0.8, 2.15], kneeL: [0.45, 1.1], kneeR: [-0.35, 1.15] },
  runA: { drop: 0.1, la: [-1.2, 0.9], ra: [1.1, 1.2], ll: [-1.2, 1.8], rl: [1.1, 2.0], kneeL: [-0.2, 1.3], kneeR: [0.9, 0.9] },
  runB: { drop: 0.1, la: [1.1, 1.2], ra: [-1.2, 0.9], ll: [1.1, 2.0], rl: [-1.2, 1.8], kneeL: [0.9, 0.9], kneeR: [-0.2, 1.3] },
  extinguisher: { la: [0.9, 0.55], ra: [1.25, 0.15], ll: [-0.45, 2.2], rl: [0.45, 2.2] },
  hug: { la: [-0.5, 1.0], ra: [0.55, 0.95], ll: [-0.42, 2.2], rl: [0.42, 2.2] },
};

// a pose can be a name or a blend { a, b, k } between two named poses, so limbs move instead of snapping
export function poseOf(pose) {
  if (typeof pose === 'string' || !pose) return POSES[pose] || POSES.stand;
  const A = poseOf(pose.a), B = poseOf(pose.b), k = Math.max(0, Math.min(1, pose.k)), o = {};
  for (const key of new Set([...Object.keys(A), ...Object.keys(B)])) {
    const va = A[key] ?? (key === 'drop' ? 0 : key.startsWith('knee') ? null : undefined), vb = B[key] ?? (key === 'drop' ? 0 : key.startsWith('knee') ? null : undefined);
    if (key === 'drop') o.drop = (va || 0) + ((vb || 0) - (va || 0)) * k;
    else if (va && vb) o[key] = [va[0] + (vb[0] - va[0]) * k, va[1] + (vb[1] - va[1]) * k];
    else if (va || vb) {   // a knee only one pose bends: straighten it toward the hip-foot midpoint
      const leg = key === 'kneeL' ? 'll' : 'rl', src = va || vb, mid = [(A[leg][0] + B[leg][0]) / 4, 1.1];
      const kk = va ? k : 1 - k;
      o[key] = [src[0] + (mid[0] - src[0]) * kk, src[1] + (mid[1] - src[1]) * kk];
    }
  }
  return o;
}
// walk / run cycles as continuous blends; phase in radians
// how much of a pose is a run (the head leans forward when running), so blends lean smoothly too
export const runWeight = (pose) => (!pose ? 0 : typeof pose === 'string' ? (pose === 'run' || pose === 'runA' || pose === 'runB' ? 1 : 0)
  : (1 - Math.max(0, Math.min(1, pose.k))) * runWeight(pose.a) + Math.max(0, Math.min(1, pose.k)) * runWeight(pose.b));
export const walkPose = (ph) => ({ a: 'strideA', b: 'strideB', k: 0.5 + 0.5 * Math.sin(ph) });
export const runPose = (ph) => ({ a: 'runA', b: 'runB', k: 0.5 + 0.5 * Math.sin(ph) });

export function face({ cx, cy, u, look = 0, expr = 'neutral', zombie = false, blink = 0, up = 0 }) {
  const ex = cx + look * 0.3 * u, sp = 0.44 * u;
  cy = cy - up * 0.38 * u; const ey = cy;
  let s = '';
  if (zombie) {
    s += ellipse(ex - sp / 2 - 0.02 * u, ey + 0.02 * u, 0.22 * u, 0.25 * u, { fill: PAL.zEye });
    s += ellipse(ex + sp / 2 + 0.03 * u, ey + 0.05 * u, 0.21 * u, 0.23 * u, { fill: PAL.zEye });
    s += circle(ex - sp / 2 + look * 0.06 * u + 0.03 * u, ey + 0.07 * u, 0.07 * u, { fill: PAL.zPupil });
    s += circle(ex + sp / 2 + look * 0.06 * u - 0.02 * u, ey + 0.1 * u, 0.065 * u, { fill: PAL.zPupil });
    s += ellipse(ex + 0.03 * u, cy + 0.55 * u, 0.15 * u, 0.2 * u, { fill: '#2A2522' });
    s += rect(ex - 0.06 * u, cy + 0.38 * u, 0.12 * u, 0.06 * u, { fill: '#E9E4D3' });
    s += path(`M${f(cx - 0.6 * u)} ${f(cy - 0.35 * u)} l${f(0.18 * u)} ${f(0.12 * u)} l${f(0.1 * u)} ${f(-0.06 * u)}`, { fill: 'none', stroke: PAL.zSkinDark, strokeWidth: 3 });
    return s;
  }
  const eyeH = { scared: 0.17, surprised: 0.17, neutral: 0.13, worried: 0.13, determined: 0.1, smile: 0.12, whisper: 0.12 }[expr] ?? 0.13;
  const eo = Math.max(0.08, 1 - blink);
  s += ellipse(ex - sp / 2, ey, 0.105 * u, (eyeH + 0.03) * u * eo, { fill: INK });
  s += ellipse(ex + sp / 2, ey, 0.105 * u, (eyeH + 0.03) * u * eo, { fill: INK });
  if (eo > 0.5) s += circle(ex - sp / 2 + 0.03 * u, ey - 0.06 * u, 0.03 * u, { fill: '#FFF' }) + circle(ex + sp / 2 + 0.03 * u, ey - 0.06 * u, 0.03 * u, { fill: '#FFF' });
  const my = cy + 0.48 * u, mx = ex + look * 0.05 * u;
  const mouth = {
    neutral: line(mx - 0.1 * u, my, mx + 0.1 * u, my, ink(4)),
    smile: path(`M${f(mx - 0.16 * u)} ${f(my - 0.04 * u)} Q${f(mx)} ${f(my + 0.14 * u)} ${f(mx + 0.16 * u)} ${f(my - 0.04 * u)}`, { fill: 'none', ...ink(4) }),
    scared: ellipse(mx, my + 0.02 * u, 0.09 * u, 0.12 * u, { fill: INK }),
    surprised: ellipse(mx, my + 0.02 * u, 0.07 * u, 0.09 * u, { fill: INK }),
    worried: path(`M${f(mx - 0.14 * u)} ${f(my + 0.03 * u)} q${f(0.07 * u)} ${f(-0.07 * u)} ${f(0.14 * u)} 0 t${f(0.14 * u)} 0`, { fill: 'none', ...ink(4) }),
    determined: line(mx - 0.14 * u, my, mx + 0.12 * u, my - 0.02 * u, ink(5)),
    whisper: ellipse(mx, my, 0.05 * u, 0.05 * u, { fill: INK }),
  }[expr] ?? '';
  s += mouth;
  if (expr === 'worried' || expr === 'scared') {
    s += line(ex - sp / 2 - 0.1 * u, ey - 0.3 * u, ex - sp / 2 + 0.06 * u, ey - 0.36 * u, ink(4));
    s += line(ex + sp / 2 - 0.06 * u, ey - 0.36 * u, ex + sp / 2 + 0.1 * u, ey - 0.3 * u, ink(4));
  }
  if (expr === 'determined') {
    s += line(ex - sp / 2 - 0.1 * u, ey - 0.33 * u, ex - sp / 2 + 0.08 * u, ey - 0.25 * u, ink(5));
    s += line(ex + sp / 2 - 0.08 * u, ey - 0.25 * u, ex + sp / 2 + 0.1 * u, ey - 0.33 * u, ink(5));
  }
  if (expr === 'scared') s += path(`M${f(cx + 0.72 * u)} ${f(cy - 0.3 * u)} q${f(0.06 * u)} ${f(0.14 * u)} 0 ${f(0.2 * u)} q${f(-0.06 * u)} ${f(-0.06 * u)} 0 ${f(-0.2 * u)}`, { fill: '#BFE3F2', stroke: INK, strokeWidth: 3 });
  return s;
}

export function body({ x, y, u, pose, torsoFill, torsoDark, legFill = INK, armW, zombie, outfit, facing = 1, hold, aim = -8, back = false, skin }) {
  const P = poseOf(pose);
  const dr = (P.drop || 0) * u;
  const hipY = y - 2.2 * u + dr, shY = y - 4.05 * u + dr, neckY = y - 4.25 * u + dr;
  const lw = armW ?? Math.max(4, 0.1 * u);
  let s = '';
  // legs
  const leg = (side, tgt, knee) => {
    const hx = x + side * 0.24 * u;
    const fx = x + tgt[0] * u * facing, fy = Math.min(y, hipY + tgt[1] * u + (P.drop ? (y - hipY - tgt[1] * u) : 0));
    let o = knee ? bent(hx, hipY, x + knee[0] * u * facing, hipY + knee[1] * u, fx, fy, lw + 1) : limb(hx, hipY, fx, fy, lw + 1);
    o += ellipse(fx + 0.12 * u * facing, fy - 0.04 * u, 0.2 * u, 0.09 * u, { fill: PAL.shoe });
    return o;
  };
  s += leg(-1, P.ll, P.kneeL) + leg(1, P.rl, P.kneeR);
  // torso
  const tw = 0.62 * u, bw = 0.56 * u, top = shY - 0.15 * u, bot = hipY + 0.1 * u;
  const torso = `M${f(x - tw)} ${f(top + 0.2 * u)} Q${f(x - tw)} ${f(top)} ${f(x - tw + 0.25 * u)} ${f(top)} L${f(x + tw - 0.25 * u)} ${f(top)} Q${f(x + tw)} ${f(top)} ${f(x + tw)} ${f(top + 0.2 * u)} L${f(x + bw)} ${f(bot)} L${f(x - bw)} ${f(bot)} Z`;
  // arms behind torso when hanging; drawn after torso for reach/flashlight poses
  const arm = (side, tgt) => {
    const sx = x + side * 0.5 * u, sy = shY + 0.05 * u;
    const hx = x + tgt[0] * u * facing * (side === -1 && tgt[0] > 0 ? 1 : 1), hy = shY + tgt[1] * u;
    const ax = x + (side * 0.5 * u) + (tgt[0] * u * facing - side * 0.5 * u);
    const mx = (sx + ax) / 2 + side * 0.15 * u, my = (sy + hy) / 2 + 0.1 * u;
    let o = bent(sx, sy, mx, my, ax, hy, lw);
    o += circle(ax, hy, 0.15 * u, { fill: skin || (zombie ? PAL.zSkin : PAL.skin), ...ink(4) });
    return { o, hand: [ax, hy] };
  };
  const A1 = arm(-1, P.la), A2 = arm(1, P.ra);
  s += path(torso, { fill: torsoFill, ...ink(6) });
  if (!zombie) {
    s += line(x + 0.05 * u * facing, top + 0.1 * u, x + 0.05 * u * facing, bot - 0.05 * u, { stroke: torsoDark, strokeWidth: 5 });
    s += path(`M${f(x - 0.42 * u)} ${f(bot - 0.55 * u)} h${f(0.3 * u)}`, { stroke: torsoDark, strokeWidth: 4, fill: 'none' });
  } else if (!back) s += outfitDetails({ x, u, top, bot, outfit });
  else s += line(x, top + 0.15 * u, x, bot - 0.1 * u, { stroke: '#00000040', strokeWidth: 3 });
  s += A1.o + A2.o;
  if (hold === 'flashlight') s += flashlight(A2.hand[0], A2.hand[1], 0.95 * u, facing > 0 ? aim : 180 - aim);
  return { s, neckY, dr, hands: [A1.hand, A2.hand] };
}

function outfitDetails({ x, u, top, bot, outfit }) {
  let s = '';
  if (outfit === 'cashier') { // red vest over grey shirt + name tag
    s += path(`M${f(x - 0.55 * u)} ${f(top + 0.15 * u)} L${f(x - 0.18 * u)} ${f(top + 0.1 * u)} L${f(x - 0.12 * u)} ${f(bot)} L${f(x - 0.52 * u)} ${f(bot)} Z`, { fill: PAL.red, ...ink(4) });
    s += path(`M${f(x + 0.55 * u)} ${f(top + 0.15 * u)} L${f(x + 0.18 * u)} ${f(top + 0.1 * u)} L${f(x + 0.12 * u)} ${f(bot)} L${f(x + 0.52 * u)} ${f(bot)} Z`, { fill: PAL.red, ...ink(4) });
    s += rect(x + 0.22 * u, top + 0.45 * u, 0.24 * u, 0.13 * u, { fill: '#F3EEDF', stroke: INK, strokeWidth: 2 });
  } else if (outfit === 'guard') {
    s += rect(x - 0.4 * u, top + 0.3 * u, 0.18 * u, 0.2 * u, { fill: PAL.yellow, stroke: INK, strokeWidth: 2 });
    s += line(x, top + 0.05 * u, x, bot, { stroke: '#1B2433', strokeWidth: 3 });
  } else if (outfit === 'suit') {
    s += poly([[x - 0.12 * u, top + 0.02 * u], [x + 0.12 * u, top + 0.02 * u], [x, top + 0.5 * u]], { fill: '#EDEBE3', stroke: INK, strokeWidth: 3 });
    s += poly([[x - 0.05 * u, top + 0.12 * u], [x + 0.05 * u, top + 0.12 * u], [x + 0.06 * u, top + 0.85 * u], [x, top + 0.95 * u], [x - 0.06 * u, top + 0.85 * u]], { fill: PAL.red, stroke: INK, strokeWidth: 2 });
  } else if (outfit === 'janitor') {
    s += rect(x - 0.38 * u, top + 0.35 * u, 0.76 * u, 0.5 * u, { fill: '#3E7C7B', stroke: INK, strokeWidth: 3, rx: 4 });
  } else if (outfit === 'jogger') {
    s += path(`M${f(x - 0.5 * u)} ${f(top + 0.55 * u)} h${f(u)}`, { stroke: '#FFFFFF', strokeWidth: 5, opacity: 0.8 });
  } else if (outfit === 'pretzel') {   // striped apron with the stand's pretzel badge
    s += rect(x - 0.4 * u, top + 0.3 * u, 0.8 * u, bot - top - 0.3 * u, { fill: '#F3E6C8', stroke: INK, strokeWidth: 3, rx: 4 });
    for (let i = 0; i < 3; i++) s += line(x - 0.4 * u, top + (0.55 + i * 0.35) * u, x + 0.4 * u, top + (0.55 + i * 0.35) * u, { stroke: PAL.red, strokeWidth: 4, opacity: 0.8 });
    s += circle(x, top + 0.5 * u, 0.13 * u, { fill: '#B5652F', stroke: INK, strokeWidth: 2 });
  }
  // tears
  s += path(`M${f(x + 0.2 * u)} ${f(bot)} l${f(0.08 * u)} ${f(-0.22 * u)} l${f(0.08 * u)} ${f(0.22 * u)}`, { fill: PAL.zSkinDark, stroke: INK, strokeWidth: 2 });
  return s;
}

function flashlight(x, y, len, angDeg) {
  const a = (angDeg * Math.PI) / 180, dx = Math.cos(a) * len, dy = Math.sin(a) * len;
  return line(x - dx * 0.2, y - dy * 0.2, x + dx * 0.6, y + dy * 0.6, { stroke: '#2C2C2C', strokeWidth: len * 0.22, strokeLinecap: 'round' })
    + line(x + dx * 0.55, y + dy * 0.55, x + dx * 0.72, y + dy * 0.72, { stroke: '#C9A43A', strokeWidth: len * 0.3, strokeLinecap: 'butt' });
}

export function hero({ x, y, s = 1, pose = 'stand', expr = 'neutral', look = 0, facing = 1, hold, aim = -8, phones = true, blink = 0, tilt = 0, breathe = 0, extra = '', filter = true, back = false }) {
  const u = 60 * s;
  const B = body({ x, y, u, pose, torsoFill: PAL.jacket, torsoDark: PAL.jacketDark, facing, hold, aim });
  const runLean = 0.25 * runWeight(pose);
  const cy = y - 5.25 * u + B.dr, cx = x + runLean * u * facing;
  let h = '';
  // headphones around neck (signature accent)
  if (phones) {
    h += path(`M${f(x - 0.55 * u)} ${f(B.neckY - 0.05 * u)} Q${f(x)} ${f(B.neckY + 0.55 * u)} ${f(x + 0.55 * u)} ${f(B.neckY - 0.05 * u)}`, { fill: 'none', stroke: INK, strokeWidth: 0.2 * u });
    h += path(`M${f(x - 0.55 * u)} ${f(B.neckY - 0.05 * u)} Q${f(x)} ${f(B.neckY + 0.55 * u)} ${f(x + 0.55 * u)} ${f(B.neckY - 0.05 * u)}`, { fill: 'none', stroke: PAL.phones, strokeWidth: 0.11 * u });
    h += rect(x - 0.86 * u, B.neckY - 0.3 * u, 0.36 * u, 0.5 * u, { rx: 0.12 * u, fill: PAL.phones, ...ink(5) });
    h += rect(x + 0.5 * u, B.neckY - 0.3 * u, 0.36 * u, 0.5 * u, { rx: 0.12 * u, fill: PAL.phones, ...ink(5) });
  }
  // head
  h += circle(cx, cy, u, { fill: PAL.skin, ...ink(6) });
  // hair: messy cap of dark hair with a cowlick
  const hx = cx - u, hy = cy;
  h += path(`M${f(hx + 0.02 * u)} ${f(hy - 0.05 * u)} C${f(hx - 0.02 * u)} ${f(hy - 1.1 * u)} ${f(cx + 1.1 * u)} ${f(cy - 1.25 * u)} ${f(cx + 0.98 * u)} ${f(cy - 0.12 * u)}
    L${f(cx + 0.7 * u)} ${f(cy - 0.42 * u)} L${f(cx + 0.48 * u)} ${f(cy - 0.3 * u)} L${f(cx + 0.18 * u)} ${f(cy - 0.5 * u)} L${f(cx - 0.12 * u)} ${f(cy - 0.36 * u)} L${f(cx - 0.45 * u)} ${f(cy - 0.52 * u)} L${f(cx - 0.72 * u)} ${f(cy - 0.32 * u)} Z`, { fill: PAL.hair, ...ink(5) });
  h += path(`M${f(cx + 0.05 * u)} ${f(cy - 0.98 * u)} q${f(0.1 * u)} ${f(-0.35 * u)} ${f(0.38 * u)} ${f(-0.3 * u)}`, { fill: 'none', stroke: PAL.hair, strokeWidth: 0.12 * u, strokeLinecap: 'round' });
  h += path(`M${f(cx + 0.05 * u)} ${f(cy - 0.98 * u)} q${f(0.1 * u)} ${f(-0.35 * u)} ${f(0.38 * u)} ${f(-0.3 * u)}`, { fill: 'none', stroke: INK, strokeWidth: 3 });
  if (back) {
    h += ellipse(cx - 0.98 * u, cy + 0.08 * u, 0.16 * u, 0.24 * u, { fill: PAL.skin, ...ink(4) }) + ellipse(cx + 0.98 * u, cy + 0.08 * u, 0.16 * u, 0.24 * u, { fill: PAL.skin, ...ink(4) });
    h += path(`M${f(cx - 0.97 * u)} ${f(cy + 0.25 * u)} C${f(cx - 1.1 * u)} ${f(cy - 1.2 * u)} ${f(cx + 1.1 * u)} ${f(cy - 1.2 * u)} ${f(cx + 0.97 * u)} ${f(cy + 0.25 * u)} Q${f(cx + 0.6 * u)} ${f(cy + 0.75 * u)} ${f(cx)} ${f(cy + 0.72 * u)} Q${f(cx - 0.6 * u)} ${f(cy + 0.75 * u)} ${f(cx - 0.97 * u)} ${f(cy + 0.25 * u)} Z`, { fill: PAL.hair, ...ink(5) });
    h += path(`M${f(cx - 0.3 * u)} ${f(cy - 0.5 * u)} q${f(0.2 * u)} ${f(0.35 * u)} ${f(0.05 * u)} ${f(0.7 * u)} M${f(cx + 0.35 * u)} ${f(cy - 0.4 * u)} q${f(-0.1 * u)} ${f(0.3 * u)} ${f(0.08 * u)} ${f(0.6 * u)}`, { fill: 'none', stroke: '#2A1E18', strokeWidth: 4 });
  } else h += face({ cx, cy, u, look: look || facing * 0.25, expr, blink });
  if (pose === 'shush') h += line(cx + 0.05 * u, cy + 0.35 * u, cx + 0.05 * u, cy + 0.7 * u, ink(0.1 * u));
  const head = tilt ? g(h, { transform: `rotate(${tilt} ${f(cx)} ${f(cy + u)})` }) : h;
  const bodyT = breathe ? `translate(${f(x)} ${f(y)}) scale(1 ${f(1 + breathe)}) translate(${f(-x)} ${f(-y)})` : undefined;
  return g(B.s + head + extra, { filter: filter ? 'url(#wobbleSoft)' : undefined, transform: bodyT });
}

export function zombie({ x, y, s = 1, outfit = 'cashier', pose = 'stand', tilt = -8, look = 0, facing = 1, dim = 0, sway = 0, extra = '', back = false, filter = true, up = 0 }) {
  const u = 60 * s;
  const fills = { cashier: '#8C8C86', guard: '#2E3D55', suit: '#3B3F48', janitor: '#5E6E70', jogger: '#C76A83', shopper: '#7C6A8E', park: '#8A7A4E', nurse: '#6FA3A6', pretzel: '#C4473A' };
  const B = body({ x, y, u, pose, torsoFill: fills[outfit] || '#777', torsoDark: '#333', zombie: true, outfit, facing, back });
  const cx = x + 0.1 * u * facing, cy = y - 5.15 * u + B.dr;
  let h = circle(cx, cy, u, { fill: PAL.zSkin, ...ink(6) });
  h += path(`M${f(cx - 0.9 * u)} ${f(cy - 0.4 * u)} Q${f(cx - 0.2 * u)} ${f(cy - 1.15 * u)} ${f(cx + 0.85 * u)} ${f(cy - 0.5 * u)}`, { fill: 'none', stroke: PAL.zSkinDark, strokeWidth: 0.18 * u, opacity: 0.6 });
  if (outfit === 'guard') h += path(`M${f(cx - 0.95 * u)} ${f(cy - 0.45 * u)} Q${f(cx)} ${f(cy - 1.35 * u)} ${f(cx + 0.95 * u)} ${f(cy - 0.45 * u)} Z M${f(cx - 0.2 * u)} ${f(cy - 0.5 * u)} h${f(1.4 * u)}`, { fill: '#1B2433', ...ink(5) });
  if (outfit === 'jogger') h += rect(cx - 0.98 * u, cy - 0.55 * u, 1.96 * u, 0.22 * u, { fill: '#F2F0EA', ...ink(4), rx: 6 });
  if (outfit === 'pretzel') h += path(`M${f(cx - 0.75 * u)} ${f(cy - 0.62 * u)} L${f(cx - 0.6 * u)} ${f(cy - 1.25 * u)} L${f(cx + 0.65 * u)} ${f(cy - 1.25 * u)} L${f(cx + 0.8 * u)} ${f(cy - 0.62 * u)} Z`, { fill: '#F7F2E6', ...ink(4) })
    + path(`M${f(cx - 0.7 * u)} ${f(cy - 0.82 * u)} h${f(1.45 * u)}`, { stroke: PAL.red, strokeWidth: 0.1 * u });
  if (outfit === 'janitor') h += path(`M${f(cx - 0.9 * u)} ${f(cy - 0.45 * u)} Q${f(cx)} ${f(cy - 1.3 * u)} ${f(cx + 0.9 * u)} ${f(cy - 0.45 * u)} Z`, { fill: '#3E7C7B', ...ink(5) });
  if (back) h += path(`M${f(cx - 0.95 * u)} ${f(cy - 0.1 * u)} Q${f(cx)} ${f(cy - 1.3 * u)} ${f(cx + 0.95 * u)} ${f(cy - 0.1 * u)} Q${f(cx)} ${f(cy + 0.25 * u)} ${f(cx - 0.95 * u)} ${f(cy - 0.1 * u)} Z`, { fill: '#5B5F55', opacity: 0.55 })
    + ellipse(cx - 0.98 * u, cy + 0.05 * u, 0.14 * u, 0.24 * u, { fill: PAL.zSkin, ...ink(4) }) + ellipse(cx + 0.98 * u, cy + 0.05 * u, 0.14 * u, 0.24 * u, { fill: PAL.zSkin, ...ink(4) });
  else h += face({ cx, cy, u, look, zombie: true, up });
  const inner = g(B.s + extra + g(h, { transform: `rotate(${tilt} ${f(cx)} ${f(cy + u)})` }));
  return g(inner + (dim ? g(inner, { opacity: dim, style: 'mix-blend-mode:multiply' }) : ''), { filter: filter ? 'url(#wobbleSoft)' : undefined, transform: sway ? `rotate(${f(sway)} ${f(x)} ${f(y)})` : undefined });
}

// distant crowd: simplified figures, back rows smaller
export function crowd({ x0, x1, y, rows = 3, n = 20, s = 0.35, seed = 1, spread = 60, arms = false, t = 0, lean = 0 }) {
  const r = rng(seed), cols = ['#8C8C86', '#2E3D55', '#3B3F48', '#C76A83', '#7C6A8E', '#8A7A4E', '#6FA3A6', '#A65F4A', '#596471'];
  let out = '';
  for (let row = rows - 1; row >= 0; row--) {
    const sc = s * (1 - row * 0.16), yy = y - row * spread * s * 3;
    for (let i = 0; i < n; i++) {
      const xx = x0 + (x1 - x0) * (i + r() * 0.8) / n, u = 60 * sc * (0.9 + r() * 0.2);
      const ph = r() * 6.28, c = cols[Math.floor(r() * cols.length)], tilt = (r() - 0.5) * 24 + 5 * Math.sin(t * (0.6 + 0.5 * ((i * 7) % 5) / 5) + ph);
      const bodySway = 2.5 * Math.sin(t * 0.7 + ph) + lean;
      let fig = line(xx - 0.25 * u, yy - 2.2 * u, xx - 0.35 * u, yy, ink(Math.max(3, 0.12 * u)))
        + line(xx + 0.25 * u, yy - 2.2 * u, xx + 0.35 * u, yy, ink(Math.max(3, 0.12 * u)))
        + rect(xx - 0.6 * u, yy - 4.2 * u, 1.2 * u, 2.1 * u, { rx: 0.25 * u, fill: c, ...ink(Math.max(3, 0.1 * u)) });
      if (arms) fig += line(xx + 0.5 * u, yy - 3.9 * u, xx + 1.4 * u, yy - 3.7 * u, ink(Math.max(3, 0.1 * u)));
      fig += g(circle(xx, yy - 5.15 * u, u, { fill: PAL.zSkin, ...ink(Math.max(3, 0.1 * u)) })
        + circle(xx - 0.3 * u, yy - 5.15 * u, 0.17 * u, { fill: PAL.zEye }) + circle(xx + 0.3 * u, yy - 5.12 * u, 0.16 * u, { fill: PAL.zEye }), { transform: `rotate(${f(tilt)} ${f(xx)} ${f(yy - 4.2 * u)})` });
      out += g(fig, { transform: `rotate(${f(bodySway)} ${f(xx)} ${f(yy)})` });
    }
  }
  return g(out, { filter: 'url(#wobbleSoft)' });
}

// ---------- captions & HUD ----------
export function caption(word, { dialogue = false, y = 870, size = 92, color } = {}) {
  const fill = color || (dialogue ? '#F2A73B' : '#FFFFFF');
  return g(text(W / 2, y, word.toUpperCase(), {
    fontFamily: 'Bangers, Impact, sans-serif', fontSize: size, letterSpacing: 2, textAnchor: 'middle',
    fill, stroke: '#2B1D21', strokeWidth: 9, paintOrder: 'stroke', transform: dialogue ? `skewX(-10)` : undefined,
    style: dialogue ? `transform-origin:${W / 2}px ${y}px` : undefined,
  }), { filter: 'url(#capShadow)' });
}
export function soundCaption(s, { y = 1000 } = {}) {
  return text(W / 2, y, `[${s}]`, { fontFamily: 'Rubik, sans-serif', fontStyle: 'italic', fontWeight: 500, fontSize: 34, fill: '#E8E1D2', textAnchor: 'middle', opacity: 0.9, letterSpacing: 1 });
}

// noise meter: n of 5 bars lit
function noiseBars(x, y, n, h = 34) {
  let s = '';
  for (let i = 0; i < 5; i++) {
    const bh = h * (0.4 + i * 0.15), on = i < n;
    s += rect(x + i * 15, y + h - bh, 10, bh, { rx: 2, fill: on ? (i >= 3 ? '#D65632' : '#E9B93E') : '#00000025', stroke: INK, strokeWidth: 2 });
  }
  return s;
}
// themed HUD: 'price' (supermarket shelf tag), 'mall' (YOU ARE HERE sticker), 'park' (wooden sign)
export function hud({ theme = 'price', day = 1, time = '4:12 PM', noise = 2, place = '' } = {}) {
  const x = 36, y = 30;
  let s = '';
  if (theme === 'price') {
    s += rect(x, y, 430, 96, { rx: 6, fill: '#FBF6EA', ...ink(4) });
    s += rect(x, y, 430, 26, { rx: 6, fill: PAL.yellow, ...ink(4) });
    s += text(x + 14, y + 19, (place || 'FRESHWAY · AISLE 7').toUpperCase(), { fontFamily: 'Rubik', fontWeight: 800, fontSize: 15, letterSpacing: 2, fill: INK });
    s += text(x + 16, y + 82, `DAY ${day}`, { fontFamily: 'Patrick Hand, Rubik', fontSize: 50, fill: INK });
    s += line(x + 175, y + 36, x + 175, y + 88, { stroke: INK, strokeWidth: 2 });
    s += text(x + 190, y + 47, 'NOISE', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 12, letterSpacing: 2, fill: '#6B5F55' });
    s += noiseBars(x + 190, y + 52, noise, 32);
    for (let i = 0; i < 16; i++) s += rect(x + 300 + i * 7, y + 40, (i % 3 === 0 ? 4 : 2), 44, { fill: INK });
    s += text(x + 300, y + 93, 'x0.00', { fontFamily: 'Rubik', fontWeight: 700, fontSize: 11, fill: '#6B5F55' });
  } else if (theme === 'mall') {
    s += circle(x + 52, y + 52, 50, { fill: PAL.red, ...ink(4) });
    s += text(x + 52, y + 46, 'YOU ARE', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 15, fill: '#FFF', textAnchor: 'middle' });
    s += text(x + 52, y + 66, 'HERE', { fontFamily: 'Rubik', fontWeight: 900, fontSize: 20, fill: '#FFF', textAnchor: 'middle' });
    s += rect(x + 112, y + 10, 330, 84, { rx: 10, fill: '#FBF6EA', ...ink(4) });
    s += text(x + 128, y + 33, (place || 'RIVERSIDE MALL · LEVEL 2').toUpperCase(), { fontFamily: 'Rubik', fontWeight: 800, fontSize: 13, letterSpacing: 2, fill: '#6B5F55' });
    s += text(x + 128, y + 80, `DAY ${day}`, { fontFamily: 'Patrick Hand, Rubik', fontSize: 46, fill: INK });
    s += text(x + 268, y + 62, 'NOISE', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 12, letterSpacing: 2, fill: '#6B5F55' });
    s += noiseBars(x + 340, y + 50, noise, 30);
  } else if (theme === 'park') {
    s += line(x + 40, y + 96, x + 40, y + 122, { stroke: '#5C4430', strokeWidth: 10 });
    s += path(`M${x} ${y + 8} h380 l24 44 l-24 44 h-380 z`, { fill: '#5E7A46', ...ink(4) });
    s += text(x + 18, y + 34, (place || 'ELM HOLLOW PARK').toUpperCase(), { fontFamily: 'Rubik', fontWeight: 800, fontSize: 15, letterSpacing: 2, fill: '#F2EBD3' });
    s += text(x + 18, y + 84, `DAY ${day}`, { fontFamily: 'Patrick Hand, Rubik', fontSize: 46, fill: '#FBF6EA' });
    s += text(x + 210, y + 46, 'NOISE', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 12, letterSpacing: 2, fill: '#F2EBD3' });
    s += noiseBars(x + 210, y + 52, noise, 32);
  }
  s += rect(x + (theme === 'mall' ? 455 : 446), y + (theme === 'mall' ? 30 : 30), 128, 44, { rx: 8, fill: '#2B1D21' });
  s += text(x + (theme === 'mall' ? 519 : 510), y + (theme === 'mall' ? 60 : 60), time, { fontFamily: 'Rubik', fontWeight: 700, fontSize: 22, fill: '#F3EBDD', textAnchor: 'middle' });
  return g(s, { filter: 'url(#wobbleSoft)' });
}
export function watermark() {
  return g(text(W - 120, H - 34, 'LAST LIGHT', { fontFamily: 'Rubik', fontWeight: 800, fontSize: 22, letterSpacing: 6, fill: '#FFFFFF', opacity: 0.55, textAnchor: 'end' })
    + circle(W - 80, H - 42, 24, { fill: '#F5E6CC', opacity: 0.7, ...ink(3) }) + rect(W - 96, H - 50, 32, 12, { rx: 5, fill: PAL.phones, opacity: 0.9 }));
}

// ---------- perspective helper for one-point interiors ----------
export function persp(vp, far) {
  return (x, y, z) => [vp[0] + (x - vp[0]) * (1 - (1 - far) * z), vp[1] + (y - vp[1]) * (1 - (1 - far) * z)];
}
