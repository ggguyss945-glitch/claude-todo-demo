// "Too Much Gold" renderer: toon-outlined 3D sets and round-head characters, rendered per frame
// as a pure function of time (chunks render out of order on several workers).
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { makePipeline } from './post.js';
import { RES } from './toon.js';
import { buildCaptions, drawCaption } from './overlay.js';
import { buildWorld } from './world.js';
import { SHOTS, findShot, initShots, resetFrame, finishFrame } from './shots.js';

const params = new URLSearchParams(location.search);
const W = parseInt(params.get('w') || '1440'), H = parseInt(params.get('h') || '2560');
const Q = { msaa: parseInt(params.get('msaa') || '4'), sub: params.get('sub') ? parseInt(params.get('sub')) : 3 };
const PROF = params.get('prof') === '1';
RES.set(W, H);

async function boot() {
  await Promise.all(['900 40px "Nunito"', '800 40px "Nunito"', '40px "Lilita One"', 'bold 40px "Liberation Sans"'].map((f) => document.fonts.load(f)));
  const words = await (await fetch('/script/words.json')).json();
  const mouth = await (await fetch('/script/mouth.json')).json().catch(() => ({}));
  const caps = buildCaptions(words);

  const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(1);
  renderer.setSize(W, H, false);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  document.body.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  const camera = new THREE.PerspectiveCamera(40, W / H, 0.05, 900);
  scene.add(camera);
  const world = buildWorld(scene, renderer);
  world.renderer = renderer; world.scene = scene; world.camera = camera; world.mouth = mouth; world.words = words;
  await initShots(world);
  const P = makePipeline(renderer, scene, camera, W, H, Q);
  const { composer, look, dof, bloom, edges, prepass } = P;

  const out = document.createElement('canvas');
  out.width = W; out.height = H;
  const og = out.getContext('2d', { willReadFrequently: true });

  // accumulation targets for motion blur and dissolves
  const accA = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType });
  const accB = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType });
  const quadCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const blendMat = new THREE.ShaderMaterial({
    uniforms: { tA: { value: null }, tB: { value: null }, k: { value: 1 }, uW: { value: 1 } },
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }',
    fragmentShader: 'uniform sampler2D tA, tB; uniform float k, uW; varying vec2 vUv; void main(){ gl_FragColor = vec4(mix(texture2D(tA, vUv).rgb, texture2D(tB, vUv).rgb, k) * uW, 1.0); }',
    depthTest: false, depthWrite: false,
  });
  const quadScene = new THREE.Scene();
  quadScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), blendMat));
  function quad(target, a, b, k, w, additive) {
    blendMat.uniforms.tA.value = a; blendMat.uniforms.tB.value = b || a; blendMat.uniforms.k.value = k; blendMat.uniforms.uW.value = w;
    blendMat.blending = additive ? THREE.AdditiveBlending : THREE.NoBlending; blendMat.transparent = !!additive;
    renderer.setRenderTarget(target);
    renderer.autoClear = !additive;
    renderer.render(quadScene, quadCam);
    renderer.autoClear = true;
  }

  function camAt(shot, t) { return shot.cam(Math.min(Math.max(t, shot.t0 - 1), shot.t1 + 1), world); }
  function camSpeed(shot, t) {
    const dt = 1 / 60;
    const a = camAt(shot, t - dt), b = camAt(shot, t + dt);
    const dp = Math.hypot(a.p[0] - b.p[0], a.p[1] - b.p[1], a.p[2] - b.p[2]);
    const da = new THREE.Vector3(...a.l).sub(new THREE.Vector3(...a.p)).normalize();
    const db = new THREE.Vector3(...b.l).sub(new THREE.Vector3(...b.p)).normalize();
    return dp * 3 + Math.acos(Math.min(1, da.dot(db))) + Math.abs((a.fov || 40) - (b.fov || 40)) * 0.01;
  }

  // stage the world for one shot at time t and run the post chain into composer.readBuffer
  function renderShot(shot, t) {
    resetFrame(world, t, shot);
    const S = world.sets[shot.set];
    for (const k in world.sets) world.sets[k].group.visible = k === shot.set;
    S.apply(t, shot);
    const c = camAt(shot, t);
    camera.position.set(...c.p);
    camera.up.set(0, 1, 0);
    camera.fov = c.fov || 40;
    camera.near = c.near || 0.05; camera.far = c.far || 900;
    camera.updateProjectionMatrix();
    camera.lookAt(...c.l);
    if (c.roll) camera.rotateZ(c.roll);
    camera.updateMatrixWorld(true);
    shot.setup(world, t, camera);
    finishFrame(world, t, shot, camera);
    // depth of field: focus on the look-at point unless the shot names a distance
    const focus = c.focus || Math.hypot(c.l[0] - c.p[0], c.l[1] - c.p[1], c.l[2] - c.p[2]);
    dof.uniforms.uFocus.value = focus;
    dof.uniforms.uAperture.value = (c.ap ?? 10) * (W / 1440);
    dof.uniforms.uMaxPx.value = 22 * (W / 1440);
    const gr = { ...S.grade, ...(shot.grade || {}) };
    const u = look.uniforms;
    u.uTime.value = t;
    u.uContrast.value = gr.contrast ?? 1.06; u.uSat.value = gr.sat ?? 1.12; u.uLift.value = gr.lift ?? 0;
    u.uVignette.value = gr.vignette ?? 0.32;
    u.uShadow.value.set(...(gr.shadow || [0.93, 0.92, 1.06])); u.uHigh.value.set(...(gr.high || [1.05, 1.0, 0.95]));
    u.uFade.value = shot.fade ? shot.fade(t) : 0;
    bloom.strength = gr.bloom ?? 0.45; bloom.threshold = gr.bloomThr ?? 0.88;
    renderer.toneMappingExposure = gr.exposure ?? 1.0;
    edges.uniforms.uStrength.value = gr.lines ?? 0.97;
    edges.uniforms.uFar.value = gr.lineFar ?? 400;
    prepass();
    composer.renderToScreen = false;
    composer.render();
    return composer.readBuffer.texture;
  }

  function renderSharpOrBlurred(shot, t, target) {
    const extra = shot.blur ? shot.blur(t) : 0;
    const need = Math.max(camSpeed(shot, t) / 0.012, extra);
    if (Q.sub <= 1 || need < 1.5) { quad(target, renderShot(shot, t), null, 0, 1, false); return; }
    const NS = Math.max(3, Math.min(14, Math.ceil(need)));
    for (let k = 0; k < NS; k++) {
      const off = (k / (NS - 1) - 0.5) * (1 / 60); // 180-degree shutter
      const tex = renderShot(shot, t + off);
      quad(target, tex, null, 0, 1 / NS, k > 0);
    }
  }

  async function renderFrame(t) {
    const shot = findShot(t);
    const i = SHOTS.indexOf(shot);
    const prev = SHOTS[i - 1];
    const d = shot.dissolve || 0;
    if (d > 0 && prev && t < shot.t0 + d) {
      renderSharpOrBlurred(prev, t, accA);
      renderSharpOrBlurred(shot, t, accB);
      const k = (t - shot.t0) / d;
      quad(null, accA.texture, accB.texture, k * k * (3 - 2 * k), 1, false);
    } else {
      renderSharpOrBlurred(shot, t, accA);
      quad(null, accA.texture, null, 0, 1, false);
    }
    og.drawImage(renderer.domElement, 0, 0);
    if (shot.overlay) shot.overlay(og, t, W, H, world, camera);
    if (!params.get('nocap')) drawCaption(og, caps, t, W, H);
    return og.getImageData(0, 0, W, H).data;
  }

  window.__renderAndPost = async (t, id) => {
    const t0 = performance.now();
    const px = await renderFrame(t);
    if (PROF) console.log('frame', t.toFixed(3), (performance.now() - t0).toFixed(0), 'ms');
    await fetch('/frame/' + id, { method: 'POST', body: px });
  };
  window.__ready = true;
}

boot().catch((e) => { console.log('BOOT ERROR', e.message, e.stack); });
