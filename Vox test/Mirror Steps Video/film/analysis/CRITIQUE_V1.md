# CRITIQUE_V1: a harsh review of the Queen of Spades film, v1

Subject: `_work/deliver/If_An_Eighth_Step_Appears_EN_1440p60_HEVC.mp4` (700 s, 317 shots).
Compared with the five new references in `_work/ref2/` (hazmat720, teacher_dog, stadium, sibling_stitched, vet_dog).
This file is the owner's critic, not the plan. It covers what is broken, what a first-time viewer will not understand,
where the tension fails, and what to change, ranked by impact. Narration, mix and voice stay. Only the picture changes.

**How it was watched**
- The whole film was decoded at 6 fps (640x360).
- 1 fps strips cover 0-700 s: `_work/review/v1/1fps_000.jpg` ... `1fps_690.jpg`, 30 s per sheet.
- 6 fps strips cover the hook (`hook6fps_*.jpg`), all seven rule cards (`card1_6fps.jpg` ... `card7_6fps.jpg`), 26 scares
  (`scare_*.jpg`) and the ending (`end_a/b/c.jpg`).
- 2 s strips cover the memory and loop section, rule 5, the aging and the ending (`r2_*.jpg`).
- 41 stills at 720p are in `_work/review/v1/full/v1_<time>.jpg`, with grids in `full_grid_00..06.jpg`, plus a spot grid (`spot_a.jpg`).
- Reference stills I grabbed are in `_work/ref2/sheets/critic_v1/`, with grids in `_work/ref2/sheets/critic_<ref>.jpg`.
  I also read the teammates' sheets `teacher_dog_480-640s.jpg`, `stadium_480-640s.jpg` and `hazmat720_320-480s.jpg`.
- Each tile label gives the time, the shot id from `film_events.json` and the words spoken at that moment.

---------------------------------------------------------------------------------------------------------------------

## 0. Verdict in six lines

1. **The Queen is not scary, and she is mostly not visible.**
   - She is on screen in 37 shots (74 s). In most of them she is a faint scratch outline in the dark: 149 s, 198 s, 623 s.
   - When she is visible, she is either silly or one repeated mask:
     - silly: a black "barcode" slab with one eye at 202.5 s, and a white teardrop face hanging on a thread at 248.5 s;
     - the mask: the same frontal shark-tooth grin in 6 shots (283.5, 478, 480.6, 531.5, 533, 696.8 s), and its mouth does not move while she talks.
2. **A first-time viewer cannot follow the physics of the story.**
   - The mirror never reads as glass.
   - The crossing through the doorway is never shown as stairs, so "her bare foot on the step below yours" (605 s) has no place to happen.
   - Neither bell is ever shown ringing.
   - The memory world and the other side look the same.
3. **About 25 continuity and staging errors land on story beats.** For example:
   - the Queen "sits down" but stays standing (465-472 s);
   - Noah and the Queen vanish from the bunk at 488-493 s;
   - "you can still feel the candy in your fist" over an open, empty hand (506.5 s);
   - the tape is back on after it "slipped out" (560 s);
   - an empty black shot for "hits his shoulder" (573.4 s);
   - Tess grabs your waist, not your collar (608 s).
4. **The light is wrong for this channel.**
   - 42.8 % of frames have a mean luma under 60 (references: 2-14 %).
   - The other side (213 s, 30 % of the film) is grey: saturation 18 on our scale.
   - The climax has 1.5 % red pixels; the references reach 13-18 %.
5. **The biggest scares are staged as static inserts:**
   - the head turn (198 s) is 60 px tall;
   - the real bell (535 s) is a flat orange cone with no strike;
   - the foot below yours (605 s) is a white sock;
   - the collar yank (608 s) has no yank;
   - the ending never shows the eighth step on the phone.
6. **What works:**
   - the script structure, the narration and the mix;
   - the command tags and red X (the KEEP IT TO YOURSELF X over your mouth at 238 s is the best device in the film);
   - the phone UI;
   - Tess, "you" and Noah13 as designs;
   - the camp gate set;
   - the emotional close-ups of the ending.

---------------------------------------------------------------------------------------------------------------------

## 1. The changes, ranked by impact

| # | change | why (evidence) |
|---|---|---|
| 1 | **Redesign the Queen and restage every appearance as a reveal ladder that comes closer.** Section 5 has the details. | She is the title and the thumbnail. v1 shows her legibly in only about 12 shots, 6 of them the same static grin (`full_grid_03/04/05`, `scare_fullface1/2.jpg`). |
| 2 | **Make the crossing a place: mirror = doorway = staircase.** | Show the red-edged stairs between the two cabins on the way in (290 s) and the way out (586-609 s). Keep the white chipped mirror frame around the doorway on both sides. Without it, the 605 s foot scare, the shoe, "don't turn around" and the collar pull have no geography (`scare_footbelow.jpg`, `scare_collar.jpg`). |
| 3 | **Relight and recolour every world.** | Night becomes blue-violet with warm practicals; the dawn side becomes warm and saturated but still; memories become sepia and paper; the climax becomes magenta-red. Measured: luma by tenth 64 61 53 65 151 144 129 107 69 45; the dawn side is saturation 18; red peaks at 1.48 % in tenth 9 (section 8). |
| 4 | **Fix the continuity and staging errors.** | Section 2: 27 items with timecodes. The top ten each break a story beat the narrator is describing at that moment. |
| 5 | **Draw the mechanisms with diagrams, labels and split screens** (step numbers, sound rings, rewind, the eighth line on the phone). | The bell logic, the time dilation, the loop and the ending payoff are told, not shown. The references draw every rule's logic: the speaker with rings (hazmat 364 s), the SMILE CAM UI (stadium 540 s), the kennel card (vet 71 s). |
| 6 | **Restage the eight big scares** (section 4). | The head turn, full face 1, the Queen sits, the fake and real bells, the foot below yours, the collar yank, the wipe, and the phone face. |
| 7 | **Rebuild the interiors as perspective room kits** with props, signage and a master wide that holds the forbidden object and the exits. | Cabin 7 is dark planks: luma 54, edge density p50 .025 against .038-.044 in the references. The dawn cabin wide never contains the doorway. Several shots are empty: 573.4, 438.5, 511-514 s. |
| 8 | **Make the rule cards story objects** with a physical entrance, and let the Queen get closer from card to card. | All 7 v1 cards are the same grey slab that reads as a whiteboard, not a mirror (`card1..7_6fps.jpg`). The references use a kennel card on bars with eyes behind it, a stitched felt board, a flyer on a corkboard, a jumbotron and a hazard sign. |
| 9 | **Redraw the hand inserts.** | About 25 inserts use the same flat grey-pink glove hand, palm to camera: 31.8, 117, 143, 466-468, 476, 506, 554-562, 570, 587, 645-653 and 689 s. It is the weakest drawing in the film. |
| 10 | **Raise the cut rate** to 36-40 per minute (v1: 27.1 planned, 27.8 detected), using reusable setups, and kill the holds. | Holds to kill: S217 5.1 s (the wrong empty wide), S133 4.3 s, S150 4.1 s. The static stairs shots S081, S071 and S007 have the lowest motion in the film. |
| 11 | **Polish the cast.** | Noah13 scale and pose (307-311 s); grown Noah's glowing yellow fear eyes (580, 593.5 s) read as possessed; the age morph is invisible; Tess's body poses are stiff (608 s); "you" needs a consistent POV sleeve. |
| 12 | **The hook: open on the scariest legible image.** | v1 opens on a grey glove drawing on what reads as a dark wall (1.0 s). The foot at 7.0 s is a sock and the eye at 7.7 s is clip art. |

---------------------------------------------------------------------------------------------------------------------

## 2. Errors (ranked by impact)

Frame refs: the strip name plus the tile time. Shot ids are from `_work/align/film_events.json`.

### 2.1 Story beats where the picture contradicts the narrator

| # | time | shot | the narrator says | v1 shows | evidence | fix |
|---|---|---|---|---|---|---|
| 1 | 464.5-472.0 | S206-S208 | "the woman in the black dress **sits down** on the bunk beside Noah… he scoots over" | She stands beside the bunk as a black column, before and after. The "sit" is a giant pale hand pressing a dark blob (S207). Noah does not scoot. | `scare_sits.jpg` 465.0 / 466.5 / 468.3 | Do one held 2 s shot (the reference "held transformation"): she bends at an inhuman hinge and lowers onto the mattress, the mattress dips, and Noah slides over without looking. |
| 2 | 487.9-493.0 | S217 (5.1 s, the longest non-card shot) | "you understand why a kid might ask to stay here" (you sitting beside him) | You stand alone in the wide. **The bunk is empty: Noah and the Queen have vanished.** The plan asks for "you small on the bunk edge". | `full/v1_0489.0.jpg`, `r2_rule5_446-506.jpg` 488.5-492.5 | Noah stays on the bunk tying the knot and the Queen sits beside him, patting the dip. You sit on the edge or nearly sit (this is the "don't sit down" beat). |
| 3 | 506.5 | S223 | "You can still feel the first one **in your fist**" | An open, empty palm. | `r2_rule5_446-506.jpg` 506.5 | A tight fist with the red wrapper twist poking out between the fingers. Keep the fist in every shot from 323.6 to 649 s (also wrong at 645.5: open before "fingers won't open"). |
| 4 | 651-654 | S296 | "the wrapper left a mark in your palm" | The palm has a red mark but **no candy**. The plan says the candy is in the palm from 649 s. | `r2_ending_630-690.jpg` 651.5, 653.5 | The candy sits in the palm, and the mark is beside it. This is the emotional payoff of "he always gave you the red ones". |
| 5 | 555-562 | S250, S252 | "his taped fingers have slipped right out of the blue tape" | The tape just disappears: no empty tape loop and no slip. In the next insert (560 s, "sweatshirt cuffs") **the tape is back on**. The cuffs never ride up. | `r2_aging_548-588.jpg` 554.7 / 556.0 / 560.0, `full/v1_0559.5.jpg` | The empty blue tape loop stays hanging from a kid-sized finger shape as the hand grows. A separate insert shows the cuffs sliding up the forearm. |
| 6 | 572.1-576.2 | S258-S260 | "He stands and hits his shoulder on a bunk he could walk under a second ago" | S258: grown Noah **sitting** on a bunk in a dark wide. S259 (573.4) is an **empty dark frame** with a sliver of hair. S260: a man standing with his hands out. The hit never happens. | `full/v1_0573.5.jpg`, `r2_aging_548-588.jpg` 573.3-576.0 | He rises, the top bunk rail slams his shoulder, the frame jumps, dust bursts, and there is a camera hit. |
| 7 | 607.3-609.5 | S279 | "Tess takes you by the collar **and pulls**" (the plan: her arm reaches through the doorway and yanks) | Tess stands beside you on the same side, her hand at your waist. You stand still with your back to us. No yank, no flash, no fall. | `scare_collar.jpg`, `full/v1_0608.6.jpg` | Show it from the stairs side: her arm comes out of the dark doorway, the fist closes on the corduroy collar, then a whip pull, a white flash and you hit the floor (rule 7 begins "You hit the floor"). |
| 8 | 511.4-514.4 and 528.8-531.5 | S227, S235 | "a bell rings… the sound from the old camp was perfect" (the plan: the bell swings by itself on the far porch) | A grey window with a tiny dark cabin and a sprinkler. **No bell on screen.** The red X and NO RATTLE land on the window. | `scare_fakebell.jpg`, `scare_smileoff.jpg` 531.0, `full/v1_0513.0.jpg` | A telephoto through the window onto the far porch: a gleaming brass bell swinging, with clean white concentric sound rings. Then the red X over the bell. |
| 9 | 535.3-538.7 | S239-S241 | "Tess hits the real bell with the padlock" | A flat orange cone ECU with a glow (no padlock, no contact). Then Tess stands at the crate with the padlock raised. The strike is never seen. | `scare_realbell.jpg` | Show the padlock swing, the contact spark, a 2-frame white flash, the rim vibrating (drawn wobble lines), the crack rattling and jagged broken sound rings. |
| 10 | 464.5 | S205 | "Her footsteps disappear" (Tess has run to the porch with the flashlight) | The empty doorway **still has the flashlight beam** in it. | `r2_rule5_446-506.jpg` 464.5 | The doorway goes dark: only moon blue and dust. The beam must leave with her. |
| 11 | 545.3-547.4 | S245 | "You shove Noah toward the opening" | You and Noah at the window. **No opening in frame.** The HIM FIRST tag sits over the window. | `card6_6fps.jpg` 545.3-546.5 | The master wide must hold the doorway. Push him toward it (see 2.3). |
| 12 | 589.4-593.9 | S268, S270 | "It's Noah's voice. Thirteen again." | S268: the Queen's soft face with normal lips. S270: **grown Noah** with glowing yellow fear eyes. The viewer does not know whose voice or face is meant. | `scare_shoe.jpg`, `full/v1_0590.0.jpg`, `v1_0593.5.jpg` | Her jaw drops into a tall dark void and Noah13's face glitches inside it while his voice plays (the sibling device, `critic_sibling_stitched.jpg` 268 / 400). |
| 13 | 31.4-32.3 | S018 | "Tess has the keys" (the plan: the key ring swinging) | An open palm in a red sleeve. **No keys.** | `full/v1_0031.8.jpg` | The key ring with the CABIN 7 tag swinging from the carabiner. |
| 14 | 1.0 / 222.5 / 559.5 | S001 / S100 / S252 | "three fingers taped together" | The tape is a single blue box across the back of four fingers (1.0 s), or a ring sitting on top of three fingers (222.5 s). | `full/v1_0001.0.jpg`, `spot_a.jpg` 222.5 | Middle, ring and little fingers wrapped together with tape that wraps around, plus a lifting edge. Keep the same design in every insert. |
| 15 | 689.5-690.8 | S312 | "You touch the bottom one. Your nail clicks against **clean glass**" | A whole open palm over the phone. **The eighth line never appears on the phone.** | `end_b.jpg` 689.5-690.8, `end_a.jpg` | The fingertip slides below the 7 tiny steps onto a clean straight red eighth line just under the glass, then the CLICK with a camera hit. This is the premise paying off and it is missing. |

### 2.2 Continuity and props

| # | time | what |
|---|---|---|
| 16 | 675-698 | Tess picks the phone up (675.5), wipes it in her hand (679-683), and then it **lies on the floor boards** (685-698) without being set down. Pick one: she holds it out to you. |
| 17 | 645.5 / 647.5 / 651.5 | The fist sequence runs open → fist → open. It should be fist (won't open) → slowly opening → palm with the candy. |
| 18 | 562.7 | S253 should be "his face mid-change". He is already fully grown, so no morph is visible anywhere (559.5-567.7). |
| 19 | 285.5-285.8 | Full face 1 rotates in 3/4 at the end of the shot, and the hair turns into a flat card (also at 532.5, S236). It reads as a paper mask turning. |
| 20 | 283.5-285.9 and 478.0-480.6 | **The Queen's mouth does not move while she talks**: the grin is frame-identical through "There's time for both of you" and "I can put you back the way he remembers you" (`scare_fullface1/2.jpg`). Her other lines also need visible speech (S111, S210, S268). |
| 21 | 307-311 | "Noah is sitting on his bed": at 307 his pose is ambiguous (legs out, head at the top-bunk swimsuits, too big for the bunk). At 310.5 **he is standing** in front of it on "he looks up and says your name". |
| 22 | 255.0-255.5 | S116: a white half-disc slides in at the left edge of the towel shot. It reads as a glitch. Check it. |
| 23 | 47.8 | S024: the first bubble is clipped to "heck the pocket." |
| 24 | 86-88 | S041: the watch shows ALM 6:45 under the finger, then a blank display. The change to 4:45 that the line is about is never readable. |
| 25 | 685.0-685.8 | "You count seven little steps": the screen is still black. The steps fade in only at 685.8-686.2. Show them on "count". |
| 26 | 283.5 | Full face 1 is staged in the **dawn cabin** (swimsuits behind her) while you are still on our side, at the doorway. Where is she? She should be in the doorway or in the glass. |
| 27 | 600-606 | You face the Queen and the foot in a "dawn cabin" ECU background (606.0, curtains behind you) although you are on the stairs or at the threshold. |

### 2.3 Sets that look empty or broken

- **573.4 (S259)** is a near-empty dark frame: a purple bunk silhouette and a sliver of hair (`full/v1_0573.5.jpg`).
- **438.5 (S194)** "Breakfast was canceled": a bell on a hook and an urn on a blank grey wall (`r2_memory_386-446.jpg`).
- **335.5-338.7 (S148/S149)** the drop:
  - the towel is a giant wavy orange band across the bottom;
  - the drop is a 10 px grey teardrop on a white wall;
  - "the room reflected upside-down inside it" (the plan) is absent (`full/v1_0337.5.jpg`).
- **The dawn-cabin master wide has no doorway in it.** You cannot see where the doorway is relative to the bunk, the window, the towel and the shoe. Every escape beat suffers: 357, 545, 586 s.
- **The mirror never reads as a mirror.** At 1.0, 3.2 and 117-120 s, the steps float on a dark plank wall with a window and posts behind them (`full/v1_0001.0.jpg`, `v1_0119.6.jpg`). Nothing reflects: not your face, not the beam's hot spot, no frame edge in most CUs.
- **The mirror-world stairs are near-black and static.** S081 at 180.1 s has luma 17 and the lowest motion in the film (median frame difference 0.22). S071 and S007 are similar. The railing, the dawn patch and Noah are barely visible (`full/v1_0009.0.jpg`).
- **Memory = the other side.** The 400.5 s memory ("you woke up in the bottom bunk") is the same grey cabin as the dawn world (`r2_memory_386-446.jpg` 400.5-402.5). Only a 20 %-opacity header says "14 YEARS AGO".

---------------------------------------------------------------------------------------------------------------------

## 3. Comprehension: where a first-time viewer is lost, and the picture that fixes it

Listed in film order. ★ marks the worst.

| time | what the viewer must understand | v1 | picture that makes it obvious |
|---|---|---|---|
| 0-3.6 | seven lipstick steps **on a mirror**; an eighth appears | The steps sit on a dark wall; the eighth line is 2 px and faint even with the 8TH STEP label | A mirror with a chipped white frame, the flashlight hot spot and a faint reflection of the kid's hand. The eighth line draws itself, thick and glowing, then the label pops. |
| 5.3-10.5 | there is a staircase **inside** the mirror, someone is coming up it, and someone you love is down there | Four abstract dark shots: a tiny figure, a sock foot, a clip-art eye, a tiny Noah in fog | A push through the glass (the frame passes the lens) onto the stairs. She is lit, 5 steps down and climbing. Then a scale ladder: WS → her pale foot with real anatomy → her lips. Noah small but lit at the bottom, looking up. |
| 95-104 | the game: call her 3 times; **if she reaches the top step she grants a wish** | A card insert, then dark memories | A diagram on the glass: steps numbered 1-7, a tiny Queen at the bottom with a dotted path to a glowing ⭐ WISH at the top. The same diagram returns at every rule card (2.8). |
| 133-146 | counting smears steps 1-7, and the eighth is **behind** the glass | Works partly (the CLEAN GLASS label at 143.7 is good) | A number 1…7 pops beside each smear as the finger passes. Then 8 sits on the clean line, and a side view shows the line behind the glass plane. |
| 146-150 | when the mirror tilts, the eighth step and **the woman stay level** | The tilt reads, but the woman is a faint 70 px outline (`scare_woman.jpg`) | She must be the brightest thing in the glass: pale skin, red lips catching the beam, a level guide line (dashed) across the tilted frame. |
| 155-172 | the glass shows the cabin **as it used to be** (the other side) | Small and dim inside a thin tilted frame (`spot_a.jpg` 160.5) | Push into the glass until the warm dawn cabin fills the frame, with the frame edge still visible. Then a 2-panel **split: THEIR FLOOR (wet prints, one shoe print then bare) / OUR FLOOR (smooth dust)** at 172-176 s. |
| ★181-184 | a boy's voice from **below her** | S081 is a near-black stairs shot (luma 17) with no boy | Tiny Noah in the dawn patch far below, face up, the gap visible, with a speech glow. Then the voicemail UI (good already) matches the face to the voice. |
| ★197-203 | she **turns her head** and is now listening to **you** | Her figure is 60 px tall and the turn is invisible (`scare_headturn.jpg`). Then a black barcode slab with one eye. | A ladder: MS back of her head → CU the head rotates past 130° with the hair sweeping → ECU one eye locks on the lens → **a dashed red line from her eye to your eye** (the vet device). |
| 211-226 | the hand through the railing is **Noah's** (the tape) | A glove-like hand on dark bars (222.5) | OTS through the glass: the railing behind her, a small hand with the CEDAR LAKE green cuff and the three taped fingers, plus a BLUE MEDICAL TAPE label. |
| 248 | **she** answers your wish | A teardrop face on a thread (`full/v1_0248.5.jpg`) | Her face in the glass behind your reflection's shoulder, lips moving: "You have it." |
| 256-262 | the mirror **is** now a doorway | The towel drops and a doorway appears. Works. | Keep, but leave the mirror's white frame around the doorway so it is visibly the mirror. |
| ★279-290 | the clock jerks back; she invites you; you step **through** | The clock is good. The face is in the wrong world. The step-through cuts straight to a window (290.6). | She speaks from the doorway (her face in the light, half in our cabin). Step-through ladder: your foot on the first red-edged step → a short descent shot (you on the stairs, our cabin small above, the dawn light below) → you emerge into the dawn cabin. **This builds the space that 586-609 s needs.** |
| 297-350 | the other side is **frozen at 6:59**; time runs slower there | The header clock (20 % opacity) and a grey wall clock; the drop is unreadable | A big clock insert at 6:59:40 → :59 → snaps back to :40 with a rewind glitch. The 49 / 48 counter. A split screen at 341-347: **OUR SIDE: Tess, beam frozen, dust hanging / THEIR SIDE: the same drop falling again**. |
| 315-318 | "Why do you look like Dad?" | CUs only | Noah's eyes go to your face, then a 0.5 s insert of a Dad photo or memory with the same jaw and stubble. |
| 357-360 | Noah cannot pass the doorway; he resets to the bunk | Works (the hands jerk, your shock, him back on the bunk) | Add the SAME KNOT label and the rewind glitch on the reset. |
| ★389-446 | the loop; the morning he went missing; why no bell rang | A memory section that looks like the dawn cabin. The fake loop (sprinkler, question) is told, not felt. | Memories in sepia with paper texture, a rounded film gate and a 14 YEARS AGO stamp (the vet flashback look). The loop repeats get a VHS rewind wipe and a counter ("LOOP 1,000,000+" or a tally of the knot). |
| 446-465 | Tess runs for the **real** bell across the path | Works (porch, path, "Go") | Keep. Add a map inset: CABIN 7 → path → MESS HALL porch with Tess's dot. |
| ★511-538 | the fake bell is perfect; the real bell has a crack and a rattle | Neither bell is seen ringing | A split screen: **THEIR BELL: clean rings ✗ / OUR BELL: crack + rattle squiggle ✓**, using the same sound-ring device both times (sibling 7:06 / hazmat 364 s speaker rings). Plant the device in the 65.9 s memory. |
| 545-560 | "let him go first": his foot gets through and stays; Tess pulls him into our side | The foot through reads (547-549). The other side of the doorway is a blank pink wall (550). | The doorway shot from our side: his bare foot appears out of the stairs dark onto our floorboards, and Tess's hands grab his wrist. |
| ★586-609 | you are **on the stairs** in the doorway; behind you she uses Noah's voice; you turn; her foot is on the step below yours; Tess yanks you out | Your flat black silhouette, a soft woman's face, grown Noah's yellow eyes, a sock foot, a waist grab | See 4.1: a POV down the stairs, then her full-face void, then the yank through the frame. |
| 619-628 | you wipe top-down; she lifts her foot toward an erased step; the glass goes dark | A towel blob; she is invisible in red murk (621.8-625.3) | The full mirror, steps 1-7 erased one by one (numbers ticking off), her pale figure on step 8 lit by the red light, her foot rising toward step 7, now a smear. Hold, then black. |
| ★677-698 | the phone was **face up the whole time**: a mirror nobody covered, so she is in it | FACE UP + red X is good. No eighth line, no reflection, the same mask. | The dark phone glass reflects Tess's face (it is a mirror). Seven tiny steps. Your fingertip, then **the eighth line**, then the click. Then her tiny figure on it, looking up. On "Can I have one more minute?" Noah13's face appears in the screen and pixel-sort glitches into her face. Hard cut. |

**Who is speaking.**
- The Queen's lines (248, 283, 474, 478, 582, 589, 697 s) need visible lip motion and a consistent voice sign:
  - a thin red glow on the mouth;
  - for the Noah-voice lines, Noah13's face flickering in her mouth or on the screen.
- Tess's off-screen calls already work: CU + badge at 350.2, 502.5 and 585.3 s.

---------------------------------------------------------------------------------------------------------------------

## 4. Tension: where it sags and where scares don't land

### 4.1 The eight scares to restage (most important first)

1. **605.2 the foot below yours** (planned as the biggest hit; `scare_footbelow.jpg`).
   - v1 does two things wrong:
     - A white sock-like foot sits under a pair of brown boot blocks. It is held for 1.5 s and repeated at 606.8.
     - The cutaway to your face uses the wrong background.
   - Restage:
     - POV down at your own boots on a red-edged tread in the dark.
     - A slow tilt reveals, on the next tread down, a pale grey foot with long toes, dark nail tips and a hem of black satin.
     - Hold 0.8 s, then tilt up the dress to her face.
     - Her face is 30 cm away and just starting to smile. Her hand is rising toward your shoulder.
     - Cut on Tess's arm.
2. **283.5 full face 1.**
   - v1: the face sits in the wrong world. It is frontal and static with the mouth frozen. It has already been seen in the hook style (`scare_fullface1.jpg`).
   - Restage:
     - She leans out of the doorway light: first only the red mouth, then the face, then her hand on the frame.
     - The new design ladder (section 5) applies.
     - Hold 2.5 s with the grin widening as she speaks.
3. **535.4 the real bell.** v1 has no strike and no flash. Restage it as described in 2.1 #9, then cut to the dawn cabin flickering with Noah dropping his lace.
4. **197.7 the head turn.** v1 is invisible. Restage it with the ladder in section 3.
5. **465-468 she sits.** v1 has no sit. Restage it with the held shot in 2.1 #1; Noah scooting is the horror.
6. **608 the collar yank.** v1 has no yank. Restage it as in 2.1 #7.
7. **622-628 the foot hangs.** v1 shows a pink sock and an invisible woman. Light her. The hanging foot is a held shot with the red light pulsing; then the glass goes dark from the edges in.
8. **697 the phone face.** v1 uses the same mask a third time. Use Noah's face glitching into hers, a design step not seen before (the jaw void or the lipstick smile running off her face), then a hard cut.

### 4.2 Where it sags

- **19-130 s, the setup (18.6 % of the film before rule 1):**
  - it is dark: ours luma 54, camp_path 41;
  - the light is flat, with nothing warm to contrast;
  - long CU holds (S026 3.7 s on your phone glow, the most static ours shot).
  - The narration cannot change, so the picture must carry it:
    - bright warm memories (the dock, the sprinkler, the bell drop) at full colour;
    - a warm caretaker window;
    - the Queen planted small in the background of a few shots (a figure in the mess hall window, a pale shape on the dock).
  - The references put threat in the background early (sibling 0:13, a tiny figure down the street).
- **290-350 s, the arrival on the other side:** a grey, washed-out cabin (luma 148, saturation 18) with static inserts:
  - S133 window and lantern, 4.3 s;
  - S138 Noah, 3.8 s;
  - S150 Tess in the doorway, 4.1 s.

  This should be the most beautiful, warm, golden place in the film, made wrong by stillness: curtains frozen mid-sway, dust motes hanging, the drop. The grey reads as unfinished, not uncanny.
- **386-446 s, the loop and the memories:** about 20 CUs of Noah and you on the same grey wall (`r2_memory_386-446.jpg`). Fix it with the memory look, inserts per noun (kitchen staff, buses, gate), and the Queen in the background of the dawn CUs, sitting a little closer each time.
- **628-690 s, the ending:** dark blue wides of three still figures, with the lowest motion in the film: S289 4.0 s, S291, S293, S304, S305. The reunion CUs are good, so keep them. Add warmth from the flashlight pool, then cool down for the phone.

### 4.3 Proximity: the Queen should come closer all film

v1 keeps her at the same distance: standing still on the eighth step, or the same bust. Use the premise ("Don't wait to see who's coming up the stairs") as the threat meter:
- every time we see the glass she is **one step higher**: rule 1 on step 8, rule 2 at step 6, the wish at step 3;
- on the other side, she is in the background of every dawn shot after 389 s: first standing far, then on the bunk, then behind you at the doorway;
- in the rule cards, her reflection behind the card gets closer each time (2.8);
- in OTS shots, put her in soft focus over your or Noah's shoulder; the references use the threat in the background constantly.

---------------------------------------------------------------------------------------------------------------------

## 5. The Queen of Spades: what is weak, what is scary, and a redesign

### 5.1 Weak or silly in v1

| beat | v1 | why it fails |
|---|---|---|
| silhouette on the step (148-152, 197-201, 621-627) | A thin pale scratch outline on near-black, about 70-230 px tall. Two white mitten-blocks for hands (150.8-152.2). | You cannot see her. The no-outline language makes her look unfinished, not otherworldly. The mittens read as a toy. |
| feet (7.0, 149.7, 605.5, 625.5) | A white tube leg and a sock-shaped foot with five toe ovals | It reads as a cast or a sock. It has no anatomy, tone or nails. |
| eye (7.7) | A red disc with radial lines and straight eyelashes on a grey almond | Clip-art icon |
| one eye through the hair (202.5) | A black rectangle with white vertical lines (hair), and a white wedge with a red dot | It reads as a barcode or curtain, with a Pac-Man shape |
| "You have it" (248.5) | A white teardrop face hanging on a white thread, with red lips | An ornament or spider. The single silliest image in the film. |
| full face (283.5, 478, 531-533, 696.8) | The same frontal symmetric pale mask: round eyes about 0.3 of face width each with grey veins, a small red iris, a 0.8-width grin of triangular shark teeth, black hair planks | It reads as a generic creepypasta mask (a Jeff-the-killer / Momo cousin), not a person and not a queen. Shown 6 times, never changing, mouth frozen during speech. |
| soft and calling (583, 590) | A sleepy woman with eye bags and a small red mouth; the call is a black open O | At the moment Noah's voice comes out of her (the twist), she looks tired, not wrong |
| identity | No crown, no spade, no card motif, no lipstick in hand | Nothing says "Queen of Spades" except the narration |

### 5.2 What the references do (all from frames I read)

- **Stadium** (`critic_stadium.jpg` 540, 562, 566, 570, 622) starts from **a normal person drawn in the cast's style**, then adds wrongness:
  - pink bloodshot sclera with red veins, but **normal-size brown irises**;
  - **deep cheek folds and crow's feet**, and tears;
  - a grin of **flat white human teeth with pink gums**;
  - at the climax, a jaw "cracking" open into a tall mouth.
  It is scary because it is a real face doing something wrong.
- **Teacher**:
  - a pretty, normal teacher whose lips "crack open" at the corners (604 s);
  - on the basement stairs, **a tall black figure with a red open mouth stands at the top step** (500 s).
  That stairs image is exactly our premise, and it reads in one glance.
- **Vet**: red glowing irises with **red blood tears** and a grin of flat teeth, worn on a recognisable uniform (purple paw cap, VET badge) on a bokeh plate (47 s).
- **Hazmat**: no face at all, but one **identifier** (a scratch across the left red lens) repeated in ECU (336 s).
- **Sibling**:
  - the **jaw that hangs unnaturally low** into a glossy dark void (268, 400 s) while the loved one's voice comes out;
  - bloodshot eyes and a too-wide smile on the possessed dad, on a purple bokeh plate (502 s).
- **Shared**:
  - the face is the brightest thing on the plate;
  - one new wrong feature per shot;
  - the full face is reserved for a few beats;
  - the villain looks into the lens.

### 5.3 Redesign (keep the motif, change the drawing)

**Keep**
- the lipstick red `#c63449` as her only colour, shared with the steps;
- the high-collared black satin dress;
- the very long black hair from a centre parting;
- bare feet, uncanny stillness and snap acting;
- the wide red glow;
- living in reflections;
- the last image in the phone.

**Change**
1. **Draw her in the cast's language.** She gets a dark outline like everyone else. The pale scratch lines become a subtle second rim that shimmers only in the glass. She must be **visible**: her skin is the brightest value in any frame she is in, lit by Tess's beam or her own red glow.
2. **Face, stage 1: beautiful and calm.**
   - porcelain grey-white skin with a soft cool shade;
   - human almond eyes about 0.16 of face width, with dark irises and two speculars;
   - long lashes and arched brows;
   - perfect red lipstick.
   The wrongness is behaviour: no blink, the head turned 130°, the hair not moving with the head.
3. **Stage 2: the lipstick has been drawn past her mouth.** Her smile line continues across the cheeks as a **zigzag lipstick staircase**: the same waxy stroke and crumbs as the steps on the glass. She drew herself a wider smile with the same stick. This is our own motif and nobody else has it.
4. **Stage 3: the full face.**
   - pupils to pinpoints;
   - the iris turns red with a bloom halo;
   - pink veined sclera;
   - the lipstick staircase smile opens into a grin 0.6-0.7 of face width of **flat human teeth**, two rows with pink gums and no fangs;
   - cheek folds and fine crack lines like old porcelain;
   - black mascara tears.
   Each appearance adds one feature: 283 s pinpoints and the smile line, 478 s teeth and folds, 533 s smile off to a blank stare.
5. **Stage 4, the shoe line (589.4 s): the jaw drops into a tall glossy dark-red void.** Noah13's face flickers inside it as his voice comes out. This is the sibling device, and it makes "who is speaking" obvious.
6. **Queen of Spades iconography, readable at thumbnail size:**
   - a small black crown or tiara of spade shapes tangled in the hair;
   - a black-and-silver spade brooch at the high collar;
   - a faint playing-card pip pattern (♠) embroidered at the cuffs and hem, catching the sheen;
   - optionally one card-like mirror symmetry beat: her reflection in the tilted glass is flipped like a court card, top half and bottom half.
7. **Hands and feet.**
   - Hands: long jointed fingers with black lacquered nails. **Her fingertips are red with lipstick**: she drew the eighth step.
   - Feet: anatomical, ash-grey with blue shadows, long toes, dark nail tips, a tendon line, and a satin hem brushing them.
8. **Hair** as strands: a sheen gradient, a parting highlight and 2-3 loose strands across the face. It hangs perfectly still while everything else moves (wind chimes, dust, the beam).
9. **Staging rules.**
   - She enters every scene small and far.
   - She comes one step closer each time.
   - She is always lit.
   - She gets the widest glow in the film.
   - She looks into the lens 2-3 times (the head turn, the doorway, the phone).
   - She is never shown frontal and symmetric in two consecutive beats.

---------------------------------------------------------------------------------------------------------------------

## 6. Cast and sets: keep and upgrade

### Cast
- **You. Keep the design:** olive jacket with a corduroy collar, stubble and the Dad jaw. Your fear eyes (359, 606 s) and tears (643, 661 s) read well.
  - Upgrade: a consistent olive sleeve on every POV hand, and the back of your head in OTS shots (the references' "you" avatar).
  - Upgrade: the left-hand candy fist as a running visual.
  - Upgrade: real acting poses in wides; at 489 and 608 s you are a standing cutout.
- **Tess. Keep:** the burnt-orange shell (the only warm accent on our side), the auburn ponytail, freckles and the beam with dust.
  - Upgrade: body poses. At 608.6 her arm is a straight horizontal stick.
  - Upgrade: her running shot needs motion (446-465 s).
- **Noah13. Keep:** the green CEDAR LAKE sweatshirt, gap teeth, one shoe, the blue tape, the knot loop and the "Finally" smile (541.8 s).
  - Upgrade: almond eyes with highlights in his CUs; the current dot eyes read blank (`r2_memory_386-446.jpg` 394.5).
  - Upgrade: correct seated scale on the bunk (307-311 s).
  - Upgrade: the gap teeth visible on every line.
- **Noah grown. Keep:** the "Hi, Mom" CU with tears (661.5 s, the best emotional frame in the film) and the sweatshirt two sizes too small.
  - Fix: the **yellow glowing fear irises** (580, 593.5 s) read as possessed. Use brown, like Noah13 and like you.
  - Fix: make the age morph visible (one held 2 s CU, 562-565 s).
  - Fix: his seated scale in the ending wides looks child-sized next to Tess (629.5, 667.5 s).
- **Hands:** replace the glove-hand template. Use foreshortened, outlined hands with knuckle and nail detail, a sleeve and wrist, holding props, at varied angles (references: vet 9:38 collar hand, hazmat 5:42 grab, teacher 8:04).
- **Extras:** the black silhouette searchers and staff (404, 434, 436 s) are fine as memory shorthand, but give them sepia colour and flashlights.

### Sets
- **Keep:**
  - the **camp gate** (arch sign, MISSING poster, NOTICE, chained gate, pines and moon; 20.5 s), the most finished set;
  - the dawn cabin's props (gingham curtains, swimsuits on the rail, lantern, wall clock, towel, shoe);
  - the mess hall porch with the crate;
  - the doorway with the splintered edge and the light spill (260.5 s);
  - the phone UI.
- **Upgrade Cabin 7 (ours).** Build a perspective room kit with:
  - a ceiling and rafters;
  - the door, the window with a torn screen and moon shafts, and the sill with the phone;
  - cubbies with name tapes (NOAH), Noah's bunk with initials carved in it, a CABIN RULES sign, and the old search tape;
  - the clock;
  - the mirror spot always in the same place in the wide (the vet keeps the blanket cage at the vanishing point).

  Lift it to luma p50 70-100 in blue-violet with a warm saturated beam pool. Add a high-wide establishing shot.
- **Upgrade the mirror.** A visible frame, a silvering texture, reflections of the beam and of the faces, and depth for the eighth line (parallax).
- **Upgrade the stairs.** Build a readable staircase:
  - red-edged treads;
  - a balustrade;
  - depth fog;
  - the dawn patch at the bottom;
  - the doorway rectangle at the top showing Cabin 7.

  Use it on the way in, on the way out, and for the foot scare.
- **Upgrade the dawn cabin (theirs).** A perspective kit:
  - warm sunrise light at saturation 60-85;
  - a sky gradient through the window;
  - frozen dust motes and curtains caught mid-sway;
  - the doorway visible in the master wide;
  - the far mess hall with its bell visible through the window (for 511-531 s).
- **Upgrade the memory look.** Sepia, paper grain, a rounded vignette and a 14 YEARS AGO stamp. Do not reuse the dawn cabin's grade.
- **Fix the empty shots.** S259 (573.4), S194 (438.5) and S227 / S235 (the bell window).
- **Lighting arc.** Warm memories and coloured night early; the darkest, reddest tenth at 70-80 % (530-600 s: magenta-red light leaking from the doorway into Cabin 7, 13-18 % red pixels); a softer final tenth before the phone's red.

---------------------------------------------------------------------------------------------------------------------

## 7. What works and must be kept

- **Story structure, narration, captions, header and mix.** The narrator's cliffhanger before each card (for example "...in the same sweatshirt he disappeared in. Rule number one") already matches the references.
- **Command tags and red X used as meaning:**
  - KEEP IT TO YOURSELF with the X over your mouth (238.3 s, `scare_wish.jpg`);
  - DON'T SIT DOWN with the X over the dip (494.5 s);
  - FACE UP with the X over the phone (677.5 s);
  - the CLEAN GLASS label (143.7 s);
  - the 8TH STEP label;
  - STAY (287.3 s).
- **Phone UI:** the MOM thread (47.8 s), the NOAH voicemail with its waveform (191 s), and the call screen with timer and chair-scrape waveform (655-666 s). They are clean, readable and in the references' style.
- **The time card** at 20.5 s (FRIDAY 11:57 PM, CAMP CEDAR LAKE · DEMOLITION TOMORROW).
- **The TESS countdown badge** and its red pops on 45 / 20 / 5 / 0. Keep it, but make it a bigger ring timer.
- **Rule card mechanics:**
  - in about 0.45 s before "Rule", with the 2-frame glitch;
  - the lipstick title;
  - word-synced text with red keywords;
  - LIKE / SUBSCRIBE on cards 1-2.

  Only the object and its choreography change.
- **Good beats to keep as they are, or nearly:**
  - the hand-jerk reset (358-360 s);
  - the bugs-at-the-window memory (236.7 s);
  - Tess's "Forty-five!" / "Twenty!" CUs;
  - Noah's "Finally" (541.8 s);
  - the bare foot crossing the threshold (547-549 s);
  - the ending reunion CUs (661-665 s);
  - the clock jerking backward (279-282.3 s).
- **Discipline:** red stays out of the first 70 % (red share ≤ 0.27 % per tenth through 490 s), and identical replays for the loop.

---------------------------------------------------------------------------------------------------------------------

## 8. Measured numbers (v1, 6 fps decode, caption band excluded)

| measure | v1 | references (REF_V2_B and my grabs) |
|---|---|---|
| frames with mean luma < 60 / < 40 | **42.8 % / 14.5 %** | sibling 2 / 0 %, vet 14 / 6 % |
| luma by tenth | 64 61 53 65 151 144 129 107 69 45 | sibling 122 … 97 (bright first), vet 121 … 61 at 70-80 % … 141 |
| saturation (mean (max-min)/max × 255) by tenth | 106 85 91 77 **27 20** 35 53 86 103 | – (the dark-frame saturation is inflated by the metric; the dawn figure is the real problem) |
| red-pixel share by tenth (%) | .19 .26 .27 .23 0 .05 .05 .66 **1.48** .08 | 13.7-18.3 % in the peak tenth |
| luma / saturation per set family | cabin_dawn 213 s: 148 / **18**; cabin_now 201 s: 54 / 95; memory 88 s: 109 / 46; mirror 62 s: 41; mirror_world 29 s: **34**; camp_path: 41 | night exterior p50 95, home by flashlight 114, normal rooms 141-166 |
| shots / cuts per min / median / p90 / > 4 s | 317 / 27.1 (plan; 27.8 detected on the file) / 2.14 s / 3.36 s / 8 (S280 5.2, **S217 5.1**, S093 4.8, S133 4.3, S294 4.2, S122 4.1, S150 4.1, S289 4.0) | 38.8-40.4 per minute, median 1.4-1.5 s, nothing over 4.8 s |
| lowest-motion shots (median frame difference, levels per 1/6 s) | S081 0.22 (stairs), S146 0.24, S071 0.24 (stairs), S109 0.25, S019 0.27, S007 0.28 (stairs), S026 0.28 | – |
| Queen | 37 shots / 74 s planned; about 12 shots have a readable face; the same grin in 6 | stadium and sibling show a changed face every beat |

---------------------------------------------------------------------------------------------------------------------

## 9. Files

- Strips (all `_work/review/v1/`):
  - 1 fps: `1fps_000.jpg` … `1fps_690.jpg` (24 sheets);
  - hook: `hook6fps_000.0/005.0/010.0/015.0.jpg`;
  - cards: `card1_6fps.jpg` … `card7_6fps.jpg`;
  - scares: `scare_{eighthline,nailclick_tilt,woman,headturn,eye,wish,youhaveit,towel,clockback,fullface1,stepthrough,drop,handjerk,faceflash,sits,fullface2,fakebell,smileoff,realbell,footthrough,shoe,footbelow,collar,wipe,foothangs}.jpg`;
  - ending: `end_a/b/c.jpg`;
  - 2 s strips: `r2_memory_386-446.jpg`, `r2_rule5_446-506.jpg`, `r2_aging_548-588.jpg`, `r2_ending_630-690.jpg`;
  - 720p stills: `full/v1_<time>.jpg` and `full_grid_00..06.jpg`;
  - `spot_a.jpg`.
- Reference grabs: `_work/ref2/sheets/critic_v1/<ref>_<sec>.jpg` and the grids `_work/ref2/sheets/critic_{hazmat720,teacher_dog,stadium,sibling_stitched,vet_dog}.jpg`.
- The decoded 6 fps frames were working data and have been deleted.
