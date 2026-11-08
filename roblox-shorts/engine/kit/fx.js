// Magic air and local light for the suburb kit (VISUAL_BIBLE §1 rule 9, §5, §6.3). All units METRES. Every effect is a
// pure function of shot time: call `fx.update(t)` from the shot's update(ctx, t) (no accumulated state).
//
//   const sp = sparkles(ctx, { center: [0, 1, 0], size: [3, 2, 2], count: 10 }); ctx.add(sp);   // update: sp.update(t)
//   const b  = burst(ctx, { pos: [0, 0.6, 0], t0: 1.2 }); ctx.add(b);                             // 0.35 s snap/transform
//
// Sprite sizes given in `px` are OUTPUT pixels of the 1080x1920 frame (constant on screen whatever the distance; they
// follow the zoom-push because they scale with 1/tan(fov/2)). Sizes given in metres are world sizes.
import * as THREE from 'three';
import { makeRng, hash32 } from '../core/random.js';
import { ringTex } from './kitlib.js';

const REF_H = 1920; // output pixel reference
const _scale = (px, cam) => (px * 2) / (REF_H * cam.projectionMatrix.elements[5]);
// A sprite whose on-screen size is `userData.px` output pixels (set userData.px each frame in update).
function pxSprite(mat) {
  const s = new THREE.Sprite(mat); s.userData.px = 40;
  s.onBeforeRender = function (renderer, scene, cam) { const k = _scale(this.userData.px, cam); this.scale.set(k, k, 1); this.updateMatrixWorld(); };
  return s;
}
const addMat = (map, color, o = {}) => new THREE.SpriteMaterial({ map, color, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, fog: false, sizeAttenuation: false, ...o });
const hdr = (hex, k) => new THREE.Color(hex).multiplyScalar(k);
const fract = (x) => x - Math.floor(x);
const smooth01 = (x) => { const u = Math.min(1, Math.max(0, x)); return u * u * (3 - 2 * u); };

// ---------------------------------------------------------------- sparkles (TF signature glints)
// 6-to-8-point white-lavender glints (some peach), 40-80 px, drifting 20-60 px/s up and sideways, twinkling
// (opacity 0.35-1, scale 0.6-1.2 on a 0.6-1.2 s sine with random phase), slow rotation. Outdoors use 6-12, indoors 8-20.
// center/size: the box they live in (they wrap around inside it, fading at the wrap so nothing pops).
// drift: metres/s (0.04-0.1 m/s reads as 20-60 px/s at 2-5 m with a 70° lens).
// sharpness/core shape the star texture (16/0.55 = thin hard asterisks; TF's soft fat snowflakes are about 7/0.75);
// underlay > 0 adds a soft radialGlow under each glint (size = underlay x the glint, opacity = underlayOpacity).
export function sparkles(ctx, { center = [0, 1, 0], size = [3, 2, 2], count = 10, px = [40, 80], colors = ['#e9dcff', '#e9dcff', '#e9dcff', '#ffe2c4'], points = [6, 8], drift = [0.04, 0.1], brightness = 1.6, seed = 'sparkles', rotSpeed = 0.35, sharpness = 16, core = 0.55, underlay = 0, underlayOpacity = 0.5, renderOrder = 0 } = {}) {
  const g = new THREE.Group(); g.name = 'sparkles'; const r = makeRng(hash32(seed, count, center.join(',')));
  const maps = Object.fromEntries(points.map((p) => [p, ctx.tex.sparkle({ points: p, sharpness, core })]));
  const glowMap = underlay > 0 ? ctx.tex.radialGlow({ falloff: 2.0 }) : null; const glints = [];
  for (let i = 0; i < count; i++) {
    const pts = points[i % points.length]; const col = colors[Math.floor(r() * colors.length)]; const s = pxSprite(addMat(maps[pts], hdr(col, brightness)));
    const ang = r() * Math.PI * 2, sp = drift[0] + (drift[1] - drift[0]) * r();
    s.userData.d = { p: [r(), r(), r()], v: [Math.cos(ang) * sp * 0.6, sp * (0.6 + 0.4 * r()), Math.sin(ang) * sp * 0.3], per: 0.6 + r() * 0.6, ph: r(), px: px[0] + (px[1] - px[0]) * r(), rot: r() * Math.PI, rs: (r() - 0.5) * rotSpeed * 2 };
    if (glowMap) { const u = pxSprite(addMat(glowMap, hdr(col, brightness * 0.6))); u.renderOrder = renderOrder; s.userData.under = u; g.add(u); }
    s.renderOrder = renderOrder + 1; glints.push(s); g.add(s);
  }
  g.update = (t) => {
    for (const s of glints) {
      const d = s.userData.d; let edge = 1;
      for (let k = 0; k < 3; k++) { const u = fract(d.p[k] + (d.v[k] * t) / size[k]); edge = Math.min(edge, smooth01(u / 0.12), smooth01((1 - u) / 0.12)); s.position.setComponent(k, center[k] + (u - 0.5) * size[k]); }
      const tw = 0.5 + 0.5 * Math.sin(((t / d.per) + d.ph) * Math.PI * 2);
      s.userData.px = d.px * (0.6 + 0.6 * tw); s.material.opacity = (0.35 + 0.65 * tw) * edge; s.material.rotation = d.rot + d.rs * t;
      const u = s.userData.under; if (u) { u.position.copy(s.position); u.userData.px = s.userData.px * underlay; u.material.opacity = s.material.opacity * underlayOpacity; }
    }
  };
  g.update(0); return g;
}

// ---------------------------------------------------------------- magic dust (gold/pink motes around a source)
// Small soft motes and pink 4-point twinkles orbiting/rising around `center` (a lantern, a wand, the gnome).
export function magicDust(ctx, { center = [0, 1, 0], radius = 0.5, height = 0.8, count = 30, colors = ['#ffd27a', '#ffb070', '#ff9ad5', '#fff2d8'], px = [8, 22], twinkles = 0.3, rise = 0.12, swirl = 0.5, brightness = 2, seed = 'dust' } = {}) {
  const g = new THREE.Group(); g.name = 'magicDust'; const r = makeRng(hash32(seed, count));
  const mote = ctx.tex.radialGlow({ falloff: 1.6 }), star = ctx.tex.sparkle({ points: 4, sharpness: 22, core: 0.6 });
  for (let i = 0; i < count; i++) {
    const tw = r() < twinkles; const s = pxSprite(addMat(tw ? star : mote, hdr(colors[Math.floor(r() * colors.length)], brightness)));
    s.userData.d = { a: r() * Math.PI * 2, rr: radius * (0.25 + 0.75 * Math.sqrt(r())), h: r(), w: swirl * (0.5 + r()) * (r() < 0.5 ? -1 : 1), px: (px[0] + (px[1] - px[0]) * r()) * (tw ? 2.2 : 1), per: 0.5 + r() * 0.8, ph: r(), tw };
    g.add(s);
  }
  g.update = (t) => {
    for (const s of g.children) {
      const d = s.userData.d; const u = fract(d.h + (rise * t) / height); const a = d.a + d.w * t;
      s.position.set(center[0] + Math.cos(a) * d.rr * (1 - 0.3 * u), center[1] + (u - 0.15) * height, center[2] + Math.sin(a) * d.rr * (1 - 0.3 * u));
      const k = 0.5 + 0.5 * Math.sin(((t / d.per) + d.ph) * Math.PI * 2);
      s.userData.px = d.px * (0.7 + 0.5 * k); s.material.opacity = (0.4 + 0.6 * k) * smooth01(u / 0.15) * smooth01((1 - u) / 0.3); if (d.tw) s.material.rotation = a;
    }
  };
  g.update(0); return g;
}

// ---------------------------------------------------------------- VFX burst (0.3-0.4 s; snaps, transformations, puffs)
// 20-40 sparkles flying out (outExpo) and fading, an expanding white ring sprite, a bright core flash, optional puff
// motes (dandelion). Pure function of t; nothing shows before t0 or after t0 + dur + tail.
export function burst(ctx, { pos = [0, 1, 0], t0 = 0, dur = 0.35, count = 28, spread = 0.7, px = [30, 70], ring = true, ringPx = [40, 620], ringColor = '#f4ecff', colors = ['#ffffff', '#e9dcff', '#ffe2c4'], core = true, corePx = 260, brightness = 2.2, puff = 0, puffColor = '#f4f0ea', gravity = -0.3, seed = 'burst' } = {}) {
  const g = new THREE.Group(); g.name = 'burst'; const r = makeRng(hash32(seed, pos.join(','), t0));
  const spk = ctx.tex.sparkle({ points: 6, sharpness: 16, core: 0.6 }), spk4 = ctx.tex.sparkle({ points: 4, sharpness: 22, core: 0.6 }), mote = ctx.tex.radialGlow({ falloff: 1.4 });
  const P0 = new THREE.Vector3(...pos);
  for (let i = 0; i < count + puff; i++) {
    const isPuff = i >= count; const s = pxSprite(addMat(isPuff ? mote : (r() < 0.6 ? spk : spk4), hdr(isPuff ? puffColor : colors[Math.floor(r() * colors.length)], isPuff ? 1.1 : brightness), isPuff ? { blending: THREE.NormalBlending } : {}));
    const th = r() * Math.PI * 2, ph = Math.acos(2 * r() - 1); const v = new THREE.Vector3(Math.sin(ph) * Math.cos(th), Math.cos(ph) * 0.8 + 0.25, Math.sin(ph) * Math.sin(th)).multiplyScalar(spread * (0.4 + 0.6 * r()) * (isPuff ? 1.6 : 1));
    s.userData.d = { v, px: (px[0] + (px[1] - px[0]) * r()) * (isPuff ? 0.35 : 1), life: (isPuff ? 1.6 : 1) * (0.7 + 0.6 * r()), rot: r() * 6, puff: isPuff }; s.visible = false; g.add(s);
  }
  let ringS = null, coreS = null;
  if (ring) { ringS = pxSprite(addMat(ringTex(), hdr(ringColor, 1.8))); ringS.position.copy(P0); ringS.visible = false; g.add(ringS); }
  if (core) { coreS = pxSprite(addMat(ctx.tex.radialGlow({ falloff: 2 }), hdr('#fff6ec', 2.2))); coreS.position.copy(P0); coreS.visible = false; g.add(coreS); }
  const outExpo = (u) => (u >= 1 ? 1 : 1 - Math.pow(2, -10 * u));
  g.update = (t) => {
    const u = (t - t0) / dur;
    for (const s of g.children) {
      if (s === ringS || s === coreS) continue; const d = s.userData.d; const ul = (t - t0) / (dur * d.life * (d.puff ? 3 : 1.6));
      if (ul < 0 || ul > 1) { s.visible = false; continue; } s.visible = true;
      const k = outExpo(ul); s.position.copy(P0).addScaledVector(d.v, k).add(new THREE.Vector3(0, gravity * ul * ul * (d.puff ? -0.3 : 1), 0));
      s.userData.px = d.px * (d.puff ? 1 : 1.2 - 0.6 * ul); s.material.opacity = Math.min(1, (1 - ul) * 1.6); s.material.rotation = d.rot + ul * 2;
    }
    if (ringS) { ringS.visible = u >= 0 && u <= 1; if (ringS.visible) { ringS.userData.px = ringPx[0] + (ringPx[1] - ringPx[0]) * outExpo(u); ringS.material.opacity = (1 - u) * (1 - u); } }
    if (coreS) { const uc = u / 0.45; coreS.visible = uc >= 0 && uc <= 1; if (coreS.visible) { coreS.userData.px = corePx * (0.6 + 0.6 * uc); coreS.material.opacity = (1 - uc) * (1 - uc) * 0.9; } }
  };
  g.update(-1); return g;
}

// ---------------------------------------------------------------- local glows and light decals
// Soft local glow sprite (lamp halos, window glows, lantern halos). size in metres (world) or px (screen-constant).
export function glow(ctx, { pos = [0, 1, 0], color = '#ffd9a0', size = 0.6, px = null, opacity = 0.6, intensity = 1, falloff = 2.4 } = {}) {
  const mat = new THREE.SpriteMaterial({ map: ctx.tex.radialGlow({ falloff }), color: hdr(color, intensity), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, opacity, fog: true, sizeAttenuation: px == null });
  const s = px == null ? new THREE.Sprite(mat) : pxSprite(mat); if (px == null) s.scale.set(size, size, 1); else s.userData.px = px;
  s.position.set(...pos); s.name = 'glow'; s.renderOrder = 5; return s;
}
// Additive light pool on the ground (lamp pools on the road, lantern pools on the lawn). radius in metres.
export function lightPool(ctx, { pos = [0, 0, 0], radius = 1.8, color = '#ffb870', opacity = 0.3, falloff = 1.6, squash = 1 } = {}) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(radius * 2, radius * 2 * squash), new THREE.MeshBasicMaterial({ map: ctx.tex.radialGlow({ falloff }), color, transparent: true, opacity, blending: THREE.AdditiveBlending, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4, fog: true }));
  m.rotation.x = -Math.PI / 2; m.position.set(pos[0], pos[1] + 0.012, pos[2]); m.name = 'lightPool'; m.renderOrder = 2; return m;
}
// Fake contact shadow under a character/gnome (VISUAL_BIBLE §5: radial decal, opacity 0.3-0.4, 1.2x the footprint).
export function contactShadow(ctx, { pos = [0, 0, 0], radius = 0.3, opacity = 0.35, color = '#0a0612' } = {}) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(radius * 2, radius * 2), new THREE.MeshBasicMaterial({ map: ctx.tex.radialGlow({ falloff: 1.2 }), color, transparent: true, opacity, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4 }));
  // radialGlow is white with alpha: use it as alphaMap-like via map alpha; colour multiplies to dark
  m.rotation.x = -Math.PI / 2; m.position.set(pos[0], pos[1] + 0.01, pos[2]); m.name = 'contactShadow'; m.renderOrder = 1; return m;
}
// Expanding ground ring (property-line shimmer, FWOOM ring rolling over the lawn): additive flat ring, world size.
export function groundRing(ctx, { pos = [0, 0, 0], t0 = 0, dur = 1.2, r0 = 0.2, r1 = 3, color = '#ffd8a0', opacity = 0.8 } = {}) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.MeshBasicMaterial({ map: ringTex(), color: hdr(color, 1.5), transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -4 }));
  m.rotation.x = -Math.PI / 2; m.position.set(pos[0], pos[1] + 0.02, pos[2]); m.visible = false; m.name = 'groundRing';
  m.update = (t) => { const u = (t - t0) / dur; m.visible = u >= 0 && u <= 1; if (!m.visible) return; const s = r0 + (r1 - r0) * (1 - Math.pow(1 - u, 2)); m.scale.set(s, s, 1); m.material.opacity = opacity * Math.sin(Math.PI * Math.min(1, u * 1.4)) * (1 - u); };
  return m;
}
// Collect everything with an update(t) under a root and call it (convenience for shots).
export function updateAll(root, t) { root.traverse((o) => { if (typeof o.update === 'function' && o !== root) o.update(t); }); }
