// cast.js — the cast of "What If Real Life Had a SETTINGS MENU?" built on rig.js + face.js.
//   toon(id, { x, y, s, facing, pose:{armL, armR, foreL, foreR, legL, legR, head, lean, bob, handL, handR,
//              pigL, pigR, pony, tail}, face: 'preset' | {eyes, brows, mouth, ...}, look:[dx,dy], add:{...}, props:{L, R} })
// L / R are the screen-left / screen-right limbs in the front view. Angles in degrees: 0 hangs down, + swings
// outward/up (180 = straight up); fore bends the forearm relative to the upper arm (+ continues outward).
import { PAL, g, path, circle, ellipse, rect, text, grad, radial, shadeBand, stroke, tone, union, rrect, rtrap, capsule, taper,
  glossCapsule, glossBox, contactShadow, f1, spline, polyline, roundPoly, FONT_UI } from './style.js';
import { face as drawFace, mapFeature, heartPath, starPath, PRESETS as FACE_PRESETS_CACHE } from './face.js';
import { buildFigure, helmetPath, bandPaths, strands, wrapPoint, hairline, yawOf, headCenterY, figureHeight } from './rig.js';

const D2R = Math.PI / 180;
const cosd = (a) => Math.cos(a * D2R), sind = (a) => Math.sin(a * D2R);

// ---------- shared hair helpers ----------
function hairFront(spec, color, extraShapes = (ctx) => [], strandList = []) {
  return (ctx) => {
    const h = helmetPath(spec, ctx.head, ctx.yaw);
    const shapes = [{ d: h.d }, ...extraShapes(ctx)];
    return union(shapes, color, { sw: ctx.sw, box: [-56, -80, 56, 30] }) + strands(strandList, ctx.head, ctx.yaw, color, spec);
  };
}
// a round puff (pigtail / bun) made of overlapping lobes
function puffShapes(cx, cy, r) {
  const out = [{ d: `M${f1(cx - r)} ${f1(cy)}a${f1(r)} ${f1(r)} 0 1 0 ${f1(2 * r)} 0a${f1(r)} ${f1(r)} 0 1 0 ${f1(-2 * r)} 0Z` }];
  for (const [a, k] of [[-40, 0.55], [60, 0.5], [170, 0.52], [250, 0.48]]) {
    const x = cx + cosd(a) * r * 0.62, y = cy + sind(a) * r * 0.62, rr = r * k;
    out.push({ d: `M${f1(x - rr)} ${f1(y)}a${f1(rr)} ${f1(rr)} 0 1 0 ${f1(2 * rr)} 0a${f1(rr)} ${f1(rr)} 0 1 0 ${f1(-2 * rr)} 0Z` });
  }
  return out;
}
const rotPt = ([x, y], [cx, cy], deg) => { const c = cosd(deg), s = sind(deg); return [cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c]; };

// ---------- props ----------
function mug(hx, hy, side, sw, big = 1) {
  const w = 30 * big, h = 34 * big, inward = side === 'L' ? 1 : -1;
  const x = hx + inward * 13 * big - w / 2, y = hy - h * 0.55;
  const c = PAL.mug;
  const hxs = inward > 0 ? x : x + w;               // handle on the hand side
  let s = path(`M${f1(hxs)} ${f1(y + h * 0.22)}Q${f1(hxs - inward * 15 * big)} ${f1(y + h * 0.22)} ${f1(hxs - inward * 15 * big)} ${f1(y + h * 0.5)}Q${f1(hxs - inward * 15 * big)} ${f1(y + h * 0.8)} ${f1(hxs)} ${f1(y + h * 0.78)}`, { fill: 'none', stroke: stroke(c), strokeWidth: f1(9 * big), strokeLinecap: 'round' })
    + path(`M${f1(hxs)} ${f1(y + h * 0.22)}Q${f1(hxs - inward * 15 * big)} ${f1(y + h * 0.22)} ${f1(hxs - inward * 15 * big)} ${f1(y + h * 0.5)}Q${f1(hxs - inward * 15 * big)} ${f1(y + h * 0.8)} ${f1(hxs)} ${f1(y + h * 0.78)}`, { fill: 'none', stroke: '#F1F2F8', strokeWidth: f1(9 * big - sw * 2), strokeLinecap: 'round' });
  s += path(rrect(x, y, w, h, 6 * big), { fill: grad(c, 'd', { up: 0.0, down: 0.1 }), stroke: stroke(c), strokeWidth: f1(sw), strokeLinejoin: 'round' });
  s += ellipse(x + w / 2, y + 2, w / 2 - 2, 3.4 * big, { fill: '#7A4A2E', stroke: stroke(c), strokeWidth: f1(sw * 0.6) });
  const tc = '#3F6FD8';
  s += text(x + w / 2, y + h * 0.42, "WORLD'S", { fontFamily: FONT_UI, fontWeight: 800, fontSize: f1(5.2 * big), fill: tc, textAnchor: 'middle' })
    + text(x + w / 2, y + h * 0.62, 'OKAYEST', { fontFamily: FONT_UI, fontWeight: 800, fontSize: f1(5.2 * big), fill: '#E2404A', textAnchor: 'middle' })
    + text(x + w / 2, y + h * 0.84, 'DAD', { fontFamily: FONT_UI, fontWeight: 800, fontSize: f1(7.2 * big), fill: tc, textAnchor: 'middle' });
  s += path(`M${f1(x + w * 0.16)} ${f1(y + h * 0.2)}L${f1(x + w * 0.16)} ${f1(y + h * 0.75)}`, { stroke: '#FFFFFF', strokeWidth: f1(2.4 * big), strokeLinecap: 'round', opacity: 0.9 });
  // steam
  s += path(`M${f1(x + w * 0.4)} ${f1(y - 6)}q-4 -6 0 -11t0 -11`, { fill: 'none', stroke: '#FFFFFF', strokeWidth: f1(2.6 * big), strokeLinecap: 'round', opacity: 0.7 });
  return s;
}
function blower(hx, hy, side, sw) {
  const out = side === 'L' ? -1 : 1, c = PAL.blower, dk = '#3A3F52';
  const bx = hx - 4 * out, by = hy + 6;
  // tube from the body toward the ground, outward
  const t0 = [bx + out * 20, by + 34], t1 = [bx + out * 96, by + 92];
  let s = path(taper(t0[0], t0[1], t1[0], t1[1], 11, 7.5), { fill: grad('#E9EBF2', 'd'), stroke: stroke('#E9EBF2'), strokeWidth: f1(sw), strokeLinejoin: 'round' });
  s += path(capsule(t1[0] - out * 6, t1[1] - 4, t1[0] + out * 4, t1[1] + 3, 17), { fill: grad(dk, 'd'), stroke: stroke(dk), strokeWidth: f1(sw) });
  s += glossCapsule(t0[0], t0[1], t1[0], t1[1], 18, { op: 0.45, thin: false });
  // handle loop (held)
  s += path(`M${f1(bx - 18)} ${f1(by + 14)}Q${f1(bx - 18)} ${f1(by - 10)} ${f1(bx)} ${f1(by - 10)}Q${f1(bx + 18)} ${f1(by - 10)} ${f1(bx + 18)} ${f1(by + 14)}`, { fill: 'none', stroke: stroke(dk), strokeWidth: f1(10 + sw * 2), strokeLinecap: 'round' })
    + path(`M${f1(bx - 18)} ${f1(by + 14)}Q${f1(bx - 18)} ${f1(by - 10)} ${f1(bx)} ${f1(by - 10)}Q${f1(bx + 18)} ${f1(by - 10)} ${f1(bx + 18)} ${f1(by + 14)}`, { fill: 'none', stroke: dk, strokeWidth: 10, strokeLinecap: 'round' });
  // body
  s += path(rrect(bx - 34, by + 8, 68, 44, 16), { fill: grad(c, 'd'), stroke: stroke(c), strokeWidth: f1(sw), strokeLinejoin: 'round' });
  s += path(rrect(bx - 34 + (out < 0 ? 40 : 0), by + 8, 28, 44, 14), { fill: grad(dk, 'd'), stroke: stroke(dk), strokeWidth: f1(sw), strokeLinejoin: 'round' });
  for (let i = 0; i < 3; i++) s += path(`M${f1(bx - 34 + (out < 0 ? 46 : 6) + i * 7)} ${f1(by + 18)}v24`, { stroke: tone(dk, 0.12), strokeWidth: 2.6, strokeLinecap: 'round' });
  s += path(`M${f1(bx - 22 + (out > 0 ? 30 : 0))} ${f1(by + 16)}L${f1(bx + 2 + (out > 0 ? 30 : 0))} ${f1(by + 16)}`, { stroke: '#FFFFFF', strokeOpacity: 0.5, strokeWidth: 4, strokeLinecap: 'round' });
  s += circle(bx + (out > 0 ? 18 : -18) * -1, by + 38, 5, { fill: '#FFD43B', stroke: stroke('#FFD43B'), strokeWidth: f1(sw * 0.6) });
  return s;
}
function phone(hx, hy, side, sw) {
  const w = 24, h = 40, x = hx - w / 2 + (side === 'L' ? 6 : -6), y = hy - h * 0.7;
  let s = path(rrect(x, y, w, h, 6), { fill: grad('#2B3150', 'd'), stroke: stroke('#2B3150'), strokeWidth: f1(sw), strokeLinejoin: 'round' });
  s += path(rrect(x + 3, y + 3.5, w - 6, h - 7, 3.5), { fill: grad('#5B8CFF', 'v') });
  s += gearPath(x + w / 2, y + h * 0.42, 6.2, '#FFFFFF');
  return s;
}
function labeler(hx, hy, side, sw) {
  const w = 22, h = 32, x = hx - w / 2, y = hy - h * 0.72, c = '#FFD43B';
  let s = path(`M${f1(x + 6)} ${f1(y + 2)}L${f1(x + 7)} ${f1(y - 12)}L${f1(x + 15)} ${f1(y - 12)}L${f1(x + 16)} ${f1(y + 2)}Z`, { fill: '#FFFFFF', stroke: stroke('#FFFFFF'), strokeWidth: f1(sw * 0.7), strokeLinejoin: 'round' });
  s += path(rrect(x, y, w, h, 7), { fill: grad(c, 'd'), stroke: stroke(c), strokeWidth: f1(sw), strokeLinejoin: 'round' });
  s += path(rrect(x + 4, y + 5, w - 8, 9, 2.5), { fill: grad('#2E3A55', 'v') }) + path(`M${f1(x + 6)} ${f1(y + 9.5)}h7`, { stroke: '#7CF0B0', strokeWidth: 1.8, strokeLinecap: 'round' });
  for (const [i, j] of [[0, 0], [1, 0], [0, 1], [1, 1]]) s += circle(x + 7.5 + i * 7, y + 20 + j * 6, 2.2, { fill: tone(c, -0.18) });
  return s;
}
export function gearPath(cx, cy, r, fill, hole = true) {
  const n = 8, pts = [];
  for (let i = 0; i < n * 4; i++) {
    const a = ((i / (n * 4)) * 360 - 90 + 360 / n / 8) * D2R, rr = (Math.floor(i / 2) % 2 === 0) ? r : r * 0.74;
    pts.push([cx + Math.cos(a) * rr, cy + Math.sin(a) * rr]);
  }
  const d = polyline(pts) + (hole ? `M${f1(cx - r * 0.34)} ${f1(cy)}a${f1(r * 0.34)} ${f1(r * 0.34)} 0 1 0 ${f1(r * 0.68)} 0a${f1(r * 0.34)} ${f1(r * 0.34)} 0 1 0 ${f1(-r * 0.68)} 0Z` : '');
  return path(d, { fill, fillRule: 'evenodd', stroke: fill, strokeWidth: f1(r * 0.12), strokeLinejoin: 'round' });
}
function drawProp(kind, { hand, side, sw, dir }) {
  const [hx, hy] = hand;
  if (kind === 'mug') return { behind: mug(hx, hy, side, sw) };
  if (kind === 'blower') return { behind: blower(hx, hy, side, sw) };
  if (kind === 'phone') return { behind: phone(hx, hy, side, sw) };
  if (kind === 'labeler') return { behind: labeler(hx, hy, side, sw) };
  void dir; return {};
}

// ---------- shared clothing bits ----------
const halfAt = (ctx, y) => { const t = (y - ctx.torsoTop) / (ctx.torsoBot - ctx.torsoTop); return (ctx.wt + (ctx.wb - ctx.wt) * t) / 2; };
function ribBand(ctx, color, h = 11) {
  const y0 = ctx.torsoBot - h, hw0 = halfAt(ctx, y0), hw1 = ctx.wb / 2;
  const d = roundPoly([[-hw0, y0, 2], [hw0, y0, 2], [hw1, ctx.torsoBot, ctx.d.torso.rb], [-hw1, ctx.torsoBot, ctx.d.torso.rb]]);
  return path(d, { fill: grad(color, 'd'), stroke: stroke(color), strokeWidth: f1(ctx.sw * 0.9), strokeLinejoin: 'round' });
}

// ======================================================================
// SAM — 12, orange hoodie with a white gear, orange headphones round his neck, messy chestnut hair + cowlick
// ======================================================================
const SAM_HAIR = {
  t: 4.5, crown: 5, height: 22,
  tips: [[-2, 24], [-1.62, 26, 4], [-1.3, 22, 4], [-1.1, 14, 4], [-0.93, -2, 6, 0.8], [-0.72, -18, 8, 0.75], [-0.46, -22, 9, 0.7], [-0.17, -24, 9, 0.7],
    [0.12, -22, 9, 0.7], [0.42, -21, 8, 0.7], [0.7, -14, 6, 0.8], [0.92, -2, 5], [1.1, 14, 4], [1.3, 22, 4], [1.62, 26, 4], [2, 24]],
};
const SAM = {
  name: 'SAM', color: '#FF7A3D',
  skin: PAL.skinCool,
  dims: { head: { w: 120, h: 112, r: 0.25 }, torso: { h: 118, wt: 104, wb: 112, rt: 28, rb: 18 }, arm: { w: 30, up: 50, fore: 46, hand: 15.5 }, leg: { w: 38, len: 104, hip: 24 }, shoe: { w: 50, h: 26 } },
  faceOpts: { eyeX: 19, eyeY: 6, mouthY: 28 },
  top: { color: PAL.samHoodie, sleeve: true, cuff: PAL.samHoodieDark },
  pants: { color: PAL.samJeans },
  shoes: { color: '#F6F7FB', sole: '#D3D8E8', accent: '#FF8A1F' },
  hair: {
    height: 26,
    front: hairFront(SAM_HAIR, PAL.samHair, (ctx) => {
      const cx = 4 * cosd(ctx.yaw) + 6 * sind(ctx.yaw);
      return [{ d: `M${f1(cx - 9)} -52Q${f1(cx - 6)} -70 ${f1(cx + 13)} -77Q${f1(cx + 5)} -66 ${f1(cx + 9)} -51Z` }];
    }, [{ y: -44, u0: -0.62, u1: 0.55, amp: 2.2, waves: 2.5 }, { y: -35, u0: -0.82, u1: 0.72, amp: 2.4, waves: 3 }, { follow: 7.5, u0: -0.85, u1: 0.8, amp: 0, dark: true, w: 3, op: 0.8 }]),
  },
  decor: {
    torso(ctx) {
      const { torsoTop: T, torsoBot: B, sw, back, tm } = ctx;
      let s = '';
      const c = PAL.samHoodie, dk = tone(c, -0.08, 1.05);
      if (back) {
        // the hood lying on the upper back
        const hw = ctx.wt * 0.36;
        s += path(`M${f1(-hw)} ${f1(T + 6)}Q${f1(-hw)} ${f1(T + 52)} 0 ${f1(T + 58)}Q${f1(hw)} ${f1(T + 52)} ${f1(hw)} ${f1(T + 6)}Z`, { fill: grad(dk, 'd'), stroke: stroke(c), strokeWidth: f1(sw), strokeLinejoin: 'round' });
        s += path(`M${f1(-hw * 0.6)} ${f1(T + 14)}Q0 ${f1(T + 40)} ${f1(hw * 0.6)} ${f1(T + 14)}`, { fill: 'none', stroke: stroke(c), strokeWidth: f1(sw * 0.7), strokeLinecap: 'round', opacity: 0.6 });
        return s + ribBand(ctx, dk);
      }
      // kangaroo pocket
      const p = tm(0), pw = ctx.wt * 0.62 * Math.max(0.55, p.k), py0 = B - 44, py1 = B - 12;
      s += path(roundPoly([[p.x - pw * 0.4, py0, 6], [p.x + pw * 0.4, py0, 6], [p.x + pw * 0.52, py1, 4], [p.x - pw * 0.52, py1, 4]]), { fill: grad(tone(c, -0.025), 'd'), stroke: stroke(c), strokeWidth: f1(sw * 0.8), strokeLinejoin: 'round' });
      s += path(`M${f1(p.x - pw * 0.4)} ${f1(py0 + 2)}Q${f1(p.x - pw * 0.5)} ${f1(py0 + 14)} ${f1(p.x - pw * 0.52)} ${f1(py1 - 2)}`, { fill: 'none', stroke: stroke(c), strokeWidth: f1(sw * 0.6), opacity: 0.5 });
      // gear logo
      const lg = tm(0);
      s += g(gearPath(0, 0, 15, '#FFFFFF'), { transform: `translate(${f1(lg.x)} ${f1(T + 48)}) scale(${f1(Math.max(0.35, lg.k))} 1)` });
      // drawstrings
      for (const sd of [-1, 1]) {
        const m = tm(sd * 11); if (m.k < 0.25) continue;
        s += path(`M${f1(m.x)} ${f1(T + 6)}Q${f1(m.x + sd * 2)} ${f1(T + 20)} ${f1(m.x + sd * 1)} ${f1(T + 32)}`, { fill: 'none', stroke: stroke('#FFFFFF'), strokeWidth: f1(4.6 + sw), strokeLinecap: 'round' })
          + path(`M${f1(m.x)} ${f1(T + 6)}Q${f1(m.x + sd * 2)} ${f1(T + 20)} ${f1(m.x + sd * 1)} ${f1(T + 32)}`, { fill: 'none', stroke: '#F4F5FA', strokeWidth: 4.6, strokeLinecap: 'round' })
          + path(capsule(m.x + sd * 1, T + 30, m.x + sd * 1, T + 37, 6), { fill: '#9AA3BC', stroke: stroke('#9AA3BC'), strokeWidth: f1(sw * 0.6) });
      }
      return s + ribBand(ctx, dk);
    },
    neck(ctx) { return phonesLayer(ctx, false); },
    neckFront(ctx) { return phonesLayer(ctx, true); },
  },
  props: {},
};
// headphones resting round the neck: cups either side of the chin; band behind the neck (seen from the back)
function phonesLayer(ctx, front) {
  const { torsoTop: T, sw, yaw, back } = ctx, c = PAL.phones, dk = '#C9561A';
  let s = '';
  if (back) {
    if (!front) return '';
    return path(`M-44 ${f1(T - 6)}Q0 ${f1(T + 10)} 44 ${f1(T - 6)}`, { fill: 'none', stroke: stroke(c), strokeWidth: f1(10 + sw * 2), strokeLinecap: 'round' })
      + path(`M-44 ${f1(T - 6)}Q0 ${f1(T + 10)} 44 ${f1(T - 6)}`, { fill: 'none', stroke: grad(c, 'v', { box: [-44, T - 10, 44, T + 10] }), strokeWidth: 10, strokeLinecap: 'round' });
  }
  for (const sd of [-1, 1]) {
    const a = (sd * 64 + yaw) * D2R, x = 46 * Math.sin(a), z = Math.cos(a);
    if ((z > -0.05) !== front) continue;
    const k = Math.max(0.42, Math.abs(Math.cos(a)) * 0.5 + 0.5);
    const cy = T + 4;
    s += g(
      path(rrect(-15, -18, 30, 36, 13), { fill: grad(c, 'd'), stroke: stroke(c), strokeWidth: f1(sw), strokeLinejoin: 'round' })
      + path(rrect(-9.5, -12, 19, 24, 8), { fill: grad(tone(c, 0.06), 'd'), stroke: stroke(c), strokeWidth: f1(sw * 0.6) })
      + path('M-9 -12L-9 6', { stroke: '#FFFFFF', strokeOpacity: 0.5, strokeWidth: 3.2, strokeLinecap: 'round' })
      + path(`M${sd * 13} -14Q${sd * 18} -26 ${sd * 14} -34`, { fill: 'none', stroke: dk, strokeWidth: 7, strokeLinecap: 'round' }),
      { transform: `translate(${f1(x)} ${f1(cy)}) rotate(${f1(sd * 14)}) scale(${f1(k)} 1)` });
  }
  return s;
}

// ======================================================================
// LILY — 6, pink overalls over a yellow tee, springy pigtail puffs, gap tooth, freckles
// ======================================================================
const LILY_HAIR = {
  t: 4, crown: 4, height: 16,
  tips: [[-2, 20], [-1.4, 18], [-1.08, 10, 3], [-0.9, -14, 3], [-0.62, -20, 4], [-0.3, -22, 4], [0.02, -22, 4], [0.34, -21, 4], [0.64, -19, 3], [0.9, -12, 3], [1.08, 10, 3], [1.4, 18], [2, 20]],
};
function lilyPuffs(ctx, front) {
  const { yaw, pose, sw } = ctx, color = PAL.lilyHair;
  let s = '';
  for (const sd of [-1, 1]) {
    const u = sd * 1.02, a = (u * 90 + yaw) * D2R, z = Math.cos(a);
    if ((z > -0.02) !== front) continue;
    const ax = 50 * Math.sin(a), ay = -30;
    const spring = (sd < 0 ? pose.pigL : pose.pigR) || 0;
    const outx = Math.sin(a) >= 0 ? 1 : -1;
    const c0 = rotPt([ax + outx * 16, ay - 6], [ax, ay], spring * outx);
    const shapes = puffShapes(c0[0], c0[1], 15.5);
    s += union(shapes, color, { sw, box: [c0[0] - 18, c0[1] - 18, c0[0] + 18, c0[1] + 18] });
    s += path(`M${f1(c0[0] - 7)} ${f1(c0[1] - 8)}Q${f1(c0[0] - 2)} ${f1(c0[1] - 12)} ${f1(c0[0] + 4)} ${f1(c0[1] - 10)}`, { fill: 'none', stroke: tone(color, 0.09), strokeWidth: 3.2, strokeLinecap: 'round' });
    const tie = rotPt([ax + outx * 3, ay - 1], [ax, ay], spring * outx);
    s += circle(tie[0], tie[1], 5.5, { fill: grad('#FFD43B', 'd'), stroke: stroke('#FFD43B'), strokeWidth: f1(sw * 0.8) });
  }
  return s;
}
const LILY = {
  name: 'LILY', color: '#FF6FAE',
  skin: PAL.skinCool,
  dims: { head: { w: 114, h: 106, r: 0.27 }, torso: { h: 82, wt: 86, wb: 96, rt: 24, rb: 16, shoulder: 20 }, arm: { w: 25, up: 36, fore: 33, hand: 13.5 }, leg: { w: 32, len: 64, hip: 20 }, shoe: { w: 42, h: 22 } },
  faceOpts: { eyeX: 19, eyeY: 7, eyeR: 13, mouthY: 28.5, gap: true, freckles: true },
  top: { color: PAL.lilyTee, sleeve: true, sleeveLen: 0.55, sleeveW: 1.16 },
  pants: { color: PAL.lilyOveralls },
  shoes: { color: '#F2475E', sole: '#FFFFFF' },
  hair: {
    height: 18,
    behind: (ctx) => lilyPuffs(ctx, false),
    front: (ctx) => hairFront(LILY_HAIR, PAL.lilyHair, () => [], [{ y: -40, u0: -0.6, u1: 0.5, amp: 1.8, waves: 2 }, { follow: 7, u0: -0.8, u1: 0.8, amp: 0, dark: true, w: 2.8, op: 0.7 }])(ctx) + lilyPuffs(ctx, true),
  },
  decor: {
    torso(ctx) {
      const { torsoTop: T, torsoBot: B, sw, back, tm } = ctx, c = PAL.lilyOveralls;
      const yW = B - 26, hw0 = halfAt(ctx, yW), hw1 = ctx.wb / 2;
      const m = tm(0), bw = ctx.wt * 0.56 * Math.max(0.5, m.k);
      const shapes = [{ d: roundPoly([[-hw0, yW, 3], [hw0, yW, 3], [hw1, B, ctx.d.torso.rb], [-hw1, B, ctx.d.torso.rb]]) }];
      if (!back) shapes.push({ d: rrect(m.x - bw / 2, T + 30, bw, yW - T - 26, 8) });
      let s = union(shapes, c, { sw, box: [-hw1, T + 30, hw1, B] });
      // straps
      for (const sd of [-1, 1]) {
        const top = tm(sd * ctx.d.torso.wt * 0.3), bot = back ? tm(sd * ctx.d.torso.wt * 0.12) : { x: m.x + sd * bw * 0.36, k: 1 };
        if (top.k < 0.2 && !back) continue;
        const y1 = back ? yW : T + 34;
        s += path(capsule(top.x, T - 2, bot.x, y1, 10), { fill: grad(c, 'd'), stroke: stroke(c), strokeWidth: f1(sw * 0.9) });
        if (!back) s += circle(bot.x, y1 - 1, 4.6, { fill: grad('#FFD43B', 'd'), stroke: stroke('#FFD43B'), strokeWidth: f1(sw * 0.6) });
      }
      if (!back) {
        s += g(path(heartPath(0.62), { fill: grad('#FFFFFF', 'd'), stroke: stroke(c), strokeWidth: 1.6 }), { transform: `translate(${f1(m.x)} ${f1(T + 48)}) scale(${f1(Math.max(0.4, m.k))} 1)` });
        s += path(`M${f1(m.x - bw * 0.3)} ${f1(T + 37)}L${f1(m.x + bw * 0.3)} ${f1(T + 37)}`, { stroke: '#FFFFFF', strokeOpacity: 0.35, strokeWidth: 2.4, strokeLinecap: 'round' });
      }
      return s;
    },
  },
};

// ======================================================================
// MOM — purple cardigan, bouncy high ponytail, glasses pushed up, label maker in her pocket
// ======================================================================
const MOM_HAIR = {
  t: 4.5, crown: 6, height: 22,
  tips: [[-2, 26], [-1.4, 25], [-1.08, 20, 3], [-0.92, -4, 4, 0.8], [-0.74, -24, 4], [-0.42, -29, 3, 1.3], [-0.05, -27, 5, 1.5], [0.32, -22, 6, 1.5], [0.66, -14, 6, 1.4], [0.92, 2, 4], [1.08, 20, 3], [1.4, 25], [2, 26]],
};
function momPony(ctx, front) {
  const { yaw, pose, sw } = ctx, color = PAL.momHair;
  const a = (2 * 90 + yaw) * D2R, z = Math.cos(a);
  if ((z > 0.05) !== front) return '';
  const sn = Math.sin(yaw * D2R);
  const dir = Math.abs(sn) > 0.2 ? -Math.sign(sn) : (Math.cos(yaw * D2R) > 0 ? 1 : -1);
  const ax = 48 * Math.sin(a) * 0.9, ay = -40;
  const sp = (pose.pony || 0) * dir;
  const P = (x, y) => rotPt([ax + dir * x, ay + y], [ax, ay], sp);
  const pts = [P(-2, -8), P(22, -22), P(48, -18), P(62, 4), P(62, 32), P(52, 56), P(44, 66), P(46, 46), P(42, 22), P(30, 6), P(8, 6)];
  let s = union([{ d: spline(pts, { closed: true, sharp: new Set([6]) }) }], color, { sw, box: [ax - 70, ay - 30, ax + 70, ay + 70] });
  const hl = [P(26, -12), P(46, -6), P(54, 14), P(52, 34)];
  s += path(spline(hl), { fill: 'none', stroke: tone(color, 0.09), strokeWidth: 3.4, strokeLinecap: 'round' });
  const sc = P(4, -1);
  s += g(path(rrect(-8, -11, 16, 22, 7), { fill: grad('#FF6FAE', 'd'), stroke: stroke('#FF6FAE'), strokeWidth: f1(sw * 0.8) }), { transform: `translate(${f1(sc[0])} ${f1(sc[1])}) rotate(${f1(-30 * dir + sp)})` });
  return s;
}
const MOM = {
  name: 'MOM', color: '#9B6CF0',
  skin: PAL.skinCool,
  dims: { head: { w: 116, h: 108, r: 0.25 }, torso: { h: 122, wt: 96, wb: 106, rt: 26, rb: 16 }, arm: { w: 27, up: 54, fore: 50, hand: 15 }, leg: { w: 34, len: 112, hip: 21 }, shoe: { w: 42, h: 21 } },
  faceOpts: { eyeX: 19, eyeY: 6, eyeR: 12.2, mouthY: 28, lashes: true },
  top: { color: PAL.momCardigan, sleeve: true, cuff: tone(PAL.momCardigan, 0.07) },
  pants: { color: PAL.momPants },
  shoes: { color: '#5A3A72', sole: null },
  hair: {
    height: 26,
    behind: (ctx) => momPony(ctx, false),
    front: (ctx) => {
      let s = hairFront(MOM_HAIR, PAL.momHair, () => [], [{ y: -42, u0: -0.7, u1: 0.4, amp: 2, waves: 2 }, { y: -34, u0: -0.55, u1: 0.75, amp: 2.2, waves: 2.5 }, { follow: 7, u0: -0.7, u1: 0.85, amp: 0, dark: true, w: 2.8, op: 0.7 }])(ctx);
      s += momPony(ctx, true);
      if (!ctx.back) {
        // glasses pushed up on her head
        const fr = '#4B2E6E';
        let gl = '';
        for (const sd of [-1, 1]) {
          const m = mapFeature(sd * 17, ctx.yaw); if (m.k < 0.25) continue;
          gl += g(path(rrect(-11, -7, 22, 14, 6), { fill: '#DDEBFF', fillOpacity: 0.55, stroke: fr, strokeWidth: 3.2 }) + path('M-6 -3L-1 -5', { stroke: '#FFFFFF', strokeWidth: 2.2, strokeLinecap: 'round' }), { transform: `translate(${f1(m.x)} -47) scale(${f1(m.k)} 1)` });
        }
        const m0 = mapFeature(0, ctx.yaw);
        gl += path(`M${f1(m0.x - 6)} -48Q${f1(m0.x)} -51 ${f1(m0.x + 6)} -48`, { fill: 'none', stroke: fr, strokeWidth: 3, strokeLinecap: 'round' });
        s += gl;
      }
      return s;
    },
  },
  decor: {
    torso(ctx) {
      const { torsoTop: T, torsoBot: B, sw, back, tm } = ctx, c = PAL.momCardigan;
      let s = '';
      if (back) return ribBand(ctx, tone(c, 0.05), 10);
      const m = tm(0), k = Math.max(0.4, m.k);
      // mint top showing through the open cardigan
      const top = PAL.momTop;
      s += path(roundPoly([[m.x - 15 * k, T + 1, 4], [m.x + 15 * k, T + 1, 4], [m.x + 22 * k, B + 1, 2], [m.x - 22 * k, B + 1, 2]]), { fill: grad(top, 'd'), stroke: stroke(c), strokeWidth: f1(sw), strokeLinejoin: 'round' });
      s += path(`M${f1(m.x - 12 * k)} ${f1(T + 4)}Q${f1(m.x)} ${f1(T + 18)} ${f1(m.x + 12 * k)} ${f1(T + 4)}`, { fill: 'none', stroke: stroke(top), strokeWidth: f1(sw * 0.7), strokeLinecap: 'round' });
      for (let i = 0; i < 3; i++) s += circle(m.x - 19 * k - 1, T + 40 + i * 20, 3.2, { fill: grad('#FFFFFF', 'd'), stroke: stroke(c), strokeWidth: 1.4 });
      // pockets + label maker peeking out of the screen-right pocket
      for (const sd of [-1, 1]) {
        const pm = tm(sd * 34); if (pm.k < 0.3) continue;
        const pw = 24 * pm.k, py = B - 40;
        if (sd > 0) s += labeler(pm.x, py + 2, 'R', sw * 0.85);
        s += path(rrect(pm.x - pw / 2, py, pw, 24, 5), { fill: grad(tone(c, -0.02), 'd'), stroke: stroke(c), strokeWidth: f1(sw * 0.8) });
      }
      return s + ribBand(ctx, tone(c, 0.05), 10);
    },
  },
};

// ======================================================================
// DAD — blue polo, side hair round a shiny bald top, thick moustache, WORLD'S OKAYEST DAD mug
// ======================================================================
const DAD_BAND = {
  t: 5,
  top: [[-2, -34], [-1.2, -33], [-0.56, -22], [0.56, -22], [1.2, -33], [2, -34]],
  bottom: [[-2, 24], [-1.3, 22], [-0.95, 10, 0], [-0.6, -2], [0.6, -2], [0.95, 10], [1.3, 22], [2, 24]],
  mask: (u) => Math.abs(u) > 0.56,
};
const DAD = {
  name: 'DAD', color: '#4A90E2',
  skin: PAL.skinWarm,
  dims: { head: { w: 122, h: 114, r: 0.24 }, torso: { h: 124, wt: 108, wb: 128, rt: 26, rb: 26 }, arm: { w: 31, up: 54, fore: 50, hand: 17 }, leg: { w: 38, len: 100, hip: 25 }, shoe: { w: 50, h: 24 } },
  faceOpts: { eyeX: 19, eyeY: 4, eyeR: 12, mouthY: 31, browLen: 18 },
  top: { color: PAL.dadPolo, sleeve: true, sleeveLen: 0.58, sleeveW: 1.2 },
  pants: { color: PAL.dadPants },
  shoes: { color: '#6B4A3A', sole: null },
  pose: { armR: 26, foreR: 112 },
  props: { R: 'mug' },
  hair: {
    height: 4,
    front(ctx) {
      const shapes = bandPaths(DAD_BAND, ctx.head, ctx.yaw).map((d) => ({ d }));
      let s = shapes.length ? union(shapes, PAL.dadHair, { sw: ctx.sw, box: [-56, -40, 56, 26] }) : '';
      s += strands([{ y: -16, u0: 0.62, u1: 1.6, amp: 1.5, waves: 1.5, inset: 4 }, { y: -16, u0: -1.6, u1: -0.62, amp: 1.5, waves: 1.5, inset: 4 }], ctx.head, ctx.yaw, PAL.dadHair, { t: 5, crown: 0 });
      // shine on the bald top
      const hx = -14 + 20 * sind(ctx.yaw);
      s += ellipse(hx, -38, 12, 4.6, { fill: '#FFFFFF', opacity: 0.6, transform: `rotate(-10 ${f1(hx)} -38)` }) + ellipse(hx + 16, -41, 3.6, 2.2, { fill: '#FFFFFF', opacity: 0.55 });
      return s;
    },
  },
  faceOver(ctx, faceSpec) {
    if (ctx.back) return '';
    const m = mapFeature(0, ctx.yaw), k = Math.max(0.45, m.k);
    const open = typeof faceSpec === 'string' ? ['shocked', 'scream', 'panic', 'laugh', 'happy', 'starstruck', 'cry', 'excited', 'yawn'].includes(faceSpec) : false;
    const lift = open ? -2.5 : 0;
    const c = '#4A2C1E';
    const d = 'M0 -3.5Q6 -8 13 -6Q20 -4 21 3Q15 1.5 11 3.5Q5 5 0 1.5Q-5 5 -11 3.5Q-15 1.5 -21 3Q-20 -4 -13 -6Q-6 -8 0 -3.5Z';
    return g(path(d, { fill: grad(c, 'd'), stroke: stroke(c), strokeWidth: 2.2, strokeLinejoin: 'round' }) + path('M-12 -3.4Q-7 -5.4 -3 -2.8', { fill: 'none', stroke: tone(c, 0.12), strokeWidth: 2, strokeLinecap: 'round' }),
      { transform: `translate(${f1(m.x)} ${f1(31 - 9.5 + lift)}) scale(${f1(k)} 1)` });
  },
  decor: {
    neckFront(ctx) {
      const { torsoTop: T, sw, back, tm } = ctx, c = tone(PAL.dadPolo, 0.06);
      if (back) return path(`M-30 ${f1(T + 2)}Q0 ${f1(T + 14)} 30 ${f1(T + 2)}L28 ${f1(T - 4)}Q0 ${f1(T + 6)} -28 ${f1(T - 4)}Z`, { fill: grad(c, 'd'), stroke: stroke(c), strokeWidth: f1(sw), strokeLinejoin: 'round' });
      let s = '';
      for (const sd of [-1, 1]) {
        const a = tm(sd * 4), b = tm(sd * 32), cc = tm(sd * 20); if (b.k < 0.2) continue;
        s += path(roundPoly([[a.x, T + 2, 2], [b.x, T - 1, 3], [cc.x, T + 20, 3], [a.x, T + 13, 2]]), { fill: grad(c, 'd'), stroke: stroke(c), strokeWidth: f1(sw), strokeLinejoin: 'round' });
      }
      return s;
    },
    torso(ctx) {
      const { torsoTop: T, sw, back, tm } = ctx, c = PAL.dadPolo;
      if (back) return '';
      const m = tm(0), k = Math.max(0.4, m.k);
      let s = path(rrect(m.x - 6 * k, T + 8, 12 * k, 30, 4), { fill: grad(tone(c, 0.03), 'd'), stroke: stroke(c), strokeWidth: f1(sw * 0.75) });
      s += circle(m.x, T + 18, 2.6, { fill: '#FFFFFF', stroke: stroke(c), strokeWidth: 1.2 }) + circle(m.x, T + 30, 2.6, { fill: '#FFFFFF', stroke: stroke(c), strokeWidth: 1.2 });
      const lg = tm(-28); if (lg.k > 0.3) s += g(path('M-5 -1Q0 -5 5 -1Q0 4 -5 -1Z', { fill: '#FFFFFF', opacity: 0.8 }), { transform: `translate(${f1(lg.x)} ${f1(T + 34)}) scale(${f1(lg.k)} 1)` });
      return s;
    },
    belt(ctx, { px, py, pw }) {
      const c = '#5A3A28', y = ctx.torsoBot - 6;
      let s = path(rrect(px + 2, y - 2, pw - 4, 10, 4), { fill: grad(c, 'v'), stroke: stroke(c), strokeWidth: f1(ctx.sw * 0.8) });
      if (!ctx.back) { const m = ctx.tm(0); s += path(rrect(m.x - 7, y - 3, 14, 12, 3), { fill: grad('#FFD43B', 'd'), stroke: stroke('#FFD43B'), strokeWidth: f1(ctx.sw * 0.8) }); }
      return s;
    },
  },
};

// ======================================================================
// BRIGGS — mustard sweater vest, bow tie, round glasses, comb-over
// ======================================================================
const BRIGGS_BAND = {
  t: 3.5,
  top: [[-2, -30], [-1.2, -28], [-0.6, -18], [0.6, -18], [1.2, -28], [2, -30]],
  bottom: [[-2, 22], [-1.3, 18], [-0.6, -2], [0.6, -2], [1.3, 18], [2, 22]],
  mask: (u) => Math.abs(u) > 0.6,
};
const BRIGGS = {
  name: 'MR. BRIGGS', color: '#E0B03A',
  skin: '#BE8562',
  dims: { head: { w: 118, h: 110, r: 0.24 }, torso: { h: 116, wt: 100, wb: 118, rt: 24, rb: 22 }, arm: { w: 28, up: 50, fore: 46, hand: 15 }, leg: { w: 34, len: 92, hip: 22 }, shoe: { w: 46, h: 22 } },
  faceOpts: { eyeX: 19, eyeY: 5, eyeR: 11.2, mouthY: 29, browColor: '#3E3640', browLen: 17 },
  top: { color: PAL.briggsShirt, sleeve: true, cuff: '#FFFFFF' },
  pants: { color: PAL.briggsPants },
  shoes: { color: '#4A3428', sole: null },
  pose: { lean: 0, head: 0 },
  hair: {
    height: 8,
    front(ctx) {
      const lc = stroke(PAL.briggsHair);
      const shapes = bandPaths(BRIGGS_BAND, ctx.head, ctx.yaw).map((d) => ({ d }));
      let s = shapes.length ? union(shapes, PAL.briggsHair, { sw: ctx.sw, box: [-56, -36, 56, 24] }) : '';
      // three comb-over strands across the bald top
      const sy = sind(ctx.yaw) * 18;
      for (const [y0, y1, lift] of [[-30, -40, -50], [-26, -36, -54], [-22, -31, -46]]) {
        if (ctx.back) break;
        const d = `M${f1(-46 + sy)} ${y0}Q${f1(-6 + sy)} ${lift} ${f1(40 + sy)} ${y1}`;
        s += path(d, { fill: 'none', stroke: lc, strokeWidth: f1(5 + ctx.sw * 2), strokeLinecap: 'round' }) + path(d, { fill: 'none', stroke: PAL.briggsHair, strokeWidth: 5, strokeLinecap: 'round' });
      }
      const hx = -10 + 20 * sind(ctx.yaw);
      s += ellipse(hx, -41, 9, 3.4, { fill: '#FFFFFF', opacity: 0.45 });
      return s;
    },
  },
  faceOver(ctx) {
    if (ctx.back) return '';
    const fr = '#7A4A22';
    let s = '';
    const pts = [];
    for (const sd of [-1, 1]) {
      const m = mapFeature(sd * 19, ctx.yaw); if (m.k < 0.25 || (ctx.side && sd * ctx.yaw > 0)) continue;
      pts.push(m);
      s += g(circle(0, 0, 15.5, { fill: '#E8F4FF', fillOpacity: 0.22, stroke: fr, strokeWidth: 3 }) + path('M-9 -6L-4 -11', { stroke: '#FFFFFF', strokeWidth: 2.6, strokeLinecap: 'round', opacity: 0.85 }), { transform: `translate(${f1(m.x)} 5) scale(${f1(m.k)} 1)` });
    }
    if (pts.length === 2) s += path(`M${f1(pts[0].x + 15.5 * pts[0].k)} 3Q${f1((pts[0].x + pts[1].x) / 2)} -1 ${f1(pts[1].x - 15.5 * pts[1].k)} 3`, { fill: 'none', stroke: fr, strokeWidth: 3, strokeLinecap: 'round' });
    return s;
  },
  decor: {
    torso(ctx) {
      const { torsoTop: T, torsoBot: B, sw, back, tm } = ctx, c = PAL.briggsVest;
      const hwT = ctx.wt / 2, hwB = ctx.wb / 2;
      const m = tm(0), k = Math.max(0.4, m.k);
      const pts = back
        ? [[-(hwT - 12), T + 6, 6], [hwT - 12, T + 6, 6], [hwT * 1.0, T + 30, 8], [hwB, B, ctx.d.torso.rb], [-hwB, B, ctx.d.torso.rb], [-hwT * 1.0, T + 30, 8]]
        : [[-(hwT - 12), T + 6, 4], [m.x, T + 52, 3], [hwT - 12, T + 6, 4], [hwT * 1.0, T + 30, 8], [hwB, B, ctx.d.torso.rb], [-hwB, B, ctx.d.torso.rb], [-hwT * 1.0, T + 30, 8]];
      let s = path(roundPoly(pts), { fill: grad(c, 'd'), stroke: stroke(c), strokeWidth: f1(sw), strokeLinejoin: 'round' });
      if (!back) {
        // argyle diamonds down the front
        for (const [dx, dy] of [[0, 72], [-18 * k, 88], [18 * k, 88]]) s += path(`M${f1(m.x + dx)} ${f1(T + dy - 9)}L${f1(m.x + dx + 7 * k)} ${f1(T + dy)}L${f1(m.x + dx)} ${f1(T + dy + 9)}L${f1(m.x + dx - 7 * k)} ${f1(T + dy)}Z`, { fill: tone(c, 0.06), opacity: 0.9 });
      }
      s += ribBand(ctx, tone(c, -0.03), 9);
      return s;
    },
    neckFront(ctx) {
      const { torsoTop: T, sw, back, tm } = ctx;
      if (back) return '';
      const m = tm(0), k = Math.max(0.4, m.k), c = PAL.briggsTie, sh = '#FFFFFF';
      let s = '';
      for (const sd of [-1, 1]) s += path(`M${f1(m.x)} ${f1(T + 4)}L${f1(m.x + sd * 20 * k)} ${f1(T + 1)}L${f1(m.x + sd * 10 * k)} ${f1(T + 16)}Z`, { fill: grad(sh, 'd'), stroke: stroke(sh), strokeWidth: f1(sw * 0.8), strokeLinejoin: 'round' });
      s += g(path('M0 0L-15 -8Q-17 0 -15 8Z', { fill: grad(c, 'd'), stroke: stroke(c), strokeWidth: f1(sw * 0.8), strokeLinejoin: 'round' }) + path('M0 0L15 -8Q17 0 15 8Z', { fill: grad(c, 'd'), stroke: stroke(c), strokeWidth: f1(sw * 0.8), strokeLinejoin: 'round' })
        + path(rrect(-4.5, -5, 9, 10, 3), { fill: grad(c, 'd'), stroke: stroke(c), strokeWidth: f1(sw * 0.8) })
        + circle(-9, -1.5, 1.6, { fill: '#FFFFFF' }) + circle(10, 2, 1.6, { fill: '#FFFFFF' }) + circle(-11, 4, 1.3, { fill: '#FFFFFF' }) + circle(8, -4, 1.3, { fill: '#FFFFFF' }),
      { transform: `translate(${f1(m.x)} ${f1(T + 9)}) scale(${f1(k)} 1)` });
      return s;
    },
  },
};

// ======================================================================
// KEVIN — tall, sunglasses always on, white tank top, lawn-proud, leaf blower
// ======================================================================
const KEVIN_HAIR = {
  t: 3.5, crown: 6, height: 40,
  tips: [[-2, 8], [-1.3, 6], [-1.02, -6, 2], [-0.82, -26, 2], [-0.45, -30, 3], [-0.05, -32, 3], [0.35, -31, 3], [0.75, -26, 2], [1.02, -6, 2], [1.3, 6], [2, 8]],
};
const KEVIN = {
  name: 'KEVIN', color: '#8E9C5A',
  skin: PAL.skinTan,
  dims: { head: { w: 114, h: 106, r: 0.22 }, torso: { h: 132, wt: 108, wb: 96, rt: 30, rb: 16 }, arm: { w: 29, up: 60, fore: 54, hand: 16 }, leg: { w: 34, len: 138, hip: 21 }, shoe: { w: 46, h: 22 } },
  faceOpts: { eyeX: 19, eyeY: 6, eyeR: 11.5, mouthY: 29 },
  top: { color: PAL.skinTan, sleeve: false },
  pants: { color: PAL.kevinShorts, len: 0.44, sock: '#FFFFFF' },
  shoes: { color: '#F6F7FB', sole: '#C9D2E3', accent: '#4BC240' },
  props: { L: 'blower' },
  pose: { armL: 10, foreL: -6 },
  hair: {
    height: 44,
    front: hairFront(KEVIN_HAIR, PAL.kevinHair, (ctx) => {
      const sx = 22 * sind(ctx.yaw), k = Math.max(0.5, Math.abs(cosd(ctx.yaw)) * 0.6 + 0.4);
      const P = (x, y) => [sx + x * k, y];
      return [{ d: spline([P(-34, -44), P(-30, -66), P(-8, -84), P(22, -86), P(44, -74), P(40, -58), P(26, -52), P(36, -66), P(14, -72), P(-6, -62), P(-2, -46)], { closed: true, sharp: new Set([5, 7]) }) }];
    }, [{ y: -44, u0: -0.55, u1: 0.5, amp: 1.6, waves: 2 }]),
  },
  headwear(ctx) {
    if (ctx.back) return '';
    // frosted tips on the quiff
    const sx = 22 * sind(ctx.yaw);
    return path(`M${f1(sx - 4)} -80Q${f1(sx + 18)} -86 ${f1(sx + 36)} -76`, { fill: 'none', stroke: '#FFF1C2', strokeWidth: 5, strokeLinecap: 'round', opacity: 0.95 })
      + path(`M${f1(sx - 18)} -64Q${f1(sx - 2)} -76 ${f1(sx + 16)} -74`, { fill: 'none', stroke: '#FFF1C2', strokeWidth: 3.4, strokeLinecap: 'round', opacity: 0.8 });
  },
  faceOver(ctx, faceSpec) {
    if (ctx.back) return '';
    // sunglasses: always on; the lenses reflect star / heart eyes
    const fname = typeof faceSpec === 'string' ? faceSpec : faceSpec?.preset;
    const refl = fname === 'starstruck' ? 'star' : fname === 'love' ? 'heart' : null;
    const tilt = ['angry', 'determined', 'evil', 'sly'].includes(fname) ? 7 : ['scared', 'panic', 'cry', 'guilty', 'nervous'].includes(fname) ? -6 : 0;
    const drop = ['shocked', 'panic', 'scream', 'scared'].includes(fname) ? 5 : 0;
    const c = '#22304A', fr = '#141A2A';
    let s = '';
    const ms = [];
    for (const sd of [-1, 1]) {
      const m = mapFeature(sd * 19.5, ctx.yaw); if (m.k < 0.22 || (ctx.side && sd * ctx.yaw > 0)) continue;
      ms.push(m);
      let lens = path(roundPoly([[-15, -10, 5], [15, -10, 5], [13, 8, 8], [-13, 8, 8]]), { fill: grad(c, 'd', { up: 0.12, down: 0.04 }), stroke: fr, strokeWidth: 3.2, strokeLinejoin: 'round' })
        + path('M-10 -4L-3 -8', { stroke: '#FFFFFF', strokeOpacity: 0.7, strokeWidth: 3, strokeLinecap: 'round' }) + path('M1 4L9 -2', { stroke: '#FFFFFF', strokeOpacity: 0.35, strokeWidth: 2.2, strokeLinecap: 'round' });
      if (refl === 'star') lens += path(polyline(starPath(7, 0.45)), { fill: '#FFD43B', opacity: 0.95 });
      if (refl === 'heart') lens += g(path(heartPath(0.62), { fill: '#FF4D6D' }), { transform: 'translate(0 0)' });
      s += g(lens, { transform: `translate(${f1(m.x)} ${f1(5 + drop)}) rotate(${f1(-sd * tilt)}) scale(${f1(m.k)} 1)` });
    }
    if (ms.length === 2) s += path(`M${f1(ms[0].x + 14 * ms[0].k)} ${f1(-2 + drop)}Q${f1((ms[0].x + ms[1].x) / 2)} ${f1(-6 + drop)} ${f1(ms[1].x - 14 * ms[1].k)} ${f1(-2 + drop)}`, { fill: 'none', stroke: fr, strokeWidth: 3.4, strokeLinecap: 'round' });
    // tiny soul patch
    const mm = mapFeature(0, ctx.yaw);
    s += path(`M${f1(mm.x - 2.5)} 40L${f1(mm.x + 2.5)} 40L${f1(mm.x)} 44.5Z`, { fill: tone(PAL.kevinHair, -0.2), stroke: tone(PAL.kevinHair, -0.3), strokeWidth: 1.2, strokeLinejoin: 'round' });
    return s;
  },
  decor: {
    torso(ctx) {
      const { torsoTop: T, torsoBot: B, sw, back, tm } = ctx, c = PAL.kevinTank;
      const hwT = ctx.wt / 2, hwB = ctx.wb / 2, m = tm(0), k = Math.max(0.4, m.k);
      const neck = back ? 10 : 30;
      const st = hwT - 30;
      const d = `M${f1(-st - 12)} ${f1(T + 1)}L${f1(-st + 1)} ${f1(T + 1)}Q${f1(m.x)} ${f1(T + neck)} ${f1(st - 1)} ${f1(T + 1)}L${f1(st + 12)} ${f1(T + 1)}Q${f1(hwT - 6)} ${f1(T + 34)} ${f1(hwT - 1)} ${f1(T + 48)}L${f1(hwB)} ${f1(B - ctx.d.torso.rb)}Q${f1(hwB)} ${f1(B)} ${f1(hwB - ctx.d.torso.rb)} ${f1(B)}L${f1(-hwB + ctx.d.torso.rb)} ${f1(B)}Q${f1(-hwB)} ${f1(B)} ${f1(-hwB)} ${f1(B - ctx.d.torso.rb)}L${f1(-hwT + 1)} ${f1(T + 48)}Q${f1(-hwT + 6)} ${f1(T + 34)} ${f1(-st - 12)} ${f1(T + 1)}Z`;
      let s = path(d, { fill: grad(c, 'd', { up: 0.0, down: 0.09 }), stroke: stroke(c), strokeWidth: f1(sw), strokeLinejoin: 'round' });
      s += glossBox(-hwT + 6, T, ctx.wt - 12, ctx.d.torso.h, { op: 0.5, top: false, sw: sw * 1.3 });
      if (!back) {
        // grass stain, because of course
        s += g(path('M-6 -3Q0 -7 7 -2Q9 3 2 4Q-5 6 -7 1Z', { fill: '#7CC86A', opacity: 0.55 }) + circle(9, 5, 1.8, { fill: '#7CC86A', opacity: 0.5 }), { transform: `translate(${f1(m.x - 18 * k)} ${f1(B - 30)}) scale(${f1(k)} 1)` });
      }
      return s;
    },
  },
};

// ======================================================================
// PICKLES — the family cat: grey, round, permanently half-lidded, tiny white socks
// ======================================================================
const PICKLES = {
  name: 'PICKLES', color: '#9EA4B4', cat: true,
  fur: PAL.cat,
  dims: { head: { w: 112, h: 94, r: 0.36 }, body: { h: 96, wt: 76, wb: 118 } },
  faceOpts: { eyeX: 20, eyeY: 2, eyeR: 12, mouthY: 24, cat: true },
};
function catEars(ctx, fur, sw) {
  let s = '';
  for (const sd of [-1, 1]) {
    const a = (sd * 0.42 * 90 + ctx.yaw) * D2R, x = 44 * Math.sin(a), z = Math.cos(a);
    const k = Math.max(0.35, Math.abs(Math.cos(a)) * 0.7 + 0.3);
    const outer = roundPoly([[-15, 6, 3], [0, -22, 6], [15, 6, 3]]);
    let e = path(outer, { fill: grad(fur, 'd'), stroke: stroke(fur), strokeWidth: f1(sw), strokeLinejoin: 'round' });
    if (z > 0 && !ctx.back) e += path(roundPoly([[-8, 3, 2], [0, -13, 4], [8, 3, 2]]), { fill: grad('#FFB3C4', 'd') });
    s += g(e, { transform: `translate(${f1(x)} -38) rotate(${f1(sd * 14)}) scale(${f1(k)} 1)` });
  }
  return s;
}
function buildCat(spec, o) {
  const yaw = yawOf(o.facing ?? 'front');
  const pose = { armL: 0, armR: 0, head: 0, lean: 0, bob: 0, tail: 0, ...(o.pose || {}) };
  const s = o.s ?? 1, fur = spec.fur, sw = 3.0;
  const sn = sind(yaw), cs = cosd(yaw), aS = Math.abs(sn), aC = Math.abs(cs), back = cs < -0.5;
  const kW = aC + 0.95 * aS;
  const bd = spec.dims.body, H = bd.h;
  const wt = bd.wt * kW, wb = bd.wb * (aC + 1.15 * aS);
  let tail = '', body = '';
  // tail: curls up from the back; swings with pose.tail
  {
    const side = Math.abs(sn) > 0.2 ? -Math.sign(sn) : 1;
    const base = [side * 34 * (aC * 0.6 + 0.6), -14];
    const P = (x, y) => rotPt([base[0] + side * x, base[1] + y], base, pose.tail * side);
    const pts = [P(0, 0), P(30, -4), P(50, -28), P(46, -66), P(30, -86), P(18, -84)];
    const d = spline(pts);
    const front = back;
    const t = path(d, { fill: 'none', stroke: stroke(fur), strokeWidth: f1(19 + sw * 2), strokeLinecap: 'round' }) + path(d, { fill: 'none', stroke: grad(fur, 'd', { box: [base[0] - 60, -100, base[0] + 60, 0] }), strokeWidth: 19, strokeLinecap: 'round' })
      + path(spline([P(32, -10), P(46, -32), P(43, -60)]), { fill: 'none', stroke: '#FFFFFF', strokeOpacity: 0.35, strokeWidth: 4, strokeLinecap: 'round' });
    tail = t; void front;
  }
  // body: pear with haunches
  const bshapes = [{ d: rtrap(0, -H, 0, wt, wb, 34, 26) }];
  for (const sd of [-1, 1]) bshapes.push({ d: `M${f1(sd * wb * 0.34 - 27)} -22a27 22 0 1 0 54 0a27 22 0 1 0 -54 0Z` });
  body += union(bshapes, fur, { sw, box: [-wb / 2, -H, wb / 2, 0] });
  body += path(rtrap(0, -H, 0, wt, wb, 34, 26), { fill: shadeBand(fur, { at: 0.86, op: 0.4 }) });
  if (!back) {
    const m = mapFeature(0, yaw);
    body += ellipse(m.x * 0.5, -58, 22 * Math.max(0.5, m.k), 28, { fill: grad('#E9ECF4', 'd') });
    // front legs with white socks
    for (const sd of [-1, 1]) {
      const a = sd < 0 ? pose.armL : pose.armR;
      const mm = mapFeature(sd * 15, yaw); if (mm.k < 0.25) continue;
      const x = mm.x * 0.62, y0 = -60, L = 50, sg = sd < 0 ? 1 : -1;
      const lx = x - sg * Math.sin(a * D2R) * L, ly = y0 + Math.cos(a * D2R) * L;
      body += union([{ d: capsule(x, y0, lx, ly - 6, 21) }], fur, { sw, box: [x - 12, y0, x + 12, ly] });
      body += union([{ d: `M${f1(lx - 13)} ${f1(ly - 6)}a13 9.5 0 1 0 26 0a13 9.5 0 1 0 -26 0Z` }, { d: capsule(lx, ly - 18, lx, ly - 8, 21) }], '#FFFFFF', { sw: sw * 0.95, box: [lx - 13, ly - 24, lx + 13, ly + 4] });
      body += path(`M${f1(lx - 3.5)} ${f1(ly - 1)}v-5M${f1(lx + 3.5)} ${f1(ly - 1)}v-5`, { stroke: stroke('#FFFFFF'), strokeWidth: 1.6, strokeLinecap: 'round', opacity: 0.7 });
    }
  } else {
    body += path(`M0 ${f1(-H + 10)}L0 -30`, { stroke: tone(fur, -0.06), strokeWidth: 3, strokeLinecap: 'round', opacity: 0.6 });
  }
  body += glossBox(-wt / 2 - 6, -H, wt, H, { op: 0.3, top: false, sw: 4 });
  // head
  const hd = spec.dims.head, hh = (100 * hd.h) / hd.w, head = { top: -hh / 2, bot: hh / 2, r: hd.r * 100 };
  const lsw = (sw * 100) / hd.w;
  const ctx = { yaw, head, sw: lsw, back, side: aS > 0.94 };
  const hp = rrect(-50, head.top, 100, hh, head.r);
  let hs = catEars(ctx, fur, lsw);
  // cheek fluff
  for (const sd of [-1, 1]) {
    const a = (sd * 90 + yaw) * D2R; if (Math.cos(a) < -0.6) continue;
    const x = 50 * Math.sin(a);
    hs += path(`M${f1(x - sd * 6)} 2L${f1(x + sd * 9)} 9L${f1(x - sd * 2)} 14L${f1(x + sd * 7)} 22L${f1(x - sd * 8)} 26Z`, { fill: grad(fur, 'd'), stroke: stroke(fur), strokeWidth: f1(lsw), strokeLinejoin: 'round' });
  }
  hs += path(hp, { fill: radial(fur, { cx: 0.36, cy: 0.32 }), stroke: stroke(fur), strokeWidth: f1(lsw), strokeLinejoin: 'round' }) + path(hp, { fill: shadeBand(fur, { at: 0.88, op: 0.45 }) });
  hs += path(`M-41 ${f1(head.top + hh * 0.35)}L-41 ${f1(head.top + hh * 0.7)}`, { stroke: '#FFFFFF', strokeOpacity: 0.4, strokeWidth: 3.6, strokeLinecap: 'round' });
  // tabby marks on the forehead
  const tx = mapFeature(0, yaw);
  if (!back) for (const dx of [-8, 0, 8]) hs += path(`M${f1(tx.x + dx * tx.k)} ${f1(head.top + 4)}L${f1(tx.x + dx * tx.k * 0.8)} ${f1(head.top + (dx ? 11 : 14))}`, { stroke: tone(fur, -0.1, 1.2), strokeWidth: 3.4, strokeLinecap: 'round' });
  else for (const y of [-30, -20, -10]) hs += path(`M-14 ${y}Q0 ${y + 4} 14 ${y}`, { fill: 'none', stroke: tone(fur, -0.1, 1.2), strokeWidth: 3.4, strokeLinecap: 'round' });
  // face: smile-type mouths become the cat's w
  let fspec = o.face || { preset: 'deadpan' };
  const mmap = { smile: 'cat', flat: 'cat', bigSmile: 'cat', meh: 'cat' };
  const res = typeof fspec === 'string' ? { preset: fspec } : { ...fspec };
  const base = { ...(res.preset ? (FACE_PRESETS_CACHE[res.preset] || {}) : {}), ...res };
  if (mmap[base.mouth]) res.mouth = mmap[base.mouth];
  const f = drawFace(res, { yaw, skin: fur, look: o.look, top: head.top - 26, ...spec.faceOpts });
  hs += f.face;
  if (!back) {
    // whiskers
    for (const sd of [-1, 1]) {
      const m = mapFeature(sd * 30, yaw); if (m.k < 0.3 || (ctx.side && sd * yaw > 0)) continue;
      for (const [dy, ang] of [[-2, -8], [3, 2], [8, 12]]) {
        const x0 = m.x, y0 = 20 + dy, x1 = x0 + sd * 22 * m.k, y1 = y0 + ang * 0.5;
        hs += path(`M${f1(x0)} ${f1(y0)}Q${f1((x0 + x1) / 2)} ${f1(y0 - 2)} ${f1(x1)} ${f1(y1)}`, { fill: 'none', stroke: stroke(fur), strokeWidth: 1.8, strokeLinecap: 'round', opacity: 0.85 });
      }
    }
  }
  const hsc = hd.w / 100, headCY = -H - hh * hsc * 0.36;
  const headG = g(hs, { transform: `translate(0 ${f1(headCY)}) scale(${f1(hsc)})` });
  const fxG = g(f.fx, { transform: `translate(0 ${f1(headCY)}) scale(${f1(hsc)})` });
  const pivot = `rotate(${f1(pose.head)} 0 ${f1(-H + 6)})`;
  const upper = g((back ? '' : tail) + body + (back ? tail : '') + g(headG, { transform: pivot }) + g(fxG, { transform: pivot }), { transform: `translate(0 ${f1(pose.bob)}) rotate(${f1(pose.lean)} 0 0)` });
  const shadow = o.shadow === false ? '' : contactShadow(0, 2, wb * 0.62 + 10, 10, { op: 0.3 });
  return g(shadow + upper, { transform: `translate(${f1(o.x ?? 0)} ${f1(o.y ?? 0)}) scale(${f1(s * 1000) / 1000})` });
}

// ---------- registry ----------
for (const c of [SAM, LILY, MOM, DAD, BRIGGS, KEVIN]) c.drawProp = drawProp;
export const CAST = { sam: SAM, lily: LILY, mom: MOM, dad: DAD, pickles: PICKLES, briggs: BRIGGS, kevin: KEVIN };
export const CAST_IDS = ['sam', 'lily', 'mom', 'dad', 'pickles', 'briggs', 'kevin'];
export function toon(id, o = {}) {
  const spec = CAST[id];
  if (!spec) throw new Error('unknown cast id ' + id);
  if (spec.cat) return buildCat(spec, o);
  return buildFigure(spec, o);
}
// height above ground (body units at s=1) and head centre, for framing
export function toonHeight(id) {
  const spec = CAST[id];
  if (spec.cat) return spec.dims.body.h + spec.dims.head.h * 1.15 + 20;
  return figureHeight(spec);
}
export function toonHeadY(id) {
  const spec = CAST[id];
  if (spec.cat) { const hd = spec.dims.head; return -spec.dims.body.h - ((100 * hd.h) / hd.w) * (hd.w / 100) * 0.36; }
  return headCenterY(spec);
}
export function toonHeadSize(id) { const hd = CAST[id].dims.head; return hd.h; }
