# Visual analysis: "The Tooth Fairies Project" (reference r4, the owner's favourite)

Reference only: we copy the **look, construction and grammar**, not the characters, plot or lines.

- **Source:** `ref60/tooth_fairies.mp4`, the full upload. It is 1080x1920, 60 fps, 131.53 s, h264 at 1.75 Mb/s, with AAC 44.1 kHz audio. This copy has picture from frame 0, so the old trimmed copy's 1.27 s gap is gone.
- **Evidence folder:** `$TFV` = `/tmp/claude-0/-home-user-claude-todo-demo/353ac1d9-152b-55bb-bdf1-0625e0fc6a83/scratchpad/rbx/tfv`. It sits in scratch and is not in the repo, because the frames are copyrighted.
  - `sh/tf_1..4.jpg`: 1-s frame sheets.
  - `s/shots_01..10.jpg`: first, middle and last frame of every shot.
  - `s/m_*.jpg`: 60-fps frame strips around moves and gestures.
  - `full/t_<sec>.jpg`: 113 full-resolution mid-shot frames.
  - `s/spec_*.png`: spectrograms of the music and SFX stem.
  - Measurement scripts: `diff.py` (cuts), `motion.py` (camera similarity transform per frame, optical flow), `resid.py` (subject motion after camera compensation), `capscan.py` (caption band per frame), `colstats.py` (palette), `shots_final.json`, `cuts_final.json`.
  - Word timings: `asr_tf.json`, a new ASR run of this full copy (570 words).
- **Method:** frames were viewed in sheets, strips and full-resolution crops; I looked at about 300 individual frames.
  - Every number below was measured. Cuts come from per-frame difference. Camera moves come from LK optical flow plus a RANSAC similarity fit. Colours are pixel and k-means samples.
  - Captions were measured on every frame against the ASR word onsets. Audio was split into voice and music with UVR-MDX.

## 0. The 15 facts that matter most

1. **It is made in Roblox Studio and screen-captured.**
   - Signs: R6 blocky avatars with catalog 2D decal faces, UGC hats and hair, and Roblox materials (Fabric wallpaper, Wood, Brick, Grass, Glacier/Ice).
   - Also Roblox Sparkles particles, Roblox skyboxes (galaxy, cloudy day) and a low-poly terrain mountain.
   - On top of that sit high-poly sculpted creature meshes (marketplace or UGC, with PBR textures).
2. **The picture has 40 unique frames per second inside a 60 fps file.**
   - Every third frame repeats in moving footage. The most common gap between duplicates is 3 frames.
   - Captions change on any of the 60 frames, so they were added in the editor. Camera moves follow the 40-fps cadence, so they were recorded in the engine.
   - **Our true 60 fps will be smoother than the reference.** That is fine and should not be copied down.
3. **Real detail is about 540-720p.** Downscaling to 540x960 and back loses almost nothing: PSNR is 40-45 dB.
4. **Fast, word-locked cutting.**
   - 113 cuts give 114 shots in 131.5 s, which is **51.5 cuts per minute**.
   - Shots: **median 1.12 s, mean 1.16 s**, range 0.17-2.28 s. Excluded from these stats is one 2-frame stray flash.
   - **60 of 63 sentences start on a cut**, within ±0.15 s.
   - **Every cut lands within ±0.2 s of a word onset**; 102 of 113 are within ±0.1 s. The median cut is 0.01 s before the word.
5. **Every shot moves.**
   - 113 of 114 shots have camera motion. The exception is the 2-frame flash.
   - The house style is a **linear, centred push-in of +19% per shot** (median; p10-p90 is +10% to +28%).
   - The push is the same whatever the shot length (r = 0.08), so it is "one push per clip".
   - It has no easing: each quarter of the shot carries 25% of the zoom. It is close to a pure zoom, with nearly no parallax.
   - Accents: 6 strong pushes (+45% to x3.2), 7 fast pull-backs or receding moves, and 12 big translations (crane, tilt, truck, whip-tilt, orbit, follow).
6. **Characters barely move.**
   - 50 of 113 shots (56 s) are near-still, with only the camera push moving.
   - 30 shots (37 s) have light motion and 33 shots (38 s) are active.
   - Roblox avatars move pose-to-pose with no in-betweens: limbs and props snap, and decal faces swap in a single frame. Creatures get smooth keyframed motion: hover-bob, wing flutter, waves, sways and flights.
7. **One picture per noun.**
   - Lists are cut item by item: "A star / A tower / a little door", "mountain / moon / stars", "coins / drawings / Fern".
   - The image arrives 0-0.1 s before its noun.
8. **Night is pastel, not dark.**
   - Interiors are **lavender-and-blue with magenta bedding**: highlights #d4bced to #e7d4fc, shadows maroon (#431007 to #723644).
   - The fairy-court scenes switch to a **peach-pink "glow" grade**: highlights #f2cfbc to #fde3c7, shadows #4a1626.
   - Exteriors are **periwinkle on pure black**: highlights #b3b6fc to #bdbffc, sky #000000 to #020018.
9. **Highlights roll off softly.**
   - Interior p99 luminance is only 185-235 of 255, so there is almost no clipping. p1 is 5-20, so blacks are slightly lifted.
   - Exteriors and space crush to true black.
   - Clipping happens only in the castle light-up and in the daylight and morning shots.
10. **No DOF, no vignette, no grain, no chromatic aberration, no motion blur, no lens distortion, no overlays.**
    - The look is "clean render + soft bloom + floating sparkles + grade".
    - Bloom is subtle: about 10-20 px halos on lamps and fairies, stronger only in two hero shots.
11. **Sparkles are everywhere.**
    - Soft 6-to-8-point white-lavender "snowflake" glints, 50-80 px, drift through almost every interior shot.
    - Pink 4-point twinkles and gold dust surround the fairies. There are a few VFX bursts (rings, streaks, puffs).
12. **Only hard cuts.** There are no fades, dissolves, white flashes or whip transitions between shots. Whips happen inside shots, as camera moves.
13. **Captions are CapCut-style auto captions.**
    - One word at a time, white heavy sans at about 96 px, about 5 px black stroke plus a soft drop shadow, centred at y ≈ 1351 (70% down the frame).
    - They switch on the spoken word (median +0.01 s), never leave the screen empty, and have **no pop or scale animation**.
14. **Sound:** continuous VO, plus one continuous tonal music bed about 8 dB under it with no ducking. There are only 2 clear SFX:
    - the swarm whoosh and sub-boom at 40.85 s
    - the light-up whoosh and shimmer at 110.75-112.6 s
15. **Sloppy bits we should not copy:**
    - a 2-frame stray clip at 14.467 s
    - a 0.17-s accidental insert at 78.60 s
    - props teleporting and pose pops
    - caption ASR errors ("everyone" for "every one", lower-case "fern")
    - window views that are brighter than the night room

---

## 1. Shot list

**Columns:**
- Times are exact frame boundaries ÷ 60.
- **Camera move** is measured (z = cumulative scale over the shot: >1 push or zoom-in, <1 pull or receding). Moves in words are from viewing the strips.
- **Subject motion** is the share of pixels that change after the camera is compensated, over 3 frames: still <1%, light 1-5%, active ≥5%.
- **Words** are the ASR words whose onset falls in the shot.
- **Sizes:** ECU / CU / MCU / MS / MWS / WS / EWS / INS (insert of an object) / OTS (over the shoulder) / POV.
- **Lens feel:** "wide" ≈ Roblox default 70° vertical FOV, with perspective stretch visible on close faces. "normal" ≈ 40-50°. "tele" ≈ 20-30°.

| # | Start-end (s) | Dur | Size | Angle | Lens | Camera move (measured) | Subj. motion | On screen | Words |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.00-1.27 | 1.27 | ECU>MS | eye | wide | fast pull-back x10 (ease-out, half done in 0.1 s) + roll drift [z 0.10] | active | Purple chubby fairy hugging a giant tooth at the bed head; blue fabric wall, clock 12:00, shelf; sparkles | In this world, the tooth fairies |
| 2 | 1.27-2.47 | 1.20 | MS>EWS | low>up | wide | crane/tilt up following the fairy (≈2400 px in 1.2 s) [z 0.70] | active | Ext. brick wall + lit window: fairy flies out, up past roof into galaxy sky, shrinks to a dot | don't just collect your teeth, |
| 3 | 2.47-3.75 | 1.28 | MS | high | wide | push-in +28% linear | active | Castle wall top (white bricks, ice floor): blue troll + orange-haired frog fairy fly up; sparkle burst 3.5 s | they're building something with them-a |
| 4 | 3.75-4.30 | 0.55 | WS | low | wide | push +58% + arc (image roll -13°) [z 1.58] | light | Reveal: tooth castle on the icy peak, black sky | castle. |
| 5 | 4.30-6.40 | 2.10 | MS | eye/high | wide | push-in +29% linear + drift (-61,+133 px) | active | Crab-like fairy (eyestalks) holds a big tooth before the brick wall, others behind | You see, every baby tooth ever lost |
| 6 | 6.40-7.47 | 1.07 | MWS | high | wide | push-in +23% linear | active | Same wall, wider: tooth set into the wall as a white brick | becomes one brick. |
| 7 | 7.47-9.07 | 1.60 | MWS | low | wide | push-in +14% linear | still | Castle towers covered in tooth tiles, pink gum bands, molar caps, star | For 10,000 years, they've been building |
| 8 | 9.07-11.27 | 2.20 | EWS | eye | normal | push-in +18% linear | still | Castle on summit of faceted icy-blue mountain, galaxy sky (no subject motion) | it on top of the tallest mountain in the world. On |
| 9 | 11.27-13.25 | 1.98 | OTS | eye | wide | push +10% + tilt [z 1.10] | still | Kid from behind (alien hood) at bedroom window; mountain, pines, street outside; lavender | clear nights, you can see it glowing white, |
| 10 | 13.25-14.47 | 1.22 | CU | low | wide | fast truck right across towers (≈1880 px / 1.2 s) + push [z 1.18] | light | Tower after tower: tooth-tile towers, molar caps on pink rings, nebula | tower after tower. |
| 11 | 14.47-14.50 | 0.03 | WS | eye | wide | static (2 frames) [z 1.00] | light | FLASH FRAME: house exterior under red nebula + pines (stray 2-frame clip) |  |
| 12 | 14.50-16.10 | 1.60 | CU | eye | wide | push +69% + slight roll [z 1.69] | light | Kid in bed, shocked small-o decal, room shelves behind | And nobody knows what happens when it's done. |
| 13 | 16.10-17.10 | 1.00 | MS | eye | wide | push-in +28% linear | light | Orange-haired frog fairy (blue tutu) waving on the sill outside; mountain, fence, road | There's only one rule: |
| 14 | 17.10-18.62 | 1.52 | MCU | high | wide | push-in +27% linear | still | Kid asleep (closed-eye decal), carved wood headboard, pillow, pink blanket | the tooth has to be under your pillow. |
| 15 | 18.62-20.55 | 1.93 | MS>CU | eye>low | wide | push x2 + fast orbit ≈90° (19.73-19.87) [z 2.02] | active | Purple fairy floats in at window reaching, then low-angle CU clinging to wall | A fairy can never take a tooth out of your hand, |
| 16 | 20.55-21.38 | 0.83 | MS | high | wide | push-in +10% linear + drift (-37,+128 px) | active | Kid sitting in bed (smile) gives tooth; tooth pops into fairy's hands at 21.03; clock 12 | it has to be given. |
| 17 | 21.38-23.05 | 1.67 | MS | eye | wide | push-in +23% linear | still | Kid sitting up, arms forward; grin-with-teeth -> open smile decal swap at 22.40 | I've lost 19 baby teeth, |
| 18 | 23.05-25.17 | 2.12 | WS | low>eye | wide | tilt down + push toward window [z 1.17] | light | Room: lavender ceiling with glow stars, window; Fern appears in the window | and every single time, the same fairy came. |
| 19 | 25.17-26.07 | 0.90 | CU | low | wide | push-in +32% linear | active | Fern intro: teal skin, red eyes, crooked grin, red hair buns, waving; clock | Her name was Fern. |
| 20 | 26.07-27.57 | 1.50 | MS | eye | wide | push-in +20% linear | light | Kid (o face) in bed with Fern beside him, back to camera | I stayed up to meet her when I was six. |
| 21 | 27.57-28.97 | 1.40 | CU | high | normal | push-in +22% linear | still | Gold coin on pillow by headboard; one twinkle | She always left a gold coin |
| 22 | 28.97-30.00 | 1.03 | CU | high | normal | push-in +25% linear | still | Coin + small white card beside it | and a tiny drawing, |
| 23 | 30.00-30.87 | 0.87 | CU | low | wide | push-in +24% linear | still | Kid holds the star card on his blocky hand toward lens (o mouth) | no bigger than a stamp, |
| 24 | 30.87-31.40 | 0.53 | INS | top | normal | push-in +23% linear | still | Star card on pink blanket | a star. |
| 25 | 31.40-31.97 | 0.57 | INS | top | normal | push-in +23% linear | still | JUMP CUT same set-up: tower card replaces star card | A tower, |
| 26 | 31.97-32.62 | 0.65 | INS | top | normal | push-in +23% linear | still | JUMP CUT: pink door card dropped on top | a little door. |
| 27 | 32.62-34.17 | 1.55 | MCU | high | wide | push-in +14% linear | still | Kid content (^^ eyes) with door card in front | I kept every one in a shoebox. |
| 28 | 34.17-34.95 | 0.78 | WS | high | wide | push + tilt [z 1.24] | light | Ext. two-storey brick house no.16 at night, pink-lit window, flower bushes | Then last night, my |
| 29 | 34.95-36.72 | 1.77 | MCU | eye | wide | push-in +23% linear | still | Kid (angry brows) tugs tooth; 36.28 pose pop: arm out, red o mouth, red streaks + sparkle + ring VFX | very last baby tooth fell out. Number |
| 30 | 36.72-37.27 | 0.55 | MCU | eye | wide | push-in +14% linear | still | Kid big grin holds tooth up; clock 12 | 20. |
| 31 | 37.27-38.75 | 1.48 | MS | high | wide | push-in +22% linear | still | Kid asleep under blanket | I put it under my pillow like always. |
| 32 | 38.75-39.60 | 0.85 | ECU | eye | normal | push-in +29% linear | still | Clock face, both hands on XII, orange rim | But at midnight, it wasn't |
| 33 | 39.60-40.77 | 1.17 | WS | eye | wide | push-in +16% linear | light | Room: bed foreground, window with Fern and other fairies outside | just fern at my window. |
| 34 | 40.77-42.02 | 1.25 | MS>EWS | high | wide | fast pull-back + crane up x11 (ease-out) [z 0.09] | active | Among fairies, pulling out to an aerial of the swarm diving at the house window | It was a hundred fairies, |
| 35 | 42.02-42.57 | 0.55 | MWS | eye | wide | push-in +25% linear | active | Wall of glowing fairies hovering, warm white haze, trees behind | glowing, buzzing, |
| 36 | 42.57-43.00 | 0.43 | CU | eye | wide | push-in +10% linear | still | Kid shocked (raised brows, red o mouth) |  |
| 37 | 43.00-44.17 | 1.17 | WS | eye | wide | push +36% [z 1.36] | active | Kid in bed, room fills with fairies flying past lens; lamp glow; warm grade starts | lighting up my whole room. |
| 38 | 44.17-45.52 | 1.35 | MS | low | wide | push +53% [z 1.53] | active | Queen (pink goblin, crown + floating tooth, moth wings, beige dress) before fairies | And in front of them, a fairy with a |
| 39 | 45.52-47.17 | 1.65 | CU | low | wide | truck right + push [z 1.20] | light | Crown and floating molar against glow-star ceiling | crown made of a tiny silver tooth, |
| 40 | 47.17-48.03 | 0.87 | CU | extreme low | wide | push-in +20% linear | active | Queen face: yellow bug eyes, bad teeth | the fairy queen. |
| 41 | 48.03-50.32 | 2.28 | MCU | low | wide | push-in +20% linear | active | Queen 3/4, crowd behind; head sways/turns | Your tooth, she said, is the last brick. |
| 42 | 50.32-50.87 | 0.55 | CU | eye | wide | push-in +19% linear | still | Kid profile, o mouth | I froze. |
| 43 | 50.87-52.57 | 1.70 | MS | eye | wide | push-in +17% linear | active | Queen front, window behind, sways | The castle is finished tonight, she said. |
| 44 | 52.57-54.08 | 1.52 | MS | eye | wide | push-in +9% linear | active | Queen with fairies behind, body sways | And when it's done, we go home. Home? |
| 45 | 54.08-54.47 | 0.38 | CU | eye | wide | push-in +9% linear | light | Kid puzzled (Home?), clock |  |
| 46 | 54.47-55.37 | 0.90 | OTS | eye | wide | push-in +16% linear | active | Behind the Queen (wings): she points out the window | She pointed out the window. Up. |
| 47 | 55.37-55.97 | 0.60 | WS>sky | high>up | wide | whip tilt-up ≈1870 px in 0.6 s [z 0.99] | active | Swarm over roof, whip up into purple nebula | Past the |
| 48 | 55.97-56.62 | 0.65 | EWS | low | normal | slight pull [z 0.96] | still | Castle on peak, black sky | mountain, past |
| 49 | 56.62-57.10 | 0.48 | EWS | eye | tele | push [z 1.19] | still | Moon: blue-violet textured sphere filling frame | the moon, |
| 50 | 57.10-57.87 | 0.77 | EWS | eye | tele | push-in +14% linear | still | Deep space, one bright star, blue nebula wisps (static picture) | at the stars. |
| 51 | 57.87-59.25 | 1.38 | MWS | low | wide | push + arc (+6° roll) [z 1.25] | still | Castle against stars | The castle is a ship. We've been building |
| 52 | 59.25-61.25 | 2.00 | CU | low | wide | push-in +11% linear | active | Queen, crowd behind, head bob | our way home for 10,000 years. |
| 53 | 61.25-62.87 | 1.62 | MCU | eye | wide | push-in +18% linear | still | Kid (angry side) pulls tooth from under pillow; warm grade; clock | I pulled the tooth out from under my pillow |
| 54 | 62.87-64.02 | 1.15 | MCU | eye | wide | push-in +23% linear | still | Kid angry, tooth in raised fist | and squeezed it in my fist. |
| 55 | 64.02-64.85 | 0.83 | MCU | eye | wide | push-in +21% linear | still | Kid sad frown decal | If I gave it to them, |
| 56 | 64.85-66.50 | 1.65 | MS | eye | wide | push-in +20% linear | active | Queen full body standing in room, sways | there'd be no more tooth fairies, ever. |
| 57 | 66.50-67.32 | 0.82 | CU | high | normal | push-in +22% linear | still | Gold coin on white nightstand (blue drawers), curtain | No more coins. |
| 58 | 67.32-68.18 | 0.87 | CU | high | normal | push-in +24% linear | still | Red shoebox lid on pink rug | No more drawings. No |
| 59 | 68.18-68.95 | 0.77 | CU | eye | wide | push-in +16% linear | active | Fern front, crowd behind, dark purple background | more fern. |
| 60 | 68.95-70.00 | 1.05 | MS | low | wide | push-in +19% linear | active | Queen standing | The queen didn't move. She |
| 61 | 70.00-70.45 | 0.45 | MCU | low | wide | push-in +7% linear | active | Queen closer, crowd | couldn't. |
| 62 | 70.45-72.42 | 1.97 | MCU | eye | wide | push-in +16% linear | still | Kid determined, tooth in hand, TO THE STARS rocket poster | A fairy can never take a tooth out of your hand. |
| 63 | 72.42-73.92 | 1.50 | CU | low | wide | push-in +15% linear | active | Queen soft, crowd | Take your time, she said softly. |
| 64 | 73.92-75.07 | 1.15 | MS | eye | wide | static + push +9% [z 1.09] | active | Room toward window: fairies fly out one by one | And one by one, the fairies |
| 65 | 75.07-75.27 | 0.20 | MS | eye | wide | none (subject flies off lens) [z 0.43] | active | Purple fairy launches from the lens toward the window |  |
| 66 | 75.27-76.52 | 1.25 | WS | low | wide | push-in +15% linear | active | Ext.: fairies lined along the roof edge above dark window, galaxy sky | flew back outside to wait. |
| 67 | 76.52-77.50 | 0.98 | MS | eye | wide | push-in +9% linear | light | Fern alone on the window sill, street lamps outside | All except Fern. |
| 68 | 77.50-78.60 | 1.10 | WS>CU | eye | wide | push x3.2 (slow, then fast in last 0.35 s) [z 3.23] | light | Fern flies from window up to the lens | She landed on my shoebox. |
| 69 | 78.60-78.77 | 0.17 | CU | eye | wide | push-in +4% linear | light | Fern head turning (0.17 s insert) | Her |
| 70 | 78.77-80.72 | 1.95 | MCU | eye | wide | push-in +27% linear | light | Fern sad, looking aside; SPACE poster | wings were drooping, thin, tired. 10,000 |
| 71 | 80.72-82.17 | 1.45 | MS | eye | wide | push-in +16% linear | still | Fern standing on red shoebox, wooden door behind, dim | years tired. She |
| 72 | 82.17-82.87 | 0.70 | MS | eye | wide | push-in +19% linear | light | Fern on the lid, taps it | tapped the lid. |
| 73 | 82.87-83.37 | 0.50 | CU | high | wide | push-in +13% linear | still | Kid leaning in (hood + face top), nightstand | I opened it. |
| 74 | 83.37-84.77 | 1.40 | CU | top | normal | push-in +25% linear | still | Inside the box: pile of cards | 19 tiny drawings. |
| 75 | 84.77-86.22 | 1.45 | MCU | eye | wide | push-in +17% linear | still | Kid thinking (side-glance decal), shelves | I'd never really looked at them all together, |
| 76 | 86.22-87.42 | 1.20 | MS | high | wide | push-in +19% linear | light | Kid kneeling on round rug; cards pop onto floor one by one; Fern edge | so I laid them out on the floor. |
| 77 | 87.42-88.00 | 0.58 | INS | top | normal | push-in +14% linear | still | Star card on wood floor | A star. |
| 78 | 88.00-88.50 | 0.50 | INS | top | normal | push-in +11% linear | light | Tower card | A tower, |
| 79 | 88.50-89.15 | 0.65 | INS | top | normal | push-in +21% linear | still | Door card on rug | a little door, |
| 80 | 89.15-89.65 | 0.50 | INS | top | normal | push-in +21% linear | still | Window card (pink house wall, purple roof) | a window, |
| 81 | 89.65-90.57 | 0.92 | INS | top | normal | push-in +21% linear | light | Family-waving card | a family waving. |
| 82 | 90.57-92.85 | 2.28 | INS | top | normal | roll -20° + slight pull [z 0.96] | light | Scattered cards slide into a 4x4 grid = one picture | And when I pushed them all together, they made one picture. |
| 83 | 92.85-94.57 | 1.72 | ECU | top | normal | push +28% (tilted frame) [z 1.28] | light | Picture detail: yellow star/planet, pink house door | A tiny house on a faraway star |
| 84 | 94.57-96.65 | 2.08 | ECU | top | normal | push +31% [z 1.31] | light | Picture detail: window, fairy family, door | and a family of fairies standing in the doorway, |
| 85 | 96.65-97.03 | 0.38 | MS | eye | wide | push-in +17% linear | still | Fern by the box, dark warm background | waiting. |
| 86 | 97.03-99.27 | 2.23 | MS | high | wide | push-in +13% linear | still | Kid kneeling behind the assembled picture, Fern left | For six years, she wasn't just leaving me drawings, |
| 87 | 99.27-100.93 | 1.67 | CU | eye | wide | push-in +21% linear | light | Fern front, red eyes, grin, sparkles | she was telling me where she wanted to go. I |
| 88 | 100.93-101.77 | 0.83 | CU | eye | wide | push-in +18% linear | still | Kid soft-eyes smile decal | looked at Fern, |
| 89 | 101.77-102.88 | 1.12 | MCU | eye | wide | push-in +16% linear | still | Kid soft eyes, looking down at hand | then at the tooth in my hand, |
| 90 | 102.88-103.98 | 1.10 | CU | high | wide | push-in +19% linear + drift (+56,+111 px) | still | Blocky hand; tooth pops on top at 103.42 | and I opened my fist. |
| 91 | 103.98-105.32 | 1.33 | MS | eye | wide | arc left + push [z 1.32] | active | Fern hugging the tooth, hovering with bob; door behind | She picked it up with both arms and |
| 92 | 105.32-106.47 | 1.15 | WS | eye | wide | pan + tilt up following [z 1.24] | light | Room: Fern flies out the window | flew it out the window, over |
| 93 | 106.47-107.13 | 0.67 | WS | top/aerial | wide | fast truck [z 0.93] | active | Aerial: street, lawns; Fern with glow pool below | the houses, |
| 94 | 107.13-107.92 | 0.78 | WS | aerial | wide | fast truck left ≈2450 px / 0.78 s [z 0.99] | active | Over brick houses, lawns, mailboxes, lamps | over the trees, |
| 95 | 107.92-109.62 | 1.70 | WS>MS | aerial>eye | wide | follow + push +64% [z 1.64] | active | Fern over dark mountain to castle tower and wall | all the way to the top of the mountain. |
| 96 | 109.62-109.87 | 0.25 | ECU | high | wide | push-in +15% linear | active | Tooth pressed into wall gap: white puff, snowflake sparkles, ring | Click the |
| 97 | 109.87-110.77 | 0.90 | MS | eye | wide | push-in +18% linear | active | Fern on castle wall waving | l Last brick. |
| 98 | 110.77-111.20 | 0.43 | WS | low | wide | push-in +5% linear | still | Castle at night, lavender | The whole castle |
| 99 | 111.20-112.52 | 1.32 | WS | low | wide | push-in +17% linear | light | Same framing: castle blazing cream-white (light-up) | lit up so bright it |
| 100 | 112.52-113.77 | 1.25 | MWS | low | wide | tilt [z 1.16] | still | House exterior in daylight, overexposed hazy sky, sun glare | turned night into day. |
| 101 | 113.77-114.75 | 0.98 | CU | low | wide | camera shake ±10-25 px [z 1.09] | light | Towers in daylight, blue cloud skybox | The towers shook, the |
| 102 | 114.75-115.85 | 1.10 | CU | low | wide | camera shake ±15-50 px [z 1.09] | light | Castle base: red/white thruster pods, dust puffs on peak | ground rumbled, and |
| 103 | 115.85-117.50 | 1.65 | WS | eye | wide | shake decays, slight pull [z 0.92] | light | Castle hovering off the peak, clouds | the castle lifted off the mountain and |
| 104 | 117.50-119.07 | 1.57 | EWS | low | normal | pull (subject recedes) [z 0.83] | light | Castle rises into black space, shrinks, pops to a point (119.03) | flew up into the stars. I |
| 105 | 119.07-121.15 | 2.08 | POV | eye | wide | push-in +13% linear | still | Through bedroom window: night sky, one tiny light; hood edge | watched until it was just one tiny light. That |
| 106 | 121.15-122.07 | 0.92 | MS | eye | normal | push-in +26% linear | light | Assembled picture framed on the wall | was 20 years ago. |
| 107 | 122.07-124.22 | 2.15 | MS | eye | wide | push-in +16% linear | still | Adult narrator (same hood) + blonde daughter in bed raising a tooth; lamp, clock | Last night, my daughter lost her first tooth. |
| 108 | 124.22-125.17 | 0.95 | MCU | high | wide | push-in +24% linear | still | Girl asleep | She put it under her pillow. |
| 109 | 125.17-126.52 | 1.35 | MCU | eye | wide | pose pop + quick tilt up [z 1.23] | still | Girl pops to sitting (125.62), laughing decal; clock; morning grade | And this morning, when she woke up, |
| 110 | 126.52-127.62 | 1.10 | CU | high | normal | push-in +22% linear | still | Gold coin on pillow, twinkle | there was a gold coin |
| 111 | 127.62-128.57 | 0.95 | CU | high | normal | push-in +24% linear | light | Coin + purple card under pillow | and a tiny drawing, |
| 112 | 128.57-129.45 | 0.88 | CU | high | wide | push-in +26% linear | still | Girl looking down at purple card on her hand | no bigger than a stamp. |
| 113 | 129.45-130.42 | 0.97 | ECU | top | normal | push-in +28% linear | still | Purple card: glowing yellow star + little fairy | A fairy waving |
| 114 | 130.42-131.53 | 1.12 | WS | eye | wide | push-in +12% linear | still | Room: girl laughing in bed, adult in hood at right | from a faraway star. |

Evidence: `s/shots_01..10.jpg` (whole list); `s/open.jpg`, `s/m_open.jpg` (#1); `s/a1.jpg` (#2); `s/m_castle1.jpg` (#3-#6); `s/m_tower.jpg` (#10-#12, the 2-frame flash); `s/m_purple.jpg` and `s/m_p2.jpg` (#15 orbit); `s/m_give.jpg` (#16); `s/m_face16.jpg` and `s/c_swap.jpg` (#17 decal swap); `s/m_cards.jpg` (#24-#26 jump cuts); `s/m_pull.jpg` (#29 VFX); `s/m_swarm.jpg` (#34-#36); `s/m_queen.jpg` and `s/m_queen2.jpg` (#38-#44); `s/m_up.jpg` (#46-#48 whip); `s/m_fly.jpg` (#64-#66); `s/m_fern.jpg` (#68-#70); `s/m_kneel.jpg` (#76); `s/m_puzzle.jpg` (#82); `s/m_hand.jpg` (#90); `s/m_fernpick.jpg` and `s/m_wings.jpg` (#91); `s/m_fernfly.jpg` (#92); `s/m_lit.jpg` (#96-#101); `s/m_liftoff.jpg` (#102-#105); `s/m_wake.jpg` (#109).

### Shot statistics

| Metric | Value |
|---|---|
| Shots / cuts | 114 / 113, including the 2-frame flash #11. Real shots: 113. |
| Cuts per minute | **51.5** |
| Shot length | **median 1.12 s, mean 1.16 s**, min 0.17 s (#69), max 2.28 s (#41, #82) |
| Length histogram | <0.5 s: 10 · 0.5-1 s: 39 · 1-1.5 s: 33 · 1.5-2 s: 22 · >2 s: 10 |
| Sizes (final framing) | CU 29 · MS 26 · MCU 15 · WS 14 · INS 9 · EWS 8 · MWS 5 · ECU 5 · OTS 2 · POV 1. **Close (ECU, CU, MCU, INS): 58 of 114 (51%).** |
| Angles (start) | eye 52 · low 23 · high 22 · top-down 14 · aerial 2 · extreme low 1. Creatures are mostly shot **from below**; the kid at eye level or slightly high; objects top-down. |
| Lens | wide (about 70° vertical) 88 · normal 24 · tele 2 |
| Camera motion | **113 of 114 shots (99%)**. 94 linear push-ins (median +19%, p10 +10%, p90 +28%; rate median x1.17 per second). 6 strong pushes (#4, #12, #15, #38, #68, #95). 7 pulls or receding (#1, #2, #34, #65, #93, #103, #104). 12 with big translation (#1, #2, #10, #18, #34, #47, #68, #92-#95, #109). 3 with camera shake (#101-#103). |
| Easing | Push-ins are linear (each quarter carries 24.6 / 25.1 / 25.2 / 24.9% of the zoom). Big pull-backs are strong ease-outs: #1 goes x10 out, half of it in the first 0.1 s; #34 goes x11 out, 0.64 after 0.1 s and 0.24 after 0.4 s. The fly-in #68 is ease-in (x1.14 over 0.7 s, then x2.8 in 0.33 s). |
| Subject motion | still 50 shots (56.2 s) · light 30 (36.9 s) · active 33 (38.4 s) |
| Screen time by location | bedroom interior 70 shots / 85.3 s (65%) · castle and mountain exterior 17 / 20.4 s · 2D drawing-card inserts 14 / 14.3 s · house and suburb exterior 9 / 8.2 s · space and sky 4 / 3.4 s |
| Transitions | 100% hard cuts. Two jump cuts inside the same set-up (#25, #26), one light-change jump (#98 to #99), one stray 2-frame clip (#11), one accidental 0.17-s insert (#69). |

---

## 2. Characters

### 2.1 Hero kid (the narrator as a child; as an adult in #107 and #114)

**Avatar type:** classic **R6**, six blocky parts with no elbows or knees. Evidence: `s/kidfaces.jpg`, `s/scale.jpg`, `full/t_22.2.jpg`.
- The head is the default Roblox head, a rounded cylinder about 1.2 studs tall.
- Torso 2x2x1. Arms 1x2x1 (flat-faced boxes with slightly rounded edges). Legs 1x2x1.
- Total about 5.2 studs, which is about 4.3 head-heights.

**Body colours** (they move a lot with the grade):
- **Skin:** salmon/orange. #bd5f5b in cool night scenes, #d17270 on the lit arm, #efab74 to #f9d296 in the warm queen scenes. The neutral base is about #e8a07a (Roblox "Nougat").
- **Shirt:** plain dark green, #093403 in shade, with a tiny lighter diamond motif (a 2D shirt texture). There is no 3D layered clothing.
- **Legs (adult):** black.

**Hat:** a 3D UGC "Little Green Men" alien hood, the character's identity marker. It is the same in every shot.
- Smooth olive-green plastic (#7a8b0f lit, #5a4812 shade; it turns yellow-green #cbbb24 in the warm grade) with a soft specular sheen.
- **Three big googly eyes** on top: lilac-white sclera #bda1ce with round black pupils.
- One antenna (a stalk plus a ball), two pointed ears sticking sideways, and long side flaps hanging to the chest.
- A dark curved "mouth" line across the forehead.
- Low-poly, with smoothed normals.

**Face:** **classic 2D decal faces**, swapped per beat (evidence `s/kidfaces.jpg`, `s/c_swap.jpg`).
- The base is always black oval eyes with black outlines, about 6-8% of head width each.
- Variants seen:
  1. small "o" mouth with raised brows (wonder)
  2. **red open "o" with raised brows** (shock)
  3. **big grin with lilac-white teeth**
  4. open smile with a red mouth
  5. **^^ closed-eye content smile**
  6. **angry slanted brows** with a flat or "o" mouth
  7. **sad worried brows with a frown**
  8. **soft "heartfelt" eyes** (lilac irises, top lashes) with a gentle smile
  9. sleeping: closed-eye arcs and a small smile
  10. side-glance thinking eyes
- **Expression changes are instant 1-frame swaps.**
  - Example: grin to open smile at frame 1344 (22.40 s), with no in-between.
  - The 36.28 s shock swap is hidden under a VFX burst.
- There is **no blinking, no lip movement, no head-turn animation.**
- Most shots use one face; a swap is used when the narration turns. Examples: #17 ("19 baby teeth"), #20 (o to content), #29 (angry to shocked).

### 2.2 Daughter (#107-#114)

- R6 with a blonde 3D hair accessory: two buns or pigtails, saturated yellow.
- A pink top with light vertical stripes (2D shirt texture).
- Decals: closed smile with brows (#107), sleeping (#108), and a **big laughing open mouth with tongue** (#109, #114).
- The same bedroom set is relit.

### 2.3 Creatures (the "tooth fairies")

The style is **high-poly sculpted "ugly-cute" clay monsters**, a complete contrast to the blocky humans. Evidence: `s/detail1.jpg`, `s/m_fern18.jpg`, `s/m_queen*.jpg`, `s/m_swarm.jpg`.

**Shared design language:**
- Matte plasticine skin (roughness about 0.7) with painted mottling and spots.
- Chubby bellies, big heads (about 40-45% of body height), short legs, small hands with 3-4 fat fingers.
- **Huge glossy bulging eyes:**
  - white sclera with red irises (#770d0b) and black pupils (Fern, the crab fairy)
  - yellow-orange (#c56812) for the Queen
  - pale blue for the purple troll
- Crooked or buck **yellowish teeth** in open grins (the mouth is sculpted open; it never moves).
- Pointy elf ears with pink or red inner colour.
- **Translucent insect or moth wings** (lavender or beige, about 50% opacity).
- **Tutus, diapers or grass skirts.**
- Cute-creepy balance: the silhouettes and tutus are cute; the eyes and teeth are creepy.

**Fern** (helper):
- Teal-grey skin (#5d646d lit, #3e4342 shade) with pink blush cheeks.
- Red-iris eyes; orange-red sculpted hair (#8d3b4c) in braided buns, a top ponytail and a green scrunchie.
- Gap-toothed grin; hot-pink layered tutu (#a02177 to #bd4ca7); lavender wings.
- About 0.5x the kid's height, roughly torso-plus-head height.

**Queen:**
- Pink-magenta goblin skin (#943d4f, deep #6d1b30), yellow bug eyes, a pig snout and big buck teeth.
- Long pointed ears with red insides.
- A **beige clay crown with five ball-tipped points**, with a **molar floating and bobbing above it**.
- Beige moth wings; a tattered beige slip dress with a bow; thin purple limbs.
- She is shot almost only in low-angle CU and MS, which makes her look big.

**Crowd** (about 100 fairies):
- About 6-10 models duplicated many times. The same purple troll and blue chubby figures repeat in #34 and #66.
- The rest: chubby purple troll (#1), orange-haired frog goblin, crab-like eyestalk fairy, grey monkey-like fairy in a yellow grass skirt, baby troll in a bonnet, pale troll with a horn, and others.

**Scale:**
- The tooth prop is about 0.7 kid-head heights, hugely oversized.
- The gold coin is about 0.5 head. The cards are about 0.8 head.
- Creatures are about 0.4-0.6x kid height.

**Consistency:** guaranteed by reusing the exact same assets in every shot. Only the scene grade changes their colour (the hood is olive at night and yellow-green in the warm grade). There are no costume or model variations.

---

## 3. Animation

**Roblox avatars move pose-to-pose with snaps.**
- **Tooth pull** (#29, 36.28 s): the arm jumps from the mouth to the side in 1 frame and the face swaps to shock. A VFX burst hides the jump: red streak lines, white sparkles and a white ring, lasting about 0.4 s (`s/m_pull.jpg`).
- **Props teleport:**
  - the tooth jumps from the kid's hand into the fairy's hands at 21.03 s
  - the tooth appears on top of the hand at 103.42 s
  - the tooth appears in Fern's arms at about 104.3 s
- **Cards pop onto the floor one at a time** every 0.15-0.3 s while the arms stay still (#76, `s/m_kneel.jpg`).
- **The girl pops from lying to sitting** at 125.62 s, covered by a quick tilt-up (`s/m_wake.jpg`).

**Holds:**
- Kid shots are static holds for the full 0.5-2.2 s. There is **no breathing idle, no blink and no head motion.**
- The only life is the camera push plus sparkles drifting past.

**Creatures are smooth and keyframed.** Evidence: `s/m_fernpick.jpg`, `s/m_wings.jpg`, `s/m_queen.jpg`, `s/m_fernfly.jpg`.
- **Hover-bob:** about 10-20 px at 1080 width, about 1 Hz.
- **Wing flutter:** small amplitude (about 15-25°), about 3-5 Hz.
- **Arm waves:** Fern at 25.2-26.0 s and 109.9-110.7 s, the frog fairy in #13.
- **Body sway and head turns** while the Queen "speaks". Her open mouth stays still, with no lip-sync.
- **Flights** follow smooth arcs, with the camera following:
  - out of the window and up into space (#2)
  - to the wall (#15)
  - from the window into the lens (#68)
  - out of the window and over the town to the castle (#92-#95)
- The Queen's floating tooth bobs slowly.

**Swarm:** dozens of instances flying in roughly parallel paths toward the window, with slight random offsets (#34, #37, #64).

**Object motion:**
- Cards slide together with an ease-in-out tween over about 1.2 s (#82, 90.6-91.8 s), then the camera rotates about -20°.
- The castle lifts off slowly, with camera shake of ±10-50 px per source frame (#101-#103). The shake decays in about 0.5 s.
- The castle flies off and **pops out to a single star** at 119.03 s.

**How much moves:** 44% of shots (43% of screen time) have no subject motion at all; the camera push alone carries them. Active shots are mainly creatures flying and the swarm.

---

## 4. Environments

| Location | Built from | Detail |
|---|---|---|
| **Kid's bedroom** (night) | Roblox parts plus meshes with PBR textures | Walls: **blue wallpaper with a strong fabric or stucco micro-texture** (Roblox Fabric look; #4958a0-#5063af in CU, #839ae7 in wides); white skirting. Ceiling: **lavender** (#b28dc0) with **pale yellow-green 5-point glow-in-the-dark star decals**. Floor: **glossy dark terracotta wood planks** (#9f3305). Bed: **carved dark-wood headboard** with vertical ridges, **white puffy pillows** with creases, **pink-magenta duvet** (#a93298 to #c585d1) with real cloth folds and a woven fabric texture, frilly white-lavender bed skirt. Nightstand: white with blue drawers and gold knobs. **Lamp**: cream cylinder shade, emissive #fffee1, on a brass stem. **Wall clock**: orange rim (#9c3703), white-lavender face, Roman numerals, **both hands at 12** in every night shot. Shelves of books (red, yellow, blue), a toy car, a teddy. **Posters**: "TO THE STARS" (rocket on navy) and "SPACE" (planets on navy). **Pink fluffy round shag rug**. A window with a thick white frame and sill. A black TV or monitor on a white desk, a beige wood-grain pillar, a brown wooden door, a **red shoebox** with lid. High density of set dressing; every CU background has a prop. |
| Same room, "fairy glow" (43.0-74.0 s) | Same set | Same props under a peach-pink light. The glow stars read yellow-green on a pink ceiling. |
| Same room, morning (#107-#114) | Same set | A warm cream grade and a different bed colour (pink). The same clock, lamp and nightstand. |
| **House exterior and suburb** | Roblox "Bloxburg-style" builds | Two-storey houses with **dark red-brown brick texture**, white window frames, dark roofs, a "16" plaque, round flower bushes. Lawns with grass texture, grey sidewalks, asphalt road with a yellow centre line, white picket fence, **black Victorian street lamps** with warm glow, black mailboxes. **Realistic textured pine trees** plus leafy trees. |
| **Castle of teeth** (on the peak) | Hundreds of instanced tooth meshes | White base cylinders. Towers clad in **overlapping tooth-shaped tiles like scales**. **Pink "gum" bands** holding rows of small teeth. Conical spires, each **topped by a big molar on a pink gum ring**. A **white 5-point star** on the highest spire. White crenellated brick walls. Pink spheres at the base. For lift-off: a ring of **red and white "thruster pods"** under a dark slab base. |
| Castle wall walkway | Parts plus textures | White bricks with mortar lines. A **light-blue icy floor with cracked or caustic texture** (Glacier or Ice). |
| **Mountain** | Low-poly faceted mesh or terrain | Flat-shaded triangles. Periwinkle at night (#747ff9 / #6871f3), grey-white by day. The castle sits on the very tip. |
| **Space** | Skybox plus meshes | Galaxy skybox: star field, **magenta and purple nebula** (#2a022c, #46134d, #3a2988), blue wisps, a spiral galaxy (#2, 2.0 s). **Moon**: a photo-textured sphere tinted blue-violet (#2b2f89-#6161d3). Black background. |
| **Day sky** (lift-off) | Cloudy skybox | Desaturated teal-blue (#68898d) with cream clouds (#e6ceb4). Sun glare on the house shot. |
| **Drawing cards** | Thin 3D boxes with 2D vector art | White-lavender paper (#d9c6fd). Flat pastel shapes with **dark-purple outlines**: pink house (#f05981), purple roof, yellow star or planet (#f3c108), sky-blue tower, small fairy family. The final card is purple with a glowing yellow star and a fairy. |

**Interiors and exteriors:**
- Interiors take about 65% of screen time.
- Exteriors are seen through the window (#9, #33, #67, #105) and in aerials.
- **Window views are often lit brighter than the night room** (daylight-ish trees at 24 s and 40 s): an inconsistency.

**Water:** none. **Studs:** none; all surfaces are smooth or textured.

---

## 5. Lighting and colour

### 5.1 Grade by scene (measured; "hi" = mean of the top 8% of pixels, "lo" = mean of the bottom 8%)

| Scene (shots) | Time of day / feel | Highlights | Shadows | Frame mean | Key colours |
|---|---|---|---|---|---|
| Bedroom, cool night (#1, #12-#33, #36, #64-#92, #105) | Night, lavender-blue | **#d4bced to #e7d4fc** (lavender white) | **#431007 to #723644** (maroon, never pure black) | #7b587e to #a487bd | wall #4958a0/#5063af/#839ae7, ceiling #b28dc0, duvet #a93298/#c585d1, pillow #dcc5f8, wood #9f3305, headboard #5d1912, kid skin #bd5f5b, shirt #093403, hood #7a8b0f |
| Fairy-court warm (#35, #37-#46, #52-#63; also #106) | "Lit by fairies", peach-pink | **#f2cfbc to #fde3c7** | **#4a1626 to #6c2a3d** | #a46964 to #dea98f | Queen skin #943d4f, bg #ac7976/#e0b5aa, kid skin #efab74, hood #cbbb24 |
| Castle and mountain night (#3-#10, #48, #51, #95-#98) | Night, periwinkle on black | **#b3b6fc to #bdbffc** | **#000000** | #483f6d to #696bb2 | castle #ae9ef6/#957cda/#7356b6, pink bands #b153c4, mountain #747ff9, sky #010106/#020018 |
| Space (end of #2, #47, #49, #50, #104) | Black void | #52539b to #7888fa | #000000 | #01010c to #2f366f | nebula #2a022c/#46134d/#3a2988, moon #2b2f89/#3f43a9/#6161d3 |
| Suburb aerial and house (#28, #93, #94) | Night, navy-violet | #636fc7 to #8383ca | #000000 to #0e1237 | #24254b to #323e71 | lawn #293c4d, road #332f82, light road #4b4a96, brick #3c214b |
| Castle lit / day (#99-#103) | "Night into day" | **#fcfcf6 (clipped)** | #205681 to #607e86 (sky-blue shadows) | #9f9591 to #bab2a2 | castle #f8dbc0/#e7c7ad, sky #68898d, cloud #e6ceb4 |
| Morning epilogue (#107-#114) | Morning, warm cream | **#fcf4d9 / #f8d09e** | #5b1b02 to #7f6a7c | #b09275 to #d1a081 | headboard #be5613, pillow #fbeacf, coin #f3b41b, wall #5b7883 |
| Drawing inserts | Paper on blanket or floor | #d7c8fb (paper) | #591f15 to #9a3e63 | #ae7c83 to #db9b8a | pink #f05981, yellow #f3c108, purple #8c2be5 |

**Per-frame numbers** are in `colstats.txt` (113 frames: mean, luminance p1/p50/p99, saturation, clipping, 5-colour palette) and `tint.txt` (per shot).

### 5.2 Light and shadow

- **Key light:** soft, from upper-front-left, low contrast. Faces and boxes show gentle gradients (`s/shad.jpg`).
- **No hard cast shadows** in the interior. Contact shadows are faint and soft. Exteriors show essentially no shadows. This looks like Roblox Future lighting with soft shadows and strong purple ambient.
- **Fill:** strong coloured ambient: lavender or blue at night, peach in the fairy scenes. Shadows are tinted maroon or purple, not grey.
- **Rim light:** none as a deliberate light. Edges glow only through bloom.
- **Practical lights:**
  - the bedside lamp: emissive #fffee1 core, small halo
  - fairies carry a light: the ground under Fern glows in a soft lavender pool of about 150 px radius at 107.5 s (`s/glow.jpg`)
  - street lamps
  - the lit pink window of the house
- **Ambient occlusion:** mild, only in folds of the duvet and pillows. Most of it is baked into textures.
- **Fog or haze:** none outdoors at night (pure black sky). A slight milky haze in the day and fairy shots, from the lifted highlights. **No volumetric light or god rays**, except the sun glare in #100.

### 5.3 Tone, contrast and saturation

| Group | Mean L | Median L std | p2 / p98 |
|---|---|---|---|
| Bedroom cool | 115 | 42 | 0 / 211 |
| Queen warm | 132 | 43 | 0 / 222 |
| Fern section | 119 | 52 | 1 / 211 |
| Castle night | 93 | 68 | 0 / 195 |
| Space | 35 | 33 | 0 / 143 |
| Day | 157 | 44 | 47 / 251 |
| Epilogue | 143 | 42 | 35 / 240 |

- **Saturation is high but pastel.** Mean HSV saturation is 0.3-0.7 (median about 0.5). Hues stay in a narrow band: **violet, lavender, magenta-pink, periwinkle, peach**, with green (hood) and orange (clock, wood) as accents.
- **White balance** is never neutral:
  - interior whites lean lavender (R≈G-30, B high: #dcc5f8)
  - warm scenes lean peach (#fde3c7)
  - night exteriors lean periwinkle

### 5.4 The "dreamcore / liminal" recipe, exactly

1. A **purple or magenta colour cast over everything** (ambient lavender and a pink tint), with **shadows going maroon or purple**, never grey.
2. **Soft highlight roll-off**: interior whites peak at about 88-92% (#e7d4fc), not 100%. This gives the milky, pastel feel.
3. **Low shadow contrast**: soft omni lighting, no hard shadows.
4. **Night shown as lavender-blue light**, not darkness. Rooms are bright (mean L 115-132); only the outdoor sky is black.
5. **Floating soft sparkles** (white snowflake glints) in nearly every interior shot. They give the "magic air".
6. **Glow-in-the-dark stars on a lavender ceiling, a clock frozen at midnight, a pink shag rug, a toy-space poster**: childhood iconography, very clean.
7. **Gentle bloom** on emissives only.
8. **Constant slow push-in** on near-still images: dreamlike drift.
9. Scene-wide **grade switches by story beat**: cool lavender, then warm peach (the fairies arrive), then cool, then white or day (castle lit), then warm cream (morning).

None of these are used: DOF, vignette, chromatic aberration, grain, overexposure (except the castle light-up beat), lifted-black fades, VHS or other overlays.

---

## 6. Post effects, particles and transitions

| Effect | Present? | Measurement and notes |
|---|---|---|
| Bloom | **Yes, subtle** | Lamp shade core 253-255. Halo ≈10-20 px; the wall next to it is unaffected (128) (`s/glow.jpg`). Stronger on the swarm "glowing" shot #35 (whites #fce3c7, warm haze) and on the lit castle #99 (27.6% clipped). In Roblox terms: Bloom with Intensity about 0.5-1, Size about 24, Threshold about 0.9-1. |
| Depth of field | **No** | Clock, posters and pillars behind close-ups are sharp (`s/dof.jpg`). Background softness in the Queen shots comes from compression and motion. |
| Vignette | **No** | The average of all frames has corners 108-131 and centre 113-118, which is flat; the median corner/centre ratio is 1.09. |
| Chromatic aberration, colour fringes | No | |
| Film grain or noise | No | Only h264 compression blur. |
| Motion blur | **No** | Whip and truck frames are sharp but displaced (`s/m_up.jpg`, `s/m_tower.jpg`). |
| Lens distortion | No barrel. Wide-angle perspective stretch only. | |
| Light leaks, overlays, scanlines, letterbox | No | |
| **Ambient sparkles** | **Yes, signature** | Soft 6-to-8-point "snowflake" glints, white-lavender, 50-80 px on 1080 width, additive, 5-15 visible, slow drift and twinkle (`s/detail1.jpg`). This is the Roblox Sparkles texture. |
| Fairy particles | Yes | Pink and purple 4-point twinkles around creatures. Gold or orange dust embers falling from Fern (#91). One big 4-point star glint on the coins (#21, #110). |
| VFX bursts | Yes, 4 | (a) 3.5 s: sparkle burst on the frog fairy. (b) 36.28 s: red radial streak lines, white sparkles and an expanding white ring, about 0.4 s. (c) 109.62 s: white puff cloud, snowflake sparkles and a ring as the tooth clicks in. (d) 114.75-116 s: tan dust puffs at the base during lift-off. |
| Light-state change | Yes | #98 to #99: the castle material jumps from lavender-lit to cream-white overexposed, as a cut with the same framing. |
| Camera shake | Yes | #101-#103: random jitter of ±5-25 px (with spikes to ±50 px) per source frame, decaying in about 0.5 s in #103. |
| Transitions | **Hard cuts only** | No fades in or out (frame 0 is full picture; the last frame is a normal wide shot). No flash frames (no luminance spikes at any cut). No whip transitions between shots. |

---

## 7. Text and captions

Evidence: `s/cap_top.jpg`, `s/cap_big.jpg`, `capscan.json`.

- **Font:** a heavy geometric grotesque in lower case: double-storey "a", straight-tailed "y", rounded but compact letters, tabular digits. It looks like **Montserrat ExtraBold / Proxima Nova Extrabold**, the usual CapCut caption style. Not Arial Black (too narrow for that).
- **Size:**
  - ascender or cap height **69 px**, x-height **51 px** (on 1080 width), so the font size is about **95-100 px**
  - word width 100-620 px (median about 220 px)
- **Colour:** pure white (250-255). **Black stroke about 5 px.** **Black drop shadow offset about (+5, +5) px, soft over about 8-10 px**, about 90% opacity (a dark run of 10 px to the right and 9 px below, against 5 px left).
- **One word on screen at a time.** Every word is shown and the band is never empty (only 5 of 7892 frames lack a caption). There are no speaker colours and no highlight colours: everything is white.
- **Position:** centred at x = 540. Ascender top at **y = 1317**, baseline **y = 1385**, centre about **y = 1351 (70.4% of height)**. Fixed for the whole video.
- **Timing:**
  - it appears on the spoken word: matched to 569 of 570 ASR onsets, **median +0.01 s** (p10 -0.07 s, p90 +0.10 s)
  - samples: "castle" -7 ms, "midnight" 0 ms, "moon" -3 ms, "Home?" +30 ms, "hundred" +43 ms, "Up" +133 ms, "Click" -153 ms
  - the word stays until the next word starts
- **Animation: none.** Bounding-box height is identical from the first frame (ratio 1.000 at frames 0-7). There is no pop, scale, bounce or fade.
- **Text rules:**
  - lower case except "I" and names
  - numbers as digits: "10,000", "19", "20", with "Number" shown as **"No."**
  - punctuation stripped
- **Auto-caption errors are left in:** "everyone" for "every one", "fern" in lower case twice. They confirm automatic captioning.

---

## 8. Editing and sound-picture sync

**Cuts on words.**
- All 113 cuts are within ±0.2 s of a word onset; 102 are within ±0.1 s.
- Histogram of cut minus word (s): [-0.2,-0.1]: 7 · [-0.1,-0.05]: 15 · [-0.05,0]: 38 · [0,0.05]: 38 · [0.05,0.1]: 11 · [0.1,0.2]: 4.
- **60 of 63 sentences open on a new shot.**
- Long sentences get 2-4 shots, cut on phrase boundaries (commas) or on each noun.

**Image-per-noun, slightly early.** Examples (cut, then word, in seconds):
- "castle" 3.75 / 3.84
- "a star" 30.87 / 30.88
- "A tower" 31.40 / 31.54
- "a little door" 31.97 / 32.02
- "moon" 56.62 / 56.67
- "stars" 57.10 / 57.07
- card list: 87.42 / 87.39, 88.00 / 88.05, 88.50 / 88.53, 89.15 / 89.17, 89.65 / 89.65
- "coins" 66.50 / 66.51, "drawings" 67.32 / 67.31, "Fern" 68.18 / 68.11

**Reaction shots** of 0.38-0.55 s on short lines: "I froze" (#42), "Home?" (#45), "20." (#30), "waiting" (#85).

**No freeze frames, no speed ramps, no digital punch-ins.** Every zoom is a continuous push.

**Picture state changes on the word:**
- the decal swap at 22.40 s comes 0.08 s after "baby"
- the castle lights up on the cut at 111.20 s ("lit" is at 111.49)
- the tooth clicks in at 109.62 s ("Click" is at 109.57)

**Audio**, from the voice and music split (`stems/tf_voice_stem.flac`, `stems/tf_music_sfx_stem.flac`, `s/spec_*.png`):
- **VO** runs continuously from 0.08 s to 131.4 s with no pauses longer than 0.64 s. Overall RMS about -21.8 dBFS.
- **Music bed**: one tonal track from start to end (piano or bell plucks plus soft pads).
  - About 96 BPM estimate. Strong pitch classes C#, F, F#, A.
  - **Constant -29.5 ± 1 dB RMS in every 2-s window**, which is **about 8 dB under the VO**.
  - **No ducking, no drops, no stingers, no hits on cuts.**
- **SFX: very sparse.**
  1. **40.85 s**: a broadband whoosh or impact transient, then a **sub-bass boom or rumble below 120 Hz to about 43.7 s**. It is the swarm arriving, synced to the cut at 40.77 s ("It was a hundred fairies").
  2. **110.75-111.0 s**: a rising broadband whoosh into a **bright shimmer or chime band from 111.0 to 112.6 s**. It is the castle lighting up, synced to the cut at 111.20 s.
  3. Nothing clearly audible on the whip-up (55.4 s), the "click", "towers shook / ground rumbled", the flights, or the card pops. Faint chimes may be masked by the music.
- The owner adds music himself. To match the reference he should keep it about 8 dB under the voice and constant.

---

## 9. What makes it look premium, and how to get there in Three.js

### 9.1 Premium drivers (ranked by impact)

1. **Creature design quality**: sculpted clay monsters with huge glossy eyes and teeth, set against blocky Roblox kids. This is the strongest single factor.
2. **A consistent pastel night grade per scene**, with soft highlight roll-off, purple or maroon shadows, and story-driven grade switches.
3. **Rhythm**: 1.16-s shots cut on words, one image per noun, and every shot drifting forward.
4. **Dense, readable set dressing**: glow stars, clock at 12, posters, rug, real fabric and wood textures, cloth-fold bedding.
5. **Magic air**: ambient sparkles, glows and small VFX bursts on key actions.
6. **Spectacle wides**: the tooth castle on a peak, the swarm aerial, the lift-off, space and moon.
7. **Clean image**: no gimmick post effects, so it never looks "filtered".

**Cheap tells in the reference (do not copy):**
- pose pops and teleporting props
- 40-fps judder
- the stray 2-frame clip (#11) and the accidental insert (#69)
- caption ASR errors
- inconsistent window lighting
- static decal faces with zero idle motion (some idle breathing or bob on humans would be better)

### 9.2 Hard to reproduce in Three.js, and the best approximation

| Look | Difficulty | Best approximation (procedural, SwiftShader-friendly) |
|---|---|---|
| Sculpted clay creatures | **Hardest** | Build bodies as **metaball or SDF-like blobs**: `MarchingCubes` from three/addons, baked once to a static BufferGeometry, or merged spheres and capsules with low-frequency noise displacement and `computeVertexNormals`. Material: `MeshPhysicalMaterial` (roughness 0.65-0.75, sheen 0.3-0.5 in a lighter tint of the skin, clearcoat 0) plus a procedural mottled-spots `CanvasTexture` and pink blush gradients. **Eyes**: sclera sphere with clearcoat 1, coloured iris disc, black pupil, partial-sphere eyelids; the eyes should be 25-35% of head width. **Teeth**: `RoundedBoxGeometry` in ivory #e8d9a8 with slight random tilt. **Ears**: lathe cones. **Hair**: `TubeGeometry` coils and torus buns. **Wings**: `ShapeGeometry` with a vein `CanvasTexture`, `transparent` opacity 0.5, `DoubleSide`, `depthWrite:false`, flutter at 3-5 Hz. **Tutus**: `LatheGeometry` with a zig-zag hem and 2-3 layers. **Crowd**: 6-8 variants instanced, with hue shifts. |
| R6 kid with decal faces | Easy | Boxes with 0.05-stud bevel (`RoundedBoxGeometry`). Head = lathe of a rounded rectangle (Roblox head). Faces drawn into a `CanvasTexture` (black ovals, outlined mouths) and swapped per beat. Alien hood = sphere shell plus extruded side flaps, 3 eye discs (sclera #d8c8f0, black pupils), antenna, cone ears, mouth line (tube); MeshStandard roughness 0.45 for a slight sheen. Add a subtle 1-2% scale "breath" idle and occasional blinks: better than the reference, still on style. |
| Fabric, wood, brick, ice textures | Medium | Procedural `CanvasTexture`s with matching normal maps (Sobel of the height): fabric = fine noise plus weave; wood = stretched noise stripes; brick = mortar grid; ice = Voronoi cracks. Duvet = high-res plane displaced by summed sines plus noise (soft folds). Shag rug = noise-displaced disc with a high-frequency normal map. |
| Castle of teeth | Medium | One tooth geometry (lathe crown plus two roots), `InstancedMesh` of about 2-5k tiles on tower cylinders in staggered rows (scales). Pink torus "gum" bands with instanced small teeth. Molar caps on pink rings. A star on the top. Night: lavender-lit (#ae9ef6). Lit state: swap to emissive cream (#fdf4e8) and raise bloom. |
| Soft pastel lighting | Medium | `HemisphereLight` (sky #b9a8ff, ground #5a2a4a, about 0.8), one soft `DirectionalLight` from upper-front-left (PCFSoft, radius 6-8, 1024-2048 map; or shadows off and fake soft contact shadows with blob textures, which is cheaper on CPU), `PointLight`s for the lamp and the fairy glow pools (decay 2, warm). |
| Grade per scene | Easy | `OutputPass`, then a custom `ShaderPass`: lift, gamma and gain toward the target hexes in §5.1; a highlight shoulder so interior whites stop at about 0.90 (#e7d4fc); saturation x1.1-1.2. Per-scene presets: cool-lavender, warm-peach, night-periwinkle, space, day, morning-cream. |
| Bloom | Easy | `UnrealBloomPass`: strength 0.3-0.45, radius 0.4-0.6, threshold 0.82-0.9; for glow beats 0.8-1.2. Make emissives (lamp, fairy auras, lit castle) exceed the threshold. |
| Sparkles | Easy | A `Points` or `Sprite` pool with a 6-to-8-point soft star `CanvasTexture`, `AdditiveBlending`. 8-20 per interior frame, 40-80 px on 1080 width, drift 20-60 px/s, twinkle (opacity and scale sine 0.6-1.2 s). Pink 4-point and gold dust variants around fairies. Bursts = 20-40 sprites plus an expanding ring sprite over 0.3-0.4 s. |
| Camera grammar | Easy | Per shot: **linear FOV zoom equal to a +19% scale** (`fov_t = 2·atan(tan(fov0/2)/(1+0.19·t/T))`), centred, no easing. fov0 = 70° vertical for wide-feel shots and 35-50° for inserts and EWS; space and moon use 20-30°. Pull-backs: exponential ease-out, x10 in 1.2 s with half done in 0.1 s. Shake: random jitter 5-25 px for 1 s. Whip-tilt: about 1900 px in 0.6 s. |
| Frame rate and resolution | Easy | Render **true 60 fps** at 1080x1920 (the reference is 40 fps, with detail about 540-720p). Use SMAA or FXAA. Supersampling is not needed. |
| Skyboxes | Easy | Galaxy: a large sphere with a `CanvasTexture` (noise-based nebula in #2a022c/#46134d/#3a2988 plus star points). Moon: a sphere with a procedural crater texture tinted #3f43a9. Day: a gradient plus noise clouds (#68898d / #e6ceb4). |
| Captions (if we do them) | Easy | Heavy sans (Montserrat ExtraBold) at 96 px, white, 5 px black stroke, black shadow (+5, +5) blur 8, centred at y = 1351. One word at a time, switched at the word onset, no animation. |

### 9.3 Production rules to copy

- About 1.1-1.2 s shots, with **a cut at every sentence and at every concrete noun in a list**.
- **Every shot gets a +15-25% linear push.** One big move per 8-10 shots (pull-back reveal, follow flight, whip-tilt, orbit).
- About 50% close shots. Creatures shot from low angle, objects top-down, the kid at eye level or slightly high.
- Change the expression (decal) per beat. Use VFX bursts to sell any snap action.
- Keep one bedroom set for about 65% of screen time and reuse it for the epilogue with a new grade.
- Change the grade at story turns: cool, warm when magic arrives, cool, white or day, warm morning.
