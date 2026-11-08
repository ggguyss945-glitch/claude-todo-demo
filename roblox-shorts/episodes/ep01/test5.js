// Timeline entry point for the EP01 5-second test (test5_timeline.json "episode"): re-exports the builder map of
// engine/episodes/ep01_test5.js keyed by the timeline's `shot` names, so
//   node tools/render.js episodes/ep01/test5_timeline.json <out.mp4> quality=final workers=3
// renders the same frames as rendering engine/episodes/ep01_test5.js directly.
import ep, { builders } from '../../engine/episodes/ep01_test5.js';
export default { ...ep, shots: builders };
