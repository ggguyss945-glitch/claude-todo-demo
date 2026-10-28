// Toon look: soft-lit materials, screen-space inverted-hull outlines, and the render layers
// that keep outlines / effects out of the edge-detection pass.
import * as THREE from 'three';

export const LAYER = { MAIN: 0, HULL: 1, FX: 2 };
export const RES = new THREE.Vector2(1440, 2560);
export const OUTLINE = '#15100c';

// averaged normals so hulls of hard-edged meshes extrude without cracks at the corners
export function addSmoothNormals(geo) {
  if (geo.getAttribute('smoothNormal')) return geo;
  const pos = geo.getAttribute('position');
  if (!geo.getAttribute('normal')) geo.computeVertexNormals();
  const nrm = geo.getAttribute('normal');
  const key = (i) => `${pos.getX(i).toFixed(4)},${pos.getY(i).toFixed(4)},${pos.getZ(i).toFixed(4)}`;
  const acc = new Map();
  for (let i = 0; i < pos.count; i++) {
    const k = key(i);
    const a = acc.get(k) || [0, 0, 0];
    a[0] += nrm.getX(i); a[1] += nrm.getY(i); a[2] += nrm.getZ(i);
    acc.set(k, a);
  }
  const out = new Float32Array(pos.count * 3);
  for (let i = 0; i < pos.count; i++) {
    const a = acc.get(key(i));
    const l = Math.hypot(a[0], a[1], a[2]) || 1;
    out[i * 3] = a[0] / l; out[i * 3 + 1] = a[1] / l; out[i * 3 + 2] = a[2] / l;
  }
  geo.setAttribute('smoothNormal', new THREE.BufferAttribute(out, 3));
  return geo;
}

const hullMats = new Map();
export function hullMaterial(widthPx = 4, color = OUTLINE) {
  const k = widthPx + color;
  if (hullMats.has(k)) return hullMats.get(k);
  const m = new THREE.ShaderMaterial({
    uniforms: { uWidth: { value: widthPx }, uRes: { value: RES }, uColor: { value: new THREE.Color(color) } },
    vertexShader: `
      attribute vec3 smoothNormal;
      uniform float uWidth; uniform vec2 uRes;
      #include <common>
      #include <fog_pars_vertex>
      void main(){
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        vec4 clip = projectionMatrix * mv;
        vec3 n = normalize(normalMatrix * smoothNormal);
        vec2 dir = (projectionMatrix * vec4(n, 0.0)).xy;
        float l = length(dir);
        dir = l > 1e-5 ? dir / l : vec2(0.0);
        // a touch thicker in close-ups, thinner far away, never vanishing
        float w = uWidth * (uRes.x / 1440.0) * clamp(3.4 / max(-mv.z, 0.05), 0.72, 1.7);
        clip.xy += dir * w * 2.0 / uRes * clip.w;
        gl_Position = clip;
        vec4 mvPosition = mv;
        #include <fog_vertex>
      }`,
    fragmentShader: `
      uniform vec3 uColor;
      #include <fog_pars_fragment>
      void main(){ gl_FragColor = vec4(uColor, 1.0);
        #include <fog_fragment>
      }`,
    side: THREE.BackSide,
    fog: true,
  });
  m.uniforms = THREE.UniformsUtils.merge([THREE.UniformsLib.fog, m.uniforms]);
  m.uniforms.uRes.value = RES;
  hullMats.set(k, m);
  return m;
}

// give a mesh a black outline shell (shares its geometry)
export function outline(mesh, widthPx = 4, color = OUTLINE) {
  addSmoothNormals(mesh.geometry);
  const h = new THREE.Mesh(mesh.geometry, hullMaterial(widthPx, color));
  h.layers.set(LAYER.HULL);
  h.castShadow = false; h.receiveShadow = false;
  h.raycast = () => {};
  h.userData.isHull = true;
  mesh.add(h);
  return mesh;
}

// soft, slightly flat "storybook" surface
export function toon(color, opts = {}) {
  const m = new THREE.MeshStandardMaterial({
    color, roughness: opts.rough ?? 0.92, metalness: opts.metal ?? 0.0, map: opts.map || null,
    emissive: opts.emissive || 0x000000, emissiveIntensity: opts.emissiveIntensity ?? 1, side: opts.side ?? THREE.FrontSide,
    transparent: !!opts.transparent, opacity: opts.opacity ?? 1, alphaTest: opts.alphaTest ?? 0, flatShading: !!opts.flat,
  });
  if (opts.lift) { // a little self-light so colours stay bright and graphic in shadow
    m.emissive = new THREE.Color(color).multiplyScalar(opts.lift);
    if (opts.map) m.emissiveMap = opts.map;
  }
  return m;
}

export function gold(opts = {}) {
  return new THREE.MeshStandardMaterial({ color: opts.color || '#ffc63a', metalness: 1.0, roughness: opts.rough ?? 0.26, envMapIntensity: opts.env ?? 1.4,
    emissive: new THREE.Color('#5a3a00'), emissiveIntensity: opts.glow ?? 0.35, map: opts.map || null });
}

// helper: mesh with material, optional outline, shadows, added to parent
export function mk(geo, mat, parent, opts = {}) {
  const m = new THREE.Mesh(geo, mat);
  m.castShadow = opts.cast ?? true;
  m.receiveShadow = opts.receive ?? true;
  if (opts.pos) m.position.set(...opts.pos);
  if (opts.rot) m.rotation.set(...opts.rot);
  if (opts.scale) (Array.isArray(opts.scale) ? m.scale.set(...opts.scale) : m.scale.setScalar(opts.scale));
  if (opts.outline !== false && opts.outline !== undefined) outline(m, opts.outline === true ? 3.2 : opts.outline);
  if (parent) parent.add(m);
  return m;
}

// effects (shafts, particles, glows) live on the FX layer so the edge pass ignores them
export function fxLayer(obj) { obj.traverse((o) => o.layers.set(LAYER.FX)); return obj; }
