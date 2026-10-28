// Episode 2 frames. Same look as episode 1, with steadier line boil (4 changes a second instead of 6),
// Nora's lines captioned in teal, and the new mall / restroom / storm templates.
import { W, H, defs, finish, caption, watermark, g } from './lib.js';
import { SH } from './ep/shots_in.js';
import './ep/shots_out.js';
import './ep/cards.js';
import './ep/ep2/shots.js';
import { easeOut } from './ep/kit.js';

const wrap = (inner, seed, boil) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}">${defs(seed, boil)}${inner}</svg>`;
const NO_CAPS = new Set(['black', 'ep_title']);
const CARD_Y = new Set(['card', 'card2', 'map', 'map2']);
const NO_MARK = new Set(['card', 'card2', 'map', 'map2', 'povaisle', 'povstorm', 'black', 'ep_title', 'radio']);
const FINISH = { card: { vignette: 0.5, grain: 0.1 }, card2: { vignette: 0.5, grain: 0.1 }, map: { vignette: 0.45, grain: 0.1 }, map2: { vignette: 0.45, grain: 0.1 },
  povaisle: { vignette: 0.6, grain: 0.16 }, povstorm: { vignette: 0.6, grain: 0.16 }, black: { vignette: 0, grain: 0.05 } };
const CAP_COLOR = { NORA: '#7FD8CC' };

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
        // a one-letter word ("I", "a", the letters of S. O. S.) rides with its neighbour, so it never flashes alone
        let txt = clean(ws[i].w), t0 = ts;
        const one = (k) => k >= 0 && k < ws.length && clean(ws[k].w).length <= 1;
        let j0 = i, j1 = i; while (one(j0 - 1) && one(i)) j0--; while (one(j1 + 1) && one(i)) j1++;
        if (one(i) && j1 > j0) {   // spelled-out letters (S. O. S.) show together as one word
          txt = ws.slice(j0, j1 + 1).map((x) => clean(x.w)).join('.') + '.'; t0 = L.start + ws[j0].t - 0.03;
        } else if (i > 0 && one(i - 1) && !one(i - 2) && txt.length > 1) { txt = clean(ws[i - 1].w) + ' ' + txt; t0 = L.start + ws[i - 1].t - 0.03; }
        else if (txt.length <= 1 && i + 1 < ws.length) txt += ' ' + clean(ws[i + 1].w);
        return { w: txt, age: tg - t0, dialogue: L.who && L.who !== 'N', color: CAP_COLOR[L.who] };
      }
    }
  }
  return null;
}
function captions(T, tg, y) {
  const w = spoken(T, tg); if (!w || !w.w) return '';
  const k = 0.86 + 0.14 * easeOut(w.age / 0.08);
  return g(caption(w.w, { y, dialogue: w.dialogue, color: w.color }), { transform: `translate(${W / 2} ${y}) scale(${k.toFixed(3)}) translate(${-W / 2} ${-y})` });
}

export function frame(T, tg) {
  const sh = T.shots.find((x) => tg >= x.start && tg < x.end) || T.shots[T.shots.length - 1];
  const boil = 7 + (Math.floor(tg * 4) % 3) * 13;
  const D = sh.end - sh.start, lt = tg - sh.start, fn = SH[sh.name];
  let s = fn ? fn(T, tg, lt, sh.p || {}, D) : '';
  const low = CARD_Y.has(sh.name) || (sh.p && ['diagram', 'panel', 'switch'].includes(sh.p.view));
  if (!NO_CAPS.has(sh.name)) s += captions(T, tg, low ? 1030 : 870);
  if (!NO_MARK.has(sh.name)) s += watermark();
  s += finish(FINISH[sh.name] || { vignette: 0.9, grain: 0.12 });
  return wrap(s, 5, boil);
}
