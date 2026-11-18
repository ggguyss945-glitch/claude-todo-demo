"""Join the owner's two voiceover parts into one take (English narration of the Bus film).
    python3 vo_join.py   -> W/narration/raw/narration_raw_24k.wav (24 kHz mono float32) + raw/joins.json
part1.wav (7:00.01) and part2.wav (5:21.82) are 24 kHz mono 16-bit slices of ONE continuous TTS stream (the owner cut it
with an online cutter): part1 ends inside the decay of "She shoves her phone at me." and part2 starts in the same decay,
0.14 s before the silence ahead of "The bars are back." (part2 also ends on 0.10 s of digital zeros, part1 starts on 0.10 s).
Measured (kept in joins.json): Parakeet reads the last 6 s of part1 + the first 6 s of part2 as "...She shoves her phone
at me. The bars are back. Call nine one one. Then belt on." (each word once; nothing lost or doubled); an LPC
prediction (order 24, last 30 ms of part1) meets part2 best 2 samples later (< 0.1 ms dropped by the cutter), but only
loosely (the decay is noisy), so part2's first 1.5 ms fade in from part1's forward prediction: no step at the cut. The
cut sits in the tail of "me." just before a silence (the edit replaces that silence by the pacing map's gap anyway).
"""
import json, os
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(os.path.dirname(HERE), '_work')
RAWDIR = os.path.join(W, 'narration', 'raw')
OUT = os.path.join(RAWDIR, 'narration_raw_24k.wav')
JOINS = os.path.join(RAWDIR, 'joins.json')


def main():
    import librosa
    a, sr = sf.read(os.path.join(RAWDIR, 'part1.wav'), dtype='float64')
    b, sr2 = sf.read(os.path.join(RAWDIR, 'part2.wav'), dtype='float64')
    assert sr == sr2 == 24000
    A = librosa.lpc(a[-int(0.03 * sr):], order=24)
    h = list(a[-24:]); pred = []
    for _ in range(64):
        v = -np.dot(A[1:], h[::-1][:24]); pred.append(v); h.append(v)
    pred = np.array(pred)
    errs = [float(np.sqrt(np.mean((pred[o:o + 10] - b[:10]) ** 2))) for o in range(30)]
    gap = int(np.argmin(errs))
    n = int(0.0015 * sr)
    w = 0.5 - 0.5 * np.cos(np.pi * (np.arange(n) + 0.5) / n)
    fill = pred[:gap]
    head = b[:n] * w + pred[gap:gap + n] * (1 - w)
    y = np.concatenate([a, fill, head, b[n:]])
    sf.write(OUT, y.astype(np.float32), sr, subtype='FLOAT')
    rec = {'parts': ['part1.wav', 'part2.wav'], 'sr': sr, 'seam_s': round(len(a) / sr, 4), 'lpc_gap_samples': gap,
           'lpc_err': round(errs[gap], 4), 'step_before': round(abs(b[0] - a[-1]), 4), 'duration': round(len(y) / sr, 3),
           'seam_text': 'She shoves her phone at me.| The bars are back.'}
    json.dump(rec, open(JOINS, 'w'), indent=1)
    print(rec)


if __name__ == '__main__':
    main()
