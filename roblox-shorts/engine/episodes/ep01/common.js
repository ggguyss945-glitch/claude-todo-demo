// EP01 full episode: helpers shared by part2..part5.js, plus the labelled placeholder ("stub") builder that index.js uses
// for every timeline shot whose part has not written its builder yet.
//
// The look helpers are copies of the approved test's (engine/episodes/ep01_test5.js, kept verbatim in part1.js): the TF
// sparkle look SPARK, the galaxy skies, constant-pixel sprites, the 4-point star glint, studWrap, gaze helpers, softenBeard,
// gradeBlend (in-shot grade switch). Everything is a pure function of shot time t (engine/README.md determinism rules).
import * as THREE from 'three';
import * as sets from '../../kit/sets.js';
import * as K from '../../kit/chars.js';

export const S = sets.STUD;                // 1 stud = 0.32 m
export const DEG = Math.PI / 180;
export const V3 = (a) => new THREE.Vector3(a[0], a[1], a[2]);
export const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
export const smooth = (x) => { const u = clamp01(x); return u * u * (3 - 2 * u); };
export const outExpo = (x) => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * clamp01(x)));
export const outQuad = (x) => 1 - (1 - clamp01(x)) * (1 - clamp01(x));

// ------------------------------------------------------------------ the approved look (test5)
export const SPARK = { sharpness: 7, core: 0.75, underlay: 0.55, underlayOpacity: 0.5, brightness: 2.0, px: [55, 95] };
export const GALAXY = { ...sets.SKIES.galaxy, nebula: 0.45 };
export const GALAXY_LOW = { ...sets.SKIES.galaxy, stops: [[-1, '#000000'], [-0.02, '#1c1650'], [0.12, '#140f3e'], [0.35, '#0b0828'], [0.65, '#06041a'], [1, '#030210']], nebula: 0.6, seed: 21 };

// ------------------------------------------------------------------ timeline params helpers
// Event time inside the shot (seconds from the shot start). `k` = index into params.events, or a word ("blinks"), or a
// substring of the event's `what`. Event frames in timeline.json are episode frames (frame = round(onset * 60)).
export function evT(ctx, k, fallback = null) {
  const evs = ctx.params.events || [];
  const e = typeof k === 'number' ? evs[k] : evs.find((x) => x.word === k) || evs.find((x) => (x.what || '').includes(k));
  return e ? (e.frame - ctx.shot.f0) / ctx.fps : fallback;
}
// The default camera move from params.camera.move ({ type: 'push'|'pull', Z, mode }); accent moves are the builder's job.
export function defaultMove(ctx) {
  const m = (ctx.params.camera && ctx.params.camera.move) || { type: 'push', Z: 0.19 };
  if (m.type === 'pull') ctx.camera.pull(m.Z ?? 0.1, { mode: m.mode });
  else ctx.camera.push(m.Z ?? m.base_push ?? 0.19, { mode: m.mode || 'fov' });
  const r = ctx.params.camera && ctx.params.camera.roll; if (r) ctx.camera.rollBy(r.deg[1] - r.deg[0]);
  return m;
}

// ------------------------------------------------------------------ sprites, glint, gaze (copied from the approved test)
export function pxSprite(mat, px = 40, aspect = 1) {
  const s = new THREE.Sprite(mat); s.userData.px = px; s.userData.aspect = aspect;
  s.onBeforeRender = function (r, sc, cam) { const k = (this.userData.px * 2) / (1920 * cam.projectionMatrix.elements[5]); this.scale.set(k, k * this.userData.aspect, 1); this.updateMatrixWorld(); };
  return s;
}
export const addSpriteMat = (map, color, k = 1, o = {}) => new THREE.SpriteMaterial({ map, color: new THREE.Color(color).multiplyScalar(k), blending: THREE.AdditiveBlending, depthWrite: false, depthTest: false, transparent: true, fog: false, sizeAttenuation: false, ...o });
export function starGlint(ctx, { pos, t0, peak = 110, rot = 25, color = '#f4ecff' }) {
  const mat = addSpriteMat(ctx.tex.sparkle({ points: 4, sharpness: 22, core: 0.6 }), color, 2.4);
  const s = pxSprite(mat, 0); s.position.copy(pos); s.renderOrder = 30; s.visible = false;
  const core = pxSprite(addSpriteMat(ctx.tex.radialGlow({ falloff: 2.2 }), '#fff4ff', 1.6), 0);
  core.position.copy(pos); core.renderOrder = 29; core.visible = false;
  const g = new THREE.Group(); g.add(core, s);
  g.update = (t) => {
    const f = (t - t0) * 60; const on = f > -0.5 && f < 16.5; s.visible = core.visible = on; if (!on) return;
    const k = f < 3 ? (f + 1) / 4 : Math.pow(1 - (f - 3) / 13.5, 1.6);
    s.userData.px = peak * k; core.userData.px = peak * 0.42 * k; mat.rotation = rot * DEG * clamp01(f / 16); s.material.opacity = 1; core.material.opacity = 0.7 * k;
  };
  g.update(-1); return g;
}
export function studWrap(obj) { const w = new THREE.Group(); w.scale.setScalar(S); w.add(obj); return w; }
export function eyesOf(g) { g.updateWorldMatrix(true, true); return g.getObjectByName('ballL').getWorldPosition(new THREE.Vector3()).add(g.getObjectByName('ballR').getWorldPosition(new THREE.Vector3())).multiplyScalar(0.5); }
export function gazeAt(g, worldPt, extraPitch = 0) {
  const e = eyesOf(g); const a = g.worldToLocal(e.clone()), b = g.worldToLocal(worldPt.clone()); const d = b.sub(a);
  K.setGnomeGaze(g, Math.atan2(d.x, d.z) / DEG, Math.atan2(d.y, Math.hypot(d.x, d.z)) / DEG + extraPitch);
}
export function softenBeard(g) { g.traverse((o) => { if (o.isMesh && o.material && o.material.bumpMap && Math.abs(o.material.bumpScale - 1.4) < 1e-6) { o.material = o.material.clone(); o.material.bumpScale = 0.8; } }); }

// In-shot grade switch (bible P3: over 6-10 frames on the beat word). const B = gradeBlend(fromGrade, toGrade); B(ctx.post.params.grade, u)
const hexArr = (h) => { const c = new THREE.Color(); c.setStyle(h, THREE.NoColorSpace); return [c.r, c.g, c.b]; };
const lerpArr = (a, b, k) => a.map((x, i) => x + (b[i] - x) * k);
const GRADE_NUM = ['temperature', 'tint', 'contrast', 'pivot', 'saturation', 'shadowsAmount', 'highlightsAmount', 'balance'];
const GRADE_COL = ['shadows', 'highlights', 'outBlack', 'outWhite'];
export function gradeBlend(A, B) {
  const a = {}, b = {};
  for (const k of GRADE_NUM) { a[k] = A[k] ?? (k === 'contrast' || k === 'saturation' ? 1 : k === 'pivot' ? 0.45 : 0); b[k] = B[k] ?? (k === 'contrast' || k === 'saturation' ? 1 : k === 'pivot' ? 0.45 : 0); }
  for (const k of GRADE_COL) { a[k] = hexArr(A[k] || (k === 'outWhite' ? '#ffffff' : '#000000')); b[k] = hexArr(B[k] || (k === 'outWhite' ? '#ffffff' : '#000000')); }
  return (G, k) => { for (const n of GRADE_NUM) G[n] = a[n] + (b[n] - a[n]) * k; for (const n of GRADE_COL) G[n] = lerpArr(a[n], b[n], k); };
}

// ------------------------------------------------------------------ the placeholder (stub) builder
// A flat card that fills the frame: shot id, builder key and owner part, the words, the picture note, size/angle/move,
// the grade colour, the caption band, and a progress bar with the shot's events ticking on their frames. The camera
// performs the shot's push/pull so the edit rhythm and the colour script read in a stills sheet or a draft render.
const STUB_BG = { night: ['#1d1b45', '#0a0820'], nightHigh: ['#262463', '#0d0b2a'], porch: ['#3a2440', '#140a18'], bedroom: ['#3a1f4a', '#160a1c'], magic: ['#7a3e2a', '#2a1008'],
  dawn: ['#c88a8a', '#5a3a4a'], day: ['#5a86c8', '#24406a'], dusk: ['#b0603a', '#3a1a12'], sepia: ['#7a5a40', '#2a1c12'], bw: ['#6a6a6a', '#202020'] };
function wrap(g, text, x, y, maxW, lh, maxLines = 99) {
  const words = String(text || '').split(/\s+/); let line = '', n = 0;
  for (const w of words) {
    const tryL = line ? line + ' ' + w : w;
    if (g.measureText(tryL).width > maxW && line) { g.fillText(line, x, y + n * lh); line = w; if (++n >= maxLines) return n; } else line = tryL;
  }
  if (line) { g.fillText(line, x, y + n * lh); n++; }
  return n;
}
function stubCard(ctx, key, part, built) {
  const p = ctx.params; const W = 540, H = 960; const grade = p.post || p.grade_preset || 'night';
  const c = document.createElement('canvas'); c.width = W; c.height = H; const g = c.getContext('2d');
  const [c0, c1] = STUB_BG[grade] || STUB_BG.night; const grd = g.createLinearGradient(0, 0, 0, H); grd.addColorStop(0, c0); grd.addColorStop(1, c1);
  g.fillStyle = grd; g.fillRect(0, 0, W, H);
  g.strokeStyle = 'rgba(255,255,255,0.18)'; g.lineWidth = 2; g.strokeRect(54, 96, W - 108, H - 192);   // inner 80 %: survives the push
  const F = (px, w = 'bold') => `${w} ${px}px "DejaVu Sans", Arial, sans-serif`;
  g.textAlign = 'center'; g.fillStyle = '#ffffff';
  g.font = F(76); g.fillText(ctx.shot.name, W / 2, 190);
  g.font = F(24); g.fillStyle = '#ffe2a8'; g.fillText(key, W / 2, 226);
  g.font = F(17, 'normal'); g.fillStyle = 'rgba(255,255,255,0.75)';
  g.fillText(`part ${p.part}  ·  builder: part${part}.js  ·  ${built ? '' : 'PLACEHOLDER'}`, W / 2, 252);
  g.font = F(30); g.fillStyle = '#ffffff'; const nw = wrap(g, p.words ? `"${p.words}"` : '(silent)', W / 2, 300, W - 130, 36, 3);
  g.textAlign = 'left'; g.font = F(17, 'normal'); g.fillStyle = 'rgba(255,255,255,0.92)';
  const lines = (p.stub && p.stub.lines) || [p.pic || p.beat || ''];
  let y = 316 + nw * 36; y += 22 * wrap(g, lines[0], 74, y, W - 148, 22, 12) + 10;
  g.fillStyle = '#c8d8ff'; for (const l of lines.slice(1)) { y += 22 * wrap(g, l, 74, y, W - 148, 22, 4) + 4; }
  g.fillStyle = 'rgba(255,255,255,0.7)'; y += 4; wrap(g, `grade ${grade}  ·  ${p.light || ''}`, 74, y, W - 148, 22, 2);
  // caption band (y 1260-1420 of 1920): keep it free
  g.fillStyle = 'rgba(255,255,255,0.07)'; g.fillRect(0, 630, W, 80); g.fillStyle = 'rgba(255,255,255,0.35)'; g.font = F(13, 'normal'); g.textAlign = 'center'; g.fillText('caption band', W / 2, 676);
  return c;
}
export function stubBuilder(key, part, built = false) {
  return {
    quality: { shadows: 'off' },
    build(ctx) {
      const p = ctx.params; const grade = p.post || p.grade_preset || 'night';
      try { ctx.post.set(sets.postPreset(grade, { exposure: 1.0, bloom: { enabled: false } })); } catch (e) { /* unknown preset: keep the episode post */ }
      ctx.post.set({ grade: { enabled: false } });          // keep the card readable; the background colour carries the grade family
      const base = stubCard(ctx, key, part, built);
      const c = document.createElement('canvas'); c.width = base.width; c.height = base.height;
      const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; tex.minFilter = THREE.LinearFilter; tex.generateMipmaps = false;
      const D = 2, fov = 70, h = 2 * D * Math.tan((fov / 2) * DEG), w = (h * 9) / 16;
      const card = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: tex, toneMapped: false, fog: false }));
      card.position.set(0, 0, -D); ctx.add(card);
      ctx.camera.set({ pos: [0, 0, 0], target: [0, 0, -1], fov });
      const m = (p.camera && p.camera.move) || { type: 'push', Z: 0.19 };
      const Z = Math.min(0.35, m.Z ?? m.base_push ?? 0.19);    // capped so the card stays readable (accent moves are the builder's job)
      if (m.type === 'pull') ctx.camera.pull(Math.min(0.35, m.Z ?? 0.3)); else ctx.camera.push(Z);
      const evs = (p.events || []).map((e) => ({ t: (e.frame - ctx.shot.f0) / ctx.fps, what: e.what || '', word: e.word || '' }));
      ctx.shared.stub = { base, c, g: c.getContext('2d'), tex, evs };
    },
    update(ctx, t) {
      const st = ctx.shared.stub; const g = st.g; const W = st.c.width; const dur = ctx.shot.duration;
      g.drawImage(st.base, 0, 0);
      const x0 = 74, x1 = W - 74, yb = 790;                 // progress bar with event ticks
      g.fillStyle = 'rgba(255,255,255,0.22)'; g.fillRect(x0, yb, x1 - x0, 8);
      g.fillStyle = '#ffe2a8'; g.fillRect(x0, yb, (x1 - x0) * Math.min(1, t / dur), 8);
      g.font = 'bold 15px "DejaVu Sans", Arial, sans-serif'; g.textAlign = 'left';
      st.evs.forEach((e, i) => {
        const x = x0 + (x1 - x0) * Math.min(1, Math.max(0, e.t / dur)); const hot = t >= e.t && t < e.t + 0.25;
        g.fillStyle = hot ? '#ff7a5a' : t >= e.t ? '#ffe2a8' : 'rgba(255,255,255,0.6)'; g.fillRect(x - 2, yb - 10, 4, 28);
        g.fillText(`${hot ? '>> ' : ''}${(ctx.shot.start + e.t).toFixed(2)} ${e.word ? '"' + e.word + '" ' : ''}${e.what}`.slice(0, 64), x0, yb + 40 + i * 20);
      });
      g.fillStyle = 'rgba(255,255,255,0.8)'; g.textAlign = 'right';
      g.fillText(`${(ctx.shot.start + t).toFixed(2)} s  (${t.toFixed(2)} / ${dur.toFixed(2)})`, x1, yb - 16);
      st.tex.needsUpdate = true;
    },
  };
}
