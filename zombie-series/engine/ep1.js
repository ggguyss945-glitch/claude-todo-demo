// Episode 1 frames: the cold open reuses the 60 s test's shots, everything after it uses the episode templates.
import { W, H, INK, defs, finish, caption, watermark, g, text } from './lib.js';
import { drawShot, SHOT_NAMES } from './anim.js';
import { SH } from './ep/shots_in.js';
import './ep/shots_out.js';
import './ep/cards.js';
import { easeOut } from './ep/kit.js';

const wrap = (inner, seed, boil) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}">${defs(seed, boil)}${inner}</svg>`;
const COLD = new Set(SHOT_NAMES);
const NO_CAPS = new Set(['povshelf', 'povlot', 'black', 'ep_title']);
const CARD_Y = new Set(['card', 'map']);
const NO_MARK = new Set(['card', 'map', 'povshelf', 'povlot', 'black', 'ep_title', 'radio']);
const FINISH = { card: { vignette: 0.5, grain: 0.1 }, map: { vignette: 0.45, grain: 0.1 }, povshelf: { vignette: 0.6, grain: 0.16 }, povlot: { vignette: 0.6, grain: 0.16 }, black: { vignette: 0, grain: 0.05 } };

// the word being spoken now, from any voiced line; dialogue (Dale, you, the PA) shows in orange
const clean = (w) => w.replace(/[.,!?]+$/, '').replace(/^\.+/, '');
function spoken(T, tg) {
  for (const L of T.voice.lines) {
    if (tg < L.start - 0.02 || tg > L.start + L.dur + 0.15) continue;
    const ws = L.words;
    for (let i = ws.length - 1; i >= 0; i--) {
      const ts = L.start + ws[i].t - 0.03;
      if (tg >= ts) {
        let te = i + 1 < ws.length ? L.start + ws[i + 1].t - 0.03 : L.start + L.dur + 0.15;
        if (ws[i].e !== undefined) te = Math.min(te, L.start + ws[i].e + 0.35);
        if (tg > te) break;
        // a one-letter word ("I", "a") rides with its neighbour, so it never flashes alone (a skewed "I" reads as "/")
        let txt = clean(ws[i].w), t0 = ts;
        if (i > 0 && clean(ws[i - 1].w).length <= 1 && txt.length > 1) { txt = clean(ws[i - 1].w) + ' ' + txt; t0 = L.start + ws[i - 1].t - 0.03; }
        else if (txt.length <= 1 && i + 1 < ws.length) txt += ' ' + clean(ws[i + 1].w);
        return { w: txt, age: tg - t0, dialogue: L.who && L.who !== 'N' };
      }
    }
  }
  return null;
}
function captions(T, tg, y) {
  const w = spoken(T, tg); if (!w || !w.w) return '';
  const k = 0.86 + 0.14 * easeOut(w.age / 0.08);
  return g(caption(w.w, { y, dialogue: w.dialogue }), { transform: `translate(${W / 2} ${y}) scale(${k.toFixed(3)}) translate(${-W / 2} ${-y})` });
}

export function frame(T, tg) {
  const sh = T.shots.find((x) => tg >= x.start && tg < x.end) || T.shots[T.shots.length - 1];
  const boil = 7 + (Math.floor(tg * 6) % 3) * 13;
  if (sh.cold && COLD.has(sh.name)) return wrap(drawShot(T, sh, tg), 5, boil);
  const D = sh.end - sh.start, lt = tg - sh.start, fn = SH[sh.name];
  let s = fn ? fn(T, tg, lt, sh.p || {}, D) : '';
  const low = CARD_Y.has(sh.name) || (sh.p && ['diagram', 'panel', 'switch'].includes(sh.p.view));   // keep captions off on-screen text
  if (!NO_CAPS.has(sh.name)) s += captions(T, tg, low ? 1030 : 870);
  if (!NO_MARK.has(sh.name)) s += watermark();
  s += finish(FINISH[sh.name] || { vignette: 0.9, grain: 0.12 });
  return wrap(s, 5, boil);
}
