# Next video: "What if..." topic research and idea list

Date: 2026-11-02. Strategist pass for the 2D-animated "What if..." video that comes after the Roblox reference study.

## 0. Data limits for this run (read first)

- **NexLev could not be used.** The first call returned `WEEKLY LIMIT EXCEEDED: 50/50 MCP tool calls, plan FREE, resets 2026-11-03 06:23 UTC`. So this run has no new NexLev numbers, including the reference channel's outlier list.
- **YouTube is blocked from this sandbox.** WebFetch to www.youtube.com and noembed.com fails with ENOTFOUND, because the hosts are outside the session's allowed network domains. Web search still works. It returns titles, video IDs and upload ages, but no view counts.
- **The data used here comes from three sources:**
  1. The owner's own figures for the reference video.
  2. Our measurements of the reference itself, taken from the uploaded clips by the earlier workflow steps (`study/audio/*`).
  3. Real NexLev data on the 2D-animated survival and "What if" story niche, pulled on 2026-10-27 (6 days ago). It is saved in `study/nexlev_old/`.
  4. Web search, for the titles and ages of recent "What if" uploads.
- **To fill the gaps once the quota resets (after 2026-11-03 06:23 UTC):**
  - `youtube_video_details 54mnfwJJdnE`, to get the channel ID.
  - `youtube_channel_videos` (newest) and `youtube_channel_outliers` on that channel.
  - `search_videos query="What if" minView=100000 startDate=2026-08-04 sortBy=viewCount`.
  - `youtube_search "what if dinosaurs" upload_date=month sort_by=views`.

## 1. The reference: "What If the WHOLE WORLD Became Roblox? 😱"

- **Basics:** video ID `54mnfwJJdnE`, length 8:02, uploaded about 2026-10-30/31. The owner reports 364K views in 2 days and 3.6K views/hour now. That is about 7.6K/h averaged over the first 48 h.
- **Channel:** web search does not show the channel, and NexLev and YouTube were unreachable. It is still to be confirmed (see the queries above).

**Measured structure** (from `study/audio/transcript.txt`, `sfx.txt`, `music.txt`, `voices.txt`):

| Time | Beat |
|---|---|
| 0:00-0:19 | Flash-forward cold open with stakes: "Seven days. One game. And by day seven the world had 60 seconds left." The system voice says "Server shutting down in sixty seconds", and the Kid says "Okay, okay, I can explain! It all started... with a pop-up." |
| 0:22 | Inciting incident: a 2 a.m. pop-up asks "Turn the world into Roblox? Yes ... or yes." |
| Day 1 (0:37) | Game rules hit daily life: alarm = daily reward, toothbrush = hotbar, stairs = fall damage, Mom talks in chat bubbles, Dad walks into a wall. |
| Day 2 (1:35) | "The rules", numbered 1-4: jump, lava, respawn, AFK kick. |
| Day 3 (2:26) | School: NPC teacher, an obby math test, badges, game pass. |
| Day 4 (3:18) | Economy: Robux, the ice-cream truck sells game passes, Mom wears 40 hats. |
| 4:19 | Subscribe call-to-action delivered as an in-world gag ("golden name tag"). |
| Day 5 (4:31) | Lag and glitches: the tone turns. |
| Day 6 (5:17) | Reveal: a giant mouse cursor, so the world is somebody's game. |
| Day 7 (6:06) | Server-shutdown countdown. The town stacks into a tower using the earlier gags: 40 hats, Dad's T-pose. |
| 7:31 | Back to normal. |
| 7:44 | "Almost..." |
| 7:53 | "Comment oof". |
| 7:56 | Sting: "Update failed. Rolling back to day one." |

**Measured craft:**

- **Lines:** 229 sentence units. The narrator speaks 147 of them and 76% of the words, in second person ("you"). A character or system line cuts in about every 6 s.
- **Voices:** 6-7 in total: narrator, kid, mom, dad, teacher NPC, band-passed system/PA voice, and townspeople.
- **Pacing:** 206 picture cuts, which is 25.6 per minute with a median shot of 1.8 s.
- **Sound effects:** about 40 per minute, rising to 60-75 per minute in the climax. 61% of cuts have a sound within 0.2 s, and every on-screen onomatopoeia has a sound on the same frame.
- **Music:** runs under the whole video at about 123 BPM and changes every 5-6 s. It deliberately drops out on 20 gag beats.

**The formula** (this is what the next video has to copy, not the Roblox skin):

> A rule system the audience already knows, applied to boring everyday life, played by a family with running gags. Escalation is day by day: rules, then school, then money, then glitches, then a god reveal, then a countdown. There is a system/announcer voice and the ending pays off the earlier gags.

## 2. What the niche data says

### 2.1 2D-animated story channels (NexLev, pulled 2026-10-27)

Outlier = top video ÷ channel average. Views per hour are computed from views and age.

| Channel (subs) | Top video | Views | Age | Length | ≈ views/h | Outlier |
|---|---|---|---|---|---|---|
| Beanie Survives (98.8K) | Zombie Outbreak: 30 Days Trapped On The 30th Floor | 2.7M | 14 d | 8:12 | 8.0K | 7.7x (avg 350K) |
| Nobody Gets In (39.7K) | Zombie Outbreak: 30 Days Locked Inside a Supermarket | 2.2M | 13 d | 10:41 | 7.1K | 7.2x (avg 305K) |
| Nobody Gets In | Zombie Outbreak: 30 Days Locked Inside a School | 1.4M | 10 d | 8:57 | 5.8K | 4.6x |
| **Oddly Elsewhere (17.1K)** | **What If You Were the Last Human on Earth?** | **871K** | 13 d | 11:01 | 2.8K | 5.9x (avg 147K) |
| **Oddly Elsewhere** | **What If Humans Lived Underwater?** | **605K** | 10 d | 10:02 | 2.5K | 4.1x |
| Oddly Elsewhere | Could You Survive a Zombie Apocalypse? | 199K | 7 d | 14:20 | 1.2K | 1.4x |
| Oddly Elsewhere | What If You Actually Lived in a Cyberpunk City? | 128K | 14 d | 9:48 | 0.4K | 0.9x |
| Beanie Survives (2nd, 9.1K) | Zombie Apartment Survival 1 Year | 485K | 14 d | 17:29 | 1.4K | 7.1x |
| One More Day (5.3K) | Doomsday: 7 Days To Prepare Before Everything Collapses | 417K | 10 d | 21:07 | 1.7K | n/a |
| Melvin Wont Die (3.1K) | Zombie Outbreak Starts In 6 Days And Only YOU Know (Animated) | 234K | 10 d | 9:51 | 1.0K | 4.9x |
| Stick Survives (1.4K) | Zombie Outbreak Survival: Day 1 to Day 30 - Trapped in a Mall | 202K | 9 d | 19:59 | 0.9K | 5.2x |
| bucky survives (1.9K) | Zombie Outbreak: Surviving 365 Days Underground | 191K | 6 d | 15:33 | 1.3K | 5.3x |
| Kit vs The End (3.0K) | Zombie Outbreak: Escaping A Zombie Cruise Ship, Day 1 To Day 100 (Full Movie) | 141K | 2 d | 1:13:02 | 2.9K | 12.6x |

The batch cohort median, which includes FunNotSoFun ("What if your money grew 10x every day", a Blender "what if" channel), is 46K views per video at an RPM of $3.31.

### 2.2 Recent "What if" uploads found by web search (views not available, see §0)

**Dinosaur titles:**
- "What If Dinosaurs Came Back Today? 🦖😱" (`DLT_oeYYF4o`, about 11 days old): a T-Rex and baby dinos in your city.
- "What If Dinosaurs Came Back in Today's World? 🦖🌍" (`6NyjaFZlI7E`)
- "What If Dinosaurs Returned Today? 🦖" (`18wefK4eei8`)
- "What If Dinosaurs Came Back to Life Today?" (`zz9d88FdiL0`)
- "What If You Woke Up in the Dinosaur Era? 🦖" (`POQEItewwmM`)
- "Could You Survive 24 Hours in the Dinosaur Age? 🦖😱" (`H7YLKDHGcy8`)
- "POV: You Wake Up in the Age of Dinosaurs" (`qaT5KDQmXjQ`)
- "What If Dinosaurs Never Went Extinct?" (`4A6PkojIEc4`, 2026-08-18)
- "What If the Dinosaur Asteroid Hit Today? The First 24 Hours" (`esvvc37kv6U`)

There is a lot of supply, and most of it looks like documentary or AI explainers rather than character comedy.

**"Woke up" / "the world became" titles:**
- "One Morning, the World Was 1962 Again ✨" (`RA3vdXyiysM`, about 44 days)
- "What If You Woke Up and Discovered You Were the Last Human on Earth? 😨" (`rKs25mVAycE`)
- "What If Zombies Were Real and You Were the Last Human Alive?" (`_nd2Z8BhKks`)

**Body and scale:**
- "What If You Shrank and Couldn't Stop?" (`t1-hzEz-4mk`, 2026-10-16)
- "What If You Shrank Until Your Garden Was Bigger Than the Universe?" (`gVFgLnq_QS0`, 2026-10-18)

**Loops and memes:**
- "What If You Were Trapped in a Time Loop?" (`n_BlWAmU1Zk`, about 2026-10-21)
- "What If You Lived the Same Day Forever?" (`HHCZwBQBt6g`)
- "What If YOU Were The Immortal Snail?" (`crd-1rQr7ZI`, 2026-10-30)
- "What If The Immortal Snail Chased You and Never Stopped?" (`rLCVK9llntQ`, 2026-10-24)

**Games:**
- "Timeline: What If The Earth Turned Into Minecraft?" (`aiVPncLcPGc`)
- "What If Everyone Was Trapped in Minecraft?" (`SmbbPp3G5Io`)
- "What If Minecraft Was the REAL Earth" (Short, about 39 days)
- "What If EVOLUTION of SIX SEVEN 67 KID Was Real? (Italian Brainrot)" (`55o6zO9iQrI`)

**New "what if" animation channels, a crowded label:**
- The What If Animator (@What_if_3danimator, weekly)
- What If Animated (@Whatifanimated)
- What If Animation Studio (AI-made)
- "What if? Animated series!" (@what-if-animated-series, "What if gravity stopped?")
- What If Animations (@WhatIfAnimations2)

### 2.3 Formats that overperform

1. **Second person plus a counter in the title.** "What if YOU...", "30 Days", "7 Days", "24 Hours", "Day 1 to Day 30". Every 4x-8x outlier in our data has one. The reference uses "Seven days" inside the story.
2. **Big-world reframes beat niche settings.** "Last Human on Earth" (871K) and "Humans Lived Underwater" (605K) did 5-7x better than "Cyberpunk City" (128K) and "Cybernetic Enhancements" (36K) on the same channel. Everyone has to be able to picture it instantly.
3. **Standalone episodes beat sequels.** Part 2s keep only 17-25% of Part 1's views: Nobody Gets In 2.2M to 375K, School 1.4M to 356K. Make a finished standalone story, with at most a sting for a sequel.
4. **Length of 8-11 minutes for short-form-energy story videos.** Reference 8:02; top zombie videos 8:12, 8:57 and 10:41; Oddly Elsewhere 10-11 min. Longer full-movie edits only work as compilations.
5. **Tiny channels break out on their first 1-3 videos.** Every channel above is 1K-100K subscribers. The topic, hook and production carry the video, not the channel size.
6. **Title pattern:** "What If the WHOLE WORLD Became X? 😱", with one word in caps and one emoji. Repeating the reference's pattern also helps suggested traffic next to it.

## 3. The owner's "Jurassic World" idea: an honest evaluation

**For it:**
- Dinosaurs are evergreen for kids and families, and the topic is being uploaded right now: at least 9 dinosaur "what if" titles in recent weeks.
- They look great in a bright 2D cartoon: jungle gradients, volcano glow, scale shots, and roars that make loud sound-design moments.
- There are many acting opportunities: a short-armed T-Rex, sneaky raptors, a dopey brachiosaurus.

**Against it, as stated:**
1. **The reference does not win because it is about a game.** It wins because a rule system the viewer knows is applied to everyday life. A plain "dinosaurs are back" story turns into survival horror, the same tone as our earlier zombie and doorbell videos, and it loses the comedy engine.
2. **"Jurassic World" is a Universal/Amblin trademark and film franchise.**
   - Its logo, gate, gyrosphere, named creatures (Blue, Indominus) and the John Williams theme are protected. The theme will certainly trigger Content ID.
   - People searching "Jurassic World" mostly want official clips, toys and games, so the click intent does not match.
   - Roblox is a softer case: it actively encourages creator videos.
3. **Supply is heavy.** Most "What if dinosaurs came back" videos are AI or documentary style. That makes room for a character comedy, but a generic title will drown.
4. **Production cost.** Expressive, rigged dinosaurs (jaw, tail, legs, eyes) cost more to build than blocky avatars. Budget for 3-4 dinosaur rigs.
5. **A "made for kids" classification risk** turns off comments (the reference ends on "Comment oof") and lowers RPM. Write it with a general-audience, Dad-joke layer the way the reference does.

**Verdict:** keep dinosaurs, but give them the reference's rule-system skeleton: **"What If the WHOLE WORLD Became a Dinosaur Park? 🦖"**
- The park PA announcer becomes the system voice, park rules become game rules, park tokens become Robux, and a power outage becomes the lag day.
- The reveal is the control-room view. The climax is a "PARK CLOSING IN 60 SECONDS" countdown.
- This matches the owner's wish and the proven formula, with low trademark exposure.
- If the owner insists on the search term, use "JURASSIC" alone ("...Went JURASSIC?"), because it is a geological period. Never use the logo, typefaces, gate, music or named creatures.

## 4. Ideas, ranked

Scores are 0-10. They weigh demand evidence, how well the idea fits the reference formula, how well it suits bright 2D character acting, IP and saturation risk, and build cost on our SVG engine.

### 1. What If the WHOLE WORLD Became a Dinosaur Park? 🦖 (8.6)

**Premise:**
- **Cold open:** "Seven days. One park. By day seven the gates opened... from the inside." The PA says "Attention guests: the park is closing. Permanently." The Kid says "Okay okay, I can explain! It started with a ticket."
- **Inciting incident:** a golden ticket in a cereal box offers "Turn your town into a dinosaur park? ACCEPT / ACCEPT".
- **Day 1:**
  - You wake up with a wristband, and the dog is now a baby triceratops.
  - The school bus is a glass ball ride, and a brachiosaurus "mows" the lawn by eating the hedge too.
  - Mom announces dinner over the park PA.
- **Day 2, the rules:**
  1. Stay inside your fence line. The backyard fence buzzes.
  2. Never run from a raptor. Dad runs.
  3. Feeding time is 12:00. Every carnivore in town turns to Dad's barbecue.
  4. Exit through the gift shop. Every door now does.
- **Day 3:** school field trip. The T-Rex teacher cannot reach the board, and a pop quiz becomes a dig site.
- **Day 4, economy:**
  - Money becomes park tokens.
  - Mom buys 40 souvenir hats.
  - The ice-cream truck becomes a feeding station.
- **Subscribe gag:** subscribers get a VIP wristband.
- **Day 5, power outage:**
  - The fences flicker and the lights go out.
  - Footsteps make ripples in a glass of water.
  - This is the horror-lite turn.
- **Day 6, reveal:** the whole town is on a giant visitor's map. A giant cursor or tour guide is rearranging the paddocks.
- **Day 7:** "PARK CLOSING IN 60 SECONDS".
  - Every dinosaur stampedes for the gate, and the gate is your street.
  - The town and the dinosaurs team up. The tower of callbacks: Mom's hats, the baby-triceratops dog, and Dad still holding the barbecue tongs.
- **Ending:** "Back to normal. Almost." Then an egg in the fridge cracks.

**Why it wins:**
- It is the owner's idea, rebuilt on the reference's exact skeleton:
  - a known rule system (theme-park rules) applied to everyday life;
  - a family with running gags;
  - escalation by day;
  - a system/PA voice;
  - a countdown climax and a payoff from earlier gags.
- The title pattern also sits next to the reference ("What If the WHOLE WORLD Became...") for suggested traffic.
- Dinosaurs are an evergreen kids' and family topic, and this is a fresh comedy angle on an over-supplied documentary topic.

**Evidence:**
- Reference: "What If the WHOLE WORLD Became Roblox?" did 364K in 2 days (about 7.6K/h average, 3.6K/h now), using this exact day-by-day rule structure.
- Day-counter titles are 4x-8x outliers in the 2D story niche: "30 Days Trapped On The 30th Floor" 2.7M (7.7x); "30 Days Locked Inside a Supermarket" 2.2M (7.2x); "Doomsday: 7 Days To Prepare..." 417K.
- Dinosaur demand is live. Web search finds at least 9 recent dinosaur "what if" uploads: "What If Dinosaurs Came Back Today? 🦖😱" (about 11 days old), "What If You Woke Up in the Dinosaur Era? 🦖", "Could You Survive 24 Hours in the Dinosaur Age? 🦖😱" and others. Their view counts are not available in this run.

**Visual potential (very high):**
- **Palette:** saturated jungle-green gradients, a neon park-sign palette, a volcano-orange sky at sunset, and a cold blue power-outage night with red emergency lights.
- **Acting:** a T-Rex with huge pupils and a short-arm gag, mischievous raptor grins, a dopey brachiosaurus, the baby-triceratops "dog", and a panicked Dad.
- **Camera:** scale shots (a foot fills the frame) and footstep ripples in a glass.
- **Sound:** a band-passed PA voice, layered roars, brass stabs on each rule card, marimba-to-timpani music shifts, a tape-stop when the power cuts, and a jingle that turns menacing.

**Risk:**
- Trademark: do not say "Jurassic World/Park" and do not use its logo, gate arch, gyrosphere, named dinosaurs or the John Williams theme. Real species names (T. rex, Velociraptor) are free.
- Build cost: 3-4 expressive dinosaur rigs (jaw, tail, legs, eye acting) in the SVG engine.
- Many competing dinosaur uploads, so the title and thumbnail have to show comedy, not a documentary.
- "Made for kids" classification would switch off comments and lower RPM, so keep a general-audience joke layer.

### 2. What If Real Life Had a SETTINGS MENU? ⚙️ (8.2)

**Premise:**
- **Cold open:** "7 days. One menu. By day seven, someone pressed RESET."
- **Inciting incident:** at 2 a.m. a settings app appears on your phone, "Apply to reality?"
- **Day 1:** you turn your sister's volume to 0, brightness on the sun to 200%, gravity to "Moon", and Dad gets subtitles.
- **Day 2, the rules:** every change applies to everyone nearby, there is no undo, and settings reset at midnight. They do not.
- **Day 3:** school on 2x speed, with the teacher on fast-forward.
- **Day 4:** someone finds Language, and the whole town speaks emoji.
- **Day 5:** "Graphics: LOW". The world turns pixelated and lags.
- **Day 6:** you discover that you are not the only one with the app.
- **Day 7:** a "Factory Reset in 60 seconds" countdown.
- **Climax:** the family has to reach the one phone that has the Cancel button.
- **Sting:** "Restore previous settings? YES / YES".

**Why it wins:**
- It is the reference's engine (a pop-up, UI rules applied to life, a system voice, a countdown) without needing any game brand. That means no IP risk and an endless supply of instantly readable visual gags.
- Every gag is a UI element, which our SVG engine draws cleanly: sliders, toggles, toasts, progress bars.
- It is also a natural series (new menus later: Parental Controls, Developer Options).

**Evidence:**
- The reference's most-shared beats are all UI gags: "Daily reward claimed!", "Equipped", "You have been disconnected", "You do not own this item", "Server shutting down in sixty seconds". About 18 system-voice lines carry its biggest laughs.
- FunNotSoFun (what-if animation, cohort data) uses an in-world HUD as its signature.
- "One Morning, the World Was 1962 Again ✨" (about 44 days old) shows the "the world changed overnight" framing is being uploaded now. Views are not available in this run.

**Visual potential (very high):**
- **Animation:** clean glassy UI over a cartoon suburb; sliders that visibly warp the world (gravity, a saturation slider that drains colour, a brightness slider that blows out the sky).
- **Acting:** strong faces (the sister on mute, Dad reading his own subtitles).
- **Sound:** every toggle gets a tick, sliders get rising or falling tones, and there is a tape-stop on low graphics.
- **Colour:** perfect for showing off gradients and colour grading.

**Risk:**
- It is less "searchable" than a known noun (dinosaurs, Minecraft), so it depends on the thumbnail and title curiosity.
- It must avoid looking like the iOS or Android settings UI, so build our own UI style.
- The abstract premise must be explained in under 10 seconds.

### 3. What If a T-Rex Hatched in Your House? (7 Days) 🥚🦖 (8.0)

**Premise:**
- **Cold open:** "Seven days. One egg. By day seven it was taller than the house, and its MOM was coming."
- **Inciting incident:** a weird egg arrives in an online order.
- **The days:**
  - **Day 1:** it hatches in the fridge. It is cute, and it eats the dog's food and the dog.
  - **Day 2:** dog-sized. It follows you to school.
  - **Day 3:** pony-sized. Hide it from the neighbours, from Mom, and from the mail carrier.
  - **Day 4:** car-sized. Dad tries to walk it.
  - **Day 5:** house-sized, and the news helicopters arrive.
  - **Day 6:** the ground shakes. Something MUCH bigger is coming.
  - **Day 7:** the mother T-Rex arrives on your street, and there is a 60-second standoff.
- **Ending:**
  - The family returns the baby. It is an emotional goodbye.
  - It comes back to visit and steps on Dad's car.
  - Sting: a second egg in the box.

**Why it wins:**
- Dinosaurs with a built-in escalation axis: size doubles every day, which gives automatic stakes and a reason for a new set-piece each day.
- An emotional pet bond gives retention and comments ("name the dino").
- The title promises a single clear image, and there is no IP at all.

**Evidence:**
- The current dinosaur supply is mostly documentary (see §2.2). "What If Dinosaurs Came Back Today? 🦖😱" (about 11 days old) leads with "cute baby dinosaurs... in your city", which shows the baby-dinosaur hook is in use.
- Day-counter structures top the niche: "Zombie Outbreak Starts In 6 Days And Only YOU Know" 234K on a 3.1K-subscriber channel (4.9x); "30 Days..." 2.2M-2.7M.

**Visual potential (very high):**
- **Acting:** a squash-and-stretch baby rex with huge expressive eyes, growing between cuts, against the same kitchen set, which shows the scale change instantly. Hiding gags: the tail sticking out of the closet.
- **Camera:** a giant eye at the window.
- **Sound:** a cute squeak that drops in pitch as it grows, a mother roar with sub-bass, and a heartbeat build in the standoff.

**Risk:**
- Close to "raise a dinosaur" and "I raised a T-Rex" kids' content, which leans toward "made for kids".
- The growth rig needs one character design that holds at every size.
- It does not use the reference's "the whole world became" pattern for suggested traffic.

### 4. What If the WHOLE WORLD Became Minecraft? ⛏️ (7.9)

**Premise:** a direct sibling of the reference.
- **Inciting incident:** a pop-up asks "Load world: EARTH (Survival)?"
- **Day 1:** everything turns blocky, you punch a tree for wood, Mom crafts breakfast, and Dad falls into a hole he dug straight down.
- **Day 2, the rules:** night spawns mobs, you get hungry every 20 minutes, and lava and water make stone.
- **Day 3:** school becomes a crafting table.
- **Day 4:** diamonds replace money.
- **Day 5:** a creeper-like hissing neighbour.
- **Day 6:** someone switches to Creative in the sky.
- **Day 7:** "World deleting in 60 seconds".

**Why it wins:**
- It has the closest audience overlap with the reference (gamer kids). The most searchable "the whole world became..." noun after Roblox, and the most ready-made rule system.

**Evidence:**
- Reference: 364K / 2 days with the identical template.
- Web search finds the topic recurring: "Timeline: What If The Earth Turned Into Minecraft?", "What If Everyone Was Trapped in Minecraft?", and "What If Minecraft Was the REAL Earth" (Short, about 39 days old). That shows demand, but also competition. Views are not available in this run.

**Visual potential (high):**
- Blocky 2D is cheap and clean in SVG, with pixel-texture gradients and a day/night colour cycle.
- But blocky characters limit facial acting, which is the owner's main ask. We would need to cheat with expressive faces on block heads.

**Risk:**
- The owner asked for a new topic, not Roblox, and this reads as a reskin of the reference.
- Mojang's guidelines allow videos about the game, but our animation cannot copy Steve, creeper or mob designs, textures or the logo.
- The reference channel itself is likely to make this next, so the field gets crowded fast.

### 5. What If Dinosaurs Came Back for 24 Hours? 🦖⏰ (7.6)

**Premise:**
- **Cold open:** "6:00 a.m. to 6:00 a.m. 24 hours. By hour 23, a T-Rex was in the school cafeteria."
- **Inciting incident:** a museum glitch, or a meteor in reverse.
- **Escalation is hour-stamped** (a timer on screen at all times):
  - 07:00 a stegosaurus traffic jam;
  - 08:00 pterodactyls steal everyone's breakfast;
  - 10:00 raptors learn to open doors (Dad's fridge);
  - 13:00 the zoo switches sides;
  - 16:00 a brachiosaurus is used as an elevator;
  - 20:00 the city goes dark;
  - 23:00 the T-Rex is in the cafeteria.
- **Countdown climax:** they must be at the museum before the portal closes.
- **Sting:** you got home, but something is purring under your bed.

**Why it wins:**
- It matches the owner's requested variant, and "24 hours" adds an always-on timer, which drives retention.
- A stampede of pure spectacle beats.

**Evidence:**
- "Could You Survive 24 Hours in the Dinosaur Age? 🦖😱"; "What If the Dinosaur Asteroid Hit Today? The First 24 Hours"; "What If Dinosaurs Came Back Today? 🦖😱" (about 11 days); "What If Dinosaurs Returned Today? 🦖"; "What If Dinosaurs Came Back in Today's World? 🦖🌍". These show live demand and heavy supply. Views are not available in this run.
- Counter titles are 4x-8x outliers in our NexLev niche data.

**Visual potential (very high):**
- Clock-face transitions with whoosh and hit on every hour card, a city day-to-night colour arc, many species, chase cameras, a dark-city red-emergency palette, and roar layering.

**Risk:**
- It is the most-saturated phrasing, so it needs a family comedy cast to stand out from the documentary and AI uploads.
- The "dinosaurs are a threat" tone can tip into horror.
- It needs many dinosaur rigs (5+).
- Trademark-free as long as no franchise imagery is used.

### 6. What If the WHOLE WORLD Became a Cartoon? 🎨 (7.5)

**Premise:**
- **Inciting incident:** a pop-up asks "Toon-ify reality?"
- **Day 1:** you wake up rubber-hosed, your yawn stretches to the ceiling, Mom gets hit by a frying pan and turns into a pancake-shaped Mom, and Dad walks off a cliff and does not fall until he looks down.
- **Day 2, the rules:** gravity only works when you notice it; you cannot die, you only flatten; painted tunnels are real for the villain, not for you.
- **Day 3:** school, where the teacher's head explodes into a steam whistle.
- **Day 4:** anvils fall when anyone lies.
- **Day 5:** the colour starts draining, and the world turns black-and-white and grainy (an old-film effect).
- **Day 6:** a giant eraser in the sky.
- **Day 7:** "THAT'S ALL, FOLKS" style closing iris (our own wording) in 60 seconds.
- **Climax:** the family has to escape the iris.

**Why it wins:**
- A meta idea that only animation can do, and it showcases the expressive acting and smooth squash-and-stretch the owner wants.
- A familiar rule system: classic cartoon physics. No brand needed.

**Evidence:**
- It has the reference's structure (rule system, day escalation, a god reveal like the giant cursor). Direct title evidence was not found in this run, so this is a format bet, not a proven keyword.

**Visual potential (maximum):**
- A wild range of styles: rubber hose, a desaturated old-film day, a paint-tunnel gag.
- The most character acting per minute of any idea, with classic cartoon sound effects for every beat.
- It is the best showcase for "smooth, fast, expressive".

**Risk:**
- Lower search demand, so the click depends on the thumbnail.
- Must not copy Looney Tunes or Disney characters, catchphrases ("That's all folks" is WB) or music.
- Requires a high animation skill level to pay off, because it is easy to look cheap.

### 7. What If the Floor Really Was Lava for 7 Days? 🌋 (7.3)

**Premise:**
- **Inciting incident:** you shout "THE FLOOR IS LAVA!" and it becomes true.
- **Day 1:** the family is stuck on furniture, and Dad's slippers melt.
- **Day 2, the rules:** anything red is lava, rugs are safe, and stairs are rafts.
- **Day 3:** the commute to school is a parkour course over a lava city.
- **Day 4:** money is replaced by couch cushions, the most valuable thing on Earth.
- **Day 5:** the lava rises. Tone turn.
- **Day 6:** you discover who else shouted it, your little sister.
- **Day 7:** "Lava reaches the rooftops in 60 seconds". The town builds a cushion tower.
- **Sting:** "the ceiling is lava".

**Why it wins:**
- Every kid's game made real, which is instantly understood and has a built-in obstacle course for fast, kinetic animation.
- It echoes the reference's best beat ("anything glowing red is lava").

**Evidence:**
- The reference's "Rule 2: Anything glowing red is lava" sequence plus its obby/parkour days are its fastest passages: 132-134 BPM music and the densest sound effects.
- No title-level view data in this run.

**Visual potential (very high):**
- Glowing lava gradients, heat shimmer, and silhouettes against orange; ideal for "ultra" colour and gradient work.
- Parkour action with motion blur and whooshes, plus bubbling and sizzling sound beds.

**Risk:**
- "Floor Is Lava" is a Netflix show title, but the phrase is a generic game, so the risk is low as long as we avoid the show's branding.
- It is a single-mechanic idea, so the script must keep inventing variation.

### 8. What If You Were the Last Kid on Earth for 7 Days? 🌍 (7.2)

**Premise:**
- **Inciting incident:** you wake up and everyone is gone, including Mom and Dad, but breakfast is still warm.
- **Day 1:** the dream day (an empty mall, a whole candy store).
- **Day 2:** you drive a lawnmower down the highway.
- **Day 3:** loneliness, and you start talking to a mannequin.
- **Day 4:** the lights go off city by city.
- **Day 5:** a message on a billboard: "WE CAN SEE YOU".
- **Day 6:** you find out everyone is in a parallel copy of the town, separated by one second.
- **Day 7:** the glitch closes in 60 seconds, and you must reach the town clock.
- **Ending:** the reunion, and the sting is that the mannequin moved.

**Why it wins:**
- The strongest "What if" title in our NexLev data, with a kid-friendly twist instead of the adult survival version.
- Bittersweet emotion helps retention.

**Evidence:**
- Oddly Elsewhere's "What If You Were the Last Human on Earth?": 871K in 13 days (5.9x the channel average, about 2.8K/h).
- Stick Through Collapse's "Every Man on Earth Disappeared Except You: Day 1 to Day 100 (Full Movie)": 82K.
- Web search finds "What If You Woke Up and Discovered You Were the Last Human on Earth? 😨" and "What If You Were the Last Human on Earth?" (several channels), a proven but contested topic.

**Visual potential (high):**
- Empty-city wide shots with gorgeous light (golden-hour, blue-hour gradients) and a lone expressive kid.
- Silence used as a sound-design contrast (rare in the reference, so it is distinctive).

**Risk:**
- The topic is already taken by several "What if" channels.
- A lone protagonist means fewer characters to bounce off. The mannequin or a pet companion has to carry the dialogue.
- Can drift into melancholy and away from fast comedy.

### 9. What If You Shrank to the Size of an Ant for 24 Hours? 🐜 (7.0)

**Premise:**
- **Inciting incident:** a weird shrink ray or a wish app. The 24-hour clock starts.
- **The hours:**
  - 07:00 lost in the bedroom carpet jungle;
  - 09:00 the cat as a kaiju;
  - 11:00 riding a bee to school;
  - 13:00 a drop of water as a bowling ball;
  - 15:00 Dad's sandwich as a mountain expedition;
  - 18:00 the dishwasher flood;
  - 22:00 a spider standoff in the garage.
- **Climax:** the ray reverses in 60 seconds, but you must be outside or you will grow inside the doghouse.

**Why it wins:**
- Scale fantasy is endlessly visual, a shrink-and-grow trend is live this month, and there is no IP.

**Evidence:**
- Two near-identical uploads in October 2026: "What If You Shrank and Couldn't Stop?" (2026-10-16) and "What If You Shrank Until Your Garden Was Bigger Than the Universe?" (2026-10-18). That shows creators are chasing a current wave. Views are not available in this run.

**Visual potential (very high):**
- Macro worlds with depth-of-field blur gradients, giant faces of family members (great acting close-ups), and colourful insects with personalities.
- Sound designed at scale: a cat purr as an earthquake, a water drop as a boom.

**Risk:**
- The wave may already be crowded.
- Fewer family-gag opportunities, because the family is giant and mostly unaware.
- Needs careful scale continuity.

### 10. What If Your Pets Could Talk for 24 Hours? 🐶🐱 (6.8)

**Premise:**
- **Inciting incident:** a midnight pop-up offers "Enable pet voice? YES / YES".
- **The hours:**
  - 07:00 the dog's first words are "Is it walk? Is it walk?";
  - 08:00 the cat reveals it has been running the house;
  - 10:00 the goldfish forgets every sentence;
  - 12:00 the neighbourhood pets unionise;
  - 15:00 the hamster has a heist plan;
  - 18:00 the pets reveal what they really think of Dad.
- **Climax:** a 60-second countdown back to silence. Say the important thing.
- **Sting:** the cat keeps talking.

**Why it wins:**
- Universal appeal, character-acting heavy, many distinct voices (great for our multi-voice text-to-speech), and very shareable.

**Evidence:**
- Format fit with the reference (pop-up, family cast, countdown).
- No strong title-level view data in this run.
- Evergreen topic on YouTube Shorts and long-form, though not measured here.

**Visual potential (high):**
- Expressive animal faces (big eyes, ears as emotion indicators), a cosy, warm house palette, and fast comedic cuts.
- Each pet gets a sound signature: a squeaky toy, a bell collar.

**Risk:**
- Crowded with kids' animation, so there is a "made for kids" classification risk.
- Lower stakes than world-scale ideas, so the 24-hour countdown and a mid-video turn are needed.

### 11. What If the WHOLE WORLD Became Jurassic World? (literal franchise version) (6.6)

**Premise:** the same story as Idea 1, but branded with the franchise name in the title and on screen: Jurassic-style gates, park jeeps, raptor training, an island volcano.

**Why it wins:**
- It is the owner's exact pitch.
- "Jurassic World" carries big search and suggested-video volume from the films, toys and games.
- It mirrors the reference's brand-in-title move ("...Became Roblox").

**Evidence:**
- Web search shows the franchise surrounded by official and fan "what if" content: "Jurassic What If...?" (fan animated series), "'What if?' Jurassic Chronicles" playlist, "Jurassic World: Chaos Theory" (official animated series).
- Dinosaur "what if" uploads are frequent (§2.2).
- Brand-in-title worked for the reference: 364K in 2 days.

**Visual potential (high):** same as Idea 1, but we would be tempted to imitate the franchise's look, which is exactly what we cannot use.

**Risk (high):**
- "Jurassic World" and "Jurassic Park" are Universal/Amblin trademarks. The logo, gate, gyrosphere, named dinosaurs (Blue, Indominus Rex) and the John Williams theme are protected. The theme will certainly get Content ID claims, and a trademark complaint or demonetisation is possible.
- The search intent is mismatched: people searching the name want official clips and toys.
- Roblox is more permissive toward creator videos than Universal.
- Recommendation: use Idea 1, or "...Went JURASSIC?" with the generic word only.

### 12. What If You Woke Up 66 Million Years Ago? (7 Days in the Dinosaur Age) 🦕 (6.3)

**Premise:**
- **Inciting incident:** you fall asleep in the museum and wake up in the Cretaceous. A kid and his dad are on a school trip gone wrong.
- **Day 1:** no Wi-Fi, a giant dragonfly. **Day 2:** the rules (the big ones hunt at dusk; herds mean safety). **Day 3:** you befriend a baby ankylosaur. **Day 4:** a volcano. **Day 5:** a raptor ambush. **Day 6:** a bright new star in the sky, getting brighter.
- **Day 7:** the asteroid is 60 seconds away, so you race back to the time rift.
- **Sting:** the ankylosaur followed you.

**Why it wins:**
- Dinosaur demand plus a ticking doomsday clock (the asteroid) everyone knows, and it is educational-adjacent, which helps longevity.

**Evidence:**
- Web search: "What If You Woke Up in the Dinosaur Era? 🦖", "What If You Were Born in the Dinosaur Era?", "What If You Lived in the Age of Dinosaurs? (Surviving T-Rex, Raptors & Giant Monsters!) 🦖", "POV: You Wake Up in the Age of Dinosaurs", "Could You Survive 24 Hours in the Dinosaur Age? 🦖😱". The topic is heavily covered, and views are not available in this run.

**Visual potential (high):**
- Prehistoric landscapes with layered parallax gradients, volcanic skies, and a growing asteroid light that tints every shot more orange each day (a great colour arc).
- Big creature acting.

**Risk:**
- One of the most saturated dinosaur phrasings, and mostly documentary competition.
- It loses the "everyday life" comedy engine, because there is no house, school or Mom.
- Easy to become a survival list video.

### 13. What If the Immortal Snail Was REAL? 🐌 (6.2)

**Premise:**
- **Inciting incident:** you accept the meme deal: $10 million, but an immortal snail slowly follows you forever, and if it touches you, you die.
- **Day 1:** rich! **Day 2:** the rules (it is always moving and never stops). **Day 3:** you fly to Australia, and it is waiting at arrivals six months later. **Day 4:** you try to trap it, and everything fails. **Day 5:** it gets famous and the town cheers for it.
- **Day 6:** you realise it is lonely.
- **Day 7:** a 60-second showdown that ends in friendship.
- **Sting:** a second snail appears.

**Why it wins:**
- A known internet meme with a deadpan, slow-menace comedy engine and a single cheap, expressive character.
- It is trending right now.

**Evidence:**
- Two uploads in the last 9 days: "What If YOU Were The Immortal Snail?" (2026-10-30) and "What If The Immortal Snail Chased You and Never Stopped?" (2026-10-24). Views are not available in this run.

**Visual potential (medium-high):**
- One very expressive snail (eyestalk acting, a creepy smile, which fits the owner's "weird faces" note), contrast between fast human panic and a slow snail, and globe-trotting backgrounds.

**Risk:**
- The trend may be gone by the time we finish.
- Others are already on it.
- The death premise must stay comedic.
- Not a "whole world" scale idea.

### 14. What If Italian Brainrot Took Over the World? (5.8)

**Premise:**
- **Inciting incident:** a pop-up says "Brainrot mode: ON".
- **The days:** brainrot creatures replace animals (Day 1), everyone speaks in made-up Italian chants (Day 2), school becomes a brainrot quiz (Day 3), money becomes collectible creature cards (Day 4), the creatures fuse (Day 5), and the original meme-maker shows up (Day 6).
- **Day 7:** "Brain fully rotted in 60 seconds".

**Why it wins:** a huge, active kids' meme universe with ready-made absurd characters and endless remix demand.

**Evidence:**
- Web search: "What If EVOLUTION of SIX SEVEN 67 KID Was Real? (Italian Brainrot)", "ALL Italian Brainrot Animated!", "I CAUGHT ALL ITALIAN BRAINROT IN REAL LIFE! (FULL MOVIE)", "ITALIAN BRAINROT, but they're BABIES!". Euronews (2025-09) covers it as a mainstream phenomenon. Views are not available in this run.

**Visual potential (medium):**
- Bright and absurd, but the characters are someone else's designs. Original variants lose the recognition that drives the click.

**Risk:**
- The trend could decay by 2026-27.
- The characters' ownership is murky.
- Very young audience, with a "made for kids" and low-RPM risk.
- The owner wants quality storytelling, not meme remixes.

### 15. What If Dinosaurs Never Went Extinct? (5.0)

**Premise:** an alternate-history explainer: the asteroid misses, dinosaurs evolve alongside mammals, and we see a modern city built around them (dino traffic, dino farms, raptor police).

**Why it wins:** a classic evergreen search term with long-tail search traffic for years.

**Evidence:**
- Web search: "What If Dinosaurs Never Went Extinct?" (2026-08-18), "What If Dinosaurs Never Went Extinct? Could We Survive?", and many older versions. Very saturated, and dominated by documentary and AI channels. Views are not available in this run.

**Visual potential (medium):** worldbuilding vistas rather than character acting, so it does not play to the owner's top asks (acting, fast dynamics).

**Risk:**
- The most saturated topic of all, with an explainer tone and weak characters.
- Hard to beat established explainer channels, and a poor fit for our character-comedy direction.

## 5. Recommendation

1. **Make Idea 1, "What If the WHOLE WORLD Became a Dinosaur Park? 🦖".**
   - It keeps the owner's dinosaur instinct and runs on the reference's proven skeleton, with no franchise risk.
   - Thumbnail: a family on a suburban roof, a giant T-Rex face with a park wristband, and a big red "PARK CLOSING" countdown.
2. **Hold Idea 2 (Settings Menu) and Idea 3 (T-Rex hatched in your house) as the next two.** Idea 3 can reuse the dinosaur rigs built for Idea 1, which makes it a cheap second episode.
3. **Carry these into any topic:**
   - a cold open with stakes in the first 15-20 s;
   - a pop-up or ticket as the inciting incident at about 0:20;
   - day cards every 50-75 s with a whoosh, a hit and a music change;
   - a system/PA voice for rules;
   - Mom and Dad running gags that pay off in the climax;
   - a subscribe gag inside the story around 4:20;
   - a tone turn at about 60% of the runtime;
   - a reveal at about 70%;
   - a 60-second countdown climax;
   - "Almost.", then a comment prompt, then a sting.
   - Target 8:00-8:30, about 25 cuts per minute and about 40 sound effects per minute.
