# SETS.md: `sets.py` for "If An Eighth Step Appears On Your Mirror..."

`sets.py` builds every set, view, lighting variant and animated prop state that `plan/shots.json` names: 96 views plus the
rule-card backgrounds, all in the engine's 1920x1080 design space, with real depth for parallax and depth of field.
All 317 shots build, and every `chars[].at` anchor name resolves.

## 1. Use

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

## 2. Prop state (`St`)
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

## 3. The mirror system
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

## 4. Sets, views, variants and anchors
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

## 5. Grades
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

## 6. Speed (measured: 2560x1440, one process, sets + grade + post, no cast or HUD)
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

## 7. Test harness
- Stills of every set, view and variant, with the cast: `_work/sets/stills/<set>__<view>__<var>__<shot>.jpg` (960x540).
- Contact sheets: `_work/sets/sheet_1..6.jpg`.
- Make them with `python3 tools/sets_sheet.py _work/sets/sheet.jpg --chars --per 24 --stills _work/sets/stills --combos [set ...]`.
  Single shots: `... sheet.jpg S119 S150@340.1`.
- Benchmark: `OMP_NUM_THREADS=1 python3 tools/sets_bench.py --combos` (or a list of shot ids). It prints the first frame
  and the warm median and max per view.
