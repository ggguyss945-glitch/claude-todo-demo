// Shot list, timed to the narration's word timings.
import * as THREE from 'three';
import { defaultPose } from './chars.js';

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

export function finishFrame(world, t, shot, camera) {
  for (const c of allChars()) if (c.root.visible) c.update(t);
  for (const cm of world.anchors.desert.camels) if (cm.root.visible) cm.update(t);
}
