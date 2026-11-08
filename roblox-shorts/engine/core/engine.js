// Shot/timeline engine. An episode module exports { shots: [...] } (and optionally a timeline JSON); each frame i is
// rendered from scratch as a pure function of i: T = i/fps, shot = the shot covering frame i, t = shot-local seconds.
import * as THREE from 'three';
import { createRenderer, applyQuality, setFog, hookSceneMaterials, lights, addLight, disposeTree, markTreePersistent, markPersistent } from './scene.js';
import { Post, deepMerge } from './post.js';
import { ShotCamera } from './camera.js';
import * as anim from './anim.js';
import * as tex from './textures.js';
import { makeRng, hash32, seedMathRandom } from './random.js';

// Global quality presets (render.js `quality=`). Shots set their own `quality` on top; the preset caps it.
// scale = output resolution factor; renderScale = 3D scene render-target factor (multiplies the shot's own
// post.renderScale); msaa = scene MSAA samples (SwiftShader: 2x costs the same as 4x).
export const QUALITY = {
  final: { scale: 1, renderScale: 1, msaa: 4, aa: 'msaa', shadowScale: 1, dofQuality: null },
  balanced: { scale: 1, renderScale: 0.85, msaa: 4, aa: 'msaa', shadowScale: 1, dofQuality: null },
  fast: { scale: 1, renderScale: 0.75, msaa: 4, aa: 'msaa', shadowScale: 1, dofQuality: null },
  draft: { scale: 1, renderScale: 0.75, msaa: 0, aa: 'fxaa', shadowScale: 0.5, dofQuality: 'low' },
  preview: { scale: 0.5, renderScale: 1, msaa: 0, aa: 'fxaa', shadowScale: 0.5, dofQuality: 'low' },
};
const DEFAULT_SHOT_QUALITY = { shadows: 'pcfsoft' };

export class Engine {
  constructor({ canvas, quality = 'final', profile = false, overrides = {} } = {}) {
    this.canvas = canvas; this.preset = { ...(QUALITY[quality] || QUALITY.final), ...overrides }; this.qualityName = quality; this.profile = profile;
    this.cache = new Map(); this.shared = {};
    this.current = null; // { entry, idx, scene, ctx }
  }

  // episodeUrl: module path (relative to the server root, e.g. '/engine/episodes/_demo.js').
  // timelineUrl: optional JSON { episode?, fps?, duration?, shots: [{ name, shot?, start, end, params? }] }.
  async load({ episode, timeline } = {}) {
    let tl = null;
    if (timeline) { tl = await (await fetch(timeline)).json(); if (!episode && tl.episode) episode = new URL(tl.episode, new URL(timeline, location.href)).pathname; }
    const mod = await import(episode); const ep = mod.default || mod; this.ep = ep;
    this.fps = tl?.fps || ep.fps || 60;
    const baseW = ep.width || 1080, baseH = ep.height || 1920; const sc = this.preset.scale || 1;
    this.width = Math.round((baseW * sc) / 2) * 2; this.height = Math.round((baseH * sc) / 2) * 2;
    // resolve shots
    let entries;
    const builders = Array.isArray(ep.shots) ? Object.fromEntries(ep.shots.map((s) => [s.name, s])) : ep.shots;
    if (tl) entries = tl.shots.map((e) => { const b = builders[e.shot || e.name]; if (!b) throw new Error('timeline shot without builder: ' + (e.shot || e.name)); return { ...b, ...e, builder: b }; });
    else entries = ep.shots.map((s) => ({ ...s, builder: s }));
    entries.sort((a, b) => a.start - b.start);
    entries.forEach((e, i) => { e.index = i; e.f0 = Math.round(e.start * this.fps); e.f1 = Math.round(e.end * this.fps); if (e.f1 <= e.f0) throw new Error('empty shot ' + e.name); });
    this.entries = entries;
    this.duration = tl?.duration ?? ep.duration ?? Math.max(...entries.map((e) => e.end));
    this.frames = Math.round(this.duration * this.fps);
    // renderer + systems
    this.canvas.width = this.width; this.canvas.height = this.height;
    this.renderer = createRenderer(this.canvas, this.width, this.height);
    tex.setAnisotropy(Math.min(8, this.renderer.capabilities.getMaxAnisotropy()));
    this.post = new Post(this.renderer, this.width, this.height);
    this.camera = new ShotCamera(this.width, this.height);
    this.ctx = this._makeCtx();
    if (ep.setup) await ep.setup(this.ctx);
    return this.info();
  }

  info() {
    const gl = this.renderer.getContext(); const dbg = gl.getExtension('WEBGL_debug_renderer_info');
    return {
      name: this.ep.name || 'episode', fps: this.fps, width: this.width, height: this.height, duration: this.duration, frames: this.frames, quality: this.qualityName,
      gpu: dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER), maxSamples: gl.getParameter(gl.MAX_SAMPLES),
      shots: this.entries.map((e) => ({ name: e.name, start: e.start, end: e.end, f0: e.f0, f1: e.f1 })),
    };
  }

  _makeCtx() {
    const eng = this;
    return {
      THREE, anim, tex, lights, addLight, engine: eng, shared: eng.shared,
      get renderer() { return eng.renderer; }, get post() { return eng.post; }, get camera() { return eng.camera; }, get cam() { return eng.camera.cam; },
      fps: eng.fps, width: eng.width, height: eng.height,
      scene: null, shot: null, params: {}, rng: makeRng(1), t: 0, T: 0, frame: 0, u: 0,
      // Shot-independent seeded RNG: use it inside cache()/setup() factories so cached content never depends on which
      // shot happened to build it first (resume / stills / interleaved workers stay identical).
      rngFor(label) { return makeRng(hash32(eng.ep.seed ?? 'ep', 'global', label)); },
      setFog(opts) { setFog(this.scene, opts); },
      add(...objs) { for (const o of objs) { if (o.isLight) addLight(this.scene, o); else this.scene.add(o); } return objs[0]; },
      // Per-worker persistent cache (survives shot changes). Object3D / textures / materials / geometries returned by
      // the factory are marked persistent and are never disposed by shot cleanup. Treat cached things as read-only.
      cache(key, factory) {
        if (eng.cache.has(key)) return eng.cache.get(key);
        const v = factory(this);
        if (v && v.isObject3D) markTreePersistent(v); else if (v && (v.isTexture || v.isMaterial || v.isBufferGeometry)) markPersistent(v);
        eng.cache.set(key, v); return v;
      },
      // A fresh transform-copy of a cached Object3D (geometry/materials shared, so cheap). Clone materials you mutate.
      instance(key, factory) { return this.cache(key, factory).clone(true); },
    };
  }

  _entryForFrame(i) {
    const E = this.entries; let lo = 0, hi = E.length - 1, best = 0;
    while (lo <= hi) { const m = (lo + hi) >> 1; if (E[m].f0 <= i) { best = m; lo = m + 1; } else hi = m - 1; }
    return E[best];
  }

  async _switchShot(entry) {
    const ctx = this.ctx;
    if (this.current) {
      const prev = this.current; prev.entry.builder.dispose?.(ctx);
      disposeTree(prev.scene); prev.scene.clear();
    }
    const scene = new THREE.Scene(); scene.background = new THREE.Color('#000000');
    const seed = hash32(this.ep.seed ?? 'ep', entry.name);
    seedMathRandom(seed);
    const dur = (entry.f1 - entry.f0) / this.fps;
    Object.assign(ctx, { scene, shot: { name: entry.name, index: entry.index, start: entry.start, end: entry.end, duration: dur, f0: entry.f0, f1: entry.f1 }, params: entry.params || {}, rng: makeRng(seed), t: 0, u: 0 });
    setFog(scene, null);
    this.camera.reset(dur);
    this.post.reset(); if (this.ep.post) this.post.set(structuredCloneSafe(this.ep.post)); if (entry.post) this.post.set(structuredCloneSafe(entry.post));
    const q = { ...DEFAULT_SHOT_QUALITY, ...(this.ep.quality || {}), ...(entry.quality || {}) };
    ctx.quality = q;
    if (entry.builder.build) await entry.builder.build(ctx);
    // quality preset caps
    const P = this.preset; const pp = this.post.params;
    if (P.aa !== 'msaa') { pp.aa = P.aa; } else if (q.msaa != null) pp.msaaSamples = q.msaa; else pp.msaaSamples = Math.min(pp.msaaSamples, P.msaa);
    if (P.dofQuality) pp.dof.quality = P.dofQuality;
    pp.renderScale = (pp.renderScale || 1) * (P.renderScale ?? 1);
    applyQuality(this.renderer, scene, q);
    const ss = (q.shadowScale ?? 1) * (P.shadowScale ?? 1);
    if (ss !== 1) scene.traverse((o) => { if (o.isLight && o.castShadow && !o.userData._ss) { o.shadow.mapSize.multiplyScalar(ss).floor(); o.userData._ss = true; } });
    this.current = { entry, scene };
  }

  // Render frame i into the canvas. Returns per-stage timings (ms) when profiling.
  async renderFrame(i) {
    const T0 = performance.now();
    const entry = this._entryForFrame(i);
    let tBuild = 0;
    if (!this.current || this.current.entry !== entry) { const b0 = performance.now(); await this._switchShot(entry); tBuild = performance.now() - b0; }
    const ctx = this.ctx; const t = Math.min((i - entry.f0) / this.fps, ctx.shot.duration);
    Object.assign(ctx, { t, T: i / this.fps, frame: i, u: ctx.shot.duration > 0 ? t / ctx.shot.duration : 0 });
    // post params may be animated by update(); non-animated ones persist from build()
    const u0 = performance.now();
    if (entry.builder.update) entry.builder.update(ctx, t);
    this.camera.apply(t);
    hookSceneMaterials(ctx.scene);
    const u1 = performance.now();
    this.post.timings = this.profile ? {} : null;
    this.post.render(ctx.scene, this.camera.cam, { focusDistance: this.camera.focusDistance, frame: i });
    if (this.profile) this.renderer.getContext().finish();
    const T1 = performance.now();
    return { frame: i, shot: entry.name, build: tBuild, update: u1 - u0, render: T1 - u1, total: T1 - T0, stages: this.post.timings };
  }

  // Encode the canvas (call right after renderFrame, in the same task). type 'jpeg' | 'png' | 'webp'.
  capture(type = 'jpeg', quality = 0.92) {
    return new Promise((res) => this.canvas.toBlob((b) => res(b), 'image/' + type, quality));
  }
}

function structuredCloneSafe(o) {
  // post params may contain THREE objects (sources for god rays); deep-merge copies plain parts only
  return deepMerge({}, o);
}
