# CAST: "If A Delivery Driver Rings Your Doorbell At 3 AM..."

The cast is in `characters.py`, built the same way as the police film's cast: the same rig, the same faces, outlines, `Acting` and lip sync.
- The police cast still works: officer, officer2, double, you, mum.
- Its API is unchanged.
- The full API is in the module docstring, under "Delivery film additions".
- All times below are film times in seconds, from `_work/align/timeline.json`.

## Who's who
| id | look | notes |
|---|---|---|
| `driver` | Nightline courier: brown shirt with a crescent NIGHTLINE patch, name tag "NO. 307", brown cap, work boots, keys on a carabiner. The handheld hangs from a coiled tether. | His face uses the officer's creepy-face system: ashen, gaunt, deep bags, a locked stare, and he never blinks. The cap's long bill puts his eyes in shadow; `light['brim']` sets how dark. |
| `you` | The police 'you' (hoodie), now in grey socks. | Use `light=dict(under='#bcd2ff')` for phone glow. |
| `mom` | The police mum's face in a plum terry robe with a shawl collar and a belt tied at the side. Nightgown, slippers, no glasses. | Use `squint_light` when she comes down the stairs. Her terror and tears come from the `fear`, `cry` and `hands_over_mouth` clips. |
| `lily` | 8 years old, 1.28 m. Big head, a bob with bangs, a yellow star clip, lavender pajamas with a moon print, bare feet. | She has a child's idle fidget, so she is never still. |
| `dad` | Memory, 21 years ago: red flannel, white tee, jeans, a moustache. | He looks like 'you' (family face). Grade the memory shots sepia. |

Heights to scale (`draw` height = feet to crown): driver 1.85 m, dad 1.82, you 1.80, mom 1.62, Lily 1.28.

## The driver's arc (automatic)
`Acting('driver')` puts the smile arc under every clip, so other clips layer on top of it.
- To switch it off, use `arc=False`.
- To override one window, use `a.smile_stage(t0, stage, t1)`.

| stage | from | beat |
|---|---|---|
| S0 | start | Flat, staring. |
| S1 | 66.2 | "The driver smiles at the camera". Closed lips; the smile is fixed. |
| S2 | 139.0 | "Just finish it". Teeth show. |
| S3 | 184.8 | "Who's the lucky one". It reads as wider by "wider now" at 196.5. |
| S4 | 340.9 | He leans close: "Ma'am". The grin is toothy with gums. |
| OFF | 435.8 | "His face is perfectly still". No smile, life 0.12, no twitches. |
| S5 | 446.4 | "Smiles again, wider than before". The widest stage: it saturates at the jaw line. |

- **Mouth lag:** `talk()` delays his mouth 0.2 s behind the voice. The self-test measures 0.18 s ("the lips catch up").
- **Eyeshine:** `eye_flash(370.77, 0.5)` makes his pupils shine white over the brim shadow and returns a `stinger` event. It reads best on the colour doorbell; the IR view blows out his near face.
- **`escalate(a, t0, t1, kind)`:** call it from `film.py`'s `escalate()`.
  - Driver twitches and jerks: every 4–6 s from 196.5, every 2.2–3.2 s from 340.9, and every 1.5–2.5 s from 446.4.
  - None while his face is still.
  - 'you' and mom get a fear tremble that builds (`FEAR_ARC`).

## Beat map: clips to call
| time | beat | clip(s) |
|---|---|---|
| 34.4 | doorbell rings | `ring_bell(t0)`: his fingertip rises at the lens. Returns `doorbell_chime` (kind ding_dong). |
| 45.6 | "a tablet in one hand" | `carry_tablet()` |
| 118.2 | holds the tablet up | `hold_tablet_up(t0, t1)`: the screen faces the camera and his grin stays visible above it. For the insert, use `draw_tablet(sig='initial', ink, ts='3:09 AM' / '3:08 AM', glitch)`. |
| 159–161 | lowers it, looks at the box | `look_at_box(t0, t1)` |
| 178.5–183 | tilts the box, taps the label | `tilt_box`, `BoxActing.tilt(angle<0, turn)`, then `tap_label(t0, n=2)`, which returns `box_tap`. The label's TO line is blank. |
| 260.1 | "tilts his head like he's listening" | `listen_tilt(t0)` |
| 279.6 | mom on the stairs | `squint_light`, then `expr('fear')` at 295 |
| 340.9 | leans close | `lean_close(t0)`. Use `Layer(a.depth(1.0), ..., ref_depth=1.0)` and `aim=(960, 470)` so the fisheye bulges his face. |
| 353.2–365.6 | the chain, the wrist | mom `reach_chain(t0, t1)` returns chain rattles and her hand shakes. You `catch_wrist(355.8)`. Use `hand_pos('mom', ...)` for her wrist. |
| 370.8 | eyes shine | `eye_flash(370.77, 0.5)` |
| 378–431 | the box knocks | `BoxActing.knock(t)` (two, a pause, one more) or `knock_loop(t0, t1, accel=0.3)` for "faster". Returns `box_knock`. Each knock bulges and jolts the box. |
| 402.4 | mom: both hands over her mouth | `hands_over_mouth(t0)` + `cry` |
| 437.5 | head turns slowly to the side yard | `slow_look_side(t0, 3.0, side, back=446.4)` |
| 460.9 | sets the box against the door | `set_box_down(t0)` returns `box_drop` and `box_scrape`. Pair it with `BoxActing.slide`. |
| 465.7 | photo of the box | `take_photo(t0)`: the flash fires at us; returns `camera_shutter`. |
| 467.9 | walks to the van, climbs in | `walk_away(t0, t1)` + `climb_in(t0)`. The layer path moves him. |
| 485 | mom on the hallway floor | `sit_floor(t0)` (you: `hold_close`). Stage it in 3/4 (`turn` ±0.5–0.7): straight-on, the knees foreshorten badly. |
| 541 | Lily's door | you `push_door(t0)` returns `door_creak` |
| 560 | photo: Lily leaning out, his tablet up to her | Lily `lean_out(t0, reach_t=...)` returns `touch_tap`. The driver uses `reach_up(t0, stretch=...)`. Recipe in `tools/cast_sheets.py` `sheet_lily_window`: clip Lily above the sill, draw the sill and the tablet, then `draw_arm('lily', ...)` over the sill. |
| 231–240 | keys in the bowl | `draw_keys_bowl(drop=t - t_release, hand=True)`. Impact is at `KEYS_DROP_IMPACT` (0.24 s). Flashback: dad `drop_keys`. |
| 305–332 | memory: dad signs | dad `sign(t0, t1)` |
| 598–610 | sunrise: the box | `BoxActing.cut(t)` (the tape is cut), then `draw_box_inside` (empty, the rusted keys on the D-A-D bead keychain) |

## Sound events the cast emits
Each event is a dict: `{t, name, gain_db, pan, params, who}`. The audio owner maps the new names. Suggested Epidemic files are in `_work/samples/epidemic/sfx`.

**New names**

| event | suggested sound |
|---|---|
| `box_knock` | Cardboard Box, Punch Or Kick / Impact, layered with a soft knock |
| `box_tap` | Cardboard Box, Impact, quiet |
| `box_creak` | Cardboard Box, Rummage |
| `box_drop` | Cardboard Box, Impact |
| `box_scrape` | Plastic Tub / Cardboard Drag; `params.dur` |
| `keys_drop` | Keys, Bunch Of House Keys, Drop |
| `touch_tap` | Touchscreen, Tap Hard |
| `stylus_scribble` | touchscreen typing, slowed; `params.dur` |
| `camera_shutter` | phone camera |
| `cloth_rustle` | Cloth, Flap, quiet |
| `van_step` | metal step |

**Police names reused:** `doorbell_chime` (use the Ding Dong), `chain_lock` (kind rattle), `footsteps_porch`, `car_door_close`, `breath` (gasp / sob), `door_creak`, `stinger` (eye_flash).

## Sheets
The sheets are in `_work/cast/`. Regenerate them with `cd film && python3 tools/cast_sheets.py [name ...]`; it takes about 10 s.

| sheet | shows |
|---|---|
| `lineup` | The whole cast to scale. |
| `driver_turnaround` | Front, 3/4 left and right, profile, back. |
| `driver_smile_arc` | S0–S5, OFF and eyeshine. |
| `driver_doorbell`, `driver_doorbell2` | Through the engine doorbell lens: ring, tablet up, fisheye lean, eyeshine, OFF head turn, IR, listen, S5, photo flash, walk away. |
| `driver_acting`, `driver_acting2` | Frame strips of the driver's clips, with their sound events. |
| `family_faces`, `family_acting` | Mom, you, Lily and dad: faces and frame strips. |
| `lily_window` | The 3:41 photo from below, and a wide with the too-long arm. |
| `props` | The knock sequence, tape cut, box inside, tablet screens, keys bowl drop, new and rusted keychain. |

## Checks
- **Self-test:** `python3 characters.py --selftest`.
  - Lip sync: r 0.67 on driver lines 28–30.
  - Mouth lag: 0.18 s.
  - The smile arc is monotonic, with OFF at 440.
  - Knock: 2-then-1 with the bulge.
  - Escalate.
  - Phone-at-ear for the new cast.
- **Speed** at 2560x1440 in one process: full body 12–22 ms; frame-filling bust 18–28 ms (officer 25 ms); frame-filling box ~45 ms; tablet insert 5 ms; keys bowl 5 ms; box inside 29 ms.
- **Police regression:** officer, mum, double and officer2 are pixel-identical within run-to-run raster noise. The only change is that 'you' now wears socks.
- **Paths:** `VOICE_WAV` and `VOICE_WORDS` now point at `W/align`. The envelope cache is in `W/cache`.


## Later changes (film assembly)
- The tablet's first letter (`sig='initial'`) now draws 68 % of the cursive J (stem and hook, then the ink blot), so it reads as a letter that stops halfway, not as a question mark.
- Back views: the `messy` and `curly` hair now covers the back of the head down to the nape (before, a bare skin oval under a small hair cap read as a blank face in the hall shots seen from behind).
- The 3:41 delivery photo no longer uses `reach_up(stretch)` or a long `lean_out` arm: it is `sets.photo_lily_scene()` with plain arm lengths (see SETS.md).
