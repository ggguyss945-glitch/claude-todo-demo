# PLAN: "If An Eighth Step Appears On Your Mirror... WIPE THE GLASS CLEAN"

This is the director's plan for the second "Rules After Dark" film. Builders work from these files:

- `plan/shots.json`: 317 shots covering 0 to 700.0 s. Each shot has its camera keys, cast and acting, props, HUD, captions, header, counter and SFX.
- `plan/sound_plan.json`: every SFX cue, the ambience beds, the music map, the voice FX and the Epidemic shopping list.
- `plan/shotlist.py`: the source table. Edit it, then run `plan/make_plan.py` and `plan/validate.py` (commands in section 10).

All times come from `_work/align/timeline.json`. Positions are in the 1920x1080 design space with the camera at x 960, y 540, zoom 1.

**YouTube title:** If An Eighth Step Appears On Your Mirror... WIPE THE GLASS CLEAN

Alternates:
- If Your Mirror Grows An Eighth Step... DON'T WAIT
- If Someone You Love Calls From The Mirror... ASK WHAT THEY WISHED FOR

The cold open's first line is the rule premise (0.16 s): "If you draw seven steps on a mirror and an eighth one appears, wipe the glass clean."

**The film in one breath.** At 11:57 PM, on the last night of a condemned summer camp, you and Tess find your missing brother's towel-wrapped mirror. On the glass are seven lipstick steps. An eighth appears. Behind it is a woman in black, and below her is Noah, who is still 13 and still waiting for a breakfast bell that never rang. Tess counts down on your side while you go through. The fake bell rings perfectly; the real one rattles. Noah comes back grown, and the queen ends up in the phone that nobody covered.

---------------------------------------------------------------------------------------------------------------------

## 1. Look rules (all builders)

### Style
- The style is the same clean flat vector as the police film:
  - uniform outline `LINE #1d1f26`, 7.5 to 9 design px on close-ups and 3 to 4.5 on wides;
  - one soft shade step;
  - no grain above 1.5 levels and no chromatic aberration;
  - a strong vignette, about 0.35 at r = 0.8 on night shots.
- **Two drawing languages.**
  - People are drawn with outlines and flat fills.
  - The Queen of Spades is drawn without outlines: a near-black silhouette whose edges are thin pale scratch lines, with lipstick-red accents carrying the widest glow in the film (section 2.5).
- **Never a still frame.**
  - Every shot has camera keys. The slowest move is 1 %/s.
  - Every shot also has an `energy` note naming what moves: particles, beams, cloth, acting.
  - When a subject is frozen (Tess's steady beam in S150), the camera still drifts and the dust still moves.

### Palettes per side of the glass
The `side` field on each shot says which world it is in.

| side | what it is | palette (most used first) | luma p50 | notes |
|---|---|---|---|---|
| `ours` | the camp and Cabin 7 at midnight | `#0b1822 #152634 #233b4c #344d5f`; moon rim `#9fb6ff`; flashlight core `#fff2d6`, falloff `#f3d9a6` | 40-55 outside, 30-45 inside | hue ~205 deg; Tess's beam is the key light; dust is always drifting in it |
| `mirror` | looking into the glass (reflection, the stairs) | as `ours` around the frame; inside the reflection as `theirs`; the stairs world is near-black `#080c14 #0b0d14` with red `#c63449` | 15-25 on the stairs | the 8th line and the queen glow |
| `theirs` | the other cabin "as it was", 6:59 AM, dawn | `#e7e5e0 #ccccc9 #adaead #7f8b94`; warm accent `#b79342`; lantern `#ffd9a0` | 140-165 | "too normal": low saturation 55-70, clean, still, no dust except one window shaft; curtains never move |
| `memory` | 14 years ago | bleached: lifted floor `#2c2824`, highlights `#f6e7c8`, saturation x0.6, halation bloom | 120-150 (day) | three variants: `memory_day`, `memory_night` (lantern amber `#e8b878` on `#1a1c2a`), `memory_morning` (overexposed cyan-white mist `#dfe8ea`) |
| climax (any side, from 534.4 s) | the red takes over | lipstick spill `#c63449`, glow `#ff4060` | -15 % | the red-pixel share stays at or below 1 % until 534 s, then reaches 3-8 % in rule 6 and rule 7 (REF rule 10) |

### Grade presets
The sets builder adds these to `engine/post.py` GRADES. The `grade` field of each shot names one.

| preset | parameters (on top of BASE) |
|---|---|
| `camp_night` | contrast 1.12, pivot .2, gamma .94, sat .9, wb (.88,.98,1.10), floor `#06101a`, bloom 1.0, vignette .35, grain 0 |
| `camp_night_run` | camp_night + exposure +.1, bloom 1.2 |
| `cabin_flash` | contrast 1.1, gamma .95, sat .85, wb (.94,.99,1.08), floor `#070d14`, bloom .9, vignette .32 |
| `cabin_doorway` | cabin_flash + wb (1.0,.99,1.0), bloom 1.1 (warm dawn spill from the doorway) |
| `cabin_after` | cabin_flash + exposure -.1, sat .8 |
| `mirror_world` | contrast 1.15, gamma .88, sat .9, floor `#04060c`, bloom 1.4, bloom_r 20 (entity glow), vignette .3 |
| `mirror_old_cabin` | cabin_flash + exposure +.2, vignette .4 (the pale reflection lives inside the dark frame) |
| `dawn_normal` | contrast .95, pivot .3, gamma 1.05, sat .7, wb (1.03,1.0,.96), floor `#3d3d40`, bloom .3, vignette .67 |
| `dawn_queen` | dawn_normal + sat .55, wb (.97,1.0,1.04), vignette .55 (colour drains near her) |
| `dawn_break` | dawn_queen + red leak at the frame edges (post red .15) + exposure flicker from `fx_post` |
| `climax_red` | contrast 1.08, gamma .9, sat 1.25, wb (1.08,.92,.94), floor `#0c0408`, bloom 1.0, bloom_thr 228, vignette .32 (not mono: the red comes from the light) |
| `memory` | contrast .85, gamma 1.08, sat .6, wb (1.06,1.0,.9), floor `#2c2824`, bloom 1.5, bloom_thr 220, vignette .45, soft 1.0 |
| `memory_night` | memory + exposure -.6, wb (1.08,.98,.86) |
| `memory_morning` | memory + exposure +.25, sat .45, wb (.98,1.0,1.04) |
| `rule_card` | the grade of the card's background set (`bg`); the card is HUD |
| `phone_dark`, `neutral` | already exist |

---------------------------------------------------------------------------------------------------------------------

## 2. Cast design sheets (characters.py)

The police cast stays in the file. Add the people below.

- **Fear eyes** (every human, REF rule 9): swap to white discs about 0.24 of head width with pupils 0.2 of the eye. Brows go up and tilt, sweat drops appear, and the hands act big.
- **Lip-sync** follows `talk(line=i)` on the real voice envelope.
- **`talk_silent(dur)`** moves the mouth softly with no audio. Use it for speech the narrator only describes ("he says your name").

**Modes** (the `mode` field of a character in a shot):

| mode | what to draw | `at` |
|---|---|---|
| `body` | full figure | `[x, y_feet, height(, depth)]` or an anchor name |
| `bust` | head and shoulders | `[cx, cy, scale]`; scale 1.0 = a 600 px head; the shot's view is the background, blurred with `dof` and dimmed 30 % |
| `hands` | hand-only insert | `[x, y, size]` |
| `feet` / `legs` | cropped lower body | |
| `silhouette` | dark shape with a rim light only | |
| `lying` | in a bunk | |

### 2.1 You (`you`, mid-20s; Noah's younger brother, 11 that summer)
- **Build:** average, shoulders slightly rounded.
- **Face:** you look like their dad, which is why Noah asks "Why do you look like Dad?".
  - Squarer jaw than the police `you`.
  - Short dark-brown hair `#382821`, slightly receding at the temples.
  - Short stubble beard `#4a3c33` (stub .6), faint forehead lines, tired bags .6.
  - Skin `#c9aa98`, shade `#97786c`. Brown eyes.
  - No scar and no ring (`scar=0, ring=0`).
- **Clothes:**
  - Olive canvas work jacket `#4a5038` (shade `#33382a`, highlight `#626a4c`) with a brown corduroy collar `#6b5a3e`. The collar is a plot prop: Tess grabs it at 608.97 and Noah holds it at 635.9.
  - Grey henley `#7d8287`, dark jeans `#2a3347`, brown boots `#4a3426`.
- **Props:** from 323.65 to 651 your left hand is a fist around the candy.
- **Expressions:** neutral, grief (sad + wet eyes), fear, shock, dread, tense, tempted (soft, eyes lowered), resolve, shout, wonder, relief_cry, scream.

### 2.2 Tess (`tess`, mid-20s; your old friend)
- **Look:** practical and brave.
  - Auburn hair `#6b3a26` in a low ponytail, freckles, strong level brows, a small set mouth.
  - Burnt-orange rain shell `#9a4a2e` (shade `#6e321e`, highlight `#b8603e`). It is the one warm accent on our side.
  - Dark grey cargo pants `#3b3f45`, hiking boots `#3a2c22`.
- **Props:**
  - A big black aluminium flashlight, body `#1c1e22`, lens ring `#b9bec6`. The beam is a light layer drawn by sets (section 3.1) and aimed by the acting clip `flashlight(aim=...)`.
  - A key ring on a carabiner with a padlock key and a CABIN 7 tag.
  - A black phone.
- **Blinks:** 1-2 frames.
- **Expressions:** brave, tense, recognise, half_smile, fear, sad, shock, resolve, shout, angry, puzzled, neutral.

### 2.3 Noah at 13 (`noah13`; the older brother)
- **Proportions:** kid. 0.8 of adult height, head 1/5.5 of height.
- **Face:** brown messy hair with a cowlick `#4a3226`, freckles `#b07a62`, round brown eyes, warm skin `#d2b3a0`. He is the warmest thing in the pale world.
- **Gap teeth:** a gap between the front teeth, 6 px at a 600 px head. Show it in every smile and on every line he speaks.
- **Green sweatshirt:** crew neck `#3f6b45` (shade `#2b4c31`, highlight `#57875c`) with a faded white "CEDAR LAKE" arc print and a kangaroo pocket that holds the candies.
- **Pajama pants:** blue-grey flannel plaid, `#4c5a72` with `#3a465c` lines.
- **Feet:** one white canvas sneaker `#e3ded2` on his **left** foot, lace loose. His right foot is bare. The other shoe sits beside the bed (S275).
- **Tape:** three fingers of his **right** hand (middle, ring, little) are taped together with blue medical tape `#4d8fd6`, sheen `#8fc0f0`. The tape edge is lifting.
- **Acting:** calm and wrong.
  - He keeps tying the same knot in a loop: `tie_loop` with a 2.4 s period, always starting from the same phase. `clip_id` marks exact replays:
    - `breakfast_A` at 318.36 and again at 419.46 must be frame-identical acting;
    - `loop_reset` at 359.74 snaps back to the pose of 305.72.
  - He rarely looks up. When he does, he gives a warm gap-tooth smile.
  - `face_flash` (366.8 s) swaps his face to grown Noah's for 0.5 s, with 2-frame flickers.

### 2.4 Noah grown (`noah_grown`, about 27)
- **Build:** 1.08x your height, broader.
- **Face:** the same face aged. Longer jaw, stubble `#4a3a30`, bags, wet eyes. The gap teeth stay.
- **Clothes:** the green sweatshirt is two sizes too small.
  - The hem sits above the belt line, cuffs halfway up the forearms, and the shoulder seams show stretch lines.
  - The pajama pants now end mid-shin. Both feet are bare.
- **Hands:** big (hand scale 1.25) and shaking (`tremble` .4-1.0).
- **Jacket:** your olive jacket is on his shoulders from 635.06.
- **Aging morph:** `age(t0, t1, part=arms|face|stubble, start=k)` drives a pose parameter `age` from 0 to 1.
  - It controls limb length, head size, jaw, stubble alpha and the sweatshirt fit.
  - It is used at 559.5-567.7 (S252-S255).

### 2.5 The Queen of Spades (`queen`; the entity)
- **Body:** a woman 1.05x adult height, neck 1.3x long, fingers 1.4x long.
- **Clothes and hair:**
  - A black high-collared, long-sleeved satin dress to the floor: base `#0b0d14`, sheen `#1c2130`.
  - Bare feet, pale blue-grey with dark toe tips.
  - Long straight black hair `#06070b` to the waist with a centre parting. It often covers the face.
- **Skin:** `#cfd5da`, shade `#8e97a3`, no blush.
- **Mouth:** lipstick `#c63449` with a glow `#ff4060`. It is the same red as the steps.
- **Drawing language:** no outline.
  - Edges are thin pale scratch lines `#d9dee6` at 50 %, 1.5-2 design px, re-jittered every 3 frames like the diver reference's scribbled entity.
  - Red accents carry the widest glow in the film: the halo stays at about 0.66 at 40 px at 2560.
- **Movement:** uncanny stillness. `life=0`, no breathing, no blinks. She moves only in snaps, then holds:
  - `head_snap(deg=130, dur=0.18)`;
  - `smile_off`, which drops the grin in 2 frames;
  - `sit_beside`, one smooth inhuman motion;
  - `lift_foot`, slow.
- **Reveal stages** (the `stage` field):

| stage | what is shown | first shot |
|---|---|---|
| 0 | back, hair, dress, feet only | S004 (5.35 s) |
| 1 | one eye through the hair: pinpoint pupil, red iris | S089 (197.46 s) |
| 2 | hands, the red mouth, the seated figure with hair over the face | S111 (248.12 s) |
| 3 | the full creepy face, used three times: S128 (283.5 s, "There's time for both of you"), S212 (478.0 s, "I can put you back...") and S316 (696.8 s, in the phone); the face going blank at S237 (532.95 s) | S128 |

- **Full creepy face:**
  - Eye whites 0.26 of head width, pupils 0.12 of the eye, red irises (`#c63449` ring 0.35 of the eye) with a glow.
  - Bloodshot veins and dark bags.
  - A too-wide grin, 0.75 of head width, with two rows of small separate teeth (24 or more). Lipstick smeared up the cheeks.
  - The head tilts beyond natural (22-28 deg).
- **Other expressions:**
  - `queen_soft`: a closed-lip red smile, motherly, with dead or hidden eyes.
  - `queen_stare`, `queen_still`, `queen_call` (mouth wide open, calling without sound), `queen_grin`.

### 2.6 Mom
Mom never appears as a drawn character. She appears only as:
- the phone UI: the MOM contact, with a small circular avatar of an older woman with grey curly hair (the police `mum` head at 120 px);
- the polaroid of Noah by the family car (S098-S099, no face).

### 2.7 Memory cast
- **`you_kid`:** you at 10-11. 0.7 adult height, big eyes, your hair colour, a blue/white striped tee `#5a7fa8`/`#e8e4da`, shorts and sneakers.
  - Expressions: happy, laugh, sad, shock, sleep, sly, sure.
- **Extras** (detail 0, faces not needed):
  - `counselor`: a teen in a teal camp-staff tee `#3f7f86` with a whistle lanyard.
  - The camp director: cap and clipboard.
  - Kitchen staff in white aprons.
  - A search line of adults with flashlights.
  - `kids`: 2-3 kid variants in sleeping bags.
  - `adult_legs`: cropped adult legs around the kid.

### 2.8 Acting clips the plan uses
**Existing in characters.py:** expr, stare, head_tilt, snap_turn, lean_in, talk, hold_up, walk, turn, freeze, look, head_down, sit, point, flinch, hand_to_mouth, nervous_glance, phone_to_ear, blink, tremble (as `pose.tremble`), life, creep.

**New** (each returns its SFX events where it makes a sound):

| group | clips |
|---|---|
| Tess and the flashlight | `flashlight(aim, sweep, on, raise_)`, `finger_to_lips(t1)`, `grab_shoulder`, `snatch`, `throw`, `grab(what)`, `grab_collar`, `yank`, `kick`, `wind_up`, `strike(prop, target)`, `unlock`, `pull_chain`, `jingle`, `set_down`, `pick_up`, `rub_fingers`, `kneel`, `laugh_dies`, `half_smile`, `step_back`, `step_over`, `shout_silent`, `fall_back` |
| you | `unwrap`, `grip_frame(tremble, fail_open)`, `tilt_frame(angle)`, `touch_glass(at)`, `nail_tap`, `smear(step, length)`, `wipe_glass(strokes, dir, sleeve)`, `squeeze_through`, `take_hand`, `pull_hand(force)`, `take(prop)`, `fist(slow, squeeze, fail_open)`, `open_fist`, `rub_thumb`, `reach(to)`, `slide_out`, `shove`, `yanked_back`, `give_jacket`, `tears(amount)`, `swallow`, `stand_up` |
| Noah | `tie_loop(period, phase)`, `hold_out(prop)`, `withdraw`, `look_up`, `head_lift`, `talk_silent`, `pulled_along`, `hand_jerk`, `stumble`, `step_through(foot)`, `fall_through`, `slip_tape`, `peel_tape(n)`, `fingers_flex`, `reach_through`, `tap_rail`, `drop_lace`, `scoot(dx)`, `pat_knees`, `laugh`, `run`, `wring`, `pull_from_pocket`, `swat`, `whistle_s`, `eat`, `wave`, `draw_step`, `breathe_sleep`, `mouth_open`, `mouth_open_close` |
| Noah grown | `age`, `look_at_hands`, `stand_hit(what)`, `cover_ears(dur)`, `rock(period)`, `hold_collar`, `hand_out` |
| the queen | `still`, `head_snap(deg, dur)`, `smile_off(dur)`, `sit_beside`, `pat(n, spacing)`, `press_through_cloth(depth)`, `lift_foot(to)`, `toes_curl`, `step_up(foot)`, `climb`, `hem_sway`, `call_silent` |
| memory | `wake_up`, `wake_squint`, `press_button`, `pull_socks`, `drop_prop`, `ring_bell`, `dare`, `hand_over_mouth`, `call_out`, `shift_weight`, `nod`, `smile`, `hand_on_glass` |

---------------------------------------------------------------------------------------------------------------------

## 3. Sets, views and lighting variants (sets.py)

### How a set is used
- A shot names `set`, `view` and `var` (the lighting variant).
- Each view is a SetPiece whose key points sit where the layout below says, with the camera at 960, 540, zoom 1.
- Camera keys in shots.json aim at these points. Shots push up to zoom 2.2, so draw each view with 25 % margin.
- Anchors are named so that `chars[].at` can use them.
- Static parts go in cached layers. The animated layers are small.

### 3.1 Lighting system shared by all `ours` sets
- **Tess's beam:**
  - a warm-white cone (core `#fff2d6`, alpha 0.35 falling off to 0 over its length);
  - a hot spot on whatever it hits;
  - dust motes (60-120 particles drifting 8-20 px/s inside the cone, never stopping);
  - a lens flare when it points near the camera.
- **Aiming the beam:** the aim comes from Tess's `flashlight` clip (`gate`, `mirror`, `floor`, `sweep`, `wild`, `ahead`). In `cabin_now/after` the flashlight lies on the floor and its beam rakes the floor.
- **Moonlight:** cool shafts through windows, `#9fb6ff` at 25 %.
- **Fireflies:** outdoors, 6-10 blinking dots crossing the frame.
- **Mist:** bands drifting at 14 px/s.
- **Pines:** sway.

### 3.2 Sets and views
Layout coordinates are in design px.

**`camp_gate`** (variants: `moon`, `moon_flash`)
- `wide`:
  - An arch sign CAMP CEDAR LAKE · EST. 1962 spans x 520-1400, y 260-360, with peeling paint.
  - A chain-link double gate spans x 640-1280, y 480-900. The padlock and chain hang at (960, 720).
  - The notice board with the MISSING poster is at (330, 560).
  - A demolition notice is zip-tied to the fence at (1500, 640).
  - Pines are in layers, the moon is at (1600, 160), and mist and fireflies drift.
  - Anchors: `tess_gate` (880, 960, h 600), `you_gate` (1100, 960, h 620).
- `lock_cu`: the padlock and chain at (960, 560), filling 40 % of the frame.
- `keys_cu`: the key ring.
- `poster`: the poster fills 70 %.
  - Header MISSING.
  - Noah's school photo (gap-tooth grin, green sweatshirt) at (960, 430), 360x430.
  - The lines "NOAH, 13" and "LAST SEEN: CAMP CEDAR LAKE, CABIN 7" at y 700.
  - The line "LAST SEEN WEARING A GREEN SWEATSHIRT" at y 760.
  - It is rain-stained with a torn corner.
- `notice`: NOTICE OF DEMOLITION · CABINS 5 - 7 · SATURDAY 7:00 AM.

**`camp_path`** (`moon`, `moon_flash`)
- `aerial`: the camp seen from high up.
  - Cabins 5, 6 and 7 at (600, 640), (900, 600) and (1200, 640).
  - The mess hall at (1500, 420).
  - The lake at the top left with a moon glint.
  - The gate at (1650, 950) with your car's headlights (they switch off at 22.6 s).
  - The excavator at (1350, 700).
- `cabins_row`: eye level.
  - Cabin 7 is nearest at x 1300: a number plaque, a hasp padlock, a faded strip of old search tape on the rail.
  - The excavator bucket is a foreground silhouette at depth 0.6.
- `path_track`: a fence and gravel path for side tracking; fence posts at depth 0.6.
- `path`: the view from the Cabin 7 door across the path to the mess hall porch.

**`mess_porch`** (`moon_flash`, `run`: Tess's beam swinging wildly, `bell_hit`: flare plus a red rim from 534.4 s)
- `wide`:
  - A long low lodge with a screen door at (960, 520) and a hand-painted MESS HALL sign at (960, 300).
  - Wind chimes at (1400, 360) that move. Stacked chairs.
  - The crate on the boards at (1180, 820).
  - Anchors: `tess_steps`, `you_steps`, `porch_mid`, `porch_left`.
- `porch_low`: a low angle on the boards with the crate in the foreground.
- `crate_cu`: the slatted pine crate stencilled SAVE FOR THE MUSEUM, with a museum tag on string ("CEDAR LAKE HISTORICAL SOC.").
- `bell_slats`: slats in the foreground at depth 0.7; inside, a brass bell (about 30 cm) at (980, 600) with a rope pull and a bracket.
- `bell_ecu`: the rim with the crack fills the frame.
- `porch_run`: Tess at the crate.
  - States: crate whole, then broken (splinters fly from 509.24); the bell rolled out; the bell struck (535.36) and vibrating.
  - Anchor: `tess_crate`.
- `boot_ecu`: the boot and a slat.

**`caretaker`** (`tv`)
- `wide`: a small clapboard house at (1200, 520).
  - One window at (1260, 520), 160x120, lit warm with a blue TV flicker. The curtain sways once at 70.32 s.
  - A pickup truck.
  - Foreground silhouettes at depth 0.6.

**`cabin_now`** (Cabin 7, our side)

Variants:

| variant | light |
|---|---|
| `flash` | Tess's beam plus moon shafts |
| `flash_low` | the beam aimed at the floor |
| `doorway_glow` | warm pale light pouring from the doorway in the wall, with haze and light rays |
| `red` | lipstick-red glow from the doorway or glass, pulsing slowly |
| `after` | moonlight plus the flashlight lying on the floor |
| `phone_glow` | after, plus a faint red glow from the phone |

Views:
- `wide` (from the door):
  - The back wall spans y 200-860, with dusty floorboards below.
  - The window spans x 780-1100, y 300-560, with a torn screen and moon shafts. The windowsill is at y 560, and Tess's phone lies face up on it at (1060, 556).
  - The wall clock is at (560, 300), radius 44.
  - The left bunk spans x -80..520.
  - Noah's bunk, by the window, spans x 1260-2000. Its bottom mattress is at y 690-780 (bare striped ticking), and the top bunk rail is at y 420-470.
  - The mirror spot is x 1130-1250, y 470-860, leaning on the back wall between the window and Noah's bunk.
  - Cubbies have a masking-tape NOAH label.
  - Anchors: `tess_mirror`, `you_mirror` (kneeling at the mirror), `noah_stand`, `doorway_mid`.
- `cabin_door`: the door creaking open with the beam leading in.
- `under_bunk`: floor level, slats overhead at depth 0.7, the towel-wrapped mirror flat at (980, 760).
- `towel_label`: a faded orange-and-white striped beach towel with a laundry tag reading NOAH in marker.
- `mirror_ots`: the mirror centred at (960, 520), frame 340x820, pane 300x760.
  - You are a back-left foreground silhouette at depth 0.7.
  - Tess is on the right.
- `two_shot`: you and Tess kneeling at the mirror, in profile.
- `sill`: the phone on the windowsill at (960, 600), with dust and a red glint in its black glass. This plants the ending.
- `fingertip`, `hands`, `sleeve`, `cuffs`, `palm`, `towel_fly`, `towel_over` (the towel draped over the mirror; fingertip bumps), `clock` (the clock face fills 70 % of the frame, (960, 540), r 360), `dust_floor` (grazing angle; smooth dust from the door to the bed, no prints), `bunk_low`, `bunk_hit`, `floor_low`.
- `doorway`: the back wall with a narrow doorway exactly the mirror's shape.
  - It spans x 860-1060, y 300-900, with a raw splintered edge.
  - The pale dawn cabin is visible through it. Light rays and haze spill out.
  - The towel lies on the floor at (1000, 920).
  - Anchors: `tess_doorway` (700, 1000), `you_doorway`.
- `floor_end`: the ending.
  - Grown Noah sits on the floor at (1060, 960), h 520 seated.
  - You sit beside him at (700, ...).
  - Tess stands at (1500, ...).
  - The flashlight on the floor at (300, 980) throws its beam across the dust.
  - Anchors: `noah_floor`, `you_floor`, `tess_floor_end`.
- `phone_screen`: Tess's phone fills 60 % of the frame, with a dark screen and dust. States: dust, wiped, 7 tiny lipstick steps, the tiny figure, the face.

**`mirror`** (close-ups of the glass; variants `flash`, `wipe`, `old_cabin`, `queen`, `red`, `dark`)
- **The pane:**
  - white-painted wooden frame, chipped to grey wood (`#d8d4c8`/`#8f8a7e`);
  - silvering spots at the edges (`#9aa0a6`);
  - a 10 % dust film;
  - a fog bloom where breath touches it (197.2 s).
- **Lipstick steps** (`mirror_cu`, drawn on the glass plane at depth 1.0):
  - A zigzag staircase of 7 treads, each 120x14 px with an 80 px riser.
  - Waxy texture: core `#b0283a`, highlight sheen `#d84a5a`, crumbly edges `#8a1e2c`.
  - The top tread is at (1280, 300). Tread k is at (1280 - 110 (k-1), 300 + 80 (k-1)), so the bottom tread (k = 7) is at (620, 780).
  - Smears: each smeared step becomes a down-right drag 40 px long at lower alpha. Counting goes from the top down.
- **The eighth step:**
  - A clean, straight line 6 px thick, `#c63449`, with a faint glow, at (510, 860), 130 px wide.
  - It sits at **depth 1.04**, just behind the glass, so camera moves show parallax: it is on the other side.
  - It draws itself left to right in 0.6 s at 2.56 s and 118.87 s.
  - It never smears. The nail clicks on it.
- **The tilt** (`queen_step_tilt`): the frame and the 7 drawn steps rotate with the mirror (-12 to -14 deg roll). The 8th line and the woman standing on it stay level (counter-rotated).
- **The woman on the eighth step:** feet at (575, 860), 230 px tall at depth 1.04.
- **`old_cabin_refl` / `old_cabin_floor`:** the reflection shows the cabin as it was, in the `theirs` palette, inside the dark frame.
  - Swimsuits drip on the top-bunk rail.
  - The door swings in.
  - Two trails of wet footprints appear one every 0.42 s: one bare; the other alternating shoe and bare foot.
  - The trail ends at Noah's bunk, whose mattress dips.
- **Other views:** `queen_face` and `queen_mouth` (the queen in the dark glass).

**`mirror_world`** (inside the glass; variants `void`, `void_noah`, `red`)
- `stairs`: a staircase descending from the foreground into black (vanishing point at (960, 380)).
  - Red-edged treads, with pale scratch lines on the treads.
  - A railing with balusters on the left.
  - The woman seen from behind at (1240, 1100, h 1000, depth 0.72).
  - `void_noah`: a pale dawn patch far below with tiny Noah.
- `railing`: balusters every 120 px; a small hand comes through at (980, 600).
- `feet`: close on the treads. Your shoes are on the upper step (y 520). Her bare foot is on the step below (y 820).
- `dress`: satin folds with a red glint crawling along them.
- `eye`: a red iris in the dark.

**`cabin_dawn`** (the other cabin at 06:59; variants `dawn`, `dawn_queen`, `dawn_break`)
- `wide` (from the doorway):
  - The window at the back left spans x 420-820, y 260-560. Yellow gingham curtains hang perfectly still.
  - A battery lantern glows on the sill at (700, 556).
  - The towel lies on the floor under the window at (620, 900). The drop rises from 820 and hangs at (620, 700).
  - Noah's bunk spans x 900-1700. Its mattress is at y 690-780, and the top rail at y 400 holds the swimsuits.
  - The dip in the mattress is at (1420, 720). The other shoe sits at (1000, 940).
  - The wall clock at (1550, 230) reads 6:59, with the second hand looping.
  - Anchors: `noah_bunk` (1180, 930, h 560, seated), `you_bunk`, `queen_bunk`.
- `noah_ms`, `noah_cu`, `knot_cu`, `candy`, `towel`, `shoe`, `mattress_dip`, `hands_jerk`, `you_face`, `clock`, `queen_bunk`, `queen_bust`, `queen_face`, `queen_mouth`.
- `window`: curtains and the lantern.
- `window_out`: the view through the window.
  - The lawn with a sprinkler at (900, 760): it comes on, spits twice and dies. It must use the identical animation both times (297.43 and 414.30).
  - The path, the pines, and the mess hall far away at (1450, 600), with a bell on its porch that swings by itself (511.4-531.5).
- `doorway_back`: looking back at the doorway (x 840-1080, y 220-900).
  - The doorway is a dark navy rectangle with Tess in it (anchor `tess_in_doorway`, 960, 900, h 640), aiming her beam into the dawn cabin.
  - Dust drifts in the beam.
- **Variant effects:**
  - `dawn_queen`: the light cools and desaturates near her (a 400 px radial).
  - `dawn_break`: after the real bell, the light flickers (`fx_post` exposure keys), red leaks in at the frame edges, and the lantern stutters.

**`memory`** (variants `memory_day`, `memory_night`, `memory_morning`)

Views:
- `dock`
- `pocket`
- `porch_steps`
- `sprinkler_lawn`
- `cabin_morning`: the cabin 14 years ago, bright, with kid-you in the bottom bunk. Anchors: `kid_bunk`, `kid_sit_dip`, `noah_bunk`.
- `bunk_night`: anchor `bunk_sleep`.
- `watch_cu`: a digital watch LCD, ALM 6:45 changing to 4:45.
- `lipstick_game`
- `card_queen`: a vintage Queen of Spades playing card.
- `kids_game`
- `grin_ecu`
- `polaroid`: Noah by the family car showing his taped fingers.
- `bench`
- `night_window`: moths around a lantern.
- `search_pines`: anchors `search_line`, `director`.
- `kitchen_staff`: anchor `kitchen_line`.
- `kitchen`: the griddle off, a percolator, the bell on its hook.
- `breakfast_table`
- `buses`: yellow buses at noon; anchor `bus_window`.
- `gate_close`
- `storage_shed`
- `path_run`
- `bell_ecu`
- `bell_ring_porch`

Memories are vignetted, slightly soft, with halation, and move like the present (no frozen photos except the polaroid).

**`ui`**: phone screens (section 5). **`rule_mirror`**: the rule card (section 5). **`black`**: pure black.

### 3.3 Props and their states
shots.json carries the full prop state at each shot's start plus any changes inside the shot (`props.changes_in_shot`).

| prop | states |
|---|---|
| steps | 7 drawn; smeared 0 → 1 → 3 → 7 (136.3-138.6, all seven marks on your finger by 138.9); glowing again, wiped top down (618.7-620.0) |
| eighth step | none / present (2.56 in the hook, which is a flash-forward that resets at 19.2; again from 118.87) |
| mirror | not_found → wrapped_under_bunk (71.4) → held_upright (89.1) → tilted (146.3) → towel_over (250.9) → gone and the doorway open (256.9) → mirror_again (615.1) → dark (628.2) |
| towel | wrapped → held → over_mirror → floor → in_hands (616.7) |
| flashlight | off → tess_on (30.95) → tess_running (463.0) → tess_on (551.9) → tess_floor (628.9) |
| candy | none → held_out (320.5) → your_fist (323.7) → a second one offered (503.8) → palm (649) |
| bell | crate → crate_seen → crate_broken (510.1) → fake_ringing (far side, 513.6) → struck and rattling (535.36) |
| tape | on → picking (222.5) → slipped (555.7) |
| shoe | one on, lace loose → reaching for the other (515.1) → lace dropped (539.8) → left behind beside the bed |
| phone | in Tess's pocket → face up on the sill (110.71) → in Tess's hand (674.4) → 7 steps on the screen (685.8) |
| sweatshirt | fits → too_small (559.1) |
| jacket | you → Noah (635.06) |
| drop | falling drips → hanging (337.1) → falling again (346.8) |
| queen | absent → on the eighth step → turned to you → in the doorway → on the bunk → on the step below yours → lifting her foot → absent → in the phone |

---------------------------------------------------------------------------------------------------------------------

## 4. Camera, cutting and transitions (assembler)

### Camera
- `cam.keys` gives `[t, x, y, zoom, roll]` at the shot's start and end. `cam.ease` is `lin` for pushes (already moving on frame 1), `out` for reveals, and `in_out` for whips.
- `cam.shake` is the handheld amplitude in design px/s. The default is 2; handheld shots use 15-26.
- `cam.snap` is `[t, factor, 0.1]`, an optical punch-in.
- `cam.hit` is `[[t, px]]`, a camera jolt.
- Add the police film's uniform post-push of 2 %/s only on UI and insert shots.

### Transitions (`tr`)

| value | what it does |
|---|---|
| `cut` | hard cut |
| `glitch` | 2-frame static into the rule cards |
| `white` | 3-frame white flash (into the dawn world, memories, the flashback) |
| `dissolve` | 0.3 s soft (into and out of memories; 3 % of cuts) |
| `black` | hard cut to black |

`fx_post` lists per-frame effects: static on the face flash, the light flicker after the bell, a white flash on the collar pull.

### Lenses
`lens` is null everywhere (flat cartoon). Use `'lens'` (mild barrel) only if a shot looks too flat when handheld.

---------------------------------------------------------------------------------------------------------------------

## 5. HUD devices

### Captions
`shots.json captions[]` holds 456 one-line chunks: median 5 words, median 1.47 s. They are timed from the word list, with dialogue in quotes.
- Style: the police caption, moved to y 964 at size about 33 (cap height 2.1 % H), uppercase and letter-spaced with a soft shadow.
- Hidden on rule cards and on black.
- Line 39 keeps the word "her", which the narrator does not say (see open problems).

### Header
- **Left:** `CABIN 7 · CAMP CEDAR LAKE  //  INTRODUCTION`, then `RULE n OF 7` after each card.
- **Look:** white at 20 % opacity, with "RULE n OF 7" at 35 %. Cap height 1.0 % H at y 0.052 H.
- **Right:** the in-world clock (`shots[].header.clock_mode`). It shows the time of the side the camera is on.
  - `ours`: 23:57:00 at 19.40 s, then real time. It passes midnight at 199.4. It runs **backward** from 278.97 to 281.81 with a glitch, then continues forward. At the end it reads about 00:08.
  - `theirs`: 06:59:40 + ((t - 297.59) mod 19.48 s). It reaches :59 and snaps back to :40 with a 2-frame glitch. It freezes at **07:00:00** from the real bell (535.36).
  - `memory`: "14 YEARS AGO".

### Tess's countdown
`shots.json counter`: a small dark pill with a red outline at the top right (1760, 118), showing a label TESS and a 46 px number.
- Shown from 289.19 ("sixty") to 609.48. Hidden on rule cards; dimmed to 60 % on memories.
- The count is dilated: one step every 4-6 s, and each step ticks.
- It lands exactly on her calls: 45 (349.86), 20 (502.45), 5 (585.56) and 0 (608.97, the collar pull). Each call pops to 1.35x with a red flash.

### Time card
At 19.43 s (S011): a clock icon, FRIDAY, a big 11:57 PM whose digits flip at 19.67, and the subline CAMP CEDAR LAKE · DEMOLITION TOMORROW. Top left at (110, 170), held 2.6 s.

### Command tags
13 tags. Red bold text in a near-black box with a red outline and glow. They pop in over 3-4 frames with an overshoot, sit at top centre (y 110-140) and land on the word:

WIPE THE GLASS 3.85 · DON'T WAIT 5.55 · LISTEN 10.67 · 7 RULES 122.87 (white) · KEEP IT TO YOURSELF 238.22 · STAY 287.27 · GO 461.08 · DON'T SIT DOWN 493.61 · NO RATTLE 530.92 · HIM FIRST 545.52 · DON'T TURN AROUND 594.88 · TOP DOWN 619.37 · FACE UP 677.44

### Red X
6 of them: 1 red-tint frame, a ring, then two strokes in 0.17 s.

| time | over |
|---|---|
| 6.05 | the rising figure |
| 238.17 | your mouth on the wish |
| 493.56 | the dip in the mattress |
| 530.87 | the perfect bell |
| 603.25 | the shoe |
| 677.39 | the face-up phone |

### Pinned labels
8 white labels with leader lines: 8TH STEP (x2), CABIN 7, THE CRACK, CLEAN GLASS, BLUE MEDICAL TAPE, ONE SHOE, SAME KNOT.

### Rule cards: lipstick on glass
Seven cards (`rule_cards[]`). Each one:

1. 2 frames of static glitch.
2. A flashlight-lit silver mirror pane, 1140x640 at the centre (about 35 % of the frame), tilted -2 deg, slides up in 0.17 s.
   - Gradient `#d9dde2` to `#9aa3ad`, a hot spot and edge vignetting.
   - It is the brightest frame of its section.
3. **RULE ONE...** hand-lettered in waxy lipstick `#c63449` at +1.0 s.
4. The statement written word by word in off-white fog-finger script (`#eef1f3` at 85 %), in sync with `words[]`. `*keywords*` are in lipstick red.
5. A tiny 7-step staircase at the bottom right with step n filled.
6. A finger-wipe smear as the exit. The cut comes 0.15 s after the sentence.
7. LIKE / SUBSCRIBE at the bottom left on cards 1-2.

The background is the shot's `bg` set, live, with post blur 6 and dim .35. No captions.

| card | appears | "Rule" said | title | sentence ends | cut | text |
|---|---|---|---|---|---|---|
| 1 | 129.80 | 130.25 | 130.80 | 133.41 | 133.56 | Count the steps with your *finger*. |
| 2 | 203.53 | 203.98 | 204.53 | 208.17 | 208.32 | If you see her face, *keep your wishes to yourself*. |
| 3 | 269.24 | 269.69 | 270.24 | 273.20 | 273.35 | *Leave somebody* on your side of the glass. |
| 4 | 350.38 | 350.83 | 351.38 | 353.38 | 353.53 | Ask what he *wished for*. |
| 5 | 446.33 | 446.78 | 447.33 | 449.59 | 449.74 | Ring the *real* bell. |
| 6 | 542.03 | 542.48 | 543.03 | 545.07 | 545.22 | Let him go *first*. |
| 7 | 609.48 | 609.93 | 610.48 | 614.56 | 614.71 | *Cover* anything else that can *reflect* the stairs. |

### Phone UI (`hud` entries with type `phone`)

| state | shots | contents |
|---|---|---|
| `message` (new) | S024, 46.0 | MOM thread: "Check the pocket.", then typing dots, then "He always had one of those cinnamon candies in there." |
| `voicemail_list` (new) | S084 | NOAH · 0:09 · JUL 18 |
| `voicemail` | S085 | NOAH, live waveform and play head |
| `calling` → `connected` | S297-S303 | MOM: one ring-back, then connected at 655.20 with a running timer; a live waveform on her line; a flat line during the long pause; a spike on the chair scrape |

---------------------------------------------------------------------------------------------------------------------

## 6. Intensity curve, scares and silences

The intensity curve runs 0-10 (`shots[].intensity`, and `sound_plan.music.intensity` scaled 0-1).

| scene | time (s) | intensity | the scare or silence |
|---|---|---|---|
| hook | 0-19.2 | 6 → **9** → 4 | WIPE THE GLASS hit at 3.92 (one of the 3 loudest bed moments); DON'T WAIT and a red X; the bare foot on the step; premise lines with the bed dipped |
| arrival | 19.2-54.3 | 3-4 | the quietest stretch: time card, the camp, Mom's text, nostalgia |
| porch and bell | 54.3-67.5 | 4-4.5 | the crack; the real cracked bell sound planted in a memory (65.92) |
| caretaker and cabin | 67.5-88.7 | 4.5-5 | sneaking; the towel memories (3.5) |
| steps and game | 88.7-121.0 | 5 → **8** | silence 117.6 → the eighth line draws itself, hit at 118.87 |
| seven rules | 121.0-129.8 | 7-8.5 | punch-ins on "seven" and "fourth"; riser into card 1 |
| rule 1 | 129.8-203.5 | 6 → **9** | silence → the nail clicks on clean glass (143.29); the woman (148.9); footprints after a silence (164.3); silence before the voice (181.6); voicemail grief (4.5); silence → the head turn hit (198.15) |
| rule 2 | 203.5-269.2 | 7 → **9** → 6 | the taped hand; grief (5); the wish with a red X; silence → "You have it" (248.39); the fingers through the cloth (253.83); silence → the towel drops (256.87); the doorway braam |
| rule 3 | 269.2-350.4 | 8 → **9.5** → 3 → 8.5 | the clock backward (281.69); silence → **full face 1** (283.77); white flash into the too-normal dawn (3); the drop rises (335.9); silence while Tess's beam is "perfectly steady" (341.5); 45 |
| rule 4 | 350.4-446.3 | 8.5 → 5 → 4 | silence → the hand jerks (358.4); the half-second grown face (367.8); silence under "a little while" (389.7); silence → the memory of the morning (397.5); the loop (sprinkler and question repeat); silence (422.9); breakfast cancelled |
| rule 5 | 446.3-542.0 | 8 → 4.5 → **10** | urgency; silence → she sits (466.5); **full face 2** (478.28); temptation dip (-18 LU, 481-499); 20; kicking the crate; the **fake perfect bell** in a cleared space (513.56); the deepest silence (533.2, 1.75 s) → the **real bell** (535.36) |
| rule 6 | 542.0-609.5 | 9 → **10** | aging; silence → "Wait, he forgot his shoe" (589.65); DON'T TURN AROUND; silence → **her bare foot on the step below yours** (605.21, the biggest hit of the film); the collar yank |
| rule 7 | 609.5-628.9 | 9.5 → **10** → out | wipes; silence while her foot hangs (625.9); the glass goes dark (628.18); 0.4 s of black |
| ending | 628.9-700 | 2.5 → 5 → **10** → 0 | relief and grief; "Hi, Mom" (the one warm swell); a true pause (661.6); FACE UP with a red X; silence → the click on clean glass (690.19); **full face 3** in the phone (696.91); hard cut to black at 698.62; a faint perfect bell in the black |

The pace builds through content and sound, not faster cutting. The cut rate stays flat. Red rises only after 534 s.

---------------------------------------------------------------------------------------------------------------------

## 7. Sound (summary; the detail is in plan/sound_plan.json)

### Signature sounds
- **The cracked bell:** a clean note, then a thin rattle like a dropped spoon.
  - Planted at 65.92 (a memory) and described at 523.75 and 525.91.
  - The real strike is at 535.36: the loudest hit of its section.
- **The fake bell** at 513.56 is one perfect clean note with a long reverb. It must be the most beautiful sound in the film. One faint perfect note returns in the final black.
- **The nail click on clean glass** at 143.29 and 690.19 is the same sample.
- **The loop sounds** must use identical samples each time, so the audience hears the loop:
  - the sprinkler's two spits (loop_id A/B, at 298.87/299.27 and 415.75/416.23);
  - the drip (332.37 and 346.83);
  - the dawn chorus, which repeats every 19.48 s.
- **The counter** ticks quietly on every step and hits on each of Tess's calls.

### Levels and dynamics
- Music runs the whole time following the intensity curve. The bed sits at -11.5 LU, with an LRA of 17 and 85 % of its energy below 250 Hz.
- The music is an unpulsed D minor drone with an Eb rub. A pulse comes in only at the queen's face (283.8), in rule 5 and in the climax.
- Each rule card gets a riser of +13 LU over 5 s that peaks on the card.

### Voice FX
`sound_plan.voice_fx`, to be added in mix.py:

| fx | lines |
|---|---|
| `below` | Noah under the stairs |
| `queen` | 97, 110, 196 |
| `queen_child` | 249 |
| `phone_child` | 299 |
| `far` | Tess through the doorway |
| `far_outside` | Tess on the porch |
| `phone` | Mom |

### SFX names
- 80 names are used. 24 already exist in `audio/sfx.py`; 56 are new.
- `sound_plan.names.new` gives each new name's description and how to build it: the owner's new Epidemic files first, then the free library, then a synthesis layer.
- Beds: `ambience_camp_night` (replaces the suburban night), `ambience_dawn`, `ambience_mirror`, `ambience_memory`, `room_tone`, `wind_chimes`, `tv_through_wall`, `lantern_hum`.

### Epidemic shopping list for the owner (`sound_plan.epidemic_wishlist`)
The owner offered to download new files. These are the searches that matter most, in order:

1. fingernail tap on glass
2. hand bell / school bell single rings, plus a spoon dropped on a table
3. marker or crayon squeak on glass, and cloth wiping glass
4. lawn sprinkler (impact)
5. water drips on fabric
6. wet barefoot footsteps on wood
7. towel or cloth flap and drop
8. candy wrapper cellophane
9. wooden crate breaking
10. padlock, chain-link gate and chain
11. bunk bed or mattress creak
12. body fall on a wooden floor
13. tape peel
14. flashlight click
15. text message notification
16. screen door
17. chair scrape
18. coffee percolator
19. gravel footsteps, walking and running
20. forest night with crickets and frogs by a lake
21. dawn birds
22. a summer camp morning
23. distant kids laughing; a search party calling
24. a school bus door

Music:
- 2 unpulsed dark drones in D or A minor;
- a music-box or celesta lullaby, nostalgic and detuned;
- sad piano with low strings in D minor;
- a horror tension build with risers and a slow pulse;
- an emotional strings-and-piano reunion cue;
- extra stingers, braams and risers.

The files go into `film/_work/samples/epidemic/{sfx,music}`, and the code picks them up first. Everything has a fallback, so the film can be built before they arrive.

---------------------------------------------------------------------------------------------------------------------

## 8. Who builds what (parallel work)

### Cast (characters.py)
Builds:
- section 2: the new cast, colours, the queen's drawing language and reveal stages, kid proportions, the age morph, fear eyes;
- all new clips with their SFX events;
- the modes (bust, hands, feet, legs, silhouette, lying);
- deterministic replays for a `clip_id`.

Test stills to check first:
- S128 / S212 (the full face);
- S089 (the head snap);
- S137 / S165 (Noah, and the grown face flash);
- S255 (Noah grown);
- S115 (fingers through the towel);
- S276 (her foot on the step below yours).

### Sets (sets.py and the grade presets)
Builds:
- section 3: every set, view, variant and anchor;
- the shared beam, dust and fireflies;
- the mirror system (steps, smears, the 8th step at depth 1.04, the tilt, the reflection, footprints);
- the doorway;
- the dawn loop (sprinkler, drop, clock);
- the grade presets in section 1.

Test stills: S003, S053, S064, S068, S072, S075, S119, S132, S148, S150, S227, S239, S283, S310.

### Sound (audio/)
Builds:
- the new SFX names (`sound_plan.names.new`) with the Epidemic-first rule;
- the beds per `sound_plan.beds`;
- score.py arranged by `sound_plan.music.sections` and events (risers, swells, silences, pulses, the final bell);
- the voice FX;
- the identical samples for `loop_id`;
- mix.py reading `film.cues()`, with sound_plan.json as the reference.

Targets: about 14 transients per minute or more, 5-6 hit events per minute, 1.8 silences per minute of about 1.2 s, and a bed dip of about 15 dB before each hit.

### Assembler (film.py)
Builds `Film(timeline)` from `plan/shots.json`:
- one builder per `type`/`set`;
- `Cam` from `cam.keys`, with snaps and hits;
- characters with Acting built from `chars[].acts`;
- HUD: captions, header clock, counter, time card, tags, red X, labels, rule cards, phone states;
- transitions and `fx_post`;
- `cues()` = sound_plan.json sfx and music events plus the acting clips' own SFX events.

Render budget: at most 0.6 s per frame at 2560x1440 per process.
- The queen's scratch lines re-jitter every 3 frames, so cache 3 versions.
- Keep live layers small and everything static cached.

---------------------------------------------------------------------------------------------------------------------

## 9. The plan's numbers (from `plan/validate.py`)

**Shots:**
- 317 shots, 316 cuts, 27.1 cuts per minute. The reference target is 26; the references measure 24.1 and 28.5.
- Shot length: mean 2.22 s, median 2.14, p10 1.08, p25 1.62, p75 2.83, p90 3.37 (min 0.48, max 5.23). The target is 0.9 / 1.4 / 2.2 / 3.0 / 3.8.
- 9 % of shots are under 1 s, 3 % are over 4 s, and none is over 6 s.
- 83 % of cuts land on a clause start (the references measure 58-68 %), with the picture 0.25 s ahead of the voice. 97 % are hard cuts.

**Motion:** the camera moves in every shot. Pull-outs are 11 % of moving time. Push median 3.0 %/s, p90 8 %/s.

**Time per side:** ours 261 s, theirs 213 s, mirror 93 s, memory 88 s, UI 16 s, cards 28 s.

**HUD:** 13 command tags and 6 red X (1.6 per minute), 8 labels, 31 inserts and UI shots (2.7 per minute). 456 captions (median 5 words, 1.47 s).

**Sound:**
- 400 SFX cues, 74 hit events (6.3 per minute).
- 23 silences (1.97 per minute, median 1.2 s).
- 30 swells (2.57 per minute, 13 s median) plus 9 risers.
- 80 SFX names, 56 of them new.

**Coverage:** all 300 lines are covered, with no gaps or overlaps from 0 to 700.0 s.

---------------------------------------------------------------------------------------------------------------------

## 10. Regenerate and open questions

```
cd "film"
python3 plan/make_plan.py && python3 plan/validate.py
```

**Open questions:**
- **Film length:** the film runs 700.0 s (42,000 frames). The narration ends at 698.58 and the black tail is 1.4 s, about 80 frames more than the ~41,920 in the brief.
- **Invented details:** CAMP CEDAR LAKE (EST. 1962), Cabin 7, FRIDAY, the JUL 18 voicemail and ALM 6:45 → 4:45 on the watch. The watch change implies you set his alarm early. Change any of them in shotlist.py and regenerate.
- **Line 39:** the caption keeps "her" ("sets her phone"), which the narrator does not say. The main session decides.
- **Rule cards:** cards 1, 3 and 4 are shorter than the references' 4.5-5.4 s because our rule sentences are short and the next line follows at once.
- **Approximate times:** acting times inside a shot are planned from word times. Builders may move a clip by up to ±0.1 s to sync with the picture, but rule-card, hit and command-tag times are fixed.
- **Voice FX:** they need small additions to mix.py.
