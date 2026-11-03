// Captions (bible 1.9 / 3.6): 1-3 words, heavy rounded font (Nunito 900), white fill, dark stroke (~0.8% H visible),
// soft drop shadow, cap height ~6% H, centred at 72% H (86% when a face is in the way, 92% in POV device shots).
// Keywords in CAPS and colour-coded by meaning with {WORD|colour} markup, e.g. caption('Gravity: {MOON|cyan}').
// Pop-in: 0.6 -> 1.05 -> 1.0 over 3 frames (p 0..1); keyword chunks use the softer 6-frame 0.85 -> 1.16 -> 1 with a ring.
// Modes: 'normal', 'type' (typewriter + block cursor in the keyword colour, for system/UI text), 'scream' (shakes ±3°).
import { W, H, FONT, Defs, f, clamp, lerp, seg, ease, rng, esc, g, rect, circle, text, textW } from './ui_style.js';

export const KW = { yellow: '#FAD309', red: '#FF4A3D', green: '#45E05A', pink: '#F05BB5', orange: '#FF9A1F', cyan: '#33C8F5', purple: '#A96BFF', white: '#FFFFFF' };
/** what each colour means in this show, so editors pick consistently */
export const KW_MEANING = {
  yellow: 'world nouns, exclamations (REALITY, WORLD, WHAT?!)',
  red: 'danger, reset, countdown (FACTORY RESET, 60 SECONDS)',
  green: 'yes, success, applied (APPLIED, ON, YES)',
  pink: 'absurd and soft (Bouncy, Cat, chipmunk)',
  orange: 'actions and settings values (TAP, MOON, 2x)',
  cyan: 'UI and system words (SETTINGS, Gravity, Subtitles)',
  purple: 'glitch and developer stuff (BUG, PATCH, DEV MODE)',
};
export const CAP_Y = { mid: 0.72 * H, face: 0.86 * H, pov: 0.92 * H };
const STROKE = '#180C18';

function parse(s) {
  return String(s).split(/(\{[^}]+\})/).filter((x) => x !== '').map((part) => {
    const m = part.match(/^\{([^|}]+)(?:\|([^}]+))?\}$/);
    return m ? { t: m[1], c: KW[m[2]] || m[2] || KW.yellow, kw: true } : { t: part, c: '#FFFFFF', kw: false };
  });
}
const tspans = (segs) => segs.map((sg) => (sg.c === '#FFFFFF' ? esc(sg.t) : `<tspan fill="${sg.c}">${esc(sg.t)}</tspan>`)).join('');

/** caption(markup, { x, y, size, mode, chars, t, ring }, p) -> svg */
export function caption(markup, o = {}, p = 1) {
  const segs = parse(markup);
  const full = segs.map((s) => s.t).join('');
  const hasKw = segs.some((s) => s.kw);
  const x = o.x ?? W / 2, yc = o.y ?? CAP_Y.mid, mode = o.mode || 'normal';
  let size = o.size ?? 96; // Nunito cap height ~0.705 em -> ~68 px = 6.3% of H
  const tw = textW(full, size);
  const maxW = o.maxW ?? W * 0.86;
  if (tw > maxW) size *= maxW / tw;
  const w = textW(full, size), base = yc + size * 0.35;
  const sw = o.stroke ?? size * 0.19; // paint-order stroke: visible outline = sw/2 ≈ 0.85% H
  const d = new Defs();
  const shadow = d.shadow(5, 3, 0.5, '#0A0510');
  const attrs = { fontFamily: FONT.ui, fontWeight: 900, fontSize: f(size), fill: '#FFFFFF', stroke: STROKE, strokeWidth: f(sw), strokeLinejoin: 'round', paintOrder: 'stroke', filter: shadow };
  let body = '';
  if (mode === 'type') {
    // typewriter: left-anchored so the text does not slide as it types; block cursor in the keyword colour
    const n = Math.round(o.chars ?? full.length);
    let left = n, shown = [];
    for (const sg of segs) { if (left <= 0) break; shown.push({ ...sg, t: sg.t.slice(0, left) }); left -= sg.t.length; }
    const x0 = x - w / 2, sw2 = textW(shown.map((s) => s.t).join(''), size);
    const curCol = (segs.find((s) => s.kw) || { c: KW.yellow }).c;
    body = text(x0, base, tspans(shown), { ...attrs });
    const blink = o.t === undefined || Math.floor(o.t * 3.5) % 2 === 0 || n < full.length;
    if (blink) body += rect(x0 + sw2 + size * 0.06, base - size * 0.74, size * 0.42, size * 0.86, { fill: curCol, stroke: STROKE, strokeWidth: f(sw * 0.45), filter: shadow });
    return d + body;
  }
  body = text(x, base, tspans(segs), { ...attrs, textAnchor: 'middle' });
  // pop-in scale
  let s;
  if (hasKw && o.soft !== false) s = p >= 1 ? 1 : p < 0.5 ? lerp(0.85, 1.17, ease.outCubic(p / 0.5)) : lerp(1.17, 1, ease.inOutSine((p - 0.5) / 0.5));
  else s = p >= 1 ? 1 : p < 0.66 ? lerp(0.6, 1.05, ease.outCubic(p / 0.66)) : lerp(1.05, 1, (p - 0.66) / 0.34);
  let rot = 0, jx = 0, jy = 0;
  if (mode === 'scream') {
    const t = o.t || 0, R = rng(Math.floor(t * 60) + 1);
    rot = 3 * Math.sin(97 * t); jx = (R() - 0.5) * 8; jy = (R() - 0.5) * 8;
  }
  let ring = '';
  const rp = o.ringP ?? (hasKw ? p : -1);
  if (o.ring !== false && hasKw && rp > 0 && rp < 1) {
    const e = ease.outCubic(rp);
    ring = circle(x, yc, lerp(40, 160, e) * (size / 96), { fill: 'none', stroke: KW.yellow, strokeWidth: f(lerp(8, 1.5, e)), opacity: f((1 - rp) * 90) / 100 });
  }
  const op = p <= 0 ? 0 : 1;
  return d + ring + g(body, { transform: `translate(${f(x + jx)} ${f(yc + jy)}) rotate(${f(rot)}) scale(${f(s * 1000) / 1000}) translate(${f(-x)} ${f(-yc)})`, opacity: op });
}

/** split a line into 1-3 word chunks the way the reference does (break at punctuation and before keywords) */
export function chunk(line, maxWords = 3) {
  const words = String(line).match(/\{[^}]+\}|\S+/g) || [];
  const out = [];
  let cur = [];
  for (const w of words) {
    const kw = w.startsWith('{');
    if (cur.length && (cur.length >= maxWords || (kw && cur.length >= 1 && !cur[cur.length - 1].startsWith('{')))) { out.push(cur.join(' ')); cur = []; }
    cur.push(w);
    if (/[.,!?…:]$/.test(w.replace(/\|[^}]+\}$/, '').replace(/\}$/, ''))) { out.push(cur.join(' ')); cur = []; }
  }
  if (cur.length) out.push(cur.join(' '));
  return out;
}

// ---------- word-timed captions (bible 1.9 / 3.6) ----------
/** meaning dictionary for auto keyword colour (CAPS words in the script); unknown CAPS words default to yellow */
export const KW_DICT = {
  cyan: ['SETTINGS', 'SETTING', 'MENU', 'APP', 'PHONE', 'BRIGHTNESS', 'SLIDER', 'TOGGLE', 'GRAVITY', 'SUBTITLES', 'VOLUME', 'LANGUAGE', 'HISTORY', 'SCROLL'],
  red: ['UNDO', 'RESET', 'FACTORY', 'DANGER', 'NO', 'MINUTE', 'COUNTDOWN', 'DEFAULT', 'STOP'],
  green: ['AGREE', 'YES', 'ON', 'APPLIED', 'WELCOME', 'DONE'],
  pink: ['DOG', 'CAT', 'BOUNCY', 'TINY', 'CUTE'],
  orange: ['ONE', 'TAP', 'SLIDE', 'PRESS', 'DRAG', 'FLICK', 'UP', '412', 'TWO'],
  purple: ['GLITCH', 'BUG', 'PATCH', 'DEV'],
  yellow: ['REALITY', 'WORLD', 'SUN', 'PLANET', 'EARTH', 'MOON', 'REAL', 'LIFE', 'WHAT'],
};
const DICT = Object.fromEntries(Object.entries(KW_DICT).flatMap(([c, ws]) => ws.map((w) => [w, c])));
/** wrap ALL-CAPS words (2+ letters, not "I") of plain text in {WORD|colour} markup by meaning; existing markup is kept.
 *  extra = {WORD: colour} overrides for one line. */
export function autoKeywords(s, extra = {}) {
  return String(s).split(/(\{[^}]+\})/).map((part) => {
    if (part.startsWith('{')) return part;
    return part.replace(/\b[A-Z][A-Z0-9]+(?:'[A-Z]+)?\b/g, (m) => {
      const key = m.replace(/'S$/, '').replace(/'/g, '');
      return `{${m}|${extra[m] || extra[key] || DICT[key] || 'yellow'}}`;
    });
  }).join('');
}
const normTok = (s) => String(s).toLowerCase().replace(/\{([^|}]+)(\|[^}]+)?\}/g, '$1').replace(/[^a-z0-9']/g, '');
/** captionsFromWords(words, {maxWords = 3, lead = 3 frames, fps = 60, tail = 0.25 s, markup, auto = true, mode, minFrames = 4})
 *  -> [{t0, t1, markup, mode?}] in the words' time base. words: [{w, t0, t1}] (also {word, start, end}). markup: the
 *  line's script text with {KEYWORD|colour} markup (else the words joined, with CAPS words auto-coloured when auto).
 *  Chunks of 1-3 words break at punctuation and before keywords (chunk()); each shows `lead` frames before its first
 *  word and holds until the next chunk; the last holds to its word end + tail. A chunk shorter than minFrames merges
 *  into the next one so nothing flashes for a frame. mode 'type' entries get cps from the words' rate. */
export function captionsFromWords(words, o = {}) {
  const fps = o.fps ?? 60, lead = (o.lead ?? 3) / fps, tail = o.tail ?? 0.25, minDur = (o.minFrames ?? 4) / fps;
  const ws = (words || []).map((w) => ({ w: w.w ?? w.word ?? w.text, t0: w.t0 ?? w.start, t1: w.t1 ?? w.end })).filter((w) => w.w !== undefined && Number.isFinite(w.t0));
  if (!ws.length) return [];
  ws.forEach((w, i) => { if (!Number.isFinite(w.t1)) w.t1 = i + 1 < ws.length ? ws[i + 1].t0 : w.t0 + 0.3; });
  let src = o.markup ?? ws.map((w) => w.w).join(' ');
  if (o.auto !== false && !/\{/.test(src)) src = autoKeywords(src);
  const chunks = chunk(src, o.maxWords ?? 3);
  const out = [];
  let wi = 0;
  for (const ch of chunks) {
    const toks = (ch.match(/\{[^}]+\}|\S+/g) || []).map(normTok).filter(Boolean);
    let first = Math.min(wi, ws.length - 1);
    if (toks.length) for (let k = wi; k < Math.min(ws.length, wi + 4); k++) if (normTok(ws[k].w) === toks[0]) { first = k; break; }
    const last = Math.min(ws.length - 1, first + Math.max(1, toks.length) - 1);
    out.push({ t0: ws[first].t0 - lead, wEnd: ws[last].t1, markup: ch });
    wi = last + 1;
  }
  // merge chunks that would be on screen for less than minFrames
  for (let i = 0; i < out.length - 1; i++) {
    if (out[i + 1].t0 - out[i].t0 < minDur && out.length > 1) {
      out[i] = { t0: out[i].t0, wEnd: out[i + 1].wEnd, markup: out[i].markup + ' ' + out[i + 1].markup };
      out.splice(i + 1, 1); i--;
    }
  }
  return out.map((c, i) => {
    const e = { t0: c.t0, t1: i + 1 < out.length ? out[i + 1].t0 : c.wEnd + tail, markup: c.markup };
    if (o.mode) e.mode = o.mode;
    if (o.mode === 'type') { const n = c.markup.replace(/\{([^|}]+)(\|[^}]+)?\}/g, '$1').length; e.cps = Math.max(18, Math.min(60, n / Math.max(0.15, c.wEnd - c.t0 - lead))); }
    return e;
  });
}
