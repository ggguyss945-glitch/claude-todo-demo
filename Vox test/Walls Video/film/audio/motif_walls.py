"""motif_walls.py: THEO'S ADDRESS SONG, the returning motif of "If Your Little Brother Says Someone Lives In The
Walls... DON'T LAUGH": an ORIGINAL little tune written for this film (no melody of any existing song), its warped
returns (Mr. Pell humming it inside the walls) and the "hush-a-bye" lullaby it ends on. No sung words: the voice track
carries every sung line (Theo's and Pell's, baked); this module only plays the tune, so it never doubles a voice.

The tune (D major, 4/4; the words are only the syllable plan: one note per syllable)
    A  Four-teen Lark-spur Lane     F#4 A4 | D5. C#5 | A4 (held)          the leap up to "Lark", sweet
    B  Ma-ple Falls                 B4 A4 | F#4 (held)
    C  That's my house              G4 A4 | B4 (held)                     rising: a question
    D  That's my name               A4 F#4 | D4 (held)                    falling home: the answer
    H  hush-a-bye, hush-a-bye, mm   A4 B4 A4 | F#4 G4 F#4 | E4 ... D4      the lullaby (3 + 3 + 6 beats)
    harmony  A: D (D/A) | B: G D | C: G Em | D: A7 D | H: D | Bm | A7 D       (one low tine / bass per change)

Versions: render(version, anchors=None, tempo=None, seed=0, **kw) -> (stereo float32 48 kHz, info)
    info: notes [(t, midi, syllable)], beats, total; gap = (t of the last note, end) (music_plan's 'gap_at' lands the
    last note: the home D, or "house" where Pell's version stops)
    toy     Theo's song: a toy piano (struck rods), a music box an octave up, soft toy bass; 104 bpm, a little
            out of tune the same way every time; phrases ABCD, loops=
    box     the same on a music box alone, 84 bpm, fragile (the hook, Theo's room, rule 5's card)
    first   phrase A only on the music box, ringing out: a 3-4 s sting; amount= warps it (0 sweet, 1 wrong)
    wall    Mr. Pell humming it INSIDE THE WALL: a man's closed-mouth hum an octave down, slow (50 bpm and sagging),
            held too long at the phrase ends, every note drifting out (fixed + random cents, the third sinking F# -> F
            as amount rises), a faint detuned music box under it; through plaster and studs (low-passed, the stud
            cavity's boom, close and dry). phrases= 'AC' (default: "Fourteen Larkspur Lane... that's my house", the
            words of line 172: he stops on HOUSE, unresolved, and never sings "that's my name"), 'ABCD', 'ACH' ...
            amount= 0..1 (default 0.7), hush=True adds the lullaby
    vent    "Hush-a-bye. That's my house.": the hum through the floor vent's sheet-metal duct (band 250 Hz-3 kHz, a
            tin ring), phrases H1 + C; amount=
    hush    the lullaby alone (H1 H2 H3), inst='box' (a soft slow music box rocking, 60 bpm), 'hum' (hummed in the
            wall) or 'hum_room' (hummed close, in the room: the tuck-in)
    warm    the motif redeemed (rule seven's "Believe me.", the last line): toy piano + celesta, soft grand-piano chords,
            in tune, 88 bpm, ABCD then the lullaby resolved home on a held D add9; short=True: C D + H3 only

CLI: python3 audio/motif_walls.py [versions...]   renders W/mix/motif/<v>.wav (16-bit), checks each (loudness, peak,
     band shares, the melody found note by note: CQT chroma rank of each note's pitch class, the interval contour
     against the score) into motif_check.json and draws motif_sheet.png.
"""
import json, os, sys
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sfx as SX                                        # noqa: E402
import jingle as J                                      # noqa: E402  (the instruments)

SR = 48000
W = SX.W
OUT = os.path.join(W, 'mix', 'motif')
# (beat in phrase, length in beats, midi, syllable)
PHRASES = {
    'A': [(0.0, 0.5, 66, 'Four'), (0.5, 0.5, 69, 'teen'), (1.0, 0.75, 74, 'Lark'), (1.75, 0.25, 73, 'spur'),
          (2.0, 2.0, 69, 'Lane')],
    'B': [(0.0, 0.5, 71, 'Ma'), (0.5, 0.5, 69, 'ple'), (1.0, 3.0, 66, 'Falls')],
    'C': [(0.0, 0.5, 67, "That's"), (0.5, 0.5, 69, 'my'), (1.0, 3.0, 71, 'house')],
    'D': [(0.0, 0.5, 69, "That's"), (0.5, 0.5, 66, 'my'), (1.0, 3.0, 62, 'name')],
    'H1': [(0.0, 1.0, 69, 'Hush'), (1.0, 0.5, 71, 'a'), (1.5, 1.5, 69, 'bye')],
    'H2': [(0.0, 1.0, 66, 'hush'), (1.0, 0.5, 67, 'a'), (1.5, 1.5, 66, 'bye')],
    'H3': [(0.0, 2.0, 64, 'mm'), (2.0, 4.0, 62, 'mm')],
}
PLEN = {'A': 4.0, 'B': 4.0, 'C': 4.0, 'D': 4.0, 'H1': 3.0, 'H2': 3.0, 'H3': 6.0}
# (beat in phrase, bass midi, chord)
HARM = {'A': [(0.0, 50, (62, 66, 69)), (2.0, 45, (62, 66, 69))], 'B': [(0.0, 43, (59, 62, 67)), (1.0, 50, (62, 66, 69))],
        'C': [(0.0, 43, (59, 62, 67)), (1.0, 40, (59, 64, 67))], 'D': [(0.0, 45, (61, 64, 67)), (1.0, 50, (62, 66, 69))],
        'H1': [(0.0, 50, (62, 66, 69))], 'H2': [(0.0, 47, (59, 62, 66))],
        'H3': [(0.0, 45, (61, 64, 67)), (2.0, 50, (62, 66, 69, 76))]}
# the toy's worn rods: every pitch wrong by its own fixed amount (cents), the same way every time it returns
TUNING = {40: 9, 43: -7, 45: 6, 47: -11, 50: -5, 59: 8, 61: -9, 62: -6, 64: 10, 66: 12, 67: -8, 69: 7, 71: -12,
          73: 14, 74: -9, 76: 11}
VERSIONS = ('toy', 'box', 'first', 'wall', 'vent', 'hush', 'warm')
BASE_TEMPO = {'toy': 104.0, 'box': 84.0, 'first': 84.0, 'wall': 50.0, 'vent': 48.0, 'hush': 60.0, 'warm': 88.0}
DEFAULT_PHRASES = {'toy': 'ABCD', 'box': 'ABCD', 'first': 'A', 'wall': 'AC', 'vent': 'H1C', 'hush': 'H1H2H3',
                   'warm': 'ABCDH1H2H3'}


def _split(ph):
    """'ABCDH1H2H3' -> ['A', 'B', 'C', 'D', 'H1', 'H2', 'H3']."""
    out, i = [], 0
    while i < len(ph):
        k = ph[i:i + 2] if ph[i] == 'H' else ph[i]
        out.append(k); i += len(k)
    return out


def score(phrases):
    """Notes [(beat, beats, midi, syl, phrase_end)], harmony [(beat, bass, chord)], total beats."""
    notes, harm, b0 = [], [], 0.0
    for p in _split(phrases):
        ns = PHRASES[p]
        for k, (b, d, m, s) in enumerate(ns):
            notes.append((b0 + b, d, m, s, k == len(ns) - 1))
        harm += [(b0 + b, bs, ch) for b, bs, ch in HARM[p]]
        b0 += PLEN[p]
    return notes, harm, b0


class TimeMap:
    """beat -> seconds: a BeatMap through anchors, else a tempo with rubato: sag (the tempo falls by sag over the
    phrase run), fermata (each phrase's last note held 1 + fermata), wander (smooth random +-wander per beat)."""

    def __init__(self, tempo, total, notes, anchors=None, sag=0.0, fermata=0.0, wander=0.0, seed=0):
        self.bm = J.BeatMap(tempo, anchors, 0.5) if anchors else None
        g = np.arange(0.0, total + 8.0, 1 / 48.0)
        spb = np.full(len(g), 60.0 / tempo) * (1 + sag * np.clip(g / max(total, 1), 0, 1))
        for b, d, m, s, last in notes:
            if last and fermata:
                spb[(g >= b) & (g < b + d)] *= 1 + fermata
        if wander:
            r = np.random.default_rng(seed + 77).standard_normal(int(total + 10))
            spb *= 1 + wander * np.interp(g, np.arange(len(r)), np.convolve(r, np.ones(3) / 3, 'same'))
        self.g = g; self.t = np.concatenate([[0.0], np.cumsum(spb[:-1] / 48.0)])

    def __call__(self, b):
        if self.bm is not None:
            return float(self.bm(b))
        return float(np.interp(b, self.g, self.t))


# ================================================================================================== instruments
def hum(notes, rng, vel=0.8, vib_c=22.0, vib_hz=5.0, scoop=45.0, wobble=0.0, breath=0.05, formants='mm'):
    """A man humming with his mouth closed: notes [(t0, t1, midi_float)] -> mono. Additive voice (harmonics shaped
    by a closed-mouth 'mm/oo' formant envelope), portamento between legato notes, a scoop up into each note after a
    rest, delayed vibrato, slow pitch wobble (cents), shimmer and a little breath at the phrase starts."""
    T = max(t1 for _, t1, _ in notes) + 0.5
    cr = 1000; nc = int(T * cr) + 2; tc = np.arange(nc) / cr
    mid = np.full(nc, float(notes[0][2])); amp = np.zeros(nc); vibd = np.zeros(nc); sc = np.zeros(nc)
    for k, (t0, t1, m) in enumerate(notes):
        nxt = notes[k + 1][0] if k + 1 < len(notes) else t1 + 0.4
        legato = nxt - t1 < 0.12
        i0, i1 = int(t0 * cr), int(min(nc, (nxt if legato else t1 + 0.4) * cr))
        mid[i0:] = m
        a1 = int(t1 * cr); att = int(0.07 * cr); rel = int(0.11 * cr)
        e = np.ones(max(1, a1 - i0))
        if len(e) > cr:                                                        # a long held note sinks
            e *= np.linspace(1.0, 0.6, len(e))
        e[:att] = np.sin(np.linspace(0, np.pi / 2, min(att, len(e)))) ** 2 if att <= len(e) else e[:att]
        if legato:
            e[-rel:] *= np.linspace(1, 0.55, min(rel, len(e)))                  # the 'm' between syllables
        else:
            e[-rel:] *= np.cos(np.linspace(0, np.pi / 2, min(rel, len(e)))) ** 2
        amp[i0:i0 + len(e)] = np.maximum(amp[i0:i0 + len(e)], e[:max(0, min(len(e), nc - i0))])
        nv = np.clip((tc[i0:a1] - t0 - 0.3) / 0.4, 0, 1)
        vibd[i0:a1] = nv[:max(0, a1 - i0)]
        prev_end = notes[k - 1][1] if k else -1
        if t0 - prev_end > 0.12:                                               # a scoop up into it after a rest
            n_s = int(0.14 * cr)
            sc[i0:i0 + n_s] = -scoop / 100.0 * np.linspace(1, 0, min(n_s, nc - i0)) ** 2
    mid = np.convolve(mid, np.ones(55) / 55, 'same')                           # portamento (55 ms)
    w = np.convolve(rng.standard_normal(nc + 1200), np.hanning(900) / 450, 'same')[600:600 + nc]
    cents = vibd * vib_c * np.sin(2 * np.pi * vib_hz * tc + rng.uniform(0, 6)) + wobble * w / (np.abs(w).max() + 1e-9)
    mid = mid + sc + cents / 100.0
    n = int(T * SR); ts = np.arange(n) / SR
    f0 = 440.0 * 2 ** ((np.interp(ts, tc, mid) - 69) / 12)
    A = np.interp(ts, tc, amp) * (1 + 0.03 * np.interp(ts, tc, np.convolve(rng.standard_normal(nc), np.ones(30) / 30, 'same')))
    ph = 2 * np.pi * np.cumsum(f0) / SR
    F = {'mm': ((260, 90, 1.0), (750, 170, 0.55), (2300, 300, 0.08)),
         'oo': ((300, 100, 1.0), (870, 160, 0.45), (2240, 260, 0.10))}[formants]
    y = np.zeros(n)
    for k in range(1, 26):
        fk = k * f0
        if fk.min() > 4200:
            break
        env = 0.08 + sum(a * np.exp(-((fk - c) / bw) ** 2) for c, bw, a in F)
        y += env / k ** 0.55 * np.sin(k * ph + rng.uniform(0, 6.28)) * (fk < 4500)
    y *= A
    br = SX.mono(SX.bp(SX.noise(T, int(rng.integers(1 << 30))), 400, 2600, 2))[:n]
    y += breath * br * np.clip(np.gradient(A) * 400, 0, 1) * 6 + 0.25 * breath * br * A
    y = y / (np.abs(y).max() + 1e-9) * vel
    return y.astype(np.float32)


def in_wall(y, amount=0.7):
    """Inside the wall by the bed: through plaster and studs: low-passed hard, the stud cavity's boom, a tight
    box-like reflection, centred and close."""
    a = float(amount)
    x = SX.hp(SX.lp(SX.st(y), 1500 - 400 * a, 2), 110, 2)
    x = SX.eq(x, ('peak', 175, 2.5, 1.3), ('peak', 480, 3.0, 1.5), ('hs', 1100, -4.0, 0.7))
    x = SX.reverb(x, 'box', 0.30, 0.002)
    m = SX.mono(x); return SX.st(m)


def in_vent(y):
    """Through the floor vent's grille: a sheet-metal duct: band 250 Hz-3 kHz, a tin ring at 1.1 and 2.4 kHz, a short
    metallic flutter."""
    x = SX.bp(SX.st(y), 250, 3000, 2)
    x = SX.eq(x, ('peak', 1100, 6.0, 4.0), ('peak', 2400, 4.0, 5.0), ('peak', 520, 3.0, 2.0))
    d = SX.n_(0.0065); fl = np.zeros_like(x); fl[d:] = x[:-d] * 0.45; fl2 = np.zeros_like(x); fl2[2 * d:] = x[:-2 * d] * 0.25
    return SX.reverb(x + fl + fl2, 'box', 0.25, 0.001)


def _buf(sec):
    return np.zeros((int(sec * SR) + 2 * SR, 2), np.float32)


def _cents(m, rng, amount):
    return TUNING.get(int(m), 8.0) * (1 + 2.5 * amount) + rng.uniform(-30, 30) * amount


# ================================================================================================== versions
def render(version, anchors=None, tempo=None, seed=0, loops=None, amount=None, phrases=None, hush=False, inst='box',
           short=False, **_):
    v = str(version)
    if v not in VERSIONS:
        raise KeyError(f'unknown motif version {version!r}')
    rng = np.random.default_rng(2000 + int(seed))
    a = float(amount if amount is not None else (0.7 if v in ('wall', 'vent') else 0.0))
    ph = phrases or DEFAULT_PHRASES[v]
    if v == 'warm' and short:
        ph = 'CDH3'
    if hush and 'H' not in ph:
        ph += 'H1H2H3'
    n_loops = int(loops or 1)
    notes, harm, total = score(ph)
    if n_loops > 1:
        notes = [(b + k * total, d, m, s, l) for k in range(n_loops) for b, d, m, s, l in notes]
        harm = [(b + k * total, bs, ch) for k in range(n_loops) for b, bs, ch in harm]
        total *= n_loops
    tp = float(tempo or BASE_TEMPO[v])
    rub = {'wall': (0.28 * a, 0.45 * a + 0.15, 0.06 * a), 'vent': (0.2 * a, 0.4 * a + 0.15, 0.05 * a),
           'hush': (0.12, 0.3, 0.02), 'warm': (0.06, 0.25, 0.0), 'first': (0.2 * a, 0.3 * a, 0.03 * a)}.get(v, (0, 0.1, 0))
    tm = TimeMap(tp, total, notes, anchors, *rub, seed=seed)
    T = tm(total) + 4.0
    buf = _buf(T)
    out_notes = []
    hummed = v in ('wall', 'vent') or (v == 'hush' and inst in ('hum', 'hum_room'))
    flat3 = a >= 0.5                                         # the third sinks: F# -> F in the second half
    if hummed:
        hn = []
        for b, d, m, s, last in notes:
            mm = m - 12 - (1 if (flat3 and m % 12 == 6 and b >= total / 2) else 0)
            t0 = max(0.0, tm(b) + rng.uniform(-0.03, 0.06) * a); t1 = tm(b + d) - (0.34 if last else 0.02)   # a breath
            hn.append((t0, t1, mm + _cents(m, rng, a) / 100.0)); out_notes.append((t0, m, s))
        y = hum(hn, rng, 0.8, vib_c=22 + 25 * a, vib_hz=5.0 - 0.8 * a, scoop=40 + 60 * a, wobble=25 * a,
                breath=0.04 + 0.04 * a)
        J._put(buf, 0.0, y, 1.0, 0.0)
        for (b, d, m, s, last), (t0, _, _) in zip(notes, hn):          # a faint music box, detuned, under the hum
            J._put(buf, t0 + 0.04, J.music_box(m, 0.10 + 0.05 * (1 - a), rng, _cents(m, rng, a), 1.3), 1.0, 0.0)
        y = J._wow(buf, depth=0.002 + 0.006 * a, hz_=0.21, fl=0.0006, fl_hz=4.5, seed=seed)
        y = (in_vent(y) if v == 'vent' else SX.reverb(y, 'living', 0.14, 0.003) if inst == 'hum_room' and v == 'hush'
             else in_wall(y, a))
    else:
        for b, d, m, s, last in notes:
            t = tm(b) + rng.uniform(-0.012, 0.02) * (1 + 3 * a)
            det = _cents(m, rng, a) * (0.25 if v == 'warm' else 1.0)
            vv = rng.uniform(0.85, 1.0)
            if v == 'toy':
                J._put(buf, t, J.toy_piano(m + 12, 0.85 * vv, rng, det), 1.0, rng.uniform(-0.1, 0.1))
                J._put(buf, t + 0.004, J.music_box(m + 24, 0.18 * vv, rng, det, 0.8), 1.0, 0.2)
            elif v == 'warm':
                J._put(buf, t, J.toy_piano(m + 12, 0.55 * vv, rng, det), 1.0, -0.15)
                try:
                    J._put(buf, t + 0.003, J.celesta(m + 12, 0.5 * vv), 1.0, 0.15)
                except Exception:
                    J._put(buf, t + 0.003, J.music_box(m + 12, 0.4 * vv, rng, det, 1.4), 1.0, 0.15)
            else:                                                       # box, first, hush (box)
                J._put(buf, t, J.music_box(m + 12, 0.8 * vv, rng, det, 1.25 if v == 'hush' else 1.0), 1.0,
                       rng.uniform(-0.15, 0.15))
            out_notes.append((t, m, s))
        for b, bs, ch in harm:
            t = tm(b) + rng.uniform(0, 0.02)
            if v == 'toy':
                J._put(buf, t, J.toy_piano(bs + 12, 0.32, rng, TUNING.get(bs, 0)), 1.0, 0.0)
            elif v == 'warm':
                J._put(buf, t, J._sample('score/piano/grand_salamander', bs) * 0.30, 1.0, 0.0)
                for c in ch:
                    J._put(buf, t + rng.uniform(0.01, 0.05), J._sample('score/piano/grand_salamander', c) * 0.13, 1.0,
                           rng.uniform(-0.3, 0.3))
            else:
                J._put(buf, t, J.music_box(bs + 24, 0.28, rng, _cents(bs, rng, a), 1.4), 1.0, 0.0)
        y = buf
        if a > 0:
            y = J._wow(y, depth=0.002 + 0.008 * a, hz_=0.3, fl=0.0008, fl_hz=5.0, seed=seed)
        if v == 'hush':
            sway = 1 + 0.10 * np.sin(2 * np.pi * np.arange(len(y)) / SR / (3 * 60 / tp))
            y = SX.reverb(SX.lp(y * sway[:, None].astype(np.float32), 3600, 2), 'living', 0.3, 0.01)
        elif v == 'warm':
            y = SX.reverb(y, 'living', 0.22, 0.01)
        elif v in ('box', 'first'):
            y = SX.reverb(y, 'living', 0.18, 0.005)
        else:
            y = SX.reverb(y, 'living', 0.12, 0.004)
    y = SX.st(np.asarray(y, np.float32))
    end = max(t for t, _, _ in out_notes)
    y = y[:int((end + (6.0 if hummed else 4.5)) * SR)]
    y = SX.fade(y, 0.003, 1.2)                                 # every version rings out: never a dead stop
    pk = SX.peak(y)
    if pk > 0.89:
        y = y * (0.89 / pk)
    info = {'version': v, 'phrases': ph, 'loops': n_loops, 'total_beats': total, 'tempo': tp, 'amount': a,
            'notes': [(round(t, 3), int(m), s) for t, m, s in out_notes],
            'transpose': -12 if hummed else (12 if v in ('toy', 'box', 'first', 'hush', 'warm') else 0),
            'beats': [round(tm(b), 3) for b in np.arange(0, total + 0.5)], 'gap': (round(end, 3), round(len(y) / SR, 3))}
    return y, info


def gap_time(version, loops=1, short=False, tempo=None, **kw):
    """Seconds from a render's start to its LAST note (the home D, or 'house' where Pell stops): music_plan's
    'gap_at' starts the event so this note lands on an anchor."""
    _, info = render(version, tempo=tempo, loops=loops, short=short, **kw)
    return info['gap'][0]


# ================================================================================================== checks
def _rms_db(x):
    return float(20 * np.log10(np.sqrt(np.mean(np.square(x))) + 1e-12))


def melody_check(y, info):
    """Is the tune there and recognisable? For each note: the CQT energy that is NEW in its first 140 ms (against the
    80 ms before) folded to pitch classes; rank of the note's pitch class (1 = the strongest new class). Then the
    pitch heard at each note (strongest new CQT bin within +-2 semitones of the written pitch, any octave of the
    version's register) and the interval contour against the score: the share of intervals within 1 semitone."""
    import librosa
    m = SX.mono(SX.st(y))
    x = librosa.resample(m, orig_sr=SR, target_sr=22050)
    lo = 'C2' if info['transpose'] < 0 else 'C3'
    C = np.abs(librosa.cqt(x, sr=22050, hop_length=256, fmin=librosa.note_to_hz(lo), n_bins=72, bins_per_octave=12))
    m0 = int(librosa.note_to_midi(lo))
    tt = librosa.times_like(C, sr=22050, hop_length=256)
    ranks, heard, want = [], [], []
    for t0, mm, s in info['notes']:
        now = C[:, (tt >= t0 + 0.02) & (tt <= t0 + 0.16)].mean(1)
        bef = C[:, (tt >= t0 - 0.09) & (tt <= t0 - 0.01)].mean(1) if t0 > 0.1 else np.zeros(72)
        new = np.maximum(now - 0.6 * bef, 0)
        ch = new.reshape(6, 12).sum(0); pc = (int(mm) - m0) % 12
        ranks.append(list(np.argsort(ch)[::-1]).index(pc) + 1)
        mt = int(mm) + info['transpose']                           # the register it sounds in
        cand = [(new[i] if 0 <= i < 72 else 0, i) for d in range(-2, 3) for o in (-12, 0, 12) for i in [mt + d + o - m0]]
        best = max(cand)[1]
        heard.append(best + m0 - (round((best + m0 - mt) / 12) * 12)); want.append(mt)
    r = np.array(ranks)
    di = np.diff(heard); dw = np.diff(want)
    ok_int = float(np.mean(np.abs(di - dw) <= 1)) if len(dw) else 0.0
    return {'notes': len(r), 'rank1': int((r == 1).sum()), 'rank_le2': int((r <= 2).sum()),
            'intervals_ok_pct': round(100 * ok_int, 0), 'contour_ok_pct': round(100 * float(np.mean(np.sign(di) == np.sign(dw))), 0)
            if len(dw) else 0.0}


def check(v, y, info):
    m = SX.mono(y)
    r = {'dur': round(len(y) / SR, 2), 'lufs': round(float(SX.lufs_int(y)), 1), 'peak_db': round(float(SX.db(SX.peak(y))), 1)}
    nn = min(len(m), SR * 60)
    P = np.abs(np.fft.rfft(m[:nn] * np.hanning(nn))) ** 2; f = np.fft.rfftfreq(nn, 1 / SR); tot = P.sum() + 1e-12
    r['low_mid_high_pct'] = [round(float(100 * P[f < 250].sum() / tot), 1), round(float(100 * P[(f >= 250) & (f < 4000)].sum() / tot), 1),
                             round(float(100 * P[f >= 4000].sum() / tot), 1)]
    r['centroid_hz'] = int((f * P).sum() / tot)
    r['phone_db'] = round(SX.mom_max(SX.hp(SX.hp(y, 300, 2), 300, 2)) - SX.mom_max(y), 1)   # > -15: a phone plays it
    k = SR // 100
    pkv = float(np.abs(m).max()) + 1e-12
    r['edge_db'] = [round(float(20 * np.log10(np.sqrt(np.mean(m[:k] ** 2)) / pkv + 1e-12)), 1),
                    round(float(20 * np.log10(np.sqrt(np.mean(m[-k:] ** 2)) / pkv + 1e-12)), 1)]
    r['melody'] = melody_check(y, info)
    r['phrases'] = info['phrases']; r['tempo'] = info['tempo']; r['amount'] = info['amount']
    return r


def sheet(names, out=OUT):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(len(names), 1, figsize=(12, 1.45 * len(names)), dpi=80)
    for ax, nm in zip(np.atleast_1d(axs), names):
        y, _ = sf.read(os.path.join(out, nm + '.wav'), dtype='float32', always_2d=True)
        ax.specgram(y.mean(1), NFFT=4096, Fs=SR, noverlap=3072, cmap='magma', vmin=-120)
        ax.set_ylim(80, 4000); ax.set_yscale('log'); ax.set_title(nm, fontsize=8, loc='left'); ax.tick_params(labelsize=6)
    fig.tight_layout(); fig.savefig(os.path.join(out, 'motif_sheet.png')); plt.close(fig)


KW = {'toy': {}, 'box': {}, 'first': {'amount': 0.4}, 'wall': {'amount': 0.7}, 'vent': {'amount': 0.8},
      'hush': {'inst': 'box'}, 'warm': {}}


def main():
    names = [a for a in sys.argv[1:] if not a.startswith('-')] or list(VERSIONS)
    os.makedirs(OUT, exist_ok=True)
    pj = os.path.join(OUT, 'motif_check.json')
    res = json.load(open(pj)) if os.path.exists(pj) else {}
    for nm in names:
        v, extra = (nm.split(':', 1) + [''])[:2]
        kw = dict(KW.get(v, {}))
        if extra:                                              # 'wall:ABCD' -> phrases, 'hush:hum' -> inst
            kw['inst' if v == 'hush' else 'phrases'] = extra
        y, info = render(v, seed=3, **kw)
        tag = nm.replace(':', '_')
        sf.write(os.path.join(OUT, tag + '.wav'), y, SR, subtype='PCM_16')
        res[tag] = check(v, y, info)
        print(tag, json.dumps(res[tag]), flush=True)
    json.dump(res, open(pj, 'w'), indent=1)
    sheet([t for t in res if os.path.exists(os.path.join(OUT, t + '.wav'))])
    print('wrote', OUT)


if __name__ == '__main__':
    main()
