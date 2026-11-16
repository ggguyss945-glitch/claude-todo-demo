# CAST: "If Your Doctor Calls At 3 AM... DON'T ASK WHAT THEY FOUND"

The cast lives in `characters.py`. This film's cast and staging tools are in `characters_doctor.py`, which `characters.py`
runs in its own namespace at import, after `characters_bunny.py`. Use everything as `import characters as CH`. The older
casts (`mom`, `narrator`, `grandma`... of the Bunnyman film) are unchanged; this film's people have their own ids. The
Bunnyman film's CAST.md is in the Bunnyman Video project.

- **Self-test:** `python3 characters.py --selftest` (about 30 s). It runs the older films' checks, then this film's:
  every id in 6 views full and close, Doctor Later in 5 perches x 6 views with his feet on the floor, tape stages x faces,
  his reach (pinch within 7 px of targets up to 1400 px away), the ticket tear, the tape coming off monotonically, no lip
  sync for him, his palm on the narrator's wrist (3 px), the handset pick-up (0.5 px jump), Ruth's palm on Milo's mouth,
  Halverson's fingers on Milo's wrist, Ruth sitting down with her feet on the floor.
- **Sheets:** `python3 tools/cast_sheets.py [names]` writes `_work/cast/*.jpg`: `later_likeness` (beside the owner's photo
  and the fan drawing), `later_turn`, `later_states`, `later_tape`, `lineup`, `lineup2`, `turn_family`, `turn_doctors`,
  `faces_ruth`, `faces_milo`, `faces_narrator`, `faces_halverson`, `faces_others`, `mouths`, `props`, `staging`.
- **Acting clips:** `python3 tools/cast_clips.py [names] [--fps 60] [--strip-only] [--review]` writes 46 clips at 960x540
  to `_work/cast/clips/<name>.mp4`, each with an 8-frame `<name>_strip.jpg`; `clips.json` (or `$CLIPS_JSON`) holds each
  clip's sound events and its contact report (reach misses, foot gap). The scenery there is a flat stand-in.

## Who's who (draw height = `CH.height_px(who, px_per_m)` at the same depth)
| id | look | notes |
|---|---|---|
| `later` | **Doctor Later, the Waiting Man.** The owner's creature: an impossibly thin black body folded on a small chair, a hunched ribbed back, a long ribbed neck reaching forward, long jointed spider limbs with bony knees and long pointed feet, long thin black fingers, a small face under a tall pointed cone. The narration's adaptations: the whole head (face and cone) wrapped round and round in old yellowed medical tape with one thin gap and two pale patient eyes in dark sockets; a white coat gone grey (lapels, pens, a blank cracked badge, frayed hem) hanging off the narrow shoulders, its sleeves far too short; a clipboard with no paper (a torn scrap under the clip); a click pen. 2.9 m standing; never stands; never lip-syncs. | Own 3D rig in centimetres (`_dl_rig`), any yaw. Pose: `dl_seat`, `dl_knee` (0 = the photo's knees .. 1 = above his head), `dl_spread`, `dl_tape` (1 -> 0 strip by strip: the face's strips first, the cone from the tip), `dl_face` (0 his own pale face, 1 Grandpa, 2 a stranger, 3 a little girl, 4 Ruth, 5 the narrator: grey, crossfading), `dl_flinch`, `dl_roof`, `dl_click`, `dl_rock`, `dl_ticket` (text), `dl_layer` ('back' / 'front': sandwich an armrest or car seat). Hands rest `dl_lrest` / `dl_rrest`: 'lap' (clipboard), 'pen', 'floor' (flat on the carpet), 'knee', 'arm'. |
| `ruth` / `ruth_sick` | **Grandma Ruth, 70s.** Short silver set curls, pale grey-blue eyes, reading glasses on a gold chain (`pose.specs` 1 on the nose / 0 hanging on the chain), a sage cardigan buttoned to the top, a white blouse collar, a charcoal skirt (it drapes over her knees when she sits), stockings. `ruth_sick`: pale at sunrise. | Expressions `stern`, `stern_afraid`, `grief_still`, `pale_hidden`, `asking`. |
| `ruth79` | Ruth at 40, 1979: a dark brown flipped bob, a quilted rose housecoat with a round collar. | On hold at the wall phone; the coffee at sunrise. |
| `grandpa79` / `grandpa_ghost` | Grandpa, about 50: brown hair greying, a moustache, a brown V-neck cardigan over a checked shirt, grey trousers, socks. The ghost: the same, drained grey and still. | `a.gone(t0)`: eyes close, head settles, breath stops (gentle: he looks asleep). |
| `milo` / `milo_sick` / `milo_jeans` / `milo_er` | **Milo, 7.** A light-brown mop with a cowlick, big brown eyes. Green dinosaur pajamas; `milo_sick` has cracked lips; `milo_jeans` a T-rex T-shirt and dinosaur-patch jeans (`pose.sag` slides them down); `milo_er` a gown with monitor leads (`pose.iv` 1: the IV in his hand). | `thirsty`, `sleepy`, `dazed`, `brave`, `kid_grin`; `drink`, `breathe_fast`, `sag` + `hold_up`. |
| `milo22` | Milo at 22: lean, a runner's tee and shorts, a glucose sensor on his left upper arm, the phone (`cell_glucose`). | |
| `narr14` | **The narrator at 14** ("I"; never said if boy or girl): dark brown shaggy hair with curtain bangs, a soft jaw, hazel eyes, an oversized burgundy hoodie, grey sweatpants, socks. | `asking` -> `asking_hard` as the questions grow. |
| `narr29` | The narrator at 29, a pediatrician on nights: the same face, tired and kind, ceil-blue scrubs under a white coat, a badge with a dinosaur sticker, a stethoscope, a watch. | `tired_kind`. |
| `halverson` / `halverson_rain` | **Doctor Anna Halverson**, pediatrician, 40s: dark-blonde messy bun, warm brown eyes, freckles; blue scrubs with a coffee stain, pens in the pocket, her badge clipped crooked with two dinosaur stickers, a watch on her left wrist. `_rain`: an olive raincoat open over the scrubs, hair soaked flat, wet streaks. | `careful_smile`, `exhausted`, `pleading`, `set_jaw`, `focused`, `fierce_kind`. Drawn warm and competent. |
| `mom_rn` | Mom, a night-shift nurse: dark low ponytail, wine scrubs, a lanyard and badge, a watch. | `warm`, `calm_firm`, `set_jaw`. |
| `er_nurse`, `er_doctor`, `medic`, `medic2`, `cardio`, `chest_man` | A calm, firm nurse (navy scrubs); a doctor (white coat over green scrubs, glasses); paramedics (navy, reflective bands, radio, patch); the cardiologist (grey bob, glasses, white coat; `cup`); the man with chest pain (work jacket). | |
| `ghost_chest`, `ghost_side`, `ghost_teen`, `ghost_girl` | The waiting room's people: an old man in an overcoat and tie, a woman in a cardigan, a teenager in a hoodie, a little girl in a coat too small for her (sleeves halfway up, buttons straining). All drained grey, still, eyes open (`waiting`). | `ticket_hold(t0, text)`, `hand_on(t0, 'chest' / 'side')`. |

Heights: Doctor Later 2.90 (folded: the cone tip about 2 m up), Grandpa 1.78, Halverson 1.68, Mom 1.66, narrator 1.62
(1.70 at 29), Ruth 1.60 (1.62 in 1979), Milo 1.22 (1.80 at 22).

## Doctor Later: staging
```python
a = CH.Acting('later', seed=1, height=CH.height_px('later', ppm)).place(chair_x, floor_y)
a.perch(seat_y, 'armchair')            # 'plastic' | 'armchair' | 'bench' | 'car' | 'low'; knee=, hands=('lap', 'pen'), props=
a.click_pen([t1, t2, ...])             # -> 'pen_click' events
a.look_at(t0, (narr, 'eyes'))          # slow, patient head turn (never darts)
a.tilt_head(t0, 18.0, 1.4)             # "He tilted his head."
tt, ev = a.tear_ticket(t0, -1, slot_xy, 'MILO', offer_to=target)   # reach across the room, tear ('ticket_tear'), hold it out
a.take_wrist(t0, -1, narr, 1)          # then draw him, the narrator, and CH.draw_later_arm(pen, a, t, -1) on top
a.count(t, 1)                          # "One..." head dips, fingers press ('pulse_count')
ev = a.loosen_tape(t0, t1, 1.0, 0.4)   # strip by strip ('tape_peel' each) with a flinch
a.faces([(t, 1), (t2, 2), ...])        # the faces under the tape
a.flinch_light(t)                      # as if a question were light
a.bend_to_roof(roof_y)                 # the car: the head bends over against the roof
```
- `a.reach_far(t0, side, target, t1, dur, z, shape, arc)` lands his pinch on any world point; past arm's length the arm
  unfolds (a second elbow opens). `a.reach_to` on him does the same. Shapes: 'flat', 'relaxed', 'pinch', 'offer' (the
  ticket between two fingers), 'grip' (round a wrist), 'pen', 'clip', 'reach', 'claw', 'point'.
- His props never leave or jump: when the clipboard hand reaches away the clipboard stays leaning against his knees
  (drawn from his rest pose); the pen stays in the pen hand (it is in his fingers when he takes the wrist). Do not
  clear `hl_prop` / `hr_prop` mid-shot unless a hand puts the thing somewhere.
- `a.where(t, part)` / `CH.later_point(a, t, part)`: 'head', 'eyes', 'mouth', 'cone_tip', 'chest', 'lap', 'hand_l/_r',
  'tips_l/_r' (the pinch), 'wrist_l/_r', 'elbow_l/_r', 'shoulder_l/_r', 'knee_l/_r', 'foot_l/_r'.
- Close-ups: `CH.draw_bust(pen, 'later', cx, cy, scale, pose)` (scale 1 = his face 600 px; use 0.25-0.6 so the cone fits);
  `CH.later_bust_place(a, t, cx, cy, scale)` gives the matching (x, y_floor, height) to stage targets in the same frame.
- Far: `CH.draw_later_far(pen, x, y, h, pose, t, lamp=(x, y), flicker=0..1)` (the bus stop). The empty chair:
  `CH.chair_rock(t, t_left)` (deg) for the set; the same value in `pose.dl_rock` rocks him with his chair.
- Rules for him: never standing; never lip-sync (`talk` leaves his mouth shut: say his lines with a head dip or a pen
  click); look slow; tape strips come off only when the narrator asks; the faces only after the face's strips are off.

## People: staging (the Bunnyman film's tools all still work: place, look_at, reach_to, sit_on / seated, kneel_down, walk,
run, pick_up / put_down / give with PropTrack, hand_over, head_to, hum, eyes_shut...)
- `receiver_to_ear(t0, t1, side, tilt_out, toward=other)`: the wall phone's handset at the ear; with `toward` it comes out
  between her ear and theirs ("tilted it so I could hear"). The cord: `CH.draw_coil_cord(pen, *CH.receiver_cord_end(a, t,
  side), base_x, base_y, px_per_cm)`. Use a `PropTrack('receiver', ...)` on the cradle and `pick_up` / `put_down`.
- `tap(t0, side, target, n)` ('card_tap'), `pull_cord(t0, side, jack)` ('cord_yank'), `strike_match(t0, side)`
  ('match_strike'; 'match' -> 'match_lit', the box in the other hand), `slide_under_door(t0, side, track, door_x, floor_y)`
  ('paper_slide'), `write_marker(t0, t1, side, paper)` ('marker_write'), `dial(t0, side, keypad, n)` ('dial_beep').
- `take_pulse(t0, side, other, other_side)`: two fingers on the inside of the wrist, the watch arm up, eyes on the watch.
- `carry(t0, child)` + `CH.draw_carry_child(pen, carrier, child, t)`: the child's hips in the carrier's arms.
- `drive(t0, t1, g10, g2)` with `CH.draw_steering_wheel(...)` (returns the grips; draw the arms over the wheel with
  `CH.draw_arm`); `CH.draw_wheelchair(...)` returns its handles for a pusher's `reach_to`.
- `hand_over(t0, side, other, 'mouth' | 'eyes')` lays a closed, cupped hand ('cover' shape: no gaps between the fingers,
  so it never reads as a black glove on a face).
- `rock(t0, t1)` (floor rocking + humming), `breathe_fast(t0, t1)` ('breath_fast'), `drink(t0, t1, side)` ('gulp'),
  `gone(t0)`, `glasses(t0, on)`, `sag` / `hold_up`, `hand_on(t0, 'chest' | 'belly' | 'side')`, `ticket_hold(t0, text)`.
- Sitting on something high (the exam table, the ER bed edge): `a.set(-1, None, 0.01, perch=1.0, sit=1.0)` and place the
  actor at the surface's y: the legs dangle. Floor sitting (`sit_floor`) and seats read only at |turn| >= 0.5.
- Props (PROPS3, centimetres, same size in a hand and on a surface): receiver, card, card_back (signed "Doctor Later"),
  match, match_lit, matchbox, note (results + marker), marker, ticket (`pose.dl_ticket` text; '' = ink gone), bottle,
  mug, cup, vial, cell (a phone at the ear draws as its dark back on the cheek), cell_glucose, keys; the older clipboard.

## Beat map: script beat -> clips (tools/cast_clips.py)
| beat | clips |
|---|---|
| cold open: the tall man folded in a plastic chair, the pen, "Take a seat" | `later_wait_plastic`, `later_likeness_profile` |
| 1979: on hold; Grandpa sits to wait; the coffee at sunrise | `ruth79_phone_hold`, `grandpa79_sits_armchair`, `ruth79_coffee_sunrise` |
| Milo thirsty, jeans falling off; the clinic, the blood test | `milo_drink`, `milo_jeans_sag`, `halverson_clinic_blood` |
| sundown: the medicine cabinet, the card | `ruth_cabinet_tap` |
| rule 1: the receiver tilted; hung up; the cord pulled; Halverson at 3 AM | `ruth_phone_tilt`, `ruth_hangup_cord`, `halverson_office_phone` |
| rule 2: the receiver down like a sleeping baby | `ruth_receiver_counter` |
| rule 3: "I'm so thirsty", the hand over his mouth | `milo_thirsty_mouth` |
| rule 4: peephole, knock and plea, the note, the match, the window, the car, the bus stop | `narr_peephole`, `halverson_porch_plead`, `ruth_door_refuse`, `halverson_write_slide`, `ruth_burn_note`, `narr_window`, `halverson_car_phone`, `later_bus_stop_far` |
| rule 5: rocking on the floor; "that's what the voice told you" | `ruth_rock_milo`, `narr_tells_ruth` |
| rule 6: him in the armchair; the grey people; the ticket | `later_armchair_front`, `ghosts_row`, `later_tear_ticket` |
| rule 7: the wrist and the count; the questions and the tape; the faces; the card | `later_take_wrist_count`, `narr_asks_tape`, `later_faces`, `narr_pull_free_card` |
| the rescue: carry, run, pulse, drive, the mirror, the back seat, the ER | `narr_carry_milo`, `halverson_run_steps`, `halverson_pulse_car`, `halverson_drive_mirror`, `later_car_backseat`, `mom_wheelchair_run`, `nurse_chest_man`, `empty_chair_rocking`, `milo_er_bed` |
| after: Milo at 22; Ruth's ticket; Mom dials; the cardiologist; the narrator at 29; the hall | `milo22_run_phone`, `ruth_sick_ticket`, `mom_dials`, `ruth_cardio_coffee`, `narr29_desk`, `hall_last_chair` |

## Sound events the cast emits (in `a.events`)
`pen_click`, `pen_scratch`, `ticket_tear`, `tape_peel`, `flinch`, `pulse_count` (a marker, no sound of its own),
`card_tap`, `cord_yank`, `match_strike`, `paper_slide`, `marker_write`, `dial_beep`, `breath_fast`, `gulp`, `card_tear`,
plus the older `knock_door`, `footsteps_*`.

## Results (this pass)
- Self-test passes (numbers above). All 46 clips render at 60 fps with 0 reach misses; the planted foot never leaves the
  floor except in the runs' flight phase (`halverson_run_steps`, `mom_wheelchair_run`, `milo22_run_phone`: about 28 px
  at the top of a stride) and the narrator up on tiptoe at the peephole (heels 16 px up, toes down, on purpose). Every strip was checked by eye
  for contact, eyelines, feet and props.

## Limits and open problems
- Doctor Later's front views fold his arms like a mantis (elbows out at the seat); his likeness is closest in profile and
  3/4 (see `later_likeness.jpg`); the coat the narration needs makes him lighter than the all-black reference.
- The faces under the tape are the cast's own heads, greyed and clipped into his face; in very close shots make the
  crossfades quick (0.4-0.6 s) so no in-between reads as a double face.
- The stand-in scenery in the clips is not the sets: in the film the armchair's arm and the car seat sit between his
  far and near limbs (`pose.dl_layer`).
