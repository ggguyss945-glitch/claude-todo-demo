# Script analysis: r4 "The Tooth Fairies Project" (the owner's favourite)

Reference only. The lines are quoted here so we can analyse them. Do not reuse them, the characters, the rule or the plot. We borrow the mechanics, not the content.

- Source: `ref/r4_tooth_fairies.mp4` (720x1280, 30 fps, 128.03 s, trimmed so the ending is missing). Inputs: ASR word times (`asr/r4_tooth_fairies.json`), both frame sheets, and about 250 extra frames I extracted with `ffmpeg -ss` (every 0.5-0.8 s through the whole video, plus 0.05-0.1 s steps around doubtful words) into `scratchpad/rbx/work/r4script/`.
- **Timing caveats.**
  - In our copy the **video stream starts at 1.27 s** and the audio starts at 0.00. So we cannot see the first 1.27 s of picture. Players hold the first available frame, which is a night exterior of a bedroom window with the caption "don't" already on screen. So in our copy the rule is **spoken** on the first frame, not written. Whether the original had a title card in 0.0-1.27 s is unknown.
  - The frame-sheet labels are about **0.8 s early**. For example, the sheet says "0:04 every" when the word is at 4.80, and "0:58 we've" when it is at 58.83. All times below come from the word timings and from exact `-ss` frames.
  - Audio: there is a music/ambience bed under everything. No stretch is quieter than -35 dB for 0.25 s or more.
- **Format.** One narrator, the hero. It opens as world lore addressed to "you" (0-21 s), then switches to first person, past tense ("I've lost 19 baby teeth", 21.44). The only quoted speaker is the **Fairy Queen**, plus one word from the hero ("Home?"). **Fern, the emotional centre, never speaks.** She communicates only through her drawings and her body (drooping wings, tapping the lid).
- **Cast on screen.**
  - Hero: a blocky Roblox avatar in a green three-eyed-alien hood. His face decal changes with every beat (smile, "o" mouth, angry brows, sad frown, soft eyes). As an adult in the epilogue he wears the same hood.
  - Fern: a teal-skinned, red-eyed, zombie-ish fairy in a pink tutu with red hair buns. She is cute-creepy.
  - The Queen: a pink goblin with yellow bug eyes, bad teeth and moth wings. Her grey crown has a tooth on top.
  - About 100 assorted creature fairies.
  - The daughter: a blonde Roblox girl.

### ASR corrections (checked against the burned-in captions)

| t (s) | ASR | Corrected | Evidence |
|---|---|---|---|
| 3.44 | "them-a castle." | "them. A castle." | The caption shows "them" (3.6), then "castle" (3.9). The noun is held back as a separate beat. |
| 31.62 | "Tower," | "a tower," | The caption shows "a" at 31.50, then "tower". The ASR dropped it at its segment boundary (31.42/31.50). The later list (87.44) also says "a tower". |
| 32.74 | "every one" | "every one" (each drawing) | The caption wrongly writes "everyone". This is a caption error, not a script choice. |
| 36.66 | "Number 20." | "Number 20." | The caption renders it as **"No."** then **"20"**. |
| 39.86 / 68.43 | "fern" | "Fern" | The caption shows "fern" in lower case at 40.0. It is capitalised at 25.7 and 68.8. |
| 57.07 | "at the stars" | kept | The caption reads "at". It continues "She pointed out the window. Up. Past the mountain, past the moon, at the stars." |
| 79.76 | "ten thousand" | "ten thousand" | The caption renders it as the digits **"10,000"**. All numbers in the captions are digits: "10,000", "19", "20". |
| 98.72 | "drawing." | "drawings." | The caption shows "drawings" at 99.3. |
| 109.59 | "Click the last brick." | "Click. The last brick." | The caption shows "click" over Fern pressing the tooth into the wall. It is an onomatopoeia beat on its own. |
| 127.75 | "a tiny" (end) | "a tiny…" (cut) | The video ends at 128.03, mid-sentence. The last frame shows the gold coin and a **purple drawing card** under the pillow, so the missing word is almost certainly "drawing". |

---

## 1. Clean transcript, numbered, tagged, with picture

Tags: RULE / CONSEQUENCE / PERSON / ESCALATION / TWIST / REVEAL / EMOTION / CALLBACK / CLIFFHANGER / DIALOGUE / DESCRIPTION (plus REVERSAL and PLANT).

| # | Start | Sentence | W | Tag | Picture (one line) |
|---|---|---|---|---|---|
| 1 | 0.08 | In this world, the tooth fairies don't just collect your teeth, they're building something with them. | 16 | **RULE** (myth remix + open loop) | No picture before 1.27 s in our copy. From 1.27: night exterior of a lit bedroom window, a chubby purple fairy inside holding a white tooth. At 1.8-2.4 it flies out over the rooftops into a galaxy sky. |
| 2 | 3.60 | A castle. | 2 | **RULE** (pay-off of the micro loop) | 3.77: a tall pink-and-white castle whose walls are built of teeth, with a star on the top spire. |
| 3 | 4.40 | You see, every baby tooth ever lost becomes one brick. | 10 | RULE (mechanic) | Fairies on a white brick wall. One carries a giant tooth (5.0) and sets it in as a brick (6.4). |
| 4 | 7.52 | For 10,000 years, they've been building it on top of the tallest mountain in the world. | 16 | CONSEQUENCE / DESCRIPTION (scale) | Low-angle castle, towers stacked with teeth (7.5). Wide at 9.07: the castle on the peak of an icy mountain under the stars. |
| 5 | 11.20 | On clear nights, you can see it glowing white, tower after tower. | 12 | CONSEQUENCE (everyone can see it) | Over the shoulder: the kid in the alien hood at his bedroom window, mountain beyond (11.3). Three quick tower close-ups at 13.3-14.4, one per "tower". |
| 6 | 14.48 | And nobody knows what happens when it's done. | 8 | CONSEQUENCE + **mystery loop** | Close-up of the kid's face, "o" mouth, eyes wide (14.5-16.0). |
| 7 | 16.16 | There's only one rule: the tooth has to be under your pillow. | 12 | **RULE** (rule within the rule) | An orange-haired frog-like fairy waves outside (16.1). Kid asleep on his pillow (17.1). |
| 8 | 18.64 | A fairy can never take a tooth out of your hand. | 11 | RULE (**PLANT**) | The purple fairy floats in through the window, reaching (18.6-19.4), then clings to the wall (19.9). |
| 9 | 20.56 | It has to be given. | 5 | RULE (**PLANT**) | The kid in bed hands the tooth to the purple fairy. Wall clock at 12 (20.6-21.2). |
| 10 | 21.44 | I've lost 19 baby teeth, and every single time, the same fairy came. | 13 | **PERSON** (switch to "I") | The kid sitting up in bed, grinning, clock at 12 (21.7-23.0). At 23.07 Fern appears in the open window. |
| 11 | 25.12 | Her name was Fern. | 4 | PERSON (naming) | Fern close-up: teal skin, huge red eyes, crooked-tooth grin (25.2-26.0). |
| 12 | 26.08 | I stayed up to meet her when I was six. | 9 | PERSON (backstory) | The kid awake with Fern beside him on the bed, clock at 12. |
| 13 | 27.52 | She always left a gold coin and a tiny drawing, no bigger than a stamp. | 14 | DESCRIPTION (**PLANT**) | Pillow close-up: gold coin, then a small white card (27.6-29.6). At 30.0 the kid holds the card up, with a star on it. |
| 14 | 30.88 | A star, a tower, a little door. | 7 | DESCRIPTION (**PLANT**) | One card insert per noun on the blanket: star (31.0), tower (31.6), little door (32.2). |
| 15 | 32.66 | I kept every one in a shoebox. | 7 | DESCRIPTION (**PLANT**) | The kid smiling, the door card in front of him (32.6-34.1). The box itself is not shown yet. |
| 16 | 34.18 | Then last night, my very last baby tooth fell out. | 10 | **ESCALATION** ("last night" + "last") | Exterior of the house at night (34.2). The kid yanks the tooth with an angry face and red motion streaks (35.0-36.4). |
| 17 | 36.66 | Number 20. | 2 | ESCALATION (count completes) | The kid grins and holds up the tooth, clock at 12. Captions "No." then "20". |
| 18 | 37.30 | I put it under my pillow like always. | 8 | DESCRIPTION (routine marker) | The kid asleep in bed (37.3-38.7). |
| 19 | 38.74 | But at midnight, it wasn't just Fern at my window. | 10 | **TWIST 1** (routine broken) | Extreme close-up of the clock, both hands on XII (38.8-39.6). Then the window: Fern with other fairies behind her (39.6-40.8). |
| 20 | 40.82 | It was a hundred fairies, glowing, buzzing, lighting up my whole room. | 12 | ESCALATION (spectacle) | Aerial: a swarm dives at the house window (40.8). A wall of glowing fairies (42.0). The kid's shocked "o" face (42.6). The room fills with fairies (43.3-44.0). |
| 21 | 44.18 | And in front of them, a fairy with a crown made of a tiny silver tooth. | 16 | ESCALATION (new figure) | The Queen at low angle: grey crown topped by a floating tooth (44.2-47.1). A "SPACE" poster is half-visible behind her (46.2). |
| 22 | 47.22 | The fairy queen. | 3 | REVEAL (naming) | Low-angle close-up of the Queen's goblin face and bad teeth. |
| 23 | 48.10 | "Your tooth," she said, "is the last brick." | 8 | **DIALOGUE (Queen)**, **TWIST 2** (main twist) | The Queen in front of a crowd of fairies, glow-in-the-dark stars on the ceiling (48.0-50.3). |
| 24 | 50.34 | I froze. | 2 | EMOTION (reaction) | The kid in profile close-up, "o" mouth (50.3). |
| 25 | 50.90 | "The castle is finished tonight," she said. | 7 | DIALOGUE (Queen), ticking clock | The Queen, medium shot, in the bedroom. |
| 26 | 52.58 | "And when it's done, we go home." | 7 | DIALOGUE (Queen), **CALLBACK** (pays #6) | The Queen wide, fairies behind (52.6-54.1). |
| 27 | 54.02 | "Home?" | 1 | DIALOGUE (hero) | The kid close-up, puzzled, clock behind. |
| 28 | 54.42 | She pointed out the window. | 5 | DESCRIPTION | The Queen from behind, pointing (54.5-55.3). |
| 29 | 55.30 | Up. | 1 | REVEAL (start) | Aerial: fairies swarming above the roof (55.4). |
| 30 | 55.63 | Past the mountain, past the moon, at the stars. | 9 | REVEAL (journey list) | One shot per noun: purple nebula (55.9), the moon (56.6), deep space with one bright star (57.1-57.8). |
| 31 | 57.87 | "The castle is a ship." | 5 | DIALOGUE (Queen, no tag, inferred), **REVEAL/REVERSAL** | Low-angle castle against the night sky (57.9-59.2). |
| 32 | 58.83 | "We've been building our way home for 10,000 years." | 9 | DIALOGUE (Queen), CALLBACK (#4) | The Queen close-up in front of her fairies (59.3-61.2). Caption "10,000". |
| 33 | 61.23 | I pulled the tooth out from under my pillow and squeezed it in my fist. | 15 | EMOTION (agency, first defiance) | The kid pulls the tooth from under the pillow with angry brows, clock behind (61.3-64.0). |
| 34 | 64.03 | If I gave it to them, there'd be no more tooth fairies, ever. | 13 | ESCALATION (**stakes**) | Sad frown decal, tooth in hand (64.0). Then the Queen standing (64.9-66.5). |
| 35 | 66.51 | No more coins. | 3 | EMOTION (loss list 1) | A gold coin on the bedside table (66.5). |
| 36 | 67.31 | No more drawings. | 3 | EMOTION (loss list 2) | The red shoebox lid (67.3). This is the first time we see the box. |
| 37 | 68.11 | No more Fern. | 3 | EMOTION (loss list 3, personal) | Fern close-up in front of the crowd (68.2-69.0). |
| 38 | 68.99 | The queen didn't move. | 4 | **REVERSAL** (the rule becomes the hero's power) | The Queen, still, medium shot (69.0-70.0). |
| 39 | 69.87 | She couldn't. | 2 | REVERSAL | The Queen, closer. |
| 40 | 70.43 | A fairy can never take a tooth out of your hand. | 11 | **CALLBACK** (word for word, #8) | The kid with the tooth in his fist, determined. A "TO THE STARS" rocket poster behind him (70.5-72.4). |
| 41 | 72.43 | "Take your time," she said softly. | 6 | DIALOGUE (Queen), de-escalation | The Queen close-up, soft, fairies behind. |
| 42 | 73.87 | And one by one, the fairies flew back outside to wait. | 11 | DESCRIPTION | Fairies fly out through the window (73.9-75.0). Exterior: fairies lined up along the roof edge (75.1-76.5). |
| 43 | 76.51 | All except Fern. | 3 | PERSON (isolation) | Fern alone on the window sill (76.5-77.5). |
| 44 | 77.55 | She landed on my shoebox. | 5 | CALLBACK (#15) | Fern in the room, landing (77.5-78.6). |
| 45 | 78.67 | Her wings were drooping. | 4 | EMOTION | Fern close-up, "SPACE" planets poster behind her (78.6-80.7). |
| 46 | 79.76 | Thin, tired, ten thousand years tired. | 6 | EMOTION + CALLBACK (#4, now emotional) | Fern standing on the red shoebox (80.7-82.1). Caption "10,000". |
| 47 | 82.08 | She tapped the lid. | 4 | DESCRIPTION (silent communication) | Fern on the box. |
| 48 | 82.88 | I opened it. | 3 | DESCRIPTION | The kid leaning in to the box (82.9). |
| 49 | 83.44 | Nineteen tiny drawings. | 3 | CALLBACK (#10, the 19) | Inside the box: a pile of the small cards (83.4-84.7). |
| 50 | 84.72 | I'd never really looked at them all together, so I laid them out on the floor. | 16 | DESCRIPTION (set-up of the puzzle) | The kid with a focused face (84.8-86.2). He kneels on the rug laying out cards, Fern beside him (86.2-87.4). |
| 51 | 87.44 | A star, a tower, a little door, a window, a family waving. | 12 | CALLBACK (#14 list) + new items | One insert per card: star (87.6), tower (88.2), door (88.8), window (89.4), family (90.0). |
| 52 | 90.56 | And when I pushed them all together, they made one picture. | 11 | **REVEAL** | Top-down: the cards slide together into a grid (90.6-92.8). |
| 53 | 92.80 | A tiny house on a faraway star, and a family of fairies standing in the doorway, waiting. | 17 | **REVEAL** | The assembled picture: a pink house with a family in the doorway, on a big yellow star or planet, small stars around (92.9-96.6). |
| 54 | 97.04 | For six years, she wasn't just leaving me drawings. | 9 | **REVEAL (reframe)** / EMOTION | Fern close-up on "waiting" (96.7). The kid and Fern over the picture on the floor (97.0-99.2). |
| 55 | 99.19 | She was telling me where she wanted to go. | 9 | **EMOTION (peak)** | Fern close-up, huge red eyes, soft (99.3-100.9). |
| 56 | 100.87 | I looked at Fern, then at the tooth in my hand, and I opened my fist. | 16 | **EMOTION (peak), sacrifice/choice**; CALLBACK ("it has to be given", #9) | The kid close-up, soft-eyes decal, gentle smile (100.9-102.9). His open hand with the tooth (103.0-103.9). |
| 57 | 103.99 | She picked it up with both arms and flew it out the window, over the houses, over the trees, all the way to the top of the mountain. | 28 | DESCRIPTION (journey) | Fern hugs the tooth with both arms (104.0-105.3). She flies out of the window (106.0). Aerial over the street and houses (106.5-107.9), then the mountain and the castle top (108.4-109.6). |
| 58 | 109.59 | Click. | 1 | PAYOFF (sound word) | Fern on the castle wall pressing the brick in. Caption "click". |
| 59 | 109.99 | The last brick. | 3 | CALLBACK (#23) | Fern waves from the castle wall. |
| 60 | 110.79 | The whole castle lit up so bright it turned night into day. | 12 | REVEAL (spectacle) | The castle blazes white (111.2-112.5). The suburb is lit like daytime under a bright sky (112.5-113.7). |
| 61 | 113.75 | The towers shook, the ground rumbled, and the castle lifted off the mountain and flew up into the stars. | 19 | REVEAL (spectacle), pays #31 | Tower close-up in daylight (113.8). The castle base with red-and-white thruster pods lifts off (114.8-115.9). Hovering (116.0). In space above the peak (117.5-119.0). |
| 62 | 119.03 | I watched until it was just one tiny light. | 9 | EMOTION (release) | From the bedroom window: night sky with one tiny point of light, the kid's arm on the sill. |
| 63 | 121.03 | That was 20 years ago. | 5 | **TWIST 3** (time jump; the narrator is an adult) | The assembled picture, **now framed on a wall**. This visual callback is never narrated. |
| 64 | 122.23 | Last night, my daughter lost her first tooth. | 8 | CALLBACK (generational; "last night") | The adult narrator (same alien hood) beside a blonde girl in bed who holds up a tooth. Clock at 12. |
| 65 | 124.23 | She put it under her pillow. | 6 | CALLBACK (#7) | The girl asleep (124.2-125.2). |
| 66 | 125.27 | And this morning, when she woke up, there was a gold coin and a tiny… | 15 | **CLIFFHANGER** + CALLBACK (#13) | The girl wakes with a huge smile, clock at 12 (125.2-126.5). Pillow: gold coin (126.5). At 127.6 a **purple** card with stars and a small winged figure is tucked under the pillow. Cut at 128.03. |

---

## 2. Beat map

| Time | Beat | What happens |
|---|---|---|
| 0.08-3.84 | **Rule (first sentence)** | "In this world, the tooth fairies don't just collect your teeth, they're building something with them." The rule lands on **"building" (2.72)**, 2.7 s in. The object is withheld until **"castle" (3.84)**. This is a myth remix: a known childhood figure plus a hidden purpose. |
| 4.40-7.04 | Rule mechanic | "every baby tooth ever lost becomes one brick". It makes every viewer part of the world, because they have lost teeth too. |
| 7.52-16.0 | **Consequence (lore + society)** | Scale: "10,000 years", "tallest mountain in the world". Visibility: "On clear nights, you can see it". Mystery: "nobody knows what happens when it's done" (14.48). This is a lore block more than a society block. Nobody's daily life changes. |
| 16.16-21.04 | **Rule within the rule** | "There's only one rule: the tooth has to be under your pillow. A fairy can never take a tooth out of your hand. It has to be given." It sounds like folklore colour, but it is the **key that locks and later unlocks the climax**. |
| **21.44** | **The one person** | "I've lost 19 baby teeth, and every single time, the same fairy came." This is the first "I". Fern is named at **25.52**. |
| 26.08-34.18 | Backstory + **the plant** | Stayed up at six. A coin and a tiny drawing each time: "A star, a tower, a little door." "I kept every one in a shoebox." At the **30 s mark the story is planting, not twisting.** |
| **34.18** | Inciting incident | "Then last night, my very last baby tooth fell out. Number 20." A countdown is completed: 19 then 20, "last". |
| **38.74** | **Twist 1** (routine broken) | "But at midnight, it wasn't just Fern at my window." Then 100 fairies (40.82) and the Queen (44.18). |
| **48.10-49.78** | **Twist 2 (the main twist)** | "Your tooth… is the last brick." The hero's ordinary tooth is the most important object in the world. |
| 50.90-54.02 | Ticking clock + pay-off of the mystery | "finished tonight", "when it's done, we go home". This pays off loop L2, opened at 14.48 (38 s earlier). |
| 54.02-61.23 | **Reveal/reversal** | "Home?" "Up. Past the mountain, past the moon, at the stars." **"The castle is a ship."** (57.87) The castle the viewer has watched for a minute is re-framed. |
| 61.23-68.99 | **Dilemma + stakes** | The kid hides the tooth in his fist. "No more coins. No more drawings. No more Fern." The stakes get smaller and more personal on purpose. |
| **68.99-72.43** | **Reversal: the rule becomes the hero's power** | "The queen didn't move. She couldn't. A fairy can never take a tooth out of your hand." The rule planted at 18.64 is repeated word for word. |
| 72.43-77.55 | De-escalation | "Take your time." The fairies leave. "All except Fern." The ticking clock is deliberately removed, so the choice becomes moral, not forced. |
| 77.55-90.56 | Helper's silent appeal | Drooping wings, "ten thousand years tired". She taps the shoebox lid. "Nineteen tiny drawings." They are laid out, and the list is repeated and **extended**: "…a window, a family waving". |
| **90.56-99.19** | **Twist 4: the plant pays off (emotional reveal)** | The drawings make one picture: "a family of fairies standing in the doorway, waiting". "For six years, she wasn't just leaving me drawings. She was telling me where she wanted to go." |
| **97.04-103.99** | **Emotional peak** | The reframe, Fern's close-up, then "I opened my fist." This is the sacrifice, and it pays the second half of the rule ("it has to be given"). |
| 103.99-119.03 | **Spectacle payoff** | The flight to the mountain, "Click. The last brick." Night into day, lift-off "into the stars", "just one tiny light". This pays "glowing white" (11.2) and "nobody knows what happens when it's done" in full. |
| **121.03** | **Twist 5: time jump / narrator reveal** | "That was 20 years ago." The narrator we took for a kid is an adult. The framed picture is on the wall. |
| 122.23-125.27 | Generational mirror | "Last night, my daughter lost her first tooth." (first against last) "under her pillow". |
| **125.27-128.03** | **Twist 6 / cliffhanger, the last beat before the trim** | "there was a gold coin and a tiny…" But there are supposed to be **no more tooth fairies, ever** (64.03). A new drawing (purple card, stars, a winged figure) appears. The cut lands mid-sentence. |

**Twist and turn cadence.** The turns land at 38.7, 49.8, 52.6, 57.9, 64.0, 69.0/70.4, 76.5, 92.8, 97.0, 100.9, 113.8, 121.0 and 125.3. After the first twist there is a new turn about every **7 s** on average (range 2.8-16 s). That is denser than r1 (12-18 s).

**Compared with the 4-step format in NICHE_NOTES:**
- Rule on the first frame: yes in the audio (0.08 s). The first visible frame (1.27 s) shows a fairy with a tooth inside a child's room, which acts as the picture of the rule.
- Consequence: 4.4-21 s. It is world lore (scale, visibility, mystery, the one rule) rather than "how people live".
- Person: 21.4 s (the narrator himself), and the companion character at 25.5 s.
- The twist is **late, as in r1.**
  - 30 s holds the **plant** (the drawings).
  - The hook at 34.2 ("last night… very last tooth") carries the viewer.
  - Twist 1 lands at **38.7 s**, the main twist at **48.1-49.8 s**.
- The 2:00+ length is carried by **five more blocks after the main twist**: reveal (ship), dilemma (fist), the helper's silent appeal plus the puzzle reveal, choice plus spectacle, and the time-jump epilogue.

### Open loops (question opened, then paid)

| # | Opened | Question in the viewer's head | Paid | Gap |
|---|---|---|---|---|
| L1 | 2.72 "building something with them" | Building what? | 3.84 "A castle." | 1.1 s (instant micro-loop on the first line) |
| L2 | 14.48 "nobody knows what happens when it's done" | What happens when it's done? | 52.58 "we go home", 57.87 "The castle is a ship", 113.75 lift-off | 38 s, then 99 s (**the spine**) |
| L3 | 18.64-21.04 "can never take a tooth out of your hand. It has to be given." | Why mention it? (unconscious plant) | 68.99-72.03 (the Queen can't take it), 100.87 "I opened my fist" | 50 s and 82 s. Each half of the rule is paid separately. |
| L4 | 21.44 "19 baby teeth… the same fairy" | Why always the same one? | 76.51 "All except Fern", 97.04 "she was telling me…" | 55-76 s |
| L5 | 27.52-34.18 "a tiny drawing… a star, a tower, a little door… I kept every one in a shoebox" | (hidden, seems like flavour) | 82.08-99.19 (the drawings form a picture and a message) | about 55-70 s (**the best plant in the set**) |
| L6 | 34.18 "my very last baby tooth" + 36.66 "Number 20" | What is special about the last one? | 48.10 "Your tooth is the last brick" | 14 s |
| L7 | 38.74 "it wasn't just Fern at my window" | Who else is here? | 40.82 a hundred fairies, 47.22 the Queen | 2-8 s |
| L8 | 52.58 "we go home" / 54.02 "Home?" | Where is home? | 54.42-57.87 "Up… at the stars. The castle is a ship." | 2-5 s |
| L9 | 61.23 the tooth squeezed in his fist | Will he give it? | 100.87 "I opened my fist" | 40 s (the dilemma loop) |
| L10 | 76.51 "All except Fern" | Why does she stay? What does she want? | 82.08 (she taps the lid), 99.19 "telling me where she wanted to go" | 6-23 s |
| L11 | 7.52 "10,000 years" | (scale) | 58.83 "building our way home for 10,000 years", 79.76 "ten thousand years tired" | repeated twice, the last time as emotion, not information |
| L12 | 11.20 "you can see it glowing white" | (image) | 110.79 "turned night into day", 119.03 "just one tiny light" | inverted at the end (huge glow, then one dot) |
| L13 | 64.03 "no more tooth fairies, ever" | (a promise of loss) | **contradicted** at 125.27: "there was a gold coin and a tiny…" | opens the final loop |
| L14 | 125.27 coin plus the new drawing | Who left it? What does it show? | not paid (cut) | open |

---

## 3. Numbers

- **Runtime analysed:** 128.03 s, all narrated. The first word starts at 0.08 s and the last word starts at 127.75. The cut lands mid-sentence.
- **Total words:** **558** in the clean transcript ("10,000" counts as one word). The ASR count is 556; the difference is the restored "a" and the split "them. A".
- **Pace:**
  - **261 wpm overall**, about **271 wpm while speaking**. Pauses (inter-word gaps of 0.5 s or more, minus about 0.3 s of word) add up to only about **4.6 s**.
  - The longest gap between words is **0.64 s** (after "10,000" at 60.11, and after "stars." at 118.39). Seventeen gaps fall between 0.53 and 0.64 s. They sit on full stops that close a key noun: "castle.", "Fern.", "shoebox.", "brick.", "drawings.". There are **no dramatic pauses**. Even "I froze." and "She couldn't." follow on at under 0.6 s.
  - The median interval between word starts is 0.16 s (4.3 words per second). This is a sped-up or very fast read. Normal storytelling is about 160-190 wpm.
  - **For our owner, who reads it himself:** at a natural 180-200 wpm, 558 words takes 2:50-3:05. To hit 2:00-2:30 he can either (a) write **400-480 words** and read at about 200 wpm, or (b) read about 215-230 wpm and speed the take up 1.1-1.15x in the edit. Option (b) keeps the reference's density.
- **Pace and cuts by section:**

| Section | Time | Sentences | Words | wpm | Mean sentence length | Cuts | Mean shot |
|---|---|---|---|---|---|---|---|
| A rule + world | 0.0-21.4 | 9 | 92 | 257 | 10.2 | 14 | 1.53 s |
| B person + plant | 21.4-34.2 | 6 | 56 | 264 | 9.3 | 10 | 1.27 s |
| C last tooth, fairies, queen, last brick | 34.2-50.3 | 8 | 69 | 256 | 8.6 | 13 | 1.24 s |
| D home/ship reveal | 50.3-61.2 | 9 | 46 | 253 | **5.1** | 10 | **1.09 s** |
| E dilemma | 61.2-77.5 | 11 | 74 | 272 | 6.7 | 15 | **1.09 s** |
| F Fern + drawings | 77.5-100.9 | 12 | 99 | 255 | 8.2 | 18 | 1.30 s |
| G choice + lift-off | 100.9-121.0 | 7 | 88 | 262 | **12.6** | 16 | 1.26 s |
| H epilogue | 121.0-128.0 | 4 | 34 | 291 | 8.5 | 6 | 1.17 s |

  - The speed in wpm is almost flat (253-272) across the whole short. The **sentence length** changes the felt tempo instead.
  - Dialogue and dilemma (D, E) use 5-7-word sentences with the fastest cutting.
  - The spectacle (G) uses long comma-chained travelling sentences (28 and 19 words).
  - About **102 cuts**, so about 103 shots, with a mean shot of **1.24 s**.
- **Sentence length** (66 sentences):
  - median **8** words, mean 8.5, minimum 1, maximum 28.
  - 1-5 words: **24 (36%)**; 6-10 words: 20 (30%); 11-15: 14 (21%); 16-20: 7 (11%); 21 or more: 1 (2%).
  - The median drops from 8 (before 64 s) to 6 (after), because the second half has more punches.
  - There are four one-word sentences: "Home?", "Up.", "Click." (plus "A castle." and "Number 20." at two words).
- **Sentence openers:**
  - "And" 6, "But" 1, "Then" 1, "So" 0. That is **8 of 66 (12%)** starting with a connective.
  - "But" is used **once**, on the first twist ("But at midnight", 38.74). "Then" is used once, on the inciting incident ("Then last night", 34.18). Each connective marks a structural hinge.
  - Other frequent openers: "I" 8, "She" 8, "The" 7, "A" 6, "No more" 3.
- **Narrative person:**
  - First person (I/me/my/I've/I'd): **27**. Second person (you/your): **8**. That is 6 from the narrator, all in the first 21 s plus the rule restated at 70.43, and 2 in the Queen's lines.
  - Third person: she/her **19** (Fern, the Queen, the daughter), they/them **10**. The Queen's "we/our": 3.
  - Structure: the "you" lore runs for 21 s. The first "I" lands at **21.44 s (17% in)**. From there it is first person, past tense, with present perfect at the start ("I've lost 19"). This hides the fact that the narrator is now an adult until 121 s.
- **Dialogue:**
  - 7 quoted sentences, **36 words (6.5% of words)**, about 13 s of the runtime (10%).
  - The Queen has 6 lines:
    - "Your tooth… is the last brick." (48.10)
    - "The castle is finished tonight" (50.90)
    - "And when it's done, we go home." (52.58)
    - "The castle is a ship." (57.87, untagged)
    - "We've been building our way home for 10,000 years." (58.83, untagged)
    - "Take your time" (72.43)
  - The hero has 1 line: "Home?" (54.02).
  - **Fern has 0 lines.** Neither do the daughter or the other fairies.
  - Every quoted line is a reveal or a turn. None is small talk.
  - Speech tags are minimal: "she said" ×3 and "she said softly" ×1. Two key lines carry no tag at all.
- **Information rate:**
  - **57 new facts or images** in 125 s. The median gap is **2.1 s**, the mean 2.2 s.
  - The longest stretch without a new fact is 5.6 s (103.99-109.59, the flight sentence). Even there, the picture changes 6 times: Fern, window, street, houses, mountain, castle.
  - Concrete nouns get their own shots: "star / tower / little door", "mountain / moon / stars", "coins / drawings / Fern".
- **Repeated words** (lemmas):
  - tooth **12** (+ teeth 2); **tiny 6**; castle 5; fairy 5 / fairies 5; Fern 5; **last 5** ("last night" ×2, "very last", "last brick" ×2)
  - years 5; mountain 4; pillow 4; window 4; "no more" 4; tower 4; "just" 4 (the "not just X" reveal engine, see Devices)
  - brick 3; home 3; hand 3; flew 3; building 3; drawings 3 (+ drawing 1); star 3 / stars 2; one 7 (one brick, one rule, one by one, one picture, one tiny light).
- **Repeated phrases** (callback chains):
  - "A fairy can never take a tooth out of your hand." ×2, word for word (18.64, 70.43).
  - "under ___ pillow" ×4 (your 16.16, my 37.30, my 61.23, her 124.23).
  - "a star, a tower, a little door" ×2 (30.88, 87.44, the second time extended to five items).
  - "the last brick" ×2 (Queen 48.10, narrator 109.99).
  - "a gold coin and a tiny…" ×2 (27.52, 125.27).
  - "last night" ×2 (34.18, 122.23).
  - "10,000 years" ×3 (7.52, 58.83, 79.76).
  - Parallel travel phrases: "past the… past the…" and "over the… over the…".
  - Routine markers that a break can contrast with: "every single time", "like always", "always".
- **Numbers and specific details:**
  - "10,000 years" ×3; "the tallest mountain in the world"; "19 baby teeth" then "Number 20" then "Nineteen tiny drawings"; "when I was six" then "For six years"; "a hundred fairies"; "20 years ago" (which echoes tooth number 20); "first tooth" (which echoes "very last baby tooth"); "one brick", "one rule", "one picture", "one tiny light".
  - Objects: gold coin; tiny drawing "no bigger than a stamp"; star, tower, little door, window, family waving; shoebox (and its lid); pillow; fist; "crown made of a tiny silver tooth"; wings "drooping"; "both arms"; "Click".
  - Sensory: glowing, buzzing, "lighting up my whole room", "turned night into day", towers "shook", ground "rumbled", "one tiny light".

---

## 4. Devices (what keeps people watching)

| # | Device | Example (time) | Why it works |
|---|---|---|---|
| 1 | **First-frame rule as a myth remix** | "In this world, the tooth fairies don't just collect your teeth, they're building something with them." (0.08) | A universal childhood myth plus a hidden purpose. The viewer already knows half the world, so the twist lands instantly. |
| 2 | **Withheld noun, micro-loop** | "…building something with them." then "A castle." (2.72→3.84) | The first open loop is paid in 1.1 s, which teaches the viewer that this video pays off. |
| 3 | **"You" plus a universal mechanic** | "You see, every baby tooth ever lost becomes one brick." (4.40) | The viewer's own lost teeth are in that castle. Personal involvement comes before any character exists. |
| 4 | **Specific scale numbers** | "For 10,000 years… the tallest mountain in the world" (7.52) | Big, concrete and quotable. The same number is reused twice more. |
| 5 | **Visible-to-everyone proof** | "On clear nights, you can see it glowing white, tower after tower." (11.20) | It makes the impossible thing part of normal life. This is the "society" note. |
| 6 | **Mystery line** | "And nobody knows what happens when it's done." (14.48) | It opens the spine loop L2 and is paid at 52.6 and 57.9 (and 113.8). |
| 7 | **Rule within the rule, as Chekhov's rule** | "There's only one rule… A fairy can never take a tooth out of your hand. It has to be given." (16.16-21.04) | It sounds like charming lore. Its two halves later become the lock ("can never take", 68.99-72.43) and the key ("given", 100.87) of the climax. |
| 8 | **Count-up to "the last one"** | "I've lost 19 baby teeth" (21.44), "my very last baby tooth… Number 20." (34.18-36.66) | A built-in clock: the viewer knows the last one is special before being told why. |
| 9 | **Naming = attachment** | "Her name was Fern." (25.12) | Four words, a close-up and a caption. It turns a creature into a person in 1 s. |
| 10 | **Micro-memory** | "I stayed up to meet her when I was six." (26.08) | One line of history makes the relationship feel years deep. |
| 11 | **Innocent plant** | "a gold coin and a tiny drawing, no bigger than a stamp. A star, a tower, a little door. I kept every one in a shoebox." (27.52-34.18) | It reads as cute detail at the 30 s mark. It is the key to the whole emotional reveal 60 s later. |
| 12 | **"Last night" immediacy** | "Then last night…" (34.18), reused in the epilogue "Last night, my daughter…" (122.23) | It makes the story feel fresh and personal, and works as a bookend. |
| 13 | **Ticking clock (visual + verbal)** | The wall clock at 12 in nearly every bedroom shot (20-72 s), the clock close-up on "midnight" (38.8), "The castle is finished tonight" (50.90) | Constant pressure without saying "hurry". |
| 14 | **Routine break** | "But at midnight, it wasn't just Fern at my window." (38.74) | "every single time" and "like always" set up a pattern so the break is felt. This is the only "But" in the script. |
| 15 | **Sensory triple** | "glowing, buzzing, lighting up my whole room" (40.82) | Three stacked sense words, each a caption pop, and the spectacle grows with each. |
| 16 | **Authority figure with a signature prop** | "a fairy with a crown made of a tiny silver tooth. The fairy queen." (44.18-47.22) | A memorable visual detail tied to the world rule (teeth). |
| 17 | **Twist in dialogue that makes the hero central** | "Your tooth," she said, "is the last brick." (48.10) | An ordinary object becomes the most important thing in the world, and the viewer's stand-in holds it. |
| 18 | **Reaction beat** | "I froze." (50.34) | It gives the viewer a beat to feel the twist, at two words. |
| 19 | **One-word exchange** | "Home?" / "Up." (54.02 / 55.30) | Maximum tension from minimum words. Each is its own caption and its own shot. |
| 20 | **Journey list over cut-per-noun visuals** | "Past the mountain, past the moon, at the stars." (55.63) | It is literally an upward camera journey in three shots: nebula, moon, stars. |
| 21 | **Re-framing reveal** | "The castle is a ship." (57.87) | It reinterprets everything the viewer has seen for a minute. It is the purest "aha" line in the short. |
| 22 | **Agency through the rule** | "I pulled the tooth out… squeezed it in my fist." (61.23) | The hero uses the world rule against the most powerful being in it. |
| 23 | **Shrinking stakes (anaphora)** | "No more coins. No more drawings. No more Fern." (66.51-68.43) | It goes from the world to objects to one beloved person. The smallest stake is the biggest. |
| 24 | **Rule paid word for word** | "The queen didn't move. She couldn't. A fairy can never take a tooth out of your hand." (68.99-72.03) | The viewer gets the pleasure of a rule they remember turning out to matter. |
| 25 | **De-escalation as a twist** | "Take your time," she said softly. (72.43) | The expected villain is kind. The conflict moves inside the hero, so it becomes a moral choice. |
| 26 | **Isolation of the helper** | "All except Fern." (76.51) | Three words separate her from the crowd, and the camera follows: Fern alone on the window sill. |
| 27 | **Body-language emotion instead of dialogue** | "Her wings were drooping. Thin, tired, ten thousand years tired." (78.67-81.60) | It re-uses the scale number as weariness. Fern never speaks, which makes her more moving. |
| 28 | **Silent request** | "She tapped the lid. I opened it." (82.08-82.88) | The helper asks without words. The viewer leans in. |
| 29 | **List repeated and extended (the reveal hides in the new items)** | "A star, a tower, a little door, a window, a family waving." (87.44) | The familiar three items, then two new ones that carry the meaning. |
| 30 | **Puzzle-assembly reveal** | "And when I pushed them all together, they made one picture." (90.56-96.64) | A visual payoff the camera can show from the top: the cards slide into one image. |
| 31 | **Structural rhyme of the "not just X" engine** | "don't just collect your teeth, they're building…" (0.08); "it wasn't just Fern…" (38.74); "she wasn't just leaving me drawings. She was telling me where she wanted to go." (97.04) | The same reveal sentence shape opens the world, the first twist and the emotional twist. |
| 32 | **Emotional sacrifice** | "I looked at Fern, then at the tooth in my hand, and I opened my fist." (100.87) | The choice is made with an action, not a speech. It pays "It has to be given." |
| 33 | **Travelling sentence** | "over the houses, over the trees, all the way to the top of the mountain" (103.99) | One 28-word sentence for one continuous flight. It changes the rhythm before the click. |
| 34 | **Onomatopoeia as its own beat** | "Click. The last brick." (109.59-109.99) | A tiny sound for a huge moment. It also gives the sound designer a hit point. |
| 35 | **Spectacle payoff of an early image** | "turned night into day… flew up into the stars" (110.79-118.39) | It pays "glowing white" and "nobody knows what happens when it's done". |
| 36 | **Diminishing final image** | "I watched until it was just one tiny light." (119.03) | A quiet, bittersweet full stop before the epilogue. It leaves room for an ending. |
| 37 | **Time jump / narrator reveal** | "That was 20 years ago." (121.03) | It turns the kid story into a memory, and "20" mirrors tooth number 20. |
| 38 | **Generational mirror** | "Last night, my daughter lost her first tooth. She put it under her pillow." (122.23-124.23) | Last becomes first, and father becomes daughter. It invites parents to share it. |
| 39 | **Callback cliffhanger that contradicts a promise** | "there was a gold coin and a tiny…" (125.27), set against "no more tooth fairies, ever" (64.03) | The final line re-opens the story with an impossible object. |
| 40 | **Visual foreshadowing in set dressing** | Glow-in-the-dark stars on the bedroom ceiling (from 24 s), a "TO THE STARS" rocket poster (glimpsed at 43.4, clear at 70.5-72.4), a "SPACE" planets poster (46.2, 78.6-80.7) | The kid's room already hints that "home" is in the stars, and repeat viewers can spot it. |
| 41 | **Unspoken visual callback** | The assembled picture framed on the adult's wall (121.2) | It shows he kept it for 20 years without spending a word. |
| 42 | **Cute-creepy contrast** | Fern's zombie-ish red-eyed face plays the most tender role, and the goblin Queen is gentle | It subverts the visual threat cue, which is a mini-misdirection in itself. |
| 43 | **Caption-built sentences** | Fragments that are a single caption: "A castle." "Number 20." "The fairy queen." "I froze." "Home?" "Up." "She couldn't." "All except Fern." "Click." The big nouns land as one-word captions over their own insert shot ("moon", "coins", "Fern", "10,000"). | Every 0.2-0.3 s a word pops, and every 1.2 s a shot changes. Numbers are shown as digits ("No. 20", "10,000", "19") so they read in one glance. |

**Captions on screen.** One word at a time, white bold sans with a black outline, in the lower-centre (about 72-75% down the frame). Numbers appear as digits. The captions contain mistakes ("everyone", "fern"), so the captions in the original are probably auto-generated.

---

## 5. How it probably continues (GUESS, inferred from the setup)

**This is a guess, not observed.** At the cut (128.03) the story is already in its epilogue. The last frame shows the gold coin and a **purple** card, not the white or pink cards Fern used. The card has stars and a small winged figure (light-green head, pink body, white wings) half under the pillow. The missing word is almost certainly "drawing".

Most likely shape of the ending, about 10-30 s more:

1. **The drawing is shown and named** (about 128-133 s). It is probably a fairy (Fern) on a starry background: the first message "from home". The purple, starry card says "sent from the stars" visually.
2. **Meaning beat** (about 133-145 s). The setup allows three readings:
   - **A (most likely, about 55%).** Fern did not forget. She is keeping the tradition from her faraway star (or comes back for this one child). This pays off "the same fairy came" and the coin/drawing chain, and contradicts "no more tooth fairies, ever" in the warmest way. The daughter's drawings might start a **new picture**, which would be the next generation's mystery, mirroring the first half.
   - **B (about 30%).** A human twist: the narrator, now a father, left the coin and drew the card to keep Fern's magic alive. This is supported by the different card colour and drawing style.
   - **C (about 15%).** A darker or bigger loop: "every baby tooth ever lost becomes one brick" starts again, so the daughter's first tooth is the first brick of a new castle (a return trip, or a new colony).
3. **Final image**, probably a quiet callback: the adult at the window looking at the sky, maybe "one tiny light" blinking back. It could also be a final line that echoes "she was telling me where she wanted to go", now addressed to the daughter.

If the original really ran 1-2 minutes longer (as the trim note says), the extra time would most likely go to a **second, shorter cycle with the daughter**: new drawings, a new picture, a return visit. That would repeat the plant-and-payoff engine once more.

---

## 6. Why it works, and where it is weak

### Retention
- **Every early line is a promise with a fast first payment.** "building something with them" pays in 1.1 s. "nobody knows what happens when it's done" holds as the spine. "There's only one rule" signals that the rule will matter.
- **A clock under the whole middle.** It counts teeth (19, then 20, then "last"), uses the midnight clock in every bedroom shot, and says "finished tonight".
- **Dense turns after the first twist:** a new turn every 7 s on average from 38.7 to 125.3.
- **About 57 new facts in 125 s** (median 2.1 s apart) and a mean shot of 1.24 s, so the eye and ear never run out of new input.
- **The cliffhanger cut contradicts an earlier promise.** That is stronger than a plain "and then…".

### Emotion
- **Personal stakes beat world stakes.** "No more Fern" lands harder than "no more tooth fairies".
- **The helper never speaks.** Drooping wings, a tapped lid and drawings do the asking, so the viewer fills in the feeling.
- **The emotional twist is earned.** The drawings were planted at 27-34 s and pay at 90-99 s. Re-framing six years of gifts as a homesick message is the peak (97-104 s).
- **Sacrifice by gesture:** "I opened my fist."
- **Bittersweet release:** a huge spectacle, then "just one tiny light", then the generational warmth.

### Shareability
- It is **universal**: everyone lost baby teeth, and every parent has played tooth fairy.
- It is **wholesome but weird**: cute-creepy creatures in a tender story, so it is safe to share with kids and family.
- **Quotable re-frames:** "The castle is a ship." "She was telling me where she wanted to go."
- The **generational ending** invites "this made me cry" and "show this to your kid" comments.
- The **set-dressing Easter eggs** (TO THE STARS poster, ceiling stars) reward rewatches.

### Weak spots
- **The twist is late.** The first twist is at 38.7 s and the main twist at 48-50 s. At 30 s the script is still in backstory and plant (21-34 s is the softest stretch). The "Then last night" hook at 34.2 rescues it, but the notes' "twist at ~30 s" is not met.
- **The consequence step is thin.** No society reacts to the rule: no laws, no habits, no conflict. It works because the myth is pre-loaded, but a fully new rule of ours would need a real consequence block.
- **Low-danger rule.** It runs on wonder and melancholy, not threat. It carries no fear-driven retention like r1's "it takes you".
- **Logic holes.**
  - Why is this kid's tooth the last of every tooth in history?
  - Why does "take your time" fit with "finished tonight"?
  - "Then last night" (34.18) and "I've lost 19" read as present-day, and are then retconned by "That was 20 years ago". It is effective misdirection, but technically contradictory.
  - "I stayed up to meet her when I was six" against "For six years" is slightly confusing.
- **Breathless read.** At 261-271 wpm there are no pauses of 0.6 s or more, even on "I froze." and "She couldn't.". The quietest beats get no room. A human narrator will need either fewer words or a sped-up take (see Numbers).
- **Word repetition:** "tiny" ×6 and "tooth" ×12 slightly flatten the descriptions.
- **Caption errors** ("everyone", "fern") and the possible missing first second of picture are polish issues.
- **The dilemma resolves without a cost to the hero beyond loss.** No one opposes him, so the middle relies on emotion, not conflict.

### Mechanics worth reusing (structure only; invent our own content)
- **Rule:** open with "In this world, [familiar thing] doesn't just [known behaviour], it [hidden purpose]." Hold the key noun back one beat.
- **Rule within the rule:** add a **two-part** "only one rule" early. The first part becomes the lock of the climax, the second part the key.
- **Plant:** make a small, repeated **object gift** (with a list of 3 concrete items) look like flavour around 25-35 s. Pay it at about 70-75% of the runtime by **repeating the list and adding the new items that carry the meaning.**
- **Clock:** count up to "the last one" (a number the viewer can track). Keep a visual clock in the room.
- **Twists:**
  - Use the same "not just X, it's Y" sentence shape for the opening, the first twist and the emotional re-frame.
  - Give the authority figure a single re-framing line ("The castle is a ship."-style).
  - Make the conflict internal with a gentle antagonist.
- **Ending:**
  - Go from spectacle to "one tiny light", then a time jump.
  - Mirror the start in the next generation (last becomes first).
  - Cut on a callback that contradicts an earlier "never again".
- **Fixes to make in ours:**
  - Land the first real twist by about 30 s. This story could move "it wasn't just Fern" earlier by trimming the backstory.
  - Give the society/consequence block at least 2-3 lines that show people living with the rule.
  - Leave 2-3 real pauses (0.6-1.0 s) on the reaction and sacrifice beats.
  - Keep the read at a pace a human can act: about 420-480 words for 2:00-2:30.
