"""Voice places for "If a Girl Is OBSESSED With Being Your Only Friend... DON'T WRITE YOUR NAME" (Night Policy; the
Buttons film's tool), baked into the voice track by tools/vo_edit.py (lines.py 'fx'; the mix must not add them again).
Tasteful and intelligible: every processed line is loudness-matched to the dry line (+ OFFSET) and must still pass the
recogniser on its own (tools/vo_asrcheck.py --every). The narrator is never processed.
    message    Evie's messages ("Are you awake?", "Why aren't you answering?", "There. Now it's only me.", the two dinner
               lines) and Danny's old "Please stop. You're scaring me.": close (+2.5 dB under 180 Hz, +1.5 dB air at
               4.5 kHz) with a faint cold digital sheen: a sample-held copy of the top (> 3.5 kHz, aliasing like a cheap
               phone speaker, -24 dB) and a 1.7 ms comb (-17 dB)
    letterbox  Evie through the letterbox (her lines 12-14): close (+2 dB under 200 Hz), flat (a gentle 2:1 leveller,
               no room), a little muffled by the slot (-5 dB shelf from 2.8 kHz) with the metal flap's small ring
               (+2 dB at 1.25 kHz, a 0.45 ms reflection at -20 dB) and a tiny box tail (0.06 s, -28 dB)
    thin       her last sung line "Only me. I'm here, I'm he-" (already slowed into the cut by vo_voices.py): stretched
               thin by effect: the body thins more and more along the line (a 650 Hz-5 kHz band blended in from 20 % to
               85 %), a faint high detuned double (+12 cents, 11 ms, -16 dB); the voice stops dead on "he-" (a 10 ms fade,
               no click) and only a short airy tail of the thin layer rings on (0.25 s decay, about 12 dB under the voice)
    tape       little Adam's song at seven, heard off Mom's old VHS camcorder tape: warm and band-limited (160 Hz-7 kHz,
               +2 dB at 300 Hz, -2.5 dB from 4 kHz, a soft tape drive), a touch of wow (0.55 Hz, 0.25 %) and flutter
               (7.5 Hz, 0.06 %) and a faint hiss under the voice only (-40 dB); every word still clear
"""
import numpy as np
from scipy import signal

SR = 48000
OFFSET = {'message': -1.0, 'letterbox': -0.5, 'thin': -1.0, 'tape': -1.0,
          'whisper': -1.0, 'car': 0.0, 'double': 0.0, 'tall': 0.5, 'phone': -1.0}
TAIL = {'message': 0.0, 'letterbox': 0.06, 'thin': 0.32, 'tape': 0.0,
        'whisper': 0.0, 'car': 0.08, 'double': 0.03, 'tall': 0.70, 'phone': 0.0}   # decay past the line (s)


def _sos(kind, f, order=2, q=None):
    return signal.butter(order, f, kind, fs=SR, output='sos')


def peak(y, f, g, q):
    """RBJ peaking EQ."""
    A = 10 ** (g / 40); w = 2 * np.pi * f / SR; al = np.sin(w) / (2 * q)
    b = [1 + al * A, -2 * np.cos(w), 1 - al * A]; a = [1 + al / A, -2 * np.cos(w), 1 - al / A]
    return signal.lfilter(np.array(b) / a[0], np.array(a) / a[0], y)


def shelf(y, f, g, high=True):
    A = 10 ** (g / 40); w = 2 * np.pi * f / SR; al = np.sin(w) / 2 * np.sqrt(2); c = np.cos(w); s = 2 * np.sqrt(A) * al
    if high:
        b = [A * ((A + 1) + (A - 1) * c + s), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - s)]
        a = [(A + 1) - (A - 1) * c + s, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - s]
    else:
        b = [A * ((A + 1) - (A - 1) * c + s), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - s)]
        a = [(A + 1) + (A - 1) * c + s, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - s]
    return signal.lfilter(np.array(b) / a[0], np.array(a) / a[0], y)


def room(dur, rt, lp, seed, dens=1.0):
    """A small diffuse decay: filtered noise with an exponential envelope (rt = -60 dB time)."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR); t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-6.91 * t / rt) * dens
    ir = signal.sosfilt(_sos('lowpass', lp), ir)
    ir[:int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
    return ir / np.sqrt(np.sum(ir ** 2))


def mix_wet(dry, wet, db):
    wet = wet[:len(dry)] if len(wet) >= len(dry) else np.concatenate([wet, np.zeros(len(dry) - len(wet))])
    return dry + wet * 10 ** (db / 20) * np.sqrt(np.mean(dry ** 2) / (np.mean(wet ** 2) + 1e-20))


def speech_db(y):
    """The edit's speech level (tools/vo_edit.py speech_level: median 20 ms level within 20 dB of the loudest)."""
    w = int(0.02 * SR); n = len(y) // w
    p = 10 * np.log10((y[:n * w].reshape(n, w) ** 2).mean(1) + 1e-20)
    return float(np.median(p[p > p.max() - 20]))


def _pad(y, fx):
    return np.concatenate([np.asarray(y, dtype=np.float64), np.zeros(int(TAIL[fx] * SR))])


def _late(y, sec):
    d = int(sec * SR)
    return np.concatenate([np.zeros(d), y[:len(y) - d]])


def world(y, semis=0.0, alpha=1.0):
    """The line re-synthesised by WORLD with its pitch moved (semitones) and its formants warped (alpha)."""
    import pyworld as pw
    from vo_voices import warp_envelope
    x = np.ascontiguousarray(y, dtype=np.float64)
    f0, t = pw.harvest(x, SR, f0_floor=70.0, f0_ceil=800.0, frame_period=5.0)
    sp = pw.cheaptrick(x, f0, t, SR); ap = pw.d4c(x, f0, t, SR)
    if alpha != 1.0: sp = warp_envelope(sp, alpha)
    z = pw.synthesize(np.ascontiguousarray(f0 * 2 ** (semis / 12)), np.ascontiguousarray(sp), np.ascontiguousarray(ap), SR, 5.0)
    return np.concatenate([z, np.zeros(max(0, len(x) - len(z)))])[:len(x)]


def whisper(y):
    z = shelf(_pad(y, 'whisper'), 180, 2.5, high=False)
    z = peak(z, 4500, 1.5, 0.8)
    top = signal.sosfilt(_sos('highpass', 3500, 4), z)
    held = np.repeat(top[::5], 5)[:len(top)]                         # sample-and-hold: a cheap screen speaker's aliasing
    held = signal.sosfilt(_sos('highpass', 3500, 2), held)
    z = mix_wet(z, held, -24)
    d = int(0.0017 * SR); c = np.zeros_like(z); c[d:] = z[:-d]
    return mix_wet(z, c, -17)


def car(y):
    z = _pad(y, 'car')
    z = mix_wet(z, signal.fftconvolve(z, room(0.12, 0.08, 3500, 21))[:len(z)], -26)
    return z


def double(y):
    z = _pad(y, 'double')
    a = _late(world(z, semis=0.09), 0.014)                           # +9 cents
    b = _late(world(z, semis=-0.07), 0.023)                          # -7 cents
    z = mix_wet(mix_wet(z, a, -12), b, -16)
    return shelf(z, 7000, -1.5, high=True)


def tall(y):
    z = _pad(y, 'tall')
    low = _late(world(z, semis=-3.0, alpha=0.90), 0.020)
    det = _late(world(z, semis=0.14), 0.009)
    w = mix_wet(mix_wet(z, low, -9), det, -14)
    w = shelf(w, 160, 2.0, high=False)
    rv = signal.fftconvolve(_late(w, 0.025), room(1.2, 0.9, 5000, 23))[:len(w)]
    return mix_wet(w, rv, -17)


def phone(y):
    z = signal.sosfilt(_sos('bandpass', [320, 3600], 4), y)
    z = peak(z, 1900, 2.0, 1.0)
    g = np.max(np.abs(z)) + 1e-12
    z = np.tanh(1.6 * z / g) / np.tanh(1.6) * g                     # a small speaker's soft drive
    return signal.sosfilt(_sos('bandpass', [300, 3800], 2), z)


def message(y):
    z = whisper(y)
    return z[:len(y) + int(TAIL['message'] * SR)]


def level_flat(z, ratio=2.0, win=0.03, rng_db=6.0):
    """A gentle leveller: each 30 ms moves (1 - 1/ratio) of its way to the speech level, within +-rng_db."""
    from scipy.ndimage import uniform_filter1d
    e = 10 * np.log10(uniform_filter1d(z * z, int(win * SR)) + 1e-12)
    ref = speech_db(z)
    g = np.clip((ref - e) * (1 - 1 / ratio), -rng_db, rng_db)
    g = np.where(e < ref - 30, 0.0, g)                                # leave the quiet bits (gaps, tails) alone
    g = uniform_filter1d(g, int(0.02 * SR))
    return z * 10 ** (g / 20)


def letterbox(y):
    z = shelf(_pad(y, 'letterbox'), 200, 2.0, high=False)
    z = shelf(z, 2800, -5.0, high=True)
    z = peak(z, 1250, 2.0, 2.5)
    d = int(0.00045 * SR); c = np.zeros_like(z); c[d:] = z[:-d]
    z = mix_wet(z, c, -20)
    z = level_flat(z)
    return mix_wet(z, signal.fftconvolve(z, room(0.08, 0.06, 3000, 31))[:len(z)], -28)


def thin(y):
    n0 = len(y)
    z = _pad(y, 'thin')
    band = signal.sosfilt(_sos('bandpass', [650, 5000], 2), z)
    band *= np.sqrt(np.mean(z ** 2) / (np.mean(band ** 2) + 1e-20))
    r = np.clip(np.arange(len(z)) / max(1, n0), 0, 1)
    r = 0.20 + 0.65 * r ** 1.4
    w = z * (1 - r) + band * r
    w = mix_wet(w, _late(world(w, semis=0.12), 0.011), -16)
    head = w.copy(); head[n0:] = 0.0                                  # the voice stops dead at the cut ...
    tl = signal.fftconvolve(head * (np.arange(len(head)) > n0 - int(0.25 * SR)), room(0.40, 0.25, 6500, 41))[:len(w)]
    tl = signal.sosfilt(_sos('highpass', 900, 2), tl)                 # ... and a short airy tail of the thin layer
    tl[:n0] *= np.linspace(0, 1, n0) ** 4                             # rings on after it (under the line it is faint)
    out = mix_wet(head, tl, -19)
    f = int(0.10 * SR); out[-f:] *= np.linspace(1, 0, f) ** 2
    return out


def tape(y):
    z = _pad(y, 'tape')
    n = len(z); t = np.arange(n) / SR
    rng = np.random.default_rng(5)
    dr = signal.sosfiltfilt(_sos('lowpass', 0.8), rng.standard_normal(n)); dr /= (np.abs(dr).max() + 1e-12)
    # wow 0.25 % at 0.55 Hz (delay depth D = dev / (2 pi f)), flutter 0.06 % at 7.5 Hz, a slow drift
    dly = 0.0025 / (2 * np.pi * 0.55) * np.sin(2 * np.pi * 0.55 * t) + 0.0006 / (2 * np.pi * 7.5) * np.sin(2 * np.pi * 7.5 * t + 1.1) + 0.0004 * dr
    dly -= dly.min()
    z = np.interp(np.arange(n) - dly * SR, np.arange(n), z)
    z = signal.sosfilt(_sos('highpass', 160, 2), z)
    z = signal.sosfilt(_sos('lowpass', 7000, 4), z)
    z = peak(z, 300, 2.0, 0.8)
    z = shelf(z, 4000, -2.5, high=True)
    g = np.max(np.abs(z)) + 1e-12
    z = np.tanh(1.4 * z / g) / np.tanh(1.4) * g                       # a soft tape drive
    hs = signal.sosfilt(_sos('bandpass', [1500, 8000], 2), rng.standard_normal(n))
    env = np.ones(n); f = int(0.04 * SR); env[:f] = np.linspace(0, 1, f); env[-f:] = np.linspace(1, 0, f)
    hs *= env * np.sqrt(np.mean(z ** 2)) / (np.sqrt(np.mean(hs ** 2)) + 1e-12) * 10 ** (-40 / 20)
    return z + hs


FX = {'message': message, 'letterbox': letterbox, 'thin': thin, 'tape': tape,
      'whisper': whisper, 'car': car, 'double': double, 'tall': tall, 'phone': phone}


def apply(y, fx):
    """The line in its place, loudness-matched to the dry line + OFFSET; same length plus TAIL."""
    f = FX.get(fx)
    if f is None: return y
    z = f(np.asarray(y, dtype=np.float64))
    z *= 10 ** ((speech_db(y) + OFFSET[fx] - speech_db(z)) / 20)
    n = int(0.004 * SR)
    z[-n:] *= np.linspace(1, 0, n)
    return z
