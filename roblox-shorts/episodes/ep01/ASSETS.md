# EP01 asset list (full episode)

Every set, set dressing, character, creature, prop, effect and sound cue the 97 shots of `board.md` use, marked **EXISTS** (with the kit call), **EXTEND** (exists, needs the option described) or **NEW** (with the spec), grouped by owner. "Used in" is computed from the shot table (`tools/shots_ep01.py`). Kit names: `K` = `engine/kit/chars.js`, `sets` = `engine/kit/sets.js`, `props` = `sets.props`, `C` = NEW `engine/kit/creatures.js`, `S` = NEW `engine/kit/sets_ep01.js`, `I` = NEW `engine/kit/interiors.js`, `X` = NEW `engine/kit/fx_ep01.js`. Units: studs (x 0.32 = metres). All new code: procedural, seeded, pure functions of t (engine determinism rules), Three.js 0.170.

| Owner | New kit file(s) | EXISTS | EXTEND | NEW |
|---|---|---|---|---|
| CREATURES + CAST | `creatures.js` (moles, mound field, dog, whale) + additions to `cast.js`, `clothing.js`, `accessories.js`, `faces.js` | 12 | 2 | 17 |
| SETS | `sets_ep01.js`, `interiors.js` | 7 | 3 | 10 |
| EFFECTS | `fx_ep01.js` | 9 | 1 | 12 |
| SOUND | (mix stage) | 58 cues, 22 primary | | |

## CREATURES + CAST

| ID | Status | Item | Kit call or spec | Used in |
|---|---|---|---|---|
| `badge6` | **NEW** | Birthday badge "6" | A round pin badge 0.45 stud (yellow #f2c230, red rim, a black '6' in the bible sign font) pinned on Theo's pyjama chest; glints on "six". | s44 |
| `cousin_kid` | **NEW** | A small girl in the 1990s (sepia, asleep) | cast.js `cousinKid`: scale 0.75, pigtails (NEW hair style `pigtails`: two side clumps with ribbons), floral nightie, face `sleeping`. | s68 |
| `dad_kid` | **NEW** | Dad as a small boy (1960s, B&W, asleep) | cast.js `dadKid`: scale 0.75, striped pyjamas, short dark hair, NEW `ears` accessory (two sticking-out half-discs 0.35 stud on the drum sides: the plant for Dad's ears), face `sleeping`. | s67 |
| `dog` | **NEW** | Next door's dog (REX) | creatures.js `makeDog({ coat: '#c98a4a', patch: '#f2ece2', ears: '#6a3a1e' })`: a Roblox-built beagle: box body 2.2 x 1.1 x 1.0 studs (bevel 0.06), 4 box legs 0.35 x 0.7, a rounded drum head 0.8 with a decal face (dog nose, ^^ eyes, tongue), floppy box ears hinged at the top, a stub tail (wag +-25 deg at 6 Hz), red collar + lead attach point `leadSocket`. Poses: `lie`, `sit`, `chew` (head down 25 deg, jaw-less: the head bobs 2 Hz). Appears in s12 only (alive, chewing a plastic gnome's hat); s13 shows its empty kennel and lead running into the hole. Never shown going down the hole. | s12 |
| `face_wink` | **NEW** | Decal face `wink` | faces.js `wink`: left eye = the ^^ arc (closed), right eye = base oval, smile arc; same line weights as the set. | s23 |
| `flashlight` | **NEW** | Grandpa's flashlight | A chunky R6-scale torch 0.9 stud long (red rubber body #b8261e, chrome head, glass lens emissive #fff1d0 when on), parented to the hand socket; beam = `fx_beam`. | s19, s20, s23, s24, s61, s64, s66, s67 |
| `granddaughter` | **NEW** | The narrator's granddaughter (about 7) | cast.js `granddaughter`: SKIN.salmon + freckles (family), dark bob hair, lilac pyjamas with hearts, scale 0.85; faces `sideGlance` (suspicious frown), `content`. | s95, s96 |
| `grandkid` | **NEW** | A generic grandkid (world montage) | cast.js `grandkid`: SKIN.orange, `plainKid` outfit with a red cap (`hat` beanie style, no pompom) and sneakers; used kneeling (s08) and hopping stones (s11). | s08, s11 |
| `grandma_short` | **NEW** | Grandma, shorter (jump cut) | `K.makeCharacter('grandma', { scale: 0.8, outfit: { ...grandmaCardigan, shirt: { ...grandmaCardigan.shirt, hand: 'sleeve' } } })`: NEW `hand: 'sleeve'` option (sleeve colour runs to the end of the arm box, no skin band = sleeves swallowing the hands). Bible exception (story says so), like CG's 0.5 character. | s07 |
| `grandpa_young` | **NEW** | Grandpa in the 1960s (B&W only) | cast.js `grandpaYoung`: `grandpa` with dark-brown hair (`short` style), dark moustache, no glasses, no wrinkles, same navy cardigan. | s67 |
| `hero_kid5` | **NEW** | The hero aged 5 (sepia flashback, asleep) | cast.js `heroKid5`: hero skin + freckles, messy brown hair, rocket pyjamas (`pyjama` style, navy #2c3e7a with yellow rocket pattern via `stars` type), scale 0.75 (bible exception), face `sleeping`. | s64, s66 |
| `hero_old_short` | **NEW** | The narrator at 71, shorter (mirror of Grandma) | `K.makeCharacter('heroOld', { scale: 0.85, outfit: { ..., shirt: { ..., hand: 'sleeve' } } })` (same `hand: 'sleeve'` option as `grandma_short`). | s96 |
| `mole_field` | **NEW** | Mound / trench system on the lawn | creatures.js `moleField(ctx, { area, count, paths, seed })`: N moles travelling along Catmull paths at 2-4 studs/s as a bulge wave under the turf (a lawn patch with vertex displacement: Gaussian bump r 1.6 studs, height 0.6-0.9, plus a 0.25-stud raised trench ridge left behind that relaxes over 3 s). API, all pure functions of t: `rise(i, t0, dur)` (mound pushes up, soil crumbs pop), `travel(i, path, t0, speed)`, `stopAt(i, center, radius)` (stops at a light ring's edge: the bulge flattens against the rim and the snout recoils), `sink(i, t0, 0.5)` (deflate + turf settles), `swallow(i, target, t0)` (GULP: turf rises around the target like a closing mouth, target sinks 6 frames, turf seals), `pushBack(center, r0, r1, t0, 0.5)` (tide). Lawn displacement is one shared 128x128 plane over the hero lawn (or a 64x64 per neighbour lawn) so many mounds cost one mesh. | s34, s35, s36, s37, s39, s40, s41, s42, s43, s46, s51, s52, s54, s56 ... (17 shots) |
| `moles` | **NEW** | Giant star-nosed moles (second hero creature) | creatures.js `makeMole({ scale, seed })` -> Group (studs x STUD) with parts `mound`, `snout`, `tentacle0..21`, `eyeL/R`, `eyeHaloL/R`. Only the mound, the snout and the eyes ever show (no teeth, no mouth, no body). MOUND: a displaced turf dome 3.0 x 0.75 studs (scale 1) built from a 48x48 grid with the lawn's own grass texture + `grassBlades` tufts on top, a crumb ring of 40 instanced soil lumps (0.06-0.14 stud) at the rim, darker wet soil showing in 3-5 cracks. SNOUT: the star nose, 0.9 stud across at scale 1: a pink disc (MeshPhysical #e48aa0, roughness 0.5, sheen 0.6 #ffc0d0, faint emissive #401018) ringed by 22 tapered capsule tentacles (11 per side, 0.32-0.45 long, 0.07 thick at the root), each a bent CatmullRom tube so it can curl; wriggle +-10 deg at 2-3 Hz with per-tentacle phase; unfurl = tentacles open from a closed bud in 0.3 s (outBack); recoil = snap back 0.15 s with spring overshoot (`anim.springKeys`). EYES (the bike reflectors): two 0.22-stud domes 0.6 apart above the snout, a faceted retro-reflector texture (hexagonal cube-corner cells, 7 across, each cell a tiny radial gradient) under a clear glossy cap (clearcoat 1), emissive #ffb020 x3-5 that rises toward the camera (fake retro-reflection: emissive *= 0.4 + 0.6 * max(0, dot(N, toCamera))^4), a 15-25 px halo sprite each; `setMoleEyes(m, level)` 0 = dark (wink out in 2 frames) .. 1; `reflectorFlash(t, t0)` = a 4-point star glint sweep. Scales: 1 = lawn mound (3 studs); 1.8 = 'BIG ones' hero snout (cheat per shot, bible 2.6 #6). | s36, s37, s39, s51, s52, s53, s55, s58, s79, s80 |
| `theo_aged` | **NEW** | Theo at 7-66 (photo series only) | cast.js `theoAt(age)`: scale 0.85 (7-10) -> 1.0 (14+); hair blond short -> brown -> grey -> bald with white side tufts (`grandpa` hair style) at 60+; NEW beard accessory `beard` (chunky grey clump beard) from 40; clothes per decade (tee, hoodie, flannel, cardigan). | s90, s92, s93 |
| `theo_granddaughter` | **NEW** | Theo's granddaughter (newest photo only) | cast.js `theoGranddaughter`: SKIN.light, blond pigtails, blue whale-print pyjamas, scale 0.75, `wave` pose, face `openSmile`; seen through the window in the last photo. | s93 |
| `whale` | **NEW** | Theo's grey-blue stuffed whale | creatures.js `stuffedWhale()`: plush whale 1.4 studs long, lathe body #7f93ad with a pale belly #dfe6ee, two felt fins, a split tail, button eyes, fabric texture (`tex.fabric`, bump 0.02). Parented to Theo's hand socket or hugged (`hug` pose). | s25, s44, s45, s55, s69, s71, s72, s82, s83, s85, s86 |
| `hero_muddy` | **EXTEND** | Hero barefoot with muddy knees and feet (dawn) | `K.makeCharacter('heroBarefoot', { outfit: { pants: { ...heroHoodie.pants, mud: { knees: 0.8, feet: 0.6 } } } })`: NEW `mud` option in clothing.js pants painter (brown #4a2e1c blotches, alpha 0.7, on the knee band and the bare-foot ends). | s82, s84, s85 |
| `theo_socks` | **EXTEND** | Theo in socks (dawn) | `K.makeCharacter('theo', { outfit: { ...OUTFITS.theoPyjamas, pants: { ...OUTFITS.theoPyjamas.pants, shoes: { style: 'socks', color: '#f4f2ee', pattern: { type: 'stripes', color: '#5a8ad8' } } } } })`, the socks band 0.45 stud so it reads in a WS. | s82 |
| `dad_arms` | **EXISTS** | A grown-up's arms (Dad) lifting a gnome | `K.makeCharacter('dad')` framed so only the plaid sleeves and hands show (camera above the shoulders), + `gold_outline`. | s15 |
| `gnome_family` | **EXISTS** | Street / family gnomes (8 variants) | `K.makeFamilyGnome(i, { lod: 'mid'/'low', lantern: 0 })`; `POINTED` variant list in part1. Lanterns light in the 44.58 s cascade. | s01, s05, s09, s10, s15, s25, s35, s40, s42, s43, s70, s81, s88 |
| `gnome_grandma` | **EXISTS** | Grandma gnome (lavender hat, rose coat, apron, round glasses) | `K.makeGnome('grandma', { lantern: false })`; glasses tilted 8 deg at the cut, levelled on "glasses". | s04, s08 |
| `gnome_grandpa` | **EXISTS** | Grandpa gnome (hero creature) | `K.makeGnome('grandpa', { lantern: 0, wear: 0.12 })` (red pointed hat, white beard + walrus moustache, navy coat, brass lantern in the right hand). Blink `K.setGnomeLids(g, K.gnomeBlink(t, [t0]))`, slow blink `{ frames: 4, slow: true }`, head `K.gnomeHeadTurn`, lantern `K.setLantern` / `K.lanternLightUp`, idle `K.gnomeIdle`, ECU polish `softenBeard` (part1). Held in the hero's arms: parent to the hero's torso (`hug`/`carry` pose), gnome root at chest height, lantern hand outward. | s04, s05, s09, s10, s16, s17, s18, s25, s29, s30, s32, s33, s34, s38 ... (36 shots) |
| `gnome_grandpa_aged` | **EXISTS** | Grandpa gnome, mossy and faded (photos 1-60 years) | `K.makeGnome('grandpa', { age })` with age = years/60 * 0.9 (faded paint, moss on the hat and boots); lantern unlit, lid level per photo (`setGnomeLids`, the newest photo 0.55 = mid-blink). | s90, s91, s92, s93 |
| `gnome_plastic` | **EXISTS** | Plastic gnomes (next door's; Mom's BALCONY GNOME) | `K.makePlasticGnome({ finish: 'glossy' })` (bible: roughness 0.15, oversaturated, dead dot eyes, $4.99 sticker, black plastic lantern). Next door's face the STREET (decorations), never their house. | s12, s41, s49, s50, s51 |
| `gnome_toddler` | **EXISTS** | A family gnome that toddles to its gate | `K.makeFamilyGnome(0)` + `K.gnomeHop(t, t0, { height: 0.1, freq: 2.5, roll: 8 })` on the root; bonk = spring back 0.15 stud (`anim.springKeys`, 4 Hz, zeta 0.3). | s14 |
| `grandma_human` | **EXISTS** | Grandma (rose cardigan, bun, rose-gold glasses) | `K.makeCharacter('grandma')` (the approved test's Grandma); `cleanGlasses()` from part1 for close shots. | s02, s03, s04, s06 |
| `grandpa_human` | **EXISTS** | Grandpa as a man (flashbacks) | `K.makeCharacter('grandpa')` (the approved test's Grandpa: white side tufts, white 3D walrus moustache, round gold glasses, navy cardigan, tartan slippers) so the man matches his gnome's navy coat. The script's fishing-hat `grandpaFlashback` is NOT used (continuity with the approved porch shots). Holds the flashlight (`flashlight`). | s02, s04, s19, s20, s21, s22, s23, s24, s61, s62, s63, s64, s66 |
| `hero` | **EXISTS** | The hero, 11 (mustard hoodie, messy brown hair, freckles) | `K.makeCharacter('hero')` (day, spring); `K.makeCharacter('heroBarefoot')` from 27.81 s (the night of the move) to the end of the dawn scene. | s16, s17, s28, s31, s32, s33, s34, s35, s38, s39, s45, s46, s47, s49 ... (27 shots) |
| `hero_old` | **EXISTS** | The narrator at 71 | `K.makeCharacter('heroOld')` (grey hair and moustache, mustard cardigan, olive fishing hat, freckles); faces `content`, `wonder`, `heartfelt`. | s91, s92, s94, s95, s97 |
| `theo` | **EXISTS** | Theo, 6 (blue pyjamas, blond, x0.85) | `K.makeCharacter('theo')`; faces `sleeping`, `wonder`, `content`. Always carries the whale (`whale`). | s25, s44, s45, s55, s60, s69, s70, s71, s72, s82, s83, s85, s86, s87 ... (16 shots) |

## SETS

| ID | Status | Item | Kit call or spec | Used in |
|---|---|---|---|---|
| `back_garden` | **NEW** | The daughter's back garden (epilogue, dusk -> night) | sets_ep01.js `backGarden(ctx, { tod: 'dusk'/'blueHour' })`: the back of a two-storey house (siding, `addHouse` back wall) with the granddaughter's ground-floor bedroom window lit (pink-warm, curtains open, a nightlight), a garden bench (wood slats), the striped deck chair facing the window (`props.deckChair`, EXISTS), lawn with dandelion clocks (`props.dandelion`, EXISTS), a low fence and pines behind, the TF moon rising for the last shot. | s90, s91, s94, s95, s96, s97 |
| `garden_table` | **NEW** | A wooden garden table at dusk (Polaroid pile) | sets_ep01.js: slatted teak table top 8 x 5 studs (`tex.woodPlanks`, roughness 0.5) in the back garden, a mug and reading glasses beside the pile. | s90 |
| `grandma_room` | **NEW** | Grandma's living room (day) | interiors.js `grandmaRoom(ctx)`: rose wingback armchair (seat top 1.5 studs, high back, rolled arms), shag rug, standard lamp (cream drum shade, emissive), side table with the teacup + knitting basket (part1 `porchDressing` pieces), window with net curtains and daylight behind (emissive sky card), framed photos and a cuckoo clock on floral wallpaper (`tex.plaster` + painted pattern), skirting, terracotta planks. 5-15 props in every framing (bible 4.1). | s06, s07 |
| `hall` | **NEW** | Our hall at night (the night of the move) | interiors.js `hall(ctx)`: narrow hall 8 studs wide, the front door (dark red, a 4-pane glass panel at head height showing the night garden), the wall clock (orange rim #9c3703, lavender face, Roman numerals; hands at 8:59:59 -> 9:00 on "nine"), the hero's rolled-up sleeping bag on a mat by the door, three boxes taped and marked THEO (bold sans black on kraft), coat hooks with a mustard hoodie, a runner rug; packed-house feel (bare picture hooks). | s26 |
| `hero_lot` | **NEW** | Our front garden, EP01 dressing by time and era | sets_ep01.js `heroLot(ctx, { tod: 'night'/'day'/'dusk'/'dawn', era: 'now'/'2010s'/'1960s', truck, sold, keepOff, bed, theoRoom })` wraps `buildLawnCloseup` (same seed, so it is the house of the approved s05/s06) and adds: the KEEP OFF THE LAWN AFTER DARK post sign beside the gate (`props.postSign`), the agent board on the lawn by the path (`agentBoard`; `sold: t0` slaps the SOLD sticker), the moving truck at the kerb from 26.61 s (`truck: 'open'/'closed'/'leaving'`), brick edging on Grandpa's flowerbed (the 'bricks' of 61.37 s), Theo's window = the bedroom window over `A1.bed0` with a real room box behind the glass (`interiors.bedroom`, era-dressed; `theoRoom: { lit, curtains }`), the family gnomes at `bedFront0, lawn0-3, bedFront1` (as s06; when Grandpa's bed is in frame move `bedFront0` 1.5 studs toward the path so its lantern pool never covers the bed), `bed` = 'grandpa' / 'empty' (ring of flat pale soil 0.9 stud + two boot dents) / 'plastic' / 'hole' (sunken dark soil 0.8 stud + the $4.99 sticker) / 'grandpaBack'. Era '2010s': no truck/board, younger bush, the hero's toys on the porch; '1960s': no sign, a picket gate in a different colour (B&W anyway), a smaller tree. | s10, s16, s19, s22, s25, s27, s28, s29, s31, s32, s34, s45, s46, s50 ... (30 shots) |
| `hero_room` | **NEW** | The old bedroom (hero 11 -> Theo now; 1960s and 1990s/2010s dressings) | interiors.js `bedroom(ctx, { era: 'hero11'/'theo'/'hero5'/'dad60s'/'cousin90s', lit })`: the TF bedroom kit (bible 4.4): fabric wallpaper (era colour: hero/Theo #4958a0 blue, 1960s rose stripe, 1990s yellow floral), lavender ceiling with glow stars, glossy terracotta planks, thick white window frame (the window over Grandpa's bed: sill 1.6 studs above the lawn outside), era beds (hero11: carved headboard + magenta duvet; theo: a bare mattress on the floor + boxes THEO + a star nightlight projector; hero5: small bed with rocket duvet; dad60s: iron bed; cousin90s: bunk), posters (our own designs), shelf with books and a toy car. Built as a box 14 x 12 x 13 studs that attaches behind the hero bungalow's window, so the same room is seen from inside (s17, s44, s55, s66, s67, s71, s72) and through the glass from outside (s27, s45, s46, s68, s69, s70). | s17, s44, s45, s55, s60, s64, s66, s67, s68, s69, s70, s71, s72 |
| `next_door` | **NEW** | Next door's lawn (lot A2) | sets_ep01.js `nextDoor(ctx, { tod, dog, hole })`: lot A2 of the street (EXISTS via `buildLot`) dressed with 3 plastic gnomes in a row facing the street, the red kennel 'REX' (`props.kennel`, EXISTS), a hose reel (EXISTS), a red lead (tube along a Catmull curve) from the kennel ring across the lawn into THE HOLE: a neat round hole 0.9 stud across (an inverted cylinder 2 studs deep, black-brown interior #120a06, a lip of crumbs). Night version: lanterns are black plastic and never light. | s12, s13, s41 |
| `phone` | **NEW** | Phone in an old hand | sets_ep01.js `phone(ctx, { photos })`: a modern phone 1.0 x 2.0 studs (rounded box, black bezel), screen = emissive plane (x1.2) showing a photo texture; `swipe(t, [t0...])` slides the next photo in from the right in 8 frames (outCubic). Held by `hero_old`'s hand socket. | s91, s92, s94 |
| `polaroids` | **NEW** | Yearly photo series (Polaroids across 60 years) | sets_ep01.js `photoSeries(ctx, years)`: each photo is rendered ONCE per worker into a 512x512 texture (`photoTexture(ctx, year)`: a small scene = hero lot in spring daylight, Grandpa gnome `age` = year/60, Theo `theoAt(6 + year)`, tulip colours and window curtains changing per year, rendered with the `day` grade + `fx_photo_look`), then mounted on a Polaroid card 3.5 x 4.2 studs (white border, thick bottom margin with the year hand-written: '1st spring', '10', '25', '40', '60'). Used as a falling stack (s90), on the phone (s91-s93) and full frame (s93). Years: 1, 5, 10, 16, 25, 33, 40, 52, 60. | s90, s91, s92, s93 |
| `truck_cab` | **NEW** | Truck cab insert (dashboard clock) | interiors.js `truckCab(ctx)`: dashboard (dark plastic), a red 7-segment LED clock '11:52' (colon blinks 1 Hz), a steering wheel with a yellow sticky note 'LEAVE 6 AM' (marker font, bold), windscreen showing the night street (P1, darker than the cab). | s48 |
| `agent_board` | **EXTEND** | Estate-agent board + SOLD sticker | `props.prop('agentBoard', { header: 'FOR SALE', lines: ['3 BED · BIG GARDEN', 'COMES WITH ANCESTORS'] })` (EXISTS) + NEW `soldSticker`: a red rounded rectangle 'SOLD' decal that slaps on diagonally (scale 1.3 -> 1 in 4 frames, outBack) on "moved". | s10, s25 |
| `dusk_street` | **EXTEND** | A street at sunset with curtains | `sets.buildStreet` + `sets.dusk` (EXISTS) + NEW curtain planes per lit window (`curtainCascade`, fx). | s11 |
| `moving_truck` | **EXTEND** | The moving truck (kerb, open back, leaving) | `props.prop('movingTruck', { boxes: ['BALCONY GNOME', 'THEO', 'KITCHEN', ''] })` (EXISTS: 24 x 9 x 10 box, open back, ramp) + NEW: a cargo dome light (emissive + 1.5 cd point), the BALCONY GNOME box on top of the stack facing the house, a roller rear door (up), a `leaving` mode (truck root moves along the road at 0 -> 6 studs/s, wheels spin) and a rear POV rig (camera inside the cargo bay looking out, box edges framing). | s25, s29, s49, s57, s88 |
| `aerial_street` | **EXISTS** | Our street from high above | `sets.buildStreet` view `views.streetHigh`, all lots, + `fx_lantern_ring` per lit gnome. | s43 |
| `dawn_lawn` | **EXISTS** | A neighbour's front lawn at dawn (Grandma's) | `sets.buildLot(ctx, { seed: 'ep01-gm' })` + `sets.dawn`; dew via sparkles. | s08 |
| `gate_lot` | **EXISTS** | A neighbour's front gate at night | Lot A3 of `sets.buildStreet` (gate leaf `gate_A3`, hinged), `sets.nightLawn`; + `fx_property_line`. | s14, s15 |
| `keep_off_sign` | **EXISTS** | KEEP OFF THE LAWN AFTER DARK sign | `props.prop('postSign', { lines: ['KEEP OFF', 'THE LAWN', 'AFTER DARK'] })`: by our gate (hero lot) and on the dusk street corner (s11). | s11, s19, s28 |
| `lawn_closeup` | **EXISTS** | Our front lawn close-up set (hero lot A1) | `sets.buildLawnCloseup(ctx, { seed: 'ep01' })`: hero bungalow, bedroom window low over Grandpa's bed (slot `A1.bed0`), family gnome slots, `sets.nightLawn`. | s05, s09, s18, s70 |
| `porch_set` | **EXISTS** | Grandparents' porch + swing (approved test) | part1 `porchScene()` (sets.buildLot + PORCH_HOUSE, `buildSwing`, `spindleRail`, `porchDressing`). | s02, s03, s04 |
| `street_night` | **EXISTS** | Our street at night (P1) | `sets.buildStreet(ctx, { seed: 'ep01', lotsPerSide: 6, hero: { side: 'A', index: 3 } })` + `streetGnomes()` (part1) + `sets.nightStreet`. | s01, s35, s40, s88 |

## EFFECTS

| ID | Status | Item | Kit call or spec | Used in |
|---|---|---|---|---|
| `fx_beam` | **NEW** | Flashlight beam | fx_ep01.js `flashlightBeam(ctx, { socket, length: 9 studs, angle: 14 deg })`: an additive cone (radial gradient along the axis, soft edges, opacity 0.18) + a ground spot (`lightPool` ellipse) + a spot light 4 cd #fff1d0, no shadow; `on(t0)` switches in 1 frame. | s19, s20, s22, s24, s61, s63, s64, s66, s67, s68 |
| `fx_curtains` | **NEW** | Curtains snap shut down the street | fx_ep01.js `curtainCascade(set, { t0, gap: 0.12, n: 6 })`: per lit window two fabric planes (`tex.fabric`, wine #7a2a3a) slide shut in 4 frames (outQuad) and the window emissive drops to x0.6 behind them. | s11 |
| `fx_glass_fog` | **NEW** | Breath fog on the window glass | fx_ep01.js `glassFog(ctx, pane, { t0, center, r1: 0.9 stud })`: an animated alpha mask (soft noisy disc, grows over 0.35 s, opacity 0.55, #dfe4ff) on the pane, lit by the amber eyes behind it. | s55 |
| `fx_gold_outline` | **NEW** | "Only family" gold outline | fx_ep01.js `goldOutline(obj, { color: '#ffd27a', scale: 1.03, opacity })`: inverted hull (BackSide clones, additive) on the given meshes (hands/arms + the gnome), opacity animated 0 -> 0.9 -> 0.5; + 6-10 gold sparkles. Two uses: s15 (Dad's hands) and s32-s33 (the hero's arms). | s15, s32, s33 |
| `fx_lantern_cascade` | **NEW** | Every lantern lit (street cascade) | fx_ep01.js `lanternCascade(ctx, gnomes, { t0, order: 'toward camera', gap: [0.15, 0.3], skip: ['A2'] })`: calls `K.lanternLightUp` per gnome at its own t0 (seeded gaps), adds its ring (radius 2) and a tink cue time list for the mix. Next door (A2) skipped. | s40 |
| `fx_lantern_ring` | **NEW** | Lantern ring of light (the moles stop at its edge) | fx_ep01.js `lanternRing(ctx, { center/follow, radius: 5 studs })`: an additive ground disc with a flat warm interior (#ffcf8a at 0.22), a bright crisp rim 0.25 stud wide (#ffe2a8 at 0.55) and a 0.6-stud soft falloff outside; it follows the lantern's ground point (slides with the hero). `edgeOf(pos)` returns the rim point toward pos (moles call `stopAt` there). Grandpa's ring radius 5 studs; family/street gnomes 2 studs. | s39, s40, s41, s42, s43, s45, s46, s50, s56, s58, s69, s70, s73, s76 ... (15 shots) |
| `fx_photo_look` | **NEW** | Photo print look | fx_ep01.js `photoLook(tex)`: for photo textures: lifted blacks (#2a2420), warm cast +8, saturation 0.85, a soft inner vignette inside the print only, a 1-px paper grain; Polaroid frame card. Never on the episode frame itself (bible: clean image). | s90, s93 |
| `fx_property_line` | **NEW** | Property-line shimmer + bonk ripple | fx_ep01.js `propertyLine(ctx, { a, b, height: 2.6 })`: a vertical additive curtain along the lot boundary at the gate (shader: faint lavender-gold vertical streaks drifting up 0.3 studs/s, opacity 0.06 idle, fades out at the top) + a gold line on the path. `bonk(t0, at)`: concentric ripple rings on the curtain from the contact point (3 rings, 0.45 s, radius 0 -> 2 studs, opacity 0.6 -> 0) + `fx_burst` small (12 sparkles); `part(t0, at)` (family carries it out): the curtain parts in a gold flash with 10 gold sparkles, no ripple. | s14, s15, s29, s32 |
| `fx_soil` | **NEW** | Soil crumbs / dust puff | fx_ep01.js `soilBurst(ctx, { pos, t0, count: 24, spread })`: instanced brown lumps (0.05-0.12 stud) thrown up on parabolas (0.4 s) + 3 soft dust puff sprites (#6a5040, opacity 0.5). Mound tops, the GULP seal, the lawn moving. | s34, s35, s37, s51 |
| `fx_sticker` | **NEW** | Price sticker flutter | fx_ep01.js `flutter(ctx, { tex: '$4.99', from, to, t0, dur: 0.4 })`: a 0.5-stud paper quad falling with a side-to-side swing (+-35 deg) and landing flat on the soil. | s51 |
| `fx_tear` | **NEW** | The gnome's dewdrop tear | fx_ep01.js `dewTear(ctx, gnome, { eye: 'L', t0, dur: 0.6 })`: a glossy water drop (MeshPhysical transmission-free: roughness 0.05, clearcoat 1, env-lit, a 6 px catchlight sprite) that swells at the lower lid for 0.15 s then slides down the cheek and beard (path in head-local coordinates). | s30 |
| `fx_window_dark` | **NEW** | Theo's window goes dark (what-if) | fx_ep01.js `windowState(win, level)` on the hero lot's Theo window: emissive and the room's nightlight to 0 in 1 frame on "dark" (light-state event), restored in later shots. | s46 |
| `fx_fwoom` | **EXTEND** | FWOOM: lantern flare + light rolling across the lawn | `sets.magicGlow(ctx, { source })` + `rig.fwoom(t0)` (EXISTS: lantern 8 -> 50 cd in 0.15 s, -> 10 over 1.5 s) + `K.setLantern(g, 4..6)` + `fx_burst` + part1 `streaks` + `fx_grade_blend` to `magic` in 8 frames, plus NEW fx_ep01.js `lightWave(ctx, { center, speed: 8 studs/s, height: 1.0, width: 1.4 })`: a thick additive ring wall rolling outward over the grass (gold #ffd38a core, pink #ff9ad5 trailing edge, sparkles kicked up at the front), radius = speed * (t - t0); moles inside the radius `sink` (staggered, 0.5 s each) and their eyes wink out pair by pair (`setMoleEyes` 0 in 2 frames, 0.2-0.3 s apart, a blip cue each). | s77, s78, s79, s80 |
| `fx_burst` | **EXISTS** | VFX burst (TF) | `sets.burst(ctx, { pos, t0, dur: 0.35, count, ringPx, corePx })` + part1 `streaks()` / `poofCloud()` (promote both to fx_ep01.js). | s04, s14, s77 |
| `fx_contact` | **EXISTS** | Contact shadows, light pools, halos | `sets.contactShadow`, `sets.lightPool`, `sets.glow`. | - |
| `fx_dandelion` | **EXISTS** | Dandelion seed clock | `props.prop('dandelion', { puff: true })` + `sets.burst(ctx, { puff: 14, count: 0 })` seeds drifting 0.3 studs/s in the last shot. | s97 |
| `fx_dew` | **EXISTS** | Dew sparkles (dawn) | `sets.sparkles` with warm colours ['#ffe2c4', '#fff4e0'], px 30-50, count 4-6, drift low (bible dawn: 0-6 warm motes). | s08, s21, s62, s82, s83, s85 |
| `fx_grade_blend` | **EXISTS** | In-shot grade switch over 6-10 frames | part1 `gradeBlend(A, B)` + the s04 update block (promote to fx_ep01.js as `inShotGrade(ctx, fromPreset, toPreset, t0, frames, amount)`). | s04, s38, s77, s80 |
| `fx_magic_dust` | **EXISTS** | Gold / pink motes | `sets.magicDust(ctx, { center, radius, height, count })`. | s04, s05, s38, s42, s47, s75, s77 |
| `fx_shake` | **EXISTS** | Camera shake | `ctx.camera.shake({ t0, dur: 0.5, px, freq: 14 })`. | s14, s34, s51, s77 |
| `fx_sparkles` | **EXISTS** | TF sparkle glints | `sets.sparkles(ctx, { ...SPARK, center, size, count })` with the approved `SPARK` look (sharpness 7, core 0.75, underlay 0.55 @ 0.5, brightness 2.0, 55-95 px) from part1; outdoors 6-12, interiors and magic 8-20; none in day shots. | s01, s02, s03, s05, s09, s14, s15, s17, s18, s27, s29, s30, s32, s33 ... (32 shots) |
| `fx_star_glint` | **EXISTS** | One big 4-point star glint | part1 `starGlint(ctx, { pos, t0, peak, rot })` (promote to fx_ep01.js). | s03, s08, s36, s44 |

### Lighting and post presets needed

| Preset | Status | Spec | Used in |
|---|---|---|---|
| `nightStreet` | **EXISTS** | `sets.nightStreet` | s01, s29, s32, s33, s35, s40, s41, s43 |
| `porchGlow` | **EXISTS** | `sets.porchGlow` + part1 `PORCH_LIGHT` | s02, s03, s04 |
| `nightLawn` | **EXISTS** | `sets.nightLawn` | s05, s09, s14, s15, s18, s19, s20, s21, s22, s27, s28, s34, s36, s37, s38, s39 ... (30) |
| `interiorDay` | **NEW** | interiors.js `interiorDay(ctx, { window })`: hemi #ffe8d0 / #6a4a3a 1.1, window key #fff3e0 2.0 from upper front-left (soft, no shadow), standard-lamp practical 2 cd, post `day` | s06, s07 |
| `dawn` | **EXISTS** | `sets.dawn` | s08, s82, s83, s84, s85, s86, s87, s88, s89 |
| `day` | **EXISTS** | `sets.day` (shot `quality: { shadows: 'pcfsoft' }`) | s10, s12, s13, s16, s93 |
| `dusk` | **EXISTS** | `sets.dusk` | s11, s25, s90, s91, s92, s94, s95, s96 |
| `bedroomNight` | **NEW** | interiors.js `bedroomNight(ctx, { lamp, moon, lanternOutside })` = bible P2: hemi #b9a8ff / #5a2a4a 1.3, key #e8deff 1.0, lamp 3-5 cd + halo, moonlight #9aa6ff 0.4, an optional warm lantern spill through the window (#ffb85c 2 cd); post `bedroom`; window view darker than the room | s17, s26, s44, s55, s66, s67, s71, s72 |
| `flashlight` | **NEW** | part of `fx_beam` (spot 4 cd #fff1d0) + under-chin point 2.5 cd for s23 | s23 |
| `sepia` | **EXISTS** | `sets.nightLawn` lit, graded with `postPreset('sepia')`, + `fx_beam` (the flashlight) | s24, s62, s63, s64, s68 |
| `lamp-post` | **EXISTS** | `sets.practicals` lamp lights + a warm 2.5 cd key placed by the shot | s30 |
| `porch` | **EXISTS** | nightLawn + porch lantern practical | s31 |
| `lantern` | **EXISTS** | `K.setLantern` light (0.7-3 cd) | s47, s57, s58, s59, s60, s65, s74, s75, s76 |
| `cabNight` | **NEW** | interiors.js `cabNight(ctx)`: dashboard glow 1 cd #ff5040 (LED) + #ffd9a0 street spill through the windscreen, hemi #8a90ff 0.6; post `night` | s48 |
| `truck` | **NEW** | truck cargo dome light (part of `moving_truck` EXTEND) | s49 |
| `magicGlow` | **EXISTS** | `sets.magicGlow` (+ `rig.fwoom`) | s77, s78, s79, s80 |
| `nightStreet-like:` | **EXISTS** | nightStreet + 2.8 cd warm spill (the s01 frame-0 key) | s97 |

Post presets: `postPreset(name)` EXISTS for every grade used (bedroom, bw, dawn, day, dusk, magic, night, nightHigh, porch, sepia). In-shot switches use `fx_grade_blend`.

## SOUND (cue list by name for the whole episode)

Times are episode seconds of the picture event (the word onset from `word_onsets.json`, or the event time in the timeline). **Primary** cues are the ones the mix must have (about 20 events in 113 s, inside the bible's 6-12 per minute); the rest are optional sweeteners, left out if the mix gets busy. No whooshes on plain cuts. The owner's music bed sits about 8 LU under the voice and drops out for the four planned pauses.

| Cue | Kind | Sound | Shots |
|---|---|---|---|
| `A_NIGHT` | bed | Crickets, suburban night, no traffic (HPF 250 Hz), the test's A1 | all night exteriors; dropped to near-silence under "empty" (28.87-29.74) |
| `A_ROOM` | bed | Interior room tone, soft clock tick far away | interiors (s06-s07, s17, s26, s44, s55, s66-s67, s71-s72) |
| `A_DAY` | bed | Day suburb: birds, distant mower | s10, s12-s13, s16 |
| `A_DUSK` | bed | Evening birds settling | s11, s25, s90-s96 |
| `A_DAWN` | bed | Dawn chorus, light | s08, s82-s89 |
| `MUSIC` | bed | The owner's music bed, about 8 LU under the voice; drops out for the 4 planned pauses | whole episode |
| `W1` (primary) | hit | Airy whoosh (test) | s01 |
| `M1` (primary) | hit | Music-box / chime shimmer (test; swap the Christmas sparkle per review defect 20) | s04-s05 |
| `P1` (primary) | hit | Cartoon pop (test) | s04 |
| `T_GLINT` | hit | Tiny glass ting | s08 (glasses) |
| `TOK` | hit | Ceramic tap | s16 |
| `SQUEAK` | hit | Squeaky toy bite | s12 |
| `CHAIN_TUG` | hit | Dog lead clink + single tug | s13 |
| `HOPS` | hit | Tiny ceramic hop clicks | s14 |
| `BONK` (primary) | hit | Hollow ceramic bonk + glassy ripple "wom" | s14 |
| `LATCH` (primary) | hit | Gate latch click | s15 |
| `SHIMMER_S` | hit | Soft gold shimmer | s15, s32 |
| `TIK` (primary) | hit | Ceramic blink "tik" | s18, s86 |
| `TIK_SLOW` (primary) | hit | Slower, lower "tik" | s75 |
| `CLICK_TORCH` (primary) | hit | Flashlight click | s20, s61 |
| `STEP_WET` | hit | Slipper on wet grass | s21, s62 |
| `SLAP_STICKER` (primary) | hit | Sticker slap (paper thwack) | s25 |
| `TICK_CLOCK` | hit | One loud clock tick | s26 |
| `DOOR_BANG` (primary) | hit | Front door bangs open | s28 |
| `FEET_WET` | hit | Bare feet running on wet grass | s28, s56 |
| `CLINK` (primary) | hit | Ceramic clink | s32 |
| `CREAK_LANTERN` | hit | Small lantern handle creak | s33 |
| `SUBBOOM` (primary) | hit | Whoosh + sub-boom + low rumble (the reveal hit) to about 39.5 s | s34-s35 |
| `CRUMBLE` | hit | Soil crumbling | s35, s51 |
| `PLINK` | hit | Reflector glint plink | s36 |
| `SNIFF` (primary) | hit | Wet sniff + wriggle | s37, s53 |
| `TINK_WHOOSH` (primary) | hit | Lantern tink-whoosh (light-up) | s38 |
| `FIP` | hit | Snout recoil squeaks x3 | s39 |
| `TINKS` (primary) | hit | Cascade of tinks 0.15-0.3 s apart | s40 |
| `CLATTER` | hit | Plastic clatter into a hole | s41 |
| `THUD_LOW` | hit | Low soft thud (window goes dark) | s46 |
| `RIP` | hit | Cardboard tape rip | s49 |
| `THUNK_PLASTIC` | hit | Plastic gnome into soil | s50 |
| `GULP` (primary) | hit | GULP | s51 |
| `FLUTTER` | hit | Paper flutter | s51 |
| `RUMBLE_ROLL` | hit | Rolling rumble | s52 |
| `BRICK` | hit | Brick clunk | s54 |
| `BREATH` | hit | Breath on glass | s55 |
| `TIDE` | hit | Turf receding whoosh | s56 |
| `GRIND` (primary) | hit | Stony grind / creak | s59, s89 (soft) |
| `KNEEL` | hit | Knees in soil | s73 |
| `SET_DOWN` | hit | Ceramic set down on soil | s76 |
| `FWOOM` (primary) | hit | Whoosh + warm shimmer 1.5-2 s (the light-up hit) | s77-s78 |
| `PASS` | hit | Light-wave pass-by whoosh | s78 |
| `DEFLATE` (primary) | hit | Soft deflating thumps 0.15 s apart | s79 |
| `BLIPS` (primary) | hit | Tiny pitched blip per eye pair (5) | s80 |
| `DOOR_CREAK` | hit | Front door opening, morning | s82 |
| `ENGINE` (primary) | hit | Truck engine starts, idles, drives off | s87-s89 |
| `RATTLE` | hit | Boxes rattling in the truck | s88 |
| `DROPS` | hit | Polaroids dropping on wood | s90 |
| `PING` | hit | Phone message ping | s91 |
| `SWIPE` | hit | Phone swipe | s92 |
| `POOF_SOFT` (primary) | hit | Dandelion poof, soft | s97 |

### Event cue sheet (from the timeline)

| Time (s) | Frame | Shot | Word | Picture event | Cue |
|---|---|---|---|---|---|
| 0.000 | 0 | s01 |  | snap pull-back at full speed on frame 0 | W1 airy whoosh (peak 0.12 s) + A1 crickets bed starts |
| 2.233 | 134 | s04 | turn | sparkle burst + human -> gnome snap | P1 poof (pop transient 2.240 s) over M1 shimmer swell (from 2.10, peak 2.30) |
| 6.600 | 396 | s08 | glasses | glasses snap level (8 frames outBack) + star glint on the lens (peak 120 px) | T_GLINT (optional) |
| 11.685 | 701 | s11 | dark | curtains snap shut on 6 lit windows, 0.12 s apart, nearest first (curtainCascade) | CURTAIN swish (optional) |
| 13.230 | 794 | s12 | plastic | the dog bites the hat: hat squashes 15 % for 6 frames | SQUEAK |
| 14.595 | 876 | s13 | hole | lead tugs 0.1 stud toward the hole (spring) | CHAIN_TUG |
| 16.312 | 979 | s14 | garden | bonk: ripple rings + 12-sparkle burst + shake 4 px 0.3 s | BONK |
| 17.033 | 1022 | s15 | family | gnome crosses the line: curtain parts (gold flash, 10 gold sparkles) | SHIMMER_S |
| 17.728 | 1064 | s15 | out | gate leaf swings shut (6 frames) and latches | LATCH |
| 18.085 | 1085 | s16 | grandpa | tap on the hat (hat tip wobbles +-6 deg, spring) | TOK |
| 20.558 | 1233 | s18 | blinks | blink, 2 frames (K.gnomeBlink) | TIK |
| 23.018 | 1381 | s20 | flashlight | flashlight on (1 frame) + beam | CLICK_TORCH |
| 23.560 | 1414 | s21 | slippers | slipper lands (6 frames after the cut) | STEP_WET |
| 27.510 | 1651 | s25 | moved | SOLD sticker slaps on (scale 1.3 -> 1 in 4 frames) | SLAP_STICKER |
| 27.933 | 1676 | s26 | nine | minute hand ticks to 12 (2-frame snap + 3-frame wobble) | TICK_CLOCK |
| 30.115 | 1807 | s28 | ran | door bangs open | DOOR_BANG |
| 30.483 | 1829 | s28 | barefoot | first bare foot lands, then every 0.25 s | FEET_WET |
| 35.087 | 2105 | s32 | picked | lift + gold ripple along the line + 6 gold sparkles | CLINK |
| 37.280 | 2237 | s34 | moved | the bulge surges 0.8 stud + shake | SUBBOOM (whoosh + sub-boom + rumble to 39.5) |
| 38.080 | 2285 | s35 | mounds | mounds rise staggered 0.05-0.15 s apart | CRUMBLE |
| 38.717 | 2323 | s36 | eyes | eyes on (0 -> 1 in 3 frames) | PLINK |
| 39.960 | 2398 | s37 | moles | turf tears, snout 1 unfurls (0.3 s outBack) | SNIFF |
| 41.760 | 2506 | s38 | lit | lantern 0 -> 1 in 3 frames (overshoot 1.5), halo 0.2 s; grade warms over 8 frames to 60 % magic; 12 gold motes | TINK_WHOOSH |
| 42.745 | 2565 | s39 | edge | snouts recoil at the rim (0.15 s spring) | FIP |
| 44.630 | 2678 | s40 | every | lantern cascade starts (12 lanterns, 0.15-0.3 s apart, toward camera) | TINKS |
| 46.005 | 2760 | s41 | door | plastic gnome tips into a hole | CLATTER |
| 53.100 | 3186 | s46 | dark | Theo's window off (1 frame) + mounds surge 0.5 stud | THUD_LOW |
| 56.630 | 3398 | s49 | stood | tape rips | RIP |
| 57.887 | 3473 | s50 | under | plastic gnome thunks into the soil | THUNK_PLASTIC |
| 58.865 | 3532 | s51 | gulp | swallow (moleField.swallow) + soil burst | GULP |
| 59.330 | 3560 | s51 | gone | price sticker flutters down (0.4 s) | FLUTTER |
| 60.045 | 3603 | s52 | rolled | mounds travel 3 studs/s toward the bed | RUMBLE_ROLL |
| 60.997 | 3660 | s53 | flowers | tulips shake, snouts wriggle | SNIFF |
| 61.635 | 3698 | s54 | bricks | a brick tips out (10 deg) | BRICK |
| 62.133 | 3728 | s55 | glass | fog blooms on the pane (0.35 s) | BREATH |
| 63.097 | 3786 | s56 | back | feet plant in the bed | FEET_WET |
| 63.578 | 3815 | s56 | backed | tide: mounds pushed back 3 studs in 0.5 s | TIDE |
| 66.550 | 3993 | s59 |  | head turn starts (0.8 s inOutSine, ends 0.1 s before the cut) | GRIND (peaks on "head") |
| 69.078 | 4145 | s61 | flashlight | flashlight on | CLICK_TORCH |
| 69.623 | 4177 | s62 | slippers | slipper lands | STEP_WET |
| 81.638 | 4898 | s73 | knelt | kneel | KNEEL |
| 83.680 | 5021 | s75 | blinked | slow blink (K.gnomeBlink frames 4, slow) | TIK_SLOW |
| 85.495 | 5130 | s76 | him | gnome touches the soil | SET_DOWN |
| 86.860 | 5212 | s77 |  | FWOOM (on the vowel): lantern 8 -> 50 cd in 0.15 s, emissive x25, burst + streaks, grade to magic in 8 frames | FWOOM |
| 89.133 | 5348 | s78 | across | the wave passes the lens | PASS |
| 90.178 | 5411 | s79 | mound | mounds sink, staggered 0.15 s, following the ring | DEFLATE |
| 91.290 | 5477 | s80 | winking | pair 1 out | BLIPS |
| 94.892 | 5694 | s82 | came | front door opens (14 frames) | DOOR_CREAK |
| 99.890 | 5993 | s86 | blinked | blink, 2 frames | TIK |
| 103.050 | 6183 | s89 |  | head turns back to the window (0.8 s) | GRIND (soft) |
| 103.830 | 6230 | s90 | spring | photo 1 lands | DROPS |
| 105.345 | 6321 | s91 | sent | message ping, the photo slides up | PING |
| 106.750 | 6405 | s92 | same | swipe to the flowerbed photo (8 frames) | SWIPE |
| 112.690 | 6761 | s97 | window | dandelion seeds lift (burst puff 14) | POOF_SOFT |
