// One-word captions, like the reference: heavy rounded white sans, black outline and soft shadow,
// centred at 70.3% of the frame height, glyphs about 5% of the frame width tall.
export function buildCaptions(words) {
  const out = [];
  for (let i = 0; i < words.length; i++) {
    const w = words[i], nx = words[i + 1];
    let e = nx ? nx.s : w.s + 0.6;
    if (w.end_line !== undefined) e = Math.min(e, w.end_line + 0.12);
    e = Math.min(e, w.s + 0.9);
    out.push({ text: w.w, s: w.s, e });
  }
  return out;
}

export function drawCaption(g, caps, t, W, H) {
  const c = caps.find((x) => t >= x.s && t < x.e);
  if (!c) return;
  const size = 0.068 * W;
  g.save();
  g.font = `900 ${size}px "Nunito"`;
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  const x = W / 2, y = 0.703 * H;
  // tiny pop-in on each new word
  const k = Math.min(1, (t - c.s) / 0.06);
  g.translate(x, y); g.scale(0.92 + 0.08 * k, 0.92 + 0.08 * k);
  g.lineJoin = 'round';
  g.shadowColor = 'rgba(0,0,0,0.55)'; g.shadowBlur = size * 0.16; g.shadowOffsetY = size * 0.05;
  g.strokeStyle = '#000'; g.lineWidth = size * 0.17;
  g.strokeText(c.text, 0, 0);
  g.shadowColor = 'transparent';
  g.fillStyle = '#ffffff';
  g.fillText(c.text, 0, 0);
  g.restore();
}
