# Team brief: "If Your Mom's Eyes Turn Into Buttons... DON'T KEEP HER SECRET" (Night Policy)

Read this whole file first.

## The job
- Night Policy, rule-format animated horror. Flat-vector 2D animation rendered in Python with skia on our own engine, 2560x1440 at 60 fps.
- Folder: `Vox test/Buttons Video/film` (F). Work files go in `F/_work` (W), which is gitignored.
- The code is a copy of our last film (Walls): engine/, render.py, characters*.py, sets*.py, audio/, tools/.
  - `film.py` is still the Walls shot list (it becomes this film's); `film_walls_ref.py` is a copy kept for reference.
  - ARCHITECTURE.md, CAST.md, SETS.md and README.md still describe the Walls film; update the parts you touch.
  - Paths, names and titles that still point at the Walls film must be fixed whenever you touch that code.
- Script, the authority on words: `F/../script/narration_en.txt` (2,248 words; read it in full).
- Story bible, the authority on designs, rules, twists and limits: `F/../script/story_bible.md` (read it in full: the Blank's forms and four limits, the design notes, the kid-safe limits, the sets, the motif, the twist and rule tables, the outro checklist).
- The same text split per voice: `F/../script/voices/*.txt`; `voices/index.json` "order" is the exact interleaving of every narrator paragraph and character line, in script order, with who speaks. `script/tools/split_voices.py` made them.
  - Removed from the narrator on purpose: the "Tik." and "Ping." beats (they are SOUNDS, placed by the sound team) and the quoted character lines (they are in each character's own take). On-screen capitals were written out for speech ("FRI." read as "Friday"; the fridge-board messages in normal case). The picture still shows the capitals.
- Voice takes: `W/narration/raw/` (48 kHz mono), `index.json` says which file is which. `W/narration/asr/*.json` holds a first Parakeet transcript of every take (word times).
  - Narrator in 7 parts, in order. One take each for Mom (13 lines, two sung), the Blank (20 lines, generated with MOM's voice on purpose), Mr. Dunn (2), Officer Mensah (1; there is also an mp3 copy of the same line).
  - Owen (11) and his son (10) come in ONE adult take (`kids_adult_take`, read with the narrator's voice): Owen's 6 lines first, then the son's 2. ElevenLabs will not design child voices, so we make them ourselves with the WORLD revoice (`tools/vo_voices.py`, which made Theo and Sam in the Walls film). Owen and his son must sound like two different boys.
- No dialogue tags exist in this script ("Mom said" etc.); the owner forbids them. Every character speaks in their own voice, so the picture must show who is talking.
- Owner's mood stills (W/ref/owner_mood_mom_*.jpg) are from a famous film: MOOD ONLY (the idea of three forms of a mother). Do not copy any design from them; the story bible's design notes say what ours look like (warm-brown bun with a pencil, freckles, oatmeal cardigan, reading glasses; no black bob, no red lipstick, no mole, no needle fingers, no spider poses).
- The owner's lessons, rules and work-lean habits from earlier films apply in full. Read these sections:
  - `F/ICE_TEAM_BRIEF_ref.md`: "The owner's feedback" (Picture 1-6, Sound 7-9; Sound 9 here means OUR motif, below), "Lessons from our earlier reviews", "Rules", "Work lean", "Lessons from the school bus film".
  - `F/WALLS_TEAM_BRIEF_ref.md`: "Lessons from the Ice Cream film", "Owner, 23 Nov: no dialogue tags", "Owner, 23 Nov: sound effects must never pop in, stop dead, or be too loud", "Owner, 23 Nov: nothing sinks into the floor, floats, or passes through anything". These are hard rules here too.

## Story in short (the script is the authority)
Owen, 11, lives with his mom Nadia in a small apartment (lobby with a glass door, his window over a streetlight and a bus stop, Barlow's shop on the corner). She works twelve-hour help-line shifts at the kitchen table in a headset; strangers get "I'm listening", he gets one finger. He types "I wish I had a different mom" in a game chat; a grey default avatar answers and fills itself in with everything he tells it, then two black buttons click on where the eyes go. He names her the Blank. Seven rules Mom and he wrote inside his closet door when he was eight (the Brave List: her words in blue pen, his crayon border) fade one by one as he breaks them; each secret he keeps for the Blank rubs him out of his family's sight (and greys his family in his own). By midnight on his birthday (Friday) his mom is reporting him missing to Officer Mensah while he stands in the kitchen beside her. He says no, gets away, tells (on the fridge board when she can't hear him), she looks at him, he names her eye colour ("Green."), and the Blank collapses into an empty cardigan. 25 years later he is the headset parent; the button jar is empty; his son's tablet shows the grey head; he puts the headset down and looks.

## The mother and her copy: the three forms (story bible, "The mother: the Blank")
- Form 0, the chat avatar: the grey default profile head (UI), filling in detail by detail; two black four-hole buttons click on last. Also the sting.
- Form 1, "normal": the real mom's exact look; the Blank fakes it only with glass over the eyes (sunglasses in the car R3, Mom's reading glasses at 2 a.m. R4). Tell: cardigan buttoned to the throat (the real mom wears hers open).
- Form 2, button-eyed and sweet: Mom made too neat (glossy perfect bun, too-smooth grey-tinged skin, cardigan buttoned to the throat with shiny black buttons), flat shiny black four-hole button eyes with a white glint, never blinks, smile a little too big, one frame of the grey default head on a fast turn, a little taller each time we see her.
- Form 3, creepy: ceiling height, very thin, neck bending along the ceiling, the cardigan stretched into a long tube with a longer row of buttons, long fingers with flat rounded button-disc fingertips (no points, no claws), a far too wide smile, joints bending the wrong way SLOWLY (never scuttling). Collapses into a flat empty cardigan.
- The real mom (Nadia): warm, tired, loving; messy warm-brown bun with a pencil, freckles, open oatmeal cardigan with pens in the pockets, reading glasses (glare hides her green eyes until the climax), headset, slippers.
- Her limits drive staging: she is blind (tilts her head toward sounds, waves at the wrong window); she moves only while nobody who loves him is looking at him (microwave-door beat: Mom looks up, the Blank is gone; Mom looks down, the Blank is closer); she cannot take him (the top button is his to close; he refuses).

## Picture devices this film needs (designs in the story bible)
- The rule card is the Brave List inside Owen's closet door: rule n in Mom's blue pen inside his crayon border, each word appearing as it is read. Broken rules fade to pale (only the crayon border stays); after R5 only rule three is blue. In R7 the ink comes back line by line as he writes on the fridge board.
- Owen fading: as secrets pile up he becomes faint to the others (Mom looks straight through him), and by R6 he is gone from the microwave-door reflection. The VIEWER must still read him clearly (keep him on screen with a cool, slightly translucent look), never a missing character. "Like a photo developing" when he tells: he comes back.
- The headset lady going pencil grey (desaturated) in Owen's sight from R5 to R6; colour returns when he says "Mom" again.
- Mom's glasses catching the laptop as two black circles (R5): for one second the real mom has button eyes.
- The chat UI (grey default head, bubbles, typing dots), the tablet, the fridge whiteboard ("FRI. O'S BIRTHDAY"; "MOM IT'S OWEN I'M HERE"; the list of everything), the button jar on the windowsill, the red coat with seven black buttons, the music box.
- Kid-safe limits (hard): no needles, no sewing, no thread, nothing ever near anyone's eyes, no injuries, no blood; the coat wraps loosely, the top button is never closed, her fingers never touch his skin (they stop an inch away), nobody dies.
- Physical rules for the hard beats: the car arm comes out through the OPEN car window; the creepy form unfolds from the gap BESIDE the fridge, never through it; Owen drops down and slips out the bottom of the loosely held coat while she keeps holding it; her head bends along the ceiling (contact, not through it).

## Our returning motif (Sound 9): the Button Song
- "One for warm and two for snug, three for Mama's button hug. Top one up and tucked in tight. Mama sees you. Say goodnight." Our original four-bar music-box waltz.
- Mom sings it in her take. Derive the tune FROM her sung take (measure its notes) so the music box, the hums and her singing agree; then it returns: clean music box in the chat, too slow and winding down in the closet at 3 a.m., hummed slowed through the car window, sung perfectly again and again at the windowsill, detuned at the climax (stopping with one button left), four notes from the empty cardigan (the real music box), and the son's tablet chime (the first four notes).
- "Tik": one button dropping into a glass jar. Introduced at Mom's jar, then every time the Blank closes distance, as his fingers rise to the top button, two tiks as the buttons drop into the jar at the end. Never metallic. The "Tik." and "Ping." beats removed from the narrator are where these sounds go (see the script text).

## Benefit: the real lesson is woven through every rule (keep it exact on screen)
- The outro checklist (story bible, "Outro checklist") must be legible while it is read, all six items.
- Values: creepy and tense, never gory; Mr. Dunn, Officer Mensah and Mom are kind, effective helpers; the real mom stays loving and respected; the owner is a Muslim creator: love, peace, respect, kindness, never preachy.

## Budget (HARD)
- The film has 2.5M output tokens; script and voices used about 0.65M, so about 1.85M are left for everything. The owner stops everything at 100%.
- Each teammate gets a share in its task brief. Stay well under it: no exploratory sheets, no repeated full renders, small patches, short reports (under 300 words). Read code with grep and sed -n ranges.
- Disk: only about 0.6 GB is free. Test renders as stills or short low-res clips only; delete intermediates at once; never copy samples (they are symlinks in `W/samples`). At most 2 CPU-heavy processes per teammate when others share the machine.
