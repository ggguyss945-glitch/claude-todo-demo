"""end_fade.py: the last music tail dies away over the end card instead of being cut at the film's last frame.
    python3 audio/end_fade.py <mix dir> <fade start s> [silent margin s]
Fades mix_en.wav and the stems (music, sfx) with a raised-cosine from the fade start to (end - margin), silence after;
the voice has ended before the end card (it is untouched: the fade starts after the last word)."""
import os, sys
import numpy as np, soundfile as sf
d, t0 = sys.argv[1], float(sys.argv[2]); margin = float(sys.argv[3]) if len(sys.argv) > 3 else 0.15
for f in ('mix_en.wav', 'stems/music.wav', 'stems/sfx.wav'):
    p = os.path.join(d, f)
    if not os.path.exists(p):
        continue
    info = sf.info(p); y, sr = sf.read(p, dtype='float32', always_2d=True)
    a, b = int(t0 * sr), max(int(t0 * sr) + 1, len(y) - int(margin * sr))
    env = np.ones(len(y), np.float32)
    env[a:b] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, b - a))
    env[b:] = 0.0
    sf.write(p + '.tmp.wav', y * env[:, None], sr, subtype=info.subtype); os.replace(p + '.tmp.wav', p)
    print(f'end fade {f}: {t0:.2f} -> {b / sr:.2f} s of {len(y) / sr:.2f} s')
