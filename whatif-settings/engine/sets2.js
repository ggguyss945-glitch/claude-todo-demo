// New sets for the hook of "What If Real Life Had a SETTINGS MENU?" (S00): the upstairs HALLWAY at 2:13 a.m. (Dad in
// pyjamas, sun pouring out of Sam's door) and SPACE (snap zoom out: one side of Earth glowing like a lamp).
// Same contract and finish as sets.js: { w, h, layers: [{ name, depth, svg }], svg }, layers[0] = shared defs, static
// layers carry no per-frame params; per-frame pieces are exported functions returning insert layers
// [{ name, after, depth, svg }] that drop straight into cam.set(set, { insert }).
import { W, H, FONT, Defs, f, clamp, lerp, seg, ease, rng, shade, mix, ink, g, rect, circle, ellipse, line, poly, path, text, st, rrPath, gearPath, starPts, contact, esc } from './ui_style.js';
import { compose, pbox, blob, twinkle, X0, X1, SW } from './sets.js';

const SWM = 3.0, SWN = 4.0;
function finish(d, layers, o = {}) {
  const all = [{ name: 'defs', depth: 0, svg: String(d) }, ...layers];
  return { w: W, h: H, layers: all, svg: compose(all, o.cam) };
}
const P = (pts) => pts.map((q, i) => (i ? 'L' : 'M') + f(q[0]) + ' ' + f(q[1])).join('') + 'Z';

// ======================================================================================
// HALLWAY (one-point perspective down the upstairs hall to Sam's door)
// ======================================================================================
// World units: X across (walls at -1 / +1), Y down (floor +1, ceiling -1.25), Z away from the lens (Sam's door wall at
// Z 4.2). hallPt([X, Y, Z]) -> screen px; hallUnit(Z) = px per unit at that depth (scale actors with it).
const VP = [960, 480], FL = 1080, ZEND = 4.2, YF = 1, YC = -1.25;
export const hallPt = ([X, Y, Z]) => [VP[0] + (FL * X) / Z, VP[1] + (FL * Y) / Z];
export const hallUnit = (Z) => FL / Z;
const quad = (pts3) => P(pts3.map(hallPt));
// HALL anchors. dad: feet + scale for toon('dad', {outfit: 'pyjamas'}) (1.55 units tall at Z 2.9, left of the runner,
// facing 'tq-right' toward the light); door: Sam's doorway on the end wall (screen box) and gap = the bright slit
// the sun pours out of; light: the light switch (left wall), frames: picture-frame centres.
export const HALL = {
  vp: VP, zEnd: ZEND,
  dad: { x: 755, y: 852, s: 1.7, Z: 2.9 },
  door: { x: 844, y: 287, w: 232, h: 450 },
  gap: { x: 1040, y: 520 },
  switch: { x: 523, y: 462 },
};

const HC = { wallL: '#55489A', wallR: '#4A3F8A', end: '#5E52A6', wain: '#3A4890', ceil: '#3C346E', floor: '#3A3468', trim: '#7383CF', rug: '#B04A86', rugB: '#FFC23D', door: '#6A58B4' };

/** a picture frame on a side wall (X = +-1), from Z0 to Z1, Y0..Y1, with simple drawn content */
function wallFrame(d, side, Z0, Z1, Y0, Y1, kind, col) {
  const X = side;
  const outer = [[X, Y0, Z0], [X, Y0, Z1], [X, Y1, Z1], [X, Y1, Z0]];
  const m = 0.06, inner = [[X, Y0 + m, Z0 + m * 1.2 * (side > 0 ? 1 : 1)], [X, Y0 + m, Z1 - m], [X, Y1 - m, Z1 - m], [X, Y1 - m, Z0 + m * 1.2]];
  let s = path(quad(outer), { fill: d.lin([shade(col, 0.06), shade(col, -0.06)]), stroke: ink(col), strokeWidth: SWM, strokeLinejoin: 'round' });
  const ip = quad(inner);
  const clip = d.clip(path(ip));
  // content in a local box mapped by an affine fit of the inner quad (vertical edges stay vertical on a side wall)
  const [a, b, c] = [hallPt(inner[0]), hallPt(inner[1]), hallPt(inner[3])];
  const M = `matrix(${f((b[0] - a[0]) / 100 * 1000) / 1000} ${f((b[1] - a[1]) / 100 * 1000) / 1000} ${f((c[0] - a[0]) / 100 * 1000) / 1000} ${f((c[1] - a[1]) / 100 * 1000) / 1000} ${f(a[0])} ${f(a[1])})`;
  let art = rect(-10, -10, 120, 120, { fill: kind === 'sun' ? '#FFF3C8' : kind === 'cat' ? '#E8ECFF' : '#BFE6FF' });
  if (kind === 'house') art += rect(0, 70, 100, 40, { fill: '#7CD06A' }) + rect(26, 40, 48, 36, { fill: '#FFE08F' }) + poly([[20, 42], [50, 18], [80, 42]], { fill: '#F0645A' }) + rect(44, 56, 12, 20, { fill: '#2FA3A0' });
  if (kind === 'sun') { art += circle(50, 50, 22, { fill: '#FFC93A' }); for (let i = 0; i < 8; i++) { const an = i * Math.PI / 4; art += line(50 + Math.cos(an) * 30, 50 + Math.sin(an) * 30, 50 + Math.cos(an) * 40, 50 + Math.sin(an) * 40, st('#FFB43D', 6)); } }
  if (kind === 'cat') art += ellipse(50, 70, 30, 24, { fill: '#8A8FA8' }) + circle(50, 40, 20, { fill: '#8A8FA8' }) + poly([[33, 30], [36, 12], [46, 24]], { fill: '#8A8FA8' }) + poly([[67, 30], [64, 12], [54, 24]], { fill: '#8A8FA8' }) + path('M40 40h6M54 40h6', st('#2A2346', 3));
  s += g(g(art, { transform: M }), { clipPath: clip });
  s += path(ip, { fill: 'none', stroke: shade(col, -0.12), strokeWidth: 2 });
  return s;
}

/** Sam's door on the end wall: frame, KEEP OUT sign, swung open by `open` (0 shut .. 1 wide) into his room */
function endDoor(d, open) {
  const x0 = -0.45, x1 = 0.45, yT = -0.75, Z = ZEND;
  let s = '';
  // trim
  s += path(quad([[x0 - 0.08, yT - 0.08, Z], [x1 + 0.08, yT - 0.08, Z], [x1 + 0.08, YF, Z], [x0 - 0.08, YF, Z]]), { fill: d.lin(['#8D9BE0', '#6070C0']), stroke: ink('#6070C0'), strokeWidth: SWM, strokeLinejoin: 'round' });
  // the doorway (Sam's room beyond: dark at night; the sun layer lights it)
  s += path(quad([[x0, yT, Z], [x1, yT, Z], [x1, YF, Z], [x0, YF, Z]]), { fill: d.lin(['#20204E', '#2E2A62']) });
  // door panel hinged on the left jamb, swinging away from us
  const th = open * 1.25, w = x1 - x0, ex = x0 + w * Math.cos(th), ez = Z + w * Math.sin(th);
  const panel = [[x0, yT, Z], [ex, yT, ez], [ex, YF, ez], [x0, YF, Z]];
  s += path(quad(panel), { fill: d.lin([shade(HC.door, 0.06), shade(HC.door, -0.06)], 'h'), stroke: ink(HC.door), strokeWidth: SWM, strokeLinejoin: 'round' });
  const pp = (u, v) => { const X = lerp(x0, ex, u), Zz = lerp(Z, ez, u), Y = lerp(yT, YF, v); return [X, Y, Zz]; };
  s += path(quad([pp(0.14, 0.08), pp(0.86, 0.08), pp(0.86, 0.42), pp(0.14, 0.42)]), { fill: 'none', stroke: shade(HC.door, -0.1), strokeWidth: 3 });
  s += path(quad([pp(0.14, 0.52), pp(0.86, 0.52), pp(0.86, 0.92), pp(0.14, 0.92)]), { fill: 'none', stroke: shade(HC.door, -0.1), strokeWidth: 3 });
  // KEEP OUT sign + a gear sticker on the panel
  const sa = hallPt(pp(0.16, 0.18)), sb = hallPt(pp(0.84, 0.18)), sc = hallPt(pp(0.16, 0.32));
  const M = `matrix(${f((sb[0] - sa[0]) / 100 * 1000) / 1000} ${f((sb[1] - sa[1]) / 100 * 1000) / 1000} 0 ${f((sc[1] - sa[1]) / 40 * 1000) / 1000} ${f(sa[0])} ${f(sa[1])})`;
  s += g(path(rrPath(0, 0, 100, 40, 8), { fill: '#FFD43B', stroke: '#8A5A10', strokeWidth: 2.5 }) + text(50, 17, "SAM'S ROOM", { fontFamily: FONT.ui, fontWeight: 900, fontSize: 13, fill: '#3A2E10', textAnchor: 'middle' }) + text(50, 34, 'KEEP OUT', { fontFamily: FONT.title, fontSize: 15, fill: '#E5303D', textAnchor: 'middle' }), { transform: M });
  const gc = hallPt(pp(0.5, 0.62));
  s += path(gearPath(gc[0], gc[1], 15 * Math.cos(th) + 4, 11 * Math.cos(th) + 3, 8, 0, 0.5), { fill: '#FF7A3D', stroke: ink('#FF7A3D'), strokeWidth: 1.5 }) + circle(gc[0], gc[1], 4, { fill: '#FFFFFF' });
  const kn = hallPt(pp(0.86, 0.56));
  s += circle(kn[0], kn[1], 6, { fill: d.lin(['#FFE48A', '#E0A520']), stroke: '#8A5A10', strokeWidth: 1.5 });
  return { svg: s, gapX: [hallPt([ex, 0, ez])[0], hallPt([x1, 0, Z])[0]] };
}

/** Hallway. o: { sun 0..1 (bakes hallwaySun into the layers for stills), door: Sam's door open 0..1 (default 0.22),
 *  cam }. Layers: far (end wall + Sam's door), mid (side walls, ceiling, floor, runner, frames, Dad's door, switch),
 *  light (night light pools, screen, live), near (foreground plant), grade (night vignette). Insert Dad after 'mid'. */
export function hallway(o = {}) {
  const d = new Defs();
  const open = o.door ?? 0.22;
  const Zn = 0.5; // near clipping depth for the side walls
  // --- far: end wall
  let far = '';
  far += path(quad([[-1, YC, ZEND], [1, YC, ZEND], [1, YF, ZEND], [-1, YF, ZEND]]), { fill: d.lin([shade(HC.end, 0.03), shade(HC.end, -0.04)]) });
  far += path(quad([[-1, 0.25, ZEND], [1, 0.25, ZEND], [1, YF, ZEND], [-1, YF, ZEND]]), { fill: d.lin([HC.wain, shade(HC.wain, -0.04)]) });
  far += path(quad([[-1, 0.2, ZEND], [1, 0.2, ZEND], [1, 0.27, ZEND], [-1, 0.27, ZEND]]), { fill: HC.trim });
  const door = endDoor(d, open);
  far += door.svg;
  // --- mid: ceiling, walls, floor, runner, doors, frames, switch
  let mid = '';
  // ceiling
  mid += path(quad([[-1, YC, Zn], [1, YC, Zn], [1, YC, ZEND], [-1, YC, ZEND]]), { fill: d.lin([shade(HC.ceil, -0.05), shade(HC.ceil, 0.03)], [0, 0, 0, 1]) });
  for (const Z of [1.2, 1.6, 2.1, 2.7, 3.4]) mid += path(quad([[-1, YC, Z], [1, YC, Z], [1, YC, Z + 0.04], [-1, YC, Z + 0.04]]), { fill: shade(HC.ceil, -0.06), opacity: 0.6 });
  // ceiling light (off at night)
  { const c = hallPt([0, YC, 2.9]); mid += ellipse(c[0], c[1] + 6, 70, 14, { fill: d.lin(['#E8ECFF', '#B9C2EC']), stroke: ink('#B9C2EC'), strokeWidth: SWM }) + ellipse(c[0] - 10, c[1] + 2, 36, 4, { fill: '#FFFFFF', opacity: 0.5 }); }
  // side walls
  for (const side of [-1, 1]) {
    const col = side < 0 ? HC.wallL : HC.wallR;
    mid += path(quad([[side, YC, Zn], [side, YC, ZEND], [side, YF, ZEND], [side, YF, Zn]]), { fill: d.lin(side < 0 ? [shade(col, 0.04), shade(col, -0.03)] : [shade(col, -0.03), shade(col, 0.03)], 'h') });
    // soft vertical wallpaper stripes (spacing shrinks with depth)
    for (let Z = 0.7; Z < ZEND - 0.05; Z += 0.22) mid += path(quad([[side, YC, Z], [side, YC, Z + 0.08], [side, 0.2, Z + 0.08], [side, 0.2, Z]]), { fill: shade(col, 0.025), opacity: 0.8 });
    // wainscot + chair rail + baseboard + crown moulding
    mid += path(quad([[side, 0.25, Zn], [side, 0.25, ZEND], [side, YF, ZEND], [side, YF, Zn]]), { fill: d.lin([HC.wain, shade(HC.wain, -0.05)], 'v') });
    for (let Z = 0.8; Z < ZEND; Z += 0.36) mid += path(quad([[side, 0.33, Z], [side, 0.33, Z + 0.26], [side, 0.9, Z + 0.26], [side, 0.9, Z]]), { fill: 'none', stroke: shade(HC.wain, -0.08), strokeWidth: 2.5 });
    mid += path(quad([[side, 0.19, Zn], [side, 0.19, ZEND], [side, 0.27, ZEND], [side, 0.27, Zn]]), { fill: d.lin([shade(HC.trim, 0.06), shade(HC.trim, -0.04)]), stroke: ink(HC.trim), strokeWidth: 2 });
    mid += path(quad([[side, 0.92, Zn], [side, 0.92, ZEND], [side, YF, ZEND], [side, YF, Zn]]), { fill: shade(HC.trim, -0.04), stroke: ink(HC.trim), strokeWidth: 2 });
    mid += path(quad([[side, YC, Zn], [side, YC, ZEND], [side, YC + 0.1, ZEND], [side, YC + 0.1, Zn]]), { fill: shade(HC.trim, 0.04), stroke: ink(HC.trim), strokeWidth: 2 });
  }
  // wall edges (tinted lines where the planes meet)
  for (const [a, b] of [[[-1, YC, ZEND], [-1, YF, ZEND]], [[1, YC, ZEND], [1, YF, ZEND]]]) { const A = hallPt(a), B = hallPt(b); mid += line(A[0], A[1], B[0], B[1], { stroke: ink(HC.end), strokeWidth: SWM }); }
  // floor: planks converging to the vanishing point + seams
  mid += path(quad([[-1, YF, Zn], [1, YF, Zn], [1, YF, ZEND], [-1, YF, ZEND]]), { fill: d.lin([shade(HC.floor, 0.0), shade(HC.floor, -0.05)], [0, 1, 0, 0]) });
  for (let X = -1; X <= 1.001; X += 0.2) { const A = hallPt([X, YF, ZEND]), B = hallPt([X, YF, Zn]); mid += line(A[0], A[1], B[0], B[1], { stroke: '#221E44', strokeWidth: 2.5, opacity: 0.6 }); }
  for (const Z of [0.9, 1.15, 1.45, 1.8, 2.25, 2.8, 3.45]) { const k = Math.round(Z * 10) % 2; for (let X = -1 + k * 0.2; X < 1; X += 0.4) mid += path(quad([[X, YF, Z], [X + 0.2, YF, Z], [X + 0.2, YF, Z + 0.015], [X, YF, Z + 0.015]]), { fill: '#221E44', opacity: 0.5 }); }
  // runner rug with a gold border and gear motifs
  const rz0 = 1.25, rz1 = 3.95, rx = 0.56;
  mid += path(quad([[-rx, YF, rz0], [rx, YF, rz0], [rx, YF, rz1], [-rx, YF, rz1]]), { fill: d.lin([shade(HC.rug, -0.06), shade(HC.rug, 0.03)], [0, 1, 0, 0]), stroke: ink(HC.rug), strokeWidth: SWM, strokeLinejoin: 'round' });
  for (const sx of [-1, 1]) mid += path(quad([[sx * (rx - 0.1), YF, rz0 + 0.08], [sx * (rx - 0.05), YF, rz0 + 0.08], [sx * (rx - 0.05), YF, rz1 - 0.06], [sx * (rx - 0.1), YF, rz1 - 0.06]]), { fill: HC.rugB, opacity: 0.85 });
  for (const Z of [1.55, 2.0, 2.55, 3.2]) { const c = hallPt([0, YF, Z]), u = hallUnit(Z); mid += g(path(gearPath(0, 0, 0.13 * u, 0.095 * u, 8, 0, 0.5), { fill: HC.rugB, opacity: 0.8 }) + circle(0, 0, 0.04 * u, { fill: HC.rug }), { transform: `translate(${f(c[0])} ${f(c[1])}) scale(1 ${f(0.28 * 1000) / 1000})` }); }
  // Dad's bedroom door (left wall, open, dark inside) and the bathroom door (right wall, shut)
  const sideDoor = (side, Z0, Z1, openK, col) => {
    let s = path(quad([[side, -0.83, Z0 - 0.06], [side, -0.83, Z1 + 0.06], [side, YF, Z1 + 0.06], [side, YF, Z0 - 0.06]]), { fill: d.lin(['#8D9BE0', '#6070C0']), stroke: ink('#6070C0'), strokeWidth: SWM, strokeLinejoin: 'round' });
    s += path(quad([[side, -0.75, Z0], [side, -0.75, Z1], [side, YF, Z1], [side, YF, Z0]]), { fill: openK ? '#1A1840' : d.lin([shade(col, 0.05), shade(col, -0.05)]), stroke: ink(col), strokeWidth: 2 });
    if (openK) {
      // opened inward: the dark room beyond, the leaf standing against the far side of the opening
      s += path(quad([[side, -0.75, Z0], [side, -0.75, Z1], [side, YF, Z1], [side, YF, Z0]]), { fill: d.lin(['#14123A', '#24205A'], 'h') });
      const lz = lerp(Z0, Z1, 0.55);
      s += g(path(quad([[side, -0.75, lz], [side * 1.32, -0.75, Z1 - 0.02], [side * 1.32, YF, Z1 - 0.02], [side, YF, lz]]), { fill: d.lin([shade(col, -0.02), shade(col, -0.1)], 'h'), stroke: ink(col), strokeWidth: 2, strokeLinejoin: 'round' }), { clipPath: d.clip(path(quad([[side, -0.75, Z0], [side, -0.75, Z1], [side, YF, Z1], [side, YF, Z0]]))) });
    } else {
      const k = hallPt([side, 0.05, Z1 - 0.1]);
      s += circle(k[0], k[1], 6, { fill: d.lin(['#FFE48A', '#E0A520']), stroke: '#8A5A10', strokeWidth: 1.5 });
      s += path(quad([[side, -0.6, Z0 + 0.08], [side, -0.6, Z1 - 0.08], [side, -0.1, Z1 - 0.08], [side, -0.1, Z0 + 0.08]]), { fill: 'none', stroke: shade(col, -0.1), strokeWidth: 2.5 });
    }
    return s;
  };
  mid += sideDoor(-1, 2.15, 2.75, 1, '#6A58B4');
  mid += sideDoor(1, 3.05, 3.6, 0, '#5C6BB4');
  // picture frames (family photos) and the light switch
  mid += wallFrame(d, 1, 1.5, 2.0, -0.78, -0.18, 'house', '#FFC23D');
  mid += wallFrame(d, 1, 2.25, 2.7, -0.7, -0.25, 'cat', '#FF7A3D');
  mid += wallFrame(d, -1, 3.0, 3.5, -0.75, -0.25, 'sun', '#3FBF8A');
  mid += wallFrame(d, -1, 1.2, 1.75, -0.85, -0.2, 'house', '#9A7AC8');
  mid += path(quad([[-1, -0.12, 2.0], [-1, -0.12, 2.08], [-1, 0.04, 2.08], [-1, 0.04, 2.0]]), { fill: d.lin(['#F4F6FF', '#C8CEE8']), stroke: ink('#C8CEE8'), strokeWidth: 2 });
  { const a = hallPt([-1, -0.07, 2.04]), b = hallPt([-1, -0.01, 2.04]); mid += line(a[0], a[1], b[0], b[1], { ...st('#9AA6C8', 5) }); }
  // a plug-in night light low on the right wall (warm)
  { const c = hallPt([1, 0.62, 2.45]); mid += path(rrPath(c[0] - 9, c[1] - 14, 18, 28, 7), { fill: d.lin(['#FFF3C8', '#FFC86A']), stroke: '#8A5A10', strokeWidth: 2 }); }
  // --- light (screen, live): night-light pool, the cool glow from Sam's door gap, a faint moonlit patch
  let light = '';
  { const c = hallPt([1, 0.62, 2.45]); light += circle(c[0], c[1], 90, { fill: d.rad([[0, '#FFD98A', 0.6], [1, '#FFD98A', 0]]), style: 'mix-blend-mode:screen' }); const fp = hallPt([0.86, YF, 2.45]); light += ellipse(fp[0] - 30, fp[1], 120, 22, { fill: d.rad([[0, '#FFD98A', 0.35], [1, '#FFD98A', 0]]), style: 'mix-blend-mode:screen' }); }
  { const [ga, gb] = door.gapX, y0 = hallPt([0, -0.75, ZEND])[1], y1 = hallPt([0, YF, ZEND])[1]; light += rect(ga, y0, Math.max(2, gb - ga), y1 - y0, { fill: '#8FD8FF', opacity: 0.5 }); light += circle((ga + gb) / 2, (y0 + y1) / 2, 160, { fill: d.rad([[0, '#9FE0FF', 0.35], [1, '#9FE0FF', 0]]), style: 'mix-blend-mode:screen' }); }
  // --- near: a hall plant on a little stand at the right edge (framing)
  let near = '';
  near += contact(1790, 1062, 120, 14, 0.25);
  near += pbox(d, 1700, 900, 180, 170, '#C9725A', { r: 22, sw: SWN });
  near += blob(d, [[1740, 840, 70], [1830, 820, 76], [1790, 760, 70], [1700, 790, 52], [1880, 870, 50]], '#3E7A6E', { sw: SWN, hiOp: 0.4 });
  // --- grade: night vignette
  const grade = rect(-40, -40, W + 80, H + 80, { fill: d.rad([[0.5, '#0E0A2A', 0], [1, '#0E0A2A', 0.55]], 0.5, 0.5, 0.75) });
  const layers = [
    { name: 'far', depth: 1, svg: far },
    { name: 'mid', depth: 1, svg: mid },
    { name: 'light', depth: 1, svg: light },
    { name: 'near', depth: 1, svg: near },
    { name: 'grade', depth: 0, svg: grade },
  ];
  const sun = clamp(o.sun ?? 0);
  if (!(sun > 0)) return finish(d, layers, o);
  const extra = hallwaySun(sun, { door: open });
  const out = [];
  for (const l of layers) { if (l.name !== 'grade') out.push(l); for (const e of extra) if (e.after === l.name) out.push(e); }
  return finish(d, out, o);
}

/** Sun pouring out of Sam's door (S00-L021), sun 0..1: the door gap blazes, a wedge of light runs down the runner,
 *  god rays fan along the hall, the hall goes warm and blows out to white. Per-frame insert layers for cam.set:
 *  doorSun (after 'far': the blazing doorway), sunBack (after 'mid': exposure, rays, wedge, bloom; list these BEFORE
 *  Dad's insert so he stands in front of them), sunlight (after 'near': a soft wash over Dad too, then the blow-out),
 *  sunGrade (the night vignette fading; use with skip: ['grade']). o.door must match the hallway({door}) used for the set. */
export function hallwaySun(sun = 0, o = {}) {
  sun = clamp(sun);
  const d = new Defs();
  const open = o.door ?? 0.22;
  const th = open * 1.25, x0 = -0.45, x1 = 0.45, w = x1 - x0, ex = x0 + w * Math.cos(th), ez = ZEND + w * Math.sin(th);
  const ga = hallPt([ex, 0, ez])[0], gb = hallPt([x1, 0, ZEND])[0], y0 = hallPt([0, -0.75, ZEND])[1], y1 = hallPt([0, YF, ZEND])[1];
  const gx = (ga + gb) / 2, gy = (y0 + y1) / 2;
  const k = ease.inOutSine(seg(sun, 0.0, 0.45)), fl = ease.inOutSine(seg(sun, 0.2, 0.8)), blow = ease.inCubic(seg(sun, 0.55, 1));
  // the doorway itself: blazing white-gold through the gap
  let ds = rect(ga, y0, Math.max(2, gb - ga), y1 - y0, { fill: d.lin(['#FFFFFF', mix('#9FE0FF', '#FFF2C0', k)], 'h'), opacity: f(lerp(0.5, 1, k) * 100) / 100 });
  // --- behind the actors: exposure ramp on the set, the wedge down the runner, god rays, bloom
  let B = '';
  const ex2 = lerp(0, 0.36, k) + 0.2 * blow;
  if (ex2 > 0) B += rect(-200, -200, W + 400, H + 400, { fill: `rgb(${Math.round(255 * ex2)},${Math.round(214 * ex2)},${Math.round(156 * ex2)})`, style: 'mix-blend-mode:color-dodge' });
  B += rect(-200, -200, W + 400, H + 400, { fill: d.rad([[0, '#FFC660', 0.6 * k], [0.4, '#FFA848', 0.26 * k], [1, '#FF9040', 0.06 * k]], gx, gy, 1300, 'userSpaceOnUse'), style: 'mix-blend-mode:screen' });
  const fA = hallPt([ex, YF, ez]), fB = hallPt([x1, YF, ZEND]);
  const spread = lerp(0.2, 1, fl);
  B += poly([fA, fB, [fB[0] + 900 * spread, H + 200], [fA[0] - 500 * spread, H + 200]], { fill: d.lin([[0, '#FFF2C8', 0.8 * k], [1, '#FFF2C8', 0.1 * k]], [0, fA[1], 0, H + 200], 'userSpaceOnUse'), style: 'mix-blend-mode:screen' });
  const R = rng(5);
  for (let i = 0; i < 14; i++) {
    const a0 = -170 + i * (340 / 14) + (R() - 0.5) * 8, a1 = a0 + 6 + R() * 7, r = 1700;
    const p0 = [gx + Math.cos(a0 * Math.PI / 180) * r, gy + Math.sin(a0 * Math.PI / 180) * r], p1 = [gx + Math.cos(a1 * Math.PI / 180) * r, gy + Math.sin(a1 * Math.PI / 180) * r];
    B += poly([[gx, gy], p0, p1], { fill: d.rad([[0, '#FFF6D8', 0.55 * fl], [1, '#FFF6D8', 0]], gx, gy, r, 'userSpaceOnUse'), style: 'mix-blend-mode:screen' });
  }
  B += circle(gx, gy, lerp(120, 520, fl), { fill: d.rad([[0, '#FFFFFF', 0.95 * k], [0.3, '#FFF6D8', 0.55 * k], [1, '#FFF6D8', 0]]), style: 'mix-blend-mode:screen' });
  // --- over everything (Dad too): a soft warm wash, a few rays crossing in front, the blow-out to white
  let L = rect(-200, -200, W + 400, H + 400, { fill: d.rad([[0, '#FFD890', 0.3 * k], [1, '#FFB060', 0.1 * k]], gx, gy, 1300, 'userSpaceOnUse'), style: 'mix-blend-mode:screen' });
  for (let i = 0; i < 5; i++) {
    const a0 = 150 + i * 14, a1 = a0 + 5, r = 1700;
    L += poly([[gx, gy], [gx + Math.cos(a0 * Math.PI / 180) * r, gy + Math.sin(a0 * Math.PI / 180) * r], [gx + Math.cos(a1 * Math.PI / 180) * r, gy + Math.sin(a1 * Math.PI / 180) * r]], { fill: d.rad([[0, '#FFF6D8', 0.3 * fl], [1, '#FFF6D8', 0]], gx, gy, r, 'userSpaceOnUse'), style: 'mix-blend-mode:screen' });
  }
  if (blow > 0) L += rect(-200, -200, W + 400, H + 400, { fill: d.rad([[0, '#FFFFFF'], [0.6, '#FFF8E6'], [1, '#FFEFCF']], gx, gy, 1400, 'userSpaceOnUse'), opacity: f(blow * 0.42 * 100) / 100 });
  const grade = sun < 1 ? rect(-40, -40, W + 80, H + 80, { fill: d.rad([[0.5, '#0E0A2A', 0], [1, '#0E0A2A', 0.55]], 0.5, 0.5, 0.75), opacity: f((1 - k) * 100) / 100 }) : '';
  return [
    { name: 'doorSun', after: 'far', depth: 1, svg: String(d) + ds },
    { name: 'sunBack', after: 'mid', depth: 1, svg: B },
    { name: 'sunlight', after: 'near', depth: 1, svg: L },
    { name: 'sunGrade', after: 'near', depth: 0, svg: grade },
  ];
}

// ======================================================================================
// SPACE (snap zoom out: Earth with one side glowing like a lamp, the moon, stars)
// ======================================================================================
// SPACE.earth: centre / radius (world px, depth 1); SPACE.house: Pinewood on the globe = the centre of the glow and
// the point a snap zoom-out should start from (frameOn(SPACE.house, z) -> z 1). Town lights there hold up to ~z 12.
export const SPACE = { earth: { x: 860, y: 610, r: 390 }, house: { x: 700, y: 418 }, moon: { x: 1610, y: 250, r: 96 } };

/** smooth closed blob through points (Catmull-Rom -> cubic) */
function smooth(pts) {
  const n = pts.length; let s = `M${f(pts[0][0])} ${f(pts[0][1])}`;
  for (let i = 0; i < n; i++) {
    const p0 = pts[(i - 1 + n) % n], p1 = pts[i], p2 = pts[(i + 1) % n], p3 = pts[(i + 2) % n];
    s += `C${f(p1[0] + (p2[0] - p0[0]) / 6)} ${f(p1[1] + (p2[1] - p0[1]) / 6)} ${f(p2[0] - (p3[0] - p1[0]) / 6)} ${f(p2[1] - (p3[1] - p1[1]) / 6)} ${f(p2[0])} ${f(p2[1])}`;
  }
  return s + 'Z';
}
/** continent outline: radial wobble around (cx, cy) in units of the earth radius */
function continent(E, cx, cy, rx, ry, seed, n = 11) {
  const R = rng(seed), pts = [];
  for (let i = 0; i < n; i++) { const a = (i / n) * Math.PI * 2, k = 0.72 + R() * 0.5; pts.push([E.x + (cx + Math.cos(a) * rx * k) * E.r, E.y + (cy + Math.sin(a) * ry * k) * E.r]); }
  return smooth(pts);
}

/** Space. o: { glow 0..1 (bakes spaceGlow in for stills), cam }. Layers: sky (stars, nebula; depth 0.08), far (moon;
 *  depth 0.3), mid (Earth; depth 1), grade (vignette, a sky shot). Per frame: spaceGlow(glow) after 'mid'. */
export function space(o = {}) {
  const d = new Defs();
  const E = SPACE.earth;
  // --- sky: deep space gradient, nebula clouds, stars
  let sky = rect(X0 - 400, -900, SW + 800, 2900, { fill: d.lin([[0, '#06071E'], [0.5, '#121446'], [1, '#1E1650']], [0, -300, 0, 1400], 'userSpaceOnUse') });
  for (const [x, y, r, c, op] of [[300, 240, 420, '#4A2E8E', 0.35], [1500, 820, 520, '#2A3C9E', 0.3], [1800, 120, 300, '#7A2E8E', 0.22], [-200, 900, 380, '#2E5A9E', 0.25]]) sky += circle(x, y, r, { fill: d.rad([[0, c, op], [1, c, 0]]) });
  const RS = rng(91);
  for (let i = 0; i < 260; i++) {
    const x = X0 - 300 + RS() * (SW + 600), y = -500 + RS() * 2100, r = 1 + RS() * 2.6, op = 0.35 + RS() * 0.65;
    sky += RS() < 0.9 ? circle(x, y, r, { fill: RS() < 0.2 ? '#FFE9B8' : '#FFFFFF', opacity: f(op * 100) / 100 }) : twinkle(x, y, r * 4, '#FFFFFF', op);
  }
  // --- far: the moon (toy grey, craters, gloss)
  const Mo = SPACE.moon;
  let far = circle(Mo.x, Mo.y, Mo.r * 1.6, { fill: d.rad([[0, '#C9D4FF', 0.18], [1, '#C9D4FF', 0]]) });
  far += circle(Mo.x, Mo.y, Mo.r, { fill: d.lin(['#F2F3FA', '#C9CCDE', '#9EA3BE'], 'd'), stroke: ink('#B8BCD0'), strokeWidth: SWM });
  for (const [cx, cy, r] of [[-0.35, -0.2, 0.22], [0.3, 0.15, 0.28], [-0.1, 0.45, 0.16], [0.42, -0.42, 0.12], [-0.5, 0.25, 0.1]]) far += circle(Mo.x + cx * Mo.r, Mo.y + cy * Mo.r, r * Mo.r, { fill: '#B3B7CE', stroke: '#9EA3BE', strokeWidth: 2 }) + path(`M${f(Mo.x + (cx - r * 0.7) * Mo.r)} ${f(Mo.y + (cy + r * 0.3) * Mo.r)}A${f(r * Mo.r)} ${f(r * Mo.r)} 0 0 0 ${f(Mo.x + (cx + r * 0.7) * Mo.r)} ${f(Mo.y + (cy + r * 0.3) * Mo.r)}`, { fill: 'none', ...st('#E4E6F2', 2.5), opacity: 0.8 });
  far += path(`M${f(Mo.x - Mo.r * 0.7)} ${f(Mo.y - Mo.r * 0.35)}A${f(Mo.r * 0.78)} ${f(Mo.r * 0.78)} 0 0 1 ${f(Mo.x - Mo.r * 0.1)} ${f(Mo.y - Mo.r * 0.75)}`, { fill: 'none', ...st('#FFFFFF', 7), opacity: 0.6 });
  // --- mid: Earth
  let mid = circle(E.x, E.y, E.r * 1.18, { fill: d.rad([[0.78, '#5AB8FF', 0.0], [0.85, '#5AB8FF', 0.45], [1, '#5AB8FF', 0]]) }); // atmosphere rim
  const disc = d.clip(circle(E.x, E.y, E.r));
  let globe = circle(E.x, E.y, E.r, { fill: d.rad([[0, '#4FB6FF'], [0.6, '#2A86E8'], [1, '#1A5CC4']], 0.38, 0.34, 0.75) });
  // continents (original shapes): land, a sandy rim, highlights; the town sits on the first one
  const lands = [
    [-0.42, -0.42, 0.42, 0.3, 4, 13], [0.36, -0.1, 0.3, 0.42, 9, 12], [-0.2, 0.42, 0.34, 0.24, 17, 10], [0.55, 0.62, 0.2, 0.16, 23, 9], [-0.78, 0.1, 0.12, 0.2, 31, 8],
  ];
  for (const [cx, cy, rx, ry, seed, n] of lands) {
    const p = continent(E, cx, cy, rx, ry, seed, n);
    globe += path(p, { fill: '#F2D98A', stroke: '#F2D98A', strokeWidth: 10, strokeLinejoin: 'round' });
    globe += path(p, { fill: d.lin(['#6ED65A', '#3FAF4A']), stroke: ink('#3FAF4A'), strokeWidth: 2.5 });
    globe += g(path(continent(E, cx - 0.04, cy - 0.04, rx * 0.55, ry * 0.5, seed + 1, 7), { fill: '#8BE07A', opacity: 0.55 }));
  }
  // ice cap + clouds
  globe += ellipse(E.x - 0.05 * E.r, E.y - 0.98 * E.r, 0.42 * E.r, 0.14 * E.r, { fill: '#F4F8FF' });
  const RC = rng(55);
  for (let i = 0; i < 10; i++) {
    const cx = E.x + (RC() - 0.5) * 1.7 * E.r, cy = E.y + (RC() - 0.5) * 1.6 * E.r, w = (0.1 + RC() * 0.12) * E.r, n = 3 + Math.floor(RC() * 2);
    const lobes = []; for (let k = 0; k < n; k++) lobes.push([cx - w + (2 * w * k) / (n - 1), cy - Math.sin((k / (n - 1)) * Math.PI) * w * 0.35, w * (0.42 + 0.18 * Math.sin((k / (n - 1)) * Math.PI))]);
    globe += g(blob(d, lobes, '#FFFFFF', { hi: false, gloss: false, up: 0, down: 0.05 }), { opacity: 0.85 });
  }
  // night side shading (soft terminator, lower right) and town lights at Pinewood
  globe += circle(E.x, E.y, E.r, { fill: d.rad([[0, '#0A1240', 0], [0.55, '#0A1240', 0], [1, '#0A1240', 0.55]], 0.25, 0.2, 1.05) });
  const Hs = SPACE.house, RT = rng(71);
  for (let i = 0; i < 46; i++) { const a = RT() * Math.PI * 2, r = Math.pow(RT(), 0.7) * 34; globe += circle(Hs.x + Math.cos(a) * r * 1.3, Hs.y + Math.sin(a) * r * 0.8, 0.7 + RT() * 1.6, { fill: RT() < 0.7 ? '#FFE08A' : '#FFFFFF', opacity: 0.9 }); }
  for (let i = 0; i < 4; i++) globe += line(Hs.x, Hs.y, Hs.x + Math.cos(i * 1.7) * 46, Hs.y + Math.sin(i * 1.7) * 30, { stroke: '#FFE08A', strokeWidth: 0.9, opacity: 0.6 }); // roads out of town
  globe += circle(Hs.x, Hs.y, 2.6, { fill: '#FFFFFF' });
  mid += g(globe, { clipPath: disc });
  mid += circle(E.x, E.y, E.r, { fill: 'none', stroke: ink('#1A5CC4'), strokeWidth: SWN });
  mid += path(`M${f(E.x - E.r * 0.78)} ${f(E.y - E.r * 0.32)}A${f(E.r * 0.86)} ${f(E.r * 0.86)} 0 0 1 ${f(E.x - E.r * 0.22)} ${f(E.y - E.r * 0.8)}`, { fill: 'none', ...st('#FFFFFF', 7), opacity: 0.3 });
  const grade = rect(-40, -40, W + 80, H + 80, { fill: d.rad([[0.55, '#05061A', 0], [1, '#05061A', 0.5]], 0.5, 0.5, 0.75) });
  const layers = [
    { name: 'sky', depth: 0.08, svg: sky },
    { name: 'far', depth: 0.3, svg: far },
    { name: 'mid', depth: 1, svg: mid },
    { name: 'grade', depth: 0, svg: grade },
  ];
  const glow = clamp(o.glow ?? 0);
  if (!(glow > 0)) return finish(d, layers, o);
  const out = [];
  for (const l of layers) { out.push(l); if (l.name === 'mid') out.push(...spaceGlow(glow, o)); }
  return finish(d, out, o);
}

/** One side of Earth glowing like a lamp (S00-L023), glow 0..1, o.t (s) turns the rays slowly.
 *  Returns per-frame insert layers [{name: 'earthGlow', after: 'mid', depth: 1, svg}] (screen pools + a lit cap). */
export function spaceGlow(glow = 1, o = {}) {
  glow = clamp(glow);
  if (!(glow > 0)) return [{ name: 'earthGlow', after: 'mid', depth: 1, svg: '' }];
  const d = new Defs();
  const E = SPACE.earth, Hs = SPACE.house, t = o.t || 0;
  const k = ease.outCubic(glow);
  let s = '';
  // lamp glow: concentric warm halo (normal blend keeps it saturated over the navy), long rays, a screen core
  let out = circle(Hs.x, Hs.y, E.r * 2.4, { fill: d.rad([[0, '#FFF6C8', 0.95 * k], [0.16, '#FFE070', 0.85 * k], [0.32, '#FFA850', 0.6 * k], [0.52, '#FF6E8A', 0.32 * k], [0.75, '#B04AB0', 0.14 * k], [1, '#7A3AB0', 0]], Hs.x, Hs.y, E.r * 2.4, 'userSpaceOnUse') });
  const a0 = Math.atan2(Hs.y - E.y, Hs.x - E.x) * 180 / Math.PI;
  const R = rng(3);
  for (let i = 0; i < 16; i++) {
    const a = a0 - 75 + i * (150 / 15) + t * 6 + (R() - 0.5) * 5, w = i % 2 ? 1.6 + R() * 1.5 : 3 + R() * 3, r = 1500;
    const pa = [Hs.x + Math.cos((a - w) * Math.PI / 180) * r, Hs.y + Math.sin((a - w) * Math.PI / 180) * r], pb = [Hs.x + Math.cos((a + w) * Math.PI / 180) * r, Hs.y + Math.sin((a + w) * Math.PI / 180) * r];
    out += poly([[Hs.x, Hs.y], pa, pb], { fill: d.rad([[0, '#FFF4C0', 0.8 * k], [0.3, '#FFD070', 0.5 * k], [0.6, '#FF7A9A', 0.22 * k], [1, '#C05AC0', 0]], Hs.x, Hs.y, r, 'userSpaceOnUse') });
  }
  // halo and rays live outside the globe only, so the far side of Earth stays blue
  const outside = d.raw('mk', `<mask id="__ID__" maskUnits="userSpaceOnUse" x="-3000" y="-3000" width="8000" height="8000"><rect x="-3000" y="-3000" width="8000" height="8000" fill="#fff"/><circle cx="${E.x}" cy="${E.y}" r="${E.r - 2}" fill="#000"/></mask>`);
  s += g(out, { mask: `url(#${outside})` });
  s += circle(Hs.x, Hs.y, E.r * 0.9, { fill: d.rad([[0, '#FFFFFF', 0.95 * k], [0.4, '#FFF6D0', 0.5 * k], [1, '#FFF6D0', 0]], Hs.x, Hs.y, E.r * 0.9, 'userSpaceOnUse'), style: 'mix-blend-mode:screen' });
  // the lit cap on the globe itself: the town's side washed out to white-gold
  const disc = d.clip(circle(E.x, E.y, E.r + 1));
  s += g(circle(Hs.x, Hs.y, E.r * 1.25, { fill: d.rad([[0, '#FFFFFF', k], [0.35, '#FFF3C0', 0.85 * k], [0.7, '#FFD970', 0.35 * k], [1, '#FFD970', 0]], Hs.x, Hs.y, E.r * 1.25, 'userSpaceOnUse') }), { clipPath: disc });
  return [{ name: 'earthGlow', after: 'mid', depth: 1, svg: String(d) + s }];
}

export const SETS2 = { hallway, space };
