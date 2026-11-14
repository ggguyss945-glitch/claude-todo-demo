# REF_MIRROR: what the two new references measure, and what it means for the mirror film

Sources: `_work/ref/diver.mp4` ("If The Diver Starts Banging On The Glass... RUN FAST", 685 s) and
`_work/ref/hazmat.mp4` ("If A Hazmat Team Locks You In A Grocery Store... DON'T MOVE", 465 s). Both are 854x480, 30 fps,
from the same channel (same caption, header and music template). We take style only: no characters, art, layouts or scenes.

Pixel values are at 854 px width unless marked. Multiply by 3 for our 2560x1440 output. Speeds marked "@1280"
can be compared directly with VISUAL_SPEC.md. The engine's design space is 1920x1080, so multiply fractions of H by 1080.

Method: cut detection on 30 fps edge maps, Farneback flow at 6 fps, and colour stats on 1 fps frames grouped into
hand-checked scene families. Audio was split into voice and bed (music plus SFX) with UVR MDX-Net, measured with
`analysis/measure.py` (the same as AUDIO_SPEC), and transcribed with timestamps by a NeMo transducer.
Scripts are in `analysis/refmirror/` and the data is in `_work/ref/data/`.

---------------------------------------------------------------------------------------------------------------------

## 1. Hook: the first 30 s (both references use the same structure, and so does our narration)

| beat | diver | hazmat | **ours (from _work/align/timeline.json)** |
|---|---|---|---|
| Title phrase ("If X... DO Y") | 0.1-6.1 s; "run fast" spoken at 5.5 s | 0.1-7.8 s; "escape now" at 7.0 s | 0.16-5.41 s; "wipe the glass clean" at 3.92-5.4 s |
| Title tag on screen | RUN FAST at 5.60 s, in sync with the word, held 1.07 s | ESCAPE NOW at 6.80 s, on the cut 0.2 s **before** the word | (do the same: WIPE THE GLASS at about 3.85 s) |
| 2-3 more commands, **one shot per clause** | 7.1-12.2 s, cuts at 6.67/7.93/8.93/9.57/11.03 (shots 1.0-1.5 s) | 8.5-17.7 s, cuts at 8.43/10.73/13.2/16.2, plus a red X and the DON'T WAIT tag at 9.7 s | 5.58-12.67 s ("Don't wait...", "listen to what they're asking for") |
| Premise or twist line | none | 18.7-23.6 s "...that something knows how to dress like them" | 12.94-19.28 s "...he was still waiting for breakfast." |
| Time or place card | 12.4 s sign card "SHARK FEEDING / TODAY 2:00 PM" | 24.2 s clock card "TUESDAY 8:46 PM" (clock icon, day, big time, subline) | 19.40 s "It's 11:57 at night" -> time card |
| Cuts in the first 30 s | **17** (34/min) | **11** (22/min) | target 13-16 |
| Loudest bed moment | 5.7 s, the RUN FAST hit (+4.5 LU over voice, the loudest second of the whole film) | rule cards | the WIPE THE GLASS hit should be one of the 3 loudest |
| "There are seven rules" + teaser | 106.9 s, "pay close attention to the fourth one" | 72.95 s, "the third rule is the one most people miss" | 121.2 s, "Pay attention to the fourth" |
| Rule 1 | 117.5 s | 81.3 s | **130.2 s**: our setup is the longest, so it needs the most inserts and cuts |

The setup between the hook and rule 1 is a normal world shown in fast establishing shots (crowd, tank, aisles),
then one odd detail ("until the diver suddenly drops his bucket", 33.5 s), then escalation.

## 2. Cutting

| | diver | hazmat | police refs (VISUAL_SPEC) | **target for us** |
|---|---|---|---|---|
| cuts/min | 24.1 | 28.5 | 15-28 | **26** (about 300 cuts in 698.7 s) |
| shot length p10/25/50/75/90 (s) | 0.77/1.49/2.33/3.22/4.22 | 0.97/1.43/2.07/2.63/3.10 | 1.17/1.6/2.4/3.5/4.7 | **0.9/1.4/2.2/3.0/3.8** |
| shots < 1 s / > 4 s / > 6 s | 14% / 13% / 2% | 11% / 3% / 0.5% | | 12% / 8% / 1% |
| hard cuts / soft (dissolve) | 96% / 4% | 97% / 3% | 85% / 11% | **96 / 4** |
| cuts on a clause start (within -0.35..+0.15 s) | **68%** (chance 24%) | **58%** (chance 22%) | | **65%** |
| cut minus clause start (median) | **-0.28 s** | **-0.28 s** | | picture leads the voice by 0.25-0.30 s |
| punch-ins (same shot, scaled) | 0.8/min, x1.25 median (x1.08-2.4) | about 0 | | 0.8/min, x1.25-1.5, on a stinger |
| static glitch, 2 frames | into rule cards 1, 3 and 6, plus one at 75 s | 2 (75.3 s and 258.8 s) | 3% of cuts | into each rule card |
| light flashes (luma +40 levels, back within 8 frames) | 16 (camera-flash strobe every 0.6 s at 342-347 s) | 12 (emergency-light flicker at 72-81 s) | | about 1.5/min, clustered on a beat |

The cut rate stays flat across the film (cuts/min per tenth: diver 19-28, hazmat 25-35). The build comes from
content and sound, not from faster cutting.

## 3. Motion inside shots

| (6 fps flow, speeds @1280) | diver | hazmat | police | **target** |
|---|---|---|---|---|
| camera moving share | 0.57 | **0.80** | 0.50-0.77 | **≥ 0.80** |
| zoom-in / zoom-out share | 0.38 / 0.11 | 0.64 / 0.11 | 0.45-0.67 / 0.03-0.09 | 0.60 / **0.11** (pull-outs are reveals) |
| push-in %/s p25/50/75/90 | 1.6/2.9/5.2/10.7 | 1.6/2.8/4.8/9.6 | 1.4-1.7/2.3-2.8/3.7-4.8/5.5-9.8 | **1.6/2.8/5/10** |
| pull-out %/s p50/p90 | 2.1/8.6 | 3.2/16.6 | 2.4/10 | 3 / 15 (fast reveal pulls) |
| pan px/s p50/p90 | 23/52 | 16/48 | 14-17/48-56 | 18/50 |
| handheld (high-pass tx std, px/s) | 9.5 | 11.5 | 7.7-11.5 | 10 |
| subject motion > 30 px/s, share of time | **0.33** | **0.34** | 0.16-0.30 | **≥ 0.33** |
| **frozen frames** (nothing changes over 0.5 s) | 12.2% (runs up to 3.1 s on stairwell and door shots) | **0.8%** | | **< 1%: never** |
| shot moves (shots ≥ 1.5 s): push / push+pan / pull / pan / static | 27/21/3/6/43 % | 48/22/5/4/21 % | | the hazmat mix |
| push ease (cumulative at 0/.2/.4/.6/.8/1) | .03/.21/.43/.69/.87/1 | -.01/.15/.26/.54/.75/1 | .02/.20/.45/.67/.83/1 | linear, already moving on frame 1 |
| total zoom per shot % p50/p90 | 0.3/9.2 | 2.8/10.7 | 2.7-4.6/10 | 3/10 |

Diver "static" shots still have constant particle motion (rising bubbles, fish crossing, caustic light rays). Hazmat has
real camera moves on nearly every shot (perspective aisles with a push toward the vanishing point). The owner wants the
hazmat standard. The moving things to copy as **craft** (not as content):
- Ambient particle layers that never stop: bubbles (diver); dust in a flashlight beam is ours.
- Things crossing the frame: fish, carts, walking crowds, a shutter sliding down.
- Light sweeps: a flashlight cone sweeping at 8:30-8:34 (diver), strobing flashes, an emergency-light blink as a story beat (hazmat 312.7 s).
- Acting cycles: pounding on glass with impact strokes (`keys/acting_strips.jpg`), hands raised, arms pointing.
- Scale reveals: a cut from big red eyes in the dark to a wide tunnel with the same eyes small (diver 338 s), then pull-outs.

## 4. Characters and the entity

Grabs: `keys/diver_faces_a.jpg`, `keys/diver_faces_b.jpg`, `keys/hazmat_faces_a.jpg`, `keys/hazmat_faces_b.jpg`.
- **Normal people** are chunky, flat and friendly. Outline width on close-ups is 2-4 px (median about 3; **9 px at 2560**).
  At rest they have almond eyes with brown or blue irises (and lashes on women), easy open smiles with teeth, and pale or warm skin.
- **Fear is an eye swap**. The calm eye becomes a round white disc about 0.24 of head width with a pinpoint pupil
  (measured 0.18-0.24 of the eye diameter, smaller than the police film's 0.30-0.40). Brows go up and tilt, the mouth is a small
  "O" or a flat line, and sweat drops appear (guard at 9:08 and 9:10, cashier calm at 1:52 vs scared at 7:34).
  Bodies act big: both hands up, pounding, a hand over the mouth.
- **The entity uses a different graphic language from the people**, and that is the scare:
  - diver: a white scribbled line-art creature on near-black, two glowing red eyes (#c63449 core with a big soft glow), a glowing lure,
    and layers of jagged white teeth. It is shown in parts first (two red eyes in the dark at 5:34, a shadow, a light), and the full
    face only comes in the last 12% (10:00-11:16).
  - hazmat: no face at all. A black mask with two glossy red lenses and one scratch across the left lens as its identifier, used in
    a split screen against a normal suit with a visible face (3:28). The close-ups get bigger through the film (MCU 3:34, ECU 5:36, 7:14).
- The light on the entity gets the biggest glow in the film: the lure light halo is still 66% at 20 px@1280, against 3-7% on ordinary lights.

## 5. Palettes and lighting per scene type (1 fps frames, caption band removed)

| family | luma p1/p5/p50/p95/p99.5 | sat mean/p90 | hue | vignette r=.4/.6/.8/.95 | palette, most frequent first |
|---|---|---|---|---|---|
| diver tank (lit, blue) | 29/38/72/126/186 | 136/202 | 201° | .85/.79/.55/.35 | #25485b #2a5972 #1e3442 #296c8e #577380 #0e1218 |
| diver dark water (void, one light) | 8/10/19/30/78 | 209/235 | 209° | .95/.79/.58/.42 | #040d17 #051727 #0a2033 #123044 #29404f |
| diver tunnel (night blue) | 13/18/41/81/138 | 148/193 | 206° | .70/.54/.35/.26 | #0b1822 #152634 #233b4c #344d5f #607788 |
| diver entity in the dark | 4/6/13/72/163 | 138/202 | 226° | .59/.42/.22/.16 | #080c14 #26262f #55545d #58222f #cdd4d5 + red #c63449 |
| diver stairwell / lobby (lit interior) | 16/22/85/173/190 | 77-89 | 200° | .77/.65/.41/.25 | #1c282f #616d6e #8e938f #3a4e56 #207286 #e0dac8 |
| diver service corridor (grey, flashlight) | 9/14/30/88/166 | 35/64 | – | .62/.38/.22/.10 | #101111 #3a3c3b #1a1c1c #8f918c |
| diver red emergency (climax) | 14/18/44/74/150 | 113/188 | **306° (red on blue reads magenta)** | .77/.67/.42/.27 | #35212e #372f43 #2c0e17 #473f52 #793f4e |
| hazmat night exterior | 10/15/69/196/238 | 123/215 | 221° | .82/.60/.39/.26 | #0d1832 #45567b #2e3953 #757577 #d4d0ca + sodium #d9ba2c |
| hazmat bright interior ("normal") | 64/85/166/226/250 | 54/161 | – | .99/.87/.67/.48 | #adaead #7f8b94 #ccccc9 #e7e5e0 #556c74 #b79342 |
| hazmat dim emergency | 29/48/107/158/179 | 67/117 | – | .86/.76/.50/.30 | #14161f #6f6469 #8c7880 #584c4b #a7929a |
| face close-ups | 14-30/26-48/63-127/182-216/232-236 | 69-92 | – | diver .61/.52/.33/.20 | dark blurred background, the face is the brightest thing |

- Whole-video mean-frame vignette: diver **.74/.56/.34/.22** (the same as the police target of about 0.3 at r = 0.8),
  hazmat .95/.81/.60/.43. Even bright scenes get a visible darkening at the corners (0.48 at r = 0.95).
- Arc (luma by tenth): diver 57 59 46 49 **36** 61 82 67 51 55, with red share 0.1-0.8% until the last 20%, then **3.0 and 2.8%**.
  Hazmat stays bright (117-139), then the last tenth drops to **103** with red share at **8.5%** and saturation at 90 (from 47-80).
- There is no measurable grain: 0.3-0.5 levels, though this low-bitrate encode would hide fine grain. Edges are crisp
  (10-90% rise of 2.3-2.4 px@1280). There is no chromatic aberration.
- Glow: ordinary lights get a tight halo (excess 0.5/0.28/0.12/0.03 at 2/6/12/20 px@1280, so about 25 px radius at 2560).
  Entity lights get a wide halo (0.66 at 20 px, 0.16 at 30 px@1280). Diver tank shots have god-rays and caustics in every shot.

## 6. On-screen text and UI (grabs: `keys/rule_card_animation.jpg`, `keys/tag_x_animation.jpg`, `keys/ui_devices.jpg`, `keys/top_hud_band.jpg`)

- **Captions**: white bold uppercase, letter-spaced, with a soft dark shadow. Cap height **2.1% H** (10 px at 480, so about 22-23 px
  in the 1080 design space), centred on **y = 0.893 H**, always one line, 17-52% of W wide. Median **5 words** (p10/p90 2/8).
  Each lasts **1.5-1.7 s** (p10 0.9, p90 2.3-2.7). There are 30-33 per minute and they are on screen 88-91% of the time.
  **Captions are hidden while a rule card is up** (0.00 s of overlap on 14 of 14 cards).
  Our `hud.caption()` is already close (y 975/1080 = 0.903, cap about 2.0%). Move it to y about 964 and size it about 33.
- **Persistent header**: a faint top line reading "FILE 085 · THE MAIN TANK // RULE 1 OF 7" (or "INTRODUCTION") on the left and a
  **running timecode** "00:00:31:19" on the right. Cap height 1.0% H at y = 0.052 H, white at about **20% opacity**, with the
  "RULE n OF 7" part brighter. Our `hud.header()` sits at 47-59% opacity: drop it to about 20%.
- **Rule cards** (measured on all 14):
  - The card **appears 0.42-0.48 s before the narrator says "Rule"** and is cut **0.1-0.2 s after the rule sentence ends**.
    It is visible 4.5-5.4 s and there is no extra hold. The text writes on **word-synced with the narration** (ink grows from 5% to 100% over
    about 3 s in 0.5 s steps).
  - diver: a 2-frame static glitch, then a whiteboard held by two cartoon hands slides up (coverage 40% -> 93% in 0.17 s).
    The red marker title "RULE ONE" pops in 1.0 s after the card (0.07 s rise), then the grey hand-lettered statement writes on.
  - hazmat: a hazard sign slams in from about 140% scale, tilted -8°, settling in 6 frames with a glow outline.
    "RULE n" writes in, then the red keyword box ("DO NOT", "NEVER", "LOOK") comes first and the rest of the statement types word by word.
  - Both: a card is a **diegetic object from the story world** and is the brightest frame of its section (luma spikes in `sheets/curve_diver.png`).
    A LIKE / SUBSCRIBE button is shown bottom-left on the rule 1 and rule 2 cards.
- **Command tags** (DON'T WAIT, MOVE AWAY, STOP, DON'T TURN AROUND...): red bold text in a near-black box with a red outline
  (diver), or with hazard-stripe end caps (hazmat). They **pop in over 3-4 frames** with a scale overshoot and a soft glow,
  **land on the command word** (from 0.2 s before it to 0.1 s after), are held 1.0-1.3 s (up to 3-4 s when the shot holds), and
  sit top-centre (y 0.06-0.12 H) or next to the subject. There are 0.5-0.8 per minute.
- **Red X** over the forbidden action (a hand reaching for a handle, a crowd at the doors): a 1-frame red full-frame tint flash,
  a ring, then two strokes drawn in about 5 frames (0.17 s), held 0.7-1.5 s, and always on a "do not" line. There are 0.5-0.9 per minute.
- **Inserts**, about 1 per minute, each motivated by a line: setting card or signage, clock card, case-file document
  ("VISITOR INCIDENT REPORT" with a stamp), CCTV view ("CAM 07 · SERVICE CORRIDOR B2", timecode, REC dot), a control panel with a
  counter ticking 282 -> 000, a floor map with a YOU marker and a red danger zone, a diegetic sign held by a character, a name tag, and an ID label ("HM-6").

## 7. Sound (bed = music + SFX, LU relative to voice integrated)

| | diver | hazmat | police refs | **target** |
|---|---|---|---|---|
| mix LUFS / peak dBFS | -14.5 / -1.1 | -14.4 / -0.7 | -14.5 / -0.9 | -14 / ≤ -1.5 dBTP |
| bed integrated rel voice | **-11.0** | -12.7 | -12.5..-13.4 | **-11.5** |
| bed during speech, median / power mean | -12.3 / -6.4 | -12.9 / -9.1 | -13.5 / -9 | -12.5 / -7.5 |
| bed short-term p10/50/90 | -16.6/-10.1/-2.1 | -21.2/-11.7/-4.7 | -16.5/-12/-4.5 | -18/-11/-3 |
| bed LRA (LU) | **16.7** | **17.5** | 13-14 | **17** (more dynamic) |
| music present (tonal, bed > voice-25 LU) | 98.6% | 95.6% | 94-98% | ≥ 97% |
| narration share / breath gaps per min / gaps ≥ 1 s | 88% / 12 / 0 | 87% / 13 / 0 | 81-83% | (ours is continuous too: 187 wpm vs 166-170) |
| transients ≥ 4 dB per min | **15.2** | 9.2 | | **≥ 14** |
| hits per min (loud, ≥ 10 dB jump) / small foley per min | **6.6** / 8.6 | 1.9 / 7.2 | 1.3-3.8 / 3.7-7 | **5 / 9** |
| hit peak rel voice p50 / max | +4.0 / +11.0 | +0.3 / +6.7 | +0.3..+3.7 / +5..+9.7 | +3 / +10 |
| hit contrast over the bed just before | 15.0 dB | 15.1 dB | 14.4-15.8 | ≥ 15 dB (dip the bed first) |
| hits under narration | 77% | 53% | 64-76% | 70% |
| rises ≥ 8 LU per min / median length | 2.63 / 13.2 s | 2.71 / 13.0 s | 2.1-2.8 / 13-15 | 2.7 / 13 s |
| silences (bed -10 dB ≥ 0.5 s) per min / median length / depth | **2.1** / 1.23 s / 14.6 dB | 0.9 / 1.18 s / 12.4 dB | 1.1-1.7 / 1.5-1.8 / 13-17 | **1.8 / 1.2 s / 14 dB**, always under a line |
| silence ends on a cut / followed by a hit | 46% / 17% | 57% / 0% | 0-41% / 6-30% | half on a cut, 1 in 5 into a hit |
| bed < 250 Hz / 250 Hz-4 kHz / > 4 kHz | **87.5 / 12.2 / 0.3** | 82.5 / 17.3 / 0.2 | 60-78 / 21-40 / 0.3-0.7 | **85 / 14 / ≤ 1** |
| octave dB rel 1 kHz (63...8k) | +11 +9 +2.5 +1.6 0 -4.8 -11 -14 | +9.4 +6.1 +3.2 +2 0 -3.8 -8 -17 | | +10 +7 +3 +2 0 -4 -9 -15 |
| key / strongest pitch classes | A minor: **A, A#, E** | D minor: **D, A, D#** | D minor: D, A, D# | minor drone with a flat-2 rub (Phrygian) |
| pulse clarity / harmonic share | 0.06 / 0.97 | 0.05 / 0.97 | 0.04-0.07 / 0.96 | unpulsed drones |
| hit decay T60 / voice tail | 1.7 / 0.44 s | 1.4 / 0.43 s | 0.8-3.3 / 0.4 | 1.5-2 s / dry voice |
| bed width side-mid / L-R correlation | -11.8 dB / 0.88 | -11.2 / 0.86 | -10 / 0.83 | -11 / 0.87 |

**Sound on picture events** (bed peak in [0, +0.4 s] minus the mean over [-1.5, -0.3 s], and the share with a ≥ 8 dB transient):

| event | diver | hazmat | random cut (baseline) |
|---|---|---|---|
| rule card appears | +4.5 dB, peak at -0.4 LU rel voice, 29% | **+6.6 dB, peak +0.6 LU**, 29% | +0.3..+1.1 dB, 0-5% |
| command tag | +4.1 dB, 33% | +1.0 dB | |
| red X | +1.8 dB, 17% | +2.0 dB, 25% | |
| punch-in | +2.7 dB, peak -4 LU, 22% | – | |

The **rule card is the main sound event**. Aligned on the card (median of 7 cards, LU rel voice, 0.5 s steps):
diver -16 at -7 s -> -5 at -2 s -> **-2 at 0** -> -7 at +3 s -> -10 at +5 s. Hazmat -15 at -4 s -> -9 at -1.5 s -> **0 at +0.5 s** -> -8 at +3 s -> -14 at +5.5 s.
So there is a **4-7 s riser of about +13 LU that peaks at voice level on the card**, then a 4-5 s decay. The loudest seconds of the hazmat bed
are the rule cards (132.9, 194.5, 250.6, 456.4 s). The loudest second of the diver bed is the title hit at 5.7 s. Several cards are preceded
by a drop-out of the bed: diver 5:52, 7:05 and 11:10 drop to about -27 LU (`sheets/curve_*.png`).

## 8. Against the police film's specs: keep and change

**Keep** (the new references confirm them): the clean flat vector look with uniform dark outlines (9-12 px at 2560), no grain and
no chromatic aberration; the strong vignette (0.34 at r = 0.8 for dark films); the push-in speed (median 2.8%/s, near-linear ease, already
moving on frame 1); about 96% hard cuts; captions at the bottom; a mix at -14 LUFS with the voice dry and in front; music under everything;
13 s swells at about 2.7 per minute; an unpulsed minor drone with a flat-2 rub (D-A-Eb works, since hazmat uses the same as the police refs).

**Change**:
1. **Cut faster and on the words**: 26 cuts/min instead of 20-25, median shot 2.2 s, p90 3.8 s. One shot per clause in the hook.
   65% of cuts on a clause start, with the picture 0.28 s ahead of the voice.
2. **Never freeze**: frozen frames under 1% (18-44% of police-ref shots were "static"). The camera moves 80% of the time, the subject or
   effects move fast 33% of the time, and 11% of moving time is pull-out reveals.
3. **Rule card timing comes from the alignment, not from fixed constants**: appear 0.45 s before "Rule", title +1.0 s,
   text word-synced, cut 0.15 s after the sentence. Today `RULE_TYPE` is 3.0 and `RULE_HOLD` is 1.5 (`engine/hud.py:34`): drop the hold.
   Make the card **a story object** with a 2-frame static glitch in, hide captions under it, and put LIKE/SUBSCRIBE on rules 1-2.
4. **Captions** 2.1% H at y 0.893, one line of about 5 words, hidden during cards. **Header** at about 20% opacity, adding "RULE n OF 7" and a running timecode.
5. **Fear eyes** with smaller pupils (0.2 of the eye, not 0.3-0.4). Give the entity **its own drawing language** and reveal it in stages.
6. **Sound density**: 14 or more transients per minute (the police target was 3 hits + 5 foley = 8), about 5 hits per minute on reveals, tags and punch-ins,
   9 foley per minute, bed LRA 17 instead of 13-14, a darker bed (85% below 250 Hz), and a riser into every rule card that peaks at voice level.
7. **Inserts** about once a minute, and command tags plus red X about 1.3 per minute in total.

## 9. Do this: rules for the director (mirror film)

1. **Hook, 0-30 s**: build 13-16 shots. Show WIPE THE GLASS as a tag at about 3.85 s with the biggest hit of the opening, a red X on
   "Don't wait to see who's coming up the stairs" (5.6 s), and a LISTEN tag on 10.7 s. Give the premise line (12.9-19.3 s) a
   slow push on the brother image with the bed dipped under it. Put the **time card "11:57 PM"** at 19.4 s (clock icon, day, big time,
   and a subline such as "CAMP · DEMOLITION TOMORROW").
2. **Setup, 25-130 s, is our longest stretch** (refs 81-117 s): cut at 26/min and use about 6 inserts: mom's text "Check the pocket..."
   as a phone UI, the SAVE FOR THE MUSEUM crate stencil, a close-up of the cracked bell, the caretaker's house window, the towel-wrapped mirror,
   and Tess's phone face up on the sill. Put the "seven rules / pay attention to the fourth" line (121-125 s) on a punch-in with a hit.
3. **Rule cards are lipstick on glass** (our own story object, not a whiteboard or a sign): use a 2-frame glitch in, then a flashlight-lit silver mirror pane filling about 35% of
   the frame (it must be the brightest frame of its section, as the references' cards are), the red lipstick title "RULE ONE" at +1.0 s, and the statement written word-synced. Exit with a finger-wipe smear 0.15 s after the
   sentence. Show it 0.45 s before "Rule number N" (130.2, 204.0, 269.7, 350.8, 446.8, 542.5, 609.9 s). No captions under it.
   Put a riser of +13 LU over 5 s, peaking at voice level, under it.
4. **The header runs the in-world clock**: "CABIN 7 // RULE n OF 7" on the left at about 20% opacity and a timecode on the right that starts at 23:57:00
   at 19.4 s and runs in real time (it passes midnight at 199.4 s and reads about 00:08 at the end, which matches "just after midnight"). At 279.1 s ("the second hand on the cabin clock jerks backward"), make the
   header clock **tick backward** for 2-3 s. That is a cheap, story-true scare.
5. **Tess's countdown is an on-screen counter** (like the refs' panel counter): 60 -> 45 -> 20 -> 5 as a small pill in Tess's flashlight frame,
   with a tick SFX on each number she calls.
6. **Every shot moves**: a push of 1.6-5%/s by default, a pull-out for each reveal (the doorway, the eighth step, the woman), and dust always drifting
   in the flashlight beam. Things cross frame: the flashlight cone sweeps, the drop rises and falls, the sprinkler spits, footprints appear.
   Frozen frames under 1%: in the "time stopped" shots (Tess's steady beam), freeze the subject but keep the camera drifting at about 1%/s.
7. **The two sides of the glass get two palettes**. Our side at midnight is the diver tunnel/tank family (p50 luma 40-70, deep navy-teal
   #0b1822 #152634 #233b4c, hue about 205°, vignette 0.35 at r = 0.8). The cabin "as it was" at dawn uses the hazmat "too-normal" family
   (p50 140-165, low saturation 55-70, pale #ccccc9 #e7e5e0 with a warm #b79342 accent, and vignette still 0.67 at r = 0.8). It is clean and still,
   with no dust, and that is the wrongness.
8. **The Queen is drawn in a different language from the cast**: a near-black silhouette (#080c14) with red lipstick-colour accents
   (#c63449 family) and the widest glow in the film. Reveal her in parts and in stages (dress on the step, the head turn at 197.7 s, the hand and
   taped fingers, her bare foot on the step below yours at 604.7 s). Save the full creepy face (huge whites, pinpoint pupils, too-wide toothy grin,
   red irises: the police film's system) for 2-3 beats only, the biggest being "There's time for both of you" (283.7 s) and "I can put you back..." (478.2 s).
9. **Fear acting** for you, Tess and Noah: swap the calm iris eyes for white discs about 0.24 of head width with pupils about 0.2 of the eye, raise
   and tilt the brows, add sweat drops, and act big with the hands (pounding, gripping a collar, covering the ears). Child Noah stays calm and wrong:
   the same knot half tied in a loop.
10. **Red rises only at the end**: red-pixel share at 1% or less until about 75% of the runtime (about 525 s), then 3-8% (lipstick-red light in the glass,
    the Queen's accents, the final wipe). The darkest tenth comes just before (the doorway / time-loop section).
11. **Sound**: music the whole time (≥ 97%), bed -11.5 LU, LRA 17. Every action on screen gets an SFX: about 14 transients and 5 hits per
    minute, with the bed dipped 15 dB before each hit. Use 1.8 silences per minute of about 1.2 s under ominous lines (for example
    "The woman turns her head" 197.7 s, "You have it" 248.4 s, "Wait, he forgot his shoe" 589.6 s), half of them ending on a cut and 1 in 5 landing on a hit.
    Every tag, punch-in and reveal gets a hit within -0.05..+0.10 s. Keep the bed dark (85% of energy below 250 Hz) and unpulsed, with a minor drone and a flat-2 rub.
12. **The grief beats** are new: the references have none. Let them use the p90 shot length (3-4 s) with a slow push of about 1%/s and a
    quieter bed (about -18 LU) without a pulse, and never a frozen frame (the dip in the mattress, the candy, "Hi, Mom").

## Files

- Contact sheets: `_work/ref/sheets/{diver,hazmat}_hook_0-30s.jpg` (1 fps), `{diver,hazmat}_NNN-NNNs.jpg` (every 2 s),
  `families_check.jpg` (scene-family samples), `palettes.png`, and `curve_{diver,hazmat}.png` (bed, voice and luma over time, with rule cards marked).
- Key frames: `_work/ref/keys/`: `diver_faces_a/b.jpg`, `hazmat_faces_a/b.jpg`, `rule_card_animation.jpg`, `tag_x_animation.jpg`,
  `ui_devices.jpg`, `top_hud_band.jpg`, `acting_strips.jpg`, `punchin_check.jpg`.
- Data in `_work/ref/data/`: `cuts30_*.json`, `motion_*.json`, `motion_summary_*.json`, `look.json`, `ui_timing.json`, `captions_*.json`,
  `asr_*.json` (timed words), `audio_*.json` (the full audio metrics), `audio_events_*.json`, `punch_*.json`, and the stems `*/voice.wav` and `*/bed.wav`.
- Scripts in `analysis/refmirror/`: `extract.sh` (decodes the frame sets and audio), `separate_ref.py`, `asr_ref.py`, `cuts30.py`, `still_share.py`, `motion_summary.py`
  (it reads the output of `../measure_motion.py`), `look_ref.py`, `ui_timing_ref.py`, `captions.py`, `punchins.py`, `audio_at_events.py`,
  `curves.py`, `cut_vs_text.py`, `sheets.py` and `grid.py`. The audio metrics come from `../measure.py`.

Limits: the sources are 480p at 225-406 kbps, so the grain and edge-softness numbers are only upper and lower bounds. The voice/bed split leaks a little.
Tag timings were measured on 9 hand-picked tags, and the red X detector is a heuristic (6 + 4 events found). Punch-in detection is conservative:
it only counts scaled matches with the same pose. Word times come from the transducer and are good to about ±0.08 s.
