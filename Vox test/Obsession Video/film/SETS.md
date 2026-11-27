# SETS.md: the sets of "If a Girl Is OBSESSED With Being Your Only Friend... DON'T WRITE YOUR NAME"

## Obsession film (this film): `sets_obsession.py`
Exec'd inside `sets.py` after `sets_buttons.py` (hook at the end of sets.py). Every name is `om_* / OM_* / _om*`; use
`import sets as ST`. The module docstring has the plans (metres: x east, y north, Y up). `ST.OM_API` lists every view,
`ST.OM_INSERTS` every insert. Built like the Dummy film: ONE floor plan for Adam's house (his room in the front wing,
whose window looks DOWN on the path and the green door; the hall, stairs, landing and kitchen in the main block), so every
view of the house is the same house. Sheet, index (anchors of every still), bench, the two widest stills: `_work/sets/`.
```
python3 tools/sets_sheet_obsession.py                    # 58 variants -> _work/sets/sets_sheet.png + index.json
python3 tools/sets_sheet_obsession.py --only front_,ins_ # some -> sets_partial.png;  --keep a,b also writes om_<name>.jpg
python3 tools/sets_sheet_obsession.py --no_stills --bench --bench_only front_down_street,tape_warp   # 2560x1440 -> bench_2560.json
```
Variants (the best example of every state): `tools/sets_sheet_obsession_list.py`. Fonts: `Obsession Video/fonts` (copied
from the Bunnyman film: Montserrat + VT323 / Caveat / Patrick Hand; it was missing).

| builder (views) | states (number or f(t) where it says level) |
|---|---|
| `om_front(view, house)`: down, street, wide, facade, step | house 'adam' (GREEN door) / 'danny' (BLUE door, `mom=True, win={'up': 1}`: her silhouette, phone to her ear); tod 'night' / 'dawn' (wet clean path) / 'day'; **track** None / 'street' / 'half' / 'foot' / 'step' (+ the empty line) / 'door' / 'mat' (the bible's table, `OM_TRACK`) with `track_u` (written 0..1, f(t)), `track_wet` (the dawn wash), `track_rub`, `text`; porch (`dict(on=t)` = "clicked on"); win {adam, up, front, stairwin, living, side}; print (the sneaker print on the step, pointing in); bucket; frame (window foreground) |
| `om_room(view)`: wide, window, door, bed, desk | lamp, ceil, phone (+phone_at), torch (+torch_at), strip (the 2 a.m. light under the door) + shadow 0..1 (Mom's feet), street, landing; door deg / f(t); drawer 0..1; bed; any om_front state (track=..) shows through the window |
| `om_hall(view)`: landing, halfway, up, door, kitchen, floor | hall, landing (the bare bulb: `dict(on=t)`), kitchen ('already on'), porch, street, phone, flash; fdoor deg / f(t); flap 0..1 / f(t) (the letterbox lifting); stub True / (x, y); chalk [dict(text, x, y, h, u, rub, wet, reader)]; `ST.om_floor_quad(sp, *sp.info['floor_only'])` / `floor_me` -> the quad + size_cm for the cast's `LetterboxFingers` / `chalk_word` |
| `om_kitchen(view)`: dinner, wide, tiles, mom | kitchen, hall, phone; dinner (plates); bucket (default True); chalk (M... E... to her chair) |
| `om_school(view)`: corridor, locker, rahman, lunch, lunch_table, office | locker_open (the bracelet on the shelf); rdoor (80 = 'My door's open') |
| `om_playground(view, tod, square)`: wide, square, hop, gate, flood, swings, tape | tod 'day' / 'sunset' (THE one red glow) / 'warm' (flashback) / 'summer' / 'night'; square 'plain' / 'girl' (the cast's chalk girl) / 'danny' (chalk_u) / 'adam' (rub, adam_u) / 'painted' (paint 0..1 / f(t)); flood (`dict(on=t)`); prints 0..1 / f(t); swings (ang_l, ang_r) or False + `ST.om_swing(pen, v, 'l', angle)`, `ST.om_swing_seat(v, 'l', angle)` |
| `om_tape(figures, warp, rewind)` | Mom's camcorder tape FULL FRAME (the swings one summer): `figures(pen, t)` draws little Adam and Danny in tape space (anchors swing_l / swing_r / _pivot; `sp.info['view']` for om_swing); post['vhs'] via sp.fx (no tube, warm, wobble, rolling tracking band, chroma bleed, snow); **warp** 0..1 / f(t) = the rule 4 return (drift slows, sick tint, chewed crease, heavy tracking); **rewind** f(t) 0..1 = the rule 7 replay (torn backward bands); `ST.om_tape_stamp(cv, t, date='JUL. 14 1996', counter0, mode 'play'/'rew'/'pause', warp)` in the HUD; `om_tape_content(...)` = the same picture as a content fn (W, H, t) |
| `om_insert(name, prop_kw, motion)` | phone (screen thread: who, msgs [(mine, text)], count 12/30/47 or f(t), typing / dark: lit, banner / map: blue, white = place or f(t), zoom 'town' / 'house' (house, inside, room) / mute: 0..3 or f(t) / actions: tap, done (Save / Block / Report) / type: draft, draft_k); card (show 0..7, words (n, k), hl n, backlit 0..1: ADAM through the scribble, bg); car_window (two layers: Evie between them at anchor 'evie'; light red / amber / green); locker (dust); shoebox (the real bracelet on top; dust=1: the drawer, chalk dust); stub (roll) |

**Chalk (everyone's primitive):** `ST.om_chalk_ground(pen, v, text, x, y, Y, h, u, rub, wet, reader=(x, y))` writes in
Adam's curly hand (the same strokes as the cast's `_LETTERS`) on any level surface of a plan, stroke by stroke (u 0..1),
rubbed out (rub), washed (wet), lit by the set's light (never below readable); `om_chalk_flat(pen, text, x, y, h, u, rub,
wet, angle, squash)` on screen; `om_chalk_events(text, t0, dur)` = one 'chalk_scrape' per stroke for sound;
`om_line_ground` = the empty line. `om_bracelet(pen, x, y, r, dust=0..1)` the green-and-gold band and its chalk copy.

Key anchors: front `on_street` / `on_half` / `on_foot` / `on_step` / `on_door` / `on_mat` (standing ON ONLY ME), `pave`,
`gate`, `step`, `doorstep`, `window_adam`, `window_up`, `print`, `bucket`; room `bed`, `pillow`, `bed_edge`, `window`,
`window_glass`, `desk`, `drawer`, `door_in`, `door_gap`, `phone_bed`; hall `door_in`, `mom_door`, `adam_door`, `letterbox`,
`door_base`, `only_floor`, `bottom_stair`, `step1..12` (`halfway`), `landing`, `lina_landing`, `card_landing`, `passage`,
`kitchen_door`; kitchen `mom_chair`, `adam_chair`, `lina_chair` (seats), `window_out` (Evie outside the dark window),
`doorway`, `by_chair`, `stand_mom`, `bucket`, `table_top`; school `locker`, `locker_in`, `shoulder`, `rahman_door`,
`crossing`, lunch `adam_seat`, `opp_seat`, `beside_l/r`, `opp_l/r`, `stand_by`, `far_table`, office `her_chair`, `visitor`,
`tissues`; playground `swing_l/r` (+ `_pivot`), `square`, `square_front`, `square_stand`, `hop_start`, `gate`, `gate_adam`,
`caretaker`, `flood`, `bench`, `roller`.
Look rules kept: red only in the square (OM_RED = KEEPING_RED), the sunset sky and the traffic light the script names;
door shots look down from his (or Danny's) upstairs window; night = blue-black with the subject lit (streetlight pool,
porch light, lit windows, phone, bulb). Bench 2560 (warm frame): 0.13-0.18 s; the tape with warp 0.34 s.
Open: the street's far houses are simple copies of our semi; the playground has no night state checked; the wing's
front window (living room) has no interior.

---

# (previous film, kept for reference) The Buttons film's sets

## Buttons film: `sets_buttons.py`
Exec'd inside `sets.py` after `sets_walls.py` (hook at the end of sets.py). Every name is `bt_* / BT_* / _bt* / sc_* / nw_*`; use
`import sets as ST`. The module docstring has the plan (metres: x east, y north, Y up; our building's street front y 0, the
street to the south; the apartment floor `ST.BT_UP` 3.4, ceiling 2.5). `ST.BT_API` lists every view, `ST.BT_INSERTS` every
insert (with notes), `ST.BT_CHAT` ready message lists. Sheet + index (anchors of every still) + bench: `_work/sets/`.
```
python3 tools/sets_sheet_buttons.py                     # every variant -> _work/sets/sets_sheet.png + index.json
python3 tools/sets_sheet_buttons.py --only apt_,ins_    # some -> sets_partial.png;  --keep a,b also writes bt_<name>.jpg
python3 tools/sets_sheet_buttons.py --no_stills --bench --bench_only apt_wide   # 2560x1440 timing -> bench_2560.json
```
Variants (the best example of every state): `tools/sets_sheet_buttons_list.py`.

| builder (views) | states (number or f(t) where it says level) |
|---|---|
| `bt_apt(view)`: wide, living, table, table_back, fridge, board, micro, window, momdoor, clock, door, couch | tod 'night' / 'evening' / 'day'; levels lamp (pendant), ceil, living, laptop (+laptop_on True/'closed'/False), tablet (+tablet_at), street; swing deg or f(t) (the lamp swings); board 'birthday'/'here'/'all' + board_k ('here' 0..1, 'all' 0..6 items, or f(t): written live); clock '11:58' or f(t)->str; jar 'full'/'open'/'black'/'empty'; carton (tablet on the milk carton), dinner, headset_table, mug, papers; fdoor / mdoor deg or f(t); refl=f(pen, t, clip) (the figures in the microwave: `ST.bt_mirror(sp.view, x, Y, y)` -> (sx, sy, px/m, depth), draw them mirrored with `reflection=True`) |
| `bt_owen(view)`: wide, window, closet, bed, sill_pov | tod; lamp, ceil, tablet (+tablet_at; tablet_bed True/'down'), hall, street; sweep=`ST.bt_sweep(t0)` (headlights across the ceiling); closet deg or f(t); door (70); ink [7] (the list at room scale); coat None/'full'/'sag'/0..1/f(t); sash 0..1 or f(t) ("sliding shut"); bed |
| `bt_street(view)`: from_window, lobby_pov, lamp, lamp_close, lobby, barlow, shopwin | tod; win {next, owen, living, kitchen, e1, e2} lit windows; sweep=`ST.bt_sweep(t0)` (a car passes, the light sweeps her face); snow (old snow at the kerbs) |
| `bt_lobby(view)`: door, close | tod (the street through the glass) |
| `bt_school(view)`: wide, curb, window, dunn, back | car True/False (then only tire tracks); rear_door 0..1 or f(t); win_open (default True: the DRIVER window is open); snow level / f(t) |
| `bt_now(view)`: desk, hall, son, window | lamp, laptop, tablet, hall, street; headset 'desk'/'stand'/None; jar 'empty'/'empty_on'; tablet_bed 'up'/'down'; door (18 = ajar) or f(t) |
| `bt_chat(msgs, show, head, typing, name, draft, draft_k, account, banner, theme)` | full-frame tablet screen; head 0..7 = the grey head filling in (bun, cardigan, freckles, car, pancakes, song, then the BUTTONS click on); account 'mom' (2:04 AM, light app); theme 'now' (the son's tablet) |
| `bt_insert(name, prop_kw, motion)` | brave_list (ink [7] 1 blue .. 0 pale, words (n, k) word by word, hl n), brave_rule (n, write, ink), board, box ('closed'/'open'), card, coat (full f(t)), jar (state, bg 'sill'/'sill_day'/'desk'), music_box (crank), lock_screen, glasses (circles 0..1), clock, laptop ('line'/'delivered'/'msg'), photo (send) |

Key anchors: apt `table_mom` (seat, the Blank at dinner), `table_owen`, `stool` (the microwave beat; in line with
`table_mom` so the door reflects both), `behind_stool`, `micro`, `fridge`, `board`, `marker`, `fridge_gap` (the creepy form
unfolds BESIDE the fridge; `gap_top` the ceiling over it), `counter_e`, `momdoor` (the Blank in front of Mom's door),
`window_k`, `jar`, `couch_door` (the headset lady facing the front door), `officer`, `lamp`, `slippers`; owen `bed`,
`pillow`, `sill_seat` (seat), `window`, `closet`, `closet_in`, `coat`, `list`, `door_in`; street `under_lamp`, `owen_window`,
`next_window` (she waves at it), `glass_out` / `glass` (palms on the lobby door), `barlow_walk`, `barlow_mom`, `coat`;
lobby `glass_out` / `glass_in`; school `kerb_owen`, `step_back`, `driver` (draw her between the layers car_body and
car_kerb_side), `car_window` (the arm comes out here), `hood_reach`, `dunn`, `dunn_owen`, `mensah`, `mom_run`; now
`desk_chair`, `jar`, `headset`, `son_door`, `doorway`, `bed_sit`, `kneel`, `tablet_bed`, `lamp_spot` (outside: figures seen
through a window take order `sp.info['out_order']`).
Night rule: the frame is dark, the subject lit (the streetlight through Owen's window, the laptop, the tablet, the pendant,
the oven clock, the lobby glow, Barlow's window). Bench 2560 (warm frame): 0.15-0.2 s; the street with headlights 0.4 s.
Open: the car is a projected side-view model (fine for side and 3/4 views, not from the front); the sash overlay reads as a
plain frame; no plan map for this film.

---

# (reference) The Walls film's sets

## Walls film: `sets_walls.py`
Exec'd inside `sets.py` after `sets_ice.py` (hook at the end of sets.py). Every name is `wl_* / WL_* / _wl*`; use
`import sets as ST`. The module docstring has the full plan (14 Larkspur Lane, metres: x east, y north from the front
wall, Y up; ground floor Y 0, upstairs `WL_UP` 2.9, yards `WL_G` -0.5, road `WL_ROAD` -0.62). `ST.WL_API` lists every
view, `ST.WL_INSERTS` every insert (with notes). Sheet, index (anchors of every still), floor plan, bench: `_work/sets/`.
```
python3 tools/sets_sheet_walls.py                     # every variant -> _work/sets/sets_sheet.png + index.json + floorplan.jpg
python3 tools/sets_sheet_walls.py --only boys_,ins_   # some -> sets_partial.png;  --keep name1,name2 also writes wl_<name>.jpg
python3 tools/sets_sheet_walls.py --no_stills --bench --bench_only boys_police   # 2560x1440 timing -> bench_2560.json
```
Variants (the best example of every state): `tools/sets_sheet_walls_list.py`.

| builder (views) | states (number or f(t) where it says level) |
|---|---|
| `wl_street(view)`: house, porch, frog, garage, keypad, across, curb, up, from_window | tod 'night' / 'day' / 'morning'; porch (light); win {liv, liv_w1, liv_w2, dining, bath, stair, boys, par, kitchen}; attic (the dormer lit: "right around two"); police None / True / `ST.wl_police(t0)` (three cruisers at our kerb, drawn in views across the lane: house, curb, up, across); frog_lift 0..1 / f(t) (the key under it), key; flash, flash_at |
| `wl_living(view)`: wide, chair, vent, window | tod; lamp, ceil, phone (+phone_at), flash; boxes |
| `wl_kitchen(view)`: wide, counter, door, water, pantry, crack | tod; kitchen_light, pantry_light, crack (the sliver of light), phone, flash; nightlight (by the garage door); bolt 1 locked .. 0 or f(t) (turning by itself); gdoor, pantry_door (deg); note; bread 'twisted' / 'open' / None |
| `wl_hall(view)`: down, switch, closet, back, hatch | hall_light, attic (the yellow line round the closet door / the hatch), boys_moon, par_lamp, phone, flash, police; switch 0/1; closet deg (7 = "opened just a crack") or f(t); boys_door (80) or f(t); par_door (70); lock; nightlight |
| `wl_boys(view)`: wide, closets, door_pov, doorway, theo, sam_wall, doorframe, closet_sam | tod ('morning' for the marks); moon; nightlight; ceil, lamp, hall_light, phone, flash, police (red / blue on the ceiling); door (80) / sam_closet / theo_closet deg or f(t); slide 0..1 or f(t) (Sam's closet back wall); hole; marks, fresh; theo_bed / sam_bed 'made' / 'turned' / 'empty' |
| `wl_parents(view)`: wide, door, vent, bed | lamp, ceil, hall_light, phone (+phone_at), flash, police; door deg or f(t); lock 0/1 or f(t); bed; phone_on_stand |
| `wl_dead(view)`: slot, hole | flash (default 1, flash_at), dad_flash, police; hole |
| `wl_insert(name, prop_kw, motion)` | note (hl 0..8), rules (show, hl 1..7, seven 0..1 = "Believe me."), rule (n 1..7, write), frog (lift, key, tod), keypad (press, tod), deadbolt (turn), bread (state), drawings ('folded' / 'spread'), switch (on), vent (rattle), phone ('dial' / 'call', secs), marks (fresh) |

Key anchors (`sp.anchors`, Spots with plan + screen data; seats carry seat_y): street `porch_door`, `porch_out`,
`step_bottom`, `frog`, `frog_kneel`, `keypad(_stand)`, `boys_window`, `attic_window`, `curb_sit` (Pell on the kerb, feet in
the gutter), `curb_officer`, `to_car`, `police_0..2`, `dab_door`, `dab_walk`; living `armchair`, `chair_front`,
`chair_seat`, `vent`, `couch_*`; kitchen `note`, `bread`, `counter_front`, `sink`, `deadbolt`, `knob`, `door_in`,
`pantry_door`, `table_n/s`, `fridge`; pantry `crack`, `crack_lean`; hall `switch`, `switch_stand`, `closet_door`,
`closet_front`, `boys_door`, `par_door`, `hall_mid`, `ceiling`, `hatch`; boys `theo_bed`, `sam_bed` (lie), `sam_pillow`,
`theo_kneel`, `doorway`, `door_in`, `sam_closet`, `sam_wall`, `vent`, `marks`, `marks_fresh`, `slide_panel`;
parents `bed_dad`, `bed_mom`, `bed_huddle`, `door_in`, `lock`, `phone`, `vent`, `dresser`, `headboard`; dead space
`sleeping_bag`, `crouch`, `flashlight`, `bread_bags`, `gone_forever`, `hole`.
Grades: `wl_night`, `wl_ext`, `wl_warm`, `wl_day`, `wl_police`, `wl_dead`, `wl_ins`, `wl_ins_night` (picked by the builders).
Night rule: the frame is dark, the subject lit (moonlight through the windows, the hall nightlight spilling into the
boys' doorway, the kitchen nightlight by the deadbolt, the attic line, phone, flashlight, police bars). Measured mean
luma: boys wide 36 (was 23 before lifting the night ambient), living wide 33, house + police 50.
Bench 2560 (one warm frame): quiet views ~0.2 s; police views 0.58 s (the red / blue bars relight the room every frame).
Open: cruisers are side-view sprites (none in from_window, only their light pools); the hole seen from the boys' room
(closet_sam) reads weakly, use `wl_dead('hole' / 'slot')` for the reveal.

---

# (previous film, kept for reference) The Ice Cream film's sets

Code: `sets_ice.py` (exec'd inside `sets.py` after `sets_bus.py`; its docstring and `IC_API` are the API reference). Every
name is `ic_* / IC_* / _ic*`; use `import sets as ST`. The older films' builders are unchanged (the bus film's are in
`sets_bus.py`, documented in its docstring). Stills, contact sheet, floor plan, index, frame check and bench: `_work/sets/`.

```
python3 tools/sets_sheet_ice.py                  # every variant (1280x720) -> ice_*.jpg + contact_sheet.jpg + index.json + floorplan.jpg
python3 tools/sets_sheet_ice.py --only ext_,ins_ # just some (contact_partial.jpg)
python3 tools/sets_sheet_ice.py --frame          # widest-camera edge check -> frame_check.json / .jpg
python3 tools/sets_sheet_ice.py --bench --no_stills --bench_only ext_kessler   # one 2560x1440 timing -> bench_2560.json
python3 tools/sets_sheet_ice.py --stage          # cast placed only from Spots (needs characters_ice) -> stage_*.jpg
```
Variants (the best examples of every state) are listed in `tools/sets_sheet_ice_list.py`.

## 1. Builders, views, states (levels = number or f(t))

| builder | views | states |
|---|---|---|
| `ic_street(view, ...)` | house, kessler, lane, lane_e, truck, curb, window_close, door, yard, roof, gap, plow, kwide, kporch, kdoor, kout, bathout, mitten, town | tod 'night' / 'morning' / '1958'; truck 'A' / 'B' / None / (x, y, fa); truck_win; truck_open 0..1; mittens; lina_mitten; truck_heads; street (`ST.ic_flicker(t0)`); porch, kporch; porches (neighbours' porch lights, one spec or a list of 4); win {liv, kitchen, bath, his, k2}; smoke (Kessler's chimney), our_smoke; walk / kwalk 'buried' / 'shoveled' / 'trodden'; tracks [(kind, [(x, y)...])]; props [('boot', x, y), ('mitten', x, y, c)]; plow dict(x (or f(t): live), y lane, dir, beacon); door_open, kdoor_open; blackout |
| `ic_living(view, ...)` | wide, couch, couch3q, tv, window, radio, opening | lamp, ceil, tv, hall, pink, beacon (`ST.ic_pass(t0)`), phone (+phone_at), flash; curtains 0 shut .. 1 open (0.04 = Lina's crack) or f(t); skull (glimpse 2 in the black TV); us (the reflection of the couch figures); frost (inside the window); blanket; radio 'table' / None; cone 'floor' (shards); blackout; truck |
| `ic_hall(view, ...)` | door, doorclose, back, hatch, bathdoor | hall, lamp, pink, beacon, phone, flash; door (deg / f(t)); rules, eighth; face (level or f(t) -> (k, rise)); knob_frost; hatch 0..1 / f(t); bath_door (deg, default 85) |
| `ic_kitchen(view, ...)` | window, wide | kitchen_light, pink, phone, flash; sash (0.12 = open a crack); cone 'sill'; stool 'window' / 'away' / None; frost |
| `ic_bath(view, ...)` | door, gap, window, wide | bath_light, beacon, pink (truck at B), phone, flash; towels 'rack' / 'gap' / 'jammed'; door; fog; wipe 0..1; (defaults: blackout, truck B) |
| `ic_1958(view)` / `ic_morning(view)` / `ic_town(view)` | any street view ('kout' = 1958 curb, 'mitten'; 'kporch' / 'house' morning; 'town') | 1958: sepia grade, old cars, Benny's footprints, the truck at B, the red mitten; morning: walks shoveled, Kessler's chimney smoking; town: a lone house without smoke, neighbours smoking, truck_x |
| `ic_insert(name, prop_kw, motion)` | rules, rule, doormat, wrapper, shatter, phone, card, radio, mittens, boot, fingers, towel, doorknob, outro, plow_cab | see `IC_INSERTS` notes (rule n 1..8, write; card time_ / temp / sub = the narration's words; outro n 0..4) |

Grades: `ic_ext` / `ic_night` (icy blue), `ic_warm` (home before the power dies, and after), `ic_dark` (blackout),
`ic_morning`, `ic_1958` (sepia-cold), `ic_ins`, `ic_ins_cold`, `ic_ins_warm` (outro).

## 2. The geography (one plan; `_work/sets/floorplan.jpg` draws every camera)

Metres: x east, y north (our front wall y 0), Y up. Our floor Y 0, ceiling 2.45; yards / street `IC_G` -0.5 with 0.34 m of
snow on the lawns (`IC_SNOWY`); feet in snow stand at `IC_FOOT` (sunk 0.16: never floating on the surface).
- OUR HOUSE (north side, facing south): kitchen front-west (window over the sink, step-stool), hall x -2.8..-1.4 (front
  door at x -2.55..-1.65 with the frosted panel 0.95-1.50 m and the CLEAR strip 1.50-1.68 m; bath door; opening to the
  living room; attic hatch at y 5.5-6.3), bathroom front x -1.4..0.4 (small frosted window), living room front-east
  (picture window x 2.2-4.6; the couch's BACK to the window, facing the TV on the back wall, so the black screen
  reflects the couch and the crack). Stoop and walk at x -2.1; picket fence y -6.3; Dad's car in the driveway at x 8.5.
- BIRCH LANE: kerbs y -8 (ours) and -16; streetlight at (-5.2, -8.5), flickers.
- MR. KESSLER'S HOUSE: front y -24 facing north, his window x 3.6-5.0 (opposite our picture window), door x 0.95-1.85,
  porch, chimney at (7.2, -28.4).
- HIS TRUCK: A = `IC_TRUCK_A` (-0.6, -9.55) heading west, serving window at (0.28, -8.43) facing our house between our door
  and our picture window (until 8:48). B = `IC_TRUCK_B` (-2.7, -14.45) heading east, serving window facing Kessler's door across his
  yard from 4 m west of his walk (from 8:50), so his door and porch stay in view past the cab from our side (the bathroom
  window POV); Mr. Kessler walks diagonally across his yard to it (anchor `kessler_half`). From our picture window Kessler's window is seen just past the truck's rear end (a 3 m step van 10 m
  away hides anything lower behind its roof, so "over the roof" is staged as "beside the snowflake, past the rear").

## 3. Staging data (every builder's result)

`sp.anchors[name]` -> Spot (.x .y feet / point in design px, .depth, .ppm, .height of a 1.85 m adult, .X .Yp .Y plan, .kind,
.turn, .seat_y); `sp.order_at(x, y)`, `sp.light_kw(x, y, Y)`, `sp.shadow(x, y)`, `ST.stage_figure(sp, who, spot, ...)`.
Depth-to-scale: ppm = S / depth; a figure m metres tall is m * ppm px at its feet. `index.json` lists every still's
anchors with plan and screen data. Paths on the street: `sp.paths['lina_out']` (porch to kerb), `['scuttle']` (fence ->
Dad's car -> eave -> the drop in front of our door), `['cross']` (our door -> Kessler's doorway).
Key anchors: street `truck_vendor` (him at the window, feet on the truck floor), `truck_window`, `truck_curb`,
`truck_reach`, `truck_roof*`, `truck_flake`, `lina_window`, `adam_grab`, `boot`, `mitten1/2`, `drop`, `fence0..5`,
`car_roof`, `eave`, `roof_edge_door`, `door_glass`, `kwindow`, `kporch`, `kdoor`, `kdoor_l/r`, `kwalk_mid`, `kessler_window_b`,
`kessler_half`, `cage`, `kwalk_shovel1..3`; living `couch_left/mid/right`, `couch_behind`, `curtain_crack`, `radio`, `tv_screen`,
`floor_cone`; hall `door_in`, `door_glass_in`, `door_frost_in`, `lock`, `knob_in`, `rules`, `under_hatch`, `hatch_face`,
`bath_door_hall`, `coats`, `bench`; kitchen `stool`, `sill_out`, `window_crack`, `fridge_photo`; bath `tub_sit`,
`door_kneel`, `gap`, `window_wipe`. `sp.info`: `tv_quad`, `window_quad`, `door_glass` (frosted, clear quads), `truck`.
Figures outside the front door in hall views sort between the outside layer and the door leaf.

## 4. Script beat -> set and view

| beat | set / view (state) |
|---|---|
| cold open: song in winter / free one on the porch / Mom knocks | `ic_street('lane')`, `ic_insert('doormat')`, `ic_hall('doorclose', face=...)` |
| Larkfield. Minus thirty-one. Sunrise | `ic_insert('card', time_='Larkfield.', temp='Minus thirty-one.', sub=...)` |
| Dad hands the radio; the orange light every hour | `ic_insert('radio')`, `ic_living('radio')`, `ic_street('plow', plow=...)`, `ic_insert('plow_cab')` |
| Kessler's shovel at six; the seven rules signed W.K. | `ic_morning('house')` (walks clear), `ic_insert('rules', door='kessler')` |
| 1958: Walter, Benny, one red mitten | `ic_1958('kout')`, `ic_1958('lane')`, `ic_1958('mitten')` |
| no scrape, our walk buried, no smoke | `ic_street('door')`, `ic_street('kessler')` (smoke 0) |
| three slow notes; rule 1 | `ic_street('plow')` pulling away; `ic_insert('rule', n=1)` |
| Eleven-oh-two; Elm, Maple, Cedar | `ic_insert('card')`, `ic_street('lane', truck=None)` |
| curtains; Lina waves; breath fogs his glass | `ic_living('window', curtains=f)`, `ic_street('gap', truck=None)` / `('kessler', truck=None, win={'his': .25})` (anchor `kwindow`) |
| the truck glides; no tracks; he leans out; mittens; flicker | `ic_street('lane', truck=(x(t)...))`, `('truck')`, `('window_close')`, `ic_insert('mittens')`, `street=ic_flicker` |
| the song stops outside; no breath cloud | `ic_street('house')`, `('curb')` |
| rule 2; the tap; the cone; the wrapper | `ic_insert('rule', n=2)`, `ic_hall('doorclose')`, `ic_insert('doormat')`, `('wrapper')` |
| on the kitchen windowsill; window open a crack | `ic_kitchen('window', cone='sill')`, `('window', sash=0.12)` |
| Lina holding the cone; it shatters | `ic_living('couch3q')`, `ic_insert('shatter')`, `ic_living(..., cone='floor')` |
| furnace stops; no bars; the TV reflection; the skull | `ic_living(..., blackout=True)`, `ic_insert('phone')`, `ic_living('tv', skull=f)` |
| rule 3; frost inside; one blanket; lullaby | `ic_insert('rule', n=3)`, `ic_living('wide', blackout, frost=f, blanket=True)` |
| boots on; fake Dad; leg shadow; orange light; real Dad | `ic_hall('door')`, `ic_insert('radio')`, `ic_living('window', beacon=ic_pass(t0))`, `ic_street('plow')` |
| rule 4; Two-ten; the door swinging; mittens in the snow | `ic_insert('card')`, `ic_hall('door', door=f)`, `ic_street('door', props=mittens, tracks=...)` |
| Lina at the pink window; he leans down; the grab | `ic_street('truck')`, `('curb')`, anchors `lina_window`, `adam_grab`, `truck_reach` |
| the boot frozen; the transformation; legs on the roof | `ic_insert('boot')`, `ic_street('window_close')`, `('truck')` (anchors `truck_roof*`) |
| the chase: fence, Dad's car, roof, the drop | `ic_street('yard')`, `('roof')`, `('door')` (path `scuttle`, anchor `drop`) |
| her mitten onto his string; Dad! static | `ic_insert('mittens', lina=True)`, `ic_insert('radio', static=1)` |
| white waxy fingertips; dry socks; she shivers | `ic_insert('fingers')`, `ic_living('wide', blackout)` |
| rule 5; Three-oh-five; Mom at the door; no breath; the face; the knob | `ic_insert('card')`, `ic_hall('doorclose', face=f, knob_frost=f)`, `ic_insert('doorknob')`, `ic_street('door')` (outside) |
| rule 6; the attic clicking; the hatch drops; the leg | `ic_hall('back')`, `ic_hall('hatch', hatch=f)` (anchors `hatch_face`, `under_hatch`) |
| the bathroom; towels; the leg tip; jammed | `ic_hall('bathdoor')`, `ic_bath('door')`, `ic_bath('gap')`, `ic_insert('towel')` |
| the song moves; wiping the window; truck at Kessler's door | `ic_bath('window', wipe=f)`, `ic_street('bathout', truck='B')` |
| Kessler shuffles out; "Walter!"; the twist | `ic_street('kporch' / 'kwide' / 'kout', truck='B', kdoor_open=True)` |
| rule 7 (his rule); Mr. Kessler halfway | `ic_insert('rule', n=7)`, `ic_street('kout')` / `('kwide')` (anchor `kessler_half`) |
| radio: real Dad; orange light on the window | `ic_insert('radio', talk=1)`, `ic_living('window', beacon=...)` |
| the crossing; legs; the blanket hooked; the cage | `ic_street('lane', truck='B')`, `('kwide')` (path `cross`, anchor `cage`) |
| the huddle in his doorway; the boy's voice; he shivers | `ic_street('kdoor')`, `('kout')` |
| the plow roars in; porch lights; the truck leaves; mitten drops | `ic_street('lane', truck='B', plow=..., porches=[...])`, `ic_insert('mittens', drop=f)` |
| the morning: shoveling, smoke, cocoa | `ic_morning('kporch')` (anchors `kwalk_shovel1..3`) |
| across town: a chime, no chimney smoke | `ic_town('town', truck_x=f)` |
| rule 8; the outro advice | `ic_insert('rule', n=8)`, `ic_insert('rules', eighth=True)`, `ic_insert('outro', n=0..4)` |

## 5. Checks (21 Nov) and open issues

- 89 stills + `contact_sheet.jpg` + `floorplan.jpg` + `index.json` (anchors of every still) in `_work/sets/`; stage test
  (`stage_sheet.jpg`): Adam and Lina seated on the couch, Mister Shiver at the serving window (the truck's curb-side wall
  sorts in front of him: he shows only through the window), Lina at the kerb, Mr. Kessler on his walk, Adam at the door.
- Frame check (52 views at their widest envelope): clean except `ext_plow` and `ext_window_close`, both false positives
  (pink / beacon light on white reads as the magenta test colour); no plate edges.
- Bench at 2560x1440 (one warm timing each): 0.10-0.18 s/frame (worst `hall_doorclose`). Live layers (a moving plow, a
  driving truck, f(t) curtains / hatch / door) redraw their parts every frame and cost more.
- Open: the 1958 grade (mono 0.72) mutes Benny's RED mitten: give that shot a colour-key or lower mono; from across the
  street (`ext_house`) truck A hides our front door (by geography); the across-town house reads dark behind the truck;
  `ext_plow` shows the streetlight's cone as a bright vertical bar; the plow cab is a flat insert (`plow_cab`), not a 3D set.
