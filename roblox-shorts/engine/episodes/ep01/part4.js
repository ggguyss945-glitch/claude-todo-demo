// EP01 full episode, PART 4 (s58-s76, 65.43-86.77 s): twist 2 and the choice: "And tomorrow night?", the head turn, the callback (s61-s63 use part1's fb_* builders), the flashbacks (sepia, B&W), the decades at the window, the slow blink, letting go.
// Shot list and every decision (camera numbers, cast and faces, light/grade, events with frames, SFX, assets) are in
// episodes/ep01/timeline.json (params of each shot) and episodes/ep01/board.md; new assets are specified in episodes/ep01/ASSETS.md.
//
// This part owns these builder keys (timeline.json parts[3].builders_owned); index.js renders a labelled placeholder for
// each key that is not in `builders` yet, so the whole episode always renders end to end:
//   away_to_window, big_in_window, bw_dad, decades_window, fb_checking_me, fb_one_stop, head_grind, hero_goodnight, hero_wet_eyes, knelt_bed, lawn_stare_lit, set_down_let_go, slow_blink, theo_lantern_cheek, tomorrow_night
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

export const PART = 4;
export const builders = {
  // key: { build(ctx) { ... }, update(ctx, t) { ... } },
};
// Keep the imports referenced until the first builder lands (they are the part's toolkit).
export const _toolkit = { THREE, sets, K, C };
