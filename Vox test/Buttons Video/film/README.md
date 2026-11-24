# "If Your Mom's Eyes Turn Into Buttons... DON'T KEEP HER SECRET": film

Night Policy's rule-format horror film, built in the Walls film's machinery (`film_walls_ref.py`, kept for reference):
the same 2.5D engine, the Film class / plan() / shot builders / BUILDERS, the header, captions, the global look and cue
sheets derived from the picture. Everything is keyed to `W/align/timeline.json` (line starts / ends and per-line word
times); there is no absolute time in the plan. The villain is the Blank (story bible; `CAST.md`, Buttons section).

All commands run from this folder (`Vox test/Buttons Video/film`). The work dir is `W = film/_work`.

| file | what |
|---|---|
| `film.py` | The shot list (about 357 shots, 13:43 with the 4 s end card). `plan()`: `plan_open` (L0-13 the cold open + hook), `plan_setup` (L14-33), `plan_chat` (L34-51 the game chat, the grey head filling in), `plan_rule1` (L52-77 the photo, the streetlight, the lobby glass), `plan_prompt` (L78-80), `plan_rule2` .. `plan_rule7`, `plan_after` (L297-316), `plan_sting` (L317-339), `plan_outro` (L340-384), `plan_globals` (the Button Song motif and the on-screen sounds no shot carries). |
| `characters.py` + `characters_buttons.py` / `CAST.md` | The cast (Buttons section). |
| `sets.py` + `sets_buttons.py` / `SETS.md` | Our block, the apartment, the school lane, the narrator's home now, the chat UI and the inserts (Buttons section). |
| `render.py` | Stills, test clips and the full worker/slice render. |
| `tools/validate.py` | The staging validator for EVERY shot type (its docstring lists the checks): anchors, floors, levels, ground lines, the car, overlaps, reach, props, kid-safe distances, cut positions, the STATE table, camera, lengths, lips. |
| `audio/` | The sound step (reads `W/cues/*.json`; owned by the sound teammate). |

## Shot kinds (film.py builders `B_<kind>`)
- `set`: a set view with figures on the plan (anchors or (x, y, Y)); `cam=MC(at, ang, d, S=)` frames from a plan point;
  `mirror=[...]` draws figures reflected in the black microwave door (`ST.bt_mirror`); `acts` add the red coat (worn: back
  behind him, front over him), the car arm, the rolling buttons, the flat cardigan, the narrator's hands.
- `bust`: face close-ups over the blurred set (`rot=-90` for a face on the pillow); `ins`: `bt_insert` props (+ hands,
  + a button dropping into the jar on its beat); `chat`: the tablet screen (`bt_chat`: the grey head filling in, Mom's
  account at 2 a.m., the son's tablet now).
- `rule`: the Brave List inside Owen's closet door. `list=True` is the whole list at "Rule number n" (the broken rules stay
  pale: `INK(t)`), then rule n big, each word appearing as it is read. `blist`: the list inside a scene (a rule fading,
  rule three staying blue, the ink coming back line by line as he writes on the fridge board).
- `prompt`: the comment prompt (stage 'ask' L78-80, 'return' L371-377), every word on its word. `list`: the outro
  checklist (L350-368), every item legible while read. `card`: the outro cards. `black`.

## Continuity (film.py `escalate()` applies it to every actor; validate.py STATE checks it)
Owen in pyjamas at night, the green coat outdoors (Monday, Wednesday pickup), the hoodie by day. `FADE(t)`: one step per
secret (L60, L89, L144, L170, L203; cool, translucent, never past 0.8), gone from the microwave door only in rule six,
back "like a photo developing" (L281-282). `PGREY(t)`: a little grey from L94, pencil grey from L205, colour back on
"Mom" (L232). Mom's glare until she pulls her glasses off (L277); the two black circles L195-197. The Blank: form 1
(sunglasses in the car, the reading glasses at 2 a.m.), form 2 (a little taller each time: `CH.BLANK_TALL`), form 3 from
midnight (unfolds BESIDE the fridge, holds the coat by its seams, fingertips always short of him, collapses flat).

## Commands
```
python3 film.py --list                                         # the cut list + pace
python3 tools/validate.py --fps 8                              # staging checks; exit 1 on any ERROR
python3 film.py --sheet _work/shots/sheet --per 12 --tile 256 --size 640x360   # contact sheets: first | mid | last frame + the lines
python3 film.py --still 105.2,451.0 --size 960x540             # stills -> W/tests/film/
python3 film.py --cues                                         # W/cues/sfx_cues.json, music_cues.json, shots.json, beats_cues.json
python3 render.py --size 640x360 --fps 30 --workers 2 --crf 23 --out _work/preview_tmp --audio _work/narration/narration_en.wav
mv _work/preview_tmp/film.mp4 _work/preview/preview.mp4        # then delete _work/preview_tmp
```

## Cue sheets: the sound step's contract
`python3 film.py --cues` writes `W/cues/sfx_cues.json` (`{t, name, gain_db, pan, space, params}`: every action of the
picture, from the shots' cue lists, the cast's acting events, the beds and `plan_globals`: coat buttons, microwave hum,
music box winding, tablet face down), `music_cues.json` (`{duration, intensity, events}`: rule cards, hits, silences
before the scares, the Button Song as `jingle` events with `version` 'box_clean' | 'box_slow' | 'hum_slow' | 'sung_loop'
| 'detuned' | 'four_notes' | 'box_real' | 'tablet_chime'), `shots.json` (the cut list with each shot's space) and
`beats_cues.json` (every Tik / Ping of `W/align/beats.json` with the shot on screen and its cause; the beats are also in
the sfx sheet as `tik` / `ping` with `params.beat`). Acting 'tik' events that are not beats become `fingertip_tap`.

## Sound: the final mix
`bash audio/final_mix.sh` (from anywhere; about 14 min; peaks about 8 GB RAM, so it can run beside a 1-2 worker render; it sets
its own `oom_score_adj` to 1000, so if RAM runs out the kernel kills the mix, never the render) does it all:
`film.py --cues` -> `audio/mix.py --plan full` -> `W/mix/final/mix_en.wav` (+ hard link `mix.wav`) -> `audio/measure_mix.py`
(`W/mix/final/measure.txt`) -> `audio/mix_scenes.py` (`W/mix/final/scenes/NN_*.png`) -> the mix muxed onto
`W/preview/preview.mp4` as `W/preview/preview_mix.mp4`. After a picture change: re-render the preview first (Commands),
then run `final_mix.sh`. The stems (`W/mix/final/stems/`, 0.9 GB) are written for the measure: delete them when done.
- The score and its scares are anchored to the narration's WORDS in `audio/music_plan.py` (EVENTS: 22 boosted scares,
  each just after its word, `nosnap`; a plan hit without `nosnap` within 0.35 s of a picture hit frame snaps onto it). The
  picture's SFX names are mapped onto this film's recipes in `audio/sfx_plan.py` (PICTURE); a name the mix does not know
  prints `unknown SFX` in `W/mix/final/mix.log`: add it to PICTURE rather than trust the keyword fallback.
- First full mix (21 Nov): -14.05 LUFS, true peak -1.69 dBTP, scares +6.0..+9.7 LU momentary over the integrated level,
  bed in the gaps rising rule by rule (ARC_TARGETS in mix.py), chime returns as in the bible's chime table.
- Sound fix round (21 Nov, after the sound critic's report `W/handoff/sound_critic.md`):
  - the boosted hits land in the voice edit's scare beats JUST AFTER their words (`end:` anchors in music_plan.py
    EVENTS, `nosnap`), never on them; mix.py's boost path holds every word in the 1.6 s after a boosted hit with a
    broadband, level-keyed duck (`speech_duck` / `zone_duck`: the hits 8 LU and the whole bed 7 LU under the voice in
    100 ms and 400 ms blocks, 10 ms look-ahead, 120 ms release; the gap before the next word stays the hit's own);
    `measure_mix.py` now prints `boosted_scares` (peak +6..+10 LU, words after >= 6 LU; `off_target` lists misses);
  - sfx_plan.py: the nine keyword-fallback names mapped, wooden steps outdoors -> snow, stacked steps merged, doubled
    leg clicks and the second furnace death dropped, cues moved off the words they name (EDIT `at`, OFF_WORDS), new
    recipes in sfx_ice.py (`jaw_strain`, `hall_clicks` behind the bathroom door until "The clicking stops.",
    `glass_slide` for the face on the glass, `leg_pry`); the chime's stem gets a voice-keyed 1-4.5 kHz cut
    (SHOW_VCUT_DB) and plays on through the dip before the jaw drop (`keep_show`); a soft lullaby under "Humming his song.".
  - L192 "Who's the coldest? YOU are!" is in his normal vendor voice (tools/vo_voices.py VARIANT): rebuilt with
    `cd tools && python3 vo_edit.py build` (narration_clean.wav bit-identical, narration_en.wav changed only in
    360.58-364.38 s), copied to `W/align/vo_en.wav`; line times unchanged (align.py into a scratch folder matched
    timeline.json to 1 ms), so timeline.json is kept and only L192's words in asr_cache.json were replaced;
    `python3 tools/vo_asrcheck.py --every`: 0 failures.
  - Measured on five excerpt mixes (90-130, 160-245, 290-440, 480-590, 630-700 s: every boosted scare; the full
    mix could not run, the machine was rendering): -14.0 LUFS, -1.7 dBTP; 21 boosted scares +7.0..+10.7 LU momentary
    over the integrated level (the towel jam is now an unboosted hit); the words after each hit +8.4..+29 LU over the
    bed (50 ms segments); the critic's 24 lines min +4.6..+30 LU (were -10.6..+0.1) and all recognised word for word
    (L52 "Out of tune." reads "two" only at 50 ms margins, with the bed 13.6 LU under it; right with 0.2 s).

- Final remix (21 Nov, 20:28, on the picture fixers' cue sheets; the delivery uses `W/mix/final/mix_en.wav`, which
  `tools/join_chain.sh` muxes): -14.04 LUFS, true peak -1.70 dBTP, LRA 3.3 LU, 0 unknown SFX; 21 boosted scares +6.4..+9.9 LU
  momentary over the integrated level; the words after every hit >= 6 LU over the bed (50 ms segments) except one dip inside
  "doorknob" after the face at the glass (5.1 LU; the bed is 12 LU under the word); the critic's 24 lines now min +3.1..+28.5 /
  median +7..+44 LU over the bed (400 ms; were -10.6..+0.1). Recogniser on the mix: 9 of 428 lines differ from the dry voice,
  6 of them digits or tense; open: L297 "Prying." (read "Crying.": the boosted leg hit at 525.54 ends 50 ms before the P),
  L52 "Out of tune." and L200 "Keeps waving." (read right with 0.2 s margins). Fixes in this remix: grade-1.0 boost target
  11.5 -> 10.5 (mix.py BOOST_TARGET_LU), the pull-back taps 0.6 s so the clicking stops on "The clicking stops." (sfx_plan.py
  leg_withdraw), the doorknob sub drop 0.55 -> 0.4 (music_plan.py).
- Memory: `final_mix.sh` renders the score first in its own process (`mix.py --score-only`, peak 7.1 GB) into a RAM cache
  (`MIX_SCORE_CACHE`, default `/dev/shm/ice_score_cache`, unlinked as soon as the mix has loaded it), then the mix (peak
  8.2 GB) loads it: bit-identical to rendering the score inside the mix (tested on a 40 s window), which peaked at 9.5 GB
  and was killed twice beside the running render.

### The final remix (run once the new cue sheets exist; from `film/`, `free -g` >= 8 GB available)
```
python3 render.py --size 640x360 --fps 30 --workers 2 --out _work/preview_tmp --audio _work/align/vo_en.wav   # if the picture changed
cp _work/preview_tmp/film.mp4 _work/preview/preview.mp4
bash audio/final_mix.sh                       # cues -> mix -> measure -> scene sheets -> preview_mix.mp4 (about 14 min)
grep -c "unknown SFX" _work/mix/final/mix.log  # 0 expected
grep -A3 boosted_scares _work/mix/final/measure.txt   # peaks +6..+10, words_after_min_LU >= 6, off_target []
rm -rf _work/mix/final/stems                  # 0.9 GB
```
