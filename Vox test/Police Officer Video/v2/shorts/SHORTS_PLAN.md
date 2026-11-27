# Three Shorts for "If A Police Officer Knocks At Midnight... DON'T PROVE YOU LIVE THERE"

Source: the long video (11:39, `v2/film.py`, lines in `../script/lines.py`). Playbook: `SHORTS_ANALYSIS.md` (four viral references, 22 rules).
Machine-readable version of everything below: `shorts_spec.json`. Lines the owner must record: `LINES_TO_RECORD.md`.

All timings are estimates (narrator 2.9 words/s, characters 2.6 words/s) because the narration audio is not available right now. The assembler re-times every beat from the real clip lengths in `timeline.json`; the rules for that are at the end of this file and in `shorts_spec.json` → `assembly_rules`.

## 1. Strategy

**What each Short has to do.** Every Short is a finished horror mini-story: hook, a five-step ladder that gets worse each step, a twist that flips what you thought was happening, and a payoff. The payoff answers the Short's own question but opens a bigger one that only the long video answers. Nothing is a random clip. Each Short re-stages long-video moments vertically, adds new close-ups, inserts and UI, and is cut to the reference pace (a cut or punch every 0.8 s).

**Three angles that barely overlap.** Each one takes a different part of the story and a different "horror device":

| | Short 1: THE OTHER GENTLEMAN | Short 2: YOUR VOICE ON THE RADIO | Short 3: NEVER CORRECT HIM |
|---|---|---|---|
| Device | Identity match: a meter climbs 0 → 100 % | Audio playback: PLAYBACK #1 → #5 | A quiz: QUESTION 1/5 with a scoreboard |
| Long-video lines | 12-134 (knock, back seat, licence, complaint, the double) | 63-105 (rules 2 and 3) | 142-174 and 220-249 (rule 5, the phone call) |
| Five steps | his habit, your licence, your clothes, your name, your face | your voice, wrong pause, he practises, it's right, your mother | tiles, pet, school, nickname, the photo |
| Twist (≈ 72-80 %) | The complaint is signed with **your** name | Your mother's voice **loops**: it's a recording | **He phoned your mother first**: she gave him the answers |
| Payoff | "That's the man in my house." in your voice | "Poor reception." Her line is busy | He is now knocking at **her** door |
| Open question for the long video | Which one of you will the officer believe? | Where is your real mother? | Does she open the door? |
| Loop | two knocks → frame 1's knocks | radio click → frame 1's "I live here." | pen click at mum's door → frame 1's quiz question |

**Why this mix.** Short 1 is the broadest hook (the long video's own title, said as a warning) and goes up first. Short 2 is the most "sound-driven", and audio horror is what holds people on Shorts. Short 3 has the strongest twist and ends at the mother's door, which is the long video's climax, so it sends the most viewers to the long video. None of them shows rule 6 (the countdown and the neighbour's keys), the coat-hook reveal, or the ending: those stay exclusive to the long video.

**Playbook applied to all three** (rule numbers from `SHORTS_ANALYSIS.md`):
- First word at 0.25 s; the premise is finished by about 3.5-4 s. Frame 1 is an extreme close-up that already shows the threat (a face bulging into the doorbell lens, a shoulder radio, a peephole face) (rules 1-2).
- 126-133 spoken words, 51-55 s, "you/your" 9-15 times, present tense, sentences under 14 words (rules 3-6).
- A five-step ladder with a HUD counter on screen from 0 s, ticking at every step (rules 7-8).
- 26-31 planned shots, plus a punch-in in every beat longer than 2 s, giving 35-50 visual cuts; zoom punches of 115-140 % on keywords (rules 9-10).
- Reference captions, not the long video's small ones: Montserrat 900, white with a thick black outline, 1-2 words per chunk, centred at 64 % of frame height, one coloured keyword per sentence. Colours: red danger, amber "you/yours", police blue, pink for the mother (rule 11).
- Text slams and diegetic hits replace the comic bursts: "KNOCK", "SAME", "IT'S YOURS.", "IT'S A RECORDING", "HE CALLED HER". Each Short has at least 3 fake UI inserts: bodycam, waveform panel, phone UI, complaint form, notebook answer key, comments panel (rules 20-21).
- Subscribe is spoken inside the story at 43-50 %: "Everyone who subscribes gets to keep their own face / voice", "...knows which one is real". A SUBSCRIBE button is pressed in sync with a story action: his palm hitting the glass, the waveform going silent, the double's half of a split screen glitching (rule 16).
- One tension gap of 1.0-1.2 s just before the twist: music out, only heartbeat, tinnitus or radio hiss (rule 14).
- End: one new line that asks the open question and points to the full video, with the card "FULL VIDEO ON THE CHANNEL". The comment prompt is on screen only, in a 1.2 s comments panel, so it costs no extra recorded line (rule 18).
- The loop never dies: the CTA ends on the same sound frame 1 starts with, then an 8-frame REWIND glitch (rule 19).
- Safe zones: nothing important in the top 8 %, the bottom 20 % or the right 12 %. The HUD sits at 9-15 % height and the SUBSCRIBE button at 74 % (rule 22).

**New lines: 7 required in total (3 + 2 + 2) and 2 optional.** Everything else is the owner's existing narration and character voices, cut by line index (word slices only where marked).

## 2. Short 1: THE OTHER GENTLEMAN

- **Title:** A Cop Knocks At 12:36 AM... The Man In His Car Is YOU
- **Hook (0-3.6 s):** two knocks on the doorbell lens and the officer's grin bulging into the fisheye. NEW line: "If a cop knocks after midnight... don't prove you live there." On "prove" there is a hard cut to an extreme close-up of him from below and the slam "DON'T PROVE YOU LIVE THERE". It's the long video's title, delivered as a warning.
- **Ladder (MATCH meter):**
  - 20 %: his thumb rubs his ring finger, the way you do when you're nervous (split screen, his hands over yours).
  - 40 %: his licence has your chipped corner (match cut).
  - SUBSCRIBE at 50 %: his palm slaps the glass as the button is pressed.
  - 50-60 %: the complaint describes you, down to the hoodie you're wearing.
  - 80 %, the twist: the complainant's name is yours. A 1.1 s tension gap, then a braam.
  - 99 %: his face is "almost yours", with tags for the scar and the ring on the wrong side.
  - 100 %: "That's him. That's the man in my house.", said in your voice while he leans into the lens.
- **CTA:** NEW: "Seven rules keep you alive. The full video is on the channel." Rule cards flick 1 → 7 and land on "FULL VIDEO ON THE CHANNEL"; the comments panel says "Comment BACK SEAT if you'd keep the door shut".
- **Music:** *From Hell* (Christoffer Moe Ditlevsen), from 13.2 s, quiet and building; its loud section at 53.2 s must land on "It's yours." Alternate: *A Massive Mist* 0-68.7 s.
- **Description:** If a police officer knocks after midnight, don't prove you live there. The man in the back seat knows your habits, your licence, your signature... and your voice. All 7 rules are in the full video on the channel: [LONG VIDEO LINK]
- **Hashtags:** #shorts #horror #scarystories #rules #creepy #police #doppelganger #horrorstory

## 3. Short 2: YOUR VOICE ON THE RADIO

- **Title:** The Police Radio Is Playing YOUR Voice...
- **Hook (0-4 s):** a radio squelch and click on an extreme close-up of the shoulder radio, then your own voice: "I live here." (L64, radio FX). Hard cut to you snapping toward the door: "You'll hear your own voice coming through it." Slam: "YOUR VOICE".
- **Ladder (PLAYBACK #1-#5):**
  - #2: the pause is too long ("I... live here.") on a waveform panel with a red "PAUSE TOO LONG" marker.
  - The man in the back seat leans forward. His lips mouth the words, with a ghost caption: he is practising.
  - #3: "Again." His mouth moves in sync with the radio, the waveforms align, "MATCH 100%". The officer leans into the lens: "Good. Now your name."
  - SUBSCRIBE at about 43 %: you cover your mouth while the waveform flattens.
  - #4: your mother on the radio, with the cough marker.
  - #5: your nickname (shown bleeped).
  - Twist: the second take has the cough in exactly the same place. Two stacked waveforms line up, "IDENTICAL". A 1.2 s gap of radio hiss, then a dry click and "IT'S A RECORDING".
- **Payoff:** "Poor reception." The officer's smile drops. "Her line will be busy." The phone UI shows BUSY.
- **CTA:** NEW: "Where's your mother? Find out in the full video on the channel." over her house at night, one window lit, the strobe sweeping across it. The last frame is a radio click that loops into frame 1's click and "I live here."
- **Music:** *Dark Forebodings* (Ethan Sloan), from 6.0 s, a constant dark pulse; its section change at 46.2 s lands on the click. Alternate: *Dark Tunnels*.
- **Description:** If you hear your own voice on a police radio, don't answer it. Someone in that patrol car is learning how you speak, and your mother is next. The full story is on the channel: [LONG VIDEO LINK]
- **Hashtags:** #shorts #horror #scary #rules #creepy #police #audiohorror #horrorstory

## 4. Short 3: NEVER CORRECT HIM

- **Title:** Never Correct The Man Who Says He's You
- **Hook (0-3.5 s):** the officer bulges into the peephole with a notebook. "What color are the kitchen tiles?" The double: "Green." Hard cut to your kitchen: "Your kitchen tiles are blue." The RULE 5 card: "Don't correct anything the other man gets wrong."
- **Ladder (QUESTION 1/5 and the scoreboard):**
  - The officer and the double snap their heads to the lens in unison.
  - First pet: HIM ✓.
  - School: his eyes flick to the officer first.
  - What your mother calls you: a 0.3 s flash of her by her phone (foreshadowing).
  - "Don't." over your knuckles going white.
  - Q5, the photo nobody mentioned: "My mother." "It was your father." HIM ✗.
- **SUBSCRIBE at 45 %:** a vertical split screen of the double over you; his half glitches as the button is pressed. "Everyone who subscribes knows which one is real."
- **Twist:** the officer turns his camera off, then a 1.0 s gap. You call your mother: "Thank goodness. Are you all right?" "She tells you he called earlier." Then a notebook answer key fills in: "Your first pet. ✓ Your school. ✓ The photograph your father took. ✓" and the slam "NOW HE KNOWS".
- **Payoff:** "There's knocking at her door." Through the curtain: "He looks just like you."
- **CTA:** NEW: "Does she open the door? Watch the full video on the channel." over an extreme close-up of her lock. Loop: the officer at her peephole and a pen click, then REWIND to frame 1, where the quiz starts over.
- **Music:** *In Continuum* (Dream Cave), from 12.0 s, a quiet 92 bpm build; its loud section at 50.4 s lands on "She tells you he called earlier." Alternate: *Tefu* 0-89.7 s.
- **Description:** Rule 5: never correct anything the other man gets wrong. He doesn't need you to answer, because someone already did. What happens at your mother's door is in the full video on the channel: [LONG VIDEO LINK]
- **Hashtags:** #shorts #horror #scarystories #rules #creepy #police #twist #horrorstory

## 5. Sound plan (all three)

- **Master:** −14 LUFS integrated, loudness range ≤ 2.5 LU, true peak ≤ −1 dBTP. The voice sits on top; music runs 8-11 dB under it (sidechain duck of 9 dB, 80/250 ms) and plays 100 % of the time except the single tension gap.
- **Sources:** the owner's Epidemic library first (`audio/catalog_epidemic.json`: knocks, porch footsteps, police radio squelch and static, car idle and doors, mail slot, phone busy and vibration, breath, heartbeat, tinnitus, risers, braams, sub drops, UI pops). The rest comes from `audio/sfx.py` (`pen_click`, `glitch`, `typing`, `crowd_whisper`, `room_tone`).
- **Density:** 3-6 strong hits per 10 s:
  - an impact or stinger on every text slam;
  - a braam plus a sub drop on each twist;
  - a whoosh on every hard cut and a UI pop on every tag and counter tick;
  - a heartbeat that speeds up from 70 to 90 bpm under the second half.
- **Diegetic motifs carry the loop:** knocks (Short 1), radio clicks (Short 2), a pen click (Short 3). The same sample is used at the first and the last frame.
- **Voices:** character lines keep the long video's radio and phone FX (Y, M and some O lines). The NEW lines are the narrator, dry and close. The two subscribe lines are whispered.

## 6. Production notes for the renderer

- **Output:** 1080×1920 at 60 fps.
- **Rendering:** reuse the `film.py` builders (door, peep, bust, car, hall, ins, hands, kitchen, mumroom, mumext, curtain, phone, wave, rule). Either render the 1920×1080 design space at 3414×1920 and crop a 1080-px window per shot (`crop_cx`; the window is 607.5 design px wide), or add a vertical camera. Busts and peephole discs should be re-centred, not cropped off-centre.
- **New compositions to build:**
  - vertical split screens (hands; faces with the SUBSCRIBE button on the seam);
  - the MATCH meter, PLAYBACK counter and quiz scoreboard HUDs;
  - the SUBSCRIBE press animation (2 s, overshoot, bell);
  - the end card "FULL VIDEO ON THE CHANNEL";
  - the fake comments panel;
  - the notebook "ANSWER KEY" insert;
  - the stacked waveforms with aligned COUGH markers;
  - a REWIND glitch of 8 frames.
- **Acting to push harder than in the long video** (Shorts are watched small): lean_in amount 1.2-1.4 so the fisheye bulge is extreme, wide_grin held 1.5 s, snap_turns in unison, dead_stare on "Poor reception.", and creep_smile behind the palm on the glass.
- **Re-timing once the narration is back:**
  1. Cut each line by `timeline.json` t/end, with word slices from the ASR words.
  2. Place the beats in order with their gaps.
  3. If the total is over 56 s: tighten the gaps, then apply atempo of up to 1.06, then drop the optional beats (S1 L23, S2 L67, S3 L222).
  4. If it is under 48 s: lengthen the tension gap to 1.6 s and the end card to 2.5 s.
  5. Check that the subscribe line lands at 43-50 % and the twist at 70-82 %.
- **Publishing:**
  - Post Short 1, then Short 2 two days later, then Short 3 two days after that.
  - In YouTube Studio, set each Short's **Related video** to the long video. This puts a tappable link on the Short itself and is the strongest route to the long video.
  - Pin a comment with the link.
  - If a Short's 3-second hold rate is weak, re-upload it with the optional alternative hook (`LINES_TO_RECORD.md`).

## 7. Beat-by-beat scripts, shot lists and sound

Columns:
- **Voice:** `Lnn` is a line index in `lines.py`, with the speaker code (N narrator, O officer, Y your voice on the radio, D the double, M mother); **NEW** marks a line the owner must record.
- **Picture:** `start-time scene: framing [acting]`. The scene is the `film.py` builder, and NEW marks a composition that is not in the long video.
- Times are estimates.

### S1 timing table (estimated 54.3 s, 133 words, "you/your" x13, 26 shots before punch-ins)

| # | Time (s) | Voice | Picture (9:16) | Overlays | Sound |
|---|---|---|---|---|---|
| 1 | 0.0-4.3 | **NEW S1-N1** "If a cop knocks after midnight... don't prove you live there." | 0.0 door: ECU fisheye: officer's face fills 70 % of the frame, lens bulge, porch light behind; crop_cx on his nose [lean_in (amount 1.3) + wide_grin, knk_at(0.0, n=2, side=0) on the lens with doorbell jolt] NEW<br>2.2 bust: officer ECU from below, bg porch with DOF, head tilt toward the lens [creep_smile -> wide_grin on "PROVE"] NEW<br>*First word at 0.25 s; the premise is finished by about 3.5 s. No title card, no logo. This is the long video's title, said as a warning.* | HUD clock 12:36 AM pops at 0.0<br>text slam "KNOCK" x2 synced to the knocks (0.2 s each)<br>on "prove": text slam centre 40 %: "DON'T PROVE YOU LIVE THERE", "PROVE" red, punch 130 %<br>captions: "COP" blue, "MIDNIGHT" red | 0.00 knock_door n=2 spacing 0.28 space=close (lens hit, plastic rattle)<br>0.00 impact_hit -3 dB<br>impact_hit on "prove"<br>whoosh hard on the cut<br>ambience_night bed -24 dB throughout<br>police flash hum low<br>MUSIC: 0.00 braam (designed_braam_braam_stinger) -6 dB<br>MUSIC: 0.00 track in at -10 dB under the voice<br>MUSIC: hit on "prove" |
| 2 | 4.3-8.8 | L12 O "We've had a report of an unauthorized person at this address." | 4.3 bust: officer medium-close, bodycam on chest visible, bg porch [talk + polite smile that never reaches the eyes]<br>7.0 ins: insert: bodycam red REC dot ECU (draw on bust crop, push 4.5 %/s) NEW | tag "BODYCAM: REC" red/white pop with ui_pop<br>caption "UNAUTHORIZED" red | bodycam_beep at the insert<br>police_radio_squelch -12 dB outside |
| 3 | 8.8-11.2 | L13 N "You tell him you live here." | 8.8 hall: you behind the door, vertical crop on you, hand flat on the door [you: nervous, glance at peephole] | speech-bubble tag "I LIVE HERE." (unvoiced; it plants Short 2) | breath close<br>footsteps_wood_inside 1 step |
| 4 | 11.2-13.7 | L18 O "That's what the other gentleman said." | 11.2 bust: officer 3/4, head turned back to lens, bg car out of focus [look_side to car then snap_turn to lens on "OTHER"] | caption "OTHER" red with punch 125 % | stinger light on "other"<br>MUSIC: music thins for 0.4 s after the line |
| 5 | 13.7-17.8 | L19 N "Only then do you notice someone sitting in the back seat." | 13.7 street: vertical crop on the patrol car at the curb, light bar strobing<br>16.0 car: back-seat window: silhouette, head lowered, strobe across the glass [double: down(), sway] | red motion box on the window + tag "UNKNOWN"<br>MATCH meter appears: "MATCH 0%" | whoosh hard<br>car_idle -18 dB<br>ui_pop for meter |
| 6 | 17.8-21.5 | L22 N "One thumb keeps rubbing the base of his ring finger." | 17.8 hands: ECU lap: thumb rubbing the base of the ring finger, ring glint [rubbing thumb loop 0.9 s] | tag "HABIT" pinned to the thumb with leader line<br>MATCH 20% | ui_pop<br>fabric rub close -10 dB |
| 7 | 21.5-24.2 | L23 N "It's something you do when you're nervous." | 21.5 hands: VERTICAL SPLIT: top half his hands in the car (strobe), bottom half your hands in the hall doing the same rub in sync NEW | split line glitch at cut<br>labels "HIM" (top) / "YOU" (bottom) | heartbeat starts, 70 bpm, -14 dB |
| 8 | 24.2-27.2 | L43 N "The card outside has the same missing piece." | 24.2 ins: licence_window: card raised to the glass, chipped corner lit by strobe [hold_up]<br>25.7 ins: licence: your card in your hand, same chip; match-cut on the corner position | red circle on both corners<br>text slam "SAME" red<br>MATCH 40% | glass tap<br>card flick<br>impact_hit on match cut |
| 9 | 27.2-30.6 | **NEW S1-N2** "Everyone who subscribes gets to keep their own face." | 27.2 car: back-seat window ECU: his palm slaps flat on the glass, fingers spread [hand_on_glass + slow creep_smile behind the palm]<br>*45-50 % of runtime. Whispered, fast, still in story; never pauses the picture.* | SUBSCRIBE button at 74 % height (above captions), cursor taps it in sync with the palm hitting the glass -> SUBSCRIBED + bell, 1.8 s<br>tag "HIS FINGERS: SPREAD LIKE YOURS" | glass thump on the palm<br>ui click + soft bell on SUBSCRIBED<br>MUSIC: bed stays, -12 dB |
| 10 | 30.6-33.2 | L112 O "Perhaps this will clear things up." | 30.6 ins: mail_slot: flap lifts, complaint sheet slides in (feed 0 -> 1), officer's fingertips<br>32.2 hall: low angle from the floor: paper lands at your feet NEW | caption "CLEAR THINGS UP" blue | mail_slot<br>paper slide<br>whoosh soft |
| 11 | 33.2-35.6 | L117 N "The clothes you're wearing right now." | 33.2 hall: tilt down your body: the grey hoodie you're wearing; the complaint line "WEARING: GREY HOODIE" overlaid<br>34.6 ins: complaint ECU | complaint lines highlight in sequence on screen: "HEIGHT: 5'11"" / "HAIR: BROWN" / "WEARING: GREY HOODIE" (MATCH 50 -> 60%)<br>caption "RIGHT NOW" red | impact_hit<br>heartbeat 90 bpm |
| 12 | 35.6-39.2 | L119 N "Then you look at the complainant's name." | 35.6 ins: complaint_name: name field blurred, slow push 4.5 %/s<br>*TENSION GAP 1.1 s after this line: music out, only heartbeat + tinnitus + room_tone; the name un-blurs letter by letter (glitch).* | field label "COMPLAINANT:" with blinking cursor | riser 3.0 s ending on "It's yours"<br>tinnitus fades in<br>MUSIC: music duck -18 dB |
| 13 | 39.2-40.3 | L120 N "It's yours." | 39.2 ins: complaint_name ECU: YOUR NAME + signature, the last-letter mistake circled<br>*Twist A at about 70 % of runtime.* | text slam "IT'S YOURS." red, full width<br>MATCH 80%<br>red flash 2 frames | braam (distorted_straight_e) + sub_drop<br>impact big<br>MUSIC: TRACK SECTION CHANGE here (from_hell 53.2 s, loud) |
| 14 | 40.3-42.2 | L126 N "light, you finally see his" (words 7-11 of the line) | 40.3 peep: the man from the back seat walks up the path into the porch light, grey coat, loose thread at the cuff [walk(from car, to door) then stop under the light, head rises] | tag "GREY COAT" pinned (leader line) | car_door_close (pre-roll 0.5 s)<br>footsteps_porch x4<br>whoosh |
| 15 | 42.2-43.6 | L127 N "It's almost yours." | 42.2 bust: double ECU, bg porch, impatient [dead_stare -> creep_smile over 1.5 s] | tags pop one by one: "SCAR: WRONG SIDE", "RING: WRONG HAND" (leader lines)<br>MATCH 99% glitches "99% ... ERROR" | ui_pop x2<br>glitch |
| 16 | 43.6-44.5 | L132 D "That's him," | 43.6 door: doorbell fisheye: the double points straight at the lens, officer behind him [pt(dx=0)] | caption "THAT'S HIM" in quotes, amber | stinger |
| 17 | 44.5-46.5 | L133 N "he says in your voice." | 44.5 wave: waveform panel, two rows "YOU" / "HIM" identical, bust double behind NEW | "MATCH 100%" red stamp | radio_static short<br>ui_pop |
| 18 | 46.5-49.2 | L134 D "That's the man in my house." | 46.5 door: ECU fisheye: the double leans into the lens until his grin bulges; officer's head tilts behind [lean_in 1.4 + wide_grin; officer head_tilt] | text slam "THE MAN IN MY HOUSE"<br>red flash | impact_hit<br>static burst 0.3 s<br>MUSIC: hit, then pad only |
| 19 | 49.2-53.5 | **NEW S1-N3** "Seven rules keep you alive. The full video is on the channel." | 49.2 rule: rule cards flick 1 -> 7 vertically (0.15 s each), stop on a card reading "FULL VIDEO ON THE CHANNEL" NEW | comments panel slides up for 1.2 s: "Comment BACK SEAT if you'd keep the door shut" (on screen only)<br>clock 12:41 AM | rule sting<br>card flick ticks x7<br>MUSIC: bed continues |
| 20 | 53.5-54.3 | (no voice) | 53.5 black: black, then 8-frame REWIND glitch to frame 1 NEW | - | knock_door n=2 (same sample as frame 1)<br>tape-rewind glitch |

### S2 timing table (estimated 53.8 s, 131 words, "you/your" x9, 27 shots before punch-ins)

| # | Time (s) | Voice | Picture (9:16) | Overlays | Sound |
|---|---|---|---|---|---|
| 1 | 0.0-1.6 | L64 Y "I live here." | 0.0 ins: radio insert ECU on the officer's shoulder, red LED blinking, grille fills the frame NEW<br>*Radio-voiced (fx radio, as in the long video). First word at 0.25 s.* | HUD "PLAYBACK #1" + REC dot<br>live waveform under the caption<br>caption in quotes "I LIVE HERE." amber | 0.00 police_radio_squelch close<br>0.00 radio_click<br>MUSIC: 0.00 track in at -11 dB<br>MUSIC: sub hit at 0.0 |
| 2 | 1.6-4.7 | L63 N "You'll hear your own voice coming through it." | 1.6 hall: you inside, snap_turn toward the door, ECU on the eyes [snap_turn + shock] | text slam "YOUR VOICE" amber, 2 lines | whoosh hard<br>impact_hit on "own voice" |
| 3 | 4.7-6.2 | L66 N "Then it plays again." | 4.7 wave: waveform panel over the officer bust (left), PLAYBACK #2 | HUD PLAYBACK #2 | radio_click<br>ui_pop |
| 4 | 6.2-8.2 | L67 N "This time, something is wrong." | 6.2 peep: peephole: officer lifts the radio, head cocked [radio + creep()] | - | radio_static -16 dB |
| 5 | 8.2-11.2 | L68 N "The pause between the words is too long." | 8.2 wave: waveform panel: gap between "I" and "live" stretched, red marker "PAUSE TOO LONG" flashing | marker "PAUSE TOO LONG" | ui_pop<br>glitch short |
| 6 | 11.2-12.6 | L69 Y "I... live here." | 11.2 ins: radio ECU, LED stutters with the pause<br>11.9 bust: you ECU, eyes wide [fear] | caption "I... LIVE HERE." with a visible stall | radio squelch<br>heartbeat starts |
| 7 | 12.6-15.6 | L70 N "see the man in the car leaning forward." (words 5-13 of the line) | 12.6 street: vertical crop on patrol car, push to the rear window<br>14.0 car: back seat: the man leans forward out of the dark into the strobe [lean_in toward the partition, wide eyes] | red motion box + tag "BACK SEAT" | whoosh<br>car_idle |
| 8 | 15.6-17.3 | L71 N "His lips are moving." | 15.6 bust: double ECU mouth (bg car), lips shaping "I live here" silently [talk() with mouth only, dead_stare] NEW | ghost caption "i live here" in small lowercase, lip-synced, 30 % opacity<br>tag "PRACTISING" | whisper layer (crowd_whisper -20 dB) |
| 9 | 17.3-17.9 | L73 O "Again," | 17.3 bust: officer radio_to_mouth, thumb on PTT [radio + creep_smile] | HUD PLAYBACK #3 | radio_click<br>squelch |
| 10 | 17.9-19.2 | L76 Y "I live here." | 17.9 car: back seat ECU: his mouth moves IN SYNC with the radio voice [talk on the radio timing]<br>18.6 wave: two waveform rows "YOU" / "BACK SEAT" sliding into alignment NEW | caption "I LIVE HERE." amber | radio voice |
| 11 | 19.2-21.2 | L77 N "This time, it sounds right." | 19.2 car: he sits back, slow creep_smile in the strobe [creep_smile] | "MATCH 100%" green stamp | braam washed -8 dB |
| 12 | 21.2-23.2 | L79 O "Good. Now your name." | 21.2 door: fisheye: officer leans into the lens, head tilt, grin widens [lean_in + head_tilt + wide_grin] | text slam "NOW YOUR NAME." red | impact_hit<br>static 0.2 s<br>MUSIC: drop to pad for 0.6 s |
| 13 | 23.2-26.6 | **NEW S2-N1** "Everyone who subscribes gets to keep their own voice." | 23.2 hall: you press your hand over your mouth, back to the door [hand_mouth + tremble] NEW<br>*45-50 % of runtime, whispered.* | SUBSCRIBE button at 74 % height, pressed -> SUBSCRIBED + bell; waveform under it flattens to silence as it is pressed | ui click + bell<br>muffled breath |
| 14 | 26.6-27.9 | L83 N "It's your mother." | 26.6 ins: radio ECU, new waveform row labelled "MUM" in pink | HUD PLAYBACK #4 | radio_static<br>radio_click |
| 15 | 27.9-31.3 | L85 M "Have you found him? Is he all right?" | 27.9 peep: officer holds the radio up toward the peephole [radio(side=1) lifted to the door]<br>29.8 mumroom: flash 0.4 s: mum's empty armchair, phone face down (foreshadow) NEW | caption in quotes, pink | radio fx on voice<br>room tone shift on the flash |
| 16 | 31.3-34.6 | L88 N "The small cough she never quite manages to clear." | 31.3 wave: waveform with a "COUGH" marker at a fixed spot | marker "COUGH" | ui_pop |
| 17 | 34.6-36.9 | L98 N "Your mother says your childhood nickname." | 34.6 bust: you ECU, eyes wet, hand moving to the lock [sad -> tremble] | HUD PLAYBACK #5 (her second take)<br>caption shows the nickname as a bleeped bar "████" | soft bleep tone under radio |
| 18 | 36.9-42.0 | L100 N "The second time, the cough comes in exactly the same place." | 36.9 wave: two stacked copies of her sentence; the COUGH markers line up perfectly; red vertical line drops through both NEW<br>*TENSION GAP 1.2 s: only radio hiss and heartbeat.* | stamp "IDENTICAL" red<br>red flash | riser 2.5 s ending on the click<br>impact on "same place"<br>MUSIC: music out after the line |
| 19 | 42.0-45.8 | L101 N "You'll hear a quiet click before the sentence starts over." | 42.0 ins: radio ECU: the LED stops, a tiny "click", the waveform snaps back to the start with a loop icon NEW<br>*Twist at about 78-82 % of runtime.* | text slam "IT'S A RECORDING" red<br>loop icon | radio_click loud, dry<br>braam + sub_drop<br>MUSIC: TRACK SECTION CHANGE here (46.2 s) |
| 20 | 45.8-46.8 | L103 O "Poor reception." | 45.8 bust: officer lowers the radio fast, smile gone -> dead_stare into the lens [snap down + dead_stare] | - | radio off clunk |
| 21 | 46.8-48.7 | L105 N "Her line will be busy." | 46.8 phone: phone UI: calling MUM -> BUSY, pushes in | phone UI "BUSY" | phone_busy tones x3 |
| 22 | 48.7-53.1 | **NEW S2-N2** "Where's your mother? Find out in the full video on the channel." | 48.7 mumext: mum's house at night, one window lit, patrol-car strobe sweeps across it NEW | card "FULL VIDEO ON THE CHANNEL" lower-middle<br>comments panel 1.2 s: "Comment MUM if you'd hang up" (on screen only) | busy tone continues under<br>car_pass |
| 23 | 53.1-53.8 | (no voice) | 53.1 ins: radio ECU, LED blinks once -> REWIND glitch to frame 1 NEW | - | radio_click (same as frame 1) |

### S3 timing table (estimated 54.2 s, 132 words, "you/your" x15, 31 shots before punch-ins)

| # | Time (s) | Voice | Picture (9:16) | Overlays | Sound |
|---|---|---|---|---|---|
| 1 | 0.0-2.8 | L146 O "What color are the kitchen tiles?" | 0.0 peep: peephole ECU: officer with notebook and pen, face bulging toward the lens [lean_in 1.2 + creep_smile] NEW<br>*First word at 0.25 s.* | HUD "QUESTION 1/5"<br>caption "KITCHEN TILES" blue, in quotes | 0.00 pen_click close<br>0.00 impact_hit soft<br>MUSIC: 0.00 track in -11 dB<br>MUSIC: braam 0.0 -8 dB |
| 2 | 2.8-3.3 | L148 D "Green," | 2.8 bust: double ECU, bg porch, answers instantly [calm_smirk] | caption "GREEN" green<br>score "HIM ✓" | ui_pop<br>whoosh |
| 3 | 3.3-5.3 | L150 N "Your kitchen tiles are blue." | 3.3 kitchen: your kitchen, blue tiles, light from the hall<br>4.3 ins: tiles insert ECU | caption "BLUE" blue, punch 130 % | impact_hit<br>room_tone inside |
| 4 | 5.3-8.4 | L142 N "Don't correct anything the other man gets wrong." | 5.3 rule: RULE 5 card (speech bubble with a cross icon), vertical layout, officer swaying behind the blur | text slam "DON'T CORRECT HIM" red<br>red flash | rule sting |
| 5 | 8.4-12.1 | L143 N "The officer will suggest asking you both a few questions." | 8.4 door: fisheye wide: officer and the man in your grey coat side by side; both snap their heads to the lens on "both" [snap_turn x2 in unison] | tags "HIM" and "YOU?" pinned | whoosh<br>stinger light |
| 6 | 12.1-14.3 | L157 N "The name of your first pet." | 12.1 ins: photo insert: a dog in a frame (first pet)<br>13.2 bust: double answers, lips moving silently [talk mouth only] | HUD QUESTION 2/5<br>score "HIM ✓" | ui_pop<br>impact soft |
| 7 | 14.3-16.3 | L158 N "Where you went to school." | 14.3 bust: double, eyes flick to the officer before answering [nervous_glance] | HUD QUESTION 3/5<br>score "HIM ✓"<br>tag "HE CHECKS THE OFFICER" | ui_pop |
| 8 | 16.3-19.3 | L159 N "What your mother calls you when she's worried." | 16.3 bust: you ECU, sweat, lips pressed shut [sweaty + m_press]<br>18.1 mumroom: flash 0.3 s: your mother by her phone NEW | HUD QUESTION 4/5<br>score "HIM ~" | heartbeat 80 bpm<br>phone vibrate faint on the flash |
| 9 | 19.3-20.0 | L162 N "Don't." | 19.3 kitchen: ECU your hand gripping the table edge, knuckles white NEW | text slam "DON'T." red | impact_hit |
| 10 | 20.0-21.7 | L168 O "Who took that picture?" | 20.0 hall: push along the hallway to the framed photograph<br>20.8 bust: officer, head tilt [head_tilt + creep_smile] | HUD QUESTION 5/5<br>tag "YOU NEVER MENTIONED IT" | stinger light<br>pen_click |
| 11 | 21.7-22.7 | L170 D "My mother." | 21.7 bust: double ECU, confident [creep_smile] | score "HIM ✗" red stamp | buzzer-like low hit |
| 12 | 22.7-24.3 | L171 N "It was your father." | 22.7 ins: photo insert, push; tag "TAKEN BY: DAD" | - | impact_hit |
| 13 | 24.3-27.4 | **NEW S3-N1** "Everyone who subscribes knows which one is real." | 24.3 bust: VERTICAL SPLIT: top the double, bottom you, same framing; the double's half glitches as the button is pressed NEW<br>*45-50 % of runtime.* | score now "HIM ✗" vs "YOU ✓ (silent)"<br>SUBSCRIBE button on the split line (at 52 % height), pressed -> SUBSCRIBED + bell | ui click + bell<br>glitch |
| 14 | 27.4-31.6 | L174 N "After a few seconds, he turns off his camera." | 27.4 ins: bodycam ECU, red REC dot goes out NEW<br>29.3 bust: officer, smile drops to dead_stare [dead_stare]<br>30.6 bust: double looks worried [nervous]<br>*TENSION GAP 1.0 s: room tone, heartbeat, then a dial tone fades in.* | tag "CAMERA OFF" | bodycam_beep (off tone)<br>MUSIC: music out after the line |
| 15 | 31.6-33.9 | L220 N "Then you try your mother again." | 31.6 phone: phone UI: calling MUM -> connected, waveform live | clock jumps to 1:14 AM | phone_ring 1x<br>phone_pickup |
| 16 | 33.9-36.5 | L222 M "Thank goodness. Are you all right?" | 33.9 mumroom: mum answers in her armchair, relieved [mum: sad -> polite] | caption pink, in quotes | phone fx on voice |
| 17 | 36.5-38.8 | L227 N "She tells you he called earlier." | 36.5 mumroom: mum on the phone in her cardigan, lamp light [mum: nervous]<br>*Twist starts here (about 67 %); it lands on "The photograph your father took." (about 78 %).* | text slam "HE CALLED HER" red | braam + sub_drop<br>MUSIC: TRACK SECTION CHANGE here (in_continuum 50.4 s) |
| 18 | 38.8-40.7 | L229 N "He asked a few questions" (words 1-5 of the line) | 38.8 ins: notebook insert: the officer's handwriting fills in an ANSWER KEY NEW | - | pen scribble |
| 19 | 40.7-41.9 | L230 N "Your first pet." | 40.7 ins: notebook: "FIRST PET ✓" | - | impact |
| 20 | 41.9-42.7 | L231 N "Your school." | 41.9 ins: notebook: "SCHOOL ✓" | - | impact |
| 21 | 42.7-44.9 | L232 N "The photograph your father took." | 42.7 ins: notebook: "PHOTO: FATHER ✓" underlined twice; flash cut to the double smiling | text slam "NOW HE KNOWS" red<br>red flash | impact big<br>stinger |
| 22 | 44.9-46.9 | L242 N "There's knocking at her door." | 44.9 mumext: mum's porch: the officer and the man in your coat; knock [knk n=3] | clock 1:16 AM | knock_door n=3 (through the phone, then real)<br>whoosh |
| 23 | 46.9-49.2 | L249 M "He looks just like you." | 46.9 curtain: mum pulls the curtain: the double outside in the strobe looks up at her [double: creep_smile -> wide_grin; mum: cry] | caption pink, in quotes | curtain rings scrape<br>phone fx on voice |
| 24 | 49.2-53.6 | **NEW S3-N2** "Does she open the door? Watch the full video on the channel." | 49.2 mumext: ECU mum's door handle and lock, a key hovering, strobe across it NEW | card "FULL VIDEO ON THE CHANNEL"<br>comments panel 1.2 s: "Comment BLUE if you stayed silent" (on screen only) | key jingle faint |
| 25 | 53.6-54.2 | (no voice) | 53.6 peep: mum's peephole: the officer, notebook up -> REWIND glitch to frame 1 NEW | - | pen_click (same as frame 1) |
