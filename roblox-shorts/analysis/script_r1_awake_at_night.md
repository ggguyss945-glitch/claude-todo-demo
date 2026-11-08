# Script analysis: r1 "Never Be Caught Awake At Night"

Reference only. The lines are quoted here so we can analyse them. Do not reuse them. We borrow the mechanics, not the content.

- Source: `ref/r1_awake_at_night.mp4` (720x1280, 30 fps, 148.03 s, trimmed so the ending is missing). Inputs: ASR word times (`asr/r1_awake_at_night.json`), both frame sheets, and about 230 extra frames I extracted with `ffmpeg -ss` (every 1 s, plus 0.15 s steps around doubtful words) into `scratchpad/rbx/work/r1script/`.
- **Timing caveats.**
  - In our copy the video stream starts at **3.70 s** and the audio starts at 0.00. So we cannot see the first 3.7 s of picture. Players hold the first available frame, which shows the creature's face at a bedroom window.
  - The frame-sheet labels are roughly 0.5-1 s early, because of the fps-filter offset. In the sheet, frames 0:00-0:04 all show the 5 s shot.
  - All times below come from the word timings and from exact `-ss` frames.
- **Format.** One narrator: the hero, "Max", tells it in first person, past tense. The opening addresses the viewer as "you". The only quoted dialogue is Grandpa's line in a flashback. There is music under the whole thing, and voice runs from the first frame to the last with no pause longer than 0.8 s.

### ASR corrections (checked against the burned-in captions and on-screen signs)

| t (s) | ASR | Corrected | Evidence |
|---|---|---|---|
| 10.15 | "lullaby" | "Lullaby" (a name) | The caption shows "lullaby". At 51.5 the caption shows "Lullaby" capitalised. |
| 38.11 / 38.43 | "tinker, tinker" | "tink, tink" | The caption reads "tink" on every frame from 37.85 to 38.75. The voice may say "tink-a". |
| 52.75 | "sleepwalk." | "sleepwalkers." | The caption shows "sleepwalkers" from 52.9 to 53.2, over a shot of a sleepwalking kid. |
| 76.26-76.98 | "Tink, tink a tink." | "Tink, tink, tink." | The caption shows "Tink" three times, then "every". |
| 88.3-89.5 | "tick and tune toy factory" | "Tick and Tune Toy Factory" | The building sign reads "TICK & TUNE TOY CO." |
| 116.88 | "Swirling" | "twirling" | The caption shows "twirling". |
| 61.87 / 90.58 | "ten" / "a hundred" | (spoken as words) | The captions render these as digits **"10"** and **"100"**. "five" (30.0) stays a word. |
| 147.95 | (missed) | **"Knit…"** | The caption reads "knit" and the audio energy jumps at 147.95. This is **"tink" spelled backwards**, matching the reversed song. The video is cut right here. |
| 74.67 / 96.02 / 116.40 | full stops | commas | The ASR put segment breaks here. These are participle fragments that carry on the sentence: "crank, turning…", "ceiling, swaying…", "thumb, twirling…". This is a judgement call and no times change. 98.32 "anything, rows" is split into two sentences. |

---

## 1. Clean transcript, numbered, tagged, with picture

Tags: RULE / CONSEQUENCE / PERSON / ESCALATION / TWIST / REVEAL / EMOTION / CALLBACK / CLIFFHANGER / DIALOGUE / DESCRIPTION (plus REVERSAL, plant).

| # | Start | Sentence | W | Tag | Picture (one line) |
|---|---|---|---|---|---|
| 1 | 0.00 | In this world, something walks the streets at midnight, and if you're awake when it passes, it takes you. | 19 | **RULE** | No picture before 3.7 s in our copy. From 3.7: a cracked porcelain doll face peers through a bedroom window, head tilted. At 4.0 a jointed hand reaches for the glass, on "takes". |
| 2 | 4.39 | You see, nobody has ever seen it up close. | 9 | DESCRIPTION (mystery) | Extreme wide night street with a tiny white figure on the zebra crossing. The shot is literally "not up close". |
| 3 | 6.23 | You only hear it. | 4 | DESCRIPTION (sound) | From behind: a rusty crank turns on its back and white music notes float up. A playground behind. |
| 4 | 7.03 | A tiny tinkling music box song getting closer. | 8 | DESCRIPTION (sound) | Low angle on the dirty nightgown hem dragging on asphalt, with a huge hand. |
| 5 | 9.75 | We call it Lullaby. | 4 | DESCRIPTION (naming) | First full face close-up: cracked doll head, red-stained mouth, notes around it. |
| 6 | 10.87 | So in our town, bedtime is the law. | 8 | **CONSEQUENCE** | Street sign "TOWN LAW / BEDTIME / LIGHTS OUT 8:00 PM / NO EXCEPTIONS". Avatars walk past. |
| 7 | 12.63 | Sleepovers are banned. | 3 | CONSEQUENCE | Sign "NOTICE: SLEEPOVERS ARE BANNED, by order of the town". A sad kid with a pillow. |
| 8 | 13.75 | Some kids sleep in their closets. | 6 | CONSEQUENCE | A kid curled up asleep on a closet floor under hanging clothes. |
| 9 | 15.11 | Some families nail the windows shut. | 6 | CONSEQUENCE | A dad behind a window hammers boards across it. Dust puffs. |
| 10 | 16.79 | And every parent in town sings their kids the exact same lullaby at bedtime. | 14 | CONSEQUENCE (plant) | A mom singing over a blonde kid cuts to a dad singing over a red-haired kid. Same framing, so "exact same". |
| 11 | 20.55 | The rule is simple. | 4 | RULE (restated) | A house at night with every window lit. |
| 12 | 21.27 | When you hear the music box, be asleep. | 8 | **RULE** (imperative) | Same house. The lights go out window by window and it is dark on "asleep" (22.6-22.9). |
| 13 | 22.99 | My name is Max, and I'm the best fake sleeper alive. | 11 | **PERSON** | Max (orange hair) in bed, eyes shut, one arm dangling. |
| 14 | 25.55 | Slow breathing. | 2 | PERSON (plant) | Push-in on the dangling arm. |
| 15 | 26.27 | One arm hanging off the bed. | 6 | PERSON (plant) | Arm close-up. |
| 16 | 27.55 | A tiny bit of drool. | 5 | PERSON (plant, humour) | Face close-up with a drool bubble. |
| 17 | 28.59 | I've fooled my mom every night for five years. | 9 | PERSON | Mom (red hair) leans over to check. Max "asleep". |
| 18 | 30.67 | My best friend Dex is the opposite. | 7 | PERSON (2nd character) | Dex in a green dinosaur onesie, in bed. |
| 19 | 32.19 | Dex can't fall asleep ever. | 5 | PERSON (plant: the victim) | Dex sitting up, wide awake. |
| 20 | 33.55 | He counts sheep until the sheep get bored. | 8 | PERSON (humour) | Sheep hop a little fence beside his bed. |
| 21 | 35.39 | Then one night, the night before our big math test, I heard it. | 13 | **ESCALATION** (inciting) | Wall calendar "OCTOBER" with 24 circled, "MATH TEST!". Then Max in bed, eyes snapping open. |
| 22 | 37.79 | Tink, tink, tink, tink. | 4 | ESCALATION (sound line) | Max's face: eyes wide, mouth open. |
| 23 | 39.07 | I went still. | 3 | CALLBACK (to 14-16) | Eyes squeezed shut. |
| 24 | 39.63 | Slow breathing. | 2 | CALLBACK | Same. |
| 25 | 40.43 | Arm off the bed. | 4 | CALLBACK | The window behind the curtain: the crank passes outside. |
| 26 | 41.23 | The song got louder, right outside my window, then softer. | 10 | ESCALATION | The cracked face presses against Max's window and peers in. This is the same set as the opening frame. |
| 27 | 43.79 | Moving down the street, toward Dex's house. | 7 | ESCALATION (relief turns to dread) | Lullaby walks away down the street, notes trailing. |
| 28 | 45.55 | In the morning, Dex's bed was empty. | 7 | **TWIST 1** | Daylight shot of Dex's yellow house, then Max at the empty green bed, sad face. |
| 29 | 47.07 | The sheets were still warm. | 5 | EMOTION (touch) | Max's face turns from sad to shocked. |
| 30 | 48.11 | That night, I didn't fake sleep. | 6 | REVERSAL (decision) | Max sits up in bed, alert. |
| 31 | 49.55 | Because there's one more thing everybody knows about Lullaby: it never takes sleepwalkers. | 13 | RULE (rule within the rule: loophole) | Max smirks. Then Lullaby glides past a sleepwalking kid in rainbow pyjamas. |
| 32 | 53.55 | Sleepwalkers are asleep. | 3 | RULE (logic) | Close on the sleepwalking kid: arms out, eyes shut. |
| 33 | 54.75 | So at midnight, when the music started, I got up, arms straight out, feet dragging, head drooping, and I sleepwalked right out my front door. | 25 | ESCALATION (plan in action) | Alarm clock "12:00". Max rises, arms out, head down, and walks out the front door. |
| 34 | 60.99 | And there it was, ten feet tall, thin as a lamppost, in a long white nightgown that dragged along the road. | 21 | **REVEAL** | Full-body profile in the street (caption "10"), then the stained hem dragging. |
| 35 | 66.19 | Its head was a cracked porcelain doll's head, tilted to one side, like it was listening. | 16 | REVEAL | The tilted, cracked doll head in close-up. |
| 36 | 69.95 | Its fingers were long and white and jointed, like a puppet's, and sticking out of its back was a giant, rusty crank, turning all by itself. | 26 | REVEAL (plant: crank) | Jointed fingers, with Max sleepwalking in the background. Then the crank on its back, with notes. |
| 37 | 76.26 | Tink, tink, tink. | 3 | DESCRIPTION (sound) | The crank turns and notes burst out. The TOWN LAW sign is behind it. |
| 38 | 77.30 | Every turn played one more note of the song. | 9 | RULE (the monster's mechanic; plant) | Wide street: Lullaby walking, Max shuffling behind. |
| 39 | 79.22 | It stopped. | 2 | ESCALATION | Wide shot; it halts. |
| 40 | 79.78 | Its head turned all the way around toward me. | 9 | ESCALATION | Back of the head, then the face rotates 180° to camera. |
| 41 | 81.54 | I kept walking, arms out, drooling. | 6 | ESCALATION + CALLBACK (drool) | Max close-up: eyes shut, mouth open. |
| 42 | 83.38 | It watched me for a long time. | 7 | ESCALATION (held beat) | Max shuffling; Lullaby looms beside a house. |
| 43 | 84.66 | Then it turned back around and kept going. | 8 | RELEASE (false safety) | Lullaby turns away. Its face in close-up at 86. |
| 44 | 86.42 | I followed it all the way across town, to the old Tick and Tune Toy Factory, the one that closed a hundred years ago. | 24 | ESCALATION (new location) | Over-the-shoulder follow, then a brick clock tower "TICK & TUNE TOY CO.", then the clock face at 12 (caption "100"). |
| 45 | 91.30 | The doors creaked open by themselves. | 6 | DESCRIPTION | Lullaby in the open doorway. |
| 46 | 93.06 | Inside, it was a nightmare made of toys. | 8 | REVEAL | The giant music box under hanging marionettes. |
| 47 | 95.06 | Marionettes hung from the ceiling, swaying, with no strings attached to anything. | 12 | DESCRIPTION (creepy detail) | Dangling marionettes whose strings end in nothing. |
| 48 | 98.72 | Rows of teddy bears sat on the conveyor belts, all facing the door. | 13 | DESCRIPTION | Long rows of teddy bears on the belts. |
| 49 | 101.84 | The walls were stacked with music boxes, thousands of them, every single one ticking. | 14 | DESCRIPTION (ticking motif) | Walls of shelves full of music boxes. |
| 50 | 105.92 | And in the middle of the room was the biggest music box I've ever seen. | 15 | REVEAL | Max seen from behind, facing the giant box. |
| 51 | 108.96 | Big as a carousel, lid wide open, and spinning on top on little brass pegs were tiny dancers. | 18 | REVEAL | The lid is a round mirror, with figures on pegs. |
| 52 | 114.08 | Kids in pajamas, shrunk down to the size of my thumb, twirling around and around, forever. | 16 | **TWIST 2** / REVEAL | The "dancers" in close-up are tiny Roblox kids in pyjamas. Top-down shot of the spin. |
| 53 | 119.20 | Every kid who'd ever been taken. | 6 | REVEAL (pays off "it takes you") | Top-down view of the dancer platter. |
| 54 | 120.64 | And right in front was Dex in his dinosaur pajamas. | 10 | REVEAL + CALLBACK + **EMOTION (peak)** | Dex on a peg in the dinosaur onesie, then Max's horrified face (123.0). |
| 55 | 123.20 | Lullaby reached out with one long finger toward an empty brass peg and then toward me. | 16 | ESCALATION (stakes) | Lullaby points at an empty peg, then at Max. |
| 56 | 127.36 | It knew. | 2 | **TWIST 3** (reversal) | Lullaby pointing, with notes. |
| 57 | 127.92 | I ran. | 2 | ESCALATION | Max runs. |
| 58 | 128.40 | Its fingers snapped shut right behind my head. | 8 | ESCALATION | The hand clamps shut just behind Max. |
| 59 | 130.32 | I dove behind the giant music box, and that's when I noticed something. | 13 | ESCALATION + open loop | Max dives to the floor; Lullaby searches. |
| 60 | 133.20 | Its crank was slowing down. | 5 | REVEAL + CALLBACK (to 38) | Crank close-up. |
| 61 | 134.48 | Tink, tink. | 2 | ESCALATION (ticking clock: fewer tinks) | Crank close-up, few notes. |
| 62 | 135.12 | And I remembered my grandpa's old music box. | 8 | CALLBACK (flashback trigger) | Max's face as he realises. |
| 63 | 137.12 | "Here's the thing about music boxes, Max," he told me once. | 11 | **DIALOGUE (Grandpa)** | Flashback in warm daylight: a white-haired grandpa beside little Max's bed with an open music box and a spinning ballerina. |
| 64 | 139.52 | "When the song ends, the dancer stops." | 7 | DIALOGUE (Grandpa) / RULE (second rule within the rule) | Ballerina close-up; she stops. |
| 65 | 141.36 | Lullaby came around the corner, and I jumped onto its back, grabbed that rusty crank with both hands, and I turned it backwards. | 23 | ESCALATION (climax action) | Lullaby rounds the corner. Max leaps onto its back, grabs the crank and cranks it. |
| 66 | 146.80 | The song played in reverse. | 5 | **TWIST 4 / CLIFFHANGER** | Notes swirl around the crank. |
| 67 | 147.95 | Knit… | 1 | CLIFFHANGER (cut mid-word) | Caption "knit" ("tink" backwards). The video ends at 148.03. |

Tag tally across 66 complete sentences (one main tag each; the counts sum to 66):
- RULE 7
- CONSEQUENCE 5
- PERSON 8
- DESCRIPTION 9
- REVEAL 9
- ESCALATION 16
- TWIST 4
- REVERSAL 2 (30, 43)
- CALLBACK 4
- EMOTION 1
- DIALOGUE 1 (#64 is counted under RULE)

Secondary tags:
- CALLBACK on 41, 54, 60
- EMOTION on 54
- DIALOGUE on 64
- CLIFFHANGER on 66, plus the cut fragment 67

---

## 2. Beat map

| Time | Beat | What happens |
|---|---|---|
| 0.00-4.39 | **Rule (first sentence)** | "In this world, something walks the streets at midnight…" The rule lands on **"it takes you" (3.75-4.39)**, 4.4 s in. The imperative form arrives at 21.27-22.84: "When you hear the music box, be asleep." |
| 4.39-10.87 | Mystery and sound signature, then the name | It is never seen up close, only heard. "Lullaby" is named at **10.15**. |
| 10.87-20.55 | **Consequence (society)** | Five sentences in 9.7 s: bedtime law, sleepovers banned, kids sleeping in closets, nailed windows, every parent singing the same lullaby. |
| 20.55-22.84 | Rule restated | "The rule is simple." The lights go out on "asleep". |
| **22.99** | **The one person** | "My name is Max, and I'm the best fake sleeper alive." The hero's skill is built to beat the rule. |
| 30.67-35.3 | The foil / future victim | "My best friend Dex is the opposite… can't fall asleep ever." |
| **35.39** | Inciting incident | "Then one night… I heard it." The narrative clock starts here (Rule 1 tests the hero). |
| 41.23-45.2 | Misdirection | The song passes Max ("then softer"), so he is safe, but it goes "toward Dex's house". |
| **45.55** | **Twist 1** | "In the morning, Dex's bed was empty." Then "The sheets were still warm." (47.07) |
| **48.11** | Reversal of character | "That night, I didn't fake sleep." The hero gives up his safe skill and goes on the offensive. |
| **49.55-54.35** | Rule within the rule (loophole) | "it never takes sleepwalkers. Sleepwalkers are asleep." |
| 54.75-60.99 | Plan in action | At midnight (12:00 on the clock) he sleepwalks out of the front door. |
| **60.99-78.82** | Midpoint reveal | First look "up close" (pays off loop 2): 10 ft, nightgown, cracked doll head, puppet fingers, crank. "Every turn played one more note" (77.30) is the plant for the climax. |
| **79.22-86.1** | Danger test | "It stopped." The head turns 180°. "It watched me for a long time." Then it moves on (false safety). |
| 86.42-93.06 | Journey | Across town to the Tick and Tune Toy Factory, "closed a hundred years ago". The doors open by themselves. |
| 93.06-113.44 | Lair reveal (slowest, most visual stretch) | Marionettes with no strings, teddy bears facing the door, thousands of ticking music boxes, a carousel-sized music box, "tiny dancers". |
| **114.08-120.16** | **Twist 2** | The dancers are the taken kids, shrunk, "forever". "Every kid who'd ever been taken." This answers the opening "it takes you" after about 115 s. |
| **120.64-127.36** | **Emotional peak** | "Dex in his dinosaur pajamas." Max's horrified face. Lullaby points at **an empty brass peg, then at Max**. |
| **127.36** | **Twist 3** | "It knew." The disguise failed. Two-word sentences follow: "I ran." |
| 128.40-131.0 | Chase | Fingers snap "right behind my head"; he dives. |
| 130.32-141.36 | Discovery and flashback | "that's when I noticed something", then "Its crank was slowing down. Tink, tink." Grandpa's rule: "When the song ends, the dancer stops." |
| 141.36-146.80 | Climax action | He jumps on its back and turns the crank backwards. |
| **146.80** | **Twist 4, last beat before the trim** | "The song played in reverse." The reversed onomatopoeia "Knit…" starts at 147.95, and the video is cut mid-word at 148.03. |

Twist and reversal cadence: 45.6, 48.1, 49.6, 79.2 (and 84.7), 114.1, 127.4, 133.2, 146.8. Once the first twist lands, there is a turn roughly every **12-18 s**.

**Compared with the 4-step format in NICHE_NOTES:**
- Rule on the first frame: yes (0.0 s).
- Society: 10.9-20.5 s.
- Person: 23.0 s.
- The "twist at ~30 s" is **late here**:
  - 30 s carries only the plant ("Dex is the opposite").
  - The inciting incident lands at 35.4.
  - The real twist (Dex taken) lands at **45.6 s**.
- The 2:00+ length is carried by **four more reveal and twist blocks** after the first one: the loophole, the monster close-up, the lair, and the chase plus solution.

### Open loops (question opened, then paid)

| # | Opened | Question in the viewer's head | Paid | Gap |
|---|---|---|---|---|
| L1 | 3.75 "it takes you" | Takes you where? What happens to them? | 114.08-120.16 (shrunk dancers on the music box) | ~115 s (the spine of the story) |
| L2 | 4.39 "nobody has ever seen it up close" | What does it look like? | 60.99-78.82 (full description) | ~57 s. The visuals tease it early but the narration withholds. |
| L3 | 9.75 "We call it Lullaby" + "music box song" | Why a music box? | 77.30 (crank: "every turn played one more note"), then the factory (101.8), then grandpa (139.5) | paid in stages |
| L4 | 24.0 "best fake sleeper alive" | Will the skill be tested? Will it hold? | 39.07-41.2 (it works), 79.2-86.1 (it seems to work), 127.36 "It knew." (it fails) | three payoffs, the last one a reversal |
| L5 | 32.19 "Dex can't fall asleep ever" | Dex is in danger | 45.55 "Dex's bed was empty" | 13 s |
| L6 | 35.39 "I heard it" | Will it take Max? | 43.79 (it passes) | 8 s |
| L7 | 45.55 Dex gone | Where is Dex? Can he be saved? | 120.64 (Dex on the peg). Rescue not yet paid. | 75 s, then open at the cut |
| L8 | 48.11 "I didn't fake sleep" | What is his plan? | 49.55 (sleepwalker loophole) | 1.4 s (fast pay that opens a bigger loop) |
| L9 | 79.22 "It stopped." | Has it seen through him? | 84.66 "kept going". Overturned at 127.36. | 5 s |
| L10 | 86.42 toy factory | What is inside? | 93-120 | 7-34 s |
| L11 | 123.20 the empty brass peg | Will Max become a dancer? | not paid (cut) | open |
| L12 | 130.32 "that's when I noticed something" | What did he notice? | 133.20 "Its crank was slowing down" | 3 s |
| L13 | 135.12 grandpa's music box | Why does it matter? | 139.52 "When the song ends, the dancer stops." Applied at 141-146. | 4-11 s |
| L14 | 146.80 "The song played in reverse." | What does reverse do? Do the kids come back? | not paid (cut) | open |
| L15 | 16.79 "every parent… sings… the exact same lullaby" | Why the same lullaby? | not paid yet (probably part of the ending) | open |

---

## 3. Numbers

- **Runtime analysed:** 148.0 s, all narrated. The first word starts at 0.0 s and the cut lands mid-word at 147.95. No silent intro, no music-only breaks.
- **Total words:** **599** complete words, plus the cut fragment "Knit".
- **Pace:**
  - **243 wpm overall**, about **250 wpm while speaking**. Pauses of 0.3 s or more add up to only about 5.5 s.
  - The longest gap between words is 0.80 s (after "sleepwalkers.", 52.75). There are no dramatic pauses anywhere; even "It knew. / I ran." are 0.56 s apart.
  - This is a sped-up or very fast read. Normal storytelling is about 160-190 wpm.
- **Pace by section:**

| Section | Time | Sentences | Words | wpm | Mean sentence length |
|---|---|---|---|---|---|
| A rule + world | 0.0-22.9 | 12 | 93 | 243 | 7.8 |
| B person + friend | 22.9-35.3 | 8 | 53 | 257 | 6.6 |
| C inciting night + loss | 35.3-48.0 | 9 | 55 | 260 | 6.1 |
| D loophole + plan | 48.0-60.9 | 4 | 47 | 219 | 11.8 |
| E monster close-up | 60.9-86.3 | 10 | 107 | 253 | 10.7 |
| F factory + lair | 86.3-123.1 | 11 | 142 | 232 | 12.9 |
| G chase + solution | 123.1-148.0 | 12 (+cut) | 102 | 246 | 8.5 |

  - Setup and action use short sentences (about 6-8 words). Description and reveal use long, comma-chained ones (11-13 words). The reveal blocks (E+F) take **42%** of the runtime.
- **Sentence length** (66 sentences):
  - median **8** words, mean 9.1, minimum 2, maximum 26.
  - 1-2 words: 6 (9%); 3-5 words: 14 (21%), so **1-5 words = 30%**.
  - 6-10 words: 39%; 11-15 words: 15%; 16 or more: 16%.
  - Sentences get slightly longer in the second half (median 7, then 8).
- **Sentence openers:**
  - "And" 5, "So" 2, "Then" 2, "Because" 1, "But" **0**. That is 10 of 66 (15%) starting with a connective.
  - Other frequent openers: "The" 6, "Its" 5, "I" 5, "It" 3.
  - "So" marks the cause-and-effect steps: "So in our town" (10.87) and "So at midnight" (54.75).
- **Narrative person:**
  - **2nd person: 5** (you, you're). All of them are in the first 22.6 s, inside the rule block, so the viewer is the potential victim.
  - **1st person singular: 28** (I 13, my 8, me 4, I've 2, I'm 1). All from 22.99 on.
  - **1st person plural: 3**: "We call it Lullaby", "our town", "our big math test". This is the voice of the community.
  - **3rd person:** the creature is "it/its" (about 20) or "Lullaby" (5). It is never "he" or "she", which keeps it an object or toy.
- **Dialogue:**
  - 2 quoted lines from 1 speaker (Grandpa, flashback, 137.12-141.3).
  - 14 quoted words: 2.3% of the words, 2.8% of the runtime.
  - Nobody talks in the present-day scenes. Max narrates everything.
- **Information rate:**
  - A new sentence, and with it a new fact or image, every **1.76 s** (median; mean 2.26, longest 6.3 s).
  - Scene-cut detection finds **70 cuts in 144 s of video**, so a new shot about every **2.1 s**.
  - The factory uses long moving shots (3-10 s: 91.1, then 98.7, 101.8, 105.9, 109.9, 120.5).
  - The chase cuts every 1.0-1.6 s (127.8-146.7).
- **Repeated words and phrases (motifs):**
  - **Sound motif:** "tink" ×9 (4, then 3, then 2), plus "knit" ×1 reversed. "music box(es)" ×7, "song" ×5, "Lullaby" ×5 (and "lullaby" once as a common noun). About 27 sound-motif words in 600.
  - **Sleep family** ×10: asleep 3, sleep 2, sleepwalkers 2, sleeper, sleepovers, sleepwalked.
  - **night/midnight/bedtime/bed** ×11.
  - **Body-performance phrases:**
    - "Slow breathing" ×2 (25.55, 39.63)
    - "(One) arm (hanging) off the bed" ×2 (26.27, 40.43)
    - "arms (straight) out" ×2 (56.83, 82.18)
    - "drool/drooling" ×2 (27.55, 81.54)
  - **Universalisers:** "every" ×5 (every parent, every night, every turn, every single one, every kid); "ever" ×4 (nobody has ever seen, can't fall asleep ever, biggest I've ever seen, who'd ever been taken).
  - **Movement words:** "around" ×5, "toward" ×4, "turn/turned/turning" ×5.
  - **Creature anatomy:** "head" ×5, "long" ×4, "crank" ×3 (with "rusty crank" ×2), "white" ×2, "fingers" ×2.
  - "tiny" ×3 (tinkling song, bit of drool, dancers). "Dex" ×5, "Max" ×2.
- **Numbers and specific details:**
  - Spoken: midnight ×2, "five years", "ten feet tall" (caption "10"), "a hundred years ago" (caption "100"), "thousands of them", "one more note", "one long finger", "the size of my thumb", "both hands", "one arm", "the night before our big math test".
  - On screen only: "LIGHTS OUT 8:00 PM", alarm clock "12:00", calendar "OCTOBER 24 – MATH TEST!", the clock tower at 12, "TICK & TUNE TOY CO.".
- **Similes:** "thin as a lamppost", "like it was listening", "like a puppet's", "big as a carousel", "the size of my thumb". Each one is a concrete household image that is easy to animate.

---

## 4. Devices (what keeps people watching)

1. **First-frame rule wording (0.00).** "In this world, something walks the streets at midnight, and if you're awake when it passes, it takes you."
   - It is a condition followed by a fatal consequence, in 19 words.
   - The creature is only "**something**", so the mystery is in the first clause.
   - "**you're**" makes the viewer the subject.
   - The picture (in our copy) is the creature's face at a bedroom window, so the rule plus a face give two hooks at once.
2. **Rule restated as a law, with a book-end (20.55-22.84).** "The rule is simple. When you hear the music box, be asleep." The rule is said twice: as a threat (0 s) and as a command (21 s). The **window lights switching off** on "asleep" closes the world block like a full stop.
3. **Mystery lines (4.39-6.23).** "You see, nobody has ever seen it up close. You only hear it." This withholds the look for about 57 s, while the visuals give the viewer glimpses: a tiny figure, the hem, the crank.
4. **Sound-first identity (7.03).** "A tiny tinkling music box song getting closer." The monster is a sound, so every "tink" later on works as an alarm. The **captions put the sound on screen** ("tink" as a word).
5. **Ironic naming (9.75).** "We call it Lullaby." A comforting word for a child-taker. This is the cute-creepy contrast in one word.
6. **Society montage in short parallel sentences (10.87-20.55).** "Sleepovers are banned. Some kids sleep in their closets. Some families nail the windows shut."
   - Anaphora: "Some… Some…".
   - Each line gets its own picture, two of them in-world signs.
   - It makes the world feel lived in, in under 10 s.
7. **In-world signage as a second caption.** "TOWN LAW… NO EXCEPTIONS" (11), "SLEEPOVERS ARE BANNED by order of the town" (12.6), "MATH TEST!" calendar (35.4), "TICK & TUNE TOY CO." (89). These state the rule visually for muted viewers and add details for repeat viewers.
8. **A hero built against the rule (22.99).** "the best fake sleeper alive". His skill is exactly what the rule rewards, so the audience immediately wonders whether it will be tested.
9. **A three-item "how-to" (25.55-27.55).** "Slow breathing. One arm hanging off the bed. A tiny bit of drool." These are body cues that are funny, specific and easy to animate. They are planted so they can be repeated word for word under pressure.
10. **Foil character planted as the victim (30.67-33.55).** "My best friend Dex is the opposite. Dex can't fall asleep ever." The viewer predicts the danger 13 s before it happens, which is dramatic irony.
11. **Humour beat before the horror (33.55).** "He counts sheep until the sheep get bored." The laugh resets attention right before the inciting night.
12. **Grounded kid stakes, "last night" immediacy (35.39).** "Then one night, the night before our big math test, I heard it." A mundane anchor (a test) makes it relatable. The calendar shot shows a specific date. Past-tense first person is how you tell a story to a friend.
13. **Plant, then exact callback under pressure (39.07-40.43).** "I went still. Slow breathing. Arm off the bed." This is the same phrasing as the setup, which rewards the viewer and builds tension through repetition.
14. **Proximity sound design in the words (41.23).** "The song got louder, right outside my window, then softer." The audience hears the danger pass, and the window shot of the face pays off the opening frame.
15. **Misdirection: relief, then a gut punch (43.79-45.55).** "Moving down the street, toward Dex's house." … "In the morning, Dex's bed was empty."
16. **Sensory proof of loss (47.07).** "The sheets were still warm." One tactile detail does the emotional work: he was just here.
17. **Character reversal (48.11).** "That night, I didn't fake sleep." The hero gives up his safe skill and the story changes from survival to rescue.
18. **Rule within the rule, and loophole logic (49.55-54.35).**
    - "Because there's one more thing everybody knows about Lullaby: it never takes sleepwalkers. Sleepwalkers are asleep."
    - The phrase "one more thing everybody knows" adds a rule mid-story without breaking the world.
    - The logic is childlike and airtight.
    - It is shown on screen (Lullaby ignores a sleepwalking kid) **before** Max relies on it.
19. **Ticking clock, made of a time:** "at midnight" (54.75), with the alarm clock showing 12:00.
20. **Delayed full reveal, piece by piece (60.99-78.82).**
    - Size, then dress, then head, then fingers, then crank. Each one is its own close-up shot.
    - The comma-chained long sentences (21-26 words) slow the viewer down to look.
    - The similes make each feature instantly picturable.
21. **Mechanic planted as an innocent detail (77.30).** "Every turn played one more note of the song." This is the key to the climax (133-146), disguised as atmosphere.
22. **Held-breath beat (79.22-84.66).** "It stopped. Its head turned all the way around toward me. … It watched me for a long time." A 2-word sentence plus an uncanny 180° head turn, then false safety: "Then it turned back around and kept going."
23. **New location with history (86.42).** "…the old Tick and Tune Toy Factory, the one that closed a hundred years ago." The specific name and the age suggest backstory and depth. The clock tower shows midnight again.
24. **Lair inventory of creepy-cute detail (93.06-113.44).** "Marionettes… swaying, with no strings attached to anything", "teddy bears… all facing the door", "thousands of them, every single one ticking". Each item is an animated image with one wrong detail in it (no strings, all facing the door, all ticking).
25. **Twist reframe (114.08-120.16).** "tiny dancers" becomes "Kids in pajamas, shrunk down to the size of my thumb, twirling around and around, forever." "Every kid who'd ever been taken." This pays off the opening "it takes you" and makes the word "dancers" sinister in hindsight. "forever" adds permanence.
26. **Personal callback at the emotional peak (120.64).** "Dex in his dinosaur pajamas." The onesie was **only shown** at 30.7 s, never mentioned. The narration names it now, which rewards attentive viewers.
27. **Stakes made visible (123.20).** "toward an empty brass peg and then toward me." No words of threat are needed: the empty slot is his.
28. **Reversal in two words (127.36).** "It knew." The hero's core skill fails, overturning L4 and L9. It is followed by "I ran.", two 2-word sentences in a row, the fastest beat of the video.
29. **Narrow escape and cliffhanger phrasing (128.40-130.32).** "Its fingers snapped shut right behind my head." Then the micro-loop "and that's when I noticed something."
30. **Countdown by onomatopoeia.** The "tink" count shrinks: 4 (37.8), then 3 (76.3), then **2** (134.5, "Its crank was slowing down"), then the reverse ("Knit", 147.95). The sound itself is the ticking clock.
31. **Generational wisdom through flashback dialogue (135.12-139.52).** "Here's the thing about music boxes, Max… When the song ends, the dancer stops."
    - An elder hands over the rule that solves the plot.
    - The warm daytime flashback is the only bright interior in the second half.
    - It is a second rule within the rule, introduced right before it is needed. Weak on its own, but it rhymes with the planted "every turn played one more note".
32. **Active climax with physical specifics (141.36).** "I jumped onto its back, grabbed that rusty crank with both hands, and I turned it backwards." Three verbs in a row; "that rusty crank" calls back 74.27.
33. **Cliffhanger at the cut (146.80-147.95).** "The song played in reverse." Then "Knit…" (caption). Because of the trim, the outcome is unknown. The reversed word is a clever caption-level device (see 34).
34. **Sentences built for word-by-word captions.**
    - One centred word at a time, with no punctuation.
    - Mostly monosyllables and concrete nouns that read as single-word captions: "drool", "closets", "crank", "pajamas", "sleepovers".
    - Numbers are shown as digits when they are big or impressive ("10", "100"). Small counts stay words ("five").
    - Onomatopoeia gets its own caption beats ("Tink", "tink"…), and the reversal is shown by spelling it backwards ("knit").
    - Comma chunks of 2-4 words ("ten feet tall, / thin as a lamppost, / in a long white nightgown") match the 2 s shot rhythm.
35. **Picture matches every noun.** Almost every sentence gets a literal shot of what is said: sign, closet, nailed window, sheep, calendar, alarm clock, doll head, fingers, crank, factory sign, marionettes, bears, dancers, the empty peg. This works as a storyboard checklist: one sentence, one shot.
36. **Light and colour storytelling.** Night purple-blue for the world. Daylight for the loss (Dex's house, 45.6). Warm golden light for grandpa's flashback (137). The factory is dark red brick and violet.

---

## 5. How it probably continues (GUESS, inferred from the setup)

The cut comes at 148 s. Two things tell us how much is missing:
- If the source is a YouTube Short (3:00 cap), **at most about 30 s remain**.
- The brief says 1-2 minutes were trimmed. If that is right, some of the remaining time may be outro or extra story.

These elements are planted but not paid: reverse song, empty peg, "dancer stops", same lullaby for all parents, a 100-year-old factory, Dex on the peg, the math test, bedtime law, sleepovers banned.

The most likely continuation:
1. **The reversal undoes the taking.** "Knit… knit…" The notes play backwards. Lullaby stiffens and winds down: "when the song ends, the dancer stops". It may shrink or freeze into a figurine on the empty brass peg that was meant for Max, so the trap flips onto the trapper. The tiny dancers spin backwards and grow back to full size, Dex included.
2. **Mass homecoming.** Every kid "who'd ever been taken" walks out, some in **old-fashioned pyjamas from a hundred years ago**. This would pay off the factory's age, and possibly the townsfolk recognising long-lost relatives. There is also a possible **generational twist**: one of the returned kids is someone the town knew. Another option is that Grandpa's warning came from experience: he was once taken, or once a "dancer".
3. **The world changes.** Morning comes, bedtime is no longer the law, sleepovers are allowed again. A light payoff of the math test is likely ("we still had to take the math test" or "we slept through it").
4. **Sting or sequel hook (common in the niche).** For example: Max keeps the little Lullaby music box on his shelf, and one night he hears "tink…" again. Or the parents' "exact same lullaby" turns out to be the music-box tune, so the lullaby the parents sang was what kept it bound.

How confident I am:
- Kids freed and Lullaby stopped: high.
- Lullaby ends up on the empty peg or as a figurine: medium.
- A closing "it's not over" sting: medium.
- Grandpa having history with Lullaby: low to medium.

---

## 6. Why it works, and where it is weak

**Retention**
- The sentence-1 hook has three things on screen together: a rule with a death-like consequence, an unseen "something", and "you".
- Loops nest at three time scales:
  - Long: L1, "takes you where?" is held for 115 s.
  - Medium: Dex's fate, about 75 s.
  - Micro: "that's when I noticed something", paid in 3 s.
- Something is always unresolved.
- New information arrives every ~1.8 s and a new shot every ~2.1 s. The narration never stops, so there is no gap to scroll away in.
- After the first twist (45.6 s) a reversal lands every 12-18 s. The story keeps changing mode:
  - survival
  - loss
  - plan
  - infiltration
  - discovery
  - capture threat
  - chase
  - solution
  - climax
- A sound motif ("tink") stands in for an audio cliffhanger. Each new "tink" means danger, and the shrinking count works as a countdown.

**Emotion**
- A best friend is taken, with the tactile line "The sheets were still warm".
- The hero chooses to risk himself instead of hiding.
- The peak puts an attachment object (the dinosaur pyjamas) next to the hero's own empty slot.
- The grandparent flashback adds warmth right before the climax.
- The cute-creepy register (a lullaby, a music box, teddy bears, a cracked doll) is scary, but safe enough for a young Roblox audience.

**Shareability**
- The concept fits in one breath: "a monster that only takes kids who are awake, and the kid pretends to sleepwalk". It invites "what would you do" comments.
- Clever logic loopholes ("sleepwalkers are asleep", "turn the crank backwards") are the kind of thing viewers repeat.
- A strong signature image (the cracked doll head on a 10 ft body with a crank) makes a natural thumbnail.

**Weak spots**
- **Late first twist.** The niche notes say ~30 s; here the first twist is at 45.6 s. From 22.9 to 35.3 s it is pure character setup (charming, but no threat on screen apart from the plant).
- **Relentless pace, about 243-250 wpm, with no pause longer than 0.8 s.** It is breathless. Big beats ("Dex's bed was empty", "It knew.") get no room. It is hard for a human to read at this speed without sounding rushed. If we record ourselves at a natural 170-190 wpm, a 2:15 short holds about **380-430 words**, not 550-600, unless we speed up the voice in the edit.
- **Convenient solution.** Grandpa's rule (137 s) is introduced only 9 s before it is used. The crank plant at 77 s softens this, but the grandpa line itself is never set up earlier. A deus-ex-memory.
- **Logic gaps.** If Lullaby "never takes sleepwalkers", why does "It knew." lead to an attack? The script never explains how it knew. Why did it let Max follow it across town? It could have been leading him, but the script never says so. This is fine for kids, but comments will poke at it.
- **The long descriptive middle (86-114 s).** Five sentences of 12-18 words describing the lair, with long camera moves. It is atmospheric but it is the slowest information stretch, and the riskiest point for drop-off before Twist 2 lands.
- **Thin agency for the second character.** Dex is only a victim and a costume. He has no line and no choice.
- **The "exact same lullaby" plant (16.8 s) is unused up to the cut.** It may pay off in the ending. If it does not, it is a dangling thread.
- **Our copy has no picture for the first 3.7 s.** We cannot judge the true first frame. From 3.7 s the first visible image is the window peek, which is the same set as 41-43 s, so it probably works as a flash-forward hook.

### Mechanics worth reusing (structure only; invent our own content)

- **Rule:** state it once as a threat with "you" and once as a two-clause command. End the world block with a visual "full stop" (lights out).
- **Hero and foil:** give the hero a skill that matches the rule exactly, and a foil who is the rule's natural victim. Plant body-specific cues and repeat them word for word under pressure.
- **Mid-story rule:** add one "one more thing everybody knows…" loophole mid-story, and **show it working on someone else first**.
- **The monster:** give it a mechanical, audible tell, and make that tell (a) a countdown and (b) the climax solution. Plant the mechanic as innocent description.
- **Payoffs:** pay the first-sentence threat ("it takes you") with a visual answer around the 75-80% mark. Pair the emotional peak with the hero's own empty slot or fate.
- **Captions:** big numbers as digits, onomatopoeia as its own caption beats, and a caption-level twist (a word spelled backwards).
- **Fixes to make in ours:**
  - Land the first real twist by about 30 s.
  - Allow 2-3 deliberate pauses of about 0.6-1.0 s on the big beats.
  - Plant the final-solution rule at least 30 s before it is used.
