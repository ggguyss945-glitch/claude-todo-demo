# Team brief: "If The School Bus Stops At Midnight... DON'T GET ON" (Night Policy)

Read this whole file first. It is short on purpose; the script and the story bible are the authority on story and design.

## The job
- Channel: Night Policy. Rule-format horror told by one English narrator. Flat-vector 2D animation rendered in Python with skia on our own engine, 2560x1440, 60 fps.
- Folder: `Vox test/Bus Video/film` (F). Work files go in `F/_work` (W; gitignored).
- Starting point: the finished code of our last film (the Doctor film), copied here:
  - engine/, render.py, film.py (still the Doctor shot list; it becomes this film's), characters.py + characters_doctor.py, sets.py + sets_doctor.py;
  - film_bunny_ref.py, film_dummy_ref.py, film_police_ref.py as references;
  - audio/, tools/ (vo_*, align.py, validate.py, cast_clips.py, cast_sheets.py, sets_sheet*.py, final_chain.sh, encode_chain.sh, enc_seg.sh, deliver.sh, progress_page.py), analysis/;
  - ARCHITECTURE.md, CAST.md, SETS.md, README.md (all still about the Doctor film).
- Write this film's cast in `characters_bus.py` and its sets in `sets_bus.py`, run by characters.py / sets.py the way the Doctor modules are. Paths and names still pointing at the Doctor film must be fixed whenever you touch that code.
- Script: `Vox test/Bus Video/script/narration_en.txt` (2,185 words; read it in full).
- Story bible: `Vox test/Bus Video/script/story_bible.md`. It covers the villain design spec, cast, sets, the rules, twist seeds and the timing table.
- Voiceover: `W/narration/raw/part1.wav` (7:00) and `part2.wav` (5:22), in that order. They are 24 kHz mono TTS, about 12:22 in all. The recording is the truth for the words.
- The previous films (Doctor, Bunnyman, Dummy, Delivery, Police, Mirror) are read-only references. The sample packs in `W/samples/` are symlinks into them: read only.

## The villain: MISTER WHISTLESTOP (original character)
- The owner sent mood references: `W/ref/owner_mood_cat_1..3.jpg`. They show a creepy grinning cat mascot in a tall hat and bow tie: a fixed grin, white gloves curling around a doorframe, VHS grain and a glitchy tape. Hit that FEELING as strongly as we can.
- The owner first asked for a 1:1 Cat in the Hat. We do NOT copy that character: it is a trademarked, copyrighted character whose owner enforces aggressively, and a copy would risk takedown and a channel strike.
- Follow the story bible's spec exactly: very tall and thin, and a crooked, far-too-tall stovepipe hat.
- Hat: faded school-bus yellow with DIAGONAL black hazard bands.
- Body: a dusty grey-brown tabby, NEVER black; an off-white matted mascot face with a fixed too-wide painted grin.
- Clothes: a mustard bus-driver jacket, and a BLACK bow tie with a small red STOP-sign pin.
- Props: a silver whistle on an orange lanyard, a ticket punch and a clipboard.
- Hands: white gloves with one knuckle too many.
- Movement: he never walks; he tape-skips closer at every flicker, with tracking lines.
- Never use red-and-white stripes, a red bow tie, a black-body/white-face/white-glove scheme, or Seuss props or words.
- His grin never moves, not even when he talks; he never lip-syncs.
- He must feel ACTIVE and dangerous every time he is on screen. The owner's main complaint about the last film was a passive villain.

## Message and values (the owner's request)
- The owner is a Muslim creator. Every video should carry love, peace, respect and kindness, and be genuinely helpful, without preaching.
- This film teaches four things:
  - a family code word (the grown-up says it first; once it leaks, change it);
  - knowing your name doesn't make someone safe;
  - no ride without a yes from home;
  - "hurry, just you, our secret" means you tell.
- Kindness: sit with the one who sits alone, ask their name. Respect: the real bus driver (Grandma Della) is a hero.
- Kid-safe: creepy and tense; no blood, gore, injury close-ups, romance or profanity. The 911 call and the real adults are warm and competent. The villain's world is sickly amber/sodium and VHS-dirty; home and morning are warm and safe.
- The advice in the outro must be legible on screen when the narration says it.

## The owner's feedback. This film must fix ALL of it; it is the bar every teammate is judged by

### Picture
1. Noticeable mistakes and off frames ruin the whole movie, above all in WIDE scenes, where character positions, scale and object placement go wrong. Examples from an older film:
   - a doll floating near the ceiling;
   - Mom standing ON the couch seat;
   - a stiff row of characters standing in a hall;
   - a mug jumping into a hand while also still on the table.
2. 3D-style shots where only the camera moves while the characters stand still are weird, long and boring.
   - PREFER CUTS.
   - Move the camera only when the move is short and motivated, with the characters acting during it.
3. Show EXACTLY what the narration says, line by line.
4. Smooth animation:
   - correct facing and eyelines;
   - hands that reach and touch what they handle, and props attached to the holding hand (never teleporting, never duplicated);
   - feet on the floor, nothing floating, scale consistent with depth;
   - continuity across cuts;
   - believable timing with anticipation and ease;
   - no "scared jiggle" as filler.
5. Improve everything to the maximum:
   - character animation and face acting (expressions, eyes, brows);
   - lip sync on character lines only; nobody's lips move on the narrator's lines;
   - designs and sets.
6. NEW from the Doctor film: the villain was too passive and the film too long.
   - In every beat with Whistlestop, he moves, closes distance, reaches, grabs or invades.
   - Scares land hard and fast. Never linger. The outro and the comment prompt are short and creative.
   - Length (the owner, 18 Nov): about 12.5 minutes is exactly right.
     - Never pad toward 15 minutes.
     - Never slow down or time-stretch the voice, and never lengthen gaps or hold shots to gain time.
     - The film's length is the tight voice edit plus only the short beats a card or a scare truly needs.

### Sound
7. Voiceover:
   - Remove breaths, clicks, mouth noises and TTS glitches.
   - Pace every gap for its moment.
   - The narrator's voice must NOT be changed (only cleaned).
   - Character lines get voice processing so they sound like those characters.
8. SFX: use only what truly fits and sounds professional. Build or find what is missing, and record every source and licence in audio/ATTRIBUTION.md. No cheesy library screams.
9. The owner loves a tune that keeps returning, warped, to build tension:
   - The Dummy film had the 1974 show tune; the Bunnyman film had the Pemberton's jingle.
   - This film's is the "Ride Right with Mister Whistlestop!" theme: an ORIGINAL cheerful 1994 kids'-TV/PSA jingle that we compose, plus his two-blast whistle "Fweet-fweet".

## Lessons from our earlier reviews: avoid these from the first pass
- Props teleported between cuts.
- Hands drawn detached from the arm, or painted on a back view; a forearm rising from the frame edge with no shoulder.
- Characters looking at the lens instead of what the line is about. Lock eyelines on the prop or person.
- Stiff rows of characters facing the camera. Give reactions, 3/4 two-shots, weight shifts and breathing.
- A default set state contradicting the line (a door said to be open was shut). Check every set state against the narration.
- Big actions read as one rigid body rotation. Stage them as clear beats: insert, medium, close-up.
- Reveals as frozen stills on a void. Stage reveals with the real set behind, varied framings and motion, and keep captions clear of the key face.
- One expression for every beat. Plan an expression state per beat.
- Lying bodies drawn as a rotated standing figure. Draw them lying.
- Insert hands cruder than the cast's hands. Every insert hand needs shaded skin, knuckles, nails, the right sleeve cuff and a believable arm.
- Absolute times hard-coded in film.py. Key every event to line and word times from timeline.json.
- The voice edit split words at line boundaries:
  - Never split inside a word; split only in a real energy dip.
  - Re-recognise every line on its own, and fail the build on any mismatch (tools/vo_asrcheck.py).
- Scares never rising above the narration:
  - Plan the biggest scares at +6 to +10 LU momentary, with smooth releases.
  - Keep narrated lines capped.
  - Let the bed in the gaps rise section by section.
- A child voice reading as a man's falsetto. Character voices need real formant shifts, measured.
- A rare skia path op crashed the full render (engine/core.py retries). Run render.py on several heavy shots at full size before calling the film ready.
- Doctor film, lit buttons and windows: bloom made red halos (fixed in engine/post.py). Keep bright saturated lights tight.

## Rules
- Work only inside `Vox test/Bus Video`. Never modify other film folders; reading them is fine.
- Never commit (the main session commits).
- No AI model names in any file.
- Never read files matching /root/.claude/uploads/*env*.
- Never copy licensed Epidemic audio out of the samples folders.
- Machine: 4 cores, 15 GB RAM, about 4.5 GB free disk, shared by up to three teammates at once:
  - At most 2 CPU-heavy processes each.
  - Test renders as stills, strips or short clips. Delete large intermediates when done.
  - Long jobs die if the container restarts: keep them resumable.
- Look at your own renders and measurements (Read the images) and fix what looks off before reporting.

## Work lean (the owner's usage budget is tight: a hard requirement, as important as quality)
Every step re-reads your whole context, so its size is the cost.
- Read code with grep / sed -n ranges, never whole big files: the characters_*, sets_* and film* files are thousands of lines. Tail or grep logs; never print long outputs.
- Look at images at most 1280 px wide. Prefer one contact sheet or strip over many stills, and never re-read an image you already judged.
- Make edits as small targeted patches.
- Trust what teammates finished and documented.
- Final report under 350 words: what you did, results, open problems, paths and commands.

## Ownership notes (coordinator, 18 Nov 16:40 UTC)
- A teammate is REDESIGNING Mister Whistlestop's head, face, fur and posture in characters_bus.py now (until about 19:00 UTC). The public API stays the same.
  - The film team must not edit the Whistlestop drawing functions in characters_bus.py.
  - Use his staging calls as they are. Write any change you need into `_work/handoff/requests.md`.
- Another teammate is re-pacing the voice edit to about 13 minutes and will re-align. Always read times from `_work/align/timeline.json` at run time; never copy times into film.py.
