#!/usr/bin/env python3
"""voice_ingest.py - measure, conform and register one voice line.

    python3 -I audio/voice_ingest.py <wav> --id S00-L006 --role SAM --text "In my defense... I only changed ONE thing."
        [--tag nervous] [--out <conformed.wav>] [--update audio/voice_lines.json] [--approach "fish audio"] [--no-conform]

Works for any WAV/MP3 (our Kokoro takes or the owner's Fish Audio files), so a Fish take replaces ours with no other change:
  1. conform: mono, 48 kHz, leading/trailing silence trimmed to 30 ms handles, loudness matched to the role target
     (ROLE_LUFS), peak <= -1 dBFS (a 1.5 ms look-ahead limiter only touches stray peaks);
  2. words: Parakeet-TDT ASR (sherpa-onnx) token times, aligned to the script words, edges refined on the energy envelope;
  3. visemes: RMS at 60 fps + spectral centroid inside word windows (production_bible 3.2 lip-sync rule), holds 3-8 frames;
  4. metrics: ASR word accuracy, pitch (pYIN), rate, pauses, loudness, artifact proxies (clipping, HNR, jitter, shimmer,
     F0 jumps, spectral clicks), DNSMOS, formant spacing, speaker similarity to the role's other lines.
With --update the entry {id, role, tag, text, file, dur, words, visemes, metrics, approach} replaces the one with the same id.
Times are seconds from the start of the conformed file.
"""
import argparse, json, os, re, sys, warnings
import numpy as np

warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
SCRATCH = '/tmp/claude-0/-home-user-claude-todo-demo/353ac1d9-152b-55bb-bdf1-0625e0fc6a83/scratchpad'
MODELS = os.environ.get('VOICE_MODELS', SCRATCH + '/models')
VOICE_DIR = os.environ.get('VOICE_DIR', SCRATCH + '/settings/voice')
LINES_JSON = os.path.join(HERE, 'voice_lines.json')

SR_OUT = 48000
HANDLE = 0.030
PEAK_DB = -1.0
# Dry-stem loudness per role (integrated LUFS). All roles sit at the same level; the mix sets the balance.
ROLE_LUFS = {'N': -20.0, 'SYS': -20.0, 'SAM': -20.0, 'DAD': -20.0, 'MOM': -20.0, 'LILY': -20.0,
             'PICKLES': -20.0, 'BRIGGS': -20.0, 'KEVIN': -20.0}
FPS = 60
VIS_REF_LUFS = -20.0          # viseme dBFS thresholds are applied as if the line sat at this loudness
VIS_CLOSED_DB, VIS_SMALL_DB = -40.0, -28.0
VIS_E_HZ, VIS_O_HZ = 1800.0, 1150.0
NARR_DF = 1180.0              # reference adult-male formant spacing; viseme centroid thresholds scale with dF / this

# ----------------------------------------------------------------------------------------------- audio io

def load(path):
    import soundfile as sf
    try:
        y, sr = sf.read(path, dtype='float32', always_2d=True)
        y = y.mean(1)
    except Exception:
        import librosa
        y, sr = librosa.load(path, sr=None, mono=True)
    return np.asarray(y, np.float32), int(sr)


def resample(y, sr, to):
    if sr == to:
        return y.astype(np.float32)
    import soxr
    return soxr.resample(y.astype(np.float32), sr, to, quality='VHQ').astype(np.float32)


def lufs(y, sr):
    import pyloudnorm as pyln
    pad = np.zeros(int(0.5 * sr), np.float32)
    z = np.concatenate([pad, y, pad])
    try:
        v = pyln.Meter(sr).integrated_loudness(z.astype(np.float64))
    except Exception:
        v = -70.0
    return float(v) if np.isfinite(v) else -70.0


def env_db(y, sr, hop=0.01, win=0.02):
    import librosa
    h, w = max(1, int(hop * sr)), max(2, int(win * sr))
    r = librosa.feature.rms(y=y, frame_length=w, hop_length=h, center=True)[0]
    return 20 * np.log10(r + 1e-9)


def speech_mask(y, sr, rel_db=-35.0, bridge=0.15, hop=0.01):
    """10 ms frames that are speech: within rel_db of the loud level, gaps shorter than `bridge` filled."""
    d = env_db(y, sr, hop)
    ref = np.percentile(d, 95)
    m = d > ref + rel_db
    n = int(round(bridge / hop))
    idx = np.where(m)[0]
    if len(idx):
        for a, b in zip(idx[:-1], idx[1:]):
            if 1 < b - a <= n:
                m[a:b] = True
    return m


def trim_handles(y, sr, handle=HANDLE, rel_db=-50.0):
    d = env_db(y, sr, 0.005, 0.01)
    on = np.where(d > np.max(d) + rel_db)[0]
    if not len(on):
        return y
    s = max(0, int((on[0] * 0.005 - handle) * sr))
    e = min(len(y), int(((on[-1] + 1) * 0.005 + handle) * sr))
    out = y[s:e].copy()
    f = int(0.004 * sr)
    if len(out) > 2 * f:
        out[:f] *= np.linspace(0, 1, f) ** 2
        out[-f:] *= np.linspace(1, 0, f) ** 2
    return out


def limit(y, sr, ceil_db=PEAK_DB, look=0.0015, rel=0.06):
    """Peak limiter: gain = min(1, ceil/|x|) smoothed with look-ahead (min filter) and release."""
    ceil = 10 ** (ceil_db / 20) * 0.995
    a = np.abs(y)
    if a.max() <= ceil:
        return y
    g = np.minimum(1.0, ceil / (a + 1e-12))
    from scipy.ndimage import minimum_filter1d
    L = max(1, int(look * sr))
    g = minimum_filter1d(g, 2 * L + 1)
    r = np.exp(-1.0 / (rel * sr))
    out = np.empty_like(g)
    cur = 1.0
    for i in range(len(g)):            # release smoothing (attack is instant thanks to the min filter)
        cur = g[i] if g[i] < cur else g[i] + (cur - g[i]) * r
        out[i] = cur
    y2 = y * out
    return np.clip(y2, -ceil, ceil)


def conform(y, sr, role, target_lufs=None):
    y = resample(y, sr, SR_OUT)
    y = y - np.mean(y)
    y = trim_handles(y, SR_OUT)
    tgt = ROLE_LUFS.get(role, -20.0) if target_lufs is None else target_lufs
    L = lufs(y, SR_OUT)
    y = y * 10 ** ((tgt - L) / 20)
    y = limit(y, SR_OUT, PEAK_DB)
    return y.astype(np.float32), SR_OUT

# ----------------------------------------------------------------------------------------------- text

def norm_word(w):
    w = w.lower().replace('’', "'")
    w = re.sub(r"[^a-z0-9']", '', w)
    return w.strip("'")


def script_words(text):
    """Script words as displayed (punctuation stripped, case kept) and their normalised forms."""
    raw = [t for t in re.split(r"[\s—]+|(?<=\.)\.+|\.\.\.", text.replace('-', ' ')) if t]
    disp, nrm = [], []
    for t in raw:
        n = norm_word(t)
        if n:
            disp.append(re.sub(r"^[^\w']+|[^\w']+$", '', t))
            nrm.append(n)
    return disp, nrm


ONES = 'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()
TENS = 'x x twenty thirty forty fifty sixty seventy eighty ninety'.split()
NUMW = set(ONES) | set(TENS[2:]) | {'hundred', 'thousand', 'million'}


def num_words(n):
    """412 -> ['four', 'hundred', 'twelve'] (no 'and'; the comparison drops 'and' between number words)."""
    if n < 20:
        return [ONES[n]]
    if n < 100:
        return [TENS[n // 10]] + ([ONES[n % 10]] if n % 10 else [])
    if n < 1000:
        return [ONES[n // 100], 'hundred'] + (num_words(n % 100) if n % 100 else [])
    if n < 1000000:
        return num_words(n // 1000) + ['thousand'] + (num_words(n % 1000) if n % 1000 else [])
    return [str(n)]


def hyp_norm(words):
    """ASR words -> comparable words: digits spelt out ('4,812' -> four thousand eight hundred twelve, '7D' -> seven d)."""
    out = []
    for w in words:
        w = w.replace(',', '') if re.fullmatch(r"[\d,]+[.?!]?", w) else w
        for part in re.findall(r"\d+|[A-Za-z']+", w):
            if part.isdigit():
                out += num_words(int(part))
            else:
                n = norm_word(part)
                if n:
                    out.append(n)
    return out


def drop_num_and(ws):
    return [w for i, w in enumerate(ws) if not (w == 'and' and 0 < i < len(ws) - 1 and ws[i - 1] in NUMW and ws[i + 1] in NUMW)]


SPELL = {'defence': 'defense', 'colour': 'color', 'favourite': 'favorite', 'realise': 'realize', 'okay': 'ok', 'mum': 'mom'}


def word_acc(ref_n, hyp_n):
    r = [SPELL.get(w, w).replace("'", '') for w in drop_num_and(ref_n)]      # planet's == planets; 412 == four hundred and twelve
    h = [SPELL.get(w, w).replace("'", '') for w in drop_num_and(hyp_n)]     # British spellings from the ASR
    D = np.zeros((len(r) + 1, len(h) + 1), int)
    D[:, 0] = range(len(r) + 1)
    D[0, :] = range(len(h) + 1)
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            D[i, j] = min(D[i - 1, j] + 1, D[i, j - 1] + 1, D[i - 1, j - 1] + (r[i - 1] != h[j - 1]))
    return (1 - D[-1, -1] / max(1, len(r))), int(D[-1, -1])

# ----------------------------------------------------------------------------------------------- models (lazy)
_M = {}


def asr_model():
    if 'asr' not in _M:
        import sherpa_onnx
        P = MODELS + '/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8'
        _M['asr'] = sherpa_onnx.OfflineRecognizer.from_transducer(
            encoder=P + '/encoder.int8.onnx', decoder=P + '/decoder.int8.onnx', joiner=P + '/joiner.int8.onnx',
            tokens=P + '/tokens.txt', num_threads=int(os.environ.get('VOICE_THREADS', '4')), model_type='nemo_transducer')
    return _M['asr']


def spk_model():
    if 'spk' not in _M:
        import sherpa_onnx
        cfg = sherpa_onnx.SpeakerEmbeddingExtractorConfig(model=MODELS + '/spk/wespeaker_en_voxceleb_resnet34.onnx', num_threads=4)
        _M['spk'] = sherpa_onnx.SpeakerEmbeddingExtractor(cfg)
    return _M['spk']


def asr(y16, lead=0.25):
    """Parakeet on 16 kHz audio (padded). Returns text and words [(word, start, end)] in the unpadded time base."""
    pad = np.zeros(int(lead * 16000), np.float32)
    z = np.concatenate([pad, y16, np.zeros(8000, np.float32)])
    st = asr_model().create_stream()
    st.accept_waveform(16000, z)
    asr_model().decode_stream(st)
    r = st.result
    toks, ts = list(r.tokens), list(r.timestamps)
    du = list(r.durations) if getattr(r, 'durations', None) else [0.08] * len(toks)
    words = []
    for t, s, d in zip(toks, ts, du):
        s -= lead
        if t.startswith(' ') or not words or (re.match(r"^[A-Za-z0-9]", t) and words[-1][0] and not re.search(r"[A-Za-z0-9']$", words[-1][0])):
            words.append([t.strip(), s, s + max(d, 0.04)])
        else:
            words[-1][0] += t
            words[-1][2] = s + max(d, 0.04)
    out = []
    for w, s, e in words:                      # '412' -> four / hundred / twelve, times spread over the token
        parts = hyp_norm([w])
        if len(parts) <= 1:
            if norm_word(w):
                out.append([w, s, e])
            continue
        for k, p_ in enumerate(parts):
            out.append([p_, s + (e - s) * k / len(parts), s + (e - s) * (k + 1) / len(parts)])
    return r.text.strip(), out


def embed(y16):
    ex = spk_model()
    s = ex.create_stream()
    s.accept_waveform(16000, y16.astype(np.float32))
    s.input_finished()
    e = np.array(ex.compute(s), np.float32)
    return e / (np.linalg.norm(e) + 1e-9)

# ----------------------------------------------------------------------------------------------- words


def align_words(text, y, sr, asr_words):
    """Script words with times. ASR words matched by sequence alignment; unmatched script words are interpolated;
    edges are refined on the 10 ms speech mask (a start never sits in silence, an end never runs into a pause)."""
    import difflib
    disp, nrm = script_words(text)
    hn = [norm_word(w[0]) for w in asr_words]
    times = [None] * len(nrm)
    sm = difflib.SequenceMatcher(a=nrm, b=hn, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1):
                times[i1 + k] = [asr_words[j1 + k][1], asr_words[j1 + k][2]]
        elif tag == 'replace':
            # spread the hypothesis span over the script words
            s, e = asr_words[j1][1], asr_words[j2 - 1][2]
            n = i2 - i1
            for k in range(n):
                times[i1 + k] = [s + (e - s) * k / n, s + (e - s) * (k + 1) / n]
    dur = len(y) / sr
    m = speech_mask(y, sr, rel_db=-38, bridge=0.0)
    idx = np.where(m)[0]
    sp_on, sp_off = (idx[0] * 0.01, (idx[-1] + 1) * 0.01) if len(idx) else (0.0, dur)
    # interpolate missing
    known = [i for i, t in enumerate(times) if t]
    for i in range(len(times)):
        if times[i]:
            continue
        prv = max([k for k in known if k < i], default=None)
        nxt = min([k for k in known if k > i], default=None)
        a = times[prv][1] if prv is not None else sp_on
        b = times[nxt][0] if nxt is not None else sp_off
        gap = [k for k in range(i, len(times)) if not times[k] and (nxt is None or k < nxt)]
        n = len(gap) + (i - (prv + 1 if prv is not None else 0))
        span = [k for k in range((prv + 1) if prv is not None else 0, nxt if nxt is not None else len(times))]
        j = span.index(i)
        times[i] = [a + (b - a) * j / len(span), a + (b - a) * (j + 1) / len(span)]
    # refine edges on speech mask
    out = []
    for i, (w, (s, e)) in enumerate(zip(disp, times)):
        s, e = max(0.0, s), min(dur, e)
        fs = int(s / 0.01)
        if fs < len(m) and not m[min(fs, len(m) - 1)]:      # start in silence: move to next speech onset (<= 0.25 s)
            nx = np.where(m[fs:fs + 25])[0]
            if len(nx):
                s = (fs + nx[0]) * 0.01
        fe = int(e / 0.01)
        seg = m[int(s / 0.01):min(len(m), fe)]
        if len(seg) and not seg[-1]:                         # end inside a pause: pull back to the last speech frame
            last = np.where(seg)[0]
            if len(last):
                e = (int(s / 0.01) + last[-1] + 1) * 0.01
        if i == len(disp) - 1:                               # last word ends where speech ends (ASR ends early)
            e = max(e, min(dur, sp_off))
        e = max(e, s + 0.06)
        out.append({'w': w, 't': round(s, 3), 'd': round(e - s, 3)})
    for a, b in zip(out[:-1], out[1:]):                      # no overlaps
        if a['t'] + a['d'] > b['t']:
            a['d'] = round(max(0.04, b['t'] - a['t']), 3)
    return out

# ----------------------------------------------------------------------------------------------- pitch & voice quality


def pitch(y, sr, fmin=60, fmax=700, gate_db=-30.0):
    """pYIN F0 (10 ms hop). Cleaned of two pYIN false positives: frames more than 30 dB under the line's loud level
    (decaying fricatives read as voiced at the floor) and frames stuck at the search floor."""
    import librosa
    y16 = resample(y, sr, 16000)
    f0, vf, vp = librosa.pyin(y16, fmin=fmin, fmax=fmax, sr=16000, frame_length=1024, hop_length=160)
    f0 = np.where(vf, f0, np.nan)
    rms = librosa.feature.rms(y=y16, frame_length=1024, hop_length=160, center=True)[0][:len(f0)]
    db = 20 * np.log10(rms + 1e-9)
    ref = np.percentile(db, 95)
    f0 = np.where(db[:len(f0)] < ref + gate_db, np.nan, f0)
    f0 = np.where(f0 < fmin * 1.05, np.nan, f0)
    return f0, 0.01


def pitch_stats(f0, hop=0.01):
    v = ~np.isnan(f0)
    if v.sum() < 8:
        return {'fry_tail': 0, 'f0_med': None, 'std_st': 0.0, 'range_st': 0.0, 'move_st': 0.0, 'tail_st': 0.0, 'voiced': round(float(v.mean()), 2), 'f0_jumps': 0}
    f = f0[v]
    med = float(np.median(f))
    st = 12 * np.log2(f / med)
    idx = np.where(v)[0]
    seg = []
    for k in range(idx[0], idx[-1] + 1, 20):
        sel = (idx >= k) & (idx < k + 20)
        if sel.sum() > 4:
            seg.append(np.median(st[sel]))
    tail = idx[idx >= idx[-1] - 35]
    tf = 12 * np.log2(f0[tail] / med)
    slope = float(np.polyfit(np.arange(len(tf)) * hop, tf, 1)[0] * 0.35) if len(tf) > 5 else 0.0
    # discontinuities: frame-to-frame jumps > 2.5 st inside voiced runs (octave errors of pYIN excluded: 11-13 st)
    d = np.abs(np.diff(12 * np.log2(f0 / med)))
    both = v[1:] & v[:-1]
    jumps = int(((d > 2.5) & (np.abs(d - 12) > 1.0) & both).sum())
    # creaky / half-pitch tail: voiced frames under 0.62 x the median at the end of the last voiced stretch
    fry = 0
    for x in f[::-1]:
        if x < 0.62 * med:
            fry += 1
        else:
            break
    return {'fry_tail': fry, 'f0_med': round(med, 1), 'f0_p10': round(float(np.percentile(f, 10)), 1), 'f0_p90': round(float(np.percentile(f, 90)), 1),
            'std_st': round(float(st.std()), 2), 'range_st': round(float(np.percentile(st, 90) - np.percentile(st, 10)), 2),
            'move_st': round(float(np.std(seg)), 2) if len(seg) > 2 else 0.0, 'tail_st': round(slope, 2),
            'voiced': round(float(v.mean()), 2), 'f0_jumps': jumps}


def praat_quality(y, sr, f0_med=None):
    import parselmouth
    from parselmouth.praat import call
    snd = parselmouth.Sound(y.astype(np.float64), sampling_frequency=sr)
    lo = 75 if not f0_med or f0_med < 200 else 120
    out = {}
    try:
        h = snd.to_harmonicity_cc(time_step=0.01, minimum_pitch=lo)
        hv = h.values[0]
        hv = hv[hv > -100]
        out['hnr_db'] = round(float(np.median(hv)), 2) if len(hv) else None
    except Exception:
        out['hnr_db'] = None
    try:
        pp = call(snd, 'To PointProcess (periodic, cc)', lo, 700)
        out['jitter_pct'] = round(100 * call(pp, 'Get jitter (local)', 0, 0, 0.0001, 0.02, 1.3), 2)
        out['shimmer_pct'] = round(100 * call([snd, pp], 'Get shimmer (local)', 0, 0, 0.0001, 0.02, 1.3, 1.6), 2)
    except Exception:
        out['jitter_pct'] = out['shimmer_pct'] = None
    try:
        # formant ceiling by voice type (adult male 5000, female 5500, child 6500 Hz), from the median pitch
        ceil = 5000 if (f0_med or 120) < 165 else (5500 if (f0_med or 0) < 250 else 6500)
        fm = snd.to_formant_burg(time_step=0.01, max_number_of_formants=5, maximum_formant=ceil)
        pt = snd.to_pitch(time_step=0.01, pitch_floor=lo, pitch_ceiling=700)
        it = snd.to_intensity(minimum_pitch=lo, time_step=0.01)
        F = [[], [], [], []]
        for t in np.arange(0.02, snd.duration - 0.02, 0.01):
            if pt.get_value_at_time(t) != pt.get_value_at_time(t):     # nan = unvoiced
                continue
            if it.get_value(t) < it.values.max() - 12:
                continue
            vals = [fm.get_value_at_time(i + 1, t) for i in range(4)]
            if all(v == v for v in vals):
                for i in range(4):
                    F[i].append(vals[i])
        if len(F[0]) > 5:
            med = [float(np.median(f)) for f in F]
            k = np.array([0.5, 1.5, 2.5, 3.5])
            dF = float(np.dot(k, med) / np.dot(k, k))
            out.update({'F1': round(med[0]), 'F2': round(med[1]), 'F3': round(med[2]), 'F4': round(med[3]), 'formant_dF': round(dF)})
    except Exception:
        pass
    return out


def clicks(y, sr):
    import librosa
    S_ = np.abs(librosa.stft(y, n_fft=1024, hop_length=256)) ** 2
    L = np.log(S_ + 1e-10)
    flux = np.maximum(0, np.diff(L, axis=1)).mean(0)
    med = np.median(flux)
    mad = np.median(np.abs(flux - med)) + 1e-6
    return int((flux > med + 10 * mad).sum())


def dnsmos(y, sr):
    try:
        from speechmos import dnsmos as D
        y16 = resample(y, sr, 16000)
        y16 = y16 / max(1e-6, np.abs(y16).max()) * 0.9
        if len(y16) < 16000 * 1.2:                      # DNSMOS wants >= ~1 s; loop-pad short lines with silence
            y16 = np.concatenate([y16, np.zeros(int(16000 * 1.2) - len(y16), np.float32)])
        r = D.run(y16.astype(np.float32), 16000)
        return {'dnsmos_ovrl': round(float(r['ovrl_mos']), 2), 'dnsmos_sig': round(float(r['sig_mos']), 2),
                'dnsmos_bak': round(float(r['bak_mos']), 2), 'dnsmos_p808': round(float(r['p808_mos']), 2)}
    except Exception as e:
        return {'dnsmos_err': str(e)[:80]}

# ----------------------------------------------------------------------------------------------- visemes


def visemes(y, sr, words, dF=None, fps=FPS):
    """Change points [t, name] at 60 fps. name in face.js VISEMES; None = leave the word window (expression mouth)."""
    import librosa
    off = VIS_REF_LUFS - lufs(y, sr)                   # judge levels as if the line sat at VIS_REF_LUFS
    hop = int(round(sr / fps))
    n = int(np.ceil(len(y) / hop))
    pad = np.concatenate([y, np.zeros(hop * 2, np.float32)])
    rms = librosa.feature.rms(y=pad, frame_length=2 * hop, hop_length=hop, center=True)[0][:n]
    db = 20 * np.log10(rms + 1e-9) + off
    S_ = np.abs(librosa.stft(pad, n_fft=2048, hop_length=hop, center=True))[:, :n]
    fr = librosa.fft_frequencies(sr=sr, n_fft=2048)
    band = (fr > 80) & (fr < 5000)
    cen = (S_[band] * fr[band, None]).sum(0) / (S_[band].sum(0) + 1e-9)
    sc = (dF or NARR_DF) / NARR_DF
    thrE, thrO = VIS_E_HZ * sc, VIS_O_HZ * sc
    lab = np.array([None] * n, dtype=object)
    # word windows, merged when the gap is < 0.12 s
    wins = []
    for w in words:
        s, e = w['t'], w['t'] + w['d']
        if wins and s - wins[-1][1] < 0.12:
            wins[-1][1] = e
        else:
            wins.append([s, e])
    for s, e in wins:
        for f in range(int(round(s * fps)), min(n, int(round(e * fps)) + 1)):
            if db[f] < VIS_CLOSED_DB:
                lab[f] = 'v_closed'
            elif db[f] < VIS_SMALL_DB:
                lab[f] = 'v_small'
            elif cen[f] > thrE:
                lab[f] = 'v_E'
            elif cen[f] < thrO:
                lab[f] = 'v_O'
            else:
                lab[f] = 'v_A'
    # runs: min hold 3 frames (short runs merge into the longer neighbour), max hold 8 (split, alternating partner)
    partner = {'v_A': 'v_O', 'v_O': 'v_A', 'v_E': 'v_small', 'v_small': 'v_E', 'v_closed': 'v_small'}

    def runs(a):
        r, s = [], 0
        for i in range(1, len(a) + 1):
            if i == len(a) or a[i] != a[s]:
                r.append([a[s], s, i])
                s = i
        return r
    for _ in range(4):
        R = runs(lab)
        changed = False
        for i, (v, s, e) in enumerate(R):
            if v is None or e - s >= 3:
                continue
            L = R[i - 1] if i > 0 else None
            Rr = R[i + 1] if i + 1 < len(R) else None
            cand = [x for x in (L, Rr) if x is not None and x[0] is not None]
            if cand:
                tgt = max(cand, key=lambda x: x[2] - x[1])[0]
            else:
                tgt = v
                # isolated short run inside a window: extend to 3 frames
                lab[s:min(n, s + 3)] = v
                continue
            lab[s:e] = tgt
            changed = True
        if not changed:
            break
    R = runs(lab)
    for v, s, e in R:
        if v is None or e - s <= 8:
            continue
        L = e - s
        k = int(np.ceil(L / 6))
        cuts = np.linspace(s, e, k + 1).round().astype(int)
        for j in range(k):
            if j % 2 == 1:
                lab[cuts[j]:cuts[j + 1]] = partner[v]
    out = []
    prev = 'start'
    for f in range(n):
        if lab[f] != prev:
            out.append([round(f / fps, 3), lab[f]])
            prev = lab[f]
    if out and out[0][1] is None and out[0][0] == 0:
        out = out[1:]
    return out

# ----------------------------------------------------------------------------------------------- measure


def measure(y, sr, text, role=None, words_override=None, want_emb=True, quick=False):
    """All metrics for a line. Returns (metrics, words, visemes, embedding)."""
    y = np.asarray(y, np.float32)
    y16 = resample(y, sr, 16000)
    hyp, aw = asr(y16)
    disp, nrm = script_words(text)
    acc, errs = word_acc(nrm, hyp_norm(hyp.split()))
    words = words_override or align_words(text, y, sr, aw)
    f0, hop = pitch(y, sr)
    ps = pitch_stats(f0, hop)
    m = speech_mask(y, sr)
    speech_s = float(m.sum() * 0.01)
    idx = np.where(m)[0]
    span = float((idx[-1] - idx[0] + 1) * 0.01) if len(idx) else 0.0
    # internal pauses >= 0.15 s (frames under -35 dB of the loud level)
    q = ~speech_mask(y, sr, bridge=0.0)
    pauses, s = [], None
    if len(idx):
        for f in range(idx[0], idx[-1] + 1):
            if q[f] and s is None:
                s = f
            if not q[f] and s is not None:
                if (f - s) * 0.01 >= 0.15:
                    pauses.append(round((f - s) * 0.01, 2))
                s = None
    met = {'asr': hyp, 'word_acc': round(acc, 3), 'word_errs': errs, 'n_words': len(nrm), 'dur': round(len(y) / sr, 3),
           'speech_s': round(speech_s, 2), 'span_s': round(span, 2),
           'wpm_voiced': round(60 * len(nrm) / max(0.2, speech_s), 1),
           'wpm_span': round(60 * len(nrm) / max(0.2, span), 1), 'pauses': pauses}
    met.update(ps)
    met['lufs'] = round(lufs(y, sr), 2)
    met['peak_dbfs'] = round(float(20 * np.log10(np.abs(y).max() + 1e-12)), 2)
    met['clipped'] = int((np.abs(y) >= 0.999).sum())
    met['click_frames'] = clicks(y, sr)
    if not quick:
        met.update(praat_quality(y, sr, ps.get('f0_med')))
        met.update(dnsmos(y, sr))
    emb = embed(y16) if want_emb else None
    vis = visemes(y, sr, words, met.get('formant_dF'))
    return met, words, vis, emb


def role_similarity(role, emb, lines, voice_dir=VOICE_DIR, skip_id=None):
    sims = []
    for L in lines:
        if L.get('role') != role or L.get('id') == skip_id:
            continue
        p = L['file'] if os.path.isabs(L['file']) else os.path.join(voice_dir, os.path.basename(L['file']))
        if not os.path.exists(p):
            continue
        y, sr = load(p)
        sims.append(float(np.dot(emb, embed(resample(y, sr, 16000)))))
    return round(float(np.mean(sims)), 3) if sims else None


def entry(id_, role, tag, text, file, y, sr, approach, extra_metrics=None, words_override=None):
    met, words, vis, emb = measure(y, sr, text, role, words_override)
    if extra_metrics:
        met.update(extra_metrics)
    return {'id': id_, 'role': role, 'tag': tag, 'text': text, 'file': file, 'dur': round(len(y) / sr, 3),
            'words': words, 'visemes': vis, 'metrics': met, 'approach': approach}, emb


def update_json(e, path=LINES_JSON, emb=None):
    lines = json.load(open(path)) if os.path.exists(path) else []
    if emb is not None:
        e['metrics']['spk_sim_role'] = role_similarity(e['role'], emb, lines, skip_id=e['id'])
    lines = [L for L in lines if L['id'] != e['id']] + [e]
    lines.sort(key=lambda L: L['id'])
    with open(path, 'w') as f:
        f.write(dumps_lines(lines))


def dumps_lines(lines):
    """Readable JSON: one line per word / viseme list."""
    out = ['[']
    for i, L in enumerate(lines):
        d = dict(L)
        body = json.dumps({k: v for k, v in d.items() if k not in ('words', 'visemes', 'metrics')}, ensure_ascii=False)[1:-1]
        s = '  {' + body + ',\n    "words": ' + json.dumps(d['words'], ensure_ascii=False) + ',\n    "visemes": ' + json.dumps(d['visemes']) + \
            ',\n    "metrics": ' + json.dumps(d['metrics'], ensure_ascii=False) + '}'
        out.append(s + (',' if i < len(lines) - 1 else ''))
    out.append(']')
    return '\n'.join(out) + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('wav')
    ap.add_argument('--id', required=True)
    ap.add_argument('--role', required=True)
    ap.add_argument('--text', required=True)
    ap.add_argument('--tag', default='')
    ap.add_argument('--out', help='conformed output wav (default: VOICE_DIR/<ID>_<ROLE>.wav)')
    ap.add_argument('--update', nargs='?', const=LINES_JSON, help='voice_lines.json to update (default audio/voice_lines.json)')
    ap.add_argument('--approach', default='external take (e.g. Fish Audio)')
    ap.add_argument('--no-conform', action='store_true', help='measure the file as is')
    a = ap.parse_args()
    y, sr = load(a.wav)
    if not a.no_conform:
        y, sr = conform(y, sr, a.role)
        out = a.out or os.path.join(VOICE_DIR, f'{a.id}_{a.role}.wav')
        import soundfile as sf
        os.makedirs(os.path.dirname(out), exist_ok=True)
        sf.write(out, y, sr, subtype='PCM_24')
    else:
        out = a.wav
    e, emb = entry(a.id, a.role, a.tag, a.text, out, y, sr, a.approach)
    if a.update:
        update_json(e, a.update, emb)
    m = e['metrics']
    print(json.dumps({k: m.get(k) for k in ('asr', 'word_acc', 'f0_med', 'std_st', 'range_st', 'wpm_voiced', 'lufs', 'peak_dbfs', 'clipped',
                                             'hnr_db', 'dnsmos_ovrl', 'formant_dF', 'spk_sim_role')}, ensure_ascii=False))
    print('words', json.dumps(e['words'], ensure_ascii=False))
    print('visemes', len(e['visemes']), 'change points;', 'file', out)


if __name__ == '__main__':
    main()
