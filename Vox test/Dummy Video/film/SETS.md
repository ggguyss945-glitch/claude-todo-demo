# Dummy film sets (sets.py)

"If Your Grandpa's Ventriloquist Dummy Tells You A Joke... DON'T LAUGH". The new code is the last section of `sets.py`
(after the delivery section); the module docstring lists the API. The police and delivery builders are unchanged.

## How to run
```
python3 tools/sets_sheet.py                    # 56 stills (1280x720) + contact_sheet.jpg + index.json -> _work/sets/
python3 tools/sets_sheet.py --only hall,ins_   # a subset
python3 tools/sets_sheet.py --frame            # + framing check at each view's widest move -> frame_check.json / .jpg
python3 tools/sets_sheet.py --bench            # + bench_2560.json (2560x1440, 1 OpenCV thread, caches warm, 2.5 %/s push)
python3 tools/sets_sheet.py --delivery         # delivery regression (--police: police regression)
```
Stills go through the engine like the film (lens, grade, set fx, the VHS look). People are left out; `index.json` lists each
variant's anchors (x, y, depth, height of a 1.85 m adult there) and its camera envelope.

## How the sets work
- **One floor plan.** Grandpa's house is laid out in metres (`HView`: x right facing the back of the house, y from the
  front wall back, Y up) and every view is a camera placed in it. The kitchen seen down the hall, through the living-room
  doorway and from its own doorway is the same kitchen: the table, Grandpa's chair facing the hall, the amber pendant, the
  mug, the window behind the chair. Plan: hall x -1.35..1.35 (stairs on the right, first riser y 0.9), kitchen opening at
  the end (y 6.0), living room to the left (arch y 3.4..4.8, doorway to the kitchen, TV on the back wall, couch mid-room
  facing it, front window and bookcase on the front wall), den door at the end of the hall on the right.
- **Light is modelled.** Each static layer is drawn as albedo and multiplied by a light map (`_lmap`: ambient + lamps).
  A lamp that changes (hall light, pendant, living-room lamp, den lamp, the TV) is its own `blend='plus'` layer (albedo x
  that lamp) whose alpha is the lamp's level, so lights add up and a flicker or a lamp going out costs nothing.
  Level specs everywhere: a number, `f(t)`, or `dict(flick=[(t0, dur)], out=[(t0, t1)], on=t, off=t)`.
- **Engine additions (opt-in, nothing else changes):** `Layer(..., blend='plus'|'screen'|'multiply')` in
  `engine/scene.py`; `post['vhs'] = dict(t, track, bezel, ...)` in `engine/post.py` (per-line wobble, rolling tracking
  band, chroma bleed, tape snow, scanlines, CRT glass curvature and rounded tube, phosphor glow, optional TV bezel).

## Builders
| builder | what | lens / grade |
|---|---|---|
| `gp_hall('kitchen')` | Down the front hall to the lit kitchen opening: Grandpa's chair at the table (`kitchen_chair`), the steaming mug, the bench with the black leather case (`case='closed'` with the envelope, `'open'` with the velvet hollow, `None`), his coat and hat on the hooks, the 1974 poster, the grandfather clock (live pendulum, `pendulum_ticks()`), the arch to the living room, the den door (`den` 0..1). `beam=` the knee-high flashlight moving down the hall. | lens, `gp_house` / `gp_dark` |
| `gp_hall('door')` | Facing the front door: the stairs coming down on the left, the bench and case on the right. `door` 0..1 or f(t) opens it (night, or `tod='morning'` with the street outside). | lens, `gp_house` / `morning` |
| `gp_hall('stairs')` | From the foot of the stairs up to the moonlit landing window (`step1/step3/step6`, `landing`). `beam=dict(keys=[(t, 0.92, 1.55)], Y=0.82, aim=(0, 0.45, -1))` = his flashlight in your face (flare). | lens, `gp_dark` |
| `gp_kitchen('table'\|'chair')` | The kitchen from its doorway / seated across the table: mint cabinets, teapot wallpaper, checker floor, red kettle, amber pendant (`kitchen` level, `sway`), the captain's chair, the mug with spoon and steam, the sugar bowl. `tod='morning'` for the last scenes. | lens, `gp_house` / `morning` |
| `gp_living('tv'\|'couch')` | `'tv'` from the couch: the CRT on its walnut cabinet with the VCR (blinking 12:00), the doorway to the kitchen with his chair in it, the arch to the hall. `'couch'`: the couch under the floor lamp, the front window with drapes, the bookcase (`bookcase_top`). `tv=dict(on=t, snow=0.6, mode='tape', pulse=f)`; `content=f(pen, W, H, t)` draws the tape (default: the studio). | lens, `gp_house` / `tv_glow` |
| `gp_den()` | Wood panelling, the show posters, the green wingback armchair (`armchair`), the brass lamp (`lamp=dict(out=...)`), the rug (`rug`), trophies and an empty dummy stand. | lens, `gp_house` |
| `gp_studio('full'\|'close')` | The 1974 'Saturday Morning with Walter Kemp' stage full frame: sunburst, cardboard clouds, rainbow, marquee sign with chasing bulbs, the red stool (`stool`, `knee`), the APPLAUSE box, the audience's heads shaking with `laugh=laugh_waves([...])`. `sp.fx(t)` carries the VHS look; `bezel=1` for the push in from the living room. | none, `vhs74` |
| `studio_content(figures, laugh)` | The same stage as a CRT content function (4:3 crop); `figures(pen, t)` draws Walter and the dummy in the studio's 1920x1080 space. | |
| `hospital('bed'\|'close')` | Mint room, the bed (`bed_head`, `bed_lap`), the visitor chair (`chair`), the monitor with a live ECG (`bpm`, `flat=t`; `monitor_beeps()`), IV pole, blinds, whiteboard, clock. | lens, `hospital` |
| `stage_1962()` | The Palace, 1962: curtains, footlights, spotlight, stool, mic, the audience. | lens, `memory` |
| `museum('case'\|'wide')` | The vitrine on its plinth (`display`; the glass is a layer in front of him), the plaque, the spotlight, the gallery. | lens, `museum` |
| `street_morning('window'\|'outside')` | 8 AM. From behind Owen at the front window (`owen`) with the museum van pulling away (`van=dict(drive=('out', t0, t1, x0, x1))`), or the house from across the street (`owen_window`: draw him before the `so_glass` layer). `museum_van()` draws the van. | lens, `morning` |
| `bedroom_doorway()` | Your bedroom at home from the bed: the open door with the hall light behind it (`doorway`). | lens, `gp_dark` |

## Inserts (`insert(name)` or `gp_insert(name)`)
| insert | prop_kw |
|---|---|
| `letter`, `letter_close` | The seven rules in Grandpa's shaky hand on hospital notepaper, the bottom torn off. Rule six is in a neater, colder hand (he changed it). `hl=n` lights rule n, `smear=0..1` makes rule six run, `show=0..7`. |
| `envelope` | 'For whoever is in my house tonight.' taped to the leather lid. |
| `ps` | The torn P.S., signed 'Walter. The real one.' |
| `latches` | `latch=0..1` or `(l, r)`: the brass latches flip open. |
| `case_open` | From above: the velvet bed with his shape pressed into it, `warm=0..1` shimmer. |
| `mug` | The show mug, `stir=f(t)` (turns), two sugar wrappers, the sugar bowl, live steam. |
| `back_slot` | The jacket's back with the slot. `hand=0..1` (your hand goes in), `paper=0..1` (the P.S. slides out). |
| `squeeze` | Inside him: your hand and the warm old hand that lets go of the stick (`take=0..1`) and squeezes (`squeeze=squeeze_pulses([t1, t2, t3])`). |
| `photo` | 'Walt & Winks '74' (drawn with the cast's `walter74` and `winks`). |
| `poster_1962`, `vcr` | The sepia first-show poster; the VCR with the tape ('SAT. MORNING w/ WALTER KEMP 1974'), `tape=0..1`, `play`. |

**The rule card that lies:** `rule_card_lie(cv, n, text, t, reveal, mode)` draws the police rule card on the HUD; at
`reveal` (card clock) `'tear'` rips it through its first text line with a red seam, `'smear'` runs the ink and scrawls
LIE in his hand, `'flicker'` is a two-frame 'LIE?' for rule two (the false lead).

## Hooks for the director and sound
- Lights: `sp.info` holds the level functions (`hall_light`, `kitchen`, `lamp`, `tv`, `tv_level`, `spot`, `reading`).
  Use them for the cast's light so people dim with the room. `tv_level(sp.info['tv'], t)` is the TV's light.
- Sound moments the sets can time: `pendulum_ticks(t0, t1)` (the hall clock), `monitor_beeps(t0, t1, bpm, flat)`,
  `laugh_waves([...])` (studio laughter = applause sign = the dummy's moves), the VCR clock, the TV `on`/`snow` times, lamp
  `flick` / `out` windows (bulb buzz and pop), the beam's `on` (flashlight click), `squeeze_pulses` times.
- Anchors: every builder documents its anchors; `index.json` has them per variant (x, y, depth, height).

## Camera
- Each view has `info['cam_env']`: the frame-centre range (x, y on the depth-1 plane at zoom 1), the dolly zoom and the
  optical f the set is built for. `--frame` renders every view at its four corners (+8 px handheld) and at its deepest
  push over magenta: results in `_work/sets/frame_check.json`.
- Interiors are 2.5D: push with optical `f` (KeyCam) and keep the dolly `zoom` at 1.3 or below. A big dolly makes the
  furniture slide on the floor. Keep pans within `cam_env`.
- The post move pads with reflection. Any post offset (`post_push(x=, y=)`, a crop offset) needs a post zoom of at least
  1 + 2|offset| / 1920, or the frame shows a mirrored copy of the set (the trap from the last film).

## Speed
See `_work/sets/bench_2560.json` (2560x1440, one process, one OpenCV thread, caches warm): numbers in the report and in
the table at the end of this file once the bench has run.
