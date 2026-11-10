# UI_V2: on-screen text, diagrams and the rule cards (v2)

This file covers DIRECTION_V2 §5.3 (the rule card is the mirror), §5.4 (diagrams and evidence) and §5.5 (type and HUD),
plus the HUD types in PLAN_V2 §2.3. Everything draws from `plan/shots.json` as the plan writes it.

| file | what |
|---|---|
| `ui_v2.py` | Public entry point (`UI`): captions, header, chips, Tess's ring badge, giant numbers, command tags, red X, labels, teaser border, glint, smear carry, rewind overlay, kinetic title, type beats, end card, stamps, highlighter, count numerals, the RULE 4 circle, balloons, LIKE/SUBSCRIBE, time card. Also frame effects in numpy (RGB split, rewind tear, pixel sort) and the split and montage helpers. |
| `ui_v2_card.py` | The rule card as the mirror (`rule_card`) |
| `ui_v2_diag.py` | Diagrams D1-D10, split overlays, sound rings, dials, map, level guide, montage overlay, phone UI (v1 states), the phone screen's new `steps` state, and the evidence documents (`doc_layer`, `draw_doc`) |
| `ui_v2_letter.py` | Materials: palette, sprite cache, a hand-lettering single-stroke font (A-Z, 0-9, punctuation) with write-on and a visible writing tool, plus lipstick wax, chalk, kid marker and grease pencil |
| `tools/ui_v2_sheet.py` | Contact sheets of every device, rendered over real plates (v1 fallback sets + cast + grade), into `_work/ui_v2/` |
| `tools/ui_v2_check.py` | Measured checks: card timing, caption collisions, counts, HUD cost |

All drawing is in the 1920x1080 design space on the HUD canvas, after the grade. It is crisp at any render size, and
blurred glows are cached as sprites at render density.

```
python3 tools/ui_v2_sheet.py all          # every sheet (about 2 min at 1280x720); groups: cards title type countdown
                                          # chips marks diagrams docs phone fx
python3 tools/ui_v2_check.py              # card timing, captions vs HUD, counts, cost at 2560 (--no-cost to skip)
```

## 1. Wiring it into film.py (for the assembly pass)

film.py has not been changed. Four small edits connect it:

```python
import ui_v2
# Film.__init__
self.UI = ui_v2.UI(self.P, self.tl)
# Film.build(k), after the cast layers: DOC shots get the paper object as a set layer
dl = ui_v2.doc_layer(sh)                  # None for non-DOC shots
if dl is not None: layers.append(dl)
# Film.hud: replace the body
def hud(self, cv, t, B, cs): self.UI.hud(cv, t, B.sh, cs, self)
# Film._render: after render_frame(...)
img = self.UI.frame_fx(img, t, B.sh, i)
```

- **SPLIT shots.** Render each panel with `ui_v2.split_panel_shot(sh, j)`. A panel with `src_t` replays that film time:
  render it at `src_t + (t - t0)`. Join the two renders with `ui_v2.split_compose(left, right)`; the HUD draws the overlay.
- **MONTAGE shots.** Render the framing at `ui_v2.montage_source_t(sh, t)`.
- **Cards and type.** Card shots keep the blurred, dimmed plate from `bg` (post blur 8, dim 0.3). TYPE and DIAGRAM shots
  use `plate.post`.
- **What film.py still does.** It handles white and glitch cuts (`fx_at`, from `tr` and `fx_post` white / glitch /
  static) and the grade.
- **What `UI` adds.** The 3-frame glint (`glint` / `tr: glint`), the smear carry (`tr: smear`), the rewind (`tr: rewind`
  and `fx_post.rewind`: the overlay plus the picture tear), the pixel sort (`fx_post.pixel_sort`), and the teaser and
  CLEAN. RGB splits.

`tools/ui_v2_sheet.py` (`Renderer`) is a working example of this wiring, on the v1 fallback views.

## 2. `UI.hud(cv, t, sh, cs=None, film=None, captions=True, header_on=True)`

**Draw order.** Split overlay and montage → diagrams, sound rings, eye line, dials, map, level guide, count numerals,
highlighter, circle, balloons, labels → stamps, type beats 3/5/6, red X, tags, time card → phone → kinetic title → rule
card plus LIKE/SUBSCRIBE → teaser border → chips → ring badge and giant numbers → glint, smear and rewind → header →
caption.

**On rule cards and the kinetic title,** the card and the title own the frame: no header, chip or badge, and no caption
on cards (`captions: false` in the plan).

**`cs` (the shot camera state, `Cam.at(t)`)** pins labels, count numerals, D1, the level guide, the RULE 4 circle and
the highlighter to the subject plane (depth 1.0) through `engine.scene.project`, so they ride the push.

**Giant numbers are cross-cut overlays.** A giant number lives 0.72 s and may outlive its shot (60 flies into the badge
over the 289.74 cut). `UI` indexes them from the whole plan.

## 3. The devices

### 3.1 The rule card is the mirror (`ui_v2_card.rule_card(cv, rc, e, t)`)
`rc` = `rule_cards[n-1]`, `e` = the shot's `rule_card` entry. The timings are read from the entry, never retyped.

| time | what (keys read) |
|---|---|
| `glitch` (t0, 2 frames) | static bands (film's `tr: glitch` adds the picture glitch) |
| `towel_whip` (t0 .. t0+0.30) | the orange-striped terry towel covers the card at t0 and is yanked up and out, with cloth lag, a curved trailing edge, motion ghosts and a shadow |
| `card` {width_w 0.62, rot -2, overshoot 0.04, settle 0.13} | the mirror card (glass 1110x610 design px, chipped white frame 36 px, 62 % W) settles from 0.97 to 1.04 to 1.0 in 0.13 s (glass thud at t0+0.13), then drifts 1 %/s |
| `rule_write` (title_at .. +0.35) | "RULE" is written in lipstick, stroke by stroke, by a visible lipstick bullet in its gold tube |
| `numeral_stamp` {t, scale0 1.6, settle 0.13, crumbs} | the numeral (thick lipstick) stamps in from 1.6x and settles in 0.13 s, with a smudged print halo and crumbs thrown out under gravity |
| `words` [[word, t]] | the statement writes word by word on the narrator's times. Each word is wiped on in 0.10-0.26 s with the tool at the reveal edge: a grease pencil for off-white words (Montserrat 800, grease grain, dark halo), the lipstick for the *command* words (Montserrat 900, waxy red, drag streaks, sheen; card 7 uses a hot pink core so it holds on the red glass) |
| `underline_at` | a lipstick underline swipes under the command, per line, in 0.16 s |
| `tape_label` | masking tape on the frame's top edge, `NOAH'S · CABIN 7` in kid marker |
| `steps_progress` | the 7-step staircase bottom right: done steps dim lipstick, step n glowing, the rest grey pencil, `n / 7` |
| `reflection` {size, pose, stage} | **her reflection IN the glass**, soft (blur 1.6 px) and dimmed, in a stair scene. Plum treads with glowing red noses step down to the gold room at the vanishing point, with fog and our moonlight from above. Per card: 1 a tiny S0 figure on the far tread against the gold; 2 S1, 16 %, three-quarter with the head to the lens; 3 S1, 25 %, in gold doorway light; 4 S2, 30 %, seated on a tread; 5 S2 bust (the drawn stair smile); 6 S3b bust (red eyes); 7 S3c face filling the glass. Drawn by `characters` (`draw` / `draw_bust` with `queen_stage`) once per card into a sprite. |
| `glass` | clean silver (1-2), gold reflection (3-4), a hairline crack (5), three cracks from an impact point plus 30 % red (6), graded red plus glowing steps plus the 1.2 s red pulse (7). The glass also carries desilvering at the edges, a dust film, smudges, sheen bands, a moving flashlight hot spot and drifting dust. |
| `like_sub` {t, hold, clicks} (cards 1-2) | the LIKE / SUBSCRIBE / bell bar bottom left (1.3x); the cursor clicks LIKE at +0.35 (turns blue), SUBSCRIBE at +0.85 (grey SUBSCRIBED) and the bell at +1.35 (rings), matching the plan's ui_pop cues |
| `wipe_out` .. `end` | a finger-wipe smear crosses the glass left to right, erasing the writing into pink streaks |
| `wipe_carry` (next shot `tr: smear`) | `smear_carry`: the streaks slide off right over the next shot for 0.2 s |

**Speed.** The shadow, glass, reflection, front and frame are one sprite with the tilt baked in, blitted axis-aligned
(a rotated or additive full-card blit cost 80-200 ms).

### 3.2 Type

| device | API (plan entry) | look and animation |
|---|---|---|
| kinetic title | `kinetic_title(cv, e, t)` (`kinetic`, S006) | WIPE / THE / GLASS pop on the word times (3.92, 4.24, 4.40); white Montserrat 900, cap height 9 % H; an elliptical ring flash and a 2-frame flash at 3.92. CLEAN. comes in lipstick red (waxy, 1.18x) at 4.80 with a 3-frame RGB split on the type and the picture, then a lipstick underline swipe. Out at 5.30 with a towel wiping right to left. The `typebeat` n=1 entry is the same title and is not drawn twice. |
| 14 YEARS (type beat 2) | `stamp(cv, e, t)` (`stamp` + `typebeat` n=2) | red rubber stamp: double border, distressed ink, rot -4; slams from 1.7x in 0.09 s, then squash, ink spatter and a hit frame. Echoed at 426.1 (size_h 0.14). |
| 7 RULES (type beat 3) | `typebeat_rules` (`typebeat` n=3, size_h 0.2) | a lipstick 7 stamps in at 122.87, white RULES slides in, and 7 lipstick treads light up as a bar |
| RULE 4 circled | `circle_mark` (`circle`) | a hand-drawn lipstick loop in 0.35 s while RULE 4 is written beside it (the shot is 0.39 s long) |
| giant numbers (type beat 4) | `giant_number(cv, e, t)` (`giant_number`) | a red numeral (white outline, gradient, sheen) at cap 38 % H inside a ring that shows the count (60 full, 45 three-quarters, ... 0 empty). It slams with a shock ring and a red hit frame, holds 0.5 s, then flies into the badge in 0.22 s with a trail. **0 does not fly:** it holds and flashes until the card 7 glitch cuts it. |
| 7:00 AM (type beat 5) | `typebeat_seven_am` (`typebeat` n=5) | warm white 7:00 plus gold AM; slams with a gold ring burst at 538.7 |
| end card (type beat 6) | `end_card` (`typebeat` n=6) | `DON'T MAKE A` in white over a large lipstick `WISH.` on black; fades in over 0.4 s from 698.75, a lipstick underline at +0.55, a slow 2.2 %/s push |
| CANCELED | `stamp` (S288) plus the chalk in `doc_layer` | the chalk strike-through and pink CANCELED on the board at 438.7, then the red stamp at 438.95 |

### 3.3 HUD

| device | API | spec |
|---|---|---|
| caption | `caption(cv, s, alpha)` + `caption_alpha(c, t)` | v1 style and position (white bold caps, 33 px = cap 2.1 % H, baseline 976 = centre 0.893 H, soft dark halo); fades in over 0.12 s and out over the last 0.06 s |
| header | `header(cv, sh, t)` | v1 (`CABIN 7 · CAMP CEDAR LAKE // RULE n OF 7` at the plan's 20 % opacity, the in-world clock right: ours / theirs (looping, 2-frame snap) / stuck 07:00:00 / 14 YEARS AGO) |
| chip | `chip(cv, s, style, u, x, y, out=)` | top-left at (44, 108) under the header, stacked 58 px apart. Styles: `ours` navy with a pulsing blue dot; `theirs` gold with an amber dot; `loop` plum with a spinning loop arrow; `teaser` red, instant text; `stairs`, `climax`, `ending`. `memory` is the red-brown `14 YEARS AGO` rubber stamp rotated -4° and slammed in. The chip opens from its dot in 0.28 s and the text arrives 0.1-0.28 s in (0.4 s pop). The text after `·` is brighter. Shot chips are drawn when `chip.pop` is true; HUD `chip` entries (LOOP, ↺ AGAIN, 7:00 AM, 12:00 PM, RULE n) stack under them. |
| ring badge | `Counter(plan['counter'], giants).draw` → `ring_badge` | top right at (1792, 126), r 50, a dark disc. The ring depletes clockwise (60 = full) with a bright moving end and 5-second ticks; TESS label and the number inside. Each step ticks in 0.12 s; a call pops to 1.35x with a red flash **when its giant number lands** (t + 0.72); 5 and below turn red; 0 flashes red; the badge glitches away at 609.48. It is hidden on cards, TYPE and black, and dimmed to 60 % in memories. |
| command tag | `cmd_tag(cv, s, x, y, u, hold)` | lipstick-red Montserrat 900 at 64 px, **no box**: dark wax edge, gradient, drag streaks, sheen, dark halo; -1.5°. Pops in 4 frames from 1.28x, a lipstick underline swipes under it at +0.07, out in 3 frames |
| red X | `red_x(cv, x, y, r, u, hold)` | the v1 X (the critique's best device): the ring draws in 0.09 s, then the two strokes, with a 1-frame red flash. Kept above the caption band (y ≤ 925 - r). |
| label | `pin_label(cv, e, u, cs)` | pinned leader line with a pulsing dot to a white tag (30 px); projected through the camera |
| teaser | `teaser_border(cv, u)` + `frame_fx` | a red 6 px frame (8 design px) with an inner glow, flickering for 6 frames; a red chip; an RGB split on the picture for 3 frames; glitch out from `fx_post` |
| side-switch glint | `glint(cv, u)` | 3 frames: a diagonal white streak at 60 % with red and cyan 6 px fringes, one position per frame (left, centre, right) |
| rewind | `rewind_overlay` + `rewind_img` | 0.2 s: a ◀◀ REWIND glyph and tracking bars over the picture. On the picture: a 4-frame horizontal tear, then a back-scrub (vertical squash jitter, chroma shift, a noise band rolling up). |
| pixel sort | `pixel_sort_img` | random bands smeared right from a threshold column, strength following sin(π u) (S448 697.95) |
| balloons | `balloon(cv, e, t)` | memory speech balloons: cream paper, brown outline and tail. A shout (NOAH!) gets a jagged edge; an empty balloon holds 3 breathing dots (the third call). |
| time card | `time_card(cv, e, t)` | v1 card restyled in the ours chip palette; the minute flips 56 to 57 |
| phone | `ui_v2_diag.phone_ui(cv, e, t, sh, film)` | all v1 states (message, voicemail_list, voicemail, calling, connected with Mom's real envelope, flat, chair-scrape spike, inset). Bubbles are 20 px and `fit_bubble` wraps and splits every line to the bubble width (error 23); `fit: true` phones are 1.1x. |

### 3.4 Diagrams (D1-D10) and devices

| id | shots | API | what is drawn |
|---|---|---|---|
| D1 | S072 98.2 | `d1_game` (pinned) | chalk tread outlines over the lipstick steps (sets.py STEP_XY), chalk numerals 1 (top) to 7 popping 0.07 s apart, a tiny dark Queen silhouette (crown, collar, gown) below step 7 labelled HER, a dotted chalk arrow climbing the steps (0.7-1.4 s), and a star plus WISH written in chalk at the top right |
| D2 | `count_pop` entries | `count_pop` (pinned) | a white numeral (900, 64 px, dark halo) pops 0.08 s from 1.5x with a ring burst. `color` red = the 7 RULES bar (glowing); `erase` = ticked off by the wipe (a lipstick strike, then a fade). It also covers the phone count (S442/S443). |
| D3 | S101 | `d3_side` | a dark panel, SIDE VIEW. The glass edge-on (a silver bar in the white frame); steps 1-7 as lipstick marks ON it (DRAWN ON IT); your eye looking at it (OUR SIDE); a dashed chalk line through the glass to the 8th tread BEHIND it (red-edged, the Queen standing on it), more treads going down; labels 8TH STEP: BEHIND IT, BEHIND THE GLASS, THE GLASS |
| level guide | S103 | `level_guide` (pinned) | a dashed white LEVEL line at y 680, the frame's -13° axis in pink, the arc and 13°, THE FRAME |
| D4 | S122 | `split_overlay` + `diagram D4` | divider; THEIR FLOOR (gold underline, chip `6:59 AM · 14 YEARS AGO`) and OUR FLOOR (blue, chip `11:59 PM · TONIGHT`); a ≠ badge on the divider; WET PRINTS and NO PRINTS |
| D5 | S139 | `eye_line` | double red target rings on her eye and yours, a marching dashed red line from hers to yours with a pulse and an arrowhead; HER EYES and YOURS |
| D6 | S229 | `dials` | OUR SIDE dial (upper left over the blue cabin): the hand crawls and dust hangs; chip `12:02 AM`. THEIR SIDE dial (lower right over the gold): the hand sweeps :40 to :59 every 1.1 s and snaps back with a flash; gold loop band, lipstick return arrow, chip `6:59:4x · LOOP` |
| D7 | S019, S257 | `d7_loop` | THEIR CLOCK inset dial (right): the :40-:59 band, the return arrow, the second hand climbing to :59 and snapping to :40 at the shot's `fx_post.rewind` time (or its end), readout `6:59:ss`, plus the LOOP chip and rewind |
| D8 | S051, S332, S338, S339, S343, S346 | `sound_rings` | clean: smooth white rings expanding (n, staggered 0.2 s); rattle: a ring with a jagged red squiggle ring trailing; broken: dashed jagged white and red rings (the real strike). Labels CLEAN NOTE and + RATTLE on DIAGRAM and SPLIT shots. The split S343 adds THEIR BELL with a red X and FAKE, OUR BELL with a green tick and REAL, beside the labels. |
| D9 | S348 | `d9_seven` | the dial passes 12 at 538.70 and keeps going (7:00:00); the loop band whitens and the return arrow breaks and drops; the dial shrinks as the 7:00 AM type slams in |
| D10 | S295 | `map_inset` | a top-left inset (1.35x) on a navy grid: CABIN 7 box, the dotted path (40 M), MESS HALL, the CRATE in red, and Tess's amber dot running cabin to crate over the 2 s |
| loop split | S280 | `split_overlay` | both chips `6:59:45 AM` and a `= SAME SECOND` badge on the divider |
| watch | S065, S251 | `watch_overlay` | ALM callout beside the watch: 6:45 flips to 4:45 with a highlighter box and 2 HOURS EARLY; or 4:45 flashing |
| montage | S437 | `montage_overlay` | a white frame on each tile cut, a chip with that moment's Cabin 7 clock (11:58 PM, 11:59 PM, 12:01 AM, 12:05 AM), 4 tile ticks; the red X and FACE UP hold across |

### 3.5 Evidence documents (`ui_v2.doc_layer(sh)` → engine Layer at depth 1.0)

They are drawn as set layers, so the camera push, DOF and the world grade (sepia for memories) apply. Marks animate on
film time.

| kind | shots | the object |
|---|---|---|
| poster | S016, S017, S030 | MISSING in red; Noah13's gap-tooth photo (`characters.draw_bust`); NOAH BRENNAN, 13 · LAST SEEN JULY 18 · CAMP CEDAR LAKE · LAST SEEN WEARING A GREEN SWEATSHIRT; rain stains, thumbtacks. Scaled to 0.82 so it clears the caption band. The poster_ecu view fits the LAST SEEN WEARING line to the plan's highlighter box exactly (560-1400 × 690-760); the highlighter (`highlight`) swipes it with a chisel tip. |
| notice | S023 | yellow band NOTICE OF DEMOLITION, CABINS 5-7, SAT 7:00 AM in red, zip ties; a lipstick-red underline at 26.4 |
| stencil | S045 | crate slats with SAVE FOR THE / MUSEUM stencilled; the museum tag swings and flips at 58.3 to CEDAR LAKE HISTORICAL SOC. |
| card | S070 | a vintage Queen of Spades court card: her S1 bust and its 180° mirror in two clipped halves, Q and spade indices, sepia |
| polaroid | S150 | Noah13 holding up the taped hand (one tape design from `characters`), NOAH · JUNE in blue marker |
| photo | S211 | sepia family photo: Dad (`you`'s face: square jaw, stubble) with kid Noah and kid you; DAD · CEDAR LAKE in pencil |
| menu | S288 | chalkboard JULY 19 / BREAKFAST 7:00 / PANCAKES / OJ · MILK · FRUIT in hand chalk; at 438.7 the old text dims, two strike-throughs and CANCELED chalked across in pink; the stamp follows |
| sign | S292 | CAMP CLOSED, hung by wires, swaying, the gate chain below |

**Phone screen (set side).** `phone_screen(pen, x, y, w, h, t, 'steps', steps, eighth, red)` draws the black glass:
reflection band, dust, the 7 tiny lipstick steps (`STEP_XY` scaled, there before "count") and the 8th line glowing
under step 7. The 'face' state is the cast's `q_nface` on the queen bust.

## 4. Legibility at 640x360 (cap height of each text style in a 640x360 frame)

| text | design size | cap at 640x360 |
|---|---|---|
| caption | 33 | 7.7 px |
| chips | 26.5 (cap 1.75 % H) | 6.2 px |
| card statement / command | 58 | 13.5 px |
| card RULE / numeral | 112 / 150 (stroke font) | 37 / 50 px |
| command tags | 64 | 15 px |
| labels | 30 | 7 px |
| chalk diagram labels | 34-44 | 7.9-10 px |
| map labels | 24-26 × 1.35 | 7.6-8.2 px |
| badge number | 38 | 8.9 px |
| LIKE / SUBSCRIBE | 21 × 1.3 | 6.4 px |
| phone bubbles | 20 × 1.34 | 6.3 px |
| giant numbers / kinetic title / end card | 585 / 139 / 236 | 136 / 32 / 55 px |

Only the header (20 % opacity by design, 3.6 px) and the badge's TESS label (decorative) are below 6 px. Every sheet
tile in `_work/ui_v2/` is 640x360 and was read by eye.

## 5. Measured (`python3 tools/ui_v2_check.py`)

**Card timing.** The card's first and last frame on screen, measured from pixels:

| card | brief appear-cut | measured | d appear / d cut |
|---|---|---|---|
| 1 | 129.80-133.56 | 129.800-133.567 | 0.000 / +0.007 |
| 2 | 203.53-208.32 | 203.530-208.330 | 0.000 / +0.010 |
| 3 | 269.24-273.35 | 269.240-273.357 | 0.000 / +0.007 |
| 4 | 350.38-353.53 | 350.380-353.530 | 0.000 / 0.000 |
| 5 | 446.33-449.74 | 446.330-449.747 | 0.000 / +0.007 |
| 6 | 542.03-545.22 | 542.030-545.230 | 0.000 / +0.010 |
| 7 | 609.48-614.71 | 609.480-614.713 | 0.000 / +0.003 |

All are within ±0.05 s; the cut error is one frame of sampling. Choreography per card: towel off t0+0.30, RULE written
title_at+0.35, numeral settled stamp+0.13, then the underline and wipe at the plan's times.

**Captions vs HUD.** 1,099 samples (every 0.1 s on every shot with HUD entries while a caption is up). One hit: the two
slam frames of the giant 20 (502.39), where the ring passes under the caption for 0.03 s. Moved out of the band:
- the split dividers (gap 928-1004);
- red X 3 (clamped);
- the D3 panel;
- D1's HER label;
- the montage chip;
- the poster's small print.

**Counts.** These match the brief:

| element | count | brief |
|---|---|---|
| red X | 4 | 4 |
| command tags | 6 | 6 |
| labels | 10 | 8 or more |
| giant numbers | 5 | 5 |
| kinetic title | 1 | 1 |
| type-beat kinds | 6 | 6 |
| teasers | 5 | 5 |
| side-switch glints | 20 | 18-22 |
| chips drawn | 58 | |

**HUD cost at 2560x1440** (warm median ms per frame):

| device | median ms |
|---|---|
| rule card | 60-110 (the 18 towel frames up to 370) |
| giant number | 35 |
| kinetic title | 31 |
| D6 | 26 |
| menu / CANCELED | 16 |
| bell split | 15 |
| D1 | 12 |
| others | under 10 |

A card's first frame costs 0.5-0.9 s while it builds its sprites (her reflection), once per process.

## 6. Sound sync (for the sound pass)

These times come from the code and match the plan's device cues:
- **Cards:** towel_whip t0, glass_thud t0+0.13, lipstick_draw title_at (0.35 s), lipstick_stamp numeral_stamp.t, word
  reveals at word t - 0.05, the underline at underline_at, glass_wipe at wipe_out. LIKE / SUBSCRIBE / bell clicks at
  like_sub.t + 0.35 / 0.85 / 1.35.
- **Giant number:** slam at t (number_thump); the badge pop on landing at t + 0.72.
- **Stamps:** contact at t + 0.09.
- **Kinetic title:** words at 3.92 / 4.24 / 4.40, CLEAN. at 4.80, underline 4.88, towel wipe 5.30-5.40.
- **7 RULES:** the 7 lands at t + 0.09, the bar ticks t + 0.18 .. + 0.48.
- **D1:** numerals every 0.07 s from t, the figure at +0.5, the arrow +0.7..+1.4, WISH +1.35.
- **Glint and rewind:** glint 3 frames from the cut; rewind 0.2 s.

## 7. Departures from the brief's letter

- **Chips:** cap height 1.75 % H instead of 1.4 %; at 1.4 % the chip is 4.9 px tall at 640x360 and does not read.
- **Badge timing:** the badge appears when the giant 60 lands (289.91), not at 289.19. Each call's new value shows when
  its giant number lands in it. The giant 0 holds instead of flying.
- **D7 / D9:** drawn as an inset THEIR CLOCK dial beside the set's wall clock, not over it. The v2 clock insert's
  geometry is unknown, and the inset carries the band, the return arrow and the readout.
- **The watch flip:** an ALM callout beside the watch. The set's LCD may or may not flip.
- **The documents:** set layers (`doc_layer`), not HUD, so they get the push and the grade. When the v2 sets draw their
  own poster or menu, drop the doc layer for that view and keep the HUD marks. The highlighter and stamps are HUD.
- **D2 numerals and labels:** placed at the plan's design coordinates. D1 is placed on sets.py's `STEP_XY` (the
  mirror_cu framing). If the v2 glass views move the steps, update `STEP_XY` in `ui_v2_diag.py` or the plan's x/y.

## 8. Sheets (`_work/ui_v2/`)

- `card1_6fps.jpg` .. `card7_6fps.jpg`: each card at 6 fps from 0.17 s before to 0.34 s after, including the smear carry
- `title_and_end.jpg`, `type_beats.jpg`, `countdown.jpg`, `chips_teasers.jpg`, `marks_tags_labels.jpg`, `diagrams.jpg`,
  `documents.jpg`, `phone.jpg`, `transitions_fx.jpg`
- `full_card2.jpg`, `full_card7.jpg`, `full_title.jpg`: 2560x1440 stills for crispness

## 9. What remains weak

- **The plates are v1 fallbacks.** The sheets show the devices over v1 views. Positions keyed to set geometry need a
  check once the v2 views land:
  - D1 / STEP_XY;
  - count numerals;
  - the RULE 4 circle;
  - label pins;
  - the eye-line points;
  - the poster ECU line;
  - the red X targets.
- **Card glass is a dark smoky mirror.** It is cool slate for 1-2 and warm for 3-4, rather than bright silver. The text
  contrast is excellent; brighten `_glass_palette` if the director wants more silver.
- **Her reflection on cards 1-4 is small and dark** by design (9-30 % of the glass) and reads best at full size.
- **The towel** is a flat striped cloth with lag and ghosts, with no real fold simulation. Its 18 frames are the
  costliest HUD frames (about 0.25-0.37 s at 2560).
- **The `face` phone state** depends on the cast's `q_nface`; `phone_screen` covers only the glass, steps and 8th line.
- **Split panel rendering and montage tiles** are only helpers here; film.py must render the two panels and the tiles.
