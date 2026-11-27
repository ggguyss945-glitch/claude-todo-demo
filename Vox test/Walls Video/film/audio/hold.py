"""hold.py: the HOLD MUSIC of "If Your Doctor Calls At 3 AM... DON'T ASK WHAT THEY FOUND", an ORIGINAL 8-bar lounge
tune written for this film (no melody of any existing song), and every version the film uses. It is the film's
returning, warping tune (the owner's trick: the 1974 show theme in the dummy film, the Pemberton's jingle in the
Bunnyman film): the sound of being put on hold, of "it can wait".

The tune (F major, 4/4, 72 bpm: a lounge tune played a little too slowly; light swing 56/44; F major shares every
note with the score's D minor, so it sits on the dark bed without a clash)
    bar 1  Fmaj7  E5 . D5 C5 A4          the hook: a sigh down the chord ("please... hold...")
    bar 2  Dm7    C5 . A4 F4 . .         and down to the floor
    bar 3  Gm7    Bb4 D5 F5 E5 D5        it lifts, hopeful
    bar 4  C7     E5 . G4 C5 . .         a question left open on C (the dominant): still waiting
    bar 5  Fmaj7  E5 . D5 C5 A4          the hook again
    bar 6  Am7 D7 C5 E5 D5 C5            a turn that almost goes somewhere
    bar 7  Gm7 C7 Bb4 D5 C5 Bb4 G4       and gives up
    bar 8  F6     A4 . . .               home, on the third: polite, patient, endless (it loops)
Harmony | Fmaj7 | Dm7 | Gm7 | C7 | Fmaj7 | Am7 D7 | Gm7 C7 | F6 |. Instruments (synthesised): soft vibraphone melody
(motor tremolo), an 80s tine e-piano comping the chords on beats 1 and the "and" of 2, a round synth bass (root /
fifth), brushes (a swish on 2 and 4, a soft tap on the off-beats) and a brushed kick; a pad for the warm version.

Versions (render(version, seed=, **kw) -> (stereo float32 at 48 kHz, info); info['beats'] = every beat's time, info
['note_times'] = every melody note's onset)
    studio      the clean lounge mix (the source of the others)
    phone_1979  1979: the hold line Grandma heard: telephone band 300-3400 Hz, carbon-mic grit, line crackle and
                hum, a slow wow (the cold open's call and the 1979 flashback)
    landline    3 AM: the kitchen landline: thin, tired and slightly flat (-35 cents, tempo x0.94), telephone band, hiss
                (the unplugged phone that rings anyway, the receiver on the counter all night)
    rooms       the same tune also coming from the hallway, the living room, Grandpa's chair: three copies in three
                rooms (different delays, darker and wetter the further), very wide
    hum         Grandma humming it, rocking Milo on the kitchen floor (the cast's 'G' voice, audio/voicesynth.py),
                slow, a little flat, phrases 0-1 by default
    pulse       the pulse count: the tune slows and sags at each count (anchors counts=[t1, t2, t3] s; speeds
                [1.0, 0.8, 0.62, 0.45]), a clean varispeed (the pitch sags with the speed, no artefacts); score.py
                cuts it dead on the narrator's first question (stop 'cut')
    ceiling     the waiting room's ceiling speaker: a small cone in a hard, low room, 400 Hz-4.5 kHz, a touch slow
    car_radio   the car radio, warped: AM band, static, a seasick wow, detuned, in the car (Doctor Later in the back seat)
    far_hall    the final reveal: faint, far down the empty hospital hall (dark, mostly reverb)
    warm        the motif redeemed (the outro): brighter (84 bpm), straight, warm pad, celesta doubling the vibes,
                no warping, a gentle ending on F6 (transpose= semitones to sit on the outro track's key)
CLI: python3 hold.py [versions...]  -> W/mix/hold/<version>.wav + hold_check.json + hold_sheet.png
"""
import json, os, sys
import numpy as np, soundfile as sf
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sfx as SX                      # noqa: E402
import jingle as JG                   # noqa: E402  (BeatMap, tine_ep, synth_bass, _put, _wow, _level, celesta)

SR = 48000
W = SX.W
OUT = os.path.join(W, 'mix', 'hold')
TEMPO = 72.0
SWING = 0.56
# (beat, duration in beats, midi) -- 8 bars of 4/4
MELODY = [(0.0, 1.5, 76), (1.5, 0.5, 74), (2.0, 1.0, 72), (3.0, 1.0, 69),
          (4.0, 1.5, 72), (5.5, 0.5, 69), (6.0, 2.0, 65),
          (8.0, 1.0, 70), (9.0, 1.0, 74), (10.0, 1.0, 77), (11.0, 0.5, 76), (11.5, 0.5, 74),
          (12.0, 1.5, 76), (13.5, 0.5, 67), (14.0, 2.0, 72),
          (16.0, 1.5, 76), (17.5, 0.5, 74), (18.0, 1.0, 72), (19.0, 1.0, 69),
          (20.0, 1.0, 72), (21.0, 1.0, 76), (22.0, 1.0, 74), (23.0, 1.0, 72),
          (24.0, 1.0, 70), (25.0, 0.5, 74), (25.5, 0.5, 72), (26.0, 1.0, 70), (27.0, 1.0, 67),
          (28.0, 3.0, 69)]
# (beat, root midi, chord tones as semitones over the root), bass (beat, midi)
CHORDS = [(0, 53, (4, 7, 11, 16)), (4, 50, (3, 7, 10, 15)), (8, 55, (3, 7, 10, 14)), (12, 48, (4, 7, 10, 16)),
          (16, 53, (4, 7, 11, 16)), (20, 57, (3, 7, 10)), (22, 50, (4, 7, 10)), (24, 55, (3, 7, 10)),
          (26, 48, (4, 7, 10)), (28, 53, (4, 7, 9, 16))]
BASS = [(0, 41), (2, 48), (4, 38), (6, 45), (8, 43), (10, 50), (12, 36), (14, 43), (16, 41), (18, 48), (20, 45),
        (22, 38), (24, 43), (26, 36), (28, 41), (30, 48)]
N_BEATS = 32.0
PHRASES = {0: (0, 8), 1: (8, 16), 2: (16, 24), 3: (24, 32)}
VERSIONS = ('studio', 'phone_1979', 'landline', 'rooms', 'hum', 'pulse', 'ceiling', 'car_radio', 'far_hall', 'warm')


def hz(m):
    return 440.0 * 2.0 ** ((np.asarray(m, float) - 69.0) / 12.0)


# ================================================================================================== instruments
def vibes(midi, vel, dur, rng, trem=5.2):
    """A soft vibraphone bar: fundamental + the tuned 4th and 10th partials, a felt-mallet attack, motor tremolo."""
    f = hz(midi); L = min(dur + 1.6, 4.0)
    t = np.arange(int(L * SR)) / SR
    y = (np.sin(2 * np.pi * f * t) * np.exp(-t / 2.2) + 0.12 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t / 0.35)
         + 0.03 * np.sin(2 * np.pi * 10 * f * t) * np.exp(-t / 0.08))
    y *= 1 - 0.28 * (0.5 + 0.5 * np.sin(2 * np.pi * trem * t + rng.uniform(0, 6)))
    y *= np.clip(t / 0.004, 0, 1) * np.clip((dur + 0.5 - t) / 0.5, 0, 1) ** 1.5      # dampened after the note
    return (y * vel).astype(np.float32)


def pad(midis, dur, vel=0.2):
    """A warm detuned saw pad (for the warm version), low-passed."""
    L = dur + 0.8; t = np.arange(int(L * SR)) / SR
    y = np.zeros_like(t)
    for m in midis:
        for d in (-0.07, 0.0, 0.07):
            ph = 2 * np.pi * hz(m + d) * t
            y += sum(np.sin(k * ph) / k for k in range(1, 6))
    env = np.clip(t / 0.35, 0, 1) * np.clip((L - t) / 0.8, 0, 1)
    y = SX.lp(y.astype(np.float32), 2200, 2)
    return (y / (len(midis) * 3) * env * vel).astype(np.float32)


def brush(kind, vel, rng):
    """'swish' (a brush swept across the snare head, on 2 and 4) or 'tap' (a light off-beat tap)."""
    if kind == 'swish':
        n = int(0.32 * SR); t = np.arange(n) / SR
        z = SX.bp(SX.noise(0.32, int(rng.integers(1 << 30))), 1800, 7000, 2)
        env = np.clip(t / 0.06, 0, 1) * np.exp(-np.maximum(0, t - 0.06) / 0.09)
    else:
        n = int(0.09 * SR); t = np.arange(n) / SR
        z = SX.bp(SX.noise(0.09, int(rng.integers(1 << 30))), 2500, 8000, 2)
        env = np.clip(t / 0.002, 0, 1) * np.exp(-t / 0.025)
    return (z[:n] * env * vel).astype(np.float32)


def soft_kick(vel):
    t = np.arange(int(0.25 * SR)) / SR
    f = 52 + 40 * np.exp(-t / 0.02)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.09) * vel).astype(np.float32)


# ================================================================================================== arrangement
def arrange(bm, loops=1, seed=0, phrases=(0, 1, 2, 3), drums=True, warm=False, transpose=0):
    """The tune for `loops` times round (phrases selects bars: a looped hold line plays all four). Returns
    (stereo, beat times, note times)."""
    rng = np.random.default_rng(seed)
    sel_b = [b for p in phrases for b in range(*PHRASES[p])]
    beat_list = []
    for k in range(loops):
        beat_list += [k * N_BEATS + b for b in sel_b]
    # compress the selected beats onto a continuous timeline (missing phrases are skipped)
    beat_pos = {b: i for i, b in enumerate(beat_list)}
    nb = len(beat_list)
    end = float(bm(nb + 3.5))
    buf = np.zeros((int((end + 4.0) * SR), 2), np.float32)
    put = JG._put
    note_times = []
    tr = int(transpose)
    for k in range(loops):
        for b, d, m in MELODY:
            bb = k * N_BEATS + int(b)
            if bb not in beat_pos:
                continue
            pb = beat_pos[bb] + (b - int(b))
            t0 = float(bm(pb)); dur = float(bm(pb + d)) - t0
            note_times.append(t0)
            vel = 0.55 + 0.1 * rng.uniform()
            put(buf, t0 + rng.uniform(0, 0.012), vibes(m + tr, vel, dur, rng), 0.75, -0.12)
            if warm:
                put(buf, t0, JG.celesta(m + tr + 12, 0.25), 0.5, 0.15)
        for i, (b, root, ivs) in enumerate(CHORDS):
            bb = k * N_BEATS + b
            if bb not in beat_pos:
                continue
            b1 = CHORDS[i + 1][0] if i + 1 < len(CHORDS) else N_BEATS
            pb = beat_pos[bb]
            span = b1 - b
            hits = [0.0, 1.5] if span <= 2 else [0.0, 1.5, 2.5 if warm else 3.0]
            for h in hits:
                if h >= span:
                    continue
                t0 = float(bm(pb + h)); dd = float(bm(pb + min(span, h + 1.0))) - t0
                for iv in ivs:
                    put(buf, t0 + rng.uniform(0, 0.008), JG.tine_ep(root + iv + tr + 12, 0.16, dd, rng), 0.6,
                        0.25 if iv % 2 else -0.25)
            if warm:
                t0 = float(bm(pb)); dd = float(bm(pb + span)) - t0
                put(buf, t0, pad([root + iv + tr + 12 for iv in (0,) + tuple(ivs[:3])], dd), 0.9, 0.0)
        for b, m in BASS:
            bb = k * N_BEATS + b
            if bb not in beat_pos:
                continue
            pb = beat_pos[bb]
            t0 = float(bm(pb)); dd = float(bm(pb + 1.8)) - t0
            put(buf, t0, JG.synth_bass(m + tr, 0.42, dd), 0.9, 0.0)
        if drums:
            for b in range(int(N_BEATS)):
                bb = k * N_BEATS + b
                if bb not in beat_pos:
                    continue
                pb = beat_pos[bb]
                if b % 2 == 1:
                    put(buf, float(bm(pb)), brush('swish', 0.07, rng), 1.0, 0.2)
                if b % 4 == 0:
                    put(buf, float(bm(pb)), soft_kick(0.22), 1.0, 0.0)
                put(buf, float(bm(pb + 0.5)), brush('tap', 0.045 + 0.02 * rng.uniform(), rng), 1.0, 0.35)
    beats = [float(bm(i)) for i in range(nb + 1)]
    y = SX.reverb(buf[:int((end + 3.0) * SR)], 'living', 0.16 if not warm else 0.22, 0.004)
    return y.astype(np.float32), beats, note_times


# ================================================================================================== treatments
def vread(y, ratio):
    """Variable-rate read (tape varispeed): ratio[n] = playback speed at output sample n."""
    pos = np.cumsum(ratio) - ratio[0]
    pos = np.clip(pos, 0, len(y) - 2); i = pos.astype(np.int64); f = (pos - i)[:, None].astype(np.float32)
    return (y[i] * (1 - f) + y[i + 1] * f).astype(np.float32)


def telephone(y, seed=0, lo=300, hi=3400, grit=1.8, crackle=0.5, hum=0.4, hiss_db=-38.0):
    """A 1970s telephone line: band 300-3400 Hz, carbon-mic grit, crackle, mains hum, line hiss. Mono."""
    rng = np.random.default_rng(seed)
    m = SX.mono(y)
    x = SX.bp(m, lo, hi, 4)
    x = SX.eq(x, ('peak', 1000, 3.0, 0.9), ('peak', 2400, 2.0, 1.2))
    pk = float(np.abs(x).max()) + 1e-9
    x = np.tanh(x / pk * grit) / np.tanh(grit) * pk
    n = len(x)
    hs = SX.bp(rng.normal(0, 1, n).astype(np.float32), 500, 3400, 2) * pk * 10 ** (hiss_db / 20) * 3
    t = np.arange(n) / SR
    hm = (np.sin(2 * np.pi * 60 * t) + 0.5 * np.sin(2 * np.pi * 180 * t)) * pk * 0.004 * hum
    cr = np.zeros(n, np.float32)
    for _ in range(int(crackle * n / SR * 6)):
        i = int(rng.integers(0, n - 200)); k = int(rng.integers(20, 160))
        cr[i:i + k] += rng.normal(0, 1, k) * np.exp(-np.arange(k) / (k / 4)) * pk * rng.uniform(0.05, 0.25)
    x = x + hs + hm + SX.bp(cr, 400, 3400, 2)
    return SX.st(x.astype(np.float32))


def detune(y, cents):
    """A clean pitch-and-speed shift (resample) by cents."""
    import soxr
    r = 2 ** (cents / 1200.0)
    return soxr.resample(y, SR, SR / r, quality='VHQ').astype(np.float32)


def rooms(y, seed=0):
    """The tune heard from three rooms at once: the hallway (left, near-ish), the living room (right, further),
    Grandpa's chair (centre-far, darkest); each delayed a little (the copies drift: not quite in sync)."""
    out = None
    for k, (pan_, delay, lp_hz, wet, g, ir) in enumerate(((-0.75, 0.0, 4200, 0.55, 0.9, 'hallway'),
                                                          (0.8, 0.045, 3200, 0.7, 0.75, 'living'),
                                                          (0.0, 0.11, 2200, 0.85, 0.7, 'hall'))):
        x = SX.lp(SX.mono(y), lp_hz, 2)
        x = np.concatenate([np.zeros(int(delay * SR), np.float32), x])
        x = JG._wow(SX.st(x), 0.0015 + 0.001 * k, 0.21 + 0.07 * k, 0.0004, 5.0, seed + k)
        x = SX.reverb(x, ir, wet, 0.01 * k)
        x = SX.st(SX.pan(SX.mono(x), pan_)) * g
        out = x if out is None else _sum(out, x)
    return SX.width(out, 1.4)


def _sum(a, b):
    n = max(len(a), len(b))
    o = np.zeros((n, 2), np.float32); o[:len(a)] += a; o[:len(b)] += b
    return o


def ceiling(y, seed=0):
    x = SX.bp(SX.mono(y), 400, 4500, 3)
    x = SX.eq(x, ('peak', 900, 4.0, 1.4), ('peak', 2600, 2.0, 1.5))
    pk = float(np.abs(x).max()) + 1e-9
    x = np.tanh(x / pk * 1.3) / np.tanh(1.3) * pk
    x = SX.reverb(SX.st(x), 'hallway', 0.6, 0.012)
    return SX.width(x, 0.7)


def car_radio(y, seed=0):
    rng = np.random.default_rng(seed)
    x = JG._wow(SX.st(y), 0.012, 0.18, 0.002, 4.0, seed)               # seasick
    x = SX.bp(SX.mono(x), 200, 4500, 3)
    pk = float(np.abs(x).max()) + 1e-9
    n = len(x)
    st_ = SX.bp(rng.normal(0, 1, n).astype(np.float32), 1500, 6000, 2)
    swell = 0.5 + 0.5 * np.sin(2 * np.pi * 0.13 * np.arange(n) / SR + rng.uniform(0, 6)) ** 2
    x = x + st_ * pk * 0.05 * swell
    x = np.tanh(x / pk * 1.6) / np.tanh(1.6) * pk
    return SX.reverb(SX.st(x.astype(np.float32)), 'car', 0.35, 0.002)


def far_hall(y, seed=0):
    x = SX.lp(SX.mono(y), 2600, 2)
    x = SX.reverb(SX.st(x), 'hall', 0.92, 0.03)
    return SX.width(x, 0.8)


# ================================================================================================== render
def render(version, tempo=None, seed=3, loops=None, phrases=None, transpose=0, counts=None, speeds=None,
           anchors=None, **kw):
    """One version (see the module docstring). Returns (stereo float32, info)."""
    v = version
    if v not in VERSIONS:
        raise KeyError(f'unknown hold-music version {v!r}')
    if v == 'hum':
        import voicesynth as VS
        bm = JG.BeatMap(tempo or 62.0, anchors, swing=0.52)
        ph = tuple(phrases if phrases is not None else (0, 1))
        sel = [(b, d, m) for p in ph for (b, d, m) in MELODY if PHRASES[p][0] <= b < PHRASES[p][1]]
        b0 = PHRASES[ph[0]][0]
        # beats of the selected phrases laid end to end
        offs = {}; acc = 0.0
        for p in ph:
            offs[p] = acc - PHRASES[p][0]; acc += PHRASES[p][1] - PHRASES[p][0]
        pb = [b + offs[next(p for p in ph if PHRASES[p][0] <= b < PHRASES[p][1])] for b, d, m in sel]
        times = [float(bm(x)) + 0.45 for x in pb]
        durs = [max(0.12, float(bm(x + d)) - float(bm(x)) - 0.04) for x, (b, d, m) in zip(pb, sel)]
        mids = [m for b, d, m in sel]
        brk = [float(bm(offs[p] + PHRASES[p][0])) + 0.45 for p in ph[1:]]
        y = VS.hum(times, mids, durs, who=kw.get('who', 'G'), transpose=float(kw.get('hum_transpose', -12.4)),
                   seed=seed, phrase_breaks=brk, vib_cents=18.0)
        y = SX.reverb(SX.st(y.astype(np.float32)), 'living', 0.12, 0.002)
        return JG._level(y, -24), {'beats': [float(bm(i)) + 0.45 for i in range(int(acc) + 1)], 'note_times': times,
                                   'transpose': -12.4 + 0.0}
    warm = v == 'warm'
    t_ = tempo or (84.0 if warm else TEMPO)
    bm = JG.BeatMap(t_, anchors, swing=0.5 if warm else SWING)
    lp_ = loops if loops is not None else (1 if v in ('warm',) else 2)
    ph = tuple(phrases) if phrases is not None else (0, 1, 2, 3)
    y, beats, nt = arrange(bm, lp_, seed, ph, drums=True, warm=warm, transpose=transpose)
    info = {'beats': beats, 'note_times': nt, 'version': v}
    if v == 'studio':
        return JG._level(y, -18), info
    if v == 'warm':
        return JG._level(y, -18), info
    if v == 'phone_1979':
        x = JG._wow(y, 0.004, 0.4, 0.001, 6.0, seed)
        return JG._level(telephone(x, seed, crackle=0.8, hum=0.6), -22), info
    if v == 'landline':
        # tired: played slower (tempo x0.94, arranged slow: the pitch is not dragged with it) and 35 cents flat
        if tempo is None:
            y, beats, nt = arrange(JG.BeatMap(TEMPO * 0.94, anchors, swing=SWING), lp_, seed, ph, True, False, transpose)
        x = detune(y, -35.0)
        k = 2 ** (35 / 1200)
        x = JG._wow(x, 0.003, 0.3, 0.0008, 5.0, seed)
        info = {'beats': [b * k for b in beats], 'note_times': [b * k for b in nt], 'version': v, 'cents': -35.0}
        return JG._level(telephone(x, seed, crackle=0.25, hum=0.2, hiss_db=-34.0), -22), info
    if v == 'rooms':
        return JG._level(rooms(detune(y, -35.0), seed), -24), info
    if v == 'ceiling':
        x = detune(y, -25.0)
        return JG._level(ceiling(x, seed), -24), dict(info, beats=[b * 2 ** (25 / 1200) for b in beats])
    if v == 'car_radio':
        return JG._level(car_radio(detune(y, -60.0), seed), -24), info
    if v == 'far_hall':
        return JG._level(far_hall(y, seed), -30), info
    if v == 'pulse':
        # the counts at counts=[t1, t2, t3] (s from the start); speed steps down at each, smoothly (0.6 s glide)
        counts = list(counts or [6.0, 11.0, 16.0])
        speeds = list(speeds or [1.0, 0.8, 0.62, 0.45])
        x = detune(y, -35.0)
        dur = float(kw.get('dur', counts[-1] + 6.0))
        n = int(dur * SR)
        tt = np.arange(n) / SR
        r = np.full(n, speeds[0], np.float32)
        for c, s0, s1 in zip(counts, speeds[:-1], speeds[1:]):
            r += ((s1 - s0) * np.clip((tt - c) / 0.6, 0, 1)).astype(np.float32)
        tail = float(kw.get('sag_to', 0.0))
        if tail:                                           # optional slide toward a stop after the last count
            r *= (1 - (1 - tail) * np.clip((tt - counts[-1] - 0.6) / 4.0, 0, 1)).astype(np.float32)
        x = vread(np.concatenate([x, np.zeros((SR, 2), np.float32)]), r)
        x = SX.reverb(SX.lp(x, 6000, 1), 'hall', 0.25, 0.01)
        pos = np.cumsum(r) / SR
        info = {'beats': [float(np.interp(b, pos, tt)) for b in beats if b <= pos[-1]], 'counts': counts,
                'speeds': speeds, 'version': v}
        return JG._level(x, -24), info
    raise KeyError(v)


# ================================================================================================== checks
def melody_check(y, note_times, midis, cents=0.0):
    """At each melody onset the strongest NEW pitch class (CQT chroma of the next 120 ms minus the 80 ms before)
    should be the note's (rank 1) or second. Returns counts and the ranks."""
    import librosa
    semis = int(round(cents / 100.0)); cents = cents - 100 * semis   # whole semitones move the notes, the rest tunes
    midis = [mm + semis for mm in midis]
    m = SX.mono(SX.st(y))
    x = librosa.resample(m, orig_sr=SR, target_sr=22050)
    C = np.abs(librosa.cqt(x, sr=22050, hop_length=256, fmin=librosa.note_to_hz('C3'), n_bins=60, bins_per_octave=12,
                           tuning=cents / 100.0))
    tt = librosa.times_like(C, sr=22050, hop_length=256)
    ranks = []
    for t0, mm in zip(note_times, midis):
        now = C[:, (tt >= t0 + 0.01) & (tt <= t0 + 0.13)].mean(1)
        bef = C[:, (tt >= t0 - 0.09) & (tt <= t0 - 0.01)].mean(1) if t0 > 0.1 else np.zeros(60)
        chroma = np.maximum(now - 0.6 * bef, 0).reshape(5, 12).sum(0)
        ranks.append(list(np.argsort(chroma)[::-1]).index(int(round(mm)) % 12) + 1)
    r = np.array(ranks)
    return {'notes_checked': len(r), 'rank1': int((r == 1).sum()), 'rank_le2': int((r <= 2).sum())}


def measure(y):
    y = SX.st(y)
    P = np.abs(np.fft.rfft(SX.mono(y)[:SR * 60])) ** 2; f = np.fft.rfftfreq(min(len(y), SR * 60), 1 / SR)
    tot = P.sum() + 1e-20
    return {'dur': round(len(y) / SR, 2), 'lufs': round(SX.lufs_int(y), 1), 'peak_db': round(float(SX.db(SX.peak(y))), 1),
            'band_lo_mid_hi_pct': [round(100 * float(P[f < 250].sum() / tot), 1),
                                   round(100 * float(P[(f >= 250) & (f < 4000)].sum() / tot), 1),
                                   round(100 * float(P[f >= 4000].sum() / tot), 1)],
            'centroid_hz': int(float((P * f).sum() / tot))}


def main():
    names = [a for a in sys.argv[1:] if not a.startswith('--')] or list(VERSIONS)
    os.makedirs(OUT, exist_ok=True)
    pj = os.path.join(OUT, 'hold_check.json')
    chk = json.load(open(pj)) if os.path.exists(pj) else {}
    mids = [m for b, d, m in MELODY]
    for v in names:
        y, info = render(v, seed=3)
        sf.write(os.path.join(OUT, v + '.wav'), y, SR, subtype='PCM_24')
        r = measure(y)
        try:
            if v in ('studio', 'warm', 'phone_1979', 'rooms', 'ceiling', 'far_hall', 'car_radio'):
                cents = {'rooms': -35, 'ceiling': -25, 'car_radio': -60}.get(v, 0)
                nt = info['note_times']
                if v == 'ceiling':
                    nt = [t * 2 ** (25 / 1200) for t in nt]
                if v == 'car_radio':
                    nt = [t * 2 ** (60 / 1200) for t in nt]
                if v == 'rooms':
                    nt = [t * 2 ** (35 / 1200) for t in nt]
                r['melody'] = melody_check(y, nt, (mids * 4)[:len(nt)], cents)
            elif v == 'landline':
                r['melody'] = melody_check(y, info['note_times'], (mids * 4)[:len(info['note_times'])],
                                           info['cents'])
            elif v == 'hum':
                r['melody'] = melody_check(y, info['note_times'], [m - 12.4 for m in mids[:len(info['note_times'])]],
                                           -40.0)
        except Exception as e:
            r['melody_error'] = repr(e)[:120]
        chk[v] = r
        print(v, json.dumps(r), flush=True)
    json.dump(chk, open(pj, 'w'), indent=1)
    sheet()


def sheet(out=OUT):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    chk = json.load(open(os.path.join(out, 'hold_check.json')))
    files = [v for v in VERSIONS if os.path.exists(os.path.join(out, v + '.wav'))]
    fig, axs = plt.subplots(len(files), 1, figsize=(16, 1.5 * len(files)), dpi=72)
    for ax, v in zip(np.atleast_1d(axs), files):
        x = sf.read(os.path.join(out, v + '.wav'), dtype='float32', always_2d=True)[0].mean(1)[:SR * 40]
        fr, t, S = signal.spectrogram(x, SR, nperseg=4096, noverlap=3072)
        S = 10 * np.log10(S + 1e-14); vm = np.percentile(S, 99.5)
        ax.pcolormesh(t, fr, S, shading='auto', cmap='magma', vmin=vm - 70, vmax=vm, rasterized=True)
        ax.set_yscale('log'); ax.set_ylim(60, 10000)
        c = chk.get(v, {}); mel = c.get('melody') or {}
        ax.set_title(f"{v} | {c.get('dur')} s, {c.get('lufs')} LUFS, peak {c.get('peak_db')}, bands {c.get('band_lo_mid_hi_pct')}"
                     + (f" | tune {mel.get('rank1')}/{mel.get('notes_checked')} rank 1, {mel.get('rank_le2')} rank<=2"
                        if mel else ''), fontsize=9, loc='left')
    plt.tight_layout()
    plt.savefig(os.path.join(out, 'hold_sheet.png'))


if __name__ == '__main__':
    main()
