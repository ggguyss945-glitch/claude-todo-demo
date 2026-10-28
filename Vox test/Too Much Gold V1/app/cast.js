// The cast. Every outfit says who the person is at a glance.
import { makeToon } from './chars.js';
import { hash } from './util.js';

// Heads follow the cartoon convention: plain white ball heads for most people, flat warm tints
// for some (the king and his people from Mali are brown).
const BROWN = ['#a2704a', '#8f5f3d', '#b07a52', '#7c5034', '#966442'];
const LIGHT = ['#f7f3ec', '#f7f3ec', '#f4ede2', '#ecd6b6', '#f7f3ec', '#efe2cc'];

export const CAST_DEFS = {
  // Mansa Musa: cream robe with a gold front band, gold collar and belt, crown, chain and medallion
  musa: { body: 'robe', color: '#f4ecda', trim: '#e2aa2a', trimDots: '#c0392b', collar: '#e8b530', belt: '#e2aa2a', hem: '#e2aa2a', necklace: true, medallion: true,
    girth: 1.08, skin: '#a2704a', beard: 'short', beardColor: '#1e140e', moustache: 'thin', hairColor: '#1e140e', hat: { type: 'crown', cap: '#b01c2c' }, head: 0.3, faceRes: 1024, shoes: '#d9a521' },
  // royal attendants: indigo / rust / green robes, white collars, gold belts
  att1: { body: 'robe', color: '#2c3a8c', collar: '#f2ead8', belt: '#e2aa2a', skin: '#8f5f3d', hat: { type: 'turban', color: '#f4f0e6', stripe: '#2c3a8c', bands: 2 } },
  att2: { body: 'robe', color: '#8a3a1e', collar: '#f2ead8', belt: '#e2aa2a', skin: '#b07a52', hat: { type: 'turban', color: '#f4f0e6', stripe: '#8a3a1e', bands: 2 }, moustache: 'thin' },
  att3: { body: 'robe', color: '#2c3a8c', collar: '#f2ead8', belt: '#e2aa2a', skin: '#7c5034', hat: { type: 'kufi', color: '#f4f0e6', stripe: '#e2aa2a' } },
  att4: { body: 'robe', color: '#2b6e44', collar: '#f2ead8', belt: '#e2aa2a', skin: '#966442', hat: { type: 'turban', color: '#e8c24a', stripe: '#2b6e44', bands: 2 } },
  // Cairo merchants
  spice: { body: 'robe', color: '#2f8a52', collar: '#f4e7c4', belt: '#c9962a', girth: 1.22, skin: '#f7f3ec', beard: 'full', beardColor: '#3a2618',
    hat: { type: 'turban', color: '#f6f1e6', stripe: '#d8cdb4', bands: 3, size: 1.1 }, faceRes: 1024 },
  cloth: { body: 'robe', color: '#e0702c', pattern: 'pinstripe', stripe: '#f2b84a', collar: '#f6e2b0', belt: '#7a2a1a', skin: '#f7f3ec', moustache: 'curl', hairColor: '#20140c',
    hat: { type: 'turban', color: '#c0282e', stripe: '#e8b43a', bands: 2 }, faceRes: 1024 },
  jewel: { body: 'robe', color: '#6a2e8a', trim: '#e2aa2a', collar: '#e2aa2a', belt: '#e2aa2a', skin: '#ecd6b6', moustache: 'thin', girth: 1.12,
    hat: { type: 'turban', color: '#2a7a9a', stripe: '#e8d9a0', bands: 3, jewel: '#d4182a' }, faceRes: 1024 },
  // the money changer (glasses, short beard), then twelve years older with a long white beard
  changer: { body: 'robe', color: '#4e2a6e', collar: '#e8c66a', belt: '#e2aa2a', skin: '#f7f3ec', beard: 'short', beardColor: '#2a1a10', glasses: true, girth: 1.05,
    hat: { type: 'turban', color: '#e2aa2a', stripe: '#4e2a6e', bands: 3, size: 1.08, jewel: '#1c9a52' }, faceRes: 1024 },
  changerOld: { body: 'robe', color: '#4e2a6e', collar: '#c8b07a', belt: '#b89a50', skin: '#f2ece2', girth: 1.0, beard3d: '#f6f4ee', glasses: true,
    hat: { type: 'turban', color: '#c9a65a', stripe: '#4e2a6e', bands: 3, size: 1.08, jewel: '#1c9a52' }, faceRes: 1024 },
  baker: { body: 'bean', color: '#c98e52', apron: '#fbf8f0', skin: '#f7f3ec', moustache: 'curl', hairColor: '#2a1a10', girth: 1.18, hat: { type: 'baker' }, faceRes: 1024 },
  beggar: { body: 'bean', color: '#8a7458', pattern: 'patched', skin: '#f2ece2', beard: 'short', beardColor: '#6a5a48', girth: 0.95,
    hat: { type: 'wrap', color: '#a8987a', stripe: '#7a6a50' } },
  camelguy: { body: 'bean', color: '#3f7cc4', belt: '#7a3a1e', skin: '#f7f3ec', hat: { type: 'wrap', color: '#efe2c4', stripe: '#c9b68e' }, moustache: 'thin', hairColor: '#1a120c', faceRes: 1024 },
  kid1: { body: 'bean', color: '#3a8fd0', belt: '#f2c240', skin: '#f7f3ec', scale: 0.62, head: 0.34, hat: { type: 'hair', color: '#1e140c', cut: 0.42, fringe: true } },
  kid2: { body: 'robe', color: '#e0567a', collar: '#ffe0ea', skin: '#ecd6b6', scale: 0.6, head: 0.34, hat: { type: 'hijab', color: '#f2c240' } },
  kid3: { body: 'bean', color: '#e8a020', buttons: '#fbf8f0', skin: '#f7f3ec', scale: 0.64, head: 0.34, hat: { type: 'kufi', color: '#f6f2e8', stripe: '#3a8fd0' } },
  guard1: { body: 'robe', color: '#a82a2a', belt: '#e0b040', collar: '#f2efe6', skin: '#f7f3ec', moustache: 'curl', hat: { type: 'helmet', wrap: '#f2efe6' } },
  guard2: { body: 'robe', color: '#a82a2a', belt: '#e0b040', collar: '#f2efe6', skin: '#ecd6b6', beard: 'short', beardColor: '#20140c', hat: { type: 'helmet', wrap: '#f2efe6' } },
};

// townsfolk for the crowds: men in robes or short tunics on stick legs, women in long dresses and hijab
const ROBES = ['#3e6e9e', '#b03a3a', '#4f8a42', '#d08a2a', '#6a4a9a', '#2e8a8a', '#c8642e', '#8a6a4a', '#b04a7a'];
const COLLARS = ['#f4ead2', '#f2c24a', '#ffffff', '#e8d0a0'];
const WRAPS = ['#f4efe4', '#e8c24a', '#c84a3a', '#3e6e9e', '#efe2c4', '#8a5a9a'];
export function townDef(i) {
  const r = (k) => hash(i * 7.1, k);
  const woman = i % 3 === 1;
  const d = {
    body: !woman && r(13) < 0.4 ? 'bean' : 'robe', color: ROBES[Math.floor(r(1) * ROBES.length)], stripe: '#f0e6d0',
    collar: COLLARS[Math.floor(r(14) * COLLARS.length)], belt: r(15) < 0.6 ? ['#e2aa2a', '#5a2a1a', '#f4ead2'][Math.floor(r(16) * 3)] : null,
    skin: LIGHT[Math.floor(r(4) * LIGHT.length)], scale: 0.94 + r(5) * 0.1, girth: 0.95 + r(6) * 0.2,
  };
  if (woman) { d.hat = { type: 'hijab', color: WRAPS[Math.floor(r(7) * WRAPS.length)] }; d.blushBase = 0.35; d.belt = null; }
  else {
    d.hat = r(8) < 0.6 ? { type: 'turban', color: WRAPS[Math.floor(r(9) * WRAPS.length)], stripe: r(10) < 0.5 ? '#d8cdb4' : null, bands: 2 } : { type: 'kufi', color: '#f4f0e6', stripe: '#8a7a5a' };
    if (r(11) < 0.35) d.beard = 'short'; else if (r(12) < 0.5) d.moustache = 'thin';
    d.beardColor = '#20140c';
  }
  return d;
}

export function makeCast(scene) {
  const cast = {};
  for (const k in CAST_DEFS) { cast[k] = makeToon({ name: k, seed: k.length * 13, ...CAST_DEFS[k] }); cast[k].root.visible = false; scene.add(cast[k].root); }
  cast.town = [];
  for (let i = 0; i < 12; i++) { const c = makeToon({ name: 'town' + i, seed: i * 31, ...townDef(i) }); c.root.visible = false; scene.add(c.root); cast.town.push(c); }
  // the king's people for the caravan
  cast.caravan = [];
  const CR = [['#2c3a8c', '#f2ead8'], ['#8a3a1e', '#f0e2c4'], ['#2b6e44', '#efe6cc'], ['#f2ead8', '#e2aa2a'], ['#5a2a6a', '#efe0c0']];
  for (let i = 0; i < 12; i++) {
    const [col, st] = CR[i % CR.length];
    const d = { body: 'robe', color: col, collar: st, belt: i % 2 ? '#e2aa2a' : null, skin: BROWN[i % BROWN.length], scale: 0.94 + hash(i, 2) * 0.1, girth: 0.95 + hash(i, 3) * 0.15,
      hat: hash(i, 4) < 0.7 ? { type: 'turban', color: ['#f4f0e6', '#e8c24a', '#f4f0e6', '#26307a'][i % 4], stripe: col, bands: 3 } : { type: 'kufi', color: '#f4f0e6', stripe: '#c9962a' } };
    if (hash(i, 5) < 0.4) d.moustache = 'thin';
    const c = makeToon({ name: 'car' + i, seed: 500 + i, ...d }); c.root.visible = false; scene.add(c.root); cast.caravan.push(c);
  }
  return cast;
}
