
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
