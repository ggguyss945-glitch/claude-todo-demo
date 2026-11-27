// Channel branding stills (?brand=1), past the end of the film. Nothing here is tied to one video:
// the logo is the channel's own mascot, the banner a cast from different eras on a plain sky.
//   200: round logo, the mascot's "wait, what?" face (render 2048x2048)
//   210: banner, the cast on both sides with the middle left clear for the name (render 2560x1440)
import { V, put, look, idle, handL } from './lib.js';
import { makeToon } from './chars2d.js';

const O = V(-600, 0, 0); // the plain 'test' set: sky and ground, no location

export function addBrand(S, W) {
  const C = W.cast;
  // the mascot: a curious narrator with round glasses and a teal tunic
  const m = (C.mascot = makeToon({ name: 'mascot', seed: 7, body: 'bean', color: '#16a39a', belt: '#ffd23f', collar: '#ffd23f', skin: '#f7f3ec',
    glasses: true, hat: { type: 'hair', color: '#2a1a10', cut: 0.42, fringe: true }, faceRes: 1024 }));
  m.root.visible = false; W.scene.add(m.root);
  const at = (x, z) => O.clone().add(V(x, 0, z));

  S.push({ t0: 200, t1: 201, set: 'test',
    cam: () => ({ p: at(0, 2.0).add(V(0, 1.42, 0)).toArray(), l: at(0, 0).add(V(0, 1.42, 0)).toArray(), fov: 30, ap: 10, focus: 2.0 }),
    setup(w, t, camera) {
      put(m, at(0, 0), 0, 'shocked'); look(m, camera.position, 1);
      handL(m, 'l', 0.3, 1.2, 0.25); handL(m, 'r', -0.3, 1.2, 0.25);
    } });

  S.push({ t0: 210, t1: 211, set: 'test',
    cam: () => ({ p: at(0, 5.6).add(V(0, 1.15, 0)).toArray(), l: at(0, -1).add(V(0, 1.15, 0)).toArray(), fov: 33, ap: 3, focus: 5.6 }),
    setup(w, t, camera) {
      const P = camera.position;
      const cast = [
        [m, -1.45, 0.45, 'surprised'], [C.musa, -2.25, -0.15, 'proud'], [C.kid1, -2.95, 0.2, 'laugh'],
        [C.changer, 1.45, 0.45, 'shocked'], [C.baker, 2.25, -0.15, 'grin'], [C.town?.[0], 2.95, 0.1, 'joy'],
      ];
      for (const [c, x, z, e] of cast) {
        if (!c) continue;
        put(c, at(x, z), -x * 0.18, e); idle(c, 0.4 + x); look(c, P, 1);
      }
      handL(m, 'l', 0.35, 1.35, 0.2);
    } });
}
