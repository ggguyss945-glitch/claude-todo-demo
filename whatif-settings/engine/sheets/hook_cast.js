// hook_cast — QA sheet for the new hook assets: TINY (poses, facings, faces, scales, house-size detail), the Day 7
// factory-reset mannequins (Mom / Dad at mannequin 0 / 0.5 / 1), Dad in pyjamas shielding his eyes in the blown-out sun,
// Sam at 2:13 a.m. (night tint + phone glow, legs: false in bed), Sam's acting extras (star -> scared morph, sweat grow,
// shrug, squint, yawn, ONE finger) and a viseme strip (3 characters x 3 facings).
import { begin, doc, studio, title, caption, bust, cell, labelBar, nameTag, toon, CAST } from './common.js';
import { posePreset, toonHipY } from '../cast.js';
import { rect, path, ramp, ellipse, glowPaint, g, circle, rrect, label } from '../style.js';

const NIGHT = { tint: { color: '#5562A4', k: 0.55 }, light: { color: '#CFE8FF', k: 0.85, from: 'phone' }, props: { R: 'phoneBack' } };
const SUN = { tint: { color: '#FFF3DC', k: 0.16 }, light: { color: '#FFF8E0', k: 0.5, from: 'left' } };
const panelTitle = (x, y, s, sub) => title(x, y, s, { size: 22 }) + (sub ? caption(x, y + 20, sub, { anchor: 'start', size: 14, color: '#7A7698' }) : '');

export default function make() {
  begin();
  let s = studio({ horizon: 1080, glow: false });
  s += title(36, 52, 'HOOK CAST — NEW ASSETS', { size: 34 }) + caption(1884, 50, 'S00 cold open + DAY 1  ·  cast.js / face.js / rig.js / style.js', { anchor: 'end', size: 17, color: '#6B6890' });

  // ---------- A. TINY ----------
  {
    const x = 30, y = 72, w = 1300, h = 392;
    let inner = rect(x, y + h - 120, w, 120, { fill: ramp(['#9FDB86', '#7CC86A']) }) + rect(x, y + h - 122, w, 4, { fill: '#6DB85C', opacity: 0.6 });
    const fl = y + h - 50;
    inner += toon('kevin', { x: x + 90, y: fl, s: 0.62, face: 'smug', facing: 'tq-right', props: { L: 'blower' } });
    const P = [
      [x + 200, { s: 0.5, face: 'happy' }, 's 0.5'],
      [x + 318, { s: 0.74, face: 'neutral' }, 'sit · neutral'],
      [x + 446, { s: 0.74, face: 'happy', pose: { wag: 0.9 } }, 'happy · wag'],
      [x + 576, { s: 0.74, face: 'excited', facing: 'tq-right', pose: { tongue: 1.4 } }, 'excited · tq'],
      [x + 712, { s: 0.74, face: 'confused', facing: 'side-left' }, 'confused · side'],
      [x + 846, { s: 0.74, face: 'shocked' }, 'shocked'],
      [x + 1010, { s: 0.74, posture: 'stand', face: 'happy', facing: 'side-right', pose: { wag: -0.6, legFL: 18, legHR: -14 } }, 'stand · side'],
      [x + 1196, { s: 0.74, posture: 'stand', face: 'excited', facing: 'front' }, 'stand · front'],
    ];
    for (const [px, o] of P) inner += toon('tiny', { x: px, y: fl, ...o });
    let labs = '';
    for (const [px, , lab] of P) labs += caption(px, y + h - 12, lab, { size: 14, color: '#2F5A2A' });
    s += cell(x, y, w, h, inner + labs, { r: 20, fill: '#F4F7FF' }) + panelTitle(x + 18, y + 30, 'TINY  ·  KEVIN’S DOG', "toon('tiny', {posture, facing, face, pose:{wag, ears, tongue, ...}})");
    s += nameTag(x + 90, y + h - 12, 'KEVIN', CAST.kevin.color, { size: 13 });
    // house-size close-up: the collar tag reads TINY from lod 1.8
    const cx = 1342, cw = 548;
    const big = toon('tiny', { x: cx + cw / 2 - 6, y: y + 512, s: 2.05, lod: 3, face: 'excited', pose: { wag: 0.4 } });
    s += cell(cx, y, cw, h, big + labelBar(cx, y + h - 34, cw, 34, 'HOUSE-SIZE DETAIL  ·  LOD 3  ·  TAG READS TINY', { size: 17 }), { r: 20, fill: '#EEF3FF' });
  }

  // ---------- B. FACTORY RESET / PYJAMAS / NIGHT ----------
  {
    const y = 476, h = 312;
    // mannequins
    const x = 30, w = 720;
    let inner = '';
    [0, 0.5, 1].forEach((k, i) => {
      inner += toon('mom', { x: x + 70 + i * 116, y: y + h - 40, s: 0.55, mannequin: k, face: 'scared', facing: 'tq-right' });
      inner += toon('dad', { x: x + 425 + i * 116, y: y + h - 40, s: 0.55, mannequin: k, face: 'scared', facing: 'tq-left', props: { R: null }, pose: { armR: 10, foreR: 10 } });
    });
    let labs = '';
    ['0', '0.5', '1'].forEach((t, i) => { labs += caption(x + 70 + i * 116, y + h - 12, 'mannequin ' + t, { size: 13 }) + caption(x + 425 + i * 116, y + h - 12, 'mannequin ' + t, { size: 13 }); });
    s += cell(x, y, w, h, inner + labs, { r: 20 }) + panelTitle(x + 18, y + 28, 'DAY 7 FACTORY RESET', "mannequin: 0..1  (or variant: 'default')  ·  silhouette never changes");
    // dad pyjamas
    const px = 762, pw = 420;
    const sunBg = rect(px, y, pw, h, { fill: ramp(['#FFFDF6', '#FFF1D2']) }) + ellipse(px - 30, y + 80, 260, 260, { fill: glowPaint('#FFFFFF', 0.9) });
    let pin = sunBg;
    pin += toon('dad', { x: px + 110, y: y + h - 40, s: 0.58, outfit: 'pyjamas', face: 'deadpan' });
    pin += toon('dad', { x: px + 300, y: y + h - 40, s: 0.58, outfit: 'pyjamas', face: 'shout', pose: posePreset('shieldEyes', 'dad'), ...SUN });
    pin += caption(px + 110, y + h - 12, "outfit: 'pyjamas'", { size: 13 }) + caption(px + 300, y + h - 12, 'shieldEyes · sun light', { size: 13 });
    s += cell(px, y, pw, h, pin, { r: 20 }) + panelTitle(px + 18, y + 28, 'WHO TURNED ON THE SUN?!', '');
    // sam night
    const nx = 1194, nw = 696;
    let nin = rect(nx, y, nw, h, { fill: ramp(['#2C2760', '#45397E']) }) + ellipse(nx + nw - 70, y + 70, 120, 120, { fill: glowPaint('#BFD0FF', 0.25) });
    for (const [sx, sy] of [[60, 60], [140, 40], [520, 90], [610, 50], [400, 30]]) nin += circle(nx + sx, y + sy, 2.2, { fill: '#FFFFFF', opacity: 0.6 });
    const bedY = y + h - 64;
    // in bed: hip 20 px under the blanket line -> origin = hipLine - toonHipY * s
    nin += toon('sam', { x: nx + 150, y: bedY + 20 - toonHipY('sam') * 0.74, s: 0.74, legs: false, pose: posePreset('bedSit', 'sam'), face: { preset: 'neutral', look: [0, 3] }, ...NIGHT });
    nin += path(`M${nx + 20} ${bedY + 6}Q${nx + 150} ${bedY - 16} ${nx + 290} ${bedY + 6}L${nx + 300} ${y + h}L${nx + 10} ${y + h}Z`, { fill: ramp(['#5876DE', '#3F57B8']), stroke: '#22306E', strokeWidth: 3 });
    nin += bust('sam', nx + 395, y + 160, 100, { face: 'squint', pose: posePreset('phoneUp', 'sam'), ...NIGHT });
    nin += bust('sam', nx + 580, y + 160, 100, { face: { preset: 'starstruck', to: 'scared', k: 0.8 }, pose: posePreset('phoneLap', 'sam'), ...NIGHT });
    nin += rect(nx, y + h - 32, nw, 32, { fill: '#221E4A', opacity: 0.85 });
    nin += caption(nx + 150, y + h - 12, 'legs:false · bedSit · phone glow', { size: 13, color: '#E4E8FF' }) + caption(nx + 395, y + h - 12, 'squint · phoneUp', { size: 13, color: '#E4E8FF' }) + caption(nx + 580, y + h - 12, 'phoneLap · star→scared', { size: 13, color: '#E4E8FF' });
    s += cell(nx, y, nw, h, nin, { r: 20, line: '#2A2346' }) + title(nx + 18, y + 28, '2:13 A.M.', { size: 22, color: '#FFFFFF' }) + caption(nx + 18, y + 48, "tint:{color,k} + light:{from:'phone'}", { anchor: 'start', size: 14, color: '#C9D0F5' });
  }

  // ---------- C. SAM ACTING + VISEMES ----------
  {
    const y = 814, h = 254, gap = 8;
    const items = [
      ['STAR k0', (cx, cy) => bust('sam', cx, cy, 86, { face: { preset: 'starstruck', to: 'scared', k: 0 } })],
      ['k 0.4', (cx, cy) => bust('sam', cx, cy, 86, { face: { preset: 'starstruck', to: 'scared', k: 0.4 } })],
      ['k 0.6', (cx, cy) => bust('sam', cx, cy, 86, { face: { preset: 'starstruck', to: 'scared', k: 0.6 } })],
      ['SCARED k1', (cx, cy) => bust('sam', cx, cy, 86, { face: { preset: 'starstruck', to: 'scared', k: 1 } })],
      ['SWEAT 0', (cx, cy) => bust('sam', cx, cy, 86, { face: { preset: 'nervous', add: { sweat: 1, sweatK: 0 } } })],
      ['SWEAT .5', (cx, cy) => bust('sam', cx, cy, 86, { face: { preset: 'nervous', add: { sweat: 1, sweatK: 0.5, sweatSize: 1.2 } } })],
      ['SWEAT 1', (cx, cy) => bust('sam', cx, cy, 86, { face: { preset: 'nervous', add: { sweat: 1, sweatK: 1, sweatSize: 1.5 } } })],
      ['SHRUG', (cx, cy) => toon('sam', { x: cx, y: cy + 128, s: 0.5, face: 'ish', pose: posePreset('shrug', 'sam') })],
      ['ONE!', (cx, cy) => toon('sam', { x: cx, y: cy + 128, s: 0.5, face: 'forcedGrin', pose: posePreset('pointUp', 'sam') })],
      ['YAWN', (cx, cy) => bust('sam', cx, cy, 86, { face: 'yawn', pose: posePreset('yawnCover', 'sam') })],
      ['SQUINT', (cx, cy) => bust('sam', cx, cy, 86, { face: 'squint' })],
    ];
    const vis = [['sam', 'front', 'v_A'], ['sam', 'tq-right', 'v_E'], ['sam', 'side-right', 'v_O'], ['mom', 'front', 'v_E'], ['mom', 'tq-left', 'v_O'], ['mom', 'side-left', 'v_A'],
      ['dad', 'front', 'v_O'], ['dad', 'tq-right', 'v_A'], ['dad', 'side-right', 'v_E']];
    const n = items.length + vis.length, cw = (1860 - gap * (n - 1) - 16) / n;
    items.forEach(([lab, fn], i) => {
      const x = 30 + i * (cw + gap);
      s += cell(x, y, cw, h, fn(x + cw / 2, y + 96) + labelBar(x, y + h - 30, cw, 30, lab.toUpperCase(), { size: 13 }), { r: 14 });
    });
    vis.forEach(([id, f, v], j) => {
      const x = 30 + (items.length + j) * (cw + gap) + 16;
      const off = f.startsWith('side') ? (f.endsWith('right') ? -34 : 34) : f.startsWith('tq') ? (f.endsWith('right') ? -6 : 6) : 0;
      s += cell(x, y, cw, h, bust(id, x + cw / 2 + off, y + 96, 86, { facing: f, face: { preset: id === 'dad' ? 'panic' : id === 'mom' ? 'angry' : 'neutral', mouth: v } }) + labelBar(x, y + h - 30, cw, 30, v.replace('v_', '') + ' · ' + f.replace('-right', '').replace('-left', '').toUpperCase(), { size: 13 }), { r: 14, fill: '#F3F5FF' });
    });
    s += caption(30 + items.length * (cw + gap) + 16, y - 6, "VISEMES ON EXPRESSIONS  ·  face: {preset, mouth: 'v_A'}", { anchor: 'start', size: 13, color: '#6B6890' });
    s += caption(30, y - 6, "SAM ACTING EXTRAS  ·  face: {preset: 'starstruck', to: 'scared', k}  ·  add: {sweatK, sweatSize}  ·  posePreset()", { anchor: 'start', size: 13, color: '#6B6890' });
  }
  void g; void rrect; void label;
  return doc(s);
}
