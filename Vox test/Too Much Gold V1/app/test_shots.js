// look-development views of the sets (not in the film)
import * as THREE from 'three';
export function add(S, W) {
  const C = W.cast;
  const put = (ch, x, z, yaw, expr) => { ch.root.visible = true; ch.root.position.set(x, 0, z); ch.root.rotation.y = yaw; ch.state.expr = expr; };
  S.push({ t0: 0, t1: 1, set: 'market', light: 'gold', cam: () => ({ p: [0.3, 1.6, 7], l: [0, 2.6, -12], fov: 50, ap: 4 }),
    setup: (w, t) => { put(C.spice, -1.2, -2, 0.3, 'greedy'); put(C.musa, 0.6, -4, 0, 'proud'); put(C.kid1, 1.4, -1, -0.4, 'joy'); C.town.slice(0, 6).forEach((c, i) => put(c, (i % 2 ? 1.8 : -1.8), -7 - i * 2, i % 2 ? -0.5 : 0.5, 'neutral')); } });
  S.push({ t0: 1, t1: 2, set: 'market', light: 'morning', cam: () => ({ p: [-1.0, 1.5, -2.5], l: [3.4, 1.2, -6.5], fov: 45, ap: 6 }),
    setup: (w, t) => { put(C.baker, 2.6, -6.4, -Math.PI / 2, 'shrug'); } });
  S.push({ t0: 2, t1: 3, set: 'desert', light: 'sunrise', cam: () => ({ p: [1000, 4, 16], l: [1000, 6, -60], fov: 50, ap: 2 }),
    setup: (w, t) => { const A = w.anchors.desert; A.camels.forEach((cm, i) => { cm.root.visible = true; cm.root.position.set(1000 - 12 + i * 4.2, 0, 0); cm.root.rotation.y = Math.PI / 2; cm.pose.walk = { phase: t * 0.9 + i * 0.3, stride: 0.8 }; cm.update(t); }); } });
  S.push({ t0: 3, t1: 4, set: 'void', cam: () => ({ p: [2000, 1.5, 2.6], l: [2000, 1.2, 0], fov: 40, ap: 8 }),
    setup: (w, t) => { const A = w.anchors.void; A.pool.clear(); A.hero.clear(); A.hero.add(new THREE.Vector3(2000, 1.36, 0), 1.2, 0.3, 0); } });
  S.push({ t0: 4, t1: 5, set: 'camp', cam: () => ({ p: [3000 + 2.5, 1.4, 3.5], l: [3000, 0.9, -0.5], fov: 45, ap: 6 }),
    setup: (w, t) => { put(C.musa, 3000 + 1.0, -0.4, Math.PI - 0.35, 'happy'); } });
}
