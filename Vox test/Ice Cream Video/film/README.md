# "If The Ice Cream Truck Plays Its Song In Winter... DON'T GO OUTSIDE": film

Night Policy's rule-format horror film, built like the bus, Doctor, Bunnyman, dummy and police films: the same 2.5D
engine, the cast and set systems, the shot-list format (`film_bunny_ref.py`, `film_police_ref.py`, `film_dummy_ref.py`
kept as references; the bus shot list read-only at `W/film_bus_old.py`), the police header, rule cards (Mr. Kessler's
paper taped inside our front door, signed W.K.; rule 8 in Adam's hand), captions, the global look with a climax ramp,
and cue sheets derived from the picture. The picture follows `W/shotmap.md` (every line of the timeline -> the picture
that carries it, plus the continuity table: truck A/B, power, curtains, frost, the cone, the radio, mittens, the boot,
Lina's state, his form, porch lights, Kessler's chimney). The villain is MISTER SHIVER (original: `CAST.md`, the story bible).

All commands run from this folder (`Vox test/Ice Cream Video/film`). The work dir is `W = film/_work`.

| file | what |
|---|---|
| `film.py` | The shot list. `plan_film()`: part A (`plan_open .. plan_rule4`, L0-262: the cold open, Larkfield, Dad and the radio, Kessler and 1958, rule 1 and the curtains, the truck and glimpse 1, the comment prompt, rule 2 and the cone, the blackout and glimpse 2 in the TV, rule 3 and the fake Dad, glimpse 3, rule 4: the walk out, the yank, the frozen boot, THE TRANSFORMATION, the chase, the mitten, the fingertips) and `plan_partb()` (L263-427: rule 5, Mom at the door, the face up the glass; rule 6, the attic, the hatch, the bathroom, the leg under the door; the truck moves to Kessler's; the twist; rule 7; the crossing under one blanket, the cage, the huddle; the hung note, the plow, the porch lights, the shrink back; Bye Benny; the morning and cocoa; across town; rule 8; the outro). Builders `B_set`, `B_bust`, `B_ins`, `B_rule`, `B_pause` (the comment prompt), `B_endB` (the outro cards: Said INSIDE? -> who on your street is inside alone; LIKE = a door knocked three times; SUBSCRIBE = a blanket round the house; the snowman next-time card), `B_card`, `B_black`. Every time is keyed to `W/align/timeline.json` (`T(i)`, `W(i, word)`, `WD`, `E`): no absolute times. |
| `characters.py` + `characters_ice.py` / `CAST.md` | The cast (Mister Shiver in both forms with the transformation and 8 legs, Adam, Lina, Dad, Mr. Kessler, 1958 Walter and Benny, his Mom copy, the medics) and the acting. |
| `sets.py` + `sets_ice.py` / `SETS.md` | Birch Lane (our house, Kessler's, the truck at A / B, the plow), the house inside (living, hall + hatch, kitchen, bathroom), 1958, the morning, across town, the inserts (rules, cards, radio, mittens, boot, fingers, towel, doorknob, outro advice). |
| `render.py` | Stills, test clips and the full worker/slice render. |
| `tools/validate.py` | The staging validator (feet heights in the house / the snow / on porches, overlaps, reach, props, cut continuity, this film's states: truck A/B, power, curtains, Adam's sock, the hatch, the towels, the chimney, porch lights, his breath; shot lengths, camera moves, lips). 0 ERROR is the bar. |
| `tools/final_chain.sh`, `tools/encode_chain.sh` (+ `enc_seg.sh`), `tools/deliver.sh` | The final render in chunks + the HEVC deliverable `W/deliver/If_The_Ice_Cream_Truck_Plays_In_Winter_EN_1440p60_HEVC.mp4` (title "If The Ice Cream Truck Plays Its Song In Winter... DON'T GO OUTSIDE"), capped CRF 20. |
| `audio/` | The sound step (reads `W/cues/*.json`). |

## Inputs
- `W/align/timeline.json` (lines L0..L427, word times in `W/align/asr_cache.json`), `W/align/vo_en.wav` (the edited
  narration with the character voices). Read at run time: a re-paced voice edit needs no change in `film.py`.
- `W/shotmap.md`: the picture contract, line by line. Handoffs: `W/handoff/film_a.md`, requests to cast / sets in
  `W/handoff/requests.md` (film never edits `characters_ice.py` / `sets_ice.py`).

## Commands
```
python3 film.py --list                                         # every shot (+ median, cuts/min)
python3 film.py --sheet _work/tests/filmB/sb --range 233 386   # review sheets: first | mid | last + lines (shot indices)
python3 film.py --lipcheck                                     # mouths move only on their own lines
python3 film.py --still 500.5,640.0                            # stills -> W/tests/film/still_T.jpg
python3 film.py --cues                                         # W/cues/sfx_cues.json, music_cues.json, shots.json
python3 tools/validate.py [--part A|B] [--fps 4]               # 0 ERROR is the bar
python3 render.py --size 640x360 --fps 30 --workers 2 --out _work/preview_tmp --audio _work/align/vo_en.wav   # preview
python3 render.py --workers 2 --from_ 498 --to 503 --out _work/tests/render5 --audio _work/align/vo_en.wav   # 5 s full-mode test
P=2 bash tools/final_chain.sh > _work/logs/final_chain.log 2>&1   # FINAL 2560x1440 / 60 fps in chunks, then deliver.sh
PICTURE_ONLY=1 P=2 bash tools/final_chain.sh ...; P=2 bash tools/encode_chain.sh   # or: picture, then resumable HEVC segments
```
- `render.py` writes `film.mp4` into `--out`; the preview lives at `W/preview/preview.mp4` (640x360, 30 fps, narration).
- Full mode: contiguous slices per worker, libx264 crf 16, `.done` markers. Delete markers and slices before
  re-rendering a changed film into the same `--out`.
- The final render needs the final mix `W/mix/final/mix_en.wav` for `deliver.sh` / `encode_chain.sh`. Run two chunks at
  a time on the shared 4-core machine, as a harness-tracked background task (never nohup).

## Cue sheets: the sound step's contract
`python3 film.py --cues` writes `W/cues/sfx_cues.json` (`{t, name, gain_db, pan, space, params}`: every action of the
picture, from the shots' explicit cue lists and the cast's acting events), `music_cues.json` (`{duration, intensity,
events}`) and `shots.json` (the cut list).
- SFX names (part B adds): `door_pound`, `glass_squeak`, `frost_creep`, `attic_click`, `attic_scuttle`, `hatch_rattle`,
  `hatch_drop`, `leg_pry`, `footsteps_run`, `door_slam`, `towel_stuff`, `leg_slide`, `towel_jam`, `leg_withdraw`,
  `frost_wipe`, `truck_glide`, `door_creak`, `slipper_shuffle`, `snow_step(s)`, `shovel_scrape`, `tape_press`,
  `radio_grab`, `radio_static`, `plow_pass`, `plow_roar`, `plow_horn`, `coat_rustle`, `blanket_wrap`, `leg_stab`,
  `leg_hook`, `cloth_tear`, `leg_stab_snow`, `porch_light_click`, `door_open_far`, `skin_stretch`, `mitten_drop`,
  `ambulance_far`, `pencil_write`, `knock_door` (the LIKE card), plus the cast's own events (`leg_click`, `legs_fold`,
  `sh_jaw_close`, the transformation stages).
- Music: HIS CHIME as `type 'jingle'` with a `version` (burst, three, far, closer, outside, lullaby, warped, bells, and in
  part B: warped at the door and in the attic, outside as it moves to Kessler's, warped through the crossing, `climax`
  L372-L385 (it hangs on the missing note and falls apart), warm for the morning, far across town (ending on the gap),
  warm under the outro), plus `hit`, `riser`, `rule` and `silence` events, and the tension curve (`intensity`).
