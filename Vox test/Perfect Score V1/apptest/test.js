// Test bench: character lineup, expressions, gait strip and IK checks.
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { makeComposer } from '../app/post.js';
import { makeCharacter, POSES, walkPose, armIK, headLook, blendPose, SEAT_H } from '../app/chars.js';
import { CAST_DEFS, classmateDef } from '../app/cast.js';

const params = new URLSearchParams(location.search);
const W = parseInt(params.get('w') || '1440'), H = parseInt(params.get('h') || '2560');
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H, false);
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color('#202428');
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 0.35;
const camera = new THREE.PerspectiveCamera(40, W / H, 0.05, 60);
const floor = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), new THREE.MeshStandardMaterial({ color: '#8a7a68', roughness: 0.8 }));
floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
const wall = new THREE.Mesh(new THREE.PlaneGeometry(40, 10), new THREE.MeshStandardMaterial({ color: '#c8b89a', roughness: 0.9 }));
wall.position.set(0, 5, -3); wall.receiveShadow = true; scene.add(wall);
const sun = new THREE.DirectionalLight('#fff0dc', 3.2);
sun.position.set(4, 7, 6); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -8, right: 8, top: 8, bottom: -8, near: 1, far: 30 }); sun.shadow.bias = -0.0004;
scene.add(sun);
scene.add(new THREE.HemisphereLight('#dfe8ff', '#5a4a3a', 0.8));
const { composer, look } = makeComposer(renderer, scene, camera, W, H, { msaa: 4 });

const names = ['you', 'teacher', 'principal', 'teacher2', 'teacher3', 'smart', 'dad', 'mom'];
const chars = names.map((n) => makeCharacter(CAST_DEFS[n]));
const kids = [0, 1, 2, 3, 5, 7].map((i) => makeCharacter(classmateDef(i)));
const all = [...chars, ...kids];
all.forEach((c) => scene.add(c.root));
const marker = new THREE.Mesh(new THREE.SphereGeometry(0.02, 8, 6), new THREE.MeshBasicMaterial({ color: '#ff2020' }));
scene.add(marker);
const chair = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.04, 0.4), new THREE.MeshStandardMaterial({ color: '#6a4a2a' }));
scene.add(chair);

function hideAll() { all.forEach((c) => (c.root.visible = false)); marker.visible = false; chair.visible = false; }

async function view(t) {
  hideAll();
  const v = Math.floor(t);
  if (v === 0 || v === 1) {
    // lineup (0: main cast, 1: classmates)
    const list = v === 0 ? chars : kids;
    list.forEach((c, i) => {
      c.root.visible = true;
      const col = i % 4, row = Math.floor(i / 4);
      c.root.position.set((col - 1.5) * 1.0, 0, -row * 1.6);
      c.root.rotation.set(0, 0, 0);
      c.setPose(POSES.stand); c.resetFace(); c.idle(0.5);
    });
    camera.position.set(0, 1.6, 6.5); camera.fov = 40; camera.lookAt(0, 1.0, -0.8);
  } else if (v === 2) {
    // expressions: 2x2 grid of heads, close-up
    const ex = ['neutral', 'smile', 'grin', 'suspicious', 'shocked', 'sad', 'angry', 'worried'];
    const sub = Math.round((t - v) * 10);
    [chars[0], chars[1], chars[3], kids[1], chars[5], chars[2]].forEach((c, i) => {
      c.root.visible = true;
      c.setPose(POSES.stand); c.resetFace(); c.expr = ex[(sub + i) % ex.length]; c.look = [(i % 2) ? -0.5 : 0.5, 0]; c.idle(0.5);
      const top = c.scale * (1.029 + 0.52 + 0.12 + 0.14);
      c.root.position.set((i % 2 - 0.5) * 0.5, -top + (1 - Math.floor(i / 2)) * 0.5 + 1.6, -0.3 * (i % 2));
      c.root.rotation.set(0, (i % 2 ? -0.35 : 0.35), 0);
    });
    camera.position.set(0, 1.6, 1.9); camera.fov = 42; camera.lookAt(0, 1.6, 0);
  } else if (v === 3) {
    // gait strip: 8 phases side by side, side view
    for (let i = 0; i < 8; i++) {
      const c = kids[i % kids.length] && i < 6 ? kids[i] : chars[i - 6];
      c.root.visible = true;
      c.root.position.set((i - 3.5) * 0.85, 0, 0);
      c.root.rotation.set(0, Math.PI / 2, 0);
      c.setPose(walkPose(i / 8, 1)); c.resetFace(); c.idle(0.5);
    }
    camera.position.set(0, 0.9, 9); camera.fov = 32; camera.lookAt(0, 0.8, 0);
  } else if (v === 4) {
    // sitting + arm IK reaching a marker on a desk-height point, plus head look
    const c = chars[0];
    c.root.visible = true; chair.visible = true; marker.visible = true;
    c.root.position.set(0, 0, 0); c.root.rotation.set(0, 0.0, 0);
    chair.position.set(0, SEAT_H * c.scale - 0.02, -0.02);
    c.setPose(POSES.sitDesk); c.resetFace(); c.idle(0.5);
    const k = t - v;
    const target = new THREE.Vector3(-0.12 + k * 0.3, 0.68, 0.38 + 0.1 * Math.sin(k * 6));
    marker.position.copy(target);
    const err = armIK(c, 'r', target, {});
    armIK(c, 'l', new THREE.Vector3(0.18, 0.68, 0.3), {});
    headLook(c, target, 1);
    c.applyFace(false);
    c.root.updateMatrixWorld(true);
    const wp = new THREE.Vector3(); c.J.rWrist.getWorldPosition(wp);
    const sp = new THREE.Vector3(); c.J.rShoulder.getWorldPosition(sp);
    console.log('ik err', err.toFixed(4), 'wrist', wp.toArray().map((x) => x.toFixed(3)), 'target', target.toArray().map((x) => x.toFixed(3)), 'shoulder', sp.toArray().map((x) => x.toFixed(3)));
    camera.position.set(1.2, 1.3, 1.6); camera.fov = 35; camera.lookAt(0, 0.7, 0.1);
  }
  look.uniforms.uTime.value = t;
  composer.render();
  return new Uint8Array(0);
}

const out = document.createElement('canvas'); out.width = W; out.height = H;
const og = out.getContext('2d', { willReadFrequently: true });
window.__renderAndPost = async (t, id) => {
  await view(t);
  og.drawImage(renderer.domElement, 0, 0);
  const px = og.getImageData(0, 0, W, H).data;
  await fetch('/frame/' + id, { method: 'POST', body: px });
};
window.__ready = true;
