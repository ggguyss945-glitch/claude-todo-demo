// Page side of layer baking: the first time a layer is drawn it goes out inline and is queued for the
// renderer, which rasterizes it once and hands back a bitmap URL used for every later frame.
import { setBaker, defs } from './lib.js';

export function installBaker() {
  const urls = new Map(), asked = new Set(), jobs = [];
  setBaker((key, make, box) => {
    const u = urls.get(key);
    if (u) return `<image href="${u}" x="${box.x}" y="${box.y}" width="${box.w}" height="${box.h}" preserveAspectRatio="none"/>`;
    const svg = make();
    if (!asked.has(key)) { asked.add(key); jobs.push({ key, box, svg }); }
    return svg;
  });
  window.takeBakeJobs = () => jobs.splice(0);
  window.bakeDone = (key, url) => { urls.set(key, url); };
  window.bakeDefs = defs(5, 7);
}
