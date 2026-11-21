# REF_V2_A: the author's newer craft (hazmat720, teacher_dog, stadium)

Sources (all 1280x720, 30 fps, same channel template):
- `_work/ref2/teacher_dog.mp4`: "If Your Teacher Brings Your Dog To School... IGNORE HIM" (885 s)
- `_work/ref2/stadium.mp4`: "If The Whole Stadium Starts Smiling... DON'T SMILE BACK" (825 s)
- `_work/ref2/hazmat720.mp4`: "If A Hazmat Team Locks You In A Grocery Store... DON'T MOVE" (552 s)

**hazmat720 is the same film as the old `_work/ref/hazmat.mp4`.** The old copy was cut off at 465 s (it lost the last 87 s) and froze for its first 3 s.
The only new material in hazmat720 is:
- the real cold open: a 0.4 s flash of the villain's red-lens mask with a red "9:03 PM" chip, then a van with a flashing beacon;
- the ending, 7:45-9:12: dispatch documents and a final symbolic image.

So **teacher_dog and stadium are the newer craft**. hazmat is used here as the "old" baseline, together with diver (REF_MIRROR.md).

Method:
- Same tools as REF_MIRROR (`analysis/refmirror/`), with captions re-cropped for 720p.
- Cuts on 30 fps edge maps, Farneback flow at 6 fps, look statistics per hand-checked scene family.
- Narration word times come from a NeMo transducer run on the mix.
- Our v1 deliverable was measured with the same scripts for a like-for-like comparison.
- Shot types were hand-classified on one-thumbnail-per-shot sheets over 2-minute windows.

Pixel values are @1280 unless marked; double them for our 2560 output.

---------------------------------------------------------------------------------------------------------------------

## 0. The short version

1. **They cut faster and lock everything to the narration.** The rate is 36.5-39.5 cuts/min (old: 24-29; v1: 27.8), and the median shot is 1.5 s (old 2.1-2.3; v1 2.0). The rule is one clause = one shot = one caption.
2. **About 40 % of the shots are wides.** The place is re-established all the time, from 10-15 different angles. In our plan only 8.5 % of shots are wides and 50 % are faces.
3. **Every noun gets a picture.** There are about 4-6 inserts, documents or UI shots per minute. Every identifying detail, every piece of evidence and even every simile gets its own shot.
4. **The mystery is explained with evidence on screen**: CCTV footage, a box of old collars with engraved years, a 1984 | TODAY split, dispatch printouts with a highlighter and a stamp. The viewer never has to infer.
5. **The villain is a human archetype who distorts in stages**, and the stages happen on camera, timed to the words. The full monster only arrives at about 80 % of the runtime (teacher_dog 11:46 of 14:45).
6. **Sets are 3D-perspective, dense and lit.** Every close-up has a defocused background (bokeh discs or soft colour blobs). Night is **not** murky: stadium night has a median luma of 93 and a contrast std of 49, while v1 has a median luma of 55 and a contrast std of 38.
7. **Typography carries structure.** There is one full-screen kinetic title command in the hook, and 3-5 more typographic beats (SECTION 214. ROW H., countdown numbers 3-2-1, a closing "DON'T SMILE" bookend).
8. **The rule card is the film's central story object, and its look evolves.**
   - stadium: the jumbotron, which is the very thing rule 2 forbids looking at; the card is seen through a camera viewfinder at rule 5 and inverted and glitched at rule 7;
   - teacher_dog: a "HAVE YOU SEEN HIM?" lost-dog flyer on the school corkboard.
9. **Red X marks and command tags are nearly gone** (one red X per film). Kinetic type, inserts and labelled flash-forwards replace them.
10. **The audio template is unchanged**: mix -14.4 to -15.0 LUFS, the rule cards and the title hit are the loudest moments, and the narration is continuous at 166-186 wpm. This matches the owner's "keep the audio".

---------------------------------------------------------------------------------------------------------------------

## 1. Numbers: old references vs new references vs our v1

| | diver (old) | hazmat (old ≈ hazmat720) | **teacher_dog** | **stadium** | **our v1 (measured)** |
|---|---|---|---|---|---|
| cuts/min | 24.1 | 29.0 | **36.5** | **39.5** | 27.8 |
| shot length p10/25/50/75/90 (s) | .77/1.49/2.33/3.22/4.22 | .97/1.43/2.00/2.63/3.03 | **.63/1.10/1.57/2.12/2.64** | **.61/1.03/1.47/1.93/2.42** | .87/1.47/2.03/2.77/3.33 |
| shots < 1 s / > 3 s / > 4 s | 14 / – / 13 % | 11 / 10 / 2.6 % | **20 / 5 / 1.1 %** | **23 / 3 / 0.7 %** | 14 / 18 / 4 % |
| cuts in the first 30 s | 17 | 15 | **20** | **22** | 16 (plan) |
| cuts per minute through the film | flat 19-28 | flat 27-31 | 31-47 (peaks: min 8 = 47, mins 10-14 = 40-41) | flat 37-44 | 24-34 |
| hard / soft | 96/4 | 97/3 | 94/6 | 97/3 | 96/4 |
| cuts on a clause start | 68 % | 57 % | **75 %** (chance 32) | 66 % (chance 28) | (plan 65 %) |
| picture leads the clause by (median) | 0.28 s | 0.28 s | **0.17 s** | **0.15 s** | (plan 0.25) |
| caption changes within 0.2 s of a cut | | 76 % | 70 % | 74 % | |
| captions/min, median length | 30-33, 1.5-1.7 s | 30.2, 1.73 s | **41.6, 1.20 s** | **45.2, 1.13 s** | |
| camera moving share | .57 | .79 | .77 | .76 | .80 |
| push-in %/s p25/50/75/90 | 1.6/2.9/5.2/10.7 | 1.6/2.8/5.0/8.9 | 1.6/**3.1/6.2/10.9** | 1.5/2.6/4.2/6.8 | 1.2/**1.6/2.2/3.5** |
| pan px/s p50/p90 | 23/52 | 15/53 | 21/70 | 17/51 | 21/57 |
| subject motion > 30 px/s, share | .33 | .34 | .32 | .36 | **.19** |
| per-shot median frame energy p10/50/90 | | .22/.73/4.46 | .13/.62/2.82 | .27/1.02/4.72 | **.13/.33/1.10** |
| frozen frames (nothing moves for 0.5 s) | 12.2 % | 0.5 % | 2.6 % (CCTV and end card) | 1.1 % | 0.2 % |
| shot moves push / push+pan / pull / pan / static | 27/21/3/6/43 | 46/22/5/4/23 | 42/27/5/2/24 | 41/18/4/12/25 | 49/12/9/7/23 |
| punch-ins per min (scale) | 0.8 (×1.25) | 0 | **1.9 (×1.08)** | 1.2 (×1.25) | |
| white flashes per min | 1.4 | 1.5 | 1.9 | **4.6** | **0** |
| red X per film | 6 | 4 | **1** (8:08) | **1** (0:10.7) | 6 planned, plus 13 HUD tags |
| rule 1 at | 117 s (17 %) | 81 s (15 %) | 125 s (14 %) | **24 s (3 %)**: rule 1 *is* the title rule, said at the end of the hook | 130 s (19 %) |
| runtime after rule 7 | | 94 s (17 %) | 190 s (21 %) | 227 s (27 %) | 90 s (13 %) |
| rule card: lead before "Rule" / visible / cut after the sentence | .42-.48 / 4.5-5.4 / .1-.2 s | .48-.71 / 3.2-6.3 s | .12-.56 / 3.3-4.9 / .15-.35 s | .14-.41 / **2.7-3.8** / .16-.35 s | .45 / 3.8 (plan) |
| whole-video luma p1/p5/p50/p95/p99.5 | | 35/56/144/214/241 | 45/62/140/216/233 | 19/29/**93**/190/230 | 10/15/**55**/168/206 |
| contrast (luma std) / sat mean | | 48 / 63 | 47 / 52 | **49 / 105** | **38** / 67 |
| mean-frame vignette r = .4/.6/.8/.95 | .74/.56/.34/.22 | .93/.79/.57/.41 | .91/.77/.59/.45 | .84/.68/.54/.43 | .80/.63/.45/.35 |
| outline width on CUs | 2-4 px @854 | | ≈3.8 px @1280 (≈7.6 @2560) | ≈3.8 px @1280 | plan 10-12 @2560 |
| grain / chromatic aberration | none | | 0.5 levels (codec floor) / none | 0.45 / none | |
| narration wpm / pauses > 1.2 s | | 166 / 0.5 per min | 186 / 1.0 per min | 176 / 0.65 per min | 187 |
| mix LUFS | -14.5 | -14.4 | -15.0 | -14.9 | |

How to read this:
- v1 is **not slow in cutting** (27.8/min is old-reference speed). Its problem is that **it is slow inside the shots**:
  - pushes are half as fast (median 1.6 %/s against 2.6-3.1);
  - subjects move half as often (0.19 against 0.32-0.36);
  - the per-shot motion energy is 1/2 to 1/3 of the references.
- v1 is **dark and flat**: the median luma is 55, against 93 for the night-set stadium, and the contrast std is 38 against 47-49.

Data: `_work/ref2/data/{cuts30,motion,motion_summary,captions,asr}_*.json`, `look_v2.json`; v1: `cuts30_v1.json`, `motion_v1.json`.

---------------------------------------------------------------------------------------------------------------------

## 2. The hooks (first 30 s)

Grabs: `_work/ref2/sheets/{teacher_dog,stadium,hazmat720}_hook_0-30s.jpg` (1 fps), `sheets/keys/td_hook_flashfwd.jpg`, `st_hook_tags.jpg`, `td_title_kinetic.jpg`, `st_title_kinetic.jpg`, `hz_ending_reveal.jpg` (the first two frames are the hazmat cold open).

**teacher_dog (20 cuts):**

| time (s) | shot | narration |
|---|---|---|
| 0-2.0 | classroom door; the teacher is a **pure black silhouette** in the doorway with the dog | "If your teacher ever walks into class" |
| 2.0-3.3 | closer; the dog on a red leash | "with your dog on a leash" |
| 3.3-3.7 | dog close-up | |
| 3.73-4.6 | **kinetic title "IGNORE HIM."** over a darkened, blurred dog CU | |
| 4.6-5.8 | the boy (you) claps a hand over his mouth | "Don't say his name" |
| 5.8-7.0 | POV hand waving | "Don't call him over" |
| 7.0-8.6 | MS: the teacher at the front of the class with the dog | "and whatever you do" |
| 8.6-10.5 | **ECU of the teacher's eyes** in a black vignette | "don't tell her he's yours" |
| 10.5-12.8 | wide from behind her over the class | "because she isn't asking whose dog he is" |
| 12.8-14.7 | insert: her fist grips the red leash | "she's waiting to see who comes to get him" |
| 15.1-16.5 | school exterior: buses, BUS LANE, flag, WILLOW CREEK sign | "It's Monday morning" |
| 16.5-18.3 | alarm clock **3:12** in a blue night room | "Last night at 3:12 a.m." |
| then | the backstory, one shot per clause: dog barking, boy yelling, doggy door ripped off, gate open, empty bowl | |

**stadium (22 cuts):**

| time (s) | shot | narration |
|---|---|---|
| 0-2.1 | two aerial shots, pushing into a 3D stadium in a night city | "If you're ever sitting in a packed stadium" |
| 2.1-4.7 | the crowd cheering, then **the whole crowd turns to camera** | "the entire crowd suddenly turns toward you" |
| 4.7-6.4 | identical smiles, with a white flash on the cut | "with the exact same smile" |
| 6.37-7.83 | **kinetic title "DON'T SMILE BACK!"** over a desaturated crowd | |
| 7.8-9.0 | POV hand waving | "Don't wave at them" |
| 9.0-10.7 | the SMILE CAM jumbotron, red X drawn over it | "don't look up at the giant screen" |
| 10.7-14.6 | camera on a tripod with a red light, then a bank of cameras, then the viewfinder POV of the crowd (ON AIR, CAM 4, ISO) | "don't let the stadium cameras see your face" |
| 14.6-17.4 | the crowd; a woman's grin with tears | "because they're happy" |
| 18.4-21.9 | **labelled flash-forwards**: SMILE CAM shots chipped "RULE 2", "RULE 4", "TONIGHT" in the bottom-left, with glitch tears | |
| 21.9-24.0 | a man's smile widens on camera | "it gets to make you do the same thing" |
| 24.0-26.7 | **RULE 1 card on the jumbotron**, typed word by word | "DON'T SMILE BACK!" |
| 27.0 | time card "SATURDAY NIGHT / CROWN POINT STADIUM" | |

**hazmat720 (re-cut cold open, 15 cuts):**
- 0-0.4 s: a flash of the villain's mask, red lenses glowing, white rim glow, red "9:03 PM" chip.
- 0.4-1.2 s: a CCTV-like shot of the suit's legs at the shutter.
- 1.2-3 s: a van with a rotating beacon, labelled HAZARDOUS MATERIALS RESPONSE.
- The old copy had a static exterior here.

**What the hooks share (and diver and the old hazmat did not):**
- The villain appears in the first 2 s, as a part or a flash: a silhouette, a mask, a crowd of smiles.
- The title command is a **full-screen kinetic type card** of 0.9-1.5 s, not a small tag.
  - First word in white, with an elliptical ring flash.
  - Second word in red, with an RGB-split glitch-in.
  - stadium adds a red smile-curve underline.
  - The background is darkened, desaturated and blurred.
- The premise line ends on a **labelled teaser** of later moments: corner chips (RULE 2 / RULE 4 / TONIGHT), or a red frame with a "3:00 PM" chip (teacher_dog 1:59-2:03).
- Then come a hard time card and an establishing wide.

---------------------------------------------------------------------------------------------------------------------

## 3. How they make the story easy to follow (the main lesson)

### 3.1 One clause = one shot = one caption
- 66-75 % of cuts land on a clause start, with the picture leading by 0.15-0.17 s.
- 70-74 % of caption changes land within 0.2 s of a cut.
- Captions are 2-5-word phrase chunks with a soft cross-fade of about 0.15 s (`sheets/keys/caption_band_strips.png`: teacher_dog 49-54 s and stadium 56-61 s at 5 fps). For the shot rhythm see `sheets/keys/td_pershot_125-245s.jpg`.
- The viewer never reads a caption that describes a different picture.

### 3.2 Every noun gets a shot
- teacher_dog 0:49-0:59: "The floppy ear, the white patch on his chest shaped like a star, his blue collar. But his name tag is missing."
  - This gives **four inserts in 6 s** (ear 0:52, star 0:54, collar 0:56, missing tag 0:58).
  - The star patch pays off at 13:48 ("his blue collar is gone").
- A simile is pictured too: "gray, like old candle wax" becomes a candle insert at 4:12.
- Clue and evidence objects: the bandaged hand with a blood spot (0:44), muddy shoes (0:42), the red leash (0:48), the leash tied to the desk leg (2:56), a marker in the bandaged hand (3:10), the "NO PETS ALLOWED" sign on Ava's building (3:44, which proves a lie), the dog tag "BISCUIT · 27 WILLOW LANE" (8:26).
- Grab: `sheets/keys/td_inserts_clarity.jpg`.
- Hand-classified shot mix (teacher_dog 2:10-4:05, 63 shots; stadium 0:27-2:27, 79 shots):

| | wides (WS/EWS) | MS / 2-shot / OTS | faces (MCU/CU/ECU) | inserts, UI, screens | POV hands | split / card |
|---|---|---|---|---|---|---|
| teacher_dog | **38 %** | 13 % | 21 % | **21 %** | 5 % | 3 % |
| stadium | **42 %** | 14 % | 27 % | **14 %** | 1 % | 3 % |
| our plan (shots.json) | **8.5 %** (WS 26 + EWS 1) | 30 % | **50 %** (CU 79, ECU 74, MCU 7) | 10 % (INSERT 24 + UI 7) | 1 % | 2 % |

### 3.3 Wides keep the geography alive
- The classroom is shown from at least 12 angles in 2 minutes: front, back, high, low, through legs, over the teacher's shoulder, from the doorway.
- The stadium is shown from at least 15: aerial, bowl, stands, field level, banner, light rig, camera platform, tunnel, concourse.
- After every rule card and every location change there is a wide.
- Wides are **3D perspective with a wide lens**: ceilings with light panels, floors with converging lines, 20-25 individual kids per classroom wide, thousands of seated fans. (`sheets/keys/td_sets.jpg`, `st_sets.jpg`, `td_classroom_full_0032.jpg`)

### 3.4 Persistent identifiers
- Places carry the same ID everywhere:
  - teacher_dog: "ROOM 14" on the door plate, in the header, on the staff record and on the lost-and-found box;
  - stadium: "SECTION 214 · ROW H · SEAT 12" on the ticket insert, the section signs, the smile-cam lower third and the kinetic type card.
- People carry labels: name patches (DALE), the desk nameplate MRS. CRANE, the EVENT STAFF vest.
- **Colour coding**:
  - In stadium the villain is the only person in a red jersey (00) in a blue-and-yellow world.
  - In teacher_dog red belongs to the villain's leash, and "you" is always the blue hoodie (MCU) or blue sleeves (POV).
  - The best friend's blue face-paint stripes make him findable in a crowd of hundreds.

### 3.5 Time is made visible
- teacher_dog uses the **classroom clock** as a recurring insert: 0:36, 1:52, 3:09 (with a chip "10:15 MONDAY · ROOM 14"), 3:34, 10:20. It walks toward the 3:00 bell, which is the deadline.
- The 3:12 a.m. alarm clock opens and closes the film: 0:16 and 13:28 / 13:42 (3:11, then 3:12 again: the loop).
- stadium keeps the scoreboard ("HOME 21 · 4TH 8:39 · AWAY 14") in every jumbotron shot.

### 3.6 Flash-forwards and flashbacks are coded, never ambiguous
- teacher_dog teaser (1:59-2:04): desaturated, a **red border**, a red "3:00 PM" chip top-left and a running timer top-right.
- stadium hook: corner chips "RULE 2", "RULE 4", "TONIGHT" plus glitch tears.
- CCTV is its own look: night-vision grey, "BACK PORCH · 03:12:48 AM", REC, IR ON, the date, CAM 2, fisheye.
- Comparisons are split-screens with chips: "1984" | "TODAY" (8:02) and eye | clock (2:51).

### 3.7 The mystery is explained with evidence, mid-film and at the end
- teacher_dog 5:06-6:04 (36-41 %):
  1. mom's text (phone UI);
  2. the CCTV clip on the phone, with a player scrubber;
  3. the clip shows a long arm through the doggy door, the bite, a tall woman standing up and leaning into the lens: "It's Mrs. Crane".
  - This answers the setup question ("She didn't find Biscuit... She came to yours").
- teacher_dog 7:20-8:02:
  1. the lost-and-found box;
  2. a pile of collars;
  3. engraved years 1981 / 1994 / 2011;
  4. the framed faculty photo "1984, FORTY-TWO YEARS AGO";
  5. the 1984 | TODAY split.
  - The truth comes in five readable steps.
- hazmat ending 8:42-9:00:
  1. a dispatch printout typing on screen;
  2. keywords marked with a **yellow highlighter**;
  3. a red rubber stamp "NO CONTAINER FOUND";
  4. a handwritten incident note with a red underline ("LOCKED FROM INSIDE").
  - Then the villain in a spotlight, and a closing symbolic image: empty chairs under one lamp, a red-eyed figure behind them.
  - Grab: `sheets/keys/hz_ending_reveal.jpg`.
- teacher_dog ending: the loop is explained by a phone community post ("Found this sweet boy wandering near my house...") plus a new teacher with a bandaged hand.

### 3.8 Set-up and pay-off are both shown
- The FIELD LIGHTING EMERGENCY SHUTOFF sign and switch (10:34) are used 10 s later (10:44), then the lights go out.
- The seat ticket (3:20) returns as the lower third at the end (12:42).
- The dog's star patch and collar return at 13:48.

### 3.9 How a rule is visualised
1. The card is a story object (`sheets/keys/td_rulecard_anim.jpg`, `st_rulecard_anim.jpg`).
   - teacher_dog: a "HAVE YOU SEEN HIM?" lost-dog flyer with tear-off tabs, pinned between "READ EVERY DAY" and "BOOK FAIR NOV 16-20" posters.
     - "RULE" is in red marker, then the number is scribbled in.
     - The statement writes on word by word in bold dark caps, and a red marker underline lands under the command ("IGNORE HIM").
   - stadium: a red LED jumbotron with smiley icons, "FILE 093 · SECTION 214" and a scoreboard strip. Its look **evolves**: rule 5 is seen through a camera viewfinder (REC), and rule 7 is an inverted white board with red text and pixel glitch.
2. The **shot right after the card shows the temptation in POV**: your hands on the desk (2:09.8), your hand waving (stadium 1:06). The next line, "Don't.", gets a reaction CU.
3. LIKE / SUBSCRIBE sits on the rule 1 and rule 2 cards, now with an animated **cursor that clicks** LIKE, SUBSCRIBE and the bell (teacher_dog 2:05-2:09).

---------------------------------------------------------------------------------------------------------------------

## 4. How they build tension

### 4.1 The villain has a reveal ladder
Grabs: `sheets/keys/td_villain_build.jpg`, `st_faces_build.jpg`, `td_inshot_motion.jpg`.

**teacher_dog: Mrs. Crane**

| time | % of runtime | what we see | stage |
|---|---|---|---|
| 0:01 | 0 | a black silhouette in the door | shape only |
| 0:09 | 1 | ECU of the eyes | part |
| 0:38-0:48 | 4-5 | wet hair, muddy shoes, bandaged hand, red leash: details before the face | parts |
| 1:16 | 9 | "She smiles": a thin smile grows on camera | normal but uncanny |
| 2:50-2:52 | 19 | "She doesn't blink. Five seconds.": eye ECU, then an eye \| clock split | behaviour |
| 3:13 | 22 | writes on the board without looking | behaviour |
| 5:16-6:04 | 36-41 | CCTV: crawls, takes the dog, leans into the lens; **empty white eyes** | first physical wrongness, safely "recorded" |
| 8:16-8:48 | 56-60 | the silhouette at the top of the basement stairs, closer every cut, a gloved hand reaching | proximity |
| 10:04 | 68 | "the corners of her lips crack open": dark slits | distortion 1 |
| 11:10 | 76 | the cracks run up the cheeks | distortion 2 |
| 11:51-12:00 | 80-81 | "her real face": the jaw drops, then the mouth tears open toward the ears, a red maw down to the chest with a single row of teeth | distortion 3 |
| 12:02-12:42 | 82-86 | the eyes fill dark red, glowing red with black veins and tears; "her jaw slowly slides back into place" | full monster, then retracted |
| 14:24 | 98 | a new teacher, same bandage | loop |

**stadium: the smile**

| time | % | what we see |
|---|---|---|
| 0:04 | 0 | the crowd turns |
| 0:16-0:23 | 2 | grins with tears; a man's grin widens on camera |
| 1:26-1:56 | 10-14 | wide-open eyes, stretched grins, 5-8 crease lines on each cheek |
| 2:14-3:00 | 16-22 | the friend is infected: tears plus a grin he cannot stop |
| 2:38 | 19 | the man in the red 00 jersey appears on the screen ("pale, and horribly stretched into a smile") |
| 3:04 | 22 | he sits right behind you on the smile cam |
| 9:16-9:30 | 67-69 | he stands in the tunnel: bloodshot eyes, gums exposed, the cheeks pulled into deep folds |
| 10:20-10:26 | 74-76 | his jaw opens and he speaks |
| 10:40 | 77 | he runs at you |
| 11:12-11:42 | 81-85 | in the dark, lit by one spotlight; ECU with the mouth hanging open |
| 13:08 | 95 | your own face on the phone, glitching into the grin |

The pattern in both:
- The villain is first **normal-but-wrong**: details, then behaviour.
- Then come **recorded / once-removed** horror: CCTV, a screen.
- Then **proximity**: stairs, tunnel, behind you.
- The full distortion arrives only at **75-85 %** of the runtime, and it is held.

### 4.2 Transformations happen on camera, in the longest shots of the film
- Longest shots: teacher_dog 12:37.2-12:43.2 is 6.0 s, its longest shot (the jaw slides back in shot). 11:56.9-12:00.6 is 3.7 s (the mouth tears open while the camera pushes from half-frame to full-frame).
- stadium's grin morphs: 0:21.9-0:24.0 and 1:54-1:57.
- The refs' shots > 3 s are only 3-5 %, and **they are spent on the villain**.
- Push speeds on those shots are 3-6 %/s, with a slight head sway; the face is never frozen.

### 4.3 Uncanny behaviour before horror
- "Doesn't blink. Five seconds." is shown as a split: her eye | the clock's second hand.
- Writing without looking; crawling through a doggy door; a whole crowd turning at once; thousands "whispering the same numbers".
- The stadium countdown is drawn as **giant red numbers in red rings**, full screen: 3, 2, 1 at 5:38-5:40, over a 6-face grid of identical grins (5:36).
- Grab: `sheets/keys/st_title_kinetic.jpg` (last frames), `st_hook_tags.jpg`.

### 4.4 Rhythm devices
- **White flash cuts**: stadium 63 (4.6/min), teacher_dog 28 (1.9/min). They come on stingers, often with an RGB or pixel glitch; one is a red-tint impact frame with radial speed lines (stadium 6:56). Grab: `sheets/keys/st_flashes.jpg`.
- **Punch-ins**: teacher_dog 1.9/min at a subtle ×1.08; stadium 1.2/min at ×1.25.
- **Cut rate rises in the climax** in teacher_dog only: min 8 = 47/min, mins 10-14 = 40-41, against 31-37 elsewhere. stadium stays flat at about 40.
- **Narration pauses** of > 1.2 s, about once a minute, always right before the reveal line: "Then, the camera stops. | Right on you."; "Five seconds. | Then she smiles."
- The mix never drops out (≤ 0.2 drop-outs per min). The loudest 3 s windows are the title hit (stadium 6.6 s), the rule cards (teacher_dog 124.7, 530.7, 694.8; stadium 24.3, 205.3, 287.9, 598.2) and the climax.

### 4.5 Light arc
- stadium luma by tenth: 90 96 99 97 121 **142** (bright concourse) 96 87 **73** (lights out) 85. The darkest tenth is the climax, with deep navy, star-like specks and red lights.
- teacher_dog luma by tenth: 137 139 141 111 127 129 146 122 124 **100**. The last tenth is the blue night at home.
- Our v1 by tenth: 58 56 49 60 **147 142 125** 104 65 41. Four tenths sit at luma ≤ 60, so the dark is not saved for the climax.

---------------------------------------------------------------------------------------------------------------------

## 5. Characters

Grabs: `sheets/keys/td_cast_normal.jpg`, `st_cast_normal.jpg`, `td_villain_build.jpg`, `st_faces_build.jpg`.

### 5.1 Normal people (close to our cast; keep)
- **Heads and faces**: round or oval heads, flat skin with a soft blush, almond eyes with coloured irises and a white highlight, a two-curve nose, a small mouth.
- **Line**: uniform dark outlines of about 3.8 px @1280 (≈ 7.6 px @2560, a little thinner than our 10-12).
- **Bodies**: chunky, mostly frontal and centred in MCU. Clothes are flat colour.
- **Identity props**:
  - DALE name patch;
  - EVENT STAFF vest and radio;
  - face paint;
  - hoodie colour;
  - a referee's stripes.
- **Fear**: round white eyes with small pupils and raised brows; a mouth "O" or flat line; a hand over the mouth (1:32); **tears that stream** (stadium 2:14, 3:00); sweat drops.
- **Close-ups always sit on a defocused background**:
  - teacher_dog: 3-4 soft colour blobs (the classmates);
  - stadium: white bokeh discs, Ø 30-110 px @1280, +22-38 luma over the surround (`st_face_cu_bokeh` family).

### 5.2 Villains are built from a human archetype, with a different drawing finish
- **Mrs. Crane**:
  - A realistic, long, thin face on a very tall, thin body (about 2× a kid's height at 4:30).
  - Pale grey-white skin with a subtle paper or charcoal texture; thin loose hair strands across the face; small light-blue eyes; thin lips.
  - She is cartoon-normal enough to pass as a teacher, but is drawn in a finer, more "realistic" line than the round kids.
  - Signature: **the bandaged right hand** (a bite). It is seen in her first scene, at the reveal and on the replacement teacher.
- **The smiling man**:
  - An ordinary fan face turned pale, with **cheek-fold creases**, bloodshot red-rimmed eyes, a grin of individually drawn teeth with **exposed gums**, and tears.
  - Signature: the **red 00 jersey**.
  - On screens he gets **scanline / CRT texture** (2:38, 2:46).
- **Hazmat**:
  - No face: a mask with **two glossy red lenses and a scratch across the left lens** (the identifier).
  - A white rim-glow outline when isolated on black.
- **The distortion vocabulary is built on the same face**, step by step:
  1. eyes: blue → empty white (CCTV) → dark red → glowing red with black vein cracks;
  2. mouth: thin smile → cracks at the corners → jaw dropped → torn to the ears with a red maw;
  3. skin: creases and folds, then tears.
- **The villain gets the strongest light**: a spotlight with a white flare (11:12), a radial white-green glow behind the head (9:22), a red glow and rim on the mask.

### 5.3 Against our Queen of Spades (v1 grab: `sheets/keys/v1_keys_for_comparison.jpg`)
- v1's queen is a generic creature: long black hair, pale face, huge bloodshot eyes, a shark-tooth grin.
- She shows that full face at 4:44 (40 %) and 7:59. There is no normal-looking stage, and her signature is not legible.
- In the references the face is **a person first**, with one recognisable signature. The monster is a distortion of that same face, revealed on camera at 75-85 %.

---------------------------------------------------------------------------------------------------------------------

## 6. Sets, light and colour

### 6.1 Build
- 3D perspective, wide lens (slight barrel curvature in concourses and tunnels), and strong one-point perspective in corridors, aisles, stairs and library stacks.
- Ceilings with light panels, floors with lines and tiles, foreground occluders (desk edges, door frames, seat backs).
- Dense props: posters, flags, clocks, maps, lockers, books; HOT DOGS / NACHOS stands; banners such as "WELCOME TO CROWN POINT STADIUM ★ MAKE SOME NOISE!".
- Real crowds: 20-25 kids, thousands of fans.
- Old diver, by contrast, was a flat front-on stage, and so is most of our v1 (side-on cabin walls and bunks).
- Grabs: `sheets/keys/st_sets.jpg`, `td_sets.jpg`, `td_classroom_full_0032.jpg`.

### 6.2 Palettes per scene family (1 fps frames, caption band removed; `data/look_v2.json`; check strip `sheets/fam/families_check_v2.jpg`)

| family | luma p1/p5/p50/p95/p99.5 | std | sat mean/p90 | hue | vignette .4/.6/.8/.95 | palette (most frequent first) |
|---|---|---|---|---|---|---|
| td classroom day | 43/68/146/221/234 | 47 | 53/136 | – | .96/.87/.68/.53 | #d1cdc5 #78796e #9c998e #b2ada1 #464e4c #447e81 #b88e47 |
| td night home (blue) | 20/26/65/123/179 | 29 | 123/170 | 223° | .80/.66/.46/.34 | #26304f #3d4f64 #15192b #5b6375 #8d8d92 + warm #a64e42 |
| td CCTV night-vision | 9/14/57/180/226 | 54 | 8/24 | – | .58/.38/.24/.13 | greys #171818 → #cacbca |
| td villain CU (class) | 40/54/166/229/236 | 53 | 30/74 | – | .91/.75/.58/.42 | #e1d9d3 #bdb9b4 #949696 #717470 #393c3b |
| td villain reveal (outdoor) | 19/36/132/209/234 | 56 | 59/130 | 224° | .80/.69/.51/.35 | #4d5249 #6c7a7d #99a5ad #d0cdca + maw #3a1e23 |
| td rule card (flyer) | 44/56/156/234/244 | 60 | 49/137 | – | .94/.77/.50/.35 | #afa9a9 #706851 #e1dedb + red #d0435b |
| td lost and found (warm) | 33/40/76/154/210 | 35 | 114/145 | 28° | .78/.58/.41/.32 | #453426 #6d543f #271f17 #9a6e58 + red #93272d |
| st bowl, lit night | 19/25/89/189/229 | 50 | 119/201 | 214° | .83/.66/.47/.38 | #424f64 #1c2438 #a7abb4 #6f7d91 #355ca8 + field #49ac65 |
| st face CU + bokeh | 20/24/90/180/214 | 45 | 131/212 | 212° | .75/.66/.55/.44 | #9192a0 #3766b8 #334c6f #1e2231 #b1b1bc |
| st villain ECU | 16/26/83/208/230 | 60 | 86/152 | 225° | .77/.54/.37/.28 | #1a213b #d9c8c0 #a18e86 #bfa89f #424456 |
| st rule card (jumbotron) | 10/20/66/184/231 | 49 | 135/236 | 317° | .71/.50/.39/.34 | #23202f #4d597a **#a01324** #9d989f #c74555 |
| st lights out (climax) | 9/13/34/86/128 | 22 | 166/215 | 228° | .69/.54/.41/.32 | #172946 #0f142e #383656 #0a050e #40527b + red lights |
| st concourse / tunnel (bright) | 35-38/58-65/156-162/215-231/234-243 | 43-52 | 38-52/125-188 | – | .94-1.02/.84-.86/.67-.74/.53-.60 | #838790 #d3d2d4 #afaeb2 + accent red #b42128, blue #274fac |
| hz documents | 24/31/220/253/254 | 90 | 49/149 | – | .89/.61/.26/.12 | paper #f3f4f0 on dark #1e2832, yellow highlight |
| hz end, dark | 3/5/13/120/176 | 36 | 95/170 | 238° | | #06070c #292021 + red #c02a28 |

Lessons:
- A night scene in these films is **deep, saturated navy with bright practicals**: sat 119-166, p95 186-190.
- Even the darkest climax keeps a p50 of 34 and points of light. It is never grey murk.
- Bright interiors (concourse, tunnel, classroom) are near-white with low saturation (38-53) and strong vignettes, which makes them a relief between night scenes.
- The documents family is the brightest frame type (p50 220).

### 6.3 Texture
- No grain beyond the codec floor (0.45-0.51 levels) and no chromatic aberration.
- The "film" feel comes from a soft overall bloom on ceiling and stadium lights, the strong vignette (mean frame .54-.59 at r = 0.8), and:
  - scanlines on screen-world shots;
  - night-vision noise on CCTV;
  - glitch tears on transitions.

---------------------------------------------------------------------------------------------------------------------

## 7. VFX inventory (newer films)

- **Bokeh discs** drifting behind every stadium close-up. **Soft colour-blob DOF** behind teacher_dog close-ups.
- **Glitch** in and out of screen and teaser material: RGB split, horizontal tears, pixel blocks. Used on the title card, the hook chips, the rule card (rule 7) and the final phone face (13:08-13:12).
- **White flash cuts** at 1.9-4.6/min; a red-tint impact frame with radial speed lines (6:56).
- **Light**: stadium light-rig flares, a villain spotlight, emergency red lights, a white rim glow on the villain against black (hazmat 9:00), red eye glow (Crane 12:18+).
- **Particles**: confetti on SMILE CAM celebrations; a light sweep on the camera lens; tears and sweat as animated drops.
- **Screen treatments**: scanlines and CRT texture on the jumbotron; a viewfinder overlay (ON AIR, CAM 4, timecode, ISO 800, framing brackets, battery); a CCTV overlay.
- **Typewriter text** on documents, a **highlighter swipe**, a **rubber stamp slam**, and a **marker underline** on rule cards.

---------------------------------------------------------------------------------------------------------------------

## 8. UI and on-screen text

| element | spec (newer films) |
|---|---|
| captions | white bold caps, letter-spaced, soft dark shadow; centred at y = 0.893 H; phrase chunks of median 1.13-1.20 s (p10 0.33-0.40, p90 2.0-2.1); width 30-33 % of W; 41-45 per minute; on screen 92-93 % of the time; soft fade between phrases; hidden under rule cards |
| header | unchanged: "FILE 094 · ROOM 14 // INTRODUCTION" or "... // RULE n OF 7" top-left, running timecode top-right, both at about 20 % opacity |
| rule card | a story object 50-70 % of frame width (the flyer or the jumbotron), with its world filling the rest (corkboard posters, stands); written word by word; red keyword underline; LIKE / SUBSCRIBE with a cursor on rules 1-2; visible 2.7-4.9 s |
| kinetic title | 1 per film, 0.9-1.5 s, full screen (§2) |
| typographic beats | SECTION 214. ROW H. (giant on the jumbotron, then echoed grey); countdown 3-2-1 in red rings; "46,000 FANS" infographic over the aerial; "TONIGHT'S SMILE CAM WINNER!" sunburst card; closing "DON'T SMILE" echo |
| chips | "3:00 PM" (red, flash-forward); "1984" / "TODAY" (split); "RULE 2" / "RULE 4" / "TONIGHT" (teaser); "10:15 MONDAY · ROOM 14" (clock); "SECTION 214 · ROW H · SEAT 12", "MIDFIELD", "SMILE CAM · LIVE" (lower thirds) |
| phone UI | realistic: Messages thread, a video player with a scrubber, a social "Posts" feed with a verified badge, a lock-screen notification; held in cartoon hands over a bokeh background |
| documents | a dispatch printout (tractor-feed holes, typed fields), a clipboard incident note (handwriting), a staff record card with a photo, a framed staff photo with a caption plate; all with highlighter, stamp and underline |
| CCTV | "BACK PORCH · 03:12:48 AM", REC, IR ON, "11-09-2026 MON", CAM 2, night-vision grey, fisheye |
| red X / command tags | almost gone: 1 red X per film; no pill tags in teacher_dog or stadium |

---------------------------------------------------------------------------------------------------------------------

## 9. What the author upgraded since diver and hazmat, precisely

1. **Pace**: from 24-29 to 36.5-39.5 cuts/min. The median shot drops from 2.0-2.3 to 1.5-1.6 s, shots under 1 s go from 11-14 % to 20-23 %, and captions from 30/min to 42-45/min. Picture and narration are tighter: 75 % of cuts on a clause, 0.15 s lead.
2. **Cold open**: from a static exterior plus a small tag to a villain flash in the first second, then a full-screen kinetic title, then labelled teasers. In stadium, rule 1 comes at 24 s.
3. **Rule card**: from a generic hazard sign or whiteboard to the film's own central object (lost-dog flyer, jumbotron). It changes look as the story escalates and carries an animated LIKE / SUBSCRIBE cursor.
4. **Inserts and evidence**: from about 1/min to about 4-6/min. Documents now have highlighter, stamp and underline; there are CCTV and phone video clips, and split-screen comparisons with chips.
5. **Coverage**: from flat front-on stages (diver) to 3D-perspective sets shot from 10-15 angles, with about 40 % wides and real crowds.
6. **Villain**: from a fixed design (mask, or a creature in the dark) to a human archetype with a signature prop, distorted in 4-6 stages on camera, with the climax distortion held for 3-6 s.
7. **Faces**: tears, cheek folds, exposed gums, bloodshot eyes, red veins; stronger expression range on the normal cast; DOF or bokeh behind every close-up.
8. **Typography**: 3-5 full-screen type beats per film (place IDs, countdowns, a bookend).
9. **Transitions**: white flash and glitch cuts up from 1.4/min to 1.9-4.6/min; red X and pill tags dropped.
10. **Kept**: header, captions, rule-card timing (lead 0.2-0.5 s, cut 0.15-0.35 s after the sentence), vignette, clean vector line, no grain, and the audio template.

---------------------------------------------------------------------------------------------------------------------

## 10. Techniques to adopt for the Queen of Spades film, ranked

Each item names the number to hit. "Ours" means v1 or the plan.

1. **Rebuild the Queen as a reveal ladder.** This is the owner's main ask; the reference is §4.1 and §5.2.
   - Design her as a *person first*: a regal, playing-card-like woman in black, with one legible signature she always carries (for example a spade motif and the perfect red lips). Draw her with a finer, more "real" face finish than the cast, and make her tall and thin.
   - Stage her: parts or silhouette, then normal-but-wrong behaviour (no blink; head turning too far), then a recorded or once-removed view (inside the glass), then proximity (the step below yours), then 3-4 distortion stages of *the same face*.
   - Hold the full-monster face for the last 20-25 % (from about 530 s). At 283.7 s use a middle stage, not the full face.
   - Every stage change happens **on camera** in a held 3-6 s push of 3-6 %/s, synced to the words. These are the only long shots.
2. **Show the geography.**
   - Raise wides from 8.5 % to 30-40 % of shots, and cut faces from 50 % to about 25 %.
   - Give each location a 3D-perspective master: camp gate, mess porch, Cabin 7 interior, the mirror wall, the dawn cabin, the staircase.
   - Shoot each master from 3-5 angles (high, low, through the bunk legs, from the doorway) and re-establish after every rule card and every jump between sides.
3. **Every noun gets a shot: 4-6 inserts/UI per minute** (our plan: 2.7/min, INSERT 24 + UI 7). Use one insert per identifying detail and per clue:
   - the seven steps counted on screen, with the eighth highlighted;
   - the taped fingers;
   - the candy;
   - the bell crack;
   - the watch alarm 6:45 → 4:45;
   - the voicemail;
   - the MISSING poster with its key line highlighted.
   - Explain the mystery with **evidence sequences**: the incident report with a highlighter and a stamp, and a NOW | THEN split with chips.
4. **Code the two worlds and time unambiguously.**
   - A persistent chip system: "CABIN 7 · 12:0x AM" for our side; "6:59 AM · 14 YEARS AGO" for the dawn side and memories; a red-bordered teaser look for flash-forwards.
   - A recurring wall-clock insert that walks the deadline.
   - Split screens for "the same place, two times" (the 1984 | TODAY device).
5. **Tighten the cut: 36-40 cuts/min, median 1.5 s, 20 % under 1 s, 1 clause = 1 shot = 1 caption** (ours: 27.8/min, median 2.03 s).
   - Phrase-chunk captions of median 1.2 s, changing on the cut, with the picture leading the clause by 0.15 s.
6. **Light and colour: night must not be murky.**
   - Night shots: luma p50 from 41-60 to about 80-95, contrast std from 38 to about 48, deep saturated navy with bright practicals (flashlight, moon, lantern). The p95 should reach about 190.
   - Dawn and "their side": keep it bright and pale (classroom family p50 146, sat 53).
   - Save the darkest tenth for the climax, with points of red light (stadium lights-out p50 34).
   - Put bokeh discs or soft colour blobs behind every close-up.
7. **Motion inside shots**: push median from 1.6 to about 3 %/s (p75 5-6), subject motion share from 0.19 to about 0.33, per-shot frame energy about 2× v1.
   - Moving things include cloth, hair, dust in the beam, tears, a breathing push and hands.
   - Add white flash or glitch cuts at 2-4/min on stingers (ours: 0) and punch-ins at 1-2/min.
8. **Typography as structure.**
   - One full-screen kinetic title in the hook for "WIPE THE GLASS CLEAN": white words with a ring flash, the red keyword with an RGB split, 0.9-1.5 s, darkened and blurred background.
   - 3-5 more type beats: "SEVEN STEPS." / "EIGHT."; Tess's countdown 60 / 45 / 20 / 5 as giant red numbers in rings instead of a small corner pill; a closing echo of the title.
9. **The rule card is the mirror itself, and it evolves.**
   - Full-frame, the brightest frame of its section, lipstick written word by word with a red keyword underline, and a cursor-click LIKE / SUBSCRIBE on rules 1-2.
   - Its look degrades as the story goes on: smeared, cracked, red-lit by rules 6-7.
   - Visible 2.7-4.9 s, appearing 0.2-0.5 s before "Rule".
   - Right after each card, show the temptation in POV.
10. **The hook.**
    - A 0.4-1 s flash of the Queen in the glass with a red time chip before the first line.
    - One shot per clause, 20-22 cuts in 30 s.
    - The premise line closes on 2-3 labelled teaser flashes ("RULE 4", "6:59 AM").
11. **Cut red X marks and command tags to 1-2 in the film** (the plan has 6 red X and 13 HUD tags). The newer films use one red X each and no pill tags; let kinetic type and inserts carry the commands.
12. **The ending**:
    - Close the loop with one readable artefact (in the refs, a phone post).
    - Echo the title in type.
    - Put the villain's last appearance in one symbolic still-but-moving image, like the hazmat empty chairs with red eyes behind them.

---------------------------------------------------------------------------------------------------------------------

## 11. Files

- Contact sheets (2 s steps): `_work/ref2/sheets/{hazmat720,teacher_dog,stadium}_NNN-NNNs.jpg`; hooks at 1 fps: `*_hook_0-30s.jpg`.
- Key frames, all in `_work/ref2/sheets/keys/`:
  - villains: `td_villain_build.jpg`, `st_faces_build.jpg`;
  - in-shot motion and morphs: `td_inshot_motion.jpg`, `st_inshot_motion.jpg`;
  - rule cards: `td_rulecard_anim.jpg`, `st_rulecard_anim.jpg`;
  - kinetic titles: `td_title_kinetic.jpg`, `st_title_kinetic.jpg`;
  - inserts and UI: `td_inserts_clarity.jpg`, `st_inserts_ui.jpg`;
  - sets: `td_sets.jpg`, `st_sets.jpg`;
  - cast: `td_cast_normal.jpg`, `st_cast_normal.jpg`;
  - hooks: `td_hook_flashfwd.jpg`, `st_hook_tags.jpg`;
  - flashes and game clock: `st_flashes.jpg`, `st_gameclock.jpg`;
  - one thumbnail per shot: `td_pershot_125-245s.jpg`, `st_pershot_027-147s.jpg`;
  - hazmat cold open and ending: `hz_ending_reveal.jpg`;
  - full-res singles: `td_classroom_full_0032.jpg`, `td_crane_full_0116.jpg`, `st_face_full_0126.jpg`;
  - our v1 at 12 moments: `v1_keys_for_comparison.jpg`.
- Scene families: `_work/ref2/sheets/fam/fam_*.jpg` and `families_check_v2.jpg`.
- Data in `_work/ref2/data/` (decoded frames and audio deleted):
  - `cuts30_*.json`, `motion_*.json`, `motion_summary_*.json`;
  - `captions_*.json`, `asr_*.json` (timed words from the mix);
  - `look_v2.json`;
  - the same `cuts30` / `motion` files for `v1`.

Limits:
- The sources are 720p at 210-360 kbps, so the grain and edge numbers are bounds.
- ASR ran on the mix, not a separated voice; word times are good to about ±0.1 s.
- Shot-type shares come from two hand-classified 2-minute windows.
- The red-X count is from a heuristic detector plus the contact sheets; small, brief overlays could be missed.
