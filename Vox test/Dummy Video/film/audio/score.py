"""score.py: the music for "If Your Grandpa's Ventriloquist Dummy Tells You A Joke... DON'T LAUGH" (the police film's
v2 score engine, as the delivery film used it), rendered from music_cues.json. The arrangement for this film is pinned
by audio/music_plan.py (cues['track_map'], and the film's own sound identity, the 'show' / 'winks' / 'motif' events,
which mix.py adds when film.py's cue sheet has none).

This film's identity (stem `show`):
    show    the cheerful 1970s kids-show theme ("Saturday Morning with Walter Kemp": the owner's Epidemic track Balloon
            Twister, Macy's Voice) heard from Grandpa's old console TV: band-limited 200 Hz-4.5 kHz, the cabinet's box,
            tape wow and flutter, hiss and hum, the room's first reflections; or from the next room ('far'), or as the
            1974 tape's own sound in the full-frame studio shots ('tape'), or the 1962 first show ('old': Ye Olde Piano
            Roll, a kinescope band with crackle). The awful contrast: it plays while he moves. warp drags the tape (the
            pitch sags up to 9 semitones), stop 'drag' winds it down to a halt (the tape stops mid-joke), 'cut' kills it
            (the lamp, the power). While it plays the dark track bed steps back 6 dB (the drone and the sub stay).
    winks   Mister Winks's theme when he is near: the SAME tune, slowed 9 semitones (0.6x, B major -> D, the film's
            key), detuned (a second read 15 cents sharp, 30 ms late), a slow seasick wow (0.22 Hz, +-35 cents) and a
            flutter, darkened (2.8 kHz), in a big dark room. It is the show theme rotting.
    motif   (the police engine's music box, kept) the celesta lullaby: Grandpa's tuck-in, the three squeezes, "Kiddo",
            the museum glass; its second phrase turns wrong.

Public API
    render(cues, duration=None, *, seed=None, normalize=True, progress=None) -> dict[str, np.ndarray]
        cues: the music_cues.json dict (ARCHITECTURE.md): {duration, intensity: [[t, 0..1], ...],
              events: [{t, type, level?, len?}, ...]}.  duration (s) overrides cues['duration'].
        Returns float32 stereo stems [n, 2] at 48 kHz, n = round(duration * SR), keys = STEMS:
          tracks   the Epidemic tracks arranged to the film (the backbone): cues['track_map'] pins one track section
                   per film section ([{t0, slug, off, flatten?, gain_db?}], off in seconds of the varispeed track,
                   flatten = share of the track's own dynamics the gain automation evens out, default FLATTEN; gain_db =
                   a level trim for that section's track, e.g. a sub-drone track that reads quiet); without it, the police
                   auto-arrangement: one track section per film section
                   (sections start at `rule` cards / `scene` events; longer than 120 s -> split at a silence), chosen
                   by fit of the track's loudness/brightness to the intensity curve, no reuse of material, D/A keys
                   preferred, the D-major track (Tefu) only for calm passages; 3 s equal-power crossfades (or a
                   switch inside a silence); tape varispeed (B->A, F->D, Bb->A, no artefacts); gain automation
                   follows the intensity curve and flattens 30 % of the track's own dynamics
          drones   synth sub (key root, slow beating, glides at key changes) + recorded contrabass/celli sustains
                   on root and fifth (crossfaded sample chains, velocity layers cross-fade pp -> f with intensity)
          pulse    heartbeat ostinato between pulse_on / pulse_off: contrabass pizz + bass drum "lub-dub"; celli
                   (8ths, I > 0.5) and violas (16ths, I > 0.72) spiccato root/b2; tempo 54 -> 110 bpm with intensity
          melodic  the music-box motif (3/4 lullaby, A D E F E | D C# D A; second phrase turns wrong: Eb, Bb, G#)
                   on celesta + glockenspiel over a harp lament bass (D C Bb A); detuned "scary" piano when
                   I >= 0.45, piano octaves + celli doubling when I >= 0.75; sparse low-piano lament between
                   motifs; reversed-piano swell into each rule sting; the ending's music box winding down
          strings  intensity-driven clusters (violas fifth then b2 rub, celli/contrabass tremolo, violins b2 cluster
                   only near the top), `swell` tremolo crescendos (velocity cross-fade), string-glissando risers,
                   the final chord and its unresolved high b2
          hits     hit / stinger / braam / sub_drop / rule sting / end boom and the non-string riser layers, sized
                   by `level`: timpani (tuned to the key), bass drum, low piano clusters, tam-tam (>= 0.7), cymbal
                   (>= 0.85), stinger string stabs (violins b2 + violas tritone), low brass + war tuba braams,
                   Epidemic impacts/stingers/braams/risers/sub drops, synth sub booms; each composite decays with
                   T60 1.5-2.8 s plus a 2 s hall, and is peak-limited to -3 dBFS
        Levels (normalize=True): the sum of every stem except `hits` integrates at REF_LUFS = -28 LUFS (AUDIO_SPEC
        bed = voice - 13 LU, minus room for SFX). Hits are sized against that reference, not normalised:
        momentary max = REF + 2 + 9 * level LU (v2.1; braams REF + 9 * level; mix.py ducks the hit tails under the voice).
        mix.py: apply ONE gain to all stems (e.g. voice_integrated - 13 - REF_LUFS); do not loudness-normalise the
        score sum (hits would pull the bed down). Silences, the end fade, pre-hit cuts (bed down 6-16 dB for
        0.35-1 s before each hit) and the post-silence re-entry (music back 12 dB quieter) are already applied;
        mix.py adds voice ducking (about 3 dB) and the final limiter.
    Unknown event types are ignored with a warning (never a crash).
    plan(cues, duration=None) -> dict      the arrangement without audio: sections [{slug, s0, s1, off, via_silence}],
                                           keys [[t0, t1, root_pc, mode(+1 major / -1 minor)]], t_end
    STEMS, SR, REF_LUFS, TRACKS (varispeed table), FIXED_KEY
    loudness helpers (BS.1770): integrated(x), short_term(x, hop=1.0), momentary_max(x)
    CLI: python score.py music_cues.json out_dir [--duration D] -> out_dir/score_<stem>.wav (32-bit float),
         score_sum.wav, score_plan.json

Event semantics (t in seconds, level 0..1, default 0.7)
    hit, stinger, braam (len = hold, default 3.5 s), sub_drop: start at t (transients sample-aligned to t);
    riser: ends at t (len default 6 s; when a hit lands on t the riser stops 0.16-0.25 s early: a breath before
    the hit); silence: everything out for len (default 1.7 s), depth 20 + 40 * level dB, 0.12 s fade;
    motif: phrase from t (len -> bars of 2.37 s, default 4 bars the first time, then 8; inst 'musicbox' | 'piano' |
    'octaves' forces the instrument, otherwise the intensity picks it);
    show: the show theme from the old TV (len, slug, shift, off, space, warp, warp_at, stop, fade; see render_show);
    winks: the same tune rotting, Mister Winks's theme (len, slug, shift, off, depth, stop; see render_winks);
    swell: string crescendo from t peaking at t + len (default 12 s), the whole bed breathes with it;
    pulse_on / pulse_off; rule: rule-card sting at t (and an arrangement boundary);
    end: the final cadence from t (len default 12 s): everything else fades over 4 s, D-minor chord (always home
    to D), music box winds down, a high b2 is left hanging. Optional: "scene" events = boundaries without sound.

Keys: each film section takes the dominant bass root of its track material (harmonic-sum bass salience, 14 s
window; a second key only for a modulation >= 20 s); every tonal layer (sub, drones, motif, lament, pulse,
timpani tuning, braams) follows it, so the recorded layers never fight the track.

Sources: Epidemic tracks/SFX (catalog_epidemic_delivery.json: the delivery, police and mirror sets; owner's licence) and the free library (library.py:
VSCO-2-CE CC0, Salamander CC-BY, Karoryfer Scary Piano, celesta, OpenAIR IRs CC-BY); synthesis only for the
sub drone and sub booms. Track analysis is cached in W/cache/score/ (W = film/_work).
"""
import os, sys, json, math, hashlib, time
import numpy as np
import soundfile as sf
import soxr
from scipy.signal import butter, sosfilt, oaconvolve

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import library as L  # noqa: E402

SR = 48000
STEMS = ('tracks', 'drones', 'pulse', 'melodic', 'strings', 'show', 'hits')
REF_LUFS = -28.0
NOM = -20.0                      # every sample is normalised to this momentary-max loudness before gains
W = os.path.normpath(os.path.join(HERE, '..', '_work'))   # this film's work dir
S = W
CACHE = os.path.join(W, 'cache', 'score')
CR = 100                         # control rate for gain curves (Hz)
SLOPE = 13.5                     # bed level change (dB) from intensity 0 to 1 (v2.1: 9 -> 13.5, the bed breathes)
PC = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']

# Epidemic tracks: varispeed (semitones, resampling = tape-style, no artefacts) so every track sits on D, A or G.
# Delivery film: the 9 new tracks are the backbone, the police six stay available where they fit (keys from
# audio/catalog_epidemic_delivery.json: Krumhansl key + lowest-octave chroma). The mirror set's tracks are catalogued
# but not loaded here (memory); add them with a shift to use them.
TRACKS = {
    'are_you_alone_victor_lundberg': 0,          # D (bass D), dark sub drone that swells to one spike: open + sting
    'the_logic_of_tyrants_hampus_naeselius': 1,  # bass C# (Krumhansl D# minor) -> D, dark low pulse
    'afterthoughts_beyza': -3,                   # F minor  -> D minor, slow, no drums
    'haunted_mind_etienne_roussel': 0,           # A minor, slow build, mid register, no drums
    'goth_christmas_par': -4,                    # F# minor -> D minor, bells / lullaby, slowed 21 %: the memory theme
    'code_of_violence_dian_shuai': 0,            # D minor, dark pulsing bass build
    'turning_stones_stefan_ekstrom': 2,          # C minor  -> D minor, pure dark drone (99 % < 250 Hz)
    'one_step_away_dian_shuai': 0,               # A (major), percussive build, the climax; drops at 132 s
    'one_hampus_naeselius': 0,                   # G minor, percussive (alternate climax)
    'a_massive_mist_ethan_sloan': -2,            # police: B minor  -> A minor
    'dark_forebodings_ethan_sloan': 0,           # police: G minor (iv of D minor), flat dark drone
    'dark_tunnels_ethan_sloan': -3,              # police: F minor  -> D minor (with Bb)
    'from_hell_christoffer_moe_ditlevsen': -1,   # police: Bb minor -> A minor
    'in_continuum_dream_cave': 0,                # police: D minor
    'tefu_sayuri_hayashi_egnell': 0,             # police: D major (false comfort)
    # dummy film: four of the mirror set's tracks
    'when_the_sun_sets_anna_landstrom': 1,       # mirror: C# major -> D major, a quiet warm pad (Grandpa, Walter's show)
    'come_closer_belladonna_strings': -1,        # mirror: D# minor -> D minor, horror strings (the stairs, the hand)
    'don_t_look_belladonna_strings': -1,         # mirror: D# minor -> D minor, horror strings (the bookcase, the TV)
    'irene_kevin_dailey': 0,                     # mirror: D minor, starts near silent and builds (the tape's twist)
}
# The vintage tunes (the dummy set) are NOT arranged as tracks: they are the diegetic show on the TV (event 'show') and,
# warped, Mister Winks's theme (event 'winks'). slug -> semitones for the TV (the tune sits on A, the film's second
# centre, a little slow: an old tape) and the default start (s, in the original track).
VINTAGE = {
    'balloon_twister_macy_s_voice': (-2.0, 6.0),            # B major -> A: THE show theme (5.5 s: the band comes in)
    'ye_olde_piano_roll_the_fly_guy_five': (-4.0, 2.0),     # F# minor -> D minor: the 1962 first show
    'the_tale_of_tomfoolery_tom_martin_landstrom': (-7.0, 1.0),   # A minor -> D minor: whimsical, spare
    'hold_tight_roll_macy_s_voice': (-2.0, 3.0), 'roaming_around_the_fly_guy_five': (0.0, 1.0),
    'circus_beat_martin_landstrom': (-2.0, 5.0), 'chasing_snakes_martin_landstrom': (-7.0, 2.0),
    'once_i_was_a_miner_martin_landstrom': (-4.0, 4.0), 'a_gal_i_know_martin_landstrom': (-7.0, 1.0),
    'it_s_just_me_instrumental_version_john_runefelt': (-6.0, 1.0), 'un_jour_peut_etre_ote': (-4.0, 1.0),
}
SHOW_THEME = 'balloon_twister_macy_s_voice'
WINKS_SHIFT = -9.0                # the theme, rotting: B -> D, 0.6x
WINKS_OFF = 6.0                   # (s in the original track) the tune, not the intro
SHOW_DUCK = {'show': -6.0, 'winks': -3.0}   # the dark track bed steps back while the TV / the Winks theme plays
KEYPREF = {2: 0.0, 9: 0.05, 5: 0.45, 10: 0.45, 7: 0.6, 0: 0.7}   # cost by root pitch class: D, A, F, Bb, G, C
KEY_W = 2.0                      # weight of the key cost (v2.1: 0.2 -> 0.6, every section lands on D or A)
OTHER_KEY = 3.0                  # cost of any other root (Eb, Ab, B, E, F#, C#: the semitone / tritone clashes)
CLASH = (1, 2, 6, 10, 11)        # root intervals that must not crossfade (semitone, whole tone, tritone)
CALM_MAX = 0.30                  # the D-major track (Tefu) only where the intensity stays under this (75th pct)
REUSE_W = 1.2                    # cost of replaying the same track material (fraction of the section)
FIXED_KEY = {'tefu_sayuri_hayashi_egnell': (2, 1)}   # melodic bass: root detection unreliable; D pedal, major
FLATTEN = 0.3                    # share of each track's own dynamics flattened by the gain automation (was 0.6-0.8)
DEFAULT_LEN = {'braam': 3.5, 'riser': 6.0, 'silence': 1.7, 'swell': 12.0, 'end': 12.0, 'show': 10.0, 'winks': 8.0}
KNOWN_EVENTS = ('hit', 'stinger', 'braam', 'riser', 'sub_drop', 'silence', 'motif', 'swell', 'pulse_on', 'pulse_off',
                'rule', 'end', 'scene', 'show', 'winks')


# ----------------------------------------------------------------------------------------------------------- utils
def db(x):
    return 10.0 ** (np.asarray(x, dtype=np.float64) / 20.0)


def _smooth(x, n):
    if n <= 1:
        return x
    k = np.hanning(n * 2 + 1)
    k /= k.sum()
    pad = np.pad(x, (n, n), mode='edge')
    return np.convolve(pad, k, mode='valid')


def _sstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


_SOS = {}


def _filt(x, kind, fc, order=2):
    key = (kind, round(float(np.atleast_1d(fc)[0]), 1), round(float(np.atleast_1d(fc)[-1]), 1), order)
    if key not in _SOS:
        _SOS[key] = butter(order, fc, kind, fs=SR, output='sos')
    return sosfilt(_SOS[key], x, axis=0).astype(np.float32, copy=False)


def _peq(x, f0, gain_db, q=0.9):
    """RBJ peaking EQ (one biquad), axis 0."""
    A = 10 ** (gain_db / 40)
    w = 2 * np.pi * f0 / SR
    al = np.sin(w) / (2 * q)
    b = np.array([1 + al * A, -2 * np.cos(w), 1 - al * A])
    a = np.array([1 + al / A, -2 * np.cos(w), 1 - al / A])
    sos = np.concatenate([b / a[0], a / a[0]])[None, :]
    return sosfilt(sos, x, axis=0).astype(np.float32, copy=False)


def _fade(n, kind='in'):
    w = np.sin(np.linspace(0, np.pi / 2, max(n, 1))) if kind == 'in' else np.cos(np.linspace(0, np.pi / 2, max(n, 1)))
    return w.astype(np.float32)


def _st(x):
    x = np.asarray(x, dtype=np.float32)
    return np.stack([x, x], 1) if x.ndim == 1 else x


def _pan(sig, p):
    if not p:
        return sig
    a = (p + 1) * np.pi / 4
    return sig * np.array([np.cos(a), np.sin(a)], dtype=np.float32) * np.float32(math.sqrt(2))


def _width(sig, w):
    m = 0.5 * (sig[:, 0] + sig[:, 1])
    s = 0.5 * (sig[:, 0] - sig[:, 1]) * w
    return np.stack([m + s, m - s], 1).astype(np.float32)


# ------------------------------------------------------------------------------------------------- loudness (BS.1770)
_KSOS = np.array([[1.53512485958697, -2.69169618940638, 1.19839281085285, 1.0, -1.69065929318241, 0.73248077421585],
                  [1.0, -2.0, 1.0, 1.0, -1.99004745483398, 0.99007225036621]])


def _kms(x, win, hop):
    x = _st(x)
    p = np.empty(len(x), np.float64)
    zi = np.zeros((2, 2, 2))
    step = 1 << 21
    for a in range(0, len(x), step):
        y, zi = sosfilt(_KSOS, x[a:a + step].astype(np.float64), axis=0, zi=zi)
        p[a:a + len(y)] = (y ** 2).sum(1)
    c = np.concatenate([[0.0], np.cumsum(p)])
    if len(p) < win:
        return np.array([c[-1] / max(len(p), 1)])
    starts = np.arange(0, len(p) - win + 1, hop)
    return (c[starts + win] - c[starts]) / win


def _lufs(ms):
    return -0.691 + 10 * np.log10(np.maximum(ms, 1e-20))


def momentary_max(x):
    return float(_lufs(_kms(x, int(0.4 * SR), int(0.05 * SR))).max())


def short_term(x, hop=1.0):
    return _lufs(_kms(x, 3 * SR, int(hop * SR)))


def integrated(x):
    ms = _kms(x, int(0.4 * SR), int(0.1 * SR))
    l = _lufs(ms)
    g = ms[l > -70]
    if not len(g):
        return -100.0
    rel = _lufs(g.mean()) - 10
    g = ms[(l > -70) & (l > rel)]
    return float(_lufs(g.mean())) if len(g) else -100.0


# ---------------------------------------------------------------------------------------------------- sample bank
class Bank:
    """Loads samples once, normalised to NOM LUFS, and caches pitch-shifted (resampled) versions."""

    def __init__(self):
        self.raw, self.pitched, self.meta = {}, {}, {}
        cp = next((os.path.join(HERE, f) for f in ('catalog_epidemic_dummy.json', 'catalog_epidemic_delivery.json',
                                                     'catalog_epidemic.json') if os.path.exists(os.path.join(HERE, f))))
        epi = json.load(open(cp))
        self.epi_sfx = {e['slug']: e for e in epi['sfx']}
        self.epi_music = {e['slug']: e for e in epi['music']}
        self._cats = {}

    def get(self, key):
        """key: free-library entry dict/id, or 'epi:<slug>'. Returns float32 [n, 2] at NOM LUFS."""
        k = key if isinstance(key, str) else key['id']
        if k in self.raw:
            return self.raw[k]
        if k.startswith('epi:'):
            e = self.epi_sfx[k[4:]]
            y, sr = sf.read(e['path'], dtype='float32', always_2d=True)
            if sr != SR:
                y = soxr.resample(y, sr, SR, quality='VHQ').astype(np.float32)
            y = _st(y[:, :2]) if y.shape[1] >= 2 else _st(y[:, 0])
            lufs = e.get('lufs')
        else:
            e = L.get(k)
            y = L.load(e)
            lufs = e.get('lufs')
        # normalise by momentary max (perceived peak loudness), so plucked, struck and sustained samples line up
        y = (y * db(NOM - momentary_max(y))).astype(np.float32)
        self.raw[k] = y
        return y

    def shifted(self, key, semis):
        k = key if isinstance(key, str) else key['id']
        q = round(float(semis) * 100)
        if q == 0:
            return self.get(key)
        kk = (k, q)
        if kk not in self.pitched:
            r = 2 ** (q / 1200.0)
            y = soxr.resample(self.get(key), SR, SR / r, quality='HQ').astype(np.float32)
            self.pitched[kk] = y
        return self.pitched[kk]

    def cat(self, category):
        if category not in self._cats:
            out = []
            for e in L.entries(category=category):
                m = e.get('midi') if e.get('midi') is not None else e.get('midi_est')
                if m is None:
                    continue
                true = m
                if e.get('midi') is not None and e.get('midi_est') is not None and abs(e['midi_est'] - e['midi']) < 0.5 \
                        and 'horror' not in category:
                    true = e['midi_est']
                out.append((float(m), float(true), e.get('vel'), e.get('rr'), e))
            self._cats[category] = out
        return self._cats[category]

    def note(self, category, midi, vel=None, rr=0, max_shift=3.0):
        """Nearest sampled note (velocity layer closest to vel, round robin among ties). Returns (key, semis)."""
        c = self.cat(category)
        if not c:
            raise KeyError(category)
        best = min(abs(x[0] - midi) for x in c)
        if best > max_shift:
            raise KeyError(f'{category}: no note near {midi}')
        c = [x for x in c if abs(x[0] - midi) <= best + 1e-6]
        if vel is not None and any(x[2] is not None for x in c):
            bv = min(abs((x[2] or 0) - vel) for x in c)
            c = [x for x in c if abs((x[2] or 0) - vel) == bv]
        c.sort(key=lambda x: (x[3] or 0, x[4]['id']))
        x = c[rr % len(c)]
        return x[4], midi - x[1]

    def vels(self, category):
        return sorted({x[2] for x in self.cat(category) if x[2] is not None})

    def play(self, category, midi, vel=None, rr=0, dur=None, rel=0.35):
        e, s = self.note(category, midi, vel, rr)
        y = self.shifted(e, s)
        if dur is not None:
            n = int((dur + rel) * SR)
            if n < len(y):
                y = y[:n].copy()
                r = int(rel * SR)
                y[-r:] *= _fade(r, 'out')[:, None]
        return y


def _limit(y, thr_db=-3.0, la=0.0015, rel=0.08):
    """Lookahead peak limiter for one-shot composites (keeps the punch, caps peaks at thr_db dBFS)."""
    from scipy.ndimage import maximum_filter1d, minimum_filter1d
    from scipy.signal import lfilter
    thr = 10 ** (thr_db / 20)
    a = np.abs(y).max(1)
    if a.max() <= thr:
        return y
    L = max(1, int(la * SR))
    r = np.minimum(1.0, thr / np.maximum(maximum_filter1d(a, 2 * L + 1), 1e-9))
    r = minimum_filter1d(r, 4 * L + 1)
    k = np.exp(-1.0 / (rel * SR))
    g, _ = lfilter([1 - k], [1, -k], r, zi=[k * r[0]])
    g = np.minimum(g, r)
    return (y * g[:, None]).astype(np.float32)


def _onset(y, thr=0.12):
    a = np.abs(y).max(1)
    pk = a.max() + 1e-12
    i = int(np.argmax(a > thr * pk))
    return max(0, i - int(0.002 * SR))


def _peak_time(y, win=0.05):
    a = (y.astype(np.float64) ** 2).sum(1)
    n = int(win * SR)
    c = np.convolve(a, np.ones(n) / n, mode='same')
    return int(np.argmax(c))


# ------------------------------------------------------------------------------------------------------ buses
IRS = {
    'hall': 'openair__1st_baptist_nashville_1st_baptist_nashville_far_clo',   # T60 2.0 s, L/R corr 0.70
    'recital': 'openair2__recital_hall',                                     # T60 1.8 s
    'cavern': 'openair__r1_nuclear_reactor_hall_stereo_r1_ortf_48k',          # T60 4.5 s
}


def _ir(name):
    ids = {e['id']: e for e in L.entries(category='ir')}
    k = IRS[name]
    e = ids.get(k) or next(v for i, v in ids.items() if i.startswith(k[:40]))
    y = L.load(e).astype(np.float64)
    i0 = max(0, int(np.argmax(np.abs(y).max(1))) - int(0.001 * SR))
    y = y[i0:]
    y[: int(0.004 * SR)] *= 0.25                       # tame the direct sound: the bus is a send
    y = sosfilt(butter(2, [90, 6500], 'bandpass', fs=SR, output='sos'), y, axis=0)
    # unity gain in the musical band (pink-weighted 80 Hz - 4 kHz), not unit total energy (rooms keep their energy low)
    nf = 1 << int(np.ceil(np.log2(len(y) + 1)))
    H = np.abs(np.fft.rfft(y, nf, axis=0)) ** 2
    f = np.fft.rfftfreq(nf, 1 / SR)
    band = (f > 80) & (f < 4000)
    y /= np.sqrt((H[band].mean(1) / f[band]).sum() / (1 / f[band]).sum())
    if len(y) > 7 * SR:
        y = y[: 7 * SR]
        y[-2 * SR:] *= np.cos(np.linspace(0, np.pi / 2, 2 * SR))[:, None]
    return y.astype(np.float32)


class Bus:
    def __init__(self, n):
        self.n = n
        self.dry = np.zeros((n, 2), np.float32)
        self.send = {}

    def add(self, t, sig, g=1.0, pan=0.0, rev=None, at=0):
        """Add sig so that its sample `at` lands on time t. g: scalar (linear) or array per sample. rev: {ir: amt}."""
        sig = _st(sig)
        i0 = int(round(t * SR)) - at
        a, b = max(0, i0), min(self.n, i0 + len(sig))
        if b <= a:
            return
        s = sig[a - i0:b - i0]
        if np.ndim(g):
            s = s * np.asarray(g, np.float32)[a - i0:b - i0, None]
        elif g != 1.0:
            s = s * np.float32(g)
        if pan:
            s = _pan(s, 0.7 * pan)
        self.dry[a:b] += s
        for k, amt in (rev or {}).items():
            if amt <= 0:
                continue
            if k not in self.send:
                self.send[k] = np.zeros(self.n, np.float32)
            self.send[k][a:b] += (s[:, 0] + s[:, 1]) * np.float32(0.5 * amt)

    def mixdown(self, irs):
        out = self.dry
        for k, snd in self.send.items():
            nz = np.flatnonzero(np.abs(snd) > 1e-7)
            if not len(nz):
                continue
            a, b = int(nz[0]), int(nz[-1]) + 1
            ir = irs[k]
            step = 1 << 21                            # chunked overlap-add keeps memory flat
            for c0 in range(a, b, step):
                c1 = min(b, c0 + step)
                w = np.stack([oaconvolve(snd[c0:c1], ir[:, c], mode='full') for c in range(2)], 1)
                m = min(len(w), self.n - c0)
                out[c0:c0 + m] += _width(w[:m].astype(np.float32), 0.6)
                del w
        self.send = {}
        return out


# ------------------------------------------------------------------------------------------------- cue parsing
def _events(cues):
    ev = []
    for i, e in enumerate(cues.get('events', [])):
        d = dict(e)
        d['t'] = float(d.get('t', 0.0))
        d['level'] = float(np.clip(d.get('level', 0.7) if d.get('level') is not None else 0.7, 0, 1))
        d['type'] = str(d.get('type', '')).lower()
        d['i'] = i
        if d.get('len') is None and d['type'] in DEFAULT_LEN:
            d['len'] = DEFAULT_LEN[d['type']]
        ev.append(d)
    ev.sort(key=lambda e: (e['t'], e['i']))
    return ev


def _intensity(cues, dur):
    pts = cues.get('intensity') or [[0, 0.3], [dur, 0.3]]
    pts = sorted((float(a), float(np.clip(b, 0, 1))) for a, b in pts)
    tt = np.arange(int(dur * CR) + 1) / CR
    return np.interp(tt, [p[0] for p in pts], [p[1] for p in pts]).astype(np.float64)


# --------------------------------------------------------------------------------------------- track analysis
def _track_audio(bank, slug):
    k = 'trk:' + slug
    if k not in bank.raw:
        e = bank.epi_music[slug]
        y, sr = sf.read(e['path'], dtype='float32', always_2d=True)
        r = 2 ** (TRACKS[slug] / 12.0)
        y = soxr.resample(y[:, :2], sr, SR / r, quality='VHQ').astype(np.float32)
        y = (y * db(NOM - e['lufs'])).astype(np.float32)
        bank.raw[k] = y
    return bank.raw[k]


def _vintage_audio(bank, slug, semis):
    """A vintage tune (the dummy set) varispeeded by `semis` (tape-style resampling), at NOM LUFS."""
    k = f'vin:{slug}:{round(float(semis) * 100)}'
    if k not in bank.raw:
        e = bank.epi_music[slug]
        y, sr = sf.read(e['path'], dtype='float32', always_2d=True)
        y = _st(y[:, 0]) if y.shape[1] == 1 else y[:, :2]
        r = 2 ** (float(semis) / 12.0)
        y = soxr.resample(y, sr, SR / r, quality='VHQ').astype(np.float32)
        bank.raw[k] = (y * db(NOM - e['lufs'])).astype(np.float32)
    return bank.raw[k]


def _bass_salience(y, nwin, hop=2.0, win=1 << 17):
    """Per 2 s window: pitch-class salience of the bass (harmonic sum of 5 partials, f0 27.5-110 Hz)."""
    m = y.mean(1)
    f = np.fft.rfftfreq(win, 1 / SR)
    df = f[1]
    f0s = 27.5 * 2 ** (np.arange(0, 28) / 12)
    hann = np.hanning(win)
    out = np.zeros((nwin, 12))
    for k in range(nwin):
        c = int(k * hop * SR + hop * SR / 2)
        a = max(0, c - win // 2)
        seg = m[a:a + win]
        if len(seg) < win:
            seg = np.pad(seg, (0, win - len(seg)))
        P = np.abs(np.fft.rfft(seg * hann))
        for f0 in f0s:
            v = sum(P[int(round(h * f0 / df))] / h for h in range(1, 6) if h * f0 < 600)
            pc = int(round(69 + 12 * np.log2(f0 / 440))) % 12
            out[k, pc] = max(out[k, pc], v)
    return out


def _track_info(bank):
    """Per-track features on a 2 s grid after varispeed: loudness (rel own integrated), centroid, bass root, mode."""
    os.makedirs(CACHE, exist_ok=True)
    sig = hashlib.md5(json.dumps(TRACKS, sort_keys=True).encode()).hexdigest()[:8]
    p = os.path.join(CACHE, f'tracks_v4_{sig}.json')
    if os.path.exists(p):
        return json.load(open(p))
    import librosa
    info = {}
    for slug in TRACKS:
        y = _track_audio(bank, slug)
        dur = len(y) / SR
        m = y.mean(1)
        hop = 2 * SR
        nwin = int(dur // 2)
        L2, C2 = [], []
        st = short_term(y, hop=2.0)
        for k in range(nwin):
            seg = m[k * hop:(k + 1) * hop]
            sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2
            f = np.fft.rfftfreq(len(seg), 1 / SR)
            C2.append(float((sp * f).sum() / (sp.sum() + 1e-20)))
        L2 = [float(st[min(k, len(st) - 1)]) for k in range(nwin)]
        y22 = soxr.resample(m, SR, 22050)
        ch = librosa.feature.chroma_cqt(y=y22, sr=22050, hop_length=1024, fmin=librosa.note_to_hz('C1'), n_octaves=6)
        fpw = 22050 * 2 / 1024
        roots, m3, M3, chs = [], [], [], []
        sal = _bass_salience(y, nwin)
        for k in range(nwin):
            roots.append(int(np.argmax(sal[max(0, k - 3):k + 4].sum(0))))           # 14 s window
            if slug in FIXED_KEY:
                roots[-1] = FIXED_KEY[slug][0]
        rr = []
        for k in range(nwin):                                          # mode filter over 14 s
            w = roots[max(0, k - 3):k + 4]
            rr.append(max(set(w), key=w.count))
        for k in range(nwin):
            a, b = int(k * fpw), int(min(ch.shape[1], (k + 1) * fpw))
            full = ch[:, a:b].mean(1) if b > a else np.ones(12)
            m3.append(float(full[(rr[k] + 3) % 12]))
            M3.append(float(full[(rr[k] + 4) % 12]))
            chs.append([round(float(v), 4) for v in full])
        modes = [1 if b_ > 1.6 * a_ else -1 for a_, b_ in zip(m3, M3)]
        if slug in FIXED_KEY:
            modes = [FIXED_KEY[slug][1]] * nwin
            M3 = [max(a_, b_) * 2 + 1e-3 for a_, b_ in zip(m3, M3)] if FIXED_KEY[slug][1] > 0 else M3
            chs = [[v * (3 if i == (FIXED_KEY[slug][0] + 4) % 12 else 1) for i, v in enumerate(c)] for c in chs]
        info[slug] = dict(dur=dur, L2=L2, C2=C2, root=rr, mode=modes, m3=m3, M3=M3, chroma=chs, lufs=integrated(y))
    json.dump(info, open(p, 'w'))
    return info


# ---------------------------------------------------------------------------------------------- arrangement plan
def _arousal(L2, C2):
    l = np.clip((np.asarray(L2) - NOM + 12) / 15.0, 0, 1)
    c = np.clip((np.log2(np.maximum(C2, 60)) - np.log2(80)) / np.log2(1400 / 80), 0, 1)
    return 0.65 * l + 0.35 * c


def plan(cues, duration=None, bank=None):
    dur = float(duration or cues.get('duration') or 60.0)
    bank = bank or Bank()
    info = _track_info(bank)
    ev = _events(cues)
    I = _intensity(cues, dur)
    # section boundaries: rule cards, scenes, end
    b = [0.0] + [e['t'] for e in ev if e['type'] in ('rule', 'scene') and 4 < e['t'] < dur - 8]
    ends = [e['t'] for e in ev if e['type'] == 'end']
    t_end = min(ends) if ends else dur
    b = sorted(set(round(x, 3) for x in b if x < t_end - 6))
    merged = [b[0]]
    for x in b[1:]:
        if x - merged[-1] >= 20:
            merged.append(x)
    bounds = merged + [dur]
    maxlen = max(v['dur'] for v in info.values()) - 6
    sil = [e['t'] for e in ev if e['type'] == 'silence']
    secs = []
    for s0, s1 in zip(bounds[:-1], bounds[1:]):
        stack = [(s0, s1)]
        while stack:
            a, c = stack.pop(0)
            if c - a <= min(maxlen, 120):
                secs.append((a, c))
                continue
            mid = 0.5 * (a + c)
            cand = [s for s in sil if a + 30 < s < c - 30]
            cut = min(cand, key=lambda s: abs(s - mid)) if cand else mid
            stack[:0] = [(a, cut), (cut, c)]
    used = {k: [] for k in info}
    segs, prev, prev_root = [], None, None
    tm = [dict(x) for x in (cues.get('track_map') or []) if x.get('slug') in info and float(x.get('t0', 0)) < dur]
    unknown = [x.get('slug') for x in (cues.get('track_map') or []) if x.get('slug') not in info]
    if unknown:
        print('[score] WARNING: track_map slugs not in TRACKS, ignored:', unknown, flush=True)
    if tm:                                            # pinned arrangement (audio/music_plan.py)
        tm.sort(key=lambda x: float(x['t0']))
        tm[0]['t0'] = 0.0
        for k, x in enumerate(tm):
            s0 = float(x['t0']); s1 = float(tm[k + 1]['t0']) if k + 1 < len(tm) else dur
            segs.append(dict(slug=x['slug'], s0=s0, s1=s1, off=float(x.get('off', 0.0)),
                             flatten=float(x.get('flatten', FLATTEN)), gain_db=float(x.get('gain_db', 0.0))))
        secs = []
    for si, (s0, s1) in enumerate(secs):
        ln = s1 - s0
        tk = np.arange(s0, s1, 2.0)
        Ik = I[np.minimum((tk * CR).astype(int), len(I) - 1)]
        best = None
        for slug, v in info.items():
            a = _arousal(v['L2'], v['C2'])
            nwin = len(a)
            room = v['dur'] - 1.0
            offs = np.arange(0, max(0.0, room - ln) + 1e-6, 2.0) if room >= ln else np.array([0.0])
            for o in offs:
                idx = np.minimum(((o + tk - s0) / 2).astype(int), nwin - 1)
                cost = float(np.mean((a[idx] - Ik) ** 2))
                if room < ln:
                    cost += 1.0 + (ln - room) / ln            # would need to loop: strongly avoided
                ov = sum(max(0, min(o + ln, u1) - max(o, u0)) for u0, u1 in used[slug])
                cost += REUSE_W * ov / ln                      # reuse allowed when the key fit needs it
                if slug == prev:
                    cost += 0.08
                rts = np.asarray(v['root'])[idx]
                cost += KEY_W * float(np.mean([KEYPREF.get(int(r), OTHER_KEY) for r in rts]))
                if np.mean(np.asarray(v['mode'])[idx]) > 0:     # major = false comfort: only for calm passages
                    cost += 1.5 * max(0.0, float(Ik.mean()) - 0.3)
                if FIXED_KEY.get(slug, (0, -1))[1] > 0 and float(np.percentile(Ik, 75)) > CALM_MAX:
                    cost += 5.0                                 # Tefu (D major) never under tension
                if prev_root is not None and (int(rts[0]) - prev_root) % 12 in CLASH:
                    cost += 0.25                                # would clash with the outgoing section
                if (si == 0 or si == len(secs) - 1) and rts[0] != 2:
                    cost += 0.04
                if o == 0:
                    cost -= 0.01
                if best is None or cost < best[0]:
                    best = (cost, slug, float(o))
        _, slug, o = best
        used[slug].append((o, o + ln))
        segs.append(dict(slug=slug, s0=s0, s1=s1, off=o))
        prev = slug
        v = info[slug]
        prev_root = int(v['root'][min(int((o + ln - 1.0) / 2), len(v['root']) - 1)])
    # boundary kinds: a silence starting within 2.5 s before the boundary -> switch inside the silence
    for k in range(1, len(segs)):
        bt = segs[k]['s0']
        ss = [e for e in ev if e['type'] == 'silence' and -2.5 <= bt - e['t'] <= 2.5]
        segs[k]['via_silence'] = (ss[0]['t'], ss[0]['t'] + ss[0]['len']) if ss else None
    # key map on a 0.5 s grid
    grid = np.arange(0, dur, 0.5)
    root = np.zeros(len(grid), int)
    chg = np.zeros((len(grid), 12))
    for sg in segs:
        v = info[sg['slug']]
        sel = (grid >= sg['s0']) & (grid < sg['s1'])
        idx = np.minimum(((sg['off'] + grid[sel] - sg['s0']) / 2).astype(int), len(v['root']) - 1)
        root[sel] = np.array(v['root'])[idx]
        chg[sel] = np.array(v['chroma'])[idx]
    # keys: one per film section (the dominant bass root of its track material, a pedal point under passing
    # chords); a second key only for a modulation that lasts >= 20 s. Mode from the aggregated chroma.
    def _mode(c, r0):
        return 1 if c[(r0 + 4) % 12] > 1.6 * c[(r0 + 3) % 12] and c[(r0 + 4) % 12] > 0.45 * c[r0] else -1
    out = []
    for sg in segs:
        sel = np.flatnonzero((grid >= sg['s0']) & (grid < sg['s1']))
        if not len(sel):
            continue
        runs, k0 = [], sel[0]
        for k in list(sel[1:]) + [None]:
            if k is None or root[k] != root[k0]:
                end = (k if k is not None else sel[-1] + 1)
                runs.append([k0, end, int(root[k0])])
                k0 = k
        while len(runs) > 1 and min(r[1] - r[0] for r in runs) < 40:     # 40 grid steps = 20 s
            i = min(range(len(runs)), key=lambda j: runs[j][1] - runs[j][0])
            j = i - 1 if i > 0 and (i == len(runs) - 1 or runs[i - 1][1] - runs[i - 1][0] >= runs[i + 1][1] - runs[i + 1][0]) \
                else i + 1
            lo, hi = min(i, j), max(i, j)
            runs[lo:hi + 1] = [[runs[lo][0], runs[hi][1], runs[j][2]]]
        for a0, a1, r0 in runs:
            t0 = sg['s0'] if a0 == sel[0] else float(grid[a0])
            t1 = sg['s1'] if a1 == sel[-1] + 1 else float(grid[a1])
            out.append([float(t0), float(t1), r0, _mode(chg[a0:a1].sum(0), r0)])
    merged = []
    for r in out:
        if merged and merged[-1][2] == r[2] and merged[-1][3] == r[3]:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    out = merged
    for k in range(1, len(segs)):
        if segs[k].get('via_silence'):
            continue
        bt = segs[k]['s0']
        r0, r1 = _key_at(out, bt - 1.0)[0], _key_at(out, bt + 0.5)[0]
        if (r1 - r0) % 12 in CLASH:          # no crossfade between clashing keys: a hard switch on the rule sting
            segs[k]['via_silence'] = (bt - 0.35, bt + 0.05)
            segs[k]['switch'] = 'sting'
    return dict(duration=dur, sections=segs, keys=out, t_end=t_end)


def _key_at(keys, t):
    for r in keys:
        if r[0] <= t < r[1]:
            return r[2], r[3]
    return keys[-1][2], keys[-1][3]


def _reg(pc, lo, hi):
    """MIDI note of pitch class pc inside [lo, hi]."""
    m = lo + ((pc - lo) % 12)
    return m if m <= hi else m - 12


# --------------------------------------------------------------------------------------------------- the score
class Score:
    def __init__(self, cues, duration, seed=None, progress=None):
        self.cues = cues
        self.dur = float(duration)
        self.n = int(round(self.dur * SR))
        self.nc = int(self.dur * CR) + 2
        h = hashlib.md5(json.dumps(cues, sort_keys=True, default=str).encode()).hexdigest()
        self.seed = int(h[:8], 16) if seed is None else int(seed)
        self.rng = np.random.default_rng(self.seed)
        self.log = progress or (lambda *a: None)
        self.bank = Bank()
        self.ev = _events(cues)
        I = _intensity(cues, self.dur + 0.05)
        self.I = np.pad(I, (0, max(0, self.nc - len(I))), mode='edge')[:self.nc]
        self.Is = _smooth(self.I, int(3 * CR))        # smoothed intensity (slow layers)
        self.plan = plan(cues, self.dur, self.bank)
        self.keys = self.plan['keys']
        self.t_end = self.plan['t_end']
        self.bus = {k: Bus(self.n) for k in ('tracks', 'drones', 'pulse', 'melodic', 'strings_bed', 'strings_fx', 'show',
                                             'hits')}
        self.motif_count = 0
        self._ents = {}
        self.end_t1 = self.dur
        # control curves (dB), CR rate
        self.duck = np.zeros(self.nc)        # pre-hit cut (bed layers)
        self.gate = np.zeros(self.nc)        # silences (all)
        self.gate_hits = np.zeros(self.nc)
        self.reentry = np.zeros(self.nc)     # post-silence (bed layers, not melodic)
        self.swell = np.zeros(self.nc)       # 0..1 swell envelope (boosts bed)
        self.endfade = np.zeros(self.nc)     # end of film (all non-end layers)
        self.showduck = np.zeros(self.nc)    # the dark track bed steps back under the TV show / the Winks theme

    # ----------------------------------------------------------------------------------------- helpers
    def i_at(self, t, smooth=False):
        a = self.Is if smooth else self.I
        return float(a[int(np.clip(t * CR, 0, len(a) - 1))])

    def bed_db(self, t):
        """Nominal level (LUFS) of the bed at time t, before normalisation."""
        return REF_LUFS + SLOPE * (self.i_at(t, True) - 0.45)

    def g_at(self, t, rel):
        return float(db(self.bed_db(t) - NOM + rel))

    def curve_bed(self):
        tt = np.arange(self.nc) / CR
        return REF_LUFS + SLOPE * (self.Is[np.minimum((tt * CR).astype(int), len(self.Is) - 1)] - 0.45) - NOM

    def to_audio(self, cdb):
        """dB control curve -> linear per-sample gain (float32), computed in chunks to keep memory low."""
        g = np.empty(self.n, np.float32)
        xc = np.arange(len(cdb))
        step = 1 << 22
        for a in range(0, self.n, step):
            x = np.arange(a, min(self.n, a + step), dtype=np.float64) * (CR / SR)
            g[a:a + len(x)] = db(np.interp(x, xc, cdb))
        return g

    def _ctl(self, cdb, a, b):
        """dB control curve -> linear gain for samples a..b (float32)."""
        x = np.arange(a, b, dtype=np.float64) * (CR / SR)
        return db(np.interp(x, np.arange(len(cdb)), cdb)).astype(np.float32)

    def norm_to(self, sig, target):
        m = momentary_max(sig)
        return (sig * db(target - m)).astype(np.float32)

    def chain(self, key, semis, dur, skip=0.7, xf=1.3, rel=1.5, attack=True):
        """Sustained note of any length from one sample: crossfaded instances (attack skipped after the first)."""
        y = self.bank.shifted(key, semis)
        ln = len(y)
        n = int((dur + rel) * SR)
        out = np.zeros((n, 2), np.float32)
        tail = int(min(0.4 * SR, ln * 0.1))
        sk = int(min(skip * SR, ln * 0.25))
        body = ln - tail - sk - int(0.5 * SR)
        nx = int(max(0.05 * SR, min(xf * SR, body // 3)))
        pos, first = 0, True
        while pos < n:
            if first and attack:
                src0 = 0
            else:
                src0 = sk + int(self.rng.uniform(0, 0.5) * SR)
                src0 = int(np.clip(src0, 0, max(0, ln - tail - 3 * nx)))
            seg = min(ln - tail - src0, n - pos)
            if seg <= 0:
                break
            s = y[src0:src0 + seg].copy()
            k = min(nx, len(s) // 2)
            if not first:
                s[:k] *= _fade(k, 'in')[:, None]
            last = pos + seg >= n
            if not last:
                s[-k:] *= _fade(k, 'out')[:, None]
            out[pos:pos + len(s)] += s
            if last:
                break
            pos += max(seg - k, int(0.05 * SR))
            first = False
        r = min(int(rel * SR), n)
        out[-r:] *= _fade(r, 'out')[:, None]
        return out

    def vread(self, y, ratio):
        """Variable-rate read of y with per-output-sample pitch ratio (cubic Hermite)."""
        pos = np.concatenate([[0.0], np.cumsum(ratio[:-1])]) + 2
        pos = np.minimum(pos, len(y) - 3)
        i = pos.astype(np.int64)
        f = (pos - i)[:, None].astype(np.float32)
        y0, y1, y2, y3 = y[i - 1], y[i], y[i + 1], y[i + 2]
        c1 = 0.5 * (y2 - y0)
        c2 = y0 - 2.5 * y1 + 2 * y2 - 0.5 * y3
        c3 = 0.5 * (y3 - y0) + 1.5 * (y1 - y2)
        return (((c3 * f + c2) * f + c1) * f + y1).astype(np.float32)

    def ents(self, category, sub=''):
        k = (category, sub)
        if k not in self._ents:
            self._ents[k] = [e for e in L.entries(category=category) if sub in e['id']]
        return self._ents[k]

    def epi(self, serves, n=None, contains=None):
        out = [k for k, e in self.bank.epi_sfx.items() if serves in e['serves'] and (contains is None or contains in k)]
        return sorted(out)

    # ----------------------------------------------------------------------------------------- tracks
    def render_tracks(self):
        bus = self.bus['tracks']
        info = _track_info(self.bank)
        Ib = self.curve_bed()
        segs = self.plan['sections']
        for k, sg in enumerate(segs):
            y = _track_audio(self.bank, sg['slug'])
            v = info[sg['slug']]
            s0, s1, off = sg['s0'], sg['s1'], sg['off']
            # entry / exit windows
            if k == 0:
                a, fin = s0, 0.05
            elif sg.get('via_silence'):
                a, fin = sg['via_silence'][1] - 0.05, 0.1
            else:
                a, fin = s0 - 0.6, 2.6
            nxt = segs[k + 1] if k + 1 < len(segs) else None
            if nxt is None:
                b, fout = min(self.dur, self.t_end + 14), 3.0
            elif nxt.get('via_silence'):
                b, fout = nxt['via_silence'][0] + 0.15, 0.15
            else:
                b, fout = nxt['s0'] + 2.4, 3.0
            a = max(0.0, a)
            src_a = off + (a - s0)
            if src_a < 0:
                a, src_a = a - src_a, 0.0
            i0, i1 = int(src_a * SR), int((src_a + (b - a)) * SR)
            seg = y[i0:min(i1, len(y))].copy()
            if len(seg) < 2:
                continue
            if i1 > len(y):                           # material ran out: loop back with a long crossfade
                need = i1 - len(y)
                xf = int(4 * SR)
                st = max(0, len(y) - need - xf - int(30 * SR))
                ext = y[st:st + need + xf].copy()
                ext[:xf] *= _fade(xf, 'in')[:, None]
                seg[-xf:] *= _fade(xf, 'out')[:, None]
                seg = np.concatenate([seg[:-xf], seg[-xf:] + ext[:xf], ext[xf:]])
            nin, nout = min(int(fin * SR), len(seg)), min(int(fout * SR), len(seg))   # (a short last section in a window)
            seg[:nin] *= _fade(nin, 'in')[:, None]
            seg[-nout:] *= _fade(nout, 'out')[:, None]
            # gain automation: follow the intensity curve, partly flatten the track's own dynamics
            tt = a + np.arange(int((b - a) * CR) + 1) / CR
            tau = off + (tt - s0)
            l2 = np.asarray(v['L2']) - v['lufs']
            l2s = _smooth(l2, 2)
            li = np.interp(tau / 2.0, np.arange(len(l2s)), l2s)
            gc = Ib[np.minimum((tt * CR).astype(int), len(Ib) - 1)] - sg.get('flatten', FLATTEN) * li - 1.5 + \
                sg.get('gain_db', 0.0)
            gc = np.clip(gc, -30, 10)
            x = np.arange(len(seg)) * (CR / SR)
            g = db(np.interp(x, np.arange(len(gc)), gc)).astype(np.float32)
            bus.add(a, seg, g[:len(seg)])
            self.log(f'track {sg["slug"][:18]} film {s0:.0f}-{s1:.0f}s from {off:.0f}s')

    # ----------------------------------------------------------------------------------------- drones
    VOICES = [
        # name, bus, category, pc offset, register lo-hi, intensity threshold, width, rel dB, pan, reverb
        ('cb_root', 'drones', 'score/strings/contrabass_sustain', 0, (31, 42), -1.0, 0.25, -7.0, 0.15, 'recital'),
        ('vc_fifth', 'drones', 'score/strings/celli_sustain', 7, (43, 54), 0.25, 0.2, -10.0, 0.3, 'recital'),
        ('va_fifth', 'strings_bed', 'score/strings/violas_sustain', 7, (55, 66), 0.3, 0.2, -13.0, -0.25, 'hall'),
        ('va_rub', 'strings_bed', 'score/strings/violas_tremolo', 1, (58, 69), 0.52, 0.18, -15.0, -0.35, 'hall'),
        ('vc_trem', 'strings_bed', 'score/strings/celli_tremolo', 0, (48, 59), 0.6, 0.15, -13.0, 0.35, 'hall'),
        ('cb_trem', 'drones', 'score/strings/contrabass_tremolo', 0, (31, 42), 0.68, 0.15, -12.0, 0.1, 'recital'),
        ('vn_cluster', 'strings_bed', 'score/strings/violins_tremolo', 1, (72, 83), 0.78, 0.12, -21.0, -0.5, 'hall'),
        ('vn_root', 'strings_bed', 'score/strings/violins_tremolo', 0, (72, 83), 0.84, 0.12, -22.0, 0.5, 'hall'),
    ]

    def render_drones(self):
        tt = np.arange(self.nc) / CR
        Ib = self.curve_bed()
        Isw = np.clip(self.Is + 0.5 * self.swell, 0, 1)
        for name, busn, cat, pco, (lo, hi), th, w, rel, pan, rv in self.VOICES:
            act = np.ones(self.nc) if th < 0 else _sstep((Isw - th) / w)
            if act.max() < 0.02:
                continue
            vels = self.bank.vels(cat)
            vlo, vhi = (vels[0], vels[-1]) if vels else (None, None)
            dyn = np.clip(0.15 + 0.95 * Isw, 0, 1)
            gdb = Ib + rel - (5.0 if busn == 'drones' else 1.0) + act_db(act) + 3.0 * (dyn - 0.5)
            wl_db = 20 * np.log10(np.cos(dyn * np.pi / 2) + 1e-4)
            wh_db = 20 * np.log10(np.sin(dyn * np.pi / 2) + 1e-4)
            amt = 0.55 if busn == 'drones' else 0.75
            for (k0, k1, root, mode) in self.keys:      # one sustained chain per key region, mixed straight in
                if k0 >= self.t_end + 6:
                    break
                ia, ib = int(k0 * CR), int(min(k1, self.dur) * CR)
                if act[ia:ib + 1].max() < 0.02:
                    continue
                midi = _reg((root + pco) % 12, lo, hi)
                a = max(0.0, k0 - 1.5)
                d = min(k1, self.t_end + 6) - a + 1.5
                i0 = int(round(a * SR))
                layers = [vlo] if vhi == vlo else [vlo, vhi]
                cs = []
                for vel in layers:
                    e, sm = self.bank.note(cat, midi, vel, rr=int(self.rng.integers(0, 4)))
                    c = self.chain(e, sm, d, rel=1.5)
                    nin = int(1.5 * SR)
                    if k0 > 0:
                        c[:nin] *= _fade(nin, 'in')[:, None]
                    cs.append(c)
                m = min(min(len(c) for c in cs), self.n - i0)
                if m <= 0:
                    continue
                i1 = i0 + m
                if len(cs) == 2:
                    blk = cs[0][:m] * self._ctl(wl_db, i0, i1)[:, None]
                    blk += cs[1][:m] * self._ctl(wh_db, i0, i1)[:, None]
                else:
                    blk = cs[0][:m].copy()
                del cs
                blk *= self._ctl(gdb, i0, i1)[:, None]
                if 'violins' in cat:
                    blk = _filt(blk, 'lowpass', 4200)
                blk = _width(_pan(blk, pan * 0.6), 0.8)
                self.bus[busn].add(i0 / SR, blk, rev={rv: amt})
                del blk
        self.render_sub()

    def render_sub(self):
        """Synth sub drone on the key root (D1 / A1 / G1), slow beating, glides at key changes."""
        grid = np.arange(self.nc) / CR
        f = np.zeros(self.nc)
        for k0, k1, root, mode in self.keys:
            sel = (grid >= k0) & (grid < k1)
            f[sel] = 440 * 2 ** ((_reg(root, 26, 37) - 69) / 12)
        f[f == 0] = f[f > 0][-1] if np.any(f > 0) else 36.7
        f = _smooth(f, int(0.8 * CR))
        amp_db = self.curve_bed() - 14.0 + 4.0 * (self.Is - 0.5) + 3.0 * self.swell      # v2.1: -3 dB (sub-heavy)
        ph0 = 0.0
        step = 1 << 21
        sos = butter(4, 160, 'lowpass', fs=SR, output='sos')
        zi = np.zeros((sos.shape[0], 2))
        bus = self.bus['drones']
        for a in range(0, self.n, step):              # chunked straight into the bus (phase and filter carried)
            x = np.arange(a, min(self.n, a + step), dtype=np.float64) * (CR / SR)
            fa = np.interp(x, np.arange(self.nc), f)
            ph = ph0 + 2 * np.pi * np.cumsum(fa) / SR
            ph0 = float(ph[-1])                        # float64 phase: no wrap (the detuned partner is not 2pi-periodic)
            lfo = 1 + 0.12 * np.sin(2 * np.pi * 0.07 * x / CR + 1.3)
            v = np.sin(ph) + 0.8 * np.sin(ph * 1.0045 + 0.7) + 0.35 * np.sin(2 * ph + 0.3)
            v = np.tanh(1.4 * v * lfo) / np.tanh(1.4)
            v, zi = sosfilt(sos, v, zi=zi)
            v = (v * db(-14.0) * db(np.interp(x, np.arange(self.nc), amp_db))).astype(np.float32)  # raw synth ~ NOM+14
            bus.add(a / SR, np.stack([v, v * np.float32(0.98)], 1))

    # ----------------------------------------------------------------------------------------- pulse
    def render_pulse(self):
        bus = self.bus['pulse']
        ons = [e for e in self.ev if e['type'] in ('pulse_on', 'pulse_off')]
        spans, cur = [], None
        for e in ons:
            if e['type'] == 'pulse_on' and cur is None:
                cur = e
            elif e['type'] == 'pulse_off' and cur is not None:
                spans.append((cur['t'], e['t'], cur['level']))
                cur = None
        if cur is not None:
            spans.append((cur['t'], self.t_end, cur['level']))
        sils = [(e['t'], e['t'] + e['len']) for e in self.ev if e['type'] == 'silence']
        rr = 0
        for t0, t1, lv in spans:
            t, beat = t0, 0
            while t < t1:
                I = self.i_at(t)
                bpm = 54 + 56 * I
                bd = 60.0 / bpm
                if any(a - 0.05 <= t < b for a, b in sils):
                    t += bd
                    beat += 1
                    continue
                root, mode = _key_at(self.keys, t)
                ramp = min(1.0, (beat + 1) / 4.0) * min(1.0, max(0.0, (t1 - t) / 1.5))
                base = self.bed_db(t) - NOM - 15.0 + 6.0 * (lv - 0.7) + 20 * np.log10(max(ramp, 1e-3))
                hj = lambda: float(self.rng.normal(0, 0.008))
                vj = lambda: float(self.rng.normal(0, 1.2))
                cb = _reg(root, 31, 42)
                # lub
                y = self.bank.play('score/strings/contrabass_pizz', cb, 3 if I > 0.5 else 1, rr=rr)
                bus.add(t + hj(), y, db(base + vj()), pan=0.1, rev={'recital': 0.35})
                kd = self.bd_hit(int(2 + 3 * I), rr)
                bus.add(t + hj(), kd, db(base - 3 + vj()), rev={'recital': 0.3}, at=_onset(kd))
                # dub
                y2 = self.bank.play('score/strings/contrabass_pizz', cb, 1, rr=rr + 1)
                bus.add(t + 0.3 * bd + hj(), y2, db(base - 6 + vj()), pan=0.1, rev={'recital': 0.35})
                # subdivisions as tension rises
                if I > 0.5:
                    sub = 2 if I < 0.78 else 4
                    pat = [0, 0, 1, 0] if mode < 0 else [0, 0, 1, 0]
                    vc = _reg(root, 43, 54)
                    for j in range(sub):
                        tj = t + j * bd / sub
                        nn = vc + pat[(beat * sub + j) % 4]
                        yv = self.bank.play('score/strings/celli_spiccato', nn, 2 if j == 0 else 1, rr=rr + j)
                        bus.add(tj + hj(), yv, db(base - 8 + 7 * (I - 0.5) + vj() - (0 if j == 0 else 2.5)), pan=0.35,
                                rev={'recital': 0.4})
                    if I > 0.72:
                        va = _reg(root + 1, 55, 66)
                        for j in range(sub):
                            if (beat * sub + j) % 2:
                                continue
                            yv = self.bank.play('score/strings/violas_spiccato', va - (j % 4 == 2), 1, rr=rr + j)
                            bus.add(t + j * bd / sub + hj(), yv, db(base - 14 + vj()), pan=-0.35, rev={'hall': 0.5})
                rr += 1
                beat += 1
                t += bd

    def bd_hit(self, v, rr):
        v = int(np.clip(v, 1, 7))
        c = self.ents('score/percussion/bass_drum', f'newhit_v{v}_')
        return self.bank.get(c[rr % len(c)]) if c else np.zeros((10, 2), np.float32)

    # ----------------------------------------------------------------------------------------- melodic
    # motif in semitones relative to the root's octave (D5 = 0 at the root D): (beats, offset)
    PHRASE_A = [(1, -5), (1, 0), (1, 2), (2, 3), (1, 2), (1, 0), (1, -1), (1, 0), (3, -5)]
    PHRASE_B = [(1, -5), (1, 0), (1, 1), (2, 3), (1, 1), (1, 0), (1, -1), (1, -4), (2, -5), (1, -6)]
    BASS_A = [(0, -24), (3, -26), (6, -28), (9, -29)]   # harp lament bass under the lullaby: D3 C3 Bb2 A2
    BASS_B = BASS_A

    def _mode_map(self, off, mode):
        if mode > 0 and off % 12 in (3, 8, 10):     # major: m3, m6, m7 -> major degrees (b2, tritone stay)
            return off + 1
        return off

    def render_melodic(self):
        bus = self.bus['melodic']
        motifs = [e for e in self.ev if e['type'] == 'motif']
        busy = []
        for e in motifs:
            inst = e.get('inst') if e.get('inst') in ('musicbox', 'piano', 'octaves') else None
            t1 = self.motif(e, force_inst=inst)
            busy.append((e['t'] - 3, t1 + 2))
        # sparse low-piano lament between motifs (D C Bb A, then the A-Bb-A neighbour, the F-E-D fall, the Eb rub);
        # v2.1: about 3x denser (critic: 22 pitch changes / min vs 91-114 in the references), every third note
        # doubled by a low string (celli) so the line moves over the drone
        lament = [0, -2, -4, -5, -4, -5, 3, 2, 0, 1, 0, -2, -4, -5, -7, -5]
        t, k = 4.0, 0
        sils = [(e['t'] - 0.5, e['t'] + e['len'] + 0.3) for e in self.ev if e['type'] == 'silence']
        while t < self.t_end - 2:
            I = self.i_at(t, True)
            gap = (7.5 - 4.5 * I) / 2.8 + float(self.rng.uniform(-0.35, 0.35))
            if not any(a <= t < b for a, b in busy + sils):
                root, mode = _key_at(self.keys, t)
                off = lament[k % len(lament)]
                off = self._mode_map(off, mode)
                m = _reg(root, 33, 44) + off
                if m < 26:
                    m += 12
                gdb = self.bed_db(t) - NOM - 5.5 + 4 * (I - 0.5) + float(self.rng.normal(0, 1))
                y = self.bank.play('score/piano/grand_salamander', m, 4 if I < 0.5 else 8, dur=gap + 1.5, rel=1.2)
                bus.add(t, y, db(gdb), pan=-0.1, rev={'hall': 0.6, 'cavern': 0.15}, at=_onset(y))
                y2 = self.bank.play('score/piano/horror_soft', m, dur=gap + 1.5, rel=1.2)
                bus.add(t + 0.012, y2, db(gdb - 8), pan=0.15, rev={'hall': 0.6}, at=_onset(y2))
                if I > 0.6 and k % 2 == 0:           # octave below doubles at higher tension
                    y3 = self.bank.play('score/piano/horror_soft', m - 12, dur=gap + 1, rel=1.2)
                    bus.add(t, y3, db(gdb - 5), rev={'hall': 0.5}, at=_onset(y3))
                if k % 3 == 1:                       # low-string lament doubling
                    try:
                        y4 = self.bank.play('score/strings/celli_sustain', m + 12 if m + 12 <= 57 else m, dur=gap + 1.2, rel=0.8)
                        bus.add(t + 0.05, y4, db(gdb - 4), pan=0.25, rev={'hall': 0.6})
                    except Exception:
                        pass
                k += 1
            t += max(1.3, gap)

    def motif(self, e, wind_down=False, force_inst=None):
        bus = self.bus['melodic']
        t0, lv = e['t'], e['level']
        root, mode = _key_at(self.keys, t0)
        shift = ((root - 2 + 6) % 12) - 6
        I = self.i_at(t0, True)
        cnt = self.motif_count
        self.motif_count += 1
        nbars = int(math.ceil(e['len'] / 2.4)) if e.get('len') else (4 if cnt == 0 else 8)
        nbars = max(2, min(nbars, 16))
        inst = force_inst or ('musicbox' if I < 0.45 else ('piano' if I < 0.75 else 'octaves'))
        bpm = 76 if inst == 'musicbox' else 66
        beat = 60.0 / bpm
        notes, bass = [], []
        b0 = 0
        phr = 0
        while b0 < nbars * 3:
            wrong = (phr % 2 == 1) or (cnt >= 2 and I > 0.5)
            P, B = (self.PHRASE_B, self.BASS_B) if wrong else (self.PHRASE_A, self.BASS_A)
            bb = 0
            for bt, off in P:
                if b0 + bb >= nbars * 3:
                    break
                notes.append((b0 + bb, bt, self._mode_map(off, mode)))
                bb += bt
            for bt, off in B:
                if b0 + bt < nbars * 3:
                    bass.append((b0 + bt, self._mode_map(off, mode)))
            b0 += 12
            phr += 1
        total = nbars * 3

        def when(bb):
            if not wind_down:
                return t0 + bb * beat
            # music box winding down: beats stretch progressively over the second half
            u = np.linspace(0, bb, 64) / max(total, 1)
            sv = 1 + 1.2 * np.clip((u - 0.4) / 0.6, 0, 1) ** 2
            return t0 + beat * float(np.sum(0.5 * (sv[1:] + sv[:-1])) * (bb / 63.0))

        def droop(bb):
            return -0.45 * max(0.0, (bb / total - 0.55) / 0.45) ** 2 if wind_down else 0.0

        gbase = self.bed_db(t0) - NOM + 1.0 + (1.0 if inst == 'musicbox' else 0.0) + 6 * (lv - 0.7)
        for k, (bb, bt, off) in enumerate(notes):
            tt = when(bb) + float(self.rng.normal(0, 0.006))
            m = 74 + shift + off
            acc = 0.0 if bb % 3 == 0 else -2.0
            gj = float(self.rng.normal(0, 0.8))
            dn = droop(bb)
            if inst == 'musicbox':
                det = float(self.rng.choice([-0.06, 0.0, 0.06])) + round(dn, 2)
                e1, s1 = self.bank.note('score/mallets/celesta', m, rr=k)
                y = self.bank.shifted(e1, s1 + det)
                bus.add(tt, y, db(gbase + acc + gj), pan=-0.2, rev={'hall': 0.8, 'cavern': 0.35}, at=_onset(y))
                if m + 12 <= 108:
                    try:
                        e2, s2 = self.bank.note('score/mallets/glockenspiel', m + 12, rr=k)
                        y2 = self.bank.shifted(e2, s2 + det + 0.08)
                        bus.add(tt + 0.004, _filt(y2, 'lowpass', 7000), db(gbase - 15 + acc), pan=0.3,
                                rev={'cavern': 0.4}, at=_onset(y2))
                    except KeyError:
                        pass
            else:
                pm = m - 12
                y = self.bank.play('score/piano/horror_soft', pm, dur=bt * beat * 1.6, rel=0.9)
                bus.add(tt, y, db(gbase + acc + gj - 1), pan=-0.1, rev={'hall': 0.7, 'cavern': 0.2}, at=_onset(y))
                e1, s1 = self.bank.note('score/mallets/celesta', m, rr=k)
                yc = self.bank.shifted(e1, s1 + dn)
                bus.add(tt + 0.01, yc, db(gbase + acc - 9), pan=0.25, rev={'cavern': 0.5}, at=_onset(yc))
                if inst == 'octaves':
                    y3 = self.bank.play('score/piano/horror_alt', pm - 12, dur=bt * beat * 1.6, rel=0.9)
                    bus.add(tt, y3, db(gbase + acc - 3), pan=0.1, rev={'hall': 0.6}, at=_onset(y3))
                    # the strings double the line, dark and low
                    yv = self.bank.play('score/strings/celli_sustain', pm - 12 if pm - 12 >= 36 else pm, 1,
                                        dur=bt * beat, rel=0.6)
                    self.bus['strings_bed'].add(tt, yv, db(gbase - 10), pan=0.3, rev={'hall': 0.6})
        for bb, off in bass:
            tt = when(bb)
            m = 74 + shift + off
            while m < 40:
                m += 12
            y = self.bank.play('score/harp', m, dur=3 * beat * 1.8, rel=1.0)
            bus.add(tt, y, db(gbase - 7), pan=0.15, rev={'hall': 0.7}, at=_onset(y))
        return when(total)

    # ----------------------------------------------------------------------------------------- strings fx
    def render_swell(self, e):
        bus = self.bus['strings_fx']
        t0, ln, lv = e['t'], max(2.0, e['len']), e['level']
        root, mode = _key_at(self.keys, t0 + ln)
        n = int((ln + 2.5) * SR)
        x = np.arange(n) / SR
        u = np.clip(x / ln, 0, 1)
        env_db = -26 + 26 * u ** 1.6                    # crescendo
        env_db = np.where(x > ln, -60 * np.clip((x - ln) / 2.5, 0, 1) ** 0.7, env_db)
        env = db(env_db).astype(np.float32)
        wh = np.sin(np.clip(u * 1.2, 0, 1) * np.pi / 2).astype(np.float32)
        wl = np.cos(np.clip(u * 1.2, 0, 1) * np.pi / 2).astype(np.float32)
        voices = [('score/strings/celli_tremolo', 0, (48, 59), 0.3),
                  ('score/strings/violas_tremolo', 1, (58, 69), -0.3),
                  ('score/strings/contrabass_tremolo', 0, (31, 42), 0.1)]
        if lv > 0.6:
            voices.append(('score/strings/violins_tremolo', 1, (70, 81), -0.5))
            voices.append(('score/strings/violas_tremolo', 7, (55, 66), 0.45))
        sig = np.zeros((n, 2), np.float32)
        for cat, pco, (lo, hi), pan in voices:
            m = _reg((root + pco) % 12, lo, hi)
            vels = self.bank.vels(cat)
            a = self.chain(*self.bank.note(cat, m, vels[0] if vels else None), ln + 1.0, rel=1.0, attack=True)
            b = self.chain(*self.bank.note(cat, m, vels[-1] if vels else None), ln + 1.0, rel=1.0, attack=True)
            k = min(len(a), len(b), n)
            v = a[:k] * wl[:k, None] + b[:k] * wh[:k, None]
            g = -9.0 if 'violins' in cat else 0.0
            sig[:k] += _pan(v, pan) * np.float32(db(g))
        sig *= env[:, None]
        sig = _filt(sig, 'lowpass', 5000)
        peak_t = t0 + ln
        target = self.bed_db(peak_t) + 2 + 6 * lv
        st = short_term(sig, 0.25).max()
        sig *= np.float32(db(target - st))
        bus.add(t0, sig, rev={'hall': 0.7})
        if lv > 0.55:                                    # timpani roll underneath
            self.roll(peak_t, ln * 0.8, root, target - 8)
        # the whole bed breathes with the swell
        i0, i1 = int(t0 * CR), int((t0 + ln + 2.5) * CR)
        uu = np.clip((np.arange(i0, i1) / CR - t0) / ln, 0, None)
        sw = np.where(uu <= 1, uu ** 2, np.clip(1 - (uu - 1) * ln / 2.5, 0, 1)) * (0.5 + 0.5 * lv)
        i1 = min(i1, self.nc)
        self.swell[i0:i1] = np.maximum(self.swell[i0:i1], sw[:i1 - i0])

    def roll(self, t_end, ln, root, target):
        c = self.ents('score/percussion/timpani', 'roll')
        e = c[int(self.rng.integers(0, len(c)))]
        semis = float(np.clip(_reg(root, 36, 47) - 41.45, -4, 4))
        y = self.bank.shifted(e, semis)
        n = min(len(y), int(ln * SR))
        y = y[:n].copy()
        y *= db(-24 + 24 * np.linspace(0, 1, n) ** 1.5).astype(np.float32)[:, None]
        y[-int(0.03 * SR):] *= _fade(int(0.03 * SR), 'out')[:, None]
        y = self.norm_to(y, target)
        self.bus['hits'].add(t_end, y, rev={'hall': 0.4}, at=len(y))

    def render_riser(self, e):
        t1, ln, lv = e['t'], max(1.5, e['len']), e['level']
        if any(x['type'] in ('hit', 'stinger', 'braam', 'rule') and -0.1 <= x['t'] - t1 <= 0.15 for x in self.ev):
            t1 -= 0.16 + 0.1 * lv          # riser -> breath -> hit: the hit lands in a small vacuum
        root, mode = _key_at(self.keys, t1)
        n = int(ln * SR)
        x = np.arange(n) / n
        target = self.bed_db(t1) + 2 + 7 * lv
        # 1) string glissando cluster (strings stem)
        sig = np.zeros((n, 2), np.float32)
        voices = [('score/strings/celli_tremolo', 0, (45, 56), 7, 0.35), ('score/strings/violas_tremolo', 1, (55, 66), 9, -0.3),
                  ('score/strings/violins_tremolo', 6, (64, 75), 10, 0.5)]
        if lv > 0.6:
            voices.append(('score/strings/contrabass_tremolo', 0, (31, 42), 5, 0.0))
        for cat, pco, (lo, hi), rise, pan in voices:
            m = _reg((root + pco) % 12, lo, hi)
            vels = self.bank.vels(cat)
            ent, s = self.bank.note(cat, m, vels[-1] if vels else None)
            src = self.chain(ent, s, ln * 2.2 + 1, rel=0.5)
            semis = rise * x ** 2.2
            y = self.vread(src, (2 ** (semis / 12)).astype(np.float64))[:n]
            sig[:len(y)] += _pan(y, pan) * np.float32(db(-6 if 'violins' in cat else 0))
        env = db(-30 + 30 * x ** 1.4).astype(np.float32)
        sig *= env[:, None]
        sig[-int(0.025 * SR):] *= _fade(int(0.025 * SR), 'out')[:, None]
        sig = _filt(sig, 'lowpass', 6000)
        sig = self.norm_to(sig, target - 2)
        self.bus['strings_fx'].add(t1, sig, rev={'hall': 0.5}, at=n)
        # 2) reversed cymbal / suspended-cymbal crescendo + Epidemic riser + timpani roll (hits stem)
        hs = np.zeros((n, 2), np.float32)
        cy = self.ents('score/percussion/cymbals', 'crash1_ff')
        if cy:
            yc = self.bank.get(cy[int(self.rng.integers(0, len(cy)))])[::-1]
            yc = _filt(yc, 'lowpass', 6500)
            k = min(n, len(yc))
            hs[n - k:] += yc[len(yc) - k:] * np.float32(db(-3))
        rs = self.epi('riser')
        if rs:
            yr = self.bank.get('epi:' + rs[e['i'] % len(rs)])
            pk = _peak_time(yr)
            a = max(0, pk - n)
            seg = yr[a:pk]
            fi = min(len(seg), int(0.5 * SR))
            seg = seg.copy()
            seg[:fi] *= _fade(fi, 'in')[:, None]
            hs[n - len(seg):] += seg * np.float32(db(-1 if lv > 0.5 else -5))
        hs[-int(0.02 * SR):] *= _fade(int(0.02 * SR), 'out')[:, None]
        hs = self.norm_to(hs, target - 2)
        self.bus['hits'].add(t1, _limit(hs), rev={'hall': 0.35}, at=n)
        if lv > 0.5:
            self.roll(t1, ln, root, target - 6)

    # ----------------------------------------------------------------------------------------- the show / Winks
    def _wow_ratio(self, n, depth, hz, fl_depth, fl_hz):
        t = np.arange(n) / SR
        return (1 + depth * np.sin(2 * np.pi * hz * t + float(self.rng.uniform(0, 6))) +
                fl_depth * np.sin(2 * np.pi * fl_hz * t + float(self.rng.uniform(0, 6)))).astype(np.float64)

    def _read(self, y, i0, ratio):
        """Variable-rate read of y from sample i0 (loops the tune if it runs out)."""
        need = int(i0 + ratio.sum() + 16)
        src = y[i0:need + 4]
        while len(src) < need - i0 + 4:
            src = np.concatenate([src, y[int(5 * SR):]])
        return self.vread(src, ratio)

    def _speaker(self, x, space):
        """The playback chain: 'tv' (the old console TV across the living room), 'far' (the TV in the next room),
        'tape' (the 1974 tape's own sound, full-frame), 'old' (the 1962 kinescope), 'clean' (no processing)."""
        if space == 'clean':
            return x
        m = x.mean(1)
        if space == 'old':
            m = _filt(_filt(m, 'highpass', 300, 4), 'lowpass', 3200, 4)
            m = np.tanh(2.0 * m / (np.abs(m).max() + 1e-9)) * (np.abs(m).max() + 1e-9)
            ck = (self.rng.uniform(size=len(m)) < 3.0 / SR).astype(np.float32) * self.rng.uniform(-1, 1, len(m)).astype(np.float32)
            m = m + _filt(ck, 'highpass', 1500, 2) * np.float32(np.abs(m).max() * 0.25)
        elif space == 'tape':
            m = _filt(_filt(m, 'highpass', 110, 2), 'lowpass', 7000, 4)
            m = np.tanh(1.25 * m / (np.abs(m).max() + 1e-9)) * (np.abs(m).max() + 1e-9)
        else:
            m = _filt(_filt(m, 'highpass', 200, 4), 'lowpass', 4500 if space == 'tv' else 2300, 4)
            m = _peq(_peq(m, 1500, 3.0, 1.0), 330, 2.5, 2.0)
            pk = np.abs(m).max() + 1e-9
            m = np.tanh(1.5 * m / pk) / np.tanh(1.5) * pk
            sl = np.zeros_like(m)
            for d, g in ((0.006, 0.16), (0.013, 0.1), (0.024, 0.05)):
                k = int(d * SR); sl[k:] += m[:-k] * g
            m = m + _filt(sl, 'lowpass', 3000, 2)
        pk = float(np.abs(m).max()) + 1e-9
        t = np.arange(len(m)) / SR
        hiss = _filt(self.rng.standard_normal(len(m)).astype(np.float32), 'bandpass', [1800, 8000], 2) * pk * 0.012
        hum = (np.sin(2 * np.pi * 60 * t) + 0.4 * np.sin(2 * np.pi * 180 * t)).astype(np.float32) * pk * \
            (0.012 if space == 'old' else 0.005)
        return _st((m + hiss + hum).astype(np.float32))

    def _envelope(self, n, fin, fout, stop):
        env = np.ones(n, np.float32)
        a = min(n, max(1, int(fin * SR)))
        env[:a] = np.sin(np.linspace(0, np.pi / 2, a)) ** 2
        b = min(n, max(1, int((0.025 if stop == 'cut' else fout) * SR)))
        env[-b:] *= np.cos(np.linspace(0, np.pi / 2, b)) ** 2
        return env

    def render_show(self, e):
        """The show on the TV (see the module docstring). Event keys: len, level, slug, shift (semitones), off (s in
        the original track), space ('tv' | 'far' | 'tape' | 'old' | 'clean'), warp (0..1: the tape sags up to 9
        semitones), warp_at (s after t where the sag starts, default len * 0.5), stop ('fade' | 'cut' | 'drag'),
        fade (fade-in s, default 0.25)."""
        t, ln, lv = e['t'], max(0.5, float(e.get('len') or 10.0)), e['level']
        slug = e.get('slug') if e.get('slug') in self.bank.epi_music else SHOW_THEME
        if slug not in self.bank.epi_music:
            print(f'[score] WARNING: show tune {slug!r} not in the catalogue: skipped', flush=True); return
        shift, off0 = VINTAGE.get(slug, (-2.0, 1.0))
        shift = float(e.get('shift', shift)); off = float(e.get('off', off0))
        space = str(e.get('space') or 'tv'); stop = str(e.get('stop') or 'fade')
        y = _vintage_audio(self.bank, slug, shift)
        r = 2 ** (shift / 12.0)
        n = int(ln * SR)
        ratio = self._wow_ratio(n, 0.0025, 0.5, 0.0007, 6.2) if space != 'clean' else np.ones(n)
        warp = float(np.clip(e.get('warp', 0.0) or 0.0, 0, 1))
        if warp > 0:
            wa = float(e.get('warp_at', ln * 0.5))
            u = np.clip((np.arange(n) / SR - wa) / max(0.3, ln - wa), 0, 1) ** 1.5
            ratio *= 2 ** (-9.0 * warp * u / 12.0)
        if space == 'old':
            ratio *= self._wow_ratio(n, 0.004, 0.8, 0.0015, 9.0)
        if stop == 'drag':                                   # the tape winds down to a halt
            k = min(n, int(0.9 * SR))
            ratio[-k:] *= np.linspace(1.0, 0.04, k) ** 1.5
        x = self._read(y, int(off / r * SR), ratio)[:n]
        x = self._speaker(x, space)
        x *= self._envelope(len(x), float(e.get('fade', 0.25)), 1.5, stop)[:, None]
        st = short_term(x, 0.25).max() if len(x) > 3 * SR else momentary_max(x)
        target = REF_LUFS + (4.0 if space in ('tv', 'tape', 'old', 'clean') else -2.0) + 8.0 * (lv - 0.5)
        x *= np.float32(db(target - st))
        rev = {'recital': 0.12} if space in ('tv', 'tape', 'clean') else ({'hall': 0.45} if space == 'far' else {'recital': 0.2})
        self.bus['show'].add(t, x, rev=rev)
        self._duck_span(t, t + len(x) / SR, SHOW_DUCK['show'] * (0.5 if space == 'far' else 1.0))
        self.log(f'show {slug[:18]} {space} {t:.1f}-{t + ln:.1f}s warp {warp} stop {stop}')

    def render_winks(self, e):
        """Mister Winks's theme: the show theme rotting (see the module docstring). Event keys: len, level, slug, shift
        (default -9), off (s in the original track), depth (0..1, the wow, default 1), stop ('fade' | 'cut' | 'drag')."""
        t, ln, lv = e['t'], max(0.5, float(e.get('len') or 8.0)), e['level']
        slug = e.get('slug') if e.get('slug') in self.bank.epi_music else SHOW_THEME
        if slug not in self.bank.epi_music:
            print(f'[score] WARNING: winks tune {slug!r} not in the catalogue: skipped', flush=True); return
        shift = float(e.get('shift', WINKS_SHIFT)); off = float(e.get('off', WINKS_OFF))
        depth = float(np.clip(e.get('depth', 1.0), 0, 1.5)); stop = str(e.get('stop') or 'fade')
        y = _vintage_audio(self.bank, slug, shift)
        r = 2 ** (shift / 12.0)
        n = int(ln * SR)
        ratio = self._wow_ratio(n, 0.02 * depth, 0.22, 0.004 * depth, 4.5)
        if stop == 'drag':
            k = min(n, int(1.2 * SR))
            ratio[-k:] *= np.linspace(1.0, 0.05, k) ** 1.5
        i0 = int(off / r * SR)
        a = self._read(y, i0, ratio)[:n]
        b = self._read(y, i0, ratio * 2 ** (0.15 / 12))[:n]
        k = int(0.03 * SR)
        x = _pan(a, -0.3) + np.concatenate([np.zeros((k, 2), np.float32), _pan(b, 0.35)[:-k]]) * np.float32(0.6)
        x = _filt(_filt(x, 'highpass', 100, 2), 'lowpass', 2800, 2)
        pk = np.abs(x).max() + 1e-9
        x = (np.tanh(1.2 * x / pk) / np.tanh(1.2) * pk).astype(np.float32)
        x *= self._envelope(len(x), float(e.get('fade', 1.2)), 1.8, stop)[:, None]
        st = short_term(x, 0.25).max() if len(x) > 3 * SR else momentary_max(x)
        x *= np.float32(db(REF_LUFS + 2.0 + 8.0 * (lv - 0.5) - st))
        self.bus['show'].add(t, x, rev={'hall': 0.6, 'cavern': 0.4})
        self._duck_span(t, t + len(x) / SR, SHOW_DUCK['winks'])
        self.log(f'winks {t:.1f}-{t + ln:.1f}s depth {depth} stop {stop}')

    def _duck_span(self, a, b, depth):
        tt = np.arange(self.nc) / CR
        d = np.interp(tt, [a - 0.6, a + 0.4, b - 0.4, b + 1.2], [0, depth, depth, 0], left=0, right=0)
        self.showduck = np.minimum(self.showduck, d)

    # ----------------------------------------------------------------------------------------- hits
    def _timp(self, root, lv, rr):
        v = 1 if lv < 0.3 else 3
        c = self.ents('score/percussion/timpani', f'timpani1_hit_v{v}')
        e = c[rr % len(c)]
        return self.bank.shifted(e, float(np.clip(_reg(root, 36, 47) - 41.45, -4, 4)))

    def _layer(self, parts, n=None):
        """parts: list of (sig, gain_db, pan, delay_s). All onsets aligned (onset of each part at delay)."""
        ln = max(len(p[0]) - _onset(p[0]) + int(p[3] * SR) for p in parts)
        out = np.zeros((ln, 2), np.float32)
        for sig, g, pan, dl in parts:
            o = _onset(sig)
            s = sig[o:]
            i0 = int(dl * SR)
            out[i0:i0 + len(s)] += _pan(s, pan) * np.float32(db(g))
        return out

    def sub_boom(self, root, dur=1.6, drop=12):
        n = int(dur * SR)
        x = np.arange(n) / SR
        f0 = 440 * 2 ** ((_reg(root, 26, 37) + 12 - 69) / 12)
        f = f0 * 2 ** (-(drop / 12) * (1 - np.exp(-x / 0.18)))
        ph = 2 * np.pi * np.cumsum(f) / SR
        env = (1 - np.exp(-x / 0.004)) * np.exp(-x / (dur / 3.2))
        y = np.tanh(1.6 * np.sin(ph)) * env
        return _st(y.astype(np.float32) * np.float32(0.1))

    def render_hit(self, e, kind='hit'):
        t, lv = e['t'], e['level']
        root, mode = _key_at(self.keys, t)
        rr = e['i']
        parts = []
        parts.append((self._timp(root, lv, rr), 0.0, 0.05, 0.0))
        parts.append((self.bd_hit(int(2 + 5 * lv), rr), -2.0, -0.05, 0.0))
        if lv >= 0.3:
            parts.append((self.sub_boom(root, 1.2 + 1.6 * lv), -4.0 + 3 * lv, 0.0, 0.0))
        pm = _reg(root, 21, 32)
        cl = [0, 1] if lv < 0.6 else [0, 1, 6]
        for j, o in enumerate(cl):
            y = self.bank.play('score/piano/horror_loud' if lv > 0.5 else 'score/piano/horror_alt', pm + o + 12 * (j == 2),
                               dur=2.5, rel=1.0)
            parts.append((y, -3.0 - 2 * j, 0.15 * (j - 1), 0.004 * j))
        if lv >= 0.45:
            imp = self.epi('impact_hit')
            if imp:
                parts.append((self.bank.get('epi:' + imp[rr % len(imp)]), -2.0 + 2 * lv, 0.0, 0.0))
        if lv >= 0.7:
            g = 'f' if lv < 0.85 else 'fff'
            gg = [x for x in self.ents('score/percussion/gong_tamtam') if x['id'].endswith('gonghit_' + g)]
            if gg:
                y = self.bank.get(gg[0])[: int(9 * SR)].copy()
                y[-int(3 * SR):] *= _fade(int(3 * SR), 'out')[:, None]
                parts.append((y, -8.0 + 4 * lv, 0.25, 0.0))
        if lv >= 0.85:
            cy = self.ents('score/percussion/cymbals', 'suscymb1_hit_f_')
            if cy:
                parts.append((_filt(self.bank.get(cy[rr % len(cy)]), 'lowpass', 7000), -14.0, -0.3, 0.0))
        if kind == 'stinger':
            parts.extend(self._stab(root, lv, rr))
            st = self.epi('stinger')
            if st:
                parts.append((self.bank.get('epi:' + st[(rr + 1) % len(st)]), 0.0, 0.0, 0.0))
        y = self._decay(_width(self._layer(parts), 0.75), 1.5 + 1.3 * lv, hold=0.1)
        target = REF_LUFS + 2 + 9 * lv          # v2.1: was +5 + 13 * lv (hits masked the reveal lines)
        y = self.norm_to(y, target)
        self.bus['hits'].add(t, _limit(y), rev={'hall': 0.45, 'cavern': 0.12 * lv})
        self.pre_duck(t, lv)

    def _decay(self, y, t60, hold=0.25):
        """Shape a layered hit to the reference decay (T60 2-3 s): hold the attack, then exponential decay."""
        x = np.arange(len(y)) / SR
        env = np.exp(-6.91 * np.maximum(0.0, x - hold) / t60).astype(np.float32)
        n = int(min(len(y), (hold + t60 * 1.2) * SR))
        return (y[:n] * env[:n, None]).astype(np.float32)

    def _stab(self, root, lv, rr):
        """Stinger string stab: high cluster on root, b2 and the tritone, short and accented (strings stem)."""
        sig = []
        for cat, pco, (lo, hi), pan in [('score/strings/violins_sustain', 1, (74, 85), -0.4),
                                         ('score/strings/violins_sustain', 0, (74, 85), 0.4),
                                         ('score/strings/violas_sustain', 6, (60, 71), -0.2),
                                         ('score/strings/celli_sustain', 0, (48, 59), 0.3)]:
            m = _reg((root + pco) % 12, lo, hi)
            vels = self.bank.vels(cat)
            y = self.bank.play(cat, m, vels[-1] if vels else None, dur=1.1, rel=0.7)
            sig.append((y, -6.0 if 'violins' in cat else -3.0, pan, 0.0))
        y = self._layer(sig)
        env = np.ones(len(y), np.float32)
        a = int(0.012 * SR)
        env[:a] = np.linspace(0, 1, a)
        y *= env[:, None]
        return [(y, -1.0, 0.0, 0.0)]

    def render_braam(self, e):
        t, lv, ln = e['t'], e['level'], max(1.5, e['len'])
        root, mode = _key_at(self.keys, t)
        hold = ln
        parts = []
        brass = [('score/brass/tuba_sustain', 0, (31, 42), 0.0, 0.0),
                 ('score/brass/trombone_sustain', 0, (43, 54), -2.0, -0.25),
                 ('score/brass/horn_sustain', 0, (50, 61), -5.0, 0.3),
                 ('score/strings/contrabass_sustain', 0, (31, 42), -3.0, 0.1),
                 ('score/strings/celli_sustain', 0, (43, 54), -4.0, 0.25)]
        if lv > 0.55:
            brass.append(('score/brass/horn_sustain', 1, (50, 61), -7.0, -0.3))
            brass.append(('score/brass/trombone_sustain', 6, (43, 54), -9.0, 0.35))
        n = int((hold + 2.0) * SR)
        sig = np.zeros((n, 2), np.float32)
        for cat, pco, (lo, hi), g, pan in brass:
            m = _reg((root + pco) % 12, lo, hi)
            vels = self.bank.vels(cat)
            ent, s = self.bank.note(cat, m, vels[-1] if vels else None)
            y = self.chain(ent, s, hold, rel=1.6)[:n]
            sig[:len(y)] += _pan(y, pan) * np.float32(db(g))
        # war tuba blat on the attack
        wt = self.bank.cat('score/brass/war_tuba')
        if wt:
            ent, s = self.bank.note('score/brass/war_tuba', _reg(root, 31, 42), 4, rr=e['i'])
            y = self.bank.shifted(ent, s)
            sig[:min(n, len(y))] += y[:n] * np.float32(db(-2))
        x = np.arange(n) / SR
        env = np.minimum(1, x / 0.06) * db(np.where(x < hold, 2.5 * np.sin(np.pi * np.clip(x / hold, 0, 1)), 0))
        sig *= env.astype(np.float32)[:, None]
        drive = 1.5 + 2.5 * lv
        sig = np.tanh(drive * sig / (np.abs(sig).max() + 1e-9)) / np.tanh(drive)
        sig = self.norm_to(_filt(sig.astype(np.float32), 'lowpass', 2800, 2), NOM + 6)
        br = self.epi('braam')
        pick = [b for b in br if b.endswith('_d')] if root == 2 else []
        bsrc = pick[0] if pick else (br[e['i'] % len(br)] if br else None)
        layers = [(sig, 0.0, 0.0, 0.0), (self.sub_boom(root, hold + 1, drop=5), -3.0, 0.0, 0.0),
                  (self._timp(root, lv, e['i']), -3.0, 0.0, 0.0)]
        if bsrc:
            ye = self.bank.get('epi:' + bsrc)
            layers.append((ye, -2.0, 0.0, 0.0))
        y = self._decay(_width(self._layer(layers), 0.75), hold + 2.5, hold=hold * 0.6)
        y = self.norm_to(y, REF_LUFS + 0 + 9 * lv)
        self.bus['hits'].add(t, _limit(y), rev={'hall': 0.4, 'cavern': 0.15})
        self.pre_duck(t, lv)

    def render_subdrop(self, e):
        t, lv = e['t'], e['level']
        root, mode = _key_at(self.keys, t)
        parts = [(self.sub_boom(root, 2.6 + 1.5 * lv, drop=19), 0.0, 0.0, 0.0)]
        sd = self.epi('sub_drop')
        if sd:
            parts.append((self.bank.get('epi:' + sd[e['i'] % len(sd)]), -3.0, 0.0, 0.0))
        y = self._layer(parts)
        y = self.norm_to(y, REF_LUFS - 1 + 9 * lv)
        self.bus['hits'].add(t, _limit(y), rev={'hall': 0.15})
        if lv > 0.6:
            self.pre_duck(t, lv * 0.7)

    def render_rule(self, e):
        """The rule-card sting (same signature every card): reversed piano swell into a low boom + piano octave,
        a music-box bell (motif head note) and a soft tam-tam, into a long dark space."""
        t, lv = e['t'], e['level']
        root, mode = _key_at(self.keys, t + 0.5)
        rr = sum(1 for x in self.ev if x['type'] == 'rule' and x['t'] < t)
        # reversed piano swell (melodic stem)
        rv = self.bank.play('score/piano/grand_salamander', _reg(root, 50, 61), 8)
        rv = rv[: int(1.1 * SR)][::-1].copy()
        fi = int(0.5 * SR)
        rv[:fi] *= _fade(fi, 'in')[:, None]
        rv = self.norm_to(rv, REF_LUFS + 2 + 6 * lv)
        self.bus['melodic'].add(t, rv, rev={'hall': 0.6}, at=len(rv))
        parts = [(self._timp(root, 0.5, rr), 0.0, 0.0, 0.0), (self.bd_hit(5, rr), -4.0, 0.0, 0.0),
                 (self.sub_boom(root, 2.0, drop=7), -3.0, 0.0, 0.0)]
        pm = _reg(root, 26, 37)
        for o, g in ((0, -1.0), (12, -3.0)):
            parts.append((self.bank.play('score/piano/horror_alt', pm + o, dur=3.0, rel=1.5), g, 0.0, 0.0))
        gg = [x for x in self.ents('score/percussion/gong_tamtam') if x['id'].endswith('gonghit_p')]
        if gg:
            y = self.bank.get(gg[0])[: int(8 * SR)].copy()
            y[-int(3 * SR):] *= _fade(int(3 * SR), 'out')[:, None]
            parts.append((y, -6.0, 0.2, 0.0))
        y = self._decay(_width(self._layer(parts), 0.75), 2.2, hold=0.15)
        y = self.norm_to(y, REF_LUFS + 1 + 9 * lv)
        self.bus['hits'].add(t, _limit(y), rev={'hall': 0.35, 'cavern': 0.3})
        # music-box bell: the motif's head note (fifth below then root), octave up
        shift = ((root - 2 + 6) % 12) - 6
        for k, (dt, off) in enumerate(((0.0, 12), (0.42, 7))):
            m = 74 + shift + off
            try:
                e1, s1 = self.bank.note('score/mallets/celesta', m, rr=rr)
                yb = self.bank.shifted(e1, s1)
                self.bus['melodic'].add(t + dt, yb, db(self.bed_db(t) - NOM + 0 + 3 * lv - 3 * k),
                                        pan=-0.25 + 0.5 * k, rev={'cavern': 0.7, 'hall': 0.4}, at=_onset(yb))
            except KeyError:
                pass
        self.pre_duck(t, lv * 0.8)

    def render_end(self, e):
        t, ln, lv = e['t'], max(4.0, e['len']), e['level']
        root, mode = _key_at(self.keys, t)
        mode = mode if root == 2 else -1
        root = 2                                      # the ending always comes home to D (A or G -> D)
        self.keys = [k for k in self.keys if k[0] < t] + [[t, self.dur + 30, 2, mode]]
        for k in self.keys[:-1]:
            k[1] = min(k[1], t)
        # final chord: contrabass root, celli root + fifth, violas m3 (resolution), pp swelling then away
        chord = [('score/strings/contrabass_sustain', 0, (31, 42), 0.1), ('score/strings/celli_sustain', 0, (43, 54), 0.3),
                 ('score/strings/celli_sustain', 7, (50, 61), -0.2), ('score/strings/violas_sustain', 3 if mode < 0 else 4,
                                                                      (60, 71), -0.35)]
        n = int((ln + 3) * SR)
        x = np.arange(n) / SR
        env = db(np.interp(x, [0, 0.35 * ln, 0.7 * ln, ln, ln + 3], [-14, 0, -3, -18, -70])).astype(np.float32)
        sig = np.zeros((n, 2), np.float32)
        for cat, pco, (lo, hi), pan in chord:
            m = _reg((root + pco) % 12, lo, hi)
            vels = self.bank.vels(cat)
            y = self.chain(*self.bank.note(cat, m, vels[0] if vels else None), ln, rel=2.5)[:n]
            sig[:len(y)] += _pan(y, pan)
        sig *= env[:, None]
        sig = self.norm_to(sig, self.bed_db(t) + 2)
        self.bus['strings_fx'].add(t, sig, rev={'hall': 0.8, 'cavern': 0.2})
        # music box winds down over the chord
        t_mb = self.motif(dict(t=t + 1.0, level=0.6, len=min(ln - 2, 9.6), i=e['i']), wind_down=True,
                          force_inst='musicbox')
        # ... and one high b2 that does not resolve (solo violin, ppp), left hanging after everything
        m = _reg((root + 1) % 12, 82, 93)
        y = self.chain(*self.bank.note('score/strings/solo_violin_sustain', m), 5.0, rel=3.0)
        y *= db(np.interp(np.arange(len(y)) / SR, [0, 2.5, 5, 8], [-30, 0, -4, -60])).astype(np.float32)[:, None]
        y = _filt(y, 'lowpass', 5500)
        y = self.norm_to(y, self.bed_db(t) - 6)
        self.bus['strings_fx'].add(min(t_mb, t + ln - 3), y, pan=0.3, rev={'cavern': 0.8})
        if lv >= 0.5:
            y = self._layer([(self.sub_boom(root, 3.0, drop=9), 0.0, 0.0, 0.0), (self._timp(root, 0.4, 0), -4, 0, 0)])
            self.bus['hits'].add(t, self.norm_to(y, REF_LUFS + 2 + 8 * lv), rev={'cavern': 0.3})
        self.end_t1 = t + ln + 9

    # ----------------------------------------------------------------------------------------- automation
    def pre_duck(self, t, lv):
        """Cut the bed just before a hit (>= 15 dB contrast), then let it recover under the tail."""
        if lv < 0.3:
            return
        depth = -(6 + 10 * lv)
        tt = np.arange(self.nc) / CR
        lead = 0.35 + 0.65 * lv                        # bigger hits get a longer suck-out before them
        d = np.interp(tt, [t - lead - 0.3, t - lead, t + 0.05, t + 2.2], [0, depth, depth, 0], left=0, right=0)
        self.duck = np.minimum(self.duck, d)

    def automation(self):
        tt = np.arange(self.nc) / CR
        for e in self.ev:
            if e['type'] != 'silence':
                continue
            t0, ln, lv = e['t'], max(0.3, e['len']), e['level']
            depth = -(20 + 40 * lv)
            t1 = t0 + ln
            g = np.interp(tt, [t0 - 0.12, t0, t1 - 0.02, t1], [0, depth, depth, 0], left=0, right=0)
            self.gate = np.minimum(self.gate, g)
            gh = np.interp(tt, [t0 - 0.05, t0 + 0.2, t1 - 0.02, t1], [0, depth, depth, 0], left=0, right=0)
            self.gate_hits = np.minimum(self.gate_hits, gh)
            r = np.interp(tt, [t1 - 0.01, t1, t1 + 4.5], [0, -12.0, 0], left=0, right=0)
            self.reentry = np.minimum(self.reentry, r)
        for e in self.ev:
            if e['type'] == 'end':           # everything but the cadence fades out under it
                i0 = int(e['t'] * CR)
                k = np.arange(self.nc - i0) / CR
                self.endfade[i0:] = np.minimum(self.endfade[i0:], -60 * np.clip(k / 4.0, 0, 1) ** 0.6)

    # ----------------------------------------------------------------------------------------- render
    def run(self, normalize=True):
        t00 = time.time()
        self.automation()
        for e in self.ev:
            ty = e['type']
            if ty in ('hit',):
                self.render_hit(e)
            elif ty == 'stinger':
                self.render_hit(e, kind='stinger')
            elif ty == 'braam':
                self.render_braam(e)
            elif ty == 'riser':
                self.render_riser(e)
            elif ty == 'sub_drop':
                self.render_subdrop(e)
            elif ty == 'swell':
                self.render_swell(e)
            elif ty == 'rule':
                self.render_rule(e)
            elif ty in ('show', 'winks'):
                if any(x['type'] == 'end' and x['t'] <= e['t'] for x in self.ev):
                    continue                              # after the end cue: rendered after the end fade (below)
                try:
                    (self.render_show if ty == 'show' else self.render_winks)(e)
                except Exception as ex:                   # an identity layer must never cost the score
                    print(f'[score] WARNING: {ty} at {e["t"]:.2f} s failed ({repr(ex)[:120]}): skipped', flush=True)
            elif ty not in KNOWN_EVENTS:
                print(f'[score] WARNING: unknown music event type {ty!r} at {e["t"]:.2f} s: ignored', flush=True)
        self.log(f'events {time.time() - t00:.1f}s')
        self.render_melodic()
        self.log(f'melodic {time.time() - t00:.1f}s')
        self.render_pulse()
        self.log(f'pulse {time.time() - t00:.1f}s')
        self.render_tracks()
        self.log(f'tracks {time.time() - t00:.1f}s')
        self.render_drones()
        self.log(f'drones {time.time() - t00:.1f}s')
        ends = [e for e in self.ev if e['type'] == 'end']
        # pre-reverb automation (ducks, re-entry, swell breathing, end fade); silences are gated after the reverb
        # v2.1: swells lift the whole bed (tracks +7, drones +3, string bed +4 dB at the peak; was tracks +4 only), so
        # the bed breathes in ~13 s rises of 8-12 LU like the references
        pre = {'tracks': self.duck + self.reentry + 7.0 * self.swell + self.endfade + self.showduck,
               'drones': self.duck + self.reentry + 3.0 * self.swell + self.endfade,
               'pulse': self.duck + self.reentry + self.endfade,
               'strings_bed': self.duck + self.reentry + 4.0 * self.swell + self.endfade + 0.5 * self.showduck,
               'melodic': np.maximum(self.duck, -8.0) + self.endfade,
               'strings_fx': self.endfade, 'hits': self.endfade, 'show': np.maximum(self.duck, -6.0) + self.endfade}
        for k, c in pre.items():
            if not np.any(c):
                continue
            g = self.to_audio(c)
            self.bus[k].dry *= g[:, None]
            for snd in self.bus[k].send.values():
                snd *= g
            del g
        for e in ends:
            self.render_end(e)
        for e in self.ev:                                 # identity events after the end cue (the TV far away at the end)
            if e['type'] in ('show', 'winks') and any(x['type'] == 'end' and x['t'] <= e['t'] for x in self.ev):
                try:
                    (self.render_show if e['type'] == 'show' else self.render_winks)(e)
                    self.end_t1 = max(self.end_t1, e['t'] + float(e.get('len') or 4.0) + 1.0)
                except Exception as ex:
                    print(f'[score] WARNING: {e["type"]} at {e["t"]:.2f} s failed ({repr(ex)[:120]}): skipped', flush=True)
        self.bank.pitched.clear()                     # free sample caches before the reverb stage
        self.bank.raw = {k: v for k, v in self.bank.raw.items() if k.startswith('trk:')}
        irs = {k: _ir(k) for k in IRS}
        out = {}
        for k in ('tracks', 'drones', 'pulse', 'melodic', 'show', 'hits'):
            out[k] = self.bus[k].mixdown(irs)
        out['strings'] = self.bus['strings_bed'].mixdown(irs)
        out['strings'] += self.bus['strings_fx'].mixdown(irs)
        out['strings'] = _width(out['strings'], 0.8)
        for k in ('tracks', 'hits'):                  # tame the 100-160 Hz hump (AUDIO_SPEC octave tilt)
            out[k] = _peq(out[k], 120.0, -3.0, 0.9)
        self.bus = {}
        self.log(f'reverb {time.time() - t00:.1f}s')
        gb, gh = self.to_audio(self.gate), self.to_audio(self.gate_hits)
        for k in out:
            out[k] *= (gh if k == 'hits' else gb)[:, None]
        del gb, gh
        # hard end: after the end cue's tail everything is silent (no stray tails past the film)
        if ends:                                      # fix 3: the fade also runs when the cadence outlasts the film
            i = min(int(min(self.dur, self.end_t1) * SR), self.n)
            fo = int(2.0 * SR)
            for k in out:
                a = max(0, i - fo)
                if i > a: out[k][a:i] *= _fade(i - a, 'out')[:, None]
                out[k][i:] = 0
        if normalize:
            bed = out['tracks'].copy()
            for k in STEMS:
                if k not in ('hits', 'tracks'):
                    bed += out[k]
            li = integrated(bed)
            del bed
            if li > -90:
                g = np.float32(db(REF_LUFS - li))
                for k in out:
                    if k != 'hits':                  # hits are already sized relative to REF_LUFS
                        out[k] *= g
            self.norm_gain_db = float(REF_LUFS - li)
        self.log(f'done {time.time() - t00:.1f}s')
        return {k: out[k].astype(np.float32) for k in STEMS}


def act_db(act):
    return 20 * np.log10(np.maximum(act, 1e-3))


def render(cues, duration=None, *, seed=None, normalize=True, progress=None):
    """See module docstring. Returns {stem: float32 [n, 2]} at 48 kHz."""
    dur = float(duration if duration is not None else cues.get('duration', 60.0))
    return Score(cues, dur, seed=seed, progress=progress).run(normalize=normalize)


def _write(path, y):
    sf.write(path, y, SR, subtype='FLOAT')        # float: the hits stem may exceed 0 dBFS before the mix


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('cues')
    ap.add_argument('out')
    ap.add_argument('--duration', type=float, default=None)
    a = ap.parse_args()
    cues = json.load(open(a.cues))
    os.makedirs(a.out, exist_ok=True)
    stems = render(cues, a.duration, progress=lambda m: print('[score]', m, flush=True))
    for k, y in stems.items():
        _write(os.path.join(a.out, f'score_{k}.wav'), y)
    _write(os.path.join(a.out, 'score_sum.wav'), sum(stems.values()))
    json.dump(plan(cues, a.duration), open(os.path.join(a.out, 'score_plan.json'), 'w'), indent=1)
