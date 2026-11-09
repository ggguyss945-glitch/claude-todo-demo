import * as THREE from 'three';
import * as sets from './sets.js';
export default { name: 'probe', fps: 60, width: 1080, height: 1920, seed: 'p', shots: [{ name: 'p', start: 0, end: 1, build(ctx) {
  const set = sets.buildLawnCloseup(ctx, { seed: 'ep01' }); ctx.add(set);
  const lot = set.getObjectByName('lot_A1'); const out = { pos: lot.position.toArray(), rot: lot.rotation.y, kids: [] };
  for (const c of lot.children) { const o = { n: c.name, t: c.type }; if (c.geometry) { c.geometry.computeBoundingBox(); const b = c.geometry.boundingBox; o.bb = [b.min.toArray().map(v=>+v.toFixed(2)), b.max.toArray().map(v=>+v.toFixed(2))]; o.idx = !!c.geometry.index; o.cnt = c.geometry.attributes.position.count; } else o.p = c.position.toArray().map(v=>+v.toFixed(2)); out.kids.push(o); }
  const L = set.userData.lots.find(l => l.id === 'A1'); out.lot = L; out.win = set.userData.windows.filter(w => w.lot === 'A1');
  out.slots = set.userData.slots.filter(s => s.lot === 'A1').map(s => [s.name, s.pos, +s.yaw.toFixed(2)]);
  out.A2 = set.userData.lots.find(l => l.id === 'A2'); out.lamps = set.userData.lamps.slice(0, 4);
  const js = JSON.stringify(out); for (let i = 0; i < js.length; i += 250) console.warn('P' + String(i/250).padStart(3,'0') + ' ' + js.slice(i, i + 250));
  ctx.camera.set({ pos: [0, 2, 5], target: [0, 1, -10], fov: 60 }); sets.nightLawn(ctx, { set });
}, update() {} }] };
