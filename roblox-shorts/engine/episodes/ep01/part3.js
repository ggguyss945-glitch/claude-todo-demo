// EP01 full episode, PART 3 (s42-s57, 46.30-65.43 s): the reframe and the attempt: "Gnomes aren't decorations / They're the fence", Theo, the what-if, the truck clock, the plastic gnome, GULP, the mounds close in, the hero runs back and stands guard.
// Shot list and every decision (camera numbers, cast and faces, light/grade, events with frames, SFX, assets) are in
// episodes/ep01/timeline.json (params of each shot) and episodes/ep01/board.md; new assets are specified in episodes/ep01/ASSETS.md.
//
// This part owns these builder keys (timeline.json parts[2].builders_owned); index.js renders a labelled placeholder for
// each key that is not in `builders` yet, so the whole episode always renders end to end:
//   balcony_box, eyes_fog_glass, fence_aerial, gnome_waiting, gulp, lit_gnome_cu, mounds_bricks, mounds_closer, mounds_flowers, plant_plastic, ran_back, stand_guard, take_window_dark, theo_intro, theo_window_out, truck_clock
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

export const PART = 3;
export const builders = {
  // key: { build(ctx) { ... }, update(ctx, t) { ... } },
};
// Keep the imports referenced until the first builder lands (they are the part's toolkit).
export const _toolkit = { THREE, sets, K, C };
