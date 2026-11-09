# EP01 "Never Move Grandpa", first cut: picture review (art director)

**File reviewed:** `scratchpad/rbx/ep01/final/ep01_clean_1080p60.mp4`

- 6798 frames, 113.3 s.
- The captioned copy was checked only for where captions sit over faces.
- `scratchpad` is `/tmp/claude-0/-home-user-claude-todo-demo/353ac1d9-152b-55bb-bdf1-0625e0fc6a83/scratchpad`.

**Judged against:**
- the approved test, `scratchpad/rbx/test5/out/test5_clean_1080p60.mp4`;
- the four references, mainly Tooth Fairies (TF);
- `board.md`, `timeline.json`, `docs/VISUAL_BIBLE.md`, `docs/STORYBOARD_RULES.md` and `test5_review.md`.

**What I looked at:**
- The contact sheet, and all 97 mid-shot frames in `final/frames/`, viewed as 3x2 tiles.
- About 40 extra frame strips at cuts, effects and character moments, for these shots: s08, s13-s15, s16, s17, s18, s23, s25, s28, s30, s35, s37, s38, s40, s46, s48, s49, s51, s55, s56, s60, s63-s64, s70, s75, s77, s81, s82, s86, s88, s89 and s97. The first and last frames were checked for the loop.
- Full-resolution crops of these moments:
  - the tear (s30);
  - the face seam (s31, s84, s87);
  - the mirrored sign (s57);
  - the gnome's eye (s89);
  - the photo (s90).
- Per-frame luma and saturation for all 6798 frames, in `review_picture/stats_shots.json`, using the same metrics as `lookdev/tools/stats.py`: mean, p1, p99, saturation, clip and crush.
- 8 TF frames side by side with ours.
- 12 captioned frames.

**Notes and evidence:** `scratchpad/rbx/ep01/review_picture/`. It holds:
- `g/` (the tiles);
- `st/` (the strips and crops);
- `cap/capgrid.jpg`;
- `ref/cmp1.jpg` (TF compared with ours);
- `stats_shots.json`;
- `shots_compact.txt`.

## Verdict

**Not ready to show as "the whole episode at test quality".**

What already works:
- The edit is frame-exact.
- The approved shots s01-s05 are preserved. s01-s05 match the test at PSNR 46-56 dB, which is encode-level only.
- The gnome is still the premium model.
- The sign inserts, s13-s14, the blinks and the sepia callbacks all work.

The second half falls apart on four systemic problems:
1. **The "fence of light" never reads as light** (blocker B1).
2. **The FWOOM climax:**
   - It whites out the frame, then goes dark and muddy olive instead of TF's warm glow (blocker B2).
3. **Most night exteriors are too dark, crushed and oversaturated against the approved s09:**
   - The bedrooms are milky instead (M2, M3).
4. **Kit-level cheap tells in every close shot:**
   - a hard shading seam down the middle of every R6 face (M1);
   - a hug pose with splayed arms and a floating gnome (M7);
   - mirrored sign text (M5);
   - moles that read as pink daisies (M6).

On top of that, about a dozen individual story beats are unreadable at a glance (section 3).

Fix order: section 5. Re-render only the shots that are touched.

---

## 1. Blockers

### B1. The lanterns and the ring of light do not read as light

**Shots:**
- s39 41.95-43.50
- s40 43.50-45.43
- s43 47.62-48.52
- s46 51.57-53.68
- s56 62.57-64.10
- s57 64.10-65.43
- s69 77.37-78.67
- s70 78.67-79.72
- s81 92.50-94.07

**Problem:**
- **The ring is not light.** It renders as a pale straw/khaki disc with a thin cream rim. It looks like dead grass or a crop circle, not a warm pool.
  - `lanternRing` uses a boost blend that multiplies the grass albedo, which desaturates it.
  - s39 averages rgb [65,69,99], which is cool. s81 averages [56,61,93].
- **s40 (the cascade):** "Every lantern lit" is unreadable at 1080 px.
  - The street gnomes are about 40 px tall.
  - The pops have no halos.
  - The camera barely moves (push 0.1). STORYBOARD_RULES 6.2 planned a 1900 px/s truck along the kerb.
- **s43:** "They're the fence" shows separate pale discs, not an unbroken chain. The frame mean is 47.
- **s70:** the callback to s09 ("every lantern lit now") shows no lit lantern at all.
  - The hero, backlit and with a black face, blocks Theo's window.
- **s69:** the "gold lantern light on the glass" is missing. The window is plain lavender.
- **s81:** the quiet wide has no warm focal point.
  - The bible (§5) says the subject is the brightest thing in a night frame.

This is the episode's central metaphor. TF and PN make it with saturated warm pools and halos.

**Fix:**
- `kit/fx_ep01.js` `lanternRing`:
  - Keep `boost` for the blade lift, but add an **additive** warm pool: `innerA` 0.06 → 0.30, inner `#ffb060`.
  - Soften the edge: `falloff` 0.6 → 1.6 studs, `rimA` 0.55 → 0.25.
  - Add a `tex.radialGlow` decal `#ffb870`, opacity 0.35, at 1.2x the radius (bible P1 "warm ground pool").
- Every lit lantern in a wide gets a halo sprite of 60-90 px and a 3-4 cd point light (P1).
- **s40:** re-block as board 6.2.
  - Camera low along the kerb (h 1.5 studs), fast truck 1900 px/s.
  - Lanterns pop toward the lens 0.15-0.3 s apart. Each pop has a `sets.burst` (count 12, ringPx [30, 220], 0.3 s).
  - The nearest lantern pops on "lit" (f2713) and fills the foreground.
- **s43:** make the rings overlap: radius 5 → 7 studs, or gnomes no more than 12 studs apart. Brighten the rim.
- **s70:**
  - Set `setLantern(1)` and add halos on all family gnomes.
  - Move the hero 1 stud left of the window axis so the lit window and the sleeping shape stay visible.
  - Give his face a warm under-key from the lantern.
- **s69:** add a `warmKey` of `#ffb85c` 2 cd outside the glass, plus a gold radialGlow on the pane.
- **s81:** lantern level 1, an 80 px halo and a visible ring pool.
  - Target: the gnome is the brightest element and the frame mean is at least 70.

### B2. The climax (s77-s80, 86.77-92.50) is a whiteout, then dark and muddy

**Problem:**
- **s77, the whiteout:** frames f5215-5231 wash out to milky cream, and the frame mean swings by 97.
  - The whiteout comes from the burst core plus the light wall passing the lens.
  - It snaps clear in one frame at f5232. The bible (P3) says "no white flash frames".
- **s77, the flare:** the lantern is tiny, behind the beard and a white tulip at frame left, so the flare itself is never seen.
- **s78-s80, the warm grade:** the P3 warm grade never arrives.

  | Shot | Mean (target 130-150) | Saturation (target 0.40-0.50) | Average rgb |
  |---|---|---|---|
  | s78 | 72.8 | 0.67 | [102,67,48] (olive-brown) |
  | s79 | 83.7 | 0.67 | [110,80,38] (olive-yellow) |
  | s80 | 36.4 | 0.68 | — |

  - s80 is the darkest exterior in the cut.
  - The warm grade turns the green lawn olive instead of peach or rose.
  - TF's magic beats (for example 109.75 s) are bright peach-lavender with dense, big, soft sparkles.

**Fix:**
- `engine/episodes/ep01/part5.js` `fwoom_flare`:
  - Add `nearFade(F.wave.group, 0.7, 2.4)` right after `X.fwoom(...)`, as s78 already does.
  - `sets.burst` b1: `corePx` 220 → 90, `ringPx` [60, 900] → [60, 520], `brightness` 2.0 → 1.4.
  - `clearPlants` second radius 0.22 → 0.45, to remove the white tulip in front of the lantern.
  - Camera yaw -15 → -25 so the lantern sits near the centre line. Bloom 0.4 is then allowed on it.
- s78-s80:
  - `magicGlow` exposure 0.95-1.0 → 1.25; hemi intensity 0.5-0.7 → 1.2 (`#ffcdb8` / `#5a2030`).
  - Grade `magic` saturation → 0.85, highlights `#ffdcc4`, so the grass goes peach rather than olive.
  - Add 20-40 gold and pink motes per frame (P3).
- **s80:** change the magic→night blend from 1 → 0.4 to 1 → 0.7, and raise exposure until the mean is at least 70. The eye pairs still read against a lit lawn.

## 2. Systemic majors

### M1. Shading seam down the middle of every R6 face

**Where:**
- Clear in s31, s58, s65, s74, s84, s87, s94 and s97 (crops in `st/s31_face.jpg`, `st/crops2.jpg` and `st/seams.jpg`).
- Visible in every human close-up.

**Problem:**
- One half of the face is lit and the other darker, with a hard vertical line through the nose position.
- `kit/avatar.js` `headGeo` is `new THREE.LatheGeometry(headProfile(), 48)` with phiStart 0, so the seam lies at +z, which is the face.
- `computeVertexNormals()` then splits the normals across the duplicated seam vertices.

**Fix:**
- Use `new THREE.LatheGeometry(headProfile(), 48, Math.PI)`, which moves the seam to the back of the head.
- Drop the `computeVertexNormals()` call: the lathe already writes analytic normals.
- Note: this also changes the approved s02-s04 faces, but only by removing the line. Ask the owner, or gate it behind an option for those builders.

### M2. Night exteriors are too dark, crushed and oversaturated, and swing within one scene

**Reference points:**
- Approved s09: mean 87.5, saturation 0.43, crushed 7.6 %.
- Bible P1: mean 60-95 (lawn close shots 75-100), saturation 0.45-0.6, crushed ≤ 25 %.

**Off target:**

| Shot | Mean | Sat | Crushed |
|---|---|---|---|
| s29 (the thumbnail frame) | 49.8 | 0.73 | 40 % |
| s34 | 55 | 0.61 | 25 % |
| s37 | 59 | 0.60 | 24 % |
| s38 | 55 | 0.68 | 29 % |
| s41 | 57 | 0.72 | — |
| s42 | — | — | 35 % |
| s43 | 47 | 0.73 | 27 % |
| s46 | 56 | 0.61 | 24 % |
| s48 | 21 | 0.79 | 58 % |
| s57 | 58 | 0.65 | 29 % |
| s58 | 52 | 0.69 | 40 % |
| s81 | 62 | 0.61 | 24 % |

**Swings within one scene:**
- The gate scene goes s29 50 → s32 117 → s34 55.
- s46 is 56, then s47 jumps to 125.

**Cold faces:** night faces go lilac. Examples: the s97 narrator, the s31 hero, and the s38 head behind the gnome. TF keeps salmon skin inside its cool grade.

**Fix:**
- Per builder: `nightRig`/`H.ep01.light` hemiIntensity 1.0 → 1.3 (bible "high-key lawn"), exposure +0.2 EV.
- Night grade saturation 1.12 → 1.0 on exteriors.
- Use `GALAXY_LOW` on every low-angle shot.
- Add a `warmKey` face light (as in the approved s02-s05) on every human close-up.
- Tone down the property-line haze in s32 and the lantern haze in s47 so they sit with their neighbours.
- QA gate per shot (mid-frame `stats.py`): mean 70-95, saturation ≤ 0.6, crushed ≤ 15 %.

### M3. Night interiors are milky, look like day, and lift their blacks

**Problem:**

| Shot | Mean | p1 | Sat |
|---|---|---|---|
| s44 | 155 | 50 | 0.32 |
| s55 | — | 38 | — |
| s69 | — | 48 | — |
| s71 | — | 50 | — |
| s72 | — | 35 | — |

- Bible P2: mean 105-125, p1 5-20.
- No night feeling at all.

**Fix:**
- `I.bedroomNight`: hemiIntensity 1.3-1.45 → 1.0, contrast 0.95 → 1.05, keep outBlack `#140507`.
- Make the lamp and nightlight the visible sources.
- The window view must be darker than the room (P2).

### M4. s17, 19.35-20.23 ("I say goodnight"): daylight outside a night window

**Problem:**
- Through the glass the lawn and fence are lit like an overcast day. s18, the next shot, is a starry night.
- Cause: the `bedroomNight` hemisphere at 1.45 lights the exterior too.

**Fix, in `part1.js` `goodnight_window`:**
- Put a night-tint plane on the outer side of the glass: `MeshBasicMaterial` `#0d0b2a`, opacity 0.55, `depthWrite:false`.
- Glass: `color #2a2450`, opacity 0.7 → 0.5.
- Keep `lanternOutside` 2.6 cd so Grandpa still reads.
- Also (minor): the wave is a forward arm rocking at chest height, which reads as knocking on the glass. The bible's wave is the arm up at 160°.

### M5. Mirrored text and continuity on the agent board and the price sticker

**Problem:**
- In s57 (64.10-65.43) the board is seen from behind and shows mirrored "FOR / 3 BED · / COMES W" (crop in `st/s57_sign.jpg`).
  - The back face carries the front texture, and the SOLD sticker, which is front-only, is missing.
  - s28 and s31 show the front correctly ("…ALE" plus the SOLD sticker; `st/signs.jpg`).
  - In s28, however, it is the agent board that looms at frame left, where the board planned the KEEP OFF sign (minor).
- The `$4.99` flutter sticker reads mirrored, "ɘɘ.4$", at s51 f3563-3579.

**Fix:**
- `kit/props.js` `addAgentBoard`: change the material array from `[edge, edge, edge, edge, face, face]` to `[edge, edge, edge, edge, face, edge]`, as `addPostSign` already does.
- `kit/fx_ep01.js` `flutter`: replace the `DoubleSide` plane with two `FrontSide` planes. The front uses `stickerTex`; the back is plain `#f4f0ea`.

### M6. The moles read as pink daisies and dark smudges, and "dozens" fails

**Problem:**
- **s35 (37.63-38.57), "Dozens of mounds":** the crane pull-back shows 3-6 faint dark smudges and no crumbs.
- **s37 (39.95-40.97):** both snouts read as a pink daisy or sea anemone. The giant one has a face-like centre.
- **s53 (60.72-61.38):** among the tulips the snout is literally a flower.
- **s55 and s79:** dark fuzzy spots.
- The bible's hero-creature rule is out-detail and readable silhouette. Here the creature is camouflaged.

**Fix, in `kit/creatures.js`:**
- Snout colour `#f6a2b0` → salmon `#f2a088`, with a darker base `#b04a68` gradient. This separates it from the magenta tulips.
- Tentacles 30 % shorter and 50 % thicker, with rounded tips: fleshy, clearcoat 0.6, roughness 0.35.
- Add a 0.35-stud cone nose between the mound and the disc, so it reads as a nose on a head.
- Raise `HEAD_AT` emerge in close-ups so the furry dome and both reflector eyes sit above the turf.
- Wriggle ±10° → ±18°.
- **s35:**
  - 30 or more mounds over three lawns, eyes on (amber pairs are what reads at night).
  - Mound height 0.6 → 0.9 studs, with a moon rim light and crumb bursts on "mounds" (f2285).

### M7. The hug pose: arms splay outward and the gnome floats untouched

**Shots:** s32, s33, s38, s45, s50, s57, s73.

**Problem:**
- `HUG = { armLx: 58, armRx: 58, armLz: -36, armRz: -36 }` in `part2.js:39`, `part3.js:44` and `part4.js:54`.
- It renders as a shrug or T-pose, with the gnome stuck to the belly.

**Fix:**
- Flip the Z signs (`armLz/armRz` → +30..+36) and set `armLx` 58 → 70.
- Check on a still that both hand sockets sit within 0.4 stud of the gnome's belly, and place the gnome between them.
- The same check applies to the avatar.js `hug` pose (`armLz -24`).

### M8. Faces and subjects sit in the caption band (y 1260-1420) of the captioned master

**Where (`cap/capgrid.jpg`):**
- s58: "tomorrow" covers his eyes.
- s74: "goodnight" covers his eyes.
- s71: "anymore" covers the hero's face in the window.
- s65: the caption covers his mouth.
- s41: "next" covers the plastic gnomes.
- s82: Theo in the doorway.

The bible (§7.1) puts faces in the upper 25-45 % of the frame.

**Fix:**
- Re-aim so the eyes sit at y 0.30-0.45:
  - s58 and s74: target +0.25 m, or pitch +6°.
  - s71: window centre at y 0.35.
- s41: camera height 4 → 6 studs, pitched down so the gnomes sit at y 0.45-0.6.
- s82: camera height 1.2 → 3 studs, so Theo is at y ≈ 0.45 and the bottom 45 % of empty grass goes.

### M9. The "heartfelt" face reads as smug, on the tenderest lines

**Shots:**
- s31 "Come on, then"
- s71
- s74 "I said goodnight"
- s85 "Say goodnight"

**Problem:** the thick lid arch (`quad(x-30,236 → x,218 → x+30,236)` in `kit/faces.js` `heartfelt`) sits on top of the irises, with lashes at the outer corners. The result is half-lidded, "sultry" eyes.

**Fix:**
- Lift the arch clear of the iris: ends y 236 → 224, apex 218 → 204.
- Add soft brows raised at the inner end (worried-tender): `quad(x∓28,196 → x,184 → x±26,190)`.
- Smile arc r 52 → 58.
- Alternatively, use `content` for s74 and `wetEyes` for s31.

## 3. Shot-level majors (story beats that do not read)

| Shot | Time | Problem | Fix |
|---|---|---|---|
| s25 `sold_truck_dusk` | 26.55-27.80 | The SOLD slap (f1652, about 90 px), the truck and Theo at the fence all sit in a thin band at 45-62 % height. The bottom 40 % is asphalt (bottom-quarter luma 15). "BALCONY GNOME" is not visible. | Camera height → 2.5 studs, fov 60 → 42, target between the board and Theo. Punch-in x1.3 on "moved" so the SOLD sticker is at least 250 px. Put the box label toward the lens. |
| s29 `gate_truck_thumb` | 31.45-33.20 | The thumbnail frame: mean 50, 40 % crushed. The truck is an anonymous white slab at frame right, and the upper 45 % is empty sky. | Use the M2 lift. Pan 10° right so the truck's open back (dome light on, box readable) fills the upper-right third. Crane down so the sky is under 25 %. |
| s30 `gnome_tear` | 33.20-34.35 | The tear on "with" (f2040) is a tiny white bead at the outer edge of the cheek, lost against the white beard (`st/crops2.jpg`). | `fx_ep01.dewTear`: colour `#e6f2ff` → `#8fd0ff` (bible tear blue), opacity 0.6 → 0.9, size 0.34 → 0.5, glint px 15 → 40, dur 0.6 → 1.0. In `part2.js:242` choose the eye whose path runs over the ruddy cheek, and keep the path dx under 0.2 so it stays in front of the beard. |
| s33 `gold_arms` | 35.60-36.70 | The hero's face is cut by the top edge at the eyes. The arms are not round the gnome (M7). | Frame from the chin down (target -0.3 stud) or the full head. Apply the M7 fix. |
| s46 `take_window_dark` | 51.57-53.68 | On "dark" (f3186) Theo's window only drops from luma 127 to 100 and stays lavender. The hero is cut by the right edge, and the mounds gliding in are not readable. | `X.windowDark`: glass → `#0d0b22`, room and nightlight to 0. Window at x ≈ 0.35, hero at x 0.55-0.8. Give the two mounds eyes on and a lit rim. |
| s48 `truck_clock` | 55.25-56.33 | The sticky note "LEAVE 6 AM" is cut by the left edge for the whole shot ("EAVE / AM"). A stray Roman-numeral clock face ("XI") sits at top left. Mean 21, 58 % crushed. | Centre the note and the clock (target 0.15 m left), fov 45 → 40, remove the stray dial, dashboard glow 1 → 2.5 cd. |
| s49 `balcony_box` | 56.33-57.87 | The label is cropped ("ALCONY NOME"). The lids pop open in one frame (f3396 → f3404) with no cover. The plastic gnome flips 90° and exits frame right. The background is a flat lavender void, so the "truck ramp" does not read. Grandpa and his lantern are absent. Jump-detector hits f3414-3418 are the hero's hair intruding at top left. | Centre the box with a readable label. Open the lids over 6 frames on RIP (f3398) under a dust puff. Lift the gnome upright toward the lens. Ground plane = ramp planks. Grandpa under the arm at frame left with a lantern halo. Keep the hair out of frame (camera +0.5 stud). |
| s55 `eyes_fog_glass` | 61.92-62.57 | Theo is not in the frame (only the duvet and pillow). The amber eyes do not read, the fog barely shows, and the window shows pink "daisies". | Theo's sleeping head on the pillow in the lower-third foreground. Eyes 0.22 → 0.35 stud, emissive 5, 40 px halo, centred in the pane. `glassFog` opacity x2. |
| s60 `away_to_window` | 67.38-69.07 | Before the whip, the hero's face is half out of the frame at top right. After the whip, Theo is a few pixels behind the mullion. | Hero face at x 0.5-0.8, y 0.2-0.4. Land the whip with Theo's head clear of the muntin bars (window target 0.3 stud left). |
| s63→s64 | 70.90 (f4254) | Known: in the same top-down framing, Grandpa jumps from the bottom of the lap to the kink. Also, the crane-down path passes through the porch roof and post at f4262-4290, so white beams sweep across and the subject is lost for 0.5 s. | `fb_lap` (callback s63): phase-shift the walker so he reaches the kink on s63's last frame. In `fb_one_stop`, offset the crane path 3 studs toward the lawn, or hide the porch roof meshes for this shot. |
| s70 `lawn_stare_lit` | 78.67-79.72 | The payoff of the s09 callback: no lantern is lit, the hero's face is black, and he blocks the window. | See B1. |
| s71 `big_in_window` | 79.72-80.87 | "I wasn't small anymore": the hero is small and far, framed by curtains, so the idea of him now being big is lost. His face sits in the caption band (M8). | Camera 1.5 studs inside the glass. His face pressed to the pane, filling about 60 % of the window width, eyes at y 0.35. Theo's sleeping head small in the lower foreground. |
| s86 `theo_blink_twoshot` | 98.58-100.35 | The payoff blink (f5993-5994, on the frame) happens on a half-cropped eye at the left frame edge. | Yaw so both gnome eyes are in frame at x 0.12-0.45, Theo at x ≈ 0.65. |
| s89 `grandpa_turned` | 102.60-103.43 | A hot-pink blob covers the gnome's right eye from f6156 to f6183, during the head yaw of 160°. Theo's torso fills the left 40 %, cut by the edge. Theo's window shows sky and horizon through the house (no room behind the glass). Nothing tells us this is from the truck. | Render a still of f6160 with `lidL`, `lidR` and `cheek` hidden one at a time to find the mesh, and reduce yaw 160 → 120. Theo half a stud further left, out of frame or behind the gnome. `dawnLot` must build Theo's room (`theoRoom: { lit: false }`). Keep the ±3 px vibration but add a slow truck drift. |
| s97 `final_window` | 111.78-113.30 | On "window" (f6761) the dandelion puff has no picture: 14 seed sprites of 14-26 px, with the dandelion out of frame. The loop motif and its POOF_SOFT sound play over nothing. The face is lilac-grey (the 2.8 cd warm spill does not land), and the moon is cut at the top-left edge. The loop framing against f0 is otherwise good. | Seeds 24 at 40-70 px, spawned in frame at bottom left and drifting across his face. Warm point 2.8 → 5 cd, or move it to 0.6 m. Moon az -16 → -10. |

## 4. Minors

| Shot | Time | Problem | Fix |
|---|---|---|---|
| s08 | 5.03-7.17 | "Sunrise" does not read: no sky, flat midday green, mean 121 against the dawn target of 135-150. The grandkid's face is turned away (only a closed-eye arc shows) and the red cap reads as a helmet. | Lower the camera and show the pink dawn sky in the top third. Turn the kid 3/4 toward the lens; cap → hair. |
| s15 | 16.77-17.92 | The gold outline is on the gnome, not on the grown-up's hands (board). | Apply `X.goldOutline` to Dad's arm meshes too. |
| s16 | 17.92-19.35 | The "spring day" is dim (mean 87, day target 110-155). The wall lamp is lit in daylight. The tapping arm crosses his face and reads as scratching his head. | Sun on the house front, wall lamp off. `armRx` about 70 toward the hat tip, below his eye line. |
| s19 | 20.97-23.00 | Grandpa's head covers the KEEP OFF sign text. | Sign 1 stud left, or the walk path 1 stud nearer the lens. |
| s21 / s62 | 23.55-23.98 / 69.60-70.30 | "Slippers" are unreadable: a grey leg box with a one-pixel tartan stripe. | Pants texture: bottom 0.3 stud as a bold red/green tartan band, plus a slipper cuff box at 1.05x. |
| s23 | 24.52-25.97 | The lower half of the frame is two arm boxes seen end-on, with mismatched textures, plus the torch pointed at the lens. | Arm R about 150° (forearm up), camera +0.5 stud, torch head just under the chin. |
| s34 | 36.70-37.63 | Stray yellow and white discs on the lawn read as litter. The hero is at the left edge. | Remove them, or turn them into the planned crumbs. |
| s38 | 40.97-41.95 | A soft out-of-focus glow disc at frame left (f2458-2503). | Remove the halo sprite or the lamp behind the lens. |
| s42 | 46.30-47.62 | The street gnome wears round glasses (Grandma's motif), and 35 % of the frame is crushed. | Remove the glasses. Apply the M2 lift. |
| s44 | 48.52-50.15 | Theo's intro: his face is rotated 90° and cut at the left, and the whale is not visible. The frame is milky (M3). | Head at x 0.3-0.7, whale under his arm in frame. |
| s45 | 50.15-51.57 | The lit gnome is hidden behind the hero's body, which defeats the shot. | Yaw 25° so the gnome and its lantern show on his near side. |
| s47 | 53.68-55.25 | Milky lantern haze (mean 125, double s46's). | Reduce the halo/glow so it matches its neighbours. |
| s50 | 57.87-58.85 | The hero is cut by the right edge and his head hidden behind his arm. | Camera yaw -12°. |
| s59 | 66.35-67.38 | The frame is mostly belly. The turned head reads, but the eye looks closed in profile. | Raise the target 0.1 m. |
| s64 | 70.90-72.83 | The flashlight "resting on the lawn" is not visible. | Put the beam pool in frame at bottom left. |
| s66 | 74.02-74.90 | The 5-year-old's head is cut by the right edge. | Bed 0.3 m left. |
| s68 | 76.40-77.37 | The 1990s girl is about 60 px, unreadable. | Push 0.18 → 0.3, or move the bunk to the window. |
| s73 | 81.62-82.60 | The hug pose (M7). | — |
| s75 | 83.40-85.18 | The lids are already half-closed before the blink (f5017), so the "sorry" settle at f5084 is not a change. | Lids open (0) until f5084, then 0 → 0.3 over 8 frames. |
| s76 | 85.18-86.77 | The hero's hair fills the top 30 % of the frame. | Camera +15° pitch toward the gnome, or hide the hair. |
| s82 | 94.07-95.87 | Theo in the caption band, 45 % empty grass (M8). | — |
| s85 | 97.22-98.58 | The hand on Theo's shoulder does not read: the arm points at the lens. "Heartfelt" reads smug (M9). | Arm `armLz` toward Theo's shoulder, camera yaw 20°. |
| s87 | 100.35-100.82 | "At Theo": the same "o" face as s83, so there is no new delighted decal. | Use `openSmile`, or the red-o shock face. |
| s88 | 100.82-102.60 | The gnomes are about 20 px, so which way they face is unreadable. Theo is not visible. | fov 70 → 50, lower the camera to lawn height. Theo by Grandpa in frame. |
| s90 | 103.43-104.98 | In the photos Theo has orange-brown hair and a beard (10th and 34th springs). Theo is blond. | `photoTex`: Theo's hair `#e6b54a` until it greys. |
| s91 | 104.98-106.23 | The phone floats beside the hand box. A ghost duplicate "Theo" sits behind the notification text. | Parent the phone to the hand socket. Remove the duplicate label. |
| s93 | 108.27-109.15 | "60th spring" on the photo is cut by the frame bottom, and the mid-blink lids are unreadable at this size. | Target 0.1 m down. Lids 0.55 with a 60 px star glint. |
| All night and magic shots | — | Sparkle density is well under TF: 2-6 small glints per frame against TF's 8-20 big soft ones. | `sparks()` counts to 8-12 outdoors and 12-20 indoors and at magic sources, at 40-80 px (bible §6.3). |

## 5. Per-shot pass (all 97)

OK = no picture defect beyond the systemic notes in brackets.

| Shot | Verdict | Shot | Verdict | Shot | Verdict | Shot | Verdict |
|---|---|---|---|---|---|---|---|
| s01 | OK (approved) | s26 | OK, clock reads 9:00 | s51 | OK, M5 sticker | s76 | minor |
| s02 | OK (approved) | s27 | OK | s52 | OK | s77 | **B2** |
| s03 | OK (approved) | s28 | OK, run reads (agent board instead of KEEP OFF, minor) | s53 | M6 | s78 | **B2** |
| s04 | OK (approved) | s29 | **major** + M2 | s54 | OK | s79 | **B2**, M6 |
| s05 | OK (approved) | s30 | **major** (tear) | s55 | **major** | s80 | **B2** |
| s06 | OK | s31 | M1, M9 | s56 | **B1** | s81 | **B1** |
| s07 | OK, jump cut works | s32 | M7, M2 jump | s57 | M5, M7, M2 | s82 | M8, minor |
| s08 | minor | s33 | **major**, M7 | s58 | M8, M2 | s83 | OK |
| s09 | OK (approved) | s34 | M2, minor | s59 | minor | s84 | OK (M1) |
| s10 | OK, board reads | s35 | **M6** | s60 | **major** | s85 | M9, minor |
| s11 | OK | s36 | OK, eyes read | s61-s63 | OK, callbacks exact | s86 | **major** |
| s12 | OK | s37 | **M6** | s64 | **major** | s87 | minor (M1) |
| s13 | OK | s38 | M2, M7, minor | s65 | M8, M1 | s88 | minor |
| s14 | OK, strong | s39 | **B1** | s66 | minor | s89 | **major** |
| s15 | minor | s40 | **B1** | s67 | OK | s90 | minor |
| s16 | minor | s41 | M8, M2 | s68 | minor | s91 | minor |
| s17 | **M4** | s42 | minor | s69 | **B1**, M3 | s92 | OK |
| s18 | OK, blink f1233-1234 on the word | s43 | **B1**, M2 | s70 | **B1** | s93 | minor |
| s19 | minor | s44 | M3, minor | s71 | **major**, M3, M8 | s94 | OK (M1) |
| s20 | OK | s45 | minor | s72 | M3 | s95 | OK |
| s21 | minor | s46 | **major**, B1 | s73 | M7 | s96 | OK, mirror of s06/s07 |
| s22 | OK | s47 | minor | s74 | M9, M8, M1 | s97 | **major** |
| s23 | minor | s48 | **major**, M2 | s75 | minor | | |
| s24 | OK | s49 | **major** | | | | |
| s25 | **major** | s50 | M7, minor | | | | |

**Keep:**
- The frame-exact edit.
- s10, s11, s26, s91 and s92 (text inserts).
- s13 and s14 (the gate bonk ripple).
- s18 and s86 (the blink frames are exact).
- s20-s22 = s61-s63 (callbacks are identical).
- s24, s65, s67, s83, s84 and s94.
- The s95/s96 mirror of s06/s07.
- The dawn palette of s83-s87.
- The loop match: f6797 and f0 have the same face position and size.

## 6. Fix order and re-render

1. **Kit fixes:** each one clears many shots at once.
   - avatar head seam (M1);
   - `addAgentBoard` and `flutter` back faces (M5);
   - `lanternRing` additive pool and the lantern halos (B1);
   - HUG signs (M7);
   - `dewTear` (s30);
   - mole snout and mound (M6);
   - `heartfelt` lids (M9).
2. **Lighting and grade lifts:** the night exteriors (M2), the bedrooms (M3), s17's window (M4) and the s77-s80 magic block (B2).
3. **Per-shot reframes** from section 3, and the caption-band re-aims (M8).
4. **Re-render** the touched shots with `render.js` from/to and resume:
   - The systemic fixes touch roughly f1161-f6798.
   - The approved s01-s05 and s09 are untouched, except the M1 seam, which needs owner sign-off.
5. **QA gate before the next mux:**
   - `stats.py` per shot: night mean 70-95, saturation ≤ 0.6, crushed ≤ 15 %; bedroom p1 ≤ 20; magic mean ≥ 120.
   - No frame-to-frame jump over 15 inside s77.
   - A captioned-frame check that no eyes sit in y 1260-1420.
