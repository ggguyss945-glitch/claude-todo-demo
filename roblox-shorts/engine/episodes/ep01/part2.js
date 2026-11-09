// EP01 full episode, PART 2 (s25-s41, 26.55-46.30 s): twist 1 and the main reveal: the evening before the move, the empty spot, the gate, the pick-up, the lawn moves, the moles, the lantern lights, every lantern lit except next door.
// Shot list and every decision (camera numbers, cast and faces, light/grade, events with frames, SFX, assets) are in
// episodes/ep01/timeline.json (params of each shot) and episodes/ep01/board.md; new assets are specified in episodes/ep01/ASSETS.md.
//
// This part owns these builder keys (timeline.json parts[1].builders_owned); index.js renders a labelled placeholder for
// each key that is not in `builders` yet, so the whole episode always renders end to end:
//   empty_spot, gate_truck_thumb, gnome_tear, gold_arms, hall_clock, hero_arms_out, lantern_lights, lawn_moves, mounds_dozens, nextdoor_dark, pick_up, reflector_eyes, ring_edge, run_out_barefoot, snout_reveal, sold_truck_dusk, street_cascade
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

export const PART = 2;
export const builders = {
  // key: { build(ctx) { ... }, update(ctx, t) { ... } },
};
// Keep the imports referenced until the first builder lands (they are the part's toolkit).
export const _toolkit = { THREE, sets, K, C };
