# "If The Bunnyman Asks You To Close Your Eyes... DON'T COUNT TO SEVEN": film

This film is made the way the police film (`film_police_ref.py`) and the dummy film (`film_dummy_ref.py`) were: the same 2.5D engine, the cast and set systems, the shot-list format, the police header, rule cards and captions, the global look with a red climax ramp, and cue sheets derived from the picture. The picture follows a shot map written before the shot list: `W/shotmap.md` (every line of the timeline -> the picture that carries it: shot kind, subject, action, framing, props, where the cut lands; then the continuity of the props).

All commands run from this folder (`Vox test/Bunnyman Video/film`). The work dir is `W = film/_work`.

| file | what |
|---|---|
| `film.py` | The shot list (`plan_film()` in 15 sections, below), the builders `B_set`, `B_bust`, `B_ins`, `B_rule`, `B_pause`, `B_card`, `B_black`, the plan helpers (`P()` people on spots or plan points, `cm()` a camera anywhere on the house's floor plan, `STEP(k)` a stair tread, `bust_place` / `bust_eyes`, `hand_layer` hands and the Bunnyman's paws in close-ups), captions / header overlay, `escalate()`, the global look, cue sheets, and the checks (`--sheet`, `--frames`, `--lipcheck`, `--bench`). The module docstring lists the shot kinds and every plan key. |
| `film_police_ref.py`, `film_dummy_ref.py` | The police and dummy shot lists, kept as the format reference. |
| `characters.py` + `characters_bunny.py` / `CAST.md` | The cast (the Bunnyman clean 1987 / filthy now / unmasked Dale, Mom, the narrator and the old body, June, Laurie at 7, Grandma, Dad, the cop, the doctor) and the acting (look_at, reach_to with contact points, PropTracks, give, hold_hand, hand_over, kneel, lie, walk / run on plan paths). |
| `sets.py` + `sets_bunny.py` / `SETS.md` | The house on Orchard Road on one floor plan (hall + stairs, living room, kitchen, upstairs corridor, June's room, the bathroom, the attic), the yard and the treeline, the front porch, Holloway Woods and the railroad bridge, the 1987 parade on tape, Holloway State Hospital, the inserts, the rule card. |
| `render.py` | Stills, test clips and the full worker/slice render (defaults to `W`). |
| `tools/final_chain.sh`, `tools/encode_chain.sh` (+ `enc_seg.sh`), `tools/deliver.sh` | The final render in chunks + the HEVC deliverable `W/deliver/If_The_Bunnyman_Asks_You_To_Close_Your_Eyes_EN_1440p60_HEVC.mp4` (title metadata "If The Bunnyman Asks You To Close Your Eyes... DON'T COUNT TO SEVEN"). |
| `engine/` | The 2.5D engine (camera, layers, lenses, grades, HUD, the VHS post). |
| `audio/` | The sound step. It reads `W/cues/*.json`. |

## Inputs
- `W/align/timeline.json` (412 lines, `duration_en` 1076.08 s since fix round 1, fixer D), `W/align/asr_cache.json` (word times), `W/align/vo_en.wav` (the edited voiceover, 48 kHz). Written by `tools/align.py` from `W/narration/narration_en.wav` (see Narration below).
- Script: `../script/lines.py` and `../script/narration_en.txt`.

## Narration (the voiceover edit)
The owner's raw TTS take (`W/narration/raw/narration_raw_24k.wav`, 970.8 s, two parts joined) is edited, never re-voiced for the narrator:
- `tools/vo_asr.py <wav> <json>`: Parakeet words with start and end times (+ a rescue pass for the short words the VAD skips) -> `W/narration/asr_raw.json`.
- `tools/vo_edit.py analyze | pacing [--force] | build | check`: maps every line of `script/lines.py` onto the take's sound islands, drops breaths / clicks / lip thumps / the TTS's noises, repairs the TTS slips (FIXES: "eleven seven", "Ye knocks", "Yah. I I", "c-corner", "c-cup", "See leave well", the part seam), re-paces every line boundary from `W/narration/pacing_map.md` (the source of truth: edit a gap there and rebuild), levels each line (one gain per line), 70 Hz high-pass, a light de-esser, 48 kHz 24-bit -> `narration_clean.wav`; then `tools/vo_voices.py` re-voices the quoted words of Mom, June, the girl in the Bunnyman, Grandma, the dying man and the old body (WORLD pitch / formant / breath) -> `narration_en.wav`. Every source span and gap: `edit_list.json`.
- `tools/vo_check.py` (or `vo_edit.py check`): before / after strips and scans (`W/narration/tests/`); `tools/vo_report.py` -> `W/narration/voice_report.md`.
- Then `python3 tools/align.py --write-pauses` (rewrites the pause / pace of every row of `script/lines.py`). With silence between all lines, align.py places every boundary in the silence (to the millisecond) and places a line the recogniser cannot hear (June's "Yeah.") on the sound between its neighbours.
- Order after any change: `vo_edit.py build`, `rm -rf _work/align && align.py --write-pauses`, `vo_edit.py check` (now also every line against the recogniser: it fails the check on a cut word), `vo_report.py` (about 7 min on 2 cores). A narration change moves the timeline: the picture follows its lines, and film.py's absolute-time tables follow through `timeline_authored.json`.
- **The channel is NIGHT POLICY** (renamed by the owner after the take was recorded): the take says "Next time on" + the old channel name; FIXES `next` cuts "on" and the old name (956.576-958.201 in the raw take: "time" keeps its whole m murmur on a 25 ms fade, the breath before "If" goes too) and "if your doctor calls..." follows after 0.45 s, the edit's shortest ellipsis. `script/lines.py` and `script/narration_en.txt` read "Next time... if your doctor calls...". The edit is 1.175 s shorter (1077.99 s); every line after 409 moved, nothing before it. Parakeet hears the repaired line word for word.
- **Fix round 1 (fixer D): no word is cut in half any more.** Critic 3 heard eleven line boundaries where the edit glued the next line's first 30-150 ms to the line before ("egg | In-side", "off | In-side", "door | A-t", "days | O-kay", "woods | T-wo", "face | I-n", "Seven" split in its v, "wood | pile", "She's | humming", "too | I-f", "things | Th-is" ...). Two causes in `line_spans`, both fixed: (1) the "word cut by a closure" extension let a line's last word claim the next island because the recogniser's END time runs on into the next word; now it never claims an island where the next line's first word starts (recognised start within 0.15 s of the island), and an island that is the next word's onset is not taken as a coda either (pass 1, when it sits nearer the next line's sound); (2) two lines in one sound island were split at the quietest point after the previous word's START (inside the word); `split_point` now anchors on the next line's first word and takes the LAST real dip (the lowest point within 25 ms, 20 dB under the island's p90) before it, and `SPLITS` hand-sets the four the TTS ran together with no dip (humming 445.285, hatchet 560.780, seven 816.620, liked_you 938.620: read on 2 ms spectrograms with the pitch and formant tracks). A line-final piece under 60 ms after a pause is dropped unless the line ends in a stop (one 19 ms tick, after "nothing."). "And count to seven." ends at the decay of its n (694.845, 25 ms fade: the stray vowel after it read "seven eyes"); the second "Thunk." reuses the first take (`FIXES['thunk2'] = {'reuse': 'thunk'}`: it read "Sunk"). The edit is 1.91 s shorter (1076.08 s); 38 line boundaries moved by 30-430 ms. film.py's absolute-time tables follow through `timeline_authored.json` (below).
- **Every line against the recogniser** (`tools/vo_asrcheck.py`, run by `vo_edit.py check` once align.py has run on the build): a word goes to the line whose sound holds its start (a word starting in a gap goes to the next line when that starts within 0.35 s: Parakeet places the first word after a silence early), a line fails on a wrong first / last word, under 80 % read, nothing heard, or a word split across a boundary; a flagged line is then recognised again on its own, and passes if it reads there (the whole-file pass depends on the VAD's chunks). Now: 412 lines, 3 flagged in the whole-file pass (the chanted "Hop, hop, hop along.", the knock count "Seven.", "A crayon drawing."), all three read word for word on their own, 0 failures. Before: 11 failures.
- **The voices** (`tools/vo_voices.py`): the real Laurie in the suit has a child's formants now (x1.24, was x1.02: a man's falsetto to the ear and the measure; June is x1.30), the man an octave down 16 dB under her (-18 whispering, -15 screaming, x1.22); at x1.25 and up a recogniser hears her "Please." as "Prees". June's "Yeah." has its own variant (x1.22, `J_yeah`): it reads on its own; the whole-file pass still skips the short word (align.py places it on its sound).

## The shot list
```
python3 film.py --list                    # every shot (index, start, length, kind) + count / median / p10 / p90
python3 film.py --cues                    # cue sheets -> W/cues/sfx_cues.json, music_cues.json, shots.json
python3 film.py --sheet W/tests/film/sheet --range 0 120 --per 8          # review sheets: first | mid | last frame + the lines
python3 film.py --frames W/tests/film/cuts/cut --threads 1    # every cut: last frame | first frame over magenta (+ cut_holes.json)
python3 film.py --lipcheck                # mouths move only on their own lines -> W/tests/film/lipcheck.json
python3 film.py --still 290.5,316,345.5   # 960x540 stills -> W/tests/film/still_T.jpg
python3 film.py --bench 40 --consec 6 --size 2560x1440 --threads 1          # full-size speed, one process (consecutive frames)
python3 film.py --bench 1 --consec 10 --shots 0,10,57 --size 2560x1440 --threads 1   # chosen shots
```
(`W` stands for `_work`.) Each command builds the film once (about 5 s) and runs at 960x540 unless `--size` says otherwise. Review sheets are 960x540 frames in 320 px tiles, 8 shots a sheet, each row `#index kind start-end (length)` with the timeline lines it covers printed under it.

- **397 shots** (after fix round 1, fixer C), median 2.43 s (p10 1.27, p90 4.56; longest 10.1 s: the rule cards, the next-episode card and the end card), 21.9 cuts/min (the police film runs 23.4).
- **The film is 1085.93 s** (65,156 frames at 60 fps; 1087.84 s before fix round 1 re-split the narration): the narration (1076.08 s) + 9.85 s for the outro. The sound step's outro jingle starts 0.1 s after the last line ends and runs 9.75 s ("...that's just the outro." and the song IS the outro, `audio/music_plan.py`), so the NIGHT POLICY end card holds for it and the film fades out with its last soft hum.
- **Story layout** (`plan_film`): `plan_open` (0-65.7 s: the cold open, the 1987 parade on tape, the Courier, Laurie walking out of the woods, the hospital, the house and the rules on the fridge), `plan_1987` (the float, the photo with Laurie holding his paw, the magic trick, the woods, the bridge, sunrise 1987, the missing poster), `plan_since` (every Easter since: the treeline, the burn barrel, Grandma's porch light, Dad and his flashlight, the police morning), `plan_rule1` (11:07, the song, the curtains, June at her window, the wave, "Past us.", Mom in the doorway), `plan_pause` (the comment prompt), `plan_rule2` .. `plan_rule7` (midnight's egg, 1:13's knock, 1:40's mail slot, 2:47's attic, 4:30's break-in and the bathroom, 6:12's sunrise and the body), `plan_reveal` (the trick, 1987 and now, the recalls of every rule, the swap), `plan_after` (Mom's body, the police, Holloway State Hospital, the visit, "Want to see a magic trick?"), `plan_outro`, `plan_globals` (the jingle by version, the count, the swap, the climax pulse and heartbeat, the beds the reveal needs).
- **How it is staged** (the owner's notes on the last films):
  - *Cuts, not long camera moves.* Every move is a short push (1.5-3.5 %/s) or a keyed zoom on a subject that is acting; no fly-throughs. Mediums and two-shots are real cameras placed on the same floor plan (`cm(eye, look)`), so walls, doors, furniture and people stay where they are between cuts.
  - *The picture shows what the line says.* Each line's picture is in `W/shotmap.md`: the knock count tags 1..7 landing on the door as the knocks land, "Mom closes the mail slot" (her fingertips push the flap shut) and "She smooths June's hair" (her hand on it), Mom tucking June in (her hands on the quilt, June asleep on the pillow), the egg rattling on the doormat, the ring rolling in the bottom half of the egg, the light under the bathroom door turning gold, the lock turning by itself and the key, "His lips move one last time. Mama." (Dale's own lips), the crayon drawing sliding in under the door, the switch flipping on "You can turn a light on now", Holloway and Pemberton's struck through in red marker, the zipper pull sliding down.
  - *Hands touch what they hold.* `reach_to` lands a palm / fingertips / grip on a point that moves with the target, props are `PropTrack`s (held, resting, gone: nothing pops or doubles), `give` passes the ring from hand to hand, `hand_over` lays a hand over eyes or a mouth, `hold_hand` joins hands (the old body and June). People face what they act on (`face=` a plan point), walkers' feet step on the floor (walk clips with footstep cues), kneeling and lying come from the spot or `kind`.
  - *No "scared jiggle" filler.* `escalate()` gives the kids wide eyes, brows and breath as the night goes on, Mom locked eyes; nobody trembles on a line that does not say so.
  - *Close-ups* (`B_bust`) are the same set behind the face (`bg=(room, view, cam)`), blurred and dimmed; set pieces whose draw order would put them in front of the face are left out of a close-up's background (review fix: the filter used the projected depth, which dropped the walls of small rooms and showed the outdoors behind June at the mail slot and in the attic).
- **The Bunnyman**: one suit in two states, `bunny87` (clean, 1987) and `bunny` (now: matted, one ear snapped, the dark old stain on the belly panel; review fix: the stain was the brightest thing on the body, an orange oval from across a room, so it is smaller, darker and lower in contrast in `characters_bunny.py`). His mask has no moving mouth: the girl's voice comes from inside it, so on her lines he tilts his head and holds the flap open with a paw (the slot shots are side-on, his muzzle at the flap). Under the half-off head Dale's face says "Mama." with his own lips (the suit's cast has `talk` 0, so the two syllables are keyed by hand) and then goes still.
- **The format**: the police header (HOUSE RULES / RULE n OF 7, the story's clock in the corner: 7:42 PM .. 6:12 AM), captions on every line, seven rule cards (the police card over the blurred laminated rules on the fridge, each with its line icon; rules 6 and 7 are recalled before they are broken), tags (HOLLOWAY STATE HOSPITAL, the knock count), the global look: a red creep from the window smash (600 s), the gold dawn holding it back (709 s), the climax ramp from Mom's hand over June's eyes (770 s) with a blue heartbeat spill at the frame edge under the counts, a white flash on "Seven." and black; the aftermath drained; 1987 on the camcorder tape (date and time stamp), memories warm, the recalls desaturated with a static cut.
- **The comment prompt (258-279.5 s) is a VHS PAUSE**: the frame freezes on Mom's face after "I told you not to look at the treeline" (PAUSE, tape counter 0:04:18, tracking noise), the comment box slides up, the screen splits MOM | THE BUNNYMAN with OR, ONE WORD., the MOM half flickers, then PLAY rolls the tape on. The outro rewinds the tape to that split ("go back to the comment you left before rule two"): THE BUNNYMAN lit, then MOM with a reply arrow, the frozen Mom, then the frame plays: her smile widens and her eyes come to us ("She liked you too.").
- **The outro shows what it says**: black and a breath, the switch flips on and the frame warms, the living room with every lamp on, the Courier's masthead and the egg's stamp struck through, the bridge in daylight, a very ordinary cup of coffee by the notebook with the story's notes, the costume on its hanger (then from behind: the zipper pull slides down), THE TRICK card (1. CLOSE YOUR EYES, 2. COUNT TO SEVEN), the open eye, "SO YOU NEVER DID.", the rewind and the split, the window at night, the LIKE that lands like a knock (a knock cue on its hit), "And subscribe." = Grandma's porch light switching on, the porch light over the empty treeline, the next-episode card (NEXT TIME ON NIGHT POLICY, 3:00 AM, the phone ringing: DR. HALVERSON), NIGHT POLICY on "Sleep well.", the last line on black and the end card held for the outro song.

## The polish pass (staging and animation)
Run `python3 tools/validate.py` after any change to the plan (about 40 s; exit 1 on an ERROR; `--shots a-b`, `--no-lip`,
`--json`). It builds the film the way the renderer does and checks, from the plan and the actors' clips:
ANCHOR (every staging point of every set on a floor of its level), FLOOR (feet inside a room and clear of furniture, seated
people on seat anchors, nobody standing on a seat), LEVEL (feet at the floor height there; the stair treads), OVERLAP (two
people inside each other), REACH (contacts that miss their target at full weight), PROP (a prop held by two hands at
once, drawn by the set and held, jumping when it changes hands), CUTPOS (the same person on the same plan jumping across a
cut with no walk to explain it: `enter=True` on a P entry marks an entrance, `montage=True` on a shot marks an ellipsis),
STATE (the story's states by time: the curtains after 11:07, the porch light, the mail-slot flap, the kitchen window and
the back door after 4:30, the bathroom lock and door, the wrecked corridor, Mom's scratched arms), CAM (a move over 4 s, a
camera moving over figures that do not act, an empty set held long under a moving camera), LEN, LIP (the masked
Bunnyman's girl's-voice lines are the allowed exception). Result: `W/tests/polish/validate.json`.
Before the pass: 179 errors and 53 warnings; after: 0 errors, 4 warnings (keyed insert moves just over 4 s and two
outro holds, checked by eye).

`python3 tools/strips.py --shots a-b [--fps 12]` renders every frame of each shot at 12 fps, flags pops (a frame that
changes 3.5x more than the shot's median: a limb or a prop that teleports) and tiles the sheets with the neighbouring
shots' last / first frames (`W/tests/polish/before/` and `after/`: all 375 / 383 shots). Every flagged pop after the
pass is an intended event (a flash, a static or VHS cut, the hand covering the lens, a light switching, a card).
`python3 tools/before_after.py --before <dir with the old film.py / sets_bunny.py>` renders matched times from two
copies of the code (`W/tests/polish/before_after/`).

What changed (film.py unless noted):
- **Night through the windows** (`sets_bunny.build_view`): everything seen through an interior window at night sits under
  a dark veil (the lit rooms' grade had lifted the front yard into a pale, daytime field); the living room's `wide2` view
  sees the FRONT yard through the front window (it drew the back yard).
- **Hands** (`hero_hand`, `hero_paw`, `hand_layer`): every hand in an insert or a close-up is the cast's hand geometry at
  hero size: skin shaded toward the light, knuckle highlights, nails with a glint, creases in skin tones, the character's
  own sleeve with its cuff (rib knit for the cardigans and the hoodie), folds and the fabric's grain, a soft shadow on
  what it lies on; Mom at dawn has her cardigan pushed up over a scratched forearm; the Bunnyman's paws are plush mittens
  with fur tufts, pads and mud. `switch_finger` puts the fingertip ON the toggle and the wrist follows it; `wrist_for` /
  `hand_tip` / `hand_low` place a hand by its fingertip or its knuckles. The hand toward the lens goes soft and dark as it
  nears the glass. Hands over eyes (`paw_eyes`) lie across both eyes and leave the mouth free (June counts).
- **New inserts**: Grandma's family knock on the red-checked cloth (`ins_knuckles2`), Laurie's hands holding the golden
  egg (`egg_gold_hands`), the new dress on the closet door beside the 1987 clipping (`dress_photo`), three hatchet
  pictures (`hatchet_steps`, `hatchet_thunk`, `hatchet_pile`), the egg taken off the doormat through the crack.
- **Restaged**: the parade photo and the magic trick in front of the float (they stood behind it, hidden); Laurie walking
  out of the woods (a wide, then a medium on 'walked'); June sitting on her bed (she stood on it); the curtains closed
  by the right hands; the narrator crossing the hall to the door after the tap; Mom stepping off the stairs to take the
  ring (the front door still ajar); June coming off the stairs and kneeling at the slot in profile; "Small, and scared."
  on the trembling flap; Mom's blank face on "doesn't recognize it"; the dark attic corner (Mom a silhouette in the
  rocker, then her eyes in a band of the bulb's light); the bathroom dash and the tub (side by side, the hand on June's
  mouth reaching it); the dawn reverse (Mom turning her key: the keyhole anchor had its plan y and height swapped);
  her scratched forearms, then her smile; the body seen from the top of the stairs; Dale's "Mama." on his lips, then
  still; the mascot curled on the gravel under the trestle; the narrator's own face under Mom's hand on "It's the
  easiest thing in the world"; the cop crouching by the body; the desk split into the notebook and the cup.
- **Anchors** (`sets_bunny.py`): eight point anchors had their plan y and height swapped (the back door's knob, bolt and
  switch, the bathroom's knob, keyhole, lock); `fridge_rules` sits on the sheet (0.86 m).
- **State continuity**: the mail-slot flap stays open from 1:40 until Mom shuts it; the curtains stay shut after 11:07;
  the back door stands open after 4:30; the front door stays ajar until the ring is pocketed.
- **Camera**: a push longer than 4 s creeps at most 8 % (`scam`; `long_ok` lets a shot keep its move); long empty holds
  are split into cuts (the gap under the door, the desk).
- **Lips**: Laurie no longer mouths the narrator's line under the paw; the narrator's realisation on "Before sunrise." is
  in the eyes and brows, the mouth closed.

## Checks
- **Every shot reviewed**: review sheets `W/tests/film/final/sheet_NNN.jpg` (48 sheets, all 383 shots after the polish pass, NNN = the first shot on the sheet; first | mid | last frame of every shot with its lines), each checked against its line and the staging rules. The shots restaged after review were checked again on stills (`W/tests/film/still_*.jpg`): the tap on the front door (the door in frame), Mom tucking June in, the door opening a crack, Mom on the stairs (up the flight from the bottom), June creeping down in her socks and kneeling at the slot, Mom closing the slot and smoothing June's hair (the camera backed off: her head was cut), the Bunnyman at the slot (side-on), the kids asleep on the couch, the close-up backgrounds at the slot and in the attic, the body at the foot of the stairs, the paw over Laurie's eyes, the joined hands, the scream past the two of them, the cop in the doorway, the visiting room, the report card's A's, the end card.
- **Cut pairs and holes** (`--frames`): every cut as last frame | first frame over magenta (`W/tests/film/cuts/cut_NN.jpg`). The colour detector flagged 35 frames; rendered again over green (`cut_holes_true.json`: a pixel that changes with the background is a real hole) only the intended ones remain: the peephole's black surround (shot 105) and the black shots. The others were magenta-coloured picture (the parade's pink bunting and balloons, the police lights' red and blue, the VHS colour fringes on a glitch cut, June's room, the pink diary).
- **Lip sync** (`--lipcheck`, `W/tests/film/lipcheck.json`): 268 actor-shots. Every speaking actor moves on its own lines and on nothing else, except the Bunnyman's masked lines (the mask has no mouth; `tools/validate.py` lists them as allowed). Dale's "Mama." moves his own lips (its own extreme close-up since the polish pass).
- **Insert animation**: a review found every animated prop insert from the sets (`kw` given as a function of time) frozen on its last state, because `ob_insert` calls it with the film clock; `B_ins` now hands it the time since the cut (the crayon drawing slides in, the lock turns, the key goes in, the highlight walks down the rules, the egg halves part).

## Rendering
```
python3 render.py --stills 290.5,316,345.5 --size 960x540                     # -> W/tests/render/still_*.jpg
python3 render.py --clip 460.9 466 --size 960x540 --audio W/align/vo_en.wav   # one process test clip
python3 render.py --size 640x360 --fps 30 --workers 2 --out W/preview_tmp --audio W/align/vo_en.wav   # low-res preview
python3 render.py --workers 2 --from_ 460.9 --to 465.9 --out W/tests/render5 --audio W/align/vo_en.wav   # a 5 s full-mode test
P=2 bash tools/final_chain.sh > W/logs/final_chain.log 2>&1      # FINAL: 2560x1440 / 60 fps in 24 chunks, then deliver.sh
```
- **The preview** is `W/preview/preview.mp4`: 640x360, 30 fps, 1085.93 s (32,578 frames, 135 MB), the edited voiceover; 2 workers, about 8 min (re-rendered by fixer D; verify round 1 spliced two re-rendered ranges in frame-exact: render the range with `--from_/--to` on whole frames, then trim + concat + re-encode with the same x264 settings). `render.py` writes `film.mp4` into its `--out`: render into a scratch dir such as `W/preview_tmp`, then move `film.mp4` to `W/preview/preview.mp4`. `bash audio/final_mix.sh` muxes the final mix onto it as `W/preview/preview_mix.mp4`.
- **The full-mode test** is `W/tests/render5_460.9-465.9_2560.mp4` (June creeping down the stairs in her socks, then kneeling at the mail slot): 2560x1440, 60 fps, 300 frames, 2 workers, end to end in 49 s, the voiceover muxed from 460.9 s. Command: `python3 render.py --workers 2 --from_ 460.9 --to 465.9 --out W/tests/render5 --audio W/align/vo_en.wav`, then rename its `film.mp4`.
- **The final render** goes through `tools/final_chain.sh`: frame-exact chunks from the film's own length (`K=24`, `P` processes; a re-run skips chunks with an OK marker), joined by stream copy into `W/picture/picture.mp4`, frame count checked, then `tools/deliver.sh` makes `W/deliver/If_The_Bunnyman_Asks_You_To_Close_Your_Eyes_EN_1440p60_HEVC.mp4` with `W/mix/final/mix_en.wav` (it needs the final mix first). `tools/encode_chain.sh` is the resumable alternative to `deliver.sh` (capped CRF 17 segments, `enc_seg.sh`). On the shared 4-core machine run two chunks at a time (`P=2`); the picture is about 1-1.5 GB of H.264, so chunks plus the joined file need about 3 GB of disk at the peak. Run it as a harness-tracked background task, not with nohup.
- **Full mode** (`render.py` without `--stills/--clip`): contiguous slices per worker process (one OpenCV thread each), libx264 crf 16 preset faster, joined by stream copy; workers pass absolute frame indices, so a range render matches the full render frame for frame. Finished slices get a `.done` marker (delete markers and slices before re-rendering a changed film into the same `--out`).

## Speed (police budget: 0.6 s/frame at 2560x1440, one process, one OpenCV thread)
- **After the polish pass** (`W/tests/film/speed_shots_2560x1440.json`): the 20 restaged / new-hand shots, 6 consecutive frames each, steady mean 0.178 s/frame, the slowest the paw over Laurie's eyes at 0.28 s; first frames bake as before.
- Consecutive frames (`--bench N --consec K`: every 3rd frame, as a render sees them): 125 evenly spaced shots x 3 frames, steady mean **0.196 s/frame**; 40 shots x 6 frames, 0.206 s/frame (`W/tests/film/speed_2560x1440.json`). The slowest shots measured on their own (8 consecutive frames, one process): "And subscribe." as Grandma's porch light comes on (368) 0.59 s (1.9 s on the frames where the light rises: the lit layers re-bake), the front of the house (60) 0.45 s, June's room (90) 0.35 s, the cold open's 2.45x push on the treeline (0) 0.16 s; every other measured shot 0.05-0.3 s.
- The first frame of a shot takes 2-8 s while its static layers are baked.
- Fixed from this bench: "Mom's chair is empty." (173) went from 1.72 to 0.18 s/frame (the set's own depth of field sent a several-screen layer through the dynamic blur on every frame; the shot is now in focus throughout, `dof=0`).
- **The sharp-cache guard** (`engine/scene.py`, `_sharp_dynamic`, the `_blur_raster_too_big` idea applied to the sharp cached path): a sharp layer whose cached raster would pass `SHARP_MAX_SCREENS` screens (12, about 44 MP at 2560: a 170 MB raster, next to `_density_cap`'s 48 MP) is drawn straight into the frame while the zoom races (a second big bake wanted within `SHARP_REBAKE_S` = 0.6 s of film time); otherwise it is baked and reused as before. Measured: the first version (6 screens, no race test) put the cold open's woods on the dynamic path and cost 1.79 s/frame against 0.15 cached, because one bake serves a whole slow push while re-drawing a forest of vector trees costs 1.7 s every frame; with the race condition the cold open is back to 0.16 s, and a racing zoom on the same woods (fz 1 -> 3 in 1.2 s) costs the same either way (`_pick_density`'s headroom already limits re-bakes to one per ~1.4x of zoom), so the guard is only a ceiling on memory and on `_density_cap`'s soft upscale.
- The 5 s full-mode test ran 300 frames in 49 s with 2 workers (about 0.33 s per frame per worker, first-frame bakes included). Estimated final render: 65,156 frames, about 2-2.5 h with `P=2` on the shared machine (about 1.5 h with 3 workers on a quiet one).

## Cue sheets: the sound step's contract
`python3 film.py --cues` writes `W/cues/sfx_cues.json` (300 events `{t, name, gain_db, pan, space, params}`), `music_cues.json` (`{duration 1085.93, intensity, events}`: 90 events) and `shots.json` (the cut list `{i, t0, t1, kind, space, loc, era, cut, room}`). `W/cues/music_cues_plan.json` is the sound step's own file.
- **Spaces**: `inside` (the house), `outside`, `close` (inserts and close-ups), `bath` (inside the locked bathroom), `attic`, `woods`, `hospital`, `vhs` (the 1987 tape and the VHS pause), `memory`.
- **Event names** (the sound step maps them; `audio/sfx.py` `BUNNY_NAMES` and its aliases): the knocks `knock_door` (`pattern` 2-3-2, `group`, `index`; soft at sunrise; the LIKE's knock), `egg_tap`, `egg_rattle`, `egg_open`, `ring_roll`, `fire_crackle` / `fire_whoosh` (the burn barrel), `mail_slot` (creak_open / close), `girl_cry` (`through_door`), `bulb_hum` / `bulb_tink` (the attic), `page_flip`, `paper`, `paper_slide` (the drawing under the door), `window_smash`, `door_crash`, `wet_step` / `wet_drag`, `hatchet_thunk` (one per stair), `knob_turn`, `door_slam`, `struggle` (the fight on the other side of the door), `wet_crack`, `lock_turn` (`by_itself`), `key_in_lock`, `door_creak` (`front_door` crack, `bathroom_open`), `deadbolt`, `light_switch` (wall / porch), `marker_strike`, `zipper`, `mug_set_down`, `phone_ring`, `count_thump` (one per number of the count, `n` of 7), `swap` (`1987` / `now`), `sirens`, `police_radio`, `heart_monitor`, `hum` (`who`), `breath` (gasp / calm_exhale), footsteps by surface and weight (`footsteps_*`, quiet on the stairs in socks), beds (`ambience_night`, `ambience_woods`, `ambience_dawn`, `room_tone`, `crowd_parade`, `tape_hiss`), and the UI (`ui_pop`, `typing`, `magnet_click`, `vhs_pause` pause / play / rewind, `vhs_glitch`, `glitch`).
- **Music events** (suggestions on the picture's frames; `audio/music_plan.py` places the score and its word-anchored events win): `jingle` by `version` (girl_broken, hum, hum_child, outro, vhs_parade; the tinny one from the woods is a bed in the sfx sheet, `version` tinny_woods), `rule` (card stings), `riser`, `swell`, `hit`, `stinger`, `braam`, `sub_drop`, `silence` (drop-outs before the scares, and the VHS pause), `pulse_on` / `pulse_off` (Mom's hand over June's eyes to "Seven."), `heartbeat` (under the counts), `drone`, `outro_warm`.

## Sound prep (the Bunnyman film)
Everything below is in `audio/`; run from `film/`. The verdicts, the music map and the tests are measured, not guessed.
- **Catalogue**: `python3 audio/epidemic_catalog.py --bunny` -> `audio/catalog_epidemic_bunny.json` (the bunny set
  `W/samples/epidemic` first, then the dummy, delivery, police and mirror sets; 271 effects, 45 tracks; a rebuild reuses
  every unchanged row and only recomputes `serves`). `library.py` and `score.py` read it first. `MAP` gives each file the
  `sfx.py` names it can feed; `NOT` keeps the rejected files away from the older names.
- **The owner's new files, judged one by one**: `python3 audio/review_sfx.py` measures all 80 (loudness, clipping,
  floor, spectrum, codec low-pass, onsets, harmonic share, tonal clarity, stereo, and what a recogniser hears in the
  crowds and voices) and draws `W/mix/review/sheet_*.png`; `--md` writes `W/mix/sfx_review.md` from its `DECISIONS`
  (effects: 29 use, 21 process, 20 reject; music: 6 use, 4 reject; every reason written down; the appendix
  `sfx_review.md.notes` covers the synthesis and the free library).
- **The jingle**: `audio/jingle.py` is the ORIGINAL Pemberton's tune (D major, 2/4, 126 bpm; bars 5-6 climb the scale one
  note per syllable of "close your eyes and count to se-ven", so June's count in the climax climbs the same scale in
  D harmonic minor and stops on C#, one step short of home). `python3 audio/jingle.py [names]` renders every version
  to `W/mix/jingle/` (vhs, vhs_cold_open, parade, speaker, speaker_near, musicbox, musicbox_minor,
  musicbox_wind_down, hum, hum_x, knocks, girl, climax, count_1..7, outro, studio), checks each one
  (`jingle_check.json`: the tune's notes found in the render, the voices' pitch against the melody) and draws
  `jingle_sheet.png`. The cold-open version puts every note on the narrator's own syllable of "Hop, hop, hop
  along..." while the band keeps a steady pulse (`COLD_OPEN_MELODY`, `COLD_OPEN_ANCHORS`). The family knock 2-3-2 is the
  tune's own rhythm (`KNOCK_BEATS`).
- **Voices made from the narration**: `audio/voicesynth.py` (WORLD, the cast settings of `tools/vo_voices.py`): `hum`
  (the narrator's /m/ from 37 words, sung on the melody: Mom, Grandma, June, the old body), `sing` (the narrator's spoken
  syllables re-timed and re-pitched onto notes: the real Laurie's broken "Hop... hop... hop along... the Bunnyman
  sings his..."; a recogniser hears "...hop... The bunny man sings his"), `cry` (her crying: wails that crack, hiccup
  sobs, shaky gasps). Analyses are cached in `W/cache/voicesynth/`.
- **SFX**: `audio/sfx.py` `BUNNY_NAMES` (44 new names, the docstring lists every parameter): `ambience_woods`,
  `owl_hoot`, `crowd_parade`, `hospital_corridor`, `hospital_room`, `burn_barrel`, `plastic_melt`, `egg_tap`, `egg_set`,
  `egg_rattle`, `egg_open`, `ring_roll`, `ring_drop`, `ring_hand`, `oven_mitt`, `knock_family` (2-3-2 on the jingle's
  beat, `groups` puts each group into the narration's gaps), `slot_flap` (open / close / snap), `girl_cry`, `jingle`
  (any version as a sound in the scene), `attic_door`, `bulb`, `chest_lid`, `page_flip`, `diary_lock`, `window_smash`,
  `door_crash`, `wet_drag`, `hatchet_step` (the Thunk lands 0.3 s after each tread), `doorknob`, `paper_under_door`,
  `struggle` (wall / shake / slam / crack / full: restrained, no library screams), `key_outside`, `sirens_arrive`,
  `vhs_pause`, `light_switch` (wall / porch / porch_off), `music_box_wind`, `flash_pop`, `dogs_search`, `bathtub`,
  `body_fall_stairs`, `zipper`, `fridge_paper`, `curtain_close`, `peephole`. New spaces: `woods`, `door` (the hall
  heard from inside the shut bathroom), `bathroom`, `slot`, `vhs`, `attic`. Aliases and keyword guesses cover loose names
  (`family_knock`, `mail_flap`, `crying`, `song`, `hum`, `hatchet`, `thunk`, `fight`, `slam`, `crack`, `porch_light`...):
  `python3 audio/sfx.py <name> out.wav --params '{...}'` renders one.
- **Voice FX** (`audio/mix.py`, timeline `fx`): `door` (2.4 kHz top, the panel's boom, the crack under the door, the
  hall, the tiled bathroom; -3 LU), `slot` (300 Hz-3.8 kHz, the slot's 1.1 kHz channel and 3.6 ms comb; -1.5 LU),
  `memory` (Grandma warm and distant; -1.5 LU), `whisper` (dry, close, the breath's air lifted; 0 LU). An unknown fx is
  left dry with a warning. `--who-fx` is now empty by default (the old `X=hall` would have put the old body in a hall).
- **Music**: `audio/music_plan.py` (19 track sections, 172 intensity points, 135 tension events, 24 identity events;
  `python3 audio/music_plan.py --table` prints the map) and `score.py` (`render_jingle`: the `jingle` event type; the new
  tracks' varispeeds in `TRACKS`; the children's tunes in `VINTAGE`; `SHOW_DUCK['jingle']` and `JINGLE_LIFT` per version).
  The score's duration runs to the end of the outro jingle: **the picture must hold its end card to about 1085.4 s** (it holds to the film's end, 1085.93 s).
- **The sound-design pass**: `audio/sfx_plan.py` ADD (112 cues anchored to the narration's words: every bed, every
  off-screen sound the narration hears, the small foley of the close-ups) on top of the picture's sheet; a row is
  skipped when the picture already has that sound within 1.5 s. EDIT is empty until the full-length checks.
- **Tests**: `python3 audio/sfx_tests.py [1..8]` mixes 8 windows through the whole pipeline (mix.py with the plan) to
  `W/mix/tests/NN_name.wav` + `.json` (every cue re-rendered and checked: sync, phone band, level against the voice and
  the music; every identity layer's level), `--sheet` draws `W/mix/tests/tests_sheet.png`. One mix at a time (about
  1 min each; the first run spends 2 min analysing the tracks into `W/cache/score/`).

## Sound: the final mix
Rebuild after a picture change, from anywhere (about 16 min; the mix peaks at 12 GB of RAM: never while a render runs, never two at once, and never edit `final_mix.sh` while it runs: bash reads it as it goes):
```
bash "Vox test/Bunnyman Video/film/audio/final_mix.sh"          # cues -> mix -> measure -> scene sheets -> preview_mix.mp4
```
1. `python3 film.py --cues`: the cue sheets from the picture (`W/cues/`).
2. `audio/mix.py ... --plan full --hits-db 4 --voice-ride 2.0` -> `W/mix/final/mix_en.wav` (+ the hard link `mix.wav`, `stems/`, `cues_used/` = the two sheets as mixed, `mix_report.json`, `mix.log`). About 14 min.
3. `audio/measure_mix.py W/mix/final --plot` -> `measure.txt`, `measure.json`, `measure_cues.json`, `measure_plot.png`.
4. `audio/mix_scenes.py W/mix/final` -> `scenes/NN_name.png` (36 scene sheets: spectrogram, cues, score events, stem levels).
5. The mix onto `W/preview/preview.mp4` -> `W/preview/preview_mix.mp4` (`--no-preview` skips it).

- **If the picture changed**, re-render the preview first (the mix is muxed onto it; about 8 min): `rm -rf _work/preview_tmp && python3 render.py --size 640x360 --fps 30 --workers 2 --out _work/preview_tmp --audio _work/align/vo_en.wav && mv _work/preview_tmp/film.mp4 _work/preview/preview.mp4 && rm -rf _work/preview_tmp`, then `bash audio/final_mix.sh`.
- **If the narration changed**: the Narration order (`vo_edit.py build`, `rm -rf _work/align && python3 tools/align.py --write-pauses`, `vo_edit.py check`, `vo_report.py`), then the preview, then `final_mix.sh`. The sound plans (`music_plan.py`, `sfx_plan.py`) are anchored to lines and words, so they follow the new timing.
- `python3 audio/mix.py --check W/cues W/mix/final` says whether the mix is stale against the picture's sheets.

**The final mix** (`W/mix/final/mix.wav` = `mix_en.wav`, 48 kHz 24-bit stereo; on the preview: `W/preview/preview_mix.mp4`). The table and notes below are from before fix round 1 (1087.84 s); the current numbers are in the fixer D section:

| measure (`measure.txt`) | value |
|---|---|
| integrated / true peak / LRA | -14.05 LUFS / -1.67 dBTP / 3.2 LU |
| voice, music, SFX, bed (integrated, rel the mix / the voice) | voice +0.47 LU over the mix; music -14.8, SFX -19.0, bed -14.2 LU under the voice |
| voice minus bed while a line is spoken (400 ms blocks) | p1 6.5, p5 8.5, p50 17.8 LU; under 6 LU 0.62 %, under 3 LU 0.22 %, under 0 LU 0.07 % of speech (before this pass: p1 2.6, under 6 LU 3.2 %) |
| the same in the 1-4 kHz band | p1 4.4, p5 11.9, p50 28.7 dB; under 6 dB 1.39 % (was 1.87 %) |
| weak spots | 6, all at scares that land on their own word by design (the face reveal over "It's", the window on "explodes", "IT'S MY HOUSE!", the hit on "key") and the stomach-drop sub in the comma after "drops," (-1.2 LU); 25+ before |
| SFX cues re-checked | 263 one-shots, 0 flags (21 before: masked foley, two late or early transients, thin on a phone) |
| silences | 29 (1.6 / min), median depth 34 dB; the three shallow ones (16.95, 113.87, 991.56 s) are the jingle / hums playing in them by design; "Then nothing." and the cut on "Seven." are true silences (after "Seven." the mix sits 50-56 LU under its integrated level: only the dawn room tone) |
| music | present 94.7 % of the time outside the authored silences; no holes; bed 3 s p10 / p50 / p90 -22.7 / -16.1 / -11.6 LU, bed in gaps +1.7 LU over the bed under speech |
| events | 4.0 hits / min, 15.2 one-shot cues / min, 7 rule stings |

- **Tension curve** (bed rel the voice by section): cold open -15.7, 1987 -14.4, the house and June -15.7, rule 1 -14.2 (the dying speaker on its drone), rule 2 -14.9, rule 3 -14.8 (the knocks alone in a 6 s drop-out), rule 4 -14.0, rule 5 -14.0, rule 6 -13.4, sunrise (false relief) -15.6, the unmasking -11.4, the dress and the count -12.6, the reveal -14.1, the swap -10.6, the aftermath -17.1, June's visits -17.9, "Easter is in nine days." under a 5.3 s drop-out (the bed about 40 LU under the line), the outro -22.2 and the outro song (the jingle's cheerful version and its last hum, the end card held to 1087.84 s).
- **The hardest hits** (the bed's loudest 100 ms moments over the mix's integrated): the face reveal +4.1 LU, the swap on "Seven." +3.3, then Mom in the doorway +1.2, "Back to bed" +0.3, GET OUT +0.1; every other hit is under 0.
- **The jingle comes back 24 times** (the score's identity stem, before the voice-keyed ducks, rel the voice): the VHS commercial under "Hop, hop, hop along" -10.2 LU, Mom's hums -12.4 / -14.4 / -14.6, the float's PA at the parade -10.6, the child's hum out of the woods -13.3, Mr. Otter for June -13.6, the dying speaker in the woods -11.5 (loudest 400 ms -6.0), Grandma's music box -14.5, the girl's broken song through the slot -9.1, Mary Had a Little Lamb on the crayon diary -11.9, the count phrase on "For the magic trick" -12.3 and on Mom's "Close your eyes. And count to seven." -10.1, the seven count notes -4.9 to -10.5 (Seven cut dead), the old body's hums -17.0 / -15.4, the music box winding down after "nine days" -12.1, the outro -9.9. The 2-3-2 knock is on the tune's beat in rule 3, in Grandma's memory and in the recap.

**What the mix pass after the channel rename changed** (all measured, nothing listened to):
- `audio/mix.py`: the **voice clarity ceiling** (`CLARITY_MARGIN_LU` 6, `CLARITY_MAX_CUT_DB` 10): while a line is spoken the bed is cut by its excess over the voice's own 400 ms level - 6 LU (2 % of the speech blocks are cut; the hits' spare windows are left alone); the music / beds duck holds 0.12 s after each syllable (`DUCK_HOLD_S`); **true silences** (plan silences at level >= 0.95) also cut the SFX events and hits buses (the swap's ring sat 26-31 dB into the silence after "Seven."); the score renders from a **fixed seed** (`SCORE_SEED`: the old seed was the hash of the cue sheets, so any cue change re-rolled the whole score and moved every weak spot); the hits limiter's boosted ceiling is graded (the face reveal and the swap +6 dB, the other boosted hits +3 dB).
- `audio/sfx.py`: stingers must hit (at most 8 s, peak within 0.3 s of the onset: both rule recall cards were playing a 26 s sub sting, late and inaudible on a phone); footsteps and knocks get a high shelf until their top is within 12 dB of the whole (`PHONE_FIX`, `phone_presence`: thin on a phone before); a single wood footstep lands its -12 dB onset on the foot plant (some grains rose 50-200 ms before the plant); the flashlight click's grain starts 3 ms before its onset (it read 45 ms early).
- `audio/sfx_plan.py` EDIT: the masked gusts and foley raised (cold open, "Neither was the suit.", Dad's steps, June's stair, Mom with the dress, the cop, the midnight walk to the door, the hospital corridor), the inaudible gust under the reveal dropped, Dad's flashlight in the memory space, the 1987 trade's flash -3 dB (its tail sat over "...in someone else."), the recap's family knock -9 dB (was -13, 19 LU under); EDIT changes can now set `space`.
- `audio/score.py`: a silence that opens on an identity cue keeps the identity stem only if the cue plays on into it; the count's "Seven" note stops at the cut, so the "Six" note no longer rings through the silence after "Seven." (with the true-silence cut above, that silence now measures about -85 LU of music and -50 LU of room tone under the mix's level).
- `audio/music_plan.py`: the rule-by-rule arc (track gains: rule 1's drone -1.5, rules 2-6 +0.5..+1.5 dB; rules 2-3's calm stretches +0.05 intensity), the stomach-drop sub 0.55 -> 0.42.
- `film.py`: the LIKE icon and its knock land in the comma after "like," (on the word they sat 5.3 LU over it); 3:00 AM sits above the phone on the next-time card (the caption covered it).
- `audio/measure_mix.py`: grass steps count as slow-onset like the other footsteps.

## Fix round 1, fixer A (the picture blockers and the acting / design that runs through the whole film)
All in `film.py` unless noted; `tools/validate.py` 0 errors (4 known WARNs), `--lipcheck` clean (only the masked lines).
- **The egg** (rule 2): the front door is pulled open a real crack (`DOOR_AJAR` 32 degrees, `door_latch_edge`, `door_gap_pt`)
  while the narrator holds the knob, which travels with the leaf; `door_spill_layer` puts the porch light in the gap and a
  warm fan of it on the hall floor (`sets_bunny._outside_porch` now lights the porch lantern when the hall's porch light is
  on). The medium is shot from the latch side so the ajar door and its lit crack stay behind the narrator; `open_egg`
  (`characters_bunny.py`) closes the free hand on the egg by its grip point, so the halves part exactly where the egg was,
  after a twist of both wrists (`pose.egg_twist` turns the lid's sheen). "Inside, rolling around" is the new insert
  `egg_halves_hand` (the narrator's view down at the right palm: the cup in it, Dad's ring rolling and settling; the lid
  in the left hand); the recap uses its settled frame and the outro rewind picks it up. The ring-on-palm insert now has the
  narrator's skin and hoodie cuff.
- **The ring**: a side-on two-shot (`RING_CAM`: Mom by the stairs left, the narrator right, the ajar door between them):
  Mom comes round the newel (her draw order switches as she clears the stair rail), takes the ring, lifts it in front of
  her face and stares at it as the smile drains; the close-up holds it pinched in her right hand (a hero hand whose forearm
  rises from her near elbow) with her eyes locked on it and a slow blink; "She puts it in her pocket." is the insert
  `ring_pocket` (her cardigan now has two patch pockets, `characters_bunny._front_cardigan3`).
- **The point**: the wave stops on the treeline close; on "lifts" the cut goes over his shoulder from the woods
  (`OTS_CAM`, `_point_house`): the whole mitten aimed along the line from his shoulder to June's lit window (no single
  raised digit); "Past us." is a closer over-the-shoulder (`OTS_CAM2`); the recap uses the same.
- **The doorway**: June's door stands open (`JUNE_DOOR_OPEN` 95) in every doorway shot and the recap; Mom is dead still
  with her hands folded (`mom_in_doorway`), no blinks, one slow tilt; she only smiles on "She's smiling." (`creep_smile`) and
  keeps that smile into "I told you...". The outro's "She liked you too." close-up starts
  exactly as that frozen frame (same smile, 12-degree tilt, zoom, open door) and plays on: the smile widens, the head comes
  upright, the eyes lock on the lens.
- **Back views** (`characters_bunny._figure3` / `_bunny_figure`): an arm whose hand is well behind the body's plane is drawn
  behind the torso (Mom's hands in the sink, a hand on a door seen from behind), never a front hand painted on a back.
  The sink gets a slow scrubbing loop (`washing_up`).
- **The knocks**: the narrator flinches at every knock and turns to Mom, Mom's head tilts as she counts and nods on
  "Seven." (`knock_acts`); the light under the front door shows the shadow of two feet and jolts with each knock; the count
  tags sit in an arch over the door frame, left to right (`door_tag`), never on a body; Mom waits with folded hands
  (`mom_waits`), the narrator holds the hoodie (`kid_braced`); "standing right next to me" is a 3/4 two-shot from the
  narrator's side (the eyes dart to her, a swallow).
- **The climax** on the landing (`SWAP_CAM`, `SW_*`): Mom is screen LEFT in every medium (the first hand over June's eyes
  at 770 s, "So the first time..." and the swap), so her hand comes from the left as in every close-up. The swap is three
  beats: June's close-up pulled out of frame by the narrator's hands (busts accept `cx`/`cy` as functions of time), Mom's
  hand left hanging empty; the two-shot where the narrator kneels into the palm; the ECU of the squeezed lids under her
  fingers.
- **The body**: "lies on his back" is seen straight down (`ins_body_above`: the figure lying on the runner it lies on,
  arms out, the mask shoved off and twisted, the dawn stripe and its dust); every close-up of Dale is from above with the
  hall floor under his head (`floor_above`, bust `floor=`, `rot=`), the framings vary (the mask, the face, the stubble, the
  eyes above the caption, the lips, the face going still with one paw twitch on the runner). Dale is gaunter (narrower jaw,
  sunken temples and cheek hollows, `gaunt` 2.3), with visible grey stubble (`stub_dots`) and cracked lips (`cracked`); the
  mask can twist (`pose.mask_twist`, `mask_slide`). The 1987 wake-up is `ins_under_bridge` (curled on its side on the
  gravel, the ties' shadows across it, a paw stirring on "woke").
- **Faces**: Mom's resting face (`too_still`) is now composed and nearly blank (smile 0.12); her smiles are separate beats;
  `fury` for "GET OUT OF MY HOUSE." (jaw wide, teeth bared, head thrust at the lens, the frame shaking; before it she squares
  up with her fists down); the kids' fear on narrated lines keeps the mouth shut (`shock_shut`, `cry_shut`: wide eyes,
  pressed lips, a swallow). Forehead folds scale with age (`characters._wrinkles`), the narrator's eye bags are lighter.
- **The Bunnyman now** (`characters_bunny._BUNNY_FUR['dirty']`): grimy grey-brown, the pinks gone dirty mauve, no pink
  cheek blush, a grey belly panel with an irregular low-contrast smear (no outline ring), mud worked up from the hem;
  thicker plush limbs; the eyes always clipped to the head; the snapped ear's break shows grey stuffing (not thread marks).
  On the masked lines the body acts: uneven sobbing catches that heave the shoulders, a paw rubbing at the glass eye
  (`bunny_cry_bust`, `_sob_beat`); a lunge of the head on "IT'S MY HOUSE!".

## Fix round 1, fixer B (the picture majors and cheap minors before 600 s)
All in `film.py` unless noted; `tools/validate.py` 0 errors (WARN: 4 known camera holds), `--lipcheck` clean (only the
masked lines). Shot numbers below are the current ones (`python3 film.py --list`). Evidence: `W/review/fixer_b/`
(`sheet_a_0-200s.jpg`, `sheet_b_200-400s.jpg`, `sheet_c_400-600s.jpg`, `strips/s1..s6_*.jpg`).
- **The hook (#0)**: a telephoto of the filthy Bunnyman at the treeline, about a third of the frame, the moon low behind.
- **June's window (#81, #82)**: no camera-only push through the glass: the yard, treeline and moon through her window
  (`moon_dir` in `sets_bunny` puts the moon in the window), then a cut on "there" to a telephoto (`WINDOW_TELE`) where he
  lifts his head to the house. June's "He's sad." face is `wistful` (innocent, not the half-lidded smirk).
- **1987**: the crowd has arms, faces, hats and kids on shoulders and cheers on a two-frame cycle (`_crowd` frames a/b
  swapped by `ob_parade` at `CROWD_RATE`); "handing out plastic eggs" shows a pink egg in his paw taken by a kid's hand from
  the curb (`handout_acts`); "He showed her a magic trick." is a closer two-shot: empty paw, closed, the other paw passes,
  open: a pink egg in a burst of light, given to her (`trick_acts`; her eyes pop and the grin spreads, no open-mouth gasp
  on the narrated line); two search dogs on leads with handlers (`draw_dog`, `dogs_acts`), noses down to the trestle, heads
  up on "lost"; the VHS stamp says APR.16 1987 and the poster LAST SEEN THURSDAY, APRIL 16, 1987 with Dale's own face at 19
  (`dale19`); the name badge breathes on the fur with a glint, as two framings (a punch-in on "named": no 4.9 s zoom);
  Laurie's golden egg is cupped in both hands.
- **Since**: Dad's flashlight beam is a cone onto the grass ahead of him; his close-up is in the yard, not on the porch;
  the new yellow dress on the closet door is lit warm by the hall light (reads yellow); Mom's early lines (2, 11, 27) have
  a warm smile beat over her blank resting face; the rule cards mark the sentence being read after the type-on
  (`_rule_marks`).
- **Rule 2**: the peephole first sees the empty porch and finds the egg on "Except for an egg"; the egg is old sun-faded
  matte plastic with scuffs (`sets_bunny._egg_scuffs`), its rattle a bigger rock; at the burn barrel the egg is between both
  oven mitts from the first frame, her eyes on it, lifted over the rim and dropped on "sets it on fire" into the fire on
  the burning trash (`_ins_egg_fire` heap), "Nine eggs." shows the old ones melted round it; the pick-up hand comes out of
  the door gap at knee height, back of the hand up.
- **Rule 3, Grandma's knock (#142-#147)**: the 2-3-2 is knocked on the oilcloth by her fist on the cue times (insert
  `knuckles`, cue `knock_door` kind='table' who='grandma'), then a 3/4 two-shot with the six-year-old, then varied close-ups.
- **Rule 4, the mail slot**: the slot sits at 0.74 m on both faces of the door (`SLOT_Y`); the porch face has its own
  brass slot plate and flap and his paw holds the flap; the slot's dull brass on the slate door matches in the wide and
  every insert (`_ins_slot`); Mom says "It took my voice" from the door side, facing us, with the two on the same sides as
  at the knocks; June comes off the stairs and kneels up at the slot (both shins on the floor) in profile, her close-up
  faces the slot; "June looks back at Mom" now cuts to Mom humming over her for 1.1 s (#169, was 0.6 s) before "Yeah.";
  Mom closing the slot stands nearer so her fingertips land on the flap (no REACH miss).
- **Rule 5**: the two asleep and slumped on the couch, June's head on the narrator's shoulder, her blanket over both of
  them to mid-shin (`blanket_acts`); "still locked" is the front door's latch edge (chain on, deadbolt thrown) with the
  narrator's hand closing on the knob and trying it twice (`try_knob`, `knob_turn`, `knob` rattle cues); "in her lap" is
  the insert `diary_lap`; the crayon is huge crooked letters (each its own size and lean) with June's fingertip tracing
  under each line as it is read (`trace_finger`); her hand turns the page on "Then Easter, 1987" (`ins_diary_turn`, one
  hand all the way over, no flip at the spine) and leafs on through three cursive spreads on "page after page"
  (`ins_diary_pages`: the hand comes in, turns, travels back to the next leaf, turns; `_diary_page_turn`).

## Fix round 1, fixer C (the picture majors and cheap minors from 600 s to the end, the outro included)
All in `film.py` unless noted; `tools/validate.py` 0 errors (4 known WARNs: #110, #205, #321, #392), `--lipcheck` clean (only the
masked lines #158, #167, #247). 397 shots. Evidence: `W/review/fixer_c/` (`sheet_NNN.jpg`: first | mid | last of every shot from
#212; `strips/a_..m_*.jpg`: 4-15 fps strips of the changed actions).
- **Rule 6, the break-in**: "Wet." / "Dragging." are two new inserts low on the kitchen lino (`ins_wet_floor`, `_lino_persp`,
  `_plush_foot`, `_wet_print`): a sodden, filthy plush foot slams down beside its last prints (splash, drips from the fur) and lifts off
  a dark wet print; then the hatchet's head is dragged across the frame ON the floor (the blade's corner on the lino, the handle
  rising out of frame to the paw), a wet smear with the moon in it and a pale scratch behind it. "I grab June and run.": a closer
  corridor camera; on "grab" the narrator lunges and closes a hand on June's wrist, spins and the two RUN at us hand in hand
  (about 2.5 m/s); "Bathroom." is from inside, by the tub: they burst through the doorway (both cross the threshold in full view),
  the narrator turns at the leaf and shoves the door shut with her palm riding it (`shut_acts`). The tub: June huddles turned to
  the narrator so the palm lands on her MOUTH (`tub_hand`), and "my hand over her mouth" cuts to a close two-face shot: June's wet
  wide eyes over the narrator's hand clamped on her mouth and chin (`hand_on_mouth`, `bust_mouth`). The stairs: one heavy
  tread every 0.95 s (`STEP_T`: 616.85, 617.80, 618.75 ..., a settle on each landing, a footstep cue on each and a hatchet thunk
  0.3 s after), the hatchet-steps insert carries the same rhythm (hits 620.0, 620.95, 621.9, 622.85) and now reads as the house's
  flight seen through the dark banister with the filthy plush feet climbing ahead of the dragged hatchet (smaller paw). "...from
  our woodpile.": a cut to the woodpile by the shed in the moonlight and the chopping block with a fresh pale gash where the
  hatchet always stood (`sets_bunny.chopping_block(hatchet=False)`, `ob_yard(chop=False)`; the split logs are drawn in depth
  order with shadows). The crayon drawing is framed from its own geometry: the bridge; a tilt DOWN the page to the tall man (no
  longer under the caption); the lady with the rock, then a cut in to the wide smile; the bunny, then a cut in to the blue tears.
  The fight: Mom strides out of her room at the end of the hall and squares up (fists, lean, heaving breath, a heavy step in the
  medium); "The whole hallway shakes." the bathroom door shudders in its frame against the bolt with plaster dust trickling, the
  feet shadows thrash under it (`ob_bath(rattle=)`); "slams" the leaf bows in hard (`slam`, stronger), a shower of dust, a body's
  shadow blots out the light under the door; "Screaming." the two flinch into each other, hunched, eyes squeezed.
- **Rule 7**: "Mom knocks, softly" shows: the leaf gives a hair on each knock (`ob_bath(knocks=)`) and her shadow under the door
  rocks with her knuckles; on "You followed every single rule" June rises onto her knees, a hand out to the rim, and the
  narrator grabs a fistful of her top and holds her down (`rise_acts`); the wreck is readable from the end of the corridor (claw
  rakes, hatchet chops with the lath, a dragged smear, a hole punched through, `sets_bunny._scratches_wall`) and Mom stays in
  the shot at the open bathroom door; after the fight her cardigan is torn at the shoulder, a button gone, dark spatter down
  the front and her hair wilder (`characters_bunny._front_cardigan3`, `_hair_region` when `pose.scratch`).
- **The reveal**: "In someone else." the mask bowed right down over the paws (h_nod 1.7); "...too scared to take off" a child's
  terror in the suit: hunched and trembling, the mask jerking round at the woods, then both paws on the sides of the head,
  gripping it ... and letting go (`scared`); Dad talks with his hands and steps closer (lips closed: the narrator's line), the
  Bunnyman's head tilts to him, it rocks and lifts a paw toward him (`dad_talk`, `bunny_listen`); "It's the easiest thing in the
  world." is now the reverse two-shot: Mom (screen left) smiling down, her scratched forearm rising from below to the hand over
  the narrator's eyes (no more three identical busts on one axis).
- **After**: "I'm on my knees" kneels Mom's body where it knelt for the trick (`SW_MOM`, knees 2) with the scratched arms out;
  "I screamed my own name" is the reverse of "my own face looks down at me": Mom's body on its knees screaming up into the lens,
  arms reaching (the wreck behind); the cop comes in along the wall past the head and kneels on the FAR side of the body, the
  body between him and us; the whisper is two beats: June climbs up into frame onto her lap (the woman's arm comes round her),
  then June's lips at the woman's ear with a cupped hand while the woman's eyes widen; `narrator_neat` (the old body at the
  hospital) has the narrator's own chin-length hair combed tidy and a sixteen-year-old's smile (`CAST tidy`, `fold_k`).
- **Outro**: "turn a light on now" flips the living-room lamp switch on the rose paper, unlabelled (`_ins_switch(room='living')`:
  the porch light is kept for "subscribe"); "No Pemberton's." is the egg lying open and EMPTY in its two halves on the desk, the
  stamp struck through (`egg_empty`); "just a costume" is the empty suit hanging slack on a wooden hanger from the closet rod
  (sleeves and feet dangling, the dark empty neck hole) with the head on the shelf beside it, its hollow showing
  (`_costume_flat`, `ins_hanger`), and from behind the zipper slides down; THE TRICK card is full from its first frame (the
  title, the two empty rows that light on "close" with an eye closing and on "count" with the count ticking to a red 7); the
  LIKE lands as three knuckle raps on the red front door, each filling a third of the like on it (`card like`, three
  `knock_door` cues); the end holds have the porch light breathing and moths blundering in front of the lens (`moths_layer`); the
  next-episode phone rings in bursts on the nightstand (buzzing, ring waves, its light pulsing, the colon of 3:00 blinking).
- **Validator** (`tools/validate.py`): OVERLAP measures a lying body along its 1.7 m length (the cop knelt INTO the body and passed
  because only its centre was checked).

## Fix round 1, fixer D (every sound item, then the full rebuild)
Critic 3's voice and sound items, the sound notes of fixers A-C, then the narration edit, the timeline, the preview, the cue
sheets and the mix rebuilt on the final picture. Evidence: `W/review/fixer_d/` (`verify_00..07.jpg`: one still per picture
fix of fixers A-C from the NEW preview, 88 tiles, each with its new time, the authored time and the fix; `stills/`;
`vo_splits*.png`: the hand-set splits on 2 ms spectrograms with the pitch and formant tracks; `vo_tails_kept.png`).
- **The narration** (`tools/vo_edit.py`, `tools/vo_voices.py`, `tools/vo_asrcheck.py`): see Narration above. All seven
  blockers (B1-B7) and M1-M5 / m1 are gone; the recogniser check passes every line. "It" of "It has a zipper" (M3) was
  never cut: the take has digital silence 906.40-906.60 and "It" starts at 906.62; Parakeet just puts it 0.3 s early.
- **The timeline moved** (1077.99 -> 1076.08 s; up to -2.0 s near the end). The picture follows its lines (`t()`, `w()`),
  and film.py's absolute-time tables (the story clock and corner labels, the VHS pause, THE END, the fear arcs, the
  global look's red / dawn / climax ramps, INTENSITY, EXTRA_SIL) are now mapped through `timeline_authored.json` (the
  line times they were written against) by `at()` / `authored()` (piecewise linear, line by line): never write a new
  absolute time into those tables without it. The Courier push on line 323 stops at 3.8 s (the line grew 0.27 s).
- **A crash fixed on the way**: a preview worker died on frame 840 (`skia.Op` "Failed to apply op" on the mascot's
  head pads). `engine/core.py` `inter / union / minus` now retry with a 0.01 px nudge and fall back (union: the two
  paths added; difference: the first); the two direct `skia.Op` calls in `characters.py` are guarded too. The final
  render would have died on the same frame.
- **The scares over the narration (M6)** (`audio/mix.py`): the narration gets a loudness cap (`voice_cap`, VOICE_CAP_LU
  2.3: no 400 ms block more than 2.3 LU over its integrated level; a 4:1 ride over +1 LU before it; whole-word cuts,
  1.3 dB at most) - before it the narration's own loudest lines were the loudest moments of the film (+5 LU); the
  boosted scares get an absolute ceiling (-1 .. -2 dBFS by grade) and a 10 dB drive into the hits limiter inside a spare
  window of at least 0.4 s, the glue leaves them alone, and the bed statistics the music gain is solved on leave them
  out; boosts: the window (+ a 6 dB 1-4.5 kHz notch for 0.3 s so "explodes" reads), the back door, the crack 2.5-3;
  "IT'S MY HOUSE!" and "key" moved after their words, the face reveal onto the cut 0.22 s before "It's" (spare 0.2);
  `--hits-db` 4 -> 6. Measured: see the table below.
- **Rule by rule (M7)**: ARC_TARGETS steers the bed in the gaps between lines (rule 1 -19 .. rule 6 -11.5 LU rel the
  voice) by section offsets on the music bus, solved in the music gain loop (the shape: the mean stays the solver's);
  the plan adds layers as the night goes on (a faint pulse under the mail slot in rule 4 and under June's
  disappearance and the last diary page in rule 5) and more tension events in rules 5-6 (the diary, "I am Laurie.",
  the hatchet, the voice under the door, the drawing).
- **Character voices (M8, m3, m11)**: the girl x1.24 (above); June's "Yeah." x1.22; the girl's "Please." through the door
  +4 dB (`LINE_TAG_DB`). The voice-made sounds were cached by duration and seed only, so the crying was still the old
  man-tract girl: the caches (`sfx.r_girl_cry`, `sfx.r_jingle` for hum / hum_x / girl) are now keyed by the voices and
  the edit (`_voice_sig`), and the cry's source is her own "Mama?" found by tag in the timeline (`voicesynth.line_span`;
  the fixed 435.32-435.95 s had moved onto silence and the girl's broken song failed to render).
- **Cues (M9, M10, m4-m10, fixers A-C)**: Grandma's 2-3-2 lands on the knuckle insert (7 knocks, checked in the cue
  sheet); the stairs are the picture's 0.95 s treads with the thunk 0.3 s after (the plan's own 0.8/s treads that
  doubled them are gone); the attic door creaks on the cut into the attic (not over the shut door); no mug_set_down over
  the untouched mug; the curtains +0.25 s and the slot flap +0.2 s onto their eased motion; the "And it hums." stinger
  moved to "My own face looks down at me." (it covered the hum); the riser before "He lifts one paw" ends 0.1 s before
  the word; the quiet identity returns up 4-5 dB (Mr. Otter, Grandma's music box, Mary Had a Little Lamb: level 0.3 ->
  0.85), Mom humming upstairs +5 dB, the girl's crying +6 dB; the trick's `magic_sparkle` has a recipe (a toy-chime
  twinkle in D, on the tape) and plays (it was dropped as "a cartoon" before the picture drew a trick); the
  next-episode phone rings on the picture's cadence (1.2 s on, 0.8 s off, `phone_ring(cycle=, on=)`) for the whole card;
  `footsteps_gravel` maps to grass steps.
- **The rebuild**: narration (`vo_edit.py build`, `align.py --write-pauses`, `vo_edit.py check` with the asr check,
  `vo_report.py`), `tools/validate.py` (ERROR 0, WARN 4: #205, #294 the Courier photo's keyed push on line 323, #321,
  #392; INFO 3 masked lines), `--lipcheck` (273 actor-shots, the 3 masked lines), the preview (`W/preview/preview.mp4`,
  1085.93 s, 32,578 frames; worker 0 died on the skia crash above and its half was re-rendered as two quarter slices
  and joined frame-exact), `audio/final_mix.sh` (cue sheets, mix, measure, scene sheets, `preview_mix.mp4`; 18.4 min).
- **Measured** (`W/mix/final/measure.txt`, plus fixer D's own table: loudness K-weighted, 400 ms):

  | | before (critic 3) | now |
  |---|---|---|
  | integrated / true peak / LRA | -14.05 LUFS / -1.67 dBTP / 3.2 | -14.04 LUFS / -1.70 dBTP / 2.7 |
  | the film's loudest 400 ms | narrated lines, +5.1 to +5.4 LU over the mix | the fight (673.85 s), +4.2; the narration's loudest +3.1 to +3.2 |
  | boosted scares (window, back door, GET OUT, IT'S MY HOUSE, crack, face reveal, swap, Seven, doorway, Back to bed) | +0.5 to +4.3 (most under +3) | +3.0 to +4.3, median +4.0 (over every narrated line) |
  | the bed in the gaps by rule (LU rel the voice) | flat (critic's own measure: -15.4 / -19.2 / -17.3 / -14.2 / -15.1 / -14.9) | -20.1 / -19.1 / -17.5 / -16.0 / -15.1 / -12.8, then rule 7's false relief -16.7 |
  | voice minus bed while speaking | p1 6.5 LU, under 6 LU 0.62 % | p1 6.3 LU, under 6 LU 0.97 % (the boosted scares ride over their words: 8 weak spots, all at those scares; in the 1-4 kHz band the words keep a median of +9 to +53 dB, single 100 ms frames dip to -4 .. -8 dB at "explodes", GET OUT, the crack, "IT'S MY HOUSE!") |
  | quiet returns (bed in their gaps) | Mr. Otter -23, music box -18, Mary -20, Mom upstairs -18, the crying -17 | -20.5, -16.6, -15.2, -12.0, -11.0 |
  | the girl's "Please." | 6.9 dB under the narration | 1.9 LU under the lines around it |
  | the voice edit vs the recogniser | 11 lines wrong (cut words) | 0 (3 whole-file chunking misses read right on their own) |

  The target the critic gave for the hardest scare (+8 to +10 LU momentary) is not reached: the score's hits are short
  and the spare windows end at the next word; a louder scare needs denser hit material (a sustained impact layer), not
  more gain (the master limiter already takes 1 dB or more on 4.1 % of the film, was 1.5 %).
- **Not done**: the girl's crying is not matched to the Bunnyman's visible sob catches (`SOB_T`, #189/#190; the cry is
  a synthesised phrase with its own timing); the four TTS re-takes (below) need the owner.

## Verify round 1 (picture)
Every picture blocker and major of critics 1 and 2 was checked on the new preview (strips across the cuts, stills, 52 full-size
2560x1440 stills of the wide shots from `render.py --stills`) and the whole preview was scanned at 1 fps. Two staging errors
were fixed with camera-only changes (no cue moved: `film.py --cues --out <scratch>` is byte-identical to `W/cues`):
- **#177 "with Mom in the armchair facing the back door"** (504.4 s): from straight on, the back-door wide showed her legs running
  straight down through the seat (the owner's "standing on the couch" error). A longer lens from the same back door
  (`cm((-3.3, 6.55, 1.2), (-3.3, 4.4, 0.95), S=1850, sy=660)`) frames her from the lap up between the chair's arms, the kids
  asleep behind her.
- **#223 "Footsteps on the stairs. Slow."** (615.7 s): the view's own camera at f 1.6 cropped the flight out of frame, so he read
  as standing still in the downstairs hall. Down the flight from the landing (`cm((0.82, 4.45, 4.0), (0.8, 1.45, 0.9), S=900,
  sy=760)`, f 1.0): the carpeted treads, the rail and the front door below him; each tread now reads as a step up.
The two ranges (504-508 s, 615-619 s) were re-rendered at 640x360/30 and spliced frame-exact into `W/preview/preview.mp4`;
`preview_mix.mp4` carries the existing mix's AAC stream unchanged (stream copy, same MD5). Still open: see Open problems
("Verify round 1 leftovers").

## Open problems
- **Verify round 1 leftovers (picture)**: (1) **the cop shot #351 (939.6-944.0 s)**: the dead man at the foot of the stairs is the
  front-view figure turned 90 degrees, so at full size it floats at waist height as a flat cutout behind the balusters, the
  spindles drawn over his face, one arm hanging to the floor (a camera from the landing does not save it: it then lies across
  the lower treads). It needs a real lying drawing in the set (the `ins_body_above` art projected onto the floor plane, or a
  low side-view lying pose), or the beat restaged with the cop over the `body_above` insert (that moves the cop's footstep cues,
  so it needs the sound step). (2) The porch slot shots (#158, #167, #171): the outer slot plate is hidden behind his body in
  every frame, and in #158 the paw sits at the lock plate with its pads to the camera. (3) Smaller: the bathroom door's own
  jolt on "shakes"/"slams" is subtle in the dark grade; Mom's open grin on "That's how he knocks, every year." still reads
  cheerful; the couch blanket in #176 hangs as a flat sheet; in the outro `egg_empty` the lid half sits high on the desk.
- **Lying figures in a set view** (`pose.lie`) are still the front view turned 90 degrees, so they only read from straight
  above: the lying beats are custom top-down inserts (`ins_body_above`, `ins_under_bridge`); the set view of the body from the
  top of the stairs is kept short (2.4 s) as the establishing shot.
- **Kneeling kids seen from behind** read as standing: June at the mail slot is shot from the side and in profile close-ups.
- **The masked Bunnyman's lines have no mouth** (by design): `tools/validate.py` lists those three shots as allowed (INFO).
- **The `porch_egg` camera's own `env`** (y 180-300) excludes the frame centre, so `scam()` falls back to (490, 590) for it.
- **Keyed insert moves** that run a little over 4 s on purpose (the push down the peephole to the egg, the move across the diary's last page) and two outro holds are WARNs in the validator, checked by eye.
- **Fixer B leftovers**: June at the slot close (#173, "Mom closes the mail slot") is drawn nearly frontal although she faces
  the door (the kneel pose's turn). (The armchair shot #177 is reframed since verify round 1; `magic_sparkle` has a recipe since fixer D.)
- **Fixer C leftovers**: the lying body in the set view at the foot of the stairs is still the front-view figure turned 90 degrees
  (the cop shot reads, the top-down inserts carry the beat); Dale's hair has no wet, matted sheen; the whisper has no wide set
  shot of the lap (the climb into frame carries it); the bathroom door's slam jolt is small at preview size (the dust, the light
  blotted out and the camera hit carry it); the hatchet-steps insert is still a side cutaway (now through the banister).
- **Sound** (the final mix is done and measured; nobody has listened to it): the riskiest by ear are the synthetic jingle timbres (toy piano, music box, the hums, the girl's singing and crying, the girl's new x1.24 voice), the narration's loudness cap (whole-word cuts of up to 1.3 dB on about 1 % of the blocks) and the boosted scares riding over their own words ("explodes", GET OUT, the crack, "Seven.": listen that each word still reads). The hardest scare is +4.3 LU, not the +8-10 the critic asked (see the fixer D table). The bed in the gaps rises rule by rule (-20 .. -13 LU); the integrated bed of rule 1 is still high (-12.5: the dying speaker's jingle carries the scene).
- **Narration re-takes** (from the voice report, still open): "Sleep well.", "At 11:07, the song starts." and "If he knocks, don't answer." are repaired splices (they read right); Mom's "And count to seven." now ends at the decay of its n and reads right too. A fresh TTS take of these would still be safer, and only the owner can make one.
