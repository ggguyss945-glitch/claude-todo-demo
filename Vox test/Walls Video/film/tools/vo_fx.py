"""Voice places for "If Your Little Brother Says Someone Lives In The Walls... DON'T LAUGH" (Night Policy), baked into
the voice track by tools/vo_edit.py (lines.py 'fx'; the mix must not add them again). Tasteful and intelligible: every
processed line is loudness-matched to the dry line (+ OFFSET) and must still pass the recogniser on its own
(tools/vo_asrcheck.py --every).
    ceiling  Mr. Pell's "Off." from inside the sealed attic, right above Sam's head: through the ceiling board (top rolled
             off from 2.6 kHz, the board's 300 Hz thump), the attic's small, dead air around it (0.35 s, -16 dB)
    wall     inside the wall by Sam's bed (the address song, the excuses): drywall in front (low-pass 2.2 kHz, a 180 Hz
             panel resonance, a little consonant leak from the top kept at -16 dB), the stud bay behind (a 40 ms
             boxy cavity, -13 dB)
    mask     in the room, through the rubber mask ("Hush-a-bye", "Shhh. Just the pipes."): subtle; the mask's cavity
             (a 1.2 ms comb, -12 dB), a soft 900 Hz box (+1.5 dB), the top a little dulled (-3.5 dB from 4 kHz)
    vent     through the floor vent's grille ("Hush-a-bye. That's my house."): a sheet-metal duct: band 220 Hz-5.5 kHz,
             three narrow duct modes (680, 1450, 2350 Hz), a short metallic flutter (3.1 ms, decaying in 90 ms, -9 dB)
    phone    the dispatcher on Mom's phone speaker: 320 Hz-3.6 kHz, a small speaker's 1.9 kHz lift, light soft
             saturation, every word clear
    outdoor  Mr. Pell unmasked at the curb: dry (the mix adds the night street)
"""
import numpy as np
from scipy import signal

SR = 48000
OFFSET = {'ceiling': -2.0, 'wall': -2.5, 'mask': -0.5, 'vent': -2.0, 'phone': -1.0, 'outdoor': 0.0}
TAIL = {'ceiling': 0.30, 'wall': 0.06, 'mask': 0.0, 'vent': 0.10, 'phone': 0.0, 'outdoor': 0.0}   # decay past the line (s)


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


def ceiling(y):
    pad = np.concatenate([y, np.zeros(int(TAIL['ceiling'] * SR))])
    z = signal.sosfilt(_sos('lowpass', 2600, 4), pad)
    z = peak(z, 300, 2.5, 1.0)
    z = mix_wet(z, signal.fftconvolve(z, room(0.4, 0.35, 3000, 11))[:len(z)], -16)
    return z


def wall(y):
    pad = np.concatenate([y, np.zeros(int(TAIL['wall'] * SR))])
    body = signal.sosfilt(_sos('lowpass', 2200, 4), pad)
    body = peak(body, 180, 3.0, 1.2)
    leak = signal.sosfilt(_sos('highpass', 2500, 2), pad)
    z = body + leak * 10 ** (-16 / 20)
    z = mix_wet(z, signal.fftconvolve(z, room(0.06, 0.04, 2500, 12))[:len(z)], -13)
    return z


def mask(y):
    d = int(0.0012 * SR)
    z = y.copy(); z[d:] += 10 ** (-12 / 20) * y[:-d]
    z = peak(z, 900, 1.5, 1.1)
    return shelf(z, 4000, -3.5, high=True)


def vent(y):
    pad = np.concatenate([y, np.zeros(int(TAIL['vent'] * SR))])
    z = signal.sosfilt(_sos('bandpass', [220, 5500], 2), pad)
    for f, g in ((680, 5.0), (1450, 4.0), (2350, 3.0)):
        z = peak(z, f, g, 9.0)
    n = int(0.09 * SR); ir = np.zeros(n); k = int(0.0031 * SR)
    for j in range(1, n // k):
        ir[j * k] = (0.72 ** j) * (1 if j % 2 else -1)
    fl = signal.fftconvolve(z, ir)[:len(z)]
    fl = peak(fl, 2350, 4.0, 6.0)
    return mix_wet(z, fl, -9)


def phone(y):
    z = signal.sosfilt(_sos('bandpass', [320, 3600], 4), y)
    z = peak(z, 1900, 2.0, 1.0)
    g = np.max(np.abs(z)) + 1e-12
    z = np.tanh(1.6 * z / g) / np.tanh(1.6) * g                     # a small speaker's soft drive
    return signal.sosfilt(_sos('bandpass', [300, 3800], 2), z)


FX = {'ceiling': ceiling, 'wall': wall, 'mask': mask, 'vent': vent, 'phone': phone, 'outdoor': None}


def apply(y, fx):
    """The line in its place, loudness-matched to the dry line + OFFSET; same length plus TAIL."""
    f = FX.get(fx)
    if f is None: return y
    z = f(np.asarray(y, dtype=np.float64))
    z *= 10 ** ((speech_db(y) + OFFSET[fx] - speech_db(z)) / 20)
    n = int(0.004 * SR)
    z[-n:] *= np.linspace(1, 0, n)
    return z
