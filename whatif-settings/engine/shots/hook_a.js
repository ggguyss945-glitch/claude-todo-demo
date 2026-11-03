// hook_a.js — hook shots A1-A5 (the promise: dog size, one app, tree flip, total control, no undo).
// STUBS (phase 2 timeline task): one placeholder per shot = the right set + a big label with the shot id + a slow push,
// so the whole timeline (episodes/hook/timeline.json) renders end to end. The shot animators replace each function
// body; keep the exported names (they are the timeline's shot names). Plan per shot: episodes/hook/SHOTS.md.
import { street, flipTree, STREET } from '../sets.js';
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

const STREET_DAY = () => street({ split: true, liveTree: 'kevin' });

// ---------- A1-A5 ----------
export function A1_dogsize(ctx) {
  const cam = _cam(ctx, { x: 600, y: 40, z: 1.22 });
  let s = cam.set(ctx.memo('hook_a/street', STREET_DAY));
  const v = 0.15 + 0.8 * ctx.u;
  const scr = U2.dogSizeScreen({ v, grab: 1 });
  s += cam.screen(U2.phone({ x: 1370, y: 560, s: 0.58, rot: -8, screen: U2.appScreen({ time: '4:05', crumb: 'Settings › {World|purple} › {Pets|pink}', content: scr.svg }), thumb: { x: scr.knob[0] + 14, y: scr.knob[1] + 26, press: 0.7 } }));
  return s + cam.screen(_label(ctx));
}

export function A2_oneapp(ctx) {
  const cam = _cam(ctx, {});
  let s = _bg(ctx, '#3B2C8F', '#1B1446');
  s += cam.layer(U2.appIcon({ cx: 960, cy: 560, size: 360 + 420 * ctx.u, glow: 1, t: ctx.t, label: 'REALITY SETTINGS' }), 1);
  return s + cam.screen(_label(ctx));
}

export function A3_treeflip(ctx) {
  const cam = _cam(ctx, { x: 520, y: -30, z: 1.3 });
  const T = STREET.trees.kevin;
  const tree = flipTree({ ...T, angle: 180, soil: 0.6 });
  let s = cam.set(ctx.memo('hook_a/street', STREET_DAY), { insert: [{ after: 'mid', depth: 0.75, svg: tree }] });
  return s + cam.screen(_label(ctx));
}

export function A4_control(ctx) {
  const cam = _cam(ctx, {});
  let s = _bg(ctx, '#2A86E0', '#1550A8');
  s += cam.layer(U2.fanMontage({ cx: 960, p: 1 }), 0.8);
  s += cam.layer(U.dayCard({ cx: 960, cy: 520, day: 7, scale: 0.9 }, 1), 1);
  return s + cam.screen(_label(ctx));
}

export function A5_noundo(ctx) {
  const cam = _cam(ctx, {});
  let s = _bg(ctx, '#3A3F6E', '#1E2140');
  s += cam.layer(U2.undoButton({ cx: 960, cy: 600, crack: 0.5 }), 1);
  return s + cam.screen(_label(ctx));
}
