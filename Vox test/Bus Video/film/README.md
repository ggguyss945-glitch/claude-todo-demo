# "If The School Bus Stops At Midnight... DON'T GET ON": film

Night Policy's rule-format horror film, built like the police, dummy, Bunnyman and Doctor films: the same 2.5D engine,
the cast and set systems, the shot-list format (`film_bunny_ref.py`, `film_police_ref.py`, `film_dummy_ref.py` are kept
as references; the Doctor shot list is kept read-only at `W/film_doctor_old.py`), the police header, rule cards and
captions, the global look with a climax ramp, and cue sheets derived from the picture. The picture follows
`W/shotmap.md` (every line of the timeline -> the picture that carries it, the props' continuity, the story clock).
The villain is MISTER WHISTLESTOP (original character: see `CAST.md` and the story bible).

All commands run from this folder (`Vox test/Bus Video/film`). The work dir is `W = film/_work`.

| file | what |
|---|---|
| `film.py` | The shot list. `plan_film()`: part A (cold open, the 1994 tape, the family and the post, the rules paper, rule 1 and midnight, the loudspeaker, the comment prompt as his 1994 broadcast, rules 2-4) and `plan_partb()` (rule 5: the deadbolt, the hallway, the capture and the blinks; rule 6: bus 9, 911, 1994, the chase; rule 7: the last stop, the climax, the bell and his defeat; after: Theo home, the clipboard, the morning, the new girl, the sting, rule 8; the outro). Builders `B_set`, `B_bust`, `B_ins`, `B_flat` (the 1994 tape), `B_rule` (the rules paper inside the front door, rule 8 in Mina's hand), `B_pause` (the comment prompt), `B_outro` (the crossed-out 1994 tape, every trick is real, bus 9's route with one piece of advice per stop, "Said yes?" callback, LIKE = bus 9 stopping at your door, SUBSCRIBE = its stop arm, next time: the ice cream truck in winter, the NIGHT POLICY end card), `B_card`, `B_black`. Every time is keyed to `W/align/timeline.json` (`T(i)`, `W(i, word)`, `WD`, `E`): no absolute times. |
| `characters.py` + `characters_bus.py` / `CAST.md` | The cast (Mister Whistlestop, Mina, Sami, Grandma Della, Theo, the new girl, the 1994 kids) and the acting. |
| `sets.py` + `sets_bus.py` / `SETS.md` | The house on Larch Street (inside, the yard, the street), his bus and bus 9 (one interior plan), the night road, Larkfield Elementary, Theo's stop, the 1994 tape and classroom, the inserts. |
| `render.py` | Stills, test clips and the full worker/slice render. |
| `tools/validate.py` | The staging validator (anchors, feet / floors / stairs, overlaps, reach, props, cut continuity, this film's prop and light states, shot lengths, camera moves, lips). 0 ERROR is the bar. |
| `tools/final_chain.sh`, `tools/encode_chain.sh` (+ `enc_seg.sh`), `tools/deliver.sh` | The final render in chunks + the HEVC deliverable `W/deliver/If_The_School_Bus_Stops_At_Midnight_EN_1440p60_HEVC.mp4` (title "If The School Bus Stops At Midnight... DON'T GET ON"), capped CRF 20 like the Doctor film. |
| `audio/` | The sound step (reads `W/cues/*.json`). |

## Inputs
- `W/align/timeline.json` (lines L0..L418, word times in `W/align/asr_cache.json`), `W/align/vo_en.wav` (the edited
  narration with the character voices). Read at run time: a re-paced voice edit needs no change in `film.py`.
- `W/shotmap.md`: the picture contract, line by line.

## Commands
```
python3 film.py --list                                      # every shot (+ median, cuts/min)
python3 film.py --sheet _work/tests/film/b/sh --range 168 270   # review sheets: first | mid | last + lines (shot indices)
python3 film.py --lipcheck                                  # mouths move only on their own lines
python3 film.py --still 395.0,600.5                         # stills -> W/tests/film/still_T.jpg
python3 film.py --cues                                      # W/cues/sfx_cues.json, music_cues.json, shots.json
python3 tools/validate.py [--part A|B] [--fps 4]            # 0 ERROR is the bar
python3 render.py --size 640x360 --fps 30 --workers 2 --out _work/preview_tmp --audio _work/align/vo_en.wav   # preview
python3 render.py --workers 3 --from_ 590 --to 595 --out _work/tests/render5 --audio _work/align/vo_en.wav   # 5 s full-mode test
P=2 bash tools/final_chain.sh > _work/logs/final_chain.log 2>&1   # FINAL 2560x1440 / 60 fps in chunks, then deliver.sh
PICTURE_ONLY=1 P=2 bash tools/final_chain.sh ...; P=2 bash tools/encode_chain.sh   # or: picture, then resumable HEVC segments
```
- `render.py` writes `film.mp4` into `--out`; the preview lives at `W/preview/preview.mp4` (640x360, 30 fps, narration).
- Full mode: contiguous slices per worker (one OpenCV thread each), libx264 crf 16, `.done` markers. Delete markers and
  slices before re-rendering a changed film into the same `--out`.
- The final render needs the final mix `W/mix/final/mix_en.wav` for `deliver.sh` / `encode_chain.sh`. Run two chunks at
  a time on the shared 4-core machine, as a harness-tracked background task (never nohup).

## Cue sheets: the sound step's contract
`python3 film.py --cues` writes `W/cues/sfx_cues.json` (`{t, name, gain_db, pan, space, params}`: every action of the
picture, from the shots' explicit cue lists and the cast's acting events), `music_cues.json` (`{duration, intensity,
events}`) and `shots.json` (the cut list).
- SFX names the picture asks for (the sound step maps them to recipes or library files): air brakes, `bus_door_fold`,
  `door_slap`, `door_slam_bus`, `door_motor`, `loudspeaker_click`, `whistle_two` / `whistle_long` (cast), `punch_clack`,
  `knock_door`, `deadbolt`, `deadbolt_slide`, `walkie_squelch`, `lights_blink`, `power_down` / `power_up`, `tape_skip`,
  `vhs_glitch`, `tape_warble`, `tape_rewind`, `engine_start_bus`, `engine_rev_bus`, `tyre_screech`, `brake_hiss`,
  `metal_rip` (the mirror), `radio_crackle`, `flag_rope_clink`, `broom_rip`, `broom_jam`, `wood_creak`, `wood_crack`,
  `fabric_rip`, `glove_snap`, `glove_squeeze`, `glove_slap_wall`, `hat_crumple`, `arm_stretch_creak`, `neck_ratchet`,
  `school_bell`, `clock_tick`, `clipboard_clatter`, `pencil_line`, `porch_light`, `flashlight_click`, footsteps (walks
  and runs: surface inside / stairs / grass / asphalt / bus), `marker_x`, `bus_ambience` (bus 9 morning).
- Music: the returning tune "Ride Right with Mister Whistlestop!" (original 1994 jingle) as `type 'jingle'` with a
  `version` (cold_open drone, title, music_box_warm, loudspeaker_detuned, slowed_tape, walkie_far, climax_warped L286..
  L364, music_box_warm again at Theo's stop L375, morning_warm L386, outro_warm L401..end), the `name_sting` at L394,
  plus `hit`, `riser`, `rule` and `silence` events, and the tension curve (`intensity`).

## Sound: the final mix
Rebuild after any picture change (about 15 min; peaks near 12 GB RAM, so never while a render runs):
```
python3 render.py --size 640x360 --fps 30 --workers 2 --out _work/preview_tmp --audio _work/align/vo_en.wav   # only if the picture changed: new preview, then move film.mp4 to _work/preview/preview.mp4
bash audio/final_mix.sh            # film.py --cues -> audio/mix.py (--plan full) -> mix_en.wav + mix.wav -> measure_mix.py -> mix_scenes.py -> preview_mix.mp4
```
Outputs in `W/mix/final/`: `mix_en.wav` (read by render.py / deliver.sh / encode_chain.sh), `mix.wav` (hard link),
`stems/`, `cues_used/` (both sheets as mixed), `measure.txt` / `measure.json`, `scenes/NN_name.png`; and
`W/preview/preview_mix.mp4`.
- `audio/sfx_plan.py` is this film's pass over the picture's SFX sheet (name -> recipe map, transient shifts, ADD beds:
  bus 9 mornings, the 911 call, the sirens, the morning birds). Every picture name is mapped on purpose: sfx.py's
  keyword guesses had sent glass_pound to a window smash, metal_rip to cloth, door_slap to a creak, bus_drive to rain.
- `audio/music_plan.py` EVENTS: `{'boost': dB}` marks the biggest scares (mix.py grades them to +8 / +9 / +10 LU
  momentary over the voice); a silence must end before the scare it sets up. `mix.py` ARC_TARGETS name line tags
  (rule1..rule7), so the rule-by-rule bed follows any voice re-edit.

- Result (18 Nov, after two remix passes): -14.03 LUFS integrated, -1.7 dBTP, voice = mix -0.01 LU, bed -12.2 LU under
  the voice; scares +6..+8.5 LU momentary over the integrated level (the hallway +7.7, LIGHTHOUSE +8.5, the lure +7.6,
  his defeat +6.7); outside the scares the mix never passes +2.8 LU. Bed in the gaps rises rule by rule -20.6, -20.8,
  -19.3, -17.9, -16.4, -16.3, -14.0 LU (rules 1-7). Open: "Almost.", "...Clever.", the hand, the doors and "Two of me."
  still cover their own words 2-9 dB in 1-4.5 kHz for 0.3-0.5 s (the tight voice edit leaves 0.15-0.3 s gaps); the 3:00
  bell peaks at +4.4 LU and "Almost." / "Backwards." / the hand at +4.8..+5.5 (target +6).

## Results (part B, 18 Nov)
- `plan_partb` adds 205 shots (L190..L418): 378 shots in all, median 1.76 s, 13:18 with the end card.
- `tools/validate.py`: 0 ERROR over all 378 shots (WARNs: a few sub-0.6 s cutaways, small reach gaps in hand-holds,
  the median below 2 s).
- Preview: `W/preview/preview.mp4` (640x360, 30 fps, 13:18, narration); 1 fps scans `W/tests/film/scan/`; cue sheets
  `W/cues/` (365 SFX events, 56 music events); review sheets `W/tests/film/b/`.
- Full mode proved on three heavy 5 s clips at 2560x1440 / 60 fps (the hallway capture 404.5 s, the aisle reach 579.9 s,
  the lot with the police lights 684 s): 300 frames each, no retries, 63-75 s per clip with 2 workers (about 0.23 s a
  frame: the whole film is about 3 hours on 2 workers). `W/tests/render5/`.
- `sets_bus.py`: one fix, `BuRoad.lights` accepts `his_pos` as f(t) (the doc promised it; it crashed).

## Review round 3: picture (18 Nov)
- Rule cards: the key phrase is yellow on a dark plate (engine `hud.rule_card(accent=, plate=)`); the reading underline is yellow.
- His busts frame the FACE: `B_bust` lifts any Whistlestop bust so the eyes sit about 0.4 H from the top (`eye_to`, default
  430; hands / acts move with it). Captions never double a line's own quote marks.
- `scam`: a push the plan asks for (f above the view's f range, up to 4) is no longer clamped to the view's 1.8 / centre box
  (many "3x" pushes had rendered as wides).
- Restaged: the phone-light scare (glove folded over her fingers; L177 reveal: him crouched by the couch, her hand in one
  glove, the walkie rising to the grin), the hallway (he fills it 1.6-1.9 m from her door, bent under the ceiling, hat
  folded on it, gloves on both walls, lit by her room), the rescue (foot insert, the glove snapping on the tail and the
  rip from the back of the aisle, a tighter catch), the long arm to Theo (from his seat, then the glove on his shoulder),
  the seat-saved bust (he creeps in, a glove at the lens), the crossing guard, the kneel cut (L373), the ticket insert
  sliding in, Grandma at the back door / crossing the yard, a hand on the mailbox letters, Sami's jolt, the palm on a
  visible window, Theo's raincoat reads yellow, the end card holds 4 s.

## Open problems
- Interiors seen from outside (his bus from the lot) only show figures through the open door: the steps / aisle beats
  are staged from inside views or the school lot.
- The school-lot wides keep the people small (about 100 px per metre): the action shots push in 2-3x.
- The broom in his doors is hard to read from the inside `doors` view at preview size.
- His busts: the redesigned head is big; framings keep his face in the upper half (`wbust` raises it).
