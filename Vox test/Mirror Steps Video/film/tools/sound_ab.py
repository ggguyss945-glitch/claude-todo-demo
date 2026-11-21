"""sound_ab.py: before/after excerpts of key moments, one A/B wav per moment (before, 1 s of silence, after).

    python3 tools/sound_ab.py BEFORE_DIR AFTER_DIR OUT_DIR [--match-voice]      (run from film/)

BEFORE_DIR / AFTER_DIR are mix.py output dirs (mix.wav + stems/voice_en.wav). With --match-voice the "before" half is
gained so that the narration has the same integrated loudness in both halves (the voice is the same recording, so the
difference you hear is the bed: music + SFX), and the gain is written in README.txt. The moments are MOMENTS below.
"""
import argparse, os, sys
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'audio'))
import sfx as SX  # noqa: E402

SR = 48000
MOMENTS = [
    (0.0, 20.0, 'hook', 'the eighth step appears (3.92 hit), the flash-forwards, the premise'),
    (112.0, 136.0, 'red_line_rule1', 'the fresh red line (118.87), the build, rule 1: the hole before the card, the card hit and the numeral stamp (silent before: no recipe)'),
    (139.0, 152.0, 'the_click', 'the true silence and the nail click (143.29), the woman on the eighth step (148.88)'),
    (190.0, 207.0, 'head_turn_rule2', 'the boy\'s voice, lean closer, riser and hole, the head turn (198.15), rule 2 card'),
    (236.0, 263.0, 'you_have_it', 'the wish, the hole before "You have it" (248.22), the towel snatched and thrown, the fingers, the towel drop (256.87), the doorway'),
    (276.0, 298.0, 'her_face_crossing', 'the clock jerks back, the riser into her face (283.77), "Then you step through": the crossing into the too-normal dawn'),
    (316.0, 334.0, 'candy_declutter', 'the candy (10 wrapper crinkles in 8 s -> one per gesture), the warm other side, the drip'),
    (505.0, 545.0, 'bells', 'kicking the box, the fake bell, the crack remembered, the deepest silence, the real bell (535.36), rule 6 card and stamp'),
    (595.0, 632.0, 'her_foot_rule7', 'you turn, the silence and her foot (605.21), the collar, rule 7, the wipe, the foot hangs, the glass goes dark'),
    (683.0, 700.0, 'last_click', 'counting the steps on the phone, the last silence and click (690.19), the riser into "one more minute", the cut'),
]


def rd(p, a, b):
    with sf.SoundFile(p) as f:
        f.seek(int(a * f.samplerate))
        return f.read(int((b - a) * f.samplerate), dtype='float32', always_2d=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('before'); ap.add_argument('after'); ap.add_argument('out')
    ap.add_argument('--match-voice', action='store_true')
    A = ap.parse_args()
    os.makedirs(A.out, exist_ok=True)
    lines = ['Before / after excerpts of the mix (sound v3). Each file: BEFORE (%s), 1 s of silence, AFTER (%s).'
             % (os.path.relpath(A.before, A.out), os.path.relpath(A.after, A.out)),
             'Film times in seconds. 48 kHz 24-bit stereo.' +
             (' The BEFORE half is gained so the narration matches the AFTER half (same voice; you hear the bed\'s'
              ' change, not the 2 dB delivery change from -16 to -14 LUFS).' if A.match_voice else ''), '']
    for k, (t0, t1, lab, what) in enumerate(MOMENTS, 1):
        b = rd(os.path.join(A.before, 'mix.wav'), t0, t1); a = rd(os.path.join(A.after, 'mix.wav'), t0, t1)
        g = 0.0
        if A.match_voice:
            vb = rd(os.path.join(A.before, 'stems', 'voice_en.wav'), t0, t1)
            va = rd(os.path.join(A.after, 'stems', 'voice_en.wav'), t0, t1)
            g = SX.lufs_int(va) - SX.lufs_int(vb)
            b = b * np.float32(10 ** (g / 20))
        pk = max(float(np.abs(b).max()), float(np.abs(a).max()))
        if pk > 0.98:                                  # never clip the comparison (both halves scaled alike)
            b *= 0.98 / pk; a *= 0.98 / pk
        f = int(0.01 * SR)
        for y in (a, b):
            y[:f] *= np.linspace(0, 1, f)[:, None]; y[-f:] *= np.linspace(1, 0, f)[:, None]
        y = np.concatenate([b, np.zeros((SR, 2), np.float32), a])
        name = '%02d_%s_%03d-%03ds.wav' % (k, lab, int(t0), int(t1))
        sf.write(os.path.join(A.out, name), y, SR, subtype='PCM_24')
        lb, la = SX.lufs_int(b), SX.lufs_int(a)
        lines.append('%s  %.1f-%.1f s: %s. Before %.1f LUFS%s, after %.1f LUFS.'
                     % (name, t0, t1, what, lb, ' (gained %+.1f dB)' % g if A.match_voice else '', la))
        print(lines[-1])
    open(os.path.join(A.out, 'README.txt'), 'w').write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
