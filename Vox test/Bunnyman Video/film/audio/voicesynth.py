"""voicesynth.py: WORLD-vocoder voices for the score and the SFX, made from the narrator's own take (so they belong to
the same recording) with the character settings of tools/vo_voices.py (Mom 'M', the real Laurie 'L', the thing in the
narrator's old body 'X').

    hum(times, midis, who='M', ...)        a closed-mouth hum of a melody: the nasal murmur of the narrator's /m/
                                           (37 "Mom" / "humming" words of narration_clean.wav, voiced frames whose
                                           100-450 Hz band is >= 22 dB over 1-4 kHz, averaged), warped to the
                                           character's vocal tract, sung on an F0 line with scoops, glides, vibrato
                                           and drift, phrase breaths through the nose
    sing(src_spans, times, midis, ...)     the narrator's spoken syllables re-pitched onto a melody and re-timed onto
                                           its notes (syllable nuclei found on the take, vowels stretched, consonants
                                           kept): the real Laurie's broken "Hop... hop... hop along" through the door
    cry(dur, who='L', ...)                 a lost child crying: long wails and hiccup sobs on the vowels of her own
                                           "Mama?" (rise-fall F0 contours that crack, shaky gasps between)
    analyze(x) / synth(f0, sp, ap)         WORLD (Harvest, CheapTrick, D4C; 5 ms frames), cached per source span
Everything returns mono float64 at 48 kHz, peak-normalised to 0.5; the caller levels it.
"""
import hashlib, json, os, sys
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.normpath(os.path.join(HERE, '..'))
W = os.path.join(FILM, '_work')
CACHE = os.path.join(W, 'cache', 'voicesynth')
SR = 48000
FP = 5.0                                              # frame period (ms)
VO_CLEAN = os.path.join(W, 'narration', 'narration_clean.wav')
VO_EN = os.path.join(W, 'align', 'vo_en.wav')
sys.path.insert(0, os.path.join(FILM, 'tools'))
import vo_voices as VV                                # noqa: E402  (VOICES, warp_envelope, breathe, eq)

_VO = {}


def vo(t0, t1, which='clean'):
    """A span of the narration (film seconds) as mono float64 at 48 kHz."""
    p = VO_CLEAN if which == 'clean' else VO_EN
    if p not in _VO:
        x, sr = sf.read(p, dtype='float64', always_2d=True)
        _VO[p] = x.mean(1)
    x = _VO[p]
    return np.ascontiguousarray(x[int(t0 * SR):int(t1 * SR)])


def analyze(x):
    """(f0, sp, ap) of x at 5 ms frames, cached by content."""
    import pyworld as pw
    h = hashlib.md5(np.asarray(x, np.float64).tobytes()).hexdigest()[:16]
    p = os.path.join(CACHE, f'w_{h}.npz')
    if os.path.exists(p):
        z = np.load(p)
        return z['f0'], z['sp'], z['ap']
    f0, t = pw.harvest(x, SR, f0_floor=60.0, f0_ceil=600.0, frame_period=FP)
    sp = pw.cheaptrick(x, f0, t, SR)
    ap = pw.d4c(x, f0, t, SR)
    os.makedirs(CACHE, exist_ok=True)
    np.savez_compressed(p, f0=f0, sp=sp, ap=ap)
    return f0, sp, ap


def synth(f0, sp, ap):
    import pyworld as pw
    C = np.ascontiguousarray
    return pw.synthesize(C(f0, np.float64), C(sp, np.float64), C(ap, np.float64), SR, FP)


def hz(m):
    return 440.0 * 2.0 ** ((np.asarray(m, float) - 69.0) / 12.0)


def _norm(y, pk=0.5):
    m = float(np.abs(y).max())
    return y * (pk / m) if m > 0 else y


# ------------------------------------------------------------------------------------------------- the hum
_HUM = {}


def hum_envelope():
    """The narrator's nasal murmur (/m/), averaged log spectral envelope over 37 words (cached)."""
    if 'env' in _HUM:
        return _HUM['env']
    p = os.path.join(CACHE, 'hum_env.npy')
    if os.path.exists(p):
        _HUM['env'] = np.load(p); return _HUM['env']
    words = json.load(open(os.path.join(W, 'align', 'asr_cache.json')))['en_words']
    cands = [t for w, t in words if 'humm' in w.lower() or w.lower().startswith(('mom', 'mam'))]
    logs = []
    for t in cands:
        x = vo(t - 0.15, t + 0.45)
        f0, sp, ap = analyze(x)
        fr = np.linspace(0, SR / 2, sp.shape[1])
        lo = sp[:, (fr > 100) & (fr < 450)].mean(1); hi = sp[:, (fr > 1000) & (fr < 4000)].mean(1)
        r = 10 * np.log10(lo / (hi + 1e-20) + 1e-20); e = 10 * np.log10(sp.sum(1) + 1e-20)
        sel = (f0 > 0) & (r > 22) & (e > e.max() - 25)
        if sel.sum() >= 4:
            logs.append(np.log(sp[sel] + 1e-20).mean(0))
    env = np.exp(np.mean(logs, 0))
    os.makedirs(CACHE, exist_ok=True); np.save(p, env)
    _HUM['env'] = env
    return env


def f0_line(n_frames, times, midis, durs, rng, vib_hz=5.3, vib_cents=16.0, scoop_cents=45.0, glide=0.06,
            drift_cents=9.0, vib_delay=0.22, rests=None):
    """An F0 line (Hz per 5 ms frame) for a melody sung legato: each note from its start, a scoop up into it after a
    rest, cosine glides (glide s) between tied notes, vibrato that blooms after vib_delay on held notes, slow drift.
    times / durs in seconds, midis may be fractional. Frames outside every note keep the nearest note (the caller
    gates them)."""
    fp = FP / 1000.0
    t = np.arange(n_frames) * fp
    cents = np.zeros(n_frames)
    base = np.full(n_frames, float(midis[0]) if len(midis) else 60.0)
    order = np.argsort(times)
    times = np.asarray(times, float)[order]; midis = np.asarray(midis, float)[order]; durs = np.asarray(durs, float)[order]
    for k, (a, m, d) in enumerate(zip(times, midis, durs)):
        b = times[k + 1] if k + 1 < len(times) else a + d + 1.0
        sel = (t >= a) & (t < b)
        base[sel] = m
        if k == 0:
            base[t < a] = m
    # glides: smooth the steps over `glide` seconds (centred a little before each note: the voice anticipates)
    g = max(1, int(glide / fp))
    k_ = np.hanning(2 * g + 1); k_ /= k_.sum()
    pad = np.pad(base, (g, g), mode='edge')
    base = np.convolve(pad, k_, 'valid')
    for k, (a, m, d) in enumerate(zip(times, midis, durs)):
        rest_before = k == 0 or (rests is not None and rests[k]) or a - (times[k - 1] + durs[k - 1]) > 0.08
        if rest_before:
            i0 = int(a / fp); n_ = int(0.07 / fp)
            seg = np.arange(min(n_, max(0, n_frames - i0)))
            cents[i0:i0 + len(seg)] -= scoop_cents * (1 - seg / n_) ** 2
        i0, i1 = int((a + vib_delay) / fp), int((a + d) / fp)
        if i1 > i0 + 4:
            tt = np.arange(i1 - i0) * fp
            bloom = np.clip(tt / 0.3, 0, 1)
            cents[i0:i1] += vib_cents * bloom * np.sin(2 * np.pi * vib_hz * tt + rng.uniform(0, 6))
    walk = np.cumsum(rng.standard_normal(n_frames)) * 0.6
    walk = np.convolve(walk - walk.mean(), np.ones(60) / 60, 'same')
    walk = walk / (np.abs(walk).max() + 1e-9) * drift_cents
    return hz(base + (cents + walk) / 100.0)


def amp_line(n_frames, times, durs, attack=0.045, release=0.12, dip_db=7.0, staccato=None, phrase_ends=()):
    """Amplitude (linear) per frame: a soft attack per note, dips of dip_db between tied notes, staccato notes
    (indices) released after 60 % of their length, a longer release at phrase ends (times)."""
    fp = FP / 1000.0
    t = np.arange(n_frames) * fp
    a = np.zeros(n_frames)
    for k, (s, d) in enumerate(zip(times, durs)):
        e = s + d * (0.6 if staccato is not None and k in staccato else 1.0)
        env = np.clip((t - s) / attack, 0, 1) * np.clip((e + release - t) / release, 0, 1)
        dip = 1.0 - (1 - 10 ** (-dip_db / 20)) * np.exp(-((t - s) / 0.035) ** 2)
        a = np.maximum(a, env * np.where(t >= s, dip, 1.0))
    return a


def breath_in(dur=0.32, nose=True, rng=None):
    """An inhalation (through the nose for the hum: narrow, high), as audio."""
    rng = rng or np.random.default_rng(0)
    n = int(dur * SR); t = np.arange(n) / SR
    from scipy import signal
    z = rng.standard_normal(n)
    lo, hi = (1800, 6500) if nose else (700, 4500)
    z = signal.sosfilt(signal.butter(2, [lo, hi], 'bandpass', fs=SR, output='sos'), z)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    return z * env * 0.05


def hum(times, midis, durs, who='M', transpose=0.0, seed=0, staccato=None, phrase_breaks=(), breath=True,
        vib_cents=14.0, dip_db=6.0, tail=0.6):
    """A closed-mouth hum of the notes (times / durs in s from 0, midis). who: 'M' Mom (an adult woman), 'X' the
    thing in the narrator's old body (the narrator's own range), 'G' Grandma. phrase_breaks: times (s) where a nasal
    breath is taken (the hum stops 0.25 s before). Returns mono float64."""
    rng = np.random.default_rng(seed)
    s = VV.VOICES.get(who, VV.VOICES['M'])
    end = max(a + d for a, d in zip(times, durs)) + tail
    n = int(end / (FP / 1000.0)) + 2
    m = np.asarray(midis, float) + transpose
    f0 = f0_line(n, times, m, durs, rng, vib_cents=vib_cents)
    amp = amp_line(n, times, durs, dip_db=dip_db, staccato=staccato)
    t = np.arange(n) * FP / 1000.0
    for b in phrase_breaks:                           # the hum stops for the breath
        amp *= 1 - np.clip(1 - np.abs(t - (b - 0.12)) / 0.16, 0, 1) ** 0.5
    env = hum_envelope()
    sp = VV.warp_envelope(np.repeat(env[None, :], n, 0), s['alpha'] * (1.0 if who != 'X' else 1.0))
    # brighter on louder, higher notes: the lips part a little (a touch of 1-3 kHz back in)
    fr = np.linspace(0, SR / 2, sp.shape[1])
    openness = np.clip((np.log2(f0 / 250.0) + 0.3) * 0.5, 0, 0.6)[:, None] * np.exp(-((fr - 1600) / 900.0) ** 2)[None, :]
    sp = sp * (1 + 8.0 * openness)
    sp = sp * (amp[:, None] ** 2 + 1e-8)
    ap = np.full_like(sp, 0.06)
    ap = VV.breathe(ap, max(0.05, s.get('breath', 0.1) * 0.6))
    y = synth(f0, sp, ap)
    g = np.interp(np.arange(len(y)) / SR, np.arange(n) * FP / 1000.0, (amp > 1e-3).astype(float))
    y *= g
    if s.get('eq'):
        y = VV.eq(y, s['eq'])
    if breath:
        for b in [times[0]] + list(phrase_breaks):
            i = int((b - 0.36) * SR)
            if i >= 0:
                br = breath_in(0.32, True, rng)
                y[i:i + len(br)] += br[:max(0, len(y) - i)] * (np.abs(y).max() + 1e-9) * 0.6
    return _norm(y)


# ------------------------------------------------------------------------------------------------- sung speech
def nuclei(f0, sp, n):
    """Frame indices of the n most prominent syllable nuclei (voiced energy peaks in 300-2500 Hz), sorted."""
    from scipy.signal import find_peaks
    fr = np.linspace(0, SR / 2, sp.shape[1])
    e = np.log(sp[:, (fr > 300) & (fr < 2500)].sum(1) + 1e-20)
    e = np.convolve(e, np.hanning(9) / np.hanning(9).sum(), 'same')
    e[f0 <= 0] -= 3.0
    pk, pr = find_peaks(e, distance=int(90 / FP), prominence=0.3)
    if len(pk) < n:
        pk, pr = find_peaks(e, distance=int(60 / FP), prominence=0.05)
    keep = np.sort(pk[np.argsort(pr['prominences'])[::-1][:n]])
    return keep, e


def sing(lines, notes, who='L', seed=0, transpose=0.0, cracks=0.25, sob_gaps=(), tremor=(6.5, 0.035)):
    """The narrator's spoken words re-sung. lines: [[b0, b1, ..., bn]] syllable boundaries in film seconds of
    narration_clean.wav (one list per spoken line, n syllables each); notes: [(t_start, dur, midi)] one per syllable
    in order, output seconds. Each syllable = onset consonant (kept at its own speed, placed just before the note) +
    vowel (stretched over the note) + coda (kept, at the note's end). F0 = the melody (+ tremor, voice cracks that
    flip up and sag); voice = the character `who` (vo_voices settings: formant warp, breath, the man's undertone).
    sob_gaps: output times where a shaky gasp is drawn in. Returns mono float64."""
    rng = np.random.default_rng(seed)
    s = VV.VOICES.get(who, VV.VOICES['L'])
    fp = FP / 1000.0
    F0, SP, AP, MARK = [], [], [], []
    off = 0
    for bounds in lines:
        t0 = bounds[0] - 0.03
        x = vo(t0, bounds[-1] + 0.03)
        f0, sp, ap = analyze(x)
        fr = np.linspace(0, SR / 2, sp.shape[1])
        e = 10 * np.log10(sp[:, (fr > 250) & (fr < 3000)].sum(1) + 1e-20)
        for i in range(len(bounds) - 1):
            s0 = max(0, int((bounds[i] - t0) / fp)); s1 = min(len(f0), int((bounds[i + 1] - t0) / fp))
            if s1 - s0 < 4:
                s1 = min(len(f0), s0 + 4)
            seg = e[s0:s1]; vs = f0[s0:s1] > 0
            mx = seg[vs].max() if vs.any() else seg.max()
            on = np.flatnonzero((seg > mx - 4) & (vs if vs.any() else True))
            nu = s0 + (int(on[0]) if len(on) else 0)
            ve = s0 + (int(np.flatnonzero((seg > mx - 12) & (vs if vs.any() else True))[-1]) + 1 if len(on) else len(seg))
            MARK.append((off + s0, off + nu, off + max(nu + 1, ve), off + s1))
        F0.append(f0); SP.append(sp); AP.append(ap); off += len(f0)
    f0s = np.concatenate(F0); sps = np.concatenate(SP); aps = np.concatenate(AP)
    notes = sorted(notes)
    if len(notes) != len(MARK):
        raise ValueError(f'{len(notes)} notes for {len(MARK)} syllables')
    end = notes[-1][0] + notes[-1][1] + 0.4
    n = int(end / fp)
    idx = np.full(n, -1, int)
    for (a, d, _m), (s0, nu, ve, s1) in zip(notes, MARK):
        on_l = min(nu - s0, int(0.12 / fp)); coda = min(s1 - ve, int(0.10 / fp))
        o0 = max(0, int(a / fp) - on_l)
        o1 = min(n, int((a + d) / fp))
        body = o1 - o0 - on_l - coda
        if body < 2:
            continue
        seg = np.concatenate([np.arange(nu - on_l, nu), np.linspace(nu, ve - 1, body), np.arange(s1 - coda, s1)])
        idx[o0:o0 + len(seg)] = np.round(seg[:n - o0]).astype(int)
    voiced = idx >= 0
    idx_c = np.clip(idx, 0, len(f0s) - 1)
    sp = sps[idx_c]; ap = aps[idx_c]; vf = f0s[idx_c] > 0
    tn = np.array([a for a, d, m in notes]); dn = np.array([d for a, d, m in notes]); mn = np.array([m for a, d, m in notes])
    f0 = f0_line(n, tn, mn + transpose, dn, rng, vib_cents=0.0, scoop_cents=60.0, glide=0.05, drift_cents=12.0)
    t = np.arange(n) * fp
    if tremor:
        f0 *= 1 + tremor[1] * np.sin(2 * np.pi * tremor[0] * t + 0.4) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.31 * t))
    for k, (a, d, m) in enumerate(notes):                # the voice breaks: a short flip up, then it sags
        if rng.uniform() < cracks:
            i0 = int((a + d * rng.uniform(0.3, 0.6)) / fp); L = int(rng.uniform(0.05, 0.09) / fp)
            f0[i0:i0 + L] *= 2 ** (rng.uniform(3, 6) / 12.0)
            f0[i0 + L:int((a + d) / fp)] *= 2 ** (-rng.uniform(0.4, 1.2) / 12.0)
    f0 = np.where(voiced & vf, f0, 0.0)
    gate = np.where(voiced, 1.0, 1e-6)[:, None]
    y = synth(f0, VV.warp_envelope(sp, s['alpha']) * gate, VV.breathe(ap, s['breath']))
    if s.get('under') is not None:                      # the man's voice an octave down under the girl (vo_voices L)
        y2 = synth(f0 * 0.5, VV.warp_envelope(sp, 0.97) * gate, VV.breathe(ap, 0.5))
        y2 = y2[:len(y)] if len(y2) >= len(y) else np.pad(y2, (0, len(y) - len(y2)))
        y = y + y2 * 10 ** (s['under'] / 20) * (np.sqrt(np.mean(y ** 2)) / (np.sqrt(np.mean(y2 ** 2)) + 1e-12))
    if s.get('eq'):
        y = VV.eq(y, s['eq'])
    for g in sob_gaps:
        i = int(g * SR)
        sob = gasp(rng, 0.45)
        if 0 <= i < len(y):
            y[i:i + len(sob)] += sob[:len(y) - i] * np.abs(y).max() * 0.5
    return _norm(y)


def gasp(rng, dur=0.45):
    """A shaky, sobbing inhalation: two or three breaths in with a voiced catch on each."""
    out = np.zeros(int(dur * SR))
    k = rng.integers(2, 4)
    for j in range(k):
        a = int(j * dur / k * SR); b = breath_in(dur / k * 0.9, False, rng) * rng.uniform(0.6, 1.0)
        out[a:a + len(b)] += b[:len(out) - a]
        c = int(a + len(b) * 0.7); L = int(0.03 * SR)
        tt = np.arange(L) / SR
        out[c:c + L] += 0.02 * np.sin(2 * np.pi * rng.uniform(380, 520) * tt) * np.hanning(L)[:len(out[c:c + L])]
    return out


# ------------------------------------------------------------------------------------------------- crying
def cry(dur=6.0, who='L', seed=0, intensity=0.8, src=(435.32, 435.95)):
    """A lost child crying for `dur` s: wails ("aaah", "uuuh" on her own "Mama?" vowels: a rise, a long fall that
    cracks and shakes) and hiccup sobs between them, the character's voice (vo_voices: the real Laurie = a girl's
    pitch in a man's tract, the man an octave under). intensity 0..1 (more wails, higher, rougher)."""
    rng = np.random.default_rng(seed)
    s = VV.VOICES.get(who, VV.VOICES['L'])
    x = vo(*src, which='clean')
    f0s, sps, aps = analyze(x)
    v = np.flatnonzero(f0s > 0)
    if not len(v):
        raise ValueError('no voiced frames in the cry source')
    fr = np.linspace(0, SR / 2, sps.shape[1])
    loud = np.log(sps[v][:, (fr > 300) & (fr < 2500)].sum(1))
    vow = v[loud > np.percentile(loud, 55)]              # the open vowels of "Mama"
    fp = FP / 1000.0
    n = int(dur / fp)
    f0 = np.zeros(n); amp = np.zeros(n); src_i = np.zeros(n, int)
    t = 0.15
    base = s['f0'] * (1.15 + 0.25 * intensity)
    while t < dur - 0.4:
        if rng.uniform() < 0.62:                          # a wail
            L = rng.uniform(0.9, 1.9) * (0.8 + 0.4 * intensity)
            i0, i1 = int(t / fp), min(n, int((t + L) / fp))
            u = np.linspace(0, 1, i1 - i0)
            pk = rng.uniform(1.05, 1.35)
            shape = np.where(u < 0.18, 0.8 + (pk - 0.8) * np.sin(np.pi / 2 * np.clip(u / 0.18, 0, 1)),
                             pk - (pk - 0.7) * np.clip((u - 0.18) / 0.82, 0, 1) ** 1.3)
            if rng.uniform() < 0.5:                       # the voice cracks up for a moment
                c = rng.uniform(0.3, 0.6); shape *= np.where(np.abs(u - c) < 0.05, 1.33, 1.0)
            f0[i0:i1] = base * shape * (1 + 0.04 * np.sin(2 * np.pi * 7.0 * u * L))
            pulse = 1 - 0.45 * intensity * (0.5 + 0.5 * np.cos(2 * np.pi * rng.uniform(3.2, 4.6) * u * L))   # "wa-a-a"
            amp[i0:i1] = np.sin(np.pi * np.clip(u / 0.12, 0, 1) / 2) * (1 - u ** 3) ** 0.7 * pulse
            src_i[i0:i1] = vow[np.linspace(0, len(vow) - 1, i1 - i0).astype(int) % len(vow)]
            t += L + rng.uniform(0.15, 0.4)
        else:                                             # hiccup sobs: 2-4 short voiced catches
            k = rng.integers(2, 5)
            for _ in range(k):
                L = rng.uniform(0.08, 0.16)
                i0, i1 = int(t / fp), min(n, int((t + L) / fp))
                u = np.linspace(0, 1, max(1, i1 - i0))
                f0[i0:i1] = base * rng.uniform(1.1, 1.4) * (1 - 0.15 * u)
                amp[i0:i1] = np.sin(np.pi * u) * 0.7
                src_i[i0:i1] = vow[rng.integers(len(vow))]
                t += L + rng.uniform(0.06, 0.14)
            t += rng.uniform(0.2, 0.45)
    jit = 1 + 0.012 * (1 + intensity) * rng.standard_normal(n)
    f0 = np.where(amp > 0.02, f0 * jit, 0.0)
    sp = VV.warp_envelope(sps[src_i], s['alpha']) * (amp[:, None] ** 2 + 1e-10)
    ap = VV.breathe(aps[src_i], min(0.9, s['breath'] + 0.15))
    y = synth(f0, sp, ap)
    if s.get('under') is not None:
        y2 = synth(f0 * 0.5, VV.warp_envelope(sps[src_i], 0.97) * (amp[:, None] ** 2 + 1e-10), VV.breathe(aps[src_i], 0.55))
        y2 = y2[:len(y)] if len(y2) >= len(y) else np.pad(y2, (0, len(y) - len(y2)))
        y = y + y2 * 10 ** ((s['under'] + 3) / 20) * (np.sqrt(np.mean(y ** 2)) / (np.sqrt(np.mean(y2 ** 2)) + 1e-12))
    # gasps in the gaps
    tt = np.arange(len(y)) / SR
    gaps = np.flatnonzero((amp[:-1] > 0.02) & (amp[1:] <= 0.02)) * fp
    for g in gaps:
        if rng.uniform() < 0.7:
            gs = gasp(rng, rng.uniform(0.25, 0.45)); i = int((g + 0.03) * SR)
            if i < len(y):
                y[i:i + len(gs)] += gs[:len(y) - i] * (np.abs(y).max() + 1e-9) * 0.9
    if s.get('eq'):
        y = VV.eq(y, s['eq'])
    return _norm(y)
