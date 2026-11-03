// bake.js — static-layer baking (bible 3.3 "Baking"). A static layer (a set's sky/far/mid/near: anything that does
// not change during the shot) can be drawn as one bitmap instead of thousands of vector paths. Page side:
//   layer(key, make, box, res)  -> svg: the first time a key is seen it is drawn inline (make()) and queued as a bake
//                                  job; once the renderer hands back a PNG url, the layer is an <image> from then on.
//   box  = world rect {x, y, w, h} the bitmap covers; res = pixels per world unit (render scale x max camera zoom).
// The renderer (tools/render.js) rasterises jobs once in engine/bake.html, caches them by content hash in its work dir
// and calls window.bakeDone(key, url) on every worker (each worker pre-decodes the image before using it).
// Without the renderer (still previews, node tests) layer() just returns make() - baking never changes the design.
let BAKER = null;
export function setBaker(fn) { BAKER = fn; }
export function hasBaker() { return !!BAKER; }
export function layer(key, make, box, res = 1) { return BAKER ? BAKER(key, make, box, res) : make(); }

const MAX_PX = 8192;            // Chromium canvas / texture cap per side
/** install the page-side baker (anim.html calls this unless ?bake=0) */
export function installBaker(opts = {}) {
  const urls = new Map(), asked = new Set(), jobs = [], ready = new Set();
  const scale = opts.scale ?? 1;
  setBaker((key, make, box, res = 1) => {
    const px = res * scale;
    const big = box.w * px > MAX_PX || box.h * px > MAX_PX;
    const k = `${key}@${Math.round(px * 100)}`;
    const u = urls.get(k);
    if (u && ready.has(k)) return `<image href="${u}" x="${box.x}" y="${box.y}" width="${box.w}" height="${box.h}" preserveAspectRatio="none"/>`;
    const svg = make();
    if (!big && !asked.has(k)) { asked.add(k); jobs.push({ key: k, box, px, svg }); }
    return svg;
  });
  window.takeBakeJobs = () => jobs.splice(0);
  // decode before first use so a frame never shows a half-loaded bitmap
  window.bakeDone = async (key, url) => {
    urls.set(key, url);
    const img = new Image(); img.src = url;
    try { await img.decode(); } catch (e) { /* fall back to inline */ return false; }
    (window.__bakeImgs ||= []).push(img);          // keep decoded bitmaps alive
    ready.add(key);
    return true;
  };
}
