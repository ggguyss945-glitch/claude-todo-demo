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
| `shiver` | **MISTER SHIVER** 1.93 m. Bus 3D rig (`_ws_rig`, arms with world-target IK) with his own egg head (1.2x), long neck, chalk-white skin, dark sockets, tiny blue eyes, no brows, frost flecks, small flat ears set back behind the jaw hinge (tilted back, a rolled C helix, mostly hidden in front view), a real profile (brow, nasal bridge, button nose, lip, chin, a soft jaw line to the ear; the smile a crescent back toward the ear), buck teeth over a gap-toothed lower row. VENDOR COAT (`_SH_ROWS`): squared shoulders with set-in sleeve caps, waist, pull folds at the buttons, two patch pockets, hem flared to mid-thigh with side vents; full striped sleeves with elbow creases and wide white turned-back cuffs; charcoal pressed trousers, long black shoes. KNITTED WOOL gloves (`_sh_glove`: plump round fingers, grey wool seams not dark gaps, knuckle bumps, V-stitch knit, 2-row ribbed cuff). No breath, no blinks, no lip sync. |
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
`sh_glim` (glimpse), `sh_lift` (cm, body slung in the leg cage; use 80-90; the torso pitches ~60 deg, the head is thrust
FORWARD at the lens and only nods by `sh_hang` (default 0.15, capped 0.15), his own legs tuck away above 40 cm), `sh_spread`,
`sh_legcap`, `sh_nolegs` (human legs hidden), `ws_bend` (lean / down and down), `sh_menace` (default 1: the monster idle,
see below; 0 = off), `sh_legs_only` (draw only the spider legs: lay them IN FRONT of people he cages).
Legs (round 3): 8 THICK jointed harvestman legs bent close round the body (coxa/femur/tibia/tarsus 30/125/135/70 cm, widths
24/24-16/16-8/8-0.6), knees at their own heights (fanned in depth per pair), tarsi splayed (never parallel stilts), tips near
z=0 so planted tips sit ON the ground line (leg_to / legs_plant default zd=0); dimmer knee rime (#c4d3e0, ~60%); the HEAD
GROWS x1.8 with the legs and gets a x1.15 thrust toward the lens, drawn LAST, in front of everything of his own (claws beside the mandible) and the red eyes fill ~45% of the sockets with a bloom >= 4 px on output;
the dropped jaw is its OWN bone mandible (~0.85 of the mask wide, ~0.22 tall, outline + frost crack, 6 icicles standing up, 2
fangs) under a dark #120A10 falloff gap crossed by sinew/frost strands (no capsule outline); the mouth never closes again once
the icicles come (sh_m > 0.4); at sh_smile > 0.5 the slit runs PAST the face outline; in the cage the arms claw forward at jaw height and the gloves go frost-grey.
Femur bowed out and tibia bowed in (an organic S), spindles tapering from thick at the body to a pale needle,
lit/shadow edges + rim light, telescoping rings, bristles, dark ball joints under flared segment ends, frost rime crusted on
top of every knee with tiny icicles, torn stripe flaps round each root. The mask: zygoma planes, temple hollows, brow ridge,
big sockets with a frost rim, the lower mask tapering ~2x long; the jaw drops ~one head to the chest and ends in a wide cracked bone mandible (the mask keeps its scale), sinews and
frost strands at the mouth's sides, icicle teeth with 3 long fangs above and 2 below. FRAME ON THE FACE: the legs may leave
the frame edges (they bracket the mask); never frame so wide that the head is under ~8% of the frame height (sh_mood, the
medium-wide in sh_transform_legs). Normal form: arms are tapered striped cylinders (6 wrapping stripes), one-piece trousers
#4d4556 with a hem break, no forehead creases (frost sparkles), smile clipped to the head until the transformation. Normal form is friendly-wrong: faint cool sockets (#aeb9c9), lit cheek
apples, the lower lids pushed up (smiling eyes), a big catchlight, 4 separate lower teeth with 2 gaps; the face is the top
value (white stripes #E4D8DE, gloves #DEDAD4, a cool #dfeaff rim, the coat darkens below the badge). Gloves x0.85, thumb
turned in, soft knit ribs (no V-stitch 'bones').
**Menace idle (automatic for sh_m >= 0.9):** the head tilts in 0.4 s moves with holds, creeps toward the lens on a 5 s
cycle, one needle lifts and re-plants every 0.58 s (same spot). `a.menace(t0, t1)` adds its soft leg_click events.
`a.fear_body(t0, t1=None, k=1)` (people): shoulders up, chin down, a 0.9 Hz breath; no jiggle.
```python
a = CH.Acting('shiver', seed=1, height=CH.height_px('shiver', ppm)).place(x, floor_y)
a.transform(t0, times)          # 8 times keyed to the words; events sh_smile_creak, sh_bone_crack, sh_eyes_sink, sh_eyes_red, sh_jaw_drop, sh_uniform_split, leg_click x8
a.shrink_back(t0, dur)          # defeat ('legs_fold', 'sh_jaw_close');  a.jaw_gape(t0, t1)  the hung note
a.glimpse(t0, 0.13)             # one flicker: long white face, red eyes
a.slow_wave(t0, t1, side)       # the over-long wave beside his head (open glove)
a.reach_far(t0, side, target)   # the glove down to Lina's hand; reach_to / look_at / lean_to from the bus rig work
a.leg_to(t0, i, target, dur, hold, back, ev='leg_stab')   # one needle tip to a world point (snow, coat, blanket, under a door)
a.legs_plant(t0, {i: (x, y)})   # plant legs (truck roof)  ;  a.cage(t0, cx, width, ground_y)  legs arched over people (lift clamped 80-90, human legs tucked; draw him BEHIND them, then
#   again with P.sh_legs_only=1 in front: see sh_hook_blanket_cage)
a.scuttle(t0, t1, path(u)->(x,y), ground(x)->y)           # gait with planted tips, clicks
a.drop_to(t0, dur, from_dy)     # from a roof edge   ;  a.pour_out(t0, dur, sill_dy, ground_dy, roof_dy=, frame_w=, ground=)  head first, legs last (see below)
a.hang_hatch(t0, dur, lower)    # upside down from the attic hatch (pair with sh_legcap=1 and leg_to)
```
Points: `a.where(t, 'eyes'|'mouth'|'chin'|'crown'|'head'|'leg0'..'leg7'|'knee0'..|'hand_l'...)`.
In the truck: draw the truck wall over him below the sill (see `shiver_in_window` in cast_clips.py); when he bends out
over the sill use `sh_nolegs=1` and draw him in front (as `sh_lean_down_reach`).
**pour_out** (clip `sh_pour_out`): 4 legs grip the roof edge and window frame from the start; he rises to the sill and curls
over it neck first, hanging head-down with the mask still turned to the lens, the gloves plant in the snow, the roof legs haul his hips out, the last 4 legs unfold out of the window
and every leg steps down to the snow; his own legs show only as the cage rights him (last); he is never horizontal or unsupported. Draw him TWICE: full figure clipped to the window
hole, the truck wall, then the figure again in front (clip away below the sill while `P._sh_pour_u < 0.1`), then the sill
ledge over his hips while `P.sh_nolegs` is 1. **scuttle**: tetrapod gait, `spread` 1.6, body slung low and pitched forward (`pitch` 28), head hanging; stage
him facing the lens (3/4) so the arch spreads across the frame; tips land on `ground(x)` (fence rail, car roof, roof slope).
**transform**: the back swells and quivers, splits, then one PAIR of legs per click (keep >= 0.45 s apart); clip
`sh_transform_legs` cuts a medium on his shoulder and back (0-1.4 s: turn 0.8, the mask turned to us, he goes rigid; only his pink light
behind) -> a MEDIUM-WIDE (1.4-4.0 s, bible step 6 'hold on the full monster': window + head, mask ~24% of the frame, legs out of the
frame edges) -> a tight wide for <= 1 s (truck ~70% of the frame, tips on the roof beside the snowflake). Copy these framings.
Other round-2 stagings: `sh_pour_out` ppm 470 (window ~30% of the frame, he pours toward the lens); `sh_scuttle_fence_car_roof` a
tracking shot (camera follows his head, ppm 300); `sh_drop_door` 0.55 s fall + 15 cm squash on landing (`drop_to`), jaw after;
`sh_hatch_upside_down` a low angle from the kids (inverted face ~20% of the frame, leg stabs between them, Adam pulls Lina behind
him); `sh_lean_down_reach` hinges over the sill (no flip), neck +25 cm, glove tracks Lina's hand ~55 px short.
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

## Faces and hats (round 2)
- No sweat drops in this film (EXPR sweat = 0). Kids (`kidface`) never get forehead lines, frown or smile folds.
- COLD-DANGER look: `sleepy` (stopped shivering, sleepy) and `cold_warm` ("I'm warm, Adam") give pale blue-grey skin, no rosy
  cheeks, blue-grey lips, heavy lids. Any expression with pale >= 0.5 and blush <= -0.5 gets this tint. `grumpy` (Kessler):
  heavy lids, brows down, mouth corners down. `fear`: smaller iris, corners down. `terrified_call`: wider shout.
- Hats (`ice_hat`): Adam a smooth knit beanie with a folded cuff; Lina the same with a POM-POM; Dad trapper ear flaps with
  fleece trim; walter58 a 1958 flat cap. Kessler's wisps lie flat on the scalp.
- Benny's ONE red mitten is on his right hand in `benny_1958` and drops at the curb at the end of the walk.

## Round 3 clip stagings
`sh_transform_face`: over Adam's shoulder (red hat left fifth), window frame + bunting ends, a monotonic camera so the mask
grows 30% -> 55% of the frame, the body cut by the real sill/wall. `sh_hook_blanket_cage`: ppm 360, three under one opaque
blanket (Kessler `hypo`, Lina, Adam), he scuttles in slung low, hooks the corner and pulls (they lean back, Adam grips the
hem), snap back, then the legs in front, jaw gape, head creep. `sh_legs_spear_coat`: ppm 330 tracking, mask at the lens,
gap closes ~600 -> ~300 px, the hem pinned (stretched, Adam jerked back, a flap stays), the pry between arm and back.
`sh_defeat_shrink`: ppm 450 for the gape, cut wide for the fold. `sh_under_door` / `sh_pluck_mitten`: close inserts with
tapered jointed legs (towel brought by Adam's hand and cuff; the mitten hooked on the needle, hung in the same frame).
EXPR: `lina_grin` (two front teeth, gap), `hypo` (severe cold, slack oval), `terrified_call` a wide D shout; kids' mouths
have a dark-red interior and one flat upper tooth band. Dad's flaps are knit trapezoids with an inner fleece border.

## Round 4 (fix pass 2)
- **The face is never covered:** in monster form (`sh_m > 0.48` or any legs out) the head is ALWAYS drawn last, the
  arms just under it (only a true back view, |turn| > 1.22, puts the body over the head); `sh_legs_only` passes keep the
  head on top too. Caged claws hang BESIDE the mandible (`_sh_rig` target head + [55, 50, 18] cm scaled by the head growth);
  slung (`sh_lift` > 40) the head drops and pushes forward (crown over the chest).
- **Maw:** the jaw drop is ~0.9 of the mask (`drop = J*(19+4L)`); the dark maw is its own path, inset ~13% of the head
  width at each side (skull, a notch, then the jaw), filled with a radial #120A10 -> #2A1420 falloff; 2 sinew strands a side
  INSIDE it at half alpha; the mandible is a squared jaw block (0.92 of the mask wide at the top, 0.8 at the chin, corner
  radius ~0.15) with 6 icicles standing up (2 long).
- **Step 1:** the slit runs ~20% of the head width past the outline with corners hooked up (fades as the jaw drops). The
  transformation sheet waves through steps 0-6 (`cast_sheets.wave_pose`).
- **Legs:** per pair femur length (1.0/0.92/1.06/0.97), angle 56-68 deg plus a knee lift (0/16/26/8 cm): the knees arch
  at clearly different heights; tarsi splay +-24-30 deg alternating per pair; dark #3E2A1C knee/ankle knobs; the rime is
  2-3 small crusts at ~0.55x the joint (no mushroom caps).
- **Vendor face:** no nasolabial lines, one smooth smiling arc under each eye; collar #E4D8DE, buttons #D8D2DA, skin_hi
  #FFFDF8 (the face is the top value). `grumpy` is sour and closed (lids 40% down, brows in and down, corners down);
  Kessler's ears x1.85. Dad's trapper hat: flaps 1.3x longer past the jaw, tilted out, wider at the bottom, fuzzy fleece on
  the brim and round the flaps, a tie cord from each tip.
- **Scuttle:** a 20 px bob at twice the stride rate, +-6 deg pitch, the head lagging 0.12 s.
- **Clips:** `sh_transform_face` cuts IN three times (medium 0-1.0, close 1.0-2.6 with a push, close-up from 3.2 s),
  framed on crown-to-mouth (28% -> 42% -> 50%+, eyes at y 360), never shrinking; Adam drawn in the same world with a 0.35
  parallax, Lina's pom-pom hat and cheek at his shoulder (carried), a 25 px / 6 deg flinch at the red eyes.
  `sh_lean_down_reach` hinges (bend <= 0.75, neck +60) and cuts to a medium at 1.5 s (glove, her hand, both faces).
  `sh_transform_legs` 0-1.4 s has the window frame, bunting end and striped wall behind him; the medium-wide is ppm 635
  (mask >= 25%, the jaw and mandible clear the sill); the tight wide (4.2-5.0 s) plants every tip ON the roof span.
  `sh_pour_out` ppm 290, snow at y 840 with the truck's lower body and wheels, tips and gloves land on it, needle holes
  (`snow_holes` now works), a 1.0 -> 1.25 push over the last 1.2 s. `sh_hook_blanket_cage`: the blanket lies flat until
  the leg hooks it, wraps the fronts of their shoulders and torsos (hem at the front, Kessler grips both edges), the three
  angled 3/4 and staggered, Lina looks then hides her face in Adam's coat, Adam steps half in front, all hunch as the cage
  lands. `sh_legs_spear_coat`: a real run (~9 px/frame scroll), the needle through the hem INTO the snow, the coat
  stretched over Adam, a 0.45 s pin with a 35 px jerk back and ~12 deg lean, then the tear (flap stays). Dad's car in
  `sh_scuttle_fence_car_roof` is drawn from the same profile the tips walk on (windows, wheels). Family clips cut from a
  <= 1.5 s wide to a medium (`_medium`): benny (from behind, sepia at shot level), lina_walk, adam_run_carry, kessler
  shuffle and cocoa; `lina_hug_kessler`: he looks down at her, his hand settles on her back at 1.2 s, the shoulders drop
  with a long breath and closed eyes at 1.8 s; her cheek turned out.

## Still open (next pass)
- Hero insert hands (ice-only thicker fingers, knuckles, nails) not built; the people's hands are still the shared thin ones.
- The raised waving glove still reads as a closed club at close scale (no separate finger tubes / palm-to-lens roll).
- Benny's pyjama stripes and red mitten on the rig, walter58 as a boy, Adam's puffy baffles, the profile cheek/jaw mass.
- `sh_face_glass` door frame + coat silhouette, `sh_hatch_upside_down` low angle, `sh_pluck_mitten` heavy leg.
- Buck teeth still smaller than the bible's (not resized this pass).

## Older open issues
- Lina's mittens and Benny's red mitten are props for the shot, not on the rig; Kessler's blanket is a shot overlay.
- Not done in round 2 (left for the next pass): Adam's coat baffles still read flat; Benny's pyjama stripes; walter58's sepia grade
  in the lineup (apply the sepia grade at shot level) and Kessler's ear scale; Dad's grip on the wheel / horn presses
  (`dad_plow_cab`); the people's hands (still thin) in the shared hand system; `lina_hug_kessler` reaction; `adam_run_carry_lina`
  3/4 hero framing; the cool rim light on Shiver in window shots; leg surface highlights at small sizes; 'cold_hands' (7:25 insert).
- Reach-miss counts in strip-only renders over-count carried children (the child is placed at draw time); full 60 fps
  renders are the measure. `sh_lean_down_reach` keeps a ~55 px glove-to-hand gap at the end of the reach on purpose (she never touches him).
  `lina_hug_kessler` is a real hug now (pressed to him, both arms round his hips).
- Truck, door glass, hatch and under-door scenery in the clips are stand-ins (sets own the snowflake and the mitten bunting).
