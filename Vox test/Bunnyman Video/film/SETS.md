# Bunnyman film sets (sets.py + sets_bunny.py)

"If The Bunnyman Asks You To Close Your Eyes... DON'T COUNT TO SEVEN". All new code is `sets_bunny.py`, executed at the end
of `sets.py` (so everything is `import sets as ST; ST.ob_living(...)`). The older films' builders are unchanged. The module
docstring of `sets_bunny.py` is the API reference; this file is the staging guide.

## How to run
```
python3 tools/sets_sheet.py                    # every set / variant / insert / rule card (1280x720) + contact_sheet.jpg,
                                               #   index.json (each variant's anchors with plan + screen data), floorplan.jpg
python3 tools/sets_sheet.py --only kit_,ins_   # a subset (names containing any of these)
python3 tools/sets_sheet.py --stage            # staging test stills: cast figures placed only from the Spots -> stage_*.jpg
python3 tools/sets_sheet.py --frame            # + framing check at every camera's widest move -> frame_check.json / .jpg
python3 tools/sets_sheet.py --bench            # + bench_2560.json (2560x1440, 1 OpenCV thread, warm caches, 2.5 %/s push)
python3 tools/sets_sheet.py --dummy            # the dummy film's sets (regression); --delivery, --police likewise
```
Everything lands in `film/_work/sets/`. `ST.plan_map(path)` redraws the floor plan with every camera.

## The house: one floor plan (metres)
x = right when you face the back of the house, y = from the front wall (Orchard Road, y 0) back toward the woods, Y = up.
Ground floor Y 0, upstairs `UP_Y` 2.85, attic `ATTIC_Y` 5.45, the yard `GROUND_Y` -0.45. The house is 10 x 10 m (x -5..5).
Every view is a camera (`BView`, any yaw: 0 looks toward the woods, 90 east, 180 toward the road) placed in this plan, so
a cut keeps every wall, door, lamp and chair where the last shot had it. `_work/sets/floorplan.jpg` shows it all.

| where | plan | what is there |
|---|---|---|
| living room | x -5..-1.4, y 0..5.8 | couch under the front window (centre (-3.3, 1.22), facing the back) with the floor lamp at its left end, coffee table (-3.3, 2.42), braided rug, fireplace on the west wall (y 2.1..3.9), Mom's wingback (-3.3, 4.55) with its back to the couch, facing the back door, the little lamp + side table by it, side window (west wall, y 4.25..5.25), bookcase |
| hall | x -1.4..1.3, y 0..5.8 | front door x -0.85..0.05 on y 0 (peephole 1.52 m, brass mail slot 0.95 m, deadbolt, chain, knob), console table, coat hooks, stairs on the east side x 0.35..1.3 rising from y 0.9 (15 risers of 0.19 m, treads 0.26 m) to the corridor at y 4.54; opening to the living room on x -1.4 (y 1.5..3.1); doorway to the kitchen on y 5.8 (x -1.2..-0.3) |
| kitchen | x -5..1.3, y 5.8..10 | back door x -3.75..-2.85 on y 10 (opens in), window over the sink x -1.95..-0.75 (sill 1.02), harvest-gold fridge (-4.6, 7.75, facing east) with the rules under the bunny magnet, table + 4 chairs under the pendant (-0.75, 7.75), wall clock on the front wall, Grandma's porch-light switch by the back door; opening to the living room y 5.8, x -4.25..-2.35 |
| back porch / front porch | x -4.7..-2.0, y 10..12.1 / x -3.1..1.9, y -2.4..0 | Grandma's porch light by the back door; the lantern by the front door, the doormat (the egg) |
| upstairs corridor | x -3.8..5.0, y 4.54..5.8 | June's door (x 0.4..1.2) faces the head of the stairs; the bathroom door (x -2.0..-1.25) next to it on y 5.8; Mom's and the narrator's doors on y 4.54; the attic door at the west end; the east window (sunrise); hall table |
| June's room | x -0.4..2.6, y 5.8..10 | window x 0.55..1.65 on y 10 looking at the treeline, bed along the east wall (2.08, 7.9), moon nightlight on the nightstand, dresser, closet (the new yellow dress) |
| bathroom | x -2.9..-0.4, y 5.8..8.6 | the pink built-in tub along the back wall (-2.0, 8.22; the kids sit IN it), pedestal sink, toilet, hex mosaic floor; the door's old knob, thumb-turn bolt, keyhole |
| attic | floor x -5..5, headroom y 1.45..8.55 | bare bulb, Mom's toy chest (LAURIE), boxes, Grandma's rocker in the dark corner, round gable window, stair opening at the west end |
| yard | y 10..46 | the shed + woodpile + chopping block, the burn barrel (-7.6, 26.3), swing set, clothesline, old fence at y 37.5, the treeline y 40 |
| front | y < 0 | Orchard Road (y -9..-16), the dead end, woods round it; patrol cars at y -15.3 |

Unbuilt (no camera may look there): the ground floor east of x 1.3, the upstairs bedrooms in front of y 4.54, the rooms
east of June's. Separate plans: Holloway Woods + the old railroad bridge (`ob_woods`), Holloway State Hospital
(`ob_hospital`), Main Street 1987 (`ob_parade`).

## Staging data (nothing floats, nobody stands on furniture, props stay on surfaces)
- `sp.anchors[name]` -> `Spot`: `.x, .y` = design px of the feet / point at the home camera, `.depth` = layer depth,
  `.ppm` = design px per metre there, `.height` = px of a 1.85 m adult, `.X, .Yp, .Y` = plan position, `.kind`
  ('stand' | 'seat' | 'kneel' | 'lie' | 'surface' | 'point'), `.turn` = the cast `turn` the set expects there,
  `.seat_y` (seats) = design y of the seat top, `.note`. Plain names are the main room's; spots of rooms seen through
  openings are also under `'room.name'` (e.g. `ob_living(...).anchors['kitchen.window']`).
- **Depth-to-scale rule:** `ppm = S / depth`; a figure of real height m is `m * ppm` px tall where its feet are
  (`CH.height_px(who, spot.ppm)`). `sp.ppm_at(x, y)`, `sp.floor_y(x, y)`, `sp.spot(x, y, Y)` for any plan point,
  `sp.pick(sx, sy)` (screen -> plan), `sp.turn_for(x, y, fx, fy)` (facing a plan direction -> cast turn),
  `sp.walkable(x, y)` (inside a floor, clear of every furniture footprint), `sp.shadow(x, y)` (contact shadow layer),
  `sp.light_kw(X, Y, h)` (Layer tint / dim so a figure takes the room's light), `sp.order_at(X, Y)` (draw order:
  furniture between the camera and the figure is drawn over it).
- **One call does all of it:** `lay, a = ST.stage_figure(sp, 'mom', 'armchair', expr='too_still')` -> the Layer and the
  `CH.Acting` (height, feet, facing, seated / kneeling / lying from the spot's kind, light, order). It warns when a seat
  is seen nearly front-on (|turn| < 0.4, unless the spot says `legs_hidden`, like the tub): seated cast figures read as
  standing from the front (cast limitation), so
  seat people where the seat is at 3/4: `liv_wide2` / `liv_couch` for the couch, `liv_wide` / `liv_back` for the
  wingback, `kit_table`, `bath_tub` (the tub's near wall hides the legs), `hosp_table`.
- Doors face the camera in these sets: at the peephole, mail slot, fridge, window a figure has its back to us
  (`turn` ~ -1.9, given by the spot) and `head_to`s the point spot (`peephole`, `mail_slot`, `fridge_rules`, ...).
- `_work/sets/index.json` lists every variant's anchors with kind, screen x/y, depth, ppm, plan position, turn, seat_y.
- Main anchors: living: `armchair`, `couch_left/mid/right`, `couch_lie`, `window_front`, `curtain_front_l/r`, `room_mid`,
  `coffee_top`, `endtable_top`, `sidetable_top`, `mantel`, `fireplace`. Hall: `door_inside`, `peephole`, `peephole_eye`,
  `mail_slot`, `mail_slot_kneel`, `deadbolt`, `chain`, `knob`, `hall_mid`, `hall_back`, `stairs_foot`, `step1..step14`,
  `stairs_bottom_body`, `console_top`, `switch`. Kitchen: `fridge`, `fridge_rules`, `sink`, `counter`, `table_top`,
  `kchair0..3`, `back_door`, `back_door_knob/bolt/out`, `porch_switch`, `window`, `kitchen_mid`. Upstairs: `stair_head`,
  `hall_mid/east/west`, `june_door`, `june_doorway`, `bath_door`, `bath_knob`, `bath_keyhole`, `attic_door`, `mom_door`.
  June: `window`, `sill`, `bed_edge`, `bed_lie`, `bed_side`, `dress`, `room_mid`, and in 'out' `bunny_treeline` /
  `bunny_clearing`. Bath: `tub_left`, `tub_right`, `door_inside`, `gap`, `gap_floor`, `lock`, `keyhole`, `knob`.
  Attic: `chest_floor`, `chest_top`, `corner_seat`, `mid`, `stair_top`. Yard: `treeline`, `treeline_deep`,
  `porch_top`, `yard_mid`, `yard_near_trees`, `barrel`, `barrel_top`, `chopping_block`, `window_june`, `porch_light`.
  Front: `doormat`, `porch_door`, `cop_porch`, `walk`, `road`. Woods: `deck`, `under_bridge`, `flashlight`, `bank_far`,
  `path`. Hospital: `bed_edge`, `bed_lie`, `chair`, `calendar`, `window`, `seat0..2`, `table`, `door`. Parade:
  `float_deck`, `float_side`, `photo`, `curb_l/r`.

## Screen direction (from the camera table; the plan map draws each camera's field of view)
| camera | looks toward | screen-right is | camera | looks toward | screen-right is |
|---|---|---|---|---|---|
| liv_wide | front-west | back-west | kit_back / kit_door | back (woods) | east |
| liv_wide2 | front-west | back-west | kit_fridge | west | back |
| liv_back | front (road) | west | kit_table | back-west | back-east |
| liv_chair | back (woods) | east | up_hall | west | back |
| liv_couch | front-west | back-west | up_west / up_from_bath | east | front |
| liv_window | front | west | up_bath | back-west | back-east |
| liv_hall | west | back | up_june | back | east |
| hall_door / slot / peep / bottom / top | front | west | june_window / june_out | back (woods) | east |
| hall_in / hall_foot | back | east | june_door | front | west |
| bath_door / gap / lock | front | west | bath_tub | back | east |
| yard_woods / treeline_close | back (woods) | east | yard_house | front (road) | west |
| front_house / porch_egg | back | east | peephole | front | west |
So: the woods / back door are screen-right in the living-room wide and couch shots (Mom's wingback faces right), the front
door is straight ahead in the hall shots, and June's door is straight ahead at the top of the stairs.

## Sets and variants
| builder | views | variants (all lights are level specs: number, f(t) or dict(flick=, out=, on=, off=)) |
|---|---|---|
| `ob_living(view)` | wide, wide2, back, chair, couch, window, hall | lamp, chair_lamp, hall, kitchen, curtains (0 closed .. 1 open, or f(t)), blanket, moon, back_door |
| `ob_hall(view)` | door, in, foot, top, slot, peep, bottom | hall, console, porch, upstairs, living, kitchen, door (degrees or f(t)), flap, bolt, chain, knob, tod 'dawn' |
| `ob_upstairs(view)` | hall, west, bath, june, from_bath | upstairs, attic_gap, june_gap, bath/june/attic_door, wrecked 0..1, tod 'dawn' |
| `ob_june(view)` | window, door, out, bed | nightlight, hall, lamp, curtains, bed 'made/turned/empty/over', dress |
| `ob_bath(view)` | door, tub, gap, lock | gap, gap_col (DAWN_C at 6:12), bath_light, lock 0..1 or f(t), knob, key, feet=f(t), slam, door |
| `ob_attic(view)` | chest, corner, mom | bulb, chest 'open/closed' |
| `ob_kitchen(view)` | back, fridge, table, door | kitchen, porch, smash / smash_t (the window explodes), back_door / crash_t (crashes open), rules, mud, clock, locked, porch_switch, tod 'memory' |
| `ob_yard(view)` | woods, house, wide, close, barrel | tod night/dawn/sunrise87/day87, back_light (Grandma's porch light), kitchen, june_light, fire, egg (melt) |
| `ob_front(view)` | house, porch, egg, peephole | front_light, egg, egg_rattle=f(t), police=dict(mode, speed, strength 0.55), tod 'dawn' / 'blue' |
| `ob_woods(view)` | bridge, under, path | flashlight (Dad's, still on), tod 'day87' (the 1987 search) |
| `ob_hospital(view)` | room, bed, visit, table, corridor | blinds, month, circle |
| `ob_parade(view)` | street, store, photo | float_y (or f(t): it drives), vhs (tape look; draw `ST.vhs_stamp(cv, t)` in the HUD for the date) |
| `ob_insert(name, prop_kw, motion)` | see `ST.INSERTS_B` | rules (hl=n, show=n), courier, egg (rattle), egg_halves (k_open, ring), egg_gold, egg_fire (melt), ring, ring_inside, diary, diary_crayon, diary_flip, diary_cursive, diary_last, drawing (slide), dress_old, dress_new, hatchet (hit=f(t)), flashlight, switch (on / flip), clock (time=(h, m), kind 'digital'), calendar, slot (flap, eyes), peep, lock (lock, key, knob) |
| `rule_card_bunny(cv, n, t)` | rule cards 1..7 | the police-style card (engine.hud.rule_card) with an icon per rule; texts in `ST.RULE_CARDS` match the narration word for word |

Grades: `ob_night`, `ob_dark`, `ob_dawn`, `ob_ext`, `ob_memory`, `ob_vhs87`, `ob_sunrise87`, `ob_hospital`, `ob_police`;
inserts use `ins_lamp`, `ins_dark`, `ins_dawn`, `ins_memory`, `ins_hosp` (no bloom on paper).

## Draw order and depth
Outside (order 900) -> rooms seen through openings (80 + i) -> the main room's shell (50) -> each furniture piece as its own
layer at its real depth (seats split into the parts behind and in front of the occupant) -> animated layers. Figures use
`sp.order_at(X, Y)`. A shell is one plate at the room's middle depth; where a camera drift could slide it off the far end of
a floor (the bathroom door) a backfill plate sits behind it.

## Engine changes (all opt-in or invisible)
- `engine/post.py`: `post['vhs']['tube']` (default True): False = the tape look without the rounded CRT mask (1987 parade).
- `engine/scene.py`: a cached layer keeps only its painted part (`_crop_to_content`); pictures are unchanged, memory per
  piece of furniture drops from a whole frame to its own size, so the 700 MB layer cache no longer thrashes at 2560
  (a living-room frame went from 2.5 s to 0.17 s).

## Results
- 126 variants (every set, view, light / time-of-day state, insert and rule card) rendered to `_work/sets/*.jpg`,
  `contact_sheet.jpg`, `index.json`; `floorplan.jpg` (the plan with all 54 cameras); `stage_sheet.jpg` (13 staging tests).
- Framing check: 78 views at the four corners of their `cam_env` (+-8 px handheld) and the deepest push, over
  magenta (blends counted too): no holes > 0.02 % (fixed on the way: the egg view's and the bathroom gap view's plates,
  the floor under the bathroom door).
- Bench at 2560x1440 (warm caches, 1 OpenCV thread, 2.5 %/s push): mean 0.174 s/frame over 125 variants, worst
  0.505 s (`front_police`: two light bars + flash), then `hall_slot_open` 0.34, the parade views ~0.3; budget 0.6 s.
  A set's first frame (building its caches) takes 2-5 s.

## Polish pass (film staging review)
- Eight point anchors had their plan y and their height swapped (the back door's `back_door_knob` / `back_door_bolt` /
  `switch`, the bathroom's `bath_knob` / `bath_keyhole` and, inside, `lock` / `knob` / `keyhole`): they pointed into the
  hall at attic height. Fixed in `KitchenRoom.spots`, `UpstairsHall.spots`, `Bathroom.spots`; `fridge_rules` now sits on
  the drawn sheet (0.86 m). `tools/validate.py` (ANCHOR) checks every anchor against the floor levels.
- Interior views at night put a dark veil (`NIGHT_VEIL`) over the outside layer seen through their windows; the '_out'
  views (the yard through June's window as the picture itself) keep their exposure. `ob_living('wide2')` sees the front
  yard through the front window. `ob_june(moon_dir=(az, el))` can place the moon in a window's frame.
- June's closet door hangs the new dress on its room-side face (`art_b`).

## Known limits
- Seated figures seen front-on read as standing (cast). Use the 3/4 views listed above; `stage_figure` warns.
- `hall_top`: the stairwell is narrow, its west wall fills the right of frame; stage people on the runner.
- The lock / slot / peephole views through the room model are context shots; for readable hardware use the inserts.
- The police dawn keeps a pink haze (`tod='blue'` is darker and moodier). The ring-on-palm hand is simple.
- Serif / sans text uses the system Liberation fonts (`/usr/share/fonts/truetype/liberation`); the hand / crayon /
  cursive / blackletter faces are in `fonts/extra` (OFL, licences beside them).
