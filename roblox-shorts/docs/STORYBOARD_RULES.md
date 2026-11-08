# STORYBOARD RULES: turning a voice-over into shots

How to cut a recorded voice-over into a shot list in the style of the four reference shorts. It covers when to cut, what each shot
shows, how the camera moves, and how to check the result. The look of each shot (characters, sets, light, grade, post) is in
`docs/VISUAL_BIBLE.md`; this file is about the edit.

Reference codes: **TF** Tooth Fairies (the master), **AW** Awake At Night, **PN** Porch Night, **CG** Clown Gate. Times like "TF 3.75" are
seconds in the full 60 fps copies (`.../scratchpad/rbx/ref60/*.mp4`); shot numbers like "TF #19" refer to the shot tables in
`analysis/visual_*.md`. Word times for the references are in `.../scratchpad/rbx/{tfv/asr_tf.json, work/vis_awake/asr.json, pnv/asr_pn.json, cgv/asr_cg.json}`.

---

## 0. Inputs and output

**Inputs**
- The voice-over WAV. EP01: `audio_39.wav`, 113.14 s, first audible sample 0.13 s, last 112.95 s.
- Word times from ASR. EP01: `/tmp/claude-0/-home-user-claude-todo-demo/353ac1d9-152b-55bb-bdf1-0625e0fc6a83/scratchpad/rbx/ep01/voice_asr.json`
  (440 words, onsets 0.16-112.69 s, 61 sentences, quantised to 80 ms, so treat each time as ±40 ms).
- The script with picture notes. EP01: `scripts/EP01_FINAL.md` (cast, sets, plants, SFX points per line).

**Output.** An engine timeline (`engine/README.md`, "Timeline JSON"): one entry per shot with `name`, `shot` (builder key), `start`, `end`
and `params`. Put the storyboard decisions in `params` so the builders never have to re-read this file:

```json
{ "name": "s018", "shot": "gnome_blink_cu", "start": 20.21, "end": 21.01,
  "params": { "words": "and he blinks.", "size": "CU", "angle": "low", "fov": 70,
              "move": { "type": "push", "Z": 0.20 }, "grade": "night", "face": null,
              "events": [ { "t": 20.55, "what": "blink2f", "sfx": "tik" } ] } }
```

`start`/`end` are episode seconds; the engine snaps them to whole frames (`round(t*60)`). `events[].t` is the episode time of the word
that triggers the event.

---

## 1. Targets

| Measure | TF | AW | PN | CG | **Our target (EP01)** |
|---|---|---|---|---|---|
| Cuts per minute | 52.0 | 34.8 | 42.1 | 48.4 | **45-52** (hook and climax may run to 55-60) |
| Words per shot | 5.0 | 6.9 | 6.3 | 5.1 | **about 5** → 88-95 shots for EP01's 440 words |
| Median / mean shot | 1.10 / 1.14 s | 1.52 / 1.71 | 1.35 / 1.41 | 1.17 / 1.23 | **1.15-1.25 s** (our VO is 235 wpm, TF 261) |
| p10 / p90 / max | 0.50 / 1.96 / 2.28 s | 0.95 / 2.69 / 5.2 | 0.84 / 2.05 / 2.43 | 0.63 / 1.78 / 3.03 | **0.5 / ≤2.0 / ≤2.3 s** (one reveal ≤2.5 s) |
| Sentences opening on a cut | 95% | 64% | 72% | 93% | **≥ 95%** |
| Cut minus naming-word onset, median | -7 ms | -40 ms | -77 ms | -23 ms | **-17 ms (1 frame early)**, window -100 to +33 ms |
| Shots with camera motion | 100% | 100% | 98% | 100% | **100%** |
| Close shots (ECU/CU/MCU/INS) | 51% | 27% | 23% | 48% | **45-50%** |
| Transitions | hard cuts | hard cuts | hard cuts | hard + 19 editor | **hard cuts only** |

---

## 2. The cutting rules, in the order you apply them

**R1. Every sentence starts on a new shot.** Cut on the first word of every sentence (TF: 60 of 63). The only exception is a sentence of
1-2 words that finishes the previous thought ("Gone." can share the shot that shows the result).

**R2. One picture per concrete noun, number or list item.** When the narration names a new thing, the picture changes to that thing.
- TF: "castle" cut 3.75 / word 3.84; "a star / A tower / a little door" 30.87 / 31.40 / 31.97 (same top-down set-up, the card swapped:
  jump cuts); "No more coins. No more drawings. No more Fern." 66.50 / 67.32 / 68.18; the card list "A star. A tower, a little door,
  a window, a family waving." 87.42 / 88.00 / 88.50 / 89.15 / 89.65; "Past the mountain, past the moon, at the stars" 55.97 / 56.62 / 57.10.
- CG: "Eight feet / nine / ten / twelve / twenty" one plate insert each (shots #83-#88, 0.45-0.63 s), "6 feet / 5'11 / 5'10" one notch insert each.
- AW: "So at midnight" → the 12:00 clock insert (54.75); "The walls" → walls of shelves (101.75).
- PN: "Mrs Pell / the Fisher boy / Danny" one porch each (#71-#73).
- A noun that is already the subject of the running shot does not need a new shot.

**R3. Cut one frame before the word that names the new picture.** `cut = onset - 1/60`, snapped to the frame. Never later than +2
frames (the picture must never lag the word) and never earlier than -6 frames. For a list phrase whose noun comes within 0.3 s of the
phrase start ("to the flowers"), cut on the phrase start, so the picture is up just before the noun (TF "A tower": cut 31.40, "tower" 31.54).

**R4. Split long sentences at commas and clauses.** A sentence longer than about 1.8 s or 8 words gets 2-4 shots, split at its commas,
or at each concrete noun. PN #5-#9: "It comes out of the cornfields at midnight, / a scarecrow, taller than the streetlights, / straw
hanging out of its sleeves, / and a sack for a head, / with a big smile stitched across it." TF #92-#95: "and flew it out the window, /
over the houses, / over the trees, / all the way to the top of the mountain." (105.32 / 106.47 / 107.13 / 107.92).

**R5. Short lines get reaction shots.** A line of 1-3 words, or a beat that lands on a character, gets a 0.35-0.6 s close-up of the
reacting face with a new decal. TF #42 "I froze." (50.32, 0.55 s), #45 "Home?" (54.08, 0.38 s), #30 "20." (36.72, 0.55 s), #85
"waiting." (96.65, 0.38 s); PN #35 "One for the porch?" (0.58 s).

**R6. Length limits.** Minimum 0.4 s (list items 0.45 s, reaction shots 0.35 s; TF's 0.17 s insert at 78.60 was an accident).
Maximum 2.3 s: split a longer stretch with a noun insert or a reaction shot, or carry it with a big camera move (TF's longest shots,
2.2-2.3 s, all have a strong push or a slide-together). AW's 3.5-5.2 s holds are reserved for the monster and lair reveals; we do not
use them.

**R7. In-shot events land on the word.** Decal swaps, light switches, pops, bursts and blinks happen on the onset of the word that
describes them, not on the cut. TF: grin → open smile 22.40 ("baby" 22.32); tooth clicks into the wall 109.62 ("Click" 109.57); castle
lights up on the cut 111.20 ("lit" 111.49). AW: eyes snap open 37.80 ("Tink" 37.79); box lights on 153.00 ("started"). PN: lamps go
out one by one 110.87-112.73 under "went out, one by one"; the window bursts 137.0 ("smashed" 137.43).

**R8. Pauses do not create cuts.** A pause in the voice is held by the running shot and its push (TF has no voice gap over 0.64 s).
The exception is a planned **silence beat**: a short atmosphere or creature shot that fills a deliberate pause (CG #18 dust puff
23.33-24.03, CG #95 back of the clown's head 115.85-116.48). EP01 has 4 planned pauses (after "empty", "fence", "flowerbed", before
"Every spring"): hold the running shot through each, or give the pause one silence-beat shot.

**R9. Every shot moves.** Default: a linear centred push of +10-30% (median +19%), no easing (`VISUAL_BIBLE.md` §7). About 1 shot in 6
gets an accent move chosen from the narration (§4 below). The first shot is always an accent.

**R10. Location, time of day and grade change only on a sentence start**, and a new location or time of day opens with an
establishing shot (WS/EWS, 0.5-2.2 s): TF #28 house exterior on "Then last night" (34.17), AW #30 the yellow house in daylight on
"In the morning" (45.50), AW #54 factory facade (88.05), TF #8 castle on its mountain (9.07). A light-state change that is itself
the story ("lit up", "went dark") may happen inside a shot or as a same-framing jump cut (TF #98 → #99).

---

## 3. Shot types: when to use them

| Type | Use it for | Size / angle / move | Reference examples |
|---|---|---|---|
| **Opener** | Frame 0, already mid-motion; the creature or the rule's image on screen within 2.5-4 s | ECU → MS snap pull-back x3-x10 (`outExpo`), or a whip | TF #1 (0.00-1.27, pull-back x10 from a fairy hugging a tooth); CG #1 (x3.4 pull-back on a man jumping, clown at 2.25); AW #1 (spin-zoom on the monster walking) |
| **Establishing** | New location or time of day | WS/EWS, slow push or tilt | TF #8 (9.07), #28 (34.17); AW #5 empty street EWS (4.38), #30 (45.50) |
| **Character intro** | The first time a creature or character is named | Low CU on the name, push +30% or punch-in x1.5-2 with +10-13° roll | TF #19 "Her name was Fern" (25.17, low CU, +32%); TF #38-#40 the queen (44.17-48.03, low, +53%); AW #8 "We call it Lullaby" (9.65, x2.0 + 13° roll) |
| **Insert** | Every named object, number, sign or text | CU/ECU/INS, objects top-down, normal lens 40-50°, push +20-30% | TF #21 coin (27.57), #32 clock at midnight (38.75); AW #36 LED clock (54.75); CG plates and notches |
| **List jump cuts** | A spoken list of 3+ items | The same set-up repeated, only the object changes, 0.45-0.65 s each | TF #24-#26 (30.87-32.62), #77-#81 (87.42-90.57); CG #83-#88 |
| **Reaction** | Short lines, emotional turns | CU of the face with a new decal, 0.35-0.6 s, small push | TF #42 (50.32), #45 (54.08), #36 (42.57) |
| **Dialogue** | A quoted line | The speaker in low MCU/CU with a body sway (creatures) or a speaking face; alternate with the listener's reaction | TF #41-#44 the queen's lines (48.03-54.08) with the kid's reactions #42, #45 |
| **Reveal** | Quantity, size, "and there it was" | Crane-up pull-back x3-x11 for quantity; punch-in x1.6-2.0 for an approach; tilt up a tall subject | TF #34 "It was a hundred fairies" (40.77, pull-back x11); AW #81 "came around the corner" (141.40, x2.0); AW #41 "ten feet tall" (tilt up) |
| **Action / flight** | Movement through space | One shot per phrase of the action; follow, fast truck, crane; screen direction kept constant | TF #92-#95 (105.32-109.62); TF #2 crane up into space (1.27) |
| **Callback** | A line that repeats an earlier line or idea | The exact earlier set-up (same framing, same order) | PN lock insert #57 = #118; TF bedroom high 3/4 set-ups; AW Max's bed #16 = #20 = #26 |
| **Mirror pair** | "Every / the same / exactly like" | Two shots with identical framing and roll, different people | AW #13 / #14 "every parent ... the exact same lullaby" (16.80 / 18.27) |
| **Quiet wide** | After a climax, before the coda | WS, small subject, slow push, 1.3-2.2 s | TF #105 POV "until it was just one tiny light" (119.07); TF #114 last wide |
| **Silence beat** | A planned pause | A creature or atmosphere shot, 0.6-0.7 s | CG #18 (23.33), #95 (115.85) |
| **Ending** | The last line | A normal shot, ending 0.3-0.4 s after the voice; match frame 0 if the story loops | TF #114 (130.42-131.53); EP01 frame 1 = last frame |

---

## 4. Choosing the camera move from the words

The default is the +19% linear push. Promote a shot to an accent move when its words call for one:

| The narration says | Accent move | Reference |
|---|---|---|
| a quantity: "a hundred", "dozens", "every", "the whole" | crane-up pull-back x2.5-x11, `outExpo` | TF #34 (40.77) |
| an approach or a reveal: "came", "toward me", "there it was", a creature's name | punch-in x1.5-x2.0 in 0.6-1.3 s, optional +10-13° roll | AW #4, #8, #49, #81 |
| going up: "up", "flew up", "lifted off", "into the sky" | crane up / tilt up following | TF #2, #47, #104 |
| going along: "down the street", "over the houses", "every lantern" in sequence | fast truck 1900-2450 px/s, or a truck along house fronts 700-1200 px/s | TF #93-#94, PN #18 |
| a jump in space: "pointed out the window. Up." | whip tilt or pan, 1900-2450 px in 0.6-0.7 s | TF #47 (55.37), AW #23 (35.28) |
| a tall or long thing: "ten feet tall", "arm stretched out" | tilt or pan along it, linear | AW #41, CG #4, #26-#28 |
| shaking, rumbling, the ground moving | shake ±5-25 px (spikes 50), decaying 0.5 s | TF #101-#103 |
| arriving, circling, "floated in" | fast orbit 90° in 0.15-0.3 s, or a slow 17-27° orbit | TF #15, AW #46 |
| something lights up or goes dark | light-state change on the word, in-shot or as a same-framing jump cut | TF #98-#99, PN 110.87 |
| a list | jump cuts on one set-up, each with its own small push | TF #24-#26, #77-#81 |

Keep about 80% plain pushes, 6% strong pushes, 6% pull-backs, 10-12% translations, 3% shakes (TF profile). Never two whips in a row.

**Angles and sizes by subject:** creatures from below (low or extreme low; EP01 gnome: camera at 0.5-1.5 studs, looking slightly up);
objects top-down or high (normal lens); the kid at eye level or slightly high, often in bed or from his window; reactions in CU.
About half the shots are close. Keep the subject on the centre line and out of the caption band (y 1260-1420).

---

## 5. Pacing across the video

| Part | Shot length | Notes | Reference |
|---|---|---|---|
| Hook (0-4 s) | 0.5-2.1 s | Opener accent; creature or rule image by 2.5-4 s; no title card | TF castle by 3.75; CG clown by 2.25; AW monster from frame 0 |
| World rules (to about 20 s) | 0.5-1.8 s | One picture per rule and noun; montage of locations and times of day | TF #5-#14; AW #9-#15 |
| Personal story | 0.9-1.8 s | Hero intro, plants, a short flashback | TF #16-#31 |
| Twist | 1.3-2.3 s | Slow down: longer holds with strong pushes, a reaction CU on the turn | TF #32-#37 (38.75-44.17) |
| Set piece / climax | 0.45-1.2 s | The fastest cutting: one shot per phrase, lists, accents every 3-4 shots | TF #47-#50 (55.37-57.87), #77-#81; CG act 3 at 53 cuts/min |
| Resolution | 1.0-2.2 s | Quiet wides, tender decals, warm grade | TF #105-#109 |
| Ending | 1-2 s | Return to the opening image or set; end 0.3-0.4 s after the voice | TF #114 |

Grade follows the story beats (TF: cool → warm when the magic arrives at 43.0 → cool → white/day at 111.2 → warm morning at 122.1).

**EP01 colour script** (times are VO word onsets; switch on the sentence start):

| Time (s) | Grade preset | What |
|---|---|---|
| 0.00-3.58 | `dusk` | Frame 1: the deck chair facing a lit window (matches the last frame) |
| 3.58-5.10 | `day` | Grandma's armchair |
| 5.10-7.18 | `dawn` | Dewy lawn, gnome in glasses |
| 7.18-10.30 | `day` | Street of gnomes; estate-agent board |
| 10.30-12.14 | `dusk` | KEEP OFF sign at sunset, curtains snapping shut |
| 12.14-15.02 | `day` | Next door's plastic gnomes, the hole |
| 15.02-17.90 | `night` | Gate bonk, family hands |
| 17.90-19.42 | `day` | Hero taps Grandpa's hat (spring) |
| 19.42-21.01 | `night` / `bedroom` | Goodnight wave, first blink |
| 21.01-26.61 | `sepia` | Human Grandpa's laps |
| 26.61-27.81 | `day` | SOLD sticker, Theo at the fence, the truck |
| 27.81-94.13 | `night` (P1) | The night: hall clock 9:00, gate, the lawn moves, the fence. Inserts inside Theo's room use `bedroom`. Lantern pools from 41.76 |
| 69.13-72.89 | `sepia` | Callback laps and the stop under the window |
| 74.97-76.41 | `bw` | Grandpa watching over young Dad |
| 76.41-78.65 | `bw` → `sepia` → `night` | Decades montage at the same window |
| 86.85-92.53 | `warmGlow` (P3) | FWOOM, light rolls, mounds sink |
| 92.53-94.13 | `night` | Quiet wide: gnome facing Theo's window |
| 94.13-103.49 | `dawn` (P4) | Theo in socks, the blink, the truck leaving |
| 103.49-109.23 | `dusk` (photos in `day`) | Photos on a phone in an old hand |
| 109.23-113.30 | `dusk` | Epilogue, ends on the frame-1 match |

---

## 6. Worked examples on EP01 (word times from `ep01/voice_asr.json`)

Cut = word onset - 0.02 s (the engine snaps to the frame). "Push +19" means the default linear push of +19%.

### 6.1 The opening, 0.00-26.61 s (24 shots, about 54 cuts/min: the world montage runs hot)

| # | Cut (s) | Words | Picture | Size / angle | Move | Grade |
|---|---|---|---|---|---|---|
| 1 | 0.00 | In this world, grandparents don't die. | ECU dandelion clock in an old hand → MS: the old man (olive fishing hat, grey moustache, mustard cardigan) dozing in a striped deck chair facing a lit child's window; the seeds burst on "die" (1.76) | ECU → MS, eye | **snap pull-back x4, `outExpo`** (opener) | dusk |
| 2 | 2.06 | They turn into garden | WS from behind the chair: seeds swirl across the garden | WS, eye | push +15 | dusk |
| 3 | 2.94 | gnomes. | The chair now holds a small gnome in the same hat (mustard coat) | CU, low | push +25 | dusk |
| 4 | 3.58 | First, your grandma gets | Grandma in her armchair, slippers touching the floor | MS, eye | push +18 | day |
| 5 | 4.62 | shorter. | Jump cut, same set-up: she is smaller, slippers dangling, sleeves swallowing her hands | MS, eye | push +18 | day |
| 6 | 5.10 | One morning, a gnome is wearing her | Sunrise, dewy lawn: a new gnome in a cardigan by the path; a grandkid kneels | WS, high | push +15 + slight crane down | dawn |
| 7 | 6.62 | glasses. | A blocky hand straightens round glasses on the gnome's face | INS, eye | push +25 | dawn |
| 8 | 7.18 | Nobody knows why they face the | Street of front gardens: every gnome turned to its house, each holding an unlit lantern (plant) | WS, high | truck along the kerb 800 px/s + push | day |
| 9 | 8.30 | house. | Over one gnome's shoulder up to a child's bedroom window | CU, low | push +20 | day |
| 10 | 8.78 | Houses here come with ancestors. | Estate-agent board "3 BED · BIG GARDEN · COMES WITH ANCESTORS", two gnomes posing beside it | MS, eye | push +19 | day |
| 11 | 10.30 | You never step on a lawn after dark. | KEEP OFF THE LAWN AFTER DARK sign at sunset; curtains snap shut down the street on "dark" (11.68) | WS, low | push +15 | dusk |
| 12 | 12.14 | Next door, the gnomes are plastic. | Next door's lawn: glossy plastic gnomes with price stickers, hose, kennel | MS, eye | push +19 | day |
| 13 | 13.74 | Their dog went down a hole. | The empty kennel; its lead runs across the grass into a neat round hole | INS, top-down | push +22 | day |
| 14 | 15.02 | Your gnome can't walk out of its garden. | A gnome toddles to its gate and bonks the property line on "garden" (16.32): light ripple burst | MS, gnome-eye low | push +15, 4 px shake on the bonk | night |
| 15 | 16.78 | Only family can carry it out. | Gold-outlined grown-up hands lift the gnome over the line; latch click on "out" (17.68) | MS, eye | push +19 | night |
| 16 | 17.90 | My grandpa turned last spring. | The hero (mustard hoodie) taps the hat of the red-coated gnome in the flowerbed under his window | MS, eye | push +19 | day |
| 17 | 19.42 | I say goodnight, | From inside his room, over his shoulder, he waves through the glass | OTS, eye | push +15 | bedroom |
| 18 | 20.21 | and he blinks. | The gnome blinks (2-frame swap) on "blinks" (20.55); SFX tik | CU, low | push +20 | night |
| 19 | 21.01 | For sixty years he walked our lawn at nine, | Human Grandpa strolls the dark lawn past the KEEP OFF sign | MS, eye | follow truck + push | sepia |
| 20 | 23.01 | flashlight, | The flashlight clicks on | INS, eye | push +20 | sepia |
| 21 | 23.65 | slippers, | Tartan slippers on wet grass | INS, low | push +20 | sepia |
| 22 | 24.05 | one lap, | His loop around the lawn, with a kink under one window (plant) | WS, top-down aerial | push +15 | sepia |
| 23 | 24.61 | checking for moles, he'd say, | Grandpa winks, flashlight under his chin (optional 0.56 s reaction at 25.41: Mom and Dad laughing behind the glass) | CU, low | push +25 | sepia |
| 24 | 25.97 | big ones. | Grandpa spreads his hands wide | MS, eye | push +20 | sepia |

Rules at work: R1 on every sentence; R2 on "gnomes", "glasses", "house", "flashlight / slippers / one lap"; R7 on "die", "dark",
"garden", "out", "blinks"; R10 on each time-of-day change; the opener is the accent. Shots 20-22 are the set-ups the callback at
69.13 / 69.69 / 70.33 reuses, in the same order.

### 6.2 The reveal set piece, 36.70-48.48 s (12 shots, the fastest stretch)

| # | Cut (s) | Words | Picture | Size / angle | Move |
|---|---|---|---|---|---|
| 1 | 36.70 | Then the lawn moved. | The lawn bulges like a duvet with something under it; sub-boom + rumble from "moved" (37.28) | WS, ground level | push +15, shake ±8 px from 37.28 |
| 2 | 37.66 | Dozens of mounds, | Mounds push up all across the lawn | WS → EWS, high | **crane-up pull-back x2.5, `outExpo`** ("dozens") |
| 3 | 38.70 | with eyes like bike reflectors. | Two amber eyes glint in a mound | CU, low | push +30 |
| 4 | 39.90 | Moles, | The turf splits: a pink star snout unfurls and sniffs | ECU, low | push +20 |
| 5 | 40.46 | big ones. | A second, bigger snout fills the frame | CU, extreme low | **punch-in x1.6** |
| 6 | 40.94 | Grandpa's lantern lit, | The gnome in the hero's arms; the lantern lights on "lit" (41.76): warm pool, tink-whoosh | CU, low | push +19, in-shot light-state change |
| 7 | 42.22 | and they stopped at its edge. | A gold circle of light on the grass; snouts snap back at the rim (spring recoil); held through the 0.7 s pause | INS, top-down | push +15 |
| 8 | 43.50 | Down the street. | The street of gardens, dark | EWS, high | push +10 |
| 9 | 44.56 | Every lantern lit, | Lanterns pop on garden by garden toward the camera, 0.15-0.3 s apart (cascade of tinks) | WS, low along the kerb | **fast truck 1900 px/s** |
| 10 | 45.52 | except next door. | Next door's dark lawn: a mound rolls over a plastic gnome | MS, eye | push +19 |
| 11 | 46.32 | Gnomes aren't decorations. | A lit street gnome, face lit from below, staring at its house | CU, low | push +22 |
| 12 | 47.60 | They're the fence. | The street outlined by a chain of lantern circles, mounds prowling outside; held across the pause to 48.48 | EWS, high aerial | slow crane up + push |

### 6.3 Phrase lists, callbacks and a long sentence

**Phrase list (R3, R4):** "Gone the mounds rolled closer, to the flowers, to the bricks, to the glass."
59.37 "Gone" → the price sticker fluttering on the soil (INS, 0.40 s, the minimum); 59.77 "the mounds rolled closer" → mounds rolling
at the house (WS, low); **60.73** "to the flowers" → snouts among the tulips; **61.37** "to the bricks" → mounds against the brick
wall; **61.93** "to the glass" → amber eyes fogging Theo's window while he sleeps (CU, push +25). Each cut sits on the phrase start,
0.26 s before its noun.

**Callback (section 3):** "Flashlight, slippers, one lap" at **69.13 / 69.69 / 70.33** reuses opening shots 20 / 21 / 22 exactly
(same framing, same order, same `sepia` grade), then **70.89** "and one stop always under my window" adds the new picture: Grandpa
standing in this flowerbed, flashlight on the lawn, the hero aged 5 asleep inside. The repetition is the reveal.

**A long sentence that the script wants as one move:** "FWOOM. His lantern flared. Light rolled across the lawn, and every mound sank,
eyes winking out pair by pair." (86.87-92.23, 5.7 s). R6 caps a shot at 2.3 s, so it becomes four shots that read as one move,
keeping the screen direction (the ring of light always travels left to right):
86.85 "FWOOM. His lantern flared." → CU of the lantern flaring white-gold, `warmGlow` on, bloom up (1.76 s);
88.61 "Light rolled across the lawn" → ground level, the ring rolls past the lens (fast truck);
89.97 "and every mound sank," → WS high, mounds deflate;
91.01 "eyes winking out pair by pair." → MS, the amber pairs blink out one at a time, the last on "pair" (92.23);
then 92.53 "Then he stood still, facing Theo's window." → the quiet wide, back to `night`.

---

## 7. QA checklist before any render

Run these on the timeline JSON against the ASR word list (a short Python check is enough):

1. Shot count 88-100; cuts per minute 45-52 overall; median 1.15-1.25 s; p90 ≤ 2.0 s; max ≤ 2.3 s (one ≤ 2.5 s); no shot under 0.35 s.
2. Every sentence's first word has a cut between -100 ms and +33 ms of its onset (≥ 95% of sentences).
3. Every cut is within -100..+33 ms of some word onset, except listed silence beats.
4. Every list item named in the script has its own shot; every sign or text has its own insert at the moment it is spoken.
5. Every shot has a `move`; 75-85% are plain pushes with Z in 0.08-0.32; accents are 12-18%, never two whips in a row; shot 1 is an accent.
6. 45-50% close shots; creature shots low; object inserts top-down or high.
7. Grade and location changes fall on cuts at sentence starts (or are listed in-shot light events); every new location or time of day opens with an establishing shot.
8. Every `events[].t` equals the onset of its word (±1 frame); every decal swap is held ≥ 0.4 s; at most 2 swaps per shot.
9. No set-up repeats back to back unless it is a list jump cut or a deliberate callback.
10. The last shot ends 0.3-0.4 s after the last audible voice sample (EP01: about 113.3 s), and its last frame matches frame 0 when the story loops.
