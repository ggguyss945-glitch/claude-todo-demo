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
python3 film.py --sheet W/tests/film/sheet_a --range 0 127 --cols 6 --tile 320     # mid-shot stills as contact sheets (frames at 960x540)
python3 film.py --sheet W/tests/film/sheet_b --range 127 254 --cols 6 --tile 320
python3 film.py --bench 40 --size 2560x1440 --threads 1                     # full-size speed, one process
python3 film.py --bench 1 --shots 217,218,219,220,228,237,206,221,234,122,187 --size 2560x1440 --threads 1   # chosen shots
```
- 254 shots, median 2.41 s (p10 1.37, p90 3.93, shortest 0.58).
- Contact sheets: `W/tests/film/sheet_a_00..03.jpg` (shots 0-126) and `sheet_b_00..03.jpg` (127-253), 36 shots a sheet, each tile labelled `index kind time`. Run the two halves as two processes (about 1.5 min each).
- The bench writes `W/tests/film/speed_<size>.json` (or `speed_shots_<size>.json` with `--shots`).
- `film.py --cues` writes:
  - `sfx_cues.json`: `{t, name, gain_db, pan, space, params}` (742 events).
  - `music_cues.json`: `{duration, intensity, events}` (121 events).
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
- **The preview** is `W/preview/preview.mp4`: 640x360, 30 fps, 642.7 s, with the voiceover. It is `film.mp4` of the preview render renamed; the slices and `picture.mp4` were deleted.
- **The 5 s full-mode test** is `W/tests/render5_553.5-558.5_2560.mp4` (the app screen cutting to the 3:41 photo): 2560x1440, 60 fps, 300 frames, 3 workers, end to end in 51 s while the mix was running; its audio offset checks to 553.50 s.

## Speed (police budget: 0.6 s/frame at 2560x1440, one process, one OpenCV thread)
- `film.py --bench 40` (160 frames over 40 shots, shared machine with the mix running): mean 0.38 s/frame including cold caches, 0.28 s steady. The heaviest shot is 0.45 s steady (shot 221, the full-screen app over the hall).
- The heaviest shots (`--bench 1 --shots ...`, steady): doorway 122 (memory, door open) 0.54 s, phone 221 0.44 s, doorway 234 0.39 s, keys 237 0.29 s, the 3:41 photo shots 0.16-0.19 s, the latch insert 0.15 s. The first frame of a shot can take up to 1.5-2.4 s while its static layers are baked.
- The doorway's dolly is capped at 2 %/s: a faster optical zoom re-blurs its frame-sized walls every frame (0.74 s).
- The photo shots bake their crop into one cached layer (`photo341_<crop>`), so the camera never zooms optically past about 1.3.
- The full film is 38,560 frames at 60 fps. Three workers render it in about 1.5 h on a quiet machine.

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

**Outputs** in `W/mix/final/`: `mix.wav` (= `mix_en.wav`, 48 kHz 24-bit stereo, 643.22 s), `stems/{voice_en,music,sfx}.wav` (float, final gain, before the limiter), `mix_report.json`, `mix.log`, `measure.json` / `measure.txt`, `measure_cues.json` (every one-shot cue re-rendered and checked), `measure_plot.png` (loudness map: voice, music, SFX, silences, hits, rule cards). The preview with the mix is `W/preview/preview_mix.mp4` (640x360, 30 fps, 642.73 s, AAC 320k stereo).

**Measured** (`measure_mix.py`, BS.1770 per-channel K-weighting; "rel voice" = against the voice stem's integrated loudness):

| | result | target |
|---|---|---|
| Mix integrated / true peak | -14.03 LUFS / -1.70 dBTP (preview AAC: -14.0 / -1.5) | -14, <= -1.0 |
| Voice vs mix | -0.05 LU | within 0.5 |
| Voice minus bed (music + SFX) during speech, 400 ms blocks | p5 7.5 LU, median 17.5; under 3 LU in 1.3 % of speech, under 0 LU in 0.4 % (word onsets under swell peaks and reveal hits) | voice always clear |
| Same in the 1-4 kHz intelligibility band | p5 10.7 dB, median 24.9 | |
| Music outside the 21 authored silences (+4 s re-entry) | above voice -32 LU 100 %, above -26 LU 96.7 %; no holes | under the voice the whole time |
| Silences | 21 (1.96/min), 17.4 dB deep (median) | 1.5/min, 15 dB |
| Bed integrated / 3 s p10-p50-p90 / LRA | -13.8 LU / -21.7, -16.1, -11.0 / 12.2 LU | -13 +- 1 / p50 -16 / 13-14 |
| Bed by quarter | -15.3 / -16.1 / -13.5 / -11.6 LU; loudest 10 s at 633 s | Q2 calmest, end loudest |
| Bed spectrum < 250 Hz / 250 Hz-4 kHz / > 4 kHz | 71 / 28 / 0.7 % | 70 / 29 / <= 2 % |
| Hits | 3.45/min; peak median -4.8 LU, max +3.2 LU rel voice | 3/min; +2 / +9 |
| One-shot SFX cues checked | 275: 0 silent, 0 failed, 7 flags left (below) | |

**Cue flags left** (all looked at): the doorbell button click under its own ding-dong (37.0 s) and two doorbell-speaker clicks under the driver's first syllable (205.0, 347.1 s), all texture, three all-night box knocks in the hall that keep only 15-18 dB above 300 Hz (486-496 s; the knocks around them read), and the sunrise tape peel's transient 70 ms after its cue (no picture sync point; the cue was moved 70 ms earlier).
