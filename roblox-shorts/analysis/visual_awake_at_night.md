# Visual analysis: "Never Be Caught Awake At Night" (awake_at_night)

Reference only. The frames are copyrighted, so every frame cited here stays in scratch and none is in the repo. We copy the craft, not the content.

- **Source:** `scratchpad/rbx/ref60/awake_at_night.mp4`. Container: H.264, 1080x1920, 60 fps, 174.27 s, 1.25 Mb/s, AAC 44.1 kHz stereo.
- **Evidence root (scratch):** `/tmp/claude-0/-home-user-claude-todo-demo/353ac1d9-152b-55bb-bdf1-0625e0fc6a83/scratchpad/rbx/work/vis_awake/`. Below this is written `VA/`.
  - `VA/f/tSSS.SS.jpg`: 98 full-resolution stills, named by time in seconds.
  - `VA/sheets/s_1..5.jpg`: frame sheets at 1 s steps.
  - `VA/trip_1..4.jpg`: first, middle and last frame of every shot.
  - `VA/pairs1..3.jpg`: the frame before and after every candidate cut.
  - `VA/an_*.jpg`: 60 fps motion strips.
  - `VA/g_00..16.jpg`: 6-up grids of the full-resolution stills.
  - `VA/spec_*.png`: audio spectrograms.
  - `VA/py/*.py`: the measurement scripts. `cuts.py` holds the frame-exact cut list. The other scripts are motion, residual, caption-change and shot-list scripts.
- **How it was watched.**
  - About 1,000 frames were looked at in total: the 174 frames on the sheets, about 130 before/after cut pairs, 306 first/middle/last shot frames, 98 full-resolution stills and about 250 frames from 60 fps strips.
  - On every one of the 10,453 frames, I measured the frame difference, the global camera motion (LK optical flow plus a similarity fit) and the subject motion left over after removing the camera motion.
  - Captions were tracked per frame and compared with Parakeet ASR word times. Those ASR times come from this full copy (`VA/asr.json`).
  - All colours are pixel samples (PIL or k-means), not guesses.
- **Sync note.** In this full copy, picture and voice both start at 0.00. The first 3.7 s, which were missing from the older trimmed copy, contain the opening hook: shots 1-3.

## 0. The 20 numbers that define this video

| What | Value |
|---|---|
| Shots | **102** (101 real cuts plus one 4-frame flicker), all hard cuts. One intro spin-zoom. **No fades, dissolves or wipes.** |
| Shot length | median **1.53 s**, mean 1.72 s, min 0.45 s, max 5.20 s. 13 % < 1 s, 55 % 1-2 s, 24 % 2-3 s, 8 % ≥ 3 s |
| Cutting rate | **34.8 cuts/min** (one new picture every ~7 narration words; the voice runs at 244 wpm) |
| Cut vs. word | a cut lands **median 40 ms (2-3 frames) before the onset of the word it illustrates**; 80 % of cuts fall within -120..+33 ms of a word onset. 49 % are on a sentence start, 24 % on a clause start, and 28 % mid-clause on the noun being illustrated |
| Camera motion | **97 % of shots move.** **80 % are slow push-ins**: median +14.6 %/s (IQR 9.6-22 %/s), median total 1.23x per shot. They run at constant speed, with no ease, and are cut mid-move. 10 % are pull-outs. Reveal words get a punch-in of 1.6-2.0x in about 1 s |
| Subject motion | 36 % of shots are **frozen tableaux**: only the camera moves, plus perhaps a face-decal swap. 33 % have small motion and 33 % have large motion. Measured as the share of pixels that change after removing camera motion |
| Real frame rate | **~37 unique fps** inside the 60 fps file: every 3rd frame or so is a duplicate, so motion judders a little. We should render true 60 |
| Shot sizes | MS 46 · WS 27 · CU 19 · MCU 7 · EWS 1 · ECU 1 |
| Angles | eye 61 · high 16 · low 16 · from behind / OTS 8 (plus 1 top-down at 90°) |
| Lens | mostly normal-to-wide. The Roblox default is 70° vertical FOV; the scenes read as about 50-70° vertical, with no lens distortion |
| Avatars | **R6 blocky (6 parts)** humans with the classic Roblox head, 2D shirt/pants textures, 3D hair meshes and **2D decal faces swapped instantly** (no blinking, no lip-sync) |
| Monster | a custom high-detail mesh ~2.4x Max's height. Glossy porcelain doll head, pleated nightgown, skeletal marionette fingers, rusty crank |
| Shadows | **none**: no cast shadows anywhere. Lighting is flat and ambient-heavy, plus Neon emissives |
| Black level | crushed: 27 % of night-exterior pixels and 36 % of factory pixels are below L=4. **Night sky = #000000** |
| Night grade | indigo/lavender. Mean #2f284b, R:G:B = 1.16:1:**1.86**, whites #d8d9f4 |
| Interior grade | rose. Mean #894f55, R:G:B = **1.73**:1:1.07, whites #ddbdd5 |
| Factory grade | magenta-plum. Mean #392039, R:G:B = 1.78:1:1.78, whites #f0d9f8 |
| Post effects | bloom only on emissive lights (halo ~25-30 px at 1080 w). **No vignette, no grain, no chromatic aberration, no DOF and no lens flare** (verified on flat walls) |
| Captions | **one word at a time**, Verdana Bold ~90 px, pure white, 6-7 px black stroke and soft shadow. Baseline y≈1335 (69.5 % down), centred. Hard swap at the word onset (median -20 ms) |
| Audio | voice -20 dB mid-channel throughout. A music bed sits under it: a narrow drone plus ticks in 0-4.4 s, then a wide stereo bed from ~23 s. Music-box SFX sit on every "tink", crank and twirl line. Also a door creak, a dive thud and a 1.8 s broadband screech that starts on the cut |

---

## 1. Shot list

Legend:
- **Lens.** W = wide (~65-75° vertical FOV). N = normal (~45-60°). T = tele (≤35°, inserts).
- **Measured scale.** The total image scale change over the shot, from optical flow. >1 means a push-in or zoom, <1 a pull-out. The %/s figure is the per-second rate.
- **Narration.** From ASR, with corrections from `script_r1_awake_at_night.md`. Each word is assigned to the shot in which it starts.
- **Evidence.** First, middle and last frames of every shot: `VA/trip_1.jpg` (#1-28), `trip_2` (#29-56), `trip_3` (#57-84), `trip_4` (#85-102).

| # | start-end (s) | dur | size | angle | lens | camera move | measured scale | on screen | narration covered |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.00-1.82 | 1.82 | WS | eye | W | intro spin-zoom (+18deg roll & 1.47x scale -> 0 in 0.35 s, overshoot -7deg), then slow truck R | 0.74x (-15%/s) | Lullaby walks the sidewalk past a cream brick house; pines, black sky; crank sticks out | In this world, something walks the streets |
| 2 | 1.82-3.70 | 1.88 | MS | low (inside, up through window) | N | push-in | 1.22x (+11%/s) | from inside a pale-blue bedroom: Lullaby bent at the window, head tilted, peering in | at midnight, and if you're awake when it passes, |
| 3 | 3.70-3.77 | 0.07 | MS | low | N | static (4 frames) | 1.01x (+0%/s) | same frame re-graded darker blue: 4-frame flicker before the next cut |  |
| 4 | 3.77-4.38 | 0.62 | MS>MCU | low | N | fast punch-in 1.9x in 0.6 s | 1.92x (+187%/s) | jointed hand rises and spreads on the glass ('takes you') | it takes you. |
| 5 | 4.38-6.10 | 1.72 | EWS | high ~35deg | W | slow push | 1.15x (+8%/s) | empty night street, zebra crossings, tiny Lullaby in the middle | You see, nobody has ever seen it up close. |
| 6 | 6.10-8.40 | 2.30 | MS | back 3/4 (from behind) | N | slow arc R + push | 1.43x (+17%/s) | Lullaby's back: crank turning, white notes rising; playground behind | You only hear it. A tiny tinkling music |
| 7 | 8.40-9.65 | 1.25 | MS | worm's-eye low | W | push 1.7x + tilt | 1.71x (+54%/s) | stained nightgown hem dragging, two skeletal hands | box song getting closer. |
| 8 | 9.65-10.75 | 1.10 | CU>ECU | slightly low | N | fast push 2.0x + roll +13deg | 2.03x (+90%/s) | first face reveal: tilted cracked doll head, notes | We call it Lullaby. |
| 9 | 10.75-12.57 | 1.82 | WS | low | W | slow push | 1.23x (+12%/s) | TOWN LAW / BEDTIME sign on black post (Dutch-tilted); two avatars walk past; blue house | So in our town, bedtime is the law. |
| 10 | 12.57-13.67 | 1.10 | MS | eye | N | slow push | 1.13x (+11%/s) | red-haired kid in tank top hugging blue pillow, frown; NOTICE: SLEEPOVERS ARE BANNED sign | Sleepovers are banned. |
| 11 | 13.67-15.05 | 1.38 | MS | high | N | push 1.37x | 1.37x (+25%/s) | kid curled asleep on closet floor under hanging coloured clothes | Some kids sleep in their closets. |
| 12 | 15.05-16.80 | 1.75 | MS | eye (outside window) | N | push 1.36x | 1.36x (+19%/s) | dad behind window hammering boards; hammer swings every ~0.55 s, dust puffs | Some families nail the windows shut. |
| 13 | 16.80-18.27 | 1.47 | MCU | high ~60deg top-down | N | push + slow roll | 1.18x (+12%/s) | mom (headband, plaid) singing over sleeping blonde kid; mouth decal flaps | And every parent in town sings their |
| 14 | 18.27-20.47 | 2.20 | MCU | high ~60deg | N | push + slow roll | 1.21x (+9%/s) | mirror shot: dad (magenta shirt) singing over red-haired kid ('exact same') | kids the exact same lullaby at bedtime. |
| 15 | 20.47-22.95 | 2.48 | WS | eye | W | near-static slow pull | 0.96x (-2%/s) | blue house at night, windows lit, switch off one by one (21.8/21.9/22.47 s) | The rule is simple. When you hear the music box, be asleep. |
| 16 | 22.95-25.42 | 2.47 | MS | high | N | push 1.5x | 1.51x (+18%/s) | Max asleep in bed (navy knit blanket, dark wood bed) | My name is Max, and I'm the best fake sleeper alive. |
| 17 | 25.42-27.58 | 2.17 | CU insert | high | N | push | 1.38x (+16%/s) | arm hanging off the bed | Slow breathing. One arm hanging off the bed. |
| 18 | 27.58-28.57 | 0.98 | ECU | eye | N | push | 1.23x (+23%/s) | Max sleeping face with drool bubble | A tiny bit of drool. |
| 19 | 28.57-29.75 | 1.18 | MS | OTS behind mom | N | slow push | 1.14x (+12%/s) | red-haired mom (red dress) leans over Max's bed | I've fooled my mom every night |
| 20 | 29.75-30.70 | 0.95 | MS | high | N | push | 1.32x (+34%/s) | Max 'asleep' (repeat of #16 set-up) | for five years. |
| 21 | 30.70-32.15 | 1.45 | MS | high | N | push 1.5x | 1.53x (+34%/s) | Dex in green dino onesie lying in bed | My best friend Dex is the opposite. |
| 22 | 32.15-35.28 | 3.13 | MS | eye, frontal | N | slow push | 1.17x (+5%/s) | Dex sits up wide awake; sheep hops a tiny fence, loops | Dex can't fall asleep, ever. He counts sheep until the sheep get bored. |
| 23 | 35.28-37.25 | 1.97 | CU insert > MS | eye > high | N | fast whip-pan R (~2400 px) across pink wall to the bed | 0.76x (-13%/s) | calendar OCTOBER, 24 circled, MATH TEST! > Max's bed | Then one night, the night before our big math test, |
| 24 | 37.25-38.87 | 1.62 | CU | eye | N | push 1.6x | 1.64x (+36%/s) | Max's face: eyes snap open (decal swap 37.8), then shocked big-mouth decal (38.3) | I heard it. Tink, tink, tink, tink. |
| 25 | 38.87-39.55 | 0.68 | CU | eye | N | push | 1.11x (+16%/s) | decal swap to squeezed-shut eyes ('went still') | I went still. |
| 26 | 39.55-40.80 | 1.25 | MCU | eye | N | slow push | 1.19x (+15%/s) | Max squeezed eyes, blanket up | Slow breathing. Arm off |
| 27 | 40.80-42.05 | 1.25 | MS | eye (inside) | N | push | 1.15x (+12%/s) | window with navy translucent curtain; cracked head rises into view outside | the bed. The song got louder, |
| 28 | 42.05-43.10 | 1.05 | CU | eye | N | push | 1.21x (+20%/s) | doll face at the glass, notes | right outside my window, |
| 29 | 43.10-45.50 | 2.40 | WS | eye | W | near-static | 1.10x (+4%/s) | Lullaby walks away down the street over the crosswalk; lamp post foreground | then softer. Moving down the street, toward Dex's house. |
| 30 | 45.50-46.05 | 0.55 | WS | eye | W | push | 1.22x (+43%/s) | DAY: Dex's yellow house, blue gradient sky | In the morning, |
| 31 | 46.05-48.05 | 2.00 | MS | high | N | push + tilt | 1.20x (+10%/s) | Max (frown) behind Dex's empty green bed | Dex's bed was empty. The sheets were still warm. |
| 32 | 48.05-49.57 | 1.52 | MS | eye, frontal | N | push | 1.24x (+15%/s) | Max sitting up in bed, awake | That night, I didn't fake sleep. |
| 33 | 49.57-51.05 | 1.48 | MCU | eye | N | push 1.36x | 1.36x (+23%/s) | Max smirk decal | Because there's one more thing everybody knows |
| 34 | 51.05-53.55 | 2.50 | WS | eye | W | slow push | 1.23x (+9%/s) | Lullaby glides past a sleepwalking kid (rainbow pyjamas, arms out) by the sign | about Lullaby: it never takes sleepwalkers. |
| 35 | 53.55-54.75 | 1.20 | MCU | slightly low | N | push | 1.12x (+10%/s) | sleepwalker: arms out, eyes shut, notes | Sleepwalkers are asleep. |
| 36 | 54.75-55.85 | 1.10 | CU insert | eye | T | push + pan | 1.28x (+25%/s) | red LED alarm clock 12:00 | So at midnight, when the music |
| 37 | 55.85-58.45 | 2.60 | MS | eye | N | crane down / tilt | 1.08x (+3%/s) | Max rises, arms come up straight (zombie pose), stands | started, I got up, arms straight out, feet dragging, |
| 38 | 58.45-59.90 | 1.45 | MS>MCU | eye | N | fast push 1.8x | 1.84x (+52%/s) | Max standing, head drooping | head drooping, and I sleepwalked |
| 39 | 59.90-61.02 | 1.12 | MS | from behind | N | tilt up | 1.03x (+3%/s) | Max walks out of the front door | right out my front door, |
| 40 | 61.02-62.12 | 1.10 | WS | eye, profile | W | push | 1.16x (+14%/s) | Lullaby full body in profile on the street, streetlamp | and there it was, ten |
| 41 | 62.12-63.65 | 1.53 | MS | low, tilt-up | W | tilt/crane up along body (~850 px) | 1.01x (+1%/s) | hem to head: 'ten feet tall, thin as a lamppost' | feet tall, thin as a lamppost, |
| 42 | 63.65-66.20 | 2.55 | MS | low | W | arc ~17deg + slow pull | 0.81x (-8%/s) | nightgown, stained hem, hands | in a long white nightgown that dragged along the road. |
| 43 | 66.20-69.85 | 3.65 | CU>ECU | eye | N | slow push 1.6x + roll -12deg | 1.60x (+14%/s) | tilted cracked doll head, notes (longest face hold, 3.65 s) | Its head was a cracked porcelain doll's head, tilted to one side, like it was listening. |
| 44 | 69.85-72.10 | 2.25 | MCU | eye | N | truck L | 1.04x (+2%/s) | jointed fingers foreground, Max sleepwalking far behind | Its fingers were long and white and jointed, like a |
| 45 | 72.10-72.55 | 0.45 | CU | eye | N | static | 1.02x (+4%/s) | fingers spread (0.45 s insert) | puppet's, |
| 46 | 72.55-77.75 | 5.20 | MS | from behind | N | slow orbit ~27deg L>R + push 1.37x | 1.37x (+6%/s) | crank turning on her back, notes bursting; TOWN LAW sign revealed | and sticking out of its back was a giant, rusty crank. Turning all by itself. Tink, tink a tink. Every turn |
| 47 | 77.75-79.70 | 1.95 | WS | eye | W | near-static | 1.13x (+7%/s) | street: Lullaby walking, Max shuffling behind; she stops | played one more note of the song. It stopped. |
| 48 | 79.70-80.80 | 1.10 | CU | behind head | N | push | 1.21x (+19%/s) | head rotates 180deg to camera in ~0.8 s (ease in-out) | Its head turned all the way around |
| 49 | 80.80-81.73 | 0.93 | CU | low | N | fast push 1.4x | 1.39x (+42%/s) | doll face after the turn | toward me. I kept |
| 50 | 81.73-83.25 | 1.52 | MS | eye, frontal | N | push | 1.23x (+15%/s) | Max sleepwalks to camera, arms out, head drooping, decal swaps | walking, arms out, drooling. |
| 51 | 83.25-85.35 | 2.10 | WS | eye | W | near-static | 1.10x (+5%/s) | Lullaby (fg right) watches Max beside the blue house | It watched me for a long time, then it turned back |
| 52 | 85.35-86.05 | 0.70 | CU | behind head | N | push | 1.18x (+27%/s) | head turns back away | around and kept |
| 53 | 86.05-88.05 | 2.00 | WS | OTS high behind Max | W | slow pull | 0.89x (-6%/s) | Max's head bottom frame, Lullaby walking toward the clock-tower factory | going. I followed it all the way across town, |
| 54 | 88.05-90.00 | 1.95 | WS | low | W | tilt | 1.11x (+6%/s) | factory facade: brick, clock tower, TICK & TUNE TOY CO. sign, full moon; both characters | to the old Tick and Tune Toy Factory, the one |
| 55 | 90.00-91.05 | 1.05 | CU insert | eye | T | push 1.3x | 1.30x (+29%/s) | clock face at 12 on brick | that closed a hundred years ago. |
| 56 | 91.05-93.05 | 2.00 | MS | eye | N | slow pull | 0.90x (-5%/s) | dark doorway; Lullaby appears in the open doors | The doors creaked open by themselves. |
| 57 | 93.05-95.05 | 2.00 | WS | eye | W | near-static | 1.07x (+3%/s) | interior: giant music box under hanging marionettes, darkness | Inside, it was a nightmare made of toys. |
| 58 | 95.05-98.65 | 3.60 | MS | low | W | tilt (~640 px) + push | 1.33x (+8%/s) | marionettes swaying on strings, shelves of music boxes | Marionettes hung from the ceiling. Swaying, with no strings attached to anything, |
| 59 | 98.65-100.70 | 2.05 | WS | high | W | push 1.46x + pan | 1.46x (+20%/s) | rows of teddy bears on conveyor belts receding; light shafts | rows of teddy bears sat on the conveyor belts, |
| 60 | 100.70-101.75 | 1.05 | MS | low, frontal | N | push | 1.17x (+16%/s) | teddies facing camera | all facing the door. |
| 61 | 101.75-105.85 | 4.10 | WS | eye | W | long pan L (~1100 px) + push 2.3x | 2.28x (+22%/s) | walls of shelves full of music boxes, marionettes, light shaft | The walls were stacked with music boxes, thousands of them, every single one ticking. |
| 62 | 105.85-109.85 | 4.00 | WS | OTS behind Max | W | push + crane | 1.32x (+7%/s) | Max facing the carousel-sized music box, round mirror lid | And in the middle of the room was the biggest music box I've ever seen. Big as a carousel, |
| 63 | 109.85-112.95 | 3.10 | WS | high | W | slow pull | 0.81x (-6%/s) | top of the music box: mirror lid, brass pole, kids on pegs spinning | lid wide open, and spinning on top, on little brass pegs, |
| 64 | 112.95-115.20 | 2.25 | MS | eye among pegs | N | push + roll | 1.35x (+14%/s) | tiny kids in pyjamas twirling on pegs | were tiny dancers, kids, in pajamas, |
| 65 | 115.20-117.45 | 2.25 | MS | eye | N | pan | 1.23x (+10%/s) | kids circling the brass pole | shrunk down to the size of my thumb. Twirling |
| 66 | 117.45-119.05 | 1.60 | WS | top-down 90deg | W | push; platter rotates ~19deg/s | 1.26x (+15%/s) | overhead of the rotating platter | around and around, forever, |
| 67 | 119.05-120.48 | 1.43 | MS | eye | N | fast pan following rotation | 0.94x (-5%/s) | kids on pegs passing camera | every kid who'd ever been taken. |
| 68 | 120.48-122.22 | 1.73 | MS | eye, frontal | N | push + roll | 1.27x (+15%/s) | Dex on a peg, arms up, dazed smile decal | And right in front was Dex in his |
| 69 | 122.22-123.20 | 0.98 | MCU | eye | N | push | 1.27x (+27%/s) | Max: 'o' decal swaps to horrified grimace | dinosaur pajamas. |
| 70 | 123.20-126.05 | 2.85 | MS | low | N | slow push | 1.23x (+8%/s) | Lullaby leans over the box, points one finger at an empty peg; bulbs fg | Lullaby reached out with one long finger toward an empty brass |
| 71 | 126.05-127.80 | 1.75 | MS | eye (Max POV) | N | push + tilt | 1.23x (+13%/s) | Lullaby turns and points at camera | peg, and then toward me. It knew. |
| 72 | 127.80-129.10 | 1.30 | WS | eye | W | follow pan | 1.07x (+5%/s) | Max runs from Lullaby across the wooden floor | I ran. Its fingers snapped |
| 73 | 129.10-130.23 | 1.13 | MS | high | N | fast pan (~800 px) | 1.18x (+16%/s) | hand snaps shut just behind Max's head | shut right behind my head. |
| 74 | 130.23-131.60 | 1.37 | WS | eye | W | pan | 0.99x (-1%/s) | Max dives flat behind the music box | I dove behind the giant music |
| 75 | 131.60-133.15 | 1.55 | WS | eye | W | push | 1.22x (+14%/s) | Lullaby searching, notes trailing, marionettes | box, and that's when I noticed something. |
| 76 | 133.15-135.05 | 1.90 | CU | eye | N | push | 1.39x (+19%/s) | crank slowing, few notes | Its crank was slowing down. Tink, tink. |
| 77 | 135.05-136.65 | 1.60 | CU | eye | N | push 1.8x | 1.77x (+43%/s) | Max (back of head turns to face, 'o' decal) | And I remembered my grandpa's old music |
| 78 | 136.65-138.05 | 1.40 | WS | eye | N | slow push | 1.17x (+12%/s) | FLASHBACK warm daylight: grandpa by little Max's bed with open music box | box. Here's the thing about music |
| 79 | 138.05-140.40 | 2.35 | MS | eye | N | push | 1.27x (+11%/s) | grandpa (white hair+beard) talking, ballerina spinning | boxes, Max, he told me once. When the song ends, |
| 80 | 140.40-141.40 | 1.00 | CU insert | eye | N | push | 1.34x (+34%/s) | ballerina stops | the dancer stops. |
| 81 | 141.40-142.72 | 1.32 | WS>MS | eye | N | fast push 2.0x | 1.98x (+68%/s) | Lullaby comes round the corner; Max hides fg right | Lullaby came around the corner, |
| 82 | 142.72-143.78 | 1.07 | MS | eye | N | pan | 1.06x (+5%/s) | Max jumps onto its back | and I jumped onto its back, |
| 83 | 143.78-145.35 | 1.57 | MS | eye | N | slow push | 1.26x (+16%/s) | Max clings, grabs the crank | grabbed that rusty crank with both |
| 84 | 145.35-146.70 | 1.35 | MS | low | N | shaky follow | 1.09x (+7%/s) | Lullaby's arms fly up, Max cranks backwards | hands, and I turned it backwards. |
| 85 | 146.70-148.95 | 2.25 | WS | eye | W | near-static | 1.01x (+0%/s) | Max cranking on its back by the box, notes swirl | The song played in reverse, knit a knit, knit. |
| 86 | 148.95-149.90 | 0.95 | CU | eye | N | violent shake (+-70 px jitter, ~1 s) | 1.05x (+5%/s) | doll face screeching | Lullaby screeched. |
| 87 | 149.90-150.50 | 0.60 | MS | from behind | N | push | 1.11x (+20%/s) | arms out in a T, flailing | Its arms |
| 88 | 150.50-152.05 | 1.55 | MS | eye | N | push | 1.19x (+12%/s) | kids on pegs | flailed. And on top of the music box, |
| 89 | 152.05-152.97 | 0.92 | MS | eye | N | near-static | 1.08x (+8%/s) | dancers stop spinning | the dancers stopped |
| 90 | 152.97-154.27 | 1.30 | WS | low | W | pull-out 0.8x | 0.80x (-16%/s) | music-box rim; panel lights switch on at 153.0; kids start to grow | spinning and started to grow. |
| 91 | 154.27-155.02 | 0.75 | MS | eye | N | static-ish | 1.01x (+1%/s) | a kid pops off the peg toward camera | One by one, |
| 92 | 155.02-157.30 | 2.28 | WS | eye | W | pull-out | 0.82x (-8%/s) | kids tumble onto the floor in front of the box | kids popped off their pegs and tumbled onto the floor. |
| 93 | 157.30-159.03 | 1.73 | WS | eye | W | crane, foreground marionette wipe | 1.38x (+20%/s) | Lullaby on the box shrinking among kids | And Lullaby got smaller and smaller |
| 94 | 159.03-162.55 | 3.52 | MS>WS | eye | N | pull-back + crane down (scale 0.22x, ~1440 px tilt) | 0.22x (-35%/s) | thumb-sized Lullaby on top of the central pole; reveals whole box | until it was the size of my thumb, standing on top of its own music box. |
| 95 | 162.55-163.62 | 1.07 | MS | eye | N | pan | 1.11x (+11%/s) | tiny Lullaby frozen mid-twirl beside a marionette | Frozen, mid-twirl. |
| 96 | 163.62-164.70 | 1.08 | MS | eye | N | push | 1.07x (+6%/s) | Dex sits up on the floor, Max beside | Dex sat up on the floor. |
| 97 | 164.70-165.75 | 1.05 | CU | profile | N | push | 1.14x (+14%/s) | Dex: 'Did I miss the math test?' | Did I miss the math test? |
| 98 | 165.75-168.05 | 2.30 | WS | low | W | near-static | 0.99x (-0%/s) | Max, Dex and kids walk out of the factory gate at night | We walked 42 kids home that night. And lullaby, |
| 99 | 168.05-169.15 | 1.10 | MS | eye | N | push 1.3x | 1.29x (+26%/s) | tiny Lullaby in an open music box on Max's shelf | it lives on my shelf now. |
| 100 | 169.15-171.90 | 2.75 | MS | high | N | slow push | 1.22x (+7%/s) | Max winds the box on his desk (frown decal) | Every night before bed, I wind it exactly one turn. |
| 101 | 171.90-173.05 | 1.15 | CU | eye | N | push | 1.20x (+17%/s) | figurine does one twirl (~0.6 s) | It does one little twirl. |
| 102 | 173.05-174.22 | 1.17 | MS | eye, frontal | N | push | 1.17x (+14%/s) | Max smiling, last frame | Honestly, it's kinda cute. |


### 1b. Shot statistics and patterns

**Counts**
- 102 shots in total, or 101 without the 4-frame flicker (#3).
- Median 1.53 s, mean 1.72 s, 34.8 cuts per minute.
- Longest shots:
  - #46, crank orbit: 5.20 s
  - #61, wall of music boxes: 4.10 s
  - #62, giant box: 4.00 s
  - #43, doll face: 3.65 s
  - #58, marionettes: 3.60 s
  - #94, shrink reveal: 3.52 s

  The long holds are reserved for the monster reveal and the lair reveal. Exposition such as the town rules runs at about 1.1-1.8 s per shot.
- **Motion:** 98 of 101 shots move (more than 4 %/s zoom, more than 40 px/s pan, or more than 2°/s roll).
  - 81 push in, 10 pull out.
  - 53 have a pan, tilt or truck of 40 px/s or more.
  - 34 have a slow roll of 2°/s or more, a Dutch drift, for example #13/#14 at about +11° over 1.5-2 s.
  - Truly static shots: only #15 (house lights), #57 (factory interior) and #85.

**Speed profile**
- Moves run at constant speed. Push rate per fifth of the shot:
  - #16: 15/17/18/17/18 %/s
  - #59: 17/18/19/20/19 %/s
  - #61: 21/20/21/21/17 %/s
- Shots start and end mid-move: these are linear tweens trimmed in the editor.

**Punch-ins on reveal words**
- #4 "it takes you": 1.9x in 0.6 s
- #7 "box song getting closer": 1.7x
- #8 "We call it Lullaby": 2.0x in 1.1 s, with a +13° roll
- #38 "head drooping": 1.8x
- #49 "toward me": 1.4x in 0.9 s
- #77 "remembered": 1.8x
- #81 "came around the corner": 2.0x in 1.3 s

**Special moves**
- **Intro (0-0.35 s):** an editor spin-zoom. The frame starts rolled about +18° at 1.47x scale, overshoots to about -7°, and settles at 0°/1.0x by about 22 frames, with ghosting on the first 2 frames (`VA/st_e.jpg`).
- **#23:** a whip-pan of about 2,400 px over about 0.7 s from the calendar to the bed (`VA/st_c.jpg`, row 1).
- **#86:** violent shake of ±70 px for 0.95 s on the screech (`VA/an_screech.jpg`).
- **#94:** pull-back plus crane-down with 0.22x scale, the "she shrank" reveal (`VA/an_shrink.jpg`).
- **#66:** a true top-down 90° view of the spinning platter.
- **#46:** an orbit of about 27° around her back.

**Composition**
- Subjects sit almost always on the vertical centre line. Faces are in the upper 25-45 % of the frame, above the caption line at about 69 %.
- Nothing important sits in the caption band (y 1260-1360). Inserts (#17 arm, #23 calendar, #36 clock, #55 clock face, #80 ballerina) cover concrete nouns.

**Repetition**
- The same set-ups come back to save builds:
  - Max's bed from a high 3/4 angle: #16, #20, #23 end, #26
  - Max frontal sitting/standing: #32, #33, #37, #38
  - The street with the crosswalk: #5, #29, #34, #40, #47
  - Behind Lullaby with the crank: #6, #46, #76
  - The giant box: #57, #62, #63, #85, #90, #92
- #13 and #14 are a mirrored pair (mom/blonde kid, then dad/red-haired kid, same framing and roll) to show "exact same".

**First 4.4 s (hook)**
- Three shots and the creature on screen from frame 0: walking wide, peering in the window, then the hand reaching for the glass with a 1.9x punch-in on "it takes you".
- **This video does not open with a title card or a black frame.**

---

## 2. Characters

### 2.1 Human avatars: R6 blocky Roblox

**Rig**
- Classic **R6**: head, torso and four limb blocks. No elbows or knees; limbs swing as rigid blocks.
  - `VA/an_rise.jpg`: the arms rise as straight bars.
  - `VA/an_pop.jpg`: the kids jump with arms up as bars.
- Measured on Max standing (`VA/f/t173.60.jpg`, `VA/grid_max.jpg`), where torso ≈ 500 px = 2 studs:
  - Head ≈ 300 px tall, 307 px wide: about 1.2 studs.
  - Torso ≈ 465 px wide.
  - Each arm ≈ 0.5x the torso width.
  - Legs: 2 studs, foreshortened in this frame.
- Proportions are classic R6: head 1.2, torso 2x2x1, arms and legs 1x2x1 studs. That is about 5.2 studs, or **4.3 heads tall**.
- Head: the classic rounded "Roblox head" (cylinder-like with rounded top edges), not a block. Hands are the plain ends of the arm blocks, in skin colour.

**Clothing**
- Clothing is **2D shirt/pants textures wrapped on the blocks**; seams are visible at the shoulders. There is no 3D layered clothing on the humans.
- Max's sweater:
  - Cream/lilac horizontal stripes with a drawn cable-knit pattern and ribbed cuffs.
  - Graded indoors to #c29fb5; at night to #7466dd-#7f75f2.
  - A small blue button-like dot at the neck in some shots.
- Max's pants: dark brown, with white-soled sneakers with red trim drawn on the leg bottoms (`VA/crop_shadows.jpg`, top right).
- Dex: a green dinosaur onesie.
  - A hood with 3D-looking white teeth (zigzag), googly eyes on top and an orange horn.
  - A beige knit belly patch, and white claw squares at the feet.
  - Probably hood accessory plus shirt/pants texture: `VA/f/t033.70.jpg`, `t121.30.jpg`.

**Hair and accessories**
- 3D accessory meshes: low-poly with flat facets.
  - Max: spiky messy orange-red hair (#c83604 to #b42605 indoors; #ad3808 / #6f0805 at night) that covers the top half of the head and eyebrows.
  - Grandpa: wild white "Einstein" hair plus a white beard accessory (#c6bcbb).
  - Mom: brown bob with a black headband.
  - Red-haired mom: big curly red hair with a white bow on the red dress.
  - Kids: black buns, blonde pigtails.
  - Dad: black curly top.
  - The kid with the pillow: big red curly hair.

**Skin**
- Max salmon: #e96e57 lit and #dd5d49 mid indoors; #983353 at night.
- Dex brown: #b7623e. Mom: very pale (graded to lavender-white).
- Dad and the sleepwalker kid: dark brown. The pajama kids: assorted tones.

**Faces: classic 2D decals, swapped and never animated**

Max's faces seen:

| Expression | Description | Frame / time |
|---|---|---|
| Asleep | closed `^ ^` eyes with lashes, small `o` mouth | `t028.00` |
| Startled | two black oval eyes, round black mouth with a red centre | `t037.60`, 37.8 s |
| Shocked | huge outlined mouth with white teeth, one brow raised | `t038.20` |
| Squeezed shut | `)(` style eyes, with a lip curve | `t039.20` |
| Smirk | one raised brow, one half-lid, side smile | `t050.30` |
| Frown | brows down, `︵` mouth | `t047.00`, `t082.50`, `t170.50` |
| Horrified | huge eyes, crazed brows, open grimace with teeth and tongue | `t122.70` |
| Open smile | used for the ending | `t173.60` |

How the faces behave:
- Swaps happen on the beat word. The eyes-open swap lands at 37.80 s, exactly on "Tink" (37.79); the swap to "went still" happens at the start of #25.
- No blinking was found anywhere. No lip movement on Max, since the narrator is off-screen.
- The only "lip-sync" is the mom in #13: two mouth decals (open smile / closed smile) alternate about every 0.3 s while she "sings" (`VA/an_mom.jpg`).
- Dad's face (#14) is a static grimace decal.

**Continuity cheats**
- Dex's face is a dot-eyes `o` mouth in his bedroom (#22) but a lashes-and-smile decal on the peg (#68), to show he is dazed.
- Max's mom is red-haired in #19, but the "every parent" mom in #13 is a different avatar.
- Otherwise Max is identical in every shot: same hair mesh, sweater and pants. That is what makes the hero readable at 1.5 s per shot.

### 2.2 The monster "Lullaby": custom mesh, about 2.4x Max's height

Evidence:
- `VA/f/t010.30`, `t061.60`, `t068.00`, `t074.00`, `t081.30`, `t065.00`, `t149.40`, `t124.60`
- `VA/an_head.jpg`, `VA/grid_lul.jpg`

**Silhouette**
- Very tall and thin, about 5.2 heads tall. In the profile at `t061.60`:
  - head ≈ 220 px of a 1,150 px figure
  - neck pole ≈ 40 px
  - the dress reaches the ground and hides the legs
- Scale: about 12-13 studs against Max's 5.2 studs. The scale is cheated per shot; at the window she bends down to a ground-floor window.

**Head**
- A sculpted vintage porcelain doll head:
  - Bald, slightly elongated cranium, small sculpted ears, a moulded nose bump and puffy baby cheeks.
  - A tiny puckered mouth with red lips (#970826 / #8e0528) and a hint of teeth, plus a red drip "blood" smear from the mouth corner.
- Eyes: deep **hollow black sockets** (#010011) with a brown inner rim and a specular glint. They are not drawn eyes.
- Pink round cheek **blush** (soft radial gradient; mean #a55a70 after the grade, centre lighter).
- A long black **crack** from the crown across the forehead, plus a few small cracks and dirt specks.
- **Glossy**: a clear specular highlight on the forehead and cheeks (porcelain or clearcoat look). Forehead graded #aaa4e6 (lit) and #6c59c6 (mid), highlight #bcb8f1.
- **Head held tilted about 20-30°** most of the time ("like it was listening").

**Neck and body**
- A thin white cylinder neck, clearly visible, about 0.4 of the head width.
- A ruffled, pleated knit collar.
- A bodice with puff shoulders, all off-white fabric with a fine knit texture.

**Dress**
- A floor-length Victorian **nightgown** with deep vertical **pleats** (about 20-30 folds around).
- The hem is ragged and dirty: brown/rust stains rising about 10-15 % of the dress height, a few dark holes, dragging on the road (`t009.00`, `t065.00`).

**Arms and hands**
- Long thin white sleeves with ragged grey fringe cuffs.
- Visible forearms are bare white jointed rods: a **marionette** construction of cylinder segments with ball joints.
- Hands: **skeletal puppet fingers**, 4 plus a thumb, each about as long as the palm-to-wrist length or longer, 3 segments each with spherical knuckles (`t071.00`, `t072.10`, `an_reach.jpg`).
- The arms bend at the elbows: this is an R15-like custom rig, unlike the R6 humans.

**Crank**
- A rusty iron **crank** through the middle of the back: a horizontal shaft plus a bent L lever with a bulbous wooden-looking handle.
- Colours: orange-rust #9b2b0b / #7f1608 to #a86e3b highlights; graded #7a4a5d on the dark side.
- It turns by itself, about 1 revolution per 1-1.5 s.

**Music notes**
- White semi-transparent quaver and beamed-note sprites float out of it: lavender-white #cdc9ec to #cbc8f8, alpha about 0.8-0.9.

**Cute vs creepy**
- Creepy from the hollow eyes, the crack, the blood drip and the stained hem.
- Cute from the baby-doll cheeks and blush, the small size of the mouth and the pastel grade.
- The finale turns it into a cute figurine.
- Stylisation: semi-realistic sculpt and fabric inside a blocky Roblox world. The contrast is the point.

### 2.3 Secondary characters and props

**Toy characters**
- **Kids on pegs:** R6 kids at about 0.3-0.5 m scale on brass pegs, both arms up in a dancer pose.
  - Pastel pyjama textures: pink, lilac #8744a4, sky blue #9095e1, mint, peach.
  - Different hair accessories. Each spins on its peg while the platter turns about 19°/s.
- **Marionettes:**
  - Toy-soldier style puppets in a red jacket and blue shorts, with a black/brown cap, rosy painted cheeks and wooden-doll faces. These are not Roblox avatars.
  - They hang from 3-5 thin white strings going up into darkness, and sway slowly.
- **Teddy bears:** realistic plush teddy meshes in orange-brown fur (a fur texture graded to #6b2112-#914536), black button eyes and nose, sitting in identical rows. They are clearly a higher-detail asset than the avatars.
- **Sheep (#22):** a fluffy white cloud-wool body with a black face and legs. It hops a tiny pink picket fence in a loop.
- **Ballerina figurine (flashback):** a pink tutu, a white body and a hood/veil, spinning on a peg in a wooden music box. The box has a blue lid mirror, teal velvet and a brass weight ball.

**Scale ladder** (Max = 1.0)
- Lullaby ≈ 2.4
- Marionettes ≈ 0.6-0.8
- Teddies ≈ 0.4
- Giant music box: about 6x Max's width
- Pegged kids ≈ 0.12-0.15
- Shrunken Lullaby: thumb size, ≈ 0.08-0.1

---

## 3. Animation

**Overall**
- Keyframed Roblox animation in the style of Moon Animator: linear or simple ease in-out tweens and pose-to-pose holds.
- No squash and stretch, and almost no overlap or secondary motion. Hair and clothes are rigid; only the dress hem and notes add life.
- Duplicated frames give an effective rate of about 37 fps (60 fps container).
- How much moves: 36 % of shots are frozen tableaux where only the camera pushes, for example #9-#11, #14, #16-#21, #24-#26, #31-#33, #55, #57, #60, #77-#80, #99-#100. Animation is spent on the creature and on action beats.

**Max sleepwalk** (`VA/an_walk2.jpg`, 81.8-83.0 s)
- **Arms held straight forward and level**: the zombie pose.
- Head pitched down about 20-30° ("head drooping").
- A small R6 leg swing, about ±15°.
- Slow forward travel with a slight bob.
- The face decal changes twice in 1.2 s: `o`, then frown, then `o`.

**Max rise** (#37, `VA/an_rise.jpg`)
- He sits on the edge of the bed, both arms rise to horizontal over about 0.5 s, then he stands and walks.
- The rise holds about 0.3 s per pose.

**Run, lunge, dive** (#72-#74, `VA/an_run.jpg`)
- A fast R6 run (limbs ±45°).
- A crouch and lunge, then a belly-flop dive flat on the floor in about 0.3 s, then still.

**Jump on the back** (#82-#83, `VA/an_jump.jpg`)
- A jump arc, then he clings to her back with both arms on the crank.
- Turning backwards: the crank lever spins fast, with notes bursting.

**Lullaby**
- **Locomotion:** a glide with no visible steps. The dress hides any legs. Slight lateral sway, arms hanging slightly away from the body with a small swing; slow, about 1-1.5 studs per second (`VA/an_walk1.jpg`).
- **Head turn** (#48, `VA/an_head.jpg`):
  - The head yaws a full 180° on the neck in about 0.8 s (79.9 to 80.7 s) with ease in-out, then holds.
  - The cut comes 0.1 s after the turn ends, to a lower, closer angle with a push-in.
- **Reach** (#4, `VA/an_reach.jpg`): the hand rises from waist to glass in about 0.45 s with the fingers fanning open, then holds against the glass.
- **Point** (#70-#71, `VA/an_point.jpg`): she leans in over the box with one arm extended and the index finger pointing down, holds for about 2 s, then the next shot turns her to point at the camera.
- **Fingers** (#44-#45): they curl and uncurl; the closed fist opens into a spread hand.
- **Screech** (#86): the head jerks side to side every 3-5 frames combined with the camera shake.
- **Flail** (#84, #87): both arms rise into a T or V, with small jitter.
- **Crank:** continuous rotation of the lever around the shaft.
- **Notes:** emitted in bursts on "tink" words.

**Small figures**
- **Kids:** each pegged kid spins around its own vertical axis (arms up) while the platter rotates.
- **Pop-off** (#91-#92): kids launch up and forward off the pegs with arms up (R6 jump pose), drop to the floor, and stand with arms up or out (`VA/an_pop.jpg`).
- **Shrink:** not animated as a scale tween on screen. It is sold by a cut to a tiny figure plus a pull-back and crane-down (#93-#94).
- **Twirl** (#101, `VA/an_twirl.jpg`): one full 360° spin in about 0.6 s, then stop. The figure keeps both arms up.

**Idle and loops**
- Idle is mostly perfectly still.
- Dex (#22) has small head tilts and turns of about ±10° over about 1 s, and the sheep hops in a loop of about 1 s (`VA/an_dex.jpg`).
- The hammering dad loops a swing every ~0.55 s (33 frames) with grey dust puffs (`VA/an_dad.jpg`).
- Window lights switch off one by one, instantly (#15: 21.8 s, 21.9 s, 22.47 s; `VA/an_lights.jpg`).
- The giant box's panel lights switch on in one frame at 153.00 s ("started to grow", `VA/st_f.jpg`).

**Prop interaction**
- Hands simply overlap props, with no finger posing for the humans: the hammer, the crank grab, and the winding key in #100.
- The crank is the one prop that is "driven" (rotation linked).

---

## 4. Environments

All the sets are Roblox builds. They are made from parts (blocks, wedges and cylinders) with **no studs**, using Roblox materials: SmoothPlastic, Fabric, Wood, WoodPlanks, Brick, Grass, Concrete/Pavement, Asphalt, Neon and Glass. Toolbox meshes are used for the trees, teddies, sheep and cars. Detail density is high for Roblox.

| Location | Shots | Build and props | Materials and colours (graded) |
|---|---|---|---|
| **Night suburb street** | 1, 5-10, 29, 34-35, 40-54 | A 2-lane asphalt road with a yellow dashed centre line and **white zebra crossings**, concrete sidewalks with curbs, and grass lawns. Small single-storey houses: brick or siding walls in cream, blue or red brick; dark shingle roofs; porches with white railings; maroon shutters; mailboxes; window boxes with flowers; warm lit windows. Black single-arm **streetlamps** with small warm bulbs. Dark pine trees and leafy trees (realistic meshes). A playground (green slides, yellow frame) behind a white picket fence. A white sedan. Signs on black posts: "TOWN LAW / BEDTIME / LIGHTS OUT 8:00 PM / NO EXCEPTIONS" and "NOTICE / SLEEPOVERS ARE BANNED / by order of the town". | Sky **#000000**, no stars. Road #0d0928-#302951. Sidewalk #312b58. Grass #22351e-#2d2b38 (dark olive). House siding blue #181b7e-#2f3296. Zebra stripes #6f5db3-#8781cb. Lit window #d3d9a7. Trees #252a15 |
| **Max's bedroom** (also the ending) | 2, 16-20, 23-28, 32-33, 36-38, 99-102 | A pink/peach flat wall (SmoothPlastic). A dark-wood bed (wood grain) with a white knit pillow and a **navy knit blanket** (Fabric). A wood-plank floor. A window with a white frame, **translucent navy curtains** (Glass/transparency) and a night street visible outside. A nightstand with a **red LED alarm clock "12:00"** (7-segment pixel font). A wall calendar ("OCTOBER", 24 circled in red, "MATH TEST!" in red marker). A desk and shelf with a Rubik's cube and books (ending). | Wall #a16a63 / #9b6461, perfectly uniform with no gradient. Wood #430806. Floor #652211. Pillow and sheets #ccaac2. Blanket graded #caa7c4 in the lit areas |
| Window shots (#2-#4, #27-#28) | | The camera is inside, looking up and out through a white-framed window. The interior wall is pale blue (#5c7ca2 mid) in #2. | |
| Other homes | 11-14, 19, 21-22, 31 | **Closet:** white wall, hanging clothes as coloured fabric blocks (red, blue, yellow, green, purple), blue carpet. **Dad's window** from outside: brown boards and a brown-sphere garland along the sill. **Kids' beds:** purple, or red with white knit. **Dex's room:** green wall (day) and a grey wall, with a green blanket. | |
| **Daylight exterior** | 30 | The same house kit in daylight: yellow siding, green door, red shutters, porch, pines. **Bright Roblox default sky: a gradient from #55b1d9 (horizon) to #258edf / #3098de (top)**, with no clouds. | Whites #f2e0c1 (warm) |
| **Factory exterior** | 53-55, 98 | A tall red-brick building (Brick material with a clear mortar grid), a **clock tower** with a big white clock face at 12, and a dark sign with gold border reading "TICK & TUNE TOY CO. / EST. 1826 · MUSIC BOXES & FINE TOYS" (serif caps). Black iron fence and gate, streetlamps along a curved road, a **big full moon** (white disc, faint craters) beside the tower. | Brick #280f23-#291730. Moon #e9f6ff. Clock face #7666b1 |
| **Factory interior (lair)** | 56-97 | A huge dark hall. **Walls of shelves stacked with thousands of tiny open music boxes** (brown box, blue lid: an instanced pattern). Brick walls and dark wood floor planks. **Marionettes** hanging on strings from the black ceiling. **Conveyor belts** (dark blue) carrying long rows of identical **teddy bears**, all facing the door. Diagonal **light shafts** (semi-transparent lavender planes with a window-grid pattern, i.e. fake god rays) from high windows. A steel truss in the ceiling. **The giant music box** in the middle: a polygonal carousel base with lit lavender-white panels in brown/gold wooden frames, a ring of glowing bulbs (Neon spheres), a **huge round mirror lid** (purple #3b2b83 with brown rim and crack lines), a navy velvet top (#02002d), mushroom-shaped **brass pegs** and a central brass pole with a ball finial (#6a2606 / #9c540a highlights). | Mean #392039. Bulbs clip to #fff2fb with warm halo. Lit panels #e3c8f1 after the lights-on cue |
| **Flashback bedroom** | 78-80 | A warm daytime room: beige/tan wall, a window with a blue curtain and daylight street outside, an armchair and quilt in brown knit patterns, a wooden music box with brass corners. Little Max (orange hair) lies in a small bed. | Warm: mean #634c42, whites #cbbeba, R:G:B 1.30:1:0.86 |

**Level of detail**
- Exteriors are dense mid-ground kits.
- Backgrounds fall off to **pure black** at a modest distance, both the sky and the far interior. This produces the void/liminal look; no horizon is visible at night.
- No terrain hills and no water. Grass is the Roblox Grass texture (fine noisy blades).

**Signage text**
- Clean geometric sans (Montserrat-like) in black, with the headers in red.
- The calendar uses the same sans plus a red marker hand-font.
- The clock uses a red pixel 7-segment font.

---

## 5. Lighting and colour

**General recipe** (every scene)
- **No cast shadows.** Checked under Lullaby on the zebra crossing, under the kids on the floor and under Max's shoes (`VA/crop_shadows.jpg`).
- Lighting is mostly ambient/hemispheric with a soft directional key from the upper front, so the faces of blocks differ only gently. The top faces are a bit lighter.
- Flat walls are **perfectly uniform**: for example, 116/255 everywhere on the bedroom wall (`VA/f/t168.60`). There are no point-light falloff gradients on the walls.
- Practicals:
  - **Neon emissive** parts: bulbs, lit windows, the moon, the LED clock.
  - Speculars on glossy items: the doll head, brass balls, the sneakers.
- No visible AO, except slight darkening in deep corners. No fog colour other than **falloff to black**.

**Per-scene measurements**
- Script: per-group statistics over the full-resolution stills, with the caption band removed.
- R:G:B is the mean-channel ratio normalised to G. "Whites" is the mean of the top 0.5 % of pixels. "Crushed" is the share of pixels with L < 4/255.

| Scene | Time of day and key | Mean colour | Median L | Whites | R:G:B | Crushed | Sat |
|---|---|---|---|---|---|---|---|
| Night exterior | Night: lavender-blue ambient, soft key from upper front, warm lamp and window practicals, moon | #2f284b | 22 | #d8d9f4 | 1.16:1:**1.86** | 27 % | 0.43 |
| Max's bedroom | Night interior, but reads as warm rose: even ambient, no visible lamp | #894f55 | 109 | #ddbdd5 | **1.73**:1:1.07 | 1.4 % | 0.57 |
| Parents' bedsides (#13-14) | Violet/blue | #734f9b | 79 | #c9ccfd | 1.46:1:1.95 | 5 % | 0.62 |
| Factory | Dark magenta-plum ambient, lavender shafts from above, warm Neon bulbs as practicals | #392039 | 19 | #f0d9f8 | 1.78:1:1.78 | **36 %** | 0.56 |
| Day exterior / Dex's room | Neutral-warm sun, blue sky | #687762 | 110 | #f2e0c1 | 0.88:1:0.82 | 0 % | 0.53 |
| Flashback | Warm, slightly desaturated sepia | #634c42 | 65 | #cbbeba | 1.30:1:0.86 | 2.6 % | 0.62 |

**Named swatches** (pixel samples; `VA/palettes.txt` and `VA/colorstats.txt` hold all 98 stills)
- **Night**
  - Lullaby face: #6c59c6 mid, #9185d9 light, #bcb8f1 highlight.
  - Dress: #b6aee5 lit, #6f597d in the folds.
  - Notes: #cdc9ec.
  - Max at night: sweater #7466dd, skin #983353, hair #ad3808.
  - Shadows #0e0a2a-#11102c. Black #000000.
- **Bedroom**
  - Shadows #310101-#3c0605 (deep maroon, never neutral grey).
  - Skin #e96e57 / #dd5d49; hair #cc3905 / #b42605.
  - White knit #ccaac2 / #bc99b3; wall #a16a63; wood #430806 / #652211.
- **Factory**
  - Black #000000 / #090104; mids #1f010d, #27050f, #3e1737; shafts #594c96.
  - Lullaby #765198-#9979b8; Max's sweater #8c69c4; Max's skin #a72618.
  - Bulb core #fceff3. Brass #6c2805. Platter #02002d.
- **Day:** sky #258edf / #55b1d9; siding #cdb376 / #c1a76d; pavement #645943; pines #34422a.

**How night is shown**
- Not by darkness alone, but by a **strong blue-violet cast on everything that is lit**: whites become lavender, greens become olive-black, reds become maroon. The sky and distance are a pure black void.
- Exterior mids stay dark (median L ≈ 22), while the subject (Lullaby's white dress and face) is the brightest thing in frame. She glows against the black.

**Interiors**
- Pushed the other way: rose/magenta (R 1.73x G).
- Blacks are deep maroon, so even "safe" home scenes feel feverish and dreamlike.

**The "dream" recipe here, exactly**
1. Shadowless, ambient-dominant lighting.
2. A **per-location monochrome tint**: violet at night, rose indoors, plum in the lair. It is applied as a white-point shift: the highlights of white objects land at #d8d9f4 / #ddbdd5 / #f0d9f8, not #ffffff.
3. Crushed blacks with a black void background.
4. Saturation of 0.43-0.62 mean in the mid-tones, with no pastel washout.
5. Small **bloom** only on emissives.
6. Slow constant push-ins.

There is **no** film grain, vignette, chromatic aberration, DOF blur, haze or light leaks. "Liminal" comes from empty streets, flat light and black voids, not from effects.

---

## 6. Post effects and transitions

**Bloom**
- Only on emissive near-white sources:
  - the bulbs on the giant box (`VA/crop_bulbs.jpg`)
  - the moon (`VA/crop_moon.jpg`)
  - lit windows and streetlamp bulbs
- Measured on a bulb (`t124.60`): the core clips at (255, 242, 252). The halo falls from 131 to about 13 over **about 25-30 px** at 1080 width, and it is warm (orange).
- Moon: core (233, 246, 255); halo about 25 px, blue-lavender.
- In Three.js terms this is a high threshold (about 0.85-0.9 linear), strength about 0.5-0.7, and a small-to-medium radius (UnrealBloom radius about 0.3-0.4 at 1080x1920).

**Not present** (checked)
- **Depth of field:** none. Backgrounds behind close-ups stay as sharp as the compression allows (`VA/crop_dof.jpg`).
- **Vignette:** none. Flat walls measure exactly 116 everywhere from the edge to the centre (`t168.60`), and 119 everywhere for the pale-blue wall in `t002.80`.
- **Chromatic aberration, colour fringes, lens distortion:** none. The moon's edge goes from (74, 84, 111) to (244, 255, 255) with no RGB offset.
- **Grain or noise:** none. Flat areas have 0-1 standard deviation.
- **Motion blur:** none in-engine. The 2-frame ghosting at 0.00-0.03 s belongs to the intro transition.
- **Overlays, light leaks, scanlines, letterbox:** none.

**Particles**
- **Music notes**, the only recurring particle: 2D quaver and beamed-note sprites.
  - Lavender-white (#cdc9ec), alpha about 0.85, 40-150 px tall at 1080 w.
  - They spawn from the crank, drift upward and outward with slight rotation, live about 1-1.5 s and fade.
  - 3-15 are visible at once; bursts sit on "tink" words and swirl during the reverse crank (#85).
- **Dust puffs** at the boarded window (grey-white smoke sprites).
- **Drool bubble**: a translucent sphere.
- No sparkles, stars or fireflies.

**Transitions**
- **100 hard cuts.**
- An **intro spin-zoom** on the first 0.35 s: roll +18° → -7° → 0° and scale 1.47 → 1.0, eased, with 2 frames of ghosting.
- A **4-frame flicker** at 3.700-3.767 s: the same frame re-graded darker and bluer, mean RGB (93, 107, 159) → (71, 79, 147). It may be a deliberate "dip" before the hand-reach punch-in.
- **In-shot lighting cues** used as transitions: the house windows going dark (#15) and the box lights coming on (#90 at 153.00 s).
- A whip-pan inside #23.
- **No** fade to or from black, no white flash, no zoom transition between shots.

**Speed ramps and freeze frames**
- No speed ramps found.
- #15, #34 and #57 contain 12-30-frame stretches with no change in the picture. These are near-still shots with very slow push, not true freezes.

---

## 7. Text and captions (burned in)

**Style**
- **One word at a time**, all 707 words. Mostly lowercase, with auto-caption-style **inconsistent** capitals:
  - "Max", "Dex" and "I" are always capitalised.
  - "Lullaby" is capitalised at 51.5 s and 123.2 s, but lowercase at 10.15 s, 148.9 s and 167.7 s.
  - "Dinosaur" is capitalised and "Tink" is capitalised at the start of a sentence.
- Numbers are shown as digits: "10", "100", "42".
- **Font:** **Verdana Bold** (or Tahoma Bold). Evidence: the x-height/ascender ratio is 49/68 = 0.72, and the 'l' stem is 15 px wide at about 90 px size (`VA/cap_crop.png`, `VA/cap_zoom.png`).
- **Size:** ascender height 68 px; the 'l' runs from the top at 1267 to the baseline at 1334. That is a font size of about 90 px at 1080 wide.
- **Colour:** pure white #FEFFFF, untouched by the grade. **No speaker colours** (checked on the grandpa lines and Dex's line, `VA/cap_colors.jpg`).
- **Stroke:** black, about 6-7 px.
- **Shadow:** a soft black drop shadow offset about 4 px down and right, blur about 10 px, opacity about 0.6. It is visible as a 10-12 px gradient on light backgrounds (`t122.70`).

**Position**
- Horizontally centred at x = 540.
- **Baseline fixed at y ≈ 1335.** Tops sit at 1267, descenders reach 1352, so the band runs from 69.5 % to 70.4 % of the height.
- No background box.

**Timing**
- Each word appears at its spoken onset: a median of **-20 ms** relative to the ASR onset, IQR -50 to +10 ms (704 of 707 words matched).
- It stays on screen until the next word, so there are no gaps and no multi-word lines.

**Animation**
- Effectively none: a hard swap.
- The 1-2 frames at a swap sometimes show the new word horizontally narrower or wider by about 10-20 % at constant height (`VA/cap_trans.png`). There is no visible scale pop at normal speed.

---

## 8. Editing and sound-picture sync

**Picture-on-word rule**
- Every cut is locked to a word onset: median -40 ms, with 80 % of cuts within -120 to +33 ms.
- The new picture is the literal illustration of the word that starts right after the cut:

| Time | Word | New picture |
|---|---|---|
| 8.40 | "box" | the hem |
| 12.57 | "Sleepovers" | the sign |
| 13.67 | "Some kids" | the closet |
| 18.27 | "kids" | the second kid |
| 35.28 | "Then one night" | the calendar |
| 54.75 | "So at midnight" | the clock 12:00 |
| 62.12 | "feet tall" | the tilt-up |
| 72.10 | "puppet's" | the finger insert |
| 90.00 | "that closed a hundred years ago" | the clock face |
| 101.75 | "The walls" | the walls of shelves |
| 120.48 | "And right in front was Dex" | Dex |
| 136.65 | "(grandpa's old music) box" | the warm flashback, 0.4 s before "Here's the thing…" |
| 148.95 | "Lullaby screeched" | the screech close-up |
| 169.15 | "Every night" | Max winding |

- The image therefore appears 2-3 frames before the word: it never lags.

**Beats inside shots are word-locked too**
- 37.80 s: eyes-open decal swap on "Tink" (37.79).
- 21.8-22.5 s: windows going dark across "music box, be asleep".
- 153.00 s: box lights on, on "started" (153.49) / "spinning".
- 79.9-80.7 s: the head turn under "head turned all the way around".

**Other edit devices**
- Punch-ins on reveal phrases: see §1b.
- No freeze frames, no speed ramps, no split screens, no on-screen graphics other than captions and in-world signs.

**Sound** (from mid/side spectrograms: `VA/spec_mid.png`, `VA/spec_side.png`, `VA/spec_zoom.png`)
- **Voice:** a single narrator at about -20 dBFS RMS, centre (L/R correlation 0.96), continuous from 0.0 to 173.9 s. The longest pauses are under 0.6 s.
- **Music** (the owner will replace this): present throughout.
  - 0-4.4 s: a sustained tonal drone of about 500-600 Hz plus regular soft ticks. It ends exactly at the 4.38 s cut.
  - From about 23 s (the "My name is Max" section) a wider stereo bed enters: the side channel rises from -50..-57 dB to -36..-41 dB.
  - Music-box-like high tones are woven in.
- **SFX heard, with times:**

| Time (s) | Sound | What it covers | Sync |
|---|---|---|---|
| 7.3-8.4 | music-box tines, 1.7-1.9 kHz | "tiny tinkling music box" | |
| 37.5-38.1 | music-box "tinks" | "Tink, tink" | the eyes-open swap |
| 73.5-74.4, 76.5 | tines | the crank shot and "Tink, tink, tink" | |
| 91.2-92.8 | door creak (dense periodic clicks) | "creaked open" | starts about 0.2 s after the cut to the doorway |
| 117-120 | tines, plus a broadband swell in the side channel at 118-120.5 | "twirling around and around, forever" | |
| ~130.8 | thud transient | | Max's dive landing |
| 146.5-148.4 | sustained music-box melody | "played in reverse, knit, knit, knit" | |
| **148.95-150.8** | **broadband screech** | the screech | **starts on the cut** to the screaming face (148.95), 0.5 s before the word "screeched" |
| 172.1-172.7 | a bright tine at 3.97 kHz | "one little twirl" | the figurine's spin |

- No whooshes on cuts were found. The high-frequency bursts near cuts are the narrator's sibilants ("see", "Sleepovers", "Some", "So", "shrunk").
- The SFX layer is sparse and literal: one sound per illustrated noise word.

---

## 9. What makes it look premium, ranked, and how to get each in Three.js

| Rank | Premium factor | Evidence | Three.js approach (SwiftShader-friendly) |
|---|---|---|---|
| 1 | **Word-locked, literal cutting** at about 35 cuts/min: every noun gets its own picture 2-3 frames before the word | §1b, §8 | Drive the timeline from ASR word times. Place cuts at `word.t - 0.04 s` and start each shot on the word that names it. Target a median shot of 1.5 s and ≤ 2.6 s for exposition; allow 3.5-5 s only for reveals. |
| 2 | **A camera that never stops**: constant-speed push-ins of about +15 %/s (1.2-1.3x per shot), punch-ins of 1.6-2.0x on reveals, slow 5-10° roll drifts, one orbit, one whip, one shake | §1b | Use a per-shot camera rig with `start` and `end` (position, target, fov, roll) and **linear** interpolation, cut mid-move. Prefer a real dolly (move the camera along the view vector) over FOV, so near and far objects show parallax. Use about 0.5-1 % per frame at 60 fps. Shake: random walk of about ±70 px for 1 s, re-randomised every 3-4 frames. |
| 3 | **Bold per-location colour grade** with crushed blacks and tinted whites | §5 tables | Use one `ShaderPass` after rendering: `c = max(c - lift, 0)/(1 - lift)` with lift ≈ 0.03-0.05; then `c = pow(c, gamma 1.1)`; then `c *= tint` (night ≈ (0.85, 0.85, 1.0), whites → #d8d9f4; bedroom ≈ (1.0, 0.75, 0.87); factory ≈ (1.0, 0.72, 1.0)); then saturation ×1.15. Fit it with a QA script: render a test frame and compare mean / white / R:G:B / crushed % with the §5 table. Clear colour #000000 and fog to black (`scene.fog = new THREE.Fog(0x000000, near, far)`) for the void. |
| 4 | **A hero creature with real sculpt and gloss** among blocky avatars | §2.2 | **Head:** `SphereGeometry(1, 64, 48)` deformed in a vertex function (elongate the cranium, cheek bulges, nose bump, chin), with `MeshPhysicalMaterial` (roughness 0.25, clearcoat 1). Eye sockets: dark inset spheres (#05010f) with a tiny glint. Blush, crack and lip drip come from a `CanvasTexture`. **Neck:** a thin cylinder. **Dress:** `LatheGeometry` with pleats (r(θ) = r0·(1 + 0.06·sin(26θ))) and a noisy hem, a canvas texture with a rust-stain gradient on the bottom 15 % and a fine knit noise. **Arms:** a chain of cylinders with sphere joints. **Fingers:** 3 segments × 5, 1.2x the palm length. **Crank:** a tube or torus elbow plus a capsule handle, rust-orange (#a0461a base). |
| 5 | **Shadowless, readable lighting** with glowing practicals | §5, §6 | `HemisphereLight` (sky lavender #8f86ff, ground #1a1030, intensity about 1.2) plus one soft `DirectionalLight` from the upper front, **no shadow maps** (also the cheapest option on SwiftShader). Neon: `MeshBasicMaterial` in white/warm. `UnrealBloomPass` (threshold 0.85, strength 0.6, radius 0.35), possibly at half resolution for speed. Light shafts: additive transparent planes with a canvas grid texture at opacity about 0.25. |
| 6 | **Dense, textured sets** (thousands of music boxes, teddy rows, street furniture) using Roblox-like materials | §4 | Use `InstancedMesh` for the shelves of boxes, the teddies, the pegs, the kids and the bulbs. Generate procedural `CanvasTexture`s: brick with mortar (40×20 px cells), wood planks with grain, knit (cable pattern), grass noise, asphalt noise, zebra stripes. Use `MeshStandardMaterial` with roughness 0.8-0.9 and metalness 0 everywhere, except brass (metalness 0.6, roughness 0.35). |
| 7 | **Expression decals timed to words** | §2.1 | Draw a face atlas on a canvas (asleep, `o`, shocked with teeth, squeezed, smirk, frown, horrified, smile) and map it on a curved plane hugging the front of the head. Swap the texture on the word. No blinking, no tweening. |
| 8 | **Recurring motif particles** (notes) tied to the SFX | §6 | Use a `Sprite` pool with a canvas-drawn ♪/♫, colour #e8e4ff (it lands at about #cdc9ec after the grade), opacity 0.85, size 0.3-0.9 m, and velocity up/out at 0.5-1 m/s with spin. Emit bursts on "tink" words. |
| 9 | **One-word captions** (the owner can add these in CapCut instead) | §7 | Verdana Bold 90 px, white, 6-7 px black stroke, shadow (4, 4) blur 10 at 60 %, baseline y = 1335, centred, hard swap at the word onset. |
| 10 | **Clean 60 fps motion**: the reference is actually about 37 unique fps with judder | §0 | Rendering every frame at 60 fps already beats the reference. Keep animation tweens frame-rate independent. |

**What reads as cheap in the reference** (copy it, or improve on it where cheap)
- Stiff R6 limb swings; the sleepwalk is just arms out.
- No contact shadows, so characters float slightly.
- Frame duplication judder.
- Face-decal continuity slips (Dex).
- Scale cheats on Lullaby.
- The 4-frame flicker.
- Compression mush (real detail is about 540-720p).

Copy the R6 stiffness and the decal faces, because they are the "Roblox" identity. We can improve on smoothness and sharpness for free.

**Hardest parts to reproduce, with the best approximation for each**
1. **The porcelain doll head:** a sculpted, organic mesh. Use a displaced-sphere approach (cheeks, brow ridge, nose and chin as Gaussian bumps), clearcoat gloss and canvas-painted features. Check it against `VA/f/t081.30.jpg` and `t068.00.jpg`.
2. **The fabric dress folds:** pleated lathe plus vertex noise plus a hem stain texture. Avoid cloth simulation.
3. **The teddy-bear and sheep plush look:** stack spheres and ellipsoids with a high-roughness fur-noise canvas texture and small normal noise. It reads at 1-2 s cuts.
4. **The "Roblox materials" feel:** procedural canvas textures (knit, brick, planks, grass) at 256-512 px with `RepeatWrapping`. A subtle normal-map bump is optional.
5. **The grade:** one LUT-like shader per location, tuned against the §5 numbers with a pixel-statistics QA script.
6. **The camera language:** simple, because it is linear tweens. The labour is in placing about 100 set-ups.

