// Shot list, timed to the narration's word timings.
import * as THREE from 'three';
import { defaultPose, CH2D } from './chars2d.js';

export const SHOTS = [];
export function findShot(t) {
  for (const s of SHOTS) if (t >= s.t0 && t < s.t1) return s;
  return t < SHOTS[0].t0 ? SHOTS[0] : SHOTS[SHOTS.length - 1];
}
let W = null;
const allChars = () => [...Object.values(W.cast).filter((c) => c.root), ...W.cast.town, ...W.cast.caravan];

export async function initShots(world) {
  W = world;
  if (new URLSearchParams(location.search).get('look') === '1') {
    (await import('./test_shots.js')).add(SHOTS, world);
    return;
  }
  (await import('./film.js')).addFilm(SHOTS, world);
}

export function resetFrame(world, t, shot) {
  for (const c of allChars()) { c.root.visible = false; c.pose = defaultPose(); c.state = { expr: 'neutral', look: [0, 0], talk: 0, blink: false }; }
  for (const o of world.actors) o.visible = false;
  world.reset?.(t);
}

// the drawings pick up a little of each scene's light colour
const TINT = { 'market:gold': '#ffe8d6', 'market:morning': '#f1f3ff', 'market:day': '#ffffff', 'desert:sunrise': '#ffe6d4', 'desert:sunset': '#ffd4cc', 'void:': '#ecdcff', 'camp:': '#a9b6ff', 'test:': '#ffffff' };
export function finishFrame(world, t, shot, camera) {
  CH2D.cam = camera; CH2D.H = world.renderer.domElement.height;
  CH2D.tint.set(shot.tint || TINT[shot.set + ':' + (shot.light || '')] || TINT[shot.set + ':'] || '#ffffff');
  for (const c of allChars()) if (c.root.visible) c.update(t);
  for (const cm of world.anchors.desert.camels) if (cm.root.visible) cm.update(t);
}
