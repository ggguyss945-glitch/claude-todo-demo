"""Sound effects for "Too Much Gold", synthesised like sfx.py (numpy + scipy, nothing sampled):
coins (clinks, showers, a pouch landing, a flood of gold), camel bells and grunts, cheering
crowds and laughing merchants, a record scratch, chalk, a broom, a moth, crickets and fire."""
import numpy as np
from scipy import signal
from sfx import SR, t_, noise, bp, lp, hp, env_ad, fade, norm, murmur, whoosh, clap

def place_into(out, x, t, g=1.0):
    i = int(t * SR)
    if i >= len(out): return
    x = x[: len(out) - i]; out[i:i + len(x)] += x * g

# ------------------------------------------------------------------ coins ---
def clink(seed=0, f0=None, dur=0.35, bright=1.0):
    """one gold coin: inharmonic partials of a thin disc, a hard tick at the start"""
    r = np.random.default_rng(seed)
    f0 = f0 or 2400 + 2600 * r.random()
    tt = t_(dur); x = np.zeros(len(tt))
    for ratio, a, d in [(1.0, 1.0, 9), (2.76, 0.55, 14), (5.40, 0.35, 22), (8.93, 0.2, 30)]:
        f = f0 * ratio * (1 + 0.004 * r.standard_normal())
        if f < SR / 2 - 500: x += a * np.sin(2 * np.pi * f * tt + r.random() * 6) * np.exp(-tt * d * (0.8 + 0.4 * r.random()))
    tick = hp(noise(dur, seed + 99), 4000) * np.exp(-tt * 400) * 0.6 * bright
    return fade(norm(x + tick, 0.6), 0.0005, 0.02)

def shower(dur=1.0, rate=40, seed=1, f_lo=2200, f_hi=5200, shape='even'):
    """many coins: clinks at random times; shape 'even', 'burst' (front-loaded) or 'swell'"""
    r = np.random.default_rng(seed); out = np.zeros(int((dur + 0.4) * SR))
    n = int(rate * dur)
    for k in range(n):
        u = r.random()
        t = dur * (u ** 2 if shape == 'burst' else u ** 0.5 if shape == 'swell' else u)
        c = clink(seed * 1000 + k, f_lo + (f_hi - f_lo) * r.random(), 0.25 + 0.2 * r.random())
        place_into(out, c, t, 0.35 + 0.65 * r.random())
    return fade(norm(out, 0.7), 0.002, 0.15)

def coin_land(seed=2):
    """a coin bouncing to rest on stone: three quick hits then a short spin-down rattle"""
    out = np.zeros(int(0.9 * SR)); r = np.random.default_rng(seed)
    t, a = 0.0, 1.0
    for k in range(3):
        place_into(out, clink(seed * 10 + k, 3000 + 400 * r.random(), 0.3), t, a); t += 0.12 * (0.7 ** k); a *= 0.6
    spin = np.sin(2 * np.pi * np.cumsum(30 + 60 * t_(0.4) / 0.4) / SR)
    rat = bp(noise(0.4, seed), 2500, 7000) * (spin > 0.6) * np.linspace(0.4, 0, len(spin))
    place_into(out, rat, t, 0.5)
    return norm(out, 0.6)

def pouch(seed=3, weight=1.0):
    """a heavy leather pouch of coins dropped into a palm: cloth thump + a squash of coins"""
    n = int(0.6 * SR); tt = np.arange(n) / SR
    thump = lp(noise(0.6, seed), 260) * np.exp(-tt * 28) * 2.0 + np.sin(2 * np.pi * 95 * tt) * np.exp(-tt * 22) * 0.8
    jing = shower(0.22, 70, seed + 5, 2600, 6000, 'burst')[:n] * 0.7
    return norm(thump * weight + jing, 0.75)

def pour(dur=2.0, seed=4):
    """a flood of gold: a roar of thousands of coins that swells and then thins out"""
    tt = t_(dur)
    roar = bp(noise(dur, seed), 1500, 9000) * (0.4 + 0.6 * np.abs(lp(noise(dur, seed + 1), 30)) * 8)
    bed = lp(noise(dur, seed + 2), 500) * 0.6
    env = np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 0.8
    x = (roar + bed) * env
    x[: len(tt)] += shower(dur, 260, seed + 3, 2000, 6500, 'swell')[: len(tt)] * 1.3
    return fade(norm(x, 0.85), 0.05, 0.3)

def sparkle(seed=5, base=2093):
    """a magical twinkle: four high bell notes rising fast"""
    out = np.zeros(int(1.2 * SR))
    for k, m in enumerate([1, 1.26, 1.5, 2.0]):
        tt = t_(0.9); f = base * m
        b = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * f * 2.76 * tt)) * np.exp(-tt * 6)
        place_into(out, b, k * 0.06, 0.8 - k * 0.12)
    return norm(out, 0.4)

def ting(f=3300, seed=6):
    """the final coin catching the light (and the lens)"""
    tt = t_(1.4)
    x = (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * f * 2.76 * tt) + 0.2 * np.sin(2 * np.pi * f * 5.4 * tt)) * np.exp(-tt * 3.2)
    return norm(x * (1 + 0.3 * np.sin(2 * np.pi * 7 * tt)), 0.55)

# ------------------------------------------------------------- caravan ---
def camel_bell(seed=7, f0=None):
    r = np.random.default_rng(seed); f0 = f0 or 900 + 300 * r.random(); tt = t_(1.0)
    x = sum(a * np.sin(2 * np.pi * f0 * m * tt + r.random() * 6) * np.exp(-tt * d) for m, a, d in [(1, 1, 3.5), (2.4, 0.5, 5), (4.1, 0.3, 8), (5.6, 0.15, 12)])
    clap_ = hp(noise(1.0, seed), 3000) * np.exp(-tt * 300) * 0.3
    return fade(norm(x + clap_, 0.4), 0.001, 0.1)

def bells_walk(dur, rate=1.6, seed=8):
    """bells swinging on a walking camel: two strikes per swing, slightly irregular"""
    out = np.zeros(int((dur + 1) * SR)); r = np.random.default_rng(seed); t = r.random() * 0.3; k = 0
    while t < dur:
        place_into(out, camel_bell(seed * 100 + k, 950 + 150 * (k % 3)), t, 0.6 + 0.4 * r.random())
        t += (1 / rate) * (0.45 if k % 2 == 0 else 0.55) * (0.9 + 0.2 * r.random()); k += 1
    return norm(out[: int(dur * SR)], 0.45)

def hoof(seed=9):
    tt = t_(0.2)
    return norm(lp(noise(0.2, seed), 300) * np.exp(-tt * 40) + bp(noise(0.2, seed + 1), 600, 2500) * np.exp(-tt * 70) * 0.3, 0.5)

def camel_grunt(dur=0.8, seed=10, pitch=1.0):
    """a camel's bubbly grumble: low pulsed voice through a nasal formant, a little gargle"""
    tt = t_(dur); r = np.random.default_rng(seed)
    f0 = 85 * pitch * (1 + 0.25 * np.sin(np.pi * tt / dur)) * (1 + 0.04 * lp(r.standard_normal(len(tt)), 15) * 20)
    src = signal.sawtooth(2 * np.pi * np.cumsum(f0) / SR)
    gurgle = 0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 23 * tt + 3 * np.sin(2 * np.pi * 3 * tt)))
    x = (bp(src, 250, 900) + bp(src, 1100, 1700) * 0.4) * gurgle
    return fade(norm(x * np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 0.6, 0.6), 0.03, 0.12)

def desert_wind(dur, seed=11):
    tt = t_(dur)
    gust = 0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * tt + 1) * np.sin(2 * np.pi * 0.07 * tt)
    x = lp(noise(dur, seed), 700) * (0.5 + 0.5 * gust) + bp(noise(dur, seed + 1), 2500, 6000) * 0.08 * gust
    return norm(x, 0.3)

# ---------------------------------------------------------------- people ---
def cheer(dur=1.6, voices=16, seed=12, kids=False):
    """a crowd whooping: rising 'hey/ooh' vowels on many voices, some claps"""
    tt = t_(dur); out = np.zeros(len(tt)); r = np.random.default_rng(seed)
    for v in range(voices):
        base = (260 if kids else 150) + (140 if kids else 110) * r.random()
        st = r.random() * 0.25; ln = 0.5 + 0.6 * r.random()
        seg = (tt >= st) & (tt < st + ln); u = np.clip((tt - st) / ln, 0, 1)
        f0 = base * (1 + 0.35 * np.sin(np.pi * u) + 0.02 * np.sin(2 * np.pi * 6 * tt))
        src = signal.sawtooth(2 * np.pi * np.cumsum(f0) / SR)
        x = bp(src, 600 + 300 * r.random(), 1300 + 400 * r.random()) + bp(src, 2400, 3300) * 0.35
        out += x * seg * np.sin(np.pi * u) ** 0.5 * (0.4 + 0.6 * r.random())
    out = norm(out, 0.5)
    return fade(norm(out + murmur(dur, 10, seed + 50, 0.15)[: len(out)], 0.55), 0.03, 0.25)

def laugh(dur=1.6, voices=4, seed=13, high=False):
    """a group belly laugh: 'ha-ha-ha' bursts on a few voices"""
    tt = t_(dur); out = np.zeros(len(tt)); r = np.random.default_rng(seed)
    for v in range(voices):
        f0 = (170 if not high else 260) + 70 * r.random()
        rate = 4.2 + 1.5 * r.random(); ph = r.random() * 6
        gate = np.clip(np.sin(2 * np.pi * rate * tt + ph), 0, 1) ** 1.5 * np.clip(1.2 - tt / dur, 0, 1)
        fz = f0 * (1 - 0.15 * tt / dur) * (1 + 0.05 * np.sin(2 * np.pi * rate * tt + ph))
        src = signal.sawtooth(2 * np.pi * np.cumsum(fz) / SR) + 0.3 * noise(dur, seed + v)
        x = bp(src, 650 + 150 * r.random(), 1250 + 200 * r.random()) + bp(src, 2300, 3000) * 0.25
        out += x * gate * (0.6 + 0.4 * r.random())
    return fade(norm(out, 0.55), 0.02, 0.2)

def market_bed(dur, seed=14):
    """a busy market: chatter, distant calls, a cart, a donkey's bell"""
    x = murmur(dur, 18, seed, 0.35) + lp(noise(dur, seed + 1), 300) * 0.2
    r = np.random.default_rng(seed); out = x.copy()
    for k in range(int(dur / 2.5)):
        place_into(out, camel_bell(seed + k, 1500 + 400 * r.random()) * 0.25, r.random() * (dur - 1))
    return norm(out, 0.3)

# ------------------------------------------------------------------ comedy ---
def record_scratch(seed=15):
    """vinyl scratch: a short chord dragged back and forth under the needle"""
    dur = 0.42; tt = t_(dur)
    speed = np.concatenate([np.linspace(1, -1.6, int(0.13 * SR)), np.linspace(-1.6, 1.4, int(0.12 * SR)), np.linspace(1.4, 0, int(0.17 * SR))])[: len(tt)]
    pos = np.cumsum(speed) / SR
    src = sum(np.sin(2 * np.pi * f * pos * 4) for f in [220, 277, 330, 440]) + 0.6 * signal.sawtooth(2 * np.pi * 180 * pos * 4)
    hiss = bp(noise(dur, seed), 1200, 6000) * np.abs(speed) * 0.5
    x = bp(src, 300, 5000) * np.abs(speed) ** 0.7 + hiss
    return fade(norm(x, 0.7), 0.002, 0.03)

def chalk(dur=0.4, seed=16):
    tt = t_(dur); r = np.random.default_rng(seed)
    f = 2600 + 700 * np.sin(2 * np.pi * 3 * tt) + 200 * lp(r.standard_normal(len(tt)), 40) * 30
    squeak = np.sin(2 * np.pi * np.cumsum(f) / SR) * (np.sin(2 * np.pi * 37 * tt) > -0.2)
    grit = bp(noise(dur, seed), 2500, 9000) * 0.6
    return fade(norm((squeak * 0.4 + grit) * np.sin(np.pi * tt / dur) ** 0.4, 0.4), 0.01, 0.05)

def broom(dur=0.42, seed=17):
    tt = t_(dur)
    x = bp(noise(dur, seed), 900, 7000) * np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 0.8
    return fade(norm(x, 0.5), 0.01, 0.05)

def pop(f0=500, f1=1100, dur=0.09):
    tt = t_(dur)
    return fade(norm(np.sin(2 * np.pi * np.cumsum(np.linspace(f0, f1, len(tt))) / SR) * np.exp(-tt * 30), 0.5), 0.001, 0.02)

def boing(dur=0.5, f0=180):
    tt = t_(dur)
    f = f0 * (1 + 0.5 * np.exp(-tt * 6) * np.sin(2 * np.pi * 12 * tt))
    return fade(norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 5), 0.5), 0.002, 0.05)

def gulp():
    tt = t_(0.25)
    f = 300 * np.exp(-tt * 6) + 120
    return fade(norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / 0.25), 0.5), 0.005, 0.03)

def scale_creak(dur=0.35, seed=18):
    tt = t_(dur)
    f = 900 + 300 * np.sin(2 * np.pi * 2 * tt)
    x = bp(signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * (np.sin(2 * np.pi * 31 * tt) > 0.2), 800, 4000)
    return fade(norm(x * np.sin(np.pi * tt / dur), 0.3), 0.01, 0.05)

# ----------------------------------------------------------------- night ---
def moth(dur=1.3, seed=19):
    tt = t_(dur)
    flap = (0.5 + 0.5 * np.sin(2 * np.pi * 26 * tt)) ** 3
    x = bp(noise(dur, seed), 200, 1800) * flap * (0.6 + 0.4 * np.sin(np.pi * tt / dur))
    return fade(norm(x, 0.5), 0.02, 0.15)

def crickets(dur, seed=20):
    tt = t_(dur); out = np.zeros(len(tt)); r = np.random.default_rng(seed)
    for k in range(4):
        f = 4200 + 900 * r.random(); rate = 1.6 + r.random()
        gate = (np.sin(2 * np.pi * rate * tt + 6 * r.random()) > 0.55).astype(float) * (np.sin(2 * np.pi * 42 * tt) > 0).astype(float)
        out += np.sin(2 * np.pi * f * tt) * lp(gate, 300) * (0.5 + 0.5 * r.random())
    return norm(out, 0.2)

def fire(dur, seed=21):
    tt = t_(dur); r = np.random.default_rng(seed)
    x = lp(noise(dur, seed), 400) * 0.5 * (0.7 + 0.3 * np.sin(2 * np.pi * 0.5 * tt))
    for _ in range(int(dur * 9)):
        t = r.random() * (dur - 0.05); c = hp(noise(0.03, int(t * 1000)), 1500) * np.exp(-t_(0.03) * 200) * (0.3 + r.random())
        i = int(t * SR); x[i:i + len(c)] += c
    return norm(x, 0.35)

def hollow_knock(seed=22):
    tt = t_(0.5)
    x = (np.sin(2 * np.pi * 180 * tt) + 0.5 * np.sin(2 * np.pi * 410 * tt)) * np.exp(-tt * 14) + lp(noise(0.5, seed), 900) * np.exp(-tt * 40)
    return norm(x, 0.5)
