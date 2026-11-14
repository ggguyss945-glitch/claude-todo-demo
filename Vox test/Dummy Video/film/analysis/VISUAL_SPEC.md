# VISUAL_SPEC: measured targets from the reference videos

References: `fire.mp4` (498 s), `hotel.mp4` (540 s), `class.mp4` (629 s), all 1280x720, 30 fps.
Crops: `$S/pov2/refcrops/<name>.png` (55 files, at most 640 px; the name ends with `__<video>_<seconds>s`).
Data: `$S/pov2/va/` (1 fps frames `<video>/fNNNN.jpg`, `motion_*.json`, `look.json`, `cuts2_*.txt`, `lum15_*.npy`).
Scripts: `v2/analysis/*.py` and `$S/pov2_trans.py`, `$S/pov2_char.py`. All pixel values are at 1280 px width unless noted.
At 2560x1440 output, double every pixel value.

The overall style is clean flat vector cartoon (thick dark outlines, flat fills, one soft shade step, no film grain)
inside heavily vignetted, dark, layered sets. The camera is almost always moving slowly. It is creepy because of the
faces (huge staring eyes, fixed grins, tears), the darkness and red light, and constant slow push-ins. It is not
creepy because of texture.

## a) Global look per scene family

Luma (0 to 255) percentiles over 1 fps frames for each family. Sat is the mean HSV S (0 to 255). Contrast is the luma std.

| family | p1 | p5 | p50 | p95 | p99.5 | contrast | sat mean / p90 | palette (most frequent first) |
|---|---|---|---|---|---|---|---|---|
| night exterior | 5 | 7 | 22 | 91 | 164 | 29 | 113 / 204 | #0b0c13 #1f2129 #3c0e10 #4a403d #8c7c6a #101c38 #68605d |
| porch light / doorway | 3 | 7 | 31 | 147 | 171 | 45 | 64 / 159 | #0e0d10 #1d1c1c #48382f #271f20 #73685f #ad8b5f #d5b88e |
| peephole | 1 | 1 | 1 (black surround) | 148 | 213 | 46 | 57 / 168 | #020101 #1a181c #343142 #9d886d #675436 #c5af8e #b29225 |
| dim interior | 12 | 14 | 30 | 77 | 171 | 23 | 90 / 150 | #17141c #2c3649 #171e37 #4d5e6c #345c96 #898b7e #cfcdc5 |
| warm interior (hotel) | 16 | 21 | 49 | 180 | 216 | 49 | 125 / 192 | #3f2920 #23150d #6a312e #7c7060 #4c4d48 #c6baaa |
| red alert | 7 | 10 | 22 | 56 | 78 | 15 | 128 / 163 | #1c090d #2e0d13 #0c0408 #543032 #381b20 #584b4e |
| phone / UI | 5 | 9 | 21 | 73 | 200 | 29 | 105 / 169 | #160c10 #20222d #3e3e44 #634e3c #a9a2a2 #dad9dd |
| rule card | 7 | 8 | 31 | 98 | 253 | 38 | 47 / 98 | #0d0a0a #221e1b #988147 #655642 #f6f6f6 #dfd7ca |
| face close-up | 15 | 22 | 48 | 196 | 226 | 51 | 103 / 171 | #211817 #2b2b32 #585850 #4f2d27 #9f958d #d9d9de |
| (classroom, brightest) | 30 | 39 | 88 | 164 | 241 | 39 | 55 / 149 | #4d5558 #303435 #687b78 #bec1c5 #eeeff0 |

- **Blacks** are never crushed to 0 except in the peephole surround and in letterbox areas. Night scenes have p1 of 3 to 7.
  The fire video's median luma is 22 to 34: it is dark. Only faces and practical lights reach above 190.
- **Grain** (high-pass std in flat regions) is 0.0 to 0.23 levels, so there is effectively none. The art is clean vector work,
  and v2 must not add visible grain (if you add any, keep the std at or below 1.5 levels).
- **Softness**: edge 10 to 90% rise width is 1.5 to 1.75 px on in-focus outlines, so the art is crisp and antialiased, not blurred.
- **Vignette** (mean-frame luma relative to the centre at r = 0.4/0.6/0.8/0.95 of the corner distance):
  fire 0.59/0.44/0.29/0.19, class 0.73/0.54/0.39/0.25, hotel 0.80/0.68/0.52/0.36. This is strong: v2 night
  scenes should reach about 0.3 at r = 0.8 and below 0.2 in the corners.
- **Bloom on lights**: on exterior lights (porch lamp, windows, truck lights) the halo excess as a fraction of peak at
  2/6/12/20/30 px is 0.20/0.19/0.10/0.07/0.04 (fire 27 s, 45 s). That is a soft glow with a radius of about 20 to 30 px
  at roughly 20% strength. Interiors have no bloom.
- **Chromatic aberration**: measured R-vs-B shift is 0.0 to 0.1 px, so there is none. Do not add any.
- **DOF**: background behind close-ups is blurred in the class video (bg edge rise 7.5 to 7.75 px vs 1.75 in focus, which is
  a Gaussian sigma of about 3 px at 1280). Hotel and fire close-ups keep backgrounds sharp (rise 1.5 to 1.75) but darken them.
  For v2, use sigma 3 px (6 px at 2560) on background layers behind face close-ups, plus darkening of about -30%.
  See `face_class_blonde_dof__class_91s.png` and `face_class_girl_scream_tears_dof__class_194s.png`.

## b) Motion (Farneback at 6 fps, 320 px wide, scaled to 1280)

| | fire | hotel | class |
|---|---|---|---|
| share of time the camera moves | 0.77 | 0.64 | 0.50 |
| share of time zooming in / zooming out | 0.67 / 0.07 | 0.51 / 0.09 | 0.45 / 0.03 |
| push-in rate in %/s, p25/50/75/90 | 1.4/2.3/3.7/5.5 | 1.7/2.8/4.8/7.6 | 1.7/2.6/4.3/9.8 |
| total zoom per shot in %, p50/p90/max | 4.6/10.3/23 | 3.1/9.7/28 | 2.7/10.4/72 |
| pan speed px/s, p25/50/75/90 | 11/16/28/48 | 11/17/31/55 | 10/14/24/56 |
| handheld shake (high-pass translation std) | 11.5 px/s | 7.7 | 9.5 |
| subjects moving (residual flow p90 > 30 px/s) | 24% of time | 30% | 16% |

- Shot moves (shots of 1.5 s or longer): fire 51% push, 27% push plus pan, 18% static, 1% pull, 2% pure pan.
  Hotel: 45/19/29/4/3. Class: 47/5/44/1/2.
- **Ease profile** of the push (mean cumulative fraction at t = 0, .2, .4, .6, .8, 1): 0.02/0.20/0.45/0.67/0.83/1.0.
  That is nearly linear with a slight ease-out. There is no ease-in, so the move is already moving on the first frame of the cut.
- Pull-outs are rare and fast (p50 2.4%/s, p90 10%/s). They are used for reveals.
- **Shot length** in seconds, p10/25/50/75/90: fire 1.17/1.67/2.42/3.67/4.83 (mean 2.86); hotel 1.17/1.5/2.17/3.17/4.27 (mean 2.51);
  class 1.17/1.67/2.5/3.67/4.67 (mean 3.0). That is 15 to 28 cuts per minute.
- **Transitions** (15 fps luma analysis of 596 cuts): 85% hard cuts, 11% soft (dissolve or motion cut over 3 or more frames),
  3% white or static flash (scare beats, `ui_fire_static_glitch__fire_62p7s.png`), under 1% dip to black.

## c) Characters

Crops: `face_*`, `body_*`. Reference sheets: `$S/pov2/va/faces1.jpg`, `expr_strip.jpg`, `bodies.jpg`.

- **Build**: chunky simplified bodies, about 3 to 3.5 heads tall (`body_hotel_family_elevator`, `body_fire_firefighter_points_neighbor`).
  The head is large, a rounded rectangle or bean, and the neck is a thick block. The bodies are wide trapezoids and the hands are simple mitts.
- **Eyes**: each eye white is a round circle about 0.17 to 0.22 of head width. The pupil is a solid black dot about 0.40 of the eye-white
  diameter, with a 1 to 2 px white catchlight. A wide-eyed (creepy or scared) look is achieved by shrinking the pupil to about 0.30
  and enlarging the eye white by about 15%. Brows are thick dark strokes, and their angle carries the emotion.
- **Outline**: near-black blue-grey, #1d1f26 (measured #101d26 to #282a31; the hotel guest is #1d1412). The width is 5 to 6 px
  (p25 to p75 is 4 to 7) on close-up figures and about 2 to 3 px on wide shots. The line weight is uniform.
- **Skin**: pale and desaturated: #c0aa9e, #b89e90, #ac9585, #b6947e, with a shadow tone of about #8c746a. There is a pink blush ellipse
  under the eyes (#e0a0a0 at about 40% alpha). Fills are flat with one soft shade step
  (skin luma std 8 to 28: one gradient falloff toward the edges, not cel bands).
- **Clothing**: flat colours with a few grunge patches. The firefighter coat has darker blotches, and uniforms are flat red #8a1f24
  with white collars. Texture is minimal: there is no paper texture or hatching.
- **How creepiness is achieved** (`face_hotel_receptionist_grin_mid__hotel_48s.png`, `..._grin_tears__hotel_58s.png`):
  - A grin wider than the eyes (about 0.6 to 0.7 of head width) with a full row of separate white teeth outlined in black.
  - A fixed stare with no blinks: blink detection found 0 blinks in 6 of 9 close-up segments. Characters stare.
  - Tears: 2 to 3 pale blue (#a8c8f0) streaks running from the eyes to the chin, while the character keeps smiling.
  - Tiny pupils, raised brows, and a flat mouth for "standing completely still" (`face_fire_peephole_still_stare__fire_432s.png`).
  - Characters loom close to the lens: the face fills 50 to 70% of the frame height.
- **Expression catalogue** (crops): calm smirk (`face_fire_peephole_calm_smirk`), shout with a big black O mouth and V brows
  (`face_fire_peephole_shout`), nervous with a wavy mouth and up-slanted brows (`face_fire_peephole_nervous`), still stare,
  grin with tears (`face_hotel_receptionist_grin_*`), crying with an O mouth (`face_hotel_guest_crying_bubble`), shock with a hand raised
  (`face_hotel_housekeeper_shock`), scream (`face_class_man_scream_redtag`, `face_class_girl_scream_tears_dof`),
  trembling (`face_class_girl_trembling`), and a red-lit sweating protagonist (`face_fire_you_redlit_sweat`).
- **Acting** (30 fps strips): faces mostly hold still. Eye-centre speed median is 0 to 11 px/s, and changes are made by cutting between
  expression poses, not by tweening. Visible motion comes from (1) camera push-ins, (2) slow sway or breathing of 2 to 4 px over
  about 2 s, (3) occasional pose swaps and head turns (back-turn at fire 53.5 s, done as a pose swap within 0.5 s), (4) arm gestures
  such as pointing (`body_fire_firefighter_points_neighbor`), and (5) tears that animate downward. When blinks occur they are
  1 to 2 frames (hotel 90.7 s, 4 blinks in 1 s for a nervous character). Walk cycles are rare and short: characters are mostly
  shown standing in doorways and halls.

## d) Doorbell and peephole lens

Crops: `peephole_fire_*`, `peephole_hotel_door__hotel_283s.png`, `face_fire_peephole_*`. Strip: `$S/pov2/va/strip_peep.jpg`.

- The disc is centred, with a diameter of 0.98 H (x 284 to 995 at 1280x720). Outside the disc it is pure black (luma 1).
- Radial luma inside, at r = 0, .1, ..., 1.0 (fire 432 s): 166 163 156 130 119 83 66 56 44 18 8. That is a strong lens vignette
  starting at r of about 0.4 and falling to about 30% at r = 0.8, with a thin brown-black rim ring (#2a2018, about 4 px).
- Barrel distortion makes straight house lines and the fire truck bow outward. The estimated k1 is about 0.25 to 0.35
  (normalized to the disc radius) with an FOV feel of about 150 degrees. The subject sits in the centre and is magnified,
  so the head appears oversized (bobble-head effect).
- Approach: the subject grows from about 45% to about 70% of the disc diameter over 2 to 3 s, combined with a camera push of
  about 2 to 4%/s. Back-turns and reveals are pose swaps.
- There is no IR or monochrome. The night look is a blue sky #101c38 to #343142 with warm windows, sometimes with a purple tint
  (fire 414 s). There is no HUD in the peephole. Doorbell-camera HUDs are not used in these references, so a v2 doorbell cam should
  follow the UI rules in section f and the same vignette.

## e) Sets and props

Crops: `set_*`, `prop_*`.

- Every set has 3 to 5 depth layers: a dark foreground silhouette or frame (door edge, wall), the subject, a mid-ground of
  furniture and props, and a background (houses, sky with stars and moon, corridor vanishing point).
- Practical lights: porch lamps, window rectangles lit warm #d5b88e to #ad8b5f with bloom, light cones on floors
  (`set_fire_porch_light_neighbor`), and screens glowing (`set_fire_livingroom_tv`).
- Gradients are used everywhere (sky, walls, floor falloff), with flat fills on top. There is about 1 detailed prop per 10% of frame area:
  clocks, key cabinets, lockers, hallway doors with numbers, smoke detectors, chalk marks.
- Red-alert scenes (`set_fire_red_smoke_room`, `set_fire_redblue_door`) use a monochrome red wash #2e0d13 to #543032 with
  fog bands and a single light source.

## f) UI and graphics

Crops: `ui_*`.

- **Captions**: bold white uppercase sans (Montserrat ExtraBold style), cap height about 1.7% H, centred at y about 0.88 H,
  with a soft dark drop shadow and no box.
- **Alert tag** "NEVER OPEN UP" (`ui_fire_never_open_up__fire_9p2s.png`): red box #c0161c, 58% of W wide, with a hard cut-in (0 frames),
  held 1.2 s, then a hard cut-out.
- **Rule card** (`ui_fire_rule_card_05__fire_298p3s.png`, `ui_hotel_rule_card__hotel_234s.png`): a large white numeral "05"
  about 9% H tall, which pops in within 2 frames (0.07 s). The rule text is white bold uppercase with keywords in red, typed on
  over about 3 s (ink grows linearly at 0.5 s samples), held about 1.5 s, then cut. The background is a dimmed, blurred scene
  with a small icon.
- **Speech or label tags** (hotel): white rounded box with a black dashed border, and red text for the threat words.
  It fades in over about 1.0 s. Height is about 6% H.
- **Phone screens** (`ui_fire_911_phone_dispatch`, `ui_hotel_phone_unknown_call`, `ui_class_chat_phone`): a dark phone held in a hand,
  filling about 55% of H, with a green or red call UI.
- **Waveform and panel graphics** (`ui_fire_waveform_panels`, `ui_fire_floorplan_panel`, `ui_fire_window_scene_panel`):
  dark navy panels with thin outlines and red or blue waveform bars.
- **Static glitch**: a full-frame grey noise flash of 2 to 6 frames.

## g) Pacing and tone arc

The table shows the average for each tenth of the video. Luma is the mean, red% is the share of strongly red pixels, cuts are per tenth,
and subj is the subject-motion p90 in px/s.

- fire: luma 30, 28, 33, 34, 32, 28, **24**, 27, 31, 29. Red% 0.7, 0.9, 0.1, 1.4, 0.7, 0.6, 0.8, **3.2, 3.2**, 2.0.
  Sat 96 rising to **144**. Subj 23 rising to **50**. Cuts per tenth fall from 22 to 13 in the climax, where shots are longer and slower.
- hotel: red% starts high (10%, the red carpet) and dips in the 7th tenth before the climax. Subj motion rises from 21 to **59**,
  and luma drops to 62 at the end.
- class: blue% peaks at 11.7 in the 6th tenth with the strongest zoom (4.65%/s). The end has red 10% and sat 121.
- The pattern: darkness and red share rise in the last 30 to 40%, subject motion roughly doubles toward the climax, and camera zoom
  stays at 2 to 3%/s throughout. The climax uses slightly longer, more saturated shots, not faster cutting.

## h) The 15 most important things v2 must do (ranked)

1. **Faces carry the horror**: in close-ups, eye whites are 0.17 to 0.22 of head width and pupils 0.30 to 0.40 of the eye white.
   Include at least one fixed grin of 0.6 or more of head width with separate teeth, and tears on the "wrong" smile. Faces should fill 50 to 70% of H in close-ups.
2. **Camera always moving**: the camera should move in at least 65% of the runtime. The default push-in is 2 to 3%/s
   (p90 6 to 8%/s), and total zoom per shot is a median of 4 to 5% (p90 about 10%). The move is already moving at the cut and eases out slightly.
3. **Cut rhythm**: median shot 2.2 to 2.5 s, p10 1.2 s, p90 4.3 to 4.8 s, 20 to 25 cuts per minute, and 85% hard cuts.
4. **Dark exposure**: night median luma 20 to 35, p5 at or below 10, and highlights (p99.5) of 160 to 215 only on faces and lights.
5. **Strong vignette**: luma at r = 0.8 should be at or below 0.35 of the centre on night shots (fire measured 0.29).
6. **Peephole**: disc diameter 0.98 H, black outside, radial falloff to about 30% at r = 0.8, barrel k1 about 0.3, and the subject
   growing from 45% to 70% of the disc on the approach.
7. **Clean outlines**: near-black blue-grey #1d1f26, 5 to 6 px at 1280 (10 to 12 px at 2560) on close-ups, uniform weight, crisp
   (edge rise at or below 2 px), no grain or CA.
8. **Pale skin palette**: #c0aa9e, #b89e90, #ac9585, with a pink under-eye blush, flat fills and one soft shade.
9. **Layered sets**: 3 to 5 depth layers per shot with at least one practical light. Bloom on the lights should be about 20% at 6 px,
   falling to 4% at 30 px.
10. **Red climax**: red-pixel share goes from at most 1% to at least 3% in the last 35%, saturation rises by about 40%, and luma drops by about 15%.
11. **Subject motion**: something moves at more than 30 px/s in 20 to 30% of the time (sway, gestures, tears, pose swaps), and that rises
    toward the climax (subject motion p90 doubles).
12. **Stare acting**: no blinks on creepy characters, 1 to 2 frame blinks on scared characters, pose swaps of 0.3 to 0.5 s, and
    2 to 4 px breathing sway.
13. **Rule cards**: the numeral pops in at 9% H (in 2 frames or fewer), the text types on over about 3 s with red keywords, and the card holds about 1.5 s.
14. **Alert tags and flashes**: hard-cut red tags about 58% of W, held about 1.2 s. Use 2 to 6 frame white or static flashes on 3% of cuts at scare beats.
15. **Background DOF** behind close-ups: Gaussian sigma about 3 px at 1280 (6 px at 2560) on background layers, darkened about 30%.
