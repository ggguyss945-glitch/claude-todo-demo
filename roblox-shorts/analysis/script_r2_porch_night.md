# Script analysis: r2 "Porch Night" (reference, trimmed at 2:37)

Source: `ref/r2_porch_night.mp4` (720x1280, 30 fps). The audio runs 0.00 to 157.01 s. The **video track starts at 1.50 s**, so the first 1.5 s of picture are missing from this file (players hold the first frame). The last word ("step.") starts at 156.63 s and the file ends at 157.03 s, exactly on a cut. Everything after that is trimmed.

Method: I took the ASR words with start times (`asr/r2_porch_night.json`, 702 words) and checked **every word** against the burned-in captions (10 fps caption-band crops, one cell per word), plus one frame per sentence and extra frames at key beats. The ASR matches the captions word for word. Corrections:
- "the fisher boy" is **"the Fisher boy"**: the caption capitalizes it, so it is a family name, not a job.
- Captions write "Mrs" without the period, "3" as a numeral (for "three times") and "Porch Night" capitalized as a proper noun (24.0 s and 94.6 s).
- The second "Open the door!" (133.67 s) is in **ALL CAPS**, so it is shouted.

Caption style: one word at a time, bold white with a black outline, low centre (about y=900 of 1280). **Dialogue is colour-coded by speaker and has no quote marks:**

| Speaker | Caption colour |
|---|---|
| Narrator | white |
| Dad | light blue |
| Mom | pink |
| Grandpa | yellow |
| Townspeople | orange |

A crude pitch check suggests one voice performs every role. Character lines sit higher and louder than the narration (narration about 170-190 Hz median F0, dialogue about 220-240 Hz, the "One for the porch!" taunt about 320 Hz).

Quotes below are for analysis only. Do not reuse any of them.

---

## 1. Corrected transcript: 84 sentences, start times, tags, picture

Tags: RULE / CONSEQUENCE (society) / PERSON / ESCALATION / TWIST / REVEAL / EMOTION / CALLBACK / CLIFFHANGER / DIALOGUE (speaker) / DESCRIPTION. PLANT marks a set-up that pays off later.

| # | Start | Sentence | Tag(s) | Picture at that moment |
|---|---|---|---|---|
| 1 | 0.00 | In this town, one night a year, every family has to leave one person outside, and in the morning, every porch is empty. | RULE + mystery | Old person in a rocking chair on a lit porch, scared face (first visible frame, 1.5 s). Cut at 3.5 s to an empty street of houses in morning light. |
| 2 | 5.47 | It comes out of the cornfields at midnight, a scarecrow taller than the streetlights, straw hanging out of its sleeves, and a sack for a head, with a big smile stitched across it. | DESCRIPTION (creature) | Scarecrow full-body against a starry sky. One cut per noun: straw sleeve 8.7, sack head 10.3, stitched smile 11.3. |
| 3 | 13.15 | It walks so slowly you can hear the straw creak with every step. | DESCRIPTION (sound), PLANT | Reaction shot: two people peeking out through a window, with a rocking chair in the foreground. |
| 4 | 16.11 | It goes porch to porch, it bends all the way down, until its face is right in front of yours, and then the stitches rip open. | DESCRIPTION, ESCALATION (2nd person) | Scarecrow walking between houses, then bending to a person in a porch chair, its face filling the frame. |
| 5 | 22.32 | Wider than its whole head. | REVEAL (horror image) | The mouth rips open huge over the seated victim. |
| 6 | 23.52 | We call it porch night. | DESCRIPTION (title drop) | Empty street with lamp posts at dusk. Caption reads "Porch" / "Night". |
| 7 | 24.64 | Every house in town has one chair on the porch, just one. | CONSEQUENCE | A house with a single porch chair. |
| 8 | 27.28 | Nobody sits in it the rest of the year. | CONSEQUENCE | Neighbours walk past an empty rocking chair in daylight. |
| 9 | 28.80 | And there's only one rule. | RULE (rule-within-the-rule) | Old man in a rocking chair on a porch, stern. |
| 10 | 30.16 | Somebody has to be in that chair. | RULE | Old woman in a chair behind the porch railing, frightened. |
| 11 | 31.68 | The year I was born, the Harpers locked their whole family inside. | CONSEQUENCE (proof), first "I" | The Harper family huddled indoors by their door. |
| 12 | 34.72 | In the morning, their door was still locked and the house was empty. | REVEAL (locked-room), PLANT | A locked door with a lantern; an empty interior. |
| 13 | 37.60 | So every family chooses. | CONSEQUENCE | A family on its front path, grandmother with a bag. |
| 14 | 38.88 | Old people go first. | CONSEQUENCE, PLANT | Lamp post on a dusk street. |
| 15 | 39.92 | That's just what you do when you get old here. | CONSEQUENCE (2nd person) | Old woman sitting serenely on a porch. |
| 16 | 41.44 | Rich families pay. | CONSEQUENCE | Rich man in a suit and bowler hat holding cash. |
| 17 | 42.37 | Mr. Wendell pays a kid from the bottom of the hill to sit on his porch, a new kid every year. | CONSEQUENCE, PLANT (Wendell) | Top-hat man handing money to a poor mother; kid in overalls on his porch. |
| 18 | 46.29 | Some families have one more kid than they wanted, and people say it like a joke. | CONSEQUENCE | A family with several kids walking down the street. |
| 19 | 49.25 | One for the porch! | DIALOGUE (townspeople, orange) | Two neighbours chatting on the sidewalk, a child behind them. |
| 20 | 50.21 | And some families tie the person to the chair so they can't knock because everyone knocks. | CONSEQUENCE, PLANT (tied, knocking) | A person roped to a porch chair. |
| 21 | 54.13 | Every year, you hear it all the way down the street, knocking, begging, and nobody opens. | CONSEQUENCE, PLANT ("nobody opens") | Night street, then someone pounding on a front door. |
| 22 | 58.45 | Last year, it was Grandpa. | PERSON (tense switches to past) | Narrator boy (yellow hair, black-and-yellow striped shirt) from behind, Grandpa on the porch. |
| 23 | 59.65 | He stood up at dinner before anyone said a word. | PERSON, EMOTION | Family dinner table. |
| 24 | 61.49 | It's me. | DIALOGUE (Grandpa, yellow) | Grandpa standing, smiling. |
| 25 | 62.05 | I've had a good run. | DIALOGUE (Grandpa), EMOTION | Same shot. |
| 26 | 63.09 | That night, I watched through a gap in the curtains. | DESCRIPTION (POV), PLANT (watcher) | Boy at a red curtain, peeking out. |
| 27 | 65.17 | It walked up our path and bent down to him. | ESCALATION | Through the window: the scarecrow walking up the path. |
| 28 | 66.93 | Grandpa took his hat off, like he was meeting someone at church. | EMOTION (dignity) | Scarecrow bending to Grandpa, who holds his hat. |
| 29 | 69.33 | Then the stitches ripped open and Grandpa was gone. | CALLBACK (to #4), REVEAL | The boy's sad face at the window. The death happens off-screen. |
| 30 | 71.57 | The chair was still rocking. | EMOTION (aftermath image) | Empty rocking chair on the porch. |
| 31 | 72.85 | My dad's the best dad in town. | PERSON (Dad, present tense) | Boy and Dad in the front yard with a ball. |
| 32 | 74.37 | He coaches my team. | PERSON | Baseball field, kids in uniforms. |
| 33 | 75.41 | He calls me buddy. | PERSON, PLANT ("buddy") | Dad in a red cap high-fiving the boy. |
| 34 | 76.29 | And every night before bed, he checks every lock in the house three times. | PERSON, PLANT (locks) | Dad at the front door checking the lock. |
| 35 | 79.57 | Nothing gets in here, buddy. | DIALOGUE (Dad, blue), PLANT (ironic) | Close-up of a hand on the gold door lock. |
| 36 | 80.85 | Not on my watch. | DIALOGUE (Dad) | Dad and the boy in the hallway by the door. |
| 37 | 81.73 | This year, it was just the three of us. | ESCALATION (stakes: who goes?) | Dining room, three at the table. |
| 38 | 83.25 | Me, Mom, and Dad. | ESCALATION | Doorway framing the three at the table. |
| 39 | 84.50 | Dinner was quiet. | EMOTION | Boy and Dad at the table, silent. |
| 40 | 85.22 | Then Mom put her fork down. | ESCALATION | Mom at the table. |
| 41 | 86.50 | It should be whoever we need the least. | DIALOGUE (Mom, pink), TWIST | Mom's face. |
| 42 | 88.02 | And she looked at me. | TWIST (Mom picks the narrator) | Mom stares into the lens (the narrator's POV). |
| 43 | 88.82 | Dad slammed the table so hard the plates jumped. | REVERSAL, sensory | Dad slamming the table. |
| 44 | 91.06 | Nobody in this house goes out there but me. | DIALOGUE (Dad), REVERSAL, PLANT | Dad standing, pointing, shouting. |
| 45 | 92.74 | Mom started crying, but she didn't argue. | EMOTION (ambiguous), PLANT | Mom crying, mouth open. |
| 46 | 94.42 | On porch night, the whole town went dark, except the porch lights. | ESCALATION (the night arrives) | Aerial night street; only the porch lights are on. |
| 47 | 97.30 | Every porch on our street had someone on it. | DESCRIPTION | A house with a figure on its porch. |
| 48 | 98.98 | Old Mrs. Pell, wrapped in a blanket, the Fisher boy, tied to his chair. | CALLBACK (#14, #20) | Old woman in a blanket in a rocking chair; a boy roped to his chair. |
| 49 | 102.10 | And on Mr. Wendell's porch, Danny from my class. | CALLBACK (#17), PERSON (mirror kid) | Danny in overalls on the porch, sad. |
| 50 | 104.34 | His mom had taken the money. | CALLBACK, CONSEQUENCE | Danny's mother holding green cash. |
| 51 | 105.46 | Dad hugged me at the door, longer than he ever had. | EMOTION (farewell) | Dad hugging the boy at the door, Mom behind. |
| 52 | 107.78 | Then he went out and sat down in the chair. | ESCALATION | Dad seated in the porch chair, grim. |
| 53 | 109.30 | Mom locked the door and we waited. | ESCALATION | Mom at the door with the boy. |
| 54 | 110.82 | At midnight, the streetlights at the end of the street went out, one by one. | ESCALATION (ticking clock) | Night street; the lamps go out towards the camera. |
| 55 | 113.86 | Then we heard the straw creaking. | CALLBACK (#3), sound-before-sight | Boy and Mom peering out of a window. |
| 56 | 115.30 | It came around the corner, and Mrs. Pell didn't even scream. | ESCALATION | Mrs. Pell calm in her rocking chair, eyes closed. |
| 57 | 117.86 | The Fisher boy did. | ESCALATION (contrast) | The tied boy screaming. |
| 58 | 118.82 | Then the knocking started. | CALLBACK (#20, #21) | Houses at night. |
| 59 | 119.94 | Every house, all the way down. | ESCALATION | Porch window with frightened faces inside. |
| 60 | 121.19 | When it got to Mr. Wendell's porch, Danny ran. | ESCALATION, CALLBACK | Danny running across the porch to the door. |
| 61 | 123.43 | He made it to the door, and Mr. Wendell held it shut while he banged on it. | TWIST (minor), PLANT (door held shut) | Mr. Wendell holding the door; Danny's face through the side glass. |
| 62 | 126.39 | It took him right off the doorstep, two houses away. | ESCALATION (distance clock) | Scarecrow claws snatching him from the doorstep. |
| 63 | 128.47 | Then Dad started knocking, soft at first. | TWIST (the hero breaks), CALLBACK | Front door seen from inside, Mom and the boy watching it. |
| 64 | 130.39 | Honey, open the door. | DIALOGUE (Dad) | Dad knocking on the door from the porch (back view). |
| 65 | 131.43 | Mom covered her mouth, then harder. | EMOTION, ESCALATION | Dad pounding. |
| 66 | 132.95 | Open the door! | DIALOGUE (Dad) | Dad pounding. |
| 67 | 133.67 | OPEN THE DOOR! | DIALOGUE (Dad, CAPS) | Mom and the boy inside, terrified. |
| 68 | 134.47 | Then nothing. | ESCALATION (silence), misdirection | Mom and the boy in the living room. |
| 69 | 135.03 | Mom whispered, He's okay, he's okay. | DIALOGUE (Mom), false relief | Mom hugging the boy. |
| 70 | 136.87 | And then glass smashed in the kitchen. | TWIST | Kitchen window shattering. |
| 71 | 138.39 | Dad came in through the back window, covered in glass, with eyes I'd never seen before. | TWIST / REVEAL, CALLBACK (#35 inverted) | Dad in the kitchen, wild furious face (close-up at 140.8). |
| 72 | 141.91 | Mom screamed his name. | EMOTION | Mom screaming. |
| 73 | 143.03 | He shoved her into the wall. | ESCALATION | Dad shoving Mom. |
| 74 | 144.07 | Then he grabbed me. | TWIST | Dad grabbing the boy. |
| 75 | 144.71 | I grabbed the table, the chairs, the door frame. | EMOTION (physical, list of three) | Dad dragging the boy through doorways. |
| 76 | 146.95 | I'm sorry, buddy. | DIALOGUE (Dad), CALLBACK (#33), EMOTIONAL PEAK | Dad dragging him, crazed and guilty face. |
| 77 | 147.75 | I'm sorry. | DIALOGUE (Dad) | Same. |
| 78 | 148.31 | I'm sorry. | DIALOGUE (Dad) | Same. |
| 79 | 148.95 | He threw me out onto the porch and slammed the door. | TWIST (inverts #44) | Boy on the dark porch, the rocking chair empty. |
| 80 | 150.95 | I hit it with both fists. | CALLBACK (#21: "everyone knocks") | Boy pounding the door. |
| 81 | 152.23 | Inside, Mom was screaming at him. | EMOTION | Through the window: Dad and Mom inside. |
| 82 | 153.91 | Then I heard the creaking on our path. | CALLBACK (#3), CLIFFHANGER | Boy on the porch, looking at the path. |
| 83 | 155.35 | Slow. | CLIFFHANGER (one-word beat) | Low angle: the scarecrow's straw legs stepping up the path. |
| 84 | 155.91 | Every single step. | CLIFFHANGER, CALLBACK ("with every step") | Same; the last frame (157.0) is the boy alone, facing the door. **Trim.** |

---

## 2. Beat map

| Time | Beat | Detail |
|---|---|---|
| 0.00-5.47 | **Rule** | The obligation is complete at "outside," (3.15 s). The hook image is "every porch is **empty**." (word at 4.99 s, sentence ends 5.47 s). Rule plus consequence are both in the first sentence. |
| 5.47-23.52 | **Monster** | Cornfields, midnight, scarecrow, straw, sack head, stitched smile. Slow walk with a sound cue. Second-person threat ("right in front of **yours**", 20.19). Horror image: "the stitches rip open. Wider than its whole head." (21.15-23.4). |
| 23.52 | **Title drop** | "We call it porch night." (the word "porch" at 23.92) |
| 24.64-31.68 | **Rule-within-the-rule** | One chair per porch. "And there's only one rule. Somebody has to be in that chair." (28.80-31.28). |
| 31.68-37.60 | **The ~30-second turn** | "The year **I** was born" brings in the first "I" (32.00). The Harpers hid and were all taken: hiding fails and locks fail. This turns a monster story into a **sacrifice dilemma**: a family must choose. |
| 37.60-58.45 | **Society (consequence)** | Old go first; rich pay; Wendell buys a poor kid; "One for the porch!" joke; people tied to chairs; "everyone knocks ... nobody opens". |
| 58.45-72.85 | **First case: Grandpa** | Volunteers, "I've had a good run", hat off "like he was meeting someone at church", gone, "The chair was still rocking." Tense switches to past at 58.45. |
| 72.85-81.73 | **The one person: Dad** | "best dad in town", coaches, "buddy", checks the locks three times, "Nothing gets in here, buddy. Not on my watch." |
| 81.73-84.50 | **Stakes** | "This year, it was just the three of us. Me, Mom, and Dad." |
| 86.50-88.82 | **Twist 1** | Mom: "It should be whoever we need the least. And she looked at me." |
| 88.82-94.42 | **Reversal 2** | Dad slams the table: "Nobody in this house goes out there but me." Mom "didn't argue". |
| 94.42-110.82 | **Porch night** | Town dark; callback montage (Mrs. Pell, the Fisher boy, Danny on Wendell's porch); long hug; Dad in the chair; door locked. |
| 110.82-121.19 | **Approach (clock)** | Midnight; streetlights out one by one; creaking; around the corner; one scream; knocking down the street. |
| 121.19-128.47 | **Mirror kid** | Danny runs, Wendell holds the door shut, Danny is taken "two houses away" (distance marker: we are next). |
| 128.47-134.63 | **Twist 2** | The hero knocks: "soft at first" ("Honey, open the door") then shouted ("OPEN THE DOOR!"). |
| 134.47-136.39 | **Misdirection** | "Then nothing." / "He's okay, he's okay." |
| 136.87-141.51 | **Twist 3** | Glass smashes; Dad breaks in through the back window "with eyes I'd never seen before". |
| 144.07-150.63 | **Twist 4** | Dad drags the narrator: "I'm sorry, buddy. I'm sorry. I'm sorry." Throws him onto the porch and slams the door. |
| 150.95-157.03 | **Last beat before the trim** | Narrator knocks with both fists; Mom screams at Dad inside; "Then I heard the creaking on our path. Slow. Every single step." Cut at 157.0. |

Where the beats fall in the visible 157 s:

| Element | Time | % of runtime |
|---|---|---|
| Rule | 0-3.5 s | 0-2% |
| Rule-within-rule plus Harpers turn | 29-37 s | 18-24% |
| Grandpa | 58 s | 37% |
| Dad introduced | 73 s | 46% |
| First real plot twist (Mom) | 87 s | 55% |
| Dad breaks in | 137 s | 87% |
| Narrator thrown out | 149 s | 95% |

**The "one person".** The narrator-child exists from 32.0 s but stays an observer. The person who tests the rule (sits in the chair, then breaks it) is **Dad**, built from 72.85 s. Grandpa (59.1 s) is a rehearsal: he shows the rule obeyed with dignity, so we can measure Dad's collapse against it.

### Open loops: opened, then paid

| # | Loop (question in the viewer's head) | Opened | Paid |
|---|---|---|---|
| L1 | What empties the porches? | 4.99 "every porch is empty" | 5.5-23.4 the scarecrow. What happens inside the mouth is never paid (a mystery kept on purpose). |
| L2 | What if nobody sits in the chair? | 31.28 "Somebody has to be in that chair" | 31.7-37.2 the Harpers, all gone |
| L3 | How do families choose? | 37.60 "So every family chooses" | 38.9-53.6 (old, rich, extra kid, tied) |
| L4 | Wendell's paid kid | 42.37 | 102.1 Danny on his porch; 121.2-128.2 Danny runs and Wendell holds the door |
| L5 | "everyone knocks ... nobody opens" | 52.85-57.89 | 118.8 knocking starts; 128.5-134.6 Dad knocks; 150.95 the narrator knocks. Will Mom open? **Still open at the trim.** |
| L6 | "Last year, it was Grandpa" | 58.45 | 59.7-72.3 |
| L7 | "Nothing gets in here, buddy. Not on my watch." | 79.57 | Inverted at 138.4 (Dad is what gets in) and at 146.95 ("I'm sorry, buddy") |
| L8 | Who goes this year (one of three)? | 81.73 | 86.5 Mom picks the narrator; 91.1 Dad overrules; 149 the narrator is thrown out anyway |
| L9 | Why didn't Mom argue? | 92.74 | Partly at 135 ("He's okay") and 141.9/152.2 (she turns on Dad). Her motive is never stated. |
| L10 | Is Dad dead after the knocking stops? | 134.47 "Then nothing." | 136.87 glass smash: no, he is breaking in |
| L11 | Will the narrator be taken? | 149-157 | **OPEN (cliffhanger).** The chair is empty and he is not sitting in it. |

### Emotional peaks
- **Main peak: 146.95-151.67 s.** "I'm sorry, buddy. I'm sorry. I'm sorry." / thrown out / "I hit it with both fists." The protector betrays the child, and the pet name planted at 75.41 s is the knife.
- **Secondary (grief): 66.93-72.29 s.** Grandpa's hat, then "The chair was still rocking."
- **Moral shock: 86.50-88.50 s.** "whoever we need the least. And she looked at me."

---

## 3. Numbers

| Measure | Value |
|---|---|
| Duration (visible) | 157.0 s; speech runs from 0.07 to 156.99 s, so there is **voice over 100% of the runtime**. |
| Total words | **702** (284 unique; type/token 0.40) |
| WPM overall | **268**. While speaking: **269**, because pauses are negligible: only 12 gaps of 0.5 s or more, the longest 0.64 s, all at sentence ends. Median gap between word onsets is 0.16 s. |
| WPM by 30 s window | 262 / 268 / 278 / 276 / 264 / 239 (last 7 s). The pace never drops for emotional beats. |
| Sentences | 84. Median length **7 words**, mean 8.4, min 1 ("Slow."), max 33 (the scarecrow description). |
| Sentence-length mix | 1-5 words: **31 (37%)**. 6-10: 32 (38%). 11-15: 12 (14%). 16+: 9 (11%). |
| Mean sentence length by section | Hook/monster 20.0. Rule/proof 9.0. Society 10.4. Grandpa 7.6. Dad 6.4. Dinner 6.7. Porch night 9.8. Attack 9.1. Dad knocking **4.4**. Break-in 6.4. Cliff **4.8**. Sentences get shorter as tension rises. |
| Sentence openers | "Then" 9, "And" 6 (one "And then"), "So" 1, "But" 0: **16 of 84 (19%)**. "Then" appears 12 times in total and drives the climax (sentences 63-74). Other frequent openers: "It" 7 (the monster), "He" 6, "Every" 5, "Mom" 5. |
| Point of view | First-person child narrator, past tense from 58.45 s. Present tense for the world rules (0-58 s) and for Dad's portrait (sentences 31-34). Pronouns, all text: first person 30 (22 in narration), second person **5 ("you/yours", all before 58 s)**, third person 57 ("it" 21, with the monster always "It", named only once as "a scarecrow" at 7.15). Communal "we": "We call it porch night", "we waited", "we heard". |
| Dialogue | 14 sentences (17% of sentences), 58 words (8.3%), about 13.7 s (8.7% of time). **Dad** 9 lines / 35 words: "Nothing gets in here, buddy." / "Not on my watch." / "Nobody in this house goes out there but me." / "Honey, open the door." / "Open the door!" / "OPEN THE DOOR!" / "I'm sorry, buddy." / "I'm sorry." / "I'm sorry." **Mom** 2 lines / 12 words: "It should be whoever we need the least." / "He's okay, he's okay." **Grandpa** 2 lines / 7 words: "It's me." / "I've had a good run." **Townspeople** 1 line / 4 words: "One for the porch!" The only speech tag is "Mom whispered,"; speakers are carried by context, the on-screen character and caption colour. |
| New information rate | A new sentence every **1.87 s**; nearly every one adds a fact or an image (the only deliberate stalls are "Open the door!" x2 and "I'm sorry." x3). **106 shots, one every 1.47 s.** 73 of 84 sentences (87%) begin on a cut, landing a median **0.07 s before the first word**. 32 more cuts fall mid-sentence on new nouns (sentence 2: "scarecrow" 6.97, "straw" 8.73, "sack" 10.33, "smile" 11.33). The longest single shot is about 4.2 s (24.5-28.7). |
| New named characters | Scarecrow 7.2, the Harpers 32.7, Mr. Wendell 42.4, Grandpa 59.1, Dad 72.9, Mom 83.6, Mrs. Pell 99.2, the Fisher boy 100.7, Danny 103.3, Danny's mom 104.3. Nine in 105 s, about one per 12 s until the attack. After that, no one new. |
| Repeated words | porch 13, every 12, door 9, Mom 9, one 9, year 7, chair 6, Dad 6, night 5, open 5, house 5, knock- family 5 (+ "banged", "hit it with both fists"), nobody 3 ("Nobody sits" / "nobody opens" / "Nobody in this house"), buddy 3, straw 3, creak 3. |
| Repeated phrases | "all the way down" 3 (bends / down the street / every house); "Open the door" 3; "I'm sorry" 3; "stitches rip(ped) open" 2 (4 → 29); "in the morning ... empty" 2 (1 → 12); "Mr. Wendell's porch" 2; "the Fisher boy" 2; "every step" 2 (3 → 84). |
| Numbers and specifics | "one night a year", "one person", "taller than the streetlights", "one chair ... just one", "only one rule", "The year I was born", "a new kid every year", "one more kid", "three times" (shown as "3"), "the three of us", "at midnight" (x2), "one by one", "two houses away", "both fists", "every single step". These are **small counts (one, two, three), not big ones**: the scale is intimate. Concrete nouns: cornfields, sack, stitched smile, the bottom of the hill, gap in the curtains, hat, church, fork, plates, porch lights, blanket, rope, money, back window, glass, door frame. |
| Word simplicity | About 77% one-syllable words, about 4% with three or more syllables (almost all "every / family / nobody / somebody"). Mean word length 4.0 letters. |

---

## 4. Devices (technique, example, time)

1. **First-frame rule in one sentence that contains its own consequence** (0.00-5.47). "In this town, one night a year, every family has to leave one person outside, and in the morning, every porch is empty." It is built in four comma chunks (place / time / obligation / result). The **last word is the punch ("empty")**: it is the final single caption before the cut.
2. **Mystery by omission** (4.99, 21.87, 34.72-37.20, 71.17). We are never told where people go: "every porch is empty", "the stitches rip open", "the house was empty", "Grandpa was gone". The horror stops at the mouth.
3. **Rule-within-the-rule** (28.80). "And there's only one rule. Somebody has to be in that chair." It reframes the rule from "a monster comes" to "you must choose who dies".
4. **Proof case that closes the loophole** (31.68-37.20). The Harpers locked themselves in and the house was empty anyway. It answers the viewer's first objection ("just hide") and plants the house-taken outcome for the ending.
5. **Society montage of coping strategies** (37.60-58.45): age ("Old people go first"), class ("Rich families pay", the Wendell kid), dark humour ("One for the porch!"), cruelty (tying people to chairs). This is the "how everyone lives" step, done as rapid three-to-ten-word facts.
6. **Every worldbuilding fact returns on screen (Chekhov montage)**. Old → Mrs. Pell (98.98, 115.30). Tied → the Fisher boy (100.58, 117.86). Paid kid → Danny (102.10, 121.19). Knocking → the street (118.82), Dad (128.47), the narrator (150.95). No setup is wasted.
7. **Rehearsal character** (58.45-72.29). Grandpa shows the rule obeyed with grace ("I've had a good run", "like he was meeting someone at church"), so Dad's failure reads as a fall.
8. **Hero portrait in triplets plus a vow** (72.85-81.25). "He coaches my team. He calls me buddy. And ... he checks every lock in the house three times." Then "Nothing gets in here, buddy. Not on my watch." Present tense and absolute language set up the irony.
9. **Plant → callback with meaning inverted**:
   - "Nothing gets in here" (79.57) → Dad gets in (138.39).
   - "buddy" (75.81) → "I'm sorry, buddy" (147.35).
   - "Nobody in this house goes out there but me" (91.06) → he throws the narrator out (148.95).
   - "everyone knocks ... nobody opens" (52.85-57.89) → the narrator knocks (150.95).
   - "straw creak with every step" (14.59-15.71) → "creaking on our path. Slow. Every single step." (154.31-156.63).
   - "stitches rip open" (21.15) → "ripped open" (69.89).
10. **Mirror / preview character**. Danny ("from my class", the same age) runs to a door that an adult holds shut and is taken off the doorstep (121.19-128.15). This happens **22 s before** the narrator's identical situation, so the audience knows exactly what is coming.
11. **Ticking clocks and distance markers**: "At midnight" (110.82); "the streetlights at the end of the street went out, one by one" (110.98-113.46); sound before sight, "Then we heard the straw creaking" before "It came around the corner" (113.86-115.86); "Every house, all the way down" (119.94); "two houses away" (127.67).
12. **Sound-led horror** (sensory detail). Creak (14.99, 114.82, 154.31), rip (21.63), knocking and begging (56.37-56.85), plates jumped (90.58), glass smashed (137.43), screaming (152.23). Visual specifics: straw sleeves, sack head, stitched smile, porch lights in a dark town. Touch: "I grabbed the table, the chairs, the door frame" (144.71), "both fists" (151.51).
13. **Second-person pull in the opener**: "you can hear the straw creak" (14.19), "right in front of **yours**" (20.19), "what you do when you get old here" (40.40). This puts the viewer in the chair, then hands over to "I" at 58 s.
14. **Tense as structure**. Present tense = the timeless law of the world (0-58 s); past tense = this story ("Last year...", 58.45). Past-tense first person also quietly suggests the narrator survives (relevant to the ending).
15. **Last-year to this-year escalation** (58.45 → 81.73). "Last year, it was Grandpa." / "This year, it was just the three of us." Immediacy comes from a small family arithmetic (three people, one chair).
16. **Moral-shock line from a trusted figure** (86.50). "It should be whoever we need the least." The visual has Mom looking straight into the lens, so the viewer is the one chosen.
17. **Reversal chain**. Mom picks the son (87) → Dad volunteers (89) → Dad breaks (128) → silence (134) → Dad breaks in (137) → Dad throws the son out (149) → the son becomes the knocker (151). There are seven turns in the last 70 s, roughly one every 10 s.
18. **Misdirection by silence and false comfort** (134.47-136.39). "Then nothing." / "He's okay, he's okay." It plays the expected death, then the window smashes.
19. **Escalating repetition with typography**. "Honey, open the door." (soft, 130.39) → "Open the door!" → "OPEN THE DOOR!" (caps caption, 133.67). Then "I'm sorry, buddy. I'm sorry. I'm sorry." (146.95-148.47): three beats, shortening.
20. **Emotional sacrifice, then its inversion**. Sacrifice: Grandpa (59.65), Dad (91.06-108.98), the long hug "longer than he ever had" (106.66). Inversion: the sacrifice is withdrawn (138.39).
21. **Contrast pairs**: "Mrs. Pell didn't even scream. / The Fisher boy did." (115.30-118.58). Rich man and poor kid. Hero and coward in one person.
22. **Cliffhanger cut on a sound callback** (153.91-157.03). The cut lands on "Every single step." with the monster's feet on screen and the narrator alone, not in the chair. No resolution.
23. **Off-screen deaths**. Grandpa's death is shown as the boy's face plus the empty rocking chair (69.3-72.3); Danny's as a claw grab. This is cheaper to animate and keeps it platform-safe, while the viewer's imagination does the work.
24. **Built for word-by-word captions**:
    - Mostly one-syllable words.
    - Sentences end on their strongest noun or verb (empty, open, head, chair, gone, rocking, buddy, least, me, money, nothing, wall, door, fists, step).
    - Fragments act as single-caption hits ("Wider than its whole head.", "Slow.", "Then nothing.").
    - Colour per speaker replaces quote marks and "he said".
    - Numerals shown as digits ("3"); a shout in caps ("OPEN THE DOOR"); the title phrase capitalized as a name ("Porch Night").
25. **Cut-per-sentence editing**. 87% of sentences start on a new shot (0.07 s before the first word); within long sentences, one cut per new noun image.

---

## 5. How it probably continues (GUESS, not seen)

**Length caveat.** The brief says the last 1-2 minutes are cut. But a YouTube Short is at most 3:00, so if this is a Short, **at most about 23 s (about 100 words at this pace) remain**. A 1-2 minute remainder would make it a 3.5-4.5-minute video. Either way, the remaining part has to resolve L5 (will anyone open?) and L11 (is the narrator taken?).

Clues in the setup:
- (a) The narrator tells the story in **past tense**, which implies he survives.
- (b) The rule is "somebody has to be **in that chair**". At the trim the chair is empty and the boy is at the door.
- (c) The Harpers precedent: if the chair is empty, the whole house is taken even when locked.
- (d) Dad has just **broken the back window**: "Nothing gets in here" is no longer true.
- (e) The Grandpa model (hat off, calm acceptance) is waiting to be repeated.
- (f) Mom's turn against Dad ("screaming at him").

Ranked guesses:
1. **(most likely)** The boy stops knocking, remembers Grandpa and **sits in the chair**, maybe taking off his cap. It bends down, face to face, the stitches start to rip... A final reversal follows. Either it passes him and goes in through the **broken back window for Dad** (the one who left the chair and opened the house), or Mom opens the door and takes his place. Morning: the narrator alive on the porch, one parent gone, the chair still rocking. Last line: a generational or ironic callback, e.g. the grown narrator who now "checks every lock three times" or always sits in the chair himself.
2. **Rule-letter ending.** Nobody is in the chair, so it takes the house, Harpers-style: "In the morning, our door was still locked and the house was empty." The boy on the porch is spared. A short coda years later: his own family, and he sits in the chair himself every year.
3. **Hard cliffhanger / part 2.** It reaches him, "and then the stitches ripped open", cut, possibly with a "Part 2" hook.

---

## 6. Why it works, and its weak spots

**Retention**
- The rule and the horror image land inside 23 s.
- The 30-second turn (only one rule, plus the Harpers) converts curiosity into a dilemma.
- From then on a new fact arrives about every 1.9 s and a new shot about every 1.5 s, with no pauses over 0.64 s, so there is no exit point.
- Loops overlap. Each payoff opens the next question (who goes? → Dad → will he hold? → he knocks → is he dead? → he breaks in → the son is outside).
- Danny previews the climax 22 s early, so tension rises before the event.
- The ticking clock (midnight, lights out one by one, "two houses away") gives the final third a countdown.

**Emotion**
- The world is built from family arithmetic: three people, one chair.
- The story then attacks the safest figure a child has, the "best dad in town", using the dad's own words ("buddy", "Nothing gets in here", "Nobody ... but me") as the weapons.
- Grandpa's dignified death sets the moral bar, which makes Dad's collapse hurt.
- The protagonist is a child viewer-surrogate who starts as a watcher behind curtains and ends on the porch.

**Shareability**
- Comment-bait dilemma: "who would your family put on the porch?"
- A quotable dark line: "One for the porch!"
- A debate trigger: is Dad a monster or human? Would you open the door?
- Class satire: rich families buy poor kids.
- The betrayal twist is easy to retell in one sentence.

**Weak spots**
- **Pace: 268 wpm, almost no breath.** Grandpa's goodbye and the hug are rushed, and "Slow." gets 0.56 s. The narration was probably sped up or synthetic (no pauses over 0.64 s). A human reading this text naturally (about 160-180 wpm) would need about 4:00. For our 2:00-2:30 target that means about 380-480 words read naturally, or about 550-650 words with a light speed-up in editing.
- **Late personal stakes.** The real dilemma for our family starts at 81.7 s (52%) and the first plot twist at 87 s (55%). Before that, retention leans entirely on worldbuilding density. The "30 s twist" is a reframe, not a plot event.
- **Rule logic gaps.**
  - Can the sitter leave the chair, and why does nothing punish Dad while he runs round the back?
  - Does being on the porch count, or only the chair?
  - The Harpers precedent says the whole locked house is taken when the chair is empty, yet Dad is safe inside with a broken window. The ending must patch this.
- **Mom's motive is opaque.** She picks her son, does not argue for her husband, then screams at the husband. Her arc relies on the viewer filling the gap.
- **Cast load.** Nine named characters in 105 s. Each is tied to a rule, but a viewer can lose track (Mrs. Pell vs the Fisher boy).
- **Tone risk for the platform and its audience.** A father shoving the mother and throwing his child out to die is strong for a Roblox-style audience. The deaths are off-screen, which helps.
- **Weak title.** "Porch Night" carries less curiosity than a forbidden-action title such as "Never Be Caught Awake At Night".
- **Possible ending dependence.** If the true ending is a part-2 hook, some viewers feel cheated.

**Mechanics to transfer (not content)**
- A one-sentence rule that ends on its consequence word.
- Rule-within-the-rule, then a proof case that kills the obvious loophole.
- Three to five society facts, each of which reappears later on screen.
- A rehearsal case "last year", then "this year" with a small family arithmetic.
- A hero portrait in three short present-tense lines plus a vow that the twist inverts word for word.
- A mirror character who previews the climax about 20 s early.
- An audio-first approach clock.
- A soft → loud → CAPS line ladder.
- Colour-coded dialogue captions and one cut per sentence.
