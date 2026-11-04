# "If An Eighth Step Appears On Your Mirror... WIPE THE GLASS CLEAN": build and delivery

Everything runs from this folder (`film/`). Work files go to `_work/` (gitignored). The plan is `plan/shots.json`
(PLAN.md); the picture is assembled by `film.py` from `sets.py` (SETS.md) and `characters.py` (CAST.md) with the
engine in `engine/`; the sound is built in `audio/` from `plan/sound_plan.json` plus the picture's own events.

Output: 2560x1440, 60 fps, 700.0 s (42,000 frames), English narration and captions.

## 0. Inputs that must exist
- `_work/align/timeline.json`, `_work/align/asr_cache.json`, `_work/align/vo_en.wav` (the narration on the film timeline)
- the owner's Epidemic files in `_work/samples/epidemic/{sfx,music}` (licensed; never copy them out of `_work`)

## 1. Checks before the long render (minutes)
```
python3 film.py --sheet _work/film/sheet                 # mid-shot still of every shot, 960x540 -> 8 contact sheets
python3 film.py --sheet _work/film/chk S059@131.5 S276   # single shots, optional @time
python3 film.py --bench S064 S122                        # full-size s/frame (one OpenCV thread, as in a worker)
python3 render.py --stills 131.5,605.3 --size 960x540    # -> _work/tests/render/still_*.jpg
python3 render.py --clip 600 606 --size 960x540 --audio _work/mix/draft/mix.wav
```
Low-res preview of the whole film with sound (about 20 min with 2 workers):
```
python3 render.py --size 640x360 --fps 30 --workers 2 --crf 23 --out _work/preview \
    --audio _work/mix/draft/mix.wav --name preview.mp4
```

## 2. Final picture (do not run while teammates render)
```
python3 render.py --workers 3                             # -> _work/picture/picture.mp4 (2560x1440, 60 fps)
```
- 3 worker processes, each one contiguous slice, libx264 crf 16 preset faster, 1 OpenCV thread per worker and 2 x264
  threads; the slices join with a stream copy.
- Progress: `_work/picture/progress_00.json` ... `_02.json` (`{done, total, fps}`); `python3 tools/progress_page.py _work
  _work/page/index.html` turns them into the counter page (it also reads `_work/status.json`).
- Resume: finished slices leave `slice_NN.mp4.done` and are skipped on a re-run. Delete `_work/picture/` to start over.
- Measured speed: mean 0.24 s per warm frame per process at 2560x1440 (median 0.22, all 317 shots; heaviest shot
  S253 0.43 s). The 5 s end-to-end test (601-606 s, the red climax, 3 workers) ran at 3.2-3.8 frames/s per worker, about
  10.4 frames/s in total, so the full 42,000 frames take about 70 min; plan on 75-90 min with encoding and the concat.
- Add `--audio _work/mix/final/mix.wav` to also write `_work/picture/film.mp4` with the final mix muxed in.

## 3. Final mix, synced to the picture
`film.py --events` writes `_work/align/film_events.json`: the actual cut times, every on-screen action the picture
performs (acting clips: steps, grabs, taps, wrapper, lace, cloth...; HUD: tag pops, red X, labels, the time card flip,
the rule cards' glitch / lipstick title / finger wipe, Mom's message bubbles, the call pickup, Tess's countdown ticks)
matched to the plan's cue ids (retimed where the picture differs), new cues where the plan has none, plan walk cues
replaced by the picture's own footsteps (`drop`), and the picture's hit times (`hits`: camera hits, punch-ins, tags,
red X, cards). `actions` lists every action with its time for checking.
```
python3 film.py --events
python3 audio/cues.py --events _work/align/film_events.json --out _work/cues
python3 audio/mix.py _work/align/timeline.json _work/align/vo_en.wav - _work/cues _work/mix/final \
    $(python3 -c "import sys;sys.path.insert(0,'audio');import cues;print(' '.join(cues.MIX_ARGS))")
python3 audio/measure_mix.py _work/mix/final --cues _work/cues
```
The mix takes about 10 min and 7 GB of memory: run it when no render is running.

## 4. Deliver (English only)
```
bash tools/deliver.sh _work/picture/picture.mp4 _work/mix/final/mix.wav _work/deliver
```
- `If_An_Eighth_Step_Appears_MASTER_1440p60.mov`: the picture stream-copied with the 24-bit PCM mix.
- `parts/...mov.001...`: the master in 390 MB pieces, with `JOIN.txt` (7-Zip or `copy /b`, SHA256).
- `If_An_Eighth_Step_Appears_EN_1440p60_HEVC.mp4`: one file under 400 MiB (HEVC 4 Mb/s, AAC 160k).
The picture is kept.

## 5. What film.py does (for the next builder)
- One `Built` per shot (LRU of 3): `sets.build_shot(shot)` + one `characters.CharRig` layer per cast entry (body modes at
  their anchor depth, busts / hands at 1.0) + `make_cam(shot)` (plan keys, linear pushes extrapolated 0.5 s each way,
  snaps, hits, handheld for shake >= 8, a 2 %/s post push on inserts and UI).
- Fixes on top of the plan: rule cards keep the neighbouring shot's cast breathing behind the blur; S055 gets you and
  Tess at the mirror, S259 / S260 get grown Noah rising into the bunk and staring at his hands (`EXTRA_CHARS`); grown
  Noah sits on the floor in S058 / S289 / S290 / S304 as the narration says (`PATCH_ACTS`); the old-cabin footprints
  carry over from shot to shot; hands in Tess's beam get a
  warm key (`HAND_FLASH`); the cast is dimmed under the night grades that lift the sets by about a stop (otherwise skin
  blows out); Tess's beam starts at her flashlight hand in body shots (`Beam.override`); the S070 dress glint.
- Transitions: `glitch` (2 frames of static and RGB split), `white` (3-frame flash), `dissolve` (0.3 s centred on the
  cut, both shots rendered), `black`; per-shot `fx_post`; a 0.22 s fade-in at the start.
- HUD: captions (`shots.json captions`), header with the running in-world timecode, Tess's countdown, the 11:57 PM time
  card, command tags, red X, pinned labels projected through the shot camera, the phone (text thread, voicemail list,
  voicemail, calling / connected with a waveform from Mom's real line), the seven lipstick-on-glass rule cards and
  LIKE / SUBSCRIBE. The cards' glass, letters and words are cached sprites (a redrawn card cost 0.4 s per frame).
