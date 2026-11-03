// hook_b.js — hook shots A6-A10 + B1 (the Day 7 flash-forward: factory reset, mannequins, Sam's defense, 412, "...Ish.",
// and the UNDO HISTORY rewind).
// STUBS (phase 2 timeline task): one placeholder per shot = the right set + a big label with the shot id + a slow push,
// so the whole timeline (episodes/hook/timeline.json) renders end to end. The shot animators replace each function
// body; keep the exported names (they are the timeline's shot names). Plan per shot: episodes/hook/SHOTS.md.
import { streetReset } from '../sets.js';
import * as U from '../ui.js';
import * as U2 from '../ui2.js';
import { FONT, text, rect, esc } from '../ui_style.js';

// ---------- stub helpers (private: names starting with _ are not registered as shots) ----------
const _r = (n) => Math.round(n * 100) / 100;
/** the stub's label card: shot id, name, owner module, brief, local/global time and a progress bar (screen space) */
function _label(ctx) {
  const P = ctx.p || {}, id = P.id || ctx.name, brief = P.brief || '';
  const lines = U.wrapText(brief, 28, 1180).slice(0, 3);
  const h = 170 + lines.length * 36;
  let s = rect(40, 40, 1260, h, { rx: 28, fill: '#101028', opacity: 0.72 });
  s += text(76, 150, esc(id), { fontFamily: FONT.title, fontSize: 112, fill: '#FFD23F', stroke: '#101028', strokeWidth: 10, paintOrder: 'stroke' });
  s += text(76 + 70 * id.length + 40, 112, esc(ctx.name), { fontFamily: FONT.ui, fontWeight: 900, fontSize: 48, fill: '#FFFFFF' });
  s += text(76 + 70 * id.length + 40, 152, esc(`STUB · ${P.module || ''}.js · set ${P.set || '?'}`), { fontFamily: FONT.ui, fontWeight: 800, fontSize: 26, fill: '#9FB4FF' });
  lines.forEach((ln, i) => { s += text(76, 206 + i * 36, esc(ln), { fontFamily: FONT.ui, fontWeight: 800, fontSize: 28, fill: '#E8ECFF' }); });
  const u = Math.max(0, Math.min(1, ctx.t / Math.max(1e-6, ctx.dur)));
  s += rect(76, h + 6, 1188, 10, { rx: 5, fill: '#2A2F5A' }) + rect(76, h + 6, 1188 * u, 10, { rx: 5, fill: '#FFD23F' });
  s += text(1880, 1050, esc(`t ${_r(ctx.t).toFixed(2)} / ${_r(ctx.dur).toFixed(2)} · ${_r(ctx.gt).toFixed(2)} s · f${ctx.frame}`), { fontFamily: FONT.ui, fontWeight: 800, fontSize: 26, fill: '#FFFFFF', textAnchor: 'end', stroke: '#101028', strokeWidth: 6, paintOrder: 'stroke' });
  return s;
}
/** a slow push (+4%) with a little drift from a framing {x, y, z} */
function _cam(ctx, f = {}) {
  const z = f.z ?? 1;
  return ctx.cam({ keys: [[0, { x: f.x || 0, y: f.y || 0, z }], [ctx.dur, { x: (f.x || 0) + (f.dx || 0), y: (f.y || 0) + (f.dy || 0), z: z * 1.04 }, 'inOutSine']], drift: 6 });
}
const _bg = (ctx, c1, c2) => `<defs><linearGradient id="stubbg_${ctx.name}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${c1}"/><stop offset="1" stop-color="${c2}"/></linearGradient></defs><rect x="-60" y="-60" width="2040" height="1200" fill="url(#stubbg_${ctx.name})"/>`;

const RESET_SET = () => streetReset({ t: 0.2, glitch: false });

// ---------- A6-A10, B1 ----------
export function A6_day7wide(ctx) {
  const cam = _cam(ctx, {});
  let s = cam.set(ctx.memo('hook_b/reset', RESET_SET));
  s += cam.screen(U.timerPill({ x: 960, y: 420, label: '1:00' }));
  return s + cam.screen(_label(ctx));
}

export function A7_mannequins(ctx) {
  const cam = _cam(ctx, { x: 0, y: 160, z: 1.45 });
  let s = cam.set(ctx.memo('hook_b/reset', RESET_SET));
  return s + cam.screen(_label(ctx));
}

export function A8_samdefense(ctx) {
  const cam = _cam(ctx, { x: -160, y: 180, z: 1.9 });
  let s = cam.set(ctx.memo('hook_b/reset', RESET_SET));
  return s + cam.screen(_label(ctx));
}

export function A9_counter412(ctx) {
  const cam = _cam(ctx, { x: -160, y: 180, z: 1.9 });
  let s = cam.set(ctx.memo('hook_b/reset', RESET_SET));
  const v = 1 + 411 * Math.max(0, Math.min(1, ctx.u * 1.1));
  s += cam.screen(U2.counter({ x: 1180, y: 300, value: v, label: 'Changes made by you' }, 1));
  return s + cam.screen(_label(ctx));
}

export function A10_ish(ctx) {
  const cam = _cam(ctx, { x: -160, y: 180, z: 2.0 });
  let s = cam.set(ctx.memo('hook_b/reset', RESET_SET));
  return s + cam.screen(_label(ctx));
}

export function B1_rewind(ctx) {
  const cam = _cam(ctx, {});
  let s = _bg(ctx, '#2B2350', '#120E2A');
  s += cam.screen(U2.undoHistory({ x: 580, y: 80, scroll: 40 + 300 * ctx.u, speed: 0 }, 1));
  return s + cam.screen(_label(ctx));
}
