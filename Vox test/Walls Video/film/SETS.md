# SETS.md: the sets of "If The Ice Cream Truck Plays Its Song In Winter... DON'T GO OUTSIDE"

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
