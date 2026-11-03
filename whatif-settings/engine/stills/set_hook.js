// QA stills for the hook's new sets and set variants (S00 + S01-L001). arg:
//   tiny        street({split, liveTree: 'kevin'}): house-size Tiny between the houses and the yard props, the tree flipped
//   tiny_small  the same at dog size with the tree mid-flip
//   tree        flipTree() at 0 / 45 / 90 / 135 / 180 deg (+ soil) on the lawn
//   night       street({night: 1}) wide: 2:13 a.m., Sam's window lit
//   night_house the same framed on the family house (z 1.8)
//   bedroom_sit bedroom({blanket: 'sit'}) with Sam sitting up at the BEDROOM.sam anchor, birds asleep
//   bedroom_sun 3-up sheet: sun 0 / 0.5 / 1 (Sam in bed, birds waking)
//   bedroom_wide the wide framing (z 0.7) showing the ceiling line
//   hallway     hallway() night + sun 0.55 with Dad   |  hallway_night / hallway_sun (single frames)
//   space       space({glow: 1})  |  space_0 (glow 0)  |  space_zoom (strip: zoom 1 / 3 / 9 on the house)
//   reset       streetReset() with the mannequin / pill anchors marked
import { street, flipTree, STREET, bedroom, BEDROOM, streetReset, RESET, compose, wrap } from '../sets.js';
import { hallway, HALL, space, SPACE } from '../sets2.js';
import { g, rect, text, FONT, contact, circle, path } from '../ui_style.js';
import { toon, posePreset, toonHipY } from '../cast.js';
import { resetDefs, defsSvg } from '../style.js';

const W = 1920, H = 1080;
const byName = (set) => Object.fromEntries(set.layers.map((l) => [l.name, l]));
/** compose a set with inserts [{after, svg, depth}] (the same rule as cam.set) for a camera {x, y, z} about the centre */
function shot(set, inserts = [], cam = {}, late = false) {
  const out = [];
  // late: an insert after 'X' goes after the set's own layers that follow X with names ending in 'Back' (sunBack)
  const L = set.layers;
  for (let n = 0; n < L.length; n++) {
    const l = L[n];
    out.push(l);
    if (late && L[n + 1] && /Back$/.test(L[n + 1].name)) continue;
    const key = late && /Back$/.test(l.name) ? L[n - 1].name : l.name;
    for (const i of inserts) if (i.after === key) out.push({ name: 'ins', depth: i.depth ?? 1, svg: i.svg });
  }
  for (const i of inserts) if (!i.after || i.after === 'top') out.push({ name: 'ins', depth: i.depth ?? 1, svg: i.svg });
  const z = cam.z ?? 1, cx = cam.x || 0, cy = cam.y || 0;
  return out.map((l) => {
    if (l.depth === 0) return l.svg;
    return `<g transform="translate(960 540) scale(${z}) translate(${-960 - cx * l.depth} ${-540 - cy * l.depth})">${l.svg}</g>`;
  }).join('');
}
const label = (x, y, s, o = {}) => text(x, y, s, { fontFamily: FONT.title, fontSize: o.size || 40, fill: '#FFFFFF', stroke: '#1E1A40', strokeWidth: 8, paintOrder: 'stroke', textAnchor: o.anchor || 'start', letterSpacing: 1 });
const cell = (svg, x, y, w, h, sc) => `<g transform="translate(${x} ${y}) scale(${sc})"><svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" overflow="hidden">${svg}</svg></g>`;

const NIGHT = { tint: { color: '#5562A4', k: 0.55 }, light: { color: '#CFE8FF', k: 0.85, from: 'phone' }, props: { R: 'phoneBack' } };

function bedroomFrame(sun, o = {}) {
  resetDefs();
  const set = bedroom({ blanket: 'sit', sun, birds: o.birds ?? true });
  const B = BEDROOM.sam;
  const tint = sun > 0 ? { tint: { color: sun > 0.5 ? '#FFF3DC' : '#C9B8E8', k: 0.2 + 0.1 * (1 - sun) }, light: { color: '#FFF2D0', k: 0.4 + 0.4 * sun, from: 'right' }, props: { R: 'phoneBack' } } : NIGHT;
  const sam = toon('sam', { x: B.x, y: B.y, s: B.s, legs: false, pose: posePreset('bedSit', 'sam'), face: sun >= 0.5 ? { preset: 'shocked' } : { preset: 'neutral', look: [0, 3] }, ...tint });
  return shot(set, [{ after: 'mid', depth: 0.75, svg: defsSvg() + sam }], o.cam);
}

export default async (arg = 'tiny') => {
  let svg = '';
  if (arg === 'tiny' || arg === 'tiny_small') {
    resetDefs();
    const big = arg === 'tiny';
    const set = street({ split: true, liveTree: 'kevin' });
    const T = STREET.tiny, s = big ? T.s1 : T.s0;
    const dog = contact(T.x, T.y + 4, 120 * s, 14 * s, 0.25) + toon('tiny', { x: T.x, y: T.y, s, lod: s, face: big ? 'excited' : 'happy', pose: { wag: 0.5 } });
    const tr = flipTree({ ...STREET.trees.kevin, angle: big ? 180 : 70, hop: big ? 0 : 60, soil: big ? 0.9 : 0 });
    svg = shot(set, [{ after: 'mid', depth: 0.75, svg: defsSvg() + dog }, { after: 'mid', depth: 0.75, svg: tr }], { x: big ? 160 : 160, y: big ? -60 : 0 });
  } else if (arg === 'tree') {
    const set = street({ split: true, liveTree: 'kevin' });
    const cells = [0, 45, 90, 135, 180].map((a, i) => {
      const T = STREET.trees.kevin;
      const tr = flipTree({ ...T, angle: a, hop: a > 0 && a < 180 ? 90 * Math.sin((a / 180) * Math.PI) : 0, soil: a === 180 ? 0.35 : 0 });
      return cell(shot(set, [{ after: 'mid', depth: 0.75, svg: tr }], { x: 770, y: -40, z: 1.6 }) + label(40, 80, `angle ${a}`), (i % 3) * 640, Math.floor(i / 3) * 360, 640, 360, 1 / 3);
    });
    svg = rect(0, 0, W, H, { fill: '#1E1A40' }) + cells.join('');
    return { w: W, h: 720, svg: wrap(svg, W, 720) };
  } else if (arg === 'night' || arg === 'night_house') {
    const set = street({ night: 1, split: true });
    svg = shot(set, [], arg === 'night' ? { x: -120, y: -40 } : { x: -660, y: -30, z: 1.75 });
  } else if (arg === 'bedroom_sit') {
    svg = bedroomFrame(0);
  } else if (arg === 'bedroom_wide') {
    svg = bedroomFrame(0, { cam: { z: 0.7, x: 0, y: -40 } });
    svg += path(`M0 ${540 + (BEDROOM.ceilY - 540 + 40 * 0.75) * 0.7}H1920`, { stroke: '#FF2BD6', strokeWidth: 3, strokeDasharray: '16 10' }) + label(20, 540 + (BEDROOM.ceilY - 540 + 30) * 0.7 - 14, `ceilY ${BEDROOM.ceilY}`, { size: 30 });
  } else if (arg === 'bedroom_sun' || arg === 'bedroom_sun1' || arg === 'bedroom_sun5') {
    if (arg !== 'bedroom_sun') return { w: W, h: H, svg: wrap(bedroomFrame(arg === 'bedroom_sun1' ? 1 : 0.5)) };
    // 3-up sheet: sun 0 / 0.5 / 1
    const cw = 1280, chh = 720;
    let s = rect(0, 0, 3 * cw + 80, chh + 130, { fill: '#1E1A40' });
    [0, 0.5, 1].forEach((k, i) => {
      s += cell(bedroomFrame(k), 20 + i * (cw + 20), 100, cw, chh, cw / W);
      s += label(40 + i * (cw + 20), 72, `sun ${k}`, { size: 48 });
    });
    s += label(3 * cw + 60, 72, "bedroom({blanket:'sit', sun})", { size: 34, anchor: 'end' });
    return { w: 3 * cw + 80, h: chh + 130, svg: wrap(s, 3 * cw + 80, chh + 130) };
  } else if (arg === 'hallway' || arg === 'hallway_night' || arg === 'hallway_sun' || arg === 'hallway_sun1') {
    const frame = (sun) => {
      resetDefs();
      const set = hallway({ sun });
      const D = HALL.dad;
      const dad = toon('dad', { x: D.x, y: D.y, s: D.s, outfit: 'pyjamas', facing: 'tq-right', face: sun > 0.2 ? 'shout' : 'sleepy',
        pose: sun > 0.2 ? posePreset('shieldEyes', 'dad', { facing: 'tq-right' }) : { armL: 8, armR: 8 },
        ...(sun > 0.2 ? { tint: { color: '#FFF3DC', k: 0.16 }, light: { color: '#FFF8E0', k: 0.55, from: 'right' } } : { tint: { color: '#5562A4', k: 0.5 } }) });
      return shot(set, [{ after: 'mid', depth: 1, svg: defsSvg() + contact(D.x, D.y + 4, 110 * D.s, 14 * D.s, 0.25) + dad }], {}, true);
    };
    if (arg !== 'hallway') return { w: W, h: H, svg: wrap(frame(arg === 'hallway_sun' ? 0.6 : arg === 'hallway_sun1' ? 1 : 0)) };
    const cw = 1280, chh = 720;
    let s = rect(0, 0, 3 * cw + 80, chh + 130, { fill: '#1E1A40' });
    [0, 0.55, 1].forEach((k, i) => {
      s += cell(frame(k), 20 + i * (cw + 20), 100, cw, chh, cw / W);
      s += label(40 + i * (cw + 20), 72, `sun ${k}`, { size: 48 });
    });
    s += label(3 * cw + 60, 72, 'hallway({sun}) + Dad in pyjamas', { size: 34, anchor: 'end' });
    return { w: 3 * cw + 80, h: chh + 130, svg: wrap(s, 3 * cw + 80, chh + 130) };
  } else if (arg === 'space' || arg === 'space_0') {
    const set = space({ glow: arg === 'space' ? 1 : 0 });
    svg = shot(set, []);
  } else if (arg === 'space_zoom') {
    const set = space({ glow: 1 });
    const P = SPACE.house;
    let s = rect(0, 0, W, 400, { fill: '#1E1A40' });
    [1, 3, 9].forEach((z, i) => {
      s += cell(shot(set, [], { z, x: (P.x - 960) * (1 - 1 / z) * 1, y: (P.y - 540) * (1 - 1 / z) }), 20 + i * 630, 40, 620, 349, 620 / W) + label(40 + i * 630, 80, `zoom ${z}`, { size: 30 });
    });
    return { w: W, h: 400, svg: wrap(s, W, 400) };
  } else if (arg === 'reset') {
    resetDefs();
    const set = streetReset({ t: 0.2, glitch: false });
    let ppl = '';
    for (const k of ['mom', 'dad']) ppl += contact(RESET[k].x, RESET[k].y + 4, 100 * RESET[k].s, 12 * RESET[k].s, 0.25) + toon(k, { x: RESET[k].x, y: RESET[k].y, s: RESET[k].s, mannequin: 1, face: 'neutral', facing: k === 'mom' ? 'tq-right' : 'tq-left', props: { R: null } });
    svg = shot(set, [{ after: 'near', depth: 1, svg: defsSvg() + ppl }]);
    const P = RESET.pill;
    svg += path(`M${P.x - P.w / 2} ${P.y - P.h / 2}h${P.w}v${P.h}h${-P.w}Z`, { fill: 'none', stroke: '#00E5FF', strokeWidth: 4, strokeDasharray: '14 8' }) + label(P.x, P.y + 14, 'RESET.pill', { size: 36, anchor: 'middle' });
  }
  return { w: W, h: H, svg: wrap(svg) };
};
