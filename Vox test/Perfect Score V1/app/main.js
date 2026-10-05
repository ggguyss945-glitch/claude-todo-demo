// "Perfect Score" renderer: low-poly sets + photo-style faces, rendered per frame
// as a pure function of time (chunks render out of order on several workers).
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { buildWorld } from './world.js';
import { makeComposer } from './post.js';
import { buildCaptions, drawCaption } from './overlay.js';
import { SHOTS, findShot, initShots, resetFrame, finishFrame } from './shots.js';

const params = new URLSearchParams(location.search);
const W = parseInt(params.get('w') || '1440'), H = parseInt(params.get('h') || '2560');
const Q = { shadow: 4096, msaa: parseInt(params.get('msaa') || '4'), sub: params.get('sub') ? parseInt(params.get('sub')) : 3 };
const PROF = params.get('prof') === '1';

async function boot() {
  await Promise.all([
    document.fonts.load('bold 40px "Liberation Sans"'), document.fonts.load('40px "Liberation Sans"'),
    document.fonts.load('bold 40px "Liberation Serif"'), document.fonts.load('italic 40px "Liberation Serif"'),
    document.fonts.load('italic bold 40px "Liberation Serif"'), document.fonts.load('40px "Liberation Serif"'),
    document.fonts.load('bold 40px "DejaVu Sans"'), document.fonts.load('40px "DejaVu Sans"'), document.fonts.load('bold 40px "DejaVu Sans Mono"'),
  ]);
  const words = await (await fetch('/script/words.json')).json();
  const caps = buildCaptions(words);

  const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(1);
  renderer.setSize(W, H, false);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  document.body.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#0a0a0c');
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  const camera = new THREE.PerspectiveCamera(40, W / H, 0.02, 80);
  scene.add(camera);
  const world = buildWorld(scene);
  world.renderer = renderer; world.scene = scene; world.camera = camera;
  await initShots(world);
  const { composer, bloom, look } = makeComposer(renderer, scene, camera, W, H, Q);
  bloom.threshold = 1.15; bloom.strength = 0.35; bloom.radius = 0.5;
  const u = look.uniforms;
  u.uCA.value = 0.8; u.uSharpen.value = 0.5; u.uSharpRadius.value = 1.4 * W / 1440; u.uVignette.value = 0.38;
  u.uContrast.value = 1.08; u.uSat.value = 1.14; u.uLift.value = -0.012; u.uGrain.value = 0.022;
  globalThis.__ikWarn = (n, L, e) => { if (PROF) console.log('IK reach error', n, L, e.toFixed(3)); };

  const out = document.createElement('canvas');
  out.width = W; out.height = H;
  const og = out.getContext('2d', { willReadFrequently: true });

  function setSet(name) {
    for (const k in world.sets) world.sets[k].group.visible = k === name;
    const S = world.sets[name];
    scene.environmentIntensity = S.env;
    renderer.toneMappingExposure = S.exposure;
  }

  // ---- temporal accumulation for motion blur
  const accRT = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType });
  const quadCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const accMat = new THREE.ShaderMaterial({
    uniforms: { tDiffuse: { value: null }, uW: { value: 1 } },
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }',
    fragmentShader: 'uniform sampler2D tDiffuse; uniform float uW; varying vec2 vUv; void main(){ gl_FragColor = vec4(texture2D(tDiffuse, vUv).rgb * uW, 1.0); }',
    depthTest: false, depthWrite: false,
  });
  const quadScene = new THREE.Scene();
  quadScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), accMat));

  function camAt(shot, t) {
    const c = shot.cam(Math.min(Math.max(t, shot.t0), shot.t1 - 1e-4), world);
    return c;
  }
  function camSpeed(shot, t) {
    const dt = 1 / 60;
    const a = camAt(shot, t - dt), b = camAt(shot, t + dt);
    const dp = Math.hypot(a.p[0] - b.p[0], a.p[1] - b.p[1], a.p[2] - b.p[2]);
    const da = new THREE.Vector3(...a.l).sub(new THREE.Vector3(...a.p)).normalize();
    const db = new THREE.Vector3(...b.l).sub(new THREE.Vector3(...b.p)).normalize();
    const ang = Math.acos(Math.min(1, da.dot(db))) + Math.abs((a.roll || 0) - (b.roll || 0)) + Math.abs((a.fov || 40) - (b.fov || 40)) * 0.01;
    return dp * 3 + ang;
  }

  function stage(t, tFrame) {
    const shot = findShot(tFrame);
    resetFrame(world, t, shot);
    setSet(shot.set);
    const c = camAt(shot, t);
    if (params.get('dcam')) { const v = params.get('dcam').split(',').map(Number); c.p = v.slice(0, 3); c.l = v.slice(3, 6); c.fov = v[6] || 50; }
    camera.position.set(...c.p);
    camera.up.set(0, 1, 0);
    camera.fov = c.fov || 40;
    camera.updateProjectionMatrix();
    camera.lookAt(...c.l);
    if (c.roll) camera.rotateZ(c.roll);
    camera.updateMatrixWorld(true);
    shot.setup(world, t, camera);
    finishFrame(world, t, shot, camera);
    // grade per shot
    u.uTime.value = t;
    u.uFade.value = shot.fade ? shot.fade(t) : 0;
    u.uWarm.value = shot.warm ?? (shot.set === 'office' || shot.set === 'home' ? 0.6 : 0.15);
    u.uCCTV.value = shot.cctv ? shot.cctv(t) : 0;
    u.uSat.value = shot.sat ?? 1.14;
    u.uVignette.value = shot.vignette ?? 0.38;
    bloom.strength = shot.bloom ?? 0.35;
    return shot;
  }

  async function renderFrame(t) {
    const shot = findShot(t);
    const spd = camSpeed(shot, t);
    const extra = shot.blur ? shot.blur(t) : 0; // object motion that needs blur
    const need = Math.max(spd / 0.012, extra);
    if (Q.sub <= 1 || need < 1.5) {
      stage(t, t);
      composer.renderToScreen = true;
      composer.render();
      return finishOverlay(shot, t);
    }
    const NS = Math.max(3, Math.min(24, Math.ceil(need)));
    composer.renderToScreen = false;
    for (let k = 0; k < NS; k++) {
      const off = (k / (NS - 1) - 0.5) * (1 / 60); // 180-degree shutter
      const tk = Math.min(Math.max(t + off, shot.t0), shot.t1 - 1e-4);
      stage(tk, t);
      composer.render();
      accMat.uniforms.tDiffuse.value = composer.readBuffer.texture;
      accMat.uniforms.uW.value = 1 / NS;
      accMat.blending = k === 0 ? THREE.NoBlending : THREE.AdditiveBlending;
      accMat.transparent = k !== 0;
      renderer.setRenderTarget(accRT);
      renderer.autoClear = k === 0;
      renderer.render(quadScene, quadCam);
      renderer.autoClear = true;
    }
    accMat.uniforms.tDiffuse.value = accRT.texture;
    accMat.uniforms.uW.value = 1;
    accMat.blending = THREE.NoBlending;
    accMat.transparent = false;
    renderer.setRenderTarget(null);
    renderer.render(quadScene, quadCam);
    if (PROF) console.log('subframes', t.toFixed(3), NS);
    return finishOverlay(shot, t);
  }

  function finishOverlay(shot, t) {
    og.drawImage(renderer.domElement, 0, 0);
    if (shot.overlay) shot.overlay(og, t, W, H, world, camera);
    drawCaption(og, caps, t, W, H);
    return og.getImageData(0, 0, W, H).data;
  }

  window.__renderAndPost = async (t, id) => {
    const t0 = performance.now();
    const px = await renderFrame(t);
    if (PROF) console.log('frame', t.toFixed(3), (performance.now() - t0).toFixed(0), 'ms');
    await fetch('/frame/' + id, { method: 'POST', body: px });
  };
  window.__findNaN = (t) => {
    stage(t, t);
    const bad = [];
    scene.traverse((o) => { if (o.visible !== false && o.matrixWorld.elements.some((v) => !Number.isFinite(v))) bad.push((o.parent && o.parent.name ? o.parent.name + '/' : '') + (o.name || o.type)); });
    for (const k in world.cast) { const c = world.cast[k]; for (const j in c.J) { const J = c.J[j]; if (J.rotation && [J.rotation.x, J.rotation.y, J.rotation.z].some((v) => !Number.isFinite(v))) bad.push(k + ':' + j); } }
    world.kids.forEach((c, i) => { for (const j in c.J) { const J = c.J[j]; if (J.rotation && [J.rotation.x, J.rotation.y, J.rotation.z].some((v) => !Number.isFinite(v))) bad.push('kid' + i + ':' + j); } });
    return bad.slice(0, 30);
  };
  window.__joints = (t, name) => {
    stage(t, t);
    const c = world.cast[name] || world.kids[parseInt(name)];
    const r = {};
    for (const j of ['hips', 'spine', 'neck', 'head']) r[j] = [c.J[j].rotation.x, c.J[j].rotation.y, c.J[j].rotation.z].map((v) => +v.toFixed(3));
    r.root = [c.root.position.x, c.root.position.y, c.root.position.z, c.root.rotation.y].map((v) => +v.toFixed(3));
    r.vis = c.root.visible;
    return r;
  };
  window.__ready = true;
}

boot().catch((e) => { console.log('BOOT ERROR', e.message, e.stack); });
