# Visual analysis: "Porch Night" (reference r2)

Reference only: we copy the **look, construction and grammar**, not the characters, plot or lines.

- **Source:** `ref60/porch_night.mp4`, the full upload. 1080x1920, 60 fps, 166.77 s (10 006 frames), h264 at 1.26 Mb/s, AAC 44.1 kHz. Picture starts at frame 0; the story now runs to the end ("...check the lock three times", 166.4 s). The old trimmed copy stopped at 157 s.
- **Evidence folder:** `$PNV` = `/tmp/claude-0/-home-user-claude-todo-demo/353ac1d9-152b-55bb-bdf1-0625e0fc6a83/scratchpad/rbx/pnv` (scratch, not the repo: the frames are copyrighted).
  - `sh/pn_1..5.jpg`: 1-s frame sheets (167 frames).
  - `s/shots_01..10.jpg`: first, middle and last frame of all 118 shots.
  - `full/m_001..118.jpg`: full-resolution middle frame of every shot (shot number = file number).
  - `s/v_*.jpg`: full-resolution mosaics (scarecrow, family, faces, townspeople, interiors, environments, glow, DOF, captions).
  - `s/m_*.jpg`: 60-fps strips around moves, gestures and in-shot events (opening, rip, walks, whip pan, rocking chairs, lamps going out, lock).
  - `s/spec_inst.png`: spectrogram of the music/SFX stem. `stems/voice.flac`, `stems/inst.flac`: UVR-MDX split.
  - Data: `asr_pn.json` (744 words, new ASR of this full copy), `cuts_final.json`, `shotmotion.json` (camera + subject motion per shot), `colstats.txt/json` (per-shot palette), `capscan2.json` (caption band per frame), `annot.py` + `mktable.py` (shot list).
- **Method:** I viewed all 167 sheet frames, all 354 shot-sheet thumbnails, about 75 full-resolution frames and about 230 strip frames. Cuts come from per-frame difference (112 auto + 5 confirmed by eye). Camera moves come from LK optical flow + RANSAC similarity per frame. Subject motion is the residual after camera compensation. Colours are pixel samples and k-means. Captions were scanned on all 10 006 frames and matched to ASR word onsets.

## 0. The 16 facts that matter most

1. **Made in Roblox Studio and screen-captured**, like Tooth Fairies, but this one is a **"Bloxburg-style" small American town** instead of a pastel dream room.
   - **R6 blocky avatars** with catalog 2D decal faces, UGC 3D hair and hats, 2D shirt and pants textures.
   - **Roblox materials**: wood planks (clapboard siding, porch floors), Wood grain (doors, frames, chairs), Plaster (interior walls), Slate/Cobblestone (foundations), Grass, Asphalt, Concrete.
   - One high-detail **marketplace scarecrow** (textured burlap, straw strands, tattered coat, bony claw) about 3x human scale. It is the only "premium" model and it carries the horror.
2. **True 60 fps.** Only 1.5% of frame-to-frame differences are near zero, and per-frame camera motion is smooth with no repeats (Tooth Fairies was 40 fps in a 60 fps file). Real detail is about 540-720p: down to 540x960 and back gives PSNR 36-42 dB.
3. **118 shots in 166.8 s: 42.1 cuts per minute.** Median shot 1.35 s, mean 1.41 s, range 0.58-2.43 s. Slower than Tooth Fairies (51.5/min, median 1.12 s).
4. **Cuts lead the words.** 76 of 92 sentences open on a cut. 107 of 117 cuts sit on a sentence or clause start. The cut comes **0.03-0.15 s before the first word** (median 0.08 s).
5. **The camera always drifts.** 115 of 118 shots move.
   - **78 shots (107 s, 64% of the runtime) are slow linear push-ins: median +11% per shot** (p10 +4%, p90 +21%), about x1.08 per second, the same whatever the shot length (r = -0.01). Each quarter of the shot carries 24/25/28/24% of the zoom: linear, no easing.
   - 9 slow pull-outs (-5% to -20%), 25 big moves (trucks along house fronts, follows, tracking at boot level, tilts, one 150° whip pan), 3 static shots.
6. **Mostly medium shots at eye level.** 69 of 118 final framings are MS, 86 of 118 at eye level, 116 of 118 with a wide lens (Roblox default 70° vertical FOV). Low angles and worm's-eye views are kept for the scarecrow.
7. **Characters actually move.** 44 shots are still (63.5 s), 48 light (67.5 s), 26 active (35.8 s). There are real walk and run cycles, sitting, rocking chairs, hugs, a drag, a throw, a whip of a claw.
   - Movement is smooth (60 fps, keyframed or Roblox default animations), but **poses and decals pop** in one frame: sit-down, arms up, the shove, the door slam.
8. **Expressions are 2D decal swaps** (O_O shock with red mouth, >< sob, ^^ laugh, worried brows, closed-eye calm). Zero lip-sync, zero blinks. Dad gets a stubble overlay and, at the climax, a detailed **"crazed" decal** (white eyes, small pupils, heavy brows).
9. **The scarecrow's face is the effect.** The stitched grin "rips" into a black mouth ringed with yellow stitch-teeth by **decal swap, plus short blurred-face flickers and an editor shake hit with motion blur** (21.0-22.1 s, 69.6-70.0 s, 162.7-162.9 s). In the first rip, the flicker, blur and shake each land on a tearing SFX transient within 0.03 s.
10. **Warm amber look.** Interiors are a deep **sepia-amber** grade (whites #e8cc90, walls #c6af7b-#e1bc75, floor #501e07, saturation 0.63, mean R-B +89). Exterior nights are near-neutral warm with **pure black starry skies** (18% pure-black pixels). Dusk shots are golden with teal or blue skies. It is not pastel and not purple.
11. **Highlights never clip.** p99 luminance tops out at 173-236 (median 215), and clipping is under 0.1% in every shot. Whites read as cream, not white.
12. **Night is shown by a black sky and lamp pools, not by darkness.** House fronts stay readable (white siding #d8d0c4). Black lamp posts every ~2 houses; lamp glass is flat pale #d6dcc0 with **no glow halo**.
13. **Clean image.** No bloom, no DOF, no vignette (corners/centre 1.08), no grain, no chromatic aberration, no lens distortion, no overlays, no ambient particles. **Real cast shadows** (sun and lamp-post shadows).
14. **Only hard cuts.** The single exception is a 0.12-s shake + blur "transition-in" on frames 0-7.
15. **Captions are CapCut auto-captions, one word at a time, and the dialogue is colour-coded by speaker:** narrator white, Dad light blue #96c8f5, Mom pink #ed99bf, Grandpa yellow #f9dd6e, townspeople orange #f1b16c. Shouted lines are in CAPS. No pop animation. Caption appears 0.02 s before the word (median).
16. **Sound:** continuous VO, a tonal music bed about 5 dB under it (-23.3 vs -18.4 dBFS), and sparse SFX locked to picture: straw creaks, stitch tears and pops, three lock clicks at the end.

### How it differs from Tooth Fairies (the owner's favourite)

| Aspect | Tooth Fairies | Porch Night |
|---|---|---|
| Palette | Pastel lavender / magenta / periwinkle | Warm amber-sepia interiors, golden dusk, black night |
| Frame rate | 40 fps in a 60 fps file | true 60 fps |
| Cut rate / median shot | 51.5/min, 1.12 s | 42.1/min, 1.35 s |
| Push per shot | +19% median | +11% median |
| Shot sizes | 51% close (CU/MCU/ECU/INS) | 58% MS, 23% close |
| Subject motion | 44% still, humans frozen | 37% still, real walks, runs, rocking |
| Effects | Soft bloom + floating sparkles everywhere | None (no bloom, no particles) |
| Shadows | Soft, almost none | Real cast shadows outdoors |
| Captions | All white | Speaker-coloured dialogue, CAPS for shouting |
| Editor effects | None | Shake + blur on the opening and on the "rip" hit |

---

## 1. Shot list

**Columns:**
- Times are exact frame boundaries ÷ 60. **Words** are the ASR words that start in the shot.
- **Camera move** is measured; `z` = cumulative scale over the shot (>1 push or zoom-in, <1 pull). Moves in words come from viewing the strips.
- **Subject motion** is the share of pixels that still change after camera compensation (3-frame step): still <1%, light 1-5%, active ≥5%.
- **Sizes:** ECU / CU / MCU / MS / MWS / WS / EWS / INS (insert of an object) / POV. **Angle:** eye / low / high / OTS (over the shoulder) / aerial / ground-level / worm's-eye.
- **Lens feel:** "wide" ≈ Roblox default 70° vertical FOV (about 43° horizontal in 9:16). "normal" ≈ 40-50° vertical.
- **Locations:** XN exterior night, XD exterior dusk / blue hour / golden hour, XY exterior day, XC cornfield night, IN family house interior, IH Harper house interior.

| # | Start-end (s) | Dur | Size | Angle | Lens | Camera move (measured) | Subj. | On screen | Words |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.00-0.68 | 0.68 | CU | OTS high | wide | editor shake+blur transition-in (f0-7; the z 0.26 is that effect), then slow push | active | Hook flash-forward: behind a man in a green-plaid shirt in a rocking chair, the scarecrow's stitched face looms in front of him; street behind | In this town, |
| 2 | 0.68-1.48 | 0.80 | EWS | aerial high | wide | push-in +7% linear [z 1.07] | still | Dusk aerial of the street: two rows of houses with lit porches, black lamp posts, cornfield at the end; one light pop at 0.98 s | one night a year, |
| 3 | 1.48-3.53 | 2.05 | MS | eye | wide | push +12% with slight arc [z 1.12] | light | Old woman (white bun, dark dress, worried decal) rocking in a chair behind a white porch railing; warm wood siding, lit window | every family has to leave one person outside, |
| 4 | 3.53-5.40 | 1.87 | WS | low | wide | push-in +16% linear [z 1.16] | still | Empty street at blue hour: white and dark-red clapboard houses, sidewalk, no people | and in the morning, every porch is empty. |
| 5 | 5.40-6.95 | 1.55 | WS | low | wide | push +17% (eases in) [z 1.17] | light | Scarecrow walks out of the cornfield toward camera; starfield sky | It comes out of the cornfields at midnight, |
| 6 | 6.95-8.73 | 1.78 | MWS | extreme low | wide | tilt/crane up (dy ≈ 185 px) [z 1.07] | active | Scarecrow towering against a milky-way sky, a street lamp beside it below its head | a scarecrow, taller than the streetlights, |
| 7 | 8.73-10.33 | 1.60 | CU | low | wide | truck ≈ 110 px + slight push [z 1.06] | active | Straw hanging out of the coat sleeve; galaxy sky, a house behind | straw hanging out of its sleeves, |
| 8 | 10.33-11.33 | 1.00 | MCU | low | wide | push-in +6% eased [z 1.06] | light | Sack head + pointed burlap hat with green patch and straw tufts; slight head sway | and a sack for a head, |
| 9 | 11.33-13.05 | 1.72 | CU | eye | wide | push-in +21% linear [z 1.21] | light | Sack face fills frame: stitched eye-holes, wide stitched smile, rope collar | with a big smile stitched across it. |
| 10 | 13.05-14.03 | 0.98 | CU | ground-level | wide | tracking with the feet (≈ 290 px truck + roll) [z 0.97] | active | Scarecrow's black boots and straw legs stepping on the asphalt | It walks so slowly |
| 11 | 14.03-16.08 | 2.05 | MS | eye | wide | slow pull-out -13% (starts at mid-shot) [z 0.87] | still | Reaction: two women peek through a lit window (O_O decals), rocking-chair back in foreground | you can hear the straw creak with every step. |
| 12 | 16.08-17.25 | 1.17 | WS | top/high | wide | push +27% + drift [z 1.27] | active | Top-down: scarecrow walking up the street between porches | It goes porch to porch, |
| 13 | 17.25-18.68 | 1.43 | WS | low | wide | slight pull -5% + tilt [z 0.95] | active | Scarecrow beside a red two-storey house bends its torso 90° toward a porch | it bends all the way down, |
| 14 | 18.68-20.57 | 1.88 | CU | OTS | wide | push-in +3% eased [z 1.03] | light | Scarecrow face right in front of the seated man's head (man seen from behind) | until its face is right in front of yours, |
| 15 | 20.57-22.17 | 1.60 | CU | eye | wide | head dips (dy +10 px/frame 21.42-21.90) then editor shake hit with blur 21.93-22.03 (±50-76 px, ±1.7°) [z 0.92] | active | Stitched face flickers (21.02, 21.13), dips under the brim, mouth rips open: black hole ringed with yellow stitch teeth | and then the stitches rip open. |
| 16 | 22.17-23.40 | 1.23 | CU | OTS low | wide | slight pull -11% [z 0.89] | light | Behind the seated man: scarecrow in profile with gaping mouth, hat brim overhead | Wider than its whole head. |
| 17 | 23.40-24.45 | 1.05 | WS | low | wide | push-in +11% linear [z 1.11] | light | Title drop: empty blue-hour street, rows of black lamp posts and houses | We call it porch night. |
| 18 | 24.45-26.63 | 2.18 | MWS | eye | wide | truck right along the house fronts (≈ 1470 px in 2.2 s), lamp post wipes foreground [z 2.09] | active | Green, then mustard house with porch, steps, wall lantern | Every house in town has one chair on the porch, |
| 19 | 26.63-28.68 | 2.05 | WS | eye | wide | truck/pan left with walkers + pull [z 0.57] | active | Golden-hour: kids and a woman walk past a porch with an empty rocking chair; blue sky, cornfield | just one. Nobody sits in it the rest of the year, |
| 20 | 28.68-30.00 | 1.32 | MS | eye | wide | push-in +22% linear [z 1.22] | light | Old man (grey hair, deadpan decal) in a rocking chair on a porch at dusk | and there's only one rule. |
| 21 | 30.00-31.63 | 1.63 | MS | eye | wide | push-in +15% eased [z 1.15] | still | Old woman (grey bun, worried decal) seated behind a porch railing | Somebody has to be in that chair. |
| 22 | 31.63-32.63 | 1.00 | WS | eye | wide | push-in +13% linear [z 1.13] | light | Grey clapboard house with porch (the Harpers' house) | The year I was born, |
| 23 | 32.63-34.67 | 2.03 | MS | eye | wide | pan left + push +25% [z 1.25] | active | Harper family rushes in the front door (kids, woman, man in cowboy hat and gingham shirt); door snaps shut at 33.78 | the Harpers locked their whole family inside. |
| 24 | 34.67-36.50 | 1.83 | MCU | eye | wide | push-in +12% linear [z 1.12] | still | Morning: white-haired neighbour (green sweater) from behind at the Harpers' door, wall lantern | In the morning, their door was still locked |
| 25 | 36.50-37.53 | 1.03 | MS | eye | wide | push-in +5% linear [z 1.05] | still | Same neighbour looks through the window of the empty house | and the house was empty. |
| 26 | 37.53-38.85 | 1.32 | MS | eye | wide | push-in +4% linear [z 1.04] | still | On a front path: brown-haired woman and white-haired grandmother face each other | So every family chooses. |
| 27 | 38.85-39.88 | 1.03 | MS | low | wide | push-in +23% linear [z 1.23] | active | Ornate black lamp post foreground, porches at sunset | Old people go first. |
| 28 | 39.88-41.38 | 1.50 | MS | eye | wide | pull -19% + tilt [z 0.81] | light | Old woman (knit cap, closed-eye smile) on a porch behind a railing, another old woman behind | That's just what you do when you get old here. |
| 29 | 41.38-42.37 | 0.98 | WS | eye | wide | push +44% [z 1.44] | light | Rich man (bowler hat, black suit, red tie) on his path holding a green cash stack | Rich families pay. Mr. |
| 30 | 42.37-44.15 | 1.78 | MS | eye | wide | push-in +5% linear [z 1.05] | still | Mr Wendell (top hat) hands cash to a poor mother in a brown dress; her kid beside | Wendell pays a kid from the bottom of the |
| 31 | 44.15-45.05 | 0.90 | MS | low | wide | push-in +9% eased [z 1.09] | light | Danny (overalls, brown curls) in front of porch steps at dusk, lamp post | hill to sit on his porch, |
| 32 | 45.05-46.25 | 1.20 | MS | eye | wide | pull -7% + truck [z 0.93] | still | Mr Wendell leaning on his porch railing (white face, top hat) | a new kid every year. |
| 33 | 46.25-48.13 | 1.88 | MS | eye | wide | follow (tracking back with the walkers) [z 0.99] | active | Family with many kids walking toward camera down the street, blue sky, mountains | Some families have one more kid than they wanted, |
| 34 | 48.13-49.20 | 1.07 | MS | eye | wide | push-in +5% linear [z 1.05] | still | Two neighbours chatting on the sidewalk (old woman in green coat, man in straw hat) | and people say it like a joke. |
| 35 | 49.20-49.78 | 0.58 | MS | eye | wide | push-in +5% linear [z 1.05] | still | Reverse angle on the neighbours; a kid in red plaid behind them (orange caption) | One for the porch? |
| 36 | 49.78-51.87 | 2.08 | MS | eye | wide | push-in +9% linear [z 1.09] | still | Old man roped to a porch chair behind the railing, worried; old woman beside | And some families tie the person to the chair |
| 37 | 51.87-52.73 | 0.87 | MCU | eye | wide | push-in +22% linear [z 1.22] | light | Same old man, laughing/shouting decal | so they can't knock, |
| 38 | 52.73-53.78 | 1.05 | MS | eye | wide | static [z 1.01] | still | Old woman (white bun) on a porch at night, column in foreground | because everyone knocks. |
| 39 | 53.78-56.22 | 2.43 | EWS | high | wide | push-in +13% linear [z 1.13] | light | Night street from above the centre line: lamp posts both sides, lit porches, black starry sky | Every year, you hear it all the way down the street, |
| 40 | 56.22-57.23 | 1.02 | MCU | eye | wide | push-in +3% linear [z 1.03] | still | Ginger-haired person kneeling, pounding on a door, porch at night | knocking, begging, |
| 41 | 57.23-58.30 | 1.07 | MS | eye | wide | truck ≈ 90 px [z 1.09] | still | Woman behind a lit window turns away (nobody opens) | and nobody opens. |
| 42 | 58.30-59.58 | 1.28 | MS | OTS | wide | push-in +4% linear [z 1.04] | light | Boy (yellow spiky hair, bee-striped shirt) from behind; Grandpa in a rocking chair on the porch | Last year, it was Grandpa. |
| 43 | 59.58-61.37 | 1.78 | MS | high | wide | static [z 1.01] | still | Dinner table: Mom, Grandpa, boy; pendant drum lamp | He stood up at dinner before anyone said a word. |
| 44 | 61.37-62.93 | 1.57 | MS | low | wide | push-in +7% eased [z 1.07] | light | Grandpa standing, ^^ laughing decal, then smile (yellow caption) | It's me, I've had a good run |
| 45 | 62.93-65.08 | 2.15 | MS | OTS | wide | slow arc + push +23% [z 1.23] | light | Boy from behind at a red curtain, peeking out | that night. I watched through a gap in the curtains. |
| 46 | 65.08-66.90 | 1.82 | POV | OTS high | wide | tilt down (≈ 150 px) [z 1.00] | light | Through the window glass (boy's hair in foreground): the scarecrow walks up the path, sepia-tinted by the glass | It walked up our path and bent down to him. |
| 47 | 66.90-67.93 | 1.03 | MCU | eye | wide | push-in +16% linear [z 1.16] | still | Grandpa seated, calm closed-eye smile, hat in hand | Grandpa took his hat off, |
| 48 | 67.93-69.25 | 1.32 | CU | OTS low | wide | pull -15% [z 0.85] | light | Behind Grandpa's white hair: the huge scarecrow face above him | like he was meeting someone at church. |
| 49 | 69.25-70.43 | 1.18 | CU | OTS | wide | tilt (dy ≈ 130 px) [z 1.05] | light | Face flickers (69.60, 69.72), mouth rips open (70.0) | Then the stitches ripped open |
| 50 | 70.43-71.48 | 1.05 | MCU | eye | wide | push-in +15% linear [z 1.15] | light | Boy's sad face behind window bars, warm | and Grandpa was gone. |
| 51 | 71.48-72.75 | 1.27 | MS | eye | wide | push-in +20% linear [z 1.20] | light | Empty rocking chair still rocking | The chair was still rocking. |
| 52 | 72.75-74.38 | 1.63 | WS | eye | wide | slight pull [z 0.97] | light | Boy and Dad (red flannel) play catch in the front yard | My dad's the best dad in town. |
| 53 | 74.38-75.33 | 0.95 | WS | eye | wide | pan right with runner (≈ 470 px) [z 0.90] | active | Baseball field: kids in red uniforms, outfield wall, grey sky | He coaches my team. |
| 54 | 75.33-76.15 | 0.82 | MS | eye | wide | push-in +8% linear [z 1.08] | light | Dad (red cap) high-fives the boy on the field | He calls me Buddy. |
| 55 | 76.15-77.28 | 1.13 | MS | eye | wide | pan follow (≈ 60 px), no zoom [z 0.99] | active | Dad walks across the red rug, smiling, side view | And every night before bed, |
| 56 | 77.28-78.83 | 1.55 | MS | eye | wide | push-in +10% linear [z 1.10] | still | Dad from behind at a window, checking it | he checks every lock in the house, |
| 57 | 78.83-80.68 | 1.85 | INS | eye | normal | push-in +7% linear [z 1.07] | light | Dad's blocky hand on the gold deadbolt; thumb-turn flips 79.53-79.62 (blue caption) | three times. Nothing gets in here, buddy. |
| 58 | 80.68-81.38 | 0.70 | MS | eye | wide | static [z 1.01] | still | Dad and boy in the hallway by the door (blue caption) | Not on my |
| 59 | 81.38-83.15 | 1.77 | MS | OTS | wide | push-in +5% linear [z 1.05] | still | Behind Mom's chair: boy and Dad seated at the table | watch. This year, it was just the three of us. |
| 60 | 83.15-84.40 | 1.25 | WS | eye | wide | push-in +8% linear [z 1.08] | still | Through a doorframe: the three at the table | Me, mom, and dad. |
| 61 | 84.40-85.12 | 0.72 | MS | eye | wide | push-in +7% linear [z 1.07] | still | Dad (back) and grumpy boy at the table | Dinner was quiet. |
| 62 | 85.12-86.42 | 1.30 | MCU | eye | wide | push-in +17% linear [z 1.17] | still | Mom seated, worried decal, plate of food | Then mom put her fork down. |
| 63 | 86.42-87.97 | 1.55 | MCU | eye | wide | push-in +11% linear [z 1.11] | still | Mom in profile speaking (pink caption) | It should be whoever we need the least. |
| 64 | 87.97-88.75 | 0.78 | CU | eye | wide | push-in +16% linear [z 1.16] | still | Mom looks into the lens (the narrator's POV) | And she looked at me. |
| 65 | 88.75-90.95 | 2.20 | MS | eye | wide | push-in +17% linear [z 1.17] | still | Dad at the table, shouting decal, arm out (slam) | Dad slammed the table so hard the plates jumped. |
| 66 | 90.95-92.65 | 1.70 | MS | low | wide | push-in +18% linear [z 1.18] | still | Dad standing, pointing, O-mouth shout (blue caption) | Nobody in this house goes out there but me. |
| 67 | 92.65-94.40 | 1.75 | MS | OTS | wide | arc right past the boy's head [z 1.05] | light | Mom crying (>< sob decal), hands to face | Mom started crying, but she didn't argue. |
| 68 | 94.40-95.63 | 1.23 | MS | eye | wide | push-in +23% linear [z 1.23] | light | From the porch: Mom's head through the window, rocking-chair back in foreground | On porch night, the whole town |
| 69 | 95.63-97.17 | 1.53 | EWS | aerial high | wide | static-ish (+3%) [z 1.03] | still | Aerial night street: only porch lights and lamps lit | went dark, except the porch lights. |
| 70 | 97.17-98.93 | 1.77 | WS | eye | wide | truck left along the houses (≈ 2060 px in 1.8 s) [z 2.10] | active | Yellow house, then green house with a figure on the porch | Every porch on our street had someone on it. |
| 71 | 98.93-100.50 | 1.57 | MS | eye | wide | push-in +15% linear [z 1.15] | still | Mrs Pell (white bun, red sweater, patterned blanket) rocking, eyes closed | Old Mrs. Pell, wrapped in a blanket, |
| 72 | 100.50-102.02 | 1.52 | MS | eye | wide | push-in +22% linear [z 1.22] | light | Fisher boy (brown hair, navy shirt) tied to a chair with rope, sad decal | the fisher boy, tied to his chair. |
| 73 | 102.02-104.30 | 2.28 | MS | eye | wide | pull -14% + truck [z 0.86] | light | Danny sitting on Mr Wendell's porch | And on Mr. Wendell's porch, Danny from my class. |
| 74 | 104.30-105.42 | 1.12 | MS | eye | wide | follow pan + tilt (≈ 630 px) [z 0.85] | active | Danny's mom walks off down the path with the cash | His mom had taken the money. |
| 75 | 105.42-107.72 | 2.30 | MS | eye | wide | push-in +6% linear [z 1.06] | still | Dad hugs the boy at the door on the red rug; Mom behind, eyes closed | Dad hugged me at the door, longer than he ever had. |
| 76 | 107.72-109.27 | 1.55 | MS | eye | wide | pan follow (≈ 610 px) [z 1.09] | active | Dad walks onto the porch, turns, sits in the rocking chair, grim | Then he went out and sat down in the chair. |
| 77 | 109.27-110.58 | 1.32 | MS | eye | wide | push-in +5% linear [z 1.05] | still | Mom (back) locks the door, boy beside her | Mom locked the door and we waited. |
| 78 | 110.58-112.93 | 2.35 | WS | eye | wide | push-in +8% linear [z 1.08] | still | Night street centre line: lamp heads go dark one at a time toward camera (110.87-112.73) | At midnight, the street lights at the end of the street went out, |
| 79 | 112.93-113.78 | 0.85 | MS | eye | wide | push +12% + truck [z 1.12] | active | Mrs Pell on her porch at night | one by one. |
| 80 | 113.78-115.22 | 1.43 | MS | eye | wide | push-in +9% linear [z 1.09] | still | Boy and Mom peek out a window behind the porch rail, scared | Then we heard the straw creaking. |
| 81 | 115.22-116.30 | 1.08 | WS | low | wide | push-in +14% linear [z 1.14] | light | Scarecrow walks out by the cornfield fence at the end of the street | It came around the corner, |
| 82 | 116.30-117.85 | 1.55 | MS | eye | wide | push-in +18% linear [z 1.18] | still | Mrs Pell rocking calmly, lamp post in foreground | and Mrs. Pell didn't even scream. |
| 83 | 117.85-118.77 | 0.92 | MS | eye | wide | push-in +18% linear [z 1.18] | light | Fisher boy screaming (red O mouth), tied | The fisher boy did. |
| 84 | 118.77-119.82 | 1.05 | WS | eye | wide | whip pan ≈ 150° across the street in ≈ 1 s (ease in/out, no blur) [z 1.04] | active | From a white house to a house where someone knocks on the door | Then the knocking started. |
| 85 | 119.82-121.33 | 1.52 | MS | eye | wide | push-in +10% linear [z 1.10] | still | Two faces in a porch window, rocking chair in foreground | Every house, all the way down. When |
| 86 | 121.33-123.42 | 2.08 | WS>MS | eye | wide | near-static; subject runs at lens [z 0.97] | light | Porch corridor: Danny jumps up and runs toward camera, arms up, then turns | it got to Mr. Wendell's porch, Danny ran. |
| 87 | 123.42-124.30 | 0.88 | MS | eye | wide | follow truck + push +36% [z 1.36] | active | Danny (back) runs to the door | He made it to the door, |
| 88 | 124.30-126.32 | 2.02 | MS | eye | wide | push-in +5% linear [z 1.05] | still | Mr Wendell holds the door shut; Danny's face (red O) in the side glass | and Mr. Wendell held it shut while he banged on it. |
| 89 | 126.32-127.55 | 1.23 | CU | low | wide | tilt up (≈ 210 px) [z 1.23] | active | Scarecrow's long bony claw reaches down to the doorstep, then up to its body and hat | It took him right off the doorstep, |
| 90 | 127.55-128.38 | 0.83 | MCU | eye | wide | push-in +14% linear [z 1.14] | still | Dad on the porch chair, shocked white-eye decal, looking aside | two houses away. |
| 91 | 128.38-130.35 | 1.97 | MS | eye | wide | push-in +17% linear [z 1.17] | light | Front door (dark red wood, gold locks) from inside, Mom and boy in foreground | Then Dad started knocking, soft at first. |
| 92 | 130.35-131.35 | 1.00 | MS | eye | wide | push-in +4% linear [z 1.04] | light | Dad from behind, knocking on the door (blue caption) | Honey, open the door. |
| 93 | 131.35-132.25 | 0.90 | MCU | eye | wide | push-in +13% linear [z 1.13] | still | Mom covers her mouth, crying-brows decal | Mom covered her mouth, |
| 94 | 132.25-133.52 | 1.27 | MS | eye | wide | push-in +4% linear [z 1.04] | light | Dad pounding on the door from behind (blue caption) | then harder. Open the door! |
| 95 | 133.52-134.28 | 0.77 | MS | eye | wide | slight pull -7% [z 0.93] | light | Boy and Mom on the red rug, terrified O_O decals (blue CAPS caption) | Open the door! |
| 96 | 134.28-134.97 | 0.68 | WS | eye | wide | push-in +12% linear [z 1.12] | light | Living room: Mom and boy standing on the rug, silent | Then nothing. |
| 97 | 134.97-136.77 | 1.80 | MS | eye | wide | push-in +13% eased [z 1.13] | still | Mom hugs the boy, crying decal (pink caption) | Mom whispered, He's okay, he's okay. |
| 98 | 136.77-138.27 | 1.50 | MS | eye | wide | push +19% + tilt [z 1.19] | light | Kitchen window from inside: glass bursts into white triangle shards at 137.0 | And then glass smashed in the kitchen. |
| 99 | 138.27-140.38 | 2.12 | MS | eye | wide | push +40% with tilt down [z 1.40] | still | Dad climbs in over the kitchen counter, lands, stands angry | Dad came in through the back window, covered in glass, |
| 100 | 140.38-141.83 | 1.45 | MCU | eye | wide | push-in +13% linear [z 1.13] | light | Dad's crazed face (wild eyes, stubble), starry window behind | with eyes I'd never seen before. |
| 101 | 141.83-143.00 | 1.17 | MS | eye | wide | push-in +4% linear [z 1.04] | still | Mom screaming (O_O, red mouth), dining room | Mom screamed his name. |
| 102 | 143.00-144.03 | 1.03 | MS | high | wide | push-in +21% linear [z 1.21] | light | Dad shoves Mom into the wall (arm pop at 143.1) | He shoved her into the wall. |
| 103 | 144.03-144.80 | 0.77 | MS | eye | wide | tilt [z 1.04] | light | Dad grabs the boy by the table | Then he grabbed me. |
| 104 | 144.80-146.87 | 2.07 | MS | eye | wide | pull -13% + tilt [z 0.87] | light | Through the doorframe: Dad drags the terrified boy toward camera | I grabbed the table, the chairs, the door frame. |
| 105 | 146.87-148.92 | 2.05 | MS | eye | wide | push +16% with slight roll [z 1.16] | light | Dad drags the boy across the red rug (blue caption) | I'm sorry, buddy. I'm sorry. I'm sorry. |
| 106 | 148.92-150.87 | 1.95 | MS | eye | wide | pan (≈ 320 px) [z 1.10] | active | Night porch: the boy is thrown out and tumbles across the boards | He threw me out onto the porch and slammed the door. |
| 107 | 150.87-152.10 | 1.23 | MS | eye | wide | push-in +7% linear [z 1.07] | light | Boy pounds the door with both fists | I hit it with both fists. |
| 108 | 152.10-153.80 | 1.70 | MS | eye | wide | pull -12% [z 0.88] | still | Through the window from outside: Dad and Mom inside, Mom screaming | Inside, Mom was screaming at him. |
| 109 | 153.80-155.22 | 1.42 | MS | eye | wide | pull -16% + truck [z 0.84] | active | Boy at the door turns his head toward the path | Then I heard the creaking on our path. |
| 110 | 155.22-156.98 | 1.77 | CU | ground-level | wide | tracking with the boots (≈ 340 px) [z 0.99] | active | Scarecrow's boots step up the path from sidewalk to lawn | Slow. Every single step. |
| 111 | 156.98-157.75 | 0.77 | MS | eye | wide | push-in +13% linear [z 1.13] | active | Boy turns around at the door, worried decal | I turned around. |
| 112 | 157.75-159.13 | 1.38 | CU | worm's-eye | wide | push +59% + truck [z 1.59] | light | Scarecrow head under the hat brim bending down toward the lens | It was already bending down, |
| 113 | 159.13-160.07 | 0.93 | MS | eye | wide | pull -20% + tilt [z 0.80] | active | Scarecrow head descends into frame beside the boy at the door; porch-corridor background | all the way down, |
| 114 | 160.07-161.85 | 1.78 | MS | eye | wide | push-in +3% eased [z 1.03] | still | Scarecrow face level with the boy | until its face was right in front of mine. |
| 115 | 161.85-162.98 | 1.13 | CU | eye | wide | near-static [z 1.02] | light | Scarecrow face in profile; stitches pop as blur flickers (162.73, 162.87) | The stitches started to pop, |
| 116 | 162.98-163.85 | 0.87 | MS | eye | wide | push-in +14% linear [z 1.14] | light | Boy at the door facing camera, terrified (O_O red mouth); arms pop up at 163.25 | one by one. |
| 117 | 163.85-164.72 | 0.87 | MS | eye | wide | push-in +4% linear [z 1.04] | still | Inside: Dad stands at the door, Mom kneels crying on the rug | And behind the door, |
| 118 | 164.72-166.77 | 2.05 | INS | eye | normal | push-in +7% linear [z 1.07] | light | Same set-up as #57: hand flips the gold deadbolt three times (165.05-166.23) | I heard Dad check the lock three times. |

Evidence: `s/shots_01..10.jpg` (all shots), `full/m_NNN.jpg` (mid frame of shot NNN); `s/m_open.jpg`, `s/c_open.jpg` (#1 transition-in); `s/m_bigA.jpg` (#10, #15, #18); `s/m_rip.jpg` (#15 frame by frame); `s/m_bigB.jpg` (#19, #23, #53); `s/m_bigC.jpg` (#70, #74, #76); `s/m_bigD.jpg` (#84, #86, #89); `s/m_whip.jpg` (#84); `s/m_bigE.jpg` (#99, #106, #109); `s/m_bigF.jpg` (#110, #112, #113); `s/m_walk.jpg`, `s/m_walk2.jpg` (#19, #55, #76, #86); `s/m_rock.jpg` (#3, #13, #51, #52, #82); `s/m_roll.jpg` (#45, #53, #67); `s/m_events1.jpg` (#49 rip, #78 lamps out, #102 shove, #115-#116 stitches pop); `s/m_end.jpg` (#118 lock).

### Shot statistics

| Metric | Value |
|---|---|
| Shots / cuts | 118 / 117. Hard cuts only. Five cuts were missed by the auto threshold and confirmed by eye (75.32, 77.27, 86.40, 87.95, 134.27 s; `s/cand1.jpg`). |
| Cuts per minute | **42.1** |
| Shot length | **median 1.35 s, mean 1.41 s**, min 0.58 s (#35 "One for the porch?"), max 2.43 s (#39) |
| Length histogram | <0.5 s: 0 · 0.5-1 s: 24 · 1-1.5 s: 40 · 1.5-2 s: 36 · 2-2.5 s: 18 |
| Sizes (final framing) | MS 69 · WS 16 · CU 14 · MCU 11 · EWS 3 · MWS 2 · INS 2 · POV 1. Close (CU, MCU, INS): 27 of 118 (23%). |
| Angles | eye 86 · low 12 · OTS 10 (incl. high/low OTS) · high/top/aerial 6 · ground-level 2 · extreme low / worm's-eye 2. The scarecrow is shot from below or at boot level; people at eye level. |
| Lens | wide (≈70° vertical) 116 · normal 2 (the lock inserts) |
| Camera motion | **115 of 118 shots (97%)**. 78 linear push-ins (median +11%, p10 +4%, p90 +21%; ≈ x1.08 per second; 107 s of screen time). 9 pull-outs (-5% to -20%). 25 big moves (≥150 px path). 3 static (#38, #43, #58). |
| Easing | Push-ins linear (quarters 24 / 25 / 28 / 24%). Trucks along house fronts at constant speed: #18 ≈ 11-13 px/frame (≈ 700 px/s), #70 ≈ 15-23 px/frame (≈ 1 200 px/s). The whip pan #84 is a smooth ease-in/out: 26 → 105 → 17 px/frame (peak ≈ 6 300 px/s) over 1.05 s. |
| Subject motion | still 44 shots (63.5 s) · light 48 (67.5 s) · active 26 (35.8 s) |
| Screen time by location | exterior night 49 shots / 66.9 s (40%) · house interior 36 / 53.4 s (32%) · exterior dusk / blue hour / golden 21 / 28.1 s (17%) · exterior day 6 / 8.6 s · cornfield night 5 / 7.7 s · Harper interior 1 / 2.0 s |
| Editor effects | 2: the transition-in (frames 0-7) and the "rip" shake hit (21.93-22.03 s). Everything else is in-engine. |

---

## 2. Characters

Evidence: `s/v_family1..3.jpg`, `s/v_faces1.jpg`, `s/v_town1..2.jpg`, `s/v_int1..2.jpg`, `s/v_misc1..2.jpg`, `s/v_unsure.jpg`.

### 2.1 Construction (all humans)

- **Classic R6**: six blocky parts, **no elbows, no knees**. Limbs bend only at shoulder and hip (see `s/m_walk.jpg`: whole legs swing as single boxes).
- Proportions measured on the standing boy (`full/m_116.jpg`): head ≈ 0.5, torso 1.0, legs ≈ 1.1 (torso = 390 px, legs = 425 px, face 155 px). That is the standard 1.2 : 2 : 2 stud R6 body, about 4.5-5 head-heights tall. All humans share the same body size; kids are not scaled down (the boy and Dad are the same height).
- **Head:** the default Roblox head (rounded cylinder) with a **2D decal face**.
- **Clothing:** **2D shirt and pants textures** wrapped on the boxes (stripes continue across arms, plaid with painted folds and a collar, buttons, suspenders, ties painted on). No 3D layered clothing on humans.
- **3D accessories:** UGC hair meshes (spiky, wavy, buns, curls, shoulder-length grey), hats (flat cap, top hat, bowler, cowboy/straw hats, red baseball cap, knit cap). The hair is semi-realistic, with strand grooves and a slight sheen.
- **Skin:** two tones: warm light "Light orange / Nougat" for the family (lit #cfb690 to #ebc284 in the warm grade) and **pure white #e8e8e8 "classic" faces** for some townspeople (Mr Wendell, Mrs Pell, the knocking grandmother).
- **Props:** green cash stacks (green block + white band), ropes (tan torus rings around torso and legs), plates with yellow and green food blocks, a white ball, a blanket shawl.

### 2.2 The family (consistent across all shots)

| Character | Hair / hat | Shirt | Pants | Typical decals | Caption colour |
|---|---|---|---|---|---|
| **Narrator boy** | **spiky bright-yellow UGC hair** (#d6d060 lit) | **yellow-and-black horizontal stripes** (#c4b160 / #1a0f05), about 10 stripes over the torso, continuing on the arms | black (#25170f) | small frown (sad at the window), O_O with red open mouth (terror), worried brows | white (he is the narrator) |
| **Dad** | dark-brown wavy hair; red baseball cap on the field | **red-and-black buffalo-plaid flannel** with collar (#71150f / #300304 lit) | **tan khaki** with painted folds and a back-pocket tag (#a96b32) | **stubble overlay on every face**: smile, grim frown, O-mouth shout, white-eye shock, the climax "crazed" face (white eyes, tiny pupils, heavy brows, gritted grin) | **light blue #96c8f5** |
| **Mom** | **auburn braided bun** | **olive-green cardigan** with dark placket and buttons (#9d753e in the warm interior, dark green outside) | black skirt | worried brows, >< sob with red mouth and sweat drops, O_O scream, closed-eye calm | **pink #ed99bf** |
| **Grandpa** | grey shoulder-length hair under a **dark flat cap** | cream shirt (#d3ac72 warm) with **dark suspenders** | beige-tan plaid trousers | ^^ laughing with red mouth, closed-eye calm smile; takes the cap off | **yellow #f9dd6e** |

### 2.3 Townspeople (one look each, reused)

- **Mr Wendell:** white classic skin, black top hat or bowler, black three-piece suit with **red tie, gold watch chain, white pocket square**, stern "—" mouth.
- **Danny:** brown curly hair, denim **overalls** over a tan shirt. Panic: red O mouth.
- **Danny's mom:** long brown hair, brown dress, carries a cash stack.
- **Mrs Pell:** white classic skin, white hair bun, **red knit sweater** with a patterned **blanket shawl**, rocking chair, closed-eye calm decal.
- **The Fisher boy:** messy brown hair, navy button shirt, **tied with rope** (tan rings) to his chair; sad, then screaming.
- **Old people on porches:** white buns or grey hair, dark dresses; worried, deadpan or laughing decals.
- **Harper family:** man in cowboy hat and blue gingham shirt, kids, mother in floral dress.
- **Baseball team:** kids in red jerseys, black pants, red caps.
- Townspeople orange caption: "One for the porch?"

### 2.4 The scarecrow (the monster)

Evidence: `s/v_scare1..3.jpg`, `s/m_rip.jpg`, `s/v_corridor.jpg`, `s/m_bigF.jpg`.

- **Scale:** about **3x a human** (≈ 15 studs; taller than the lamp posts in #6). Its head is about 3x the boy's head (#113-#114). Shot from below almost always.
- **Head:** a scaled Roblox-style head shape covered in a **real burlap/sack texture** (#a4855e lit, darker seams, vertical stitch lines).
  - **Face decal A (closed):** two black ragged **eye-holes with radiating stitch "lashes"**, a **wide cross-stitched grin** with stitched dimples.
  - **Face decal B (ripped):** the same eyes over a **huge black mouth hole** filling the lower half of the face, ringed by short **yellow stitch threads like teeth**.
  - A **rope collar** at the neck (twisted-rope texture), then a **white-and-brown ruff** of fabric and straw.
- **Hat:** wide floppy brim + **pointed witch-style crown with a bent tip**, burlap texture (#514839 / #251a11), a **green fabric patch**, **bright-yellow straw tufts** poking out at the brim.
- **Body:** red-and-black **plaid shirt** under a **tattered brown coat** with a jagged hem; **cream straw** (#ddd6c7) bursting from the sleeves and trousers as hundreds of thin strands; **black boots**; long arms.
- **Hand:** long, bony **cream claws** (4-5 tapered fingers, #e8dcae) used to snatch Danny (#89).
- **Materials:** textured, matte, much higher detail than the R6 humans. The contrast "flat toy people vs one detailed textured monster" is what makes it creepy.
- **Cute vs creepy:** fully creepy: no cute features. The horror is the grin, the scale and the slowness.

### 2.5 Consistency

The same avatar is reused in every shot: the yellow hair and bee stripes make the boy readable even from behind (he is shown from behind or as a foreground OTS shape in about 10 shots: #42, #45, #46, #67, #91, #103, #106, #107, #109, #113). Only the grade changes colours: Mom's olive cardigan reads ochre in the amber interiors and dark green at dusk.

---

## 3. Animation

Evidence: `s/m_walk.jpg`, `s/m_walk2.jpg`, `s/m_rock.jpg`, `s/m_bigA..F.jpg`, `s/m_events1.jpg`, `s/m_rip.jpg`, `s/m_end.jpg`.

**Humans (R6):**
- **Walk:** legs swing as rigid boxes about ±35-40° at the hip, about one stride every 0.3-0.5 s; the arms hold a pose (down, holding cash, carrying the boy) rather than swinging. Dad in #55 and #76; Danny's mom in #74; walkers in #19 and #33.
- **Run:** faster leg swing (half-cycle ≈ 0.25 s) with **both arms raised forward to shoulder height** (panic run, Danny in #86).
- **Turns** are quick rotations of the whole body (≈ 90° in 0.1-0.2 s; Dad #76, the boy #109 and #111).
- **Sit:** Dad walks to the chair, turns, and **pops into the sitting pose** in one frame at ≈ 108.6 s.
- **Pose pops** (1 frame, no in-between): Mom's shove arm at 143.1 s; the boy's arms up at 163.25 s; the Harper door snapping shut at 33.78 s; arms raised to the face for crying.
- **Rocking chairs:** smooth sinusoidal pitch, about ±5-8°, period about 2 s, with the sitter rocking in the chair (#3, #51 empty chair "still rocking", #71, #82).
- **Gestures:** pointing (Dad #66), high-five (#54), ball toss (#52), hugging (#75, #97), dragging the boy (#104-#105: the boy's body tilted, legs trailing), the boy thrown and **tumbling across the porch boards** (#106), pounding the door with both fists (#107), knocking (#40, #92, #94), the hand flipping the deadbolt (#57, #118).
- **Faces:** decal swaps only, often on a cut rather than inside a shot. No blinks, no lip movement.
- **Idle:** seated or standing characters are frozen apart from rocking chairs. No breathing.

**Scarecrow (smooth, keyframed):**
- **Walk:** very slow, heavy steps (roughly one step per second); the camera tracks at boot level (#10, #110).
- **Bend:** the torso pitches from upright to ≈ 90° forward over ≈ 1.4 s with ease-in-out (#13); the head lowers into frame beside the boy (#113).
- **Head:** slight sways; dips under the brim before the rip (21.42-21.90 s, ≈ 10 px per frame).
- **Rip:** a decal swap dressed with editor effects (see §6).
- **Claw grab:** the claw sweeps down and lifts Danny (#89), with the camera tilting up after it.

**Objects and set events:**
- **Lamps go out one by one** toward the camera at 110.87, 111.33, 111.47, 111.78, 112.23, 112.48 and 112.73 s (0.15-0.45 s apart). The glass goes dark **and** the light pool goes: the road near the lamps drops from 107 to 63 mean luminance.
- **Glass smash:** the kitchen window bursts into **white triangular wedge shards** flying toward the camera at 137.0 s (physics parts).
- **Deadbolt** thumb-turn flips at 79.53-79.62 s and three times at 165.05-166.23 s.

**How much moves:** 37% of shots have no subject motion; the camera drift carries them. The active shots are walks, runs, the scarecrow's moves and the climax struggle.

---

## 4. Environments

| Location | Built from | Detail |
|---|---|---|
| **Main street** (night, dusk, blue hour, day) | Roblox parts and textured materials ("Bloxburg-style" build) | Straight street, two-lane **asphalt** (#49352a dusk, #565050 lamp-lit) with a **dashed yellow centre line**, **concrete sidewalks** (#41322b night), **grass lawns** with dirt patches (#927a4c / #a08652 golden), **stone foundations**. Identical **two-storey colonial houses** in a row, each with a **full-width front porch**: white square columns, white spindle railings, porch steps, wall lantern, one **rocking chair**. **Clapboard siding** in muted colours: cream, sage green, mustard (#b29753), grey (#978265), white (#aab2cc at blue hour), dark red, blue-grey. White window trim with 6- or 4-pane sashes, **dark shutters** (#4d5353), dark-red doors. **Black Victorian lamp posts** (fluted pole, cross-arm, lantern head) on both sidewalks about every second house. A **cornfield** closes the end of the street; **low grey mountains** on the horizon. |
| **Porch** (many close shots) | Parts | Wide wood-plank floor (#aa742c warm), white columns and railing, white ceiling, a lit window behind (#cbb794 glow). From the end of a porch the joined porches form an **endless white "porch corridor"** (#86, #109-#114): a liminal image. |
| **Cornfield** | Instanced meshes | Dense rows of cream-beige stalks (tapered leaf planes, #d5cfaa) on purple-brown furrowed soil (half-cylinder rows); a wooden fence at the edge. |
| **Family house interior** | Parts + materials | **Cream walls with a vertical-streak Plaster texture** (#c6af7b to #e1bc75 graded), white ceiling (#f2daae), thick **dark wood door frames** and trims (wood grain), **dark wood plank floor** (#501e07), **red rug** in the hall (#801a0e), **front door** dark-red wood (#58170e) with **gold block hardware** (deadbolt, knob, chain of gold balls). Dining room: wood table with a white runner, ladder-back chairs, **cream drum pendant lamp on a black cord** (#e5bf69), plates. Kitchen: counter with a light wood top (#af773a), window. Living room: dark window, small cabinet. Red curtains at the boy's window. |
| **Harper house interior** | Same kit | Wood-panel wainscot, cream wall, open door to the street, rug. |
| **Baseball field** (day) | Flat parts | Grass, dirt infield, white line, dark-green outfield wall with net, bench. Flat grey sky. |
| **Outside the kitchen window** | Lazy backdrop | Black sky plus a **flat grey plane** and a row of corn (visible in #98-#100): a set edge left in shot. |

- **Interior vs exterior:** about 57% exterior night/dusk/day, 32% house interior.
- **Level of detail:** medium. Clean low-poly architecture with good textures, dressed with lots of small parts (lanterns, rails, steps, shutters, chairs). No clutter.
- **Studs:** none. **Water:** none. **Terrain:** flat baseplate lawns; no hills except the distant mountain silhouettes.
- **Skyboxes:**
  1. **Night starfield:** pure black (#000000) with dense small grey-white stars.
  2. **Milky-way galaxy** band (photo skybox, #7b7786 core) behind the scarecrow in #6-#7 and at the edge of #84.
  3. **Dusk:** dark teal-grey zenith (#373d3b) to brown-orange horizon (#77594e) (#2).
  4. **Blue hour:** saturated blue (#3e64b7 to #4f84b0) fading to a **peach horizon** (#d1ad7d), with a few faint stars (#4, #17).
  5. **Golden-hour day:** clear blue sky (#19, #33, #52).
  6. **Overcast flat grey** (#b2b1ac) on the baseball field.

---

## 5. Lighting and colour

### 5.1 Grade by scene (measured on 118 mid frames; "hi" = mean of the top 8% of pixels, "lo" = bottom 8%)

| Scene (shots) | Time / feel | Highlights | Shadows | Frame mean | Mean L / std | Sat | R-B | Key colours |
|---|---|---|---|---|---|---|---|---|
| **Exterior night** (49 shots) | Night: black starry sky, lamp-lit street | **#d2c9b8** (warm cream) | **#000000** (18% of pixels pure black) | #6f5c43 | 97 / 65 | 0.44 | +38 | white siding #d8d0c4, road #565050 lit / #2e2423 unlit, lawn #573f25, lamp glass #d6dcc0, scarecrow sack #a4855e |
| **Exterior dusk, blue hour, golden** (21) | Evening | **#e0c4a6** | #110203 | #7c634a | 103 / 60 | 0.47 | +48 | blue sky #3e64b7 / #4f84b0, peach horizon #d1ad7d, dusk sky #373d3b-#77594e, porch wood #aa742c, sidings #b29753 / #978265 |
| **Exterior day** (6) | Clear golden day / overcast | #e3cba9 | #1b0f0d | #877a5d | 123 / 54 | 0.39 | +36 | sky blue, grey #b2b1ac, red jerseys #c62d23 |
| **Cornfield night** (5) | Black sky, galaxy | #d1cac0 | #000000 (41% black) | #433b30 | 61 / 65 | 0.36 | +31 | corn #d5cfaa, milky way #7b7786, coat #6b442c |
| **House interior** (36) | Night, lamp-lit, **amber** | **#e8cc90** | **#190101** (maroon-black) | **#9a673f** | 112 / 69 | **0.63** | **+89** | wall #c6af7b-#e1bc75, ceiling #f2daae, floor #501e07, rug #801a0e, door #58170e, shade #e5bf69, Mom's cardigan #9d753e |

**Per-frame numbers** are in `colstats.txt` (mean, luminance p1/p50/p99, std, saturation, R-B, clipping, black share, 5-colour palette).

### 5.2 Light and shadow

- **Exteriors, dusk/day:** one **low warm sun** from the side; long **cast shadows** of lamp posts and houses across lawns and walls (`s/m_bigA.jpg` #18, `s/m_bigB.jpg` #19, `full/m_004.jpg`). Shadow edges are soft-ish (a few px of penumbra), as in Roblox ShadowMap/Future lighting. Fill is a cool sky ambient.
- **Exteriors, night:** a **soft moonlight-like key** keeps house fronts readable (white siding stays at #d8d0c4); **street lamps cast real light pools** on the road and sidewalks and throw **shadows of the lamp posts** across the asphalt (`full/m_078.jpg`). Porch wall lanterns and lit windows add warm accents. Shadows go to true black.
- **Interiors:** soft, warm, almost shadowless omni light from the pendant and the ceiling; faint contact shadows under people and furniture; gentle box shading on the R6 limbs (lit side about 25% brighter).
- **Rim light:** none. **Volumetrics / god rays:** none. **Fog:** a light distance haze in dusk wides (far houses lighten); none at night.
- **Practical lights:** lamp glass and porch lanterns are **flat emissive** (#d6dcc0 / #e1bb74) with **hard edges and no halo** (`s/v_glow.jpg`: 212 → 8 in under 5 px).
- **Ambient occlusion:** mild, only in corners and under the table.

### 5.3 Tone, contrast and saturation

- **Highlight roll-off:** p99 luminance 173-236 (median 215) across all 118 shots; clipping is at most 0.08% of a frame. Whites are cream (#d2c9b8 outside, #e8cc90 inside). This is the single biggest "filmic" cue: nothing is ever pure white.
- **Blacks:** crushed to 0 at night (sky and unlit areas); interiors keep a warm maroon-black (#190101).
- **Contrast:** medium-high (luminance std 54-69).
- **Saturation:** moderate outside (0.36-0.47), high inside (0.63) because of the amber cast.
- **White balance:** never neutral. Exteriors are slightly warm (R-B +31 to +48); interiors are strongly amber (R-B +89). Blue-hour skies are the only cool element (R-B -48 in #4).

### 5.4 The look recipe, exactly

This is **"warm small-town Americana at night"**, not pastel dreamcore. The liminal feel comes from **emptiness and repetition**, not from post effects:
1. A **warm amber/sepia cast** on everything, strongest indoors (as if a Roblox ColorCorrection tint of about (1.0, 0.88, 0.62) on the interiors and (1.0, 0.95, 0.85) outside), plus warm light colours.
2. **Highlight shoulder:** whites stop at about 85-92% and turn cream.
3. **Black void skies** with dense small stars (and once a milky way) above lit, readable houses.
4. **Repetition:** identical houses, identical porches, one rocking chair each, lamp posts marching to the vanishing point, the endless porch corridor.
5. **Emptiness:** wide empty streets at blue hour; the street only populated by lone figures on porches.
6. **Clean render:** no bloom, no DOF, no grain, no vignette.
7. **Constant slow push-in** (+11%) on near-still images.
8. **Time-of-day switches by story beat:** night hook, blue-hour/golden exposition, amber interiors for the family, black night for porch night.

---

## 6. Post effects, particles and transitions

| Effect | Present? | Measurement and notes |
|---|---|---|
| Bloom / glow | **No** | Lamp glass profile drops from 212 to 8 within 5 px; no halo on lanterns or the pendant (`s/v_glow.jpg`). |
| Depth of field | **No** | Backgrounds behind CUs are sharp (window, door frames, wallpaper grain) (`s/v_dof.jpg`). |
| Vignette | **No** | Average of all 118 mid frames: corner/centre ratio 1.08; the radial profile rises toward the edges. |
| Chromatic aberration, colour fringes, lens distortion | No | |
| Film grain / noise | No | Only h264 blocking. |
| Motion blur (in engine) | **No** | During the 6 300 px/s whip pan, horizontal gradient energy stays above vertical (`s/m_whip.jpg`). |
| **Editor shake + blur** | **Yes, 2 times** | (a) **Transition-in, frames 0-7**: a blurred, rotated, scaled-down frame (z 0.26, rot up to 18°) snapping into place; frames 1-3 are identical blurred frames; the caption shakes with it (`s/m_open.jpg`, `s/c_open.jpg`). (b) **Rip hit, 21.93-22.03 s**: 6 frames of jolts (±50-76 px vertical, ±1.7° roll, scale 0.95-1.01) with directional blur, on the mouth opening and a tearing SFX (`s/m_rip.jpg`). |
| **Face blur flicker** | **Yes** | The scarecrow face decal is replaced for 1-7 frames by a **blurred copy**: 21.017, 21.133, 21.5 s; 69.60, 69.72 s; 162.73, 162.87 s (`s/m_rip.jpg`, `s/m_events1.jpg`). In the first rip the flicker (21.017), the blur (21.5) and the shake (21.93) each sit on a tearing transient (21.04, 21.52, 21.92-22.06 s). The later flickers have no transient of their own. |
| Light-state changes | Yes | Lamps switch off one by one (110.87-112.73 s). One unexplained lighting pop at 0.98 s in #2. |
| Particles | Almost none | Only the white glass shards (#98) and the straw strands (geometry, not particles). No dust, no sparkles, no stars drifting. |
| Overlays (light leaks, scanlines, letterbox) | No | |
| Transitions | **Hard cuts only** | No fades in or out (the last frame is a normal lock insert), no flash frames, no whip transitions between shots. |

---

## 7. Text and captions

Evidence: `s/cap_crops.jpg`, `s/cap_zoom.png`, `capscan2.json`.

- **Font:** the same CapCut auto-caption style as Tooth Fairies: a heavy geometric grotesque (Montserrat ExtraBold / Proxima Nova Extrabold look), double-storey "a", single-storey "g".
- **Size:** x-height ≈ 50 px; text block with stroke ≈ 57 px for x-height words and ≈ 88 px for words with ascenders and descenders (1316-1404). Font size ≈ 95-100 px on 1080 width.
- **Fill colours (sampled):**
  - narrator: white #fffefe
  - **Dad: light blue #96c8f5**
  - **Mom: pink #ed99bf**
  - **Grandpa: yellow #f9dd6e**
  - **townspeople: orange #f1b16c**
- **Stroke** ≈ 3-5 px black; **soft black drop shadow** offset about +4-6 px down/right. No box or background.
- **One word on screen at a time.** The band is never empty (8 of 10 006 frames).
- **Position:** centred at x = 540; text block 1314-1402, centre **y ≈ 1354 (70.5% of height)**. Fixed for the whole video.
- **Timing:** 741 of 744 ASR words matched a caption change; **median -0.02 s** (caption slightly before the ASR onset), p10 -0.09 s, p90 +0.07 s. Samples: "scarecrow" +13 ms, "Harpers" -20 ms, "Grandpa" +10 ms, "Danny" 0 ms, "Slow" 0 ms, "smashed" -80 ms, "three" 0 ms. The word stays until the next word.
- **Animation: none.** Bounding-box height and width ratios are exactly 1.000 from the first frame of each word. The only movement is the opening shake (frames 8-13).
- **Text rules:** dialogue has **no quote marks**, only colour. Shouting is **ALL CAPS** ("OPEN THE DOOR!" in blue caps at 133.67 s). Proper nouns are capitalised ("Porch Night", "Grandpa", "Mom", "Dad", "Mr", "Pell", "Wendell's"); "Mrs" without a period; punctuation stripped.

---

## 8. Editing and sound-picture sync

**Cuts lead the voice.**
- 76 of 92 sentences start on a cut; 107 of 117 cuts are on a sentence or clause start.
- Cut minus nearest word onset: [-0.2, -0.1]: 40 · [-0.1, -0.05]: 43 · [-0.05, 0]: 22 · [0, 0.05]: 4 · later: 8. **The picture changes 0.05-0.15 s before the word** (median 0.08 s).
- Long sentences get 2-3 shots, split at commas: "It comes out of the cornfields at midnight, / a scarecrow, taller than the streetlights, / straw hanging out of its sleeves, / and a sack for a head, / with a big smile stitched across it." (#5-#9).
- **One picture per noun or list item:** Mrs Pell / the Fisher boy / Danny (#71-#73); table / chairs / door frame inside one dragging shot (#104).
- **Short reaction shots** (0.6-0.9 s) on one-line beats: "One for the porch?" (#35, 0.58 s), "Then nothing." (#96), "I turned around." (#111).
- **Callbacks reuse set-ups:** the lock insert (#57 = #118), the scarecrow-over-the-chair OTS (#1 = #14-#16, #48-#49), the boot-level tracking (#10 = #110), "bends all the way down" (#13 = #112-#113).
- **One sloppy cut:** "Mr. / Wendell" is split across #29-#30.
- **No freeze frames, no speed ramps, no punch-ins.** All zooms are continuous camera moves.

**Picture events on the word:**
- face flicker 21.017 s on "stitches" (21.12), mouth opens 21.9 s on "open" (21.92), shake 21.93 s
- second rip: flicker 69.60 s, "ripped" 69.87, mouth open 70.0
- lamps go out over "went out, one by one" (110.87-112.73; "one by one" 113.1-113.5)
- glass bursts 137.0 s, "smashed" 137.43
- shove pose 143.1 s, "shoved" 143.3
- stitches flicker 162.73 / 162.87, "pop" 162.71
- deadbolt flips 165.05-166.23, "lock three times" 165.75-166.4

**Audio** (UVR-MDX split: `stems/voice.flac`, `stems/inst.flac`):
- **VO:** continuous from 0.04 to 166.8 s, one narrator voice acting all roles; voice stem RMS **-18.4 dBFS**.
- **Music bed:** one tonal track (low pads/keys under 1.5 kHz, pitch classes C, E, F, A strongest; tempo estimate ≈ 134 BPM). Stem RMS **-23.3 dBFS, about 5 dB under the VO.** In 2-s windows: -26 dB for 0-42 s, louder **-21/-22 dB for 42-130 s**, quieter **-28 dB for 132-150 s** (the break-in and drag), back to -24/-25 dB to the end. No stingers.
- **SFX** (high-frequency transients in the music stem where the voice is quiet):
  1. **Straw creak** 14.45-14.75 s and 15.8-16.15 s, around "creak" (14.96).
  2. **Tearing hits** 21.04, 21.36, 21.52 and a sustained tear 21.92-22.16 s, on the face flicker (21.017), the blur (21.5) and the shake hit (21.93). A single hit at 70.02 s when the second mouth opens (70.0).
  3. A weak **glass hit** at 137.04 s (the window bursts at 137.0). Other weak hits around 39.8, 43.2, 66.6, 113.2 ("straw creaking") and 138.3-140.5 s (Dad's entry).
  4. **Stitch pop** 163.12-163.20 s, on "one" (163.11), not on the face flickers (162.73-162.87).
  5. **Three lock clicks** 165.46-165.52, 165.90-165.98 and 166.40-166.56 s, roughly on the deadbolt turns (picture events 165.05-166.23).
  - Knocking, the table slam and the door slam are **not** clearly audible as separate SFX; the narration carries them.
- The owner adds music himself. To match: keep the bed about 5 dB under the voice, let it rise a little in the middle act and drop before the climax. Add the creaks, tears, pops and lock clicks on the picture events.

---

## 9. What makes it look premium, and how to get there in Three.js

### 9.1 Premium drivers (ranked by impact)

1. **One detailed, textured monster against flat toy people**: the burlap scarecrow with stitched face, straw strands, tattered coat and claws, shown huge and from below.
2. **Coherent warm grade with a highlight shoulder:** amber interiors, golden dusk, black-sky nights, and nothing ever clips.
3. **A believable small-town set:** a long street of identical porched houses with lamp posts, cornfield and mountains; real cast shadows; lamp pools.
4. **Rhythm:** about 1.4-s shots cut just before the words, one picture per idea, every shot drifting forward.
5. **Characters that act:** walks, runs, rocking chairs, hugs, a drag, a throw, plus speaker-coloured captions that make dialogue readable.
6. **Synced horror hits:** decal swap + blur flicker + shake + tearing SFX on the same frame.
7. **True 60 fps** smoothness and a clean image with no gimmick filters.

**Cheap tells in the reference (do not copy):**
- pose pops (sit-down, arms up, shove) and the door snap
- frozen idles, no blinks, no lip-sync
- the flat grey backdrop plane outside the kitchen window
- the light pop at 0.98 s
- the "Mr. / Wendell" split across a cut
- the blurred-face flicker looks like a texture-loading glitch when seen frame by frame (keep it short and SFX-locked if used)

### 9.2 Hard to reproduce in Three.js, and the best approximation

| Look | Difficulty | Best approximation (procedural, SwiftShader-friendly) |
|---|---|---|
| **Scarecrow** | **Hardest** | Build a ~3x R6-proportioned rig (≈ 15 studs) with its own geometry: head = `LatheGeometry` rounded cylinder with a **procedural burlap `CanvasTexture`** (cross-hatched weave noise, #a4855e base, darker seams) + normal map from the same noise; face drawn on a second canvas layer (decal A: ragged black eye-holes with stitch lashes, cross-stitched grin; decal B: black mouth hole with yellow stitch teeth) and swapped by `map` change. Hat = lathe brim + cone crown whose tip vertices are bent sideways, burlap texture, a green patch plane, yellow straw tufts (thin boxes). Coat = boxes with an alpha-tested jagged hem texture. **Straw** = `InstancedMesh` of 300-800 thin cream boxes (0.03 x 0.6 studs, #e8dcae) splayed from cuffs, neck and legs with random tilt. Claws = 4-5 `CylinderGeometry` cones in bone colour. Shoot it from below with the wide lens. |
| R6 humans | Easy | Boxes with 0.05-stud bevel; head = rounded-cylinder lathe; shirt/pants as `CanvasTexture`s (bee stripes ≈ 10 per torso, buffalo plaid #71150f/#300304 with collar, olive cardigan with placket, suspenders, overalls, suits with red tie and watch chain). Hair as merged low-poly blobs (spiky = cones on a cap; bun = torus + sphere; wavy = displaced cap). Decal faces drawn in canvas (O_O, ><, ^^, worried, stubble overlay, Dad's crazed face). Add subtle breathing and blinks: better than the reference and still on style. |
| Clapboard houses, porches, street | Medium | One parametric house generator (width, colour, door/window layout) with canvas siding texture (horizontal plank lines every ~0.6 stud + grain noise), white trim boxes, shutters, porch (columns, spindle railing via `InstancedMesh`, steps, lantern, rocking chair). Place 10-14 per side along a straight street; asphalt plane with noise + yellow dashes; sidewalks; grass with dirt-patch noise; lamp posts every ~2 houses (instanced). Corn rows = instanced tapered planes; distant mountains = low-poly grey silhouettes. |
| Interiors | Medium | Plaster wall texture (vertical streak noise, cream), wood floors (stretched-noise grain, #501e07 after grade), thick wood door frames, red rug, door with gold block hardware, drum pendant (cylinder + emissive bottom), table, ladder-back chairs. |
| Lighting + shadows | Medium on CPU | Exterior day/dusk: one `DirectionalLight` (warm, low sun) with `PCFSoftShadowMap` 2048, tight shadow frustum per shot + `HemisphereLight` sky/ground. Night: dim cool directional "moon" (no or low-res shadows) + `PointLight`s only for the 4-6 lamps nearest the camera (decay 2, distance ~30 studs, warm white), the rest emissive-only with **additive "light pool" decals** on the road. Interior: `HemisphereLight` + 1-2 warm `PointLight`s, no shadows (or one soft shadow from the pendant). |
| Grade | Easy | `OutputPass`, then a `ShaderPass`: per-scene gain toward the measured whites (interior gain ≈ (0.91, 0.80, 0.57) at the top with saturation x1.25; exterior night ≈ (0.82, 0.79, 0.72); dusk ≈ (0.88, 0.77, 0.65)), a **highlight shoulder so p99 lands at 0.82-0.90**, blacks at 0 outdoors at night and lifted to a maroon (#190101) indoors. ACES or AgX tone mapping at exposure ≈ 0.9 helps the shoulder. |
| Skies | Easy | Night: black background + `Points` star field (2-4k stars, 1-3 px, grey-white) + optional milky-way band (noise texture on a great circle). Dusk / blue hour: vertical gradient shader with the measured stops (#373d3b → #77594e; #3e64b7 → #4f84b0 → #d1ad7d). Overcast: flat #b2b1ac. |
| Camera grammar | Easy | Wide lens: 70° vertical FOV. Per shot a **linear push of +11%** (p10-p90 +4% to +21%) as a dolly or FOV zoom; 1 shot in 12 a slow pull-out; 1 in 5 a big move: truck along the house fronts at 700-1 200 px/s, boot-level tracking, tilt-ups on the monster, follow pans, one ease-in/out whip pan (≈ 150° in 1 s). |
| Editor hits | Easy | Post pass with a camera jitter (±50-76 px, ±1.7° for 6 frames, decaying) + directional blur (a few accumulated offsets) on the rip; a 0.12-s blur-and-snap transition-in on frame 0; optional 1-frame face-texture blur flickers locked to SFX. |
| Glass smash | Easy | 30-60 white triangle `Mesh`es with simple ballistic motion and spin from the window plane toward the lens. |
| Frame rate / resolution | Easy | True 60 fps at 1080x1920 (matches the reference here), FXAA or SMAA; the reference detail is only 540-720p, so no supersampling is needed. |
| Captions (if we do them) | Easy | Montserrat ExtraBold ≈ 96 px, white or speaker colour (#96c8f5 / #ed99bf / #f9dd6e / #f1b16c), 4 px black stroke, soft shadow (+5, +5), centred at y ≈ 1354, one word at a time, switched on the word onset, no animation, CAPS for shouting. |

### 9.3 Production rules to copy

- Shots of about 1.2-1.6 s, **cut 0.05-0.15 s before the sentence or clause starts**, one picture per noun in a list.
- Every shot drifts: a +8-15% linear push by default; a big move (truck, track, tilt-up, whip) every 4-6 shots.
- Most shots MS at eye level; the monster from below or at boot level; inserts for key props (the lock).
- Faces change by decal swap on the beat; horror beats get decal swap + blur flicker + shake + SFX on the same frame.
- Night = black starry sky + lamp pools + readable houses; interiors = warm amber; exposition at blue hour or golden hour.
- Reuse set-ups for callbacks (the same lock insert, the same over-the-chair angle, the same boot-level track).
