# CAST: "If The Bunnyman Asks You To Close Your Eyes... DON'T COUNT TO SEVEN"

The cast lives in `characters.py`. This film's cast and the new staging tools are in `characters_bunny.py`, which
`characters.py` runs in its own namespace at import. Use everything as `import characters as CH`. The older films' casts and
API still work unchanged. The dummy film's Mom is now `mom_dummy`, and the delivery film's Dad is `dad_delivery`.

- **Self-test:** `python3 characters.py --selftest`. It runs the older films' checks, with their lip sync measured against the dummy
  film's recording, then this film's checks: views, reach precision, seats, kneels, walk slide, prop pick-up, look-at,
  holding hands and lip sync.
- **Sheets:** `python3 tools/cast_sheets.py`. It writes about 1 min of sheets to `_work/cast/*.jpg`.
- **Acting clips:** `python3 tools/cast_clips.py [names] [--strip-only] [--review]`. It writes 40 clips at 960x540 and 60 fps to
  `_work/cast/clips/<name>.mp4`, each with an 8-frame `<name>_strip.jpg`. `clips.json` holds the sound events and the
  contact report for each clip: reach misses and foot gaps. Every clip currently reports 0 misses and 0 px foot gap.

## Who's who (draw height = `CH.height_px(who, px_per_m)` at the same depth)
| id | look | notes |
|---|---|---|
| `bunny` | **The Bunnyman now.** A grey plush mascot suit on a tall man, 1.98 m to the crown with the ears above. Fur matted dark. The character's right ear is snapped 40 % up and its flap hangs over the side of the head, swinging with motion. Round black glass eyes in dirty felt rings that **reflect nothing**. Pink nose on two puffy muzzle pads, bent whiskers (one broken off), two big yellowed buck teeth (one chipped), and a long stitched smile with a rust-brown dribble. White belly panel soaked with a rust-brown stain, with runs and drops. Torn rips with stuffing bulging out. Mud on the legs and feet. A cotton tail, and a zipper in the back. | The mask **never lip-syncs**: `talk` only nods it a little, because the voice is inside. Paw hand shapes: `paw`, `paw_open` (wave), `paw_point`, `paw_grip` (holding), `paw_flat` (pads to camera). `pose.unmask` 0..1 tips the foam head back off his crown and shows Dale's face, which lip-syncs "Mama". |
| `bunny87` | The clean 1987 department-store mascot. Fluffy light grey, white belly, both ears up, glossy eyes with highlights, pink nose and inner ears, white teeth. | `hold_prop('basket', side)` gives him the Easter basket. |
| `mom` | **Laurie, 43.** Auburn chin-length bob with a side part, green eyes, pearl studs. Dusty-rose cardigan over a cream blouse with a round collar, taupe trousers, ballet flats, her gold wedding ring. | Expressions: `too_still` (a smile the eyes don't share), `hum()`, `proud`, `warm_smile`. `pose.scratch` 1 pushes her sleeves up and scratches her forearms to ribbons; `pose.mess` loosens her hair. |
| `mom_hosp` | The same body in a hospital gown, with long unkempt hair and dark circles. | This is the **narrator inside Mom's body**, so play them as a scared cast member: blinks, `haunted`, `fear`, `cry`. |
| `june` / `june_dress` | **June, 7.** Honey-brown low pigtails with pink scrunchies, brown eyes. Mint pajamas with a tiny Easter-egg print and white socks with pink toes. Or the yellow Easter dress: puff sleeves, white collar, sash and bow, lace hem, Mary Janes. | She is a child: never still, with big irises. |
| `laurie87` | **Laurie at 7, 1987.** Strawberry-blonde high pigtails with big yellow ribbon bows, green eyes (Mom's), and the same yellow dress. | `hold_prop('egg_gold', side)` + `hum()` for sunrise. |
| `narrator` | **The narrator, 16** ("I"; never said if boy or girl). Chin-length dark auburn hair, soft jaw, hazel-green eyes, no make-up. Oversized sage hoodie with the sleeves half over the hands, charcoal joggers, grey socks. | Scared cast. |
| `narrator_new` / `narrator_neat` | The thing in the narrator's body. In the hallway it wears the same clothes. At the hospital visits it is neat: hair tucked, a pressed cream cardigan, a white collar. | It never blinks and wears `wrong_smile` + `hum()`. Its lips barely move (talk 0.35). |
| `narrator_kid` | The narrator at six, in Grandma's memory. | |
| `grandma` | Silver hair in a soft bun, glasses, a lavender cardigan over a flowered blouse, a gold brooch, a plum skirt. | `knock_pattern(t, (2, 3, 2))` |
| `dad` | Mid 40s. Brown hair greying at the temples, stubble, blue-grey eyes. Tan canvas work jacket, charcoal henley, jeans, boots, gold ring. | `hold_prop('maglite', side)`; beam with `CH.torch_pos3(a, t, side)` + `CH.draw_torch_beam`. |
| `dale` | Dale at 55: gaunt, grey stubble, thin grey hair. | You normally never draw `dale` directly: he is the face under `unmask`. Use `expr('little_girl')`, `mama(t)`, `dead(t)`. |
| `cop`, `cop2`, `doctor`, `nurse` | The police from the police film made ordinary and kind (they blink, with natural eyes); a doctor in a white coat with glasses and a stethoscope; a nurse in teal scrubs with a ponytail. | `hold_prop('notebook' / 'clipboard', side)` |

Heights: bunny 1.98, dad 1.83, narrator 1.68, mom 1.66, grandma 1.58, june / laurie87 1.22, narrator_kid 1.15.

## Staging rules: the owner's notes, and the tool for each
1. **Place every actor** with `a = CH.Acting(who, seed, height=CH.height_px(who, ppm)).place(x, y_floor)`. Use the same
   x / y / height you pass to `CH.draw`. `y_feet` is always the **floor**: seated, kneeling and crouching figures keep their
   feet on it. For a lying figure, `y_feet` is the surface it lies on.
2. **Sit on real furniture:** `a.sit_on(t0, seat_y, dur, t1=stand_up_time)` or `a.seated(seat_y)`. The hips rest on the
   seat top and the feet stay on the floor. Standing up leans the weight forward first. Stage seated or floor-sitting people
   at |turn| >= 0.5: front-on, the thighs foreshorten and the figure reads as standing (that is the dummy film's
   "standing on the couch").
3. **Kneel:** `a.kneel_down(t0, dur, knees=0|1|2)`. 0 is one knee down, 1 is both knees, 2 is sitting back on the heels. A foot
   or a knee stays on the floor every frame.
4. **Eyelines:** `a.look_at(t0, target, t1, dur, z=None, body=0)` takes a point, a callable, `(other_actor, 'eyes')` or a
   `PropTrack`. The eyes lead and the head follows. Use it for every glance at a person, a prop or a sound source.
5. **Contact:** `a.reach_to(t0, side, target, t1, dur, contact='palm'|'tips'|'grip', z=depth)` lands the palm on the target
   (measured within 1-3 px). Targets slightly out of reach make the figure lean, squat and bend. Real misses go to
   `a.misses` as (t, side, units): **check it**. The clip tool fails loudly on any miss. Other contact clips:
   - `hand_over(t0, side, other, 'eyes'|'mouth')`;
   - `hold_hand(t0, side, other, other_side)`, where the taller one's arm hangs and the child reaches up;
   - `smooth_hair(t0, side, other, n)`;
   - `head_to(t0, target, part)`, which brings an eye to a peephole, a mouth to an ear or a face into a hand.
6. **Props never teleport and never duplicate.** One `PropTrack(name, x, y, px_per_cm)` per prop that rests or changes
   hands. It draws itself only while resting, and the hand draws it while held. Use `a.pick_up(track, t0, side)`,
   `a.put_down(track, t0, side, x, y)` and `a.give(track, t0, side, other, other_side)`. The jump at pick-up is under 1 px.
   `px_per_cm = height / (m * 100)` at that depth. For props a character simply holds, use `a.hold_prop(name, side, t0, t1)`.
7. **Doors face the camera in our sets**, so to look through a peephole or talk into the mail slot, a character turns their
   back (turn about 1.6-2.0) and `head_to`s it. A profile at a camera-facing door looks along the wall, not through it.
8. **A hand in front of another figure** (for example Mom's hand smoothing June's hair from behind her): draw the figure, the
   other figure, then `CH.draw_arm(pen, who, side, pose, x=, y_feet=, height=)` on top.
9. **No scared jiggle as filler.** Act the line. Faces have `too_still`, `wrong_smile`, `little_girl`, `terror`, `haunted`,
   `determined`, `proud`, `sleep`, plus the older set. `a.eyes_shut(t0, t1, squeeze)` is for counting,
   `a.hum(t0, t1)` for the jingle, and `talk([(t0, t1, text)])` for **character lines only**.

## Beat map: script beat to clips
| beat | clips / calls (see `tools/cast_clips.py` for each staging) |
|---|---|
| 1987 parade, eggs, the photo, into the woods | `bunny87_parade_wave`, `bunny87_kneel_egg` (`give` egg), `bunny87_walk_hand` (`hold_hand` + `walk`) |
| sunrise, she walks out humming with a golden egg | `laurie87_sunrise` |
| at the treeline: slow wave, stops, points past us, head tilt | `bunny_treeline_wave_point` (`wave(slow=True)`, `point_at`), `bunny_head_tilt_bust` |
| Dad walks out with a flashlight | `dad_flashlight_treeline` (`torch_pos3` beam) |
| Grandma's porch light; Grandma teaches the knock | `grandma_porch_light`, `grandma_knock` (`knock_pattern((2,3,2))` returns knock events) |
| Mom humming all week | `mom_hum_bust` |
| close the curtains, run upstairs | `narr_close_curtains`, `narr_run` (`run()`; footsteps events) |
| June waves at the window; "That's Mister Bunny..." | `june_window_wave`, `june_whisper` |
| Mom in the doorway, smiling: "I told you not to look..." | `mom_doorway_smile` |
| the peephole; the egg on the doormat; the door a crack; the egg opens; the ring | `narr_peephole`, `narr_egg_open` (`PropTrack` + `pick_up` + `open_egg`, `egg_open` event), `narr_ring_stare` |
| burn barrel in oven mitts | `mom_egg_mitts_barrel` (hand shape `oven`) |
| "You opened it." She takes the ring, stares, pockets it | `mom_takes_ring_pockets` (`give`, then the pocket) |
| 1:40, the mail slot | `bunny_mail_slot` (outside), `june_kneel_slot`, `mom_slot_hair_hum` (closes the slot, `smooth_hair`, "Bedtime, bunny", hum) |
| Mom in the armchair facing the back door | `mom_armchair_backdoor` |
| 2:47: I wake up | `narr_couch_wake` |
| attic: June with the diary and the tiny dress; Mom in the dark corner | `june_attic_diary`, `mom_attic_corner` |
| 4:30, footsteps on the stairs, the hatchet knocking | `bunny_stairs_hatchet` (`climb` + `drag_hatchet`: `hatchet_thunk` per step) |
| the bathtub, my hand over her mouth | `narr_tub_june` (`hand_over(... 'mouth')`) |
| the crayon drawing slides under the door | `crayon_drawing` (`CH.draw_crayon_drawing`; prop `drawing` in a hand) |
| sunrise: Mom unlocks with a key, scratched to ribbons, smiling | `mom_scratched_smile` |
| the Bunnyman dead at the bottom of the stairs, the head half off, "Mama." | `bunny_dead_wide`, `bunny_dead_face` (`unmask`, `mama`, `dead`) |
| Mom kneels with the little yellow dress, hand over June's eyes, June counts | `mom_kneel_dress_eyes` |
| I pull June away and push my own face in: "Six. Seven." | `narrator_swap` |
| on my knees, looking at myself holding June's hand, humming | `narrator_new_holds_june` |
| hospital: police, doctors; June in my lap: "I know it's you" | `cops_notes`, `doctor_nurse`, `mom_hosp_lap_whisper` |

## Sound events the cast emits (in `a.events`)
| event | when |
|---|---|
| `footsteps_wood_inside` / `footsteps_porch` | `walk`; `run` (kind `run`, +1 dB); `climb` (kind `stair`) |
| `knock_door` | `knock_pattern`, with params group and index (kind `table` for Grandma's table) |
| `hatchet_thunk` | `climb(..., hatchet=side)`: the hatchet head hitting each step |
| `egg_open` | `open_egg`: the plastic egg splitting |

These join the older events (`breath`, `cloth_rustle`, `paper`).

## Speed and limits
- **Speed:** a v3 figure at 960x540 renders at about 0.04 s per frame of a clip, scene included. The 2560x1440 bench is in the
  report.
- **What draws where:** the cast draws in a 1920x1080 design space. Faces scale their line weight with on-screen size, so
  eyes stay open and readable on wide shots.
- **Perspective:** feet forward of the body plane (seated) land slightly below `y_feet`, which is correct perspective.
  The furniture's front edge belongs there.
