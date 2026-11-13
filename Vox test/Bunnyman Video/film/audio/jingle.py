"""jingle.py: the Pemberton's Department Store jingle, an ORIGINAL 8-bar tune written for this film (no melody of any
existing song), and every version the film uses. The words are the narrator's: "Hop, hop, hop along. / The
Bunnyman sings his song. / Close your eyes and count to seven. / Find an egg that fell from heaven."

The tune (D major, 2/4, 126 bpm, a light skip: swung eighths 58/42)
    bars 1-2  "Hop, hop, hop a-long"            F#4 A4 | D5 B4 A4      three hops up the D triad, a step down
    bars 3-4  "(The) Bun-ny-man sings his song"  (A4) B4 A4 G4 | F#4 G4 E4   the answer, down to a half close on E
    bars 5-6  "Close your eyes and count to se-ven"  D4 E4 F#4 G4 | A4 B4 C#5 D5   the COUNT: the scale climbs one
              note per syllable, the leading tone C# on "se-" resolving to D on "-ven"
    bars 7-8  "Find an egg that fell from hea-ven"   E5 D5 B4 A4 | G4 F#4 E4 D4   the egg falls back down to D
    Harmony | D | D | G | A7 | D | A7 | G | A7 . D |, an oom-pah bass (root on 1, fifth on 2), a tag bar on D.
    The hook is the climb: in the climax June counts "One, Two, Three... Four, Five... Six, Seven" on the same
    scale in D harmonic minor (D E F G A Bb C#), and it stops on C#, the leading tone, one step short of home: the
    jingle has resolved it every time before; this time the music is cut to silence on "Seven".
    The family knock 2-3-2 is the tune's own rhythm: "Hop, hop" (two quarter knocks), "Bun-ny-man" (eighth, eighth,
    quarter), "sings his" ... two more: Grandma made her secret knock out of the jingle her daughter loved.

Instruments: toy piano (synthesised: struck rods, partials 1 : 6.27 : 17.55, a wooden box, slightly out of tune),
glockenspiel (VSCO-2-CE, CC0), celesta (A Sampled Celesta, CC0), an 80s "tine" e-piano on the off-beat chords and
a soft synth bass (synthesised), kick and shaker (synthesised), hand claps and finger snaps (Body Percussion, CC0),
a music box (synthesised comb tines, pin clicks and the spring's governor), the hums and the girl's singing
(audio/voicesynth.py: WORLD resynthesis of the narrator's own take in the cast's voices).

Versions (render(version, ...) -> (stereo float32 at 48 kHz, info); info['beats'] = the time of every beat)
    studio     the clean commercial mix (the source of the others)
    vhs        1987: the TV commercial taped off the air: mono-ish, wow and flutter, 10.5 kHz top, hiss, kids
               cheering the tag ("Yay!") -- the cold open
    parade     the float's PA horn at the Easter parade, filmed on a camcorder (PA band, street echo, the crowd close
               to the camera, AGC pumping), loops= times round -- under the 1987 parade
    speaker    a tinny portable speaker in the woods with dying batteries: 500 Hz-3.3 kHz, crushed, the motor slowing
               (0.5-0.62x) and sagging, drop-outs and contact crackle, far across the yard -- rule 1
    musicbox   the tune on a music box (an octave up, rubato, the spring running down when wind_down=True)
    hum        Mom humming it (closed mouth, A major, a slow lullaby tempo); who='X': the thing in the narrator's
               old body (the narrator's own range); who='G': Grandma
    knocks     the 2-3-2 family knock on the tune's beat, the tune faint from the woods under it (reference)
    girl       the real Laurie singing it through her sobs, breaking off on "sings his..." (the L voice)
    climax     "Close your eyes and count to seven" in D minor, slow, detuned music box and low piano, every syllable
               on Mom's words (anchors)
    count      one note of the count: n=1..7 (D E F G A Bb C#), slow, minor, detuned; n=7 stops dead (cut=True)
    outro      cheerful and clean (music box, toy piano, celesta, soft claps), the last phrase given to a soft hum
Anchors: render(..., anchors=[(beat, seconds), ...]) bends the tempo so those beats land on those times (the
narrator's "Hop" on beat 0, "Bun" on 4, "Close" on 8, "Find" on 12); otherwise tempo= sets a constant tempo.

CLI: python3 audio/jingle.py [--out W/mix/jingle] [names...]    renders every version (or the names) to wav, checks
     each one (loudness, peak, band shares, the melody's notes found by pitch tracking, for the voices the F0 against
     the melody, for the girl what a recogniser hears) into jingle_check.json and draws jingle_sheet.png
"""
import json, os, sys
import numpy as np, soundfile as sf
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sfx as SX                                        # noqa: E402  (DSP helpers, reverbs, loudness)
import library as LIB                                   # noqa: E402

SR = 48000
W = SX.W
OUT = os.path.join(W, 'mix', 'jingle')
TEMPO = 126.0
SWING = 0.58

# (beat, length in beats, midi, syllable): D major, beat 0 = "Hop"
MELODY = [(0.0, 1.0, 66, 'Hop'), (1.0, 1.0, 69, 'hop'), (2.0, 0.5, 74, 'hop'), (2.5, 0.5, 71, 'a'), (3.0, 0.5, 69, 'long'),
          (3.5, 0.5, 69, 'The'), (4.0, 0.5, 71, 'Bun'), (4.5, 0.5, 69, 'ny'), (5.0, 1.0, 67, 'man'),
          (6.0, 0.5, 66, 'sings'), (6.5, 0.5, 67, 'his'), (7.0, 1.0, 64, 'song'),
          (8.0, 0.5, 62, 'Close'), (8.5, 0.5, 64, 'your'), (9.0, 0.5, 66, 'eyes'), (9.5, 0.5, 67, 'and'),
          (10.0, 0.5, 69, 'count'), (10.5, 0.5, 71, 'to'), (11.0, 0.5, 73, 'se'), (11.5, 0.5, 74, 'ven'),
          (12.0, 0.5, 76, 'Find'), (12.5, 0.5, 74, 'an'), (13.0, 0.5, 71, 'egg'), (13.5, 0.5, 69, 'that'),
          (14.0, 0.5, 67, 'fell'), (14.5, 0.5, 66, 'from'), (15.0, 0.5, 64, 'hea'), (15.5, 1.5, 62, 'ven')]
# chord changes (beat, root midi, pitch classes rel root) ; voicings are built in the 55-67 range
CHORDS = [(0.0, 62, (0, 4, 7)), (4.0, 67, (0, 4, 7)), (6.0, 69, (0, 4, 7, 10)), (8.0, 62, (0, 4, 7)),
          (10.0, 69, (0, 4, 7, 10)), (12.0, 67, (0, 4, 7)), (14.0, 69, (0, 4, 7, 10)), (15.5, 62, (0, 4, 7))]
# oom-pah bass (beat, midi)
BASS = [(0, 38), (1, 45), (2, 38), (3, 42), (4, 43), (5, 47), (6, 45), (7, 40), (8, 38), (9, 45), (10, 45), (11, 49),
        (12, 43), (13, 47), (14, 45), (15, 45), (15.5, 38), (16, 38)]
N_BEATS = 16.0                                          # 8 bars of 2/4 (the tag rings on after it)
KNOCK_BEATS = [0.0, 1.0, 3.0, 3.5, 4.0, 6.0, 7.0]       # 2 (Hop, hop) - 3 (The Bun-ny...) - 2: the family knock
# the narrator's syllables of the jingle lines (narration_clean.wav, film s): boundaries per spoken line
SYLL = {3: [17.905, 18.355, 18.62, 18.855, 18.95, 19.405],
        4: [19.645, 19.73, 19.93, 20.12, 20.395, 20.70, 20.905, 21.365],
        5: [21.645, 21.99, 22.10, 22.45, 22.605, 22.885, 23.075, 23.305, 23.57],
        6: [23.845, 24.30, 24.44, 24.775, 24.955, 25.26, 25.43, 25.66, 25.915]}
# the cold open: the band keeps a steady pulse per phrase (anchors on the phrase downbeats), the melody follows the
# narrator's own syllables like a singer phrasing over a band (each note on its syllable's vowel: boundary + 50 ms)
COLD_OPEN_ANCHORS = [(0.0, 17.94), (4.0, 19.77), (8.0, 21.69), (12.0, 23.89), (16.0, 26.0)]
COLD_OPEN_MELODY = [(b, round(t + 0.05, 3)) for (b, d, m, s), t in
                    zip(MELODY, SYLL[3][:-1] + SYLL[4][:-1] + SYLL[5][:-1] + SYLL[6][:-1])]
MINOR = {66: 65, 71: 70, 78: 77, 83: 82, 54: 53, 59: 58, 42: 41, 47: 46}   # F# -> F, B -> Bb (D harmonic minor)
COUNT_MIDI = [62, 64, 65, 67, 69, 70, 73]             # One..Seven: D E F G A Bb C# (no D: never home)


def hz(m):
    return 440.0 * 2.0 ** ((np.asarray(m, float) - 69.0) / 12.0)


# ================================================================================================== time
class BeatMap:
    """beat -> seconds. anchors [(beat, s)] (monotone cubic through them, edge tempo outside) or a constant tempo;
    swing delays every off-beat eighth to `swing` of its beat."""

    def __init__(self, tempo=TEMPO, anchors=None, swing=SWING, t0=0.0):
        self.swing = swing
        if anchors and len(anchors) >= 2:
            from scipy.interpolate import PchipInterpolator
            b, s = zip(*sorted(anchors))
            self.f = PchipInterpolator(np.array(b, float), np.array(s, float), extrapolate=False)
            self.b0, self.b1 = b[0], b[-1]; self.s0, self.s1 = s[0], s[-1]
            self.r0 = (s[1] - s[0]) / (b[1] - b[0]); self.r1 = (s[-1] - s[-2]) / (b[-1] - b[-2])
        else:
            self.f = None; self.spb = 60.0 / tempo; self.t0 = t0

    def _lin(self, b):
        b = np.asarray(b, float)
        if self.f is None:
            return self.t0 + b * self.spb
        out = self.f(np.clip(b, self.b0, self.b1))
        out = np.where(b < self.b0, self.s0 + (b - self.b0) * self.r0, out)
        return np.where(b > self.b1, self.s1 + (b - self.b1) * self.r1, out)

    def __call__(self, b):
        b = np.asarray(b, float)
        fl = np.floor(b + 1e-9); fr = b - fl
        sw = np.where(np.abs(fr - 0.5) < 1e-6, fl + self.swing, b)
        return self._lin(sw)

    def spb_at(self, b):
        return float(self._lin(b + 0.5) - self._lin(b - 0.5))


# ================================================================================================== instruments
_SMP = {}


def _sample(category, midi, vel=None, rr=0):
    """A library note pitched to midi (resampled), float32 mono."""
    key = (category, round(float(midi), 2), vel, rr)
    if key in _SMP:
        return _SMP[key]
    e, semis = LIB.note(category, midi, vel, rr)
    y = LIB.load(e).mean(1).astype(np.float32)
    if abs(semis) > 1e-3:
        import soxr
        y = soxr.resample(y, SR, SR / 2 ** (semis / 12.0), quality='HQ').astype(np.float32)
    y = y / (np.abs(y).max() + 1e-9)
    _SMP[key] = y
    return y


def toy_piano(midi, vel, rng, detune_cents=0.0):
    """A toy piano note: struck metal rod (partials 1 : 6.27 : 17.55), a beating twin, a wooden box, the hammer."""
    f = hz(midi) * 2 ** (detune_cents / 1200.0)
    d1 = 1.3 * (440.0 / f) ** 0.35
    dur = min(2.6, d1 * 2.2)
    t = np.arange(int(dur * SR)) / SR
    ph = rng.uniform(0, 6.28, 5)
    y = (np.sin(2 * np.pi * f * t + ph[0]) * np.exp(-t / d1)
         + 0.22 * np.sin(2 * np.pi * f * 1.0028 * t + ph[1]) * np.exp(-t / (d1 * 0.8))
         + 0.30 * np.sin(2 * np.pi * f * 6.267 * t + ph[2]) * np.exp(-t / 0.16)
         + 0.07 * np.sin(2 * np.pi * f * 17.55 * t + ph[3]) * np.exp(-t / 0.035))
    y *= (1 - np.exp(-t / 0.0008))
    box = SX.modal([212.0, 488.0, 930.0], [0.05, 0.03, 0.015], [1.0, 0.6, 0.3], 0.15, int(rng.integers(1 << 30)))
    ham = SX.lp(SX.noise(0.004, int(rng.integers(1 << 30))) * np.hanning(int(0.004 * SR)), 3500, 2)
    out = y.astype(np.float32) * vel
    out[:len(box)] += box * 0.10 * vel
    out[:len(ham)] += ham * 0.15 * vel
    return out


def music_box(midi, vel, rng, detune_cents=0.0, decay=1.0):
    """A music-box tine: plucked by a cylinder pin (a tiny click), a long pure fundamental, an inharmonic shimmer."""
    f = hz(midi) * 2 ** (detune_cents / 1200.0)
    d1 = 2.4 * (523.0 / f) ** 0.6 * decay
    dur = min(4.0, d1 * 2.5)
    t = np.arange(int(dur * SR)) / SR
    ph = rng.uniform(0, 6.28, 4)
    y = (np.sin(2 * np.pi * f * t + ph[0]) * np.exp(-t / d1)
         + 0.05 * np.sin(2 * np.pi * 2 * f * t + ph[1]) * np.exp(-t / (d1 * 0.4))
         + 0.22 * np.sin(2 * np.pi * f * 5.43 * t + ph[2]) * np.exp(-t / 0.22)
         + 0.06 * np.sin(2 * np.pi * f * 11.9 * t + ph[3]) * np.exp(-t / 0.05))
    y *= (1 - np.exp(-t / 0.0004))
    click = SX.hp(SX.noise(0.002, int(rng.integers(1 << 30))) * np.hanning(int(0.002 * SR)), 2500, 2) * 0.08
    out = y.astype(np.float32) * vel
    out[:len(click)] += click * vel
    return out


def tine_ep(midi, vel, dur, rng):
    """An 80s FM 'tine' e-piano chord note: a bell attack (1:14 modulator falling away) on a soft sine body."""
    f = hz(midi)
    L = dur + 0.35
    t = np.arange(int(L * SR)) / SR
    idx = 2.2 * np.exp(-t / 0.05)
    y = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * 14 * f * t)) * np.exp(-t / 1.4)
    y += 0.3 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.4)
    env = np.clip((L - t) / 0.3, 0, 1)
    return (y * env * vel).astype(np.float32)


def synth_bass(midi, vel, dur):
    f = hz(midi)
    L = dur + 0.08
    t = np.arange(int(L * SR)) / SR
    y = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t)
    env = (1 - np.exp(-t / 0.004)) * (0.6 + 0.4 * np.exp(-t / 0.12)) * np.clip((L - t) / 0.06, 0, 1)
    return (y * env * vel).astype(np.float32)


def kick(vel, rng):
    t = np.arange(int(0.3 * SR)) / SR
    f = 48 + 90 * np.exp(-t / 0.03)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)
    y[:int(0.003 * SR)] += SX.noise(0.003, int(rng.integers(1 << 30)))[:int(0.003 * SR)] * 0.2
    return (y * vel).astype(np.float32)


def shaker(vel, rng):
    n = int(0.07 * SR); t = np.arange(n) / SR
    z = SX.hp(SX.noise(0.07, int(rng.integers(1 << 30))), 5500, 2)
    env = np.clip(t / 0.012, 0, 1) * np.exp(-t / 0.025)
    return (z * env * vel).astype(np.float32)


def clap(vel, rr):
    e = LIB.get(f'bodyperc__samples_body_handclap_vl2_rr{1 + rr % 6}')
    y = LIB.load(e).mean(1).astype(np.float32)
    return SX.hp(y / (np.abs(y).max() + 1e-9), 250, 2) * vel


def snap(vel, rr):
    ids = [e['id'] for e in LIB.entries(category='score/percussion/body') if '_snap_' in e['id'] and 'pinky' not in e['id']]
    y = LIB.load(ids[rr % len(ids)]).mean(1).astype(np.float32)
    return y / (np.abs(y).max() + 1e-9) * vel


def glock(midi, vel):
    return _sample('score/mallets/glockenspiel', midi) * vel


def celesta(midi, vel):
    return _sample('score/mallets/celesta', midi) * vel


def low_piano(midi, vel, rr=0):
    try:
        return _sample('score/piano/horror_soft', midi, None, rr) * vel
    except KeyError:
        return _sample('score/piano/grand_salamander', midi) * vel


# ================================================================================================== arrangement
def _put(buf, t, y, gain=1.0, pan=0.0):
    i = int(round(t * SR))
    y = SX.st(y) if y.ndim == 1 else y
    if pan:
        y = SX.pan(y, pan)
    a, b = max(0, i), min(len(buf), i + len(y))
    if b > a:
        buf[a:b] += y[a - i:b - i] * gain


def _melody(minor=False, octave=0):
    out = []
    for b, d, m, s in MELODY:
        mm = MINOR.get(m, m) if minor else m
        out.append((b, d, mm + 12 * octave, s))
    return out


def studio(bm, loops=1, seed=0, drums=True, minor=False, inst=('toy', 'celesta', 'glock', 'ep', 'bass'), tag=True,
           detune=12.0, bm_mel=None):
    """The commercial's own mix (dry), `loops` times through. bm_mel: a separate map for the melody (the cold open:
    the melody on the narrator's syllables over the band's steady pulse). Returns (stereo, beat times, end time)."""
    rng = np.random.default_rng(seed)
    mel_t = (lambda b: float(bm_mel(b))) if bm_mel is not None else (lambda b: float(bm(b)))
    total_beats = N_BEATS * loops + (2.0 if tag else 0.0)
    end = float(bm(total_beats)) + 2.5
    buf = np.zeros((int(end * SR) + SR, 2), np.float32)
    tune = {m: rng.uniform(-detune, detune) for m in range(20, 128)}   # an old toy piano: each rod its own tuning
    for L in range(loops):
        o = L * N_BEATS
        for b, d, m, s in _melody(minor):
            t = mel_t(o + b)
            acc = 1.0 if abs(b - round(b)) < 1e-6 else 0.82
            if 'toy' in inst:
                _put(buf, t, toy_piano(m, 0.9 * acc * rng.uniform(0.92, 1.0), rng, tune[m]), 1.0, -0.1)
            if 'celesta' in inst:
                _put(buf, t + 0.004, celesta(m + 12, 0.42 * acc), 1.0, 0.25)
            if 'glock' in inst and acc == 1.0:
                _put(buf, t + 0.002, glock(m + 24, 0.22), 1.0, 0.35)
            if 'musicbox' in inst:
                _put(buf, t, music_box(m + 12, 0.9 * acc, rng, tune[m] * 0.5), 1.0, 0.0)
        if 'ep' in inst:
            for k, (b, root, pcs) in enumerate(CHORDS):
                nb = CHORDS[k + 1][0] if k + 1 < len(CHORDS) else N_BEATS + 1
                if minor:
                    root = MINOR.get(root, root)
                notes = sorted(55 + ((root + p - 55) % 12) for p in pcs)
                if minor and root == 62:
                    notes = [n - 1 if (n % 12) == 6 else n for n in notes]
                if minor and root == 67:
                    notes = [n - 1 if (n % 12) == 11 else n for n in notes]
                x = b + 0.5
                while x < nb - 1e-6:                    # off-beat "pah" chords
                    t = float(bm(o + x)); dd = float(bm(o + x + 0.4)) - t
                    for nn in notes:
                        _put(buf, t, tine_ep(nn, 0.16, dd, rng), 1.0, 0.0)
                    x += 1.0
        if 'bass' in inst:
            for k, (b, m) in enumerate(BASS):
                if b >= N_BEATS and L < loops - 1:
                    continue
                if minor:
                    m = MINOR.get(m, m)
                nb = BASS[k + 1][0] if k + 1 < len(BASS) else b + 1.0
                t = float(bm(o + b)); dd = (float(bm(o + nb)) - t) * 0.8
                _put(buf, t, synth_bass(m, 0.5, dd), 1.0, 0.0)
        if drums:
            for x in np.arange(0, N_BEATS, 0.5):
                t = float(bm(o + x))
                if abs(x % 2) < 1e-6:
                    _put(buf, t, kick(0.6, rng), 1.0, 0.0)
                if abs(x % 2 - 1) < 1e-6:
                    _put(buf, t, clap(0.28, int(x)), 1.0, 0.1)
                _put(buf, t, shaker(0.10 if abs(x - round(x)) < 1e-6 else 0.07, rng), 1.0, 0.3)
    if tag:                                             # the tag: the D chord rings, a glock sparkle, a bell "ding"
        o = loops * N_BEATS
        t = float(bm(o))
        for j, m in enumerate((74, 78, 81, 86)):
            _put(buf, t + 0.06 * j, glock(m + 12, 0.25), 1.0, -0.3 + 0.2 * j)
        _put(buf, t + 0.3, glock(98, 0.35), 1.0, 0.2)
        _put(buf, t + 0.3, celesta(86, 0.35), 1.0, -0.2)
        if 'bass' in inst:
            _put(buf, t, synth_bass(38, 0.55, 1.4), 1.0, 0.0)
        if 'ep' in inst:
            for nn in (57, 62, 66):
                _put(buf, t, tine_ep(MINOR.get(nn, nn) if minor else nn, 0.18, 1.4, rng), 1.0, 0.0)
    beats = [float(bm(b)) for b in np.arange(0, total_beats + 0.5, 1.0)]
    return SX.fade(buf[:int(end * SR)], 0.002, 0.3), beats, end


# ================================================================================================== chains
def _wow(y, depth=0.0025, hz_=0.45, fl=0.0008, fl_hz=7.0, seed=0):
    n = len(y); rng = np.random.default_rng(seed)
    t = np.arange(n) / SR
    r = 1 + depth * np.sin(2 * np.pi * hz_ * t + rng.uniform(0, 6)) + fl * np.sin(2 * np.pi * fl_hz * t + rng.uniform(0, 6))
    pos = np.clip(np.cumsum(r) - r[0], 0, n - 2); i = pos.astype(np.int64); f = (pos - i)[:, None].astype(np.float32)
    return (y[i] * (1 - f) + y[i + 1] * f).astype(np.float32)


def vhs(y, seed=0, lp_hz=10500, hiss_db=-46.0, width=0.18, dropouts=0.25):
    """A 1987 VHS recording: wow and flutter, linear-track band (70 Hz-10.5 kHz), soft tape saturation, near mono,
    hiss, a few dropouts."""
    rng = np.random.default_rng(seed)
    y = _wow(SX.st(y), seed=seed)
    y = SX.lp(SX.hp(y, 70, 2), lp_hz, 4)
    y = SX.eq(y, ('peak', 3200, -1.5, 0.8), ('ls', 150, 1.0, 0.7))
    pk = SX.peak(y) + 1e-9
    y = (np.tanh(1.3 * y / pk) / np.tanh(1.3) * pk).astype(np.float32)
    y = SX.width(y, width)
    n = len(y)
    hiss = SX.hp(rng.standard_normal((n, 2)).astype(np.float32), 1800, 1) * pk * 10 ** (hiss_db / 20)
    y = y + SX.width(hiss, 0.4)
    k = int(dropouts * n / SR / 10)
    for _ in range(k):
        a = int(rng.uniform(0, n - SR * 0.2)); L = int(rng.uniform(0.02, 0.07) * SR)
        g = 1 - 0.75 * np.hanning(L)
        y[a:a + L] *= g[:, None].astype(np.float32)
    return y


def pa_horn(y):
    """The float's PA horn: 380 Hz-5.2 kHz, the horn's 2.2 kHz honk, driven."""
    m = SX.mono(SX.st(y))
    m = SX.lp(SX.hp(m, 380, 4), 5200, 4)
    m = SX.eq(m, ('peak', 2200, 5.0, 1.2), ('peak', 900, 2.0, 1.0))
    pk = SX.peak(m) + 1e-9
    return SX.st((np.tanh(2.0 * m / pk) / np.tanh(2.0) * pk).astype(np.float32))


def camcorder(y, seed=0):
    """A home camcorder at the parade: mono mic, AGC that pumps, 120 Hz-9 kHz, then the tape."""
    m = SX.mono(SX.st(y))
    m = SX.lp(SX.hp(m, 120, 2), 9000, 2)
    m = SX.compress(m, SX.db(SX.peak(m)) - 20, 4.0, 0.01, 0.35, makeup=0.0)
    return vhs(SX.st(m), seed, lp_hz=9000, hiss_db=-42.0, width=0.08, dropouts=0.4)


def dying_speaker(y, seed=0, speed=0.56, sag_every=4.0, dropout_rate=0.5):
    """A cheap portable tape player in the woods, batteries dying: the motor runs slow (speed) and sags (every
    ~sag_every s it drops 15-25 % and claws back), so the pitch sags with it; a tiny cone (520 Hz-3.3 kHz) driven
    asymmetrically; the level follows the motor; contact drop-outs with crackle."""
    rng = np.random.default_rng(seed)
    x = SX.mono(SX.st(y)).astype(np.float64)
    n_out = int(len(x) / speed * 1.15)
    t = np.arange(n_out) / SR
    sp = speed * (1 + 0.035 * np.sin(2 * np.pi * 0.13 * t + rng.uniform(0, 6)) + 0.006 * np.sin(2 * np.pi * 5.1 * t))
    tt = rng.uniform(1.0, sag_every)
    while tt < t[-1]:
        depth = rng.uniform(0.12, 0.25); a = rng.uniform(0.25, 0.5); r = rng.uniform(0.6, 1.4)
        sag = np.where(t < tt, 0, np.where(t < tt + a, (t - tt) / a, np.clip(1 - (t - tt - a) / r, 0, 1)))
        sp *= 1 - depth * np.sin(np.pi / 2 * sag)
        tt += rng.uniform(0.6, 1.6) * sag_every
    pos = np.cumsum(sp); pos -= pos[0]
    keep = pos < len(x) - 2
    pos = pos[keep]; sp = sp[keep]
    i = pos.astype(np.int64); f = pos - i
    z = x[i] * (1 - f) + x[i + 1] * f
    z = SX.lp(SX.hp(z.astype(np.float32), 520, 4), 3300, 4)
    z = SX.eq(z, ('peak', 1400, 6.0, 1.3), ('peak', 2600, 3.0, 2.0))
    pk = SX.peak(z) + 1e-9
    z = np.tanh(2.2 * (z / pk + 0.18 * np.abs(z / pk))) * pk * 0.6
    z = z * (0.55 + 0.45 * np.clip((sp / speed - 0.7) / 0.3, 0, 1))      # weaker as it sags
    n = len(z)
    k = int(dropout_rate * n / SR)
    for _ in range(k):
        a = int(rng.uniform(0, max(1, n - SR * 0.3))); L = int(rng.uniform(0.04, 0.25) * SR)
        g = np.ones(L); r_ = int(0.004 * SR); g[r_:-r_] = rng.uniform(0.0, 0.08)
        g[:r_] = np.linspace(1, g[r_], r_); g[-r_:] = np.linspace(g[r_], 1, r_)
        z[a:a + L] *= g[:len(z[a:a + L])]
        for e_ in (a, a + L):
            c = int(rng.integers(4, 12))
            for _c in range(c):
                j = e_ + int(rng.uniform(-0.01, 0.01) * SR)
                if 0 <= j < n - 3:
                    z[j:j + 3] += rng.uniform(-1, 1) * pk * 0.25
    return SX.st(z.astype(np.float32))


def far_woods(y, wet=0.55):
    """Far across the yard, from the treeline: air absorption, the forest and the house fronts."""
    y = SX.lp(SX.st(y), 4200, 2)
    y = SX.reverb(y, 'forest', wet, 0.02, dry=0.55)
    return SX.reverb(y, 'street', 0.25, 0.0, dry=1.0)


def _level(y, lufs=-23.0):
    L = SX.lufs_int(y) if len(y) > SR * 0.6 else SX.mom_max(y)
    return (y * 10 ** ((lufs - L) / 20)).astype(np.float32) if L > -90 else y


def _crowd(dur, seed=0, cheer_at=None, kids=1.0, bed=0.5):
    """The parade crowd from the bunny set (kids cheering close, the adult walla far), dur s; cheer_at: s of a swell."""
    import sfx as S
    rng = np.random.default_rng(seed)
    k = [e for e in S.src('crowd_parade') if 'walla_distant_marching_band_kids_cheering' in e['id']]
    a = [e for e in S.src('crowd_parade') if 'cheltenham' in e['id'] and 'parade_ring' in e['id'] and 'winner' not in e['id']]
    out = np.zeros((int(dur * SR), 2), np.float32)
    if k:
        x = S.excerpt(k[0], dur, rng, 1.5)
        out += SX.lp(x, 9000, 2) * kids
    if a:
        x = S.excerpt(a[0], dur, rng, 1.5)
        out += SX.lp(x, 2500, 2) * bed * 0.6
    if cheer_at is not None and k:
        sw = np.clip(1 - np.abs(np.arange(len(out)) / SR - cheer_at) / 1.6, 0, 1) ** 1.5
        out *= (1 + 1.6 * sw)[:, None].astype(np.float32)
    return out


# ================================================================================================== versions
def render(version, anchors=None, tempo=None, seed=0, **kw):
    """One version (see the module docstring). Returns (stereo float32, info)."""
    v = version
    if v in ('studio', 'vhs', 'parade', 'speaker', 'outro', 'knocks'):
        bm = BeatMap(tempo or TEMPO, anchors)
        mel = kw.get('melody_anchors')
        bm_mel = BeatMap(tempo or TEMPO, mel, swing=0.5) if mel else None
    if v == 'studio':
        y, beats, end = studio(bm, kw.get('loops', 1), seed)
        return _level(y, -16), {'beats': beats}
    if v == 'vhs':
        y, beats, end = studio(bm, 1, seed, bm_mel=bm_mel)
        y = _level(y, -18)
        tag_t = beats[16] if len(beats) > 16 else end - 1.5
        cr = _crowd(len(y) / SR, seed + 1, cheer_at=tag_t + 0.6, kids=0.0, bed=0.0)
        k = _crowd(len(y) / SR, seed + 2, kids=1.0, bed=0.0)
        g = np.clip((np.arange(len(y)) / SR - (tag_t - 0.2)) / 0.4, 0, 1) * np.clip(1 - (np.arange(len(y)) / SR - tag_t - 2.0) / 1.0, 0, 1)
        y = y + _level(k, -27) * g[:, None].astype(np.float32) * 1.6
        y = vhs(y, seed)
        info = {'beats': beats, 'tag': tag_t}
        if bm_mel is not None:
            info['note_times'] = [float(bm_mel(b)) for b, d, m, s in MELODY]
        return _level(y, -18), info
    if v == 'parade':
        loops = int(kw.get('loops', 3))
        y, beats, end = studio(bm, loops, seed)
        y = pa_horn(_level(y, -18))
        y = SX.reverb(y, 'street', 0.45, 0.0, dry=1.0)[:len(y)]
        n = len(y); t = np.arange(n) / SR
        pass_t = kw.get('pass_at', n / SR * 0.5)          # the float nearest the camera
        dist = 1 / (1 + ((t - pass_t) / 9.0) ** 2)
        y = SX.lp(y, 5200, 1) * (0.35 + 0.65 * dist)[:, None].astype(np.float32)
        cr = _crowd(n / SR, seed + 3, cheer_at=pass_t, kids=1.0, bed=0.7)
        y = _level(y, -24) + _level(cr, -24)
        y = camcorder(y, seed)
        return _level(y, -18), {'beats': beats, 'pass_at': pass_t}
    if v == 'speaker':
        loops = int(kw.get('loops', 3))
        y, beats, end = studio(BeatMap(tempo or TEMPO), loops, seed, drums=True, tag=False)
        sp = float(kw.get('speed', 0.56))
        z = dying_speaker(_level(y, -18), seed, speed=sp)
        if kw.get('far', True):
            z = far_woods(z)
        beats = [b / sp for b in beats]                   # nominal (the sags move them)
        return _level(z, -22), {'beats': beats, 'speed': sp}
    if v == 'musicbox':
        rng = np.random.default_rng(seed)
        bm = BeatMap(tempo or 100.0, anchors, swing=0.55)
        minor = bool(kw.get('minor', False))
        loops = int(kw.get('loops', 1)); wind_down = bool(kw.get('wind_down', False))
        n_b = N_BEATS * loops + 1
        # the spring: rubato, slowing at the end when it runs down
        bt = np.arange(0, n_b + 1, 0.5)
        slow = 1 + (np.clip((bt - (n_b - 6)) / 6, 0, 1) ** 2 * 1.8 if wind_down else np.zeros_like(bt))
        tt = np.concatenate([[0], np.cumsum(np.diff(bm(bt)) * slow[1:])]) + 0.3
        tmap = lambda b: float(np.interp(b, bt, tt)) + rng.normal(0, 0.006)
        end = tt[-1] + 3.5
        buf = np.zeros((int(end * SR), 2), np.float32)
        tune = {m: rng.uniform(-6, 6) for m in range(20, 128)}
        for L in range(loops):
            for b, d, m, s in _melody(minor):
                t = tmap(L * N_BEATS + b)
                _put(buf, t, music_box(m + 12, 0.8 * rng.uniform(0.85, 1.0), rng, tune[m]), 1.0, 0.1)
            for b, m in BASS[::2]:                         # the comb's low tines: the roots on the down-beats
                if b < N_BEATS:
                    mm = MINOR.get(m, m) if minor else m
                    _put(buf, tmap(L * N_BEATS + b), music_box(mm + 24, 0.45, rng, tune[mm]), 1.0, -0.1)
        n = len(buf); t = np.arange(n) / SR
        whir = SX.bp(np.random.default_rng(seed).standard_normal(n).astype(np.float32), 900, 4200, 2)
        whir *= (0.6 + 0.4 * np.sin(2 * np.pi * 23 * t)).astype(np.float32) * np.clip((tt[-1] - t) / 0.5, 0, 1).astype(np.float32)
        buf += SX.st(whir) * 0.004
        if kw.get('wind', False):                          # the winding first (the bunny set's winding ratchet)
            import sfx as S
            try:
                if 'music_box_wind' not in S.RECIPES:
                    raise KeyError('no music_box_wind recipe')
                ww = SX.st(S.render('music_box_wind', seed))[:int(1.6 * SR)]
                buf = np.concatenate([ww * 0.6, buf])
                tt = tt + len(ww) / SR
            except Exception as e:
                print('[jingle] winding skipped:', repr(e)[:80])
        y = SX.reverb(buf, 'living', 0.18, 0.003)
        return _level(y, -22), {'beats': [float(np.interp(b, bt, tt)) for b in np.arange(0, n_b + 1)]}
    if v in ('hum', 'hum_x', 'hum_g'):
        import voicesynth as VS
        who = {'hum': 'M', 'hum_x': 'X', 'hum_g': 'G'}[v] if 'who' not in kw else kw['who']
        bm = BeatMap(tempo or 84.0, anchors, swing=0.55)
        phrases = kw.get('phrases', (0, 1, 2, 3))
        tr = float(kw.get('transpose', -5.0 if who in ('M', 'G') else -17.0))
        sel = [(b, d, m, s) for b, d, m, s in MELODY if int(b // 4) in phrases or (b == 3.5 and 1 in phrases)]
        if not sel:
            raise ValueError('no phrases')
        b0 = sel[0][0]
        times = [float(bm(b - b0)) + 0.45 for b, d, m, s in sel]
        durs = [max(0.12, float(bm(b - b0 + d)) - float(bm(b - b0)) - 0.03) for b, d, m, s in sel]
        mids = [m for b, d, m, s in sel]
        brk = [float(bm(4 * p - b0)) + 0.45 for p in phrases[1:] if p * 4 > b0]
        stac = {i for i, (b, d, m, s) in enumerate(sel) if s in ('Hop', 'hop')}
        y = VS.hum(times, mids, durs, who=who, transpose=tr, seed=seed, staccato=stac, phrase_breaks=brk)
        y = SX.reverb(SX.st(y.astype(np.float32)), 'living', 0.1, 0.002)
        return _level(y, -24), {'beats': [float(bm(b)) + 0.45 for b in np.arange(0, 17)], 'who': who}
    if v == 'girl':
        import voicesynth as VS
        rng = np.random.default_rng(seed)
        bm = BeatMap(tempo or 64.0, None, swing=0.5)
        # "Hop... hop... hop a-long... the Bun-ny-man sings his..."  (breaks, a sob, the last note never comes)
        sel = MELODY[:11]
        lag = 0.0; notes = []
        for k, (b, d, m, s) in enumerate(sel):
            if k in (1, 2):
                lag += rng.uniform(0.25, 0.45)               # she waits between the hops
            if k == 5:
                lag += 1.05                                  # she has to stop: a sob
            t = float(bm(b)) + 0.3 + lag
            dd = (float(bm(b + d)) - float(bm(b))) * (1.25 if k in (4, 10) else 0.95)
            notes.append((t, dd, m))
        notes11 = notes[:11]
        sylls = [SYLL[3], SYLL[4][:7]]                    # 5 + 6 syllables: "Hop hop hop a long" "The Bun ny man sings his"
        y = VS.sing(sylls, notes11, who='L', seed=seed, sob_gaps=[notes11[4][0] + notes11[4][1] + 0.12],
                    cracks=0.35)
        cr = VS.cry(4.5, 'L', seed + 7, 0.7)
        tail = notes11[-1][0] + notes11[-1][1] + 0.05
        out = np.zeros(int((tail + len(cr) / SR + 0.5) * SR))
        out[:len(y)] += y
        i = int(tail * SR); out[i:i + len(cr)] += cr * 0.8
        out = SX.st(out.astype(np.float32))
        return _level(out, -24), {'notes': notes11, 'cry_at': tail}
    if v == 'climax':
        rng = np.random.default_rng(seed)
        spb = 60.0 / (tempo or 44.0)
        bm = BeatMap(tempo or 44.0, anchors, swing=0.5, t0=0.4 - 8 * spb)   # standalone: "Close" at 0.4 s
        buf = np.zeros((int((float(bm(17)) + 6) * SR), 2), np.float32)
        sel = [x for x in _melody(minor=True) if 8 <= x[0] < 12] if kw.get('phrase3_only', True) else _melody(True)
        for b, d, m, s in sel:
            t = float(bm(b))
            for dc in (-18, 16):
                _put(buf, t, music_box(m + 12, 0.45, rng, dc, decay=1.4), 1.0, 0.3 if dc > 0 else -0.3)
            _put(buf, t + 0.01, low_piano(m - 24, 0.4, int(b * 2) % 2), 1.0, 0.0)
        y = _wow(buf, depth=0.004, hz_=0.21, fl=0.0, seed=seed)
        y = SX.reverb(SX.lp(y, 6500, 2), 'hall', 0.35, 0.02)
        return _level(y, -24), {'beats': [float(bm(b)) for b in range(8, 13)]}
    if v == 'count':
        rng = np.random.default_rng(seed + int(kw.get('n', 1)))
        nn = int(np.clip(kw.get('n', 1), 1, 7))
        m = COUNT_MIDI[nn - 1]
        L = 4.5
        buf = np.zeros((int(L * SR), 2), np.float32)
        for dc in (-22, 19):
            _put(buf, 0.0, music_box(m + 12, 0.5, rng, dc, decay=1.6), 1.0, 0.35 if dc > 0 else -0.35)
        _put(buf, 0.005, low_piano(m - 24, 0.55, nn % 2), 1.0, 0.0)
        _put(buf, 0.0, SX.st(SX.sub_boom(hz(m - 36) * 1.4, hz(m - 36), 1.8, 0.0)) * 0.3, 1.0, 0.0)
        y = _wow(buf, depth=0.005, hz_=0.3, fl=0.0, seed=seed)
        y = SX.reverb(SX.lp(y, 6000, 2), 'hall', 0.3, 0.02)
        if kw.get('cut', nn == 7):                        # "Seven": the note is cut dead after 0.32 s
            k = int(0.32 * SR); y = y[:k + int(0.012 * SR)].copy()
            y[k:] *= np.linspace(1, 0, len(y) - k)[:, None].astype(np.float32)
        return _level(y, -22), {'n': nn, 'midi': m}
    if v == 'outro':
        y, beats, end = studio(BeatMap(tempo or 118.0, anchors), 1, seed, drums=False,
                               inst=('toy', 'celesta', 'musicbox', 'bass'), tag=False, detune=5.0)
        # the instruments leave on the last phrase; a soft hum finishes it
        cut = beats[12] - 0.05
        n = len(y); t = np.arange(n) / SR
        y = y * np.clip(1 - (t - cut) / 0.8, 0, 1)[:, None].astype(np.float32)
        h, hi = render('hum', tempo=118.0 * 0.82, seed=seed + 5, phrases=(3,), who=kw.get('who', 'M'))
        out = np.zeros((max(n, int((cut + len(h) / SR) * SR)), 2), np.float32)
        out[:n] += _level(y, -20)
        i = int((cut - 0.45) * SR)
        out[i:i + len(h)] += _level(h, -24)[:len(out) - i]
        return _level(SX.reverb(out, 'living', 0.12, 0.003), -20), {'beats': beats, 'hum_from': cut}
    if v == 'knocks':
        import sfx as S
        y, beats, end = studio(bm, 1, seed, tag=False)
        far = far_woods(dying_speaker(_level(y, -18), seed, speed=1.0, sag_every=99, dropout_rate=0.05))[:len(y)]
        kn = S.render('knock_family', seed, 'inside', beat=60.0 / (tempo or TEMPO))
        out = np.zeros((max(len(far), len(kn)) + SR, 2), np.float32)
        out[:len(far)] += _level(far, -34)
        out[:len(kn)] += kn
        return out, {'beats': beats, 'knocks_at': [float(bm(b)) for b in KNOCK_BEATS]}
    raise KeyError(f'unknown jingle version {version!r}')


VERSIONS = ('studio', 'vhs', 'parade', 'speaker', 'musicbox', 'hum', 'hum_x', 'knocks', 'girl', 'climax', 'count',
            'outro')


# ================================================================================================== checks
def melody_check(y, info, minor=False, transpose=0.0, first=0, count=None, swing=SWING):
    """Is the tune there? At each melody note (its onset from info['beats'], swung eighths), the chroma of the next
    120 ms (CQT, the note's onset energy against the 80 ms before it) is ranked: the note's pitch class should be
    the strongest NEW pitch class (rank 1) or second (the chord's root can win on a downbeat). Returns the ranks."""
    import librosa
    m = SX.mono(SX.st(y))
    x = librosa.resample(m, orig_sr=SR, target_sr=22050)
    C = np.abs(librosa.cqt(x, sr=22050, hop_length=256, fmin=librosa.note_to_hz('C3'), n_bins=60, bins_per_octave=12))
    tt = librosa.times_like(C, sr=22050, hop_length=256)
    beats = info.get('beats') or []
    ranks = []
    sel = MELODY if count is None else MELODY[first:first + count]
    note_t = info.get('note_times')
    for k, (b, d, mm, s) in enumerate(sel):
        if note_t is not None:
            if k >= len(note_t):
                break
            t0 = float(note_t[k])
        else:
            if not beats or b + 0.1 > len(beats) - 1:
                break
            fl = np.floor(b + 1e-9); fr = b - fl
            bb = fl + swing if abs(fr - 0.5) < 1e-6 else b
            t0 = float(np.interp(bb, np.arange(len(beats)), beats))
        now = C[:, (tt >= t0 + 0.01) & (tt <= t0 + 0.13)].mean(1)
        bef = C[:, (tt >= t0 - 0.09) & (tt <= t0 - 0.01)].mean(1) if t0 > 0.1 else np.zeros(60)
        new_ = np.maximum(now - 0.6 * bef, 0)
        chroma = new_.reshape(5, 12).sum(0)
        want = int(round((MINOR.get(mm, mm) if minor else mm) + transpose)) % 12
        order = list(np.argsort(chroma)[::-1])
        ranks.append(order.index(want) + 1)
    r = np.array(ranks)
    return {'notes_checked': len(r), 'rank1': int((r == 1).sum()), 'rank_le2': int((r <= 2).sum()),
            'ranks': [int(v) for v in r]}


def measure(y):
    y = SX.st(y)
    P = np.abs(np.fft.rfft(SX.mono(y)[:SR * 60])) ** 2; f = np.fft.rfftfreq(min(len(y), SR * 60), 1 / SR)
    tot = P.sum() + 1e-20
    return {'dur': round(len(y) / SR, 2), 'lufs': round(SX.lufs_int(y), 1), 'peak_db': round(float(SX.db(SX.peak(y))), 1),
            'low_mid_high_pct': [round(100 * float(P[f < 250].sum() / tot), 1), round(100 * float(P[(f >= 250) & (f < 4000)].sum() / tot), 1),
                                 round(100 * float(P[f >= 4000].sum() / tot), 1)]}


def main():
    names = [a for a in sys.argv[1:] if not a.startswith('--')] or list(VERSIONS)
    out = OUT
    if '--out' in sys.argv:
        out = sys.argv[sys.argv.index('--out') + 1]
    os.makedirs(out, exist_ok=True)
    pj = os.path.join(out, 'jingle_check.json')
    chk = json.load(open(pj)) if os.path.exists(pj) else {}
    jobs = []
    for nm in names:
        if nm == 'count':
            jobs += [(f'count_{k}', 'count', dict(n=k)) for k in range(1, 8)]
        elif nm == 'vhs':
            z = COLD_OPEN_ANCHORS[0][1] - 0.6
            jobs.append(('vhs_cold_open', 'vhs', dict(anchors=[(b, t - z) for b, t in COLD_OPEN_ANCHORS],
                                                      melody_anchors=[(b, t - z) for b, t in COLD_OPEN_MELODY])))
            jobs.append(('vhs', 'vhs', {}))
        elif nm == 'musicbox':
            jobs.append(('musicbox', 'musicbox', dict(wind=True)))
            jobs.append(('musicbox_wind_down', 'musicbox', dict(wind_down=True)))
            jobs.append(('musicbox_minor', 'musicbox', dict(minor=True, tempo=72.0)))
        elif nm == 'speaker':
            jobs.append(('speaker', 'speaker', dict(loops=3)))
            jobs.append(('speaker_near', 'speaker', dict(loops=1, far=False)))
        else:
            jobs.append((nm, nm, {}))
    for fn, ver, kw in jobs:
        y, info = render(ver, seed=3, **kw)
        sf.write(os.path.join(out, fn + '.wav'), y, SR, subtype='PCM_24')
        r = measure(y)
        try:
            if ver in ('studio', 'vhs', 'outro', 'knocks'):
                r['melody'] = melody_check(y, info, count=12 if ver == 'outro' else None)
            elif ver == 'parade':
                r['melody'] = melody_check(y, info)
            elif ver == 'musicbox':
                r['melody'] = melody_check(y, info, minor=kw.get('minor', False), swing=0.55)
            elif ver in ('hum', 'hum_x'):
                r['melody'] = melody_check(y, info, transpose=-5.0 if ver == 'hum' else -17.0, swing=0.55)
            elif ver == 'climax':
                bt = info['beats']
                r['melody'] = melody_check(y, {'beats': [0.0] * 8 + bt}, minor=True, first=12, count=8, swing=0.5)
        except Exception as e:
            r['melody_error'] = repr(e)[:120]
        r['info'] = {k: (v if not isinstance(v, list) or len(v) < 40 else v[:40]) for k, v in info.items()}
        chk[fn] = r
        print(fn, json.dumps({k: v for k, v in r.items() if k != 'info'}), flush=True)
    json.dump(chk, open(pj, 'w'), indent=1)
    print('wrote', pj)


if __name__ == '__main__':
    main()
