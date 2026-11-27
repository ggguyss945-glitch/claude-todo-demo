"""motif_buttons.py: THE BUTTON SONG, the returning motif of "If Your Mom's Eyes Turn Into Buttons... DON'T KEEP HER
SECRET" (Night Policy). Our own original four-bar 3/4 waltz, written FROM Mom's sung take so that the music box, the
hums and her singing agree: `python3 audio/motif_buttons.py measure` pitch-tracks her two sung lines in the voice track
(timeline lines 'mom_one_for_warm' and 'mom_mama_sees_you'; WORLD harvest f0, per-word medians) and checks the tune
below against them (W/mix/motif/mom_notes.json). No sung words here: the voice track carries every sung line (Mom's
and the Blank's, baked); this module only plays the tune.

The tune (A major, Mom's key; her tuning measured +8..+20 cents: TUNE_CENTS = 15; one bar per line, one note per syllable, the
same lilting cell every bar: beat 1 = eighth + two sixteenths, beat 2 = the same, beat 3 = the held word)
    1  One for warm and two for snug          F#3 B3 A3 | B3 C#4 C#4 | A3      (6 2 1 2 3 3 1)
    2  three for Mama's button hug            B3 C#4 G#3 | G#3 F#3 E3 | F#3    (2 3 7 7 6 5 6)
    3  Top one up and tucked in tight         B3 A3 A3 | E3 G#3 A3 | G#3       (2 1 1 5 7 1 7)
    4  Mama sees you. Say goodnight.          A3 G#3 B3 | G#3 A3 B3 | A3       (1 7 2 7 1 2 1: home)
    harmony (oom-pah-pah)  1: A | 2: E . D | 3: A . E | 4: A E A
Her register is A3; the music boxes play it two octaves up, the hums in her own register.

Versions: render(version, anchors=None, tempo=None, seed=0, loops=None, amount=None, phrases=None, n=None, short=False)
-> (stereo float32 48 kHz, info). phrases = the bars ('1234', '12' ...); n = notes played (the rest never sound);
anchors [(beat, s)] bend the tune onto words (score.py passes them relative to the event).
    box       clean music box, quiet, in tune (the chat: "Our song.")                                    72 bpm, 1234
    winddown  the stolen music box in the closet at 3 a.m.: too slow and winding down (58 -> ~20 bpm, the governor
              catching), the spring runs out on "three for Mama" (n=10); muffled by the closet door, a faint whirr
    hum       hummed, slowed, in Mom's voice register through the car window (closed-mouth 'mm', muffled, cabin)
    sill      the windowsill: sung-feel music box + a perfect 'oo' voice, no vibrato, like a recording: loops=3 copies
              that are sample-for-sample identical (again and again)
    detuned   the climax: the box detuned and sagging, bars 12, STOPS with one note left (n=13: no "hug"); give it
              anchors on the Blank's sung words so each button closes on her beat
    real      Mom's real music box (her birthday gift), warm and in tune: the aftermath; anchors put bar 4 on her
              "Mama sees you. Say goodnight."
    cardigan  four notes from the real box under the empty cardigan (bar 1, n=4), muffled by the cloth, the last
              turn of the spring
    chime     the son's tablet chime: the first four notes as a clean UI chime (tablet speaker band)

CLI: python3 audio/motif_buttons.py [versions...] | measure
     renders W/mix/motif/<v>.wav (16-bit), checks each (loudness, peak, edges, the melody found note by note, the key
     heard against A major, the tuning against Mom's) into motif_check.json and draws motif_sheet.png.
"""
import json, os, sys
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sfx as SX                                        # noqa: E402
import jingle as J                                      # noqa: E402  (the instruments)
import motif_walls as MW                                # noqa: E402  (hum, TimeMap, melody_check, check)

SR = 48000
W = SX.W
OUT = os.path.join(W, 'mix', 'motif')
TUNE_CENTS = 15.0                    # Mom's sung tuning: +8..+20 cents (WORLD f0 of both sung lines, pitch_tuning)
RHYTHM = [(0.0, 0.5), (0.5, 0.25), (0.75, 0.25), (1.0, 0.5), (1.5, 0.25), (1.75, 0.25), (2.0, 1.0)]
TUNE = {'1': ([54, 59, 57, 59, 61, 61, 57], ['One', 'for', 'warm', 'and', 'two', 'for', 'snug']),
        '2': ([59, 61, 56, 56, 54, 52, 54], ['three', 'for', 'Ma', "ma's", 'but', 'ton', 'hug']),
        '3': ([59, 57, 57, 52, 56, 57, 56], ['Top', 'one', 'up', 'and', 'tucked', 'in', 'tight']),
        '4': ([57, 56, 59, 56, 57, 59, 57], ['Ma', 'ma', 'sees', 'you', 'Say', 'good', 'night'])}
# (beat in bar, bass midi, chord): a harmony starting on a beat gives the bass there, other beats the chord ("pah")
HARM = {'1': [(0, 45, (57, 61, 64))], '2': [(0, 40, (56, 59, 64)), (2, 38, (54, 57, 62))],
        '3': [(0, 45, (57, 61, 64)), (2, 40, (56, 59, 62))],
        '4': [(0, 45, (57, 61, 64)), (1, 40, (56, 59, 62)), (2, 45, (57, 61, 64))]}
WORN = {38: -4, 40: 5, 45: -3, 52: 4, 54: -5, 56: 3, 57: -2, 59: 4, 61: -6, 62: 3, 64: -4}   # cents: the comb's own
VERSIONS = ('box', 'winddown', 'hum', 'sill', 'detuned', 'real', 'cardigan', 'chime')
BASE_TEMPO = {'box': 72.0, 'winddown': 58.0, 'hum': 50.0, 'sill': 66.0, 'detuned': 54.0, 'real': 76.0,
              'cardigan': 46.0, 'chime': 150.0}
DEFAULT_BARS = {'box': '1234', 'winddown': '123', 'hum': '12', 'sill': '1234', 'detuned': '12', 'real': '1234',
                'cardigan': '1', 'chime': '1'}
DEFAULT_N = {'winddown': 10, 'detuned': 13, 'cardigan': 4, 'chime': 4}
TRANSPOSE = {'hum': 0}                                  # every other version: the box register, +24


def score(bars):
    """Notes [(beat, beats, midi, syl, bar_end)], harmony [(beat, bass, chord, starts)], total beats."""
    notes, harm, b0 = [], [], 0.0
    for b in bars:
        ms, sy = TUNE[b]
        for k, ((o, d), m, s) in enumerate(zip(RHYTHM, ms, sy)):
            notes.append((b0 + o, d, m, s, k == 6))
        hs = HARM[b]
        for beat in range(3):
            cur = [h for h in hs if h[0] <= beat][-1]
            harm.append((b0 + beat, cur[1], cur[2], cur[0] == beat))
        b0 += 3.0
    return notes, harm, b0


def _wind_map(total, t0=58.0, t1=20.0, seed=0):
    """The spring running out: the tempo falls from t0 to t1 (faster at the end), the governor catching (small
    random hitches on a few beats)."""
    g = np.arange(0.0, total + 4.0, 1 / 48.0)
    x = np.clip(g / max(total, 1.0), 0, 1)
    bpm = t0 * (t1 / t0) ** (x ** 1.6)
    spb = 60.0 / bpm
    r = np.random.default_rng(seed + 31)
    for b in r.choice(int(total), size=max(1, int(total) // 3), replace=False):
        spb[(g >= b + 0.4) & (g < b + 0.6)] *= 1.0 + r.uniform(0.6, 1.4)          # a hitch
    t = np.concatenate([[0.0], np.cumsum(spb[:-1] / 48.0)])
    return lambda b: float(np.interp(b, g, t))


def _box(m, vel, rng, cents, decay=1.0, bright=1.0):
    y = J.music_box(m, vel, rng, cents, decay)
    return y if bright >= 1.0 else SX.mono(SX.lp(y, 2500 + 5000 * bright, 2))


def _chime_note(m, vel, dur, rng, cents):
    """A clean UI chime note: a sine with a soft FM bell attack and a touch of 2nd harmonic."""
    f = J.hz(m) * 2 ** (cents / 1200.0)
    t = np.arange(int(dur * SR)) / SR
    mod = 1.4 * np.exp(-t / 0.05) * np.sin(2 * np.pi * f * 3.0 * t)
    y = np.sin(2 * np.pi * f * t + mod) + 0.12 * np.sin(4 * np.pi * f * t) * np.exp(-t / 0.12)
    y *= np.exp(-t / (dur * 0.33)) * (1 - np.exp(-t / 0.0015)) * J._tail_fade(len(t), 0.25)
    return (y * vel).astype(np.float32)


def _loop_tile(y, loop_len, loops):
    """Exactly the same pass `loops` times (overlap-add of the rings): a recording, again and again."""
    L = int(round(loop_len * SR))
    out = np.zeros((L * (loops - 1) + len(y), 2), np.float32)
    for k in range(loops):
        out[k * L:k * L + len(y)] += y
    return out


def render(version, anchors=None, tempo=None, seed=0, loops=None, amount=None, phrases=None, n=None, short=False,
           follow=None, **_):
    """follow (detuned): one sung pitch per note (MIDI float, None = the written note), measured from the singer's
    take, so the box plays under her IN TUNE (her own notes and cents, two octaves up); only the tines' wear and the
    wow stay 'detuned' (no sag, no random tine errors)."""
    v = str(version)
    if v not in VERSIONS:
        raise KeyError(f'unknown motif version {version!r}')
    rng = np.random.default_rng(3000 + int(seed))
    a = float(amount if amount is not None else {'detuned': 1.0, 'winddown': 0.6}.get(v, 0.0))
    bars = str(phrases or ('34' if short and v == 'real' else DEFAULT_BARS[v]))
    notes, harm, total = score(bars)
    nn = int(n if n is not None else DEFAULT_N.get(v, len(notes)))
    notes = notes[:nn]
    last_b = notes[-1][0]
    harm = [h for h in harm if h[0] <= last_b + 0.01]
    tp = float(tempo or BASE_TEMPO[v])
    if v == 'winddown' and not anchors:
        tm = _wind_map(last_b + 1.0, tp, tp * (0.34 + 0.2 * (1 - a)), seed)   # the spring is out by the last note
    else:
        rub = {'hum': (0.06, 0.25, 0.03), 'real': (0.0, 0.15, 0.0), 'cardigan': (0.5, 0.6, 0.0),
               'detuned': (0.15 * a, 0.2, 0.02 * a)}.get(v, (0.0, 0.0, 0.0))
        tm = MW.TimeMap(tp, total, notes, anchors, *rub, seed=seed)
    tr = TRANSPOSE.get(v, 24)
    T = tm(total) + 5.0
    buf = np.zeros((int(T * SR) + 2 * SR, 2), np.float32)
    out_notes = []
    fol = [None if f is None else float(f) for f in (follow or [])]
    if fol and v == 'detuned':                              # her notes replace the written ones (same rhythm)
        notes = [(b, d, (int(round(fol[k])) if k < len(fol) and fol[k] is not None else m), s, last)
                 for k, (b, d, m, s, last) in enumerate(notes)]

    def fcents(m, k):
        if k < len(fol) and fol[k] is not None:
            return (fol[k] - int(round(fol[k]))) * 100.0 + WORN.get(m, 0) * 1.5 + rng.uniform(-6, 6)
        return None

    def cents(m, k):
        c = TUNE_CENTS
        if v in ('box', 'real', 'cardigan', 'sill', 'winddown'):
            c += WORN.get(m, 0) * (1.0 + 1.5 * (v == 'winddown'))
        if v == 'detuned' and fol:                          # under her sung line: her tuning, only the wear
            return float(np.median([(f - round(f)) * 100.0 for f in fol if f is not None])) + WORN.get(m, 0) * 1.5
        if v == 'detuned':                                  # every tine wrong, and the whole thing sagging flat
            c += WORN.get(m, 0) * 6 + rng.uniform(-35, 35) * a - 55.0 * a * (k / max(1, nn - 1)) ** 1.5
        return c

    if v == 'hum':
        hn = []
        for k, (b, d, m, s, last) in enumerate(notes):
            t0 = max(0.0, tm(b) + rng.uniform(-0.02, 0.04)); t1 = tm(b + d) - (0.3 if last else 0.03)
            hn.append((t0, t1, m + cents(m, k) / 100.0)); out_notes.append((t0, m, s))
        y = MW.hum(hn, rng, 0.8, vib_c=14.0, vib_hz=5.2, scoop=30.0, wobble=8.0, breath=0.03)
        J._put(buf, 0.0, y, 1.0, 0.0)
        y = J._wow(buf, depth=0.0015, hz_=0.2, fl=0.0, seed=seed)
        x = SX.hp(SX.lp(SX.st(y), 1900, 2), 140, 2)                    # through the car's open window, the cabin
        x = SX.eq(x, ('peak', 320, 3.0, 1.2), ('hs', 1400, -4.0, 0.7))
        y = SX.reverb(x, 'box', 0.28, 0.003)
    else:
        for k, (b, d, m, s, last) in enumerate(notes):
            t = tm(b) + rng.uniform(-0.008, 0.012) * (1 + 3 * a)
            vv = rng.uniform(0.86, 1.0)
            c = cents(m, k)
            if v == 'chime':
                J._put(buf, t, _chime_note(m + tr, 0.8 * vv, 0.9 if k == nn - 1 else 0.45, rng, TUNE_CENTS), 1.0,
                       0.0)
            elif v == 'detuned':
                fc = fcents(m, k) if fol else None
                c = c if fc is None else fc
                J._put(buf, t, _box(m + tr, 0.8 * vv, rng, c, 0.9), 1.0, rng.uniform(-0.2, 0.2))
                J._put(buf, t + 0.01, _box(m + 12, 0.32 * vv, rng, c + (9.0 if fol else 23.0), 0.8), 1.0, 0.0)   # a beating low twin
            elif v in ('real', 'cardigan'):
                J._put(buf, t, _box(m + tr, 0.8 * vv, rng, c, 1.3, 0.55), 1.0, rng.uniform(-0.1, 0.1))
            else:                                               # box, winddown, sill
                vel = 0.8 * vv * (1.0 - 0.35 * (k / max(1, nn - 1)) if v == 'winddown' else 1.0)
                J._put(buf, t, _box(m + tr, vel, rng, c, 1.0), 1.0, rng.uniform(-0.15, 0.15))
            out_notes.append((t, m, s))
        if v != 'chime':                                        # oom-pah-pah: the bass tine, then the chord tines
            for b, bs, ch, starts in harm:
                t = tm(b) + rng.uniform(0, 0.015)
                g = {'cardigan': 0.0, 'winddown': 0.7, 'detuned': 0.45 if fol else 0.8}.get(v, 1.0)
                if not g:
                    continue
                bright = 0.55 if v == 'real' else 1.0
                if starts:
                    J._put(buf, t, _box(bs + 24, 0.30 * g, rng, cents(bs, 0), 1.3, bright), 1.0, 0.0)
                else:
                    for c_ in ch:
                        J._put(buf, t + rng.uniform(0, 0.01), _box(c_ + 12, 0.11 * g, rng, cents(c_, 0), 0.9, bright),
                               1.0, rng.uniform(-0.3, 0.3))
        if v == 'sill':                                         # the perfect voice: no vibrato, no scoop, no breath
            hn = [(tm(b), tm(b + d) - (0.12 if last else 0.02), m + TUNE_CENTS / 100.0) for b, d, m, s, last in notes]
            J._put(buf, 0.0, MW.hum(hn, np.random.default_rng(7), 0.55, vib_c=0.0, scoop=0.0, wobble=0.0, breath=0.0,
                                    formants='oo'), 1.0, 0.0)
        y = buf
        if v == 'detuned':
            y = J._wow(y, depth=0.004 + 0.008 * a, hz_=0.27, fl=0.001, fl_hz=4.0, seed=seed)
        if v == 'winddown':                                     # the governor's whirr, slowing; inside the closet
            mech = SX.st(SX.bp(SX.noise(len(y) / SR + 0.1, seed + 5), 900, 3500, 2))[:len(y)]
            ts = np.arange(len(y)) / SR
            spd = np.interp(ts, [tm(b) for b in np.arange(0, total + 1)], np.linspace(1, 0.35, int(total) + 1))
            am = 0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(9.0 * spd) / SR)
            mech = mech * (0.012 * am * spd * (ts < tm(last_b) + 1.0))[:, None]
            y = SX.lp(y + mech.astype(np.float32), 3200, 2)
            y = SX.reverb(SX.eq(y, ('peak', 240, 3.0, 1.2), ('hs', 2000, -3.0, 0.7)), 'box', 0.30, 0.002)
        elif v == 'cardigan':                                   # under the cloth
            y = SX.reverb(SX.lp(y, 2400, 2), 'living', 0.14, 0.004)
        elif v == 'chime':
            y = SX.eq(SX.lp(SX.hp(y, 380, 2), 10000, 2), ('peak', 2500, 2.0, 1.0))
        elif v == 'sill':
            y = SX.reverb(y, 'living', 0.15, 0.004)
        else:
            y = SX.reverb(y, 'living', 0.18 if v in ('box', 'real') else 0.22, 0.005)
    y = SX.st(np.asarray(y, np.float32))
    end = max(t for t, _, _ in out_notes)
    ring = {'chime': 1.4, 'cardigan': 3.5, 'hum': 2.5, 'detuned': 4.0}.get(v, 4.5)
    y = y[:int((end + ring) * SR)]
    if v == 'sill':
        lp_ = tm(total)
        y = _loop_tile(y, lp_, int(loops or 3))
        out_notes = [(t + k * lp_, m, s) for k in range(int(loops or 3)) for t, m, s in out_notes]
        end = max(t for t, _, _ in out_notes)
    y = SX.fade(y, 0.003, min(1.2, 0.4 * ring))                 # every version rings out: never a dead stop
    pk = SX.peak(y)
    if pk > 0.89:
        y = y * (0.89 / pk)
    info = {'version': v, 'phrases': bars, 'loops': int(loops or 1), 'total_beats': total, 'tempo': tp, 'amount': a,
            'n': nn, 'notes': [(round(t, 3), int(m), s) for t, m, s in out_notes], 'transpose': tr,
            'beats': [round(tm(b), 3) for b in np.arange(0, total + 0.5)], 'gap': (round(end, 3), round(len(y) / SR, 3))}
    return y, info


def gap_time(version, **kw):
    """Seconds from a render's start to its LAST note (music_plan's 'gap_at' lands it on an anchor)."""
    return render(version, **kw)[1]['gap'][0]


# ================================================================================================== checks
_KS_MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
_KS_MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
PCN = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'G#', 'A', 'Bb', 'B']


def key_check(y):
    """The key heard (CQT chroma against the Krumhansl profiles: best key, A major's correlation and rank) and the
    tuning heard (cents) against Mom's."""
    import librosa
    x = librosa.resample(SX.mono(SX.st(y)), orig_sr=SR, target_sr=22050)
    C = librosa.feature.chroma_cqt(y=x, sr=22050, hop_length=512).mean(1)
    sc = []
    for r in range(12):
        sc.append((float(np.corrcoef(C, np.roll(_KS_MAJ, r))[0, 1]), PCN[r] + ' major'))
        sc.append((float(np.corrcoef(C, np.roll(_KS_MIN, r))[0, 1]), PCN[r] + ' minor'))
    sc.sort(reverse=True)
    names = [s for _, s in sc]
    tun = float(librosa.estimate_tuning(y=x, sr=22050, resolution=0.01)) * 100
    return {'key': names[0], 'a_major_rank': names.index('A major') + 1,
            'a_major_r': round(dict((s, c) for c, s in sc)['A major'], 2), 'tuning_cents': round(tun, 1),
            'vs_mom_cents': round(tun - TUNE_CENTS, 1)}


def check(v, y, info):
    r = MW.check(v, y, info)
    r['key'] = key_check(y)
    r['n'] = info['n']
    return r


def measure():
    """Mom's sung notes from the voice track: per-word WORLD f0 medians of her two sung lines, her tuning, and the
    agreement of TUNE with them (pitch within a semitone of the written note + her tuning, contour signs)."""
    import librosa, pyworld as pw
    tl = json.load(open(os.path.join(W, 'align', 'timeline.json')))
    vo = os.path.join(W, 'narration', 'narration_en.wav')
    syl = [m for b in '1234' for m in TUNE[b][0]]
    maps = {'mom_one_for_warm': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24, 25, 26, 27],
            'mom_mama_sees_you': [21, 23, 24, 25, 27]}   # 'goodnight.' is mostly its held 'night'
    res, allv = {}, []
    for l in tl['lines']:
        if l.get('tag') not in maps:
            continue
        x, sr = sf.read(vo, start=int(l['t'] * 48000), stop=int(l['end'] * 48000), dtype='float64')
        x = librosa.resample(x if x.ndim == 1 else x.mean(1), orig_sr=sr, target_sr=16000)
        f0, _ = pw.harvest(x, 16000, f0_floor=80, f0_ceil=700, frame_period=10)
        m = np.where(f0 > 0, librosa.hz_to_midi(np.maximum(f0, 1)), np.nan)
        allv += list(m[~np.isnan(m)])
        ws = l['words'] + [['END', l['end']]]
        meas = []
        for k in range(len(ws) - 1):
            s = m[int((ws[k][1] - l['t']) * 100) + 3:int((ws[k + 1][1] - l['t']) * 100) - 2]
            s = s[~np.isnan(s)]
            meas.append(round(float(np.median(s)), 2) if len(s) > 2 else None)
        want = [syl[i] for i in maps[l['tag']]][:len(meas)]
        ok = [abs(a - (b + TUNE_CENTS / 100)) <= 1.0 for a, b in zip(meas, want) if a is not None]
        pairs = [(a, b) for a, b in zip(meas, want) if a is not None]
        con = [np.sign(round(p2[0] - p1[0], 0)) == np.sign(p2[1] - p1[1]) for p1, p2 in zip(pairs, pairs[1:])]
        res[l['tag']] = {'words': [w for w, _ in l['words']], 'measured_midi': meas, 'tune_midi': want,
                         'within_1_semitone_pct': round(100 * float(np.mean(ok)), 0),
                         'contour_agree_pct': round(100 * float(np.mean(con)), 0)}
    res['tuning_cents'] = round(float(librosa.pitch_tuning(librosa.midi_to_hz(np.array(allv)), resolution=0.01)) * 100, 1)
    res['median_midi'] = round(float(np.median(allv)), 2)
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, 'mom_notes.json'), 'w'), indent=1)
    for k, r in res.items():
        print(k, r if not isinstance(r, dict) else {kk: r[kk] for kk in ('within_1_semitone_pct', 'contour_agree_pct')})
    return res


KW = {'box': {}, 'winddown': {}, 'hum': {}, 'sill': {'loops': 2}, 'detuned': {}, 'real': {}, 'cardigan': {},
      'chime': {}}


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
        res[nm] = check(nm, y, info)
        print(nm, json.dumps(res[nm]), flush=True)
    json.dump(res, open(pj, 'w'), indent=1)
    MW.sheet([t for t in res if os.path.exists(os.path.join(OUT, t + '.wav'))], OUT)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
