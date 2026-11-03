// hook_c.js — hook shots C1-C9 (2:13 a.m.: bedtime, the app appears, terms and conditions, the page stack, the flick,
// I AGREE and the ripple).
// STUBS (phase 2 timeline task): one placeholder per shot = the right set + a big label with the shot id + a slow push,
// so the whole timeline (episodes/hook/timeline.json) renders end to end. The shot animators replace each function
// body; keep the exported names (they are the timeline's shot names). Plan per shot: episodes/hook/SHOTS.md.
import { bedroom, street } from '../sets.js';
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

const BED = () => bedroom({ clock: '2:13' });
const NIGHT_STREET = () => street({ night: 1, split: true });
/** phone POV over the night bedroom: the phone in Sam's hand with an app screen (SCREEN-space content) */
function _pov(ctx, content, crumb, screen) {
  const cam = _cam(ctx, { x: 80, y: -40, z: 1.25 });
  let s = cam.set(ctx.memo('hook_c/bed', BED));
  s += cam.screen(U2.phone({ x: 1180, y: 600, s: 0.56, rot: -6, glow: 0.8, screen: screen || U2.appScreen({ time: '2:13', crumb, content }) }));
  return s + cam.screen(_label(ctx));
}

// ---------- C1-C9 ----------
export function C1_bedtime(ctx) {
  const cam = _cam(ctx, { z: 1.0 });
  return cam.set(ctx.memo('hook_c/bed', BED)) + cam.screen(_label(ctx));
}

export function C2_supposedly(ctx) {
  const cam = _cam(ctx, { x: -120, y: -170, z: 2.1 });
  return cam.set(ctx.memo('hook_c/bed', BED)) + cam.screen(_label(ctx));
}

export function C3_appappears(ctx) {
  return _pov(ctx, '', 'Home', U2.homeScreen({ time: '2:13', newApp: Math.min(1, ctx.t / 0.6), t: ctx.t }));
}

export function C4_terms(ctx) {
  return _pov(ctx, '', 'Settings › {Terms|purple}');
}

export function C5_pagestack(ctx) {
  const cam = _cam(ctx, { y: -40, z: 0.72, dy: -60 });
  let s = cam.set(ctx.memo('hook_c/bed', BED));
  s += cam.layer(U2.pageStack({ cx: 1040, base: 760, n: 400 + 4400 * ctx.u, w: 300, t: ctx.t }), 0.75);
  return s + cam.screen(_label(ctx));
}

export function C6_squint(ctx) {
  const cam = _cam(ctx, { x: -120, y: -170, z: 2.1 });
  return cam.set(ctx.memo('hook_c/bed', BED)) + cam.screen(_label(ctx));
}

export function C7_flick(ctx) {
  const cam = _cam(ctx, {});
  let s = _bg(ctx, '#25204A', '#0F0C24');
  s += cam.layer(U.termsPage({ x: 560, y: 70, w: 800, h: 860, page: '4,812', of: '4,812', highlight: 1 }), 1);
  return s + cam.screen(_label(ctx));
}

export function C8_agree(ctx) {
  const cam = _cam(ctx, { x: 80, y: -40, z: 1.25 });
  let s = cam.set(ctx.memo('hook_c/bed', BED));
  s += cam.screen(U2.phone({ x: 1180, y: 600, s: 0.56, rot: -6, glow: 0.8, screen: U2.appScreen({ time: '2:13', crumb: 'Settings › {Terms|purple}' }) }));
  s += cam.screen(U2.agreeButton({ cx: 960, cy: 760, w: 640, h: 184 }, 1));
  return s + cam.screen(_label(ctx));
}

export function C9_ripple(ctx) {
  const cam = _cam(ctx, { x: -120, y: -40, z: 1.0 });
  return cam.set(ctx.memo('hook_c/nightstreet', NIGHT_STREET)) + cam.screen(_label(ctx));
}
