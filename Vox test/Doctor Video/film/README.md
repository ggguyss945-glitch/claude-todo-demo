# "If Your Doctor Calls At 3 AM... DON'T ASK WHAT THEY FOUND": film

Night Policy's rule-format horror film, built like the police, dummy and Bunnyman films: the same 2.5D engine, the cast
and set systems, the shot-list format (`film_bunny_ref.py`, `film_police_ref.py`, `film_dummy_ref.py` are kept as
references), the police header, rule cards and captions, the global look with a climax ramp, and cue sheets derived from
the picture. The picture follows `W/shotmap.md` (every line of the timeline -> the picture that carries it, the props'
continuity, the story clock).

All commands run from this folder (`Vox test/Doctor Video/film`). The work dir is `W = film/_work`.

| file | what |
|---|---|
| `film.py` | The shot list (`plan_film()`: cold open, 1979 and the family, rules 1-5, the comment prompt as a call ON HOLD (part A); rule 6, rule 7, the rescue and the ER, after and the twist, the outro (part B)), the builders `B_set`, `B_bust`, `B_ins`, `B_rule`, `B_pause`, `B_card`, `B_black`, `B_outro` (the insulin explainer, serious / treatable, call back, the voice in your head, the comment "don't" -> "ask" and the first names, the like, subscribe as a call that connects instantly, next time: the school bus, the 3 AM pick-up, the end card), the helpers (`P()`, `cm()`, `phone_rig`, `ghosts()`, `HIM()`, `NARR()`, `offer_acts` / `take_wrist_acts` (the ticket, the wrist), `carry_layer`, `mirror_acts`, `wheel_acts`, `wheelchair_run`, `write_card`, `card_burn`), captions / header, `escalate()`, the global look, cue sheets and the checks. Every time is keyed to `W/align/timeline.json` (`T(i)`, `W(i, word)`): no absolute times. |
| `characters.py` + `characters_doctor.py` / `CAST.md` | The cast (Doctor Later, Ruth, Milo, the narrator at 14 and 29, Doctor Halverson, Mom, the ER staff, the waiting room's grey people) and the acting. |
| `sets.py` + `sets_doctor.py` / `SETS.md` | Ruth's house (and its waiting-room state), 1979, the street, the clinic, the office, the car, the ER, the hospital hall, the cardiologist, the run, the outro room, the inserts. |
| `render.py` | Stills, test clips and the full worker/slice render. |
| `tools/validate.py` | The staging validator (reach, props, feet, cut continuity, prop states, shot lengths, camera moves). |
| `tools/strips.py` | 10-15 fps strips with a pop check. |
| `tools/final_chain.sh`, `tools/encode_chain.sh` (+ `enc_seg.sh`), `tools/deliver.sh` | The final render in chunks + the HEVC deliverable `W/deliver/If_Your_Doctor_Calls_At_3AM_EN_1440p60_HEVC.mp4` (title "If Your Doctor Calls At 3 AM... DON'T ASK WHAT THEY FOUND"). |
| `audio/` | The sound step (reads `W/cues/*.json`). |

## Sound fix round (critic review of the final mix)
- M1 rings: `mix.py` RING_DUCK_DB (9 dB): every `landline_ring` / `phone_ring` dips under the narration, keyed on the
  voice (10 ms attack, 0.12 s hold). `sfx_plan.py`: rings closer than 1 s (the nine in 4 s) are short bursts (0.5 x the
  spacing) and `sfx.py _bell_burst` damps a short ring's tail (70 ms), so the nine count as nine.
- M2 arc: `mix.py ARC_TARGETS` re-keyed to this film's 'Rule number N.' lines (65, 103, 124, 146, 192, 213, 252; the
  old indices were a rule off), targets -19 / -17.5 / -16 / -14.5 / -13 / -11.8 / -10.6 LU (bed in the gaps, re voice),
  ARC_MAX_DB 6.
- M3 warm hold: `music_plan.IDENTITY` plays the warm arrangement from "Change it to 'ask.'" (s442-0.5) to the end card,
  three times round, a tone up (G) over the bright track; `score.py` HOLD_LIFT warm +2.5 (was -1), SHOW_DUCK warm -15;
  car_radio +2 (was -1).
- M4 tear / match: already on "tore" / "lit" from the picture round (cues checked: 697.25, 491.66).
- Scares: true silences (level 0.95) added before "It was a waiting room.", "Take a seat." and "He was in the back
  seat."; true silences now dip the room tone 15 dB (was 6). The boosted hits sit at line end + 0.17 s (nosnap).
- Grandma's voice: `tools/vo_voices.py` G 162 Hz, formants x1.08, jitter 2 % (G_sharp 166, G_hush 164, G_soft 166);
  re-voiced in place (her 12 lines from narration_clean.wav, same slots) into narration_en.wav and W/align/vo_en.wav:
  measured 160-168 Hz against Halverson's 187-196 Hz (x1.15).
- Three line-final "p" releases the TTS spat out as ticks (540.88, 626.64, 815.69 s) softened (3.5 kHz low-pass, -5 dB,
  16 ms) in narration_en.wav and vo_en.wav.
- Result (`_work/mix/final/measure.txt`): -14.1 LUFS, true peak -1.7 dBTP, no voice weak spot (was 2), bed in the gaps
  rule 1..7 -19.3 / -17.7 / -16.4 / -14.9 / -13.5 / -12.2 / -11.3 LU re voice (rising every rule), loudest scare +9.1 LU
  momentary at 714.9 ("Take a seat."), rings 1-4 kHz under the voice: p10 7-12 dB, median 19-30 dB. Not done: the
  knocks still start on "knocked." and the boosted hits sit +0.08..0.17 s after the line (moving the knocks moves the
  picture's KNOCK tags: needs a preview re-render).
- `sfx_plan.EDIT` (new `at` key: move a cue onto a word): the KNOCK tags' pops dropped, the 1979 steps -5 dB, the porch
  steps full weight +2 dB, the card tear on "tore".

## Picture fix round (critic review of preview_mix.mp4)
- `lap_layer()` (film.py): Ruth sitting on the kitchen floor (`sit_floor`, the skirt now drapes over the knees) with Milo
  sitting between her knees, her arms round him, rocking; camera `K_LAP`. Line 303: the narrator kneels, takes him, rises
  (`carry_layer(..., rise=t)`).
- `crowd_for()` / `_is_wait()`: every view of the waiting-room living room (sets and bust backgrounds) gets the grey
  people automatically unless the shot stages them itself (`no_crowd=True` to opt out).
- characters_doctor.py: perched seats too high for the feet (Milo on the exam table) dangle the shins (`_leg_chain`);
  Doctor Later's limbs are thin and black (thin rim), shins 128 cm (knees above the head), short thin sleeves; in the
  car the cone bows forward against the roof; `halverson_rain` keeps the bun; `careful_smile`, `pleading`, `set_jaw`
  read unsmiling.
- sets_doctor.py: insert `blood` (Milo's arm, the gloved hand, the MILO tube; kid-safe).
- New cameras: `K_LAP`, `CLINIC_SIDE`, `K_JEANS`, `W_REACH` (his reach across to the machine), re-aimed `K_PHONE_LOW`,
  `W_HANDS`, `CLINIC_TWO`.

## Inputs
- `W/align/timeline.json` (456 lines, 1295.17 s; film 1305.17 s with the end card), `W/align/asr_cache.json` (word times),
  `W/align/vo_en.wav` (the voiceover). Voice: `W/narration/voice_report.md`.
- Script: `../script/narration_en.txt`.

## Commands
```
python3 film.py --list                                      # every shot (+ median, cuts/min)
python3 film.py --sheet _work/tests/film/B --range 192 400 --threads 1   # review sheets: first | mid | last + lines
python3 film.py --still 695.5,724.8                         # stills -> W/tests/film/still_T.jpg
python3 film.py --cues                                      # W/cues/sfx_cues.json, music_cues.json, shots.json
python3 tools/validate.py [--part A|B]                      # 0 ERROR is the bar
python3 tools/strips.py --times 722.4-731 --fps 12          # motion strips + pop check -> W/tests/polish/strips
python3 render.py --size 640x360 --fps 30 --workers 2 --out _work/preview_tmp --audio _work/align/vo_en.wav   # preview
python3 render.py --workers 2 --from_ 724 --to 729 --out _work/tests/render5 --audio _work/align/vo_en.wav   # 5 s full-mode test
P=2 bash tools/final_chain.sh > _work/logs/final_chain.log 2>&1   # FINAL 2560x1440 / 60 fps in chunks, then deliver.sh
```
- `render.py` writes `film.mp4` into `--out`; the preview lives at `W/preview/preview.mp4`.
- Full mode: contiguous slices per worker (one OpenCV thread each), libx264 crf 16, `.done` markers; a range render
  matches the full render frame for frame. Delete markers and slices before re-rendering a changed film into the same `--out`.
- The final render (`tools/final_chain.sh`, `K=24` chunks, `P` processes, resumable) needs the final mix
  `W/mix/final/mix_en.wav` for `deliver.sh`. Run two chunks at a time on the shared 4-core machine.

## Cue sheets: the sound step's contract
`python3 film.py --cues` writes `W/cues/sfx_cues.json` (`{t, name, gain_db, pan, space, params}`), `music_cues.json`
(`{duration, intensity, events}`) and `shots.json` (the cut list). The HOLD MUSIC is `type 'hold'` with a `version`
(part A: tinny_receiver, tinny_1979, onhold_clean, receiver_close, receiver_far(_slow), every_room(_warped), hummed;
part B: ceiling (the waiting room), pulse (slows at each count, `slow_at`), far_hall, warm (the subscribe call)), plus
`hit`, `silence` and the rule stings. Spaces: inside, outside, close, bath, wait, car, hospital, office, clinic.

## Sound prep (the Doctor film)

- Catalogue: `python3 audio/epidemic_catalog.py --doctor` -> `audio/catalog_epidemic_doctor.json` (the doctor set
  `_work/samples/epidemic`, one flat folder, first; then the bunny, dummy, delivery, police and mirror sets).
  `audio/library.py` and `audio/score.py` read it first.
- Review of every new file: `_work/mix/sfx_review.md` (measured by `audio/review_doctor.py`: `_work/mix/review/`).
- The HOLD MUSIC (the film's returning tune, original): `audio/hold.py`; `python3 audio/hold.py` renders every
  version to `_work/mix/hold/` with `hold_check.json` (a pitch check of every melody note) and `hold_sheet.png`.
  Versions: studio, phone_1979, landline, rooms, hum (Grandma), pulse (slows at each count), ceiling, car_radio,
  far_hall, warm (the outro).
- SFX names for this film: `sfx.DOCTOR_NAMES` (plus `pen_click` rebuilt on the new ballpoints, and the aliases at
  the end of sfx.py). `python3 audio/sfx_doctor_check.py [names]` renders and measures each to `_work/mix/sfx_doctor/`
  (`sheet.jpg`). New spaces: 'waiting', 'er', 'office'.
- Voice FX (lines.py fx codes, `audio/mix.py`): 'phone' (landline band, grit, hiss), 'recording' (the phone system's
  lady), 'rooms' (every room: delayed copies in the voice plus a wide stereo wash on the events bus), with 'door',
  'whisper', 'memory' as before; an unknown fx stays dry with a warning.
- Music map: `audio/music_plan.py` (`--table` prints it); the score renders its 'hold' events with hold.py.
- Tests: `python3 audio/sfx_tests.py [1..8] [--jobs 2]` -> `_work/mix/tests/` (wav + json per test, `--sheet`).


## Sound: the final mix
Rebuild after any picture or narration change (about 15 min, peaks near 12 GB: no render at the same time):
```
bash audio/final_mix.sh            # film.py --cues -> mix.py --plan full -> measure_mix.py -> mix_scenes.py -> preview_mix.mp4
python3 audio/sfx_plan.py          # dry run of the SFX pass (what is renamed, dropped, added)
python3 audio/music_plan.py --table
```
- Out: `W/mix/final/mix_en.wav` (= `mix.wav`, hard link), stems in `W/mix/final/stems/` (1.4 GB, read by
  measure_mix.py; delete them after the last measure if disk is short), `measure.txt`, `scenes/NN_name.png` (one
  sheet per scene, `_SC` in mix_scenes.py by line number), `cues_used/` (both sheets as mixed). Preview with the mix:
  `W/preview/preview_mix.mp4`.
- `audio/sfx_plan.py` is this film's: film.py's names -> recipes (phone_ring -> landline_ring one ring per cue until
  the final twist, typing -> typewriter, room_tone kinds -> house_night / er_bustle, the fluorescent bed ->
  waiting_room from the door, breath_fast runs -> one breathing bed per run, tape_peel -> q 1..4), drops (the
  per-count pulse cues, the car rain, hold_click, cold_breath, car_drive / car_accelerate), EDIT re-levels and ADD
  (waiting room under the cold open, 1979 dial and coffee, line hiss, receiver set down, streetlight, NOW SERVING,
  clipboard, one pulse_count with the three counts, carry, rain at the door, the car idling then the drive, dawn,
  the 3 AM office, the outro's call), all anchored to line / word times.
- Boosted scares (`music_plan.EVENTS`, `boost`): the waiting room (e217), "Take a seat." (e250), the first question
  (e270, after a silence that kills the pulse-slowed hold music through the whole question), the face under the tape
  (e280), "Then... me." (e285), the back seat (e332). Hits sit in the gap after the line, not on the words.
- Measured (pass 3): -14.1 LUFS, -1.7 dBTP, scares +6.5..+8.8 LU momentary over the integrated level, narrated
  lines elsewhere at most +3.2 LU, no voice weak spot, music present 95 % (> -26 LU), hold music 13 returns.

## Results (part B and the finish of the picture)
- 396 shots, 1305.17 s; median 2.73 s, p10 1.49, p90 5.32, 18.2 cuts/min (`python3 film.py --list`).
- `python3 tools/validate.py`: **0 ERROR**, 28 WARN for the whole film (long held cards / inserts, cross-room moves between
  scenes, small reach misses under 45 px, two camera moves).
- Review sheets of part B: `W/tests/film/B_*.jpg` (first | mid | last + lines, every part B shot checked; fix stills
  `W/tests/film/B_fix1.jpg`). Motion strips at 12 fps with the pop check: `W/tests/polish/strips/s*` (the phone and the
  cord, the knock / note / match, the ticket tear and offer, the wrist, the carry, the car pulse, the ER doors and the
  wheelchair): no single-frame pops; the flagged frames are the long arm's continuous reach.
- Full mode at 2560x1440 / 60 fps: `W/tests/render5a.mp4` (the wrist, 724-729 s), `render5b.mp4` (HIM revealed, 656-661 s),
  `render5c.mp4` (Mom with the wheelchair, 967.9-972.9 s), one worker each, about 1.5 frames/s.
- Cue sheets: `W/cues/sfx_cues.json` (299 events), `music_cues.json` (66 events), `shots.json`.
- Preview: `W/preview/preview.mp4` (640x360, 30 fps, the narration).

## Open problems
- Narrator busts in the waiting room still read close to frontal (turn -0.62); the floor-sitting poses on the kitchen
  floor are small; the rear-view mirror shows Milo large in the glass; Halverson reaches the steps late in 307.
- The advice list and the comment card hold long (animated, every item lit as it is read).
- Mixing: the sound step reads `W/cues`; the hold-music part B versions (ceiling, pulse, far_hall, warm) are named in
  `music_cues.json`.

## Verify round (after the picture and sound fix rounds)
- Checked every blocker and major on `_work/preview/preview_mix.mp4` (stills/strips) and the mix stems (ring ducking, warm hold music, cue onsets); 1 fps scan of the whole preview: nothing newly broken.
- Small picture fixes (no sound cue moved): line 50 Halverson's careful smile now lands on "took one look" (`WD(50,'smile') - 0.9`);
  lines 281-285 faces under the tape in five varied, closer framings (scale 0.8-1.4, offsets, turns);
  line 359 the chest-pain man and the nurse walk off together (`ER_LEAVE`) while the empty chair rocks.
- Preview patched in place: ranges 179-186, 786-801, 993-999 re-rendered with `render.py --from_ --to` at 640x360/30
  and spliced into `preview.mp4`; `preview_mix.mp4` re-muxed with the existing mix audio (mix not re-run, cues unchanged).
- Still open (picture): stiff straight-arm holds (383, 451-454, 990 s); no ticket between his fingers on line 246; no pen
  in the "She wrote them down" insert (crude arm); Halverson not on the steps on line 307; ER doors do not visibly slide
  and Mom crosses sideways (348-349); the pen insert in the car keeps the green waiting-room background (334);
  Ruth's receiver covers her face (302). Sound: knocks still start on the word "knocked." (minor).
- Preview AAC true peak reads -0.9 dBTP (encoder overshoot); the delivery mix `mix.wav` is -14.1 LUFS, -1.69 dBTP.
