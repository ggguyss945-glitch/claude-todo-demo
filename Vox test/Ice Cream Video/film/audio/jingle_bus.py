"""jingle_bus.py: "Ride Right with Mister Whistlestop!", the 1994 Channel 6 bus-safety tape's theme: an ORIGINAL 8-bar
tune written for this film (no melody of any existing song; never sung: the story bible keeps the PSA jingle
instrumental), and every version the film uses. It runs on jingle.py's engine (the beat map with anchors, the toy
piano, music box, celesta, glock, tine e-piano, synth bass, kick, shaker and claps, the VHS chain).

The tune (D major, 4/4, 132 bpm, straight eighths with a hint of bounce)
    The HOOK is his whistle: "Fweet-fweet" = two staccato A5 eighths on the downbeat of bars 1, 3 and 7, doubled by a
    pea whistle two octaves up (A7, ~3.5 kHz, where a referee whistle sings). In the film every real "Fweet-fweet"
    (sfx.py 'whistle') is that same rhythm: the jingle and the villain share one sound.
    bars 1-2   (Fweet-fweet!) "Ride right, ride right, with Mis-ter Whis-tle-stop"  A A . D F# D F# | A B A F# G E
               a bugle-call arpeggio on D that climbs to B and falls to a half close on E (over A7)
    bars 3-4   (Fweet-fweet!) "Look both ways and wait your turn for the bus"       A A . D F# D F# | A B G F# D
               the same call, answered home to D
    bars 5-6   "Hold your card up to the ca-me-ra..."   G G B A G F# | E D E . A    (G, E minor, A7): the tape's own
               request, the only phrase that leans (the B-section: up to B, down to an open A)
    bars 7-8   (Fweet-fweet!) "Ride right with Mis-ter Whis-tle-STOP!"   A A . D F# A B | D6 C#6 E D (held)
               the call again, this time over the top to D6, and home; a whistle tag and a bell "ding" after it.
    Harmony | D | G A7 | D | G A7 D | G | Em A7 | D Bm | G A7 D |, oom-pah bass (root on 1, fifth on 3).

Instruments (synthesised unless noted): an FM synth-brass lead (2-op, the 1994 local-TV keyboard), the pea whistle
(a sine trilled by the pea at ~38 Hz, breath noise, an upward chirp at the start of each blast), jingle.py's toy
piano, celesta and glockenspiel (VSCO-2-CE / A Sampled Celesta, CC0), tine e-piano, synth bass, kick, a gated snare
(noise + 190 Hz body), shaker and hand claps (Body Percussion, CC0); the warm ending adds a soft piano (the free
library's horror_soft / Salamander grand, CC-BY) and a slow string pad (detuned saws, low-passed).

Versions (render(version, anchors=None, tempo=None, seed=0, **kw) -> (stereo float32 at 48 kHz, info);
info['beats'] = time of every beat, info['note_times'] = time of every melody note played)
    studio    the clean band mix (the source of the others)
    tv1994    the 1994 tape on the school's TV cart: the VHS chain (wow / flutter, 9 kHz top, hiss, drop-outs), the
              CRT's small speaker (150 Hz-6.5 kHz, 1.5 kHz cone peak, mono) and a faint 15.7 kHz line whine
    musicbox  tension: the tune on a slow, warped, detuned music box (D harmonic minor, ~66 bpm, +-30 cents per tine,
              heavy wow, a sagging spring); wind_down=True runs it down to a stop on the last phrase
    pa        HIS bus loudspeaker at midnight: the horn's narrow band (420 Hz-3.6 kHz, 1.9 kHz honk, driven), slap
              echoes off the house fronts, the street around it, a touch of feedback ringing at the phrase ends
    tapestop  the tape plays (tv1994) and then stops: the speed falls to zero in ~0.9 s (pitch dives), a beat of
              nothing, then the tape REWINDS (the last bars backwards at 7x, a whining squeal) and clunks off.
              stop_beat= (default 16: after two phrases) sets where it dies
    warm      the motif redeemed (Theo going home, the porch light, the morning, rule eight): 92 bpm, soft piano,
              celesta, a string pad, soft bass and brushes, the whistle hook given to a gentle flute-like celesta
              figure, a ritardando and a held D add9. loops= times round
    sting     just the hook: "Fweet-fweet" on the brass + whistle, one bar (a cut-in sting; space it in score.py)
Anchors: render(..., anchors=[(beat, seconds), ...]) bends the tempo so those beats land there; tempo= sets a
constant tempo; transpose= semitones.

CLI: python3 audio/jingle_bus.py [names...]    renders every version (or the names) to W/mix/jingle_bus/<v>.wav,
     checks each (loudness, peak, band shares, the melody found by pitch tracking at every note, version-specific
     checks: the TV / PA band, the music box detune and tempo, the tape-stop pitch fall and the rewind) into
     jingle_check.json, and draws jingle_sheet.png (every version's spectrogram).
"""
import json, os, sys
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sfx as SX                                        # noqa: E402
import jingle as J                                      # noqa: E402  (the engine: beat map, instruments, VHS chain)

SR = 48000
W = SX.W
OUT = os.path.join(W, 'mix', 'jingle_bus')
TEMPO = 132.0
SWING = 0.53
HOOK = 81                                               # A5: "Fweet-fweet"

# (beat, length in beats, midi, syllable), D major, 4/4: beat 0 = the first "Fweet"
MELODY = [
    (0.0, 0.4, 81, 'Fweet'), (0.5, 0.4, 81, 'fweet'),
    (1.5, 0.5, 74, 'Ride'), (2.0, 1.0, 78, 'right'), (3.0, 0.5, 74, 'ride'), (3.5, 0.5, 78, 'right'),
    (4.0, 1.0, 81, 'with'), (5.0, 0.5, 83, 'Mis'), (5.5, 0.5, 81, 'ter'), (6.0, 0.5, 78, 'Whis'),
    (6.5, 0.5, 79, 'tle'), (7.0, 1.0, 76, 'stop'),
    (8.0, 0.4, 81, 'Fweet'), (8.5, 0.4, 81, 'fweet'),
    (9.5, 0.5, 74, 'Look'), (10.0, 1.0, 78, 'both'), (11.0, 0.5, 74, 'ways'), (11.5, 0.5, 78, 'and'),
    (12.0, 1.0, 81, 'wait'), (13.0, 0.5, 83, 'your'), (13.5, 0.5, 79, 'turn'), (14.0, 0.5, 78, 'the'),
    (14.5, 1.5, 74, 'bus'),
    (16.0, 0.5, 79, 'Hold'), (16.5, 0.5, 79, 'your'), (17.0, 1.0, 83, 'card'), (18.0, 0.5, 81, 'up'),
    (18.5, 0.5, 79, 'to'), (19.0, 1.0, 78, 'the'),
    (20.0, 1.0, 76, 'ca'), (21.0, 0.5, 74, 'me'), (21.5, 0.5, 76, 'ra'), (22.0, 2.0, 81, '...'),
    (24.0, 0.4, 81, 'Fweet'), (24.5, 0.4, 81, 'fweet'),
    (25.5, 0.5, 74, 'Ride'), (26.0, 0.5, 78, 'right'), (26.5, 0.5, 81, 'with'), (27.0, 1.0, 83, 'Mis'),
    (28.0, 1.0, 86, 'ter'), (29.0, 0.5, 85, 'Whis'), (29.5, 0.5, 76, 'tle'), (30.0, 2.0, 74, 'STOP'),
]
CHORDS = [(0.0, 62, (0, 4, 7)), (4.0, 67, (0, 4, 7)), (6.0, 69, (0, 4, 7, 10)), (8.0, 62, (0, 4, 7)),
          (12.0, 67, (0, 4, 7)), (13.0, 69, (0, 4, 7, 10)), (14.0, 62, (0, 4, 7)), (16.0, 67, (0, 4, 7)),
          (20.0, 64, (0, 3, 7)), (22.0, 69, (0, 4, 7, 10)), (24.0, 62, (0, 4, 7)), (26.0, 71, (0, 3, 7)),
          (28.0, 67, (0, 4, 7)), (29.0, 69, (0, 4, 7, 10)), (30.0, 62, (0, 4, 7))]
N_BEATS = 32.0
HOOK_BEATS = (0.0, 8.0, 24.0)
PHRASES = ((0.0, 8.0), (8.0, 16.0), (16.0, 24.0), (24.0, 32.0))
MINOR = {78: 77, 66: 65, 90: 89, 83: 82, 71: 70, 59: 58, 47: 46, 54: 53, 42: 41}   # F# -> F, B -> Bb (C# kept)


def hz(m):
    return 440.0 * 2.0 ** ((np.asarray(m, float) - 69.0) / 12.0)


def _bass_line():
    out = []
    for k, (b, root, pcs) in enumerate(CHORDS):
        nb = CHORDS[k + 1][0] if k + 1 < len(CHORDS) else N_BEATS
        r = 38 + ((root - 38) % 12)
        x = b
        while x < nb - 1e-6:
            out.append((x, r if int(round(x)) % 2 == 0 else r + 7 - (12 if r + 7 > 50 else 0)))
            x += 1.0
    return out


# ================================================================================================== new instruments
def _fitn(x, n):
    x = np.asarray(x, np.float32)
    return x[:n] if len(x) >= n else np.pad(x, (0, n - len(x)))


def fm_brass(midi, vel, dur, rng, detune=0.0):
    """A 1994 local-TV keyboard's synth brass: 2-op FM (1:1), the index swelling in 40 ms and settling, a small
    pitch scoop, a second voice 7 cents up."""
    f = hz(midi) * 2 ** (detune / 1200.0)
    L = dur + 0.12
    t = np.arange(int(L * SR)) / SR
    idx = 0.6 + 2.0 * (1 - np.exp(-t / 0.04)) * (0.55 + 0.45 * np.exp(-t / 0.25))
    sc = 1 - 0.012 * np.exp(-t / 0.03)
    ph = 2 * np.pi * np.cumsum(f * sc) / SR
    y = np.sin(ph + idx * np.sin(ph)) + 0.6 * np.sin(ph * 1.004 + idx * 0.8 * np.sin(ph * 1.004) + rng.uniform(0, 6))
    env = (1 - np.exp(-t / 0.012)) * np.clip((L - t) / 0.1, 0, 1)
    return SX.lp((y * env * vel * 0.5).astype(np.float32), 5200, 2)


def pea_whistle(midi, dur, vel, rng):
    """A referee's pea whistle: a sine (here at `midi`) trilled by the rolling pea (~38 Hz frequency and amplitude
    wobble), breath noise around it, the blast's upward chirp and a hard stop."""
    f = hz(midi)
    L = dur
    n = int(L * SR); t = np.arange(n) / SR
    pr = rng.uniform(34, 42)
    trill = np.sin(2 * np.pi * pr * t + rng.uniform(0, 6))
    fi = f * (1 - 0.07 * np.exp(-t / 0.025)) * (1 + 0.028 * trill)
    y = np.sin(2 * np.pi * np.cumsum(fi) / SR) * (0.72 + 0.28 * trill)
    br = _fitn(SX.bp(SX.noise(L, int(rng.integers(1 << 30))), f * 0.8, f * 1.3, 2), n) * 0.35
    env = np.clip(t / 0.008, 0, 1) * np.clip((L - t) / 0.012, 0, 1)
    return ((y + br * (0.6 + 0.4 * trill)) * env * vel).astype(np.float32)


def snare(vel, rng):
    n = int(0.22 * SR); t = np.arange(n) / SR
    z = _fitn(SX.bp(SX.noise(0.22, int(rng.integers(1 << 30))), 1800, 9000, 2), n) * np.exp(-t / 0.06)
    b = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.035)
    return ((0.8 * z + 0.6 * b) * vel).astype(np.float32)


def pad(midis, dur, vel, rng):
    """A slow string pad: detuned saws (3 per note), low-passed at 2.2 kHz, a 0.8 s swell."""
    L = dur + 1.2
    t = np.arange(int(L * SR)) / SR
    y = np.zeros(len(t))
    for m in midis:
        for d in (-6, 0, 7):
            f = hz(m) * 2 ** (d / 1200)
            ph = (f * t + rng.uniform(0, 1)) % 1.0
            y += (2 * ph - 1) * 0.3
    env = np.clip(t / 0.8, 0, 1) * np.clip((L - t) / 1.2, 0, 1)
    return SX.lp((y * env * vel / max(1, len(midis))).astype(np.float32), 2200, 2)


def flute(midi, dur, vel, rng):
    """A soft flute-like tone (sine + a little 2nd and breath, a slow vibrato) for the warm hook."""
    f = hz(midi); L = dur + 0.2
    t = np.arange(int(L * SR)) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t) * np.clip((t - 0.15) / 0.3, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    y = np.sin(ph) + 0.12 * np.sin(2 * ph) + _fitn(SX.bp(SX.noise(L, int(rng.integers(1 << 30))), f, f * 3, 1), len(t)) * 0.05
    env = np.clip(t / 0.06, 0, 1) * np.clip((L - t) / 0.2, 0, 1)
    return (y * env * vel).astype(np.float32)


# ================================================================================================== arrangements
def _notes(minor=False, transpose=0):
    return [(b, d, (MINOR.get(m, m) if minor else m) + transpose, s) for b, d, m, s in MELODY]


def _chord_notes(root, pcs, minor, transpose):
    if minor:
        root = MINOR.get(root, root)
    notes = sorted(55 + ((root + p - 55) % 12) for p in pcs)
    if minor:
        notes = [MINOR.get(n, n) for n in notes]
    return [n + transpose for n in notes]


def band(bm, seed=0, transpose=0, loops=1, tag=True, stop_beat=None):
    """The clean 1994 band, `loops` times round (stop_beat: render only up to that beat). Returns (stereo, info)."""
    rng = np.random.default_rng(seed)
    total = N_BEATS * loops + (2.0 if tag else 0.0)
    if stop_beat is not None:
        total = min(total, float(stop_beat))
    end = float(bm(total)) + 2.2
    buf = np.zeros((int(end * SR) + SR, 2), np.float32)
    tune = {m: rng.uniform(-6, 6) for m in range(20, 128)}
    note_t = []
    for L in range(loops):
        o = L * N_BEATS
        for b, d, m, s in _notes(False, transpose):
            if o + b >= total - 1e-6:
                break
            t = float(bm(o + b)); dd = float(bm(o + b + d)) - t
            hook = s.lower() == 'fweet'
            note_t.append(t)
            _put = J._put
            _put(buf, t, fm_brass(m, 0.55 if not hook else 0.5, dd * (0.55 if hook else 0.9), rng, 0.0), 1.0, -0.12)
            _put(buf, t + 0.003, J.toy_piano(m, 0.35, rng, tune[m]), 1.0, 0.15)
            if hook:
                _put(buf, t, pea_whistle(m + 24, dd * 0.6, 0.30, rng), 1.0, 0.25)
                _put(buf, t + 0.002, J.glock(m + 12, 0.25), 1.0, 0.3)
            elif abs(b - round(b)) < 1e-6:
                _put(buf, t + 0.002, J.celesta(m + 12, 0.22), 1.0, 0.3)
        for k, (b, root, pcs) in enumerate(CHORDS):
            nb = CHORDS[k + 1][0] if k + 1 < len(CHORDS) else N_BEATS
            notes = _chord_notes(root, pcs, False, transpose)
            x = b + 0.5
            while x < nb - 1e-6 and o + x < total:
                t = float(bm(o + x)); dd = float(bm(o + x + 0.35)) - t
                for nn in notes:
                    _put(buf, t, J.tine_ep(nn, 0.12, dd, rng), 1.0, 0.0)
                x += 1.0
        for k, (b, m) in enumerate(_bass_line()):
            if o + b >= total - 1e-6:
                break
            t = float(bm(o + b)); dd = (float(bm(o + b + 1)) - t) * 0.75
            _put(buf, t, J.synth_bass(m + transpose, 0.5, dd), 1.0, 0.0)
        for x in np.arange(0, N_BEATS, 0.5):
            if o + x >= total - 1e-6:
                break
            t = float(bm(o + x))
            if abs(x % 2) < 1e-6:
                _put(buf, t, J.kick(0.6, rng), 1.0, 0.0)
            if abs(x % 2 - 1) < 1e-6:
                _put(buf, t, snare(0.30, rng), 1.0, 0.05)
                _put(buf, t + 0.004, J.clap(0.16, int(x)), 1.0, -0.1)
            _put(buf, t, J.shaker(0.09 if abs(x - round(x)) < 1e-6 else 0.06, rng), 1.0, 0.35)
    if tag and stop_beat is None:                     # the tag: the whistle's "Fweet-fweet", the D chord, a "ding"
        o = loops * N_BEATS
        t = float(bm(o)); t2 = float(bm(o + 0.5)); e8 = (t2 - t) * 0.6
        for tt in (t, t2):
            J._put(buf, tt, pea_whistle(HOOK + 24 + transpose, e8, 0.33, rng), 1.0, 0.2)
            J._put(buf, tt, fm_brass(HOOK + transpose, 0.45, e8, rng), 1.0, -0.1)
        tb = float(bm(o + 1.0))
        for nn in (62, 66, 69, 74):
            J._put(buf, tb, fm_brass(nn + transpose, 0.3, 1.2, rng), 1.0, 0.0)
        J._put(buf, tb, J.synth_bass(38 + transpose, 0.55, 1.2), 1.0, 0.0)
        J._put(buf, tb + 0.05, J.glock(98 + transpose, 0.35), 1.0, 0.25)
        J._put(buf, tb + 0.05, J.celesta(86 + transpose, 0.3), 1.0, -0.25)
        J._put(buf, tb, J.kick(0.6, rng), 1.0, 0.0)
    beats = [float(bm(b)) for b in np.arange(0, total + 0.5, 1.0)]
    return SX.fade(buf[:int(end * SR)], 0.002, 0.25), {'beats': beats, 'note_times': note_t, 'end': end}


def musicbox_arr(bm, seed=0, transpose=0, wind_down=False, detune=30.0):
    """The tune alone on a slow, detuned music box in D harmonic minor (tension)."""
    rng = np.random.default_rng(seed)
    end = float(bm(N_BEATS)) + 4.0
    buf = np.zeros((int(end * SR) + SR, 2), np.float32)
    tune = {m: rng.uniform(-detune, detune) for m in range(20, 128)}
    note_t = []
    for b, d, m, s in _notes(True, transpose):
        t = float(bm(b)) + rng.uniform(-0.03, 0.05)              # the cylinder's pins: never quite in time
        note_t.append(t)
        J._put(buf, t, J.music_box(m + 12, 0.8 * rng.uniform(0.85, 1.0), rng, tune[m]), 1.0, rng.uniform(-0.2, 0.2))
        if abs(b % 4) < 1e-6:                                      # a low tine on each bar: the chord's root
            root = next(r for bb, r, p in reversed(CHORDS) if bb <= b)
            root = MINOR.get(root, root)
            J._put(buf, t, J.music_box(50 + ((root - 50) % 12) + transpose, 0.35, rng, tune[root] * 1.5, 1.4), 1.0, 0.0)
    y = SX.fade(buf[:int(end * SR)], 0.002, 1.5)
    return y, {'beats': [float(bm(b)) for b in np.arange(0, N_BEATS + 0.5, 1.0)], 'note_times': note_t, 'end': end}


def warm_arr(bm, seed=0, transpose=0, loops=1):
    """The motif redeemed: soft piano, celesta, a pad, soft bass and brushes; the hook on a flute-like tone."""
    rng = np.random.default_rng(seed)
    total = N_BEATS * loops
    end = float(bm(total + 2.0)) + 4.0
    buf = np.zeros((int(end * SR) + SR, 2), np.float32)
    note_t = []
    for L in range(loops):
        o = L * N_BEATS
        for b, d, m, s in _notes(False, transpose):
            t = float(bm(o + b)); dd = float(bm(o + b + d)) - t
            note_t.append(t)
            if s.lower() == 'fweet':
                J._put(buf, t, flute(m, dd * 0.9, 0.22, rng), 1.0, 0.2)
                J._put(buf, t, J.celesta(m + 12, 0.25), 1.0, 0.25)
            else:
                J._put(buf, t, J.low_piano(m, 0.5, int(rng.integers(3))), 1.0, -0.1)
                J._put(buf, t + 0.01, J.celesta(m + 12, 0.12), 1.0, 0.3)
        for k, (b, root, pcs) in enumerate(CHORDS):
            nb = CHORDS[k + 1][0] if k + 1 < len(CHORDS) else N_BEATS
            t = float(bm(o + b)); dd = float(bm(o + nb)) - t
            notes = _chord_notes(root, pcs, False, transpose)
            J._put(buf, t, pad([n - 12 for n in notes], dd, 0.10, rng), 1.0, 0.0)
            J._put(buf, t, J.synth_bass(38 + ((root - 38) % 12) + transpose, 0.32, dd * 0.9), 1.0, 0.0)
            for j, nn in enumerate(notes):                       # a rolled piano chord under the tune
                J._put(buf, t + 0.03 * j, J.low_piano(nn - 12, 0.2, j), 1.0, -0.2 + 0.2 * j)
        for x in np.arange(0, N_BEATS, 1.0):
            t = float(bm(o + x))
            J._put(buf, t, J.shaker(0.05, rng), 1.0, 0.3)
    t = float(bm(total))                                         # the held D add9 (the porch light comes on)
    for j, nn in enumerate((50, 57, 62, 64, 66, 69)):
        J._put(buf, t + 0.04 * j, J.low_piano(nn + transpose, 0.32, j), 1.0, -0.3 + 0.12 * j)
    J._put(buf, t, pad([n + transpose for n in (50, 57, 62, 64, 66)], 3.5, 0.12, rng), 1.0, 0.0)
    J._put(buf, t + 0.2, J.celesta(86 + transpose, 0.25), 1.0, 0.25)
    J._put(buf, t + 0.2, flute(HOOK + transpose, 0.25, 0.12, rng), 1.0, 0.1)
    J._put(buf, t + 0.55, flute(HOOK + transpose, 0.9, 0.12, rng), 1.0, 0.1)    # the whistle's two notes, gently
    y = SX.fade(buf[:int(end * SR)], 0.002, 2.5)
    return y, {'beats': [float(bm(b)) for b in np.arange(0, total + 0.5, 1.0)], 'note_times': note_t, 'end': end}


# ================================================================================================== chains
def tv_chain(y, seed=0):
    """The 1994 tape on a school TV cart: VHS (wow, flutter, 9 kHz, hiss, drop-outs), the CRT's small speaker
    (150 Hz-6.5 kHz, 1.5 kHz cone, mono), a faint 15.734 kHz line-output whine."""
    z = J.vhs(y, seed, lp_hz=9000, hiss_db=-44.0, width=0.1, dropouts=0.35)
    m = SX.mono(z)
    m = SX.lp(SX.hp(m, 150, 2), 6500, 4)
    m = SX.eq(m, ('peak', 1500, 3.0, 1.0), ('peak', 400, 1.5, 1.2))
    pk = SX.peak(m) + 1e-9
    m = (np.tanh(1.4 * m / pk) / np.tanh(1.4) * pk).astype(np.float32)
    t = np.arange(len(m)) / SR
    m = m + (np.sin(2 * np.pi * 15734 * t) * pk * 10 ** (-52 / 20)).astype(np.float32)
    return SX.st(m)


def pa_chain(y, seed=0, feedback=0.6):
    """HIS bus loudspeaker: 420 Hz-3.6 kHz, the horn's 1.9 kHz honk, driven; slap-back off the house fronts; the
    street; feedback ringing (2.35 kHz) for a moment at each phrase end."""
    rng = np.random.default_rng(seed)
    m = SX.mono(SX.st(y))
    m = SX.lp(SX.hp(m, 420, 4), 3600, 4)
    m = SX.eq(m, ('peak', 1900, 6.0, 1.3), ('peak', 850, 2.0, 1.0))
    pk = SX.peak(m) + 1e-9
    m = (np.tanh(2.3 * m / pk) / np.tanh(2.3) * pk).astype(np.float32)
    sl = np.zeros_like(m)
    for d, g in ((0.062, 0.28), (0.141, 0.16), (0.236, 0.08)):
        k = int(d * SR); sl[k:] += m[:-k] * g
    m = m + SX.lp(sl, 2500, 2)
    if feedback > 0:
        t = np.arange(len(m)) / SR
        for c in (len(m) / SR * 0.24, len(m) / SR * 0.48, len(m) / SR * 0.74):
            c += rng.uniform(-0.3, 0.3)
            env = np.exp(-0.5 * ((t - c) / 0.18) ** 2)
            f0 = 2350 * (1 + 0.004 * np.sin(2 * np.pi * 3 * t))
            m = m + (np.sin(2 * np.pi * np.cumsum(f0) / SR) * env * pk * 0.22 * feedback).astype(np.float32)
    return SX.reverb(SX.st(m), 'street', 0.32, 0.01)


def _vread(y, ratio):
    """Read y at a time-varying speed (ratio per output sample): a tape speeding up or stopping."""
    pos = np.cumsum(ratio); pos -= pos[0]
    pos = pos[pos < len(y) - 2]
    i = pos.astype(np.int64); f = (pos - i)[:, None].astype(np.float32)
    return (y[i] * (1 - f) + y[i + 1] * f).astype(np.float32)


def tape_stop_rewind(y, t_stop, stop_s=0.9, gap=0.3, rew_s=1.6, rew_speed=7.0, seed=0):
    """Play y up to t_stop, then the tape stops (speed 1 -> 0 over stop_s: the pitch dives), gap s of nothing (the
    motor's hum), then the REWIND: the bars just played run backwards at rew_speed, high-passed, with the transport's
    whine, and a clunk."""
    rng = np.random.default_rng(seed)
    y = SX.st(y)
    a = int(t_stop * SR)
    head = y[:a]
    k = int(stop_s * SR)
    r = np.linspace(1.0, 0.0, k) ** 1.6
    dive = _vread(y[a:a + int(stop_s * SR * 1.2) + SR], r)
    dive *= np.linspace(1, 0.2, len(dive))[:, None].astype(np.float32)
    hum = SX.st((np.sin(2 * np.pi * 60 * np.arange(int(gap * SR)) / SR) * 0.004).astype(np.float32))
    src = y[max(0, a - int(rew_s * rew_speed * SR)):a][::-1]
    ramp = np.concatenate([np.linspace(1.5, rew_speed, int(0.35 * SR)), np.full(int(rew_s * SR), rew_speed)])
    rew = _vread(src, ramp)
    rew = SX.lp(SX.hp(rew, 900, 2), 6500, 4) * 0.55               # still the TV's speaker
    n = len(rew); t = np.arange(n) / SR
    wh = np.sin(2 * np.pi * np.cumsum(2600 + 900 * np.clip(t / 0.4, 0, 1)) / SR) * 0.02 * SX.peak(y)
    rew = rew + SX.st(wh.astype(np.float32))
    rew = SX.fade(rew, 0.05, 0.04)
    clunk = SX.st(SX.modal([95.0, 240.0, 610.0], [0.06, 0.03, 0.012], [1.0, 0.5, 0.3], 0.2, int(rng.integers(1 << 20))))
    clunk = clunk * (SX.peak(y) * 0.5 / (SX.peak(clunk) + 1e-9))
    return np.concatenate([head, dive, hum, rew, clunk]).astype(np.float32), {
        't_stop': t_stop, 't_dive_end': (len(head) + len(dive)) / SR,
        't_rewind': (len(head) + len(dive) + len(hum)) / SR, 'end': (len(head) + len(dive) + len(hum) + len(rew)) / SR}


# ================================================================================================== render
VERSIONS = ('studio', 'tv1994', 'musicbox', 'pa', 'tapestop', 'warm', 'sting')


def render(version, anchors=None, tempo=None, seed=0, transpose=0, loops=1, wind_down=False, stop_beat=16.0,
           melody_anchors=None, **_):
    v = str(version)
    base = {'musicbox': 66.0, 'warm': 92.0}.get(v, TEMPO)
    bm = J.BeatMap(tempo or base, anchors, SWING if v not in ('musicbox',) else 0.5)
    if v == 'studio':
        y, info = band(bm, seed, transpose, loops)
    elif v == 'tv1994':
        y, info = band(bm, seed, transpose, loops)
        y = tv_chain(y, seed)
    elif v == 'pa':
        y, info = band(bm, seed, transpose, loops)
        y = pa_chain(y, seed)
    elif v == 'sting':
        y, info = band(bm, seed, transpose, 1, tag=False, stop_beat=1.0)
    elif v == 'musicbox':
        y, info = musicbox_arr(bm, seed, transpose)
        y = J._wow(y, depth=0.006, hz_=0.33, fl=0.0015, fl_hz=5.0, seed=seed)
        n = len(y); t = np.arange(n) / SR                         # the spring sags: slower and flatter late on
        r = 1.0 - 0.10 * np.clip(t / (n / SR), 0, 1) ** 2
        if wind_down:
            t0 = float(bm(24.0))
            r = r * np.where(t < t0, 1.0, np.clip(1 - (t - t0) / (n / SR - t0 + 1e-9), 0.04, 1) ** 0.8)
        y2 = _vread(np.concatenate([y, np.zeros((SR * 4, 2), np.float32)]), r)
        sc = np.cumsum(r) / SR                                    # note times move with the sag
        info['note_times'] = [float(np.searchsorted(sc, x)) / SR for x in info['note_times']]
        y = SX.fade(y2, 0.002, 1.0)
    elif v == 'warm':
        y, info = warm_arr(bm, seed, transpose, loops)
    elif v == 'tapestop':
        y, info = band(bm, seed, transpose, 1, tag=False, stop_beat=float(stop_beat) + 1.0)
        y = tv_chain(y, seed)
        y, ti = tape_stop_rewind(y, float(bm(float(stop_beat))), seed=seed)
        info.update(ti)
        info['note_times'] = [x for x in info['note_times'] if x < ti['t_stop']]
    else:
        raise KeyError(f'unknown jingle version {version!r}')
    y = SX.st(np.asarray(y, np.float32))
    pk = SX.peak(y)
    if pk > 0.89:
        y = y * (0.89 / pk)
    info['version'] = v
    return y, info


# ================================================================================================== checks
def melody_check(y, info, minor=False, transpose=0):
    """At each played melody note: is its pitch class the strongest (or second) NEW pitch class in the 120 ms after
    its onset (CQT, the onset energy over the 80 ms before)? Returns the counts and ranks."""
    import librosa
    x = librosa.resample(SX.mono(SX.st(y)), orig_sr=SR, target_sr=22050)
    C = np.abs(librosa.cqt(x, sr=22050, hop_length=256, fmin=librosa.note_to_hz('C3'), n_bins=72, bins_per_octave=12))
    tt = librosa.times_like(C, sr=22050, hop_length=256)
    ranks = []
    for (b, d, m, s), t0 in zip(_notes(minor, transpose), info.get('note_times', [])):
        now = C[:, (tt >= t0 + 0.01) & (tt <= t0 + 0.13)].mean(1)
        bef = C[:, (tt >= t0 - 0.09) & (tt <= t0 - 0.01)].mean(1) if t0 > 0.1 else np.zeros(72)
        ch = np.maximum(now - 0.6 * bef, 0).reshape(6, 12).sum(0)
        ranks.append(list(np.argsort(ch)[::-1]).index(m % 12) + 1)
    r = np.array(ranks)
    return {'notes_checked': len(r), 'rank1': int((r == 1).sum()), 'rank_le2': int((r <= 2).sum()),
            'ranks': [int(v) for v in r]}


def _band_share(y, lo, hi):
    m = SX.mono(SX.st(y))[:SR * 60]
    P = np.abs(np.fft.rfft(m)) ** 2; f = np.fft.rfftfreq(len(m), 1 / SR)
    return round(100 * float(P[(f >= lo) & (f < hi)].sum() / (P.sum() + 1e-20)), 1)


def _centroid_track(y, hop=0.1):
    m = SX.mono(SX.st(y)); k = int(hop * SR); out = []
    for i in range(0, len(m) - 4096, k):
        s = np.abs(np.fft.rfft(m[i:i + 4096] * np.hanning(4096)))
        f = np.fft.rfftfreq(4096, 1 / SR)
        out.append(float((f * s).sum() / (s.sum() + 1e-12)) if s.sum() > 1e-6 else 0.0)
    return np.array(out)


def check(v, y, info):
    r = J.measure(y)
    r['melody'] = melody_check(y, info, minor=(v == 'musicbox'))
    if v in ('tv1994', 'tapestop'):
        r['pct_150_6500'] = _band_share(y, 150, 6500)
        r['pct_above_9k'] = _band_share(y, 9000, 24000)
    if v == 'pa':
        r['pct_420_3600'] = _band_share(y, 420, 3600)
        r['pct_below_300'] = _band_share(y, 0, 300)
    if v == 'musicbox':
        nt = np.array(info['note_times'])
        r['bpm_measured'] = round(60.0 * 4 / float(np.median(np.diff(nt[[0, 12, 24, 36]])) / 2), 1) if len(nt) > 36 else None
        import librosa
        f0, vf, _ = librosa.pyin(SX.mono(y)[:SR * 20].astype(np.float32), fmin=300, fmax=2500, sr=SR, frame_length=4096)
        f0 = f0[np.isfinite(f0)]
        cents = 1200 * np.log2(f0 / 440.0); dev = ((cents + 50) % 100) - 50
        r['detune_cents_abs_median'] = round(float(np.median(np.abs(dev))), 1) if len(dev) else None
    if v == 'tapestop':
        ct = _centroid_track(y)
        a, b = int(info['t_stop'] / 0.1), int(info['t_dive_end'] / 0.1)
        r['centroid_before_stop_hz'] = int(np.median(ct[max(0, a - 20):a]))
        r['centroid_end_of_dive_hz'] = int(np.median(ct[max(a, b - 3):b]))
        c = int(info['t_rewind'] / 0.1)
        r['centroid_rewind_hz'] = int(np.median(ct[c:c + 10]))
        r['times'] = {k: round(info[k], 2) for k in ('t_stop', 't_dive_end', 't_rewind', 'end')}
    if v == 'warm':
        r['pct_above_4k'] = _band_share(y, 4000, 24000)
    return r


def sheet(names, out=OUT):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from scipy import signal
    fig, axs = plt.subplots(len(names), 1, figsize=(14, 2.1 * len(names)), dpi=80)
    for ax, v in zip(np.atleast_1d(axs), names):
        y, _ = sf.read(os.path.join(out, v + '.wav'), dtype='float32')
        m = y.mean(1) if y.ndim > 1 else y
        f, t, Z = signal.stft(m, SR, nperseg=2048, noverlap=1536)
        ax.pcolormesh(t, f, 20 * np.log10(np.abs(Z) + 1e-7), vmin=-110, vmax=-20, shading='auto', cmap='magma')
        ax.set_yscale('symlog', linthresh=500); ax.set_ylim(80, 20000)
        ax.set_title(v, fontsize=9, loc='left'); ax.tick_params(labelsize=7)
    fig.tight_layout(); fig.savefig(os.path.join(out, 'jingle_sheet.png')); plt.close(fig)


def main():
    names = [a for a in sys.argv[1:] if not a.startswith('--')] or list(VERSIONS)
    os.makedirs(OUT, exist_ok=True)
    pj = os.path.join(OUT, 'jingle_check.json')
    res = json.load(open(pj)) if os.path.exists(pj) else {}
    for v in names:
        y, info = render(v, wind_down=(v == 'musicbox'))
        sf.write(os.path.join(OUT, v + '.wav'), y, SR, subtype='PCM_24')
        res[v] = check(v, y, info)
        print(v, json.dumps({k: (x if k != 'melody' else {kk: x[kk] for kk in ('notes_checked', 'rank1', 'rank_le2')})
                             for k, x in res[v].items()}), flush=True)
    json.dump(res, open(pj, 'w'), indent=1)
    sheet([v for v in VERSIONS if os.path.exists(os.path.join(OUT, v + '.wav'))])
    print('wrote', pj)


if __name__ == '__main__':
    main()
