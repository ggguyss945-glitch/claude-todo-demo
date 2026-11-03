// REALITY SETTINGS, part 2: the components the 60-second hook needs (script S00 + S01-L001), in the same toy-plastic
// language as ui.js (navy glass, bevelled periwinkle rims, orange gear, lipped buttons, Nunito 900 / Lilita One).
// Every component is a pure function of explicit params -> SVG string, deterministic (seeded rng, closed-form motion):
//   p      0..1 entry progress (pop with overshoot + flash ring, ui_style.popIn); omitted or >= 1 = settled
//   t      seconds, for looping motion (glows, wiggles, gear spin) - drive it from the shot's local time
//   other  explicit animation params (v, press, crack, fall, scroll, flip, value...) that a shot keys per frame
// Design space 1920x1080 unless a component says it is drawn in SCREEN space (the phone's portrait screen, 720x1480,
// origin top-left), which phone() and insideApp() place into the frame.
import {
  W, H, FONT, Defs, f, clamp, lerp, seg, esc, ease, rng, shade, mix, ink, g, rect, circle, ellipse, line, poly, path, text,
  tr, st, rrPath, gearPath, arcPath, starPts, popIn, popScale, textW,
} from './ui_style.js';
import { glyph } from './ui_icons.js';
import {
  UI, KWUI, CATS, rich, plain, glassCard, logo, iconTile, button, toggle, slider, row, dayCard, DAY_COLORS, DAY_ICONS,
  termsPage, wrapText, defaultTag, tapRing,
} from './ui.js';
import { PAL, stroke as lineOf } from './style.js';
import { starburst, speedLines, shockRing, sparkles, crackedGlass } from './fx.js';

export { termsPage, defaultTag };
const NUN = (size, weight = 900, fill = UI.text, extra = {}) => ({ fontFamily: FONT.ui, fontWeight: weight, fontSize: size, fill, ...extra });
const LIL = (size, fill = UI.text, extra = {}) => ({ fontFamily: FONT.title, fontSize: size, fill, ...extra });
const op = (v) => f(clamp(v) * 100) / 100;
const sc3 = (v) => Math.round(v * 1000) / 1000;
const TAU = Math.PI * 2;

// extra setting categories the hook uses (same shape as ui.CATS)
export const CATS2 = {
  dog: { label: 'Dog size', icon: 'dog', color: '#E8952F' },
  trees: { label: 'Tree direction', icon: 'tree', color: '#3FB24A' },
  sun: { label: 'Brightness', icon: 'brightness', color: '#FFAE1F' },
  bedtime: { label: 'Bedtime', icon: 'moon', color: '#5C5CE0' },
  homework: { label: 'Homework', icon: 'doc', color: '#2FA8F0' },
  birds: { label: 'Birdsong', icon: 'bird', color: '#17C2A0' },
  mondays: { label: 'Mondays', icon: 'clock', color: '#8A5CF2' },
};
const cat = (k) => CATS[k] || CATS2[k] || { label: k, icon: 'gear', color: UI.orange };

// =====================================================================================================================
// PHONE (hand-held, POV) and the app screens
// =====================================================================================================================
export const SCREEN = { w: 720, h: 1480, r: 88 };
export const PHONE = { w: 800, h: 1560, r: 128, bezel: 40, body: '#2E3458' };
export const SKIN = PAL.skinCool;                 // Sam's skin tone (cast.js SAM.skin)

/** the app's screen background (screen space): deep navy with a warm glow under the header and a faint gear watermark */
export function appBg(w = SCREEN.w, h = SCREEN.h, o = {}) {
  const d = new Defs(), top = o.top || '#22306A', bot = o.bot || '#0E1434';
  let s = rect(0, 0, w, h, { fill: d.lin([top, UI.navy1, bot]) });
  s += rect(0, 0, w, h * 0.5, { fill: d.rad([[0, o.glow || UI.orange, 0.22], [1, o.glow || UI.orange, 0]], 0.5, 0, 0.75) });
  if (o.watermark !== false) s += path(gearPath(w * 0.86, h * 0.9, Math.min(w, h) * 0.42, Math.min(w, h) * 0.33, 10, o.rot || 0, 0.52), { fill: '#FFFFFF', opacity: 0.035 });
  return d + s;
}

/** status bar (screen space): clock on the left, signal / wifi / battery on the right. k scales it (k 1 = phone) */
export function statusBar(w = SCREEN.w, o = {}) {
  const k = o.k || 1, y = (o.y ?? 58) * k, c = o.color || '#FFFFFF';
  let s = text(46 * k, y, esc(o.time || '2:13'), NUN(34 * k, 900, c));
  s += g(glyph('signal', c), { transform: tr(w - 196 * k, y - 11 * k, 0.32 * k) });
  s += g(glyph('wifi', c), { transform: tr(w - 140 * k, y - 12 * k, 0.34 * k) });
  s += g(glyph('battery', c), { transform: tr(w - 76 * k, y - 11 * k, 0.4 * k), opacity: 0.95 });
  return s;
}

/** compact app header for the phone (screen space): gear logo, REALITY SETTINGS, breadcrumb, divider */
export function appHeader(w = SCREEN.w, o = {}) {
  const y = o.y ?? 96, d = new Defs();
  let s = logo(76, y + 52, 40, { rot: o.logoRot || 0, glow: false });
  const fs = Math.min(48, (w - 170) / textW('REALITY SETTINGS', 1, 'lil'));
  s += text(132, y + 56, `REALITY <tspan fill="${UI.orange}">SETTINGS</tspan>`, LIL(fs, '#FFFFFF', { letterSpacing: 0.5 }));
  s += text(134, y + 90, rich(o.crumb || 'Settings › {World|purple}'), NUN(24, 800, UI.sub));
  s += path(rrPath(30, y + 118, w - 60, 4, 2), { fill: d.lin([[0, UI.orange, 0.9], [0.4, UI.rimHi, 0.5], [1, UI.rimHi, 0.0]], 'h') });
  return d + s;
}

/** a full app screen (screen space): bg + status bar + header + content (screen-space svg, laid out below y 240) */
export function appScreen(o = {}) {
  const w = o.w || SCREEN.w, h = o.h || SCREEN.h;
  let s = appBg(w, h, o.bg || {});
  if (o.status !== false) s += statusBar(w, { time: o.time });
  if (o.header !== false) s += appHeader(w, { crumb: o.crumb, logoRot: o.logoRot });
  return s + (o.content || '');
}

/** home screen (screen space) with generic app tiles and the REALITY SETTINGS icon that "you never downloaded".
 *  newApp 0..1 pops the icon into its slot; wiggle {t, amp} rattles it; time = status bar clock */
export function homeScreen(o = {}) {
  const w = SCREEN.w, h = SCREEN.h, d = new Defs();
  let s = rect(0, 0, w, h, { fill: d.lin(['#3B2A86', '#5A46C8', '#E58AB8']) });
  s += circle(w * 0.75, h * 0.2, 260, { fill: d.rad([[0, '#FFE6A8', 0.55], [1, '#FFE6A8', 0]]) });
  s += path(`M0 ${f(h * 0.78)}Q${f(w * 0.3)} ${f(h * 0.7)} ${f(w * 0.6)} ${f(h * 0.76)}T${f(w)} ${f(h * 0.74)}V${f(h)}H0Z`, { fill: '#2A1E66', opacity: 0.55 });
  s += statusBar(w, { time: o.time || '2:13' });
  const apps = [
    ['clock', '#5C6B9E', 'Clock'], ['weather', '#3BAEFF', 'Weather'], ['play', '#FF5596', 'Music'], ['graphics', '#6DC52A', 'Photos'],
    ['bell', '#F2A51C', 'Alarms'], ['language', '#3D7FEA', 'Chat'], ['cat', '#9EA4B4', 'Pets'], ['download', '#17C2A0', 'Files'],
    ['user', '#A779FF', 'Friends'], ['speed', '#E5303D', 'Games'], ['volume', '#25AEF2', 'Podcasts'], [null, null, null],
  ];
  const cols = 4, tile = 118, gx = (w - cols * tile) / (cols + 1), y0 = 170, gy = 196;
  apps.forEach(([ic, col, lab], i) => {
    const cx = gx + tile / 2 + (i % cols) * (tile + gx), cy = y0 + tile / 2 + Math.floor(i / cols) * gy;
    if (!ic) {
      // the new app slot
      const k = o.newApp === undefined ? 1 : clamp(o.newApp);
      if (k <= 0) return;
      const wg = o.wiggle ? (o.wiggle.amp ?? 6) * Math.sin(TAU * 9 * (o.wiggle.t || 0)) : 0;
      const ic2 = g(appIcon({ cx, cy, size: tile, glow: o.glow ?? 0.6, badge: o.badge ?? 1, label: 'Settings', labelSize: 24, t: o.t }), { transform: `rotate(${f(wg)} ${f(cx)} ${f(cy)})` });
      s += popIn(ic2, cx, cy, k >= 1 ? undefined : k, { ring: 'circle', r: tile * 0.6, ringGrow: 60, ringColor: '#FFE0B0' });
      return;
    }
    s += iconTile(ic, cx, cy, tile, col);
    s += text(cx, cy + tile / 2 + 38, esc(lab), NUN(24, 800, '#FFFFFF', { textAnchor: 'middle', opacity: 0.92 }));
  });
  // dock
  const dy = h - 210;
  s += path(rrPath(30, dy, w - 60, 170, 58), { fill: '#FFFFFF', opacity: 0.16 });
  [['phone', '#2FD27C'], ['language', '#3CCBFF'], ['globe', '#3D7FEA'], ['graphics', '#FF7A3D']].forEach(([ic, col], i) => {
    s += iconTile(ic, 30 + (w - 60) * (i + 0.5) / 4, dy + 85, 112, col);
  });
  return d + s;
}

// ---------- Sam's hand (POV, right hand) ----------
// Mitten hand in the cast style (rig.mitten): one rounded palm mass, a capsule thumb, finger tips as soft scallops,
// cream skin (PAL.skinCool) with a tinted outline from style.stroke(), orange hoodie sleeve with a ribbed cuff.
// Coordinates are phone-local units (phone centre 0,0; body 800x1560), so it scales with the phone.
function capsulePath(x1, y1, x2, y2, r1, r2 = r1) {
  const dx = x2 - x1, dy = y2 - y1, L = Math.hypot(dx, dy) || 0.001, ux = dx / L, uy = dy / L, nx = -uy, ny = ux;
  return `M${f(x1 + nx * r1)} ${f(y1 + ny * r1)}L${f(x2 + nx * r2)} ${f(y2 + ny * r2)}A${f(r2)} ${f(r2)} 0 0 0 ${f(x2 - nx * r2)} ${f(y2 - ny * r2)}L${f(x1 - nx * r1)} ${f(y1 - ny * r1)}A${f(r1)} ${f(r1)} 0 0 0 ${f(x1 + nx * r1)} ${f(y1 + ny * r1)}Z`;
}
const ellPath = (cx, cy, rx, ry, rot = 0) => {
  const a = (rot * Math.PI) / 180, c = Math.cos(a), s = Math.sin(a);
  const P = (u, v) => `${f(cx + u * c - v * s)} ${f(cy + u * s + v * c)}`;
  return `M${P(-rx, 0)}A${f(rx)} ${f(ry)} ${f(rot)} 1 0 ${P(rx, 0)}A${f(rx)} ${f(ry)} ${f(rot)} 1 0 ${P(-rx, 0)}Z`;
};
/** union of shapes with one outline (strokes underneath, fills on top) - the cast's single-silhouette rule */
function unionFill(ds, fill, line, sw) {
  return ds.map((dd) => path(dd, { fill: line, stroke: line, strokeWidth: f(sw * 2), strokeLinejoin: 'round' })).join('') + ds.map((dd) => path(dd, { fill })).join('');
}
const ROOT0 = [398, 268], TL1 = 252, TL2 = 238;      // thumb root (local units) and bone lengths
function handGeom(o) {
  const th = o.thumb || {};
  const tx = (th.x ?? SCREEN.w * 0.58) - SCREEN.w / 2, ty = (th.y ?? SCREEN.h * 0.6) - SCREEN.h / 2;
  // the grip slides along the phone so the thumb can reach: the hand moves just enough to bring the root in range
  const reach = (TL1 + TL2) * 0.93, dx0 = ROOT0[0] - tx, dy0 = ROOT0[1] - ty, D0 = Math.hypot(dx0, dy0) || 1;
  let sx = 0, sy = 0;
  if (D0 > reach) { sx = tx + (dx0 / D0) * reach - ROOT0[0]; sy = ty + (dy0 / D0) * reach - ROOT0[1]; }
  sx = clamp(sx + (o.handShift?.[0] || 0), -50, 40); sy = clamp(sy + (o.handShift?.[1] || 0), -640, 140);
  return { tx, ty, lx: sx, ly: sy };
}
/** parts of the hand behind the phone: sleeve, cuff, palm heel */
function handBack(d, o, G) {
  const skin = o.skin || SKIN, ln = lineOf(skin), sw = 7;
  const hood = PAL.samHoodie, cuff = PAL.samHoodieDark;
  const { lx, ly } = G;
  let s = '';
  // forearm in the hoodie sleeve, running off the frame to the lower right
  const sleeve = capsulePath(500 + lx, 980 + ly, 1240 + lx, 1640 + ly, 190, 232);
  s += unionFill([sleeve], d.lin([shade(hood, 0.05), shade(hood, -0.07)], 'd'), lineOf(hood), sw);
  s += path(capsulePath(470 + lx, 1110 + ly, 880 + lx, 1480 + ly, 24, 28), { fill: '#FFFFFF', opacity: 0.22 });
  // ribbed cuff at the wrist
  const c0 = [404 + lx, 878 + ly], c1 = [560 + lx, 1018 + ly];
  s += unionFill([capsulePath(c0[0], c0[1], c1[0], c1[1], 176, 184)], d.lin([shade(cuff, 0.05), shade(cuff, -0.06)], 'd'), lineOf(cuff), sw);
  const ax = (c1[0] - c0[0]) / 205, ay = (c1[1] - c0[1]) / 205, nx = -ay, ny = ax;
  for (let i = -4; i <= 4; i++) {
    const ox = c0[0] + (c1[0] - c0[0]) * 0.5 + nx * i * 38, oy = c0[1] + (c1[1] - c0[1]) * 0.5 + ny * i * 38, half = 108 - Math.abs(i) * 6;
    s += path(`M${f(ox - ax * half)} ${f(oy - ay * half)}L${f(ox + ax * half)} ${f(oy + ay * half)}`, { fill: 'none', stroke: lineOf(cuff), strokeWidth: 5, strokeLinecap: 'round', opacity: 0.3 });
  }
  // heel of the palm below the phone's lower-right corner
  s += unionFill([ellPath(300 + lx, 770 + ly, 232, 182, -30), ellPath(150 + lx, 690 + ly, 200, 160, -10)], d.lin([shade(skin, 0.04), shade(skin, -0.08)], 'd'), ln, sw);
  return s;
}
/** finger pads round the left edge, the thenar on the right edge and the thumb over the screen (above the phone) */
function handFront(d, o, G) {
  const skin = o.skin || SKIN, ln = lineOf(skin), sw = 7, th = o.thumb || {};
  const press = clamp(th.press || 0);
  const { tx, ty, lx, ly } = G;
  const skinG = d.lin([shade(skin, 0.05), shade(skin, -0.07)], 'd');
  let s = '';
  // fingers curling round the left edge from behind: four short capsules that overlap the bezel, the pinky shorter
  const ex = -PHONE.w / 2;
  const fing = [[ex - 70, ex + 34, 52, 54], [ex - 76, ex + 38, 160, 55], [ex - 70, ex + 34, 268, 53], [ex - 56, ex + 22, 370, 46]];
  const fD = fing.map(([x0, x1, y, r]) => capsulePath(x0, y + ly, x1, y + ly, r, r));
  s += unionFill(fD, d.lin([shade(skin, 0.05), shade(skin, -0.07)], 'v'), ln, sw);
  fing.forEach(([x0, x1, y, r]) => { s += path(`M${f(x1 - r * 0.9)} ${f(y + ly - r * 0.52)}L${f(x1 - r * 0.1)} ${f(y + ly - r * 0.5)}`, { fill: 'none', stroke: '#FFFFFF', strokeWidth: 11, strokeLinecap: 'round', opacity: 0.5 }); });
  fing.slice(0, 3).forEach(([x0, x1, y, r]) => { s += path(`M${f(x0 + 6)} ${f(y + ly + r * 0.98)}L${f(x1 - r * 0.6)} ${f(y + ly + r * 0.98)}`, { fill: 'none', stroke: ln, strokeWidth: 4, strokeLinecap: 'round', opacity: 0.35 }); });
  // thenar: the thumb's base wrapping the right edge
  const rx0 = ROOT0[0] + lx, ry0 = ROOT0[1] + ly;
  const thenar = ellPath(rx0 + 64, ry0 + 118, 104, 172, -14);
  if (th.hide) return s + unionFill([thenar], skinG, ln, sw);
  // thumb: 2-bone mitten thumb from the root to the touch point, the knuckle bulging up and out
  const ex2 = tx, ey2 = ty, dx = ex2 - rx0, dy = ey2 - ry0, D = Math.hypot(dx, dy) || 1;
  // too far: the thumb stretches a little; near: it foreshortens toward the glass (bent tip seen from above) instead of
  // folding into a V, so the bones scale to the distance with a gentle bend (never below 55%)
  const k = D > TL1 + TL2 - 2 ? D / (TL1 + TL2 - 2) : Math.max(0.55, Math.min(1, (D * 1.1) / (TL1 + TL2)));
  const l1 = TL1 * k, l2 = TL2 * k;
  const a = Math.acos(clamp((l1 * l1 + D * D - l2 * l2) / (2 * l1 * D), -1, 1));
  const base = Math.atan2(dy, dx), bend = th.bend ?? 1;
  const kx = rx0 + Math.cos(base + bend * a) * l1, ky = ry0 + Math.sin(base + bend * a) * l1;
  const ang = Math.atan2(ey2 - ky, ex2 - kx);
  const R1 = 64, R2 = 57 * (1 + press * 0.07);
  if (press > 0.02) s += ellipse(tx, ty, R2 * 1.25, R2 * 0.95, { fill: '#0A0F2A', opacity: op(0.28 * press) }) +
    circle(tx, ty, R2 * (1.4 + 0.5 * press), { fill: 'none', stroke: '#FFFFFF', strokeWidth: 6, opacity: op(0.35 * press) });
  const prox = capsulePath(rx0, ry0, kx, ky, R1 + 6, R1);
  const dist = capsulePath(kx, ky, ex2, ey2, R1 - 2, R2);
  s += unionFill([thenar, prox, dist], skinG, ln, sw);
  // knuckle crease and a gloss strip along the lit (upper-left) side of the thumb
  const na = ang - Math.PI / 2;
  s += path(`M${f(kx + Math.cos(na) * R1 * 0.75)} ${f(ky + Math.sin(na) * R1 * 0.75)}Q${f(kx + Math.cos(ang) * 16 + Math.cos(na) * 20)} ${f(ky + Math.sin(ang) * 16 + Math.sin(na) * 20)} ${f(kx + Math.cos(na) * R1 * 0.05)} ${f(ky + Math.sin(na) * R1 * 0.05)}`, { fill: 'none', stroke: ln, strokeWidth: 5, strokeLinecap: 'round', opacity: 0.45 });
  const side = Math.sin(na) < 0 ? 1 : -1;        // the side of the thumb facing up
  const gp = (u, r) => [kx + Math.cos(ang) * l2 * u + Math.cos(na) * r * side, ky + Math.sin(ang) * l2 * u + Math.sin(na) * r * side];
  const [g0x, g0y] = gp(0.12, R2 * 0.5), [g1x, g1y] = gp(0.86, R2 * 0.46);
  s += path(`M${f(g0x)} ${f(g0y)}L${f(g1x)} ${f(g1y)}`, { fill: 'none', stroke: '#FFFFFF', strokeWidth: 15, strokeLinecap: 'round', opacity: 0.45 });
  s += ellipse(rx0 + 24, ry0 + 30, 40, 90, { fill: '#FFFFFF', opacity: 0.22, transform: `rotate(-18 ${f(rx0 + 24)} ${f(ry0 + 30)})` });
  if (o.glow) s += path(dist, { fill: o.glowColor || '#BFE3FF', opacity: op(o.glow * 0.22) });
  return s;
}

/** phone({x, y, s, rot, screen, bg, glow, glowColor, glare, thumb:{x, y, press, hide, bend}, hand, shake, crack, t})
 *  A hand-held phone, POV. (x, y) = phone centre in the frame, s = scale (s 1: body 800x1560 px; 0.6 fills a 1080 frame
 *  height), rot in degrees. screen = svg in SCREEN space (720x1480, origin top-left), clipped to the rounded screen;
 *  bg: 'app' (default appBg) | 'none' | a colour. thumb x/y are SCREEN coords of the touch point (press 0..1 squashes
 *  the pad and shades the glass); the grip slides up/down the phone by itself so the thumb can reach (handShift [dx, dy]
 *  local units adds to it); thumb:false draws the hand without a thumb (hand:false = phone only).
 *  glow 0..1 = screen light spilling round the phone (night). shake: number px or {amp, t, freq} = buzz rattle.
 *  crack 0..1 = cracked glass over the screen (fx.crackedGlass). */
export function phone(o = {}) {
  const { x = 960, y = 540, s = 0.6, rot = 0 } = o;
  const d = new Defs(), BW = PHONE.w, BH = PHONE.h, R = PHONE.r, sw = SCREEN.w, sh = SCREEN.h;
  const body = o.body || PHONE.body, hand = o.hand !== false;
  const thumbOn = hand && o.thumb !== false;
  const G = handGeom({ thumb: o.thumb || {}, handShift: o.handShift });
  let dx = 0, dy = 0, dr = 0;
  if (o.shake) {
    const sk = typeof o.shake === 'number' ? { amp: o.shake } : o.shake, t = sk.t ?? o.t ?? 0, A = sk.amp ?? 10, fq = sk.freq ?? 24;
    dx = A * Math.sin(TAU * fq * t); dy = A * 0.35 * Math.sin(TAU * fq * 1.37 * t + 1); dr = (sk.rot ?? A * 0.16) * Math.sin(TAU * fq * 0.91 * t + 2);
  }
  let out = '';
  // light spill round the phone (radial gradients only: cheap and safe inside baked layers)
  if (o.glow) {
    const gc = o.glowColor || '#BFE3FF';
    out += ellipse(0, 0, BW * 1.05, BH * 0.78, { fill: d.rad([[0, gc, 0.5 * o.glow], [0.55, gc, 0.2 * o.glow], [1, gc, 0]]) });
  }
  if (hand) out += handBack(d, o, G);
  // body: dark lip, plastic body, bevel highlight, side buttons
  const ln = '#121630';
  out += path(rrPath(-BW / 2 + 6, -BH / 2 + 16, BW, BH, R), { fill: '#0B0E22', opacity: 0.55 });
  for (const [bx, by, bw, bh] of [[BW / 2 - 6, -440, 22, 150], [-BW / 2 - 16, -500, 22, 110], [-BW / 2 - 16, -360, 22, 110]]) {
    out += path(rrPath(bx, by, bw, bh, 10), { fill: d.lin([shade(body, 0.1), shade(body, -0.08)], 'h'), stroke: ln, strokeWidth: 5 });
  }
  out += path(rrPath(-BW / 2, -BH / 2, BW, BH, R), { fill: d.lin([shade(body, 0.09), body, shade(body, -0.07)], 'd') });
  out += path(rrPath(-BW / 2 + 9, -BH / 2 + 9, BW - 18, BH - 18, R - 9), { fill: 'none', stroke: d.lin([[0, '#FFFFFF', 0.4], [0.35, '#FFFFFF', 0.08], [1, '#FFFFFF', 0.02]], 'd'), strokeWidth: 6 });
  out += path(rrPath(-BW / 2, -BH / 2, BW, BH, R), { fill: 'none', stroke: ln, strokeWidth: 7 });
  // screen
  const sx = -sw / 2, sy = -sh / 2;
  const clip = d.clip(path(rrPath(sx, sy, sw, sh, SCREEN.r)));
  let scr = '';
  if (o.bg === undefined || o.bg === 'app') scr += appBg(sw, sh);
  else if (o.bg !== 'none') scr += rect(0, 0, sw, sh, { fill: o.bg });
  scr += o.screen || '';
  let face = g(scr, { transform: `translate(${f(sx)} ${f(sy)})` });
  // glare: a soft diagonal sheet and a thin streak (glass), strength o.glare
  const gl = o.glare ?? 1;
  if (gl > 0) {
    face += poly([[sx, sy], [sx + sw * 0.62, sy], [sx, sy + sh * 0.46]], { fill: d.lin([[0, '#FFFFFF', 0.16 * gl], [1, '#FFFFFF', 0]], 'd') });
    face += poly([[sx + sw * 0.78, sy], [sx + sw * 0.9, sy], [sx, sy + sh * 0.66], [sx, sy + sh * 0.6]], { fill: '#FFFFFF', opacity: op(0.06 * gl) });
  }
  if (o.crack) face += crackOverlay(sx, sy, sw, sh, clamp(o.crack), o.crackAt || [sw * 0.6, sh * 0.3], o.seed || 3);
  out += g(face, { clipPath: clip });
  out += path(rrPath(sx, sy, sw, sh, SCREEN.r), { fill: 'none', stroke: '#05071A', strokeWidth: 5 });
  // punch-hole camera
  out += circle(0, sy + 40, 15, { fill: '#05071A' }) + circle(-4, sy + 36, 4.5, { fill: '#5A6AB8', opacity: 0.8 });
  if (hand) out += handFront(d, { ...o, thumb: thumbOn ? (o.thumb || {}) : { ...(o.thumb || {}), hide: true } }, G);
  if (o.shake && o.buzz !== false) {
    const A = typeof o.shake === 'number' ? o.shake : (o.shake.amp ?? 10);
    for (const side of [-1, 1]) for (let i = 0; i < 2; i++) {
      const bx = side * (BW / 2 + 60 + i * 46), by = -BH * 0.32;
      out += path(`M${f(bx)} ${f(by - 70 - i * 26)}Q${f(bx + side * 26)} ${f(by)} ${f(bx)} ${f(by + 70 + i * 26)}`, { fill: 'none', ...st('#FFFFFF', 12 - i * 3), opacity: op(Math.min(1, A / 8) * (0.9 - i * 0.3)) });
    }
  }
  return d + g(out, { transform: `translate(${f(x + dx)} ${f(y + dy)}) rotate(${f(rot + dr)}) scale(${sc3(s)})` });
}
/** frame coords of a SCREEN point on a phone placed with the same {x, y, s, rot} (shake ignored) */
export function phonePoint(o, px, py) {
  const { x = 960, y = 540, s = 0.6, rot = 0 } = o, a = (rot * Math.PI) / 180;
  const u = (px - SCREEN.w / 2) * s, v = (py - SCREEN.h / 2) * s;
  return [x + u * Math.cos(a) - v * Math.sin(a), y + u * Math.sin(a) + v * Math.cos(a)];
}
/** the screen's rectangle in frame px (axis-aligned bounds; exact when rot = 0) - e.g. for a zoomThrough portal */
export function phoneScreenRect(o) {
  const c = [[0, 0], [SCREEN.w, 0], [0, SCREEN.h], [SCREEN.w, SCREEN.h]].map(([a, b]) => phonePoint(o, a, b));
  const xs = c.map((q) => q[0]), ys = c.map((q) => q[1]);
  const x0 = Math.min(...xs), y0 = Math.min(...ys);
  return { x: x0, y: y0, w: Math.max(...xs) - x0, h: Math.max(...ys) - y0, r: SCREEN.r * (o.s ?? 0.6) };
}

/** insideApp(content, {t, time, edge, glare, header, crumb, bg}) - full-frame "we are inside the app" framing: app
 *  background over the whole 1920x1080 frame, status bar, optional app header, then content (frame space).
 *  edge 0..1 brings the phone's bezel in from the frame edges (1 = screen inset ~70 px with rounded corners) so a push
 *  from phone() into insideApp() reads as one move. */
export function insideApp(content = '', o = {}) {
  const d = new Defs();
  let s = appBg(W, H, { rot: (o.t || 0) * 6, ...(o.bg || {}) });
  if (o.status !== false) s += statusBar(W, { k: 1.25, time: o.time, y: 54 });
  if (o.header) {
    s += logo(120, 150, 52, { rot: o.logoRot || 0 });
    s += text(194, 164, `REALITY <tspan fill="${UI.orange}">SETTINGS</tspan>`, LIL(64, '#FFFFFF', { letterSpacing: 1 }));
    s += text(196, 206, rich(o.crumb || 'Settings › {World|purple}'), NUN(30, 800, UI.sub));
  }
  s += content;
  const gl = o.glare ?? 0.7;
  if (gl > 0) s += poly([[0, 0], [W * 0.5, 0], [0, H * 0.75]], { fill: d.lin([[0, '#FFFFFF', 0.1 * gl], [1, '#FFFFFF', 0]], 'd') });
  const e = clamp(o.edge || 0);
  if (e > 0.001) {
    const ins = 70 * e, r = 40 + 90 * e;
    s += path(`M-20 -20H${W + 20}V${H + 20}H-20Z${rrPath(ins, ins, W - ins * 2, H - ins * 2, r)}`, { fill: PHONE.body, fillRule: 'evenodd' });
    s += path(rrPath(ins, ins, W - ins * 2, H - ins * 2, r), { fill: 'none', stroke: '#05071A', strokeWidth: 6 });
  }
  return d + s;
}

// =====================================================================================================================
// SLIDERS: Dog size (big thumb) and Brightness (incl. the full-screen version)
// =====================================================================================================================
/** bigSlider({x, y, w, v, iconL, iconR, iconLs, iconRs, color, color2, knobR, railH, bubble, bubbleK, stops, grab, knob})
 *  A chunky slider for touch: rail centred on y from x to x+w (end icons inside that span), gear knob of radius knobR
 *  (grab 0..1 swells it with a glow ring, as when the thumb holds it), value bubble above the knob. knob:'sun' swaps the
 *  gear for a glowing sun (brightness). */
export function bigSlider(o = {}) {
  const { x = 0, y = 0, w = 640, iconL = 'dogSmall', iconR = 'dog', color = UI.orange, color2 = UI.amber, stops } = o;
  const v = clamp(o.v ?? 0.5), d = new Defs(), kr = o.knobR ?? 54, rh = o.railH ?? 40, grab = clamp(o.grab || 0);
  const er = o.endR ?? 40, rx0 = x + er * 2 + 22, rx1 = x + w - er * 2 - 22;
  let s = '';
  [[x + er, iconL, o.iconLs ?? 0.48], [x + w - er, iconR, o.iconRs ?? 0.66]].forEach(([cx, ic, k]) => {
    s += circle(cx, y + 5, er, { fill: '#070A1C', opacity: 0.6 });
    s += circle(cx, y, er, { fill: d.lin([UI.navy3, UI.navy2]), stroke: '#070A1C', strokeWidth: 3 });
    s += g(glyph(ic, UI.sub, UI.navy2), { transform: tr(cx, y, k * er / 40) });
  });
  s += path(rrPath(rx0 - 6, y - rh / 2 - 6, rx1 - rx0 + 12, rh + 12, rh / 2 + 6), { fill: d.lin([UI.rim, UI.rimHi]) });
  s += path(rrPath(rx0, y - rh / 2, rx1 - rx0, rh, rh / 2), { fill: d.lin(['#060A1E', '#141C44']) });
  const kx = lerp(rx0, rx1, v);
  if (v > 0) {
    s += path(rrPath(rx0, y - rh / 2, Math.max(rh, kx - rx0 + rh / 2), rh, rh / 2), { fill: d.lin([color, color2], 'h') });
    s += path(rrPath(rx0 + 10, y - rh / 2 + 6, Math.max(4, kx - rx0 - 14), rh * 0.2, rh * 0.1), { fill: '#FFFFFF', opacity: 0.45 });
  }
  if (o.ticks) for (let i = 1; i < o.ticks; i++) { const tx = lerp(rx0, rx1, i / o.ticks); s += rect(tx - 2, y - rh * 0.22, 4, rh * 0.44, { fill: tx < kx ? '#FFFFFF' : UI.dim, opacity: 0.45, rx: 2 }); }
  if (stops) stops.forEach((lab, i) => {
    const sx = lerp(rx0, rx1, stops.length === 1 ? 0.5 : i / (stops.length - 1));
    const near = Math.abs(sx - kx) < (rx1 - rx0) / (stops.length * 2);
    s += circle(sx, y + rh / 2 + 22, near ? 7 : 5, { fill: near ? UI.orangeHi : UI.dim });
    s += text(sx, y + rh / 2 + 62, esc(lab), NUN(o.stopSize || 28, 900, near ? '#FFFFFF' : UI.dim, { textAnchor: i === 0 ? 'start' : i === stops.length - 1 ? 'end' : 'middle', dx: i === 0 ? -14 : i === stops.length - 1 ? 14 : 0 }));
  });
  // knob
  const R = kr * (1 + grab * 0.14);
  if (grab > 0) s += circle(kx, y, R * 1.45, { fill: d.rad([[0, '#FFFFFF', 0.35 * grab], [0.6, color2, 0.25 * grab], [1, color2, 0]]) });
  if (o.knob === 'sun') {
    for (let i = 0; i < 10; i++) {
      const a = (i / 10) * TAU + (o.rot || 0) * Math.PI / 180;
      s += line(kx + Math.cos(a) * R * 1.02, y + Math.sin(a) * R * 1.02, kx + Math.cos(a) * R * 1.32, y + Math.sin(a) * R * 1.32, { ...st('#FFE36A', R * 0.13) });
    }
    s += circle(kx, y + R * 0.09, R * 0.92, { fill: '#B8650A', opacity: 0.5 });
    s += circle(kx, y, R * 0.92, { fill: d.lin(['#FFF6B0', '#FFD43B', '#FFA21F']), stroke: ink('#FFC23D'), strokeWidth: 3.5 });
    s += ellipse(kx - R * 0.3, y - R * 0.42, R * 0.34, R * 0.15, { fill: '#FFFFFF', opacity: 0.85, transform: `rotate(-25 ${f(kx - R * 0.3)} ${f(y - R * 0.42)})` });
  } else {
    s += path(gearPath(kx, y + R * 0.12, R, R * 0.86, 12, v * 220 + (o.rot || 0), 0.5), { fill: '#070A1C', opacity: 0.45 });
    s += path(gearPath(kx, y, R, R * 0.86, 12, v * 220 + (o.rot || 0), 0.5), { fill: d.lin(['#FFFFFF', '#D3DCF4']), stroke: '#3C4370', strokeWidth: 3 });
    s += circle(kx, y, R * 0.44, { fill: d.lin([UI.orangeHi, UI.orange2]) });
    s += ellipse(kx - R * 0.3, y - R * 0.46, R * 0.3, R * 0.13, { fill: '#FFFFFF', opacity: 0.9 });
  }
  if (o.bubble) {
    const bk = clamp(o.bubbleK ?? 1), bfs = o.bubbleSize || 40;
    const bw = textW(o.bubble, bfs) + 60, bh = bfs * 1.7, by = y - R - 34 - bh;
    const bx = clamp(kx - bw / 2, x - 10, x + w - bw + 10);
    let b = path(rrPath(bx, by + 7, bw, bh, bh / 2), { fill: shade(UI.orange2, -0.22) });
    b += poly([[kx - 16, by + bh - 2], [kx + 16, by + bh - 2], [kx, by + bh + 20]], { fill: UI.orange2, stroke: ink(UI.orange), strokeWidth: 3, strokeLinejoin: 'round' });
    b += path(rrPath(bx, by, bw, bh, bh / 2), { fill: d.lin([UI.orangeHi, UI.orange, UI.orange2]) });
    b += path(rrPath(bx + 20, by + 8, bw - 40, 9, 4.5), { fill: '#FFFFFF', opacity: 0.4 });
    b += text(bx + bw / 2, by + bh / 2 + bfs * 0.36, rich(o.bubble, { ...KWUI, white: '#FFFFFF' }, 'white'), NUN(bfs, 900, '#FFFFFF', { textAnchor: 'middle', letterSpacing: 0.5 }));
    b += path(rrPath(bx, by, bw, bh, bh / 2), { fill: 'none', stroke: ink(UI.orange), strokeWidth: 3 });
    s += bk >= 1 ? b : popIn(b, kx, by + bh, bk, { ring: false });
  }
  return d + s;
}
/** knob centre of a bigSlider with the same params (for placing the thumb / tap rings) */
export function bigSliderKnob(o = {}) {
  const { x = 0, y = 0, w = 640 } = o, er = o.endR ?? 40;
  return [lerp(x + er * 2 + 22, x + w - er * 2 - 22, clamp(o.v ?? 0.5)), y];
}

/** settingCard({x, y, w, cat, label, icon, color, value, v, bubble, stops, grab, sub, ...bigSlider opts}, p)
 *  A tall settings card: icon tile + label + value on top, a bigSlider below, optional sub line. Height 380 (+44 sub). */
export function settingCard(o = {}, p) {
  const { x = 0, y = 0, w = 660 } = o;
  const c = { ...cat(o.cat || 'dog'), ...(o.label ? { label: o.label } : {}), ...(o.icon ? { icon: o.icon } : {}), ...(o.color ? { color: o.color } : {}) };
  const h = o.h || (o.sub ? 424 : 380), d = new Defs(), r = 34;
  let s = path(rrPath(x, y + 7, w, h, r), { fill: '#080C24', opacity: 0.9 });
  s += path(rrPath(x, y, w, h, r), { fill: o.selected === false ? d.lin([UI.row, UI.rowLo]) : d.lin(['#3C3F86', '#2B2E6C']) });
  s += path(rrPath(x + 26, y + 7, w - 52, 8, 4), { fill: '#FFFFFF', opacity: 0.14 });
  if (o.selected !== false) s += path(rrPath(x - 3, y - 3, w + 6, h + 6, r + 3), { fill: 'none', stroke: UI.orange, strokeWidth: 5 }) +
    path(rrPath(x - 3, y + 30, 10, 60, 5), { fill: UI.orangeHi });
  s += iconTile(c.icon, x + 30 + 39, y + 62, 78, c.color);
  s += text(x + 130, y + 78, esc(c.label), NUN(o.labelSize || 44, 900, '#FFFFFF'));
  if (o.value) s += text(x + w - 32, y + 78, rich(o.value), NUN(40, 900, UI.orangeHi, { textAnchor: 'end' }));
  s += bigSlider({ ...o, x: x + 26, y: y + 262, w: w - 52, bubble: o.bubble, stops: o.stops });
  if (o.sub) s += text(x + 32, y + h - 26, rich(o.sub, KWUI, 'orange'), NUN(26, 800, UI.sub));
  return popIn(d + s, x + w / 2, y + h / 2, p, { bbox: { x, y, w, h, r }, ringGrow: 36 });
}
/** the knob position of a settingCard (frame / screen space of the card) */
export const settingCardKnob = (o = {}) => bigSliderKnob({ ...o, x: (o.x || 0) + 26, y: (o.y || 0) + 262, w: (o.w || 660) - 52 });

/** Dog size screen content (screen space, below the header): the card, a live preview tile and a small note */
export function dogSizeScreen(o = {}) {
  const v = clamp(o.v ?? 0.35);
  const mult = Math.round(lerp(1, 20, v * v) * 10) / 10;
  const label = v < 0.18 ? 'Normal' : v < 0.55 ? 'BIG' : v < 0.85 ? 'HUGE' : 'HOUSE';
  let s = text(36, 300, esc('PETS'), NUN(26, 900, UI.dim, { letterSpacing: 3 }));
  const card = { x: 24, y: 326, w: SCREEN.w - 48, cat: 'dog', value: `{${label}|orange}`, v, grab: o.grab, bubble: o.bubble ?? `×${mult}`, stops: ['Tiny', 'Big', 'HOUSE'], sub: 'Applies to: {Tiny|pink} (next door)' };
  s += settingCard(card);
  // a second, quieter row so the screen reads as a real menu
  s += row({ x: 24, y: 792, w: SCREEN.w - 48, cat: 'trees', label: 'Tree direction', icon: 'tree', color: '#3FB24A', value: o.treeValue || 'Up' });
  s += row({ x: 24, y: 918, w: SCREEN.w - 48, kind: 'toggle', cat: 'birds', label: 'Birdsong', icon: 'bird', color: '#17C2A0', k: 1 });
  s += row({ x: 24, y: 1044, w: SCREEN.w - 48, cat: 'gravity', value: 'Earth' });
  s += row({ x: 24, y: 1170, w: SCREEN.w - 48, cat: 'weather', value: 'Sunny' });
  return { svg: s, knob: settingCardKnob(card) };
}

/** brightnessFull({v, t, wash, label}) - full-frame "Brightness fills the screen": inside the app, a giant sun icon
 *  that swells and spins with v, a huge slider, and a value readout; above v .7 the frame washes warm white (wash adds
 *  more on top, 0..1). Returns frame-space svg (use instead of insideApp for this beat). */
export function brightnessFull(o = {}) {
  const v = clamp(o.v ?? 0.3), t = o.t || 0, d = new Defs();
  let c = '';
  const sx = 960, sy = 400, sr = 90 + 90 * v;
  c += circle(sx, sy, sr * 2.6, { fill: d.rad([[0, '#FFE36A', 0.55 * v + 0.1], [1, '#FFE36A', 0]]) });
  for (let i = 0; i < 12; i++) {
    const a = (i / 12) * TAU + t * 0.6 + v * 1.5, r0 = sr * 1.2, r1 = sr * (1.55 + 0.35 * v);
    c += line(sx + Math.cos(a) * r0, sy + Math.sin(a) * r0, sx + Math.cos(a) * r1, sy + Math.sin(a) * r1, { ...st(i % 2 ? '#FFF3B0' : '#FFD43B', sr * 0.16) });
  }
  c += circle(sx, sy + sr * 0.08, sr, { fill: '#B8650A', opacity: 0.45 });
  c += circle(sx, sy, sr, { fill: d.lin(['#FFF8C4', '#FFD43B', '#FFA21F']), stroke: ink('#FFC23D'), strokeWidth: 5 });
  c += ellipse(sx - sr * 0.32, sy - sr * 0.42, sr * 0.36, sr * 0.15, { fill: '#FFFFFF', opacity: 0.85, transform: `rotate(-25 ${f(sx - sr * 0.32)} ${f(sy - sr * 0.42)})` });
  c += text(960, 132, esc(o.label || 'Brightness'), NUN(64, 900, '#FFFFFF', { textAnchor: 'middle' }));
  c += text(960, 186, rich(o.sub || 'Applies to: {everything|orange}'), NUN(32, 800, UI.sub, { textAnchor: 'middle' }));
  c += bigSlider({ x: 150, y: 780, w: 1620, v, iconL: 'sunSmall', iconR: 'sunBig', iconLs: 0.5, iconRs: 0.62, color: '#FFB21F', color2: '#FFF3A0', knobR: 92, railH: 64, endR: 58, knob: 'sun', rot: t * 40, ticks: 10, grab: o.grab ?? 1 });
  c += text(960, 960, `${Math.round(v * 100)}%`, LIL(110, '#FFE36A', { textAnchor: 'middle', stroke: '#5A3000', strokeWidth: 9, paintOrder: 'stroke', strokeLinejoin: 'round' }));
  let s = insideApp(c, { t, status: true, glare: 0.5, bg: { glow: '#FFC23D' } });
  const wash = clamp(seg(v, 0.7, 1) * 0.6 + (o.wash || 0));
  if (wash > 0.005) s += rect(-10, -10, W + 20, H + 20, { fill: d.rad([[0, '#FFFFFF', Math.min(1, wash * 1.6)], [0.6, '#FFF6D8', wash * 0.9], [1, '#FFE9B0', wash * 0.75]], 0.5, 0.37, 0.8) });
  return d + s;
}
/** brightness slider for the phone screen (screen space): a settingCard dressed as Brightness */
export function brightnessScreen(o = {}) {
  const v = clamp(o.v ?? 0.3);
  const card = { x: 24, y: 326, w: SCREEN.w - 48, cat: 'sun', label: 'Brightness', icon: 'brightness', color: '#FFAE1F', value: `{${Math.round(v * 100)}%|yellow}`, v, grab: o.grab, iconL: 'sunSmall', iconR: 'sunBig', iconLs: 0.5, iconRs: 0.62, color2: '#FFF3A0', knob: 'sun', rot: (o.t || 0) * 40, sub: 'Applies to: {everything|orange}' };
  let s = text(36, 300, 'DISPLAY', NUN(26, 900, UI.dim, { letterSpacing: 3 })) + settingCard(card);
  s += row({ x: 24, y: 792, w: SCREEN.w - 48, kind: 'toggle', cat: 'bedtime', label: 'Night mode', icon: 'moon', color: '#5C5CE0', k: o.night ?? 1 });
  s += row({ x: 24, y: 918, w: SCREEN.w - 48, cat: 'weather', value: 'Clear' });
  s += row({ x: 24, y: 1044, w: SCREEN.w - 48, cat: 'volume', kind: 'toggle', k: 0 });
  return { svg: s, knob: settingCardKnob(card) };
}

// =====================================================================================================================
// APP ICON, NOTIFICATION
// =====================================================================================================================
/** appIcon({cx, cy, size, rot, glow, badge, label, labelSize, shine, t}) - the REALITY SETTINGS app icon: an orange
 *  plastic squircle with a lip and the white gear. Every width scales with size, so it holds up in a zoom to the lens
 *  (size 1500+). glow 0..1 halo (radial gradient, no filter); badge = number on a red dot; shine 0..1 sweeps a glint
 *  across; rot spins the gear (degrees). */
export function appIcon(o = {}) {
  const { cx = 960, cy = 540, size = 200 } = o;
  const d = new Defs(), r = size * 0.27, x = cx - size / 2, y = cy - size / 2, lip = size * 0.07, rot = (o.rot ?? 0) + (o.t || 0) * (o.spin ?? 0);
  let s = '';
  if (o.glow) s += circle(cx, cy, size * 1.15, { fill: d.rad([[0, '#FFB070', 0.75 * o.glow], [0.45, UI.orange, 0.35 * o.glow], [1, UI.orange, 0]]) });
  s += path(rrPath(x, y + lip, size, size, r), { fill: shade(UI.orange2, -0.17) });
  s += path(rrPath(x, y, size, size, r), { fill: d.lin(['#FFA766', UI.orange, UI.orange2]) });
  s += path(rrPath(x + size * 0.035, y + size * 0.035, size * 0.93, size * 0.93, r * 0.88), { fill: 'none', stroke: '#FFFFFF', strokeWidth: size * 0.018, opacity: 0.3 });
  s += path(gearPath(cx, cy + size * 0.035, size * 0.35, size * 0.265, 9, rot - 90, 0.52), { fill: shade(UI.orange2, -0.22), opacity: 0.55 });
  s += path(gearPath(cx, cy, size * 0.35, size * 0.265, 9, rot - 90, 0.52), { fill: d.lin(['#FFFFFF', '#FFE9D8']), stroke: ink(UI.orange, 0.42), strokeWidth: size * 0.012 });
  s += circle(cx, cy, size * 0.115, { fill: d.lin([UI.orange, UI.orange2]), stroke: ink(UI.orange, 0.42), strokeWidth: size * 0.01 });
  s += path(rrPath(x + size * 0.15, y + size * 0.06, size * 0.7, size * 0.11, size * 0.055), { fill: '#FFFFFF', opacity: 0.4 });
  if (o.shine !== undefined && o.shine > 0 && o.shine < 1) {
    const clip = d.clip(path(rrPath(x, y, size, size, r)));
    const bx = lerp(x - size * 0.8, x + size * 1.3, o.shine);
    s += g(poly([[bx, y - 10], [bx + size * 0.22, y - 10], [bx - size * 0.3, y + size + 10], [bx - size * 0.52, y + size + 10]], { fill: '#FFFFFF', opacity: 0.45 }), { clipPath: clip });
  }
  s += path(rrPath(x, y, size, size + lip, r), { fill: 'none', stroke: ink(UI.orange), strokeWidth: Math.max(2.5, size * 0.03) });
  if (o.badge !== undefined && o.badge !== null && o.badge !== false) {
    const br = size * 0.17, bx = x + size - size * 0.06, by = y + size * 0.06;
    s += circle(bx, by + br * 0.1, br, { fill: '#7A0A1C' });
    s += circle(bx, by, br, { fill: d.lin(['#FF7A7E', UI.red, '#D41E3A']), stroke: '#FFFFFF', strokeWidth: br * 0.2 });
    s += text(bx, by + br * 0.42, esc(String(o.badge)), LIL(br * 1.2, '#FFFFFF', { textAnchor: 'middle' }));
  }
  if (o.label) s += text(cx, y + size + lip + (o.labelSize || size * 0.2) * 1.3, esc(o.label), NUN(o.labelSize || size * 0.2, 800, o.labelColor || '#FFFFFF', { textAnchor: 'middle' }));
  return d + s;
}

/** notifyCard({x, y, w, title, sub, note, time, rattle, t}, p) - "An app you never downloaded": a notification with the
 *  app icon, SETTINGS / for real life, a NEW pill, an OPEN button and the small print "Downloaded: never".
 *  rattle 0..1 = buzz amplitude (rotation + jitter + buzz marks, t seconds drives it). Height 200. */
export function notifyCard(o = {}, p) {
  const { x = 60, y = 60, w = 860, title = 'SETTINGS', sub = 'for {real life|orange}', note = 'Downloaded: never', time = 'now' } = o;
  const h = 200, d = new Defs(), t = o.t || 0, rt = clamp(o.rattle || 0);
  let s = glassCard(d, x, y, w, h, 58);
  s += appIcon({ cx: x + 106, cy: y + h / 2 - 6, size: 120, glow: 0.35 + 0.3 * rt, badge: o.badge ?? null, rot: t * 25 });
  const tx = x + 196;
  s += text(tx, y + 82, esc(title), LIL(60, '#FFFFFF', { letterSpacing: 1.5 }));
  const nx = tx + textW(title, 60, 'lil') + 12 + 18;
  s += path(rrPath(nx, y + 40, 86, 44, 16), { fill: d.lin([shade(UI.green, 0.06), shade(UI.green, -0.06)]), stroke: ink(UI.green), strokeWidth: 3 });
  s += text(nx + 43, y + 71, 'NEW', NUN(24, 900, '#FFFFFF', { textAnchor: 'middle', letterSpacing: 1.5 }));
  s += text(x + w - 230, y + 56, esc(time), NUN(24, 800, UI.dim, { textAnchor: 'end' }));
  s += text(tx, y + 130, rich(sub), NUN(40, 900, '#FFFFFF'));
  s += g(glyph('warning', '#FFC23D', UI.navy1), { transform: tr(tx + 14, y + 166, 0.26) });
  s += text(tx + 38, y + 175, esc(note), NUN(24, 800, UI.dim));
  s += button(x + w - 206, y + 62, 164, 80, 'OPEN', { tone: UI.orange, press: o.press || 0 });
  if (rt > 0) {
    const ang = rt * 3.5 * Math.sin(TAU * 21 * t), jx = rt * 10 * Math.sin(TAU * 17 * t + 1);
    let bz = '';
    for (const side of [-1, 1]) for (let i = 0; i < 2; i++) {
      const bx = side < 0 ? x - 26 - i * 30 : x + w + 26 + i * 30, by = y + h / 2;
      bz += path(`M${f(bx)} ${f(by - 46 - i * 18)}Q${f(bx + side * 18)} ${f(by)} ${f(bx)} ${f(by + 46 + i * 18)}`, { fill: 'none', ...st('#FFFFFF', 8 - i * 2), opacity: op(rt * (0.9 - i * 0.3)) });
    }
    s = g(s, { transform: `translate(${f(jx)} 0) rotate(${f(ang)} ${f(x + w / 2)} ${f(y + h / 2)})` }) + bz;
  }
  return popIn(d + s, x + 106, y + h / 2, p, { bbox: { x, y, w, h, r: 58 }, ringGrow: 46 });
}

// =====================================================================================================================
// UNDO: the button that cracks and falls, and the history panel
// =====================================================================================================================
function undoGeom(w, h, lip, seed) {
  const R = rng(seed);
  const ix = w * (0.04 + R() * 0.06), iy = -h * 0.1;
  const top = -h / 2 - lip - 14, bot = h / 2 + lip * 1.6 + 14;
  const T = [[ix + w * 0.03, top], [ix + w * 0.045 + (R() - 0.5) * 16, -h * 0.33], [ix - 8 + (R() - 0.5) * 10, -h * 0.2], [ix, iy],
    [ix - w * 0.05, h * 0.05], [ix + w * 0.025, h * 0.22], [ix - w * 0.03, h * 0.38], [ix - w * 0.01, bot]];
  const br = [-160, -112, -42, 22, 148, 200].map((a, i) => {
    const A = ((a + (R() - 0.5) * 20) * Math.PI) / 180, L = w * (0.12 + R() * 0.12), m = 0.45 + R() * 0.2, kink = (R() - 0.5) * 0.5;
    return [[ix, iy], [ix + Math.cos(A + kink) * L * m, iy + Math.sin(A + kink) * L * m * 0.7], [ix + Math.cos(A) * L, iy + Math.sin(A) * L * 0.7]];
  });
  return { I: [ix, iy], T, br, top, bot };
}
const polyLen = (P) => P.reduce((a, q, i) => (i ? a + Math.hypot(q[0] - P[i - 1][0], q[1] - P[i - 1][1]) : 0), 0);
const dPath = (P) => P.map((q, i) => (i ? 'L' : 'M') + f(q[0]) + ' ' + f(q[1])).join('');
function crackLines(P, k, wd) {
  if (k <= 0) return '';
  const L = polyLen(P), dash = { strokeDasharray: `${f(L * k)} ${f(L + 10)}` };
  return path(dPath(P), { fill: 'none', stroke: '#0B1030', strokeWidth: wd * 1.9, strokeLinejoin: 'round', strokeLinecap: 'round', opacity: 0.85, ...dash }) +
    path(dPath(P.map(([x, y]) => [x + 1.5, y - 1.5])), { fill: 'none', stroke: '#FFFFFF', strokeWidth: wd * 0.55, strokeLinejoin: 'round', strokeLinecap: 'round', opacity: 0.85, ...dash });
}
/** undoButton({cx, cy, w, h, label, tone, crack, fall, fallDist, rot, press, seed, scale})
 *  The big UNDO button. crack 0..1 runs a crack out from the impact point (main split first, branches after .3; from
 *  .85 the halves start to part); fall 0..1 drops the two halves off the screen under gravity (fallDist px, ease-in),
 *  spinning apart (rot degrees at fall 1) with a few glass chips. */
export function undoButton(o = {}) {
  const { cx = 960, cy = 540, w = 460, h = 156, label = 'UNDO', tone = '#2FA8F0' } = o;
  const d = new Defs(), lip = h * 0.13, r = h * 0.34, crack = clamp(o.crack || 0), fall = clamp(o.fall || 0);
  const press = clamp(o.press || 0), dy = press * lip * 0.85, sc = o.scale || 1;
  const x = -w / 2, y = -h / 2;
  let face = path(rrPath(x, y + lip, w, h, r), { fill: shade(tone, -0.2) });
  face += path(rrPath(x, y + dy, w, h, r), { fill: d.lin([shade(tone, 0.08), shade(tone, -0.05)]) });
  face += path(rrPath(x + h * 0.28, y + dy + h * 0.1, w - h * 0.56, h * 0.13, h * 0.065), { fill: '#FFFFFF', opacity: 0.38 });
  const fs = h * 0.44, lw = textW(label, fs, 'lil') + h * 0.62, lx = -lw / 2;
  face += g(glyph('undo', shade(tone, -0.3)), { transform: tr(lx + h * 0.22, dy + 4, h * 0.0042) });
  face += g(glyph('undo', '#FFFFFF'), { transform: tr(lx + h * 0.22, dy, h * 0.0042) });
  face += text(lx + h * 0.56, dy + fs * 0.36 + 4, esc(label), LIL(fs, shade(tone, -0.3), { opacity: 0.5, letterSpacing: 2 }));
  face += text(lx + h * 0.56, dy + fs * 0.36, esc(label), LIL(fs, '#FFFFFF', { letterSpacing: 2 }));
  face += path(rrPath(x, y, w, h + lip, r), { fill: 'none', stroke: ink(tone), strokeWidth: 4 });
  const G = undoGeom(w, h, lip, o.seed || 7);
  // cracks: the main split grows out from the impact both ways, then the branches
  let cr = '';
  if (crack > 0) {
    const iIdx = 3, up = G.T.slice(0, iIdx + 1).reverse(), down = G.T.slice(iIdx);
    const km = seg(crack, 0, 0.55);
    cr += crackLines(up, km, 4) + crackLines(down, km, 4);
    G.br.forEach((b, i) => { cr += crackLines(b, seg(crack, 0.3 + i * 0.07, 0.7 + i * 0.05), 3); });
    cr += circle(G.I[0], G.I[1], 7 * seg(crack, 0, 0.2), { fill: '#FFFFFF', opacity: 0.9 });
    cr = g(cr, { clipPath: d.clip(path(rrPath(x, y, w, h + lip, r))) });      // cracks live inside the plastic
  }
  const part = seg(crack, 0.85, 1) * 5;
  let s = '';
  if (fall <= 0 && part <= 0) s = face + cr;
  else {
    const big = w;
    const left = [[-big, G.top], ...G.T, [-big, G.bot]], right = [[big, G.top], ...G.T, [big, G.bot]];
    const cl = d.clip(poly(left)), cR = d.clip(poly(right));
    const dist = o.fallDist ?? 1100, rot = o.rot ?? 38, e = fall * fall;
    const half = (clip, sgn, k) => {
      const hx = sgn * w * 0.25, hy = 0, dx = sgn * (part + 70 * fall), yy = dist * e * k, rr = sgn * rot * fall * (k > 1 ? 0.8 : 1);
      return g(g(face + cr, { clipPath: clip }), { transform: `translate(${f(dx)} ${f(yy)}) rotate(${f(rr)} ${f(hx)} ${f(hy)})` });
    };
    s = half(cl, -1, 1) + half(cR, 1, 1.12);
    if (fall > 0) {
      const R = rng((o.seed || 7) + 99);
      for (let i = 0; i < 9; i++) {
        const vx = (R() - 0.5) * 700, vy = -250 - R() * 420, tt = fall * 0.9, sz = 8 + R() * 14;
        const px = G.I[0] + vx * tt, py = G.I[1] + vy * tt + 0.5 * 2600 * tt * tt;
        s += poly([[px, py - sz], [px + sz * 0.8, py + sz * 0.5], [px - sz * 0.7, py + sz * 0.6]], { fill: i % 2 ? '#FFFFFF' : shade(tone, 0.1), stroke: ink(tone), strokeWidth: 2, opacity: op(1 - fall * 0.6), transform: `rotate(${f(R() * 360 + fall * 500)} ${f(px)} ${f(py)})` });
      }
    }
  }
  return d + g(s, { transform: `translate(${f(cx)} ${f(cy)}) scale(${sc3(sc)})` });
}

// ---- UNDO HISTORY ----
export const HIST_DAY_COUNTS = [12, 40, 55, 60, 70, 95, 80];      // changes per day (Day 1..7), 412 in all
const HIST_ITEMS = [
  ['dog', 'Dog size', 'HOUSE'], ['trees', 'Trees', 'Upside down'], ['sun', 'Brightness', '100%'], ['gravity', 'Gravity', 'Moon'],
  ['volume', "Lily's volume", '0'], ['language', 'Language', 'Cat'], ['speed', 'Playback speed', '2x'], ['graphics', 'Graphics', 'Low'],
  ['weather', 'Weather', 'Snow'], ['homework', 'Homework', 'Done'], ['mondays', 'Mondays', 'Off'], ['bedtime', 'Bedtime', 'Never'],
  ['subtitles', 'Subtitles', 'Honest'], ['difficulty', 'Difficulty', 'Easy'], ['birds', 'Birdsong', 'Loud'], ['weather', 'Clouds', 'Pink'],
  ['gravity', 'Gravity', 'Bouncy'], ['speed', 'School day', '0.5x'], ['volume', "Kevin's blower", 'Muted'], ['dog', 'Cat size', 'Pocket'],
];
const HIST_CACHE = new Map();
/** the 419-item list (7 day headers + 412 changes), newest first; deterministic per seed */
export function historyItems(seed = 3) {
  if (HIST_CACHE.has(seed)) return HIST_CACHE.get(seed);
  const R = rng(seed), out = [];
  let n = 412, last = -1, last2 = -1;
  for (let day = 7; day >= 1; day--) {
    out.push({ head: true, day, count: HIST_DAY_COUNTS[day - 1] });
    for (let i = 0; i < HIST_DAY_COUNTS[day - 1]; i++) {
      let k = Math.floor(R() * HIST_ITEMS.length);
      if (k === last || k === last2) k = (k + 1 + Math.floor(R() * 5)) % HIST_ITEMS.length;   // no repeats back to back
      last2 = last; last = k;
      const it = day === 1 && i >= HIST_DAY_COUNTS[0] - 2 ? HIST_ITEMS[HIST_DAY_COUNTS[0] - 1 - i] : HIST_ITEMS[k];
      out.push({ day, n: n--, cat: it[0], label: it[1], value: it[2] });
    }
  }
  HIST_CACHE.set(seed, out);
  return out;
}
/** undoHistory({x, y, w, h, scroll, speed, seed, t, title}, p) - the UNDO HISTORY panel. scroll = list position in
 *  items (0 = newest at the top; 419 items incl. day headers); speed = items/s (drive it with the scroll derivative):
 *  above ~4 px/frame the list gets a vertical motion blur (filter region = the list viewport only) and white streaks.
 *  The header's day pill follows the day at the top of the view. */
export function undoHistory(o = {}, p) {
  const { x = 600, y = 80, w = 760, h = 920 } = o;
  const d = new Defs(), items = historyItems(o.seed ?? 3), N = items.length;
  const scroll = clamp(o.scroll ?? 0, 0, N - 1), pitch = 98, rh = 84;
  let s = glassCard(d, x, y, w, h, 46);
  s += iconTile('history', x + 78, y + 76, 76, '#5C6B9E');
  s += text(x + 136, y + 84, 'UNDO HISTORY', LIL(52, '#FFFFFF', { letterSpacing: 1 }));
  s += text(x + 138, y + 120, rich(o.sub || '{412|orange} changes · newest first'), NUN(26, 800, UI.sub));
  const topItem = items[Math.min(N - 1, Math.floor(scroll + 0.2))];
  const dcol = DAY_COLORS[(topItem.day - 1) % 7];
  const pw = 150, px = x + w - pw - 34;
  s += path(rrPath(px, y + 46, pw, 58, 29), { fill: d.lin([shade(dcol, 0.07), shade(dcol, -0.06)]), stroke: ink(dcol), strokeWidth: 3 });
  s += text(px + pw / 2, y + 85, `DAY ${topItem.day}`, LIL(34, '#FFFFFF', { textAnchor: 'middle', letterSpacing: 1 }));
  s += path(rrPath(x + 34, y + 146, w - 68, 4, 2), { fill: d.lin([[0, UI.orange, 0.9], [0.4, UI.rimHi, 0.5], [1, UI.rimHi, 0.0]], 'h') });
  // list viewport
  const vx = x + 26, vy = y + 164, vw = w - 26 - 52, vh = h - 164 - 26;
  const clip = d.clip(rect(vx, vy, vw, vh));
  const first = Math.floor(scroll), nVis = Math.ceil(vh / pitch) + 2;
  let list = '';
  for (let i = Math.max(0, first - 1); i < Math.min(N, first + nVis); i++) {
    const it = items[i], ry = vy + 8 + (i - scroll) * pitch;
    if (it.head) {
      const c = DAY_COLORS[(it.day - 1) % 7];
      list += path(rrPath(vx + 6, ry + 6, vw - 12, rh - 8, 24), { fill: '#060A1E', opacity: 0.6 });
      list += path(rrPath(vx + 6, ry, vw - 12, rh - 8, 24), { fill: d.lin([shade(c, 0.06), shade(c, -0.07)], 'h'), stroke: ink(c), strokeWidth: 3 });
      list += path(rrPath(vx + 30, ry + 6, vw - 60, 7, 3.5), { fill: '#FFFFFF', opacity: 0.35 });
      list += g(glyph(DAY_ICONS[(it.day - 1) % 7], '#FFFFFF', shade(c, -0.1)), { transform: tr(vx + 52, ry + (rh - 8) / 2, 0.42) });
      list += text(vx + 92, ry + 52, `DAY ${it.day}`, LIL(40, '#FFFFFF', { letterSpacing: 1.5, stroke: ink(c), strokeWidth: 5, paintOrder: 'stroke' }));
      list += text(vx + vw - 30, ry + 50, `${it.count} changes`, NUN(26, 900, '#FFFFFF', { textAnchor: 'end', opacity: 0.9 }));
    } else {
      const c = cat(it.cat);
      list += path(rrPath(vx + 6, ry + 5, vw - 12, rh - 8, 22), { fill: '#080C24', opacity: 0.85 });
      list += path(rrPath(vx + 6, ry, vw - 12, rh - 8, 22), { fill: d.lin([UI.row, UI.rowLo]) });
      list += path(rrPath(vx + 26, ry + 5, vw - 52, 6, 3), { fill: '#FFFFFF', opacity: 0.09 });
      list += iconTile(c.icon, vx + 50, ry + (rh - 8) / 2 - 2, 54, c.color);
      const lab = `${it.label} → {${it.value}}`, fs = Math.min(32, (vw - 230) / (textW(plain(lab), 1) || 1));
      list += text(vx + 92, ry + 49, rich(lab), NUN(fs, 900, '#FFFFFF'));
      list += text(vx + vw - 26, ry + 48, `#${it.n}`, NUN(24, 900, UI.dim, { textAnchor: 'end' }));
    }
  }
  const pxf = Math.abs(o.speed || 0) * pitch / 60;
  if (pxf > 4) {
    const sd = Math.min(30, pxf * 0.32);
    const fid = d.raw('vb', `<filter id="__ID__" filterUnits="userSpaceOnUse" x="${f(vx)}" y="${f(vy - 40)}" width="${f(vw)}" height="${f(vh + 80)}" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="0 ${f(sd)}" edgeMode="duplicate"/></filter>`);
    list = g(list, { filter: `url(#${fid})` });
    const R = rng(Math.floor(scroll * 3) + 17), k = clamp((pxf - 4) / 30);
    for (let i = 0; i < 9; i++) list += rect(vx + 20 + R() * (vw - 40), vy + R() * vh * 0.6, 3 + R() * 4, vh * (0.2 + R() * 0.4), { fill: '#FFFFFF', opacity: op(k * (0.15 + R() * 0.25)), rx: 3 });
  }
  s += g(list, { clipPath: clip });
  // soft fades at the viewport edges
  s += rect(vx, vy, vw, 36, { fill: d.lin([[0, UI.navy2, 0.95], [1, UI.navy2, 0]]) });
  s += rect(vx, vy + vh - 44, vw, 44, { fill: d.lin([[0, UI.navy1, 0], [1, UI.navy1, 0.95]]) });
  // scrollbar
  const sx = x + w - 34, th = Math.max(40, vh * 0.06), tpos = vy + (vh - th) * clamp(scroll / (N - 8));
  s += path(rrPath(sx - 5, vy, 10, vh, 5), { fill: '#070A1C', opacity: 0.6 });
  s += path(rrPath(sx - 5, tpos, 10, th, 5), { fill: d.lin([UI.orangeHi, UI.orange2]) });
  return popIn(d + s, x + w / 2, y + h / 2, p, { bbox: { x, y, w, h, r: 46 } });
}
/** list position (items) of a day's header in undoHistory, e.g. historyDayAt(1) = where Day 1 starts */
export function historyDayAt(day, seed = 3) { return historyItems(seed).findIndex((it) => it.head && it.day === day); }

// =====================================================================================================================
// COUNTER: odometer 1 -> 412
// =====================================================================================================================
/** counter({x, y, value, digits, label, speed, size}, p) - "Changes made by you:" + rolling odometer digits. value may
 *  be fractional: the ones wheel rolls continuously and each higher wheel turns only while the one below passes 9.
 *  speed = value units/s (adds a vertical smear to wheels turning faster than ~6 digits/s). (x, y) = top-left. */
export function counter(o = {}, p) {
  const { x = 0, y = 0, digits = 3, label = 'Changes made by {you|orange}:' } = o;
  const v = Math.max(0, o.value ?? 412), d = new Defs(), dw = 104, dh = 150, gap = 12, fs = 128;
  const innerW = digits * dw + (digits - 1) * gap, lw = textW(plain(label), 34);
  const w = Math.max(innerW, lw) + 84, h = 92 + dh + 34;
  let s = glassCard(d, x, y, w, h, 42);
  s += text(x + w / 2, y + 66, rich(label), NUN(34, 900, UI.sub, { textAnchor: 'middle' }));
  const x0 = x + (w - innerW) / 2, wy = y + 92;
  const face = d.lin(['#FFFFFF', '#E3E8F6']), drum = d.lin([[0, '#0B1030', 0.35], [0.22, '#0B1030', 0], [0.78, '#0B1030', 0], [1, '#0B1030', 0.4]]);
  for (let i = 0; i < digits; i++) {
    const pos = digits - 1 - i, P = 10 ** pos, wx = x0 + i * (dw + gap);
    const q = v / P, base = Math.floor(q) % 10;
    let frac;
    if (pos === 0) frac = v - Math.floor(v);
    else { const lower = v - Math.floor(v / P) * P; frac = lower > P - 1 ? lower - (P - 1) : 0; }
    const lead = pos > 0 && v < P;                      // leading zero: dimmed
    s += path(rrPath(wx, wy + 6, dw, dh, 22), { fill: '#05081A', opacity: 0.7 });
    s += path(rrPath(wx, wy, dw, dh, 22), { fill: face });
    const clip = d.clip(path(rrPath(wx, wy, dw, dh, 22)));
    const rate = Math.abs(o.speed || 0) / P, smear = clamp((rate - 6) / 20);
    const col = d.lin([UI.navy3, UI.navy0]);
    let wh = '';
    for (const [dd, off] of [[base, 0], [(base + 1) % 10, 1]]) {
      const ty = wy + dh / 2 + fs * 0.36 + (off - frac) * dh;
      const dim = lead && dd === 0 ? 0.22 : 1;
      if (smear > 0) for (const k of [-0.18, 0.18]) wh += text(wx + dw / 2, ty + k * dh, String(dd), LIL(fs, UI.navy2, { textAnchor: 'middle', opacity: op(0.3 * smear * dim) }));
      wh += text(wx + dw / 2, ty, String(dd), LIL(fs, col, { textAnchor: 'middle', opacity: op(dim * (1 - smear * 0.35)) }));
    }
    s += g(wh, { clipPath: clip });
    s += path(rrPath(wx, wy, dw, dh, 22), { fill: drum });
    s += path(rrPath(wx + 14, wy + 8, dw - 28, 9, 4.5), { fill: '#FFFFFF', opacity: 0.8 });
    s += rect(wx + 3, wy + dh / 2 - 1.5, dw - 6, 3, { fill: '#0B1030', opacity: 0.12 });
    s += path(rrPath(wx, wy, dw, dh, 22), { fill: 'none', stroke: '#070A1C', strokeWidth: 3.5 });
  }
  return popIn(d + s, x + w / 2, y + h / 2, p, { bbox: { x, y, w, h, r: 42 }, ringGrow: 40 });
}
export const counterSize = (o = {}) => { const digits = o.digits || 3; return { w: Math.max(digits * 104 + (digits - 1) * 12, textW(plain(o.label || 'Changes made by you:'), 34)) + 84, h: 276 }; };

// =====================================================================================================================
// MONTAGE: sliders and toggles fan across the screen
// =====================================================================================================================
const FAN_CATS = ['gravity', 'volume', 'dog', 'weather', 'speed', 'trees', 'language', 'sun', 'subtitles', 'graphics', 'birds', 'difficulty', 'mondays', 'bedtime', 'homework', 'parental'];
const FAN_VALS = ['Moon', null, 'HOUSE', '{Snow|cyan}', '2x', 'Flip', '{Cat|pink}', '100%', null, 'Low', null, 'Easy', 'Off', 'Never', 'Done', null];
/** fanMontage({cx, cy, p, count, seed, spread, scale, pivotY}) - settings rows and sliders burst out of a pivot below
 *  the frame (where the phone is) and fan across the whole screen on three arcs, staggered (each item ~40% of p),
 *  popping with overshoot and a gentle tilt; toggles flip on and sliders slide as they land. Frame space. */
export function fanMontage(o = {}) {
  const { cx = 960, count = 16, seed = 7, spread = 1, scale = 0.78 } = o;
  const p = clamp(o.p ?? 1), R = rng(seed), piv = [cx, o.pivotY ?? 1560];
  const rings = [760, 1060, 1360], per = [4, 6, 6];
  const items = [];
  let i = 0;
  rings.forEach((rad, ri) => {
    for (let j = 0; j < per[ri] && i < count; j++, i++) {
      const n = per[ri], u = n === 1 ? 0.5 : j / (n - 1);
      const span = [44, 50, 54][ri] * spread;
      const kindR = R(), ci = Math.floor(R() * FAN_CATS.length);
      items.push({ rad, ri, a: lerp(-span, span, u) + (R() - 0.5) * 5, kind: kindR < 0.35 ? 'toggle' : kindR < 0.6 ? 'slider' : 'value', ci, order: R() });
    }
  });
  // stagger by distance from the centre line so the fan opens outward
  items.sort((A, B) => Math.abs(A.a) - Math.abs(B.a) || A.ri - B.ri);
  let out = '';
  items.forEach((it, k) => {
    const st0 = (k / items.length) * 0.6, q = seg(p, st0, st0 + 0.4);
    if (q <= 0) return;
    const fly = ease.outCubic(clamp(q * 1.35)), a = it.a * ease.outBack(clamp(q * 1.2), 1.2), ar = (a * Math.PI) / 180;
    const px = piv[0] + Math.sin(ar) * it.rad * fly, py = piv[1] - Math.cos(ar) * it.rad * fly;
    const s = popScale(clamp(q * 1.3)) * scale * (1 - it.ri * 0.08), c = FAN_CATS[it.ci];
    let inner;
    if (it.kind === 'slider') {
      const d = new Defs();
      inner = d + path(rrPath(-360, -66, 720, 140, 30), { fill: '#080C24', opacity: 0.9, transform: 'translate(0 6)' }) +
        path(rrPath(-360, -66, 720, 140, 30), { fill: d.lin([UI.row, UI.rowLo]), stroke: '#0A0F2C', strokeWidth: 2.5 }) +
        slider({ x: -330, y: 4, w: 660, v: lerp(0.12, 0.88, ease.inOutCubic(seg(q, 0.3, 1))), iconL: cat(c).icon, iconR: cat(c).icon });
    } else inner = row({ x: -360, y: -52, w: 720, kind: it.kind, cat: c, label: cat(c).label, icon: cat(c).icon, color: cat(c).color, value: FAN_VALS[it.ci] || 'On', k: seg(q, 0.45, 0.85) });
    out += g(inner, { transform: `translate(${f(px)} ${f(py)}) rotate(${f(a * 0.3)}) scale(${sc3(s)})`, opacity: op(q * 4) });
  });
  return out;
}

// =====================================================================================================================
// TERMS: pages stacking up, I AGREE, welcome toast
// =====================================================================================================================
/** pageStack({cx, base, n, w, th, wobble, t, seed, depth}) - a stack of n paper pages standing on y = base (th px per
 *  page; 4,812 pages at th .25 = 1,200 px, past the ceiling). Drawn as up to 90 slabs with page-edge lines, a right
 *  side face and a top sheet with print; wobble 0..1 sways the tower (more at the top, lagging), t seconds. */
export function pageStack(o = {}) {
  const { cx = 960, base = 1000, w = 520, th = 0.25, t = 0, seed = 11, depth = 60 } = o;
  const n = Math.max(1, o.n ?? 400), wob = clamp(o.wobble || 0), d = new Defs(), R = rng(seed);
  const Ht = n * th, B = Math.min(90, Math.max(1, Math.ceil(n / 12))), bh = Ht / B, dk = depth;
  const paper = d.lin(['#FFFFFF', '#E6EBF6'], 'h'), side = d.lin(['#C9D1E8', '#AEB8D6'], 'v'), edge = '#8E9AC2';
  let s = '';
  let lastX = cx;
  for (let b = 0; b < B; b++) {
    const yb = base - (b + 1) * bh, hgt = (b + 1) * bh;
    const sway = wob * 70 * (hgt / 700) ** 1.6 * Math.sin(TAU * 0.7 * t - b * 0.05);
    const jx = (R() - 0.5) * 16, X = cx + jx + sway, L = X - w / 2, Rr = X + w / 2;
    s += poly([[Rr, yb + bh], [Rr, yb], [Rr + dk, yb - dk * 0.5], [Rr + dk, yb + bh - dk * 0.5]], { fill: side, stroke: edge, strokeWidth: 1.5, strokeLinejoin: 'round' });
    s += rect(L, yb, w, bh + 0.6, { fill: paper });
    const lines = Math.min(4, Math.floor(bh / 3));
    for (let k = 1; k <= lines; k++) s += line(L + 4, yb + (bh * k) / (lines + 1), Rr - 4, yb + (bh * k) / (lines + 1), { stroke: '#C3CBE3', strokeWidth: 1.2 });
    s += path(`M${f(L)} ${f(yb)}V${f(yb + bh)}M${f(Rr)} ${f(yb)}V${f(yb + bh)}`, { stroke: edge, strokeWidth: 2.5 });
    if (b === 0) s += line(L, yb + bh, Rr, yb + bh, { stroke: edge, strokeWidth: 3 });
    lastX = X;
  }
  // top sheet with print
  const T = base - Ht, L = lastX - w / 2, Rr = lastX + w / 2;
  s += poly([[L, T], [Rr, T], [Rr + dk, T - dk * 0.5], [L + dk, T - dk * 0.5]], { fill: '#FFFFFF', stroke: edge, strokeWidth: 2.5, strokeLinejoin: 'round' });
  for (let k = 0; k < 4; k++) {
    const yy = T - dk * 0.5 * ((k + 1) / 5), xs = L + dk * ((k + 1) / 5) + 30;
    s += line(xs, yy, xs + (w - 80) * (0.6 + 0.1 * (k % 3)), yy, { stroke: '#AEB7D3', strokeWidth: 3, strokeLinecap: 'round' });
  }
  s += line(L, T, Rr, T, { stroke: edge, strokeWidth: 2.5 });
  return d + s;
}

/** agreeButton({cx, cy, w, h, label, press, ripple, glow, t, R}, p) - the big green I AGREE button with a check.
 *  press 0..1 pushes it into its lip; ripple 0..1 sends three rings out to radius R (default 1500) behind it (the
 *  sub-boom: room, house, street - combine with fx.ripple for the frame-wide wave); glow pulses with t. */
export function agreeButton(o = {}, p) {
  const { cx = 960, cy = 600, w = 640, h = 184, label = 'I AGREE', t = 0 } = o;
  const d = new Defs(), tone = UI.green, press = clamp(o.press || 0), rip = clamp(o.ripple || 0), glw = o.glow ?? 0.7;
  const x = cx - w / 2, y = cy - h / 2, lip = h * 0.12, dy = press * lip * 0.85;
  let s = '';
  if (rip > 0 && rip < 1) for (let j = 0; j < 3; j++) {
    const q = clamp(rip * 1.35 - j * 0.17);
    if (q <= 0 || q >= 1) continue;
    const e = ease.outCubic(q), rr = lerp(w * 0.45, o.R ?? 1500, e);
    s += ellipse(cx, cy + lip / 2, rr, rr * 0.62, { fill: 'none', stroke: j ? '#FFFFFF' : '#7CF0B0', strokeWidth: f(lerp(34, 3, e)), opacity: op((1 - q) * 0.9) });
  }
  if (glw > 0) s += ellipse(cx, cy + lip / 2, w * 0.78, h * 1.3, { fill: d.rad([[0, '#7CF0B0', 0.55 * glw * (0.85 + 0.15 * Math.sin(TAU * 1.6 * t))], [1, tone, 0]]) });
  s += button(x, y, w, h, '', { tone, press, r: h * 0.36 });
  const fs = h * 0.42, lw = textW(label, fs, 'lil') + fs * 1.25, lx = cx - lw / 2;
  s += circle(lx + fs * 0.42, cy + dy + 3, fs * 0.5, { fill: shade(tone, -0.25), opacity: 0.6 });
  s += circle(lx + fs * 0.42, cy + dy, fs * 0.5, { fill: '#FFFFFF' });
  s += g(glyph('check', shade(tone, -0.12)), { transform: tr(lx + fs * 0.42, cy + dy + 2, fs * 0.0065) });
  s += text(lx + fs * 1.25, cy + dy + fs * 0.36 + 3, esc(label), LIL(fs, shade(tone, -0.3), { opacity: 0.5, letterSpacing: 2 }));
  s += text(lx + fs * 1.25, cy + dy + fs * 0.36, esc(label), LIL(fs, '#FFFFFF', { letterSpacing: 2, stroke: ink(tone), strokeWidth: 5, paintOrder: 'stroke' }));
  if (press > 0 && press < 1 && o.tap !== false) s += tapRing(cx + w * 0.1, cy + dy, press, '#FFFFFF');
  return popIn(d + s, cx, cy, p, { bbox: { x, y, w, h: h + lip, r: h * 0.36 }, ringGrow: 50, ringColor: '#C8FFD9' });
}

/** welcomeToast({x, y, title, sub, glow, t, slide, life}, p) - "Welcome to Reality Settings!" with the gear logo glowing
 *  and spinning (glow 0..1, t s); slide 0..1 slides it in from the left with overshoot (1 = in place). */
export function welcomeToast(o = {}, p) {
  const { x = 60, y = 60, title = 'Welcome to Reality Settings!', sub = 'Every setting. For {real life|orange}.', t = 0 } = o;
  const d = new Defs(), glw = clamp(o.glow ?? 1), h = 144, ttl = 46;
  const w = Math.max(textW(title, ttl), textW(plain(sub), 30, 'n800')) + 150 + 60;
  const sl = o.slide === undefined ? 1 : ease.outBack(clamp(o.slide), 1.6), offx = (1 - sl) * -(w + x + 60);
  let s = glassCard(d, x, y, w, h, h / 2);
  const ix = x + 74, iy = y + h / 2, pulse = 0.85 + 0.15 * Math.sin(TAU * 1.4 * t);
  s += circle(ix, iy, 92, { fill: d.rad([[0, '#FFD08A', 0.9 * glw * pulse], [0.5, UI.orange, 0.45 * glw], [1, UI.orange, 0]]) });
  for (let i = 0; i < 12; i++) {
    const a = (i / 12) * TAU + t * 0.8, r0 = 60, r1 = 74 + (i % 2) * 10;
    s += line(ix + Math.cos(a) * r0, iy + Math.sin(a) * r0, ix + Math.cos(a) * r1, iy + Math.sin(a) * r1, { ...st('#FFE0B0', 5), opacity: op(glw * 0.85) });
  }
  s += logo(ix, iy, 50, { rot: t * 40, glow: false });
  s += text(x + 146, y + 66, esc(title), NUN(ttl, 900, '#FFFFFF'));
  s += text(x + 146, y + 106, rich(sub), NUN(30, 800, UI.sub));
  if (o.life !== undefined) {
    s += path(rrPath(x + 140, y + h - 16, w - 210, 6, 3), { fill: '#070A1C', opacity: 0.6 });
    s += path(rrPath(x + 140, y + h - 16, Math.max(6, (w - 210) * clamp(o.life)), 6, 3), { fill: UI.orange });
  }
  return g(popIn(d + s, ix, iy, p, { bbox: { x, y, w, h, r: h / 2 }, ringGrow: 50 }), { transform: `translate(${f(offx)} 0)` });
}
export const welcomeToastWidth = (o = {}) => Math.max(textW(o.title || 'Welcome to Reality Settings!', 46), textW(plain(o.sub || 'Every setting. For real life.'), 30, 'n800')) + 210;

// =====================================================================================================================
// DAY 1 card slam (the hook's button, S01-L001 "Day one.")
// =====================================================================================================================
/** daySlam({cx, cy, day, p, t, scale, burst, flash}) - p 0..1 over the slam (~0.6 s): the card drops in from 2.8x
 *  (converging speed lines), hits at p .3 (squash, starburst, double shock ring, radial lines, sparkles), settles by .7.
 *  flash:true adds a 2-frame white hit around p .3 (skip it when the cardSlam transition already flashes). Frame space,
 *  transparent background. */
export function daySlam(o = {}) {
  const { cx = 960, cy = 540, day = 1, t = 0, scale = 1, seed = 5 } = o;
  const p = clamp(o.p ?? 1), hit = 0.3, after = seg(p, hit, 1);
  let k;
  if (p < hit) k = lerp(2.8, 1, ease.inCubic(p / hit));
  else if (p < 0.38) k = lerp(1, 0.92, ease.outQuad(seg(p, hit, 0.38)));
  else if (p < 0.52) k = lerp(0.92, 1.05, ease.inOutSine(seg(p, 0.38, 0.52)));
  else k = lerp(1.05, 1, ease.inOutSine(seg(p, 0.52, 0.72)));
  const col = DAY_COLORS[(day - 1) % 7];
  let s = '';
  if (p < hit) s += speedLines({ cx, cy, count: 40, r0: 420 * scale, r1: 1500, t: p * 2, width: 22, op: 0.7 * (p / hit) });
  if (p >= hit && o.burst !== false) {
    s += speedLines({ cx, cy, count: 44, r0: 380 * scale, r1: 1600, t: t, width: 26, op: 0.85 * (1 - seg(after, 0.3, 1) * 0.6) });
    s += starburst({ cx, cy, r: 520 * scale, points: 14, fill: o.burstColor || '#FFB21F', core: '#FFF3B0', seed: seed + day, rot: t * 6 }, seg(after, 0, 0.5));
    s += shockRing(cx, cy, 1000 * scale, seg(after, 0, 0.55), '#FFFFFF', 34) + shockRing(cx, cy, 760 * scale, seg(after, 0.06, 0.6), col, 24);
    s += sparkles({ x: cx - 700 * scale, y: cy - 420 * scale, w: 1400 * scale, h: 840 * scale, count: 18, seed: seed + 3, t, size: 34 * scale });
  }
  s += dayCard({ cx, cy, day, scale: k * scale * 0.95, gearRot: t * 40, tilt: p < hit ? -14 : lerp(-8, -3, ease.outCubic(seg(after, 0, 0.6))) });
  if (o.flash && p >= hit && p < hit + 0.06) s += rect(-20, -20, W + 40, H + 40, { fill: '#FFFFFF', opacity: op(0.7 * (1 - seg(p, hit, hit + 0.06))) });
  return s;
}

// =====================================================================================================================
// small helpers used above
// =====================================================================================================================
function crackOverlay(sx, sy, sw, sh, k, at, seed) {
  return crackedGlass({ cx: sx + at[0], cy: sy + at[1], r: Math.max(sw, sh) * 0.85, k, seed, box: [sx, sy, sw, sh] });
}
