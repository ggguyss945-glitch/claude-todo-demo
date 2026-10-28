// Hats, turbans, crowns and hair. Each builder adds outlined meshes to the head group
// (origin at the centre of the head sphere, radius R, face towards +z).
import * as THREE from 'three';
import { toon, gold, mk } from './toon.js';
import { canvas, toTex } from './tex.js';

function stripeTex(base, stripe, n = 8, wobble = 0) {
  const [c, g] = canvas(256, 256);
  g.fillStyle = base; g.fillRect(0, 0, 256, 256);
  if (stripe) {
    g.fillStyle = stripe;
    for (let i = 0; i < n; i++) { g.save(); g.translate(0, (i + 0.5) * 256 / n); g.rotate(wobble); g.fillRect(-20, -5, 300, 10); g.restore(); }
  }
  return toTex(c, { aniso: 4 });
}

export function build(h, head, R, def) {
  const f = BUILDERS[h.type];
  if (!f) throw new Error('unknown hat ' + h.type);
  f(h, head, R, def);
}

const BUILDERS = {
  turban(h, head, R) {
    const mat = toon('#ffffff', { map: stripeTex(h.color, h.stripe, h.bands || 6, 0.5), lift: 0.06 });
    const big = h.size || 1;
    const rings = [[0.58, 0.86, 0.24, 0.12], [0.78, 0.8, 0.23, -0.16], [0.96, 0.66, 0.21, 0.1]];
    for (const [y, rr, tube, tilt] of rings) {
      mk(new THREE.TorusGeometry(R * rr * big, R * tube * big, 12, 32), mat, head, { pos: [0, R * y, -R * 0.04], rot: [Math.PI / 2 + tilt, 0, tilt * 0.6], outline: 6.5 });
    }
    mk(new THREE.SphereGeometry(R * 0.76 * big, 24, 16, 0, Math.PI * 2, 0, Math.PI * 0.55), mat, head, { pos: [0, R * 0.8, -R * 0.05], scale: [1, 0.95, 1], outline: 6.5 });
    if (h.jewel) {
      mk(new THREE.SphereGeometry(R * 0.11, 16, 12), toon(h.jewel, { rough: 0.25, lift: 0.25 }), head, { pos: [0, R * 0.8, R * 0.98], outline: 4.6 });
      mk(new THREE.TorusGeometry(R * 0.13, R * 0.03, 8, 20), gold(), head, { pos: [0, R * 0.8, R * 0.96], outline: false });
    }
    if (h.feather) {
      const fm = mk(new THREE.SphereGeometry(R * 0.12, 12, 10), toon(h.feather, { lift: 0.1 }), head, { pos: [R * 0.05, R * 1.1, R * 0.62], scale: [0.6, 2.6, 0.5], rot: [0.3, 0, -0.25], outline: 4.2 });
      fm.name = 'feather';
    }
  },
  crown(h, head, R) {
    const g = gold({ rough: 0.22, glow: 0.4 });
    // velvet cap inside, gold band with points and jewels
    mk(new THREE.SphereGeometry(R * 0.8, 24, 16, 0, Math.PI * 2, 0, Math.PI * 0.5), toon(h.cap || '#b01c2c', { lift: 0.06 }), head, { pos: [0, R * 0.58, 0], scale: [1, 0.9, 1], outline: 6.1 });
    mk(new THREE.CylinderGeometry(R * 0.86, R * 0.82, R * 0.42, 32, 1, true), g, head, { pos: [0, R * 0.68, 0], outline: 6.5 });
    for (let i = 0; i < 6; i++) {
      const a = (i / 6) * Math.PI * 2;
      const x = Math.sin(a) * R * 0.84, z = Math.cos(a) * R * 0.84;
      mk(new THREE.ConeGeometry(R * 0.13, R * 0.42, 4), g, head, { pos: [x, R * 1.05, z], rot: [0, a, 0], outline: 5.4 });
      mk(new THREE.SphereGeometry(R * 0.07, 12, 10), g, head, { pos: [x, R * 1.3, z], outline: 4.6 });
      mk(new THREE.SphereGeometry(R * 0.075, 12, 10), toon(i % 2 ? '#1c9a52' : '#d4182a', { rough: 0.2, lift: 0.3 }), head, { pos: [Math.sin(a) * R * 0.89, R * 0.68, Math.cos(a) * R * 0.89], outline: 2 });
    }
  },
  kufi(h, head, R) {
    mk(new THREE.SphereGeometry(R * 1.03, 28, 16, 0, Math.PI * 2, 0, Math.PI * 0.36), toon('#ffffff', { map: stripeTex(h.color, h.stripe, 5), lift: 0.05 }), head, { pos: [0, R * 0.02, 0], outline: 6.1 });
  },
  wrap(h, head, R) {
    const mat = toon('#ffffff', { map: stripeTex(h.color, h.stripe, 4, 0.4), lift: 0.05 });
    mk(new THREE.TorusGeometry(R * 0.86, R * 0.16, 10, 28), mat, head, { pos: [0, R * 0.5, -R * 0.05], rot: [Math.PI / 2 + 0.15, 0, 0.1], outline: 3 });
    mk(new THREE.SphereGeometry(R * 0.92, 24, 14, 0, Math.PI * 2, 0, Math.PI * 0.42), mat, head, { pos: [0, R * 0.18, -R * 0.03], outline: 3 });
  },
  hijab(h, head, R) {
    const mat = toon(h.color, { lift: 0.06, side: THREE.DoubleSide });
    const g = new THREE.SphereGeometry(R * 1.1, 36, 26);
    const pos = g.getAttribute('position');
    const keep = [];
    const idx = g.getIndex();
    for (let i = 0; i < idx.count; i += 3) {
      let inside = 0;
      for (let k = 0; k < 3; k++) {
        const v = idx.getX(i + k);
        const x = pos.getX(v) / R, y = pos.getY(v) / R, z = pos.getZ(v) / R;
        if (z > 0.25 && (x * x) / 0.62 + ((y + 0.08) * (y + 0.08)) / 0.78 < 1) inside++;
      }
      if (!inside) keep.push(idx.getX(i), idx.getX(i + 1), idx.getX(i + 2));
    }
    g.setIndex(keep);
    mk(g, mat, head, { pos: [0, R * 0.02, -R * 0.02], outline: 6.5 });
    // drape over neck and shoulders
    const prof = [[0.55, 0.0], [0.75, -0.35], [0.95, -0.8], [1.12, -1.1]].map(([r, y]) => new THREE.Vector2(r * R, y * R));
    const drape = new THREE.LatheGeometry(prof, 32);
    mk(drape, mat, head, { pos: [0, -R * 0.42, -R * 0.05], outline: 6.1 });
  },
  baker(h, head, R) {
    const w = toon('#fbf8f0', { lift: 0.12 });
    mk(new THREE.CylinderGeometry(R * 0.78, R * 0.82, R * 0.45, 28), w, head, { pos: [0, R * 0.8, 0], outline: 6.1 });
    mk(new THREE.SphereGeometry(R * 0.98, 24, 16), w, head, { pos: [0, R * 1.22, 0], scale: [1, 0.62, 1], outline: 6.1 });
  },
  helmet(h, head, R) {
    const steel = new THREE.MeshStandardMaterial({ color: '#b8bcc4', metalness: 0.85, roughness: 0.32 });
    mk(new THREE.SphereGeometry(R * 1.06, 28, 18, 0, Math.PI * 2, 0, Math.PI * 0.5), steel, head, { pos: [0, R * 0.25, 0], outline: 6.1 });
    mk(new THREE.ConeGeometry(R * 0.16, R * 0.6, 12), steel, head, { pos: [0, R * 1.5, 0], outline: 5.0 });
    mk(new THREE.TorusGeometry(R * 1.02, R * 0.12, 10, 28), toon(h.wrap || '#f2efe6', { lift: 0.06 }), head, { pos: [0, R * 0.28, 0], rot: [Math.PI / 2, 0, 0], outline: 5.4 });
  },
  hair(h, head, R) {
    const mat = toon(h.color || '#1a120c', { lift: 0.02 });
    mk(new THREE.SphereGeometry(R * 1.04, 28, 16, 0, Math.PI * 2, 0, Math.PI * (h.cut || 0.4)), mat, head, { pos: [0, R * 0.02, -R * 0.02], outline: 3 });
    if (h.fringe) mk(new THREE.SphereGeometry(R * 0.3, 14, 10), mat, head, { pos: [R * 0.28, R * 0.8, R * 0.6], scale: [1.3, 0.55, 0.7], rot: [0.5, 0, -0.4], outline: 4.6 });
  },
};

// long beard for the money changer when he is old
export function longBeard(head, R, color) {
  const prof = [[0.0, -1.25], [0.18, -1.05], [0.42, -0.6], [0.55, -0.2], [0.52, 0.05]].map(([r, y]) => new THREE.Vector2(r * R, y * R));
  const g = new THREE.LatheGeometry(prof, 24, -Math.PI * 0.62, Math.PI * 1.24);
  const m = mk(g, toon(color, { lift: 0.15, side: THREE.DoubleSide }), head, { pos: [0, -R * 0.25, R * 0.28], rot: [0.25, 0, 0], scale: [1, 1, 0.8], outline: 3 });
  m.name = 'beard';
  return m;
}
