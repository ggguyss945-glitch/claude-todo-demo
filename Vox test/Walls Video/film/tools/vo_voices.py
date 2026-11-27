"""Child voices for "If Your Little Brother Says Someone Lives In The Walls... DON'T LAUGH" (Night Policy; the Ice Cream
film's WORLD revoice). ElevenLabs will not design child voices, so Theo (6) and Sam (12) were read in ONE adult take
(W/narration/raw/index.json: theo_and_sam_adult_take) and are re-voiced here, line by line, as tools/vo_edit.py cuts
them (vo_edit calls voice_line(y, line) for every theo / sam line). Every other character has its own take: untouched.

Method: WORLD vocoder (pyworld: Harvest F0, CheapTrick envelope, D4C aperiodicity, 1 ms frames). For each voice:
  - pitch: the line's F0 is moved to the voice's median (geometric), its excursions scaled (rng) and softly limited
    (comp: e -> comp * tanh(e / comp) octaves), with a little jitter; never a plain resample, so no chipmunk;
  - formants: the spectral envelope is warped along frequency (x alpha: a child's shorter vocal tract), independent of
    the pitch; piecewise-linear (x alpha up to 4.5 kHz, then straight to Nyquist, so the top band is not stretched into
    a hiss); voiceless frames keep only the share 'unv' of the move, easing over 15 ms;
  - "face" heard as "verse" (the first test, x1.38): the onset of a voiceless fricative before a vowel was converted
    (Harvest voices the f's last 10-20 ms, and the 8 ms crossfade widened it), so the warped vowel started with a buzz
    (a v) and its formants glided down into an "er". Fix ('fric'): a voiced run is only converted from the first frame
    whose low band (< 1 kHz) carries the voicing (D4C aperiodicity < 0.25 there), so the f stays dry noise to its
    end, and the warp eases in over the vowel's first 'ease' ms from the voiceless share (no glide from a v);
  - breath: the aperiodicity is raised a little toward noise (a child's breathy voice);
  - voicing: a frame is voiced when Harvest says so AND D4C finds it periodic below 2 kHz AND it is within 30 dB of
    the line's speech level; voiceless sounds (h, s, th, f, t, k) pass through dry with 8 ms ramps;
  - a gentle tone EQ (no chest, a little presence).
Each processed line is loudness-matched to the same line dry (+ the voice's offset), with 12 ms fades at its edges.
Test: python3 tools/vo_voices.py --test [theo|sam ...]   -> W/narration/tests/voices/<tag>_{dry,wet}.wav and
  voices_test.json: F0 in -> out, the measured formant warp (measure_warp) and Parakeet + Whisper on each line alone.
"""
import numpy as np

SR = 48000
NAR_F0 = 168.5                                         # the narrator's median F0 (Hz), measured on the take
FP = 1.0                                               # WORLD frame period (ms)
PAD = 0.040                                            # silence padded around a line for the analysis (s)
FRY = 0.8                                              # frames this many octaves under the line's median are creak
WARP_FC = 4500.0                                       # formant-warp knee (Hz of the source): see warp_envelope
XF = 8.0                                               # dry <-> converted crossfade at voicing edges (ms)
QATT = -10.0                                           # level of a quiet voiced run (a hum after a word), kept dry (dB)
UNV = 0.35                                             # share of the formant warp kept on voiceless frames (consonants)

# voice -> settings. f0: target median Hz (None: the line's own); rng: excursion scale; comp: soft limit of the scaled
# excursions in octaves; smooth: F0 contour smoothing (s); alpha: formant warp; breath: -1..1 aperiodicity move
# (+ noisier, - purer); trem: (Hz, depth) F0 tremor; jit: F0 jitter (fraction); under: (level dB, formant warp) of an
# octave-down copy, or None; eq: (kind, f, gain dB, q) bands; lu: loudness offset vs the dry line (dB).
# Tape (optional): wow: (Hz, depth) pitch+formant warble; sag: (s, semitones) pitch+formant fall over the line's last
# voiced seconds; morph: (voice, from, to) a glide into another voice over that share of the voiced span; tape: (from,
# speed) playback slowed from that share of the speech to its end, down to that speed (the word gets longer).
_B = dict(f0=None, rng=1.0, comp=None, smooth=0.0, alpha=1.0, breath=0.0, trem=None, jit=0.0, under=None, eq=None,
          lu=0.0, wow=None, sag=None, morph=None, tape=None)
_KID = dict(_B, rng=0.95, comp=0.42, breath=0.12, jit=0.004, unv=0.35, fric=True, ease=0.0, nasal=0.0)
VOICES = {
    'theo': dict(_KID, f0=285.0, alpha=1.26, lu=-0.5, eq=[('ls', 220, -4.0, 0.7), ('peak', 3200, 1.0, 1.0)],
                 desc="Theo, 6: a small boy (285 Hz; a child's vocal tract, formants x1.26: from x1.28 up the recognisers heard Larkspur as marks per in the sung address), a lively melody (x0.95), "
                      'a little breath (0.12), no chest (-4 dB under 220 Hz)'),
    'sam': dict(_KID, f0=232.0, alpha=1.245, rng=0.90, comp=0.40, breath=0.10, lu=-0.5, nasal=-20.0,
                eq=[('ls', 200, -3.0, 0.7), ('peak', 3000, 0.8, 1.0)],
                desc='Sam, 12: a boy before his voice breaks (232 Hz, formants x1.245), a calmer melody (x0.90), '
                     'a little breath (0.10), a lighter chest (-3 dB under 200 Hz)'),
}


def voice_for(line):
    return line['who'] if line.get('who') in VOICES else None


# ============================================================================ DSP helpers
def warp_envelope(sp, alpha):
    """Spectral envelope warped along frequency: formants move by alpha (> 1 up); alpha is one number or one per frame."""
    n = sp.shape[1]
    f = np.arange(n, dtype=np.float64)
    a = np.asarray(alpha, dtype=np.float64)
    lsp = np.log(sp + 1e-20)
    fc = WARP_FC / (SR / 2) * (n - 1)                                 # the knee (bins)

    def source(aa):                                                   # piecewise-linear warp: x alpha up to the knee,
        aa = np.asarray(aa)[..., None]                                # then straight to Nyquist (the top band is not
        k = fc * aa                                                   # stretched into a hiss band)
        hi = fc + (f - k) * (n - 1 - fc) / (n - 1 - k)
        return np.clip(np.where(f <= k, f / aa, hi), 0, n - 1)
    if a.ndim == 0:
        src = source(a)
        i0 = np.floor(src).astype(int); i1 = np.minimum(i0 + 1, n - 1); w = src - i0
        return np.exp(lsp[:, i0] * (1 - w) + lsp[:, i1] * w)
    if np.ptp(a) < 1e-9: return warp_envelope(sp, float(a[0]))
    out = np.empty_like(lsp)
    for k in range(0, len(a), 1000):                                 # in blocks: a long line stays small in memory
        aa = a[k:k + 1000]; lk = lsp[k:k + 1000]
        src = source(aa)
        i0 = np.floor(src).astype(np.int32); i1 = np.minimum(i0 + 1, n - 1); w = src - i0
        r = np.arange(len(aa))[:, None]
        out[k:k + 1000] = lk[r, i0] * (1 - w) + lk[r, i1] * w
    return np.exp(out)


def new_f0(f0, s, t):
    """The voice's F0 track from the line's own (voiced frames only; unvoiced stay 0)."""
    f0 = clean_f0(f0)
    v = f0 > 0
    out = np.zeros_like(f0)
    if not v.any(): return out
    lf = np.log(f0[v]); med = np.median(lf)
    tgt = s['f0'] if s.get('f0') else float(np.exp(med))
    lo = s['rng'] * (lf - med)
    if s.get('comp'):                                                # soft limit: small movements pass, big slides bend
        c = s['comp'] * np.log(2.0)
        lo = c * np.tanh(lo / c)
    fry = (lf - med) < -FRY * np.log(2.0)                            # creak keeps its own depth: compressed, a sentence-
    lo[fry] = (lf - med)[fry]                                        # final fry became a voiced extra syllable ("Theo."
    if s.get('smooth'):                                              # an even contour: smoothed inside each voiced run
        from scipy.ndimage import uniform_filter1d
        n = max(3, int(s['smooth'] * 1000 / FP))
        full = np.zeros_like(f0); full[v] = lo
        d = np.diff(np.concatenate([[0], v.astype(np.int8), [0]]))
        for a, b in zip(np.where(d == 1)[0], np.where(d == -1)[0]):
            if b - a > 3: full[a:b] = uniform_filter1d(full[a:b], size=min(n, b - a), mode='nearest')
        lo = full[v]
    out[v] = np.exp(np.log(tgt) + lo)                                # was heard "See ya")
    if s.get('f0'): out[v] = np.where(fry, np.maximum(out[v], 50.0), np.clip(out[v], tgt * 0.62, tgt * 1.6))
    if s.get('trem'):
        hz, depth = s['trem']
        out[v] *= 1 + depth * np.sin(2 * np.pi * hz * t[v] + 0.7)
    if s.get('jit'):
        out[v] *= 1 + s['jit'] * np.random.default_rng(11).standard_normal(v.sum())
    return out


def tape_curve(t, v, s):
    """Per-frame speed factor of the tape effects (multiplies F0 and the formant warp together): wow + drift, end sag."""
    m = np.ones_like(t)
    if s.get('wow'):
        from scipy.ndimage import uniform_filter1d
        hz, d = s['wow']
        dr = np.random.default_rng(7).standard_normal(len(t) + 2000)
        for _ in range(3): dr = uniform_filter1d(dr, size=int(600 / FP), mode='wrap')     # a drift under ~1 Hz
        dr = dr[1000:1000 + len(t)]; dr = dr / (dr.std() + 1e-12)
        m *= 1 + d * np.sin(2 * np.pi * hz * t + 0.4) + 0.5 * d * dr
    if s.get('sag') and v.any():
        dur, st = s['sag']
        e = int(np.where(v)[0][-1]); a = max(0, e - int(dur * 1000 / FP))
        r = np.zeros_like(t); r[a:e + 1] = np.linspace(0, 1, e + 1 - a) ** 2; r[e + 1:] = 1
        m *= 2.0 ** (-st / 12.0 * r)
    return m


def frame_db(xp, n):
    k = int(SR * FP / 1000); m = min(n, len(xp) // k)
    p = np.full(n, -200.0)
    p[:m] = 10 * np.log10((xp[:m * k].reshape(m, k) ** 2).mean(1) + 1e-20)
    return p


def voiced_gate(xp, f0, ap, floor=30.0, ap_max=0.5):
    """Frames that are really voiced: Harvest says so, D4C finds them periodic below 2 kHz (aperiodicity < ap_max: a
    breathy h reads 1.0 there and a vowel 0.01-0.02, while Harvest calls both voiced) and they are within 'floor' dB of
    the line's speech level (Harvest also "voices" -60 dB silence after a word)."""
    from scipy.ndimage import uniform_filter1d
    lo = ap[:, :max(1, int(ap.shape[1] * 2000 / (SR / 2)))].mean(1)
    p = uniform_filter1d(frame_db(xp, len(f0)), size=5, mode='nearest')
    return (f0 > 0) & (lo < ap_max) & (p > speech_rms_db(xp) - floor)


def quiet_runs(xp, f1, below=18.0):
    """Frames of voiced runs whose loudest 1 ms frame is 'below' dB or more under the line's speech level: a breath or a
    click the tracker called voiced ("He..." ends on one); they stay unvoiced (dry), never a converted syllable."""
    from scipy.ndimage import uniform_filter1d
    p = uniform_filter1d(frame_db(xp, len(f1)), size=int(10 / FP), mode='nearest')     # 10 ms level, not 1 ms peaks
    ref = speech_rms_db(xp)
    out = np.zeros(len(f1), bool)
    d = np.diff(np.concatenate([[0], (f1 > 0).astype(np.int8), [0]]))
    for a, b in zip(np.where(d == 1)[0], np.where(d == -1)[0]):
        if p[a:b].max() < ref - below: out[a:b] = True
    return out


def ramp_share(n, v, a, b):
    """0 -> 1 (smoothstep) between the shares a and b of the voiced span of n frames."""
    vi = np.where(v)[0]
    if not len(vi): return np.zeros(n)
    pos = (np.arange(n) - vi[0]) / max(1, vi[-1] - vi[0])
    r = np.clip((pos - a) / max(1e-6, b - a), 0, 1)
    return r * r * (3 - 2 * r)


def tape_slow(y, a, speed):
    """Playback slowed like a stopping tape: speed 1 until the share a of the speech, easing to 'speed' at its end (and
    held after it). Pitch and formants fall together; the signal gets longer. Returns (y', its length / the input's)."""
    w = int(0.01 * SR); n = len(y) // w
    p = (y[:n * w].reshape(n, w) ** 2).mean(1); pdb = 10 * np.log10(p + 1e-20)
    on = np.where(pdb > pdb.max() - 35)[0]
    if not len(on): return y, 1.0
    s0, s1 = on[0] * w, (on[-1] + 1) * w
    k0 = s0 + a * (s1 - s0)
    pos = np.arange(len(y), dtype=np.float64)
    r = np.clip((pos - k0) / max(1.0, s1 - k0), 0, 1); r = r * r * (3 - 2 * r)
    sp = 1.0 + (speed - 1.0) * r                                      # speed at each input position
    T = np.concatenate([[0.0], np.cumsum(1.0 / sp[:-1])])            # output time of each input sample
    m = int(T[-1])
    src = np.interp(np.arange(m), T, pos)
    return np.interp(src, pos, y), m / len(y)


def revoice(x, key):
    """One line of the narrator's voice -> the voice 'key'. Returns (y, stats); y is longer only with 'tape'."""
    import pyworld as pw
    s = VOICES[key]
    pad = np.zeros(int(PAD * SR))
    xp = np.ascontiguousarray(np.concatenate([pad, x, pad]), dtype=np.float64)
    f0, t = pw.harvest(xp, SR, f0_floor=60.0, f0_ceil=500.0, frame_period=FP)
    ap = pw.d4c(xp, f0, t, SR)
    f0 = f0 * voiced_gate(xp, f0, ap)
    sp = pw.cheaptrick(xp, f0, t, SR)
    f1 = new_f0(f0, s, t)
    q = quiet_runs(xp, f1)
    f1[q] = 0.0
    if s.get('fric'):                                                 # a voiced run starts converting only where the
        lo = ap[:, :max(1, int(ap.shape[1] * 1000 / (SR / 2)))].mean(1)   # low band carries the voicing: the end of
        d = np.diff(np.concatenate([[0], (f1 > 0).astype(np.int8), [0]]))   # an f / s / th before a vowel stays dry
        for a_, b_ in zip(np.where(d == 1)[0], np.where(d == -1)[0]):    # noise ("face" was heard as "verse")
            k = a_
            while k < b_ and lo[k] >= 0.25: k += 1
            f1[a_:k] = 0.0
    v = f1 > 0
    alpha = np.full(len(t), s['alpha'])
    ap1 = breathe(ap, s['breath'])
    under = s.get('under')
    ug = np.ones(len(t))                                              # the second voice's level, per frame (0..1)
    if s.get('morph'):                                                # a glide into another voice
        k2, a_, b_ = s['morph']; s2 = VOICES[k2]
        r = ramp_share(len(t), v, a_, b_)
        f2 = new_f0(f0, s2, t)
        f1 = np.where(v, np.exp(np.log(np.maximum(f1, 1e-3)) * (1 - r) + np.log(np.maximum(f2, 1e-3)) * r), 0.0)
        alpha = s['alpha'] ** (1 - r) * s2['alpha'] ** r
        ap1 = ap1 * (1 - r[:, None]) + breathe(ap, s2['breath']) * r[:, None]
        if s2.get('under') and not under: under, ug = s2['under'], r
    from scipy.ndimage import uniform_filter1d                       # consonants keep their noise: the full warp on
    wv = uniform_filter1d(v.astype(np.float64), size=int(15 / FP), mode='nearest')   # voiced frames, a third of it on
    if s.get('ease'):                                                 # the warp eases in over a vowel's first ms
        rr = np.zeros(len(v)); d = np.diff(np.concatenate([[0], v.astype(np.int8), [0]]))
        for a_, b_ in zip(np.where(d == 1)[0], np.where(d == -1)[0]):
            rr[a_:b_] = np.clip((np.arange(b_ - a_) + 1) / (s['ease'] / FP), 0, 1)
        wv = np.minimum(wv, uniform_filter1d(rr, size=int(5 / FP), mode='nearest'))
    if s.get('nasal'):                                                # a nasal murmur (n, m: little energy above
        fb = np.arange(sp.shape[1]) * (SR / 2) / (sp.shape[1] - 1)    # 1 kHz) keeps the voiceless share of the warp:
        r = 10 * np.log10(sp[:, (fb >= 1000) & (fb < 4000)].sum(1) / (sp[:, fb < 800].sum(1) + 1e-20) + 1e-20)
        mur = uniform_filter1d((v & (r < s['nasal'])).astype(np.float64), size=int(10 / FP), mode='nearest')
        wv = wv * (1 - mur)                                           # fully warped it read as an l ("Night" -> "Like")
    unv = s.get('unv', UNV)
    alpha = np.exp(np.log(alpha) * (unv + (1 - unv) * wv))         # voiceless ones (x1.38 turned "He"/"Theo" into "See")
    m = tape_curve(t, v, s)
    f1 = f1 * m; alpha = alpha * m
    C = np.ascontiguousarray
    y = pw.synthesize(C(f1), C(warp_envelope(sp, alpha)), C(ap1), SR, FP)
    if under:                                                         # the faint second voice an octave down
        lvl, al2 = under
        y2 = pw.synthesize(C(f1 * 0.5), C(warp_envelope(sp, al2 * m)), C(breathe(ap, min(0.0, s['breath']))), SR, FP)
        n = min(len(y), len(y2)); y2 = y2[:n]; y = y[:n]
        g = np.interp(np.arange(n), np.arange(len(ug)) * FP * SR / 1000.0, ug)
        y = y + y2 * g * 10 ** (lvl / 20) * (np.sqrt(np.mean(y ** 2)) / (np.sqrt(np.mean(y2 ** 2)) + 1e-12))
    n = min(len(y), len(xp)); y = y[:n]                              # voiceless sounds pass through dry
    fr = np.arange(n) * 1000.0 / (FP * SR)                           # sample -> frame position
    from scipy.ndimage import maximum_filter1d                     # the ramp lies on the voiceless side, so only
    wv = maximum_filter1d(v.astype(np.float64), size=int(XF / FP) + 1, mode='nearest')    # noise meets noise (centred
    wv = uniform_filter1d(wv, size=int(XF / FP), mode='nearest')     # on the edge, the dry and the converted voicing
    g = np.interp(fr, np.arange(len(wv)), wv)                        # would overlap out of phase)
    qd = np.interp(fr, np.arange(len(q)), uniform_filter1d(q.astype(np.float64), size=int(XF / FP), mode='nearest'))
    y = y * g + xp[:n] * (1 - g) * (1 - (1 - 10 ** (QATT / 20)) * qd)
    n_pad = len(pad)
    y = y[n_pad:n_pad + len(x)]
    if len(y) < len(x): y = np.concatenate([y, np.zeros(len(x) - len(y))])
    if s.get('eq'): y = eq(y, s['eq'])
    grow = 1.0
    if s.get('tape'): y, grow = tape_slow(y, *s['tape'])
    y = y * 10 ** ((speech_rms_db(x) + s['lu'] - speech_rms_db(y)) / 20)
    v0 = f0[f0 > 0]; v1 = f1[f1 > 0]
    st = {'voice': key, 'f0_in_median': round(float(np.median(v0)), 1) if len(v0) else 0,
          'f0_out_median': round(float(np.median(v1)), 1) if len(v1) else 0,
          'f0_out_p5_p95': [round(float(np.percentile(v1, 5)), 1), round(float(np.percentile(v1, 95)), 1)] if len(v1) else [0, 0],
          'formant_warp': s['alpha'] if not s.get('morph') else f"{s['alpha']}->{VOICES[s['morph'][0]]['alpha']}",
          'breath': s['breath'], 'tape_end_speed': s['tape'][1] if s.get('tape') else 1.0,
          'loudness_offset_db': s['lu'], 'dur_in': round(len(x) / SR, 3), 'dur_out': round(len(y) / SR, 3)}
    return y, st


def voice_line(y, line):
    """vo_edit.py's hook: (voiced line, stats) for a character line, (y, None) for the narrator."""
    key = voice_for(line)
    if key is None: return y, None
    z, st = revoice(y, key)
    f = int(0.012 * SR)
    ramp = np.sin(np.linspace(0, np.pi / 2, f)) ** 2
    if len(z) > 2 * f: z[:f] *= ramp; z[-f:] *= ramp[::-1]
    st.update({'who': line['who'], 'tag': line['tag'], 'fx': line['fx'], 'en': line['en'], 'desc': VOICES[key]['desc']})
    return z, st



def clean_f0(f0):
    """Harvest's F0 with its rare slips removed: voiced runs shorter than 4 frames dropped; a frame more than half an
    octave from the median of the voiced frames within +-40 ms (a spike at an onset) takes that median; a 5-frame median
    filter inside each voiced run. Nothing is folded toward the line's median: the narrator's real range is wide (104-271
    Hz, single sentences slide from 270 to 90 Hz) and Harvest follows it (99 % agreement with Praat, no abrupt jumps)."""
    from scipy.signal import medfilt
    from scipy.ndimage import median_filter
    f = f0.copy(); v = f > 0
    d = np.diff(np.concatenate([[0], v.astype(np.int8), [0]]))
    st, en = np.where(d == 1)[0], np.where(d == -1)[0]
    for a, b in zip(st, en):
        if b - a < 4: f[a:b] = 0.0; continue
        lf = np.log2(f[a:b])
        loc = median_filter(lf, size=min(81, 2 * ((b - a) // 2) + 1), mode='nearest')
        bad = np.abs(lf - loc) > 0.5
        lf[bad] = loc[bad]
        f[a:b] = 2.0 ** lf
        if b - a >= 5: f[a:b] = medfilt(f[a:b], 5)
    return f


def breathe(ap, amount):
    """Aperiodicity moved toward 1 (noise) by a positive amount (more in the upper bands), or toward 0 (pure voicing)
    by a negative one."""
    if amount == 0: return ap
    if amount < 0: return np.clip(ap * (1 + amount), 1e-6, 1)
    n = ap.shape[1]; tilt = np.linspace(0.6, 1.0, n)[None, :]
    a = np.clip(amount * tilt, 0, 0.98)
    return np.clip(ap + (1 - ap) * a, 0, 1)


def eq(y, bands):
    """Biquad EQ (RBJ cookbook): ('peak'|'ls'|'hs', f, gain dB, q)."""
    from scipy import signal
    for kind, f0, g, q in bands:
        A = 10 ** (g / 40); w = 2 * np.pi * f0 / SR; cw, sw = np.cos(w), np.sin(w); al = sw / (2 * q)
        if kind == 'peak':
            b = [1 + al * A, -2 * cw, 1 - al * A]; a = [1 + al / A, -2 * cw, 1 - al / A]
        elif kind == 'ls':
            sA = np.sqrt(A)
            b = [A * ((A + 1) - (A - 1) * cw + 2 * sA * al), 2 * A * ((A - 1) - (A + 1) * cw), A * ((A + 1) - (A - 1) * cw - 2 * sA * al)]
            a = [(A + 1) + (A - 1) * cw + 2 * sA * al, -2 * ((A - 1) + (A + 1) * cw), (A + 1) + (A - 1) * cw - 2 * sA * al]
        else:
            sA = np.sqrt(A)
            b = [A * ((A + 1) + (A - 1) * cw + 2 * sA * al), -2 * A * ((A - 1) + (A + 1) * cw), A * ((A + 1) + (A - 1) * cw - 2 * sA * al)]
            a = [(A + 1) - (A - 1) * cw + 2 * sA * al, 2 * ((A - 1) - (A + 1) * cw), (A + 1) - (A - 1) * cw - 2 * sA * al]
        y = signal.lfilter(np.array(b) / a[0], np.array(a) / a[0], y)
    return y


def speech_rms_db(y):
    w = int(0.01 * SR); n = len(y) // w
    if n < 2: return -99.0
    p = (y[:n * w].reshape(n, w) ** 2).mean(1); pdb = 10 * np.log10(p + 1e-20)
    sel = pdb > pdb.max() - 20
    return float(10 * np.log10(p[sel].mean() + 1e-20))


def formants_median(y):
    """Median F1/F2/F3 (Hz) over the voiced frames (Praat Burg, 5 formants up to 5.5 kHz) and the F0 median."""
    import parselmouth
    s = parselmouth.Sound(y, SR)
    p = s.to_pitch_ac(time_step=0.01, pitch_floor=60, pitch_ceiling=600); f = p.selected_array['frequency']
    fm = s.to_formant_burg(time_step=0.01, max_number_of_formants=5, maximum_formant=5500)
    F = [[], [], []]
    for t, fv in zip(p.xs(), f):
        if fv > 0:
            for k in range(3):
                v = fm.get_value_at_time(k + 1, t)
                if v == v: F[k].append(v)
    return [round(float(np.median(v))) if v else 0 for v in F], (round(float(np.median(f[f > 0])), 1) if (f > 0).any() else 0)


def measure_warp(dry, wet):
    """The formant shift actually achieved: the frequency warp alpha (0.75-1.55) that best maps the dry line's average
    log spectral envelope (WORLD CheapTrick, voiced frames, 150-5500 Hz) onto the voiced line's; and both lines' median
    F0. Independent of the F0 change (the envelope is pitch-adaptive), so a child voice that is only a raised pitch
    (a falsetto) measures ~1.0 here."""
    import pyworld as pw
    def env(y):
        y = np.ascontiguousarray(y, dtype=np.float64)
        f0, t = pw.harvest(y, SR, f0_floor=60.0, f0_ceil=600.0, frame_period=5.0)
        sp = pw.cheaptrick(y, f0, t, SR)
        v = f0 > 0
        if v.sum() < 3: return None, 0.0
        return np.log(sp[v] + 1e-20).mean(0), float(np.median(f0[v]))
    e0, f00 = env(dry); e1, f01 = env(wet)
    if e0 is None or e1 is None: return None, f00, f01
    n = len(e0); f = np.arange(n) * SR / 2 / (n - 1)
    band = (f > 150) & (f < 5500)
    best, ba = 1e9, 1.0
    for a in np.arange(0.75, 1.551, 0.01):
        w = np.interp(f / a, f, e0)                                  # dry envelope moved up by a
        d = (w - w[band].mean()) - (e1 - e1[band].mean())
        err = float(np.mean(d[band] ** 2))
        if err < best: best, ba = err, a
    return round(float(ba), 2), round(f00, 1), round(f01, 1)


# ============================================================================ test: the voices on the cut lines
_REC = {}


def hear(y, pad=0.3):
    """(Parakeet, Whisper) on one line alone, padded with silence."""
    import soxr, sherpa_onnx, os
    m = os.environ.get('VO_MODELS', '/tmp/claude-0/-home-user-claude-todo-demo/aa250ae7-a0b4-594f-9bc6-bd18b596cf27/scratchpad/models')
    if not _REC:
        pk, wd = m + '/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8', m + '/sherpa-onnx-whisper-base.en'
        _REC['p'] = sherpa_onnx.OfflineRecognizer.from_transducer(
            encoder=f'{pk}/encoder.int8.onnx', decoder=f'{pk}/decoder.int8.onnx', joiner=f'{pk}/joiner.int8.onnx',
            tokens=f'{pk}/tokens.txt', model_type='nemo_transducer', num_threads=2)
        _REC['w'] = sherpa_onnx.OfflineRecognizer.from_whisper(
            encoder=f'{wd}/base.en-encoder.int8.onnx', decoder=f'{wd}/base.en-decoder.int8.onnx',
            tokens=f'{wd}/base.en-tokens.txt', num_threads=2)
    z = np.concatenate([np.zeros(int(16000 * pad)), soxr.resample(y, SR, 16000), np.zeros(int(16000 * pad))]).astype(np.float32)
    out = []
    for k in ('p', 'w'):
        st = _REC[k].create_stream(); st.accept_waveform(16000, z); _REC[k].decode_stream(st); out.append(st.result.text.strip())
    return out


def _test(args):
    import json, os, soundfile as sf
    import vo_edit as V
    sel = [a for a in args if '=' not in a]
    for a in args:                                                    # key=value: try a setting on the selected voices
        if '=' in a:
            k, v = a.split('=')
            for kk in (sel or VOICES):
                if kk in VOICES: VOICES[kk][k] = float(v)
    L = V.prepared()
    out = os.path.join(V.N, 'tests', 'voices'); os.makedirs(out, exist_ok=True)
    res, bad = [], 0
    for l in L:
        if l['who'] not in VOICES or (sel and l['who'] not in sel): continue
        y, _ = V.line_audio(l)
        z, st = voice_line(y.copy(), l)
        st['measured_warp'], _, _ = measure_warp(y, z)
        st['heard_dry'], st['heard'] = hear(y), hear(z)
        ok = [V.toks(h) == V.toks(l['en']) for h in st['heard']]
        st['word_perfect'] = ok; bad += not all(ok)
        sf.write(os.path.join(out, l['tag'] + '_dry.wav'), y.astype(np.float32), SR)
        sf.write(os.path.join(out, l['tag'] + '_wet.wav'), z.astype(np.float32), SR)
        print('%-30s F0 %5.1f->%5.1f warp %s | P: %s | W: %s %s' % (l['tag'], st['f0_in_median'], st['f0_out_median'],
              st['measured_warp'], st['heard'][0], st['heard'][1], '' if all(ok) else '  <-- MISMATCH'))
        res.append(st)
    json.dump(res, open(os.path.join(out, 'voices_test.json'), 'w'), indent=1)
    print('%d lines, %d not word-perfect on both recognisers' % (len(res), bad))
    return 1 if bad else 0


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--test': sys.exit(_test(sys.argv[2:]))
    print(__doc__)
