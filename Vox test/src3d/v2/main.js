import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { buildWorld, drawTV, drawPainting, SURV, BOOTH } from './world.js';
import { makeComposer } from './post.js';
import { buildCaptions, drawCaption, drawCCTV, tcString } from './overlay.js';
import { SHOTS, findShot, stageDefault, setAnchors, registerPaper, getPaper, getPovRig } from './shots.js';
import { POSES } from './chars.js';
import * as TX from './tex.js';
import { prog, lerp, clamp, easeInOut, keys } from './util.js';

const params = new URLSearchParams(location.search);
const VERSION = params.get('v') || 'v2';
const W = parseInt(params.get('w') || '1440'), H = parseInt(params.get('h') || '2560');
const QUALITY = {
  v2: { shadow: 2048, msaa: 0, smaa: true, feedRes: 256 },
  v3: { shadow: 4096, msaa: 4, smaa: false, feedRes: 384 },
};
const Q = QUALITY[VERSION] || QUALITY.v2;

async function boot() {
  await Promise.all([
    document.fonts.load('bold 40px "Liberation Sans"'), document.fonts.load('40px "Liberation Sans"'),
    document.fonts.load('bold 40px "Liberation Serif"'), document.fonts.load('italic bold 40px "Liberation Serif"'),
    document.fonts.load('bold 40px "DejaVu Sans"'), document.fonts.load('40px "DejaVu Sans"'),
  ]);
  const words = await (await fetch('/transcript/words.json')).json();
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
  scene.background = new THREE.Color('#020306');
  scene.fog = new THREE.Fog('#03050c', 9, 26);
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.22;
  if ((params.get('off') || '').includes('env')) scene.environment = null;
  const camera = new THREE.PerspectiveCamera(60, W / H, 0.03, 80);
  scene.add(camera);
  const world = buildWorld(scene, Q);
  drawPainting(world);
  const { composer, bloom, look } = makeComposer(renderer, scene, camera, W, H, Q);
  const OFF = (params.get('off') || '').split(',');
  composer.passes.forEach((p) => {
    const n = p.constructor.name;
    if ((OFF.includes('bloom') && n === 'UnrealBloomPass') || (OFF.includes('smaa') && n === 'SMAAPass') || (OFF.includes('look') && n === 'ShaderPass')) p.enabled = false;
  });
  if (OFF.includes('shadow')) renderer.shadowMap.enabled = false;

  // dome camera stage (by the right wall, with wood panelling behind)
  const dome = world.props.dome;
  dome.position.set(8.25, 3.75, 3.2);
  const wood = new THREE.Mesh(new THREE.PlaneGeometry(4.5, 3.6), new THREE.MeshStandardMaterial({ map: TX.woodPanelTexture(), roughness: 0.6, color: '#3a3430' }));
  wood.position.set(8.95, 1.8, 3.2);
  wood.rotation.y = -Math.PI / 2;
  world.sets.casino.add(wood);
  const soffit = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.5, 2.4), new THREE.MeshStandardMaterial({ color: '#2a2622', roughness: 0.8 }));
  soffit.position.set(8.4, 4.05, 3.2);
  world.sets.casino.add(soffit);
  const domeLight = new THREE.PointLight('#ffd8b0', 7, 5, 1.5);
  domeLight.position.set(7.2, 3.2, 4.2);
  scene.add(domeLight);
  setAnchors(dome.position.clone(), world.props.claw.position.clone());

  // reflection of you in the dome: rendered from the dome's point of view
  const reflRT = new THREE.WebGLRenderTarget(512, 512);
  const reflCam = new THREE.PerspectiveCamera(30, 1, 0.05, 30);
  const reflGeo = new THREE.SphereGeometry(0.305, 24, 12, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2);
  {
    const p = reflGeo.attributes.position, uv = reflGeo.attributes.uv;
    for (let i = 0; i < p.count; i++) uv.setXY(i, 0.5 - p.getX(i) / 0.5, 0.95 + p.getY(i) / 0.42);
  }
  const reflMat = new THREE.MeshBasicMaterial({ map: reflRT.texture, transparent: true, opacity: 0, color: new THREE.Color(1.6, 1.6, 1.6), depthWrite: false });
  const refl = new THREE.Mesh(reflGeo, reflMat);
  refl.rotation.y = Math.PI / 2;
  refl.position.y = -0.03;
  dome.add(refl);
  const glint = new THREE.Mesh(new THREE.SphereGeometry(0.306, 8, 6, Math.PI * 0.95, Math.PI * 0.32, Math.PI * 0.52, Math.PI * 0.3), new THREE.MeshBasicMaterial({ color: new THREE.Color(2.6, 2.6, 2.7), side: THREE.DoubleSide }));
  glint.position.y = -0.03;
  dome.add(glint);

  // ------------------------------------------------- surveillance feeds ---
  const FR = Q.feedRes;
  const feeds = [];
  const feedCams = [
    { p: [-1.75, 2.75, -0.95], l: [0.05, 0.95, 1.55] },
    { p: [2.4, 3.2, 1.8], l: [0, 0.9, -0.3] },
    { p: [-0.42, 1.42, 1.22], l: [0.08, 1.22, 2.05] },
    { p: [-2.55, 3.15, 2.05], l: [-0.35, 1.0, -1.35] },
    { p: [0.5, 1.4, 0.6], l: [-0.05, 0.84, 1.28] },
    { p: [-4.5, 2.8, 3.0], l: [-1.0, 1.0, 0.0] },
  ];
  for (let i = 0; i < feedCams.length; i++) {
    const rt = new THREE.WebGLRenderTarget(FR, Math.round(FR * 0.8));
    rt.texture.colorSpace = THREE.SRGBColorSpace;
    const cam = new THREE.PerspectiveCamera(50, 1.25, 0.05, 40);
    cam.position.set(...feedCams[i].p);
    cam.lookAt(...feedCams[i].l);
    feeds.push({ rt, cam });
  }
  world.props.monitors.forEach((scr, i) => {
    scr.material = new THREE.MeshBasicMaterial({ map: feeds[(i * 7 + 3) % feeds.length].rt.texture, color: new THREE.Color(1.35, 1.35, 1.5) });
  });
  // the big "Cam 7" monitor the operator stares at (centre of the wall)
  const cam7RT = new THREE.WebGLRenderTarget(768, 614);
  cam7RT.texture.colorSpace = THREE.SRGBColorSpace;
  const cam7 = new THREE.PerspectiveCamera(44, 1.25, 0.05, 40);
  const bigMon = new THREE.Group();
  const bigBody = new THREE.Mesh(new THREE.BoxGeometry(1.25, 1.02, 0.5), new THREE.MeshStandardMaterial({ color: '#2e3238', roughness: 0.6 }));
  bigBody.position.z = -0.26;
  bigMon.add(bigBody);
  const bigScr = new THREE.Mesh(new THREE.PlaneGeometry(1.1, 0.88), new THREE.MeshBasicMaterial({ map: cam7RT.texture, color: new THREE.Color(0.95, 0.95, 1.05) }));
  bigMon.add(bigScr);
  const hudC = document.createElement('canvas');
  hudC.width = 1100; hudC.height = 880;
  const hudTex = TX.toTex(hudC);
  const hud = new THREE.Mesh(new THREE.PlaneGeometry(1.1, 0.88), new THREE.MeshBasicMaterial({ map: hudTex, transparent: true, color: new THREE.Color(1.1, 1.1, 1.1) }));
  hud.position.z = 0.003;
  bigMon.add(hud);
  bigMon.position.set(SURV.x + 0.32, 1.32, SURV.z - 2.5);
  scene.add(bigMon);

  // ------------------------------------------------- mugshot sheet ---
  function grab(rt, w, h) {
    const px = new Uint8Array(w * h * 4);
    renderer.readRenderTargetPixels(rt, 0, 0, w, h, px);
    const [c, g] = TX.canvas(w, h);
    const img = g.createImageData(w, h);
    for (let y = 0; y < h; y++) img.data.set(px.subarray((h - 1 - y) * w * 4, (h - y) * w * 4), y * w * 4);
    g.putImageData(img, 0, 0);
    return c;
  }
  const shotRT = new THREE.WebGLRenderTarget(400, 400);
  shotRT.texture.colorSpace = THREE.SRGBColorSpace;
  const shotCam = new THREE.PerspectiveCamera(30, 1, 0.05, 20);
  const mugs = [];
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  for (const name of ['mugDealer', 'mugWheel', 'mugCard']) {
    const ch = world.cast[name];
    for (const k in world.cast) world.cast[k].root.visible = false;
    world.crowd.forEach((c) => (c.root.visible = false));
    ch.root.visible = true;
    ch.root.position.set(BOOTH.x, 0, BOOTH.z);
    ch.setPose(POSES.stand);
    shotCam.position.set(BOOTH.x, 1.5, BOOTH.z + 2.1);
    shotCam.lookAt(BOOTH.x, 1.45, BOOTH.z);
    renderer.setRenderTarget(shotRT);
    renderer.render(scene, shotCam);
    renderer.setRenderTarget(null);
    mugs.push(grab(shotRT, 400, 400));
    ch.root.visible = false;
  }
  // polaroid of you, taken from the Cam 7 angle
  const pl = world.cast.player;
  pl.root.visible = true;
  pl.root.position.set(0, 0, 2.02);
  pl.root.rotation.set(0, Math.PI, 0);
  pl.setPose(POSES.sitTable);
  shotCam.position.set(-0.42, 1.38, 1.3);
  shotCam.lookAt(0.0, 1.25, 2.0);
  renderer.setRenderTarget(shotRT);
  renderer.render(scene, shotCam);
  renderer.setRenderTarget(null);
  const polCanvas = grab(shotRT, 400, 400);
  pl.root.visible = false;

  const [pc, pg] = TX.canvas(840, 1120);
  pg.fillStyle = '#f2f2ee';
  pg.fillRect(0, 0, 840, 1120);
  const labels = [['Dealer Collusion'], ['Wheel Bias', 'Exploitation'], ['Card counting']];
  for (let i = 0; i < 3; i++) {
    pg.drawImage(mugs[i], 50, 40 + i * 360, 320, 320);
    pg.fillStyle = '#111';
    pg.font = '46px "Liberation Sans", Arial';
    labels[i].forEach((ln, j) => pg.fillText(ln, 395, 210 + i * 360 + j * 52 - (labels[i].length - 1) * 26));
  }
  TX.noiseFill(pg, 840, 1120, 0, 6, 3, 2);
  const paperTex = TX.toTex(pc);
  const paper = new THREE.Group();
  const sheet = new THREE.Mesh(new THREE.PlaneGeometry(0.42, 0.56), new THREE.MeshBasicMaterial({ map: paperTex, side: THREE.DoubleSide, color: new THREE.Color(0.78, 0.8, 0.86) }));
  paper.add(sheet);
  const pHand = new THREE.Mesh(new THREE.BoxGeometry(0.09, 0.15, 0.04), new THREE.MeshStandardMaterial({ color: '#e8c8b0', roughness: 0.7, flatShading: true }));
  pHand.position.set(0.15, -0.27, 0.02);
  pHand.rotation.z = 0.3;
  paper.add(pHand);
  const pSleeve = new THREE.Mesh(new THREE.CylinderGeometry(0.055, 0.06, 0.5, 7), new THREE.MeshStandardMaterial({ color: '#202024', roughness: 0.8, flatShading: true }));
  pSleeve.position.set(0.3, -0.5, 0.08);
  pSleeve.rotation.z = 0.7;
  paper.add(pSleeve);
  scene.add(paper);
  const [polc, polg] = TX.canvas(440, 520);
  polg.fillStyle = '#f4f4f0'; polg.fillRect(0, 0, 440, 520);
  polg.drawImage(polCanvas, 20, 20, 400, 400);
  const polaroid = new THREE.Mesh(new THREE.PlaneGeometry(0.2, 0.236), new THREE.MeshBasicMaterial({ map: TX.toTex(polc), side: THREE.DoubleSide, color: new THREE.Color(0.8, 0.8, 0.84) }));
  scene.add(polaroid);
  registerPaper(paper, polaroid);

  // ------------------------------------------------------------ frame ---
  const out = document.createElement('canvas');
  out.width = W; out.height = H;
  const og = out.getContext('2d', { willReadFrequently: true });
  const L = world.lights;
  let faceLight = new THREE.SpotLight('#ffe0c8', 0, 3, 0.5, 0.6, 1.5);
  scene.add(faceLight, faceLight.target);
  const camFill = new THREE.PointLight('#c8d8ff', 0, 5, 1.6);
  scene.add(camFill);

  function setSet(set, shot) {
    const casino = set === 'casino';
    world.sets.casino.visible = casino;
    world.sets.surv.visible = set === 'surv';
    world.sets.office.visible = set === 'office';
    world.sets.booth.visible = false;
    bigMon.visible = set === 'surv';
    hud.visible = !!shot.paper;
    L.key.visible = casino;
    L.dealerFill.visible = casino;
    L.wallWash.visible = casino; L.wallWash2.visible = casino;
    L.room.forEach((l) => (l.visible = casino));
    domeLight.visible = casino;
    L.surv.forEach((l) => (l.visible = set === 'surv'));
    L.office.forEach((l) => (l.visible = set === 'office'));
    L.booth.forEach((l) => (l.visible = false));
    L.hemi.intensity = { casino: 0.6, surv: 0.3, office: 0.22 }[set];
    // key light framing per shot type
    world.props.chandeliers.forEach((ch) => (ch.visible = !shot.topdown));
    if (shot.topdown) {
      L.key.position.set(0.3, 4.3, 0.1); L.key.target.position.set(0, 0, 0);
      L.key.angle = 0.72; L.key.intensity = 22; L.key.distance = 16; L.hemi.intensity = 0.3;
    } else {
      L.key.position.set(0.1, 3.6, -0.3); L.key.target.position.set(0, 0.8, 0.0);
      L.key.angle = 0.62; L.key.intensity = 11; L.key.distance = 14;
    }
    scene.fog.near = set === 'casino' ? 9 : 6;
  }

  function renderFeeds(t) {
    for (const f of feeds) {
      renderer.setRenderTarget(f.rt);
      renderer.render(scene, f.cam);
    }
    renderer.setRenderTarget(null);
  }

  function drawHud(t, glyphs) {
    const g = hudC.getContext('2d');
    g.clearRect(0, 0, hudC.width, hudC.height);
    g.save();
    g.scale(hudC.width / W * 1.25, hudC.height / H * 2.4);
    drawCCTV(g, { cam: 'Cam 7', tc: (tt) => 22 * 3600 + 10 * 60 + 14 + (tt - 39.0) + 4 / 30, y: 0.13 }, t, W, H);
    g.restore();
    g.font = 'bold 120px "DejaVu Sans"';
    g.fillStyle = '#f4f4f4';
    g.strokeStyle = '#000'; g.lineWidth = 10;
    const gl = [';.?', '...?', ',=:?'][Math.floor(t * 2) % 3];
    g.strokeText(gl, 60, 330); g.fillText(gl, 60, 330);
    hudTex.needsUpdate = true;
  }

  const PROF = params.get('prof') === '1';
  let tm = {};
  const mark = (k) => { if (PROF) { const n = performance.now(); tm[k] = n; } };
  async function renderFrame(t) {
    mark('a');
    const shot = findShot(t);
    if (world.dealerDark) { world.dealerDark.headMesh.material.forEach((m) => m.color.setScalar(1)); world.dealerDark = null; }
    stageDefault(world, t, camera);
    // camera
    const c = shot.cam(t);
    camera.position.set(...c.p);
    camera.up.set(...(c.up || [0, 1, 0]));
    camera.fov = c.fov || 60;
    camera.updateProjectionMatrix();
    camera.lookAt(...c.l);
    if (c.roll) camera.rotateZ(c.roll);
    camera.updateMatrixWorld(true);
    camFill.intensity = (c.fill || 0) * 4.0;
    camFill.visible = camFill.intensity > 0;
    camFill.position.copy(camera.position).add(new THREE.Vector3(0.3, 0.5, 0).applyQuaternion(camera.quaternion));
    shot.setup(world, t, camera);
    setSet(shot.set, shot);
    drawTV(world, t);
    // per-shot extras
    faceLight.intensity = 0;
    if (world.extraLights && shot.t0 === 14.3) {
      const d = world.dealerNow;
      d.root.updateMatrixWorld(true);
      const hp = new THREE.Vector3();
      d.J.head.localToWorld(hp.set(0, 0.13, 0.1));
      faceLight.position.set(hp.x - 0.3, hp.y + 0.6, hp.z - 1.2);
      faceLight.target.position.copy(hp);
      faceLight.intensity = 5 * world.extraLights.faceLight;
      const dk = 0.06 + 0.94 * world.extraLights.faceLight;
      d.headMesh.material.forEach((m) => m.color.setScalar(dk));
      if (PROF) console.log('dk', t, dk, d.root.name, d.headMesh.material.length);
      world.dealerDark = d;
      L.key.visible = false;
      L.dealerFill.visible = false;
    }
    world.extraLights = null;
    faceLight.visible = faceLight.intensity > 0;
    // dome reflection
    reflMat.opacity = 0;
    if (shot.t0 === 23.467) {
      const k = clamp((t - 24.15) * 2.0);
      reflMat.opacity = 0.75 * k;
      if (k > 0) {
        const pl = world.cast.player;
        pl.root.visible = true;
        pl.root.position.set(0, 0, 2.02);
        pl.root.rotation.set(0, Math.PI, 0);
        pl.setPose(POSES.sitTable);
        reflCam.position.set(-0.15, 1.95, 1.05);
        reflCam.fov = 34; reflCam.updateProjectionMatrix();
        reflCam.lookAt(0.0, 1.32, 2.02);
        world.sets.casino.visible = true;
        renderer.setRenderTarget(reflRT);
        renderer.render(scene, reflCam);
        renderer.setRenderTarget(null);
        pl.root.visible = false;
      }
    }
    // surveillance monitors show live casino feeds
    if (shot.set === 'surv') {
      const vis = { surv: world.sets.surv.visible, casino: world.sets.casino.visible };
      // stage the casino for the feeds
      const C = world.cast;
      const pl = C.player;
      pl.root.visible = true; pl.root.position.set(0, 0, 2.02); pl.root.rotation.set(0, Math.PI, 0); pl.setPose(POSES.sitTable);
      world.sets.casino.visible = true;
      L.key.visible = true; L.hemi.intensity = 0.6;
      const survVisibleChars = [];
      for (const k of ['operator', 'operator2', 'guard', 'guard2']) if (C[k].root.visible) { survVisibleChars.push(k); }
      renderFeeds(t);
      cam7.position.set(-0.42, 1.42, 1.25);
      cam7.lookAt(0.08, 1.22, 2.05);
      renderer.setRenderTarget(cam7RT);
      renderer.render(scene, cam7);
      renderer.setRenderTarget(null);
      pl.root.visible = false;
      world.sets.casino.visible = vis.casino;
      L.key.visible = false;
      L.hemi.intensity = 0.35;
      drawHud(t);
    }
    // paper / polaroid
    const { paper, polaroid } = getPaper();
    if (shot.paper) {
      paper.visible = true;
      if (shot.t0 === 39.0) {
        paper.position.set(SURV.x + 0.5, lerp(1.08, 1.13, prog(t, 39, 40.2)), SURV.z - 2.05);
        paper.rotation.set(0, -0.08, 0.03);
      } else if (shot.t0 === 40.233) {
        paper.position.set(SURV.x + 0.78, 1.45, SURV.z - 1.75);
        paper.rotation.set(0, 0.35, 0.05);
        paper.scale.setScalar(0.8);
      } else {
        paper.position.set(SURV.x + 0.22, 1.17, SURV.z - 1.8);
        paper.rotation.set(-0.05, 0.05, 0.02);
        paper.scale.setScalar(1);
      }
      if (shot.t0 !== 40.233) paper.scale.setScalar(1);
    }
    if (shot.polaroid) {
      polaroid.visible = true;
      const k = easeInOut(prog(t, 69.0, 70.2));
      polaroid.position.set(SURV.x + lerp(0.45, 0.33, k), lerp(0.9, 1.01, k), SURV.z - 1.74);
      polaroid.rotation.set(-0.1, 0, lerp(-0.25, -0.05, k));
    }
    // handshake: your hand from the right
    if (shot.handshake) {
      const rig = getPovRig(scene);
      if (rig.visible) {
        rig.position.copy(camera.position);
        rig.quaternion.copy(camera.quaternion);
        const k = prog(t, 71.6, 72.2) * (1 - prog(t, 73.2, 73.6));
        const pump = Math.sin((t - 72.2) * 9) * 0.02 * prog(t, 72.2, 72.4) * (1 - prog(t, 73.0, 73.2));
        const a = rig.userData.arms;
        a[0].visible = false;
        a[1].visible = true;
        a[1].position.set(lerp(0.45, 0.13, easeInOut(k)), -0.3 + pump, lerp(-0.25, -0.55, easeInOut(k)));
        a[1].rotation.set(0.15, 0.55, -1.2);
      }
    }
    // post look per shot
    const u = look.uniforms;
    u.uTime.value = t;
    u.uCCTV.value = shot.cctv ? 1 : (shot.t0 === 39.0 ? 0.35 : 0);
    u.uScreen.value = shot.screen ? 1 : 0;
    u.uScreenCell.value = 18;
    u.uFade.value = 0;
    u.uWarm.value = shot.set === 'office' ? 1 : 0;
    bloom.strength = shot.set === 'surv' ? 0.8 : 0.6;
    mark('b');
    composer.render();
    if (PROF) { const gl = renderer.getContext(); const px1 = new Uint8Array(4); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px1); }
    mark('c');
    if (PROF) { const gl = renderer.getContext(); const big = new Uint8Array(W * H * 4); const t0 = performance.now(); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, big); console.log('readPixels full', (performance.now() - t0).toFixed(0)); }
    // composite overlay
    og.drawImage(renderer.domElement, 0, 0);
    if (shot.cctv) {
      const info = { ...shot.cctv };
      if (shot.faceTrack) {
        const pl = world.cast.player;
        pl.root.updateMatrixWorld(true);
        const hp = new THREE.Vector3(), top = new THREE.Vector3();
        pl.J.head.localToWorld(hp.set(0, 0.11, 0.05));
        pl.J.head.localToWorld(top.set(0, 0.24, 0.05));
        const a = hp.clone().project(camera), b = top.clone().project(camera);
        const size = Math.abs(a.y - b.y) * 0.5 * H / W * 2.1;
        info.face = { x: (a.x + 1) / 2, y: (1 - a.y) / 2, s: size, glyphX: shot.t0 === 59.4 ? undefined : undefined };
      }
      drawCCTV(og, info, t, W, H);
    }
    drawCaption(og, caps, t, W, H);
    mark('d');
    const data = og.getImageData(0, 0, W, H).data;
    mark('e');
    if (PROF) console.log(`prof t=${t} stage=${(tm.b - tm.a).toFixed(0)} compose=${(tm.c - tm.b).toFixed(0)} overlay=${(tm.d - tm.c).toFixed(0)} read=${(tm.e - tm.d).toFixed(0)}`);
    return data;
  }

  window.__renderAndPost = async (t, id) => {
    const px = await renderFrame(t);
    await fetch('/frame/' + id, { method: 'POST', body: px });
  };
  window.__ready = true;
}

boot().catch((e) => { console.log('BOOT ERROR', e.message, e.stack); });
