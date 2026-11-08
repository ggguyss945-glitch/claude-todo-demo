# EP01 "Never Move Grandpa": 5-second look test, storyboard and sound

The test covers voice line 01: *"In this world, grandparents don't die. They turn into garden gnomes."* It is 5.00 s long
(300 frames at 60 fps, 1080x1920) and uses the owner's own voice-over and Epidemic SFX. Follow `docs/STORYBOARD_RULES.md`
(the edit) and `docs/VISUAL_BIBLE.md` (the look). The engine data is in:

| File | What |
|---|---|
| `episodes/ep01/test5_timeline.json` | Engine timeline. 5 shots, frame-snapped. The builders are an object map in `episodes/ep01/test5.js` (written by the animate stage), keyed `sky_to_street`, `porch_couple`, `grandma_cu`, `poof_swing`, `gnome_hero`. Every decision below is repeated in `params`. |
| `episodes/ep01/test5_captions.json` | One word at a time (bible §8.1), with frame numbers and the style spec |
| `scratchpad/rbx/test5/sound/test5_mix.wav` | 48 kHz stereo, 24-bit, 5.000 s: voice and SFX, no music |
| `scratchpad/rbx/test5/sound/test5_voice.wav`, `test5_sfx.wav` | Stems, so the owner can add music under them |
| `scratchpad/rbx/test5/sound/test5_mix_report.json` | Measured levels and the exact cue list |
| `scratchpad/rbx/test5/sound_tools/mix_test5.py`, `make_test5_board.py` | Scripts that rebuild the mix, the timeline and the captions, and run the QA |

(`scratchpad` = `/tmp/claude-0/-home-user-claude-todo-demo/353ac1d9-152b-55bb-bdf1-0625e0fc6a83/scratchpad`. Reference frames
and the SFX files stay in scratch and are never copied into the repo.)

---

## 1. Word timings (owner's read, `ep01/voice_asr.json`, refined on the waveform)

The ASR times are quantised to 80 ms, so every cut word was re-measured on 5 ms band envelopes of the 24 kHz file.
The line actually runs **0.24-3.415 s**, not "about 0.2-4.5 s": "gnomes" ends at 3.415 s, and the next line
("First, your grandma...") starts at 3.59 s. That line is cut out. The voice fades out over 3.400-3.440 s, so
3.44-5.00 s holds the picture in silence (crickets and the shimmer tail).

| Word | ASR (s) | Onset used (s) | Evidence |
|---|---|---|---|
| In | 0.16 | 0.240 | voicing starts 0.235-0.245 (a soft lip noise at 0.10-0.16 s is kept, -48 dBFS) |
| this | 0.40 | 0.395 | dental fricative after the dip at 0.395 |
| world | 0.56 | 0.572 | /s/ of "this" ends 0.565; /w/ voicing 0.575 |
| **grandparents** | 0.88 | **0.940** | silence 0.89-0.935, /g/ burst 0.940 |
| **don't** | 1.52 | **1.500** | closure 1.47-1.495, voice bar 1.500, burst 1.515 |
| **die** | 1.76 | **1.738** | closure 1.715-1.735, /d/ burst 1.740 |
| **They** | 2.08 | **2.118** | creak of "die" ends 2.115; /dh/ 2.120 |
| **turn** | 2.24 | **2.228** | closure 2.215-2.225, /t/ burst 2.230 |
| into | 2.40 | 2.400 | no acoustic boundary after the /n/ of "turn"; the ASR time is kept |
| garden | 2.64 | 2.630 | /g/ voice bar from 2.58, burst 2.655 (midpoint used) |
| **gnomes** | 2.96 | **2.940** | the /n/ of "garden" runs into "gnomes": /d/ burst 2.87 plus schwa and /n/ puts the onset at about 2.94 |

---

## 2. Shot list (hard cuts only; cut = naming-word onset minus 1 frame)

5 shots in 5.0 s, 4 cuts. During the voice that is 4 cuts in 3.4 s, the hot hook pace of the rules (§5: hook shots
0.5-2.1 s). Every cut lands 17-23 ms before its word (window -100 to +33 ms). Both sentences open on a cut.
All shots are night in the P1 grade family, at one location: our street and the hero lot.

| ID | Frames | Start-end (s) | Dur | Words | Picture | Size / angle | Camera move (numbers) | Faces | VFX | SFX | Grade |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **s01** | 0-54 | 0.000-0.917 | 0.917 | In this world, | **Opener.** Frame 0 looks up into the galaxy sky with the TF blue-violet moon, roof ridges and pine tips along the bottom edge. The camera swoops down to the night street: a gnome on every lawn, every one turned to face its house (backs to us), unlit lanterns, lamp posts, warm windows | sky → WS, high 3/4 | **Accent: crane down + tilt down**, `outQuart` over 0-0.95 s (99.9% done at the cut): tilt -40.8° (pitch +28° → -12.8°), crane -22 studs, dolly +6 studs, roll -9° → 0°, ending on `views.streetWide` (fov 62). Peak speed about 5300 px/s on frame 0 (bible: 3000-5600). Linear push +10% (FOV) layered on top, so the shot never settles | none (gnome backs) | 8 sparkle glints (40-80 px) over the near lawns | **W1** airy whoosh (peak 0.12 s), **A1** crickets bed starts | `night` (nightStreet P1) |
| **s02** | 55-88 | 0.917-1.483 | 0.567 | grandparents | An old couple on a porch swing at night: Grandma (frame left, rose cardigan, round glasses, grey bun) and Grandpa (frame right, navy cardigan, walrus moustache). Behind them: the lit window, the wall lantern and the front door | MS two-shot, eye level (seated heads) | **Push +19%** linear (FOV), truck -0.15 stud (about 30 px/s). Camera 9.5 studs from the swing, 28° front-right, y = deck + 4.4, aimed at deck + 3.4, fov 70. The swing sways ±2.5° at 0.45 Hz | Grandma `neutral`, Grandpa `neutral` | 6 glints | none | `porch` (porchGlow) |
| **s03** | 89-125 | 1.483-2.100 | 0.617 | don't die. | **Reaction CU**: Grandma, perfectly content. On "die" her glasses flash a 4-point star glint (a cheeky "nope"; also plants the glasses for line 03) | CU, eye | **Push +16%** linear, roll drift 0 → +1.0°. Camera 3.2 studs from her head, 20° front-right (same side of the axis as s02), fov 70; face in the upper 30-40% of the frame. Window and lantern behind her shoulder; the navy edge of Grandpa's cardigan at frame right | Grandma `content` (^^) **from the cut** (frame 89), held 0.62 s | **Glint on frame 104 (1.733 s, "die")**: `tex.sparkle` 4 points, #f4ecff, 0 → 110 px in 3 frames, gone by +16 frames, rotating 0 → 25°. Plus 5 glints | none (kept sparse; the optional "ting" T1 below is not in the mix) | `porch` |
| **s04** | 126-174 | 2.100-2.917 | 0.817 | They turn into garden | **Transformation.** Same porch and swing, lower and from the other front side. Magic dust swirls around the couple from the cut; on "turn" a sparkle burst covers both, and they **snap into two gnomes** standing on the swing seat (Grandma-gnome with lavender hat and round glasses, Grandpa-gnome with an unlit lantern). The swing jolts | MS, low | **Push +20%** linear. Camera 8.5 studs from the swing, 20° front-left (Grandma stays frame left), y = deck + 2.4, aimed at deck + 3.2 (looking up), fov 70. The swing sways ±2.5°; at the snap the seat dips 0.15 stud and swings ±5° (`springKeys`, 3 Hz, zeta 0.35) | humans `content` until the snap; then the gnomes (sculpted; eyes on the lens, `gnomeIdle`) | `magicDust` from 2.10 s, building. **Burst on frame 134 (2.233 s, "turn")**: one `fx.burst` per grandparent at chest height, count 30, puff 12, corePx 520, ring 40 → 620 px, 0.35 s. **Humans hidden and gnomes shown on frame 134**, under the burst core | **M1** shimmer swell (from 2.10, peak 2.30), **P1** poof (pop transient 2.240 s) | `porch` |
| **s05** | 175-299 | 2.917-5.000 | 2.083 | gnomes. | **Hero creature, character intro.** Grandpa as a glazed ceramic gnome in his flowerbed under the bedroom window, facing the house, seen from below. A warm window spill (behind the camera) lights his face; the brass lantern is unlit. Behind him: tulips, lawn, picket fence and gate, a lamp-post halo, the lit windows across the street, and the galaxy sky behind the hat tip. Holds in silence after the line (the creepy-cute stare) | CU → ECU, low | **Push +28%** linear (character-intro push, rules §3) + crane +0.10 stud + roll 0 → +1.2°. Camera between the gnome and the house wall, 1.7 studs from his face, y = 0.9, aimed at his nose (y 1.35, about 12° up), fov 70 (cull the wall for this shot if needed) | gnome: `gnomeIdle` only, gaze up +10° (to the bedroom window). **No blink, no head turn, lantern UNLIT** (plot devices for later) | 8 glints + 6 gold motes still settling | **M1** sparkle tail to 5.0, **A1** crickets. Voice ends 3.415 | `nightHigh` (nightLawn P1 high-key) |

**Kit calls** (`engine/kit`): street `sets.buildStreet(ctx, { seed: 'ep01', lotsPerSide: 6 })`, lawn
`sets.buildLawnCloseup`, gnomes `K.makeFamilyGnome(i)` and `K.makeGnome('grandpa', { lantern: 0 })` /
`K.makeGnome('grandma', { lantern: false })`, humans `K.makeCharacter('grandpa' | 'grandma')` in the `sit` pose, faces
`K.setFace`, light presets `nightStreet` / `porchGlow` / `nightLawn`, fx `sparkles` / `magicDust` / `burst`.
Units: studs x 0.32 = metres.

**New prop needed: the porch swing.** A slatted wooden bench 5.5 x 1.6 studs, seat top 1.5 studs above the deck (the `sit`
pose expects 1.5), backrest 1.6 tall, two chains to the porch ceiling, painted #e9e4da or the deck wood. If the hero
bungalow's 11-stud centre porch is too tight, give the hero house `porch: 'full'` for s02-s04. Fallback: two
`rockingChair` props side by side, rocking ±4° out of phase.

---

## 3. Sound: cue list (`test5_mix.wav`)

The voice is always on top. No music (the owner adds it, about 8 LU under the voice and constant, as in TF). SFX follow
bible §8.2: sparse and literal, one sound per picture event, never a hit on a plain cut. The only whoosh is on the opener's
accent move.

| Cue | Picture event | Test in-out (s) | Source file (Epidemic, from the owner's zips) | Source in-out (s) | Level | Fades / filters |
|---|---|---|---|---|---|---|
| **A1** | night bed under the whole test | 0.00-5.00 | `ES_Ambience, Suburban, Field With Crickets, Distant Traffic, Night 01` | 32.00-37.00 | -33 LUFS (17 LU under the voice) | in 60 ms / out 150 ms; HPF 250 Hz removes the distant-traffic rumble and keeps the crickets |
| **W1** | s01 crane down from the sky | 0.00-1.46 (peak 0.12) | `ES_Swooshes, Whoosh, Airy, Short` (variant 3, peak at 11.21) | 11.09-12.55 | -26 LUFS on 0-0.5 s (10 LU under) | in 20 ms / out 250 ms; HPF 200 Hz, LPF 9 kHz. It has decayed 18-35 dB by "In this world" |
| **M1** | s04 transformation: swell from the cut, sparkle tail through s05 | 2.10-5.00 (peak 2.30) | `ES_Magic, Shimmer, Christmas, Sparkle, Magic, Shimmer Dust` | 2.20-5.10 | -28 LUFS on 2.10-3.10 s (12 LU under) | in 40 ms / out 600 ms; HPF 1.5 kHz (it sits above the voice) |
| **P1** | s04 the snap (burst frame 134) | 2.105-2.425 (pop transient **2.240**) | `ES_Cartoon, Pop, Vanish` (variant 1: an air rise into a pop) | 0.10-0.42 | -33 LUFS on 2.10-2.50 s; peak 2 dB under the voice peak in that window | in 12 ms / out 50 ms; HPF 180 Hz. It fills the closure gap before "turn" without covering it |
| T1 (optional, not mixed) | s03 glint on "die" (1.733) | - | `ES_User Interface, Misc, Pings, Tings` | 0.00-0.60 | -36 LUFS if used | left out to keep the SFX sparse |

**Voice.** The voice is cut from the owner's `voice_raw.wav` at 0-5.00 s, with a raised-cosine fade over 3.400-3.440 s
(after the /z/ of "gnomes", before the breath and "First"). It is upsampled 24 → 48 kHz (exact 2x polyphase), given a 60 Hz
rumble high-pass and +3.24 dB of gain, and played as dual mono.

**Measured** (BS.1770-4, `pyloudnorm`):

| Measure | Value |
|---|---|
| Voice | -16.0 LUFS on the line (0.2-3.42 s); short-term max -15.6 |
| Mix | -16.0 LUFS integrated; short-term max -15.4 |
| True peak | -1.2 dBTP (the limiter takes at most 0.25 dB) |
| SFX bus | 14 LU under the voice |
| Voice over SFX while speaking | median +17.7 dB |
| Exception | the 0.1 s around the snap, where the pop sits in the /t/ closure gap at the voice's level |

---

## 4. Captions (`test5_captions.json`)

One word at a time, lower case, punctuation stripped, apostrophe kept ("don't"). Each word swaps 1 frame before its
onset; the first word is up from frame 0. The words are: in · this · world · grandparents · don't · die · they ·
turn · into · garden · gnomes.

- **Frames:** 0, 23, 33, 55, 89, 103, 126, 133, 143, 157, 175.
- **Locked to the cuts:** the swaps at 55, 89, 126 and 175 fall on the cut frames.
- **Last word:** "gnomes" holds to frame 226 (3.767 s, 0.35 s after the last voice sample), so the silent hero hold
  ends clean. Set `hold_last_to_end: true` to keep it to 5.0 s.
- **Style (bible §8.1):** white, 96 px, 5 px black outside stroke, black 90% shadow (+5, +5, blur 9), centred at
  x 540, baseline y 1385, no animation.
- **Font:** Montserrat ExtraBold is not installed offline; the fallback is DejaVu Sans Bold.

---

## 5. QA (STORYBOARD_RULES §7, adapted to 5 s; `make_test5_board.py` prints it)

| Check | Result |
|---|---|
| Cut minus naming-word onset | s02 -23 ms, s03 -17 ms, s04 -18 ms, s05 -23 ms (window -100 to +33): **pass** |
| Sentences opening on a cut | 2 of 2 (frame 0 and "They"): **pass** |
| Shot lengths | 0.57-2.08 s (min 0.35, max 2.3): **pass**. Median 0.82 s: hook pace |
| Every shot moves; opener is an accent | s01 crane accent, then 4 linear pushes: Z 0.19 / 0.16 / 0.20 / 0.28 (all in 0.08-0.32). s05's +28% is the character-intro push: **pass** |
| In-shot events on the word (±1 frame) | glint frame 104 vs "die" 1.738 s (-0.28 frame); burst + snap frame 134 vs "turn" 2.228 s (+0.32 frame): **pass** |
| Decal swaps held ≥ 0.4 s, at most 2 per shot | swaps only on cuts (Grandma `content` held 0.62 s); the human → gnome snap is hidden under the burst: **pass** |
| Creature low, close shots | s05 low, from 0.9 studs; 2 of 5 shots close (CU s03, CU/ECU s05) |
| No set-up repeated back to back | s02 and s04 show the same swing from opposite front sides, low vs eye level, and are not adjacent: **pass** |
| Captions inside -2..+1 frames of the onset | all 10 swaps after the first sit at -0.7 to -1.4 frames: **pass** |
| Grade or location change only on a sentence start | one location and one P1 grade family; s01 is the establishing shot of the street the porch and lawn belong to: **pass** |

---

## 6. Decisions and deviations (for the owner and the next stages)

1. **Night opener instead of the dusk deck chair.** STORYBOARD_RULES §6.1 plans the episode's frame 1 as a dusk deck
   chair (the loop match). This test follows the brief: a TF-style night look with the five suggested beats. If the
   owner approves, the episode can open this way or keep the §6.1 loop opener.
2. **The "don't die" beat** is a reaction CU with the content face on the cut and a glint on "die". It is not an in-shot
   face swap, because a swap 0.25 s into a 0.62 s shot would break the bible's 0.4 s hold rule.
3. **The transformation happens on the swing**, where the audience just met the couple: two gnomes on a porch swing, cute
   and clear in 0.8 s. "garden GNOMES" then cuts to Grandpa-gnome in his garden spot facing the house, which is the
   series rule.
4. **The lantern stays unlit** in every shot, and the gnome neither blinks nor turns its head. These are plot devices:
   the lantern lights at 41.76 s, the first blink is at 20.55 s. The warm key on the gnome comes from the bedroom window.
   If the owner wants the TF glow in the test anyway, the one-line change is `lanternLightUp(t, 3.75)` in s05 with a
   "tink" cue. That would spend the plant.
5. **Gnome look.** The kit's `grandpa` preset (red pointed hat, full beard, navy coat that matches human Grandpa's
   cardigan) is used, as the kit README decided. The script's fishing-hat version is `grandpaFishing`.
6. **SFX density.** There are 3 events in 3.4 s of voice (whoosh, shimmer, poof) plus the bed. That is above the
   episode average (6-12 per minute) because the hook holds the opener accent and the magic snap; the rest of the
   episode returns to sparse.
7. **The silent tail of 1.6 s** exists only because the test is 5 s long. In the episode, line 02 starts at 3.59 s and
   s05 would end there.
