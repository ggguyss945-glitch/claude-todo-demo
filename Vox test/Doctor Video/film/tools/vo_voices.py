"""Character voices for the edited narration of the Doctor film: the quoted words of Grandma Ruth (G), Doctor Halverson
(H), the Waiting Man / Doctor Later (W), Milo (K), Mom (M), the ER nurse (U) and the phone-system recording (R) are
re-voiced from the narrator's own take; the narrator's lines are never touched (the quote / "she said" splits of
script/lines.py are the cut points, so only the quoted words change). vo_edit.py calls voice_line(y, line) for every
line before the layout (a voice may lengthen its line: the Waiting Man speaks slower).

Method: WORLD vocoder (pyworld: Harvest F0, CheapTrick envelope, D4C aperiodicity, 1 ms frames). For each character:
  - pitch: the line's F0 is moved to the character's median (geometric) and its excursions scaled (rng), optionally
    smoothed (an even, unhurried contour), with an optional tremor (an old voice) and jitter (a rough, tired one);
    never a plain resample, so no chipmunk;
  - formants: the spectral envelope is warped along frequency (x alpha: a smaller or larger vocal tract), independent
    of the pitch;
  - breath: the aperiodicity is raised toward noise (breathy, out of breath, whispered) or, with a negative amount,
    lowered toward pure voicing (the Waiting Man's airless, too-smooth voice);
  - tempo: the voiced frames can be stretched (the Waiting Man: vowels 1.18x slower, consonants untouched, so the words
    stay crisp and the speech is just too slow);
  - undertone: a second copy an octave lower with a longer vocal tract sits under the voice (the Waiting Man's faint
    second voice, 17 dB under);
  - a gentle tone EQ (warmth, proximity, a softer top).
Each processed line is loudness-matched to the same line dry (+ the character's offset), with 12 ms fades at its edges.
The narrator measures F0 104-271 Hz (5-95 %, median 155 Hz), F1/F2/F3 518/1713/2775 Hz (voiced frames of the 393
narrator lines of narration_clean.wav): a young adult male voice, so every character is a real move away from him.
"""
import numpy as np

SR = 48000
NAR_F0 = 155.0                                         # the narrator's median F0 (Hz), measured on the edit
FP = 1.0                                               # WORLD frame period (ms)
PAD = 0.040                                            # silence padded around a line for the analysis (s)

# character -> settings. f0: target median Hz; rng: excursion scale; smooth: F0 contour smoothing (s); alpha: formant
# warp; breath: -1..1 aperiodicity move (+ noisier, - purer); trem: (Hz, depth) F0 tremor; jit: F0 jitter (fraction);
# stretch: voiced-frame tempo factor (> 1 slower); under: (level dB, formant warp) of an octave-down copy, or None;
# eq: (kind, f, gain dB, q) bands; lu: loudness offset vs the dry line (dB)
VOICES = {
    'G': dict(f0=186.0, rng=0.85, smooth=0.0, alpha=1.11, breath=0.20, trem=(5.4, 0.024), jit=0.010, stretch=1.0, under=None,
              eq=[('hs', 5500, -2.0, 0.7), ('peak', 300, 1.0, 1.0)], lu=-1.0,
              desc='Grandma Ruth, 70s, firm and frightened: an old woman (median 186 Hz, formants x1.11), a slow 5.4 Hz '
                   'tremor and 1 % jitter, a little breathy (0.20), a softer top'),
    'G_sharp': dict(f0=198.0, rng=1.00, smooth=0.0, alpha=1.11, breath=0.14, trem=(5.4, 0.020), jit=0.014, stretch=1.0, under=None,
                    eq=[('hs', 5500, -1.5, 0.7), ('peak', 1800, 1.5, 1.0)], lu=0.0,
                    desc='Grandma cutting the doctor off ("Don\'t tell me... Don\'t you dare"): the same old woman, '
                         'higher (198 Hz) and harder, livelier pitch, more edge (+1.5 dB at 1.8 kHz), rougher (1.4 %)'),
    'G_hush': dict(f0=180.0, rng=0.70, smooth=0.0, alpha=1.11, breath=0.55, trem=(5.4, 0.030), jit=0.010, stretch=1.0, under=None,
                   eq=[('hs', 6000, -2.0, 0.7), ('ls', 180, -2.0, 0.7)], lu=-3.5,
                   desc='Grandma hushing Milo ("Shh. Not after dark. Not out loud."): a hissed, half-whispered old '
                        'voice (aperiodicity +0.55), flatter, 3.5 dB softer'),
    'G_soft': dict(f0=182.0, rng=0.80, smooth=0.0, alpha=1.11, breath=0.32, trem=(5.0, 0.032), jit=0.012, stretch=1.0, under=None,
                   eq=[('hs', 5500, -2.5, 0.7), ('peak', 300, 1.0, 1.0)], lu=-2.0,
                   desc='Grandma rocking Milo ("Just until morning, baby. It can wait."): soft and shaking (tremor 3.2 %), '
                        'breathier (0.32), 2 dB softer'),
    'H': dict(f0=196.0, rng=0.95, smooth=0.0, alpha=1.15, breath=0.12, trem=None, jit=0.004, stretch=1.0, under=None,
              eq=[('peak', 250, 1.5, 0.9), ('hs', 7000, -1.0, 0.7)], lu=-0.5,
              desc='Doctor Anna Halverson, 40s, warm and exhausted (in the car): an adult woman (196 Hz, formants x1.15), '
                   'warm low-mids, a touch of breath'),
    'H_call': dict(f0=192.0, rng=1.05, smooth=0.0, alpha=1.15, breath=0.36, trem=None, jit=0.016, stretch=1.0, under=None,
                   eq=[('peak', 250, 1.0, 0.9), ('hs', 7000, -1.0, 0.7)], lu=-0.5,
                   desc='Doctor Halverson on the 3 AM call ("rough, out of breath"): breathy (0.36) and rough (1.6 % '
                        'jitter), a little lower (192 Hz)'),
    'H_door': dict(f0=200.0, rng=1.05, smooth=0.0, alpha=1.15, breath=0.20, trem=None, jit=0.008, stretch=1.0, under=None,
                   eq=[('peak', 250, 1.2, 0.9), ('peak', 2000, 1.0, 1.0)], lu=0.0,
                   desc='Doctor Halverson on the porch: urgent and tired (200 Hz, breath 0.20, 0.8 % jitter), a little '
                        'more presence to carry through the door'),
    'W': dict(f0=116.0, rng=0.60, smooth=0.06, alpha=0.93, breath=-0.40, trem=None, jit=0.0, stretch=1.18, under=(-17.0, 0.90),
              eq=[('peak', 160, 2.5, 0.8), ('hs', 6500, -2.0, 0.7)], lu=-1.5,
              desc='the Waiting Man / Doctor Later: a soft, kind, grandfatherly man (116 Hz, formants x0.93: a longer '
                   'vocal tract) made subtly inhuman: too even (pitch range x0.60, contour smoothed over 60 ms), too '
                   'slow (vowels stretched 1.18x, consonants not), airless (aperiodicity -0.40: no breath at all), close '
                   '(+2.5 dB proximity at 160 Hz, softer top), and a faint second voice an octave under it (17 dB down)'),
    'W_count': dict(f0=116.0, rng=1.00, smooth=0.06, alpha=0.93, breath=-0.40, trem=None, jit=0.0, stretch=1.18, under=(-17.0, 0.90),
                    eq=[('peak', 160, 2.5, 0.8), ('hs', 6500, -2.0, 0.7)], lu=-1.5,
                    desc='the Waiting Man counting the pulse ("One... Two... Three..."): the same voice keeping the '
                         'count\'s own pitch movement (x1.00; flattened to x0.60-0.80 the drawn-out "Two" reads as "Till")'),
    'W_count2': dict(f0=116.0, rng=1.00, smooth=0.06, alpha=0.93, breath=-0.40, trem=None, jit=0.0, stretch=1.70, under=(-17.0, 0.90),
                     eq=[('peak', 160, 2.5, 0.8), ('hs', 6500, -2.0, 0.7)], lu=-1.5,
                     desc='the Waiting Man\'s "Two...": the same voice on the short falling "two" of "Rule number two:" '
                          '(the take\'s own count rose like a question and read as "Till"), its vowel drawn out 1.7x'),
    'W_whisper': dict(f0=116.0, rng=0.55, smooth=0.06, alpha=0.93, breath=0.45, trem=None, jit=0.0, stretch=1.12, under=(-19.0, 0.90),
                      eq=[('peak', 160, 2.0, 0.8), ('hs', 6500, -2.0, 0.7)], lu=-3.0,
                      desc='the Waiting Man as the voice in your head (outro): the same voice half-whispered (breath '
                           '0.45), a little less slow (1.12x), 3 dB softer'),
    'K': dict(f0=272.0, rng=1.10, smooth=0.0, alpha=1.33, breath=0.50, trem=None, jit=0.004, stretch=1.0, under=None,
              eq=[('ls', 200, -4.0, 0.7)], lu=-3.0,
              desc='Milo, 7, thirsty and weak, whispering: a small child (272 Hz, a child\'s vocal tract: formants x1.33), '
                   'breathy whisper that keeps every word (0.50), no chest (-4 dB under 200 Hz), 3 dB softer'),
    'M': dict(f0=205.0, rng=0.90, smooth=0.0, alpha=1.16, breath=0.08, trem=None, jit=0.0, stretch=1.0, under=None,
              eq=[('peak', 260, 1.2, 0.9)], lu=0.0,
              desc='Mom, 40s, a night-shift nurse, decisive and warm: an adult woman (205 Hz, formants x1.16), steady '
                   'intonation (x0.90), warm low-mids'),
    'U': dict(f0=188.0, rng=0.80, smooth=0.0, alpha=1.13, breath=0.06, trem=None, jit=0.0, stretch=1.0, under=None,
              eq=[('peak', 300, 1.0, 0.9), ('hs', 6000, -1.0, 0.7)], lu=0.0,
              desc='the ER nurse, calm and firm: an adult woman, lower and steadier than Mom (188 Hz, x0.80, formants '
                   'x1.13)'),
    'R': dict(f0=212.0, rng=0.65, smooth=0.05, alpha=1.18, breath=0.04, trem=None, jit=0.0, stretch=1.0, under=None,
              eq=[('ls', 200, -3.0, 0.7), ('peak', 2500, 1.5, 1.0)], lu=-1.0,
              desc='the phone-system recording: a polite automated lady (212 Hz, formants x1.18), flat and even '
                   '(x0.65, contour smoothed over 50 ms), clean (breath 0.04), thin and present (the mix adds the '
                   'phone band)'),
}
# lines that use a variant (by tag)
VARIANT = {
    'dont_tell': 'G_sharp', 'dont_dare': 'G_sharp',
    'shh': 'G_hush', 'not_after_dark': 'G_hush', 'not_out_loud': 'G_hush',
    'until_morning': 'G_soft', 'g_wait1': 'G_soft', 'g_wait2': 'G_soft',
    'this_is_halverson': 'H_call', 'sorry_hour': 'H_call', 'results_back': 'H_call',
    'count1': 'W_count', 'count2': 'W_count2', 'count3': 'W_count',
    'w_nothing': 'W_whisper', 'w_bother': 'W_whisper', 'w_wait': 'W_whisper',
}


def voice_for(line):
    who, tag, fx = line['who'], line.get('tag'), line.get('fx')
    if who == 'N': return None
    if tag in VARIANT: return VARIANT[tag]
    if who == 'H' and fx == 'door': return 'H_door'
    return who


# ============================================================================ DSP helpers
def warp_envelope(sp, alpha):
    """Spectral envelope warped along frequency: formants move by alpha (> 1 up)."""
    n = sp.shape[1]
    f = np.arange(n, dtype=np.float64)
    src = np.clip(f / alpha, 0, n - 1)
    i0 = np.floor(src).astype(int); i1 = np.minimum(i0 + 1, n - 1); w = src - i0
    lsp = np.log(sp + 1e-20)
    return np.exp(lsp[:, i0] * (1 - w) + lsp[:, i1] * w)


def clean_f0(f0):
    """The take's F0 with tracker slips removed: voiced runs shorter than 4 frames dropped, octave jumps folded back
    toward the line's median, a 5-frame median filter inside each voiced run."""
    from scipy.signal import medfilt
    f = f0.copy(); v = f > 0
    d = np.diff(np.concatenate([[0], v.astype(np.int8), [0]]))
    st, en = np.where(d == 1)[0], np.where(d == -1)[0]
    for a, b in zip(st, en):
        if b - a < 4: f[a:b] = 0.0
    v = f > 0
    if not v.any(): return f
    med = np.median(np.log2(f[v]))
    oc = np.round(np.log2(f[v]) - med)
    f[v] = f[v] * 2.0 ** (-np.where(np.abs(np.log2(f[v]) - med) > 0.6, oc, 0))
    for a, b in zip(st, en):
        if b - a >= 5 and (f[a:b] > 0).all(): f[a:b] = medfilt(f[a:b], 5)
    return f


def new_f0(f0, s, t):
    """The character's F0 track from the line's own (voiced frames only; unvoiced stay 0)."""
    f0 = clean_f0(f0)
    v = f0 > 0
    out = np.zeros_like(f0)
    if not v.any(): return out
    lf = np.log(f0[v]); med = np.median(lf)
    lo = s['rng'] * (lf - med)
    if s.get('smooth'):                                              # an even contour: smoothed inside each voiced run
        from scipy.ndimage import uniform_filter1d
        n = max(3, int(s['smooth'] * 1000 / FP))
        full = np.zeros_like(f0); full[v] = lo
        d = np.diff(np.concatenate([[0], v.astype(np.int8), [0]]))
        for a, b in zip(np.where(d == 1)[0], np.where(d == -1)[0]):
            if b - a > 3: full[a:b] = uniform_filter1d(full[a:b], size=min(n, b - a), mode='nearest')
        lo = full[v]
    out[v] = np.exp(np.log(s['f0']) + lo)
    out[v] = np.clip(out[v], s['f0'] * 0.62, s['f0'] * 1.6)
    if s.get('trem'):
        hz, depth = s['trem']
        out[v] *= 1 + depth * np.sin(2 * np.pi * hz * t[v] + 0.7)
    if s.get('jit'):
        out[v] *= 1 + s['jit'] * np.random.default_rng(11).standard_normal(v.sum())
    return out


def breathe(ap, amount):
    """Aperiodicity moved toward 1 (noise) by a positive amount (more in the upper bands), or toward 0 (pure voicing)
    by a negative one."""
    if amount == 0: return ap
    if amount < 0: return np.clip(ap * (1 + amount), 1e-6, 1)
    n = ap.shape[1]; tilt = np.linspace(0.6, 1.0, n)[None, :]
    a = np.clip(amount * tilt, 0, 0.98)
    return np.clip(ap + (1 - ap) * a, 0, 1)


def stretch_frames(f0, sp, ap, voiced, factor):
    """Variable-rate time stretch of the WORLD frames: voiced frames last 'factor' times longer, unvoiced ones keep their
    length (consonants stay crisp); the rate is smoothed over 15 ms so it never jumps."""
    from scipy.ndimage import uniform_filter1d
    w = np.where(voiced, factor, 1.0)
    w = uniform_filter1d(w, size=max(3, int(15 / FP)), mode='nearest')
    pos = np.concatenate([[0.0], np.cumsum(w)])                    # output position where source frame k starts
    m = int(round(pos[-1]))
    src = np.interp(np.arange(m), pos[:-1], np.arange(len(w)))
    i0 = np.clip(np.floor(src).astype(int), 0, len(w) - 1); i1 = np.minimum(i0 + 1, len(w) - 1); fr = (src - i0)[:, None]
    lsp = np.log(sp + 1e-20)
    sp2 = np.exp(lsp[i0] * (1 - fr) + lsp[i1] * fr)
    ap2 = ap[i0] * (1 - fr) + ap[i1] * fr
    near = np.where(fr[:, 0] < 0.5, i0, i1)
    f2 = np.where((f0[i0] > 0) & (f0[i1] > 0), f0[i0] * (1 - fr[:, 0]) + f0[i1] * fr[:, 0], f0[near])
    return f2, sp2, ap2


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


def revoice(x, key):
    """One line of the narrator's voice -> the character 'key'. Returns (y, stats); y may be longer (stretch)."""
    import pyworld as pw
    s = VOICES[key]
    pad = np.zeros(int(PAD * SR))
    xp = np.ascontiguousarray(np.concatenate([pad, x, pad]), dtype=np.float64)
    f0, t = pw.harvest(xp, SR, f0_floor=60.0, f0_ceil=500.0, frame_period=FP)
    sp = pw.cheaptrick(xp, f0, t, SR)
    ap = pw.d4c(xp, f0, t, SR)
    f1 = new_f0(f0, s, t)
    sp1 = warp_envelope(sp, s['alpha'])
    ap1 = breathe(ap, s['breath'])
    C = np.ascontiguousarray
    voiced = f1 > 0
    if s.get('stretch', 1.0) != 1.0:
        f1, sp1, ap1 = stretch_frames(f1, sp1, ap1, voiced, s['stretch'])
        _, sp_u, ap_u = stretch_frames(f0, sp, ap, voiced, s['stretch'])
    else:
        sp_u, ap_u = sp, ap
    y = pw.synthesize(C(f1), C(sp1), C(ap1), SR, FP)
    if s.get('under'):                                                # the faint second voice an octave down
        lvl, al2 = s['under']
        y2 = pw.synthesize(C(f1 * 0.5), C(warp_envelope(sp_u, al2)), C(breathe(ap_u, min(0.0, s['breath']))), SR, FP)
        n = min(len(y), len(y2)); y2 = y2[:n]; y = y[:n]
        y = y + y2 * 10 ** (lvl / 20) * (np.sqrt(np.mean(y ** 2)) / (np.sqrt(np.mean(y2 ** 2)) + 1e-12))
    n_pad = len(pad)                                                  # the pads are unvoiced: they keep their length
    y = y[n_pad:max(n_pad + 1, len(y) - n_pad)]
    if s.get('stretch', 1.0) == 1.0:
        y = y[:len(x)]
        if len(y) < len(x): y = np.concatenate([y, np.zeros(len(x) - len(y))])
    if s.get('eq'): y = eq(y, s['eq'])
    y = y * 10 ** ((speech_rms_db(x) + s['lu'] - speech_rms_db(y)) / 20)
    v0 = f0[f0 > 0]; v1 = f1[f1 > 0]
    st = {'voice': key, 'f0_in_median': round(float(np.median(v0)), 1) if len(v0) else 0,
          'f0_out_median': round(float(np.median(v1)), 1) if len(v1) else 0,
          'f0_out_p5_p95': [round(float(np.percentile(v1, 5)), 1), round(float(np.percentile(v1, 95)), 1)] if len(v1) else [0, 0],
          'formant_warp': s['alpha'], 'breath': s['breath'], 'stretch': s.get('stretch', 1.0),
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
