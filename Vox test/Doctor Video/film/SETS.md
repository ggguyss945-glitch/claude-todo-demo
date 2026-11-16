# SETS.md: the sets of "If Your Doctor Calls At 3 AM... DON'T ASK WHAT THEY FOUND"

Code: `sets_doctor.py` (exec'd inside `sets.py` after `sets_bunny.py`; its module docstring and `DR_API` are the API
reference). Every name is `dr_* / DR_* / D_*`; use `import sets as ST`. Stills, contact sheets, the floor plan and the
stage tests live in `_work/sets/` (`index.json` holds every still's anchors with plan and screen data).

```
python3 tools/sets_sheet.py              # all 130 Doctor stills (1280x720) + contact_sheet.jpg + index.json + floorplan.jpg
python3 tools/sets_sheet.py --only er_   # just the variants whose name contains er_
python3 tools/sets_sheet.py --stage      # cast placed only from Spots -> stage_*.jpg + stage_sheet.jpg
python3 tools/sets_sheet.py --frame      # widest-camera-move edge check;  --bench  draw time at 2560x1440
```
Variants are listed in `tools/sets_sheet_doctor.py` (DOCTOR list: name, builder call, note) and are the best examples of
every state below. `--bunny / --dummy / --delivery / --police` render the older films' regressions.

## 1. Builders, views and states

| builder | views | states / keyword arguments |
|---|---|---|
| `dr_living(view, state, tod, ...)` | now/1979: wide, chair, window, window_bus, door, sunrise; wait: wide, front, rows, him, grandpa, side, machine | state 'now' / '1979' (harvest gold) / 'wait' (the waiting room); tod night / sunrise; lamp, ceiling, headlights, car, hall, door (deg), coffee, keys, clock=(h,m), tubes=[4 levels], sign, tv, ticket ('MILO'), tear, serving ('1979'), rain |
| `dr_hall(view, ...)` | door, back, livdoor, peep, floor | hall, porch, kitchen, living (light levels), door / front_door / bath_door (deg), headlights, living_state ('wait' shows the waiting room through the door) |
| `dr_kitchen(view, ...)` | phone, phone_side, wide, sink, floor, hall, front | era now / 1979, tod, hood, ceiling, fire (burn in the sink), phone hung / off, cord in / out, ring 0..1 or f(t), clock, paper |
| `dr_bath(view, ...)` | sink, mirror, cabinet, door | cabinet 0..1 (or deg, or f(t)) the mirror door open, card (False after it is torn out), cab_empty, vanity, bath_door |
| `dr_front(view, ...)` | house, porch, door, driveway, car, street, bus, bus_far, peephole | tod night / sunrise, car, rain, porch, headlights, front_door, glow, bus_flicker |
| `dr_car(view, ...)` | front, driver, back, mirror, windshield | speed 1 driving / 0 parked, dome (level spec), dash, wheel (False: draw CH.draw_steering_wheel), wipers, rain, clock |
| `dr_clinic(view)` | wide, table, door | (bright day) |
| `dr_office(view, owner, ...)` | desk, wide, door | owner 'halverson' / 'narrator' (the final twist), lamp, monitor, ceiling, stack, door, rain |
| `dr_er_entrance(view, doors, car, rain)` | ext, doors | doors 0 shut .. 1 open or f(t) (live layer); lobby figures use `layer.order = sp.info['inside_order']` |
| `dr_er_bay(view, ...)` | bay, side, monitor | live_monitor, bpm (140), exam |
| `dr_er_wait(view, rock)` | wide, chairs, desk | rock = the empty chair still rocking (deg amplitude) |
| `dr_hosp_hall(view, on, flicker_end)` | hall, chair | on = indices of lit ceiling lights; the last plastic chair at the end |
| `dr_cardio(view)` | side, ruth | warm morning |
| `dr_run(view, speed)` | side, front, rail | Milo at 22, the marathon |
| `dr_outro(view, lamp, phone)` | table, phone, wide | lamp level spec (dict(on=t)), phone 'off' / lit |
| `dr_insert(name, prop_kw, motion)` | card, card_back, phone, phone_counter, phone_cord, badge, results, note, burn, ticket, sign, clipboard, pen, wrist, tape, glucose, clock, coffee, advice | see `DR_INSERTS` notes; prop_kw may hold f(t) for ring / click / flick / time; motion f(t) -> (dx, dy, dscale, drot), keep |dx|,|dy| < 300 px |

Level specs (lamp, dome...) accept a number or f(t). Cameras are `DR_CAMS` on one plan in metres (x east, y back from
Larch Street, Y up; floor 0, ceiling 2.55, ground -0.5): a cut between views keeps every wall, door and chair in place.
See `_work/sets/floorplan.jpg` before choosing a reverse angle.

## 2. Anchors per view (from `_work/sets/index.json`)

Anchor = `Spot`: `.x .y` (screen px of the feet / point), `.ppm`, `.depth`, `.height` (a 1.85 m adult), `.X .Yp .Y`
(plan), `.kind` stand / seat / kneel / lie / surface / point / floor_sit, `.turn`, `.seat_y`.

| stills (same anchors) | anchors |
|---|---|
| liv_wide, liv_wide_lamp, liv_chair, liv_window_bus, liv_door, liv79_wide, liv79_chair, liv79_sunrise, liv_sunrise | armchair, armchair_arm_r, armchair_front, clock, coffee_top, couch_left, couch_mid, couch_right, door, door_knob, keys, room_mid, side_top, tv_screen, window, window_glass, window_side |
| liv_wide_headlights, liv_window | armchair, armchair_arm_r, armchair_front, car_back_l, car_back_r, car_driver, car_passenger, clock, coffee_top, couch_left, couch_mid, couch_right, door, door_knob, keys, room_mid, side_top, tv_screen, window, window_glass, window_side |
| liv_door_open | armchair, armchair_arm_r, armchair_front, bath_door, clock, coffee_top, couch_left, couch_mid, couch_right, deadbolt, door, door_inside, door_knob, door_through, hall_back, hall_mid, keys, kitchen_door, knob, living_door, living_knob, peephole, peephole_eye, room_mid, side_top, tv_screen, under_door, window, window_glass, window_side, + hall.* (the neighbouring room's anchors, prefixed) |
| wait_wide, wait_front, wait_rows, wait_him, wait_grandpa, wait_side, wait_machine, wait_wide_dead | aisle_front, armchair, armchair_arm_r, armchair_front, carpet_l, carpet_r, clock, door, door_knob, grandpa_seat, keys, room_mid, side_top, sign, ticket_machine, ticket_slot, tv, window, window_glass, window_side, seat_r<row>_<n> (12 seats) |
| hall_door, hall_door_lit, hall_door_open, hall_back, hall_livdoor, hall_peep, hall_floor | bath_door, clock, counter, deadbolt, door_inside, door_through, floor_kneel, floor_rock, fridge, hall_back, hall_doorway, hall_mid, jack, kchair0, kchair1, kchair2, kitchen_door, kitchen_mid, knob, living_door, living_knob, milo_enter, peephole, peephole_eye, phone, phone_base, phone_beside, phone_cord_base, phone_hook, plug_floor, receiver_counter, sink, sink_bowl, table_top, under_door, window, + kitchen.* (the neighbouring room's anchors, prefixed) |
| hall_livdoor_wait | aisle_front, armchair, armchair_arm_r, armchair_front, bath_door, carpet_l, carpet_r, clock, counter, deadbolt, door, door_inside, door_knob, door_through, floor_kneel, floor_rock, fridge, grandpa_seat, hall_back, hall_doorway, hall_mid, jack, kchair0, kchair1, kchair2, keys, kitchen_door, kitchen_mid, knob, living_door, living_knob, milo_enter, peephole, peephole_eye, phone, phone_base, phone_beside, phone_cord_base, phone_hook, plug_floor, receiver_counter, room_mid, side_top, sign, sink, sink_bowl, table_top, ticket_machine, ticket_slot, tv, under_door, window, window_glass, window_side, seat_r<row>_<n> (12 seats), + kitchen.*, living.* (the neighbouring room's anchors, prefixed) |
| kit_phone, kit_phone_ring, kit_phone_side, kit_phone_side_counter, kit_wide, kit_wide_light, kit_sink, kit_sink_fire, kit_floor, kit_hall, kit_front, kit79_phone, kit_sunrise | bath_door, clock, counter, deadbolt, door_inside, door_through, floor_kneel, floor_rock, fridge, hall_back, hall_doorway, hall_mid, jack, kchair0, kchair1, kchair2, kitchen_door, kitchen_mid, knob, living_door, living_knob, milo_enter, peephole, peephole_eye, phone, phone_base, phone_beside, phone_cord_base, phone_hook, plug_floor, receiver_counter, sink, sink_bowl, table_top, under_door, window, + hall.* (the neighbouring room's anchors, prefixed) |
| bath_sink, bath_sink_open, bath_mirror, bath_cabinet, bath_cabinet_open, bath_cabinet_nocard, bath_door | bath_door, cab_shelf, card, deadbolt, door_in, door_inside, door_through, hall_back, hall_mid, kitchen_door, knob, living_door, living_knob, mirror, peephole, peephole_eye, sink, sink_watch, tub_edge, under_door, + hall.* (the neighbouring room's anchors, prefixed) |
| ext_house, ext_porch, ext_door, ext_door_open, ext_driveway, ext_car, ext_street, ext_bus, ext_bus_far, ext_peephole | bus_bench, bus_lamp, car_back_l, car_back_r, car_door, car_driver, car_passenger, driveway, lawn, porch_door, porch_knock, porch_step, street_mid, walk, walk_run, window_out |
| ext_house_sunrise | bus_bench, bus_lamp, car_door, driveway, lawn, porch_door, porch_knock, porch_step, street_mid, walk, walk_run, window_out |
| clinic_wide, clinic_table, clinic_door | counter_top, desk_top, door, exam_table, parent_chair, stand_table, stool, table_lie |
| office_desk, office_wide, office_door, office_narrator | desk_chair, desk_top, door, phone, results, window |
| car_front, car_driver, car_back, car_back_dome, car_mirror | back_l, back_r, driver, lap_back_r, mirror, mirror_back_l, mirror_back_r, narrator_eye, passenger, roof_back_l, wheel, wheel_10, wheel_2 |
| car_windshield | back_l, back_r, driver, lap_back_r, mirror, narrator_eye, passenger, roof_back_l, wheel, wheel_10, wheel_2 |
| er_ext, er_doors, er_doors_open | car_door_r, car_stop, curb, doors, inside |
| er_bay, er_bay_side, er_monitor | bed_edge, bed_lie, doctor, foot, iv_bag, iv_hand, monitor, nurse |
| er_wait, er_wait_chairs, er_desk | chest_seat, desk_front, desk_nurse, entrance, nurse_walk, rock_seat, seat_r<row>_<n> (21 seats) |
| hosp_hall, hosp_hall_chair | hall_mid, hall_near, last_chair, office_door |
| cardio, cardio_ruth | coffee, desk_top, doctor_chair, patient_chair0, patient_chair1 |
| run_side, run_front, run_rail | rail, rail_stand, runner, runner_ahead, runner_behind |
| outro_table, outro_table_dark, outro_phone, outro_wide | bed_edge, floor, lamp_switch, phone, stand_top |

Inserts have no anchors (one sharp plane).

## 3. Staging recipe

```python
import sets as ST, characters as CH
sp = ST.dr_living('wide', state='wait')
lay, a = ST.stage_figure(sp, 'later', 'armchair')              # HIM folded into Grandpa's armchair (perch='armchair')
lay2, b = ST.stage_figure(sp, 'grandpa', 'grandpa_seat', seed=2)  # Grandpa seated in the last row
# acting=lambda a: ... adds beats (CH.Acting API: CAST.md) before the figure is drawn
```
`ST.stage_figure(sp, who, spot, act=None, turn=None, seed=1, expr='neutral', name=None, light=True, acting=None, perch=None)`
returns `(Layer, Acting)`: height from the spot's ppm (`CH.height_px`), feet on the spot's floor point, facing `.turn`,
the room light at that point (`sp.light_kw`) and the furniture-aware draw order (`sp.order_at`). `act` defaults from the
spot's kind (seat / kneel / lie). Doctor Later ('later') on a seat Spot is perched with his own rig: `perch` =
'armchair' | 'plastic' | 'bench' | 'car' | 'low' (default from the spot name: armchair*, bus*, back_*, else plastic).
Off-anchor positions: `sp.spot(x, y, Y)` (plan metres) and `sp.walkable(x, y)`; never place a figure by hand-typed pixels.
Lying figures (Grandpa 1979 is SITTING; Milo on the ER bed uses `bed_lie`) use a 'lie' Spot, never a rotated stand.

## 4. Depth-to-scale rule

`ppm = S / depth` (depth along the view axis); a figure m metres tall is `m * ppm` px at its feet. Always take ppm from
the anchor or `sp.ppm_at(x, y)`; a walking figure re-reads ppm every frame from its plan point. Props held in hands use
the holder's ppm. Feet on `sp.floor_y(x, y)`; nothing floats, nobody stands on furniture (`sp.info['blocks']` are the
furniture footprints; `walkable` is False inside them).

## 5. Mirror and roof data (car, bathroom)

- `dr_car('mirror')`: `sp.info['mirror_quad']` (screen quad of the rear-view glass); anchors `mirror_back_l` /
  `mirror_back_r` are where Milo and HIM appear in the glass: draw them flipped left-right, clipped to the quad, using the
  reflection's ppm and seat_y; `sp.info['mirror_roof_y']` is the reflected roof line (HIM's bent head touches it).
- every car view: `sp.info['roof_y']` = screen y of the roof lining over each seat (driver, passenger, back_l, back_r);
  Doctor Later in the back seat bends his head to `roof_y['back_l']` (anchor `roof_back_l`). `sp.info['wheel']` = the
  steering-wheel centre and radius (`wheel_10`, `wheel_2` hand anchors).
- bathroom: the medicine cabinet's mirror door is `cabinet` (0 shut, 1 = 105 deg); the card is drawn on its inside
  (anchor `card`); `card=False` leaves the tape ghosts after the narrator tears it out; `cab_shelf` for hands reaching in.

## 6. Script beat -> set and view

| beat | set / view (state) | inserts |
|---|---|---|
| Cold open: phone at 3 AM, hold, waiting room, "Take a seat" | kit_phone_ring; wait_wide, wait_him; hosp_hall_chair | ins_phone_ring, ins_ticket, ins_tape, ins_card |
| 1979: chest pain, Grandma calls, "It can wait until morning" | dr_kitchen era=1979 'phone'; dr_living state=1979 wide / chair | ins_clock_kitchen |
| 1979 sunrise: coffee, the still chair | liv79_sunrise (coffee=True) | ins_coffee, ins_coffee_cold |
| Milo's symptoms; Halverson's clinic, blood taken | dr_clinic wide / table / door | ins_badge |
| Sundown: the cabinet, the yellow card | dr_bath mirror / cabinet (cabinet open) | ins_card (hl=n per rule) |
| Rule 1: 3 AM call, seven rings, "Don't you dare", cord pulled | dr_kitchen phone / phone_side / wide / floor; dr_office desk (Halverson calling) | ins_phone_ring, ins_phone_cord, ins_clock_kitchen |
| Comment prompt | ins_phone / kitchen hold | ins_phone_counter |
| Rule 2: unplugged phone rings, hold music everywhere | kit_phone_side_counter; hall_back, liv_wide, liv_chair | ins_phone_counter, ins_phone_cord |
| Rule 3: Milo thirsty, hand over mouth, pen click in hall | kit_wide / kit_front; hall_back | ins_pen_click |
| Rule 4: knock, peephole, house call, paper under door, burn | hall_door / hall_peep / hall_floor; ext_peephole, ext_porch, ext_door; kit_sink_fire | ins_badge, ins_results_slide, ins_note, ins_burn(_half/_ash) |
| Rule 4: Halverson in her car at 4 AM; the bus stop | liv_window / liv_wide_headlights; ext_driveway, ext_car; liv_window_bus, ext_bus, ext_bus_far | |
| Rule 5: Milo breathing fast, Grandma rocking on the floor | kit_floor, kit_hall | ins_clock |
| Rule 6: the waiting room, the patients, Grandpa, the ticket MILO | hall_livdoor_wait; wait_wide, wait_front, wait_rows, wait_grandpa, wait_him, wait_side, wait_machine | ins_sign, ins_ticket(MILO), ins_ticket_grandpa, ins_clipboard |
| Rule 7: pulse, questions, the tape loosens, faces | wait_him, wait_wide_dead (tubes dying), wait_side | ins_wrist(_count/_free), ins_clock_slow, ins_tape(_loose) |
| The card's back, "Doctor Later" | dr_bath cabinet (card torn: card=False) | ins_card_back |
| Rescue: out the door, Halverson on the steps | hall_door_open, ext_door_open, ext_porch, ext_driveway | |
| The car: pulse, rain, diabetes talk, HIM in the mirror | car_front, car_driver, car_back(_dome), car_mirror, car_windshield | |
| ER: doors open, Mom with the wheelchair, the bay | er_ext, er_doors -> er_doors_open (doors=f(t)), er_bay, er_bay_side, er_monitor | |
| The man holding his chest; the empty chair rocking | er_wait, er_wait_chairs (rock), er_desk | |
| After: Milo at 22 | run_side / run_front / run_rail | ins_glucose |
| Grandma's ticket at sunrise; the cardiologist | liv_sunrise; ext_house_sunrise; cardio, cardio_ruth | ins_ticket_ruth |
| Final twist: the narrator's night office; the last chair | office_narrator (owner='narrator'); hosp_hall, hosp_hall_chair | |
| Outro: lights on, the advice list, like / subscribe, next time | outro_table_dark -> outro_table, outro_phone, outro_wide | ins_advice (show=0..5), ins_advice_3 |

## 7. Notes

- The ER entrance lobby haze scales with distance (close 'doors' view keeps TRIAGE legible); the lobby lamp is 1.25.
- Villain world grades are sickly green-yellow (wait states, `dr_ins_wait`); hospital, clinic and ER grades are bright
  and warm (`dr_ins_bright`, `dr_er_night` lobby). Keep the doctors' spaces bright.
