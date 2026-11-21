# CAST: "If The Ice Cream Truck Plays Its Song In Winter... DON'T GO OUTSIDE"

This film's cast and staging tools are in `characters_ice.py` (see `ICE_API`), run in the `characters` namespace after
`characters_bus.py`. Use everything as `import characters as CH`.

characters.py runs it (the `_ICE_SRC` exec line after the bus module is in place).

- **Sheets:** `python3 tools/cast_sheets.py [sh_turn sh_head sh_transform sh_monster sh_mood sh_limits lineup faces]` -> `_work/cast/`.
- **Clips:** `python3 tools/cast_clips.py [names] [--strip-only]` -> `_work/cast/clips/<name>.mp4` + `_strip.jpg` (960x540,
  60 fps); `clips_a.json` / `clips_b.json` hold sound events and contact reports. Scenery is a stand-in (sets own the truck).

## Who's who (draw height = `CH.height_px(id, px_per_m)`)
| id | look |
|---|---|
| `shiver` | **MISTER SHIVER** 1.93 m. Bus 3D rig (`_ws_rig`, arms with world-target IK) with his own egg head (1.2x), long neck, chalk-white skin, dark sockets, tiny blue eyes, no brows, frost flecks, small flat ears (tilted back, helix), a real profile (brow, nasal bridge, nose, lip, chin; the smile a crescent back toward the ear), buck teeth over a gap-toothed lower row. VENDOR COAT (`_SH_ROWS`): squared shoulders with set-in sleeve caps, waist, pull folds at the buttons, two patch pockets, hem flared to mid-thigh with side vents; full striped sleeves with elbow creases and wide white turned-back cuffs; charcoal pressed trousers, long black shoes. KNITTED WOOL gloves (`_sh_glove`: plump round fingers, grey wool seams not dark gaps, knuckle bumps, V-stitch knit, 2-row ribbed cuff). No breath, no blinks, no lip sync. |
| `adam` / `adam_in` / `adam_sock` | Adam 12: navy puffy coat with 3 quilting baffles, red knit hat, boots / indoors hoodie / `adam_sock` after 6:45: LEFT boot, RIGHT foot in a grey sock caked with snow (`feet_lr`) |
| `lina` / `lina_pj` | Lina 6: yellow coat worn OPEN over the pink snowflake pyjamas (white snowflakes show), pink hat, bigger eyes set lower than Adam's, gap teeth / pyjamas only |
| `dad` | hi-vis orange jacket, brown hat, heavier stubble, 1.88 m |
| `kessler` / `kessler_out` / `kessler_am` | 80, glasses, large ears (1.6), white stubble, grey cardigan / grey undershirt + slippers, blue-grey skin (severe cold; use heavy lids + slack mouth for "not shivering") / morning |
| `walter58`, `benny` | sepia 1958 |
| `mom_photo`, `shiver_mom` | Mom (photo) / HIS copy at the door glass (no breath, no blinks) |
| `medic_a`, `medic_b` | paramedics |

## Mister Shiver: pose keys and staging
Pose: `sh_m` 0..1 = THE TRANSFORMATION (`SH_STEPS`, 8 states: wave, smile past cheeks, long bone mask + frost cracks,
eyes sink, red, jaw to chest with icicle teeth, uniform splits + legs punch out, planted). Overrides: `sh_smile`,
`sh_long`, `sh_sink`, `sh_red`, `sh_jaw`, `sh_gape`, `sh_split`, `sh_legs` (0..8, they punch out one PAIR at a time),
`sh_glim` (glimpse), `sh_lift` (cm, body slung in the leg cage; the head hangs by `sh_hang`, default 0.55), `sh_spread`,
`sh_legcap`, `sh_nolegs` (human legs hidden), `ws_bend` (lean / down and down).
Legs: 8 jointed harvestman legs (femur ~2.9x his height): bowed spindles tapering from thick at the body to a pale needle,
lit/shadow edges + rim light, telescoping rings, bristles, dark ball joints under flared segment ends, frost rime crusted on
top of every knee with tiny icicles, torn stripe flaps round each root. The mask: zygoma planes, temple hollows, brow ridge,
big sockets with a frost rim, the lower mask tapering ~2x long; the dropped jaw ends in a cracked bone mandible, sinews and
frost strands at the mouth's sides, icicle teeth with 3 long fangs above and 2 below. In medium shots frame wide enough for
the knees (they ride high over his head).
```python
a = CH.Acting('shiver', seed=1, height=CH.height_px('shiver', ppm)).place(x, floor_y)
a.transform(t0, times)          # 8 times keyed to the words; events sh_smile_creak, sh_bone_crack, sh_eyes_sink, sh_eyes_red, sh_jaw_drop, sh_uniform_split, leg_click x8
a.shrink_back(t0, dur)          # defeat ('legs_fold', 'sh_jaw_close');  a.jaw_gape(t0, t1)  the hung note
a.glimpse(t0, 0.13)             # one flicker: long white face, red eyes
a.slow_wave(t0, t1, side)       # the over-long wave beside his head (open glove)
a.reach_far(t0, side, target)   # the glove down to Lina's hand; reach_to / look_at / lean_to from the bus rig work
a.leg_to(t0, i, target, dur, hold, back, ev='leg_stab')   # one needle tip to a world point (snow, coat, blanket, under a door)
a.legs_plant(t0, {i: (x, y)})   # plant legs (truck roof)  ;  a.cage(t0, cx, width, ground_y)  legs arched over people
a.scuttle(t0, t1, path(u)->(x,y), ground(x)->y)           # gait with planted tips, clicks
a.drop_to(t0, dur, from_dy)     # from a roof edge   ;  a.pour_out(t0, dur, sill_dy, ground_dy, roof_dy=, frame_w=, ground=)  head first, legs last (see below)
a.hang_hatch(t0, dur, lower)    # upside down from the attic hatch (pair with sh_legcap=1 and leg_to)
```
Points: `a.where(t, 'eyes'|'mouth'|'chin'|'crown'|'head'|'leg0'..'leg7'|'knee0'..|'hand_l'...)`.
In the truck: draw the truck wall over him below the sill (see `shiver_in_window` in cast_clips.py); when he bends out
over the sill use `sh_nolegs=1` and draw him in front (as `sh_lean_down_reach`).
**pour_out** (clip `sh_pour_out`): 4 legs grip the roof edge and window frame from the start; he rises to the sill and curls
over it neck first, the gloves plant in the snow, the roof legs haul his hips out, the last 4 legs unfold out of the window
and every leg steps down to the snow; he is never horizontal or unsupported. Draw him TWICE: full figure clipped to the window
hole, the truck wall, then the figure again in front (clip away below the sill while `P._sh_pour_u < 0.1`), then the sill
ledge over his hips while `P.sh_nolegs` is 1. **scuttle**: tetrapod gait, `spread` 1.6, body slung low, head hanging; stage
him facing the lens (3/4) so the arch spreads across the frame; tips land on `ground(x)` (fence rail, car roof, roof slope).
**transform**: the back swells and quivers, splits, then one PAIR of legs per click (keep >= 0.45 s apart); clip
`sh_transform_legs` cuts a 3/4 medium on the split (only his pink light behind: no truck interior) to the wide.
Lights: `light=dict(rim=, rim_a=, side=, dark=0..1)` (dark: only eyes and teeth catch light).

## People
All the older tools work (walk/run take ABSOLUTE x: place walkers at x=0; radio_to_mouth with prop 'walkie'; drive +
draw_steering_wheel; wave(slow=True); hum; hold_hand; hold_prop 'mug').
**carry (this film)**: `adam.carry(t0, lina)` AFTER `adam.run(...)` (else the run's arms pump): Lina on his hip and chest,
thighs round his waist, knees bent, arms locked round his neck, cheek on his shoulder, face to the lens; his near arm under
her seat, far arm across her back. Draw with `CH.draw_carry_child(pen, adam, lina, t, light)`.
`CH.draw_breath(pen, actor, t, period, k)`: a breath puff from the mouth (people only; never Shiver).

## Beat map -> clips
drive-by/lean/wave/look `sh_drive_by_lean`; glimpse `sh_glimpse_flicker`; window `sh_slide_window`; down + glove
`sh_lean_down_reach`; transformation `sh_transform_face` + `sh_transform_legs`; `sh_pour_out`; chase `sh_legs_spear_coat`,
`sh_scuttle_fence_car_roof`, `sh_drop_door`; mitten `sh_pluck_mitten`; door glass `sh_face_glass`; attic `sh_hatch_upside_down`;
bathroom `sh_under_door`; climax `sh_hook_blanket_cage`; defeat `sh_defeat_shrink`. People: `adam_radio_over`,
`lina_wave_kessler`, `kessler_window_hand`, `lina_walk_humming`, `adam_run_carry_lina`, `dad_plow_cab`,
`kessler_shuffle_out`, `lina_hug_kessler`, `kessler_cocoa_morning`, `benny_1958`.

## Open issues
- Lina's mittens and Benny's red mitten are props for the shot, not on the rig; Kessler's blanket is a shot overlay.
- Adam's hat cuff, Dad's trapper ear flaps and Kessler's hair wisps are unchanged (the hat/hair styles are shared rigs).
- Reach-miss counts in strip-only renders over-count carried children (the child is placed at draw time); full 60 fps
  renders are the measure. `sh_lean_down_reach` keeps a ~55 px glove-to-hand gap at the end of the reach.
- Truck, door glass, hatch and under-door scenery in the clips are stand-ins (sets own the snowflake and the mitten bunting).
