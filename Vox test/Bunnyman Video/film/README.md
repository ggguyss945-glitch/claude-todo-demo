# "If The Bunnyman Asks You To Close Your Eyes... DON'T COUNT TO SEVEN": film

This film is made the way the police film (`film_police_ref.py`) and the dummy film (`film_dummy_ref.py`) were: the same 2.5D engine, the cast and set systems, the shot-list format, the police header, rule cards and captions, the global look with a red climax ramp, and cue sheets derived from the picture. The picture follows a shot map written before the shot list: `W/shotmap.md` (every line of the timeline -> the picture that carries it: shot kind, subject, action, framing, props, where the cut lands; then the continuity of the props).

All commands run from this folder (`Vox test/Bunnyman Video/film`). The work dir is `W = film/_work`.

| file | what |
|---|---|
| `film.py` | The shot list (`plan_film()` in 15 sections, below), the builders `B_set`, `B_bust`, `B_ins`, `B_rule`, `B_pause`, `B_card`, `B_black`, the plan helpers (`P()` people on spots or plan points, `cm()` a camera anywhere on the house's floor plan, `STEP(k)` a stair tread, `bust_place` / `bust_eyes`, `hand_layer` hands and the Bunnyman's paws in close-ups), captions / header overlay, `escalate()`, the global look, cue sheets, and the checks (`--sheet`, `--frames`, `--lipcheck`, `--bench`). The module docstring lists the shot kinds and every plan key. |
| `film_police_ref.py`, `film_dummy_ref.py` | The police and dummy shot lists, kept as the format reference. |
| `characters.py` + `characters_bunny.py` / `CAST.md` | The cast (the Bunnyman clean 1987 / filthy now / unmasked Dale, Mom, the narrator and the old body, June, Laurie at 7, Grandma, Dad, the cop, the doctor) and the acting (look_at, reach_to with contact points, PropTracks, give, hold_hand, hand_over, kneel, lie, walk / run on plan paths). |
| `sets.py` + `sets_bunny.py` / `SETS.md` | The house on Orchard Road on one floor plan (hall + stairs, living room, kitchen, upstairs corridor, June's room, the bathroom, the attic), the yard and the treeline, the front porch, Holloway Woods and the railroad bridge, the 1987 parade on tape, Holloway State Hospital, the inserts, the rule card. |
| `render.py` | Stills, test clips and the full worker/slice render (defaults to `W`). |
| `tools/final_chain.sh`, `tools/encode_chain.sh` (+ `enc_seg.sh`), `tools/deliver.sh` | The final render in chunks + the HEVC deliverable `W/deliver/If_The_Bunnyman_Asks_You_To_Close_Your_Eyes_EN_1440p60_HEVC.mp4` (title metadata "If The Bunnyman Asks You To Close Your Eyes... DON'T COUNT TO SEVEN"). |
| `engine/` | The 2.5D engine (camera, layers, lenses, grades, HUD, the VHS post). |
| `audio/` | The sound step. It reads `W/cues/*.json`. |

## Inputs
- `W/align/timeline.json` (412 lines, `duration_en` 1079.16 s), `W/align/asr_cache.json` (word times), `W/align/vo_en.wav` (the edited voiceover, 48 kHz). Written by `tools/align.py` from `W/narration/narration_en.wav` (see Narration below).
- Script: `../script/lines.py` and `../script/narration_en.txt`.

## Narration (the voiceover edit)
The owner's raw TTS take (`W/narration/raw/narration_raw_24k.wav`, 970.8 s, two parts joined) is edited, never re-voiced for the narrator:
- `tools/vo_asr.py <wav> <json>`: Parakeet words with start and end times (+ a rescue pass for the short words the VAD skips) -> `W/narration/asr_raw.json`.
- `tools/vo_edit.py analyze | pacing [--force] | build | check`: maps every line of `script/lines.py` onto the take's sound islands, drops breaths / clicks / lip thumps / the TTS's noises, repairs the TTS slips (FIXES: "eleven seven", "Ye knocks", "Yah. I I", "c-corner", "c-cup", "See leave well", the part seam), re-paces every line boundary from `W/narration/pacing_map.md` (the source of truth: edit a gap there and rebuild), levels each line (one gain per line), 70 Hz high-pass, a light de-esser, 48 kHz 24-bit -> `narration_clean.wav`; then `tools/vo_voices.py` re-voices the quoted words of Mom, June, the girl in the Bunnyman, Grandma, the dying man and the old body (WORLD pitch / formant / breath) -> `narration_en.wav`. Every source span and gap: `edit_list.json`.
- `tools/vo_check.py` (or `vo_edit.py check`): before / after strips and scans (`W/narration/tests/`); `tools/vo_report.py` -> `W/narration/voice_report.md`.
- Then `python3 tools/align.py --write-pauses` (rewrites the pause / pace of every row of `script/lines.py`). With silence between all lines, align.py places every boundary in the silence (to the millisecond) and places a line the recogniser cannot hear (June's "Yeah.") on the sound between its neighbours.
- Order after any change: `vo_edit.py build`, `vo_edit.py check`, `rm -rf _work/align && align.py --write-pauses`, `vo_report.py` (about 6 min on 2 cores).

## The shot list
```
python3 film.py --list                    # every shot (index, start, length, kind) + count / median / p10 / p90
python3 film.py --cues                    # cue sheets -> W/cues/sfx_cues.json, music_cues.json, shots.json
python3 film.py --sheet W/tests/film/sheet --range 0 120 --per 8          # review sheets: first | mid | last frame + the lines
python3 film.py --frames W/tests/film/cuts/cut --threads 1    # every cut: last frame | first frame over magenta (+ cut_holes.json)
python3 film.py --lipcheck                # mouths move only on their own lines -> W/tests/film/lipcheck.json
python3 film.py --still 290.5,316,345.5   # 960x540 stills -> W/tests/film/still_T.jpg
python3 film.py --bench 40 --consec 6 --size 2560x1440 --threads 1          # full-size speed, one process (consecutive frames)
python3 film.py --bench 1 --consec 10 --shots 0,10,57 --size 2560x1440 --threads 1   # chosen shots
```
(`W` stands for `_work`.) Each command builds the film once (about 5 s) and runs at 960x540 unless `--size` says otherwise. Review sheets are 960x540 frames in 320 px tiles, 8 shots a sheet, each row `#index kind start-end (length)` with the timeline lines it covers printed under it.

- **375 shots**, median 2.52 s (p10 1.31, p90 4.85; shortest 0.69 s, longest 10.1 s: the rule cards, the next-episode card and the end card), 20.7 cuts/min (the police film runs 23.4): 169 set shots, 96 close-ups, 79 inserts, 9 rule cards (7 + 2 recalls), 12 VHS-pause shots, 7 cards, 3 black.
- **The film is 1089.01 s** (65,341 frames at 60 fps): the narration (1079.16 s) + 9.85 s for the outro. The sound step's outro jingle starts 0.1 s after the last line ends and runs 9.75 s ("...that's just the outro." and the song IS the outro, `audio/music_plan.py`), so the RULES AFTER DARK end card holds for it and the film fades out with its last soft hum.
- **Story layout** (`plan_film`): `plan_open` (0-65.7 s: the cold open, the 1987 parade on tape, the Courier, Laurie walking out of the woods, the hospital, the house and the rules on the fridge), `plan_1987` (the float, the photo with Laurie holding his paw, the magic trick, the woods, the bridge, sunrise 1987, the missing poster), `plan_since` (every Easter since: the treeline, the burn barrel, Grandma's porch light, Dad and his flashlight, the police morning), `plan_rule1` (11:07, the song, the curtains, June at her window, the wave, "Past us.", Mom in the doorway), `plan_pause` (the comment prompt), `plan_rule2` .. `plan_rule7` (midnight's egg, 1:13's knock, 1:40's mail slot, 2:47's attic, 4:30's break-in and the bathroom, 6:12's sunrise and the body), `plan_reveal` (the trick, 1987 and now, the recalls of every rule, the swap), `plan_after` (Mom's body, the police, Holloway State Hospital, the visit, "Want to see a magic trick?"), `plan_outro`, `plan_globals` (the jingle by version, the count, the swap, the climax pulse and heartbeat, the beds the reveal needs).
- **How it is staged** (the owner's notes on the last films):
  - *Cuts, not long camera moves.* Every move is a short push (1.5-3.5 %/s) or a keyed zoom on a subject that is acting; no fly-throughs. Mediums and two-shots are real cameras placed on the same floor plan (`cm(eye, look)`), so walls, doors, furniture and people stay where they are between cuts.
  - *The picture shows what the line says.* Each line's picture is in `W/shotmap.md`: the knock count tags 1..7 landing on the door as the knocks land, "Mom closes the mail slot" (her fingertips push the flap shut) and "She smooths June's hair" (her hand on it), Mom tucking June in (her hands on the quilt, June asleep on the pillow), the egg rattling on the doormat, the ring rolling in the bottom half of the egg, the light under the bathroom door turning gold, the lock turning by itself and the key, "His lips move one last time. Mama." (Dale's own lips), the crayon drawing sliding in under the door, the switch flipping on "You can turn a light on now", Holloway and Pemberton's struck through in red marker, the zipper pull sliding down.
  - *Hands touch what they hold.* `reach_to` lands a palm / fingertips / grip on a point that moves with the target, props are `PropTrack`s (held, resting, gone: nothing pops or doubles), `give` passes the ring from hand to hand, `hand_over` lays a hand over eyes or a mouth, `hold_hand` joins hands (the old body and June). People face what they act on (`face=` a plan point), walkers' feet step on the floor (walk clips with footstep cues), kneeling and lying come from the spot or `kind`.
  - *No "scared jiggle" filler.* `escalate()` gives the kids wide eyes, brows and breath as the night goes on, Mom locked eyes; nobody trembles on a line that does not say so.
  - *Close-ups* (`B_bust`) are the same set behind the face (`bg=(room, view, cam)`), blurred and dimmed; set pieces whose draw order would put them in front of the face are left out of a close-up's background (review fix: the filter used the projected depth, which dropped the walls of small rooms and showed the outdoors behind June at the mail slot and in the attic).
- **The Bunnyman**: one suit in two states, `bunny87` (clean, 1987) and `bunny` (now: matted, one ear snapped, the dark old stain on the belly panel; review fix: the stain was the brightest thing on the body, an orange oval from across a room, so it is smaller, darker and lower in contrast in `characters_bunny.py`). His mask has no moving mouth: the girl's voice comes from inside it, so on her lines he tilts his head and holds the flap open with a paw (the slot shots are side-on, his muzzle at the flap). Under the half-off head Dale's face says "Mama." with his own lips (the suit's cast has `talk` 0, so the two syllables are keyed by hand) and then goes still.
- **The format**: the police header (HOUSE RULES / RULE n OF 7, the story's clock in the corner: 7:42 PM .. 6:12 AM), captions on every line, seven rule cards (the police card over the blurred laminated rules on the fridge, each with its line icon; rules 6 and 7 are recalled before they are broken), tags (HOLLOWAY STATE HOSPITAL, the knock count), the global look: a red creep from the window smash (600 s), the gold dawn holding it back (709 s), the climax ramp from Mom's hand over June's eyes (770 s) with a blue heartbeat spill at the frame edge under the counts, a white flash on "Seven." and black; the aftermath drained; 1987 on the camcorder tape (date and time stamp), memories warm, the recalls desaturated with a static cut.
- **The comment prompt (258-279.5 s) is a VHS PAUSE**: the frame freezes on Mom's face after "I told you not to look at the treeline" (PAUSE, tape counter 0:04:18, tracking noise), the comment box slides up, the screen splits MOM | THE BUNNYMAN with OR, ONE WORD., the MOM half flickers, then PLAY rolls the tape on. The outro rewinds the tape to that split ("go back to the comment you left before rule two"): THE BUNNYMAN lit, then MOM with a reply arrow, the frozen Mom, then the frame plays: her smile widens and her eyes come to us ("She liked you too.").
- **The outro shows what it says**: black and a breath, the switch flips on and the frame warms, the living room with every lamp on, the Courier's masthead and the egg's stamp struck through, the bridge in daylight, a very ordinary cup of coffee by the notebook with the story's notes, the costume on its hanger (then from behind: the zipper pull slides down), THE TRICK card (1. CLOSE YOUR EYES, 2. COUNT TO SEVEN), the open eye, "SO YOU NEVER DID.", the rewind and the split, the window at night, the LIKE that lands like a knock (a knock cue on its hit), "And subscribe." = Grandma's porch light switching on, the porch light over the empty treeline, the next-episode card (the phone ringing on the nightstand at 3:00 AM: DR. HALVERSON), RULES AFTER DARK, the last line on black and the end card held for the outro song.

## Checks
- **Every shot reviewed**: review sheets `W/tests/film/final/sheet_NNN.jpg` (47 sheets, all 375 shots, NNN = the first shot on the sheet; first | mid | last frame of every shot with its lines), each checked against its line and the staging rules. The shots restaged after review were checked again on stills (`W/tests/film/still_*.jpg`): the tap on the front door (the door in frame), Mom tucking June in, the door opening a crack, Mom on the stairs (up the flight from the bottom), June creeping down in her socks and kneeling at the slot, Mom closing the slot and smoothing June's hair (the camera backed off: her head was cut), the Bunnyman at the slot (side-on), the kids asleep on the couch, the close-up backgrounds at the slot and in the attic, the body at the foot of the stairs, the paw over Laurie's eyes, the joined hands, the scream past the two of them, the cop in the doorway, the visiting room, the report card's A's, the end card.
- **Cut pairs and holes** (`--frames`): every cut as last frame | first frame over magenta (`W/tests/film/cuts/cut_NN.jpg`). The colour detector flagged 35 frames; rendered again over green (`cut_holes_true.json`: a pixel that changes with the background is a real hole) only the intended ones remain: the peephole's black surround (shot 105) and the black shots. The others were magenta-coloured picture (the parade's pink bunting and balloons, the police lights' red and blue, the VHS colour fringes on a glitch cut, June's room, the pink diary).
- **Lip sync** (`--lipcheck`, `W/tests/film/lipcheck.json`): 263 actor-shots. Every speaking actor moves on its own lines and on nothing else, except 5 shots flagged on purpose: the Bunnyman's three masked lines (the mask has no mouth), the narrator's gasp into shock on "Before sunrise." (724.96 s) and Laurie's silent count under the paw (798.94 s). Dale's "Mama." (763.4 s) moves his own lips.
- **Insert animation**: a review found every animated prop insert from the sets (`kw` given as a function of time) frozen on its last state, because `ob_insert` calls it with the film clock; `B_ins` now hands it the time since the cut (the crayon drawing slides in, the lock turns, the key goes in, the highlight walks down the rules, the egg halves part).

## Rendering
```
python3 render.py --stills 290.5,316,345.5 --size 960x540                     # -> W/tests/render/still_*.jpg
python3 render.py --clip 460.9 466 --size 960x540 --audio W/align/vo_en.wav   # one process test clip
python3 render.py --size 640x360 --fps 30 --workers 2 --out W/preview_tmp --audio W/align/vo_en.wav   # low-res preview
python3 render.py --workers 2 --from_ 460.9 --to 465.9 --out W/tests/render5 --audio W/align/vo_en.wav   # a 5 s full-mode test
P=2 bash tools/final_chain.sh > W/logs/final_chain.log 2>&1      # FINAL: 2560x1440 / 60 fps in 24 chunks, then deliver.sh
```
- **The preview** is `W/preview/preview.mp4`: 640x360, 30 fps, 1089.0 s (32,670 frames, 154 MB), the edited voiceover; 2 workers, 11.5 min. `render.py` writes `film.mp4` into its `--out`: render into a scratch dir such as `W/preview_tmp`, then move `film.mp4` to `W/preview/preview.mp4`. `bash audio/final_mix.sh` muxes the final mix onto it as `W/preview/preview_mix.mp4`.
- **The full-mode test** is `W/tests/render5_460.9-465.9_2560.mp4` (June creeping down the stairs in her socks, then kneeling at the mail slot): 2560x1440, 60 fps, 300 frames, 2 workers, end to end in 49 s, the voiceover muxed from 460.9 s. Command: `python3 render.py --workers 2 --from_ 460.9 --to 465.9 --out W/tests/render5 --audio W/align/vo_en.wav`, then rename its `film.mp4`.
- **The final render** goes through `tools/final_chain.sh`: frame-exact chunks from the film's own length (`K=24`, `P` processes; a re-run skips chunks with an OK marker), joined by stream copy into `W/picture/picture.mp4`, frame count checked, then `tools/deliver.sh` makes `W/deliver/If_The_Bunnyman_Asks_You_To_Close_Your_Eyes_EN_1440p60_HEVC.mp4` with `W/mix/final/mix_en.wav` (it needs the final mix first). `tools/encode_chain.sh` is the resumable alternative to `deliver.sh` (capped CRF 17 segments, `enc_seg.sh`). On the shared 4-core machine run two chunks at a time (`P=2`); the picture is about 1-1.5 GB of H.264, so chunks plus the joined file need about 3 GB of disk at the peak. Run it as a harness-tracked background task, not with nohup.
- **Full mode** (`render.py` without `--stills/--clip`): contiguous slices per worker process (one OpenCV thread each), libx264 crf 16 preset faster, joined by stream copy; workers pass absolute frame indices, so a range render matches the full render frame for frame. Finished slices get a `.done` marker (delete markers and slices before re-rendering a changed film into the same `--out`).

## Speed (police budget: 0.6 s/frame at 2560x1440, one process, one OpenCV thread)
- Consecutive frames (`--bench N --consec K`: every 3rd frame, as a render sees them): 125 evenly spaced shots x 3 frames, steady mean **0.196 s/frame**; 40 shots x 6 frames, 0.206 s/frame (`W/tests/film/speed_2560x1440.json`). The slowest shots measured on their own (8 consecutive frames, one process): "And subscribe." as Grandma's porch light comes on (368) 0.59 s (1.9 s on the frames where the light rises: the lit layers re-bake), the front of the house (60) 0.45 s, June's room (90) 0.35 s, the cold open's 2.45x push on the treeline (0) 0.16 s; every other measured shot 0.05-0.3 s.
- The first frame of a shot takes 2-8 s while its static layers are baked.
- Fixed from this bench: "Mom's chair is empty." (173) went from 1.72 to 0.18 s/frame (the set's own depth of field sent a several-screen layer through the dynamic blur on every frame; the shot is now in focus throughout, `dof=0`).
- **The sharp-cache guard** (`engine/scene.py`, `_sharp_dynamic`, the `_blur_raster_too_big` idea applied to the sharp cached path): a sharp layer whose cached raster would pass `SHARP_MAX_SCREENS` screens (12, about 44 MP at 2560: a 170 MB raster, next to `_density_cap`'s 48 MP) is drawn straight into the frame while the zoom races (a second big bake wanted within `SHARP_REBAKE_S` = 0.6 s of film time); otherwise it is baked and reused as before. Measured: the first version (6 screens, no race test) put the cold open's woods on the dynamic path and cost 1.79 s/frame against 0.15 cached, because one bake serves a whole slow push while re-drawing a forest of vector trees costs 1.7 s every frame; with the race condition the cold open is back to 0.16 s, and a racing zoom on the same woods (fz 1 -> 3 in 1.2 s) costs the same either way (`_pick_density`'s headroom already limits re-bakes to one per ~1.4x of zoom), so the guard is only a ceiling on memory and on `_density_cap`'s soft upscale.
- The 5 s full-mode test ran 300 frames in 49 s with 2 workers (about 0.33 s per frame per worker, first-frame bakes included). Estimated final render: 65,341 frames, about 2-2.5 h with `P=2` on the shared machine (about 1.5 h with 3 workers on a quiet one).

## Cue sheets: the sound step's contract
`python3 film.py --cues` writes `W/cues/sfx_cues.json` (284 events `{t, name, gain_db, pan, space, params}`), `music_cues.json` (`{duration 1089.01, intensity, events}`: 90 events) and `shots.json` (the cut list `{i, t0, t1, kind, space, loc, era, cut, room}`). `W/cues/music_cues_plan.json` is the sound step's own file.
- **Spaces**: `inside` (the house), `outside`, `close` (inserts and close-ups), `bath` (inside the locked bathroom), `attic`, `woods`, `hospital`, `vhs` (the 1987 tape and the VHS pause), `memory`.
- **Event names** (the sound step maps them; `audio/sfx.py` `BUNNY_NAMES` and its aliases): the knocks `knock_door` (`pattern` 2-3-2, `group`, `index`; soft at sunrise; the LIKE's knock), `egg_tap`, `egg_rattle`, `egg_open`, `ring_roll`, `fire_crackle` / `fire_whoosh` (the burn barrel), `mail_slot` (creak_open / close), `girl_cry` (`through_door`), `bulb_hum` / `bulb_tink` (the attic), `page_flip`, `paper`, `paper_slide` (the drawing under the door), `window_smash`, `door_crash`, `wet_step` / `wet_drag`, `hatchet_thunk` (one per stair), `knob_turn`, `door_slam`, `struggle` (the fight on the other side of the door), `wet_crack`, `lock_turn` (`by_itself`), `key_in_lock`, `door_creak` (`front_door` crack, `bathroom_open`), `deadbolt`, `light_switch` (wall / porch), `marker_strike`, `zipper`, `mug_set_down`, `phone_ring`, `count_thump` (one per number of the count, `n` of 7), `swap` (`1987` / `now`), `sirens`, `police_radio`, `heart_monitor`, `hum` (`who`), `breath` (gasp / calm_exhale), footsteps by surface and weight (`footsteps_*`, quiet on the stairs in socks), beds (`ambience_night`, `ambience_woods`, `ambience_dawn`, `room_tone`, `crowd_parade`, `tape_hiss`), and the UI (`ui_pop`, `typing`, `magnet_click`, `vhs_pause` pause / play / rewind, `vhs_glitch`, `glitch`).
- **Music events** (suggestions on the picture's frames; `audio/music_plan.py` places the score and its word-anchored events win): `jingle` by `version` (girl_broken, hum, hum_child, outro, vhs_parade; the tinny one from the woods is a bed in the sfx sheet, `version` tinny_woods), `rule` (card stings), `riser`, `swell`, `hit`, `stinger`, `braam`, `sub_drop`, `silence` (drop-outs before the scares, and the VHS pause), `pulse_on` / `pulse_off` (Mom's hand over June's eyes to "Seven."), `heartbeat` (under the counts), `drone`, `outro_warm`.

## Sound prep (the Bunnyman film)
Everything below is in `audio/`; run from `film/`. The verdicts, the music map and the tests are measured, not guessed.
- **Catalogue**: `python3 audio/epidemic_catalog.py --bunny` -> `audio/catalog_epidemic_bunny.json` (the bunny set
  `W/samples/epidemic` first, then the dummy, delivery, police and mirror sets; 271 effects, 45 tracks; a rebuild reuses
  every unchanged row and only recomputes `serves`). `library.py` and `score.py` read it first. `MAP` gives each file the
  `sfx.py` names it can feed; `NOT` keeps the rejected files away from the older names.
- **The owner's new files, judged one by one**: `python3 audio/review_sfx.py` measures all 80 (loudness, clipping,
  floor, spectrum, codec low-pass, onsets, harmonic share, tonal clarity, stereo, and what a recogniser hears in the
  crowds and voices) and draws `W/mix/review/sheet_*.png`; `--md` writes `W/mix/sfx_review.md` from its `DECISIONS`
  (effects: 29 use, 21 process, 20 reject; music: 6 use, 4 reject; every reason written down; the appendix
  `sfx_review.md.notes` covers the synthesis and the free library).
- **The jingle**: `audio/jingle.py` is the ORIGINAL Pemberton's tune (D major, 2/4, 126 bpm; bars 5-6 climb the scale one
  note per syllable of "close your eyes and count to se-ven", so June's count in the climax climbs the same scale in
  D harmonic minor and stops on C#, one step short of home). `python3 audio/jingle.py [names]` renders every version
  to `W/mix/jingle/` (vhs, vhs_cold_open, parade, speaker, speaker_near, musicbox, musicbox_minor,
  musicbox_wind_down, hum, hum_x, knocks, girl, climax, count_1..7, outro, studio), checks each one
  (`jingle_check.json`: the tune's notes found in the render, the voices' pitch against the melody) and draws
  `jingle_sheet.png`. The cold-open version puts every note on the narrator's own syllable of "Hop, hop, hop
  along..." while the band keeps a steady pulse (`COLD_OPEN_MELODY`, `COLD_OPEN_ANCHORS`). The family knock 2-3-2 is the
  tune's own rhythm (`KNOCK_BEATS`).
- **Voices made from the narration**: `audio/voicesynth.py` (WORLD, the cast settings of `tools/vo_voices.py`): `hum`
  (the narrator's /m/ from 37 words, sung on the melody: Mom, Grandma, June, the old body), `sing` (the narrator's spoken
  syllables re-timed and re-pitched onto notes: the real Laurie's broken "Hop... hop... hop along... the Bunnyman
  sings his..."; a recogniser hears "...hop... The bunny man sings his"), `cry` (her crying: wails that crack, hiccup
  sobs, shaky gasps). Analyses are cached in `W/cache/voicesynth/`.
- **SFX**: `audio/sfx.py` `BUNNY_NAMES` (44 new names, the docstring lists every parameter): `ambience_woods`,
  `owl_hoot`, `crowd_parade`, `hospital_corridor`, `hospital_room`, `burn_barrel`, `plastic_melt`, `egg_tap`, `egg_set`,
  `egg_rattle`, `egg_open`, `ring_roll`, `ring_drop`, `ring_hand`, `oven_mitt`, `knock_family` (2-3-2 on the jingle's
  beat, `groups` puts each group into the narration's gaps), `slot_flap` (open / close / snap), `girl_cry`, `jingle`
  (any version as a sound in the scene), `attic_door`, `bulb`, `chest_lid`, `page_flip`, `diary_lock`, `window_smash`,
  `door_crash`, `wet_drag`, `hatchet_step` (the Thunk lands 0.3 s after each tread), `doorknob`, `paper_under_door`,
  `struggle` (wall / shake / slam / crack / full: restrained, no library screams), `key_outside`, `sirens_arrive`,
  `vhs_pause`, `light_switch` (wall / porch / porch_off), `music_box_wind`, `flash_pop`, `dogs_search`, `bathtub`,
  `body_fall_stairs`, `zipper`, `fridge_paper`, `curtain_close`, `peephole`. New spaces: `woods`, `door` (the hall
  heard from inside the shut bathroom), `bathroom`, `slot`, `vhs`, `attic`. Aliases and keyword guesses cover loose names
  (`family_knock`, `mail_flap`, `crying`, `song`, `hum`, `hatchet`, `thunk`, `fight`, `slam`, `crack`, `porch_light`...):
  `python3 audio/sfx.py <name> out.wav --params '{...}'` renders one.
- **Voice FX** (`audio/mix.py`, timeline `fx`): `door` (2.4 kHz top, the panel's boom, the crack under the door, the
  hall, the tiled bathroom; -3 LU), `slot` (300 Hz-3.8 kHz, the slot's 1.1 kHz channel and 3.6 ms comb; -1.5 LU),
  `memory` (Grandma warm and distant; -1.5 LU), `whisper` (dry, close, the breath's air lifted; 0 LU). An unknown fx is
  left dry with a warning. `--who-fx` is now empty by default (the old `X=hall` would have put the old body in a hall).
- **Music**: `audio/music_plan.py` (19 track sections, 172 intensity points, 135 tension events, 24 identity events;
  `python3 audio/music_plan.py --table` prints the map) and `score.py` (`render_jingle`: the `jingle` event type; the new
  tracks' varispeeds in `TRACKS`; the children's tunes in `VINTAGE`; `SHOW_DUCK['jingle']` and `JINGLE_LIFT` per version).
  The score's duration runs to the end of the outro jingle: **the picture must hold its end card to about 1088.5 s**.
- **The sound-design pass**: `audio/sfx_plan.py` ADD (112 cues anchored to the narration's words: every bed, every
  off-screen sound the narration hears, the small foley of the close-ups) on top of the picture's sheet; a row is
  skipped when the picture already has that sound within 1.5 s. EDIT is empty until the full-length checks.
- **Tests**: `python3 audio/sfx_tests.py [1..8]` mixes 8 windows through the whole pipeline (mix.py with the plan) to
  `W/mix/tests/NN_name.wav` + `.json` (every cue re-rendered and checked: sync, phone band, level against the voice and
  the music; every identity layer's level), `--sheet` draws `W/mix/tests/tests_sheet.png`. One mix at a time (about
  1 min each; the first run spends 2 min analysing the tracks into `W/cache/score/`).

## Sound: the final mix
`bash audio/final_mix.sh` (from anywhere; about 7 min, peaks at 9 GB of RAM: never while a render runs) rebuilds everything after a picture change: `film.py --cues`, then `audio/mix.py ... --plan full --hits-db 4 --voice-ride 2.0` to `W/mix/final/` (`mix_en.wav`, the hard link `mix.wav`, `stems/`, `mix_report.json`, `cues_used/` = the two sheets as mixed), then `audio/measure_mix.py W/mix/final --plot` (`measure.txt`, `measure.json`, `measure_cues.json`, `measure_plot.png`), then the mux onto the preview `W/preview/preview_mix.mp4` (`--no-preview` skips it). `python3 audio/mix.py --check W/cues W/mix/final` says whether the mix is stale against the picture's sheets.
- Not run for this film yet (the next sound step). The measurements that stood here were the dummy film's mix and no longer apply. The picture holds its end card to 1089.0 s for the outro song (see The shot list).

## Open problems
- **Sets**: the `fridge_rules` anchor sits at Y 1.42 m but the laminated sheet is drawn at about 0.84 m on the fridge door; the plan aims at plan points (-4.21, 7.74, 0.86) for the sheet and (-4.21, 7.74, 1.09) for the bunny magnet instead. The `porch_egg` camera's own `env` (y 180-300) excludes the frame centre, so `scam()` falls back to (490, 590) for it.
- **The bathroom door from inside** cannot show the corridor through the open doorway: at sunrise the door swings open on the gold light and Mom is seen next in the corridor. A reverse from the corridor (`up` / `bath`, Mom turning the key) was tried and dropped: her reach to the `bath_keyhole` anchor goes to the wrong height in that view.
- **Lying figures** (`pose.lie`) are the front view turned 90 degrees: they read from the side or from above (June asleep, the mascot on the gravel in 1987, the body at the foot of the stairs seen through the balusters), never along their length.
- **Kneeling kids seen from behind** read as standing; June at the mail slot is shot from the side for that reason.
- **The paw / hand over the eyes** in the close-ups is a flat hand layer laid over the bust (`hand_layer`): it reads, but it is the plainest image of the reveal; sleeves are plain tubes (with scratches on Mom's).
- **The three hatchet inserts** (rule 6: "something hard knocking", "Thunk.", "the old hatchet from our woodpile") are one composition, varied by zoom and the hit, not by angle.
- **The Bunnyman's lines have no mouth** (the mask): by design; `--lipcheck` lists those three shots.
- **Sound**: the picture's music events are suggestions and the score is placed by `audio/music_plan.py`; the final mix for this film is the next sound step (`bash audio/final_mix.sh`, never while a render runs).
