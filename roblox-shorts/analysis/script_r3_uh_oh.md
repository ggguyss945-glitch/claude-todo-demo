# Script analysis: r3 "Uh Oh"

Reference only. Lines are quoted for analysis, never for reuse. We borrow mechanics, not content.

- **Source:** `ref/r3_uh_oh.mp4` (720x1280, 30 fps, 111.03 s; trimmed, so the ending is missing).
- **Inputs:**
  - ASR word times (`asr/r3_uh_oh.json`, 474 tokens).
  - Both frame sheets.
  - About 700 extra frames, all in `scratchpad/rbx/work/r3script/`:
    - a 5 fps strip of the caption band over the whole video (`bandsheet_*.png`), used to check every word against the burned-in caption;
    - one frame per sentence (`sentsheet_*.jpg`);
    - 0.6 s close-up windows for 22-36 s, 45-57 s, 62-80 s and 82-111 s (`win_*.jpg`);
    - shot-cut detection (`cuts.txt`).
- **Timing caveats:**
  - In our copy the **video stream starts at 0.933 s** and the audio starts at 0.00 s, so we cannot see the picture for the first 0.93 s. That covers "In my world," (0.03-0.75). The first visible frame already shows the caption "your", followed by "superpower".
  - The audio confirms "In my world," is spoken: there are three syllable bursts, then a comma pause at 0.62-0.72 s before "your" at 0.75.
  - The labels on the frame sheets run about 1 s early (the fps-filter offset). The 0:00 tile already shows "superpower", and the 0:32 tile shows "first" (33.0 s).
  - All times below come from the ASR word starts, cross-checked with the caption band. Captions and ASR agree to within about 0.2 s from 1 s onwards.
- **Format:**
  - One narrator: the unnamed hero, a kid, in first person. Present tense for the world, then past tense from "Then came the field trip" (52.3 s).
  - The only viewer address is the rule's "your … you" and the aside "You see".
  - A music bed runs under everything: silencedetect finds no silence at -30, -35 or -40 dB.
  - The voice never stops. The longest gap between words is 0.64 s.
  - The narrator acts all the dialogue himself. Rough pitch with the music bed: about 210 Hz median while narrating, about 280 Hz on the "uh-oh!" screams, about 420 Hz on "Mr. Baker, stop!".

### ASR corrections (checked against the burned-in captions)

| t (s) | ASR | Corrected / note | Evidence |
|---|---|---|---|
| 0.03-0.75 | "In my world," | kept | No picture in our copy before 0.93 s. The audio energy profile matches 3 syllables plus a comma pause before "your". |
| 18.11 | "mama" | "Mama" | The caption shows "Mama" capitalised. |
| 29.75 | "newborn" | "newborn" | The caption capitalises it ("Newborn"). This is auto-capitalisation, not a name. |
| 45.35 | "mom says" | "Mom says" | Used as a name. |
| 47.67 | "a hundred" | "a hundred" (spoken) | The caption renders it as the digits **"100"**. |
| 56.07 | "river" | "river" | The caption shows "River" capitalised (an auto-caption quirk). |
| 37.19, 38.23, 39.91, 46.87, 70.75, 82.99, 90.85, 94.69, 98.29, 98.77, 99.33 | "uh-oh" (one token) | "uh-oh" | Every time, the caption splits it into **two pages, "uh" then "oh"**. |
| 86.91-87.15 | "Mr. Baker" | confirmed | Caption pages "Mr" and "Baker". The picture is a bus driver in a blue beanie. |
| 32.55 / 100.05 | "Leo's" / "20th" | confirmed | The caption shows "Leo's" and "20th" as digits. |
| 24.11-25.35 | three ASR sentences: "…yelling fly!" "Fly!" "Say fly!" | one sentence with a quoted chant | This is a judgement call and no times change. Raw ASR gives 62 sentences; the merged count is 59. |
| 86.91-88.85 | "Mr. Baker, stop!" + "I screamed at the bus driver." | one sentence with its speech tag | Same reason. |

No real mishearings were found. Every content word matches the caption band.

---

## 1. Clean transcript, numbered, tagged, with picture

Tags: RULE / CONSEQUENCE / PERSON / ESCALATION / TWIST / REVEAL / EMOTION / CALLBACK / CLIFFHANGER / DIALOGUE / DESCRIPTION. I also mark plant (a setup that pays off later), mystery (an open question) and reversal.

| # | Start (s) | Sentence | Tag(s) | Picture at that moment |
|---|---|---|---|---|
| 1 | 0.03 | In my world, your superpower is the first word you ever said. | **RULE** | Our copy has no picture until 0.93 s. The first visible frame shows a kid in a black hoodie hovering over a crosswalk with sparkles, and a fire-haired kid behind him. He lifts off into the sky at about 1-2 s. |
| 2 | 3.07 | So every parent in town spends a whole year trying to get their baby to say fly. | CONSEQUENCE | A yellow "noob" dad with a mustache holds a protest sign reading "FLY!" in front of a house and car. |
| 3 | 6.99 | You see, kids whose first word was up can fly. | CONSEQUENCE / DESCRIPTION (power example 1) | The hoodie kid soars over the treetops with a sparkle trail. |
| 4 | 9.23 | Kids who said hot have fire hands. | DESCRIPTION (example 2) | A red spiky-haired kid in red, grinning, with flames on his hands. |
| 5 | 10.99 | A kid in my class said ball, so now he bounces everywhere he goes. | DESCRIPTION (example 3) | A kid mid-bounce, high up a street-lamp pole in the suburb. |
| 6 | 13.95 | A girl down the street said doggy. | DESCRIPTION (setup) | A blonde girl in a yellow shirt waves on her front lawn. |
| 7 | 15.47 | She turns into a golden retriever when she sneezes. | DESCRIPTION (punch) | A blocky golden retriever with pink "sneeze" sparkles. |
| 8 | 17.55 | And kids who said mama can make their mom appear right next to them anywhere, anytime. | DESCRIPTION (setup) | A nerdy kid with glasses and a red bow tie spreads his arms. A pink flash, and his mom pops in beside him. |
| 9 | 21.31 | Their moms hate it. | CONSEQUENCE / EMOTION (deadpan punchline) | Close-up of a frazzled mom: messy hair, crooked tie, stained shirt, gritted teeth. |
| 10 | 22.35 | Parents stand over cribs all day yelling, "Fly! Fly! Say fly!" | CONSEQUENCE + DIALOGUE (parents, chorus) | A nursery: a red-haired mom and the yellow dad lean over a wooden crib. A baby-POV shot looks up at them under a ceiling fan as they shout. |
| 11 | 25.91 | And nobody ever says anything bad in front of a baby. | CONSEQUENCE (social taboo, a rule-within-the-rule) | The same crib shot, parents frozen wide-eyed. |
| 12 | 28.31 | One dad stubbed his toe next to his newborn once. | CONSEQUENCE (anecdote setup) | The yellow dad in a tank top hops in pain beside a coffee table. |
| 13 | 30.55 | We don't talk about what that kid can do. | ESCALATION (dark-joke jolt) / mystery | A baby in a crib with glowing red eyes, an evil grin and red mist. Flash and glitch cuts at 30.97, 31.07 and 31.13. |
| 14 | 32.07 | My best friend Leo's first word was no, so he can make a force field. | PERSON (helper) / plant | A playground: the hero (orange spiky hair, cream sweater) stands next to Leo (brown hair, blue shirt, arms crossed). |
| 15 | 35.35 | Nothing gets through it. | DESCRIPTION / **plant** (an absolute statement) | Leo throws up a translucent blue bubble and an orange ball bounces off it. |
| 16 | 36.31 | My first word was uh-oh. | **PERSON** (the hero; title drop) | Close-up of the hero grinning on "uh … oh". |
| 17 | 37.75 | Nobody knows what uh-oh does. | mystery (the title question) | The grin drops. He looks worried, hand to his head. |
| 18 | 38.95 | The kids at school call me uh-oh, but some weird stuff does happen around me. | EMOTION (outsider) / mystery | Wide shot: a group of kids far off by the slide while the hero stands alone. He shrugs on "weird stuff". |
| 19 | 42.15 | Every time I say it, I get this strange feeling, like I've done this all before. | **plant** (déjà-vu clue) | Close-up side-eye, then a sad frown on "feeling". |
| 20 | 45.19 | And Mom says that when I was little, I said uh-oh about a hundred times a day, but I never once broke anything. | **plant** (clue) / flashback | A kitchen: Mom (red braids, gingham dress) beside the toddler hero in a high chair with a blue sippy cup. The toddler smirks. |
| 21 | 49.91 | Not a cup, not a plate, not one single thing. | DESCRIPTION (tricolon) | The blue cup lies on the floor, intact, then a yellow plate on the floor. The toddler laughs and Mom shrugs. |
| 22 | 52.31 | Then came the field trip. | ESCALATION (inciting incident; tense switch) | A yellow school bus on a forest road. |
| 23 | 53.43 | Our whole class on the big yellow bus, crossing the bridge over the river. | DESCRIPTION (setting and stakes) | Inside the bus: rows of green seats full of classmates. Then the bus side-on, driving onto the bridge. |
| 24 | 56.39 | Leo was sitting next to me, making a tiny force field around his sandwich. | **plant** (the anchor object) | Over-the-shoulder close-up of Leo's sandwich inside a small blue bubble. |
| 25 | 59.51 | And that's when the truck in front of us slammed on its brakes. | ESCALATION | A white box truck braking ahead on the bridge. |
| 26 | 61.99 | The bus swerved. | ESCALATION | The front of the bus swerves. |
| 27 | 62.87 | It smashed right through the railing. | ESCALATION | The bus bursts through the concrete railing as chunks fly. |
| 28 | 64.31 | And for one second, we were flying. | ESCALATION / CALLBACK (the "fly" motif, now a disaster) | The bus airborne against a blue sky, debris around it. |
| 29 | 66.03 | Kids were screaming, backpacks were floating, and the river was coming up fast. | ESCALATION (sensory tricolon) | Inside: backpacks float and Leo's bubble is visible. Then a windshield POV of the river rushing up. |
| 30 | 69.31 | And without even thinking, I yelled, "Uh-oh!" | DIALOGUE (hero) / **EMOTION peak** | Extreme close-up of the hero screaming, eyes huge. A white flash on "oh". |
| 31 | 71.39 | And everything went backwards. | **TWIST 1** | The bus flies backwards up out of the river. |
| 32 | 72.59 | The water pulled away. | TWIST / DESCRIPTION | The bus rises as the water recedes. |
| 33 | 73.55 | The bus flew up, the railing put itself back together, and suddenly we were driving on the bridge again. | TWIST / DESCRIPTION (rewind tricolon) | The railing pieces reassemble, then a side view of the bus driving normally. |
| 34 | 77.71 | Leo was making a force field around his sandwich. | **CALLBACK** (repeat line and repeat shot) | The same over-the-shoulder sandwich-in-bubble framing as S24. The picture itself is déjà vu. |
| 35 | 79.79 | I knew that sandwich! | REVEAL (recognition) | The hero's eyes narrow. |
| 36 | 80.75 | I'd seen this exact moment five seconds ago. | REVEAL (the power's limit) | Close-up of the hero, one eye rimmed in red (shock). |
| 37 | 82.99 | Uh-oh doesn't mean oops, it means undo. | **REVEAL** (pays off the title loop) | The camera pushes in on the hero in his seat. A classmate with glasses peeks over the seat behind. |
| 38 | 85.39 | The truck slammed on its brakes again. | ESCALATION / reversal (it repeats) | Windshield POV: the truck braking ahead. |
| 39 | 86.91 | "Mr. Baker, stop!" I screamed at the bus driver. | DIALOGUE (hero) | The hero half-stands in the aisle yelling. Cut to Mr. Baker (blue beanie, glasses, grey mustache) panicking at the wheel. |
| 40 | 89.25 | Too late. | ESCALATION (failure 1) | Wide shot: the bus hits the railing again. |
| 41 | 89.73 | Through the railing. | ESCALATION | Debris. The bus tips toward the water. |
| 42 | 90.37 | The river. | ESCALATION | Windshield POV of the river. |
| 43 | 90.85 | Uh-oh. | DIALOGUE (hero) | Screaming close-up with a floating backpack and a white flash. |
| 44 | 91.49 | Five seconds back. | DESCRIPTION (reset) | Wide shot: the bus on the bridge again. |
| 45 | 92.29 | This time, I grabbed the steering wheel. | ESCALATION (attempt 2) | The hero lunges at the wheel beside Mr. Baker. |
| 46 | 93.89 | We still went over. | ESCALATION (failure 2) | Wide shot: the bus goes off the bridge. |
| 47 | 94.69 | Uh-oh! | DIALOGUE (hero) | Screaming close-up. |
| 48 | 95.33 | Back again. | DESCRIPTION (reset) | The bus driving on the bridge. |
| 49 | 95.89 | I tried everything. | EMOTION (frustration) | The hero frowning, defeated. |
| 50 | 96.77 | Five seconds isn't a lot of time. | ticking clock | The bus through the railing again, then diving nose-first. |
| 51-53 | 98.29 / 98.77 / 99.33 | Uh-oh. Uh-oh. Uh-oh. | DIALOGUE (hero; montage) | Three rapid screaming close-ups linked by whip-pan flashes. |
| 54 | 99.81 | By the 20th try, I was dizzy. | EMOTION (exhaustion) / time compression | Spiral "dizzy" eyes. |
| 55 | 101.49 | I knew every scream by heart. | EMOTION | The hero sunk low in his seat. The glasses classmate peeks again. |
| 56 | 102.93 | Then I looked at Leo, at his force field, around his sandwich. | **CALLBACK** (third time) / turn | The hero glances over, then an over-the-shoulder shot of the bubble, then an extreme close-up of the sandwich in the force field. |
| 57 | 105.49 | "Leo," I said, "when I say now, make the biggest force field you've ever made." | DIALOGUE (hero) / plan (pays off the S15 plant) | The hero turns to Leo, determined, talking. |
| 58 | 109.01 | "Right next to the railing." | DIALOGUE (hero) | The hero leans toward Leo. |
| 59 | 109.97 | He looked at me like I was crazy. | **CLIFFHANGER** (last beat before the trim) | Leo gives a skeptical side-look, sandwich bubble in hand. The video ends at 111.03. |

---

## 2. Beat map

| Time (s) | % of 111 s | Beat | What happens |
|---|---|---|---|
| 0.03-2.75 | 0-2% | **Rule** | "In my world, your superpower is the first word you ever said." "superpower" lands at 0.91 and the rule is complete at **"said" (2.75)**. |
| 3.07-32.07 | 3-29% | **Consequence (society)** | 12 sentences in 29 s. A "gag ladder" of first-word powers, each one sillier than the last: up→fly, hot→fire hands, ball→bounce, doggy→dog when sneezing, mama→summon Mom ("Their moms hate it"). Then the social laws: parents chant at cribs, and nobody says anything bad near a baby. |
| 30.55 | 28% | **The ~30 s jolt** (tone reversal) | "We don't talk about what that kid can do." The cute world turns creepy for 1.5 s (red-eyed baby, glitch flashes). This is the slot the niche notes reserve for a twist. Here it is a hook refresh, not the plot twist. |
| 32.07 | 29% | **Person A: the helper** | "My best friend Leo's first word was no, so he can make a force field. Nothing gets through it." His power is planted before it is needed. |
| **36.31** | 33% | **Person B: the hero** | "My first word was uh-oh." Title drop. Then at 37.75: "Nobody knows what uh-oh does." The hero is never named. His nickname is the title. |
| 38.95-51.83 | 35-47% | Character and clues | Outsider ("kids call me uh-oh"). Clue 1, déjà vu (42.15). Clue 2, "never once broke anything" (45.19-51.83), shown as an intact cup on the floor. |
| **52.31** | 47% | Inciting incident | "Then came the field trip." The switch from present to past tense: the story proper starts here. |
| 56.39 | 51% | Plant: the anchor object | Leo's "tiny force field around his sandwich". |
| 59.51-69.31 | 54-62% | Disaster | The truck brakes, the bus swerves and smashes through the railing. At 64.31: "for one second, we were flying." Screaming, backpacks floating, the river coming up fast. |
| **69.31-71.39** | 62-64% | **Emotional peak + Twist 1** | "I yelled, 'Uh-oh!'" Scream close-up and white flash, then "And everything went backwards." (71.39) |
| 71.39-77.39 | 64-70% | Rewind spectacle | The water pulls away, the railing rebuilds, the bus is driving again. |
| 77.71-82.67 | 70-74% | Recognition | The sandwich line and shot repeat word for word. "I knew that sandwich!" "…five seconds ago." |
| **82.99** | 75% | **Reveal** (title loop paid after 45 s) | "Uh-oh doesn't mean oops, it means undo." |
| **85.39** | 77% | Reversal: the loop | "The truck slammed on its brakes again." Undoing does not equal saving. |
| 86.91-99.81 | 78-90% | Escalating failures, compressed | Attempt 1 is shouting at the driver: "Too late." Attempt 2 is grabbing the wheel: "We still went over." Then "I tried everything", three uh-ohs in 1.5 s, and "By the 20th try…" |
| 99.81-102.53 | 90-92% | Low point | "I was dizzy." "I knew every scream by heart." |
| **102.93** | 93% | Turn (the idea) | "Then I looked at Leo, at his force field, around his sandwich." This is the third sandwich callback and the anchor becomes the key. |
| 105.49-109.49 | 95-99% | Plan | "…make the biggest force field you've ever made. Right next to the railing." Pays off "Nothing gets through it" (planted at 35.35). |
| **109.97-111.03** | 99-100% | **Last beat before the trim (cliffhanger)** | "He looked at me like I was crazy." The new obstacle is that the helper doesn't believe him, and there are only five seconds to convince him. |

**Twist and reversal cadence:** 30.6 (tone jolt), 45.2 (clue reversal: uh-oh but nothing broke), 64.3 (disaster), **71.4 (twist)**, **83.0 (reveal)**, 85.4 (it repeats), 89.3 ("Too late"), 93.9 ("We still went over"), 99.8 (20 tries), 102.9 (the idea), 110.0 (the skeptic).

The first half (0-52 s) runs on gags and mystery, with no turns. Once the disaster hits, the turns come **every 4-6 s**.

**Against the 4-step format in NICHE_NOTES:**
- Rule on the first frame: yes.
- Society: long, 3-32 s.
- Person: 32 s (the helper) and 36 s (the hero).
- **The plot twist is late:** 71.4 s, with the reveal at 83 s.
- The 30 s slot carries only a dark-joke jolt (30.6). The 37 s slot carries the title mystery.
- What holds the 36-71 s stretch is the open question "what does uh-oh do?", plus two clues and the disaster set-piece.

### Open loops (question opened, then paid)

| # | Opened | Question in the viewer's head | Paid | Gap |
|---|---|---|---|---|
| L1 | 0.91 "your superpower is the first word you ever said" | What would mine be? What is the narrator's? | 37.19 "My first word was uh-oh." (The viewer's own version is never paid. It goes to the comments.) | 36 s |
| L2 | 3.07 "say fly" | Why fly? What do the other words do? | 6.99-21.31, paid in instalments of one example every 2-4 s | 4-18 s |
| L3 | 30.55 "We don't talk about what that kid can do." | What did the toe kid get? | **not paid** in the visible part. Probably a dangling gag. | open |
| L4 | **37.75 "Nobody knows what uh-oh does."** (and the title) | What does uh-oh do? | **82.99 "it means undo"**. Clues at 42.15, 45.19 and 79.79. | **45 s (the spine)** |
| L5 | 38.95 "some weird stuff does happen around me" | What stuff? | 71.39 (everything goes backwards) | 32 s |
| L6 | 45.19 "never once broke anything" | Why not? | 82.99 (he undid it). Implied, never said. | 38 s |
| L7 | 52.31 "Then came the field trip." | What goes wrong? | 59.51 (the truck brakes) | 7 s |
| L8 | 64.31 "for one second, we were flying" | Will they die? | 71.39 (rewind) | 7 s |
| L9 | 71.39 "everything went backwards" | What just happened? | 79.79-82.99 | 8-12 s |
| L10 | 85.39 "slammed on its brakes again" | Can he stop it this time? | 89.25 "Too late." / 93.89 "We still went over." It stays open into the plan. | 4 s, then open |
| L11 | 35.35 "Nothing gets through it." (plant, not a question) | When will this matter? | 105.49 plan. The real payoff lies past the cut. | 70 s |
| L12 | 102.93 "Then I looked at Leo…" | What's the idea? | 105.49 | 2.5 s |
| L13 | 105.49-109.49 the plan + 109.97 "like I was crazy" | Will Leo do it? Will it work? | **not paid (cut)** | open |

**Emotional peak:** 69.31-71.39. This is the scream of "Uh-oh!": an extreme close-up, the highest pitch so far, the white flash, and the climax of the falling-bus set-piece.

**Secondary low point:** 99.8-102.5 ("dizzy", "every scream by heart"). The emotion is exhaustion, followed by resolve at 105.5.

---

## 3. Numbers

- **Runtime analysed:** 111.03 s, voiced from 0.03 to 110.69. There is no silent intro and no music-only break.
- **Words:** **474** (ASR tokens, counting "uh-oh" as one word). On screen that makes **485 caption pages**, because "uh-oh" takes two, which is about 4.4 pages per second.
- **Pace:**
  - **256 wpm overall**. While speaking it is **about 280 wpm**, after removing about 9.9 s of pause beyond a 0.3 s baseline.
  - Median gap between word starts: 0.16 s. Longest gap: 0.64 s.
  - Per section:

    | Section | Time (s) | Pace (wpm) |
    |---|---|---|
    | Setup | 0-36 | 258 |
    | Hero and clues | 36-52 | 278 |
    | Incident | 52-71 | 258 |
    | Reveal | 71-85 | 236 |
    | Loop | 85-103 | 229 (the most pauses) |
    | Plan | 103-111 | 296 |

  - **For the owner's own read:** at a natural 160-180 wpm, these 474 words would take 2:38-2:58. To land at 2:00-2:30 when read naturally, a script needs about **330-420 words**. Otherwise, record and speed up about 1.3x.
- **Pauses:** the longest gaps sit right **after the trigger word**: "uh-oh!" at 70.75 (0.64 s), "undo." at 84.75 (0.64 s), "Uh-oh." at 90.85 (0.64 s), "Uh-oh!" at 94.69 (0.64 s). These are pockets left for the rewind whoosh and flash.
- **Sentences:**
  - **59** after merging dialogue tags (62 in the raw ASR).
  - Median **7 words**, mean 8.0, minimum 1, maximum 23. The longest is S20, the clue sentence.
  - Length buckets:

    | Length (words) | Share |
    |---|---|
    | 1 | 8% (all five are "Uh-oh") |
    | 1-3 | 20% |
    | **1-5** | **37%** (40% in the raw ASR) |
    | 6-10 | 34% |
    | 11-15 | 20% |
    | 16+ | 8% |

  - Median length by section:

    | Section | Median (words) |
    |---|---|
    | Setup | 10 |
    | Hero and clues | 12.5 |
    | Incident | 7 |
    | Reveal | 7 |
    | **Loop** | **3** |
    | Plan | 10 |

  - Sentences get shortest where the action repeats.
- **Sentence starts:**
  - **And ×7, Then ×2, So ×1, But ×0**, which is 10 of 59 (17%).
  - Inside sentences: ", but" ×2 (S18, S20) and ", so" ×2 (S5, S14).
  - The "And" starts cluster in the action: S25, S28, S30 and S31 are four of the seven.
- **Person:**
  - **First person dominates: 32 tokens** (I 16, me 4, my 4, we 4, us 1, our 1, I've 1, I'd 1).
  - Second person: 4 tokens. Two are in the rule ("your … you"), one is "You see" and one is inside dialogue ("you've").
  - Third person: 16 (his 6, he 4, their 3, she 2, them 1).
  - The narrator is the unnamed protagonist. "In my world" replaces the usual "In this world".
- **Dialogue:**
  - **9 utterances, about 31 words (6.5% of words, about 9-10 s or 9% of runtime)**.
  - Parents (chorus) ×1: "Fly! Fly! Say fly!" (24.1).
  - The hero ×8:
    - "Uh-oh!" (70.75);
    - "Mr. Baker, stop!" (86.91);
    - "Uh-oh." (90.85);
    - "Uh-oh!" (94.69);
    - "Uh-oh." ×3 (98.29-99.33);
    - "Leo, when I say now, make the biggest force field you've ever made. Right next to the railing." (105.49).
  - Leo and Mr. Baker never speak. They react with faces only.
- **New information:**
  - 54 distinct new facts or images in 111 s: a new one **every 2.07 s on average (median 1.76 s)**.
  - By section:

    | Section | Seconds per new fact |
    |---|---|
    | Setup | 2.42 |
    | Hero | 2.67 |
    | Incident | 2.12 |
    | Reveal | 2.00 |
    | **Loop** | **1.35** |
    | Plan | 2.02 |

  - The longest stretch without new information is 4.7 s (S20, the long clue sentence).
- **Picture rhythm:**
  - 85 cuts detected (a few are flash frames), so about **1.3 s per shot**.
  - **53 of 59 sentence starts fall on a cut (±0.2 s).** Each sentence gets its own shot.
- **Repeated words and phrases:**
  - **"uh-oh" ×11**: 5 times as a name or subject (37.2, 38.2, 39.9, 46.9, 83.0) and 6 times as the spoken trigger.
  - "force field" ×5. "fly" ×5, plus "flying" and "flew". "first word" ×4. "railing" ×4. "sandwich" ×4. "Leo" ×4 (plus "Leo's"). "bus" ×4. "river" ×3. "five seconds" ×3.
  - The exact phrase **"force field around his sandwich" ×3** (56.4, 77.7, 102.9) is the déjà-vu anchor.
  - "slammed on its brakes" ×2. "through the railing" ×2.
- **Loop compression:** each retelling of the crash is about half the length of the one before.

  | Loop | Time (s) | Sentences | Words | Duration |
  |---|---|---|---|---|
  | 1 (full) | 59.51-70.75 | S25-S30 | **49** | 11.2 s |
  | 2 | 85.39-90.85 | S38-S43 | **24** | 5.5 s |
  | 3 | 92.29-94.69 | S45-S47 | **12** | 2.4 s |
  | 4-6 | 98.29 / 98.77 / 99.33 | S51-S53 | **1 each** | 0.5 s each |
  | 7-20 | 99.81 | in "By the 20th try" | (one phrase) | 1.7 s |

- **Numbers and specifics:**
  - "a whole year" (4.6), "about a hundred times a day" (47.7, shown on screen as "100"), "not one single thing" (51.3), "for one second" (64.6), "**five seconds**" (82.1, 91.5, 96.8), "**the 20th try**" (100.1).
  - Concrete nouns: golden retriever, fire hands, cribs, newborn, toe, cup, plate, big yellow bus, bridge, river, railing, truck, backpacks, steering wheel, sandwich, Mr. Baker.

---

## 4. Devices (what keeps people watching)

| Device | Example | Time (s) | Why it works |
|---|---|---|---|
| **First-frame rule** | "In my world, your superpower is the first word you ever said." (12 words) | 0.03-2.75 | Three hooks in one line. "In my world" marks the format and sets up a first-person narrator. "your superpower" is wish fulfilment aimed at the viewer. "the first word you ever said" is universal, personal and checkable (ask your mom), so it drives comments. The rule is **wondrous, not deadly**: here the rule supplies the solution and the danger comes from an ordinary accident. |
| Rule wording lands on the key noun | "superpower" at 0.91 is the first caption the viewer can see in our copy | 0.9-1.3 | The first readable caption is the hook word, over a kid taking off into the sky. |
| **Gag ladder (literal-word logic)** | up→fly, hot→fire hands, ball→bounces, doggy→golden retriever "when she sneezes", mama→Mom appears | 6.99-21.31 | Each example is a 1-2 sentence mini-joke that teaches the rule's logic (the word is taken literally). They escalate from cool to silly to social. One new picture every 2-4 s. |
| Long setup, short punchline | "…make their mom appear right next to them anywhere, anytime." / "Their moms hate it." | 17.55 → 21.31 | A 16-word setup, then a 4-word deadpan. The rhythm makes the joke without any joke words. |
| **Rules-within-the-rule** | 1) Social law: "nobody ever says anything bad in front of a baby." 2) Leo's power: "Nothing gets through it." 3) The power's limit: "five seconds". | 25.91 / 35.35 / 80.75 | The society gets its own laws. The two absolute statements (nothing gets through, five seconds) become the puzzle's constraints. |
| **Dark-joke jolt at ~30 s** | "One dad stubbed his toe… We don't talk about what that kid can do." | 28.31-31.67 | A tone break at exactly the 30 s retention dip: a red-eyed baby and glitch flashes. It promises that this world has a dark side. |
| **Mystery lines** | "Nobody knows what uh-oh does." / "some weird stuff does happen around me" / "We don't talk about…" | 37.75 / 38.95 / 30.55 | Each one is a direct statement that information is withheld. The first one carries the whole middle of the video. |
| **Title = the open question** | Title "Uh Oh". The hero's nickname is "uh-oh", and he has no other name. | 36.31 | The viewer clicked on the mystery word. Its meaning is withheld until 82.99. |
| **Misdirection on the word itself** | "uh-oh" means oops or a mistake, so we expect a useless or bad-luck power. Then "I never once broke anything". | 37.2-51.8 → 82.99 | The reveal reverses the word's everyday meaning: "Uh-oh doesn't mean oops, it means undo." The pun lands because the misreading was set up. |
| **Clue plants → payoff** | Déjà vu "like I've done this all before" (42.15). "never once broke anything" (45.19), with the intact cup on the floor. | → 71.39-82.99 | Two fair clues make the reveal feel earned. Viewers who guess early feel smart and keep watching to confirm. |
| **Chekhov's power** | Leo's "Nothing gets through it." | 35.35 → 105.49 | The helper's power is planted 70 s before the hero thinks to use it. |
| **Anchor object for the time loop** | "making a tiny force field around his sandwich" | 56.39 → 77.71 → 102.93 | A silly, specific, visual detail. It is repeated verbatim with the same shot, so the viewer experiences the déjà vu too ("I knew that sandwich!"). The third time, the sandwich turns into the solution. |
| **Motif reversal** | Everyone wants their baby to "fly". The only flying we see is a bus falling off a bridge: "for one second, we were flying." | 3.07-25.35 → 64.31 | A callback with a sour twist. The society's dream becomes the nightmare. |
| **Stakes** | "Our whole class on the big yellow bus… crossing the bridge over the river." | 53.43 | Every kid in the class, a height and water. The stakes are ordinary and instantly readable. |
| **Ticking clock** | "I'd seen this exact moment five seconds ago." / "Five seconds back." / "Five seconds isn't a lot of time." | 80.75 / 91.49 / 96.77 | The power works but is too short. That turns a superpower into a puzzle. |
| **Sensory tricolon** | "Kids were screaming, backpacks were floating, and the river was coming up fast." | 66.03 | Sound, sight and motion in one breath. |
| **Rewind described as a picture** | "The water pulled away. The bus flew up, the railing put itself back together…" | 72.59-77.39 | The reverse motion is told as physical images, so the narration and the picture match. |
| **Reversal: power ≠ solution** | "The truck slammed on its brakes again." / "Too late." / "We still went over." | 85.39 / 89.25 / 93.89 | Straight after the triumphant reveal comes a failure. It avoids an easy win. |
| **Loop compression** | 49 → 24 → 12 → 1 → "By the 20th try" | 59.5-99.8 | Tell it fully once, then shorten each repeat until it is a single word, then skip 14 loops in one phrase. Repetition becomes acceleration instead of boredom. |
| **Fragment montage** | "Too late. Through the railing. The river. Uh-oh. Five seconds back." | 89.25-91.97 | Five fragments in 2.7 s. The audio equivalent of fast cuts. |
| **Specific numbers** | "a whole year", "a hundred times a day", "five seconds", "the 20th try" | 4.6 / 47.7 / 82.1 / 100.1 | They make the world measurable. "20th" sells how hopeless it is without showing 20 loops. |
| **Emotional exhaustion beat** | "By the 20th try, I was dizzy. I knew every scream by heart." | 99.81-102.53 | A human cost inside a gimmick. "every scream by heart" is a chilling sensory detail. |
| **Helper's skepticism as a new obstacle** | "He looked at me like I was crazy." | 109.97 | The plan is known but not trusted. With five seconds, convincing Leo is the next puzzle. A clean cliffhanger. |
| **Outsider hero** | "The kids at school call me uh-oh" over a wide shot of him alone | 38.95 | Underdog sympathy. It sets up a redemption payoff. |
| **Flashback through Mom** | "And Mom says that when I was little…" | 45.19 | Backstory in one sentence, in a parent's voice, and it doubles as a clue. |
| **Tense switch = "story starts now"** | Present tense for the world, then "Then came the field trip." | 52.31 | The niche's "last night" device in another form: a specific event marker instead of a time marker. There is no "last night" in this video. |
| **Exact-repeat line and shot** | S24 and S34 differ by only "sitting next to me". The shot is identical. | 56.39 / 77.71 | The script and the edit reuse the same asset to show time repeating. It costs nothing to make and reads instantly. |
| **Built for word-by-word captions** | One idea per sentence, end-weighted (the image word comes last: "…say **fly**", "…**fire hands**", "…through the **railing**", "…it means **undo**"). Mostly one-syllable words. Lists in parallel syntax ("Kids who said X…"). Numbers as digits ("100", "20th"). The title word splits into two caption pages, "uh" / "oh". | throughout | Each caption page is about 0.23 s, so the payload word must be short and come last, where the cut lands. 53 of 59 sentences start on a cut. |
| Sound pockets | 0.64 s gaps after each "uh-oh" and after "undo." | 70.75, 84.75, 90.85, 94.69 | The script leaves room for the rewind sound effect and flash, so the effect gets its own beat. |
| Acted dialogue by one narrator | A pitch jump on screams (~280 Hz) and "Mr. Baker, stop!" (~420 Hz) | 69-71, 87 | One voice covers everyone. The emotion is carried by pitch and volume, not by extra actors. |

**Devices not used** in the visible part: "last night" immediacy, a generational ending, emotional sacrifice. Possibly some appear after the cut.

---

## 5. How it probably continues (GUESS, inferred from the setup)

This is a guess. The real ending is cut off; we lose about 1-2 minutes, which puts the original at roughly 2:50-3:50.

1. **Convincing Leo (most likely next).** Leo thinks he's crazy, so the hero uses the loop to prove he knows the future. He predicts the truck, a classmate's line or the sandwich ("You're about to say…"). A failed loop or two may come first, still compressed. *The plant that supports this:* the five-second limit makes persuasion itself the puzzle.
2. **Execution.** On "now", Leo throws the biggest force field of his life at the railing. *The plant:* "Nothing gets through it." The bus bounces off or slides along the bubble and stays on the bridge. There is probably a beat of doubt first: the bubble cracks, or Leo is too slow and the hero has to undo once more.
3. **Aftermath, with an emotional or social reversal.** Nobody but the hero remembers the 20 crashes. Leo just sees a weird bubble moment, and maybe complains about his sandwich. Mr. Baker is confused. Possibly the kids who mocked "uh-oh" never know he saved them (bittersweet), or the class finds out and the nickname turns into respect (a redemption of the outsider beat at 38.95).
4. **Closing callback (the strongest guess for the last line).** Back to the first-word theme:
   - a line like "Uh-oh doesn't mean oops…" returns with new weight; or
   - a crib or generational ending that mirrors the parents chanting "Fly!" (the hero, years later, hoping his own baby says the "useless" word); or
   - a final open loop about the toe kid ("We don't talk about…"), which was set up at 30.55 and never paid.
5. **Possible extra twist.** The déjà-vu line "like I've done this all before" hints that he has undone far more than he knows. One example: today was not the first time this field trip happened.

---

## 6. Why it works, and where it is weak

### Why it works

- **Retention.**
  - A new fact or picture arrives about every 2 s and the shot changes about every 1.3 s.
  - The setup is not an info-dump. It is a chain of one-line jokes, each one a new character and set.
  - The middle is carried by one strong question, the title ("what does uh-oh do?"), held for 45 s and backed by two fair clues.
  - Once the disaster hits, there is a turn every 4-6 s. The loop section speeds up (shorter sentences, a new fact every 1.35 s) instead of repeating.
- **Emotion.**
  - Comedy leads to a creepy jolt, then underdog sympathy ("kids call me uh-oh"), then terror (the falling bus, the scream), then wonder (the rewind), then frustration and exhaustion ("every scream by heart"), then resolve (the plan).
  - Kids in danger is the most universal stake there is.
  - The outsider with the "worst" word has the best power: a classic underdog reversal.
- **Shareability.**
  - The rule invites self-insertion ("my first word was 'dada', so…") and produces comments that answer an unspoken question.
  - "Uh-oh means undo" is a quotable, pun-shaped reveal.
  - The power menu (fire hands, dog sneeze, summoning Mom) gives lots of "which one would you want" bait.
- **Craft.**
  - The world's rule produces both the problem's solution (undo plus force field) and the obstacle (five seconds, a disbelieving friend).
  - The anchor object (the sandwich) ties the comedy register to the climax.

### Weak spots

- **Slow start to the story.** The hero appears at 36 s and the inciting event at 52 s. There is no plot twist at 30 s, only a tonal jolt. It survives because the gag ladder is dense. A weaker gag list would leak viewers.
- **Throwaway world-building.** The fire hands, bouncing kid, dog girl, Mama kid and toe kid never return in the visible part. The toe-kid loop may never be paid, which can read as a cheap tease.
- **Logic gaps.**
  - The hero says "uh-oh" "a hundred times a day" and gets déjà vu every time. Why has nobody, including him, worked out that it rewinds time?
  - "Nobody knows what uh-oh does" is hard to believe if it works every time he says it.
  - Mr. Baker hears "stop!" but can't stop. That one is fine, but the loop never explains why grabbing the wheel fails.
- **Passive supporting cast.** Leo and Mr. Baker have no lines. Leo's skepticism is the first trace of his personality, and it comes at 110 s.
- **Very fast read.** 256-280 wpm is hard to act naturally. The owner's natural read would need about 20-30% fewer words for the same runtime.
- **Repetition risk.** "Uh-oh" ×11 plus loop repeats can grate. The compression saves it here, but a longer loop section would tire viewers.
- **Late title payoff with no new question opened before it.** Between 52 and 71 s the only pull is the disaster itself. The undo reveal is guessable from the clues for sharp viewers, so it lands as a confirmation rather than a surprise.

### Mechanics worth reusing (structure only; invent our own content)

1. **A rule that is a power system, not a threat.** The danger comes from an ordinary accident. The rule's twist is what the hero's odd power really does.
2. **Gag ladder for the society section:** one example per 2-4 s, escalating from cool to silly to social to dark, ending on a creepy jolt near 30 s.
3. **The title is the hero's unknown variable.** State the mystery out loud ("Nobody knows what X does") and plant two fair clues before the reveal.
4. **Give the helper's ability one absolute sentence early** ("Nothing gets through it") and make it the solution 60-70 s later.
5. **Use a silly, specific anchor object** that repeats word for word with the same shot when time repeats, and that becomes the key the third time.
6. **Power + limit = puzzle** (here, five seconds). Follow the triumphant reveal at once with failure ("Too late.").
7. **Loop compression:** tell it once in full, then halve the words each time until one word is left, then jump with a number ("By the 20th try").
8. **End-weight every sentence for word-by-word captions.** Leave a 0.5-0.7 s pocket after each trigger word for the sound effect and flash. One sentence per shot.
9. **Cliffhanger on doubt, not on danger:** "He looked at me like I was crazy." The next obstacle is a person's disbelief.
