"""review_sfx.py: measure the owner's new Epidemic files for this film (W/samples/epidemic: the bunny set) so each one
can be judged before it is used (use / process / reject: the decisions and reasons are in W/mix/sfx_review.md).

    python3 audio/review_sfx.py [--kind sfx|music|all] [--no-asr] [--only <substring>]      (from film/)

For every file (mono analysis unless noted):
    dur, LUFS (BS.1770, sfx.lufs_int), sample peak, true peak (4x), clipped samples (|x| >= 0.999) and the longest run
    noise floor = 5th percentile of the 50 ms RMS (dBFS), active level = its 95th percentile, their difference (SNR)
    spectrum over the active frames: centroid and 95 % roll-off medians, energy share < 250 Hz / 250 Hz-4 kHz / > 4 kHz,
    the codec's low-pass (highest frequency where the long-term spectrum is within 60 dB of its 1-5 kHz level)
    onsets per second; harmonic share (HPSS); tonal clarity (median of the chroma max / mean: a band or a tune is > 2.5)
    stereo: L/R correlation and side-minus-mid (dB)
    speech: Silero VAD share and the words Parakeet hears (crowds, voices, hospital ambiences; --no-asr skips it)
Draws one strip per file (log-frequency spectrogram 30 Hz-20 kHz with the 50 ms RMS envelope under it) into contact
sheets W/mix/review/sheet_<kind>_NN.png (6 files per sheet) and writes W/mix/review/review_measure.json.
"""
import json, os, re, sys, warnings
import numpy as np, soundfile as sf
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sfx as SX                                            # noqa: E402

W = SX.W
SET = os.path.join(W, 'samples', 'epidemic')
OUT = os.path.join(W, 'mix', 'review')
MODELS = '/tmp/claude-0/-home-user-claude-todo-demo/aa250ae7-a0b4-594f-9bc6-bd18b596cf27/scratchpad/models'
SR = 48000
ASR_WORDS = ('crowd', 'voices', 'hospital', 'ambience', 'fight', 'efforts', 'cheer')


def slug(f):
    import epidemic_catalog as EC
    return EC.slugify(os.path.splitext(f)[0])


def measure(path):
    x, sr = sf.read(path, dtype='float32', always_2d=True)
    if sr != SR:
        import soxr
        x = soxr.resample(x, sr, SR).astype(np.float32)
    st = x[:, :2] if x.shape[1] > 1 else np.repeat(x, 2, 1)
    m = st.mean(1)
    n = len(m)
    r = {'dur': round(n / SR, 2), 'channels': int(x.shape[1])}
    r['lufs'] = round(SX.lufs_int(st), 1) if n > SR * 0.4 else round(SX.mom_max(st), 1)
    r['peak_db'] = round(float(SX.db(np.abs(st).max())), 1)
    up = signal.resample_poly(st[:SR * 120], 4, 1, axis=0) if n > 0 else st
    r['true_peak_db'] = round(float(SX.db(np.abs(up).max())), 1)
    cl = np.abs(st).max(1) >= 0.999
    r['clipped'] = int(cl.sum())
    if cl.any():
        d = np.diff(np.concatenate([[0], cl.astype(int), [0]]))
        r['clip_run_max'] = int((np.flatnonzero(d == -1) - np.flatnonzero(d == 1)).max())
    k = int(0.05 * SR)
    nb = max(1, n // k)
    rms = np.sqrt((m[:nb * k].reshape(nb, k) ** 2).mean(1) + 1e-20)
    rdb = SX.db(rms)
    r['floor_db'] = round(float(np.percentile(rdb, 5)), 1)
    r['active_db'] = round(float(np.percentile(rdb, 95)), 1)
    r['snr_db'] = round(r['active_db'] - r['floor_db'], 1)
    f, t, Z = signal.stft(m, SR, nperseg=4096, noverlap=3072, boundary=None)
    P = np.abs(Z) ** 2
    fe = P.sum(0)
    act = fe > np.percentile(fe, 40)
    if act.sum() < 3:
        act = fe > 0
    Pa = P[:, act]
    cen = (f[:, None] * Pa).sum(0) / (Pa.sum(0) + 1e-20)
    cs = np.cumsum(Pa, 0) / (Pa.sum(0) + 1e-20)
    roll = f[np.argmax(cs >= 0.95, axis=0)]
    r['centroid_hz'] = int(np.median(cen))
    r['rolloff95_hz'] = int(np.median(roll))
    tot = Pa.sum() + 1e-20
    r['low_mid_high_pct'] = [round(100 * float(Pa[f < 250].sum() / tot), 1),
                             round(100 * float(Pa[(f >= 250) & (f < 4000)].sum() / tot), 1),
                             round(100 * float(Pa[f >= 4000].sum() / tot), 1)]
    lt = 10 * np.log10(Pa.mean(1) + 1e-30)
    ref = float(np.median(lt[(f > 1000) & (f < 5000)]))
    hi = np.flatnonzero(lt > ref - 60)
    r['codec_lowpass_hz'] = int(f[hi[-1]]) if len(hi) else None
    import librosa
    y22 = librosa.resample(m, orig_sr=SR, target_sr=22050)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        on = librosa.onset.onset_detect(y=y22, sr=22050, units='time')
        r['onsets_per_s'] = round(len(on) / max(0.5, n / SR), 2)
        Hs, Ps = librosa.decompose.hpss(np.abs(librosa.stft(y22[:22050 * 90], n_fft=2048, hop_length=512)) ** 2)
        r['harmonic_pct'] = round(100 * float(Hs.sum() / (Hs.sum() + Ps.sum() + 1e-20)), 1)
        ch = librosa.feature.chroma_stft(y=y22[:22050 * 90], sr=22050, hop_length=2048)
        cm = ch.max(0) / (ch.mean(0) + 1e-9)
        r['tonal_clarity'] = round(float(np.median(cm)), 2)
    if st.shape[1] == 2 and np.std(st[:, 0]) > 0 and np.std(st[:, 1]) > 0:
        r['lr_corr'] = round(float(np.corrcoef(st[:, 0], st[:, 1])[0, 1]), 2)
        s_ = (st[:, 0] - st[:, 1]) * 0.5
        r['side_minus_mid_db'] = round(float(10 * np.log10((s_ ** 2).mean() + 1e-20) - 10 * np.log10((m ** 2).mean() + 1e-20)), 1)
    return r, m, rdb


_ASR = None


def asr(m):
    """Speech share (Silero VAD) and the words Parakeet hears."""
    global _ASR
    import sherpa_onnx, soxr
    pk = os.path.join(MODELS, 'sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8')
    if _ASR is None:
        _ASR = sherpa_onnx.OfflineRecognizer.from_transducer(
            encoder=f'{pk}/encoder.int8.onnx', decoder=f'{pk}/decoder.int8.onnx', joiner=f'{pk}/joiner.int8.onnx',
            tokens=f'{pk}/tokens.txt', model_type='nemo_transducer', num_threads=1)
    x16 = soxr.resample(m, SR, 16000).astype(np.float32)
    cfg = sherpa_onnx.VadModelConfig(); cfg.silero_vad.model = os.path.join(MODELS, 'vad.onnx')
    cfg.silero_vad.threshold = 0.5; cfg.silero_vad.min_silence_duration = 0.3
    cfg.silero_vad.min_speech_duration = 0.25; cfg.silero_vad.max_speech_duration = 12; cfg.sample_rate = 16000
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=400)
    segs = []
    for i in range(0, len(x16), 512):
        vad.accept_waveform(x16[i:i + 512])
        while not vad.empty():
            segs.append((vad.front.start / 16000, len(vad.front.samples) / 16000)); vad.pop()
    vad.flush()
    while not vad.empty():
        segs.append((vad.front.start / 16000, len(vad.front.samples) / 16000)); vad.pop()
    words = []
    for a, d in segs[:40]:
        s = _ASR.create_stream(); s.accept_waveform(16000, x16[int(a * 16000):int((a + d) * 16000)])
        _ASR.decode_stream(s)
        if s.result.text.strip():
            words.append(f'{a:.1f}s: {s.result.text.strip()}')
    return round(100 * sum(d for _, d in segs) / (len(x16) / 16000), 1), words


def strip(ax, ax2, m, rdb, title):
    f, t, S = signal.spectrogram(m, SR, nperseg=2048, noverlap=1536)
    S = 10 * np.log10(S + 1e-14)
    vmax = np.percentile(S, 99.5)
    ax.pcolormesh(t, f, S, shading='auto', cmap='magma', vmin=vmax - 80, vmax=vmax, rasterized=True)
    ax.set_yscale('log'); ax.set_ylim(30, 20000)
    ax.set_yticks([50, 100, 250, 1000, 4000, 16000]); ax.set_yticklabels(['50', '100', '250', '1k', '4k', '16k'], fontsize=6)
    ax.tick_params(axis='x', labelsize=6)
    ax.set_title(title, fontsize=7, loc='left')
    tt = np.arange(len(rdb)) * 0.05
    ax2.plot(tt, rdb, lw=0.6, color='k'); ax2.set_ylim(-90, 0); ax2.set_xlim(0, max(tt[-1], 0.1))
    ax2.set_yticks([-80, -40, 0]); ax2.tick_params(labelsize=6); ax2.grid(alpha=0.3)
    ax.set_xlim(0, max(tt[-1], 0.1))


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    kind = 'all'
    if '--kind' in sys.argv:
        kind = sys.argv[sys.argv.index('--kind') + 1]
    only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else None
    do_asr = '--no-asr' not in sys.argv
    os.makedirs(OUT, exist_ok=True)
    pj = os.path.join(OUT, 'review_measure.json')
    res = json.load(open(pj)) if os.path.exists(pj) else {}
    for kd in (('sfx', 'music') if kind == 'all' else (kind,)):
        files = sorted(f for f in os.listdir(os.path.join(SET, kd)) if f.lower().endswith(('.mp3', '.wav')))
        if only:
            files = [f for f in files if only in slug(f)]
        per = 6
        for si in range(0, len(files), per):
            fig = plt.figure(figsize=(16, 2.0 * per), dpi=100)
            gs = fig.add_gridspec(per * 3, 1, hspace=0.9)
            for j, fn in enumerate(files[si:si + per]):
                sl = slug(fn)
                r, m, rdb = measure(os.path.join(SET, kd, fn))
                if do_asr and kd == 'sfx' and any(w in sl for w in ASR_WORDS):
                    r['speech_pct'], r['asr'] = asr(m)
                res[f'{kd}:{sl}'] = dict(r, file=fn, kind=kd)
                print(kd, sl, json.dumps({k: v for k, v in r.items() if k != 'asr'}), flush=True)
                if r.get('asr'):
                    print('    ASR:', ' | '.join(r['asr'])[:600], flush=True)
                ax = fig.add_subplot(gs[j * 3:j * 3 + 2, 0]); ax2 = fig.add_subplot(gs[j * 3 + 2, 0])
                strip(ax, ax2, m if kd == 'sfx' else m[:SR * 240], rdb if kd == 'sfx' else rdb[:20 * 240],
                      f"{sl[:110]}  |  {r['dur']} s, {r['lufs']} LUFS, pk {r['peak_db']} (TP {r['true_peak_db']}), floor "
                      f"{r['floor_db']} SNR {r['snr_db']}, cen {r['centroid_hz']} Hz, L/M/H {r['low_mid_high_pct']}, "
                      f"lp {r['codec_lowpass_hz']}, tonal {r['tonal_clarity']}, harm {r['harmonic_pct']}%"
                      + (f", speech {r['speech_pct']}%" if 'speech_pct' in r else '') + (f", CLIP {r['clipped']}" if r['clipped'] else ''))
            fig.savefig(os.path.join(OUT, f'sheet_{kd}_{si // per + 1:02d}.png'), bbox_inches='tight')
            plt.close(fig)
            json.dump(res, open(pj, 'w'), indent=1)
    print('wrote', pj)


if __name__ == '__main__':
    main()
