// TEMPORARY (part 5 QA, deleted after use): s88 camera variants side by side, one per second.
import * as THREE from 'three';
import * as sets from '../../kit/sets.js';
import * as K from '../../kit/chars.js';
import * as CR from '../../kit/creatures.js';
import * as SE from '../../kit/sets_ep01.js';

const TL = await (await fetch(new URL('../../../episodes/ep01/timeline.json', import.meta.url))).json();
const P88 = TL.shots.find((s) => s.name === 's88').params;
const VARS = [
  { bo: -8, h: 10.5, back: 1.5, side: 3.5, yaw: 68, pitch: -16, fov: 50, skip: 1, dt: 0 },
  { bo: -8, h: 8, back: 2.5, side: 3.0, yaw: 55, pitch: -12, fov: 60, skip: 1, dt: 0 },
  { bo: -16, h: 10.5, back: 2.5, side: 3.0, yaw: 55, pitch: -16, fov: 55, skip: 1, dt: 0 },
  { bo: -30, h: 8, back: 0.9, side: 3.0, yaw: 48, pitch: -9, fov: 70, skip: 1, dt: 0 },
  { bo: -8, h: 6, back: 4, side: 3, yaw: 50, pitch: -8, fov: 70, skip: 1, dt: 0 },
  { bo: -20, h: 10, back: 3, side: 3, yaw: 45, pitch: -14, fov: 60, skip: 1, dt: 0 },
];
const wp = (o) => { o.updateWorldMatrix(true, false); return o.getWorldPosition(new THREE.Vector3()); };
function build(ctx, v) {
  const T = SE.ep01Street(ctx, { tod: 'dawn', lanterns: 0.5, truck: 'leaving', skip: v.skip ? ['A4.bed0', 'A4.lawn0', 'A4.lawn3'] : [], truckOpts: { t0: -0.45, accel: 4, vmax: 6, balconyBox: false, dome: false, backOffset: v.bo ?? -8 } }); ctx.add(T); ctx.shared.T = T;
  const gpos = wp(T.ep01.grandpa); const theo = K.makeCharacter('theo', { face: 'content' }); const wh = CR.stuffedWhale(); CR.holdWhale(theo, wh, 'underArm');
  theo.position.set(gpos.x + 0.9, 0, gpos.z + 0.55); theo.rotation.y = 0.5; K.setPose(theo, { armLx: 14, armLz: -10, armRz: 130 }); ctx.add(theo);
  const pov = T.ep01.truck.ep01.povCamera({ height: v.h, back: v.back, side: v.side, pitch: v.pitch, fov: v.fov || 70, yaw: v.yaw });
  ctx.camera.set({ pos: pov.pos, target: pov.target, fov: pov.fov });
  sets.dawn(ctx, { set: T, sun: { az: v.az ?? 92, el: 9 }, postOpts: { exposure: 1.6 } });
}
export default {
  name: 'p5dbg', fps: 60, width: 1080, height: 1920, seed: 'ep01', quality: { shadows: 'pcfsoft' }, post: sets.postPreset('dawn'),
  shots: VARS.map((v, i) => ({ name: 'v' + i, start: i, end: i + 1, params: P88, build: (ctx) => build(ctx, v), update: (ctx, t) => ctx.shared.T.ep01.update(t + v.dt) })),
};
