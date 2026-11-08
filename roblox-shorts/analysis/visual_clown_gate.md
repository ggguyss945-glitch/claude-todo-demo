# Visual analysis: "Clown Gate" (reference r5)

Reference only: we copy the **look, construction and film grammar**, not the clown, the rule, the characters or the lines.

- **Source:** `ref60/clown_gate.mp4`, the full upload. It is **1080x1916** (not 1920), 60 fps, 127.62 s (7657 frames), h264 at 1.63 Mb/s, with AAC 44.1 kHz stereo.
  - Picture starts at frame 0. The old trimmed copy's 2.27 s gap is gone: the real opening is a flat-cap man jumping at the barrier arm, not the clown.
  - Real detail is **about 540-720p**. A 540x958 round trip loses little (PSNR 38.5 dB); a 720p round trip loses almost nothing (42.7 dB).
- **Evidence folder:** `$CG` = `/tmp/claude-0/-home-user-claude-todo-demo/353ac1d9-152b-55bb-bdf1-0625e0fc6a83/scratchpad/rbx/cgv`. It is in scratch and not in the repo, because the frames are copyrighted.
  - `sh/cg_1..4.jpg`: 1-s frame sheets (128 frames).
  - `s/shots_01..09.jpg`: first, middle and last frame of every shot. These sheets were made before the final merge, so they show 105 cells. Sheet cells #94+#95 are one shot here (#94), and sheet cells #96-#105 are shots #95-#104.
  - `full/m_###.jpg`: one full-resolution mid-frame per shot (104 frames). `full/t_*.jpg` holds extra stills.
  - `m/*.jpg`: 60-fps strips and crops. These include `walk_kid`, `walk_pell`, `gest_a`, `gest_b`, `turn96`, `face_swap`, `s01`, `s02_04`, `s18`, `s28`, `s66_70`, `tr_5100`, `tr_5470`, `tr_5755`, `tr_6475`, `tr_6865`, `cappop`, `capcrops`, `cap_quotes`, `specks`, `glow`, `outline`, `bg_sharp`, `measure35` and `avg_all`. The `v_*.jpg` files are character and environment mosaics.
  - `m/spec_0..2.png`, `spec_zoom*.png`: spectrograms of the music and SFX stem. The UVR stems were deleted to save disk; `sep_cg.py` regenerates them in about 1.5 min.
  - Data: `cuts_final.json`, `shotmotion.json`, `colstats.txt`, `resid.json`, `capscan.json`, `feat.npy`, `motion.npy`, and `asr_cg.json`/`.txt` (a new ASR run of this full copy, 532 words).
  - Scripts: `diff.py`, `motion.py`, `cadence.py`, `feat.py`, `capscan.py`, `colstats.py`, `resid.py`, `parallax.py`, `samp.py` and `strip.py`.
- **Method:**
  - Cuts come from per-frame difference plus a histogram jump, and every doubtful cut was checked in a strip.
  - Camera motion comes from LK optical flow plus a RANSAC similarity fit on every frame.
  - Subject motion is the residual after camera compensation.
  - Cadence comes from residuals at 270x480.
  - Colour comes from k-means and pixel samples.
  - Captions were scanned on every frame against ASR word onsets.
  - Audio was split into voice and music with UVR-MDX.
  - I looked at about 450 frames: 128 in the sheets, 315 shot-sheet cells, about 260 strip frames and about 50 full-resolution frames.

## 0. The 16 facts that matter most

1. **It is Roblox Studio, screen-captured, then edited in a CapCut-style editor.**
   - Signs:
     - R6 blocky avatars with catalog 2D decal faces.
     - UGC hair, hats and hoods.
     - Roblox materials: Wood planks, Brick, Fabric/knit, Slate.
     - Terrain grass and dirt.
     - Atmosphere fog, a SunRays sun halo, ParticleEmitter dust and a **Highlight outline**.
   - Everything is built from parts. **The "creature" is itself a parts-built wooden clown statue**: cylinders, spheres, wedges and planks.
2. **The picture has 48 unique frames per second inside the 60 fps file, with a 1-1-0-1-2 judder.**
   - In every 5 frames, one frame repeats and the next one jumps 2 steps. The pattern is measured in all sampled shots.
   - Camera zooms stall on the repeated frames, so camera moves were recorded in the engine.
   - Captions change on repeated frames as often as on any other frame (9% vs 9%), so text and overlays were added at 60 fps in the editor.
   - **Our true 60 fps will be smoother. Keep it.**
3. **Fast, word-locked cutting.**
   - 103 cuts make 104 shots in 127.6 s: **48.4 cuts per minute**.
   - Shots: **median 1.17 s, mean 1.23 s**, range 0.45-3.03 s (p10 0.63, p90 1.78).
   - **93 of 103 cuts land within ±0.1 s of a word onset**, and 101 within ±0.2 s. The median cut is 0.02 s *before* the word.
   - **56 of 60 sentences start on a cut.**
   - The only two cuts off a word sit in the two silent beats (23.33 dust puff, 115.85 back of the clown's head).
4. **Every shot moves (104/104).**
   - House style: a **linear, centred push-in**. 90 of 104 shots push. The median is **+14.7%** per shot (p10 +8.7%, p90 +27.8%), at about +14%/s. Each quarter of the shot carries 25% of the zoom.
   - 10 shots pull back or recede.
   - 8 shots carry big translations: the 1470-px arm pan, the 930/500-px wall tilts, the 3-s wall pan with whip, the 2.65-s road dolly with a 42° roll, and the 1414-px arm pan at dusk.
   - Accents: a ×3.4 snap pull-back opens the video (#1), an accelerating ×2.36 push with roll introduces the clown (#2), and a ×1.67 push with a 13° roll lands the twist (#56).
5. **Characters barely act.**
   - In 48 of 104 shots under 1% of pixels move once the camera is compensated, and only about 20 shots show real body motion.
   - Motions:
     - walks: default-style R6 swing, about a 0.75-s cycle
     - a hands-to-head snap in 8 frames
     - a jump
     - a kneel-and-brush
     - a drag
     - a 180° turn in 14 frames
     - a hand-on-shoulder in 16 frames
     - the clown's head rotating 180° in about 2 s
   - Faces are decals that change **between** shots, never animated inside one.
6. **Colour follows the clock in 4 worlds**, with measured medians (section 5):
   - **Grey-green fog day** (0-72 s): fog/sky about #6a7b68 to #808a71. The grade is olive and warm (R-B about +44), saturation 0.39, and highlights only reach about #bab083 (p99 L 195). It is low-key and flat, with no clipping.
   - **Warm wood barn interior** (31-54 s): saturation 0.66, R-B +103.
   - **Orange sunset and orange fog** (72-91 s): sky #bb541a, saturation 0.68-0.75.
   - **Purple dusk** (91-112 s): mean #524249, saturation 0.32, R≈B, then **blue-violet night** (112-128 s): sky #0a0e27, road #494261.
7. **Fog is the main "liminal" device.**
   - Thick distance fog swallows everything past about 20-40 studs, and there is no visible sky in the gate scenes.
   - Characters vanish into and emerge from fog. A real white-out transition (16.5-18.3 s) does it.
8. **The post-production look switches at 85.03 s**, the moment they step into the fog. This is "act 3". Before 85 s the picture is clean. From 85.03 s on:
   - **Vignette:** corner/centre luminance falls from 0.82-0.95 to 0.49 (orange fog), then **0.33-0.36** (dusk) and **0.30** (night).
   - **Glitch transitions** on 16 of the 38 cuts: 5-9 frames of semi-transparent full-width **red (#d84040) and cyan (#3ed0e8) bars** about 50% opaque, plus thin horizontally offset image slices.
   - **White flash-in transitions** on 3 cuts: about 55% white for 2 frames, then 40% and 12%, then gone.
   - **Dust specks:** 4-6 px white and dark dots, each living about 3 frames at random positions, 60-fps animated.
   - Lifted, hazy, desaturated purple grade.
9. **Bloom is mild.**
   - Lanterns glow, but halos are small.
   - Whites burn only on paper and the calendar: shot #36 is 56% clipped.
   - Backlit night foliage gets silvery edge highlights.
   - **There is no DOF, no chromatic aberration, no motion blur, no lens distortion and no grain before 85 s.**
10. **The clown is the visual hook and is used as a recurring "face" insert.**
    - 34 of 104 shots are the clown or its sign, arm and plates.
    - Its pupils sit at the bottom of the glasses rings from the very first shot. That is a fair-play clue built into the design.
11. **Diegetic text carries the plot.** Signs, plates (8/9/10/12/20 FEET), road markings (1 FT…7 FEET), wall notches with heights and years, a calendar and a door plaque are all set in a bold geometric sans.
12. **Captions are CapCut auto-captions.**
    - One lowercase word at a time, white (#f9f9f9) bold geometric sans.
    - x-height about 44 px, about 84 px font size at 1080 wide.
    - About 5 px black stroke plus a soft shadow. Baseline at y = 1382 (72% down), centred.
    - **1-frame pop**: the first frame is at about 92% scale, then 100%.
    - Numbers are written as digits. Captions switch on the word (median +0.013 s) and are almost never empty (1.1% of frames).
13. **Hook:** the first frame is already an extreme close-up mid-motion. A ×3.4 snap pull-back reveals the man jumping at the out-of-reach arm, and the clown follows at 2.25 s.
14. **Sound bed:**
    - 0-72 s: a playful-creepy plucked or mallet ostinato about 10 dB under the voice (music RMS about -33 dBFS vs voice -22 dBFS).
    - **A sub-boom at 72.2 s** on the twist ("…your shadow"). After it, a dark sustained pad runs to the end.
    - A second sub-boom at 104.4 ("Eight feet").
    - Whoosh or glitch hits on the late fast cuts (107.47, 107.92, 116.6).
    - Music dropouts as "silence beats" at 79.1, 97.5 and 115.6-115.9.
15. **Production values are uneven, in an intentional "Roblox" way.** Faces are flat decals, limbs are rigid boxes and poses pop. The premium comes from the set dressing, the fog, the colour progression, the camera that never stops, and the editing.
16. **Sloppy bits we should not copy:**
    - the 48-fps judder
    - blocking and banding on the flat fog gradients (low bitrate)
    - a 0.6-s empty-caption gap at 116.12-116.73 before "I"
    - faceted low-poly trees placed next to photoreal mesh trees in the same frame (#10, #55)
    - the red Highlight outline that appears on the clown's head in only one shot (#97)

---

## 1. Shot list

Legend:
- **In** is how the shot begins: hard cut, glitch-in, flash-in or fog-white.
- **Lens:** W ≈ wide, about 70° vertical FOV (the Roblox default, visible perspective stretch on low angles and top-downs). N ≈ normal, 40-50°. T ≈ tele/insert, 20-30°, with flat perspective on wall and sign close-ups. These are rough estimates from perspective cues.
- **Camera:** the description of the move, then the **measured** total zoom (+ is push, − is pull), the path length in px of 1080 when over 60 px, and the roll in degrees when over 2°.
- **Words:** the narration spoken under the shot (from ASR word onsets).

| # | Time (s) | Dur | In | Size | Angle | Lens | Camera (measured: zoom %, path px, roll°) | On screen | Words |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.00–2.25 | 2.25 | start | ECU→MS | eye, rolled | W | fast pull-back ×3.4 (78% done in first 25%), roll −19° levels out, drift right (-71%, 1705 px, -19°) | Flat-cap man (suspenders) jumps at the barrier arm, arms up; townsfolk at frame edges; fog | In this town, there's a sign at the only road out. |
| 2 | 2.25–3.53 | 1.28 | cut | MS→CU | low (worm's-eye) | W | accelerating push ×2.36 + roll +12° (+136%, +12°) | Clown full figure → face | You see, it's a wooden clown. |
| 3 | 3.53–4.77 | 1.23 | cut | ECU | slightly low | N | linear push (+33%) | Clown face: red ball nose, glasses eyes, wooden teeth | Big painted grin. |
| 4 | 4.77–6.03 | 1.27 | cut | MS | low | W | fast pan/truck along the arm (≈1470 px, ease-out) (+28%, 1495 px, +8°) | Striped barrier arm from sign/post out to the white glove; flat-cap man looks up at the end | One arm stretched out flat. |
| 5 | 6.03–7.15 | 1.12 | cut | CU | low | N | linear push (+24%, +3°) | Sign plank YOU MUST BE THIS TALL TO LEAVE | And under the arm it says, |
| 6 | 7.15–8.73 | 1.58 | cut | MS | low | N | linear push (+12%) | Post, arm, sign and farm gate in fog | you must be this tall to leave. |
| 7 | 8.73–10.42 | 1.68 | cut | MS | low | W | linear push (+25%) | Flat-cap man under the arm, reaching up, 'o' mouth | The arm is seven feet off the ground. |
| 8 | 10.42–12.10 | 1.68 | cut | WS | eye | N | linear push (+23%, +5°) | 5 townsfolk lined up before the gate (knee-high Mrs. Pell already there) | Nobody in this town is seven feet tall. |
| 9 | 12.10–13.77 | 1.67 | cut | MWS | eye, from behind | N | slow linear pull-back (-26%) | Red-haired + flat-cap men walk toward the gate into fog | Nobody has left in 90 years. |
| 10 | 13.77–14.50 | 0.73 | cut | MCU | eye | N | linear push (+14%, +4°) | Red-haired man snaps hands to head (8 frames); village houses | People still try. |
| 11 | 14.50–15.67 | 1.17 | cut | MS | eye | N | side follow (truck), no zoom (+3%, 71 px, +3°) | Red-haired man walks past the red barn | They walk up to the clown, stand |
| 12 | 15.67–16.48 | 0.82 | cut | MCU | low | N | push, roll −5° (+21%, 89 px, -5°) | Red-haired man under the arm, stormy sky, church | under the arm, |
| 13 | 16.48–18.00 | 1.52 | cut | MS | eye | N | slow pull; fog white-out over last 1.3 s (-11%, 107 px, +2°) | He walks into the fog (frame mean L 123→189) | and walk through the gate into the fog. |
| 14 | 18.00–20.23 | 2.23 | fog-white | MS→MCU | eye | N | push (ease-out); fog clears from white in 0.3 s (+23%, 244 px, -4°) | Ghost figure walks out of the fog, head down | A minute later, they come walking back out of the fog, facing |
| 15 | 20.23–20.83 | 0.60 | cut | MCU | eye | N | punch-in jump cut + push (+28%, 135 px) | Same man closer, sad | town. |
| 16 | 20.83–21.78 | 0.95 | cut | MS | low | N | linear push (+21%) | Man, now shorter, under the arm | one inch shorter. |
| 17 | 21.78–23.33 | 1.55 | cut | CU | low | N | linear push (+28%) | Clown face and ruff | And every time somebody fails |
| 18 | 23.33–24.03 | 0.70 | cut | ECU | eye | N | push (+17%, 83 px) | Clown shoulder joint: warm dust-puff burst (no words, the only pause) |  |
| 19 | 24.03–25.72 | 1.68 | cut | MS | low | N | linear push (+19%) | Shrunken man drops arms, looks up at the raised arm | the clown's arm goes up one inch. |
| 20 | 25.72–26.88 | 1.17 | cut | MS | eye | N | linear push (+17%) | Mrs. Pell at her door (THE PELLS sign, 2 lanterns, baskets) | Mrs. Pell next door has |
| 21 | 26.88–28.15 | 1.27 | cut | CU | eye/slightly high | N | push + drift (+17%, 139 px) | Tally marks (wooden sticks) on a stone wall, leafy plant in front | tried forty one times. |
| 22 | 28.15–29.27 | 1.12 | cut | WS | eye | N | linear push (+19%, -3°) | Knee-high Mrs. Pell next to the kid (narrator's first appearance) | She's three feet tall now. |
| 23 | 29.27–30.90 | 1.63 | cut | MS | eye | N | dolly back with subject (~170 px drift), no zoom (+0%, 176 px, +4°) | Mrs. Pell walks down the street toward camera | She still walks to the gate every Sunday. |
| 24 | 30.90–32.58 | 1.68 | cut | MS→MWS | eye | N | pull-back −41% (ease-out) reveal (-41%, +2°) | Grandpa in front of the height wall | My grandpa keeps a wall in his barn. |
| 25 | 32.58–34.32 | 1.73 | cut | MCU | eye | N | linear push (+21%) | Boy being measured: a hand lays a ruler/book on his head | Every kid in our family measured every birthday |
| 26 | 34.32–35.98 | 1.67 | cut | ECU | eye | T | tilt up 930 px (smooth) (-6%, 932 px) | Carved 1934 at the bottom, notches climbing | since 1934. |
| 27 | 35.98–36.98 | 1.00 | cut | ECU | eye | T | tilt up 500 px + push (+12%, 499 px) | Notch column with years | Most notches go up. |
| 28 | 36.98–40.02 | 3.03 | cut | ECU | eye | T | 3 s: slow tilt up Dad's column, whip right (peak 8500 px/s), pan down-right along descending notches to the red 5'2" (+73%, 4819 px) | Dad's notches | My dad's notches go up until he turned twenty, then they start going down. |
| 29 | 40.02–40.55 | 0.53 | cut | ECU | eye | T | linear push (+11%) | 6'0" notch | 6 feet, |
| 30 | 40.55–41.18 | 0.63 | cut | ECU | eye | T | linear push (+12%) | 5'11" notch | 5'11, |
| 31 | 41.18–41.75 | 0.57 | cut | ECU | eye | T | linear push (+13%) | 5'10" notch | 5'10. |
| 32 | 41.75–43.88 | 2.13 | cut | MCU | eye/slightly low | N | push, roll +5° (+11%, 124 px, +5°) | Dad walking, stormy sky, church, houses | Every year, on his birthday, he tries the clown. |
| 33 | 43.88–46.35 | 2.47 | cut | MS→MCU | eye | N | push (accelerating) (+25%, 298 px) | Dad walks out of fog (silhouette → colour) | Every year, he comes back out of the fog a little smaller. |
| 34 | 46.35–47.37 | 1.02 | cut | MCU | eye | N | linear push (+20%) | Dad, sad, red 5'2" mark at head height | He's 5'2 now. |
| 35 | 47.37–48.40 | 1.03 | cut | WS | eye | N | linear push (+13%) | Dad and kid side by side, same height; JUNE/SAM/TOMMY; calendar | I'm almost as tall as him. |
| 36 | 48.40–49.43 | 1.03 | cut | ECU | eye | N | linear push (+21%) | Calendar NOVEMBER, 5 circled red, DAD'S BIRTHDAY (56% of pixels clipped) | Tomorrow is his birthday. |
| 37 | 49.43–50.73 | 1.30 | cut | MS | eye | N | push + slight pan (+14%, 79 px, -4°) | Kid in front of a house at dusk (purple sky), sad | I found him in the barn that night, |
| 38 | 50.73–51.67 | 0.93 | cut | MCU | eye, 3/4 profile | N | linear push (+11%) | Dad in the dark barn: red wall, hay, lantern | staring at the wall. |
| 39 | 51.67–52.83 | 1.17 | cut | MCU | eye | N | punch-in + push (+12%) | Dad, angry-determined brows | One more try, he said. |
| 40 | 52.83–54.38 | 1.55 | cut | MCU OTS | eye | N | linear push (+16%) | Dad sad-eyed; kid's green hood in the left foreground | One of these years it's gonna let me through. |
| 41 | 54.38–55.88 | 1.50 | cut | MS | eye | N | lateral tracking with the kid (~280 px), no zoom (+1%, 298 px, +5°) | Kid walks past the red barn | So I went to look at the clown myself. |
| 42 | 55.88–57.05 | 1.17 | cut | MS | low | W | linear push (+27%) | Clown upper body | Up close, he's worse. |
| 43 | 57.05–58.38 | 1.33 | cut | ECU | eye | N | linear push (+32%) | Hat, glasses eyes, nose | Paint peeling off his face. |
| 44 | 58.38–59.38 | 1.00 | cut | ECU | eye | N | linear push (+19%) | Nose and splinter teeth | Splinters for teeth |
| 45 | 59.38–60.10 | 0.72 | cut | ECU | eye | N | linear push (+23%) | Glasses eyes and nose | and his eyes. |
| 46 | 60.10–61.07 | 0.97 | cut | CU | low | W | linear push (+13%) | Clown face; sun halo and sun rays in the sky | His eyes don't look at you. |
| 47 | 61.07–61.73 | 0.67 | cut | ECU | eye | T | linear push (+14%) | One eye: the pupil sits at the bottom of the ring | They never have. |
| 48 | 61.73–62.43 | 0.70 | cut | MS | low | N | linear push (+13%) | Clown looking down | They looked down |
| 49 | 62.43–63.10 | 0.67 | cut | insert | top-down POV | N | linear push (+14%) | Dirt road, kid's leg entering | at the road. |
| 50 | 63.10–64.37 | 1.27 | cut | MS | eye | N | linear push (+14%, 78 px, +4°) | Kid walks toward camera, 'o' mouth | I knelt down where he was staring. |
| 51 | 64.37–66.15 | 1.78 | cut | MS | high | N | push, roll +5° (+15%, +5°) | Kid kneels and brushes dirt; dust puffs; white lines appear | Under the dirt, faded white lines |
| 52 | 66.15–66.98 | 0.83 | cut | CU | top-down | N | linear push (+9%, +4°) | Ruler lines 1 FT 2 FT 3 FT; kid's hand at edge | painted on the road, |
| 53 | 66.98–67.62 | 0.63 | cut | WS | ground level | W | linear push (+22%) | Ruler lines receding to the gate in fog | like a ruler, |
| 54 | 67.62–70.27 | 2.65 | cut | CU travelling | ground level | W | 2.65 s dolly forward along the road 0→7 FEET (3170 px), roll −42°, ×1.91 (+91%, 3201 px, -42°) | Ends on kid's feet at 7 FEET | and way out at the end, a line marked seven feet. |
| 55 | 70.27–71.23 | 0.97 | cut | MCU | eye | N | linear push (+21%, 75 px, +3°) | Kid realising, 'o' mouth, houses | He's not measuring you, |
| 56 | 71.23–72.35 | 1.12 | cut | MCU→CU | eye | N | fast push +67% with roll +13° (+67%, +13°) | Kid shouting (the twist) | he's measuring your shadow. |
| 57 | 72.35–74.43 | 2.08 | cut | WS | top-down | W | slow rise (pull −13%) (-13%) | Kid on the ruler at noon, round puddle shadow | At noon, your shadow is a puddle under your feet, |
| 58 | 74.43–75.20 | 0.77 | cut | MS | eye | N | linear push (+18%, -5°) | Kid at the gate in orange sunset; clown legs and sign behind | but at sunset |
| 59 | 75.20–76.93 | 1.73 | cut | MS | eye | N | dolly back with subjects + push (+13%, 129 px, +6°) | Kid drags Dad past the red barn | the next night I dragged my dad to the gate, |
| 60 | 76.93–78.42 | 1.48 | cut | WS OTS | eye/high | N | slight pull + drift (-4%, 101 px, +4°) | Gate silhouetted in orange haze; kid's head at frame bottom | right as the sun touched the hills. |
| 61 | 78.42–80.17 | 1.75 | cut | MS | top-down | W | slow drift (+3%, +3°) | Kid and Dad on the ruler; long shadows | Our shadows stretched out across the road. |
| 62 | 80.17–81.15 | 0.98 | cut | CU | top-down | W | truck right 117 px + push (+9%, 123 px) | Shadows across 4 FT / 5 FT | Past five feet, |
| 63 | 81.15–81.77 | 0.62 | cut | CU | top-down | W | linear push (+8%) | Shadows over 6 FT / 7 FEET | past six, |
| 64 | 81.77–83.02 | 1.25 | cut | MS | low | W | linear push (+22%) | Road with shadows past 7 FEET; Dad's legs at top | past the seven foot line, |
| 65 | 83.02–84.28 | 1.27 | cut | WS | top-down | W | rise/pull −25% + roll −15° (-25%, 458 px, -15°) | Shadows way past the lines | way, way past it. |
| 66 | 84.28–85.03 | 0.75 | cut | MCU | eye/slightly low | N | push (ease-in) (+13%, 121 px, +2°) | Kid determined, sunset village | We stepped through, |
| 67 | 85.03–85.70 | 0.67 | glitch | MS | eye | N | slight pull (-4%, +4°) | Kid walks into orange fog | into the fog. |
| 68 | 85.70–87.10 | 1.40 | cut | MS | eye | N | linear push (+8%, 143 px, -4°) | Kid glancing back in orange fog | I held his sleeve the whole way. |
| 69 | 87.10–88.12 | 1.02 | cut | MCU | eye | N | linear push (+11%, 118 px) | Dad worried in orange fog | Ten steps, twenty, |
| 70 | 88.12–89.83 | 1.72 | cut | MS | eye | N | linear push (+18%) | Empty gate and arm in orange fog | and for the first time in ninety years, |
| 71 | 89.83–91.18 | 1.35 | cut | MS | eye | N | linear push (+13%, +4°) | Two villagers waiting, shocked (girl in pink earmuffs) | nobody came walking back out. |
| 72 | 91.18–92.07 | 0.88 | flash | MCU | eye | N | linear push (+6%, +4°) | Kid in purple haze | The fog cleared. |
| 73 | 92.07–93.52 | 1.45 | cut | WS | high | W | slow pull (-4%, +7°) | Kid and Dad small on a misty road | We were on a road we'd never seen. |
| 74 | 93.52–94.82 | 1.30 | cut | WS | low | W | tilt up + push (+7%, 93 px) | Huge blue dusk sky with stars; kid and Dad at frame bottom | Trees on both sides, |
| 75 | 94.82–95.92 | 1.10 | cut | MCU | eye | N | linear push (+9%, 74 px, +4°) | Kid sad, trees behind | silent, no birds. |
| 76 | 95.92–97.08 | 1.17 | glitch | MS OTS | eye | N | linear push (+14%) | Kid's back; road up to the clown gate | The sun was almost gone. |
| 77 | 97.08–98.33 | 1.25 | cut | WS | eye | N | linear push (+25%, 65 px, +4°) | Road to the 8 FEET gate; row of clowns; dusk glow | And a hundred feet up the road, |
| 78 | 98.33–99.10 | 0.77 | glitch | MS | low | N | linear push (+25%) | Another clown, full figure | there was another sign. |
| 79 | 99.10–99.87 | 0.77 | glitch | MS | low | N | linear push (+11%) | Clown, closer | Another clown. |
| 80 | 99.87–101.12 | 1.25 | cut | ECU | eye | N | linear push (+22%) | Clown face | Same peeling grin, |
| 81 | 101.12–102.42 | 1.30 | cut | MS | low | W | pan along the arm (1414 px) + roll +19° (+7%, 1420 px, +19°) | Clown → arm → glove; dusk sky | same arm stretched out. |
| 82 | 102.42–104.13 | 1.72 | glitch | CU | eye | N | linear push (+10%) | Sign + 8 FEET plate | You must be this tall to leave. |
| 83 | 104.13–104.65 | 0.52 | cut | ECU | eye | T | punch-in + push (+9%) | 8 FEET | Eight feet |
| 84 | 104.65–105.90 | 1.25 | glitch | MS | low | N | linear push (+26%, +2°) | Next clown with 9 FEET | and past that one, another, |
| 85 | 105.90–106.53 | 0.63 | glitch | ECU | eye | T | linear push (+8%) | 9 FEET | nine feet, |
| 86 | 106.53–107.47 | 0.93 | cut | MS | low | N | linear push (+17%) | Clown with 10 sign | and another, ten, |
| 87 | 107.47–107.92 | 0.45 | glitch | CU | eye | N | linear push (+6%) | Sign 12 FEET | twelve, |
| 88 | 107.92–108.42 | 0.50 | flash | MS | low | N | linear push (+7%) | Clown with 20 FEET | twenty, |
| 89 | 108.42–109.48 | 1.07 | glitch | MS | low | N | linear push (+15%) | Clown | all the way down the road, |
| 90 | 109.48–110.63 | 1.15 | cut | WS | eye | N | linear push (+12%) | Row of clowns receding down the road, dusk glow | as far as I could see, |
| 91 | 110.63–112.57 | 1.93 | glitch | ECU | low | N | linear push (+14%, 74 px) | Clown face and hat | every single one staring at the ground. |
| 92 | 112.57–113.47 | 0.90 | cut | MS | eye | N | linear push (+13%, +4°) | Night: kid and Dad, kid shocked | The sun went down, |
| 93 | 113.47–114.42 | 0.95 | cut | MS | ground level | W | slight push (+5%) | Legs on the dark road; no shadows | our shadows disappeared, |
| 94 | 114.42–115.85 | 1.43 | glitch | WS | eye | N | linear push (+10%) | Night: town gate, first clown, barn, church | and behind us, in the dark, |
| 95 | 115.85–116.48 | 0.63 | glitch | CU | eye | N | linear push (+14%, 70 px) | Back of the first clown's head (silent beat) |  |
| 96 | 116.48–117.23 | 0.75 | cut | MS OTS→MCU | eye | N | push + slight pan (+10%, 79 px) | Kid turns around (180° in 14 frames) → scream face | I turned around. |
| 97 | 117.23–119.32 | 2.08 | glitch | CU | eye | N | push +37% (accelerating) (+37%, 63 px) | Clown head rotates back → front over ~2 s (thin red outline) | The first clown's head was turning, slowly, away |
| 98 | 119.32–120.17 | 0.85 | glitch | ECU | eye | N | linear push (+24%) | Clown face, lavender-lit | from the road. |
| 99 | 120.17–120.72 | 0.55 | flash | ECU | eye | N | punch-in + push (+13%) | Eye and nose | Toward us, |
| 100 | 120.72–122.65 | 1.93 | cut | MS | eye | N | linear push (+15%, 65 px, -5°) | Kid and Dad shocked, clowns behind | and for the first time in ninety years, he |
| 101 | 122.65–123.92 | 1.27 | glitch | CU | eye | N | linear push (+17%, +5°) | Clown face | wasn't looking at the ground. My |
| 102 | 123.92–125.17 | 1.25 | cut | MS | eye | N | linear push (+14%, +4°) | Dad's hand moves onto the kid's shoulder (16 frames) | dad put his hand on my shoulder. |
| 103 | 125.17–125.85 | 0.68 | cut | MCU | eye | N | linear push (+10%, -5°) | Dad determined | Keep walking, |
| 104 | 125.85–127.62 | 1.77 | glitch | MS | eye | N | push, roll −10° (+23%, 85 px, -10°) | Kid walks toward camera, Dad beside; barn and clowns behind | we're gonna need a lot more sunsets. |

### Shot statistics

| Measure | Value |
|---|---|
| Shots / cuts | **104 / 103** in 127.62 s |
| Shot length | **median 1.17 s, mean 1.23 s**, min 0.45 (#87 "twelve"), max 3.03 (#28 the wall pan); p10 0.63, p90 1.78 |
| Cuts per minute | **48.4** overall. Part 1 (0-72.4 s): 47.2/min, median 1.17 s. Sunset (72.4-85): 42.9/min. Act 3 (85-127.6): **53.0/min**, median 1.12 s |
| Camera motion | **104/104 shots (100%)**: 90 push-ins, 10 pull-backs or recedes, 8 big translations (#1, 4, 26, 27, 28, 54, 65, 81), and 12 shots with a roll of 5° or more (#1, 2, 4, 12, 51, 54, 56, 59, 65, 73, 81, 104) |
| Push size | median **+14.7%** (p10 +8.7%, p90 +27.8%). The rate is about +14%/s. Weak correlation with length (r = 0.42), so longer shots push a little more |
| Push profile | Linear: the 25/50/75% time marks carry 25/50/75% of the zoom (±0.08) in 76 of the 90 push-ins. Eased exceptions: #1 (exponential ease-out), #2, #33, #66, #97 (ease-in or accelerating), #4 and #24 (ease-out) |
| Parallax | Mostly pure scale. On #6 the top, middle and bottom scale is 1.13/1.13/1.12, and on #35 it is 1.11/1.14/1.14. A little depth parallax shows in #8 (1.05 vs 1.17), so this is a slow dolly or FOV change in the engine, not a 2D zoom |
| Handheld shake | None. All moves are smooth tweens |
| Transitions | 83 hard cuts, **16 glitch-ins, 3 flash-ins, 1 fog white-out** (#13→#14). All the glitch and flash transitions come after 85.03 s |
| Shot sizes | ECU 20, CU 14 (1 of them an insert), MCU 16, MS 41, WS/MWS 13 (counting the start size; 6 shots change size during a push or pull) |
| Angles | eye level 65, low 25, top-down/high 11, ground level 3; 4 of them over-the-shoulder |
| Lens feel | normal 77, wide 18 (low angles on the clown, top-downs, ground-level road), tele/insert 9 (wall notches, plates, eye) |

---

## 2. Characters

### 2.1 Build (all humans)

- **R6 classic avatars.**
  - The body is 6 rigid blocks: torso 2×2×1, arms and legs 1×2×1 each, and a classic cylinder "head" (a rounded cylinder, 1.2 studs).
  - There are **no elbows and no knees.** Limbs pivot only at the shoulders and hips (see the walk strips `m/walk_kid.jpg` and `m/walk_pell.jpg`).
- **Measured proportions** on #35 (`m/measure35.jpg`, Dad and kid front-on, 1080 frame):
  - head 130 px, torso 240 px, legs 240 px, torso width 240 px
  - head : torso : legs = **0.54 : 1 : 1**
  - total height **4.7 head heights**
  - arms are half the torso width
- **Scale:**
  - Every adult and the kid are the **same full R6 size (about 5.2 studs)**. That is why "I'm almost as tall as him" reads: Dad and kid are equal height in #35.
  - **Mrs. Pell is scaled to about 0.5-0.55** (hip-high to the kid in #22, where she stands slightly further back). The "one inch shorter" red-haired man (#16, #19) shows no visible rescale. The loss is implied by a low-angle framing under the arm.
- **Clothing:**
  - Classic **2D shirt and pants textures** wrapped on the blocks, with **baked shading and wrinkles**. Examples:
    - the white shirt with black suspenders and pinstripe trousers
    - Dad's brown leather vest with gold buttons, white cravat, red-brown belt and creased off-white trousers
    - the navy pea-coat with gold buttons
    - the fair-isle sweater
  - Several outfits use a **coarse knit or burlap texture** that reads as 3D fabric: the red-haired man's tan coat, Mrs. Pell's pink cardigan, the flat cap.
  - No 3D layered clothing.
- **Accessories (UGC meshes), stylised, chunky, smooth-shaded:**
  - **Kid:** a lime **three-eyed alien hood** (Toy-Story-alien style): 3 white eyeballs with black pupils, 2 pointed ears, an antenna ball and side flaps. Hood colour #b5de09 in daylight.
  - **Red-haired man:** a voluminous curly orange mesh hair and a red scarf.
  - **Flat-cap man:** a grey knit flat cap.
  - **Mrs. Pell:** a grey bun hairdo with a curl, red rectangular glasses (a mesh), a pink knit cardigan and white trousers.
  - **Dad:** bald on top with **brown side-hair tufts as a mesh** (#38, the 3/4 view).
  - **Grandpa:** white side hair, a grey mustache, a navy blazer and a white shirt.
  - **Townsfolk:**
    - Afro-haired man in a brown fair-isle sweater
    - blond man in a navy henley
    - girl with long ginger hair, a pearl headband and pink earmuffs (#71)
    - boy with a ginger mop and an orange scarf
- **Body colours (measured, daylight):**
  - kid skin **#f49134** on the face and #f1722b on the arms (saturated orange "Roblox" skin)
  - kid shirt **#2d8a05**, kid pants **#030002** (pure black)
  - the adults have peach to yellow skin; Dad's head reads #fce26d under the warm barn light
- **Faces:**
  - Classic **2D decal faces** wrapped on the cylinder head: black outline cartoon eyes and brows, simple mouths. The ones seen:
    - small "o" (shock)
    - big open shout with teeth
    - frown
    - worried with raised inner brows
    - smile with teeth
    - smug half-grin
    - sad with tear lines (Dad, #33/#34)
    - angry slanted brows (Dad, #39)
    - wide scream with white teeth (kid, #96)
  - Dad's **mustache is part of the face decal** (front view #35) and wraps the cylinder.
  - **Expressions change only on cuts** (single-frame swap between shots). There is no blinking, no lip-sync and no in-shot animation of the face. For example, #55 has the "o" face and #56 the shout.
- **Consistency:** each character keeps one outfit, one accessory set and one scale for the whole video. Only the face decal changes per beat. The kid's hood makes him readable even from behind (#76, #96) or at 30 px tall (#73).

### 2.2 The creature: the wooden clown statue

`m/v_clown1.jpg`, `full/t_2.6.jpg`, `m/outline.jpg`

- **It is built from primitive parts**, like a carnival cut-out sign.
- **Head:** a large flat **cylinder disc**, cream-painted wood planks (#ded3a0 lit). On it:
  - **Eyes:** two black **torus/ring "glasses"** with black disc pupils pushed to the **bottom** of each ring, so it looks down at the road.
  - **Brows:** pink plank brows plus angled black plank brows.
  - **Nose:** a **red glossy sphere** (#8c0406 in shadow, about #c01010 lit).
  - **Cheeks:** salmon discs (#b96150).
  - **Mouth:** a thick red curved mouth (bent tube segments) with **two rows of triangular wedge teeth in raw wood grain** (the "splinters").
  - **Damage:** small rectangular **wood-grain patches** where the paint "peels".
- **Hair:** 3-5 **orange-red glossy spheres** on each side (#5c1b04 in shade).
- **Hat:** a blue stacked-cylinder top hat (#45525b in the grey fog) with a red ball on top.
- **Body:**
  - a white **ruff** of capsules and spheres (#ad9f72 in fog)
  - a yellow plank torso (#7d601f in shade) with **polka-dot discs and spheres**: teal #366658, red #791a16, maroon #550f0a
  - red-and-white **striped legs**
  - a white **ball glove**
- **The arm is the barrier:** a horizontal beam in yellow with red bands, ending in a white cartoon glove with the thumb up. The sign hangs under it on a wooden frame.
- **Back of the head (#95/#97):** a plain wood plank board with the hair balls. It reads as a flat cut-out.
- **Scale:** about 2.5-3 avatar heights tall. The arm sits at about 1.4-1.6 avatar heights ("seven feet").
- **Creepy vs cute:** cute circus palette and toy shapes, made creepy by:
  - shooting from very low angles (#2, #42, #46, #78)
  - extreme close-ups of the teeth and pupils
  - angry brows
  - fog
  - at night, a cool lavender front light from below, plus a thin red **Highlight outline** (about 2 px) only while the head turns (#97)
- **Reuse:** the clown model is duplicated about 6-8 times down the road at dusk (#77, #90), each with its own height plate (8/9/10/12/20 FEET).

---

## 3. Animation

| What | How it moves (measured) | Evidence |
|---|---|---|
| Idle | **Perfectly still.** No breathing and no sway: 48 shots have under 1% moving pixels after camera compensation | `resid.json` |
| Walk (kid, Mrs. Pell, Dad, the red-haired man) | Roblox-default R6 walk: arms and legs swing as rigid blocks about ±40° in opposite phase, with no torso bob or twist. Cycle **≈ 0.73 s** (kid, f3294→f3338). Mrs. Pell's cycle is about 1 s (small scale, same animation). The camera follows by trucking or dollying back | `m/walk_kid.jpg`, `m/walk_pell.jpg` |
| Walking out of fog | The figure walks toward camera while the fog density in front of it falls (silhouette → colour over about 1.5 s) | #14, #33 |
| Jump | Default R6 jump pose: arms straight up and legs together, a parabolic hop. It hooks the opening shot | #1, `m/s01.jpg` |
| Gesture "hands to head" | Both arms snap from down to the sides of the head in **8 frames** (0.13 s) with a slight ease-out, then hold with a tiny rock | #10, `m/gest_a.jpg` |
| Arms drop | The raised arms fall in about 0.3 s, then the man looks up | #19 |
| Kneel and brush | Torso pitched about 60° forward with the head down. One arm rocks back and forth (brushing), with **brown dust puffs** (particles) at the hand | #51, `m/gest_b.jpg` |
| Drag | The kid walks toward camera with an arm back. Dad follows just off-frame | #59 |
| Turn around | The whole body rotates 180° about the vertical axis in **14 frames** (0.23 s) with an ease-in-out. The face is already the scream decal when it comes into view | #96, `m/turn96.jpg` |
| Hand on shoulder | Dad's arm lifts from down to horizontal across onto the kid's shoulder in **16 frames** (0.27 s), then holds | #102 |
| Clown head turn | A **slow rotation of 180° in about 2.1 s** about the vertical axis (back → side at 118.3 → front at 119.3), nearly linear. It continues into #98 | #97, `m/gest_b.jpg` |
| Barrier arm | "Goes up one inch" is shown by a **dust-puff burst at the shoulder** (#18), not by a visible lift | #18, `m/s18.jpg` |
| Facial | Decal swaps only between shots | `m/face_swap.jpg` |
| Physicality | None. No squash, no overlap, no secondary motion; hair and hood are rigid. Poses snap | — |
| Particles | Warm glowing dust puff (#18); brown dust at the hand (#51); later, the editor's dust-speck overlay (section 6) | — |

How much moves per shot (`resid.json`):
- **48 shots are near-still**: only the camera moves.
- **35 have light motion**: small head and arm moves, or parallax.
- **21 are active**. The top ones are #12, #66, #41, #23, #1, #18, #11, #13, #59, #32, #54 and #50.
- The film runs on camera moves plus cutting. The characters are mostly posed props.

---

## 4. Environments

`m/v_env1..3.jpg`, `m/v_fog_orange.jpg`, `m/bg_sharp.jpg`

1. **The town gate (the hero location, 34 shots).**
   - A big **timber frame**: two square posts and a top beam with diagonal braces. Inside it:
     - a 5-bar **farm gate** with a diagonal brace
     - post-and-wire fences running sideways
     - a **dirt road** (terrain Ground/Mud, #76552a lit) with grassy verges (#948043) and leafy weeds
     - the clown standing beside it, its arm across the road
   - Behind it: **pure fog**. Fog fills the sky and swallows the road after about 20-40 studs.
   - The **road "ruler"**: raised cream planks across the road (about 0.1 stud thick) with stencil-bold "1 FT…6 FT, 7 FEET" text, partly worn and broken. The lines are spaced like a ruler starting at the gate.
2. **The village street.**
   - Clapboard houses (blue-grey and beige siding textures), white **porch columns**, brown shingle roofs and red **brick chimneys**.
   - White **picket fences**, mailboxes, flower boxes, barrels, wicker baskets, lanterns, power poles with crossarms and **sagging wires**, and a **church with a stepped spire**.
   - Trees: faceted **low-poly green blobs** next to detailed photoreal foliage meshes.
   - The **red barn**: red plank walls, white trim, white X-braced doors, a rust-orange shingle roof. Around it: hay bales (yellow with red bands), crates and a bench.
3. **Mrs. Pell's porch.** A stone/plaster wall, a dark-red plank door with a brass knob, a "THE PELLS" wooden plaque, **two rusty lanterns with glowing yellow glass**, baskets and a flower box. The tally-mark wall (#21) is a stone/plaster wall with dark wooden sticks fixed to it, probably the same house.
4. **Barn interior.**
   - A **wood-plank height wall** (#c87e3d lit) with:
     - dark wooden notches
     - year labels (1934…2023)
     - height labels (6'0", 5'11"… red 5'2") and names (HANK, ROSE, JUNE, SAM, TOMMY) in a bold geometric sans
     - a vertical ruler strip
   - **Saturated red plank walls** (#aa1814), a plank floor, hay bales, a wall lantern, a beam, and a **calendar** (cream paper, red header "NOVEMBER", red hand-drawn circle around 5, "DAD'S BIRTHDAY").
5. **Evening house exterior** (#37): a grey clapboard house, purple dusk sky, a big detailed tree, a power pole.
6. **The new road beyond the fog** (dusk to night):
   - A worn **stone/asphalt road** (lavender-grey at night, #494261), **dense detailed trees on both sides** whose leaves glow silver when backlit.
   - A row of **6-8 clown gates** receding, each with its sign and plate.
   - At night: the town gate, barn and church seen from behind.
- **Construction level:**
  - Roblox parts with **textured materials, no studs**: Wood planks, Brick, Slate, Fabric, Concrete.
  - **Terrain** for ground and grass.
  - Marketplace meshes for trees, lanterns, baskets, barrels and plants.
  - Set dressing is dense: every frame has 5-15 props. Only the fog shots are empty on purpose.
- **Skies:**
  - **Day at the gate:** no sky texture, just fog colour (#6a7b68 to #808a71).
  - **Village:** a **dark stormy cloud skybox** (#71746d, #12/#32).
  - **Sunset:** warm cumulus clouds on an amber sky (#66) and a flat orange haze (#bb541a, #60).
  - **Dusk:** a deep blue gradient (#283d76 top → #4d62a9 low) with stars (#74), and a yellow-grey horizon glow behind the trees (#77/#90).
  - **Night:** navy-black (#0a0e27 / #050e1f) with sparse star or dust specks.
- **There is no water.**
- **Interiors vs exteriors:** about 80% exterior. The barn interior covers 11 + 3 shots.

---

## 5. Lighting and colour

### 5.1 Grade by scene

Measured on one mid-frame per shot with the caption band removed. "hi" is the mean of the top 8% of pixels and "lo" the mean of the bottom 8%. `colstats.txt` has per-shot 5-colour k-means palettes.

| Scene (shots) | Mean | hi | lo | L p1/p50/p99 | std | Sat | R−B | Notes |
|---|---|---|---|---|---|---|---|---|
| A. Gate in fog, day (24 shots) | #7d6f51 | #bab083 | #401a0f | 19/123/195 | 39 | 0.39 | +44 | Grey-green fog #6a7b68 to #808a71, warm olive-sepia midtones, highlights never white (cream #ded3a0 peak), 0% clip |
| B. Village, day (16) | #755e34 | #ddc86e | #261408 | 13/90/223 | 48 | 0.62 | +67 | Stormy sky, warmer and more saturated; the kid's green and orange pop |
| C. Barn interior, day (11) | #a76a39 | #d4a566 | #571f12 | 27/115/164 | 30 | 0.66 | +103 | Orange wood and red walls, flat front light, low contrast; the calendar shot is 56% clipped |
| D. Night barn and evening house (4) | #784b3b | #e1b293 | #2a0704 | 8/61/202 | 50 | 0.63 | +51 | Dark red, 14% of pixels near black, warm key on faces |
| E. Sunset (9) | #66441c | #d4a24f | #250d03 | 14/56/210 | 44 | **0.75** | +63 | Orange sky #bb541a, backlit, long shadows, dark ground |
| F. Orange fog (5) | #905d32 | #d39d4a | #3d2217 | 27/100/188 | 39 | 0.68 | +93 | Lifted blacks, amber haze, glow; vignette begins |
| G. Dusk, new road (20) | #524249 | #a89385 | #26131d | 19/60/165 | 35 | **0.32** | +13 | **Purple-mauve**, desaturated, lifted blacks (p1 ≈ 19), strong vignette |
| H. Night (13) | #3e3542 | #8d8594 | #0d0816 | 5/50/169 | 35 | 0.40 | −3 | Blue-violet; sky #0a0e27; road lavender #494261; kid shirt #47415c; 8% crushed |

### 5.2 Light and shadow

- **Day fog:**
  - Overcast and ambient-heavy. A weak key comes from the upper front-left: the left sides of the clown's balls are brighter.
  - **Soft blob shadows** under the characters (#9) and **no hard cast shadows**.
  - Fog colour adds an olive-green ambient tint.
- **Noon top-down (#57):** a **round dark "puddle" shadow** under the kid, soft-edged, about 1.3× the body width. It is a story point.
- **Sunset (#58-#65):**
  - A low orange sun **behind the gate** (backlight), dark ground.
  - **Long, dark, semi-transparent blocky shadows** (real shadow-mapped R6 silhouettes) stretching across the ruler lines toward the gate. The story needs these exact shapes.
- **Barn interior:** a warm, frontal and slightly overexposed key with almost no shadow. The night barn (#38-#40) is dark, with a warm key on the face and the red wall falling off to near black.
- **Practicals:**
  - Pell's lanterns: emissive yellow glass with a small glow.
  - The barn lantern.
  - The **sun disc with a soft halo and faint diagonal sun rays** in the fog sky (#46, Roblox SunRays).
- **Night:** a cool **lavender-white front fill** on faces and the clown (the clown's face reads #c4b2d3 to #d8c3e1). There is no visible moon. Silver rim highlights on the foliage.
- **AO:** only mild, through soft shadowing in creases. No strong contact darkening.
- **Atmosphere:**
  - Distance fog in every exterior: grey-green by day, amber at sunset and in the orange fog, mauve haze at dusk (#73 haze is purple).
  - No volumetric god rays except the faint sun rays in #46.

### 5.3 How night is shown

- **Not black.** The scene is lifted into **mauve and blue-violet**: R≈B, G lower.
  - Dusk midtones #4d3e44 to #5e4f5b.
  - Night midtones #37333e to #3e3542.
  - The sky alone goes to navy black.
- Faces and the clown keep readable values under the cool front fill.
- From 85 s the vignette crushes the frame edges to about 30% of the centre, so the eye stays in the middle.

### 5.4 The "liminal / dreamcore" recipe, exactly

1. **Fog as the world boundary.** It is thick and depth-based, coloured, never white:
   - grey-green #76846d day
   - amber #8a4624 to #bb541a sunset
   - mauve #3a1930 haze at dusk
2. **Muted, low-key daylight.** Highlights are capped at about L 195-210 and warm-cream (#ded3a0, not white). Blacks are slightly lifted (p1 about 15-25). Saturation is about 0.4.
3. **Olive-sepia white balance by day:** R−B +40 to +70, with the green channel above blue.
4. **A colour script that tracks the clock:** grey-green, then warm interior, then orange sunset, then purple dusk, then blue night.
5. **Act-3 post stack** from 85 s:
   - vignette (corners about 0.3 of centre)
   - lifted, desaturated purple grade (sat 0.32)
   - dust specks
   - glitch and flash transitions
6. **Empty compositions:** the gate with nothing behind it, a lone figure on a road, a huge sky with tiny figures (#73, #74).
7. **No DOF, no grain, no chromatic aberration.** The "dream" comes from fog plus the grade plus the vignette, not from lens effects.

---

## 6. Post effects, particles and transitions

| Effect | Present? | Measured detail | Three.js |
|---|---|---|---|
| Bloom | Mild | Small halos on lanterns and the sun. The cream calendar and white sleeves burn (#36: 56% clipped). Backlit night foliage has silvery edges | `UnrealBloomPass` with strength 0.25-0.35, radius 0.4, threshold 0.85, raised to 0.5 for the calendar and orange fog |
| Depth of field | **No** | Backgrounds are sharp. Only fog softens distance (`m/bg_sharp.jpg`) | None |
| Vignette | **From 85.03 s only** | Corner/centre luminance: 0.95 (0-36 s), 0.88 (36-72), 0.82 (72-85, from content), **0.49** (85-91 orange fog), **0.33-0.36** (dusk), **0.30** (night) | Radial darken shader: smoothstep from r = 0.35 to 0.95, strength 0.55 in the fog, 0.7 at dusk and night |
| Chromatic aberration | No (apart from the glitch bars) | — | None |
| Film grain / noise | Only as dust specks after 85 s | Repeated frames differ only at the specks | — |
| Dust specks | **From about 85 s** | 4-6 px white (and some dark) dots. Each lives about 3 frames (50 ms) at random positions; about 20-40 on screen at once (2-4 per 500×400 crop); random, not drifting (`m/night_grain.jpg`, `m/specks.jpg`) | A 2D overlay of random points regenerated every 3 frames, alpha 0.6-0.9 |
| Motion blur | No | Even the 8500 px/s whip in #28 is sharp | None (or a very light one on the whip) |
| Lens distortion | No | — | None |
| Light leaks / overlays | No leaks. The orange fog shots (#67-#69) look double-exposed, but that is thick amber haze plus glow over the village | — | Amber `FogExp2` plus bloom |
| Particles (in-engine) | Few | #18: a warm glowing dust puff at the clown's shoulder, which expands and fades in about 0.6 s. #51: brown dust at the brushing hand | `Points` or sprite puffs with additive blending |
| Highlight outline | One shot | A thin (about 2 px) red outline around the clown's head while it turns (#97) | Inverted-hull or edge-detect outline pass on that one object |
| **Glitch transition** | **16 cuts** (85.03, 95.92, 98.33, 99.10, 102.42, 104.65, 105.90, 107.47, 108.42, 110.63, 114.42, 115.85, 117.23, 119.32, 122.65, 125.85) | On the **incoming** shot's first 5-9 frames (0.08-0.15 s): 2-5 full-width bands 50-250 px tall in **red ≈ #d84040 and cyan ≈ #3ed0e8 at about 50% opacity**, plus 3-8 thin 5-20 px horizontal image slices shifted sideways. The layout re-randomises every 3-5 frames. At 85.03 (orange world) the bars are orange and pink (`m/tr_5100.jpg`, `m/tr_5755.jpg`, `m/tr_6865.jpg`) | 2D shader pass: random bands (mix to red or cyan at 0.5) plus a per-band UV x-offset of ±10-40 px, for 6-8 frames after the cut |
| **Flash-in** | **3 cuts** (91.18, 107.92, 120.17) | White overlay alpha about **0.55, 0.55, 0.40, 0.12, 0** on frames 0-4 of the incoming shot. Mean L jumps from 63-76 to 167-173 (`m/tr_6475.jpg`) | Full-screen white quad with that alpha curve |
| **Fog white-out** | 1 (#13→#14) | Outgoing shot: frame mean L 123→181 and black level 53→136 over the last 1.3 s, accelerating. Incoming shot starts at L 189 and clears to 125 in about 0.3 s (18.0-18.3) | Animate fog density (`FogExp2.density` ×4 to ×6) plus a final 0.15-s cream fade |

Other transitions: none (no dissolves, no whip-transitions between shots, no zoom transitions). Whips happen *inside* shots as camera moves (#4, #28, #81).

---

## 7. Text and captions

- **Style:**
  - White (#f9f9f9 measured fill) **bold geometric sans**: a double-storey "a", single-storey "g", "t" with an angled top cut, straight-tail "y".
  - Closest free matches: **Poppins Bold (700)**, or Montserrat Bold.
  - **All lowercase**, numbers as digits ("90", "41", "7", "10", "20", "100", "12", "6", "5").
  - **About 5 px solid black stroke** plus a **soft black shadow/glow** about 6-8 px wide, heavier below (offset about 2-3 px down).
- **Size:** x-height glyph about 44 px (50 px with stroke). Ascender top to baseline is 68 px with stroke. That gives **font-size ≈ 82-86 px** at 1080 wide. Word widths: "one" 158 px, "was" 140 px, "on" 102 px; the longest word is about 710 px.
- **Position:** centred at x = 540. **Baseline y = 1382** (72.1% of 1916). x-height top at 1332, ascender top at 1314. It sits in the same place in every shot, over the subject's chest.
- **Rhythm:**
  - **One word at a time**: 520 caption changes for 532 spoken words.
  - It changes on the word: the median is **+0.013 s** after the ASR onset (p25 −0.04, p75 +0.07). 393 of 520 are within ±0.1 s.
  - A word stays up until the next word. The screen is empty only 1.1% of the time (23.37-24.07, the dust-puff pause, and 116.12-116.73).
- **Animation:** a **1-frame pop**. The first frame is at about **92% scale** (median width ratio 0.923; p10 0.80), and from the second frame on it is 100%. No bounce, no fade, no colour highlighting (`m/cappop.jpg`).
- **No speaker colours.** Quotes ("One more try", the sign text "you must be this tall to leave") use the same white (`m/cap_quotes.jpg`).
- **Diegetic text** (part of the picture, not captions):
  - The sign: red **#c81e1e-ish heavy geometric caps on a cream plank**, "YOU MUST BE / THIS TALL TO LEAVE".
  - Plates: "8 FEET", "9 FEET", "12 FEET", "20 FEET" in red on white.
  - Road: cream stencil "1 FT".
  - Wall: dark years and heights, names, red "5'2"".
  - Calendar: red header, bold black numerals.
  - Door plaque: "THE PELLS".
  - Each one is shown in its own insert at the moment it is spoken.

---

## 8. Editing and sound-picture sync

- **Cuts land on words.** 93 of 103 cuts are within ±0.1 s of a word onset, and the median cut leads the word by 0.023 s. 56 of 60 sentence starts are on a cut. The picture for a noun arrives **0-0.1 s before** the noun:
  - "clown" → #2
  - "grin" → #3
  - "arm" → #4
  - "says" → the sign (#5)
  - "Mrs. Pell" → #20
  - "forty-one" → tallies (#21)
  - "1934" → carved year (#26)
  - "6 feet / 5'11 / 5'10" → three notch inserts (#29-#31), one per number
  - "calendar"-day → #36
  - "eyes" → #45/#47
  - "Eight feet / nine / ten / twelve / twenty" → one insert per number (#83-#88), the fastest stretch: 0.45-0.63 s shots
- **Lists are cut item by item**, often with glitch-ins in act 3 to make the escalation feel like a malfunction.
- **Inside-shot moves illustrate the sentence:**
  - the pan along the arm on "One arm stretched out flat"
  - the tilt up the notches on "since 1934 / Most notches go up"
  - the 3-s wall pan that goes up and then down on "go up until he turned twenty, then they start going down"
  - the road dolly 0→7 FEET on "way out at the end, a line marked seven feet"
- **Punch-in jump cuts** on the same axis: #14→#15, #38→#39, #82→#83, #84→#85, #98→#99.
- **There are no freeze frames, speed ramps or editor zoom punches.** Every zoom is an in-engine camera move.
- **Silent beats:** the only gaps in the voice are filled with a creature or atmosphere shot. #18 (23.33-24.03) is the dust puff with a whoosh. #95 (115.85-116.48) is the back of the clown's head with the music cut out.
- **Sound** (from the UVR split, `m/spec_*.png`):
  - Voice: continuous. RMS median −22 dBFS.
  - **Music, part 1 (0-72 s):** a light, playful-creepy **plucked/mallet ostinato** (pizzicato or marimba-like quick notes, 2-4 kHz centroid) at about **−33 dBFS RMS, about 10 dB under the voice**, with no ducking.
  - **72.2 s, the twist ("…your shadow" ended at 71.9):**
    - a noise burst at 72.0
    - a **sub-boom** at 72.24, +55 dB in the 25-110 Hz band against its own baseline, peaking at −10 dBFS and decaying over about 3 s
    - the music switches to a **dark sustained pad/drone** (1.2-1.4 kHz centroid), −28 to −32 dBFS, to the end
  - **104.4 s:** a second sub-boom on "Eight feet".
  - **Music dropouts** ("silence beats") at 79.0-79.3, 97.4-97.6 (before "there was another sign") and **115.5-115.9** (before "I turned around").
  - **Whoosh/glitch hits** (high-band transients stronger than the vocal leak):
    - 23.15 (dust puff)
    - 44.76 (Dad out of the fog)
    - **107.46 and 107.93** (the "twelve" and "twenty" glitch/flash cuts)
    - **116.61** (the turn-around)
    - 119.41 (the glitch onto the clown's face)
    - Other glitch cuts carry faint ticks that I cannot separate from voice consonants.
  - Music volume and genre are the owner's choice. The SFX placement above is the part to copy.

---

## 9. What makes it look premium, and how to get there in Three.js

### 9.1 Premium drivers, ranked by impact

1. **A camera that never stops.** Every shot is a linear push of about +15%, plus a few big motivated moves: snap pull-back, pans along the arm, wall tilts and whips, the road dolly with roll. This alone hides the stiff R6 acting.
2. **Word-locked cutting at about 48/min, one picture per noun.** A dedicated insert for every number, sign and object that is named.
3. **Fog and colour script.** The coloured, depth-based fog plus the clock-driven grade (grey-green, warm wood, orange, purple, blue) gives depth and mood with very little geometry.
4. **Dense, textured set dressing.** Wood grain, siding, brick, knit fabrics, lanterns, wires, hay, signage. No flat untextured parts.
5. **A well-designed hero prop** (the clown). It is readable at every scale and built from simple primitives, so it is cheap to model but iconic.
6. **Diegetic typography** carries the information: signs, plates, ruler, wall, calendar.
7. **Act-3 treatment** marks the "other side": vignette, purple grade, dust specks, glitch and flash cuts.
8. **Clean captions:** big white bold lowercase word-by-word with a stroke, always present.
9. **Restraint on lens effects.** No DOF, chromatic aberration or grain, so the image stays crisp and "game-like" rather than muddy.

What reads as cheap (accepted by the genre): rigid R6 limbs, decal faces, the judder, low-poly trees next to detailed ones. We can be cleaner on all of these without losing the look.

### 9.2 Hard to reproduce in Three.js, and the best approximation

| Element | Difficulty | Approximation |
|---|---|---|
| Roblox Atmosphere fog (coloured, haze, glare) | Easy | `scene.fog = new THREE.FogExp2(color, d)`: day #7a8670 with d about 0.035-0.05/stud; sunset #b4602a; dusk #4a3a52. Use the fog colour as the background (no skybox in the gate shots). Add a large back-facing sky sphere with a vertical gradient for dusk and night |
| Soft overcast light | Easy | `HemisphereLight` (sky #c9cfb4, ground #5a4630, 0.9) plus a weak `DirectionalLight` from the upper front-left (0.6, warm #fff1d0). Use PCFSoftShadowMap at 2048 with radius 4-6. Use ACESFilmic tone mapping with exposure about 0.85 so whites cap near L 200 |
| Sunset long shadows | Medium | DirectionalLight at 6-10° elevation behind the gate, #ff8a3a, intensity 2. The shadow camera must cover the ruler. Use a hard-ish shadow (radius 1.5) with shadow opacity faked by ambient fill |
| Noon puddle shadow | Easy | Sun overhead plus a soft shadow, or a radial-gradient decal under the character |
| R6 avatars | Easy | 6 `RoundedBoxGeometry` parts (bevel 0.04): torso 2×2×1, limbs 1×2×1, head a `CylinderGeometry` 1.2 diameter with a 0.1 bevel (`LatheGeometry`). Use `CanvasTexture` shirts and pants with painted folds and shading baked in. Pivot limbs at the shoulders and hips |
| Decal faces | Easy | Draw on a canvas and wrap on the front 120° of the cylinder (UV-mapped band). Keep a face library: o, shout, frown, worried, grin, sad-tears, angry, scream. Swap only on cuts |
| Knit and burlap clothing | Medium | Procedural noise canvas (ribbed knit: rows of small ellipses) as a map plus a bumpMap at 0.02 |
| Hood, hair and cap meshes | Medium | Hood: a sphere shell with 3 white sphere eyes, cone ears and a cylinder plus sphere antenna. Curly hair: 15-30 overlapping spheres. Flat cap: a squashed sphere plus a brim |
| The wooden clown | Medium | All primitives: cylinder face disc, torus eyes, circle pupils offset down, wedge teeth (`ExtrudeGeometry` triangles with a wood map), a tube mouth (`TubeGeometry` on an arc), spheres for nose, hair and dots, box planks for the body. Use a wood-plank canvas texture tinted cream or yellow, and patches as small boxes with raw wood |
| Wood, brick, siding and shingle materials | Medium | Procedural canvas textures (plank lines plus noise, brick grid, clapboard bands, shingle rows) with MeshStandardMaterial roughness 0.8-0.9 and `bumpMap`. No studs |
| Detailed trees | Hard | Instanced leaf quads (alpha-tested canvas leaf) around a trunk cylinder, 2-4k leaves per tree, or the faceted low-poly version (icosahedron, flatShading). Backlit at night: rim light plus bloom |
| Terrain and dirt road | Easy-Medium | PlaneGeometry with noise vertex displacement and a blended dirt/grass canvas texture. Weed clumps as crossed alpha quads |
| Bloom | Easy | UnrealBloomPass (strength 0.3, radius 0.4, threshold 0.85). Heavier in the orange fog (0.6) |
| Vignette, purple grade, dust specks | Easy | A final ShaderPass: vignette, lift/gamma/gain (dusk: lift +0.06 with a magenta tint, gain 0.9, saturation 0.75), and a speck layer from a hashed grid re-seeded every 3 frames |
| Glitch and flash transitions | Easy | Editor-side 2D shader on the composited frame (section 6). Keep it outside the 3D render so it is deterministic per frame |
| Highlight outline | Easy | Inverted-hull duplicate (BackSide, scale 1.03, red) on the clown head |
| Captions | Easy | Draw on a 2D canvas over the frame: Poppins 700 at 84 px, `lineJoin` round, stroke 10 px (5 px visible outside), black shadow blur 8 at offset (0, 3). Scale 0.92→1.0 on the first frame |
| Camera grammar | Easy | Per shot, a linear dolly or FOV push of +15% (log-linear, no easing). Accents: a ×3.4 pull with exponential ease-out over 0.5 s; a ×2.4 accelerating push with +12° roll; pans as linear 1000-1500 px/s screen moves; the 3-s wall move as keyframes (tilt up, 0.25-s whip, pan). Always render true 60 fps |
| SwiftShader cost | Watch | Fog, the shadows and 2-3 passes are fine. Dense trees and many shadow casters are the expensive part, so limit shadows to the hero area and use instancing |

### 9.3 Production rules to copy (for "Never Move Grandpa")

1. One shot per noun or number. Cut 0-0.05 s **before** the word onset. Target a median shot of 1.1-1.2 s and 45-53 cuts/min. Never hold a static frame: every shot gets a +10-20% linear push.
2. Open on an extreme close-up mid-action with a ×3 snap pull-back, then show the "creature/object" in a low-angle accelerating push within 2.5 s.
3. Build one iconic object from primitives and give it its own insert vocabulary: face ECU, eye ECU, detail ECU, low-angle MS, a pan along its key feature.
4. Put the plot information into diegetic text (signs, marks, labels) and give each one an insert timed to the word.
5. Colour script by time of day. Keep daylight muted and olive with capped highlights. Do night as mauve or blue-violet, not black.
6. Hold back vignette, glitch and flash transitions and dust specks until the story crosses into the "other world" (here the last third). That makes the switch read as a turn.
7. Faces: one decal per shot, swapped on cuts. Bodies: minimal, snappy pose changes (8-16 frames) and default-style walks.
8. Captions: one lowercase word, white bold sans at about 84 px, 5 px stroke plus soft shadow, baseline at 72% of the height, 1-frame pop.
9. Sound: 2 sub-booms at the twist and the escalation, short silence beats before reveals, and whoosh or glitch hits on act-3 cuts. The music is the owner's choice.
