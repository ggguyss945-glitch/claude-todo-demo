# REF_V2_B: what sibling_stitched and vet_dog measure, and what to change in the Queen of Spades film

Sources: `_work/ref2/sibling_stitched.mp4` ("If Your Sibling's Mouth Is Ever Stitched Shut... STAY QUIET", 830.4 s) and
`_work/ref2/vet_dog.mp4` ("If Your Vet Won't Give Your Dog Back... LEAVE HIM THERE", 909.4 s). Both are 1280x720, 30 fps, and come from the same channel as
the diver/hazmat references in REF_MIRROR.md. The caption, header and rule-card system is the same as before. Everything else has moved up a level.
These are style references only: no characters, art, layouts or scenes are to be copied.

Method: the same `analysis/refmirror/` tools as REF_MIRROR (cuts30, motion via `measure_motion.py` + motion_summary, still_share, cut_vs_text,
ASR of the mix with the NeMo transducer). Look statistics come from 1 fps frames resized to 640x360 with the caption band dropped. Faces and sets were
judged on full-res 720p frames. Our v1 (`_work/deliver/If_An_Eighth_Step_Appears_EN_1440p60_HEVC.mp4`) was measured with the same scripts, so the
"ours" column is directly comparable. Pixel sizes are at 720p unless marked: **x2 for our 1440p output, x1.5 for the 1080 design space.**

---------------------------------------------------------------------------------------------------------------------

## 0. In five lines

1. **Twice the light and three times the colour.** Night is blue-violet with warm practical lights, never black. Our v1 has 44% of frames with mean luma
   under 60. The references have 2% (sibling) and 14% (vet). Colourfulness p50 is **16 for v1 against 56 and 49**.
2. **The villain is drawn in the cast's own language.** It is a person first, made wrong by adding detail one feature at a time: red glowing irises,
   veined sclera, a grin 0.5-0.75 of face width full of **flat human teeth** (never fangs), wrinkle lines, blood tears, or a jaw that drops into a tall dark void.
3. **Cutting is about 40 per minute**: sibling 38.8, vet 40.4, v1 27.8. The median shot is 1.4-1.5 s and **no shot runs past 4.8 s** (v1 has 12 shots over 4 s, the longest 8.9 s).
   About a third of shots reuse an earlier setup, which is what makes this rate affordable.
4. **Sets are full, readable places**: perspective rooms, 15-30 props, signage and labels, re-shot from 4-6 angles. Close-ups sit on blurred **bokeh plates**
   in the location's light colours. Edge density (a measure of detail) p50 is .038/.044 against .025 for v1.
5. **Comprehension devices are everywhere.** One picture per clause. Every key object gets an insert. Phone texts are typed full-screen. Time cards,
   timer badges, a CCTV map, contagion lines drawn between eyes and WALK ✓ / ✗ DON'T RUN labels all appear. Each rule is **demonstrated on a bystander first**, and the rule's state
   (closed eyes, a hand over the mouth) stays visible in frame.

---------------------------------------------------------------------------------------------------------------------

## 1. The numbers (refs vs ours)

| | sibling | vet | **our v1** | older refs (REF_MIRROR) |
|---|---|---|---|---|
| duration / words / wpm / speech share | 830 s / 2491 / 180 / 0.97 | 909 s / 2549 / 168 / 0.89 | 700 s / 2181 / 187 | 465-685 s / 166-170 wpm |
| cuts per min (hard / soft) | **38.8** (96/4 %) | **40.4** (96/4 %) | 27.8 (96/4 %) | 24.1-28.5 |
| shot length p10/25/50/75/90 (s) | 0.72/1.10/**1.50**/1.97/**2.40** | 0.63/1.00/**1.40**/1.87/**2.33** | 0.87/1.47/2.03/2.77/3.33 | 0.77-0.97/…/2.07-2.33/…/3.1-4.2 |
| shots < 1 s / > 3 s / longest | 20 % / 1 % / 4.2 s | 25 % / 2 % / 4.8 s | 14 % / **18 %** / **8.9 s** | |
| cuts in the first 30 s / 60 s | 21 / 44 | 24 / 47 | 18 / 31 | 11-17 in 30 s |
| cuts/min per tenth | 45 38 37 36 34 43 40 43 36 38 | 47 40 38 40 32 39 38 45 42 42 | 30 26 27 24 25 26 27 32 34 27 | flat |
| cuts on a clause start (chance) / picture lead | 63 % (23 %) / **-0.17 s** | 67 % (30 %) / **-0.17 s** | | 58-68 % / -0.28 s |
| setups reused (shot mid-frame matches an earlier non-adjacent shot) | 30 % | 36 % | (not measurable: too dark) | |
| camera moving / zoom-in / zoom-out / pan share | 0.85 / 0.66 / 0.12 / 0.40 | 0.81 / 0.65 / 0.10 / 0.35 | | 0.57-0.80 |
| push-in %/s p25/50/75/90 | 1.9/3.2/5.4/10.0 | 1.9/3.2/5.7/9.6 | | 1.6/2.8/5/10 |
| pull-out %/s p50/p90 | 3.3/14.7 | 3.4/12.0 | | |
| shot moves (shots ≥ 1.5 s): push / push+pan / pull / pan / static | 51/22/2/6/18 % | 48/25/2/5/19 % | | hazmat 48/22/5/4/21 |
| subject motion > 30 px/s @1280, share of time | **0.40** | **0.36** | | 0.33-0.34 |
| per-shot median frame energy p10/50/90 | 0.27/**1.08**/4.86 | 0.20/**0.79**/3.71 | 0.13/**0.33**/1.10 | |
| near-static shots (median energy < 0.15) / frozen frames | 3 % / 0.5 % | 7 % / 1.3 % | **14 %** / 0.2 % | |
| mean luma / p50 of per-frame median | 103 / 88 | 118 / 134 | 88 / **55** | |
| frames with mean luma < 60 / < 40 | **2 % / 0 %** | **14 % / 6 %** | **44 % / 20 %** | |
| per-frame contrast p95-p5 (median) | 136 | 149 | 118 | |
| HSV sat mean / colourfulness p50 | 111 / **56** | 93 / **49** | 68 / **16** | |
| edge density p50 / p90 (Canny, 640 px) | .038 / .075 | .044 / .078 | .025 / .066 | |
| red-pixel share overall / peak tenth | 5.5 % / 18.3 % (tenth 8) | 4.8 % / 13.7 % (tenth 8) | 1.2 % / 6.7 % (tenth 9) | ≤ 1 % then 3-8 % |
| luma by tenth | 122 117 133 110 87 87 89 88 91 97 | 121 124 125 142 140 110 92 **61** 122 141 | 61 60 50 63 153 146 127 107 66 43 | |
| vignette r = .4/.6/.8/.95 (mean frame) | .82/.64/.44/.33 | .89/.75/.57/.47 | .75/.56/.41/.34 | |
| mix LUFS / LRA | -17.2 / 5.6 LU | -16.0 / 5.1 LU | -14.3 / **2.4 LU** | -14.4 / – |

The reference arc is: bright, colourful normality for the first 40-50%, a darker and more saturated middle, and the **darkest and reddest tenth at 70-80%**
(the climax). Then vet returns to bright daylight (luma 141) for the twist ending. Our v1 starts dark, goes bright and grey in the middle (sat 20-36), and
ends darkest (43). The opening has nothing to contrast against.

---------------------------------------------------------------------------------------------------------------------

## 2. Hook and structure

Grabs: `_work/ref2/sheets/sibling_hook_0-40s.jpg`, `sib_hook_full_1_5_21_24.jpg`, `vet_hook_0-32s.jpg`, `vet_framing.jpg`.

- **Frame 0 is the scariest image as an ECU**: the stitched mouth in sibling, and the vet's bloody red eyes followed by her grin with spit strings (vet 0:00-0:01).
  The same ECU book-ends the premise (sibling 19-20 s, "hasn't spoken a single word").
- **The title commands are each acted out by "you"**: vet 0:03 is a POV shot of your red sleeve pushing the exit door on "Leave him". Then a two-shot on "don't argue",
  your back walking down the corridor on "don't sneak into the back", and an ECU of the dog's red eyes on "don't look your dog in the eyes".
  Red X is used sparingly: twice in the sibling hook (0:07 on the hand reaching for the stitches, 0:11 on the window for "don't answer anyone calling").
- **Background threat**: sibling 0:13 has the sibling in the foreground and a tiny dark figure far down the street ("something followed them"), in `sib_framing.jpg`.
- **Rule cards come every ~100 s, like chapter headings.** Sibling: 21, 109, 208, 312, 411, 519, 638 s (gaps 88-119). Vet: 71, 154, 248, 347, 458, 572, 677 s
  (gaps 83-114). Sibling puts rule 1 *inside the hook* (21 s), and the time card follows at 24 s. Vet plays "there are seven rules" over a **flash-forward** of the
  three infected standing in a dark room (70-71 s), which is the climax image from 9:54-9:58.
  (Ours: 130.2, 204.0, 269.7, 350.8, 446.8, 542.5, 609.9 s. We keep the narration, so the picture must carry the long 0-130 s setup; see section 8.)
- **Every rule card follows a cliffhanger line**, for example "...something goes terribly wrong. Rule number six" (sibling 519 s).
- **Time is always labelled**: "9:38 PM / SATURDAY NIGHT" in a dark box with a red edge, top-left, over a real wall clock whose hands spin forward (sibling 24-28 s),
  then a "6 HOURS MISSING" label on the clock (28 s). There is also "3 DAYS AGO" over a storm (vet 20 s) and "10 MINUTES LATER" over a fast-spinning clock (vet 31 s).
- **Endings**: vet replays its hook shots under a repeat of the title lines (14:52-15:08), then cuts to the dog's red eyes and black.
  Sibling ends with the possessed boy and a police officer smiling into the lens, and a parking lot of people turning toward camera one by one (12:56-13:18).

## 3. Cutting

- About 40 per minute, flat across the film (32-47 per tenth). As in the older references, the build comes from content, light and sound, not from a faster cut rate.
- **One picture per clause, and often one per noun.** 63-67% of cuts land on a clause start, with the picture 0.17 s ahead. With 29-36 clauses
  per minute and 39-40 cuts per minute, list sentences get a shot per item ("racing games, basketball machines, and rows of flashing arcade cabinets", sibling 6:02-6:06).
- **The reveal ladder**, vet 37-58 s (`vet_reveal_seq_37-58s.jpg`), has 14 shots in 21 s (0.5-2.2 s each) and changes scale on every clause:
  waiting room wide → empty staff door ("the staff door opens") → full figure in the doorway → wider shot that relates her to the reception desk → **ECU eyes** ("her eyes are bright red")
  → CU blood → MCU lips pulled back → ECU teeth → reaction wide ("you stand up") → CU of you talking → MCU stare → wide growl → profile → OTS with you in the foreground.
  Sibling 4:10-4:36 (`sib_reveal_seq_249-277s.jpg`) does the same: a creaking door insert, then a low wide up the stairs with the man tiny at the top, then OTS past dad's
  flashlight, ECU eyes, MCU jaw, ECU void, reaction, and an insert of hands gripping.
- **Exactly one held shot per big transformation**, inside the fast cutting: dad's grin stretches over **4 s** in one MCU (sibling 8:22-8:25, `sib_dad_turns_486-510s.jpg`).
- Soft cuts are 4% (dissolves into memories and the found-footage video). There are 50-54 light flashes, clustered on the alarm strobes (sibling 609-680 s: 30 flashes).

## 4. Camera and framing

Grabs: `sib_framing.jpg`, `vet_framing.jpg`, `sib_sets.jpg`, `vet_sets.jpg`.
- Motion numbers are close to hazmat's (camera moving 81-85%, push median 3.2%/s, pulls 10-12%), but **subject motion is higher (0.36-0.40)** and in-shot
  change is **2.4-3.3x ours** (per-shot frame energy p50 0.79-1.08 against 0.33).
- **Wide-angle perspective** on interiors gives strong convergence. **Dutch and low angles are used for threat** (the stairs at sibling 4:14, the alarm high-wide at 10:12),
  and high wides establish geography (vet waiting room 0:16).
- **The "you" avatar is always identifiable.** Sibling's you wears a yellow hoodie and vet's wears a red one: we see the back of the head in OTS shots (sibling 6:16, vet 0:02)
  and **POV hands in that sleeve colour** (vet 0:03 pushing the door, sibling 9:15 pressing on the sibling's mouth, 6:22 being grabbed). The OTS share is about 10% and POV hands about 5%
  (manual tally of 80 frames).
- Shot scale, manual tally of sibling 0-160 s at 2 s steps: CU/ECU about 35%, inserts (objects, phone, UI) about 18%, MS about 22%, wide/establishing about 25%.
  **About 30% of all frames are close-ups or phone inserts on a blurred bokeh plate.**
- There is a split screen for "his eyes meet hers" (vet 5:22). Villains look straight into the lens: through the teen's phone camera (vet 2:54, with REC 00:24 and a zoom UI),
  as a row of all three infected (9:58), and as the officer and boy smiling (sibling 13:00).

## 5. Characters

Grabs: `sib_faces_a.jpg`, `sib_faces_b.jpg`, `vet_faces.jpg`, `face_measure_grid.jpg`, `sib_possessed.jpg`, `sib_lovedone_140-164s.jpg`,
`sib_dad_turns_486-510s.jpg`, `sib_stitchbreak_528-560s.jpg`. Full-res stills are in `sheets/keys_B/`.

**Normal people**
- Outlines are black, about 4 px on MS/MCU (8 px at 1440) and 6-8 px on ECUs, so our 7.5-9 design px is fine. Inner features (nose, mouth, smile lines) are thin **dark-brown**
  2 px lines, not black. Eyelids are tapered strokes, thick at the top lid and thin at the ends. There is no lower lid line.
- At rest, almond eyes are about 0.15-0.17 of face width, with irises filling the eye height and 1-2 highlights. Blush is a soft round patch. Hair is a flat colour with a jagged or zigzag
  outline and a few darker strand lines. Bodies have natural proportions in wides (head about 1/6-1/7 of height). Heads only get big in CU.
- In fear, the eyes open into white discs and the **iris shrinks to about 0.25 of eye width**. Tears are glossy blue streaks. Acting stays physical: hands over the mouth,
  trembling, gripping a wrist, covering the ears.

**The villain is the same drawing system with more detail added**, and that wrongness on a plausible person is the scare:
- **Eyes**: red irises with two speculars and a **red bloom halo** around the eye, red veins in the sclera and red lower lids (vet). In the sibling dad, the sclera goes pink
  with veins and a red ring circles the iris (8:12). Sizes stay human (0.15-0.2 of face width). The scare is colour, glow and stillness ("he doesn't blink"), not giant eyes.
- **Mouth**: a grin **0.5-0.75 of face width** with two full rows of 12 or more **flat white human teeth**, thick red lips, pink gums and spit strings (vet 0:01). The other mouth is the
  **jaw that "hangs unnaturally low"**: the face stretches vertically and the mouth becomes a tall glossy dark-red void with one short row of upper teeth
  (sibling 4:28, 6:40, 9:40, 12:00). The references never use fangs.
- **Extra lines appear only on the wrong face**: frown lines between the brows, nasolabial folds and crow's feet (dad 8:22, the officer at 13:00).
- **Fluids**: blood tears drawn as glossy tubes with drip bulbs (vet). Black tear and thread marks (sibling).
- **Escalation is one feature per shot, timed to the clause.** For the dad (8:06-8:29): he raises his head → ECU of bloodshot eyes → the mouth opens → the void with the sibling's voice
  → a reaction shot → he turns to mom → the smile starts → a 4 s held stretch to "nearly all his teeth" → two possessed people walking in step.
- **The threat spreads, so the cast of villains grows**: vet goes from 1 (0:42) to 2 (3:23, "now there are two of them") to 3 (5:30), then the little girl (9:00) and a row of all
  three (9:58). Sibling goes from the stranger to the boy, dad, the crowd and the police officer.

**The uncanny loved one (sibling: closest to our Noah)**
- The loved one **keeps their whole design** (hoodie, hair, freckles, the stitches). Only eyes and mouth change, and the body acts against its own will: the sibling forces
  their own mouth shut while the lips keep moving under their fingers (2:41-2:43). The loved one's voice comes out of the wrong mouth (6:40, 8:15).
- **The possession is first seen through a screen.** A phone video with full player UI (scrub bar, ⏮ ⏸ ⏭, timecode) runs from 2:18 to 2:43, and the face takes a
  **pixel-sort or datamosh glitch** at the moment the wrong voice comes out (2:37.6). A second video at 12:24-12:42 turns the camera to a mirror where "someone wearing your clothes" stands.
- **Clue chains on the loved one's body**: a black mark on the carpet → ECU of the broken thread → ECU of the stitches with one snapped → the face in tears (8:50-8:58).

**What this means for our Queen** (v1: `_work/cast/cast_queen_scary.png`, and `sheets/ours_v1_samples.jpg` at 284 s and 481 s)
- v1 is a frontal, symmetric, pale mask with eyes about 0.3 of face width and a shark-fang grin, framed by black hair that reads as flat planks. She has no Queen or Spades
  iconography, and she sits on a flat grey background. It reads as a generic creepypasta mask, and it is the same mask in every beat.
- Rework her as a **person in the cast's drawing language**, with otherness carried by light, colour and behaviour. Use the references' ladder, one feature per beat:
  - **S0**: the silhouette on the step, back turned.
  - **S1**, the head turn at 197.7 s: a calm, almost beautiful pale face with red lipstick and normal almond eyes. The calm is the uncanny part.
  - **S2**, "There's time for both of you" at 283.7 s: she doesn't blink, the pupils go to pinpoints, and the **lipstick smile runs past the lips** onto the cheeks (our own motif: the steps are drawn in lipstick).
  - **S3**, "I can put you back..." at 478 s: veined sclera, red irises with a halo and two speculars, a 0.6-0.75-width grin of **flat human teeth**, stretch lines
    and mascara-black tears.
  - **S4**, "Wait, he forgot his shoe" in Noah's voice at 589.6 s: **the jaw drops into the tall glossy void and a loved one's voice comes out of the wrong mouth.** This is exactly the sibling device.
  - In the phone at 697 s: the screen glitch on her face.
- Give her readable **Queen of Spades iconography**: a small black crown or spade hair ornament, a spade brooch or pendant, playing-card trim on the dress, and lipstick red as her only colour.
  Hair needs strand lines and a sheen gradient, not planks.
- **Noah stays Noah**: the same design with one feature changed at a time. In the mirror, use the screen-glitch device on his face, and let him act against his will.

## 6. Sets, light and palettes

Grabs: `sib_sets.jpg`, `vet_sets.jpg`, `families_palettes.jpg` (frames with their k-means palettes), and `texture_crops_100pct.jpg` / `texture_crops2_100pct.jpg`.
- The environments look like 3D: perspective rooms with ceilings, consistent vanishing points, flat-shaded walls with soft light gradients and darkened corners, and
  characters as flat outlined cutouts inside them. The engine is 2D, so build each main location as a **perspective room kit** (floor, walls, ceiling, 15-30 props,
  signage) and re-shoot it from 4-6 angles (front, reverse, high wide, low dutch, OTS, the window into the next room).
- **Props and labels make the place legible**: CEDAR GROVE ANIMAL HOSPITAL, STAFF ONLY, EXIT, VACCINES SAVE LIVES, name tags (PEPPER, JENNA), a paw-print wallpaper,
  STARLITE ARCADE, HOOPS, RECORD YOUR OWN MESSAGE · 50¢, BOOTH POWER ON/OFF with a warning triangle, FIRE PULL DOWN.
- **The forbidden object always sits in the same place**: the blue-blanket cage at the vanishing point of a symmetric kennel room (vet 6:00), seen through the
  little window in the staff door and on CCTV.

| family | luma p1/5/50/95/99.5 | sat mean/p90 | hue | palette (most frequent first) |
|---|---|---|---|---|
| sibling night exterior | 14/30/**95**/206/239 | 94/165 | 238° | #555786 #383a69 #7d7692 #1b1d42 #a99d9c #dcd0c8, plus warm windows and a glowing moon |
| sibling home, lights on (normal) | 56/79/**166**/230/246 | 59/117 | 25° | #cfc0a9 #b29e86 #8a7a69 #e8ded2 #515a8c #5f4640 |
| sibling home after lights out, by flashlight | 35/45/**114**/206/235 | 87/171 | 241° | #494981 #9395ba #70709a #332d59 #ccc8ce, plus a warm pool #b18c27 |
| sibling arcade neon | 22/30/64/164/219 | 140/178 | 253° | #352b6f #26203f #584c95 #7a64c6 #aa6443 #b8b1bf |
| sibling alarm red (climax) | 31/38/78/159/206 | **168**/211 | 327° | #57183d #ae438f #822f68 #8a1e38 #be3f4e #d59aaa |
| sibling CU on bokeh | 19/26/67/179/210 | 143/197 | 248° | #30326b #241f39 #5c5ca9 #885652 #9196cc #d0b5a7 |
| vet waiting room (normal) | 41/60/**141**/222/247 | 83/189 | 207° | #ced4da #2f68a1 #a5aaad #797a7a #54aad7 #354056 |
| vet kennel room (lit) | 40/82/148/218/247 | 50/159 | 214° | #8c9299 #acb5be #696e76 #d1d7de #4a8ee4 #3c3f46 |
| vet dark kennel (darkest room) | 19/25/**70**/180/197 | 101/155 | 214° | #303c4d #172331 #46566a #66768d #9cb9e1 |
| vet eyes-closed red (darkest family) | 5/9/**45**/140/175 | 149/235 | 354° | #270a0b #562523 #815b64 #302e49 #a58796 #a23c20 |
| vet flashback (sepia) | 56/74/150/221/238 | 69/146 | 36° | #a0917f #81705c #c3b39c #e2d4bd #604b36 #d5a74b |
| vet villain CU | 10/24/104/206/244 | 116/190 | 321° | #32201f #dac1b4 #335a85 #a69384 #5593c2 #90413d |

- **"Dark" is a hue and a contrast choice, not black.** The darkest normal room still has p50 70. Night is saturated royal blue or lavender at p50 95-114, with warm
  windows, a moon halo and a warm flashlight pool. Only the eyes-closed sequence goes to p50 45. Our camp night and cabin should sit in the 70-115 band, with the
  flashlight as a warm saturated pool. That band is the single biggest step toward "visually appealing".
- **Normal is bright and saturated** (sat 59-83, p90 117-189), and the wrongness is added on top of it. Our "theirs" dawn cabin measured sat 20-36 (grey), which reads as dull, not as uncanny.
  Keep it bright, make it warm and colourful, and make it wrong through stillness and details.
- **The climax is saturated magenta-red** (sat 168, hue 327°), as a light colour on the set (alarm strobes, an emergency light), with **13-18% red pixels at 70-80% of runtime**.
- **Bokeh plates** behind CUs use big soft discs in the location's light colours: blue and orange at home, magenta and cyan in the arcade, the paw wall dissolved into colour blobs (vet).
  They are cheap, premium-looking and easy to read, because the face is the only sharp thing.
- Post: bloom on everything emissive (red eyes, stitch punctures, neon, moon, flashlight). The vignette matches ours (.44-.57 at r .8). There is no measurable grain or chromatic
  aberration (R-B shift ≤ 0.05 px; flat-area noise 0.3 levels, though this encode would hide fine grain). A faint paper texture is visible at 100%.

## 7. VFX, UI and on-screen text

Grabs: `sib_rulecard_anim.jpg`, `vet_rulecard_anim.jpg`, `vet_ui_a.jpg`, `vet_ui_b.jpg`, `vet_ui_c.jpg`, `sib_inserts.jpg`, `vet_clues.jpg`,
`vet_eyes_closed_600-640s.jpg`, `header_bands.jpg`, `caption_*.jpg`.

**Rule cards are story objects with physical choreography and story information printed on them**

| | sibling | vet |
|---|---|---|
| object | red felt board with stitched edges, grommets, a "FILE 092 · STAY QUIET" tag and a stitched-mouth emblem | hospital "KENNEL CARD · PATIENT CHART · CAGE 07", clipped to kennel bars; Max's red collar hangs beside it and **two red eyes glow in the dark behind the bars** |
| entry | drops from the top and settles in about 0.25 s (208.47 → 208.73) | swings in at about -35° and settles like a pendulum in about 0.5 s (71.13 → 71.67) |
| number | a stitched badge stamps in at about 1.6x and settles in 0.13 s | a red rubber stamp with ink splatter, 0.7 s after the card |
| text | **a needle and thread stitch the words in**, word-synced | typed word-synced; the **command comes last, in red on a yellow highlighter** ("DON'T ARGUE", "DON'T LIFT THE BLANKET") |
| story info | file number, rule name | date SAT 11/07 10:42 AM, patient MAX, GOLDEN RETRIEVER, DR. HALE, a ☒ DO NOT OPEN tick box |
| appears before "Rule" | 0.04-0.33 s (median 0.15) | 0.31-0.60 s (median 0.44) |
| visible | 2.8-4.2 s (median 3.0) | 3.7-4.8 s (median 4.3) |
| out | 0.55-0.8 s after the sentence ends | 0.3-0.6 s after |
| grade | the bokeh plate behind it carries the section's colour | the rule 7 card is **red-graded** with the climax |

- **Captions** use the same template as before: white bold caps at 2.1% H (15 px at 720), centred on y 0.893 H, 25-42% of W, on a translucent dark box (it lowers luma by about 40%).
  The **header** is now almost invisible ("FILE 091 · THE CLINIC // RULE 6 OF 7" plus a timecode).
- **Phone text**: huge black type fills a phone held by a hand on a bokeh plate, typed letter by letter with a keyboard. There are about 14 message beats in sibling (about 1 per minute),
  because the mute sibling "speaks" through the screen. The **camera roll** ("Recents 1,285 items", a 0:17 thumbnail) and **photos** on the phone prove the backstory.
- **Diagrams that state the logic**:
  - red target rings and a **dashed red line from the infected eyes to the next victim's eyes** (vet 3:02 over a wide, 3:50-3:58, the 5:22 split, the 6:42 flashback,
    and the 8:14 x-ray line of sight);
  - **✓ WALK / ✗ DON'T RUN** labels next to the old man (5:02);
  - a red X over the exit doors on "Don't." (4:14);
  - **a speaker with pulsing rings** to show how far sound reaches (sibling 7:06, 7:40), and fire-alarm rings (vet 10:12).
- **Counters**: circular red-ring badges, "9 SECONDS" (vet 3:02, "five seconds pass, then ten") and "37 SECONDS" (6:42).
- **Found footage and devices**: a CCTV quad labelled CAM 1 WAITING ROOM / CAM 2 RECEPTION / CAM 3 KENNEL HALLWAY / CAM 4 PARKING LOT, with a date stamp and REC
  (8:26-9:26): this is the map of the whole set. An x-ray light box where a finger points at the second pair of eyes (8:00-8:16). A police radio insert. A **news report** with
  labelled portrait cards (DR. HALE / JENNA / TEEN, 17) that recaps who was affected (13:10-13:14). A sepia flashback with paper texture (vet 6:32-7:00).
- **Sensory devices**: an **eyelid wipe** (an eye-shaped matte closes with red rims, vet 10:04), then red with vein texture "through the eyelids" (10:14).
  Sounds heard with eyes shut are shown as dim, red-washed images, intercut with your face, eyes closed, to keep the rule visible (10:14-10:56).

## 8. Why they are easy to follow (devices, ranked by how often they appear)

1. **The noun of each clause is the picture**: one shot per clause, and per item in a list.
2. **Every key object gets an insert before it matters**: the scissors, the alarm box, the booth power switch, the speaker, the thread; the collar on the cage, the x-ray, the radio.
   That is about 2-2.5 inserts per minute, including phone and UI.
3. **Each rule is demonstrated on someone else first.** The teen films her and gets infected (rule 2), the woman runs and gets chased (rule 3), the officer looks and gets infected.
   Dad answers the voice and is later possessed (sibling). The viewer sees the cause and the effect before the protagonist faces it.
4. **The rule's state stays in frame**: eyes shut in every CU during the blind escape, the hand over the mouth or the stitches in nearly every sibling CU.
5. **Geography first**: a 3-6 shot approach to each new place (sibling arcade 5:44-6:02: car POV → plaza wide → sign → entrance → interior wide → crowd), a high wide of every
   room, the CCTV quad, and the window in the door into the next room.
6. **Time and count labels** (time cards, "6 HOURS MISSING", timer badges).
7. **Proof and recap**: a phone video, photos, an x-ray, the news report with portraits, the 0:17 clip length matching "17 seconds long".
8. **The "you" avatar** is identifiable by sleeve colour in OTS and POV shots, so the second-person narration always has a body.

## 9. How they build tension

1. Open on the scariest ECU at 0.0 s, then show the normal world bright, warm and busy for the first 40-50%.
2. **Threats start small and far away** (in a doorway, at the top of the stairs, at the end of the driveway) and are revealed by a scale ladder (WS → MS → CU → ECU) with one wrong feature per clause.
3. One held transformation shot per big reveal (3-4 s) inside the 1.5 s cutting.
4. **The threat multiplies** (one villain becomes two, three, then a crowd) and the light shifts from normal to coloured night to the red climax at 70-80%, the darkest and most saturated tenth.
5. **The villain looks into the lens**: through a phone camera, as a row of the infected, or as a crowd turning toward camera.
6. Timers and counts on screen; a cliffhanger line right before every rule card.
7. Sensory deprivation: eyes shut, black, red through the lids, sounds made visible.
8. Callbacks: three slow knocks (sibling 0:40 and 11:46), the whine and the tail thumps (vet). Vet's ending replays the hook shots.

## 10. Sound (brief: the owner is happy with ours)

- The mix is quieter and more dynamic than ours: -17.2 / -16.0 LUFS with **LRA 5.6 / 5.1 LU**, against our -14.3 LUFS with LRA 2.4.
  Short-term (3 s) mix loudness p10/50/90 is -0.7/+2.1/+4.2 LU (sibling) and 0/+2.3/+4.5 (vet) relative to integrated.
- Around rule cards the mix rises **+3 to +5.5 LU at 1-2 s after the card** (the stamp or stitch hit and the riser tail). The loudest 3 s windows are the climax
  (sibling 550-657 s, vet 678-747 s) and the card at 154.8 s.
- Small upgrade: keep -14 LUFS for delivery, but let the quiet stretches drop and the hits stand out, for an LRA of about 5. Add a stamp, swing or stitch hit
  on each rule card's choreography.

---------------------------------------------------------------------------------------------------------------------

## 11. Adopt, ranked (most impact first)

1. **Relight and recolour the whole film.** Night is blue-violet (p50 70-115, hue 230-250°, sat 90-140) with warm practicals in every night shot (cabin windows, a lantern,
   a warm saturated flashlight pool). The dawn "theirs" world is bright and warm-coloured (sat 60-85), not grey. The climax is saturated magenta-red light at 70-85% of runtime.
   **Targets: frames with mean luma < 60 at 10% or less (v1 44%), colourfulness p50 of 45 or more (v1 16), contrast p95-p5 of 135 or more (v1 118), and red share 13-18% in the peak tenth.**
2. **Redesign the Queen as a person in the cast's language, with a five-stage ladder** (section 5): human eyes that turn red and glow, flat human teeth instead of fangs,
   a lipstick smile that runs past her lips, stretch lines and black tears, and the **jaw-drop void with Noah's voice** at 589.6 s. Add crown and spade iconography and real hair.
   Save the full face for 2-3 beats, with **one new wrong feature per clause**.
3. **Cut at 36-40 per minute**: median 1.5 s, p90 2.4 s or less, nothing over 4.8 s except a few held transformation shots. That is about 420-460 shots for 700 s (v1: 324).
   Pay for it with a **library of reusable setups** (a third of shots reuse one): a CU of each character on the bokeh plate, OTS from each side, the mirror insert, the
   doorway, the bell. Keep one held 3-4 s transformation shot per big reveal.
4. **Rebuild the sets as perspective room kits** with 15-30 props, signage and labels each (CABIN 7, SAVE FOR THE MUSEUM, camp signs, the bunk name tape, the clock), shot from 4-6
   angles. Use wide-angle convergence, and low or dutch angles for threat. **Target edge density p50 of .035 or more (v1 .025).** Keep the mirror (the forbidden object) in the same place in every wide.
5. **Put close-ups on bokeh plates** in the location's light colours (about 30% of shots). Blur everything but the face.
6. **Rule cards as a story object with choreography**: a 0.25-0.5 s physical entry (drop or swing and settle), a number stamp at 1.6x that settles in 0.13 s, text written word-synced with a story tool
   (our lipstick), and the **command last, highlighted**. Print story facts on the card (the cabin, the date and 11:57 PM, NOAH, a ☒ DO NOT WISH box). In at 0.15-0.45 s
   before "Rule", out 0.3-0.8 s after the sentence, visible 3-4.5 s. Put the section's colour on the plate behind it, and grade the last card red.
7. **Comprehension inserts at about 2-2.5 per minute**: mom's text and Tess's phone as full-screen phone UI; a time card at 19.4 s ("11:57 PM", over a real clock); Tess's countdown
   as a **ring-timer badge** (60 → 45 → 20 → 5); labels; and **diagrams that state the logic**. Draw a dashed red line from the Queen's eyes to yours at 197.7 s ("now she's listening to you"),
   number 1-8 beside the mirror steps, and show the **two bells as sound rings: a clean ring for the fake one, and a ring plus a broken rattle for the real one** (the speaker device from sibling 7:06).
8. **Demonstrate each rule's consequence before it bites.** Noah is our bystander: show what his wish did, in a flash insert, before the rule that depends on it.
   Keep each rule's state visible in frame: the towel, the taped fingers, Tess's count badge, your clenched fist with the candy.
9. **Make the "you" avatar identifiable**: the same sleeve colour in every POV hand and the back of the head in OTS shots (about 10% OTS, 5% POV hands).
10. **Use the reveal ladder for every entrance of the Queen**: start her small and far (on the step, in the doorway), then WS → MS → CU → ECU, one feature per clause, with a reaction shot between steps.
11. **Use screens for the uncanny**: mirror and phone views get player or camera UI and a pixel-sort glitch on the face at the moment it goes wrong (her in the phone at 697 s; Noah's face flash).
    Have the villain **look into the lens** 2-3 times.
12. **Hook**: frame 0 is the new Queen ECU (or her hand on the eighth step), 21-24 cuts in the first 30 s, the title commands acted by "you" in POV, a red X on the two "don't" lines,
    and the threat small in the background behind Tess at "Don't wait to see who's coming up the stairs".
13. **The arc in light**: bright warm memories and normality early, coloured night, the darkest and reddest tenth at 70-80%, and a brighter final tenth before the last sting (in the phone).
14. **Motion inside shots** at 2-3x v1 (per-shot frame energy p50 of 0.8 or more, v1 0.33; near-static shots 5% or fewer, v1 14%): cloth, hair, the flashlight beam swinging, dust, people crossing, acting cycles.
15. **Sound, small**: LRA about 5 at -14 LUFS, and a hit on each card's stamp or swing.

## Files

- Contact sheets at 2 s steps: `_work/ref2/sheets/sib_{0-160,160-320,320-480,480-640,640-800,800-831}s.jpg` and `vet_{0-160,...,800-909}s.jpg`. Hooks at 1 fps:
  `sibling_hook_0-40s.jpg` and `vet_hook_0-32s.jpg`.
- Key-frame grids: `sib_faces_a.jpg`, `sib_faces_b.jpg`, `vet_faces.jpg`, `face_measure_grid.jpg`, `sib_possessed.jpg`, `sib_lovedone_140-164s.jpg`, `sib_dad_turns_486-510s.jpg`,
  `sib_stitchbreak_528-560s.jpg`, `sib_reveal_seq_249-277s.jpg`, `vet_reveal_seq_37-58s.jpg`, `sib_rulecard_anim.jpg`, `vet_rulecard_anim.jpg`, `sib_inserts.jpg`,
  `vet_ui_a/b/c.jpg`, `vet_clues.jpg`, `vet_eyes_closed_600-640s.jpg`, `sib_sets.jpg`, `vet_sets.jpg`, `sib_framing.jpg`, `vet_framing.jpg`, `families_palettes.jpg`,
  `texture_crops_100pct.jpg`, `texture_crops2_100pct.jpg`, `header_bands.jpg`, `caption_*.jpg`, and `ours_v1_samples.jpg` (v1 at 2-640 s for comparison).
- Full-res 720p stills: `_work/ref2/sheets/keys_B/sib_NNNN.jpg` and `vet_NNNN.jpg` (NNNN = second).
- Data in `_work/ref2/data/`: `cuts30_{sibling_stitched,vet_dog}.json`, `asr_*.json` (timed words), `motion_*.json`, `motion_summary_*.json`,
  `look_{sibling_stitched,vet_dog}.json` (per-second look stats), `families_B.json`. The decoded frames and audio were deleted.

Limits: the sources are 720p at 210-240 kbps, so grain and fine texture are hidden. The ASR ran on the full mix (no voice/bed split), so word times are good to
about ±0.1 s and a few words are wrong. Setup reuse is an edge-NCC heuristic. Shot-scale, OTS and POV shares are manual tallies of 80 frames.
The v1 look numbers come from the delivered 1440p file at 1 fps with the same scripts.
