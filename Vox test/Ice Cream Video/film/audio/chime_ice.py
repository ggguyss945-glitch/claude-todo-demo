"""chime_ice.py: HIS CHIME, Mister Shiver's truck song: an ORIGINAL 8-bar music-box melody written for this film (no
melody of any existing song or jingle; never sung, no lyrics, no voices in the tune), and every version the film uses.
It runs on jingle.py's engine (BeatMap with anchors, the music-box tine, celesta, glockenspiel, soft piano, _put, _wow).

The tune (D major, 3/4, 72 bpm: a little too slow; every tine a little out of tune)
    bars 1-2   A4 D5 F#5 | A5 (held) G5 F#5          a sweet rising call (the "three slow notes" are its first three)
    bars 3-4   E5 G5 B5  | A5 (held)                 the same shape a step higher, a half close on A
    bars 5-6   B5 A5 F#5 | G5 E5 C#5                 falling back (A7 under bar 6)
    bars 7-8   D5 F#5 E5 | ( GAP )                   the leading line asks for D5 on the downbeat of bar 8 and it
                                                     NEVER comes: bar 8 is a held silent bar, everything stops
                                                     (the place waiting for the next person)
    harmony    | D | D | Em | A | Bm | A7 | D A7 | - |   one low tine on each downbeat (the cylinder's bass comb)
    tuning     each pitch carries its own fixed error (TUNING, cents: the comb's worn teeth), so the same notes are
               wrong the same way every time it returns; seed varies only the pin timing.

Versions: render(version, anchors=None, tempo=None, seed=0, **kw) -> (stereo float32 48 kHz, info)
    info: beats (time of every beat), note_times, gap (s0, s1) = where the missing note's bar sits in the render
    burst      the cold open: bars 1-4 on the truck speaker, bright and close (under "Who's cold?...")
    three      the first three notes, very slow (40 bpm), thin and far, for under the radio static (1:33)
    far        far away across town: thin (650 Hz-2.6 kHz), wind-smeared (gusting level, pitch smear), a big cold
               distance; the full tune with its gap. wind= 0..1 (default 0.7)
    closer     coming street by street: loops= passes (default 3: Elm, Maple, Cedar), each pass a step nearer
               (thin and wet -> fuller and drier), the gap between passes; loops=1: ONE pass that comes all the way
               from across town to the speaker horn by bar 7 (the film's 1:45 entry)
    gap_time(version, loops, short) -> seconds from a render's start to its gap (music_plan's 'gap_at')
    outside    right outside: full, through the chrome speaker horn on the roof (380 Hz-5 kHz, a 1.6 kHz honk,
               a little drive, the house fronts' slap-back); loops=
    lullaby    softer and slower (52 bpm), an octave down on soft celesta + music box, low-passed, a slow sway;
               loops= (default 2); ends on the same gap
    warped     the night getting worse: amount= 0..1 (default 0.6): the tines drift further out (up to +-55 cents),
               the spring sags (tempo falls 12 % per pass), the third goes flat (F# -> F) in the second pass, wow
    climax     plays (outside), reaches the empty beat and HANGS there: the last tone (E5) freezes into a held,
               trembling cluster that swells for hang= s (default 4.0), then FALLS APART over fall= s (default 3.0):
               the tines detune and sink, the spring unwinds in a rattle, the speaker crackles out
    stinger    two nights later across town: bars 5-8 far and thin, ending on the missing note (wind after it)
    warm       the motif redeemed (porch lights, "Bye, Benny", cocoa, the morning, the outro): 80 bpm, in tune,
               soft piano + celesta + a string pad, and the last note finally PLAYED: D5 on a held D add9;
               loops= (default 1), short=True: bars 5-8 + the resolution only (the SHORT outro)
    bells      his bells hidden in static / under a copied voice: dur= s of scattered chime tines from the tune,
               out of tune, through a narrow band (mix.py 'mimic' and sfx.py 'radio_bells' use it)

CLI: python3 audio/chime_ice.py [versions...]    renders to W/mix/chime_ice/<v>.wav (16-bit, small), checks each
     (loudness, peak, band shares, the gap's depth, the melody found at every note) into chime_check.json and draws
     chime_sheet.png.
"""
import json, os, sys
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sfx as SX                                        # noqa: E402
import jingle as J                                      # noqa: E402  (the engine)

SR = 48000
W = SX.W
OUT = os.path.join(W, 'mix', 'chime_ice')
TEMPO = 72.0
BAR = 3.0
# (beat, length in beats, midi): 3/4, beat 0 = the first note
MELODY = [
    (0.0, 1.0, 69), (1.0, 1.0, 74), (2.0, 1.0, 78),
    (3.0, 2.0, 81), (5.0, 0.5, 79), (5.5, 0.5, 78),
    (6.0, 1.0, 76), (7.0, 1.0, 79), (8.0, 1.0, 83),
    (9.0, 3.0, 81),
    (12.0, 1.0, 83), (13.0, 1.0, 81), (14.0, 1.0, 78),
    (15.0, 1.0, 79), (16.0, 1.0, 76), (17.0, 1.0, 73),
    (18.0, 1.0, 74), (19.0, 1.0, 78), (20.0, 1.0, 76),
]
MISSING = (21.0, 74)                                    # the note that should be there: D5 on bar 8's downbeat
N_BEATS = 24.0                                          # 8 bars; bar 8 (beats 21-24) is the silent gap
BASS = [(0.0, 50), (3.0, 50), (6.0, 52), (9.0, 45), (12.0, 47), (15.0, 45), (18.0, 50), (20.0, 45)]
CHORDS = {0.0: (62, 66, 69), 3.0: (62, 66, 69), 6.0: (64, 67, 71), 9.0: (61, 64, 69), 12.0: (62, 66, 71),
          15.0: (61, 64, 67), 18.0: (62, 66, 69), 20.0: (61, 64, 67)}
# the comb's worn teeth: every pitch wrong by its own fixed amount (cents)
TUNING = {45: -14, 47: 9, 50: -6, 52: 12, 61: 16, 62: -9, 64: 11, 66: 18, 67: -12, 69: 13, 71: -16, 73: 21, 74: -11,
          76: 15, 78: 19, 79: -13, 81: 9, 83: -18, 85: 14, 86: -7}
VERSIONS = ('burst', 'three', 'far', 'closer', 'outside', 'lullaby', 'warped', 'climax', 'stinger', 'warm', 'bells')


def _tune(m, amount=1.0):
    return TUNING.get(m, 10.0) * amount


def _notes(first=0.0, last=N_BEATS):
    return [(b, d, m) for b, d, m in MELODY if first <= b < last]


def _box_pass(bm, rng, buf, t_off=0.0, amount=1.0, octave=0, vel=0.8, bass=True, first=0.0, last=N_BEATS,
              flat3=False, extra_detune=0.0, inst='box'):
    """One pass of the tune into buf, starting t_off s; returns the note times."""
    nt = []
    for b, d, m in _notes(first, last):
        mm = (m - 1 if (flat3 and m % 12 == 6) else m) + 12 * octave
        t = t_off + float(bm(b)) + rng.uniform(-0.02, 0.045)          # the pins are never quite in time
        det = _tune(m, amount) + rng.uniform(-extra_detune, extra_detune)
        v = vel * rng.uniform(0.86, 1.0)
        if inst in ('box', 'both'):
            J._put(buf, t, J.music_box(mm + 12, v, rng, det, 1.15), 1.0, rng.uniform(-0.15, 0.15))
        if inst in ('celesta', 'both'):
            try:
                J._put(buf, t, J.celesta(mm, v * 0.55), 1.0, 0.0)
            except Exception:
                J._put(buf, t, J.music_box(mm, v * 0.6, rng, det, 1.6), 1.0, 0.0)
        nt.append(t)
    if bass:
        for b, r in BASS:
            if first <= b < last:
                t = t_off + float(bm(b)) + rng.uniform(0, 0.03)
                J._put(buf, t, J.music_box(r + 12 * octave + 12, 0.32, rng, _tune(r, amount) * 1.3, 1.5), 1.0, 0.0)
    return nt


def _damp(buf, a, b, floor=0.02, ramp=0.22):
    """The cylinder reaches the missing note and the comb is stopped: every tine still ringing is damped from a (the
    gap's first beat) to b, so the gap is a real hole, not a decay."""
    i0, i1 = int(a * SR), min(len(buf), int(b * SR))
    if i1 <= i0:
        return buf
    k = min(i1 - i0, int(ramp * SR))
    g = np.full(i1 - i0, floor, np.float32)
    g[:k] = floor + (1 - floor) * np.cos(np.linspace(0, np.pi / 2, k)) ** 2
    if i1 < len(buf):
        r = min(int(0.02 * SR), i1 - i0)
        g[-r:] = np.maximum(g[-r:], np.linspace(floor, 1, r))
    buf[i0:i1] *= g[:, None]
    return buf


def _damp_passes(buf, bm, n, t0=0.0, P=None):
    P = P or _pass_len(bm)
    for k in range(n):
        g0 = t0 + k * P + float(bm(MISSING[0]))
        _damp(buf, g0, t0 + (k + 1) * P if k < n - 1 else len(buf) / SR)
    return buf


def _buf(sec):
    return np.zeros((int(sec * SR) + SR, 2), np.float32)


def speaker(y, seed=0, drive=1.6, wet=0.22):
    """The chrome speaker horn at the centre of the roof snowflake: 380 Hz-5 kHz, a 1.6 kHz honk, a little drive, the
    horn's short metal ring, the house fronts' slap-back."""
    m = SX.mono(y)
    m = SX.eq(SX.lp(SX.hp(m, 380, 4), 5000, 4), ('peak', 1600, 4.0, 1.4), ('peak', 900, 2.0, 1.0))
    pk = SX.peak(m) + 1e-9
    m = (np.tanh(drive * m / pk) / np.tanh(drive) * pk).astype(np.float32)
    k = int(0.0011 * SR); ring = np.zeros_like(m); ring[k:] = m[:-k] * 0.25
    m = m + SX.lp(ring, 3000, 2)
    out = SX.reverb(SX.st(m), 'street', wet, 0.008)
    sl = np.zeros_like(out); k2 = int(0.09 * SR); sl[k2:] = out[:-k2] * 0.18
    return out + SX.lp(sl, 2500, 2)


def far_chain(y, seed=0, wind=0.7, lo=650.0, hi=2600.0, wet=0.75):
    """Across town in the cold: thin, smeared by the wind (slow gusting level, a pitch smear), a big cold distance."""
    rng = np.random.default_rng(seed + 91)
    y = J._wow(SX.st(y), depth=0.004 + 0.004 * wind, hz_=0.21, fl=0.001, fl_hz=3.1, seed=seed)
    y = SX.lp(SX.hp(y, lo, 2), hi, 2)
    n = len(y); t = np.arange(n) / SR
    g = np.zeros(n)
    for f, a in ((0.07, 1.0), (0.17, 0.6), (0.41, 0.3)):
        g += a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.3))
    g = 10 ** ((-5.0 * wind * (g / 1.9 + 0.4)) / 20)                # the wind takes it away and brings it back
    y = y * g[:, None].astype(np.float32)
    y = SX.reverb(y, 'hall', wet, 0.06, dry=0.55)
    return SX.lp(y, hi * 1.1, 2)


def _gap_info(bm, t_off=0.0):
    return (t_off + float(bm(MISSING[0])), t_off + float(bm(N_BEATS)))


def _pass_len(bm):
    return float(bm(N_BEATS))


def render(version, anchors=None, tempo=None, seed=0, loops=None, wind=0.7, amount=0.6, hang=4.0, fall=3.0,
           short=False, dur=3.0, far=None, **_):
    v = str(version)
    rng = np.random.default_rng(1000 + int(seed))
    base = {'three': 40.0, 'lullaby': 52.0, 'warm': 80.0}.get(v, TEMPO)
    bm = J.BeatMap(tempo or base, anchors, 0.5)
    info = {'version': v, 'beats': [float(bm(b)) for b in np.arange(0, N_BEATS + 0.5)]}
    P = _pass_len(bm)
    if v == 'burst':
        buf = _buf(float(bm(12.0)) + 3)
        info['note_times'] = _box_pass(bm, rng, buf, 0.0, 1.0, 0, 0.9, True, 0.0, 12.0, inst='both')
        y = speaker(SX.fade(buf, 0.002, 1.2), seed, 1.8, 0.18)
        info['gap'] = None
    elif v == 'three':
        buf = _buf(float(bm(3.0)) + 4)
        info['note_times'] = _box_pass(bm, rng, buf, 0.0, 1.2, 0, 0.8, False, 0.0, 3.0)
        y = far_chain(SX.fade(buf, 0.002, 2.0), seed, 0.4, 500, 3000, 0.6)
        info['gap'] = None
    elif v in ('far', 'stinger'):
        first = 12.0 if v == 'stinger' else 0.0
        t0 = -float(bm(first))
        n = int(loops or 1)
        buf = _buf(n * P + t0 + 5)
        nt = []
        for k in range(n):
            nt += _box_pass(bm, rng, buf, t0 + k * P, 1.1, 0, 0.8, True, first, N_BEATS)
        info['note_times'] = nt
        info['gap'] = _gap_info(bm, t0 + (n - 1) * P)
        _damp_passes(buf, bm, n, t0, P)
        y = far_chain(SX.fade(buf, 0.002, 1.0), seed, float(wind) if v == 'far' else 0.85,
                      700 if v == 'stinger' else 650, 2300 if v == 'stinger' else 2600, 0.8 if v == 'stinger' else 0.75)
        if v == 'stinger':                                       # the wind after the missing note
            w = SX.lp(SX.hp(SX.noise(4.0, seed + 5), 200, 2), 900, 2) * 0.012
            y = np.concatenate([y, np.zeros((SR, 2), np.float32)])
            SX.place(y, SX.st(SX.fade(w, 1.5, 2.0)), int(info['gap'][0] * SR))
    elif v == 'closer' and int(loops or 3) == 1:            # one pass that comes from far away to right outside
        buf = _buf(P + 3)
        nt = _box_pass(bm, rng, buf, 0.0, 1.0, 0, 0.85, True)
        _damp_passes(buf, bm, 1)
        b = SX.fade(buf, 0.002, 0.8)
        yf = far_chain(b, seed, 0.75, 650, 2600, 0.75)
        yn = far_chain(b, seed + 1, 0.15, 380, 4800, 0.3)
        sp = speaker(b, seed, 1.4, 0.3)
        L = min(len(yf), len(yn), len(sp))
        u = np.clip(np.arange(L) / (float(bm(18.0)) * SR), 0, 1)[:, None] ** 1.3   # nearest by bar 7
        y = (yf[:L] * (1 - u) + (0.5 * yn[:L] + 0.5 * sp[:L]) * u) * (10 ** (-14 * (1 - u) / 20))
        info['note_times'] = nt; info['gap'] = _gap_info(bm)
    elif v == 'closer':
        n = int(loops or 3)
        parts, nt = [], []
        for k in range(n):
            buf = _buf(P + 2)
            nt += [x + k * P for x in _box_pass(bm, rng, buf, 0.0, 1.0, 0, 0.85, True)]
            _damp_passes(buf, bm, 1)
            near = (k + 1) / n                                    # Elm, Maple, Cedar: each pass a street nearer
            yk = far_chain(SX.fade(buf, 0.002, 0.8), seed + k, 0.7 * (1 - near) + 0.1,
                           650 - 300 * near, 2600 + 2400 * near, 0.75 - 0.45 * near)
            if near > 0.99:                                       # Cedar: the speaker horn comes through
                sp = speaker(SX.fade(buf, 0.002, 0.8), seed, 1.4, 0.3)
                L = min(len(yk), len(sp)); yk = 0.5 * yk[:L] + 0.5 * sp[:L]
            parts.append((k * P, yk * (10 ** ((-14 * (1 - near)) / 20))))
        y = np.zeros((int((n + 0.3) * P * SR) + 4 * SR, 2), np.float32)
        for t, p in parts:
            SX.place(y, SX.st(p), int(t * SR))
        info['note_times'] = nt; info['gap'] = _gap_info(bm, (n - 1) * P)
    elif v == 'outside':
        n = int(loops or 1)
        buf = _buf(n * P + 3)
        nt = []
        for k in range(n):
            nt += _box_pass(bm, rng, buf, k * P, 1.0, 0, 0.9, True, inst='both')
        info['note_times'] = nt; info['gap'] = _gap_info(bm, (n - 1) * P)
        _damp_passes(buf, bm, n, 0.0, P)
        y = speaker(SX.fade(buf, 0.002, 1.0), seed)
    elif v == 'lullaby':
        n = int(loops or 2)
        buf = _buf(n * P + 4)
        nt = []
        for k in range(n):
            nt += _box_pass(bm, rng, buf, k * P, 0.8, -1, 0.55, True, inst='both')
        _damp_passes(buf, bm, n, 0.0, P)
        y = J._wow(SX.fade(buf, 0.002, 2.0), depth=0.003, hz_=0.18, fl=0.0004, fl_hz=4.0, seed=seed)
        y = SX.reverb(SX.lp(y, 3200, 2), 'living', 0.35, 0.01)
        sway = 1 + 0.12 * np.sin(2 * np.pi * np.arange(len(y)) / SR / (3 * 60 / base))
        y = y * sway[:, None].astype(np.float32)
        info['note_times'] = nt; info['gap'] = _gap_info(bm, (n - 1) * P)
    elif v == 'warped':
        n = int(loops or 2)
        a = float(amount)
        nt, segs = [], []
        t = 0.0
        for k in range(n):
            bmk = J.BeatMap((tempo or base) * (1 - 0.12 * a * k), None, 0.5)
            Pk = _pass_len(bmk)
            buf = _buf(Pk + 3)
            nt += [x + t for x in _box_pass(bmk, rng, buf, 0.0, 1.0 + 2.0 * a, 0, 0.85, True, flat3=(k >= 1),
                                            extra_detune=25 * a)]
            _damp_passes(buf, bmk, 1)
            segs.append((t, buf)); info['gap'] = (t + float(bmk(MISSING[0])), t + Pk)
            t += Pk
        y = np.zeros((int(t * SR) + 4 * SR, 2), np.float32)
        for t0, b in segs:
            SX.place(y, b, int(t0 * SR))
        y = J._wow(y, depth=0.004 + 0.01 * a, hz_=0.27, fl=0.0012, fl_hz=5.5, seed=seed)
        r = 1.0 - 0.08 * a * (np.arange(len(y)) / len(y)) ** 2            # the spring sags late on
        pos = np.cumsum(r); pos = np.clip(pos - pos[0], 0, len(y) - 2); i = pos.astype(np.int64)
        f = (pos - i)[:, None].astype(np.float32); y = y[i] * (1 - f) + y[i + 1] * f
        sc = np.cumsum(r) / SR                                            # times move with the sag
        info['gap'] = tuple(float(np.searchsorted(sc, x)) / SR for x in info['gap'])
        nt = [float(np.searchsorted(sc, x)) / SR for x in nt]
        y = speaker(SX.fade(y, 0.002, 1.0), seed, 1.6 + a, 0.3)
        info['note_times'] = nt
    elif v == 'climax':
        buf = _buf(P + float(hang) + float(fall) + 4)
        nt = _box_pass(bm, rng, buf, 0.0, 1.0, 0, 0.9, True, inst='both')
        g0 = float(bm(MISSING[0]))
        _damp(buf, g0, g0 + 0.6, floor=0.25)              # the comb stops... but one tone will not let go
        hold = _hang(float(hang), rng, seed)                              # E5 frozen in the empty beat
        SX.place(buf, hold, int((float(bm(20.0)) + 0.35) * SR))
        fa = _fall_apart(float(fall), rng, seed)
        SX.place(buf, fa, int((g0 + float(hang)) * SR))
        y = speaker(SX.fade(buf, 0.002, 0.5), seed, 1.7, 0.2)
        info['note_times'] = nt; info['gap'] = (g0, g0 + float(hang)); info['fall'] = (g0 + float(hang),
                                                                                       g0 + float(hang) + float(fall))
    elif v == 'warm':
        y, info2 = _warm(bm, rng, seed, int(loops or 1), bool(short))
        info.update(info2)
    elif v == 'bells':
        y = bells(float(dur), seed)
        info['note_times'] = []; info['gap'] = None
    else:
        raise KeyError(f'unknown chime version {version!r}')
    y = SX.st(np.asarray(y, np.float32))
    pk = SX.peak(y)
    if pk > 0.89:
        y = y * (0.89 / pk)
    return y, info


def gap_time(version, loops=1, short=False, tempo=None):
    """Seconds from the start of a render (no anchors) to its gap (beat 21 of the last pass); for 'warm' the played
    last note; for 'stinger' / short warm the render starts at beat 12."""
    v = str(version)
    base = tempo or {'three': 40.0, 'lullaby': 52.0, 'warm': 80.0}.get(v, TEMPO)
    spb = 60.0 / base
    first = 12.0 if (v == 'stinger' or (v == 'warm' and short)) else 0.0
    n = max(1, int(loops or 1)) if v in ('far', 'outside', 'lullaby', 'warm', 'closer') else 1
    return (n - 1) * N_BEATS * spb + (MISSING[0] - first) * spb


def _hang(sec, rng, seed):
    """The tune stuck in the empty beat: E5 (the last note played) frozen as a trembling cluster of three detuned
    tines re-struck faster and faster, swelling, never resolving to D."""
    n = int((sec + 1.0) * SR); out = np.zeros((n, 2), np.float32)
    t = 0.0; k = 0
    while t < sec:
        g = 0.35 + 0.65 * (t / sec)
        for m, c in ((76, 15), (76, -22), (75, 30)):
            J._put(out, t + rng.uniform(0, 0.02), J.music_box(m + 12, 0.45 * g, rng, c + rng.uniform(-8, 8), 0.7), 1.0,
                   rng.uniform(-0.3, 0.3))
        t += max(0.09, 0.42 * (1 - t / sec) ** 1.4)
        k += 1
    tt = np.arange(n) / SR
    tone = 0.05 * np.sin(2 * np.pi * J.hz(76 + 12) * 2 ** (15 / 1200) * tt) * np.clip(tt / sec, 0, 1) ** 1.5
    tone *= (1 + 0.5 * np.sin(2 * np.pi * 7.0 * tt))
    out += SX.st(tone.astype(np.float32)) * (tt < sec + 0.2)[:, None]
    return SX.fade(out, 0.002, 0.25)


def _fall_apart(sec, rng, seed):
    """It falls apart: the tines detune and sink in scattered, slowing strikes, the spring unwinds in a rattle,
    the speaker crackles out."""
    n = int((sec + 1.5) * SR); out = np.zeros((n, 2), np.float32)
    for k in range(int(10 + 8 * sec)):
        u = rng.uniform(0, 1) ** 0.8; t = u * sec
        m = int(rng.choice([69, 74, 78, 81, 76, 73]))
        J._put(out, t, J.music_box(m + 12 - int(10 * u), 0.5 * (1 - 0.7 * u), rng, rng.uniform(-80, 80) - 300 * u, 0.6),
               1.0, rng.uniform(-0.5, 0.5))
    tt = np.arange(n) / SR
    rate = 32 * np.exp(-tt / (sec * 0.45)) + 2
    ph = np.cumsum(rate) / SR
    clicks = (np.mod(ph, 1.0) < 0.06).astype(np.float32) * np.exp(-tt / sec)
    rat = SX.bp(SX.st(clicks * SX.mono(SX.noise((n / SR), seed + 3))[:n]), 900, 5000, 2) * 0.5
    out += rat[:n]
    cr = SX.mono(SX.noise(n / SR, seed + 4))[:n] * (rng.uniform(0, 1, n) > 0.997) * np.clip(tt / sec, 0, 1)
    out += SX.st(SX.hp(cr.astype(np.float32), 1500, 2)) * 0.35
    return SX.fade(out, 0.002, 0.8)


def _warm(bm, rng, seed, loops=1, short=False):
    """The motif redeemed: in tune, soft piano + celesta, a slow string pad, and the missing D finally played."""
    first = 12.0 if short else 0.0
    t0 = -float(bm(first))
    P = _pass_len(bm)
    end = t0 + loops * P + 7.0
    buf = np.zeros((int(end * SR) + SR, 2), np.float32)
    nt = []
    for k in range(loops):
        off = t0 + k * P
        for b, d, m in _notes(first, N_BEATS):
            t = off + float(bm(b)) + rng.uniform(0, 0.012)
            try:
                J._put(buf, t, J.low_piano(m, 0.55 * rng.uniform(0.9, 1.0), k), 1.0, -0.1)
            except Exception:
                J._put(buf, t, J.music_box(m, 0.5, rng, 0, 1.6), 1.0, -0.1)
            try:
                J._put(buf, t + 0.01, J.celesta(m + 12, 0.22), 1.0, 0.15)
            except Exception:
                pass
            nt.append(t)
        for b, r in BASS:
            if b >= first:
                try:
                    J._put(buf, off + float(bm(b)), J.low_piano(r - 12, 0.35, 1), 1.0, 0.0)
                except Exception:
                    pass
        for b, ch in CHORDS.items():                                        # the string pad under every bar
            if b >= first:
                bl = float(bm(min(N_BEATS, b + 3.0)) - bm(b)) + 0.6
                J._put(buf, off + float(bm(b)), _pad([c - 12 for c in ch], bl, 0.05), 1.0, 0.0)
    tg = t0 + (loops - 1) * P + float(bm(MISSING[0]))                       # the last note, finally played
    try:
        J._put(buf, tg, J.low_piano(74, 0.6, 2), 1.0, -0.1)
        J._put(buf, tg + 0.012, J.celesta(86, 0.3), 1.0, 0.15)
        J._put(buf, tg, J.low_piano(50, 0.4, 2), 1.0, 0.0)
    except Exception:
        J._put(buf, tg, J.music_box(74, 0.6, rng, 0, 2.0), 1.0, 0.0)
    J._put(buf, tg, _pad([50, 57, 62, 64, 66], 6.0, 0.07), 1.0, 0.0)          # D add9, held
    nt.append(tg)
    y = SX.reverb(SX.fade(buf, 0.002, 2.5), 'recital', 0.22, 0.01)
    return y, {'note_times': nt, 'gap': None, 'resolved_at': tg}


def _pad(midis, dur, vel):
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.zeros(n)
    for m in midis:
        for d in (-6, 0, 7):
            f = J.hz(m) * 2 ** (d / 1200)
            y += np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)
    y = y / (len(midis) * 3)
    env = np.minimum(1, t / 0.8) * np.minimum(1, (dur - t) / 1.2).clip(0, 1)
    return SX.st(SX.lp((y * env * vel).astype(np.float32), 1800, 2))


def bells(dur=3.0, seed=0, band=(900.0, 4200.0)):
    """His bells leaking under a copy or hidden in the static: scattered tines of the tune (its own wrong tuning),
    soft, a narrow band, coming and going."""
    rng = np.random.default_rng(seed + 77)
    n = int((dur + 2.0) * SR); out = np.zeros((n, 2), np.float32)
    t = rng.uniform(0, 0.2)
    seq = [m for _, _, m in MELODY]
    k = int(rng.integers(0, len(seq)))
    while t < dur:
        m = seq[k % len(seq)]; k += 1
        J._put(out, t, J.music_box(m + 12, rng.uniform(0.4, 0.8), rng, _tune(m) * 1.5, 0.8), 1.0, rng.uniform(-0.3, 0.3))
        t += rng.uniform(0.28, 0.55)
    y = SX.lp(SX.hp(out, band[0], 2), band[1], 2)
    tt = np.arange(len(y)) / SR
    y = y * (0.6 + 0.4 * np.sin(2 * np.pi * 0.6 * tt + rng.uniform(0, 6)))[:, None].astype(np.float32)
    return SX.fade(y, 0.05, 0.6)


# ================================================================================================== checks
def _rms_db(x):
    return float(20 * np.log10(np.sqrt(np.mean(np.square(x))) + 1e-12))


def check(v, y, info):
    m = SX.mono(y)
    r = {'dur': round(len(y) / SR, 2), 'lufs': round(SX.lufs_int(y), 1) if len(y) > SR else None,
         'peak_db': round(float(SX.db(SX.peak(y))), 1)}
    S = np.abs(np.fft.rfft(m[:SR * 60] * np.hanning(min(len(m), SR * 60))))
    f = np.fft.rfftfreq(min(len(m), SR * 60), 1 / SR); P = S ** 2
    tot = P.sum() + 1e-12
    r['low_mid_high_pct'] = [round(100 * P[f < 250].sum() / tot, 1), round(100 * P[(f >= 250) & (f < 4000)].sum() / tot, 1),
                             round(100 * P[f >= 4000].sum() / tot, 1)]
    r['centroid_hz'] = int((f * P).sum() / tot)
    g = info.get('gap')
    if g:                                      # the gap: the level of the missing note's first beat vs the bar before
        a, b = int(g[0] * SR) + int(0.25 * SR), int(g[0] * SR) + int(0.85 * SR)
        pre = m[max(0, int(g[0] * SR) - int(1.6 * SR)):int(g[0] * SR) - int(0.1 * SR)]
        if b < len(m) and len(pre):
            r['gap_db_rel_bar7'] = round(_rms_db(m[a:b]) - _rms_db(pre), 1)
            # no new onset in the gap: the energy only decays (the 50 ms RMS in the gap never rises 3 dB)
            seg = m[a:b]; hop = int(0.05 * SR)
            e = [_rms_db(seg[i:i + hop]) for i in range(0, len(seg) - hop, hop)]
            r['gap_new_onset'] = bool(any(e[i + 1] - e[i] > 3 for i in range(len(e) - 1)))
    # the melody: the strongest partial near each expected note, 40-200 ms after its time
    if info.get('note_times') and v not in ('bells', 'warped', 'climax', 'closer'):
        exp = [mm for _, _, mm in MELODY if mm] if v not in ('stinger',) else [mm for b, _, mm in MELODY if b >= 12]
        if v == 'burst':
            exp = [mm for b, _, mm in MELODY if b < 12]
        if v == 'three':
            exp = exp[:3]
        if v == 'lullaby':
            exp = [mm - 12 for mm in exp]
        ok = 0; cents = []
        nts = info['note_times'][:len(exp)]
        for t, mm in zip(nts, exp):
            a = int((t + 0.04) * SR); seg = m[a:a + int(0.16 * SR)]
            if len(seg) < 1000:
                continue
            Sx = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), 8 * len(seg))); fx = np.fft.rfftfreq(8 * len(seg), 1 / SR)
            best = None
            for oc in (0, 12):
                f0 = J.hz(mm + oc); k = (fx > f0 * 0.94) & (fx < f0 * 1.06)
                if k.any():
                    i = np.argmax(Sx[k]); val = Sx[k][i]
                    if best is None or val > best[0]:
                        best = (val, fx[k][i], f0)
            if best:
                c = 1200 * np.log2(best[1] / best[2]); cents.append(c)
                ok += abs(c) < 60
        r['melody_found'] = f'{ok}/{len(nts)}'
        r['detune_cents_mean_abs'] = round(float(np.mean(np.abs(cents))), 1) if cents else None
    if v == 'warm' and info.get('resolved_at'):
        a = int((info['resolved_at'] + 0.03) * SR); seg = m[a:a + int(0.3 * SR)]
        Sx = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))); fx = np.fft.rfftfreq(len(seg), 1 / SR)
        k = (fx > 280) & (fx < 310)
        r['last_note_D5_db_rel_peak'] = round(float(20 * np.log10(Sx[k].max() / (Sx[(fx > 100) & (fx < 2000)].max() + 1e-9))), 1)
    return r


def sheet(names, out=OUT):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(len(names), 1, figsize=(12, 1.5 * len(names)), dpi=90)
    for ax, nm in zip(np.atleast_1d(axs), names):
        y, _ = sf.read(os.path.join(out, nm + '.wav'), dtype='float32', always_2d=True)
        m = y.mean(1)
        ax.specgram(m, NFFT=2048, Fs=SR, noverlap=1536, cmap='magma', vmin=-120)
        ax.set_ylim(100, 8000); ax.set_yscale('log'); ax.set_title(nm, fontsize=8, loc='left'); ax.tick_params(labelsize=6)
    fig.tight_layout(); fig.savefig(os.path.join(out, 'chime_sheet.png')); plt.close(fig)


def main():
    names = [a for a in sys.argv[1:] if not a.startswith('-')] or list(VERSIONS)
    os.makedirs(OUT, exist_ok=True)
    pj = os.path.join(OUT, 'chime_check.json')
    res = json.load(open(pj)) if os.path.exists(pj) else {}
    kw = {'closer': {'loops': 3}, 'warped': {'amount': 0.7}, 'climax': {'hang': 4.0, 'fall': 3.0}, 'bells': {'dur': 4.0},
          'lullaby': {'loops': 2}}
    for v in names:
        y, info = render(v, seed=3, **kw.get(v, {}))
        sf.write(os.path.join(OUT, v + '.wav'), y, SR, subtype='PCM_16')
        res[v] = check(v, y, info)
        print(v, json.dumps(res[v]), flush=True)
    json.dump(res, open(pj, 'w'), indent=1)
    sheet([v for v in VERSIONS if os.path.exists(os.path.join(OUT, v + '.wav'))])
    print('wrote', OUT)


if __name__ == '__main__':
    main()
