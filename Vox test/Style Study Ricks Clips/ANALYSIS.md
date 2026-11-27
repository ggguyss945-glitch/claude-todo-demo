# Style study: Rick's Clips (@ricksclips3000)

This study covers five Shorts from the channel: *What the Grave Bell Really Meant*, *The Job Nobody Wants in
Japan*, *He Could Spot Winning Tickets Just by Looking*, *Why the Second Draw Always Wins* and *The Ancient Jar
That Warned an Empire*. It compares them with our current style and gives a verdict on switching.

## How it was measured

Every number below comes from the uploaded files. Nothing is estimated by eye unless it says so.

* **Narration:** Parakeet-TDT speech recognition on the isolated voice, with a timestamp for every word.
* **Voice and bed:** UVR MDX-Net split each mix into the voice and the music+SFX bed.
* **Loudness:** EBU R128 for the mix, the voice and the bed.
* **Voice pitch and formants:** pYIN for pitch, LPC for formants.
* **Music:** key from chroma profiles, plus tempo and onsets.
* **SFX:** hits more than 9 dB above the bed's median, lined up against the words being spoken at that moment.
* **Shots:** a 4-frame histogram distance, which also catches short dissolves.
* **Camera:** an affine fit of the optical flow, separating zoom, pan and tilt for every frame.
* **Colour:** CIELAB lightness, contrast, saturation and the a*/b* colour casts per shot.
* **By eye:** contact sheets at 1 fps, 10 fps strips across transitions, and full-resolution stills.

## 1. The numbers side by side

| | Grave Bell | Japan | Tickets | Second Draw | Jar | **Our *Perfect Score*** |
|---|---|---|---|---|---|---|
| Length | 59.6 s | 60.6 s | 63.3 s | 56.1 s | 63.0 s | 81.0 s |
| Words / speaking rate | 220 / 3.73 w/s | 225 / 3.72 | 231 / 3.69 | 219 / 3.93 | 229 / 3.65 | 273 / 3.40 |
| First word | 0.00 s | 0.00 s | 0.00 s | 0.00 s | 0.00 s | 0.00 s |
| Pauses over 0.55 s | 14 (longest 0.72) | 19 (0.88) | 13 (0.96) | 11 (0.64) | 14 (0.72) | — |
| Narrator median pitch | 174 Hz | 184 Hz | 198 Hz | 192 Hz | 180 Hz | 130 Hz |
| Pitch range (semitones, p5–p95) | −8.1/+8.3 | −7.6/+7.3 | −7.9/+6.6 | −7.9/+7.1 | −7.5/+8.3 | −6.4/+8.8 |
| Mix loudness / peak | −14.1 LUFS / −1.9 dB | −14.1 / −2.1 | −14.1 / −2.4 | −14.1 / −2.4 | −14.1 / −2.2 | −14.0 / −1.0 |
| **Voice above the bed** | **13.3 LU** | **16.6 LU** | **16.7 LU** | **16.2 LU** | **14.0 LU** | **4.6 LU** |
| Bed ducking under the voice | 1.5 dB | 2.6 dB | 1.6 dB | 3.2 dB | 0.8 dB | 2.5 dB |
| Music key / tempo | D minor / ~117 | D minor / ~117 | D minor / ~117 | E minor (weak) / ~112 | D minor / ~112 | B minor / 120 |
| Bed onsets per minute (music + SFX) | 76 | 44 | 68 | 25 | 48 | ~150 SFX events alone |
| Shots | 24 | 34 | 27 | 22 | 31 | 48 |
| Mean / median shot | 2.48 / 1.67 s | 1.78 / 1.53 s | 2.34 / 1.70 s | 2.55 / 2.36 s | 2.03 / 1.57 s | 1.69 / 1.63 s |
| Push-ins / pull-outs / static shots | 13 / 8 / 2 | 20 / 7 / 4 | 13 / 7 / 5 | 7 / 6 / 7 | 12 / 10 / 5 | — |
| Mean lightness L* / contrast | 44 / 20 | 55 / 21 | 44 / 25 | 47 / 21 | 46 / 18 | 44 / 24 |
| Saturation | 0.52 | 0.44 | 0.46 | 0.49 | 0.41 | 0.44 |
| Colour cast a* / b* | +18 / −10 | +7 / −11 | +11 / +3 | +13 / 0 | +12 / +2 | +6 / +13 |

**What the table says:**

* **The format is the same in all five.** Every video is 56–63 s and about 225 words, the first word lands at
  0.00 s, the mix is exactly −14.1 LUFS, and the music is D minor at about 112–117 BPM. This is one template
  applied five times.
* **The narration is faster and denser than ours.** It runs at 3.65–3.93 words/s against our 3.40, with almost
  no pauses: the longest gap is under 1 s.
* **The voice is a bright, animated male voice:**
  * Its median pitch is about 175–198 Hz. That is a high, energetic male register, well above the Loaded Dice
    narrator (125 Hz) and our voice (130 Hz).
  * Its formants (F1 ≈ 410 Hz, F2 ≈ 1600 Hz) sit in the same adult-male range as the Loaded Dice narrator.
  * Its pitch swings about ±8 semitones. It does character voices: "You go check! No, you go check.",
    "Hey, it's the toy guy!" and "Sir, that's impossible."
* **The music is almost background.** The voice sits 13–17 LU above the music+SFX bed, against 4.6 LU in our
  mix and 4.7 in Loaded Dice. The bed plays 100% of the time but very quietly. This is the opposite of what we
  built.
* **The music is the same kind of music every time.** The five beds are 0.81–0.86 alike on a chroma comparison.
  They are 0.86–0.89 alike with the *Empty Pot* bed, but only 0.73–0.83 with Loaded Dice and 0.71–0.78 with
  ours. It is a light, quirky low-mid underscore of plucks or pizzicato and bass, with 59–94% of its
  energy below 2 kHz; Grave is the brightest because of its bell. Nothing in it competes with the voice.
* **The bed is sparser than ours.** It has 25–76 detected onsets per minute, music notes and SFX together,
  against about 150 placed SFX events alone in our mix. The hits cluster where the story happens (see each
  video below).
* **Their cutting is slightly slower than ours** (1.8–2.5 s per shot against our 1.7 s), but **almost every
  shot moves:**
  * Push-ins are the default move, with pull-outs, pans and tilts after them.
  * Most shots also carry a slight continuous wobble, like a handheld or noise-driven camera.
  * Only 2–7 shots per video are close to static.
* **The colour is warmer and pinker than ours.** a* sits at +7 to +18, a magenta-red cast, while b* swings
  between cool blue nights and warm interiors. Ours leans yellow (b* +13).

## 2. The visual style

### Characters

* **The design is round-headed stick-figure people,** in the same family as the Cyanide & Happiness look:
  * A large cream-white sphere head with a thick black outline.
  * Faces drawn in flat black: dot or circle eyes, a single-stroke brow, and a simple mouth shape.
  * A capsule-shaped torso in a solid costume colour.
  * Thin black stick legs and arms ending in round blob hands.
  * Heads are mostly cream-white, with a few characters in a tan tone. Identity comes from props and costume:
    hats, wraps, uniforms, moustaches, glasses, a Chinese official's hat.
* **They are 3D models with toon shading,** not flat 2D cut-outs:
  * The heads catch real scene light. The grave doctor's face takes orange lantern light from below, and a
    moonlight shaft falls across the widow's face.
  * They cast soft shadows.
  * The camera orbits around them.
  * The outline weight stays constant at every distance.
* **The animation is limited animation, and that is deliberate:**
  * Bodies barely move: poses change, the characters slide on and off, and there are few full walk cycles.
  * The performance is in the face. Frame strips show mouth shapes swapping every 1–2 frames on dialogue, plus
    brow changes, blinks, sweat drops and dizzy spirals.
  * Big moments get 2D effects layered on the 3D: speed lines, fire streaks, smear frames and a sparkle on
    impact, as in the quick draw at 14–16 s.
* **Why it works:** a stick figure has no realistic hands, fingers or joints to get wrong. Small errors in
  contact or posing don't read as errors. This is the exact weakness our V3 had.

### Environments and props

* **The sets are fully 3D with toon shading and black outlines on the architecture.** Planks, bricks and window
  frames have drawn edges, and the textures are hand-painted with a slight storybook grain.
* **Every story builds a new world with dense prop dressing:**
  * a Victorian snowy village
  * a Japanese office tower
  * a lottery store and a printing factory
  * a Wild West street and saloon
  * an imperial palace (European-castle architecture with Chinese court costumes), a city and an army

  Each video has 5–8 distinct locations.
* **Diagram and cutaway shots explain the mechanism.** These are the channel's signature:
  * The ground in cross-section, with coffins and bell strings.
  * Number grids with the repeated numbers colour-highlighted.
  * A road map with gas-station pins circled in red.
  * The pendulum and rods inside the jar, seen from above.
  * An abstract pupil graphic for the idea of reacting without deciding.
* **Hero props are modelled in detail and shown in macro:** the bell, the "Vault Buster" scratch card, the
  death certificate, the dragon heads, the emperor's wine bowl with his reflection, the
  "CAREER DEVELOPMENT ROOM" sign.
* **On-screen text stays inside the world,** on signs, cards, a calendar page or a phone inbox, never as
  floating titles.

### Lighting and colour

* **Every frame has a motivated light source:** lanterns, a desk lamp, a sun or moon through a window, sunset
  backlight. It usually comes with **volumetric light shafts**, **bloom halos** and **floating particles**
  (snow, dust motes, embers).
* **The light is a story clock.**
  * In the grave story it goes from a magenta sunset (0–3 s) to a blue night (10–36 s), a warm interior, and
    finally a pink sunrise (52–59 s) as the bell stops.
  * In the jar story it goes from day in the palace to a golden sunset on the hill, a blue moonlit night when the
    balls drop, and an orange dust-filled morning after the collapse.
* **Warm and cool always share the frame:** a warm interior against a cold window, or a warm character light
  against a blue night. With the magenta push measured above (a* +7 to +18), the grade reads as a soft
  "storybook dusk".
* **Strong depth of field** throws backgrounds into soft blur on most close shots. A **vignette** and a slight
  **halation** (glow around bright edges) finish the look.

### Camera

* **Something is always moving.** Of 138 shots, 65 push in, 38 pull out and 47 pan, and almost every shot has
  a slow drift or wobble. Japan pushes the hardest (median +7% zoom per second). In the others, pushes and pulls roughly balance out,
  at −1.3 to +2.5%/s.
* **There are three kinds of transition:**
  * Hard cuts in the hook. Japan has three cuts in its first 1.3 s.
  * 0.2–0.3 s cross-dissolves between scenes, confirmed in the 10 fps strips at grave 10.0 s, draw 8.0 s and
    jar 13.5 s.
  * Push-through or whip moves into macro shots.
* **Typical setups:**
  * A two-shot at eye level for dialogue.
  * An over-the-shoulder POV for "imagine you…". In the second-draw story the camera sits behind your
    shoulder, looking down the street at Eddie.
  * A top-down for maps and diagrams.
  * A low angle for power: the emperor on his throne, the boss.
  * A slow orbit to show off a hero object, like the jar at 7–12 s.

### Captions

* **They show one word at a time,** occasionally two or three, karaoke-style and locked to the word timings.
* **The style:**
  * White heavy rounded sans with a black outline and a soft drop shadow.
  * Centred on the width, at **70.3% of the height**.
  * About **54 px glyph height at 1080 wide** (5% of the frame width). That is smaller and calmer than most
    Shorts captions, and it never covers faces.
* **Ours** are phrase captions at 71.65% of the height. The position is almost the same; the granularity is not.

## 3. Story engine (all five)

| Beat | Grave Bell | Japan | Tickets | Second Draw | Jar |
|---|---|---|---|---|---|
| **Hook (0–3 s): a paradox stated as fact** | "They buried a man alive with a bell tied to his finger." | "It's impossible to get fired in Japan, but companies found something way worse." | "Look at these two scratch cards. One's a winner and one's garbage." | "The fastest gun in the West had one rule: never draw first." | "He put a bronze ball in a dragon's mouth and told the emperor, if this ever falls out, run." |
| **Context (3–8 s)** | "You see," safety coffins | "Imagine" (second person) | "Yet there's a way to tell" | "Imagine you're standing…" (second person) | "See," eight dragons and frogs |
| **Escalation, a turn every 2–6 s** | Except, Then, now, But | Then, Every Friday, Still | But, So, which means | So, Yet, But | But, Weeks later, Now, So, Then |
| **Mystery peak (20–36 s)** | "Wait, practiced?" (36.0) | the happy guy in the corner (33.3) | "how does the machine know?" (17.4) | "How is that possible?" (19.8) | all eight balls drop and the guards laugh (32.9–43.6) |
| **Reveal** | "Well, he was never dead." (37.1) | "Then, one Monday… he's gone." (42.5) | the "loners" pattern (39.3) | "You see, think about the last time your phone slid off a table." (36.5) | the palace in rubble, then the pendulum (45.9–52.5) |
| **Explanation and twist close** | "You see… every debt got buried right along with him, and the house was all hers." | "You see, Japanese law…" (49.3) | sorted unscratched cards, the game pulled (52–60) | "Eddie never decides anything." | "All eight meant the biggest earthquake the empire had ever—" |
| **Ending** | Dark ironic twist | Dark punchline, then "Mm." | Real-world consequence | Clean explanation | **Cut mid-sentence: a loop back into "He put a bronze ball…"** |

**The rules behind it:**

1. **The first sentence is a paradox or impossible rule,** said flatly as fact over its literal image, with a
   hard-cut flurry and an SFX hit cluster in the first second. Grave, Japan and Draw each have hits about
   20 dB over the bed between 0.0 and 1.7 s.
2. **"You see," or "Imagine" lands within 3–5 s** and turns the paradox into a mechanism the viewer wants
   explained.
3. **The story is a single protagonist following one thread.** Turn words come every 2–6 s.
4. **The midpoint question is spoken out loud:** "Wait, practiced?", "How is that possible?"
5. **The explanation arrives late (36–54 s) through an everyday analogy or a cutaway diagram,** then a short
   ironic closer. Several endings are cut so the last line flows back into the first.
6. **Character voices inside the narration** ("No, you go check.") give comic relief every 10–15 s.
7. **The stories are real history or real cases, dramatized:**
   * the 19th-century safety coffins with bells;
   * Japan's *oidashi-beya* "expulsion rooms";
   * Mohan Srivastava's 2003 cracking of an Ontario scratch-card game;
   * Niels Bohr's observation that the second gunfighter to draw wins;
   * Zhang Heng's seismoscope from 132 AD.

## 4. How the narration and visuals connect

**Almost every noun or verb gets its own shot or its own change inside a shot.** That is why the cut rate feels
high even though shots average 2+ s. Examples with timestamps:

| Line | Picture |
|---|---|
| "a bell tied to his finger" (grave 1–2 s) | The coffin from above, with the string running up from his finger. |
| "graves came with a little bell on top" (4–9 s) | A cross-section of a row of graves, then a push-in to the bell. |
| "Three short, one long." (32.8 s) | The bell rings again right on the line (hits at 32.8–33.3 s) while the camera holds on the wife's face. |
| "no computer and no work" (Japan 8 s) | An empty desk with tape outlines where the computer used to be. |
| "Your new job is… nothing" (14–15 s) | The boss opens a gift box, and it's empty. |
| "The emails stop" (24 s) | A phone screen showing Inbox (0). |
| "most of the numbers show up two or three times, but a few only show up once" (Tickets 32–39 s) | The number grids light up in colour, number by number. |
| "clean them out" (45–47 s) | A state map, with a pointer and the gas stations circled in red. |
| "lose a race to the saloon against a guy carrying two beers" (Draw 21–25 s) | The literal race. |
| "think about the last time your phone slid off a table" (37–43 s) | A smartphone on a Wild West poker table, a deliberate anachronism gag. |
| "Not even a ripple in the emperor's wine" (Jar 20 s) | A macro of the wine bowl, with the emperor's face reflected. |

**Sound follows the words the same way:**

* **Grave:** the bell rings at 10.2–11.5 s ("starts ringing"), again at 32.8–33.3 s ("Three short, one
  long"), and once more at 48.5 s ("listening to it ring").
* **Jar:** thuds at 27–29 s ("threw the inventor out… jar and all"), drops at 34.8–35.1 s ("a ball dropped,
  then another"), a 21 dB collapse at 45.9–46.9 s ("pile of rubble"), and rumbles at 60–62 s ("earthquake").
* **Japan:** a run of hits at 55.5–56.3 s on "they take away your work".

## 5. How each video is put together

### What the Grave Bell Really Meant (59.6 s, 24 shots)

**Locations:**

* a sunset graveyard
* the cross-section diagram
* a snowy night cemetery
* the neighbour's attic bedroom
* a village street with porches
* the widow's dark parlour
* a daylight flashback in town and the garden
* a sunrise graveside

**Strongest moves:**

* The cross-section diagram, which makes the premise instantly clear.
* The bell SFX returning each time the narration mentions it.
* Time of day used as a clock, with the moon turning to sunrise as she sits all night.
* The final shot: the widow pats the grave mound with her shovel and smirks.

**Colour:** the most saturated of the five (0.52), with the strongest magenta cast (a* +18).

### The Job Nobody Wants in Japan (60.6 s, 34 shots)

**Second person throughout ("your boss walks you…").**

**Locations:** the boss's office, with a big red FIRE EMPLOYEE button and a 誠 scroll; the green-tiled "Career
Development Room" (yellow sun patch, clock); the open-plan office; the office tower at night; a dim corridor under
a lamp.

**The fastest cutting of the five** (mean 1.78 s) and the hardest push-ins (+7%/s median).

**Recurring motifs:**

* The wall clock, for time passing.
* The boss's fixed grin at the door every Friday.
* The empty chair pushed in.

**The ending:** the camera looks through the door's window at you, now the one left alone, and the narrator says
"Mm."

### He Could Spot Winning Tickets Just by Looking (63.3 s, 27 shots)

**Opening:** the two-card hook colour-codes the winner (gold glow) and the "garbage" (green tint).

**The heaviest data visualisation:**

* macro number grids with colour highlighting
* the printing factory's "WINNERS 400,000" counter
* the state map with pins

**The topic is a lottery,** which is gambling and outside our channel's rules. Use it only as a reference for
technique.

### Why the Second Draw Always Wins (56.1 s, 22 shots)

**Second person:** "you" are the challenger, filmed over your shoulder down the street.

**The most stylised effects:**

* anime speed lines
* fire streaks
* smear frames
* a sparkle on impact during the draw

**Contrast between scenes:**

* a golden sunset when the riders arrive
* a warm saloon interior
* a blue night at the telegraph office

**The explanation is an everyday analogy** (catching a falling phone), illustrated with a deliberate anachronism.
It is the only one of the five without a final twist, and it has the fewest SFX (25/min).

### The Ancient Jar That Warned an Empire (63.0 s, 31 shots)

**The biggest production of the five:**

* the palace throne room
* a balcony over a huge army
* the city gates
* the sunset hill
* the moonlit hill
* the portcullis
* the morning collapse with a smoke column
* the internal mechanism cutaway

**Camera:** an orbit around the jar when it's introduced, a top-down symmetric view for the mechanism, and a
macro of the dragon's jaw opening.

**The ending is cut mid-sentence** ("…the biggest earthquake the empire had ever"), so the video loops straight
into "He put a bronze ball…".

## 6. Their style compared with ours

| | **Our current style** (Loaded Dice / *Eye in the Sky* family) | **Rick's Clips style** |
|---|---|---|
| Characters | Low-poly bodies with semi-realistic painted faces. Realistic proportions mean hands, contact and gait all have to be correct. | Round-head stick figures with drawn faces. There are no fingers or realistic joints to get wrong. |
| What a viewer forgives | Very little. A hand off a prop or a foot sliding is obvious, which was the complaint about V3. | A lot. Limited animation is the look. |
| Facial acting | Subtle, and it can look stiff. | Big and readable at phone size. Mouth flaps and swapped expressions are cheap. |
| Environments | Fairly sparse sets are acceptable. | Dense, painterly, outlined sets, 5–8 per story, plus cutaway diagrams. **This becomes the main cost.** |
| Lighting and post | Bloom, grade, vignette, grain. | The same, **plus** toon shading, outlines, depth of field, volumetric shafts and particles. These are one-time pipeline work. |
| Camera | Purposeful moves, hard cuts. | Almost every shot moving, 0.2–0.3 s dissolves, macro and top-down setups. |
| Voice | Deep and serious. The bed sits 4–5 LU under it. | Bright, fast, comic, with character voices. **The bed sits 13–17 LU under it.** |
| Music and SFX | Score that drives the cut, with ~150 SFX per minute. | Quiet, constant pizzicato bed and 25–76 SFX per minute that illustrate the words. |
| Tone | Serious "how it works" exposé. | Comic, dark-ironic storytelling. |

### Which is easier and faster to make

**Characters and animation: Rick's style is much easier.**

* A character is a sphere, a capsule and four sticks, plus a face drawn from a dozen shapes. I can generate a new
  costume in minutes, compared with hours for one of ours.
* Most of our *Perfect Score* time went into making realistic motion correct: arm IK, hands on desks and papers,
  planted feet, desk pushing, and fixing pops. This style needs a fraction of that.

**Environments: Rick's style is harder.** Each story needs several richly dressed new locations and at least one
diagram. Our pipeline builds sets in code, so this becomes the main per-video work, and it is where we would be
weaker than them at first.

**Audio: the mix is easier,** because it is a quiet bed with fewer SFX. The voice is harder. This style lives on
a comic, acted read, and synthetic narration is weakest at exactly that.

**Overall:** after a one-time pipeline build (toon shader and outlines, a character generator with drawn faces,
depth of field, light shafts and particles, word-by-word captions, dissolves), a Rick-style video should take
**less time than *Perfect Score*** and show **far fewer visible animation errors**. The time saved on animation
moves into set building.

### Can I copy this style exactly, 1:1?

**The style: very close.** Everything measurable can be matched, because it is all just parameters:

* character proportions, outline weight and face language
* toon shading ramps
* palette and grade (a* and b* targets, saturation, lightness)
* depth of field, bloom, light shafts and particles
* the camera grammar: push-in rates, wobble, 0.2–0.3 s dissolves, macro and top-down setups
* the caption style (one word, 70.3% height, 5% glyph size)
* the mix (−14.1 LUFS, voice +13–17 LU over the bed)
* the music (D minor pizzicato bed at ~115 BPM)
* the SFX placement rules

**The sets: close, but not identical.** Their environments look hand-built and hand-painted, prop by prop. I
build sets procedurally in code. I can reach the same look and lighting, but at first our sets will look somewhat
simpler and less cluttered than theirs, and closing that gap costs time on every video.

**Their exact characters, sets and scripts: I don't recommend copying these 1:1.** A visual style can't be owned,
but their specific character designs, branding and scripts are their work. A literal clone would read as a
knock-off channel, both to viewers and to YouTube's reused-content review. The right move is **the same style
family with our own character design:** a different head shape or colour, a signature detail, and POLYWIT's
red-ink accent. Their format and storytelling rules are free to use with **our own stories**.

### Is switching to this style the logical choice?

**Yes, with three conditions.**

**Why it makes sense:**

1. **It removes our biggest quality problem.** The complaints about V3 (wrong actions, items not moving with
   hands) come from realistic characters. Stick figures with blob hands don't expose those errors.
2. **It is faster per video** once the pipeline exists. Character work drops sharply.
3. **It fits POLYWIT.** "Smart stories, honest wins" suits clever historical stories with ironic twists, it is
   naturally family-friendly, and the name still works because the look is still 3D.
4. **It is a proven format:** the same template applied consistently, with a loop-friendly ending.

**The conditions:**

1. **Our own character design,** not a clone (see above).
2. **A short pilot first.** Before switching, I'd make an 8–10 s test shot: one character, one dressed set,
   depth of field, light shafts and the word-by-word caption. You compare it side by side with their frames.
3. **The best possible voice.** In this style the narrator is half the entertainment. A human voice actor
   matters even more here than in the Loaded Dice style. If we stay synthetic, I would cast a brighter, higher
   voice (around 175–195 Hz) and direct each line separately, with separate takes for the character lines.

**What it costs:**

* A one-time pipeline rebuild.
* New branding renders: logo, banner and thumbnail in the new style.
* More set building per video.

**One limit on this study:** I couldn't read the channel's view counts or subscribers, because this environment
can't reach youtube.com. If you send screenshots of their Shorts grid, as you did for Loaded Dice, I can add a
performance comparison.

## 7. Using their format for our stories

These topics are true, halal, and use the same engine: a paradox hook, then the mechanism, an escalation, the
question asked out loud, a "You see," explanation, and an ironic loop ending.

| Story | Hook line in their style |
|---|---|
| **Ibn al-Haytham and the Nile.** He promised Caliph al-Hakim he could control the Nile flood, saw it was impossible, and pretended to be mad to stay alive. While under house arrest he wrote the *Book of Optics*. | "He pretended to be insane for ten years… and changed how the world understands light." |
| **Archimedes and the crown.** The king suspected a goldsmith of mixing silver into his gold crown. Archimedes caught the cheat with a bathtub. | "The king's crown was perfect. That's how they knew someone was lying." |
| **Eratosthenes measures the Earth.** He used two shadows, one well and a paced-out walking distance. | "A librarian measured the whole planet… with a stick." |
| **Semmelweis and the hand-washing rule.** Doctors laughed at it; deaths at his clinic fell from about 10% to about 1–2%. | "One rule cut deaths by almost ninety percent, and the doctors hated him for it." |

*The Ancient Jar* (Zhang Heng's seismoscope) would also fit our rules, but it's their video, so I would choose
a different story.
