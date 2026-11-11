"""snd_env.py: loudness / band / onset envelopes of a mix and its voice and bed, for the sound study (sound v3).

    python3 analysis/refmirror/snd_env.py NAME OUT.npz --mix MIX.wav [--bed BED.wav --voice VOICE.wav]
    python3 analysis/refmirror/snd_env.py ours OUT.npz --stems _work/mix/final_v2      (mix.wav + stems/{voice_en,music,sfx})

References: the bed and voice come from separate_ref.py (UVR, bed = mix - voice). Ours: bed = music + sfx stems.
Everything is resampled to 48 kHz and measured with the BS.1770 K-weighting of audio/sfx.py (both channels).
Saves at 10 Hz (t = k / 10, block centred): mix_M / bed_M / voice_M (400 ms momentary, LUFS), mix_S / bed_S (3 s
short-term), bed band levels (dB, 400 ms, bands below), bed onset strength (spectral flux, 100 Hz), and the
integrated loudness of mix and voice. analysis/refmirror/snd_study.py turns these into the study's numbers.
"""
import argparse, os, sys
import numpy as np, soundfile as sf, soxr
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'audio'))
import sfx as SX  # noqa: E402

SR = 48000
BANDS = ((20, 60), (60, 250), (250, 1000), (1000, 4000), (4000, 12000))


def load(p):
    x, sr = sf.read(p, dtype='float32', always_2d=True)
    if x.shape[1] == 1:
        x = np.repeat(x, 2, 1)
    if sr != SR:
        x = soxr.resample(x, sr, SR).astype(np.float32)
    return x


def lev(x, win, hop=0.1):
    """K-weighted block loudness every hop, blocks centred on k * hop (padded)."""
    pad = int(win / 2 * SR)
    y = np.pad(x, ((pad, pad), (0, 0)))
    return (-0.691 + 10 * np.log10(SX._blocks(y, win, hop) + 1e-20)).astype(np.float32)


def bands(x, hop=0.1, win=0.4):
    m = x.mean(1)
    out = []
    for lo, hi in BANDS:
        sos = signal.butter(4, [lo, hi], 'bandpass', fs=SR, output='sos')
        y = signal.sosfilt(sos, m).astype(np.float64)
        c = np.concatenate([[0.0], np.cumsum(y * y)]); w = int(win * SR); h = int(hop * SR)
        i = np.arange(0, len(m), h); a = np.clip(i - w // 2, 0, len(m)); b = np.clip(i + w // 2, 0, len(m))
        p = (c[b] - c[a]) / np.maximum(1, b - a)
        out.append(10 * np.log10(p + 1e-14))
    return np.array(out, np.float32)


def flux(x, hop=0.01):
    """Positive spectral flux of the bed above 300 Hz (log magnitude), 100 Hz rate: the SFX / transient activity."""
    m = x.mean(1).astype(np.float32); h = int(hop * SR); C = 60 * SR; out = []
    for a in range(0, len(m), C):                        # 60 s chunks (the STFT of a whole film is > 1 GB)
        seg = m[a:a + C]
        f, t, Z = signal.stft(seg, SR, nperseg=2048, noverlap=2048 - h, boundary=None, padded=False)
        A = np.log1p(1000 * np.abs(Z[f > 300]))
        out.append(np.maximum(0, np.diff(A, axis=1)).mean(0)[:len(seg) // h])
    d = np.concatenate(out)
    return np.concatenate([[0], d]).astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('name'); ap.add_argument('out')
    ap.add_argument('--mix'); ap.add_argument('--bed'); ap.add_argument('--voice'); ap.add_argument('--stems')
    ap.add_argument('--t0', type=float, default=0.0); ap.add_argument('--t1', type=float, default=None)
    A = ap.parse_args()
    if A.stems:
        mix = load(os.path.join(A.stems, 'mix.wav'))
        voice = load(os.path.join(A.stems, 'stems', 'voice_en.wav'))
        bed = load(os.path.join(A.stems, 'stems', 'music.wav'))
        bed += load(os.path.join(A.stems, 'stems', 'sfx.wav'))[:len(bed)]
    else:
        mix = load(A.mix)
        voice = load(A.voice) if A.voice else None
        bed = load(A.bed) if A.bed else None
    n = len(mix)
    for y in (voice, bed):
        if y is not None:
            n = min(n, len(y))
    a, b = int(A.t0 * SR), int((A.t1 or n / SR) * SR)
    mix = mix[a:b]
    R = dict(name=A.name, dur=len(mix) / SR, I_mix=SX.lufs_int(mix), mix_M=lev(mix, 0.4), mix_S=lev(mix, 3.0))
    if voice is not None:
        voice = voice[a:b]
        R.update(I_voice=SX.lufs_int(voice), voice_M=lev(voice, 0.4))
    if bed is not None:
        bed = bed[a:b]
        R.update(bed_M=lev(bed, 0.4), bed_S=lev(bed, 3.0), bed_B=bands(bed), bed_F=flux(bed), I_bed=SX.lufs_int(bed))
    np.savez_compressed(A.out, **R)
    print(A.name, 'dur %.1f I_mix %.2f' % (R['dur'], R['I_mix']), 'I_voice %.2f' % R.get('I_voice', np.nan),
          'I_bed %.2f' % R.get('I_bed', np.nan), '->', A.out)


if __name__ == '__main__':
    main()
