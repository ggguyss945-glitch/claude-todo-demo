"""Sound effects for the police-officer "rules" video, synthesised in the house style of
Too Much Gold's sfx.py (numpy + scipy, nothing sampled). Wood and metal are modal resonances
excited by short force pulses, rooms are short synthetic impulse responses, radios and phones are
band-limited and a little overdriven, beds take any duration. Every function returns mono
float32 at SR with its peak below -1 dBFS.
    python3 sfx_horror.py <out_dir>      renders every effect to WAV plus index.json
"""
import json, os, sys
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
import numpy as np
from scipy import signal

SR = 48000

# ------------------------------------------------------------------ helpers ---
def t_(dur): return np.arange(int(round(dur * SR))) / SR
def zeros(dur): return np.zeros(int(round(dur * SR)))
def noise(dur, seed=0): return np.random.default_rng(seed).standard_normal(int(round(dur * SR)))
def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def _flt(x, f, kind, order): return signal.sosfilt(signal.butter(order, f, btype=kind, fs=SR, output='sos'), x)
def lp(x, f, order=2): return _flt(x, f, 'low', order)
def hp(x, f, order=2): return _flt(x, f, 'high', order)
def bp(x, lo, hi, order=2): return _flt(x, [lo, hi], 'band', order)
def unit(x): return x / (np.std(x) + 1e-12)
def norm(x, pk=0.7): return (np.asarray(x) * (pk / (np.max(np.abs(x)) + 1e-12))).astype(np.float32)

def reson(x, f, q=8.0, g=1.0):
    """add a resonant peak at f: a plastic shell, a speaker box, a formant"""
    b, a = signal.iirpeak(f, q, fs=SR); return x + g * signal.lfilter(b, a, x)

def fade(x, fi=0.002, fo=0.02):
    x = np.array(x, float); n = len(x); a, b = min(n, int(fi * SR)), min(n, int(fo * SR))
    if a: x[:a] *= np.linspace(0, 1, a)
    if b: x[n - b:] *= np.linspace(1, 0, b)
    return x

def place(out, x, t, g=1.0):
    i = int(round(t * SR)); j = min(len(out), i + len(x))
    if j > i: out[i:j] += g * np.asarray(x)[: j - i]
    return out

def fin(x, pk=0.7, fo=0.03, fi=0.0005, trim=True):
    """finish a sound: no DC, trailing silence trimmed (one-shots only), clean ends, peak at pk"""
    x = hp(x, 18)
    if trim:
        loud = np.nonzero(np.abs(x) > np.max(np.abs(x)) * 10 ** (-66 / 20))[0]
        if len(loud): x = x[: min(len(x), loud[-1] + int(0.05 * SR))]
    return norm(fade(x, fi, fo), pk)

def slow(dur, rate=0.1, seed=0):
    """a smooth random wander between 0 and 1 that changes at about `rate` Hz"""
    m = int(dur * 50) + 16
    v = signal.sosfiltfilt(signal.butter(2, min(rate, 20), fs=50, output='sos'), np.random.default_rng(seed).standard_normal(m))
    return np.interp(t_(dur), np.arange(m) / 50, (v - v.min()) / (np.ptp(v) + 1e-12))

_TABLES = {}
def wavetable(nh):
    """one cycle of a sawtooth with nh harmonics (4096 points, cached)"""
    if nh not in _TABLES:
        k = np.arange(1, nh + 1)
        _TABLES[nh] = (np.sin(2 * np.pi * np.outer(np.arange(4096) / 4096, k)) / k).sum(1) * 0.55
    return _TABLES[nh]

def saw(f, dur, seed=0, fmax=5000):
    """band-limited sawtooth; f is a frequency or a per-sample frequency array"""
    n = int(round(dur * SR)); f = np.broadcast_to(np.asarray(f, float), (n,))
    tab = wavetable(int(np.clip(fmax / max(f.max(), 1.0), 1, 256)))
    ph = (np.random.default_rng(seed).random() + np.cumsum(f) / SR) % 1.0
    return tab[(ph * 4096).astype(np.int64) & 4095]

def sweep(x, fc, kind='band', bw=0.5, blk=256):
    """filter with a moving cutoff ('low') or centre ('band') that follows the per-sample array fc"""
    y = np.empty(len(x)); zi = None
    for i in range(0, len(x), blk):
        c = float(fc[i])
        f = [max(25.0, c / (1 + bw)), min(SR / 2 - 200, c * (1 + bw))] if kind == 'band' else min(SR / 2 - 200, c)
        sos = signal.butter(2, f, btype=kind, fs=SR, output='sos')
        if zi is None: zi = np.zeros((len(sos), 2))
        y[i:i + blk], zi = signal.sosfilt(sos, x[i:i + blk], zi=zi)
    return y

def modes(spec, dur=0.5, seed=0, jit=0.01):
    """impulse response of a struck object: decaying sines from (freq Hz, decay 1/s, gain)"""
    r = np.random.default_rng(seed); tt = t_(dur); y = np.zeros(len(tt))
    for f, d, g in spec:
        f *= 1 + jit * r.standard_normal()
        if f < SR / 2 - 2000: y += g * np.exp(-d * tt) * np.sin(2 * np.pi * f * tt)
    return y

def force(width, seed=0, grit=0.2, dur=0.02):
    """the blow itself: a half-sine force pulse (wider = softer and darker) plus contact noise"""
    tt = t_(dur); x = np.where(tt < width, np.sin(np.pi * np.minimum(tt / width, 1)), 0.0)
    return x + grit * hp(noise(dur, seed), 2500) * np.exp(-tt / (0.3 * width + 0.0002))

def strike(spec, width, seed=0, grit=0.2, dur=0.5, jit=0.01):
    """a struck object: force pulse convolved with the object's modes"""
    return signal.fftconvolve(force(width, seed, grit), modes(spec, dur, seed + 1, jit))

def room_ir(rt60=0.5, damp=4000, seed=0, size=1.0):
    """synthetic room impulse response (unit energy): a few early reflections, then a noise tail
    whose highs die out faster than its lows"""
    r = np.random.default_rng(seed); n = int(rt60 * 1.2 * SR) + 1; tt = np.arange(n) / SR
    tail = lp(r.standard_normal(n), 1500) * np.exp(-6.9 * tt / rt60) + 0.5 * hp(r.standard_normal(n), 1500) * np.exp(-13.8 * tt / rt60)
    tail *= np.minimum(1, tt / (0.015 * size))
    s = np.std(tail[: int(0.05 * SR)])
    for _ in range(7):
        i = int((0.002 + 0.03 * r.random()) * size * SR)
        if i < n: tail[i] += r.choice((-1, 1)) * (2 + 4 * r.random()) * s
    tail = lp(tail, damp)
    return tail / np.sqrt(np.sum(tail ** 2))

def room(x, rt60=0.5, wet=0.3, damp=4000, seed=0, size=1.0):
    """x plus its reverb in a synthetic room (the output is longer by the tail)"""
    ir = room_ir(rt60, damp, seed, size); y = np.zeros(len(x) + len(ir) - 1)
    y[: len(x)] = x
    return y + wet * signal.oaconvolve(x, ir)

def outside(x, dist=2.0, seed=0):
    """move a sound out onto the street: distance dulls it, the houses across the road throw back
    slap echoes, and a thin open-air tail follows"""
    x = lp(x, 14000 / dist); y = np.zeros(len(x) + int(0.4 * SR)); y[: len(x)] = x
    for d, g in [(0.052, 0.3), (0.13, 0.2), (0.24, 0.12)]: place(y, lp(x, 2000), d, g * min(1.0, 0.5 * dist))
    return room(y, 1.1, 0.35 * min(1.5, dist ** 0.5), 2500, seed, size=3)

def radio_speaker(x, drive=2.0):
    """a shoulder-mic speaker: narrow band, a boxy plastic resonance, gentle overdrive"""
    x = reson(reson(bp(x, 400, 3200, 3), 1800, 3, 1.2), 950, 2.5, 0.5)
    return np.tanh(drive * x / (4 * np.std(x) + 1e-12))

def phone_line(x, hiss=0.004, seed=0):
    """a telephone earpiece: 300-3400 Hz, a little codec grit, a whisper of line hiss"""
    y = bp(x, 300, 3400, 3); y = np.tanh(1.5 * y / (np.max(np.abs(y)) + 1e-12))
    return y + hiss * unit(bp(noise(len(y) / SR, seed), 300, 3400))

def _creak(dur, f0, f1, res, seed=0):
    """stick-slip friction (a floorboard, a dry hinge): a ragged pulse train ringing the material"""
    tt = t_(dur); r = np.random.default_rng(seed)
    f = np.linspace(f0, f1, len(tt)) * (1 + 0.15 * (slow(dur, 10, seed) - 0.5))
    cnt = np.cumsum(f) / SR; i = np.nonzero(np.diff(np.floor(cnt)))[0] + 1
    imp = np.zeros(len(tt)); imp[i] = 0.4 + r.random(len(i))
    return signal.oaconvolve(imp, modes(res, 0.08, seed))[: len(tt)] * np.sin(np.pi * tt / dur) ** 0.6

def _clink(seed, f0):
    """one small key or curtain ring touching another"""
    d = 30 + 25 * np.random.default_rng(seed).random()
    return norm(strike([(f0, d, 1.0), (f0 * 2.32, d * 1.5, 0.6), (f0 * 4.05, d * 2.2, 0.4), (f0 * 6.2, d * 3, 0.25)], 0.0003, seed, 0.3, 0.35), 1.0)

def _thump(f0=46.0, dur=0.4, decay=14.0, seed=0):
    """a soft, deep body thump with a falling pitch (heartbeats, pulses)"""
    tt = t_(dur); f = f0 * (1 + 0.7 * np.exp(-tt * 35))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * decay) * (1 - np.exp(-tt * 350)) + 0.025 * unit(lp(noise(dur, seed), 120)) * np.exp(-tt * 40)

def _boom(dur=5.0, f_end=36.71, seed=0):
    """dry sub boom: a sine dropping an octave onto f_end, a noisy body, a long low rumble"""
    tt = t_(dur); f = f_end * (1 + np.exp(-tt * 5))
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 1.3) * (1 - np.exp(-tt * 250))
    body = norm(lp(noise(dur, seed), 250) * np.exp(-tt * 9), 0.5) + 0.3 * np.sin(2 * np.pi * 2 * np.cumsum(f) / SR) * np.exp(-tt * 6)
    rumble = norm(lp(noise(dur, seed + 1), 70) * np.exp(-tt * 1.1) * (1 - np.exp(-tt * 8)), 0.3)
    return sub + body + rumble

WOOD_DOOR = [(78, 45, 0.2), (124, 42, 0.35), (171, 40, 0.5), (236, 40, 0.7), (318, 44, 0.8), (455, 48, 0.85), (610, 54, 0.9),
             (840, 64, 0.85), (1130, 80, 0.7), (1570, 100, 0.55), (2240, 140, 0.35), (3100, 190, 0.22), (4300, 260, 0.1)]
GLASS = [(265, 60, 0.1), (420, 60, 0.2), (690, 55, 0.35), (1180, 55, 0.6), (1930, 65, 0.7), (2870, 80, 0.6), (4120, 100, 0.45), (5650, 130, 0.3), (7600, 170, 0.15)]
METAL_SMALL = [(1900, 220, 0.3), (3100, 260, 0.5), (4700, 320, 0.4), (6900, 420, 0.3)]
BOLT = [(780, 55, 0.6), (1520, 65, 0.5), (2650, 80, 0.45), (3900, 110, 0.3), (5400, 150, 0.2)]
BRASS = [(300, 45, 0.25), (920, 40, 0.7), (2240, 50, 0.5), (3650, 70, 0.35), (5300, 90, 0.2)]
PLASTIC = [(1250, 260, 0.3), (2600, 350, 0.5), (4300, 450, 0.4), (6800, 600, 0.3)]
CAR_BODY = [(62, 30, 0.4), (98, 30, 0.6), (147, 32, 0.7), (215, 36, 0.7), (330, 42, 0.6), (520, 55, 0.45), (900, 75, 0.3), (1500, 100, 0.15)]
LATCH = [(380, 40, 0.4), (1250, 45, 0.6), (2700, 60, 0.5), (4100, 80, 0.35)]

# -------------------------------------------------------------- the door ---
def knock_door(variant='heavy', seed=0):
    """Three knocks on a solid wooden front door, heard from the hallway inside; 'heavy' is a flat
    fist with the door shifting in its frame, 'polite' is knuckles."""
    heavy = variant == 'heavy'; r = np.random.default_rng(seed)
    gap = 0.34 if heavy else 0.23; out = zeros(3 * gap + 1.2)
    for k in range(3):
        w = (0.0012 if heavy else 0.0005) * (1 + 0.12 * r.standard_normal())
        hit = norm(strike(WOOD_DOOR, w, seed * 10 + k, 0.3, 0.7, 0.015), 1.0)
        tt = t_(0.008); hit[: len(tt)] += norm(bp(noise(0.008, seed + 70 + k), 700, 5000) * np.exp(-tt / 0.001), 0.7 if heavy else 1.0)
        t = 0.01 + k * gap + 0.012 * r.standard_normal() * (k > 0)
        place(out, hit, t, ((1.0, 0.9, 1.1) if heavy else (1.0, 0.85, 0.75))[k] * (0.94 + 0.12 * r.random()))
        if heavy:
            tt = t_(0.1); rattle = bp(noise(0.1, seed + 50 + k), 900, 4000) * np.exp(-tt * 50) * (np.sin(2 * np.pi * 75 * tt) > 0.2)
            place(out, unit(rattle), t + 0.004, 0.05)
    low = signal.oaconvolve(lp(out, 220), modes([(57, 8, 1.0), (94, 11, 0.6), (141, 15, 0.4)], 1.0, seed))[: len(out)]
    out += norm(low, (0.06 if heavy else 0.03) * np.max(np.abs(out)))       # the hallway booms along a little
    return fin(room(out, 0.6, 0.5, 3500, seed), 0.85 if heavy else 0.55, 0.3)

def tap_glass(taps=3, seed=1):
    """Knuckle taps on a window pane: a hard little tick and a short glassy ring."""
    r = np.random.default_rng(seed); out = zeros(taps * 0.3 + 0.6)
    for k in range(taps):
        hit = norm(strike(GLASS, 0.0004, seed * 10 + k, 0.6, 0.5, 0.02), 1.0)
        place(out, hit, 0.01 + k * 0.29 + 0.01 * r.random(), (1.0, 0.9, 0.8)[k % 3])
    return fin(room(out, 0.45, 0.35, 5000, seed), 0.55, 0.2)

def key_in_lock(seed=12):
    """A key finding the lock: the ring jostles, the tip scrapes the plate, slides in over the
    pins click by click, and seats."""
    r = np.random.default_rng(seed); out = zeros(1.3)
    place(out, _clink(seed, 3400), 0.02, 0.3); place(out, _clink(seed + 1, 2700), 0.07, 0.2)
    tt = t_(0.18); place(out, norm(bp(noise(0.18, seed + 2), 2500, 9000) * np.sin(np.pi * tt / 0.18) * (0.5 + 0.5 * slow(0.18, 15, seed)), 1.0), 0.12, 0.25)
    tt = t_(0.45); place(out, norm(bp(noise(0.45, seed + 3), 3000, 9000) * np.sin(np.pi * tt / 0.45) ** 0.5, 1.0), 0.32, 0.12)
    for k, t in enumerate([0.34, 0.41, 0.47, 0.55, 0.62]):
        spec = [(f * (0.9 + 0.2 * r.random()), d, a) for f, d, a in METAL_SMALL]
        place(out, norm(strike(spec, 0.0003, seed * 10 + k, 0.7, 0.06), 1.0), t, 0.45 + 0.1 * k)
    place(out, norm(strike([(f * 0.7, d, a) for f, d, a in METAL_SMALL], 0.0006, seed + 9, 0.5, 0.12), 1.0), 0.75, 0.9)
    return fin(room(out, 0.35, 0.3, 6000, seed), 0.5, 0.2)

def lock_turn(seed=13):
    """A deadbolt thrown: gritty turn of the cylinder, the cam catching, the heavy bolt clacking
    home with the door's wood behind it."""
    out = zeros(1.0); tt = t_(0.2)
    place(out, norm(bp(noise(0.2, seed), 1500, 6000) * np.sin(np.pi * tt / 0.2) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 45 * tt))), 1.0), 0.02, 0.25)
    place(out, norm(strike(METAL_SMALL, 0.0004, seed + 1, 0.5, 0.1), 1.0), 0.17, 0.35)
    place(out, norm(strike(BOLT, 0.0012, seed + 2, 0.35, 0.5), 1.0), 0.24, 1.0)
    place(out, norm(strike(WOOD_DOOR[:6], 0.003, seed + 3, 0.1, 0.5), 1.0), 0.242, 0.6)
    return fin(room(out, 0.5, 0.45, 4500, seed), 0.7, 0.2)

def keys_jingle(seed=14):
    """A ring of keys lifted and shaken: clusters of little inharmonic clinks."""
    r = np.random.default_rng(seed); out = zeros(1.5)
    for s, t0 in enumerate([0.03, 0.42, 0.8]):
        for j in range(7 + int(r.integers(0, 5))):
            place(out, _clink(seed * 100 + s * 20 + j, 2200 + 2600 * r.random()), t0 + 0.16 * r.random() ** 1.5, 0.3 + 0.7 * r.random())
    return fin(room(out, 0.35, 0.3, 7000, seed), 0.45, 0.2)

def mail_slot(seed=15):
    """Something pushed through the brass mail slot: the sprung flap creaks open, a sheet slides
    through and drops to the floor, the flap snaps shut and its spring sings."""
    out = zeros(2.9)
    place(out, norm(strike(BRASS, 0.0008, seed, 0.4, 0.3), 1.0), 0.02, 0.3)
    place(out, norm(_creak(0.4, 520, 760, [(1450, 90, 0.6), (2600, 120, 0.5), (3900, 160, 0.3)], seed), 1.0), 0.05, 0.4)
    tt = t_(1.3)
    place(out, norm(bp(noise(1.3, seed + 1), 900, 7000) * np.sin(np.pi * tt / 1.3) ** 0.7 * (0.6 + 0.4 * slow(1.3, 14, seed + 2)), 1.0), 0.3, 0.45)
    tt = t_(0.3)
    place(out, norm(lp(noise(0.3, seed + 4), 900) * np.exp(-tt * 30) + 0.025 * unit(bp(noise(0.3, seed + 5), 600, 4000)) * np.exp(-tt * 60), 1.0), 1.72, 0.35)
    place(out, norm(strike(BRASS, 0.0012, seed + 6, 0.3, 0.7), 1.0), 1.6, 1.0)
    tt = t_(0.6); place(out, np.sin(2 * np.pi * 1900 * tt * (1 + 0.01 * np.sin(2 * np.pi * 23 * tt))) * np.exp(-tt * 9), 1.605, 0.06)
    return fin(room(out, 0.55, 0.6, 4000, seed), 0.65, 0.3)

def paper_rustle(dur=1.1, seed=16):
    """A sheet of paper handled and unfolded: a soft swish under dry crinkles."""
    tt = t_(dur); r = np.random.default_rng(seed)
    env = slow(dur, 4, seed) ** 1.5 * np.sin(np.pi * tt / dur) ** 0.5
    swish = norm(bp(noise(dur, seed), 700, 7000) * env, 0.5)
    m = int(dur * 600); idx = r.integers(0, len(tt), m); idx = idx[r.random(m) < env[idx]]
    cr = np.zeros(len(tt)); cr[idx] = r.standard_normal(len(idx))
    return fin(room(swish + norm(bp(cr, 2000, 10000), 1.0), 0.3, 0.2, 7000, seed), 0.45, 0.1)

def pen_click(seed=17):
    """A ballpoint pen clicked: two snappy plastic transients, press and release."""
    out = zeros(0.3)
    for k, (t0, g, s) in enumerate([(0.01, 1.0, 1.0), (0.016, 0.45, 1.3), (0.15, 0.7, 1.1), (0.155, 0.3, 1.4)]):
        place(out, norm(strike([(f * s, d, a) for f, d, a in PLASTIC], 0.00015, seed * 10 + k, 0.8, 0.06), 1.0), t0, g)
    return fin(room(out, 0.25, 0.15, 8000, seed), 0.45, 0.05)

def curtain_rings(seed=23, dur=1.4):
    """Curtains pulled along a metal rod: rings grinding and chattering, bunching up at the end."""
    tt = t_(dur); r = np.random.default_rng(seed)
    speed = np.sin(np.pi * np.clip((tt - 0.05) / 1.0, 0, 1)) ** 1.2
    cnt = np.cumsum(35 + 60 * speed) / SR; i = np.nonzero(np.diff(np.floor(cnt)))[0] + 1
    imp = np.zeros(len(tt)); imp[i] = speed[i] * (0.3 + r.random(len(i)))
    chatter = signal.oaconvolve(imp, modes([(2650, 180, 0.6), (4100, 220, 0.5), (5900, 300, 0.3), (1500, 150, 0.2)], 0.06, seed))[: len(tt)]
    x = norm(chatter, 0.6) + norm(bp(noise(dur, seed + 1), 1800, 7000) * speed, 0.2) + norm(bp(noise(dur, seed + 2), 300, 2500) * speed, 0.3)
    for k in range(4): place(x, _clink(seed + 10 + k, 2300 + 1100 * r.random()), 1.02 + 0.05 * k + 0.02 * r.random(), 0.35 - 0.06 * k)
    return fin(room(x, 0.4, 0.35, 6000, seed), 0.45, 0.2)

def tv_off(seed=22):
    """A television switched off in the next room: relay tick, a crackle of collapsing static,
    a soft speaker thump and a faint falling whine."""
    out = zeros(1.0); r = np.random.default_rng(seed)
    place(out, norm(strike([(700, 200, 0.3), (1700, 300, 0.5), (2900, 350, 0.4), (4600, 450, 0.3)], 0.0003, seed, 0.6, 0.05), 1.0), 0.02, 0.6)
    tt = t_(0.25); st = hp(noise(0.25, seed + 1), 1500) * np.exp(-tt * 14) * (r.random(len(tt)) < 0.15)
    place(out, norm(st, 1.0), 0.022, 0.4)
    tt = t_(0.4); place(out, np.sin(2 * np.pi * 70 * tt) * np.exp(-tt * 18) * (1 - np.exp(-tt * 300)), 0.025, 0.2)
    tt = t_(0.5); place(out, np.sin(2 * np.pi * np.cumsum(3800 + 5500 * np.exp(-tt * 9)) / SR) * np.exp(-tt * 7), 0.025, 0.05)
    return fin(room(out, 0.5, 0.5, 4500, seed), 0.45, 0.2)

def slippers_floor(steps=6, seed=11):
    """Soft slippers shuffling across a wooden floor inside, one board giving a small creak."""
    r = np.random.default_rng(seed); gap = 0.62; out = zeros(steps * gap + 1.0); tt = t_(0.35)
    for k in range(steps):
        e = np.sin(np.pi * np.minimum(tt / 0.3, 1)) ** 2 * np.exp(-tt * 4)
        shuffle = norm(bp(noise(0.35, seed * 40 + k), 300, 2600) * e * (0.7 + 0.3 * np.sin(2 * np.pi * 31 * tt) ** 2), 1.0)
        pat = norm(lp(noise(0.35, seed * 40 + k + 20), 140) * np.exp(-tt * 35), 0.5)
        place(out, shuffle + pat, 0.02 + k * gap + 0.03 * r.random(), 0.8 + 0.3 * r.random())
    place(out, norm(_creak(0.38, 120, 70, [(380, 60, 1.0), (720, 80, 0.7), (1150, 110, 0.5), (1900, 150, 0.3)], seed), 1.0), 0.1 + 3 * gap, 0.3)
    return fin(room(out, 0.4, 0.4, 4000, seed), 0.4, 0.2)

def _shoe(seed=0, hard=1.0):
    """one hard-soled step: heel thump and click, a gritty scuff, the sole slapping down"""
    tt = t_(0.25); r = np.random.default_rng(seed)
    heel = norm(lp(noise(0.25, seed), 240) * np.exp(-tt * 55), 0.6) + norm(bp(noise(0.25, seed + 1), 1800, 7000) * np.exp(-tt * 420), 1.0 * hard)
    grit = norm(bp(noise(0.25, seed + 2), 2500, 9000) * np.exp(-tt * 30), 0.08 * (0.5 + r.random()))
    toe = place(np.zeros(len(tt)), norm(bp(noise(0.12, seed + 3), 600, 4000) * np.exp(-t_(0.12) * 110), 0.45), 0.07 + 0.02 * r.random())
    return heel + grit + toe

def footsteps_path(steps=9, seed=10):
    """Hard shoes on the concrete path outside, walking up from the street to the porch."""
    r = np.random.default_rng(seed); gap = 0.57; out = zeros(steps * gap + 1.6)
    for k in range(steps):
        u = k / max(1, steps - 1); d = 10 - 8.5 * u                     # metres from the door
        s = room(lp(_shoe(seed * 50 + k, 0.8 + 0.4 * (k % 2)), 2500 + 8000 * u), 0.9, 0.25 + 0.5 * (1 - u), 2500, seed + k, 2)
        place(out, s, 0.02 + k * gap + 0.02 * r.standard_normal() * (k > 0), (1.5 / d) ** 0.8)
    return fin(out, 0.6, 0.3)

# ---------------------------------------------------------- the patrol car ---
def radio_crackle(seed=2, dur=0.9):
    """Shoulder-radio squelch burst: key-up pop, a rush of band-limited static with crackle and a
    buried unintelligible voice, then the squelch tail snapping shut."""
    r = np.random.default_rng(seed); tt = t_(dur); n = len(tt)
    hiss = unit(noise(dur, seed)) * (0.55 + 0.45 * slow(dur, 18, seed + 1))
    crack = np.zeros(n); i = r.integers(0, n, int(dur * 90)); crack[i] = r.standard_normal(len(i))
    f0 = 150 + 25 * np.sin(2 * np.pi * 3.1 * tt) + 15 * slow(dur, 6, seed + 2); src = saw(f0, dur, seed)
    voice = unit(bp(src, 500, 900) + 0.6 * bp(src, 1300, 2100)) * (np.sin(2 * np.pi * 4.6 * tt + 1) > -0.1)
    e_end = 0.65 * dur
    env = np.minimum(1, tt / 0.003) * np.where(tt < e_end, 0.75, 1.3 * np.exp(-(tt - e_end) * 18)) * (tt < e_end + 0.16)
    x = (0.5 * hiss + 0.35 * voice * (tt < e_end) + norm(hp(crack, 800), 3.0)) * env
    x[: int(0.004 * SR)] += np.linspace(2, 0, int(0.004 * SR))                # the key-up pop
    return fin(radio_speaker(x, 3.0), 0.6, 0.005)

def radio_static_bed(dur=20.0, seed=3):
    """Low radio static left open: band-limited hiss that drifts, sparse crackle, a faint whistle."""
    tt = t_(dur); r = np.random.default_rng(seed); n = len(tt)
    x = unit(noise(dur, seed)) * (0.7 + 0.3 * slow(dur, 0.4, seed + 1))
    m = int(dur * 3); c = np.zeros(n); c[r.integers(0, n, m)] = r.standard_normal(m) * 25
    x += hp(c, 1000) + 0.08 * np.sin(2 * np.pi * np.cumsum(1320 + 15 * np.sin(2 * np.pi * 0.07 * tt)) / SR)
    return fin(radio_speaker(x, 1.5), 0.3, 0.3, 0.3, trim=False)

def radio_click(seed=4):
    """A tiny relay click: contact snap, one bounce, a whisper of metal ring."""
    out = zeros(0.1)
    for k, (dt, a) in enumerate([(0.004, 1.0), (0.0075, 0.45)]):
        place(out, norm(strike([(650, 250, 0.3), (2900, 400, 0.6), (4700, 500, 0.4), (7100, 700, 0.3)], 0.0002, seed + k, 0.8, 0.05), 1.0), dt, a)
    return fin(out, 0.5, 0.02)

def radio_beep(seed=5):
    """Push-to-talk chirp from the radio: two quick rising tones through the little speaker."""
    out = zeros(0.25)
    for t0, f, d in [(0.01, 1050, 0.05), (0.075, 1580, 0.07)]:
        tt = t_(d); place(out, fade(np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(2 * np.pi * 3 * f * tt), 0.003, 0.004), t0)
    tt = t_(0.25); out += 0.03 * unit(noise(0.25, seed)) * (tt > 0.145) * np.exp(-(tt - 0.145).clip(0) * 40)
    return fin(radio_speaker(out, 1.6), 0.45, 0.01)

def car_door_open(seed=6, dist=2.0):
    """A car door opening at the curb: handle flick, the latch letting go, the check strap clunking."""
    out = zeros(1.0); tt = t_(0.12)
    place(out, norm(strike([(1900, 180, 0.5), (3300, 220, 0.4), (5200, 300, 0.2)], 0.0005, seed, 0.6, 0.1), 1.0), 0.02, 0.4)
    place(out, norm(strike(LATCH, 0.0012, seed + 1, 0.4, 0.4), 1.0), 0.09, 1.0)
    place(out, norm(lp(noise(0.12, seed + 2), 1200) * np.sin(np.pi * tt / 0.12), 1.0), 0.1, 0.15)
    for k, (t, g) in enumerate([(0.45, 0.6), (0.62, 0.4)]):
        place(out, norm(strike(CAR_BODY[1:], 0.004, seed + 3 + k, 0.1, 0.4), 1.0), t, g)
    return fin(outside(out, dist, seed), 0.55, 0.3)

def car_door_close(seed=7, dist=2.5):
    """A car door shut out on the street: a deep body thunk with the latch in it, and a slap echo
    off the houses across the road."""
    out = zeros(1.0); tt = t_(0.06)
    place(out, norm(strike(CAR_BODY, 0.0035, seed, 0.15, 0.8), 1.0), 0.01, 1.0)
    place(out, norm(strike(LATCH, 0.001, seed + 1, 0.4, 0.3), 1.0), 0.016, 0.6)
    place(out, norm(lp(noise(0.06, seed + 2), 600) * np.exp(-tt * 60), 1.0), 0.008, 0.2)
    return fin(outside(out, dist, seed), 0.7, 0.4)

def _engine(rpm, seed=0):
    """a V8 from a per-sample rpm curve: exhaust pulses at the firing rate with the lumpy
    uneven-bank pattern, through a muffler, plus some mechanical noise"""
    n = len(rpm); r = np.random.default_rng(seed)
    cnt = np.cumsum(rpm / 60 * 4) / SR                      # four firings per revolution
    i = np.nonzero(np.diff(np.floor(cnt)))[0] + 1
    imp = np.zeros(n); imp[i] = (0.6 + 0.8 * r.random(8))[np.floor(cnt[i]).astype(int) % 8] * (1 + 0.15 * r.standard_normal(len(i)))
    puff = modes([(48, 45, 0.5), (96, 45, 0.8), (150, 55, 0.75), (230, 70, 0.6), (380, 95, 0.4), (620, 140, 0.2)], 0.12, seed)
    body = signal.oaconvolve(imp, puff)[:n] + 0.15 * signal.oaconvolve(imp, hp(noise(0.03, seed), 300) * np.exp(-t_(0.03) * 120))[:n]
    mech = unit(bp(noise(n / SR, seed + 3), 900, 3500)) * (0.5 + 0.5 * norm(lp(np.abs(imp), 40), 1.0))
    return unit(hp(body, 35)) + 0.06 * mech

def car_engine_idle_bed(dur=20.0, seed=8, dist=3.0):
    """A patrol car idling at the curb, heard from the house: lumpy V8 burble, a little fan whir."""
    tt = t_(dur)
    rpm = 680 + 30 * (slow(dur, 0.3, seed) - 0.5) + 8 * np.sin(2 * np.pi * 0.9 * tt)
    x = lp(_engine(rpm, seed), 1200) + 0.03 * unit(bp(noise(dur, seed + 1), 300, 1500))
    return fin(outside(x, dist, seed)[: len(tt)], 0.4, 0.5, 0.5, trim=False)

def car_drive_away(seed=9, dur=8.0):
    """The patrol car pulling away: clunk into gear, revs climbing through a shift, tyres hissing
    on asphalt, everything dulling and thinning as it goes down the street."""
    tt = t_(dur)
    rpm = 680 + lp(np.interp(tt, [0, 0.7, 1.0, 3.0, 3.25, 3.6, 6.0, dur], [0, 0, 220, 1620, 820, 870, 1420, 1320]), 4)
    load = np.interp(tt, [0, 0.8, 1.0, 3.1, 3.25, 3.5, 6.0, dur], [0.2, 0.2, 1, 1, 0.3, 1, 0.7, 0.5])
    v = np.interp(tt, [0, 1.0, 3.2, 6.0, dur], [0, 0, 7, 13, 14])
    d = np.sqrt(12 ** 2 + (np.cumsum(v) / SR) ** 2)          # starts 12 m from the house
    x = _engine(rpm, seed) * (0.6 + 0.6 * load) + 0.8 * unit(bp(noise(dur, seed + 1), 200, 2500)) * (v / 14) ** 1.5
    place(x, 2 * unit(strike(CAR_BODY[2:], 0.005, seed + 2, 0.1, 0.3)), 0.75, 1.0)
    x = sweep(x, 3500 * (12 / d) ** 1.2, 'low') * (12 / d)
    return fin(outside(x, 3.0, seed)[: len(tt)], 0.6, 1.5, 0.05, trim=False)

def camera_beep(state='on', seed=26):
    """Body-worn camera: a rubbery button press and a two-note piezo chirp, rising for 'on' and
    falling for 'off'."""
    out = zeros(0.35); tt = t_(0.075)
    place(out, norm(strike(PLASTIC, 0.0004, seed, 0.4, 0.05), 1.0), 0.01, 0.35)
    for k, f in enumerate((2700, 3600) if state == 'on' else (3600, 2700)):
        tone = sum(np.sin(2 * np.pi * f * h * tt) / h for h in (1, 3, 5) if f * h < 20000)
        place(out, reson(fade(tone, 0.002, 0.004), f, 6, 0.5), 0.06 + 0.11 * k, 0.5)
    return fin(out, 0.4, 0.01)

# ------------------------------------------------------------- the phone ---
def _cadence(dur, on, off, start=0.0):
    tt = t_(dur); return lp((((tt - start) % (on + off)) < on) * (tt >= start) * 1.0, 150)

def phone_busy_tone(dur=6.0, seed=18):
    """US busy signal in the earpiece: 480 + 620 Hz, half a second on, half a second off."""
    tt = t_(dur)
    return fin(phone_line((np.sin(2 * np.pi * 480 * tt) + np.sin(2 * np.pi * 620 * tt)) * _cadence(dur, 0.5, 0.5), 0.01, seed), 0.4, 0.01, trim=False)

def phone_ring_out(dur=12.0, seed=19):
    """US ringback while a call rings out: 440 + 480 Hz, two seconds on, four off."""
    tt = t_(dur)
    return fin(phone_line((np.sin(2 * np.pi * 440 * tt) + np.sin(2 * np.pi * 480 * tt)) * _cadence(dur, 2.0, 4.0, 0.25), 0.01, seed), 0.35, 0.01, trim=False)

def phone_pickup(seed=20):
    """The far end picks up: a click, a handling bump, then the open line."""
    out = zeros(0.9); tt = t_(0.9)
    place(out, norm(strike(PLASTIC, 0.0002, seed, 0.7, 0.05), 1.0), 0.02, 0.8)
    place(out, norm(lp(noise(0.25, seed + 1), 300) * np.exp(-t_(0.25) * 18), 1.0), 0.05, 0.5)
    out += 0.03 * unit(bp(noise(0.9, seed + 2), 300, 3400)) * np.clip((tt - 0.03) / 0.05, 0, 1)
    return fin(phone_line(out, 0.006, seed), 0.45, 0.15)

def phone_hangup_click(seed=21):
    """The call drops: a hard click on the line and then dead air."""
    out = zeros(0.4); tt = t_(0.4)
    place(out, norm(strike(PLASTIC, 0.0002, seed, 0.8, 0.04), 1.0), 0.06, 1.0)
    place(out, norm(strike(PLASTIC, 0.0002, seed + 1, 0.8, 0.04), 1.0), 0.066, 0.4)
    x = phone_line(out, 0.0, seed) + 0.02 * unit(bp(noise(0.4, seed + 2), 300, 3400)) * (tt < 0.06)
    return fin(x, 0.45, 0.01)

# -------------------------------------------------------------- the body ---
def _breath(dur, bands, seed, shake=1.0):
    """one breath: noise through the mouth's resonances, with a tremor and a couple of catches"""
    tt = t_(dur); r = np.random.default_rng(seed)
    x = sum(g * unit(bp(noise(dur, seed + j), lo, hi)) for j, (lo, hi, g) in enumerate(bands))
    env = np.sin(np.pi * tt / dur) ** 0.9 * (1 + shake * 0.7 * (slow(dur, 9, seed + 7) - 0.5))
    for c in 0.2 + 0.6 * r.random(2): env *= 1 - 0.55 * shake * np.exp(-((tt / dur - c) / 0.03) ** 2)
    return x * env

def breath_close(seed=24):
    """One slow, nervous breath right at the mic: a shaky inhale that catches twice, a held beat,
    a long unsteady exhale."""
    out = zeros(4.6)
    place(out, norm(_breath(1.5, [(700, 1500, 1.0), (1800, 3200, 0.5), (4000, 8000, 0.3)], seed, 1.0), 0.8), 0.05)
    place(out, norm(_breath(2.3, [(400, 1100, 1.0), (1200, 2500, 0.45), (3000, 7000, 0.12)], seed + 20, 0.6), 0.65), 1.95)
    out += norm(lp(noise(4.6, seed + 40), 160) * lp(np.abs(out), 8), 0.12)     # close-mic air on the diaphragm
    return fin(room(out, 0.25, 0.12, 6000, seed), 0.4, 0.2)

def heartbeat(dur=20.0, bpm=62, seed=25):
    """A heartbeat felt in the chest: a deep, slightly irregular lub-dub."""
    r = np.random.default_rng(seed); out = zeros(dur); t, k = 0.05, 0
    while t < dur - 0.6:
        place(out, _thump(46, 0.4, 13, seed + k), t, 0.92 + 0.08 * r.random())
        place(out, _thump(58, 0.3, 20, seed + k + 1), t + 0.29, 0.62)
        t += 60 / bpm * (1 + 0.025 * r.standard_normal()); k += 2
    x = lp(out, 170); x += 0.45 * np.max(np.abs(x)) * bp(np.tanh(2.5 * x / (np.max(np.abs(x)) + 1e-12)), 90, 300)
    return fin(x, 0.8, 0.1, trim=False)

def tinnitus_ring(dur=6.0, seed=34):
    """The thin ring in your ears after a shock: a 5.2 kHz tone with a slow beat, swelling in and
    fading away."""
    tt = t_(dur); env = np.minimum(1, tt / 1.0) ** 2 * np.minimum(1, (dur - tt) / 3.0) ** 1.5
    return fin((np.sin(2 * np.pi * 5200 * tt) + 0.6 * np.sin(2 * np.pi * 5203.1 * tt) + 0.05 * np.sin(2 * np.pi * 2600 * tt)) * env, 0.16, 0.01, trim=False)

# ---------------------------------------------------------- tension / design ---
def countdown_tick(seed=27):
    """One second of a countdown: a dry mechanical tick with a low, dark D under it."""
    out = zeros(1.6); tt = t_(1.5)
    place(out, norm(strike([(820, 90, 0.3), (1750, 120, 0.6), (3150, 160, 0.5), (4900, 220, 0.3)], 0.0004, seed, 0.6, 0.15), 1.0), 0.01, 1.0)
    place(out, (np.sin(2 * np.pi * hz(38) * tt) + 0.3 * np.sin(2 * np.pi * hz(50) * tt)) * np.exp(-tt * 6) * (1 - np.exp(-tt * 120)), 0.01, 0.2)
    return fin(room(out, 1.4, 0.35, 3000, seed), 0.6, 0.2)

def clock_tick_bed(dur=20.0, seed=28):
    """A wall clock across a quiet room: tick and tock once a second."""
    r = np.random.default_rng(seed); out = zeros(dur); n = len(out)
    tick = [(2350, 280, 0.6), (3700, 320, 0.5), (5200, 400, 0.3), (520, 160, 0.12), (910, 200, 0.08)]
    pool = [[norm(strike([(f * s, d, a) for f, d, a in tick], 0.0003, seed + 10 * j + k, 0.5, 0.12), 1.0) for k in range(4)] for j, s in enumerate((1.0, 0.82))]
    for k in range(int(dur)):
        place(out, pool[k % 2][int(r.integers(4))], 0.2 + k + 0.002 * r.standard_normal(), 0.9 + 0.1 * r.random())
    return fin(room(out, 0.6, 0.6, 5000, seed)[:n], 0.35, 0.3, 0.05, trim=False)

def low_boom(seed=29):
    """A deep sub boom (falling onto D1) that rolls away into a big dark space."""
    return fin(room(_boom(5.0, hz(26), seed), 3.0, 0.5, 1200, seed)[: int(6.5 * SR)], 0.85, 0.8)

def whoosh_soft(dur=1.6, seed=30):
    """A soft, airy whoosh passing close by: a band of noise sweeping up and back down."""
    u = t_(dur) / dur
    x = sweep(noise(dur, seed), 260 * 9 ** np.sin(np.pi * u), 'band', 0.5) * np.sin(np.pi * u) ** 2
    return fin(room(x, 0.8, 0.25, 5000, seed), 0.4, 0.2)

def reverse_swell(dur=3.0, seed=31):
    """A reversed reverb tail: a dark D-Ab-Eb-A cluster swelling out of nothing and stopping dead."""
    tt = t_(0.6)
    hit = sum(np.sin(2 * np.pi * hz(m) * tt) for m in (38, 44, 51, 57)) * np.exp(-tt * 7) + 0.4 * bp(noise(0.6, seed), 200, 3000) * np.exp(-tt * 20)
    wet = signal.fftconvolve(hit, room_ir(dur * 1.1, 3000, seed, 3))[: int(dur * SR)]
    return fin(wet[::-1], 0.6, 0.012, 0.01, trim=False)

def stinger_dissonant(seed=32):
    """A dissonant string stab: D, Eb, Ab and A bowed hard together over a low D, with bow scrape,
    a glassy ponticello edge and a sub underneath, ringing off into a big room."""
    dur = 4.5; tt = t_(dur); x = np.zeros(len(tt))
    env = (1 - np.exp(-tt * 120)) * (0.35 + 0.65 * np.exp(-tt * 6)) * np.exp(-tt * 0.9)
    for j, m in enumerate([50, 62, 63, 68, 69]):
        for k, cents in enumerate((-7, 6)):
            f = hz(m) * 2 ** (cents / 1200) * (1 + 0.003 * np.sin(2 * np.pi * (5.2 + 0.4 * j) * tt + j))
            x += saw(f, dur, seed + 2 * j + k, 6000) * (1.3 if m == 50 else 1.0)
    body, edge = lp(x, 3200) * env, hp(x, 2500) * env * np.exp(-tt * 2)
    scrape = bp(noise(dur, seed), 1200, 6000) * np.exp(-tt * 14)
    sub = np.sin(2 * np.pi * hz(26) * tt) * np.exp(-tt * 2.5) * (1 - np.exp(-tt * 80))
    y = norm(body, 1.0) + norm(edge, 0.3) + norm(scrape, 0.35) + norm(sub, 0.5)
    return fin(room(y, 3.2, 0.7, 4000, seed)[: int(7 * SR)], 0.8, 1.0)

def riser(dur=6.0, seed=33):
    """Tension riser: a dissonant cluster sliding upward under a tremolo that speeds up, noise
    sweeping open, everything growing until it stops dead at the end."""
    tt = t_(dur); u = tt / dur; tones = np.zeros(len(tt))
    trem = 1 - 0.45 * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(2 + 12 * u ** 2) / SR))
    for j, m in enumerate([50, 56, 57, 63]):
        f = hz(m) * 2 ** (5 * u ** 2 / 12)
        tones += saw(f * 2 ** (-5 / 1200), dur, seed + 2 * j, 5000) + saw(f * 2 ** (5 / 1200), dur, seed + 2 * j + 1, 5000)
    tones = sweep(tones, 350 * 14 ** u, 'low')
    air = sweep(noise(dur, seed), 300 * 25 ** u, 'band', 0.6)
    x = (norm(tones, 1.0) * trem + norm(air, 0.6) + norm(lp(noise(dur, seed + 9), 90), 0.3) * u) * u ** 2.2
    return fin(x, 0.75, 0.012, 0.01, trim=False)

# ------------------------------------------------------------------- beds ---
def _cricket(dur, f, rate, seed):
    """one cricket: chirps of three or four quick pulses, now and then a rest"""
    r = np.random.default_rng(seed); out = zeros(dur); t = r.random()
    tp = t_(0.022); pulse = np.sin(2 * np.pi * f * tp) * np.sin(np.pi * tp / 0.022) ** 2
    while t < dur - 0.2:
        if r.random() < 0.85:
            for p in range(3 + (r.random() < 0.4)): place(out, pulse, t + p * 0.03, 0.8 + 0.2 * r.random())
        t += (0.85 + 0.3 * r.random()) / rate + (r.random() < 0.06) * 3 * r.random()
    return out

def night_ambience_bed(dur=60.0, seed=35):
    """A quiet suburban night outside: very soft wind, a distant traffic hum with a far car now
    and then, and a few crickets."""
    r = np.random.default_rng(seed)
    wind = unit(lp(noise(dur, seed), 350)) * (0.25 + 0.75 * slow(dur, 0.07, seed + 1)) + 0.15 * unit(bp(noise(dur, seed + 2), 500, 1300)) * slow(dur, 0.05, seed + 3) ** 2
    hum = unit(bp(noise(dur, seed + 4), 45, 260)) * (0.8 + 0.2 * slow(dur, 0.03, seed + 5))
    cars = np.zeros(len(hum)); t = 4 + 10 * r.random()
    while t < dur:
        L = 7 + 5 * r.random(); place(cars, unit(bp(noise(L, seed + int(t)), 90, 900)) * np.sin(np.pi * t_(L) / L) ** 3, max(0, t - L / 2))
        t += 14 + 20 * r.random()
    crick = sum(_cricket(dur, 4200 + 900 * r.random(), 1.1 + 0.6 * r.random(), seed + 10 + k) * (0.4 + 0.6 * r.random()) for k in range(3))
    return fin(0.25 * wind + 0.12 * hum + 0.12 * cars + 0.15 * crick, 0.3, 0.5, 0.5, trim=False)

def house_room_tone_bed(dur=30.0, seed=36):
    """A still house at night: soft air, a faint fridge hum through the wall, the furnace far off."""
    tt = t_(dur)
    air = unit(lp(noise(dur, seed), 260)) + 0.12 * unit(bp(noise(dur, seed + 1), 300, 2500)) + 0.03 * unit(hp(noise(dur, seed + 2), 5000))
    hum = sum(a * np.sin(2 * np.pi * 60 * k * tt + k) for k, a in [(1, 0.05), (2, 0.09), (3, 0.04), (4, 0.025), (6, 0.01)])
    hvac = unit(lp(noise(dur, seed + 4), 90)) * slow(dur, 0.01, seed + 5)
    return fin(0.6 * air + hum * (0.7 + 0.3 * slow(dur, 0.02, seed + 3)) + 0.4 * hvac, 0.2, 0.5, 0.5, trim=False)

# ----------------------------------------------------------------- render ---
LIBRARY = [
    ('knock_door_heavy', knock_door, dict(variant='heavy')), ('knock_door_polite', knock_door, dict(variant='polite')),
    ('tap_glass', tap_glass, {}), ('radio_crackle', radio_crackle, {}), ('radio_static_bed', radio_static_bed, dict(dur=20.0)),
    ('radio_click', radio_click, {}), ('radio_beep', radio_beep, {}), ('car_door_open', car_door_open, {}),
    ('car_door_close', car_door_close, {}), ('car_engine_idle_bed', car_engine_idle_bed, dict(dur=20.0)),
    ('car_drive_away', car_drive_away, {}), ('footsteps_path', footsteps_path, {}), ('slippers_floor', slippers_floor, {}),
    ('key_in_lock', key_in_lock, {}), ('lock_turn', lock_turn, {}), ('keys_jingle', keys_jingle, {}),
    ('mail_slot', mail_slot, {}), ('paper_rustle', paper_rustle, {}), ('pen_click', pen_click, {}),
    ('phone_busy_tone', phone_busy_tone, dict(dur=6.0)), ('phone_ring_out', phone_ring_out, dict(dur=12.0)),
    ('phone_pickup', phone_pickup, {}), ('phone_hangup_click', phone_hangup_click, {}), ('tv_off', tv_off, {}),
    ('curtain_rings', curtain_rings, {}), ('breath_close', breath_close, {}), ('heartbeat', heartbeat, dict(dur=20.0)),
    ('camera_beep_on', camera_beep, dict(state='on')), ('camera_beep_off', camera_beep, dict(state='off')),
    ('countdown_tick', countdown_tick, {}), ('clock_tick_bed', clock_tick_bed, dict(dur=20.0)), ('low_boom', low_boom, {}),
    ('whoosh_soft', whoosh_soft, {}), ('reverse_swell', reverse_swell, {}), ('stinger_dissonant', stinger_dissonant, {}),
    ('riser', riser, dict(dur=6.0)), ('tinnitus_ring', tinnitus_ring, {}),
    ('night_ambience_bed', night_ambience_bed, dict(dur=60.0)), ('house_room_tone_bed', house_room_tone_bed, dict(dur=30.0)),
]

def main(out_dir):
    import soundfile as sf
    os.makedirs(out_dir, exist_ok=True); index = []
    for name, fn, kw in LIBRARY:
        x = np.asarray(fn(**kw), np.float32)
        if not np.all(np.isfinite(x)): raise ValueError(name + ': non-finite samples')
        sf.write(os.path.join(out_dir, name + '.wav'), x, SR, subtype='PCM_24')
        pk = 20 * np.log10(np.max(np.abs(x)) + 1e-12)
        desc = ' '.join(fn.__doc__.split()).split('. ')[0].rstrip('.')
        index.append(dict(name=name, file=name + '.wav', duration=round(len(x) / SR, 3), peak_dbfs=round(float(pk), 2),
                          function=fn.__name__, args=kw, desc=desc))
        print(f'{name:22s} {len(x) / SR:6.2f} s  peak {pk:6.1f} dBFS')
    with open(os.path.join(out_dir, 'index.json'), 'w') as f: json.dump(index, f, indent=1)

if __name__ == '__main__':
    if len(sys.argv) != 2: sys.exit('usage: python3 sfx_horror.py <out_dir>')
    main(sys.argv[1])
