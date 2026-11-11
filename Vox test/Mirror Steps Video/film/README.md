# "If The Queen Of Spades Appears In Your Mirror... DON'T MAKE A WISH" (v2): build and delivery

Everything runs from this folder (`film/`). Work files go to `_work/` (gitignored). The brief is `DIRECTION_V2.md`; the plan
is `plan/shots.json` (295 shots after review round 2's flow pass: 449 written, merged into continuous moves, `PLAN_V2.md` section 0); the picture is assembled by `film.py` from `sets.py` + `sets_v2.py`
(SETS.md), `characters.py` (CAST.md) and `ui_v2*.py` (UI_V2.md) with the engine in `engine/`; the sound is built in
`audio/` from `plan/sound_plan.json` plus the picture's own events.

Output: 2560x1440, 60 fps, 700.0 s (42,000 frames), English narration and captions. The narration, its timeline and the
v1 mix are unchanged (the sound pass re-syncs the mix to the v2 cuts).

## 0. Inputs that must exist
- `_work/align/timeline.json`, `_work/align/asr_cache.json`, `_work/align/vo_en.wav` (the narration on the film timeline)
- the owner's Epidemic files in `_work/samples/epidemic/{sfx,music}` (licensed; never copy them out of `_work`)

## 1. Checks before the long render (minutes)
```
python3 plan/make_plan.py && python3 plan/validate.py      # the plan (only if plan/shotlist.py changed)
python3 film.py --sheet _work/film_v2/sheets/s --part 1/2 --keep _work/film_v2/stills   # mid-shot still of every shot,
python3 film.py --sheet _work/film_v2/sheets/s --part 2/2 --keep _work/film_v2/stills   # 960x540, 12 contact sheets (~4 min)
python3 film.py --sheet _work/film_v2/chk S190@284.6 S306       # single shots, optional @time
python3 tools/film_v2_checks.py                                  # one labelled 720p still per v1 error (33) + errors_sheet.jpg
python3 film.py --bench S001 S140 S233 S190                      # full-size s/frame (one OpenCV thread, as in a worker)
python3 tools/shot_frames.py OUT.jpg S129 289.7-293.1 --n 5      # n frames across shots / spans (checks of continuous moves)
python3 tools/at_times.py OUT.jpg 106.9:119.9:12 134.2 --cols 4  # frames at film times (A:B:N = N times), labelled shot/set/view
python3 tools/view_try.py OUT.jpg S052 110.5 cabin_now/master     # a shot's moment in other set views (compare set-ups)
python3 tools/dyn_flicker.py [ids]                               # flicker scan of the travelling (cam3) shots' room layers
python3 tools/motion_metrics.py CLIP.mp4 T0 [--json OUT]         # the critic's 60 fps spike / jerk measure on a clip
python3 render.py --stills 131.5,605.3 --size 960x540            # -> _work/tests/render/still_*.jpg
python3 render.py --clip 600 606 --size 960x540 --audio _work/mix/final/mix.wav
```
Low-res preview of the whole film with sound (8 min with 2 workers), then its measurements against the brief (5 min; the
decoded frames are deleted afterwards unless `--keep`):
```
rm -f _work/preview_v2/slice_*                               # finished slices (.done) are reused, even if the code changed
python3 render.py --size 640x360 --fps 30 --workers 2 --crf 23 --out _work/preview_v2 \
    --audio _work/mix/final_v2/mix.wav --name preview.mp4
python3 tools/measure_preview.py _work/preview_v2/preview.mp4    # -> _work/preview_v2/measure_preview.json
```

## 2. Final picture (do not run while teammates render)
```
python3 render.py --workers 3                             # -> _work/picture/picture.mp4 (2560x1440, 60 fps)
```
- 3 worker processes, each one contiguous slice, libx264 crf 16 preset faster, 1 OpenCV thread per worker and 2 x264
  threads; the slices join with a stream copy.
- Progress: `_work/picture/progress_00.json` ... `_02.json` (`{done, total, fps}`); `python3 tools/progress_page.py _work
  _work/page/index.html` turns them into the counter page.
- Resume: finished slices leave `slice_NN.mp4.done` and are skipped on a re-run. Delete `_work/picture/` to start over.
- Measured speed (v2, 2560x1440, one OpenCV thread): warm median per frame 0.19-0.49 s on the 24 heaviest candidate
  shots (heaviest S001 the hook's Queen ECU 0.49 s, S140 card 2 0.45 s, S233 0.43 s, S190 H1 0.43 s); a shot's first
  frame costs 0.3-6 s while it bakes its cached layers. The 5 s end-to-end test (600-605 s, the red climax, 3 workers)
  ran at 2.8-2.9 frames/s per worker, about 8.7 frames/s in total: plan on 80-95 min for the 42,000 frames with the
  encode and the concat.
- Review round 1: the 23 travelling (cam3) shots (about 100 s of film) rebuild their room every frame; with the room bands
  rasterised at half resolution (`room3d.LIVE_BAND_RES`) they measure 0.41-0.84 s per frame at 2560x1440 (median over each
  shot: S156 0.41, S130 0.52, S291 0.61, S192 0.65, S046 0.84; the first frame of a shot 1.6-4.7 s while it bakes its plane
  textures), against 0.19-0.49 s for the cached shots: budget about 15 min more for the full render.
- Add `--audio _work/mix/final_v2/mix.wav` to also write `_work/picture/film.mp4` with the final mix muxed in.

## 3. Final mix, synced to the picture
`film.py --events` writes `_work/align/film_events.json` (version 2): the actual cut times (with each shot's transition),
every on-screen action the picture performs (acting clips of the staged cast, the cast `film.py` adds, card stamps, giant
numbers, stamps, red X, tags, flashes, glitches, glints, rewinds, phone states, the countdown) matched to the plan's cue
ids (retimed where the picture differs), new cues where the plan has none, plan walk cues replaced by the picture's own
footsteps (`drop`), and the picture's hit times (`hits`). The v2 plan already carries every HUD device cue at the time
ui_v2 draws it. `actions` lists every action with its time for checking.
Rebuild after any picture change (the same steps run in `_work/final_chain_v2.sh`; the mix takes about 6 min and 7 GB
of memory: run it when no render is running):
```
python3 film.py --events                                                  # only if the picture changed
python3 audio/cues.py --events _work/align/film_events.json --out _work/cues
python3 audio/mix.py _work/align/timeline.json _work/align/vo_en.wav - _work/cues _work/mix/final_v2 \
    $(python3 -c "import sys;sys.path.insert(0,'audio');import cues;print(' '.join(cues.MIX_ARGS))")
python3 audio/measure_mix.py _work/mix/final_v2 --cues _work/cues
python3 analysis/refmirror/snd_env.py ours _work/review/snd_v3/env/ours_final.npz --stems _work/mix/final_v2
python3 analysis/refmirror/snd_compare.py _work/review/snd_v3/env/ours_final.npz      # the table below, vs the references
```
The sound v3 test was built exactly so, from the current `film_events.json`, into its own folders (the final mix in
`_work/mix/final_v2` is still review round 1's):
```
python3 audio/cues.py --events _work/align/film_events.json --out _work/mix/v3_test/cues
python3 audio/mix.py _work/align/timeline.json _work/align/vo_en.wav - _work/mix/v3_test/cues _work/mix/v3_test \
    $(python3 -c "import sys;sys.path.insert(0,'audio');import cues;print(' '.join(cues.MIX_ARGS))")
python3 analysis/refmirror/snd_env.py ours_v3test _work/review/snd_v3/env/ours_v3test.npz --stems _work/mix/v3_test
python3 analysis/refmirror/snd_compare.py _work/review/snd_v3/env/ours_v2r1.npz _work/review/snd_v3/env/ours_v3test.npz
python3 tools/sound_ab.py _work/mix/final_v2 _work/mix/v3_test _work/mix/v3_test/excerpts --match-voice
```
- Quick checks: `mix.py ... --t0 S --t1 S` renders a window (the music map's fitted offsets and the layer curves are now
  shifted into the window; before, the score failed in windows and mix.py fell back to its placeholder drone).
- Plots: `python3 analysis/refmirror/snd_plot.py OUT.png T0 T1 ours:_work/mix/v3_test --cues _work/mix/v3_test/cues`
  (voice / music / SFX levels rel the voice, cue ticks, music events, lines, bed spectrogram; `ref:<name>` for a
  reference stretch). Study plots in `_work/review/snd_v3/plots/`.
- The reference study (voice and bed separated with sherpa-onnx UVR MDX-NET Voc_FT): stadium whole, the other four in
  stretches (`_work/review/snd_v3/ref/sep_win.sh`: hooks, cards, reveals, climaxes, 13 min in all; the whole films
  were too heavy next to a render). `snd_env.py` (K-weighted loudness, bands, onsets) -> `snd_study.py` (per-film
  numbers) -> `snd_compare.py` (pooled table). Envelopes in `_work/review/snd_v3/env*/` (kept); the decoded reference
  mixes and stadium's separated stems were deleted (2.2 GB; `ref/sep_all.sh` re-makes them, about 1 s per second of audio
  on 2 threads); the stretches' stems stay in `_work/review/snd_v3/ref/win/<film>_<t0>/`.

### Sound v3: what the references do, and the rework
The owner: the SFX and music need rework, taking inspiration from how the references build tension. Measured on the five
references (separated beds), what builds their tension is not loudness and not cutting the bed:
- **The bed is continuous and steady** under the narration: 3 s short-term p10 / p50 / p90 -17.4 / -13.0 / -9.1 LU rel
  the voice, a loudness range of 9.3 LU; it **rises in the narration's pauses** (-14.2 under speech, -10.4 in pauses).
  v2 r1 was choppy instead: -20.5 / -14.4 / -5.1, range 17.7 (24 silences or dips, 95 pre-hit suck-outs, 44 swells),
  and it did not rise in pauses (-15.9 / -15.0).
- **It is dark and heavy**: 87 % of its energy under 250 Hz, the 20-60 Hz band 8.8 dB and 60-250 Hz 6.5 dB over 250 Hz-1
  kHz (v2 r1: 70 %, +1.7 / +2.0): sub drones, not mid-range pads.
- **Hits are punctuation** on the running bed: 2.7 a minute, peak 4 LU under the voice, decay to -10 dB in 1.4 s, a
  small suck-out before them (2.7 dB). **Drop-outs are short** (0.5 s, 1 a minute), right before a turn.
- **Few SFX**: 18 bed onsets a minute, 0.6 strong ones (v2 r1: 38 and 5.7, from 618 one-shots).
- **Rule cards**: the bed drops about 7 dB 1-1.5 s before "Rule number", the card's hit lands with the words, a second
  peak 1.5-2 s later (the stamp / the number), then the new act's music.
- **Their loudness range comes from the narrator**, not the bed: stadium's separated voice alone has LRA 5.4 (ours 2.4,
  raw `vo_en.wav` 2.5); stadium's voice over our bed measures LRA 5.2, our voice over stadium's bed 2.3. Every mix peak
  over +4.5 LU in the references is the narrator's emphasis after a pause (bed at -10 LU there). With our voice fixed,
  the mix's range can only come from the bed, which the references keep steady: see the table.

What changed (all in the pipeline, rebuilt from `film_events.json`):
- `audio/cues.py` `sfx_v3()`: the HUD / edit sounds go (ui_pop, diagram_pop, chalk_draw, glint, flash_hit, glass_thud, the
  cards' lipstick write-ons and statement squeaks, the header-clock glitches), repeated gestures keep one sound each
  (`THIN`: lace, candy, tape, taps, cloth, creaks, flashlight, breaths, whooshes), faint breaths go; the cards keep the
  towel's whip, the card's hit and the numeral's stamp (+2 dB); the pre-hit suck-out stays only on real hits (stamps,
  thumps, foley lose the `hit` flag). One-shots in the cue sheet: 618 -> 468 (40 a minute; footsteps, keys, gate,
  bells, the phone, the candy and the towel stay on their frames).
- **Six plan sounds had no recipe and were never in the mix** (`mix.py` logged them as skipped): `towel_whip`,
  `lipstick_stamp`, `number_thump`, `ring_tick`, `rubber_stamp`, `tape_rewind`, i.e. every rule card's stamp, the giant
  numbers, Tess's count ticks, the 14 YEARS / CANCELED stamps and the loop resets. `audio/sfx_mirror.py` now has them.
- `music_v3()`: nine true silences (`KEEP_SILENCES`: the click 142.09, time stopping 341.53, the deepest before the real
  bell 533.18, before her foot 603.91, the foot hanging 626.4-628.18, the glass dark 628.7, Mom's pause 661.64, the last
  click 688.05, the end); every other plan silence that ends in a hit becomes a 0.5 s hole right before it (`DROP_LEN`,
  the score's buses -10 dB, reverb tails kept); the rest -5 dB dips. A 0.6 s hole before each rule card with its riser
  stopping there (`CARD_GAP`, risers at level 0.6, were 0.9 and ended on the card). Risers into the head turn, "You have
  it", her face (283.77, 478.28) and the last sting; the plan risers written with their start time and review round 1's
  two risers (they ended 5-7 s before their silences) now end where they should (`RISER_FIX`). Swells 44 -> 25 (only the
  builds, 9 s apart; tracks lift 5 dB at a swell, was 9). The score's pre-hit duck scaled 0.7 (`PRE_DUCK`).
- The act shape: `ARC` (the music as heard under the narration, LU rel the voice, per act: hushed arrival -17, the game
  -16 to -11.5 into card 1, rule 2's wish -11.5 to -10.5, the too-normal dawn -18, the memory -19.5, the build to the
  bell -13 to -10, the climax -9.5 to -8.5, the ending -18 rising to -11.5 into the phone). `mix.py --steer 0.85`
  steers the score to it (median of the 1 s level over 5 s, held across holes, risers, silences and cards) and replaces
  the two-way leveler, which lifted every quiet passage. The score's own intensity slope 16 -> 9 dB.
- Weight: the drones (synth sub on the key root, contrabass and celli) at 0 dB under every act but the dawn, the memory and
  the warm half of the ending (were -5), the sub +4 dB (`SUB_DB`), `--tilt v3` (the references' octave balance: 63 Hz up
  to +4 dB, a 1.4-1.9 dB cut at 250-500 Hz).
- `MIX_ARGS`: -14 LUFS (`--master-lufs`, was -16), true peak <= -1 dBTP (`--tp-max -1.0`, measured -1.2), the bed up under
  the voice and rising in the pauses (`--duck 4` with the arc 4 dB over it), the ambience beds -3 dB and the foley -1.5
  dB under the music, the bed bus limited to -4 dBTP before the voice joins (`--bed-ceiling`: the big hits had the master
  limiter take 6 dB and the narration with it), hits' punch +4 dB to -2.5 dBTP (was +6 to -1). The voice chain's own
  true-peak limiter is back at v2's range (`--voice-plr 12`, r1 13: set for -16 LUFS, at -14 it left the plosives to the
  master limiter). The narration itself, its timing and its line FX are unchanged.

Measured (`snd_compare.py`; references: whole mixes for the mix rows, the separated stretches pooled for the bed rows;
"rel voice" = LU relative to the narration's integrated loudness; v3 = `_work/mix/v3_test`):

| measure | v2 r1 (`final_v2`) | v3 test | references |
|---|---|---|---|
| mix integrated / true peak | -16.05 LUFS / -1.7 dBTP | -14.04 LUFS / -1.2 dBTP | -14.4 .. -17.2 LUFS |
| mix LRA (EBU-style) | 3.0 | 2.4 | 3.5 .. 5.6 (the narrator's own range, see above) |
| mix momentary max over integrated | +5.3 | +4.9 (the narration's own peak; hits stay under it) | +6.5 .. +8.8 |
| master limiter max / time over 1 dB | 5.6 dB / 0.35 % | 4.0 dB / 0.32 % | |
| mix drop-outs a minute (critic's measure) | 1.71 | 0.86 | 0.14 .. 1.85 |
| bed integrated, rel voice | -8.2 | -10.7 | -11.6 |
| bed short-term p10 / p50 / p90 | -20.5 / -14.4 / -5.1 | -17.4 / -13.0 / -7.6 | -17.4 / -13.0 / -9.1 |
| bed loudness range | 17.7 | 10.8 | 9.3 |
| bed under speech / in pauses | -15.9 / -15.0 | -13.8 / -12.0 | -14.2 / -10.4 |
| voice over bed at 1-4 kHz in speech, p10 / p50 | 7.4 / 23.7 dB | 9.8 / 23.4 dB | 9.2 / 20.8 dB |
| bed swells a minute | 2.3 | 1.1 | 1.9 |
| bed drop-outs a minute, length p50 | 2.8, 1.3 s | 1.5, 1.0 s (9 true silences of 1.15-1.8 s) | 1.0, 0.5 s |
| rule card: bed at -0.5 / 0 / +0.5 / +2 s from "Rule" | -0.6 / -4.3 / -10.2 / -17.3 | -10.0 / -7.4 / -5.6 / -14.5 | -10.8 / -7.0 / -7.7 / -15.1 (stadium) |
| bed onsets a minute (strong) | 38.1 (5.7) | 42.9 (6.1) | 18.4 (0.6) |
| bed under 250 Hz; 20-60 / 60-250 Hz over 250 Hz-1 kHz | 70 %; +1.7 / +2.0 dB | 80 %; +4.4 / +3.5 dB | 87 %; +8.8 / +6.5 dB |

Not met, and why: the mix's loudness range and momentary max (the references' come from their narrator: with our evenly
read narration fixed, a steady bed gives 2.3-2.5 LU; review round 1's 3.0 came from a choppy bed peaking 5 LU under the
voice, which the references never do; riding the narration -1.5 dB in the dawn / memory / ending and +1 dB in the climax
would add about 1 LU, if the owner allows touching the voice's level); the bed's onsets (the cut UI sounds were quiet
or never rendered; what remains is foley on the picture's actions, 84 footsteps, the ambience beds' birds and crickets
and the music's own notes); the sub weight is half way (more ate the true-peak headroom at -14 LUFS).
Before / after excerpts (voice-matched A/B, 10 moments): `_work/mix/v3_test/excerpts/` with `README.txt`.

## 4. Deliver (English only)
```
bash tools/deliver.sh _work/picture/picture.mp4 _work/mix/final/mix.wav _work/deliver
```
- `..._MASTER_1440p60.mov`: the picture stream-copied with the 24-bit PCM mix.
- `parts/...mov.001...`: the master in 390 MB pieces, with `JOIN.txt` (7-Zip or `copy /b`, SHA256).
- `..._EN_1440p60_HEVC.mp4`: one file under 400 MiB (HEVC 4 Mb/s, AAC 160k).
The file names still carry v1's `If_An_Eighth_Step_Appears` base (`B=` in `tools/deliver.sh`); rename for the v2 title
if wanted. The picture is kept.

## 5. What film.py does (v2, for the next builder)
- **One `Built` per shot** (LRU of 4): `sets.build_shot(shot)` (room3d views, bokeh plates behind close-ups, the card's
  live `bg`, the TYPE / DIAGRAM `plate`, both SPLIT panels, the light arc `arc_fx`) + one `characters.CharRig` layer per
  cast entry + the DOC paper object (`ui_v2.doc_layer`) + `make_cam(shot)`.
- **Grades**: the shot's v2 look (`night_v2 ... ending_v2`); rule cards take the grade of their background world. The cast
  is never dimmed. Close-ups of people get half bloom (the white fear eyes glowed under full bloom). `LIGHT_TRIM` lifts
  OURS / STAIRS before 140 s and the ending (the preview measured them under the arc); `SAT_LIFT` 1.06 outside the climax.
- **Staging the cast** (`stage`, `place`): the plan's `at` are first guesses, so
  - kneels and sits become acting clips; a straight-on sit turns three-quarter (it read as standing);
  - on the other side, seated Noah / the Queen / you sit on Noah's mattress (feet on the floor in front of it, sizes from
    the room's 3D camera) in the `queen_3s` and `master` views; H2's `sit_beside` becomes a `glide_sit` from the stairs'
    foot into her seat;
  - people sitting on our floor (the ending) drop by a shin;
  - a standing person's size stays within 0.75-1.33x of what the room's camera gives at their feet;
  - the section's small figures stand on its treads at 1.7x the plan's size, in front of the cutaway;
  - depth: just in front of the distance band that holds the floor under the feet (or the nearest anchor on the stairs);
    busts, hands, feet and OTS figures (feet below the frame) in front of the whole room; the DOF focus follows the
    subject;
  - acts that start after the shot ends are dropped (a not-yet-running clip still wrote its rest pose: S418's fist was
    open for the whole shot); a bust's `tie_loop` becomes a small head-down (the head left the frame).
- **Per-shot fixes** (`SEAT`, `EXTRA_CHARS`): Tess in the THEIRS doorway (S226, S227, S232, S295); H1's Queen framed in the
  doorway (S190); the loose arm through the towel dropped (S173, the set presses the fingertips through); grown Noah big
  enough to meet the top rail (S372, S373); the knot hands for the 14 YEARS echo (S281); the tape loop sliding off the
  grown fingers (S361); your and Tess's reflections in the glass (S067, S078).
- **Reflections and glass**: `reflection` entries are drawn mirrored, faint and cool, clipped to the glass (or the phone
  screen) and behind the lipstick; a `hands` reflection also draws the real hand; `in_glass` / `through_glass` /
  `inside` entries are clipped; the tiny Queen of H10 stands on the phone's 8th line.
- **SPLIT** panels that replay a film time (the loop twins) draw the source shot's cast in their half; **MONTAGE** tiles
  render the sill at each tile's source time (that moment's props, OURS or climax look).
- **Camera** (review round 1): merged shots move on one `PathCam` (monotone cubic through every key under a glide time warp:
  alive at the cut, no stop at the keys, no jerk); two-key linear pushes are extrapolated 0.5 s each way; the word beats are
  eased push accelerations (`cam.accel`); the only snaps are the hits at 143.29, 605.21 and 690.19; the uniform post push only
  on the holds. **Travelling shots** (`cam3`): `campath_of(sh)` (room3d `CamPath3`) moves the 3D camera through the room;
  `_dyn_layers` rebuilds the view for each frame's camera (`sets_v2.MOVE`; the room drawn as live bands from baked plane
  textures, `Scene3.live_bands` / `TexCache`; a plane that reaches behind the lens is always filled from its texture through
  its visible polygon) and stands the cast at world points (`_world_fn`: `w`, named anchors, Noah's bunk seats, the plan's
  screen point cast onto the floor of the view it was framed in), nearer people in front of farther ones; hands and busts are
  pinned to the glass or a plane. One blocking chart for the THEIRS bunk 382-500 s (`bunk_chart`).
- **Review round 2** (continuity and smoothness): 2D shots can move figures in depth (`path2d` [[t, x, y_feet, h], ...],
  monotone cubic: the walk to the porch, the caretaker track, the climb); lying figures are laid along their mattress or the
  floor from world points (`lie`, `floor`: no bed drawn); an explicit `_depth` wins over the room placement, `front` keeps a
  figure in front of the near band; POV / disembodied hands in travelling shots sit in front of the room (depth 0.32);
  a person or plane that the travelling camera comes near fades out over 0.2-0.5 m (Euclidean distance to the feet, hips and
  head, never the view depth) instead of filling the lens; the 2D dolly is capped (`engine/scene.py`: a near layer's
  distance never drops under 0.42 of its rest distance: the taped hand used to blow up). `CamPath3` re-times its keys with
  `ArcBlend` (even travelled speed blended with the keyed timing, so a travelling shot never stops at a key; `arc: 0` in a
  merge keeps exact key times for a hit). New transition `pan` (0.45 s whip pan, horizontal motion blur, `pan_dir`).
  A plane with any corner nearer than the camera's near plane (5 cm) is filled from its baked texture through its visible
  polygon (`engine/room3d.draw_plane`; the vector path through a nearly singular homography drew S072's floor dark for one
  frame at 171.317). Grown Noah's CEDAR LAKE print is drawn at every detail level, stretched over his chest. The light
  arc's trims (`sets_v2.arc_fx`) ease over 1.2 s round their times, and the dawn_break bulb dips / red-leak stutter ease
  slot to slot (they stepped: one-frame exposure pops inside shots).
- **Per-shot overrides** are keyed by a film time inside the shot (`SEAT_T`, `EXTRA_CHARS_T`, `REPLACE_CHARS_T`; shot ids
  change when shots merge); `characters.CLIP_ORIGIN` likewise.
- **Transitions**: `cut`; `pan` (review round 2, above); `flow` (review round 1: 0.5 s travel dissolve between two places of one move, the outgoing
  picture accelerating into the shot's `flow` point; the rule cards enter on it); `glint` (ui_v2); `white` (3-frame flash);
  `glitch` (2 frames of static, RGB split and a light pop); `rewind` (ui_v2 tear + back-scrub); `sepia` (review round 1: a 0.45 s
  paper dissolve, 0.2 s before the cut and 0.25 s after, `paper_dissolve`);
  `smear` (the card's wipe carried over, ui_v2); `black`; in-shot `fx_post` white / glitch / static / rewind / pixel_sort.
- **HUD**: `ui_v2.UI.hud` (captions, header, chips, Tess's ring badge and giant numbers, tags, red X, labels, diagrams
  D1-D10, documents' marks, type beats, the kinetic title, the seven mirror rule cards, the phone, teasers), then
  `UI.frame_fx` (RGB split, rewind tear, pixel sort).

## 6. Review round 1 measurements
- Plan (`plan/validate.py`): 449 -> 314 shots, 26.8 cuts/min, shot p50 1.84 s; 72 merged shots from 182 old ones, 23 travelling
  shots, 21 flow joins; jump cuts 1.3 % (v2 18.5 %), world switches 5.1 /min (v2 11), no memory run under 2.5 s, 3 snaps.
- Motion (`tools/motion_metrics.py`, the critic's 60 fps rule) on the six most motion-heavy minutes
  (`_work/review/v2_r1/motion_check_*.mp4`, 480x270 60 fps): 167 spikes and 469 jerks against the critic's 282 and 681 on v2;
  what remains is mostly deliberate (glitches, white flashes, stamps, the loop rewinds, giant numbers) and the 0.45-0.5 s
  transition blends. The travelling shots' room composite scans clean (`tools/dyn_flicker.py`).
- Mix (`_work/mix/final_v2`; sound v3's test and its numbers are in section 3): -16.05 LUFS, -1.7 dBTP, limiter max 5.6 dB (v2 6.1), glue p95 0.6 dB; the critic's envelope tool:
  LRA 3.0 (v2 2.4, refs 4.2-5.4), momentary max +6.6 LU (v2 +5.3, refs +7.6-8.4), short-term p95 +1.6 (v2 +1.2, refs
  +2.0-2.4); 618 one-shots (v2 776), UI / edit sounds about 220 -> 73, five real silences.
- Preview: `_work/preview_v2/preview.mp4` (640x360, 30 fps, the final_v2 mix), contact sheets `contact_1fps_0.jpg` (0-350 s)
  and `contact_1fps_1.jpg` (350-700 s); v2's preview kept as `preview_v2_before_r1.mp4`.

## 7. Measured on the v2 preview before review round 1 (`_work/preview_v2/measure_preview.json`)
| measure | v2 preview | brief |
|---|---|---|
| cuts / min, first 30 s | 39.0, 25 | 36-40, 22-24 |
| shot p10 / p50 / p90 | 0.67 / 1.43 / 2.30 s | 0.65 / 1.5 / 2.5 |
| shots over 3 s (detected) | 5.0 % | <= 4 % |
| white flash cuts detected | 1.71 / min | 2-3 (flash + glitch) |
| frames luma < 60 / < 40 | 5.1 / 1.3 % | <= 10 / <= 3 % |
| colourfulness p50 | 46.2 | >= 45 |
| contrast p95-p5 / luma std | 125 / 38 | >= 135 / >= 45 |
| edge density p50 | .031 | >= .035 |
| red share 490-560 / 560-630 | 7.5 / 19.0 % (16.3 % before the saturation lift, which now skips the climax) | 3-8 / 13-18 % |
| push median / p75 | 2.3 / 3.1 %/s | ~3.0 / ~5.5 |
| subject motion share | 0.20 | >= 0.32 |
| per-shot frame energy p50 / near-static shots | 0.58 / 1.1 % | >= 0.8 / <= 5 % |
| luma p50 by tenth | 91 93 90 100 146 144 130 98 61 92 | 95-110 95-110 85-100 90-105 135-150 130-145 120-135 95-110 60-75 90-100 |
