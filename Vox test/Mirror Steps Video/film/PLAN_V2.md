# PLAN_V2: the shot plan for "If The Queen Of Spades Appears In Your Mirror... DON'T MAKE A WISH"

The v2 plan turns DIRECTION_V2.md (the contract) into `plan/shots.json` and `plan/sound_plan.json`. It replaces PLAN.md's shot
list. PLAN.md, CAST.md and SETS.md stay the reference for v1 names that v2 keeps.

```
python3 plan/make_plan.py      # plan/shotlist.py -> plan/shots.json + plan/sound_plan.json
python3 plan/validate.py       # hard checks + the DIRECTION_V2 target table; exit 1 on any error or missed target
python3 plan/doc_v2.py         # rewrites the tables at the end of this file from the JSON
```

| file | role |
|---|---|
| `plan/shotlist.py` | the source table: 449 shots in film order, written with `X(t0, typ, world, 'set/view', var, frame, cam, **kw)`; prop STATEs; the rule-card builder `RULE(n)`; `PUNCHES`; the camera grammar (`PULL_OUTS`, the fast quartile); `V2_SFX` |
| `plan/dsl.py` | times from the timeline (`T(i)`, `Wc(i, word)`, `w`, `e`, `R`), `LEAD = 0.17`, the builders `C A fx M` and the v2 HUD builders (`chip teaser kinetic typebeat giant diagram doc count_pop stamp highlight mapins level_guide rings eye_line dials`), `X()` |
| `plan/make_plan.py` | resolves the table: ids, cut-on-clause, camera keys, props per shot, header clock, chips, side-switch glints, looks, v1 fallbacks, captions, the ring badge, the sound plan |
| `plan/validate.py` | the checks and the target table (section A1 below) |
| `plan/doc_v2.py` | the tables of section A |
| `plan/v1/` | v1's frozen plan (`shotlist_v1.py`, `shots_v1.json`, `sound_plan_v1.json`, ...): make_plan re-homes the v1 sound cues from it |

**Status: every target of DIRECTION_V2 5.1 / 5.5 / 2.2 / 1.2 that a plan can set is met (table A1).** The measures that only a
render can prove (luma, colourfulness, subject motion share, frame energy, edge density) are not in the plan; the plan carries the
intent per shot (`look`, `energy`, `cam`).

---------------------------------------------------------------------------------------------------------------------

## 1. How the plan follows the brief

- **Beat outline (1.4)**: every row became 1-4 shots cut on its clauses. Times are built from the aligned words, never typed:
  a clause cut is `word - 0.17 s` (65.6 % of cuts); the rest are action cuts (the snap, the drop, the hit, the 2-frame jerk).
- **Shot count and pace**: 449 shots, 38.4 cuts/min, 24 cuts in the first 30 s, rule 6 at 41.8/min, the ending at 35.5/min;
  median 1.52 s, p10 0.71 s, p90 2.24 s.
- **Holds (2.2)**: H1-H10 are the only shots over 2.5 s besides the seven cards and the time card (A3). Each pushes 3-5 %/s and
  carries the on-camera change as acting clips on the word (`split_open` at 479.24, `smile_off` at 533.68, `jaw_drop` at 589.60 ...).
- **Shot mix (5.1)**: wides 32.5 %, MS/OTS/2S 16.4 %, faces 26.6 %, inserts/docs/diagrams/UI 19.1 %, POV 5.5 %. Every rule card is
  followed by a wide (a reveal pull-out), and each of the 18 OURS/THEIRS scene switches has a wide in its first two shots.
- **The Queen's ladder (2.4, 3.3)**: every appearance has `queen = {stage, step, size, where, framing, wrong}` (A5). She is S0
  until 198.15, S1 to 283.6, S2 to 479.24, S3a, S3b at 499.56, S3c at 531.9, OFF at 533.68, S4 at 589.6. The stage never goes
  back except in the two "a second ago" callbacks (`past: true`) and the flash-forwards (`teaser`).
- **The four looks (1.2)**: `world` on every shot (ours, stairs, theirs, theirs_break, memory, climax, ending, ui, card, black)
  and `look` = the grade preset of section 4.8 (night_v2, stairs_v2, dawn_v2, dawn_queen_v2, dawn_break_v2, memory_sepia,
  climax_v2, ending_v2, phone_dark, rule_card, neutral). A chip on every shot (`chip.text`), drawn where `chip.pop` is true.
- **Diagrams, inserts, evidence (5.4)**: D1-D10, the documents and the noun inserts are explicit HUD entries with their content
  (A6). 63 shots carry a `device` (5.4 per minute).
- **Rule cards (5.3)**: unchanged times; the card HUD entry carries the whole choreography (towel whip, RULE written at t0 + 0.45,
  numeral stamp at t0 + 0.80, word-synced statement, the command in lipstick with an underline, the tape label, the progress
  staircase, her reflection size and pose per card, the glass state, LIKE/SUBSCRIBE with a cursor on cards 1-2, the exit smear).
- **The 33 errors (6)**: every number names its fixing shots in `errfix` and in `shots.json errors` (A7).

### Where the plan departs from the brief's letter (and why)

1. **Side-switch glints = 20** by one rule: a cut is a switch when the camera moves between Cabin 7 / the camp (looking into the
   glass counts as our side) and the other side's cabin; the stairs, memories, UI and type are neutral. Counting every cut into a
   stairs or through-glass shot gave 49, far over the brief's 18-22.
2. **Captions: 514, median 1.28 s, 75 % change within 0.2 s of a cut**, but 13 % have six words. With one-line captions (a caption
   never spans two narration lines) and 2,182 words, a five-word cap cannot go below 548 captions; 500-520 needs some six-word ones.
3. **Chip clocks follow the header clock** (real time from 23:57:00 at 19.40 s): the master wide reads `CABIN 7 · 11:57 PM` (the
   brief's table example says 11:59) and the D6 dial `12:02 AM` (brief 12:01), so chip and header never disagree.
4. **"4-6 inserts, documents, diagrams per minute"** is measured on the shots that carry a `device` (5.4/min); the insert *class*
   (inserts, docs, diagrams, UI, type, montage) is 19.1 % of shots (the 18-20 % target). Counting the class per minute gives 7.4.
5. **Giant numbers** 60/45/20/5/0 slam over Tess's calling CUs (type beat 4 as an overlay), not as separate shots; the 0 lands on
   the collar-grab insert.
6. **The face-up phone montage** (676.7 s) is one `MONTAGE` shot of 1.4 s with four 0.35 s tiles, so the red X and FACE UP hold
   across it.
7. **Small timing shifts**: H1 283.60-286.20; H3 478.03-481.13 (the split stays on "back" 479.24); H9 3.23 s (brief 3.4: the
   line timing); the 7 RULES slam on "seven" (122.87) and the RULE 4 circle on "fourth" (124.97) so they land with the v1 hits.
8. **Kid-Tess** (458.6 s) uses the cast's `kids` with `role: tess_kid` (there is no `tess_kid` rig); `mom` is hands only.

---------------------------------------------------------------------------------------------------------------------

## 2. shots.json (v2): every field

The file keeps every v1 key so film.py, sets.py and characters.py still load it; v2 adds keys and values.

### 2.1 Top level

| key | meaning |
|---|---|
| `meta` | title (the YouTube title), `version: 2`, fps 60, size 2560x1440, design 1920x1080, duration 700.0, narration_end, frames, `lead` 0.17, timeline, brief, fields (this file) |
| `sections[]` | name, t0, t1, title, shots, `cuts_per_min`, intensity range |
| `rule_cards[]` | v1 keys + `command`, `reflection` {size, pose, stage}, `glass` |
| `holds[]` | **new**: id H1-H10, `brief` [t0, t1, length], what, shot, t0, t1, dur |
| `queen_ladder[]` | **new**: one row per Queen appearance: shot, t0, stage, step, size, where, framing, wrong, on_screen |
| `devices[]` | **new**: shot, t0, type, kind (insert, doc, diagram, ui), id, what |
| `errors{}` | **new**: "1".."33" -> {error, shots[]} |
| `header` | v1 + `chips` (the chip rule) and the stairs clock rule |
| `counter` | v1 + `kind: ring` and the ring-badge look (the count is unchanged: 60 at 289.19 to 0 at 608.97, steps dilated to land on her calls) |
| `captions[]` | t0, t1, text, line, **`on_cut`** (true when it changes within 0.2 s of a cut) |
| `shots[]` | below |

### 2.2 A shot

v1 keys, unchanged in meaning: `id t0 t1 dur section lines cut_on_clause clause_offset set view var side type frame cam lens grade
dof chars props hud captions header counter tr intensity energy sfx mus voice_fx fx_post bg`.

| key | values | meaning (reader) |
|---|---|---|
| `type` | EWS WS SEC / MS OTS 2S / MCU CU ECU / INSERT DOC DIAGRAM SPLIT UI TYPE MONTAGE / POV / CARD BLACK | framing; `SEC` = the dollhouse section, `TYPE` = a full-frame type beat over a plate, `SPLIT` = two panels, `MONTAGE` = tiles (film.py) |
| `cls` | wide, mid, face, insert, pov, card, black | the class the shot mix is measured on (validate) |
| `world` | ours, stairs, theirs, theirs_break, memory, climax, ending, ui, card, black | the world whose look the shot has (sets, film) |
| `look` | night_v2, stairs_v2, dawn_v2, dawn_queen_v2, dawn_break_v2, memory_sepia, climax_v2, ending_v2, phone_dark, rule_card, neutral | the 4.8 grade preset; `grade` carries the same name (engine/post.py must define them; until then use `v1.grade`) |
| `side` | ours, mirror, **stairs**, theirs, memory, ui, card, black | v1 meaning; `mirror` = the glass seen from our side, whatever world is inside it; `stairs` is new (the header keeps the clock of the side the camera came from) |
| `family` | ours, theirs, null | where the camera physically is (the glint and chip rule) |
| `glint` | bool | the 3-frame glass glint plays on this cut (a side switch); 20 in the film. `tr` is `glint` unless another transition was written |
| `chip` | {text, style, pop} or null | the place/time chip of the shot; style ours (navy chip, blue dot), theirs (gold chip, amber dot), memory (red-brown stamp, -4 deg), loop, teaser; drawn 0.4 s in and held while `pop` is true. Teasers carry their own red chip in `hud` |
| `queen` | {stage, step, size, where, framing, wrong, on_screen} or null | the ladder entry (characters, film) |
| `hold` | H1..H10 | one of the ten holds |
| `setup` / `setup_reused` / `reuse` | name / bool / shot id | a named setup (C7_MASTER, THEIRS_MASTER, THEIRS_REVERSE, SECTION, PORCH_HIGH, QUEEN_BUNK, ...); whether this (set, view) was used before; `reuse` = the id of the earlier shot this one calls back ([R] in the brief) |
| `past` | true | an "a second ago" callback: the Queen shows an earlier stage on purpose |
| `errfix` | [n] | the section 6 errors this shot fixes |
| `device` | {kind, id, what} | the shot teaches a noun or a mechanism (insert, doc, diagram, ui) |
| `teaser` | 'RULE 2' ... | a flash-forward: red 6 px border, red chip, RGB split in, glitch out |
| `split` | {panels: [{set, view, var, world, label?, chip?, mark?, subject?, src_t?}, ...]} | a two-panel split (D4, D5, the loop twins, the bells); `set` is `split` |
| `plate` | {set, view, var, post {blur, dim}} | the blurred live plate under a TYPE / DIAGRAM shot (like a card's `bg`) |
| `montage` | [{t, src_t}] | the tiles of a MONTAGE shot: at t, show the framing of the shot at film time src_t |
| `loop` | A, B | the frame-identical loop animations: A the sprinkler (297.4, 414.3), B breakfast_A (318.4, 419.5) |
| `card` / `time_card` | n / true | the rule card number; the time card shot |
| `bokeh` | {palette, plate, discs} | every face shot sits on a bokeh plate in its world's palette (4.7); `dof` is set when missing |
| `v1` | {set, view, var, grade, bg?} | a view the v1 sets.py can render today (preview fallback until the v2 view exists; cards also get `bg`) |
| `cam` | v1 keys + `silence`, `snap_word` | `snap` = the punch-in [t, k, 0.1] (20 of them, on emphasis words); `roll` constant = a dutch angle (climax only); `move` pull/reveal = the pull-outs |
| `props` | the running state at t0 + `changes_in_shot` | see 2.4 |
| `chars[]` | v1 spec + `stage` (queen), `pov`, `sleeve`, `hand`, `fist`, `candy`, `tape`, `eyes`, `cuffs`, `seated`, `kneel`, `soft_focus`, `in_glass`, `through_glass`, `reflection`, `inside`, `tiny`, `role`, `age`, `face_hidden`, `light` | as named; `light` presets per world (L_OURS, L_BEAM, L_GOLD, L_STAIRS, L_RED, L_MEM, L_PHONE, L_END, L_QUEEN in shotlist.py) |

### 2.3 HUD entries (`hud[]`)

v1 types kept: `tag` (now `style: lipstick`, no pill box; 6 in the film), `red_x` (+ `n` 1-4), `label` (10), `time_card`, `phone`
(+ `fit`, `inset`, `scale`, `focus`), `rule_card` (+ the v2 choreography keys), `like_sub` (+ `cursor`, `clicks`).

| new type | keys | used for |
|---|---|---|
| `chip` | text, style, x, y, hold? | LOOP, ↺ AGAIN, 7:00 AM, 12:00 PM, the teaser RULE chips |
| `teaser` | chip, border_px, rgb_split, glitch_out | the five flash-forwards |
| `kinetic` | parts [{t, text, color, size_h, fx, underline?}], out {t, fx} | WIPE THE GLASS / CLEAN. (3.75 s) |
| `typebeat` | n, text, size_h?, echo?, red_word?, fade? | 1 the title, 2 the 14 YEARS stamp (and its echo), 3 7 RULES, 5 7:00 AM, 6 DON'T MAKE A WISH. |
| `giant_number` | value, size_h 0.38, hold, to_badge | type beat 4: 60, 45, 20, 5, 0 |
| `diagram` | id, content, hold?, build? | D1-D10 and the watch / loop-split diagrams: `content` says literally what is drawn |
| `doc` | kind, text, marks [{t, what, text}] | poster, notice, stencil, card, polaroid, photo, menu, sign: evidence with highlight / stamp / underline / chalk marks |
| `count_pop` | n, x, y, color, erase | D2 numerals 1-7 (count, the progress bar, the phone, the wipe ticking off) |
| `stamp` | text, x, y, color, rot, size_h, hit | 14 YEARS, CANCELED |
| `highlight` | text, box, color, dur | the highlighter on the poster line |
| `map` | hold, items [[label, x, y]], dot | D10 inset |
| `level_guide` | y, frame_rot, hold | the dashed level line at 146.6 |
| `sound_rings` | kind clean / rattle / broken, x, y, n, hold | D8 |
| `eye_line` | a, b, hold | D5 |
| `dials` | left, right {label, chip, rate}, hold | D6 |
| `circle` | text, x, y, color, draw | RULE 4 circled in lipstick |
| `balloon` | text, x, y, empty? | the memory speech balloons, NOAH! |

### 2.4 Props (`props`): the state at the shot's start, plus `changes_in_shot`

| key | timeline (s) |
|---|---|
| `steps_drawn`, `eighth`, `smeared`, `erased` | the lipstick steps 0-8: 7 drawn; the 8th draws at 2.56 (hook) and 118.87; smeared 1-7 by 139.6; erased 1-3 by 619.7, 7 by 620.8 |
| `mirror` | hook_glass, wrapped (19.3), glass (88.9), tilted (146.3), towel_over (251.75), doorway (256.87), glass returning (614.9), dark (628.18), covered (629) |
| `doorway` | none, gold (256.87), navy_dark when Tess runs (463.89), red (534.70), none (614.9) |
| `towel` | wrapped, floor_beside (88.9), tess_hands (249.67), over_glass (251.75), floor_flat (256.87), tess_hands (260.4), tess_shoulder (462.9), your_hands (617.8), draped_over_mirror (629) |
| `fist` / `candy` | none; candy_fist 323.65; trembling 645.0; opening 649.12; palm_candy 651.11 |
| `tape` | on; off_loop at 556.3 (no tape after 557.4) |
| `shoe` | left_on_lace_loose (the other shoe beside the bed) |
| `jacket` | you; noah at 635.06 |
| `flashlight` | off; tess_on 30.95; tess_running 462.9; tess_porch 500.03; tess_doorway 546.4; floor 614.9 |
| `padlock` | hasp_locked; hasp_open 71.9; tess_hand 462.9; struck 535.36; tess_hand 536.4 |
| `keys` / `gate_padlock` | tess_hand 30.95 / open 45.75 |
| `phone` (Tess's) | tess_pocket; sill_face_up 110.71; sill_face_up_red_glint 118.87; tess_hand 674.43; screen_steps 684.98; screen_eighth 690.19; screen_queen 691.86; screen_face 697.95 |
| `your_phone` | pocket; hand 44.4; pocket 192.0; call_mom 653.91; noah_hand 659.90 |
| `bell` | crate; porch_boards 510.4; struck 535.36 |
| `drop`, `clock`, `queen`, `noah`, `tess`, `you` | the hanging drop (337.09), the other side's clock 7:00 from 538.7, where the Queen is (glass_step8 ... phone), where each person is |

### 2.5 Transitions (`tr`)

`cut`, `glint` (side switch), `white` (white flash cut), `glitch`, `rewind` (loop reset: 4-frame tear + back-scrub 0.2 s), `sepia`
(into or out of a memory), `smear` (the card's finger-wipe exit carried 0.2 s over the next shot), `black`. In-shot flashes,
glitches, rewinds and the pixel-sort are `fx_post` entries (`white`, `glitch`, `rewind`, `pixel_sort`). The white flash / glitch
count is 2.91 per minute.

### 2.6 Camera grammar

The cams are written per shot; `camera_grammar()` at the end of shotlist.py then applies two documented rules: the 39 shots in
`PULL_OUTS` open tight and pull back (reveals; 8.9 % of shots with the 4 written ones), and inserts / docs / diagrams / UI / type /
POV push at least 5.5 %/s (6.5 %/s under 1 s), ECUs at least 5 %/s. Result: push median 3.0 %/s, p75 5.0 %/s; no static shot.
Silences push 1.5 %/s (`cam.silence`). Handheld on the runs (446-465 s, 500-546 s) and the climax; dutch 6-8 deg only in 560-628 s.
Camera hits at 143.29, 256.87, 535.36, 573.54, 605.21, 608.97, 614.9, 690.19. Whips on 198.15 and 594.2.

---------------------------------------------------------------------------------------------------------------------

## 3. sound_plan.json (v2)

- **The v1 cues stay at their film times** (the narration did not move) and are re-homed to the v2 shot that contains them. Removed:
  the old counter ticks and the old card cues (regenerated), and the cues of dropped picture (the DON'T WAIT, LISTEN, STAY and GO tag
  pops, the 7.52 eye-flash stinger, the 530.87 and 603.25 red-X stingers, the 125.48 lace pull). Re-timed where the picture moved
  (`SFX_MOVE` in make_plan.py: the car door slam 221.42 -> 220.40, the sit 466.52 -> 467.30, the fall 615.13 -> 614.90, the 7:00
  glitch 540.40 -> 538.70, ...). The identical-sample rules (nail click 143.29 = 690.19, the sprinkler and drip loops) keep their
  exact times, so audio/cues.py LOOP_LINKS still match.
- **New picture beats** (`V2_SFX` in shotlist.py): the hook foot, the teaser sounds, the padlock hung and yanked, the smile split,
  the red eyes, Tess's sprint, her foot on tread 8, the montage tile cuts, the tiny figure's step in the phone.
- **Device cues** generated from the HUD and the transitions: towel whip, glass thud, RULE written in lipstick, the numeral stamp
  (+3-5 LU), the statement and underline, the exit smear; giant-number thumps; ring ticks on every badge step; rubber stamps; the
  highlighter; chalk for diagrams; diagram and numeral pops; flash hits on white cuts; glitches; tape rewinds on loop resets;
  side-switch glints; the pixel-sort glitch. 13 new names, each with a `fallback` existing name + params until it is built (A10).
- **Music**: sections, intensity and all 124 events (23 silences, 9 risers, 44 swells, the stings) are v1's, re-homed; the music map
  in audio/cues.py is untouched.
- Cue ids are `<shot>:<name>:<k>` with the new shot ids, so an old `_work/align/film_events.json` does not apply to v2.

---------------------------------------------------------------------------------------------------------------------

## 4. Notes for the other builders

- **Sets (C)**: table A8 lists every (set, view) with its shot count, vars and first use. New sets: `stairs` (down, up, section,
  treads, ots_climb, pov_down, low, railing, queen_ecu, bokeh), `split`, `type`, `diagram`. New views on the v1 sets follow the 4.1
  and 4.4 angle lists (cabin_now master / reverse / profile / overhead / ots_mirror / three_q / floor_wide / dutch_low / doorway_down
  ...; cabin_dawn master / reverse / top_stairs / overhead / floor_prints / queen_3s / bunk_2s / dip_low / far_porch ...; mirror
  glass_cu / glass_wide / glass_tilt / through / queen_glass / reflection / towel_over). Vars: `night` (OURS), `doorway_glow`, `red`,
  `after`, `phone_glow`, `stairs`, `dawn`, `dawn_queen`, `dawn_break`, `sepia_day`, `sepia_night`, `sepia_morning`, `bell_hit`.
  Every face shot asks for a `bokeh` plate.
- **Cast (B)**: the Queen's stage comes from `chars[].stage` and `shots[].queen.stage` (S0, S1, S2, S3a, S3b, S3c, OFF, S4); her
  expressions are queen_still / queen_soft / queen_drawn / queen_grin / queen_grin_red / queen_full / queen_off / queen_void. The
  clips already aligned with characters.py: split_open, eyes_red, head_to_lens, sit_beside, jaw_drop, smile_off, head_snap, pat.
  Table A9 lists any clip the plan calls that characters.py does not define (none at the last generation: the cast pass already
  added lean_out, rise, climb_step, slide_rail, grin_widen, reach_shoulder, pixel_sort_in, reach_grab, hang_open, ...). Lip-sync lines: Queen 97, 110, 196 (`talk_line`); S4 line 249 as `talk` with
  `inner: noah13`; Noah13 68, 123, 125, 149, 152, 158, 169, 223, 299 (in the phone); grown Noah 282; Tess 137, 206, 246, 292; you 92, 188.
- **HUD (D)**: section 2.3; the rule-card entry carries the choreography keys; the counter is a ring badge.
- **Assembly (E)**: film.py's v1 id-keyed patches (`EXTRA_CHARS`, `PATCH_ACTS`, the S070 dress glint) point at v1 ids and now hit
  other shots: remove them. Grade names are the v2 presets (fallback `shot['v1']['grade']`). New: side `stairs`, `tr` values
  glint / rewind / sepia / smear, `fx_post` rewind / pixel_sort, `split`, `plate`, `montage`, `chip`, `bokeh`. Preview any shot
  today with `dict(shot, **shot['v1'])` (cards: `bg = shot['v1']['bg']`).
- **Sound (F)**: section 3 and A10; the counter cues are `ring_tick` (61) and the giant numbers `number_thump`.

## 5. What remains weak

- **Nothing here is rendered.** 96 of the plan's 139 (set, view) pairs are new (341 shots; none is in sets.py yet), and every new
  HUD type and transition is a contract for the other builders; the v1 fallback only gives a rough preview.
- The Queen's `size` is given for the ladder's key appearances; the other on-screen frames carry only the stage and the `at` spec.
- Clause-cut share sits at the bottom of the band (65.6 %): the short action and reaction cuts that bring p10 down to 0.71 s are
  mid-clause by nature.
- p10 is 0.71 s (brief 0.65) and the push p75 5.0 %/s (brief about 5.5): close, not exact.
- Device sound cues are dense (586 cues, 50/min against v1's 34): most are -16 to -20 dB ticks and pops, but the sound pass should
  thin the ring ticks and diagram pops if the quiet stretches lose their LRA.
- Character `at` coordinates are first guesses in design space; the assembly will need to re-seat bodies on the new perspective
  rooms (feet on the floor lines of each view).

---------------------------------------------------------------------------------------------------------------------

## A. Tables (generated)

<!-- AUTO:BEGIN -->
<!-- generated by plan/doc_v2.py from plan/shots.json; do not edit by hand -->

### A1. The target table (`python3 plan/validate.py`)

```
shots                                                  449   430-450       PASS  
cuts per minute                                       38.4   36.0-40.0     PASS  
cuts per minute, rule 6 (542-610 s)                   41.8   40.0-44.0     PASS  
cuts per minute, ending (629-700 s)                   35.5   34.0-38.0     PASS  brief: 34-36
cuts in the first 30 s                                  24   22-24         PASS  
shot length p10 (s)                                   0.71   0.55-0.85     PASS  brief 0.65
shot length p50 (s)                                   1.52   1.40-1.60     PASS  brief 1.5
shot length p90 (s)                                   2.24   2.20-2.60     PASS  brief 2.5
shots over 3 s (%)                                     3.1   <= 4.0        PASS  holds, cards, time card only
cuts on a clause start (%)                            65.6   65.0-75.0     PASS  
picture lead on clause cuts, median (s)               0.17   0.12-0.20     PASS  brief 0.15-0.17
wides (%)                                             32.5   30.0-35.0     PASS  
MS / OTS / 2S (%)                                     16.4   15.0-20.0     PASS  
faces (%)                                             26.6   25.0-30.0     PASS  
inserts, documents, diagrams, UI (%)                  19.1   18.0-20.0     PASS  
POV hands (%)                                          5.5   4.0-6.0       PASS  brief 5
inserts / documents / diagrams per minute             5.40   4.00-6.00     PASS  shots carrying a device
setups reused: explicit [R] callbacks (%)              8.9   >= 8.0        PASS  plus same-angle wides/mids below
setups reused: wide/mid on an earlier angle (%)       30.7   >= 25.0       PASS  brief about 30
push-in median (%/s)                                  3.00   2.60-3.60     PASS  brief about 3.0
push-in p75 (%/s)                                     5.00   4.00-6.00     PASS  brief about 5.5
pull-outs (% of shots)                                 8.9   7.0-13.0      PASS  brief about 10
near-static shots (%)                                  0.0   <= 5.0        PASS  
white flash / glitch cuts per minute                  2.91   2.00-3.00     PASS  
punch-ins per minute                                  1.97   1.00-2.00     PASS  
side-switch glints                                      20   18-22         PASS  
re-establishing wide after each rule card                7   7-7           PASS  of 7
wide in the first 2 shots after a side switch           18   18-18         PASS  of 18 blocks
holds (the only shots over 2.5 s)                       10   10-10         PASS  
red X                                                    4   4-4           PASS  
command tags                                             6   6-6           PASS  
labels with leader lines                                10   >= 8          PASS  
captions                                               514   500-520       PASS  
caption length median (s)                             1.28   1.10-1.30     PASS  brief 1.2
caption words p10                                        2   >= 2          PASS  p90 6; six-word captions 13 % (the 500-520 count needs some)
caption words max                                        6   <= 6          PASS  
captions changing within 0.2 s of a cut (%)           75.1   >= 70.0       PASS  
errors 1-33 mapped to shots                             33   33-33         PASS  
lines covered                                          300   300-300       PASS  
CU/ECU on a bokeh plate (%)                            100   >= 90         PASS  shots[].bokeh
     device cues: ring_tick 61, diagram_pop 48, flash_hit 21, glint_whoosh 20, lipstick_draw 19, glitch 15, glass_wipe 14, ui_pop 13, chalk_draw 12, number_thump 7, glass_resonance 7, towel_whip 7, glass_thud 7, lipstick_stamp 7, tape_rewind 6, rubber_stamp 3, highlighter_squeak 2, pixel_glitch 2
```

OK: every target met

### A2. Shot table summary by section

Class counts are wide / MS-OTS-2S / faces / inserts-docs-diagrams-UI / POV.

| section | t (s) | what | shots | cuts/min | classes | median s | holds | ids |
|---|---|---|---|---|---|---|---|---|
| hook | 0.00-19.26 | Cold open: the premise, the flash-forwards | 20 | 62.3 | 9/0/3/7/1 | 0.73 | - | S001-S020 |
| arrival | 19.26-54.46 | 11:57 PM, the camp, Tess, Mom's text | 22 | 37.5 | 7/4/5/6/0 | 1.42 | - | S021-S042 |
| porch | 54.46-67.59 | The mess hall porch and the cracked bell | 9 | 41.1 | 4/0/1/4/0 | 1.36 | - | S043-S051 |
| cabin | 67.59-88.70 | The caretaker's house, Cabin 7, the towel | 14 | 39.8 | 6/3/2/3/0 | 1.60 | - | S052-S065 |
| steps | 88.70-121.10 | Seven steps, the game, the eighth step | 21 | 38.9 | 9/2/5/5/0 | 1.52 | - | S066-S086 |
| seven | 121.10-129.80 | There are seven rules | 5 | 34.5 | 2/0/0/3/0 | 1.62 | - | S087-S091 |
| rule1 | 129.80-203.53 | Rule 1: count the steps | 48 | 39.1 | 16/6/12/9/4 | 1.60 | - | S092-S139 |
| rule2 | 203.53-269.24 | Rule 2: keep your wishes to yourself | 43 | 39.3 | 10/13/12/5/2 | 1.59 | - | S140-S182 |
| rule3 | 269.24-350.38 | Rule 3: leave somebody on your side | 51 | 37.7 | 15/9/15/9/2 | 1.76 | H1 | S183-S233 |
| rule4 | 350.38-446.33 | Rule 4: ask what he wished for | 60 | 37.5 | 22/8/20/8/1 | 1.56 | - | S234-S293 |
| rule5 | 446.33-542.03 | Rule 5: ring the real bell | 57 | 35.7 | 21/8/16/9/2 | 1.60 | H2, H3, H4 | S294-S350 |
| rule6 | 542.03-609.48 | Rule 6: let him go first | 47 | 41.8 | 12/12/13/6/3 | 1.36 | H5, H6, H7 | S351-S397 |
| rule7 | 609.48-629.05 | Rule 7: cover anything that reflects | 10 | 30.7 | 4/1/0/1/2 | 1.52 | H8 | S398-S407 |
| ending | 629.05-700.00 | Just after midnight: Hi, Mom; the phone | 42 | 35.5 | 6/6/13/9/7 | 1.48 | H9, H10 | S408-S449 |

### A3. The ten holds (the only shots over 2.5 s besides the cards and the time card)

| hold | shot | plan t | s | brief | what changes on camera |
|---|---|---|---|---|---|
| H1 | S190 | 283.60-286.20 | 2.60 | 283.5-286.1 (2.6) | she leans into the light; the drawn smile; the lips talk |
| H2 | S306 | 464.59-468.35 | 3.76 | 464.7-468.4 (3.7) | she sits; the mattress dips |
| H3 | S312 | 478.03-481.13 | 3.10 | 478.0-481.1 (3.1) | the drawing splits into teeth on "back" |
| H4 | S344 | 531.58-534.68 | 3.10 | 531.6-534.7 (3.1) | the full face turns to the lens, then the smile goes off |
| H5 | S366 | 562.41-565.13 | 2.72 | 562.5-565.2 (2.7) | the age morph |
| H6 | S386 | 589.48-591.58 | 2.10 | 589.5-591.6 (2.1) | the jaw drops into the void, with Noah's face inside |
| H7 | S395 | 604.48-607.36 | 2.88 | 604.6-607.4 (2.8) | the POV tilt from your boots to her foot to her face |
| H8 | S404 | 621.92-625.53 | 3.61 | 622.0-625.6 (3.6) | she lifts her foot toward an erased step |
| H9 | S428 | 661.64-664.87 | 3.23 | 661.6-665.0 (3.4) | the long pause on "Hi, Mom" |
| H10 | S446 | 691.86-695.62 | 3.76 | 692.0-695.7 (3.7) | her tiny figure on the phone's 8th line, climbing one step |

### A4. Rule cards (times unchanged) and the re-establishing wide after each

| n | shot | t | command (lipstick red) | her reflection | glass | the wide after it |
|---|---|---|---|---|---|---|
| 1 | S092 | 129.80-133.56 | COUNT THE STEPS | 9 % tiny figure on the bottom step | clean silver | re-establishing wide: you kneel at the mirror, Tess beside you with th |
| 2 | S140 | 203.53-208.32 | KEEP YOUR WISHES TO YOURSELF | 16 % head turned toward the lens | clean silver | re-establishing wide [R C7 master]: you kneel at the mirror; Tess behi |
| 3 | S183 | 269.24-273.35 | LEAVE SOMEBODY | 25 % standing in gold doorway light | gold reflection | re-establishing wide: you go to the gold doorway; Tess behind you |
| 4 | S234 | 350.38-353.53 | WHAT HE WISHED FOR | 30 % seated, hands in her lap | gold reflection | re-establishing side wide: you take Noah's hand and lead him to the fo |
| 5 | S294 | 446.33-449.74 | REAL | 45 % the S2 drawn smile | a hairline crack | re-establishing wide [R reverse], low angle up the stairs: you shout u |
| 6 | S351 | 542.03-545.22 | FIRST | 65 % red eyes | three cracks, 30 % red tint | THE SECTION [R]: you push Noah up the red steps toward the doorway; ta |
| 7 | S398 | 609.48-614.71 | COVER | 90 % the S3c face filling the glass | graded red, steps glowing | OURS, red: you slam onto the floorboards (dust, camera hit at 614.9);  |

### A5. The Queen ladder: every appearance with stage, step and size

Stage S0..S4 and OFF are the brief's 3.3 stages; step is the tread she stands on in mirror shots (8 = the bottom); size is her height (or face height for CUs) as a fraction of the frame height. Teasers (0-12.7 s) are flash-forwards.

| shot | t0 | stage | step | size | where | framing | new wrong thing |
|---|---|---|---|---|---|---|---|
| S001 | 0.00 | S3c | - | 120 % | glass (flash-forward of 605 s) | ECU | (teaser) |
| S005 | 3.28 | S0 | - | 15 % | glass, on the eighth line | foot 15 % | somebody is there |
| S008 | 6.05 | S0 | - | 18 % | glass, three steps down | figure 18 % | she is coming |
| S009 | 6.62 | S0 | - | 18 % | the stairs | figure 18 % (low angle) |  |
| S010 | 7.36 | S0 | - | - |  | WS |  |
| S013 | 10.55 | S1 | - | - |  | INSERT |  |
| S015 | 11.88 | S3c | - | - |  | WS |  |
| S092 | 129.80 | S0 | - | 9 % | reflection behind the card words | card 1 | tiny figure on the bottom step |
| S104 | 148.23 | S0 | 8 | 25 % | glass, step 8 | WS 25 % | stands level in a tilted world |
| S105 | 150.63 | S0 | - | - |  | MS |  |
| S106 | 152.31 | S0 | 8 | 45 % | glass, step 8 | CU of the bowed head |  |
| S107 | 153.75 | S0 | - | - |  | INSERT |  |
| S108 | 154.39 | S0 | - | - |  | OTS |  |
| S134 | 197.50 | S0 | - | - |  | MS |  |
| S135 | 198.15 | S1 | 8 | 45 % | glass, step 8 | MS | head turns 130 deg, the hair does not follow |
| S136 | 198.55 | S1 | 8 | 45 % | glass, step 8 | CU face 45 % | looks into the lens (1 of 3) |
| S137 | 199.26 | S0 | - | - |  | CU |  |
| S138 | 200.46 | S0 | - | - |  | WS |  |
| S139 | 202.29 | S1 | 8 | 100 % | glass | ECU of the eye | no blink |
| S140 | 203.53 | S1 | - | 16 % | reflection behind the card words | card 2 | head turned toward the lens |
| S144 | 211.49 | S1 | 7 | 32 % | glass, step 7 | WS 32 % | she climbs while nobody watches |
| S145 | 213.09 | S1 | - | - |  | MS |  |
| S154 | 228.00 | S1 | 7 | 32 % | glass, step 7 | WS |  |
| S155 | 229.92 | S1 | 6 | 40 % | glass, step 6 | background, 40 % | closer again |
| S157 | 234.12 | S1 | 5 | 45 % | glass, step 5 | MS | she climbs while nobody watches |
| S161 | 238.96 | S1 | 4 | 100 % | glass, step 4 | ECU of the eyes | she heard it |
| S167 | 245.26 | S1 | 3 | 25 % | glass, step 3 | behind your reflection | rising |
| S168 | 246.99 | S1 | 2 | 35 % | glass, step 2 | face behind your reflection 35 % | right behind you |
| S169 | 248.22 | S1 | 1 | 70 % | glass, the top | CU face 70 % | she speaks |
| S173 | 253.66 | S1 | - | - | through the towel | fingers to the lens | red bleeds through the cloth |
| S183 | 269.24 | S1 | - | 25 % | reflection behind the card words | card 3 | standing in gold doorway light |
| S190 | 283.60 | S2 | - | 55 % | the doorway at the mirror spot | CU face 55 % | the drawn stair-smile; pinpoint pupils |
| S234 | 350.38 | S2 | - | 30 % | reflection behind the card words | card 4 | seated, hands in her lap |
| S255 | 382.16 | S2 | - | 30 % | on the bunk beside Noah | WS 30 % | she was here all along |
| S256 | 384.32 | S2 | - | - |  | MS |  |
| S259 | 389.84 | S2 | - | 20 % | the window corner, background | soft focus 20 % | she watches |
| S261 | 392.72 | S2 | - | 18 % | the window corner, background | soft focus |  |
| S283 | 429.04 | S2 | - | 15 % | the window corner, background | soft focus 15 % | threat in the background |
| S294 | 446.33 | S2 | - | 45 % | reflection behind the card words | card 5 | the S2 drawn smile |
| S306 | 464.59 | S2 | - | 35 % | rises from the corner, sits on the bunk | WS 35 % | the inhuman sit |
| S307 | 468.35 | S2 | - | - |  | MS |  |
| S310 | 473.55 | S2 | - | 50 % | on the bunk | CU 50 % |  |
| S311 | 475.63 | S2 | - | - |  | INSERT |  |
| S312 | 478.03 | S3a | - | 70 % | on the bunk | CU 70 % | the drawing opens into teeth |
| S314 | 483.31 | S3a | - | 30 % | on the bunk | WS |  |
| S316 | 487.87 | S3a | - | 30 % | on the bunk | WS | the grin of teeth, patting the dip |
| S319 | 492.99 | S3a | - | - |  | WS |  |
| S322 | 496.67 | S3a | - | 40 % | over your shoulder | OTS 40 % |  |
| S323 | 498.19 | S3b | - | 40 % | over your shoulder | OTS 40 % | red irises |
| S326 | 503.15 | S3b | - | 30 % | on the bunk | WS |  |
| S344 | 531.58 | S3c | - | 80 % | on the bunk | CU to ECU 80 % | the full face; then the smile goes off |
| S349 | 539.19 | OFF | - | 30 % | on the bunk | WS | the smile is gone; the loop is broken |
| S351 | 542.03 | S3b | - | 65 % | reflection behind the card words | card 6 | red eyes |
| S375 | 576.25 | S3c | - | 30 % | by the bunk, behind you | WS 30 % | calling |
| S376 | 577.29 | S3c | - | 65 % | by the bunk | CU 65 % | calling |
| S385 | 587.88 | S3c | 8 | 30 % | the foot of the stairs | low WS | she follows |
| S386 | 589.48 | S4 | - | 75 % | the foot of the stairs | low CU 75 % | the jaw void with Noah's voice |
| S387 | 591.58 | S4 | - | - |  | ECU |  |
| S393 | 601.32 | S3c | 3 | 10 % | two steps below you (section) | section | she follows |
| S395 | 604.48 | S3c | below yours | 100 % | the step below yours | POV, 100 % | 30 cm away |
| S398 | 609.48 | S3c | - | 90 % | reflection behind the card words | card 7 | the S3c face filling the glass |
| S404 | 621.92 | S3c | - | 35 % | through the streak, the lower steps | WS 35 % | the foot finds no step |
| S405 | 625.53 | S3c | - | - |  | INSERT |  |
| S446 | 691.86 | S3c | 8 | 3 % | in the phone | 3 % | starting again |
| S448 | 696.74 | S3c | - | 60 % | the phone | 60 % | looks into the lens (3 of 3) |

### A6. Inserts, documents and diagrams (the per-minute device count)

| shot | t0 | type | kind | id | what it teaches | HUD entries |
|---|---|---|---|---|---|---|
| S002 | 0.42 | INSERT | insert | lipstick | lipstick steps drawn on a mirror (it reflects: the hand, the hot spot) | - |
| S003 | 1.90 | WS | diagram | D2 | count the steps: 1-7 pop beside the drawn steps | count_pop |
| S004 | 2.56 | WS | insert | 8th | the eighth line appears by itself | - |
| S016 | 12.79 | DOC | doc | poster | the MISSING poster: Noah, 13 | doc |
| S019 | 17.58 | INSERT | diagram | D7 | the loop clock 6:59:59 -> :40 | diagram |
| S021 | 19.26 | EWS | doc | time_card | FRIDAY 11:57 PM · CAMP CEDAR LAKE · DEMOLITION TOMORROW | - |
| S023 | 24.94 | DOC | doc | notice | the demolition notice: Cabins 5-7, Saturday 7:00 AM | doc |
| S025 | 28.70 | MS | insert | cabin7 | Cabin 7 is this one: plaque, padlock on the hasp | - |
| S027 | 31.75 | INSERT | insert | keys | Tess has the keys: the CABIN 7 tag | - |
| S030 | 35.34 | DOC | doc | poster_line | LAST SEEN WEARING A GREEN SWEATSHIRT (highlighted) | highlight |
| S038 | 46.14 | UI | ui | texts | Mom's texts | phone |
| S041 | 50.78 | INSERT | insert | candy | red cinnamon candies in red twist wrappers | - |
| S045 | 57.18 | DOC | doc | crate | the crate: SAVE FOR THE MUSEUM | doc |
| S047 | 60.62 | INSERT | insert | bell | the old breakfast bell | - |
| S049 | 62.87 | INSERT | insert | crack | the crack in the rim | - |
| S051 | 66.15 | DIAGRAM | diagram | D8 | the cracked bell rings twice: clean, then a rattle | diagram, sound_rings |
| S054 | 71.51 | MS | insert | padlock | the padlock on Cabin 7's hasp | - |
| S056 | 73.43 | INSERT | insert | cubby | the NOAH cubby is empty: no sweatshirt | - |
| S058 | 75.91 | INSERT | insert | towel | Noah's towel (label NOAH) | - |
| S065 | 86.46 | INSERT | insert | watch | the alarm changed: 6:45 -> 4:45 | diagram |
| S070 | 95.26 | DOC | doc | card | the Queen of Spades playing card (plants the crown, collar, beauty mar | doc |
| S072 | 98.20 | DIAGRAM | diagram | D1 | the game: she climbs from the bottom to WISH at the top | diagram |
| S079 | 109.82 | INSERT | insert | phone | the phone face up on the sill (a mirror too) | - |
| S085 | 118.70 | INSERT | insert | 8th | a fresh red line appears beneath the bottom step | - |
| S094 | 134.32 | POV | diagram | D2 | counting: a numeral pops beside each smeared step | count_pop |
| S098 | 140.55 | INSERT | insert | fingertip | seven red marks on your finger | - |
| S101 | 143.60 | DIAGRAM | diagram | D3 | the eighth step is behind the glass | diagram |
| S110 | 157.75 | WS | insert | swimsuits | damp swimsuits on the rail | - |
| S112 | 161.03 | WS | insert | wash_door | someone came in from the wash house | - |
| S119 | 172.39 | INSERT | insert | one_shoe | one shoe, then a bare foot: ONE SHOE | - |
| S122 | 176.63 | SPLIT | diagram | D4 | two times: their floor has prints, ours is untouched | diagram |
| S127 | 186.30 | UI | doc | voicemail | the 14-year-old voicemail from Noah | phone |
| S139 | 202.29 | SPLIT | diagram | D5 | she is now listening to YOU: the eye line | diagram, eye_line |
| S146 | 214.85 | INSERT | insert | tape | three fingers taped with blue medical tape | - |
| S150 | 221.57 | DOC | doc | polaroid | the tape polaroid | doc |
| S179 | 263.92 | POV | insert | stairs | the doorway leads down a staircase | - |
| S188 | 280.72 | INSERT | insert | clock_back | our clock jerks backward | - |
| S194 | 290.06 | SEC | diagram | section | the crossing is a place: blue cabin, stairs, gold cabin | - |
| S197 | 293.10 | WS | insert | lantern | the battery lantern | - |
| S199 | 295.66 | INSERT | insert | lantern | the battery lantern; almost light outside | - |
| S211 | 315.94 | DOC | doc | dad_photo | you look like Dad | doc |
| S218 | 324.44 | INSERT | insert | fist | the candy in your fist (it stays there to 649 s) | - |
| S225 | 336.76 | INSERT | insert | drop | a drop hangs in the air (time is stuck) | - |
| S229 | 342.82 | SEC | diagram | D6 | our time crawls, their time loops | diagram, dials |
| S241 | 362.50 | INSERT | insert | same_knot | the same knot, half tied: SAME KNOT | - |
| S252 | 376.80 | WS | insert | wish | Noah made the wish at 4:45 AM (his alarm woke him) | - |
| S257 | 386.64 | INSERT | diagram | D7 | the loop clock | diagram |
| S267 | 401.02 | WS | insert | towel_wet | the wet towel on the floor that morning | - |
| S280 | 422.32 | SPLIT | diagram | loop_split | the same moment twice | diagram |
| S288 | 437.89 | DOC | doc | menu | Breakfast was canceled | doc, stamp |
| S293 | 445.17 | WS | insert | crate_bell | the bell went into the crate | - |
| S295 | 449.74 | WS | diagram | D10 | the map: Cabin 7 -> the path -> the mess hall crate | map |
| S332 | 513.39 | INSERT | insert | fake_bell | a perfect bell rings by itself (the fake) | sound_rings |
| S338 | 523.42 | DIAGRAM | diagram | D8 | the real bell: a clean note, then a rattle | diagram, sound_rings |
| S341 | 527.58 | INSERT | insert | spoon | like somebody dropped a spoon | - |
| S343 | 530.46 | SPLIT | diagram | D8_split | the fake bell vs the real bell | diagram, sound_rings |
| S348 | 538.15 | INSERT | diagram | D9 | the loop breaks: 7:00 AM | diagram, typebeat |
| S414 | 638.89 | INSERT | insert | clock_1207 | just after midnight: 12:07 | - |
| S421 | 651.11 | POV | insert | candy_palm | the candy, kept | - |
| S424 | 655.19 | WS | ui | call | the call to Mom | phone |
| S437 | 677.34 | MONTAGE | doc | face_up | the phone lay face up the whole time (a mirror nobody covered) | - |
| S442 | 684.98 | INSERT | diagram | D2_phone | seven tiny steps on the phone screen | count_pop |
| S445 | 689.38 | POV | insert | eighth_phone | the eighth line on the phone | - |

### A7. Error-to-shot map (DIRECTION_V2 section 6: 1-27 from the critique, 28-33 new)

| # | v1 error | fixed by (shot, t0) | how (first fixing shot) |
|---|---|---|---|
| 1 | she never sits | S306 (464.6), S307 (468.4) | HOLD H2: she rises from the window corner (where she has stood since 389 s) and in one smo |
| 2 | Noah and the Queen vanish from the 488 wide | S316 (487.9) | WIDE: Noah tying the knot, the Queen beside him patting the dip, the beautiful gold room;  |
| 3 | open palm for "in your fist" | S217 (323.2), S218 (324.4), S328 (505.8) | POV: your olive cuff takes the candy; your LEFT hand closes into a fist at 323.65 |
| 4 | a mark but no candy | S421 (651.1), S422 (652.4) | the red candy lies in the open palm |
| 5 | the tape vanishes, then is back on | S360 (554.3), S361 (555.9), S364 (559.5) | ECU: the fingers lengthen inside the blue tape |
| 6 | no shoulder hit | S373 (573.4) | the top rail slams his shoulder (573.5): dust burst, the frame jumps, camera hit |
| 7 | a waist grab, no yank | S357 (551.3), S396 (607.4), S397 (609.0) | MS at the doorway from our side: Tess's orange arm, foreshortened toward the lens, grabs h |
| 8 | no bell on screen; the X on a window | S332 (513.4), S343 (530.5) | telephoto: a GLEAMING bell swinging by itself on the far porch, clean white rings |
| 9 | the real bell is never struck | S345 (534.7), S346 (535.4) | OURS porch: Tess winds up with the padlock (534.96) |
| 10 | the beam stays after Tess leaves | S305 (463.9) | THEIRS: the doorway at the top goes DARK NAVY, no beam; the empty corner by the window |
| 11 | no opening in frame for the shove | S352 (545.2), S355 (547.4) | THE SECTION [R]: you push Noah up the red steps toward the doorway; tag HIM FIRST |
| 12 | whose voice and face at 589 | S386 (589.5), S387 (591.6) | HOLD H6: her jaw drops; the face below the eyes stretches 1.35x into a tall glossy void; N |
| 13 | no keys | S027 (31.8) | the key ring swings into CU: padlock keys, the carabiner and a CABIN 7 key tag |
| 14 | the tape design changes | S002 (0.4), S146 (214.8), S360 (554.3) | a taped kid hand (green CEDAR LAKE cuff, the one blue tape design: middle, ring and little |
| 15 | no 8th line on the phone | S445 (689.4) | silence: your fingertip finds a clean red line under the glass (the eighth); CLICK at 690. |
| 16 | the phone jumps from hand to floor | S435 (674.3), S436 (676.4), S437 (677.3), S441 (683.9) | Tess picks up her phone from the windowsill |
| 17 | fist, open, fist, open | S418 (644.8), S419 (646.6), S420 (649.0) | POV: your left fist trembles and will not open |
| 18 | already grown, no morph | S366 (562.4) | HOLD H5: the face morphs from 13 to 27 on camera: the jaw lengthens, stubble fades in, bro |
| 19 | the face turns into a paper card | S190 (283.6), S344 (531.6) | HOLD H1: she leans out of the doorway, half in blue, half in gold. The lipstick smile is d |
| 20 | her mouth frozen while she talks | S169 (248.2), S190 (283.6), S312 (478.0) | CU in the glass: "You have it." lip-sync, a thin red glow on the mouth while she speaks |
| 21 | Noah too big, then standing | S205 (305.9) | wide on the bunk: Noah at correct seated kid scale, feet on the floor, white sneaker on hi |
| 22 | a white half-disc glitch at 255 | S173 (253.7), S175 (256.9) | five long fingertips push the cloth toward the lens, lipstick red bleeding through the ter |
| 23 | the clipped text bubble | S038 (46.1) | your phone: MOM thread, bubble "Check the pocket." (text-fit checked) |
| 24 | the finger hides the watch digits | S065 (86.5) | the watch LCD fills 70 % of the frame; the finger presses the button BESIDE the digits (ne |
| 25 | the phone steps appear late | S442 (685.0) | the phone (in Tess's hand) fills the frame: 7 tiny lipstick steps, already there; numerals |
| 26 | the face in the wrong world at 283.5 | S190 (283.6) | HOLD H1: she leans out of the doorway, half in blue, half in gold. The lipstick smile is d |
| 27 | the dawn cabin behind you on the stairs | S375 (576.2), S385 (587.9), S394 (602.5), S395 (604.5) | THEIRS (dawn_break) behind you (OTS): she stands by the bunk calling his name, S3c face, m |
| 28 | "Instead" has no picture | S056 (73.4) | the NOAH cubby, empty: masking-tape label NOAH, a cobweb, no sweatshirt (you looked; it is |
| 29 | grown Noah's yellow eyes | S366 (562.4), S377 (578.7) | HOLD H5: the face morphs from 13 to 27 on camera: the jaw lengthens, stubble fades in, bro |
| 30 | "Breakfast was canceled" over a bare wall | S288 (437.9) | the menu chalkboard JULY 19 · BREAKFAST 7:00 · PANCAKES with CANCELED chalked across and a |
| 31 | the other side's doorway at floor level, no stairs | S018 (16.1), S109 (156.0), S145 (213.1), S196 (291.3) | THEIRS master wide: Cabin 7 flipped and golden, frozen; the stairs rise along the back wal |
| 32 | the padlock never planted | S025 (28.7), S054 (71.5), S303 (462.6) | Cabin 7 (nearest the path): the number plaque, the door with its padlock on the hasp, old  |
| 33 | the mirror never reads as a mirror | S002 (0.4), S003 (1.9), S066 (88.7), S067 (90.3) | a taped kid hand (green CEDAR LAKE cuff, the one blue tape design: middle, ring and little |

### A8. Set / view vocabulary (what sets.py must build) with the v1 fallback

shots[].v1 = {set, view, var, grade} names a view the v1 sets.py renders today, so film.py can preview every shot before the v2 view lands (`build_shot(dict(shot, **shot["v1"]))`).

| set/view | shots | vars | types | v1 fallback | first use |
|---|---|---|---|---|---|
| black/black | 2 | black | BLACK | black/black | pure black for 0.5 s |
| cabin_dawn/bokeh | 36 | dawn, dawn_break | CU, MCU | cabin_dawn/noah_cu | CU of Noah13 looking up with the gap-tooth smile (almond eye |
| cabin_dawn/bunk_2s | 9 | dawn | MS, WS | cabin_dawn/noah_ms | wide on the bunk: Noah at correct seated kid scale, feet on  |
| cabin_dawn/clock | 4 | dawn, dawn_break | INSERT | cabin_dawn/clock | D7 the loop clock: 6:59:59 snaps back to 6:59:40 with the re |
| cabin_dawn/dip_low | 2 | dawn_queen | INSERT, WS | cabin_dawn/mattress_dip | low wide along the mattress: her black satin settles into th |
| cabin_dawn/door_wash | 1 | dawn | WS | cabin_dawn/wide | the wash-house door swings in: wet morning light on the boar |
| cabin_dawn/far_porch | 1 | dawn | INSERT | cabin_dawn/window_out | telephoto: a GLEAMING bell swinging by itself on the far por |
| cabin_dawn/floor_prints | 4 | dawn | INSERT, WS | mirror/old_cabin_floor | low wide across the floor at the wash-house door: water spre |
| cabin_dawn/hands | 3 | dawn | INSERT, POV | cabin_dawn/candy | POV: your olive cuff takes the candy; your LEFT hand closes  |
| cabin_dawn/hands_jerk | 1 | dawn | POV | cabin_dawn/hands_jerk | POV: his hand snaps out of yours in 2 frames; your empty han |
| cabin_dawn/knot | 3 | dawn | INSERT | cabin_dawn/knot_cu | knot insert: the lace half tied |
| cabin_dawn/lantern | 1 | dawn | INSERT | cabin_dawn/window | the lantern glowing on the sill; through the glass a peach s |
| cabin_dawn/master | 9 | dawn, dawn_break | INSERT, MS, WS | cabin_dawn/wide | THEIRS master wide: Cabin 7 flipped and golden, frozen; the  |
| cabin_dawn/ots_noah | 3 | dawn | MCU, OTS | cabin_dawn/noah_cu | reverse OTS past Noah to you: you stand in the gold room, un |
| cabin_dawn/overhead | 3 | dawn | WS | mirror/old_cabin_floor | high angle on the floor: two sets of wet footprints appear o |
| cabin_dawn/queen_3s | 14 | dawn_break, dawn_queen | 2S, CU, MS, OTS, WS | cabin_dawn/queen_bunk | wide [R 305.9]: SHE IS SITTING ON THE BUNK BESIDE NOAH, S2,  |
| cabin_dawn/reverse | 6 | dawn | MS, WS | cabin_dawn/doorway_back | REVERSE [setup] from the bunk up the stairs: Tess in the doo |
| cabin_dawn/shoe | 1 | dawn | INSERT | cabin_dawn/shoe | his feet: one white sneaker, one bare foot; label ONE SHOE |
| cabin_dawn/swimsuits | 1 | dawn | WS | cabin_dawn/wide | a row of damp swimsuits (teal, coral, violet, lemon) over th |
| cabin_dawn/top_stairs | 2 | dawn | WS | cabin_dawn/wide | THEIRS from the top of the stairs: the gold, mirror-flipped  |
| cabin_dawn/towel_floor | 5 | dawn | INSERT, WS | cabin_dawn/towel | floor-level across the towel under the window: drips tap ont |
| cabin_dawn/window | 3 | dawn | WS | cabin_dawn/window | the window wall: the old battery lantern glowing on the sill |
| cabin_dawn/window_out | 3 | dawn | WS | cabin_dawn/window_out | LOOP A: through the window: the sprinkler comes on, spits tw |
| cabin_now/bokeh | 30 | after, doorway_glow, night, phone_glow, red | CU, ECU | cabin_now/two_shot | CU of you (olive jacket, stubble) leaning in, wet eyes, the  |
| cabin_now/bunk_rail | 2 | red | MS | cabin_now/bunk_hit | MS: he rises |
| cabin_now/clock | 2 | after, doorway_glow | INSERT | cabin_now/clock | clock insert: the second hand jerks back three ticks with th |
| cabin_now/cubby | 1 | night | INSERT | cabin_now/wide | the NOAH cubby, empty: masking-tape label NOAH, a cobweb, no |
| cabin_now/door | 2 | night | INSERT, MS | cabin_now/cabin_door | Cabin 7's door: Tess unhooks the padlock and hangs it open o |
| cabin_now/doorway | 10 | doorway_glow, red | 2S, CU, MS | cabin_now/doorway | MS of the doorway: the white chipped frame around a raw spli |
| cabin_now/doorway_down | 1 | doorway_glow | POV | cabin_now/doorway | POV down through the doorway: eight red-edged steps descendi |
| cabin_now/dutch_low | 3 | red | WS | cabin_now/wide | wide: grown Noah hunched under the bunk he could walk under |
| cabin_now/floor_cu | 3 | night, red | INSERT, WS | cabin_now/floor_low | low: the towel lying flat, dust settling, the empty frame ab |
| cabin_now/floor_wide | 8 | after, phone_glow | 2S, MS, WS | cabin_now/floor_end | ENDING wide: grown Noah sitting on the floor at adult scale  |
| cabin_now/hands | 11 | after, night, red | INSERT, POV | cabin_now/hands | FLASH-FORWARD TONIGHT: big adult forearms in green CEDAR LAK |
| cabin_now/master | 12 | doorway_glow, night, phone_glow, red | MS, WS | cabin_now/wide | CABIN 7 MASTER WIDE (high, from the door): left bunk, wall c |
| cabin_now/ots_mirror | 6 | night | 2S, MS | cabin_now/mirror_ots | you and Tess react: you lean back, Tess's hand to her mouth; |
| cabin_now/overhead | 1 | night | WS | cabin_now/floor_end | overhead wide of Cabin 7: the beam pool slides over our dust |
| cabin_now/phone_screen | 9 | phone_glow | CU, INSERT, POV | cabin_now/phone_screen | insert: the orange sleeve wipes the dust off the black glass |
| cabin_now/profile | 4 | night | WS | cabin_now/mirror_ots | profile along the back wall: you pull the towel off; the mir |
| cabin_now/reverse | 4 | doorway_glow, night | POV, WS | cabin_now/wide | OUR FLOOR (reverse wide toward the door): the smooth dust fi |
| cabin_now/sill | 4 | night, phone_glow | INSERT, MONTAGE, MS | cabin_now/sill | insert: Tess sets her phone FACE UP on the windowsill; its b |
| cabin_now/three_q | 3 | night | 2S, WS | cabin_now/two_shot | three-quarter from the left bunk: Tess raises the flashlight |
| cabin_now/towel_label | 1 | night | INSERT | cabin_now/towel_label | the striped towel's laundry label in marker: NOAH |
| cabin_now/towel_over | 1 | night | INSERT | cabin_now/towel_over | FLASH-FORWARD (253 s): five long fingertips press through th |
| cabin_now/under_bunk | 1 | night | WS | cabin_now/under_bunk | floor-level under Noah's bunk, slats overhead: a towel-wrapp |
| camp_gate/aerial | 1 | night | EWS | camp_path/aerial | the camp aerial relit blue-violet: the lake with the moon, C |
| camp_gate/bokeh | 5 | night | CU | camp_gate/wide | CU of you looking at the poster photo of Noah in the green s |
| camp_gate/fence_track | 1 | night | OTS | camp_path/path_track | OTS following Tess along the fence toward the gate, her beam |
| camp_gate/gate_reverse | 1 | night | WS | camp_gate/wide | reverse wide from inside the gate: the two of you reach the  |
| camp_gate/keys_cu | 1 | night | INSERT | camp_gate/keys_cu | the key ring swings into CU: padlock keys, the carabiner and |
| camp_gate/notice | 1 | night | DOC | camp_gate/notice | NOTICE OF DEMOLITION zip-tied to the fence: CABINS 5-7 · SAT |
| camp_gate/poster | 2 | night | DOC | camp_gate/poster | MISSING poster on the gate board: NOAH, 13, gap-tooth school |
| camp_gate/poster_ecu | 1 | night | DOC | camp_gate/poster | ECU of the poster line LAST SEEN WEARING A GREEN SWEATSHIRT; |
| camp_gate/wide | 5 | night | 2S, MS, WS | camp_gate/wide | the gate wide (v1 set, relit): you and Tess small by the car |
| camp_path/bokeh | 1 | night | CU | camp_path/path | CU of Tess, finger to her lips |
| camp_path/cabin7_door | 1 | night | MS | camp_path/cabins_row | Cabin 7 (nearest the path): the number plaque, the door with |
| camp_path/cabins_row | 1 | night | WS | camp_path/cabins_row | low wide: three dark cabins in a row with orange spray-paint |
| camp_path/path_run | 2 | night | WS | camp_path/path_track | Tess runs out the door with the beam into the night; Cabin 7 |
| caretaker/wide | 1 | night | WS | caretaker/wide | the caretaker's house: warm window #ffb84d with TV flicker,  |
| diagram/side_view | 1 | night | DIAGRAM | mirror/mirror_cu | D3 side view: the glass plane edge-on, the seven drawn steps |
| memory/bell_ecu | 2 | sepia_day | DIAGRAM | memory/bell_ecu | D8 planted: the bell rings on the boards; a clean white ring |
| memory/bell_ring_porch | 3 | sepia_day | CU, MS, WS | memory/bell_ring_porch | memory: the counselor rings it on the porch |
| memory/bench | 2 | sepia_day | CU, MS | memory/bench | memory: Noah on the bench by the lake picking at the tape, k |
| memory/breakfast_table | 3 | sepia_day | CU, WS | memory/breakfast_table | memory CU: Noah at the breakfast table stuffing pancakes |
| memory/bunk_morning | 2 | sepia_morning | CU, WS | memory/cabin_morning | memory: Noah wrings the towel over kid-you's pillow in the b |
| memory/bunk_night | 2 | sepia_night | MS, WS | memory/bunk_night | memory, night: Noah asleep in the top bunk, his arm with the |
| memory/bus_run | 1 | sepia_morning | WS | memory/path_run | memory (his plan): Noah in pajamas sprinting toward a yellow |
| memory/bus_window | 1 | sepia_day | CU | memory/buses | kid-you's face in a bus window looking back at the cabins |
| memory/buses | 1 | sepia_day | WS | memory/buses | yellow buses in a line; kids' faces in the windows; chip 12: |
| memory/car_20 | 1 | sepia_day | CU | memory/kitchen | memory flash: CU of you at 20 in a car saying it |
| memory/car_door | 1 | sepia_day | WS | memory/polaroid | memory: the family car; the door slams on a small hand; kid  |
| memory/card_queen | 1 | sepia_night | DOC | memory/card_queen | a vintage Queen of Spades playing card: the court-card queen |
| memory/crate_bell | 1 | sepia_day | WS | memory/storage_shed | memory wide on the porch: the counselor lowers the bell into |
| memory/dad_photo | 1 | sepia_day | DOC | memory/polaroid | a sepia family photo: Dad with your square jaw and stubble |
| memory/director | 1 | sepia_morning | MS | memory/kitchen_staff | memory: the director with a clipboard on the mess-hall porch |
| memory/dock | 1 | sepia_day | WS | memory/dock | memory: Noah13 on the lake dock in the green CEDAR LAKE swea |
| memory/flash_445 | 1 | sepia_night | WS | memory/lipstick_game | THE KEY MEMORY: Noah13 alone at this mirror at 4:45 AM in pa |
| memory/gate_close | 2 | sepia_day | DOC, WS | memory/gate_close | the gate chained [R the gate, sepia] |
| memory/kids_game | 4 | sepia_night | CU, WS | memory/kids_game | memory: kids in sleeping bags dare each other, flashlights u |
| memory/kids_mouths | 1 | sepia_night | CU | memory/kids_game | CU: three kids' faces in a row by lantern whisper her name o |
| memory/kitchen_15 | 1 | sepia_day | CU | memory/kitchen | memory flash: CU of you at 15 at the kitchen table saying it |
| memory/kitchen_staff | 1 | sepia_morning | WS | memory/kitchen_staff | the director waves cooks in white aprons out of the kitchen |
| memory/lantern_game | 1 | sepia_night | WS | memory/lipstick_game | memory, night by lantern in Cabin 7: kids in sleeping bags w |
| memory/legs | 2 | sepia_morning | WS | memory/porch_steps | kid-you among adult legs on the porch |
| memory/menu_board | 1 | sepia_morning | DOC | memory/kitchen | the menu chalkboard JULY 19 · BREAKFAST 7:00 · PANCAKES with |
| memory/moms_car | 2 | sepia_day | CU, WS | memory/gate_close | memory: Mom's car at the gate, a waving arm from the window  |
| memory/night_window | 6 | sepia_night | CU, MS, WS | memory/night_window | memory, the night he vanished: Cabin 7's window from outside |
| memory/office_phone | 1 | sepia_day | CU | memory/kitchen | memory CU: Noah at the camp office payphone, laughing into t |
| memory/officer | 1 | sepia_morning | MS | memory/porch_steps | an officer with a notebook bends to listen |
| memory/open_window | 3 | sepia_day | CU, WS | memory/night_window | memory: water through the open window onto the bottom bunk |
| memory/percolator | 1 | sepia_morning | INSERT | memory/kitchen | memory-morning insert: a percolator bubbling on the camp sto |
| memory/pocket | 1 | sepia_day | INSERT | memory/pocket | memory insert: the green sweatshirt's kangaroo pocket, a kid |
| memory/polaroid | 1 | sepia_day | DOC | memory/polaroid | the polaroid: Noah by the family car holding up the taped fi |
| memory/porch_drop | 1 | sepia_day | WS | memory/porch_steps | memory: a counselor drops the bell on the porch steps; kid-y |
| memory/red_candy | 3 | sepia_day | CU, MS | memory/pocket | memory: Noah gives kid-you the red one |
| memory/run_barefoot | 1 | sepia_day | WS | memory/path_run | memory: kid-you and kid-Tess running barefoot across the pat |
| memory/search_pines | 2 | sepia_morning | WS | memory/search_pines | flashlights in the pines, mist |
| memory/search_window | 1 | sepia_morning | WS | memory/search_pines | through the window: counselors with flashlights in the mist; |
| memory/socks | 1 | sepia_morning | MS | memory/cabin_morning | memory: kid-you on that spot pulling socks on |
| memory/spoon | 1 | sepia_day | INSERT | memory/breakfast_table | insert: the spoon drops on the table and bounces (the simile |
| memory/sprinkler_lawn | 2 | sepia_day | MS, WS | memory/sprinkler_lawn | memory: the lawn sprinkler arcs; Noah runs through it holdin |
| memory/tape_wrap | 1 | sepia_day | WS | memory/polaroid | memory wide, the family kitchen: Mom (her face out of frame) |
| memory/towel_wet | 1 | sepia_morning | WS | memory/cabin_morning | memory wide: the cabin floor between the bunks: the same str |
| memory/wake | 2 | sepia_morning | CU, WS | memory/cabin_morning | memory-morning CU: kid-you wakes in the bottom bunk and squi |
| memory/watch_cu | 2 | sepia_night | INSERT | memory/watch_cu | the watch LCD fills 70 % of the frame; the finger presses th |
| mess_porch/bell_ecu | 2 | night | INSERT | mess_porch/bell_ecu | the old brass breakfast bell in the crate, lit by the beam |
| mess_porch/bell_hit | 1 | bell_hit | INSERT | mess_porch/bell_ecu | CONTACT at 535.36: padlock on the rim, spark, 2-frame white  |
| mess_porch/bokeh | 2 | night | CU | mess_porch/porch_run | CU of you recognising the old breakfast bell, a brass glint  |
| mess_porch/boot | 1 | night | WS | mess_porch/boot_ecu | low wide on the porch boards: her boot smashes the slats (50 |
| mess_porch/crate_cu | 1 | night | DOC | mess_porch/crate_cu | insert: the stencil SAVE FOR THE MUSEUM on the slats and a p |
| mess_porch/high_wide | 2 | night | WS | mess_porch/wide | HIGH WIDE from the mess-hall porch: the porch in the foregro |
| mess_porch/porch_crate | 6 | bell_hit, night | WS | mess_porch/porch_run | FLASH-FORWARD (535 s): on the dark porch Tess swings the pad |
| mess_porch/porch_low | 1 | night | WS | mess_porch/porch_low | low angle on the boards: Tess's boot steps over the crate |
| mirror/glass_cu | 15 | night, red | CU, DIAGRAM, INSERT, OTS, POV | mirror/mirror_cu | a taped kid hand (green CEDAR LAKE cuff, the one blue tape d |
| mirror/glass_tilt | 1 | night | WS | mirror/queen_step_tilt | the whole mirror, frame and drawing tilted at -13 deg; the e |
| mirror/glass_wide | 8 | night, red | POV, WS | cabin_now/mirror_ots | the whole mirror leaning on the back wall of Cabin 7, white  |
| mirror/queen_glass | 13 | stairs | CU, ECU, INSERT, MS, WS | mirror/queen_step_tilt | she stands on the eighth line inside the glass, back three-q |
| mirror/reflection | 2 | night | OTS | cabin_now/mirror_ots | OTS on your reflection in the glass; behind its shoulder som |
| mirror/through | 8 | dawn, red, stairs | CU, ECU, INSERT, OTS, WS | mirror/old_cabin_refl | through a gap in the smear: a tall figure three steps down t |
| mirror/towel_over | 3 | night | INSERT, MS | cabin_now/towel_over | the draped towel, still; Tess backing away |
| rule_mirror/card | 7 | dawn, dawn_break, dawn_queen, doorway_glow, night, red | CARD | rule_mirror/card | the rule card is the mirror: towel whips off, RULE in lipsti |
| split/bells | 1 | dawn | SPLIT | cabin_dawn/window_out | split: THEIR BELL (smooth rings, red X mark) / OUR BELL (rin |
| split/eyes | 1 | stairs | SPLIT | mirror/queen_step_tilt | D5 eye line: her unblinking eye (left) beside your eye (righ |
| split/floors | 1 | night | SPLIT | mirror/old_cabin_floor | D4 split: THEIR FLOOR (wet prints, chip 6:59 AM · 14 YEARS A |
| split/twins | 1 | dawn | SPLIT | cabin_dawn/noah_cu | split: the two identical CUs side by side, both chipped 6:59 |
| stairs/bokeh | 4 | red, stairs | CU, ECU | mirror_world/stairs | CU of Tess in the doorway at the top, calling down "Forty-fi |
| stairs/down | 3 | stairs | WS | mirror_world/stairs | from the top of the stairs looking down: eight red-edged tre |
| stairs/low | 4 | red, stairs | CU, ECU, WS | mirror_world/stairs | low angle up the plum stairs: her silhouette climbing, the s |
| stairs/ots_climb | 4 | red, stairs | MS, OTS | mirror_world/stairs | OTS on the stairs: our blue cabin above, gold below; you go  |
| stairs/pov_down | 2 | red | POV | mirror_world/feet | POV from the stairs down into the red-lit gold cabin: the sh |
| stairs/queen_ecu | 1 | red | ECU | mirror_world/eye | FLASH-FORWARD (605 s): the Queen at S3c inside the glass, fa |
| stairs/railing | 4 | stairs | INSERT, MS, WS | mirror_world/railing | the stairs from the side along the railing: she climbs, the  |
| stairs/section | 5 | red, stairs | SEC | mirror_world/stairs | THE SECTION [setup]: Cabin 7 upper left in blue night, the w |
| stairs/treads | 2 | stairs | INSERT, POV | mirror_world/feet | inside the glass: a pale bare foot with black toenails sets  |
| stairs/up | 4 | red | INSERT, POV, WS | cabin_dawn/doorway_back | Tess at the top of the stairs in the doorway (from the stair |
| type/beat | 1 | night | TYPE | mirror/mirror_cu | type beat 3: 7 RULES slams over the glowing steps |
| type/kinetic | 1 | night | TYPE | mirror/mirror_cu | KINETIC TITLE over the darkened, blurred mirror: WIPE THE GL |
| ui/call | 1 | phone | UI | ui/call | Mom's live waveform: "Did you find the sweatshirt?" |
| ui/text | 2 | phone | UI | ui/text | your phone: MOM thread, bubble "Check the pocket." (text-fit |
| ui/voicemail | 1 | phone | UI | ui/voicemail | your phone: VOICEMAIL list, NOAH · 0:09 · JUL 18 |

### A9. Acting clips the plan calls that characters.py does not define yet

characters.py ignores an unknown clip (no crash, no motion). 138 clips are used in all; these 0 need a method (or a rename in the shot list):

| clip | who |
|---|---|

### A10. Sound plan summary

586 cues (50.2 per minute): 297 carried from v1 at their film times, re-homed to the v2 shots (103 v1 cues left out: the old counter ticks and card cues, regenerated as device cues, and SFX_DROP; SFX_MOVE re-timed 17), 18 new picture beats (shotlist.py V2_SFX), 271 device cues. 83 hit events (7.1 per minute), 23 silences, 44 swells, 9 risers (music events unchanged from v1, re-homed). New names for the v2 devices (each with a fallback existing name until it is built):

| name | cues | what | fallback |
|---|---|---|---|
| chalk_draw | 12 | chalk lines drawn on glass for the diagrams (soft scratch) | lipstick_draw {'clean': True} |
| diagram_pop | 48 | a diagram element or count numeral popping in (tiny chalk tick / pop) | ui_pop  |
| flash_hit | 21 | a white flash cut: short bright air hit (no low end) | whoosh {'kind': 'hard'} |
| glass_thud | 7 | the mirror card settling: a small glass-and-wood thud | mirror_handle {'kind': 'bump'} |
| glint_whoosh | 20 | the 3-frame glass glint on a side switch: a tiny bright glass whoosh | whoosh {'kind': 'soft'} |
| highlighter_squeak | 2 | a highlighter swiped across paper | paper  |
| lipstick_stamp | 7 | the rule numeral stamping into the glass in lipstick: soft waxy impact with crum | lipstick_draw {'strokes': 1} |
| number_thump | 7 | a giant number / type beat slamming in: low punchy thump with a short ring tail | impact_hit {'size': 0.6} |
| pixel_glitch | 2 | the pixel-sort glitch (589.6, 697.95): digital crunch | glitch {'dur': 0.3, 'amount': 0.9} |
| ring_tick | 61 | Tess's ring-timer badge ticking one step (kind call: the bigger tick when she ca | countdown_tick  |
| rubber_stamp | 3 | a rubber stamp slammed on paper (14 YEARS, CANCELED) | impact_hit {'size': 0.4} |
| tape_rewind | 6 | the loop reset: a 0.2 s tape rewind scrub | drop_reverse  |
| towel_whip | 7 | the orange-striped towel whipped up off the rule card (cloth whip, 0.3 s) | towel_cloth {'kind': 'snatch'} |

Device cues by name: ring_tick 61, diagram_pop 48, flash_hit 21, glint_whoosh 20, lipstick_draw 19, glitch 15, glass_wipe 14, ui_pop 13, chalk_draw 12, number_thump 7, glass_resonance 7, towel_whip 7, glass_thud 7, lipstick_stamp 7, tape_rewind 6, rubber_stamp 3, highlighter_squeak 2, pixel_glitch 2.

<!-- AUTO:END -->
