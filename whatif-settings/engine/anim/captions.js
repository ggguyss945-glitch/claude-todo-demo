// captions.js — word-timed caption track for engine v3 (bible 1.9, 3.6), drawn above everything by frame.js.
// Timeline entries: T.captions = [{t0, t1, markup, mode?, y?, size?, cps?, x?}] in global seconds, where
//   markup  caption.js markup: 'Gravity: {MOON|cyan}' ({WORD|colour} keywords; colours yellow red green pink orange cyan purple)
//   mode    'normal' (default) | 'type' (typewriter + block cursor, for SYS/UI text; cps chars per second, default 30)
//           | 'scream' (shakes +-3 deg every frame) | 'quote' (curly quotes for in-world dialogue; quote: 'open' |
//           'close' | 'both' (default) | 'none' says which side of a multi-chunk line this chunk carries)
//   y       number (px) or 'mid' (72% H, default) | 'face' (86%) | 'pov' (92%); a shot can set its default with
//           capY in the timeline (shot.capY) and the caption's own y wins.
// Pop-in: plain chunks 0.6 -> 1.05 -> 1 over 3 frames, keyword chunks 0.85 -> 1.16 -> 1 over 6 frames (caption.js).
// captionsFromLine() builds entries from a voice line's word times: 1-3 word chunks (caption.chunk), each shown
// `lead` frames (default 3) before its first word and held until the next chunk (or the line end + tail).
import { caption, chunk, CAP_Y } from '../caption.js';
import { FPS, clamp } from './motion.js';

const POPF = { plain: 3, kw: 6 };
const norm = (s) => String(s).toLowerCase().replace(/\{([^|}]+)(\|[^}]+)?\}/g, '$1').replace(/[^a-z0-9']/g, '');

/** draw the caption(s) active at global time gt. capY: default y from the shot. */
export function drawCaptions(list, gt, o = {}) {
  const fps = o.fps ?? FPS;
  let out = '';
  for (const c of list || []) {
    if (gt < c.t0 || gt >= c.t1) continue;
    const kw = /\{/.test(c.markup);
    const n = c.popFrames ?? (kw ? POPF.kw : POPF.plain);
    const p = clamp(((gt - c.t0) * fps) / n);
    const yv = c.y ?? o.capY ?? 'mid';
    const y = typeof yv === 'number' ? yv : CAP_Y[yv] ?? CAP_Y.mid;
    let markup = c.markup;
    if (c.mode === 'quote') { const q = c.quote || 'both'; markup = `${q === 'both' || q === 'open' ? '“' : ''}${markup}${q === 'both' || q === 'close' ? '”' : ''}`; }
    const mode = c.mode === 'quote' ? 'normal' : c.mode || 'normal';
    const opts = { y, x: c.x, size: c.size, mode, t: gt - c.t0, ring: c.ring };
    if (mode === 'type') opts.chars = (gt - c.t0) * (c.cps ?? 30);
    if (mode === 'scream') opts.t = gt;
    out += caption(markup, opts, mode === 'type' ? 1 : p);
  }
  return out;
}

/** build caption entries from one voice line. line: {start, words:[{w, t0, t1}] (relative to start), dur}
 *  markupText: the script text with {KEYWORD|colour} markup (optional; plain words are used otherwise).
 *  o: {lead frames = 3, tail s = 0.25, maxWords = 3, mode, y, fps, until (global s: no chunk outlives it, e.g. the
 *  cut into a shot where nobody says it)} */
export function captionsFromLine(line, markupText, o = {}) {
  const fps = o.fps ?? FPS, lead = (o.lead ?? 3) / fps, tail = o.tail ?? 0.25;
  const words = line.words || [];
  if (!words.length) return [];
  const chunks = chunk(markupText || words.map((w) => w.w).join(' '), o.maxWords ?? 3);
  // walk the chunks over the word list by normalised spelling (falls back to word counts)
  const out = [];
  let wi = 0;
  for (const ch of chunks) {
    const toks = (ch.match(/\{[^}]+\}|\S+/g) || []).map(norm).filter(Boolean);
    let first = wi;
    if (toks.length) for (let k = wi; k < Math.min(words.length, wi + 4); k++) if (norm(words[k].w) === toks[0]) { first = k; break; }
    const last = Math.min(words.length - 1, first + Math.max(1, toks.length) - 1);
    out.push({ t0: line.start + words[Math.min(first, words.length - 1)].t0 - lead, markup: ch, wEnd: line.start + words[last].t1, mode: o.mode, y: o.y });
    wi = last + 1;
  }
  for (let i = 0; i < out.length; i++) {
    out[i].t1 = i + 1 < out.length ? out[i + 1].t0 : Math.max(out[i].wEnd + tail, line.start + (line.dur || 0));
    if (o.until !== undefined) out[i].t1 = Math.min(out[i].t1, Math.max(out[i].t0 + 2 / fps, o.until));
    delete out[i].wEnd;
    if (out[i].mode === 'quote') out[i].quote = out.length === 1 ? 'both' : i === 0 ? 'open' : i === out.length - 1 ? 'close' : 'none';
    if (out[i].mode === undefined) delete out[i].mode;
    if (out[i].y === undefined) delete out[i].y;
  }
  return out;
}
