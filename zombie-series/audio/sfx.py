# Synthesized sound effects. Every function returns float32 (N, 2) stereo at SR.
import numpy as np
from scipy.signal import butter, sosfilt, sosfiltfilt

SR = 48000
rng = np.random.default_rng(7)

def t_(dur): return np.arange(int(dur * SR)) / SR
def sos(kind, f, order=2):
    f = np.atleast_1d(f) / (SR / 2)
    return butter(order, f if len(f) > 1 else f[0], kind, output='sos')
def lp(x, f, o=2): return sosfilt(sos('low', f, o), x, axis=0)
def hp(x, f, o=2): return sosfilt(sos('high', f, o), x, axis=0)
def bp(x, lo, hi, o=2): return sosfilt(sos('band', [lo, hi], o), x, axis=0)
def white(n): return rng.standard_normal(n).astype(np.float32)
def pink(n):
    w = np.fft.rfft(white(n)); f = np.fft.rfftfreq(n, 1 / SR); f[0] = 1
    return np.fft.irfft(w / np.sqrt(f), n).astype(np.float32) / 30
def brown(n): x = np.cumsum(white(n)); x -= np.linspace(x[0], x[-1], n); return (x / (np.abs(x).max() + 1e-9)).astype(np.float32)
def norm(x, peak=0.9): return x / (np.abs(x).max() + 1e-9) * peak
def st(x, pan=0.0, width=0.0):
    """mono -> stereo, constant-power pan in [-1, 1]; width adds a decorrelated copy."""
    a = (pan + 1) * np.pi / 4
    L, R = np.cos(a) * x, np.sin(a) * x
    if width:
        d = int(0.011 * SR); y = np.concatenate([np.zeros(d), x[:-d]]) if len(x) > d else x
        L, R = L + width * y * 0.5, R - width * y * 0.5
    return np.stack([L, R], 1).astype(np.float32)
def fade(x, a=0.005, b=0.02):
    n = len(x); na, nb = min(int(a * SR), n // 2), min(int(b * SR), n // 2); e = np.ones(n)
    if na: e[:na] = np.linspace(0, 1, na)
    if nb: e[-nb:] = np.linspace(1, 0, nb)
    return x * (e[:, None] if x.ndim == 2 else e)

# ---------------- ambience ----------------
def fridge_hum(dur, level=1.0):
    t = t_(dur); x = np.zeros_like(t)
    for k, a in [(1, .5), (2, 1.0), (3, .35), (4, .25), (6, .12), (8, .06)]:
        x += a * np.sin(2 * np.pi * 59.7 * k * t + k)
    x *= 1 + 0.08 * np.sin(2 * np.pi * 0.23 * t)
    x = 0.35 * x / 2.3 + 0.6 * bp(pink(len(t)), 90, 500) * 3
    x += 0.05 * bp(white(len(t)), 2000, 6000) * (1 + 0.5 * np.sin(2 * np.pi * 7.1 * t))   # compressor rattle
    return st(lp(x, 1800) * level, 0, 0.6)

def room_tone(dur, level=1.0):
    return st(lp(pink(int(dur * SR)), 4000) * 0.6 * level, 0, 0.9)

def wind(dur, level=1.0):
    n = int(dur * SR); t = t_(dur)
    gust = 0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * t + 1) * np.sin(2 * np.pi * 0.07 * t)
    L = bp(brown(n), 80, 900) * gust; R = bp(brown(n), 80, 900) * gust[::-1]
    return np.stack([L, R], 1).astype(np.float32) * 0.5 * level

# ---------------- body ----------------
def breath(dur, kind='in', strength=1.0):
    n = int(dur * SR); x = white(n)
    x = bp(x, 350, 2600) if kind == 'in' else bp(x, 250, 1700)
    ph = np.linspace(0, np.pi, n); env = np.sin(ph) ** (1.6 if kind == 'in' else 2.4)
    if kind == 'shaky': env *= 1 + 0.45 * np.sin(2 * np.pi * 11 * t_(dur))
    x = x * env
    x += 0.25 * bp(white(n), 900, 1400) * env   # faint mouth resonance
    return st(norm(x, 0.5 * strength), 0, 0.15)

def heartbeat_at(level=1.0):
    def thump(f, d, a):
        t = t_(d); return a * np.sin(2 * np.pi * f * t * (1 - 0.25 * t / d)) * np.exp(-t / (d / 4))
    x = np.zeros(int(0.5 * SR))
    for sig, o in [(thump(52, 0.16, 1.0), 0), (0.4 * thump(85, 0.08, 1.0), 0), (thump(60, 0.12, 0.7), int(0.27 * SR))]:
        x[o:o + len(sig)] += sig
    return st(lp(x, 220) * level)

# ---------------- objects ----------------
def click(level=1.0, body_f=1300):
    t = t_(0.06); x = np.zeros_like(t)
    c = bp(white(len(t)), 2500, 9000) * np.exp(-t / 0.0015); x += c
    x += 0.6 * np.sin(2 * np.pi * body_f * t) * np.exp(-t / 0.012)
    o = int(0.014 * SR); x[o:] += 0.5 * c[:-o]
    return st(x * level)

def toggle_switch(level=1.0):
    a = click(1.0, 1100); b = click(0.7, 700)
    x = np.zeros((int(0.12 * SR), 2), np.float32); x[:len(a)] += a; o = int(0.035 * SR); x[o:o + len(b)] += b
    return x * level

def pa_pop(level=1.0):
    t = t_(0.25)
    x = np.sin(2 * np.pi * 70 * t) * np.exp(-t / 0.03) + 0.3 * bp(white(len(t)), 500, 4000) * np.exp(-t / 0.01)
    crackle = np.zeros_like(t); idx = rng.integers(0, len(t), 40); crackle[idx] = rng.uniform(-1, 1, 40)
    x += 0.6 * bp(crackle, 800, 5000)
    return st(x * level)

def chime(level=1.0):
    def bell(f, d):
        t = t_(d); y = np.zeros_like(t)
        for r, a, tau in [(1, 1, .9), (2.0, .5, .5), (2.76, .3, .35), (4.07, .18, .2), (5.4, .08, .12)]:
            y += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / tau)
        return y * (1 - np.exp(-t / 0.003))
    a, b = bell(659.3, 1.6), bell(523.3, 2.0)
    x = np.zeros(int(2.6 * SR)); x[:len(a)] += a; o = int(0.55 * SR); x[o:o + len(b)] += b
    return st(norm(x, 0.8) * level)

def footstep(level=1.0, soft=False):
    d = 0.14 if not soft else 0.22; t = t_(d)
    x = lp(white(len(t)), 1500 if not soft else 900) * np.exp(-t / (0.02 if not soft else 0.05))
    x += 0.8 * np.sin(2 * np.pi * 75 * t) * np.exp(-t / 0.025)
    if soft:  # dragging scuff
        x += 0.5 * bp(white(len(t)), 300, 1800) * np.sin(np.pi * t / d) ** 2
    return x * level

def crowd_steps(dur, rate0, rate1, walkers=14, level=1.0, muffle=900, seed=3):
    """many shuffling dead walking; rate in steps/s ramps rate0->rate1"""
    r = np.random.default_rng(seed); n = int(dur * SR); L = np.zeros(n); R = np.zeros(n)
    t = 0.0
    while t < dur:
        rate = rate0 + (rate1 - rate0) * t / dur
        if rate <= 0.05: t += 0.05; continue
        t += r.exponential(1 / rate)
        if t >= dur: break
        s = footstep(r.uniform(0.3, 1.0), soft=r.random() < 0.6)
        i = int(t * SR); m = min(len(s), n - i); p = r.uniform(-0.8, 0.8)
        L[i:i + m] += s[:m] * np.cos((p + 1) * np.pi / 4); R[i:i + m] += s[:m] * np.sin((p + 1) * np.pi / 4)
    x = np.stack([L, R], 1)
    return (lp(x, muffle) * level).astype(np.float32)

def groan(dur=1.4, f0=82, level=1.0, seed=1, vowel='uh'):
    r = np.random.default_rng(seed); t = t_(dur); n = len(t)
    f = f0 * (1 + 0.04 * np.sin(2 * np.pi * 3.1 * t + r.uniform(0, 6))) * np.linspace(1.05, 0.88, n)
    f *= 1 + 0.02 * lp(r.standard_normal(n), 30) * 8
    ph = np.cumsum(2 * np.pi * f / SR); src = (ph / np.pi) % 2 - 1           # sawtooth
    src = src * (1 + 0.3 * lp(r.standard_normal(n), 40) * 6) + 0.35 * white(n)
    F = {'uh': [(550, 90), (1000, 110), (2500, 200)], 'oh': [(450, 80), (800, 100), (2600, 200)], 'eh': [(600, 90), (1700, 130), (2600, 200)]}[vowel]
    y = sum(bp(src, fc - bw, fc + bw) * g for (fc, bw), g in zip(F, [1.0, 0.6, 0.25]))
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.7 * (1 - np.exp(-t / 0.08))
    y = np.tanh(2.2 * y / (np.abs(y).max() + 1e-9)) * env
    return st(lp(y, 3200) * level * 0.6, 0, 0.3)

def metal_rattle(dur=0.7, level=1.0, seed=5):
    r = np.random.default_rng(seed); n = int(dur * SR); x = np.zeros(n); t = 0
    while t < dur - 0.1:
        t += r.uniform(0.025, 0.07); i = int(t * SR); tt = t_(0.09)
        hit = sum(np.sin(2 * np.pi * f * tt + r.uniform(0, 6)) * np.exp(-tt / r.uniform(0.02, 0.05)) for f in r.uniform(280, 2200, 5))
        m = min(len(tt), n - i); x[i:i + m] += hit[:m] * r.uniform(0.3, 1.0)
    return st(lp(x, 4000) * level * 0.25, 0, 0.5)

def scrape(dur=1.0, level=1.0, seed=8):
    r = np.random.default_rng(seed); n = int(dur * SR); t = t_(dur)
    env = np.clip(lp(np.abs(r.standard_normal(n)), 6) * 9, 0, 1) * np.sin(np.pi * t / dur)
    x = bp(white(n), 1200, 5000) * env + 0.2 * np.sin(2 * np.pi * (1700 + 120 * np.sin(2 * np.pi * 5 * t)) * t) * env ** 2
    return st(x * level * 0.5, 0, 0.3)

def whoosh(dur=0.45, level=1.0, up=True):
    n = int(dur * SR); t = t_(dur); x = white(n); out = np.zeros(n); B = 32
    for k in range(B):
        a, b = k * n // B, (k + 1) * n // B; fr = (k + 0.5) / B; fc = 300 * (10 ** (fr if up else 1 - fr))
        out[a:b] = bp(x, fc * 0.6, min(fc * 1.6, 20000))[a:b]
    env = np.sin(np.pi * t / dur) ** 1.5
    return st(out * env * level * 0.8, 0, 0.8)

def tok(level=1.0, f=1050):
    t = t_(0.12)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.018) + 0.5 * np.sin(2 * np.pi * f * 1.62 * t) * np.exp(-t / 0.01)
    x += 0.4 * bp(white(len(t)), 2000, 8000) * np.exp(-t / 0.002)
    return st(x * level * 0.6)

def pencil_tick(level=1.0):
    t = t_(0.05); return st(bp(white(len(t)), 2500, 8000) * np.exp(-t / 0.004) * level * 0.5)

def slam(level=1.0):
    t = t_(0.6)
    x = np.sin(2 * np.pi * 55 * t * (1 - 0.3 * t)) * np.exp(-t / 0.12) + 0.6 * lp(white(len(t)), 1800) * np.exp(-t / 0.03)
    x += 0.35 * bp(white(len(t)), 1000, 6000) * np.exp(-t / 0.008)
    return st(x * level)

def boom(level=1.0, dur=3.0):
    t = t_(dur)
    f = 32 + 40 * np.exp(-t / 0.25); ph = np.cumsum(2 * np.pi * f / SR)
    x = np.sin(ph) * np.exp(-t / 0.9) + 0.5 * lp(white(len(t)), 300) * np.exp(-t / 0.15)
    x += 0.15 * lp(white(len(t)), 2500) * np.exp(-t / 0.02)
    return st(np.tanh(1.5 * x) * level, 0, 0.3)

def reverse_swell(dur=1.6, level=1.0):
    t = t_(dur); x = bp(white(len(t)), 300, 6000) * (t / dur) ** 3
    x += 0.4 * lp(white(len(t)), 600) * (t / dur) ** 4
    return st(x * level * 0.6, 0, 0.9)

def riser(dur=2.8, level=1.0):
    t = t_(dur); n = len(t); out = np.zeros(n); x = white(n); B = 40
    for k in range(B):
        a, b = k * n // B, (k + 1) * n // B; fc = 200 * 25 ** ((k + .5) / B)
        out[a:b] = bp(x, fc * 0.7, min(fc * 1.4, 20000))[a:b]
    tone = sum(np.sin(np.cumsum(2 * np.pi * (f0 * 2 ** (2 * t / dur)) / SR)) for f0 in (220, 223.5, 331))
    y = out * (t / dur) ** 2 + 0.12 * tone * (t / dur) ** 2.5
    return st(y * level * 0.7, 0, 0.8)

def alarm_bell(dur, level=1.0):
    """mechanical twin-bell alarm clock: hammer alternates two bells at ~20 Hz"""
    n = int(dur * SR); x = np.zeros(n); tt = t_(0.3)
    modes = lambda f: sum(a * np.sin(2 * np.pi * f * r * tt) * np.exp(-tt / d) for r, a, d in [(1, 1, .18), (2.32, .6, .1), (4.25, .35, .06), (6.63, .2, .04)])
    b1, b2 = modes(1180), modes(1410); k = 0; t = 0.0
    while t < dur:
        i = int(t * SR); b = b1 if k % 2 == 0 else b2; m = min(len(b), n - i)
        x[i:i + m] += b[:m] * (0.85 + 0.15 * rng.random()); t += 1 / 19.5; k += 1
    x += 0.15 * bp(white(n), 3000, 7000) * (np.arange(n) % int(SR / 19.5) < 200)   # hammer clack
    return st(norm(x, 0.7) * level)

def flicker_buzz(dur=0.14, level=1.0):
    t = t_(dur); x = np.sign(np.sin(2 * np.pi * 120 * t)) * 0.4 + 0.3 * bp(white(len(t)), 1500, 6000)
    return st(lp(x, 3000) * np.sin(np.pi * t / dur) * level * 0.4)
