"""review_doctor.py: batch measurement of the Doctor film's new Epidemic effects (W/samples/epidemic, flat folder) for
the per-file verdicts in W/mix/sfx_review.md: duration, integrated / momentary-max loudness, sample peak, clipped
samples, noise floor (10th percentile of 50 ms RMS), crest, spectral centroid, band shares (<250 Hz / 250 Hz-4 kHz /
>4 kHz), the strongest spectral peak (bells, hums, tones), onsets per second, stereo correlation; plus one spectrogram
contact sheet (W/mix/review/spectro_sheet.jpg, each tile with its envelope). Writes W/mix/review/measures.json.
    python3 review_doctor.py
"""
import json, os, sys
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import epidemic_catalog as EC

W = os.path.normpath(os.path.join(HERE, '..', '_work'))
D = os.path.join(W, 'samples', 'epidemic')
OUT = os.path.join(W, 'mix', 'review')


def measure(p):
    import pyloudnorm, librosa
    x, sr = sf.read(p, dtype='float32', always_2d=True)
    x = x[:, :2] if x.shape[1] > 1 else np.repeat(x, 2, 1)
    m = x.mean(1)
    meter = pyloudnorm.Meter(sr)
    L = meter.integrated_loudness(x) if len(x) > 0.5 * sr else float('nan')
    k = int(0.05 * sr)
    rms = np.sqrt(np.mean(m[:len(m) // k * k].reshape(-1, k) ** 2, 1) + 1e-12) if len(m) > k else np.array([1e-6])
    rdb = 20 * np.log10(rms)
    S = np.abs(np.fft.rfft(m[:sr * 30] * np.hanning(min(len(m), sr * 30)))) ** 2
    f = np.fft.rfftfreq(min(len(m), sr * 30), 1 / sr)
    tot = S.sum() + 1e-20
    sel = f > 40
    fpk = float(f[sel][np.argmax(S[sel])])
    y = librosa.resample(m, orig_sr=sr, target_sr=22050)
    on = librosa.onset.onset_detect(y=y, sr=22050, units='time')
    cent = float(np.median(librosa.feature.spectral_centroid(y=y, sr=22050)[0]))
    c = np.corrcoef(x[:, 0], x[:, 1])[0, 1] if x[:, 0].std() > 0 and x[:, 1].std() > 0 else 1.0
    return {'dur': round(len(x) / sr, 2), 'sr': sr, 'lufs': None if not np.isfinite(L) else round(float(L), 1),
            'peak_db': round(float(20 * np.log10(np.abs(x).max() + 1e-9)), 1),
            'clipped': int((np.abs(x) > 0.999).sum()), 'floor_db': round(float(np.percentile(rdb, 10)), 1),
            'loud_db': round(float(np.percentile(rdb, 95)), 1), 'crest': round(float(np.percentile(rdb, 95) - np.percentile(rdb, 10)), 1),
            'centroid': int(cent), 'low_mid_high': [round(100 * float(S[f < 250].sum() / tot), 1),
                                                   round(100 * float(S[(f >= 250) & (f < 4000)].sum() / tot), 1),
                                                   round(100 * float(S[f >= 4000].sum() / tot), 1)],
            'peak_hz': int(fpk), 'onsets_s': round(len(on) / max(0.5, len(x) / sr), 2), 'corr': round(float(c), 2)}


def sheet(files, out):
    import librosa
    from PIL import Image, ImageDraw
    cols, tw, th = 6, 210, 92
    rows = (len(files) + cols - 1) // cols
    im = Image.new('RGB', (cols * tw, rows * th), (16, 16, 18)); dr = ImageDraw.Draw(im)
    for k, (slug, p) in enumerate(files):
        y, sr = librosa.load(p, sr=16000, mono=True, duration=40)
        Sg = librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=512, hop_length=max(64, len(y) // 200))), ref=np.max)
        Sg = np.clip((Sg + 70) / 70, 0, 1)[::-1]
        a = (255 * Sg).astype(np.uint8)
        t = Image.fromarray(a).resize((tw - 4, th - 18)).convert('RGB')
        r, c = divmod(k, cols)
        im.paste(t, (c * tw + 2, r * th + 16))
        dr.text((c * tw + 3, r * th + 2), f'{k:02d} {slug[:31]}', fill=(230, 220, 120))
    im.save(out, quality=88)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    files = [(EC.slugify(os.path.splitext(f)[0]), os.path.join(D, f)) for f in sorted(os.listdir(D))
             if not EC._is_music(f)]
    res = {}
    for k, (slug, p) in enumerate(files):
        res[slug] = dict(measure(p), idx=k, file=os.path.basename(p))
    json.dump(res, open(os.path.join(OUT, 'measures.json'), 'w'), indent=1)
    for slug, r in res.items():
        print(f"{r['idx']:02d} {slug[:58]:58s} {r['dur']:6.1f}s L{r['lufs']} pk{r['peak_db']} clip{r['clipped']} "
              f"fl{r['floor_db']} cr{r['crest']} c{r['centroid']} b{r['low_mid_high']} f{r['peak_hz']} on{r['onsets_s']} "
              f"cor{r['corr']}")
    sheet(files, os.path.join(OUT, 'spectro_sheet.jpg'))
