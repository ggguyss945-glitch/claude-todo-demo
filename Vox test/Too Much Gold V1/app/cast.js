// The cast. Every outfit says who the person is at a glance.
import { makeToon } from './chars.js';
import { hash } from './util.js';

const BROWN = ['#7a4e33', '#5e3a26', '#8a5a3c', '#6b4430', '#4e3020'];
const LIGHT = ['#f3e3cf', '#e9cfae', '#f0d6b8', '#e2c29c', '#d8b48c', '#f4ece0'];

export const CAST_DEFS = {
  // Mansa Musa: white robe with gold trim, gold crown, chain and medallion
  musa: { body: 'robe', color: '#f6f2e8', trim: '#d9a521', trimDots: '#b8320f', necklace: true, medallion: true, sash: '#d9a521', girth: 1.12,
    skin: '#7a4e33', beard: 'short', beardColor: '#1a100a', hat: { type: 'crown', cap: '#b01c2c' }, head: 0.28, faceRes: 1024, shoes: '#c9962a' },
  // royal attendants: indigo mudcloth robes, white-and-indigo turbans
  att1: { body: 'robe', color: '#26307a', pattern: 'mudcloth', stripe: '#ece4cf', skin: '#5e3a26', hat: { type: 'turban', color: '#f4f0e6', stripe: '#26307a', bands: 3 } },
  att2: { body: 'robe', color: '#7a3a1e', pattern: 'mudcloth', stripe: '#f0e2c4', skin: '#6b4430', hat: { type: 'turban', color: '#f4f0e6', stripe: '#7a3a1e', bands: 3 }, moustache: 'thin' },
  att3: { body: 'robe', color: '#26307a', pattern: 'mudcloth', stripe: '#ece4cf', skin: '#4e3020', hat: { type: 'kufi', color: '#f4f0e6', stripe: '#c9962a' } },
  att4: { body: 'robe', color: '#2b5e3a', pattern: 'mudcloth', stripe: '#efe6cc', skin: '#8a5a3c', hat: { type: 'turban', color: '#e8c24a', stripe: '#2b5e3a', bands: 3 } },
  // Cairo merchants
  spice: { body: 'robe', color: '#2f7a4a', pattern: 'stripes', stripe: '#e3d29a', girth: 1.32, skin: '#e9cfae', beard: 'full', beardColor: '#20140c',
    hat: { type: 'turban', color: '#f6f1e6', stripe: '#d8cdb4', bands: 5, size: 1.08 }, faceRes: 768 },
  cloth: { body: 'robe', color: '#d0662a', pattern: 'stripes', stripe: '#f2c25a', skin: '#f3e3cf', moustache: 'curl', hairColor: '#20140c',
    hat: { type: 'turban', color: '#b8262e', stripe: '#e8b43a', bands: 4 }, faceRes: 768 },
  jewel: { body: 'robe', color: '#5a2e7a', trim: '#d9a521', skin: '#e2c29c', moustache: 'thin', girth: 1.2,
    hat: { type: 'turban', color: '#2a6a8a', stripe: '#e8d9a0', bands: 5, jewel: '#d4182a' }, faceRes: 768 },
  // the money changer, then twelve years older
  changer: { body: 'robe', color: '#4e2a6e', trim: '#d9a521', skin: '#f0d6b8', beard: 'short', beardColor: '#2a1a10', girth: 1.1,
    hat: { type: 'turban', color: '#d9a521', stripe: '#4e2a6e', bands: 6, size: 1.12, jewel: '#1c9a52' }, faceRes: 768 },
  changerOld: { body: 'robe', color: '#4e2a6e', trim: '#b89a50', skin: '#ecd2b4', girth: 1.0, beard3d: '#f2f0ea', browW: 1.4,
    hat: { type: 'turban', color: '#c9a65a', stripe: '#4e2a6e', bands: 6, size: 1.12, jewel: '#1c9a52' }, faceRes: 768 },
  baker: { body: 'robe', color: '#c99a62', apron: '#fbf8f0', skin: '#f2dcc0', moustache: 'curl', hairColor: '#2a1a10', girth: 1.28,
    hat: { type: 'baker' }, faceRes: 1024 },
  beggar: { body: 'robe', color: '#7a6248', pattern: 'patched', skin: '#d8b48c', beard: 'short', beardColor: '#5a4a3a', girth: 0.92,
    hat: { type: 'wrap', color: '#9a8a6a', stripe: '#6e5e44' } },
  camelguy: { body: 'robe', color: '#4a78b8', pattern: 'stripes', stripe: '#3a64a0', skin: '#e9cfae', hat: { type: 'wrap', color: '#efe2c4', stripe: '#c9b68e' },
    moustache: 'thin', hairColor: '#1a120c', faceRes: 768 },
  kid1: { body: 'tunic', color: '#3a8fd0', skin: '#f0d6b8', scale: 0.6, head: 0.33, hat: { type: 'hair', color: '#1e140c', cut: 0.42, fringe: true } },
  kid2: { body: 'robe', color: '#e0567a', skin: '#e2c29c', scale: 0.58, head: 0.33, hat: { type: 'hijab', color: '#f2c240' } },
  kid3: { body: 'tunic', color: '#e8a020', skin: '#d8b48c', scale: 0.62, head: 0.33, hat: { type: 'kufi', color: '#f6f2e8', stripe: '#3a8fd0' } },
  guard1: { body: 'robe', color: '#a82a2a', sash: '#e0b040', skin: '#e9cfae', moustache: 'curl', hat: { type: 'helmet', wrap: '#f2efe6' } },
  guard2: { body: 'robe', color: '#a82a2a', sash: '#e0b040', skin: '#f0d6b8', beard: 'short', beardColor: '#20140c', hat: { type: 'helmet', wrap: '#f2efe6' } },
};

// townsfolk for the crowds: men in turbans or caps, women in long dresses and hijab
const ROBES = ['#3e6e9e', '#9a3a3a', '#5a8a4a', '#c08a3a', '#6a4a8a', '#2e7a7a', '#b8642e', '#8a7a5a', '#a04a6a'];
const WRAPS = ['#f4efe4', '#e8c24a', '#c84a3a', '#3e6e9e', '#efe2c4', '#8a5a9a'];
export function townDef(i) {
  const r = (k) => hash(i * 7.1, k);
  const woman = i % 3 === 1;
  const d = {
    body: 'robe', color: ROBES[Math.floor(r(1) * ROBES.length)], pattern: r(2) < 0.35 ? 'stripes' : null, stripe: '#f0e6d0',
    skin: (r(3) < 0.3 ? BROWN : LIGHT)[Math.floor(r(4) * 5)], scale: 0.92 + r(5) * 0.12, girth: 0.92 + r(6) * 0.3,
  };
  if (woman) { d.hat = { type: 'hijab', color: WRAPS[Math.floor(r(7) * WRAPS.length)] }; d.blushBase = 0.3; }
  else {
    d.hat = r(8) < 0.6 ? { type: 'turban', color: WRAPS[Math.floor(r(9) * WRAPS.length)], stripe: r(10) < 0.5 ? '#d8cdb4' : null, bands: 4 } : { type: 'kufi', color: '#f4f0e6', stripe: '#8a7a5a' };
    if (r(11) < 0.4) d.beard = 'short'; else if (r(12) < 0.5) d.moustache = 'thin';
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
  const CR = [['#26307a', '#ece4cf'], ['#7a3a1e', '#f0e2c4'], ['#2b5e3a', '#efe6cc'], ['#f2ead8', '#c9962a'], ['#5a2a6a', '#efe0c0']];
  for (let i = 0; i < 12; i++) {
    const [col, st] = CR[i % CR.length];
    const d = { body: 'robe', color: col, pattern: col === '#f2ead8' ? 'stripes' : 'mudcloth', stripe: st, skin: BROWN[i % BROWN.length], scale: 0.94 + hash(i, 2) * 0.1, girth: 0.95 + hash(i, 3) * 0.15,
      hat: hash(i, 4) < 0.7 ? { type: 'turban', color: ['#f4f0e6', '#e8c24a', '#f4f0e6', '#26307a'][i % 4], stripe: col, bands: 3 } : { type: 'kufi', color: '#f4f0e6', stripe: '#c9962a' } };
    if (hash(i, 5) < 0.4) d.moustache = 'thin';
    const c = makeToon({ name: 'car' + i, seed: 500 + i, ...d }); c.root.visible = false; scene.add(c.root); cast.caravan.push(c);
  }
  return cast;
}
