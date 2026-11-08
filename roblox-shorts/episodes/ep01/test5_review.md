# EP01 5-second test: art-director review against the four references

Reviewed file: `scratchpad/rbx/test5/out/test5_clean_1080p60.mp4` (and the captioned copy). 300 frames, 1080x1920, 60 fps.
(`scratchpad` = `/tmp/claude-0/-home-user-claude-todo-demo/353ac1d9-152b-55bb-bdf1-0625e0fc6a83/scratchpad`.)

**What I looked at:**
- All 300 frames, as tiles of every 5th frame plus every frame around the 4 cuts, the glint and the snap.
- The contact sheet and the five compare sheets.
- 30 reference frames chosen to match our shot types:
  - TF: 0.3, 2.3, 25.6, 33.4, 34.5, 36.2-36.4, 42.8, 47.5, 48.8, 76.0, 77.0, 99.9, 106.8, 107.5, 109.75, 122.8 s
  - PN: 1.0, 2.5, 29.3, 41.0, 53.2, 54.8, 58.9 s
  - AW: 5.0, 10.2, 67.0 s

**What I measured:**
- `lookdev/tools/stats.py` on 13 of our frames and 14 reference frames.
- A hue histogram, plus skin, decal and gnome colour samples.
- DIS optical flow with a RANSAC similarity fit on every frame pair (push, linearity, drift, stalls).
- Caption glyph boxes.
- Loudness per 100 ms of the mix and its stems.

The review sheets and crops are in scratch only (`scratchpad/rbx/test5/review/`, e.g. `sheet_a.jpg` to `sheet_g.jpg`, `ref_a.jpg` to `ref_c.jpg`, `pair_s02_s04.jpg`, `burst.jpg`, `s05_crop.jpg`, `motion.json`). Reference frames never go in the repo.

## Verdict

**The test is not ready to show as "this is the TF look".** The base is right:
- the night-street grade numbers match the TF aerial;
- the R6 bodies and decal faces are correctly built;
- the gnome is the most detailed thing on screen (glossy domed eyes, veins, glaze);
- the timing is frame-exact, the pushes are linear and the 60 fps is clean.

The owner will still say "this doesn't look like the references", for five visible reasons:
1. **The transformation shot (s04) does not show its payoff.** Two tiny gnomes sit at the frame edges of an empty bench.
2. **Every face and creature is purple.** Skin and the gnome's ruddy colours land in the magenta-violet range. TF keeps warm salmon skin against a cool set.
3. **The porch shots (s02-s04) read as a bright daytime room.** There is no night visible, the lantern is unlit and a pink-white window dominates. The couple is framed at the edges with their legs as dark boxes.
4. **Frame 0 is 89.5 % black sky.** TF opens on a bright creature close-up with a snap pull-back.
5. **The "magic" does not look like TF:**
   - The sparkles are small thin asterisks.
   - The poof is a milky fog that lifts the whole frame by 34 luma points, with the swap visible through it.
   - The warm magic grade never appears.
   - The last 1.56 s are a near-static silent hold.

Fix the blocker and the eleven majors below and re-render. The minors can ride along.

---

## Ranked defects (most damaging to "looks like the references" first)

Severity: **blocker** = the owner rejects the look on this alone; **major** = clearly visible "not like TF"; **minor** = polish
or a rule mismatch few viewers notice.

### 1. BLOCKER: s04 (2.10-2.92 s, f126-174): the transformation payoff is unreadable

**Problem:**
- The camera is 7.4 studs out and 20° front-left, with low framing. The couple sits at the extreme left and right frame edges, and Grandma's head touches x = 0.
- After the snap (f134) the two gnomes stand about 1,000 px apart. They are about 10 % of the frame width each, at x ≈ 20-60 and 190-230 on a 270-wide tile.
- The frame centre is empty swing slats and the window.
- The deck fills the bottom 35-40 % of the frame.
- TF's transformation and pose-pop shots (TF #29 36.3 s, #96 109.7 s) are MCU/ECU with the subject filling the centre.

**Fix:**
- Re-frame s04 as a centred MS. Camera yaw -20° → -6°, `R` 7.4 → 5.2 studs, y = deck + 2.6, target = seat centre at deck + 2.9.
- Place the gnomes together in the centre after the snap: in `porchScene({gnomes:true})` set `ggm.position.x = -1.05`, `ggp.position.x = +1.05` (not ±`SEAT_X`). Turn them 15° toward each other (`ggm.rotation.y = +0.26`, `ggp.rotation.y = -0.26`).
- Cheat their scale ×1.35 (bible §2.6 #6: "scale is cheated per shot"), so they read at 25-30 % of the frame width each.
- Before the snap the humans then fill the frame width (heads in the upper 30 %), so the burst covers the centre of the frame.
- Keep push Z 0.20.

### 2. MAJOR: s02-s05: skin and creature colours collapse into purple, with no warm local colour

**Problem:**
- Grandma's cheeks measure #95558f to #a3597f in s03 (albedo `SKIN.peach`). Her forehead and highlight is #c68cab.
- The gnome's nose measures #995183 (albedo #e8836e "ruddy"), his face #a67fbd (albedo #f0b49a), his beard #b0a4e9 and his hat #a44973.
- Our porch close-up has 0.2 % of its pixels in the orange hue band and 44 % in purple. Its hue entropy is 1.87, against 2.3-2.5 in TF close-ups (TF 33.4 s: 33 % red, 19 % yellow, 24 % green; skin #c8705a-#efab74).
- TF keeps salmon or orange Roblox skin and saturated local colours inside its lavender grade. That is what makes "Roblox" read.
- The cause is the cool hemisphere (#8a90ff at 1.25) acting as the main light on the faces, plus the porch grade (tint +12, shadows #3a1640) and the `nightHigh` grade (temperature -18).

**Fix:**
- Give every face a warm key and let the set keep the cool fill.
- **Porch (s02-s04):**
  - In `sets.porchGlow(... subject: {...})`: colour #ffe0c8 → #ffc49a, cd 1.6 → 3.0, placed upper front-left of the heads (1.2 m up, 1.5 m out, 35° left of the lens).
  - Porch hemisphere intensity 1.25 → 0.95.
  - `PORCH_POST.grade`: tint 12 → 4, temperature -9 → -3, shadows #3a1640 → #3e1420 (TF maroon), highlights #e2c8f6 → #f0d2e0, outWhite #ddcaf6 → #e9d4ee.
- **Gnome (s05):**
  - Raise the "window spill" point light from 0.9 cd to 2.8 cd, colour #ffc08a. Move it to upper front-left of the face (az -35°, el 35°, 0.8 m from the nose) instead of directly over the lens.
  - `nightLawn` hemisphere 1.25 → 1.0.
  - Add a cool rim: `lights.sun` #8a90ff, 0.8, from behind-right.
- **Acceptance (stats on samples):**
  - human skin midtones ≥ #d8988a with R-B ≥ +35;
  - gnome nose ≥ #cc6a5e, gnome face ≥ #d8a090;
  - set whites still lavender (hi #d6b9de-#e7d4fc).

### 3. MAJOR: s02 (0.92-1.48 s, f55-88): the "grandparents" two-shot is badly composed

**Problem:**
- Grandma's head is at the left edge, with the wall lantern touching it. Grandpa's head runs off the right edge from about f70 as the push proceeds; at f85-88 it is cut by about 30 %.
- The two R6 bodies (4 studs wide each, arms touching, `SEAT_X` 2.0) merge into one purple-blue slab, so "holding hands" is invisible.
- The seated legs point straight at the lens as near-black boxes (lo #14011a) and fill the lower centre. They read as ottomans.
- PN never frames seated R6 legs head-on. PN 2.5, 29.3 and 41.0 s are 3/4 views with a white spindle railing across the lower third hiding the legs, one person per frame.

**Fix:**
- Camera yaw 28° → 42°, height deck + 4.65 → deck + 5.8 (about 8° down), `R` 7.4 → 8.0, target the midpoint between the two heads (not the swing centre), fov 70. This foreshortens the legs and keeps both heads inside x 90-990 for the whole +19 % push.
- Yaw the riders toward each other: `gm.rotation.y = +0.21`, `gp.rotation.y = -0.21`.
- Put a porch railing section (white spindles, 3 studs high, `sets` porch rail) 2-2.5 studs in front of the swing, so it crosses the lower 30 % of the frame like PN 2.5 s.
- Give Grandpa's trousers the cast's grey (#6a6470): the leg fronts render black because the only light comes from above. The warm front key from defect 2 also fixes this.

### 4. MAJOR: s01 f0 (0.00 s): the hook frame is a black sky

**Problem:**
- Frame 0 is 89.5 % crushed (L < 4), with mean #03020d: a starfield with a small moon and a roof tip.
- TF's frame 0 is a bright ECU of the creature with a snap pull-back x10 (TF #1, bible §7.4 "Snap pull-back (opener)"). AW and PN also open on a full picture.
- On a Shorts feed this frame is the thumbnail and the scroll-stopper.
- The sky also lacks the TF galaxy nebula (see defect 15), so it reads as an empty void.

**Fix (preferred, TF grammar):**
- Open on a neighbour's street gnome (not the hero) in ECU, seen from its house side, so its glossy face looks at the lens.
- Snap pull-back x6-8 with `outExpo` (half done in 0.1 s, 78 % in the first quarter), crane up +14 studs, roll -15° → 0°.
- End on a high 3/4 view from the porches looking out over the lawns. Every gnome then faces the camera (they face their houses), which sells the rule better than the backs do now.
- Frame 0 mean luma ≥ 80. The episode's last frame (a gnome ECU) then loop-matches frame 0.

**Fix (minimal, keeps the crane):**
- `camera.start.up_studs` 22 → 10, `pitch_deg` 28 → 12, so roofs and lit windows fill the lower 40-45 % of frame 0 and the moon sits in the upper third.
- Nebula 0.28 → 0.45 (defect 15).
- Target: crushed pixels ≤ 50 % on f0.

### 5. MAJOR: s02-s04: the porch does not read as night, the lantern is unlit and the window dominates

**Problem:**
- p50 95-111 is fine for a TF night interior, but this is an exterior porch with nothing dark in frame except a shutter.
- The pink-white lit window (≈ #e8d0ea) and the saturated red curtains (#b84a5a graded to about #c01820) are the largest and brightest shapes. The bible says the subject is the brightest thing in a night frame.
- The wall lantern beside Grandma has dark glass and no halo, although the board asks for "wall lantern lit".
- PN porches at night (29.3, 53.2 s) show warm lamp pools on the porch and the black street beyond.
- The cut from s01's night street to a daylight-looking porch is a lighting jump inside one location.

**Fix:**
- Window: lit-window emissive ×2.2 → ×1.4, colour toward amber #ffc890, so it lands at about #e0b090 (below the faces).
- Curtains: #b84a5a → #7a2a3a, drawn half-closed, so the red area drops by about 50 %.
- Wall lanterns lit: glass emissive #ffd9a0 ×4, a 20-30 px halo sprite, point #ffb766 3 cd. `porchGlow` has `lantern n: 2`; check that it binds to the hero house's wall lanterns.
- Show the night:
  - s02 yaw 42° (defect 3) brings the open end of the porch into the top-right 15-20 % of the frame: black yard plus one lit lamp post across the road.
  - In s04, keep the porch-ceiling edge and a slice of black sky with stars at the top right.
- Porch hemisphere 0.95 (defect 2), so corners fall off to maroon (target p1 5-15).

### 6. MAJOR: s04 snap (f133-150, 2.22-2.50 s): the poof is a milky wash, and the swap shows through it

**Problem:**
- `poofCloud` uses normal-blended lavender puffs at alpha ≤ 0.98·(1-u)^2.2. At f134 they are about 50 % opaque, so both gnomes are already visible through the cloud on the swap frame: a visible pop.
- The cloud lifts the whole frame's mean luma from 94 to 128 (+34) and is still +21 at f150 (0.27 s later). The frame turns hazy instead of punchy.
- TF's bursts (36.28 s, 109.62 s) are local: the frame mean changes by only +3 to +5. They are a bright additive core, red or pink radial streak lines, 20-40 white snowflake sparkles and a crisp white ring, gone in about 0.4 s.
- Our `fx.burst` core (`corePx` 520) is not visible as a flash; the poof sprites (renderOrder 25+) are drawn over it.

**Fix:**
- In s04, either draw the burst after the poof (burst renderOrder 40) or drop the poof to 4 puffs.
- On frames 134-135 the core must be opaque (alpha ≥ 0.92) over each human's torso-plus-head box. `poofCloud` px [230,400] → [380,520], spread y 0.62 → 0.9, centre at seat + 3.4 studs.
- Then collapse fast: `dur` 0.3 → 0.18, so the frame-mean lift is ≤ +8 by f146.
- Swap the gnomes in on f135, not f134, so the swap lands under the opaque peak.
- Add TF streaks: 12-16 additive thin streak sprites, #ffffff and #ff7aa0, 120-260 px long, radiating from each chest, life 0.25 s.
- Burst sparkles 30 → 36 at 50-90 px.

### 7. MAJOR: s05 (2.92-5.00 s): the hero gnome is lit flat and cool, framed dead-front, and not low enough

**Problem:**
- The bible and TF shoot the creature from below with a tilt (TF #19 Fern low CU, #40 Queen extreme low, AW 67.0 s doll tilted 20-30°).
- Our camera is at y 0.95 studs looking about 12° up. The gnome is perfectly frontal and symmetric, so it reads as a passport photo.
- The 0.9 cd warm "window spill" does not show; see defect 2 for the colour readings.
- The beard is one lavender mass covering 50-55 % of the frame by f299.
- The lantern (his identity prop) is cut off at the left edge. The `?lantern=1` alternate (`alt_lantern/_alt.jpg`) only shows an orange rim on the hat brim; the lantern itself is out of frame.
- Roll is +1.2°, while STORYBOARD_RULES's character-intro row asks for +10-13°.

**Fix:**
- Camera y 0.95 → 0.55 studs. Look up 25-28° at the eyes, distance 1.22 → 1.4 studs from the nose.
- Yaw 18-22° to 3/4, toward his lantern hand, so the lantern is fully inside x 90-990.
- Roll 0 → +10° over the shot (`rollBy(10)`), push Z 0.28.
- Warm key and cool rim as in defect 2.
- The beard keeps its lavender in shadow, but the key separates it from the face.
- Re-check that the moon stays just off the hat tip after the yaw.

### 8. MAJOR: s04 to s05: the test never shows the TF warm "magic glow" grade

**Problem:**
- TF's signature is cool → warm when magic happens (bible §5 P3 and P5.8, §6.3 "Magic glow moment": `warmGlow` grade, bloom 0.35-0.45, glow 0.12, gold and pink motes).
- The transformation is the literal magic beat, but s04 stays on the porch grade.
- The owner's favourite look is therefore never demonstrated in the test.

**Fix:**
- In s04, switch in-shot on "turn" (f134) to `sets.postPreset('magic')` (grade `warmGlow`, bloom 0.4, threshold 0.9, glow 0.12 #ffd8c8) over 8 frames (bible P3: in-shot over 6-10 frames, no white flash).
- Hemisphere to #ffcdb8 / #5a2030 at 1.4. 20-30 gold and pink motes (`magicDust` count 44 → 30, px [10,26] → [14,30]).
- Hold warm to the cut; s05 returns to `nightHigh` (the cut is the beat).
- Acceptance: post-snap hi #f2cfbc-#fde3c7, mean luma 130-150.

### 9. MAJOR: all shots: the sparkles do not look like TF's "snowflake" glints

**Problem:**
- Ours are thin, hard 4/6-point asterisks. `kit/fx.js` `sparkles()` uses `tex.sparkle({ sharpness: 16, core: 0.55 })`.
- The visible star body is about 50-60 % of the sprite px, so stars measure 25-45 px on screen, and only 3-6 are visible per frame.
- TF glints (0.3, 99.9, 109.75 s) are soft, fat 6-8-point snowflakes with a glow core, 50-80 px, 5-15 per interior frame (bible §6.3, rule 9).
- In s05 the 8 glints and 6 motes are barely visible.

**Fix:**
- Add `sharpness`/`core` options to `sparkles()` (or a local copy in `ep01_test5.js`, like `starGlint`). Use sharpness 16 → 7 and core 0.55 → 0.75, plus a `radialGlow` underlay sprite at 0.55x size and opacity 0.5.
- px [40,80] → [55,95] and brightness 1.6 → 2.0.
- Counts: s01 8 → 10, s02 and s03 6/5 → 10-12, s04 6 → 12, s05 8 → 10, with the s05 box placed between the lens and the gnome (it currently sits behind his head).
- Acceptance: 8-12 glints visible per frame, 45-80 px measured.

### 10. MAJOR: s05 tail (3.44-5.00 s): 1.56 s of silence on a near-static frame

**Problem:**
- After "gnomes" the mix drops from -16 LUFS to -32.7 LUFS (crickets only, 17 LU down).
- The picture is a slow 0.24 %/frame push on a frozen statue, and the caption band goes empty at 3.77 s.
- None of the references has a gap like this: the voice is continuous over a constant music bed about 8 LU under it.
- STORYBOARD_RULES set a silence beat at 0.6-0.7 s and an ending 0.3-0.4 s after the voice.
- This is the last impression of the test.

**Fix (owner's choice, in this order):**
- (a) For the look test, use the lantern alternate as the tail event:
  - `?lantern=1` lights it at 3.75 s;
  - reframe per defect 7 so the lantern is in frame;
  - add the bible's light-up hit "whoosh + bright shimmer" (a tink-whoosh at 3.75 s, about -24 LUFS short-term);
  - let the warm pool and halo grow over the face.
  - This demonstrates TF's warm glow; it spends the 41.76 s plant, so say so to the owner.
- (b) Keep the plant: cut at about 3.77 s to a 1.23 s silence-beat shot, a low wide of the whole lawn with every gnome turned to the house and staring, with a slow pull-back -10 %.
- In both cases, if the owner's library has a music-box bed, lay it 8 LU under the voice (about -24 LUFS) for the whole 5 s. The owner said they add music later, but every reference has music and the test sounds empty without it.

### 11. MAJOR: s01 last frames (0.45-0.92 s): the street composition is right-heavy and the gnome rule does not read

**Problem:**
- At f54 the houses are pushed against the right edge and the nearest one is cut.
- A huge white picket fence and sidewalk run diagonally across the left half. The fence is the brightest element (hi #867edc), and its tightly packed pickets render as a zigzag-topped wall with bowling-ball finials.
- There is no road, no lamp posts and no lamp pools. TF 106.8/107.5 and PN 54.8 all show the road with yellow dashes and black lamp posts with warm pools.
- One lawn holds 8+ gnomes scattered at random, including the three extra foreground gnomes, so "a gnome on every lawn, each facing its house" reads as "a lawn full of toys". From behind, the facing is ambiguous.

**Fix:**
- Re-aim the end view so the street or sidewalk runs up the vertical centre, with houses on one side and lawns in the middle third.
- Show 2-3 lit lamp posts near the camera with `radialGlow` pools (#ffb870, opacity 0.3, radius 6 studs).
- 1-2 gnomes per lawn, centred in front of each house. Drop the three extra fence gnomes (`BUILDERS.sky_to_street`).
- Fence: picket pitch at least 1.8x the picket width (visible gaps), finial balls 0.9 → 0.5 stud, or keep the fence out of the lower-left foreground.
- If defect 4's pull-back is adopted, the end view looks from the houses toward the street and all of this is solved at once.

### 12. MINOR: s01 end (f44-54, 0.73-0.90 s): the accent move lands and the camera stops before the cut

**Problem:** Measured flow speed falls 134 → 8 px/s over the last 10 frames (`outQuart` with t1 = 0.95 s). The image is near-still for about 0.15 s before the cut. Bible rule 2: never stop, cut mid-move.

**Fix:** `camera.move.ease` outQuart → outCubic with t1 0.95 → 1.2 s. That is 98.4 % done at the cut while still moving about 290 px/s. Peak speed on frame 1 stays about 4,800 px/s (measured 4,815, inside 3,000-5,600).

### 13. MINOR: s03 (1.48-2.10 s): the close-up push stalls and slides sideways

**Problem:**
- The board asks for +16 %; measured +5.2 %, with the per-frame scale falling from +0.39 % to 0 by f115.
- The image drifts right at up to 102 px/s (bible 20-70).
- Cause: the swing sway (±2.5° at 0.45 Hz) carries Grandma's head away from the lens and sideways. That cancels the FOV push in the second half.

**Fix:** In `grandma_cu`, either use sway amplitude 0 for s03 (`updateSwing` with a scale of 0), or have the camera ride the swing (camera position = pivot transform × fixed offset, then push). Target: Z +14 to +18 %, linear ratio 0.9-1.1, drift ≤ 60 px/s.

### 14. MINOR: s02 and s04: the deck planks look like cartoon parquet

**Problem:** The deck has short staggered planks with thick black seams. At the low s04 angle it fills 35-40 % of the frame. TF's floor is long glossy terracotta boards with fine seams (bible §4.2: planks 0.8-1.0 stud wide, roughness 0.3-0.4 sheen).

**Fix:**
- Deck `tex.woodPlanks`: seam darkness to about 0.15 (now near black), seam width 1-2 px at 128 px/stud, plank length at least 6 studs, roughness 0.35.
- Mostly solved by re-framing s04 (defect 1).

### 15. MINOR: s01 f0-15 and s05: the galaxy sky has no visible nebula

**Problem:** The sky is black with lavender stars. The TF galaxy has magenta and purple nebula wisps (#2a022c/#46134d/#3a2988, TF 2.3 s). `SKIES.galaxy.nebula` 0.28 does not show after the grade. The animate notes say the s05 nebula was "lifted", but it is not visible in s05 either.

**Fix:** `skyOpts: { nebula: 0.45 }`, with the wisps placed in the upper sky band the camera actually sees (zenith-ward 0.3-0.7), for s01 and s05. Keep the sky luma at 0-15.

### 16. MINOR: captioned version: the caption font is DejaVu Sans Bold

**Problem:**
- DejaVu Sans Bold is about 25-35 % wider per glyph than TF's heavy grotesque. "gnomes" is 414 px wide (69 px per letter) against TF "everyone" 402 px (50 px per letter); "grandparents" spans 724 px.
- The height matches (glyph box 1330-1405 against TF 1334-1403).

**Fix:** Inter ExtraBold is installed: `/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf`. It has a double-storey "a" and a straight-tailed "y", close to Montserrat ExtraBold. Use it at 92-96 px in `burn_captions.py`, keeping the stroke and shadow.

### 17. MINOR: s03: the glasses lens greys the ^^ eyes, and the hinge reads as a mole

**Problem:** Behind the lenses the eye lines measure #2f1c5c (purple-navy), while the mouth line is #08000f (black). The right temple stub shows as a dark square dot beside the lens (x ≈ 1000, f89-125).

**Fix:** Lens opacity to about 0.08, or remove the lens glass. Trim the temple arms so they end inside the head silhouette from a 20° front view.

### 18. MINOR: s02-s04: the porch close-ups are sparsely dressed

**Problem:**
- About 5 props are visible: lantern, window, curtains, shutter, swing. The bible asks for 5-15 per frame and a recognisable prop behind every close-up.
- In s03 the lantern is cropped at the top-left, and the board's navy edge of Grandpa's cardigan at frame right is missing.

**Fix:**
- Add a hanging fern basket, a small side table with a teacup and knitting basket, a doormat, potted geraniums and a wind chime.
- Move the "14" plaque away from head height (it peeks behind Grandma's head at f55-88).
- In s03, shift the target about 0.25 stud left so the lantern is whole and the cardigan edge shows at the right.

### 19. MINOR: s05: the gnome's "chips" read as white dust, and the beard as noodles

**Problem:** The bisque chips appear as dozens of tiny white specks across the hat (they read as snow or dust at the ECU). The beard strand bump is a uniform fine groove pattern, so it looks like extruded pasta.

**Fix:**
- 3-5 larger chips (0.04-0.08 stud) on edges only: hat brim, nose tip, boot toes, with a darker rim.
- Beard bump scale 1.4 → 0.8, plus 3-4 deep separations between big locks.

### 20. MINOR: sound: SFX taste check

**Problem:**
- M1 is "Shimmer, Christmas, Sparkle". On a red-hat, white-bearded, navy-coated gnome, any sleigh-bell content will read as Santa. Listen to 2.1-3.4 s.
- W1 on the opener and P1 on the snap are fine. The pop transient lands 7 ms after the burst frame, inside the /t/ gap.

**Fix:** If there are jingles, swap M1 for a music-box or chime-tine shimmer (bible palette) at the same level (-28 LUFS, HPF 1.5 kHz).

### 21. MINOR: s02 and s04: the swing chains read as a black ladder at the frame edge

**Problem:** The swing reads as a bench. Its chains show only as a ladder-like black strip at x ≈ 0-20 (f55-88), and the hooks are never seen.

**Fix:** After re-framing (defects 1 and 3), keep one chain fully in frame. Chain colour #3a3a40 → brass #8a6a3a with a sheen, so it reads as a swing.

### 22. MINOR: captioned version: the caption band is empty for 3.77-5.00 s

**Problem:** This follows the captions JSON (`hold_last_to_end: false`). It is acceptable with no voice, but the tail looks unfinished.

**Fix:** Resolve it with defect 10. If the tail stays silent, set `hold_last_to_end: true`.

---

## What passes (keep it)

- **Cut timing:** cuts are on frames 55/89/126/175, 17-23 ms before "grandparents / don't / They / gnomes". The glint peaks at f106-107 on "die" (1.738 s). The snap is f134 on "turn" (2.228 s). Caption swaps sit 1 frame before onsets.
- **Push grammar:**
  - s02 +18.5 %, linear (2nd-half / 1st-half rate 0.98), drift 38 px/s.
  - s04 +21.0 %, linear 0.92.
  - s05 +35.6 %, linear 0.96, steady 0.23-0.27 %/frame.
  - The opener peaks at 4,815 px/s on frame 1 (bible 3,000-5,600).
- **Motion:** no jitter, duplicate or frozen frames (the minimum mean frame difference outside cuts is 2.0). There are no pops outside the cut and burst frames (the swap at f134 excepted, see defect 6). True 60 fps.
- **Grade numbers:**
  - s01 end: p50 63, hi #867edc, sat 0.63 (TF aerial 106.8 s: p50 59, hi #8d87d5, sat 0.57).
  - Porch: p50 95-111, p99 200, hi #d6b9de, clip 0 % (TF interior CUs: p50 117-120, hi #ccb3d9-#dfb6bf).
  - s05 end: p50 66, 29 % crushed (AW 67.0 s doll: p50 78, 31 % crushed).
  - The darkness is acceptable once the face carries warm light (defect 2).
- **R6 construction:** drum heads, 2x2x1 torso, 1x2x1 limbs, rigid seated pose, 2D painted cardigans with buttons and knit, a single chunky hair accessory. The decal faces ^^, neutral and smile use the TF line language (black mouth line, thick strokes).
- **Gnome:** it is clearly the most detailed model on screen, as the bible requires. Glazed ceramic, domed glossy eyes at about 28 % of head width with catchlights and bloodshot veins, buck teeth, a sculpted moustache. Fix its light and angle, not its build.
- **Audio:** the mix is -16.0 LUFS integrated, -1.2 dBTP, voice +17.7 dB over the SFX, 0-sample offset in the mux.

## Fix order for the fix stage (one re-render)

1. Lighting and grade:
   - warm face keys and porch/gnome grade changes (defect 2);
   - porch night cues: window, curtains, lantern, black slice (defect 5).
   - Check on stills with `stats.py` first.
2. Framings:
   - s04 centred, with gnomes together and ×1.35 (defect 1);
   - s02 at 42° with the railing (defect 3);
   - s05 low, 3/4 and rolled (defect 7);
   - s01 end view (defect 11);
   - s01 opener: pull-back or a lower start (defect 4).
3. Magic: burst and poof rework (defect 6), s04 warm switch (defect 8), sparkle texture and counts (defect 9), nebula (defect 15).
4. Camera fixes: s01 outCubic with t1 1.2 (defect 12), s03 sway-free push (defect 13).
5. Tail decision with the owner (defect 10), then the minors.

Re-run `sync_check.py` and this review's motion check (`scratchpad/rbx/test5/review/motion.py <mp4> <out.json>`) after the re-render.
