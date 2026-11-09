// EP01 full episode, PART 5 (s77-s97, 86.77-113.30 s): FWOOM to the end: the flare, the light rolling, the mounds sinking, the eyes winking out, the quiet wide, dawn with Theo, the truck leaving, the photos, the narrator at 71, the loop shot.
// Shot list and every decision (camera numbers, cast and faces, light/grade, events with frames, SFX, assets) are in
// episodes/ep01/timeline.json (params of each shot) and episodes/ep01/board.md; new assets are specified in episodes/ep01/ASSETS.md.
//
// This part owns these builder keys (timeline.json parts[4].builders_owned); index.js renders a labelled placeholder for
// each key that is not in `builders` yet, so the whole episode always renders end to end:
//   bench_granddaughter, dawn_theo_out, eyes_wink_out, final_window, fwoom_flare, grandpa_turned, hero_nicest, light_rolls, mounds_sink, nudge_theo, old_reveal, phone_reveal, phone_swipes, photo_midblink, polaroid_stack, quiet_wide, theo_asks, theo_blink_twoshot, theo_o, truck_pov
//
// Contract for every builder (engine/README.md): { build(ctx), update(ctx, t), quality? }; `ctx.params` = the shot's params;
// update must be a pure function of t (no accumulated state, no Math.random / Date); use ctx.rng / ctx.rngFor and ctx.cache.
// Event times: C.evT(ctx, 'word' | index) -> seconds from the shot start. The approved look helpers are in ./common.js
// (SPARK, GALAXY, GALAXY_LOW, starGlint, gazeAt, softenBeard, gradeBlend, defaultMove); the approved test code is in ./part1.js.
// Add `quality: { shadows: 'pcfsoft' }` to builders that use a shadowed sun (dawn / dusk / day presets).
import * as THREE from 'three';
import * as sets from '../../kit/sets.js';
import * as K from '../../kit/chars.js';
import * as C from './common.js';

export const PART = 5;
export const builders = {
  // key: { build(ctx) { ... }, update(ctx, t) { ... } },
};
// Keep the imports referenced until the first builder lands (they are the part's toolkit).
export const _toolkit = { THREE, sets, K, C };
