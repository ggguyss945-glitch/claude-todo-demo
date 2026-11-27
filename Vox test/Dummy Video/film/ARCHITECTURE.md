# "If A Police Officer Knocks…" v2: architecture contract

v1 (in `../src/`) was rejected by the channel owner. Their verdict, in short:
- The characters are not weird or terrifying. They should act weirdly and creepily, with creepy faces and smiles.
- The animation is bad, boring and slow, nowhere near the references.
- The video lacks music and sound effects. Sound design is vital: tension-building music and SFX on every action, at
  ultra quality and perfectly synced to the picture.
- Most of the video is one doorbell-camera look with the officer standing still and only the mouth moving.
- In the firefighter reference, the doorbell view behaves like a real doorbell camera: when the camera moves, the view
  and the person change the way they would in real life, with smooth, professional animation and action.
- Pace and tone change and build through the references. Colours, gradients and smoothness are on an ultra level there.

v2 is a ground-up rebuild of the visuals and the sound. The story, the script, the captions' look and the narration
(new recording) stay.

## Owner-supplied Epidemic Sound library: the first-choice sound source
The owner downloaded 74 professional SFX and 6 horror music tracks from Epidemic Sound (licensed through their
subscription).
- Files: 48 kHz stereo WAV in `$S/pov2/samples/epidemic/{sfx,music}/`.
- Catalogue: `v2/audio/catalog_epidemic.json`, built by `v2/audio/epidemic_catalog.py`.
  - Each SFX has `serves`: the required SFX names it covers. Together they cover 32 names (knocks, porch and wood
    footsteps, police radio chatter and static, sirens, car doors, idle and pass-bys, locks, chain, keys, mailbox,
    phone ring, busy and vibration, paper, breathing, heartbeat, tinnitus, whooshes, risers, braams, impacts and
    stingers, sub drops, UI pops, bodycam beep, three suburban night ambiences).
  - Each music track has loudness and brightness curves (every 2 s), tempo, tonal centre and section boundaries.
- Rules:
  - SFX: use the Epidemic recordings first for every name they serve, layered and processed (perspective, reverb,
    variation). Fill the remaining names from the free library (`catalog.json`) or high-quality synthesis:
    `room_tone`, `clock_tick`, `countdown_tick`, `tv_off`, `crowd_whisper`, `typing`, `door_creak`, `glitch`,
    `pen_click`, `phone_pickup`.
  - Music: the backbone of the score is the 6 Epidemic tracks, arranged to the film.
    - Pick track sections by mood (loudness and brightness curves) to follow the intensity curve.
    - Change tracks or sections at scene changes with musical crossfades.
    - Automate true silences and drops before scares.
    - Duck under the voice per AUDIO_SPEC.
    - Layer the Epidemic risers, braams, impacts and sub drops on top at the music events.
  - `score.py` adds recorded-instrument layers (music-box motif, string swells) only where they strengthen the
    tracks. It must not fight their key: tonal centres are in the catalogue.
- Licence: no attribution needed. Never commit these files. The owner must keep the channel connected in their
  Epidemic account.

## References (study them; measure, don't guess)
- `$S/ref2/fire.mp4` (If A Firefighter Knocks…, 8:18): the closest format. It has only about 25 hard cuts; the energy comes
  from continuous motion inside shots: slow push-ins, drifts, vehicles driving through, flashing red/blue light sweeps,
  a fisheye peephole with the face bulging toward the lens, UI tags ("MICROPHONE"), waveform panels, a 911 phone UI and
  rule cards.
- `$S/ref2/hotel.mp4` (Hotel crying, first 9:00) and `$S/ref2/class.mp4` (Class screams, 10:30): shots average 3.4 s and
  4.3 s. They have creepy faces: ashen skin, huge eye whites with tiny pupils, dark eye bags, a too-wide toothy grin with
  tears running, screaming mouths. Backgrounds behind close-ups get a shallow depth-of-field blur. Interiors are richly
  textured. Speech-bubble tags, phone and voicemail screens.
- Contact sheets: `$S/ref2/{fire,hotel,class}_sheet.jpg`, `fire_motion1.jpg`, `fire_motion2.jpg`.
  `$S = /home/user/claude-todo-demo/Vox test/Police Officer Video/v2/_work`

## Inputs
- Script: `../script/lines.py` (`LINES`: 286 entries `L(who, en, ru, pause, fx, pace, tag)`; who = N narrator,
  O officer, Y your voice on the radio, D the double, M mother, F second officer; fx in radio/phone/phone_far) and
  `../script/narration_en.txt`.
- New English narration: `$S/pov2/narration_en_v2.wav` (697.5 s, 48 kHz).
- Timeline (when alignment finishes): `$S/pov2/align/timeline.json`.
  - `duration_en`
  - `lines[{i, who, tag, fx, en, ru, t, end, found_en, ...}]`: `t` and `end` are English line times in seconds.
  - `$S/pov2/align/vo_en.wav` and `vo_ru_dub.wav` (Russian dub already fitted to the English timeline).
- Fonts: `../fonts/MontserratLC-{600,700,800,900}.ttf` (Latin and Cyrillic).
- v1 code `../src/` may be read for ideas (`align.py`, `mix.py` voice-FX logic, `render.py` worker/slice scheme). Its
  drawings are what got rejected; do not reuse them as they are.

## Output
- 2560×1440, 60 fps, English captions (v1 style: small white uppercase, letter-spaced, low in frame, soft shadow) and
  the tiny "HOUSE RULES / RULE n OF 7" header.
- Work directory for renders and audio: `$S/pov2/`. Code lives in this folder (`v2/`). Nothing large goes in git.
- Render speed budget: at most 0.6 s per frame at 2560×1440 in one process (3 worker processes on 4 cores). The full
  41,860 frames must render in about 2.5 h.

## Modules and contracts
All drawing happens in a 1920×1080 design space; the engine scales to the render size. Render size must be
configurable (`set_render_size(w, h)`) so tests can run at 960×540.

### `engine/` (engine agent)
- `engine/core.py`
  - Kept from v1 `../src/look.py`: `col`, `mix`, `Pen` (fill/line/shape/shade/glow/grad/wash), `text`, `wrap`,
    `typeface`, geometry (`smooth`, `poly`, `rect`, `rrect`, `oval`, `inter`/`union`/`minus`).
  - New: easing (`ease_in_out`, `ease_out_cubic`, `ease_out_back`, `spring`), `noise1(t, seed)` (smooth value noise
    for idle and handheld motion), `tex(name)` (cached procedural texture shaders: grunge, fabric, plaster, wood,
    asphalt, paper, skin pores), `Pen.texture(path, name, alpha, blend)`, soft drop shadow, rim light, radial and
    linear gradient helpers.
- `engine/camera.py`
  - `Cam(keys=[(t, x, y, zoom, roll), ...], ease='in_out', shake=0.0, shake_hz=0.6, seed=0)`; `cam.at(t)` returns a
    state.
  - Helpers: `push_in`, `drift`, `pan`, `whip`, `snap_zoom` (punch-in), `handheld`, `hold`.
- `engine/scene.py`
  - `Layer(depth, draw, name='', blur=None, alpha=1.0)`.
  - `draw(pen, t)` draws in design coordinates as seen at reference depth 1.0.
  - Parallax: a layer at depth d moves and scales with the camera by a factor of 1/d. DOF blur grows with
    `|1/d - 1/focus|`. Blurred layers render at half resolution.
  - `render_frame(layers, cam_state, t, frame_i, focus=1.0, dof=0.0, lens=None, grade=None, post=None)` returns uint8
    RGB at render size.
- `engine/lens.py`
  - Real lens models applied after the layers are composited.
  - `'doorbell'`: equidistant fisheye, about 160° FOV, strong barrel, slight chromatic aberration at the edges,
    low-light noise and a hint of compression blockiness. It also has an IR night mode.
  - `'peephole'`: a circular fisheye in a dark ring.
  - `'lens'`: mild cinematic barrel.
  - Because the lens works on the composited 2.5D scene, camera moves and people moving toward the lens distort the way
    a real doorbell camera does.
- `engine/post.py`
  - `Grade` presets: `night_blue`, `porch_warm`, `interior_dim`, `red_alert`, `phone_dark`, `ir_night`, plus
    `police_flash(t)` red/blue sweeps.
  - Bloom, vignette, film grain, softness, lifted blacks, colour noise.
  - Every look must sit on the references' palette: deep navy nights, warm sodium porch light, desaturated mids, soft
    gradients.
- `engine/hud.py`
  - `caption(cv, text)`, `header(cv, right, corner)`, `rule_card(cv, n, text, t)`, `tag(cv, text, x, y, style)`
    (red/white label like the references' "MICROPHONE"), `speech_bubble`, `waveform_panel`.
  - Phone UI: calling, busy, incoming, connected, voicemail.
  - Doorbell HUD: camera name, live dot, timestamp, motion box, signal and battery.
  - Bodycam HUD.
- `render.py`
  - Worker/slice renderer as in v1 (`../src/render.py`): `--stills`, `--clip t0 t1 --size 960x540`, and a full mode
    with slices encoded by libx264 crf 16 preset faster.
  - It imports the film from `film.py` (`Film(timeline).frame(t, i)`).

### `characters.py` (character agent)
- Cast: `officer` (police cap, uniform, badge, shoulder radio, bodycam), `officer2` (female officer), `double` (looks
  like you but wrong: grey coat, scar on the wrong side, ring on the wrong hand), `you` (hoodie, scar left, ring left),
  `mum` (elderly, curly grey hair, glasses, cardigan).
- Faces are the centrepiece. Creepy features:
  - ashen or pale skin with grey shading, huge eye whites with tiny pupils, dark eye bags, wrinkles and folds;
  - a too-wide toothy grin that grows slowly, an unblinking stare, head tilts, sudden snaps, tears.
- `draw(pen, who, x, y_feet, height, pose)` draws the full body. `draw_bust(pen, who, cx, cy, scale, pose)` draws a
  head-and-shoulders close-up at large scale, with textures and shading at full detail.
- Views: front, 3/4 left and right, profile, back.
- `Acting`: a timeline builder; `acting.at(t)` returns a `Pose`. Clips have easing, overlapping action, breathing,
  blinking and micro head motion.
  - Required clips: `idle`, `stare`, `creep_smile`, `wide_grin`, `head_tilt`, `snap_turn`, `lean_in` (toward the
    lens), `knock` (impact times returned for SFX sync), `talk(intervals)` (mouth shapes from speech timing),
    `radio_to_mouth`, `press_bodycam`, `hold_up(prop)`, `hand_on_glass`, `walk(from, to)` (proper walk cycle),
    `turn_back`, `cry`, `scream`, `nervous_glance`, `twitch(times)`.
  - Every clip that makes a sound returns its SFX event times.

### `sets.py` (sets agent)
- Environment builders return `[Layer]` with depth, plus animated elements: moths around the porch light, a
  flickering bulb, swaying branches, a patrol car driving in or out with a moving light bar, headlight sweeps, police
  flash on walls, curtains, rain or mist where it helps.
- Sets:
  - porch from the doorbell camera (door frame, railing, steps, path, street, houses at depth);
  - porch from the peephole; street wide; patrol car exterior and back-seat window;
  - hallway interior (door, coat hook, mail slot, lamp, photo); kitchen; living-room window;
  - mother's house exterior and room.
- Props (drawable at any scale): police notebook, licence card, complaint sheet, phone, shoulder radio, keys and lock,
  bag contents, the photograph.
- Close-up insert compositions with DOF.

### `film.py` (director agent)
- `Film(timeline)`: the shot list.
  - About 200–260 shots with continuous camera motion inside each one; pace varies with the story.
  - Each shot has layers from `sets`, characters with `Acting`, a `Cam`, lens, grade, focus/DOF and HUD.
- `.frame(t, i)` returns RGB. `.cues()` returns the SFX cue list (`{t, name, gain_db, pan}`) and the music intensity
  and cue sheet derived from the picture: knock impacts, car doors, radio clicks, cuts, whooshes on camera moves, hits
  on reveals, silences before scares.

### `audio/` (audio agents)
- `audio/samples/`: a recorded sample library from permissively licensed sources reachable here (GitHub, PyPI, npm).
  - Only CC0, CC-BY or MIT/BSD; no non-commercial licences. The channel is monetized.
  - `catalog.json` lists each sample's path, category, licence, source and attribution. `ATTRIBUTION.md` holds the
    credits text for the video description.
  - The samples themselves stay in `$S/pov2/samples/`.
- `audio/sfx.py`: `render(name, **params)` returns stereo float32 at 48 kHz.
  - Built from the recorded samples, layered and processed, with high-quality synthesis only where no recording fits.
  - Required names: `knock_door`, `doorbell_chime`, `footsteps_porch`, `footsteps_wood_inside`, `car_pass`,
    `car_idle`, `car_door_open`, `car_door_close`, `siren_far`, `police_radio_squelch`, `radio_click`, `radio_static`,
    `bodycam_beep`, `phone_ring`, `phone_busy`, `phone_vibrate`, `phone_pickup`, `mail_slot`, `paper`, `pen_click`,
    `key_in_lock`, `lock_turn`, `chain_lock`, `door_creak`, `breath`, `heartbeat`, `whoosh` (soft and hard), `riser`,
    `braam`, `impact_hit`, `sub_drop`, `stinger`, `glitch`, `ui_pop` (tags appearing), `typing`, `tinnitus`,
    `ambience_night` (crickets, wind, distant dog, streetlight buzz), `room_tone`, `clock_tick`, `countdown_tick`,
    `tv_off`, `crowd_whisper`.
- `audio/score.py`: the music, from recorded orchestral and piano samples where possible.
  - Cue- and intensity-driven stems: drones, pulse or ostinato that tightens with tension, piano or music-box motifs,
    string clusters, tremolo swells, risers, braams, hits, stingers, and true silences.
  - `render(cues, duration)` returns a dict of stereo stems.
- `audio/mix.py`: voice (radio/phone voicing as in v1), SFX, and the score stems with gentle sidechain ducking.
  - Levels follow the reference measurements in `analysis/AUDIO_SPEC.md`. The music must be clearly audible, not
    buried.
  - Output: −14 LUFS, true peak ≤ −1.5 dBTP, `mix_en.wav` and `mix_ru.wav` (Russian dub, same cues).

### Cue sheets: the contract between picture and sound
`film.py` writes these to `$S/pov2/cues/`.

`sfx_cues.json` is a list of events:
- `t`: seconds.
- `name`: one of the required SFX names.
- `gain_db`: default 0.
- `pan`: −1..1.
- `params`: an optional dict, for example `{"n": 3, "spacing": 0.32}` for `knock_door`, or `{"dur": 4}` for a bed or
  ambience, or `{"space": "outside"}`.
- `space` is `outside` (heard through the door), `inside`, `doorbell_mic`, or `close`.

`music_cues.json`:
- `duration`.
- `intensity`: a piecewise-linear tension curve, `[[t, 0..1], ...]`.
- `events`: `[{t, type, level, len?}]`, where `type` is one of:
  - `hit`, `stinger`, `braam`, `riser` (ends at `t`), `sub_drop`;
  - `silence` (everything out for `len`);
  - `motif` (piano or music-box phrase), `swell` (strings);
  - `pulse_on`, `pulse_off`;
  - `rule` (rule-card sting), `end`.

`audio/mix.py` (the SFX agent owns it): `mix.py <timeline.json> <vo_en.wav> <vo_ru_dub.wav> <cues dir> <out dir>` renders
the SFX from `sfx_cues.json` and the score from `music_cues.json`, then mixes.

## Working rules for every agent
- Measure the references with code (OpenCV, numpy, librosa) instead of eyeballing where you can. View frames as small
  contact sheets or crops; images are expensive.
- Test at 960×540. Keep test outputs in `$S/pov2/tests/<module>/`.
- Document your module's public API in its docstring. Other agents build on it.
- No secrets in code. Never read or copy `/root/.claude/uploads/*env*`.
- Do not commit; the lead commits at the end.
