# "If a Girl Is OBSESSED With Being Your Only Friend... DON'T WRITE YOUR NAME": film

Night Policy's rule-format horror film, built in the Buttons film's machinery (`film_buttons_ref.py`, kept for reference):
the Film class / plan() / shot builders / BUILDERS, captions, the header, the global look and cue sheets derived from the
picture. Every time in the plan is keyed to `W/align/timeline.json` (line starts / ends and per-line word times): there
is no absolute time anywhere. All commands run from this folder (`Vox test/Obsession Video/film`); `W = film/_work`.

| file | what |
|---|---|
| `film.py` | The shot list: 278 shots, 12:48.6 with the 4 s end card (median 2.3 s, 21.7 cuts/min). |
| `characters.py` + `characters_evie.py` + `characters_obsession.py` / `CAST.md` | Evie (EVIE_ARC, her clips, LetterboxFingers, StubDrop, the slot smile, the chalk girl) and the family. |
| `sets.py` + `sets_obsession.py` / `SETS.md` | The house (one plan), the path from his window, school, playground, the tape, the inserts. |
| `tools/validate.py` | The staging validator for EVERY shot type (docstring lists the checks); `W/shots/validate.json`. |
| `audio/` | The sound step (reads `W/cues/*.json`; owned by the sound teammate). |

- **Story layout** (`plan()`): `plan_trailer` (L0-6, the cold open as a TRAILER, below), `plan_hook` (L7-12: the card,
  the scribbled name, the doormat / Lina / halfway flash-forwards), `plan_setup` (L13-51: Danny with Kofi and Sam, the
  camcorder tape of the swings and the song, the bare wrist, the hoodie, the hopscotch legend and the chalk girl, Evie
  arrives, the locker, "favourite person", Danny brings the card with Mrs. Rahman nodding in her doorway), `plan_rule1`
  (L52-85: pings, 12 / 30 / 47, the dark screen, ONLY ME under the streetlight, the porch light, flat and slid away, the
  wet path, Mom on the phone, the sneaker print, the comment prompt), `plan_rule2` .. `plan_rule7` (the card, then each
  rule's beats), `plan_after` (L302-340: the scrub, Lina's song, Mrs. Rahman, the message, the painted square, the lunch
  table, the shoebox, the card in blue pen, the coda with grown Adam's hands only), `plan_outro` (L341-382: the lamp, the
  painted square, the checklist, the end card, the comment return, like / subscribe, the empty path).
- **The trailer** (`plan_trailer`, `TRAILER`): three waves, every cut on a word or a hit: (1) the tape PLAY, the kids on
  the swings, tearing on "met" / "says"; Evie at his shoulder on "favourite"; the tape chewing on "don't say it back"; her
  ear-to-ear smile pushing in, eyes on the lens; HIT 1. (2) The dark phone lighting up "I can see your light's still on";
  ONLY ME one stretch nearer on every word of "don't look out the window" (jump cuts from above, glitch cuts); HIT 2 the
  neck stretching up to his window. (3) The letterbox fingers writing O-N-L-Y; a WHIP to the blue door from above; Evie
  standing up out of the red Keeping Square at sunset; HIT 3 the counter racing 12 -> 47; the blue door again (slow tilt)
  under "...don't go down."; Danny's mom's window lighting up on "Wake a grown-up."; HARD STOP: black and the one
  silence; "I know who it is." lands on the scribbled name. The cold-open pauses were widened by 2.5 s for the hits
  (`tools/vo_lines.py` PACE: L1 0.85, L2 0.85, L3 0.80, L5 1.25; words untouched, nothing stretched).
- **Look and continuity** (`escalate()`, validate.py STATE): EVIE_ARC is set once from the timeline
  (`CH.evie_arc_from_lines`); flash-forwards carry their own `stage`. Evie is chalk-flat at night (`is_night`). Adam's
  hoodie sleeves are chalk-white only at Danny's blue door (`chalk=1`). The tracker stands where OM_TRACK says each night
  and Evie stands ON it; every dawn the path is wet / scrubbed with the bucket. Door shots look down from the window:
  standing figures there are drawn at their projected (foreshortened) length, leaning with the view (`figure()`
  `fore`), so the figure is small and ONLY ME the biggest shape. Grown-ups share a frame with Evie only where their look
  holds her back (porch light, floodlight, Mom's chair, Mom at the door) or with their back to her (dinner).
- **The tape**: `B_tape` (om_tape + om_tape_stamp): little Adam and Danny ride the swings (`tape_kids`), little Adam sings
  on his own sung line; it returns warped in rule 4 (L164-165) and as a rewind over the cold open's blue door in rule 7
  (L280-284, `rewind_fx` + REW stamp).

## Commands
```
python3 film.py --list                                   # the cut list + pace
python3 tools/validate.py --fps 8                        # staging checks; exit 1 on any ERROR (now: 0 ERROR, 23 WARN)
python3 film.py --contact --size 640x360                 # W/shots/contact_00..05.jpg + contact_all.jpg (mid frame + line)
python3 film.py --still 105.2,451.0 --size 960x540       # stills -> W/shots/
python3 film.py --cues                                   # W/cues/*.json (below)
python3 render.py --size 640x360 --fps 30 --workers 2 --crf 23 --out /dev/shm/prev --audio _work/narration/narration_en.wav
mv /dev/shm/prev/film.mp4 _work/preview/preview.mp4      # then delete /dev/shm/prev
```

## Cue sheets: the sound step's contract
`python3 film.py --cues` writes `W/cues/sfx_cues.json` (`{t, name, gain_db, pan, space, params}`: the cast's events
(Evie's chalk_scrape kinds write / creep / slide / flatten / rise / stretch, chalk_tap, chalk_stub_drop, chalk_roll,
chalk_dust_whoosh; the family's phone_tap, brush_scrub, paint_roll, footsteps, swing_creak, cloth_rustle), the shots' own
sounds (letterbox_flap / rattle, locker_open, porch_light_click, floodlight_on, car_indicator, fork_down, card_drop,
drawer_open, shoebox_lid, bucket_slosh, phone_buzz, light_switch, torch_click, door_open, knock_door), the beds and the
trailer hits as impact_hit with `params.trailer`), `music_cues.json` (`{duration, intensity, events}`: rule cards, hits,
silences, and the picture spans: `tape_song` (version sweet | warped | rewind, space 'tape'), `evie_theme` (the tape song
rotted, every span with Evie near), `drag_stop` (I was. / From me. / It was me. / I'm he-), the trailer's `hit` (level
0..1, why), its `silence` and `trailer_pulse` (three waves)), `shots.json` (the cut list with space / loc),
`beats_cues.json` (each Ping / Clank of `W/align/beats.json` with the shot on screen and its cause) and `spans.json`
(the same tape / Evie-near / drag / trailer spans in one file).

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
