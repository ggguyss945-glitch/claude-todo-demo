// Renderer setup, per-shot quality, fog (distance + exponential height fog), light helpers, resource disposal.
import * as THREE from 'three';

// ---------------- height fog: patch three's fog chunks once (before any shader compiles) ----------------
// Fog factor = 1 - (1 - distanceFog) * (1 - heightFog). Height fog is exponential in height (Roblox-Atmosphere /
// UE-style): density * exp(-falloff * (y - base)), integrated analytically along the view ray.
export const fogUniforms = {
  fogHeight: { value: new THREE.Vector4(0, 0.3, 0, 0) }, // x base height, y falloff (1/m), z density, w enabled
  fogHeightColor: { value: new THREE.Color(1, 1, 1) },
  fogHeightMax: { value: 1 }, // cap of the height-fog opacity
};
let _patched = false;
export function patchFogChunks() {
  if (_patched) return; _patched = true;
  const C = THREE.ShaderChunk;
  C.fog_pars_vertex = `#ifdef USE_FOG\n varying float vFogDepth; varying vec3 vFogWorldPos;\n#endif`;
  C.fog_vertex = `#ifdef USE_FOG\n vFogDepth = - mvPosition.z; vFogWorldPos = transpose(mat3(viewMatrix)) * (mvPosition.xyz - viewMatrix[3].xyz);\n#endif`;
  C.fog_pars_fragment = `#ifdef USE_FOG
  uniform vec3 fogColor; varying float vFogDepth; varying vec3 vFogWorldPos;
  uniform vec4 fogHeight; uniform vec3 fogHeightColor; uniform float fogHeightMax;
  #ifdef FOG_EXP2
    uniform float fogDensity;
  #else
    uniform float fogNear; uniform float fogFar;
  #endif
#endif`;
  C.fog_fragment = `#ifdef USE_FOG
  #ifdef FOG_EXP2
    float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
  #else
    float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
  #endif
  vec3 fogCol = fogColor;
  if ( fogHeight.w > 0.5 ) {
    vec3 rd = vFogWorldPos - cameraPosition; float dist = length( rd );
    float k = fogHeight.y; float dy = rd.y;
    float h0 = exp( - k * ( cameraPosition.y - fogHeight.x ) );
    float integ = abs( k * dy ) > 1e-4 ? h0 * ( 1.0 - exp( - k * dy ) ) / ( k * dy ) : h0;
    float hf = min( 1.0 - exp( - fogHeight.z * dist * integ ), fogHeightMax );
    fogCol = mix( fogColor, fogHeightColor, hf / max( 1e-4, hf + fogFactor ) );
    fogFactor = 1.0 - ( 1.0 - fogFactor ) * ( 1.0 - hf );
  }
  gl_FragColor.rgb = mix( gl_FragColor.rgb, fogCol, fogFactor );
#endif`;
}
const _hooked = new WeakSet();
function hookMaterial(m) {
  if (_hooked.has(m)) return; _hooked.add(m);
  const prev = m.onBeforeCompile;
  m.onBeforeCompile = function (shader, renderer) {
    shader.uniforms.fogHeight = fogUniforms.fogHeight; shader.uniforms.fogHeightColor = fogUniforms.fogHeightColor; shader.uniforms.fogHeightMax = fogUniforms.fogHeightMax;
    if (prev && prev !== THREE.Material.prototype.onBeforeCompile) prev.call(this, shader, renderer);
  };
}
// Install the height-fog uniforms on every material in the scene (cheap; the engine calls this every frame).
export function hookSceneMaterials(scene) {
  scene.traverse((o) => { const m = o.material; if (!m) return; if (Array.isArray(m)) m.forEach(hookMaterial); else hookMaterial(m); });
}
// setFog(scene, {color, near, far} | {color, density} | null, height?: {base, falloff, density, color, max})
// Distance fog uses three's Fog/FogExp2; height fog is optional on top. Sky domes: give them fog: true to fade
// into the fog colour (Roblox Atmosphere look), fog: false to stay visible (night skies).
export function setFog(scene, opts) {
  if (!opts) { scene.fog = null; fogUniforms.fogHeight.value.w = 0; return; }
  const color = new THREE.Color(opts.color ?? '#808080');
  if (opts.density != null) scene.fog = new THREE.FogExp2(color, opts.density);
  else scene.fog = new THREE.Fog(color, opts.near ?? 10, opts.far ?? 100);
  const h = opts.height;
  if (h) { fogUniforms.fogHeight.value.set(h.base ?? 0, h.falloff ?? 0.3, h.density ?? 0.05, 1); fogUniforms.fogHeightColor.value.set(h.color ?? color); fogUniforms.fogHeightMax.value = h.max ?? 1; }
  else fogUniforms.fogHeight.value.w = 0;
}

// ---------------- renderer ----------------
export function createRenderer(canvas, width, height) {
  patchFogChunks();
  THREE.ColorManagement.enabled = true;
  const r = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: false, preserveDrawingBuffer: false, powerPreference: 'high-performance', stencil: false, depth: false });
  r.setPixelRatio(1); r.setSize(width, height, false);
  r.outputColorSpace = THREE.SRGBColorSpace; // the post stack encodes sRGB itself; this only matters without post
  r.toneMapping = THREE.NoToneMapping; r.toneMappingExposure = 1; // tone mapping happens in the post uber pass
  r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFSoftShadowMap; r.shadowMap.autoUpdate = true;
  return r;
}
export const SHADOW_TYPES = { off: null, basic: THREE.BasicShadowMap, pcf: THREE.PCFShadowMap, pcfsoft: THREE.PCFSoftShadowMap, vsm: THREE.VSMShadowMap };
// quality: { shadows: 'pcfsoft'|'vsm'|'pcf'|'basic'|'off', shadowMapSize: 2048 (applies to lights made with helpers
// that pass size 'auto'), msaa: 4 }. Returns true if materials need recompiling.
export function applyQuality(renderer, scene, q) {
  const type = SHADOW_TYPES[q.shadows ?? 'pcfsoft'];
  const enabled = type != null; let changed = false;
  if (renderer.shadowMap.enabled !== enabled) { renderer.shadowMap.enabled = enabled; changed = true; }
  if (enabled && renderer.shadowMap.type !== type) { renderer.shadowMap.type = type; changed = true; }
  if (changed) scene.traverse((o) => { if (o.material) [].concat(o.material).forEach((m) => (m.needsUpdate = true)); });
  return changed;
}

// ---------------- lights (physically based: intensities in lux / candela, decay 2) ----------------
export const lights = {
  ambient(color = '#ffffff', intensity = 0.3) { return new THREE.AmbientLight(color, intensity); },
  hemi(sky = '#bfd4ff', ground = '#3a3040', intensity = 0.8) { return new THREE.HemisphereLight(sky, ground, intensity); },
  // Directional "sun/moon" with a shadow box around `target`. size = half-extent of the ortho shadow camera (m).
  sun({ color = '#fff2e0', intensity = 2.5, pos = [5, 10, 6], target = [0, 0, 0], shadow = true, size = 8, mapSize = 2048, bias = -0.0004, normalBias = 0.02, radius = 3, blurSamples = 12, near = 0.5, far = 60 } = {}) {
    const l = new THREE.DirectionalLight(color, intensity); l.position.set(...pos); l.target.position.set(...target);
    if (shadow) {
      l.castShadow = true; const c = l.shadow.camera; c.left = -size; c.right = size; c.top = size; c.bottom = -size; c.near = near; c.far = far;
      l.shadow.mapSize.set(mapSize, mapSize); l.shadow.bias = bias; l.shadow.normalBias = normalBias; l.shadow.radius = radius; l.shadow.blurSamples = blurSamples;
    }
    l.userData.addTarget = true; return l;
  },
  // Point light: intensity in candela (a 60 W bulb ~ 70 cd; small lantern 2-10 cd). distance 0 = infinite.
  point({ color = '#ffcf8a', intensity = 5, pos = [0, 1, 0], distance = 0, decay = 2, shadow = false, mapSize = 512, bias = -0.002, radius = 4, near = 0.05, far = 30 } = {}) {
    const l = new THREE.PointLight(color, intensity, distance, decay); l.position.set(...pos);
    if (shadow) { l.castShadow = true; l.shadow.mapSize.set(mapSize, mapSize); l.shadow.bias = bias; l.shadow.radius = radius; l.shadow.camera.near = near; l.shadow.camera.far = far; }
    return l;
  },
  spot({ color = '#ffffff', intensity = 50, pos = [0, 4, 0], target = [0, 0, 0], angle = 0.6, penumbra = 0.6, distance = 0, decay = 2, shadow = false, mapSize = 1024, bias = -0.0005, radius = 3 } = {}) {
    const l = new THREE.SpotLight(color, intensity, distance, angle, penumbra, decay); l.position.set(...pos); l.target.position.set(...target);
    if (shadow) { l.castShadow = true; l.shadow.mapSize.set(mapSize, mapSize); l.shadow.bias = bias; l.shadow.radius = radius; }
    l.userData.addTarget = true; return l;
  },
};
// Add a light (and its target, if any) to a scene/group.
export function addLight(parent, l) { parent.add(l); if (l.userData.addTarget && l.target) parent.add(l.target); return l; }

// ---------------- disposal ----------------
// Resources flagged persistent (textures from textures.js, objects built through ctx.cache) survive shot changes.
export const markPersistent = (res) => { if (res) res.userData = Object.assign(res.userData || {}, { persistent: true }); return res; };
export function markTreePersistent(obj) {
  obj.traverse((o) => {
    if (o.geometry) markPersistent(o.geometry);
    if (o.material) [].concat(o.material).forEach((m) => { markPersistent(m); for (const k in m) { const v = m[k]; if (v && v.isTexture) markPersistent(v); } });
  });
  return obj;
}
export function disposeTree(obj) {
  const seen = new Set();
  obj.traverse((o) => {
    if (o.geometry && !o.geometry.userData?.persistent && !seen.has(o.geometry)) { seen.add(o.geometry); o.geometry.dispose(); }
    if (o.material) for (const m of [].concat(o.material)) {
      if (seen.has(m)) continue; seen.add(m);
      for (const k in m) { const v = m[k]; if (v && v.isTexture && !v.userData?.persistent && !seen.has(v)) { seen.add(v); v.dispose(); } }
      if (!m.userData?.persistent) m.dispose();
    }
    if (o.isLight && o.shadow?.map) { o.shadow.map.dispose(); o.shadow.map = null; }
  });
}
