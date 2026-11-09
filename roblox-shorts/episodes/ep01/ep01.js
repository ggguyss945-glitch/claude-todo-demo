// Timeline entry point for the EP01 full episode (timeline.json "episode"): re-exports the routed builder map of
// engine/episodes/ep01/index.js keyed by the timeline's `shot` names, so
//   node tools/render.js episodes/ep01/timeline.json <out> quality=final workers=3
// renders the same frames as rendering engine/episodes/ep01/index.js directly.
import ep, { builders } from '../../engine/episodes/ep01/index.js';
export default { ...ep, shots: builders };
