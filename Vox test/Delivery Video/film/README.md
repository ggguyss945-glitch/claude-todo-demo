# "If A Delivery Driver Rings Your Doorbell At 3 AM... DON'T SIGN FOR IT": film

This film is made the way the police film was ("If A Police Officer Knocks At Midnight...", `film_police_ref.py`). It uses the same engine, cast and set systems, the same shot-list format, the police header, rule cards and captions, the same global look with the red climax ramp, and cue sheets derived from the picture.

All commands run from this folder (`Vox test/Delivery Video/film`). The work dir is `W = film/_work`.

| file | what |
|---|---|
| `film.py` | The shot list (`plan()`), the shot builders `B_<kind>`, captions/header overlay, `escalate()`, global look, cue sheets. The module docstring lists the shot kinds and plan conventions. |
| `film_police_ref.py` | The police film's shot list, kept as the format reference. |
| `characters.py` / `CAST.md` | Cast, acting clips, the driver's smile arc, the box (`BoxActing`), props. |
| `sets.py` / `SETS.md` | Sets (porch / doorbell / peephole / street / hall / upstairs / Lily's room / side yard / doorway), inserts, the app phone. |
| `render.py` | Stills, test clips and the full worker/slice render (defaults to `W`). |
| `engine/` | The 2.5D engine (camera, layers, lenses, grades, HUD). |
| `audio/` | Sound pipeline (the audio teammate's). It reads `W/cues/*.json`. |

## Inputs
- `W/align/timeline.json`: line times for the 286 lines. `W/align/asr_cache.json`: word times. `W/align/vo_en.wav`: the voiceover, 48 kHz, 640.72 s. These are written by `tools/align.py`.
- Script: `../script/lines.py` and `../script/narration_en.txt`.

## The shot list
```
python3 film.py --list                    # every shot (index, start, length, kind) + count / median / p10 / p90
python3 film.py --cues                    # cue sheets -> W/cues/sfx_cues.json, music_cues.json, shots.json
python3 film.py --sheet W/tests/film/a --range 0 126 --cols 6 --tile 320    # mid-shot stills as contact sheets (960x540)
python3 film.py --bench 40 --size 2560x1440 --threads 1                     # full-size speed, one process
python3 film.py --bench 1 --shots 10,41,237 --size 2560x1440 --threads 1   # speed of chosen shots
```
- Contact sheets go to the prefix you pass, e.g. `_work/tests/film/a_00.jpg`. The bench writes `W/tests/film/speed_<size>.json`.
- `film.py --cues` writes:
  - `sfx_cues.json`: `{t, name, gain_db, pan, space, params}`.
  - `music_cues.json`: `{duration, intensity, events}`.
  - `shots.json`: the cut list, `{i, t0, t1, kind, space, loc, era, cut}`, for the sound team.

## Rendering
```
python3 render.py --stills 12.5,151.9,371.0 --size 960x540                  # -> W/tests/render/still_*.jpg
python3 render.py --clip 370 380 --size 960x540 --audio W/align/vo_en.wav   # one process test clip
python3 render.py --workers 3 --audio <mix.wav>                             # FULL: 2560x1440, 60 fps -> W/picture/picture.mp4 + film.mp4
python3 render.py --workers 3 --from_ 100 --to 105 --out W/tests/render5    # a 5 s full-mode test (slices + join)
python3 render.py --size 640x360 --fps 30 --workers 2 --out W/preview --audio W/align/vo_en.wav   # low-res preview
```
- **Full mode** splits the range into contiguous slices, one per worker process, each with one OpenCV thread. Each slice is encoded with libx264 at crf 16, preset faster.
- **Finished slices** get a `.done` marker. A re-run skips them, so delete the markers (and the slices) before rendering a changed film into the same `--out`.
- **The preview** `W/preview/preview.mp4` is the full-mode output (`film.mp4`) renamed. Its audio is the voiceover only, until the mix exists.

## Speed (police budget: 0.6 s/frame at 2560x1440, one process, one OpenCV thread)
- `film.py --bench 40`: mean 0.37 s/frame including cold caches, 0.27 s steady.
- The heaviest shots, measured steady:
  - the sunrise keys: about 0.6 s on a busy machine, 0.38 s alone;
  - the doorway views: 0.47-0.54 s;
  - the knocking-box close-ups and the wave panels: about 0.4-0.5 s.
- The full film is 38,560 frames at 60 fps. With 3 workers it renders in about 1.5 h.
