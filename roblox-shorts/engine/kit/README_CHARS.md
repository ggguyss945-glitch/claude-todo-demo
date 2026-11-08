# Character kit (R6 humans, decal faces, 2D clothing, accessories, the gnomes)

Implements VISUAL_BIBLE §2 (construction) and §3 (animation) for the whole of EP01. Everything is procedural, seeded and
deterministic (no `Math.random`), and every builder is cheap after its first call in a worker (geometry, canvases and
materials are cached and marked persistent, so shot cleanup never disposes them).

```
engine/kit/
  chars.js        entry point of the character kit (re-exports the modules below; no dependency on the sets kit)
  index.js        shared entry point: sets kit (kitlib/props/suburb/sky/lighting/fx) + character kit
  util.js         STUD, caches, canvas/texture helpers, clumpGeo, shadowBlob, ownMat (per-instance materials)
  faces.js        decal face system (19 expressions + overlays)
  clothing.js     2D painted shirts / pants on box atlases, OUTFITS, SKIN, HAIR palettes
  accessories.js  hair, glasses, hats, 3D walrus moustache, hood
  avatar.js       R6 builder, rig, pose library, pose-to-pose, walk / run / wave cycles, setFace
  gnome.js        the hero creature (Grandpa gnome), plastic variant, family gnomes, lantern, blink / turn / hop API
  cast.js         EP01 cast presets (grandpa, grandma, hero, theo, ...)
  _chars_qa.js    QA episode: character sheets rendered with tools/render.js stills mode
```

```js
import * as K from '../kit/chars.js';          // or: import * as kit from '../kit/index.js' (sets + characters)
const gp = K.makeCharacter('grandpa', { face: 'content' });   // metres (root scaled 0.32), feet at y = 0, faces +z
const gm = K.makeCharacter('grandma');
const gnome = K.makeGnome('grandpa', { lantern: 0, lanternLight: true });
gp.position.set(-0.5, 0, 0); ctx.add(gp, gm, gnome);
// update(ctx, t):
K.setPose(gp, K.poseAt(t, [[0, 'stand'], [0.4, 'point']], 0.15, 'outBack'));
K.setFace(gp, K.faceAt(t, [[0, 'neutral'], [0.4, 'shock']]));          // instant swap on the beat word
K.setGnomeLids(gnome, K.gnomeBlink(t, [1.25]));                        // the 2-frame blink (plot point)
```

## Units and conventions

- The kit builds in **studs**; every builder returns a root `Group` scaled by `STUD = 0.32` (metres) unless `units: 'stud'`.
  Place roots in metres like any engine object. Feet at y = 0. Characters face **+z**; a character's **left is +x**
  (so `armL` / `hipL` are on +x, and the right hand that holds things is on -x).
- All pose angles are **degrees**. Every animation helper is a pure function of shot time `t` (engine determinism rule).
- Do not store objects in `userData` (the engine clones with `clone(true)`); the kit looks parts up by name.
- `ctx.instance(key, () => K.makeCharacter(...))` is fine: face swaps and lantern levels clone the one material they
  change per instance (`ownMat`), so clones never affect each other.

## R6 avatar (avatar.js, bible §2.1-2.2)

`makeAvatar({ skin, outfit: { shirt, pants }, face, faceOverlays, accessories: [...], scale, units, shadow, shadowOpacity, name })`

- Six rigid parts: torso 2x2x1, arms and legs 1x2x1, `RoundedBoxGeometry(…, 3, 0.06)`; drum head = lathe of the bible
  profile (fillet 0.25, 48 segments). Total 5.2 studs, eye line about 4.65. `scale` is uniform (bible: Theo 0.85, the
  5-year-old 0.75; everyone else 1). SmoothPlastic skin (roughness 0.52), clothing roughness 0.64-0.72.
- A soft contact-shadow blob is added under the feet (`shadow: false` to omit).
- Rig (names, for `getObjectByName` or `K.rig(root)`): `body` (yaw, roll, lift) → `hips` (pivot y 2, forward lean) →
  `torso`, `neck` (pivot y 4) → `head` (y 4.6: `headMesh`, `face`, accessories), `shoulderL/R` (pivots (±1.5, 3.5): arm
  meshes `armL/R`); `hipL/R` (pivots (±0.5, 2)). Shoulder gaps during swings are part of the look.
- `handSocket(root, 'R' | 'L')` returns a group at the hand end, to parent props (props never teleport in view: hand-offs
  under a cut or a VFX).

### Poses

`setPose(root, pose)` with pose keys (degrees, missing = 0):
`armLx armRx` (+ raise forward), `armLz armRz` (+ raise outward), `armLy armRy` (twist), `legLx legRx` (+ swing
forward), `legLz legRz`, `neckX` (+ look up), `neckY` (+ turn to its left), `neckZ` (tilt), `bodyX` (+ lean forward at
the hips), `bodyY` (yaw), `bodyZ` (roll), `lift` (studs, whole body up/down), `breath` (torso scale-y offset).

`POSES` (joint-angle sets): `stand idle lookUp lookDown lookLeft lookRight point pointUp reach hold holdLantern carry hug
kneel kneelPlace sit sitFloor wave shocked handsToHead sad shrug cheer sleepwalk jump run panicRun walk presentTall
handOnHeart` (see `POSE_NAMES`). `sit` expects a seat top at y 1.5 studs; `kneel` / `sitFloor` drop the body with `lift`.

- `poseAt(t, [[t0, 'stand'], [t1, poseObj], ...], blend = 0.15, ease = 'outQuad')`: bible pose-to-pose (snap of
  6-16 frames, then hold). `blend = 0` gives a 1-frame pop (only on a cut, under a VFX burst or in a whip).
- `mixPose(a, b, u)`, `addPose(...poses)` (sums angles; for offsets such as a breath).
- Cycles (absolute joint values; merge with `{ ...pose, ...cycle }`): `walkCycle(t, { period: 0.73, legs: 38, arms: 40,
  holdArms })` (travel `WALK_SPEED` = 7 studs/s), `runCycle(t, { period: 0.5, panic })` (`RUN_SPEED` 13),
  `waveCycle(t, { amp: 15, freq: 2, arm: 'R' })`, `handsToHeadAt(t, t0, fromPose)` (8-frame snap + rock),
  `breath(t)` (optional idle, 0.25 Hz), `turnAt(t, t0, t1, fromDeg, toDeg)` (inOutSine; bible: 180° in 14 frames).

## Decal faces (faces.js, bible §2.5)

- Transparent canvas drawn in the bible's 512 frame (x 256 centre, y 0 head top) at **1024 px** (2x) on a band that
  copies the front 140° of the drum (radius x1.004, `polygonOffset` -2, `depthWrite:false`). Black #141414 round-cap lines,
  red #d01818, teeth #f1ecff, tongue #e2405a. Identical line weights across the set.
- `FACES`: `neutral wonder shock grin openSmile content angry sad heartfelt sleeping sideGlance horrified sob wetEyes
  smirk` (bible #1-15) + `talk blank worriedSmile determined`. Aliases (`ALIASES`): smile, o, surprise, teeth, laugh,
  happy, worried, tender, asleep, suspicious, terror, cry, tears, speaking, …
- `setFace(root, name, overlays?)` swaps instantly (1 frame) by switching the cached texture. `faceAt(t, [[t, name], …])`
  gives the face for a timeline. No lip-sync: for in-scene speech flap `talk` / `neutral` every 0.25-0.3 s. No human
  blinks.
- Overlays (`faceOverlays` on the avatar or the 3rd argument): `freckles`, `blush` (colour), `wrinkles` (crow's feet +
  smile folds), `stubble`, `moustache` (decal walrus, colour), `brows` (soft bushy brows in a colour, drawn only when the
  expression has none). `faceTexture(name, overlays)` / `drawFace(g2d, name, overlays)` for other uses.

## Clothing (clothing.js, bible §2.3)

- 2D painted textures, never 3D layers: one canvas atlas per box part at `PPU = 176` px/stud, laid out
  `[-x | front | +x | back]` over `[top | bottom]` so stripes / plaid wrap continuously; patterns align in world y across
  torso and arms. Baked shading: collar shadow, armpit darkening, soft blurred fold strokes, darker hem, lighter cuff;
  long sleeves end in a skin "hand" band (0.36 stud), short sleeves on a skin arm. Knit styles add a weak bump map.
- Shirt spec: `{ style: 'tee'|'shirt'|'hoodie'|'pyjama'|'cardigan'|'sweater'|'blazer', color, pattern, trim, buttons,
  inner: { color, pattern, buttons, collar }, open, vDepth, necklace, pocket, piping, strings, suspenders, sleeves:
  'long'|'short'|'three', hand, knit }`. Patterns: `{ type: 'stripes'|'plaid'|'tartan'|'check'|'stars'|'dots'|'floral',
  color, color2, period, density, size, alpha }`.
- Pants spec: `{ style: 'trousers'|'jeans'|'pyjama'|'skirt'|'shorts', color, pattern, belt, piping, skirtLen, stockings,
  shoes: { style: 'shoes'|'sneakers'|'slippers'|'socks'|'barefoot', color, color2, pattern, h } }`.
- `OUTFITS`: `heroHoodie theoPyjamas grandpaCardigan grandpaFlashback grandmaCardigan momSweater dadPlaid plainKid`.
- `SKIN` (bible albedos): salmon #e8a07a, orange #f49134, coral #e96e57, light #ebc284, pale #e8e8e8, peach, tan, brown,
  deep, elder. `HAIR`: brown, darkBrown, blond, ginger, black, grey, silver, white.

## Accessories (accessories.js, bible §2.4)

`accessories: [{ type, ... }]` on `makeAvatar`, or `addAccessory(headGroup, spec)`. Chunky, smooth, rigid UGC meshes in
head-local studs.

| type | styles / options |
|---|---|
| `hair` | `style`: `messy` (EP01 hero: big asymmetric spikes + side fringe), `short`, `grandpa` (bald crown, puffy side tufts), `bun` (grandma: combed cap, side volume, top-back bun), `bob`; `color` (strand-streak map). Caps follow the drum head with a hairline high at the front and low at the nape |
| `glasses` | `style`: `round` (thin metal) / `thick` (plastic); `color` |
| `hat` | `style`: `fishing` (olive bucket hat with two spoons, a feather fly and a hook), `flatCap`, `beanie` (`band` = cuff / pompom); `color` |
| `moustache` | 3D walrus moustache (CG's Hank); `color` |
| `hood` | bunched hood behind the neck (hoodies); `color` |

## Cast (cast.js)

`CAST` / `makeCharacter(name, extra)`:
- `grandpa` (test cast): elder skin, white bald-crown hair with side tufts, 3D white walrus moustache, soft grey brows,
  round gold glasses, navy cardigan over a blue check shirt, grey trousers, tartan slippers.
- `grandma` (test cast): grey bun, round rose-gold glasses, rose cardigan open over a floral blouse with pearls, long plum
  skirt, stockings, slippers, blush and soft wrinkles.
- `hero` / `heroBarefoot` (11: mustard hoodie + hood, messy brown hair, freckles), `theo` (x0.85, star pyjamas, blond),
  `grandpaFlashback` (script: olive fishing hat with lures, brown cardigan), `heroOld` (71: mustard cardigan, fishing hat,
  grey moustache), `mom`, `dad`.

## The gnome (gnome.js, bible §2.6-2.7, §3.2)

`makeGnome(presetOrOptions, extra)` → root (metres), 2.0 studs tall with the hat (0.38x an R6, `height` to change).

- Sculpted, not boxes: displaced lathe coat with a belly and hem folds, rolled hem, belt with a gold buckle, buttons,
  egg boots, tapered sleeves with cuffs, mitten hands; a sphere head with ears and ruddy cheeks; a **round nose**; a **thick
  tapered hat with a soft bend** (lathe bent sideways and back, folds on the inside of the bend, thick rolled brim); a
  **big flowing beard**: one sculpted mass with five big flowing lock flutes and fine strands + side locks and three wavy
  points; a two-lobe walrus moustache; bushy brows; white back hair under the brim.
- Glazed ceramic per the bible: `MeshPhysicalMaterial` roughness 0.28, clearcoat 1, clearcoatRoughness 0.12, with a
  painted glaze map (mottling, speckles, **chips of white bisque** with a dark rim, matte + no clearcoat on chips),
  baked vertex ambient occlusion and **dirt at the base**. `age` (0-1) fades the paint and adds moss (epilogue).
- **Huge glossy eyes** (32% of head width each): sclera with a pinkish rim and faint veins, blue iris with fibres, black
  pupil, painted catchlights, clearcoat 1. Upper lid shells with a lash line and lower lids. The uncanny details: the
  bulging veined stare, **tiny fixed teeth** under the moustache and a **hairline crack** on the left temple. The mouth
  never animates.
- Lantern in the right hand at cheek height (faces are lit from below), brass + emissive glass + flame + halo sprites +
  a warm additive ground pool; optional point light.

Options (`GNOME_DEFAULTS`): `material` ('ceramic' | 'plastic'), `finish` (plastic: 'matte' default | 'glossy'), `lod`
('hero' | 'mid' | 'low'), `height`, `hat: { style: 'pointed'|'fishing', color, height, bendSide, bendBack, dots }`, `coat`,
`belt`, `buckle`, `boots`, `buttons`, `skin`, `nose`, `cheek`, `beard` ('full'|'short'|'walrus'|'none'), `beardColor`,
`brows`, `eyes: { iris, size, style: 'glossy'|'dead', open }`, `mouth` ('teeth'|'smile'|'none'), `crack`, `glasses`
(colour), `apron` (colour), `hair` ('curls'), `hairColor`, `arms` ('lanternSide'|'lanternFront'), `lantern` (initial
level, `false` = none), `lanternLight` (`true` = 0.7 cd at level 1, or a number of cd), `pool`, `sticker` (text),
`base` (moulded plinth), `wear`, `age`, `seed`, `shadow`, `units`.

Presets (`GNOME_PRESETS`): `grandpa` (hero: red pointed hat, white full beard + walrus moustache, coat in Grandpa's navy
cardigan blue), `grandpaFishing` (script build sheet: olive fishing hat with lures, red coat, moustache only), `narrator`
(frame-1 gnome: fishing hat, mustard coat, grey moustache), `grandma` (lavender hat, rose coat, apron, round glasses,
grey curls, no beard), `plastic`.
- `makePlasticGnome(extra)`: next door's cheap gnome: low-poly, smooth beard blob, oversaturated flat colours, matte,
  **dead black dot eyes**, green moulded base with a "$4.99" price sticker, black plastic lantern.
- `makeFamilyGnome(i, extra)`: 8 street variants (`FAMILY_GNOMES`: hat colours and dots, coats, beards, glasses,
  aprons, a fishing hat), `lod: 'mid'`.

Animation (pure functions of t; bible §3.2 "a statue that moves only on beats", creatures never frozen):

| function | |
|---|---|
| `setGnomeLids(g, closed01)` | eyelids 0 open … 1 closed |
| `gnomeBlink(t, [t0, …], { frames: 2, slow })` | 1 for exactly `frames` frames from each t0 (the 2-frame blink); `{ frames: 4, slow: true }` = the slow blink with half-closed frames either side |
| `setGnomeGaze(g, yawDeg, pitchDeg)` | eyeballs (painted catchlights move with them: it is a statue) |
| `setGnomeHead(g, yaw, pitch, roll)` + `gnomeHeadTurn(t, t0, dur, from, to, { jitter: 2.5, every: 3 })` | the stony grind: inOutSine with a stepped 2-3° jitter every 3 frames |
| `gnomeHop(t, t0, { height: 0.1, freq: 2.5, roll: 8 })` | gate toddle: returns `{ y (studs), roll (deg) }` for the root |
| `gnomeIdle(g, t)` | micro sway so a held gnome is never frozen |
| `setLantern(g, level, { halo, flicker, light })` | 0 unlit, 1 lit (glass emissive x6, halo, pool, light), >1 boosted (FWOOM 4-6) |
| `lanternLightUp(t, t0)` | `{ level, halo }`: 0 → 1 in 3 frames, 6-frame overshoot to 1.5, halo fades in over 0.2 s |
| `lanternFlicker(t)` | ±6% at 7 Hz; multiply into the level |
| `buildLantern({ plastic })` | a standalone lantern (origin at the ring, hangs down ~0.32 stud) |

Part names: `gnomeBody`, `gnomeHead` (neck pivot), `eyeL/R`, `ballL/R`, `lidL/R`, `gnomeHat`, `beard`, `moustache`,
`lantern`, `lanternGlass`, `lanternHalo`, `lanternLight`, `lanternPool`, `shadowBlob`.

## Performance

`quality=fast`, 1 worker: about 640 ms/frame for a night lawn with Grandpa, Grandma, the hero gnome and one lantern point
light (engine demo: 571). Triangles: hero gnome 77k (59 meshes), family gnome (`lod: 'mid'`) 34k, plastic 14k, Grandpa
19k, Grandma 17k. Give point lights only to the 1-3 lanterns nearest camera (the halo, core sprite and ground pool carry
the rest). First build of a gnome variant in a worker takes ~0.25 s, then each `makeGnome` is a ~1 ms clone; an avatar
build is ~30 ms (its textures are cached after the first).

## QA sheets

```bash
cd roblox-shorts; export NODE_PATH=/opt/node-tools/node_modules
node tools/render.js engine/kit/_chars_qa.js <outdir> times=0.5,2.5,4.5,6.5,8.5,10.5,12.5,14.5,16.5,18.5,20.5,22.5,24.5,26.5 workers=3 quality=final sheet=1
```

Shot i covers [2i, 2i+2): 0 gnome neutral light, 1 gnome ECU, 2 turnaround (Grandpa, Grandma, hero: front / 3-4 / side),
3 gnome turnaround + variants, 4 faces, 5 elder + hero faces, 6 poses, 7 gnome night close-up (P1, lit lantern), 8 gnome
dusk close-up (unlit), 9 blink (lids closed), 10 lineup (scale vs R6), 11 cast in context (P1 night lawn), 12 animation
API test (t 0.25 / 0.5 blink frame / 1.5), 13 extra cast + hats.

## Decisions where the task, the bible and the script differ

- **Gnome look**: the task asks for a thick tapered red hat and a big flowing white beard (the bible's EP01 table and the
  script describe an olive fishing hat and a walrus moustache). The `grandpa` preset follows the task; the script look is
  `grandpaFishing` / `narrator`. The hero's coat is navy blue to match human Grandpa's cardigan (a red coat under a red hat
  reads as Santa); the script's red coat is one option away (`coat`).
- **Plastic gnome finish**: the task says matte, the bible says glossy (roughness 0.15): `finish: 'matte'` by default,
  `'glossy'` gives the bible version.
- **Blink**: the bible describes a 2-frame eyelid texture swap on painted domes; the kit uses sculpted lid shells snapped
  closed for exactly 2 frames (4 for the slow blink), which reads the same and works from every angle.
- **Moustache on human Grandpa**: a chunky 3D walrus moustache (CG's Hank), so it matches the gnome; the decal version is
  `faceOverlays.moustache`.
- **Lantern light**: 0.7 cd per lantern at level 1 (the bible's 3-4 cd is measured for street-lamp distances; at 0.2 m from
  the gnome's face it blows out the hat brim). Raise with `lanternLight: <cd>` for wider shots or with the level for FWOOM.
