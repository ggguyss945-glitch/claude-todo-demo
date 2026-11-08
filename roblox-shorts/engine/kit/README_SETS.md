# Suburb night SET kit (engine/kit): API

The reusable sets for the "In this world..." shorts: a Roblox-built suburban street (night, dusk, dawn, day), front
lawns with gnome and character slots, a lawn close-up set, props, skies, the VISUAL_BIBLE §5 lighting presets, the §6 post
presets and the "magic air" effects. Everything is procedural, seeded and deterministic (frames are bit-identical rendered with 1
or 2 workers, checked).

| File | What |
|---|---|
| `sets.js` | **Entry point of the set kit**: `import * as sets from '../kit/sets.js'` |
| `suburb.js` | houses, lots, the street, the lawn close-up set, slots, camera presets |
| `props.js` | props (lamp posts, fences/gates, mailboxes, tulip beds, bushes, pines, stepping stones, porch lanterns, rocking and deck chairs, dandelion, signs, kennel, hose reel, hydrant, bin, car, moving truck, boxes), grass blades |
| `sky.js` | galaxy / void night skies, moon, dusk, blue hour, dawn, day domes, sun disc, mountain silhouettes |
| `lighting.js` | lighting presets as functions, `GRADE`, `postPreset()`, practical lights, lamp/window light states |
| `fx.js` | sparkle glints, magic dust, VFX burst, glow sprites, light pools, contact shadows, ground rings |
| `kitlib.js` | helpers: `Parts` merge batcher, material library `M(key)`, extra textures (siding, asphalt, fieldstone, louvres), canvas decals (window interiors, doors, plaques, signs) |
| `_sets_qa.js` | QA episode: renders the set stills (see QA below) |

`index.js` is shared with the character kit (README_CHARS.md) and re-exports both kits; `sets.js` is the set kit alone.

## Conventions

- **Units.** Sets and props are **built in studs** inside a root group scaled by `STUD = 0.32`, so everything a shot
  touches is in **metres**: camera, lights, fog, slots, views, fx. Scale chart (VISUAL_BIBLE §2.7): R6 human 5.2 studs,
  gnome 2.0, picket fence 3.5, lamp post 13.5, bungalow ridge ~18, two-storey ~28, lot 36 x 22 lawn, road 26, sidewalk 6.
- **Facing.** Every object faces **+Z** in its own frame (same as the character kit). A slot `yaw` is applied as
  `obj.rotation.y = yaw` (`place()` does it). Lot frame: +Z points to the street, so **gnome slots have yaw = lot yaw + PI:
  the gnome faces its house, back to the street** (EP01 rule). Character slots on porches face the street.
- **Caching.** `buildStreet()` and friends build once per worker (`ctx.cache`) and return a cheap clone per shot. Clones
  share geometry and materials: never mutate a shared material; swap it (`setLamps`, `setWindows` do that).
- **Determinism.** No `Math.random`; all variation is seeded from `seed` and the lot id. Effects are pure functions of shot
  time `t` (call `fx.update(t)` in `update()`).

## Quick start (a night lawn shot)

```js
import * as sets from '../kit/sets.js';
build(ctx) {
  const set = sets.buildLawnCloseup(ctx, { seed: 'ep01' }); ctx.add(set);
  const hero = set.userData.lots.find((l) => l.hero).id;               // 'A1'
  sets.place(grandpa, sets.slot(set, hero + '.bed0')); ctx.add(grandpa); // in his flowerbed, facing the bedroom window
  ctx.add(sets.contactShadow(ctx, { pos: sets.slot(set, hero + '.bed0').pos, radius: 0.24 }));
  ctx.camera.set(set.userData.views.gnomeCU).push(0.19);               // camera FIRST: presets aim the key from it
  ctx.shared.rig = sets.nightLawn(ctx, { set, subject: { pos: [...] } }); // sky + lights + fog + post grade
  ctx.shared.fx = sets.sparkles(ctx, { center: [...], size: [2.5, 1.4, 1.6], count: 9 }); ctx.add(ctx.shared.fx);
},
update(ctx, t) { ctx.shared.fx.update(t); },
```

## Sets (`suburb.js`)

### `buildStreet(ctx, opts)` -> Group (clone, scaled by STUD)

| option | default | |
|---|---|---|
| `seed` | `'street'` | all house styles, colours, lit windows, props |
| `lotsPerSide` | 6 | lots on side A (z < 0, houses face +Z) and side B (mirrored) |
| `lotW`, `lawnDepth` | 36, 22 | studs |
| `roadW`, `sidewalkW` | 26, 6 | studs; road top y = -0.4, kerbs/sidewalks/lawns at y = 0 |
| `sideB` | true | houses across the street |
| `extend` | 160 | road/sidewalk/lawn/lamps continue past the lots (fades into fog) |
| `lampSpacing`, `lampHeight` | 36, 13.5 | one black Victorian lamp per lot boundary on each side |
| `forest` | true | pine silhouettes behind the back yards |
| `detailRadius` | 2 | lots further than this from the hero get `detail: 'low'` (no tulips, fewer props) |
| `hero` | `{ side: 'A', index: 0, closeup: false, house: {}, lot: {} }` | the lot the views are built around; `closeup: true` adds ~19k instanced grass blades over its front lawn and ~90 daisies |
| `houses` | `{}` | per-lot overrides: `{ A2: { house: {...}, lot: {...} } }` |

`buildLot(ctx, o)` = a 3-lots-per-side street with the hero at A1 (a single lawn plus context; cheaper).
`buildLawnCloseup(ctx, o)` = `buildLot` with `closeup: true` and a hero bungalow whose bedroom window sits low over the
grandpa bed (foundation 1.0, sill 1.6), both front windows lit, centre porch, stepping-stone path, porch steps.

### `set.userData` (all positions in metres, set-root space)

| key | content |
|---|---|
| `slots[]` | `{ name: 'A1.bed0', kind: 'gnome' or 'char', lot: 'A1', pos: [x,y,z], yaw, onBed }` |
| `lots[]` | `{ id, side, index, origin, yaw, houseFront, door, steps, gate, deckY, ridge, beds: [{ pos, len, dep }], hero }` |
| `lamps[]` | `{ name: 'lamp_7', side, pos, head }` (head = lantern glass centre) |
| `lanterns[]` | porch wall lanterns `{ lot, pos }` |
| `windows[]` | `{ lot, face: 'front' or 'left' or 'right', lit, tone: 'warm' or 'pink', pos }` |
| `views` | camera presets `{ pos, target, fov }` for the hero lot: `streetWide` (3/4 along the lawns, gnome backs), `streetHigh` (aerial along the street), `lawn`, `porch`, `porchOut` (from the door: gnome faces), `gnomeCU` (gnome eye level, lit window above), `gnomeFace` (reverse), `lawnLow` |

Slot names per lot (prefix `A1.` etc.):
- gnome (yaw faces the house): `bed0`, `bed1` (standing IN the flowerbed under a front window, a tulip-free gap is kept;
  `bed0` is grandpa's spot under the hero window), `bedFront0/1` (lawn in front of the bed), `lawn0`..`lawn3` (within ~5 studs of
  the path so they fit a 9:16 frame).
- character: `porchDoor`, `porchSide` (on the deck, facing the street), `porchSteps`, `lawnMid` (facing the street),
  `gateIn`, `gateOut`, `windowLook` (facing the house).

Helpers: `place(obj, slot, set?)` (pass `set` if you moved/rotated the set root), `slot(set, name)`,
`slotsOf(set, { kind, lot, name })`, `lot(set, id)`.

Named objects for per-shot control (`set.getObjectByName` / traverse): `lot_A1` (merged lot meshes, one per material;
lit windows are meshes named `win:<tone>:...`), `gate_A1` (gate leaf; rotate `.rotation.y` about its hinge to open),
`lampGlass` / `lampHalo` / `lampPool` (inside `lamp_<i>` groups), `lanternGlass`, `lanternHalo`, `winGlow`,
`agentBoard`, `sign`, `heroBlades`, `heroDaisies`, `ground`, `forest`.

### Lower level: `addHouse(P, o)`, `addLot(P, lotOpts, houseOpts)`
Both build into a `Parts` batch in studs. `HOUSE_DEFAULTS`: `type` ('bungalow' / 'twoStorey'), `width`, `depth`, `wall`
('siding' / 'brick'), `wallColor`, `roofColor`, `trimColor`, `doorColor`, `shutterColor` (null = none), `roof` ('side' /
'front' gable), `porch` ('full' with rocking chair, 'center' with a small gable, 'none' = door hood + stoop), `porchDepth`,
`porchWidth`, `foundation`, `sill`, `storeyH`, `panes` (4/6), `doorX`, `lit` (fraction or per-window array: front windows,
then side windows), `tone`, `pinkWindow` (index), `curtain`, `winIntensity` (2.3 = emissive x2.3), `number` (plaque),
`chimney`, `planters`, `deck`, `seed`. `LOT_DEFAULTS`: `lotW`, `lawnDepth`, `detail` ('hero'/'full'/'low'), `fence`, `path`
('stones'/'walk'), `beds`, `mailbox`, `extras` (`'hoseReel'`, `'kennel'`, `'trashBin'`, `'hydrant'`, `'leafyTree'`,
`'pineFront'`, `{ board: { lines, header } }` estate-agent board, `{ sign: { lines, header } }` post sign), `backTrees`.
`PALETTE` holds the siding/brick/roof/door/shutter/curtain/tulip colours (albedo; PN clapboard palette, TF brick).

Each house is ~10-15 draw calls (merged per material). Every surface is textured (siding boards 0.6 stud, brick 1 x 0.44,
shingles, fieldstone foundations, plank porches, painted-wood trim with faint grain, concrete slabs 6 studs, asphalt,
grass, soil); no studs.

## Props (`props.js`)

Every prop has `addX(P, opts)` (merge into a `Parts` batch at its current transform) and `prop(name, opts)` (standalone
Group in studs: scale by `STUD` or put it in a scaled group). Origin on the ground, front = +Z.

`streetLamp` (`heads: 1|2`; glass separate, emissive #ffd9a0 x4), `mailbox`, `picketFence` (`length`, `gate: { at, width }`;
the gate leaf is a separate hinged object), `flowerbed` (tulips, `gaps` for a gnome spot, stone/brick edging, bushes),
`tulip`/`daisy`, `bush` (round, optional blossoms), `pine` (stacked noisy cones, 18-30), `leafyTree`, `steppingStones`
(polyline), `dirtPatch`, `wallLantern`, `rockingChair`, `deckChair` (striped sling, EP01 frame 1), `hoseReel`, `kennel`,
`hydrant`, `trashBin`, `potPlant`, `dandelion` (`puff: true` = seed clock; burst it with `fx.burst`), `agentBoard`
(`lines`, `header`; e.g. `['COMES WITH', 'ANCESTORS']`), `postSign` (`['KEEP OFF', 'THE LAWN', 'AFTER DARK']`), `car`,
`cardboardBox` (`label`), `movingTruck` (24 x 9 x 10 box, open back at -Z, ramp, labelled boxes incl. `BALCONY GNOME`, `THEO`).
`grassBlades({ area, count, height, seed, feather })` -> InstancedMesh (studs) of two-sided, up-lit blades for close-ups.

## Skies (`sky.js`)

`sky(ctx, { preset, moon, sun, mountains, rotation })` -> Group (dome radius 400 m, `fog: false`). Presets (`SKIES`):
`galaxy` (TF: black zenith, deep violet horizon, magenta/purple nebula, 3.2k stars; default night), `void` (AW/PN black
with stars), `dusk` (EP01 frame 1: amber horizon to violet), `duskPN`, `blueHour`, `dawn` (periwinkle -> mauve -> peach),
`day`. `moon(ctx, { az, el, size, style: 'tf' | 'aw' })` (blue-violet crater disc / white disc with halo), `sunDisc(...)`,
`mountains(ctx, { color, distance, height })`. az/el in degrees, az 0 = toward -Z.

## Lighting presets (`lighting.js`)

Call after `ctx.camera.set(...)` (the key light is placed at the camera's upper front-left). Each returns
`rig = { sky, hemi, key, lights: [...], subject?, update(t) }` and sets fog and the post preset.

| function | bible | hemi (sky / ground / I) | key | practicals | fog | post |
|---|---|---|---|---|---|---|
| `nightStreet(ctx, { set })` | P1 | #8a90ff / #241a3a / 1.4 | moon #b4b8ff 1.8, el 48, no shadow | 3 nearest lamps #ffc27a 5 cd, 1 porch lantern #ffb766 3 cd (<= 12 m), 1 window spill #ffd9a0 1.5 cd (<= 10 m) | exp2 #06051a 0.012 | `night` |
| `nightLawn(ctx, o)` = `nightStreet(ctx, { highKey: true })` | P1 lifted lawn close shots | 1.25 | same | window 2 cd | same | `nightHigh` |
| `porchGlow(ctx, o)` | P1 + porch | 1.25 | 1.5 | 3 lamps, 2 lanterns 4 cd, 2 windows 2.2 cd | same | `porch` |
| `magicGlow(ctx, { source })` | P3 | #ffcdb8 / #5a2030 / 1.4 | #ffe2c8 1.2 | `source` point #ffb85c 8 cd; `rig.fwoom(t0, { emissives })` returns an update fn: 8 -> 50 cd in 0.15 s, -> 10 over 1.5 s inOutSine | #1a0a14 0.01 | `magic` |
| `dawn(ctx, o)` | P4 | #c4c8ff / #6a4a3a / 1.0 | sun #ffcf9e 2.6, el 10, from behind-side, pcfsoft shadow | lamps and windows OFF | #e8c4c0 0.006 | `dawn` |
| `dusk(ctx, o)` | DUSK (frame 1) | #a08ad0 / #5a3424 / 1.7 | sun #ff9a50 2.6, el 6, az 78 (side light: a street-side sun at 6° puts every lawn in fence shadow) | lamps dim, 1 lantern, 1 window | #c08a6a 0.006 | `dusk` |
| `day(ctx, o)` | DAY | #bcd4ff / #5a4a30 / 1.0 | sun #fff3e0 2.5, el 45 | off | #c8d0e0 0.006 | `day` |

Options for every preset: `set`, `hemi` / `hemiIntensity`, `key`, `sun`, `lamp` / `lantern` / `window` (`{ n, cd, color, maxD }`),
`subject: { pos, cd, color }` (a soft lift so the subject is the brightest thing at night), `sky: false`, `skyPreset`,
`skyOpts`, `moon` (object or false), `sunDisc`, `fog: false`, `fogOpts`, `post: false`, `postOpts`, `target`, `shadows`.
Numbers live in `LIGHT` (edit there, not in shots). Shadows: night presets cast none (bible); sun presets need the shot
`quality: { shadows: 'pcfsoft' }` (the sets cast/receive; cost only appears when a shadowed sun exists).

Light states: `setLamps(set, 'on' | 'dim' | 'off')`, `setWindows(set, 'on' | 'off')` (material swaps on the clone; good for
cascades on a cut). `practicals(ctx, set, {...})`, `keyLight`, `sunLight`, `camBasis` are exported for custom rigs.

### Post presets (§6)
`postPreset(name, overrides)` -> a full post params object (§6.1 base: ACES, MSAA, dither, bloom 0.12 / threshold 1.2 /
radius 0.35, everything else OFF: no DOF, vignette, grain, CA, lens, glow) plus the scene row. Names (`POST_NAMES`):
`night` (exp 1.25), `nightHigh` (1.0), `porch` (1.12, bloom 0.13), `bedroom`, `magic` (1.15, bloom 0.4 / 0.9 / 0.5, glow
0.12 screen #ffd8c8), `dawn` (1.4), `day`, `dusk` (1.4, bloom 0.15), `sepia`, `bw`. `GRADE` = the §6.2 grade presets, with
`night` calibrated to saturation 0.9, contrast 1.08, shadowsAmount 0.2 (outWhite stays #c4c3fc), `warmGlow` saturation 0.92,
`dusk` temperature 16 / saturation 1.02. Bloom never exceeds 0.15 outside the magic preset; halos are local sprites.

## FX (`fx.js`), metres, pure functions of `t`

| function | spec |
|---|---|
| `sparkles(ctx, { center, size, count, px: [40, 80], points: [6, 8], drift, colors })` | TF glints: 6/8-point, #e9dcff (some #ffe2c4), 40-80 px on the 1080x1920 frame whatever the distance, twinkle (opacity 0.35-1, scale 0.6-1.2, 0.6-1.2 s), slow rotation, drift 0.04-0.1 m/s (20-60 px/s at 2-5 m), wrap inside the box with fades (no pops). Outdoors 6-12, indoors 8-20 |
| `magicDust(ctx, { center, radius, height, count, colors })` | gold/pink motes + 4-point pink twinkles rising and swirling around a source |
| `burst(ctx, { pos, t0, dur: 0.35, count, spread, ringPx, puff })` | 0.3-0.4 s snap/transformation burst: sparkles flying out (outExpo), expanding white ring, core flash; `puff: n` adds soft motes (dandelion clock) |
| `glow(ctx, { pos, color, size | px, opacity })` | soft additive local glow sprite (world size or screen px) |
| `lightPool(ctx, { pos, radius, color, opacity })` | additive ground pool (lantern pools: 3-4 studs across) |
| `contactShadow(ctx, { pos, radius, opacity })` | fake contact shadow decal (bible: 0.3-0.4 opacity, 1.2x footprint) |
| `groundRing(ctx, { pos, t0, dur, r0, r1 })` | expanding ring on the ground (property-line shimmer, FWOOM ring) |
| `updateAll(root, t)` | calls `update(t)` on everything under root |

The street itself carries lamp halos (3.6 studs), split sidewalk/road lamp pools (r 7.5 studs, #ffb870, 0.32), porch
lantern halos and lit-window glows, so the night look holds without extra fx.

## `kitlib.js` (for new sets)

`Parts`: `add(key, geometry, pos, rot, scale)`, `box(key, w, h, d, pos, rot, { tile, bevel })` (world-tiled UVs),
`bar(key, a, b, w, t)` (a beam between two points), `cyl(...)`, `push(matrix)` / `pop()`, `build(M, { name, cast, receive })`
-> one mesh per material key. Material keys `M('family:#albedo')`: `siding brick shingle stone flag porch wood trim lawn grass
dirt concrete kerb asphalt line plaster bark pine bush door doorEdge shutter glassDark win emissive metal black brass plastic
tulip stem basic dirtPatch` (tile sizes in `TILE`). `texMat(key, map)` registers a textured material for custom keys
(signs, plaques). Textures: `siding`, `asphalt`, `fieldstone`, `louvre`; decals `windowInteriorTex`, `doorTex`,
`plaqueTex`, `signTex` (bold sans black on white, red header; Montserrat is not installed offline, DejaVu Sans Bold is
used), `moonTex`, `ringTex`, `blobAlphaTex`; geometry `boxUV`, `prismGeo`, `planarUV`, `scaleUV`, `trs`.

## QA (night exteriors vs references)

`node tools/render.js engine/kit/_sets_qa.js <dir> times=0.5,1.5,2.5,3.5,4.5,6.5,7.45,8.5,9.5 quality=final`
(shots: street, lawn, porch, closeup, porchOut, plan (5.5, debug top-down of all slots), dusk, magic, dawn, props).
Stand-in characters come from `lookdev/js/chars.js` (gnomes normalised to 2.0 studs, an R6 kid); the character kit's
`makeGnome` drops onto the same slots (both face +Z). Stills from the final calibration are in
`scratchpad/rbx/test5/sets/` (not in the repo). `python3 -I lookdev/tools/stats.py`, caption band masked:

| still | mean L | hi | lo | sat | crush | target (VISUAL_BIBLE §5) |
|---|---|---|---|---|---|---|
| 01 street wide (P1) | 64 | #8786e0 | #000000 | 0.60 | 20.0% | mean 60-95, sat 0.45-0.6, crush <= 25%, lo #000-#0e1237 |
| 02 single lawn (P1) | 65 | #948bca | #020004 | 0.61 | 8.2% | same |
| 03 porch (porch glow) | 84 | #beb0d6 | #040001 | 0.50 | 8.5% | same, warm accents survive (R-B +6) |
| 04 lawn close-up (P1 high-key) | 96 | #c4bdea | #0d0411 | 0.44 | 1.5% | lawn close 75-100, hi #b3b6fc-#c4c3fc |
| 05 porch out (porch glow) | 59 | #8b86da | #010005 | 0.64 | 8.9% | mean 60-95 |
| 06 dusk garden (frame-1 look) | 73 | #e9b87c | #100612 | 0.62 | 0.0% | 90-110, sat 0.6-0.75 (this framing is mostly shaded wall) |
| 07 magic glow (P3) | 132 | #f4d5ac | #250c10 | 0.52 | 0.0% | 130-150, hi #f2cfbc-#fde3c7, sat 0.4-0.5 |
| 08 dawn street (P4) | 128 | #ecd2ae | #341e17 | 0.39 | 0.0% | 135-150, hi #fcf4d9-#f8d09e |

References, same tool: TF suburb house 34.6 s mean 41 (hi #776edd, sat 0.53, crush 24%), TF aerial 107.6 s 61 (hi
#958ed8, sat 0.61), AW 1.2 s 55, AW 21.0 s 27, PN 96.4 s 41 (warm), PN 55.0 s 43. Our night frames sit in the TF suburb
colour family (periwinkle whites, blue-violet mids, black void sky, warm windows as the accent) and are lifted ~+20 luma
as EP01 asks ("high-key night, never dark navy"). Highlights stay below the #c4c3fc output white (no luma clipping).

## Performance (SwiftShader, 1080x1920)

Street wide at `quality=fast`, 1 worker, machine shared (load ~4): ~700 ms/frame with 6 point lights, ~530 ms without
(each point light costs ~30 ms/frame: keep the defaults, 3 lamps + 1 lantern + 1 window). Geometry is not the
bottleneck (6 vs 3 lots per side: same time). Glazed lookdev gnomes add ~30 ms each when large on screen. First build of a
street costs ~2 s per worker (textures are generated once, then cached). Sun shadows (dusk/dawn/day) add one 2048 map.

## Known limits / next steps

- Trees are one style (stacked-cone pines; leafy trees exist as an extra); keep one style per shot.
- No zebra crossing, driveways or garages yet (AW/TF have them); `houses` overrides cover per-lot needs.
- The dusk frame-1 composition should be re-measured once the real shot exists (target mean 90-110).
