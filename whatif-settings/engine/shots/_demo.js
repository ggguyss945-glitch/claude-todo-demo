// _demo.js — engine v3 demo (about 7 s): Sam to camera on the street (idle, blinks, lip-sync to a dummy viseme
// track, slow push, punch-in on "ONE"), a whip pan into the kitchen with the family (blinks, reactions, Dad's
// auto-visemed line), a toast pop-in with a camera bump, a 7-frame snap zoom onto Sam (ghost copies), a card slam
// into a DAY 1 card, and word-timed captions from the timeline. demo_layers is a benchmark shot (p.set, p.only).
// Timeline: scratchpad settings/engine/demo_timeline.json. Render: node tools/render.js <timeline> <out.mp4>
import { street, kitchen } from '../sets.js';
import * as U from '../ui.js';
import { seg, ease, clamp } from '../anim/motion.js';
import { frameOn } from '../anim/camera.js';
import { toonHeadY } from '../cast.js';
import { starburst, sparkles } from '../fx.js';

/** the sets never change inside a shot, so build them once per worker */
const STREET = () => street({});
const KITCHEN = () => kitchen({ tableY: 800 });

export function demo_sam(ctx) {
  const set = ctx.memo('demo/street', STREET);
  const L = ctx.line('D1');
  const tOne = L ? L.at('ONE') : 1.9;
  ctx.cue('whoosh_short', tOne - 0.05);
  const cam = ctx.cam({
    keys: [[0, { x: 40, y: -20, z: 1.0 }], [ctx.dur, { x: 70, y: -36, z: 1.06 }, 'inOutSine']],
    punch: [{ t: tOne - 1 / 60, k: 1.12, at: [1000, 400], settle: 0.3, keep: 0.04 }],
    drift: 8,
  });
  // Sam: three-quarter to camera, nervous until "ONE", then a forced grin and one finger raised
  const sam = ctx.actor('sam', {
    x: 1000, y: 1330, s: 3.4, facing: -14,
    face: [[0, 'nervous'], [0.95, { preset: 'guilty' }], [tOne, { preset: 'excited', mouth: 'grin' }]],
    talk: 'D1',
    pose: [[0, { armL: 10, armR: 12, foreR: 0 }], [tOne - 0.12, { armR: 58, foreR: 96, handR: 'point', lean: -2 }, 'outBack', 0.12]],
    add: [[0, { sweat: 1 }], [tOne, { sweat: 2 }]],
    nervous: [[0, 0.6], [tOne, 0.25]],
    lurch: [[tOne, 1.06]],
  });
  return cam.set(set, { insert: [{ after: 'mid', svg: sam, depth: 1 }], bake: ctx.p.bake ? 'demo/street' : null });
}

const feetY = () => 930;

export function demo_kitchen(ctx) {
  const set = ctx.memo('demo/kitchen', KITCHEN);
  const t = ctx.t, tToast = 0.75;
  const D2 = ctx.line('D2');
  const tChamp = D2 ? D2.at('champ') : 1.9;
  ctx.cue('ui_toast', tToast); ctx.cue('whoosh_whip', -0.1);
  // slow push, then a 7-frame expo snap onto Sam's face 0.4 s before the end (the reaction button)
  const tSnap = ctx.dur - 0.4, samHead = [1660, feetY() + 10 + toonHeadY('sam') * 1.6];
  const F = frameOn(samHead, 2.1, [960, 470]);
  const cam = ctx.cam({
    keys: [[0, { x: -20, y: 10, z: 1.02 }], [tSnap, { x: 6, y: 2, z: 1.06 }], [tSnap + 7 / 60, F, 'outExpo']],
    shake: [{ t: tToast + 4 / 60, amp: 9, decay: 0.07 }],
    punch: [{ t: tChamp - 1 / 60, k: 1.08, at: [1290, 520], settle: 0.25, keep: 0.03 }],
    drift: 10,
  });
  const feet = feetY();
  let people = '';
  people += ctx.actor('mom', { x: 330, y: feet, s: 1.55, facing: 'tq-right', face: [[0, 'neutral'], [tToast + 0.1, 'skeptic']],
    pose: [[0, { armL: 14, armR: 22, foreR: 90 }], [tToast + 0.1, { armR: 30, foreR: 120 }]], look: [[0, [2, 0]], [tToast + 0.1, [4, -2]]] });
  people += ctx.actor('lily', { x: 720, y: feet - 6, s: 1.62, face: [[0, 'happy'], [tToast + 0.05, 'shocked'], [tToast + 0.6, 'starstruck']],
    pose: [[0, { armL: 30, armR: 30 }], [tToast + 0.05, { armL: 120, armR: 120, foreL: 40, foreR: 40 }], [tToast + 0.6, { armL: 150, armR: 150, foreL: 10, foreR: 10 }]],
    y: [[0, feet - 6], [tToast + 0.05, feet - 6], [tToast + 0.2, feet - 46, 'outQuad'], [tToast + 0.36, feet - 6, 'inQuad']],
    squash: [[tToast + 0.36, 0.12]], ground: feet - 6 });
  people += ctx.actor('dad', { x: 1290, y: feet, s: 1.55, facing: 'tq-right', props: { L: null, R: null }, talk: 'D2',
    face: [[0, 'neutral'], [D2 ? D2.start : 1.2, 'happy']],
    pose: [[0, { armL: 10, armR: 12 }], [D2 ? D2.start - 0.1 : 1.1, { armR: 150, foreR: 25, handR: 'open' }]] });
  people += ctx.actor('sam', { x: 1660, y: feet + 10, s: 1.6, facing: 'tq-left', face: [[0, 'sly'], [tToast, 'starstruck'], [tToast + 0.9, 'sly'], [tSnap + 2 / 60, 'guilty']],
    pose: { armL: 24, foreL: 120, armR: 10 }, props: { L: 'phone' }, lookAt: [[0, [1290, 500]], [tToast, [900, 120]], [tToast + 0.9, [1290, 520]]] });
  const cat = ctx.actor('pickles', { x: 985, y: 812, s: 1.05, face: 'deadpan', lookAt: [[0, [1290, 520]], [tToast + 0.2, [900, 120]]] });
  let s = cam.set(set, { insert: [{ after: 'light', svg: people, depth: 1 }, { after: 'near', svg: cat, depth: 1 }], bake: ctx.p.bake ? 'demo/kitchen' : null });
  // screen-locked UI: the toast pops in (8 frames), holds, the life bar drains
  const p = seg(t, tToast, tToast + 8 / 60);
  if (t >= tToast) s += cam.screen(U.toast({ x: 520, y: 34, title: 'Subtitles: Honest', sub: 'Everyone now says what they {mean}', icon: 'check', life: 1 - seg(t, tToast, tToast + 3) }, p), { shake: true });
  return s;
}

/** DAY 1 card over a turning sunburst; enters with the cardSlam transition (timeline tin) */
export function demo_day(ctx) {
  const t = ctx.t;
  ctx.cue('card_slam', 0.12);
  const cam = ctx.cam({ keys: [[0, { z: 1.0 }], [ctx.dur, { z: 1.05 }]], drift: 6 });
  let s = `<rect x="-40" y="-40" width="2000" height="1160" fill="#25AEF2"/>`;
  s += cam.layer(starburst({ cx: 960, cy: 540, r: 1500, points: 16, rot: t * 12, fill: '#3FC0FF', core: 'none', jitter: 0.12 }, 1), 0.4);
  s += cam.layer(U.dayCard({ cx: 960, cy: 540, day: 1, gearRot: t * 40, scale: 1.18 }, 1), 1);
  s += cam.screen(sparkles({ x: 380, y: 120, w: 1160, h: 840, count: 14, seed: 4, t }), {});
  return s;
}

/** benchmark / QA shot: one set (p.set = 'street' | 'kitchen' | ...), optional p.only / p.skip layer lists */
export function demo_layers(ctx) {
  const name = ctx.p.set || 'street';
  const set = ctx.memo('demo/set/' + name, () => (name === 'kitchen' ? KITCHEN() : name === 'street' ? STREET() : null));
  const cam = ctx.cam({ keys: [[0, { z: 1 }], [ctx.dur, { z: 1.05 }]] });
  return cam.set(set, { only: ctx.p.only, skip: ctx.p.skip, bake: ctx.p.bake ? 'demo/' + name : null });
}
