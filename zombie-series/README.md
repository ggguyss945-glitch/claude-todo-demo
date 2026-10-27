# Zombie series: drawing engine and series bible

- `engine/lib.js` — SVG drawing library in the Nobody Gets In-like style: hero and zombie rigs, crowds, HUD themes, captions, grades, paper grain.
- `engine/scenes.js` — style frames: character sheet, supermarket (day, night, exterior, close-up), mall, park, POV, motion-graphics cards.
- `tools/render.js` — renders scenes to PNG with Playwright: `NODE_PATH=$(npm root -g) node tools/render.js supermarket_night mall@0`.
- `docs/` — series bible page and the rendered style frames.

## 60-second test pipeline
1. `audio/voice.py <scratch> <voice_dir>` — Kokoro TTS (blend am_puck + am_michael), studio-mic chain, word timings via Parakeet ASR.
2. `audio/timeline.py <voice.json> <timeline.json>` — shots and sound events derived from the voice.
3. `audio/mix.py <scratch> <timeline.json> <voice_dir> <audio_dir>` — synthesized SFX (`audio/sfx.py`), score on GeneralUser GS (`audio/music.py`), ducking, -14 LUFS master.
4. `tools/render_anim.js <timeline.json> <frames_dir> 30 4` — renders `engine/anim.js` frame by frame and keeps `<frames_dir>/progress.json` current.
5. `tools/encode.sh <frames_dir> <mix.wav> <out.mp4>`.

## Live render monitor
`tools/live_monitor.html` is the published render page (db `render/status` + uploaded preview frames). `tools/watch_render.sh <frames_dir>` prints a line each time `progress.json` changes; each line is pushed to the page.
