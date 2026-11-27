"""Voice places for "If Your Mom's Eyes Turn Into Buttons... DON'T KEEP HER SECRET" (Night Policy), baked into the
voice track by tools/vo_edit.py (lines.py 'fx'; the mix must not add them again). Tasteful and intelligible: every
processed line is loudness-matched to the dry line (+ OFFSET) and must still pass the recogniser on its own
(tools/vo_asrcheck.py --every). Nothing is time-stretched: "slower" is only ever an effect (a late, lower double).
    whisper  the Blank's chat messages, the card, "I see you." and the sting (read whispered in her take): close and
             intimate (+2.5 dB proximity under 180 Hz, +1.5 dB air at 4.5 kHz), a faint cold digital sheen: a
             sample-held copy of the top (> 3.5 kHz, aliasing like a cheap screen speaker, -24 dB) and a 1.7 ms comb (-17 dB)
    car      her car line, as dry as the real Mom (the viewer must not hear a difference): a hint of the cabin (0.12 s,
             -26 dB) only
    double   2 a.m. and dinner: a subtle, too-smooth double: two WORLD copies (+9 cents at 14 ms, -12 dB; -7 cents at
             23 ms, -16 dB), the top smoothed (-1.5 dB from 7 kHz)
    tall     the cold open, midnight, the climax and her song: the tall form: a lower, detuned double (WORLD: -3 semitones,
             formants x0.90 = a longer throat, 20 ms late, -9 dB), a second copy +14 cents (9 ms, -14 dB), a touch of
             size (a 0.9 s room, 25 ms pre-delay, -17 dB) and body (+2 dB under 160 Hz)
    phone    Mom's "Baby? I'm at the table. Where are you?" on Owen's phone speaker: 320 Hz-3.6 kHz, a small speaker's
             1.9 kHz lift, light soft saturation, every word clear
"""
import numpy as np
from scipy import signal

SR = 48000
OFFSET = {'whisper': -1.0, 'car': 0.0, 'double': 0.0, 'tall': 0.5, 'phone': -1.0}
TAIL = {'whisper': 0.0, 'car': 0.08, 'double': 0.03, 'tall': 0.70, 'phone': 0.0}   # decay past the line (s)


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


FX = {'whisper': whisper, 'car': car, 'double': double, 'tall': tall, 'phone': phone}


def apply(y, fx):
    """The line in its place, loudness-matched to the dry line + OFFSET; same length plus TAIL."""
    f = FX.get(fx)
    if f is None: return y
    z = f(np.asarray(y, dtype=np.float64))
    z *= 10 ** ((speech_db(y) + OFFSET[fx] - speech_db(z)) / 20)
    n = int(0.004 * SR)
    z[-n:] *= np.linspace(1, 0, n)
    return z
