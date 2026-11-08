# VISUAL BIBLE: the look of our Roblox "In this world..." shorts

This is the single spec the builders follow to reproduce the reference look in Three.js (engine: `engine/`, r170, rendered on
SwiftShader at 1080x1920, 60 fps). It merges the four reference analyses and the metrics pass:

| Code | Reference | Source analysis | Role for us |
|---|---|---|---|
| **TF** | The Tooth Fairies Project (131.5 s) | `analysis/visual_tooth_fairies.md` | **Master look** (the owner's favourite): grade, sparkles, pacing, camera, faces |
| AW | Never Be Caught Awake At Night (174.3 s) | `analysis/visual_awake_at_night.md` | Night suburb kit, monster sculpt, punch-ins, sleepwalk/run/reach acting, sepia flashback |
| PN | Porch Night (166.8 s) | `analysis/visual_porch_night.md` | Street/porch/lamp kit, walk and run cycles, dusk and blue-hour skies, lamp pools, light cascades |
| CG | Clown Gate (127.7 s) | `analysis/visual_clown_gate.md` | Primitive-built hero prop, gesture timings, fog, optional "act 3" editor kit |
| M | Cross-video numbers | `analysis/visual_metrics.md` | Targets for QA |

How to read it:
- **MUST** = measured in the references (keep it). **CHOSEN** = our decision where the references are silent, contradict each other, or show a cheap tell we fix.
- Sizes are in **studs**; the engine works in metres with **`STUD = 0.32` m** (as in `engine/episodes/_demo.js`). The look-dev kit
  (`lookdev/js/*.js`) builds in studs (1 unit = 1 stud): wrap those assets in a group scaled by 0.32.
- Pixels are output pixels of the 1080x1920 frame. Colours are display-space sRGB hex, **measured after the reference grade**, unless the
  row says "albedo".
- Evidence frames are in scratch (copyrighted, never in the repo): `$TFV=.../scratchpad/rbx/tfv`, `$AW=.../scratchpad/rbx/work/vis_awake`,
  `$PNV=.../scratchpad/rbx/pnv`, `$CGV=.../scratchpad/rbx/cgv` (full root: `/tmp/claude-0/-home-user-claude-todo-demo/353ac1d9-152b-55bb-bdf1-0625e0fc6a83/scratchpad/rbx`).
  Look at the frames named in each section before you build that part.
- The storyboard method (how narration becomes shots) is in `docs/STORYBOARD_RULES.md`.

---

## 1. The look in one paragraph, and the 12 rules

**The look.** A Roblox Studio screen capture: blocky **R6 avatars** (six rigid boxes, a rounded drum head, flat 2D decal faces,
2D painted clothing, one chunky accessory) standing in **dense, studless, textured Roblox-material sets** (fabric wallpaper, glossy
wood, brick, grass), next to **one hero creature that is a sculpted, glossy, far more detailed model**; that contrast is the
production value. Every location carries **one monochrome tint**: whites land on lavender (#e7d4fc), peach (#fde3c7) or periwinkle
(#bdbffc), never on #ffffff; highlights roll off softly (p99 luma 210-230); interior shadows go maroon, never grey; night skies are a
black or deep-violet void. Night is shown as **coloured light, not darkness**. The image is **clean**: no depth of field, vignette,
grain, chromatic aberration, motion blur or lens distortion; the only "magic" is soft local glows and **drifting 6-to-8-point sparkle
glints**. The camera **never stops**: every shot is a linear, centred push-in of about +19%, with a fast crane, whip or pull-back
about once every six shots. **Hard cuts only**, about one per 1.1-1.2 s, landing one frame before the word that names the new picture;
one picture per noun. Characters mostly hold still in readable poses while the camera and sparkles carry the motion; faces change by
instant decal swaps on the beat word.

**The 12 must-match rules, ranked by impact on "does it look like the references"**

| # | Rule | Numbers (MUST unless marked) | Engine |
|---|---|---|---|
| 1 | **Word-locked hard cuts, one picture per noun** | Cut at the naming word's onset minus 1 frame (TF median -7 ms). 95% of sentences open on a new shot. 45-52 cuts/min, median shot 1.1-1.2 s, p90 2.0 s, max 2.3 s. Hard cuts only. | Timeline JSON from VO word times (`docs/STORYBOARD_RULES.md`) |
| 2 | **The camera never stops** | 94-99% of shots push in; linear in image scale, no easing, median +19% per shot (p10 +10%, p90 +30%), independent of shot length; cut mid-move. ~1 shot in 6 is a fast move (1000-8000 px/s); the opening shot is always one. | `ctx.camera.push(Z)` + accents (§7) |
| 3 | **One monochrome grade per location** | Whites tinted (never #fff), p99 luma 210-230, luma clip ≤ 0.3%, saturation 0.45-0.6; interiors: lifted maroon blacks (p1 5-20); night exteriors: black or violet void sky. Grade switches on story beats. | `post.grade` presets (§6), QA with `lookdev/tools/stats.py` |
| 4 | **R6 avatars, exactly** | 6 rigid parts, head 1.2, torso 2x2x1, limbs 1x2x1, 5.2 studs = 4.3 heads; no elbows, no knees; kids and adults the same size. | §2.1 |
| 5 | **One hero creature that out-details everyone** | Sculpted, smooth, glossy or clay; huge glossy eyes or hollow sockets; cute silhouette, creepy details; shot from below. | §2.6 |
| 6 | **Decal faces, swapped on the word** | Black-line cartoon faces on the head's front band; swaps are instant (1 frame) on the beat word or on the cut; no lip-sync, no human blinks. | §2.5 |
| 7 | **Dense, readable, textured sets** | No studs, no flat untextured parts; 5-15 props per frame; a recognisable prop behind every close-up; childhood iconography. | §4, `ctx.tex.*` |
| 8 | **Clean image** | No DOF, vignette, grain, CA, motion blur, lens distortion, overlays. Global bloom ≤ 0.15; glows are local sprites. | §6 base preset |
| 9 | **Magic air** | 8-20 soft 6-to-8-point white-lavender glints (40-80 px) drifting in night and magic shots; pink/gold dust around magic sources; 0.3-0.4 s VFX bursts to sell snaps. | §6.3 |
| 10 | **Soft, coloured, low-contrast light** | Strong coloured hemisphere ambient, one soft key from upper front-left, no hard shadows indoors, emissive practicals with small halos; subject is the brightest thing in a night frame. | §5 |
| 11 | **Pose-to-pose humans, smooth creatures** | Humans hold poses and snap between them (8-16 frames, or 1 frame under a VFX burst or a cut); creatures move smoothly (bob ~1 Hz, flutter 3-5 Hz). About half the shots have a near-still subject. | §3 |
| 12 | **True 60 fps, clean frames, sharper than the reference** | The references are 40-48 unique fps with judder and about 540-720p real detail. We render every frame; `quality=fast` (scene at 810x1440) already exceeds the reference detail. | `tools/render.js` |

Cheap tells in the references that we do **not** copy (CHOSEN): 40-fps judder, stray 2-frame clips, accidental inserts, props
teleporting in view, window views brighter than the night room, caption ASR errors, a backdrop plane visible in shot, an unexplained
lighting pop, a name split across a cut.

---

## 2. Character construction kit

Look first at: `$TFV/s/kidfaces.jpg`, `$TFV/s/scale.jpg`, `$AW/grid_max.jpg`, `$PNV/s/v_family1.jpg`, `$PNV/s/v_faces1.jpg`,
`$CGV/m/v_kid_dad.jpg`, `$CGV/m/measure35.jpg`.

### 2.1 R6 avatar (all humans)

Measured: AW head 1.2 x 1.23 studs on a 2-stud torso; PN head : torso : legs = 0.5 : 1 : 1.1; CG 0.54 : 1 : 1. All are the standard R6
body, about 4.3-4.7 head-heights tall.

| Part | Size (studs, W x H x D) | Shape | Position (feet at y = 0) | Pivot / motion |
|---|---|---|---|---|
| Torso | 2 x 2 x 1 | Box, edge bevel 0.05-0.06 (`RoundedBoxGeometry(…, 3, 0.06*STUD)`), flat faces | centre y = 3.0 | Root of the rig; rotates only as a whole body |
| Head | 1.2 x 1.2 x 1.2 | **Classic Roblox head: an upright drum** = `LatheGeometry` of the profile (0,-0.6) → (0.35,-0.6) → quarter arc → (0.6,-0.35) → (0.6,0.35) → quarter arc → (0.35,0.6) → (0,0.6); fillet radius 0.25, 32+ radial segments. Never a box, never a sphere | centre y = 4.6 (sits on the torso top) | Neck yaw ±45°, pitch ±25° (rarely used) |
| Arm L/R | 1 x 2 x 1 | Box, bevel 0.05; the hand is just the box end | centre (±1.5, 3.0) | Swing axis = horizontal X axis at **y = 3.5** (0.5 below the shoulder top, Roblox `Right Shoulder` C0 (1, 0.5, 0)) |
| Leg L/R | 1 x 2 x 1 | Box, bevel 0.05; feet are the box end (pants texture may draw shoes) | centre (±0.5, 1.0) | Swing axis = X axis at **y = 2.0** (hip) |

- Total height 5.2 studs (1.66 m); eye line about y = 4.65; shoulder top 4.0; hip 2.0.
- **All humans share this size** (MUST: TF, PN, CG). CHOSEN for EP01: Theo (6) may use x0.85 and the hero aged 5 in the flashback x0.75;
  never shrink anyone else. CG scaled one character to 0.5 only because the story said so.
- Small visible gaps or overlaps at the shoulder during a swing are part of the R6 look; do not hide them.

### 2.2 Materials and colours (humans)

| Element | Material | Values |
|---|---|---|
| Skin, plastic parts | `MeshStandardMaterial`, "SmoothPlastic" | roughness 0.5-0.55, metalness 0, no texture or a 2% noise |
| Clothing | `MeshStandardMaterial` with a painted `CanvasTexture` | roughness 0.6-0.7; knit/fabric looks may add a weak `bumpMap` (scale 0.02) |
| Hair, hats, hoods (UGC) | `MeshStandardMaterial` | roughness 0.4-0.55 (a soft sheen), metalness 0, smooth normals on low-poly forms |
| Glasses, buttons | Standard | roughness 0.3 |

Skin albedos seen (they shift strongly with the grade): TF kid salmon (base about #e8a07a; graded #bd5f5b cool, #efab74 warm), CG kid
orange #f49134, AW Max #e96e57, PN family light orange #ebc284, classic pale #e8e8e8 for some townspeople. Shirts are saturated flat
colours (TF #093403 dark green, CG #2d8a05).

### 2.3 Clothing method (MUST: 2D, not 3D)

- Clothing is a **2D shirt / pants texture wrapped on the boxes**: no 3D layered clothing on humans. The shirt covers the torso and both
  arms; the pants cover both legs (and may draw shoes at the bottom 0.25-0.3 stud, AW). Seams at the shoulder are visible.
- Draw at about 128 px per stud: torso front/back 256x256, torso sides 128x256, arm and leg faces 128x256. One canvas atlas per outfit
  with box UVs (see `boxUV` in `lookdev/js/lib.js`).
- Paint in the Roblox-shirt manner: a flat base colour, the pattern (stripes about 10 per torso, buffalo plaid, cable knit, cardigan
  placket, suspenders, ties, buttons), then **baked shading**: a collar shadow, armpit darkening, soft diagonal fold strokes (alpha
  0.15-0.25), a 10-15% darker gradient toward the hem, and a lighter cuff band. Short sleeves end on a skin-coloured band.
- Patterns continue across the arms (PN bee stripes). Knit and burlap textures read as 3D fabric (CG, AW): use fine noise rows plus a
  bump map.

### 2.4 Accessories (UGC meshes)

- One chunky, smooth-shaded accessory per character, readable as a silhouette from behind and at 30 px tall (the **identity marker**:
  TF/CG three-eyed alien hood, PN spiky yellow hair + bee stripes, AW messy orange hair).
- Hair: merged clumps (teardrop `clumpGeo` in `lookdev/js/chars.js`), covering the top half of the head and sometimes the brows; low
  poly with smooth normals; a slight sheen. Hats: lathe or squashed spheres plus a brim. Hoods: a sphere shell plus extruded side flaps,
  sphere eyes (sclera lilac-white, black pupils), cone ears, a stalk-and-ball antenna.
- Accessories are rigid: no secondary motion.
- CHOSEN (EP01): the hero's marker is the mustard hoodie plus messy brown hair (script build sheet). Make the hoodie strongly saturated
  (albedo #d9a52c) and give the hair one big, asymmetric spiky silhouette, so he reads from behind at 30 px; if he does not, add a hood.

### 2.5 The face system

**Construction.** The face is a transparent `CanvasTexture` (512x512) on a thin band that hugs the head: a copy of the head lathe
covering the front 140°, scaled x1.004, `polygonOffset` -2, `depthWrite:false`. A flat plane (as in the demo) shows its edge in 3/4
views; do not use it. Canvas origin top-left, x = 256 is the face centre; y = 0 is the head top, y = 512 the bottom. Lines are black
#141414 with round caps; red mouth interiors #d01818; teeth #f1ecff; tongue #e2405a.

**Base layout (neutral smile)**: eyes = filled ovals centred at (196, 240) and (316, 240), radii 20 x 36; mouth = arc centred (256, 300),
radius 70, from 35° to 145° (the lower arc), stroke 11. Every other face moves only these parts.

| # | Name | Drawing (canvas coordinates) | Used for |
|---|---|---|---|
| 1 | neutral smile | base layout | default, establishing |
| 2 | o-wonder | base eyes; brows = short up-curved arcs at y 175 over each eye, stroke 8; mouth = small filled black ellipse (256, 345) r 9 x 12 | listening, "huh" (TF #1, #12) |
| 3 | red-o shock | eyes r 22 x 40; brows high at y 165; mouth = black-outlined ellipse (256, 350) r 18 x 24, stroke 6, filled red | surprise (TF 42.8 s) |
| 4 | grin with teeth | mouth = D shape: flat top from x 190 to 322 at y 305, curved bottom to y 385, outline 8, filled #f1ecff with vertical tooth lines every 22 px | delight, pride (TF 22.2 s) |
| 5 | open smile | same D shape filled black, red tongue across the lower half | laughing, excited |
| 6 | ^^ content | eyes = upward arcs (∩) 56 px wide at y 250, stroke 10; smile arc | content, cosy (TF 33.4 s) |
| 7 | angry | base eyes; brows = straight bars from (160, 188) to (222, 214) and mirrored, stroke 12; mouth flat bar 226-286 at y 345, or a small o | determined, cross (TF 35.8 s) |
| 8 | sad / worried | brows rising toward the centre: (166, 214) → (222, 188) and mirrored; mouth = frown arc centred (256, 385) r 45, 200°-340° | worry, guilt (TF 64.4 s) |
| 9 | heartfelt | eyes = lilac irises #c9b3ff with black pupils under a thick upper-lid line (stroke 10) with 3 short lashes; gentle smile arc | tender beats (TF 101.35 s) |
| 10 | sleeping | eyes = downward arcs (∪) 50 px wide with two short lashes; tiny smile or small o | asleep (TF 17.8 s) |
| 11 | side-glance | ovals shifted 18 px sideways with a flat upper-lid line cutting their top third; small flat mouth offset to the same side | thinking, suspicion (TF 84.8 s) |
| 12 | horrified scream | white ovals with black outline and tiny pupils, crazed brows; huge open oval mouth, top teeth row, red tongue | terror (AW 122.7, CG #96) |
| 13 | >< sob | eyes = ">" and "<" chevrons, stroke 12; open red trapezoid mouth; 2 light-blue sweat drops #8fd0ff at the temple | crying, panic (PN #67) |
| 14 | wet eyes (CHOSEN, EP01 line 45) | base or heartfelt eyes plus a white catchlight and a light-blue tear bead at the lower lid | holding back tears |
| 15 | smirk (AW) | one raised brow, one half-lidded eye, side smile | cheek, mischief |

Overlays: stubble (PN Dad), freckles (EP01 hero: 6-8 dots #b8573c at 40% opacity across the cheeks at y 285), moustache in the decal (CG
Dad). Keep line weights identical across the set so swaps never "jump" in style.

**Behaviour (MUST):**
- Swap instantly (1 frame, no tween) on the onset of the beat word, or on the cut. Examples: TF grin → open smile at 22.40 s on "baby"
  (+0.08 s); AW eyes snap open at 37.80 s on "Tink" (37.79). At most 2 swaps per shot, each held at least 0.4 s.
- One face per shot is the norm; change it when the narration turns.
- **No lip-sync**. When a character speaks in-scene, either hold a speaking face, or flap 2 mouth decals (open/closed) every 0.25-0.3 s
  for the line only (AW mom singing).
- **No human blinks** (CHOSEN, consistent with all four references): in EP01 the gnome's blink is a plot device, so it must be the only
  blink on screen.
- Snap actions whose pose change would look cheap (tooth pull, arm flick) are hidden under a VFX burst on the same frame (TF 36.28 s).

### 2.6 Creature design rules

The creature is where the references spend their detail budget (TF: "the strongest single factor"; PN: "the only premium model").

1. **Contrast**: high-poly, smooth, sculpted, textured, against blocky flat humans. Never build the creature from R6 boxes (CG's clown is
   the one exception: a primitive-built statue, still more detailed and better textured than the humans).
2. **Cute silhouette, creepy details**: chubby or doll-like proportions, pastel or circus palette, tutus or small hands; then creepy eyes
   (huge glossy bulging eyes with coloured irises, or hollow black sockets), crooked or buck teeth, cracks, stains, a fixed open mouth.
3. **Eyes**: 25-35% of head width each; sclera sphere with clearcoat 1, coloured iris disc, black pupil, painted catchlight; partial
   eyelid shells when needed. (TF irises #770d0b red, #c56812 yellow-orange; AW sockets #010011 with a glint.)
4. **Materials**: clay/plasticine = `MeshPhysicalMaterial` roughness 0.65-0.75, sheen 0.3-0.5 (lighter tint of the skin), painted
   mottling and blush; porcelain/glazed ceramic = roughness 0.2-0.3, clearcoat 1, clearcoatRoughness 0.1-0.15; fabric = high roughness
   plus a fine knit or weave texture; translucent wings = `ShapeGeometry`, vein canvas texture, opacity 0.5, `DoubleSide`, `depthWrite:false`.
5. **Mouth never animates** (sculpted open or closed). Personality comes from body sway, head tilt (AW 20-30°), bob and flight.
6. **Scale is cheated per shot** for drama (AW bends a 12-stud monster to a ground-floor window), but the model stays the same.
7. **Crowds** = 6-8 variants, instanced, with hue shifts and random offsets (TF swarm).
8. **Shoot it from below**: low and extreme-low angles for the creature; it reads bigger and creepier.
9. **Hero props are oversized** for readability: TF tooth 0.7 head, coin 0.5 head, cards 0.8 head.

**EP01 creatures (construction CHOSEN to these rules; designs from `scripts/EP01_FINAL.md` build sheet):**

| Creature | Build | Look |
|---|---|---|
| **Grandpa gnome** (hero creature) | Sculpted, not boxes: lathe body with a belly, sphere head, cone hat with the tip bent sideways, clump moustache, boots, mitten hands around the lantern. Height **2.0 studs** with hat (0.38x the kid; the script's "knee-high" would be 1 stud and too small to read in medium shots). See `makeGnome` in `lookdev/js/chars.js`. | Glazed ceramic: `MeshPhysicalMaterial` roughness 0.28, clearcoat 1, clearcoatRoughness 0.12. Red coat, olive fishing hat with lures, white walrus moustache, ruddy nose and cheeks. Painted eyes on glossy domes (iris about 30% of eye width) with catchlights. Chips showing white bisque, dirt at the base. Blink = 2-frame eyelid texture swap (4 frames for the slow blink). Epilogue: moss and lichen, faded paint. |
| Brass lantern | Cap, glass cylinder, 4 bars, ring handle (`makeLantern`) | Brass roughness 0.35, metalness 0.7; glass emissive #ffb347 (0 when unlit); halo sprite 0.9 stud |
| Street gnomes | 6-8 variants of the same build (hat shape, coat colour, beard), instanced | Same glaze; next door's are glossy **plastic** (roughness 0.15, oversaturated, a price-sticker decal) |
| Star-nosed moles | Only a turf mound (displaced grass-textured blob, 3 studs across, 0.6-0.9 high, crumbs at the rim) with a pink star snout (a disc with 22 tapered capsule tentacles, 0.9 stud across) and two amber "bike reflector" eyes (0.22 stud, 0.6 apart). No teeth, no mouth | Snout `MeshPhysicalMaterial` #e48aa0 roughness 0.5, sheen 0.6, faint emissive #401018; eyes emissive #ffb020 intensity 3-5 with a faceted reflector texture and a 15-25 px halo sprite |

### 2.7 Scale chart (studs; metres = studs x 0.32)

| Item | Size | Source |
|---|---|---|
| R6 human (adult or kid) | 5.2 tall, head 1.2, eye line 4.65 | MUST (all refs) |
| Small creature (TF fairies) | 0.4-0.6x human | TF |
| Big monster | 2.4-3x human (12-15 studs) | AW, PN |
| EP01 gnome | 2.0 (0.38x) | CHOSEN |
| Hand props | 0.5-0.8 head (0.6-1.0 stud) | TF |
| Interior door | 7.5 x 4 | CHOSEN (Bloxburg-like) |
| Interior wall height | 12-13 | CHOSEN |
| Window sill / window | sill at 3, window 4 x 5 | CHOSEN |
| Single bed | 7.5 x 5, mattress top 2.4 | CHOSEN |
| Picket fence / gate | 3.5 high, gate 4 wide | CHOSEN |
| Street lamp | 13-14 tall, one every second house (~35 studs) | PN (scarecrow 15 > lamps) |
| Bungalow / two-storey house | 14-16 / 26-30 to the ridge | CHOSEN |
| Lot width, front lawn depth | 32-40, 20-28 | CHOSEN |
| Sidewalk / 2-lane road / kerb | 6 / 24-28 / 0.4 high | CHOSEN |
| Pines | 18-30 | CHOSEN |
| Moving truck box | 24 long x 9 wide x 10 high | CHOSEN |

---

## 3. Animation spec

Look first at: `$PNV/s/m_walk.jpg`, `$CGV/m/walk_kid.jpg`, `$CGV/m/gest_a.jpg`, `$CGV/m/turn96.jpg`, `$AW/an_head.jpg`,
`$AW/an_reach.jpg`, `$TFV/s/m_fernpick.jpg`, `$TFV/s/m_wings.jpg`, `$TFV/s/m_pull.jpg`.

**Budget (MUST):** about 45% of shots near-still (only the camera moves), 25% light motion, 30% active (M: TF 49/26/39 shots).
Animation time goes to the creature and to action beats; exposition shots are tableaux.

### 3.1 Humans (R6)

| Action | Spec | Ref |
|---|---|---|
| Idle | Frozen pose. CHOSEN: an optional breath of torso scale-y 1.00-1.01 at 0.25 Hz; no head drift, no weight shifts, no blinks | all refs frozen |
| Walk | Arms and legs swing as rigid blocks, sine, opposite phase: legs ±35-40°, arms ±40° (or arms held in a pose: carrying, holding). Cycle **0.73 s**. No torso bob, no twist. Travel about 7 studs/s so the feet do not slide (2 x 2·sin40° per cycle). Small figures far away may use a 1 s cycle | CG f3294-3338, PN |
| Run | Legs ±55-60°, cycle 0.5 s; either arms opposite ±45-60°, or the **panic run with both arms raised forward to shoulder height** | AW #72, PN #86 |
| Sleepwalk / zombie | Both arms straight forward and level (90°), head pitched down 20-30°, legs ±15°, slow | AW #50 |
| Jump | Default R6 jump: arms straight up (180°), legs together, parabolic hop about 0.5 s | CG #1 |
| Sit | Hips 90°, legs forward; pop into it in one frame under a cut or VFX, otherwise a 0.15 s blend | PN 108.6 s |
| Kneel | Torso pitched about 60° forward, legs rotated back under the body (no knees) | CG #51 |
| Turn | Whole body yaws; 90° in 0.1-0.2 s, 180° in **14 frames** with inOutSine | PN, CG #96 |
| Hands to head | Both arms snap to the sides of the head in **8 frames** with an ease-out, then hold with a tiny rock | CG #10 |
| Hand on shoulder | Arm from down to horizontal across in **16 frames**, then hold | CG #102 |
| Reach / point | Arm rises waist to target in about 0.45 s; hold the point about 2 s | AW #4, #70 |
| Hug / carry | Both arms forward 70-90°, the carried object parented to the torso | PN #75 |
| Wave | Arm up 160°, wrist-less wave = arm rocks ±15° at 2 Hz | TF |
| Props | Hands simply overlap props (no fingers). CHOSEN: props never teleport in view; a hand-off happens under a cut, a VFX puff or a camera whip | AW, TF tell fixed |

Pose-to-pose timing:
- Gestures use a short snap of 6-16 frames with `outBack` or `outQuad`, then a hold until the shot ends. Use `ctx.anim.poseSeq(t, keys, blend)`
  with blend 0.1-0.25 s, or explicit eased keys.
- A **1-frame pop** is allowed only when it lands on a cut, under a VFX burst, or during a whip (that is how the references hide them).
- Facial swaps follow §2.5 (on the word).

### 3.2 Creatures and magic objects (smooth, keyframed)

| Motion | Spec | Ref |
|---|---|---|
| Hover-bob | 10-20 px vertical at about 1 Hz (`anim.bob`) | TF |
| Wing flutter | ±15-25° at 3-5 Hz | TF |
| Body sway while "speaking" | ±5-10° at about 0.5 Hz, head turns ±15°; mouth fixed | TF Queen |
| Glide / walk | Monster glide 1-1.5 studs/s with slight lateral sway; heavy walk at one step per second | AW, PN |
| Creepy head turn | 180° yaw in **0.8 s inOutSine** (AW) or **2.1 s almost linear** (CG). Cut 0.1 s after it ends to a lower, closer angle | AW #48, CG #97 |
| Torso bend | 0 → 90° over 1.4 s inOutSine | PN #13 |
| Flight | Catmull arcs with the camera following; fly-ins accelerate (ease-in) toward the lens | TF #2, #68, #92-95 |
| Objects sliding into place | inOutSine over about 1.2 s | TF #82 |
| Light-state events | Instant (1 frame) switches, cascaded 0.15-0.45 s apart (lamps going out, windows going dark, lanterns lighting) | PN 110.87-112.73 s, AW #15 |
| Lift-off / rumble | Slow rise plus camera shake (§7) | TF #101-103 |

EP01 specifics (CHOSEN):
- **Gnome**: a statue; it moves only on beats. Blink = 2-frame closed-lid swap (slow blink: 4 frames closed). Head turn = a stony grind
  of 120-180° over 0.9-1.2 s with a 2-3° stepped jitter every 3 frames and a stony-creak SFX. The gate toddle (line 09) = small hops of
  0.1 stud at 2.5 Hz with ±8° roll, then a bonk and a light ripple at the property line.
- **Moles**: mounds travel 2-4 studs/s with a bulge wave rolling under the turf; the snout tentacles wriggle ±10° at 2-3 Hz with phase
  offsets; recoil from light = a 0.15 s snap back with a spring overshoot (`anim.springKeys`); sinking = the mound deflates over 0.5 s
  and the eyes wink out one pair at a time every 0.2-0.3 s.
- **Lanterns**: unlit until the beat; light-up = emissive 0 → 4 in 3 frames with a 6-frame overshoot to 6, halo sprite fades in
  0.2 s; idle flicker ±6% (`anim.wobble` 7 Hz).

### 3.3 What NOT to do

- Too smooth: no squash and stretch, no overlapping action on hair, hoods or clothes, no elbow or knee bends on humans, no IK foot
  planting, no Pixar-style acting holds with micro-motion, no lip-sync, no idle blinking, no continuous fidget.
- Too stiff: no shot without camera motion, no props teleporting in view, no visible 1-frame pops outside a cut/VFX/whip, no 40-fps
  judder, no frozen creature (creatures always bob, sway or breathe).
- Every motion must be a pure function of shot time `t` (engine determinism rule): use tracks, `springKeys`, `wobble`, never
  accumulate state.

---

## 4. Environment kit

Look first at: `$TFV/s/env1.jpg`, `$TFV/s/ext1.jpg`, `$TFV/s/shad.jpg`, `$AW/g_01.jpg`, `$PNV/s/v_env1.jpg`, `$PNV/s/v_int1.jpg`,
`$CGV/m/v_env1.jpg`.

### 4.1 Building rules (MUST)

- Roblox parts: boxes, wedges and cylinders with **no studs**, small bevels (0-0.05 stud) or sharp edges, every surface textured.
  Low-poly architecture, detailed props.
- Dense dressing: 5-15 props in every frame, and **a recognisable prop behind every close-up** (TF: clock, lamp, poster, shelf).
- A recurring **motif prop** visible in most night close-ups (TF: the clock frozen at 12; AW: the red LED 12:00). EP01 CHOSEN: Grandpa's
  lantern glow, the hall clock at 9:00, and the hero's (later Theo's) window.
- Distance falls off: to black (night), to fog colour (day haze), never to a visible set edge.
- Childhood iconography where it fits: glow stars, posters, shag rug, toys, stuffed animal.
- In-world text (signs, boards, labels) in a bold geometric sans (Montserrat-like) black on white with red headers; clocks with Roman
  numerals; each sign gets its own insert at the moment it is spoken (CG, AW).

### 4.2 Materials (Roblox material → engine generator)

| Roblox look | Engine | Tiling and values |
|---|---|---|
| Fabric wallpaper (TF blue wall) | `tex.plaster({ bump })` | fine micro-bump, tile about 4 studs, roughness 0.9 |
| Glossy wood floor (TF) | `tex.woodPlanks({ color: '#9f3305' })` | planks 0.8-1.0 stud wide, roughness 0.3-0.4 (visible sheen) |
| WoodPlanks, Wood (frames, doors, porches) | `tex.woodPlanks` | roughness 0.6-0.7 |
| Brick | `tex.brick` | bricks about 1.0 x 0.45 stud, mortar visible, roughness 0.9 |
| Clapboard siding (PN) | port `sidingTextures` from `lookdev/js/lib.js` (the engine has no siding generator yet) | boards 0.6 stud, grain noise |
| Grass (lawns) | `tex.grass` | fine noisy blades, dirt-patch variation, roughness 1.0 |
| Concrete sidewalk | `tex.concrete({ seams })` | slabs 6 studs, roughness 0.85 |
| Asphalt road | `tex.concrete` dark or `asphaltTextures` | yellow centre dashes 3 x 0.3 every 8 studs |
| Shingle roof | `tex.roofShingles` | roughness 0.85 |
| Duvet, bedding | `tex.fabric` on a displaced plane (summed sines + noise folds) | roughness 0.95, frilly skirt = lathe |
| Shag rug | `tex.carpet` on a noise-displaced disc | roughness 1.0 |
| Glass | `MeshPhysicalMaterial` transmission 0 / opacity 0.25, roughness 0.05 | lit windows are emissive planes behind it |
| Neon (bulbs, lit windows, LED) | `MeshBasicMaterial` or emissive Standard | see §5 |

### 4.3 Suburban exterior kit (night, dusk, dawn, day)

| Element | Spec |
|---|---|
| Houses | Bungalows and two-storey houses in a row, one parametric generator: brick (TF dark red-brown) or clapboard (PN cream, sage, mustard, grey, white, red, blue-grey); white window trim, 4- or 6-pane sashes, dark shutters, dark-red or brown front door with a brass knob, house-number plaque, dark shingle roof, stone foundation, porch with white square columns, spindle railing (instanced), steps, wall lantern |
| Windows at night | Warm emissive glass (#ffd9a0) for lit rooms, a few pink-lit (TF #f7a8d0), dark ones with a faint reflection; curtains as fabric planes |
| Gardens | Lawn with dirt patches, flowerbed with tulips under the bedroom window, round flower bushes, white picket fence and gate, path stepping stones, mailbox (black), hose, kennel, estate-agent board on a post |
| Street | Concrete sidewalk with kerb, 2-lane asphalt with yellow dashed centre line, optional zebra crossing (AW), black Victorian lamp posts (fluted pole, cross-arm, lantern head) one per two houses on both sides, signs on black posts |
| Vegetation | Realistic-feeling pines (stacked cones with noise, 18-30 studs) and blob trees; keep one tree style per shot (CG mixed low-poly and photoreal: a tell) |
| Backdrop | Distant low-poly mountains as dark silhouettes; at night everything past ~60 m fades to the sky colour |
| EP01 extras | Moving truck (box 24 x 9 x 10, open back, ramp, cardboard boxes "BALCONY GNOME", "THEO"), SOLD sticker, "KEEP OFF THE LAWN AFTER DARK" sign, street gnomes with brass lanterns, property-line shimmer |

### 4.4 Bedroom kit (TF master interior; reused for Theo's room seen through the window)

Blue fabric-textured wallpaper (#4958a0-#839ae7 graded), white skirting; lavender ceiling (#b28dc0) with pale yellow-green 5-point
glow-star decals (emissive 0.6); glossy dark terracotta plank floor (#9f3305); bed with a carved dark-wood headboard (vertical ridges),
white puffy creased pillows, magenta duvet (#a93298-#c585d1) with real folds, frilly white-lavender bed skirt; white nightstand with
blue drawers and gold knobs; cream drum lamp shade (emissive #fffee1) on a brass stem; wall clock (orange rim #9c3703, lavender-white
face, Roman numerals; EP01 hall clock at 9:00); posters on navy ("TO THE STARS"-style, our own designs); pink round shag rug; shelves
with red, yellow and blue books, a toy car, a teddy; thick white window frame and sill; wooden door. AW alternative for a warmer room:
uniform rose wall #a16a63, navy knit blanket, red 7-segment LED clock.

### 4.5 Sky and terrain

| Sky | Spec | Ref |
|---|---|---|
| Night void | Pure black, or `tex.starSky` with stops from #000000 (zenith) to #0d0a2a (horizon), 2-4k small grey-white stars | AW, PN |
| Galaxy night (TF, our default for magic nights) | Black to deep violet (#020018) with magenta-purple nebula wisps #2a022c / #46134d / #3a2988 (nebula 0.25-0.35) and dense stars | TF |
| Moon | Large sphere with a crater texture, tinted blue-violet #3f43a9-#6161d3 (TF) or a white disc #e9f6ff with a 25 px halo (AW) | TF, AW |
| Dusk | Zenith #373d3b → horizon #77594e (PN), or a warm sunset: horizon #bb541a to amber (CG) | PN, CG |
| Blue hour | #3e64b7 / #4f84b0 fading to a peach horizon #d1ad7d, a few faint stars | PN |
| Dawn (CHOSEN for EP01's "pink dawn") | Zenith #5d74c4 → mid #c39cc4 → horizon #f8cba4, low sun disc #fff0d8 | derived from PN blue hour + TF morning |
| Day | Roblox default gradient #258edf (top) → #55b1d9 (horizon), or cloudy #68898d with cream clouds #e6ceb4 | AW, TF |
| Terrain | Flat baseplate lawns; no hills except distant silhouettes; no water | all |

Use `tex.skyDome(tex, { radius, fog: false })` for skies that must stay visible.

---

## 5. Lighting presets

General rules (MUST): strong **coloured** hemisphere ambient; one soft key from the **upper front-left**; no hard cast shadows indoors;
exteriors at night show essentially no shadows (TF, AW); real soft sun shadows only in dusk, dawn and day exteriors (PN); emissive
practicals with small halos; **the subject is the brightest thing in a night frame**. Use one shadowed light at most per shot and fake
contact shadows under characters with a radial-gradient decal (`tex.radialGlow`, multiply, opacity 0.3-0.4, 1.2x the footprint): it is
also the cheapest option on SwiftShader (a point-light cube shadow costs about 150 ms per frame).

Light units are the engine's physically based units (`ctx.lights.*`; point lights in candela). Values below are **starting points**,
calibrated against the demo scene (hemi 1.1, moon 1.7, lantern 3.2 cd at exposure 1.15); the grade preset (§6) does the final colour.
Always verify a test still against the target column with `python3 -I lookdev/tools/stats.py still.png` (same metrics as the analyses).

### 5.1 Presets

**P1 NIGHT STREET / NIGHT LAWN** (TF periwinkle exterior, lifted for EP01; used 28-94 s)

| Item | Value |
|---|---|
| Sky | Galaxy night (§4.5), `fog:false` |
| Hemisphere | sky #8a90ff, ground #241a3a, intensity 1.0 (raise to 1.3 for the EP01 "high-key" lawn shots) |
| Key (moon) | `lights.sun` #b4b8ff, intensity 1.4, upper front-left, elevation 40-55°; shadows **off** by default; for a hero wide use pcfsoft, radius 6, mapSize 2048, tight frustum |
| Street lamps | Glass emissive #ffd9a0 x4; a point light #ffc27a, 4-6 cd, decay 2, no shadow, only on the 4-6 lamps nearest camera; the rest get an additive light-pool decal on the road (`radialGlow`, #ffb870, opacity 0.25-0.35, radius 5-7 studs) |
| Lit windows / porch lantern | Emissive #ffd9a0 x2-2.5 / point #ffb766, 2-4 cd |
| Gnome lanterns (lit) | Point #ffb85c, 3-4 cd, decay 2, no shadow; glass emissive #ffb347 x4-9; halo sprite; a warm ground pool decal 3-4 studs across (TF fairy glow pool about 150 px) |
| Fog | exp2, colour #06051a, density 0.012 per metre (houses across the street stay clear; the street end fades) |
| Exposure | ACES, 1.0-1.1 |
| Target stats | mean luma 60-95 (EP01 lawn close shots 75-100), sky 0-10, hi #b3b6fc-#c4c3fc, lo #000000-#0e1237, sat 0.45-0.6, crushed ≤ 25% |

**P2 BEDROOM NIGHT** (TF cool interior: lamp plus moonlight)

| Item | Value |
|---|---|
| Hemisphere | sky #b9a8ff, ground #5a2a4a, intensity 1.3 (the coloured ambient does most of the work) |
| Key | `lights.sun` #e8deff, intensity 1.0, upper front-left; shadows off, or pcfsoft radius 8, mapSize 1024 (soft, faint) |
| Bedside lamp | Shade emissive #fffee1 x2.5; point #ffe6c0, 3-5 cd, decay 2, no shadow; halo sprite 15-30 px |
| Moonlight | Directional #9aa6ff at 0.4x the key, from the window side, no shadow |
| Glow stars, clock | Emissive #e9f7a0 x0.6 |
| Window view | The P1 world behind glass, **darker than the room** (CHOSEN: fixes TF's bright windows) |
| Fog | none |
| Exposure | ACES 1.05 |
| Target stats | mean luma 105-125, p1 5-20, p99 200-230, hi #d4bced-#e7d4fc, lo #431007-#723644, sat 0.45-0.6 |

**P3 MAGIC GLOW MOMENT** (TF fairy-court warm grade; EP01 lantern lit 41-43 s, FWOOM 86.9-92.5 s)

| Item | Value |
|---|---|
| Switch | On the beat word: on the cut, or in-shot over 6-10 frames. No white flash frames (TF never flashes) |
| Hemisphere | sky #ffcdb8, ground #5a2030, intensity 1.4 |
| Key | #ffe2c8, intensity 1.2, soft, no shadow |
| Source | Lantern point #ffb85c 8 cd lit; FWOOM: 8 → 40-60 cd in 0.15 s, then down to 10 over 1.5 s (inOutSine); emissive x4 → x25; an expanding additive ring (disc sprite / flat torus) rolling over the lawn at 6-10 studs/s |
| Particles | 20-40 gold and pink motes plus white glints (§6.3) |
| Post | bloom 0.35-0.45 (threshold 0.9), glow 0.12 (§6) |
| Target stats | mean luma 130-150, hi #f2cfbc-#fde3c7, lo #4a1626-#6c2a3d, sat 0.4-0.5 |

**P4 DAWN** (EP01 94-103 s; TF morning cream + PN blue hour)

| Item | Value |
|---|---|
| Sky | Dawn gradient (§4.5), sun disc low on the horizon |
| Sun | #ffcf9e, intensity 2.2, elevation 8-12°, from behind-side (rims and long soft shadows); pcfsoft radius 3, mapSize 2048 |
| Hemisphere | sky #c4c8ff, ground #6a4a3a, intensity 0.9 |
| Practicals | Lanterns dimmed to 0.5 cd or off; windows off |
| Fog | exp2 #e8c4c0, 0.006 per metre (distance lightens) |
| Target stats | mean luma 135-150, p99 235-245, clip ≤ 1%, hi #fcf4d9-#f8d09e, lo #5b1b02-#7f6a7c |

**P5 THE "DREAMY" HOUSE LOOK** (applies on top of every preset; TF §5.4)
1. A purple/magenta (or peach) cast over everything; shadows maroon or purple, never grey.
2. Soft highlight shoulder: whites stop at 88-92% and take the location tint (`grade.outWhite`).
3. Low shadow contrast: soft omni light, no hard shadows.
4. Night as coloured light: rooms bright (mean luma 105-130); only the sky is black.
5. Floating soft sparkles in nearly every night and magic shot.
6. Gentle glows on emissives only (sprites + low bloom).
7. A constant slow push-in on near-still images.
8. Grade switches by story beat (cool → warm when magic arrives → cool → day/white → warm morning).

**Additional presets used in EP01**

| Preset | Light | Target |
|---|---|---|
| DAY (world montage, SOLD sticker) | Sun #fff3e0, intensity 2.5, elevation 45°, pcfsoft radius 3; hemi #bcd4ff / #5a4a30, 1.0; light haze #c8d0e0 0.006/m | whites #f2e0c1-#fcfcf6, mean luma 110-155, sat 0.5 |
| DUSK (frame 1, epilogue; loop-matched) | Sun #ff9a50, intensity 2.0, elevation 4-6°, long soft shadows; hemi #8a7cc0 / #4a2a20, 0.8; warm lit window | hi #e0c4a6-#f2d4b0, mean luma 90-110, sat 0.6-0.75 |
| SEPIA FLASHBACK | Light as NIGHT or DAY; colour from the grade | AW flashback: mean #634c42, whites #cbbeba, R:G:B 1.30:1:0.86 |
| B&W FLASHBACK (CHOSEN, older memory) | As above; grade saturation 0 | whites #e8e2d8, blacks #0e0c0a |

---

## 6. Post stack presets (engine/core/post.js)

The post stack is HDR scene → bloom/glow → uber pass (white balance, tone map, grade, vignette, fade/flash, grain, dither). **Never
use `renderer.toneMapping`.** Post params reset at every shot start (episode `post` → shot `post` → `build()`).

**Do not copy the demo's post** (`_demo.js` turns on DOF, vignette and glow): the references measured none of them.

### 6.1 Episode base (every shot)

```js
post: {
  toneMapping: 'aces', exposure: 1.0, aa: 'msaa', msaaSamples: 4, dither: true,
  bloom: { enabled: true, strength: 0.12, radius: 0.35, threshold: 1.2, knee: 0.5, start: 'quarter', tint: '#ffffff' },
  glow: { enabled: false }, dof: { enabled: false }, vignette: { enabled: false }, chroma: { enabled: false },
  lens: { enabled: false }, grain: { enabled: false }, godrays: { enabled: false }, blur: { enabled: false },
  grade: { enabled: true, ...GRADE.night },   // replace per shot
}
```

Bloom: the metrics found **no measurable thresholded bloom** (halo tails are the same for mid-tones and lamps); TF's visible glows are
local. So bloom stays low and catches only emissives above the threshold; the visible halos come from additive sprites. Tune so a lamp
shade or lit lantern has a 15-30 px halo at 1080 wide (TF 10-20 px, AW 25-30 px).

### 6.2 Grade presets (`grade` params; colours are display-space)

`outBlack`/`outWhite` are output levels (`col = outBlack + col * (outWhite - outBlack)`), applied after tone mapping, lift/gain,
contrast, saturation and split toning. `outWhite` is where the location tint lives.

```js
export const GRADE = {
  // TF periwinkle night exterior (P1). outWhite luma ≈ 202 → p99 ≈ 195-215.
  night:      { temperature: -18, tint: 8,  contrast: 1.05, pivot: 0.4, saturation: 1.12,
                shadows: '#1a1446', shadowsAmount: 0.3, highlights: '#c8c4ff', highlightsAmount: 0.25, balance: 0,
                outBlack: '#000000', outWhite: '#c4c3fc' },
  // TF cool lavender interior (P2). outWhite luma ≈ 222; outBlack lifts p1 to ≈ 9 (maroon).
  bedroom:    { temperature: -6,  tint: 14, contrast: 0.95, saturation: 1.08,
                shadows: '#5a1e3a', shadowsAmount: 0.35, highlights: '#e0c8f8', highlightsAmount: 0.2,
                outBlack: '#140507', outWhite: '#e7d4fc' },
  // TF warm "fairy glow" (P3). outWhite luma ≈ 231.
  warmGlow:   { temperature: 14,  tint: 6,  contrast: 0.95, saturation: 1.0,
                shadows: '#6c2a3d', shadowsAmount: 0.35, highlights: '#ffdcc4', highlightsAmount: 0.25,
                outBlack: '#1e070b', outWhite: '#fde3c7' },
  // TF morning cream / EP01 pink dawn (P4). outWhite luma ≈ 243.
  dawn:       { temperature: 10,  tint: 6,  saturation: 1.05,
                shadows: '#5b2a3a', shadowsAmount: 0.25, highlights: '#ffe6cc', highlightsAmount: 0.2,
                outBlack: '#120604', outWhite: '#fcf4d9' },
  day:        { temperature: 2,   saturation: 1.05, outBlack: '#0a0604', outWhite: '#f6f2e6' },
  dusk:       { temperature: 22,  tint: 4,  saturation: 1.15,
                shadows: '#2a0d18', shadowsAmount: 0.3, highlights: '#ffd2a0', highlightsAmount: 0.25,
                outBlack: '#0c0304', outWhite: '#f2d4b0' },
  sepia:      { temperature: 30,  contrast: 0.95, saturation: 0.6, highlights: '#ffd9a8', highlightsAmount: 0.2,
                outBlack: '#1a0e08', outWhite: '#e3cdb8' },
  bw:         { contrast: 1.08, saturation: 0, outBlack: '#0e0c0a', outWhite: '#e8e2d8' },
};
```

### 6.3 Per scene type

| Scene type | Grade | Exposure | Bloom (strength / threshold / radius) | Glow | Sprites (in the scene, not post) | Everything else |
|---|---|---|---|---|---|---|
| Night street / lawn | `night` | 1.0-1.1 | 0.12 / 1.2 / 0.35 | off | 8-15 white-lavender glints; lamp halos; lantern pools | off |
| Bedroom night | `bedroom` | 1.05 | 0.15 / 1.1 / 0.35 | off | 5-15 glints; lamp halo | off |
| Magic glow moment | `warmGlow` | 1.1 | 0.35-0.45 / 0.9 / 0.5 | `{ enabled: true, amount: 0.12, radius: 0.8, mode: 'screen', tint: '#ffd8c8' }` | 20-40 gold + pink motes, burst ring | off |
| Dawn | `dawn` | 1.0 | 0.12 / 1.2 / 0.35 | off | 0-6 warm motes | off |
| Day | `day` | 1.0 | 0.1 / 1.3 / 0.3 | off | none | off |
| Dusk (frame 1, epilogue) | `dusk` | 1.0 | 0.15 / 1.1 / 0.4 | off | dandelion seeds, 3-6 warm motes | off |
| Sepia / B&W flashback | `sepia` / `bw` | 1.0 | 0.1 / 1.2 / 0.35 | off | none | off |

**Sparkle spec (TF signature).** `tex.sparkle({ points: 6 or 8 })` on additive `Sprite`s (`depthWrite:false`), colour #e9dcff (some
#ffe2c4), 40-80 px on screen, 8-20 visible per frame in night interiors and magic shots (fewer outdoors: 6-12), drifting 20-60 px/s
upward and sideways, twinkling (opacity 0.35-1 and scale 0.6-1.2 on a 0.6-1.2 s sine with random phase), slow rotation. Variants: pink
4-point twinkles and gold dust around magic sources; one big 4-point star glint on a precious prop (TF coin). **Bursts**: 20-40 sprites
plus an expanding white ring sprite over 0.3-0.4 s (TF 3.5, 36.28, 109.62 s); EP01 uses them for the dandelion puff, the gate ripple,
the lantern lighting and FWOOM. The `sparkles()` helper in `_demo.js` is a valid starting point.

**Optional "escalation" kit (CG act 3 only; NOT used in EP01):** vignette `{ amount: 0.5, size: 0.3, softness: 0.7, roundness: 0 }`
(edges at about x0.5), glitch-bar cuts (an `extra` pass: 2-5 full-width bars, red #d84040 / cyan #3ed0e8 at 50%, plus 3-8 sliced
rows shifted ±10-40 px, re-randomised every 3-5 frames, for 6-9 frames after the cut), white flash-in (`flash.amount` 0.55, 0.55, 0.40,
0.12, 0 on frames 0-4), dust specks (20-40 dots of 4-6 px, each living 3 frames).

**Editor shake hit (PN, optional for a horror beat):** 6 frames of ±50-76 px jolts and ±1.7° roll with directional blur
(`camera.shake({ px })` + `post.blur.dir`), locked to an SFX transient.

---

## 7. Camera grammar

Look first at: `$TFV/s/m_open.jpg` (opening pull-back), `$TFV/s/m_up.jpg` (whip tilt), `$TFV/s/m_swarm.jpg` (crane pull-back),
`$TFV/s/m_liftoff.jpg` (shake), `$AW/zoomcmp.jpg`.

### 7.1 Lens and framing

- **Vertical FOV** (engine `fov` is vertical): wide **70°** (the Roblox default; TF 77% of shots, PN 98%), normal 40-50° for inserts and
  extreme wides, tele 20-30° for moon/space/far reveals. On 9:16, 70° vertical is only 43° horizontal; perspective stretch on close faces
  is part of the look.
- **Subject on the vertical centre line**; faces in the upper 25-45% of the frame; nothing important in the caption band (y 1260-1420).
  CHOSEN: keep key action inside x 90-900 and y 250-1500 (YouTube Shorts buttons and description).
- Camera heights: human eye level 4.6 studs; slightly high 6-8; low 1-2.5; gnome eye level 1.4; ground level 0.3-0.5; top-down 90° for
  objects on beds, floors and lawns.

### 7.2 Shot size and angle distribution (targets for an episode)

| Size | TF share | Target | | Angle | TF share | Target |
|---|---|---|---|---|---|---|
| ECU / CU / MCU / INS (close) | 51% | 45-50% | | eye level | 45% | 45% |
| MS / MWS | 27% | 25-30% | | low / extreme low | 21% | 20% (creatures) |
| WS / EWS | 19% | 18-22% | | high | 19% | 18% (the kid in bed) |
| OTS / POV | 3% | 3-5% | | top-down / aerial | 14% | 12-15% (objects, lawns) |

Creatures low, objects top-down, the kid at eye level or slightly high.

### 7.3 The default move (MUST)

```js
ctx.camera.set({ pos, target, fov: 70 }).push(Z);   // Z per shot: median 0.19, p10 0.10, p90 0.30
```

- Linear in image scale (`fov_t = 2·atan(tan(fov0/2) / (1 + Z·u))`), centred, **no ease at either end**, cut mid-move. Z is drawn per shot
  (e.g. `clamp(0.19 + 0.07·ctx.rng.gauss(), 0.08, 0.32)`) and does **not** scale with shot length (TF r = 0.08). FOV mode (no parallax) is
  the TF default; use `{ mode: 'dolly' }` in about 1 shot in 4 for parallax (AW, CG).
- Add a slow drift of 20-70 px/s (a small `truck`/`crane`) and, in about 1 shot in 3, a roll drift of 0.5-1.5° over the shot (`rollBy`).
- Pull-outs are accents: 5-10% of shots.

### 7.4 Accent moves (about 1 shot in 6; the opener is always one)

| Move | Numbers | When | Ref |
|---|---|---|---|
| Snap pull-back (opener) | x3.4-x10 out, exponential ease-out (`outExpo`): half done in the first 0.1 s, 78% in the first quarter; peak 3000-5600 px/s; may carry a roll that levels out (-19° → 0) | First shot; "a hundred", "whole", "dozens" (reveal of quantity) | TF #1, #34; CG #1 |
| Punch-in on a reveal | x1.45-x2.0 in 0.6-1.3 s (linear or accelerating), optional roll +10-13° | Naming the creature, "takes you", "came around the corner" | TF #4, #38; AW #4, #8, #81 |
| Fly-in to lens | ease-in: x1.14 over 0.7 s, then x2.8 in 0.33 s | Creature approaching | TF #68 |
| Whip tilt / pan | about 1900-2450 px in 0.6-0.7 s (≈ 70° tilt, 95° pan at 70° vFOV), `inOutSine`; frames stay sharp (no blur) | Jumps in space: "Up.", "toward Dex's house" | TF #47, AW #23, PN #84 |
| Fast truck / aerial follow | 1900-2450 px/s constant | Flights over houses; lanterns lighting down the street | TF #93-94 |
| Truck along house fronts | 700-1200 px/s constant | Street exposition | PN #18, #70 |
| Crane up following | 2400 px in 1.2 s | Something rises into the sky | TF #2 |
| Orbit | 90° in 0.15-0.3 s (fast) or 17-27° over 2.5-5 s (slow) | A creature arriving; circling a tableau | TF #15, AW #46 |
| Tilt along a tall subject | 850-1440 px, linear | "ten feet tall", wall of marks | AW #41, CG #26 |
| Boot-level tracking | ground-level dolly beside feet | Monster walking | PN #10 |
| Shake | ±5-25 px with spikes to ±50, re-randomised every 3 frames, decaying over 0.5 s (`shake({ px, dur, freq })`); violent ±70 px for 1 s only on a scream | "shook", "rumbled", the lawn moving | TF #101-103, AW #86 |
| Jump cut on the same axis | x1.15-1.3 punch, or same set-up with the object changed | Lists, emphasis | TF #24-26, CG #15 |
| Light-state jump cut | Same framing, new lighting | "lit up", lanterns lighting | TF #98 → #99 |

Per 100 shots (TF profile): about 80 plain linear pushes, 6 strong pushes, 6 pull-backs, 10-12 big translations, 3 shakes.

### 7.5 Cutting

- Cuts per minute 45-52 (TF 52, CG 48). EP01's voice is 235 wpm against TF's 261, so aim for about **5 words per shot**: 88-95 shots in
  113 s, median 1.15-1.25 s.
- Shot length targets: p10 0.5 s, median 1.1-1.2 s, p90 2.0 s, max 2.3 s (one reveal may reach 2.5 s with a strong move). Histogram
  target: <0.5 s 8% · 0.5-1 s 35% · 1-1.5 s 30% · 1.5-2 s 18% · >2 s 9%.
- **Transitions: 100% hard cuts.** No fades in or out, dissolves, wipes, flash frames or whip transitions between shots (whips live
  inside shots). Frame 0 is a full picture, mid-motion; no title card, no black frame. The video ends about 0.35 s after the last
  audible voice sample (EP01: last audible sample 112.95 s, so end at about 113.3 s) on a normal shot, ideally matching frame 0 for the loop.
- How shots follow the narration (cut on the naming word, sentence starts, lists, reactions, inserts): `docs/STORYBOARD_RULES.md`.

---

## 8. Captions (optional captioned version) and SFX palette

### 8.1 Captions

Deliver a clean master; the owner may caption in CapCut. If we burn captions, use the TF/PN house style:

| Property | Value |
|---|---|
| Font | Heavy geometric grotesque: **Montserrat ExtraBold (800)**; a double-storey "a", straight-tailed "y". (AW uses Verdana Bold; CG Poppins Bold.) |
| Size | About 96 px (cap/ascender height 69 px, x-height 51 px) |
| Fill | White #ffffff (narrator) |
| Stroke | Black, 5 px outside the glyph (canvas: `strokeText` with lineWidth 10, `lineJoin: 'round'`, then `fillText`) |
| Shadow | Black at 90%, offset (+5, +5), blur 8-10 px |
| Position | Centred at x 540; baseline y 1385 (ascender top 1317; band centre about y 1351-1355) |
| Words | One word at a time, lower case except "I" and names, numbers as digits ("60", "71", "9"), punctuation stripped. Fix ASR errors (TF left them in) |
| Timing | Swap exactly on the word onset (-2 to +1 frames); hold until the next word; the band is never empty |
| Animation | None (TF, PN). CG has a 1-frame 92% pop; use it only if the owner asks |
| Speaker colours (PN, for quoted lines) | Grandpa #f9dd6e (yellow), Theo #96c8f5 (light blue), the hero speaking in-scene #f1b16c (orange), others #ed99bf (pink); shouting in CAPS; no quote marks |

CapCut equivalent: auto captions, one word per line, Montserrat ExtraBold 96 (or the closest bold sans), white, black stroke 5,
shadow on, position about 70.5% down, no animation.

### 8.2 SFX palette and density

What the references do (measured):
- A continuous voice with **no gaps**; a music bed about 8 LU under it, constant, no ducking (the owner adds music).
- SFX are **sparse and literal**: one sound per illustrated noise word or story action, not on cuts (cut-hit rate = chance). TF has
  only 2 clear SFX in 131 s; AW about 9; PN about 10; CG about 8. Non-speech transients run 10-19 per minute including music.
- Two signature hits: a **whoosh + sub-boom** on the big reveal (TF 40.85 s, CG 72.2 s) and a **whoosh + bright shimmer** on a magic
  light-up (TF 110.75-112.6 s). A short **silence beat** (music drop) before a reveal (CG 79.1, 97.5, 115.6 s).
- No whooshes on ordinary cuts.

Palette for our shorts: music-box/chime tines (magic motifs), soft whoosh, sub-boom, shimmer, creaks (wood, stone), pops and clicks
(latches, locks), small foley (feet on wet grass, door bang, ceramic clink), creature sounds (sniff, wriggle, gulp). Density: 6-12
events per minute, each on a picture event that is on screen.

EP01 hit list (times are VO word onsets from the ASR; place each on its picture event, not on the cut):

| Time (s) | Word / event | Sound |
|---|---|---|
| 1.76 | "die": dandelion clock bursts | soft airy poof + tiny chime |
| 17.68 | "out": gate latch shuts | latch click |
| 20.55 | "blinks" | ceramic "tik" |
| 30.08-30.48 | "ran out barefoot" | door bang, bare feet on wet grass |
| 35.12 | "picked him up" | ceramic clink |
| 36.96-37.28 | "the lawn MOVED" | **sub-boom + low rumble to about 39.5** (the reveal hit) |
| 40.48 | "big ones": snout unfurls | wet sniff / wriggle |
| 41.76 | "lit" | lantern tink-whoosh |
| 44.58-45.5 | "Every lantern lit" | cascade of tinks, 0.15-0.3 s apart |
| 58.87 | "Gulp" | gulp |
| 66.83-67.15 | "turned his head" | stony grind / creak |
| 83.68 | "blinked slowly" | slow, lower "tik" |
| 86.87 | "FWOOM" (ASR "Boom") | **whoosh + warm shimmer, 1.5-2 s** (the light-up hit) |
| 90.2-92.3 | "every mound sank… pair by pair" | soft deflating thumps; tiny pitched blips per eye pair |
| 99.91 | "blinked" (at Theo) | "tik" |
| 100.31-101.1 | "At Theo / from the truck" | truck engine starts |

Mix: voice continuous; master about -16 LUFS integrated, LRA ≤ 3.5, peak ≤ -1 dBFS; our raw VO is -21.8 LUFS and needs about +5 dB.

---

## 9. Gaps, approximations and risks

| Gap or risk | What the reference has | Our approximation (CHOSEN) |
|---|---|---|
| Roblox Future lighting and materials | Soft engine GI, Roblox material set, Sparkles texture, skyboxes | Coloured hemisphere + one soft key + emissives; procedural canvas materials (`ctx.tex`); sparkle sprites; procedural sky domes. Calibrate every preset with `stats.py` against §5 targets |
| Sculpted creatures (marketplace/UGC meshes with PBR textures) | High-poly sculpts | Displaced lathes and spheres, `MarchingCubes` or merged blobs baked once, `MeshPhysicalMaterial`, painted canvas textures. Biggest risk: "procedural blob" look. Mitigation: a dedicated look-dev pass on the gnome and moles (glaze, catchlights, chips, mottling) checked in close-up before any shot is built |
| UGC hair, hoods, hats | Smooth chunky meshes | Merged clumps, lathes and spheres; smooth normals; slight sheen |
| 2D clothing | Artist-painted shirts with baked folds | Canvas painting per outfit (§2.3); budget time for it, it carries the "Roblox" read |
| Cloth (duvet folds, dresses) | Real meshes | Displaced planes and pleated lathes; no cloth simulation |
| Detailed trees | Photoreal foliage meshes | Cone pines and blob trees; instanced leaf quads only for one hero tree (expensive on SwiftShader) |
| Bloom | TF shows halos; metrics measured no thresholded bloom | Low bloom (≤ 0.15) on emissives + additive halo sprites; raise only for magic beats |
| Grade | Roblox ColorCorrection plus the editor | `post.grade` presets (§6.2); ACES can desaturate saturated pastels, so check saturation 0.45-0.6 and pastel channels allowed to hit 255 while luma stays ≤ 235 (M §3a) |
| 40-48 fps judder, 540-720p detail | Present in TF, AW, CG | Not copied: true 60 fps. Render at `quality=fast` (scene 810x1440, upsampled): it already exceeds the reference detail, looks closer to their softness than a razor-sharp 1080p, and saves about 40% render time (about 52 min for 6,790 frames with 3 workers) |
| Shadows on CPU | Soft engine shadows | One shadowed light per shot at most, only in dusk/dawn/day exteriors; blob contact decals elsewhere; never point-light cube shadows except one hero lantern shot |
| Units | — | The engine demo is in metres (`STUD = 0.32`); the look-dev kit is in studs. Build in studs inside a group scaled 0.32 so lights, fog densities and camera distances stay in metres |
| Script vs references: night sky | The script asks for a "high-key lavender and pink sky, never dark navy"; all four references use black or violet-black night skies | TF galaxy sky (black to deep violet with magenta nebula, never flat navy) and a lifted subject: night lawn close shots at mean luma 75-100 (P1 with hemi 1.3). The lawn, gnomes and houses carry the lavender, not the sky |
| Script vs references: focus pull | The script asks for a rack focus at line 42 (hero's face → Theo's window) | No DOF in any reference. Do it with a camera move (pan or push from the gnome to the window) or a cut. If the owner insists, it is the single DOF use in the episode (`dof.aperture` ≤ 10 px) |
| Script vs references: caption pop | The script says "the caption pops" on stress words | TF and PN have no pop; follow TF unless the owner asks for CG's 1-frame pop |
| Script vs references: gnome size | "Knee-high" (about 1 stud) | 2.0 studs so it reads in medium shots (TF fairies are 0.4-0.6x the kid) |
| Gold "only family" shimmer outline | CG uses a Roblox Highlight outline once | Inverted-hull outline (BackSide, scale 1.03, gold #ffd27a, additive) on the hands and gnome + a few gold sparkles; 1-2 shots only |
| B&W flashback | Not in the references (AW has a warm flashback only) | `bw` grade, same lighting; keep it short (2-4 shots) |
| Timing accuracy | ASR word times are quantised to 80 ms (±40 ms) | Snap cuts to the waveform onset when a cut word starts with a plosive; check the edit against the VO at 60 fps before rendering |
| Render time | 6,790 frames | `fast` preset: about 52 min with 3 workers; `final` about 88 min; shadows and many point lights are what break the budget |
| Copyright | The references' characters and assets | We copy construction, look and grammar only; all designs, names, signs and posters are our own |

Top risks, in order: (1) the creatures look procedural instead of sculpted; (2) the grade drifts from the targets shot to shot (run
`stats.py` on one still per shot); (3) the cut list drifts off the words; (4) set dressing too sparse in close-ups; (5) render time if
shadows or point lights multiply.
