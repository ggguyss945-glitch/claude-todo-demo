# "If A Delivery Driver Rings Your Doorbell At 3 AM... DON'T SIGN FOR IT": film

This film is made the way the police film was ("If A Police Officer Knocks At Midnight...", `film_police_ref.py`). It uses the same engine, cast and set systems, the same shot-list format, the police header, rule cards and captions, the same global look with the red climax ramp, and cue sheets derived from the picture.

All commands run from this folder (`Vox test/Delivery Video/film`). The work dir is `W = film/_work`.

| file | what |
|---|---|
| `film.py` | The shot list (`plan()`), the shot builders `B_<kind>`, captions/header overlay, `escalate()`, global look, cue sheets. The module docstring lists the shot kinds and plan conventions. |
| `film_police_ref.py` | The police film's shot list, kept as the format reference. |
| `characters.py` / `CAST.md` | Cast, acting clips, the driver's smile arc, the box (`BoxActing`), props. |
| `sets.py` / `SETS.md` | Sets (porch / doorbell / peephole / street / hall / upstairs / Lily's room / side yard / doorway), inserts, the app phone, the 3:41 delivery photo (`photo_lily_scene`). |
| `render.py` | Stills, test clips and the full worker/slice render (defaults to `W`). |
| `engine/` | The 2.5D engine (camera, layers, lenses, grades, HUD). |
| `audio/` | Sound pipeline. It reads `W/cues/*.json`. `audio/final_mix.sh` rebuilds the final mix after picture changes; `audio/measure_mix.py` measures it (see **Sound: the final mix**). |

## Inputs
- `W/align/timeline.json`: line times for the 286 lines. `W/align/asr_cache.json`: word times. `W/align/vo_en.wav`: the voiceover, 48 kHz, 640.72 s. These are written by `tools/align.py`.
- Script: `../script/lines.py` and `../script/narration_en.txt`.

## The shot list
```
python3 film.py --list                    # every shot (index, start, length, kind) + count / median / p10 / p90
python3 film.py --cues                    # cue sheets -> W/cues/sfx_cues.json, music_cues.json, shots.json
python3 film.py --sheet W/tests/film/sheet_a --range 0 118 --cols 6 --tile 320     # mid-shot stills as contact sheets (frames at 960x540)
python3 film.py --sheet W/tests/film/sheet_b --range 118 235 --cols 6 --tile 320
python3 film.py --bench 40 --size 2560x1440 --threads 1                     # full-size speed, one process
python3 film.py --bench 1 --shots 13,17,45,51,78,189,199,200,204,208,218,229 --size 2560x1440 --threads 1   # chosen shots
```
- 235 shots, median 2.41 s (p10 1.36, p90 4.19, shortest 0.58), 21.9 cuts/min (fix 3 merged 19 needless same-setup cuts into
  continuous moves; the police film runs 23.4).
- Contact sheets: `W/tests/film/sheet_a_00..03.jpg` (shots 0-117) and `sheet_b_00..03.jpg` (118-234), 36 shots a sheet, each tile labelled `index kind time`. Run the two halves as two processes (about 1.5 min each). The fix-3 sheets are in `W/tests/fix3/sheets/`.
- The bench writes `W/tests/film/speed_<size>.json` (or `speed_shots_<size>.json` with `--shots`).
- `film.py --cues` writes:
  - `sfx_cues.json`: `{t, name, gain_db, pan, space, params}` (339 events: the hazard relay is one phase-locked bed now, not 400 ticks).
  - `music_cues.json`: `{duration, intensity, events}` (115 events; `duration` = the picture's length, 644.22 s).
  - `shots.json`: the cut list, `{i, t0, t1, kind, space, loc, era, cut}`, for the sound team.
  - `music_cues_plan.json` in the same folder is the audio teammate's file; `--cues` does not touch it.

## Rendering
```
python3 render.py --stills 12.5,151.9,371.0 --size 960x540                  # -> W/tests/render/still_*.jpg
python3 render.py --clip 370 380 --size 960x540 --audio W/align/vo_en.wav   # one process test clip
python3 render.py --workers 3 --audio <mix.wav>                             # FULL: 2560x1440, 60 fps -> W/picture/picture.mp4 + film.mp4
python3 render.py --workers 3 --from_ 553.5 --to 558.5 --out W/tests/render5 --audio W/align/vo_en.wav   # a 5 s full-mode test
python3 render.py --size 640x360 --fps 30 --workers 2 --out W/preview --audio W/align/vo_en.wav          # low-res preview
```
(`W` in these commands stands for `_work`.)
- **Full mode** splits the range into contiguous slices, one per worker process, each with one OpenCV thread. Each slice is encoded with libx264 at crf 16, preset faster, and the slices are joined with a stream copy. Workers pass absolute frame indices to the film (the same as stills), so a range render matches the full render frame for frame.
- **Finished slices** get a `.done` marker. A re-run skips them, so delete the markers (and the slices) before rendering a changed film into the same `--out`.
- **Audio**: `film.mp4` gets the audio padded to the picture's length (the last 2 s of black after the final line stay). For a partial range (`--from_ / --to`) the audio is muxed from `--from_`. Until the mix exists, use the voiceover `W/align/vo_en.wav`.
- **The film is 644.22 s**: the narration (640.72 s) + 3.5 s (fix 3 added 1.5 s of black after the last knock so the end
  cadence rings out inside the picture). 38,653 frames at 60 fps.
- **The preview** is `W/preview/preview.mp4` (640x360, 30 fps, 644.2 s, the voiceover) and `W/preview/preview_mix.mp4` (the same
  picture with the final mix). The preview render was run with `--audio _work/mix/final/mix.wav`; its `film.mp4` became
  `preview_mix.mp4`, the voiceover was muxed onto `picture.mp4` for `preview.mp4`, and the slices were deleted.
- **The 5 s full-mode test** is `W/tests/render5_553.5-558.5_2560.mp4` (the app screen cutting to the 3:41 photo): 2560x1440, 60 fps, 300 frames, 3 workers, end to end in 51 s while the mix was running; its audio offset checks to 553.50 s.

## Speed (police budget: 0.6 s/frame at 2560x1440, one process, one OpenCV thread)
- `film.py --bench 40` (160 frames over 40 shots, shared machine with the mix running): mean 0.38 s/frame including cold caches, 0.28 s steady. The heaviest shot is 0.45 s steady (shot 221, the full-screen app over the hall).
- Fix 3, consecutive frames (every 3rd frame of the shot, cold caches included, one process): the door push with your hand
  (199) 0.25 s, Lily's room window push (200) 0.25, the vent push (208) 0.21, the one-move 3:41 photo drawn live (204) 0.29,
  the 3:11 clock push (78) 0.25. `--bench` samples 4 frames spread over a shot, so on the shots with an optical push
  (`mv='keys'` with f > 1) every sample re-bakes a layer cache at a new density and reads 0.8-1.4 s: not what a render sees.
  Keep optical zoom (f) changes small or constant on big cached sets (shot 199 holds f and pushes into the image instead).
- Review 4, consecutive frames (one process, the mix running beside it): the door push with your hand (199, now a deeper
  dolly z 3.0 -> 4.6 at a constant optical f 1.3) 0.19 s steady; the 3:41 photo (204) 0.27; Lily awake by the vent (208)
  0.27; the sting street with the van rolling in (229) 0.19; Lily asleep (197) 0.19. An optical f of 1.7 or more on the
  upstairs set costs 2.4-2.6 s a frame (its caches are baked at that density): keep f <= 1.3 there.
- The heaviest shots (`--bench 1 --shots ...`, steady): doorway 122 (memory, door open) 0.54 s, phone 221 0.44 s, doorway 234 0.39 s, keys 237 0.29 s, the 3:41 photo shots 0.16-0.19 s, the latch insert 0.15 s. The first frame of a shot can take up to 1.5-2.4 s while its static layers are baked.
- The doorway's dolly is capped at 2 %/s: a faster optical zoom re-blurs its frame-sized walls every frame (0.74 s).
- The 3:41 photo is one shot drawn live (vector, sharp at any zoom, ~0.15 s a frame for the still itself); the old `comp=` crops still bake one cached layer each.
- The full film is 38,653 frames at 60 fps. Three workers render it in about 1.5 h on a quiet machine.

## Sound: the final mix
**Rebuild after any picture change** (about 7 min; `mix.py` peaks at 7 GB, so no render may run at the same time):
```
bash audio/final_mix.sh                 # all five steps below; --no-preview skips step 5
```
which runs, from this folder:
```
python3 film.py --cues                                                                  # 1. cue sheets from the picture
(cd audio && python3 mix.py ../_work/align/timeline.json ../_work/align/vo_en.wav - ../_work/cues ../_work/mix/final --langs en)   # 2. the police mix
ln -f _work/mix/final/mix_en.wav _work/mix/final/mix.wav                                # 3. mix.wav (render.py / deliver.sh read mix_en.wav)
python3 audio/measure_mix.py _work/mix/final --plot                                     # 4. measure + misfire list
ffmpeg -v error -y -i _work/preview/preview.mp4 -i _work/mix/final/mix.wav -map 0:v -map 1:a -c:v copy \
  -c:a aac -b:a 320k -ar 48000 -af apad -shortest -movflags +faststart _work/preview/preview_mix.mp4   # 5. onto the preview
```
Full picture with the mix: `python3 render.py --workers 3 --audio _work/mix/final/mix.wav`. `python3 audio/mix.py --check _work/cues _work/mix/final` exits 1 when the mix is older than the cue sheets.

**Outputs** in `W/mix/final/`: `mix.wav` (= `mix_en.wav`, 48 kHz 24-bit stereo, 644.22 s = the picture's length exactly, with a
1.5 s master fade to silence over the cut to black), `stems/{voice_en,music,sfx}.wav` (float, final gain, before the limiter), `mix_report.json`, `mix.log`, `measure.json` / `measure.txt`, `measure_cues.json` (every one-shot cue re-rendered and checked), `measure_plot.png` (loudness map: voice, music, SFX, silences, hits, rule cards). The preview with the mix is `W/preview/preview_mix.mp4` (640x360, 30 fps, 644.2 s, AAC 320k stereo).

**Measured** (`measure_mix.py`, BS.1770 per-channel K-weighting; "rel voice" = against the voice stem's integrated loudness):

| | result | target |
|---|---|---|
| Mix integrated / true peak | -14.03 LUFS / -1.70 dBTP | -14, <= -1.0 |
| Voice vs mix | -0.06 LU | within 0.5 |
| Voice minus bed (music + SFX) during speech, 400 ms blocks | p5 7.6 LU, median 17.1; under 3 LU in 1.0 % of speech, under 0 LU in 0.4 % | voice always clear |
| Same in the 1-4 kHz intelligibility band | p5 11.0 dB, median 24.8 | |
| Music outside the 20 silences | above voice -32 LU 100 %, above -26 LU 97.6 %; no holes | under the voice the whole time |
| Silences | 20 (1.86/min), 18.2 dB deep (median), all >= 1.7 s, none at 376.9 / 436, one added at 136.4 | 1.5/min, 15 dB |
| Bed integrated / 3 s p10-p50-p90 / LRA | -13.7 LU / -21.6, -16.0, -11.0 / 11.7 LU | -13 +- 1 / p50 -16 / 13-14 |
| Bed by quarter | -15.2 / -15.8 / -13.5 / -11.7 LU; loudest 10 s at 633 s | Q2 calmest, end loudest |
| Bed spectrum < 250 Hz / 250 Hz-4 kHz / > 4 kHz | 74 / 26 / 0.6 % | 70 / 29 / <= 2 % |
| Hits | 3.07/min; peak median -4.8 LU, max +4.5 LU rel voice | 3/min; +2 / +9 |
| The end | the last knock (640.04) lands in silence, the hit 0.15 s after it; the last 100 ms of the file -103 dBFS, last sample 0 | no chop |
| One-shot SFX cues checked | 246: 0 silent, 0 failed, 8 flags left (below) | |

**Cue flags left** (all looked at): the doorbell button click under its own ding-dong (37.0 s), a cloth rustle and the
driver's last step on the porch under the voice (159.8, 469.1 s: texture; his steps fade away from the mic on purpose), three
box knocks that keep only 15-16 dB above 300 Hz (417.5 outside; 490.4 and 495.3 in the hall, the all-night loop), and the
sunrise tape cut / box flaps whose recorded transients sit 130 ms after the cue (no exact picture sync point).

## Fix round 3 (picture and sound review of the first preview)
Picture:
- **Backs of heads**: the hair covers the skull down to the nape (`characters._nape`, `_hairline`) and a head turned more than
  ~100 deg leaves out the jaw under the back hairline (`_nape_cut`): seen from behind you get hair, small ears and the neck,
  never a pale 'face' oval (all from-behind shots and the 3:11 photo, which is drawn live from the cast).
- **Lily's window**: the lower sash is up with a black night gap, the curtains blow into the room (`sets._curtain_billow`,
  gusts lift the hem up to 30 % and swing the free edge across the gap); "wide open / curtains moving / bed empty" is one
  shot: a push to the window (`KeyCam` optical zoom), then a pan down to the empty bed.
- **The driver** is never pleasant: `DRIVER_STAGES` start at a fixed grin with a line of teeth and tiny pupils; he talks
  through it (`talk` 0.72) and the bust tablet is held by his hand.
- **The 3:41 photo**: he stands on the green wheelie bin under her window, the arm bent (reach solved on `hand_pos`), head
  turned back over his shoulder into the flash; the four photo shots are ONE 12.7 s move over the live-drawn still
  (`B_photo path=`), stamp top right, clear of faces and captions.
- **Merged cuts** (19): the doorbell ring/feed (36-43 s), the order screen, the tablet insert (124-137 s, the letter draws
  itself in on "isn't"), the timestamp zoom, the box look, the label tilt, the photo 3:11 / photo gone / app-updates / next
  night phone shots (keyed phone `zkeys`), the window search, the van leaving through her window, the 3:41 photo.
- **Motion**: lens shots on the deep sets (upstairs, side, hallback, lily) get a 2.8 %/s post push + drift and the upstairs a
  nervous handheld; snap punch-ins are eased 0.24 s pushes; the run through the house is a running handheld follow
  (`surface='inside_run'`), "open a crack" is a dark door with a bright slit, "you push the door open" is your hand.
- **Story beats**: the app shows only the photo and "Return complete" until the reveal (`sig`), the box at the door is in the
  doorbell lens with its label, the sting's label reads "Lily" in her hand, the van comes from down the street, the empty
  box 21 years ago, the cut tape, sitting down next to mom, the phone glow at 3:07, the 3:39 clock on what Lily heard, the
  open window from outside, terror (not drowsiness) on your face.
- **Climax look**: from rule 7 (508 s) a faster ramp into red and dark, and the van's hazards wash the frame in blinking red
  (`engine.post.Spill`) until they stop on "stop" (`T_HZ_OFF` 591.65). Red pixels: <= 0.6 % per tenth before, 4.5 % over the
  last 35 %; luma 39 vs 44 in the first 65 % (12 % darker; the flash-lit photo and the sunrise keep it from 15 %).
Sound:
- The mix is the picture's length with a master fade; the score's end fade runs even when the cadence outlasts the film.
- Knocks have their own bus: out of the foley-dip key and the pre-hit dips (only the first knock of a group dips 2 dB).
- The payoff knocks are heard (640.04 in silence, the hit after it; 378.8 hit at 0.5, 0.3 s late, close knock +4 dB).
- Risers peak on the reveal words (rings, empty, shine, wide, Lily); none into silences or doubling a card riser.
- "Two, then one" at 489 is clean (the all-night loop leaves 1.2 s either side); the faster knocks group 0.16 / 0.33 s.
- 21 years ago the box murmurs (`box_voice` + whispers), the van door slams on "shut" (+6 dB), the van arrival +6 dB.
- The sunrise is heard (+15 dB, the open porch with birds from the door creak; no impact on the soft white cut).
- One set of stair steps (mom in slippers on the stairs at -7), a running pace for the search (3.5 steps/s).
- The diesel idles under every exterior van shot (a second layer on top of the indoor bed), the pull-away +4 dB.
- The hazard relay is one phase-locked bed; tag pops are off in the hushed beats; the doorbell speaker clicks only when he
  starts talking again; what Lily heard comes through her vent; the far knocks are 6 dB up.

## Review 4 (verification of fix round 3)
Every fix-3 item was checked on the new preview (1 fps scan of the whole film, 4-6 fps strips of the climax and the end,
native and 2560 stills, optical-flow camera fits per shot, red / luma per tenth) and on the new mix (the sound critic's
loudness curves, `_work/review/snd/tools`). Evidence: `_work/review/v4/`. What changed in this round:
- **The 3:41 photo** no longer spells "Lily" before the reveal: the flash flares off the tablet's glass over the signature
  box (`sets.photo_lily_scene`; the name is first read on the tablet insert at 571.5 s). The driver's head is turned further
  over his shoulder (`h_turn` -1.8): both ringed eyes and the grin catch the flash (it read as a smeared profile).
- **Lily in bed**: "she sleeps with a nightlight..." (535.7 s) showed an empty-looking bed before the door is opened; she is
  now visibly asleep (hair on the pillow, eyes shut, the quilt at her chin); "she heard the knock through her vent"
  (573.8 s) shows her awake in bed (`bed='awake'`, eyes open toward the vent).
- **"You push the door open"** (540.9 s): the camera is now near her door (dolly z 3.0 -> 4.6), so your hand meets the door's
  edge instead of pushing at a door at the far end of the hall.
- **"Somewhere down the street"** (633.4 s): the van's amber flashers wash in from down the street first (a blinking
  `Spill` growing over the shot, `post_fn` now works on street shots), then the van rolls into frame.
- **The red build** starts at 455 s (the box at the door): a faint blinking hazard wash ramps up to the rule-7 climax; the
  3:41 photo carries the hazard light frozen in it (static red spill, 0.3 stop darker).
- **Sound**: the diesel idle layer on exterior shots +8 dB (-1 -> +7), the dawn porch bed +2 dB.
