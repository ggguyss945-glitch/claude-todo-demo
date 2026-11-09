"""EP01 "Never Move Grandpa": procedural sound designs (the SFX the owner's Epidemic library does not have).

Every design is a pure function of its arguments and a string seed (numpy default_rng seeded by crc32), so the
same call always returns the same samples. Output: float64 arrays at 48 kHz, shape (n, 2), peak-normalised to
-1 dBFS (the catalog sets the final level by loudness, see catalog.py). Designs that need a recorded layer take
it from the extracted Epidemic files through `Lib` (read as data only, decoded by ffmpeg).

Run `python3 -I synth.py [out_dir] [name ...]` to write every design (or the named ones) as 24-bit WAVs.
"""
import os, sys, zlib, subprocess
import numpy as np
from scipy.signal import butter, sosfilt, sosfiltfilt, fftconvolve, resample_poly

SR = 48000
SCRATCH = os.environ.get('EP01_SOUND_SCRATCH',
                         '/tmp/claude-0/-home-user-claude-todo-demo/353ac1d9-152b-55bb-bdf1-0625e0fc6a83/scratchpad/rbx/ep01/sound')


# ----------------------------------------------------------------------------------------------- basics
def rng(seed):
    return np.random.default_rng(zlib.crc32(str(seed).encode()))


def n_(dur):
    return max(1, int(round(dur * SR)))


def tt(dur):
    return np.arange(n_(dur)) / SR


def db(x):
    return 10 ** (x / 20)


def _sos(kind, f, order=2):
    if kind == 'bp':
        lo, hi = f
        hi = min(hi, SR / 2 * 0.95)
        return butter(order, [lo, hi], 'bandpass', fs=SR, output='sos')
    f = min(f, SR / 2 * 0.95)
    return butter(order, f, 'lowpass' if kind == 'lp' else 'highpass', fs=SR, output='sos')


def lp(x, f, order=2):
    return sosfilt(_sos('lp', f, order), x, axis=0)


def hp(x, f, order=2):
    return sosfilt(_sos('hp', f, order), x, axis=0)


def bp(x, lo, hi, order=2):
    return sosfilt(_sos('bp', (lo, hi), order), x, axis=0)


def peak_bp(x, f, q):
    """RBJ constant-0-dB-peak band-pass biquad (a resonance) at f with quality q."""
    w = 2 * np.pi * f / SR
    al = np.sin(w) / (2 * q)
    b = np.array([al, 0, -al]); a = np.array([1 + al, -2 * np.cos(w), 1 - al])
    sos = np.concatenate([b / a[0], a / a[0]])[None, :]
    return sosfilt(sos, x, axis=0)


def tv_bp(x, fc, q=1.2, block=240):
    """Time-varying band-pass: fc is an array (Hz) per sample; coefficients change per 5 ms block (state carried)."""
    y = np.zeros_like(x); zi = np.zeros((1, 2))
    for i in range(0, len(x), block):
        f = float(np.clip(fc[min(i + block // 2, len(fc) - 1)], 30, SR * 0.45))
        w = 2 * np.pi * f / SR; al = np.sin(w) / (2 * q)
        b = np.array([al, 0, -al]); a = np.array([1 + al, -2 * np.cos(w), 1 - al])
        sos = np.concatenate([b / a[0], a / a[0]])[None, :]
        y[i:i + block], zi = sosfilt(sos, x[i:i + block], zi=zi)
    return y


def tv_lp(x, fc, block=240):
    y = np.zeros_like(x); zi = np.zeros((1, 2))
    for i in range(0, len(x), block):
        f = float(np.clip(fc[min(i + block // 2, len(fc) - 1)], 30, SR * 0.45))
        sos = butter(2, f, 'lowpass', fs=SR, output='sos')
        y[i:i + block], zi = sosfilt(sos, x[i:i + block], zi=zi)
    return y


def white(n, r):
    return r.standard_normal(n)


def pink(n, r):
    """Pink noise (Voss-McCartney style via FFT shaping), unit RMS."""
    X = np.fft.rfft(r.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR); f[0] = f[1]
    X /= np.sqrt(f)
    y = np.fft.irfft(X, n)
    return y / (np.std(y) + 1e-12)


def brown(n, r):
    y = np.cumsum(r.standard_normal(n)); y = hp(y, 15)
    return y / (np.std(y) + 1e-12)


def smooth_noise(n, rate_hz, r):
    """Slow random control signal in [-1, 1] (cubic-interpolated random points at rate_hz)."""
    k = int(n / SR * rate_hz) + 4
    pts = r.uniform(-1, 1, k)
    x = np.linspace(0, k - 3, n)
    i = np.floor(x).astype(int); f = x - i
    p0, p1, p2, p3 = pts[i], pts[i + 1], pts[i + 2], pts[np.minimum(i + 3, k - 1)]
    return p1 + 0.5 * f * (p2 - p0 + f * (2 * p0 - 5 * p1 + 4 * p2 - p3 + f * (3 * (p1 - p2) + p3 - p0)))


def env_ad(n, att, dec, curve=1.0):
    """Attack (linear-ish, s) then exponential decay (time constant dec, s)."""
    t = np.arange(n) / SR
    a = np.clip(t / max(att, 1e-4), 0, 1) ** curve
    d = np.exp(-np.maximum(t - att, 0) / max(dec, 1e-4))
    return a * d


def fade(x, fin=0.002, fout=0.01):
    x = x.copy(); a, b = n_(fin), n_(fout)
    w = lambda k: 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, k))
    if a > 1: x[:a] *= w(a)[:, None] if x.ndim == 2 else w(a)
    if b > 1: x[-b:] *= w(b)[::-1][:, None] if x.ndim == 2 else w(b)[::-1]
    return x


def place(buf, x, t):
    """Add mono/stereo x into buf (stereo) at time t (s)."""
    i = int(round(t * SR))
    if x.ndim == 1: x = np.stack([x, x], 1)
    if i < 0: x = x[-i:]; i = 0
    j = min(len(buf), i + len(x))
    if j > i: buf[i:j] += x[:j - i]
    return buf


def addat(y, x, i, g=1.0):
    """y[i:] += g * x, clipped to y's length (i in samples)."""
    i = int(i)
    if i >= len(y) or i + len(x) <= 0: return y
    if i < 0: x = x[-i:]; i = 0
    m = min(len(x), len(y) - i); y[i:i + m] += g * x[:m]
    return y


def pan(x, p):
    """Constant-power pan of mono x, p in [-1 (L), 1 (R)]."""
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1)


def stereo(x, width=0.0, r=None, delay_ms=0.0):
    """Mono -> stereo; width>0 adds a decorrelated (Haas-free) side made from a 2-tap all-pass smear."""
    if x.ndim == 2: return x
    if width <= 0: return np.stack([x, x], 1)
    d = max(1, int(delay_ms * SR / 1000)) if delay_ms else 37
    s = np.zeros_like(x); s[d:] = x[:-d]; s = hp(s - np.roll(s, 11), 300)
    return np.stack([x + width * s, x - width * s], 1)


def norm(x, peak_db=-1.0):
    m = np.abs(x).max()
    return x * (db(peak_db) / m) if m > 0 else x


def to_st(x):
    return np.stack([x, x], 1) if x.ndim == 1 else x


def resample(x, ratio_num, ratio_den):
    """Pitch/time change by resampling (ratio num/den > 1 = slower/lower)."""
    return resample_poly(x, ratio_num, ratio_den, axis=0)


# ------------------------------------------------------------------------------------------- reverb
def ir(kind='night', seed='ir'):
    """Synthetic stereo impulse responses: 'night' (open garden, sparse early reflections off houses, RT60 ~0.7 s,
    dark), 'room' (small furnished bedroom, RT60 0.35 s), 'hall' (hallway, RT60 0.55 s, brighter)."""
    r = rng(seed + kind)
    rt, lpf, er = {'night': (0.7, 3500, [(0.019, .35), (0.043, .22), (0.071, .14)]),
                   'room': (0.35, 6000, [(0.004, .5), (0.009, .35), (0.013, .25), (0.021, .2)]),
                   'hall': (0.55, 7000, [(0.006, .45), (0.017, .3), (0.029, .22)])}[kind]
    n = n_(rt * 1.2); t = np.arange(n) / SR
    out = np.zeros((n, 2))
    for c in range(2):
        tail = r.standard_normal(n) * np.exp(-6.9 * t / rt) * np.clip(t / 0.008, 0, 1)
        tail = lp(tail, lpf * (0.85 + 0.3 * c))
        out[:, c] = tail * 0.25
        for d, g in er:
            k = int((d * (1 + 0.07 * (c - 0.5))) * SR)
            if k < n: out[k, c] += g * (0.8 + 0.4 * r.random())
    return out / np.sqrt((out ** 2).sum() / 2)


def verb(x, kind='night', wet=0.18, seed='v'):
    """Mix a dry signal with its convolution through ir(kind). wet = wet/dry amplitude ratio."""
    x = to_st(x)
    h = ir(kind, seed)
    y = np.stack([fftconvolve(x[:, c], h[:, c])[:len(x) + len(h) - 1] for c in range(2)], 1)
    out = np.zeros_like(y); out[:len(x)] += x
    return out + wet * y


# ------------------------------------------------------------------------------------- library layers
class Lib:
    """Read-only access to the extracted Epidemic Sound files (untrusted data: decoded by ffmpeg, never executed)."""
    def __init__(self, root=os.path.join(SCRATCH, 'sfx')):
        self.root = root; self.cache = {}

    def path(self, name):
        p = os.path.join(self.root, name if name.endswith('.mp3') else name + ' - Epidemic Sound.mp3')
        if not os.path.isfile(p): raise FileNotFoundError(p)
        return p

    def load(self, name, sr=SR):
        key = (name, sr)
        if key not in self.cache:
            raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', self.path(name), '-f', 'f32le', '-ac', '2', '-ar', str(sr), '-'],
                                 capture_output=True, check=True).stdout
            self.cache[key] = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
        return self.cache[key]

    def seg(self, name, a, b):
        x = self.load(name)
        return x[int(a * SR):int(b * SR)].copy()


LIB = Lib()
CEREAL = 'ES_Food & Drink, Ingredients, Cereal, Malted Wheats, Pour From Box Into Bowl'
CEREAL2 = 'ES_Food & Drink, Ingredients, Cereal, Malted Wheats, Pour Back Into Box'


def crumble(dur, seed, dark=2200, slow=1.25, lib=LIB):
    """Soil crumbling: the cereal-pour recording (granular crackle), pitched down (slow x) and low-passed so it reads
    as damp soil clods; a seeded window of the take, faded."""
    r = rng(seed)
    src = lib.load(CEREAL2 if r.random() < 0.5 else CEREAL)
    need = n_(dur / slow) + 10
    a = int(r.uniform(0.25, 1.4) * SR) if len(src) > need + int(1.6 * SR) else 0
    seg = src[a:a + need]
    seg = resample(seg, int(round(slow * 100)), 100)[:n_(dur)]
    seg = lp(hp(seg, 120), dark, 2)
    return fade(seg, 0.01, min(0.12, dur / 3))


# ------------------------------------------------------------------------------------------ modal hits
def modal(freqs, decays, amps, dur, r=None, detune=0.0, attack=0.0005, phase=None):
    t = tt(dur); y = np.zeros_like(t)
    for i, (f, d, a) in enumerate(zip(freqs, decays, amps)):
        f2 = f * (1 + (r.uniform(-detune, detune) if r is not None and detune else 0))
        ph = (r.uniform(0, 2 * np.pi) if r is not None else 0) if phase is None else phase
        y += a * np.exp(-t / d) * np.sin(2 * np.pi * f2 * t + ph)
    y *= np.clip(t / max(attack, 1e-5), 0, 1) * np.clip((dur - t) / 0.006, 0, 1)   # no truncation click
    return y


def click(dur=0.0006, hpf=2500, r=None):
    n = n_(dur); w = np.sin(np.linspace(0, np.pi, n)) ** 2
    if r is not None: w = w * (1 + 0.3 * r.standard_normal(n))
    return hp(np.concatenate([w, np.zeros(n_(0.004))]), hpf)


def tine(f, dur=1.2, seed='tine', amp=1.0, bright=1.0):
    """Music-box tine (clamped steel bar): fundamental + 6.27x and 17.55x bar modes decaying fast, a slow beat from a
    second slightly detuned fundamental, and the pluck-pin click. The bible's magic motif (AW tines 1.7-4 kHz)."""
    r = rng(seed)
    d1 = 0.9 * (1000 / f) ** 0.4
    y = modal([f, f * 1.0006 + 0.35, f * 6.27, f * 17.55, f * 2.0],
              [d1, d1 * 0.8, 0.06 * bright, 0.012 * bright, 0.15],
              [1.0, 0.18, 0.22 * bright, 0.07 * bright, 0.05], dur, r, attack=0.0008)
    c = click(0.0004, 3000, r)
    y[:len(c)] += 0.12 * bright * c[:len(y)]
    return amp * fade(y, 0.0, min(0.15, dur / 4))


NOTE = lambda name: 440.0 * 2 ** ((
    {'C': -9, 'C#': -8, 'D': -7, 'D#': -6, 'E': -5, 'F': -4, 'F#': -3, 'G': -2, 'G#': -1, 'A': 0, 'A#': 1, 'B': 2}[name[:-1]]
    + 12 * (int(name[-1]) - 4)) / 12)
PENTA = ['E6', 'F#6', 'G#6', 'B6', 'C#7', 'E7', 'F#7', 'G#7', 'B7']   # E major pentatonic: the episode's magic key


# ================================================================================ DESIGNS (the NEW sounds)
def tik(seed='tik', slow=False):
    """TIK: the gnome's painted-eyelid blink, a tiny dry porcelain 'tik' (2-frame decal swap) with a softer
    re-open click 34 ms later. slow=True -> TIK_SLOW (83.68 s, 'blinked slowly ... like he was sorry'): modes x0.78,
    longer ring, the re-open 0.17 s later and lower, the lids settling (a faint soft second contact)."""
    r = rng(seed + ('slow' if slow else ''))
    k = 0.78 if slow else 1.0; ring = 1.9 if slow else 1.0
    fr = np.array([1480, 2950, 4870, 7230, 9800]) * k
    dc = np.array([0.020, 0.030, 0.018, 0.012, 0.008]) * ring
    am = [0.35, 1.0, 0.6, 0.35, 0.18]
    dur = 0.45 if slow else 0.16
    y = np.zeros(n_(dur))
    hit1 = modal(fr, dc, am, 0.12 * ring, r, detune=0.015)
    c = click(0.0005, 2500, r); hit1[:len(c)] += 0.6 * c
    y[:len(hit1)] += hit1
    off = 0.17 if slow else 0.034
    hit2 = modal(fr * (0.94 if slow else 1.06), dc * 0.8, am, 0.1 * ring, r, detune=0.02) * (0.22 if slow else 0.3)
    i = n_(off); y[i:i + len(hit2)] += hit2[:len(y) - i]
    if slow:   # lids settling low: a faint soft porcelain brush after the re-open
        s = bp(white(n_(0.12), r), 2500, 6000) * env_ad(n_(0.12), 0.03, 0.03) * 0.05
        j = n_(0.25); y[j:j + len(s)] += s[:len(y) - j]
    y = fade(y, 0.0, 0.02)
    return norm(verb(y, 'night', 0.025, seed)[:n_(dur + 0.08)])


def ceramic_tok(seed='tok', soft=1.0):
    """TOK: a fingertip tap on the hollow ceramic hat (Dad, s16): dull hollow porcelain modes, soft excitation."""
    r = rng(seed)
    y = modal([820, 1960, 3340, 5100, 240], [0.032, 0.02, 0.012, 0.008, 0.025], [1, 0.55, 0.3, 0.12, 0.4], 0.25, r, detune=0.02,
              attack=0.0015)
    th = lp(white(n_(0.03), r), 900) * env_ad(n_(0.03), 0.001, 0.006) * 0.4 * soft
    y[:len(th)] += th
    return norm(fade(y, 0, 0.03))


def plink(seed='plink', f0=None, n=2, gap=0.045, bright=1.0):
    """PLINK / T_GLINT: light catching a bike reflector / a lens: a quick upward glint chirp into small glass partials,
    with a few tiny 9-12 kHz sparkle ticks. n pings gap s apart (two eyes), the second a fifth up."""
    r = rng(seed)
    f0 = f0 or r.uniform(4300, 5200)
    dur = 0.6 + gap * n
    y = np.zeros(n_(dur))
    for k in range(n):
        f = f0 * (1.5 if k % 2 else 1.0) * (1 + r.uniform(-0.02, 0.02))
        t = tt(0.5)
        chirp_f = f * (1 - 0.18 * np.exp(-t / 0.012))
        ph = 2 * np.pi * np.cumsum(chirp_f) / SR
        g = (np.sin(ph) * np.exp(-t / 0.085) + 0.35 * np.sin(2.32 * ph) * np.exp(-t / 0.045)
             + 0.15 * np.sin(4.25 * ph) * np.exp(-t / 0.02)) * np.clip(t / 0.002, 0, 1) * np.clip((0.5 - t) / 0.1, 0, 1)
        for s in range(3):
            j = n_(r.uniform(0.0, 0.08))
            sp = np.sin(2 * np.pi * r.uniform(9000, 12500) * tt(0.012)) * env_ad(n_(0.012), 0.001, 0.003) * 0.25 * bright
            g[j:j + len(sp)] += sp
        i = n_(k * gap); y[i:i + len(g)] += g * (1.0 if k == 0 else 0.8)
    y = fade(y, 0, 0.05)
    return norm(stereo(y, 0.35, r) if n > 1 else stereo(y, 0.2, r))


def reflector_flash(seed='flash'):
    """The 'reflectors' sweep (39.39 s): a short bright 'shing' (noise swept 3 -> 9 kHz) over a ping pair."""
    r = rng(seed)
    n = n_(0.5); t = np.arange(n) / SR
    sw = tv_bp(white(n, r), 3000 * 3 ** np.clip(t / 0.22, 0, 1), q=4) * env_ad(n, 0.05, 0.06)
    y = 0.4 * sw / (np.abs(sw).max() + 1e-9)
    p = plink(seed + 'p', f0=5600, n=2, gap=0.06)[:, 0]
    y[:len(p)] += 0.7 * p[:n] if len(p) >= n else 0
    return norm(stereo(fade(y, 0.001, 0.05), 0.4, r))


def lantern_light(seed='lantern', note='E6', big=1.0, sparkle=5):
    """TINK_WHOOSH: Grandpa's lantern lights (41.76 s, 3-frame light-up with overshoot): a soft ignition whoosh that
    swells 0.12 s into the flash (band-passed noise swept 600 -> 2.4 k -> 900 Hz), a warm 'fwmp' body under it, the
    lantern-glass tink (a music-box tine + octave), and a short sparkle tail of pentatonic tines.
    The clip starts 0.12 s BEFORE the light-up (lead 0.12)."""
    r = rng(seed)
    lead = 0.12; dur = 1.4
    n = n_(dur); t = np.arange(n) / SR - lead
    fc = np.where(t < 0.03, 600 * 4 ** np.clip((t + lead) / (lead + 0.03), 0, 1), 2400 * (900 / 2400) ** np.clip((t - 0.03) / 0.4, 0, 1))
    wenv = np.where(t < 0.02, np.clip((t + lead) / (lead + 0.02), 0, 1) ** 2, np.exp(-(t - 0.02) / 0.16))
    wh = tv_bp(pink(n, r), fc, q=1.1) * wenv
    wh /= (np.abs(wh).max() + 1e-9)
    y = 0.55 * big * wh
    i0 = n_(lead)
    body = (np.sin(2 * np.pi * np.cumsum(95 + 65 * np.exp(-tt(0.3) / 0.05)) / SR) * env_ad(n_(0.3), 0.004, 0.08)
            + 0.5 * lp(white(n_(0.3), r), 420) * env_ad(n_(0.3), 0.002, 0.04) / 3)
    y[i0:i0 + len(body)] += 0.35 * big * body
    f = NOTE(note)
    tk = tine(f, 1.2, seed + 't'); o = tine(2 * f, 0.8, seed + 'o'); tk[:len(o)] += 0.35 * o
    y[i0:i0 + len(tk)] += 0.55 * tk[:n - i0]
    for k in range(sparkle):
        j = i0 + n_(0.05 + 0.1 * k + r.uniform(0, 0.05))
        s = tine(NOTE(PENTA[r.integers(4, 9)]), 0.5, f'{seed}s{k}', bright=0.6) * (0.22 * 0.8 ** k)
        y[j:j + len(s)] += s[:n - j]
    y = fade(y, 0.002, 0.2)
    return norm(verb(stereo(y, 0.3, r), 'night', 0.12, seed)[:n + n_(0.3)])


def lantern_cascade(times, seed='cascade', near_last=True, far=8):
    """TINKS: 'Every lantern lit' down the street, toward the camera: one small tink-whoosh per lantern at the given
    episode times (first = farthest: darker, quieter, panned left; last = nearest: bright, centre) climbing the
    pentatonic scale, over a faint dense twinkle of `far` distant lanterns. Returns (clip, t_start)."""
    r = rng(seed)
    t0 = times[0] - 0.12; dur = times[-1] - t0 + 1.3
    y = np.zeros((n_(dur), 2))
    m = len(times)
    for k, t in enumerate(times):
        a = k / max(1, m - 1)
        one = lantern_light(f'{seed}{k}', note=PENTA[min(8, 1 + k)], big=0.45 + 0.4 * a, sparkle=2)
        one = lp(one, 3500 + 9000 * a) * db(-9 + 9 * a)
        one = one[:, 0] * 0.5 + one[:, 1] * 0.5
        place(y, pan(one, -0.55 + 0.55 * a), t - 0.12 - t0)
    span = times[-1] - times[0] + 0.3
    for k in range(far):
        s = tine(NOTE(PENTA[r.integers(3, 9)]), 0.6, f'{seed}f{k}', amp=0.12, bright=0.5)
        s = lp(s, 4000)
        place(y, pan(s, r.uniform(-0.9, 0.3)), 0.12 + r.uniform(0, span))
    return norm(verb(y, 'night', 0.15, seed)), t0


def rumble(dur, seed='rumble', sub=1.0, crackle=1.0, lumps=4.0, move=None):
    """Mound rumble (SUBBOOM tail, RUMBLE_ROLL, distant): brown-noise earth rumble under 160 Hz with random lumps,
    a wobbling 34-42 Hz sub, and sparse soil crackle. move=(p0, p1) pans it across over the duration."""
    r = rng(seed)
    n = n_(dur)
    e = lp(brown(n, r), 110, 4) * (0.6 + 0.4 * smooth_noise(n, lumps, r))
    e += 0.5 * bp(white(n, r), 60, 180) * (0.5 + 0.5 * smooth_noise(n, lumps * 1.7, r)) * 0.4
    f = 38 + 4 * smooth_noise(n, 0.8, r)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * sub * 0.5
    y = e / (np.abs(e).max() + 1e-9) + s
    if crackle:
        c = crumble(dur, seed + 'c', dark=1700)
        y = y + crackle * 0.22 * c[:, 0] * (0.4 + 0.6 * (smooth_noise(n, 2, r) > 0))
    if move:
        p = np.linspace(move[0], move[1], n); a = (p + 1) * np.pi / 4
        st = np.stack([y * np.cos(a), y * np.sin(a)], 1)
    else:
        r2 = rng(seed + 'R'); y2 = lp(brown(n, r2), 110, 4); y2 /= np.abs(y2).max() + 1e-9
        st = np.stack([y, 0.75 * y + 0.25 * (y2 + s)], 1)
    return norm(fade(st, 0.08, min(0.6, dur / 3)))


def squeak(f0, dur, seed, drop=0.8, vib=45, harm=5, breath=0.12):
    """One small rodent squeak: harmonic tone, up-then-down pitch contour, fast vibrato, breathy edge."""
    r = rng(seed)
    t = tt(dur); x = t / dur
    f = f0 * (1 + 0.15 * np.sin(np.pi * np.clip(x / 0.25, 0, 1)) * (x < 0.25) + (drop - 1) * np.clip((x - 0.2) / 0.8, 0, 1))
    f *= 1 + 0.03 * np.sin(2 * np.pi * vib * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = sum(np.sin(k * ph) / k ** 1.5 for k in range(1, harm + 1))
    y += breath * bp(white(len(t), r), f0 * 1.5, min(f0 * 3, 16000)) / 2
    return y * env_ad(len(t), min(0.006, dur / 5), dur / 3)


def chitter(dur, seed='chitter', rate=14, f0=3800):
    r = rng(seed); y = np.zeros(n_(dur)); t = 0.0; k = 0
    while t < dur - 0.03:
        s = squeak(f0 * r.uniform(0.8, 1.25), r.uniform(0.018, 0.032), f'{seed}{k}', drop=r.uniform(0.85, 1.05), harm=3)
        i = n_(t); y[i:i + len(s)] += s[:len(y) - i] * r.uniform(0.4, 1.0)
        t += 1 / rate * r.uniform(0.6, 1.4); k += 1
    return y * np.clip(np.linspace(2, 0, len(y)), 0, 1)


def fip(seed='fip'):
    """FIP: three snouts snap back at the ring edge (42.745 s): three quick recoiling squeaks 50-90 ms apart
    (falling pitch), each with a tiny wet flick, panned across."""
    r = rng(seed)
    y = np.zeros((n_(0.6), 2))
    t = 0.0
    for k, (f0, p) in enumerate(zip([3600, 3050, 4150], [-0.5, 0.45, 0.0])):
        s = squeak(f0, r.uniform(0.055, 0.075), f'{seed}{k}', drop=0.72)
        fl = bp(white(n_(0.02), r), 1500, 5000) * env_ad(n_(0.02), 0.001, 0.004) * 0.3
        s[:len(fl)] += fl
        place(y, pan(s, p), t); t += r.uniform(0.05, 0.09)
    return norm(verb(y, 'night', 0.1, seed))


def sniff(seed='sniff', size=1.0, n_sniffs=3, wriggle=0.35):
    """SNIFF: a star-nosed mole snout testing the air: 2-3 quick wet inhales (band-passed noise, band rising), a
    mucus 'tsk' + squelch, then a rubbery wriggle and a tiny chitter. size>1 = the big mole: lower, longer, a snort."""
    r = rng(seed)
    lo = 1.0 / size
    y = np.zeros(n_(0.25 * n_sniffs + wriggle + 0.4))
    t = 0.0
    for k in range(n_sniffs):
        d = r.uniform(0.07, 0.11) * size ** 0.5
        m = n_(d); tk = np.arange(m) / SR
        fc = (2200 + 1000 * tk / d) * lo
        s = tv_bp(pink(m, r), fc, q=1.6) * np.clip(tk / 0.015, 0, 1) * np.clip((d - tk) / 0.03, 0, 1)
        s /= np.abs(s).max() + 1e-9
        i = n_(t); y[i:i + m] += s * r.uniform(0.7, 1.0)
        t += d + r.uniform(0.04, 0.07)
    ts = n_(t - 0.02)
    tsk = modal([1400 * lo, 2600 * lo], [0.004, 0.003], [1, 0.5], 0.03, r)
    sq = bp(white(n_(0.06), r), 700 * lo, 1600 * lo) * (0.5 + 0.5 * np.sin(2 * np.pi * 95 * tt(0.06))) * env_ad(n_(0.06), 0.004, 0.02)
    y[ts:ts + len(tsk)] += 0.5 * tsk; y[ts + n_(0.01):ts + n_(0.01) + len(sq)] += 0.35 * sq / (np.abs(sq).max() + 1e-9)
    if wriggle:
        w0 = ts + n_(0.07); m = n_(wriggle)
        w = bp(pink(m, r), 300 * lo, 900 * lo) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * tt(wriggle))) * env_ad(m, 0.05, wriggle / 2)
        w /= np.abs(w).max() + 1e-9
        y[w0:w0 + m] += 0.3 * w[:len(y) - w0]
        c = chitter(wriggle * 0.8, seed + 'c', rate=13, f0=3800 * lo ** 0.5)
        y[w0:w0 + len(c)] += 0.18 * c[:len(y) - w0]
    if size > 1.2:   # the big one snorts
        sn = lp(white(n_(0.18), r), 900) * env_ad(n_(0.18), 0.01, 0.06)
        sn += 0.6 * np.sign(np.sin(2 * np.pi * 105 * tt(0.18))) * env_ad(n_(0.18), 0.01, 0.05) * 0.2
        y[:len(sn)] += 0.5 * sn / (np.abs(sn).max() + 1e-9)
    return norm(verb(stereo(fade(y, 0.002, 0.05), 0.25, r), 'night', 0.08, seed))


def gulp(seed='gulp'):
    """GULP (58.865 s, moleField.swallow): the turf lips rise with a wet slurp (0-0.12 s), close over the plastic gnome
    with a deep descending throat 'bloop' and a sub thump (0.12-0.35 s), then the seal settles and burps crumbs
    (0.38-0.5 s, in the gap before 'Gone'). Weight sits under 300 Hz, under the narrator's own 'Gulp'."""
    r = rng(seed)
    n = n_(0.9); y = np.zeros(n)
    sl = bp(pink(n_(0.13), r), 500, 1800) * (0.6 + 0.4 * np.sin(2 * np.pi * 70 * tt(0.13))) * env_ad(n_(0.13), 0.05, 0.05)
    y[:len(sl)] += 0.25 * sl / (np.abs(sl).max() + 1e-9)
    i = n_(0.10)
    gl = modal([1800, 640], [0.003, 0.012], [0.6, 1.0], 0.04, r)
    y[i:i + len(gl)] += 0.35 * gl
    i = n_(0.12); m = n_(0.32); t = np.arange(m) / SR
    f = 70 + 230 * np.exp(-t / 0.09)
    ph = 2 * np.pi * np.cumsum(f) / SR
    bl = (np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)) * env_ad(m, 0.008, 0.1)
    bl += 0.35 * bp(white(m, r), 140, 520) * env_ad(m, 0.006, 0.05)
    y[i:i + m] += 0.9 * bl
    i = n_(0.24)
    th = np.sin(2 * np.pi * np.cumsum(48 + 30 * np.exp(-tt(0.3) / 0.04)) / SR) * env_ad(n_(0.3), 0.003, 0.09)
    y[i:i + len(th)] += 0.8 * th
    c = crumble(0.5, seed + 'c', dark=1800)[:, 0]
    i = n_(0.18); y[i:i + len(c)] += 0.3 * c[:n - i]
    i = n_(0.39)
    bu = bp(pink(n_(0.09), r), 250, 1100) * env_ad(n_(0.09), 0.01, 0.03)
    y[i:i + len(bu)] += 0.3 * bu / (np.abs(bu).max() + 1e-9)
    c2 = crumble(0.18, seed + 'c2', dark=2400)[:, 0]
    y[i + n_(0.02):i + n_(0.02) + len(c2)] += 0.25 * c2[:n - i - n_(0.02)]
    return norm(verb(stereo(fade(y, 0.002, 0.1), 0.2, r), 'night', 0.08, seed))


def fwoom(seed='fwoom', second=1.06):
    """FWOOM (86.86 s, on the vowel; lantern 8 -> 50 cd in 0.15 s, grade to magic): a 0.28 s air swell into a warm
    combustion 'FWOOM' (low-mid burst + pitched-down sub thump + an airy band sweeping down), a warm shimmer: a fast
    E-major tine arpeggio, a twinkling 3-10 kHz grain cloud and a soft E3/B3 pad, ~1.8 s; plus the Epidemic 'Magic
    Spell, Bright' shimmer above 2 kHz. `second` s later the smaller pulse on 'flared' (87.92 s).
    The clip starts 0.28 s BEFORE the hit (lead 0.28)."""
    r = rng(seed)
    lead = 0.28; dur = lead + 2.7
    n = n_(dur); t = np.arange(n) / SR - lead
    y = np.zeros((n, 2))
    pre = tv_bp(pink(n, r), 400 * 3 ** np.clip((t + lead) / lead, 0, 1), q=0.9) * np.where(t < 0, np.clip((t + lead) / lead, 0, 1) ** 2.5, np.exp(-t / 0.05))
    pre /= np.abs(pre).max() + 1e-9
    y += 0.35 * to_st(pre)
    i0 = n_(lead)
    m = n_(1.2); tm = np.arange(m) / SR
    burst = bp(pink(m, r), 120, 700) * env_ad(m, 0.012, 0.22)
    burst /= np.abs(burst).max() + 1e-9
    sub = np.sin(2 * np.pi * np.cumsum(52 + 60 * np.exp(-tm / 0.05)) / SR) * env_ad(m, 0.004, 0.2)
    air = tv_bp(pink(m, r), 3200 * (900 / 3200) ** np.clip(tm / 0.7, 0, 1), q=0.8) * env_ad(m, 0.03, 0.35)
    air /= np.abs(air).max() + 1e-9
    body = 0.7 * burst + 0.8 * sub + 0.5 * air
    y[i0:i0 + m] += stereo(body, 0.35, r)
    for k, nm in enumerate(['E6', 'G#6', 'B6', 'E7', 'G#7', 'B7']):
        s = tine(NOTE(nm), 1.6, f'{seed}a{k}', amp=0.3 * 0.9 ** k)
        place(y, pan(s, (-1) ** k * 0.4), lead + 0.01 + 0.035 * k)
    g = np.zeros(n)
    for k in range(70):
        tg = r.uniform(0.02, 1.7)
        if r.random() > np.exp(-tg / 0.9): continue
        fg = r.uniform(3000, 10000); d = r.uniform(0.02, 0.06)
        s = np.sin(2 * np.pi * fg * tt(d)) * env_ad(n_(d), 0.002, d / 3) * r.uniform(0.3, 1.0)
        j = i0 + n_(tg); g[j:j + len(s)] += s[:n - j]
    y += 0.12 * stereo(g, 0.8, r)
    # the bright 'air' of the light-up (TF 111.0-112.6 lifts 6-16 kHz by ~17 dB): twinkling band noise 5-14 kHz
    ma = n_(2.0); ta = np.arange(ma) / SR
    hs = bp(white(ma, r), 5000, 14000, 2) * (0.35 + 0.65 * np.clip(smooth_noise(ma, 25, r), 0, 1) ** 2)
    hs = fade(hs * np.clip(ta / 0.05, 0, 1) * np.exp(-ta / 0.75), 0.0, 0.4)
    hs2 = bp(white(ma, rng(seed + 'R')), 5000, 14000, 2) * (0.35 + 0.65 * np.clip(smooth_noise(ma, 25, rng(seed + 'r2')), 0, 1) ** 2)
    hs2 = fade(hs2 * np.clip(ta / 0.05, 0, 1) * np.exp(-ta / 0.75), 0.0, 0.4)
    place(y, np.stack([hs, hs2], 1) / (np.abs(hs).max() + 1e-9) * 0.75, lead + 0.01)
    tp = tt(2.0)
    pad = (np.sin(2 * np.pi * NOTE('E4') / 2 * tp) + 0.7 * np.sin(2 * np.pi * NOTE('B4') / 2 * tp * 1.002)
           + 0.4 * np.sin(2 * np.pi * NOTE('E5') / 2 * tp * 0.998)) * env_ad(len(tp), 0.08, 0.55) * (1 + 0.15 * np.sin(2 * np.pi * 5.5 * tp))
    pad = fade(pad, 0.0, 0.6)
    place(y, stereo(lp(pad, 1800), 0.6, r) * 0.18, lead)
    try:
        sh = LIB.seg('ES_Magic, Shimmer, Magic Spell, Bright, Shimmer', 0.0, 2.2)
        sh = hp(sh, 2000) * np.linspace(1, 0.2, len(sh))[:, None]
        sh = fade(sh, 0.03, 0.6) / (np.abs(sh).max() + 1e-9)
        place(y, sh * 0.8, lead + 0.02)
    except FileNotFoundError:
        pass
    if second:
        j = lead + second
        m2 = n_(0.7); tm2 = np.arange(m2) / SR
        b2 = bp(pink(m2, r), 150, 900) * env_ad(m2, 0.015, 0.12); b2 /= np.abs(b2).max() + 1e-9
        s2 = np.sin(2 * np.pi * np.cumsum(60 + 40 * np.exp(-tm2 / 0.04)) / SR) * env_ad(m2, 0.004, 0.12)
        place(y, stereo(0.35 * b2 + 0.3 * s2, 0.3, r), j)
        for k, nm in enumerate(['B6', 'E7']):
            place(y, pan(tine(NOTE(nm), 1.0, f'{seed}b{k}', amp=0.14), 0.3 - 0.6 * k), j + 0.02 + 0.05 * k)
    y = fade(y, 0.005, 0.7)
    return norm(verb(y, 'night', 0.14, seed))


def breath_glass(seed='breath'):
    """BREATH (62.13 s, fog blooms on Theo's pane, heard from inside the room): a mole's short inhale then a slow
    warm exhale 'hhaaah' (formant-filtered noise), muffled by the glass (low-passed, a faint pane ring)."""
    r = rng(seed)
    y = np.zeros(n_(0.8))
    m = n_(0.12)
    inh = tv_bp(pink(m, r), np.linspace(1800, 2600, m), q=1.5) * env_ad(m, 0.04, 0.04)
    y[:m] += 0.3 * inh / (np.abs(inh).max() + 1e-9)
    m = n_(0.55); i = n_(0.16)
    src = pink(m, r)
    ex = 1.0 * peak_bp(src, 480, 3) + 0.6 * peak_bp(src, 1050, 4) + 0.25 * peak_bp(src, 2300, 5)
    ex *= np.clip(np.arange(m) / SR / 0.07, 0, 1) * np.exp(-np.maximum(np.arange(m) / SR - 0.12, 0) / 0.16)
    y[i:i + m] += fade(ex / (np.abs(ex).max() + 1e-9), 0.0, 0.2)
    y = lp(y, 3200, 2) + 0.04 * peak_bp(y, 1850, 20)
    return norm(verb(stereo(fade(y, 0.005, 0.08), 0.15, r), 'room', 0.12, seed))


def step_wet(seed='step', bare=False, weight=1.0):
    """STEP_WET (slipper on wet grass) / FEET_WET step (bare=True: a skin slap + wetter splat, lighter thud)."""
    r = rng(seed)
    y = np.zeros(n_(0.3))
    th = (np.sin(2 * np.pi * np.cumsum(70 + 40 * np.exp(-tt(0.08) / 0.015)) / SR) * env_ad(n_(0.08), 0.002, 0.022)
          + 0.6 * lp(white(n_(0.08), r), 380) * env_ad(n_(0.08), 0.002, 0.015) / 2)
    y[:len(th)] += (0.55 if bare else 0.8) * weight * th
    sw = hp(white(n_(0.11), r), 2600) * env_ad(n_(0.11), 0.008, 0.03)
    y[:len(sw)] += 0.18 * sw / (np.abs(sw).max() + 1e-9)
    m = n_(0.08); i = n_(0.012)
    sq = bp(white(m, r), 900, 2300) * (0.5 + 0.5 * np.sin(2 * np.pi * r.uniform(70, 110) * tt(0.08))) * env_ad(m, 0.004, 0.025)
    y[i:i + m] += (0.45 if bare else 0.28) * sq / (np.abs(sq).max() + 1e-9)
    if bare:
        sl = bp(white(n_(0.025), r), 600, 3200) * env_ad(n_(0.025), 0.0006, 0.007)
        y[:len(sl)] += 0.6 * sl / (np.abs(sl).max() + 1e-9)
    return norm(stereo(fade(y, 0.001, 0.04), 0.1, r))


def feet_run(times, seed='feet'):
    """FEET_WET: bare feet running on wet grass at the given relative times (s), alternating L/R slightly."""
    r = rng(seed)
    y = np.zeros((n_(times[-1] + 0.4), 2))
    for k, t in enumerate(times):
        s = step_wet(f'{seed}{k}', bare=True, weight=r.uniform(0.85, 1.1))[:, 0] * r.uniform(0.8, 1.0)
        place(y, pan(s, 0.12 * (-1) ** k), t)
    return norm(verb(y, 'night', 0.06, seed))


def walk(times, seed='walk'):
    """STEP_WET series (Grandpa's slippers on the wet lawn, flashback): soft slipper steps at relative times."""
    r = rng(seed)
    y = np.zeros((n_(times[-1] + 0.4), 2))
    for k, t in enumerate(times):
        s = step_wet(f'{seed}{k}', weight=r.uniform(0.8, 1.0))[:, 0] * (0.9 if k < len(times) - 1 else 0.7)
        place(y, pan(s, 0.1 * (-1) ** k), t)
    return norm(y)


def rip(seed='rip'):
    """RIP (56.63 s): cardboard tape pulled off a box: an accelerating stream of stick-slip micro-impulses through the
    tape's band and the box's cardboard resonances, ending in a release tick."""
    r = rng(seed)
    dur = 0.46; n = n_(dur)
    imp = np.zeros(n)
    t = 0.0
    while t < 0.38:
        rate = 320 + 650 * (t / 0.38) ** 0.7
        imp[n_(t)] += r.uniform(0.4, 1.0) * (1 if r.random() > 0.08 else 2.2)
        t += 1 / rate * r.uniform(0.6, 1.5)
    e = np.clip(np.arange(n) / SR / 0.015, 0, 1) * np.clip((0.40 - np.arange(n) / SR) / 0.03, 0, 1)
    imp *= e
    y = bp(imp, 1200, 7000) + 0.8 * peak_bp(imp, 650, 3) + 0.6 * peak_bp(imp, 1400, 4)
    y += 0.25 * bp(white(n, r), 2000, 6000) * e
    addat(y, click(0.001, 1500, r), n_(0.40), 0.6)
    return norm(stereo(fade(y, 0.001, 0.03), 0.2, r))


def flutter(seed='flutter', dur=0.45):
    """FLUTTER (59.33 s): the $4.99 price sticker swinging down (+-35 deg) and landing on the soil: faint paper flaps."""
    r = rng(seed)
    y = np.zeros(n_(dur + 0.1)); t = 0.02
    while t < dur - 0.04:
        s = bp(white(n_(0.025), r), 1500, 6500) * env_ad(n_(0.025), 0.004, 0.006)
        y[n_(t):n_(t) + len(s)] += s * r.uniform(0.4, 1.0)
        t += 1 / r.uniform(7, 10)
    land = lp(white(n_(0.03), r), 1200) * env_ad(n_(0.03), 0.001, 0.006)
    y[n_(dur):n_(dur) + len(land)] += 0.8 * land
    return norm(stereo(fade(y, 0.002, 0.02), 0.2, r))


def plastic_knock(seed, f0=420, amp=1.0, dur=0.18):
    r = rng(seed)
    y = modal(f0 * np.array([1, 2.3, 3.9, 6.1]), [0.04, 0.025, 0.015, 0.008], [1, 0.6, 0.35, 0.15], dur, r, detune=0.03)
    c = click(0.0008, 400, r); y[:len(c)] += 0.5 * c
    return amp * y


def thunk_plastic(seed='thunk'):
    """THUNK_PLASTIC (57.887 s): Mom's hollow plastic gnome pushed into the bed: hollow knock + soil thud + crunch."""
    r = rng(seed)
    y = np.zeros(n_(0.6))
    k = plastic_knock(seed + 'k', 380, 0.7)
    y[:len(k)] += k
    th = np.sin(2 * np.pi * np.cumsum(80 + 50 * np.exp(-tt(0.12) / 0.02)) / SR) * env_ad(n_(0.12), 0.002, 0.035)
    th += 0.5 * lp(white(n_(0.12), r), 320) * env_ad(n_(0.12), 0.002, 0.02) / 2
    y[:len(th)] += 0.8 * th
    c = crumble(0.4, seed + 'c', dark=2000)[:, 0]
    y[n_(0.01):n_(0.01) + len(c)] += 0.3 * c[:len(y) - n_(0.01)]
    return norm(verb(stereo(fade(y, 0.001, 0.08), 0.15, r), 'night', 0.08, seed))


def clatter(seed='clatter'):
    """CLATTER (46.005 s): next door's plastic gnome tips into a mole hole: 4 bouncing hollow knocks, a muffled
    drop inside the hole, then a trickle of soil."""
    r = rng(seed)
    y = np.zeros(n_(1.0))
    ts = [0.0, 0.13, 0.22, 0.28]
    for k, t in enumerate(ts):
        s = plastic_knock(f'{seed}{k}', r.uniform(340, 520), 0.9 * 0.7 ** k)
        y[n_(t):n_(t) + len(s)] += s
    d = lp(np.sin(2 * np.pi * np.cumsum(90 + 40 * np.exp(-tt(0.15) / 0.02)) / SR) * env_ad(n_(0.15), 0.002, 0.04), 600)
    y[n_(0.37):n_(0.37) + len(d)] += 0.5 * d
    c = crumble(0.55, seed + 'c', dark=1800)[:, 0]
    y[n_(0.36):n_(0.36) + len(c)] += 0.3 * c[:len(y) - n_(0.36)]
    return norm(verb(stereo(fade(y, 0.001, 0.1), 0.2, r), 'night', 0.1, seed))


def deflate(seed='deflate', n=6, gap=0.15):
    """DEFLATE (90.178 s): every mound sinks as the ring passes, staggered `gap` s: per mound a soft low thump, an air
    'pff' and a little soil settling; each a bit quieter, panning left to right with the ring."""
    r = rng(seed)
    y = np.zeros((n_(gap * n + 0.7), 2))
    for k in range(n):
        m = n_(0.4); tm = np.arange(m) / SR
        th = np.sin(2 * np.pi * np.cumsum(46 + 32 * np.exp(-tm / 0.03)) / SR) * env_ad(m, 0.004, 0.07)
        th += 0.4 * lp(white(m, r), 300) * env_ad(m, 0.003, 0.04) / 2
        pf = tv_bp(pink(m, r), 1500 * (300 / 1500) ** np.clip(tm / 0.25, 0, 1), q=0.8) * env_ad(m, 0.01, 0.1)
        pf /= np.abs(pf).max() + 1e-9
        c = crumble(0.4, f'{seed}c{k}', dark=1600)[:m, 0]
        s = 0.9 * th + 0.35 * pf + 0.25 * np.pad(c, (0, m - len(c)))
        place(y, pan(s * 0.86 ** k, -0.6 + 1.2 * k / max(1, n - 1)), k * gap + r.uniform(-0.01, 0.01))
    return norm(verb(y, 'night', 0.08, seed))


def blips(times, seed='blips', notes=('B6', 'G#6', 'E6', 'C#6', 'B5')):
    """BLIPS (s80): one tiny pitched blip per eye pair winking out, each a step lower (E-major pentatonic, falling),
    with a little downward bend: 'bip' as a light goes out. times are relative (s)."""
    r = rng(seed)
    y = np.zeros((n_(times[-1] + 0.3), 2))
    for k, t in enumerate(times):
        f = NOTE(notes[k % len(notes)]); m = n_(0.09); tm = np.arange(m) / SR
        ff = f * (1 - 0.1 * np.clip(tm / 0.06, 0, 1))
        ph = 2 * np.pi * np.cumsum(ff) / SR
        s = fade((np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph)) * env_ad(m, 0.002, 0.025), 0.0, 0.03)
        place(y, pan(s, r.uniform(-0.6, 0.6)), t)
    return norm(verb(y, 'night', 0.04, seed))


def engine(seed='engine', crank=0.45, idle_rpm=650, cab=False):
    """ENGINE (100.37 s): the moving truck (6-cyl diesel) starts off-screen: starter cranking with compression chugs,
    the catch at `crank` s (rev flare to 1100 rpm), it pulls away (rpm climbs, a gear change at 1.25 s), then fades
    out by 2.9 s (s89 'ENGINE fades' before the 'Every spring' pause). cab=True: heard from the truck's back."""
    r = rng(seed)
    dur = 3.1; n = n_(dur); t = np.arange(n) / SR
    y = np.zeros(n)
    m = n_(crank + 0.05); tc = np.arange(m) / SR
    chug = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 5.2 * tc)) * 0.6
    whine = sum(np.sin(2 * np.pi * k * 190 * tc * (1 + 0.04 * np.sin(2 * np.pi * 5.2 * tc))) / k for k in range(1, 6))
    st = 0.25 * whine * chug + 0.6 * lp(white(m, r), 500) * chug + 0.15 * hp(white(m, r), 1500) * chug
    st *= np.clip(tc / 0.03, 0, 1) * np.clip((crank + 0.05 - tc) / 0.05, 0, 1)
    y[:m] += st / (np.abs(st).max() + 1e-9) * 0.6
    rpm = np.where(t < crank, 0.0,
           np.where(t < crank + 0.25, 300 + 800 * np.clip((t - crank) / 0.25, 0, 1),
           np.where(t < crank + 0.65, 1100 - 350 * np.clip((t - crank - 0.25) / 0.4, 0, 1),
           np.where(t < 1.25, 750 + 600 * np.clip((t - crank - 0.65) / (1.25 - crank - 0.65), 0, 1),
                    1000 + 500 * np.clip((t - 1.25) / 1.5, 0, 1)))))
    ff = rpm / 20.0
    ph = np.cumsum(ff) / SR
    cyc = np.floor(ph).astype(int); frac = ph - cyc
    amp_c = r.uniform(0.8, 1.2, cyc.max() + 2)
    pulses = np.exp(-frac / 0.12) * amp_c[cyc] * (rpm > 0)
    tone = peak_bp(pulses, 90, 1.5) + 0.7 * peak_bp(pulses, 220, 2.5) + 0.35 * peak_bp(pulses, 480, 3)
    knock = hp(white(n, r), 1600) * (frac < 0.08) * (rpm > 0) * 0.25
    load = 0.6 + 0.4 * np.clip((rpm - 700) / 800, 0, 1)
    eng = (tone / (np.abs(tone).max() + 1e-9) + knock) * load
    out = np.clip((2.9 - t) / 1.1, 0, 1) ** 1.5
    y += 0.9 * eng * out
    y = lp(y, 1400 if cab else 2500, 2)
    return norm(verb(stereo(fade(y, 0.01, 0.2), 0.3, r), 'night', 0.12 if not cab else 0.05, seed))


def rattle(dur=1.8, seed='rattle'):
    """RATTLE (s88): cardboard boxes knocking in the truck's back as it pulls away (bumps every ~0.8 s)."""
    r = rng(seed)
    y = np.zeros(n_(dur + 0.2)); t = 0.05
    while t < dur:
        bump = 1.0 + 0.8 * (np.sin(2 * np.pi * 1.2 * t) > 0.7)
        m = n_(0.05)
        k = bp(white(m, r), 170, 520) * env_ad(m, 0.001, 0.012) + 0.3 * bp(white(m, r), 1500, 4000) * env_ad(m, 0.001, 0.004)
        y[n_(t):n_(t) + m] += k * r.uniform(0.3, 1.0) * bump
        t += r.exponential(1 / 7.0) + 0.02
    return norm(verb(stereo(fade(y, 0.02, 0.2), 0.4, r), 'room', 0.1, seed))


def photo_drop(times, seed='drops'):
    """DROPS (s90): Polaroids dropping onto a pile on the wooden garden table: a little air before each lands, a card
    slap, a damped table knock under it."""
    r = rng(seed)
    y = np.zeros((n_(times[-1] + 0.5), 2))
    for k, t in enumerate(times):
        m = n_(0.25); s = np.zeros(m)
        air = bp(white(n_(0.04), r), 800, 3000) * np.linspace(0, 1, n_(0.04)) ** 2 * 0.15
        sl = bp(white(n_(0.03), r), 1500, 6000) * env_ad(n_(0.03), 0.0005, 0.005)
        wood = modal([240, 560, 980], [0.03, 0.02, 0.012], [1, 0.6, 0.3], 0.1, r, detune=0.05) * 0.35
        s[:len(air)] += air; j = len(air)
        s[j:j + len(sl)] += sl / (np.abs(sl).max() + 1e-9); s[j:j + len(wood)] += wood * (0.7 ** k)
        place(y, pan(s * r.uniform(0.8, 1.0), r.uniform(-0.3, 0.3)), t - 0.04)
    return norm(verb(y, 'night', 0.05, seed))


def creak(dur, seed='creak', rates=(45, 110, 70), res=((380, 12), (920, 16), (1750, 20)), grit=0.03):
    """Wood creak by stick-slip: an irregular impulse train (rate gliding through `rates`) exciting resonances."""
    r = rng(seed)
    n = n_(dur); t = np.arange(n) / SR
    k = np.linspace(0, len(rates) - 1, n)
    rate = np.interp(k, np.arange(len(rates)), rates)
    imp = np.zeros(n); x = 0.0
    while x < dur:
        imp[n_(x) if n_(x) < n else n - 1] += r.uniform(0.5, 1.0)
        x += 1 / rate[min(n - 1, n_(x))] * r.uniform(0.8, 1.2)
    y = sum(peak_bp(imp, f, q) * (1 / (i + 1)) for i, (f, q) in enumerate(res))
    y = y / (np.abs(y).max() + 1e-12)
    y += grit * bp(white(n, r), 2000, 6000) * (imp > 0).astype(float).cumsum() / max(1, (imp > 0).sum())
    return y * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.7


def door_creak(seed='door'):
    """DOOR_CREAK (94.892 s): the front door opens at dawn (14 frames): the latch, then a soft wood creak."""
    r = rng(seed)
    y = np.zeros(n_(0.9))
    try:
        la = LIB.seg('ES_Doors, Hardware, Latch, Lock', 0.28, 0.62)[:, 0]
        la = lp(la, 6000) * 0.5; y[:len(la)] += la
    except FileNotFoundError:
        pass
    c = creak(0.55, seed + 'c', rates=(40, 95, 60))
    c /= np.abs(c).max() + 1e-9
    y[n_(0.1):n_(0.1) + len(c)] += 0.5 * c
    return norm(verb(stereo(fade(y, 0.001, 0.1), 0.15, r), 'night', 0.1, seed))


def lantern_creak(seed='lcreak'):
    """CREAK_LANTERN (s33): the little lantern's wire handle creaking as he lifts it: a thin metal squeak."""
    c = creak(0.3, seed, rates=(120, 260, 180), res=((1600, 12), (3100, 14), (4700, 16)), grit=0.05)
    return norm(stereo(fade(c, 0.005, 0.05), 0.15, rng(seed)))


def grind(seed='grind', dur=0.8, soft=False):
    """GRIND (66.55 s): the ceramic head turns 150 deg in stepped jerks (2-3 deg every 3 frames = 20 Hz) with an
    inOutSine speed curve: a stone-on-stone grind whose loudness follows the turn speed, a gritty 'krk' on every
    20 Hz step, and the Epidemic slow-ratchet clicks pitched down x0.75 underneath. soft=True: the far, low-passed
    version from the truck (103.05 s)."""
    r = rng(seed + ('soft' if soft else ''))
    n = n_(dur + 0.15); t = np.arange(n) / SR
    v = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.2
    g = bp(white(n, r), 500, 3200) * (0.6 + 0.4 * smooth_noise(n, 30, r))
    g = 0.6 * g + 0.5 * peak_bp(g, 1300, 5) + 0.35 * peak_bp(g, 2600, 6)
    y = g / (np.abs(g).max() + 1e-9) * v * 0.5
    for k in range(int(dur / 0.05)):
        j = n_(k * 0.05 + r.uniform(0, 0.006))
        m = n_(0.03)
        kr = bp(white(m, r), 700, 3500) * env_ad(m, 0.001, 0.008)
        kr = kr + 0.6 * peak_bp(kr, 1500, 6)
        y[j:j + m] += kr / (np.abs(kr).max() + 1e-9) * (0.35 + 0.65 * v[min(n - 1, j)]) * 0.6
    try:
        ra = LIB.seg('ES_Mechanical, Ratchet, Clicks, Slow', 1.55, 1.55 + dur * 0.75 + 0.02)[:, 0]
        ra = resample(ra, 4, 3)[:n]
        ra = lp(ra, 4500) / (np.abs(ra).max() + 1e-9)
        y[:len(ra)] += 0.35 * ra * v[:len(ra)]
    except FileNotFoundError:
        pass
    if soft:
        y = lp(y, 2800, 2)
    return norm(verb(stereo(fade(y, 0.005, 0.1), 0.2, r), 'night', 0.1 if not soft else 0.2, seed))


def kneel(seed='kneel'):
    """KNEEL (81.638 s): knees into the soft soil: a fabric brush, two soft knee thuds 0.07 s apart, soil crunch."""
    r = rng(seed)
    y = np.zeros(n_(0.6))
    fb = bp(white(n_(0.15), r), 2000, 6000) * env_ad(n_(0.15), 0.04, 0.04)
    y[:len(fb)] += 0.12 * fb / (np.abs(fb).max() + 1e-9)
    for k, t in enumerate([0.06, 0.13]):
        th = np.sin(2 * np.pi * np.cumsum(62 + 30 * np.exp(-tt(0.12) / 0.02)) / SR) * env_ad(n_(0.12), 0.003, 0.03)
        th += 0.5 * lp(white(n_(0.12), r), 350) * env_ad(n_(0.12), 0.002, 0.02) / 2
        y[n_(t):n_(t) + len(th)] += 0.7 * th * (0.85 ** k)
    c = crumble(0.35, seed + 'c', dark=1800)[:, 0]
    y[n_(0.07):n_(0.07) + len(c)] += 0.35 * c[:len(y) - n_(0.07)]
    return norm(stereo(fade(y, 0.002, 0.08), 0.15, r))


def set_down(seed='setdown'):
    """SET_DOWN (85.495 s): the ceramic gnome's base touches the soil: the Epidemic mug-down transient, dulled (soil,
    not a table), with a soft crunch of soil."""
    r = rng(seed)
    y = np.zeros(n_(0.5))
    try:
        mug = LIB.seg('ES_Food & Drink, Glassware, Mug, Coffee, Down On Table 02', 0.0, 0.15)[:, 0]
        mug = lp(mug, 2200, 2) / (np.abs(mug).max() + 1e-9)
        y[:len(mug)] += 0.7 * mug
    except FileNotFoundError:
        y[:n_(0.2)] += ceramic_tok(seed)[:n_(0.2), 0] * 0.6
    c = crumble(0.3, seed + 'c', dark=1700)[:, 0]
    y[n_(0.005):n_(0.005) + len(c)] += 0.3 * c[:len(y) - n_(0.005)]
    return norm(stereo(fade(y, 0.001, 0.08), 0.1, r))


def squeak_toy(seed='squeaky'):
    """SQUEAK (13.23 s): the dog bites the plastic hat (squash 15 % for 6 frames): a comic squeaky-toy squeeze: a
    reedy air tone gliding up then down, rough at the edges, with a little plastic crunch at the bite."""
    r = rng(seed)
    dur = 0.24; m = n_(dur); tm = np.arange(m) / SR; x = tm / dur
    f = 1350 + 420 * np.sin(np.pi * np.clip(x / 0.6, 0, 1)) - 250 * np.clip((x - 0.6) / 0.4, 0, 1)
    f *= 1 + 0.02 * smooth_noise(m, 60, r)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = sum(np.sin(k * ph) * (1 / k) for k in range(1, 7))
    y = y + 0.8 * peak_bp(y, 3000, 2)
    y *= (1 + 0.2 * np.sin(2 * np.pi * 35 * tm)) * np.clip(tm / 0.02, 0, 1) * np.clip((dur - tm) / 0.05, 0, 1)
    y += 0.15 * bp(white(m, r), 2000, 8000) * np.clip(tm / 0.02, 0, 1) * np.clip((dur - tm) / 0.05, 0, 1)
    out = np.zeros(n_(0.4)); out[n_(0.02):n_(0.02) + m] += y / (np.abs(y).max() + 1e-9)
    cr = bp(white(n_(0.04), r), 1500, 7000) * env_ad(n_(0.04), 0.001, 0.008)
    out[:len(cr)] += 0.4 * cr / (np.abs(cr).max() + 1e-9)
    return norm(stereo(fade(out, 0.001, 0.03), 0.1, r))


def chain_tug(seed='chain'):
    """CHAIN_TUG (14.595 s): the dog's lead clinks (small chain links) and gives one tug (leather creak + thud)."""
    r = rng(seed)
    y = np.zeros(n_(0.5))
    for k in range(4):
        f = r.uniform(3200, 7200)
        s = modal([f, f * 2.7, f * 5.1], [0.04, 0.02, 0.01], [1, 0.4, 0.2], 0.12, r)
        j = n_(0.015 * k + r.uniform(0, 0.01)); y[j:j + len(s)] += 0.35 * s
    c = creak(0.12, seed + 'c', rates=(80, 140), res=((700, 5), (1600, 7)))
    c /= np.abs(c).max() + 1e-9
    y[n_(0.08):n_(0.08) + len(c)] += 0.3 * c
    th = lp(white(n_(0.05), r), 400) * env_ad(n_(0.05), 0.002, 0.01)
    y[n_(0.1):n_(0.1) + len(th)] += 0.4 * th / (np.abs(th).max() + 1e-9)
    return norm(stereo(fade(y, 0.001, 0.05), 0.2, r))


def hops(times, seed='hops'):
    """HOPS (s14): the family gnome toddling down its path in small hops: tiny ceramic taps on stone at `times`."""
    r = rng(seed)
    y = np.zeros((n_(times[-1] + 0.25), 2))
    for k, t in enumerate(times):
        s = modal([1650, 3500, 6100, 900], [0.02, 0.012, 0.006, 0.02], [1, 0.5, 0.2, 0.3], 0.08, r, detune=0.05)
        place(y, pan(s * r.uniform(0.7, 1.0), 0.05 * (-1) ** k), t)
    return norm(y)


def bonk(seed='bonk'):
    """BONK (16.312 s): the family gnome's hollow ceramic head bonks the invisible property line: a hollow porcelain
    bonk with a cartoon pitch-drop, then a glassy ripple 'wom-wom-wom' (3 rings in 0.45 s, the ripple rings on the
    curtain) with a 12-grain sparkle on top."""
    r = rng(seed)
    y = np.zeros(n_(1.0))
    m = n_(0.4); tm = np.arange(m) / SR
    f0 = 380 * (1 + 0.08 * np.exp(-tm / 0.02))
    ph = 2 * np.pi * np.cumsum(f0) / SR
    b = (np.sin(ph) * np.exp(-tm / 0.12) + 0.6 * np.sin(2.4 * ph) * np.exp(-tm / 0.07)
         + 0.35 * np.sin(4.3 * ph) * np.exp(-tm / 0.04) + 0.2 * np.sin(7.1 * ph) * np.exp(-tm / 0.025))
    b += 0.5 * np.sin(2 * np.pi * 240 * tm) * np.exp(-tm / 0.08)
    c = click(0.0006, 800, r); b[:len(c)] += 0.6 * c
    y[:m] += b
    m = n_(0.6); tm = np.arange(m) / SR
    am = np.clip(np.sin(np.pi * np.clip(tm / 0.45, 0, 1) * 3), 0, 1) ** 1.5 * np.exp(-tm / 0.25)
    fc = 520 * (1 + 0.04 * np.sin(2 * np.pi * 6.7 * tm))
    pc = 2 * np.pi * np.cumsum(fc) / SR
    wom = np.sin(pc + 1.2 * np.exp(-tm / 0.2) * np.sin(1.41 * pc)) + 0.5 * np.sin(pc / 2)
    y[n_(0.03):n_(0.03) + m] += 0.45 * wom * am
    for k in range(12):
        f = r.uniform(5500, 10500); d = r.uniform(0.02, 0.05)
        s = np.sin(2 * np.pi * f * tt(d)) * env_ad(n_(d), 0.001, d / 3)
        j = n_(0.02 + r.uniform(0, 0.3)); y[j:j + len(s)] += 0.12 * s
    return norm(verb(stereo(fade(y, 0.001, 0.15), 0.3, r), 'night', 0.1, seed))


def poof_soft(seed='poof'):
    """POOF_SOFT (112.69 s): the dandelion clock releases its seeds: a soft breathy puff (the Epidemic cartoon pop
    variant 3, low-passed) and one tiny high tine; the tail is gone 0.55 s later (episode end 113.30)."""
    r = rng(seed)
    y = np.zeros((n_(0.6), 2))
    m = n_(0.35); tm = np.arange(m) / SR
    pu = tv_bp(pink(m, r), 900 * 2.5 ** np.clip(tm / 0.06, 0, 1), q=0.7) * env_ad(m, 0.02, 0.08)
    place(y, stereo(fade(0.6 * pu / (np.abs(pu).max() + 1e-9), 0.0, 0.15), 0.4, r), 0.0)
    try:
        p = LIB.seg('ES_Cartoon, Pop, Vanish', 3.10, 3.40)
        p = lp(p, 3500, 2) / (np.abs(p).max() + 1e-9)
        place(y, fade(p, 0.02, 0.05) * 0.35, -0.08)
    except FileNotFoundError:
        pass
    place(y, pan(tine(NOTE('B6'), 0.45, seed + 't', amp=0.18), 0.2), 0.05)
    return norm(fade(y, 0.002, 0.15))


def ripple_shimmer(seed='shimmer_s'):
    """SHIMMER_S (17.033 s / 35.087 s): a soft gold shimmer as a gnome crosses the line in family hands: the
    Epidemic bright shimmer's first 0.9 s above 2 kHz plus a rising three-tine figure."""
    r = rng(seed)
    y = np.zeros((n_(1.1), 2))
    try:
        sh = LIB.seg('ES_Magic, Shimmer, Magic Spell, Bright, Shimmer', 0.0, 1.0)
        sh = hp(sh, 2200) / (np.abs(sh).max() + 1e-9)
        place(y, fade(sh, 0.04, 0.4) * 0.6, 0.0)
    except FileNotFoundError:
        pass
    for k, nm in enumerate(['B6', 'E7', 'G#7']):
        place(y, pan(tine(NOTE(nm), 0.7, f'{seed}{k}', amp=0.25), -0.3 + 0.3 * k), 0.02 + 0.06 * k)
    return norm(fade(y, 0.002, 0.2))


def thud_low(seed='thud'):
    """THUD_LOW (53.1 s): Theo's window goes dark and the mounds surge: the Epidemic dark low hit (its click removed
    by the low-pass) under a short mound rumble surge."""
    r = rng(seed)
    y = np.zeros((n_(1.6), 2))
    try:
        h = LIB.seg('ES_Designed, Boom, Impact, Dark, Cinematic, Low HIt', 0.33, 1.9)
        h = lp(h, 700, 4) / (np.abs(h).max() + 1e-9)
        place(y, fade(h, 0.005, 0.5) * 0.8, 0.0)
    except FileNotFoundError:
        pass
    rb = rumble(1.2, seed + 'r', sub=0.4, crackle=0.6)
    place(y, rb * 0.35, 0.03)
    return norm(y)


def tide(seed='tide'):
    """TIDE (63.578 s): the ring of light pushes the mounds back 3 studs in 0.5 s, like a tide going out: a turf
    whoosh that recedes (filter closing, level falling) over a rumble that moves away, with soil hiss."""
    r = rng(seed)
    n = n_(0.9); t = np.arange(n) / SR
    w = tv_bp(pink(n, r), 2200 * (350 / 2200) ** np.clip(t / 0.6, 0, 1), q=0.7) * env_ad(n, 0.05, 0.22)
    w /= np.abs(w).max() + 1e-9
    rb = rumble(0.9, seed + 'r', sub=0.5, crackle=1.0)
    y = 0.6 * stereo(w, 0.6, r) + 0.6 * rb[:n] * np.exp(-t / 0.35)[:, None]
    c = crumble(0.6, seed + 'c', dark=3000)
    y[:len(c)] += 0.25 * c[:n]
    return norm(fade(y, 0.01, 0.15))


def brick(seed='brick'):
    """BRICK (61.635 s): an edging brick tips out of the bed (10 deg): a dull clay clunk with a little grit."""
    r = rng(seed)
    y = modal([180, 610, 1450, 2600], [0.03, 0.025, 0.015, 0.008], [0.8, 1, 0.5, 0.25], 0.3, r, detune=0.03)
    c = click(0.0008, 500, r); y[:len(c)] += 0.4 * c
    g = crumble(0.25, seed + 'c', dark=3500)[:, 0]
    y[n_(0.01):n_(0.01) + len(g)] += 0.25 * g[:len(y) - n_(0.01)]
    return norm(verb(stereo(fade(y, 0.001, 0.05), 0.15, r), 'night', 0.06, seed))


def slap_sticker(seed='slap'):
    """SLAP_STICKER (27.51 s): the SOLD sticker slaps onto the agent board (scale 1.3 -> 1 in 4 frames): the Epidemic
    rubber-stamp thwack under a short paper 'fap' and a hollow board knock."""
    r = rng(seed)
    y = np.zeros(n_(0.35))
    try:
        st = LIB.seg('ES_Office Supplies, Rubber Stamp, Document 01', 0.0, 0.2)[:, 0]
        st = st / (np.abs(st).max() + 1e-9); y[:len(st)] += 0.8 * st
    except FileNotFoundError:
        pass
    fa = bp(white(n_(0.03), r), 1200, 7000) * env_ad(n_(0.03), 0.002, 0.006)
    y[:len(fa)] += 0.5 * fa / (np.abs(fa).max() + 1e-9)
    bd = modal([210, 470, 890], [0.03, 0.02, 0.012], [1, 0.6, 0.3], 0.15, r)
    y[n_(0.008):n_(0.008) + len(bd)] += 0.3 * bd
    return norm(verb(stereo(fade(y, 0.0005, 0.05), 0.1, r), 'night', 0.05, seed))


def room_tone(dur, seed='room'):
    """Interior room tone: dark pink noise (< 300 Hz) with a whisper of air on top; no hum."""
    r = rng(seed)
    n = n_(dur)
    a = lp(pink(n, r), 300, 2) + 0.06 * hp(pink(n, rng(seed + 'h')), 2500)
    b = lp(pink(n, rng(seed + 'R')), 300, 2) + 0.06 * hp(pink(n, rng(seed + 'H')), 2500)
    return np.stack([a, 0.8 * a + 0.2 * b], 1) / 4


def mower(dur, seed='mower'):
    """Distant lawn mower (A_DAY): a single-cylinder 2-stroke at ~3300 rpm (55 Hz firing), harmonics, far away
    (low-passed), drifting in level as it turns."""
    r = rng(seed)
    n = n_(dur); t = np.arange(n) / SR
    f = 55 * (1 + 0.03 * smooth_noise(n, 0.4, r))
    ph = np.cumsum(f) / SR; frac = ph - np.floor(ph)
    p = np.exp(-frac / 0.15) + 0.3 * hp(white(n, r), 800) * (frac < 0.2)
    y = lp(p, 650, 2) * (0.6 + 0.4 * smooth_noise(n, 0.15, r))
    return stereo(y / (np.abs(y).max() + 1e-9), 0.4, r)


def curtains(seed='curtain', n=6, gap=0.12):
    """CURTAIN (11.685 s, optional): six lit windows, curtains snapping shut nearest first: short fabric swishes
    (Epidemic double-swish variants, low-passed, each further one quieter and duller)."""
    r = rng(seed)
    y = np.zeros((n_(gap * n + 0.5), 2))
    vs = [(0.04, 0.30), (1.58, 1.84), (3.12, 3.38), (4.40, 4.66)]
    for k in range(n):
        a, b = vs[k % len(vs)]
        try:
            s = LIB.seg('ES_Swooshes, Swish, Fast, Double Swish, Variations', a, b)
        except FileNotFoundError:
            s = to_st(bp(white(n_(0.2), r), 600, 4000) * env_ad(n_(0.2), 0.03, 0.04))
        s = lp(s, 5000 - 500 * k) / (np.abs(s).max() + 1e-9) * 0.8 ** k
        place(y, fade(s, 0.005, 0.05), k * gap)
    return norm(y)


DESIGNS = {   # name -> zero-arg callable producing the default render (used by the catalog and the QA sheets)
    'tik': lambda: tik(), 'tik_slow': lambda: tik(slow=True), 'tok': lambda: ceramic_tok(),
    't_glint': lambda: plink('glint', f0=6200, n=1), 'plink': lambda: plink('plink'), 'reflector_flash': lambda: reflector_flash(),
    'tink_whoosh': lambda: lantern_light(), 'tinks': lambda: lantern_cascade([0.0, 0.2, 0.39, 0.59])[0],
    'rumble_roll': lambda: rumble(1.4, 'roll', sub=0.7, move=(-0.5, 0.5)), 'rumble_tail': lambda: rumble(2.4, 'tail', sub=1.0),
    'rumble_far': lambda: lp(rumble(0.9, 'far', sub=0.5, crackle=0.3), 400),
    'fip': lambda: fip(), 'sniff': lambda: sniff(), 'sniff_big': lambda: sniff('sniffbig', size=1.8, n_sniffs=2),
    'sniff_wriggle': lambda: sniff('wriggle', n_sniffs=2, wriggle=0.5), 'gulp': lambda: gulp(), 'fwoom': lambda: fwoom(),
    'breath': lambda: breath_glass(), 'step_wet': lambda: step_wet(), 'feet_wet': lambda: feet_run([0, 0.25, 0.5, 0.75]),
    'feet_plant': lambda: feet_run([0.0, 0.09], 'plant'), 'walk': lambda: walk([0, 0.44, 0.88, 1.32, 1.75]),
    'rip': lambda: rip(), 'flutter': lambda: flutter(), 'thunk_plastic': lambda: thunk_plastic(), 'clatter': lambda: clatter(),
    'deflate': lambda: deflate(), 'blips': lambda: blips([0, 0.38, 0.558, 0.793, 0.943]), 'engine': lambda: engine(),
    'rattle': lambda: rattle(), 'drops': lambda: photo_drop([0, 0.4, 0.638, 0.92]), 'door_creak': lambda: door_creak(),
    'creak_lantern': lambda: lantern_creak(), 'grind': lambda: grind(), 'grind_soft': lambda: grind(soft=True),
    'kneel': lambda: kneel(), 'set_down': lambda: set_down(), 'squeak': lambda: squeak_toy(), 'chain_tug': lambda: chain_tug(),
    'hops': lambda: hops([0, 0.22, 0.45, 0.67, 0.9]), 'bonk': lambda: bonk(), 'poof_soft': lambda: poof_soft(),
    'shimmer_s': lambda: ripple_shimmer(), 'thud_low': lambda: thud_low(), 'tide': lambda: tide(), 'brick': lambda: brick(),
    'slap_sticker': lambda: slap_sticker(), 'curtain': lambda: curtains(),
}


if __name__ == '__main__':
    import soundfile as sf
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SCRATCH, 'synth')
    names = sys.argv[2:] or list(DESIGNS)
    os.makedirs(out, exist_ok=True)
    for k in names:
        x = to_st(DESIGNS[k]())
        sf.write(os.path.join(out, k + '.wav'), x.astype(np.float32), SR, subtype='PCM_24')
        print(f'{k:16s} {len(x) / SR:5.2f} s  peak {20 * np.log10(np.abs(x).max() + 1e-12):5.1f} dBFS')
