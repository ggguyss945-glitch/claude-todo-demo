// lipsync.js — viseme tracks for engine v3.
// A voice line carries words [{w, t0, t1}] and (ideally) visemes [[t, name], ...], both in seconds from the line start.
// Viseme names: the face.js mouths 'v_closed' 'v_small' 'v_E' 'v_A' 'v_O', or the short forms 'closed' 'small' 'E' 'A' 'O'
// (also 'X'/'rest'/null = no viseme: the face falls back to its expression mouth). When a line has words but no
// visemes, autoVisemes() makes a plausible track from the spelling: one open shape per syllable (vowel letters pick
// A / E / O), closed lips on m/b/p onsets, 'small' between syllables, every shape held 3-8 frames (bible 3.2).
import { FPS, clamp } from './motion.js';

const NAMES = { closed: 'v_closed', small: 'v_small', e: 'v_E', a: 'v_A', o: 'v_O', mbp: 'v_closed', ee: 'v_E', ah: 'v_A', oo: 'v_O', u: 'v_O', i: 'v_E' };
/** normalise a viseme name to a face.js mouth name, or null for rest */
export function visemeName(v) {
  if (v === null || v === undefined || v === false) return null;
  const s = String(v);
  if (/^v_/.test(s)) return s;
  const k = s.toLowerCase();
  if (k === 'x' || k === 'rest' || k === 'sil' || k === '' || k === 'none') return null;
  return NAMES[k] || null;
}

/** normalise words from any of {w,t0,t1} | {w,t,d} (audio/voice_lines.json: start + duration) | {w,t,e} |
 *  {word,start,end} | [w, t0, t1] */
export function normWords(words = [], offset = 0) {
  return words.map((x) => {
    if (Array.isArray(x)) return { w: String(x[0]), t0: +x[1] - offset, t1: +(x[2] ?? x[1] + 0.25) - offset };
    const w = x.w ?? x.word ?? x.text ?? '';
    const t0 = +(x.t0 ?? x.t ?? x.start ?? 0);
    const t1 = +(x.t1 ?? x.e ?? x.end ?? (x.d !== undefined ? t0 + +x.d : t0 + 0.25));
    return { w: String(w), t0: t0 - offset, t1: t1 - offset };
  }).filter((x) => Number.isFinite(x.t0)).sort((a, b) => a.t0 - b.t0);
}
export function normVisemes(vis = [], offset = 0) {
  return vis.map((k) => (Array.isArray(k) ? [+k[0] - offset, visemeName(k[1])] : [+(k.t ?? k.t0) - offset, visemeName(k.v ?? k.name ?? k.viseme)]))
    .filter((k) => Number.isFinite(k[0])).sort((a, b) => a[0] - b[0]);
}

// ---------- auto visemes from spelling ----------
const VOWEL = /[aeiouy]+/gi;
function syllables(word) {
  const w = word.toLowerCase().replace(/[^a-z']/g, '');
  if (!w) return [];
  const out = [];
  let m; VOWEL.lastIndex = 0;
  while ((m = VOWEL.exec(w))) out.push({ v: m[0], i: m.index, onset: w.slice(Math.max(0, m.index - 1), m.index) });
  // silent final e ("made", "line") merges into the previous syllable
  if (out.length > 1 && /e$/.test(w) && out[out.length - 1].v === 'e' && out[out.length - 1].i === w.length - 1) out.pop();
  if (!out.length) out.push({ v: 'u', i: 0, onset: w[0] });     // "hmm", "shh", numbers spelled oddly
  return out;
}
function vowelShape(v, onset) {
  const s = v.toLowerCase();
  if (/^o|^u|ou|oo|ow|aw/.test(s)) return 'v_O';
  if (/^a|ai|au/.test(s)) return 'v_A';
  if (/^e|^i|^y|ee|ea|ie/.test(s)) return /w/.test(onset || '') ? 'v_O' : 'v_E';
  return 'v_A';
}
/** words [{w, t0, t1}] (any time base) -> viseme keys [[t, name|null]] in the same time base */
export function autoVisemes(words = [], o = {}) {
  const fps = o.fps ?? FPS, minHold = (o.minFrames ?? 3) / fps;
  const raw = [];
  for (const wd of words) {
    const syl = syllables(wd.w), d = Math.max(minHold, wd.t1 - wd.t0);
    const n = Math.max(1, Math.min(syl.length, Math.floor(d / (minHold * 2)) || 1));
    const step = d / n;
    for (let k = 0; k < n; k++) {
      const sy = syl[Math.min(syl.length - 1, Math.round((k * (syl.length - 1)) / Math.max(1, n - 1)))];
      const t = wd.t0 + k * step;
      const lips = /[mbp]/.test(sy.onset || '');
      if (lips && step > minHold * 2.2) { raw.push([t, 'v_closed']); raw.push([t + minHold, vowelShape(sy.v, sy.onset)]); }
      else raw.push([t, vowelShape(sy.v, sy.onset)]);
      // a short 'small' release before the next syllable when there is room
      if (step > minHold * 3) raw.push([t + step - minHold, 'v_small']);
    }
    raw.push([wd.t1, null]);
  }
  raw.sort((a, b) => a[0] - b[0]);
  // enforce the minimum hold: drop keys that come too soon after the previous one (keep rests that close a gap)
  const out = [];
  for (const k of raw) {
    const last = out[out.length - 1];
    if (last && k[0] - last[0] < minHold) {
      if (k[1] === null) continue;          // the word continues: keep the open shape
      last[1] = k[1]; continue;
    }
    if (last && last[1] === k[1]) continue;
    out.push([k[0], k[1]]);
  }
  return out;
}

/** viseme at time t from keys [[t, name|null]]: the last key <= t; null before the first key or after o.until */
export function visemeAt(keys, t, o = {}) {
  if (!keys || !keys.length || t < keys[0][0]) return null;
  if (o.until !== undefined && t > o.until) return null;
  let lo = 0, hi = keys.length - 1;
  if (t >= keys[hi][0]) return keys[hi][1];
  while (hi - lo > 1) { const m = (lo + hi) >> 1; if (keys[m][0] <= t) lo = m; else hi = m; }
  return keys[lo][1];
}
/** is t inside a word window (with a little tail so the last shape can close) */
export function inWord(words, t, tail = 0.04) {
  for (const w of words) { if (t >= w.t0 - 0.01 && t <= w.t1 + tail) return w; if (w.t0 > t) break; }
  return null;
}
/** mouth openness 0..1 for a viseme (for jaw bob / head nod accents) */
export const openness = (v) => ({ v_closed: 0, v_small: 0.35, v_E: 0.6, v_O: 0.75, v_A: 1 }[v] ?? 0);
export { clamp };
