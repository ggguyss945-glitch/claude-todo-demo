// transitions.js — edits between two shots (bible 3.5). A transition is declared on the incoming shot as
// `tin: {type, dur, ...}` (or on the outgoing one as `tout`). Near the boundary b = B.start the frame renderer draws
// both neighbours (A keeps running past its end, B starts before its start: shots must accept t outside 0..dur)
// and hands them to the transition as lazy thunks A(), B() that return each shot's full-frame SVG.
//
//   type         window around b          what it does
//   cut          -                         hard cut (default)
//   whip         [b - d/2, b + d/2]        both shots slide as one strip (bell-shaped velocity, easeInOutCubic) with
//                d = 0.15-0.25 s           directional blur on the strip (blurK 0.2 x px/frame, about a 250-degree shutter;
//                                          max 64 px) + white speed streaks; dir 'left'|'right'|'up'|'down' = direction the
//                                          camera pans; ease 'front' = front-loaded outQuart. blur:false: crisp art + streaks
//   flash        [b - 2f, b + d]           white (or color) frame: ramps up over 2 frames, holds `hold` frames, decays
//   glitch       [b - d/2, b + d/2]        2-frame RGB band slices re-rolled every 2 frames, A before b, B after
//                                          (slices are re-drawn string copies, never <use>, so blend layers survive)
//   zoomThrough  [b - d, b]                push A into a screen rect (rect: [x, y, w, h, r] in A's screen space, or
//                                          the portal A's shot sets with ctx.portal(...)) while B grows from it
//   dipBlack     [b - d/2, b + d/2]        A fades to black, B fades up from black (color for a dip to white etc.)
//   cardSlam     [b, b + d]                B slams in: scale from 1.35 to 1 in 40% of d, 1-frame white hit, shake
import { FPS, clamp, lerp, seg, ease, rand, shake as shakeFn } from './motion.js';
import { motionBlur, W, H, CX, CY } from './camera.js';
import { speedLines } from '../fx.js';

const r3 = (n) => Math.round(n * 1000) / 1000;
const solid = (color, op) => (op <= 0.001 ? '' : `<rect x="-40" y="-40" width="${W + 80}" height="${H + 80}" fill="${color}" opacity="${r3(Math.min(1, op))}"/>`);
const tx = (svg, x, y) => (Math.abs(x) < 1e-3 && Math.abs(y) < 1e-3 ? svg : `<g transform="translate(${r3(x)} ${r3(y)})">${svg}</g>`);
const clipRect = (id, x, y, w, h, r = 0) => `<clipPath id="${id}"><rect x="${r3(x)}" y="${r3(y)}" width="${r3(w)}" height="${r3(h)}" rx="${r3(r)}"/></clipPath>`;

/** the time window [w0, w1] a transition occupies around boundary b */
export function windowOf(tr, b, fps = FPS) {
  const d = tr.dur ?? DEFAULT_DUR[tr.type] ?? 0.2;
  switch (tr.type) {
    case 'whip': case 'glitch': case 'dipBlack': return [b - d / 2, b + d / 2];
    case 'flash': return [b - 2 / fps, b + d];
    case 'zoomThrough': return [b - d, b];
    case 'cardSlam': return [b, b + d];
    default: return [b, b];
  }
}
export const DEFAULT_DUR = { whip: 0.2, flash: 0.22, glitch: 0.1, zoomThrough: 0.45, dipBlack: 0.4, cardSlam: 0.3 };

const DIRS = { left: [-1, 0], right: [1, 0], up: [0, -1], down: [0, 1] };

/** render transition tr at time gt; A, B thunks; info {b, w0, w1, fps, seed, portal} */
export function renderTransition(tr, gt, A, B, info) {
  const fps = info.fps ?? FPS, b = info.b, [w0, w1] = [info.w0, info.w1];
  const q = clamp((gt - w0) / Math.max(1e-6, w1 - w0));
  const fn = TRANSITIONS[tr.type];
  if (!fn) return gt < b ? A() : B();
  return fn({ tr, gt, q, b, w0, w1, fps, A, B, seed: info.seed ?? 1, portal: info.portal });
}

export const TRANSITIONS = {
  cut: ({ gt, b, A, B }) => (gt < b ? A() : B()),

  whip({ tr, q, fps, A, B, w0, w1, seed }) {
    const [dx, dy] = DIRS[tr.dir || 'right'] || DIRS.right;
    const shapeFn = tr.ease === 'front' ? ease.outQuart : ease.inOutCubic;
    const p = shapeFn(q);                             // 0 -> 1 strip travel (one screen)
    const span = dx ? W : H;
    const off = -p * span;                            // content moves opposite to the camera pan
    // only draw the halves that are on screen
    // each shot is clipped to its own frame: sets draw well beyond 0..W, which must not leak into the neighbour
    let strip = `<defs>${clipRect('whipclip', 0, 0, W, H)}</defs>`;
    if (p < 0.999) strip += tx(`<g clip-path="url(#whipclip)">${A()}</g>`, dx * off, dy * off);
    if (p > 0.001) strip += tx(`<g clip-path="url(#whipclip)">${B()}</g>`, dx * (off + span), dy * (off + span));
    // speed in px/frame from the derivative of the easing
    const dq = 1 / (fps * Math.max(1e-6, w1 - w0));
    const v = (shapeFn(clamp(q + dq / 2)) - shapeFn(clamp(q - dq / 2))) * span;
    let out = strip;
    if (tr.blur !== false && v > 4) out = motionBlur(strip, -dx * v, -dy * v, { k: tr.blurK ?? 0.2, max: tr.blurMax ?? 64, id: 'whip' });
    const lineOp = clamp(v / 140) * (tr.lines ?? 0.85);
    if (lineOp > 0.02) {
      const ang = dx ? 0 : 90;
      out += speedLines({ mode: 'dir', angle: ang, count: tr.lineCount ?? 26, color: '#FFFFFF', seed: (seed % 997) + 5, t: q * 0.6, speed: 9000 * -(dx || dy), op: lineOp, width: 9 });
    }
    return out;
  },

  flash({ tr, gt, b, fps, A, B }) {
    const hold = (tr.hold ?? 1) / fps, d = tr.dur ?? DEFAULT_DUR.flash;
    let op;
    if (gt < b) op = ease.inQuad(clamp((gt - (b - 2 / fps)) / (2 / fps)));
    else if (gt < b + hold) op = 1;
    else op = 1 - ease.outCubic(clamp((gt - b - hold) / Math.max(1e-6, d - hold)));
    const base = gt < b ? A() : B();
    return base + solid(tr.color || '#FFFFFF', op * (tr.peak ?? 1));
  },

  glitch({ tr, gt, b, fps, A, B, seed }) {
    const cur = gt < b ? A : B, other = gt < b ? B : A;
    const s0 = cur(), s1 = other();
    const R = (i, j) => rand(seed + 71, Math.floor(gt * fps / 2), i * 13 + j);
    const n = tr.bands ?? 6, amt = tr.amount ?? 120;
    let out = s0, defs = '';
    for (let i = 0; i < n; i++) {
      const y = R(i, 1) * H, h = 12 + R(i, 2) * 120, dx = (R(i, 3) - 0.5) * 2 * amt, id = `gl${i}_${Math.floor(gt * fps)}`;
      defs += clipRect(id, -60, y, W + 120, h);
      const src = R(i, 4) < 0.45 ? s1 : s0;
      const tint = R(i, 5) < 0.5 ? '#FF2BD6' : '#33E8FF', tint2 = tint === '#FF2BD6' ? '#33E8FF' : '#FF2BD6';
      out += `<g clip-path="url(#${id})">${tx(src, dx, 0)}<rect x="-60" y="${r3(y)}" width="${W + 120}" height="${r3(h)}" fill="${tint}" opacity="0.14"/>`
        + `<rect x="-60" y="${r3(y)}" width="${W + 120}" height="${r3(Math.min(4, h / 4))}" fill="${tint}" opacity="0.8"/>`
        + `<rect x="-60" y="${r3(y + h - Math.min(4, h / 4))}" width="${W + 120}" height="${r3(Math.min(4, h / 4))}" fill="${tint2}" opacity="0.8"/></g>`;
      if (R(i, 6) < 0.4) out += `<rect x="-60" y="${r3(y + h * R(i, 7))}" width="${W + 120}" height="${r3(3 + R(i, 8) * 8)}" fill="${tint2}" opacity="0.5"/>`;
    }
    return `<defs>${defs}</defs>` + out;
  },

  zoomThrough({ tr, q, A, B, portal }) {
    const R0 = tr.rect || portal || [W * 0.35, H * 0.3, W * 0.3, H * 0.4, 24];
    const [x0, y0, w0, h0, rr = 24] = R0;
    const e = (tr.ease === 'expo' ? ease.inOutExpo : ease.inOutCubic)(q);
    const S1 = Math.max(W / w0, H / h0);
    const s = Math.exp(Math.log(S1) * e);                      // uniform scale of A, log-interpolated
    const c0 = [x0 + w0 / 2, y0 + h0 / 2], c = [lerp(c0[0], CX, e), lerp(c0[1], CY, e)];
    // A: scaled by s about its portal centre, which travels to the frame centre
    const aM = `translate(${r3(c[0])} ${r3(c[1])}) scale(${r3(s)}) translate(${r3(-c0[0])} ${r3(-c0[1])})`;
    const rw = w0 * s, rh = h0 * s, rx = c[0] - rw / 2, ry = c[1] - rh / 2;
    // B: 'cover' fit into the growing rect
    const bs = Math.max(rw / W, rh / H);
    const bM = `translate(${r3(c[0])} ${r3(c[1])}) scale(${r3(bs)}) translate(${-CX} ${-CY})`;
    const id = 'zt';
    let out = `<g transform="${aM}">${A()}</g>`;
    out += `<defs>${clipRect(id, rx, ry, rw, rh, rr * s * (1 - e))}</defs><g clip-path="url(#${id})"><g transform="${bM}">${B()}</g>`;
    // screen glare fading as we go through the glass
    out += solid('#FFFFFF', (1 - e) * (tr.glare ?? 0.35)) + '</g>';
    return out;
  },

  dipBlack({ tr, q, A, B }) {
    const c = tr.color || '#000000';
    if (q < 0.5) return A() + solid(c, ease.inOutSine(q / 0.5));
    return B() + solid(c, 1 - ease.inOutSine((q - 0.5) / 0.5));
  },

  cardSlam({ tr, gt, q, b, fps, A, B, seed }) {
    const imp = tr.impact ?? 0.4;                  // fraction of d where the card lands
    const d = tr.dur ?? DEFAULT_DUR.cardSlam;
    const u = clamp(q / imp);
    const s = q < imp ? lerp(tr.from ?? 1.35, 1, ease.inQuad(u)) : 1;
    const op = clamp((gt - b) * fps / 2);           // 2-frame fade-in under the slam
    const tImp = b + imp * d;
    const sh = shakeFn(gt, [{ t: tImp, amp: tr.amp ?? 26, decay: 0.07, freq: 30 }], seed + 5);
    let bSvg = B();
    bSvg = `<g transform="translate(${r3(CX + sh.x)} ${r3(CY + sh.y)}) scale(${r3(s)}) translate(${-CX} ${-CY})">${bSvg}</g>`;
    let out = op < 1 ? A() + `<g opacity="${r3(op)}">${bSvg}</g>` : bSvg;
    const hitF = (gt - tImp) * fps;
    if (hitF >= 0 && hitF < (tr.hitFrames ?? 1)) out += solid(tr.hitColor || '#FFFFFF', tr.hit ?? 0.55);
    return out;
  },
};
