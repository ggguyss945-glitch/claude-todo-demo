"""shorts/mix_short.py: the sound of one vertical Short, from the assembler's voice track and cue lists.

    python3 shorts/mix_short.py --short 1|2|3 --in <assembler out dir> [--out DIR] [--no-mux] [--no-stems]
                                [--under 10] [--duck 2]

Reads (shorts/assemble.py output): <in>/voice.wav (dry narration, 48 kHz mono), timing.json (clips with their radio /
phone fx, beats with the tension beat, overlay events), cues_sfx.json, cues_music.json; muxes onto <in>/picture.mp4.
Writes to <out> (default <in>):
    mix.wav          48 kHz 24-bit stereo master (-14 LUFS integrated, loudness range <= 2.5 LU, true peak <= -1 dBTP)
    stems/{voice,music,sfx}.wav   float32 at master gain, before the master leveler / limiter
    mix_report.json  measured loudness (ffmpeg ebur128), LRA, true peak, silences, music under the voice, music
                     coverage, SFX density (from the cues and measured on the master like SHORTS_ANALYSIS.md)
    short_mix.mp4    picture.mp4 + mix.wav (AAC 320k)

Signal flow
  voice  per-clip loudness levelling (70 % toward the median, +-4 dB) -> radio / phone line FX where timing.json says
         (audio/mix.py apply_line_fx, v1 logic) -> HPF 70 Hz, -1.5 dB at 250 Hz, +2 dB at 3.5 kHz, +1 dB air ->
         audio/mix.py voice_chain (-14 LUFS, 2.5:1 on the loudest syllables, true-peak PLR 11 dB)
  music  the plan's Epidemic track (cues_music.track), edited with musical cuts:
           pre-gap segment: starts on the strongest onset near the plan's start (pulled earlier when it would cross
           the loud section before the gap), so the Short opens on a musical attack together with the braam;
           tension gap: music out from the end of the last word to the next voice onset (1.0-1.2 s), with a 40 ms
           cut (the riser in the cues ends on it);
           post-gap segment: slipped so the track's loud section lands exactly on the twist; it re-enters with a
           0.1-0.3 s swell under the first word after the gap;
           REWIND: the last 10 frames (60 fps) play the music reversed at 3x (tape rewind) into the loop.
         HPF 30 Hz, low shelf -3 dB at 120 Hz, -3 dB at 300 Hz (phone playback, room for the voice) -> slow leveller
         (1 s loudness, 75 % toward the track's own median, -6..+9 dB) + the cue sheet's intensity curve (+-2 dB) ->
         voice-keyed bell cut (1-4.5 kHz, 4 dB) -> sidechain duck (--duck 2 dB, 80 / 250 ms) -> pre-hit dips (6 dB
         over 0.25 s before braams / stingers / the twist) -> one gain solved so the music sits --under dB (default
         10) under the voice (median of 400 ms K-weighted loudness over speech), so about 8 dB under between phrases.
  music hits  cue-sheet hits / braams / sub drops / stingers not already in the SFX cues (sfx.py, Epidemic first);
         the twist layer: a reversed-impact swell from the voice re-entry into the twist (or a riser when the twist is
         far from the gap); never ducked at the transient.
  sfx    hit balance first: distinct strong hit events (cues within 0.25 s count once) per 10 s held to 3-6 by
         promoting keyword punches / diegetic clicks (+5 dB) or accenting a cut, never in the build into the gap.
         Every cue in cues_sfx.json via audio/sfx.py render_event (owner's Epidemic recordings first), gain, pan,
         placed at t - pre. Bed cues (ambience, room tone, tinnitus, heartbeat, static, idle, whispers) with
         gain_db <= -10 are read as the plan's level relative to the voice (cues.py writes the plan's "-24 dB"),
         not as an offset from sfx.py's house level. Buses: beds (ducked 2 dB under the voice; ambience / car idle
         down 12 dB in the gap, heartbeat up 4 dB), events (1 dB), hits (+2 dB, a bright 'snap' transient under
         impacts / stingers / braams and a parallel harmonic exciter so the subs read on a phone; tails ducked 4 dB
         after the first 0.15 s); HPF 25 Hz, -2 dB shelf at 50 Hz. The SUBSCRIBED pop gets a bell. Frame 1's
         diegetic motif (knocks / radio click / pen click) is rendered once and the very same audio is placed again
         just before the REWIND, so the loop closes on the same sound (added if the cue sheet lost it).
  master voice + bed bus (2:1 glue) -> -14 LUFS -> short-term leveller only if the loudness range is over 2.3 LU
         (3 s loudness toward -14, never lifting the tension gap) -> 4x oversampled look-ahead true-peak limiter
         (ceiling -1.4 dBTP), iterated to -14, then trimmed to ffmpeg ebur128's own reading.
"""
import argparse, json, os, subprocess, sys, time, re
import numpy as np, soundfile as sf
from scipy import signal
from scipy.ndimage import uniform_filter1d

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(V2, 'audio'))
import sfx as SX  # noqa: E402
import mix as MX  # noqa: E402

SR = 48000
TARGET = -14.0
S = '/home/user/claude-todo-demo/Vox test/Police Officer Video/v2/_work'
CACHE = os.path.join(S, 'pov2', 'cache', 'shorts_mix')
CATALOG = os.path.join(V2, 'audio', 'catalog_epidemic.json')
SPEC = os.path.join(HERE, 'shorts_spec.json')
LOOP_PRIMARY = ('pen_click', 'radio_click', 'knock_door')            # frame 1's diegetic motif, in priority order
LOOP_GROUP = ('pen_click', 'radio_click', 'knock_door', 'police_radio_squelch')
GAP_DUCK = ('ambience_night', 'car_idle', 'crowd_whisper')          # beds pulled down inside the tension gap
GAP_LIFT = ('heartbeat',)                                          # ...and the heartbeat up: the gap is tense, not dead
GAP_LIFT_DB = 4.0
BIG_HITS = ('braam', 'sub_drop', 'stinger')
SNAP = ('impact_hit', 'stinger', 'braam')                          # hits that get the bright transient layer
HIT_LIFT_DB = 2.0                                                  # hits bus lift over sfx.py's house level


def log(*a):
    print('[mix_short]', *a, flush=True)


def ldb(p):
    return -0.691 + 10 * np.log10(np.maximum(p, 1e-20))


def mom(x, win=0.4, hop=0.1):
    """K-weighted loudness of win-second blocks every hop seconds (block k starts at k * hop)."""
    return ldb(SX._blocks(SX.st(x), win, hop))


def lra(y):
    """EBU Tech 3342 loudness range: 3 s short-term blocks every 0.1 s, -70 LUFS absolute and -20 LU relative gates,
    P95 - P10."""
    p = SX._blocks(y, 3.0, 0.1); L = ldb(p)
    p = p[L > -70]; L = L[L > -70]
    if not len(p): return 0.0
    rel = ldb(p.mean()) - 20
    L = L[L > rel]
    return float(np.percentile(L, 95) - np.percentile(L, 10))


# ============================================================================ inputs
def load(ind):
    T = json.load(open(os.path.join(ind, 'timing.json')))
    cues = json.load(open(os.path.join(ind, 'cues_sfx.json')))
    mc = json.load(open(os.path.join(ind, 'cues_music.json')))
    v, sr = sf.read(os.path.join(ind, 'voice.wav'), dtype='float32')
    if v.ndim > 1: v = v.mean(1)
    if sr != SR: v = signal.resample_poly(v, SR, sr).astype(np.float32)
    dur = float(T['duration']); N = int(round(dur * SR))
    v = np.pad(v[:N], (0, max(0, N - len(v))))
    return T, cues, mc, v, dur, N


def key_times(T, mc, dur):
    clips = sorted(T['clips'], key=lambda c: c['dst_on'])
    k = dict(twist=mc.get('twist_t'), sub=mc.get('subscribe_t'), end=mc.get('end_card_t'), gap=None, rewind=None,
             clips=clips)
    tb = [b for b in T['beats'] if b.get('tension')]
    if tb:
        g0 = float(tb[0]['voice_off'])
        nxt = [c['dst_on'] for c in clips if c['dst_on'] > g0 + 0.05]
        g1 = float(min(nxt)) if nxt else float(tb[0]['t1'])
        if g1 - g0 > 1.2: g0 = g1 - 1.2                 # music holds after the line, then goes out for 1.2 s
        g1 = max(g1, g0 + 1.05)                          # at least 1.0 s out (the swell re-enters under the first word)
        k['gap'] = (round(g0, 3), round(g1, 3))
    rw = [e['t'] for e in T['events'] if e.get('type') == 'rewind']
    k['rewind'] = float(rw[0]) if rw else None
    return k


# ============================================================================ voice
def build_voice(v, clips):
    v = v.copy()
    Ls = []
    for c in clips:
        a, b = int(c['dst_on'] * SR), int(c['dst_off'] * SR)
        Ls.append(SX.lufs_int(v[a:b]) if b - a > SR // 10 else -70.0)
    ok = [L for L in Ls if L > -60]
    med = float(np.median(ok)) if ok else -20.0
    gains = []
    for c, L in zip(clips, Ls):
        if L <= -60: gains.append(0.0); continue
        g = float(np.clip((med - L) * 0.7, -4.0, 4.0)); gains.append(round(g, 1))
        a, b = int(max(0.0, c['dst_on'] - 0.08) * SR), int(min(len(v) / SR, c['dst_off'] + 0.15) * SR)
        w = np.full(b - a, 10 ** (g / 20), np.float32); r = min(int(0.03 * SR), (b - a) // 4)
        if r > 1:
            w[:r] = np.linspace(1, w[r], r); w[-r:] = np.linspace(w[-r - 1], 1, r)
        v[a:b] *= w
    spans = [(c['dst_on'], c['dst_off'], c['fx']) for c in clips if c.get('fx')]
    if spans:
        v = MX.apply_line_fx(v, spans)
    v = SX.hp(v, 70, 2)
    v = SX.eq(v, ('peak', 250, -1.5, 1.0), ('peak', 3500, 2.0, 0.8), ('hs', 9000, 1.0, 0.7))
    v, st = MX.voice_chain(v.astype(np.float32), 12.0)
    st['clip_gains_db'] = gains
    st['line_fx'] = [[round(a, 2), round(b, 2), k] for a, b, k in spans]
    return v.astype(np.float32), st


# ============================================================================ SFX
def bell(seed=0):
    """Soft notification bell for SUBSCRIBED (C6 with bell partials, 1.4 s)."""
    t = np.arange(int(1.4 * SR)) / SR
    rng = np.random.default_rng(seed)
    y = np.zeros_like(t)
    for r, a, d in ((1.0, 1.0, 0.9), (2.0, 0.35, 0.5), (2.76, 0.25, 0.35), (5.40, 0.10, 0.15), (8.93, 0.04, 0.08)):
        y += a * np.sin(2 * np.pi * 1046.5 * r * (1 + rng.uniform(-0.002, 0.002)) * t) * np.exp(-t / d)
    y *= 1 - np.exp(-t / 0.002)
    y = SX.reverb(SX.st(y.astype(np.float32)), 'hall', 0.15)
    return SX.fade(y, 0.001, 0.2)


def snap(seed=0):
    """Bright transient for a hit (so dark, sub-heavy impacts still read on a phone speaker): band-passed noise crack
    (12 ms decay) + a 140 Hz chest thump (35 ms) + a short room."""
    rng = np.random.default_rng(seed); n = int(0.09 * SR); t = np.arange(n) / SR
    crack = SX.bp(rng.standard_normal(n).astype(np.float32), 1800, 9000, 2) * np.exp(-t / 0.012)
    body = np.sin(2 * np.pi * np.cumsum(140 * (1 - 0.35 * t / t[-1])) / SR) * np.exp(-t / 0.035)
    y = SX.st((crack / (np.abs(crack).max() + 1e-9) * 0.8 + body * 0.55).astype(np.float32))
    y = SX.reverb(SX.fade(y, 0.0005, 0.01), 'live', 0.12)
    return SX.pnorm(y)


def phone_body(x, amt=0.35):
    """Parallel harmonic exciter for the hits bus: the 40-160 Hz band saturated, band-passed 180-3000 Hz, added back."""
    lo = SX.bp(x, 40, 160, 2)
    h = SX.bp(np.tanh(lo * 6.0).astype(np.float32), 180, 3000, 2)
    return x + h * np.float32(amt)


def loop_plan(cues, rewind, dur):
    """Frame 1's diegetic motif -> (group indices at the start, shift to the end, end indices it replaces, added)."""
    start = [i for i, c in enumerate(cues) if c['name'] in LOOP_GROUP and c['t'] <= 0.4]
    if not start: return None
    prim = next((n for n in LOOP_PRIMARY if any(cues[i]['name'] == n for i in start)), None)
    if prim is None: return None
    i0 = min((i for i in start if cues[i]['name'] == prim), key=lambda i: cues[i]['t'])
    rw = rewind if rewind is not None else dur - 0.15
    ends = [i for i, c in enumerate(cues) if c['name'] == prim and rw - 1.5 <= c['t'] <= rw + 0.01 and c['t'] > 1.0]
    added = False
    if ends:
        te = min(cues[i]['t'] for i in ends)          # the end group's first hit (the copy must finish before the REWIND)
    else:
        te = rw - 0.12; added = True
    shift = te - cues[i0]['t']
    names = set(cues[i]['name'] for i in start)
    span = max(cues[i]['t'] for i in start) - min(cues[i]['t'] for i in start)
    repl = [i for i, c in enumerate(cues) if c['name'] in names and c['t'] > 1.0
            and te - 0.3 <= c['t'] <= te + span + 0.3]
    return dict(start=start, prim=prim, shift=shift, replace=repl, t_end=te, added=added)


PROMOTE = ('impact_hit', 'mail_slot', 'car_door_close', 'bodycam_beep', 'radio_click', 'police_radio_squelch', 'knock_door',
           'pen_click', 'glitch', 'paper', 'stinger')


def hit_events(cues, sep=0.25):
    ev = []
    for t in sorted(c['t'] for c in cues if c.get('kind') == 'hit'):
        if not ev or t - ev[-1] > sep: ev.append(t)
    return ev


def balance_hits(cues, dur, kt, lo=3, hi=6):
    """Distinct strong hit events (hit cues closer than 0.25 s count once) per 10 s window held to lo..hi (pro rata for a
    short last window): extra hits are demoted (-4 dB, transient); missing ones come from promoting keyword punches and
    diegetic clicks / slots / beeps (+5 dB, the snap layer), spread out and never inside the build into the tension gap,
    then from accenting a cut with a new impact. Returns (cues, log)."""
    cues = [dict(c) for c in cues]; notes = []
    quiet = (kt['gap'][0] - 1.0, max(kt['gap'][1], kt['twist'] or 0) - 0.02) if kt['gap'] else (-1, -1)
    for j in range(int(np.ceil(dur / 10))):
        a, b = 10 * j, min(dur, 10 * j + 10)
        if b - a < 2.0: break
        need = max(2, int(round(lo * (b - a) / 10))); cap = max(2, int(round(hi * (b - a) / 10)))
        ev = [t for t in hit_events(cues) if a <= t < b]
        while len(ev) > cap:                                       # demote the weakest cluster
            weakest = min(ev, key=lambda t: max(c.get('prio', 0) for c in cues if c.get('kind') == 'hit' and abs(c['t'] - t) <= 0.25))
            for c in cues:
                if c.get('kind') == 'hit' and abs(c['t'] - weakest) <= 0.25:
                    c['kind'] = 'transient'; c['gain_db'] = round(c['gain_db'] - 4, 1); c['why'] += ' (mixer: demoted)'
            ev.remove(weakest); notes.append(('demoted', round(weakest, 2)))
        while len(ev) < need:
            cand = [c for c in cues if a <= c['t'] < b and c.get('kind') != 'hit' and c['name'] in PROMOTE
                    and not (quiet[0] <= c['t'] <= quiet[1]) and c['t'] > 0.6 and all(abs(c['t'] - t) >= 0.8 for t in ev)]
            if cand:
                rank = lambda c: (0 if c.get('why', '').startswith('keyword') else 1 if c.get('kind') == 'diegetic' or
                                  c.get('why') == 'staging' else 2, -min([abs(c['t'] - t) for t in ev] + [99]))
                c = min(cand, key=rank)
                c['kind'] = 'hit'; c['gain_db'] = round(c['gain_db'] + 5, 1); c['why'] += ' (mixer: promoted to hit)'
                if c['name'] == 'impact_hit': c.setdefault('params', {})['size'] = 0.85
                ev.append(c['t']); notes.append(('promoted', c['name'], c['t']))
                continue
            cuts = [c['t'] for c in cues if c.get('why') == 'cut' and a <= c['t'] < b and not (quiet[0] <= c['t'] <= quiet[1])
                    and all(abs(c['t'] - t) >= 0.8 for t in ev)]
            if not cuts: break
            t = max(cuts, key=lambda x: min([abs(x - y) for y in ev] + [99])) + 0.05
            cues.append(dict(t=round(t, 3), name='impact_hit', gain_db=-4.0, pan=0.0, kind='hit', why='cut accent (mixer)',
                             params=dict(size=0.8), prio=40))
            ev.append(t); notes.append(('cut accent', round(t, 2)))
    return cues, notes


OVER_SPEECH_DB = {'stinger': -8.0, 'impact_hit': -4.0, 'whoosh': -3.0}    # cue gain when it lands while the voice speaks


def render_sfx(cues, N, dur, kt, act=None):
    SX.reset()
    buses = {b: np.zeros((N, 2), np.float32) for b in ('beds', 'events', 'hits')}
    gap = kt['gap']
    gap_env = lift_env = None
    if gap:
        gap_env = MX.gain_env(N, [(gap[0], gap[1], -12.0, 0.15, 0.2)])
        lift_env = 2.0 - MX.gain_env(N, [(gap[0] + 0.03, gap[1] - 0.02, -6.0, 0.08, 0.1)])   # 1 outside, 1.5 inside
        lift_env = 1.0 + (lift_env - 1.0) / 0.5 * (10 ** (GAP_LIFT_DB / 20) - 1.0)
    lp = loop_plan(cues, kt['rewind'], dur)
    skip = set(lp['replace']) if lp else set()
    order = sorted(range(len(cues)), key=lambda k: (cues[k]['t'], k))
    rendered = {}
    hit_times, big = [], []
    counts = {'hits': 0, 'events': 0, 'beds': 0}
    bed_levels = []
    over_speech = []
    t0 = time.time()

    def put(c, y, pre, t):
        name = c['name']
        g = float(c.get('gain_db', 0.0))
        if act is not None and name in OVER_SPEECH_DB and not (kt['twist'] and abs(t - kt['twist']) < 0.15):
            i0, i1 = int(max(0.0, t) * SR), int(min(dur, t + 0.45) * SR)
            if i1 > i0 and float(act[i0:i1].mean()) > 0.3:
                g += OVER_SPEECH_DB[name]; over_speech.append((round(t, 2), name))
        y = y * np.float32(10 ** (g / 20))
        if c.get('pan'): y = SX.pan(y, float(c['pan']))
        b = 'beds' if c.get('kind') == 'bed' else 'hits' if (c.get('kind') == 'hit' or name in SX.HITS) else 'events'
        i = int(round((t - pre) * SR))
        if gap_env is not None and (name in GAP_DUCK or name in GAP_LIFT):
            z = np.zeros((N, 2), np.float32); SX.place(z, y, i)
            z *= (gap_env if name in GAP_DUCK else lift_env)[:, None]; buses[b] += z
        else:
            SX.place(buses[b], y, i)
        counts[b] += 1
        if b == 'hits': hit_times.append(t)
        if name in BIG_HITS: big.append(t)

    for rank, k in enumerate(order):
        if k in skip: continue
        c = cues[k]; name = c['name']
        params = dict(c.get('params') or {})
        space = c.get('space') or params.pop('space', None)
        params.pop('space', None)
        kind_p = params.get('kind')
        if name == 'ui_pop': params.pop('kind', None)
        if name in SX.BEDS and params.get('dur'):
            params['dur'] = float(max(0.5, min(float(params['dur']), dur - c['t'] + 0.5)))
        lvl = 0.0
        if (c.get('kind') == 'bed' or name in SX.BEDS or name == 'heartbeat') and float(c.get('gain_db', 0)) <= -10:
            # a continuous bed whose gain is the plan's level relative to the voice ("ambience_night -24 dB"), not an
            # offset from sfx.py's house level (that would put the night bed at -49 LU, inaudible)
            sp_ = space or SX.DEFAULT_SPACE[name]
            lvl = float(c['gain_db']) - SX.LEVEL_LU[name] - SX.SPACE_LU.get(sp_, 0.0)
            c = dict(c, gain_db=0.0); bed_levels.append((name, round(float(cues[k]['gain_db']), 1)))
        y, pre = SX.render_event(name, seed=int(c.get('seed', rank)), space=space, level=lvl, **params)
        if name in SNAP and c.get('kind') == 'hit':              # bright transient on the strong hits
            pk = SX.peak(y) * 10 ** (float(c.get('gain_db', 0.0)) / 20)
            sn = snap(rank) * np.float32(pk * 10 ** (-5 / 20))
            SX.place(buses['hits'], SX.pan(sn, float(c.get('pan', 0.0))), int(round(c['t'] * SR)))
        rendered[k] = (y, pre)
        put(c, y, pre, c['t'])
        if name == 'ui_pop' and kind_p == 'bell':
            yb = bell(rank)
            yb = yb * np.float32(10 ** ((TARGET - 13 + float(c.get('gain_db', 0)) - SX.mom_max(yb)) / 20))
            SX.place(buses['events'], yb, int(round(c['t'] * SR)))
    loop_info = None
    if lp:
        for k in lp['start']:
            c = cues[k]; y, pre = rendered[k]
            c2 = dict(c, t=round(c['t'] + lp['shift'], 3), why='loop: frame 1 motif again before the REWIND')
            if c2['t'] < dur: put(c2, y, pre, c2['t'])
        loop_info = dict(motif=lp['prim'], at=round(lp['t_end'], 3), cues=len(lp['start']), replaced=len(lp['replace']),
                         added=lp['added'])
    log('sfx rendered in %.1f s: %s; beds at plan level (LU rel voice): %s; ducked under speech: %d' % (time.time() - t0, counts, bed_levels,
                                                                                                 len(over_speech)))
    return buses, sorted(hit_times), sorted(big), counts, loop_info


# ============================================================================ music
def track_entry(slug):
    for e in json.load(open(CATALOG))['music']:
        if e['slug'] == slug: return e
    raise KeyError(slug)


def onset_curve(slug, path):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, slug + '_onset.npz')
    if os.path.exists(p):
        z = np.load(p); return z['t'], z['o']
    import librosa
    y, sr = librosa.load(path, sr=22050, mono=True)
    o = librosa.onset.onset_strength(y=y, sr=sr, hop_length=256)
    t = librosa.frames_to_time(np.arange(len(o)), sr=sr, hop_length=256)
    np.savez(p, t=t, o=o)
    return t, o


def snap_onset(t, ot, oo, rng=0.5, k=2.0):
    """The strongest onset within +-rng s of t when it stands out (> k x median onset strength), else t."""
    w = (ot > t - rng) & (ot < t + rng)
    if not w.any(): return t, False
    i = np.flatnonzero(w)[np.argmax(oo[w])]
    return (float(ot[i]), True) if oo[i] > k * np.median(oo) else (t, False)


def plan_music(mc, kt, dur, sid):
    spec = json.load(open(SPEC))
    sp = [s for s in spec['shorts'] if s['id'] == sid][0]
    slug = mc['track']; e = track_entry(slug)
    ot, oo = onset_curve(slug, e['path'])
    twist = kt['twist'] if kt['twist'] is not None else 0.0
    anchor = float(mc['start_in_track']) + twist             # the track's section boundary that lands on the twist
    anchor, snapped_a = snap_onset(anchor, ot, oo, 0.3, 3.0)
    post_off = anchor - twist
    segs = []
    planned = float(sp['music'].get('start_in_track', mc['start_in_track']))
    if kt['gap'] and kt['gap'][1] <= twist + 0.01:
        g0, g1 = kt['gap']
        P = planned
        if P + g0 > anchor - 0.4: P = max(0.0, anchor - 0.4 - g0)   # never reach the loud section before the gap
        P, snapped_p = snap_onset(P, ot, oo, 0.5, 1.6)
        segs = [(0.0, g0, P), (g1, dur, post_off)]
    else:
        P = post_off; snapped_p = False
        segs = [(0.0, dur, post_off)]
        if kt['gap']:
            segs = [(0.0, kt['gap'][0], post_off), (kt['gap'][1], dur, post_off)]
    return dict(slug=slug, path=e['path'], tonal_centre=e.get('tonal_centre'), anchor=round(anchor, 3),
                anchor_on_onset=snapped_a, pre_start=round(P, 3), pre_on_onset=snapped_p, planned_start=planned,
                segs=[(round(a, 3), round(b, 3), round(o, 3)) for a, b, o in segs])


def render_track(pm, N, dur, kt):
    x, sr = sf.read(pm['path'], dtype='float32')
    if sr != SR: x = signal.resample_poly(x, SR, sr, axis=0).astype(np.float32)
    x = SX.st(x)
    out = np.zeros((N, 2), np.float32)
    twist = kt['twist'] or 0.0
    for (a, b, off) in pm['segs']:
        i0, i1 = int(round(a * SR)), int(round(b * SR)); j0 = int(round((a + off) * SR))
        if j0 < 0: i0 -= j0; j0 = 0
        seg = x[j0:j0 + (i1 - i0)]
        seg = np.pad(seg, ((0, (i1 - i0) - len(seg)), (0, 0))).copy()
        n = len(seg)
        if a <= 0.0:
            f = int(0.005 * SR); seg[:f] *= np.linspace(0, 1, f)[:, None]
        else:                                                 # re-entry after the gap: a short swell into the twist
            L = float(np.clip(twist - a, 0.1, 0.3)) if twist - a < 1.5 else 0.12
            f = min(n, int(L * SR)); w = 10 ** (np.linspace(-18, 0, f) / 20); seg[:f] *= w[:, None]
        if b < dur - 0.01:                                    # the cut into the tension gap
            f = min(n, int(0.04 * SR)); seg[-f:] *= (np.cos(np.linspace(0, np.pi / 2, f)) ** 2)[:, None]
        out[i0:i0 + n] += seg
    if kt['rewind'] is not None:                              # tape rewind: the last 8 frames play the music backwards
        r0 = int(round(kt['rewind'] * SR)); L = N - r0
        if 0 < L < SR:
            src = out[max(0, r0 - 3 * L):r0][::-1].copy()
            scrub = SX.rate(src, 3.0)[:L]
            scrub = np.pad(scrub, ((0, L - len(scrub)), (0, 0)))
            scrub *= np.linspace(1.0, 0.5, L)[:, None]
            out[r0:] = scrub
    return out


def level_track(m, mc, dur, gap):
    """Slow leveller toward the track's own median + the intensity curve (+-2 dB). Returns (music, gain dB @ 20 Hz)."""
    hop = 0.05
    l = mom(m, 1.0, hop); tb = np.arange(len(l)) * hop + 0.5
    ing = np.zeros(len(l), bool)
    if gap: ing = (tb > gap[0] - 0.6) & (tb < gap[1] + 0.6)
    live = (l > -60) & ~ing
    if not live.any(): return m, np.zeros(1)
    med = float(np.median(l[live]))
    g = np.clip((med - l) * 0.75, -6.0, 9.0)
    g[l < med - 30] = 0.0; g[ing] = np.minimum(g[ing], 0.0)
    iv = np.array(mc.get('intensity') or [[0, 0.65], [dur, 0.65]], float)
    I = np.interp(tb, iv[:, 0], iv[:, 1])
    g += np.clip((I - 0.65) * 6.0, -2.0, 2.0) * ~ing
    g = uniform_filter1d(g, size=int(1.5 / hop))
    gs = np.interp(np.arange(len(m)) / SR, tb, g).astype(np.float32)
    return m * (10 ** (gs / 20))[:, None], g


def music_hits(mc, cues, kt, N, dur, pm):
    """Cue-sheet music events not already in the SFX cues + the twist layer."""
    out = np.zeros((N, 2), np.float32); done = []
    fam = dict(hit=('impact_hit', 'stinger', 'braam', 'knock_door'), braam=('braam',), sub_drop=('sub_drop',),
               stinger=('stinger', 'braam'))
    key = 'd' if (pm.get('tonal_centre') or '').upper() in ('D', 'A', 'G') else 'e'
    gap = kt['gap']; twist = kt['twist']
    for k, e in enumerate(mc.get('events', [])):
        typ, t = e['type'], float(e['t'])
        if typ in fam:
            if any(c['name'] in fam[typ] and abs(c['t'] - t) < 0.1 for c in cues): continue
            lev = float(e.get('level', 0.7))
            name = 'impact_hit' if typ == 'hit' else typ
            params = dict(size=0.6 + 0.6 * lev) if name == 'impact_hit' else dict(key=key) if name == 'braam' else {}
            y, pre = SX.render_event(name, seed=900 + k, **params)
            y = y * np.float32(10 ** ((lev - 1.0) * 8 / 20))
            SX.place(out, y, int(round((t - pre) * SR))); done.append((round(t, 2), name))
            if name in SNAP:
                SX.place(out, snap(500 + k) * np.float32(SX.peak(y) * 10 ** (-5 / 20)), int(round(t * SR)))
        elif typ == 'riser':
            L = float(e.get('len', 3.0))
            if gap and t - L < gap[1] and t > gap[0]: continue          # replaced by the twist layer below
            y, pre = SX.render_event('riser', seed=900 + k, dur=L)
            SX.place(out, y * np.float32(10 ** (-4 / 20)), int(round((t - 0.1 - pre) * SR))); done.append((round(t, 2), 'riser'))
    if twist is not None:
        if gap and 0 <= twist - gap[1] < 1.6:                 # twist right after the gap: reversed-impact swell
            L = max(0.2, twist - 0.04 - (gap[1] - 0.05))
            h, pre = SX.render_event('impact_hit', seed=777, size=1.3)
            i = int(pre * SR); tail = h[i:i + int(1.6 * SR)][::-1].copy()
            sw = tail[-int(L * SR):] if len(tail) > int(L * SR) else tail
            r, _ = SX.render_event('riser', seed=778, dur=max(0.6, L))
            r = r[-len(sw):]
            sw = sw + 0.6 * np.pad(r, ((len(sw) - len(r), 0), (0, 0)))
            sw = SX.fade(sw, min(0.05, L / 4), 0.004)
            sw *= np.float32(10 ** ((TARGET - 7.0 - SX.mom_max(sw)) / 20))
            SX.place(out, sw, int(round((twist - 0.04) * SR)) - len(sw)); done.append((round(twist, 2), 'twist swell %.2fs' % L))
        elif not any(c['name'] == 'riser' and abs(c['t'] - twist) < 0.4 for c in cues):
            t_from = gap[1] if gap and gap[1] < twist else 0.0
            L = float(min(3.0, twist - t_from - 0.3))
            if L >= 0.8:
                y, pre = SX.render_event('riser', seed=779, dur=L)
                y = y * np.float32(10 ** (-5 / 20))
                SX.place(out, y, int(round((twist - 0.1 - pre) * SR))); done.append((round(twist, 2), 'riser %.1fs' % L))
    return out, done


# ============================================================================ master
def leveller(y, gap, strength, rng_db=4.0):
    hop = 0.1
    l = ldb(SX._blocks(y, 3.0, hop)); tb = np.arange(len(l)) * hop + 1.5
    g = np.clip(-(l - TARGET) * strength, -rng_db, rng_db)
    g[l < TARGET - 25] = 0.0
    if gap:
        k = (tb > gap[0] - 1.6) & (tb < gap[1] + 1.6); g[k] = np.minimum(g[k], 0.0)
    g = uniform_filter1d(g, size=10)
    gs = np.interp(np.arange(len(y)) / SR, tb, g).astype(np.float32)
    return y * (10 ** (gs / 20))[:, None]


def master(mix, gap, strength=0.0):
    y = mix * np.float32(10 ** ((TARGET - SX.lufs_int(mix)) / 20))
    if strength > 0: y = leveller(y, gap, strength)
    info = {}
    for it in range(6):
        y = y * np.float32(10 ** ((TARGET - SX.lufs_int(y)) / 20))
        z, gr, frac = MX.tp_limit(y, -1.4)
        L = SX.lufs_int(z); tp = MX.true_peak(z)
        info = dict(iters=it + 1, limiter_gr_max_db=round(gr, 2), limiter_over_1db_pct=round(100 * frac, 2))
        if abs(L - TARGET) < 0.08 and tp <= -1.15: return z, info
        y = y * np.float32(10 ** ((TARGET - L) / 20 * 1.0))
    return z, info


def ebur128(path):
    r = subprocess.run(['ffmpeg', '-nostats', '-hide_banner', '-i', path, '-filter_complex', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    s = r[r.rfind('Summary:'):]
    g = lambda pat: float(re.search(pat, s, re.S).group(1))
    return dict(integrated_lufs=g(r'I:\s+(-?[\d.]+) LUFS'), lra_lu=g(r'LRA:\s+(-?[\d.]+) LU'),
                true_peak_dbtp=g(r'True peak:.*?Peak:\s+(-?[\d.]+) dBFS'))


# ============================================================================ measurements
def silences(y, thr=-45.0, hop=0.05):
    h = int(hop * SR); n = len(y) // h
    r = 20 * np.log10(np.sqrt((y[:n * h].reshape(n, h, -1) ** 2).mean((1, 2))) + 1e-12)
    runs = []; k = 0
    while k < n:
        if r[k] < thr:
            j = k
            while j < n and r[j] < thr: j += 1
            runs.append((round(k * hop, 2), round((j - k) * hop, 2))); k = j
        else: k += 1
    return runs


def ref_onsets(y, dur):
    """SHORTS_ANALYSIS.md SFX count: 16 kHz mono, >2 kHz spectral flux, peaks over median + k std, 0.25 s apart."""
    a = signal.resample_poly(y.mean(1), 1, 3).astype(np.float32); sr = 16000
    W, H = 1024, 512; nf = (len(a) - W) // H; win = np.hanning(W)
    S = np.abs(np.fft.rfft(np.stack([a[k * H:k * H + W] * win for k in range(nf)]), axis=1))[:, 128:]
    Lg = np.log1p(S * 10); fl = np.maximum(Lg[1:] - Lg[:-1], 0).sum(1)
    out = {}
    for name, kk in (('strong_hits', 4), ('all_transients', 2)):
        thr = np.median(fl) + kk * np.std(fl)
        pk = [k for k in range(1, len(fl) - 1) if fl[k] > thr and fl[k] >= fl[k - 1] and fl[k] >= fl[k + 1]]
        on = []
        for k in pk:
            t = (k + 1) * H / sr
            if not on or t - on[-1] > 0.25: on.append(t)
        out[name] = [sum(1 for t in on if j * 10 <= t < (j + 1) * 10) for j in range(int(np.ceil(dur / 10)))]
    return out


def measure(final, vstem, mstem, mall, bstem, dur, kt, cues):
    rep = {}
    # music under the voice: 400 ms K-weighted loudness, speech blocks (voice within 10 LU of its integrated);
    # mstem = the track (the bed), mall = track + music hits, bstem = music + SFX
    Lv = mom(vstem); Lm = mom(mstem); La = mom(mall); Lb = mom(bstem); n = min(len(Lv), len(Lm), len(Lb), len(La))
    Lv, Lm, La, Lb = Lv[:n], Lm[:n], La[:n], Lb[:n]
    sp = Lv > SX.lufs_int(vstem) - 10
    d = (Lv - Lm)[sp]
    rep['music_under_voice_db'] = dict(median=round(float(np.median(d)), 1), p10=round(float(np.percentile(d, 10)), 1),
                                       p90=round(float(np.percentile(d, 90)), 1))
    rep['music_with_hits_under_voice_db'] = round(float(np.median((Lv - La)[sp])), 1)
    rep['bed_under_voice_db'] = round(float(np.median((Lv - Lb)[sp])), 1)
    # reference method (SHORTS_ANALYSIS.md): 50 ms RMS of the master, speech frames vs the quietest 10 % of frames
    h = int(0.05 * SR); m = len(final) // h
    r = 20 * np.log10(np.sqrt((final[:m * h].reshape(m, h, 2) ** 2).mean((1, 2))) + 1e-12)
    rv = 20 * np.log10(np.sqrt((vstem[:m * h].reshape(m, h, -1) ** 2).mean((1, 2))) + 1e-12)
    spf = rv > np.percentile(rv[rv > -80], 50) - 6
    rep['ref_method_voice_vs_floor_db'] = [round(float(np.median(r[spf])), 1), round(float(np.percentile(r, 10)), 1)]
    # music coverage: 400 ms blocks with the music stem above voice - 30 LU, outside the gap
    tb = np.arange(n) * 0.1 + 0.2
    ing = np.zeros(n, bool)
    if kt['gap']: ing = (tb > kt['gap'][0]) & (tb < kt['gap'][1])
    on = Lm > SX.lufs_int(vstem) - 30
    rep['music_coverage_pct_outside_gap'] = round(100 * float(on[~ing].mean()), 1)
    # music-out stretch (measured on the music stem, 50 ms RMS more than 40 dB under its median)
    rm = 20 * np.log10(np.sqrt((mstem[:m * h].reshape(m, h, 2) ** 2).mean((1, 2))) + 1e-12)
    out = rm < np.median(rm) - 40
    runs = []; k = 0
    while k < m:
        if out[k]:
            j = k
            while j < m and out[j]: j += 1
            runs.append((round(k * 0.05, 2), round((j - k) * 0.05, 2))); k = j
        else: k += 1
    rep['music_out_runs_s'] = [x for x in runs if x[1] >= 0.2]
    # true silence on the master
    sil = silences(final)
    rep['silence_runs_below_-45dBFS'] = [x for x in sil if x[1] >= 0.3]
    rep['longest_silence_s'] = max([x[1] for x in sil], default=0.0)
    # density: cue sheet (kind) and measured on the master (reference method)
    per = []
    for j in range(int(np.ceil(dur / 10))):
        a, b = 10 * j, min(dur, 10 * j + 10)
        hits = sum(1 for c in cues if a <= c['t'] < b and c.get('kind') == 'hit')
        tr = sum(1 for c in cues if a <= c['t'] < b and c.get('kind') in ('hit', 'transient', 'diegetic'))
        per.append([a, round(b - a, 1), hits, tr])
    rep['cue_density_per_window'] = per
    ev = hit_events(cues)
    rep['distinct_hit_events_per_window'] = [sum(1 for t in ev if 10 * j <= t < 10 * j + 10) for j in range(int(np.ceil(dur / 10)))]
    rep['measured_onsets_per_10s'] = ref_onsets(final, dur)
    return rep


# ============================================================================ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--short', type=int, required=True, choices=[1, 2, 3])
    ap.add_argument('--in', dest='ind', required=True)
    ap.add_argument('--out', default=None)
    ap.add_argument('--no-mux', action='store_true')
    ap.add_argument('--no-stems', action='store_true')
    ap.add_argument('--under', type=float, default=None, help='music under the voice (dB, speech median; default 10, S1 13)')
    ap.add_argument('--duck', type=float, default=2.0, help='sidechain duck of the music under the voice (dB)')
    ap.add_argument('--music-cut', type=float, default=None, dest='mcut',
                    help='voice-keyed 1-4.5 kHz cut on the music (dB; default 4, S1 6)')
    A = ap.parse_args()
    # S1's track (From Hell) is dense in the voice band: 20 % of its speech frames had the music within 3 dB of the voice
    # at the default settings (S2: 8 %), so it sits 2 dB lower and gets a deeper voice-keyed 2-4 kHz dip
    PER = {1: dict(under=13.0, mcut=6.0, scoop=-4.0)}.get(A.short, {})
    if A.under is None: A.under = PER.get('under', 10.0)
    if A.mcut is None: A.mcut = PER.get('mcut', 4.0)
    T0 = time.time()
    sid = 'S%d' % A.short
    out = A.out or A.ind
    os.makedirs(out, exist_ok=True)
    T, cues, mc, v, dur, N = load(A.ind)
    kt = key_times(T, mc, dur)
    log('%s %.2f s, %d cues, gap %s, twist %s, rewind %s' % (sid, dur, len(cues), kt['gap'], kt['twist'], kt['rewind']))

    # ---- voice
    V, vst = build_voice(v, kt['clips'])
    log('voice', {k: vst[k] for k in vst if k != 'clip_gains_db'})
    act = MX.voice_activity(V, att=0.08, rel=0.25)

    # ---- SFX
    cues, hit_notes = balance_hits(cues, dur, kt)
    log('hit balance', hit_notes)
    buses, hit_times, big, counts, loop_info = render_sfx(cues, N, dur, kt, act)

    # ---- music
    pm = plan_music(mc, kt, dur, sid)
    log('music', {k: pm[k] for k in ('slug', 'anchor', 'pre_start', 'segs')})
    M = render_track(pm, N, dur, kt)
    M = SX.eq(SX.hp(M, 30, 2), ('ls', 120, -3.0, 0.7), ('peak', 300, -3.0, 1.0))   # phone-first low end, room for the voice
    if PER.get('scoop'):                                     # S1: a static scoop where From Hell's mids sit on the voice
        M = SX.eq(M, ('peak', 650, PER['scoop'], 0.7), ('peak', 2600, PER['scoop'] * 0.75, 0.9))
    M, lev = level_track(M, mc, dur, kt['gap'])
    Mh, mh_done = music_hits(mc, cues, kt, N, dur, pm)
    log('music hits', mh_done)
    bigs = sorted(set([round(t, 2) for t in big] + [round(e['t'], 2) for e in mc.get('events', []) if e['type'] in BIG_HITS]
                      + ([round(kt['twist'], 2)] if kt['twist'] else [])))
    dips = [(h - 0.03, h, -6.0, 0.25, 0.08) for h in bigs if not (kt['gap'] and kt['gap'][0] - 0.3 < h < kt['gap'][1] + 1.2)]
    pre_dip = MX.gain_env(N, dips)
    duck = (10 ** (-A.duck * act / 20)).astype(np.float32)
    M = MX.dyn_cut(M, act, A.mcut) * (duck * pre_dip)[:, None]
    # music gain: the track sits --under dB under the voice (speech median of 400 ms loudness)
    Lv = mom(V); Lm = mom(M); n = min(len(Lv), len(Lm))
    spk = Lv[:n] > SX.lufs_int(V) - 10
    gm_db = float(np.median((Lv[:n] - Lm[:n])[spk])) - A.under
    M *= np.float32(10 ** (gm_db / 20))
    # SFX buses
    act_h = MX.voice_activity(V, att=0.02, rel=0.25)
    spare = np.ones(N, np.float32)
    for h in hit_times:
        i = int(h * SR); spare[max(0, i - int(0.01 * SR)):i + int(0.15 * SR)] = 0.0
    beds = MX.dyn_cut(buses['beds'], act, 4.0) * (duck * pre_dip)[:, None]
    ev = MX.dyn_cut(buses['events'], act, 3.0) * (10 ** (-1.0 * act / 20)).astype(np.float32)[:, None]
    hd = (10 ** (-4.0 * act_h * spare / 20)).astype(np.float32)[:, None]
    hits = MX.dyn_cut(phone_body(buses['hits']), act, 3.0) * hd * np.float32(10 ** (HIT_LIFT_DB / 20))
    mh = MX.dyn_cut(phone_body(Mh), act, 3.0) * hd * np.float32(10 ** (HIT_LIFT_DB / 20))
    sfx_bus = SX.eq(SX.hp(beds + ev, 25, 2) + SX.hp(hits, 25, 2), ('ls', 50, -2.0, 0.7))
    mus_bus = M + mh
    bed = sfx_bus + mus_bus
    bed_g, glue_gr, g_curve = MX.glue(bed, 0.0, 2.0)
    sfx_bus *= g_curve[:, None]; mus_bus *= g_curve[:, None]
    Vs = np.stack([V, V], 1)
    mix = Vs + bed_g

    # ---- master: raise the short-term leveller until the loudness range is <= 2.3 LU
    tries = []
    for s in (0.0, 0.3, 0.5, 0.7, 0.85):
        fin, minfo = master(mix, kt['gap'], s)
        r = lra(fin); tries.append((s, round(r, 2)))
        if r <= 2.3: break
    log('master leveller tries (strength, LRA):', tries)
    g_master = 10 ** ((TARGET - SX.lufs_int(mix)) / 20)
    stems = dict(voice=Vs * g_master, music=mus_bus * g_master, sfx=sfx_bus * g_master)
    track_stem = M * g_curve[:, None] * np.float32(g_master)

    # ---- write
    mp = os.path.join(out, 'mix.wav')
    sf.write(mp, np.clip(fin, -1, 1), SR, subtype='PCM_24')
    if not A.no_stems:
        os.makedirs(os.path.join(out, 'stems'), exist_ok=True)
        for k, y in stems.items(): sf.write(os.path.join(out, 'stems', k + '.wav'), y.astype(np.float32), SR, subtype='FLOAT')
    eb = ebur128(mp)
    for _ in range(3):                                           # trim to ffmpeg's own gating, re-limit, re-measure
        if abs(eb['integrated_lufs'] - TARGET) < 0.05: break
        fin, _gr, _f = MX.tp_limit(fin * np.float32(10 ** ((TARGET - eb['integrated_lufs']) * 0.8 / 20)), -1.4)
        sf.write(mp, np.clip(fin, -1, 1), SR, subtype='PCM_24'); eb = ebur128(mp)
    rep = dict(short=sid, duration=dur, master=eb, master_internal=dict(lra=round(lra(fin), 2), tp=round(MX.true_peak(fin), 2), **minfo),
               leveller_tries=tries, voice=vst, music=dict(pm, gain_db=round(gm_db, 1), duck_db=A.duck, under_target_db=A.under,
                                                          hits=mh_done, glue_gr_p95_db=round(glue_gr, 2)),
               tension_gap=kt['gap'], twist_t=kt['twist'], subscribe_t=kt['sub'], end_card_t=kt['end'], rewind_t=kt['rewind'],
               loop=loop_info, sfx_counts=counts, hit_balance=hit_notes)
    rep.update(measure(fin, Vs * g_master, track_stem, stems['music'], stems['music'] + stems['sfx'], dur, kt, cues))
    rep['seconds'] = round(time.time() - T0, 1)
    json.dump(rep, open(os.path.join(out, 'mix_report.json'), 'w'), indent=1, default=float)
    log('master', eb, 'music under voice', rep['music_under_voice_db'], 'longest silence', rep['longest_silence_s'],
        'music out', rep['music_out_runs_s'])
    if not A.no_mux:
        pic = os.path.join(A.ind, 'picture.mp4')
        dst = os.path.join(out, 'short_mix.mp4')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', pic, '-i', mp, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac',
                        '-b:a', '320k', '-ar', '48000', '-shortest', '-movflags', '+faststart', dst], check=True)
        log(dst)
    log('done in %.1f s' % (time.time() - T0))


if __name__ == '__main__':
    main()
