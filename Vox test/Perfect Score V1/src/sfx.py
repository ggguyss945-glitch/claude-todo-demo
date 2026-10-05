"""Procedural sound effects (numpy only). Every sound is synthesised from noise,
oscillators and filters; nothing is sampled. All functions return mono float32
at SR, roughly normalised so 1.0 ~ full scale."""
import numpy as np
from scipy import signal

SR = 48000
rng = np.random.default_rng(7)

def t_(dur): return np.arange(int(dur * SR)) / SR
def noise(dur, seed=None):
    r = np.random.default_rng(seed) if seed is not None else rng
    return r.standard_normal(int(dur * SR)).astype(np.float32)
def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype='band', fs=SR, output='sos'); return signal.sosfilt(sos, x)
def lp(x, f, order=2):
    sos = signal.butter(order, f, btype='low', fs=SR, output='sos'); return signal.sosfilt(sos, x)
def hp(x, f, order=2):
    sos = signal.butter(order, f, btype='high', fs=SR, output='sos'); return signal.sosfilt(sos, x)
def env_ad(n, a, d, curve=4.0):
    a_n = max(1, int(a * SR)); e = np.ones(n)
    e[:a_n] = np.linspace(0, 1, a_n)
    tt = np.arange(n - a_n) / SR
    e[a_n:] = np.exp(-tt / max(d, 1e-3) * curve / 4)
    return e
def fade(x, fi=0.005, fo=0.02):
    n = len(x); a = min(n, int(fi * SR)); b = min(n, int(fo * SR))
    if a: x[:a] *= np.linspace(0, 1, a)
    if b: x[-b:] *= np.linspace(1, 0, b)
    return x
def norm(x, peak=0.9):
    m = np.max(np.abs(x)) + 1e-9; return (x / m * peak).astype(np.float32)

# ------------------------------------------------------------------ foley ---
def footstep(kind='shoe', weight=1.0, seed=0):
    """heel + toe: low thump and a hard click; 'hall' is a hard floor with sharper click"""
    r = np.random.default_rng(seed)
    n = int(0.18 * SR)
    thump = lp(noise(0.18, seed), 180 + 60 * r.random()) * env_ad(n, 0.002, 0.03) * 2.2
    click = bp(noise(0.18, seed + 1), 1800, 5200) * env_ad(n, 0.0005, 0.012) * (1.2 if kind == 'hall' else 0.6)
    toe = np.zeros(n); k = int((0.05 + 0.02 * r.random()) * SR)
    toe[k:] = (bp(noise(0.18, seed + 2), 900, 3500) * env_ad(n, 0.001, 0.02))[: n - k] * 0.45
    return norm(thump + click + toe, 0.8 * weight)

def paper_rustle(dur=0.4, seed=1, bright=1.0):
    x = bp(noise(dur, seed), 1500, 9000) * (0.4 + 0.6 * np.abs(signal.sosfilt(signal.butter(2, 18, fs=SR, output='sos'), noise(dur, seed + 3))) * 6)
    return fade(norm(x * env_ad(len(x), 0.02, dur * 0.6), 0.6 * bright), 0.01, 0.08)

def paper_slap(seed=2, size=1.0):
    """a sheet landing flat on a desk: air puff + soft slap"""
    n = int(0.25 * SR)
    puff = lp(noise(0.25, seed), 900) * env_ad(n, 0.003, 0.05) * 1.2
    slap = bp(noise(0.25, seed + 1), 600, 4000) * env_ad(n, 0.001, 0.025)
    return norm(puff + slap, 0.7 * size)

def scribble(dur, speed=None, seed=3, kind='pencil'):
    """pencil (graphite grain) or marker (felt squeak) writing, modulated by stroke speed"""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    if speed is None: speed = np.ones(n)
    if kind == 'pencil':
        grain = bp(noise(dur, seed), 2500, 9000)
        mod = 0.55 + 0.45 * np.sin(2 * np.pi * (11 + 4 * np.sin(tt * 3)) * tt) ** 2
        x = grain * mod * speed
    else:  # marker: squeaky band-limited noise with a resonant whistle that follows speed
        base = bp(noise(dur, seed), 1200, 6000) * 0.7
        f = 1800 + 900 * speed
        ph = 2 * np.pi * np.cumsum(f) / SR
        squeak = np.sin(ph) * (0.25 + 0.2 * np.sin(tt * 37)) * speed
        x = (base + squeak) * speed
    return fade(x.astype(np.float32), 0.004, 0.02)

def thud(freq=60, dur=0.5, seed=4, click=0.5):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = freq * (1 + 1.5 * np.exp(-tt * 30))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9)
    knock = bp(noise(dur, seed), 300, 2500) * np.exp(-tt * 60) * click
    return norm(body + knock, 0.9)

def stack_slam(seed=5):
    a = thud(52, 0.8, seed, click=1.0)
    b = paper_slap(seed + 1, 1.3)
    out = np.zeros(int(0.8 * SR)); out[:len(a)] += a; out[:len(b)] += b * 0.9
    return norm(out, 0.95)

def stamp_slam(seed=6):
    n = int(0.6 * SR); tt = np.arange(n) / SR
    wood = np.sin(2 * np.pi * 180 * tt) * np.exp(-tt * 40) * 0.6
    smack = bp(noise(0.6, seed), 400, 6000) * np.exp(-tt * 45)
    low = thud(70, 0.6, seed + 1, 0.3) * 0.8
    return norm(wood + smack + low[:n], 0.95)

def whoosh(dur=0.45, up=True, seed=8, lo=300, hi=5000, strength=1.0):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = noise(dur, seed)
    # sweep a band-pass by filtering in short blocks
    out = np.zeros(n); blk = 512
    for i in range(0, n, blk):
        k = i / n
        k = k if up else 1 - k
        c = lo * (hi / lo) ** k
        sos = signal.butter(2, [max(40, c * 0.6), min(SR / 2 - 100, c * 1.6)], btype='band', fs=SR, output='sos')
        out[i:i + blk] = signal.sosfilt(sos, x[i:i + blk])
    e = np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 1.5
    return fade(norm(out * e, 0.7 * strength), 0.01, 0.05)

def riser(dur=2.0, seed=9):
    n = int(dur * SR); tt = np.arange(n) / SR
    w = whoosh(dur, True, seed, 200, 9000, 1.0)
    f = 120 * 2 ** (tt / dur * 3)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3 * (tt / dur) ** 2
    return norm((w + tone) * (tt / dur) ** 1.5, 0.8)

def sub_boom(dur=1.4, f0=48):
    tt = t_(dur)
    f = f0 * (1 + 0.6 * np.exp(-tt * 8))
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 2.6), 0.95)

def reverse_swell(dur=1.0, seed=10):
    x = hp(noise(dur, seed), 2000) * (t_(dur) / dur) ** 3
    return fade(norm(x, 0.6), 0.01, 0.01)

def clock_tick(seed=11, tock=False):
    n = int(0.06 * SR); tt = np.arange(n) / SR
    f = 3200 if not tock else 2500
    x = (np.sin(2 * np.pi * f * tt) * 0.5 + bp(noise(0.06, seed), 2000, 8000)) * np.exp(-tt * 180)
    return norm(x, 0.5)

def mug_clink(seed=12):
    tt = t_(0.5)
    x = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * d) * a for f, d, a in [(2350, 9, 0.5), (3870, 12, 0.3), (5600, 16, 0.2)])
    x += bp(noise(0.5, seed), 2000, 7000) * np.exp(-tt * 80) * 0.4
    return norm(x, 0.5)

def sip(dur=0.35, seed=13):
    x = bp(noise(dur, seed), 900, 3000) * np.sin(np.pi * t_(dur) / dur) ** 2
    return norm(x, 0.35)

def pen_drop(seed=14):
    """plastic pen hitting a desk and bouncing twice"""
    out = np.zeros(int(0.7 * SR))
    for k, (dt, a) in enumerate([(0.0, 1.0), (0.13, 0.55), (0.22, 0.3), (0.27, 0.15)]):
        tt = t_(0.08)
        h = (np.sin(2 * np.pi * 1450 * tt) * 0.4 + bp(noise(0.08, seed + k), 1500, 7000)) * np.exp(-tt * 70) * a
        i = int(dt * SR); out[i:i + len(h)] += h
    return norm(out, 0.6)

def chair_roll(dur=0.5, seed=15):
    tt = t_(dur)
    x = lp(noise(dur, seed), 600) * (0.6 + 0.4 * np.sin(2 * np.pi * 23 * tt)) * np.exp(-tt * 3)
    return fade(norm(x, 0.5), 0.01, 0.1)

def scrape(dur, speed, seed=16):
    """desk legs dragged on vinyl: low rumble + chattering squeak, follows speed"""
    tt = t_(dur); n = len(tt)
    rumble = lp(noise(dur, seed), 350) * 1.5
    chat = bp(noise(dur, seed + 1), 600, 2200) * (0.5 + 0.5 * np.sin(2 * np.pi * (31 + 9 * np.sin(tt * 2)) * tt) ** 8)
    sq = np.sin(2 * np.pi * np.cumsum(700 + 300 * speed) / SR) * 0.12
    return fade(((rumble + chat + sq) * speed).astype(np.float32), 0.02, 0.06)

def zipper(dur=0.35, seed=17):
    tt = t_(dur)
    teeth = (np.sin(2 * np.pi * np.cumsum(90 + 140 * tt / dur) / SR) > 0.6).astype(float)
    x = bp(noise(dur, seed), 1500, 7000) * (0.3 + teeth) * np.sin(np.pi * tt / dur)
    return norm(x, 0.5)

def peel(dur=1.0, seed=18):
    """sticky label peeling: crackly tearing"""
    tt = t_(dur); n = len(tt)
    r = np.random.default_rng(seed)
    clicks = np.zeros(n); idx = r.integers(0, n, 900); clicks[idx] = r.standard_normal(900)
    x = bp(clicks, 1500, 9000) * 6 + bp(noise(dur, seed), 3000, 9000) * 0.3
    return fade(norm(x * (0.4 + 0.6 * np.sin(np.pi * tt / dur)), 0.45), 0.02, 0.05)

def crinkle(dur=0.4, seed=19):
    return peel(dur, seed) * 0.8

def tape_rewind(dur=1.5, seed=20):
    tt = t_(dur)
    f = 900 + 700 * np.sin(2 * np.pi * 1.6 * tt) ** 2
    chirp = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.15
    hiss = bp(noise(dur, seed), 2000, 8000) * 0.25
    flutter = (np.sin(2 * np.pi * 14 * tt) > 0).astype(float) * 0.5 + 0.5
    return fade(norm((chirp + hiss) * flutter, 0.4), 0.02, 0.1)

def beep(f=1200, dur=0.08):
    tt = t_(dur); return fade(norm(np.sign(np.sin(2 * np.pi * f * tt)) * 0.3 + np.sin(2 * np.pi * f * tt), 0.35), 0.002, 0.01)

def error_buzz(dur=0.25):
    tt = t_(dur); x = np.sign(np.sin(2 * np.pi * 140 * tt)) * 0.6 + np.sin(2 * np.pi * 280 * tt) * 0.4
    return fade(norm(lp(x, 2500), 0.4), 0.003, 0.03)

def keyclicks(dur, rate=12, seed=21):
    out = np.zeros(int(dur * SR)); r = np.random.default_rng(seed)
    t = 0.0
    while t < dur - 0.03:
        c = bp(noise(0.03, int(t * 1000) + seed), 2000, 8000) * np.exp(-t_(0.03) * 200)
        i = int(t * SR); out[i:i + len(c)] += c * (0.5 + 0.5 * r.random())
        t += (1 / rate) * (0.6 + 0.8 * r.random())
    return norm(out, 0.35)

def phone_buzz(dur=0.42, seed=22):
    tt = t_(dur)
    x = np.sin(2 * np.pi * 165 * tt) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 330 * tt))) + bp(noise(dur, seed), 2000, 5000) * 0.3
    x *= (0.6 + 0.4 * np.sin(2 * np.pi * 24 * tt) ** 2)
    return fade(norm(lp(x, 4000), 0.55), 0.01, 0.03)

def ringtone(dur=1.4):
    """a simple marimba-ish ring melody"""
    out = np.zeros(int(dur * SR))
    notes = [(0.0, 784), (0.12, 988), (0.24, 1175), (0.36, 988), (0.7, 784), (0.82, 988), (0.94, 1175), (1.06, 988)]
    for t0, f in notes:
        tt = t_(0.3)
        n = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 4 * tt)) * np.exp(-tt * 14)
        i = int(t0 * SR)
        if i >= len(out): continue
        m = min(len(n), len(out) - i); out[i:i + m] += n[:m]
    return norm(out, 0.4)

def muffled_voice(dur=1.2, seed=23):
    """tiny voice leaking from a phone: band-limited babble"""
    tt = t_(dur)
    f0 = 140 + 30 * np.sin(2 * np.pi * 2.3 * tt) + 20 * np.sin(2 * np.pi * 5.1 * tt)
    src = signal.sawtooth(2 * np.pi * np.cumsum(f0) / SR)
    syl = (np.sin(2 * np.pi * 4.2 * tt) > -0.2).astype(float)
    x = bp(src, 700, 2600) * syl
    return fade(norm(lp(x, 2800), 0.25), 0.03, 0.08)

def cloth(dur=0.3, seed=24):
    return fade(norm(bp(noise(dur, seed), 400, 3000) * np.sin(np.pi * t_(dur) / dur), 0.3), 0.01, 0.05)

def door_creak(dur=0.7, seed=25):
    tt = t_(dur)
    f = 260 + 120 * np.sin(2 * np.pi * 0.9 * tt) + 40 * np.sin(2 * np.pi * 7 * tt)
    stick = (np.sin(2 * np.pi * np.cumsum(f / 6) / SR) > 0.3).astype(float)
    x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * (0.4 + 0.6 * stick)
    x = bp(x, 300, 3000)
    return fade(norm(x * np.sin(np.pi * tt / dur) ** 0.5, 0.35), 0.02, 0.1)

def latch(seed=26):
    tt = t_(0.15)
    x = (np.sin(2 * np.pi * 2100 * tt) * 0.4 + bp(noise(0.15, seed), 1500, 7000)) * np.exp(-tt * 90)
    return norm(x, 0.6)

def heartbeat():
    out = np.zeros(int(0.9 * SR))
    for dt, a in [(0.0, 1.0), (0.22, 0.7)]:
        b = thud(45, 0.4, 27, 0.05) * a; i = int(dt * SR); out[i:i + len(b)] += b
    return norm(lp(out, 150), 0.9)

def clap(seed=28):
    tt = t_(0.12)
    return norm(bp(noise(0.12, seed), 800, 5000) * np.exp(-tt * 55), 0.6)

def applause(dur=1.2, n=4, seed=29):
    out = np.zeros(int(dur * SR)); r = np.random.default_rng(seed)
    for k in range(n):
        t = r.random() * 0.15
        while t < dur - 0.15:
            c = clap(seed + int(t * 100) + k * 7) * (0.5 + 0.5 * r.random())
            i = int(t * SR); out[i:i + len(c)] += c
            t += 0.21 + r.random() * 0.06
    return fade(norm(out, 0.5), 0.05, 0.2)

def notification():
    tt = t_(0.4)
    x = np.sin(2 * np.pi * 1568 * tt) * np.exp(-tt * 9) + np.sin(2 * np.pi * 2093 * np.maximum(tt - 0.09, 0)) * np.exp(-np.maximum(tt - 0.09, 0) * 9) * (tt > 0.09)
    return norm(x, 0.3)

def frame_knock(seed=30):
    return norm(thud(220, 0.25, seed, 0.8), 0.5)

def groan(dur=0.9, voices=10, seed=31):
    """a classroom 'awww': formant-shaped buzz voices with falling pitch"""
    tt = t_(dur); out = np.zeros(len(tt)); r = np.random.default_rng(seed)
    for v in range(voices):
        f0 = (210 + 90 * r.random()) * (1 - 0.18 * tt / dur)
        src = signal.sawtooth(2 * np.pi * np.cumsum(f0 * (1 + 0.01 * np.sin(2 * np.pi * (5 + r.random()) * tt))) / SR)
        x = bp(src, 500 + 200 * r.random(), 1300 + 300 * r.random()) + bp(src, 2300, 3200) * 0.3
        d = int(r.random() * 0.08 * SR)
        out[d:] += x[:len(out) - d] * (0.6 + 0.4 * r.random())
    e = np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 0.7
    return fade(norm(out * e, 0.5), 0.05, 0.2)

def murmur(dur, voices=14, seed=32, level=0.3):
    """indistinct crowd chatter for ambience"""
    tt = t_(dur); out = np.zeros(len(tt)); r = np.random.default_rng(seed)
    for v in range(voices):
        f0 = (110 + 160 * r.random()) * (1 + 0.15 * np.sin(2 * np.pi * (0.7 + r.random()) * tt + r.random() * 6))
        src = signal.sawtooth(2 * np.pi * np.cumsum(f0) / SR)
        syl = (np.sin(2 * np.pi * (3 + 2 * r.random()) * tt + r.random() * 6) > 0.1 * r.random()).astype(float)
        syl = lp(syl, 20)
        x = bp(src, 400 + 300 * r.random(), 1800 + 600 * r.random()) * syl
        out += x * (0.3 + 0.7 * r.random())
    return norm(lp(out, 3000), level)

def room_tone(dur, kind='class', seed=33):
    tt = t_(dur)
    if kind == 'class':
        hum = lp(noise(dur, seed), 220) * 0.5 + np.sin(2 * np.pi * 120 * tt) * 0.02
        birds = np.zeros(len(tt)); r = np.random.default_rng(seed)
        for _ in range(int(dur * 0.8)):
            t0 = r.random() * (dur - 0.4); f = 3000 + 1500 * r.random()
            b = np.sin(2 * np.pi * np.cumsum(f + 600 * np.sin(2 * np.pi * 18 * t_(0.25))) / SR) * np.sin(np.pi * t_(0.25) / 0.25) * 0.08
            i = int(t0 * SR); birds[i:i + len(b)] += b
        x = hum + birds
    elif kind == 'hall':
        x = lp(noise(dur, seed), 400) * 0.6 + murmur(dur, 10, seed + 1, 0.25)
    elif kind == 'office':
        x = lp(noise(dur, seed), 180) * 0.4 + np.sin(2 * np.pi * 60 * tt) * 0.01
    elif kind == 'home':
        x = lp(noise(dur, seed), 300) * 0.3 + bp(noise(dur, seed + 1), 300, 1200) * 0.05 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * tt))
    else:  # night: crickets + far traffic
        cr = np.zeros(len(tt))
        for k, f in enumerate([4300, 4700, 5100]):
            gate = (np.sin(2 * np.pi * (2.2 + 0.3 * k) * tt + k) > 0.3).astype(float) * (np.sin(2 * np.pi * 38 * tt) > 0).astype(float)
            cr += np.sin(2 * np.pi * f * tt) * lp(gate, 200) * 0.05
        x = cr + lp(noise(dur, seed), 200) * 0.3
    return norm(x.astype(np.float32), 0.25)
