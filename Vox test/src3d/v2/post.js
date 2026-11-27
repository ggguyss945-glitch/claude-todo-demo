// Post-processing: bloom + a "look" pass that reproduces the original's grade
// (crushed blacks, saturation, sharpening halos, chromatic fringe, vignette)
// and the CCTV/monitor treatments.
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { SMAAPass } from 'three/addons/postprocessing/SMAAPass.js';

const LookShader = {
  uniforms: {
    tDiffuse: { value: null },
    res: { value: new THREE.Vector2(1440, 2560) },
    uTime: { value: 0 },
    uCA: { value: 1.0 },
    uSharpen: { value: 0.55 },
    uSharpRadius: { value: 1.6 },
    uVignette: { value: 0.45 },
    uContrast: { value: 1.12 },
    uSat: { value: 1.12 },
    uLift: { value: -0.02 },
    uGrain: { value: 0.03 },
    uCCTV: { value: 0.0 },
    uScreen: { value: 0.0 },
    uScreenCell: { value: 9.0 },
    uFade: { value: 0.0 },
    uWarm: { value: 0.0 },
  },
  vertexShader: `varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
  fragmentShader: `
    uniform sampler2D tDiffuse; uniform vec2 res; uniform float uTime, uCA, uSharpen, uSharpRadius, uVignette, uContrast, uSat, uLift, uGrain, uCCTV, uScreen, uScreenCell, uFade, uWarm;
    varying vec2 vUv;
    float h12(vec2 p){ vec3 p3=fract(vec3(p.xyx)*.1031); p3+=dot(p3,p3.yzx+33.33); return fract((p3.x+p3.y)*p3.z); }
    vec3 samp(vec2 uv){
      vec2 d = (uv-0.5);
      float k = uCA * 0.0022 * (0.4 + dot(d,d)*3.0);
      vec3 c;
      c.r = texture2D(tDiffuse, uv + d*k*1.0).r;
      c.g = texture2D(tDiffuse, uv).g;
      c.b = texture2D(tDiffuse, uv - d*k*1.2).b;
      return c;
    }
    void main(){
      vec2 uv = vUv;
      vec2 px = 1.0/res;
      if (uCCTV > 0.0) {
        // slight horizontal line jitter like a weak analogue feed
        float line = floor(uv.y*res.y/3.0);
        uv.x += (h12(vec2(line, floor(uTime*30.0))) - 0.5) * 0.0012 * uCCTV;
      }
      vec3 c = samp(uv);
      // unsharp mask (gives the crisp "upscaled game capture" halos)
      vec2 r = px * uSharpRadius;
      vec3 blur = (samp(uv+vec2(r.x,0.0))+samp(uv-vec2(r.x,0.0))+samp(uv+vec2(0.0,r.y))+samp(uv-vec2(0.0,r.y)))*0.25;
      c += (c - blur) * uSharpen;
      // grade
      c = max(c + uLift, 0.0);
      c = (c - 0.5) * uContrast + 0.5;
      float l = dot(c, vec3(0.2126,0.7152,0.0722));
      c = mix(vec3(l), c, uSat);
      c *= vec3(1.0 + uWarm*0.06, 1.0, 1.0 - uWarm*0.06);
      if (uCCTV > 0.0) {
        // aperture-grille stripes + noise + tint
        float col = mod(gl_FragCoord.x, 6.0);
        vec3 mask = col < 2.0 ? vec3(1.15,0.85,0.85) : (col < 4.0 ? vec3(0.85,1.15,0.85) : vec3(0.85,0.85,1.15));
        float stripe = 0.82 + 0.18*step(1.0, mod(gl_FragCoord.x, 3.0));
        vec3 cc = c * mask * stripe;
        float n = h12(gl_FragCoord.xy + fract(uTime*7.13)*100.0) - 0.5;
        cc += n * 0.10;
        cc = mix(cc, cc*vec3(0.92,1.05,1.0), 0.5);
        cc = (cc-0.5)*1.08+0.52;
        c = mix(c, cc, uCCTV);
      }
      if (uScreen > 0.0) {
        vec2 cell = mod(gl_FragCoord.xy, vec2(uScreenCell, uScreenCell*3.0));
        float sub = floor(cell.x / (uScreenCell/3.0));
        vec3 m = sub < 1.0 ? vec3(1.6,0.5,0.5) : (sub < 2.0 ? vec3(0.5,1.6,0.5) : vec3(0.5,0.5,1.6));
        float gap = step(uScreenCell*2.6, cell.y) + step(uScreenCell*0.92/3.0*3.0, cell.x);
        vec3 sc = c * m * (1.0 - 0.7*clamp(gap,0.0,1.0));
        c = mix(c, sc, uScreen);
      }
      // vignette
      vec2 d = vUv - 0.5;
      float v = smoothstep(0.85, 0.2, length(d*vec2(1.0, 0.75)));
      c *= mix(1.0, v, uVignette);
      // film grain
      c += (h12(gl_FragCoord.xy*1.37 + fract(uTime*3.7)*311.0) - 0.5) * uGrain;
      c = mix(c, vec3(0.0), uFade);
      gl_FragColor = vec4(clamp(c,0.0,1.0), 1.0);
    }`,
};

export function makeComposer(renderer, scene, camera, W, H, Q) {
  const rt = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: Q.msaa });
  const composer = new EffectComposer(renderer, rt);
  composer.setPixelRatio(1);
  composer.setSize(W, H);
  const rp = new RenderPass(scene, camera);
  composer.addPass(rp);
  const bloom = new UnrealBloomPass(new THREE.Vector2(W, H), 0.6, 0.38, 0.9);
  composer.addPass(bloom);
  composer.addPass(new OutputPass());
  if (Q.smaa) composer.addPass(new SMAAPass(W, H));
  const look = new ShaderPass(LookShader);
  look.uniforms.res.value.set(W, H);
  composer.addPass(look);
  return { composer, renderPass: rp, bloom, look };
}
