# CAST: "If The School Bus Stops At Midnight... DON'T GET ON"

The cast lives in `characters.py`. This film's cast and staging tools are in `characters_bus.py`, which `characters.py`
runs in its own namespace at import, after `characters_bunny.py` and `characters_doctor.py` (see `BUS_API`). Use
everything as `import characters as CH`. The older casts are unchanged; this film's people have their own ids.

- **Self-test:** `python3 characters.py --selftest` runs the older films' checks, then this film's (`_selftest_bus`):
  every id in 6 views full and bust; his proportions (legs 55 %, crown 244 cm, fingertips at the knee, hat 92 cm leaning
  12 deg); no lip sync and no blinks (a head bob on his lines); a 1400 px stretching reach (0 px miss); the hat crushed
  under 2.35 / 2.0 / 1.6 m ceilings; the tape skip (hard cut, one stutter frame back, tear, events); feet on the floor
  standing / bent / under a ceiling; `lean_to` (grin 28 cm from Mina's eyes); the crossing-guard hold (11 px); red
  pixels 0.005 % (the STOP pin only); Mina's foot onto the step.
- **Sheets:** `python3 tools/cast_sheets.py [names]` -> `_work/cast/`: `ws_turn`, `ws_mood` (beside the owner's refs),
  `ws_limits` (every hard limit, measured), `ws_states`, `ws_head`, `ws_creepy` (doorframe peek with half a face and one
  glove, peephole fisheye, frosted glass, amber up-light, near darkness, far silhouette in a bus door, the 1994 TV, down
  and down), `lineup`, `turn_family`, `turn_others`, `faces_mina`,
  `faces_sami`, `faces_della`, `faces_others`, `props`, `props2`.
- **Acting clips:** `python3 tools/cast_clips.py [names] [--strip-only]` -> `_work/cast/clips/<name>.mp4` + `_strip.jpg`
  (44 clips, 960x540, 60 fps); `clips.json` holds sound events and the contact report. Scenery there is a stand-in.

## Who's who (draw height = `CH.height_px(who, px_per_m)`)
| id | look | notes |
|---|---|---|
| `whistle` | **MISTER WHISTLESTOP** (original; the bible's spec, head redesigned 18 Nov to read as a creepy furry CAT mascot). 2.44 m to the crown, legs 55 %, narrow torso, arms to the knees, a predator's forward hunch (rounded shoulders, neck pushed forward, head tilted 7 deg). THE HEAD: a big furry cat-mascot costume head, about 1/5 of his height (41 cm crown to chin, 47 cm across the cheeks, ~55 cm with the fur): a cat skull with broad flaring CHEEK RUFFS (jagged fur tufts anchored in 3D, so they never crawl when he turns), tall pointed ears with tip tufts and dusty pink-grey insides (a TICKET-PUNCH HOLE through the left one), a tabby crown with dark stripes running down the forehead into the off-white matted face (yellowed, stained edges), layered cheek fur, fur strokes everywhere; a MUZZLE: two puffy whisker pads with follicle dots, a small dark triangular cat nose, long pale whiskers with a dark edge (two bent, one snapped); painted almond CAT EYES (sickly yellow, thick dark rims flicked up, tiny pinprick pupils, his left one higher, a hard glint, no lids, never blink); THE GRIN: a cat's mouth stretched from under the whisker pads up into the cheeks, dark inside, a flat row of too many white teeth with small canines and a short lower row, corners dug into the cheeks (never moves; slips out of register only at the defeat). Off-white chest ruff under the bow tie, tabby fur tufts at the wrists, a furry tabby tail hanging straight. A 92 cm stovepipe in faded school-bus yellow with TWO helical black hazard bands (diagonal from every side), dented halfway, ragged brim, leaning 12 deg to his left. Mustard driver jacket (short sleeves; oval WHISTLESTOP patch, brass buttons), BLACK bow tie with a red STOP-sign pin, silver whistle on an orange lanyard, white gloves with four segments per finger, too-short trousers, long worn shoes. | Own 3D rig in cm (`_ws_rig`), any yaw, `ws_elev` for low angles. `whistle94` = the 1994 host: clean bright colours, hat nearly upright. Never walks, never lip-syncs. |
| `mina` / `mina_bare` | **Mina, 13** (narrator): dark low ponytail, brown eyes, oversized grey-green hoodie over plum pajama bottoms, socks (`_bare`: barefoot for the chase). | fear, hush_fear, resolve, guilt, kind_ask, tempted, terrified_call, relief, tender. |
| `sami` / `sami_torn` | **Sami, 6**: round face, gap-toothed proud grin, green dinosaur pajamas with a spiked hood and a tail to the floor (`_torn`: half the tail ripped off, frayed). Props `rex`, `walkie`, `dino_pack`. | proud_grin, shout_here ("HERE!"), sleepy, dazed, cry. |
| `della` | **Grandma Della, 63**: warm brown skin, grey curls under a burgundy knit cap, reading glasses on a cord, navy driver jacket open over a cream sweater, white DELLA name tape. Props `keys`, `maglite`, `cell`, `broom`. | warm, calm_firm, set_jaw, grim_drive, shout, tender, whisper. |
| `theo` / `theo_color` | **Theo** (1994, 12 forever): yellow raincoat with black toggles, hood down, a 1994 side cut. `theo` faded and desaturated (nobody sees him); `theo_color` after three o'clock. | lonely, kind_smile ("Hi, Mina"), brave, shout_here. |
| `new_girl` | The new girl (~11): pink hair clip, mustard cardigan, oversized plain `backpack` with NO name. | lonely -> kind_smile. |
| `kid94_a/b/c` | 1994 studio kids in bright early-90s hoodies; `name_card` with `pose.card_text` ('NAME|SCHOOL|BUS'). | proud_grin, lock on the lens. |

Heights: Whistlestop 2.44 (+0.9 hat), Della 1.63, Mina 1.57, new girl 1.42, Theo 1.38, 1994 kids 1.30, Sami 1.16.

## Mister Whistlestop: staging (every beat: he moves, closes, reaches, grabs)
```python
a = CH.Acting('whistle', seed=1, height=CH.height_px('whistle', ppm)).place(x, floor_y)
a.unfold(t0, 2.6)                          # out of the bus door like a ladder: knees, waist, neck, hat ('ws_unfold_clack' x4)
a.tape_skip([(t, dict(x=, y=, h=, turn=, ...)), ...])   # every flicker: cut closer, 1 stutter frame, tear ('tape_skip')
a.curl_door(t0, side, edge_xy)             # gloves curl round a doorframe; pose ws_hands_front=3 + CH.draw_whistle_hands on top
a.bend_double(t0, ceil_y)                  # indoors: hat crushed/folded on the ceiling, bent double
a.walls_flat(t0, left_xy, right_xy)        # gloves flat on both hallway walls
a.lean_to(t0, (mina, 'eyes'), gap=30)      # "down, and down": solved waist bend + crouch, in slow beats
a.reach_far(t0, side, target, dur=2.4)     # the arm stretches (down the aisle to Theo's shoulder)
a.hold_child(t0, side, sami, sami_side)    # like a crossing guard (the child reaches up)
a.grip_small(t0, side, mina, mina_side)    # the glove folded small round her fingers, too tight
a.walkie_to_grin(t0, side)                 # her walkie pressed to the grin
a.blow_whistle(t0, 'two' | 'long', side)   # fweet-fweet / one long blast ('whistle_two' / 'whistle_long')
a.snap_glove(t0, side, target)             # snaps shut on fabric ('glove_snap'); then a.ws_hold(t, side, 'tail_piece')
a.head_backwards(t0)                       # 180 deg in three ratchet ticks ('neck_ratchet')
a.clipboard(t0, 1) ; a.punch(t0) ; a.write_line(t0, t1)   # roll call; click-clack; a line through a name
a.host(t0, t1)                             # the 1994 presenter
a.say([(t0, t1, text)]) / a.talk(...)      # head bob only: the grin never moves
a.defeat(t0)                               # grin slips out of register, tracking tears, rewinds away ('tape_warble', 'tape_rewind')
a.look_at(t0, target, snap=True)           # painted eyes: the head turns (slowly, or one hard tick)
```
Light keys he understands (the `light` dict of `CH.draw` / `draw_bust`): `rim`, `rim_a`, `side`; `under` + `under_a`
(lit from below: a phone, the dash, sodium amber); `dark` 0..1 (near darkness: the figure sinks into the dark and only
the painted eyes and the teeth catch light; `dark=1` = a black silhouette with glinting eyes and grin).
Points: `a.where(t, part)` with 'head', 'eyes', 'mouth'/'grin', 'chin', 'crown', 'hat_top', 'chest', 'hand_l/_r',
'tips_l/_r', 'wrist_*', 'elbow_*', 'shoulder_*', 'knee_*', 'foot_*'. Close-ups: `CH.draw_bust(pen, 'whistle', ...)`.
Props stay in the holding glove (`hl_prop` / `hr_prop`: 'ws_clipboard', 'ws_clipboard_new', 'walkie', 'ticket_y',
'punch', 'pencil', 'tail_piece'); a dropped prop is drawn by the shot from the hand's last point (see `ws_defeat`).
`CH.ws_tracking(pen, x, y, w, h, amount, t)` draws VHS tracking lines for sets and transitions.

## People: staging
All the Bunnyman / Doctor tools work (place, look_at, reach_to, hold_prop, sit_on / seated, kneel_down, crouch, walk,
run, hold_hand, hand_over, carry, drive + draw_steering_wheel, dial, tap, phone_to_ear, radio_to_mouth, knock_pattern,
point_at, wave, sit_floor, draw_palm_on_glass). New: `step_up(t0, side, up, hold, back)` (a foot onto the bus's first
step and back: 'step_touch', 'step_off'), `hug_prop(t0, prop)` (Rex, the backpack).

## Beat map: script beat -> clips (tools/cast_clips.py)
| beat | clips |
|---|---|
| 1994 tape | `ws_tv_host_1994`, `kids94_cards` |
| Grandma's job, the post, the rules | `della_brakes_names`, `mina_post_phone`, `della_rules_door`, `della_mailbox`, `sami_here` |
| rule 2: the bus, the skips, the door | `ws_unfold_door`, `ws_skip_lawn`, `ws_door_curl`, `ws_frosted_glass`, `mina_hush_sami`, `ws_punch_ticket` |
| rule 3: 911, the fake Grandma | `mina_911_nobars`, `della_keys_leave`, `mina_whats_the_word`, `ws_peephole`, `della_trapped_pound` |
| rule 4: the dark hand, the walkie | `ws_dark_grip`, `ws_walkie_grin`, `sami_walkie`, `sami_lighthouse` |
| rule 5-6: the deadbolt, the hallway, the guard | `mina_deadbolt_floor`, `ws_hallway_bent`, `ws_crossing_guard`, `sami_palm_window` |
| the chase | `della_drive_swerve`, `ws_window_backwards`, `ws_whistle_two` |
| rule 7: the last stop | `ws_steps_clipboard`, `mina_step_scream`, `ws_glove_snap`, `ws_aisle_reach`, `ws_lean_to_mina`, `mina_asks_name`, `della_broom_jam`, `theo_twist_free`, `ws_whistle_long_clock`, `ws_defeat` |
| after | `della_kneel_theo`, `della_hug_mina`, `theo_hi_mina`, `mina_sits_new_girl`, `ws_final_sting` |

## Sound events the cast emits
`ws_unfold_clack`, `tape_skip`, `whistle_two`, `whistle_long`, `glove_snap`, `neck_ratchet`, `punch_clack`,
`pencil_line`, `tape_warble`, `tape_rewind`, `clipboard_clatter`, `step_touch`, `step_off`, plus the older
`knock_door` (kind 'glass'), `dial_beep`, `card_tap`, `footsteps_*`.

## Limits and open problems
- The clips' scenery is a flat stand-in; the bus door, aisle, windows, peephole fisheye and hallway are sets' work.
- Front views read his bend by foreshortening only; stage "bent double" at 3/4 (as `ws_hallway_bent`).
- Several props are small at wide framings (whistle, walkie, ticket): cut to an insert for "my walkie", the ticket, the punch.
- The defeat's grin slip reads best in a close-up (`ws_head` slip cells); in wides it is the tears and the fade.
- The head is bigger now (1/5): framings made for the old 1/7 head may need a little more headroom; `CAST['whistle']['hh']`
  is 200 body units, so `draw_bust` scales are smaller for the same `scale` value.
- In a near-profile, his near ear is drawn over the hat crown (it is nearer the lens); from far away the ears and ruffs
  merge into the head silhouette (the hat and the long body carry the far read).
- Peephole / frosted glass / doorframe-peek treatments in `ws_creepy` are sheet comps (tools/cast_sheets.py `_peek`,
  fisheye remap, blur); the sets team owns the final versions.
