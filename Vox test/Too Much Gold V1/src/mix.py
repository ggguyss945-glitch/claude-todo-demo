#!/usr/bin/env python3
"""Soundtrack for "Too Much Gold": narration (studio chain), the score stems (lightly ducked
under the voice), synthesised SFX on the picture's actions, and a bed per location.
    python3 mix.py <vo_raw.wav> <music stem dir> <out.wav>
"""
import sys, os, numpy as np, soundfile as sf, pyloudnorm as pyln
from math import gcd
from scipy import signal
from scipy.ndimage import minimum_filter1d
sys.path.insert(0, os.path.dirname(__file__))
import sfx as X
import sfx_gold as G

SR = 48000
DUR = 51.0
N = int(DUR * SR)
VO_PATH, MUS_DIR, OUT = sys.argv[1:4]
db = lambda g: 10 ** (g / 20)

def biquad(kind, f0, gain_db=0.0, q=0.707):
    A = 10 ** (gain_db / 40); w = 2 * np.pi * f0 / SR; c, s = np.cos(w), np.sin(w); al = s / (2 * q)
    if kind == 'peak':
        b = [1 + al * A, -2 * c, 1 - al * A]; a = [1 + al / A, -2 * c, 1 - al / A]
    elif kind == 'lowshelf':
        sq = 2 * np.sqrt(A) * al
        b = [A * ((A + 1) - (A - 1) * c + sq), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - sq)]
        a = [(A + 1) + (A - 1) * c + sq, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - sq]
    else:
        sq = 2 * np.sqrt(A) * al
        b = [A * ((A + 1) + (A - 1) * c + sq), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - sq)]
        a = [(A + 1) - (A - 1) * c + sq, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - sq]
    return np.array(b) / a[0], np.array(a) / a[0]
def eq(x, *bands):
    for kind, f, g, q in bands:
        b, a = biquad(kind, f, g, q); x = signal.lfilter(b, a, x)
    return x
def env_fast(x, win=0.01):
    w = max(1, int(win * SR)); k = np.ones(w) / w
    return np.sqrt(np.convolve(x * x, k, 'same') + 1e-12)
def compress(x, thr_db, ratio, att=0.005, rel=0.09):
    e = env_fast(x, att * 2 + 0.004)
    lvl = 20 * np.log10(e + 1e-9)
    gr = np.minimum(0, (thr_db - lvl) * (1 - 1 / ratio))
    g = 10 ** (gr / 20)
    g = signal.lfilter([1 - np.exp(-1 / (rel * SR))], [1, -np.exp(-1 / (rel * SR))], g)
    return x * g
def limiter(x, ceil_db=-1.0, look=0.002, rel=0.05):
    ceil = 10 ** (ceil_db / 20)
    up = signal.resample_poly(np.max(np.abs(x), axis=1), 4, 1)
    pk = np.max(up.reshape(-1, 4), axis=1)[: len(x)]
    need = np.minimum(1.0, ceil / np.maximum(pk, 1e-9))
    g = minimum_filter1d(need, size=2 * int(look * SR) + 1)
    g = np.minimum(g, signal.lfilter([1 - np.exp(-1 / (rel * SR))], [1, -np.exp(-1 / (rel * SR))], g))
    g = minimum_filter1d(g, size=2 * int(look * SR) + 1)
    return x * g[:, None]
def synth_ir(dur=0.5, rt60=0.35, pre=0.008, seed=1, bright=6000):
    n = int(dur * SR); t = np.arange(n) / SR; r = np.random.default_rng(seed)
    ir = np.stack([X.lp(r.standard_normal(n) * np.exp(-6.91 * t / rt60), bright) for _ in range(2)], 1)
    ir = np.concatenate([np.zeros((int(pre * SR), 2)), ir])
    return ir / np.sqrt(np.sum(ir ** 2))
def place(bus, x, t, gain_db=0.0, pan=0.0):
    i = int(round(t * SR))
    if i >= len(bus) or i + len(x) <= 0: return
    if i < 0: x = x[-i:]; i = 0
    x = x[: len(bus) - i]; g = db(gain_db)
    l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
    bus[i:i + len(x), 0] += x * g * l * np.sqrt(2); bus[i:i + len(x), 1] += x * g * r * np.sqrt(2)

meter = pyln.Meter(SR)
# ----------------------------------------------------------------- voice ---
vo0, sr0 = sf.read(VO_PATH)
if vo0.ndim > 1: vo0 = vo0.mean(1)
g_ = gcd(SR, sr0)
vo = signal.resample_poly(vo0, SR // g_, sr0 // g_) if sr0 != SR else vo0
vo = np.concatenate([vo, np.zeros(max(0, N - len(vo)))])[:N]
vo = X.hp(vo, 75, 2)
vo = eq(vo, ('lowshelf', 140, 1.5, 0.7), ('peak', 320, -3.0, 1.0), ('peak', 3400, 3.0, 0.8), ('highshelf', 6000, 2.5, 0.7))
ess = X.bp(vo, 5000, 10000, 2)
red = np.clip((env_fast(ess, 0.004) / (env_fast(vo, 0.004) + 1e-9) - 0.22) * 3.0, 0, 0.8)
vo = vo - ess * red
vo = vo / (np.max(np.abs(vo)) + 1e-9) * 0.5
vo = compress(vo, -20, 3.0)
vo = compress(vo, -10, 6.0, att=0.001, rel=0.04)
ir_vo = synth_ir(0.4, 0.25, 0.006, 3, 7000)
vo_st = np.stack([vo, vo], 1) + np.stack([signal.fftconvolve(vo, ir_vo[:, c])[:N] for c in range(2)], 1) * db(-25)
vo_st *= db(-17.0 - meter.integrated_loudness(vo_st))
vo_on = signal.lfilter(*signal.butter(1, 4 / (SR / 2)), (env_fast(vo, 0.03) > 0.01).astype(float))

# ----------------------------------------------------------------- music ---
def load(name):
    a, s = sf.read(os.path.join(MUS_DIR, name + '.wav'))
    if a.ndim == 1: a = np.stack([a, a], 1)
    return np.concatenate([a, np.zeros((max(0, N - len(a)), 2))])[:N]
GAIN = {'pizz': 0.0, 'world': 0.0, 'bass': 1.0, 'drums': -1.5, 'keys': -1.0, 'winds': 0.5, 'strings': -1.0, 'brass': -2.0, 'pads': 0.0}
mus = sum(load(k) * db(g) for k, g in GAIN.items())
mus *= db(-22.0 - meter.integrated_loudness(mus))
mus *= (1 - vo_on * (1 - db(-3.0)))[:, None]
hits = load('hits')
hits *= db(-18.0 - meter.integrated_loudness(hits + 1e-7 * np.random.default_rng(0).standard_normal(hits.shape)))
music = mus + hits

# ------------------------------------------------------------------- SFX ---
fx = np.zeros((N, 2)); fxr = np.zeros((N, 2)); COUNT = [0]
def F(t, x, g=0.0, pan=0.0, rev=0.0):
    COUNT[0] += 1; place(fx, x, t, g, pan)
    if rev: place(fxr, x, t, g + 20 * np.log10(rev), pan)

# beds per location, crossfaded at the cuts
BEDS = [(0.0, 3.3, 'market', -29), (3.3, 10.12, 'desert', -22), (10.12, 19.7, 'market', -28), (19.7, 31.6, 'market', -32),
        (31.6, 35.86, 'void', -40), (35.86, 38.62, 'market', -34), (38.62, 39.94, 'desert', -23), (39.94, 43.2, 'camp', -23), (43.2, 51.0, 'market', -30)]
for a, b, kind, g in BEDS:
    d = b - a + 0.3
    if kind == 'market': x = G.market_bed(d, int(a * 10))
    elif kind == 'desert': x = G.desert_wind(d, int(a * 10)) + G.bells_walk(d, 1.5, int(a * 10)) * 0.8
    elif kind == 'camp': x = G.crickets(d, int(a)) + G.fire(d, int(a)) * 0.9
    else: x = X.lp(X.noise(d, 7), 160) * 0.3
    F(max(0, a - 0.15), X.fade(x.astype(np.float64), 0.15, 0.15), g)

# HOOK: the crowd roars, two handfuls of gold fly past the lens
F(0.0, G.cheer(1.7, 18, 1), -19)
for t, pan in [(0.3, -0.3), (0.86, 0.3)]:
    F(t - 0.05, X.whoosh(0.3, True, int(t * 10), 400, 3000, 0.7), -25, pan)
    F(t + 0.05, G.shower(0.55, 70, int(t * 100), 2600, 6000, 'burst'), -17, pan)
    F(t + 0.2, X.whoosh(0.35, False, int(t * 10) + 1, 800, 7000, 1.0), -19, -pan)
F(1.15, G.camel_grunt(0.7, 3, 1.0), -27, 0.2)
# the spice merchant sweeps the coins away like dirt
for t in [1.52, 2.32, 3.0]:
    F(t, G.broom(0.42, int(t * 10)), -20, -0.3)
    F(t + 0.12, G.shower(0.35, 25, int(t * 10) + 5, 2400, 5000), -25, -0.2)
F(3.3, X.whoosh(0.5, True, 33, 300, 4000, 0.6), -26)
# the caravan
for t in [3.5, 4.1, 4.7, 5.3]: F(t, G.hoof(int(t * 10)), -30)
F(6.2, G.camel_grunt(0.9, 6, 0.9), -27, 0.3)
F(9.6, G.clink(96, 3200, 0.35), -20, 0.2); F(10.0, G.hoof(100) * 0.6, -27, 0.2)
# a whole pouch for one roll of cloth
F(11.3, G.pouch(113, 1.0), -15, 0.15); F(11.33, G.pop(600, 1300, 0.08), -24); F(11.75, G.sparkle(117, 2349), -24, 0.2)
# gold for everyone
F(12.15, G.cheer(1.7, 20, 12), -20)
F(12.2, G.shower(1.6, 70, 122, 2300, 6000), -20)
F(14.0, G.pouch(140, 0.8), -17, -0.2); F(14.08, G.sparkle(141, 2637), -25, -0.2)
F(14.45, G.shower(0.7, 110, 145, 2800, 6500), -17, 0.2)
F(15.32, G.cheer(0.75, 8, 153, kids=True), -14); F(15.3, G.shower(0.7, 50, 154), -24)
F(16.45, G.camel_grunt(0.8, 164, 1.1), -21, 0.3); F(16.9, G.sparkle(169, 2093), -23, -0.1)
# Cairo is drowning in gold
F(17.56, G.cheer(2.1, 24, 175), -18)
F(17.56, G.shower(2.1, 140, 176, 2200, 6000, 'swell'), -19)
F(17.6, X.whoosh(2.0, True, 177, 200, 3000, 0.5), -27)
# "Except," — the needle drags off the record
F(19.69, G.record_scratch(197), -11)
F(20.95, G.chalk(0.4, 209), -21, 0.25); F(21.35, G.chalk(0.5, 213), -22, 0.25)
F(23.45, G.boing(0.4, 220), -27); F(23.5, X.cloth(0.3, 235), -23)
# the money changer: one gold coin in, three silver out, then one taken back
F(26.45, G.clink(264, 2700, 0.4), -18, -0.2); F(26.5, G.scale_creak(0.35, 265), -26)
for t in [26.85, 27.15, 27.45]: F(t, G.clink(int(t * 100), 4200, 0.3), -20, 0.2)
F(27.85, G.broom(0.25, 278) * 0.6, -28, 0.2); F(28.0, G.clink(280, 4400, 0.3), -23, 0.25); F(27.9, G.scale_creak(0.3, 279), -27)
# a man sunk in gold, holding up one loaf
F(29.0, G.shower(0.6, 30, 290, 2200, 4500), -25); F(29.75, G.gulp(), -24)
# a coin in the dirt, stepped over
for k in range(7): F(30.3 + k * 0.23, X.footstep('shoe', 1.0, 300 + k), -13 if k in (2, 3, 4) else -17, -0.4 + 0.13 * k)
F(30.36, G.clink(303, 3000, 0.2) * 0.4, -30)
# the showroom: one coin, then a flood
F(31.55, X.whoosh(0.5, True, 315, 300, 5000, 0.6), -24); F(31.75, G.sparkle(317, 3136), -21)
F(33.9, G.pour(2.0, 339), -13)
F(34.5, G.shower(1.2, 80, 345, 2200, 5500), -19)
# twelve years later; the best part; the camp
F(35.8, X.whoosh(0.5, True, 358, 300, 4000, 0.5), -26)
F(38.55, X.whoosh(0.5, True, 386, 300, 4000, 0.5), -26)
F(39.9, X.whoosh(0.5, True, 399, 300, 4000, 0.5), -26)
F(40.5, X.latch(405), -17); F(40.6, X.door_creak(0.9, 406), -11)
# runs out of money: an empty box, a moth
F(41.97, G.moth(1.25, 420), -11, 0.0)
F(42.05, G.hollow_knock(421), -27)
# back to the merchants
F(43.2, X.whoosh(0.5, True, 432, 300, 4000, 0.5), -27)
for k in range(5): F(43.45 + k * 0.42, X.footstep('shoe', 0.8, 434 + k), -19, 0.4 - 0.12 * k)
F(47.72, G.pouch(477, 0.7), -18, -0.1); F(47.8, G.sparkle(478, 2349), -27)
# they laugh; one coin flips into the lens
F(48.32, G.laugh(2.2, 4, 483), -11)
F(49.0, G.laugh(1.4, 3, 490, high=True), -16, 0.3)
F(50.2, X.whoosh(0.5, True, 502, 600, 7000, 0.8), -21); F(50.3, G.ting(3300, 503), -15)

ir_s = synth_ir(1.2, 0.8, 0.015, 7, 5000)
fx_rev = np.stack([signal.fftconvolve(fxr[:, c], ir_s[:, c])[:N] for c in range(2)], 1)
fx_all = (fx + fx_rev * db(-6)) * db(4.0)  # effects sit a few dB under the voice, as in the references

# ------------------------------------------------------------------- bus ---
tt = np.arange(N) / SR
# "runs out of money": the world goes quiet for a beat (beds and music down, the moth stays)
quiet = 1 - 0.7 * np.clip((tt - 41.88) / 0.05, 0, 1) * np.clip((43.15 - tt) / 0.1, 0, 1)
mix = vo_st + music * quiet[:, None] + fx_all
mix *= db(-14.0 - meter.integrated_loudness(mix))
mix = limiter(mix, -1.5)
mix *= db(-14.0 - meter.integrated_loudness(mix))
mix = limiter(mix, -1.2)
n = int(0.04 * SR); mix[:n] *= np.linspace(0, 1, n)[:, None]; mix[-n:] *= np.linspace(1, 0, n)[:, None]
sf.write(OUT, mix.astype(np.float32), SR, subtype='FLOAT')
base = OUT.rsplit('.', 1)[0]
for name, x in [('vo', vo_st), ('music', music), ('fx', fx_all)]: sf.write(base + '_' + name + '.wav', x.astype(np.float32), SR, subtype='FLOAT')
print('SFX events', COUNT[0])
print('LUFS', round(meter.integrated_loudness(mix), 2), 'peak dBFS', round(20 * np.log10(np.abs(mix).max()), 2))
print('VO', round(meter.integrated_loudness(vo_st), 1), 'music', round(meter.integrated_loudness(music), 1), 'fx', round(meter.integrated_loudness(fx_all), 1))
