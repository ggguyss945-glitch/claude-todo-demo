
## Creatures + cast (EP01 full episode) - `kit/creatures.js` + additions to `kit/cast.js`

```js
import * as K from '../../kit/chars.js';        // cast additions come through chars.js (and index.js)
import * as C from '../../kit/creatures.js';    // moles, mound field, dog, whale, flashlight (+ re-exports theoAt, makeBadge6, addBadge6)
```
Same conventions as README_CHARS.md: builders return a root in **metres** with content in **studs** (STUD 0.32), faces +z,
feet / mound base at y 0. Every animation call is a **pure function of shot time t**; geometry/materials/textures are cached
per worker; per-instance state (tentacle vertices, eye-level materials) is owned per mesh, so `ctx.instance()` clones are
safe. Frames are bit-identical with 1 or 2 workers (checked). The approved test shots (s01-s04) still render pixel-identical
after the cast.js changes (checked by md5).

QA (stills only): `node tools/render.js engine/kit/_creatures_qa.js <dir> times=... workers=2 quality=final` (19 shots,
shot i = [2i, 2i+2); names in the file). Stills + reference comparisons: `scratchpad/rbx/ep01/assets/creatures+cast/`.

### Giant star-nosed moles (`moles`, bible 2.6 / 3.2)
`C.makeMole({ preset, scale, seed, lod, mound, crumbs, blades, claws, body, headFur, snout, fur, eyeColor, units })`
- One mole = a **turf mound** (3.0 x 0.82 studs at scale 1, the lawn's own grass texture mapped in world xz so it melts
  into the lawn; cracks with wet soil, torn soil rim, grass tufts, 36 soil crumbs) whose **head stays under the turf**:
  only the **two bike-reflector eyes** (in soil-ringed holes) and the **pink star nose** (nostril pad + 22 fleshy rays,
  Eimer's-organ bumps, ringed segments) break the surface. Under the turf there is a full sculpt: velvety dark head
  (sheen), huge digging paws with 5 ivory claws, a plump body; `emerge` brings them out.
- `MOLE_PRESETS`: `lawn` (1), `small` (0.72), `runt` (0.58), `old` (1.15), `big` (1.8, the "BIG ones" cheat), `giant` (2.4);
  any `seed` changes the mound lumps, cracks, crumbs and ray lengths ("dozens"). `lod`: `hero` (~25k tris) / `mid` / `low`.
- Parts: `mound` (`moundTurf`, `moundBlades`, `moundCrumbs`), `moleUpper` (emerge pivot) > `moleHead` (`headFur`, `snout` >
  `snoutDisc`, `snoutMuzzle`, `tentacles`, `eyeL/R` > `eyeDomeL/R`, `eyeCapL/R`, `eyeLidL/R`, `eyeHaloL/R`, `eyeGlintL/R`),
  `pawL/R`, `moleTorso`, `moleShadow`.
- Pose: `C.setMole(m, { t, rise, open, recoil, sniff, emerge, eyes, flash, look: [yaw, pitch], wriggle, crumbs, breathe })`
  - `rise` 0 flat .. 1 up (overshoot ok); `open` 0 closed bud .. 1 open rays; `recoil` 0..1 snout snapped back, rays clenched;
  - `emerge` -1 hidden / 0 snout + eyes (default) / 0.5 peek (head up, paws flat on the turf, claws over the rim) / 1 out to
    the shoulders; `eyes` 0 dark .. 1 lit (emissive x3.2 with fake retro-reflection, brightest facing the camera, + halo);
    `flash` 0..1 reflector flash (x2.6 + a 4-point star glint per eye). Rays always wriggle +-10 deg at 2-3 Hz and the
    mound breathes, so a mole is never frozen.
- Cue sheet (one call per frame): `C.animateMole(m, t, { rise, riseDur, unfurl, eyesOn, eyesOff, flash, recoil, sink,
  sinkDur, sniff: [t0, t1], emerge: [[t, v], ...], look })` (all shot seconds). With `unfurl` and no `emerge`, the head waits
  under the turf and pushes the snout out just before it opens ("the turf splits"). `sink` deflates the mound in 0.5 s and
  winks the eyes out (2 frames) 0.12 s later.
- Curves: `moleRise(t, t0, dur=.5)` (outBack), `moleUnfurl(t, t0, .3)`, `moleRecoil(t, t0)` (0.15 s spring snap),
  `moleSink`, `eyesOn(t, t0)` (3 frames), `eyesOff(t, t0)` (2 frames), `reflectorFlash(t, t0)`; `setMoleEyes(m, level, { flash })`.
- Board use: s36 `animateMole(m, t, { eyesOn: evT('eyes'), flash: evT('reflectors') })` with a warm practical behind the lens;
  s37 small mole `{ unfurl: evT('moles'), sniff: [...] }` + `makeMole({ preset: 'big' })` with `emerge: [[0, -1], [tBig, 0.55]]`;
  s53 `sniff`; s55 eyes at the glass: a mole with `emerge: 0.5`, `eyes: 1`; s58 eye pairs at the ring edge; s79 `sink`.

### Mound field (`mole_field`): many moles as bulges under one shared turf sheet
`const f = C.moleField(ctx, { center: [x, z] (world m), size: [w, d] (studs), yaw, res: 128 (hero lawn) | 64, seed,
heads: 'snout' | 'eyes' | false, lod: 'mid', height: [0.6, 0.9] }); ctx.add(f.group);` then register events in `build()`
and call `f.update(t)` in `update()` (pure function of t; ~5-10 ms per frame):
- `i = f.add({ at: [x, z], scale, height, head, face: [x, z] | yaw })` (world metres; `face` = what it looks at when still)
- `f.rise(i, t0, dur)`, `f.sink(i, t0, dur)`, `f.eyes(i, tOn, tOff)`, `f.recoil(i, t0)`
- `f.travel(i, [[x, z], ...], t0, speed=3)` Catmull path, studs/s; a bulge wave (steeper front) with a 0.25-stud trench
  ridge that relaxes over 3 s; `f.stopAt(i, [x, z], radius)` stops it at a light ring's edge (bulge flattens, snout recoils)
- `f.swallow(i, targetObject3D | [x, z], t0, { depth, radius })` GULP: turf lips rise round the target (0.12 s), close over
  it like a mouth while it sinks in 6 frames (it is hidden when gone), then a dome deflates to a low seal
- `f.pushBack([x, z], r0, r1, t0, dur=.5)` the FWOOM / "backed off" tide; `f.heightAt([x, z], t)` turf height (m)
- `f.moles[i].head` is the riding mole (snout + eyes at the bulge front, fur hidden: the turf is its head).
- The sheet only shows where it is raised (alpha fades flat turf out), so it can lie over beds, paths and stones.

### Next door's dog REX (`dog`)
`C.makeDog({ coat: '#c98a4a', patch: '#f2ece2', ears: '#6a3a1e', saddle, collar: '#d0242a', head: 0.8 })`: Roblox-built
beagle (painted box body 2.2 x 1.0 x 1.1, 0.35 x 0.7 legs, drum head with a decal face (^^ eyes, blaze, blush), white
muzzle block with a glossy nose and a pink tongue, floppy hinged ears, stub tail, red collar + gold tag + `leadSocket`).
`C.dogAt(dog, t, { pose: 'stand' | 'sit' | 'lie' | 'chew', wag: 1, wagFreq: 6, look: [yaw, pitch] })` (tail +-25 deg at
6 Hz, chew = head down 25 deg bobbing at 2 Hz, ears lag the head, breathing); `C.setDogPose(dog, nameOrObj)`, `DOG_POSES`.
Lead: attach the fx/prop lead to `dog.getObjectByName('leadSocket')` (s13 uses the empty kennel only).

### Theo's whale, Grandpa's flashlight
- `C.stuffedWhale({ color: '#7f93ad', belly: '#dfe6ee', length: 1.4 })`: plush (sheen, fabric normal), big round head,
  belly grooves, stitched smile, button eyes with a glint, felt fins, curled tail with flukes, felt spout tuft.
  `C.holdWhale(avatar, whale, 'hug' | 'underArm' | 'asleep' | 'hand')` parents it at real size (compensates Theo's 0.85).
  Use pose `K.POSES.hug` / `carry` with `'hug'`.
- `C.makeFlashlight({ on, cd: 18, angle: 22 })`: red rubber body, chrome head, glowing lens + glow sprite, SpotLight
  `torchLight`. `C.holdFlashlight(avatar, torch, { side: 'R', axis: 'arm' | 'forward' })` (arm: beam runs down the arm like
  a Roblox tool), `C.setFlashlight(torch, 0..1, { cd })` (click = 0 -> 1 on a frame), `C.aimFlashlight(torch, worldPoint)`
  (after setPose: e.g. s23 aim at the chin `head.localToWorld(V(0, -0.2, 0.55))`), `C.flashlightRay(torch)` -> `{ origin, dir }`
  for the fx beam.

### New cast and variants (`K.makeCharacter(name, extra)`)
| name | who | notes |
|---|---|---|
| `grandmaShort` / `heroOldShort` | s07 / s96 jump-cut shrink | scale 0.8 / 0.85, sleeves to the end of the arms (hands swallowed) |
| `heroMuddy` | dawn s82-s85 | heroBarefoot + mud on knees (0.8) and feet (0.6) |
| `theoSocks` / `theoAsleep` / `theoBadge` | s82 / s44 s55 / s44 | striped socks (0.45 band); face sleeping; "6" badge pinned |
| `grandkid` | s08 s11 | orange skin, green tee, red beanie-style cap (no pompom), sneakers |
| `heroKid5` | s64 s66 (sepia) | x0.75, freckles, messy hair, navy rocket pyjamas, sleeping |
| `grandpaYoung` / `dadKid` | s67 (B&W) | dark short hair + moustache, no glasses / x0.75 striped pyjamas, sticking-out ears |
| `cousinKid` | s68 (sepia) | x0.75, pigtails with pink ribbons, floral nightie, sleeping |
| `granddaughter` | s95 s96 | x0.85, family freckles, dark bob, lilac heart pyjamas, face sideGlance |
| `theoGranddaughter` | s93 photo | x0.75, blond pigtails, whale-print pyjamas, waving, openSmile |
| `theoMom` / `theoDad` | the new family (background) | teal cardigan + blond bob / rust tee, khakis, glasses |
| `momNight` / `dadNight` | Mom / Dad night variants | pink dressing gown + pyjamas / grey tee + plaid pyjamas |
`K.theoAt(age, extra)` (also `C.theoAt`): Theo at 7..66 for the photos (scale 0.85 -> 1, blond -> brown -> grey -> bald
with white tufts at 60+, clump beard from 40, a tee / hoodie / flannel / sweater / cardigan per decade, face grin).

Options any cast spec (or `extra`) understands on top of makeAvatar's (`K.castAvatar(spec)` builds a free spec):
`hand: 'sleeve'` (top level or `outfit.shirt.hand`), `mud: { knees, feet }`, socks `outfit.pants.shoes: { style: 'socks',
pattern: { type: 'stripes', color }, h }`, prints `outfit.shirt.print` / `outfit.pants.print = { motif: 'hearts' | 'whales'
| 'rockets', color, color2, density, size }`, extra accessories `{ type: 'pigtails', color, ribbon }`, `{ type: 'ears', size }`,
`{ type: 'beard', color, length, moustache }`, `{ type: 'cap', color, band }`, `face: 'wink'`, `pose: name | object`, `badge: true`.
- Faces: `K.EXTRA_FACES` = `wink` (s23: left eye ^ arc, right eye open, smile; same line weights). Use
  **`K.setFaceEx(avatar, name)`** wherever a shot can show `wink` (it falls back to `K.setFace` for the 19 standard faces).
- Badge: `K.addBadge6(avatar, { at: [x, y] })` (hips-local studs; default left chest, 0.45 stud at any avatar scale);
  glint position: `avatar.getObjectByName('badge6').getWorldPosition(v)` -> `starGlint` (common.js) on "six".
- Sitting the shrunk ones on a full-size seat: `avatar.position.y += K.seatOffset(avatar, seatTopStuds = 1.5)` (metres) and
  `K.setPose(avatar, K.CAST_POSES.sitDangle)` (feet dangle off the seat front, hands in the sleeves) or `sitSunk`.

### Decisions / deviations (creatures + cast)
- Moles: ASSETS/bible say only mound + snout + eyes show; the task also asked for a velvety body and huge claws. Both are
  built: the default pose (`emerge` 0) keeps the bible look; `emerge` 0.5 / 1 shows head, claws and chest (no mouth, no
  teeth ever). The 22 rays are one merged, per-frame-rewritten mesh named `tentacles` (not 22 objects `tentacle0..21`).
- Eye glow: emissive x3.2 (bible 3-5) with a more saturated amber `#ffa416`: at x4-5 ACES turned the reflectors peach-white.
- Field heads hide their fur (the turf bulge is the head); individual `makeMole` mounds keep it under the turf.
- Clothing / faces / accessories are extended **from cast.js** (overlay painting on cached atlases, extra accessory builders,
  an extra-face texture) instead of editing clothing.js / faces.js / accessories.js (owned elsewhere). `K.setFace(a, 'wink')`
  therefore shows the neutral face: call `K.setFaceEx`.
- The flashlight beam cone and the lead are FX/props (`fx_beam`, sets); the flashlight only gives a lens glow + SpotLight.

## SETS (EP01 full episode) - `kit/sets_ep01.js` + `kit/interiors.js`

```js
import * as S from '../../kit/sets_ep01.js';    // hero lot, next door, truck, SOLD, our street, back garden, photos, phone
import * as I from '../../kit/interiors.js';    // bedroom (5 eras), Grandma's room, hall, truck cab + their light presets
```

Everything is procedural, seeded and cached per worker (`ctx.cache` / `ctx.instance`; each call returns a cheap clone), pure
functions of `t`, Three.js 0.170. Sets are built in studs inside STUD-scaled groups; every root, slot, spot and view is in
**metres** (world, root at the origin). Views are `{ pos, target, fov }` and go straight into `ctx.camera.set(view)`, then
`.push(Z)` as usual. Look calibration (`lookdev/tools/stats.py`, caption band masked) is listed under QA below.

### heroLot: our front garden by time of day and era (ASSETS `hero_lot`, `hero_room` from outside, `agent_board`, `moving_truck`, `keep_off_sign`, `next_door`)

```js
const H = S.heroLot(ctx, { tod: 'night', bed: 'empty', truck: 'open', gate: 1.5 }); ctx.add(H);
ctx.camera.set(H.ep01.views.gateTruck).push(0.22);
S.heroLight(ctx, H);                            // the tod's preset (night = sets.nightLawn) + Theo's room glow
update(ctx, t) { H.ep01.update(t); }           // SOLD slap, truck leaving, etc.
```

It wraps `sets.buildLawnCloseup(ctx, { seed: 'ep01' })` (the approved s05/s09 house: lot `A1`, mustard bungalow, purple
curtains, door 14) and **cuts a real hole** in the front wall at the window over Grandpa's bed (`A1.bed0`): reveal, glass and
the real room (`I.bedroomRoom`) behind it. Root = `[set (studs clone), extras (metres: gnomes, truck, lights)]`;
`H.userData` = the street's userData (slots, lots, lamps, windows, views), so `sets.place`, `sets.slot`, presets and
practicals work on `H` as on a plain street.

| option | default | |
|---|---|---|
| `tod` | `'night'` | `'night'` / `'day'` / `'dusk'` / `'dawn'`: sets Theo's window state and `heroLight`'s preset |
| `era` | `'now'` | `'now'` (sign, board, family gnomes, Theo's room) / `'2010s'` (no board, toys on the porch, younger tree, room `hero5`) / `'1990s'` (room `cousin90s`) / `'1960s'` (no sign, blue-grey gate, small tree, room `dad60s`, 2 gnomes) |
| `year` | `0` | 0..60 years after the move: repaint by decade (`yearLook(year)`: mustard -> sage -> cream -> blue-grey -> white), grown tree (x0.85 -> x1.5), other curtains and tulips per year, room era `later`, gnome `age: year/60` (moss) |
| `bed` | era | Grandpa's spot: `'grandpa'` (K gnome on `bed0`) / `'grandpaBack'` (gnome + fresh soil ring) / `'empty'` (flattened soil ring + two boot prints) / `'plastic'` (Mom's glossy plastic gnome in the ring) / `'hole'` (sunken dark soil, crumbs, the $4.99 sticker) / `'none'` |
| `lantern`, `grandpa` | `0`, `{}` | Grandpa gnome lantern level / extra `makeGnome` options |
| `gnomes`, `lanterns` | era, `0` | family gnomes (`true`, `false` or slot names; variants as part1 `lawn_stare`) and their lantern level |
| `shiftBedFront0` | `true` | moves `bedFront0`'s gnome 1.5 studs toward the path so its lantern pool never covers the bed (ASSETS); `false` = the s09 layout |
| `truck`, `truckOpts` | `false` | `'open'` / `'closed'` / `'leaving'` + `movingTruck` / `parkTruck` options (`backOffset`, `t0`, `layout`, `balconyBox`, `dome`) |
| `board`, `sold` | era, `null` | the FOR SALE / 3 BED · BIG GARDEN / COMES WITH ANCESTORS board by the path; `sold: t0` slaps the SOLD sticker on at `t0` (shot s), `-1` = already on |
| `keepOff` | era | KEEP OFF THE LAWN AFTER DARK post sign beside the gate |
| `gate` | `0` | gate leaf open angle (rad, 0..1.9) |
| `bricks` | `true` | dog-tooth brick edging in front of Grandpa's bed (the "bricks" of 61.4 s): `H.ep01.bricks[i]` are separate meshes (jostle one loose) |
| `theoRoom` | era | `{ era, lit, curtains: 'open' | 'half' | 'closed', curtain }` or `false` (dark glass, no room) |
| `roomGlow`, `roomLevel`, `haze` | `true`, `1`, `0.85` | exterior read of the lit room: a warm 12 cd fill inside + the nightlight + an additive warm haze on the glass (continuity with the approved warm windows of s05/s09) |
| `nextDoor` | `true` | dresses lot A2 (below); `{ plastics, holeX, holeZ }` or `false` |
| `tree`, `toys` | era | tree scale override; 2010s porch toys |

`H.ep01` handles: `set`, `lot` (lot group, studs), `gnomes { grandpa, plastic, family: { slot: gnome } }`, `truck`, `board`,
`sticker`, `sign`, `gate`, `bricks[]`, `nextDoor`, `spots`, `views`, `room` (world anchors of the room: `lamp`, `nightlight`,
`windowWorld`, `sleeper { head, body, yaw, top, bed }`, `clock`, `views`), `update(t)`, `light(ctx, opts)`, and Theo's window:

- `H.ep01.setTheoWindow(k)` = `H.ep01.theo.setLevel(k)`: room light level (0 = dark: lamp shade off, projected stars off,
  glow lights hidden, window spill marked unlit in `userData.windows`). This is the `fx_window_dark` hook (s46 "goes DARK").
- `H.ep01.theo.setGlass('outside' | 'inside' | 'dark' | 'day' | 'photo')`; `H.ep01.theo.setInterior(true)` turns the exterior
  glow off for interior shots (`I.bedroomNight` calls both). `H.ep01.theo.glass` is the 4 x 5 stud pane (target for
  `fx_glass_fog`); `theo.haze`, `theo.room` (the room group), `theo.winGlow`.

**Spots** (`H.ep01.spots`, metres): `bed0`, `bed0Yaw`, `theoWindow` (outer glass centre), `theoSill`, `gate`, `door`, `steps`,
`houseFront`, `bricks`, `board`, `truckBack`, `ramp`, and the lot slots `bedFront0/1`, `lawn0..3`, `porchSteps`, `gateIn`,
`gateOut`, `windowLook`, `lawnMid`.

**Views** (`H.ep01.views`; shot = board number): `boardMS` s10, `tapHat` s16, `gnomeCU` s18, `lapTop` s22/s63 (top-down, house
at the top), `streetWS` s25 (truck back in the left third), `emptySpot` s27, `runOut` s28, `gateTruck` s29, `theoWindowOut`
s45/s68/s69, `theoWindowHigh`, `profileWS` s46, `ramp` s49 (top-down), `bedKneel` s50, `bedLow` s51, `moundsLow` s52,
`tulipsCU` s53, `bricksCU` s54, `highWS` s56, `standGuard` s57, `kneelLow` s73, `quietWide` s81, `dawnLow` s82,
`fromTruckTele` s89, `photo` (the yearly photo framing); room views `room_toWindow` s66/s67, `room_sleeperCU` s44,
`room_fromBed` s55/s71, `room_sleeperHigh` s72, `room_otsWindow` s17; next door `nextDoorMS` s12, `kennelTop` -> `holeTop`
s13 (truck between them), `nextDoorNight` s41. **Porch column:** it stands 2.6 studs right of Theo's window, so keep outside
views of that window at yaw <= 0 (the board's s45 "yaw 20" puts the column across the right of the frame).

`S.heroLight(ctx, H, opts)`: night `sets.nightLawn`; day `sets.day` with the sun from the street side (az 160, el 45: the
kit's az -40 back-lights every front lawn) and exposure 1.15 (shot `quality: { shadows: 'pcfsoft' }`); dawn `sets.dawn`
(sun az 150 el 12, exposure 1.7); dusk `sets.dusk` (exposure 1.65). Any preset option passes through (`skyPreset`, `moon`,
`window`, `postOpts`...). Day/dawn switch Theo's room off unless `keepRoom: true`.

### Next door (lot A2): `S.dressNextDoor(ctx, set, extras, o)` (done by heroLot)

Three glossy plastic gnomes in a row facing the STREET (`K.makePlasticGnome({ finish: 'glossy' })`, $4.99 stickers, black
lanterns that never light), the red kennel with a REX board, bowl and ball, a hose reel, the red lead (tube on a Catmull curve)
from the kennel ring across the lawn into THE HOLE (0.9 stud dark disc with a lip of crumbs). `H.ep01.nextDoor`: `gnomes[]`,
`lead`, `hole`, `kennel`, `ringW`, `holeW`, `dogSpot` (where the dog lies chewing the first gnome's hat, s12),
`tug(t, t0)` (s13: the lead pulls 0.1 stud toward the hole with a spring).

### Moving truck: `S.movingTruck(ctx, o)`, `S.parkTruck(truck, set, lotId, { backOffset: -8 })`

`o = { mode: 'open' | 'closed' | 'leaving', layout: 'stack' | 'aisle', balconyBox, dome: true, domeCd: 1.5, door, t0, vmax: 6,
accel: 3 }` -> Group in metres (cab +Z, open back -Z). Props' 24 x 9 x 10 truck + separate spinning wheels, a cargo stack
(`stack`: near the open back, for s25/s29/s49; `aisle`: boxes along the walls, for the s88 POV), the separate **BALCONY GNOME**
box on top (`truck.ep01.balconyBox`, hinged `flapL` / `flapR` to rip open), the cargo dome light (emissive + 1.5 cd point
light + halo), the roller-door drum (door up) or the closed roller door, the ramp (`open` only). `truck.ep01`:
`update(t)` (leaving: 0 -> 6 studs/s from `t0`, wheels roll, a small engine judder), `dist(t)`, `backCenter(t)` (world point,
a camera target), `povCamera({ height, back, pitch, yaw, fov })` -> ShotCamera spec that rides inside the cargo bay looking out
of the back (s88). `parkTruck` parks it at the kerb with the open back 8 studs left of the gate, cab toward -X, so the open
back reads through the open gate (s29) and the ramp runs along the road past the gate.

### SOLD sticker: `S.soldSticker(boardMesh, { t0 })`
Red rounded "SOLD" decal laid diagonally on an agent board; slaps on at `t0` (scale 1.3 -> 1 in 4 frames, outBack);
`sticker.update(t)`. heroLot's `sold` option uses it.

### Our street: `S.ep01Street(ctx, { lanterns, heroLike: true, truck, tod, skip })`
The 6-lot street of the approved s01 (`seed 'ep01'`, hero `A3`) with one or two gnomes per lawn placed exactly like part1's
`streetGnomes()` (same seeds), Grandpa in our bed, next door (`A4`) with plastic gnomes facing the street. `heroLike` restyles
our house A3 like heroLot's bungalow (`S.HERO_HOUSE`; s01 never shows it). `T.ep01.gnomes` = `[{ g, lot, slot, pos, plastic,
dist }]` sorted by distance from our gate (for `fx_lantern_cascade`), `T.ep01.grandpa`, views `aerial` (s43), `alongLawns`
(s35/s40) + the street's `streetWide`, `streetHigh`, `porchOut`...

### Back garden (epilogue): `S.backGarden(ctx, { tod, windowLit })`, `S.backGardenLight(ctx, G, { tod })`
The back of a two-storey sage house (wall at z = 0 facing the garden), the granddaughter's ground-floor window lit pink-warm
(curtains open, a star nightlight), a flowerbed and pots along the wall, a bird bath, a shed, dandelion clocks and daisies, a
low white fence and pines (lower behind the deck chair so the moon clears them), the striped deck chair facing the window,
a slatted garden bench, the teak garden table (8 x 5, a mustard mug, reading glasses). `G.ep01.release` is the separate
dandelion beside the chair (hide its puff under the s97 burst). Anchors (`G.userData.anchors`, metres): `window`,
`chairSeat` (+`chairYaw`), `benchSeatL`, `benchSeatR` (+`benchYaw`), `tableTop`, `pile`, `release`, `door`. Views: `tableTop`
s90, `phoneECU` s91, `otsPhone` s92, `benchCU` s94, `benchMS` s95/s96 (the s06 numbers: h 3.6, d 7.5, yaw -15), `windowReverse`
s97, `gardenWide`. `backGardenLight`: `dusk` (sun az 75 el 7, exposure 1.75), `blueHour`, `night` (galaxy + TF moon az 166
el 30 behind the chair, window spill 3.5 cd from behind the lens).

### Yearly photos, Polaroids, phone (render-to-texture)
- `S.photoTexture(ctx, year, { blink, girl, headYaw: 150, person, size: 512, exposure })` -> `{ texture, canvas }`: the hero
  lot in spring daylight `year` years after the move (`heroLot({ tod: 'day', year })`), Grandpa gnome mossy by `year/60`
  looking back over his shoulder at the camera, Theo at `6 + year` beside him (`K.theoAt` when present, else
  `S.theoAtFallback`), this year's tulips/curtains/paint. Rendered ONCE per worker (HDR target -> ACES + a light print look:
  lifted warm blacks, saturation 0.88, soft inner vignette -> readback). `blink: 0.55` + `girl: true` = the s93 photo.
  `S.PHOTO_YEARS = [1, 5, 10, 16, 25, 33, 40, 52, 60]`.
- `S.polaroid(ctx, year, { label })` -> card Mesh in metres (3.5 x 4.2 studs, white border, hand-written label '1st spring',
  '10'...); `S.polaroidStack(ctx, years, { at, t0s, dur })` -> group whose `update(t)` drops the cards one by one onto a pile (s90).
- `S.phone(ctx, { photos: [years], name: 'Theo' })` -> Group in metres (1 x 2 studs, screen +Z): a gallery strip (status bar,
  "Theo / just now", the photo, likes); `phone.ep01.swipe(t, [t0...])` slides the next photo in from the right in 8 frames
  (outCubic); `phone.ep01.show(i)`. Attach it to `K.handSocket(heroOld)`.

### Interiors (`interiors.js`)
- `I.bedroomRoom(ctx, { era, curtains, curtain, duvet })` -> the bare room in studs (room frame: origin on the floor at the
  inner face of the window wall, centred on the window, +Z out through the window; x -5.2..8.8, z -12..0, height 10 = the
  bungalow storey). Eras (`I.ROOM_ERAS`): `hero11` (blue fabric wall, carved bed + magenta duvet, posters, shelf with books /
  toy car / teddy, pink shag rug, glow-star stickers, nightstand + lamp, clock), `theo` (half-empty: bare mattress on the floor,
  boxes THEO, lamp on a box, ghost rectangles + bare hooks where posters were, star projector + projected stars),
  `hero5` (small bed, rocket duvet, toys), `dad60s` (rose stripe, iron bed), `cousin90s` (yellow floral, bunk bed, girl on
  top), `later` (blue duvet). Use it through `heroLot` (`theoRoom`) so it sits behind the real window.
- `I.bedroomNight(ctx, { set: H, lamp: 4, nightlight: 2.5, moon: true, lanternOutside: false | true | { pos, cd } })`: bible
  P2 (hemi #b9a8ff / #5a2a4a 1.8, key #e8deff 1.0, lamp + halo, moonlight 0.4x through the window, warm lantern spill
  outside, galaxy sky), switches heroLot to interior mode (exterior glow off, darker inside glass: the window view stays
  darker than the room), post `bedroom` at exposure 1.5 / saturation 0.92 (calibrated on TF 24.0 / 40.2 s).
- `I.grandmaRoom(ctx)` (s06/s07): rose wingback armchair (seat top 1.5), shag rug, standard lamp, side table with teacup +
  knitting basket, net-curtained window with daylight, cuckoo clock, framed photos on rose wallpaper, cabinet, footstool,
  plant. Anchors: `seat`, `lamp`, `window`, `table`, `rug`; views `armchairMS` (the s06 numbers), `armchairCU`, `wide`.
  `I.interiorDay(ctx, { room })`: hemi #ffe8d0 / #6a4a3a 1.1, window key #fff3e0 2.0, lamp 2 cd + a window spill, post `day`.
- `I.hall(ctx)` (s26): 8-stud hall, dark red front door with a 4-pane glass panel onto a night-garden card, the clock
  (`hall.ep01.setClock(h, m, s)`, `hall.ep01.tickToNine(t, t0)`: 8:59:59 -> 9:00 with a 3-frame overshoot on "nine"),
  rolled sleeping bag, three THEO boxes, coat hooks with the mustard hoodie, runner rug, bare picture hooks. View `clockINS`.
  Light: `I.bedroomNight(ctx, { room: hall })` + a ceiling-lamp point at `hall.userData.anchors.lamp`.
- `I.truckCab(ctx, { time: '11:52', note: 'LEAVE 6 AM' })` (s48): dashboard, red 7-segment LED (`cab.ep01.update(t, T)` blinks
  the colon at 1 Hz on episode time), steering wheel with the yellow sticky note, a cup, a map, the night street card behind
  the windscreen. Views `clockINS`, `ledECU`. `I.cabNight(ctx, { cab })`: LED glow 1 cd, street spill 4.5 cd, hemi 1.6.
- Helpers for other builders: `I.XM(key)` (material keys `wp:` / `floor:` / `ceil:` / `fab:` / `rug:` / `glow:` / `gloss:` /
  `net:` / `tex:`, falling back to kitlib `M`), `I.decalMat`, `I.ctex`, `I.rect`, `I.wallWithHoles`, `I.posterTex`,
  `I.wallpaperTex`, `I.clockMesh` + `I.setClock`, `I.addBed`, `I.addCurtains`...

### QA (stills only)
`node tools/render.js engine/kit/_sets_ep01_qa.js <dir> times=0.5,1.5,...,30.5 quality=final workers=2` (31 shots, one per
item in story context with the cast kit as stand-ins). Final stills, a contact sheet and reference comparisons:
`scratchpad/rbx/ep01/assets/sets/` (not in the repo). Cost at `final`, 2 workers: first build of a hero-lot shot ~1.3-1.7 s
per worker (cached after), render ~0.5-0.7 s per frame; each photo texture is a one-off ~0.3 s per worker.

| still | p50 | hi | sat | target |
|---|---|---|---|---|
| s45 window out (night) | 108 | #b8ade0 | 0.43 | lawn close 75-100 (approved s09 render: p50 86, hi #c1b9e6, sat 0.42) |
| s70 lawn stare, lanterns lit | 95 | #baaddc | 0.42 | same |
| s44/s55 Theo's room (bedroom) | 98 | #cfb5e3 | 0.52 | P2 105-125, hi #d4bced-#e7d4fc, sat 0.45-0.6 (TF 24.0 s: 157 / #dec4ec / 0.37) |
| s17 OTS / hero11 wide | 109 / 91 | #c5a9d7 / #c19ddc | 0.48 / 0.60 | same |
| s06 Grandma's room (day) | 132 | #e9dac2 | 0.50 | DAY 110-155, whites #f2e0c1-#fcfcf6, sat 0.5 |
| s10 board / s12 next door (day) | 183 / 102 | #dbd1c7 / #d8cec4 | 0.29 / 0.45 | DAY 110-155 |
| s25 SOLD + truck (dusk) | 83 | #e19063 | 0.61 | DUSK 90-110, sat 0.6-0.75 |
| s95 bench (dusk) | 53 | #e78156 | 0.63 | DUSK (back-lit sky framing) |
| s82 dawn / s88 truck POV | 59 / 69 | #f5ddb9 / #f8e1be | 0.51 / 0.47 | P4 135-150, hi #fcf4d9-#f8d09e (low framings with a lot of lawn) |
| s26 hall / s48 cab | 144 / 13 | #c5a9db / #9c7795 | 0.48 / 0.79 | night interiors (the cab is a dark insert: the LED and note read) |

### Notes and requests to other owners
- `fx_curtains` (dusk street curtain cascade, s11) is the effects owner's (`fx_ep01.curtainCascade`); window positions are in
  `set.userData.windows` (lit, tone, pos per lot). `fx_glass_fog` targets `H.ep01.theo.glass`; `fx_window_dark` =
  `H.ep01.setTheoWindow(0)`; `fx_lantern_ring` / `fx_lantern_cascade` can use `H.ep01.spots.bed0` / `T.ep01.gnomes`.
- props.js (not mine): `addAgentBoard` puts the sign texture on the back face too, so the board reads mirrored from the house
  side (s17); `addCardboardBox` uses the wood-plank material, so boxes read as wooden crates in close-ups (a kraft-card
  material would help s26/s49).
- The room is 10 studs tall (the bungalow storey), not the bible's 12-13: it lives inside the approved house.
- Theo's window from outside reads pink-warm (lit room + glass haze), close to but not identical with the approved
  emissive window of s05/s09 (stats above); `haze`/`roomLevel` tune it per shot.

## SOUND (EP01 full episode) - `episodes/ep01/sound/`

Sound library + mixer for the whole 113.30 s episode: the owner's VO on top, every SFX cue of `ASSETS.md` / `board.md`
at its picture event, ambience beds per shot, 48 kHz stereo out. Python only (numpy/scipy/soundfile/pyloudnorm, ffmpeg
for mp3 decode); every procedural sound is seeded (`crc32` of a string), so every run is bit-identical.
Run everything with `python3 -I` from anywhere (scripts add their own folder to `sys.path`).

```bash
S=roblox-shorts/episodes/ep01/sound; R=<scratch>/rbx
python3 -I $S/catalog.py                     # render + measure every cue -> sfx_map.json (gains), previews <scratch>/ep01/sound/cues/*.wav
python3 -I $S/mix.py                         # full mix (profile 'bible') -> <scratch>/ep01/sound/out/ep01_mix.wav + stems + report
python3 -I $S/mix.py --range 0 5 --compare $R/test5/sound/test5_mix.wav    # the 5-s test check
python3 -I $S/mix.py --profile standard|full|primary --out DIR [--no-stems] [--music MUSIC.wav]
python3 -I $S/qa.py STEMS_DIR OUT_DIR --test ... --refs $R/ref60 --refstems $R/metrics/audio/stems   # 1080x1920 QA sheets
python3 -I $S/synth.py [OUT_DIR] [design ...]  # write the procedural designs as WAVs
```

### Files
| File | What |
|---|---|
| `synth.py` | 48 procedural designs (`DESIGNS` dict + parametric functions): `tik(slow)`, `ceramic_tok`, `plink`, `reflector_flash`, `lantern_light` (tink-whoosh), `lantern_cascade(times)`, `rumble(dur, move)`, `squeak/chitter/fip` (mole squeaks), `sniff(size)`, `gulp`, `fwoom`, `breath_glass`, `step_wet/feet_run/walk(times)`, `rip`, `flutter`, `plastic_knock/thunk_plastic/clatter`, `deflate(n, gap)`, `blips(times)`, `engine(crank)`, `rattle`, `photo_drop(times)`, `creak/door_creak/lantern_creak`, `grind(soft)`, `kneel`, `set_down`, `squeak_toy`, `chain_tug`, `hops(times)`, `bonk`, `poof_soft`, `ripple_shimmer`, `thud_low`, `tide`, `brick`, `slap_sticker`, `curtains`, `room_tone`, `mower`; helpers `verb(x, 'night'|'room'|'hall')`, `tine(f)` (music-box tine), `Lib` (read-only access to the extracted Epidemic files) |
| `catalog.py` | `CUES` (58 cues) and `BEDS` (11 beds): source, in/out, sync, offset, filters, fades, reverb, target level, priority, layer, placement rule. `render_cue(cid, times, shot)`, `bed(name, t0, t1)`, `momentary()`, `band_peak()` |
| `sfx_map.json` | Generated catalog: every cue -> `source` (`file` + `in`/`out` s, `synth` design, or `layers`), `sync`, `offset`, `hp`/`lp`, `fin`/`fout`, `target`, `measured_lufs`, **`gain_db`**, `prio`, `layer_of`, `rule`; every bed -> loop `in`/`period_s`/`xfade_s`/`phase_s`, filters, **`gain_db`**, 10 s loudness |
| `mix.py` | Resolver (timeline events -> placements), voice leveler, SFX bus + ducker, beds, master limiter, report |
| `cue_sheet.json` | Every resolved placement of the last full mix: `cue, t (picture event), times, start/end (clip span), shot, word, prio, layer_of, gain_db` + what the profile left out |
| `cue_times.json` | Multi-hit times the picture should match: HOPS s14, FEET_WET s28, TINKS s40, STEP_WET s62-s64, DEFLATE s79, BLIPS s80, DROPS s90, SWIPE s92 |
| `music_cues.json` | Voice pauses; `planned: true` = the board's 4 pauses (28.87-29.72 "empty", 48.44 "fence", 82.58 "flower bed", 103.12-103.455 before "Every spring"): drop the owner's music there |
| `qa.py` | QA sheets (spectrogram stills of sound) |

### How a cue is placed
- Cue names come from the timeline: each event's `sfx` string and each shot's `sfx_cues` are tokenised
  (`GRIND (soft)` -> `GRIND_SOFT`, `SNIFF (distant)` -> `SNIFF_FAR`, `distant rumble` -> `RUMBLE_FAR`; bed tokens and
  tails such as `M1 tail`, `FWOOM tail`, `ENGINE fades` are skipped). Extra picture events without an `sfx` string are
  hooked by word: `FLASH` on s36 "reflectors", `SNIFF_BIG` on s37 "big".
- Clip start = event `t` + `offset` - `sync` (`sync` = the transient / whoosh peak inside the trimmed clip). E.g. LATCH
  lands 0.10 s after "out" (the gate swings 6 frames), TINK_WHOOSH starts 0.12 s early so its swell peaks on the light-up,
  FWOOM starts 0.28 s early and its hit lands on 86.86 (the vowel), the second pulse on "flared" (+1.06 s).
- Multi-hit rules: `shot_events` (BLIPS, DROPS, SWIPE: one hit per later event in the shot), `cascade` (TINKS: seeded
  0.15-0.3 s gaps from "every" fitted to end on the "lit" event), `feet` (every 0.25 s to the cut; s56 = a 2-step plant),
  `steps` (s62: every 0.44 s until the s64 "stop" event), `deflate` (6 x 0.15 s), `hops` (5 x 0.22 s ending 0.18 s
  before the bonk), `shot_start`, `shot_at` ("at 100.37").
- To move a sound onto the picture: write `episodes/ep01/sound/cue_times_override.json` = `{"TINKS": {"times": [...]}, ...}`
  and re-run `mix.py` (the first time becomes the cue time).

### Levels (the approved test's method)
- **Voice**: 24 -> 48 kHz (exact 2x polyphase), HPF 60 Hz, dual-mono. Phrase leveler: sentences merged to >= 2.5 s
  groups (31 groups), each set to **-16 LUFS** (gated), clamped to the whole-take gain +-3 dB (+2.87 dB), gain changes
  only in the gaps. Group 0 is measured on the test's window 0.20-3.42 s -> +3.236 dB, exactly the test's.
- **Cues**: `gain_db` brings each cue to its target: `mmax` (max 400 ms momentary loudness, LUFS), `win` (the test's
  integrated-over-window method, W1/M1/P1) or `band_peak` (SUBBOOM: 25-110 Hz 100 ms peak -15 dBFS = +3.9 dB over the
  mix RMS, like TF 40.85; CG is +10.6). Typical targets: small foley -27..-33, creature/medium -24..-28, signature hits
  TINK_WHOOSH/TINKS -23, GULP -21, FWOOM -18 (its 5-14 kHz air sits +4.7 dB over the voice's own top end while it rings).
- **Ducker**: the non-approved SFX bus is ducked only between 200 Hz and 5 kHz (sub and sparkle untouched) when its
  300-4000 Hz band comes within 12 dB of the voice's (150 ms voice hold, 10 ms attack + look-ahead, 150 ms release,
  max 10 dB). The approved test cues (W1, M1, P1) are not ducked (they are the approved balance).
- **Beds** (one per shot, 30 ms equal-gain crossfades on the cuts, no crossfade inside a run of the same bed; the source
  position is absolute episode time, so a bed that returns continues where it would be):
  `A_NIGHT` crickets (test A1: file 32-37 s at t 0, HPF 250, -2.09 dB, -33 LUFS; loop period 113.30/4 so the last frame
  continues seamlessly into frame 0), `A_NIGHT_OLD` (sepia, LPF 6 k), `A_NIGHT_BW`, `A_NIGHT_CAB` (s48), `A_DAWN` -33,
  `A_DAY` -32.5 (+ distant mower), `A_DUSK` -34 (+ first crickets), `A_ROOM` -40 (room tone + far wall clock + crickets
  through the glass), `A_ROOM_DAY` (s06-s07, birds through the window), `A_ROOM_OLD` (s66-s67), `A_HALL` (s26, the clock
  close). Automation: s27 silence beat (night -14 dB from 28.87 until the door-bang cut), s97 dusk -> night (crickets at
  the opening level on the last frame).
- **Master**: sum, 10 ms end fade, true-peak limiter -1.2 dBTP (the test's). No music: the owner adds it ~8 LU under the
  voice (-24 LUFS) and drops it in the planned pauses (`music_cues.json`; `--music` previews that).

### Profiles (density)
`bible` (default) = the board's 22 primary cues (24 cue IDs with SNIFF_BIG and GRIND_SOFT) + the layers that belong to a primary event (CRUMBLE, PLINK, FLASH
under SUBBOOM; FEET_WET under DOOR_BANG; SHIMMER_S under CLINK; PASS under FWOOM; RATTLE under ENGINE; SNIFF_BIG):
25 events = 13.2 per minute (bible 8.2: 6-12; the board's primary list already sits at the top). `standard` adds p2
sweeteners by rank (CLATTER, THUD_LOW, TIDE, FIP, SET_DOWN, RUMBLE_ROLL, PING, ...) while no sweetener has more than
9 events within +-15 s (~20/min). `full` = all 64 placements (29/min). Every cue, sweetener or not, is in the library.

### Result (default mix, `<scratch>/ep01/sound/out/ep01_mix.wav`)
Mix -15.97 LUFS integrated, LRA 1.3 LU, -1.20 dBTP (limiter max 1.9 dB, on the voice's own plosive peaks, as in the
test); voice -16.1 LUFS, short-term p5/p50/p95 -17.0/-16.2/-15.6; SFX -25.0, beds -33.8 LUFS. Voice over SFX+bed in
the 300-4000 Hz band inside words: median 23.8 dB, p5 10.4 dB (4.6 % of word frames under 10 dB, all 10-50 ms where a
hit lands on its own naming word, by design). Last voice 112.92 s, end 113.30 s.
**5-second test**: 0-3.40 s of the episode mix nulls against `test5_mix.wav` at -86 dB (max sample difference 7e-5,
the 24-bit floor); W1/M1/P1/A1 gains -7.48/-11.63/-10.28/-2.09 dB, identical. From 3.40 s the episode continues
("First, your grandma gets shorter" at 3.59, the cut to Grandma's room at 3.567 with its room bed); M1's sparkle tail
now fades out by 3.95 s instead of running to 5.0; the test-only W2 swell and crickets lift are not used.

QA stills (1080x1920): `<scratch>/ep01/assets/sound/qa_cues_01..10.jpg` (every cue of the full profile in its mix
context), `qa_refs.jpg` (SUBBOOM vs TF 40.85 / CG 72.24, FWOOM vs TF 111.0, tines vs AW "Tink, tink", GRIND vs AW
door creak), `qa_test5_vs_episode.jpg`, `qa_overview.jpg` (loudness timeline with cues, cuts and planned pauses).

### Notes and requests to other owners (sound)
- Picture owners: please match (or send back) the multi-hit times in `cue_times.json`. In particular **TINKS (part 2,
  s40)**: the board asks for 12 lanterns 0.15-0.3 s apart *and* the nearest on "lit" at 45.22 s (0.59 s after "every"),
  which cannot both hold. The sound plays 4 near tinks (44.63, 44.82, 45.01, 45.22) over a faint dense twinkle of 8 far
  lanterns. When the s40 builder exists, write `fx_ep01.lanternCascade(...).cues[].t` (+ the shot start, episode
  seconds) into `cue_times_override.json` as `{"TINKS": {"times": [...]}}` and re-run `mix.py`.
- HOPS (s14) times are estimated (5 hops before the bonk), and HOPS is optional (`full` only).
- GULP is built around the picture's swallow: lips 0-0.12 s, closure "bloop" + sub at 0.12-0.35 s, crumb burp at
  0.38-0.5 s (59.245-59.365, in the gap before "Gone").
- GRIND follows the s59 turn exactly (0.8 s inOutSine from 66.55, 20 Hz stepped jerks = 3 frames); its loudest point is
  mid-turn, 66.95 s.
- Every source file the library uses was extracted from the owner's two Epidemic zips into
  `<scratch>/ep01/sound/sfx/` (42 files, incl. 6 from the nested "UI Buttons" zip); read as data only.

## EFFECTS (EP01 full episode) - `kit/fx_ep01.js`

```js
import * as X from '../../kit/fx_ep01.js';
build(ctx)  { /* set the camera first (some effects read it at t = 0) */ const L = X.lanternLight(ctx, g, { t0: evT(ctx, 'lit') }); ctx.add(L.group); }
update(ctx, t) { /* pose gnome / hero / field first */ L.update(t); }
```
Conventions: world **metres**; sizes the ASSETS spec gives in studs are taken in **studs** (`radius: 5` = 5 studs); `px` =
output pixels of the 1080x1920 frame (screen-constant sprites). Every effect is a pure function of shot time `t` (no state
between frames); anything that needs this frame's camera (streak directions, catchlight glints) is placed in
`onBeforeRender`, because the engine applies the camera after `update()`. Each call returns `{ group, update(t), cues }`
(or an Object3D with `.update`); `cues` = `[{ t, kind }]` in shot seconds for the sound mix. Ground light uses a
**light-boost blend** (`X.boostBlend(mat)`: dst x (1 + c)) so warm light lights the lawn texture instead of an additive wash
that the cool night grade turns grey. QA: `node tools/render.js engine/kit/_fx_ep01_qa.js <dir> times=... workers=2
quality=final` (20 shots, shot i = [2i, 2i+2), names in the file); stills + reference comparisons (`cmp_0*.jpg`):
`<scratch>/rbx/ep01/assets/effects/`.

### Lantern light-up, ring, street cascade (`fx_lantern_ring`, `fx_lantern_cascade`; s38-s43, s45-s46, s50, s56-s58, s69-s81)
- `X.lanternLight(ctx, gnome, { t0, level: 1, cd: 1.6, ring: 5, ringOpts, burst: true, haloPx: 64, glassK: 2.4,
  lightOffset: null, levelFn: null })` -> `{ group, update, ring, light, level(t), cues }`. Bible 3.2 light-up via
  `K.lanternLightUp` (3 frames + 6-frame overshoot, halo 0.2 s) + flicker; the glass is re-driven at x2.4 emissive (the kit's
  x6 clips to lavender-white under the night grade), a screen halo (15-30 px core), an unshadowed point light at the glass
  (the TF under-light on the face), a small gold burst, and the ring. Uses the gnome's own `lanternLight` if it has one.
  Held lanterns (s38): `cd: 0.9, lightOffset: [m]` moves the light 0.3-0.4 m out of the beard (else it blows the face out).
  Pair with `X.inShotGrade(ctx, 'current', 'magic', t0, 8, 0.6)` for s38's "grade warms to 60 % magic".
- `X.lanternRing(ctx, { center | follow, radius: 5, rim: 0.25, falloff: 0.6, inner: '#ff8a2a', boost: 1.7, rimColor:
  '#ffb04a', rimBoost: 3.0, rimA: 0.55, innerA: 0.06, glints: 0 })` -> Mesh with `.group`, `update(t)`, `setLevel(k)`,
  `radius` (m), `center`, `centerXZ()`, `edgeOf(pos)` -> `[x, z]`, `edgeVec(pos)`, `contains(pos)`. `follow` = Object3D or
  `(t) => Object3D` (slides with the hero, s46). Moles stop at it: `field.stopAt(i, ring.centerXZ(), ring.radius)`
  (checked in QA shot 1: they halt and recoil on the rim). Street gnomes use `radius: 2`.
- `X.lanternCascade(ctx, gnomes, { t0, order: 'toward camera', gap: [0.15, 0.3], skip: ['A4'], preLit: ['A3'], ring: 2,
  lights: 4, cd: 1.6 })` -> `{ group, items, cues, update }`; `gnomes` = `S.ep01Street(...).ep01.gnomes` (plastic ones are
  skipped) or Object3Ds. Seeded gaps; only the `lights` nearest the camera get a real point light; one `tink` cue each.

### FWOOM (`fx_fwoom` EXTEND; s77-s81)
- `X.fwoom(ctx, { gnome, t0, t2 (second pulse, "flared"), field, moles: 'all', speed: 8, stagger: 0.04, sinkDur: 0.5,
  rig, grade: 'magic', frames: 8, hemi, peak: 6, cd: [2.2, 11, 3], ring: 5, wave: {} })` -> `{ group, update, cues, wave,
  lantern, level(t) }`: lantern flare (glass, halos, ring), burst ring + streaks + gold/pink motes, grade to magic over 8
  frames (+ rig.hemi to P3), a `lightWave` from the bed, and `field.sink(i, ...)` for every mole as the front reaches it
  (eyes wink out 0.12 s later inside creatures.js); one `blip` cue per mole.
- `X.fwoomLevel(t, t0, { base, peak, end, t2, peak2, shape: 'flash' | 'sine' })` the lantern curve alone.
- `X.lightWave(ctx, { center, t0, speed: 8, height: 1.0, width: 1.4, maxR: 40, core, trail, sparkles: 60, sector:
  'camera', light: 2.5 })` -> `{ group, update, radiusAt(t), speed }`: additive ring wall (gold front, pink trail, fades at
  grazing angles), a light-boost band + crisp line on the grass, sparkles kicked up at the front, a 2.5 cd point light
  riding the front toward the camera (lights the blades it passes). s78: put the camera beside the wave's path.
- `X.winkOut(ctx, [{ L, R, t }], { px: 46 })` the blip glint on each eye as a pair goes dark (s80); `X.fieldEyes(field, i)`
  -> `[L, R]` world positions; schedule the eyes themselves with `field.eyes(i, tOn, tOff)` at the same t.
- `X.inShotGrade(ctx, from = 'current' | preset, to, t0, frames = 8, amount = 1, { rig, hemi })` -> `update(t)` (grade,
  exposure, bloom, glow, hemi); `X.gradeBlend(A, B)`; promoted, look-identical `X.starGlint`, `X.streaks`, `X.poofCloud`.

### Soil, GULP, mounds, sticker (`fx_soil`, `fx_sticker`; s34, s35, s37, s51)
- `X.soilBurst(ctx, { pos, t0, count: 24, spread: 0.9, apex: 0.6, dur: 0.4, size: [0.022, 0.05], y0, puffs: 3, rest }
  | { bursts: [...] })`: instanced crumbs on parabolas (tumble, rest, shrink away) + soft dust puffs.
- `X.moundCrumbs(ctx, field, { moles: 'all', rate: 16, life: 0.5, pops: true })`: crumbs flicked off travelling bulge
  fronts + a pop when a mound rises (reads the field's travel / rise plans; call after `field.update(t)`).
  `X.moleAt(field, i, t)` / `X.moleWorld(field, i, t)` = a mole's planned position.
- `X.gulp(ctx, { field, index, target, t0, depth: 2.2, radius: 0.85, swallow: true, wobble: 8, sticker: {} | null })`:
  calls `field.swallow` (pass `swallow: false` if the shot already did), dark throat inside the lips, jerky wobble while the
  gnome is pulled down, crumbs as the lips rise, a dirt puff + crumb burp on the seal (t0 + 0.24) and a second small burp;
  the `$4.99` sticker flutters down at t0 + 0.47 and lands toward the camera, outside the seal. Without `field` it builds and
  updates its own small mole field. Ground = the target's base height (the flowerbed soil is raised).
- `X.flutter(ctx, { text: '$4.99', from, to, t0, dur: 0.4, size: 0.5, swing: 35 })`; `X.stickerTex(ctx, text)`.

### Gate, gold, tear, beam, curtains, fog, window (`fx_property_line`, `fx_gold_outline`, `fx_tear`, `fx_beam`, `fx_curtains`, `fx_glass_fog`, `fx_window_dark`)
- `X.propertyLine(ctx, { a, b, height: 2.6, opacity: 0.06 })` -> `{ group, update, bonk(t0, at), part(t0, at) }`: lavender-
  gold streak curtain drifting up + gold ground line; `bonk` = 3 ripple rings (0.45 s, 0 -> 2 studs) + flash + 12-sparkle
  burst (add `ctx.camera.shake({ t0, dur: 0.3, px: 4 })`); `part` = the curtain opens in a gold flash, 10 gold sparkles and
  a gold pulse running along the line (s32's ripple).
- `X.goldOutline(ctx, [armL, armR, gnome], { t0, color: '#ffb43a', width: 0.02, peak: 0.9, hold: 0.5, t1, sparkles: 8 })`:
  inverted hull on smoothed normals (no cracks on R6 boxes), crisp rim + soft halo, 0 -> 0.9 -> 0.5, gold sparkles.
- `X.dewTear(ctx, gnome, { eye: 'L', t0, dur: 0.6, swell: 0.15 })`: the path is ray-cast onto the face once (head-local, so
  it follows head turns); glossy drop + sheen + catchlight, wet trail into the beard.
- `X.flashlightBeam(ctx, { torch | origin + dir, length: 9, angle: 14, t0, t1, cd: 4, opacity: 0.18 })` -> `{ group,
  update, on(t0) }`: soft additive cone, elongated ground spot, unshadowed SpotLight, motes. With `C.makeFlashlight` use
  `{ light: false }` on the torch (or `light: false` here) so the lawn is not lit twice.
- `X.curtainCascade(ctx, set, { t0, gap: 0.12, n: 6, color: '#7a2a3a', frames: 4, inView: true })`: lit front windows in
  the camera view, nearest first; backlit wine panels slide shut in 4 frames between glass and muntins, window glow x0.6.
- `X.glassFog(ctx, pane, { t0, center, r1: 0.9, grow: 0.35, opacity: 0.7, eyes: [L, R] })` (pane = `H.ep01.theo.glass`).
- `X.windowState(win, level)` / `X.windowDark(ctx, H, { t0, t1 })` (Theo's window via `ep01.theo.setLevel`, 1 frame).

### Accents, dawn, photos (s18, s75, s86, s82-s85, s90, s93)
- `X.blinkTik(ctx, gnome, { t0, frames: 2, slow: false, px: 58 })` -> `{ group, update, tReopen, cues }`: the [TIK] glint on
  both catchlights as the lids reopen (second eye 1 frame later); same t0 as `K.gnomeBlink(t, [t0])`.
- `X.dawnSweep(ctx, { from, to, t0, dur: 1.4, width: 5, intensity: 1.6, shade: 0.3, sun: rig.key, ramp: [0.45, 1],
  hemi: rig.hemi, glints: 10 })` -> `{ group, update, k(t) }`: warm band over the ground (ground ahead stays in blue shade),
  the sun / hemi ramp up with it (lights blades, props, people), dew glints wake as it passes.
- `X.photoLook(ctx, canvas | texture, { lift: '#2a2420', warm: 8, sat: 0.85, vignette: 0.28, grain: 1 })` -> `{ canvas,
  texture }` (photo textures only, never the frame); `X.polaroid(ctx, { photo: S.photoTexture(ctx, year), date:
  X.photoDate(year), curl: 0.12, w: 3.5, h: 4.2 })` -> Group (front +Z, `userData.size`): paper frame with grain, the look,
  blue ballpoint date, curl (bow + one lifted corner), dark back; `X.polaroidDrop(ctx, cards, { at, t0s, dur: 0.28 })`
  (s90 pile with contact shadows); `X.polaroidSlide(card, { t0, dur: 0.3, from, spin })` (s93 insert).

### Decisions / deviations (effects)
- Determinism: stills are bit-identical with 1 or 2 workers in any order (checked by md5 on FWOOM, GULP, light wave, bonk).
  No other kit file was edited; the approved shots s01-s05 / s09 do not import fx_ep01.js.
- **Light values**: FWOOM uses the bible's curve shape at 2.2 -> 11 -> 3 cd (the bible's 8 -> 50 -> 10 put a 1 m close-up at
  p50 217; QA now p50 106 after the flash, 72 later); the visual level falls fast (0.32 s exponential) instead of 1.5 s
  inOutSine, which kept the frame white for 0.6 s. Held lantern 0.9 cd, offset from the beard.
- **Ring numbers**: the ASSETS spec's additive 0.22 / 0.55 washed the lawn grey under the night grade; the ring is a light
  boost (x2.7 warm interior, x4 rim) + a thin additive rim. Colours are more saturated than the spec for the same reason.
- **Dawn sweep** is a ground band + sun ramp, not a moving shadow edge: the street set's lawn takes no sun shadows (a test
  cube casts none on it, even with `receiveShadow` forced). Ground bands (ring, wave band, dawn) sit under the grass-blade
  geometry, so they read from above and at medium height; at ground level the wave's wall and riding light carry it.
- `photoLook` / `polaroid` take the sets owner's `S.photoTexture` canvases; the print look is applied on a copy.

### Requests to other owners (effects)
- Sets: if a shot needs real sun shadows on the lawn (dawn sweep as a shadow edge), make the street lawn `receiveShadow`.
- Creatures: field heads with `heads: 'eyes'` read small at 6-10 studs; s80 may want `scale: 0.9-1.0` eye pairs closer to
  the lens. `winkOut` glints are placed from `fieldEyes(field, i)` after `field.update(t)`.
- Part builders: build effects after `ctx.camera.set(...)` (cascade order, curtains in view, glass-fog side, wave sparkle
  sector and gulp sticker landing read the camera at t = 0).
