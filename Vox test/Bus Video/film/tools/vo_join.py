"""Join the owner's seven voiceover parts into one take (English narration of the Doctor film).
    python3 vo_join.py            -> W/narration/raw/narration_raw_44k.wav (44.1 kHz mono, float32) + raw/joins.json
                                     + W/narration/tests/join_seams.png
The seven parts (raw/part1.wav ... part7.wav: 44.1 kHz stereo 16-bit, L = R within 0.002, peaks limited at 0.705)
are consecutive slices of ONE continuous TTS stream: each part ends with a few ms of digital zeros (85-827 samples:
the exporter's padding) and the next part starts inside the same sound. Measured (this file's analysis, kept in
joins.json):
  - no part repeats audio of the one before (normalised cross-correlation of every part's first 0.15-0.6 s against
    the last 6 s of the part before stays under 0.52; a re-used rendition would read > 0.9);
  - both recognisers (Parakeet TDT, Whisper base.en) read every seam's concatenation as the script, each word once:
    "Day or night. I me|an it.", "...a pen on paper. | Something in our hallway", "bolted toge|ther. Fluorescent
    lights", "Then me. Ev|ery face of every person", "right now|. The chair next to his", "For real|. If something";
  - an LPC prediction (order 24, from the last 30 ms of part k) meets part k+1's first samples best a few samples
    later (0-43 samples, < 1 ms): the exporter dropped about that much at each cut.
So the join is a plain concatenation: the trailing zeros go, and the missing samples at each cut are filled by a blend
of the forward prediction from part k and the backward prediction from part k+1 (no lost audio); where no clear
continuation is found (a fricative, a quiet tail) part k+1's first 1.5 ms fade in from part k's forward prediction so
there is no step at the cut. The mono mix is (L + R) / 2. The script's "Together." at the start of part 4 is the "-ther" of "together" (part 3 ends
on "...bolted toge").
"""
import json, os
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
W = os.path.join(FILM, '_work')
RAWDIR = os.path.join(W, 'narration', 'raw')
OUT = os.path.join(RAWDIR, 'narration_raw_44k.wav')
JOINS = os.path.join(RAWDIR, 'joins.json')
TESTS = os.path.join(W, 'narration', 'tests')
NPARTS = 7


def lpc(a, order):
    import librosa
    return librosa.lpc(np.asarray(a, dtype=np.float64), order=order)


def predict(hist, A, n):
    order = len(A) - 1
    buf = list(hist[-order:])
    for _ in range(n):
        buf.append(-np.dot(A[1:], buf[-1:-order - 1:-1]))
    return np.array(buf[order:])


def best_gap(x, y, sr, order=24, max_gap=64):
    """Missing samples between the end of x and the start of y: the offset where x's forward LPC prediction meets
    y's first 80 samples best. Returns (gap, error ratio at gap, error at 0, fill samples)."""
    a = x[-int(0.030 * sr):]
    A = lpc(a, order)
    pred = predict(a, A, max_gap + 80)
    tgt = y[:80]
    err = np.array([np.sum((pred[o:o + 80] - tgt) ** 2) / (np.sum(tgt ** 2) + 1e-12) for o in range(max_gap + 1)])
    g = int(np.argmin(err))
    if err[g] > 0.6 or err[0] - err[g] < 0.1:                       # noise-like or no clear continuation: no fill
        g = 0
    fill = np.zeros(0)
    if g:
        fwd = pred[:g]
        b = y[:int(0.030 * sr)][::-1]                               # backward prediction from y
        Bk = lpc(b, order)
        bwd = predict(b, Bk, g)[::-1]
        w = (np.arange(g) + 0.5) / g
        fill = fwd * (1 - w) + bwd * w
    return g, float(err[g]), float(err[0]), fill


def main():
    parts, info = [], []
    sr0 = None
    for k in range(1, NPARTS + 1):
        x, sr = sf.read(os.path.join(RAWDIR, f'part{k}.wav'), dtype='float64', always_2d=True)
        sr0 = sr0 or sr
        assert sr == sr0, (k, sr)
        m = x.mean(axis=1)
        nz = np.where(np.abs(m) > 0)[0]
        tz = len(m) - 1 - nz[-1]
        if k < NPARTS: m = m[:nz[-1] + 1]                          # the exporter's zero padding (the last part keeps its tail)
        parts.append(m)
        info.append({'part': k, 'samples': int(len(x)), 'duration': round(len(x) / sr, 3), 'trailing_zeros': int(tz),
                     'lr_max_diff': round(float(np.abs(x[:, 0] - x[:, 1]).max()), 4), 'peak': round(float(np.abs(x).max()), 4)})
    out = [parts[0]]
    seams = []
    pos = len(parts[0])
    for k in range(1, NPARTS):
        g, e, e0, fill = best_gap(parts[k - 1], parts[k], sr0)
        out.append(fill); pos += len(fill)
        seams.append({'between': [k, k + 1], 'at': round(pos / sr0, 4), 'filled_samples': g,
                      'lpc_err_at_fill': round(e, 3), 'lpc_err_no_fill': round(e0, 3)})
        nxt = parts[k].copy()
        if g == 0:                                                  # no clear continuation (noise, a quiet tail): the
            n = int(0.0015 * sr0)                                   # first 1.5 ms of part k+1 fade in from part k's
            a = parts[k - 1][-int(0.030 * sr0):]                    # forward prediction (no step at the cut)
            pr = predict(a, lpc(a, 24), n)
            w = np.sin((np.arange(n) + 0.5) / n * np.pi / 2) ** 2
            nxt[:n] = pr * (1 - w) + nxt[:n] * w
            seams[-1]['blend_ms'] = 1.5
        out.append(nxt); pos += len(nxt)
    y = np.concatenate(out)
    sf.write(OUT, y.astype(np.float32), sr0, subtype='FLOAT')
    json.dump({'sr': sr0, 'duration': round(len(y) / sr0, 3), 'parts': info, 'seams': seams,
               'method': __doc__.strip().split('\n')[2].strip()}, open(JOINS, 'w'), indent=1)
    for s in seams: print('seam %d/%d at %8.3f s: %2d samples filled (LPC err %.2f vs %.2f unfilled)'
                          % (s['between'][0], s['between'][1], s['at'], s['filled_samples'], s['lpc_err_at_fill'], s['lpc_err_no_fill']))
    print(f'{OUT}: {len(y) / sr0:.2f} s')
    # seam picture: +-40 ms waveform and the 1-6 kHz residual (a click shows as a spike)
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    from scipy import signal
    os.makedirs(TESTS, exist_ok=True)
    hp = signal.sosfiltfilt(signal.butter(4, 3000, 'highpass', fs=sr0, output='sos'), y)
    fig, axs = plt.subplots(2, len(seams), figsize=(4 * len(seams), 6))
    for c, s in enumerate(seams):
        i = int(s['at'] * sr0); a, b = i - int(0.04 * sr0), i + int(0.04 * sr0)
        t = (np.arange(a, b) - i) / sr0 * 1000
        axs[0, c].plot(t, y[a:b], lw=0.7); axs[0, c].axvline(0, color='r', lw=0.5)
        axs[0, c].set_title('seam %d/%d at %.3f s (%d filled)' % (s['between'][0], s['between'][1], s['at'], s['filled_samples']), fontsize=8)
        axs[1, c].plot(t, hp[a:b], lw=0.7, color='g'); axs[1, c].axvline(0, color='r', lw=0.5)
        axs[1, c].set_title('> 3 kHz residual', fontsize=8); axs[1, c].set_xlabel('ms')
    plt.tight_layout(); plt.savefig(os.path.join(TESTS, 'join_seams.png'), dpi=70)


if __name__ == '__main__':
    main()
