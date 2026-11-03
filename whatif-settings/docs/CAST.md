# What If Real Life Had a SETTINGS MENU? — cast (design brief)

Look: the reference's clean "toy plastic" 2D vector finish (see ../zombie-series/whatif/production_bible.md §1.6, §3.1, §3.2),
but our own original designs. Chibi build about 3.1 heads tall, rounded-square heads, rigid body parts that act through
pose snaps, faces that change every 0.5–2 s. No Roblox studs, logos or likenesses; no iOS/Android UI likeness.

| Id | Who | Look | Personality / acting | Voice (Fish Audio) |
|---|---|---|---|---|
| SAM | The kid, 12 — the viewer's "you". Others call him Sam. | Orange hoodie (#FF7A3D→#E4572A) with a white **gear** logo, our channel's **orange over-ear headphones** round his neck, messy chestnut hair with one cowlick, cool-cream skin, dark jeans, white sneakers | Curious, impulsive, a little guilty; big reactions, star eyes when he discovers a setting, sweat drops when it goes wrong | Real boy, 11-13, natural, quick |
| LILY | Little sister, 6 | Pink overalls over a yellow tee, two springy pigtail puffs, gap tooth, freckles | LOUD. Screams at everything. Muted on Day 1, her scream saves the world on Day 7 | Real girl, 6-8, shrill when loud |
| MOM | Mom | Purple cardigan (#9B6CF0), bouncy ponytail, glasses pushed up on her head, a label maker in her pocket | Organized, in control, secretly delighted by Parental Controls | Bright, warm, firm |
| DAD | Dad | Blue polo (#4A90E2), side-hair with a shiny bald top, thick moustache, mug "WORLD'S BEST-ISH DAD" | Dad jokes, deadpan, flips to falsetto panic | Deadpan baritone → falsetto |
| PICKLES | The family cat | Grey, round, permanently half-lidded judging eyes, tiny white socks | Silent all week; on Day 4 (Language: Cat) speaks like a bored aristocrat | Deep, slow, posh, bored |
| BRIGGS | Mr. Briggs, the teacher | Mustard sweater vest, bow tie, round glasses, comb-over | Long-winded; becomes a chipmunk on 2x speed | Older man, monotone (we speed him up) |
| KEVIN | Kevin next door | Tall, sunglasses always on, white tank top, lawn-obsessed, holds a leaf blower | Smug; secretly has the app too (Day 6) | Smug, nasal |
| TINY | Kevin's dog (the cold open: Sam drags DOG SIZE and Tiny grows to the size of a house) | Caramel puppy (#EFA75F), cream muzzle / bib / paws / tail tip, chocolate floppy ears, a patch over one eye, a spiky top tuft, red collar with a gold bone tag reading TINY | Happy, excitable, tongue out; ears spring up on shock; tail never stops | No voice (barks are SFX) |
| SYSTEM | The settings assistant (voice + UI) | Appears as the app: a glowing gear, panels, toasts | Polite, calm, slightly too cheerful; never panics | Calm neutral/female, clean; we add the UI chime and filter |
| N | Narrator | — | Second person ("you"); two registers: HYPE and DEADPAN | Young adult male, energetic storyteller with good deadpan |

## Using the cast in shots (engine/cast.js)

`toon(id, o)` returns SVG markup; ids: `sam lily mom dad pickles briggs kevin tiny`. The old API is unchanged
(`{x, y, s, facing, pose, face, look, add, props, shadow}`); every existing sheet renders pixel-identical. New options:

| Option | What it does |
|---|---|
| `outfit: 'pyjamas'` | Dad in soft blue striped pyjamas with navy piping and slippers (hair and moustache kept, no mug). |
| `mannequin: 0..1` or `variant: 'default'` | Day 7 factory reset: smooth light-grey plastic, blank moulded face; hair, ponytail, glasses and moustache stay as grey shapes. The silhouette never changes, so a shot can flicker 0 / 1 per frame. Features fade out by 0.75, the blank face fades in from 0.35. |
| `tint: {color, k, mode}` | Grade a character into the scene, with no blend modes. `mode`: `'multiply'` (night: `{color: '#5562A4', k: 0.55}`), `'screen'` (blow-out: `{color: '#FFF3DC', k: 0.16}`) or `'mix'`. By default, light colours screen and darker ones multiply. |
| `light: {color, k, from, r}` | A light pool masked to the character (outlines get a little light and ink none, so eyes stay crisp). `from`: `'phone'` (pool between the held phone and the face: the 2:13 a.m. look), `'below'`, `'left'`, `'right'`, `'above'`, `'front'` or `[x, y]` in body units. It costs about one extra build (≈1 ms). |
| `legs: false` | Waist up, no legs and no contact shadow, for sitting in bed. Place the figure with `y = hipLine - toonHipY(id) * s`. The set draws the blanket over him. |
| `lod` (dog) | Detail level, which defaults to `s`: from 1.8 the tag reads TINY, from 2.5 fur tufts appear. Pass `lod` when a camera zoom makes a small `s` big on screen. |

All of these can also go inside `add:{}` (for example `add: {mannequin: 1}`), which is how `anim/actor.js` passes them today.

**Faces.** `face: {preset, mouth: 'v_A'}` puts any viseme (`v_closed v_small v_E v_A v_O`) on top of any expression:
the eyes, brows and add-ons come from the preset, and the preset's mouth scale and offsets are dropped. Visemes stay readable in profile.
`face: {preset: 'starstruck', to: 'scared', k}` is a clean shrink-swap-grow morph (k 0..1; brows and look glide, no double eyes),
and it lip-syncs too. New presets: `squint` (seriously reading), `ish` (guilty half-lid grimace), `forcedGrin`, `shout`, `blank`.
Sweat: `add: {sweat: 1, sweatK: 0..1, sweatSize}` slides the drop 20 units down and grows it ×1.4 (animate `sweatK`; pop `sweatSize` 0 → 1.2 → 1).

**Poses.** `posePreset(name, id, o)` gives a pose object: `shrug` (`o.k` scales it; it uses the new `pose.shrug` shoulder raise), `shieldEyes`
(visor hand over the brow, R hand by default, `o.side: 'L'`), `phoneUp` / `phoneChest` / `phoneLap` (tween them to lower the phone slowly;
use `props: {R: 'phoneBack'}`, which shows the case side with a screen-glow rim), `bedSit`, `yawnStretch`, `yawnCover`, `pointUp` ("ONE thing").
`reach(id, 'L'|'R', [x, y], {facing, elbow})` is two-bone arm IK in body units, and `headPoint(id, [hx, hy])` converts head units to body units for it.

**TINY.** `toon('tiny', {posture: 'sit'|'stand', facing: 'front'|'left'|'right'|'side-left'|'side-right', face, pose})`.
Pose keys: `wag` (-1..1, so `wag(t, hz)` from cast.js gives a wagging tail), `tail` (degrees), `ears` / `earL` / `earR` (0 hangs, about 120 springs up),
`flop`, `tongue` (0..1.5), `head` (tilt), `headTurn`, `pawL` / `pawR` (raise), `legFL legFR legHL legHR` (standing swing), `lean`, `bob`.
Faces: any preset. `neutral happy excited shocked confused sad love sleepy guilty` have dog versions (panting tongue, muzzle mouths),
and `shocked` / `excited` / `confused` set the ears and head tilt unless the pose overrides them. Size: to read as a small dog next to a person, use about 0.8 × the person's `s`. It holds up from `s` 0.5 to 6.

**Speed** (node, warm, one call with `resetDefs`): humans 0.3-0.9 ms, Pickles 0.13 ms, Tiny 0.2 ms, a mannequin 0.6 ms, Sam night-lit 1.1 ms.
The first call ever is about 9 ms (JIT warm-up).

QA sheets: `sheets/hook_cast.js` (renders/hook_cast.png) and `sheets/hook_visemes.js` (all humans × visemes × three facings).
