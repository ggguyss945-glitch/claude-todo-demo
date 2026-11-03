// frame.js — engine v3 frame renderer: frame(T, t) -> one 1920x1080 SVG string, a pure function of (timeline, time).
// Works in the browser (engine/anim.html, driven by tools/render.js) and in node (tests, cue export).
//
// Timeline T (JSON):
//   { fps: 60, dur, modules: ['shots/hook.js', ...]                       shot modules, relative to engine/
//     shots: [{ name, use?, start, end, p?, capY?, tin?, tout? }, ...]   use = registered shot function (default name)
//     voice: { lines: [{ id, role, start, dur, file, text, words: [{w, t0, t1}], visemes: [[t, 'A'], ...] }] }
//            word / viseme times are seconds from the line start (voice.absolute: true if they are global)
//     captions: [{ t0, t1, markup, mode?, y?, size?, cps? }],            global seconds, see anim/captions.js
//     overlays: [{ t0, t1, use: 'flash' | <registered fn>, p? }] }        screen-space, above shots, below captions
// Shot function: render(ctx) -> svg string covering the frame (screen space). ctx: see makeCtx() / README.md.
import { resetDefs, defsSvg } from '../style.js';
import { FPS, clamp, seg, val, hash, rng, rand, noise1d } from './motion.js';
import { camera } from './camera.js';
import { actor, actorState } from './actor.js';
import { normWords, normVisemes, autoVisemes, visemeAt, inWord } from './lipsync.js';
import { windowOf, renderTransition } from './transitions.js';
import { drawCaptions } from './captions.js';
import { layer as bakeLayer } from './bake.js';

export const W = 1920, H = 1080;
const REG = new Map();
const MEMO = new Map();

/** register a shot (or overlay) function under a name */
export function register(name, fn) { if (typeof fn === 'function') REG.set(name, fn); }
/** register every exported function of a module (names starting with _ are private), plus mod.SHOTS = {name: fn} */
export function registerModule(mod) {
  for (const [k, v] of Object.entries(mod)) if (typeof v === 'function' && !k.startsWith('_') && k !== 'default') register(k, v);
  if (mod.SHOTS) for (const [k, v] of Object.entries(mod.SHOTS)) register(k, v);
  if (typeof mod.default === 'function' && mod.default.shotName) register(mod.default.shotName, mod.default);
}
export const registered = () => [...REG.keys()];
/** import T.modules with importer(path) (browser: p => import('./' + p)), register them, prepare T */
export async function loadTimeline(T, importer) {
  for (const m of T.modules || []) registerModule(await importer(m));
  return prepare(T);
}

// ---------- timeline preparation (once per T) ----------
export function prepare(T) {
  if (T.__prep) return T;
  const fps = (T.fps = T.fps || FPS);
  T.shots = (T.shots || []).slice().sort((a, b) => a.start - b.start);
  if (T.dur === undefined) T.dur = T.shots.length ? T.shots[T.shots.length - 1].end : 0;
  const abs = !!T.voice?.absolute;
  T.__lines = (T.voice?.lines || []).map((L) => {
    const start = +L.start || 0;
    const words = normWords(L.words || [], abs ? start : 0);
    let vis = L.visemes ? normVisemes(L.visemes, abs ? start : 0) : null;
    const auto = !vis && words.length > 0;
    if (auto) vis = autoVisemes(words, { fps });
    const dur = L.dur ?? (words.length ? words[words.length - 1].t1 + 0.1 : 1);
    return { ...L, start, dur, end: start + dur, words, visemes: vis || [], auto, roleKey: String(L.role || '').toLowerCase() };
  });
  T.__lineById = new Map(T.__lines.map((L) => [L.id, L]));
  // transition windows at every boundary
  T.__tr = [];
  for (let i = 1; i < T.shots.length; i++) {
    const A = T.shots[i - 1], B = T.shots[i];
    const tr = B.tin || A.tout;
    if (!tr || !tr.type || tr.type === 'cut') continue;
    const [w0, w1] = windowOf(tr, B.start, fps);
    if (w1 > w0) T.__tr.push({ i, b: B.start, tr, w0, w1 });
  }
  T.captions = (T.captions || []).slice().sort((a, b) => a.t0 - b.t0);
  T.__prep = true;
  return T;
}

/** index of the shot that owns global time gt (gaps hold the previous shot; clamps at both ends) */
export function shotIndex(T, gt) {
  const S = T.shots; let i = 0;
  for (let k = 0; k < S.length; k++) if (S[k].start <= gt + 1e-9) i = k; else break;
  return i;
}

// ---------- voice helpers ----------
function localLine(L, off) {
  if (!L) return null;
  const words = L.words.map((w) => ({ w: w.w, t0: L.start + w.t0 - off, t1: L.start + w.t1 - off }));
  const norm = (s) => String(s).toLowerCase().replace(/[^a-z0-9']/g, '');
  return {
    id: L.id, role: L.role, text: L.text, file: L.file, start: L.start - off, end: L.end - off, dur: L.dur, words,
    visemes: L.visemes.map(([t, v]) => [L.start + t - off, v]),
    /** word by index or by spelling (first match, or the n-th with word(text, n)) -> {w, t0, t1} | null */
    word(k, n = 0) {
      if (typeof k === 'number') return words[k < 0 ? words.length + k : k] || null;
      const m = words.filter((w) => norm(w.w) === norm(k));
      return m[n] || null;
    },
    /** start time of a word (or the line start if not found) */
    at(k, n = 0) { const w = this.word(k, n); return w ? w.t0 : L.start - off; },
  };
}
function findLines(T, who) {
  if (!who) return [];
  if (typeof who === 'object') return [who];
  const L = T.__lineById.get(who);
  if (L) return [L];
  const k = String(who).toLowerCase();
  return T.__lines.filter((x) => x.roleKey === k);
}
/** viseme name for `who` (role, line id or {visemes, words, start}) at global time gt, or null */
export function mouthAt(T, who, gt) {
  for (const L of findLines(T, who)) {
    const start = L.start ?? 0, lt = gt - start;
    const words = L.words || [];
    const end = L.end ?? (start + (L.dur ?? (words.length ? words[words.length - 1].t1 + 0.1 : 0)));
    if (gt < start - 0.01 || gt > end + 0.1) continue;
    if (words.length && !inWord(words, lt, 2 / (T.fps || FPS))) return null;     // between words: expression mouth
    const v = visemeAt(L.visemes || [], lt);
    return v;
  }
  return null;
}

// ---------- ctx ----------
const memo = (key, fn) => { if (!MEMO.has(key)) MEMO.set(key, fn()); return MEMO.get(key); };
export function makeCtx(T, i, gt, extra = {}) {
  const sh = T.shots[i], fps = T.fps;
  const t = gt - sh.start, dur = sh.end - sh.start;
  const seed = hash(sh.name) % 1000003;
  const holder = extra.holder || {};
  const ctx = {
    T, shot: sh, name: sh.name, index: i, p: sh.p || {}, t, gt, dur, u: clamp(t / Math.max(1e-6, dur)), fps, W, H,
    start: sh.start, end: sh.end, frame: Math.round(gt * fps), seed,
    // voice
    line: (id) => localLine(T.__lineById.get(id), sh.start),
    lines: (role) => T.__lines.filter((L) => (!role || L.roleKey === String(role).toLowerCase()) && L.end > sh.start - 0.5 && L.start < sh.end + 0.5).map((L) => localLine(L, sh.start)),
    mouth: (who, tt = t) => mouthAt(T, typeof who === 'object' ? { ...who, start: (who.start ?? 0) + sh.start } : who, tt + sh.start),
    talking: (who, tt = t) => findLines(T, who).some((L) => tt + sh.start >= L.start && tt + sh.start <= L.end),
    word: (who, tt = t) => {
      for (const L of findLines(T, who)) { const w = inWord(L.words || [], tt + sh.start - L.start, 0); if (w) return { w: w.w, t0: L.start + w.t0 - sh.start, t1: L.start + w.t1 - sh.start }; }
      return null;
    },
    // time helpers
    seg: (a, b) => seg(t, a, b),
    at: (v, o) => val(v, t, o),
    rng: (s = 0) => rng((seed ^ hash(String(s))) >>> 0),
    rand: (a = 0, b = 0) => rand(seed, a, b),
    noise: (x, s = 0) => noise1d(x, seed + s),
    // building blocks
    cam: (o = {}) => camera(t, { dur, fps, seed, bakeFn: bakeLayer, ...o }),
    actor: (id, o = {}) => actor(id, o, o.t ?? t, ctx),
    actorState: (id, o = {}) => actorState(id, o, o.t ?? t, ctx),
    memo,
    bake: (key, make, box, res) => bakeLayer(key, make, box, res),
    portal: (rect) => { holder.portal = rect; },
    cue: (name, at = 0, o = {}) => { if (T.__collect) T.__collect.push({ t: sh.start + at, cue: name, shot: sh.name, ...o }); },
    ...extra.ctx,
  };
  return ctx;
}

function errorCard(name, e) {
  const msg = String((e && e.message) || e).replace(/[<&>]/g, ' ').slice(0, 160);
  return `<rect width="${W}" height="${H}" fill="#FF00AA"/><text x="80" y="500" font-family="Rubik" font-size="54" font-weight="800" fill="#fff">SHOT ERROR: ${name}</text><text x="80" y="580" font-family="Rubik" font-size="30" font-weight="800" fill="#fff">${msg}</text>`;
}
export const ERRORS = [];
/** render shot i at global time gt -> svg (screen space); holder receives side outputs (portal) */
export function renderShot(T, i, gt, holder = {}) {
  const sh = T.shots[i];
  const fn = REG.get(sh.use || sh.name);
  if (!fn) return errorCard(sh.name, `no shot function "${sh.use || sh.name}" (registered: ${[...REG.keys()].slice(0, 12).join(', ')})`);
  try {
    const out = fn(makeCtx(T, i, gt, { holder }));
    return typeof out === 'string' ? out : out?.svg ?? '';
  } catch (e) {
    ERRORS.push({ shot: sh.name, t: gt, msg: String(e && e.stack || e) });
    if (typeof console !== 'undefined') console.error(`shot ${sh.name} at ${gt.toFixed(3)}:`, e);
    return errorCard(sh.name, e);
  }
}
function lazy(fn) { let v, done = false; return () => (done ? v : ((done = true), (v = fn()))); }

function drawOverlays(T, gt) {
  let out = '';
  for (const ov of T.overlays || []) {
    if (gt < ov.t0 || gt >= ov.t1) continue;
    const lt = gt - ov.t0, d = ov.t1 - ov.t0, p = ov.p || {};
    if ((ov.use || ov.type) === 'flash') {
      const fps = T.fps, up = (p.up ?? 1) / fps, hold = (p.hold ?? 1) / fps;
      const op = lt < up ? lt / up : lt < up + hold ? 1 : 1 - clamp((lt - up - hold) / Math.max(1e-6, d - up - hold));
      out += `<rect x="-40" y="-40" width="${W + 80}" height="${H + 80}" fill="${p.color || '#FFFFFF'}" opacity="${Math.round(op * (p.peak ?? 1) * 1000) / 1000}"/>`;
      continue;
    }
    const fn = REG.get(ov.use);
    if (!fn) continue;
    try { out += fn({ T, t: lt, gt, dur: d, u: clamp(lt / d), p, fps: T.fps, W, H, overlay: ov }) || ''; } catch (e) { ERRORS.push({ overlay: ov.use, t: gt, msg: String(e) }); }
  }
  return out;
}

/** the whole frame at global time gt -> complete <svg> document string */
export function frame(T, gt, o = {}) {
  prepare(T);
  resetDefs();
  const fps = T.fps;
  gt = Math.round(gt * fps * 1000) / (fps * 1000);          // snap to a 1/1000-frame grid: same t -> same string
  const trw = T.__tr.find((x) => gt >= x.w0 && gt < x.w1);
  let body, capY;
  if (trw) {
    const hA = {}, hB = {};
    const A = lazy(() => renderShot(T, trw.i - 1, gt, hA)), B = lazy(() => renderShot(T, trw.i, gt, hB));
    if (trw.tr.type === 'zoomThrough' && !trw.tr.rect) A();
    body = renderTransition(trw.tr, gt, A, B, { b: trw.b, w0: trw.w0, w1: trw.w1, fps, seed: hash(T.shots[trw.i].name) % 100003, portal: hA.portal });
    capY = (gt < trw.b ? T.shots[trw.i - 1] : T.shots[trw.i]).capY;
  } else {
    const i = shotIndex(T, gt);
    body = T.shots.length ? renderShot(T, i, gt) : '';
    capY = T.shots[i]?.capY;
  }
  const ov = o.overlays === false ? '' : drawOverlays(T, gt);
  const caps = o.captions === false ? '' : drawCaptions(T.captions, gt, { fps, capY });
  return `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${defsSvg()}<rect width="${W}" height="${H}" fill="${T.bg || '#000'}"/>${body}${ov}${caps}</svg>`;
}

/** SFX cue export: every shot is drawn once at its start with ctx.cue() recording; returns [{t, cue, shot, ...}] */
export function collectCues(T) {
  prepare(T);
  T.__collect = [];
  for (let i = 0; i < T.shots.length; i++) { resetDefs(); renderShot(T, i, T.shots[i].start + 0.0001); }
  const seen = new Set(), out = [];
  for (const c of T.__collect.sort((a, b) => a.t - b.t)) { const k = `${c.cue}@${c.t.toFixed(3)}`; if (!seen.has(k)) { seen.add(k); out.push(c); } }
  delete T.__collect;
  return out;
}
