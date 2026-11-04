# CAST: the Mirror Steps cast in `characters.py`

The police film's API is kept: `draw`, `draw_bust`, `draw_head`, `draw_hand`, `draw_prop`, `Pose`, `EXPR`, `Acting`.
The police cast still renders. Its lead was renamed **`you_police`**, because `you` is now this film's lead.
Everything is drawn in the 1920x1080 design space.

Sheets are in `_work/cast/cast_{you,tess,noah13,noah_grown,queen,queen_scary,memory}.png`. Regenerate them with
`python3 tools/cast_sheets.py [name...]`. Run the self-test with `python3 characters.py --selftest`.

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
  all 264 character entries.
- `at` may be an anchor name, such as `noah_bunk`, `queen_bunk`, `tess_gate`, `noah_floor`, `bunk_sleep`,
  `kid_bunk`, `search_line` or `adult_legs`. Resolve it in `sets.py` and pass `at=[...]`; `rig.draw` raises on a
  string.
- `at` formats per mode:
  - `body`, `legs` and `silhouette`: `[x, y_feet, height(, depth)]`.
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
- `stage` 0, 1, 2 and 3 and `face` `hidden` or `mouth_only` set `hair_over`, `eye_gap` and `m_gap`.
- Queen feet shots that have a `toes_curl` act show a single foot seen from above, with no hem.

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
| `queen` | Drawn in a different language: **no outline**. Edges are pale `#d9dee6` scratch lines and the face features are dark etched scratches, re-jittered every 3 frames (`seed = frame // 3`). Long neck (+42 body units), fingers 1.4x long, toes too long, pale blue-grey skin, sunken sockets, red irises with a glow, pinpoint pupils, veins. Lipstick `#c63449` carries the widest glow (`#ff4060`). Straight black hair from a centre parting hangs with gravity whatever the head tilt. Black high-collar satin dress to the floor with a sheen. Bare feet with tendons and cold dark toe tips. She never breathes or blinks; `life` is 0. |
| `you_kid` | You at 10-11: big head and eyes, mop hair, blue/white striped tee, shorts, sneakers. |
| `counselor` | Teen in a teal camp-staff tee with a whistle lanyard. |
| `kid_a`, `kid_b`, `kid_c` | Kid variants. The plan's `kids` maps to `kid_a`. |
| `director`, `cook`, `searcher`, `adult` | Extras. The plan's `extras` maps to `searcher` (`WHO_ALIAS`). The cook has an apron. |
| `officer`, `officer2`, `double`, `mum`, `you_police` | The police film's cast, unchanged. Mom's phone avatar is `mum`. |

**Fear eyes (REF rule 9).** The new people have almond eyes at rest (`eye_h`). These become white discs as
`pose.wide` rises, and the iris shrinks to a dot (`fear_eyes`).

**Grief reads human.** Brows go up at the inner ends, the lids are heavy, the eyes wet, the mouth pressed and
trembling, and tears stop at the jaw.

## 3. Expressions (`EXPR`)
- **New:**
  - `grief`, `dread`, `tense`, `tempted`, `resolve`, `wonder`, `relief_cry`;
  - `brave`, `recognise`, `half_smile`, `puzzled`;
  - `calm_kid`, `grin_kid`, `laugh`, `listening`, `relief`, `shy`, `sleep`, `strain`, `worried`;
  - `hopeful`, `shaken`, `happy`, `sly`, `sure`, `giggle`.
- **The queen:**
  - `queen_still`, `queen_stare`;
  - `queen_soft`: a closed red smile with dead eyes;
  - `queen_call`: the jaw past natural;
  - `queen_grin`: a 0.8-width grin, 2 rows of 18 small separate teeth, lipstick smeared up the cheeks;
  - `queen_blank`.
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

**The queen**
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
- `flashlight(t, aim, sweep, on, raise_)`: `pose.beam` and `pose.beam_dx` tell the sets where the beam points; the
  lens is at the right hand.
- `jingle`, `unlock`, `pull_chain`, `finger_to_lips`, `set_down` and `pick_up` (phone), `rub_fingers`.
- `grab_shoulder`, `grab`, `grab_collar`, `yank`, `shove`, `snatch`.
- `throw` (towel), `wind_up`.
- `strike` (SFX bell_cracked and impact_hit at t + 0.14).
- `kick` (SFX crate_break).
- `wipe_glass(t, strokes, dir, sleeve, prop)`: `pose.wipe` is the stroke progress.

**You**
- `unwrap`.
- `grip_frame(t, tremble, fail_open)`: the fingers twitch open and clamp back.
- `tilt_frame(t, angle)`: sets `pose.frame_tilt`.
- `touch_glass`, `nail_tap`, `smear`.
- `take_hand`, `pull_hand`.
- `take` (candy, towel), `fist(slow, squeeze, fail_open, tremble)`, `open_fist`: the candy lies on the palm.
- `rub_thumb`, `reach(t, to)`, `slide_out`, `give_jacket`, `yanked_back`.

**Noah**
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
