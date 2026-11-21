# SETS.md: the sets of "If The School Bus Stops At Midnight... DON'T GET ON"

Code: `sets_bus.py` (exec'd inside `sets.py` after `sets_bunny.py` and `sets_doctor.py`; its docstring and `BU_API` are
the API reference). Every name is `bu_* / BU_* / _bu*`; use `import sets as ST`. Stills, contact sheet, floor plan, stage
tests, frame check and bench live in `_work/sets/` (`index.json` holds every still's anchors with plan and screen data).

```
python3 tools/sets_sheet.py                    # every bus-film still (1280x720) + contact_sheet.jpg + index.json + floorplan.jpg
python3 tools/sets_sheet.py --only liv_,ins_   # just the variants whose names contain these
python3 tools/sets_sheet.py --stage            # cast placed only from Spots -> stage_*.jpg + stage_sheet.jpg
python3 tools/sets_sheet.py --frame --bench    # widest-move edge check (frame_check.*) + draw time at 2560x1440 (bench_2560.json)
python3 tools/sets_sheet.py --doctor           # the Doctor film's sets (regression; doctor_* files)
```
Variants are listed in `tools/sets_sheet_bus.py` (BUS: name, builder call, note) and are the best examples of every state.

## 1. Builders, views, states

| builder | views | states / keyword arguments (levels = number or f(t)) |
|---|---|---|
| `bu_living(view, ...)` | wide, reverse, couch, couch3q, window, door, hand | lamp, ceil, tv, heads (his headlights through the curtains), hall, phone (+phone_at), flash; curtains gap 0..1 (0.12) or f(t); backpack 'window' / 'wall' / None; walkie; blackout; his (bus outside) |
| `bu_hall(view, ...)` | door, doorclose, side, stairs, up, window | hall, porch, heads, up, liv, phone, flash; door / back_door (deg or f(t)); rules, eighth; frost (his silhouette through the frosted panes); ticket 0..1 (under the door); broom 'bus9' + cab9 (the side window view) |
| `bu_upstairs(view, ...)` | hall, back, stairs | up, gran, sami (light through open doors), gran_door / sami_door (deg or f(t)), bolt, blackout |
| `bu_gran(view, ...)` | door, window, wide | lamp, ceil, hall, door (deg or f(t)), bolt 1 thrown / 0 slid, bed, phone, flash |
| `bu_sami(view, ...)` | room, bed | ceil, hall, nightlight, bed 'made' / 'turned' / 'empty', rex 'bed', walkie |
| `bu_front(view, ...)` | house, street, curb, mailbox, porch, door, frame, driveway, bus9door, sideyard, peephole, gap, granout | his, his_door (0..1 or f(t)), his_win, his_heads, his_x (pulling away), porch, street (`ST.bu_flicker(t0)` = the three tape-skip flickers), letters 0..1, win {liv, hall, gran, gran_w, mina, den, sami}, broom 'porch' / 'bus9', door9, cab9, flash (+flash_at), mirror9, frost_lit |
| `bu_bus_in(view, kind, tod, ...)` | aisle, back, seat4, seat22, seat21, steps, doors, driver, step_out, cab, seat1, radio, windshield, back_window | kind 'his' (amber; seat_lit {4: 1, 22: 1}; dome; step) / 'bus9' (tod 'night' / 'morning'); door 0..1 or f(t); broom, bend, crack; drive (m/s); his_ahead (x, y); brake; far_figure (back_window) |
| `bu_road(view, ...)` | side, ahead, behind, window | his_pos (x, y) or f(t); his_win 0 dark .. 1 amber; brake; speed; heads9; mirror_r False after the swerve |
| `bu_school(view, ...)` | wide, doors, clock, flag, reverse, lot | clock (h, m[, s]); his; his_door (or f(t)); his_win; heads9; broom9, bend, crack; clipboard; tail; police; wind |
| `bu_theo_stop(view, porch)` | house, wide | porch: the light coming on (level spec) |
| `bu_class94(view, content)` | cart, tv | content 'full' / 'kids' / 'title' playing on the CRT |
| `bu_tape94(view)` | full, kids, title | the 1994 tape full frame (VHS fx); anchors host, kids_row |
| `bu_insert(name, prop_kw, motion)` | post, comment, nobars, call911, rules, ticket, walkie, punch, clipboard, flashlight, clock, backpack, tail, mailbox, chalkboard | see `BU_INSERTS` notes (rules: show / hl / eighth; ticket: slide; clipboard: page 'list' / 'last', write; clock: time; walkie: talk; punch: click) |

Grades: `bu_night`, `bu_warm`, `bu_dark` (blackout), `bu_amber` (HIS world: sodium-amber, crushed, grainy; his sets also carry
`bu_vhs_dirt()` tape dirt), `bu_ext`, `bu_road`, `bu_morning`, `bu_class`, `bu_vhs94`, `bu_ins`, `bu_ins_amber`.

## 2. The plan (one plan per location; `_work/sets/floorplan.jpg` draws every camera)

Metres: x east, y back from the front wall (Larch Street at y 0), Y up. House floor Y 0, upstairs `BU_UP` 2.95 (ceiling
+2.4), yard / street `BU_G` -0.5.
- Ground floor: hall x -5.6..-3.2 (front door x -4.4..-3.5 hinged west, frosted panes, peephole 1.55 m, rules sheet 0.83..1.13 m;
  side window over the driveway; stairs along the west wall rising +y from y 3.2 to 6.84; back door at y 9.6); living room
  x -3.2..2.4, y 0..5.8 (picture window x -2.0..0.8 with the curtain gap at x -0.6; couch along the back facing the window;
  Grandma's armchair facing west; TV in the front-east corner; opening to the hall y 0.3..3.2).
- Upstairs: hall x -4.6..-3.4, y 3.2..8.2 (1.2 m wide, 2.4 m ceiling: he must bend double); Grandma's room x -5.6..-1.6,
  y 0..3.2 (deadbolt door at the hall's front end, window over the driveway); Sami's room x -3.4..0.8, y 5.4..9.6.
- Outside: porch y -1.8..0, steps to y -2.6, walk to the kerb (y -12.2), mailbox (-3.0, -11.65), bus 9 in the driveway at
  (-8.3, -1.0) nose +y (its door faces the house), his bus at the kerb (-0.2, -13.75) heading west (door faces our walk),
  the flickering streetlight (-6.4, -12.6).
- Bus plan (both buses): x across (+x = door side), y back from the windshield, floor Y 0, ground -0.95; seat n: row
  (n-1)//2, odd = driver side; seat 4 = row 1 door side, 21 / 22 = back row; `seat<n>_win` / `seat<n>_aisle` = two kids on one bench.
- School: facade on y 0 facing -y; his bus (-5.0, -3.4) facing +x, door toward the lot; bus 9 (-2.0, -16.5) nose +y, headlights on Mina.

Screen direction: in the house, the street is always "front" (-y). Cuts between views of one plan keep every wall, door
and bus in place; the reverse angles are on the floor plan.

## 3. Staging recipe and rules

```python
import sets as ST, characters as CH
sp = ST.bu_living('couch3q', lamp=1.0)
lay, a = ST.stage_figure(sp, 'mina', 'couch_right')            # seated from the anchor's seat_y: never standing on the seat
lay2, b = ST.stage_figure(sp, 'sami', 'couch_mid', seed=2)
# outside: figures order = sp.order_at(x, y); bus seats: anchors b9_driver / his_driver sort between the bus parts
```
- Seated figures read as seated only at |turn| >= 0.5 (stage_figure warns): use couch3q (not couch / reverse) for the
  couch, seat4 / seat22 / seat21 / seat1 (not aisle) for bus seats.
- `floor_sit` (Grandma's door_sit) needs the cast's floor-sit pose; `kneel` (lot_kneel) the kneel pose.
- Depth-to-scale rule: ppm = S / depth; a figure m metres tall is m * ppm px at its feet (Spot.height = a 1.85 m adult).
- Him in the upstairs hall: hall_mid with ceiling anchor (Y 5.35) and wall_l / wall_r (his gloves flat on both walls).
- Tape-skip path: `bu_front('street', street=ST.bu_flicker(t0))` and anchors mailbox -> lawn_mid -> porch_step; then the
  door: `bu_front('frame')` anchors doorframe / doorframe_w; `bu_hall('door', frost=f)` (his silhouette through the panes).

## 4. Script beat -> set and view

| beat (narration) | set / view (state) |
|---|---|
| Hook: the bus stops outside at midnight; "ask for the family word" | `bu_front('house', his_heads=1)`, `bu_living('window', heads=1)`; `bu_hall('door', frost=1, porch=1)` |
| 1994: every school rolled out the TV cart | `bu_class94('cart')` -> `bu_class94('tv')` -> push into `bu_tape94('full')` / `('title')` |
| "Write your name... hold it up" / the kids hold up their cards | `bu_tape94('kids')` (the small yellow raincoat at the end, card unreadable) |
| Grandma Della, bus 9 in the driveway; "Brakes, mirrors, names" | `bu_front('driveway', cab9=0)`, photo on the living-room wall (`bu_living('wide')`) |
| Seat twenty-two, the boy in the raincoat; "Hi, Mina" | `bu_bus_in('seat22', kind='bus9', tod='morning')` |
| Sami practises roll call; the walkie-talkies | `bu_living('couch3q', lamp=1)`, `bu_insert('walkie')` |
| The post: chalkboard, 41 likes, the faceless comment "Great smile!" | `bu_insert('chalkboard')`, `bu_insert('post', prop_kw=dict(show=0..2, hl='comment'))`, `bu_insert('comment')` |
| Grandma's face went grey: "Take it down." | `bu_living('reverse', lamp=1)` |
| Seven rules taped inside the door; the family word | `bu_hall('doorclose', hall=1)`, `bu_insert('rules', prop_kw=dict(show=n, hl=k))` |
| Rule 1: lights off, letters off the mailbox, backpack to the wall | `bu_front('mailbox', letters=f)`, `bu_insert('mailbox')`, `bu_living('reverse', backpack='wall')`, `bu_insert('backpack', side='back')`, `bu_front('house_before' -> lights off)` |
| Midnight: air brakes, yellow headlights fill the curtains | `bu_living('wide' / 'window', heads=f)`, `bu_front('house', his_heads=1)` |
| The loudspeaker reads the post; "He read it off my phone" | `bu_front('curb')`, `bu_insert('post')` |
| Rule 2: through the gap his door folds open; something unfolds | `bu_front('gap', his_door=f)`, `bu_front('curb', his_door=f)` |
| The streetlight flickers: mailbox, lawn, porch steps | `bu_front('street', street=ST.bu_flicker(t0))`, anchors mailbox / lawn_mid / porch_step |
| White gloves on the doorframe; through the frosted glass: a crooked hat | `bu_front('frame')`, `bu_hall('door', frost=1, porch=1)` |
| Roll call; Sami jolts awake; hand over his mouth | `bu_living('couch3q')` (Mina couch_right, Sami couch_mid) |
| The punched ticket slides under the door | `bu_hall('doorclose', ticket=f)`, `bu_insert('ticket', prop_kw=dict(slide=f))` |
| Rule 3: 911, no bars | `bu_insert('nobars')` |
| Grandma slips out the back; the flashlight crosses the yard, goes out | `bu_hall('stairs', back_door=f)`, `bu_front('sideyard', flash=f, flash_at=...)` |
| Three knocks: "It's Grandma!"; "What's the word?" | `bu_hall('door' / 'side')` |
| The peephole goes white | `bu_front('peephole')` + the cast's grin |
| Real Grandma trapped in bus 9, the broom through her doors | `bu_front('driveway' / 'bus9door', broom='bus9', cab9=0.6)`, `bu_hall('window', broom='bus9', cab9=0.6)` |
| Rule 4: Sami upstairs for Rex; my walkie on the cushion | `bu_hall('up', up=1)`, `bu_living('hand')` (anchor walkie) |
| 2:10 blackout: a small cold hand; the phone light; the glove; my walkie at the grin | `bu_living('hand' / 'couch3q', blackout=True, phone=f, phone_at=...)` |
| Lights back; Sami hugging Rex: "LIGHTHOUSE!" | `bu_sami('room', ceil=1)`, `bu_upstairs('back', up=1, sami_door=80)` |
| Rule 5: Grandma's room, back against the deadbolt | `bu_gran('door', lamp=0.6)` (door_sit) |
| 2:31: a flashlight blinks in bus 9, three times; I go to the window | `bu_front('granout', flash=f)`, `bu_insert('flashlight', prop_kw=dict(on=f))`, `bu_gran('window')` |
| "Lighthouse"; the deadbolt slides; the hallway is full of him | `bu_gran('door', bolt=f, door=f)`, `bu_upstairs('hall', gran_door=95)` |
| Blink: stairs, front hall, lawn, his bus steps | `bu_upstairs('stairs')`, `bu_hall('stairs')`, `bu_front('street')`, `bu_front('curb', his_door=1)` |
| The doors slap shut; Sami's palm on seat 4's window; seat 22 glows | `bu_front('curb', his_door=f)` (anchor his_window* ), `bu_bus_in('seat4')`, `bu_bus_in('aisle')` |
| The bus pulls away with no lights | `bu_front('street', his_x=f, his_win=0, his_heads=0)` |
| Rule 6: rip the broom out; Grandma's phone; 911; seat one | `bu_front('bus9door', broom='bus9')`, `bu_insert('call911')`, `bu_bus_in('seat1', kind='bus9', drive=14)` |
| 1994 story; the dash radio crackles in Grandma's voice | `bu_bus_in('radio', kind='bus9', drive=14)` |
| Up ahead his bus, dark; his head out of the window, backwards | `bu_bus_in('windshield', kind='bus9', his_ahead=(0, -26))`, `bu_road('ahead')`, `bu_road('window')` |
| Brake lights; swerve; our mirror ripped off; the road empty | `bu_road('ahead', brake=f)`, `bu_road('side', his_pos=f)`, `bu_bus_in('windshield', drive=14)` |
| The other mirror full of amber: he's behind us | `bu_road('behind', his_win=1, mirror_r=False)` |
| Rule 7: 2:57, Larkfield Elementary, dark windows, the flag rope | `bu_school('wide' / 'flag' / 'clock', clock=(2, 57))` |
| His bus at the doors, cobwebs; amber; top of the steps with the clipboard | `bu_school('doors')`, `bu_bus_in('step_out', door=1)` |
| I stop at the bottom step; two of me; my foot lifts | `bu_school('doors' / 'reverse')` (bottom_step, behind_mina), `bu_bus_in('step_out')` |
| The glove snaps on his pajamas; rip; half the tail gone | `bu_bus_in('steps', door=1)`, `bu_insert('tail')` |
| 2:58: seat 22 glows; the arm down the aisle; the lure | `bu_insert('clock', time=(2, 58))`, `bu_bus_in('back' / 'aisle' / 'seat22')` |
| 2:59: "What's your name?"; doors folding on the broom; it bends, cracks | `bu_school('doors', his_door=f, broom9=1, bend=f, crack=f)`, `bu_bus_in('doors', broom=1, bend=f, crack=f)` |
| The grin swings to the clock; three o'clock bell | `bu_school('clock', clock=(3, 0))`, `bu_insert('clock')` |
| The bus rewinds into the dark; the clipboard on the asphalt; Grandma kneels | `bu_school('lot', his=False, clipboard=True, tail=True, police=True)` (lot_kneel) |
| Theo's stop: the porch light comes on | `bu_theo_stop('house', porch=f)` |
| The clipboard: Sat alone, crossed out; the last page | `bu_insert('clipboard', page='list' / 'last')` |
| Morning: seat 21, the new girl; I sit next to her | `bu_bus_in('seat21', kind='bus9', tod='morning')` (seat21_win / seat21_aisle) |
| Out the back window: the tall figure, a new clipboard | `bu_bus_in('back_window', kind='bus9', tod='morning')` (far_figure) |
| That night: rule eight | `bu_insert('rules', prop_kw=dict(eighth=True))` |

## 5. Anchors per view (from `_work/sets/index.json`: kind, screen x/y, depth, ppm, plan point, turn, seat_y, note)

| stills (same anchors) | anchors |
|---|---|
| ext_house, ext_house_before, ext_street, ext_street_flicker, ext_curb, ext_mailbox, ext_mailbox_off, ext_porch, ext_door, ext_frame, ext_driveway, ext_bus9door, ext_sideyard, ext_peephole, ext_gap, ext_granout | b9_door, b9_driver, b9_step, b9_top, back_corner, doorframe, doorframe_w, gran_window_out, his_door, his_driver, his_step, his_top, lamp, lawn_mid, mailbox, mailbox_box, mailbox_front, peephole_out, porch_door, porch_knock, porch_step, street_mid, walk, window_out, yard_west, + <bus>_window0..9 |
| liv_wide, liv_wide_dark, liv_reverse, liv_couch, liv_couch3q, liv_window, liv_door, liv_hand, liv_wall_pack | armchair, back_door, backpack, backpack_reach, bench, couch_front, couch_left, couch_mid, couch_right, deadbolt, door_inside, hall.back_door, hall.deadbolt, hall.door_inside, hall.hall_mid, hall.knob, hall.opening, hall.panes, hall.peephole, hall.peephole_eye, hall.rules, hall.side_window, hall.stair10, hall.stair13, hall.stair2, hall.stair6, hall.stairs_foot, hall.under_door, hall_mid, kitchen_door, knob, lamp_switch, opening, panes, peephole, peephole_eye, room_mid, rules, side_window, stair10, stair13, stair2, stair6, stairs_foot, tv_screen, under_door, walkie, window, window_gap |
| hall_door, hall_door_dark, hall_doorclose, hall_side, hall_stairs, hall_up, hall_window | armchair, back_door, backpack, backpack_reach, bench, ceiling, couch_front, couch_left, couch_mid, couch_right, deadbolt, door_inside, hall_back, hall_front, hall_mid, kitchen_door, knob, lamp_switch, landing, living.armchair, living.backpack, living.backpack_reach, living.bench, living.couch_front, living.couch_left, living.couch_mid, living.couch_right, living.kitchen_door, living.lamp_switch, living.opening, living.room_mid, living.tv_screen, living.walkie, living.window, living.window_gap, opening, panes, peephole, peephole_eye, room_mid, rules, sami_door, side_window, stair10, stair13, stair2, stair6, stairs_foot, tv_screen, under_door, uphall.ceiling, uphall.hall_back, uphall.hall_front, uphall.hall_mid, uphall.landing, uphall.sami_door, uphall.wall_l, uphall.wall_r, walkie, wall_l, wall_r, window, window_gap |
| up_hall | back_door, bed, bed_edge, ceiling, deadbolt, door_in, door_inside, door_sit, gran.bed, gran.bed_edge, gran.deadbolt, gran.door_in, gran.door_sit, gran.knob, gran.rocker, gran.room_mid, gran.window, gran.window_glass, hall.back_door, hall.deadbolt, hall.door_inside, hall.hall_mid, hall.knob, hall.opening, hall.panes, hall.peephole, hall.peephole_eye, hall.rules, hall.side_window, hall.stair10, hall.stair13, hall.stair2, hall.stair6, hall.stairs_foot, hall.under_door, hall_back, hall_front, hall_mid, knob, landing, opening, panes, peephole, peephole_eye, rocker, room_mid, rules, sami_door, side_window, stair10, stair13, stair2, stair6, stairs_foot, under_door, wall_l, wall_r, window, window_glass |
| up_back, up_stairs | back_door, ceiling, deadbolt, door_inside, hall.back_door, hall.deadbolt, hall.door_inside, hall.hall_mid, hall.knob, hall.opening, hall.panes, hall.peephole, hall.peephole_eye, hall.rules, hall.side_window, hall.stair10, hall.stair13, hall.stair2, hall.stair6, hall.stairs_foot, hall.under_door, hall_back, hall_front, hall_mid, knob, landing, opening, panes, peephole, peephole_eye, rules, sami_door, side_window, stair10, stair13, stair2, stair6, stairs_foot, under_door, wall_l, wall_r |
| gran_door, gran_window, gran_wide | bed, bed_edge, deadbolt, door_in, door_sit, knob, rocker, room_mid, window, window_glass |
| sami_room, sami_bed | bed, bed_edge, door_in, rex, room_mid, walkie, window |
| his_aisle, his_back, his_seat4, his_seat22, his_steps, his_doors, his_doors_crack, his_driver, b9_cab, b9_seat1, b9_radio, b9_windshield, b9m_aisle, b9m_seat21, b9m_back_window, his_step_out | aisle10, aisle2, aisle5, aisle8, aisle_back, bottom_step, door_lever, driver, outside_door, radio, step1, top_step, top_step_back, wheel, + seat1..22 (and _win / _aisle), window1..22 |
| road_side, road_ahead, road_behind, road_window | b9_door, b9_driver, b9_step, b9_top, his_door, his_driver, his_step, his_top, his_window, + <bus>_window0..9 |
| sch_wide, sch_doors, sch_doors_broom, sch_clock, sch_flag, sch_reverse, sch_lot | asphalt, b9_door, b9_driver, b9_step, b9_top, behind_mina, bottom_step, clock, flag_rope, his_door, his_driver, his_step, his_top, lot_kneel, + <bus>_window0..9 |
| theo_house, theo_house_on | door, porch_light, walk |
| class_cart, class_tv | desk_front, tv_screen |

Inserts and the 1994 tape are flat (one sharp plane); the tape has anchors host / kids_row (Anchor, 290 px per metre).
