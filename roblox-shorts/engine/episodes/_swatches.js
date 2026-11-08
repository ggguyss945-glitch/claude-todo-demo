// Texture swatch board: every procedural generator on a lit tile (2 columns x 5 rows) plus a sky strip.
// node tools/render.js engine/episodes/_swatches.js <outdir> times=0.5
import * as THREE from 'three';

export default {
  name: 'swatches', fps: 60, seed: 'swatches',
  shots: [{
    name: 'board', start: 0, end: 1,
    build(ctx) {
      const { tex } = ctx;
      const items = [
        ['grass', tex.grass({ repeat: 2 })], ['woodPlanks', tex.woodPlanks({ color: '#9f3305', planks: 6, repeat: 1 })],
        ['brick', tex.brick({ repeat: 1 })], ['plaster', tex.plaster({ color: '#5063af', repeat: 1 })],
        ['fabric', tex.fabric({ color: '#a93298', repeat: 1 })], ['carpet', tex.carpet({ color: '#e58fc2', repeat: 1 })],
        ['roofShingles', tex.roofShingles({ repeat: 1 })], ['concrete', tex.concrete({ repeat: 1 })],
        ['dirt', tex.dirt({ repeat: 1 })], ['woodPlanks light', tex.woodPlanks({ color: '#c99a6b', planks: 4, joints: 2, seed: 5, gloss: 0.5, repeat: 1 })],
      ];
      const g = new THREE.Group();
      items.forEach(([name, b], i) => {
        const m = new THREE.Mesh(new THREE.PlaneGeometry(1.9, 1.9), new THREE.MeshStandardMaterial({ ...b.mat, roughness: 1 }));
        m.position.set((i % 2) * 2 - 1, 4 - Math.floor(i / 2) * 2, 0); g.add(m);
      });
      const sky = tex.starSky({ seed: 9, width: 1024, stops: [[-1, '#05041a'], [0, '#2a2766'], [0.25, '#13113f'], [1, '#020210']], stars: 1500, nebula: 0.4 });
      const strip = new THREE.Mesh(new THREE.PlaneGeometry(3.9, 1.95), new THREE.MeshBasicMaterial({ map: sky })); strip.position.set(0, -6.05, 0); g.add(strip);
      ctx.add(g);
      ctx.add(ctx.lights.hemi('#ffffff', '#888888', 1.2));
      ctx.add(ctx.lights.sun({ color: '#ffffff', intensity: 2.2, pos: [-3, 4, 6], shadow: false }));
      ctx.camera.set({ pos: [0, -1, 9.6], target: [0, -1, 0], fov: 69 });
      ctx.post.set({ toneMapping: 'neutral' });
    },
  }],
};
