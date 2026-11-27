# Reference Shorts analysis (4 viral "What if..." Roblox Shorts)

Owner's 4 references, all vertical 9:16 at 60 fps (ref3 is 1080x1920, the others 720x1280).

| # | Title | Length |
|---|---|---|
| ref1 | What If Your MOM Started Playing Roblox? | 50.8 s |
| ref2 | What If Your BEST FRIEND Quit Roblox? | 55.1 s |
| ref3 | What If MOM Gave You 10 Seconds of Roblox? | 50.0 s |
| ref4 | What If You Got 1 ROBUX Every Time You Blinked? | 56.7 s |

How this was measured: narration was transcribed with sherpa-onnx (Whisper base.en int8 plus the Silero VAD). Words that Whisper misheard ("roebox", "Noob King") were checked against the captions in the frames. Cuts come from ffmpeg `scdet` (threshold 10 at 180x320, with cuts closer than 0.2 s merged). "Visual events" are frame-difference peaks with score above 4 spaced at least 0.25 s apart, which counts zoom punches, pops and flashes as well as cuts. Loudness is EBU R128. Music and voice levels are the RMS of 50 ms frames inside VAD speech, compared with the quietest 10 % of frames. SFX were counted as high-band (above 2 kHz) spectral-flux onsets at two thresholds.

The contact sheets are in `/tmp/claude-0/-home-user-claude-todo-demo/aa250ae7-a0b4-594f-9bc6-bd18b596cf27/scratchpad/shortref/`:
- `sheet1.jpg` to `sheet4.jpg`: 1 frame per second, with the second number in the corner.
- `hook1.jpg` and `hooks234.jpg`: the first 3 s at 4 fps. The burned-in labels are offset by +2.0 s, so the label "2.00" is t=0.

---

## 1. Measured numbers at a glance

| Metric | ref1 | ref2 | ref3 | ref4 | Playbook target |
|---|---|---|---|---|---|
| First spoken word | 0.32 s | 0.25 s | 0.28 s | 0.25 s | **≤ 0.3 s** |
| Title question finished | 2.7 s | 4.3 s* | 3.1 s | 3.7 s | **≤ 3.5 s** |
| Words | 114 | 135 | 124 | 122 | **115–135** |
| WPM, whole video | 135 | 147 | 149 | 129 | **130–150** |
| WPM while talking | 159 | 154 | 175 | 157 | **155–175** |
| Share of runtime with speech | 85 % | 95 % | 85 % | 82 % | **82–95 %** |
| Average words per sentence | 6.0 | 5.0 | 6.5 | 5.3 | **5–6.5, max ≈ 14** |
| "you/your" count | 6 | 9 | 10 | 13 | **≥ 1 per 5 s** |
| Gaps between phrases | 0.18–0.75 s, with one 1.0 and one 1.7 s | 0.15–0.37 s | 0.18–0.98 s | 0.18–0.66 s, plus 1.1, 1.5 and 2.7 s | **0.2–0.4 s; 1–2 dramatic gaps of 1–2.7 s near the climax** |
| Hard cuts | 35 | 37 | 14 | 52 | **30–50** |
| Median shot | 1.03 s | 1.10 s | 2.77 s | 0.97 s | **≈ 1.0 s** |
| Longest shot | 5.4 s | 4.8 s | 11.2 s** | 6.4 s | **≤ 5 s** |
| A visual event every | 0.74 s | 0.76 s | 1.22 s | 0.67 s | **≤ 0.8 s** |
| Integrated loudness | −14.0 LUFS | −14.0 | −14.0 | −14.0 | **−14 LUFS** |
| Loudness range | 1.9 LU | 2.2 | 1.6 | 1.8 | **≤ 2.5 LU** |
| Sample peak | −0.5 dBFS | −0.1 | −0.9 | −0.4 | **≤ −1 dBTP** (theirs is slightly hot) |
| Voice level vs quietest bed | −17.9 / −25.8 dB | −19.2 / −30.3 | −17.7 / −27.2 | −18.8 / −27.5 | **music 8–11 dB under the voice** |
| Silence below −45 dB | 0.3 s | 0.4 s | 0.8 s | 0.2 s | **never more than 1 s of true silence** |
| Strong SFX hits per 10 s | 4,6,2,3,3 | 3,5,3,6,4 | 5,5,3,1,4 | 4,5,3,3,3,5 | **3–6** |
| All transients per 10 s | 12–15 | 11–18 | 7–18 | 9–17 | **12–16** (whooshes, pops, dings) |
| Subscribe call | none | 24.9 s (45 %) | 24.8 s (50 %) | 26.7 s (47 %) | **at 45–50 % of runtime** |
| End comment prompt | 47.1 s | 50.6 s | 47.4 s | 54.6 s | **in the last 3–5 s** |
| Loop device | whip-blur back to the start | "REWIND" overlay | "REWIND" overlay | whip-blur back | **always** |

\* ref2 adds a fake chat line and a three-line exchange inside the hook.
\*\* ref3 holds one bedroom set for a long time but moves the camera and punches in on every count.

---

## 2. Per-reference breakdowns

### ref1: "What If Your MOM Started Playing Roblox?" (50.8 s)

**Hook (0–3 s).** It opens on an extreme close-up of Mom in a glowing RGB gaming headset at 3 AM, smirking. The captions run "What if" (white), "your MOM" (pink), "started", "PLAYING" (green), "ROBLOX?" (yellow) at about 2.5 chunks per second. On "PLAYING" her eyes go wide with gritted teeth, and on "ROBLOX?" the camera zoom-punches to a manic grin. At 2.7 s it hard-cuts to a flashback. **Why it stops the scroll:** an absurd role reversal (Mom as a gamer) and an expressive face filling the frame. The question is asked inside the first 2.7 s.

**Beats:**
- 0–6 s, setup: "What's so special about this blocky game? Give me that." A "YOINK!" burst as she grabs the tablet.
- 7–15 s, Day 1: she spawns as a noob and walks into a wall "for 10 minutes". A "10 MIN" clock gag. "Which button is JUMP?!" is the first character line, in her voice.
- 15–20 s, Day 2: she beats the hardest obby (Stage 97 to 99) "while folding laundry".
- 20–25 s, Day 3: "the Noob King spawns. Mom takes off her slipper. Critical hit." Boss bar, a slow-motion slipper swing, "K.O.!".
- 25–30 s, Day 4: number 1 on every leaderboard, with a fashion leaderboard insert. "They call her the SLIPPER QUEEN" and a golden slipper throne.
- 30–45 s, Day 5 (role reversal, which is the twist): an alarm clock reads 3:00 A.M. and the kid now says Mom's own line, "10 seconds, then you go to bed." "Just one more round!" "Did you spend my ROBUX?!" "It was for a pet… for you, sweetie." A MYTHIC golden flying slipper reveal, then "BONK!".
- 45–47 s, tag twist: "And then… Grandma logged in." A server-join message and GrandmaGamer_1942.
- 47–50.8 s, CTA and loop: a fake YouTube comments panel with a keyboard typing "GG". "Comment GG if your mom would destroy you at Roblox." A whip-blur back to frame 1.

**Why it feels complete:** five numbered days give a clear arc from incompetent to god-tier to a role reversal. The callback (Mom's own bedtime line turned on her) closes the loop, and a final topper gag tops the climax.

### ref2: "What If Your BEST FRIEND Quit Roblox?" (55.1 s)

**Hook (0–3 s).** Two avatars under a rainbow with "BFF" hearts. The captions run "What if", "BEST FRIEND" (blue), then a fist "BUMP!" insert on a pink sunburst, then "didn't wanna", "play Roblox". A chat toast reads "MaxPro99 left the game" and the friend greys out. The shocked "?!" face lands on "ANYMORE?" at 2.5 s. **Why it stops the scroll:** a cute, warm image is broken in front of you (the greyed-out friend), and a relatable fear is stated as a question.

**Beats:**
- 3–7 s: the friend says "Roblox is for babies. I quit." The hero says "You WHAT?!" with a wide scream face.
- 7–10 s, Day 1: a game invite and a friends-list UI with a red DECLINED stamp.
- 10–14 s, Day 2: a legendary dragon pet gift comes back as "RETURN TO SENDER".
- 14–19 s, Day 3: he builds a giant "PLEASE COME BACK!" sign across the map.
- 19–24 s, Day 4: the server counter climbs 33, 269, 1,000 players, everyone spamming "COME BACK!". This is the escalation peak.
- 25–28 s, **subscribe CTA in the story:** "Everyone who subscribes gets a best friend who never quits." A cursor clicks SUBSCRIBE and it turns to SUBSCRIBED.
- 29–35 s, Day 5: peeking through the window, the friend is playing Roblox "on a secret account": TotallyNotMe123.
- 35–47 s, twist: "Okay, okay, I didn't QUIT. I've been STUCK on the same obby jump for a whole month." Insert counters: FAILS 3 to 9,999 and a calendar reading 30.
- 47–55 s, payoff, CTA and loop: "It's the first jump. The tutorial one." (1 STUD, press SPACE). "Bro… I'll carry you." "Comment CARRY if you'd help your friend too." A comments panel full of "CARRY". "I fell again!" lands on the last frame, then a "REWIND" overlay goes back to the start.

**Why it feels complete:** a mystery (why did he quit?) and a five-step escalation of effort, answered by a humiliating, relatable reveal. Then an emotional resolution (carry) and a final punchline.

### ref3: "What If MOM Gave You 10 Seconds of Roblox?" (50.0 s)

**Hook (0–3 s).** A night bedroom. Mom's hand slams a red alarm clock reading 0:10, and a persistent "0:10" timer sits at the top centre. The captions run "What if", "your MOM" (pink), "only", "gave you", "TEN" (red), "seconds of", "ROBLOX?" (yellow). The kid's face is sweating. **Why it stops the scroll:** a ticking countdown is on screen from frame 1, so the viewer is promised the video ends when it reaches zero. The built-in timer is a retention device.

**Beats:**
- 3–9 s: Mom says "10 seconds. Then you go to bed." The kid says "TEN SECONDS? That's nothing… unless you're a SPEEDRUNNER." A zoom punch on a smug face with a lightning bolt.
- 9–31 s: the countdown is the structure. A big "SECOND 10 / 9 / 7 / 6 / 5" badge appears per beat, each beat about 3 s:
  - 10: a 100-stage obby beaten in one JUMP.
  - 9: the Noob King, one PUNCH, K.O.
  - 8: "he drops a billion Robux" (counter 0 to 999,999,999).
  - 7: buy EVERY game pass, "even the one that turns you into a TOASTER" (absurd topper, "DING!").
  - 6: **subscribe CTA in the story:** "Everyone who subscribes gets a golden crown."
  - 5: hatch the rarest pet in the WHOLE GAME, "LEGENDARY 0.001 %".
- 31–36 s: the counting slows ("FOUR… THREE…"). Mom's face zooms in, the kid finds a "+10 SECONDS" gamepass.
- 36–44 s, climax: "More time? GIMME!" Mom DIVES, "everything goes SLOW-MO… but you're a SPEEDRUNNER." Slow motion is used as a dramatic speed ramp.
- 44–47 s, payoff: "KA-CHING! Purchase successful, +10 SECONDS." Mom in bed says "Not… AGAIN!"
- 47–50 s, CTA and loop: a comments panel, "LOOP if you watched this more than once." A "REWIND" overlay goes to the timer at 0:03 and back to the start.

**Why it feels complete:** the on-screen countdown is a progress bar the viewer trusts. Every second is a self-contained gag, and the ending loops the premise logically: +10 seconds means it starts again.

### ref4: "What If You Got 1 ROBUX Every Time You Blinked?" (56.7 s)

**Hook (0–3 s).** An extreme close-up of the kid's face lit by a tablet. A Robux coin appears over his head on "ONE ROBUX…". The camera pushes to an ultra close-up of the eyes on "every time you BLINKED?", and on the blink a "+1" pops and the top-right counter ticks to 1. **Why it stops the scroll:** a simple wish-fulfilment premise that viewers test on themselves while watching (you blink as you watch). A counter is on screen from 3 s.

**Beats:**
- 4–10 s, Day 1: "It's REAL!" "Blink, blink, blink, blink! 100 Robux!" The counter goes 0, 2, 98, 100 and a coin pile appears.
- 10–15 s, Day 2: dry, cracked eyes. Mom thinks you're winking. "Why do you keep WINKING at me?"
- 15–22 s, Day 3: "You're RICH!" The counter jumps to 1,000,000, then the Dominus, the mansion and the cosmic egg as a rapid montage, 1 item per second.
- 22–27 s, Day 4: blinking in class, everyone stares, "DING!"
- 27–29 s, **subscribe CTA:** "Everyone who subscribes gets one FREE blink." A SUBSCRIBE button is pressed.
- 29–37 s, Day 5 (antagonist): "Mom has had enough. Staring contest, sweetie. If you blink, no more Roblox." A trophy shelf: "Mom has never lost a staring contest", "VS. CAT".
- 37–47 s, climax with dramatic silences (gaps of 1.5 and 2.7 s): "One hour… THREE hours… Must… not… BLINK…" Eyes bloodshot, a fly lands on Mom's face. "Then Mom blows in your face." "NOOOO!"
- 47–53 s: "No more Roblox, sweetie!" THUD. Then the twist: "GAME UPDATED… Now every blink COSTS one Robux."
- 53–56.7 s, CTA and loop: "Comment BLINK if you just blinked." A comments panel full of "BLINK", then a whip-blur to frame 1.

**Why it feels complete:** a premise, five days of escalating stakes, an antagonist duel, a reversal of the rule itself, and a participatory CTA that ties to the premise.

---

## 3. Shared patterns

**Narration.** The narrator speaks to "you" in present tense, energetically, with big pitch swings (median F0 about 200–230 Hz). There are 1–2 character voices (Mom, the friend) with clearly different timbre, and character lines are short, under 8 words. The script is a numbered ladder: "Day 1… Day 5" in 3 of 4, and "Second 10… 5" in ref3. **Five steps** each time, about 5 s per step, with a numeric counter that climbs (100, then 1,000,000, then 1,000 players, then 9,999 fails). Every step ends on a punch word that the caption shows in UPPERCASE colour (JUMP?!, K.O.!, DECLINED, TOASTER, RICH). There are about 9–13 numbers per Short. The climax slows down: words get spaced out ("Must… not… BLINK"), with up to 2.7 s of near-silence before the payoff.

**Editing.** A hard cut or a new element lands every 0.7–1.2 s, with a cut on every new sentence. A zoom punch (scale jump of roughly 110–140 % in one frame) lands on every keyword. Slow push-ins run under dialogue. Extreme close-ups of faces and eyes are the default framing for emotions. Insert shots of fake game UI (friends list, leaderboard, shop, gamepass, server chat toast, YouTube comments panel with keyboard) make it feel native to the platform. Slow motion (ref3) and shakes on hits are used, along with whip-blur or a "REWIND" glitch as the final transition. There are no fades and no static slides.

**On-screen text.** Captions are word-synced, 1–2 words per chunk (rarely 3), and each chunk is shown for 0.25–1.0 s. They use a heavy rounded sans (black weight) in white with a thick dark outline and a soft drop shadow. Cap height is about 4.5–5 % of frame height, a chunk spans about 35–55 % of frame width, and the chunk is centred at **about 64 % of frame height**, below the face and above the YouTube UI. The keyword in each sentence takes a colour: yellow (ROBLOX, money), pink (MOM), green (actions), red (danger, numbers), blue (friend). Day titles ("DAY 1") are chunky yellow italic with an outline and a swoosh, top-left to centre, and pop in with an overshoot. A persistent HUD counter sits at the top: a Robux balance, a 0:10 timer, a Players count, STAGE nn, or FAILS. Comic onomatopoeia bursts ("YOINK!", "BUMP!", "K.O.!", "BONK!", "DING!", "OOF!", "KA-CHING!", "THUD!") appear about 1 every 5 s.

**Sound.** The mix is mastered to −14 LUFS with a loudness range under 2.5 LU (heavily compressed, so it is always loud). A music bed runs throughout, about 8–11 dB under the voice, with almost no true silence (under 1 s per Short). Strong SFX hits come 3–6 per 10 s, and transients overall (whooshes on cuts, pops on captions, coin dings) run 12–16 per 10 s. Risers go into the climax. The music drops out or ducks for the 1–3 s tension gap before the payoff, then a hit plays on the punchline.

**Ending, loop and CTA.**
- Subscribe is said by the narrator inside the story at **45–50 %** of runtime, as "Everyone who subscribes gets [an in-world reward]". The SUBSCRIBE button animation is drawn into the scene. It never pauses the story.
- The end CTA is a comment prompt tied to the premise ("Comment GG / CARRY / BLINK", "LOOP if…"), shown as a fake comments panel in the last 3–5 s.
- The last line or image is unresolved or rhymes with frame 1 ("I fell again!", "+10 seconds", "Now every blink COSTS"), then a whip or "REWIND" goes straight to the first frame, so the replay feels intended.
- No reference asks the viewer to watch a long video. They are standalone channels. For us, the long-video CTA has to borrow this same "in-story" mechanism.

**Premium cues:** a consistent character style, with thick outlines, flat shading and very expressive faces (sweat drops, anger marks, bloodshot eyes). The palette is saturated and each beat changes background colour. 60 fps motion, overshoot easing on every pop-in and particle sparkles add finish. UI mockups are clean and readable. Nothing on screen is idle for more than about 0.7 s.

---

## 4. Numeric playbook (rules for our Shorts)

1. **First spoken word by 0.3 s.** No logo, no silent establishing shot.
2. **The full premise question finishes by 3.5 s**, as 5–9 words of on-screen text. Frame 1 already shows the conflict (a face or object in extreme close-up).
3. **Length 48–56 s.** The narration ends by about 1 s before the loop cut.
4. **115–135 spoken words**, at **about 160 WPM while talking** and 130–150 WPM over the whole video. Speech fills 82–95 % of runtime.
5. **Sentences average 5–6.5 words, with a hard maximum of about 14.** Character lines stay under 8 words.
6. **Second person:** "you/your" at least 6 times, and the narration stays in present tense.
7. **A five-step ladder** of numbered beats (Rule/Minute/Day 1 to 5) at **about 5–7 s per step**. Each step raises the stakes and ends on a punch word.
8. **A visible counter or HUD from 0–3 s to the end** (timer, clock, count, number), which ticks on every beat.
9. **A cut or a new visual element every ≤ 0.8 s** on average. The median shot is about 1.0 s and no shot runs longer than 5 s without a punch-in or camera move.
10. **A zoom punch (110–140 %, 2–4 frames, overshoot) on each caption keyword**, about 1 every 2–3 s, plus a slow push-in under every dialogue line.
11. **Captions: 1–2 words per chunk, 0.25–1.0 s each.** Heavy sans, white with a black outline (about 12 % of cap height), cap height about 5 % of frame height, centred at **64 % of frame height**, and a keyword in an accent colour once per sentence.
12. **A beat title card per step** (e.g. "RULE 4") that pops with overshoot for 0.8–1.2 s, top-left to centre.
13. **SFX: 3–6 strong hits per 10 s**, with a whoosh on every cut and a pop on every title card. Total transients 12–16 per 10 s.
14. **A music bed for 100 % of runtime, 8–11 dB under the voice.** True silence never runs longer than 1 s, except one deliberate 1–2.7 s tension gap before the twist.
15. **Master to −14 LUFS integrated, loudness range ≤ 2.5 LU, true peak ≤ −1 dBTP.**
16. **The subscribe CTA comes at 45–50 % of runtime, spoken inside the story** as "Everyone who subscribes gets ___" with a reward from the story world, and an on-screen SUBSCRIBE press animation of about 2 s. It is never placed at the start.
17. **A twist at 75–85 % of runtime** that reverses the premise (the rule is broken, the role flips, or the rule changes).
18. **The end CTA in the last 3–5 s**, tied to the premise. For us it is the long-video pointer plus an optional comment prompt.
19. **Loop:** the last line stays unresolved or repeats the first line's words, followed by a 6–10-frame whip-blur or "REWIND" glitch to frame 1. Frame 1 must make sense right after the last frame.
20. **One or two comic or impact text bursts every 5 s** (for horror: "KNOCK", "CLICK", "STATIC").
21. **Platform-native inserts** (fake UI: phone, comments panel, radio transcript, police report) at least 3 times per Short.
22. **Safe zones:** nothing important in the top 8 % or the bottom 20 % of frame height, or in the right-side 12 % strip (YouTube buttons).

## 5. Translating this to Rules After Dark (police-at-midnight video)

- The references are comedy, but the mechanics carry over to horror unchanged. Swap "Day 1–5" for "Rule 1…" or a ticking clock ("12:36 AM" as a HUD that advances). Swap the comic bursts for diegetic hits (knock, radio static, camera beep). Keep music 8–11 dB under the voice, but use drones and risers instead of bouncy loops, and keep the single long tension gap before the twist.
- The long video already has the right ladder: 7 numbered rules, a two-claimant mystery ("which one of you belongs here"), and a teased payoff ("the fourth one explains why…"). Each Short should take one sub-arc with a premise, 4–5 escalation steps, a twist and an unresolved last frame, and end by deferring the answer to the long video ("the full story is on the channel").
- The "in-story" subscribe pattern adapts as something like "Everyone who subscribes keeps their door locked tonight." This is a **new line** that the owner must voice. Keep new spoken lines to about 2–3 per Short (subscribe, long-video pointer, optional comment prompt) and build everything else from existing narration.
