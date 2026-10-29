# "If X knocks… NEVER OPEN UP": how the format works

This analysis covers *If A Firefighter Knocks At Night With No Fire… NEVER OPEN UP* and *If Everyone In Your Hotel Starts Crying… LEAVE RIGHT NOW*.

**How it was measured**

* Contact sheets: one frame every 3 s across both videos.
* Full-resolution stills of the key moments.
* Cut detection.
* A timed transcript of the firefighter video (Parakeet ASR).
* EBU R128 loudness.

I can't listen to the audio, so the sound section covers only what can be measured.

## 1. The numbers

| | Firefighter | Hotel |
|---|---|---|
| Length | 8:18 | 9:00 (of 12:06) |
| Narration | 1,387 words, **167 wpm** | similar, slow and calm |
| Pauses over 1 s | 20 (longest 1.8 s) | n/a |
| Detected cuts | 102 (median shot 2.9 s, mean 4.9 s) | n/a |
| Loudness | −14.4 LUFS, LRA 3.2 LU | −14.6 LUFS, LRA 4.1 LU |
| Rules | 7 | 7 |

**Reading the numbers**

* **Narration:** slow and calm, about half the pace of a Shorts narrator. The calm voice describing wrong things is the main source of dread.
* **Loudness:** very even, with no loud jump scares in the mix. The fear comes from the information, not from volume.

## 2. Script structure (the firefighter video)

1. **Cold open (0–15 s): the whole premise in one breath.** "If a firefighter ever knocks… but there's no smoke, no flames… never open up. Don't unlock the door, don't step on the porch, and whatever you do, don't tell them how many people are inside." The last clause is a hook: why would that matter?
2. **The setup in second person, present tense.** "You're watching TV when three heavy knocks shake your front door." The viewer *is* the victim.
3. **Small wrong details, listed calmly:**
   * the truck has no lights on;
   * he doesn't answer the question;
   * he checks a notebook;
   * he asks "is it just you tonight?";
   * the neighbour opens her door and her porch light goes out.

   None of these is scary alone, but together they are.
4. **"There are seven rules you need to follow."** Each rule is a title card followed by a mini-scene that shows why the rule exists. Each one escalates the threat:
   * he only knocks;
   * then taps the window;
   * then the smoke alarm;
   * then fake 911 answers;
   * then a second truck;
   * then the house "on fire";
   * then the real firefighters arrive.
5. **The final twist recontextualises everything.** The thing at the door was only a distraction, and the real one is already inside: muddy boots by the basement door.

## 3. Visual style

* **Flat vector illustration.** Thin dark outlines, one shade tone per material, no gradients on characters.
* **Palette:**
  * night navy (`#0a1226`–`#1c2c4c`);
  * warm interior browns;
  * warm window glow (`#f2c46b`);
  * accents of red (alarm, truck, red light) and blue (police lights, screens).
* **Finish on every frame:** a heavy vignette, film grain and a slight softness.
* **Characters are simple:**
  * a box face;
  * big round white eyes with small pupils;
  * an "L" nose and a small mouth;
  * a blocky uniform.

  Simplicity makes the wrongness obvious, because one change to the face reads instantly:
  * a grin that is far too wide, with a full grid of teeth;
  * tears while smiling;
  * staring straight into the peephole;
  * standing too still.
* **Text:**
  * Captions: one sentence per screen, white uppercase geometric sans with letter-spacing, small, low in the frame, synced to the voice.
  * A tiny persistent header, "HOUSE RULES / RULE 4 OF 7", keeps the viewer oriented and feeds the "just one more rule" binge.

## 4. How they build tension visually

1. **Point of view is the viewer's eye.**
   * **Peephole:** a circular fisheye in a black frame. You see only what the character lets you see.
   * **Doorbell or CCTV:** LIVE, timestamp, face box.
   * **Phone in your hand.**
2. **Diegetic screens as evidence.** These make the threat feel documented rather than imagined:
   * the 911 call with its timer and waveform;
   * dispatcher text: "units near you: none";
   * a notebook counting people per house;
   * a chalk "1" next to your doorbell;
   * truck-speaker waveforms proving the voice is a recording.
3. **Light as the threat meter.**
   * A porch light goes out when someone is taken.
   * Red and blue washes sweep the ceiling.
   * A red glow comes from the kitchen, and the screen tints red during the climaxes.
   * Darkness and black frames work as pauses.
4. **Stillness.** Long holds with slow push-ins, and characters that don't move. Motion is rare, so every small movement (a head turn, a tap on the glass) lands.
5. **Repetition with variation.** The same truck, the same knock and the same sentence come back slightly wrong. A second truck has the same number, and the voice repeats exactly.
6. **Reveals timed to single words.** The cut to the grin lands on "Not a normal smile."
7. **Rule cards with a progress bar.** They give structure and a promise of more, and they give the viewer a breath before the next escalation.

## 5. Animation (limited, cut-out style)

* **Camera:** slow push-ins and pans over layered flat scenes with a little parallax.
* **Characters:** a head turn, an arm raise, a blink, a mouth swap, an expression swap at the reveal.
* **Effects:** light flicker and colour washes, fog sprites, waveform and phone-UI animation, typed text on the rule cards.
* **Transitions:** mostly hard cuts, with dissolves and fades to black between rules.

## 6. Thumbnails (one template, every video)

* **Left half:** solid red with a two-word command in heavy geometric sans. The first word is white with a soft dark drop shadow ("NEVER", "LEAVE", "DON'T"), the second is black ("OPEN", "NOW", "MOVE", "LOOK").
* **Arrow:** a thick white hand-drawn arrow with a black edge, curving from under the words into the face.
* **Right half:** a white-bordered, round-cornered image of the antagonist, close and centred.
* **The face:** red irises, dark sockets, a huge grin with every tooth showing. Behind it is either a doorbell or CCTV UI (LIVE, FRONT DOOR, timestamp, a "HUMAN 2%" face box) or a crowd of grinning faces.

## 7. How we make it

* **Engine:** `horror.py`, a skia 2D renderer for flat shapes, plus a numpy post pass for vignette, grain, softness, fisheye and peephole. A 1080p frame draws in about 1–2 s on this machine's CPU. In video, the static layers are drawn once, so a 10-minute video renders in hours, not days.
* **Kit:**
  * a character kit with calm and creepy variants of each character;
  * set pieces (street at night, porch, hallway, living room);
  * a UI kit (doorbell cam, peephole, phone 911, dispatcher chat, rule card, header);
  * a thumbnail template.
* **Test frames:** in `cop_frames.py`, for "If A Police Officer Knocks At 3 AM… NEVER OPEN THE DOOR".
