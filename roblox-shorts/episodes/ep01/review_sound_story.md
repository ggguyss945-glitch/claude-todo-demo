# EP01 first cut: sound, sync and story-clarity review

Reviewed:
- `scratchpad/rbx/ep01/final/ep01_clean_1080p60.mp4`
- `scratchpad/rbx/ep01/final/ep01_captions_1080p60.mp4`
- the stems and `ep01_mix_report.json` beside them

This is a read-only review: no repo or render file was changed. The measurement scripts, JSON results and QA grids are in `scratchpad/rbx/ep01/review_sound/`:
- `audio_an.py` / `audio_an2.py`: masking, cue sync, gaps, clicks and beds
- `ref_floor.py`: loudness floors against the four references
- `video_events.py`: the picture-change frame of every timeline event
- `caption_check.py`: caption swaps in the burned file
- `grids.py`: contact grids in `grids/` and `det1`-`det5/`

## Verdict

The **sound and the sync are ready**:
- Loudness is in the reference range.
- A/V offset is 0.
- Every cut lands 8-43 ms before its first word.
- Every SFX transient lands within 1 frame of its event.
- All 433 caption swaps land on their planned frame.
- There are no gaps over 0.44 s and no clicks in the SFX or bed buses.

The remaining sound items are minor and about taste: density, a few stressed words under hits, and the missing music floor.

**Story clarity is not ready.** Five beats show something other than what the narration says:
- **The plastic decoy looks the same as Grandpa** (s49-s51), so "Gulp. Gone." reads as Grandpa being eaten.
- **The what-if window does not go dark** (s46).
- **"I wasn't small anymore" shows the hero small** (s71).
- **The "mid-blink" payoff is tiny and sits in the caption band** (s93).
- **Grandpa's tear cannot be seen** (s30).

The flashback grades and the 60-year epilogue read clearly, and the loop match works. Fix the five majors before any re-render. None of them touches s01-s05 or s09.

## 1. Measurements

### 1.1 Loudness (BS.1770 / ffmpeg ebur128)

| File | Integrated | LRA | 100 ms floor p2 / p5 / p10 (LUFS) |
|---|---|---|---|
| EP01 clean mp4 (AAC) | -16.0 LUFS | 1.4 LU | -34.5 / -31.5 / -27.8 |
| EP01 captions mp4 (same audio) | -16.0 | 1.4 | same |
| Tooth Fairies | -17.5 | 3.0 | -25.5 / -23.4 / -21.5 |
| Awake at Night | -16.9 | 3.3 | -24.6 / -23.1 / -21.4 |
| Porch Night | -13.7 | 2.1 | -20.6 / -18.6 / -17.0 |
| Clown Gate | -17.2 | 3.6 | -26.4 / -24.4 / -22.6 |

- **Level:** inside the reference range. True peak is -1.1 dBTP (AAC); the mix is -1.2.
- **Floor:** between words our mix drops 8-14 dB lower than any reference, because all four references have a music bed and we have none. Our beds sit about 20 LU under the voice (median momentary -36.5 LUFS).
- **Silence:** the only stretch under -40 LUFS is the planned s27 silence beat (28.87-29.73 s; 10 ms RMS minimum -66.5 dBFS at 29.48 s).

### 1.2 Voice intelligibility

| Measure | Value |
|---|---|
| Voice minus (SFX + beds), K-weighted momentary 400 ms, during speech | median 19.2 dB, p5 7.9 dB; 8.2 % of speech under 10 dB, 3.0 % under 6 dB |
| Per word, 300-4000 Hz band, 434 caption words | median 21.9 dB; 47 words under 12 dB, 20 under 6 dB |

Most low per-word values are short function words whose window falls in a gap, where the bed dominates. The real overlaps are the stressed words that a hit sits on (R7 puts events on the word):

| Word | Time | Band SNR | Cue |
|---|---|---|---|
| "moved" | 37.28 s | 5.0 dB | SUBBOOM |
| "lit" | 41.76 s | 5.1 dB | TINK_WHOOSH |
| "lit" | 45.22 s | 5.8 dB | TINKS |
| "turned / his / head" | 66.76-67.11 s | 8.6 / 9.0 / 8.3 dB | GRIND |
| "gulp" | 58.87 s | 9.8 dB | GULP (onomatopoeia, acceptable) |
| "flared" | 87.92 s | 9.8 dB | FWOOM second pulse |
| "blinked" | 99.89 s | 10.2 dB | TIK |
| "window" | 112.69 s | 8.8 dB | POOF_SOFT + crickets fade-in |

- All of these stay intelligible.
- The SUBBOOM rumble is the one loud masker (see the defects table).
- The whispered lines were not flattened: the phrase leveller's gain was +1.5 to +3.4 dB on every line, so the whispers keep the same level offset they have in the raw take.

### 1.3 SFX density and taste against the references

- **Density:** 25 events (34 placements) in 113.3 s, which is 13.2 events/min.
- **Against the bible:** the target is 6-12 events/min.
- **Against the references** (clear SFX, bible section 8.2): TF 2 in 131 s (0.9/min), AW about 3.1/min, PN 3.6/min, CG 3.8/min.
- **Two clusters:**
  - 36.96-45.22 s: SUBBOOM, CRUMBLE, PLINK, FLASH, SNIFF, SNIFF_BIG, TINK_WHOOSH and 4 TINKS (11 hits in 8.3 s).
  - 86.86-92.23 s: FWOOM, PASS, 6 DEFLATE and 5 BLIPS (13 hits in 5.4 s).
- **Audibility:** every placed cue is audible above 250 Hz, so it survives a phone speaker; its best band clears the voice and beds by 9-38 dB somewhere in its first 400 ms.
- **Source:** 22 of the 31 cue types are synthesised (`synth.py`). That includes the two signature hits the bible asks for: FWOOM (light-up) and the TINK_WHOOSH.
- **Library alternatives:** the extracted Epidemic folder has `ES_Magic, Shimmer, Magic Spell, Bright, Shimmer` and `ES_Magic, Spell, Swell, Reversed Cymbal`, which is exactly TF's "whoosh + bright shimmer". These need an ear A/B; I did not listen.

### 1.4 Sync

| Check | Result |
|---|---|
| Cut minus first-word onset (96 cuts, refined onsets) | -8 to -43 ms, median -16 ms (rule: -100 to +33): pass |
| SFX transient vs event (band-limited onset, every hit) | within ±1 frame, with two physically correct exceptions: LATCH +2.2 frames lands on the gate closing (picture f1070); SLAP_STICKER +2.7 lands on the 4-frame slap (f1655). PASS is a pass-by whoosh peaking 6 frames before f5348 with no visible edge, so that is fine |
| Picture event vs word (frame-difference peak) | 0-2 frames for s04 snap, s14 bonk, s18/s75/s86 blinks, s20/s61 torch, s23 wink, s25 sticker, s32 lift, s34 bulge, s36 eyes, s38 lantern, s46 window, s49 lift, s51 gulp, s64 stop, s76 "go", s77 second pulse, s91 ping. The FWOOM picture peak f5217 equals the SFX peak (86.944 s) |
| A/V | offset 0 samples; both streams 113.300 s |
| Captions in the burned file | 433/433 swaps on their `f0` (error 0); lead -1.5 to +0.3 frames against the onset (rule -2 to +1); band never empty; glyphs at y 1308-1416 (band 1260-1420) |
| Voice gaps | the longest is 0.44 s (s39 after "edge"), then 0.42 s (before "Every") and 0.37 s (s27 silence beat). All are under TF's 0.64 s |
| Clicks | none in the SFX or bed buses (30 ms crossfades are clean). One mouth click in the raw VO at 43.587 s (start of "Down"): a 2-sample spike of +0.22, -17.7 dBFS above 8 kHz in the mix |

### 1.5 Captions against the script (`scripts/EP01_VOICEOVER.md`)

All 434 words match the script except "six" → "6", which is correct. Problems:
- **Digits:** "nine" is spelled out twice (22.59 s, 27.93 s). The bible's digits rule lists "9".
- **"Theo's sent" (105.0 s):**
  - The voice says "Theo sent". The frication between "Theo" and "sent" lasts 110 ms with no voiced /z/, the same length as the single /s/ in "same" (110 ms) and "socks" (120 ms).
  - The ASR also hears "Theo", and s91's phone UI reads "Theo sent a photo".
- **One-frame and short words:**
  - Two words flash for 1 frame: "at" (f1909, onset 31.830, after "the" at 31.828) and "the" (f3659, 60.997, the same onset as "flowers").
  - 9 more words show for only 2-3 frames.
  - In both 1-frame cases the cause is an onset collision in `word_onsets.json`.
- **Speaker colours** are correct: Grandpa yellow for s23 and s24, hero orange, Theo blue.

### 1.6 Story clarity, beat by beat

Rated from one frame per shot (after its last event) plus about 50 detail frames, at phone size, from the captioned file.

**Reads clearly:**
- The world rules: s06/s07 grandma shrinks, s10 the board, s11 the sign, s12-s13 the dog and hole, s14 bonk, s15 family carry, s18 blink.
- The sepia flashback: hue 18-47° and saturation 0.32-0.41, against 240-275° and 0.44-0.62 for the present night.
- s26 the clock at 9:00, s27 the empty ring.
- The reveal: s34 bulge, s36 reflector eyes, s38 lantern, s39 ring.
- s44 Theo's 6 badge, s47 the waiting gnome, s48 the 11:52 clock.
- s56-s58, s65 wet eyes.
- s67 B&W 1960s (saturation 0.10).
- s73-s76, s79, s82-s88, s89 the gnome facing the truck.
- The epilogue: s90 Polaroids "19th / 34th spring", s91 the phone, s94 "I'm 71", s95/s96 the jump-cut shrink.

**The 60-year time jumps** read clearly at s19, s67 and s90-s94. They read weakly at s66 (not graded sepia) and at s68/s69 (the child in the window cannot be seen).

**The hypotheticals do not read** (s46): see the defects table.

**The ending loop works:**
- f6797 is an ECU of the old man's face. Its centre is at about 0.54 W, 0.60 H and it is about 0.70 W wide. Frame 0's gnome face is at about 0.57 W, 0.53-0.58 H and about 0.72 W wide.
- Both frames have the same night sky and stars.
- The voice ends at 112.92 s and the picture holds 0.38 s more under the crickets. On the loop, the W1 whoosh and "In this world" follow.
- What is missing is that the last line's noun, "window", is never on screen.

## 2. Defects

Severity: **major** = the picture contradicts or hides what the narration says at a key beat; **minor** = polish or taste.

| # | Shot / time | Sev | Problem | Fix |
|---|---|---|---|---|
| 1 | s49-s51, 56.33-59.70 s (and s12) | major | Mom's plastic gnome is a clone of Grandpa: red hat, blue coat, white beard, even a lantern (f3533). Only a green base differs. In s50 the hero leaves frame with Grandpa barely visible, so "Gulp. Gone." reads as Grandpa swallowed until s56/s57 show him in the hero's arms | Give the plastic gnomes their own palette and finish: pink or teal hat, yellow coat, flat dot eyes, a bright orange $4.99 sticker on the chest, glossy one-colour plastic, no lantern. Change `K.makePlasticGnome` so s12, s41 and s49-s51 all change. In s50, keep Grandpa (lantern lit) clearly in the hero's arm until he exits |
| 2 | s46, 51.57-53.68 s | major | The what-if does not read. On "dark" (f3186) Theo's window only dims (window luma 116 → 74, p95 178 → 120) while the whole frame dims about 15 % (59 → 50), so the window is still the brightest thing on the left. The hero barely moves, the truck is not in frame, and nothing marks the shot as imagined. THUD_LOW is dropped by the bible profile | <ul><li>Window off completely (emissive and interior light 0, ceiling stars off); no global dim.</li><li>Show the hero stepping toward the truck: frame it at the right edge, or truck the camera.</li><li>Grade the shot as imagined (about 50 % desaturated, cool, vignette, light edge blur), then cut back on "Leave" to the normal grade with the window lit.</li><li>Put THUD_LOW back on f3186.</li></ul> |
| 3 | s71, 79.72-80.87 s | major | On "I wasn't small anymore", the hero's face is small in the window opening (about 0.2 of the frame width, behind the curtains). The picture says the opposite of the line | Move the hero to the glass so his face fills 60-70 % of the window pane; lower the camera so sleeping Theo is small in the foreground (board intent). Push +19 % as planned |
| 4 | s93, 108.27-109.15 s | major | The "always mid-blink" payoff gnome is about 0.17 of the frame width in the bottom-right corner. His eyes are at about (810, 1408), inside the caption band and touching the "mid-blink" caption | Reframe the photo as a close two-shot with the gnome large in the lower-middle foreground (eyes at y 1000-1150, lids 0.55 clearly visible), Theo at 66 behind, and the granddaughter in the window above. Nothing below y 1250 |
| 5 | s30, 33.20-34.35 s | major | Grandpa's tear (from f2040) cannot be seen even at full resolution: a small white drop runs over the white beard and moustache | Make a bigger glossy tear (blue-white with a dark rim and a strong specular). Start it at the inner eye corner over skin, run it down the cheek above the beard line, and finish the push on an ECU of that eye |
| 6 | s34-s37, 36.96-40.86 s | minor | The SUBBOOM rumble is the loudest bed under speech: +4.6 LU over the voice at 37.5 s, then 1-6 LU under it through 40.0 s ("Dozens of mounds, with eyes like bike reflectors"). The bible ends the rumble at about 39.5 s. "moved" has a band SNR of 5.0 dB | Keep the hit; drop the rumble tail 6 dB from 37.9 s and fade it out by 39.5 s; HPF the tail at 35 Hz |
| 7 | s38 41.76, s40 45.22, s59 66.6-67.3, s77 87.92 s | minor | Hits on stressed words: "lit" 5.1 / 5.8 dB, "turned his head" 8.3-9.0 dB, "flared" 9.8 dB | Raise the ducker margin from 12 to 15 dB and its maximum gain reduction from 10 to 14 dB for TINK_WHOOSH, TINKS, GRIND and FWOOM, or start their transients 2-3 frames before the vowel |
| 8 | whole cut; clusters 36.96-45.22 s and 86.86-92.23 s | minor | SFX density is 13.2 events/min: above the bible's 6-12 and 3.5-15 times the references' clear-SFX rate (TF, the owner's favourite, 0.9/min). The two clusters hold 11 and 13 hits | Before the music goes in, trim to about 9/min. Drop the CRUMBLE, PLINK, FLASH and SNIFF_BIG layers, the s53 SNIFF, RATTLE, GRIND_SOFT and POOF_SOFT, and cut DEFLATE from 6 hits to 3 |
| 9 | s77 86.58 s, s38, s40 (signature hits) | minor | The bible's signature light-up hit ("whoosh + bright shimmer", TF 110.75-112.6 s) is synthesised, along with TINK_WHOOSH, TINKS, GULP and ENGINE. Library alternatives are in the extracted folder | A/B by ear: build FWOOM from `ES_Magic, Spell, Swell, Reversed Cymbal` plus `ES_Magic, Shimmer, Magic Spell, Bright`, keeping the 0.28 s sync point; keep whichever sounds closer to TF |
| 10 | s97, 112.69 s | minor | POOF_SOFT (the dandelion) has no visible source: the dandelion is outside the ECU (no picture change at f6761). The bible requires every SFX to sit on a picture event that is on screen | Drop POOF_SOFT, or let a few seeds drift across his face from f6761 (it would echo frame 0's sparkles) |
| 11 | whole cut | minor | With no music, the floor between words is 8-14 dB below every reference's, so the cut sounds dry between phrases | Owner action. Preview with `mix.py --music <bed>` at -24 LUFS and re-limit at the final mux (mix.py's note); the planned music drops are in `music_cues.json` |
| 12 | 18 cuts, e.g. 5.03, 12.12, 13.73, 17.92, 19.35, 48.52, 50.15 s | minor | The ambience bed switches with a 30 ms crossfade on cuts, with level jumps of 5-10.5 dB (s16 → s17 at 19.35 s: -10.5 dB). In the montage this is a sound change on almost every cut, audible on headphones | Use 150-250 ms crossfades, match the bed levels within ±3 dB (A_ROOM -41.9 against A_DAY -34.6), and hold one bed across a sentence group |
| 13 | s27, 28.87-29.73 s | minor | The silence beat drops the master to about -40 LUFS (10 ms RMS minimum -66.5 dBFS). Without music it can sound like a dropout on a phone | Dip the crickets by 8-10 dB instead of 14, or let the owner's music drop carry it |
| 14 | s40, 43.587 s | minor | Mouth click in the raw VO at the start of "Down" (2-sample spike, -17.7 dBFS above 8 kHz in the mix) | De-click in `voice_track` (1 ms interpolation or spectral repair at 43.586-43.588 s) |
| 15 | s29 31.83 s, s53 61.00 s (and 9 more) | minor | "at" (f1909) and "the" (f3659) flash for 1 frame; 9 more words show for only 2-3 frames. The cause is non-monotonic or colliding onsets ("at" 31.830 is after "the" 31.828) | In `make_captions.py`, force onsets to be monotonic (use the ASR time for "at": 31.76), give every word at least 5 frames by taking time from the previous word, and merge any function word that cannot get 5 frames into the next word |
| 16 | s19 22.59 s, s26 27.93 s | minor | "nine" is spelled out; the bible's digits rule lists "9" | Caption "9" |
| 17 | s91, 105.0 s | minor | The caption says "Theo's sent"; the voice and s91's own phone UI say "Theo sent" | Caption "Theo sent", or re-record to match the script |
| 18 | s29, 31.45-33.20 s | minor | The thumbnail frame: the gnome is cut by the left edge (hat and back only) and the truck is an unreadable white panel and ramp at the right edge | Gnome three-quarters back, whole, in the lower-left third; the truck's open back with the lit cargo and the BALCONY GNOME box in the upper-right third; property-line shimmer visible |
| 19 | s97, 111.78-113.30 s | minor | "I've already picked my window": no window is ever on screen (the reverse angle hides it), so the last noun has no picture (R2) | Open s97 through the window: sill, curtain edges and warm glow in the foreground, which leave the frame during the push. The ending framing then still matches frame 0 |
| 20 | s17, 19.35-20.23 s | minor | On "I say goodnight", the view through the window is bright and day-like (lit lawn and fence) against the purple night room, a fault the bible lists | Light the exterior seen through the glass with nightLawn about 1.5 EV under the room; keep the gnome lit by the window spill |
| 21 | s21 23.55-23.98 s, s62 69.60-70.30 s | minor | The slippers cannot be seen: the feet are buried in grass at y about 1260-1350, behind the "slippers" caption | Raise the feet into y 700-1100 (camera a little higher, tilt down, a short-grass patch) so the tartan slippers are whole |
| 22 | s48, 55.25-56.33 s | minor | The LEAVE 6 AM note is cut by the frame edge ("EAVE 6 AM", then "AVE AM" at the end of the push), which loses the "dawn" clue | Move the note 150 px toward the centre, or reduce the push so "LEAVE 6 AM" stays whole |
| 23 | s66, 74.02-74.90 s | minor | The flashback is not sepia: hue 254°, against 18-47° for the other sepia shots, so it reads as the present | Apply the `sepia` preset to s66 the way s61-s64 and s68 have it |
| 24 | s63 → s64, 70.90 s | minor | Match-cut teleport: in the same top-down framing, Grandpa jumps from the bottom of the loop to the kink at upper left | Shift the walk phase of s63's `fb_lap` callback so Grandpa reaches the kink on s63's last frame (s22 can stay as it is) |
| 25 | s68-s69, 76.40-78.67 s | minor | "For 60 years, whoever was small in that room": neither the 1990s girl nor Theo can be seen in the window, and the torch beam on the sill is not visible | Bring the bed and child into the lower window pane at readable size (head at least 80 px) and put the beam or lantern light across the sill |
| 26 | s78, 88.58-89.75 s | minor | "light rolled across the lawn": the wall of light does not read, because the whole lawn is already gold (no visible edge at f5348) | Keep the lawn ahead of the wave in the night grade so the front edge (bright band plus sparkles) sweeps visibly through the frame |
| 27 | s31 34.35 s, s74 82.60 s (and s85) | minor | The "heartfelt" face decal (half-lidded eyes with lashes, lopsided smile) reads smug or sly at phone size on the whispered tender lines | Use content (^^) or o-wonder with soft raised brows, or redraw "heartfelt" without lashes and with a symmetric soft smile |
| 28 | s37, 39.95-40.97 s | minor | The star-nosed snout, purple with tentacles, reads as a flower; nothing says "mole" | Add a dark furred rim and two pale digging claws at the turf break, and push the snout hue pinker |
| 29 | s57, 64.10-65.43 s | minor | Continuity: the board behind the hero reads "FOR ... 3 BED / COMES W..." with no SOLD sticker after s25 | Add the SOLD sticker to the board asset after s25 |

## 3. What passes (keep)

- **Loudness:** -16.0 LUFS integrated, -1.1 dBTP, LRA 1.4. The references run -13.7 to -17.5.
- **Mux:** A/V offset 0, both streams 113.300 s, the captioned file's audio is identical.
- **Cuts:** all 96 land 8-43 ms before their first word; 67 of 69 sentences open on a cut.
- **SFX sync:** every hit within ±1 frame of its event, and every picture event within 0-2 frames of its word.
- **Captions:** frame-exact swaps, the band never empty, glyphs inside the band, speaker colours correct, ASR forms replaced by the script.
- **Voice:** continuous (longest gap 0.44 s), no masking in the speech band beyond the items above, whispers not flattened.
- **Story:** the world rules, the sepia/B&W flashbacks, the reveal set piece, the dawn scene, the epilogue time jump and the loop match all read.
