# Shared voice toolkit: Supertonic-3 takes, take selection through ASR, studio-mic / radio / PA chains.
# Call init(scratch_dir) once before using the voice or ASR functions.
import re, numpy as np, librosa
import sherpa_onnx
from pedalboard import (Pedalboard, HighpassFilter, LowpassFilter, LowShelfFilter, HighShelfFilter, PeakFilter,
                        Compressor, Reverb, Gain, Distortion)

SR = 48000
narr = rec = kok = None

def init(S):
    global narr, rec, kok
    from kokoro_onnx import Kokoro
    d = f'{S}/models/sherpa-onnx-supertonic-3-tts-int8-2026-05-11/'
    narr = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
        supertonic=sherpa_onnx.OfflineTtsSupertonicModelConfig(
            duration_predictor=d + 'duration_predictor.int8.onnx', text_encoder=d + 'text_encoder.int8.onnx',
            vector_estimator=d + 'vector_estimator.int8.onnx', vocoder=d + 'vocoder.int8.onnx', tts_json=d + 'tts.json',
            unicode_indexer=d + 'unicode_indexer.bin', voice_style=d + 'voice.bin'), num_threads=4)))
    M = S + '/models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8'
    rec = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=M + '/encoder.int8.onnx', decoder=M + '/decoder.int8.onnx',
            joiner=M + '/joiner.int8.onnx', tokens=M + '/tokens.txt', num_threads=4, model_type='nemo_transducer')
    kok = Kokoro(f'{S}/tts/kokoro-v1.0.onnx', f'{S}/tts/voices-v1.0.bin')

def trim(a, pre=0.03, post=0.1):
    idx = np.where(np.abs(a) > 0.02 * np.abs(a).max())[0]
    a = a[max(0, idx[0] - int(pre * SR)): idx[-1] + int(post * SR)].copy()
    fi, fo = int(0.008 * SR), int(0.03 * SR)
    a[:fi] *= np.linspace(0, 1, fi); a[-fo:] *= np.linspace(1, 0, fo)
    return a

def take(text, speed, sid):
    g = sherpa_onnx.GenerationConfig(); g.sid = sid; g.speed = float(speed); g.num_steps = 8
    r = narr.generate(text, g)
    a = librosa.resample(np.asarray(r.samples, np.float32), orig_sr=r.sample_rate, target_sr=SR)
    a = trim(a)
    return a / (np.sqrt(np.mean(a ** 2)) + 1e-9) * 0.08     # same speech level for every take

def hp(x, f, order=4):
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(order, f / (SR / 2), 'high', output='sos'), x)

# "studio mic" chain: a little proximity warmth, less boxiness, gentle presence, light compression, dry
mic = Pedalboard([HighpassFilter(75), LowShelfFilter(cutoff_frequency_hz=150, gain_db=1.5), PeakFilter(320, -2.0, 1.0),
                  PeakFilter(3400, 1.5, 0.9), HighShelfFilter(cutoff_frequency_hz=10000, gain_db=0.8),
                  Compressor(threshold_db=-21, ratio=2.4, attack_ms=8, release_ms=130), Gain(3)])
def deess(x):
    # dynamic cut of 5.5-9 kHz when it dominates
    from scipy.signal import butter, sosfiltfilt
    band = sosfiltfilt(butter(2, [5500 / (SR / 2), 9000 / (SR / 2)], 'band', output='sos'), x)
    env = np.sqrt(np.convolve(band ** 2, np.ones(240) / 240, 'same')) + 1e-9
    full = np.sqrt(np.convolve(x ** 2, np.ones(240) / 240, 'same')) + 1e-9
    red = np.clip((env / full - 0.35) * 1.6, 0, 0.6)
    return x - band * red

def process_narration(a):
    a = mic(a.astype(np.float32), SR)
    room = Pedalboard([Reverb(room_size=0.08, damping=0.8, wet_level=0.018, dry_level=1.0, width=0.1)])
    return room(deess(a).astype(np.float32), SR)

pa_chain = Pedalboard([HighpassFilter(450), LowpassFilter(3600), PeakFilter(1800, 5, 1.2), Distortion(drive_db=9),
                       Compressor(threshold_db=-18, ratio=6), Reverb(room_size=0.85, damping=0.4, wet_level=0.35, dry_level=0.75, width=0.6), Gain(-4)])

# walkie-talkie: narrow band, a little crunch, squelch tail; hiss rides only while the channel is open
radio_chain = Pedalboard([HighpassFilter(420), LowpassFilter(3100), PeakFilter(1600, 5, 1.0), Distortion(drive_db=14),
                          Compressor(threshold_db=-22, ratio=6, attack_ms=2, release_ms=60), LowpassFilter(3300), Gain(-3)])
def radio(a, seed=0):
    r = np.random.default_rng(seed)
    y = radio_chain(a.astype(np.float32), SR)
    pre, post = int(0.12 * SR), int(0.16 * SR)
    y = np.concatenate([np.zeros(pre, np.float32), y, np.zeros(post, np.float32)])
    hiss = Pedalboard([HighpassFilter(900), LowpassFilter(3600)])(r.standard_normal(len(y)).astype(np.float32) * 0.02, SR)
    burst = np.zeros_like(y); nb = int(0.07 * SR)
    burst[:nb] = r.standard_normal(nb) * 0.09 * np.linspace(1, 0.2, nb)                 # key-up squelch
    burst[-nb:] = r.standard_normal(nb) * 0.11 * np.linspace(0.3, 1, nb) ** 2 * np.linspace(1, 0, nb) ** 0.3
    burst = Pedalboard([HighpassFilter(600), LowpassFilter(4200)])(burst.astype(np.float32), SR)
    y = y + hiss + burst
    y[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR))
    return y.astype(np.float32), pre / SR

def whisper(a, seed=0):
    """Close, hushed delivery: thinner low end, breath noise following the voice envelope."""
    r = np.random.default_rng(seed)
    y = Pedalboard([HighpassFilter(140), LowShelfFilter(cutoff_frequency_hz=250, gain_db=-4), PeakFilter(2800, 2.5, 0.9),
                    Compressor(threshold_db=-24, ratio=3, attack_ms=5, release_ms=120)])(a.astype(np.float32), SR)
    env = np.sqrt(np.convolve(y ** 2, np.ones(480) / 480, 'same'))
    air = Pedalboard([HighpassFilter(1800), LowpassFilter(7000)])(r.standard_normal(len(y)).astype(np.float32), SR)
    y = y * 0.75 + air * env * 0.45
    return deess(y).astype(np.float32)

def num_words(w):
    """How many spoken script words an ASR token stands for (digits only)."""
    w = w.strip('.,!?')
    if not re.search(r'\d', w): return 1
    if re.fullmatch(r'\d{1,2}[.:]\d{2}', w):  # clock time 2.14 -> two fourteen; 2.31 -> two thirty-one (hyphenated = 1)
        return 2
    n = int(re.sub(r'\D', '', w) or 0)
    if n >= 1000 and n % 1000 == 0: return 2   # nine thousand
    return 1                                     # 12 -> twelve, 38 -> thirty-eight

def asr(a):
    """Recognized words with start times; numbers expanded into one placeholder per script word."""
    y = librosa.resample(a.astype(np.float32), orig_sr=SR, target_sr=16000)
    st = rec.create_stream(); st.accept_waveform(16000, y); rec.decode_stream(st)
    r = st.result; words = []; cur = None
    for tok, t in zip(r.tokens, r.timestamps):
        if tok.startswith(' ') or cur is None:
            if cur: words.append(cur)
            cur = [tok.strip(), t]
        else: cur[0] += tok
    if cur: words.append(cur)
    words = [w for w in words if re.search(r'[A-Za-z0-9]', w[0])]
    exp, dur = [], len(a) / SR
    for i, (w, t0) in enumerate(words):
        t1 = words[i + 1][1] if i + 1 < len(words) else dur - 0.1
        n = num_words(w)
        for j in range(n): exp.append(('#' if n > 1 or re.search(r'\d', w) else w.lower().strip('.,!?'), t0 + (t1 - t0) * j / n))
    asr.raw = words
    return exp, r.text

# number words a digit token from the ASR may stand for ("231" = "two thirty-one", "31%" = "thirty-one percent")
NUMW = set('zero oh one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen '
           'seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred thousand percent and'.split())
numberish = lambda w: all(p in NUMW for p in w.lower().strip("'").split('-'))

def align(raw, text, dur):
    """Match ASR tokens to script words. A word token must equal its script word; a token with digits may
    cover 1-4 consecutive number words. Returns a start time per script word, or None if it does not fit."""
    sw = [_norm(w) for w in script_words(text)]
    toks = [(re.sub(r'[.,!?]', '', w), t) for w, t in raw]
    n, m = len(sw), len(toks)
    from functools import lru_cache
    @lru_cache(None)
    def go(i, j):
        if i == n and j == m: return ()
        if i == n or j == m: return None
        w, _ = toks[j]
        if re.search(r'\d', w):
            # "20-foot" against "twenty-foot": the word parts must agree, the number part is free
            if '-' in sw[i] and '-' in w and [x for x in w.lower().split('-') if not re.search(r'\d', x)] == [x for x in sw[i].split('-') if not numberish(x)]:
                rest = go(i + 1, j + 1)
                if rest is not None: return ((j, 1),) + rest
            for k in range(1, 5):
                if i + k <= n and all(numberish(x) for x in sw[i:i + k]):
                    rest = go(i + k, j + 1)
                    if rest is not None: return ((j, k),) + rest
            return None
        if _norm(w) == sw[i] or sw[i].replace('-', '') == _norm(w).replace('-', ''):
            rest = go(i + 1, j + 1)
            if rest is not None: return ((j, 1),) + rest
        # a hyphenated script word may come back as separate tokens ("two-oh-one" -> "two oh one")
        parts = sw[i].split('-')
        if len(parts) > 1 and j + len(parts) <= m and [_norm(x) for x, _ in toks[j:j + len(parts)]] == parts:
            rest = go(i + 1, j + len(parts))
            if rest is not None: return ((j, -len(parts)),) + rest
        return None
    path = go(0, 0)
    if path is None: return None
    times = []
    for j, k in path:
        t0 = toks[j][1]
        if k < 0: times.append(t0); continue
        nxt = toks[j + 1][1] if j + 1 < m else dur - 0.1
        times += [t0 + (nxt - t0) * q / k for q in range(k)]
    return times

script_words = lambda text: re.findall(r"[A-Za-z0-9'\-]+", text)
SAME = {'isle': 'aisle', 'ok': 'okay', "four's": 'fours'}   # spellings the ASR may use either way
_norm = lambda w: SAME.get(w.lower().strip("'"), w.lower().strip("'"))
def reads_back(exp, text):
    sw = [_norm(w) for w in script_words(text)]
    # hyphenated number words ("two-oh-one") may come back as one token or several
    if len(exp) != len(sw):
        return False
    return all(h == '#' or _norm(h) == s or s.replace('-', '') == _norm(h).replace('-', '') for (h, _), s in zip(exp, sw))

def pitch_life(a):
    """Std of pitch in semitones over voiced frames: higher = livelier intonation."""
    y = librosa.resample(a, orig_sr=SR, target_sr=16000)
    f0, vf, _ = librosa.pyin(y, fmin=60, fmax=400, sr=16000, frame_length=1024, hop_length=160)
    f = f0[vf & ~np.isnan(f0)]
    return float((12 * np.log2(f / np.median(f))).std()) if len(f) > 5 else 0.0

def longest_gap(a):
    fr = librosa.feature.rms(y=a, frame_length=960, hop_length=960)[0]; q = 20 * np.log10(fr / fr.max() + 1e-9) < -38
    best = c = 0
    for v in q: c = c + 1 if v else 0; best = max(best, c)
    return best * 0.02

def best_take(text, rate, sid, takes=6, say=None):
    """Voice `say` (default: text) and keep the take that reads back as `text`."""
    n = len(script_words(text)); target = n / rate + 0.13
    probe = take(say or text, 1.0, sid)
    # short phrases come out quick, so they may be slowed further before the voice starts to drag
    speed = float(np.clip(len(probe) / SR / target, 0.64 if n <= 4 else 0.72, 1.12))
    cands = []
    for k in range(takes):
        a = take(say or text, speed * (0.97, 1.0, 1.03)[k % 3], sid)
        exp, heard = asr(a)
        ok = align(asr.raw, text, len(a) / SR) is not None
        score = pitch_life(a) - 5 * abs(np.log(len(a) / SR / target)) - (2 if longest_gap(a) > 0.3 else 0) - (0 if ok else 100)
        cands.append((score, a, exp, heard))
    cands.sort(key=lambda c: -c[0])
    s, a, exp, heard = cands[0]
    if s < -50: print('  WARNING: no take reads back cleanly for', repr(text), '| best heard:', heard)
    return a, exp, heard, speed, s
