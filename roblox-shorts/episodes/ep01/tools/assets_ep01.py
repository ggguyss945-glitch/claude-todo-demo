# EP01 asset registry: every set, set dressing, character, creature, prop, effect and sound the full-episode board uses.
# make_board.py writes ASSETS.md from this table and fills each "used in" column from the shots' `assets` lists.
# status: EXISTS (kit call given) | NEW (spec given) | EXTEND (exists, needs the option or change described).
# owner: CAST (creatures.js + cast/face additions), SETS (sets_ep01.js / interiors.js), FX (fx_ep01.js), SOUND.

A = {}
def a(id, owner, status, name, how, file=None):
    A[id] = dict(id=id, owner=owner, status=status, name=name, how=how, file=file)

# ------------------------------------------------------------------ CREATURES + CAST
a('gnome_grandpa', 'CAST', 'EXISTS', 'Grandpa gnome (hero creature)',
  "`K.makeGnome('grandpa', { lantern: 0, wear: 0.12 })` (red pointed hat, white beard + walrus moustache, navy coat, brass lantern in the right hand). "
  "Blink `K.setGnomeLids(g, K.gnomeBlink(t, [t0]))`, slow blink `{ frames: 4, slow: true }`, head `K.gnomeHeadTurn`, lantern `K.setLantern` / `K.lanternLightUp`, idle `K.gnomeIdle`, ECU polish `softenBeard` (part1). "
  "Held in the hero's arms: parent to the hero's torso (`hug`/`carry` pose), gnome root at chest height, lantern hand outward.")
a('gnome_grandpa_aged', 'CAST', 'EXISTS', 'Grandpa gnome, mossy and faded (photos 1-60 years)',
  "`K.makeGnome('grandpa', { age })` with age = years/60 * 0.9 (faded paint, moss on the hat and boots); lantern unlit, lid level per photo (`setGnomeLids`, the newest photo 0.55 = mid-blink).")
a('gnome_grandma', 'CAST', 'EXISTS', 'Grandma gnome (lavender hat, rose coat, apron, round glasses)', "`K.makeGnome('grandma', { lantern: false })`; glasses tilted 8 deg at the cut, levelled on \"glasses\".")
a('gnome_family', 'CAST', 'EXISTS', 'Street / family gnomes (8 variants)', "`K.makeFamilyGnome(i, { lod: 'mid'|'low', lantern: 0 })`; `POINTED` variant list in part1. Lanterns light in the 44.58 s cascade.")
a('gnome_toddler', 'CAST', 'EXISTS', 'A family gnome that toddles to its gate', "`K.makeFamilyGnome(0)` + `K.gnomeHop(t, t0, { height: 0.1, freq: 2.5, roll: 8 })` on the root; bonk = spring back 0.15 stud (`anim.springKeys`, 4 Hz, zeta 0.3).")
a('gnome_plastic', 'CAST', 'EXISTS', "Plastic gnomes (next door's; Mom's BALCONY GNOME)",
  "`K.makePlasticGnome({ finish: 'glossy' })` (bible: roughness 0.15, oversaturated, dead dot eyes, $4.99 sticker, black plastic lantern). Next door's face the STREET (decorations), never their house.")
a('moles', 'CAST', 'NEW', 'Giant star-nosed moles (second hero creature)',
  "creatures.js `makeMole({ scale, seed })` -> Group (studs x STUD) with parts `mound`, `snout`, `tentacle0..21`, `eyeL/R`, `eyeHaloL/R`. "
  "Only the mound, the snout and the eyes ever show (no teeth, no mouth, no body). "
  "MOUND: a displaced turf dome 3.0 x 0.75 studs (scale 1) built from a 48x48 grid with the lawn's own grass texture + `grassBlades` tufts on top, a crumb ring of 40 instanced soil lumps (0.06-0.14 stud) at the rim, darker wet soil showing in 3-5 cracks. "
  "SNOUT: the star nose, 0.9 stud across at scale 1: a pink disc (MeshPhysical #e48aa0, roughness 0.5, sheen 0.6 #ffc0d0, faint emissive #401018) ringed by 22 tapered capsule tentacles (11 per side, 0.32-0.45 long, 0.07 thick at the root), "
  "each a bent CatmullRom tube so it can curl; wriggle +-10 deg at 2-3 Hz with per-tentacle phase; unfurl = tentacles open from a closed bud in 0.3 s (outBack); recoil = snap back 0.15 s with spring overshoot (`anim.springKeys`). "
  "EYES (the bike reflectors): two 0.22-stud domes 0.6 apart above the snout, a faceted retro-reflector texture (hexagonal cube-corner cells, 7 across, each cell a tiny radial gradient) under a clear glossy cap (clearcoat 1), "
  "emissive #ffb020 x3-5 that rises toward the camera (fake retro-reflection: emissive *= 0.4 + 0.6 * max(0, dot(N, toCamera))^4), a 15-25 px halo sprite each; `setMoleEyes(m, level)` 0 = dark (wink out in 2 frames) .. 1; `reflectorFlash(t, t0)` = a 4-point star glint sweep. "
  "Scales: 1 = lawn mound (3 studs); 1.8 = 'BIG ones' hero snout (cheat per shot, bible 2.6 #6).")
a('mole_field', 'CAST', 'NEW', 'Mound / trench system on the lawn',
  "creatures.js `moleField(ctx, { area, count, paths, seed })`: N moles travelling along Catmull paths at 2-4 studs/s as a bulge wave under the turf (a lawn patch with vertex displacement: Gaussian bump r 1.6 studs, height 0.6-0.9, plus a 0.25-stud raised trench ridge left behind that relaxes over 3 s). "
  "API, all pure functions of t: `rise(i, t0, dur)` (mound pushes up, soil crumbs pop), `travel(i, path, t0, speed)`, `stopAt(i, center, radius)` (stops at a light ring's edge: the bulge flattens against the rim and the snout recoils), `sink(i, t0, 0.5)` (deflate + turf settles), `swallow(i, target, t0)` (GULP: turf rises around the target like a closing mouth, target sinks 6 frames, turf seals), `pushBack(center, r0, r1, t0, 0.5)` (tide). "
  "Lawn displacement is one shared 128x128 plane over the hero lawn (or a 64x64 per neighbour lawn) so many mounds cost one mesh.")
a('dog', 'CAST', 'NEW', "Next door's dog (REX)",
  "creatures.js `makeDog({ coat: '#c98a4a', patch: '#f2ece2', ears: '#6a3a1e' })`: a Roblox-built beagle: box body 2.2 x 1.1 x 1.0 studs (bevel 0.06), 4 box legs 0.35 x 0.7, a rounded drum head 0.8 with a decal face (dog nose, ^^ eyes, tongue), floppy box ears hinged at the top, a stub tail (wag +-25 deg at 6 Hz), red collar + lead attach point `leadSocket`. "
  "Poses: `lie`, `sit`, `chew` (head down 25 deg, jaw-less: the head bobs 2 Hz). Appears in s12 only (alive, chewing a plastic gnome's hat); s13 shows its empty kennel and lead running into the hole. Never shown going down the hole.")
a('hero', 'CAST', 'EXISTS', 'The hero, 11 (mustard hoodie, messy brown hair, freckles)', "`K.makeCharacter('hero')` (day, spring); `K.makeCharacter('heroBarefoot')` from 27.81 s (the night of the move) to the end of the dawn scene.")
a('hero_muddy', 'CAST', 'EXTEND', 'Hero barefoot with muddy knees and feet (dawn)', "`K.makeCharacter('heroBarefoot', { outfit: { pants: { ...heroHoodie.pants, mud: { knees: 0.8, feet: 0.6 } } } })`: NEW `mud` option in clothing.js pants painter (brown #4a2e1c blotches, alpha 0.7, on the knee band and the bare-foot ends).")
a('hero_kid5', 'CAST', 'NEW', 'The hero aged 5 (sepia flashback, asleep)', "cast.js `heroKid5`: hero skin + freckles, messy brown hair, rocket pyjamas (`pyjama` style, navy #2c3e7a with yellow rocket pattern via `stars` type), scale 0.75 (bible exception), face `sleeping`.")
a('theo', 'CAST', 'EXISTS', 'Theo, 6 (blue pyjamas, blond, x0.85)', "`K.makeCharacter('theo')`; faces `sleeping`, `wonder`, `content`. Always carries the whale (`whale`).")
a('theo_socks', 'CAST', 'EXTEND', 'Theo in socks (dawn)', "`K.makeCharacter('theo', { outfit: { ...OUTFITS.theoPyjamas, pants: { ...OUTFITS.theoPyjamas.pants, shoes: { style: 'socks', color: '#f4f2ee', pattern: { type: 'stripes', color: '#5a8ad8' } } } } })`, the socks band 0.45 stud so it reads in a WS.")
a('whale', 'CAST', 'NEW', "Theo's grey-blue stuffed whale", "creatures.js `stuffedWhale()`: plush whale 1.4 studs long, lathe body #7f93ad with a pale belly #dfe6ee, two felt fins, a split tail, button eyes, fabric texture (`tex.fabric`, bump 0.02). Parented to Theo's hand socket or hugged (`hug` pose).")
a('badge6', 'CAST', 'NEW', 'Birthday badge "6"', "A round pin badge 0.45 stud (yellow #f2c230, red rim, a black '6' in the bible sign font) pinned on Theo's pyjama chest; glints on \"six\".")
a('theo_aged', 'CAST', 'NEW', 'Theo at 7-66 (photo series only)', "cast.js `theoAt(age)`: scale 0.85 (7-10) -> 1.0 (14+); hair blond short -> brown -> grey -> bald with white side tufts (`grandpa` hair style) at 60+; NEW beard accessory `beard` (chunky grey clump beard) from 40; clothes per decade (tee, hoodie, flannel, cardigan).")
a('grandpa_human', 'CAST', 'EXISTS', 'Grandpa as a man (flashbacks)',
  "`K.makeCharacter('grandpa')` (the approved test's Grandpa: white side tufts, white 3D walrus moustache, round gold glasses, navy cardigan, tartan slippers) so the man matches his gnome's navy coat. "
  "The script's fishing-hat `grandpaFlashback` is NOT used (continuity with the approved porch shots). Holds the flashlight (`flashlight`).")
a('flashlight', 'CAST', 'NEW', "Grandpa's flashlight", "A chunky R6-scale torch 0.9 stud long (red rubber body #b8261e, chrome head, glass lens emissive #fff1d0 when on), parented to the hand socket; beam = `fx_beam`.")
a('grandpa_young', 'CAST', 'NEW', 'Grandpa in the 1960s (B&W only)', "cast.js `grandpaYoung`: `grandpa` with dark-brown hair (`short` style), dark moustache, no glasses, no wrinkles, same navy cardigan.")
a('dad_kid', 'CAST', 'NEW', 'Dad as a small boy (1960s, B&W, asleep)', "cast.js `dadKid`: scale 0.75, striped pyjamas, short dark hair, NEW `ears` accessory (two sticking-out half-discs 0.35 stud on the drum sides: the plant for Dad's ears), face `sleeping`.")
a('cousin_kid', 'CAST', 'NEW', 'A small girl in the 1990s (sepia, asleep)', "cast.js `cousinKid`: scale 0.75, pigtails (NEW hair style `pigtails`: two side clumps with ribbons), floral nightie, face `sleeping`.")
a('grandma_human', 'CAST', 'EXISTS', 'Grandma (rose cardigan, bun, rose-gold glasses)', "`K.makeCharacter('grandma')` (the approved test's Grandma); `cleanGlasses()` from part1 for close shots.")
a('grandma_short', 'CAST', 'NEW', 'Grandma, shorter (jump cut)', "`K.makeCharacter('grandma', { scale: 0.8, outfit: { ...grandmaCardigan, shirt: { ...grandmaCardigan.shirt, hand: 'sleeve' } } })`: NEW `hand: 'sleeve'` option (sleeve colour runs to the end of the arm box, no skin band = sleeves swallowing the hands). Bible exception (story says so), like CG's 0.5 character.")
a('grandkid', 'CAST', 'NEW', 'A generic grandkid (world montage)', "cast.js `grandkid`: SKIN.orange, `plainKid` outfit with a red cap (`hat` beanie style, no pompom) and sneakers; used kneeling (s08) and hopping stones (s11).")
a('dad_arms', 'CAST', 'EXISTS', "A grown-up's arms (Dad) lifting a gnome", "`K.makeCharacter('dad')` framed so only the plaid sleeves and hands show (camera above the shoulders), + `gold_outline`.")
a('hero_old', 'CAST', 'EXISTS', 'The narrator at 71', "`K.makeCharacter('heroOld')` (grey hair and moustache, mustard cardigan, olive fishing hat, freckles); faces `content`, `wonder`, `heartfelt`.")
a('hero_old_short', 'CAST', 'NEW', 'The narrator at 71, shorter (mirror of Grandma)', "`K.makeCharacter('heroOld', { scale: 0.85, outfit: { ..., shirt: { ..., hand: 'sleeve' } } })` (same `hand: 'sleeve'` option as `grandma_short`).")
a('granddaughter', 'CAST', 'NEW', "The narrator's granddaughter (about 7)", "cast.js `granddaughter`: SKIN.salmon + freckles (family), dark bob hair, lilac pyjamas with hearts, scale 0.85; faces `sideGlance` (suspicious frown), `content`.")
a('theo_granddaughter', 'CAST', 'NEW', "Theo's granddaughter (newest photo only)", "cast.js `theoGranddaughter`: SKIN.light, blond pigtails, blue whale-print pyjamas, scale 0.75, `wave` pose, face `openSmile`; seen through the window in the last photo.")
a('face_wink', 'CAST', 'NEW', 'Decal face `wink`', "faces.js `wink`: left eye = the ^^ arc (closed), right eye = base oval, smile arc; same line weights as the set.")

# ------------------------------------------------------------------ SETS
a('porch_set', 'SETS', 'EXISTS', 'Grandparents\' porch + swing (approved test)', "part1 `porchScene()` (sets.buildLot + PORCH_HOUSE, `buildSwing`, `spindleRail`, `porchDressing`).", 'part1.js')
a('street_night', 'SETS', 'EXISTS', 'Our street at night (P1)', "`sets.buildStreet(ctx, { seed: 'ep01', lotsPerSide: 6, hero: { side: 'A', index: 3 } })` + `streetGnomes()` (part1) + `sets.nightStreet`.")
a('lawn_closeup', 'SETS', 'EXISTS', 'Our front lawn close-up set (hero lot A1)', "`sets.buildLawnCloseup(ctx, { seed: 'ep01' })`: hero bungalow, bedroom window low over Grandpa's bed (slot `A1.bed0`), family gnome slots, `sets.nightLawn`.")
a('hero_lot', 'SETS', 'NEW', 'Our front garden, EP01 dressing by time and era',
  "sets_ep01.js `heroLot(ctx, { tod: 'night'|'day'|'dusk'|'dawn', era: 'now'|'2010s'|'1960s', truck, sold, keepOff, bed, theoRoom })` wraps `buildLawnCloseup` (same seed, so it is the house of the approved s05/s06) and adds: "
  "the KEEP OFF THE LAWN AFTER DARK post sign beside the gate (`props.postSign`), the agent board on the lawn by the path (`agentBoard`; `sold: t0` slaps the SOLD sticker), "
  "the moving truck at the kerb from 26.61 s (`truck: 'open'|'closed'|'leaving'`), brick edging on Grandpa's flowerbed (the 'bricks' of 61.37 s), "
  "Theo's window = the bedroom window over `A1.bed0` with a real room box behind the glass (`interiors.bedroom`, era-dressed; `theoRoom: { lit, curtains }`), "
  "the family gnomes at `bedFront0, lawn0-3, bedFront1` (as s06; when Grandpa's bed is in frame move `bedFront0` 1.5 studs toward the path so its lantern pool never covers the bed), "
  "`bed` = 'grandpa' | 'empty' (ring of flat pale soil 0.9 stud + two boot dents) | 'plastic' | 'hole' (sunken dark soil 0.8 stud + the $4.99 sticker) | 'grandpaBack'. "
  "Era '2010s': no truck/board, younger bush, the hero's toys on the porch; '1960s': no sign, a picket gate in a different colour (B&W anyway), a smaller tree.")
a('hero_room', 'SETS', 'NEW', 'The old bedroom (hero 11 -> Theo now; 1960s and 1990s/2010s dressings)',
  "interiors.js `bedroom(ctx, { era: 'hero11'|'theo'|'hero5'|'dad60s'|'cousin90s', lit })`: the TF bedroom kit (bible 4.4): fabric wallpaper (era colour: hero/Theo #4958a0 blue, 1960s rose stripe, 1990s yellow floral), lavender ceiling with glow stars, glossy terracotta planks, thick white window frame (the window over Grandpa's bed: sill 1.6 studs above the lawn outside), "
  "era beds (hero11: carved headboard + magenta duvet; theo: a bare mattress on the floor + boxes THEO + a star nightlight projector; hero5: small bed with rocket duvet; dad60s: iron bed; cousin90s: bunk), posters (our own designs), shelf with books and a toy car. "
  "Built as a box 14 x 12 x 13 studs that attaches behind the hero bungalow's window, so the same room is seen from inside (s17, s44, s55, s66, s67, s71, s72) and through the glass from outside (s27, s45, s46, s68, s69, s70).")
a('grandma_room', 'SETS', 'NEW', "Grandma's living room (day)",
  "interiors.js `grandmaRoom(ctx)`: rose wingback armchair (seat top 1.5 studs, high back, rolled arms), shag rug, standard lamp (cream drum shade, emissive), side table with the teacup + knitting basket (part1 `porchDressing` pieces), "
  "window with net curtains and daylight behind (emissive sky card), framed photos and a cuckoo clock on floral wallpaper (`tex.plaster` + painted pattern), skirting, terracotta planks. 5-15 props in every framing (bible 4.1).")
a('hall', 'SETS', 'NEW', 'Our hall at night (the night of the move)',
  "interiors.js `hall(ctx)`: narrow hall 8 studs wide, the front door (dark red, a 4-pane glass panel at head height showing the night garden), the wall clock (orange rim #9c3703, lavender face, Roman numerals; hands at 8:59:59 -> 9:00 on \"nine\"), "
  "the hero's rolled-up sleeping bag on a mat by the door, three boxes taped and marked THEO (bold sans black on kraft), coat hooks with a mustard hoodie, a runner rug; packed-house feel (bare picture hooks).")
a('next_door', 'SETS', 'NEW', "Next door's lawn (lot A2)",
  "sets_ep01.js `nextDoor(ctx, { tod, dog, hole })`: lot A2 of the street (EXISTS via `buildLot`) dressed with 3 plastic gnomes in a row facing the street, the red kennel 'REX' (`props.kennel`, EXISTS), a hose reel (EXISTS), a red lead (tube along a Catmull curve) from the kennel ring across the lawn into "
  "THE HOLE: a neat round hole 0.9 stud across (an inverted cylinder 2 studs deep, black-brown interior #120a06, a lip of crumbs). Night version: lanterns are black plastic and never light.")
a('agent_board', 'SETS', 'EXTEND', 'Estate-agent board + SOLD sticker', "`props.prop('agentBoard', { header: 'FOR SALE', lines: ['3 BED · BIG GARDEN', 'COMES WITH ANCESTORS'] })` (EXISTS) + NEW `soldSticker`: a red rounded rectangle 'SOLD' decal that slaps on diagonally (scale 1.3 -> 1 in 4 frames, outBack) on \"moved\".")
a('keep_off_sign', 'SETS', 'EXISTS', 'KEEP OFF THE LAWN AFTER DARK sign', "`props.prop('postSign', { lines: ['KEEP OFF', 'THE LAWN', 'AFTER DARK'] })`: by our gate (hero lot) and on the dusk street corner (s11).")
a('dusk_street', 'SETS', 'EXTEND', 'A street at sunset with curtains', "`sets.buildStreet` + `sets.dusk` (EXISTS) + NEW curtain planes per lit window (`curtainCascade`, fx).")
a('dawn_lawn', 'SETS', 'EXISTS', "A neighbour's front lawn at dawn (Grandma's)", "`sets.buildLot(ctx, { seed: 'ep01-gm' })` + `sets.dawn`; dew via sparkles.")
a('gate_lot', 'SETS', 'EXISTS', 'A neighbour\'s front gate at night', "Lot A3 of `sets.buildStreet` (gate leaf `gate_A3`, hinged), `sets.nightLawn`; + `fx_property_line`.")
a('moving_truck', 'SETS', 'EXTEND', 'The moving truck (kerb, open back, leaving)',
  "`props.prop('movingTruck', { boxes: ['BALCONY GNOME', 'THEO', 'KITCHEN', ''] })` (EXISTS: 24 x 9 x 10 box, open back, ramp) + NEW: a cargo dome light (emissive + 1.5 cd point), the BALCONY GNOME box on top of the stack facing the house, "
  "a roller rear door (up), a `leaving` mode (truck root moves along the road at 0 -> 6 studs/s, wheels spin) and a rear POV rig (camera inside the cargo bay looking out, box edges framing).")
a('truck_cab', 'SETS', 'NEW', 'Truck cab insert (dashboard clock)', "interiors.js `truckCab(ctx)`: dashboard (dark plastic), a red 7-segment LED clock '11:52' (colon blinks 1 Hz), a steering wheel with a yellow sticky note 'LEAVE 6 AM' (marker font, bold), windscreen showing the night street (P1, darker than the cab).")
a('aerial_street', 'SETS', 'EXISTS', 'Our street from high above', "`sets.buildStreet` view `views.streetHigh`, all lots, + `fx_lantern_ring` per lit gnome.")
a('back_garden', 'SETS', 'NEW', "The daughter's back garden (epilogue, dusk -> night)",
  "sets_ep01.js `backGarden(ctx, { tod: 'dusk'|'blueHour' })`: the back of a two-storey house (siding, `addHouse` back wall) with the granddaughter's ground-floor bedroom window lit (pink-warm, curtains open, a nightlight), "
  "a garden bench (wood slats), the striped deck chair facing the window (`props.deckChair`, EXISTS), lawn with dandelion clocks (`props.dandelion`, EXISTS), a low fence and pines behind, the TF moon rising for the last shot.")
a('phone', 'SETS', 'NEW', 'Phone in an old hand', "sets_ep01.js `phone(ctx, { photos })`: a modern phone 1.0 x 2.0 studs (rounded box, black bezel), screen = emissive plane (x1.2) showing a photo texture; `swipe(t, [t0...])` slides the next photo in from the right in 8 frames (outCubic). Held by `hero_old`'s hand socket.")
a('polaroids', 'SETS', 'NEW', 'Yearly photo series (Polaroids across 60 years)',
  "sets_ep01.js `photoSeries(ctx, years)`: each photo is rendered ONCE per worker into a 512x512 texture (`photoTexture(ctx, year)`: a small scene = hero lot in spring daylight, Grandpa gnome `age` = year/60, Theo `theoAt(6 + year)`, tulip colours and window curtains changing per year, "
  "rendered with the `day` grade + `fx_photo_look`), then mounted on a Polaroid card 3.5 x 4.2 studs (white border, thick bottom margin with the year hand-written: '1st spring', '10', '25', '40', '60'). "
  "Used as a falling stack (s90), on the phone (s91-s93) and full frame (s93). Years: 1, 5, 10, 16, 25, 33, 40, 52, 60.")
a('garden_table', 'SETS', 'NEW', 'A wooden garden table at dusk (Polaroid pile)', "sets_ep01.js: slatted teak table top 8 x 5 studs (`tex.woodPlanks`, roughness 0.5) in the back garden, a mug and reading glasses beside the pile.")

# ------------------------------------------------------------------ EFFECTS
a('fx_sparkles', 'FX', 'EXISTS', 'TF sparkle glints', "`sets.sparkles(ctx, { ...SPARK, center, size, count })` with the approved `SPARK` look (sharpness 7, core 0.75, underlay 0.55 @ 0.5, brightness 2.0, 55-95 px) from part1; outdoors 6-12, interiors and magic 8-20; none in day shots.")
a('fx_magic_dust', 'FX', 'EXISTS', 'Gold / pink motes', "`sets.magicDust(ctx, { center, radius, height, count })`.")
a('fx_burst', 'FX', 'EXISTS', 'VFX burst (TF)', "`sets.burst(ctx, { pos, t0, dur: 0.35, count, ringPx, corePx })` + part1 `streaks()` / `poofCloud()` (promote both to fx_ep01.js).")
a('fx_star_glint', 'FX', 'EXISTS', 'One big 4-point star glint', "part1 `starGlint(ctx, { pos, t0, peak, rot })` (promote to fx_ep01.js).")
a('fx_grade_blend', 'FX', 'EXISTS', 'In-shot grade switch over 6-10 frames', "part1 `gradeBlend(A, B)` + the s04 update block (promote to fx_ep01.js as `inShotGrade(ctx, fromPreset, toPreset, t0, frames, amount)`).")
a('fx_contact', 'FX', 'EXISTS', 'Contact shadows, light pools, halos', "`sets.contactShadow`, `sets.lightPool`, `sets.glow`.")
a('fx_property_line', 'FX', 'NEW', 'Property-line shimmer + bonk ripple',
  "fx_ep01.js `propertyLine(ctx, { a, b, height: 2.6 })`: a vertical additive curtain along the lot boundary at the gate (shader: faint lavender-gold vertical streaks drifting up 0.3 studs/s, opacity 0.06 idle, fades out at the top) + a gold line on the path. "
  "`bonk(t0, at)`: concentric ripple rings on the curtain from the contact point (3 rings, 0.45 s, radius 0 -> 2 studs, opacity 0.6 -> 0) + `fx_burst` small (12 sparkles); `part(t0, at)` (family carries it out): the curtain parts in a gold flash with 10 gold sparkles, no ripple.")
a('fx_gold_outline', 'FX', 'NEW', '"Only family" gold outline', "fx_ep01.js `goldOutline(obj, { color: '#ffd27a', scale: 1.03, opacity })`: inverted hull (BackSide clones, additive) on the given meshes (hands/arms + the gnome), opacity animated 0 -> 0.9 -> 0.5; + 6-10 gold sparkles. Two uses: s15 (Dad's hands) and s32-s33 (the hero's arms).")
a('fx_tear', 'FX', 'NEW', "The gnome's dewdrop tear", "fx_ep01.js `dewTear(ctx, gnome, { eye: 'L', t0, dur: 0.6 })`: a glossy water drop (MeshPhysical transmission-free: roughness 0.05, clearcoat 1, env-lit, a 6 px catchlight sprite) that swells at the lower lid for 0.15 s then slides down the cheek and beard (path in head-local coordinates).")
a('fx_beam', 'FX', 'NEW', 'Flashlight beam', "fx_ep01.js `flashlightBeam(ctx, { socket, length: 9 studs, angle: 14 deg })`: an additive cone (radial gradient along the axis, soft edges, opacity 0.18) + a ground spot (`lightPool` ellipse) + a spot light 4 cd #fff1d0, no shadow; `on(t0)` switches in 1 frame.")
a('fx_lantern_ring', 'FX', 'NEW', 'Lantern ring of light (the moles stop at its edge)',
  "fx_ep01.js `lanternRing(ctx, { center|follow, radius: 5 studs })`: an additive ground disc with a flat warm interior (#ffcf8a at 0.22), a bright crisp rim 0.25 stud wide (#ffe2a8 at 0.55) and a 0.6-stud soft falloff outside; it follows the lantern's ground point (slides with the hero). "
  "`edgeOf(pos)` returns the rim point toward pos (moles call `stopAt` there). Grandpa's ring radius 5 studs; family/street gnomes 2 studs.")
a('fx_lantern_cascade', 'FX', 'NEW', 'Every lantern lit (street cascade)', "fx_ep01.js `lanternCascade(ctx, gnomes, { t0, order: 'toward camera', gap: [0.15, 0.3], skip: ['A2'] })`: calls `K.lanternLightUp` per gnome at its own t0 (seeded gaps), adds its ring (radius 2) and a tink cue time list for the mix. Next door (A2) skipped.")
a('fx_curtains', 'FX', 'NEW', 'Curtains snap shut down the street', "fx_ep01.js `curtainCascade(set, { t0, gap: 0.12, n: 6 })`: per lit window two fabric planes (`tex.fabric`, wine #7a2a3a) slide shut in 4 frames (outQuad) and the window emissive drops to x0.6 behind them.")
a('fx_window_dark', 'FX', 'NEW', "Theo's window goes dark (what-if)", "fx_ep01.js `windowState(win, level)` on the hero lot's Theo window: emissive and the room's nightlight to 0 in 1 frame on \"dark\" (light-state event), restored in later shots.")
a('fx_soil', 'FX', 'NEW', 'Soil crumbs / dust puff', "fx_ep01.js `soilBurst(ctx, { pos, t0, count: 24, spread })`: instanced brown lumps (0.05-0.12 stud) thrown up on parabolas (0.4 s) + 3 soft dust puff sprites (#6a5040, opacity 0.5). Mound tops, the GULP seal, the lawn moving.")
a('fx_sticker', 'FX', 'NEW', 'Price sticker flutter', "fx_ep01.js `flutter(ctx, { tex: '$4.99', from, to, t0, dur: 0.4 })`: a 0.5-stud paper quad falling with a side-to-side swing (+-35 deg) and landing flat on the soil.")
a('fx_glass_fog', 'FX', 'NEW', 'Breath fog on the window glass', "fx_ep01.js `glassFog(ctx, pane, { t0, center, r1: 0.9 stud })`: an animated alpha mask (soft noisy disc, grows over 0.35 s, opacity 0.55, #dfe4ff) on the pane, lit by the amber eyes behind it.")
a('fx_fwoom', 'FX', 'EXTEND', 'FWOOM: lantern flare + light rolling across the lawn',
  "`sets.magicGlow(ctx, { source })` + `rig.fwoom(t0)` (EXISTS: lantern 8 -> 50 cd in 0.15 s, -> 10 over 1.5 s) + `K.setLantern(g, 4..6)` + `fx_burst` + part1 `streaks` + `fx_grade_blend` to `magic` in 8 frames, plus NEW fx_ep01.js "
  "`lightWave(ctx, { center, speed: 8 studs/s, height: 1.0, width: 1.4 })`: a thick additive ring wall rolling outward over the grass (gold #ffd38a core, pink #ff9ad5 trailing edge, sparkles kicked up at the front), radius = speed * (t - t0); moles inside the radius `sink` (staggered, 0.5 s each) and their eyes wink out pair by pair (`setMoleEyes` 0 in 2 frames, 0.2-0.3 s apart, a blip cue each).")
a('fx_photo_look', 'FX', 'NEW', 'Photo print look', "fx_ep01.js `photoLook(tex)`: for photo textures: lifted blacks (#2a2420), warm cast +8, saturation 0.85, a soft inner vignette inside the print only, a 1-px paper grain; Polaroid frame card. Never on the episode frame itself (bible: clean image).")
a('fx_dew', 'FX', 'EXISTS', 'Dew sparkles (dawn)', "`sets.sparkles` with warm colours ['#ffe2c4', '#fff4e0'], px 30-50, count 4-6, drift low (bible dawn: 0-6 warm motes).")
a('fx_dandelion', 'FX', 'EXISTS', 'Dandelion seed clock', "`props.prop('dandelion', { puff: true })` + `sets.burst(ctx, { puff: 14, count: 0 })` seeds drifting 0.3 studs/s in the last shot.")
a('fx_shake', 'FX', 'EXISTS', 'Camera shake', "`ctx.camera.shake({ t0, dur: 0.5, px, freq: 14 })`.")

# ------------------------------------------------------------------ SOUND (cue names; the mix stage maps them to library files)
SFX = [
 ('A_NIGHT', 'bed', 'Crickets, suburban night, no traffic (HPF 250 Hz), the test\'s A1', 'all night exteriors; dropped to near-silence under "empty" (28.87-29.74)'),
 ('A_ROOM', 'bed', 'Interior room tone, soft clock tick far away', 'interiors (s06-s07, s17, s26, s44, s55, s66-s67, s71-s72)'),
 ('A_DAY', 'bed', 'Day suburb: birds, distant mower', 's10, s12-s13, s16'),
 ('A_DUSK', 'bed', 'Evening birds settling', 's11, s25, s90-s96'),
 ('A_DAWN', 'bed', 'Dawn chorus, light', 's08, s82-s89'),
 ('MUSIC', 'bed', 'The owner\'s music bed, about 8 LU under the voice; drops out for the 4 planned pauses', 'whole episode'),
 ('W1', 'hit', 'Airy whoosh (test)', 's01'),
 ('M1', 'hit', 'Music-box / chime shimmer (test; swap the Christmas sparkle per review defect 20)', 's04-s05'),
 ('P1', 'hit', 'Cartoon pop (test)', 's04'),
 ('T_GLINT', 'hit', 'Tiny glass ting', 's08 (glasses)'),
 ('TOK', 'hit', 'Ceramic tap', 's16'),
 ('SQUEAK', 'hit', 'Squeaky toy bite', 's12'),
 ('CHAIN_TUG', 'hit', 'Dog lead clink + single tug', 's13'),
 ('HOPS', 'hit', 'Tiny ceramic hop clicks', 's14'),
 ('BONK', 'hit', 'Hollow ceramic bonk + glassy ripple "wom"', 's14'),
 ('LATCH', 'hit', 'Gate latch click', 's15'),
 ('SHIMMER_S', 'hit', 'Soft gold shimmer', 's15, s32'),
 ('TIK', 'hit', 'Ceramic blink "tik"', 's18, s86'),
 ('TIK_SLOW', 'hit', 'Slower, lower "tik"', 's75'),
 ('CLICK_TORCH', 'hit', 'Flashlight click', 's20, s61'),
 ('STEP_WET', 'hit', 'Slipper on wet grass', 's21, s62'),
 ('SLAP_STICKER', 'hit', 'Sticker slap (paper thwack)', 's25'),
 ('TICK_CLOCK', 'hit', 'One loud clock tick', 's26'),
 ('DOOR_BANG', 'hit', 'Front door bangs open', 's28'),
 ('FEET_WET', 'hit', 'Bare feet running on wet grass', 's28, s56'),
 ('CLINK', 'hit', 'Ceramic clink', 's32'),
 ('CREAK_LANTERN', 'hit', 'Small lantern handle creak', 's33'),
 ('SUBBOOM', 'hit', 'Whoosh + sub-boom + low rumble (the reveal hit) to about 39.5 s', 's34-s35'),
 ('CRUMBLE', 'hit', 'Soil crumbling', 's35, s51'),
 ('PLINK', 'hit', 'Reflector glint plink', 's36'),
 ('SNIFF', 'hit', 'Wet sniff + wriggle', 's37, s53'),
 ('TINK_WHOOSH', 'hit', 'Lantern tink-whoosh (light-up)', 's38'),
 ('FIP', 'hit', 'Snout recoil squeaks x3', 's39'),
 ('TINKS', 'hit', 'Cascade of tinks 0.15-0.3 s apart', 's40'),
 ('CLATTER', 'hit', 'Plastic clatter into a hole', 's41'),
 ('THUD_LOW', 'hit', 'Low soft thud (window goes dark)', 's46'),
 ('RIP', 'hit', 'Cardboard tape rip', 's49'),
 ('THUNK_PLASTIC', 'hit', 'Plastic gnome into soil', 's50'),
 ('GULP', 'hit', 'GULP', 's51'),
 ('FLUTTER', 'hit', 'Paper flutter', 's51'),
 ('RUMBLE_ROLL', 'hit', 'Rolling rumble', 's52'),
 ('BRICK', 'hit', 'Brick clunk', 's54'),
 ('BREATH', 'hit', 'Breath on glass', 's55'),
 ('TIDE', 'hit', 'Turf receding whoosh', 's56'),
 ('GRIND', 'hit', 'Stony grind / creak', 's59, s89 (soft)'),
 ('KNEEL', 'hit', 'Knees in soil', 's73'),
 ('SET_DOWN', 'hit', 'Ceramic set down on soil', 's76'),
 ('FWOOM', 'hit', 'Whoosh + warm shimmer 1.5-2 s (the light-up hit)', 's77-s78'),
 ('PASS', 'hit', 'Light-wave pass-by whoosh', 's78'),
 ('DEFLATE', 'hit', 'Soft deflating thumps 0.15 s apart', 's79'),
 ('BLIPS', 'hit', 'Tiny pitched blip per eye pair (5)', 's80'),
 ('DOOR_CREAK', 'hit', 'Front door opening, morning', 's82'),
 ('ENGINE', 'hit', 'Truck engine starts, idles, drives off', 's87-s89'),
 ('RATTLE', 'hit', 'Boxes rattling in the truck', 's88'),
 ('DROPS', 'hit', 'Polaroids dropping on wood', 's90'),
 ('PING', 'hit', 'Phone message ping', 's91'),
 ('SWIPE', 'hit', 'Phone swipe', 's92'),
 ('POOF_SOFT', 'hit', 'Dandelion poof, soft', 's97'),
]
PRIMARY_SFX = {'W1', 'M1', 'P1', 'BONK', 'LATCH', 'TIK', 'CLICK_TORCH', 'DOOR_BANG', 'CLINK', 'SUBBOOM', 'SNIFF', 'TINK_WHOOSH', 'TINKS', 'GULP', 'GRIND', 'TIK_SLOW', 'FWOOM', 'DEFLATE', 'BLIPS', 'ENGINE', 'POOF_SOFT', 'SLAP_STICKER'}
