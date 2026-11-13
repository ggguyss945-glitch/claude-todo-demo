"""Character voices for the edited narration: the quoted words of Mom, June, the little-girl voice in the Bunnyman,
Grandma, the dying man and the thing in the narrator's old body are re-voiced from the narrator's own take; the
narrator's lines are never touched (the quote / "she says" splits of script/lines.py are the cut points, so only the
quoted words change).

Method: WORLD vocoder (pyworld: Harvest F0, CheapTrick envelope, D4C aperiodicity, 5 ms frames). For each character:
  - pitch: the line's F0 is moved to the character's median (geometric) and its excursions scaled (range), with an
    optional tremor (an old voice, a frightened one) and jitter; never a plain resample, so no chipmunk;
  - formants: the spectral envelope is warped along frequency (x alpha: a smaller or larger vocal tract), independent
    of the pitch;
  - breath: the aperiodicity is raised (a breathy or whispered voice keeps its formants, loses some of its buzz);
  - optional undertone: the real Laurie is a little girl's voice in a 55-year-old man's body, so a second copy of her
    words an octave lower, with the man's formants, sits 15 dB under it;
  - a gentle tone EQ (Mom's "close and dark" lines get more low-mid, Grandma loses a little top).
Each processed line is loudness-matched to the same line dry (+ the character's offset), with 15 ms fades inside the
silence around it. The narrator measures F0 104-256 Hz (5-95 %, median 150 Hz), F1/F2/F3 480/1510/2650 Hz: a young
male voice, so every character is a real move away from him.
"""
import numpy as np

SR = 48000
NAR_F0 = 150.0                                         # the narrator's median F0 (Hz), measured on the take

# character -> settings. f0: target median Hz; rng: excursion scale; alpha: formant warp; breath: 0..1 aperiodicity mix
# (1 = whisper); trem: (Hz, depth) of F0 tremor; jit: random F0 jitter (fraction); under: undertone level dB (or None);
# eq: list of (kind, f, gain dB, q) for vo_edit's EQ; lu: loudness offset vs the dry line (dB)
VOICES = {
    'M': dict(f0=198.0, rng=0.80, alpha=1.16, breath=0.10, trem=None, jit=0.0, under=None,
              eq=[('peak', 260, 1.5, 0.9), ('hs', 6000, -1.5, 0.7)], lu=-0.5,
              desc='Mom: an adult woman, warm and too calm (median 198 Hz, flattened intonation x0.8, formants x1.16, '
                   'a touch of breath, warm low-mids)'),
    'M_dark': dict(f0=172.0, rng=0.70, alpha=1.09, breath=0.18, trem=None, jit=0.0, under=None,
                   eq=[('peak', 220, 3.0, 0.8), ('peak', 3200, -1.5, 1.0), ('hs', 6000, -2.5, 0.7)], lu=0.5,
                   desc='Mom, darker and closer (her last lines): lower (172 Hz), flatter, formants only x1.09, more '
                        'breath and chest, less top'),
    'M_shout': dict(f0=215.0, rng=0.90, alpha=1.10, breath=0.08, trem=None, jit=0.006, under=None,
                    eq=[('peak', 250, 2.5, 0.8), ('peak', 2500, 1.5, 1.0)], lu=0.5,
                    desc='Mom shouting GET OUT OF MY HOUSE: a woman\'s shout, dark (formants x1.10), a little rough'),
    'J': dict(f0=285.0, rng=1.15, alpha=1.30, breath=0.15, trem=None, jit=0.0, under=None,
              eq=[('ls', 180, -3.0, 0.7)], lu=-1.0,
              desc='June, 7: a small child (median 285 Hz, livelier intonation x1.15, formants x1.30, no chest)'),
    'J_whisper': dict(f0=285.0, rng=1.10, alpha=1.30, breath=0.82, trem=None, jit=0.0, under=None,
                      eq=[('ls', 200, -4.0, 0.7)], lu=-3.0,
                      desc='June whispering: the same child voice, mostly breath (aperiodicity 0.82), softer'),
    'L': dict(f0=262.0, rng=1.30, alpha=1.02, breath=0.45, trem=(6.5, 0.025), jit=0.010, under=-15.0,
              eq=[('peak', 400, 1.5, 1.0)], lu=-1.5,
              desc='the real Laurie in the Bunnyman: a little girl\'s pitch and sing-song intonation (262 Hz, x1.30) '
                   'over a grown man\'s vocal tract (formants x1.02), breathy (0.45), shaking (6.5 Hz tremor, jitter), '
                   'with the man\'s own voice an octave down 15 dB under it'),
    'L_whisper': dict(f0=262.0, rng=1.20, alpha=1.02, breath=0.85, trem=(6.5, 0.02), jit=0.010, under=-18.0,
                      eq=[('peak', 400, 1.0, 1.0)], lu=-3.0,
                      desc='the real Laurie whispering ("Is she humming?"): the same, mostly breath'),
    'L_scream': dict(f0=330.0, rng=1.10, alpha=1.03, breath=0.30, trem=(7.0, 0.03), jit=0.020, under=-12.0,
                     eq=[('peak', 1800, 2.0, 1.0)], lu=0.5,
                     desc='the real Laurie screaming IT\'S MY HOUSE: a girl\'s scream (330 Hz) in a man\'s body, '
                          'rough (jitter 2 %), the man\'s voice 12 dB under it'),
    'G': dict(f0=188.0, rng=0.85, alpha=1.10, breath=0.25, trem=(5.2, 0.022), jit=0.012, under=None,
              eq=[('hs', 5000, -2.0, 0.7), ('peak', 300, 1.0, 1.0)], lu=-1.0,
              desc='Grandma, remembered: an old woman (188 Hz, formants x1.10), a slow 5.2 Hz tremor and jitter, '
                   'a little breathy, softer top'),
    'D': dict(f0=150.0, rng=1.0, alpha=0.95, breath=0.80, trem=(4.0, 0.03), jit=0.03, under=None, contour='crack',
              eq=[('hs', 4500, -3.0, 0.7)], lu=-5.0,
              desc='the dying man\'s "Mama": a weak, cracked whisper (aperiodicity 0.8) with a child\'s rise-fall '
                   'contour that breaks on the second syllable and falls into creak, a grown man\'s formants (x0.95), '
                   '5 dB under the narrator'),
    'X': dict(f0=139.0, rng=0.55, alpha=0.97, breath=0.40, trem=None, jit=0.0, under=-20.0,
              eq=[('peak', 180, 1.5, 0.9), ('hs', 7000, -1.5, 0.7)], lu=-1.5,
              desc='the thing in the narrator\'s old body: the narrator\'s own voice made subtly wrong: a little lower '
                   '(x0.93), almost no melody (x0.55), whispery (0.40), formants x0.97, a faint voice an octave down'),
}
# lines that use a variant (by tag)
VARIANT = {'get_out': 'M_shout', 'happy_easter': 'M_dark', 'trick': 'M_dark', 'close_eyes': 'M_dark',
           'count_to_seven': 'M_dark', 'my_house': 'L_scream', 'is_she_humming': 'L_whisper'}
WHISPER_FX = {'whisper'}


def voice_for(line):
    who, tag, fx = line['who'], line.get('tag'), line.get('fx')
    if who == 'N': return None
    if tag in VARIANT: return VARIANT[tag]
    if who == 'J' and fx in WHISPER_FX: return 'J_whisper'
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
    """The take's F0 with tracker slips removed: voiced runs shorter than 20 ms dropped, octave jumps folded back
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
    out[v] = np.exp(np.log(s['f0']) + s['rng'] * (lf - med))
    out[v] = np.clip(out[v], s['f0'] * 0.62, s['f0'] * 1.6)
    if s.get('contour') == 'crack':                                  # the dying "Ma-ma": rise, break, fall into creak
        idx = np.where(v)[0]; n = len(idx); u = np.linspace(0, 1, n)
        shape = np.where(u < 0.35, 1.0 + 0.30 * np.sin(np.pi * u / 0.35),                    # "Ma" rises and falls
                np.where(u < 0.45, 1.25, 1.18 - 0.75 * (u - 0.45) / 0.55))                   # crack up, then sink
        out[idx] = s['f0'] * shape
        tail = idx[u > 0.8]
        out[tail] = np.maximum(55.0, out[tail] * (0.6 + 0.4 * np.random.default_rng(7).random(len(tail))))   # creak
    if s.get('trem'):
        hz, depth = s['trem']
        out[v] *= 1 + depth * np.sin(2 * np.pi * hz * t[v] + 0.7)
    if s.get('jit'):
        out[v] *= 1 + s['jit'] * np.random.default_rng(11).standard_normal(v.sum())
    return out


def breathe(ap, amount):
    """Aperiodicity raised toward 1 (noise) by 'amount' (0..1), more in the upper bands."""
    if amount <= 0: return ap
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


def revoice(x, key):
    """One stretch of the narrator's voice -> the character 'key'. Returns (y, stats)."""
    import pyworld as pw
    s = VOICES[key]
    x = np.ascontiguousarray(x, dtype=np.float64)
    f0, t = pw.harvest(x, SR, f0_floor=60.0, f0_ceil=500.0, frame_period=5.0)
    sp = pw.cheaptrick(x, f0, t, SR)
    ap = pw.d4c(x, f0, t, SR)
    f1 = new_f0(f0, s, t)
    sp1 = warp_envelope(sp, s['alpha'])
    ap1 = breathe(ap, s['breath'])
    C = np.ascontiguousarray
    y = pw.synthesize(C(f1), C(sp1), C(ap1), SR, 5.0)[:len(x)]
    if len(y) < len(x): y = np.concatenate([y, np.zeros(len(x) - len(y))])
    if s.get('under') is not None:                                   # the man under the girl
        f2 = f1 * 0.5
        sp2 = warp_envelope(sp, 0.97)
        y2 = pw.synthesize(C(f2), C(sp2), C(breathe(ap, 0.5)), SR, 5.0)[:len(x)]
        if len(y2) < len(x): y2 = np.concatenate([y2, np.zeros(len(x) - len(y2))])
        y = y + y2 * 10 ** (s['under'] / 20) * (np.sqrt(np.mean(y ** 2)) / (np.sqrt(np.mean(y2 ** 2)) + 1e-12))
    if s.get('eq'): y = eq(y, s['eq'])
    y = y * 10 ** ((speech_rms_db(x) + s['lu'] - speech_rms_db(y)) / 20)
    v0 = f0[f0 > 0]; v1 = f1[f1 > 0]
    st = {'voice': key, 'f0_in_median': round(float(np.median(v0)), 1) if len(v0) else 0,
          'f0_out_median': round(float(np.median(v1)), 1) if len(v1) else 0,
          'f0_out_p5_p95': [round(float(np.percentile(v1, 5)), 1), round(float(np.percentile(v1, 95)), 1)] if len(v1) else [0, 0],
          'formant_warp': s['alpha'], 'breath': s['breath'], 'loudness_offset_db': s['lu']}
    return y, st


def apply_voices(y, edl, sr=SR):
    """Re-voice every character line of the edited narration in place. edl: vo_edit's edit list (line 'out' times).
    Returns (new signal, report rows)."""
    assert sr == SR
    out = y.copy()
    rep = []
    for e in edl:
        key = voice_for(e)
        if key is None: continue
        a, b = e['out']
        m = 0.03                                                    # a little silence on each side (gaps are >= 0.15 s)
        i0, i1 = max(0, int((a - m) * SR)), min(len(y), int((b + m) * SR))
        seg = y[i0:i1]
        z, st = revoice(seg, key)
        f = int(0.012 * SR)
        ramp = np.sin(np.linspace(0, np.pi / 2, f)) ** 2
        z[:f] *= ramp; z[-f:] *= ramp[::-1]
        out[i0:i1] = z
        st.update({'i': e['i'], 'who': e['who'], 'tag': e['tag'], 'fx': e['fx'], 'en': e['en'], 'out': e['out'],
                   'desc': VOICES[key]['desc']})
        rep.append(st)
    return out, rep
