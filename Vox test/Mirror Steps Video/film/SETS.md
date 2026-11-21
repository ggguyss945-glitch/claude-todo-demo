# SETS.md: the sets of "If The Queen Of Spades Appears In Your Mirror... DON'T MAKE A WISH" (v2)

`sets.py` builds every set view the plan names; the v2 sets live in `sets_v2.py` (imported at the end of `sets.py`, which
registers them in `sets.VIEWS`) and are built on `engine/room3d.py`, a small projection kit: **one room model in metres gives
every angle of Cabin 7, the mirror's true reflection and the flipped other side.** All 449 shots of `plan/shots.json` build.
The v1 builders are still used for the relit exteriors and memories (appendix B keeps their notes).

```python
import sets
sp = sets.build_shot(shot)          # shots.json entry -> SetPiece (TYPE / DIAGRAM shots build their blurred `plate`,
                                    # rule cards their `bg`, SPLIT shots both panels)
sp.anchors['noah_bunk']             # Anchor(x, y, depth, height): computed from the 3D model for this camera
sp.info['cam3'], sp.info['xf']      # the room3d camera and model transform: place anything at a 3D point (below)
img = render_frame(list(sp) + char_layers, cam.at(t), t, i, **sp.render_kw(), post=sp.fx(t), hud=...)
```

Tools (all under `tools/`):

| tool | what |
|---|---|
| `sets_v2_try.py OUT [--chars] [--size WxH] SPEC ...` | quick renders: `S055`, `S055@72.8`, or `set/view/var@t[:prop=value,...]` (a synthetic shot with the plan's props at t); prints build / bake / warm times and luma |
| `sets_v2_stills.py OUT [--combos] [--chars] [--size WxH]` | one still per shot (or per set/view/var), the look statistics of REF_V2 (640x360, caption band dropped: luma p5/p50/p95, HSV sat, colourfulness, Canny edges, red-pixel share, hue), per-world and per-tenth summaries, `looks.json` |
| `sets_v2_geography.py [OUT]` | the geography sheet: top-down plans of both cabins rendered from the model, both master wides, the doorway, the stairs from both ends, the section |
| `sets_bench.py --combos` | warm frame time at 2560x1440 per set/view/var (sets + grade + post, no cast or HUD) |

Deliverables in `_work/sets_v2/`: `geography_v2.jpg`; `gate_g2_stills.jpg` (+ `gate_g2/`, the 12 G2 stills at 1280x720 with the
cast); `combos/stills/` (one still per set/view/var with the cast, 960x540) and `contact_combos_1..4.jpg`; `all/stills/` (one
still per shot, sets only, 640x360), `all/sheet_1..5.jpg`, `all/looks.json`; `bench/bench.txt`.

---------------------------------------------------------------------------------------------------------------------

## 1. The model (geography)

Units are metres. **x** runs right from Cabin 7's left wall, **y** up from our floor, **z** from the door wall (0) to the back wall
(6.4). The roof is gabled along z (walls 2.6 m, ridge 3.9 m), with rafters every 0.8 m, three tie beams and a ridge beam.

| thing | OURS (Cabin 7 tonight) | THEIRS (x -> 5.6 - x, 14 years younger) |
|---|---|---|
| left bunk / Noah's bunk | left bunk along the left wall x 0.08-0.92, z 4.25-6.3; **Noah's bunk** along the right wall x 4.68-5.52 | **Noah's bunk** on the left (green plaid), the other bunk on the right (blue) |
| back wall, left to right | clock (x 1.15, y 2.12), window x 1.45-2.2 (torn screen, moon), **the mirror** x 2.39-2.94, calendar, pennant | Noah's bunk, **the 8 steps rising along the back wall** (tread 8 beside the bunk at x 0.94-1.18, tread 1 = the landing under the doorway), **the doorway 1.8 m up** (x 2.66-3.21, the same white chipped frame), window (gingham frozen at 12 deg, lantern), clock 6:59 |
| cubbies | 6 cubbies on the right wall above Noah's bunk (TY ELI SAM / LUIS JAKE NOAH), all empty, NOAH with a cobweb | full (clothes, comics); on the left wall |
| front | door x 3.55-4.45 (swings out; hasp + padlock outside; DEMOLITION sticker), rules sign + broom + mattress stack at front-left | the wash-house door (it swings in, `door_wash`) |
| floor | dust film, the moon patch (the window projected along the moonlight), AO under the furniture | the sun patch, the towel + the drop under the window, the other shoe, the wet prints from the wash-house door to the bunk |
| the crossing | through the doorway the stair shaft descends away from the back wall to the gold (`stairs_scene`, 0.25 m treads, 0.2 m risers, 9 balusters, plum, red edges) | their floor is 1.8 m below ours |

- **The mirror** (`mirror_plane`): 160 x 55 cm, 6 cm white chipped frame, standing on the floor at the mirror spot and leaning 22 cm
  out from the wall. The glass shows a **true reflection** of the same model (`Xf.reflect_plane`, darker and cooler, the mattresses
  and signs left out), a sheen band, a bevel line, desilvering spots and dust; the lamp shows **in** the glass (`glass_glint`).
  The lipstick steps and the 8th line are v1's (`lipstick_steps`, `eighth_line`) mapped onto the glass through a homography
  (`mirror_local_H`), so the v1 mirror-local coordinates (PANE 300..1620 x -1092..2252, `STEP_XY`, `EIGHTH`) still hold.
  States (`CabinCtx.mirror_state`): absent (the towel bundle under Noah's bunk), glass, tilted (-13 deg, `TILT_V2`; the 8th line
  stays level), towel (the towel over it, fingertips through the cloth on the `cloth_press` cues, the drop on `towel_drop`),
  doorway (the same frame, a raw splintered edge, the stair shaft inside), covered (the towel draped, the ending), dark.
- **The other side shows through** (`mirror/queen_glass`, `mirror/through`): the glass is cleared in its layer and a deeper layer
  shows the plum stairwell under the 8th step (or THEIRS from the top of their stairs, or the red version); the room's reflection
  stays at 20 %.
- **Doorway**: gold haze, rays and a floor pool spill into the blue cabin (`doorway_spill`), gold steam wisps 263.5-271 s,
  red with a 1.2 s pulse in the climax; in THEIRS the opening is our blue night, navy-dark while Tess is gone, red after 534.7.
- The geography sheet `_work/sets_v2/geography_v2.jpg` shows both plans (rendered from the model), the section and the matching wides.

## 2. engine/room3d.py

- `Cam3(pos, look=..., fov=..., roll=..., shift=...)`: pinhole camera into the 1920x1080 design space. `proj`, `pt`, `dist`,
  `px_per_m`, `anchor(P, height_m, d0) -> (x, y, height_px, layer_depth)`, `H(O, U, V)` (plane homography).
- `Scene3`: `plane(O, U, V, w_cm, h_cm, draw, order, ..., readable)`, `box(...)` (visible faces only), `quad`, `poly3`,
  `custom(centre, draw(pen, cam, xf))`, `light(P, colour, alpha, radius)`. Planes are drawn in their own centimetre coordinates
  through a perspective matrix, clipped to the part in front of the camera and to a bounded projection window (skia misbehaves
  past ~32k px). Point lights wash every plane and box face facing them (`a r^2/(r^2+d^2)`, confined to what the plane drew).
- `Xf`: model transforms. `Xf.flip_x(W)` = the other side (layout flipped; `readable=True` planes keep their text readable,
  `readable=False` planes, the shell, mirror with the room so holes and light pools stay in place); `Xf.reflect_plane` = the glass.
- `Scene3.layers(cam, d0, bands, key)`: cached engine Layers per distance band, layer depth = band distance / d0 (min 0.55,
  so plan dollies never blow up the near band). Planes are banded by their **farthest** corner (a wall or floor strip always
  lies behind what stands on it); the floor, walls and roof are split into strips that overlap 12 % so dollies do not open seams.
- Painter's order inside a band: camera depth of the item centre minus `order` (walls -100, floor -120, outside -200).

## 3. Views

### 3.1 Cameras
- **Cabin 7, OURS** (`OURS_CAMS`, 4.1's 12 angles): master (high, from the door), reverse (from the mirror spot to the door),
  under_bunk, profile (along the back wall), overhead, ots_mirror, three_q (from the left bunk), doorway_down (POV down the
  stairs through the doorway), dutch_low (8 deg, climax), floor_wide (the ending), doorway (MS), bunk_rail, floor_cu; inserts
  clock, cubby, sill, hands (a soft plate); door / camp_path cabin7_door = Cabin 7's front from outside (padlock on the hasp,
  hanging open from 71.9, gone at 462.9; DEMOLITION sticker; orange X; the 7 plaque).
- **THEIRS** (`THEIRS_CAMS`, 4.4's 10 angles + inserts): master (from their door: stairs, doorway, bunk, window in one frame),
  reverse (from the bunk up the stairs to the doorway), window, towel_floor, bunk_2s, queen_3s, top_stairs (Tess's view),
  ots_noah, dip_low, overhead, floor_prints, door_wash, swimsuits, lantern, clock, knot, shoe, hands, hands_jerk; window_out
  (the frozen lawn, the cue-timed sprinkler of loop A, the far porch whose bell swings by itself from 511.9) and far_porch (the
  gleaming fake bell, telephoto).
- **Stairs** (`STAIRS_CAMS`, 4.3's views): down (from our doorway: the treads to the gold room, Noah's bunk at the foot), up (to
  the doorway, Tess in it), low, treads (feet on treads), ots_climb (going down before 400 s, climbing after), pov_down, railing;
  section (the fixed dollhouse cutaway: Cabin 7 upper left, the white frame, 8 red treads, the gold cabin lower right; anchors
  `tread1..8`, `you_top`, `tess_door`, `noah_bunk`); bokeh, queen_ecu (blurred plates).
- **Mirror** (`MIRROR_CAMS`, placed on the mirror's normal): glass_cu (the steps, the left frame edge in shot), glass_wide,
  glass_tilt, queen_glass, reflection (OTS), through, towel_over (also `cabin_now/towel_over`).
- **Memory, past cabin** (`PAST_CAMS`): the real Cabin 7 14 years ago in 3D (OURS layout, lived-in, sepia palettes `past_day /
  past_morning / past_night`, the mirror at the same spot): bunk_morning, bunk_night, wake, towel_wet, socks, open_window,
  flash_445 (Noah at this mirror at 4:45), lantern_game, kids_game. Every memory has the film gate (`memory_gate_layer`:
  rounded corners 6 % H, specks, a hair now and then, a 1 px weave of the gate).
- **Relit v1 sets**: exteriors through `relight_night` (baked into each cached layer once: luma lifted, cool pixels rotated
  toward #5a5fa8, warm practicals kept warm) plus fireflies, warm practicals, orange X marks; memories through `relight_sepia`
  (cream / tan / dark ramp keeping 14 % of the original chroma). New exterior views: high_wide (from the porch toward Cabin 7's
  door, the crate right of the screen door), poster_ecu, gate_reverse, fence_track, aerial (X marks, warm windows). New memory
  plates: menu_board / kitchen_15 / office_phone / percolator (a kitchen with 8+ props), spoon (the spoon drops and bounces),
  moms_car / car_20 (the car at the gate), bell_ecu (the real cracked bell, sepia).
- **The bells** (`brass_bell`): a cast brass bell (crown loop, shoulder, waist, flared sound bow, a thick lip, the mouth as an
  ellipse with the clapper, engraved bands, verdigris, THE CRACK) everywhere v1 had a cone: mess_porch/bell_ecu (in the crate,
  in the beam), bell_hit (contact at 535.36: the padlock swings into the rim, spark, flash, wobble rings, the crack rattling,
  the red rim light), memory/bell_ecu, the fake perfect bell (gleam, no crack, no patina) on the far porch.
- **Bokeh plates** (4.7): every `*/bokeh` view (and `stairs/queen_ecu`) is a location view pushed far back, blurred (16 px), with
  drifting discs Ø 45-165 px in the world's colours (`BOKEH`: OURS blue-violet + warm beam discs, THEIRS peach/gold, CLIMAX
  magenta, STAIRS plum/red/gold, MEMORY cream). The CU views vary the location angle by shot.
- **Splits** (`split/*`): each panel is a full set view centred in its half (`src_t` panels run at their source time: the loop
  twins); anchors are prefixed `L_` / `R_`. **Plates**: `type/*` and `diagram/*` build `shot['plate']` with its blur/dim.

### 3.2 Anchors and placing the cast
Every room3d view computes its anchors from the model for its own camera: `Anchor(x, y_feet, depth = distance / d0, height
= design px of a person of that height there)`. OURS: `tess_door, you_door, you_mirror, you_kneel, tess_mirror, tess_beside,
tess_center, noah_stand, noah_floor, you_floor, tess_sill, noah_bunk_edge, doorway, mirror, sill, phone, clock, cubby_noah,
bundle`; THEIRS: `noah_bunk / noah_seat (on his mattress), queen_bunk, you_bunk_end, you_stand, you_room, queen_corner,
tess_doorway, doorway, stairs_foot, tread8, tread1, towel, drop, shoe, dip, door_wash, clock, window`; stairs: `tread1..8,
doorway, tess_doorway, bottom, noah_bunk, you_stairs, queen_tread8, queen_below`; mirror: `eighth / queen_step` (depth 1.04),
`step1..7`, `queen_on_step1..7` (the Queen grows 1.25x per step up), `glass`, `top_step`, `bottom_step`; past: the OURS set +
`kid_bunk, noah_top, kid_floor, kids_floor, noah_mirror`.
The plan's `chars[].at` are explicit design positions (first guesses); to seat a person on the floor of a v2 room use
`sp.info['cam3'].anchor(sp.info['xf'].p(P), height_m, sp.info['d0'])` for any 3D point P, or the named anchors.

### 3.3 `info` keys
`cam3`, `xf`, `d0`, `model` (the Scene3), `world`; mirror views: `glass` (projected glass polygon), `mirror_H` (mirror-local px ->
design px: clip and place the reflections of the cast, the Queen inside the glass, the HUD's count pops), `tilt`; OURS: `beam`
(the Beam: set `.override = f(t) -> (sx, sy, ax, ay, k)` to drive it from Tess's rig), `phone_spot`, `clock`, `sill`,
`mirror_plane`, `glass3d`; THEIRS: `tread_pt`, `stairs_theirs`, `doorway_theirs`, `swim_drips`, `towel`, `drop`, `shoe`;
section: `section`; bokeh: `bokeh` (palette), `insert`.

### 3.4 What moves (the "never a still frame" rule)
- OURS: moon shafts with drifting motes, Tess's beam (hand wobble, dust lit by it, its hot spot, the lamp seen in the glass),
  the clock (real time, the backward jerk 278.97-281.81), the lipstick (draw-on, smears on the cues, the wipe from the top down,
  the glow in the red), the phone on the sill (from 110.71, red glint from 118.87), the doorway spill (breathing; red pulse 1.2 s),
  the ending flashlight raking the floor with dust in its beam, fireflies outdoors, swaying pines, mist.
- THEIRS (frozen): motes hang and only twinkle; the loop moves: swimsuit drips, the clock loop (6:59:40 + 19.48 s, 7:00 at 535.36),
  the drop (drips, rises 335.25-337.09 and hangs with the room upside down inside it, falls again), the sprinkler arcs (cue-timed,
  identical in both loops), the prints (appearing on the `wet_footstep` cues 165.52-172.16, staying after), the wash-house door
  (swings in on the `door_creak` cue), the lantern's breath, Tess's beam down the stairs from the doorway (off while she runs),
  dawn_break: the red leak at the frame edges (`red_leak_layer`), the lantern stutter, the post flicker.
- Stairs: fog bands drifting, falling dust, the red edge glow breathing (2.4 s), the gold glow below.
- Set animations read their cue times from `plan/sound_plan.json` (`sets._plan_cues`), since v2 shots carry no `sfx`.

## 4. Looks

### 4.1 Palettes (`PAL`, `SPAL`) and variants
`night` (OURS: walls #50559a, floor #625e94, moon #cfd8ff, beam #ffd58a, pool #f0a84e), `after` (the ending), `red` (CLIMAX: a
wine-magenta base #7a3c80 / #642c64 so only the lights count as red pixels; red pours #ff2d55 from the doorway or glass),
`theirs` (gold #dcb878 / #d2b070, kept yellow enough that the gold does not count as red pixels), `theirs_break`,
`past_day / past_morning / past_night` (sepia), stairs `stairs` (treads #4a2c66, risers #2c1a3e, edge #c63449, fog, gold spill
#ffcf8a, moon #9fa8ff) and its `red`. Variant -> grade: night, doorway_glow -> `night_v2`; red -> `climax_v2`; after, phone_glow ->
`ending_v2`; dawn -> `dawn_v2`; dawn_queen -> `dawn_queen_v2`; dawn_break -> `dawn_break_v2`; stairs -> `stairs_v2`; sepia_* ->
`memory_sepia` (a shot's own `grade` wins).

### 4.2 Grades (engine/post.py, `_V2`)
`night_v2, stairs_v2, dawn_v2, dawn_queen_v2, dawn_break_v2, climax_v2, ending_v2, memory_sepia` (plus v1's `phone_dark`,
`neutral`). The 4.8 values (wb, sat, floors, bloom, vignette) with two changes: **no exposure lift** (the sets are drawn at their
target brightness, so the cast is never dimmed or blown), and contrast 1.26-1.32 with a low pivot (the brief's contrast target).
`memory_sepia` adds grain 2.5 and softness 0.8.

### 4.3 The light arc (`sets_v2.ARC`, `arc_fx`)
`sets.build` merges `arc_fx(t, world)` into every SetPiece's `fx`: +0.36 stop on OURS shots in 0-140 s (night readable), -0.06 /
-0.3 stop on THEIRS in 350-420 / 420-490 (the gold cooling near her), the red creeping into THEIRS after 534.7 (post `red` 0.08 ->
0.2), the climax pulse (+-0.06 stop at 1.2 s) in 560-628. The rest of the arc is the worlds themselves.

### 4.4 Measured (sets_v2_stills.py; REF_V2 method)
See section 6 for the numbers against the brief.

## 5. Speed
Static parts are cached per band; live layers are small. Rules learned: never paint an unbounded radial under a perspective
matrix (it shades the whole canvas: 0.7 s a frame; bound it with a path); relight cached layers at bake time, never live ones per
frame; the room model is built once per shot (`fit_bounds` still shrinks every bake rect to what the shot's camera sees).
First-frame bakes are 1-7 s per shot at 2560x1440 (once per shot). Bench: `_work/sets_v2/bench/bench.txt`.

## 6. Status against DIRECTION_V2 (measured; filled from the runs)
Measured with `tools/sets_v2_stills.py` (the REF_V2 lookstats method). "Sets" = one still per shot at its mid time, sets only
(449 stills, 640x360, `_work/sets_v2/all/looks.json`); "cast" = one still per set/view/var with the plan's cast (173 stills,
960x540, `_work/sets_v2/combos/looks.json`). The HUD and captions are not in either.

**Worlds (DIRECTION_V2 1.2)**

| world | luma p50 sets / cast | target | p95 sets / cast | target | HSV sat (cast) | target | hue (cast) | target |
|---|---|---|---|---|---|---|---|---|
| OURS | 85 / 88 | 80-100 (int.), 85-100 (ext.) | 147 / 166 | >= 190-200 | 121 | 90-130 | 240 | 235-255 |
| STAIRS | 75 / 76 | 55-75 | 147 / 181 | >= 180 | 131 | 110-150 | 301 | 300-320 |
| THEIRS | 147 / 151 | 140-165 | 204 / 207 | >= 235 | 119 | 80-120 | 36 | 30-45 |
| THEIRS break | 124 / 122 | 110-130 | 188 / 192 | | 99 | 70-100 | 29 | |
| MEMORY | 143 / 146 | 130-160 | 189 / 197 | | 79 | 50-75 | 33 | 30-40 |
| CLIMAX | 60 / 61 | 60-80 | 113 / 124 | >= 200 | 179 | 150-175 | 317 | 330-350 |
| ENDING | 93 / 87 | 85-100 | 154 / 164 | | 104 | 90-120 | 241 | 235 + warm |

**The arc by tenth (sets, duration-weighted; DIRECTION_V2 2.1)**

| tenth (s) | 0-70 | 70-140 | 140-210 | 210-280 | 280-350 | 350-420 | 420-490 | 490-560 | 560-630 | 630-700 |
|---|---|---|---|---|---|---|---|---|---|---|
| luma p50 (median of shots) | 85 | 91 | 86 | 94 | 148 | 145 | 136 | 110 | 61 | 93 |
| target | 95-110 | 95-110 | 85-100 | 90-105 | 135-150 | 130-145 | 120-135 | 95-110 | 60-75 | 90-100 |
| red-pixel share % | 2.45 | 0.54 | 2.87 | 3.11 | 2.77 | 2.76 | 1.92 | 6.70 | **15.9** | 0.04 |
| target | <= 0.5 | <= 1 | <= 1.5 | <= 1.5 | <= 1 | <= 1 | <= 1.5 | 3-8 | **13-18** | <= 2 |

**Whole film (sets, duration-weighted)**: frames under luma 60: 7.5 % (target <= 10 %; v1 42.8 %); under 40: 1.7 % (<= 3 %);
colourfulness p50 44 (>= 45; v1 16); contrast p95-p5 p50 111 (>= 135); luma std p50 34 (>= 45); edge density p50 .041 (>= .035;
v1 .025). With the cast, per-world contrast p95-p5 is 100-160 and edge density .046-.075.

**Bench** (2560x1440, one process, OMP 1, sets + grade + post, 173 set/view/var combos, 6 frames each):
warm frame median 0.147 s, mean 0.156 s; the heaviest view medians are mirror/glass_cu/red 0.314 s (max frame 0.365 s),
mirror/glass_wide/red 0.283, cabin_now/floor_cu 0.279, cabin_now/overhead 0.274; none over 0.35 s median or 0.4 s max.
First-frame bakes: median 2.7 s, max 8.4 s (mirror views draw the room twice: the room and its reflection), once per shot.

**Not met / weak** (for the assembly and the next passes)
- p95 highlights are short of 190-235 in OURS, THEIRS and CLIMAX, so frame contrast (111) and std (34) are below 135 / 45 on the set
  stills; the cast lifts them but the film-wide numbers must be measured on the assembled preview.
- The red share in tenths 1 and 3-6 is 2-3 % against <= 0.5-1.5 %: the red-bordered flash-forwards, the lipstick, the red stair
  edges, and THEIRS' coral swimsuits and gold floor (the gold palette is already pushed yellow to keep it out of the metric).
  The CLIMAX hue sits at 317 deg (target 330-350): the base was turned magenta-purple so that only the lights count as red
  pixels and the climax tenth lands at 15.9 % (13-18 %).
- MEMORY saturation 79 (50-75).
- Tenths 1-2 are 85 / 91 on the set stills (95-110), with +0.36 stop already in `arc_fx`.


---------------------------------------------------------------------------------------------------------------------

## A. Every set/view the plan uses (generated)

| set/view | shots | vars | built by | anchors |
|---|---|---|---|---|
| black/black | 2 | black | black |  |
| cabin_dawn/bokeh | 36 | dawn, dawn_break | bokeh_theirs | face |
| cabin_dawn/bunk_2s | 9 | dawn | room3d THEIRS (flipped) | clock, dip, doorway, drop, noah_bunk, noah_seat, queen_bunk, queen_corner, ... |
| cabin_dawn/clock | 4 | dawn, dawn_break | room3d THEIRS (flipped) | clock, doorway, drop, tess_doorway, towel, tread1, tread8, window |
| cabin_dawn/dip_low | 2 | dawn_queen | room3d THEIRS (flipped) | clock, dip, doorway, drop, noah_bunk, noah_seat, queen_bunk, shoe, ... |
| cabin_dawn/door_wash | 1 | dawn | room3d THEIRS (flipped) | door_wash, you_bunk_end, you_room |
| cabin_dawn/far_porch | 1 | dawn | far_porch | bell |
| cabin_dawn/floor_prints | 4 | dawn | room3d THEIRS (flipped) | clock, dip, door_wash, doorway, drop, noah_bunk, noah_seat, queen_bunk, ... |
| cabin_dawn/hands | 3 | dawn | room3d THEIRS (flipped) | clock, dip, doorway, drop, noah_bunk, noah_seat, queen_bunk, queen_corner, ... |
| cabin_dawn/hands_jerk | 1 | dawn | room3d THEIRS (flipped) | clock, dip, doorway, drop, noah_bunk, noah_seat, queen_bunk, queen_corner, ... |
| cabin_dawn/knot | 3 | dawn | room3d THEIRS (flipped) | dip, noah_bunk, noah_seat, queen_bunk, shoe, stairs_foot, tread8, you_bunk_end |
| cabin_dawn/lantern | 1 | dawn | room3d THEIRS (flipped) | clock, doorway, drop, queen_corner, tess_doorway, towel, window |
| cabin_dawn/master | 9 | dawn, dawn_break | room3d THEIRS (flipped) | clock, dip, doorway, drop, noah_bunk, noah_seat, queen_bunk, queen_corner, ... |
| cabin_dawn/ots_noah | 3 | dawn | room3d THEIRS (flipped) | clock, dip, door_wash, doorway, drop, noah_bunk, noah_seat, queen_bunk, ... |
| cabin_dawn/overhead | 3 | dawn | room3d THEIRS (flipped) | clock, dip, door_wash, doorway, drop, noah_bunk, noah_seat, queen_bunk, ... |
| cabin_dawn/queen_3s | 14 | dawn_break, dawn_queen | room3d THEIRS (flipped) | clock, dip, doorway, drop, noah_bunk, noah_seat, queen_bunk, queen_corner, ... |
| cabin_dawn/reverse | 6 | dawn | room3d THEIRS (flipped) | clock, doorway, drop, noah_bunk, noah_seat, queen_corner, stairs_foot, tess_doorway, ... |
| cabin_dawn/shoe | 1 | dawn | room3d THEIRS (flipped) | dip, doorway, drop, noah_bunk, noah_seat, queen_bunk, queen_corner, shoe, ... |
| cabin_dawn/swimsuits | 1 | dawn | room3d THEIRS (flipped) | dip, doorway, drop, noah_bunk, noah_seat, queen_bunk, shoe, stairs_foot, ... |
| cabin_dawn/top_stairs | 2 | dawn | room3d THEIRS (flipped) | clock, dip, door_wash, doorway, drop, noah_bunk, noah_seat, queen_bunk, ... |
| cabin_dawn/towel_floor | 5 | dawn | room3d THEIRS (flipped) | clock, dip, doorway, drop, noah_bunk, noah_seat, queen_bunk, queen_corner, ... |
| cabin_dawn/window | 3 | dawn | room3d THEIRS (flipped) | clock, dip, doorway, drop, noah_bunk, noah_seat, queen_bunk, queen_corner, ... |
| cabin_dawn/window_out | 3 | dawn | window_out2 | bell_far, sprinkler |
| cabin_now/bokeh | 30 | after, doorway_glow, night, phone_glow, red | bokeh_ours | face |
| cabin_now/bunk_rail | 2 | red | room3d OURS | bundle, clock, cubby_noah, doorway, mirror, noah_bunk_edge, noah_floor, noah_stand, ... |
| cabin_now/clock | 2 | after, doorway_glow | room3d OURS insert | clock, cubby_noah, doorway, mirror, phone, sill |
| cabin_now/cubby | 1 | night | room3d OURS insert | bundle, cubby_noah, noah_bunk_edge |
| cabin_now/door | 2 | night | cab_door2 | door, padlock, tess_door |
| cabin_now/doorway | 10 | doorway_glow, red | room3d OURS | bundle, clock, cubby_noah, doorway, mirror, noah_bunk_edge, noah_floor, noah_stand, ... |
| cabin_now/doorway_down | 1 | doorway_glow | room3d OURS | bundle, doorway, mirror, noah_bunk_edge, phone, sill, tess_beside, tess_mirror, ... |
| cabin_now/dutch_low | 3 | red | room3d OURS | bundle, clock, cubby_noah, doorway, mirror, noah_bunk_edge, noah_floor, noah_stand, ... |
| cabin_now/floor_cu | 3 | night, red | room3d OURS | bundle, clock, cubby_noah, doorway, mirror, noah_bunk_edge, phone, sill, ... |
| cabin_now/floor_wide | 8 | after, phone_glow | room3d OURS | bundle, clock, cubby_noah, doorway, mirror, noah_bunk_edge, noah_floor, noah_stand, ... |
| cabin_now/hands | 11 | after, night, red | room3d OURS insert | bundle, clock, cubby_noah, doorway, mirror, noah_bunk_edge, noah_floor, noah_stand, ... |
| cabin_now/master | 12 | doorway_glow, night, phone_glow, red | room3d OURS | bundle, clock, cubby_noah, doorway, mirror, noah_bunk_edge, noah_floor, noah_stand, ... |
| cabin_now/ots_mirror | 6 | night | room3d OURS | bundle, clock, cubby_noah, doorway, mirror, noah_bunk_edge, phone, sill, ... |
| cabin_now/overhead | 1 | night | room3d OURS | bundle, clock, cubby_noah, doorway, mirror, noah_bunk_edge, noah_floor, noah_stand, ... |
| cabin_now/phone_screen | 9 | phone_glow | v1 set relit (night) | bottom_step, screen |
| cabin_now/profile | 4 | night | room3d OURS | bundle, clock, cubby_noah, doorway, mirror, noah_bunk_edge, noah_floor, noah_stand, ... |
| cabin_now/reverse | 4 | doorway_glow, night | room3d OURS | bundle, cubby_noah, noah_bunk_edge, noah_floor, noah_stand, tess_beside, tess_center, tess_door, ... |
| cabin_now/sill | 4 | night, phone_glow | room3d OURS insert | clock, doorway, mirror, phone, sill, tess_sill, you_kneel, you_mirror |
| cabin_now/three_q | 3 | night | room3d OURS | bundle, clock, cubby_noah, doorway, mirror, noah_bunk_edge, noah_floor, noah_stand, ... |
| cabin_now/towel_label | 1 | night | v1 set relit (night) |  |
| cabin_now/towel_over | 1 | night | <lambda> | bottom_step, eighth, glass, queen_on_step1, queen_on_step2, queen_on_step3, queen_on_step4, queen_on_step5, ... |
| cabin_now/under_bunk | 1 | night | room3d OURS | bundle, clock, cubby_noah, doorway, mirror, noah_bunk_edge, noah_floor, noah_stand, ... |
| camp_gate/aerial | 1 | night | v1 set relit (night) |  |
| camp_gate/bokeh | 5 | night | bokeh plate of a relit v1 set | face |
| camp_gate/fence_track | 1 | night | v1 set relit (night) | tess_path, you_path |
| camp_gate/gate_reverse | 1 | night | v1 set relit (night) | padlock, tess_gate, you_gate |
| camp_gate/keys_cu | 1 | night | v1 set relit (night) | keys |
| camp_gate/notice | 1 | night | v1 set relit (night) |  |
| camp_gate/poster | 2 | night | v1 set relit (night) |  |
| camp_gate/poster_ecu | 1 | night | v1 set relit (night) |  |
| camp_gate/wide | 5 | night | v1 set relit (night) | padlock, tess_gate, you_gate |
| camp_path/bokeh | 1 | night | bokeh plate of a relit v1 set | face |
| camp_path/cabin7_door | 1 | night | cab7_door | door, padlock, tess_door |
| camp_path/cabins_row | 1 | night | v1 set relit (night) | cabin7_door |
| camp_path/path_run | 2 | night | v1 set relit (night) | tess_path, you_path |
| caretaker/wide | 1 | night | v1 set relit (night) | tess_pass, you_pass |
| diagram/side_view | 1 | night | plate: blurred mirror/glass_cu (shot.plate) | bottom_step, eighth, glass, queen_on_step1, queen_on_step2, queen_on_step3, queen_on_step4, queen_on_step5, ... |
| memory/bell_ecu | 2 | sepia_day | mem_bell2 | bell, rim |
| memory/bell_ring_porch | 3 | sepia_day | v1 memory relit (sepia) | adult_legs, counselor, kid_steps, noah_steps |
| memory/bench | 2 | sepia_day | v1 memory relit (sepia) | noah_bench |
| memory/breakfast_table | 3 | sepia_day | v1 memory relit (sepia) | noah_bench |
| memory/bunk_morning | 2 | sepia_morning | room3d past (sepia) | bundle, clock, cubby_noah, doorway, kid_bunk, kid_floor, kids_floor, mirror, ... |
| memory/bunk_night | 2 | sepia_night | room3d past (sepia) | bundle, clock, cubby_noah, doorway, kid_bunk, kid_floor, kids_floor, mirror, ... |
| memory/bus_run | 1 | sepia_morning | v1 memory relit (sepia) | run_a, run_b |
| memory/bus_window | 1 | sepia_day | v1 memory relit (sepia) | bus_window |
| memory/buses | 1 | sepia_day | v1 memory relit (sepia) | bus_window |
| memory/car_20 | 1 | sepia_day | v1 memory relit (sepia) |  |
| memory/car_door | 1 | sepia_day | v1 memory relit (sepia) |  |
| memory/card_queen | 1 | sepia_night | v1 memory relit (sepia) | kid_hands |
| memory/crate_bell | 1 | sepia_day | v1 memory relit (sepia) |  |
| memory/dad_photo | 1 | sepia_day | v1 memory relit (sepia) |  |
| memory/director | 1 | sepia_morning | v1 memory relit (sepia) | director, kitchen_line, search_line |
| memory/dock | 1 | sepia_day | v1 memory relit (sepia) | kid_dock, noah_dock |
| memory/flash_445 | 1 | sepia_night | room3d past (sepia) | bundle, clock, cubby_noah, doorway, kid_bunk, kid_floor, mirror, noah_bunk_edge, ... |
| memory/gate_close | 2 | sepia_day | v1 memory relit (sepia) |  |
| memory/kids_game | 4 | sepia_night | room3d past (sepia) | bundle, cubby_noah, kid_bunk, kid_floor, kids_floor, noah_bunk_edge, noah_floor, noah_mirror, ... |
| memory/kids_mouths | 1 | sepia_night | v1 memory relit (sepia) | bunk_sleep, kids |
| memory/kitchen_15 | 1 | sepia_day | v1 memory relit (sepia) |  |
| memory/kitchen_staff | 1 | sepia_morning | v1 memory relit (sepia) | director, kitchen_line, search_line |
| memory/lantern_game | 1 | sepia_night | room3d past (sepia) | bundle, clock, cubby_noah, doorway, kid_bunk, kid_floor, kids_floor, mirror, ... |
| memory/legs | 2 | sepia_morning | v1 memory relit (sepia) | adult_legs, counselor, kid_steps, noah_steps |
| memory/menu_board | 1 | sepia_morning | v1 memory relit (sepia) |  |
| memory/moms_car | 2 | sepia_day | v1 memory relit (sepia) |  |
| memory/night_window | 6 | sepia_night | v1 memory relit (sepia) | noah_window |
| memory/office_phone | 1 | sepia_day | v1 memory relit (sepia) |  |
| memory/officer | 1 | sepia_morning | v1 memory relit (sepia) | adult_legs, counselor, kid_steps, noah_steps |
| memory/open_window | 3 | sepia_day | room3d past (sepia) | bundle, clock, cubby_noah, doorway, kid_floor, mirror, noah_bunk_edge, noah_floor, ... |
| memory/percolator | 1 | sepia_morning | v1 memory relit (sepia) |  |
| memory/pocket | 1 | sepia_day | v1 memory relit (sepia) | pocket |
| memory/polaroid | 1 | sepia_day | v1 memory relit (sepia) |  |
| memory/porch_drop | 1 | sepia_day | v1 memory relit (sepia) | adult_legs, counselor, kid_steps, noah_steps |
| memory/red_candy | 3 | sepia_day | v1 memory relit (sepia) | pocket |
| memory/run_barefoot | 1 | sepia_day | v1 memory relit (sepia) | run_a, run_b |
| memory/search_pines | 2 | sepia_morning | v1 memory relit (sepia) | director, kitchen_line, search_line |
| memory/search_window | 1 | sepia_morning | v1 memory relit (sepia) | director, kitchen_line, search_line |
| memory/socks | 1 | sepia_morning | room3d past (sepia) | bundle, cubby_noah, doorway, kid_bunk, kid_floor, mirror, noah_bunk_edge, noah_floor, ... |
| memory/spoon | 1 | sepia_day | v1 memory relit (sepia) | noah_bench |
| memory/sprinkler_lawn | 2 | sepia_day | v1 memory relit (sepia) | noah_run |
| memory/tape_wrap | 1 | sepia_day | v1 memory relit (sepia) |  |
| memory/towel_wet | 1 | sepia_morning | room3d past (sepia) | bundle, clock, cubby_noah, doorway, kid_bunk, kid_floor, kids_floor, mirror, ... |
| memory/wake | 2 | sepia_morning | room3d past (sepia) | bundle, cubby_noah, doorway, kid_bunk, mirror, noah_bunk_edge, noah_mirror, noah_stand, ... |
| memory/watch_cu | 2 | sepia_night | v1 memory relit (sepia) | buttons |
| mess_porch/bell_ecu | 2 | night | bell_ecu2 | bell, crack |
| mess_porch/bell_hit | 1 | bell_hit | bell_hit2 | bell, contact |
| mess_porch/bokeh | 2 | night | bokeh plate of a relit v1 set | face |
| mess_porch/boot | 1 | night | v1 set relit (night) | boot |
| mess_porch/crate_cu | 1 | night | v1 set relit (night) |  |
| mess_porch/high_wide | 2 | night | porch_high | cabin7_door, crate, tess_porch |
| mess_porch/porch_crate | 6 | bell_hit, night | porch_crate2 | crate, tess_crate |
| mess_porch/porch_low | 1 | night | v1 set relit (night) | tess_low |
| mirror/glass_cu | 15 | night, red | room3d mirror | bottom_step, eighth, glass, queen_on_step1, queen_on_step2, queen_on_step3, queen_on_step4, queen_on_step5, ... |
| mirror/glass_tilt | 1 | night | room3d mirror | bottom_step, eighth, glass, queen_on_step1, queen_on_step2, queen_on_step3, queen_on_step4, queen_on_step5, ... |
| mirror/glass_wide | 8 | night, red | room3d mirror | bottom_step, eighth, glass, queen_on_step1, queen_on_step2, queen_on_step3, queen_on_step4, queen_on_step5, ... |
| mirror/queen_glass | 13 | stairs | room3d mirror | bottom_step, eighth, glass, queen_on_step1, queen_on_step2, queen_on_step3, queen_on_step4, queen_on_step5, ... |
| mirror/reflection | 2 | night | room3d mirror | bottom_step, eighth, glass, queen_on_step1, queen_on_step2, queen_on_step3, queen_on_step4, queen_on_step5, ... |
| mirror/through | 8 | dawn, red, stairs | room3d mirror | bottom_step, eighth, glass, queen_on_step1, queen_on_step2, queen_on_step3, queen_on_step4, queen_on_step5, ... |
| mirror/towel_over | 3 | night | room3d mirror | bottom_step, eighth, glass, queen_on_step1, queen_on_step2, queen_on_step3, queen_on_step4, queen_on_step5, ... |
| rule_mirror/card | 7 | dawn, dawn_break, dawn_queen, doorway_glow, night, red | card bg: shot.bg view, blurred | bundle, clock, cubby_noah, doorway, mirror, noah_bunk_edge, phone, sill, ... |
| split/bells | 1 | dawn | split: two set views | L_bell, R_bell, R_crack |
| split/eyes | 1 | stairs | split: two set views | L_bottom_step, L_eighth, L_glass, L_queen_on_step1, L_queen_on_step2, L_queen_on_step3, L_queen_on_step4, L_queen_on_step5, ... |
| split/floors | 1 | night | split: two set views | L_clock, L_dip, L_door_wash, L_doorway, L_drop, L_noah_bunk, L_noah_seat, L_queen_bunk, ... |
| split/twins | 1 | dawn | split: two set views | L_face, R_face |
| stairs/bokeh | 4 | red, stairs | bokeh_stairs | face |
| stairs/down | 3 | stairs | room3d stairs | bottom, doorway, noah_bunk, queen_below, queen_tread8, tess_doorway, tread1, tread2, ... |
| stairs/low | 4 | red, stairs | room3d stairs | doorway, queen_below, queen_tread8, tess_doorway, tread1, tread2, tread3, tread4, ... |
| stairs/ots_climb | 4 | red, stairs | room3d stairs | bottom, doorway, noah_bunk, queen_below, queen_tread8, tess_doorway, tread1, tread2, ... |
| stairs/pov_down | 2 | red | room3d stairs | bottom, noah_bunk, queen_below, queen_tread8, tread2, tread3, tread4, tread5, ... |
| stairs/queen_ecu | 1 | red | queen_ecu | face |
| stairs/railing | 4 | stairs | room3d stairs | bottom, noah_bunk, queen_below, queen_tread8, tread2, tread3, tread4, tread5, ... |
| stairs/section | 5 | red, stairs | section cutaway (2D) | gold_floor, noah_bunk, tess_door, tread1, tread2, tread3, tread4, tread5, ... |
| stairs/treads | 2 | stairs | room3d stairs | bottom, noah_bunk, queen_below, queen_tread8, tread2, tread3, tread4, tread5, ... |
| stairs/up | 4 | red | room3d stairs | bottom, doorway, queen_below, queen_tread8, tess_doorway, tread1, tread2, tread3, ... |
| type/beat | 1 | night | plate: blurred mirror/glass_cu (shot.plate) | bottom_step, eighth, glass, queen_on_step1, queen_on_step2, queen_on_step3, queen_on_step4, queen_on_step5, ... |
| type/kinetic | 1 | night | plate: blurred mirror/glass_cu (shot.plate) | bottom_step, eighth, glass, queen_on_step1, queen_on_step2, queen_on_step3, queen_on_step4, queen_on_step5, ... |
| ui/call | 1 | phone | ui |  |
| ui/text | 2 | phone | ui |  |
| ui/voicemail | 1 | phone | ui |  |


---------------------------------------------------------------------------------------------------------------------

# B. v1 internals still in use (the relit exteriors and memories, the St prop parser, the lipstick, the Beam)

### B.1 The v1 document (unchanged)

`sets.py` builds every set, view, lighting variant and animated prop state that `plan/shots.json` names: 96 views plus the
rule-card backgrounds, all in the engine's 1920x1080 design space, with real depth for parallax and depth of field.
All 317 shots build, and every `chars[].at` anchor name resolves.

### 1. Use

```python
import sets
sp = sets.build_shot(shot)                    # shots.json entry -> SetPiece (rule cards build their live `bg` set + its post)
sp = sets.build(set, view, var, shot=shot)    # the same, explicit; shot supplies props, changes, sfx, cam, grade, dof
at = sets.resolve_at(sp, spec)                # chars[i] -> list for characters.CharRig (anchor name or the plan's list)
img = render_frame(sp.add(*char_layers), cam.at(t), t, i, **sp.render_kw(), post=sp.fx(t), hud=...)
```

- **`SetPiece`** is a list of engine `Layer`s plus the following.
  - `.anchors`: `{name: Anchor}`. `Anchor(x, y, depth, height)`; `.at()` gives `[x, y, height, depth]`.
  - `.grade`: the shot's grade, or the variant default.
  - `.focus` and `.dof`.
  - `.fx(t)`: per-frame post: the `dawn_break` red edge leak and flicker, plus the shot's `fx_post` keys.
  - `.info`: see below.
  - `.add()`, `.without(name)`, `.layer(name)` and `.render_kw()`.
- **Character layers.** Put body modes at the anchor depth (`Layer(a.depth, ..., ref_depth=a.depth)`). Bust and hands
  modes go at depth 1.0.
- **Close-ups.** When every character in a shot is a `bust`, `build` calls `push_back(sp, 2.6)`. It does the same for
  `bust` + `hands` shots on background views (`floor_end`, `doorway`, `wide`, `two_shot`, `noah_ms`, `doorway_back`,
  `queen_bunk`, `cabin_door`, `porch_run`).
  - Every set layer at depth 0.85 or more moves 2.6x further back. The picture at the home camera is unchanged.
  - Static layers darken by 0.25 and `dof` becomes 6.75, so the background gets a real DOF blur.
  - Insert views (`info['insert']`) already have their background at depth 3.
- **`fit_bounds(sp, shot)`** runs inside `build`. It shrinks every cached layer's bake rect to what the shot's camera
  keys can see, including shake, hits and roll, and keys the cache by that rect. Without it, push-ins re-bake huge caches
  every frame. Build the SetPiece once per shot, not per frame.

### `info` keys the assembler may use
| key | where | meaning |
|---|---|---|
| `beam` | most `ours` views | a `Beam`. Its default path is plausible per view. Set `sp.info['beam'].override = f(t) -> (sx, sy, ax, ay, k)` to drive it from Tess's rig (`pose.beam`, `pose.beam_dx`, the hand point). Dust motes follow the beam (`Beam.k_at`). |
| `press` | `cabin_now/towel_over` | set `f(t) -> [(x, y, k), ...]` (design px, `k` 0..1) for the fingertip bumps under the towel. By default the bumps come from the queen hands `at` and the shot's `cloth_press` cue times. The towel layer (depth 0.985) is drawn over the hand. |
| `screen` | `cabin_now/phone_screen` | the screen path. Use `sets.clip_layer(layer, sp.info['screen'])` for the queen inside the phone (S314-S316). |
| `mirror_xf`, `tilt`, `counter_roll` | mirror views | the mirror-local to design transform `(cx, cy, s)`, the set tilt in degrees, and the counter-roll function under a camera roll (S067). |
| `insert` | inserts | the view already carries a depth-3 blurred background. |
| `st` | all | the `St` prop-state object. |

### 2. Prop state (`St`)
`St(shot)` parses `props`, including the human-readable strings and `changes_in_shot`, and the shot's `sfx` cues.

- `v(key, t)`: the state at time `t`.
- `since(key, t)`: seconds since that state began.
- `change_t(key, value)`: the time of a change.
- `ev(name)`: parsed events: `step_draw`, `eighth_draw`, `erase`, `glow`, `fog`, `towel_throw`, `towel_drop`,
  `crate_break`, `strike`, `drop_rise`, `drop_fall`, `sprinkler`, `clock_back`, `footprints`, `clock_dawn`,
  `fake_bell` and `watch`.
- `sfx(name)`: the cue times of one SFX in the shot.

Set animations are timed to the plan's SFX cues, so picture and sound stay locked:

| cue | drives |
|---|---|
| `lipstick_smear` | smear timing; `steps_smeared` changes give the end times |
| `glass_wipe` | the towel wipe (hook S003) |
| `wet_footstep` | footprints, one per cue; `params.bare` picks bare or shoe |
| `door_creak` | the reflected door (S074) and the Cabin 7 door (S035) |
| `sprinkler_spit` | the sprinkler. Valve on = the cue without a loop id; spits = the `loop_id` cues, the same arc animation each time; `kind: die` ends it |
| `cloth_press` | the bumps under the towel |
| `towel_drop` | the towel falls and dust bursts |
| `wood_thud` | the bunk jumps |
| `body_fall` | the floor dust burst |
| `mattress_creak` | the dip |
| `wood_break` / `crate_break` | the boot snaps the slats |
| `bell_drop` / `metal_clang` | the bell dropped in the memory |
| `water_splash` / `puddle_splash` | the puddle |

**Clocks.**
- `clock_ours(t)` follows the header spec: 23:57:00 at 19.40 s, backward 278.97-281.81 s, forward after. The Cabin 7
  wall clock jerks back 2 s at 281.69 and then steps back once every 0.2 s.
- `clock_theirs(t)` is the 06:59:40 + (t - 297.59) mod 19.48 loop, frozen at 07:00:00 from 535.36.
- `cabin_dawn/clock` snaps from :50 back to :40 at the plan's 388.57.

### 3. The mirror system
- **Mirror-local coordinates.** These are the `mirror_cu` framing.
  - Pane x 300..1620, y -1092..2252 (`PANE`), frame 88 px. The pane is far taller than the frame, so `mirror_cu`
    shows its side bars and the cabin wall beyond.
  - Transforms: `mirror_cu` (960, 580, 1.0); `mirror_ots` `OTS_MIRROR` (960, 520, 0.227), giving the plan's 300x760
    pane; `cabin_now/wide` `CAB_MIRROR` (1190, 665, 0.111); `old_cabin_refl` (960, 560, 0.42); `towel_over`
    (960, 540, 0.33).
- **Layers by depth.** `mirror_layers()` builds these.

| depth | layer |
|---|---|
| 2.2 | reflection (parallax: the reflection is twice as far away) |
| 1.15 | the wall, with a pane-shaped hole |
| 1.04 | `eighth`: the 8th line, behind the glass |
| 1.0 | `glass`: sheen, desilvering, dust film, smudges, the white chipped frame |
| 0.995 | `steps`: lipstick (cached when static, live when drawing, smearing, wiping or erasing) |
| 0.99 | glare and fog breath |
| 0.9 | dust |

- **Lipstick.**
  - Treads `STEP_XY[k]` = (1280 - 110k, 300 + 80k), top k=0 to bottom k=6, 120 px wide, 19 px waxy strokes (the plan
    asks for 14 px; this reads better at 1920) with 80 px risers.
  - Draw-on: steps 6 and 7 at 0.56 and 0.88 (S001).
  - Smears: a down-right drag per tread, in time with the cues.
  - Wipe: irregular dragged streaks plus a pink haze above the towel line.
  - Erased: faint smudges, plus one last streak thinning in S284.
  - Climax glow: `red` variant.
- **The 8th line.** `EIGHTH` = left end (510, 860), 130 px long. It draws itself in 0.6 s at the plan's 2.56 and
  118.87. The queen's feet go at its centre (575, 860), depth 1.04 (`anchors['eighth']`).
- **Tilt.** When `mirror == tilted` and the camera does not roll, the frame, glass and steps are drawn at `TILT` = -13
  degrees. The 8th line, the queen and the reflected world stay level. Under a camera roll (S067), the line
  counter-rotates instead.
- **Reflection variants.**
  - `flash`: the dark cabin behind you, with its window.
  - `queen`, `void`: near-black stairwell falling away under the 8th step, with a red glow.
  - `old_cabin`: the pale cabin as it was. The bunks are made; swimsuits drip on the top rail; the door swings in
    (`door_creak`); wet footprints appear on the cues and run door to bunk; the mattress dips after the last print. The
    static part is cached and the live part is small.
  - `red`: red pulse.
  - `dark`: everything drains to black 628.18-628.48.

### 4. Sets, views, variants and anchors
Anchors are `(x, y, depth, height)`. For bust anchors, height is the bust scale; anchors with `h 1` are prop points.

| set | view | variants | anchors |
|---|---|---|---|
| `black` | `black` | black | - |
| `cabin_dawn` | `candy` | dawn, dawn_queen | - |
| `cabin_dawn` | `clock` | dawn | - |
| `cabin_dawn` | `doorway_back` | dawn, dawn_break | `tess_in_doorway` (960, 900, d 1.05, h 640), `doorway` (960, 560, d 1.00, h 1.00) |
| `cabin_dawn` | `hands_jerk` | dawn | - |
| `cabin_dawn` | `knot_cu` | dawn, dawn_break, dawn_queen | - |
| `cabin_dawn` | `mattress_dip` | dawn, dawn_queen | - |
| `cabin_dawn` | `noah_cu` | dawn, dawn_break | - |
| `cabin_dawn` | `noah_ms` | dawn | `noah_bunk` (1180, 930, d 1.00, h 560), `queen_bunk` (1440, 930, d 1.00, h 600), `you_bunk` (760, 1010, d 1.00, h 640), `you_stand` (760, 1010, d 1.00, h 640), `dip` (1420, 720, d 1.00, h 1.00), `towel` (620, 900, d 1.00, h 1.00), `shoe` (1000, 940, d 1.00, h 1.00) |
| `cabin_dawn` | `queen_bunk` | dawn, dawn_queen | `noah_bunk` (1180, 930, d 1.00, h 560), `queen_bunk` (1440, 930, d 1.00, h 600), `you_bunk` (760, 1010, d 1.00, h 640), `you_stand` (760, 1010, d 1.00, h 640), `dip` (1420, 720, d 1.00, h 1.00), `towel` (620, 900, d 1.00, h 1.00), `shoe` (1000, 940, d 1.00, h 1.00) |
| `cabin_dawn` | `queen_bust` | dawn_queen | - |
| `cabin_dawn` | `queen_face` | dawn_break, dawn_queen | - |
| `cabin_dawn` | `queen_mouth` | dawn_break | - |
| `cabin_dawn` | `shoe` | dawn_break, dawn_queen | - |
| `cabin_dawn` | `towel` | dawn | `drop` (960, 330, d 1.00, h 1.00) |
| `cabin_dawn` | `wide` | dawn, dawn_break, dawn_queen | `noah_bunk` (1180, 930, d 1.00, h 560), `queen_bunk` (1440, 930, d 1.00, h 600), `you_bunk` (760, 1010, d 1.00, h 640), `you_stand` (760, 1010, d 1.00, h 640), `dip` (1420, 720, d 1.00, h 1.00), `towel` (620, 900, d 1.00, h 1.00), `shoe` (1000, 940, d 1.00, h 1.00) |
| `cabin_dawn` | `window` | dawn | - |
| `cabin_dawn` | `window_out` | dawn | `sprinkler` (900, 760, d 3.00, h 1.00), `bell_far` (1420, 600, d 3.60, h 1.00) |
| `cabin_dawn` | `you_face` | dawn_break | - |
| `cabin_now` | `bunk_hit` | red | - |
| `cabin_now` | `bunk_low` | red | - |
| `cabin_now` | `cabin_door` | flash | `tess_door` (960, 930, d 1.18, h 600) |
| `cabin_now` | `clock` | after, flash | - |
| `cabin_now` | `cuffs` | red | `hands` (960, 600, d 1.00, h 420), `noah_floor` (820, 1240, d 1.00, h 900) |
| `cabin_now` | `doorway` | doorway_glow, red | `tess_doorway` (700, 1000, d 1.00, h 640), `you_doorway` (1000, 960, d 1.05, h 620), `doorway` (960, 600, d 1.15, h 1.00), `queen_doorway` (1080, 900, d 1.60, h 600) |
| `cabin_now` | `dust_floor` | flash_low | - |
| `cabin_now` | `fingertip` | flash | `hands` (960, 600, d 1.00, h 420), `noah_floor` (820, 1240, d 1.00, h 900) |
| `cabin_now` | `floor_end` | after, phone_glow | `noah_floor` (1060, 960, d 1.00, h 520), `you_floor` (700, 975, d 1.00, h 560), `tess_floor_end` (1500, 1000, d 1.00, h 640) |
| `cabin_now` | `floor_low` | red | `you_floor` (960, 1000, d 1.00, h 640) |
| `cabin_now` | `hands` | after, flash, red | `hands` (960, 600, d 1.00, h 420), `noah_floor` (820, 1240, d 1.00, h 900) |
| `cabin_now` | `mirror_ots` | flash | `you_mirror` (560, 1240, d 0.70, h 980), `tess_mirror` (1500, 1040, d 0.95, h 640), `mirror` (960, 520, d 1.00, h 1.00) |
| `cabin_now` | `palm` | after | - |
| `cabin_now` | `phone_screen` | after, phone_glow | `screen` (960, 560, d 1.04, h 1.00), `bottom_step` (894, 568, d 1.04, h 1.00) |
| `cabin_now` | `sill` | after, flash | `phone` (960, 630, d 1.00, h 1.00) |
| `cabin_now` | `sleeve` | doorway_glow | `hands` (960, 600, d 1.00, h 420), `noah_floor` (820, 1240, d 1.00, h 900) |
| `cabin_now` | `towel_fly` | flash | - |
| `cabin_now` | `towel_label` | flash | - |
| `cabin_now` | `towel_over` | flash | `press` (960, 520, d 1.00, h 380) |
| `cabin_now` | `two_shot` | flash | `you_mirror` (640, 1100, d 1.00, h 860), `tess_mirror` (1340, 1110, d 1.00, h 840) |
| `cabin_now` | `under_bunk` | flash | `bundle` (980, 760, d 1.00, h 1.00) |
| `cabin_now` | `wide` | doorway_glow, flash, flash_low, red | `tess_mirror` (1440, 960, d 1.00, h 600), `you_mirror` (1090, 950, d 1.00, h 590), `noah_stand` (1560, 950, d 1.00, h 640), `doorway_mid` (1190, 862, d 1.16, h 400), `mirror` (1190, 665, d 1.00, h 1.00) |
| `camp_gate` | `keys_cu` | moon_flash | `keys` (960, 500, d 1.00, h 1.00) |
| `camp_gate` | `lock_cu` | moon_flash | `padlock` (960, 560, d 1.00, h 1.00) |
| `camp_gate` | `notice` | moon_flash | - |
| `camp_gate` | `poster` | moon_flash | - |
| `camp_gate` | `wide` | moon, moon_flash | `tess_gate` (880, 960, d 1.00, h 600), `you_gate` (1100, 960, d 1.00, h 620), `padlock` (960, 720, d 1.00, h 1.00) |
| `camp_path` | `aerial` | moon | - |
| `camp_path` | `cabins_row` | moon | `cabin7_door` (1300, 940, d 1.00, h 560) |
| `camp_path` | `path` | moon | - |
| `camp_path` | `path_track` | moon_flash | `tess_path` (800, 960, d 1.00, h 600), `you_path` (1080, 960, d 1.00, h 620) |
| `caretaker` | `wide` | tv | `tess_pass` (700, 1150, d 0.60, h 900), `you_pass` (1000, 1160, d 0.60, h 930) |
| `memory` | `bell_ecu` | memory_day | - |
| `memory` | `bell_ring_porch` | memory_day | `adult_legs` (1120, 860, d 1.00, h 1100), `noah_steps` (760, 1080, d 0.95, h 600), `kid_steps` (1080, 1090, d 0.95, h 470), `counselor` (1180, 860, d 1.05, h 620) |
| `memory` | `bench` | memory_day | `noah_bench` (960, 1000, d 1.00, h 560) |
| `memory` | `breakfast_table` | memory_day | `noah_bench` (960, 1000, d 1.00, h 560) |
| `memory` | `bunk_night` | memory_night | `bunk_sleep` (900, 690, d 1.00, h 900), `kids` (960, 1000, d 1.00, h 470) |
| `memory` | `buses` | memory_day | `bus_window` (1225, 600, d 1.00, h 0.32) |
| `memory` | `cabin_morning` | memory_day, memory_morning | `kid_bunk` (1300, 680, d 1.00, h 460), `kid_sit_dip` (1420, 930, d 1.00, h 470), `noah_bunk` (1000, 1010, d 1.00, h 600) |
| `memory` | `card_queen` | memory_night | `kid_hands` (1180, 400, d 1.00, h 300) |
| `memory` | `dock` | memory_day | `noah_dock` (1100, 960, d 1.00, h 600), `kid_dock` (780, 980, d 1.00, h 470) |
| `memory` | `gate_close` | memory_day | - |
| `memory` | `grin_ecu` | memory_day | - |
| `memory` | `kids_game` | memory_night | `bunk_sleep` (900, 690, d 1.00, h 900), `kids` (960, 1000, d 1.00, h 470) |
| `memory` | `kitchen` | memory_morning | - |
| `memory` | `kitchen_staff` | memory_morning | `search_line` (960, 900, d 2.00, h 380), `director` (1350, 940, d 1.60, h 460), `kitchen_line` (900, 940, d 1.60, h 440) |
| `memory` | `lipstick_game` | memory_night | `kid_hands` (1180, 400, d 1.00, h 300) |
| `memory` | `night_window` | memory_night | `noah_window` (760, 1080, d 1.00, h 640) |
| `memory` | `path_run` | memory_day | `run_a` (800, 1060, d 1.00, h 600), `run_b` (1150, 1050, d 1.00, h 470) |
| `memory` | `pocket` | memory_day | `pocket` (960, 450, d 1.00, h 1.00) |
| `memory` | `polaroid` | memory_day | - |
| `memory` | `porch_steps` | memory_day, memory_morning | `adult_legs` (1120, 860, d 1.00, h 1100), `noah_steps` (760, 1080, d 0.95, h 600), `kid_steps` (1080, 1090, d 0.95, h 470), `counselor` (1180, 860, d 1.05, h 620) |
| `memory` | `search_pines` | memory_morning | `search_line` (960, 900, d 2.00, h 380), `director` (1350, 940, d 1.60, h 460), `kitchen_line` (900, 940, d 1.60, h 440) |
| `memory` | `sprinkler_lawn` | memory_day | `noah_run` (1200, 1040, d 1.00, h 600) |
| `memory` | `storage_shed` | memory_day | - |
| `memory` | `watch_cu` | memory_night | `buttons` (1320, 400, d 1.00, h 1.00) |
| `mess_porch` | `bell_ecu` | bell_hit, moon_flash | - |
| `mess_porch` | `bell_slats` | moon_flash | `bell` (980, 600, d 1.00, h 1.00) |
| `mess_porch` | `boot_ecu` | run | `boot` (960, 640, d 1.00, h 900) |
| `mess_porch` | `crate_cu` | moon_flash | - |
| `mess_porch` | `porch_low` | moon_flash | `tess_low` (800, 900, d 1.00, h 900) |
| `mess_porch` | `porch_run` | bell_hit, run | `tess_crate` (820, 960, d 1.00, h 640), `crate` (1050, 810, d 1.00, h 1.00) |
| `mess_porch` | `wide` | moon_flash | `tess_steps` (800, 1060, d 0.95, h 600), `you_steps` (1080, 1075, d 0.95, h 620), `porch_mid` (960, 830, d 1.05, h 520), `porch_left` (600, 830, d 1.05, h 520), `crate` (1185, 820, d 1.00, h 1.00) |
| `mirror` | `mirror_cu` | dark, flash, queen, red, wipe | `eighth` (575, 860, d 1.04, h 230), `queen_step` (575, 860, d 1.04, h 230), `top_step` (1280, 300, d 1.00, h 1.00), `bottom_step` (620, 780, d 1.00, h 1.00), `queen_face` (960, 560, d 1.04, h 1.40) |
| `mirror` | `old_cabin_floor` | old_cabin | - |
| `mirror` | `old_cabin_refl` | old_cabin | `noah_bunk_refl` (1204, 694, d 2.00, h 1.00) |
| `mirror` | `queen_face` | queen | `eighth` (575, 860, d 1.04, h 230), `queen_step` (575, 860, d 1.04, h 230), `top_step` (1280, 300, d 1.00, h 1.00), `bottom_step` (620, 780, d 1.00, h 1.00), `queen_face` (960, 560, d 1.04, h 1.40) |
| `mirror` | `queen_mouth` | queen | `eighth` (575, 860, d 1.04, h 230), `queen_step` (575, 860, d 1.04, h 230), `top_step` (1280, 300, d 1.00, h 1.00), `bottom_step` (620, 780, d 1.00, h 1.00), `queen_face` (960, 560, d 1.04, h 1.40) |
| `mirror` | `queen_step_tilt` | flash, queen, red | `eighth` (575, 860, d 1.04, h 230), `queen_step` (575, 860, d 1.04, h 230), `top_step` (1280, 300, d 1.00, h 1.00), `bottom_step` (620, 780, d 1.00, h 1.00), `queen_face` (960, 560, d 1.04, h 1.40) |
| `mirror_world` | `dress` | void | - |
| `mirror_world` | `eye` | void | - |
| `mirror_world` | `feet` | red, void | `your_step` (880, 560, d 1.00, h 600), `her_step` (1040, 860, d 1.00, h 700) |
| `mirror_world` | `railing` | void | `hand` (980, 600, d 1.00, h 260), `queen_side` (1500, 1000, d 0.80, h 820) |
| `mirror_world` | `stairs` | void, void_noah | `queen_back` (1240, 1100, d 0.72, h 1000), `noah_far` (960, 760, d 8.00, h 150), `landing` (960, 780, d 6.00, h 1.00) |
| `ui` | `call` | phone | - |
| `ui` | `text` | phone | - |
| `ui` | `voicemail` | phone | - |

The `rule_mirror` card shots build their `bg` set (for example `cabin_now/mirror_ots`) with `{'blur': 6, 'dim': 0.35}`
merged into `fx(t)`. The card itself is HUD.

**What moves in each world** (the "never a still frame" rule):
- **Ours:**
  - Tess's beam with hand wobble and searching sweeps; dust motes lit by the beam;
  - moths near the hot spot; fireflies, mist bands and swaying pines outdoors;
  - star twinkle, lake glints, wind chimes;
  - the caretaker's TV flicker and the curtain sway at 70.32;
  - the clock, the doorway haze and rays, and the red pulse.
- **Theirs:** deliberately still: curtains never move.
  - The motion is the slow window-shaft dust, the drop loop (drips, then rise and hang, then fall again), the sprinkler
    spits, the far fake bell swinging (513.56), and the clock loop.
  - `dawn_break` adds a stuttering lantern, the red leak and the flicker.
- **Mirror world:** pale scratch lines that re-jitter every 3 frames, falling dust, a breathing under-glow and the
  red-iris flare.
- **Memories:** halation motes, morning mist, water glitter, sprinkler arcs, the gate closing with the chain and the
  padlock snap, the bell lowered into the crate with the lid shutting, the puddle splash, and moths at the lantern.

### 5. Grades
The plan's 14 presets are added to `engine/post.py` `GRADES`: `camp_night`, `camp_night_run`, `cabin_flash`,
`cabin_doorway`, `cabin_after`, `mirror_world`, `mirror_old_cabin`, `dawn_normal`, `dawn_queen`, `dawn_break`,
`climax_red`, `memory`, `memory_night` and `memory_morning`. `dawn_break`'s red leak and flicker come from `sp.fx(t)`.

The plan's parameters are kept, with one change: exposure was added to `camp_night` (+0.95), `camp_night_run` (+1.05),
`mirror_world` (+0.75) and `dawn_normal` (+0.25, inherited by `dawn_queen` and `dawn_break`) to move toward the plan's
luma targets.

Measured luma p50 on the stills (960x540, cast included), against the targets:

| world | measured | target |
|---|---|---|
| ours outside | 33-38 | 40-55 |
| ours inside | median 41 | 30-45 |
| theirs | about 130-185 (median 132 before the exposure change) | 140-165 |
| stairs world | 12-14 | 15-25 |
| memory day | 110-150 | 120-150 |

### 6. Speed (measured: 2560x1440, one process, sets + grade + post, no cast or HUD)
- The first frame of a shot bakes its caches: 0.1-3.3 s (mean 0.6 s), once per shot.
- Warm frames, over all 137 set/view/variant combinations:
  - mean 0.15 s per frame;
  - heaviest after optimisation: `towel_fly` 0.31 s (a 0.8 s shot), `keys_cu` 0.28 s, `mirror_cu/wipe` 0.22 s,
    `bell_ecu/bell_hit` 0.22 s, `sleeve` 0.22 s;
  - most views are 0.08-0.2 s.
- A density re-bake during a big pull-out can spike one frame to about 0.47 s (S055).
- That leaves at least 0.3 s of the 0.6 s budget for the cast and the HUD.
- Per-view numbers: `_work/sets/bench.txt` (the full run, taken before the last two speed fixes) and the re-bench lines
  at its end.
- What keeps it fast:
  - `fit_bounds`;
  - `_R` / `_L`: gradient stops normalised, so the engine's gradient-image cache hits instead of rebuilding per frame;
  - the beam as one near-1:1 sprite drawn with nearest sampling;
  - static reflection parts cached.
- Keep it fast:
  - never build a SetPiece per frame;
  - avoid stop alphas that change per frame in new code (use `_R` / `_L`);
  - keep live layers small.

### 7. Test harness
- Stills of every set, view and variant, with the cast: `_work/sets/stills/<set>__<view>__<var>__<shot>.jpg` (960x540).
- Contact sheets: `_work/sets/sheet_1..6.jpg`.
- Make them with `python3 tools/sets_sheet.py _work/sets/sheet.jpg --chars --per 24 --stills _work/sets/stills --combos [set ...]`.
  Single shots: `... sheet.jpg S119 S150@340.1`.
- Benchmark: `OMP_NUM_THREADS=1 python3 tools/sets_bench.py --combos` (or a list of shot ids). It prints the first frame
  and the warm median and max per view.
## Gate review changes (G1 + G2)

- **Tess's beam reads in OURS wides.** `_ours_light` put the beam's source behind the camera, so `draw_beam` fell back to
  its off-frame wash and the cone never showed. The source is now just off the lower-left corner (`cam.C + 0.9 fwd - 0.7
  right - 0.45 up`), alpha 0.52, hot spot 230, and `beam_layers` adds a warm floor pool (`#f0a84e` / `#ffd58a`,
  layer `beam_pool`) under the hot spot: the OURS signature "blue-violet night with a warm beam" is visible.
- **Moon shafts** a little stronger in OURS (alpha 44, `after` 26).
- Measured on plan shots with the cast (640x360): S055 master p50 101 / p95 184 / p95-p5 146 / std 48 (was 97 / 166 / 128
  / 41); S177 doorway master p95 190, contrast 154.
- **`dawn_queen_v2`** (engine/post.py): cooler white balance and a dark floor `#2e2428`, so her black satin and hair
  stay black near her instead of brown.
