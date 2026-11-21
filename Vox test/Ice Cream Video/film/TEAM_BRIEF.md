# Team brief: "If The Ice Cream Truck Plays Its Song In Winter... DON'T GO OUTSIDE" (Night Policy)

Read this whole file first. The script and the story bible are the authority on story and design.

## The job
- Channel: Night Policy. Rule-format horror told by one English narrator. Flat-vector 2D animation rendered in Python with skia on our own engine, 2560x1440, 60 fps.
- Folder: `Vox test/Ice Cream Video/film` (F). Work files go in `F/_work` (W; gitignored).
- Starting point: the finished code of our last film (the school bus film), copied here:
  - engine/, render.py, film.py (still the bus shot list; it becomes this film's);
  - characters.py + characters_bus.py (and older casts), sets.py + sets_bus.py (and older sets);
  - film_*_ref.py references;
  - audio/, tools/, analysis/;
  - ARCHITECTURE.md, CAST.md, SETS.md, README.md (all still about the bus film).
- Write this film's cast in `characters_ice.py` and its sets in `sets_ice.py`, run by characters.py / sets.py the way the bus modules are.
- Code still pointing at the bus film must be fixed whenever you touch it. That includes audio/sfx_plan.py, music_plan.py, mix_scenes.py and mix.py's per-line tables, which are keyed to the LAST film's lines and sounds: rewrite them for this film, never reuse them blind.
- Script: `Vox test/Ice Cream Video/script/narration_en.txt` (2,099 words; read it in full).
- Story bible: `Vox test/Ice Cream Video/script/story_bible.md`. It covers the villain spec (both forms and the transformation), his truck, the cast, sets, the rules, twist seeds, the chime and the timing table.
- Owner's references (mood and archetype only): `Vox test/Ice Cream Video/ref/owner_mood_normal.jpg` and `owner_mood_monster.jpg`.
- Voiceover: `W/narration/raw/part1.wav`, ONE file, 13:06, 24 kHz mono TTS. The recording is the truth for the words.
- Sounds: `W/samples/epidemic_ice/` holds the owner's NEW pack for this film (54 effects, 14 music tracks). The earlier packs are linked beside it, read only: epidemic_bus, epidemic_doctor, epidemic_bunny, epidemic_dummy, epidemic_delivery, epidemic_police, epidemic_mirror.

## The villain: MISTER SHIVER (original character)
- The owner's references are fan art of the ice cream man from the game "Ice Scream". We do NOT copy that character, game or story. The story bible has the full table of what is ours and the hard limits: no "Rod", no "Ice Scream" or any pun on it, no freeze ray, no factory, no frozen or captive kids, no truck interior beyond the window, no cone on the roof (ours is a frosted SNOWFLAKE), no existing jingle.
- Hit the owner's FEELING as strongly as we can.
- **Normal form:** a bald, chalk-white, too-friendly ice cream man, tiny bright blue eyes, a too-wide smile with buck teeth, a pink-and-white striped vendor uniform. He breathes NO cloud in the cold.
- **Monster form:**
  - the smile stretches past the face into a long white bone-like mask with frost cracks;
  - the eyes sink and come back red;
  - the jaw drops to the chest: no throat, just dark and icicle teeth;
  - long brown jointed spider legs burst out of the uniform, with frost on the joints and needle tips that leave holes in the snow;
  - he pours out of his window head first, scuttles over fences, cars and roofs, crawls in the attic, drops from the hatch.
- The full transformation plays once on screen, step by step; three short glimpses come before it.
- He must feel ACTIVE and dangerous in every beat: the owner's main complaint about an older film was a passive villain.
- His mouth never lip-syncs.

## Message and values (the owner's request)
- The owner is a Muslim creator. Every video should carry love, peace, respect and kindness and be genuinely helpful, without preaching.
- **This film teaches:**
  - the signs of dangerous cold: stopped shivering, sleepy, confused, "feels warm" means call for help; get them in and dry, wrap the middle, stay close;
  - frostbite: don't rub;
  - never heat with an oven or grill indoors;
  - lures ("free treat", "your dad said it's okay", "just come to the window"): never, tell a grown-up;
  - with a grown-up, knock on the door of someone who lives alone.
- Kindness through the twist: everybody inside means somebody alone. Old Mr. Kessler cleared everyone's walks for years and nobody checked on him.
- Kid-safe: creepy and tense; no blood, gore, injury close-ups, romance or profanity. Taking a person is never shown.
- Cold night and monster scenes are icy blue and sickly pink. Home after the rescue, the morning and the outro are warm and safe.
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
   - In every beat with Mister Shiver, he moves, closes distance, reaches, grabs or invades.
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
   - This film's is HIS TRUCK'S CHIME: an ORIGINAL sweet, too-slow, slightly out-of-tune music-box melody that we compose, which always ends on a GAP where the last note should be (see the story bible's chime table). It warps as the night gets worse, and at the climax it hangs on the missing note and falls apart.

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
- Work only inside `Vox test/Ice Cream Video`. Never modify other film folders; reading them is fine.
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


## Lessons from the school bus film: avoid these from the first pass
- Captions showed literal markdown asterisks (`**...**`). Caption text must come out clean: no `*`, `_` or brackets anywhere.
- Close-ups of the tall villain filled the frame with his hat and cut his face off. Frame on the FACE (eyes about a third from the top).
- Rule cards had a bar covering part of the rule text. Every rule's full text must be legible while it is read.
- Night shots were too dark to read the action. Light the subject (truck window glow, phone light, frost-blue moonlight, the plow's orange beacon), not the whole frame.
- The camera code capped planned pushes at 1.8x, so wide shots kept people tiny. That is fixed (max 4x): use it.
- Scares covered their own words. Leave short scare beats in the voice edit so a hit lands just after its word.
- Two agents once edited the same voice files at the same time. Each teammate owns only the files its job names.
