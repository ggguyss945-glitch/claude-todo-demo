// look-development views (not in the film): ?look=1
import * as THREE from 'three';
export function add(S, W) {
  const C = W.cast;
  const put = (ch, x, z, yaw, expr) => { ch.root.visible = true; ch.root.position.set(x, 0, z); ch.root.rotation.y = yaw; ch.state.expr = expr; };
  // 0: lineup of the main cast in the market street
  S.push({ t0: 0, t1: 1, set: 'market', light: 'gold', cam: () => ({ p: [0, 1.25, 3.6], l: [0, 1.0, -1.0], fov: 46, ap: 3 }),
    setup: (w, t) => {
      [[C.spice, -1.05, -1.2, 'smug'], [C.musa, -0.35, -0.6, 'proud'], [C.baker, 0.4, -0.7, 'happy'], [C.kid1, 0.95, -0.2, 'joy'], [C.changer, 1.25, -1.6, 'unimpressed'], [C.att1, -1.5, -2.2, 'neutral']]
        .forEach(([c, x, z, e]) => put(c, x, z, -x * 0.25, e));
    } });
  // 1: medium shot of the king, framed like the reference's emperor shot
  S.push({ t0: 1, t1: 2, set: 'market', light: 'gold', cam: () => ({ p: [0.15, 1.3, 1.55], l: [-0.05, 1.12, -0.5], fov: 50, ap: 9, focus: 2.1 }),
    setup: (w, t) => { put(C.musa, -0.25, -0.45, 0.35, 'smug'); const m = C.musa; m.pose.hands.r = new THREE.Vector3(-0.3, 1.05, 0.25); m.pose.headYaw = 0.25; } });
  // 2: crowd of townsfolk
  S.push({ t0: 2, t1: 3, set: 'market', light: 'gold', cam: () => ({ p: [0, 1.4, 4.2], l: [0, 1.1, -2], fov: 50, ap: 3 }),
    setup: (w, t) => { C.town.forEach((c, i) => put(c, -1.8 + (i % 6) * 0.72, -0.6 - Math.floor(i / 6) * 1.3, 0, ['happy', 'neutral', 'surprised', 'grin', 'unimpressed', 'joy'][i % 6])); } });
}
