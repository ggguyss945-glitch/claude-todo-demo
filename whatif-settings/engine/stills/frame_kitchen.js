// Combined style frame (cast + set + UI + caption in one shot): Day 1 breakfast, S01-L017.
// Subtitles are on HONEST: Dad says "Morning, champ!", his in-world subtitle tells the truth. Lily is still muted from
// the Volume gag, Mom has heard it before, Pickles sits on the table like he owns it, Sam holds the phone with the app.
import * as U from '../ui.js';
import { kitchen, compose, wrap } from '../sets.js';
import { caption } from '../caption.js';
import { g, contact } from '../ui_style.js';
import { toon } from '../cast.js';
import { resetDefs, defsSvg } from '../style.js';

export default async () => {
  const ty = 800;
  const set = kitchen({ tableY: ty });
  const L = Object.fromEntries(set.layers.map((l) => [l.name, l]));
  resetDefs();
  const feet = 930;
  let people = '';
  people += contact(330, feet, 150, 14, 0.18) + contact(1300, feet, 150, 14, 0.18);
  people += toon('mom', { x: 330, y: feet, s: 1.55, face: 'skeptic', facing: 'three-quarter-right', pose: { armL: 14, armR: 30, foreR: 120, pony: -10 } });
  people += toon('lily', { x: 720, y: feet - 6, s: 1.62, face: 'scream', facing: 'front', pose: { armL: 120, armR: 40, foreL: 40, foreR: 90, pigL: -16, pigR: 18, head: -4 } });
  people += toon('dad', { x: 1290, y: feet, s: 1.55, face: 'happy', facing: 'three-quarter-right', pose: { armL: 10, armR: 150, foreR: 25, handR: 'open' }, props: { L: null, R: null } });
  people += toon('sam', { x: 1660, y: feet + 10, s: 1.6, face: 'sly', facing: 'three-quarter-left', pose: { armL: 24, foreL: 120, armR: 10 }, props: { L: 'phone' } });
  // Pickles on the tablecloth, between the juice and the bowl
  let table = contact(985, ty + 14, 80, 10, 0.25);
  table += toon('pickles', { x: 985, y: ty + 12, s: 1.05, face: 'deadpan', pose: { tail: 18 } });
  let s = compose([L.defs, L.far, L.mid, L.light]) + defsSvg() + people + compose([L.near]) + table;
  // in-world UI: Lily's mute badge, Dad's honest subtitle (Mom's is a short one so the system reads at a glance)
  s += U.muteBadge({ cx: 720, cy: 432, r: 50 }, 1);
  s += U.subtitle({ cx: 1210, y: 216, speaker: 'DAD', text: '[I forgot his {name} for a second]', size: 36, tailX: 1280 }, 1);
  s += U.subtitle({ cx: 360, y: 300, speaker: 'MOM', text: '[he forgot it {yesterday} too]', size: 30, tailX: 352 }, 1);
  // screen-locked layer: the change toast and the narrator caption
  s += U.toast({ x: 520, y: 34, title: 'Subtitles: Honest', sub: 'Everyone now says what they {mean}', icon: 'check', life: 0.7 }, 1);
  s += caption('Honest mode: {ON.|green}', {}, 1);
  return { w: 1920, h: 1080, svg: wrap(s) };
};
