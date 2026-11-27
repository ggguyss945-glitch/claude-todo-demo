# CAST: the Mirror Steps cast in `characters.py`

The police film's API is kept: `draw`, `draw_bust`, `draw_head`, `draw_hand`, `draw_prop`, `Pose`, `EXPR`, `Acting`.
The police cast still renders. Its lead was renamed **`you_police`**, because `you` is now this film's lead.
Everything is drawn in the 1920x1080 design space.

**v2 (DIRECTION_V2 §3).** The Queen of Spades is redrawn from scratch (section 0 below), the Mirror cast's hands are a
new hand system, and the people got the §3.7 upgrades. v2 sheets are in `_work/cast_v2/`:
`queen_sheet.png`, `queen_thumbnail_test.png`, `queen_vs_references.jpg`, `queen_plan_v2.png` (every Queen entry of
`plan/shots.json`), `you_sheet.png`, `tess_sheet.png`, `noah13_sheet.png`, `noah_grown_sheet.png`, `hands_sheet.png`,
and the gate G1 stills `gate_0284.5.jpg`, `gate_0532.2.jpg`, `gate_0605.8.jpg`, `gate_0606.4.jpg` (`gate_stills.jpg`).
Regenerate: `python3 tools/cast_v2_sheets.py [queen thumb compare plan_queen you tess noah13 noah_grown hands]` and
`python3 tools/queen_gate_stills.py --extra` (restages the v1 shots of those times in the real film pipeline).
The v1 sheets (`_work/cast/`, `tools/cast_sheets.py`) still run. Self-test: `python3 characters.py --selftest`.

## 0. The Queen of Spades v2 (DIRECTION_V2 §3)

A playing-card queen drawn as a real, regal woman in the cast's language: an outline in plum `#2b1a2a` at 0.75x the cast
weight, inner features `#4a2c3a`. All of her is drawn by the `queen_*` functions (section "Queen of Spades v2" in
`characters.py`); `draw`, `draw_bust`, `draw_head`, `draw_hands`, `draw_feet` and `draw_silhouette` route to them.

- **Body.** 1.12x an adult (give her `at` height = 1.12 x the adults' in the shot), head 1/7.5 of her height (`hh` 133),
  long neck, narrow shoulders, cinched waist, arms to mid-thigh, fingers 1.35x. She never breathes or blinks.
- **Four-shape silhouette.** A crown of 5 black spade points on a silver band (centre 0.22 H, then 0.16, 0.12); a black
  lace fan collar standing behind the neck to ear height with 9 ribs and a white lace edge; waist-length straight hair
  from a centre parting (sheen band, dark strands, light highlights, a parting line, two loose strands over her left cheek
  that never move); a bell gown to the floor (hem 1.6x the shoulders, a train behind) with a playing-card border of white
  spade pips between two red lines, a spade brooch with a red stone at the throat, 9 silver buttons.
- **Face (S1, reworked at the gate).** A long oval: high cheekbones, a jaw angle and a pointed chin (`_QSP`), the head
  drawn 0.88x narrow (`_Q_NARROW`), the curtains sweeping over the temples and closing in along the jaw so the face shows
  widest at the cheekbones. Porcelain modelled with a cool contour (`_q_face_model`: temples, sockets, cheek hollows
  under the cheekbones, the jaw, the nose side; light on the cheekbones, bridge, brow and chin), no blush. Almond eyes
  ~0.19 W on the 0.47 H line: grey-violet irises with fibres and two highlights, a smoky plum lid, a heavy tapered liner
  with a wing, 5 curled lashes, a crease; calm stages hood the iris a little. A long fine nose (bridge line, alar wings,
  nostrils, highlight); full lipstick lips `#c63449` with a cupid's-bow light and gloss, the seam at y 55 close under the
  nose; **a black spade beauty mark** under her left eye.
- **Her values are pre-grade.** `QV` skin is `#d0c9d3` (shade `#a89bb2`, light `#e9e5ee`): the v2 grades (contrast ~1.3)
  lift it to the brief's porcelain (~luma 215-235) with the modelling intact; the brief's `#ece6e8` drawn raw blew out to
  white in the film. Face highlight p99.5 measured graded: 230 OURS / 240 THEIRS (dawn_queen_v2) / 232 CLIMAX.
  `tools/cast_v2_sheets.py` grades every cell with its world's v2 preset (`--raw` to skip), so the sheets show film values.
- **S3 (gate rework).** S3a: the stair drawing is the top edge of a deep grin (0.69 W, down toward the chin) with exposed
  pink gums, 14 flat upper teeth hanging tread by tread (a staircase of teeth) and 14 lower teeth, a dark mouth, a thin
  stretched lower lip, cheek folds round the corners. S3b: red irises with bloom, pink whites with 8 branching veins, an
  inflamed lower rim, sunken plum sockets. S3c: lids wide (white round the iris), 4 folds a side plus bunched skin under
  the eyes, 3 cracks, a mascara smudge and 2 glossy black tears an eye (one drips into the grin, one runs to the jaw).
  The S2 drawing is hand-drawn lipstick (`_q_brush_steps`: each tread and riser its own waxy stroke overshooting the
  corner, a darker under-edge, a sheen, crumbs).
- **Hands.** Porcelain, outlined, knuckle creases, long black almond nails with a sheen, the right index and middle
  fingertips smudged lipstick red (with crumbs). The satin sleeve ends in a point over the back of the hand.
- **Feet (gate rework).** Bare, narrow, an arch, tendons; in 3/4 five elongated toes aligned with the foot (big toe in
  front, the rest stepping back), from above (`view='pov'`, `_q_foot_top`) one scalloped toe line with creases. Nails are
  small PALE cold plates (`QV['toenail']`, the black ovals read as eyes; one key to change back). The hem with the pip
  border brushes the ankles.
- **Gown (gate rework).** Satin sheen bands on the skirt and arms, a cool moon rim on the far side of skirt, bodice and
  arms, a pointed stomacher edged in silver, a silver chain girdle with a spade clasp (red stone), a pendant chain to a
  silver spade at the knee (standing), a wider hem band of white pips: the gown reads in wides and silhouettes.
- **`fade_in(t0, dur)`** (new act): not drawn before t0, then fades in (H7: her face arrives as the camera tilts up).
- **Her light.** Cool key from below the front, a red rim `#ff3b5c` on the far side (the plan's queen light dict
  `{key_c, key_from, rim, rim_a, bloom, drain_px}` is read: its `rim`/`rim_a` are hers). Extra keys for special shots:
  `qrim`, `qrim_a`, `qrim2` (a second rim on the near side) and `qsplit=(colour_far, colour_near)` (half one world's
  light, half the other's: H1 in the doorway). The CLIMAX `red` preset reddens her dress and hair a little, never her
  face.
- **Speed (2560x1440).** Full-frame bust about 53 ms (S3c), full body at 900 px about 32 ms.

### Stages (plan field `stage`: `S0 S1 S2 S3a S3b S3c OFF S4`; v1 ints 0-3 map to S0, S1, S2, S3c)
Every stage is a set of continuous pose numbers (`QSTAGES`, `queen_stage(name)`), so a change is a 2-frame snap or a
draw-on: `q_hide` (S0: the hair closes over the face), `q_draw` (the lipstick stair smile), `q_pin` (pinpoint pupils),
`q_split` (S3a: the drawing splits into a grin of 2 x 14 flat human teeth, gums, the lips stretched round it; the lower
edge talks), `q_red` (S3b: red irises with a bloom halo, pink veined whites), `q_full` (S3c: 4 cheek folds a side, 3
porcelain cracks, 2 glossy black mascara tears per eye with drip bulbs, going behind the open mouth), `q_off` (OFF: the
grin drops to a pressed flat line, the steps stay as scars, the red eyes stay), `q_void` (S4: the face below the eyes
stretches 1.35x into a tall glossy void with 6 upper teeth; **Noah13's face floats inside** at 40 % of its width,
lip-synced on the queen's `m_open`, band-glitched by `q_glitch`), `q_widen` (the grin widens), `q_nface` (the phone:
Noah13's face occupying her bust, pixel-sorting into hers as it falls 1 -> 0).
Plan spec: `stage` (or `queen: {stage: ...}`), `face: 'hidden'` / `face_hidden: true` (S0 hair), `seated: true`.

### Her acts (`acts: [t, name, args]`)
| act | what |
|---|---|
| `stage {to, dur, draw_on}` | move every q_* to a stage over dur (0.033 = 2 frames) |
| `split_open` / `smile_split {dur}` | S3a on "back" (479.24) |
| `eyes_red`, `full_face`, `smile_off {dur}` | S3b on "better", S3c, OFF in 2 frames (533.68) |
| `jaw_drop {dur, glitch}`, `void_talk {line, inner, pixel_sort}` | S4 at 589.6; void_talk also lip-syncs the line (249) on Noah's face |
| `draw_smile {dur}` | the stair smile draws itself on |
| `head_snap {deg=130, dur=0.18}` | the head turns; **the hair lags 0.4 s** (`q_hair`), then settles within 60 deg of the body |
| `turn_to_lens` / `head_to_lens {dur=0.25}` | the snap to the lens, eyes locked |
| `talk {line}` | lip-sync on her lips (lines 97, 110, 196: r = 0.88, 0.88, 0.81); a red glow marks her voice |
| `lean_out {dur}` | H1: in from the doorway side, the face growing a little |
| `rise {dy}` | bust: rises dy px into frame; body: straightens out of a stoop |
| `sit_beside` / `glide_sit {to, dur=1.2}` | H2: one eased 1.2 s glide to `to` and the sit, no bob |
| `pat`, `press_through_cloth`, `fingers_curl {amount}`, `reach_shoulder` | hands |
| `climb {steps_per_s}`, `climb_step`, `slide_rail {dx}`, `step_up`, `lift_foot {to}`, `toes_curl` | stairs and feet; body mode shows the lifted bare foot under a raised hem |
| `grin_widen {amount}`, `call_silent`, `drift`, `still`, `hem_sway`, `pixel_sort_in {dur}` | |
She always drifts (tilt about 0.5 deg/s, lean, hem sway): never pixel-identical between frames.

## 1. The easy path: plan specs → rigs

```python
import characters as C
rig = C.CharRig(spec, shot)            # spec = shot['chars'][i] from plan/shots.json, shot = the shot dict
info = rig.draw(pen, t, at=None, light='auto')   # t = film seconds; returns positions (below)
rig.events                              # SFX events of the acting clips [{t, name, gain_db, pan, params, who}]
rig.pose(t)                             # the Pose (e.g. P.beam, P.beam_dx, P.frame_tilt, P.wipe for the sets)
```

### What `CharRig` handles

**Inputs**
- Every `mode`, every `expr` and every act in the plan (`acts`: `[t, name, args]`) is wired up. The self-test builds
  all 428 character entries of the v2 plan. An act that fails is skipped with one stderr line (never a crash); a body
  whose `at[2]` is under 10 (a bust-style scale) is reported on stderr.
- Plan names: `kids` -> `kid_a`, `extras` -> `searcher`, `mom` -> `mum` (hands / arm only); `tess_kid` is a cast entry.
- `clip_id` may sit on the spec or (v2 plans) in an act's args (`talk {line, clip_id}`): the rig replays the first
  shot carrying it frame for frame (`breakfast_A`: S278 replays S214, max difference 0).
- `at` may be an anchor name, such as `noah_bunk`, `queen_bunk`, `tess_gate`, `noah_floor`, `bunk_sleep`,
  `kid_bunk`, `search_line` or `adult_legs`. Resolve it in `sets.py` and pass `at=[...]`; `rig.draw` raises on a
  string.
- `at` formats per mode:
  - `body`, `legs` and `silhouette`: `[x, y_feet, height(, depth)]` (height in design px; the queen 1.12x the adults,
    grown Noah 1.08x yours, Noah13 about 0.8x).
  - `bust`: `[cx, cy, scale]`. `scale` 1 means a 600 px head.
  - `hands` and `feet`: `[x, y, size]`. For `hands`, `size` is the hand length; for `feet`, it is the shin-and-foot
    height.
  - `lying`: `[x, y, body length]`.

**Lighting**
- With `light='auto'`, `rig.draw` uses `spec['light']`. When the spec has no light it uses `default_light(shot)`:
  - `theirs` gets `dawn`;
  - `memory` gets none;
  - from 534.4 s, `ours` and `mirror` get `red`;
  - with Tess's flashlight on, the other characters get `flashlight`;
  - the queen gets a red rim;
  - anything else gets `moon`.

**Defaults set from the shot's `props`**
- Tess holds the flashlight, with `beam` 1 when the prop is `tess_on` or `tess_running`.
- Noah's tape is on until `slipped`.
- Grown Noah wears your jacket from 635.06. From then on, `you` is drawn in the henley.
- Your left hand is a fist from 323.65 to 651.

**Queen stages and faces**
- See section 0. `stage` is a name (`S0`..`S4`, `OFF`) or a v1 int; the v1 `hair_over` / `eye_gap` / `m_gap` fields are
  no longer drawn.

**Replays (`clip_id`)**
- A rig with a `clip_id` replays its origin shot frame for frame:
  - `breakfast_A`: S186 replays S142 (max difference 0).
  - `loop_reset`: S161 replays S137 (305.72).
- Change the origins in `CLIP_ORIGIN`.

**Seeds and timing**
- Seeds are per shot and character, and deterministic. Blinks and idle motion repeat when a frame is re-rendered.
- Contact acts land on the plan time: `step_up` lands at t, `nail_tap` clicks at t, `strike` hits at t + 0.14 and
  `grab` grips at t + 0.18. Builders may shift a clip by up to ±0.1 s.

### What `rig.draw` returns
- `body`, `bust`, `legs` and `lying` return `head` (the design point), `head_px`, `roll` and `hands` (`{side: (x, y)}`,
  where -1 is the character's right and +1 the left) and `B` (the Body rig).
- `hands` returns `tip` (fingertip per hand `'r'` / `'l'`: sync lipstick lines, smears and the nail click to this),
  `wrist` and `prop`.
- `feet` returns the sole points `r` and `l`.

### Lower-level calls

| call | what |
|---|---|
| `draw(pen, who, x, y_feet, height, pose, detail, light, t)` | full body (returns Body; `.info` as above) |
| `draw_bust(pen, who, cx, cy, scale, pose, detail, light, t)` | head and shoulders, real arms and hands |
| `draw_head(pen, who, cx, cy, size, pose)` | head only |
| `draw_hands(pen, who, x, y, size, pose, detail, light, t, main='r')` | hand insert; `main='l'` puts the main hand on the character's left |
| `draw_feet(pen, who, x, y, size, pose, detail, light, t)` | feet insert, low 3/4 view on a step edge |
| `draw_legs(pen, who, x, y_feet, height, pose, ..., cut=0.5)` | lower body, cropped at the waist |
| `draw_silhouette(pen, who, x, y_feet, height, pose, light)` | dark shape with a rim offset toward the light |
| `draw_lying(pen, who, x, y, size, pose, ..., facing=1, hang_arm=False)` | in a bunk: pillow and blanket that breathes; `hang_arm` = Noah's watch wrist |
| `draw_mode(pen, who, mode, at, pose, light, detail, view, main)` | the dispatcher `CharRig` uses |
| `draw_prop(pen, name, x, y, size, angle)` | props (§5) |
| `timeline_line(i)` | line `i` of `_work/align/timeline.json` |
| `voice_envelope()` | the envelope of `_work/align/vo_en.wav`, cached in `_work/cache/` |

## 2. Cast (`CAST` keys)

| key | design |
|---|---|
| `you` | 27. Looks like their dad: square jaw, receding temples, stubble with fine dots, faint forehead lines, brown irises. Olive canvas work jacket with a corduroy collar (lifts with `collar_pull`), grey henley, jeans, brown boots. No scar, no ring. |
| `tess` | Auburn hair: a side-swept fringe and a low ponytail brought over her left shoulder. Freckles, level brows, small mouth with muted lips. Burnt-orange rain shell (zip, stand collar, nylon sheen), grey cargo pants, boots. Holds the flashlight. Blinks last 1-2 frames. |
| `noah13` | Kid proportions: head about 1/5.5 of his height. Messy mop with a crown cowlick, freckles, warm skin. **Gap between the front teeth** whenever the teeth show (smiles, talk). Green CEDAR LAKE sweatshirt with a kangaroo pocket, plaid pyjama pants, one white sneaker (left) with a loose lace, the right foot bare. **Blue tape** on the right middle, ring and little fingers, with a lifting edge (`tape`, `tape_peel`, `tape_slip`). |
| `noah_grown` | The same face at 27: longer jaw, stubble, bags, wet eyes, the gap teeth. Hands 1.25x. The sweatshirt is two sizes too small: the hem is above the waistband (a skin band shows), the cuffs sit halfway up the forearms and there are stretch lines. Pyjamas end mid-shin and both feet are bare. `jacket_on` drapes your jacket over his shoulders. **Age morph:** `age_body` and `age_face` (0 to 1) interpolate everything from `noah13`. |
| `queen` | **v2, section 0.** (The v1 scratch-line queen and its shark-tooth mask are retired.) |
| `you_kid` | You at 10-11: big head and eyes, mop hair, blue/white striped tee, shorts, sneakers. |
| `tess_kid` | Tess at 10: auburn ponytail, freckles, orange tee, shorts (memory, the barefoot run). |
| `counselor` | Teen in a teal camp-staff tee with a whistle lanyard. |
| `kid_a`, `kid_b`, `kid_c` | Kid variants. The plan's `kids` maps to `kid_a`. |
| `director`, `cook`, `searcher`, `adult` | Extras. The plan's `extras` maps to `searcher` (`WHO_ALIAS`). The cook has an apron. |
| `officer`, `officer2`, `double`, `mum`, `you_police` | The police film's cast, unchanged. Mom's phone avatar is `mum`. |

**Eyes (v2).** The new people have almond eyes at rest (`eye_h`; Noah13 0.74) with a real iris (`iris_k` of the eye:
a dark limbal ring, a lighter ring round a 0.42 pupil, fibres at CU) and **two highlights** (0.3 and 0.12 of the iris).
Fear (REF rule 9): the eyes become white discs as `pose.wide` rises and the iris shrinks toward 0.3 (`fear_eyes`).
`fear_wide` caps it: grown Noah (`fear_wide` 0.35, `fear_eyes` 0) keeps **brown, human eyes** in fear (no possessed
discs).

**People upgrades (DIRECTION_V2 3.7).**
- **You:** every POV hand wears the olive canvas sleeve `#4a5038` with the stitched cuff band `#33382a` (hands inserts and
  the phone UI hand, `POV_SLEEVE`); the back of your head (turn 2) has hair to the nape; the **left candy fist** from
  323.65 s draws the red wrapper twisting out of both ends of the fist (body, bust and inserts); kneel is a real kneel
  (one knee down, the other foot planted), reach / recoil / yanked_back read in 3/4 views (their motion is toward the lens).
- **Tess:** `run` is a run cycle (0.27 s per step, flight, knees high, arms pumping, the beam hand swinging, lean);
  `reach_grab {foreshortened}` and `grab_collar` drive a **foreshortened orange arm** in the hands insert (`ir_fore`,
  coming from the doorway above) and `base_prop 'collar'` (your corduroy collar under her fist).
- **Noah13:** almond eyes with two highlights; **the gap teeth show on every line he speaks** (`talk_line`); seated on a
  bunk his feet stay on the floor when the mattress top is about 0.25 x his height above `y_feet`; **one tape design**
  (`draw_tape` = `_tape_on`): middle, ring and little fingers bound together in two blue bands `#4d8fd6` with sheen
  `#8fc0f0`, the edge lifting on the little-finger side, in every mode (open, palm, fist, grip, point); `tape_slip`
  slides the bands off.
- **Grown Noah:** brown eyes, a longer, squarer adult face (heavier brows, darker stubble, forehead lines); the age
  morph (`age {part: face|arms}`, H5) interpolates all of it from Noah13 and reads across 2.7 s.
- **Hands (all of the Mirror cast):** the v2 hand system `_hand2` (section "hands v2"): views `back`, `3q`, `palm`;
  shapes `open`, `relaxed`, `pat`, `flat`, `palm`, `claw`, `reach`, `point`, `pinch`, `fist`, `grip` (`mitt` now draws
  `relaxed`); palm, knuckle line, tapered 3-phalanx fingers that foreshorten when curled, thumb with the thenar,
  knuckle creases, nails, tendons, palm lines and pads, per-character skin and proportions (kids smaller, grown Noah
  1.25x). The police cast keeps its own hands.

**Grief reads human.** Brows go up at the inner ends, the lids are heavy, the eyes wet, the mouth pressed and
trembling, and tears stop at the jaw.

## 3. Expressions (`EXPR`)
- **New:**
  - `grief`, `dread`, `tense`, `tempted`, `resolve`, `wonder`, `relief_cry`;
  - `brave`, `recognise`, `half_smile`, `puzzled`;
  - `calm_kid`, `grin_kid`, `laugh`, `listening`, `relief`, `shy`, `sleep`, `strain`, `worried`;
  - `hopeful`, `shaken`, `happy`, `sly`, `sure`, `giggle`.
- **The queen (v2):** her face comes from the stage. `queen_still`, `queen_stare`, `queen_soft`, `queen_grin`,
  `queen_blank`, `queen_full`, `queen_drawn`, `queen_grin_red`, `queen_off`, `queen_void` only lock the eyes and
  still her; `queen_call` opens the mouth (calling).
- **Kept from the police film:** `neutral`, `fear`, `shock`, `shout`, `scream`, `sad`, `angry` and the rest.

## 4. Acting clips (`Acting` methods; times are film seconds)

All clips are eased and layer over breathing, blinks and saccades. Each one drives both the rig's arms (`hl_*` /
`hr_*`) and the inserts (`ir_*` / `il_*`, `base_prop`, `fl_*` / `fr_*`), so the same act works in every mode.
The clips marked **(SFX)** return events, using the names in `plan/sound_plan.json`.

**Speech and face**
- `talk_line(t, line)`: lip-sync on the real envelope. The self-test measures r = 0.85, 0.88 and 0.81 on lines 125,
  97 and 196.
- `talk_silent(t, dur)`, `shout_silent`, `mouth_open`, `mouth_open_close`.
- `whistle_s`: teeth together, so the gap shows.
- `smile`, `half_smile`, `laugh`, `laugh_dies` (SFX breath).
- `tears(t, amount)`, `swallow`, `tremble(t, amount)`: the lips, the head and the hands shake (`hshake`).
- `look_at(t, x, y, head_xy, lost)`: the plan's look target in design px.
- `nod`, `head_lift`, `look_up`: the gap-tooth smile.
- `face_flash(t, dur, flicker)`: grown Noah's face with 2-frame flickers.
- Kept from the police film: `expr`, `stare`, `head_tilt`, `snap_turn`, `lean_in`, `blink`, `flinch`, `freeze`,
  `life`.

**Body**
- `stand_up`, `kneel`, `step_back`, `fall_back` (SFX body_fall), `stumble`, `run`, `sneak`, `scoot`, `rock`,
  `shift_weight`, `squeeze_through`, `step_over`, `step_through` (SFX bare_foot_step), `fall_through`.
- `walk` (police film). For gravel, the bridge renames the SFX to `footsteps_gravel`.

**The queen** (v2 list in section 0)
- `still`: no breath, no blinks.
- `head_snap(t, deg=130, dur=0.18)`: overrides the head yaw and holds; a back view shows the face over the shoulder.
- `smile_off(t)`: the smile goes in 2 frames to `queen_blank`.
- `call_silent`.
- `sit_beside(t, dur)`: one smooth inhuman motion, no bob.
- `pat(t, n, spacing)`.
- `press_through_cloth(t, depth)`: in the hands insert, `ins_k` grows the hand toward the lens.
- `lift_foot`, `toes_curl`.
- `step_up`: lands at t.
- `climb(t, steps_per_s)`: dx and dy by `run` and `rise` x height per tread.
- `hem_sway`: the hem moves while she does not.

**Tess**
- `run` (v2 run cycle), `reach_grab {foreshortened}`, `hang_open {prop}` (the padlock on the hasp), `fade_out`.
- `flashlight(t, aim, sweep, on, raise_)`: `pose.beam` and `pose.beam_dx` tell the sets where the beam points; the
  lens is at the right hand.
- `jingle`, `unlock`, `pull_chain`, `finger_to_lips`, `set_down` and `pick_up` (phone), `rub_fingers`.
- `grab_shoulder`, `grab`, `grab_collar`, `yank`, `shove`, `snatch`.
- `throw` (towel), `wind_up`.
- `strike` (SFX bell_cracked and impact_hit at t + 0.14).
- `kick` (SFX crate_break).
- `wipe_glass(t, strokes, dir, sleeve, prop)`: `pose.wipe` is the stroke progress.

**You**
- `open_hand` (the palm already open: candy and mark), `give {prop}` (passes the phone), `step_down` (a boot onto tread 1).
- `unwrap`.
- `grip_frame(t, tremble, fail_open)`: the fingers twitch open and clamp back.
- `tilt_frame(t, angle)`: sets `pose.frame_tilt`.
- `touch_glass`, `nail_tap`, `smear`.
- `take_hand`, `pull_hand`.
- `take` (candy, towel), `fist(slow, squeeze, fail_open, tremble)`, `open_fist`: the candy lies on the palm.
- `rub_thumb`, `reach(t, to)`, `slide_out`, `give_jacket`, `yanked_back`.

**Noah**
- `shrug`; `tie_loop`'s `phase` may be a name (`'loop_reset'` = the start of the cycle).
- `tie_loop(t, period=2.4, phase)`: the same knot. In the insert, two hands hold the lace over the sneaker; in a body
  shot he sits on the bunk with his left foot up. The cycle is deterministic.
- `draw_step`: the lipstick stroke.
- `withdraw`, `wave`, `pull_from_pocket`, `hold_out` (candy on the palm), `wring`, `breathe_sleep`, `tap_rail`.
- `reach_through`, `fingers_flex`, `peel_tape`, `slip_tape`: the tape ring stays (`base_prop 'tape_ring'`).
- `drop_lace`, `swat`, `pat_knees`, `eat`, `pulled_along`.
- `hand_jerk`: in 2 frames.

**Grown Noah**
- `age(t, t1, part='arms'|'face', start)`.
- `look_at_hands`, `stand_hit` (SFX wood_thud).
- `cover_ears`: the backs of the hands over the ears, eyes squeezed.
- `hold_collar`, `hand_out`.
- `phone_to_ear` (police film).

**Memory**
- `whisper` (the kids' dare), `wrap_tape` (Mom's hands winding the tape), `write` (an officer's notebook).
- `wake_up`, `wake_squint`, `press_button` (watch_beep), `pull_socks`, `drop_prop`, `ring_bell`, `dare`,
  `hand_over_mouth`, `call_out`.

## 5. Props (`draw_prop` names, also hand props)
- **New:** `lipstick` (glowing bullet), `candy_red`, `wrapper`, `keys` (carabiner, padlock key, CABIN 7 tag),
  `padlock`, `flashlight`, `phone_dark` (red glint), `bell` (brass, cracked rim), `clipboard`, `shoe`, `tape_ring`,
  `towel` (faded orange stripes), `watch`, `lace`, `mirror_small`.
- **Kept from the police film:** `card`, `pen`, `notebook`, `key`, `phone`, `phone_back`, `glasses`, `mic`, `photo`,
  `badge`, `radio`.

## 6. Lighting (`light=`)

A light is a preset name or a dict with `rim`, `rim_a`, `side`, `key` (-1 night to +1 warm), `flash` (a warm
hot spot on the figure), `under` (a colour lighting from below), `tint` and `tint_k`, and `sat`.

| preset | look |
|---|---|
| `flashlight` | Tess's warm key: rim `#fff2d6`, hot spot `#ffe2b0` |
| `moon` | `#9fb6ff` rim, night key |
| `dawn` | flat cool-white rim, saturation 0.72 ("too normal") |
| `red` | lipstick rim from one side, red tint, dark under-light |

- **Fast path.** A light with only key and rim keys the palette (cloth, hair, skin) and adds no layer. Any other light
  uses one bounded layer with a colour matrix, with the hot spot and under-light painted src-atop.

## 7. Speed (2560x1440, one process, best of 6, shared machine)

v2: the queen's full-frame bust about 53 ms (S3c, 1.15 scale), her full body at 900 px about 32 ms; people's busts
23-37 ms. `Ctx.glow` now caches one gradient image per colour and puts the (animated) alpha on the paint (no cache
misses for animated glows, same pixels).


| what | time |
|---|---|
| full body at 900 px tall | 21-23 ms |
| bust at scale 1 (fills the frame), moon or rim light | 24-45 ms (the queen ≈ 45 ms: scratch lines) |
| bust with `flashlight`, `dawn` or `red` (layer) | ≈ 80 ms |
| hand inserts | 30-80 ms (`grip_frame`, two hands, is the most) |
| feet | 23-38 ms |
| silhouette | ≈ 45 ms (drawn twice) |
| lying | ≈ 25 ms |

## 8. Notes for the builders

**Sets and anchors**
- Sets own the anchors (`noah_bunk` and the rest). The cast sheets use guesses, so check the seated and lying poses
  against the real bunk.
- The towel and cloth over the queen's hand (S115/S116) is the sets' job. Drape it over `info['tip']` and the hand
  outline, because the hand grows toward the lens through `ins_k`.

**Lipstick and glass**
- Lipstick lines, smears and taps: use `info['tip']['r']` from the hands insert, at every frame.

**The beam**
- Use `pose.beam` and `pose.beam_dx` from `rig.pose(t)`, and `info['hands'][-1]` for the lens.

**For the assembler (v2)**
- `pose.alpha` < 1 fades a character (`fade_out`); `draw_mode` handles it.
- film.py does not dim the queen under bright grades (`rig.who != 'queen'`), so with the v1 doorway / climax grades her
  face blooms toward white (see `gate_0606.4.jpg`); keep her the brightest value but cap it (luma about 230-245).
- Queen in the phone: draw her bust inside the screen clip; `pixel_sort_in` at 697.95 handles Noah13's face -> hers.
- H7 (605.2): you `feet` with `pov: true` (boots from above) and the queen `feet` `view: 'pov'` (her foot on the tread
  below, toes at you, the pip hem); the tilt up to her face is a `bust` (or a `body` with a real height, see the report).
