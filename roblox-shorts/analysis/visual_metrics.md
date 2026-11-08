# Visual metrics: automated measurements across the four reference shorts

Measured on the full 60 fps copies: TF = Tooth Fairies (the owner's favourite), AW = Never Be Caught Awake At Night, PN = Porch Night, CG = Clown Gate.
This file is numbers plus what they mean for our Three.js render. The look itself (characters, sets, lighting) is described in `visual_*.md`.

- **Data (scratch, not in the repo):** `/tmp/claude-0/-home-user-claude-todo-demo/353ac1d9-152b-55bb-bdf1-0625e0fc6a83/scratchpad/rbx/metrics/`
  - `<video>.json` (TF/AW/PN/CG: `tooth_fairies.json` ...) has the final cut list, the shot stats and a **per-shot table** with camera, subject, colour and a 6-colour palette for every shot. It also holds the caption and cut-to-word stats.
  - `effects.json` holds vignette, bloom, grain, DOF and chromatic aberration. `audio.json` holds loudness, music, SFX and pace. `looks.json` holds shot colour clusters.
  - `cuts_summary.json` scores PySceneDetect. `sd_<video>.csv/.json` are the raw PySceneDetect outputs. `events.json` lists the glitch and flash transitions and the cut-list corrections.
  - The scripts are in `py/`:
    - `sd.py`: PySceneDetect.
    - `pass1.py`: per-frame diff, caption mask, DIS optical flow, colour.
    - `pass2.py`: effects on 1-fps full-resolution frames.
    - `pass3*.py`: glitch and flash detection.
    - `pass4.py`: bloom by brightness class, plus the flat-row vignette test.
    - `agg*.py`, `audio.py`, `looks.py`: aggregation.
- **Units:** px and px/s are in the 1080x1920 output frame. "Zoom %" is the image-scale change from a RANSAC similarity fit to the optical flow. Luma Y' is 0-255 (Rec.709 weights on the encoded values). Times are video seconds, and frame n is at n/60.

---

## 0. The numbers to build to

| What | TF (favourite) | AW | PN | CG | Use in our render |
|---|---|---|---|---|---|
| Cuts per minute | **52.0** | 34.8 | 42.1 | 48.4 | Aim for 45-52 per minute. Follow TF. |
| Median / mean shot | **1.10 / 1.14 s** | 1.52 / 1.71 s | 1.35 / 1.41 s | 1.17 / 1.23 s | Median 1.1-1.2 s. Keep 90 % of shots under 2.0 s. |
| p10 / p90 shot | 0.50 / 1.96 s | 0.95 / 2.69 s | 0.84 / 2.05 s | 0.63 / 1.78 s | Never go past 2.3 s (TF max 2.28 s). |
| Shots that push in | **94 %** | 81 % | 75 % | 88 % | Every shot moves. Default is a push-in. |
| Push per shot, median (p10-p90) | **+19.7 %** (+10 to +32) | +20.5 % (+8 to +52) | +10.0 % (+4 to +19) | +16.2 % (+11 to +32) | Default push is +18-20 % per shot, whatever the shot length. |
| Push speed, median | 18.4 %/s | 12.1 %/s | 7.4 %/s | 16.3 %/s | |
| Push easing (2nd-half / 1st-half rate) | 1.04 | 1.05 | 1.02 | 1.03 | **Linear, no ease.** Cut mid-move. |
| Pull-outs | 4 % (median -38 %) | 12 % (-9 %) | 14 % (-9 %) | 10 % (-19 %) | Use a pull-out as an accent only. |
| Whip or fast move (peak > 1000 px/s) | 18 % of shots | 8 % | 8 % | 11 % | About 1 shot in 6 gets a fast crane, whip or orbit. **Every video opens on one.** |
| Camera static (< 10 px/s) | 0 % of time | 0.3 % | 1.6 % | 0 % | **Never a locked-off camera.** |
| Subject still / light / active shots | 49 / 26 / 39 | 36 / 25 / 40 | 56 / 26 / 36 | 61 / 21 / 22 | About half the shots have a near-still character and only the camera moves. |
| Unique frame rate in moving shots | 40 fps in 76 % of shots | 40 fps in 89 % | 60 fps in 97 % | mixed (46 % at 40) | We render true 60 fps. That is smoother, and fine. |
| Mean luma, frame median | 115 | 48 | 103 | 94 | TF is bright pastel night; AW is genuinely dark. |
| Contrast p95-p5 | 153 | 126 | 189 | 123 | |
| Black level p1, median | 7 | 0 | 0 | 19 (lifted) | TF blacks are slightly lifted. CG is milky. |
| White clip (Y' ≥ 250), mean of frames | 0.33 % | 0 % | 0 % | 0.02 % | Highlights roll off. Keep p99 around 210-230. |
| HSV saturation, mean | 0.47 | 0.58 | 0.51 | 0.51 | |
| Shadow / highlight tint | #381713 / #d8bfd5 | #000000 / #927fb5 | #0e0301 / #dbc59c | #2d1a12 / #c19e75 | TF: maroon shadows, lilac-pink highlights. |
| Vignette (post) | **none** | none | none | **none until 88 s, then strong** | TF has none. Use it only for a horror-escalation act. |
| Bloom (thresholded) | not measurable | none | lamps only | none | Leave global bloom off, or ≤ 0.15. |
| Grain | none (σ 0.18) | none | none | none (slight chroma noise) | No film grain. |
| DOF blur | none | none | none | none | Keep everything sharp. No BokehPass. |
| Chromatic aberration | none (0.00 px) | none | none | none (CG glitch bars excepted) | None. |
| Transitions | 100 % hard cuts | hard cuts | hard cuts + 1 shake hit | hard + **16 glitch-bar cuts + 3 white-flash cuts** in 85-126 s | TF style is hard cuts only. |
| Caption swap vs word onset, median | +7 ms | -27 ms | -23 ms | 0 ms | One word at a time, swapped on the onset (±1-2 frames). |
| Cut vs word onset, median (p10-p90) | **-7 ms** (-69 to +62) | -40 ms | -77 ms | -23 ms | Put each cut 0-2 frames before the word that names the picture. |
| Sentences starting on a cut (±150 ms) | **95 %** | 64 % | 72 % | 93 % | Every sentence starts with a new shot. |
| Mix loudness (integrated, LRA, peak) | -17.5 LUFS, 3.0 LU, -1.7 dB | -16.9 LUFS | -13.7 LUFS | -17.2 LUFS | Master to about -16 LUFS integrated, LRA ≤ 3.5, peak ≤ -1 dBFS. |
| Voice above music+SFX | +8.3 LU | +7.6 LU | +5.8 LU | +9.1 LU | Run a music bed the whole time, about 8 LU under the voice. |
| Voice pace (overall / without pauses > 0.35 s) | 261 / 286 wpm | 244 / 270 | 268 / 288 | 251 / 275 | Our VO is 235 / 262 wpm, about 10 % slower. That is fine; do not speed it up for the picture. |

---

## 1. Shots and cuts

**Method**
- PySceneDetect 0.7.2 `ContentDetector` ran with the default threshold of 27. `min_scene_len` was 6 frames (the default of 15 drops real 4-frame shots). Downscaling was automatic, so analysis ran at 270 px wide.
- Every disagreement between PySceneDetect and the frame-checked cut lists from the per-video analyses was inspected on frame strips (frames c-3 to c+6).
- I also searched every frame for single-frame content spikes (content value > 10 and > 4x the local median) that neither list had, and viewed those strips too.
- The final lists are in `<video>.json -> shots.cuts_frames`.

### 1a. Shot statistics (final, frame-checked)

| | TF | AW | PN | CG |
|---|---|---|---|---|
| Duration | 131.53 s | 174.22 s | 166.77 s | 127.62 s |
| Shots / cuts | 115 / 114 | 102 / 101 | 118 / 117 | 104 / 103 |
| Cuts per minute | **52.0** | 34.8 | 42.1 | 48.4 |
| Median shot | **1.10 s** | 1.52 s | 1.35 s | 1.17 s |
| Mean shot | 1.14 s | 1.71 s | 1.41 s | 1.23 s |
| p10 / p90 | 0.50 / 1.96 s | 0.95 / 2.69 s | 0.84 / 2.05 s | 0.63 / 1.78 s |
| Min / max | 0.033 s (2-frame flash) / 2.28 s | 0.067 s / 5.20 s | 0.58 / 2.43 s | 0.45 / 3.03 s |
| Shots < 1 s / 1-2 s / 2-3 s / ≥ 3 s | 44 / 47 / 9 / 0 % | 14 / 55 / 24 / 8 % | 20 / 64 / 15 / 0 % | 36 / 57 / 7 / 1 % |
| Longest shots (start s, length) | 48.03 (2.28), 90.57 (2.28), 97.03 (2.23), 9.07 (2.20), 122.07 (2.15) | 72.55 (5.20), 101.75 (4.10), 105.85 (4.00), 66.20 (3.65), 95.05 (3.60) | 53.78 (2.43), 110.58 (2.35), 105.42 (2.30), 102.02 (2.28), 88.75 (2.20) | 36.98 (3.03), 67.62 (2.65), 43.88 (2.47), 0.00 (2.25), 18.00 (2.23) |

What this means for our render:
- TF and CG cut almost every sentence-half: 44 % of TF shots are under 1 s.
- AW is the slow outlier. Its long shots (4-5 s) carry big +45 % to +82 % pushes (§2).
- For "Never Move Grandpa": median 1.1-1.2 s and p90 ≤ 2.0 s. Allow ≤ 2.5 s only for a reveal that has a strong push.

### 1b. PySceneDetect against the frame-checked list

| | Cuts found by SD | Real cuts | True pos. | False pos. | Missed | Precision | Recall |
|---|---|---|---|---|---|---|---|
| TF | 126 | 114 | 112 | 14 | 2 | 88.9 % | 98.2 % |
| AW | 115 | 101 | 100 | 15 | 1 | 87.0 % | 99.0 % |
| PN | 121 | 117 | 116 | 5 | 1 | 95.9 % | 99.1 % |
| CG | 96 | 103 | 90 | 6 (shifted) | 13 | 93.8 % | 87.4 % |

**False cuts PySceneDetect reports (all checked on frames):**
- **TF (14):**
  - 7 fast camera moves or whips: 1.72, 1.82 and 2.22 s (the opening crane); 19.82 s (an orbit); 40.87, 107.32 and 108.82 s.
  - 3 crowds of creatures flying through the frame: 41.27, 43.32 and 43.47 s.
  - 2 sparkle or star twinkles: 3.87 and 13.42 s.
  - 2 lighting changes with the same framing: 91.82 s (the drawing dims) and 125.62 s (the sunrise light-up).
- **AW (15):**
  - 5 fast moves across the dense teddy-bear shelves: 101.95 to 103.35 s.
  - 9 subject movements: puppets at 119.80, 120.20 and 120.35 s; Lullaby's snapping arms at 145.80, 146.08 and 146.50 s; other movement at 126.35, 130.02 and 158.15 s.
  - 1 caption-only change at 90.15 s.
- **PN (5):**
  - 1 editor shake hit at 21.95 s.
  - 2 lamp posts wiping across the foreground: 97.88 and 98.02 s.
  - 2 fast trucks past lamp posts: 118.95 and 119.10 s.
- **CG (6):** every one is a real cut detected 5-8 frames late. The glitch-bar overlay (§5f) suppresses the first frame: 99.20, 105.97, 107.55, 108.50, 115.98 and 119.40 s.

**Real cuts PySceneDetect misses:**
- **TF:**
  - 31.40 s: a jump cut where the card is swapped on the same set-up (content value 22, below 27).
  - One edge of the 2-frame flash at 14.47 s (merged).
- **AW:** 3.70 s, a 4-frame shot (below `min_scene_len`).
- **PN:** 87.97 s, a cut with the same palette (content value 22).
- **CG:**
  - 7 cuts with the same palette or fog: 18.00, 20.23, 40.02, 40.55, 41.18, 85.70 and 87.10 s. The 40-41 s cuts are on the height-chart wall.
  - The 6 glitch cuts above, which it finds late.

**Corrections to the earlier hand-made lists:**
- **TF: added 78.37 s (frame 4702).** It is a jump cut (punch-in about 1.15x) on "shoebox"; frames 4701 and 4702 differ, 4700/4701 and 4702/4703 do not.
- **AW: added 157.45 s (frame 9447).** It is a jump cut on "Lullaby" where the whole frame shifts in one frame.
- **AW: removed 72.10 s (frame 4326).** The background is identical; only the hand pose snaps. That is pose-to-pose animation, not a camera cut.

The lesson for us:
- A content detector over-fires on whips, swarms and light changes. It misses same-palette jump cuts.
- We do not need detection for our own edit, because cuts come from the timeline.
- To QA our renders against the references, use threshold 27 plus a frame check, or compare our timeline directly.

---

## 2. Camera and subject motion

**Method**
- DIS optical flow (OpenCV, MEDIUM preset) at 270x480, between frames i-3 and i (50 ms), every 3rd frame. The caption band (rows 62-76 %) was excluded, and samples that straddle a cut were dropped.
- The camera is a RANSAC similarity fit (zoom, roll, translation) on textured points.
- Subject motion is the 90th percentile of the residual flow after removing the camera model. It contains parallax too.
- Classes were calibrated against the TF hand labels: residual p90 is 59 / 150 / 628 px/s for the labelled still / light / active shots.
  - **still** < 100 px/s
  - **light** 100-300 px/s
  - **active** > 300 px/s

| | TF | AW | PN | CG |
|---|---|---|---|---|
| Shots with camera motion (median RMS ≥ 10 px/s) | **100 %** | 100 % | 98.3 % | 100 % |
| Camera-static samples (RMS < 10 px/s) | 0.0 % | 0.3 % | 1.6 % | 0.0 % |
| Median camera RMS motion per shot | 164 px/s | 121 px/s | 70 px/s | 150 px/s |
| Push-in / pull-out / no zoom (share of shots) | 94 / 4 / 2 % | 81 / 12 / 7 % | 75 / 14 / 10 % | 88 / 10 / 3 % |
| Total zoom per shot p10 / p25 / p50 / p75 / p90 | +8 / +15 / **+19** / +24 / +31 % | -5 / +7 / +19 / +28 / +46 % | -5 / +3 / +7 / +13 / +18 % | -1 / +11 / +16 / +22 / +31 % |
| Zoom rate p25 / p50 / p75 | 11 / **16** / 27 %/s | 5 / 10 / 16 %/s | 2 / 5 / 10 %/s | 9 / 15 / 22 %/s |
| Strong pushes (> +45 %) | 6 | 11 | 2 | 4 |
| Push easing, 2nd half / 1st half rate | 1.04 | 1.05 | 1.02 | 1.03 |
| Translation (drift) p50 / p75 / p90 | 36 / 71 / 215 px/s | 31 / 93 / 241 px/s | 25 / 57 / 166 px/s | 32 / 86 / 182 px/s |
| Shots with a whip or fast move (peak > 1000 px/s) | 18.4 % | 7.9 % | 7.6 % | 10.6 % |
| Roll, median abs | 0.74 °/s | 0.76 °/s | 0.30 °/s | 0.54 °/s |
| Opening shot | pull-back -85 %, peak 5570 px/s | whip, peak 2720 px/s | editor spin-in, peak 5660 px/s | pull-back -68 %, peak 3100 px/s |
| Subject still / light / active (shots) | 49 / 26 / 39 | 36 / 25 / 40 | 56 / 26 / 36 | 61 / 21 / 22 |
| Same, in seconds | 59 / 28 / 44 s | 61 / 49 / 64 s | 82 / 37 / 48 s | 71 / 25 / 32 s |
| Samples with the subject still | 45 % | 36 % | 49 % | 57 % |

**Cadence.** In moving shots, every third frame repeats. This was measured as the share of duplicate frames among moving frames, per shot.

| | TF | AW | PN | CG |
|---|---|---|---|---|
| Moving shots at 40 fps (duplicate share 0.2-0.45) | 76 % | 89 % | 3 % | 46 % |
| Moving shots at true 60 fps (≤ 0.1) | 5 % | 3 % | 97 % | 6 % |

What this means for our render:
- Camera rig per shot:
  - The default is a centred dolly or FOV push that is **linear in scale**: `scale(t) = 1 + Z·t/T`, with Z drawn from +12 to +30 % (median +19 %).
  - Add a slow drift of 20-70 px/s and a roll of ≤ 1 °/s.
  - Use no easing at either end. Cut mid-move.
- About 1 shot in 6 is a fast move (crane, whip or orbit) at 1000-8000 px/s. Open the video with one: a pull-back from an extreme close-up, or a whip.
- Pull-outs are rare, 5-12 % of shots.
- Characters: keep about half the shots near-still (idle breathing only) and about a third active.
- Render a true 60 fps. Do not reproduce the 40-fps judder.

---

## 3. Colour

**Method**
- Frames were sampled every 6th frame (10 Hz) at 270x480, with the caption band excluded.
- Statistics were taken per frame, then the median per shot and per video was used.
- Palettes are k-means in Lab on 300 random pixels per sampled frame.
- Shadow and highlight tints are the mean RGB of the darkest and brightest 10 % of pixels.

### 3a. Per video

| | TF | AW | PN | CG |
|---|---|---|---|---|
| Mean luma (all frames) | 115.4 | 54.1 | 101.7 | 91.5 |
| Shot mean luma p10 / p50 / p90 | 57 / 115 / 157 | 20 / 51 / 106 | 64 / 103 / 133 | 54 / 90 / 126 |
| p0.5 / p1 / p5 (black level) | 2.3 / 7.3 / 34.3 | 0 / 0 / 0 | 0 / 0.1 / 4.8 | 14.4 / 19.1 / 30.4 |
| Frames whose p1 is 0 | 37 % | 82 % | 66 % | 9 % |
| Pixels ≤ 8 | 9.9 % | 28.5 % | 11.7 % | 1.5 % |
| p95 / p99 | 197 / 211 | 130 / 169 | 198 / 214 | 158 / 188 |
| Contrast p95-p5 (shot p10 / p50 / p90) | 153 (114 / 152 / 194) | 126 (75 / 129 / 177) | 189 (150 / 189 / 213) | 123 (85 / 118 / 166) |
| White clip, luma ≥ 250 (mean %, frames > 0.5 %) | 0.33 %, 2.7 % | 0, 0 | 0, 0 | 0.02 %, 0.2 % |
| Any channel ≥ 250 (mean %) | 10.0 % | 0.8 % | 0.17 % | 2.9 % |
| HSV saturation mean (shot p10 / p50 / p90) | 0.47 (0.33 / 0.47 / 0.62) | 0.58 (0.39 / 0.58 / 0.77) | 0.51 (0.34 / 0.50 / 0.69) | 0.51 (0.30 / 0.48 / 0.75) |
| Chroma mean | 0.275 | 0.202 | 0.240 | 0.244 |
| Shadow tint (darkest 10 %) | #381713 maroon | #000000 | #0e0301 | #2d1a12 brown |
| Highlight tint (brightest 10 %) | #d8bfd5 lilac-pink | #927fb5 violet | #dbc59c cream | #c19e75 tan |
| Hue histogram, chroma-weighted (≥ 1 %) | red-pink 33, azure 18, blue 12, rose 9, orange 9, violet 8, magenta 4, yellow 3 | blue 33, red 32, azure 15, rose 6, violet 4, magenta 3, orange 3 | orange 65, red 32, azure 2 | orange 43, red 40, yellow 6, chartreuse 3, rose 3, azure 3 |
| k-means 6 (% of pixels) | #af9ed0 22, #d3ab9c 21, #6956a9 18, #a44a3f 18, #191618 17, #8f8111 5 | #140b17 45, #4f4398 21, #ab92b3 12, #591c10 11, #776a4c 7, #b5441b 4 | #1c120e 25, #c89f5a 20, #755c3c 18, #cdbb9f 18, #723412 15, #747c94 4 | #6b4523 25, #2c211f 22, #81826e 20, #c06b2d 15, #524a64 11, #c0b164 8 |

A note on clipping:
- "Any channel ≥ 250" is high in TF (10 %) while luma clipping is only 0.33 %.
- The pastel pinks and lilacs reach 255 in R or B without being white.
- So for our render: **saturated pastel highlights may hit 255 in one channel, but white must stay at about 210-235.**

### 3b. Colour "looks" (shots clustered by mean colour and highlight tint, k = 4)

| Video | Look | Shots / s | Mean | Highlight | Shadow | Luma | Contrast | Sat | Example start times (s) |
|---|---|---|---|---|---|---|---|---|---|
| TF | warm peach "fairy glow" | 37 / 44.5 | #b88e7c | #f2d1bb | #5d2c2a | 146 | 144 | 0.41 | 42.0, 43.0, 44.2, 45.5 |
| TF | magenta-maroon interior | 28 / 33.5 | #816063 | #d7bdd7 | #0f0a03 | 105 | 173 | 0.59 | 11.3, 16.1, 27.6, 30.0 |
| TF | lavender interior | 29 / 31.5 | #8e70a8 | #d0bae1 | #401e26 | 123 | 136 | 0.46 | 0.0, 4.3, 6.4, 17.1 |
| TF | periwinkle night exterior | 20 / 22.0 | #2f356a | #858dec | #000000 | 56 | 141 | 0.54 | 1.3, 2.5, 3.8, 9.1 |
| AW | violet night (dark) | 51 / 90.6 | #241931 | #7e629d | #000000 | 30 | 105 | 0.60 | 0.0, 4.4, 10.8 |
| AW | moonlit blue | 23 / 39.5 | #484273 | #a09de0 | #000000 | 71 | 153 | 0.52 | 1.8, 3.7, 6.1 |
| AW | rose interior | 18 / 28.2 | #855155 | #c3a2bf | #320602 | 93 | 153 | 0.60 | 23.0, 25.4, 27.6 |
| AW | warm brown | 10 / 15.9 | #6a4f3c | #c0aa9e | #140b05 | 85 | 144 | 0.60 | 30.7, 32.2, 45.5 |
| PN | amber lamplight | 41 / 59.8 | #9d6d3c | #e9c88d | #230702 | 116 | 185 | 0.65 | 14.0, 28.7, 32.6 |
| PN | sepia day | 40 / 56.0 | #7b6246 | #d4c5a8 | #0b0201 | 101 | 192 | 0.49 | 1.5, 8.7, 24.5 |
| PN | dark porch night | 22 / 30.9 | #49392c | #c4b692 | #000000 | 61 | 179 | 0.42 | 0.0, 0.7, 5.4 |
| PN | neutral grey-pink | 15 / 20.0 | #71635d | #d6ced1 | #040102 | 101 | 206 | 0.41 | 3.5, 23.4, 45.1 |
| CG | dim mauve night (late act) | 34 / 37.2 | #4b3b40 | #977e7c | #1f1519 | 64 | 103 | 0.35 | 50.7, 61.1, 92.1, 95.9 |
| CG | olive fog day | 24 / 33.3 | #7f6e52 | #b1ad81 | #442211 | 111 | 122 | 0.39 | 0.0, 2.3, 3.5 |
| CG | mustard dusk | 26 / 32.3 | #685028 | #cea744 | #261207 | 81 | 145 | 0.66 | 13.8, 15.7, 28.2 |
| CG | orange haze | 20 / 24.8 | #a26b2d | #ebb545 | #552910 | 118 | 116 | 0.70 | 16.5, 23.3, 30.9 |

What this means for our render:
- Each video uses about 4 grades, and **each grade is a per-location monochrome tint applied to the highlights** (white objects land on the tint colour, not #ffffff).
- For a TF-like look, grade per set:
  - **Interior:** lavender/pink; highlight tint #d0bae1 to #f2d1bb; shadows maroon #401e26 to #5d2c2a; lift black to p1 ≈ 5-10.
  - **Night exterior:** periwinkle on true black; highlight #858dec.
- In Three.js, use ACES or AgX tone mapping with exposure set so that p99 is about 210-230. Then apply a final colour-matrix pass per set:
  - multiply the highlights toward the tint;
  - add the shadow tint with a lift of about 0.02-0.04;
  - saturation ×1.0-1.1.

---

## 4. Effects

Effects were measured on one full-resolution frame per second (131-174 frames per video), with the caption band excluded.

### 4a. Vignette

| | TF | AW | PN | CG (0-85 s) | CG (88-127 s) |
|---|---|---|---|---|---|
| Corner / centre luma, frame median (all content) | 1.07 | 0.61 | 1.05 | 0.76 overall | |
| Frames with all 4 corners < 0.8x centre | 7 % | 27 % | 2 % | 38 % overall | |
| **Flat-row test**: outer column / middle of the same uniform row (rows 0-2, 25-27) | **1.00** | **1.00** | **0.99** | **≈ 1.00** | **0.47-0.73 (median ≈ 0.63)** |
| Mid-height row, edge / centre (late CG only) | | | | | 0.46-0.58 at the edge, 0.74 at 25 % in, 0.93 at 35 % in |
| Vertical, top or bottom edge / centre (late CG) | | | | | 0.45 / 0.47 |

Reading the results:
- The flat-row test only uses rows of nearly uniform content (sky, fog, walls), so it separates a post vignette from composition.
- **TF, AW and PN have no post vignette.** AW's dark corners (0.61) come from lighting: a lit subject in the middle and black sky and ground around it.
- **CG adds a strong vignette from about 88 s to the end** (the horror act), together with dust specks, glitch cuts and flashes.
- For our render: **vignette strength 0** in the TF style. If we want a CG-style escalation act, use a vignette that:
  - is elliptical, following the frame aspect;
  - starts about 30 % from the centre;
  - reaches x0.75 at 60 % and x0.5 at the edges, i.e. `v = mix(1.0, 0.5, smoothstep(0.30, 1.0, length((uv-0.5)*2.0)))`.

### 4b. Bloom and glow

The halo profile was measured as the luma excess outside bright blobs, normalised to the excess at 1 px. Blobs were grouped by peak brightness at 540x960. Widths are converted to 1080 px. "Tail" is the mean normalised excess at 12-30 px (1080 scale).

| Peak luma class | TF tail / w10 | AW | PN | CG |
|---|---|---|---|---|
| 150-185 (non-emissive mid-tones) | 0.131 / 26 px | 0.130 / 26 px | 0.121 / 24 px | 0.114 / 22 px |
| 185-215 | 0.160 / 30 px | 0.155 / 28 px | 0.106 / 26 px | 0.163 / 28 px |
| 215-240 | 0.145 / 28 px | 0.192 / 34 px | 0.142 / 26 px | 0.156 / 28 px |
| 240-255 (lamps, sparkles, white-hot) | 0.144 / 26 px (n = 57) | **0.030 / 12 px** | 0.192 / 36 px (n = 9) | 0.123 / 32 px |
| Small bright points (≤ 40 px²) vs large | 0.29 vs 0.23 at 16 px | 0.10 vs 0.05 | **0.27 vs 0.08** | 0.22 vs 0.20 |
| Dark-blob control (same edge spread with no light) | 0.136 | 0.119 | 0.130 | 0.208 |

Reading the results:
- The brightest objects do **not** spread wider than mid-tone objects, and bright edges look like the dark-blob control. The roughly 25-30 px tail is the same softness everywhere: 540p detail upscaled, compression and soft shading.
- So there is **no measurable thresholded bloom**. TF's visible glows are local: sprite halos on fairies and lamps, and Sparkles particles.
- PN's small lamp points carry a tail 3x wider than its large bright areas, so lamp glow is local there too.
- For our render:
  - Do not rely on UnrealBloomPass for the look. If used, keep it very low: threshold about 0.9 (after tone mapping), strength ≤ 0.15, radius about 0.3.
  - Fake glows with additive soft-disc sprites (radius 15-40 px) on lamps, fairy wands and sparkle particles.

### 4c. Grain and noise

The measure is the std of the high-pass (luma minus Gaussian σ 2) in flat 32x32 blocks, in 8-bit levels.

| | TF | AW | PN | CG |
|---|---|---|---|---|
| Luma noise σ, median (p90) | 0.18 (0.32) | 0.16 (0.36) | 0.23 (0.39) | 0.28 (0.36) |
| Chroma σ, Cb / Cr | 0.18 / 0.10 | 0.19 / 0.13 | 0.21 / 0.12 | **0.40 / 0.35** |
| Flat blocks per frame | 295 | 207 | 232 | 204 |

There is **no grain in any video**: noise is far below one 8-bit level. CG has about 2x the chroma noise, which fits its dusty late-act filter, but it is still invisible. For our render: no film-grain pass. Our clean render will match.

### 4d. Blur and depth of field

The measure is the Laplacian variance per cell (6x10 grid at 540x960), normalised by gradient energy. The ratio compares periphery cells with centre cells that have enough edges.

| | TF | AW | PN | CG |
|---|---|---|---|---|
| Periphery / centre normalised sharpness, median (p10) | 1.07 (0.79) | 1.06 (0.75) | 0.93 (0.64) | 1.09 (0.83) |
| Frames with periphery < 0.6x centre | 1.6 % | 1.7 % | 9.0 % | 2.4 % |

The strongest candidates were checked on frames. They are flat textures (plaster, cloud, card), a large foreground door, and fog or haze. None are lens blur. For our render: **no DOF and no BokehPass**. Haze comes from scene fog (CG, PN), not blur.

### 4e. Chromatic aberration

The measure is phase correlation of R vs G and B vs G in 192x192 patches at the 4 corners and the centre, projected on the radial direction.

| | TF | AW | PN | CG |
|---|---|---|---|---|
| Corner R / B radial offset, median | 0.000 / 0.001 px | 0.002 / 0.000 | 0.000 / -0.003 | 0.002 / -0.001 |
| Corner abs offset p90, R / B | 0.06 / 0.06 px | 0.06 / 0.06 | 0.05 / 0.07 | 0.04 / 0.06 |
| Patches with offset > 1 px | 0 % | 0 % | 0 % | 0 % |

There is **no chromatic aberration**. The only RGB split anywhere is CG's glitch-bar transition (§4f), which is a horizontal band effect, not lens CA.

### 4f. Transitions and editor effects (detected per frame, then checked on strips)

| Effect | TF | AW | PN | CG |
|---|---|---|---|---|
| Hard cuts | all | all | all | all |
| Glitch-bar cut: full-width red and cyan horizontal bars, RGB-split ghost, 6-9 frames starting on the cut | 0 | 0 | 0 | **16**: 85.03, 95.92, 98.33, 99.10, 102.42, 104.65, 105.90, 107.47, 108.42, 110.63, 114.42, 115.85, 117.23, 119.32, 122.65, 125.85 s |
| White-flash cut: the first frame is washed toward white (about +50 % white), decaying over 3-4 frames | 0 | 0 | 0 | **3**: 91.18, 107.92, 120.17 s |
| Editor shake hit | 0 | 0 | 1 (21.93 s) plus an opening spin-in (0-0.12 s) | 0 |
| Dissolves or fades | 0 | 0 | 0 | 0 |

The effect detectors also flag content that only looks like an effect:
- Glitch-like flags caused by striped content (gate barrier, railings, picture frames): TF 1, AW 13, PN 12, CG 20. A sample of about 30 was viewed and all were content, not glitch.
- Flash flags caused by hard cuts into bright scenes or fog: TF 5, PN 1, CG 1. 4 were viewed and none was a flash.

For our render: TF style uses **hard cuts only**. Keep the glitch and white-flash cuts for a horror-escalation act if we ever want the CG feel.

---

## 5. Captions (burned in), timed against ASR

**Method**
- **Caption mask:** bright fill pixels (Y' > 150, max channel > 200) within about 4 px of a black stroke pixel (max channel < 50), in the band at 60-78 % of the height.
- **Change event:** the first frame where the mask XOR between consecutive frames exceeds 50 % of the union. Events within 3 frames are merged.
- **ASR:** Parakeet TDT 0.6B int8 through `tools/transcribe.py`, run on each full copy. Word count: TF 570, AW 707, PN 744, CG 532.
- **Matching:** mutual nearest event and word, within ±0.4 s.
- **Precision:** ASR word times are quantised to 80 ms, so treat lag values as ±40 ms.

| | TF | AW | PN | CG |
|---|---|---|---|---|
| Text band (fill rows, 1920 scale) / centre y | 1326-1384 / **1355** | 1284-1334 / 1309 | 1326-1384 / 1355 | 1334-1384 / 1359 |
| Text x extent (typical word) | 364-712 | 338-726 | 348-736 | 372-698 |
| Caption change events / ASR words | 553 / 570 | 698 / 707 | 706 / 744 | 529 / 532 |
| Matched pairs | 434 | 593 | 561 | 420 |
| Caption minus word onset, median | **+7 ms** | -27 ms | -23 ms | 0 ms |
| IQR | -37 to +40 ms | -53 to +10 | -57 to +17 | -37 to +40 |
| Within ±50 ms / ±100 ms | 62 % / 91 % | 66 % / 94 % | 62 % / 93 % | 60 % / 86 % |
| Median hold per caption | 0.20 s | 0.23 s | 0.18 s | 0.23 s |
| Frames without a caption | 0.66 % | 0.09 % | 0.13 % | 1.55 % |

For our render (or for CapCut):
- Show one word at a time, swapped exactly on the word onset, between -2 and +1 frames.
- The band is never empty.
- Centre y is about 1355 in the TF/PN/CG house style (AW sits about 45 px higher).

---

## 6. Cuts against word onsets

**Method**
- For each cut, take the nearest ASR word onset; the signed distance is cut minus word.
- "Chance" is the share of random times that land within the same tolerance of some word onset. Words come about 4.2-4.5 per second, so even random cuts are within 150 ms of a word 85-88 % of the time.

| | TF | AW | PN | CG |
|---|---|---|---|---|
| Cuts within ±150 ms of a word onset (chance) | **98.2 %** (85.7 %) | 96.0 % (85.0 %) | 89.7 % (88.2 %) | 96.1 % (86.2 %) |
| Within ±80 ms (chance) | **86.8 %** (61.3 %) | 68.3 % (58.9 %) | 47.9 % (63.6 %) | 84.5 % (60.8 %) |
| Within ±40 ms (chance) | 54.4 % (34.7 %) | 41.6 % (32.5 %) | 17.1 % (36.1 %) | 50.5 % (33.4 %) |
| Cut minus word, median (p10 to p90) | **-7 ms** (-69 to +62) | -40 ms (-120 to +37) | **-77 ms** (-143 to -5) | -23 ms (-83 to +36) |
| Sentences whose first word is within 150 ms of a cut | **95.2 %** (60 of 63) | 63.6 % | 71.7 % | 93.3 % |

Reading the results:
- The ±150 ms figure barely beats chance, so it is not a useful test. The ±40-80 ms figures and the median offset carry the signal.
- TF and CG lock cuts to the onset (median -7 / -23 ms, i.e. 0-1 frame early).
- PN leads consistently by about 5 frames (-77 ms): the picture arrives just before the word.
- For our render: **cut at `word.t - 0.02 s` (1 frame early)** on the word that names the new picture, and start every sentence on a new shot (TF: 95 %).

---

## 7. Audio

**Method**
- ffmpeg `ebur128` on the mixes and on UVR-MDX-NET-Inst_HQ_3 stems (voice vs music+SFX).
- The CG and AW stems were separated for this run. The TF and PN stems came from the per-video analyses.
- Onsets were found with librosa on the music+SFX stem. "Strong" means onset strength > median + 8 MAD while the stem is above -40 dBFS.

| | TF | AW | PN | CG | Our VO (`audio_39.wav`) |
|---|---|---|---|---|---|
| Mix: integrated / LRA / peak | -17.5 LUFS / 3.0 LU / -1.7 dBFS | -16.9 / 3.3 / -0.4 | -13.7 / 2.1 / -0.8 | -17.2 / 3.6 / -0.9 | -21.8 / 1.8 / -1.9 (raw VO) |
| Voice stem | -21.6 LUFS | -18.2 | -15.1 | -17.9 | |
| Music + SFX stem | -29.9 LUFS | -25.8 | -20.9 | -27.0 | |
| **Voice above music+SFX** | **+8.3 LU** | +7.6 LU | +5.8 LU | +9.1 LU | |
| Music stem active (RMS > -50 / > -40 dBFS) | 100 / 98.5 % of time | 99.9 / 97.9 % | 100 / 100 % | 99.9 / 95.2 % | |
| Music RMS under speech vs voice RMS | -31 vs -23 dBFS | -29.5 vs -22.7 | -23.6 vs -19.2 | -32.1 vs -22.4 | |
| Tonality (spectral flatness, chroma peakiness) | 0.0003, **0.61** (clearly tonal: melodic music box or piano) | 0.0001, 0.22 (pad or drone) | 0.0000, 0.28 | 0.0002, 0.40 | |
| Music-stem onsets per min (all / strong / strong and not on a word onset) | 234 / 41.5 / **16.4** | 143 / 56.8 / 19.3 | 167 / 50.0 / 17.6 | 196 / 31.0 / 10.3 | |
| Cuts with a strong onset within 100 ms (chance) | 14.0 % (13.4 %) | 23.8 % (17.9 %) | 20.5 % (15.9 %) | 8.7 % (10.3 %) | |
| Words / span | 570 / 131.1 s | 707 / 174.0 s | 744 / 166.4 s | 532 / 127.1 s | 440 / 112.5 s |
| wpm overall / without pauses > 0.35 s | 261 / 286 | 244 / 270 | 268 / 288 | 251 / 275 | **235 / 262** |
| Pauses > 0.35 s (median length) | 117 (0.40 s) | 139 (0.48 s) | 132 (0.40 s) | 99 (0.40 s) | 88 |
| First word / video end after last word | 0.08 s / +0.36 s | 0.00 s / +0.31 s | 0.00 s / +0.38 s | 0.00 s / +0.72 s | |

What this means for our render:
- **The voice starts on frame 0, and the video ends about 0.3-0.4 s after the last word.**
- A music bed runs the whole time, about 8 LU under the voice. TF's bed is clearly melodic.
- SFX are sparse: about 10-19 transients per minute that are not speech, one every 3-6 s. **They are not tied to cuts**: the cut-hit rate is roughly chance. Place SFX on story actions (a door, a creak, a pop), not on every cut.
- Master to about -16 to -17 LUFS integrated with LRA ≤ 3.5 LU. Our raw VO at -21.8 LUFS needs about +5 dB of gain or compression.

---

## 8. Render checklist derived from the numbers (Three.js / SwiftShader)

1. **Timeline**
   - Cuts are computed from ASR word times: cut = onset of the naming word - 1 frame. Every sentence starts on a cut.
   - Target 45-52 cuts per minute, median shot 1.1-1.2 s, p90 ≤ 2.0 s, maximum about 2.3 s.
2. **Camera**
   - Every shot has a linear push with no easing: scale +12 to +30 % per shot, median +19 %, about 16 %/s. Add a slow drift of 20-70 px/s and a roll of ≤ 1 °/s.
   - About 15 % of shots get a fast crane, whip or orbit, and the first shot is one: a pull-back from an extreme close-up, at 3000-5500 px/s peak.
   - About 8 % of shots are pull-outs. The camera is never locked off.
3. **Animation:** about half the shots have a near-still character (idle only), and about 35 % are active. Render a true 60 fps.
4. **Grade**
   - Use a per-set monochrome highlight tint (TF: lavender #d0bae1, peach #f2d1bb, periwinkle #858dec). Shadows are maroon or lifted (p1 ≈ 5-10) indoors and true black outdoors at night.
   - p99 luma ≈ 210-230, and luma clipping ≤ 0.3 % of pixels. Saturation is about 0.45-0.6 (HSV mean).
5. **Post**
   - None of the following: vignette, grain, CA, DOF, motion blur.
   - Global bloom is off or at most 0.15 (threshold 0.9). Glows are additive sprites.
   - Captions, if we burn them, are one word at a time, centred at y ≈ 1355, and swap at the onset.
6. **Optional "escalation" kit (CG only)**
   - A strong elliptical vignette (edges x0.5).
   - Glitch-bar cuts: 6-9 frames of full-width red and cyan bars plus an RGB-split ghost.
   - White-flash cuts: +50 % white, decaying over 3-4 frames.
   - Floating dust specks.

## 9. Caveats

- **The residual "subject motion" includes parallax.** The thresholds were calibrated on TF's hand labels, so treat the classes as approximate for the other videos.
- **The cadence estimate needs motion.** It reads only moving frames and calls a frame a duplicate when its difference is below 0.2x the local motion level, so static shots are unclassified.
- **Bloom, grain and CA are measured after YouTube compression** at about 1.3-1.75 Mb/s and roughly 540-720p real detail. A very faint effect (bloom tail < 0.05, grain σ < 0.5) could be hidden by compression. Anything that changes the look visibly would show.
- **The vignette and "looks" figures use content averages.** The flat-row test is what separates post vignette from lighting. The looks are k-means clusters (k = 4) of shot means, not hand-labelled sets.
