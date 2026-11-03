# Cue picks: Epidemic library for "What If Real Life Had a SETTINGS MENU?"

What we have, what goes where, and what is missing. All numbers were measured. Nobody listened to these files. Data files:
`audio/library.json` (201 files), `audio/music_map.json` (20 tracks, picks under `hook` and `slots`), `audio/sfx_map.json`
(75 names, 276 variants) and `audio/lib.py` (`load_sfx`, `load_music`, `info`, `selftest`). Times are seconds in the original file.

## The downloads

| Zip | Content |
|---|---|
| `b9b286fa…Refrigerator…` | 40 SFX (world, cartoon brass, sirens, animals, crowds, ambiences, house). Also a nested zip with 20 UI/mechanical SFX (clicks, toggles, ratchets, ticks) |
| `6e1e3d00…Notification_Ping…` | 121 SFX (UI, impacts, risers, whooshes, cartoon, glass, tape, kitchen, clocks) |
| `bbbe23e9…Alleyways_of_Seoul…`, `e54f98cf…No_Dessert…`, `cbc70388…National_Anthem…` | 20 music tracks (6 + 8 + 6) |

- Everything is MP3 at 48 kHz (the 320 kbps WAV option was not used). No stems are included, so music drops are done as hard cuts with a slam-back on a downbeat. We cannot mute individual layers.
- The ID3 tags carry Epidemic's genre, mood, energy and BPM. Our beat-grid fit matches the tagged BPM to within 0.02 BPM on 18 of the 20 tracks (rms beat deviation 6-20 ms). The exceptions are Gavotte, which is rubato, and No Dessert, which is off by 0.04 BPM.
- Two files are byte-identical duplicates (`… Jump, Bonk (1)` and `… Short Up and Down (1)`). library.json marks them `duplicate_of`.
- No SFX has flat-top clipping. 12 of the 20 music masters decode with inter-sample overs of up to +1.3 dBFS (float values above 1.0, no flat tops), so apply the music gain before any limiter.
- The kitchen ambience has a digital dropout at 7.25-7.59 s, which the map avoids.
- ffmpeg's gapless decode is 24-47 ms shorter than the MP3 header duration. Always use `lib.decode`, `load_sfx` or `load_music`, so that analysis times line up with samples.

## Music for the 60-second hook (in order)

| Slot | First choice, with in/out points | Why (measured) | Alternates |
|---|---|---|---|
| **(a) Cold open + Day 7 flash-forward**, S00-L001…L008 | **Our Last Stand** (FormantX). Use 0.70-19.95 s. Cut on its hits: hit 1 at 0.80 (peak 0.875) for the title line, hit 2 at 6.425/6.495 for "One app.", hit 3 at 7.38/7.455 for "Total control.", hit 4 at 8.28/8.355 for "No undo." The music cuts hard to a sub drone at 15.60, which carries the flash-forward. A reversed riser runs 18.78-19.35, then a full-band slam lands at 19.395/19.455. Stop the music hard before "...Ish." | D minor, 130 BPM (grid 130.01), heavy sub, -9.7 LUFS. Its first 20 s already form a trailer arc: one title hit, three hits two beats apart (rises of 23, 12 and 16 dB), a drop to dread, then a riser and a slam. Each hit masks the previous tail, so the joins need only a 10 ms crossfade. | **Unfettered and Unchained**, 27.55-61.5 (C# minor, feels like 130 BPM; a hit every 2.775 s from 27.685; lift at 60.915). **Power Pulse**, 15.2-61 (softer, "hopeful"; hits at 16.15, 45.69, 53.08 and 60.485). |
| **(b) Rewind into the 2:13 a.m. bedroom**, L009…L016 | **12 O'Clock Magic** (Jerry Lacey). Start at 0.30 (first note 0.315). A layer enters at 15.145, under "An app you never downloaded." Cut 0.1-0.2 s before the I AGREE sub boom. | Sparse plucks that sound like a music box or celesta over soft sustained tones. C minor/major colours, 65 BPM (feels like 130), quiet (-21 to -17 LUFS, so it needs little ducking) and almost no percussion (percussive ratio 0.02). Tagged "Sneaking; Dreamy": twinkly, curious and a little spooky. | **Trapped Outside**, 0-20.3 (sneaky pizzicato in B minor at 121 BPM, with built-in stops about every second from 3.0 to 8.6 s). **Mr. Payne**, 84.9-108.9 (its quiet, mysterious middle). |
| **(c) "Welcome to Reality Settings!" + brightness gag**, L017…L022; hard drop on L023 | **Gotta Catch That Unicorn** (Josef Bel Habib). Start at 0.10. Boot-up boops play from 0.195 to 1.995; put the toast on the groove downbeat at 2.392. The next section, at 15.02, can land on "Slide it up". Cut hard (fade of 20 ms or less) on "That's the planet's." and hold 0.5-0.8 s of silence, or play a soft sub_boom or whoosh_long into the snap zoom. | The brightest track we have (median centroid 2450 Hz) and the strongest major-key fit (E major, r = 0.91). It is happy bit-music/electro, so it reads as the app's own theme. 150 BPM. It is loud (-9.1 LUFS), so pull it about 6 dB below the bed target. | **Tree House Story**, 10.6-32.5 (quirky orchestral comedy in E major; full entry at 11.11). **Take Me to Prom**, 25.5-55 (an A major waltz whose +7.4 dB lift at 26.03 fits the moon becoming a sun). Trade-off: with a chiptune here, Day 5 must use a different 8-bit track. |
| **(d) DAY 1 card slam**, S01-L001, then the Day 1 bed | **Average Duck Face** (Mike Franklyn). Put the card slam on the groove downbeat at 8.87. Optionally start at 6.30 so the pickup hits at 6.325 and 7.33 play under the card fly-in. Sections run 8.87-28.9 and 28.9-44.9; an 8-bar loop runs 46.86-62.86 (seam 0.996). | C major, 120 BPM (grid 120.01), tagged "Funny; Quirky". Bouncy plucks with sliding-bass glides (visible 9-30 s). This is the closest match to the reference's Day 1 bed (G major, 120 BPM, bouncy plucks). | **Loser**, from 8.495 (G major, 120 BPM; it slams in on its own at 8.495 after a silence from 7.3; mini-stops at 22.7, 54.2 and 68.7). **Buster**, from 2.02 (G major comedy band, 105 BPM). |

### The rest of the video (the 9 slots in EPIDEMIC_LIST)

| # | Slot | First choice | Alternates | Reason |
|---|---|---|---|---|
| 1 | Cold open | Our Last Stand | Unfettered and Unchained, Power Pulse | see (a) |
| 2 | 2:13 a.m. bedroom | 12 O'Clock Magic | Trapped Outside, Mr. Payne | see (b) |
| 3 | Days 1-2 comedy bed (2 tracks) | Average Duck Face + Loser | Buster, Tree House Story, No Dessert | Two different 120 BPM major-key beds. No Dessert (F major, 88 BPM, quirky, with stops at 9.4 and 18.3) suits the breakfast scene |
| 4 | Day 2 rules, Day 3 school | Trapped Outside | College Dropout, Buster | Staccato and sneaky with a stop on every bar, at 121 BPM. The `march_band` SFX (35 s of brass march) covers a literal march gag |
| 5 | Day 3 at 2x speed | Fat and Muscles | Conquerors of Space, Buster | Ragtime piano band, C major, 153 BPM |
| 6 | Day 4, Pickles the posh cat | Gavotte des Papillons | An Afternoon at the Versailles, Take Me to Prom | Baroque with a bright, harpsichord-like timbre (centroid 2150 Hz). It is rubato, so follow `beats_tracked`, not the grid |
| 7 | Day 5, low graphics | Alleyways of Seoul | Conquerors of Space, Gotta Catch That Unicorn | 8-bit, C major, 180 BPM (feels like 90), constant level, 8-bar loop 0.372-11.029. Bit-crush it further |
| 8 | Day 6 chaos into the Day 7 countdown | Unfettered and Unchained, then Our Last Stand | Power Pulse | Unfettered builds in stages (drone, hits every 2.775 s, lift at 60.9, final build 174-238.5, 2 s break, ending). Our Last Stand returns as the Day 7 callback, with slams at 126.58 and 157.82 |
| 9 | Ending + 2:13 a.m. twist | Power Pulse (lifts 45.3-106, calm outro 119-136, E major) | Mr. Payne, Take Me to Prom | Major-key "hopeful" relief. The brass TA-DA is the `fanfare` SFX. For the eerie sting, reprise 12 O'Clock Magic 0.3-6 or use the `tension_sting` SFX |
| - | **Unused** | National Anthem Germany (Christmas Version) | - | A solo-piano Christmas arrangement of a national anthem (Eb major, peaceful). It does not fit a comedy channel |

For editing: an `edit_points` value written as `[onset, peak]` gives the start of the attack and its loudest 10 ms. Put the peak on the cut frame, because the trailer hits swell for 50-75 ms. In music_map.json, grid downbeats are `downbeat_t0_s + n * bar_s`. The hits we checked by hand land on them.

## SFX map (load with `lib.load_sfx(name, i)`; `i` wraps around, so repeats can cycle through variants)

`gain_db` brings every clip to -18 LUFS: one-shots are measured on their loudest 200 ms, loops on integrated loudness. The gain is capped so the true peak stays at or below -1 dBTP. Each variant records `dur_ms`, `onset_ms`, `peak_ms` and `sync_ms` (the attack for hits; the peak for whooshes, risers and swells), plus `tail_ms`, `glide` (start/end Hz for whistles and zips) and `notes`.

| Hook need | Map name: variants, length @ sync ms |
|---|---|
| Taps, selects | `ui_tap` 6 (0.03-0.52 s, transient at 2-30 ms), `ui_select` 5, `ui_confirm` 2, `ui_back` 2 |
| Sliders, toggles | `slider_tick` 5 (28-140 ms), `slider_drag` 5 (three 0.2 s ratchet flicks plus two loops of 2.4 and 3.5 s), `toggle` 6 |
| Pings, success, error, pop-up | `notif_ping` 7, `success_chime` 6, `error_buzz` 7, `popup_whoosh` 6 (rising; variants 0-4 sync on the peak at 88-240 ms) |
| Digital | `glitch` 4, `data_loop` 4 (3.5-26 s), `countdown_beep` 4 (the last is a 2.57 s fast count for the 412 counter), `power_down` 4, `low_battery` 1, `padlock` 3, `stamp` 4 (70-210 ms) |
| Phone | `phone_vibrate` 3 (0.6 s buzz, double buzz, 3.2 s loop), `typing` 4 |
| Transitions | `whoosh_short` 11 (peak at 250-810 ms), `whoosh_long` 2 (3.4 s @ 328 ms, 7.7 s @ 2.56 s), `swish` 6, `zip` 2 |
| Impacts | `sub_boom` 4 (4-10 s tails, so fade after 2-3 s), `impact_hit` 4, `bass_drop` 2 |
| Risers (sync = end) | `riser` 6: 1.45, 1.60, 3.23, 5.35 (orchestral swell peaking at 2.8 s), 13.9 and 12.0 s. `reverse_cymbal` 3: 1.45, 1.60 and 3.23 s |
| Tape and time | `record_scratch` 4, `tape_stop` 3 (stand-ins), `fast_forward` 2, `vhs_rewind` 4 (4-5 s whirr beds and a 0.45 s engage) |
| UNDO cracks and falls | `glass_crack` 3 (ice/glass crackle 1.2-1.7 s), then `glass_break` 3 |
| Cartoon | `bonk` 4, `boing` 9, `slide_whistle_up` 4 (variant 0 rises fast from 680 to 3400 Hz, then holds: for the dog growing), `slide_whistle_down` 4, `cartoon_pop` 9 (6 single pops from "Pops x6"), `magic_shimmer` 4, `fanfare` 4 |
| Alarms, clocks | `siren` 6, `alarm_tone` 2 (two-tone PA), `clock_tick` 4, `clock_tick_loop` 4 (1, 1.8 and 5 ticks/s) |
| World | `crickets_night` (52 s), `morning_birds` 3 (22 s at the densest chirping, plus a 4.7 s burst), `yawn` 3, `snore` 4, `footsteps` 3, `door_slam` 3, `crowd_gasp` 6, `cheer` 3, `duck_quack` 5, `cat_meow` 9, `cat_purr` 2 |
| Rest of the video | `fridge_open`, `mug_down`, `spoon_bowl`, `cereal_pour`, `kitchen_amb`, `cafeteria_amb`, `school_bell`, `alarm_clock_ring`, `chalk`, `pencil_scribble`, `bubbles`, `splash`, `sad_trombone`, `villain_sting`, `tension_sting`, `crowd_panic`, `freeze_crackle`, `march_band` |

Suggested placements in the hook: L001 `ui_tap` + `slider_tick` per step + `slide_whistle_up`[0] (dog grows) · L002 `whoosh_short` (zoom) + `swish` + `boing` (tree flips) · L003 `toggle`/`cartoon_pop` per item · L004 `glass_crack`[0] then `glass_break`[0] on the fall · L005 `alarm_tone`[0] before the SYS line, `siren`[0], `data_loop`[0] (sky loading bar), `power_down` + `glitch` (mannequins flicker), `stamp` ×2 (DEFAULT tags), `countdown_beep`[0] · L007 `countdown_beep`[3] under the counter roll · L008 music stop + `record_scratch`[0] · L009 `vhs_rewind`[0] + `whoosh_long`[0] · L010 `crickets_night` + `clock_tick_loop`[1] low · L011 `phone_vibrate`[1], `notif_ping`[0], `magic_shimmer`[2] · L012 `popup_whoosh`[0] · L015 `swish`[0] + `whoosh_short` · L016 `ui_confirm`[0] + `reverse_cymbal`[0] into `sub_boom`[0] + `whoosh_long`[0] (ripple) · L017 `popup_whoosh` + `success_chime`[0] + `magic_shimmer`[0] · L020 `slider_drag`[1], `riser`[0] (peak on the flare), `morning_birds`[2] then [0] · L021 `door_slam`[0] · L023 `whoosh_long`[1] (peak on the snap) + `sub_boom`[2] · S01-L001 `whoosh_short` (peak one frame early) + `impact_hit`[0] + `sub_boom`[3].

## Missing for the hook, and the substitutes

| Missing | Where | Substitute or synthesis |
|---|---|---|
| Paper page flip / riffle | DAY card flips 1→7 (L003), T&C pages stacking (L013), the "one flick" (L015) | Synthesize. One flip = band-passed noise 1-6 kHz with a 4 ms attack and 60-90 ms decay, plus a 20 ms thump at 300 Hz. A riffle = 30-40 flips accelerating over 0.5 s, layered on `swish`[0] |
| Dog bark / growl | The neighbour's dog grows to house size (L001) | Not in the downloads. Best fix: the owner downloads "small dog bark" and "big dog woof" from Epidemic. Otherwise synthesize a cartoon "woof" (two formant-filtered saw bursts, F0 450→300 Hz, 120 ms), pitched down an octave with reverb for the giant dog. The growth itself = `slide_whistle_up`[0] + `sub_boom`[3] |
| Sun flare / camera-flash "whoomp" | Moon flares into a sun, room blows out white (L020) | `riser`[0] (peak on the flare) + `magic_shimmer`[1] + `impact_hit`[1]. For a flash: a 10 ms noise burst plus a 2→8 kHz chirp over 120 ms (synthesized) |
| Shockwave whoosh | I AGREE ripple through room, house, street (L016) | `sub_boom`[0] + `whoosh_long`[0]. Synthesize a low-passed noise swell with a 60→35 Hz sine drop |
| True tape stop | Music stop on "...Ish." / punchlines | Synthesize on the music bus by resampling the last 0.6-0.8 s with a falling rate. `tape_stop` stand-ins: transport clunk, power-down sweep |
| Counter roll 1→412 | L007 | `countdown_beep`[3] (15 beeps/s) + synthesized blips. The owner already plans to make the counter ticks |
| Sweat-drop "bloop" | L006 | Synthesize a sine 900→1400 Hz over 60 ms, or use `cartoon_pop`[6] |
| Space air / zoom-out drone | L023 snap zoom to space | `whoosh_long`[1] + `sub_boom`[2]. If needed, the sub drone in Our Last Stand at 15.8-19.1 |
| Kid yawn | Sam "Prove it." (L018) | The library yawns are adult male, so let the VO perform it. If a library yawn is used, pitch it up about 4 semitones |
| Cartoon dizzy birds (needed after every bonk, not in the hook) | Bonks | Synthesize ~5 kHz chirp pairs (production bible 4.3) |

Missing for the rest of the video: leaf blower, light wind/snow, a real quirky march with bassoon and tuba (the march_band SFX or Trapped Outside stand in), and an eerie *synth* sting (use 12 O'Clock Magic or `tension_sting`). One more note: the exaggerated cartoon snore's Epidemic file name mentions a cartoon character. Prefer the human snore variants 0-2.

## How it was checked

- `lib.selftest()` decodes every map variant and all 20 tracks. Result: **276/276 SFX and 20/20 music OK**: none silent, no clipping, lengths exact to the sample.
- QA sheets show the envelope, take spans and spectrogram for every file, every map variant and every track. They are in the scratch `epidemic/qa/` folder (`sfx_*.png`, `map_*.png`, `music_*.png`, `zoom_*.png`). The take segmentation was checked on them: for example "Pops x6" gives 6 takes, "Short Bursts" 4 bursts (11 sub-pulses), each short dry whoosh file 4, each meow file 3, the duck quacks 3 and 6. In the map, multi-part sounds are grouped (`take: [i, j]`), and every one-shot was checked for heads cut into the sound and truncated tails.
- Scripts live in the scratch `epidemic/scripts/` folder: `ingest.py`, `music_an.py`, `build_sfx_map.py`, `build_music_map.py`, `hits.py` and `qa_*.py`.
