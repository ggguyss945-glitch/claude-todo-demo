"""Sound effects for "If A Police Officer Knocks..." v2: recorded, layered, perspective-processed, 48 kHz stereo float.

Every sound is built from the recorded library (the owner's Epidemic files first, then the free CC0/CC-BY library in
catalog.json via library.py), cut into single events ("grains") automatically, layered 2-3 deep (e.g. a knock =
recorded knuckle/door hit + modal door-body thump + hallway convolution), varied by seed and never repeating the same
grain back to back. Synthesis is used only to fill gaps or add a layer (door-body modes, sub booms, sirens with
doppler, ring-back tones, CRT power-off, squelch tails).

Public API
    render(name, seed=0, space=None, level=0.0, **params) -> np.ndarray float32 [n, 2] at 48 kHz
    render_event(name, seed=0, space=None, level=0.0, **params) -> (audio, pre_s)
        pre_s = seconds of audio that come BEFORE the cue time t, so mix.py places the audio at t - pre_s:
        a riser ends at t, a whoosh / car_pass / siren pass peaks at t, a hit's transient lands on t.
    NAMES       the 42 required names           SPACES   'close', 'inside', 'outside', 'doorbell_mic'
                                                          (+ 'street', 'phone', 'radio', 'car', 'dry')
    LEVEL_LU    house level of each name in LU relative to the narration's integrated loudness
    BEDS        continuous names (take dur; calibrated by integrated loudness; mix.py ducks them with the music)
    HITS        names mix.py treats as hits (bed dips just before them, never ducked)
    DEFAULT_SPACE  per-name default perspective
    space(y, kind, seed=0, wet=None) -> stereo      perspective processing on any audio
    ir(name) -> [n, 2]    unit-energy IRs: recorded OpenAIR 'live', 'hall', 'recital', 'church', 'reactor', 'forest';
                          synthetic (image-source early reflections + per-band exponential tail) 'hallway', 'living',
                          'porch', 'street', 'car'
    reset()     clears the recent-pick memory (mix.py calls it before rendering a cue sheet, so renders are repeatable)
    helpers reused by mix.py: lufs_int, mom_max, kw, follow, compress, eq, hp, lp, bp, st, mono, fade, pan

Calibration: output loudness is absolute for a mix whose voice sits at -14 LUFS integrated. One-shots: momentary
(400 ms) maximum = -14 + LEVEL_LU[name] + SPACE_LU[space] + level (+ a force/intensity term); beds: integrated
loudness the same way. gain_db = 0 in sfx_cues.json therefore gives the house level.

Parameters (all optional; unknown keys are ignored; every name accepts seed, space, level, dur where it makes sense)
    knock_door      n=3, spacing=0.32, force=0.7 (0..1), accel=0 (0..0.3 speeds up), material='wood'|'glass', door=1
    doorbell_chime  -                                footsteps_porch / footsteps_wood_inside  n or dur, rate=1.8
                                                     steps/s, approach=0 (+1 nearer, -1 away), creak=0.3, weight=0.7
    car_pass        dist=1 (x reference distance), direction=1|-1, dur=None (window around the pass)
    car_idle        dur=8              car_door_open / car_door_close  -      siren_far  dur=12, dist=1, synth=False,
                                                     mode='wail'|'yelp', speed=0 (m/s, >0 = drive-by with doppler)
    police_radio_squelch  kind='key'|'unkey'|'burst'  radio_click  -   radio_static  dur=3, amount=0.6
    bodycam_beep    n=2                phone_ring  dur=None or n=2, kind='ring'|'ringback'   phone_busy  dur=3
    phone_vibrate   n=2                phone_pickup -    mail_slot  paper=False    paper  dur=1.2
    pen_click       n=1                key_in_lock  -    lock_turn  -              chain_lock  action='lock'|'unlock'
    door_creak      dur=None (stretch), slow=1.0         breath  kind='nervous'|'panic'|'panting'|'gasp'|'held', dur=3
    heartbeat       bpm=70, bpm_end=None, dur=6          whoosh  kind='soft'|'hard'
    riser           dur=6              braam  key='d'    impact_hit  size=1.0 (0.5..1.5)   sub_drop  -   stinger  -
    glitch          dur=0.6, amount=0.7                  ui_pop  -   typing  dur=3, cps=7   tinnitus  dur=4, freq=None
    ambience_night  dur=30, dog=0.5, wind=0.5, buzz=0.5  room_tone  dur=10       clock_tick  dur=6, bpm=60
    countdown_tick  n=1, spacing=1.0, rise=0 (semitones per tick)                tv_off  -
    crowd_whisper   dur=4, density=6 (voices per second)
"""
import os, sys, json, math, hashlib
from collections import OrderedDict, defaultdict, deque
import numpy as np, soundfile as sf
from scipy import signal
import soxr
from numba import njit

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import library as LIB

SR = 48000
REF = -14.0
S = '/home/user/claude-todo-demo/Vox test/Police Officer Video/v2/_work'
CACHE = os.path.join(S, 'pov2', 'cache', 'sfx')

NAMES = ('knock_door', 'doorbell_chime', 'footsteps_porch', 'footsteps_wood_inside', 'car_pass', 'car_idle',
         'car_door_open', 'car_door_close', 'siren_far', 'police_radio_squelch', 'radio_click', 'radio_static',
         'bodycam_beep', 'phone_ring', 'phone_busy', 'phone_vibrate', 'phone_pickup', 'mail_slot', 'paper',
         'pen_click', 'key_in_lock', 'lock_turn', 'chain_lock', 'door_creak', 'breath', 'heartbeat', 'whoosh',
         'riser', 'braam', 'impact_hit', 'sub_drop', 'stinger', 'glitch', 'ui_pop', 'typing', 'tinnitus',
         'ambience_night', 'room_tone', 'clock_tick', 'countdown_tick', 'tv_off', 'crowd_whisper')

LEVEL_LU = dict(knock_door=-3, doorbell_chime=-6, footsteps_porch=-11, footsteps_wood_inside=-11, car_pass=-13,
                car_idle=-23, car_door_open=-12, car_door_close=-7, siren_far=-16, police_radio_squelch=-8,
                radio_click=-11, radio_static=-19, bodycam_beep=-9, phone_ring=-7, phone_busy=-12, phone_vibrate=-11,
                phone_pickup=-11, mail_slot=-7, paper=-13, pen_click=-11, key_in_lock=-10, lock_turn=-7,
                chain_lock=-8, door_creak=-9, breath=-13, heartbeat=-8, whoosh=-8, riser=-4, braam=-1,
                impact_hit=+1, sub_drop=-3, stinger=0, glitch=-8, ui_pop=-13, typing=-14, tinnitus=-15,
                ambience_night=-25, room_tone=-31, clock_tick=-15, countdown_tick=-9, tv_off=-9, crowd_whisper=-13)
SPACE_LU = dict(close=1.0, inside=0.0, outside=-7.0, doorbell_mic=-2.0, street=-6.0, phone=-4.0, radio=-3.0,
                car=-2.0, dry=0.0)
SPACES = tuple(SPACE_LU)
PEAK_CAP = defaultdict(lambda: -7.0, knock_door=-5.0, impact_hit=-4.0, braam=-4.0, stinger=-4.0, sub_drop=-4.0,
                       riser=-5.0, car_door_close=-6.0, mail_slot=-6.0, lock_turn=-6.0)
BEDS = ('ambience_night', 'room_tone', 'radio_static', 'car_idle', 'tinnitus', 'phone_busy', 'crowd_whisper')
HITS = ('impact_hit', 'stinger', 'braam', 'sub_drop')
DEFAULT_SPACE = defaultdict(lambda: 'close', knock_door='inside', footsteps_porch='outside', car_pass='street',
                            car_idle='outside', car_door_open='street', car_door_close='street', siren_far='street',
                            mail_slot='inside', key_in_lock='inside', lock_turn='inside', chain_lock='inside',
                            door_creak='inside', footsteps_wood_inside='inside', ambience_night='outside',
                            room_tone='inside', clock_tick='inside', phone_busy='phone', doorbell_chime='inside',
                            riser='dry', braam='dry', impact_hit='dry', sub_drop='dry', stinger='dry', whoosh='dry',
                            tinnitus='dry', glitch='dry', ui_pop='dry', heartbeat='dry')


# ======================================================================================== basic DSP
def st(y):
    y = np.asarray(y, np.float32)
    if y.ndim == 1:
        return np.stack([y, y], 1)
    return y if y.shape[1] == 2 else np.repeat(y[:, :1], 2, 1)


def mono(y):
    return y.mean(1) if y.ndim == 2 else y


def n_(sec):
    return max(1, int(round(sec * SR)))


def fade(y, fi=0.002, fo=0.015):
    y = np.array(y, np.float32, copy=True)
    a, b = min(n_(fi), len(y) // 2), min(n_(fo), len(y) // 2)
    if a > 1:
        w = np.sin(np.linspace(0, np.pi / 2, a)) ** 2
        y[:a] *= w[:, None] if y.ndim == 2 else w
    if b > 1:
        w = np.cos(np.linspace(0, np.pi / 2, b)) ** 2
        y[-b:] *= w[:, None] if y.ndim == 2 else w
    return y


_SOS = {}


def _bw(kind, f, order):
    k = (kind, f, order)
    if k not in _SOS:
        _SOS[k] = signal.butter(order, f, kind, fs=SR, output='sos')
    return _SOS[k]


def hp(y, f, o=2):
    return signal.sosfilt(_bw('highpass', float(f), o), y, axis=0).astype(np.float32)


def lp(y, f, o=2):
    return signal.sosfilt(_bw('lowpass', float(min(f, SR * 0.49)), o), y, axis=0).astype(np.float32)


def bp(y, lo, hi, o=2):
    return signal.sosfilt(_bw('bandpass', (float(lo), float(min(hi, SR * 0.49))), o), y, axis=0).astype(np.float32)


def _rbj(kind, f0, g, q=0.707):
    A = 10 ** (g / 40); w = 2 * np.pi * f0 / SR; c = np.cos(w); s = np.sin(w)
    if kind == 'peak':
        al = s / (2 * q)
        b = [1 + al * A, -2 * c, 1 - al * A]; a = [1 + al / A, -2 * c, 1 - al / A]
    else:
        al = s / 2 * np.sqrt(2.0) * (q / 0.707) ** -1 if q else s / 2 * np.sqrt(2)
        r = 2 * np.sqrt(A) * al
        if kind == 'ls':
            b = [A * ((A + 1) - (A - 1) * c + r), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - r)]
            a = [(A + 1) + (A - 1) * c + r, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - r]
        else:
            b = [A * ((A + 1) + (A - 1) * c + r), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - r)]
            a = [(A + 1) - (A - 1) * c + r, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - r]
    return np.array(b + a) / a[0]


def eq(y, *bands):
    """bands: (kind, f0, gain_db, q) with kind 'peak' | 'ls' (low shelf) | 'hs' (high shelf)."""
    if not bands:
        return y
    sos = np.vstack([_rbj(*b) for b in bands])
    return signal.sosfilt(sos, y, axis=0).astype(np.float32)


def pan(y, p):
    p = float(np.clip(p, -1, 1))
    if abs(p) < 1e-3:
        return y
    a = (p + 1) * np.pi / 4
    y = st(y).copy()
    y[:, 0] *= np.sqrt(2) * np.cos(a); y[:, 1] *= np.sqrt(2) * np.sin(a)
    return y


def width(y, w):
    y = st(y); m = y.mean(1); s = (y[:, 0] - y[:, 1]) * 0.5 * w
    return np.stack([m + s, m - s], 1).astype(np.float32)


def rate(y, r):
    """Varispeed by ratio r (r > 1: shorter and higher)."""
    if abs(r - 1) < 1e-4:
        return y
    return soxr.resample(np.ascontiguousarray(y, np.float32), SR * r, SR, quality='HQ').astype(np.float32)


def semis(s):
    return 2.0 ** (s / 12.0)


def place(dst, src, i):
    i = int(i)
    a, b = max(0, i), min(len(dst), i + len(src))
    if b > a:
        dst[a:b] += src[a - i:b - i]
    return dst


def peak(y):
    return float(np.max(np.abs(y))) if len(y) else 0.0


def pnorm(y, to=1.0):
    p = peak(y)
    return y * (to / p) if p > 0 else y


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-12))


def sat(y, drive=2.0):
    p = peak(y)
    if p <= 0:
        return y
    return (np.tanh(y / p * drive) / np.tanh(drive) * p).astype(np.float32)


@njit(cache=True)
def follow(x, a_att, a_rel):
    """One-pole peak follower with separate attack/release coefficients (exp(-1/(tau*SR)))."""
    out = np.empty_like(x); v = 0.0
    for i in range(x.size):
        xi = x[i]
        if xi > v:
            v = a_att * v + (1.0 - a_att) * xi
        else:
            v = a_rel * v + (1.0 - a_rel) * xi
        out[i] = v
    return out


def coef(tau):
    return float(np.exp(-1.0 / (max(tau, 1e-5) * SR)))


def compress(y, thr_db, ratio=3.0, att=0.005, rel=0.12, knee=6.0, makeup=0.0, key=None):
    d = np.abs(mono(y if key is None else key)).astype(np.float64)
    env = follow(d, coef(att), coef(rel))
    over = db(env) - thr_db
    gr = np.where(over <= -knee / 2, 0.0, np.where(over >= knee / 2, over * (1 - 1 / ratio),
                                                   (1 - 1 / ratio) * (over + knee / 2) ** 2 / (2 * knee)))
    g = (10 ** ((makeup - gr) / 20)).astype(np.float32)
    return y * (g[:, None] if y.ndim == 2 else g)


# ---------------------------------------------------------------------------------------- loudness (BS.1770)
_KB = (np.array([1.53512485958697, -2.69169618940638, 1.19839281085285]), np.array([1.0, -1.69065929318241, 0.73248077421585]))
_KH = (np.array([1.0, -2.0, 1.0]), np.array([1.0, -1.99004745483398, 0.99007225036621]))


def kw(y):
    return signal.lfilter(*_KH, signal.lfilter(*_KB, y, axis=0), axis=0)


_KSOS = np.vstack([np.concatenate(_KB), np.concatenate(_KH)])
SEG = 0.05


def seg_power(y, seg=SEG):
    """K-weighted mean power (channels summed) per seg-second segment, filtered in chunks (low memory for long mixes).
    Returns (powers, exact) where exact=False means the sound is shorter than one segment (one whole-sound value)."""
    y = st(y); n = len(y); s = n_(seg); m = n // s
    if m == 0:
        z = kw(y.astype(np.float64)); return np.array([(z ** 2).sum() / max(n, 1)]), False
    out = np.empty(m); zi = np.zeros((2, 2, 2)); step = s * 400
    for a in range(0, m * s, step):
        b = min(m * s, a + step)
        z, zi = signal.sosfilt(_KSOS, y[a:b].astype(np.float64), axis=0, zi=zi)
        out[a // s:b // s] = (z * z).sum(1).reshape(-1, s).mean(1)
    return out, True


def _blocks(y, win=0.4, hop=0.1):
    """Mean K-weighted power of win-second blocks every hop seconds (win, hop multiples of 50 ms)."""
    P, ok = seg_power(y)
    k = max(1, int(round(win / SEG))); h = max(1, int(round(hop / SEG)))
    if not ok or len(P) <= k:
        return np.array([P.mean()])
    c = np.concatenate([[0.0], np.cumsum(P)])
    i = np.arange(0, len(P) - k + 1, h)
    return (c[i + k] - c[i]) / k


def mom_max(y):
    return float(-0.691 + 10 * np.log10(_blocks(y).max() + 1e-20))


def lufs_int(y):
    e = _blocks(y)
    L = -0.691 + 10 * np.log10(e + 1e-20)
    e = e[L > -70]
    if not len(e):
        return -70.0
    g = -0.691 + 10 * np.log10(e.mean()) - 10
    e2 = e[-0.691 + 10 * np.log10(e) > g]
    return float(-0.691 + 10 * np.log10((e2 if len(e2) else e).mean()))


def onset_s(y, rel_db=-24):
    """Time of the first sample within rel_db of the peak (the transient)."""
    a = np.abs(mono(st(y)))
    if not len(a):
        return 0.0
    i = int(np.argmax(a > a.max() * 10 ** (rel_db / 20)))
    return i / SR


def env_peak_s(y, smooth=0.25):
    a = mono(st(y)) ** 2
    k = n_(smooth)
    e = np.convolve(a, np.ones(k) / k, 'same')
    return int(np.argmax(e)) / SR


# ======================================================================================== impulse responses
_IR = {}
_REC_IR = dict(live='openair2__live_room', hall='openair__central_hall_university_york_ir_centre_stalls',
               recital='openair2__recital_hall', church='openair__1st_baptist_nashville_1st_baptist_nashville_far_close',
               reactor='openair__r1_nuclear_reactor_hall_stereo_r1_ortf_48k', forest='openair__forest_in_wheldrakewood_s1r1_ms')


def _unit(h):
    h = h.astype(np.float32)
    return h / np.sqrt((h ** 2).sum() / 2 + 1e-20)


def _tail(length, t60s, seed, t0=0.02):
    """Decorrelated stereo diffuse tail, per-band exponential decay (bands <250, 250-1k, 1-4k, 4-8k, >8k)."""
    rng = np.random.default_rng(seed); n = n_(length); t = np.arange(n) / SR
    out = np.zeros((n, 2), np.float32)
    edges = [(None, 250), (250, 1000), (1000, 4000), (4000, 8000), (8000, None)]
    for ch in range(2):
        x = rng.standard_normal(n).astype(np.float32)
        for (lo, hi), T in zip(edges, t60s):
            b = lp(x, hi, 4) if lo is None else (hp(x, lo, 4) if hi is None else bp(x, lo, hi, 4))
            out[:, ch] += b * np.exp(-6.91 * t / T)
    ramp = np.clip((t - t0) / 0.015, 0, 1)[:, None]
    return out * ramp


def _shoebox(dims, src, mic, betas, order, t60s, length, seed, spread=0.18, tail_db=0.0):
    """Image-source early reflections (per-wall reflection coefficients betas = (x0, x1, y0, y1, z0, z1), HF loss per
    order) for two mics `spread` m apart, plus a per-band exponential diffuse tail."""
    n = n_(length); h = np.zeros((order + 1, n, 2), np.float64)
    L = np.array(dims, float); s = np.array(src, float)
    mics = [np.array(mic, float) + [-spread / 2, 0, 0], np.array(mic, float) + [spread / 2, 0, 0]]
    rng = range(-order, order + 1)
    for nx in rng:
        for ny in rng:
            for nz in rng:
                o = abs(nx) + abs(ny) + abs(nz)
                if o > order:
                    continue
                pos = []; amp = 1.0
                for k, nk in enumerate((nx, ny, nz)):
                    pos.append(nk * L[k] + s[k] if nk % 2 == 0 else (nk + 1) * L[k] - s[k])
                    hi_, lo_ = (math.ceil(nk / 2), nk // 2) if nk > 0 else (abs(nk) // 2, math.ceil(abs(nk) / 2))
                    amp *= betas[2 * k] ** lo_ * betas[2 * k + 1] ** hi_
                if amp < 1e-4:
                    continue
                pos = np.array(pos)
                for ch, m in enumerate(mics):
                    d = max(np.linalg.norm(pos - m), 0.3); x = d / 343.0 * SR
                    i = int(x); f = x - i
                    if i + 1 < n:
                        h[o, i, ch] += amp / d * (1 - f); h[o, i + 1, ch] += amp / d * f
    er = np.zeros((n, 2), np.float32)
    for o in range(order + 1):
        er += lp(h[o].astype(np.float32), 16000 / (1 + 0.8 * o), 2) if o else h[o].astype(np.float32)
    first = np.argmax(np.abs(er).sum(1) > 0)
    tl = _tail(length, t60s, seed, t0=first / SR + 0.012)
    e_er = (er[first + n_(0.004):] ** 2).sum()
    tl *= np.sqrt(e_er / ((tl ** 2).sum() + 1e-20)) * 10 ** (tail_db / 20)
    return _unit(er + tl)


def _street_ir(seed=7):
    rng = np.random.default_rng(seed); n = n_(1.8); h = np.zeros((n, 2), np.float32)
    h[0] = 1.0
    for k in range(9):                                  # facade / car / fence reflections
        d = rng.uniform(0.018, 0.17); g = rng.uniform(0.25, 0.55) * (0.02 / d) ** 0.35
        p = rng.uniform(-0.8, 0.8); i = n_(d)
        h[i, 0] += g * np.cos((p + 1) * np.pi / 4) * np.sqrt(2); h[i, 1] += g * np.sin((p + 1) * np.pi / 4) * np.sqrt(2)
    h[1:] = lp(h[1:], 6000, 2)
    f = ir('forest'); f = f[:n] if len(f) >= n else np.pad(f, ((0, n - len(f)), (0, 0)))
    return _unit(h + 0.55 * f * np.sqrt((h ** 2).sum() / ((f ** 2).sum() + 1e-20)))


def ir(name):
    if name in _IR:
        return _IR[name]
    if name in _REC_IR:
        y = LIB.load(_REC_IR[name])
        if name == 'forest':                             # OpenAIR M/S file -> L/R
            m, s = y[:, 0], y[:, 1]; y = np.stack([m + s, m - s], 1)
        if name == 'reactor':
            y = fade(y[:n_(7.0)], 0, 1.5)
        h = y
    elif name == 'hallway':
        h = _shoebox((1.4, 5.5, 2.5), (0.7, 0.35, 1.3), (0.75, 2.6, 1.6), (0.78, 0.78, 0.7, 0.8, 0.72, 0.8), 3,
                     (0.62, 0.55, 0.46, 0.34, 0.24), 1.2, 11)
    elif name == 'living':
        h = _shoebox((4.6, 5.8, 2.6), (2.0, 1.4, 1.2), (2.7, 4.1, 1.4), (0.75, 0.7, 0.75, 0.65, 0.6, 0.8), 3,
                     (0.6, 0.55, 0.45, 0.35, 0.25), 1.2, 12)
    elif name == 'porch':
        h = _shoebox((3.2, 2.6, 2.7), (1.6, 0.9, 1.5), (1.4, 0.4, 1.4), (0.0, 0.0, 0.85, 0.0, 0.8, 0.55), 2,
                     (0.4, 0.35, 0.3, 0.22, 0.15), 0.6, 13, tail_db=-9)
    elif name == 'car':
        h = _shoebox((1.45, 2.3, 1.15), (0.4, 0.6, 0.7), (1.0, 1.6, 0.8), (0.5, 0.5, 0.6, 0.45, 0.35, 0.4), 3,
                     (0.14, 0.12, 0.09, 0.07, 0.05), 0.35, 14)
    elif name == 'street':
        h = _street_ir()
    else:
        raise KeyError(name)
    _IR[name] = _unit(h)
    return _IR[name]


def _conv(x, h):
    x = mono(st(x)).astype(np.float32)
    return np.stack([signal.oaconvolve(x, h[:, 0]), signal.oaconvolve(x, h[:, 1])], 1).astype(np.float32)


def reverb(y, name, wet=0.3, predelay=0.0, dry=1.0, hpf=None):
    y = st(y); h = ir(name)
    src = hp(y, hpf) if hpf else y
    w = _conv(src, h) * wet
    out = np.zeros((len(y) + len(h) + n_(predelay), 2), np.float32)
    out[:len(y)] += y * dry
    place(out, w, n_(predelay))
    return _trim_tail(out)


def _trim_tail(y, thr_db=-75):
    a = np.abs(y).max(1); p = a.max()
    if p <= 0:
        return y[:1]
    idx = np.nonzero(a > p * 10 ** (thr_db / 20))[0]
    end = min(len(y), idx[-1] + n_(0.02))
    return fade(y[:end], 0, 0.02)


# ======================================================================================== perspective spaces
def space(y, kind, seed=0, wet=None):
    """Perspective processing. 'close' near the listener, 'inside' in the hallway, 'outside' heard from inside through
    the closed front door, 'doorbell_mic' through the porch camera's mic (outdoor early reflections, band-limited,
    compressed, mono), 'street' distant outdoors, 'phone', 'radio', 'car' (inside the patrol car), 'dry'."""
    y = st(y)
    if kind in (None, 'dry'):
        return y
    if kind == 'close':
        return reverb(y, 'living', 0.12 if wet is None else wet, 0.002)
    if kind == 'inside':
        return reverb(lp(y, 15000, 1), 'hallway', 0.45 if wet is None else wet, 0.0)
    if kind == 'outside':
        m = mono(y)
        door = eq(lp(m, 1000, 2), ('peak', 160, 5, 1.1), ('peak', 420, 2, 1.5), ('hs', 2200, -9, 0.7))
        leak = bp(m, 1400, 5000, 2) * 0.035           # air gap round the door frame
        d = door + leak
        return width(reverb(d, 'hallway', 0.8 if wet is None else wet, 0.001), 0.6)
    if kind == 'doorbell_mic':
        x = reverb(y, 'porch', 0.35 if wet is None else wet)
        x = mono(reverb(x, 'forest', 0.12, 0.01))
        x = eq(lp(hp(x, 260, 4), 6800, 4), ('peak', 2700, 3.5, 1.2), ('peak', 900, -2, 1.0))
        x = compress(x, db(peak(x)) - 16, 4.0, 0.002, 0.09, makeup=0)
        return st(sat(x, 1.4))
    if kind == 'street':
        return reverb(lp(y, 9000, 1), 'street', 0.6 if wet is None else wet, 0.0, hpf=120)
    if kind == 'phone':
        x = bp(mono(y), 320, 3300, 4); x = sat(compress(x, db(peak(x)) - 14, 3.0, 0.003, 0.1), 1.6)
        return st(x)
    if kind == 'radio':
        x = bp(mono(y), 380, 3200, 4); return st(sat(x, 3.0))
    if kind == 'car':
        return reverb(lp(y, 11000, 1), 'car', 0.35 if wet is None else wet)
    raise KeyError(kind)


# ======================================================================================== sample access, grains, picking
_AC = OrderedDict(); _AC_BYTES = [0]
_GC = None
_RECENT = defaultdict(lambda: deque(maxlen=6))


def reset():
    _RECENT.clear()


def audio(e):
    e = LIB.get(e); k = e['id']
    if k in _AC:
        _AC.move_to_end(k); return _AC[k]
    y = LIB.load(e).astype(np.float32)
    _AC[k] = y; _AC_BYTES[0] += y.nbytes
    while _AC_BYTES[0] > 1.5e9 and len(_AC) > 1:
        _, v = _AC.popitem(last=False); _AC_BYTES[0] -= v.nbytes
    return y


def _gcache():
    global _GC
    if _GC is None:
        p = os.path.join(CACHE, 'grains.json')
        _GC = json.load(open(p)) if os.path.exists(p) else {}
    return _GC


def _gsave():
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, 'grains.json'); tmp = p + '.%d' % os.getpid()
    json.dump(_GC, open(tmp, 'w')); os.replace(tmp, p)


def grains(e, mode='onset', gap=0.25, floor=-40.0, max_len=3.0, min_len=0.03, keep=-24.0):
    """Cut a recording into single events. mode 'onset' (spectral-flux onsets: knocks, steps, keys) or 'phrase'
    (split at gaps >= gap s of near-silence: doorbell phrases, car doors, beeps). Returns [(s0, s1)] in samples.
    Events weaker than `keep` dB under the file's loudest event are dropped. Cached in $S/pov2/cache/sfx/grains.json."""
    e = LIB.get(e)
    key = f"{e['id']}|{mode}|{gap}|{floor}|{max_len}|{min_len}|{keep}"
    gc = _gcache()
    if key in gc:
        return [tuple(g) for g in gc[key]]
    y = mono(audio(e)); hop = 120
    nf = len(y) // hop
    if nf < 4:
        gc[key] = [[0, len(y)]]; _gsave(); return [(0, len(y))]
    fr = y[:nf * hop].reshape(nf, hop)
    env = db(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    env = np.convolve(env, np.ones(3) / 3, 'same')
    noise = np.percentile(env, 10); P = env.max()
    thr = max(P + floor, noise + 6)
    out = []
    if mode == 'phrase':
        act = env > thr; g = int(gap * SR / hop)
        idx = np.nonzero(act)[0]
        if len(idx):
            runs = []; a = idx[0]; b = idx[0]
            for i in idx[1:]:
                if i - b > g:
                    runs.append((a, b)); a = i
                b = i
            runs.append((a, b))
            for a, b in runs:
                out.append((max(0, a * hop - n_(0.004)), min(len(y), (b + 1) * hop + n_(0.03))))
    else:
        import librosa
        o = librosa.onset.onset_detect(y=y, sr=SR, hop_length=256, backtrack=True, units='samples',
                                       wait=max(1, int(gap * SR / 256)), delta=0.08)
        o = sorted(set(int(v) for v in o))
        for k, s0 in enumerate(o):
            nxt = o[k + 1] if k + 1 < len(o) else len(y)
            f0 = s0 // hop; f1 = min(nf, nxt // hop)
            if f1 <= f0 + 1:
                continue
            pk = f0 + int(np.argmax(env[f0:f1]))
            after = np.nonzero(env[pk:f1] < max(env[pk] + floor, noise + 3))[0]
            end = (pk + after[0]) * hop if len(after) else f1 * hop
            end = min(end + n_(0.02), nxt - n_(0.004), s0 + n_(max_len))
            out.append((max(0, s0 - n_(0.003)), end))
    res = []
    for s0, s1 in out:
        s1 = min(s1, s0 + n_(max_len))
        if s1 - s0 < n_(min_len):
            continue
        f0, f1 = s0 // hop, max(s0 // hop + 1, min(nf, s1 // hop))
        if env[f0:f1].max() < P + keep:
            continue
        res.append((int(s0), int(s1)))
    if not res:
        res = [(0, min(len(y), n_(max_len)))]
    gc[key] = [list(r) for r in res]; _gsave()
    return res


def src(serves=None, category=None, tag=None, has=None, nothas=None, epi=None, tags=None):
    """Library entries: Epidemic kept even when flagged; free files dropped if clipped or noisy."""
    out = []
    for e in LIB.entries(category=category, serves=serves, tag=tag):
        isepi = e['source'] == 'epidemic'
        if not isepi and any(q.startswith('clip') or q == 'noise_floor_high' for q in e.get('qc', [])):
            continue
        if has and not any(s in e['id'] for s in has):
            continue
        if nothas and any(s in e['id'] for s in nothas):
            continue
        if epi is not None and isepi != epi:
            continue
        if tags and not set(tags) & set(e.get('tags', [])):
            continue
        out.append(e)
    return out


class Pool:
    """Weighted grain pool across several recordings; picks avoid the last few grains used under the same key."""

    def __init__(self, key, entries, mode='onset', epi_w=3.0, **seg):
        self.key = key; self.items = []; self.w = []
        for e in entries:
            gs = grains(e, mode, **seg)
            wt = (epi_w if e['source'] == 'epidemic' else 1.0) / np.sqrt(len(gs))
            for g in gs:
                self.items.append((e['id'], g[0], g[1])); self.w.append(wt)
        self.w = np.array(self.w, float)

    def __len__(self):
        return len(self.items)

    def pick(self, rng, avoid=3):
        n = len(self.items)
        if n == 0:
            raise KeyError('empty pool ' + self.key)
        rec = _RECENT[self.key]; ban = set(list(rec)[-min(avoid, n - 1):]) if n > 1 else set()
        cand = [i for i in range(n) if self.items[i] not in ban]
        w = self.w[cand]; w = w / w.sum()
        it = self.items[cand[int(rng.choice(len(cand), p=w))]]
        rec.append(it)
        return it

    def get(self, rng, rj=0.03, tilt=1.5, avoid=3, fi=0.002, fo=0.02):
        """One varied grain: random varispeed +-rj, high-shelf tilt +-tilt dB, peak-normalised."""
        eid, a, b = self.pick(rng, avoid)
        y = audio(eid)[a:b]
        y = rate(y, 1 + rng.uniform(-rj, rj)) if rj else y
        if tilt:
            y = eq(y, ('hs', 3000, rng.uniform(-tilt, tilt), 0.7))
        return fade(pnorm(y), fi, fo)


_POOLS = {}


def pool(key, entries_fn, mode='onset', **seg):
    if key not in _POOLS:
        _POOLS[key] = Pool(key, entries_fn(), mode, **seg)
    return _POOLS[key]


def excerpt(e, dur, rng, xfade=1.5, active=True):
    """A dur-second stretch of a recording starting at a random point; loops with equal-power crossfades if short."""
    y = audio(e); n = n_(dur); xf = min(n_(xfade), len(y) // 4)
    if len(y) >= n + n_(0.5):
        off = int(rng.integers(0, len(y) - n))
        return fade(y[off:off + n], 0.05, 0.08)
    out = np.zeros((n + xf, 2), np.float32); i = 0
    win = np.sin(np.linspace(0, np.pi / 2, xf)) ** 2
    while i < n:
        off = int(rng.integers(0, max(1, len(y) // 3)))
        c = y[off:].copy()
        if i > 0:
            c[:xf] *= np.sqrt(win)[:, None]
        c[-xf:] *= np.sqrt(win[::-1])[:, None]
        place(out, c, i)
        i += len(c) - xf
    return fade(out[:n], 0.05, 0.08)


# ======================================================================================== synthesis building blocks
def modal(freqs, decays, amps, dur, seed=0, exc=0.002):
    """Bank of damped resonances excited by a short half-sine pulse (door panel, strike plate, bars)."""
    t = np.arange(n_(dur)) / SR; y = np.zeros_like(t)
    rng = np.random.default_rng(seed)
    for f, d, a in zip(freqs, decays, amps):
        y += a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28)) * np.exp(-t / d)
    k = n_(exc); pulse = np.sin(np.linspace(0, np.pi, k))
    y = np.convolve(y, pulse / pulse.sum(), 'full')[:len(t)]
    return fade(y.astype(np.float32), 0.0008, 0.02)


def sub_boom(f0=58, f1=31, dur=1.6, click=0.15, seed=0):
    t = np.arange(n_(dur)) / SR
    f = f1 + (f0 - f1) * np.exp(-t / (dur * 0.18))
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-t / (dur * 0.33)) * (1 - np.exp(-t / 0.004))
    y = np.tanh(1.6 * y) / np.tanh(1.6)
    if click:
        nz = np.random.default_rng(seed).standard_normal(len(t)) * np.exp(-t / 0.006)
        y = y + click * lp(nz.astype(np.float32), 2500, 2)
    return fade(y.astype(np.float32), 0.0005, 0.1)


def tone(freqs, dur, amps=None, att=0.004, rel=0.02):
    t = np.arange(n_(dur)) / SR; amps = amps or [1.0] * len(freqs)
    y = sum(a * np.sin(2 * np.pi * f * t) for f, a in zip(freqs, amps))
    return fade(np.asarray(y, np.float32) / len(freqs), att, rel)


def noise(dur, seed=0):
    return np.random.default_rng(seed).standard_normal(n_(dur)).astype(np.float32)


def sweep_bp(x, f_start, f_end, q=2.0, steps=48):
    """Time-varying band-pass (piecewise) for whooshes and risers; f follows a geometric path."""
    n = len(x); out = np.zeros_like(x); seg = int(np.ceil(n / steps)); zi = None
    fs = np.geomspace(f_start, f_end, steps) if np.ndim(f_start) == 0 else f_start
    for k in range(steps):
        f = float(np.clip(fs[k], 30, SR * 0.45)); bw = f / q
        sos = signal.butter(2, [max(20, f - bw / 2), min(SR * 0.48, f + bw / 2)], 'bandpass', fs=SR, output='sos')
        a, b = k * seg, min(n, (k + 1) * seg)
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        out[a:b], zi = signal.sosfilt(sos, x[a:b], zi=zi)
    return out


def siren_synth(dur, mode='wail', d0=90.0, speed=0.0, tc=None, seed=0):
    """Electronic siren: band-limited square-ish horn tone with a proper wail (slow rise, longer fall) or yelp, driven
    through a horn response; moving source with exact doppler (emission-time phase), 1/r level and distance
    air absorption, pan following the azimuth, ground bounce. Returns stereo (dry; add 'street' space)."""
    rng = np.random.default_rng(seed); n = n_(dur); t = np.arange(n) / SR
    tc = dur / 2 if tc is None else tc
    x = speed * (t - tc); r = np.sqrt(d0 ** 2 + x ** 2)
    te = t - r / 343.0                                   # emission time
    period = 4.6 if mode == 'wail' else 0.32
    tt = np.arange(int((dur + 2) * SR)) / SR - 1.0
    ph = (tt / period + rng.uniform()) % 1.0
    up = 0.42
    shape = np.where(ph < up, (1 - np.exp(-3.5 * ph / up)) / (1 - np.exp(-3.5)), 1 - ((ph - up) / (1 - up)) ** 0.85)
    f = 640 + (1450 - 640) * shape
    Phi = 2 * np.pi * np.cumsum(f) / SR
    P = np.interp(te, tt, Phi); fi = np.interp(te, tt, f)
    y = np.zeros(n)
    for k in range(1, 12):
        a = (1.0 / k) if k % 2 else 0.35 / k
        y += a * np.sin(k * P) * (k * fi < 9000)
    y = eq(y.astype(np.float32), ('peak', 1500, 5, 0.9), ('peak', 3000, 3, 1.4))
    y = bp(y, 350, 6000, 2)
    y = sat(y, 1.8)
    near, mid_, far = lp(y, 7000, 1), lp(y, 2800, 2), lp(y, 1100, 2)
    dn = np.clip((r - 30) / 300, 0, 1)
    y = (near * (1 - dn) ** 2 + mid_ * 2 * dn * (1 - dn) + far * dn ** 2) * (30.0 / np.maximum(r, 30.0))
    gb = np.roll(y, n_(0.004)) * 0.4                      # ground bounce
    y = y + gb
    az = np.arctan2(x, d0); p = np.sin(az) * 0.75
    a = (p + 1) * np.pi / 4
    return np.stack([y * np.cos(a) * np.sqrt(2), y * np.sin(a) * np.sqrt(2)], 1).astype(np.float32)


def _ring_cad(dur, on, off, f, phase=0.0, rng=None):
    t = np.arange(n_(dur)) / SR; per = on + off
    gate = (((t + phase) % per) < on).astype(np.float32)
    k = n_(0.006); gate = np.convolve(gate, np.ones(k) / k, 'same')
    return (sum(np.sin(2 * np.pi * fr * t) for fr in f) / len(f) * gate).astype(np.float32)


# ======================================================================================== recipes
# each returns (stereo audio, pre_s, level_offset_db, spaced) ; spaced=True means space() was already applied

def _seq(events, extra=0.5):
    """events: [(t_s, stereo)] -> one buffer."""
    end = max(n_(t) + len(y) for t, y in events) + n_(extra)
    out = np.zeros((end, 2), np.float32)
    for t, y in events:
        place(out, st(y), n_(t))
    return out


def r_knock_door(rng, sp, n=3, spacing=0.32, force=0.7, accel=0.0, material='wood', door=1, **_):
    if material == 'glass':
        A = pool('knock_glass', lambda: src('knock_door', has=['glass_panel']), 'onset', gap=0.12, max_len=0.8)
    else:
        A = pool('knock_wood', lambda: src('knock_door', has=['knock_wood', 'plank', 'wood_heavy', 'officedoorknock']),
                 'onset', gap=0.12, max_len=0.9)
    K = pool('knuckle', lambda: src('knock_door', has=['wood_light', 'wood_heavy']), 'onset', gap=0.05, max_len=0.25)
    dr = np.random.default_rng(1000 + int(door))
    modes = np.array([88, 133, 181, 247, 338, 489, 702]) * (1 + 0.05 * dr.standard_normal())
    dec = np.array([0.2, 0.15, 0.12, 0.08, 0.06, 0.04, 0.025])
    amp = np.array([1.0, 0.8, 0.65, 0.45, 0.35, 0.22, 0.12])
    wb, wk, wbody = {'inside': (1.0, 0.35, 1.0), 'outside': (1.0, 0.2, 0.7)}.get(sp, (1.0, 0.8, 0.35))
    ev = []; t = 0.0; force = float(np.clip(force, 0.05, 1.0))
    for k in range(int(n)):
        v = force * (0.9 + 0.12 * (k == n - 1) + 0.05 * rng.standard_normal())
        v = float(np.clip(v, 0.05, 1.1))
        a = A.get(rng, rj=0.04) * v ** 1.2
        kn = hp(K.get(rng, rj=0.06, fo=0.03)[:n_(0.06)], 1800, 2) * 0.6 * v
        body = modal(modes * (1 + 0.01 * rng.standard_normal()), dec * (0.75 + 0.5 * v),
                     amp * v ** 1.6, 0.6, seed=int(rng.integers(1 << 30)))
        thump = lp(noise(0.03, int(rng.integers(1 << 30))) * np.exp(-np.arange(n_(0.03)) / n_(0.004)), 380, 2) * 0.6 * v
        b = np.zeros(max(len(a), len(body)), np.float32); b[:len(body)] += body * 0.5; b[:len(thump)] += thump
        layer = np.zeros((len(b), 2), np.float32); layer[:len(a)] += a * wb
        layer[:len(kn)] += kn * wk; layer += st(pnorm(b, 0.7) * wbody * v)
        ev.append((t, pan(layer, rng.uniform(-0.05, 0.05))))
        t += spacing * (1 - accel) ** k * (1 + 0.07 * rng.standard_normal())
    y = _seq(ev, 0.3)
    return y, 0.003, 9 * np.log10(force / 0.7), False


def r_doorbell_chime(rng, sp, **_):
    P = pool('doorbell', lambda: src('doorbell_chime'), 'phrase', gap=0.5, max_len=4.0, keep=-18)
    y = P.get(rng, rj=0.0, tilt=0.5, fo=0.25)
    # bar-chime body layer in the same pitch area, very low, for weight on small speakers
    body = st(modal([659.3, 1819, 523.3, 1444], [0.9, 0.3, 1.1, 0.35], [1, 0.25, 0, 0], 1.8, 3)) * 0.05
    y = _seq([(0, y), (0, body)], 0.1)
    return y, 0.0, 0.0, False


def _steps(rng, key, entries_fn, n=None, dur=None, rate_=1.8, approach=0.0, creak=0.3, weight=0.7):
    P = pool(key, entries_fn, 'onset', gap=0.18, max_len=0.7, keep=-20)
    C = pool('creak_short', lambda: src(category='sfx/creaks_scrapes', tags=['creak']), 'onset', gap=0.2, max_len=0.9)
    n = int(n or max(1, round((dur or 3.0) * rate_)))
    ev = []; t = 0.0
    for k in range(n):
        g = P.get(rng, rj=0.05, fo=0.04)
        prog = k / max(1, n - 1)
        gdb = (approach * (prog - 0.5) * 9) + (-1.2 if k % 2 else 0) + rng.normal(0, 0.8)
        cut = 9000 * 2 ** (approach * (prog - 0.5) * 1.2)
        g = lp(g, cut, 1) * 10 ** (gdb / 20) * (0.6 + 0.6 * weight)
        g = eq(g, ('ls', 150, (weight - 0.5) * 6, 0.7))
        ev.append((t, pan(g, (0.08 if k % 2 else -0.08))))
        if rng.uniform() < creak:
            ev.append((t + rng.uniform(0.02, 0.09), C.get(rng, rj=0.1)[:n_(0.5)] * 0.18 * 10 ** (gdb / 20)))
        t += (1.0 / rate_) * (1 + 0.05 * rng.standard_normal())
    return _seq(ev, 0.4)


def r_footsteps_porch(rng, sp, n=None, dur=None, rate=1.8, approach=0.0, creak=0.3, weight=0.7, **_):
    y = _steps(rng, 'steps_porch', lambda: src('footsteps_porch', nothas=['civitas__footsteps']), n, dur, rate,
               approach, creak, weight)
    return y, 0.0, 0.0, False


def r_footsteps_wood_inside(rng, sp, n=None, dur=None, rate=1.8, approach=0.0, creak=0.4, weight=0.6, **_):
    y = _steps(rng, 'steps_wood', lambda: src('footsteps_wood_inside', nothas=['barn_reverberant']), n, dur, rate,
               approach, creak, weight)
    return y, 0.0, 0.0, False


def r_car_pass(rng, sp, dist=1.0, direction=1, dur=None, **_):
    E = src('car_pass'); e = E[int(rng.choice(len(E), p=_epi_w(E)))]
    y = audio(e); pk = env_peak_s(y, 0.5)
    pre = min(pk, (dur or 12) / 2); post = min(len(y) / SR - pk, (dur or 10) / 2)
    seg = y[n_(pk - pre):n_(pk + post)]
    if direction < 0:
        seg = seg[:, ::-1]
    if dist > 1:
        seg = lp(seg, 9000 / dist ** 0.7, 2)
    return fade(seg, 0.8, 1.0), pre, -6 * np.log2(max(dist, 0.25)), False


def _epi_w(E, w=3.0):
    p = np.array([w if e['source'] == 'epidemic' else 1.0 for e in E]); return p / p.sum()


def r_car_idle(rng, sp, dur=8.0, **_):
    E = src('car_idle'); e = E[int(rng.integers(len(E)))]
    y = excerpt(e, dur, rng)
    y = eq(y, ('ls', 90, 3, 0.7))
    return y, 0.0, 0.0, False


def _car_door_pools():
    E = src('car_door_close')
    if 'car_close' not in _POOLS:
        P = Pool('car_door', E, 'phrase', gap=0.35, max_len=2.5, keep=-26)
        feats = []
        for it in P.items:
            y = mono(audio(it[0])[it[1]:it[2]])
            lo = peak(lp(y, 250, 4)); feats.append((lo, peak(y)))
        close, opn = Pool.__new__(Pool), Pool.__new__(Pool)
        for q, k in ((close, 'car_close'), (opn, 'car_open')):
            q.key = k; q.items = []; q.w = []
        byfile = defaultdict(list)
        for i, it in enumerate(P.items):
            byfile[it[0]].append(i)
        for f, idx in byfile.items():
            best = max(feats[i][0] for i in idx)
            for i in idx:
                tgt = close if feats[i][0] >= best * 0.5 else opn
                tgt.items.append(P.items[i]); tgt.w.append(1.0)
        for q in (close, opn):
            if not q.items:
                q.items = list(P.items); q.w = [1.0] * len(P.items)
            q.w = np.array(q.w)
        _POOLS['car_close'], _POOLS['car_open'] = close, opn
    return _POOLS['car_open'], _POOLS['car_close']


def r_car_door_open(rng, sp, **_):
    o, _c = _car_door_pools()
    return o.get(rng, rj=0.03, fo=0.08), 0.0, 0.0, False


def r_car_door_close(rng, sp, **_):
    _o, c = _car_door_pools()
    y = c.get(rng, rj=0.03, fo=0.1)
    th = st(modal([62, 95, 140], [0.09, 0.06, 0.04], [1, 0.6, 0.3], 0.4, int(rng.integers(1 << 30)))) * 0.35
    on = onset_s(y, -12)
    return _seq([(0, y), (on, th)], 0.1), on, 0.0, False


def r_siren_far(rng, sp, dur=12.0, dist=1.0, synth=False, mode='wail', speed=0.0, **_):
    if synth or speed:
        y = siren_synth(dur, mode, 90 * dist, speed, seed=int(rng.integers(1 << 30)))
        pre = dur / 2 if speed else 0.0
        return fade(y, 1.0, 1.5), pre, -6 * np.log2(max(dist, 0.25)), False
    E = src('siren_far', nothas=['brazil']); e = E[int(rng.choice(len(E), p=_epi_w(E)))]
    y = excerpt(e, dur, rng)
    if dist > 1:
        y = lp(y, 6000 / dist ** 0.6, 2)
    y = fade(y, min(1.5, dur / 4), min(2.0, dur / 3))
    return y, 0.0, -6 * np.log2(max(dist, 0.25)), False


def _static_pool():
    return pool('static_burst', lambda: src('police_radio_squelch', has=['static_radio', 'lost_signal', 'interference']),
                'onset', gap=0.15, max_len=0.7, keep=-20)


def _click_pool():
    return pool('clicks', lambda: src('radio_click', nothas=['kenney_ui__switch']), 'onset', gap=0.05, max_len=0.2,
                keep=-18)


def _squelch_tail(rng, dur=0.16):
    x = noise(dur + 0.02, int(rng.integers(1 << 30)))
    t = np.arange(len(x)) / SR
    x = bp(x, 600, 4200, 2) * np.where(t < dur, 1.0, np.exp(-(t - dur) / 0.004)) * (0.8 + 0.2 * np.sin(2 * np.pi * 37 * t))
    return fade(x, 0.001, 0.004)


def r_police_radio_squelch(rng, sp, kind='key', **_):
    click = hp(_click_pool().get(rng, rj=0.05), 500, 2) * 0.5
    burst = _static_pool().get(rng, rj=0.04, fo=0.03)
    if kind == 'burst':
        burst = burst[:n_(rng.uniform(0.35, 0.7))]
    else:
        burst = burst[:n_(rng.uniform(0.12, 0.28))]
    tail = st(_squelch_tail(rng, rng.uniform(0.09, 0.16))) * 0.55
    if kind == 'unkey':
        ev = [(0, burst * 0.5), (0.04, tail), (0.2, click)]
    else:
        ev = [(0, click), (0.012, fade(burst, 0.003, 0.03)), (0.012 + len(burst) / SR * 0.8, tail)]
    y = _seq(ev, 0.05)
    y = st(sat(bp(mono(y), 300, 3600, 4), 2.2))
    return y, 0.0, 0.0, False


def r_radio_click(rng, sp, **_):
    c = hp(_click_pool().get(rng, rj=0.06), 300, 2)
    s = st(bp(noise(0.03, int(rng.integers(1 << 30))), 1000, 4000, 2) * np.exp(-np.arange(n_(0.03)) / n_(0.008))) * 0.12
    thock = st(modal([310, 720], [0.012, 0.007], [1, 0.4], 0.06, 2)) * 0.25
    return _seq([(0, c), (0.003, s), (0, thock)], 0.03), 0.0, 0.0, False


def r_radio_static(rng, sp, dur=3.0, amount=0.6, **_):
    E = src('radio_static'); e = E[int(rng.choice(len(E), p=_epi_w(E, 2)))]
    y = excerpt(e, dur, rng, 0.4)
    m = lp(noise(dur, int(rng.integers(1 << 30))), 7, 1); m = m / (peak(m) + 1e-9)
    y = bp(y, 250, 4800, 2) * (1 + 0.35 * amount * st(m)[:len(y)])
    return y, 0.0, 6 * np.log10(max(amount, 0.05) / 0.6), False


def r_bodycam_beep(rng, sp, n=2, **_):
    P = pool('cam_beep', lambda: src('bodycam_beep'), 'phrase', gap=0.06, max_len=0.6, keep=-14)
    ev = []
    for k in range(int(n)):
        b = P.get(rng, rj=0.005, tilt=0.3, fo=0.01)[:n_(0.2)]
        syn = st(tone([2730, 5460], 0.085, [1, 0.12], 0.003, 0.012)) * 0.35
        ev += [(k * 0.16, b * 0.8), (k * 0.16, syn)]
    return _seq(ev, 0.05), 0.0, 0.0, False


def r_phone_ring(rng, sp, dur=None, n=2, kind='ring', **_):
    if kind == 'ringback':
        d = dur or 6 * n - 3.5
        y = st(_ring_cad(d, 2.0, 4.0, [440, 480]) * 0.6)
        y = fade(y, 0.01, 0.05)
        return y, 0.0, -4.0, False
    P = pool('ring', lambda: src('phone_ring'), 'phrase', gap=0.4, max_len=4.0, keep=-15)
    ev = []; t = 0.0
    for k in range(int(n if dur is None else max(1, round(dur / 2.4)))):
        r = P.get(rng, rj=0.0, tilt=0.4, fo=0.06)
        ev.append((t, r)); t += len(r) / SR + 0.55
    return _seq(ev, 0.1), 0.0, 0.0, False


def r_phone_busy(rng, sp, dur=3.0, **_):
    E = src('phone_busy'); y = excerpt(E[0], dur, rng, 0.0)
    return fade(y, 0.005, 0.03), 0.0, 0.0, False


def r_phone_vibrate(rng, sp, n=2, **_):
    P = pool('vibe', lambda: src('phone_vibrate', has=['vibration', 'punchy']), 'phrase', gap=0.15, max_len=1.2, keep=-14)
    ev = []; t = 0.0
    for k in range(int(n)):
        v = P.get(rng, rj=0.01, fo=0.03); ev.append((t, v)); t += max(len(v) / SR + 0.35, 0.9)
    return _seq(ev, 0.1), 0.0, 0.0, False


def r_phone_pickup(rng, sp, **_):
    H = pool('plastic', lambda: src('phone_pickup'), 'onset', gap=0.1, max_len=0.6)
    h = lp(H.get(rng, rj=0.08), 3500, 2) * 0.35
    c1 = hp(_click_pool().get(rng, rj=0.05), 600, 2) * 0.6
    c2 = hp(_click_pool().get(rng, rj=0.05), 600, 2) * 0.4
    line = st(bp(noise(0.35, int(rng.integers(1 << 30))), 400, 3200, 2) * np.exp(-np.arange(n_(0.35)) / n_(0.09))) * 0.05
    return _seq([(0, h), (0.12, c1), (0.165, c2), (0.17, line)], 0.05), 0.12, 0.0, False


def r_mail_slot(rng, sp, paper=False, **_):
    P = pool('mail', lambda: src('mail_slot'), 'onset', gap=0.12, max_len=1.2, keep=-22)
    a = P.get(rng, rj=0.03, fo=0.05)
    b = P.get(rng, rj=0.03, fo=0.05)
    if peak(lp(mono(a), 400, 2)) > peak(lp(mono(b), 400, 2)):
        a, b = b, a                                       # softer one opens, the snap closes
    ev = [(0, a * 0.7)]; t = len(a) / SR * 0.6 + rng.uniform(0.25, 0.5)
    if paper:
        pp = r_paper(rng, sp, dur=1.0)[0] * 0.8
        ev.append((t, pp)); t += 0.8
    ev.append((t, b))
    return _seq(ev, 0.1), 0.0, 0.0, False


def r_paper(rng, sp, dur=1.2, **_):
    E = src('paper', nothas=['pencil', 'book']); e = E[int(rng.choice(len(E), p=_epi_w(E)))]
    y = audio(e); n = n_(dur)
    gs = grains(e, 'phrase', gap=0.2, max_len=8.0, keep=-18)
    s0, s1 = gs[int(rng.integers(len(gs)))]
    if s1 - s0 > n:
        o = int(rng.integers(s0, s1 - n)); seg = y[o:o + n]
    else:
        seg = y[s0:s1]
    return fade(seg, 0.02, 0.1), 0.0, 0.0, False


def r_pen_click(rng, sp, n=1, **_):
    P = pool('pen', lambda: src('pen_click', has=['click', 'clip', 'mech'], nothas=['kenney_ui__switch']), 'onset',
             gap=0.04, max_len=0.15, keep=-16)
    ev = []; t = 0.0
    for k in range(int(n)):
        a = hp(P.get(rng, rj=0.05), 700, 2)
        b = hp(P.get(rng, rj=0.05), 900, 2) * 0.55
        ev += [(t, a), (t + rng.uniform(0.07, 0.12), rate(b, 1.08))]
        t += rng.uniform(0.35, 0.5)
    return _seq(ev, 0.05), 0.0, 0.0, False


def r_key_in_lock(rng, sp, **_):
    J = pool('keys', lambda: src('key_in_lock', has=['keys_jingle_hand', 'keys_jingle']), 'phrase', gap=0.15,
             max_len=0.8, keep=-16)
    I = pool('key_insert', lambda: src('key_in_lock', has=['mechlock']), 'phrase', gap=0.12, max_len=2.2, keep=-16)
    j = J.get(rng, rj=0.04, fo=0.08) * 0.45
    k = I.get(rng, rj=0.03, fo=0.05)
    return _seq([(0, j), (0.18, k)], 0.05), 0.18, 0.0, False


def r_lock_turn(rng, sp, **_):
    P = pool('lock', lambda: src('lock_turn', has=['deadbolt', 'mortise', 'frontdoorlock', 'metallatch', 'doorlockkey']),
             'onset', gap=0.15, max_len=1.0, keep=-14)
    y = P.get(rng, rj=0.03, fo=0.05)
    th = st(modal([182, 330, 610], [0.04, 0.025, 0.012], [1, 0.6, 0.3], 0.15, 4)) * 0.25
    on = onset_s(y, -6)
    return _seq([(0, y), (on, th)], 0.05), on, 0.0, False


def r_chain_lock(rng, sp, action='lock', **_):
    E = src('chain_lock', has=['chain_unlock' if action == 'unlock' else 'chain_lock'])
    y = fade(pnorm(audio(E[0])), 0.002, 0.05)
    y = rate(y, 1 + rng.uniform(-0.03, 0.03))
    C = pool('vsco_chain', lambda: src(category='sfx/design/vsco_misc', tag='chain'), 'onset', gap=0.1, max_len=0.6)
    lay = [(0, y)]
    if len(C):
        lay.append((rng.uniform(0.0, 0.05), C.get(rng, rj=0.05) * 0.15))
    return _seq(lay, 0.05), 0.0, 0.0, False


def r_door_creak(rng, sp, dur=None, slow=1.0, **_):
    D = pool('door_creak', lambda: src('door_creak', category='sfx/door_creak'), 'phrase', gap=0.2, max_len=4.0,
             keep=-18)
    B = pool('bass_creak', lambda: src(category='sfx/creaks_scrapes', tags=['creak', 'bow_noise', 'scrape']),
             'phrase', gap=0.2, max_len=4.0, keep=-18)
    a = D.get(rng, rj=0.04, fo=0.1)
    r = 1.0 / max(0.3, slow)
    if dur:
        r = float(np.clip(len(a) / SR / dur, 0.5, 1.6))
    a = rate(a, r)
    b = B.get(rng, rj=0.03, fo=0.15)
    b = rate(b, semis(-rng.uniform(2, 6)))
    b = b[:len(a) + n_(0.3)] if len(b) > len(a) else b
    return _seq([(0, a), (0.02, lp(b, 3500, 2) * 0.35)], 0.1), 0.0, 0.0, False


def r_breath(rng, sp, kind='nervous', dur=3.0, **_):
    if kind in ('panic', 'panting'):
        E = src('breath', epi=True, has=['panic'] if kind == 'panic' else ['panting'])
        e = E[int(rng.integers(len(E)))]
        y = excerpt(e, dur, rng, 0.3)
        return fade(y, 0.15, 0.3), 0.0, 0.0, False
    if kind == 'gasp':
        P = pool('gasp', lambda: src('breath', has=['gasp', 'freaked', 'attenti'], epi=False), 'phrase', gap=0.2,
                 max_len=2.0, keep=-14)
        return P.get(rng, rj=0.03, fo=0.1), 0.0, 0.0, False
    P = pool('breaths', lambda: src('breath', has=['breath'], nothas=['panic', 'panting']), 'phrase', gap=0.25,
             max_len=2.5, keep=-20)
    ev = []; t = 0.0
    held = kind == 'held'
    while t < dur:
        b = P.get(rng, rj=0.05, fo=0.12)
        ev.append((t, b * (0.6 if held else 1.0)))
        t += len(b) / SR + (rng.uniform(0.8, 1.6) if held else rng.uniform(0.15, 0.5))
    return _seq(ev, 0.1), 0.0, -3.0 if held else 0.0, False


def r_heartbeat(rng, sp, bpm=70, bpm_end=None, dur=6.0, **_):
    P = pool('heart', lambda: src('heartbeat'), 'onset', gap=0.12, max_len=0.35, keep=-16)
    bpm_end = bpm_end or bpm
    ev = []; t = 0.0
    while t < dur:
        b = bpm + (bpm_end - bpm) * (t / max(dur, 1e-3))
        per = 60.0 / b
        lub = lp(P.get(rng, rj=0.02, tilt=0.5, fo=0.04), 900, 2)
        dub = lp(P.get(rng, rj=0.02, tilt=0.5, fo=0.04), 1100, 2) * 0.55
        sub1 = st(sub_boom(62, 44, 0.22, 0.0)) * 0.6
        sub2 = st(sub_boom(75, 52, 0.16, 0.0)) * 0.3
        s2 = 0.27 * per ** 0.5
        ev += [(t, lub), (t, sub1), (t + s2, dub), (t + s2, sub2)]
        t += per
    return _seq(ev, 0.3), 0.0, 0.0, False


def r_whoosh(rng, sp, kind='soft', **_):
    P = pool('whoosh', lambda: src('whoosh'), 'phrase', gap=0.25, max_len=3.0, keep=-15)
    a = P.get(rng, rj=0.05, fo=0.15)
    if kind == 'soft':
        y = lp(a, 5500, 2)
        return y, env_peak_s(y, 0.08), -5.0, False
    b = rate(P.get(rng, rj=0.03, fo=0.15), 0.78)
    L = max(len(a), len(b)); d = L / SR
    nz = noise(d, int(rng.integers(1 << 30)))
    sw = sweep_bp(nz, np.concatenate([np.geomspace(180, 1400, 24), np.geomspace(1400, 250, 24)]), q=1.6)
    env = np.sin(np.linspace(0, np.pi, len(sw))) ** 3
    syn = st(sw * env * 0.5)
    ap = np.linspace(-0.7, 0.7, L)
    ys = _seq([(0, a), (0, lp(b, 3000, 2) * 0.7), (0, syn)], 0.1)
    ys[:L, 0] *= np.sqrt(2) * np.cos((ap + 1) * np.pi / 4); ys[:L, 1] *= np.sqrt(2) * np.sin((ap + 1) * np.pi / 4)
    return ys, env_peak_s(ys, 0.08), 0.0, False


def r_riser(rng, sp, dur=6.0, **_):
    E = src('riser')
    L = [e for e in E if e['dur'] >= dur * 0.8] or E
    e = L[int(rng.integers(len(L)))]
    y = audio(e); pk = env_peak_s(y, 0.15)
    end = min(len(y), n_(pk + 0.06))
    start = max(0, end - n_(dur))
    seg = y[start:end]
    if len(seg) < n_(dur) * 0.9:
        seg = rate(seg, len(seg) / n_(dur))
    seg = fade(seg, len(seg) / SR * 0.35, 0.04)
    d = len(seg) / SR; t = np.arange(len(seg)) / SR
    f = 32 + 26 * (t / d) ** 2
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / d) ** 2.5 * 0.5
    nz = sweep_bp(noise(d, int(rng.integers(1 << 30))), 300, 5000, q=1.4) * (t / d) ** 3 * 0.25
    y = seg + st(sub + nz)[:len(seg)]
    return fade(y, 0.05, 0.03), len(y) / SR, 0.0, False


def r_braam(rng, sp, key='d', **_):
    E = src('braam')
    pref = [e for e in E if e['id'].endswith('_' + str(key).lower())] or E
    e = pref[int(rng.integers(len(pref)))] if rng.uniform() < 0.7 else E[int(rng.integers(len(E)))]
    y = fade(pnorm(audio(e)), 0.002, 0.5)
    f0 = 36.71 if str(key).lower() == 'd' else 41.2
    t = np.arange(n_(2.5)) / SR
    sub = st(np.sin(2 * np.pi * f0 * t) * np.exp(-t / 0.9) * (1 - np.exp(-t / 0.01)) * 0.5)
    y = _seq([(0, y), (0, sub)], 0.0)
    y = reverb(y, 'church', 0.28, 0.02, hpf=150)
    return y, onset_s(y, -20), 0.0, True


def r_impact_hit(rng, sp, size=1.0, **_):
    A = pool('hits', lambda: src('impact_hit', epi=True), 'phrase', gap=0.6, max_len=8.0, keep=-12)
    B = pool('booms', lambda: src(category='score/percussion/bass_drum') + src(category='score/percussion/timpani'),
             'phrase', gap=0.5, max_len=4.0, keep=-12)
    a = A.get(rng, rj=0.02, fo=0.6)
    b = lp(B.get(rng, rj=0.03, fo=0.4), 2500, 2) * 0.45
    sb = st(sub_boom(55 * size ** -0.3, 30, 1.4 * size, 0.1, int(rng.integers(1 << 30)))) * 0.55
    on = onset_s(a, -14)
    y = _seq([(0, a), (on, b), (on, sb)], 0.0)
    y = reverb(y, 'church', 0.22 * size, 0.015, hpf=180)
    return y, onset_s(y, -14), 6 * np.log10(max(size, 0.2)), True


def r_sub_drop(rng, sp, **_):
    E = src('sub_drop', epi=True); e = E[int(rng.integers(len(E)))]
    a = fade(pnorm(audio(e)), 0.002, 0.3)
    s = st(sub_boom(92, 27, 2.6, 0.0)) * 0.6
    on = onset_s(a, -14)
    return _seq([(0, a * 0.8), (on, s)], 0.0), on, 0.0, False


def r_stinger(rng, sp, **_):
    E = src('stinger', epi=True) + src(category='score/stingers')
    e = E[int(rng.choice(len(E), p=_epi_w(E, 2)))]
    a = fade(pnorm(audio(e)), 0.002, 0.4)
    S2 = pool('scrape', lambda: src(category='sfx/creaks_scrapes', tags=['scrape', 'bow_noise']), 'phrase', gap=0.2,
              max_len=2.5, keep=-15)
    sc = lp(S2.get(rng, rj=0.03, fo=0.3), 4000, 2) * 0.18
    y = _seq([(0, a), (0.01, sc)], 0.0)
    y = reverb(y, 'church', 0.2, 0.015, hpf=200)
    return y, onset_s(y, -14), 0.0, True


def r_glitch(rng, sp, dur=0.6, amount=0.7, **_):
    P = pool('glitch', lambda: src('glitch'), 'phrase', gap=0.12, max_len=2.0, keep=-18)
    g = P.get(rng, rj=0.08, fo=0.03)
    n = n_(dur); g = g[:n] if len(g) >= n else np.pad(g, ((0, n - len(g)), (0, 0)))
    out = g.copy()
    k = 0
    while k < n:                                          # stutter: repeat short slices
        L = n_(rng.uniform(0.02, 0.07))
        if rng.uniform() < amount * 0.6 and k + L < n:
            rep = int(rng.integers(2, 6)); s = g[k:k + L]
            for r in range(rep):
                a = k + r * L
                if a + L > n:
                    break
                out[a:a + L] = fade(s, 0.001, 0.002) * (0.9 ** r)
            k += rep * L
        else:
            k += L
    bits = int(8 - 3 * amount); q = 2 ** bits
    out = np.round(out * q) / q
    dec = int(2 + 8 * amount)
    out = np.repeat(out[::dec], dec, axis=0)[:n]
    out = bp(out, 150, 9000, 2)
    return fade(out, 0.002, 0.02), 0.0, 0.0, False


def r_ui_pop(rng, sp, **_):
    P = pool('ui', lambda: src('ui_pop', has=['notification', 'glass_ui', 'confirm', 'kenney_ui']), 'onset', gap=0.06,
             max_len=0.4, keep=-14)
    a = lp(P.get(rng, rj=0.03), 7000, 2) * 0.8
    t = np.arange(n_(0.07)) / SR; f = 700 + 500 * (1 - np.exp(-t / 0.01))
    bl = st(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.018) * 0.35)
    return _seq([(0, a), (0, fade(bl, 0.001, 0.01))], 0.02), 0.0, 0.0, False


def r_typing(rng, sp, dur=3.0, cps=7.0, **_):
    P = pool('keys_typing', lambda: src('typing'), 'onset', gap=0.05, max_len=0.2, keep=-18)
    ev = []; t = 0.0
    while t < dur:
        burst = int(rng.integers(3, 9))
        for _k in range(burst):
            if t >= dur:
                break
            ev.append((t, P.get(rng, rj=0.04, tilt=1.0, fo=0.01) * 10 ** (rng.normal(0, 1.5) / 20)))
            t += rng.gamma(6, 1 / (cps * 6))
        t += rng.uniform(0.12, 0.45)
    return _seq(ev, 0.1), 0.0, 0.0, False


def r_tinnitus(rng, sp, dur=4.0, freq=None, **_):
    E = src('tinnitus'); e = E[int(rng.integers(len(E)))]
    y = excerpt(e, dur, rng, 0.5) * 0.6
    f = freq or rng.uniform(3600, 4600)
    t = np.arange(n_(dur)) / SR
    s = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * (f * 1.003) * t)) * (0.85 + 0.15 * np.sin(2 * np.pi * 0.3 * t))
    y = y[:len(t)] + st(s.astype(np.float32) * 0.25)[:len(y)]
    return fade(y, dur * 0.3, dur * 0.35), 0.0, 0.0, False


def _buzz(dur, rng):
    t = np.arange(n_(dur)) / SR
    y = sum((0.8 / k) * np.sin(2 * np.pi * 120 * k * t + rng.uniform(0, 6)) for k in range(1, 14))
    fl = 1 + 0.25 * (lp(rng.standard_normal(len(t)).astype(np.float32), 3, 1) * 30)
    return bp(np.tanh(2 * y * fl).astype(np.float32), 100, 5000, 2)


def r_ambience_night(rng, sp, dur=30.0, dog=0.5, wind=0.5, buzz=0.5, **_):
    E = src('ambience_night', epi=True)
    base = excerpt(E[int(rng.integers(len(E)))], dur, rng, 3.0)
    F = src('ambience_night', epi=False, has=['cricket', 'night', 'owl'])
    lay = [(0, base)]
    if F:
        f2 = excerpt(F[int(rng.integers(len(F)))], dur, rng, 2.0)
        lay.append((0, f2 * (10 ** (-9 / 20)) * peak(base) / (peak(f2) + 1e-9)))
    D = src('ambience_night', has=['dog', 'bark'])
    if D and dog > 0:
        t = rng.exponential(25 / dog)
        while t < dur - 2:
            e = D[int(rng.integers(len(D)))]
            gs = grains(e, 'phrase', gap=0.4, max_len=3.0, keep=-15)
            s0, s1 = gs[int(rng.integers(len(gs)))]
            b = lp(audio(e)[s0:s1], 2500, 2)
            b = pan(fade(pnorm(b), 0.01, 0.2), rng.uniform(-0.8, 0.8)) * peak(base) * 0.7
            lay.append((t, reverb(b, 'forest', 0.5)))
            t += rng.exponential(25 / dog) + 6
    W = src('ambience_night', has=['wind', 'gust'])
    if W and wind > 0:
        w = excerpt(W[int(rng.integers(len(W)))], dur, rng, 2.0)
        lay.append((0, lp(w, 4000, 2) * peak(base) / (peak(w) + 1e-9) * 0.45 * wind))
    if buzz > 0:
        bz = pan(st(_buzz(dur, rng)), 0.3) * peak(base) * 0.045 * buzz
        lay.append((0, bz))
    y = _seq(lay, 0.0)[:n_(dur)]
    return fade(y, 1.0, 1.5), 0.0, 0.0, False


def r_room_tone(rng, sp, dur=10.0, **_):
    E = src('room_tone', has=['roomtone']) or src('room_tone')
    y = lp(excerpt(E[int(rng.integers(len(E)))], dur, rng, 2.0), 9000, 2)
    return fade(y, 0.5, 0.8), 0.0, 0.0, False


def r_clock_tick(rng, sp, dur=6.0, bpm=60, **_):
    P = pool('clock', lambda: src('clock_tick', category='sfx/clock_tick'), 'onset', gap=0.3, max_len=0.25, keep=-14)
    a = P.get(rng, rj=0.0, tilt=0.0); b = rate(P.get(rng, rj=0.0, tilt=0.0), semis(-1.5))
    ev = []; t = 0.0; k = 0
    while t < dur:
        ev.append((t, (a if k % 2 == 0 else b) * (1 if k % 2 == 0 else 0.8)))
        t += 60.0 / bpm + rng.normal(0, 0.002); k += 1
    return _seq(ev, 0.2), 0.0, 0.0, False


def r_countdown_tick(rng, sp, n=1, spacing=1.0, rise=0.0, **_):
    T = pool('tick', lambda: src('countdown_tick', category='sfx/countdown_tick') + src('clock_tick', category='sfx/clock_tick'),
             'onset', gap=0.2, max_len=0.2, keep=-14)
    B = pool('blip', lambda: src('countdown_tick', category='sfx/ticks_blips'), 'phrase', gap=0.1, max_len=0.5, keep=-12)
    ev = []
    for k in range(int(n)):
        tk = hp(T.get(rng, rj=0.01, tilt=0.5), 400, 2)
        bl = lp(rate(B.get(rng, rj=0.0, tilt=0.0, avoid=0), semis(rise * k)), 3000, 2) * 0.25
        sb = st(sub_boom(70, 50, 0.18, 0.0)) * 0.35
        ev += [(k * spacing, tk), (k * spacing, bl), (k * spacing, sb)]
    return _seq(ev, 0.3), 0.0, 0.0, False


def r_tv_off(rng, sp, **_):
    P = pool('tvoff', lambda: src('tv_off', category='sfx/tv_off'), 'phrase', gap=0.2, max_len=2.0, keep=-15)
    a = lp(P.get(rng, rj=0.05, fo=0.2), 8000, 2)[:n_(1.2)]
    c = hp(_click_pool().get(rng, rj=0.03), 300, 2) * 0.7
    t = np.arange(n_(0.4)) / SR
    f = 60 + 840 * np.exp(-t / 0.08)
    pew = st(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12) * 0.25)
    crack = st(bp(noise(0.3, int(rng.integers(1 << 30))), 2000, 7000, 2) * np.exp(-np.arange(n_(0.3)) / n_(0.05))) * 0.3
    th = st(sub_boom(55, 40, 0.15, 0.0)) * 0.4
    return _seq([(0, c), (0.005, th), (0.01, pew), (0.0, crack), (0.02, fade(a, 0.002, 0.3) * 0.6)], 0.1), 0.0, 0.0, False


def r_crowd_whisper(rng, sp, dur=4.0, density=6.0, **_):
    W = pool('whisper', lambda: src('crowd_whisper', has=['whisper']) + src('breath', has=['shh', 'whisper']), 'phrase',
             gap=0.08, max_len=2.0, keep=-20)
    M = src('crowd_whisper', has=['murmur', 'walla', 'talk', 'crowd', 'restaurant', 'voices'])
    lay = []
    if M:
        m = excerpt(M[int(rng.integers(len(M)))], dur, rng, 1.0)
        m = rate(lp(m, 2500, 2), semis(-2))[:n_(dur)]
        lay.append((0, m * 0.25))
    t = 0.0
    while t < dur:
        g = W.get(rng, rj=0.0, fo=0.04, avoid=4)
        g = rate(g, semis(rng.uniform(-4, 3)))
        if rng.uniform() < 0.25:
            g = fade(g[::-1].copy(), 0.1, 0.01)
        g = pan(g * 10 ** (rng.uniform(-9, 0) / 20), rng.uniform(-0.9, 0.9))
        g = reverb(g, 'hall', rng.uniform(0.1, 0.6))
        lay.append((t, g))
        t += rng.exponential(1.0 / density)
    y = _seq(lay, 0.2)[:n_(dur) + n_(1.0)]
    return fade(y, 0.4, 0.8), 0.0, 0.0, False


RECIPES = {k: globals()['r_' + k] for k in NAMES}


# ======================================================================================== public entry points
def render_event(name, seed=0, space=None, level=0.0, **params):
    """Render one SFX. Returns (stereo float32 at 48 kHz, pre_s)."""
    if name not in RECIPES:
        raise KeyError(f'unknown SFX {name!r}')
    sp = space or params.pop('space', None) or DEFAULT_SPACE[name]
    params.pop('space', None)
    h = int(hashlib.md5(f'{name}|{seed}'.encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(h)
    y, pre, offs, spaced = RECIPES[name](rng, sp, **params)
    y = st(y)
    if not spaced:
        y0 = len(y)
        y = globals()['space'](y, sp, seed)
    target = REF + LEVEL_LU[name] + SPACE_LU.get(sp, 0.0) + offs + float(level)
    bed = name in BEDS or (params.get('dur') and name in ('breath', 'siren_far', 'typing', 'heartbeat'))
    L = lufs_int(y) if bed else mom_max(y)
    if np.isfinite(L) and L > -90:
        y = y * 10 ** ((target - L) / 20)
    cap = 10 ** ((PEAK_CAP[name] + float(level) + offs) / 20)     # short transients: momentary loudness under-reads them
    pk = peak(y)
    if pk > cap:
        y = y * (cap / pk)
    return np.ascontiguousarray(y, np.float32), float(pre)


def render(name, seed=0, space=None, level=0.0, **params):
    """Render one SFX as stereo float32 [n, 2] at 48 kHz (see module docstring for params)."""
    return render_event(name, seed, space, level, **params)[0]


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='render one SFX to a wav')
    ap.add_argument('name'); ap.add_argument('out'); ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--space'); ap.add_argument('--params', default='{}')
    a = ap.parse_args()
    y = render(a.name, a.seed, a.space, **json.loads(a.params))
    sf.write(a.out, y, SR, subtype='FLOAT')
    print(a.name, round(len(y) / SR, 2), 's', 'peak %.1f dBFS' % db(peak(y)), 'Mmax %.1f' % mom_max(y))
