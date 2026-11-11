# "If The Queen Of Spades Appears In Your Mirror... DON'T MAKE A WISH" (v2): build and delivery

Everything runs from this folder (`film/`). Work files go to `_work/` (gitignored). The brief is `DIRECTION_V2.md`; the plan
is `plan/shots.json` (314 shots after review round 1's flow pass: 449 written, merged into continuous moves, `PLAN_V2.md` section 0); the picture is assembled by `film.py` from `sets.py` + `sets_v2.py`
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
python3 tools/dyn_flicker.py [ids]                               # flicker scan of the travelling (cam3) shots' room layers
python3 tools/motion_metrics.py CLIP.mp4 T0 [--json OUT]         # the critic's 60 fps spike / jerk measure on a clip
python3 render.py --stills 131.5,605.3 --size 960x540            # -> _work/tests/render/still_*.jpg
python3 render.py --clip 600 606 --size 960x540 --audio _work/mix/final/mix.wav
```
Low-res preview of the whole film with sound (8 min with 2 workers), then its measurements against the brief (5 min; the
decoded frames are deleted afterwards unless `--keep`):
```
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
```
python3 film.py --events
python3 audio/cues.py --events _work/align/film_events.json --out _work/cues
python3 audio/mix.py _work/align/timeline.json _work/align/vo_en.wav - _work/cues _work/mix/final_v2 \
    $(python3 -c "import sys;sys.path.insert(0,'audio');import cues;print(' '.join(cues.MIX_ARGS))")
python3 audio/measure_mix.py _work/mix/final_v2 --cues _work/cues
```
The mix takes about 10 min and 7 GB of memory: run it when no render is running.
Review round 1 (critic M1-M4), in `audio/cues.py`: only five real silences stay (533.18 H4, 603.91 H7, 628.7 glass dark,
661.64 Mom's pause, the end); the other plan silences are -6 dB thinned dips of the score (`KEEP_SILENCES`, `SIL_DIP_DB`);
`declutter()` thins the UI / edit sounds (no glint whooshes, ring ticks only on the giant numbers, one soft gesture per
diagram, flash hits only on the real hits, glitches only in the hook's flash-forwards; about 220 -> 73); the music map changes
cue only on a card or on picture travel (one lullaby for rule 4, one build for rule 5 into the bell, one theme for the ending),
the tracks bus ramps from rule 5's card to the bell and risers lead into the bell and her foot (`EXTRA_MUSIC`); `MIX_ARGS`
deliver at -16 LUFS (`--master-lufs`), with the glue eased (`--glue-max 1.5`, ratio 1.5), a lighter duck under the voice
(`--duck 2.5`), a louder bed (`--bed-rel -9.5 --bed-p50 -12`) and freer hits (`--hit-duck 3 --score-hits-db 6 --voice-plr 13`).

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
- **Per-shot overrides** are keyed by a film time inside the shot (`SEAT_T`, `EXTRA_CHARS_T`, `REPLACE_CHARS_T`; shot ids
  change when shots merge); `characters.CLIP_ORIGIN` likewise.
- **Transitions**: `cut`; `flow` (review round 1: 0.5 s travel dissolve between two places of one move, the outgoing
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
- Mix (`_work/mix/final_v2`): -16.05 LUFS, -1.7 dBTP, limiter max 5.6 dB (v2 6.1), glue p95 0.6 dB; the critic's envelope tool:
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
