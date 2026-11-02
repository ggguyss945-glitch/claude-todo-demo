# Production bible: "What If the WHOLE WORLD Became a Dinosaur Park?" (title gets one emoji on upload, as the reference does)

Creative director's bible for our next video, written from the measured study of the reference **"What If the WHOLE WORLD Became Roblox?"** (8:02, 364K views in 2 days). Source data: `study/all_findings.json` (same folder as this file). Unless marked otherwise, every timestamp below is **full-video time in the reference** (chunk times were converted: c1 = 1:36 + t, c2 = 3:12 + t, c3 = 4:50 + t, c4 = 6:26 + t).

**Data caveats, stated once.**
- The first 0.7-5.4 s of each reference chunk has audio but no picture (c0 3.87 s, c1 4.89, c2 1.94, c3 5.38, c4 0.66), so about 17 s of the 8:02 was never seen, including the opening hook line (0:00-0:03.9).
- I cannot listen to audio. Every sound judgement is measured (stems, onsets, LUFS, pitch).
- NexLev was rate-limited, so the reference channel's name and outlier data are missing.
- Our own Ep.2 numbers come from `episodes/ep2/timeline.json`, `episodes/ep2/voice.json`, the Ep.2 render logs and the audio study. Ep.2's frame-motion percentage was never measured.
- Cut counts come from two methods that disagree. An automatic detector on the full video finds 206 cuts (25.6 per minute); hand-checked per-chunk counts find 220 hard cuts in the 7:45 of visible picture (28.4 per minute). The detector misses cuts in c0 and c4 and fires on in-shot accents in c2. Where they differ, the hand counts are used.
- Still-frame shares are recomputed on one threshold for all chunks (mean frame difference ≤0.05 on the 0-255 scale, frozen padding at chunk starts excluded), because the chunk reports used different thresholds.
- This bible and the study live in the scratchpad, which a container restart can wipe. P1 copies them into the project (7.4).

---

## 0. The contract: what "matches the reference" means, in numbers

Every row below is a pass/fail gate in QA (section 3.10). The numbers are necessary, not sufficient: they make the video move and sound like the reference, while the faces, the jokes and the critic pass in 3.10 decide whether it is as good.

| Metric | Reference (measured) | Our Ep.2 | Target for the next video |
|---|---|---|---|
| Runtime | 8:02 | 15:22 | 7:45-8:30 |
| Hard cuts per minute | 24.6-31.6 per chunk by hand count (28.4 over all visible picture); 25.6 by the automatic detector | **10.6** (Ep.1 14.9) | 25-30 |
| Setup changes per minute (cuts + whips + snap zooms) | 30-40 | ~11 | ≥30 |
| Median shot length | 1.45-1.8 s | **5.1 s** | ≤1.9 s |
| Shots longer than 6 s | 1 (6.1 s, kept alive by UI and a +31% push) | **59 of 163** (17 over 10 s) | 0 without internal events |
| Still frames at 60 fps (mean difference to the previous frame ≤0.05/255) | 1.3-1.9% per chunk; longest still run 16 frames, except the 35-frame "tree." deadpan freeze (1:24.1) | not measured | ≤3% on the same measure; no still run over 16 frames unless it is a tagged gag freeze (≤40 frames) |
| Shots with camera motion | ~100% (push of 1-6% or more) | minority (static plates, cards) | 100% |
| New gag or visual idea | every 2-4 s (Day 1: 14 gags in 56 s) | every ~10-20 s | every ≤4 s |
| Face changes on a speaking or reacting character | every 0.35-2 s, on the stressed word | rare (7 expressions in total) | every ≤2 s |
| Expression vocabulary | about 25 eye/brow/mouth states plus add-ons | 7 | ≥24 |
| Lip-sync | 4-5 visemes, each held 2-6 frames | none | 5 visemes, holds of 3-8 frames |
| Words per minute | 133 overall, 156 while voiced, 174 inside sentences | slower, horror read | 130-140 overall, 150-160 while voiced |
| Longest gap between voice lines | 1.46 s, and every gap over 1 s carries a sound gag | many long silences | ≤1.5 s |
| Non-narrator voice line | every ~6 s (81 lines, 6-7 voices), each 1-8 words | 32 lines in 15:22 (one every ~29 s), 3 character voices | every 6-8 s, 5-6 voices, 1-8 words each |
| Sentence length (narration) | median 4 words; 30% of sentences are 1-2 words | longer, procedural sentences | median ≤5 words; ≥25% of sentences 1-2 words |
| SFX events per minute | ~40 average, 60-75 in action | **~4** (62 timeline cues in 15:22, plus ambience beds) | 40 average, 60+ in action |
| Cuts with an SFX transient within ±0.1 s | 47% | not measured | ≥50% |
| Music presence | 96.4% | lower | ≥95% |
| Deliberate music drops | 20 (2.5 per minute), each 0.3-2 s, hard cut with a downbeat slam-back | 15 slow fade-outs (0.15-1.0 s) into silence, no slam-backs | 2-3 per minute, hard cut and slam-back |
| Music texture changes | ~10 per minute; cue change on every chapter card | 36 cue starts (~2.3 per minute) | ~10 per minute |
| Integrated loudness / LRA | -14.0 LUFS / **3.0 LU** | -13.9 / **11.0 LU** | -14 / ≤4 LU |
| Silences ≥0.4 s at -40 dB | 1 | **24** | ≤2, designed |
| Voice minus background (short-term median) | +14.3 dB | not measured | +13 to +15 dB |
| Script overlap with the reference transcript | n/a | n/a | **0** shared runs of 4+ words, except the title formula "What if ... the WHOLE WORLD ..." (7.12) |

---

## 1. What makes the reference work, ranked by impact

### 1.1 The gag engine: a known rule system collides with ordinary life every 4 seconds (largest impact)

- **Premise mechanics.** Every joke is a real Roblox mechanic applied to family life, and each one is proven on screen by a UI element. Day 1 alone has 14 gags in 56 s (0:38-1:34): daily-reward alarm, block hands, plastic bed, stud floor, nametag, hotbar toothbrush, stair jump with fall damage, chat bubble, click-to-eat, "tastes like plastic", square sun, block clouds, cloned trees, and Dad stuck walking into a wall.
- **The 4-beat recipe, used every time** (c1 analysis, 1:36-3:12). A payoff lands every 5-8 s:
  1. A one-line premise with a HUD card.
  2. A literal visual demo, escalating in threes: roof → neighbour's roof → passing bird → the whole neighbourhood becomes an obby (1:41-1:49).
  3. A twist that hurts somebody: the hot tub is lava and the hero explodes (1:53-1:56); "immortal!" is answered by "stop respawning on my clean sheets!" (2:03-2:07).
  4. A reaction close-up or deadpan button.
- **Escalation inside each day:** personal (hands, bed), then the house (stairs, Mom), then the world (sun, clouds, trees), ending on the biggest character gag (Dad BONKs into the wall for 45 minutes, 1:26-1:34).
- **Callbacks.** At least 7 planted gags all pay off in the climax: Dad and the car (1:30 → 7:38), the "sweetie" chat bubble (1:04 → 7:46), 40 hats (4:08 → 6:43), the T-pose as a platform (5:03 → 6:57), the roof/bird route (1:41 → 6:56), 99 Robux (3:31 → 6:01), and the yes-only pop-up (0:26 → 6:33).
- **Running state persists across shots.** After 1:02 the health bar stays reduced. Dad stays T-posed in every later appearance (5:09-6:24). Mom's hat tower keeps growing.
- **Chapter clock.** DAY cards land every 46-73 s (0:37, 1:35, 2:26, 3:18, 4:31, about 5:15, 6:06), on top of a ticking stakes clock: 60 seconds of server life, set in the hook.
- **Second-person narration** ("you") plus POV hands (0:22.75, 0:43.5) makes the viewer the culprit.
- **Who speaks when.** The usual unit is a narrator set-up, then one character or system punchline of 1-8 words on a close-up with a face change, then a deadpan narrator tag. Characters almost never hold a back-and-forth conversation.
- **Re-hooks.** A rhetorical question roughly every 25 s, and a question or threat every 5-10 s in the Day 6-7 stretch, alternating dread and joke.

### 1.2 Pacing: something new every 1-2 s, and no frame is ever dead

- **Cut rate.** The automatic detector finds 206 cuts in 8:02 (25.6 per minute, median shot 1.8 s). Hand counts per chunk give 30.6, 31.6, 28.7, 26.5 and 24.6 hard cuts per minute (28.4 overall). Counting whips, snap zooms and flash frames, 30-40 setups per minute (c3 30.5, c2 35.6, c4 about 40).
- **Long takes only when action carries them.** The 4.4 s jump crane (1:41.4) and the 6.1 s tablet POV (0:22.75-0:28.9) are held up by a +31% push and constant UI typing.
- **Motion.** At 60 fps, 98-99% of frames differ from the previous one: on one threshold for every chunk, only 1.3-1.9% are still. Even "hold" shots keep 55-77% of their frames moving (c4). Holds keep moving through camera drift, sparkle twinkles, blinking cursors and idle bobs.
- **Every shot has camera motion.** Measured pushes: +14% (0:17.3-0:20.5), +31% (0:22.75-0:28.9), +24% (1:12-1:17), +30% (1:33.9-1:36), +18.8% (3:25.9-3:28.4).
- **Stillness is used only as a joke.** The AFK Dad close-up has 12% duplicate frames (2:11.3). "Disconnected" is 4.6 s of dead air with the music cut (2:13.5-2:18.1).
- **The picture leads the sentence by 0.1-0.5 s.** Cuts follow sentences, not the music beat: only 18 of 57 cuts in c2 land on a beat.
- **One picture beat per noun, payoff on the last word.** "Roof... bird... hats... and Dad" is four separate landings about 0.8 s apart (6:56.6-7:00.1), and "Cloud... cloud" is one hop per word. The visual payoff lands on the sentence's last word: the stamp on "DELETED", the counter hitting 1,000 on "trucks!".

### 1.3 Characters that act with their faces

- **Face changes.** One new expression per caption chunk, every 0.35-2 s. The record is 8 faces in 3 s (Dad, 5:12-5:15). Swaps are instant, with no in-betweens: smile → O-shock → zig-zag fear lands on "glowing / red / is LAVA" (1:51.1-1:51.5), and the O-shock "take" lasts only 2 frames. For emphasis a character lurches toward the lens: the head grows about 25% in 2 frames (1:51.85).
- **Library.** Ring eyes with a dot pupil, half-lid, closed arcs with blush, star eyes, money/coin eyes, teary, squint/wink, and red glowing eyes. Brows: worry, angry, flat. About 8-10 mouths: D-open with teeth and tongue, grin, small o, wavy panic, flat, smirk, yawn, scream O, gritted grid, tongue-out. Add-ons: sweat drops that grow and slide, tears, ?/??, Z's, hearts, dizzy stars, and a bump with orbiting stars.
- **The punchline is a deadpan held for about 1 s**, usually with the music cut: "Plastic." 0:45.1, "plastic." 1:15.4 (music silent 1:15.75-1:17.0), "tree." 1:24.0, "Mom. You can't fit through the door." 4:13-4:18.
- **Lip-sync.** The mouth changes on almost every 2-frame sample (0:13.47-0:14.43). The teacher uses 4 shapes, each held 2-6 frames (2:35.3-2:36.6). The hero lip-syncs the narrator's "you" lines (6:33-6:36.7).
- **Body.** Rigid blocks. All the elasticity comes from snapping between poses in 4-8 frames, plus whole-body springs on impact: on Dad's BONK the body drops 20 px and settles in 7 frames (4:55.7). A nervous character jitters 1-3 px every frame, and the scream close-up jitters 4-8 px per frame (7:59.4).
- **Listeners react while others talk:** the hero's eyes widen one step per hat (4:06.5-4:08.5). Group reactions swap on the same frame (2:48.6).
- **Chibi proportions.** Head, torso and legs are roughly 1:1:1, so faces read even in wide shots.

### 1.4 The hook (0:00-0:37): open on the ending, rewind, and make the viewer the culprit

- 0:00-0:03.7: the title question is restated.
- 0:03.9-0:05.4: "Seven days." A calendar tears through its pages.
- 0:05.4-0:06.6: "One game." A game card dives into its thumbnail.
- 0:06.6-0:10.4: a time-lapse to a crimson apocalypse and "60 seconds left".
- 0:10.45: the system voice: "Server shutting down in sixty seconds."
- 0:13.3: the hero breaks the fourth wall: "Okay, okay, I can explain!"
- 0:16.2: VHS pause and rewind, with 2-3-frame flash-forwards of later set pieces.
- 0:17.3: "Last night. 2 a.m."
- 0:26-0:27.8: the first joke. "Yes... or yes." The NO button turns into YES.
- 0:33.75: the irreversible press, "You pressed... yes." A sub boom (0:34.16), a grid infection, then a transformation that scales outward: room, house, street, planet. An echoed "yes" at 0:35.2 keeps the voice gap under 1.5 s.
- 0:36.85: DAY 1.

That gives stakes and a deadline by 10 s, three voices by 15 s, and an open loop (the 60 s countdown) that runs the whole video.

### 1.5 Sound design: every visual event has a sound, and the music is edited like picture

- **SFX density.** About 40 SFX per minute on average; 60-75 per minute in the climax (6:50-7:10). Never more than about 3 s without a hit. 68% of the SFX play under dialogue: they are not kept out of speech, only 1.6x denser in the gaps.
- **Sync.** 47% of cuts have a transient within ±0.1 s (chance is 22%). The median SFX-to-cut offset is -16 ms. Every on-screen sound word has a matching sound on the same frame: CHOMP sound 3:16.58 vs text 3:16.567, DAY 5 slam 4:30.71 vs 4:30.717.
- **Palette: cartoon plus game UI.**
  - Sub booms on stakes beats (0:03.89, 0:07.49, 0:08.92, 0:34.16).
  - Slide-whistle falls (1:01.0-1:01.8).
  - Boings, one per jump (6:55.8-6:59.2).
  - A stepped arpeggio on the stairs (0:58.7-1:00).
  - Tape rewind (0:16.2-0:17.3).
  - Typing blips (0:23.4-0:28).
  - Error buzzer (2:53.2), two-tone alarm (6:07.7), sirens (6:15-6:38), brass TA-DA (7:39.6).
  - Cartoon dizzy-bird tweets at about 5 kHz after every head bonk (1:31, 4:56).
- **Layering.** A typical hit has 2-3 layers on one frame: a transient, a tonal accent and a tail.
- **Music.** Present 96.4% of the time, at about 123 BPM, with about 10 texture changes per minute and a new cue on every DAY card. It is deliberately stopped 20 times (2.5 per minute) on punchlines, then slams back on the next downbeat; the strongest onset of c0 is at 1:17.15. There is also a tape-stop (6:01.6) and a music bus that "lags" (4:53).
- **Voices.** 6-7 of them, with a two-register narrator: deadpan at 100-140 Hz, hype at 180-330 Hz. A non-narrator line every ~6 s.
- **Mix.** -14.0 LUFS, LRA 3.0 LU, voice +14.3 dB over the bed, ~4 dB ducking, and the bed pushed about +10 dB in the climax.

### 1.6 Visual finish: a clean "toy plastic" vector look

- **No grain, no line boil, no vignette.** A flat sky patch measures a standard deviation under 1, and the corner pixel equals the centre at the same height.
- **Every surface is a 2-stop gradient** of about 10-15% luminance, plus a gloss strip (white at 25-45% opacity) along the lit edge. Skies and props run top to bottom; block faces and faces run top-left to bottom-right, from a key light at the upper left (c3, c4). Example: hero torso #FF8467 → #DA4E2F with a #FF9A81 sheen (1:51.6).
- **No cast shadows.** Only soft contact ellipses under feet, and soft ground ellipses under lifted objects (5:23.6).
- **Outlines are tinted, never black:** the darker shade of each fill. Width scales with depth: about 2-3% of head height on the hero, 0.4% of frame height on props, 1-2 px on far houses, and no line at all on clouds and far skyline.
- **High-key, saturated palette with one hue family per scene.** Sky #1F81FB → #72BEFC. Apocalypse #55070C → #AB1617 with mauve far buildings. Violet night #483664/#5562A4 with motivated light pools.
- **Depth.** Atmospheric desaturation on far layers. Depth-of-field blur only in close-ups (6:33-6:36.7). Motion blur only on whips.
- **State grades tell the story.** Death or disconnect: saturation 101 → 45, luma 159 → 80 (2:13.5). Time-lapse to night: chroma -26% (5:07.5). Red act with a flash frame (6:11.8). Lavender flashback (6:30.4). The restored world has a flat blue sky (7:30.9).

### 1.7 The game UI is the storytelling layer

Each joke is proven by a diegetic UI element, never just narrated:
- Toasts (0:40.2 "Daily reward claimed!").
- A hotbar (0:55) and a "-50" health hit (1:02.15).
- A Studio selection box with dimension labels on the sun (1:19.2).
- An AFK counter running 00:00 → 20:00 in 1.25 s (2:12.0-2:13.3).
- "Disconnected" (2:13.5), "Dad joined the game" (2:23), and a stack of badge toasts used as spam (3:03.9).
- A GAMEPASSES card (3:29.9).
- A ping meter from 38 to 9,000 (4:30.9-4:48.4).
- An editor window whose output log calls back earlier gags (5:35.3).
- A copy-paste counter to x1,000 (5:57-5:59.3), a countdown dial (6:13 onward) and a game menu (7:14.3).
- In the climax, two clocks at once: a world-space dial that pops only on key numbers (46, 38, 30, 10, 5-4-3) and a corner timer pill that turns red at 0:10 and freezes at 0:03. A waypoint pill shows the live distance to the goal ("MENU 10,000 studs" → 9,994 as the crowd jumps, 6:40-6:41.4).

UI elements enter in 4-10 frames with overshoot and a flash ring, and each has its own SFX. The CTA lives inside the story too: the golden name tag vs "default noob, forever" (4:18-4:30), and "Comment OOF" (7:50.9).

### 1.8 Camera and animation craft

- **Default move:** a slow push of 2-6% with easeInOutSine.
- **Punch-in on stressed words:** 1.06-1.3x, settling over 0.25 s (3:38.05 "of GAS?!", 5:32.7 "GAME.").
- **Big snap zooms as cut substitutes:** x1.6 in 0.28 s (4:20.5); about 2.2x out and 2.5x in over 26-27 frames (6:28.2, 6:29.3); an expo punch-in of about 3.8x in 15 frames (7:11.2). The continuous zoom-out into the editor UI is about 4x in 0.85 s (5:34.5).
- **Snap zoom-outs to reveal scale:** to x0.53 in 0.37 s (1:46.1), and to x0.51 on the 40-hat tower (4:10.7).
- **Whips, two velocity shapes:** most are bell-shaped, 4-17 frames, with crisp art plus speed lines rather than blur in c2 (3:48.2). Some are front-loaded ease-outs: the whip at 5:45 moves about 1,000 px in one 3-frame step, then 197, 59 and 13 px, with blur only during the move.
- **Shake:** A·e^(−t/0.08) for about 12 frames.
- **Cut on the impact frame** (7:11.65, 7:13.9, 7:27.3).
- **Continuous zoom-out into an editor UI and back** (5:34.5-5:37.6).
- **Thought-bubble wipe** into a flashback and out again (6:30.4/6:33.0).
- **Long vertical travel** past world-space props, with parallax (6:37.3-6:38.8).
- **Colour isolation on a memory cue:** everything but the hero desaturates to about 10% over 12 frames on "Then you remember..." (6:29-6:30.4), just before the thought-bubble wipe.
- **Grabbed objects have weight:** the dragged school follows the cursor on a spring, tilts up to about 10° with velocity, leaves a 3-copy ghost trail and drops with a squash, debris and a THUD (5:23.1-5:25.4).

### 1.9 Captions

- **Layout.** 1-3 words visible at a time, changing on every word. Heavy rounded sans in mixed case (Nunito Black or Montserrat ExtraBold class). White fill, dark stroke of about 0.8% of frame height, soft drop shadow, cap height 4.6-8% of the frame (most often 5.5-6.5%), centred at about 72% of frame height (86-92% when a face or a POV device is in the way).
- **Pop-in in 3 frames:** 55-60% → 105% → 100% (c1, c3). Keyword chunks in c2 use a softer 6-frame version, 85% → 115-118% → 100%, with a thin yellow ring behind.
- **Keywords in caps and colour-coded by meaning:** yellow for world and exclamations, red for danger, green for yes, success and money, pink for absurd, orange for actions and food, cyan for UI, purple for glitch.
- **Modes.** Typewriter with a block cursor for system or quoted UI text. Quotes for in-world dialogue. Screams shake ±3° every frame (1:54.6).

---

## 2. The gap: where our previous videos fall short, point by point

Sources: `engine/lib.js`, the Ep.2 timeline and QA sheets (`ep2/qa/sheets/sheet_00.jpg`, `sheet_03.jpg`) and the Ep.2 audio measurements. One honest framing first: Ep.1 and Ep.2 deliberately copied a different reference ("Nobody Gets In": slow, gritty survival horror). Part of the gap is that genre choice. The owner's verdict ("bad quality and not that engaging") still holds, and every point below is something we have to change.

1. **Gag engine and script.** Our episodes are survival procedure with information cards. Ep.2 has 21 `card` shots: fact cards on beige paper ("50 DECIBELS", "3 SECONDS = 1 KM", a backpack list), maps (`map2` ×6) and building windows (`mallwin`). That means information every 10-20 s, where the reference has a gag every 4 s. There is no rule system that every viewer already knows, no planted callbacks paid off in a climax, no in-world CTA and no loop ending.
2. **Pacing.** 163 shots in 922 s is 10.6 cuts per minute against 25.6. The median shot is 5.1 s against 1.8 s. 59 shots run over 6 s and 17 over 10 s (longest 15.8 s), several of them near-static plates (mall windows, storm clouds, maps). The runtime is 15:22, almost twice the reference.
3. **Characters and acting.**
   - `hero()` is a circle head on stick limbs: single ink `line`/`bent` strokes, hands as small circles.
   - `face()` takes **one expression string out of 7** (neutral, smile, scared, surprised, worried, determined, whisper). Eyes are two ink ellipses, the mouth is one stroke, brows exist only for worried, scared and determined, and the sweat drop only for scared.
   - There are no star, ring, half-lid or closed-arc eyes, no visemes, no add-ons and no listener reactions.
   - In the sheets the hero mostly stands front-on with a neutral or slight-worry face (sheet_03 shots 48 and 56).
   - Poses blend smoothly but softly (`poseOf` lerp), where the reference snaps pose-to-pose with overshoot.
4. **Hook.** Ep.2 opens on dark, desaturated POV aisle shots with a single-word caption and "[aisle twelve]" text (sheet_00). There is no restated title question, no stakes or deadline by 10 s, no three voices by 15 s and no flash-forward or rewind. The title card arrives at 0:50.
5. **Sound.**
   - LRA is 11 LU against 3. There are 24 silences of 0.4 s or more at -40 dB against 1.
   - All voices were Supertonic presets (narrator plus Dale, Nora and the hero: 32 character lines in 15:22, one every ~29 s against ~6 s). The owner had already rejected Supertonic once.
   - The SFX were synthesized and sparse: 62 timeline cues in 15:22, about 4 per minute against ~40. Music was fluidsynth cues: 36 cue starts (~2.3 per minute against ~10 texture changes) and 15 slow fade-outs (0.15-1.0 s) into silence, never a hard drop with a slam-back on the downbeat.
   - The Vox session lesson applies directly: a score and effects that are only synthesized sound thin.
6. **Visual finish.** `defs()`/`finish()` apply `wobble`/`wobbleSoft` feTurbulence displacement to every character and to the HUD, `grain` at 0.10, `blotch` at 0.07 and a 0.85 vignette. One near-black `INK` #1E1A1A outlines everything. The palette is beige and desaturated (paper #F5E6CC, wall #D4D0BC), with flat fills and no gradients. Night is a 0.62 multiply (#3A4C70), which turns most of Ep.2 murky grey-blue (sheet_03 shots 49-53 and 57-61). This is the exact opposite of every measured trait in 1.6.
7. **UI and motion graphics.** Our HUD is a static, wobbly price tag with a DAY/NOISE meter, plus fact cards. Nothing proves a joke, there are no toasts, typewriter text, counters or stickers, and our sound captions are plain bracket text ("[silence]").
8. **Camera.** Most shots are static plates with a gentle drift. There is no world-group camera with punch-ins, whips, snap zooms, shake, speed lines or zoom-throughs. Bake headroom is only 1.25x, so zooms over 1.25x would soften baked layers.
9. **Captions.** We use Bangers, ALL CAPS, one word, 92 px at y=870 (80.6% of frame height), white or orange with a skew for dialogue. There are no colour-coded keywords, no 1-3-word phrasing, no pop, no typewriter mode and no shake. The look is horror-comic, not the bright rounded sans of the reference.

---

## 3. Engine upgrade plan ("engine v3")

### 3.0 Platform decision: stay on SVG/JS + Playwright

- **Why stay.** The reference is a flat vector look built from gradients, gloss strips, clip-paths, blend modes and blurs. SVG does all of that natively, can be inspected frame by frame in Chromium, and our timeline, baker, renderer, caption and ASR tooling already exists.
- **Alternative considered: skia-python, as in the Vox v2 rebuild.** That pipeline rendered at about 0.42 s per frame per worker (≈7 fps on 3 workers). Our Ep.2 render averaged 5.7 fps on 4 workers at 1440p60 (2.4 fps in its heaviest chunk), so skia is only about 1.2x faster on average. It also lives in another session's container (only the code is on branch `claude/vox-test-video-recreation-oh0z7p`), and porting our characters, sets and timeline would burn days of agent usage. Rendering costs no usage, so a slower renderer is the cheaper trade.
- **Speed instead comes from:** dropping the per-frame feTurbulence wobble on characters and HUD (grain and vignette were already baked), baking static sets and glows, and adding sub-frame motion blur only where needed.
- **Re-open the skia question** only if the 20-frame benchmark at the end of Phase 2 comes in under 1.5 fps at 1440p.

### 3.1 Art style spec

**Global**
- Delete `wobble`, `wobbleSoft`, `grain` and `blotch` from this show. Vignette only on night POV, sky-only and flashback shots (radial, edges 25-35% darker).
- No pure black outlines anywhere. Near-black #1A1215 is reserved for pupils, eye rings and brows.
- **Gradient banding is now our problem.** The old grain hid banding; clean full-screen sky gradients will band in 8-bit 4:2:0 H.264 and again after YouTube's re-encode. Render frames as JPEG at quality 98+ (PNG for the hook proof), encode the master and the upload file in 10-bit (HEVC Main10 for the ≤400 MB upload, near-lossless 10-bit for the master), and if a sky still bands, add an ordered dither of ±0.5 code value inside the gradient only (the reference's flat sky has a standard deviation under 1, so this stays invisible). QA checks the sky in 5 frames per act at 400% zoom.
- **Contact shadows:** a soft ellipse under every foot and under lifted objects (radial gradient, multiply, 20-30% opacity, shrinking and lightening with height). No cast shadows.

**Colour math** (new `engine/style.js`, all in OKLCH)
- `grad(fill, dir)`: linearGradient, top (or top-left) L +0.05, bottom (or bottom-right) L -0.07 (≈10-15% luminance spread). Vertical for skies and props, diagonal top-left → bottom-right for character blocks. Faces use a radial version: centre L +0.03, rim L -0.05, chin 12-15% darker than the forehead, lit left side lighter (c4: #f1e4da left vs #dbc7bc right).
- `cube(fill)`: top face L +0.12, front face as `grad`, side face L -0.18 (cubes, signs, rocks, crates).
- `stroke(fill)`: L = 0.28-0.32, chroma ×0.9, hue rotated 10-15° toward purple. Examples: red #FB6F4B → maroon #5D2011; blue shirt → #254268; hair → #491F05.
- `gloss(part)`: a rounded white strip at 30-45% opacity, inset 8-12% from the top or left edge and 10-18% of the part's width, plus a thin rim highlight on limbs.
- `atmos(fill, depth)`: mix 25-40% toward the sky colour and reduce chroma by 30% for back layers.

**Outline weights** (world-space, scaling with the camera, never `non-scaling-stroke`; values at a 1080 design space, ×1.33 at 1440p)
- Hero and cast: 2.0-2.9% of head height (≈8-10 px for a 400 px close-up head, ≈4-5 px in medium shots).
- Eye rings: 2x the body stroke.
- Props: 0.6x the character stroke. Mid buildings: 0.4x. Far skyline and clouds: no stroke, shade face only.
- Round joins and caps, uniform width.

**Show palette** (dinosaur park; one dominant hue family per scene)

| Token | Value |
|---|---|
| sky_day | #1F81FB → #3498FA → #80C6FB |
| sky_dusk | #FF9A5A → #FF6F91 → #6A5ACD |
| sky_outage | #0E1A3A → #23345E, with emergency-red pools #FF2E3B |
| sky_volcano (Day 7) | #55070C → #850E12 → #AB1617, far layers mauve #BF5A78 |
| jungle | grass #4BC240 / #59C84D, fern #2E9E52, leaf highlight #8BE07A |
| park neon | sign pink #FF4FB0, teal #18D3C5, gold #FFD43B |
| path | #E9D7A8, with a footprint motif at +6% L |
| hero | shirt #FF7A3D → #E4572A, logo white dino footprint, signature **orange headphones** kept from our channel's hero |
| Mom | #9B6CF0 |
| Dad | #4A90E2 |
| Kid skin (cool cream, as in the reference) | #F4E7DB → #D5C5C0 |
| dinos | Rex #6FBF4A with belly #FFE38A; raptors #F09A3E with stripes #B5562A; Brachio #4FB7C9; baby Trike "Biscuit" #F28FD0 with frill #FFD1EC |
| UI panels | #1D2436 at 92%, border #2E3A55, primary green #21C258, alert red #FF3B3B |

**Light and glow**
- Light is motivated: sun halo (radial, 2.2x the sun, screen blend at 0.6), countdown-ring outer glow (blur 8-10), device under-light on faces (cool white radial, screen at 0.7), moon shaft (gradient trapezoid at 0.25 → 0), neon sign bloom, emergency lights.
- Night is a multiply of #3A4C70 at about 0.6 **with** screen-blended light pools on top. Never a flat murk.

**Patterns.** Our brand motif replaces Roblox studs: a dinosaur-scale pattern (overlapping semicircles at +6% L) on ground and park surfaces, ticket perforations on UI, and three-toed footprints on paths.

**Particles** (deterministic, closed-form in t): 4-point twinkles, leaf confetti, dust puffs, rock and wood debris, embers (Day 7), tokens (Day 4) and hearts.

### 3.2 Character system

**Construction** (new `engine/rig.js`; our own toy design, not Roblox)
- About 3.1 heads tall (the reference measures 2.7-3.3), head ≈ torso width, so faces read in wides.
- Head: a rounded square with rx 22-26% (softer than the reference's measured 12-18%), a radial face gradient, and a rigid hair helmet with 2-3 wavy highlight strands.
- Torso: a rounded trapezoid with a logo and a sheen strip.
- Arms: capsules pivoting at the shoulder. The **hero, Mom and Dad get an optional elbow** (2 segments) for points, facepalms and hand-to-head; extras stay one-piece. Hands are mitten blobs.
- Legs: 2 capsules plus a shoe cap, pivoting at the hip.
- Back view for every cast member, needed for over-the-shoulder and Dad-from-behind shots.
- Data API: `toon(id, {x, y, s, facing, back, pose:{armL, armR, foreL, foreR, legL, legR, head, lean, bob}, face:{...}, add:{sweat, tears, blush, q, zzz, stars, bump}, badge})`.

**Dinosaur rigs** (4)
- **Rex:** head with a hinged jaw, eyes and brows; tiny arms; 2-part legs; a tail chain of 4 segments with follow-through.
- **Raptor:** jaw, head-bob, a tail of 3 segments, a crouch pose.
- **Brachio:** a neck chain of 5 segments with spring lag, and a slow-blink face.
- **Baby Trike "Biscuit":** a tail wag, a frill bounce, a tongue.
- All dinosaurs use the same eye, brow and mouth kit (scaled), so they act like the humans.

**Face kit** (new `engine/face.js`; any eyes × brows × mouth, plus add-ons)
- Eyes: ring with a dot pupil (dart ±3 px), black bean with catchlight, half-lid with pupils low, closed ^^ with blush, star, token (Day 4), tiny pinpoint (shock), teary, squint, wink, spiral (dizzy), glowing red (the bully or raptor).
- Brows: worry, angry, flat, raised, asymmetric (skeptic).
- Expression mouths: D-open with teeth band #FFFFFF, interior #551124 and tongue #FD6C89; grin; small o; scream O up to 45% of head height; wavy panic; flat deadpan; smirk; gritted grid; yawn; tongue-out; laugh.
- Visemes: closed, small, mid/E (teeth), wide A (tongue), O.
- Add-ons: sweat drop (0 → 1.2 → 1.0 over 6 frames, then slides 20 px and grows ×1.4), tear streams, ? and ??, Z's, hearts, dizzy stars, bump with orbiting stars, tremor arcs, blush.

**Animation rules**
- **Lip-sync:** visemes from the voice WAV (RMS at 60 fps plus spectral centroid: below -40 dBFS closed; -40 to -28 small; louder with centroid over 1.8 kHz wide/E; louder and lower A/O), restricted to ASR word windows. Hold each shape 3-8 frames. Between words, fall back to the beat's expression mouth. Every on-screen speaker lip-syncs, and so does the hero during "you" narration over his close-up.
- **Expression track:** keyframes on ASR word times, an instant swap, a minimum hold of 6 frames except for a 2-frame "take" face between two holds (as at 1:51.13), and a 2-frame head squash (scaleY 0.95) on big swaps. **Lurch:** on a shouted word the whole character scales about +25% toward the lens in 2 frames and settles over 8.
- **Eye darts and blinks:** a saccade every 0.3-0.8 s (2-frame move) when nervous. A blink every 2-4 s (3 frames: half, closed, half), never during a deadpan stare.
- **Pose-to-pose:** per-joint tracks with easeOutBack (s ≈ 1.7) over 4-8 frames, then hold with a ≤2° drift.
- **Idle layer, always on:** breathing scaleY 1 ± 0.01 at 0.4-0.6 Hz; head bob ±1.5 px; arm sway ±2-3°; phase offsets per character so no two move in sync. The nervous flag adds 1-3 px per-frame jitter; panic adds 4-8 px.
- **Squash and stretch:** parts stay rigid, as in the reference, which gets all its elasticity from pose snaps and position springs (Dad's BONK: the body drops 20 px and settles in 7 frames). Our addition, to be judged on the hook proof: the whole-body group squashes up to 10% on anticipation and landing (a 7-frame damped spring), and stretches up to 8% on launches only.
- **Overlap and follow-through:** damped springs (k ≈ 120, ζ ≈ 0.35) on hats and Mom's plush pile, dinosaur tails and necks, badges, lanyards and wristbands (the reference sways hats and stacks but keeps hair rigid; ponytail springs are our addition). Arms lag the torso by 2 frames on big moves.

### 3.3 Camera system (new `engine/cam.js`)

- **Structure:** a world group `<g id=world transform="translate scale rotate">`. HUD, captions, stickers and flash frames live in screen space above it.
- **Shot keys:** `cam:[{t, x, y, z, r, ease}]`.

| Move | Spec |
|---|---|
| Default push | z 1.00 → 1.03-1.08 per shot, easeInOutSine, plus 20-60 px drift. Long UI or POV takes push up to +30% over 6 s |
| Punch-in on a stressed word | z ×1.06-1.3 in 1-4 frames (easeOutBack or expo), settling about 3% over 0.25 s, with radial speed lines (24 tapered wedges at 0.8 → 0 over 0.3 s) |
| Snap zoom as a cut substitute | z ×1.6-3.8 in or out over 15-28 frames: animate log(z) with easeInOutSine, or an expo ease-out z0·(z1/z0)^(1−2^(−10u)) for punch-ins; ghost copies above 25 px/frame; a whoosh ending on the last frame |
| Snap-zoom shock | start the shot at 1.18 on the face and ease out to 1.0 in 0.3 s (easeOutExpo), with a starburst behind the head |
| Snap reveal | z 1 → 0.5-0.7 in 15-22 frames, easeOutQuart |
| Whip pan or tilt | 4-15 frames, easeInOutCubic (bell-shaped velocity), or a front-loaded easeOutQuart (about 1,000 px in the first 3 frames, then 197, 59, 13); white speed streaks in the move direction; directional blur from 3-6 ghost copies at opacity 1/N (cheap, in-page), or 6 sub-frames averaged (6x the render cost on those frames); a whoosh peaking on the cut |
| Shake | offset A·e^(−t/0.08)·noise(60t), A = 20-30 px at 1080, 6-12 frames |
| Parallax | layer factors: far 0.3, mid 0.7, cast 1.0, foreground 1.3 |
| Rack focus / DOF | in close-ups the background group gets feGaussianBlur 3-5 px (baked per shot); a rack is 0 → 4 px over 10 frames, darken background 5% |
| Follow crane | camera y follows the character through a critically damped spring (ω ≈ 12) |
| Zoom-through | a nested `<svg>` viewport (UI card or map → scene) animated from viewport space to screen space over 15-51 frames |
| Device realism (the owner's "camera must behave like the real thing") | POV hands float ±4 px; screens get glare and a finger occlusion; in-world cameras (photo booth, park CCTV during the Day 5 outage) get lens distortion, rolling exposure and timecode, applied to the composited layers as in the Vox v2 doorbell lesson |

- **Baking:** today's bake headroom is 1.25x (`over` in `render_anim.js`), but the reference zooms up to 3.8x (4x on the editor zoom-out). Bake per zoom band instead of one layer per shot: each framing a camera key rests on gets its own bitmap of only the region visible at that zoom (at most 2x the frame per side, so never near the 8,192 px cap), and the fast in-between frames use the nearer band under the ghost-copy blur. Only static layers are baked; characters and FX stay live vector. The Vox render crashed on a push-in that asked for a 49,000 px canvas, so clamp and log every bake request.

### 3.4 Motion-graphics kit (new `engine/ui.js` and `engine/fx.js`)

Every component takes `(t0, ...)`, is a pure function of time and **emits its SFX cue** (3.10).

| Component | Spec (from measured reference behaviour) |
|---|---|
| ticketTear(day) | Our version of the calendar montage. Tickets fly up from y+500 with vertical streaks, tilt -5° → +2°; each tear lifts −650 px and rotates 8° over 9 frames, 0.3 s apart; DAY 7 gets a starburst and a sub boom |
| dayTitle(n) | Chunky yellow #FFD43B lettering with a 6 px dark stroke. Letters 3 frames apart with smear trails; the number slams 2.5 → 1.0 in 3 frames; a ring burst and an underline swoosh (stroke-dashoffset over 8 frames); a riser ending on the slam |
| ruleCard(n, text) | A 3D cube icon (rule colour) at scale 0.4 → 1.08 with rotation −25° → −10° over 2 frames; a navy pill wipes in over 4 frames; a white ring r 40 → 110; typing at 30 chars per second; a thunk plus ticks |
| toast(icon, title, sub) | #1D2436 panel, radius 12-14, easeOutBack slide over 5-12 frames, held 2-3 s; stackable (y −48 per item, one every 0.12 s for spam gags) |
| banner(text, hazard) | Red alert bar with hazard-stripe caps and a pulse |
| countdownRing(n) | 60 tick dashes, a progress arc, gradient numerals #FF7A4A → #E0201C, a blurred outer glow. Entry: sparkle, then clock-wipe, then burst (0.5 s). Becomes a corner HUD that ticks every ~1.5 s with a beep |
| timerPill / counter | Rolling numbers with easeInOutCubic and jitter; the tick-SFX rate follows the derivative |
| chatBubble / paBubble | Typewriter at 18-30 chars per second with a block cursor in the keyword colour; a "lag" variant reveals irregular 2-4 character chunks every 0.15-0.4 s with a loader dot; the bubble is a physical object that can be bonked |
| waitBoard(min) | Split-flap digits (ours; the park's version of the ping meter) |
| mapPin / selectBox / bboxCascade | Selection and pin overlays drawn on via stroke-dashoffset in 6 frames, labels popping 40-150 ms apart (used for the Day 6 "the world is a park map" reveal) |
| wristband / scanner | Beep plus green or red flash |
| priceTag(n) | "One token more than you have": the price ticks up by 1 as the wallet opens. Scale-pop and coin spin (scaleX = \|cos θ\|, half-turns at 0.13 s, decelerating) |
| sticker(word) | Onomatopoeia: chunky italic (Luckiest Guy, else Bangers, which we have), gradient #FFE44D → #FF8A1F, inner stroke #7A1414, white outer stroke, rotated −8° to −12°; 0 → 1.25 → 1.0 over 5 frames, ±3° wobble at 6 Hz, fade at 0.6-1.0 s; always with a spark star at the contact point |
| impact(x, y, size) | 10-14-point starburst with a white core and red rim; radial wedges; shock ring 0 → 2·size over 12 frames; sparkles; debris under gravity (2,500 px/s²); shake. Repeated hits scale 1x, 1.5x, 2.5x, and the third gets a 1-2-frame solid flash frame (#F0386B, as on the triple YES at 7:28.8) |
| spotlightDim | World saturation 0.35 plus a multiply #3A3F4A at 0.45 over 0.15 s, with the UI element at full colour above it |
| speedLines | Radial or directional tapered polygons, 20-60 of them, opacity tied to camera velocity |
| puff (POOF/FLOOF) | 6-9 circles cover the object in 5 frames, the asset swaps on frame 3, the puff drifts and fades over 12 frames |
| ctaSubscribe / ctaComment | In-world finger press, button flip, confetti; a comment panel with a 1,204 → 9,805 count-up and rows sliding in every 0.6 s |
| waypoint(label, dist) | Edge-pinned pill at the off-screen goal's projected x, gold 2 px stroke, arrow icon, live distance that drops as the hero climbs ("GIFT SHOP EXIT 2,000 ft") |
| timerPill / dialPop | Corner timer that turns red at 0:10 and can freeze; the world-space dial pops only on key numbers, with a red vignette flash (0 → 0.5 → 0 over 12 frames) |
| godRays(x, y) | 20 alternating wedges (yellow at 70%, white at 50%) from the chest, rotating 20°/s, opacity 0.6 ± 0.15, screen blend, radial fade; for triumphant beats |
| drag(obj) | The object follows the hand on a critically damped spring (k 180), tilt = clamp(−0.04·vx, ±12°), a 3-copy ghost trail and a lift shadow; the drop squashes 0.9 → 1.03 → 1 with debris and a THUD |
| lag(actor) | Time remap tLag = t − (t mod hold), holds of 3-8 frames then catch-up jumps, on selected actors only; RGB ghost copies at ±6-14 px for 2-6 frames; the music bus gates for 80-150 ms on the same frames (Day 5 outage) |

### 3.5 Transitions (in order of use)

1. Hard cut (default, about 70% of edits). The picture leads the sentence by 0.1-0.5 s.
2. Cut on impact: the next shot starts on the contact frame, with the impact kit on frame 0.
3. Whip pan or tilt (about 6 per minute).
4. Snap zoom in or out as a cut substitute.
5. Zoom-through UI (the park map brochure into the city; a ticket into the world).
6. Flash frame: 4-6 frames solid or screen-blend on act changes (#D10C25 solid at 6:11.8, a pink-red overlay at 5:52.8); 1-2 frames of #F0386B on the biggest hit of a triple.
7. VHS pause and rewind for the flashback (re-render earlier shots backwards at 8-15x, 2-3 frames each, chroma ±4 px, tracking bands, OSD).
8. Thought-bubble wipe in and out of a memory (clipPath scaled ×12 over 4-5 frames; lavender grade).
9. Transformation sweep: a glowing wavy front converts the real style into the park style, with spawning leaf and vine particles.
10. Tile dissolve from a tap point: cells appear in distance order and fill the screen in 11 frames.
11. Grade wipe: a skyline-shaped clipPath brings in the red volcano sky.
12. Puff cover, used for swaps.
13. Glitch cut (2-frame RGB bands, then a pose snap), for the Day 5 outage.
14. Colour isolation: the world desaturates to about 10% over 12 frames while the hero stays in full colour, on a "you remember" beat, then the thought-bubble wipe.

### 3.6 Caption style (new `engine/caption2.js`)

- **Font:** Nunito Black (OFL; download it into `assets/fonts`). Fallback Rubik 800, which we already have. Lilita One (we have it) for titles; Bangers only for stickers.
- **Size and position:** mixed case, cap height 6% of H (≈86 px at 1440p), white fill, paint-order stroke #180C18 at 0.8% of H, drop shadow (dy 4, blur 3, 50%). Centred at y = 0.72 H, moving to 0.86 H when a face box overlaps and to 0.92 H in POV device shots.
- **Chunking:** 1-3 words per chunk from TTS or ASR word timings; break at punctuation and before keywords; show each chunk 2-4 frames before its word starts.
- **Pop:** 0.6 → 1.05 → 1.0 over 3 frames. Keyword chunks also get a thin yellow ring (r 40 → 160, 0.25 s).
- **Keyword colours:**

| Colour | Hex | Used for |
|---|---|---|
| yellow | #FAD309 | park and world nouns, exclamations |
| red | #FF4A3D | danger and closing |
| green | #45E05A | accept, success, tokens |
| pink | #F05BB5 | absurd and soft words (plush, souvenir) |
| orange | #FF9A1F | actions and food |
| cyan | #33C8F5 | UI and system words |
| purple | #A96BFF | glitch and outage |

- **Modes:** typewriter with a block cursor for the announcer, system voice and quoted UI text; quotes for in-world dialogue; scream mode with rotation 3·sin(97t) plus 4 px noise.

### 3.7 Shot grammar: 16 reusable templates

Each template is a function in `ep/templates.js` that takes the set, cast, line IDs and gag props and returns a shot with camera keys and SFX cues already attached. All of them inherit the idle layer, the default push, captions and the cue emitter.

| # | Template | Duration | Camera | Content and rules | Reference |
|---|---|---|---|---|---|
| T1 | EST-WIDE | 1.5-3 s | push 3-6% plus drift | Set with ambient life (walkers, birds, dinos, cars, steam); the premise line | 5:15 DAY 6 wide |
| T2 | REACT-CU | 0.4-1.2 s | locked or micro push | One expression swap on the stressed word; the punchline button | 2:37.2 "Uh...", 2:41.7 deadpan |
| T3 | SHOCK-PUNCH | 0.6-1.5 s | snap 1.18 → 1.0, shake | Starburst behind the head, speed lines, face swap, sting | 0:40.83, 3:38.05 |
| T4 | DEADPAN-HOLD | 0.8-2 s | slow push to 1.15-1.28 | Flat face, blinks only, music drop | 1:15.4, 2:54.2 |
| T5 | POV-DEVICE | 2-6 s | push +15-30% | Hands, screen or ticket UI, typewriter, button pops, tap ripple | 0:22.75-0:28.9 |
| T6 | UI-PROOF | 1.5-3 s | slight push | Spotlight dim, HUD or toast proves the gag, sparkle on the payoff word | 0:54.9-0:57.4 |
| T7 | INSERT | 0.4-1.3 s | push 5-6% | Prop extreme close-up (clock, wallet, sign) with glow or pulse | 0:20.5, 3:36 pump LCD |
| T8 | ACTION-FOLLOW | 2-4.5 s | zoom-out then spring follow | Parabolic jump or chase, a rotation, landing FX, sticker | 0:58-1:02, 6:55.9 |
| T9 | WHIP-REVEAL | 0.3 s whip plus a hold | whip tilt or pan | Lands on the reveal (giant hand, sky, threat) | 5:18.3 cursor |
| T10 | SNAP-OUT-SCALE | 1-3 s | z → 0.5-0.7 in 0.25-0.4 s | The scale gag (tower, 1,000 copies, a park the size of the world) | 1:46.1, 4:10.7 |
| T11 | DIALOG-SR | 0.4-3 s per side | locked, inserts 0.4-0.65 s | Shot/reverse with lip-sync, bubbles and identical-loop gags | 2:34-2:42 teacher |
| T12 | CROWD-PANIC | 0.7-2 s | micro drift or a fast push | Phase-offset flails, chat or PA bubbles stacking, banner | 0:10.45, 6:26.7 |
| T13 | CHAPTER-CARD | 1.2-2 s | push +9-30% | dayTitle slam over a wide, a cue change, whoosh plus low hit | 0:36.85, 1:34.6 |
| T14 | TIMELAPSE | 1.5-2.5 s | static | Action quantised to 12 fps, HUD clock at 60 fps, grade drift, sped-up music | 5:07.5 |
| T15 | CONCEPT-CARD | 1-2 s | rise plus slow push | Sunburst or skewed triptych panels, coin or token spin | 3:20.3-3:23.4 |
| T16 | OTS-THREAT, then REVERSE | 1.2 s plus 1.2 s | slow pull, then reverse | Backs of heads toward the threat, then frontal panic with the threat as a HUD | 6:14.9-6:17.4 |

Two special set-pieces are built once: **FLASHBACK** (VHS rewind or thought bubble) and **TRANSFORM** (sweep from room to house to street to planet).

### 3.8 Render budget at 1440p60

- **Frame count:** 8:00 at 60 fps = 28,800 frames (the reference length would be 28,920).
- **Measured speed today:** the Ep.2 final (55,318 frames at 1440p60, 4 Chromium workers, `tools/render_ep.py`) took 2.7 h: 5.7 fps on average, 2.4 fps in the heaviest 3,000-frame chunk and up to 9.5 fps in the lightest (logs: `scratchpad/ep2/render/render_*.log`). That already includes the per-frame wobble filters; grain and vignette were baked.
- **Expected speed for v3:**
  - Faster: no feTurbulence wobble on characters and HUD.
  - Slower: more live characters and props per frame, gradients (cheap), live glows and blurs (Chromium rasterises feGaussianBlur on the CPU; bake static ones), per-zoom-band bakes, background DOF (bake per shot), and 6-sub-frame motion blur if used (6x the cost on about 3-5% of frames, +15-30% overall; in-page ghost copies cost far less).
  - **Estimate: 2.5-5 fps; plan on 2.5. Benchmark 20 representative frames (a crowd wide, a close-up with DOF, a whip, a particle-heavy impact, a UI-dense POV) at the end of Phase 2.**

| Pass | Frames | Speed | Machine time |
|---|---|---|---|
| Hook proof, 60 s at 1440p60 | 3,600 | 2.5-5 fps | 12-24 min |
| Animatic or preview of the full video at 720p30 | 14,400 | 8-12 fps | 20-30 min each, ×2-3 passes |
| Final at 1440p60 | 28,800 | 2.5-5 fps | **1.6-3.2 h** |
| Re-render of fixed shots (~25%) | ~7,200 | same | 0.4-0.8 h |
| **Total** | | | **≈4-6 machine-hours**, which cost no usage |

- **Disk is the real blocker. Only about 860 MB is free (98% full).**
  - The chunked renderer already exists. `tools/render_ep.py` renders 3,000-frame chunks through `render_anim.js`, encodes each to an H.264 segment while the next chunk renders, deletes the JPEGs and resumes from finished segments. Reuse it rather than rebuild it; switch its encode to 10-bit and a lower crf for this show (3.1).
  - Ep.2 frames averaged 307 KB (JPEG q95), so one chunk is about 0.9 GB (more at q98) and the renderer holds up to two at once. Peak need: about 2-2.5 GB of frames, 1.5-3 GB of segments, plus 1-2 GB of Epidemic downloads (with stems) and voice files.
  - Even the 60-s hook proof (3,600 frames ≈ 1.1 GB) does not fit today. **Free at least 6 GB in P1, before the Epidemic ingest and any 1440p render.** Delivered old work in the scratchpad: `shorts` 3.0 GB, `final` 2.6 GB, `ep2` 1.9 GB, `ep1` 1.7 GB, `stems` 1.7 GB (keep `models`, 2.1 GB: it holds the ASR and TTS models). **Ask the owner before deleting any of it.**

### 3.9 Pipeline and code modules

- `engine/style.js` (palette, OKLCH helpers, gradient and gloss cache, `atmos`)
- `engine/rig.js` (toon and dinosaur rigs, pose tracks, idle, springs)
- `engine/face.js` (kit, visemes, blink and saccade)
- `engine/cam.js` (camera keys, shake, whip, parallax, DOF)
- `engine/fx.js` (impact, particles, puff, flash, glitch, transformation)
- `engine/ui.js` (the kit in 3.4)
- `engine/caption2.js`
- `engine/cues.js`: every FX, UI, caption-keyword, cut and whip call registers `{t, cue, gain, pan, layer}` in `cues.json`
- `ep/templates.js` (the T1-T16 functions)
- `episodes/ep3/{script.tsv, shots.js, timeline.json, voice.json, cues.json}`
- `tools/render_anim.js` changes: per-zoom-band baking with clamped bake sizes, and optional sub-frame blur for flagged ranges. Segment encoding and resume already exist in `tools/render_ep.py`; extend the existing `tools/motion_qa.py` (animation-pop detector) with the still-frame scan.
- `tools/qa_metrics.py`: cut rate, setup rate, shot lengths, still frames and longest still run (from frame diffs, on the same threshold as section 0), caption lead, SFX per minute, cut-to-SFX share, music presence, drops per minute, LUFS, LRA, voice minus bed. It reuses `study/audio/scripts/*`, copied into the project in P1 (`tools/refmetrics/`), and compares against the table in section 0.
- `tools/originality.py`: 4-word n-gram overlap of the script, captions and on-screen text against `study/audio/transcript.txt`, plus a banned-word scan ("Jurassic", "Indominus", "Roblox", "Robux", "noob", "oof"). Runs on every script version.

### 3.10 QA gates (run on the hook proof, the animatic and the final)

1. Every row of the section 0 table passes.
2. Frame-diff scan: no unflagged static run over 16 frames.
3. Every visible sticker or UI pop has a cue within ±1 frame.
4. Every on-screen speaker has visemes, and lip-sync correlation with the voice is at least 0.6 (the Vox v2 bar was 0.71).
5. Every caption chunk appears 2-4 frames before its word.
6. A critic pass on 6 clips covering picture, acting, sound and comedy, with a numeric before/after from the fixer and a verifier go/no-go.
7. `motion_qa.py` flags no unexplained animation pop (a frame-to-frame jump far above its shot's own motion) in any segment, as was run on every Ep.2 segment.
8. No visible banding on the sky gradients in the encoded upload file (3.1).
9. `originality.py` passes: no shared 4-word run with the reference outside the title formula, no banned word, and no restaged film shot from the list in 6.1.

---

## 4. Sound plan

### 4.1 Voices (following the voice lab's recommendation)

**Cast**

| Role | Voice and delivery | Approx. lines |
|---|---|---|
| N (narrator) | Second person; two registers, HYPE (180-330 Hz feel) and DEADPAN (100-140 Hz) | about 150 |
| KID (hero) | A real child voice, about 300-330 Hz | about 30 |
| MOM | Bright, sing-song | about 12 |
| DAD | Deadpan, flipping to falsetto panic | about 12 |
| PARK ANNOUNCER (SYS) | Flat, then our band-pass 300-3,400 Hz chain with most energy at 1-3 kHz, a two-tone PA chime before each line, light bitcrush | about 16 |
| T-REX TEACHER and the ANIMATRONIC SHOW voice (NPC) | The show voice is one take reused identically each time the show restarts | |
| CROWD and raptors | Short walla | |

Dinosaur vocals are SFX (layered roars), not TTS.

**Who records what**
- **Final voices:** the owner, in Fish Audio (the tool they already used successfully) or ElevenLabs. Narrator and characters must come from the same tool, with emotion tags on every character line.
- **Voice rights:** generate on a plan whose terms allow commercial use on a monetised channel. Pick only the tool's own official voices or voices the owner designed; Fish's public library also holds user-uploaded clones of real people and cartoon characters, and none of those may be used. DAD can be the narrator's voice played deadpan and falsetto, as in the reference (same performer by embedding).
- **Scratch track, starting now:** Kokoro (N am_michael, KID af_jessica raised 3 semitones, MAN am_onyx, WOMAN af_heart), best of 3 takes checked by ASR, using the same `<id>_<role>.wav` names. The animation is timed to line IDs and word times, so the owner's files drop in and the timeline re-flows.
- **Local fallback:** Kokoro for announcer and system lines (they are processed anyway) and Piper libritts_r (904 speakers, CC BY 4.0) for crowd filler.
- **Prosody QA:** tag every line HYPE or DEADPAN. Reject a hype take whose within-line pitch standard deviation (pYIN) is under 2 semitones; the reference narrator averages 2.9, a flat read about 1.5.

### 4.2 Music: Epidemic Sound as the backbone, edited to picture

- **Why:** the Vox lesson is that a fully synthesized score was heard as missing and thin.
- **Licence timing:** the owner mentioned a one-month Epidemic subscription during the Vox session (around Oct 30). Epidemic clears content published while the subscription is active, on channels connected to the account. So the video must be **published** before that month ends (or the plan renewed), and the channel it goes on, including a fresh channel (7.10), must be connected first. Check the plan's channel limit before recommending a new channel.
- **Owner downloads 6-8 tracks**, with stems where Epidemic offers them (melody, bass, drums, instruments), so we can drop and re-enter layers:
  1. Bouncy comedy, pizzicato or marimba with a sliding bass, 118-126 BPM, major key (Days 1-2). **Two variants.**
  2. Quirky "march" or "rules" cue, 110-120 BPM (Day 2 rules, Day 3 school).
  3. Night lullaby or music box (the cold-open flashback, the Day 5 start).
  4. Suspense pulse or drone, low centroid (the Day 5 outage and the Day 6 reveal).
  5. Epic or hybrid-orchestral chase, 132-145 BPM, minor key, ideally with an upward modulation (Day 7).
  6. Happy resolution in a major key with a brass hit (restoration and ending).
  7. Optional: a glitchy or electronic twist sting (the loop ending).
- **Synthesized or processed by us:** tape-stop (resample the last 0.6-0.8 s with a falling rate), rewind (reversed audio plus a stutter gate), outage "power-down" pitch drops, the stutter-gated music bus on glitch beats, risers and booms, the brass TA-DA (fluidsynth GM 62 as a fallback), and mickey-mousing plucks on stair or step gags.
- **Edit rules** (in an `ep_music.py` cue sheet generated from the timeline):
  - Music present at least 95% of the time; a texture change every 5-6 s; a new cue on every DAY card.
  - 2-3 drops per minute on punchlines (0.3-2 s, 20-30 ms fade-out), then a re-entry on the next downbeat with a hit.
  - The bed rises about +4 dB from Day 1 to Day 7, and +10 dB for the climax run.
  - Key plan: major for fun, minor for threat, upward modulation in stages for the climax, the relative major on "Thank you for visiting".

### 4.3 SFX: Epidemic for organic and cartoon, synthesis for UI

**Epidemic shopping list for the owner** (put it in at most 3 zips, because chat allows 5 attachments per message)
- **Cartoon:** boings (5+), slide-whistle up and down, spring wobble, bonk, clonk, pop, cork, kazoo or sad trombone, cartoon run.
- **Impacts and transitions:** whooshes (8+, short and long), risers (3), booms and sub drops (4), braam (1), glass and wood crash.
- **Dinosaurs:** roars large and small, raptor chirps and screeches, a snort, heavy footsteps and stomps (with ground rumble), wing flaps, a tail swish.
- **Park:** PA chime two-tone, crowd walla calm and panic, turnstile clack, wristband scanner beep, cash register, camera shutter or flash, ride safety bar, electric fence buzz and zap, jungle ambience, birds, gate creak.
- **Domestic:** fridge open and close, cereal pour, kitchen ambience, door, footsteps on stairs, splash.
- **Alarms:** a siren, a two-tone alert.

**Synthesized** (`sfx.py`, unlimited variants, exactly timed): UI blips, ticks, keyclicks and typing; notification pings and bloops; sparkle ladders; coin and token chimes; counter ticks; error buzzer; glitch stutters and digital chirps; the power-down sweep; heartbeat; tremor buzz.

**Rules**
- Every cut, pop, sticker, UI element, expression swap on a punchline, and every repeated action (each jump, each plush) gets its own sound, placed 0-17 ms before the frame.
- SFX are not kept out of speech: about two thirds of the reference's effects sit under dialogue, ducked by the voice's sidechain rather than moved into the gaps.
- Every head bonk is followed by cartoon dizzy-bird tweets (around 5 kHz).
- A typical hit has 3 layers: transient, tonal accent, tail.
- Key SFX are mono and centred; music is wide.

### 4.4 Cue-density and mix targets

| Target | Value |
|---|---|
| SFX events per minute | 40 average; 60-75 in action; no gap over 3 s |
| Cuts with an SFX transient within ±0.1 s | at least 50% |
| Music changes per minute | about 10 texture changes and about 4-5 strong changes; a cue change on every DAY card |
| Music drops per minute | 2-3 |
| Non-narrator voice lines | every 6-8 s |
| Gaps between lines | median 0.44 s, none over 1.5 s; any gap over 1 s carries a sound gag |
| Loudness | -14 LUFS integrated; true peak ≤ -1.0 dBTP (YouTube-safe; the reference is -0.3); LRA ≤ 4 LU; short-term -16.7 to -13 LUFS everywhere |
| Balance | voice ≈14 dB over the music+SFX bus (short-term median); about 4 dB ducking under speech (attack 30 ms, release 250 ms); key SFX within about 5 dB of the voice; at most 2 silences of 0.4 s or more at -40 dB, both designed |
| Deliverables | VO, MUS and SFX stems |

---

## 5. Voices: the answer for the owner

**Can we do clean, realistic multi-voice narration ourselves?** Clean, yes. Realistic acting, no.

We tested five local engines and measured each one, since I can't listen.
- **Kokoro is the best of them.** It is very clear (speech recognition heard every word except "respawn", which a respelling fixes), sounds the cleanest on our quality score, runs 4x faster than real time and is licensed for commercial use.
- **But none of the local engines can act.** They have no emotion controls and no real child voice. Our "kid" is an adult voice raised 3 semitones. The engines that copy a voice sounded worse: flat, slurred or clipped.
- **The better open models are out of reach.** The open models that do support emotion can't be downloaded in this environment, and most aren't licensed for commercial use anyway.
- **Recommendation:** you make the final voices in Fish Audio, as you did for the police video (or ElevenLabs if you prefer). We do everything around them.

**The exact workflow**
1. **We send you a line sheet:** about 230 lines for an 8-minute video, each with an ID (S01-L002), a role, a delivery note ("excited, breathless") and the exact text, including respellings such as "re-spawn". You also get one paste-ready block per role.
2. **You pick one voice per role** in Fish (narrator, kid, mom, dad, park announcer) and save it as a preset. First send us the 4 test lines; we measure them and reply within minutes.
3. **You generate the lines** with an emotion tag at the start of each, e.g. `(excited) Wait, wait, wait...`. Do the hook first: the cold open and the start of Day 1 (about 27 lines, 15-20 min), so the 60-second proof you judge at check-in #1 already has your real voices.
   - Name each file `<ID>_<ROLE>.wav` (S01-L002_KID.wav). A retake gets `_t2`.
   - Or, if that is quicker, one file per role per scene, with about 1 s of silence between lines; we split them automatically.
   - WAV only (MP3 at 192 kbps or higher if that's all the tool offers). No music, effects or speed-up.
4. **Upload** as 2 zips (voices_N.zip and voices_chars.zip), because chat allows 5 attachments per message.
5. **We check every line automatically:** clipping, loudness, speech recognition against the script, and whether the voice stays the same across lines. You get a short retake list (for example "S01-L002 heard 'respond' for 'respawn'").
6. **We align, time, lip-sync and mix.** Captions, mouths, cuts and sound effects all lock to your words.

Expect about **60-90 minutes of your time** per 8-minute video if you use the per-scene batch files (about 30-40 generations, one per role per scene), or 2-4 hours if you export and rename one file per line. Meanwhile we animate against our Kokoro scratch voices, so nothing waits on you.

**Rights, in one line:** use a plan that allows commercial use, use only the tool's official voices or ones you designed (no clones of real people or cartoon characters from the public library), and never paste an API key into the chat.

---

## 6. Ideas: top 5, and the recommended first video

### 6.1 Top 5, ranked

1. **What If the WHOLE WORLD Became a Dinosaur Park?** (score 8.6) **RECOMMENDED.**
   - It keeps your dinosaur idea and rebuilds it on the reference's proven engine: a rule system everyone knows (theme-park rules: wristbands, wait times, height checks, "exit through the gift shop", feeding times, the PA announcer) applied to family life, day-by-day escalation, a system voice, and a countdown climax that pays off the gags.
   - The title pattern can be suggested next to the reference.
   - Dinosaurs are evergreen and the current uploads are mostly documentaries, so a comedy angle stands out.
   - Risk: we build 4 dinosaur rigs (they are reused in idea 3). Strict IP rules: no "Jurassic" anywhere, no gate arch with torches, no gyrosphere, no named film dinosaurs (Blue, Indominus), no John Williams theme, no film sound effects (the film's T-Rex roar and raptor calls; use library roars), and no restaged signature film shots: the rippling water cup, raptors stalking a kitchen, the T-Rex in a mirror, a brachiosaurus reveal under an awe swell.
   - Risk: "made for kids". A cartoon kid with dinosaurs may be classified as made for kids, which switches off comments (the "Comment ROAR" CTA dies) and personalised ads. Keep the general-audience parent-joke layer the reference has, and set the audience honestly on upload; mislabelling is a legal (COPPA) risk for the owner, not just a reach risk.
   - Risk: copying the reference too closely. Its structure and devices are free to use; its lines and signature gags are not. 7.12 sets the rule.
2. **What If Real Life Had a SETTINGS MENU?** (8.2)
   - The cheapest to make with our engine: UI-heavy, no creature rigs, and no IP risk.
   - The system voice and pop-up engine of the reference, applied to a slider that turns gravity down.
   - A weaker search noun, so it depends on the thumbnail.
   - The backup, or video #2.
3. **What If a T-Rex Hatched in Your House? (7 Days)** (8.0)
   - The creature doubles in size each day, so escalation and stakes are built in.
   - It reuses the rigs from idea 1, so it is a cheap follow-up.
   - Higher risk of being classified "made for kids".
4. **What If the WHOLE WORLD Became Minecraft?** (7.9)
   - The highest audience overlap with the reference.
   - But it reads as a reskin of it, and you asked for something new.
   - We cannot use Mojang's character designs, textures or logo.
   - The reference channel will probably make this one next.
5. **What If the WHOLE WORLD Became a Cartoon?** (7.5)
   - The best showcase for exactly what you asked for: acting, squash and stretch, speed.
   - The search demand is unproven.
   - I rank it above "Dinosaurs for 24 Hours" (7.6) because that one would compete with ideas 1 and 3 for the same dinosaur audience in the most crowded wording.

### 6.2 Recommended first video: cast and world

- **The Kid ("you")** wears an orange hoodie with a white footprint logo and the channel's orange headphones, plus a park wristband reading "GUEST · ALL ACCESS".
- **Mom** wins a plush dinosaur at every game stall, and the pile she carries grows (our accumulation gag; the reference's was Mom's hat tower, so no hats).
- **Dad**'s rule is "never run from a raptor", and he always runs.
- **Biscuit**, the dog, is now a baby triceratops.
- **Rex** is the T-Rex who becomes the teacher.
- **The raptors** are a mischievous trio.
- **Brachio** is the gentle giant who ends up as the elevator.
- **The PARK ANNOUNCER** is the system voice, with a two-tone chime.
- **Running gags:** the wristband won't come off; "YOU MUST BE THIS TALL" signs; wait-time boards; every door exits through the gift shop; the ticket's fine print; Mom's plush pile; Dad running; Biscuit; everything costs one token more than you have; the PA chime.

### 6.3 60-second hook script draft

Delivery is in brackets. KEY words are the caption colour words.

| t | ID | Role | Line | Picture (template) | Sound |
|---|---|---|---|---|---|
| 0:00.2-0:03.4 | S00-L001 | N [hype, rising] | "What if one morning... the WHOLE WORLD was a dinosaur PARK?" | Dawn suburb (T1, push +6%). On "PARK" a brachiosaurus neck pops up over the roofs like a periscope and a striped ticket booth with balloons slams down at the end of our street | Bouncy hype cue; sub boom plus brass stab on PARK; birds |
| 0:03.6-0:04.6 | S00-L002 | N [punchy] | "Seven days." | ticketTear: DAY 1 → 7 stubs tear off every 0.3 s; DAY 7 is red with a "60" badge and a starburst | 5 tear rips plus a boom |
| 0:04.9-0:05.8 | S00-L003 | N | "One park." | A park-map brochure card, "THE WHOLE WORLD · OPEN NOW · 8,000,000,000 guests ▶ ENTER", pops, then zoom-through into the map | Whoosh into the zoom-through |
| 0:06.2-0:10.0 | S00-L004 | N [drops to DEADPAN] | "And on day seven... something wanted OUT." | Time-lapse grade to the volcano-red sky; the turnstiles at the end of our street spin backwards and the park fence bursts outward; two huge footprints stamp; the countdown ring "60" pops (T14 → T9) | Boom on red; 2 stomps with rumble; ring entrance |
| 0:10.3-0:12.8 | S00-L005 | SYS (chime) | "Attention guests: the park closes... in sixty seconds." | Hazard banner "! PARK CLOSING IN 60 SECONDS"; PA speaker on a lamp post; a raptor holds a map upside down (T12) | Two-tone chime; siren starts |
| 0:12.4-0:13.2 | S00-L006 | CROWD | "Who bought the TICKET?!" | Bubbles pop: HELP! / my car!! / who bought the ticket?? / a stegosaurus "NOOO" | Bubble pops ×6 |
| 0:13.3-0:16.0 | S00-L007 | KID [panicked, fast] | "It's NOT my fault! ...Okay, it's a LITTLE my fault." | Hero close-up (T3-lite, push 6%); ring top left; sweat ×2; arms snap up at 14.4 | Panic slide-whistle |
| 0:16.2-0:17.3 | (no line) | | | VHS PAUSE, then ◄◄ REW with flash-forwards (the brachio elevator, the plush pile, Dad running) | Tape rewind; music drops to -50 dB |
| 0:17.4-0:19.8 | S00-L008 | N [calm, night] | "Last night. Midnight snack." | Night kitchen; the fridge light under-lights the Kid's face; cereal bowl (T1 night grade, push +14%) | Music-box plinks |
| 0:20.0-0:22.4 | S00-L009 | N | "A GOLDEN ticket falls out of your cereal." | Insert: the ticket flutters into the bowl and glints (T7) | Sparkle ting; splash plink |
| 0:22.7-0:26.0 | S00-L010 | N [reading] | "'Turn your town into a dinosaur park? Scratch to ACCEPT.'" | POV hands, ticket UI typewriter, one scratch box (T5, push +25%) | Type ticks; low thump on the question |
| 0:26.2-0:28.4 | S00-L011 | N [deadpan] | "There's no 'decline' box." | The coin hunts for a DECLINE box; there is none. A magnifier finds the fine print: "Another bite of this cereal counts as ACCEPT." (first joke) | Scratch; magnifier whoosh; tiny "dun" |
| 0:28.7-0:30.3 | S00-L012 | KID [sleepy, greedy smirk] | "Free park? ...Sure." | Half-lids and a slow smirk (T2), then a yawn | Drowsy pitch glide |
| 0:30.5-0:31.7 | S00-L013 | DAD [off-screen, muffled] | "Who's eating cereal at midnight?" | The Kid freezes guiltily; the ceiling light flicks on upstairs | Footsteps upstairs |
| 0:32.4-0:33.8 | S00-L014 | N [slow, weighty] | "You took... one more bite." | POV spoon crunch; a vine-and-leaf tile grid spreads from the ticket and fills the screen in 11 frames | Crunch hit, then the biggest sub boom so far |
| 0:34.0-0:36.8 | S00-L015 (0:35.2-0:36.6) | SYS (chime) | "Welcome... to the park!" | TRANSFORM: the Kid glows with an orbiting leaf ring; whip tilt up; the house becomes the park (fence → electric fence, mailbox → GIFT SHOP sign, car → safari tram on rails); the globe gets a map grid with pins; sunrise | Sparkle ladder, whoosh, PA chime, the music swells and ducks under the line, boom |
| 0:37.0 | S01-L001 | N | "Day one." | DAY 1 title slams over the morning bedroom (T13) | Riser into the slam; Day 1 cue (marimba, 122 BPM) |
| 0:38.2-0:40.0 | S01-L002 | N | "Six a.m. Instead of your alarm..." | The clock wiggles and becomes a PA speaker | Wiggle tick |
| 0:40.2-0:41.6 | S01-L003 | SYS | "Good morning, guests!" | Toast "Wristband activated · Day 1"; the Kid's eyes snap open (T3) | Chime; ping; shock sting |
| 0:42.3-0:44.0 | S01-L004 | N | "Then... you check your wrist." | POV: neon wristband "GUEST · ALL ACCESS" | Scanner beep |
| 0:44.2-0:45.4 | S01-L005 | N [deadpan] | "It won't come OFF." | Pull... "THWAP!" sticker as it snaps back; deadpan (T4) | Rubber twang plus smack; music drop |
| 0:45.8-0:47.6 | S01-L006 | N | "Your dog?" | Biscuit, a baby triceratops, licks his face: "SLURP!" sticker | Slurp; tail-wag thumps; music slams back |
| 0:47.8-0:48.8 | S01-L007 | N [deadpan] | "Triceratops." | Slobbered deadpan close-up | (music drop) |
| 0:49.2-0:51.5 | S01-L008 | N | "And the stairs have a sign:" | Insert: "YOU MUST BE THIS TALL TO RIDE" with a measuring arrow | Ding |
| 0:51.8-0:52.6 | S01-L009 | N [deadpan] | "You're NOT." | Red ✗ "BZZT"; he rides the banister instead, now a water slide: "WHEEE... SPLASH!" (T8) | Buzzer; slide-whistle down; splash |
| 0:53.5-0:56.0 | S01-L010 | MOM [PA, sing-song] | "Breakfast is now served... in the FOOD COURT!" | Mom with a PA mic in the kitchen; a queue rope; a wait-time board | Chime; Mom's voice through the PA chain |
| 0:56.4-0:58.2 | S01-L011 | N | "The wait time for breakfast..." | The wait board flips | Split-flap clatter |
| 0:58.4-1:00.0 | S01-L012 | SYS [flat] | "...forty-five MINUTES." | Board reads 45 MIN; the Kid's face droops (T4) | Music drop, then re-entry on the cut |

Count check: 5 voices by 0:31; first joke at 0:27; stakes and deadline by 0:10.6; DAY 1 at 0:37; 7 gags between 0:38 and 1:00, which matches the reference's Day 1 density. Longest voice gap 1.4 s, twice (the VHS rewind and the transformation), each filled by a sound gag. Fastest line about 3.7 words/s (the panicked KID). No 4-word run matches the reference script except the title formula.

### 6.4 Beat outline (about 8:00)

| Time | Section | Beats and gags (each: premise → proof → twist → reaction) | Plants (P) and payoffs (★) | Look and music |
|---|---|---|---|---|
| 0:00-0:37 | Cold open | As 6.3 | P: the ticket and its fine print (no decline box), Dad at midnight | Hype → night music box → transformation swell |
| 0:37-1:35 | DAY 1: "Good morning, guests" | PA alarm; wristband won't come off; Biscuit is a triceratops; the height sign and the stair slide; breakfast in the food court with a 45-min wait; the bathroom exits through the gift shop and Mom wins **plush #1** at a ring-toss stall; Brachio "mows" the lawn by eating the hedge; Dad's car is a safari tram on rails and only loops the block ("Dad's been to work... 0 times"). The Day 1 button: Dad passes for the 30th time, "Almost there!" | P: height sign, gift shop, plush #1, Dad's tram loop, Brachio | Bright day, jungle green and sky blue; bouncy marimba at 122 BPM |
| 1:35-2:30 | DAY 2: "Park Rules" | ruleCards 1-4. 1: Stay inside your fence (the Kid steps into the neighbour's yard, ZAP, hair poofs). 2: Never run from a raptor (Dad runs; a chase montage; "Dad is now the fastest man in town"). 3: Feeding time is 12:00 (every carnivore turns toward Dad's barbecue). 4: Keep hands inside the ride at all times (the swing, the bathtub, the shopping cart all get safety bars) | P: Dad running, feeding time | Rules march cue, 116 BPM |
| 2:30-3:20 | DAY 3: School field trip | Rex is the teacher and can't reach the board (tiny arms; writes with a stick); the lesson is an animatronic show that restarts from the top every time the door opens ("Welcome, explorers, to the Age of... *click* Welcome, explorers..."); a pop quiz at a dig site (fossils); recess, pterodactyls steal lunches; role reversal: tourists tap on the classroom window at a sign "HUMANS · Feeding 3 PM" | ★ Rex's short arms (callback in Day 7); P: Rex | Warm school palette; quirky cue |
| 3:20-4:30 | DAY 4: "One token short" | Money becomes park tokens (concept card with a token spin); everything costs exactly one token more than you have, and the price ticks up as you open your wallet; a photo booth on every corner ("Your photo: 25 tokens", with a flash); Mom's plush pile grows from 1 to **40** (accumulation tilt-up plus snap-out reveal); Dad's wallet holds only a park map. **Mid CTA at about 4:15:** the PA announces a new perk, "Subscribers ride in the VIP lane." Cut to the regular queue: the wait board flips to ∞ and a skeleton in a sun hat waves from the line (deadpan, music drop) | ★ plush #1 → 40; P: one token short | Neon gift-shop pinks and teals; music drop on the ∞ board |
| 4:30-5:15 | DAY 5: "Power outage" | "Park systems offline": fences flicker; Mom's plush pile and the cereal bowl hop with each distant footstep (BOOM... BOOM); emergency red pools on blue night; the PA chime stutters "G-g-guests..." (lag toolkit); the raptors raid the snack bar and try on Mom's plushies; Dad tiptoes; the twist: Rex just wants the night light back (deadpan) | P: the night light | Cold blue night with red emergency light; suspense pulse with a power-down sweep |
| 5:15-6:05 | DAY 6: "The Visitor" | A shadow crosses the street; whip tilt up to a GIANT HAND holding a park map; the hand peels the school up like a sticker and re-sticks it beside Rex's paddock; it draws a dotted tour route straight through your kitchen, and the safari tram follows it through the house; pin labels cascade on every building ("everything is an attraction"); snap-out: the whole town sits inside a gift-shop SNOW GLOBE, held by a giant kid deciding whether to buy it. He shakes it: snow, earthquake, everyone tumbles. Anticlimax: Mom waves at him | ★ gift-shop gag; P: the giant visitor, the snow globe | Golden-hour diorama look; mystery cue |
| 6:05-7:40 | DAY 7: "The park is closing" | PA "Attention guests"; volcano-red grade wipe and flash frame; countdown 60. SYS: "Guests still in the park at closing... will be kept for next season." KID: "We're the SOUVENIR?!" (glitch to the snow globe sitting on a shelf, then back). The fine print on the cereal ticket: "All guests must exit through the gift shop", and the gift shop is on top of the volcano. **Assembly from callbacks:** Brachio as an elevator (Day 1 lawn), Mom's 40 plush dinos as bouncy stepping stones, Dad's tram-loop rails as the track up the slope, Dad's running (Rule 2) outrunning the raptors with the Kid on his shoulders, Biscuit pushing, Rex's tiny arms giving the Kid a boost ("first time those arms reached anything"). At the gift-shop turnstile, **the height sign: you're finally tall enough, on Dad's shoulders** (★ Day 1). The giant hand reaches for the CLOSE lever; KID: "We never even got our ride photo!"; music drop; the photo booth flashes; the giant kid buys the photo instead of the globe and walks out; a "Rate your visit ★★★★★?" dialog; the Kid taps 5 stars ×3, escalating hits with a 1-2-frame flash. Restoration montage reversing each gag: Biscuit is a dog again (the frill stays), the wristband pops off, Mom's pile shrinks to one plush, Dad's tram is a car again and he drives straight into a 45-minute traffic jam (★ the wait board) | ★ fine print, height sign, plush pile, Dad running, tram rails, Brachio, Rex's arms, gift shop, wait board | Volcano red → black at the summit → restored flat blue; chase cue at 140 BPM modulating upward; riser; major-key resolution; brass TA-DA |
| 7:40-8:00 | Ending | "The park was gone. Well... mostly." The PA chime rings once from the kitchen. The egg in the fridge wobbles and cracks. **End CTA:** "Comment ROAR if you'd buy a ticket" (comment panel count-up). Loop: the cereal box back reads "Collect all 7 tickets!" and a new ticket falls out: "Turn your town into... an OCEAN park?" KID: "Mom! Do NOT pour that cere—" cut to black | ★ the cereal ticket; series tease | Glitch sting, cut on the last syllable |

Planned totals: about 7 DAY cards; about 90-100 gags; 9 callbacks paid off in Day 7; 2 in-world CTAs.

---

## 7. Lessons from the Vox session we must apply

1. **Reference first, measured with code, written into a contract before building.** Vox v1 failed on exactly the things it never measured. This bible's section 0 is that contract. Put it into `episodes/ep3/SPEC.md` and gate every phase on it.
2. **Use "ultracode" effort for coding, spent wisely:** parallel agents for independent modules (style, rig, face, cam, UI, FX, audio), then critic → fixer → verifier rounds on short clips with numeric before/after checks, *before* the full render. In Vox this caught frozen acting, lip-sync at 0.16 correlation, a stale mix, hot radio lines and clashing keys.
3. **Rendering costs no usage; agent work does.** Render generously (previews, A/B clips, full passes) and spend usage on code quality. Keep check-ins sparse during renders (about every 25 min).
4. **Usage limit and container resilience.**
   - Commit and checkpoint before every long agent phase.
   - Keep working data inside the project, not the scratchpad. A container restart killed the Vox workflows and invalidated scratchpad paths. In P1, copy this bible, `all_findings.json` and `study/audio/scripts/` into the project (`docs/ep3/` and `tools/refmetrics/`); the large reference media can stay in the scratchpad.
   - Use absolute paths and `.done` markers so renders can resume.
   - When the owner asks "are you sure it is running?", actually check the processes.
5. **Progress reporting the owner's way:** "step N of M", then "frame N of 28,800 · X fps", on a live page that is republished on every update. The Vox page sat at 0 frames because it was never republished.
6. **Sound comes from licensed recordings.** Give the owner an exact, grouped Epidemic shopping list (section 4.3), ask for zipped uploads, never commit Epidemic files, and remind them to connect the channel in Epidemic to avoid Content ID claims and to publish while the subscription is active (4.2). Credit any CC-BY items in the description (including Piper libritts_r voices, if used).
7. **Voices:** the owner's commercial tool does the final voices (section 5). Never handle or repeat API keys; if a key is pasted, advise revoking it. Don't clone third-party voices.
8. **Don't invent new designs for the thumbnail.** Reuse the film's own character code (Vox `draw_bust`), clear and clean, with no blur. Note the inversion: the Vox lesson was "creepy, not goofy" because that was horror. **Here the target is expressive, weird, funny faces:** star eyes, sweat and blush are exactly right.
9. **Owner check-ins at the decisive points only:** (1) idea and cast approval; (2) the 60-s hook proof at final quality, the most important gate; (3) the full animatic; (4) the final. Show a clip, not a description.
10. **Delivery:** lead with one upload-ready 10-bit HEVC file of 400 MB or less (chat limit; 10-bit keeps the clean gradients from banding), plus the near-lossless master in parts with JOIN.txt and a SHA256. Recommend a fresh single-niche channel plus 2-3 Shorts cut from the video. The Vox upload on an old travel channel got 3 impressions in 12 h.
11. **Camera realism.** Any in-world device or camera (photo booth, CCTV in the outage) must behave like the real thing: apply the lens to the composited layers so moves and lean-ins distort correctly.
12. **Match the reference's quality, not its script.** Its devices are free to use: the cold-open flash-forward, the day counter, numbered rules, an in-world CTA, callbacks paid off in a countdown climax, a loop ending. Its words and signature gags are not: no shared run of 4+ words outside the title formula ("Okay, okay, I can explain", "Your alarm doesn't ring", "hold your breath", "Nobody can jump that high", "Everything was back to normal. Almost." are all out), no Mom-says-"sweetie" tic, no hat tower, no 99-price gag, no identical NPC-line loop, no "it changes your roof to pink" beat. A close clone invites a manual copyright claim from the reference channel, YouTube's reused-content review, and copycat comments from exactly the audience we want to be suggested to. `tools/originality.py` (3.9) enforces the text side.

---

## 8. Phased plan with time estimates

A "session" is one working block of about 4-5 hours of agent time. Machine render hours cost no usage and are listed separately.

| Phase | What | Owner's part | Agent time | Machine | Gate |
|---|---|---|---|---|---|
| P0 Decisions | Approve the idea and cast; confirm the Epidemic subscription end date and which channel is connected (4.2); confirm the Fish plan allows commercial use; start the Epidemic downloads (4.2/4.3); pick Fish voices and send 4 test lines. We re-run the NexLev checks after the weekly reset (2026-11-03 06:23 UTC): the reference channel, its outliers, view counts of recent dinosaur "What if" uploads | 1.5-2 h | 0.5 session | none | Owner OK on idea #1 |
| P1 Contract and script | Copy the study into the project (7.4); free ≥6 GB of disk (with the owner's OK, 3.8); SPEC.md (section 0); script v1 (about 1,050 words, about 230 lines, HYPE/DEADPAN tags); line sheet; shot list skeleton with templates; Kokoro scratch VO plus alignment; fonts (Nunito) | review the script (20 min), then generate the hook's ~27 lines (15-20 min) | 1-1.5 sessions | ~0.2 h | Script reads at 130-140 wpm, has ≥90 gags and passes `originality.py` |
| P2 Engine v3 core | style.js, rig.js plus face.js (kit, visemes, blink and saccade, springs), cam.js, caption2.js, ui.js, fx.js, cues.js, templates T1-T16; render_anim segmenting, sub-frame blur, resume; qa_metrics.py. Parallel agents | none | 3-4 sessions | ~0.5 h of tests | Unit clips per module; 20-frame benchmark ≥2 fps at 1440p |
| P3 Hook proof | The 0:00-1:00 hook at final quality (1440p60) with the owner's real voices for the hook (scratch only if they are late), Epidemic music and the full SFX layer; run every metric; critic, fixer, verifier | **check-in #1**: watch 60 s (10 min) | 1.5-2 sessions | ~1 h | Section 0 metrics pass; the owner says "this is the level" |
| P4 Cast and sets | Kid, Mom, Dad, crowd kit (8 variants), Rex, raptors, Brachio, Biscuit; about 9 sets (bedroom, kitchen, stairs, street, school, park plaza, gift shop, night street, volcano summit); park UI chrome | none | 2.5-3.5 sessions | ~0.5 h | Turnaround and expression sheets |
| P5 Full animatic (720p30) | All 8 minutes with scratch VO, cues and temp music; metrics on the full length | **check-in #2**: watch the animatic (15 min), notes | 2.5-3.5 sessions | ~1.5 h (3 passes) | Cut rate, gags and timing pass; owner notes in |
| P6 Final voices and sound | Ingest the owner's Fish files, QA, retake list; re-flow the timeline; lip-sync; edit Epidemic stems to the cue sheet; SFX placement; mix to the 4.4 targets | record the remaining ~200 lines (60-90 min as per-scene batch files), plus retakes | 1.5-2 sessions | ~0.3 h | LUFS, LRA, density, sync gates pass |
| P7 Review loop | Critic (picture, acting, comedy, sound) → fixer → verifier on 6 clips; fix list | none | 1-1.5 sessions | ~1 h | Verifier go |
| P8 Final render and delivery | 1440p60 segmented render; assembly; final QA; 10-bit HEVC ≤400 MB plus master parts; thumbnail (character code reuse, 2-3 A/B); title, description, tags, CC-BY credits; 2-3 Shorts | **check-in #3**: final approval | 1-1.5 sessions | 2-4 h | Delivered |
| **Total** | | **≈3.5-4.5 h** | **≈14-20 sessions ≈ 6-9 calendar days** (usage windows permitting) | **≈7-9 h** | |

**After this video:** most of P2 and much of P4 is a one-time investment. Video #2 (for example the Settings Menu, or the T-Rex hatchling reusing these dinosaur rigs) should take about 50-60% of this effort.

**Risks to watch:**
1. Render speed below 2 fps. Fall back to more baking and fewer live blurs; re-open the skia question only after the benchmark.
2. Disk space: must be freed in P1; even the hook proof does not fit in today's ~860 MB.
3. Voice turnaround from the owner. The scratch track keeps us unblocked.
4. Dinosaur rigs being the long pole of P4. Build Rex first; the others derive from its chain code.
5. IP: run a check for "Jurassic" in all text and art, and no film-like designs, shots, sounds or music (6.1).
6. Copying the reference: `originality.py` on every script version, plus the beat-level rule in 7.12.
7. Licences lapsing: the video must be published while the Epidemic month is active, on a connected channel.
8. Bespoke assets per gag: templates stage a gag, but 90-100 gags still need roughly 60-80 one-off props and animations. If P5 slips, cut to about 75 gags and keep the density with reaction close-ups and UI proofs, which are cheap.
