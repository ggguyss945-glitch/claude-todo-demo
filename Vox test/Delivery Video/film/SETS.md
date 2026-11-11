# Delivery film sets (sets.py)

The police sets were re-dressed for 3:07 AM: house 144, the porch, the street, the doorbell and peephole views, the hallway and their lighting. Police defaults are unchanged. Re-rendered police sets differ from the pre-change renders by about 1 grey level on average, which is the engine's own run-to-run noise (0.9 mean between two identical runs).

The new delivery code is the section at the end of `sets.py`, and the module docstring lists the API.

## How to run
```
python3 tools/sets_sheet.py                 # 49 stills (1280x720) + contact_sheet.jpg + index.json -> _work/sets/
python3 tools/sets_sheet.py --only lily,app # a subset
python3 tools/sets_sheet.py --bench         # + bench_2560.json (2560x1440, 1 OpenCV thread, caches warm, 2.5 %/s push)
python3 tools/sets_sheet.py --police        # police regression stills
```
Stills are graded through the engine the same way as the film. Sets that need people are shown empty. `index.json` lists each variant's anchors.

## Builders
All builders are in `SETS` and `build()`.

| builder | what | lens / grade |
|---|---|---|
| `delivery_porch(view='doorbell'\|'peephole', van, hazard, box, ir, tod, era)` | Porch at 3:07. The white NIGHTLINE van is at the curb with its hazards blinking, which puts an amber spill on the yard, the railing and the houses across. All windows across are dark except one. `box='door'` places the tall box against the door, where the fisheye shows it as a slab at the left edge. `box='boots'` places it beside the driver. | `doorbell` / `doorbell_ir`, `doorbell_night` |
| `delivery_street(van, era)` | House 144 seen from across the street, all windows dark, with the van in front. | `night_blue` |
| `memory_porch('doorway'\|'street')` | 21 years ago: the same van, the box on the porch, and the family's old wood-panel station wagon. | `memory` (sepia) |
| `porch_doorway(tod='night'\|'dawn', era, box, door_open)` | The front door open, framed from 1.45 m inside. The box stands at the threshold, backlit at night. At dawn its tape is cut, the flaps are open and daylight pours in. `door_open=f(t)` swings the door. | `interior_dim` / dawn blend |
| `sunrise_porch('doorbell'\|'doorway')` | 6:12: the box is open and the van is gone. | `dawn` |
| `delivery_hall(stairs, bowl, lamp, door_open, outside)` | The police hall facing the door. The stairs replace the coat hooks; the key bowl is `'house'` or `'dad'`. | `lens`, `interior_dim` |
| `hall_back(bowl, upstairs, hazard)` | From the front door into the house (behind you): the side table with lamp, bowl and photo, the stairs climbing to the dark gallery, and the kitchen doorway at the end with the microwave clock showing 3:11. | `lens`, `interior_dim` |
| `upstairs_hall(lily_door, window_open, hall_light, mom_door)` | Lily's door at the end of the corridor, open a crack (moon-glow wedge on the floor) or wide open (her window). | `nightlight` |
| `lily_room(view='room'\|'window', window_open, bed, hazard, drive)` | Room view: moon nightlight, star quilt, vent, crayon drawing of mom and two kids (no dad), open window with billowing curtains. Window view: the side yard, the fence, and the van at the end of the side yard, which can pull away with its headlights off. | `nightlight` |
| `side_yard(window_open, hazard)` | Under Lily's window, looking up. This is the view of the 3:41 photo. Her curtain streams out of the open sash. | `nightlight` |
| `phone_bg(bg)` + `app_phone(cv, screen, t, x, y, scale)` | The delivery app on the police phone UI, drawn in the HUD. `phone_bg` gives the blurred background set. | `phone_dark` |

### `app_phone` screens (`APP_SCREENS`)
- `notify_delivered`
- `order` (sender RETURN)
- `notify_photo`
- `photo_hall` (you from behind, 3:11)
- `photo_gone`
- `attempted` (pickup 6:12 a.m.)
- `notify_return`
- `photo_lily` (3:41, signed "Lily.")
- `notify_on_way`
- `on_way` (sender "Lily" in a child's hand)

The two in-app photos are rendered from the real sets plus the `characters.py` figures and cached once per size.

### Inserts
Use them through `insert(name)`.

| insert | content |
|---|---|
| `label` | The shipping label (FROM: RETURN, blank TO) with the driver's finger. |
| `label_to` | Close-up of the blank TO line with the finger. |
| `label_lily` | The label with TO: "Lily". |
| `tablet_sign` | The tablet with your initial, using `lens='doorbell'` so it fills the doorbell frame. |
| `tablet_lily` | The tablet with "Lily." signed. |
| `key_bowl` | The key bowl. `prop_kw=dict(drop=0..1)` drops keys in. |
| `key_bowl_dad` | The key bowl with dad's keys. `prop_kw=dict(drop=0..1)` drops them in. |
| `box_keys` | The open box with the rusted keys inside. |
| `van_seat` | The empty driver's seat with the blinking hazard telltale. |
| `hazard_switch` | The dashboard hazard switch. |

The tablet, the inside of the box and dad's keyring come from `characters.py` (`draw_tablet`, `draw_box_inside`, `draw_keyring`), so they match the props the cast holds.

## Hooks for the director and sound
- **Van flashers:** `hazard(t, rate=1.25, t_on, t_off)` returns 0..1 for the flashers. Pass `hazard=dict(t_off=...)` to switch them off.
- **Flasher sound:** `hazard_ticks(t0, t1)` returns the relay on/off times for the hazard-tick SFX. Every set's `info['hazard']` is f(t), for an amber rim light on people.
- **Van options:** `van=dict(...)` takes these keys:
  - `driver`: True draws his silhouette with cap in the cab. **Set False whenever the driver character is on the porch.**
  - `door`: 0..1, the sliding door.
  - `drive`: `('out', t0, t1, X0, X1)`.
  - `head`: headlights; default off.
- **Knocks:** `box=dict(at='door', knock=knock_pulse([t, t+.32, t+1.1]))` jolts the static set box and puffs dust off it.
- **Two boxes:** the set box is static dressing in true perspective, used at the door, the threshold and at dawn. When the box acts in frame (tilting, bulging, being carried), use `characters.draw_box` at `anchors['box_boots']`.
- **Doorbell anchors:** `driver`, `driver_close`, `box_boots`, `box_door`, `steps`, `path_mid`, `gate`, `van_cab`, `van_door`; paths `porch_to_van` / `van_to_porch`.
- **Hall anchors:** `stairs_low` / `stairs_mid` / `wall_sit`.
- **Reverse hall:** paths `stairs_down` (mom), plus anchors `hall_end` and `wall_sit`.
- **Side yard:** anchors `driver` and `lily_window`.
- **Grades:** `dawn`, `memory` and `nightlight` are registered by name in `engine.post.GRADES` when `sets.py` is imported.

## Speed (2560x1440, one process, 1 OpenCV thread, sets only, full frame including lens and grade)
- **All variants:** 50 variants averaged 0.149 s/frame.
- **Slowest:** the IR doorbell at 0.257 s, then the hazard-switch insert at 0.26 s. Everything else is at 0.07-0.25 s.
- **Budget:** the police budget is 0.6 s/frame, and the cast adds roughly 20-50 ms per figure.
- **Doorway caution:** do not put an optical punch-in (`Cam.snap`) on the frame-sized hall layers. At 2560 the caches blow the 700 MB layer cache and every frame re-bakes (3.5 s/frame). Use `porch_doorway()` for the framed doorway; `doorway_camera()` only dollies.

## Open points
- `film.py` is still the police shot list. It needs these changes:
  - install `hud._hand = characters.hud_phone_hand`;
  - use `delivery_*` sets with `police=False`;
  - set the van's `driver` flag to follow the driver character;
  - add amber rims from `info['hazard']`.
- The rule-7 window montage can reuse the police `kitchen()` and `living_room_window()` with `police=False`. There is no bathroom window or mom's-room window yet.
- The lock screen shows Wednesday (Thursday for the final night). The tablet's initial comes from `characters.draw_tablet` and is currently 'J'.
