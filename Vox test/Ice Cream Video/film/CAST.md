# CAST: "If The Ice Cream Truck Plays Its Song In Winter... DON'T GO OUTSIDE"

This film's cast and staging tools are in `characters_ice.py` (see `ICE_API`), run in the `characters` namespace after
`characters_bus.py`. Use everything as `import characters as CH`.

**HOOK STILL NEEDED in characters.py** (the cast job may not edit it): add after the `_BUS_SRC` exec line
```python
_ICE_SRC = os.path.join(_HERE, 'characters_ice.py')
exec(compile(open(_ICE_SRC).read(), _ICE_SRC, 'exec'))
```
Until then `tools/cast_clips.py` / `tools/cast_sheets.py` exec it themselves (`if not hasattr(CH, 'ICE_API')`), and
film.py must do the same.

- **Sheets:** `python3 tools/cast_sheets.py [sh_turn sh_head sh_transform sh_monster sh_mood sh_limits lineup faces]` -> `_work/cast/`.
- **Clips:** `python3 tools/cast_clips.py [names] [--strip-only]` -> `_work/cast/clips/<name>.mp4` + `_strip.jpg` (960x540,
  60 fps); `clips_a.json` / `clips_b.json` hold sound events and contact reports. Scenery is a stand-in (sets own the truck).

## Who's who (draw height = `CH.height_px(id, px_per_m)`)
| id | look |
|---|---|
| `shiver` | **MISTER SHIVER** 1.93 m. Bus 3D rig (`_ws_rig`, arms with world-target IK) with his own egg head (1.2x), long neck, chalk-white skin, dark sockets, tiny blue eyes, no brows, frost flecks, nose, ears, buck-toothed too-wide smile; pink/white vertical stripes, Peter Pan collar, pink bow tie + snowflake pin, snowflake SHIVER badge, white knitted gloves. No breath, no blinks, no lip sync. |
| `adam` / `adam_in` / `adam_sock` | Adam 12: navy puffy coat, red knit hat, boots / indoors hoodie / socks (see issues) |
| `lina` / `lina_pj` | Lina 6: yellow coat, pink hat, pink snowflake pyjamas, gap teeth / pyjamas only |
| `dad` | hi-vis orange jacket, brown hat, stubble, 1.88 m |
| `kessler` / `kessler_out` / `kessler_am` | 80, glasses, big ears, white stubble, grey cardigan / grey undershirt + slippers / morning |
| `walter58`, `benny` | sepia 1958 |
| `mom_photo`, `shiver_mom` | Mom (photo) / HIS copy at the door glass (no breath, no blinks) |
| `medic_a`, `medic_b` | paramedics |

## Mister Shiver: pose keys and staging
Pose: `sh_m` 0..1 = THE TRANSFORMATION (`SH_STEPS`, 8 states: wave, smile past cheeks, long bone mask + frost cracks,
eyes sink, red, jaw to chest with icicle teeth, uniform splits + legs punch out, planted). Overrides: `sh_smile`,
`sh_long`, `sh_sink`, `sh_red`, `sh_jaw`, `sh_gape`, `sh_split`, `sh_legs` (0..8), `sh_glim` (glimpse), `sh_lift` (cm,
body slung in the leg cage), `sh_spread`, `sh_legcap`, `sh_nolegs` (human legs hidden), `ws_bend` (lean / down and down).
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
a.drop_to(t0, dur, from_dy)     # from a roof edge   ;  a.pour_out(t0, dur, sill_dy, ground_dy)  head first, legs last
a.hang_hatch(t0, dur, lower)    # upside down from the attic hatch (pair with sh_legcap=1 and leg_to)
```
Points: `a.where(t, 'eyes'|'mouth'|'chin'|'crown'|'head'|'leg0'..'leg7'|'knee0'..|'hand_l'...)`.
In the truck: draw the truck wall over him below the sill (see `shiver_in_window` in cast_clips.py); when he bends out
over the sill use `sh_nolegs=1` and draw him in front (as `sh_lean_down_reach`).
Lights: `light=dict(rim=, rim_a=, side=, dark=0..1)` (dark: only eyes and teeth catch light).

## People
All the older tools work (walk/run take ABSOLUTE x: place walkers at x=0; carry + draw_carry_child; radio_to_mouth with
prop 'walkie'; drive + draw_steering_wheel; wave(slow=True); hum; hold_hand; hold_prop 'mug').

## Beat map -> clips
drive-by/lean/wave/look `sh_drive_by_lean`; glimpse `sh_glimpse_flicker`; window `sh_slide_window`; down + glove
`sh_lean_down_reach`; transformation `sh_transform_face` + `sh_transform_legs`; `sh_pour_out`; chase `sh_legs_spear_coat`,
`sh_scuttle_fence_car_roof`, `sh_drop_door`; mitten `sh_pluck_mitten`; door glass `sh_face_glass`; attic `sh_hatch_upside_down`;
bathroom `sh_under_door`; climax `sh_hook_blanket_cage`; defeat `sh_defeat_shrink`. People: `adam_radio_over`,
`lina_wave_kessler`, `kessler_window_hand`, `lina_walk_humming`, `adam_run_carry_lina`, `dad_plow_cab`,
`kessler_shuffle_out`, `lina_hug_kessler`, `kessler_cocoa_morning`, `benny_1958`.

## Open issues
- characters.py hook (above). `adam_sock` has two socks (no one-boot variant); Lina's mittens and Benny's red mitten are
  props for the shot, not on the rig; Lina's coat reads closed; Kessler's blanket is a shot overlay.
- His gloves use the bus mascot-glove geometry (lighter seams): they read a little bony at wide sizes.
- Profile head is egg-like; stage him front / 3/4 (he faces out of the window).
- Truck, door glass, hatch and under-door scenery in the clips are stand-ins.
