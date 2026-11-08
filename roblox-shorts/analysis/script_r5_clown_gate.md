# Script analysis: r5 "Clown Gate"

Reference only. The lines are quoted here so we can analyse them. Do not reuse them, the characters, the rule or the plot. We borrow the mechanics, not the content.

- Source: `ref/r5_clown_gate.mp4` (720x1278, 30 fps, 113.03 s, trimmed so the ending is missing). Inputs: ASR segments and word times (`asr/r5_clown_gate.txt/.json`), both frame sheets, two extra odd-second contact sheets, about 110 exact `ffmpeg -ss` frames at doubtful words and story beats, a shot-change scan and an audio-level check (all in `scratchpad/rbx/work/r5script/`).
- **Timing caveats.**
  - In our copy the **video stream starts at 2.27 s** and the audio starts at 0.00. We cannot see the picture under the first spoken sentence ("In this town, there's a sign at the only road out."). Players hold the first available frame: a low-angle wide of the wooden clown in grey-green fog, with the caption "you" already on screen. Whether the original had a title card or text in 0.0-2.27 s is unknown.
  - The frame-sheet labels run about **0.9 s early** compared with the audio. The sheet says "0:12 90" when "90" is at 13.04, and "0:02 wooden" when "wooden" is at 2.88. All times below come from the word timings and from exact `-ss` frames.
  - Audio: a music/SFX bed runs under everything (about -25 dB even in the only real pause, 22.8-24.0 s). There is no silence.
- **Format.** One narrator, a kid, the hero. The first 26 s are communal lore in the present tense ("People still try."). A narrator is first hinted at with "next door" (26.3). First person starts with "My grandpa" (30.88) and switches to past tense with "I found him" (49.51). The only quoted speaker is **Dad**, with two lines. The sign's text is quoted twice and works as the clown's "voice".
- **Cast on screen.**
  - The clown (the creature): a wooden cut-out clown statue. It has a blue hat, orange pom-pom hair, a red ball nose, round "glasses" eyes **whose pupils already look down in the first frame** (a fair-play clue), jagged splinter teeth, a polka-dot suit and striped legs. One arm holds a striped boom barrier over a farm gate. The plank reads "YOU MUST BE THIS TALL TO LEAVE" in red.
  - The hero: a kid in a green three-eyed-alien hood, the same avatar look as r4's hero. His face decal changes per beat.
  - Dad: balding, with a mustache, a brown vest and white sleeves.
  - Grandpa: white hair, a mustache and a navy blazer.
  - Mrs. Pell: a knee-high old lady in a pink cardigan with red glasses. She is planted in the crowd shot at 10-12 s before she is named.
  - Townsfolk: a red-haired man in a tan coat (the demo "failure"), a man in a flat cap with suspenders, and a girl with earmuffs.
- **Colour script follows the clock.**
  - 0-74 s: grey-green fog by day. The barn interior is warm wood.
  - 74-91 s: orange sunset.
  - 91-113 s: blue-purple dusk, then night with stars.

### ASR corrections (checked against the burned-in captions)

| t (s) | ASR | Corrected | Evidence |
|---|---|---|---|
| 20.76/20.84 | "facing town." / "one inch shorter." (segment break) | "...facing town, one inch shorter." | It is one sentence. The ASR segment boundary split it. The punishment is end-weighted onto the last three words. |
| 13.04, 89.04 | "90" / "ninety" | ninety | The caption shows the digits **"90"** (13.1). |
| 27.12 | "forty one" | forty-one | The caption shows **"41"** over a wall of tally marks. |
| 34.96 | "nineteen thirty four" | 1934 | The caption shows **"1934"** over the year carved at the bottom of the wall. |
| 39.99-41.19 | "6 feet, 5'11, 5'10" | "Six feet, five-eleven, five-ten." | The captions split the numbers: "feet", "5", "11", "5"... The pictures are close-ups of the 6'0", 5'11" and 5'10" notches. |
| 46.55 | "5'2" | "five-two" | The caption shows "5", then "2". The wall shows a red **5'2"** notch. |
| 58.39-59.67 | "Splinters for teeth and his eyes." | "Splinters for teeth. And his eyes..." | It is a trailing beat that the next line picks up ("His eyes don't look at you."). |
| 61.91 | "looked" | **look** | The caption shows "look" (62.0). The present tense matches "don't look" and "never have". |
| 74.47-75.19 | "but at sunset the next night I dragged" | "But at sunset... / The next night, I dragged..." | Two sentences. The explanation is cut off and the next scene finishes it. |
| 112.82 | "The sun went" (end) | "The sun went—" (cut) | The video ends at 113.03, mid-sentence. The last frame is night: the kid has an open-mouthed shocked face, Dad stands beside him, and the town gate and red barn are visible behind them. |

The name "Mrs. Pell" is confirmed by the door plaque "THE PELLS" (26.1) and the caption "Pell".

---

## 1. Clean transcript, numbered, tagged, with picture

Tags: RULE / CONSEQUENCE / PERSON / ESCALATION / TWIST / REVEAL / EMOTION / CALLBACK / CLIFFHANGER / DIALOGUE / DESCRIPTION (plus PLANT where a detail pays off later).

| # | Start | Sentence | W | Tag | Picture (one line) |
|---|---|---|---|---|---|
| 1 | 0.00 | In this town, there's a sign at the only road out. | 11 | RULE (setup), trapped premise | Video missing until 2.27 s. The first frame is a low-angle wide of the wooden clown in fog, its arm on a gate barrier. |
| 2 | 2.32 | You see, it's a wooden clown. | 6 | DESCRIPTION | The same low angle, slow push-in. The pupils already point down (PLANT). |
| 3 | 3.68 | Big painted grin. | 3 | DESCRIPTION | Extreme close-up of the face: red ball nose, glasses eyes, jagged wooden teeth. |
| 4 | 4.80 | One arm stretched out flat. | 5 | DESCRIPTION (PLANT: the arm) | A striped boom barrier ending in a white-gloved hand. The sign hangs below. |
| 5 | 6.00 | And under the arm it says, "You must be this tall to leave." | 13 | RULE | The plank "YOU MUST BE THIS TALL TO LEAVE", red letters on wood. |
| 6 | 8.80 | The arm is seven feet off the ground. | 8 | RULE (number) | The flat-cap man in suspenders looks up at the arm, shocked "o" mouth. |
| 7 | 10.48 | Nobody in this town is seven feet tall. | 8 | RULE (impossibility) | Five townsfolk lined up before the gate. The tiny old lady in pink (Mrs. Pell) is already there (PLANT). |
| 8 | 12.16 | Nobody has left in ninety years. | 6 | CONSEQUENCE | Two men walk toward the gate from behind, fog beyond. Caption "90". |
| 9 | 13.76 | People still try. | 3 | CONSEQUENCE | The red-haired man in a tan coat, determined frown, village houses behind. |
| 10 | 14.56 | They walk up to the clown, stand under the arm, and walk through the gate into the fog. | 18 | CONSEQUENCE (ritual) | He walks under the arm into white fog. The red barn is behind. |
| 11 | 18.08 | A minute later, they come walking back out of the fog, facing town, one inch shorter. | 16 | CONSEQUENCE + TWIST (penalty) | A ghostly silhouette walks out of the fog. Close-up of his face, then he stands visibly shorter under the arm. |
| 12 | 21.84 | And every time somebody fails, the clown's arm goes up one inch. | 12 | ESCALATION (rule within the rule) | Push-in on the clown's face. A whoosh blur fills the only 1.2 s pause. The arm rises while the shrunk man looks up. |
| 13 | 25.68 | Mrs. Pell next door has tried forty-one times. | 9 | PERSON (side) | Mrs. Pell at her door ("THE PELLS", lanterns), then a wall of tally marks. Caption "41". |
| 14 | 28.16 | She's three feet tall now. | 5 | CONSEQUENCE | Mrs. Pell knee-high next to the hero. **First appearance of the narrator** (alien hood). |
| 15 | 29.28 | She still walks to the gate every Sunday. | 8 | EMOTION (stubborn hope) | Mrs. Pell striding down the village street. |
| 16 | 30.88 | My grandpa keeps a wall in his barn. | 8 | PERSON (family) | Grandpa in front of a wooden wall of height marks with names (HANK, ROSE). |
| 17 | 32.64 | Every kid in our family, measured every birthday since 1934. | 12 | DESCRIPTION (PLANT: the measuring motif) | A boy measured with a ruler on his head. Close-up of the carved "1934". |
| 18 | 36.00 | Most notches go up. | 4 | DESCRIPTION | Notches climbing past years 1996-2023. |
| 19 | 36.96 | My dad's notches go up until he turned twenty, then they start going down. | 14 | TWIST (personal reversal) | Dad's column (1964-1994) climbs, then the camera pans down past 5'4", 5'3" and a red 5'2". |
| 20 | 39.99 | Six feet, five-eleven, five-ten. | 6 | ESCALATION (countdown) | Close-ups of the 6'0", 5'11" and 5'10" notches. |
| 21 | 41.83 | Every year, on his birthday, he tries the clown. | 9 | PERSON | Dad under a stormy sky, village and church behind. |
| 22 | 44.07 | Every year, he comes back out of the fog a little smaller. | 12 | CONSEQUENCE | Dad walking out of the fog, ghosted. |
| 23 | 46.31 | He's five-two now. | 4 | ESCALATION | Dad sad-eyed in front of the wall, with the red 5'2" mark by his head. |
| 24 | 47.35 | I'm almost as tall as him. | 6 | EMOTION (role reversal) | Dad and the kid side by side in the barn, the same height. JUNE/SAM/TOMMY on the wall, a calendar pinned up. |
| 25 | 48.47 | Tomorrow is his birthday. | 4 | ESCALATION (ticking clock) | Calendar: NOVEMBER, 5 circled in red, "DAD'S BIRTHDAY". |
| 26 | 49.51 | I found him in the barn that night, staring at the wall. | 12 | EMOTION | The kid outside the house at dusk, then Dad in the barn. |
| 27 | 51.75 | "One more try," he said. | 5 | DIALOGUE (Dad) | Dad close-up, set jaw, angry brows. |
| 28 | 52.87 | "One of these years, it's gonna let me through." | 9 | DIALOGUE (Dad), EMOTION | Dad sad-eyed. The kid's green hood is in the foreground. |
| 29 | 54.39 | So I went to look at the clown myself. | 9 | PERSON (the tester acts) | The kid walks past the red barn. |
| 30 | 55.91 | Up close, he's worse. | 4 | DESCRIPTION | Clown from a low dutch angle. |
| 31 | 57.11 | Paint peeling off his face. | 5 | DESCRIPTION (sensory) | Extreme close-up of cracked face paint and nose. |
| 32 | 58.39 | Splinters for teeth. | 3 | DESCRIPTION (sensory) | Extreme close-up of the jagged wooden teeth. |
| 33 | 59.43 | And his eyes... | 3 | DESCRIPTION (suspense) | Close-up of the glasses eyes. |
| 34 | 60.07 | His eyes don't look at you. | 6 | REVEAL | Tilted clown, then an extreme close-up of one pupil. |
| 35 | 61.11 | They never have. | 3 | REVEAL | Extreme close-up of the eye. |
| 36 | 61.75 | They look down at the road. | 6 | REVEAL (clue) | Clown medium shot, then the clown's POV tilting down onto the dirt road. |
| 37 | 63.11 | I knelt down where he was staring. | 7 | PERSON | The kid kneels in the road. |
| 38 | 64.47 | Under the dirt, faded white lines painted on the road, like a ruler. | 13 | REVEAL | The kid brushes dirt away: white stripes marked 1 FT, 2 FT... |
| 39 | 67.67 | And way out at the end, a line marked seven feet. | 11 | REVEAL + CALLBACK (seven feet) | The camera tracks along the stripes to "6 FT... 7 FEET". |
| 40 | 70.31 | He's not measuring you. | 4 | TWIST | The kid's face, wide-eyed realisation. |
| 41 | 71.27 | He's measuring your shadow. | 4 | TWIST (main) | The kid's open-mouth shout. |
| 42 | 72.39 | At noon, your shadow is a puddle under your feet. | 10 | DESCRIPTION (explains) | Top-down: the kid on the ruler with a tiny shadow under him. |
| 43 | 74.47 | But at sunset... | 3 | ESCALATION (cut-off) | The kid at the gate in orange light, the sign behind. |
| 44 | 75.19 | The next night, I dragged my dad to the gate, right as the sun touched the hills. | 17 | ESCALATION (the test) | The kid pulls Dad by the arm past the red barn. The gate in an orange haze. |
| 45 | 78.47 | Our shadows stretched out across the road. | 7 | DESCRIPTION | Top-down: two figures with long shadows across the ruler lines. |
| 46 | 80.32 | Past five feet, past six, past the seven-foot line, way, way past it. | 14 | ESCALATION (triumph) | Shadows slide over 5 FT, 6 FT and 7 FEET. |
| 47 | 84.40 | We stepped through, into the fog. | 6 | ESCALATION | The kid, determined, then glowing orange fog. |
| 48 | 85.76 | I held his sleeve the whole way. | 7 | EMOTION | The kid glancing back, worried, in orange glow. |
| 49 | 87.12 | Ten steps, twenty... | 3 | ESCALATION (count) | Dad in the fog, worried. Captions "10", "20". |
| 50 | 88.16 | And for the first time in ninety years, nobody came walking back out. | 13 | CALLBACK + TWIST (first success) | The empty gate in orange fog. Two villagers wait in the street, shocked. |
| 51 | 91.20 | The fog cleared. | 3 | REVEAL | The kid in twilight. The palette turns blue-purple. |
| 52 | 92.08 | We were on a road we'd never seen. | 8 | REVEAL | Wide shot: the kid and Dad small on a misty road. |
| 53 | 93.60 | Trees on both sides. | 4 | DESCRIPTION | Trees and a dusk sky, the pair small. |
| 54 | 94.80 | Silent. | 1 | DESCRIPTION (absence) | The kid's sad close-up. |
| 55 | 95.36 | No birds. | 2 | DESCRIPTION (absence) | Glitch transition (RGB slice), then a view up the road. |
| 56 | 95.92 | The sun was almost gone. | 5 | ESCALATION (ticking clock) | Far up the road: clowns and an "8 FEET" plate in dusk light. |
| 57 | 97.04 | And a hundred feet up the road, there was another sign. | 11 | TWIST (win becomes trap) | Slow push toward the next clown. |
| 58 | 99.20 | Another clown. | 2 | TWIST | Clown medium shot. |
| 59 | 99.94 | Same peeling grin, same arm stretched out. | 7 | CALLBACK | Extreme close-up of the clown's face. |
| 60 | 102.50 | "You must be this tall to leave." | 7 | CALLBACK (rule text) | The same plank, plus a new plate: "8 FEET". |
| 61 | 104.18 | Eight feet. | 2 | ESCALATION | The "8 FEET" plate fills the frame. |
| 62 | 104.66 | And past that one, another: nine feet. | 7 | ESCALATION | The next clown with a "9 FEET" plate. |
| 63 | 106.58 | And another: ten, twelve, twenty. | 5 | ESCALATION (runaway) | More clowns with "10", "12 FEET" and "20" plates. |
| 64 | 108.42 | All the way down the road, as far as I could see, every single one staring at the ground. | 19 | REVEAL (infinite) + CALLBACK (the eyes) | A row of clowns receding into the dark, then an extreme close-up of a clown face staring. |
| 65 | 112.50 | The sun went— | 3 | CLIFFHANGER (trim) | Night with stars: the kid's open-mouth shock, Dad beside him, the town gate and barn behind them. |

Tag totals (primary tag): DESCRIPTION 14, ESCALATION 13, REVEAL 8, CONSEQUENCE 6, PERSON 5, TWIST 5, RULE 4, EMOTION 4, CALLBACK 3, DIALOGUE 2, CLIFFHANGER 1.

---

## 2. Beat map

| Block | Time | Share of 113 s | Job |
|---|---|---|---|
| A. Rule | 0.0-13.4 | 12% | An object, then the rule, then the impossibility, then "90 years". |
| B. Society | 13.8-30.5 | 15% | The ritual, the penalty, the rising bar, Mrs. Pell as living proof. |
| C. Family / stakes | 30.9-54.1 | 21% | The height wall, Dad shrinking, the role reversal, the birthday clock, Dad's line. |
| D. Investigation, then twist | 54.4-74.8 | 18% | The creepy close-up, the clue (eyes), the ruler, then "measuring your shadow". |
| E. Test, then success | 75.2-90.9 | 14% | Sunset, shadows past 7 ft, the sleeve, "nobody came walking back out". |
| F. New world, then escalation, then cut | 91.2-113.0 | 19% | A silent road, another clown, 8/9/10/12/20 ft, endless clowns, the sun goes down. |

Key moments:
- **The rule lands at 7.20-8.32 s**, on the words "You must be this tall to leave", quoted from the sign.
  - The impossibility is closed at **11.76 s** ("...seven feet **tall**").
  - The stakes arrive at **13.36 s** ("Nobody has left in ninety **years**").
  - The first sentence (0.0) is not the rule. It is a location plus a trapped premise ("the only road out"). The visual hook is the creature.
- **Consequence (society):**
  - 13.76: "People still try."
  - 18.08-21.44: the penalty, "one inch shorter".
  - 21.84-25.36: the bar rises.
  - 25.68-30.48: Mrs. Pell, 41 tries, three feet tall, every Sunday.
- **Meeting the one person:**
  - The narrator is hinted at 26.3 ("next door") and seen at 28.2 (next to Mrs. Pell).
  - The narrator is introduced in voice at **30.88** ("My grandpa...").
  - The personal stake (Dad) arrives at **36.96** ("My dad's notches").
  - The tester acts at **54.39** ("So I went to look at the clown myself.") and tests at **75.19** ("I dragged my dad to the gate").
- **Twists / reversals:**
  1. **21.44** "one inch shorter": failing costs your body, not just your time.
  2. **25.36** "arm goes up one inch": the goal moves away with every failure (rule within the rule).
  3. **39.60** "then they start going down": Dad is a victim. The chart flips. This is the "twist at about 30 s" slot, landing at 35% of runtime.
  4. **47.35-48.15** "I'm almost as tall as him": child overtakes parent (emotional reversal).
  5. **62.63** "They look down at the road": the creature has been looking somewhere else all along (clue).
  6. **70.31-71.91** "He's not measuring you, he's measuring your shadow": **the main twist**, at 63% of the trimmed runtime.
  7. **88.16-90.88** "for the first time in ninety years, nobody came walking back out": the ritual is reversed and the first success lands.
  8. **97.04-99.36** "another sign. Another clown.": the win becomes a trap. This is the "level 2" reveal.
  9. **104.18-112.18** 8, 9, 10, 12, 20 ft, "every single one staring at the ground": runaway escalation into infinity.
  10. **112.50** "The sun went—": the ticking clock runs out (cliffhanger at the trim).
- **Emotional peak:** 85.76-90.88. Holding Dad's sleeve, counting steps, the first exit in 90 years. Secondary peaks:
  - 46.31-54.07: the shrinking father, "I'm almost as tall as him", "One more try".
  - Dread peak at 108.4-112.2: endless clowns at nightfall.
- **Last beat before the trim:** 112.50-112.82, "The sun went". The video ends at 113.03 on a night shot of the shocked kid and Dad.

### Open loops (question opened, then paid)

| # | Opened | Question in the viewer's head | Paid |
|---|---|---|---|
| L1 | 0.0 "a sign at the only road out" | What does the sign say? | 7.2 (the sign's text) |
| L2 | 11.8 "Nobody... is seven feet tall" | Then how could anyone leave? | 71.9 (shadow), 90.9 (they pass) |
| L3 | 17.6 "into the fog" | What happens in there? | 21.4 (you come back shorter); what lies beyond is paid at 92-99 |
| L4 | 25.7 Mrs. Pell, 41 tries | Will she ever make it? | **Not paid** in the trimmed part |
| L5 | 30.9 "a wall in his barn" | Why a wall? | 32.6-39.6 (family heights, Dad shrinking) |
| L6 | 39.6 "start going down" | Why is Dad shrinking? | 41.8-45.9 (he tries every birthday) |
| L7 | 48.5 "Tomorrow is his birthday" | Will he shrink again? | 75.2 (they go the next night), 90.9 (they pass) |
| L8 | 52.9 "it's gonna let me through" | Will it? | 90.9 |
| L9 | 59.4 "And his eyes..." | What about the eyes? | 60.1-62.6 (they look down at the road) |
| L10 | 62.6 the road | What is on the road? | 64.5-69.9 (a ruler, a 7-ft line) |
| L11 | 69.9 a ruler on a road? | What is it measuring? | 70.3-71.9 (your shadow) |
| L12 | 74.5 "But at sunset..." | Then what? | 78.5-84.1 (shadows way past 7 ft) |
| L13 | 84.4 "into the fog" | What is on the other side? | 91.2-99.4 (a road nobody has seen, another clown) |
| L14 | 95.9 "The sun was almost gone" | What happens when it sets? | **Open at the trim** (112.5 "The sun went—") |
| L15 | 99.4 "Another clown" | How do they pass 8, 9... 20 ft? | **Open at the trim** |
| L16 | 47.4 "I'm almost as tall as him" | Is the kid next in line? | Partly: the kid leads. Generational payoff **open** |

At any moment from 7 s to the end there are 2-4 loops open. A loop is usually paid within 2-10 s and replaced by a new one before it closes (L9, then L10, then L11, then L12 run in a chain of about 3 s each, 59-75 s).

---

## 3. Numbers

- **Words:**
  - 480 spoken words in the corrected transcript (numbers expanded: "five-eleven" counts 2). The ASR has 477 tokens.
  - 65 sentences (split at full stops / read-aloud stops).
  - 131 words in the first 30 s.
- **Speed:** **~255 wpm overall** (480 / 113.03 s), and **~258 wpm while speaking**.
  - The voice is essentially continuous. Only **one** gap is longer than 0.65 s: 1.2 s after "fails" (22.80 to 24.00), filled with a push-in on the clown and SFX.
  - All other sentence gaps are 0.45-0.64 s.
  - Per 20-s window: 273, 234, 261, 273, 240, 226 wpm.
  - This is far above a natural reading pace (150-190 wpm). It is a sped-up or very tight delivery.
- **Sentence length:** median **6** words, mean 7.4, min 1 ("Silent."), max 19 (64).
  - 1-5 words: 26 sentences = **40%**.
  - 6-9 words: 22 = 34%.
  - 10-14 words: 13 = 20%.
  - 15+ words: 4 = 6% (10, 11, 44, 64). These are the action/ritual sentences and the final panorama.
- **Seconds per sentence:** mean 1.76, median 1.52. The longest stretches inside one sentence are 4.1 s (46 and 64) and 3.5 s (10).
- **Openers:**
  - "And" 8, "So" 1, "But" 1, "Then" 0. That is **10/65 = 15%**.
  - 5 of the 8 "And"s come after 88 s. They chain the escalating reveals ("And a hundred feet up...", "And past that one, another...", "And another...").
  - Other repeated openers: "The" 5, "Every" 3 (two are the "Every year..." pair), "He's" 3, "One" 3, "They" 3, "I" 3, "Nobody" 2 (back to back).
- **Narration person:**
  - **Third person/communal 0-26 s.** "Nobody" ×3, "People", "They" ×5, "somebody", "she/she's" 2.
  - **First person from 30.88.** "I" 6, "I'm" 1, "my" 3, "we" 2, "we'd" 1, "our" 2: 15 first-person tokens.
  - **Second person to the viewer:** 6 ("You see", "don't look at you", "not measuring you", "your shadow" ×2, "your feet"). The main twist is addressed to "you", plus 2 "you" in the sign's text.
  - he/he's/his/him: 18. Mixed between Dad and the clown ("he's worse", "where he was staring", "He's not measuring you").
- **Tense:** present tense for the world and the family facts (0-48.5). It switches to past tense for the story at 49.51 ("I found him...").
- **Dialogue:** 2 lines, both **Dad**: "One more try," (51.75) and "One of these years, it's gonna let me through." (52.87). That is 14 words = **2.9%**. The sign's text is quoted twice (7.20, 102.50), 14 words = 2.9%. Total quoted: under 6%. The hero never speaks aloud.
- **New information:** 60 of 65 sentences add a new fact or image. The exceptions are "And his eyes...", "They never have.", "But at sunset..." (set-ups) and the two callbacks 59-60. So **one new fact about every 1.9 s**.
  - Visual cuts: about **70 shot changes** in 110.8 s of picture, **one every 1.6 s** (median 1.3 s).
  - **50 of 65 sentences start on a cut** (cut on the first word).
  - The longest held shots: 16.5-21.8 (the walk into and out of the fog), 37.0-41.8 (a pan down the notch wall), 41.8-46.4, and 95.9-99.9 (a push toward the second clown).
- **Repeated words and phrases:**
  - "feet" 10, "road" 7, "every" 7, "arm" 6, "clown" 5, "tall" 5, "fog" 5, "past" 5, "way" 5, "seven" 4, "down" 4, "another" 4, "staring" 3, "sun" 3, "birthday" 3, "nobody" 3.
  - Phrases:
    - "You must be this tall to leave" ×2.
    - "seven feet" ×3 + "seven-foot" ×1.
    - "(walking/comes) back out (of the fog)" ×3: 18.96, 44.63, 90.40.
    - "ninety years" ×2 (13.04, 89.04).
    - "arm stretched out" ×2 (4.96, 101.46).
    - "peeling" ×2 (57.43, 100.26).
    - "staring" ×3 (Dad at the wall 50.79, the clown at the road 63.99, every clown at the ground 111.62).
    - "Every year" ×2.
    - "Nobody..." ×2 back to back.
    - "past" ×4 in one sentence.
- **Numbers and specific details (spoken):**
  - seven feet; ninety years ×2; a minute later; one inch ×2; forty-one times; three feet tall; every Sunday; 1934; twenty (age).
  - Six feet / five-eleven / five-ten / five-two; tomorrow; that night; noon; sunset; the next night.
  - five feet / six / seven-foot line; ten steps, twenty; a hundred feet; eight, nine, ten, twelve, twenty feet.
  - About **27 number mentions in 113 s**, roughly one every 4 s.
- **Visual-only details (never spoken):**
  - Tally marks on Pell's wall.
  - Names on the height wall: HANK, ROSE, JUNE, SAM, TOMMY.
  - Years 1964-2023 on the notches.
  - The calendar "NOVEMBER 5, DAD'S BIRTHDAY".
  - Lanterns on the Pell porch.
  - "FT" stencils on the road.
  - Plates reading 8/9/10/12/20 FEET under each later clown.
  - These reward a rewatch and the pause button.

---

## 4. Devices (what keeps people watching)

1. **Object-first hook with a trapped premise.** "In this town, there's a sign at the only road out." (0.0). It does not open with an abstract "in this world". It opens with a place, a single exit and a mystery object. "Only road out" implies people want out.
2. **A familiar phrase made sinister.** "You must be this tall to leave." (7.20) reuses the funfair "you must be this tall to ride" template. Everyone understands it instantly, and the one swapped word ("leave") makes it a prison rule. This is the strongest single device in the script.
3. **Creature on the first frame.** The cute-creepy wooden clown fills the screen from the first visible frame, low angle, in fog. Its pupils already point down, a clue that is fair from second 2.
4. **Verbless noun fragments for word-by-word captions.** "Big painted grin. One arm stretched out flat." (3.68-5.68); "Paint peeling off his face. Splinters for teeth." (57.11-59.03); "Trees on both sides. Silent. No birds." (93.60-95.52). Each fragment is one image and one shot.
5. **Impossibility plus duration, as anaphora.** "Nobody in this town is seven feet tall. Nobody has left in ninety years." (10.48-13.36). Two "Nobody"s seal the trap.
6. **Three-word pivot into action.** "People still try." (13.76) turns a static rule into behaviour, and hope.
7. **Ritual in present tense, three verbs.** "They walk up..., stand under the arm, and walk through the gate into the fog." (14.56).
8. **End-weighted punishment.** "...facing town, one inch shorter." (18.08-21.44). The horror is held back to the last three words.
9. **Rule within the rule (a moving goal).** "And every time somebody fails, the clown's arm goes up one inch." (21.84). The only real pause sits mid-sentence, after "fails" (1.2 s), on a whoosh push-in to the clown's face.
10. **Side character as living proof, with numbers and pathos.** "Mrs. Pell next door has tried forty-one times. She's three feet tall now. She still walks to the gate every Sunday." (25.68-30.48). Tragicomic. Visually planted in the crowd shot at 10-12 s before she is named.
11. **The narrator slipped in sideways.** "next door" (26.3), then the hero appears on screen next to Mrs. Pell (28.2), then "My grandpa..." (30.88). Society narrows to the family, then to Dad.
12. **The cost shown as data on a physical object.** The barn height wall "since 1934" (30.88-41.19). "Most notches go up. My dad's notches go up until he turned twenty, then they start going down." The reversal is a graph the camera pans down.
13. **Countdown list.** "Six feet, five-eleven, five-ten." (39.99). It has the slowest cadence in the video (0.64 s gaps). Each number is its own caption and close-up.
14. **Anaphora "Every year..."** (41.83, 44.07). The repetition is itself the sad routine.
15. **Generational role reversal.** "He's five-two now. I'm almost as tall as him." (46.31-48.15). The child overtakes the shrinking parent. It is the emotional engine and a quiet generational clock.
16. **Ticking clocks, stacked.**
    - "Tomorrow is his birthday." (48.47)
    - "right as the sun touched the hills" (77.35)
    - "The sun was almost gone." (95.92)
    - "The sun went—" (112.50)
    - The colour script (grey, then orange, then blue-purple, then black) shows the clock visually.
17. **"That night" / "the next night" immediacy.** "I found him in the barn that night" (49.51); "The next night, I dragged my dad to the gate" (75.19). The tense shift to past marks "the story starts now".
18. **One line of dialogue as character.** "'One more try,' he said. 'One of these years, it's gonna let me through.'" (51.75-54.07). Denial and hope in 14 words. It is the only voice besides the narrator's.
19. **Protagonist agency with "So".** "So I went to look at the clown myself." (54.39). The kid acts where the adults gave up.
20. **Sensory close-up crescendo.** "Up close, he's worse." (55.91), then paint, then splinters, then eyes. The camera goes extreme close-up on each noun.
21. **Trailing beat plus repetition (anadiplosis).** "And his eyes... His eyes don't look at you. They never have." (59.43-61.43). "They never have" adds 90 years of uncanny history in three words.
22. **Plant and payoff of the eyes and staring.**
    - The pupils point down in the first frame (2.3), then "They look down at the road" (61.75).
    - The "staring" motif: Dad staring at the wall (50.79), the clown "where he was staring" (63.99), every clown "staring at the ground" (111.62).
    - The "measuring" plant: the family wall (32.64) pays off as the ruler on the road (64.47).
23. **Misdirection by the rule's own wording.** The first minute frames everything as **height**: "this tall", "seven feet", notches, inches. The solution is a **shadow**. The sign's arm is a decoy; the real measure is on the ground.
24. **The main twist as a "not X, but Y" chiasmus.** "He's not measuring you. He's measuring your shadow." (70.31-71.91). 8 words, two halves, quotable, and addressed to "you".
25. **Explaining in one concrete image.** "At noon, your shadow is a puddle under your feet." (72.39).
26. **Cut-off explanation plus a time jump.** "But at sunset..." (74.47). The sentence is never finished in words; the next scene ("The next night...") finishes it visually. This saves 5-8 s of explanation.
27. **Triumph through accelerating anaphora.** "Past five feet, past six, past the seven-foot line, way, way past it." (80.32-84.08). Top-down shots of the shadows crossing the stencils.
28. **Physical intimacy detail.** "I held his sleeve the whole way." (85.76). Love shown, not said, and the child leading the parent.
29. **Count-up suspense.** "Ten steps, twenty..." (87.12).
30. **Callback that reverses the ritual.** "And for the first time in ninety years, nobody came walking back out." (88.16). It reuses "ninety years" (13.04) and "walking back out" (18.96) and cuts to the waiting villagers (the shrunk red-haired man) looking stunned.
31. **Absence as dread.** "Silent. No birds." (94.80-95.52), with a glitch transition on "birds".
32. **Win becomes trap (structural repeat).** "And a hundred feet up the road, there was another sign. Another clown. Same peeling grin, same arm stretched out. 'You must be this tall to leave.'" (97.04-103.62). This is a verbatim callback of the rule.
33. **Runaway escalation ladder.** "Eight feet... nine feet... ten, twelve, twenty" (104.18-107.94). The steps grow (+1, +1, +2, +8) and the delivery speeds up.
34. **Infinity image tied to the mechanism.** "All the way down the road, as far as I could see, every single one staring at the ground." (108.42). "Staring at the ground" means they all measure shadows, and night is falling.
35. **Cliffhanger on the clock.** "The sun went—" (112.50). With no sun there is no shadow, so the solution just stopped working.
36. **Second person to make the twist personal.** "You see" (2.32), "don't look at you" (60.07), "not measuring you... your shadow" (70.31), "your feet" (72.39). The viewer is the one who was fooled.
37. **Captions built for one-word display.**
    - One white bold word, centre screen.
    - Every number is shown as digits ("90", "7", "41", "1934", "5"/"11", "10", "20", "100").
    - Key nouns land on matching shots: "1934" on the carved year, "tomorrow"/"birthday" on the calendar, "fails" on the clown's face, "41" on the tallies.
    - 74% of sentences are 9 words or fewer, and most words are monosyllables.
38. **Picture literally illustrates each sentence.** About 71% of cuts fall on a sentence start, and each new noun brings a new shot (one shot per sentence or per fragment).
39. **Universal family roles, one name.** Only Mrs. Pell is named. Grandpa, Dad and "I" are roles, so anyone can project themselves.

---

## 5. How it probably continues (GUESS, inferred from the setup)

The brief says 1-2 minutes are cut, so the full video is probably about 2:50-3:50. The trimmed part ends on "The sun went—" with night falling, the pair just past the first gate, and an endless row of clowns from 8 to 20+ ft ahead.

- **Most likely next beat (guess):**
  - "...down." Darkness means no shadows, so they are stuck in the no-man's-land between the first clown and the second.
  - Going back probably costs height. Going forward is impossible without a long shadow.
  - Expect a night beat of fear (the clowns may seem to move or watch, fog closing in), then a second clever use of the same mechanic. Candidates:
    - Sunrise also gives long shadows.
    - A low light source makes a huge shadow. The Pell porch lanterns were visible at 26 s, a possible plant.
    - Moonlight.
- **Possible bigger reveal (guess):**
  - The inches taken from people who failed are what raise the arms or build the taller clowns (it would pay off "the arm goes up one inch").
  - Or the road loops back to the same town. The final frame oddly shows the town gate and red barn right behind them.
- **Likely emotional ending (guess):** the format here builds a generational payoff ("since 1934", "I'm almost as tall as him", the sleeve). The likely shapes are:
  - Dad cannot go on and pushes the kid forward (sacrifice).
  - Or they return and give the town the sunset secret: Mrs. Pell finally walks through, paying off the open loop L4.
  - Or a time-jump epilogue: the narrator, grown, keeps his own wall where every notch goes up.
- **The final line probably echoes the rule** ("this tall", "leave", "shadow") with a reversed meaning. The video likely ends on a close-up of a clown face, since the clown's face is the bookend image at 0-4 s and 111-112 s.

---

## 6. Why it works, and where it is weak

### Retention
- The rule is a **familiar phrase with one word swapped**, readable in one second and creepy on contact.
- **Constant new information:**
  - a new fact every about 1.9 s;
  - a new shot every about 1.6 s;
  - a number every about 4 s.
- **Chained open loops** (always 2-4 open). Clue, then a new question, then a clue, every about 3 s through the investigation (59-75 s).
- **Many small reversals instead of one big twist**: 21, 25, 39, 47, 62, 71, 90, 99, 108, 112 s. The story turns roughly every 10 s after the setup.
- The **ticking clock is visible** (sky colour) as well as spoken.
- The near-continuous VO (one 1.2 s pause) leaves no dead air.

### Emotion
- The shrinking father seen through his child: "He's five-two now. I'm almost as tall as him." An unusual, very visual sadness.
- Dad's hope line ("One more try"), and the kid holding his sleeve.
- **Catharsis, then instant dread**: first exit in 90 years (88-91 s), then another clown (97-99 s), then infinite clowns at nightfall (108-113 s). The emotional high is deliberately undercut.

### Shareability
- A puzzle with an "aha" solution ("He's measuring your shadow"). It is quotable and makes viewers feel clever.
- **Built-in comment bait.** "Why did nobody try at sunset in 90 years?", "How do you pass 20 ft?", and "the arm goes up an inch each time, so how is it still 7 ft?" Logic debates drive comments.
- Universal fear imagery (clowns, fog, being trapped) plus a family story. Safe for all ages.

### Weak spots
- **The rule lands at 7.2 s, not on the first frame**, and the impossibility at 11.8 s. The first spoken line is setup, plus filler ("You see," at 2.32). In our copy the first 2.27 s of picture are missing, so an on-screen rule text cannot be confirmed.
- **Logic holes:**
  - 90 years and nobody tried at sunset by chance (Mrs. Pell goes every Sunday).
  - The arm rises an inch per failure, yet "the arm is seven feet" and the road line is a fixed 7 ft. The rising-arm mechanic is dropped after 25 s.
  - Mrs. Pell lost 41 inches to reach 3 ft, so she started at about 6'5".
  - The kid solves in one visit what the whole town missed (a convenient clue).
- **Pronoun ambiguity:** "he" switches between Dad and the clown ("he's worse", "where he was staring", "He's not measuring you"). It is clear on screen, muddy by ear.
- **The main twist is late** (71 s, 63% of the trimmed runtime). The "twist at about 30 s" slot is filled by smaller turns (Mrs. Pell, then Dad's notches at 39.6 s), which work but are softer.
- **Picture and line mismatches:**
  - "ten" is captioned over a "12 FEET" plate (107.1-107.6).
  - The notch wall shows years and heights that differ from the spoken sequence at 39.9.
- **The pace is very fast** (about 255 wpm). Fine for TTS or speed-up, but hard for a human voice actor without cutting words.
- **Thin interiority:** the hero has no name and no line of his own. Dad's despair is told in two lines. The Mrs. Pell loop is left hanging in the trimmed part.

### Mechanics worth reusing (structure only; invent our own content)
- Open on a **single concrete object** that embodies the rule. Quote the rule as **text written on it**. A familiar everyday phrase with one word changed works best.
- State the impossibility and its duration in two short anaphoric lines. Then "people still try" turns the rule into behaviour.
- Give the rule a **cost per attempt** and a **moving goal**, revealed as end-weighted punchlines.
- Show society's cost through **one side character with a number** (tries, size, routine).
- Narrow to the family through a **physical archive** (a wall, a log, a jar). Let the data reverse ("go up, then go down").
- Put the parent in danger and the child closer to the edge ("almost as tall as him"). Add a dated deadline ("tomorrow").
- The investigation is a ladder of 3-second clue/question beats ending in a **"not X, but Y" twist** addressed to "you".
- Leave the explanation unfinished ("But at...") and jump straight to the test.
- Success via a **callback** that reverses the opening ritual. Then **immediately** reveal the next, bigger version of the rule. End on the clock running out.
- **For our VO (the owner records it):** at a natural 170-190 wpm a 2:00-2:30 short holds about 380-470 words. To match this reference's density (about 255 wpm) the edit would need about 1.3x speed-up, or we write fewer, denser words.
  - Keep the median sentence at about 6 words, 40% at 1-5 words, numbers spoken as digits-friendly words, and one deliberate pause per minute on a visual sting.
  - Emphasis words fall at sentence ends: "shorter", "tall", "shadow", "out", "clown". Write the key word last so the performer can land it.
