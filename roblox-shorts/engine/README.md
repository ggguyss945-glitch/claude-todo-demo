# Roblox Shorts 3D engine (Three.js r170, offline, 1080x1920 @ 60 fps)

Everything is procedural: characters, props, sets and textures are built in code. Frames are rendered by headless
Chromium (WebGL2 on SwiftShader, i.e. on the CPU), encoded in-page to JPEG, posted to the driver, and encoded to x264
in segments.

```
engine/
  index.html            page entry; exposes window.ENGINE for tools/render.js (and ?ep=...&t=... manual preview)
  core/engine.js        shot/timeline system, ctx, quality presets, deterministic frame loop
  core/post.js          post stack (HDR scene target -> bloom/glow/DOF/god rays -> uber pass -> FXAA/extra)
  core/camera.js        ShotCamera: keyframed pos/target/fov/roll + push/pull/orbit/truck/crane/... + shake + focus
  core/anim.js          easing, keyframe tracks, springs, wobble/bob/blink, pose-to-pose
  core/random.js        seeded RNG, hashes, Perlin/fBm noise (1D/2D/3D, tileable)
  core/textures.js      procedural tileable textures (+ normal/roughness maps), sky, sprite glows/sparkles
  core/scene.js         renderer, quality, fog + height fog, light helpers, disposal
  episodes/_demo.js     4 s demo (night lawn, avatar + lantern) - copy it as a template
  episodes/_demo.timeline.json  example timeline driving the demo's shot builders
  episodes/_swatches.js  board of every procedural texture (render one still to preview texture params)
tools/render.js         the renderer (stills, benchmark, resumable segmented video)
tools/encode.py         mux voice-over, contact sheets, stills, concat, QC check
```

## Quick start

```bash
cd roblox-shorts; export NODE_PATH=/opt/node-tools/node_modules
node tools/render.js engine/episodes/_demo.js /tmp/out/stills times=0.5,3 workers=2 sheet=1      # stills + sheet
node tools/render.js engine/episodes/_demo.js /tmp/out/demo.mp4 workers=3 quality=final sheet=1   # video
node tools/render.js engine/episodes/_demo.js /tmp/out/x.mp4 bench=36 workers=3 quality=fast      # benchmark
python3 -I tools/encode.py mux /tmp/out/ep.mp4 voiceover.wav /tmp/out/ep_vo.mp4 offset=0
python3 -I tools/encode.py check /tmp/out/ep_vo.mp4
```

Manual preview in a browser served from the project root: `/engine/index.html?ep=/engine/episodes/_demo.js&t=1.5&quality=draft`.

## Episode module

```js
export default {
  name: 'ep01', fps: 60, width: 1080, height: 1920, seed: 'ep01',   // seed feeds every shot RNG
  duration: 113.2,                    // optional (default: last shot end)
  quality: { shadows: 'pcfsoft' },    // default shot quality (see Quality)
  post: { bloom: { enabled: true } }, // default post params for every shot (deep-merged)
  async setup(ctx) {},                // once per worker before any shot (fonts, shared builders); put results in ctx.shared
  shots: [
    { name: 's01', start: 0.0, end: 1.15,
      quality: { shadows: 'pcfsoft', shadowScale: 1 }, post: { ... },   // optional per-shot overrides
      build(ctx) { /* create scene objects, camera moves, post look */ },
      update(ctx, t) { /* per frame, t = seconds from the shot start */ },
      dispose(ctx) {} },              // optional
  ],
};
```

**Timeline JSON** (times kept out of code; one builder can be reused by many shots):

```json
{ "episode": "ep01.js", "fps": 60, "duration": 113.2,
  "shots": [ { "name": "s01", "shot": "bedroom_push", "start": 0.0, "end": 1.15, "params": { "face": "shock" } } ] }
```

`episode` is relative to the JSON file. With a timeline, `shots` in the module may be an object map
`{ bedroom_push: { build, update } }`; each timeline entry picks its builder by `shot` (default: `name`) and passes
`params` as `ctx.params`. Render with `node tools/render.js engine/episodes/ep01.timeline.json out.mp4`.

**Cut timing.** Shot boundaries are rounded to whole frames: the shot covers frames `round(start*fps)` to
`round(end*fps)-1`, and `t` is exactly `0` on its first frame. Put cuts on the word onsets from the VO analysis.

## Determinism rules (important)

Frames are rendered out of order by several workers (frame i is a pure function of i), and renders resume from
the middle. So:

1. **`update(ctx, t)` must be a pure function of `t`.** No accumulating state between frames: no `x += v`. Use tracks,
   springs (`springKeys` / `springFollow` are stateless) and noise of `t`.
2. **No `Math.random`, `Date`, `performance.now` in episodes.** Use `ctx.rng` (seeded per shot), or `ctx.rngFor(label)`
   inside `ctx.cache()` factories and `setup()`, because cached content must not depend on which shot built it first.
   (`Math.random` is re-seeded per shot as a safety net.)
3. `build()` runs once per worker per shot, so it must give identical results every time.
4. Cached objects (`ctx.cache`) are shared across shots: treat them as read-only, use `ctx.instance()` for a
   transform copy, and clone materials before changing them.
5. **Post params are reset at every shot start**: episode `post`, then shot `post`, then `build()`. `update()` may
   animate any param (e.g. `ctx.post.params.flash.amount`). Values set in `build()` persist for the shot.

## ctx (passed to setup/build/update)

| member | |
|---|---|
| `THREE`, `anim`, `tex`, `lights` | modules (also importable directly) |
| `scene` | fresh `THREE.Scene` per shot (background black) |
| `add(...objs)` | add to scene (lights also get their target added) |
| `camera` | `ShotCamera` (below); `cam` = the `THREE.PerspectiveCamera` |
| `post` | `Post`; `post.set({...})` deep-merges, `post.params` is the live object |
| `setFog(opts)` | distance + height fog (below) |
| `rng` | seeded RNG for this shot: `rng()`, `.range(a,b)`, `.int(a,b)`, `.pick(arr)`, `.gauss()`, `.chance(p)`, `.fork(label)` |
| `rngFor(label)` | shot-independent RNG for caches |
| `cache(key, factory)` / `instance(key, factory)` | per-worker persistent assets (never disposed) / cheap clone of a cached Object3D |
| `shared` | object shared by setup and every shot (per worker) |
| `shot` | `{ name, index, start, end, duration, f0, f1 }`; `params` = timeline params |
| `t, T, u, frame` | shot time, episode time, `t/duration`, global frame index |
| `fps, width, height, quality, renderer, engine` | |

At shot end every geometry, material and texture in the shot scene is disposed, except resources marked
persistent (textures from `tex.*`, anything created through `ctx.cache`). Shadow maps are disposed too.

## Camera (`ctx.camera`, core/camera.js)

```js
ctx.camera.set({ pos: [0, 1.6, 4], target: [0, 1.2, 0], fov: 50, roll: 0 })  // each: constant | keys | Track | fn(t)
  .push(0.19)                          // house style: linear centred zoom push, image scale 1 -> 1.19 (no parallax)
  .push(0.19, { mode: 'dolly' })       // same scale growth by moving the camera toward the target (parallax)
  .pull(0.3, { ease: 'outExpo' })      // scale 1 -> 1/1.3
  .orbit(20) .truck(0.5) .crane(0.3) .dolly(0.4) .pan(10) .tilt(-8) .rollBy(5) .zoomFov(30)
  .follow(obj, { offset: [0, 0.5, 0] })               // target tracks an object
  .handheld({ rot: 0.35, pos: 0.01, freq: 0.6 })      // continuous drift (deg, m, Hz)
  .shake({ t0: 0.4, dur: 0.5, rot: 1.2, pos: 0.02, px: 12, freq: 14 })  // decaying; px = 2D pixel jitter (editor shake)
  .custom((state, t, cam) => {});
ctx.camera.frame({ target: [0, 1, 0], distance: 3, yaw: 20, pitch: 10, fov: 45 }); // place by angles
ctx.camera.focus(objOrPointOrMetres);   // DOF focus target (default: distance to target)
ctx.camera.toScreen([x, y, z]);         // -> [px, py] (call after apply)
```

Every move takes `{ t0, t1, ease }`; the window defaults to the whole shot and the ease to linear. Keys look like
`[[0, [x,y,z]], [1.2, [x,y,z], 'inOutSine']]`. FOV is **vertical** degrees (the Roblox default is 70).
`pushFov(fov0, amount, u)` gives the zoom curve directly.

## Animation (`ctx.anim`, core/anim.js)

- `ease.*`: linear, step/hold, smooth, smoother, in/out/inOut for Quad, Cubic, Quart, Quint, Sine, Expo, Circ,
  Back, Elastic and Bounce; `cubicBezier(x1,y1,x2,y2)`; `getEase(nameOrFnOrArray)`.
- `track(keys, {interp:'linear'|'catmull'})`: values can be numbers, booleans, arrays, Vector2/3/4, Color or
  '#hex' (linear-space lerp), Quaternion (slerp), Euler (slerp), or plain objects of numbers (poses).
  A key's ease shapes the segment arriving at it; `'step'` snaps at that key. `.at(t, out?)`. `steps(keys)` makes
  every key snap.
- `value(spec, t)` evaluates a constant, keys, Track or fn.
- `seg(t,t0,t1,ease)` 0..1, `tween(t,t0,t1,a,b,ease)`, `pulse(t,t0,attack,hold,release)`, `loop`, `pingpong`,
  `quantize(t, 1/12)` (stepped "on twos" motion).
- Springs (stateless): `springStep(u,freq,zeta)`, `spring(t,t0,from,to,freq,zeta)`,
  `springKeys(t, [[t,v],...], freq, zeta)` (exact chase of stepped targets: overshoot pops),
  `springFollow(t, targetFn, freq, zeta)`, `jiggle(t,t0,amp,freq,decay)`.
- Noise: `wobble(t, seed, freq, amp)`, `wobble3`, `bob(t,freq,amp,phase)`, `blink(t, seed, interval, dur)` -> 0..1.
- Poses: `poseSeq(t, [[t0,{armL:..}], [t1,{...}]], blend=0)`. Blend 0 gives Roblox single-frame snaps;
  0.08-0.15 s gives a quick in-between.
- `applyTransform(obj, t, {pos, rot, scale, quat})`.
- Math: `clamp, lerp, invLerp, remap, smoothstep, deg, fract`.

## Post stack (`ctx.post`, core/post.js)

Every effect is off by default (except dither), and only enabled effects are compiled into the shaders.
The scene renders linear HDR (half float, MSAA). Tone mapping happens in the uber pass, so **use the post tone
mapper, not `renderer.toneMapping`**. Colours marked display are in sRGB display space ('#hex' or [r,g,b] 0..1).

| key | params (defaults) | notes |
|---|---|---|
| `toneMapping` | `'aces'` / `'agx'` / `'neutral'` / `'reinhard'` / `'cineon'` / `'linear'` / `'none'` | |
| `exposure` | `1` | applied before tone mapping |
| `aa`, `msaaSamples` | `'msaa'`, `4` | also `'fxaa'`, `'msaa+fxaa'`, `'none'` |
| `renderScale` | `1` | scene target scale (multiplied by the quality preset's) |
| `bloom` | `strength .4, radius .6 (0..1 halo size), threshold .9 (linear), knee .5, levels 6, start 'quarter', tint` | dual-filter pyramid; emissive above threshold blooms |
| `glow` | `amount .2, radius .75, threshold 0, knee .5, mode 'screen'/'add'/'mix', tint` | "dreamy" diffusion / Pro-Mist; `mix` = soft-focus haze |
| `dof` | `focus 'auto'/metres, aperture 14 (px blur at infinity, 1080-wide), maxBlur 24 px, range 0 m (sharp band), quality 'low'/'med'/'high'` | half-res gather, near/far aware |
| `vignette` | `amount .3, size .45, softness .55, roundness .6, color, center [.5,.5]` | |
| `chroma` | `amount 2.5` px at the corner | radial RGB split |
| `lens` | `k1 -.08 (barrel <0), k2 0, zoom 1` | |
| `grade` | `temperature/tint (-100..100, white balance in linear), lift/gamma/gain/offset [r,g,b], contrast, pivot .45, saturation, vibrance, shadows/highlights colour + shadowsAmount/highlightsAmount + balance (split toning), outBlack/outWhite (output levels)` | display space, after tone mapping. Example: `outWhite: '#e7d4fc'` caps whites like the Tooth Fairies interiors |
| `grain` | `amount .035, size 1.6 px, colored .2` | deterministic per frame |
| `godrays` | `source [x,y,z] / Vector3 / Object3D / {screen:[u,v]}, threshold .8, strength .6, density .9, decay .96, weight 1, samples 40, skyOnly, tint` | 1/4-res radial blur; `skyOnly` uses depth |
| `blur` | `dir [px,px], zoom (fraction), center, samples 10` | editor-style shake or whip blur |
| `fade` / `flash` | `{ amount, color }` | fade mixes toward the colour; flash is a screen blend. Animate in `update()` |
| `dither` | `true` | kills banding in dark gradients |
| `extra` | `[{ material }]` | custom LDR ShaderMaterials (`tDiffuse`, `vUv`, optional `uFrame`) run after FXAA |

## Fog and lights (core/scene.js)

```js
ctx.setFog({ color: '#1d1b45', density: 0.04 });                          // exp2 distance fog (or near/far for linear)
ctx.setFog({ color: '#6a7b68', near: 8, far: 40,                          // Roblox Atmosphere-like
             height: { base: 0, falloff: 1.5, density: 0.2, color: '#8a9a88', max: 0.8 } });  // + exponential ground mist
ctx.add(ctx.lights.hemi('#8f8ff0', '#3a2448', 1.1));
ctx.add(ctx.lights.sun({ color, intensity, pos, target, shadow: true, size: 6, mapSize: 2048, radius: 4, bias, normalBias }));
ctx.add(ctx.lights.point({ color, intensity /* cd */, pos, distance: 0, decay: 2, shadow: false, mapSize: 512 }));
ctx.add(ctx.lights.spot({ ... angle, penumbra, shadow }));
```

Lights are physically based (the three.js r155+ units): a point light at 3-10 cd is a lantern or bedside lamp. Height fog
works on every material automatically (the engine patches three's fog chunks and hooks materials before they compile).
For sky domes, `fog: false` keeps stars visible and `fog: true` fades them into the fog colour.

## Textures (`ctx.tex`, core/textures.js)

```js
const wood = ctx.tex.woodPlanks({ color: '#9f3305', planks: 6, seed: 2, repeat: [3, 3] });
new THREE.MeshStandardMaterial({ ...wood.mat, roughness: 0.5 });   // mat = { map, normalMap, roughnessMap, normalScale }
```

| generator | main params |
|---|---|
| `grass` | `color, dark, light, blades, normal` |
| `woodPlanks` | `color, variation, planks, joints, gap, gapColor, grain, rings, gloss` |
| `brick` | `color, variation, mortarColor, rows, cols, mortar, speckle` |
| `plaster` | `color, mottle, speckle, bump` (plaster, stucco, Roblox Fabric-wallpaper micro bump) |
| `fabric` | `color, threads, contrast, fuzz` (plain weave: duvets, clothes) |
| `carpet` | `color, fibre, mottle` (rugs, shag) |
| `roofShingles` | `color, variation, rows, tabs, slot, granule` |
| `concrete` | `color, mottle, pores, seams, seamColor` (sidewalk slabs) |
| `dirt` | `color, dark, pebble, pebbles` |
| `starSky(o)` + `skyDome(tex, {radius, fog})` | `stops [[elev -1..1, '#hex']], stars, nebula, nebulaColors` (equirect) |
| `radialGlow({falloff})`, `sparkle({points: 4/6/8})` | sprite textures for halos, light pools, glints |

Every generator takes `size` (power of two, default 512) and `seed`. Bundles are cached by params (repeat
variants share one GPU texture), so you can call them freely from any shot. Low-level tools: `fbm`, `valueNoise`,
`stretchNoise`, `normalFromHeight`, `hexRgb`.

## Quality presets and performance (4 vCPU, SwiftShader)

`quality=` in render.js. Shots may lower `post.renderScale` or shadow sizes further.

| preset | scene target | AA | demo ms/frame (3 workers, wall) | 113 s episode (6,790 frames) |
|---|---|---|---|---|
| `final` | 1080x1920 | MSAA 4x | 750-800 | ~85-92 min |
| `balanced` | x0.85 (918x1632) | MSAA 4x | 570 | ~65 min |
| `fast` | x0.75 (810x1440) | MSAA 4x | 460 | ~52 min |
| `draft` | x0.75 | FXAA, half shadows, low DOF | 400 | ~45 min |
| `preview` | 540x960 output | FXAA | | |

At 1080x1920, `final` and `fast` are hard to tell apart; the references' real detail is about 540-720p.
Per-pass cost in the demo at `final` (each pass measured on its own with a forced sync):

| pass | ms |
|---|---|
| scene | 650-680 (MSAA ≈ 300 of it, lantern point-light cube shadow ≈ 150) |
| DOF | 140 (≈ 50 at render scale 0.75) |
| bloom + glow | 43 |
| uber | 81 |
| god rays | 62 |
| FXAA | 68 |
| JPEG encode | 40 |

Throughput by worker count (`fast`): 1 worker 571 ms/frame, 2 workers 482, 3 workers 459, 4 workers 461.
`mode=pages` (one browser) gives no gain, because all pages share one GPU process. **`workers=3` is the default.**
MSAA 2x costs the same as 4x. Point-light shadows are expensive (6 cube faces): use them sparingly, and prefer one
shadowed sun or moon plus unshadowed practicals and fake blob or contact shadows.

## render.js

`node tools/render.js <episode.js|timeline.json> <out> [from= to= workers= mode= chunk= quality= rs= jpegq= crf= preset= gop= times= sheet= bench= profile= keep=]`

- **Video**: frames go to `<out>.parts/frames/`. Each 300-frame chunk is encoded as soon as it is complete
  (libx264 crf 16, preset medium, `-g 120`, yuv420p, BT.709 limited range with exact BT.601-to-709 conversion) and its
  JPEGs are deleted. Back-pressure keeps at most about 3 chunks of JPEGs on disk.
  `progress.json` (done/total/fps/eta) is in the parts folder. Re-running the same command resumes: finished segments
  and frames already written are skipped. At the end the segments are concatenated (`-c copy`) and the parts folder
  is removed (`keep=1` keeps it). A crashed page is restarted and its frame retried.
- **Stills**: `times=0.5,1.2` with `<out>` a directory; `sheet=1` adds a contact sheet.
- **Benchmark**: `bench=N` renders N frames after a warm-up and prints ms/frame and per-stage averages.

## Gotchas found while building this

- `gl.finish()` does not block in Chromium; to time a pass, read back 1 pixel (`readPixels`) after it.
- `post.params` is replaced at every shot start, so do not hold a reference to it across shots.
- Arrays have `.at()`: never duck-type a Track by `.at` (use `instanceof Track`).
- Decode our video as BT.709 when extracting frames (`encode.py stills/sheet` do it). A plain `ffmpeg -> .jpg` shifts colours.
- Changing shadow type between shots recompiles materials (the engine handles it). Changing `post` features
  recompiles only the uber shader (cached per feature set).
