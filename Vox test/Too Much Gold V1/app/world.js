// Sets: each lives in its own group far from the others; only the active one is visible.
import * as THREE from 'three';
import { toon, mk, fxLayer, LAYER } from './toon.js';
import { canvas, toTex } from './tex.js';
import { makeCast } from './cast.js';
import * as SETS from './sets.js';

export function buildWorld(scene, renderer) {
  const W = { sets: {}, cast: {}, props: {}, anchors: {}, scene, actors: [] };
  W.cast = makeCast(scene);
  for (const name of SETS.ORDER) W.sets[name] = SETS.BUILD[name](scene, W, renderer);
  return W;
}

// gradient sky dome with a sun glow, drawn with a tiny shader so it never shows banding
export function skyDome(parent, o) {
  const mat = new THREE.ShaderMaterial({
    uniforms: {
      top: { value: new THREE.Color(o.top) }, mid: { value: new THREE.Color(o.mid) }, hor: { value: new THREE.Color(o.horizon) },
      sunDir: { value: new THREE.Vector3(...o.sunDir).normalize() }, sunCol: { value: new THREE.Color(o.sun || '#fff2c8') },
      sunSize: { value: o.sunSize ?? 0.9994 }, glow: { value: o.glow ?? 0.6 }, stars: { value: o.stars ? 1 : 0 },
    },
    vertexShader: 'varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: `
      uniform vec3 top, mid, hor, sunCol, sunDir; uniform float sunSize, glow, stars; varying vec3 vD;
      float h(vec3 p){ return fract(sin(dot(p, vec3(12.9898,78.233,37.719))) * 43758.5453); }
      void main(){
        float y = clamp(vD.y, -0.2, 1.0);
        vec3 c = mix(hor, mid, smoothstep(0.0, 0.18, y));
        c = mix(c, top, smoothstep(0.18, 0.75, y));
        float s = max(dot(vD, sunDir), 0.0);
        c += sunCol * (pow(s, 12.0) * 0.35 + pow(s, 120.0) * 0.6) * glow;
        c = mix(c, sunCol * 2.4, smoothstep(sunSize, sunSize + 0.0004, s));
        if (stars > 0.5) {
          vec3 q = floor(vD * 420.0);
          float st = step(0.9965, h(q)) * smoothstep(0.05, 0.3, y);
          c += st * vec3(1.0, 0.97, 0.9) * (0.6 + 0.4 * h(q + 3.1));
        }
        gl_FragColor = vec4(c, 1.0);
      }`,
    side: THREE.BackSide, depthWrite: false, fog: false,
  });
  const m = new THREE.Mesh(new THREE.SphereGeometry(o.radius || 700, 48, 24), mat);
  m.renderOrder = -10;
  m.layers.set(LAYER.FX);
  parent.add(m);
  return m;
}
