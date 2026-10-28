// Post-processing for the toon look:
//   normal/depth pre-pass -> line-art edges -> depth of field -> bloom -> tone map -> grade
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { Pass, FullScreenQuad } from 'three/addons/postprocessing/Pass.js';
import { LAYER } from './toon.js';

const QUAD_VS = `varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }`;
const LIN = `
  uniform float near, far;
  float linZ(float d){ float z = d*2.0-1.0; return 2.0*near*far/(far+near - z*(far-near)); }`;

// line art from inverse-depth second derivative (silhouettes, steps) and normal changes (creases)
const EdgeShader = {
  uniforms: {
    tDiffuse: { value: null }, tNormal: { value: null }, tDepth: { value: null }, res: { value: new THREE.Vector2(1440, 2560) },
    near: { value: 0.05 }, far: { value: 600 }, uWidth: { value: 1.25 }, uStrength: { value: 0.88 }, uDepthK: { value: 0.012 },
    uNormK: { value: 0.22 }, uLine: { value: new THREE.Color('#1c130d') }, uFar: { value: 400 },
  },
  vertexShader: QUAD_VS,
  fragmentShader: `
    uniform sampler2D tDiffuse, tNormal, tDepth; uniform vec2 res; uniform float uWidth, uStrength, uDepthK, uNormK, uFar; uniform vec3 uLine;
    varying vec2 vUv;
    ${LIN}
    float iz(vec2 uv){ return 1.0 / linZ(texture2D(tDepth, uv).x); }
    vec3 nn(vec2 uv){ return texture2D(tNormal, uv).xyz * 2.0 - 1.0; }
    void main(){
      vec2 px = uWidth / res;
      float c = iz(vUv);
      float l = iz(vUv - vec2(px.x, 0.0)), r = iz(vUv + vec2(px.x, 0.0));
      float d = iz(vUv - vec2(0.0, px.y)), u = iz(vUv + vec2(0.0, px.y));
      // planes have zero second derivative of 1/z in screen space, so only real steps light up
      float lap = (abs(l + r - 2.0*c) + abs(u + d - 2.0*c)) / max(c, 1e-6);
      float e = smoothstep(uDepthK, uDepthK * 2.5, lap);
      vec3 n0 = nn(vUv);
      float nd = max(max(1.0 - dot(n0, nn(vUv + vec2(px.x, 0.0))), 1.0 - dot(n0, nn(vUv - vec2(px.x, 0.0)))),
                     max(1.0 - dot(n0, nn(vUv + vec2(0.0, px.y))), 1.0 - dot(n0, nn(vUv - vec2(0.0, px.y)))));
      e = max(e, smoothstep(uNormK, uNormK + 0.2, nd));
      float z = 1.0 / c;
      e *= 1.0 - smoothstep(uFar * 0.6, uFar, z);   // sky and far haze stay clean
      vec4 col = texture2D(tDiffuse, vUv);
      col.rgb = mix(col.rgb, uLine, e * uStrength);
      gl_FragColor = col;
    }`,
};

// depth of field: half-resolution scatter-as-gather blur, then a full-resolution blend by circle of confusion
class DofPass extends Pass {
  constructor(W, H) {
    super();
    this.half = new THREE.WebGLRenderTarget(Math.round(W / 2), Math.round(H / 2), { type: THREE.HalfFloatType });
    this.uniforms = {
      tDiffuse: { value: null }, tDepth: { value: null }, tBlur: { value: null }, res: { value: new THREE.Vector2(W, H) },
      near: { value: 0.05 }, far: { value: 600 }, uFocus: { value: 3.0 }, uAperture: { value: 0.0 }, uMaxPx: { value: 22.0 },
    };
    const COC = `
      uniform float uFocus, uAperture, uMaxPx;
      float coc(float z){ return clamp(uAperture * abs(1.0 - uFocus / z), 0.0, uMaxPx); }
      // nearest depth within ~6 px: outline shells (not in the depth buffer) take their subject's depth
      float nearZ(sampler2D dt, vec2 uv, vec2 rs){
        float z = linZ(texture2D(dt, uv).x);
        for (int k = 0; k < 8; k++) {
          float a = float(k) * 0.785398;
          z = min(z, linZ(texture2D(dt, uv + vec2(cos(a), sin(a)) * 6.0 / rs).x));
        }
        return z;
      }`;
    this.blurMat = new THREE.ShaderMaterial({
      uniforms: this.uniforms, vertexShader: QUAD_VS,
      fragmentShader: `
        uniform sampler2D tDiffuse, tDepth; uniform vec2 res; varying vec2 vUv;
        ${LIN} ${COC}
        void main(){
          float zc = nearZ(tDepth, vUv, res);
          float cc = coc(zc);
          vec3 acc = texture2D(tDiffuse, vUv).rgb; float ws = 1.0;
          const int N = 44;
          float R = max(cc, 1.0);
          for (int i = 0; i < N; i++) {
            float fi = float(i) + 0.5;
            float rr = sqrt(fi / float(N)) * uMaxPx;
            float a = fi * 2.39996;
            vec2 o = vec2(cos(a), sin(a)) * rr / res;
            float zs = linZ(texture2D(tDepth, vUv + o).x);
            float cs = coc(zs);
            // a neighbour contributes if its own blur disc reaches us; nearer blurry things may spill over sharp ones
            float reach = smoothstep(rr - 1.5, rr + 1.5, cs);
            float behind = zs > zc + 0.05 ? min(1.0, cc / max(rr, 1.0)) : 1.0;
            float w = reach * behind;
            acc += texture2D(tDiffuse, vUv + o).rgb * w; ws += w;
          }
          gl_FragColor = vec4(acc / ws, cc);
        }`,
    });
    this.mixMat = new THREE.ShaderMaterial({
      uniforms: this.uniforms, vertexShader: QUAD_VS,
      fragmentShader: `
        uniform sampler2D tDiffuse, tDepth, tBlur; uniform vec2 res; varying vec2 vUv;
        ${LIN} ${COC}
        void main(){
          vec4 s = texture2D(tDiffuse, vUv);
          vec4 b = texture2D(tBlur, vUv);
          float cc = coc(nearZ(tDepth, vUv, res));
          gl_FragColor = vec4(mix(s.rgb, b.rgb, smoothstep(0.6, 2.2, cc)), 1.0);
        }`,
    });
    this.q1 = new FullScreenQuad(this.blurMat);
    this.q2 = new FullScreenQuad(this.mixMat);
  }
  render(renderer, writeBuffer, readBuffer) {
    if (this.uniforms.uAperture.value <= 0.01) { // nothing to blur: copy through
      this.uniforms.tDiffuse.value = readBuffer.texture;
      this.uniforms.tBlur.value = readBuffer.texture;
      this.uniforms.uAperture.value = 0;
    } else {
      this.uniforms.tDiffuse.value = readBuffer.texture;
      renderer.setRenderTarget(this.half); this.q1.render(renderer);
      this.uniforms.tBlur.value = this.half.texture;
    }
    renderer.setRenderTarget(this.renderToScreen ? null : writeBuffer);
    this.q2.render(renderer);
  }
}

// storybook grade: split-toned shadows/highlights, contrast, saturation, vignette, grain, fade
const LookShader = {
  uniforms: {
    tDiffuse: { value: null }, res: { value: new THREE.Vector2(1440, 2560) }, uTime: { value: 0 },
    uContrast: { value: 1.06 }, uSat: { value: 1.12 }, uLift: { value: 0.0 }, uVignette: { value: 0.32 }, uGrain: { value: 0.014 },
    uShadow: { value: new THREE.Color(0.93, 0.92, 1.06) }, uHigh: { value: new THREE.Color(1.05, 1.0, 0.95) }, uFade: { value: 0 },
    uFadeColor: { value: new THREE.Color(0, 0, 0) }, uSharpen: { value: 0.28 },
  },
  vertexShader: QUAD_VS,
  fragmentShader: `
    uniform sampler2D tDiffuse; uniform vec2 res; uniform float uTime, uContrast, uSat, uLift, uVignette, uGrain, uFade, uSharpen;
    uniform vec3 uShadow, uHigh, uFadeColor; varying vec2 vUv;
    float h12(vec2 p){ vec3 p3=fract(vec3(p.xyx)*.1031); p3+=dot(p3,p3.yzx+33.33); return fract((p3.x+p3.y)*p3.z); }
    void main(){
      vec2 px = 1.0 / res;
      vec3 c = texture2D(tDiffuse, vUv).rgb;
      vec3 bl = (texture2D(tDiffuse, vUv + vec2(px.x,0.0)).rgb + texture2D(tDiffuse, vUv - vec2(px.x,0.0)).rgb +
                 texture2D(tDiffuse, vUv + vec2(0.0,px.y)).rgb + texture2D(tDiffuse, vUv - vec2(0.0,px.y)).rgb) * 0.25;
      c += (c - bl) * uSharpen;
      float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
      c *= mix(uShadow, uHigh, smoothstep(0.15, 0.8, l));
      c = max(c + uLift, 0.0);
      c = (c - 0.5) * uContrast + 0.5;
      l = dot(c, vec3(0.2126, 0.7152, 0.0722));
      c = mix(vec3(l), c, uSat);
      vec2 d = vUv - 0.5;
      float v = smoothstep(0.9, 0.25, length(d * vec2(1.0, 0.72)));
      c *= mix(1.0, v, uVignette);
      c += (h12(gl_FragCoord.xy * 1.37 + fract(uTime * 3.7) * 311.0) - 0.5) * uGrain;
      c = mix(c, uFadeColor, uFade);
      gl_FragColor = vec4(clamp(c, 0.0, 1.0), 1.0);
    }`,
};

export function makePipeline(renderer, scene, camera, W, H, Q) {
  // normal + depth of the solid world (no hulls, no effects)
  const nd = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType });
  nd.depthTexture = new THREE.DepthTexture(W, H);
  nd.depthTexture.type = THREE.UnsignedIntType;
  const normalMat = new THREE.MeshNormalMaterial();
  const rt = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: Q.msaa });
  const composer = new EffectComposer(renderer, rt);
  composer.setPixelRatio(1);
  composer.setSize(W, H);
  composer.addPass(new RenderPass(scene, camera));
  const edges = new ShaderPass(EdgeShader);
  edges.uniforms.res.value.set(W, H);
  edges.uniforms.tNormal.value = nd.texture;
  edges.uniforms.tDepth.value = nd.depthTexture;
  composer.addPass(edges);
  const dof = new DofPass(W, H);
  dof.uniforms.tDepth.value = nd.depthTexture;
  composer.addPass(dof);
  const bloom = new UnrealBloomPass(new THREE.Vector2(W, H), 0.45, 0.55, 0.88);
  composer.addPass(bloom);
  composer.addPass(new OutputPass());
  const look = new ShaderPass(LookShader);
  look.uniforms.res.value.set(W, H);
  composer.addPass(look);

  function prepass() {
    const bg = scene.background, fog = scene.fog;
    scene.overrideMaterial = normalMat;
    scene.background = null;
    camera.layers.set(LAYER.MAIN);
    renderer.setRenderTarget(nd);
    renderer.setClearColor(0x8080ff, 1);
    renderer.clear();
    renderer.render(scene, camera);
    renderer.setRenderTarget(null);
    scene.overrideMaterial = null;
    scene.background = bg; scene.fog = fog;
    camera.layers.enableAll();
    for (const p of [edges.uniforms, dof.uniforms]) { p.near.value = camera.near; p.far.value = camera.far; }
  }
  return { composer, edges, dof, bloom, look, prepass };
}
