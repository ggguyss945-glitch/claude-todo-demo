// Post stack, built for SwiftShader (CPU) speed: the scene renders once into a half-float HDR target; blur chains
// run at half resolution and below; one full-resolution "uber" pass does everything else. Each effect is compiled
// in only when enabled (shader #defines), so disabled effects cost nothing.
//
// Order: scene (HDR linear, MSAA) -> [DOF gather, half res] -> [bloom pyramid] -> [glow pyramid] -> [god rays, 1/4 res]
// -> UBER: lens distortion, chromatic aberration, directional/zoom blur, DOF composite, + bloom, + rays, glow,
// exposure, white balance (temperature/tint), tone map (ACES/AgX/Neutral/...), sRGB encode, grade (lift/gamma/gain,
// contrast, saturation, split toning, output levels), vignette, fade, flash, grain, dither -> [FXAA] -> [extra LDR passes]
import * as THREE from 'three';
import { FullScreenQuad } from 'three/addons/postprocessing/Pass.js';
import { FXAAShader } from 'three/addons/shaders/FXAAShader.js';

// ---------------- parameters ----------------
export function defaultPostParams() {
  return {
    toneMapping: 'aces', // 'aces' | 'agx' | 'neutral' | 'reinhard' | 'cineon' | 'linear' | 'none'
    exposure: 1,
    aa: 'msaa', // 'msaa' (scene MSAA x msaaSamples) | 'fxaa' | 'msaa+fxaa' | 'none'
    msaaSamples: 4,
    dither: true,
    // Bloom on highlights (soft threshold). strength = mix amount, radius 0..1 = halo size (scatter), threshold in
    // linear HDR units (1.0 = white before tone mapping), knee = threshold softness.
    bloom: { enabled: false, strength: 0.4, radius: 0.6, threshold: 0.9, knee: 0.5, levels: 6, tint: '#ffffff' },
    // "Dreamy" diffusion / Pro-Mist glow: a wide blur of the whole image (threshold 0) blended over it.
    // mode 'screen' (display space, Orton-like), 'add' (linear light), 'mix' (soft-focus haze).
    glow: { enabled: false, amount: 0.2, radius: 0.75, threshold: 0.0, knee: 0.5, levels: 6, mode: 'screen', tint: '#ffffff' },
    // Depth of field. focus: 'auto' (ShotCamera focus) or metres. aperture = blur in px (1080-wide) for objects at
    // infinity; maxBlur clamps near blur (px). range = in-focus band half-width (m). quality: 'low'|'med'|'high'.
    dof: { enabled: false, focus: 'auto', aperture: 14, maxBlur: 24, range: 0.0, quality: 'med' },
    // Vignette (display space). amount 0..1 = darkening at corners, size = radius where it starts (0..1),
    // softness = falloff width, roundness 1 = circle in screen space, 0 = follows the 9:16 frame.
    vignette: { enabled: false, amount: 0.3, size: 0.45, softness: 0.55, roundness: 0.6, color: '#000000', center: [0.5, 0.5] },
    // Chromatic aberration: radial RGB split, px at the frame corner (1080-wide).
    chroma: { enabled: false, amount: 2.5 },
    // Lens distortion: k1 barrel(-)/pincushion(+), k2 higher order, zoom to hide the edges.
    lens: { enabled: false, k1: -0.08, k2: 0.0, zoom: 1.0 },
    // Colour grade. Colours accept '#hex' (display-space) or [r,g,b] 0..1.
    // temperature/tint: -100..100 (Lightroom-like white balance in linear light; + = warmer / more magenta).
    // lift/gamma/gain: per-channel (lift adds to shadows, gamma bends mids, gain scales highlights).
    // contrast around pivot (display space), saturation (1 = unchanged), vibrance (boosts low-sat colours),
    // split toning: shadows/highlights colours with amount 0..1 and balance -1..1,
    // outBlack/outWhite: output levels (e.g. outWhite '#e7d4fc' caps whites like the Tooth Fairies interiors).
    grade: {
      enabled: false, temperature: 0, tint: 0,
      lift: [0, 0, 0], gamma: [1, 1, 1], gain: [1, 1, 1], offset: [0, 0, 0],
      contrast: 1, pivot: 0.45, saturation: 1, vibrance: 0,
      shadows: '#808080', shadowsAmount: 0, highlights: '#808080', highlightsAmount: 0, balance: 0,
      outBlack: [0, 0, 0], outWhite: [1, 1, 1],
    },
    // Film grain (display space): amount 0..0.2, size in px, colored 0 (mono) .. 1 (RGB).
    grain: { enabled: false, amount: 0.035, size: 1.6, colored: 0.2 },
    // God rays: radial blur of bright pixels away from `source` (world [x,y,z] / Vector3 / Object3D, or screen
    // {screen:[u,v]} with v up). skyOnly uses the depth buffer so only the sky/background emits.
    godrays: { enabled: false, source: [0, 10, -50], threshold: 0.8, strength: 0.6, density: 0.9, decay: 0.96, weight: 0.35, samples: 40, skyOnly: false, tint: '#ffffff' },
    // Editor-style blur: directional (px, 1080-wide) and/or radial zoom (fraction), used for shake hits / whips.
    blur: { enabled: false, dir: [0, 0], zoom: 0, center: [0.5, 0.5], samples: 10 },
    // Transitions (display space): fade mixes toward colour, flash adds colour (screen blend).
    fade: { amount: 0, color: '#000000' },
    flash: { amount: 0, color: '#ffffff' },
    // Extra LDR ShaderMaterials (uniform tDiffuse, vUv). [{ material, enabled: true }]
    extra: [],
  };
}

const isObj = (v) => v && typeof v === 'object' && !Array.isArray(v) && !v.isColor && !v.isVector3 && !v.isObject3D && !v.isMaterial;
export function deepMerge(dst, src) {
  for (const k in src) { if (isObj(src[k]) && isObj(dst[k])) deepMerge(dst[k], src[k]); else dst[k] = src[k]; }
  return dst;
}
// display-space colour -> [r,g,b]
function rgb(v) {
  if (Array.isArray(v)) return v;
  if (typeof v === 'number') return [v, v, v];
  if (v && v.isColor) { const c = v.clone().convertLinearToSRGB(); return [c.r, c.g, c.b]; }
  const c = new THREE.Color(); c.setStyle(v, THREE.NoColorSpace); return [c.r, c.g, c.b];
}
// '#hex' -> linear THREE.Color (for light-space tints)
const lin = (v) => (Array.isArray(v) ? new THREE.Color(v[0], v[1], v[2]) : new THREE.Color(v));
const vec3 = (a) => new THREE.Vector3(a[0], a[1], a[2]);

// White balance matrix (Unity's LMS method). temperature/tint in -100..100.
function whiteBalance(temperature, tint) {
  const t1 = temperature / 65, t2 = tint / 65;
  const x = 0.31271 - t1 * (t1 < 0 ? 0.1 : 0.05);
  const y = 2.87 * x - 3 * x * x - 0.27509507 + t2 * 0.05;
  const X = x / y, Y = 1, Z = (1 - x - y) / y;
  const L = 0.7328 * X + 0.4296 * Y - 0.1624 * Z, M = -0.7036 * X + 1.6975 * Y + 0.0061 * Z, S = 0.003 * X + 0.0136 * Y + 0.9834 * Z;
  const w1 = [0.949237, 1.03542, 1.08728]; const b = [w1[0] / L, w1[1] / M, w1[2] / S];
  const lin2lms = new THREE.Matrix3().set(3.90405e-1, 5.49941e-1, 8.92632e-3, 7.08416e-2, 9.63172e-1, 1.35775e-3, 2.31082e-2, 1.28021e-1, 9.36245e-1);
  const lms2lin = new THREE.Matrix3().set(2.85847, -1.62879, -2.4891e-2, -2.10182e-1, 1.1582, 3.24281e-4, -4.1812e-2, -1.18169e-1, 1.06867);
  const D = new THREE.Matrix3().set(b[0], 0, 0, 0, b[1], 0, 0, 0, b[2]);
  return new THREE.Matrix3().multiplyMatrices(lms2lin, D).multiply(lin2lms);
}

// ---------------- shaders ----------------
const VS = /* glsl */`varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`;

// Dual-filter (Kawase) downsample with optional soft threshold + Karis average on the first level.
const DOWN_FS = /* glsl */`
uniform sampler2D tSrc; uniform vec2 uTexel; uniform vec4 uThresh; // x=threshold y=knee z=enable w=karis
varying vec2 vUv;
vec3 prefilter(vec3 c){
  if (uThresh.z < 0.5) return c;
  float br = max(c.r, max(c.g, c.b));
  float k = uThresh.x * uThresh.y + 1e-4;
  float soft = clamp(br - uThresh.x + k, 0.0, 2.0 * k); soft = soft * soft / (4.0 * k);
  float contrib = max(soft, br - uThresh.x) / max(br, 1e-4);
  return c * contrib;
}
vec3 tap(vec2 uv){ return min(texture2D(tSrc, uv).rgb, vec3(64.0)); }
void main(){
  vec2 o = uTexel;
  vec3 a = tap(vUv), b = tap(vUv + vec2(-o.x, -o.y)), c = tap(vUv + vec2(o.x, -o.y)), d = tap(vUv + vec2(-o.x, o.y)), e = tap(vUv + vec2(o.x, o.y));
  vec3 col;
  if (uThresh.w > 0.5) { // Karis average against fireflies
    float wa = 1.0/(1.0+dot(a,vec3(.2126,.7152,.0722))), wb = 1.0/(1.0+dot(b,vec3(.2126,.7152,.0722))), wc = 1.0/(1.0+dot(c,vec3(.2126,.7152,.0722))), wd = 1.0/(1.0+dot(d,vec3(.2126,.7152,.0722))), we = 1.0/(1.0+dot(e,vec3(.2126,.7152,.0722)));
    col = (a*wa*4.0 + b*wb + c*wc + d*wd + e*we) / (wa*4.0 + wb + wc + wd + we);
  } else col = (a * 4.0 + b + c + d + e) / 8.0;
  gl_FragColor = vec4(prefilter(col), 1.0);
}`;
// Dual-filter upsample (8 taps, tent-like) mixed with the matching down level by scatter.
const UP_FS = /* glsl */`
uniform sampler2D tLow; uniform sampler2D tHigh; uniform vec2 uTexel; uniform float uScatter;
varying vec2 vUv;
void main(){
  vec2 o = uTexel;
  vec3 s = texture2D(tLow, vUv + vec2(-2.0*o.x, 0.0)).rgb + texture2D(tLow, vUv + vec2(2.0*o.x, 0.0)).rgb
         + texture2D(tLow, vUv + vec2(0.0, -2.0*o.y)).rgb + texture2D(tLow, vUv + vec2(0.0, 2.0*o.y)).rgb
         + (texture2D(tLow, vUv + vec2(-o.x, -o.y)).rgb + texture2D(tLow, vUv + vec2(o.x, -o.y)).rgb
         +  texture2D(tLow, vUv + vec2(-o.x, o.y)).rgb + texture2D(tLow, vUv + vec2(o.x, o.y)).rgb) * 2.0;
  s /= 12.0;
  gl_FragColor = vec4(mix(texture2D(tHigh, vUv).rgb, s, uScatter), 1.0);
}`;

// Single-pass gather DOF at half resolution (after Dennis Gustafsson, "Bokeh depth of field in a single pass").
const DOF_FS = /* glsl */`
#include <packing>
uniform sampler2D tColor; uniform sampler2D tDepth; uniform vec2 uPx; // full-res px size in uv
uniform float uNear, uFar, uFocus, uAperture, uMaxBlur, uBand;
varying vec2 vUv;
float viewZ(vec2 uv){ return -perspectiveDepthToViewZ(texture2D(tDepth, uv).x, uNear, uFar); }
float coc(float z){ float d = 1.0 - uFocus / z; float s = sign(d); d = max(abs(d) - uBand, 0.0); return clamp(s * d * uAperture, -uMaxBlur, uMaxBlur); }
const float GOLDEN = 2.39996323;
void main(){
  float cz = viewZ(vUv); float cs = abs(coc(cz));
  vec3 col = texture2D(tColor, vUv).rgb; float tot = 1.0; float cover = cs;
  float r = RAD_SCALE; float ang = 0.0;
  for (int i = 0; i < MAX_TAPS; i++) {
    if (r >= uMaxBlur) break;
    vec2 tc = vUv + vec2(cos(ang), sin(ang)) * uPx * r;
    vec3 sc = texture2D(tColor, tc).rgb; float sz = viewZ(tc); float ss = abs(coc(sz));
    if (sz > cz) ss = clamp(ss, 0.0, cs * 2.0);
    float m = smoothstep(r - 0.5 * RAD_SCALE, r + 0.5 * RAD_SCALE, ss);
    if (sz < cz) cover = max(cover, m * ss);
    col += mix(col / tot, sc, m); tot += 1.0;
    r += RAD_SCALE * RAD_SCALE / r; ang += GOLDEN;
  }
  gl_FragColor = vec4(col / tot, cover);
}`;

// God rays: threshold mask then radial blur (GPU Gems 3, ch. 13).
const RAYMASK_FS = /* glsl */`
uniform sampler2D tColor; uniform sampler2D tDepth; uniform float uThreshold; uniform float uSkyOnly;
varying vec2 vUv;
void main(){
  vec3 c = texture2D(tColor, vUv).rgb; float l = max(c.r, max(c.g, c.b));
  float m = smoothstep(uThreshold, uThreshold * 1.5 + 0.05, l);
  #ifdef USE_DEPTH
  if (uSkyOnly > 0.5) m *= step(0.99999, texture2D(tDepth, vUv).x);
  #endif
  gl_FragColor = vec4(min(c, vec3(16.0)) * m, 1.0);
}`;
const RAYBLUR_FS = /* glsl */`
uniform sampler2D tSrc; uniform vec2 uLight; uniform float uDensity, uDecay, uWeight;
varying vec2 vUv;
void main(){
  vec2 uv = vUv; vec2 d = (uv - uLight) * uDensity / float(SAMPLES);
  vec3 sum = vec3(0.0); float ill = 1.0;
  for (int i = 0; i < SAMPLES; i++) { uv -= d; sum += texture2D(tSrc, uv).rgb * ill * uWeight; ill *= uDecay; }
  gl_FragColor = vec4(sum, 1.0);
}`;

const UBER_FS = /* glsl */`
#include <packing>
#include <tonemapping_pars_fragment>
uniform sampler2D tScene; uniform sampler2D tDepth; uniform sampler2D tDof; uniform sampler2D tBloom; uniform sampler2D tGlow; uniform sampler2D tRays;
uniform vec2 uRes; uniform float uAspect; uniform float uExposure;
uniform float uNear, uFar, uFocus, uAperture, uMaxBlur, uBand;
uniform float uBloomStrength; uniform vec3 uBloomTint;
uniform float uGlowAmount; uniform vec3 uGlowTint;
uniform float uRayStrength; uniform vec3 uRayTint;
uniform vec3 uLensK; // k1, k2, zoom
uniform float uChroma; // uv units at corner
uniform vec2 uBlurDir; uniform float uBlurZoom; uniform vec2 uBlurCenter;
uniform mat3 uWB;
uniform vec3 uLift, uGamma, uGain, uOffset, uOutBlack, uOutWhite, uShadowsTint, uHighlightsTint;
uniform vec4 uGradeA; // contrast, pivot, saturation, vibrance
uniform float uBalance;
uniform vec4 uVig; // amount, size, softness, roundness
uniform vec3 uVigColor; uniform vec2 uVigCenter;
uniform vec4 uFade; uniform vec4 uFlash; // rgb, amount
uniform vec3 uGrain; // amount, size, colored
uniform float uFrame;
varying vec2 vUv;

float luma(vec3 c){ return dot(c, vec3(0.2126, 0.7152, 0.0722)); }
float hash12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
vec3 hash32(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * vec3(.1031, .1030, .0973)); p3 += dot(p3, p3.yxz + 33.33); return fract((p3.xxy + p3.yzz) * p3.zyx); }

vec3 sceneAt(vec2 uv){
  vec3 c = texture2D(tScene, uv).rgb;
  #ifdef USE_DOF
  float z = -perspectiveDepthToViewZ(texture2D(tDepth, uv).x, uNear, uFar);
  float d = 1.0 - uFocus / z; d = max(abs(d) - uBand, 0.0) * uAperture;
  vec4 b = texture2D(tDof, uv);
  float a = smoothstep(0.6, 2.0, max(min(d, uMaxBlur), b.a * 2.0));
  c = mix(c, b.rgb, a);
  #endif
  return c;
}
vec3 sceneBlur(vec2 uv){
  #ifdef USE_BLUR
  vec3 s = vec3(0.0);
  for (int i = 0; i < BLUR_SAMPLES; i++) {
    float f = (float(i) / float(BLUR_SAMPLES - 1)) - 0.5;
    vec2 p = uv + uBlurDir * f + (uv - uBlurCenter) * uBlurZoom * f;
    s += sceneAt(p);
  }
  return s / float(BLUR_SAMPLES);
  #else
  return sceneAt(uv);
  #endif
}
vec3 softLight(vec3 a, vec3 b){ return mix(2.0*a*b + a*a*(1.0-2.0*b), sqrt(a)*(2.0*b-1.0) + 2.0*a*(1.0-b), step(0.5, b)); }
vec3 toneMap(vec3 c){
  c *= uExposure;
  #if defined(TM_ACES)
  return ACESFilmicToneMapping(c);
  #elif defined(TM_AGX)
  return AgXToneMapping(c);
  #elif defined(TM_NEUTRAL)
  return NeutralToneMapping(c);
  #elif defined(TM_REINHARD)
  return ReinhardToneMapping(c);
  #elif defined(TM_CINEON)
  return CineonToneMapping(c);
  #elif defined(TM_LINEAR)
  return clamp(c, 0.0, 1.0);
  #else
  return c;
  #endif
}
vec3 toDisplay(vec3 c){ c = clamp(c, 0.0, 1.0); return mix(c * 12.92, 1.055 * pow(c, vec3(1.0/2.4)) - 0.055, step(0.0031308, c)); }

void main(){
  vec2 uv = vUv;
  vec2 cuv = uv - 0.5; vec2 asp = vec2(uAspect, 1.0);
  #ifdef USE_LENS
  { vec2 q = cuv * asp; float r2 = dot(q, q) / dot(asp * 0.5, asp * 0.5); float f = 1.0 + uLensK.x * r2 + uLensK.y * r2 * r2; cuv = cuv * f / uLensK.z; uv = cuv + 0.5; }
  #endif
  vec3 col;
  #ifdef USE_CHROMA
  { vec2 dir = cuv * 2.0; col.r = sceneBlur(uv - dir * uChroma).r; col.g = sceneBlur(uv).g; col.b = sceneBlur(uv + dir * uChroma).b; }
  #else
  col = sceneBlur(uv);
  #endif
  #ifdef USE_BLOOM
  col += texture2D(tBloom, uv).rgb * uBloomStrength * uBloomTint;
  #endif
  #ifdef USE_RAYS
  col += texture2D(tRays, uv).rgb * uRayStrength * uRayTint;
  #endif
  #ifdef USE_GLOW
  vec3 g = texture2D(tGlow, uv).rgb * uGlowTint;
  #if GLOW_MODE == 1
  col += g * uGlowAmount;
  #elif GLOW_MODE == 2
  col = mix(col, g, uGlowAmount);
  #endif
  #endif
  col = max(uWB * col, vec3(0.0));
  col = toneMap(col);
  col = toDisplay(col);
  #if defined(USE_GLOW) && GLOW_MODE == 0
  { vec3 gd = toDisplay(toneMap(g)); col = 1.0 - (1.0 - col) * (1.0 - gd * uGlowAmount); }
  #endif
  #ifdef USE_GRADE
  col = uGain * (col + uLift * (1.0 - col)) + uOffset;
  col = pow(max(col, vec3(0.0)), 1.0 / uGamma);
  col = (col - uGradeA.y) * uGradeA.x + uGradeA.y;
  float l = luma(col);
  col = mix(vec3(l), col, uGradeA.z);
  if (uGradeA.w != 0.0) { float mx = max(col.r, max(col.g, col.b)), mn = min(col.r, min(col.g, col.b)); float sat = mx - mn; col = mix(vec3(l), col, 1.0 + uGradeA.w * (1.0 - sat)); }
  col = clamp(col, 0.0, 1.0);
  { float t = clamp(luma(col) + uBalance, 0.0, 1.0); col = softLight(col, mix(vec3(0.5), uShadowsTint, 1.0 - t)); col = softLight(col, mix(vec3(0.5), uHighlightsTint, t)); }
  col = uOutBlack + col * (uOutWhite - uOutBlack);
  #endif
  #ifdef USE_VIGNETTE
  { vec2 d = (vUv - uVigCenter) * mix(vec2(1.0), asp, uVig.w) * 2.0; float r = length(d) / length(mix(vec2(1.0), asp, uVig.w));
    float v = smoothstep(uVig.y, uVig.y + uVig.z, r); col = mix(col, uVigColor, v * uVig.x); }
  #endif
  col = mix(col, uFade.rgb, uFade.a);
  col = 1.0 - (1.0 - col) * (1.0 - uFlash.rgb * uFlash.a);
  #ifdef USE_GRAIN
  { vec2 p = floor(gl_FragCoord.xy / uGrain.y); vec3 n = hash32(p + fract(uFrame * 0.6180339) * 1000.0) - 0.5; n = mix(vec3(n.r), n, uGrain.z);
    float lw = 1.0 - pow(abs(luma(col) - 0.5) * 2.0, 2.0) * 0.6; col += n * uGrain.x * 2.0 * lw; }
  #endif
  #ifdef USE_DITHER
  col += (hash12(gl_FragCoord.xy + uFrame * 3.17) - 0.5) / 255.0;
  #endif
  gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}`;

// ---------------- the stack ----------------
export class Post {
  constructor(renderer, width, height) {
    this.r = renderer; this.W = width; this.H = height;
    this.params = defaultPostParams();
    this.quad = new FullScreenQuad(null);
    this.timings = null; // set by profile mode
    this.frame = 0;
    this._rts = {};
    const mk = (fs, uniforms, defines = {}) => new THREE.ShaderMaterial({ vertexShader: VS, fragmentShader: fs, uniforms, defines, depthTest: false, depthWrite: false, toneMapped: false });
    this.mDown = mk(DOWN_FS, { tSrc: { value: null }, uTexel: { value: new THREE.Vector2() }, uThresh: { value: new THREE.Vector4() } });
    this.mUp = mk(UP_FS, { tLow: { value: null }, tHigh: { value: null }, uTexel: { value: new THREE.Vector2() }, uScatter: { value: 0.6 } });
    this.mDof = mk(DOF_FS, { tColor: { value: null }, tDepth: { value: null }, uPx: { value: new THREE.Vector2() }, uNear: { value: 0.1 }, uFar: { value: 100 }, uFocus: { value: 5 }, uAperture: { value: 10 }, uMaxBlur: { value: 12 }, uBand: { value: 0 } }, { RAD_SCALE: '1.0', MAX_TAPS: 64 });
    this.mRayMask = mk(RAYMASK_FS, { tColor: { value: null }, tDepth: { value: null }, uThreshold: { value: 1 }, uSkyOnly: { value: 0 } });
    this.mRayBlur = mk(RAYBLUR_FS, { tSrc: { value: null }, uLight: { value: new THREE.Vector2(0.5, 0.5) }, uDensity: { value: 0.9 }, uDecay: { value: 0.96 }, uWeight: { value: 0.3 } }, { SAMPLES: 40 });
    const U = (v) => ({ value: v });
    this.mUber = mk(UBER_FS, {
      tScene: U(null), tDepth: U(null), tDof: U(null), tBloom: U(null), tGlow: U(null), tRays: U(null),
      uRes: U(new THREE.Vector2(width, height)), uAspect: U(width / height), uExposure: U(1),
      uNear: U(0.1), uFar: U(100), uFocus: U(5), uAperture: U(10), uMaxBlur: U(20), uBand: U(0),
      uBloomStrength: U(0), uBloomTint: U(new THREE.Vector3(1, 1, 1)), uGlowAmount: U(0), uGlowTint: U(new THREE.Vector3(1, 1, 1)),
      uRayStrength: U(0), uRayTint: U(new THREE.Vector3(1, 1, 1)), uLensK: U(new THREE.Vector3(0, 0, 1)), uChroma: U(0),
      uBlurDir: U(new THREE.Vector2()), uBlurZoom: U(0), uBlurCenter: U(new THREE.Vector2(0.5, 0.5)), uWB: U(new THREE.Matrix3()),
      uLift: U(new THREE.Vector3()), uGamma: U(new THREE.Vector3(1, 1, 1)), uGain: U(new THREE.Vector3(1, 1, 1)), uOffset: U(new THREE.Vector3()),
      uOutBlack: U(new THREE.Vector3()), uOutWhite: U(new THREE.Vector3(1, 1, 1)), uShadowsTint: U(new THREE.Vector3(0.5, 0.5, 0.5)), uHighlightsTint: U(new THREE.Vector3(0.5, 0.5, 0.5)),
      uGradeA: U(new THREE.Vector4(1, 0.45, 1, 0)), uBalance: U(0), uVig: U(new THREE.Vector4()), uVigColor: U(new THREE.Vector3()), uVigCenter: U(new THREE.Vector2(0.5, 0.5)),
      uFade: U(new THREE.Vector4()), uFlash: U(new THREE.Vector4()), uGrain: U(new THREE.Vector3()), uFrame: U(0),
    });
    const fx = FXAAShader;
    this.mFxaa = new THREE.ShaderMaterial({ uniforms: THREE.UniformsUtils.clone(fx.uniforms), vertexShader: fx.vertexShader, fragmentShader: fx.fragmentShader, depthTest: false, depthWrite: false, toneMapped: false });
    this.mFxaa.uniforms.resolution.value.set(1 / width, 1 / height);
    this.mCopy = mk(/* glsl */`uniform sampler2D tSrc; varying vec2 vUv; void main(){ gl_FragColor = texture2D(tSrc, vUv); }`, { tSrc: U(null) });
  }

  reset() { this.params = defaultPostParams(); return this; }
  set(p) { deepMerge(this.params, p); return this; }

  // ---- render targets (lazily (re)created) ----
  _rt(key, w, h, opts) {
    const sig = JSON.stringify([w, h, opts.type, opts.samples || 0, !!opts.depth]);
    let rt = this._rts[key];
    if (rt && rt._sig === sig) return rt;
    if (rt) { rt.depthTexture?.dispose(); rt.dispose(); }
    rt = new THREE.WebGLRenderTarget(w, h, {
      type: opts.type ?? THREE.HalfFloatType, format: THREE.RGBAFormat, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter,
      depthBuffer: !!opts.depthBuffer || !!opts.depth, stencilBuffer: false, samples: opts.samples || 0, generateMipmaps: false, colorSpace: THREE.LinearSRGBColorSpace,
    });
    if (opts.depth) { rt.depthTexture = new THREE.DepthTexture(w, h, THREE.UnsignedIntType); rt.depthTexture.minFilter = rt.depthTexture.magFilter = THREE.NearestFilter; }
    rt.texture.wrapS = rt.texture.wrapT = THREE.ClampToEdgeWrapping;
    rt._sig = sig; this._rts[key] = rt; return rt;
  }
  _pass(material, target) { this.quad.material = material; this.r.setRenderTarget(target); this.quad.render(this.r); }
  _t(label) { if (!this.timings) return; const gl = this.r.getContext(); gl.finish(); const now = performance.now(); this.timings[label] = (this.timings[label] || 0) + (now - this._last); this._last = now; }

  // Downsample/upsample pyramid from `src` (full-res HDR). Returns the half-res result texture.
  _pyramid(name, src, p) {
    const W = this.W, H = this.H; const levels = Math.max(1, Math.min(8, p.levels | 0));
    const downs = [];
    let w = W, h = H, input = src;
    for (let i = 0; i < levels; i++) {
      const iw = w, ih = h; w = Math.max(1, Math.ceil(w / 2)); h = Math.max(1, Math.ceil(h / 2));
      const rt = this._rt(`${name}_d${i}`, w, h, {});
      const m = this.mDown; m.uniforms.tSrc.value = input; m.uniforms.uTexel.value.set(0.5 / iw * 2, 0.5 / ih * 2);
      m.uniforms.uThresh.value.set(p.threshold || 0, p.knee ?? 0.5, i === 0 && (p.threshold > 0) ? 1 : 0, i === 0 ? 1 : 0);
      this._pass(m, rt); downs.push(rt); input = rt.texture;
    }
    let low = downs[levels - 1].texture;
    for (let i = levels - 2; i >= 0; i--) {
      const hi = downs[i]; const rt = this._rt(`${name}_u${i}`, hi.width, hi.height, {});
      const m = this.mUp; m.uniforms.tLow.value = low; m.uniforms.tHigh.value = hi.texture; m.uniforms.uScatter.value = Math.min(0.97, Math.max(0.05, p.radius));
      m.uniforms.uTexel.value.set(1 / hi.width, 1 / hi.height);
      this._pass(m, rt); low = rt.texture;
    }
    return low;
  }

  // Render `scene` with `camera` through the stack to `target` (null = canvas).
  render(scene, camera, { focusDistance = 5, target = null, frame = 0 } = {}) {
    const r = this.r, P = this.params, W = this.W, H = this.H;
    if (this.timings) { r.getContext().finish(); this._last = performance.now(); }
    const aa = P.aa || 'none'; const msaa = aa.includes('msaa') ? P.msaaSamples | 0 : 0;
    const needDepth = !!(P.dof.enabled || (P.godrays.enabled && P.godrays.skyOnly));
    const sceneRT = this._rt('scene', W, H, { samples: msaa, depth: needDepth, depthBuffer: true });
    const prevAuto = r.autoClear; r.autoClear = true;
    r.setRenderTarget(sceneRT); r.render(scene, camera);
    this._t('scene');
    const u = this.mUber.uniforms; const defs = {};
    u.tScene.value = sceneRT.texture; u.tDepth.value = sceneRT.depthTexture || null;
    u.uNear.value = camera.near; u.uFar.value = camera.far;

    // DOF
    if (P.dof.enabled) {
      const d = P.dof; const focus = d.focus === 'auto' || d.focus == null ? focusDistance : d.focus;
      const k = W / 1080; const hw = Math.ceil(W / 2), hh = Math.ceil(H / 2);
      const rt = this._rt('dof', hw, hh, {});
      const m = this.mDof; const rad = d.quality === 'high' ? '0.9' : d.quality === 'low' ? '2.0' : '1.35';
      if (m.defines.RAD_SCALE !== rad) { m.defines.RAD_SCALE = rad; m.needsUpdate = true; }
      m.uniforms.tColor.value = sceneRT.texture; m.uniforms.tDepth.value = sceneRT.depthTexture;
      m.uniforms.uPx.value.set(2 / W, 2 / H); // gather radius in half-res px
      m.uniforms.uNear.value = camera.near; m.uniforms.uFar.value = camera.far; m.uniforms.uFocus.value = focus;
      m.uniforms.uAperture.value = d.aperture * k / 2; m.uniforms.uMaxBlur.value = d.maxBlur * k / 2;
      const band = d.range > 0 ? Math.abs(1 - focus / (focus + d.range)) : 0; m.uniforms.uBand.value = band;
      this._pass(m, rt);
      u.tDof.value = rt.texture; u.uFocus.value = focus; u.uAperture.value = d.aperture * k; u.uMaxBlur.value = d.maxBlur * k; u.uBand.value = band;
      defs.USE_DOF = 1; this._t('dof');
    }
    // bloom
    if (P.bloom.enabled && P.bloom.strength > 0) {
      u.tBloom.value = this._pyramid('bloom', sceneRT.texture, P.bloom); u.uBloomStrength.value = P.bloom.strength;
      const c = lin(P.bloom.tint); u.uBloomTint.value.set(c.r, c.g, c.b); defs.USE_BLOOM = 1; this._t('bloom');
    }
    // glow / diffusion
    if (P.glow.enabled && P.glow.amount > 0) {
      u.tGlow.value = this._pyramid('glow', sceneRT.texture, P.glow); u.uGlowAmount.value = P.glow.amount;
      const c = lin(P.glow.tint); u.uGlowTint.value.set(c.r, c.g, c.b);
      defs.USE_GLOW = 1; defs.GLOW_MODE = P.glow.mode === 'add' ? 1 : P.glow.mode === 'mix' ? 2 : 0; this._t('glow');
    }
    // god rays
    if (P.godrays.enabled && P.godrays.strength > 0) {
      const g = P.godrays; const qw = Math.ceil(W / 4), qh = Math.ceil(H / 4);
      let lu = 0.5, lv = 0.5, visible = 1;
      if (g.source && g.source.screen) { lu = g.source.screen[0]; lv = g.source.screen[1]; }
      else {
        const v = new THREE.Vector3(); if (g.source.isObject3D) g.source.getWorldPosition(v); else if (Array.isArray(g.source)) v.set(...g.source); else v.copy(g.source);
        v.project(camera); lu = v.x * 0.5 + 0.5; lv = v.y * 0.5 + 0.5; if (v.z > 1) visible = 0;
      }
      const mask = this._rt('rays_m', qw, qh, {}), a = this._rt('rays_a', qw, qh, {}), b = this._rt('rays_b', qw, qh, {});
      const mm = this.mRayMask; mm.uniforms.tColor.value = sceneRT.texture; mm.uniforms.tDepth.value = sceneRT.depthTexture; mm.uniforms.uThreshold.value = g.threshold; mm.uniforms.uSkyOnly.value = g.skyOnly ? 1 : 0;
      const wantDepth = g.skyOnly && sceneRT.depthTexture ? 1 : 0; if ((mm.defines.USE_DEPTH ? 1 : 0) !== wantDepth) { if (wantDepth) mm.defines.USE_DEPTH = 1; else delete mm.defines.USE_DEPTH; mm.needsUpdate = true; }
      this._pass(mm, mask);
      const mb = this.mRayBlur; const n = Math.max(8, Math.min(96, g.samples | 0)); if (mb.defines.SAMPLES !== n) { mb.defines.SAMPLES = n; mb.needsUpdate = true; }
      // pass 1: long streaks (energy-normalised, x weight*8); pass 2: fills the gaps between pass-1 taps
      const norm = (1 - Math.pow(g.decay, n)) / (1 - g.decay + 1e-6);
      mb.uniforms.uLight.value.set(lu, lv); mb.uniforms.uDecay.value = g.decay; mb.uniforms.uWeight.value = (g.weight * 8) / norm;
      mb.uniforms.tSrc.value = mask.texture; mb.uniforms.uDensity.value = g.density; this._pass(mb, a);
      mb.uniforms.tSrc.value = a.texture; mb.uniforms.uDensity.value = g.density / n; mb.uniforms.uDecay.value = 1; mb.uniforms.uWeight.value = 1 / n; this._pass(mb, b);
      u.tRays.value = b.texture; u.uRayStrength.value = g.strength * visible; const c = lin(g.tint); u.uRayTint.value.set(c.r, c.g, c.b);
      defs.USE_RAYS = 1; this._t('godrays');
    }
    // uber uniforms
    const tm = { aces: 'TM_ACES', agx: 'TM_AGX', neutral: 'TM_NEUTRAL', reinhard: 'TM_REINHARD', cineon: 'TM_CINEON', linear: 'TM_LINEAR' }[P.toneMapping];
    if (tm) defs[tm] = 1;
    u.uExposure.value = P.exposure;
    const k = W / 1080;
    if (P.lens.enabled) { defs.USE_LENS = 1; u.uLensK.value.set(P.lens.k1, P.lens.k2, P.lens.zoom || 1); }
    if (P.chroma.enabled && P.chroma.amount) { defs.USE_CHROMA = 1; u.uChroma.value = (P.chroma.amount * k) / Math.hypot(W, H) * 0.5; }
    if (P.blur.enabled && (P.blur.dir[0] || P.blur.dir[1] || P.blur.zoom)) {
      defs.USE_BLUR = 1; defs.BLUR_SAMPLES = Math.max(2, P.blur.samples | 0);
      u.uBlurDir.value.set((P.blur.dir[0] * k) / W, (-P.blur.dir[1] * k) / H); u.uBlurZoom.value = P.blur.zoom; u.uBlurCenter.value.set(P.blur.center[0], 1 - P.blur.center[1]);
    }
    const G = P.grade;
    u.uWB.value = G.enabled && (G.temperature || G.tint) ? whiteBalance(G.temperature, G.tint) : u.uWB.value.identity();
    if (G.enabled) {
      defs.USE_GRADE = 1;
      u.uLift.value.copy(vec3(rgb(G.lift))); u.uGamma.value.copy(vec3(rgb(G.gamma))); u.uGain.value.copy(vec3(rgb(G.gain))); u.uOffset.value.copy(vec3(rgb(G.offset)));
      u.uGradeA.value.set(G.contrast, G.pivot, G.saturation, G.vibrance || 0);
      const st = rgb(G.shadows), ht = rgb(G.highlights);
      u.uShadowsTint.value.set(0.5 + (st[0] - 0.5) * G.shadowsAmount, 0.5 + (st[1] - 0.5) * G.shadowsAmount, 0.5 + (st[2] - 0.5) * G.shadowsAmount);
      u.uHighlightsTint.value.set(0.5 + (ht[0] - 0.5) * G.highlightsAmount, 0.5 + (ht[1] - 0.5) * G.highlightsAmount, 0.5 + (ht[2] - 0.5) * G.highlightsAmount);
      u.uBalance.value = G.balance; u.uOutBlack.value.copy(vec3(rgb(G.outBlack))); u.uOutWhite.value.copy(vec3(rgb(G.outWhite)));
    }
    if (P.vignette.enabled && P.vignette.amount > 0) {
      const v = P.vignette; defs.USE_VIGNETTE = 1; u.uVig.value.set(v.amount, v.size, v.softness, v.roundness);
      const c = rgb(v.color); u.uVigColor.value.set(c[0], c[1], c[2]); u.uVigCenter.value.set(v.center[0], 1 - v.center[1]);
    }
    { const c = rgb(P.fade.color); u.uFade.value.set(c[0], c[1], c[2], P.fade.amount || 0); }
    { const c = rgb(P.flash.color); u.uFlash.value.set(c[0], c[1], c[2], P.flash.amount || 0); }
    if (P.grain.enabled && P.grain.amount > 0) { defs.USE_GRAIN = 1; u.uGrain.value.set(P.grain.amount, Math.max(1, P.grain.size * k), P.grain.colored); }
    if (P.dither) defs.USE_DITHER = 1;
    u.uFrame.value = frame % 100000;
    // recompile only when the feature set changes
    const sig = JSON.stringify(defs);
    if (sig !== this._uberSig) { this.mUber.defines = defs; this.mUber.needsUpdate = true; this._uberSig = sig; }

    const extras = (P.extra || []).filter((e) => e && e.enabled !== false && e.material);
    const fxaa = aa.includes('fxaa');
    const chain = [...(fxaa ? [{ material: this.mFxaa, fxaa: true }] : []), ...extras];
    if (!chain.length) { this._pass(this.mUber, target); this._t('uber'); }
    else {
      let src = this._rt('ldrA', W, H, { type: THREE.UnsignedByteType });
      this._pass(this.mUber, src); this._t('uber');
      chain.forEach((e, i) => {
        const last = i === chain.length - 1; const dst = last ? target : this._rt(i % 2 ? 'ldrA' : 'ldrB', W, H, { type: THREE.UnsignedByteType });
        const m = e.material; if (m.uniforms.tDiffuse) m.uniforms.tDiffuse.value = src.texture; if (m.uniforms.uFrame) m.uniforms.uFrame.value = frame;
        this._pass(m, dst); src = dst;
      });
      this._t('ldr');
    }
    r.autoClear = prevAuto;
  }

  dispose() { for (const k in this._rts) { this._rts[k].depthTexture?.dispose(); this._rts[k].dispose(); } this._rts = {}; }
}
