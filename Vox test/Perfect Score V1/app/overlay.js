// 2D overlay: burned-in captions (2-4 word groups, timed to the narration's
// word timings) and the CCTV HUD (camera label, timecode, rewind icon).
import { prog, clamp } from './util.js';

export const CAPTION_GROUPS = [
  "Imagine you scored",
  "a perfect hundred",
  "on every single exam.",
  "This is how fast",
  "it would take",
  "for your school",
  "to accuse you of cheating.",
  "Your first perfect score,",
  "nobody notices.",
  "Anyone can have",
  "a good day.",
  "But after your second",
  "and third hundred,",
  "your teacher",
  "starts to notice.",
  "He doesn't say a word.",
  "He just keeps",
  "an eye on you.",
  "By your fifth in a row,",
  "your desk gets moved",
  "to the front,",
  "right next to his.",
  "Every time you look up,",
  "he's already watching.",
  "Then comes",
  "the hardest exam",
  "of the year,",
  "with a bonus question",
  "nobody has ever solved.",
  "You solve it.",
  "And now,",
  "this can't be ignored.",
  "You're called",
  "to the principal's office.",
  "They search your bag,",
  "your pencil case,",
  "even the label",
  "on your water bottle.",
  "They replay",
  "the classroom camera,",
  "and compare your answers",
  "with the smartest kid",
  "in class.",
  "Nothing.",
  "No notes,",
  "no signals,",
  "no copying.",
  "But nobody",
  "believes you.",
  "Your parents",
  "get a phone call.",
  "Your score",
  "gets cancelled.",
  "By lunch,",
  "the whole school",
  "is whispering",
  "one word.",
  "Cheater.",
  "So the principal",
  "makes a decision.",
  "A brand new exam,",
  "taken alone",
  "in his office,",
  "with three teachers",
  "watching your every move.",
  "You pick up",
  "your pencil.",
  "Twenty minutes later,",
  "you put it down.",
  "They grade it",
  "right in front of you.",
  "One hundred.",
  "The room",
  "goes silent.",
  "Because you",
  "were never cheating.",
  "You were just studying",
  "every single night,",
  "while everyone else",
  "was on their phones.",
  "The principal apologizes,",
  "and puts your name",
  "on the wall of honor.",
  "And your desk",
  "gets moved again,",
  "to the very back.",
  "This time,",
  "so nobody",
  "can copy you.",
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
  // a caption stays up until the next one, but clears during long pauses
  let wj = 0;
  for (let i = 0; i < out.length; i++) {
    const n = CAPTION_GROUPS[i].split(' ').length;
    const lastEnd = words[wj + n - 1].e;
    wj += n;
    const next = i + 1 < out.length ? out[i + 1].s : 99;
    out[i].e = Math.min(next, lastEnd + 0.55);
  }
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
