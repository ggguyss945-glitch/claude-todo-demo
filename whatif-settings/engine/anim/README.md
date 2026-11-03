# engine v3 animation runtime (`engine/anim/`)

The contract shot authors code against. Everything here is a pure function of time: the same timeline and the
same `t` always give the identical SVG string (no `Math.random`, no `Date`; seeds come from names via `hash()`),
so any frame can be drawn alone, in any order, on any worker. Design space is 1920x1080; the renderer scales it.

| file | what |
|---|---|
| `motion.js` | easings, keyframe tracks, springs, seeded noise, pops, squash, shake, anticipation keys |
| `actor.js` | `actor(id, o, t, ctx)`: `cast.toon()` plus idle, blinks, lip-sync, pose keys, overlap, accents, look targets |
| `lipsync.js` | word / viseme normalisation, `autoVisemes()` from spelling when a line has no visemes |
| `camera.js` | per-shot camera: keys, push, drift, punch-ins, shake, parallax, auto motion blur / zoom ghosts, screen layer |
| `transitions.js` | cut, whip, flash, glitch, zoomThrough, dipBlack, cardSlam |
| `captions.js` | caption track drawn above everything (caption.js look), `captionsFromLine()` |
| `frame.js` | `frame(T, t)` -> full `<svg>`; shot registry, ctx, transitions, overlays, captions, cue export |
| `bake.js` | optional static-layer baking (off by default: vector is faster for our sets, see "Speed") |
| `../anim.html` | the frame page (`window.renderAt(t)`, `window.svgAt(t)`, `window.__ready`, `window.cues()`) |
| `../bake.html` | bake page used by `tools/render.js bake=1` |
| `../shots/_demo.js` | worked example: street close-up, whip into the kitchen, toast, snap zoom, card slam |

## 1. Timeline JSON

```js
{
  fps: 60, dur: 61.5, bg: '#000',
  modules: ['shots/hook.js'],                     // shot modules, relative to engine/; every exported function
                                                  // (names not starting with _) is registered under its name
  shots: [
    { name: 'h01_sam_cu', start: 0, end: 1.4, p: { ... }, capY: 'face' },
    { name: 'h02_kitchen', use: 'kitchenWide', start: 1.4, end: 3.1, tin: { type: 'whip', dur: 0.2, dir: 'right' } },
  ],                                              // use: registered function (default: name). p: free params.
                                                  // capY: default caption y for this shot. tin/tout: transition
  voice: { lines: [
    { id: 'S00-L006', role: 'SAM', start: 12.34, dur: 2.6, file: '...wav', text: '...',
      words: [{ w: 'In', t: 0.03, d: 0.12 }, ...],          // or {w, t0, t1} | {word, start, end} | [w, t0, t1]
      visemes: [[0.03, 'v_A'], [0.1, 'v_small'], ..., [2.5, null]] },   // optional; null = expression mouth
  ] },                                            // word/viseme times are seconds from the line start (= the file
                                                  // start: audio/voice_lines.json entries drop in as they are, plus
                                                  // `start`); voice.absolute: true if they are global instead
  captions: [{ t0, t1, markup: 'I only changed {ONE|orange} thing.', mode?, y?, size?, cps? }],   // global s
  overlays: [{ t0, t1, use: 'flash' | '<registered fn>', p: { color, peak, up, hold } }],         // optional
}
```

Shots may be drawn at `t` outside `0..dur` (transitions draw both neighbours across the boundary), so never assume
`0 <= t <= dur`. Gaps between shots hold the previous shot.

## 2. A shot: `render(ctx) -> svg string`

```js
// engine/shots/hook.js
import { kitchen } from '../sets.js';
import * as U from '../ui.js';
import { seg } from '../anim/motion.js';

export function h02_kitchen(ctx) {
  const set = ctx.memo('kitchen', () => kitchen({ tableY: 800 }));     // sets are static: build once per worker
  const L = ctx.line('S00-L007');                                      // voice line in local time (or null)
  const tHit = L ? L.at('champ') : 1.0;                                // word start, local s
  ctx.cue('ui_toast', 0.75);                                           // SFX cue (call unconditionally)
  const cam = ctx.cam({
    keys: [[0, { x: -20, z: 1.02 }], [ctx.dur, { x: 10, z: 1.07 }]],   // default push is +3% if no keys
    punch: [{ t: tHit - 1 / 60, k: 1.1, at: [1290, 520] }],            // punch-in on the stressed word
    shake: [{ t: 0.8, amp: 12 }],
  });
  const dad = ctx.actor('dad', {
    x: 1290, y: 930, s: 1.55, facing: 'tq-right', talk: 'S00-L007',
    face: [[0, 'neutral'], [tHit, 'happy']],                           // instant swaps + 3-frame squash accent
    pose: [[0, { armR: 12 }], [tHit - 0.1, { armR: 150, foreR: 25, handR: 'open' }]],   // pose-to-pose snaps
  });
  let s = cam.set(set, { insert: [{ after: 'light', svg: dad }] });     // actors between set layers, with parallax
  if (ctx.t >= 0.75) s += cam.screen(U.toast({ title: 'Subtitles: Honest' }, seg(ctx.t, 0.75, 0.75 + 8 / 60)), { shake: true });
  return s;                                                            // screen-space SVG covering the frame
}
```

### ctx

| field | meaning |
|---|---|
| `t`, `u`, `dur`, `gt`, `fps`, `frame` | local seconds (0 at shot start), `t/dur` clamped, shot length, global seconds, 60, global frame index |
| `p`, `shot`, `name`, `index`, `start`, `end`, `T`, `W`, `H` | the shot's params and timeline entry |
| `line(id)` | voice line in local time: `{id, role, text, start, end, dur, words:[{w,t0,t1}], visemes, word(k, n), at(k, n)}`; `at('ONE')` = local start of that word (case/punctuation-insensitive; `n` = n-th match; number = index, negative from the end) |
| `lines(role?)` | lines overlapping the shot (+-0.5 s), local time |
| `mouth(who, t?)` | viseme for a role / line id / `{visemes, words}` at local t, or null (between words) |
| `talking(who, t?)`, `word(who, t?)` | is a line of `who` running; the word being spoken `{w, t0, t1}` (local) |
| `cam(o)` | the shot camera (section 4); fills `t`, `dur`, `fps`, a seed from the shot name |
| `actor(id, o)`, `actorState(id, o)` | draw an actor / get its resolved parameters (head position etc.); `o.t` overrides the local time (lag gags) |
| `rng(s)`, `rand(a, b)`, `noise(x, s)` | seeded PRNG (mulberry32, seed = shot + s), lattice random 0..1, smooth noise -1..1 |
| `seg(a, b)`, `at(v)` | progress of t through [a, b]; evaluate a constant / function / keyframe list at t |
| `memo(key, fn)` | per-worker cache for static things (sets, paths); key must include everything fn depends on |
| `portal([x, y, w, h, r])` | screen rect a following `zoomThrough` pushes into (e.g. the phone screen) |
| `cue(name, at, o?)` | register an SFX cue at local time `at` (exported with `render.js ... cues=1`) |
| `bake(key, make, box, res)` | low-level bake hook (normally use `cam.set(set, {bake})`) |

Shot errors do not crash a render silently: the frame shows a magenta SHOT ERROR card and `render.js` stops
(unless `errors=ignore`).

## 3. Actors: `ctx.actor(id, o)`

Cast ids: `sam lily mom dad pickles briggs kevin tiny`. Every option may be a constant, a function of local `t`, or
keyframes `[[t, value, ease?], ...]` (eased segments, see `track()`), unless noted.

| option | meaning |
|---|---|
| `x, y, s` | feet position (world px) and scale |
| `facing` | rig.js FACINGS: `front` (0), `tq-right`/`right` (32), `tq-left`/`left` (-32), `side-right` (90), `side-left` (-90), `tq-back-right` (148), `tq-back-left` (-148), `back` (180), or degrees; keys in degrees turn smoothly |
| `pose` | partial pose `{armL, armR, foreL, foreR, handL, handR, legL, legR, head, lean, bob, ...}` or **pose keys** `[[t, {armR: 150}, ease = 'outBack', dur = 6 frames], ...]`: hold, then snap over dur, then hold (fields merge forward). `anticPose(t, from, to, {wind: 4, dur: 6, amt: 0.15})` (from actor.js) returns a wind-up + snap pair to splice in |
| `face` | preset name (face.js PRESETS: neutral happy starstruck shocked deadpan smug scared panic angry guilty sleepy confused scream laugh cry sly determined disgusted dizzy love relieved nervous bored evil excited wink sad skeptic surprised yawn blep), an object `{preset, eyes, brows, mouth, look, add, ...}`, or **step keys** `[[t, face, accent?], ...]`: instant swaps, each with a 3-frame body squash accent (`accent: 0` off, a number scales it; `o.accent: false` disables all) |
| `talk` | role (`'SAM'`), line id, or `{visemes, words}`: lip-sync. The viseme replaces the mouth inside word windows and falls back to the expression mouth between words; a small head nod follows mouth openness (`talkNod`, `talkScale`) |
| `look` / `lookAt` | pupil offset `[dx, dy]` (about +-5) / a world point the eyes track (both keyable) |
| `blink` | default on: seeded blinks every ~1.5-5.5 s, 4-6 frames (half, closed..., half), 12% doubled, global time so they continue across cuts; skipped on eyes that cannot close (star, heart, spiral...). `false` off; `{cell, seed}` |
| `saccade`, `nervous`, `panic` | eye darts amplitude; 0..1 per-frame tremble (1-3 px / 4-8 px) with darts |
| `idle` | idle layer amplitude (1 default, 0 statue): breathing (+-0.6%), 1.4 px bob, arm sway, head drift, per-character phases |
| `overlap` | default on with pose keys / moving x,y: forearms and hands lag 2 frames (`lag`), ponytail, pigtails and tail follow springs (`hair`, `hairFreq`, `hairDamping`) |
| `squash` | `[[t, amount], ...]` damped squash pulses about the feet (+ squash, - stretch); landings, BONKs |
| `lurch` | `[[t, k = 1.25], ...]` grow toward the lens in 2 frames, settle over 8 (shouted words) |
| `ground` | floor y: draws a detached contact shadow that shrinks as the actor jumps |
| `add`, `props` | toon add-ons `{sweat, tears, q, zzz, ...}` / props `{L: 'phone', R: null}`, constant or step keys |
| `mannequin`, `tint`, `light`, `lod` | passed to `toon()` as top-level keys (cast.js): constant, function of `t` or track keys; numbers and `{color, k, from}` objects blend between keys (for a hard flicker use a function or doubled keys). Same output as putting them in `add:{}` |
| `outfit`, `variant`, `legs` | passed to `toon()`: constant, function or step keys (hold until the next key), e.g. `outfit: 'pyjamas'`, `variant: 'default'`, `legs: false` |
| `tailWag`, `tailHz` | Tiny only: idle tail wag added to `pose.wag` (amplitude, default 0.5 of a full -1..1 wag, scaled by `idle`; 0 = off) at `tailHz` (2.2 Hz, global time) |
| `opacity`, `seed`, `shadow` | |

`toon()` costs about 1 ms per character (pickles 0.3 ms), a set 1.5-4.5 ms to build (memoise it). A full frame
is 3-4 ms of JS; rasterising is what costs.

## 4. Camera: `const cam = ctx.cam(o)`

Screen centre shows world point `(960 + x, 540 + y)` at zoom `z`, roll `r` degrees.

| option | meaning |
|---|---|
| `keys` | `[[t, {x, y, z, r}, ease?], ...]`, fields carry forward, zoom interpolated in log space. **Snap zoom**: a key 6-8 frames after a hold key with `'outExpo'`: `[[0, {z: 1}], [1.0, {z: 1}], [1.0 + 7/60, {z: 1.6}, 'outExpo']]`. **In-shot whip**: an x key 0.15-0.25 s later with `'inOutCubic'`. `frameOn([x, y], z, [sx, sy])` (camera.js) gives `{x, y, z}` that puts a world point at a screen point |
| `push` | extra push over the shot (default 0.03 without keys, 0 with keys) |
| `drift` | seeded drift amplitude px (default 10; 0 locks) or `{amp, freq}` |
| `dolly` | 0..1: far layers zoom less than near ones |
| `punch` | `[{t, k = 1.12, at: [sx, sy], in = 2 frames, settle = 0.25, keep = 0.03, hold?, until?}]` screen punch-ins (crisp) |
| `shake` | `[{t, amp = 22, decay = 0.08, freq = 28, rot = 0}]` trauma shake A e^(-t/decay) noise (crisp) |
| `blur` | auto directional blur when the world moves > 30 px/frame over the frame's shutter (blurK 0.25 x speed, max 64 px); `false` off |
| `ghost` | auto 3-6 ghost copies of the world (equal average over 0.6 frame) when the frame corners move > 25 px/frame more than the centre (snap zooms, rolls); wins over blur; `false` off, a number forces N |

| method | |
|---|---|
| `cam.set(set, {insert, only, skip, bake, live})` (with `bake`, layers named in `live`, default `LIVE_LAYERS` = `['light', 'phone', 'grade']`, stay vector) | draw a sets.js set `{layers}` with per-depth parallax (sky .08, far .3, mid .75, light .75, near 1); `insert: [{after: 'mid', svg, depth = 1, screen?}]` puts actors between layers (`after: 'top'` or none = above all). Applies blur / ghosts |
| `cam.layer(svg, depth = 1)` | one world layer at a depth (no blur) |
| `cam.render([{svg, depth, screen?}])` | compose your own layer list with the automatic blur / ghosts |
| `cam.screen(svg, {shake})` | screen-locked layer above the world (UI, stickers); shakes only if asked |
| `cam.toScreen(P, d)`, `cam.toWorld(S, d)` | point mapping; `cam.state` = `{x, y, z, r, k, vx, vy, speed, cornerSpeed, ghosts, blur, ...}` |
| `cam.maxZoom(d)`, `cam.visible(d)` | over the whole shot (bake sizing) |

Blend-mode and filter layers stay frame-sized and are never placed inside `<use>` or `fx.glitch()` (Chromium drops
them); the glitch transition re-draws strings, never `<use>`.

## 5. Transitions (`tin` on the incoming shot, or `tout` on the outgoing one)

| type | window around the boundary b | notes |
|---|---|---|
| `cut` | - | default |
| `whip` | [b - d/2, b + d/2], d 0.15-0.25 | both shots slide as one strip, `dir: left|right|up|down` (camera pan direction), `ease: 'front'` = front-loaded outQuart; directional blur (`blurK` 0.2, `blurMax` 64, `blur: false` = crisp art) + white speed streaks (`lines` 0..1) |
| `flash` | [b - 2 frames, b + d], d 0.22 | white ramps in over 2 frames, holds `hold` frames (1), decays; `color`, `peak` |
| `glitch` | [b - d/2, b + d/2], d 0.1 | RGB band slices re-rolled every 2 frames; `bands`, `amount` |
| `zoomThrough` | [b - d, b], d 0.45 | A pushes into `rect: [x, y, w, h, r]` (screen px in A) or the rect A's shot gave `ctx.portal()`; B grows inside it and lands at exactly 1:1 on b; `ease: 'expo'`, `glare` |
| `dipBlack` | [b - d/2, b + d/2], d 0.4 | `color` for a dip to white etc. |
| `cardSlam` | [b, b + d], d 0.3 | B slams 1.35 -> 1 by `impact` (0.4 of d), 1-frame white hit (`hit` 0.55), shake (`amp` 26) |

Snap zooms and punch-ins are camera moves inside a shot, not transitions.

## 6. Captions

`T.captions` entries are drawn above shots and overlays by `drawCaptions` with caption.js pop-in (plain chunks
0.6 -> 1.05 -> 1 in 3 frames; chunks with `{KEYWORD|colour}` 0.85 -> 1.16 -> 1 in 6 frames).
`mode`: `normal` | `type` (typewriter + cursor, `cps` 30) | `scream` (shakes every frame) | `quote` (curly quotes;
`quote: open|close|both|none`). `y`: px or `mid` (72% H) | `face` (86%) | `pov` (92%); default from the shot under
the caption's first word (`shot.capY`), so a caption never jumps at a cut.

Build them from voice lines (timeline builder, node):
```js
import { captionsFromLine } from '../engine/anim/captions.js';
captionsFromLine(line /* {start (global), dur, words:[{w,t0,t1}] relative} */, 'I only changed {ONE|orange} thing.',
                 { lead: 3 /* frames before the word */, maxWords: 3, tail: 0.25, mode, y, until /* e.g. next cut */ });
```
Chunks of 1-3 words, each shown `lead` frames before its first word and held until the next chunk.

## 7. motion.js toolkit (all pure)

`ease.*` (linear, in/out/inOut x Quad Cubic Quart Quint Expo Sine Back, outBackBig, outElastic, inElastic,
outBounce, anticipate), `outBackS(s)`, `clamp lerp seg invLerp remap frames round`; `track(keys, {ease, log})`
for numbers, arrays, `'#hex'` colours (linear-light mix) and objects; `snaps(keys)` pose-to-pose; `step(keys)`
hold/step; `lastKey`; `spring(t, freq, damping)` (0 -> 1 step response), `wobble` (impulse), `follow(fn, t, o)`
(stateless spring-lagged copy of a signal); `noise1d noise2d fbm1d jitter rand rng hash`; `pop(t, t0)`
(0.6 -> 1.05 -> 1, 3 frames), `popKw` (0.85 -> 1.16 -> 1, 6 frames), `popBig` (toasts); `squash(t, t0, amount)`,
`squashes`, `stretch`; `shake(t, events)`; `antic(t, from, to, {wind, dur, amt})` number-track anticipation keys,
`holdKeys`; `stepTime` (on-twos / lag remap), `pingpong osc bell`.

## 8. Rendering

```
node tools/render.js <timeline.json> <out.mp4> [fps=60] [workers=4] [scale=1.3333333 (2560x1440) | 2 (3840x2160)]
     [from=s] [to=s] [chunk=300] [crf=15] [preset=medium] [audio=<wav>] [bake=1] [keep=1] [errors=ignore]
node tools/render.js <timeline.json> <out_dir> times=1.2,3.4 | times=<json list> [scale=0.5] [ext=png]   stills
node tools/render.js <timeline.json> <cues.json> cues=1                                                SFX cue list
python3 -I tools/sheet.py <timeline.json> <video.mp4 | frames_dir | render> <out.jpg> [--times a,b] [--cols 3]
```
Workers (one Chromium each) draw frames at output size (CSS scaling, deviceScaleFactor 1) as JPEG q95 into
`<out>.parts/frames_<chunk>/`; each finished chunk is encoded at once (libx264 crf 15, preset medium, yuv420p, high,
-g 120, BT.709) and its JPEGs deleted, so disk holds about two chunks (JPEG q95 is ~550 KB per 1440p frame: ~330 MB
with chunk=300; segments add ~2 MB per second of video). Re-running the same
command resumes: finished segments (`.ok`) are skipped, frames on disk are kept. Ctrl-C / kill stops cleanly.
Segments are joined losslessly at the end. `<out>.parts/progress.json` has done/total, ms/frame, ETA.
Captures happen right after the DOM swap (verified: no stale or duplicated frames).

**Speed (4-core box, 1440p60, 4 workers):** drawing 14.5 fps (69 ms/frame wall; heavy whip frames ~2x);
end to end with encoding about 5 fps (the x264 encode at preset medium is the bottleneck), so the 60 s hook
(3,600 frames) takes about 12 min. Baking static set layers (`bake=1` + `cam.set(set, {bake: 'name'})`) works
but is slower here (206 vs 77 ms/frame) and slightly softer: our flat vector sets raster faster than large
transformed bitmaps. Keep it for future layers with heavy filters only.

## 9. QA helpers (scratch)

`<scratch>/settings/engine/tools/`: `node_check.mjs <timeline>` (JS ms/frame, determinism of out-of-order
re-renders, shot errors, cues), `motion_check.py <video>` (still frames, longest still run, frame-diff spikes =
pops; every spike should be a designed event), `smooth_check.mjs` (second differences of camera/actor tracks).
