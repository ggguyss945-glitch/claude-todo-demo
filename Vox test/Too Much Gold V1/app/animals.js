// Camels (with saddle cloth and gold sacks) and a sleeping cat, in the same outlined toon style.
import * as THREE from 'three';
import { toon, gold, mk } from './toon.js';
import { Hose } from './chars.js';
import { canvas, toTex } from './tex.js';
import { coinGeometry, coinMats } from './props.js';
import { toCard } from './camel2d.js';

const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);

function blanketTex(a, b, c) {
  const [cv, g] = canvas(256, 256);
  g.fillStyle = a; g.fillRect(0, 0, 256, 256);
  g.fillStyle = b; for (let y = 0; y < 256; y += 64) g.fillRect(0, y + 20, 256, 16);
  g.fillStyle = c; for (let x = 0; x < 256; x += 32) for (let y = 0; y < 256; y += 64) { g.beginPath(); g.moveTo(x, y + 8); g.lineTo(x + 16, y); g.lineTo(x + 32, y + 8); g.lineTo(x + 16, y + 16); g.fill(); }
  g.fillStyle = c; g.fillRect(0, 236, 256, 20);
  return toTex(cv, { aniso: 4 });
}

// camel: root at the ground under the hump, facing +z
export function makeCamel(o = {}) {
  const cm = { root: new THREE.Group(), o };
  const fur = toon(o.fur || '#d6a65e', { lift: 0.05 });
  const dark = toon('#a8783a');
  const body = new THREE.Group(); cm.root.add(body); cm.body = body;
  mk(new THREE.SphereGeometry(0.5, 28, 20), fur, body, { pos: [0, 1.35, 0], scale: [0.78, 0.72, 1.45], outline: 7 });
  mk(new THREE.SphereGeometry(0.36, 24, 18), fur, body, { pos: [0, 1.72, -0.05], scale: [1, 0.85, 1.2], outline: 6.5 });
  // saddle cloth over the hump, sacks of gold on both sides
  if (o.blanket !== false) {
    const bt = blanketTex(o.cloth || '#b8262e', o.cloth2 || '#f2c24a', o.cloth3 || '#26307a');
    mk(new THREE.SphereGeometry(0.52, 28, 16, 0, Math.PI * 2, 0, Math.PI * 0.42), toon('#ffffff', { map: bt, side: THREE.DoubleSide, lift: 0.06 }), body, { pos: [0, 1.38, 0], scale: [0.86, 0.95, 1.2], outline: 5 });
  }
  if (o.sacks) {
    for (const sd of [-1, 1]) {
      const sack = new THREE.Group(); sack.position.set(sd * 0.48, 1.18, 0.05); body.add(sack);
      mk(new THREE.SphereGeometry(0.22, 18, 14), toon('#c8a46a', { lift: 0.05 }), sack, { scale: [0.75, 1.0, 0.95], outline: 5 });
      const g = coinMats().gold;
      for (let i = 0; i < 7; i++) mk(coinGeometry(), g, sack, { pos: [sd * 0.05 + (i % 3 - 1) * 0.05, 0.2 + (i % 2) * 0.02, (i - 3) * 0.035], rot: [0.4 + i, i * 0.7, 0.3], scale: 1.6, outline: false });
      mk(new THREE.SphereGeometry(0.14, 14, 10), gold({ rough: 0.3, glow: 0.4 }), sack, { pos: [sd * 0.02, 0.17, 0], scale: [1, 0.35, 1], outline: 3 });
    }
  }
  if (o.seat) { // royal seat on the hump for the king
    mk(new THREE.BoxGeometry(0.62, 0.12, 0.62), toon('#7a1a2a', { lift: 0.06 }), body, { pos: [0, 2.0, -0.05], outline: 4 });
    mk(new THREE.BoxGeometry(0.66, 0.05, 0.66), gold({ rough: 0.3 }), body, { pos: [0, 1.94, -0.05], outline: 3 });
  }
  // neck: a thick hose from chest to head, head and ears
  cm.neck = new Hose(0.13, fur, 14, 12, 0.32);
  body.add(cm.neck.mesh);
  const head = new THREE.Group(); body.add(head); cm.head = head;
  const [fc, fg] = canvas(256, 256);
  fg.fillStyle = o.fur || '#d6a65e'; fg.fillRect(0, 0, 256, 256);
  const faceTex = toTex(fc);
  // sphere UVs: the front (+z) sits at u = 0.25; circles need half the width in u
  cm.drawEyes = (lid) => {
    fg.fillStyle = o.fur || '#d6a65e'; fg.fillRect(0, 0, 256, 256);
    for (const x of [40, 88]) {
      const y = 100, rx = 17, ry = 32;
      fg.fillStyle = '#fbfbf6'; fg.beginPath(); fg.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2); fg.fill();
      fg.strokeStyle = '#141010'; fg.lineWidth = 3.5; fg.stroke();
      fg.fillStyle = '#141010'; fg.beginPath(); fg.ellipse(x, y + 9, 7, 13, 0, 0, Math.PI * 2); fg.fill();
      // heavy, unimpressed eyelid
      const ly = y - ry + 2 * ry * lid;
      fg.save(); fg.beginPath(); fg.ellipse(x, y, rx + 1, ry + 1, 0, 0, Math.PI * 2); fg.clip();
      fg.fillStyle = '#b8864a'; fg.fillRect(x - rx - 2, y - ry - 2, 2 * rx + 4, ly - (y - ry) + 2); fg.restore();
      fg.lineWidth = 4.5; fg.beginPath(); fg.moveTo(x - rx - 1, ly); fg.lineTo(x + rx + 1, ly); fg.stroke();
    }
    faceTex.needsUpdate = true;
  };
  cm.drawEyes(0.55);
  const skull = mk(new THREE.SphereGeometry(0.2, 22, 16), [toon('#ffffff', { map: faceTex })][0], head, { scale: [0.85, 0.82, 1.0], outline: 5.5 });
  // UVs of a sphere put the texture centre at the front (+z) half; good enough for two big eyes
  mk(new THREE.SphereGeometry(0.17, 20, 14), fur, head, { pos: [0, -0.07, 0.24], scale: [0.85, 0.72, 1.25], outline: 5 });
  mk(new THREE.BoxGeometry(0.16, 0.012, 0.04), toon('#3a2010'), head, { pos: [0, -0.15, 0.38], outline: false });
  for (const sd of [-1, 1]) {
    mk(new THREE.SphereGeometry(0.025, 10, 8), toon('#3a2010'), head, { pos: [sd * 0.05, -0.04, 0.44], outline: false });
    mk(new THREE.ConeGeometry(0.05, 0.12, 8), fur, head, { pos: [sd * 0.14, 0.15, -0.05], rot: [-0.3, 0, sd * 0.6], outline: 3.5 });
  }
  if (o.bridle) mk(new THREE.TorusGeometry(0.155, 0.018, 6, 20), toon(o.bridle), head, { pos: [0, -0.05, 0.22], rot: [0.2, 0, 0], scale: [1, 0.8, 1], outline: 2 });
  // legs: four hoses with knobbly knees; tail
  cm.legs = [];
  for (const [x, z] of [[-0.22, 0.45], [0.22, 0.45], [-0.22, -0.5], [0.22, -0.5]]) {
    const hose = new Hose(0.06, fur, 12, 8, 0.25); body.add(hose.mesh);
    const knee = mk(new THREE.SphereGeometry(0.075, 10, 8), fur, body, { outline: 3.5 });
    const hoof = mk(new THREE.SphereGeometry(0.09, 12, 8), dark, cm.root, { scale: [1, 0.45, 1.25], outline: 3.5 });
    cm.legs.push({ x, z, hose, knee, hoof, front: z > 0 });
  }
  cm.tail = new Hose(0.025, dark, 8, 6, 0.2); body.add(cm.tail.mesh);
  cm.pose = { walk: null, neck: 0, headPitch: 0, headYaw: 0, chew: 0, lid: 0.55, sit: 0 };
  cm.update = (t) => updateCamel(cm, t);
  toCard(cm); // drawn flat, like the people
  return cm;
}

function updateCamel(cm, t) {
  cm._t = t;
  const p = cm.pose;
  const w = p.walk; // {phase, stride}
  const sit = p.sit || 0;
  const bob = w ? Math.abs(Math.sin(w.phase * Math.PI * 2)) * 0.05 : 0;
  cm.body.position.y = bob - sit * 0.75;
  cm.body.rotation.x = w ? Math.sin(w.phase * Math.PI * 2) * 0.02 : 0;
  // neck curve
  const sway = (w ? Math.sin(w.phase * Math.PI * 2) * 0.06 : 0) + p.neck;
  const base = V(0, 1.45, 0.62), ctrl = V(0, 2.0 + sway, 1.15), headP = V(0, 2.05 + sway + p.headPitch * 0.2, 1.08 + p.neck * 0.3);
  cm.neck.update(base, ctrl, headP);
  cm.head.position.copy(headP).add(V(0, 0.05, 0.05));
  cm.head.rotation.set(0.15 + p.headPitch, p.headYaw, 0);
  if (p.chew) cm.head.children[1].position.y = -0.07 + Math.sin(t * 11) * 0.012 * p.chew;
  // legs: diagonal-free pacing gait (same-side legs move together)
  for (const L of cm.legs) {
    const side = L.x < 0 ? 0 : 0.5;
    let fz = L.z, fy = 0.04;
    if (w) {
      const ph = (w.phase + side) * Math.PI * 2;
      fz += Math.sin(ph) * w.stride * 0.5;
      fy += Math.max(0, Math.cos(ph)) * 0.16;
    }
    if (sit > 0) { fy = 0.05; fz = L.z + (L.front ? 0.25 : -0.2) * sit; }
    const hip = V(L.x * 0.9, 1.15 - sit * 0.75, L.z * 0.85);
    const foot = V(L.x, fy, fz);
    const knee = hip.clone().lerp(foot, 0.5).add(V(0, sit * 0.2, (L.front ? 0.05 : -0.05) + sit * (L.front ? 0.35 : -0.25)));
    // the hose lives in body space (body may bob): convert
    L.hipR = hip.clone(); L.kneeR = knee.clone(); L.footR = foot.clone();
    const off = V(0, cm.body.position.y, 0);
    L.hose.update(hip.clone().sub(off), knee.clone().sub(off), foot.clone().sub(off));
    L.knee.position.copy(knee).sub(off);
    L.hoof.position.copy(foot);
  }
  cm.tail.update(V(0, 1.3, -0.7), V(0, 1.1, -0.85), V(0.03 * Math.sin(t * 3), 0.85, -0.82));
  if (p.lid !== cm._lid) { cm.drawEyes(p.lid); cm._lid = p.lid; }
}

export function makeCat() {
  const g = new THREE.Group();
  const fur = toon('#e08a3a', { lift: 0.06 });
  mk(new THREE.SphereGeometry(0.16, 18, 14), fur, g, { pos: [0, 0.09, 0], scale: [1.25, 0.6, 0.95], outline: 4 });
  const head = mk(new THREE.SphereGeometry(0.085, 16, 12), fur, g, { pos: [0.17, 0.1, 0.06], outline: 4 });
  for (const sd of [-1, 1]) mk(new THREE.ConeGeometry(0.03, 0.06, 6), fur, head, { pos: [0.01, 0.075, sd * 0.045], rot: [sd * 0.3, 0, 0], outline: 2 });
  // closed eyes and stripes as little boxes
  for (const sd of [-1, 1]) mk(new THREE.BoxGeometry(0.004, 0.006, 0.03), toon('#2a1408'), head, { pos: [0.08, 0.015, sd * 0.032], rot: [0, 0, 0.2], outline: false });
  for (let i = 0; i < 4; i++) mk(new THREE.BoxGeometry(0.03, 0.005, 0.2), toon('#b8601e'), g, { pos: [-0.12 + i * 0.07, 0.185, 0], rot: [0, 0, 0.1], outline: false });
  const tail = new Hose(0.025, fur, 10, 6, 0.3); g.add(tail.mesh);
  tail.update(V(-0.18, 0.06, 0), V(-0.25, 0.04, 0.2), V(0.0, 0.03, 0.22));
  g.userData.breathe = (t) => { g.children[0].scale.y = 0.6 + Math.sin(t * 2.4) * 0.02; };
  return g;
}
