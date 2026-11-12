# CAST: "If Your Grandpa's Ventriloquist Dummy Tells You A Joke... DON'T LAUGH"

The cast lives in `characters.py`. It uses the same rig, outline style, `Acting` timelines and lip sync as the police and delivery casts, and all of their API still works.
- The full API is in the module docstring, under "Dummy film additions".
- This film's cast takes the plain names `mom` and `you`. The delivery designs are still there as `mom_delivery` and `you_police`, and the other police and delivery ids are unchanged.
- All times are film times in seconds, taken from `_work/align/timeline.json`.

## Who's who
| id | look | notes |
|---|---|---|
| `winks` | **Mister Winks**, an original vent figure 0.85 m tall, made to be menacing at every size. Ivory-to-pale-peach painted wood under a hard lacquer: one hard highlight on the forehead and one on each cheekbone, fine crazing, two paint chips, two small faded rouge circles and a few faint freckles. Glossy painted eyeballs with small near-black irises and a hard pinpoint highlight, no lashes; the wooden upper lids rest a little low (he is sizing you up), with a faint grey-violet shadow under each eye. Heavy, sharply arched black-brown painted brows angle down toward the nose: a sly scowl even while he grins. A small carved nose. A wide, tight painted grin in thin dark-red lips that stretch to the marionette lines, with painted creases hooking up from the corners. Teeth show only as strips when the jaw is open, around a black void with a dark-red rim. The **lower jaw block** is cut on two marionette slot lines with deep dark grooves. Carved auburn hair with sculpted ridges, a glossy shine and a hard side part. He wears a burgundy usher's jacket (brass buttons, gold braid, shoulder boards), a pillbox cap, white gloves and navy trousers with a gold stripe, and carries the usher's flashlight. There is a slot in his back. | He has no breath and no drift. He only moves in hard wooden ticks, ratchet head turns and jaw snaps. His glass eyes follow the lens (`lock`). His left eye is the wink eye. |
| `grandpa` | 86. Bald with a white fringe, big ears, the hooked Kemp nose, bushy white brows, deep folds and liver spots. Moss cardigan over a checked shirt. | The thing that lived as Walter. Use `expr('still_smile')`: the smile is a little too still. His lips barely move when he talks (`talk` 0.3). He blinks rarely. |
| `grandpa_bed` | The same man in a hospital gown, gaunt, with an ID band on his left wrist. | Use `in_bed()` and give him the dummy with `draw_lap(..., between=blanket)`. |
| `walter` | The real Walter, in that body for one hour. | A scared cast member: he blinks and trembles. Use `expr('lucid')` and `grab_wrist()`. He whispers the "It wasn't me" lines (G, fx memory, 104.2-106.6). |
| `walter74` | Young Walter on the 1974 tape: pompadour, sideburns, powder-blue suit with huge lapels, a big shirt collar and a wide tie. | Use `showman()` for the big fixed TV smile. His lips never move (`talk` 0): never call talk on him. |
| `mom` | Mid 40s: long camel coat, chunky teal scarf, dark hair in a low bun with loose strands, tired eyes. | |
| `owen` | 9 years old: cowlick, big ears, a missing front tooth, mustard hoodie, red sneakers. | `try_wink_kid()` closes both eyes. Use `expr('kid_grin')` for his grin. |
| `owen_new` | The thing in Owen's body, from 567.06 ("Owen's eyes close"). | A creepy cast member: he never blinks, keeps the glass stare and his lips barely move (`talk` 0.3, like Grandpa). Use `doorway_smile()` and `hold_mug()`. |
| `you` | About 16: dark curtain bangs over the ears, a blue denim jacket over a grey hoodie, black jeans, white sneakers. | |

Heights to scale (`draw` height = feet to crown): winks 0.85 m (`DUMMY_M`), walter74 1.78, you 1.74, grandpa 1.72, mom 1.65, owen 1.32. Stage seated people in 3/4: straight-on, their knees foreshorten.

## Mister Winks's arc (automatic, `WINKS_ARC`)
Over the night the painted grin widens and tightens (`grin_w`), the irises shrink, the brows sharpen and drop toward the nose, the lids sink lower, the shadows deepen and the crackle spreads (`crack`). On the 1974 tape (`tape`) the man inside pleads through wet, wide eyes; with Owen inside (`owen`) the eyes are desperate under the same painted grin.

| stage | from | beat |
|---|---|---|
| S0 | start | The hospital and the case. |
| S1 | 173.97 | In Grandpa's chair. |
| S2 | 250.39 | His head has turned all the way round. |
| S3 | 314.69 | He stands up on the chair. |
| S4 | 401.93 | "He smiles up at me". |
| S5 | 523.43 | On Owen's lap. This is the widest stage. |
| asleep | 567.06 | Lids shut, with Owen inside him. |
| owen | 655.6 | "Opens his eyes": the lids creep open over 1.8 s. The brows plead, the eyes are wet and a tear runs, all under the widest grin. |

- **The 1974 tape:** use `Acting('winks', arc=WINKS_TAPE_ARC)`. He is in `show` (cheerful) until 448.58 ("looks straight into the camera"), then in `tape` (the real Walter crying inside).
- **Overrides:** to override one window, use `a.smile_stage(t0, stage, t1)`.
- **Ticks:** `escalate()` adds his wooden head ticks: every 5-8 s from 174, every 3-5 s from 315 and every 2-3.5 s from 402 s. There are none while he sleeps, and none with `kind='worked'` (on a lap).

## The jaw (speech) and the clacks
- **Talking:** `a.talk(...)` on `winks` drives `pose.jaw`. It drops hard and snaps shut on each syllable, from the local contrast of the voice envelope. Each snap emits a `dummy_clack` event (kind `speech`, -14..-8 dB).
- **Measured on his joke (271.3-274.4 s):** r = 0.79 against the voice at a 0.02 s lead, with 14 clacks for 15 syllables. Human mouths stay as before (Owen 534.7 s: r = 0.86).
- **Which lines he says:**
  - Use `talk_lines(lines, ('K', 'U', 'R', 'G'), fx=...)` as the shot needs: K is the joke, U the copied voices, R the tape crying, and G with fx `dummy` is Grandpa's voice from inside him.
  - For U lines, don't move Mom's mouth.
  - G with fx `memory` belongs on `grandpa` (bedtime) or `walter` (the hospital whisper).
- **Between lines:**
  - `jaw_hang(t0, 0.3)` leaves the jaw a little open.
  - `jaw_drop(t0)` drops it with gravity and returns `dummy_jaw`.
  - `clack(t, dur)` snaps it shut and returns `dummy_clack`. With `dur` 1.6 it closes very slowly first: "It closes, very slowly. Clack."

## Beat map: clips to call
| time | beat | clip(s) |
|---|---|---|
| 68.2-75.7 | memory: tuck in, the three squeezes, "See you in the morning, kiddo" | grandpa `tuck_in`, `squeeze_hand(t0, 3)`, `talk` (lips barely move) |
| 76-94 | hospital: Grandpa works him one last time | grandpa_bed `in_bed` + `vent_pose(side=1)`; winks `sit_dummy` + `puppet`; `draw_lap(..., between=blanket)` |
| 96.9 / 104.2 | the wrist / "It wasn't me. It was never me." | walter `grab_wrist(97.3)`, `expr('lucid')`, `talk` on lines 37-38 |
| 151.7 | Mom pops the latches | mom `open_latches(~153.4)` returns `case_latch` x2 |
| 174-183 | in Grandpa's chair, the flashlight pointed at the ceiling | winks `sit_dummy(hands='table')`, `torch_on(t, 0, 1, hold='up')` |
| 184.4 | Mom smells the mug, all the colour leaves her face | mom `smell_mug(184.4, None, -1, pale_at=186.6)`; prop `mug` |
| 222-234 | the voices from upstairs (U) | optional: his jaw moves in the kitchen while the voice comes from above (`talk_lines` U) |
| 243.5 / 247.1 | "See you in the morning, kiddo" / "Dad?" | winks `talk`; mom `hand_to_mouth(247.0)` |
| 250.4-257.8 | the head has turned all the way; the jaw hangs; it closes very slowly; clack | winks `head_turn_180(t0, 3.2)` (body turned away), `jaw_drop(254.1)`, `clack(257.84, 1.6)` |
| 271.3-278.8 | the joke | winks `talk` (K) |
| 283.5 | Owen snorts | owen `snort(283.5)` |
| 286.6 / 287.1 | clack; a glove lifts off the table | winks `clack(286.56)`, `glove_lift(287.1)` |
| 290.2 | you clamp a hand over Owen's mouth | you `clamp_mouth(290.2)`; Owen `expr('fear')` + `still` |
| 312.3 / 313.7 / 316-320 | fingers curl, elbow bends, hands flat and he stands on the chair | winks `fingers_curl(312.4)`, `elbow_bend(313.7)`, `stand_on_chair(316.0)` |
| 327.6-333 | a knee-high flashlight moving down the hall | winks `torch_on(327.6, 90, hold='side')` + `torch_sweep`; beam with `draw_torch_beam` |
| 354.6 | on the stairs, three steps up, the torch in your face | winks `sit_dummy()` (perch on the 3rd step), `torch_on(t, 0, -1, hold='lens')`; glare `draw_torch_beam(..., lens=1)` |
| 359.0 / 360.2 | grab him, hand through the slot | you `grab_dummy(359.0)`, `hand_inside(360.3)` |
| 373.7 / 374.8-377.3 | the hand squeezes once, twice, three times | you `squeezed([374.9, 375.8, 376.6])` returns `hand_squeeze` x3 |
| 384.6-400.8 | "Kiddo, it's me..." (G dummy) | winks `talk` |
| 401.9 | his jaw clacks shut, he smiles up at me | winks `clack(402.1)` (S4 starts at 401.93) |
| 415.0-420.4 | Mom grabs her keys; "We're leaving / Get your shoes" from the bookcase | mom `grab_keys(415.0)`; winks on the bookcase `sit_dummy(hands='limp')` + `torch_on(t, 0, 1, hold='chin')` + `talk` (U); light `dict(under='#fff1c8', under_a=210)` |
| 422.0 | you spin around | you `spin_around(422.0)` |
| 435-464 | the tape: young Walter and the dummy; it stops, turns to the camera and cries | walter74 `vent_pose` + `showman`; tape winks `puppet`, `head_snap(448.6, 0)`, `talk` (R 457.5-462.0); `draw_lap(..., light=TV)` |
| 523.4-543.6 | Owen in the armchair with the dummy on his knee | owen `vent_pose(side=1)` + `expr('kid_grin')` + `talk` (O); winks S5 + `puppet` + `talk` (G dummy) |
| 543.7-552.2 | Mom screams and pulls; Owen shrieks; "Pull, and his hand comes with me" | mom `pull_dummy(544.0, 549.0)` + `scream`; owen `cry` + `expr('scream')` |
| 552.3 / 555.0 | you catch Mom's wrist, kneel | you `catch_wrist(552.3)`, `kneel(555.1)` |
| 561.5-566.9 | he turns to Owen; click, a wink; "Goodnight, Owen." | winks `doll_turn(561.6, to, 1.2, 3)`, `wink(563.7)`, `talk` (G) |
| 567.1 | Owen's eyes close (both) | owen `lids(567.1)` or `set(..., lid_l=1, lid_r=1)`; from here his body is `owen_new` |
| 570-577 | slides his hand out, jumps up, hugs Mom: "It worked!" | owen_new `jump_hug(574.0)`; winks `fall_face_down(574.3)` returns `dummy_thud` |
| 598.2-603 | you pick him up; the P.S. slides out of his back | you `hold_dummy`; winks `carried` + `paper_out(600.0)` (back view shows the slot) |
| 655.5-664 | in your arms he opens his eyes; tries to wink; both lids close, click, click | `draw_carry`; winks arc `owen` (or `eyes_open(655.6)`), `try_wink(660.9, gap=0.45)` |
| 673.8 | the new Owen waves at the window | owen_new `wave(673.9, 677.3)` |
| 677.4-691 | behind glass in the museum: he tries to wink at you | winks stage `owen` + `try_wink` |
| 693.8 / 696.9-704.8 | coffee with two sugars; the doorway smile; "See you in the morning, kiddo." | owen_new `hold_mug(sip=[694.0])`, `doorway_smile(697.0, 5.0)`, `talk` (O, lips barely move) |

## Composites
- **`draw_lap(pen, who, x, y_feet, height, pose, dpose, side=1, m=...)`** draws three things in order: the person, Mister Winks on the knee top (`lap_anchor`, raised by `lift`), then, with `free_arm=True`, the other arm over him.
  - Give the person `vent_pose(side)`: the hand on the dummy's side goes into his back and he hides it.
  - Stage them front-on or turned a little toward the dummy (`turn` 0..+0.25 for side +1).
  - `between(pen)` draws a hospital blanket between the person and the dummy.
- **`draw_carry(pen, 'you', ..., pose, dpose)`** draws him cradled across your arms (`hold_dummy` on you, `carried` on him): his head rests in the crook of the arm behind him, and the other arm comes over his legs.
- **Perching:** `pose.perch` makes `y_feet` the surface a sitting figure sits on (chair seat, stair, bookcase, lap). The `sit_dummy` and `carried` clips set it.
- **`pose.recline`** tips the figure about its hips.
- **`pose.lie`** lays the figure on the floor: 1 is face down, -1 face up.
- **Busts:** `draw_bust` keeps a seated or kneeling face where the bust was asked for.

## Sound events the cast emits
Each event is a dict `{t, name, gain_db, pan, params, who}`. `film.py`'s `shot_common` picks up every `a.events` inside the shot. Suggested sources: the owner's new Epidemic packs, then the police and delivery libraries in `_work/samples/`.

| event | suggested sound |
|---|---|
| `dummy_clack` | Wooden dummy jaw clack. kind `snap` (0 dB) for deliberate ones; kind `speech` (-14..-8 dB) for one per syllable, which should be lighter and varied. |
| `dummy_jaw` | The hinge bottoming out as the jaw drops: a dull wooden knock. |
| `eyelid_click` | A small wooden click. kind `shut` / `open`. |
| `wood_creak` | Wooden joint creak. kind `tick` is short; kind `grind` is the 180° head turn (`params.dur`). |
| `flashlight_click` | Torch switch, kind `on` / `off`. |
| `dummy_thud` | The dummy falling face down on a rug. |
| `case_latch` | Brass case latch pop, x2. |
| `hand_squeeze` | A soft cloth and leather squeeze (the three squeezes, and Grandpa's in the memory). |
| `snort` | A kid's stifled snort-laugh. |
| `sip` | A sip of coffee. |
| `paper` (kind `slide`) | Paper sliding out of fabric. |

Reused names: `cloth_rustle` (kind `grab` / `glove` / `slot`), `breath` (sniff / gasp / sob), `keys_drop` (kind `jangle`), `footsteps_wood_inside`, `whoosh`.

## Sheets
The sheets are in `_work/cast/`. Regenerate them with `cd film && python3 tools/cast_sheets.py [name ...]`; it takes about 15 s for all of them.

| sheet | shows |
|---|---|
| `lineup` | The whole cast to scale. |
| `winks_turnaround` | Front, 3/4 left and right, profile, back (the slot), seated. |
| `winks_faces` | **Close-up** (the jaw hanging, the black hollow); **medium** (shut, dropped, wink, blink, torch under the chin, TV glow 3/4); **wide** (in Grandpa's chair with the torch up, standing on the chair). |
| `winks_arc` | S0-S5, TAPE, OWEN INSIDE. |
| `winks_acting`, `winks_acting2`, `winks_acting3` | Ratchet turn, 180° head turn, jaw drop and slow clack, glove lift, fingers and elbow, stand on chair, torch sweep, stairs glare, fall face down, bookcase with the torch under the chin while talking, eyes open and try_wink in your arms, the 1974 tape. |
| `family_faces`, `family_acting` (Mom), `family_acting2` (Owen), `family_acting3` (you, Grandpa) | Faces and frame strips of the family clips, with their sound events. |
| `laps` | Hospital, 1974, Owen in the armchair, in your arms, face down. |
| `props` | Flashlight (off / on / glare), mug, keys, the P.S. in his back. |

`python3 tools/cast_sheets.py sync` writes `jaw_sync_winks.mp4` and `lip_sync_owen.mp4` (4 s each, 960x540, 60 fps, with the voice), plus `sync_plot.jpg` and `sync.json`.

## Speed and tests
- **Speed** (2560x1440, one process): a full body takes 13-18 ms and a bust filling the frame 17-30 ms. `draw_lap` (Owen plus the dummy) takes 31 ms.
- **Self-test:** `python3 characters.py --selftest`. It covers the police and delivery checks plus:
  - jaw sync and clacks;
  - Owen's lip sync;
  - the arc;
  - jaw drop and clack, wink and try_wink;
  - the dummy's ticks;
  - every new id in 5 views, plus the composites.
