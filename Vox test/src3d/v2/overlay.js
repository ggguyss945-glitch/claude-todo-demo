// 2D overlay: burned-in captions and the CCTV HUD (camera label, timecode,
// face-tracking box, glitch glyphs, rewind icon).
import { prog, clamp } from './util.js';

export const CAPTION_GROUPS = [
  'Imagine you have', 'a magic pair of glasses', 'that can tell you', 'upcoming roulette rolls.', 'This is how fast',
  'it would take', 'for you to get banned.', 'The first few bets you win,', 'nobody notices.', 'Everyone can get this lucky,',
  'but as you keep crushing it', 'suspicion starts at the table.', 'The dealer', 'and the pit manager', 'notice your unusual',
  'winning pattern,', 'but they just keep an eye', 'on you at first.', 'But as your perfect', 'winning streak continues,',
  'surveillance gets pinged', 'and the eye in the sky', 'locks onto you.', 'They carefully', 'inspect your bet timing',
  'and body language.', 'However, nothing about', 'you can be linked', 'to known cheating methods.', 'Nonetheless, at this point,',
  "you're straight up", 'draining the casino,', 'and this cannot be ignored.', 'They scramble to identify',
  'you and see if you are linked|6', 'to any previous incidents', "and you're not.", 'At this point,', 'a crowd of people',
  'have gathered', 'around the table', 'to witness your', 'incredible streak.', 'A few people even started',
  'copying your bets,', 'thus making the casino', 'bleed cash.', 'Security fear', 'you might have an inside man,',
  'so they change', "the table's dealer,", "but that doesn't stop you", 'from winning.', 'And thus', 'management is faced',
  'with a difficult decision.', 'Let you continue', 'or kick you out', 'in front of everyone', 'and face a reputation blow.',
  'But as you win', 'a few more times,', 'your unbelievable streak', 'cannot be explained', 'by just luck',
  "and you're labeled", 'as an advantage player.', 'They congratulate', 'you on your wins', 'and kindly', 'ask you',
  'to stop playing roulette.', 'You can play on', 'other games though.',
];

export function buildCaptions(words) {
  const out = [];
  let wi = 0;
  for (const g of CAPTION_GROUPS) {
    const [text, nStr] = g.split('|');
    const n = nStr ? parseInt(nStr) : text.split(' ').length;
    out.push({ text, s: Math.max(0, words[wi].s - 0.17) });
    wi += n;
  }
  for (let i = 0; i < out.length; i++) out[i].e = i + 1 < out.length ? out[i + 1].s : 99;
  return out;
}

export function drawCaption(g, caps, t, W, H, style = {}) {
  const c = caps.find((x) => t >= x.s && t < x.e);
  if (!c) return;
  const size = (style.size || 0.0432) * W; // ~62px at 1440
  g.save();
  g.font = `bold ${size}px "Liberation Sans", Arial, sans-serif`;
  g.textAlign = 'center';
  g.textBaseline = 'alphabetic';
  const x = W / 2, y = (style.y || 0.7165) * H;
  g.lineJoin = 'round';
  // soft dark shadow, then crisp black outline, then white fill
  g.shadowColor = 'rgba(0,0,0,0.85)';
  g.shadowBlur = size * 0.18;
  g.shadowOffsetY = size * 0.04;
  g.strokeStyle = '#000';
  g.lineWidth = size * 0.16;
  g.strokeText(c.text, x, y);
  g.shadowColor = 'transparent';
  g.lineWidth = size * 0.1;
  g.strokeText(c.text, x, y);
  g.fillStyle = '#ffffff';
  g.fillText(c.text, x, y);
  g.restore();
}

export function tcString(sec) {
  const f = Math.floor((sec * 30) % 30), s = Math.floor(sec) % 60, m = Math.floor(sec / 60) % 60, h = Math.floor(sec / 3600) % 24;
  const p = (v) => String(v).padStart(2, '0');
  return `${p(h)}:${p(m)}:${p(s)}:${p(f)}`;
}

function hudText(g, text, x, y, size, weight, align, W) {
  g.save();
  g.font = `${weight} ${size}px "DejaVu Sans", "Liberation Sans", sans-serif`;
  g.textAlign = align;
  g.lineJoin = 'round';
  g.strokeStyle = 'rgba(0,0,0,0.9)';
  g.lineWidth = size * 0.16;
  g.strokeText(text, x, y);
  g.fillStyle = '#f4f4f4';
  g.shadowColor = 'rgba(255,255,255,0.6)';
  g.shadowBlur = size * 0.12;
  g.fillText(text, x, y);
  g.restore();
}

export function drawCCTV(g, info, t, W, H) {
  if (!info) return;
  const size = 0.058 * W;
  const y = info.y ? info.y * H : 0.268 * H;
  hudText(g, info.cam, 0.072 * W, y, size, 'bold', 'left', W);
  hudText(g, tcString(info.tc(t)), 0.945 * W, y, size * 1.08, 'normal', 'right', W);
  if (info.rewind && info.rewind(t)) {
    hudText(g, '«', 0.4 * W, 0.47 * H, size * 1.5, 'bold', 'center', W);
  }
  if (info.face) {
    const f = info.face; // {x,y,s} in normalized screen coords
    const bw = f.s * W, bx = f.x * W - bw / 2, by = f.y * H - bw / 2;
    g.save();
    g.strokeStyle = '#f4f4f4';
    g.lineWidth = 0.0045 * W;
    g.shadowColor = 'rgba(0,0,0,0.7)';
    g.shadowBlur = 6;
    g.strokeRect(bx, by, bw, bw);
    g.restore();
    const glyphs = [',=:?', '...?', ';.?-', '/!..', '..?', ',.?'];
    const gi = Math.floor(t * 2.2) % glyphs.length;
    const gx = f.glyphX !== undefined ? f.glyphX * W : bx - 0.05 * W;
    hudText(g, glyphs[gi], gx, by + bw * 0.25, 0.1 * W, 'bold', f.glyphAlign || 'right', W);
  }
}
