// The cast: one definition per person so every shot uses the identical model.
import { makeCharacter } from './chars.js';
import { rng } from './util.js';

const UNI = { kind: 'uniform', top: '#1d2846', sleeve: '#dcdcd6', pants: '#2b2f3a', shoes: '#16110d', tieColor: '#7a1c24', shirt: '#e6e6e0' };
const UNI_GIRL = { ...UNI, pants: '#1d2846' };

export const CAST_DEFS = {
  you: {
    name: 'you', scale: 0.92, build: 0.93, clothes: UNI, cuffs: true,
    face: { skin: '#c99a74', hair: '#1c120c', hairStyle: 'short', eye: '#3e2614', age: 0.0, young: 1, seed: 101, brow: 1.15, lip: '#a06a5c', widthK: 1.0 },
  },
  teacher: {
    name: 'teacher', scale: 1.0, build: 1.04, glasses: 'rect',
    clothes: { kind: 'suit', top: '#6b4a2e', sleeve: '#6b4a2e', pants: '#383a40', shoes: '#1a120c', shirt: '#dfe8f4', tie: 'plain', tieColor: '#7a1e22', buttons: '#2a1a10' },
    face: { skin: '#d6a585', hair: '#3a2a1e', hairStyle: 'short', beard: 'full', beardColor: '#3a2a1e', eye: '#3a4a3a', age: 0.45, seed: 202, brow: 1.15 },
  },
  principal: {
    name: 'principal', scale: 1.0, build: 1.08,
    clothes: { kind: 'suit', top: '#23262e', sleeve: '#23262e', pants: '#23262e', shoes: '#0c0c0c', shirt: '#f4f4f2', tie: 'plain', tieColor: '#1c2f6e', pocketSquare: true },
    face: { skin: '#d2a07e', hair: '#bdb8b0', hairStyle: 'short', beard: 'full', beardColor: '#cfcac2', eye: '#4a3a2a', age: 0.78, seed: 303, brow: 1.2 },
  },
  teacher2: {
    name: 'teacher2', scale: 0.97, build: 0.95, female: true, hijab: '#6a2e3e', dress: '#2a2c36', skirtLong: true,
    clothes: { kind: 'cardigan', top: '#3c4c5e', sleeve: '#3c4c5e', pants: '#2a2c36', shoes: '#1a1210', shirt: '#efe8e0' },
    face: { skin: '#e0b090', female: true, eye: '#4a3020', age: 0.35, makeup: 0.15, seed: 404, lip: '#b06060' },
  },
  teacher3: {
    name: 'teacher3', scale: 1.02, build: 1.12,
    clothes: { kind: 'tracksuit', top: '#1e4a8c', sleeve: '#1e4a8c', pants: '#1e4a8c', shoes: '#e8e8e8' },
    face: { skin: '#c08a68', hairStyle: 'bald', beard: 'stubble', beardColor: '#2a1a10', eye: '#3a2a1a', age: 0.42, seed: 505 },
  },
  smart: {
    name: 'smart', scale: 0.9, build: 0.88, glasses: 'round', clothes: UNI, cuffs: true,
    face: { skin: '#e9c4a4', hair: '#4a2c18', hairStyle: 'slick', eye: '#3a4a5a', age: 0.0, young: 1, seed: 606, brow: 0.9, lip: '#a87064' },
  },
  dad: {
    name: 'dad', scale: 1.0, build: 1.05,
    clothes: { kind: 'sweater', top: '#4c5a40', sleeve: '#4c5a40', pants: '#3a3a3e', shoes: '#22180f', shirt: '#eeeeea' },
    face: { skin: '#c69872', hair: '#22160e', hairStyle: 'short', beard: 'full', beardColor: '#22160e', eye: '#3a2414', age: 0.45, seed: 707 },
  },
  mom: {
    name: 'mom', scale: 0.96, build: 0.95, female: true, hijab: '#2e3a5c', dress: '#5e4e6e', skirtLong: true,
    clothes: { kind: 'cardigan', top: '#6e5e7e', sleeve: '#6e5e7e', pants: '#5e4e6e', shoes: '#1a1210', shirt: '#ece4dc' },
    face: { skin: '#d8ac8a', female: true, eye: '#3e2818', age: 0.38, makeup: 0.1, seed: 808, lip: '#b06464' },
  },
};

// classmates: boys and girls in the same uniform, most girls in a hijab
const SKINS = ['#e8c4a2', '#c99a74', '#a8764e', '#e0b28c', '#8a5a3a', '#d6a682', '#f0d0b4', '#b98660'];
const HAIRS = ['#1a120c', '#2e1e12', '#4a2e1a', '#120c08', '#6a4428', '#1e1a18'];
const HIJABS = ['#f2f2ee', '#1d2846', '#f2f2ee', '#1d2846', '#e8e2d8'];
export function classmateDef(i) {
  const r = rng(9100 + i * 37);
  const girl = i % 2 === 1;
  const skin = SKINS[Math.floor(r() * SKINS.length)];
  const hair = HAIRS[Math.floor(r() * HAIRS.length)];
  const d = {
    name: 'kid' + i, scale: 0.86 + r() * 0.08, build: 0.86 + r() * 0.1, cuffs: true, faceRes: 448,
    clothes: girl ? UNI_GIRL : UNI,
    face: { skin, hair, hairStyle: girl ? 'bun' : ['short', 'short', 'curly', 'buzz', 'slick'][Math.floor(r() * 5)], eye: ['#3e2614', '#2a1a10', '#4a3a2a', '#3a4a5a'][Math.floor(r() * 4)],
      age: 0, young: 1, seed: 1000 + i * 13, female: girl, brow: 0.8 + r() * 0.4, widthK: 0.95 + r() * 0.08, lip: girl ? '#b46a62' : '#a06a5c' },
  };
  if (girl) {
    d.female = true; d.dress = '#1d2846'; d.skirtLong = true;
    if (i % 6 !== 5) d.hijab = HIJABS[Math.floor(r() * HIJABS.length)];
    d.face.lip = '#b46a62';
  }
  if (r() < 0.15 && !d.hijab) d.glasses = 'rect';
  return d;
}

export function makeCast() {
  const cast = {};
  for (const k in CAST_DEFS) cast[k] = makeCharacter(CAST_DEFS[k]);
  return cast;
}
