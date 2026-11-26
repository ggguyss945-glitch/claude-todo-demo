# CAST: "If a Girl Is OBSESSED With Being Your Only Friend... DON'T WRITE YOUR NAME"

## The family and helpers: `characters_obsession.py`, see `OBSESSION_API`
Run in the `characters` namespace by the one exec line at the very end of characters.py (after Evie's); `import characters as CH`. Every id is a v3 cast entry on the existing people rig (faces, lip sync, poses, `look_at`, `reach_to`, props, `kneel_down`, `seated`, `walk`, `run`, `climb`, `swing_ride`), so all of their clips work. This film takes the plain names; the older films' ones live on as `adam_ice`, `lina_ice`, `mom_buttons`, `sam_walls`. Times below are film seconds from `_work/align/timeline.json` (key shots to the line tags; the times move if the voice edit changes).

### Who's who
| id | look | notes |
|---|---|---|
| `adam` | **Adam, 12.** One family face with Mom and Lina (warm light-olive skin, near-black hair, brown eyes). A messy dark mop (`shaggy`) that falls into his eyes, thick straight brows that do the acting, a guarded low upper lid, a long face for his age, thin and a little hunched. An oversized grey hoodie (white strings, kangaroo pocket), dark joggers, scuffed white trainers. His phone is always within reach. | Expressions: `adam_guarded` (Monday, "Art."), `adam_lonely` (lunch alone, the bracelet), `adam_scared` (the lit screen, the window, the stairs), `adam_ashamed` (the reveal, telling Mom), `adam_steady` (the kind clear no, Mrs. Rahman, the coda). State `ob_chalk` 1: the hoodie sleeves dusty chalk-white from cuff to elbow (Monday); `ob_tired` grows through the week. |
| `adam_night` | The same boy in navy long-sleeved pyjamas and socks (bed, window, stairs, kitchen at midnight, the door). | Phone glow: `phone_type` sets `ob_glow`; light the face with `light=dict(under='#cfe0ff', under_a=150, key=-0.3)`. |
| `adam7` | **Adam at 7, on the tape.** Rounder, a big happy grin, the same mop cut short; a sunny yellow tee, light trousers, blue trainers. | Sings "Stick Like Glue": `talk` on line `adam7_me_and_you` + `sing_sway`. |
| `danny` | **Danny, 12.** A head shorter than Adam, soft and round-faced, pink cheeks; sandy-brown hair combed to the side; round dark-rimmed glasses; a mustard jumper over a white collar; navy trousers. A chewed blue pen tucked behind his right ear (hides when he faces away). Bare left wrist. | `danny_shy` (eyes off Adam: `not_meeting`), `danny_kind` (the gentle explanation, "Can we sit here?"). |
| `danny7` | **Danny at 7, on the tape.** The same glasses and side parting, a sky-blue tee, the green-and-gold woven bracelet on his left wrist (`bracelet=1`). | |
| `mom` | **Mom, 40s.** Warm, tired, sharp. Near-black hair pulled straight back into a low ponytail, tired lower lids (`bags` 0.6), straight brows that go firm; a dusty-blue long-sleeved work shirt (collar, buttons, two pockets) over a cream tee, charcoal trousers, flats. | `mom_warm`, `mom_watchful` (the look a beat too long, fork down), `mom_tired` (dawn, the phone), `mom_firm` (Save / Block / Report, the look at the door). State `ob_knuck` 1: red raw knuckles on every scrubbing morning and at midnight. |
| `lina` | **Lina, 7.** Adam's eyes in a round face, two low pigtails with yellow bobbles, a straight fringe; oversized lilac pyjamas with soft-yellow stars, sleeves over her hands, legs pooling on her socks. Crayons and drawings. | `lina_earnest` (at his door, under the bulb), `lina_sing` (the healed song). Never creepy. |
| `rahman` | **Mrs. Rahman, 50s,** the counsellor: calm, unshockable. Warm brown skin, kind dark eyes with smile lines; a **navy hijab** framing her face (a lighter under-cap edge at the brow, the drape over neck and chest, folds from the temples; the face window follows every head turn, so the face reads in 3/4 and profile); a long grey jacket over a cream blouse, navy trousers, flats; a teal lanyard with her ID card. | `rahman_calm`, `rahman_kind`, `nod`, `listen_tilt`. |
| `kofi`, `sam` | Danny's new friends (silent). Kofi: tall, close crop, steel-blue zip jacket. Sam: smaller, black curls, an orange tee. | Background reactions: `look_at`, `kind_smile`, `talk`. |
| `caretaker` | 60s: grey hair and moustache, a weathered kind face; navy bib overalls (straps, brass buttons, a pencil in the bib pocket) over a grey work shirt; work boots. | `squint_up` + a hand shading his eyes under the floodlight; `roller` paints the square. |
| `danny_mom` | Only ever the silhouette at her upstairs window, phone to her ear. | `draw_silhouette(pen, 'danny_mom', ..., rim='#e8c88a')` with `phone_to_ear`. |
| `adam_grown` | Grown Adam's hands only: a charcoal hoodie (his grey one, grown up). | `draw_arm`; `ob_tips` 1 = "My fingertips went white". |

Heights to scale (`height_px(id, ppm)`, feet to crown): caretaker 1.76 m, mom 1.66, danny_mom 1.65, rahman 1.62, kofi 1.56, adam 1.52, sam 1.49, danny 1.45, evie 1.40, adam7 1.22, lina 1.17, danny7 1.17. Seated people: stage in 3/4 (`turn` +-0.5) at the table edge (hands on the top reach without leaning).

### Beat map: clips to call
| time (tag) | beat | clip(s) |
|---|---|---|
| 49.2 `now_he_ate` / 51.4 `chewed_blue_pen` | Danny at lunch with Kofi and Sam; the pen | all `seated`; Kofi `talk`, Sam and Kofi `look_at` Danny, Danny `kind_smile`; a CU of the pen behind his ear |
| 54.7-66.4 `at_seven_on`, `adam7_me_and_you` | the tape: swings, singing; the bracelet | `adam7` / `danny7` `seated(seat_y)` + `swing_ride(t0, t1, pivot, L)` + `sing_sway`; `adam7.talk_lines(L, who='adam7')`; `CH.draw_swing(..., part='back')`, figure, `part='front'` |
| 68.9 `dannys_wrist_was` | the bare wrist | `danny` insert of the left wrist (no bracelet) |
| 74.1-81.7 `monday_mom_held` ... `she_looked_a` | Mom holds up the hoodie; "Art."; the look | mom `hold_hoodie(t0)` (sleeves chalk-white), `expr('mom_watchful')` from 80.1; adam `ob_chalk` 1, `adam_guarded`, `talk` on `adam_art`, `look_at` away |
| 127.6-136.6 `then_danny_crossed`, `danny_my_mom_wrote` | Danny crosses the hall with the card, hands it over without meeting his eyes; Mrs. Rahman in her doorway nods | danny `walk` + `CH.PropTrack('rule_card', ...)` held, `give(track, t, 1, adam, -1)`, `not_meeting(t, adam)`, `talk`; rahman `look_at` Danny, `nod(t)` |
| night of Wed (`the_dark_screen` 156.1) | Adam in bed typing / the screen lights | adam_night `seated(mattress_y)` + `phone_type(t0, t1)` (duvet drawn over his legs by the set) |
| 169.9 `below_me_our` | he looks down from his window, then ducks | adam_night `look_down_at(t0, street_pt)`, `duck(t)` |
| "Bucket by the door. Mom on the phone, knuckles red." / 183.1 `mom_i_know_ill` | Mom on the phone in the kitchen | mom `ob_knuck` 1, `phone_to_ear(t0, t1)`, `talk`; `CH.draw_bucket(pen, x, y, ppc)` by the door |
| 208.3 `inside_my_locked` | the locker, the bracelet | adam `reach_to` the handle (release before the door finishes its swing), `pick_up(PropTrack('bracelet_real', ...))` on the shelf, `look_at` it, `adam_scared` |
| 254.5 `i_typed_mine` | he types his password | adam `seated` + `phone_type` |
| 279.8-284.9 `mrs_rahman_the`, `rahman_just_checking_i` | Mrs. Rahman at her open door | rahman `rahman_kind`, `talk`, `nod`; adam `walk` past |
| "Mom's car. Red light." ... 306.8 `next_red_light` | in Mom's car at red lights | mom `seated` + `drive(t0, t1, g10, g2)` (grips from `CH.draw_steering_wheel`), eyes on the road; adam `seated`, `look_at` his window |
| 314.8-319.6 `i_found_danny` ... `danny_what_song` | "You told her our song?" / "What song?" | adam `talk`, `adam_scared`; danny `blink`, `danny_shy` -> `puzzled`, `talk` |
| 321-365 `at_sunset_i` ... `i_ran` | to the square; runs home | `walk`, `run(t0, t1, x0, x1, surface='outside')` |
| "Clank. Floodlight." | the caretaker squints right at them | caretaker `expr('squint_up')`, `reach_to` a flat hand to his brow, light `dict(rim='#f4f0d8', rim_a=130)` |
| 379.8-407.2 `saturday_dinner` ... `adam_youre_my_only` | dinner: fork down, "Anything...", phone into his lap; Lina's drawing; he types | mom `seated`, fork `hold_prop` -> `set_down(t, 'fork', 1, xy)` at 395.0, `mom_watchful`, `talk`; lina `hold_prop('lina_drawing')` out to him; adam `phone_type`, `adam_ashamed` |
| 414.3-420.9 `lina_knocked` ... `i_looked_down` | Lina at his shut door; she points up at his window | lina `knock(t, n=2, side=+1)`, `talk`; `point_at(t, window_pt)` (the bible: "There's a girl at our door" heard through the door) |
| 465.7 `my_feet_moved` | top of the stairs, one step, two, halfway | adam_night `climb(t0, t1, 0, -rise, 4, run)` from the landing |
| 471.9-478.5 `lina_under_the`, `lina_it_says_your` | Lina under the bare bulb holds up the card | lina `reach_to` up-front with `prop='rule_card'` + `hold_prop`, `talk`; bulb light `dict(rim='#fff1c8', rim_a=110, side=1)` |
| 493.6 `i_stepped_over` | he steps over the chalk | adam_night `walk` + `step_up(t, side=1)` starting 0.3 s before the foot reaches the letters |
| 496.5-503.6 `the_kitchen_light` ... `i_told_her` | Mom still dressed, red knuckles; he tells her | both `seated` 3/4 at the table edge, adam hands on the table, `adam_ashamed` -> `adam_steady`; mom `listening_soft`, `nod`, `ob_knuck` 1 |
| 531.9 `mom_saved_every` | Save, Block, Report | mom `phone_taps([t1, t2, t3])`, `mom_firm` |
| 566.8-587.6 `mom_didnt_look` ... `adam_i_hope_you` | at the open door, side by side; "No." | mom `mom_firm`, `look_at` Evie on the doormat; adam `adam_steady`, `talk`; nobody touches |
| 600.8 `at_dawn_we` / 607.6 `lina_me_and_you` | scrubbing together; Lina sings | mom `scrub(t0, t1, pt)`; lina `scrub(..., amp=10)` + `sing_sway` + `talk` |
| 616.7-625.5 `monday_i_told` ... `rahman_that_was_brave` | in her office chair | rahman `seated`, `listen_tilt`, `nod(t, n=2)`, `rahman_kind`, `talk`; adam `seated`, `adam_steady` |
| 640.4 `the_caretaker_painted` | paints the square over (from behind) | caretaker `roller(t0, t1, ground_pt)` standing about 1 m from it; `CH.draw_roller(pen, a, t, ppc)` |
| 643-664.5 `weeks_later_danny` ... `danny_i_crossed_it` | "Can we sit here?"; the shoebox; the card | danny `talk`; shoebox `CH.draw_shoebox(pen, x(t), table_y, ppc, open_)` pushed with both palms, released, slides; adam palms on the lid; danny `danny_kind` + `talk` |
| 670.6 `my_fingertips_went` / 678.6 `i_scrubbed_it` | grown hands: white fingertips, the phone; scrubbing ONLY | `adam_grown` `draw_arm` with `ob_tips` 1, `phone_ob`; `scrub_brush` |
| cold-open replay | Danny's mom at the lit window | `draw_silhouette(pen, 'danny_mom', ...)` + `phone_to_ear` |

### Props (`PROPS3`, cm) and free functions
`phone_ob` (Adam's dark phone), `phone_ob_lit` (screen glow spilling round it), `phone_mom` (teal case), `scrub_brush`, `bucket` (held by the handle), `hoodie_held` (grey, sleeves chalk-white to the elbow), `crayon`, `rule_card` / `rule_card_back` (cream, purple handwriting, a blue scribble at the top; the full-screen card is the UI's), `bracelet_real` (green and gold, no chalk; Evie's chalky one is `evie_bracelet`), `fork`, `lina_drawing` (a crayon drawing of the two of them, LINA in the corner). Free: `draw_bucket(pen, x, y_base, ppc, water, brush, wet)`, `draw_shoebox(pen, x, y_base, ppc, open_)`, `draw_roller(pen, actor, t, ppc)`, `draw_silhouette`, `draw_lina_drawing`.

### Sound events the family emits
`phone_tap` (typing, Save / Block / Report), `brush_scrub` (one per stroke), `paint_roll` (one per roller pass), `cloth_rustle` kind `grab` (the hoodie), plus the rig's own `footsteps_*` (walk, run, the stairs: kind `stair`), `knock_door` (Lina), `swing_creak` (the tape swings).

### Sheets and tests
`cd film && python3 tools/cast_family.py sheet faces selftest strips` (about 4 min for everything; `strips <group>` for one group). Outputs in `_work/cast/`: `family_sheet.png` (everyone to scale, 18 face busts, states, props), `family_faces_640.jpg` (faces at the size they must read), `family_strips_<group>.jpg` (adam_a, adam_b, adam_c, mom_a, mom_b, lina, danny, help, misc: 27 actions on stand-in sets with a printed reach/feet report), `family_check.jpg`. Self-test: 13 ids x 5 views x 3 detail levels, about 28 ms per full body.

## Evie (this film's villain): `characters_evie.py`, see `EVIE_API`
Run in the `characters` namespace by the one `characters_evie.py` exec line at the end of characters.py; `import characters as CH`. One id, `'evie'`, for every form: her look follows `EVIE_ARC` on the film clock plus pose fields. All of it is our own design (story bible). Nothing comes from the mood stills.

**Design.** About 12 and 1.40 m, shorter than Adam. She has a round, freckled kid's face with a gap-tooth grin (two front teeth and a gap) and pale grey-blue eyes that open a little too wide. Her two dark braids start from a centre parting, go back behind the ears and come forward over her shoulders onto her chest. They are tied with faded red ribbon bows (`KEEPING_RED` #b0584f, the Keeping Square's red; the sets use the same constant). She wears a long-sleeved white blouse with a high round collar under an ankle-length navy pinafore (bib, straps, crossed straps at the back, two buttons, and a bib pocket with chalk dust on its lip), navy leggings and white sneakers. A worn chalk stub is always in her right hand: `pose.e_stub`, drawn even when a clip forgets it. Chalk dust sits on her fingertips and a little always drifts down, more each night (`e_dust`), and it also gathers on her hem. She is modest in every form: arms, legs and neck are always covered. She never touches anyone, and nothing she does is romantic.

**Her arc (`EVIE_ARC`, automatic, like `WINKS_ARC`).** Each stage starts at a narration line (`EVIE_CUES`). The film sets the real times once: `CH.set_evie_arc({'wed': t, 'r1': t, ...})` or `CH.evie_arc_from_lines(lines)`. Until then, word-count placeholders are used. Stages change on cuts (transition 0). To override one window, use `a.stage(t0, 'r5', t1)`.

| stage | starts at | smile (`e_chalk`) | blinks | braids (`e_unravel`) | dust | night flatness (`e_flatn`) | head tilt |
|---|---|---|---|---|---|---|---|
| mon | "That day, a new girl sat behind me." | her real gap-tooth smile | yes | neat | 0.12 | 0 | 0 |
| wed | "Wednesday, at my shoulder... she didn't blink." | real, held too long | **never again** | 0.08 | 0.25 | 0.30 | 9 |
| r1 | Rule number one. | real | no | 0.16 | 0.35 | 0.45 | 10 |
| r2 | Rule number two. | chalk line just past the corners (0.25) | no | 0.30 | 0.45 | 0.52 | 11 |
| r3 | Rule number three. | mid-cheek (0.42) | no | 0.42 | 0.55 | 0.60 | 12 |
| r4 | Rule number four. | wider (0.58) | no | 0.55 | 0.66 | 0.68 | 13 |
| r5 | Rule number five. | almost at her ears (0.80) | no | 0.70 | 0.78 | 0.76 | 14 |
| r6 / r7 | Rule number six / seven. | ear to ear (1.0) | no | 0.84 / 0.92 | 0.9 / 1.0 | 0.84 / 0.88 | 15 |
| drain | "Evie was on our doormat, smiling ear to ear." | ear to ear | no | 0.95 | 1.0 | 0.92 | 12 |

- **The chalk smile** is a smooth white chalk line drawn on the face surface over her mouth. The real mouth is gone and the line's ends curl up. It is never a cut: no red, no teeth. When she talks (`talk()` / `m_open`), the line parts in the middle like a drawn mouth, with a dark fill and no teeth.
- **Night:** call `a.night()` in night shots. Her colour then goes chalk-flat by `e_flatn`. Under a lit hall, use `a.night(amount=0.4)` so the drain still reads.
  Review fix: the night flatness goes to a mid grey-blue (skin about 0.70 at most, never near-white), the chalk smile has a dark under-stroke (#2c3040) with shadow curls at its ends and stays on the front of the face (ends curling up the cheeks toward the ears), and the phone glow under her chin is weaker (alpha 120). Only the drain goes to chalk-white. The letterbox fingers hang from a narrow palm and wrist at the slot, taper, bend at two knuckle joints each and arch at the tip as they write.
- **Braids:** they unravel from the bottom up. The bow droops, loses a loop, and from about R5 hangs untied. Flyaway hairs increase.

**Movement vocabulary (clips; each has a clear start and end, and her feet stay on the ground).**
- **NORMAL:** `bounce(t0, t1)` (on her toes; she never leaves the ground), `laugh_away(t0, dur, side)`, `wave_hi(t0, t1)` (her left hand, the grin), plus the arc's normal blinks.
- **OBSESSED:**
  - Looks: `tilt_hold(t0, deg)`, `lens_lock(t0, t1)` (eyes on the lens, dead still), `hold_smile(t0, t1)`.
  - Phone: `phone_glow(t0, t1, look='up')` (phone under her chin, face lit from below; for the background before Adam notices her), `type_phone(t0, t1)` (`phone_tap` events).
  - Closeness: `one_inch(t0, t1, toward)` (the film places her one inch away), `block_wide(t0, t1)` (arms wide across a gate or doorway; never touching).
  - Bracelet and swing: `hold_out_bracelet(t0, t1, target=None)`, then `seated(seat_y)` + `swing_ride(t0, t1, pivot, length)` + `swing_state(t)` / `draw_swing`, and `sing_song(t0, beat)` (or `talk` on the sung take).
- **CREEPY:**
  - Flat: `flat_drawing()` (she IS the chalk girl lying on the ground), `lie_flat(t0, dur, flat_k)` (she folds down into the ground plane, hinged at her feet, and becomes the drawing).
  - Moving: `slide_flat(t0, dur, to, scale_to)` (a smooth slide that leaves a faint smear), `stand_from_ground(t0, dur)` (the drawing peels up into her with a rubbery overshoot).
  - `neck_up(t0, dur, length, dx, grow)`: a smooth rubbery stretch toward his window, with no joints and no crack.
  - Expressions: `evie_flat` (flat delight), `evie_hope` ("Write your name?"), `evie_hurt` ("Don't you trust me?").
- **DRAIN:** `drain_away(t0, flat_dur, dust_dur, wind=±1)`. Her colour drains to flat chalk-white, then the wind lifts her away as dust (`e_drain` 0..1). The dust leaves from the downwind edge and the top first. What is left stays upright: she never crumbles or falls.
- **The setup's chalk girl:** `CH.draw_chalk_girl(pen, x, y, h, flat_k=k)` draws a child's chalk drawing with two braids and bows, a pinafore, the stub, and a smile that runs past the face's outline. It stands up into Evie with an actor on `flat_drawing()` + `stand_from_ground()`.

**Letterbox, stub, prints (free functions, placed on the set's points).**
- **Fingers:** `f = CH.LetterboxFingers(slot=(x, y, w), door_base=(x, y), floor_quad=[nl, nr, fr, fl], text='ONLY', box=(u0, v0, u1, v1), size_cm=(w, d), px_per_cm=k, t_in=t, letter_times=[tO, tN, tL, tY], t_out=None)`. The four fingers are chalk-white and far too long, with soft knuckle creases, rounded tips and no nails. They come through the slot, run down the door, creep across the floor and write in Adam's curly hand.
  - Calls: `f.draw_chalk(pen, t)` on the floor layer (the letters stay written), `f.draw(pen, t)` over it, `f.tip(t)`, `f.events`.
  - For R7, use `text='ME', axis='v'` with the box ending at Mom's chair and `t_out=None` (they stop there).
- **Stub:** `CH.StubDrop(t0, slot_xy, floor_y, stop_xy, px_per_cm)`: it falls, bounces once and rolls to the bottom stair. Calls: `.draw(pen, t)`, `.events`.
- **Slot smile:** `CH.draw_slot_smile(pen, (x, y, w, h), t, amount, hum)`: only her chalk smile shows in the slot, ear to ear, shivering while she hums.
- **Writing and marks:**
  - `CH.chalk_word(pen, 'ONLY ME', quad, box, u)`: the same handwriting for the ONLY ME tracker, ADAM and DANNY.
  - `CH.draw_sneaker_print(pen, x, y, px_per_cm, angle, squash)`: one white chalk print, pointing the way she went.
  - `CH.draw_chalk_stub(pen, x, y, px_per_cm, angle)`.
- **Props:** `chalk_stub`, `evie_phone`, `evie_phone_screen`, `evie_bracelet` (green and gold, chalk dust).

**Beat map (key every time to the timeline's line and word times).**
| beat | clips |
|---|---|
| "someone had chalked a little girl. Two braids. A smile that didn't stop." | `draw_chalk_girl(..., flat_k)` in the square (or an actor on `flat_drawing()`) |
| "a new girl sat behind me... faded red ribbons" / "Hi! I'm Evie. Like forever." | stage mon, `expr('evie_grin')`, `wave_hi` + `talk`, `bounce` |
| Tuesday, the locker, the crisps | `bounce`, `laugh_away` |
| "Wednesday, at my shoulder... she didn't blink." / "favourite person" | `one_inch`, `hold_smile`, `lens_lock`, `tilt_hold`, `talk` |
| R1 messages; "Under the streetlight, Evie smiled up" | `type_phone` / `phone_glow` cutaways; `night()` + `look_at(window)` + `hold_smile` |
| "Evie lay down flat, like a chalk drawing... and slid away." | `lie_flat(t, 0.8, flat_k)` then `slide_flat(t, 1.6, to)` |
| R2 "one inch from my shoulder" / "Only me?" / "Just past the corners." | `one_inch`, `hold_out_bracelet` (optional), `talk`; the night shot shows stage r2 |
| R3 "Best friends share passwords. Don't you trust me?" | `expr('evie_hurt')` + `talk`; her phone with `reach_to(..., prop='evie_phone_screen')` |
| R4 the red lights ("She never ran.") | standing still, `lens_lock`, `hold_smile`; she is there on cuts, never moving |
| "on the swings, she sang my song" | `seated` + `swing_ride` + `sing_song` / `talk` on the sung take |
| "The chalk slid out... and stood up. Evie. Washed in red." / "Arms spread across the gate." | `flat_drawing` + `slide_flat` + `stand_from_ground`; red sunset rim light; `block_wide`; `expr('evie_flat')` + `talk` |
| "She was flat chalk again." | `lie_flat(t, 0.35)` (fast) |
| R5 "Evie's lips moved" at the dark window | `night()`, `lens_lock`, `talk` (the chalk line parts) |
| "Up... and up... toward my window." | `neck_up(t, 3.0, 900, grow=0.2)` from above |
| R6 the letterbox: "O. N. L. Y.", humming, the stub | `LetterboxFingers('ONLY', letter_times=...)`, `draw_slot_smile(hum=1)`, `StubDrop` |
| R7 "Chalk fingers wrote M... E... toward the kitchen" | `LetterboxFingers('ME', axis='v')` stopping at the chair |
| "on our doormat, smiling ear to ear" / "Write your name?" | stage r7 or drain, `night(0.4)`, `hold_smile`, `expr('evie_hope')` + `talk` |
| "Only me. I'm here, I'm he-" / "Her colour drained to chalk-white..." | `talk` / `sing_song`, then `drain_away(t, 1.6, 2.8, wind)` |

**Sound events she emits.** Each event is a dict `{t, name, gain_db, pan, params, who: 'evie'}` in `a.events`, `f.events` or `stub.events`.

| event | kinds and level (dB) | suggested sound |
|---|---|---|
| `chalk_scrape` | write -13 (one per stroke, `dur`); creep -22 (fingers coming or going); slide -15; flatten -18; rise -14; stretch -24 (the neck: a long soft drag, never a crack) | chalk on a board / floor |
| `chalk_tap` | tap -16 (`chalk_tap(t)`); beat -18 (`sing_song(taps=True)`); land -16; stop -16 (the stub against the stair) | one soft chalk tap |
| `chalk_stub_drop` | drop -10, bounce -18 | a small chalk stick on boards |
| `chalk_roll` | -19, `dur` | a chalk stub rolling |
| `chalk_dust_whoosh` | -12, `dur` (the drain) | a soft airy whoosh with powder |
| `phone_tap` | about -22 | screen taps |
| `swing_creak` | about -22, at each end of the swing | a chain creak |

**Sheets and checks** (`python3 _work/cast/evie_sheets.py [sheet] [strips slide neck letterbox drain swing]`):
- `W/cast/evie_sheet.png`: every form, the smile stages R1-R7 side by side, the drain steps, the letterbox fingers and the slot smile.
- `W/cast/evie_strip_*.jpg`: 12 frames at 8 fps of each action, with its events printed.
- Self-test: `python3 -c "import characters as CH; CH._selftest_evie()"`.
- Speed (2560x1440, a 1200-px figure): 50 ms against 40 ms for Owen. The drain dust frame takes about 200 ms.


## (reference) Buttons film: `characters_buttons.py`, see `BUTTONS_API`
Run in the `characters` namespace after `characters_walls.py` (the `_BUTTONS_SRC` exec line in characters.py). Use
`import characters as CH`. Old ids kept: `mom_walls`, `owen_dummy`. All designs are ours (story bible), none from the mood stills.

- **Sheet / faces / strips:** `python3 tools/cast_buttons.py [sheet] [faces] [details] [strips [mom|owen|blank_a|blank_b|misc]]`
  -> `_work/cast/cast_sheet.png`, `faces_640.jpg`, `details.jpg` (contact crops), `strips_<group>.jpg` (8 frames per action,
  stand-in scenery; prints reach misses and foot gaps). Self-test: `python3 characters.py --selftest` (buttons checks last;
  the older films' checks run with their own `mom` / `owen`).
- **Ids** (height `CH.height_px(id, ppm, tall=0)`): `owen` 1.45 m (blue hoodie, brown eyes) / `owen_coat` (green coat,
  broken zip, open) / `owen_pj`; `mom` 1.65 m Nadia (open oatmeal cardigan, pens in the pocket, teal tee, messy bun +
  pencil, freckles, reading glasses with laptop glare, headset, slippers); `blank1` (form 1: Mom's look, cardigan buttoned
  to the throat, reading glasses over button eyes) / `blank1_shades` (sunglasses, the car); `blank2` (form 2: glossy bun,
  smooth grey-tinged skin, shiny black buttons, button eyes, never blinks, big smile; grow her per scene with
  `tall=CH.BLANK_TALL['r1'|'r3'|'r4'|'r4_micro'|'r5'|'sill']`); `blank3` (form 3, drawn by `_draw_blank3`: height =
  FLOOR TO CEILING px); `dunn` 1.74 m; `mensah` 1.83 m; `son` 1.40 m; `narrator_b` (hands only: `CH.draw_arm`).
- **Looks (pose fields, set with `a.set(t0, t1, fade, **kw)`):** `faded` 0..1 (Owen rubbed out: cool, translucent,
  still clear; animate back to 0 for "like a photo developing"); `CH.draw(..., reflection=True)` + `refl_hide` 1 = gone
  from the microwave door; `pgrey` 0..1 (headset lady pencil grey, also on busts); `glare` 1 = glare OFF (default on);
  `circles` 1 = the two black circles; `specs` 0 = glasses off (`a.glasses_off(t0, side=-1)`: green eyes);
  `hs_off` 1 = headset off; `shades` / `shades_dn` 0..1 (lower the sunglasses: buttons); `default_head` 1 for one
  frame (`a.flicker(t)`); expressions `busy`, `puzzled`, `listening_soft`, `quiet_sure`, `too_sweet`, `too_wide`.
- **Mom:** `typing(t0, t1, kb_xy, side=0)` (laptop or tablet; `key_tap` events); `one_finger(t0, t1, side, toward)`;
  `snap_photo(t0, aim_xy, side, dur)` -> (shutter t, events); `phone_to_ear` + `cry` (existing);
  `press_headset(t0, t1, side)`; `headset_off(t0, side)` + `glasses_off(t0, side=-other)`; `walk` / `turn` (step between);
  `hug(t0, child, t1)` (kneels, palms on his back); `wind_box(t0, t1, side)` (prop `music_box`, pose.crank);
  `set_down(t0, prop, side, xy)` -> release t.
- **Owen / son:** `typing` with `hold_prop('tab_back', -1, t0, t1)`; `point_at`, `crouch(t0, 1.6, t1, dur=0.25)` (duck),
  `wave`, `walk(t0, t1, 0, dx, facing=-1)` (step back; walk/run take OFFSETS from the placed x), `run`;
  `write_marker(t0, t1, side, board_xy)`; `rise_to(t0, button_xy, side, dur)` (stops 2.5 cm short, `tik`);
  `drop_out(t0, x_to)` (fast crouch, then runs to design x); son `tablet_down(t0, bed_xy)` -> contact t, then
  `look_at` up + expr `kind_smile`.
- **Blank 1 / 2:** `wave(..., slow=True)` + `look_at` the WRONG window; `hand_on_glass(t0, t1, side)` both hands;
  `listen_tilt(t0, None, side, angle)`; `seated(seat_y)` (chair, windowsill) + `typing`; `talk` for the song.
- **Form 3** (`a = CH.Acting('blank3', height=floor_y - ceiling_y).place(x, floor_y)`, `a.set(-1e9, None, 0, b3_face=-1)`
  faces left): `b3_unfold(t0, dur)` (from a low crouch in the gap BESIDE the fridge: draw the fridge after her);
  `b3_hand(t0, side, target, t1, dur)` (FINGERTIPS to a point / callable / (actor, part); slow wrong-way elbows; `tik`);
  `b3_hold_coat(t0, coat_fn, t1, dur, face)`; `b3_lunge(t0, from_xy, to_xy, dur, t1)` (fingers sweep the counter);
  `freeze(t0, t1)`; `b3_collapse(t0, dur)` (folds to `draw_flat_cardigan`); points: `CH.b3_point(a, t, part)`.
  Keep her fingertips >= 2.5 cm from his skin (target his hood / the coat, never his face).
- **The red coat:** `CH.draw_red_coat(pen, cx, cy, h, buttons, open_, full, part, top_out, top_to)`; `CH.coat_on(owen, t)`
  -> (cx, cy, h) at his shoulders; `CH.coat_pts(cx, cy, h)` (shoulders, top button). Worn: draw `part='back'`, Owen,
  then `part='front'`. Buttons close from the bottom; the top one can never be drawn closed. After `drop_out` set
  `full` 0 and keep the coat where her hands hold it.
- **Car arm (R3):** `CH.draw_long_arm(pen, window_xy, hood_xy, ext 0..1, t, px_per_cm)` (bends where arms don't bend,
  fingers tap; stops 3 cm short; ext back to 0 folds it in). **Dunn:** `hold_sign(-1e9, None, side=-1)`,
  `radio_up(t0, t1, side)`, `shelter(t0, owen, t1, side, toward)`. **Mensah:** `take_notes(t0, t1)`,
  `read_board(t0, board_xy, t1, then=(mom, 'eyes'))`.
- **Props (cm):** `headset`, `music_box`, `stop_sign`, `notepad`, `tab` / `tab_back`, `button`; existing `cell`,
  `walkie`, `marker`, `pencil`, `glasses`. `CH.draw_flat_cardigan(pen, cx, floor_y, w)`.
- **Open:** form 3's arms cannot lean past their reach (stage her within ~1.5 m); the folded start is a crouch, not
  flat; the sting cuffs are heavy at very close range; Mom's glare is fixed (no per-shot sweep yet).

---

# (reference) Walls film cast: "If Your Little Brother Says Someone Lives In The Walls... DON'T LAUGH"

## Walls film: `characters_walls.py`, see `WALLS_API`
Run in the `characters` namespace after `characters_ice.py` (the `_WALLS_SRC` exec line in characters.py). Use
`import characters as CH`. Old ids kept: `mom_bunny`, `dad_ice`, `theo94`.

- **Sheet / strips:** `python3 tools/cast_walls.py [sheet] [faces] [strips [names]]` -> `_work/cast/cast_sheet.png`,
  `faces_640.jpg` (four close-ups at 640x360), `strip_<name>.jpg` (8 frames each; stand-in scenery; prints reach misses
  and foot gaps). Self-test: `python3 characters.py --selftest` (walls checks run last).
- **Ids** (draw height `CH.height_px(id, ppm)`): `sam` 1.50 m (green tee) / `sam_pj`; `theo` 1.16 m (blue dinosaur
  pyjamas); `mom` / `mom_pj`; `dad` 1.87 m in THE red buffalo-check flannel (day one) / `dad_tee` / `dad_pj`; `pell`
  1.88 m masked (Dad's flannel, grey trousers, grey socks, long pale hands with plaster-dust fingertips, stoop 0.28);
  `pell_bare` (grey stubble, tired); `dabrowski` (late 60s, teal cardigan, glasses); `reyes`; `officer_w`.
- **The mask** (`pell`): original latex hound over his own head: pale fawn dome, worried brow folds, heavy half-closed
  rubber lids over dark holes with HIS eyes in them (they blink), red droopy lower lids, long muzzle, wet black nose,
  his own teeth in the mouth slit (moves with `talk`), long ears hanging in along the jowls that swing a beat late
  (`pose.ear_sw`, set automatically), grey tape on his left ear, a loose rubber hem and back seam. `pose.mask_lift` 0..1
  pulls it up off his face; `where(t, 'mouth'|'nose'|'crown')` are the MASK's points while it is on.
- **Shared tilt:** `WALLS_TILT` (h_tilt 21, nod 0.12); `a.walls_tilt(t0, t1, dur)` for Dad's habit; `pell.doorway(t0, t1)`
  = the same tilt, arms hanging, dead still, stoop straightened (his doorway silhouette = Dad's: sheet row 2).
- **Pell acting:** `back_away(t0, t1, steps)` (legs only: shrink height / raise y_feet for the hall depth);
  `tuck_blanket(t0, a, b, dur, knees, t1)` (kneels, both palms along the blanket edge a->b, returns press time);
  `shush(t0, t1, side)` (index across the mask's mouth); `crawl(t0, t1, x0, x1, facing)` (hands and knees, side view;
  `crawl_thump` events); `slide_panel(t0, side, grip, dx, dur)` -> `panel_dx(t)` for the set; `cuffed(t0, t1)` (hands
  together at the lap, steel cuffs + chain) with `seated(curb_y, hands=None)`; eye at the crack: `head_to(t0, pt,
  'eye_l')` or the insert `CH.draw_head_at(pen, 'pell', P, x, y, px_per_unit, 'eye_l')`.
- **Family:** `sam.carry_hush(t0, theo, t1)` + `CH.draw_carry_walls(pen, sam, theo, t, light, blanket=True)` (hand over
  his mouth, the blanket hanging); `sam.shake_awake(t0, t1, dad)` (dad lying: `lie(..., face='up')`; `where()` now
  follows lying figures); `sam.flip_switch(t0, side, xy)` -> flip time; `dad.read_note(t0, t1, side)` (prop 'note',
  kept in the hand after), `dad.laugh(t0, dur)`, `dad.sigh(t0, dur)`; `mom.phone_to_ear(t0, t1, side)` + expr
  `terrified_call`, then `mom.phone_to(t0, side, theo)`; `theo.sing(intervals)` (= talk, lip sync);
  `theo.phone_to_mouth(t0, t1)` if he holds it himself.
- **Neighbour / police:** `dabrowski.offer_pie(t0, dur, facing)` (both hands; props `pie` / `pie_r`);
  `reyes.lift_mask(t0, pell, dur)` -> time the face is clear; the mask then hangs from her hand (`hound_mask`).
- **Open:** lying figures are the old front view turned 90 deg (stage bed shots close); the crawl's legs read best in
  side view; profile mask is weaker than front / 3/4 (prefer 3/4 for his face beats).

---
# (reference) Ice Cream film cast

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
- Review 1 (picture): form 3 is floor to CEILING at her own plan point (film.figure: the set's ceiling projected there), her
  neck runs along the ceiling with a wide bend and her shadow is thrown up onto it; tapered knit cardigan tube, 9 small shiny
  buttons, warmer skin, `too_wide` is now a closed-lips far-too-wide smile; `eye_shade` (pose) hides button eyes in the
  brow's shadow; `b3_elbow_out` bends her elbows away from Owen in the climax.
