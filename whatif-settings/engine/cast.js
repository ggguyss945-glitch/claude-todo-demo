// cast.js — the cast of "What If Real Life Had a SETTINGS MENU?" built on rig.js + face.js.
//   toon(id, { x, y, s, facing, pose:{armL, armR, foreL, foreR, legL, legR, head, lean, bob, handL, handR,
//              pigL, pigR, pony, tail, shrug}, face: 'preset' | {eyes, brows, mouth, ...} | {preset, to, k},
//              look:[dx,dy], add:{...}, props:{L, R},
//              outfit: 'pyjamas' (Dad), mannequin: 0..1 | variant: 'default', legs: false,
//              tint: {color, k, mode}, light: {color, k, from: 'below'|'phone'|'left'|'right'|'above'|'front'|[x, y], r} })
//   (mannequin / variant / tint / light / outfit / legs may also ride inside add:{} so cast-unaware callers pass them)
// L / R are the screen-left / screen-right limbs in the front view. Angles in degrees: 0 hangs down, + swings
// outward/up (180 = straight up); fore bends the forearm relative to the upper arm (+ continues outward).
import { PAL, g, path, circle, ellipse, rect, text, grad, addDef, fxDef, radial, shadeBand, stroke, tone, union, rrect, rtrap, capsule, taper,
  glossCapsule, glossBox, contactShadow, f1, spline, polyline, roundPoly, FONT_UI, FONT_DISPLAY, uid, withFx, noFx, fxTint, fxMannequin, fxLightMask } from './style.js';
import { face as drawFace, mapFeature, heartPath, starPath, resolve as resolveFace, PRESETS as FACE_PRESETS_CACHE } from './face.js';
import { buildFigure, helmetPath, bandPaths, strands, wrapPoint, hairline, yawOf, headCenterY, figureHeight, hipYOf, withAdd } from './rig.js';

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

function limbLobes(band, yaw, ys, r, t) {
  const out = [];
  for (const sd of [-1, 1]) {
    const u = (sd * 90 - yaw) / 90, w = ((((u + 2) % 4) + 4) % 4) - 2;
    if (!band.mask(w)) continue;
    for (const y of ys) out.push({ d: `M${f1(sd * (50 + t - r * 0.55) - r)} ${f1(y)}a${f1(r)} ${f1(r)} 0 1 0 ${f1(2 * r)} 0a${f1(r)} ${f1(r)} 0 1 0 ${f1(-2 * r)} 0Z` });
  }
  return out;
}
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
    + text(x + w / 2, y + h * 0.62, 'BEST-ISH', { fontFamily: FONT_UI, fontWeight: 800, fontSize: f1(5.2 * big), fill: '#E2404A', textAnchor: 'middle' })
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
  const t0 = [bx + out * 18, by + 36], t1 = [bx + out * 70, by + 100];
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
let PROP_AT = null;        // where the last toon() held a phone (body units), for light: {from: 'phone'}
function phone(hx, hy, side, sw) {
  const w = 24, h = 40, x = hx - w / 2 + (side === 'L' ? 6 : -6), y = hy - h * 0.7;
  PROP_AT = [x + w / 2, y + h / 2];
  let s = path(rrect(x, y, w, h, 6), { fill: grad('#2B3150', 'd'), stroke: stroke('#2B3150'), strokeWidth: f1(sw), strokeLinejoin: 'round' });
  s += noFx(() => path(rrect(x + 3, y + 3.5, w - 6, h - 7, 3.5), { fill: grad('#5B8CFF', 'v') }) + gearPath(x + w / 2, y + h * 0.42, 6.2, '#FFFFFF'));
  return s;
}
// the phone seen from behind (the character is looking at the screen): dark case, camera bump, a rim of screen glow
function phoneBack(hx, hy, side, sw) {
  const w = 26, h = 42, x = hx - w / 2 + (side === 'L' ? 5 : -5), y = hy - h * 0.84;
  PROP_AT = [x + w / 2, y + h / 2];
  const c = '#3A4166';
  let s = noFx(() => path(rrect(x - 2.5, y - 2.5, w + 5, h + 5, 8.5), { fill: '#BFE3FF', opacity: 0.55 }));
  s += path(rrect(x, y, w, h, 6.5), { fill: grad(c, 'd', { up: 0.08, down: 0.06 }), stroke: stroke(c), strokeWidth: f1(sw), strokeLinejoin: 'round' });
  s += path(rrect(x + 4, y + 4, 10, 13, 3.5), { fill: tone(c, -0.06), stroke: stroke(c), strokeWidth: 1.2 }) + circle(x + 9, y + 8.2, 2.3, { fill: '#1E2238' }) + circle(x + 9, y + 13.4, 2.3, { fill: '#1E2238' });
  s += path(`M${f1(x + 4)} ${f1(y + 22)}L${f1(x + 4)} ${f1(y + h - 6)}`, { stroke: '#FFFFFF', strokeOpacity: 0.35, strokeWidth: 2.2, strokeLinecap: 'round' });
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
  if (kind === 'phoneBack') return { behind: phoneBack(hx, hy, side, sw) };
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
  tips: [[-2, 24], [-1.66, 27, 4], [-1.4, 22, 3], [-1.2, 8, 2], [-1.02, -3, 2], [-0.9, -7, 6, 0.8], [-0.7, -19, 10, 0.72], [-0.43, -21, 11, 0.68], [-0.14, -23, 11, 0.68],
    [0.15, -21, 11, 0.68], [0.44, -20, 10, 0.7], [0.7, -15, 7, 0.8], [0.9, -7, 2], [1.02, -3, 2], [1.2, 8, 3], [1.4, 22, 4], [1.66, 27, 4], [2, 24]],
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
      return [{ d: `M${f1(cx - 7)} -53Q${f1(cx - 5)} -66 ${f1(cx + 9)} -69Q${f1(cx + 3)} -62 ${f1(cx + 7)} -52Z` }];
    }, [{ y: -46, u0: -0.58, u1: 0.5, amp: 2, waves: 2 }, { y: -38, u0: -0.76, u1: 0.68, amp: 2.2, waves: 2.5 }, { y: -30.5, u0: -0.7, u1: 0.62, amp: 1.6, waves: 3, dark: true, w: 3.2, op: 0.6 }]),
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
      // kangaroo pocket (front-only details drop out once they turn past ~55 degrees)
      const p = tm(0), pw = ctx.wt * 0.62 * Math.max(0.55, p.k), py0 = B - 44, py1 = B - 12;
      if (p.k < 0.6) return s + ribBand(ctx, dk);
      s += path(roundPoly([[p.x - pw * 0.4, py0, 6], [p.x + pw * 0.4, py0, 6], [p.x + pw * 0.52, py1, 4], [p.x - pw * 0.52, py1, 4]]), { fill: grad(tone(c, -0.025), 'd'), stroke: stroke(c), strokeWidth: f1(sw * 0.8), strokeLinejoin: 'round' });
      s += path(`M${f1(p.x - pw * 0.4)} ${f1(py0 + 2)}Q${f1(p.x - pw * 0.5)} ${f1(py0 + 14)} ${f1(p.x - pw * 0.52)} ${f1(py1 - 2)}`, { fill: 'none', stroke: stroke(c), strokeWidth: f1(sw * 0.6), opacity: 0.5 });
      // gear logo
      const lg = tm(0);
      if (lg.k > 0.6) s += g(gearPath(0, 0, 14, '#FFFFFF'), { transform: `translate(${f1(lg.x)} ${f1(T + 60)}) scale(${f1(Math.max(0.35, lg.k))} 1)` });
      // drawstrings
      for (const sd of [-1, 1]) {
        const m = tm(sd * 11); if (m.k < 0.25) continue;
        s += path(`M${f1(m.x)} ${f1(T + 6)}Q${f1(m.x + sd * 2)} ${f1(T + 24)} ${f1(m.x + sd * 1)} ${f1(T + 38)}`, { fill: 'none', stroke: stroke('#FFFFFF'), strokeWidth: f1(4.6 + sw), strokeLinecap: 'round' })
          + path(`M${f1(m.x)} ${f1(T + 6)}Q${f1(m.x + sd * 2)} ${f1(T + 24)} ${f1(m.x + sd * 1)} ${f1(T + 38)}`, { fill: 'none', stroke: '#F4F5FA', strokeWidth: 4.6, strokeLinecap: 'round' })
          + path(capsule(m.x + sd * 1, T + 36, m.x + sd * 1, T + 43, 6), { fill: '#9AA3BC', stroke: stroke('#9AA3BC'), strokeWidth: f1(sw * 0.6) });
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
  const { torsoTop: T, sw, yaw, back } = ctx, c = PAL.phones, dk = '#C8541A';
  if (!front) return '';
  const band = (d, w) => path(d, { fill: 'none', stroke: stroke(c), strokeWidth: f1(w + sw * 2), strokeLinecap: 'round' }) + path(d, { fill: 'none', stroke: grad(c, 'v', { box: [-50, T, 50, T + 30] }), strokeWidth: f1(w), strokeLinecap: 'round' });
  if (back) return band(`M-48 ${f1(T + 8)}Q0 ${f1(T - 10)} 48 ${f1(T + 8)}`, 9);
  const cups = [-1, 1].map((sd) => { const a = (sd * 60 + yaw) * D2R; return { sd, x: 44 * Math.sin(a), z: Math.cos(a), k: Math.max(0.45, Math.abs(Math.cos(a)) * 0.5 + 0.5) }; });
  const vis = cups.filter((cp) => cp.z > -0.15);
  let s = '';
  // the band hangs in front, under the chin, like a necklace
  if (vis.length === 2) s += band(`M${f1(cups[0].x)} ${f1(T + 12)}Q${f1((cups[0].x + cups[1].x) / 2)} ${f1(T + 38)} ${f1(cups[1].x)} ${f1(T + 12)}`, 8);
  for (const cp of vis) {
    const r = 15;
    s += g(
      circle(0, 0, r, { fill: grad(c, 'd'), stroke: stroke(c), strokeWidth: f1(sw) })
      + circle(0, 0, r * 0.62, { fill: grad(dk, 'd', { up: 0.02, down: 0.06 }), stroke: stroke(c), strokeWidth: f1(sw * 0.6) })
      + circle(0, 0, r * 0.26, { fill: tone(c, 0.08) })
      + path(`M${f1(-r * 0.62)} ${f1(-r * 0.42)}Q${f1(-r * 0.5)} ${f1(-r * 0.68)} ${f1(-r * 0.2)} ${f1(-r * 0.76)}`, { fill: 'none', stroke: '#FFFFFF', strokeOpacity: 0.6, strokeWidth: 3.2, strokeLinecap: 'round' }),
      { transform: `translate(${f1(cp.x)} ${f1(T + 12)}) scale(${f1(cp.k)} 1)` });
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
  const ax = 40 * Math.sin(a) * 0.9, ay = -50;
  const sp = (pose.pony || 0) * dir;
  const P = (x, y) => rotPt([ax + dir * x, ay + y], [ax, ay], sp);
  const pts = [P(6, -8), P(30, -22), P(58, -16), P(74, 6), P(76, 34), P(66, 58), P(52, 70), P(60, 50), P(62, 30), P(56, 10), P(40, -2), P(16, 4)];
  let s = union([{ d: spline(pts, { closed: true, sharp: new Set([6]) }) }], color, { sw, box: [ax - 80, ay - 30, ax + 80, ay + 75] });
  s += path(spline([P(30, -14), P(54, -8), P(66, 12), P(66, 36)]), { fill: 'none', stroke: tone(color, 0.09), strokeWidth: 3.4, strokeLinecap: 'round' });
  s += path(spline([P(44, 4), P(56, 20), P(56, 42)]), { fill: 'none', stroke: tone(color, -0.08), strokeWidth: 2.6, strokeLinecap: 'round', opacity: 0.7 });
  const sc = P(20, -12);
  s += g(path(rrect(-9, -12, 18, 24, 8), { fill: grad('#FF6FAE', 'd'), stroke: stroke('#FF6FAE'), strokeWidth: f1(sw * 0.8) }) + path('M-4 -7L-4 6', { stroke: '#FFFFFF', strokeOpacity: 0.5, strokeWidth: 2.4, strokeLinecap: 'round' }), { transform: `translate(${f1(sc[0])} ${f1(sc[1])}) rotate(${f1(dir * 58 + sp)})` });
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
        if (sd > 0 && !Object.values(ctx.props || {}).includes('labeler')) s += labeler(pm.x, py + 2, 'R', sw * 0.85);
        s += path(rrect(pm.x - pw / 2, py, pw, 24, 5), { fill: grad(tone(c, -0.02), 'd'), stroke: stroke(c), strokeWidth: f1(sw * 0.8) });
      }
      return s + ribBand(ctx, tone(c, 0.05), 10);
    },
  },
};

// ======================================================================
// DAD — blue polo, side hair round a shiny bald top, thick moustache, WORLD'S BEST-ISH DAD mug
// ======================================================================
const OPEN_MOUTHS = new Set(['o', 'dOpen', 'laugh', 'grin', 'scream', 'wavyOpen', 'gritted', 'grimace', 'yawn', 'cry', 'evil', 'blech', 'ugh', 'v_small', 'v_E', 'v_A', 'v_O']);
const DAD_BAND = {
  t: 5,
  top: [[-2, -20], [-1.5, -25], [-1.08, -30], [-0.78, -18], [-0.6, -8], [0.6, -8], [0.78, -18], [1.08, -30], [1.5, -25], [2, -20]],
  bottom: [[-2, 18, 4], [-1.72, 20, 4], [-1.45, 18, 3], [-1.15, 12], [-0.95, 4], [-0.72, -4], [-0.6, -6], [0.6, -6], [0.72, -4], [0.95, 4], [1.15, 12], [1.45, 18, 3], [1.72, 20, 4], [2, 18]],
  mask: (u) => Math.abs(u) > 0.6,
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
      const shapes = bandPaths(DAD_BAND, ctx.head, ctx.yaw).map((d) => ({ d })).concat(limbLobes(DAD_BAND, ctx.yaw, [-25, -12, 1], 8.5, 5));
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
    const open = typeof faceSpec === 'string' ? ['shocked', 'scream', 'panic', 'laugh', 'happy', 'starstruck', 'cry', 'excited', 'yawn'].includes(faceSpec) : OPEN_MOUTHS.has(resolveFace(faceSpec).mouth);
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

// Dad in pyjamas: soft blue stripes, navy piping (notch collar, placket, pocket, cuffs, hems), navy slippers.
// Hair and moustache unchanged; no mug.
const PJ = { base: '#9DC2F2', stripe: '#6F9BE0', piping: '#3D58A8', slipper: '#4A57A6' };
DAD.outfits = {
  pyjamas: {
    ...DAD,
    top: { color: PJ.base, sleeve: true, cuff: PJ.piping, stripes: { color: PJ.stripe, n: 3, w: 0.15, op: 0.75, gap: 18, wT: 5.4 } },
    pants: { color: PJ.base, stripes: { color: PJ.stripe, n: 3, w: 0.14, op: 0.75 }, hem: PJ.piping },
    shoes: { color: PJ.slipper, sole: null, accent: '#C9D4FF' },
    pose: {}, props: {},
    decor: {
      neckFront(ctx) {
        const { torsoTop: T, sw, back, tm } = ctx, c = PJ.base, pc = PJ.piping;
        if (back) return path(`M-30 ${f1(T + 2)}Q0 ${f1(T + 14)} 30 ${f1(T + 2)}L28 ${f1(T - 4)}Q0 ${f1(T + 6)} -28 ${f1(T - 4)}Z`, { fill: grad(c, 'd'), stroke: pc, strokeWidth: f1(sw), strokeLinejoin: 'round' });
        let s = '';
        // V neckline (skin) then notch lapels with piping
        const m = tm(0), k = Math.max(0.4, m.k);
        s += path(`M${f1(m.x - 15 * k)} ${f1(T + 1)}L${f1(m.x)} ${f1(T + 26)}L${f1(m.x + 15 * k)} ${f1(T + 1)}Z`, { fill: grad(DAD.skin, 'd'), stroke: stroke(DAD.skin), strokeWidth: f1(sw * 0.8), strokeLinejoin: 'round' });
        for (const sd of [-1, 1]) {
          const a = tm(sd * 3), b = tm(sd * 34), cc = tm(sd * 22), e = tm(sd * 6); if (b.k < 0.2) continue;
          s += path(roundPoly([[a.x, T + 27, 2], [b.x, T - 1, 3], [cc.x, T + 12, 2], [tm(sd * 26).x, T + 26, 3], [e.x, T + 36, 2]]), { fill: grad(tone(c, 0.04), 'd'), stroke: pc, strokeWidth: f1(sw * 1.05), strokeLinejoin: 'round' });
        }
        return s;
      },
      torso(ctx) {
        const { torsoTop: T, torsoBot: B, sw, back, tm } = ctx, pc = PJ.piping;
        if (back) return '';
        const m = tm(0), k = Math.max(0.4, m.k);
        let s = path(`M${f1(m.x)} ${f1(T + 34)}L${f1(m.x + 2 * k)} ${f1(B - 4)}`, { stroke: pc, strokeWidth: f1(sw * 0.9), strokeLinecap: 'round', fill: 'none' });
        for (let i = 0; i < 3; i++) s += circle(m.x + 7 * k, T + 46 + i * 24, 3.6, { fill: grad('#FFFFFF', 'd'), stroke: pc, strokeWidth: 1.5 });
        const pm = tm(-30);
        if (pm.k > 0.3) {
          const pw = 26 * pm.k;
          s += path(rrect(pm.x - pw / 2, T + 34, pw, 26, 5), { fill: grad(tone(PJ.base, -0.02), 'd'), stroke: stroke(PJ.base), strokeWidth: f1(sw * 0.8) })
            + path(`M${f1(pm.x - pw / 2 + 1)} ${f1(T + 36)}L${f1(pm.x + pw / 2 - 1)} ${f1(T + 36)}`, { stroke: pc, strokeWidth: f1(sw * 1.1), strokeLinecap: 'round' });
        }
        s += path(`M${f1(-ctx.wb / 2 + 6)} ${f1(B - 3)}L${f1(ctx.wb / 2 - 6)} ${f1(B - 3)}`, { stroke: pc, strokeWidth: f1(sw * 0.9), strokeLinecap: 'round', opacity: 0.85 });
        return s;
      },
    },
  },
};

// ======================================================================
// BRIGGS — mustard sweater vest, bow tie, round glasses, comb-over
// ======================================================================
const BRIGGS_BAND = {
  t: 4,
  top: [[-2, -16], [-1.5, -20], [-1.08, -25], [-0.82, -14], [-0.72, -8], [0.72, -8], [0.82, -14], [1.08, -25], [1.5, -20], [2, -16]],
  bottom: [[-2, 14, 3], [-1.7, 16, 3], [-1.4, 13, 3], [-1.12, 8], [-0.9, -2], [-0.72, -4], [0.72, -4], [0.9, -2], [1.12, 8], [1.4, 13, 3], [1.7, 16, 3], [2, 14]],
  mask: (u) => Math.abs(u) > 0.72,
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
      const shapes = bandPaths(BRIGGS_BAND, ctx.head, ctx.yaw).map((d) => ({ d })).concat(limbLobes(BRIGGS_BAND, ctx.yaw, [-18, -8, 2], 7, 4));
      let s = shapes.length ? union(shapes, PAL.briggsHair, { sw: ctx.sw, box: [-56, -36, 56, 24] }) : '';
      // three comb-over strands across the bald top
      const sy = sind(ctx.yaw) * 8, kx = 0.5 + 0.5 * Math.abs(cosd(ctx.yaw));
      for (const [y0, y1, lift] of [[-22, -44, -56], [-17, -33, -44], [-12, -22, -31]]) {
        if (ctx.back) break;
        const d = `M${f1(-47 * kx + sy)} ${y0}Q${f1(-8 * kx + sy)} ${lift} ${f1(36 * kx + sy)} ${y1}`;
        s += path(d, { fill: 'none', stroke: lc, strokeWidth: f1(3.2 + ctx.sw * 2), strokeLinecap: 'round' }) + path(d, { fill: 'none', stroke: PAL.briggsHair, strokeWidth: 3.2, strokeLinecap: 'round' });
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
    front(ctx) {
      const sx = 18 * sind(ctx.yaw), k = Math.max(0.55, Math.abs(cosd(ctx.yaw)) * 0.55 + 0.45);
      const P = (x, y) => [sx + x * k, y];
      const q = [P(-46, -44), P(-42, -64), P(-18, -86), P(-20, -70), P(8, -94), P(4, -74), P(38, -86), P(30, -66), P(48, -66), P(44, -46)];
      const qd = spline(q, { closed: true, sharp: new Set([2, 3, 4, 5, 6, 7, 8]) });
      const helm = helmetPath(KEVIN_HAIR, ctx.head, ctx.yaw);
      let s = union([{ d: helm.d }, { d: qd }], PAL.kevinHair, { sw: ctx.sw, box: [-56, -96, 56, 10] });
      // frosted tips: the top of the quiff fades to pale gold
      const fid = fxDef('kevfrost', `<linearGradient id="kevfrost" gradientUnits="userSpaceOnUse" x1="0" y1="-58" x2="0" y2="-92"><stop offset="0" stop-color="#FFF2C6" stop-opacity="0"/><stop offset="0.55" stop-color="#FFF2C6" stop-opacity="0.75"/><stop offset="1" stop-color="#FFF8E2" stop-opacity="0.95"/></linearGradient>`);
      s += path(qd, { fill: `url(#${fid})` });
      s += path(spline([P(-30, -56), P(-14, -74), P(2, -82)]), { fill: 'none', stroke: tone(PAL.kevinHair, -0.1), strokeWidth: 2.6, strokeLinecap: 'round', opacity: 0.6 })
        + path(spline([P(-6, -58), P(12, -72), P(26, -76)]), { fill: 'none', stroke: tone(PAL.kevinHair, -0.1), strokeWidth: 2.6, strokeLinecap: 'round', opacity: 0.6 });
      s += strands([{ y: -44, u0: -0.5, u1: 0.45, amp: 1.4, waves: 2 }], ctx.head, ctx.yaw, PAL.kevinHair, KEVIN_HAIR);
      return s;
    },
  },
  faceUnder(ctx) {
    // tiny soul patch, under the mouth so open mouths cover it
    if (ctx.back) return '';
    const mm = mapFeature(0, ctx.yaw);
    return path(`M${f1(mm.x - 2.6)} 40.5L${f1(mm.x + 2.6)} 40.5L${f1(mm.x)} 45Z`, { fill: tone(PAL.kevinHair, -0.2), stroke: tone(PAL.kevinHair, -0.3), strokeWidth: 1.2, strokeLinejoin: 'round' });
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
  const f = drawFace(withAdd(res, o.add), { yaw, skin: fur, look: o.look, top: head.top - 26, headBox: head, ...spec.faceOpts });
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

// ======================================================================
// TINY — Kevin's dog. Caramel puppy, cream muzzle / bib / paws, chocolate floppy ears, a patch over one eye,
// a red collar with a gold bone tag reading TINY. Sits (default) or stands; grows to house size in the hook.
//   pose: { sit (1 sit / 0 stand), head, lean, bob, headTurn, ears | earL | earR (deg: 0 hang, + lift outward,
//           ~120 straight up), flop (extra tip droop), tail (deg), wag (-1..1 side swing), tongue (0..1.5),
//           pawL | pawR (front-leg raise, deg), legFL legFR legHL legHR (standing swing, deg, + forward) }
//   o.lod: detail level (defaults to s): >= 1.2 toe lines, >= 1.5 muzzle dots, >= 1.8 TINY on the tag, >= 2.5 fur tufts
// ======================================================================
const TINY = {
  name: 'TINY', color: '#E99A4F', dog: true,
  fur: '#EFA75F', cream: '#FFF1DE', ear: '#A35F3B', patch: '#B86C40', nose: '#3A2833', collar: '#E2404A', tag: '#FFD43B',
  dims: { head: { w: 126, h: 104, r: 0.38 } },
  faceOpts: { eyeX: 21, eyeY: -5, eyeR: 12.8, mouthY: 24, browColor: '#5E3422', browLen: 13, browW: 5.2 },
};
const DOG_MOUTH = { smile: 'dogW', flat: 'dogW', meh: 'dogW', set: 'dogW', smirk: 'dogW', cat: 'dogW', wavy: 'dogW', tongueOut: 'dogW',
  bigSmile: 'dogPant', dOpen: 'dogPant', laugh: 'dogPant', grin: 'dogPant', blech: 'dogPant' };
// dog versions of the face presets (any face.js preset still works; its mouth is mapped onto the muzzle)
export const DOG_FACES = {
  neutral: { eyes: 'bean', brows: 'neutral', mouth: 'dogW', tongue: 0.35 },
  happy: { eyes: 'happy', brows: 'raised', mouth: 'dogPant', tongue: 1, add: { blush: 0.7 } },
  excited: { eyes: 'ring', pupil: 0.52, look: [0, -1], brows: 'raised', mouth: 'dogPant', tongue: 1.35, add: { sparkle: 1, blush: 0.6 } },
  shocked: { eyes: 'ring', pupil: 0.3, brows: 'raised', mouth: 'o', add: { shock: 1 } },
  confused: { eyes: 'ring', eyeL: { scale: 0.86, look: [2, -1] }, eyeR: { scale: 1.12, look: [-1, -1] }, brows: 'skeptic', mouth: 'dogW', add: { q: 1 } },
  sad: { eyes: 'teary', brows: 'sad', mouth: 'dogW', look: [0, 2] },
  love: { eyes: 'heart', brows: 'raised', mouth: 'dogPant', tongue: 1, add: { hearts: 1, blush: 1 } },
  sleepy: { eyes: 'closed', brows: 'soft', mouth: 'dogW', add: { zzz: 1 } },
  guilty: { eyes: 'bean', look: [-5, 3], brows: 'worry', mouth: 'dogW', add: { sweat: 1 } },
};
// default ear / head acting per face when the pose leaves them unset
const DOG_ACT = { shocked: { earL: 128, earR: 128 }, excited: { earL: 42, earR: 42 }, happy: { earL: 14, earR: 14 },
  confused: { earL: 70, earR: -4, head: 11 }, scared: { earL: -12, earR: -12 }, sad: { earL: -14, earR: -14 }, love: { earL: 30, earR: 30 } };
const ellD = (cx, cy, rx, ry) => `M${f1(cx - rx)} ${f1(cy)}a${f1(rx)} ${f1(ry)} 0 1 0 ${f1(2 * rx)} 0a${f1(rx)} ${f1(ry)} 0 1 0 ${f1(-2 * rx)} 0Z`;
// a bone-shaped tag centred at 0,0 (w x h)
function bonePath(w, h) {
  const r = h * 0.36, x = w / 2 - r * 0.9, n = h * 0.2;
  return `M${f1(-x)} ${f1(-n)}L${f1(x)} ${f1(-n)}A${f1(r)} ${f1(r)} 0 1 1 ${f1(x + r * 0.55)} ${f1(-n * 0.1)}A${f1(r)} ${f1(r)} 0 1 1 ${f1(x)} ${f1(n)}L${f1(-x)} ${f1(n)}A${f1(r)} ${f1(r)} 0 1 1 ${f1(-x - r * 0.55)} ${f1(n * 0.1)}A${f1(r)} ${f1(r)} 0 1 1 ${f1(-x)} ${f1(-n)}Z`;
}
// floppy ear: root -> mid -> tip chain; a = lift (deg, 0 hangs down), out = screen side (-1 / 1)
function dogEar(root, a, flop, out, len, wid, color, sw, inner) {
  const bend = 10 - Math.max(0, a) * 0.42 - flop;                 // lifted ears droop at the tip
  const d1 = [out * Math.sin(a * D2R), Math.cos(a * D2R)], a2 = a + bend;
  const d2 = [out * Math.sin(a2 * D2R), Math.cos(a2 * D2R)];
  const L1 = len * 0.52, L2 = len * 0.48;
  const mid = [root[0] + d1[0] * L1, root[1] + d1[1] * L1], tip = [mid[0] + d2[0] * L2, mid[1] + d2[1] * L2];
  const n1 = [-d1[1], d1[0]], n2 = [-d2[1], d2[0]];
  const w0 = wid * 0.36, w1 = wid * 0.5, w2 = wid * 0.42;
  const P = (p, n, w) => [p[0] + n[0] * w, p[1] + n[1] * w];
  const pts = [P(root, n1, w0), P(mid, n1, w1), P(tip, n2, w2 * 0.92), [tip[0] + d2[0] * wid * 0.32, tip[1] + d2[1] * wid * 0.32], P(tip, n2, -w2 * 0.92), P(mid, n1, -w1), P(root, n1, -w0)];
  const d = spline(pts, { closed: true });
  let s = union([{ d }], color, { sw, box: [Math.min(root[0], tip[0]) - wid, root[1] - wid, Math.max(root[0], tip[0]) + wid, Math.max(root[1], tip[1]) + wid] });
  if (inner) s += path(spline([P(mid, n1, w1 * 0.25), P(tip, n2, w2 * 0.2)]), { fill: 'none', stroke: tone(color, 0.08), strokeWidth: f1(wid * 0.16), strokeLinecap: 'round', opacity: 0.8 });
  return s;
}
function dogHead(spec, ctx, o) {
  const { yaw, head, sw, pose, lod } = ctx;
  const fur = spec.fur, cream = spec.cream;
  const sn = sind(yaw), aS = Math.abs(sn);
  // face spec: dog presets, smile-type mouths mapped onto the muzzle
  const fs = o.face || 'neutral';
  const pre = typeof fs === 'string' ? fs : fs.preset;
  let res = typeof fs === 'string' ? { ...(DOG_FACES[fs] || { preset: fs }) } : { ...(pre && DOG_FACES[pre] ? DOG_FACES[pre] : {}), ...fs, preset: pre && DOG_FACES[pre] ? undefined : pre };
  const base = { ...(res.preset ? (FACE_PRESETS_CACHE[res.preset] || {}) : {}), ...res };
  if (DOG_MOUTH[base.mouth]) res.mouth = DOG_MOUTH[base.mouth];
  if (res.to) { const t = typeof res.to === 'string' ? (DOG_FACES[res.to] || { preset: res.to }) : res.to; res = { ...res, to: t }; }
  const act = DOG_ACT[pre] || {};
  const ear = (sd) => pose[sd < 0 ? 'earL' : 'earR'] ?? pose.ears ?? act[sd < 0 ? 'earL' : 'earR'] ?? 0;
  const m0 = mapFeature(0, yaw);
  const mz = { x: m0.x * (1 + 0.28 * aS), y: 16, rx: 25 * (0.6 + 0.4 * Math.max(0.3, m0.k)) + 3 * aS, ry: 16.5 };
  let back = '', skull = '', front = '';
  // ears: far ear behind the skull, near ear(s) over it
  for (const sd of [-1, 1]) {
    const a = (sd * (0.8 + 0.34 * aS) * 90 + yaw) * D2R, x = 47 * Math.sin(a), z = Math.cos(a);
    const out = Math.abs(x) > 10 ? Math.sign(x) : -Math.sign(sn || 1);
    const e = dogEar([x * 0.96, head.top + 15], ear(sd), pose.flop || 0, out, 58, 30, spec.ear, sw, lod >= 1.2);
    if (z < 0.05) back += e; else front += e;
  }
  // skull
  const hp = rrect(-50, head.top, 100, head.bot - head.top, head.r);
  skull += path(hp, { fill: radial(fur, { cx: 0.36, cy: 0.32, r: 0.85 }), stroke: stroke(fur), strokeWidth: f1(sw), strokeLinejoin: 'round' });
  skull += path(hp, { fill: shadeBand(fur, { at: 0.875, op: 0.55, dL: 0.07 }) });
  skull += path(`M-41 ${f1(head.top + 30)}L-41 ${f1(head.bot - 22)}`, { stroke: '#FFFFFF', strokeOpacity: 0.5, strokeWidth: 4, strokeLinecap: 'round' });
  // top tuft
  {
    const tx = m0.x * 0.55, k = Math.max(0.55, m0.k);
    const T = (x, y) => [tx + x * k, head.top + y];
    const d = spline([T(-14, 6), T(-9, -9), T(-3, -2), T(3, -14), T(7, -2), T(14, -7), T(15, 6)], { closed: true, sharp: new Set([1, 3, 5]) });
    skull = union([{ d }], fur, { sw, box: [tx - 16, head.top - 16, tx + 16, head.top + 8] }) + skull;
  }
  // eye patch (screen-left eye) and cheek fluff
  {
    const m = mapFeature(-spec.faceOpts.eyeX, yaw);
    if (m.k > 0.25 && !(ctx.side && -yaw > 0)) skull += path(spline([[m.x - 18 * m.k, -7], [m.x - 8 * m.k, -24], [m.x + 10 * m.k, -24], [m.x + 19 * m.k, -7], [m.x + 11 * m.k, 9], [m.x - 9 * m.k, 10]], { closed: true }), { fill: grad(spec.patch, 'd'), opacity: 0.92 });
  }
  // muzzle (protrudes in profile) + philtrum, nose comes after the mouth
  skull += path(ellD(mz.x, mz.y, mz.rx, mz.ry), { fill: radial(cream, { cx: 0.42, cy: 0.3, r: 0.9 }), stroke: stroke(cream, 0.06), strokeWidth: f1(sw * 0.8) });
  if (lod >= 1.5) for (const sd of [-1, 1]) for (const [dx, dy] of [[9, 3], [13, 7], [8.5, 9]]) {
    const xx = mz.x + sd * dx * (mz.rx / 25); if (ctx.side && sd * yaw < 0 && Math.abs(xx - mz.x) > 6) continue;
    skull += circle(xx, mz.y + dy, 1.3, { fill: tone(cream, -0.18, 2) });
  }
  const f = drawFace(withAdd(res, o.add), { yaw, skin: fur, look: o.look, top: head.top - 14, headBox: head, ...spec.faceOpts, mouthShift: mz.x - m0.x, tongue: pose.tongue });
  const nx = mz.x + 6 * sn, ny = 6.5, nk = Math.max(0.55, m0.k);
  const nose = g(path('M-9 -4.5Q0 -8 9 -4.5Q10 1.5 3.5 5Q0 6.8 -3.5 5Q-10 1.5 -9 -4.5Z', { fill: grad(spec.nose, 'd', { up: 0.1, down: 0.04 }), stroke: stroke(spec.nose), strokeWidth: 1.6, strokeLinejoin: 'round' })
    + ellipse(-3, -3.6, 3.2, 1.6, { fill: '#FFFFFF', opacity: 0.75 }), { transform: `translate(${f1(nx)} ${f1(ny)}) scale(${f1(nk)} 1)` });
  const phil = path(`M${f1(nx)} ${f1(ny + 5)}L${f1(mz.x + 2 * sn)} ${f1(spec.faceOpts.mouthY - 2)}`, { stroke: '#1A1215', strokeWidth: 2.6, strokeLinecap: 'round', fill: 'none', opacity: 0.85 });
  return { svg: back + skull + f.face + phil + nose + front, fx: f.fx };
}
function buildDog(spec, o) {
  const pose = { sit: 1, head: 0, lean: 0, bob: 0, tail: 0, wag: 0, headTurn: 0, ...(o.pose || {}) };
  const sit = o.posture ? o.posture === 'sit' : pose.sit >= 0.5;
  let yaw = yawOf(o.facing ?? 'front');
  if (Math.abs(yaw) > 90) yaw = Math.sign(yaw) * 90;
  const by = Math.max(-90, Math.min(90, yaw * (sit ? 1.15 : 1.5)));           // the body turns a bit further than the head
  const s = o.s ?? 1, sw = 3.2, lod = o.lod ?? s;
  const fur = spec.fur, cream = spec.cream, farFur = tone(fur, -0.05, 1.04), farCream = tone(cream, -0.05);
  const sb = sind(by), cb = cosd(by);
  // 3D -> screen: f forward, l lateral (+ = dog's left = screen right in the front view), y up-negative
  const X = (f, l) => f * sb + l * cb, Z = (f, l) => f * cb - l * sb, far = (l) => -l * sb < -6;
  const rxOf = (rf, rl) => Math.hypot(rf * sb, rl * cb);
  const parts = [];        // { z, svg } drawn far -> near around the body union
  let bodyShapes = [], over = '', under = '', tailSvg = '';
  const foot = (f, l, y, rx, ry, isFar) => {
    const x = X(f, l), c = isFar ? farCream : cream;
    let s2 = union([{ d: ellD(x, y, rx * (0.75 + 0.25 * Math.abs(sb)), ry) }], c, { sw, box: [x - rx, y - ry, x + rx, y + ry] });
    if (lod >= 1.2 && !isFar) s2 += path(`M${f1(x - rx * 0.28)} ${f1(y + ry * 0.05)}v${f1(ry * 0.6)}M${f1(x + rx * 0.28)} ${f1(y + ry * 0.05)}v${f1(ry * 0.6)}`, { stroke: stroke(c), strokeWidth: 1.7, strokeLinecap: 'round', opacity: 0.65 });
    return s2;
  };
  const legCap = (f0, l, y0, f1_, y1, w0, w1, isFar) => {
    const a = [X(f0, l), y0], b = [X(f1_, l), y1], c = isFar ? farFur : fur;
    return union([{ d: taper(a[0], a[1], b[0], b[1], w0 / 2, w1 / 2) }], c, { sw, box: [Math.min(a[0], b[0]) - w0, a[1] - w0, Math.max(a[0], b[0]) + w0, b[1] + 4] })
      + (isFar ? '' : glossCapsule(a[0], a[1], b[0], b[1], (w0 + w1) / 2, { op: 0.28, thin: false, from: 0.15, to: 0.6 }));
  };
  let headC, neckTop, collarY, tailBase, shadowW;
  if (sit) {
    // haunches + hull + chest form one fur silhouette
    const hy = -38, cy = -98;
    for (const l of [-30, 30]) {
      const sh = { d: ellD(X(-12, l), hy, rxOf(36, 30), 37) };
      if (far(l)) parts.push({ z: -50, svg: union([sh], farFur, { sw, box: [-90, hy - 40, 90, 0] }) }); else bodyShapes.push(sh);
    }
    const hc = [X(-8, 0), -42], cc = [X(14, 0), cy];
    bodyShapes.push({ d: taper(hc[0], hc[1], cc[0], cc[1], 46, rxOf(30, 37)) }, { d: ellD(cc[0], cc[1], rxOf(30, 37), 36) });
    // bib on the chest
    const bk = Math.max(0, cb);
    if (bk > 0.15) over += path(ellD(X(30, 0), cy + 14, 21 * (0.55 + 0.45 * bk), 31), { fill: radial(cream, { cx: 0.4, cy: 0.3 }), opacity: Math.min(1, bk * 1.6) });
    // front legs (+ optional paw raise) and hind feet
    for (const l of [-17, 17]) {
      const isFar = far(l), raise = (l < 0 ? pose.pawL : pose.pawR) || 0;
      const top = [22 + (isFar ? 12 : 0), -84], len = 78, a = raise * D2R;
      const end = [top[0] + Math.sin(a) * len * 0.75, top[1] + Math.cos(a) * len];
      const svg = legCap(top[0], l, top[1], end[0], end[1] - 4, 26, 24, isFar) + foot(end[0] + 2, l, end[1] - 6, 16, 10.5, isFar);
      parts.push({ z: isFar ? -40 : Z(30, l) + 60, svg });
    }
    for (const l of [-40, 40]) { const isFar = far(l); parts.push({ z: isFar ? -45 : Z(8, l) + 40, svg: foot(8 + (isFar ? 14 : 0), l, -9, 18, 10.5, isFar) }); }
    headC = [X(18, 0), -170]; neckTop = -128; collarY = -113; tailBase = [X(-38, 0), -30]; shadowW = Math.max(rxOf(60, 70), 64) + 14;
  } else {
    const yb = -88, Hh = 35;
    const ch = [X(42, 0), yb], rp = [X(-42, 0), yb - 2];
    const rx = rxOf(36, 43);
    bodyShapes.push({ d: ellD(ch[0], ch[1], rx, Hh + 1) }, { d: ellD(rp[0], rp[1], rx * 0.98, Hh) });
    if (Math.abs(ch[0] - rp[0]) > 1) { const x0 = Math.min(ch[0], rp[0]), x1 = Math.max(ch[0], rp[0]); bodyShapes.push({ d: `M${f1(x0)} ${f1(yb - Hh)}L${f1(x1)} ${f1(yb - Hh)}L${f1(x1)} ${f1(yb + Hh - 1)}L${f1(x0)} ${f1(yb + Hh - 1)}Z` }); }
    // neck into the head
    bodyShapes.push({ d: taper(X(40, 0), yb - 18, X(56, 0), yb - 52, 30, 26) });
    // belly / bib
    if (aSide(sb)) over += path(ellD((ch[0] + rp[0]) / 2 + 8 * Math.sign(sb), yb + Hh * 0.55, Math.abs(ch[0] - rp[0]) * 0.42 + 10, 11), { fill: grad(cream, 'v'), opacity: 0.95 });
    if (cb > 0.3) over += path(ellD(X(70, 0), yb - 4, 22 * cb + 4, 27), { fill: radial(cream, { cx: 0.4, cy: 0.3 }), opacity: Math.min(1, cb * 1.4) });
    const legs = [[40, -19, pose.legFL || 0], [40, 19, pose.legFR || 0], [-40, -28, pose.legHL || 0], [-40, 28, pose.legHR || 0]];
    for (const [f, l, sw_] of legs) {
      const isFar = far(l), hind = f < 0, a = sw_ * D2R * Math.sign(sb || 1);
      const top = [f + (isFar ? 13 : 0), yb + 6 + 16 * cb * cb], len = 76 - 16 * cb * cb;
      const end = [f + Math.sin(sw_ * D2R) * len * 0.6, top[1] + Math.cos(a) * len];
      const svg = legCap(top[0], l, top[1], end[0], end[1] - 4, hind ? 30 : 25, 23, isFar) + foot(end[0] + 3 * Math.sign(sb), l, end[1] - 7, 15.5, 10, isFar);
      parts.push({ z: isFar ? -40 : Z(f, l) + (hind ? 20 : 40), svg });
    }
    headC = [X(64, 0), -142 - 30 * cb * cb]; neckTop = -110; collarY = headC[1] + 44; tailBase = [X(-70, 0), yb - 18]; shadowW = Math.max(rxOf(110, 50), 60) + 10;
  }
  // tail: thick curl with a cream tip; wags about its base
  {
    const side = Math.abs(sb) > 0.25 ? -Math.sign(sb) : 1;
    const wag = (pose.wag || 0) * 32 + (pose.tail || 0);
    const P = (x, y) => rotPt([tailBase[0] + side * x, tailBase[1] + y], tailBase, wag * side);
    const pts = sit ? [P(0, 0), P(30, -6), P(48, -26), P(52, -50), P(46, -64)] : [P(0, 0), P(18, -18), P(28, -40), P(26, -60), P(20, -70)];
    const d = spline(pts);
    const tipD = spline(pts.slice(3));
    tailSvg = path(d, { fill: 'none', stroke: stroke(fur), strokeWidth: f1(17 + sw * 2), strokeLinecap: 'round' }) + path(d, { fill: 'none', stroke: grad(fur, 'd', { box: [tailBase[0] - 60, tailBase[1] - 80, tailBase[0] + 60, tailBase[1] + 10] }), strokeWidth: 17, strokeLinecap: 'round' })
      + path(tipD, { fill: 'none', stroke: cream, strokeWidth: 13, strokeLinecap: 'round' })
      + path(spline(pts.slice(1, 4)), { fill: 'none', stroke: '#FFFFFF', strokeOpacity: 0.35, strokeWidth: 4, strokeLinecap: 'round' });
  }
  const tailFront = !sit && Math.abs(sb) < 0.2;          // standing, facing us: tail pokes up behind the body
  let body = union(bodyShapes, fur, { sw, box: [-120, sit ? -140 : -130, 120, -20] });
  body += path(bodyShapes[sit ? bodyShapes.length - 1 : 0].d, { fill: shadeBand(fur, { at: 0.86, op: 0.35 }) });
  body += over + glossBox(-46, sit ? -132 : -120, 86, sit ? 110 : 64, { op: 0.28, top: false, sw: 4.4 });
  parts.sort((p, q) => p.z - q.z);
  const behind = parts.filter((p) => p.z < 0).map((p) => p.svg).join(''), infront = parts.filter((p) => p.z >= 0).map((p) => p.svg).join('');
  // collar + bone tag (TINY at close range)
  let collar = '';
  {
    const cx = headC[0] * (sit ? 0.9 : 0.86), w = sit ? 84 : 66, c = spec.collar;
    const k = sit ? 1 : 0.7 + 0.3 * Math.abs(cb);
    const d = `M${f1(cx - w / 2)} ${f1(collarY - 6)}Q${f1(cx)} ${f1(collarY + 10)} ${f1(cx + w / 2)} ${f1(collarY - 6)}L${f1(cx + w / 2 - 2)} ${f1(collarY + 6)}Q${f1(cx)} ${f1(collarY + 22)} ${f1(cx - w / 2 + 2)} ${f1(collarY + 6)}Z`;
    collar += path(d, { fill: grad(c, 'd'), stroke: stroke(c), strokeWidth: f1(sw), strokeLinejoin: 'round', transform: k !== 1 ? `translate(${f1(cx)} 0) scale(${f1(k)} 1) translate(${f1(-cx)} 0)` : undefined });
    if (lod >= 1.5) collar += path(`M${f1(cx - w / 2 + 6)} ${f1(collarY + 1)}Q${f1(cx)} ${f1(collarY + 16)} ${f1(cx + w / 2 - 6)} ${f1(collarY + 1)}`, { fill: 'none', stroke: '#FFFFFF', strokeOpacity: 0.55, strokeWidth: 1.6, strokeDasharray: '4 3', strokeLinecap: 'round' });
    const tx = cx + 6 * sb, ty = collarY + 26, tc = spec.tag;
    collar += circle(tx, ty - 9, 3.2, { fill: 'none', stroke: stroke(tc), strokeWidth: 2.4 });
    collar += g(path(bonePath(34, 15), { fill: grad(tc, 'd', { up: 0.08, down: 0.1 }), stroke: stroke(tc), strokeWidth: f1(sw * 0.75), strokeLinejoin: 'round' })
      + path('M-11 -3.2L5 -3.2', { stroke: '#FFFFFF', strokeOpacity: 0.7, strokeWidth: 2, strokeLinecap: 'round' })
      + (lod >= 1.8 ? text(0, 3.3, 'TINY', { fontFamily: FONT_DISPLAY, fontSize: 9.4, fill: stroke(tc), textAnchor: 'middle', letterSpacing: 0.6 }) : ''),
    { transform: `translate(${f1(tx)} ${f1(ty)}) rotate(${f1(-pose.head * 0.4 + 4 * sb)}) scale(${f1(Math.max(0.6, Math.abs(cb) * 0.4 + 0.6))} 1)` });
  }
  // fur tufts on the chest at house size
  if (lod >= 2.5 && sit && cb > 0.3) for (const [dx, dy] of [[-8, -86], [6, -80], [-2, -70]]) collar += path(`M${f1(X(30, 0) + dx)} ${f1(dy)}q3 5 7 1`, { fill: 'none', stroke: tone(cream, -0.12), strokeWidth: 2, strokeLinecap: 'round' });
  // head
  const hd = spec.dims.head, hh = (100 * hd.h) / hd.w, head = { top: -hh / 2, bot: hh / 2, r: hd.r * 100 };
  const lsw = (sw * 100) / hd.w;
  const hyaw = Math.max(-90, Math.min(90, yaw + (pose.headTurn || 0)));
  const hctx = { yaw: hyaw, head, sw: lsw, pose, lod, side: Math.abs(hyaw) > 75 };
  const H = dogHead(spec, hctx, { ...o, pose });
  const act = DOG_ACT[typeof o.face === 'string' ? o.face : o.face?.preset] || {};
  const tilt = pose.head || act.head || 0;
  const hsc = hd.w / 100;
  const headG = g(H.svg, { transform: `translate(${f1(headC[0])} ${f1(headC[1])}) rotate(${f1(tilt)}) scale(${f1(hsc)})` });
  const fxG = g(H.fx, { transform: `translate(${f1(headC[0])} ${f1(headC[1])}) rotate(${f1(tilt)}) scale(${f1(hsc)})` });
  void neckTop;
  const upper = (tailFront ? '' : tailSvg) + behind + body + (tailFront ? tailSvg : '') + infront + collar + headG + fxG;
  const upperG = g(upper, { transform: `translate(0 ${f1(pose.bob)}) rotate(${f1(pose.lean)} 0 0)` });
  const shadow = o.shadow === false ? '' : contactShadow(0, 2, shadowW, 11, { op: 0.3 });
  return g(shadow + upperG, { transform: `translate(${f1(o.x ?? 0)} ${f1(o.y ?? 0)}) scale(${f1(s * 1000) / 1000})` });
}
const aSide = (sb) => Math.abs(sb) > 0.35;
// tail wag helper for shots: wag(t, hz = 2.5, amp = 1) -> -amp..amp (pose.wag)
export const wag = (t, hz = 2.5, amp = 1) => amp * Math.sin(2 * Math.PI * hz * t);

// ---------- registry ----------
for (const c of [SAM, LILY, MOM, DAD, BRIGGS, KEVIN, DAD.outfits.pyjamas]) c.drawProp = drawProp;
export const CAST = { sam: SAM, lily: LILY, mom: MOM, dad: DAD, pickles: PICKLES, briggs: BRIGGS, kevin: KEVIN, tiny: TINY };
export const CAST_IDS = ['sam', 'lily', 'mom', 'dad', 'pickles', 'briggs', 'kevin', 'tiny'];
export const HUMANS = ['sam', 'lily', 'mom', 'dad', 'briggs', 'kevin'];
const pick = (o, k) => (o[k] !== undefined ? o[k] : o.add && o.add[k] !== undefined ? o.add[k] : undefined);
function buildAny(spec, o) { return spec.cat ? buildCat(spec, o) : spec.dog ? buildDog(spec, o) : buildFigure(spec, o); }
export function toon(id, o = {}) {
  const spec0 = CAST[id];
  if (!spec0) throw new Error('unknown cast id ' + id);
  const outfit = pick(o, 'outfit'), tint = pick(o, 'tint'), light = pick(o, 'light'), legs = pick(o, 'legs');
  const mq = Math.max(0, Math.min(1, +(pick(o, 'mannequin') ?? (pick(o, 'variant') === 'default' ? 1 : 0)) || 0));
  const spec = outfit && spec0.outfits?.[outfit] ? spec0.outfits[outfit] : spec0;
  if (!(mq > 0) && !tint && !(light && light.k > 0) && legs === undefined && spec === spec0) return buildAny(spec, o);   // the plain path
  let oo = o;
  if (mq > 0 || legs !== undefined) oo = { ...o, blank: mq, legs };
  const fxT = tint && tint.k > 0 ? fxTint(tint.color, tint.k, tint.mode) : null, fxM = fxMannequin(mq);
  const build = (q) => withFx(fxT, () => withFx(fxM, () => buildAny(spec, q)));
  if (!(light && light.k > 0)) return build(oo);
  // lit: build in local space, then a light-coloured overlay masked by a light-mask copy of the same build
  const local = { ...oo, x: 0, y: 0, s: 1 };
  PROP_AT = null;
  const body = build(local);
  const propAt = PROP_AT;
  const mask = withFx(fxLightMask(), () => buildAny(spec, { ...local, shadow: false }));
  return g(body + lightOverlay(id, spec, oo, light, propAt, mask), { transform: `translate(${f1(o.x ?? 0)} ${f1(o.y ?? 0)}) scale(${f1((o.s ?? 1) * 1000) / 1000})` });
}
// light overlay in body units. from: 'below' (chin up), 'phone' (radial from the held phone), [x, y] (radial from a
// body-unit point, origin at the feet), 'left' | 'right' | 'above' (linear wash from that side), 'front' (flat).
function lightOverlay(id, spec, o, L, propAt, maskSvg) {
  const Ht = toonHeight(id), hy = toonHeadY(id), hh = spec.dims.head.h;
  const box = [-Ht * 0.75 - 60, -Ht - 80, Ht * 0.75 + 60, 30];
  const c = L.color || '#CFE8FF', k = Math.min(1, L.k), from = L.from || 'below';
  const mid = uid('lm'), gid = uid('lg');
  let paint;
  const pose = { lean: 0, bob: 0, ...(spec.pose || {}), ...(o.pose || {}) };
  const lean = (p) => { if (spec.cat || spec.dog) return [p[0], p[1] + (pose.bob || 0)]; const hip = hipYOf(spec), a = (pose.lean || 0) * D2R, dx = p[0], dy = p[1] - hip; return [dx * Math.cos(a) - dy * Math.sin(a), hip + dx * Math.sin(a) + dy * Math.cos(a) + (pose.bob || 0)]; };
  if (from === 'below' || from === 'phone' || Array.isArray(from)) {
    // a phone's screen faces the character, so its light pool sits between the phone and the face
    const P = Array.isArray(from) ? from : from === 'phone' && propAt ? (([x, y]) => [x * 0.6, y - hh * 0.42])(lean(propAt)) : [0, hy + hh * 0.75];
    const r = L.r || hh * (from === 'phone' ? 1.35 : 1.25);
    const op = (v) => f1(k * v * 100) / 100;
    addDef(gid, `<radialGradient id="${gid}" gradientUnits="userSpaceOnUse" cx="${f1(P[0])}" cy="${f1(P[1])}" r="${f1(r)}"><stop offset="0" stop-color="${c}" stop-opacity="${op(0.85)}"/><stop offset="0.3" stop-color="${c}" stop-opacity="${op(0.55)}"/><stop offset="0.65" stop-color="${c}" stop-opacity="${op(0.2)}"/><stop offset="1" stop-color="${c}" stop-opacity="0"/></radialGradient>`);
  } else {
    const [x1, y1, x2, y2] = from === 'left' ? [box[0] * 0.55, 0, box[2] * 0.35, 0] : from === 'right' ? [box[2] * 0.55, 0, box[0] * 0.35, 0] : from === 'above' ? [0, -Ht - 20, 0, -Ht * 0.25] : [0, 0, 0, 1];
    const flat = from === 'front';
    addDef(gid, `<linearGradient id="${gid}" gradientUnits="userSpaceOnUse" x1="${f1(x1)}" y1="${f1(y1)}" x2="${f1(x2)}" y2="${f1(y2)}"><stop offset="0" stop-color="${c}" stop-opacity="${f1(k * 0.85 * 100) / 100}"/><stop offset="1" stop-color="${c}" stop-opacity="${flat ? f1(k * 0.85 * 100) / 100 : 0}"/></linearGradient>`);
  }
  paint = `url(#${gid})`;
  addDef(mid, `<mask id="${mid}" maskUnits="userSpaceOnUse" x="${f1(box[0])}" y="${f1(box[1])}" width="${f1(box[2] - box[0])}" height="${f1(box[3] - box[1])}">${maskSvg}</mask>`);
  let s = rect(box[0], box[1], box[2] - box[0], box[3] - box[1], { fill: paint, mask: `url(#${mid})` });
  return s;
}

// height above ground (body units at s=1) and head centre, for framing
export function toonHeight(id) {
  const spec = CAST[id];
  if (spec.cat) return spec.dims.body.h + spec.dims.head.h * 1.15 + 20;
  if (spec.dog) return 236;
  return figureHeight(spec);
}
export function toonHeadY(id, o = {}) {
  const spec = CAST[id];
  if (spec.cat) { const hd = spec.dims.head; return -spec.dims.body.h - ((100 * hd.h) / hd.w) * (hd.w / 100) * 0.36; }
  if (spec.dog) return (o.posture === 'stand' || (o.pose && o.pose.sit === 0)) ? -142 - 30 * Math.cos(Math.min(90, Math.abs(yawOf(o.facing ?? 'front')) * 1.5) * D2R) ** 2 : -170;
  return headCenterY(spec);
}
// hip height (body units, negative = above the feet): place a legs:false figure on a mattress / seat
export function toonHipY(id) { const spec = CAST[id]; return spec.cat || spec.dog ? 0 : hipYOf(spec); }

// ---------- reach: two-bone IK for the arms ----------
// reach(id, 'L' | 'R', [x, y], {facing, shrug, elbow: 'out' | 'in'}) -> {arm, fore} angles that put the hand point
// (the grip point props hang from) at [x, y] in body units (origin at the feet, s = 1). Unreachable targets get a
// straight arm pointing at them. Use it for hand-to-face poses: posePreset() does for the common ones.
export function reach(id, side, target, o = {}) {
  const spec = CAST[id], d = spec.dims, yaw = yawOf(o.facing ?? 'front');
  const ankleY = -d.shoe.h * 0.62, hipY = ankleY - d.leg.len, torsoBot = hipY + (d.torso.hipOverlap ?? 14), torsoTop = torsoBot - d.torso.h;
  const sy = torsoTop + (d.torso.shoulder ?? 20) - 9 * Math.max(0, Math.min(1.3, o.shrug || 0));
  const shX = d.torso.wt / 2 + d.arm.w * (d.arm.out ?? 0.02), cs = Math.cos(yaw * D2R);
  const sx = (side === 'L' ? -1 : 1) * shX * cs, sgn = side === 'L' ? 1 : -1;
  const L1 = d.arm.up, L2 = d.arm.fore + d.arm.hand * 0.75;
  const tx = target[0] - sx, ty = target[1] - sy, D = Math.min(L1 + L2 - 0.01, Math.max(Math.abs(L1 - L2) + 0.01, Math.hypot(tx, ty)));
  const ang = (vx, vy) => Math.atan2(-sgn * vx, vy) / D2R;              // inverse of dirDown(a, sgn) = [-sgn sin a, cos a]
  const base = ang(tx, ty), al = Math.acos(Math.max(-1, Math.min(1, (L1 * L1 + D * D - L2 * L2) / (2 * L1 * D)))) / D2R;
  const sols = [base + al, base - al].map((a) => {
    const ex = sx - sgn * Math.sin(a * D2R) * L1, ey = sy + Math.cos(a * D2R) * L1;
    let f = ang(target[0] - ex, target[1] - ey) - a; f = ((f + 540) % 360) - 180;
    const an = ((a + 450) % 360) - 90;                                     // arm angle in (-90, 270]
    return { arm: Math.round(an * 10) / 10, fore: Math.round(f * 10) / 10, ex };
  });
  const out = (o.elbow ?? 'out') === 'out';
  sols.sort((p, q) => (out ? Math.abs(q.ex) - Math.abs(p.ex) : Math.abs(p.ex) - Math.abs(q.ex)));
  return { arm: sols[0].arm, fore: sols[0].fore };
}
// head-local point (head units: x -50..50, y about -47..47, centre 0,0) -> body units, for reach() targets
export function headPoint(id, [hx, hy], o = {}) {
  const spec = CAST[id], k = spec.dims.head.w / 100, shrug = Math.max(0, Math.min(1.3, o.shrug || 0));
  return [hx * k, headCenterY(spec) + 6 * shrug + hy * k];
}
// ---------- pose presets ----------
// posePreset(name, id, o) -> a pose object (merge it, or use it as a pose key). Names:
//   shrug       tiny shrug: shoulders up, palms out at the hips (the "...Ish." beat)
//   shieldEyes  one hand flat over the brow like a visor (R hand; o.side 'L' for the other one)
//   phoneUp     phone held up at chin height in the R hand (screen toward the face; use props {R: 'phoneBack'})
//   phoneChest  phone at chest height, L hand steadying it; phoneLap: lowered to the lap. Tween up -> lap to lower it
//   bedSit      phoneChest + leaning back a touch (pair with legs: false and toonHipY for the mattress line)
//   yawnStretch both fists up; yawnCover: L fist to the mouth; pointUp: "ONE thing" finger raised
export function posePreset(name, id = 'sam', o = {}) {
  const spec = CAST[id], hd = spec.dims.head.h, f = o.facing;
  const R = (side, hp, extra = {}) => { const r = reach(id, side, headPoint(id, hp, o), { facing: f, shrug: o.shrug, elbow: extra.elbow }); return side === 'L' ? { armL: r.arm, foreL: r.fore } : { armR: r.arm, foreR: r.fore }; };
  const chestY = (k) => { const hy = headCenterY(spec); return hy + hd * 0.5 + spec.dims.torso.h * k; };
  const RB = (side, x, y, extra = {}) => { const r = reach(id, side, [x, y], { facing: f, elbow: extra.elbow }); return side === 'L' ? { armL: r.arm, foreL: r.fore } : { armR: r.arm, foreR: r.fore }; };
  switch (name) {
    case 'shrug': return { shrug: 1, armL: 14, foreL: 100, armR: 14, foreR: 100, handL: 'flat', handR: 'flat', head: -4 };
    case 'shieldEyes': {
      const sd = o.side === 'L' ? 'L' : 'R', sg = sd === 'L' ? -1 : 1;
      return { ...R(sd, [sg * 15, -12]), [sd === 'L' ? 'handL' : 'handR']: 'flat', ...(sd === 'R' ? { armL: 14, foreL: 18 } : { armR: 14, foreR: 18 }), head: -sg * 3 };
    }
    case 'phoneUp': return { ...R('R', [10, 62]), handR: 'grip', armL: 10, foreL: 20 };
    case 'phoneChest': return { ...RB('R', 6, chestY(0.32)), ...RB('L', -8, chestY(0.38), { elbow: 'out' }), handL: 'open', handR: 'grip' };
    case 'phoneLap': return { ...RB('R', 8, chestY(0.82)), armL: 12, foreL: 30, handR: 'grip' };
    case 'bedSit': return { ...posePreset('phoneChest', id, o), lean: -3 };
    case 'yawnStretch': return { armL: 162, armR: 162, foreL: -24, foreR: -24, handL: 'fist', handR: 'fist', head: -4 };
    case 'yawnCover': return { ...R('L', [-4, 40]), handL: 'fist' };
    case 'pointUp': return { armR: 34, foreR: 128, handR: 'point', armL: 10, foreL: 14 };
    default: return {};
  }
}
export const POSE_NAMES = ['shrug', 'shieldEyes', 'phoneUp', 'phoneChest', 'phoneLap', 'bedSit', 'yawnStretch', 'yawnCover', 'pointUp'];
export function toonHeadSize(id) { const hd = CAST[id].dims.head; return hd.h; }
