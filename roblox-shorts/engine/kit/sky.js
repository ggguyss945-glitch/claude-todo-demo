// Skies for the suburb kit (VISUAL_BIBLE §4.5): night galaxy (TF, our default), black void with stars (AW/PN), moon
// (TF blue-violet crater sphere look or AW white disc with halo), dusk, blue hour, dawn, day, plus distant mountain
// silhouettes. Domes are in METRES and centred on the world origin (radius 400 < camera far 1000), `fog: false`.
//
//   ctx.add(sky(ctx, { preset: 'galaxy', moon: { az: -35, el: 32, size: 7, style: 'tf' } }));
//
// az/el are degrees: az 0 = toward -Z (the default camera look direction), positive az turns toward +X; el above horizon.
import { THREE, moonTex, persistTree, STUD } from './kitlib.js';

// Gradient stops are [elevation -1..1, '#hex'] (texture colour, before the grade).
export const SKIES = {
  // TF galaxy night: black zenith, deep-violet horizon, magenta/purple nebula wisps, dense small stars. Sky luma 0-10 graded.
  galaxy: { stops: [[-1, '#000000'], [-0.02, '#0a0722'], [0.08, '#07051a'], [0.4, '#030110'], [1, '#000002']], stars: 3200, nebula: 0.3, nebulaColors: ['#46134d', '#3a2988'], seed: 21 },
  // AW/PN void: pure black with small grey-white stars (no nebula).
  void: { stops: [[-1, '#000000'], [0, '#020208'], [1, '#000000']], stars: 2600, nebula: 0, seed: 22 },
  // PN dusk (cool): teal-grey zenith to brown-orange horizon.
  duskPN: { stops: [[-1, '#2a201c'], [0, '#77594e'], [0.25, '#4f4a46'], [1, '#373d3b']], stars: 120, nebula: 0, seed: 23 },
  // EP01 frame-1 dusk (warm, CG-like): amber-orange horizon, violet zenith.
  dusk: { stops: [[-1, '#3a1c12'], [0, '#e98a3c'], [0.08, '#d9733a'], [0.22, '#a9586a'], [0.5, '#5a4078'], [1, '#2c2d5c']], stars: 60, nebula: 0, seed: 24 },
  // PN blue hour: saturated blue fading to a peach horizon, a few faint stars.
  blueHour: { stops: [[-1, '#2a2a3a'], [0, '#d1ad7d'], [0.12, '#7f93b8'], [0.35, '#4f84b0'], [1, '#3e64b7']], stars: 220, nebula: 0, seed: 25 },
  // EP01 pink dawn: periwinkle zenith -> mauve -> peach horizon.
  dawn: { stops: [[-1, '#6a4a5a'], [0, '#f8cba4'], [0.12, '#e9b6b0'], [0.3, '#c39cc4'], [1, '#5d74c4']], stars: 40, nebula: 0, seed: 26 },
  // Roblox default day.
  day: { stops: [[-1, '#55b1d9'], [0, '#55b1d9'], [1, '#258edf']], stars: 0, nebula: 0, seed: 27 },
};

const dir = (az, el, r = 1) => { const a = (az * Math.PI) / 180, e = (el * Math.PI) / 180; return new THREE.Vector3(Math.sin(a) * Math.cos(e) * r, Math.sin(e) * r, -Math.cos(a) * Math.cos(e) * r); };
export const skyDir = dir;

// Moon. style 'tf': big blue-violet crater disc (#3f43a9-#6161d3 after the grade); 'aw': white disc #e9f6ff with a
// ~25 px halo. size = angular diameter in degrees (Roblox moons are big: 4-10).
export function moon(ctx, { az = -30, el = 30, size = 6, style = 'tf', color = null, intensity = null, halo = true, distance = 360 } = {}) {
  const g = new THREE.Group(); g.name = 'moon';
  const D = distance, s = 2 * D * Math.tan(((size * Math.PI) / 180) / 2);
  const col = new THREE.Color(color || (style === 'tf' ? '#8a8ff0' : '#e9f6ff')).multiplyScalar(intensity ?? (style === 'tf' ? 0.85 : 1.25));
  const m = new THREE.Sprite(new THREE.SpriteMaterial({ map: moonTex(), color: col, fog: false, depthWrite: false, transparent: true }));
  m.scale.set(s, s, 1); m.renderOrder = -990; m.name = 'moonDisc'; g.add(m);
  if (halo) {
    const h = new THREE.Sprite(new THREE.SpriteMaterial({ map: ctx.tex.radialGlow({ falloff: 2.4 }), color: new THREE.Color(style === 'tf' ? '#6c6ee0' : '#cfe0ff').multiplyScalar(style === 'tf' ? 0.35 : 0.5), fog: false, depthWrite: false, transparent: true, blending: THREE.AdditiveBlending }));
    h.scale.set(s * 2.6, s * 2.6, 1); h.renderOrder = -991; h.name = 'moonHalo'; g.add(h);
  }
  g.position.copy(dir(az, el, D)); g.userData.dir = dir(az, el).toArray();
  return g;
}
// Sun disc (dawn/dusk/day): core + wide glow, HDR colour so it blooms gently.
export function sunDisc(ctx, { az = 30, el = 6, size = 3.5, color = '#fff0d8', intensity = 3, glow = 0.6, distance = 360 } = {}) {
  const g = new THREE.Group(); g.name = 'sun'; const D = distance, s = 2 * D * Math.tan(((size * Math.PI) / 180) / 2);
  const core = new THREE.Sprite(new THREE.SpriteMaterial({ map: ctx.tex.radialGlow({ falloff: 0.6 }), color: new THREE.Color(color).multiplyScalar(intensity), fog: false, depthWrite: false, transparent: true, blending: THREE.AdditiveBlending }));
  core.scale.set(s, s, 1); core.renderOrder = -989; g.add(core);
  const halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: ctx.tex.radialGlow({ falloff: 3 }), color: new THREE.Color(color).multiplyScalar(glow), fog: false, depthWrite: false, transparent: true, blending: THREE.AdditiveBlending }));
  halo.scale.set(s * 9, s * 9, 1); halo.renderOrder = -990; g.add(halo);
  g.position.copy(dir(az, el, D)); g.userData.dir = dir(az, el).toArray(); return g;
}
// Distant low-poly mountain ridge ring (silhouettes). At night keep it near the horizon colour (barely visible).
export function mountains(ctx, { color = '#0b0920', distance = 300, height = 28, seed = 3, arc = [0, 360] } = {}) {
  return ctx.cache('kit:mountains:' + [color, distance, height, seed, arc].join(','), () => {
    const segs = 160, P = [], I = []; const r = ctx.rngFor('mountains' + seed);
    const hs = []; for (let i = 0; i <= segs; i++) hs.push(i);
    let h = 0.5; const prof = hs.map(() => { h = Math.min(1, Math.max(0.15, h + (r() - 0.5) * 0.35)); return h; });
    for (let i = 0; i <= segs; i++) {
      const a = ((arc[0] + ((arc[1] - arc[0]) * i) / segs) * Math.PI) / 180, x = Math.sin(a) * distance, z = -Math.cos(a) * distance;
      P.push(x, -5, z, x, prof[i] * height * (0.6 + 0.4 * Math.sin(i * 0.37 + seed)), z);
      if (i < segs) { const k = i * 2; I.push(k, k + 2, k + 1, k + 1, k + 2, k + 3); }
    }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3)); g.setIndex(I);
    const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color, fog: false, side: THREE.DoubleSide })); m.renderOrder = -980; m.name = 'mountains'; return m;
  }).clone();
}

// sky(ctx, { preset, moon, sun, mountains, rotation, radius, intensity }) -> Group (dome [+ moon] [+ sun] [+ ridge]).
// preset: a SKIES key or a custom { stops, stars, nebula, nebulaColors, seed }.
export function sky(ctx, { preset = 'galaxy', moon: mo = null, sun = null, mountains: mt = null, rotation = 0, radius = 400, intensity = 1, width = 2048 } = {}) {
  const P = typeof preset === 'string' ? SKIES[preset] : preset; if (!P) throw new Error('unknown sky ' + preset);
  const g = new THREE.Group(); g.name = 'sky:' + (typeof preset === 'string' ? preset : 'custom');
  const t = ctx.tex.starSky({ width, ...P });
  g.add(ctx.tex.skyDome(t, { radius, fog: false, rotation, intensity }));
  if (mo) g.add(moon(ctx, mo === true ? {} : mo));
  if (sun) g.add(sunDisc(ctx, sun === true ? {} : sun));
  if (mt) g.add(mountains(ctx, mt === true ? {} : mt));
  return g;
}
export { STUD };
