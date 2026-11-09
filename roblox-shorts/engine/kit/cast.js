// EP01 cast presets (R6 humans). The 5-second test uses GRANDPA, GRANDMA and the Grandpa gnome (gnome.js).
//   makeCharacter('grandpa', { face: 'content' })  -> avatar root (metres unless units: 'stud')
import { makeAvatar, SKIN, rig, setFace, setPose, POSES } from './avatar.js';
import { OUTFITS, HAIR, PARTS, faceRects } from './clothing.js';
import { hairMat, hairCapGeo, hatGroup } from './accessories.js';
import { drawFace, FACE_RES } from './faces.js';
import { THREE, cached, keyOf, mesh, group, canvas, canvasTex, makeRng, hash32, rgba, shade, clumpGeo, claimMat } from './util.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

export const CAST = {
  // Older styling: white hair (bald crown + puffy side tufts), 3D walrus moustache, soft grey brows, round gold glasses,
  // navy cardigan over a blue check shirt, grey trousers, tartan slippers. The gnome wears the same blue for its coat.
  grandpa: { skin: SKIN.elder, outfit: OUTFITS.grandpaCardigan, face: 'neutral', faceOverlays: { wrinkles: true, brows: '#e4e0e8' },
    accessories: [{ type: 'hair', style: 'grandpa', color: HAIR.white }, { type: 'moustache', color: HAIR.white }, { type: 'glasses', style: 'round', color: '#c9a24e' }] },
  // Grey bun, round rose-gold glasses, rose cardigan over a floral blouse with pearls, plum skirt, slippers.
  grandma: { skin: SKIN.peach, outfit: OUTFITS.grandmaCardigan, face: 'neutral', faceOverlays: { wrinkles: true, blush: '#ff7f8f' },
    accessories: [{ type: 'hair', style: 'bun', color: HAIR.silver }, { type: 'glasses', style: 'round', color: '#d98aa8' }] },
  // Script variants (flashback Grandpa, the narrator at 71)
  grandpaFlashback: { skin: SKIN.elder, outfit: OUTFITS.grandpaFlashback, faceOverlays: { wrinkles: true, brows: '#e4e0e8' },
    accessories: [{ type: 'hair', style: 'grandpa', color: HAIR.white }, { type: 'moustache', color: HAIR.white }, { type: 'hat', style: 'fishing', color: '#6f7342' }] },
  heroOld: { skin: SKIN.salmon, outfit: { shirt: { style: 'cardigan', color: '#d9a52c', trim: '#b98a1e', buttons: '#6b4a2a', inner: { color: '#efe6d2' } }, pants: OUTFITS.grandpaFlashback.pants },
    faceOverlays: { wrinkles: true, freckles: true, brows: '#cfcbd2' }, accessories: [{ type: 'hair', style: 'grandpa', color: HAIR.grey }, { type: 'moustache', color: HAIR.grey }, { type: 'hat', style: 'fishing', color: '#6f7342' }] },
  // EP01 hero (11): mustard hoodie, messy brown hair, freckles.
  hero: { skin: SKIN.salmon, outfit: OUTFITS.heroHoodie, faceOverlays: { freckles: true }, accessories: [{ type: 'hair', style: 'messy', color: HAIR.brown }, { type: 'hood', color: '#d9a52c' }] },
  heroBarefoot: { skin: SKIN.salmon, outfit: { shirt: OUTFITS.heroHoodie.shirt, pants: { ...OUTFITS.heroHoodie.pants, shoes: { style: 'barefoot' } } }, faceOverlays: { freckles: true }, accessories: [{ type: 'hair', style: 'messy', color: HAIR.brown }, { type: 'hood', color: '#d9a52c' }] },
  // Theo (6): oversized blue pyjamas, x0.85.
  theo: { skin: SKIN.light, scale: 0.85, outfit: OUTFITS.theoPyjamas, accessories: [{ type: 'hair', style: 'short', color: HAIR.blond }] },
  mom: { skin: SKIN.peach, outfit: OUTFITS.momSweater, accessories: [{ type: 'hair', style: 'bob', color: HAIR.ginger }] },
  dad: { skin: SKIN.light, outfit: OUTFITS.dadPlaid, faceOverlays: { stubble: true }, accessories: [{ type: 'hair', style: 'short', color: HAIR.darkBrown }] },
};
export function makeCharacter(name, extra = {}) {
  const c = CAST[name]; if (!c) throw new Error('unknown cast member ' + name);
  return castAvatar({ name, ...c, ...extra, faceOverlays: { ...(c.faceOverlays || {}), ...(extra.faceOverlays || {}) } });
}
