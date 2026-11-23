# Team brief: "If Your Little Brother Says Someone Lives In The Walls... DON'T LAUGH" (Night Policy)

Read this whole file first.

## The job
- Channel and format:
  - Night Policy, rule-format horror.
  - Flat-vector 2D animation rendered in Python with skia on our own engine, 2560x1440 at 60 fps.
- Folder: `Vox test/Walls Video/film` (F).
  - Work files go in `F/_work` (W), which is gitignored.
  - The code is a copy of our last film (Ice Cream): engine/, render.py, characters*.py, sets*.py, audio/, tools/.
  - `film.py` is still the Ice Cream shot list (it becomes this film's); `film_ice_ref.py` is a copy kept for reference.
  - ARCHITECTURE.md, CAST.md, SETS.md and README.md still describe the Ice Cream film; update the parts you touch.
  - Paths and names that still point at the Ice Cream film must be fixed whenever you touch that code.
- Script, the authority on words:
  - Full script: `Vox test/Walls Video/script/narration_en.txt` (2,138 words; read it in full).
  - The same text split per voice: `script/voices/*.txt`.
  - Each voice was generated separately in ElevenLabs.
- Voice takes:
  - The recordings are in `W/narration/raw/` (48 kHz mono); `index.json` says which file is which voice.
  - There are 6 narrator parts, in order, and one take each for Dad, Mom, Mrs. Dabrowski, Mr. Pell, the 911 dispatcher and Officer Reyes.
  - Theo and Sam come in ONE adult take (`theo_and_sam_adult_take`: Theo 0 to 17.49 s, Sam after that). ElevenLabs will not design child voices, so we make them ourselves.
  - A first test of the child voices is in `W/narration/kids/`:
    - Theo, 6: F0 285 Hz, formant warp x1.38.
    - Sam, 12: F0 232 Hz, x1.245.
    - Both use the WORLD revoice in `tools/vo_voices.py`.
    - Recognition was word-perfect except "face", which was heard as "verse".
- Owner's mood references for the villain: `W/ref/owner_mood_hound_*.jpg/.webp`.
- The owner's lessons, rules and work-lean habits from the last film apply in full. Read these sections of `F/ICE_TEAM_BRIEF_ref.md`:
  - "The owner's feedback" (Picture 1-6 and Sound 7-9; Sound 9 here means OUR motif, below);
  - "Lessons from our earlier reviews";
  - "Rules";
  - "Work lean";
  - "Lessons from the school bus film".

## Story in short (the script is the authority)
- The family:
  - Sam is 12 and is the narrator as a boy; the grown-up Sam narrates and is never drawn.
  - His brother Theo is 6.
  - Mom and Dad.
- They move into 14 Larkspur Lane, Maple Falls, in an August heat wave.
- The old owner, Mr. Pell, "just walked away". He left:
  - his green armchair;
  - a stone frog with a key under it;
  - his old garage keypad code;
  - a note that explains every noise away.
- Theo says "Hushabye" lives in the wall and has a sad dog face. Dad's old rubber Halloween hound mask was taped into a box marked GONE FOREVER in the garage.
- Theo's seven rules: Sam writes them down in Theo's dinosaur notebook, and the seventh line stays blank.
- The signs:
  - a deadbolt turns by itself;
  - the bread bag is twisted shut again;
  - an eye watches through a crack in the pantry plaster;
  - the armchair is warm in August;
  - Theo's drawings are hidden under the cushion;
  - the hall switch "that does nothing" lights a sealed attic and a voice says "Off.";
  - a man's voice sings Theo's address song inside the wall and repeats the note's excuses.
- The climax:
  - At 3 a.m., "Dad" in the doorway (Pell, in Dad's red flannel shirt and the hound mask) tucks Theo in, hushes Sam, and goes back through the closet wall.
  - Sam does NOT follow him. He carries Theo to his parents' room, locks the door and wakes Dad.
  - Mom calls 911. Theo sings the address to the dispatcher.
  - The family stays locked in while the man scratches through the walls and sings through the floor vent. Then the police come.
- The ending:
  - Pell is found in the dead space between the closets.
  - Unmasked, he is a tired old man. He grew up in Sam's room.
  - The doorframe has pencil marks: L age 4, 8, 12, and a fresh one dated last week.
  - Rule seven was "Believe me."

## The villain: MR. PELL, "HUSHABYE" (original character; a real man, no supernatural)
- Body:
  - A tall, thin man in his late sixties, slightly stooped.
  - Long pale hands with plaster dust on the fingertips.
  - Moves silently in socks and folds himself into narrow spaces.
- Clothes:
  - Dad's red-and-black buffalo-check flannel shirt, loose on him.
  - Grey work trousers and grey socks.
- The mask: Dad's old rubber Halloween hound mask.
  - Long droopy ears that swing a beat late.
  - Heavy, sad, half-closed eyes and a wet black rubber nose.
  - The mouth opening shows his own human teeth.
  - It is a cheap rubber mask, not a real dog head: a visible neck edge, a tape repair on one ear.
- Unmasked: grey stubble, blinking, tired and lonely.
- At night, in the doorway, his silhouette must read as Dad at first glance, with the same head tilt each time.
- Hit the FEELING of the owner's references (a sad hound face on a man in red flannel, "it lives inside the walls") with our own design. Copy no existing character.
- He must be ACTIVE and scary in every beat. He:
  - watches through cracks and vents;
  - crawls fast inside the walls;
  - turns the deadbolt;
  - eats, tucks Theo in, kneels, tilts his head, lifts a finger to his lips;
  - slides the closet's back wall;
  - scratches around the bedroom behind the furniture;
  - sings through the floor vent.
- The kid-safe line: he never hurts anyone. Menace comes from closeness, watching and touching things, never from violence.

## Our returning motif (Sound 9)
- Theo's address song, "Fourteen Larkspur Lane. Maple Falls. That's my house. That's my name.", is our original little tune:
  - a sweet child's melody;
  - it returns warped, slow and low, when Pell sings it inside the walls;
  - it ends on the "hush-a-bye" lullaby.
- Compose it ourselves. It must stay recognisable.

## Cast (7 drawn) and sets (about 8)
- Cast:
  - Sam, 12;
  - Theo, 6 (dinosaur pyjamas);
  - Mom;
  - Dad;
  - Mr. Pell (masked and unmasked);
  - Mrs. Dabrowski (the neighbour, late sixties, with a pie);
  - Officer Reyes, plus generic officers.
- Sets:
  - The house exterior: porch with the stone frog, the garage keypad, the street, Mrs. Dabrowski's house across, the August night.
  - The kitchen: the counter with the note, the pantry with the plaster crack, the door from the garage with its deadbolt.
  - The living room: Mr. Pell's green armchair, the floor vent, fans in the windows.
  - The upstairs hall: the dead switch, the hall closet with the attic hatch, the line of light.
  - The boys' bedroom: two beds, the closet whose back wall slides, the doorway, the doorframe pencil marks, the wall by Sam's bed.
  - The parents' bedroom: lockable door, dresser, headboard, floor vent, phone.
  - The dead space between the closets: about a foot and a half wide, with a sleeping bag, Dad's flashlight, folded bread bags and the empty GONE FOREVER box.
  - The night street with the police cars and the curb.
- Inserts:
  - the note;
  - the notebook page with the rules (rule 7 a blank line);
  - the frog and key; the keypad;
  - the deadbolt turning;
  - the bread bag;
  - the drawings;
  - the switch;
  - the vent grille;
  - the phone at 911;
  - the pencil marks.

## Benefit: the real lesson is woven through every rule (keep it exact on screen)
- The outro checklist must be legible while it is read:
  - lock every door and window every night, including the garage door and the basement;
  - when you move in, change the locks and codes, and leave no key under the frog;
  - food gone, things moved, doors unlocked, lights you didn't touch: tell your family and check together in daylight;
  - if someone may be inside, don't look for him: get out, or lock yourself in a room with a phone, and call 911;
  - know your address;
  - grown-ups: listen to kids, then check.
- Kid-safe and values:
  - Creepy and tense: no blood, no gore, no weapons, no injury.
  - Police and the dispatcher are calm, kind and competent.
  - The owner is a Muslim creator: love, peace, respect, kindness, never preachy.

## Lessons from the Ice Cream film (one-frame glitches cost a whole extra render round)
- A shot rendered across two processes can jump in texture at the split, because `tex()` seeds per process. Use the shot param `tex_seed=True` on static textured shots.
- Check full-size frames, not only previews: some defects only show at 2560 px.
- Scan for one-frame pops (tools in `analysis/`) before calling any stage done.

## Budget (HARD, the owner was upset we overspent last time)
- The whole film has 2.5M output tokens and about 2.0M are left.
- Each teammate gets a share in its task brief. Stay well under it:
  - no exploratory sheets;
  - no repeated full renders;
  - small patches;
  - short reports (under 300 words).
- Disk: only about 0.75 GB is free.
  - Test renders as stills or short low-res clips only.
  - Delete intermediates at once.
  - Never copy samples; they are symlinks in `W/samples`.

## Owner, 23 Nov: no dialogue tags
- The narrator's "Dad said.", "I said.", "Mom said." and similar tags are cut from the voice track, the line map and the captions.
  - The full list of 17 is in `W/narration/drop_tags.json`.
  - Every character speaks in their own voice, so the picture shows who is talking.
- Keep "Dad read it out loud, and laughed." and "'Night, Dad,' I almost said."

## Owner, 23 Nov: sound effects must never pop in, stop dead, or be too loud (it happened in the Ice Cream film and earlier)
- No sound may start or stop in the middle of itself.
  - Every effect fades in if it is cut into, and lets its tail die away (or fades out over up to 350 ms) if it is cut off while still ringing.
  - `audio/sfx.py` now does this for every event: `fade()` adapts, and `render_event()` applies it at the end.
  - Use `hard_end=True` only for a deliberate dead stop, and only where the film needs one.
  - The same holds where the mix trims or ducks: beds trimmed to a shot, window edges, ducking ramps, a sound cut at a picture cut.
- No effect may jump out of the mix.
  - Everyday foley (doors, steps, bags, switches) sits under the voice.
  - Only the few planned scare hits rise above it (+6 to +10 LU momentary), and they have a smooth release.
- Before calling the mix done, measure every event in the effects stem:
  - its first and last 10 ms against its own peak (no loud edge);
  - its momentary loudness against the voice at the same time;
  - list and fix every outlier.

## Owner, 23 Nov: nothing sinks into the floor, floats, or passes through anything (seen in almost every film so far)
- Problems seen:
  - characters, props and cars sank into floors or roads;
  - objects stood inside each other.
- Tiny ones nobody notices are tolerated. The obvious ones were not, and they are now a hard rule.
- Every figure, prop and vehicle stands on its surface:
  - feet on the floor, wheels on the road, a cup on the table;
  - seated figures on the seat;
  - lying figures on the bed or floor.
- Nothing passes through anything: furniture, walls, door frames, beds, cars, other people.
- Place everyone on the set's own anchors and ground lines, never on loose coordinates.
- `tools/validate.py` already checks floors, levels, furniture footprints and body overlap, but only in sets with a floor plan. The film teammate extends it to EVERY shot type, sampled at 8 fps:
  - flat sets and close shots get the set's ground line at that x, for feet, wheels and prop bases (tolerance a few design px);
  - figure-against-furniture and vehicle rectangles;
  - a held prop that is not in its hand.
- Every ERROR is fixed before a preview goes to review.
- The review round also looks specifically for this on full-size wide shots and on 4 fps strips of every action shot.
