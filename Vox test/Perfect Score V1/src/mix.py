#!/usr/bin/env python3
"""Final soundtrack: narration (studio chain) + score stems (ducked under the voice)
+ procedural SFX placed on the picture's action (footsteps on the walk cycles, pen
squeaks on the drawn strokes, slams on contact frames) + room tone per location.
    python3 mix.py <vo_raw.wav> <music stem dir> <whisper dir> <out.wav>
"""
import sys, os, numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy import signal
sys.path.insert(0, os.path.dirname(__file__))
import sfx as X

SR = 48000
DUR = 81.0
N = int(DUR * SR)
VO_PATH, MUS_DIR, WH_DIR, OUT = sys.argv[1:5]
db = lambda g: 10 ** (g / 20)

# --------------------------------------------------------------- helpers ---
def biquad(kind, f0, gain_db=0.0, q=0.707):
    A = 10 ** (gain_db / 40); w = 2 * np.pi * f0 / SR; c, s = np.cos(w), np.sin(w); al = s / (2 * q)
    if kind == 'peak':
        b = [1 + al * A, -2 * c, 1 - al * A]; a = [1 + al / A, -2 * c, 1 - al / A]
    elif kind == 'lowshelf':
        sq = 2 * np.sqrt(A) * al
        b = [A * ((A + 1) - (A - 1) * c + sq), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - sq)]
        a = [(A + 1) + (A - 1) * c + sq, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - sq]
    elif kind == 'highshelf':
        sq = 2 * np.sqrt(A) * al
        b = [A * ((A + 1) + (A - 1) * c + sq), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - sq)]
        a = [(A + 1) - (A - 1) * c + sq, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - sq]
    return np.array(b) / a[0], np.array(a) / a[0]
def eq(x, *bands):
    for kind, f, g, q in bands:
        b, a = biquad(kind, f, g, q); x = signal.lfilter(b, a, x)
    return x
def envelope(x, att=0.005, rel=0.08):
    """peak follower with separate attack/release (vectorised in blocks)"""
    a_a = np.exp(-1 / (att * SR)); a_r = np.exp(-1 / (rel * SR))
    y = np.abs(x); out = np.empty_like(y); e = 0.0
    for i, v in enumerate(y):
        e = a_a * e + (1 - a_a) * v if v > e else a_r * e + (1 - a_r) * v
        out[i] = e
    return out
def env_fast(x, win=0.01):
    """RMS envelope via moving average (fast)"""
    w = max(1, int(win * SR)); k = np.ones(w) / w
    return np.sqrt(np.convolve(x * x, k, 'same') + 1e-12)
def compress(x, thr_db, ratio, att=0.005, rel=0.09, knee=6):
    e = env_fast(x, att * 2 + 0.004)
    # smooth release with a one-pole on the gain curve
    lvl = 20 * np.log10(e + 1e-9)
    over = lvl - thr_db
    gr = np.where(over <= -knee / 2, 0, np.where(over >= knee / 2, over * (1 - 1 / ratio), (over + knee / 2) ** 2 / (2 * knee) * (1 - 1 / ratio)))
    b, a = signal.butter(1, 1 / (rel * 2 * np.pi) * 2 * np.pi / (SR / 2) * 0.5 if False else 8 / (SR / 2))
    gr = signal.lfilter(b, a, gr)
    return x * 10 ** (-gr / 20)
def limiter(x, ceil_db=-1.0, look=0.002, rel=0.05):
    """lookahead brickwall on the stereo max, 4x oversampled peak estimate"""
    ceil = 10 ** (ceil_db / 20)
    up = signal.resample_poly(np.max(np.abs(x), axis=1) if x.ndim > 1 else np.abs(x), 4, 1)
    pk = np.max(up.reshape(-1, 4), axis=1)[: len(x)]
    need = np.minimum(1.0, ceil / np.maximum(pk, 1e-9))
    L = int(look * SR)
    g = np.minimum.accumulate(np.concatenate([need[L:], np.ones(L)])[::-1])[::-1] if False else need
    # running min over lookahead window, then smooth release
    from scipy.ndimage import minimum_filter1d
    g = minimum_filter1d(need, size=2 * L + 1)
    ar = np.exp(-1 / (rel * SR)); out = np.empty_like(g); cur = 1.0
    for i, v in enumerate(g):
        cur = v if v < cur else ar * cur + (1 - ar) * v
        out[i] = cur
    return x * (out[:, None] if x.ndim > 1 else out)
def synth_ir(dur=0.5, rt60=0.35, pre=0.008, seed=1, bright=6000):
    n = int(dur * SR); t = np.arange(n) / SR
    r = np.random.default_rng(seed)
    ir = np.zeros((n, 2))
    for ch in range(2):
        x = r.standard_normal(n) * np.exp(-6.91 * t / rt60)
        x = X.lp(x, bright)
        ir[:, ch] = x
    p = int(pre * SR); ir = np.concatenate([np.zeros((p, 2)), ir])
    ir /= np.sqrt(np.sum(ir ** 2))
    return ir
def place(bus, x, t, gain_db=0.0, pan=0.0):
    """mix mono (or stereo) x into bus at time t with equal-power pan"""
    i = int(round(t * SR))
    if i >= len(bus) or i + len(x) <= 0: return
    if i < 0: x = x[-i:]; i = 0
    x = x[: len(bus) - i]
    g = db(gain_db)
    if x.ndim == 1:
        l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
        bus[i:i + len(x), 0] += x * g * l * np.sqrt(2); bus[i:i + len(x), 1] += x * g * r * np.sqrt(2)
    else:
        bus[i:i + len(x)] += x * g

# ---------------------------------------------------------------- voice ---
vo24, sr0 = sf.read(VO_PATH)
if vo24.ndim > 1: vo24 = vo24.mean(1)
from math import gcd
g_ = gcd(SR, sr0)
vo = signal.resample_poly(vo24, SR // g_, sr0 // g_) if sr0 != SR else vo24
vo = np.concatenate([vo, np.zeros(max(0, N - len(vo)))])[:N]
# studio chain: clean low end, warmth, de-mud, presence, air (exciter), de-ess, compression
vo = X.hp(vo, 75, 2)
vo = eq(vo, ('lowshelf', 140, 1.5, 0.7), ('peak', 320, -3.0, 1.0), ('peak', 3400, 3.5, 0.8), ('highshelf', 5000, 3.0, 0.7), ('peak', 2200, 2.0, 1.0))
air = X.hp(np.tanh(X.hp(vo, 3000) * 6) / 6, 9500, 4)
vo = vo + air * db(-20)
# de-esser: reduce 5-10 kHz when it dominates
ess = X.bp(vo, 5000, 10000, 2)
e_s = env_fast(ess, 0.004); e_all = env_fast(vo, 0.004)
ratio = e_s / (e_all + 1e-9)
red = np.clip((ratio - 0.22) * 3.0, 0, 0.8)
vo = vo - ess * red
pk = np.max(np.abs(vo)) + 1e-9; vo = vo / pk * 0.5
vo = compress(vo, -20, 3.0)
vo = compress(vo, -10, 6.0, att=0.001, rel=0.04)
vo_st = np.stack([vo, vo], 1)
ir_vo = synth_ir(0.45, 0.3, 0.006, 3, 7000)
room = np.stack([signal.fftconvolve(vo, ir_vo[:, c])[:N] for c in range(2)], 1)
vo_st = vo_st + room * db(-23)
meter = pyln.Meter(SR)
vo_st *= db(-17.0 - meter.integrated_loudness(vo_st))  # voice at -17 LUFS before the bus
vo_env = env_fast(vo, 0.03)
vo_on = signal.lfilter(*signal.butter(1, 4 / (SR / 2)), (vo_env > 0.01).astype(float))

# ---------------------------------------------------------------- music ---
def load(name):
    a, s = sf.read(os.path.join(MUS_DIR, name + '.wav'))
    if a.ndim == 1: a = np.stack([a, a], 1)
    a = np.concatenate([a, np.zeros((max(0, N - len(a)), 2))])[:N]
    return a
STEM_GAIN = {'pads': 2.0, 'strings': 0.0, 'pizz': 0.0, 'bass': 1.0, 'drums': -1.0, 'keys': 0.0, 'brass': -2.0, 'hits': -3.0}
mus = np.zeros((N, 2)); hits = None
for k, g in STEM_GAIN.items():
    a = load(k) * db(g)
    if k == 'hits': hits = a
    else: mus += a
mus *= db(-23.0 - meter.integrated_loudness(mus))       # score bed ~5 LU under the voice, like the references
# light duck under the narration (2.5 dB), released in the gaps
duck = 1 - vo_on * (1 - db(-2.5))
mus = mus * duck[:, None]
hits *= db(-19.0 - meter.integrated_loudness(hits + 1e-9 * np.random.default_rng(0).standard_normal(hits.shape)))
music = mus + hits

# ------------------------------------------------------------------ SFX ---
fx = np.zeros((N, 2))
fxr = np.zeros((N, 2))  # sent to the hallway reverb
FX_COUNT = [0]
def F(t, x, g=0.0, pan=0.0, rev=0.0):
    FX_COUNT[0] += 1
    place(fx, x, t, g, pan)
    if rev: place(fxr, x, t, g + 20 * np.log10(rev), pan)

# room tone per location (crossfaded at the cuts)
SETS = [(0, 30.25, 'class'), (30.25, 32.05, 'hall'), (32.05, 44.4, 'office'), (44.4, 46.05, 'home'), (46.05, 47.6, 'office'),
        (47.6, 51.3, 'hall'), (51.3, 68.85, 'office'), (68.85, 72.65, 'night'), (72.65, 74.0, 'office'), (74.0, 75.85, 'hall'), (75.85, 81.0, 'class')]
TONE_G = {'class': -33, 'hall': -31, 'office': -38, 'home': -36, 'night': -32}
for a, b, kind in SETS:
    d = b - a + 0.1
    x = X.room_tone(d, kind, int(a * 10))
    x = X.fade(x, 0.05, 0.05)
    g = TONE_G[kind] + (-10 if a <= 65.8 < b else 0)
    F(a, x, g)
# 'The room goes silent' 65.8-67.3: tone dips further (handled by a gain ride below)

# pen strokes: the red 100 (stroke timeline mirrors paper.js)
SEG100 = [(0, 0.0735), (0.1285, 0.2761), (0.3157, 0.4632), (0.5064, 1.0)]
def strokes(t0, t1, segs, kind='marker', g=-14, seed=1):
    d = t1 - t0; n = int(d * SR); sp = np.zeros(n)
    for a, b in segs:
        i, j = int(a * n), int(b * n); sp[i:j] = 1.0
    sp = signal.lfilter(*signal.butter(1, 40 / (SR / 2)), sp)
    F(t0, X.scribble(d, sp, seed, kind), g, 0.15)
strokes(0.25, 1.6, SEG100, 'marker', -15, 1)
strokes(64.38, 65.2, SEG100, 'marker', -11, 2)
for i, (a, b) in enumerate([(62.55, 62.85), (63.05, 63.35), (63.55, 63.85)]):
    strokes(a, b, [(0, 0.3), (0.35, 1.0)], 'marker', -10, 10 + i)
    F(b - 0.02, X.clock_tick(40 + i), -20)

# footsteps on the walk cycles (cadence 0.958 Hz -> a step every 0.522 s)
def steps(t_start, t_end, kind='shoe', g=-19, pan=0.0, rev=0.0, first=1):
    t = t_start + 0.522 * first; k = 0
    while t < t_end - 0.05:
        u = (t - t_start) / (t_end - t_start)
        amp = np.sin(np.pi * np.clip(u, 0.05, 0.95)) ** 0.5
        F(t, X.footstep(kind, 1.0, int(t * 100)), g + 20 * np.log10(max(amp, 0.2)), pan + (0.08 if k % 2 else -0.08), rev)
        t += 0.522; k += 1
steps(2.05, 4.75, 'shoe', -20)
steps(6.2, 9.0, 'shoe', -18)
steps(30.0, 32.2, 'hall', -15, 0.0, 0.5)
steps(47.3, 50.6, 'hall', -17, 0.0, 0.5)
for t in [18.14, 18.66, 19.09, 19.61, 76.37, 76.89, 77.16, 77.68]: F(t, X.footstep('shoe', 1, int(t * 100)), -20)

# desk pushes: scrape follows the desk speed
def push(ta, tb, accel, g=-17):
    d = tb - ta; n = int(d * SR); k = np.linspace(0, 1, n)
    sp = (4 * k - 3 * k * k) if accel else (1 - k) * (1 + 3 * k)
    sp = np.clip(sp / sp.max(), 0, 1)
    F(ta, X.scrape(d, sp, int(ta)), g)
push(17.62, 18.95, True); push(18.95, 19.95, False); F(19.93, X.thud(110, 0.3, 3, 0.6), -20)
push(75.85, 77.02, True); push(77.02, 78.05, False); F(78.03, X.thud(110, 0.3, 4, 0.6), -20)

# cut whooshes (short, under the voice), like the references
for t in [3.1, 6.6, 10.5, 12.6, 16.75, 22.8, 30.25, 32.05, 35.5, 37.05, 44.4, 46.05, 47.6, 51.3, 53.15, 58.85, 68.85, 70.6, 72.65, 74.0, 75.85, 78.25]:
    F(t - 0.18, X.whoosh(0.4, True, int(t * 10)), -24, 0.0)

# hook
F(0.0, X.whoosh(0.6, False, 2, 200, 3000), -20)
F(5.05, X.cloth(0.35, 1), -20)
F(5.28, X.whoosh(0.65, True, 3, 300, 8000, 1.0), -13)
F(5.45, X.murmur(0.8, 10, 5, 0.6), -26)
F(6.24, X.sub_boom(1.2, 46), -10)
# rising action
F(7.0, X.paper_rustle(0.32, 4), -22); F(7.62, X.paper_slap(5), -15)
F(9.05, X.paper_rustle(0.45, 6), -23)
for t in [11.08, 11.56, 17.2]:
    F(t - 0.32, X.paper_rustle(0.3, int(t)), -21); F(t, X.paper_slap(int(t * 3)), -14)
F(12.6, X.scribble(0.42, None, 7, 'marker'), -22)
F(13.92, X.mug_clink(), -18); F(14.6, X.sip(0.32), -18)
for t in [13.85, 14.85, 15.85]: F(t, X.clock_tick(int(t)), -22)
F(15.1, X.whoosh(1.5, True, 9, 80, 900, 0.8), -22)
F(17.62, X.murmur(2.2, 12, 8, 0.6), -30)
F(20.45, X.scribble(0.6, None, 9, 'pencil'), -24)
# conflict
F(23.0, X.whoosh(0.4, True, 11, 200, 2000), -20)
F(23.42, X.stack_slam(), -5); F(23.42, X.sub_boom(1.2, 44), -11)
F(23.92, X.groan(0.9, 12), -15)
F(24.6, X.scribble(2.0, None, 12, 'pencil'), -22)
F(27.2, X.scribble(0.72, None, 13, 'pencil') * 1.4, -16); F(27.95, X.scribble(0.3, None, 14, 'pencil'), -18)
F(28.35, X.scribble(0.5, None, 15, 'marker'), -22)
F(29.17, X.pen_drop(), -13); F(29.15, X.chair_roll(0.5), -16); F(29.15, X.cloth(0.3, 2), -18)
F(30.35, X.heartbeat(), -14); F(31.2, X.heartbeat(), -15)
F(31.33, X.latch(), -18, 0, 0.5); F(31.4, X.door_creak(0.6), -20, 0, 0.5)
F(32.2, X.zipper(0.35, 1), -16); F(32.55, X.paper_rustle(0.4, 13), -20); F(32.95, X.paper_slap(14, 0.8), -18)
F(33.05, X.paper_rustle(0.3, 15), -22); F(33.35, X.paper_slap(16, 0.6), -20); F(33.4, X.zipper(0.25, 2), -19)
F(33.95, X.crinkle(0.35, 3), -20); F(34.15, X.peel(1.1, 4), -14)
F(35.5, X.tape_rewind(1.55), -17)
for k in range(6): F(37.1 + k * 0.42 + 0.21, X.clock_tick(60 + k, True), -26)
F(39.62, X.sub_boom(1.0, 40), -18)
for ts in [40.49, 41.13, 41.77]:
    F(ts - 0.1, X.keyclicks(0.25, 14, int(ts * 10)), -20)
    F(ts + 0.2, X.error_buzz(0.22), -19)
F(42.22, X.beep(880, 0.12), -22)
F(43.5, X.clock_tick(70), -27)
# dip
F(44.4, X.ringtone(0.75), -18, -0.2)
for t in [44.4, 45.0]: F(t, X.phone_buzz(0.18 if t < 44.6 else 0.12), -16, -0.2)
F(45.12, X.cloth(0.25, 3), -20); F(45.12, X.latch(5) * 0.3, -24, -0.2)
F(45.7, X.muffled_voice(0.35), -24, -0.3)
F(46.6, X.whoosh(0.34, False, 21, 300, 3000), -16); F(46.94, X.stamp_slam(), -5); F(46.94, X.sub_boom(0.8, 55), -14)
F(47.6, X.murmur(3.7, 16, 22, 0.7), -25, 0, 0.6)
wh = sorted(f for f in os.listdir(WH_DIR) if f.endswith('.wav'))
W = {f: sf.read(os.path.join(WH_DIR, f))[0] for f in wh}
for t, f, g, pan in [(47.85, 'w04.wav', -19, -0.6), (48.3, 'w03.wav', -21, 0.55), (48.75, 'w08.wav', -20, -0.4), (49.15, 'w06.wav', -22, 0.7),
                     (49.45, 'w01.wav', -22, -0.75), (49.8, 'w09.wav', -21, 0.45), (50.05, 'w02.wav', -20, -0.3),
                     (50.3, 'w00.wav', -13, 0.15), (50.36, 'w07.wav', -16, -0.35), (50.45, 'w05.wav', -18, 0.6)]:
    F(t, W[f], g, pan, 0.8)
F(49.3, X.reverse_swell(1.0), -18)
F(51.55, X.clock_tick(80), -24); F(52.0, X.cloth(0.5, 4), -21); F(52.55, X.clock_tick(81, True), -24)
F(53.35, X.paper_rustle(0.7, 30, 0.8), -18)
for t in [54.8, 55.8, 56.8]: F(t, X.clock_tick(int(t), t > 55), -23)
F(56.3, X.cloth(0.5, 5), -22)
F(57.7, X.cloth(0.3, 6), -24); F(58.05, X.thud(900, 0.08, 7, 0.4), -20)
F(58.85, X.whoosh(1.15, True, 31, 300, 6000, 0.7), -19)
for k in range(9): F(58.95 + k * 0.1, X.clock_tick(90 + k, k % 2 == 1), -18)
F(60.5, X.thud(800, 0.08, 8, 0.5), -19); F(60.55, X.cloth(0.4, 7), -24)
F(61.35, X.latch(9) * 0.6, -22)
F(64.34, X.sub_boom(1.6, 42), -7)
F(66.4, X.clock_tick(99), -26)
# payoff
F(68.9, X.scribble(1.6, None, 40, 'pencil'), -23)
for t in [70.8, 71.3, 71.9, 72.3]: F(t, X.thud(2500, 0.03, int(t), 0.2), -30)
F(71.0, X.notification(), -24)
F(72.8, X.cloth(0.3, 8), -20); F(73.25, X.applause(0.8, 3), -24)
F(74.72, X.frame_knock(), -15, 0.3, 0.5)
for k, t in enumerate([78.55, 78.85, 79.1, 79.45, 79.7]): F(t, X.chair_roll(0.25, 50 + k) * 0.7, -24, -0.6 + 0.3 * k)
F(78.3, X.scribble(1.5, None, 41, 'pencil'), -25)

# hallway reverb for sent effects
ir_h = synth_ir(1.6, 1.1, 0.02, 7, 5000)
fx_rev = np.stack([signal.fftconvolve(fxr[:, c], ir_h[:, c])[:N] for c in range(2)], 1)
fx_all = (fx + fx_rev * db(-6)) * db(-1.0)

# ------------------------------------------------------------------ bus ---
mix = vo_st + music + fx_all
# 'the room goes silent': pull music + room tone right down 65.8-67.25
tt = np.arange(N) / SR
ride = 1 - 0.85 * np.clip((tt - 65.75) / 0.12, 0, 1) * np.clip((67.25 - tt) / 0.15, 0, 1)
mix = vo_st + (music + fx_all) * ride[:, None]
# gentle bus glue + loudness normalisation + true-peak ceiling
mix = mix * db(-14.0 - meter.integrated_loudness(mix))
mix = limiter(mix, -1.2)
mix = mix * db(-14.0 - meter.integrated_loudness(mix))
mix = limiter(mix, -1.0)
fade_n = int(0.25 * SR); mix[-fade_n:] *= np.linspace(1, 0, fade_n)[:, None]
sf.write(OUT, mix.astype(np.float32), SR, subtype='FLOAT')
# stems for checking
base = OUT.rsplit('.', 1)[0]
for name, x in [('vo', vo_st), ('music', music), ('fx', fx_all)]:
    sf.write(base + '_' + name + '.wav', x.astype(np.float32), SR, subtype='FLOAT')
print('SFX events', FX_COUNT[0])
print('LUFS', round(meter.integrated_loudness(mix), 2), 'peak dBFS', round(20 * np.log10(np.abs(mix).max()), 2))
print('VO', round(meter.integrated_loudness(vo_st), 1), 'music', round(meter.integrated_loudness(music), 1), 'fx', round(meter.integrated_loudness(fx_all), 1))
