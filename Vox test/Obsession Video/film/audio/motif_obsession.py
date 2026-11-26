"""motif_obsession.py: "STICK LIKE GLUE", the returning motif of "If a Girl Is OBSESSED With Being Your Only
Friend... DON'T WRITE YOUR NAME" (Night Policy). Little Adam's own playground chant, made up at seven for Danny: our
original FOUR-NOTE chant (C, Eb, F, Ab = mi, sol, la, do' of A-flat major) with one soft chalk tap on every beat,
written FROM little Adam's sung take so the motif and the voices agree. No sung words here: the voice track carries
every sung line (little Adam's 'adam7_me_and_you' on the tape, Evie's 'Only me. I'm here, I'm he-', Lina's
'lina_me_and_you', all baked); this module only plays the tune.

How it was derived (`python3 audio/motif_obsession.py measure` redoes it and writes W/mix/motif/sung_notes.json):
pyin f0 of timeline line 'adam7_me_and_you' (narration_en.wav 57.64-66.41 s), per-word medians, then a brute-force fit
of every key, four-note set and tuning offset: best = A-flat major {mi, sol, la, do'} at +40 cents (mean error 0.59
semitones: the sung take wobbles; a few words read an octave low and fold back). Tempo: the four lyric lines start
1.92 / 2.36 / 2.08 s apart = one 4/4 bar each at about 112 bpm. Quantised per word to the four notes, then tidied:
    1  Me and you, and you and me,        F F Eb Eb C F | Eb          (la la sol sol mi la sol)
    2  stick like glue, and you will see.  Ab Ab Ab | C Eb F Ab       (the four notes climbing to "see")
    3  Everywhere you go, I'm near.        F F F Ab Ab F | F (held)    (left hanging on la)
    4  Only me. I'm here, I'm here.        F F Ab | Eb Ab | F Ab       (home on do')
Lina's healed line ('lina_me_and_you') fits D-flat major at +45 cents: the same tune a fourth up, the same tuning, so
'healed' is transposed +5 (D-flat) with the film's +40 cents. The tape song (score.VINTAGE, At the Ballet) is
varispeeded onto A-flat +40 cents too, and every dark track of score.TRACKS carries the same +0.4 semitone.

Versions: render(version, anchors=None, tempo=None, seed=0, loops=None, n=None, first=0, stop_at=None,
phrases=None, taps=None, accel=0.0, **_) -> (stereo float32 48 kHz, info)
    ping       ONE message ping = ONE note of the song (first = which note, 0-based, wraps): beats.json pings call it
               with first = 0, 1, 2 ... so each ping is the next note
    pings      the looped run "Every ping, one note of my song.": pings in the song's rhythm, loops (default 2),
               accel (0..1: the tempo climbs to +60 % as the counter runs 12, 30, 47)
    swings     Evie's perfect bright version on the swings: toy glockenspiel + music box two octaves up, dead in time,
               a soft chalk tap on every beat (we have no sung take of her)
    letterbox  hummed slow (70 bpm) and a SEMITONE FLAT through the letterbox: closed-mouth hum, muffled by the slot,
               a chalk scrape on every beat
    block      the pings again, slower (64 bpm) and an octave lower, under Mom saving the messages; stop_at = seconds
               into the render where Block is tapped: a CLEAN dead stop (the ringing ping is cut by a 60 ms
               raised-cosine and only a short natural room tail remains; never a click)
    healed     the healed major version under Lina's sung line: warm piano chords and a soft celesta arpeggio in her
               key (D-flat, +40 cents), never doubling her voice; anchors (beat, s) put the bars on her words
    taps       four soft chalk taps (the film opens on them), at the chant's tempo
phrases = bars ('1234', '34' ...); n = notes played; anchors [(beat, s)] bend the tune onto words (score.py passes
them relative to the event). Every version eases its own edges (fade in 3 ms, the last note rings out).

CLI: python3 audio/motif_obsession.py [measure] [version ...]   -> W/mix/motif/<version>.wav + motif_check.json
"""
import json, os, sys
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sfx as SX                                        # noqa: E402
import jingle as J                                      # noqa: E402  (the instruments)
import motif_walls as MW                                # noqa: E402  (hum, TimeMap, check)

SR = 48000
W = SX.W
OUT = os.path.join(W, 'mix', 'motif')
TUNE_CENTS = 40.0                    # little Adam's sung tuning (the fit above); Lina's +45 rounds to the same
HOME = 68                            # A-flat 4: do' of the chant
TEMPO = 112.0                        # the take: one bar per lyric line
NOTES4 = (60, 63, 65, 68)            # C4 Eb4 F4 Ab4: the four notes
# bar -> [(beat, beats, midi, syllable)]
TUNE = {
    '1': [(0.0, .5, 65, 'Me'), (.5, .5, 65, 'and'), (1.0, .5, 63, 'you'), (1.5, .5, 63, 'and'), (2.0, .5, 60, 'you'),
          (2.5, .5, 65, 'and'), (3.0, 1.0, 63, 'me')],
    '2': [(0.0, .5, 68, 'Stick'), (.5, .5, 68, 'like'), (1.0, 1.0, 68, 'glue'), (2.0, .5, 60, 'and'),
          (2.5, .5, 63, 'you'), (3.0, .5, 65, 'will'), (3.5, .5, 68, 'see')],
    '3': [(0.0, .25, 65, 'Ev'), (.25, .25, 65, 'ery'), (.5, .5, 65, 'where'), (1.0, .5, 68, 'you'), (1.5, .5, 68, 'go'),
          (2.0, .5, 65, "I'm"), (2.5, 1.5, 65, 'near')],
    '4': [(0.0, .25, 65, 'On'), (.25, .25, 65, 'ly'), (.5, 1.0, 68, 'me'), (1.5, .5, 63, "I'm"), (2.0, 1.0, 68, 'here'),
          (3.0, .5, 65, "I'm"), (3.5, .5, 68, 'here')],
}
# bar -> [(beat, bass, chord)] in A-flat: I(add6) | IV I | vi IV | IV V I
HARM = {'1': [(0, 44, (56, 60, 63)), (2, 44, (56, 60, 65))], '2': [(0, 49, (56, 61, 65)), (2, 44, (56, 60, 63))],
        '3': [(0, 41, (56, 60, 65)), (2, 49, (56, 61, 65))],
        '4': [(0, 49, (56, 61, 65)), (1, 51, (55, 58, 63)), (2, 44, (56, 60, 63))]}
VERSIONS = ('ping', 'pings', 'swings', 'letterbox', 'block', 'healed', 'taps')
BASE_TEMPO = {'ping': TEMPO, 'pings': TEMPO, 'swings': TEMPO, 'letterbox': 70.0, 'block': 64.0, 'healed': 100.0,
              'taps': TEMPO}
TRANSPOSE = {'ping': 24, 'pings': 24, 'swings': 24, 'letterbox': -1, 'block': 12, 'healed': 5, 'taps': 0}
MEASURED = {'adam7': {'key': 'Ab major', 'cents': 40, 'err': 0.59}, 'lina': {'key': 'Db major', 'cents': 45, 'err': 0.51}}


def score(bars):
    """Notes [(beat, beats, midi, syl, last_of_bar)], harmony [(beat, bass, chord)], total beats."""
    notes, harm, b0 = [], [], 0.0
    for b in bars:
        for k, (o, d, m, s) in enumerate(TUNE[b]):
            notes.append((b0 + o, d, m, s, k == len(TUNE[b]) - 1))
        harm += [(b0 + o, bs, ch) for o, bs, ch in HARM[b]]
        b0 += 4.0
    return notes, harm, b0


def all_notes():
    return score('1234')[0]


# ---------------------------------------------------------------------------------------------------- instruments
def ping_note(m, cents=TUNE_CENTS, vel=1.0, dec=0.32, dark=False, seed=0):
    """One message ping on one note: a soft sine with a short FM bell attack, a tiny pitch blip into it, odd
    harmonics through a little tube (the phone's hollow speaker). dark: the R7 pings (longer, low-passed)."""
    rng = np.random.default_rng(seed)
    f = J.hz(m) * 2 ** (cents / 1200.0)
    n = int((dec * 3.2 + 0.05) * SR)
    t = np.arange(n) / SR
    fr = f * 2 ** ((-0.5 * np.exp(-t / 0.008)) / 12)
    ph = 2 * np.pi * np.cumsum(fr) / SR
    mod = 1.1 * np.exp(-t / 0.03) * np.sin(3.0 * ph)
    y = (np.sin(ph + mod) + 0.16 * np.sin(3 * ph) + 0.04 * np.sin(5 * ph)) * np.exp(-t / dec) * (1 - np.exp(-t / 0.0018))
    d = int(0.0011 * SR); h = y.copy()
    for k in range(1, 4):
        h[k * d:] += y[:-k * d] * (0.36 ** k)
    h = h * J._tail_fade(len(h), 0.3) * vel * rng.uniform(0.92, 1.0)
    x = SX.hp(SX.lp(SX.st(h.astype(np.float32)), 2600 if dark else 8000, 2), 250 if dark else 320, 2)
    return SX.eq(x, ('peak', 600 if dark else 1150, 3.0, 1.4))


def chalk(kind, rng, dur=None):
    """A chalk tap / scrape from sfx.py (audio/sfx_obsession.py recipes), at a fixed level for the music."""
    try:
        p = {'kind': kind}
        if dur:
            p['dur'] = dur
        y = SX.render('chalk_scrape' if kind in ('write', 'creep') else 'chalk_tap', int(rng.integers(1 << 20)),
                      'close', **p)
        return SX.st(y) * np.float32(0.5)
    except Exception as ex:                                   # the tune must never fail on a foley layer
        print(f'[motif] chalk {kind} skipped ({repr(ex)[:80]})', flush=True)
        return np.zeros((SR // 10, 2), np.float32)


def _box(m, vel, rng, cents):
    return J.music_box(m, vel, rng, cents, 1.0)


# ---------------------------------------------------------------------------------------------------- render
def render(version, anchors=None, tempo=None, seed=0, loops=None, n=None, first=0, stop_at=None, phrases=None,
           taps=None, accel=0.0, **_):
    v = str(version)
    if v not in VERSIONS:
        raise KeyError(f'unknown motif version {version!r}')
    rng = np.random.default_rng(4000 + int(seed))
    tp = float(tempo or BASE_TEMPO[v])
    tr = TRANSPOSE[v]
    cents = TUNE_CENTS
    if v == 'ping':                                          # one note: the next one of the song
        allm = all_notes()
        k = int(first) % len(allm)
        m = allm[k][2]
        y = SX.reverb(ping_note(m + tr, cents, 1.0, seed=seed + k), 'living', 0.12, 0.003)
        y = SX.fade(y, 0.002, 0.25)
        y = y * np.float32(min(1.0, 0.89 / (SX.peak(y) + 1e-9)))
        return y, {'version': v, 'n': 1, 'notes': [(0.0, m, allm[k][3])], 'first': k, 'tempo': tp, 'phrases': '-',
                   'loops': 1, 'amount': 0.0, 'total_beats': 1.0, 'transpose': tr, 'beats': [0.0]}
    bars = str(phrases or '1234')
    notes, harm, total = score(bars)
    lp_ = int(loops or (2 if v == 'pings' else 1))
    if v == 'pings' and lp_ > 1:                             # the run loops the song
        notes = [(b + k * total, d, m, s, last) for k in range(lp_) for b, d, m, s, last in notes]
        harm = [(b + k * total, bs, ch) for k in range(lp_) for b, bs, ch in harm]
        total *= lp_
    if v == 'taps':
        notes = [(float(b), 1.0, HOME, 'tap', b == 3) for b in range(4)]
        harm, total = [], 4.0
    if first:
        f0 = int(first) % max(1, len(notes))
        notes = notes[f0:] + []
    nn = int(n if n is not None else len(notes))
    notes = notes[:nn]
    if accel and not anchors:                                # the counter racing: the tempo climbs to (1 + 0.6 accel)
        g = np.arange(0.0, total + 8.0, 1 / 48.0)
        spb = 60.0 / (tp * (1 + 0.6 * float(accel) * np.clip(g / max(total, 1), 0, 1) ** 1.3))
        tt = np.concatenate([[0.0], np.cumsum(spb[:-1] / 48.0)])
        tm = lambda b: float(np.interp(b, g, tt))
    else:
        rub = {'letterbox': (0.12, 0.35, 0.04), 'block': (0.18, 0.2, 0.0), 'healed': (0.0, 0.15, 0.0)}.get(v, (0, 0, 0))
        tm = MW.TimeMap(tp, total, notes, anchors, *rub, seed=seed)
    last_b = notes[-1][0] if notes else 0.0
    T = tm(total) + 5.0
    buf = np.zeros((int(T * SR) + 2 * SR, 2), np.float32)
    fx = np.zeros_like(buf)                                  # chalk layer (not reverberated with the tune)
    out = []
    use_taps = (v in ('swings', 'taps')) if taps is None else bool(taps)
    if v == 'letterbox':                                     # the hum, a semitone flat, through the slot
        hn = []
        for b, d, m, s, last in notes:
            t0 = max(0.0, tm(b) + rng.uniform(-0.02, 0.05)); t1 = tm(b + d) - (0.25 if last else 0.04)
            hn.append((t0, t1, m + tr + cents / 100.0)); out.append((t0, m + tr, s))
        y = MW.hum(hn, rng, 0.8, vib_c=6.0, vib_hz=4.6, scoop=18.0, wobble=10.0, breath=0.0, formants='mm')
        J._put(buf, 0.0, y, 1.0, 0.0)
        for b in np.arange(0.0, last_b + 1.0, 1.0):          # a chalk scrape on every beat
            J._put(fx, tm(b) + 0.02, chalk('write', rng, 0.32), 0.55, rng.uniform(-0.2, 0.2))
    else:
        for k, (b, d, m, s, last) in enumerate(notes):
            t = tm(b)
            vv = rng.uniform(0.88, 1.0)
            if v in ('pings', 'block'):
                J._put(buf, t, ping_note(m + tr, cents, 0.9 * vv, 0.55 if v == 'block' else 0.3, v == 'block',
                                         seed + k), 1.0, rng.uniform(-0.1, 0.1))
            elif v == 'swings':                              # glockenspiel + music box, dead in time, bright
                J._put(buf, t, J.glock(m + tr, 0.75 * vv), 1.0, -0.12)
                J._put(buf, t, _box(m + tr, 0.55 * vv, rng, cents), 1.0, 0.15)
            elif v == 'taps':
                J._put(fx, t, chalk('tap', rng), 1.0, 0.0)
            out.append((t, m + tr, s))
        if v == 'healed':                                    # warm piano chords + celesta arpeggio, her key
            out = []
            for k, (b, bs, ch) in enumerate(harm):
                if b > last_b + 0.01:
                    continue
                t = tm(b)
                J._put(buf, t, J.low_piano(bs + tr - 12, 0.42, k), 1.0, -0.1)
                for c_ in ch:
                    J._put(buf, t + rng.uniform(0.0, 0.02), J.low_piano(c_ + tr - 12, 0.22, k), 1.0,
                           rng.uniform(-0.25, 0.25))
                for j, c_ in enumerate(ch + (ch[0] + 12,)):  # the celesta rocks gently through the chord
                    J._put(buf, tm(b + 0.5 * j), J.celesta(c_ + tr + 12, 0.16), 1.0, 0.2 * (-1) ** j)
                out.append((t, bs + tr, 'chord'))
    if use_taps and v != 'taps':                             # one soft chalk tap on every beat
        for b in np.arange(0.0, last_b + 1.0, 1.0):
            J._put(fx, tm(b), chalk('tap', rng), 0.45, 0.0)
    y = buf
    if v == 'letterbox':                                     # muffled by the slot and the hall
        y = SX.eq(SX.hp(SX.lp(y, 1500, 2), 160, 2), ('peak', 850, 4.0, 2.0), ('peak', 300, 2.0, 1.0))
        y = SX.reverb(y, 'hallway', 0.25, 0.004)
        y = J._wow(y, depth=0.002, hz_=0.25, fl=0.0, seed=seed)
    elif v == 'block':
        y = SX.reverb(y, 'living', 0.2, 0.004)
    elif v == 'healed':
        y = SX.reverb(y, 'living', 0.22, 0.005)
    elif v in ('pings', 'swings'):
        y = SX.reverb(y, 'living', 0.12 if v == 'pings' else 0.16, 0.003)
    if v != 'taps':
        y = SX.st(y)[:len(buf)] + 0.0
    y = y[:len(buf)] + fx[:len(y)] * (np.float32(1.0) if v in ('taps', 'letterbox') else np.float32(1.0))
    end = max([t for t, _, _ in out] + [0.0])
    ring = {'letterbox': 2.0, 'block': 1.6, 'healed': 3.0, 'taps': 0.6}.get(v, 1.8)
    y = y[:int((end + ring) * SR)]
    if v == 'block' and stop_at is not None:                 # Block: a clean dead stop, a short natural tail
        i = int(float(stop_at) * SR)
        if i < len(y):
            k = int(0.06 * SR)
            g = np.ones(len(y), np.float32)
            g[i:i + k] = np.cos(np.linspace(0, np.pi / 2, k)) ** 2
            g[i + k:] = 0.0
            dry = y * g[:, None]
            tail = SX.reverb(dry[max(0, i - int(0.25 * SR)):i + k], 'living', 0.5, 0.0, dry=0.0)
            y = dry[:i + k + int(0.45 * SR)]
            j = len(y) - len(tail)
            tl = tail[:len(y) - max(0, i - int(0.25 * SR))]
            y[max(0, i - int(0.25 * SR)):max(0, i - int(0.25 * SR)) + len(tl)] += tl * np.float32(0.35)
            y = SX.fade(y, 0.002, 0.3)
            out = [o for o in out if o[0] < stop_at]
    y = SX.fade(SX.st(np.asarray(y, np.float32)), 0.003, min(1.0, 0.4 * ring))
    pk = SX.peak(y)
    if pk > 0.89:
        y = y * (0.89 / pk)
    info = {'version': v, 'phrases': bars, 'loops': lp_, 'total_beats': total, 'tempo': tp, 'amount': float(accel),
            'n': len(out), 'notes': [(round(t, 3), int(m), s) for t, m, s in out], 'transpose': tr,
            'beats': [round(tm(b), 3) for b in np.arange(0, total + 0.5)], 'gap': (round(end, 3), round(len(y) / SR, 3))}
    return y.astype(np.float32), info


# ---------------------------------------------------------------------------------------------------- checks
def measure():
    """Pitch-track the sung lines (pyin, per-word medians) and fit key + tuning to the four-note set."""
    import librosa
    T = json.load(open(os.path.join(W, 'align', 'timeline.json')))
    sr = sf.info(os.path.join(W, 'narration', 'narration_en.wav')).samplerate
    res = {}
    for tag in ('adam7_me_and_you', 'lina_me_and_you'):
        L = next(l for l in T['lines'] if l['tag'] == tag)
        y, _ = sf.read(os.path.join(W, 'narration', 'narration_en.wav'), start=int((L['t'] - 0.05) * sr),
                       stop=int((L['end'] + 0.1) * sr), dtype='float32')
        y = librosa.resample(y.mean(1) if y.ndim > 1 else y, orig_sr=sr, target_sr=16000)
        f0, vf, _ = librosa.pyin(y, fmin=150, fmax=1000, sr=16000, frame_length=1024, hop_length=160)
        tt = np.arange(len(f0)) * 0.01 + L['t'] - 0.05
        wl = []
        for k, (w, t0) in enumerate(L['words']):
            t1 = L['words'][k + 1][1] if k + 1 < len(L['words']) else L['end']
            msk = (tt >= t0) & (tt < t1) & vf
            wl.append((w, round(t0, 2), round(float(librosa.hz_to_midi(np.nanmedian(f0[msk]))), 2) if msk.sum() > 2 else None))
        p = np.array([x[2] for x in wl if x[2] is not None and x[2] > 52])
        best = (9, 0, 0)
        for key in range(12):
            pcs = [(key + d) % 12 for d in (0, 4, 7, 9)]
            for c in np.arange(-0.5, 0.5, 0.05):
                err = float(np.mean([min(abs(((x - c - pc + 6) % 12) - 6) for pc in pcs) for x in p]))
                if err < best[0]:
                    best = (round(err, 3), key, int(round(c * 100)))
        res[tag] = {'words': wl, 'key': J_PC[best[1]] + ' major', 'cents': best[2], 'err': best[0]}
        print(tag, res[tag]['key'], f"{best[2]:+d} cents", 'err', best[0], flush=True)
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, 'sung_notes.json'), 'w'), indent=1)


J_PC = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
KW = {'ping': {'first': 7}, 'pings': {'loops': 2, 'accel': 0.5}, 'swings': {}, 'letterbox': {'phrases': '34'},
      'block': {'phrases': '12', 'stop_at': 6.2}, 'healed': {}, 'taps': {}}


def main():
    if 'measure' in sys.argv[1:]:
        measure(); return
    names = [a for a in sys.argv[1:] if not a.startswith('-')] or list(VERSIONS)
    os.makedirs(OUT, exist_ok=True)
    pj = os.path.join(OUT, 'motif_check.json')
    res = json.load(open(pj)) if os.path.exists(pj) else {}
    for nm in names:
        y, info = render(nm, seed=3, **KW.get(nm, {}))
        sf.write(os.path.join(OUT, nm + '.wav'), y, SR, subtype='PCM_16')
        r = MW.check(nm, y, info) if nm not in ('taps',) else {}
        r.update(dur=round(len(y) / SR, 2), notes=len(info['notes']), tempo=info['tempo'])
        res[nm] = r
        print(nm, json.dumps({k: r[k] for k in r if k in ('dur', 'lufs', 'peak_db', 'edge_db', 'centroid_hz', 'notes')}),
              flush=True)
    json.dump(res, open(pj, 'w'), indent=1)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
