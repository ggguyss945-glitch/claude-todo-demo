"""Final mix for v2: narration (EN or the RU dub) with radio/phone voicing, the SFX from sfx_cues.json, and the score
stems from music_cues.json, mixed to the reference measurements in analysis/AUDIO_SPEC.md.

CLI
    python3 mix.py <timeline.json> <vo_en.wav> <vo_ru_dub.wav> <cues dir> <out dir>
                   [--t0 S --t1 S]  render only a window (tests)     [--langs en,ru]
                   [--fallback]     force the placeholder drone instead of audio/score.py
                   [--bed-p50 -16]  target bed (music + SFX) 3 s short-term median, LU rel voice (true K-weighting)
                   [--bed-rel -13]  reference integrated bed level; the bed is capped at bed_rel + 1.5
                   [--voice-plr 11.5] narration peak-to-loudness ratio after the voice peak limiter
                   [--music-width 0.7] [--no-stems]
Reads <cues>/sfx_cues.json (list of {t, name, gain_db, pan, params, space}) and <cues>/music_cues.json
({duration, intensity, events}). Writes to <out>:
    mix_en.wav, mix_ru.wav        48 kHz 24-bit stereo, -14 LUFS integrated, true peak <= -1.5 dBTP
    stems/voice_en.wav, stems/voice_ru.wav, stems/sfx.wav, stems/music.wav   float32 at the final gain, after the bus
                                  processing and before the limiter (voice_xx + sfx + music = mix before limiting;
                                  the EN ducking is baked into sfx/music)
    mix_report.json               measured loudness, levels relative to the voice, events per minute, limiter use

Signal flow
    voice  -> v1 radio/phone line FX (kept from ../src/mix.py) -> -14 LUFS -> 2.5:1 compression on the loudest
              syllables -> true-peak limiter at PLR 11.5 dB (the EN narration arrives at PLR 15.6 dB)
    sfx    -> sfx.render_event per cue (seeded by cue order, so renders repeat) -> gain/pan -> 3 buses:
              beds (ambience, room tone, static...), events, hits
    music  -> audio/score.py render(cues, duration) stems (placeholder D-A drone if score.py is missing or fails)
    bed bus = music + SFX beds + events + hits:
        - silence events in music_cues: SFX beds drop 9 dB (80 ms out, 400 ms back; score.py silences the music)
        - pre-hit dip: music and beds dip 8 dB over the 0.4 s before each SFX hit/stinger/braam/sub_drop/knock
          (score.py ducks its own hits; SFX beds also dip for the score's hits)
        - score bus: bounded auto tilt EQ toward the AUDIO_SPEC octave tilt, width 0.7, slow two-way leveler
        - dynamic bell cut at 1-4.5 kHz keyed by the voice (music/beds up to -5 dB, events -2 dB, hits 0)
        - sidechain duck from the voice envelope: music/beds -3 dB (max 6), events -1.5 dB, hits 0
        - glue compressor 2:1 on the whole bed bus (slow, RMS, ~1-3 dB)
        - music gain solved so the bed's 3 s short-term median = voice - 16 LU and its integrated <= voice - 11.5 LU.
          These are the references re-measured with true per-channel K-weighting (bed integrated -12.5/-12.8/-13.4,
          short-term p10/p50/p90 about -20.8/-16.0/-9.2, LRA 12.8). AUDIO_SPEC's short-term numbers come from
          analysis/measure.py, whose kweight() runs lfilter along the channel axis of [n, 2] arrays (no frequency
          weighting, channels mixed), so they are biased by 3-6 dB depending on spectrum and L/R correlation.
    master = voice + bed -> loudness to -14 LUFS -> look-ahead true-peak limiter (4x oversampled, ceiling -1.7 dBTP),
             iterated until integrated is -14 +- 0.1 and TP <= -1.5
"""
import argparse, json, os, sys, time, traceback
import numpy as np, soundfile as sf
from scipy import signal
from scipy.ndimage import minimum_filter1d, uniform_filter1d

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sfx as SX

SR = 48000
TARGET = -14.0


def log(*a):
    print('[mix]', *a, flush=True)


# ============================================================================ voice FX (v1 logic, kept)
def band(x, lo, hi, order=4):
    return signal.sosfilt(signal.butter(order, [lo, hi], 'bandpass', fs=SR, output='sos'), x).astype(np.float32)


def radio_fx(x):
    y = band(x, 380, 3200); y = np.tanh(y * 3.0) / np.tanh(3.0)
    return (y + band(np.random.default_rng(1).normal(0, 1, len(y)).astype(np.float32), 1500, 6000) * 0.006) * 1.1


def phone_fx(x, far=False):
    y = band(x, 320, 3300, 6); y = np.tanh(y * 1.6) / np.tanh(1.6)
    if far: y = band(y, 300, 1500, 4) * 0.8
    return y * 1.05


def apply_line_fx(vo, spans):
    """spans: list of (start s, end s, kind). Replace those stretches of the voice with the processed version."""
    out = vo.copy()
    for a, b, kind in spans:
        i0, i1 = max(0, int((a - 0.05) * SR)), min(len(vo), int((b + 0.15) * SR))
        seg = vo[i0:i1]
        if len(seg) < 100: continue
        y = radio_fx(seg) if kind == 'radio' else phone_fx(seg, kind == 'phone_far')
        f = int(0.01 * SR); w = np.ones(len(seg), np.float32); w[:f] = np.linspace(0, 1, f); w[-f:] = np.linspace(1, 0, f)
        out[i0:i1] = seg * (1 - w) + y[:len(seg)] * w
    return out


def load_vo(path, n):
    x, sr = sf.read(path, dtype='float32')
    if x.ndim > 1: x = x.mean(1)
    if sr != SR: x = signal.resample_poly(x, SR, sr).astype(np.float32)
    y = np.zeros(n, np.float32); y[:min(n, len(x))] = x[:n]
    return y


def voice_tracks(tl, vo_en, vo_ru, n_full, langs):
    L = tl['lines']
    en_spans = [(l['t'], l['end'], l['fx']) for l in L if l.get('fx') and l.get('found_en', True)]
    ru_start = {}
    for g in tl.get('dub', []):
        i, j = g['lines']; ru_start[i] = g['ru_start']
    ru_spans = []
    for l in L:
        if not l.get('fx'): continue
        a = ru_start.get(l['i'], l['t']); d = l['ru_src'][1] - l['ru_src'][0] if 'ru_src' in l else l['end'] - l['t']
        ru_spans.append((a, a + max(0.4, d), l['fx']))
    out = {}
    if 'en' in langs: out['en'] = apply_line_fx(load_vo(vo_en, n_full), en_spans)
    if 'ru' in langs: out['ru'] = apply_line_fx(load_vo(vo_ru, n_full), ru_spans)
    return out


# ============================================================================ placeholder score
def placeholder_score(cues, dur):
    """D-A drone with an Eb rub, following the intensity curve; hits, risers and silences from the events. Only for
    testing the mix while audio/score.py is missing."""
    n = int(dur * SR); t = np.arange(n) / SR
    iv = np.array(cues.get('intensity') or [[0, 0.4], [dur, 0.4]], float)
    I = np.interp(t, iv[:, 0], iv[:, 1]).astype(np.float32)
    rng = np.random.default_rng(5)
    def saw(f, det=0.0):
        ph = np.cumsum(np.full(n, f * (1 + det))) / SR
        return sum(np.sin(2 * np.pi * k * ph + rng.uniform(0, 6)) / k for k in range(1, 9)).astype(np.float32)
    pad = (saw(73.42) + saw(73.42, 0.004) + 0.8 * saw(110.0, -0.003) + 0.5 * saw(146.83, 0.002)) * 0.25
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * t / 23.0)
    # crude time-varying low-pass by crossfading two fixed filters
    dark, bright = SX.lp(pad, 260, 2), SX.lp(pad, 900, 2)
    x = dark * (1 - I) + bright * I
    sub = (np.sin(2 * np.pi * 36.71 * t) * 0.5).astype(np.float32)
    rub = (saw(77.78) * 0.12 * np.clip((I - 0.55) / 0.3, 0, 1)).astype(np.float32)
    rub = SX.lp(rub, 400, 2)
    g = (10 ** ((-14 + 14 * I + 2 * lfo) / 20)).astype(np.float32)
    drone = (x + sub + rub) * g
    st = np.stack([drone * 0.95, np.roll(drone, 240) * 0.95], 1)
    hits = np.zeros((n, 2), np.float32); env = np.ones(n, np.float32)
    for e in cues.get('events', []):
        i = int(e['t'] * SR); lv = float(e.get('level', 0.7))
        if e['type'] in ('hit', 'stinger', 'braam', 'sub_drop', 'rule'):
            b = SX.st(SX.sub_boom(60, 30, 2.0, 0.2)) * lv
            b = SX.reverb(b, 'church', 0.3)
            SX.place(hits, b * 2.0, i)
        elif e['type'] == 'riser':
            L = float(e.get('len', 4.0)); m = int(L * SR)
            r = SX.sweep_bp(SX.noise(L, abs(i)), 200, 3000, 1.5) * np.linspace(0, 1, m) ** 2 * lv
            SX.place(hits, SX.st(r) * 0.6, i - m)
        elif e['type'] == 'silence':
            a, b = i, i + int(float(e.get('len', 1.7)) * SR)
            env[a:b] = 0.03
    env = SX.lp(env, 8, 1)
    return {'drone': st * env[:, None], 'hits': hits}


def score_stems(cues, dur, force_fallback=False):
    if not force_fallback:
        try:
            import importlib
            score = importlib.import_module('score')
            st = score.render(cues, dur)
            if isinstance(st, dict) and st:
                log('score.py stems:', ', '.join(st))
                return st, 'score.py'
            log('score.py returned nothing; using placeholder')
        except Exception as e:
            log('score.py unavailable or failed (%s); using placeholder drone' % repr(e)[:200])
            traceback.print_exc(limit=2)
    return placeholder_score(cues, dur), 'placeholder'


# ============================================================================ bus helpers
def fit(y, n):
    y = SX.st(np.asarray(y, np.float32))
    return y[:n] if len(y) >= n else np.pad(y, ((0, n - len(y)), (0, 0)))


def voice_activity(v, att=0.04, rel=0.35):
    """0..1 activity from the voice's envelope (10 ms RMS), for ducking and the dynamic EQ."""
    a = np.abs(v).astype(np.float64)
    e = SX.follow(a, SX.coef(att), SX.coef(rel))
    edb = SX.db(e)
    ref = np.percentile(edb[edb > -70], 90) if (edb > -70).any() else -20
    return np.clip((edb - (ref - 26)) / 14, 0, 1).astype(np.float32)


_BPV = None


def dyn_cut(x, act, depth_db):
    """Bell cut centred ~2.1 kHz (1-4.5 kHz), depth follows the voice activity: x + (g-1) * BP(x)."""
    global _BPV
    if depth_db == 0:
        return x
    if _BPV is None:
        _BPV = signal.butter(1, [1000, 4500], 'bandpass', fs=SR, output='sos')
    b = signal.sosfilt(_BPV, x, axis=0).astype(np.float32)
    b *= (10 ** (-depth_db * act / 20) - 1).astype(np.float32)[:, None]
    b += x
    return b


def gain_env(n, segs):
    """segs: [(t0, t1, dB, fade_in, fade_out)] -> multiplicative envelope (minimum of the dips)."""
    e = np.zeros(n, np.float32)
    for a, b, d, fi, fo in segs:
        i0, i1 = int(a * SR), int(b * SR)
        ia, ib = int((a - fi) * SR), int((b + fo) * SR)
        t = np.arange(max(0, ia), min(n, ib))
        if not len(t): continue
        w = np.ones(len(t), np.float32)
        up = t < i0; w[up] = np.clip((t[up] - ia) / max(1, i0 - ia), 0, 1)
        dn = t > i1; w[dn] = np.clip(1 - (t[dn] - i1) / max(1, ib - i1), 0, 1)
        w = np.sin(w * np.pi / 2) ** 2
        e[t] = np.minimum(e[t], d * w)
    return (10 ** (e / 20)).astype(np.float32)


def glue(x, thr_rel=0.0, ratio=2.0):
    """Slow RMS glue compressor on the bed bus (30 ms attack lets hit transients through). Threshold = p95 of the
    bed's 50 ms RMS + thr_rel; gain reduction capped at 3 dB."""
    p = (x[:, 0] * x[:, 0] + x[:, 1] * x[:, 1]) * 0.5
    k = int(0.05 * SR); r = np.sqrt(np.maximum(uniform_filter1d(p, k), 0)).astype(np.float32); del p
    rdb = SX.db(r); live = rdb > -60
    if not live.any():
        return x, 0.0, np.ones(len(x), np.float32)
    thr = np.percentile(rdb[live], 95) + thr_rel
    env = SX.follow(r, SX.coef(0.03), SX.coef(0.3))
    over = (20 * np.log10(np.maximum(env, 1e-9)) - thr).astype(np.float32); del env; knee = 6.0
    gr = np.where(over <= -knee / 2, 0, np.where(over >= knee / 2, over * (1 - 1 / ratio),
                                                 (1 - 1 / ratio) * (over + knee / 2) ** 2 / (2 * knee))).astype(np.float32)
    del over
    gr = np.minimum(gr, 3.0)
    g = (10 ** (-gr / 20)).astype(np.float32)
    return x * g[:, None], float(np.percentile(gr[live], 95)), g


def true_peak(y, os_=4, chunk=SR * 20):
    m = 0.0
    for a in range(0, len(y), chunk):
        u = signal.resample_poly(y[max(0, a - 64):a + chunk + 64].astype(np.float32), os_, 1, axis=0)
        m = max(m, float(np.abs(u).max()))
    return 20 * np.log10(m + 1e-12)


def tp_limit(y, ceiling_db=-1.7, look=0.005, rel=0.08, os_=4, chunk=SR * 20):
    """Look-ahead limiter on the 4x-oversampled peak: gain = backward moving average of the forward-looking minimum of
    the required gain (so it is fully down at each peak), then instant-attack / exponential release."""
    c = 10 ** (ceiling_db / 20); n = len(y); req = np.ones(n, np.float32)
    for a in range(0, n, chunk):
        lo = max(0, a - 64); seg = y[lo:a + chunk + 64].astype(np.float32)
        u = np.abs(signal.resample_poly(seg, os_, 1, axis=0)).max(1)
        m = len(seg); u = u[:m * os_].reshape(m, os_).max(1)
        # also take the neighbours (inter-sample peaks between i-1 and i)
        u = np.maximum(u, np.concatenate([[0], u[:-1]]))
        r = np.minimum(1.0, c / np.maximum(u, 1e-9))
        req[a:a + chunk] = r[a - lo:a - lo + min(chunk, n - a)]
    L = max(1, int(look * SR))
    gmin = minimum_filter1d(req, size=2 * L + 1, origin=-L)        # min over [i, i + 2L]
    gs = uniform_filter1d(gmin, size=L, origin=(L - 1) // 2)       # mean over [i - L + 1, i]
    gs = np.minimum(gs, gmin)
    gr = SX.follow((1.0 - gs).astype(np.float32), 0.0, SX.coef(rel)); del gmin
    g = (1.0 - gr).astype(np.float32)
    return y * g[:, None], float(-20 * np.log10(max(float(g.min()), 1e-6))), float((g < 10 ** (-1 / 20)).mean())


def voice_chain(v, plr=11.0):
    """Narration bus: loudness to -14 LUFS, gentle 2.5:1 compression on the loudest syllables, then a transparent
    true-peak limiter so the voice's peak-to-loudness ratio is <= plr dB (EN narration arrives at PLR 15.6 dB, which
    would otherwise make the master limiter pump on every plosive). Returns (voice, stats)."""
    L0 = SX.lufs_int(v)
    if L0 <= -70:
        return v, {}
    v = v * 10 ** ((TARGET - L0) / 20)
    e = SX.follow(np.abs(v).astype(np.float64), SX.coef(0.003), SX.coef(0.06)); edb = SX.db(e)
    thr = float(np.percentile(edb[edb > -60], 97))
    v = SX.compress(v, thr, 2.5, 0.003, 0.06, knee=6.0)
    v = v * 10 ** ((TARGET - SX.lufs_int(v)) / 20)
    y, gr, frac = tp_limit(np.stack([v, v], 1), TARGET + plr, look=0.003, rel=0.05)
    v = y[:, 0]
    v = (v * 10 ** ((TARGET - SX.lufs_int(v)) / 20)).astype(np.float32)
    return v, {'plr': round(true_peak(np.stack([v, v], 1)) - TARGET, 1), 'limit_gr_max': round(gr, 1),
               'limit_over_1dB_pct': round(100 * frac, 2)}


TILT = {63: 8.0, 125: 3.0, 250: 4.0, 500: 4.0, 2000: -7.0, 4000: -10.0, 8000: -14.0}   # AUDIO_SPEC sec. 2, rel 1 kHz


def match_tilt(m, amount=0.8, lo=-6.0, hi=2.0, probe=None):
    """Bounded auto-EQ for the score bus: measures its octave levels (rel 1 kHz) and moves them `amount` of the way
    toward the reference tilt with one-octave peaking bells, each limited to lo..hi dB (cuts only from 2 kHz up, so
    the score never brightens into the voice band). `probe`: the same music after
    the voice-keyed bell cut, so the tilt is measured as it will be heard. Returns (music, {Hz: dB})."""
    x = (m if probe is None else probe).mean(1)
    if len(x) > 240 * SR:
        x = x[::max(1, len(x) // (240 * SR))]
    f, P = signal.welch(x, SR, nperseg=8192)
    lev = lambda c: 10 * np.log10(P[(f >= c / 1.414) & (f < c * 1.414)].sum() + 1e-30)
    ref = lev(1000)
    corr = {c: float(np.clip(amount * (t - (lev(c) - ref)), lo, hi if c < 2000 else 0.0)) for c, t in TILT.items()}
    bands = [('peak', c, g, 1.41) for c, g in corr.items() if abs(g) > 0.3]
    return (SX.eq(m, *bands) if bands else m), {c: round(g, 1) for c, g in corr.items()}


def level_music(m, sil, up_max=9.0, lo_rel=-4.5, hi_rel=6.5, r_up=0.7, r_dn=0.5):
    """Slow two-way leveler for the score bus (non-causal 2 s smoothing, so no pumping): passages more than 4.5 LU
    under the score's own median are lifted (70%, at most +9 dB), passages more than 6.5 LU over it are compressed 2:1.
    Near-silence (< median - 30 LU) and the authored silences (plus 4 s after, where the music must come back quieter)
    are never lifted. Returns (music, gain curve dB at 20 Hz)."""
    hop = 0.05
    b = SX._blocks(m, 1.0, hop); l = -0.691 + 10 * np.log10(b + 1e-20)
    live = l > -70
    if not live.any():
        return m, np.zeros(1)
    med = float(np.median(l[live]))
    g = np.where(l < med + lo_rel, np.minimum(up_max, (med + lo_rel - l) * r_up), 0.0)
    g = np.where(l < med - 30, 0.0, g)
    g = np.where(l > med + hi_rel, -(l - med - hi_rel) * r_dn, g)
    tb = np.arange(len(l)) * hop + 0.5
    for a, e in sil:
        k = (tb > a - 0.3) & (tb < e + 4.0)
        g[k] = np.minimum(g[k], 0.0)
    g = uniform_filter1d(g, size=int(2.0 / hop))
    gs = np.interp(np.arange(len(m)) / SR, tb, g).astype(np.float32)
    return m * (10 ** (gs / 20))[:, None], g


def short_term_rel(x, ref, win=0.4, hop=0.1):
    return -0.691 + 10 * np.log10(SX._blocks(x, win, hop) + 1e-20) - ref


# ============================================================================ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('timeline'); ap.add_argument('vo_en'); ap.add_argument('vo_ru'); ap.add_argument('cues')
    ap.add_argument('out')
    ap.add_argument('--t0', type=float, default=0.0); ap.add_argument('--t1', type=float, default=None)
    ap.add_argument('--langs', default='en,ru'); ap.add_argument('--fallback', action='store_true')
    ap.add_argument('--bed-rel', type=float, default=-13.0, help='reference integrated bed level (report and cap)')
    ap.add_argument('--bed-p50', type=float, default=-16.0, help='target bed 3 s short-term median, LU rel voice')
    ap.add_argument('--no-stems', action='store_true')
    ap.add_argument('--voice-plr', type=float, default=11.5)
    ap.add_argument('--music-width', type=float, default=0.7)
    A = ap.parse_args()
    T0 = time.time()
    langs = [s for s in A.langs.split(',') if s]
    os.makedirs(A.out, exist_ok=True)
    tl = json.load(open(A.timeline))
    sfx_cues = json.load(open(os.path.join(A.cues, 'sfx_cues.json')))
    mpath = os.path.join(A.cues, 'music_cues.json')
    mcues = json.load(open(mpath)) if os.path.exists(mpath) else {'duration': tl['duration_en'] + 2.5, 'intensity': [],
                                                                  'events': []}
    full = max(tl['duration_en'] + 2.5, float(mcues.get('duration') or 0))
    t0 = A.t0; t1 = min(full, A.t1) if A.t1 else full
    dur = t1 - t0; N = int(round(dur * SR)); i0 = int(round(t0 * SR))
    log(f'window {t0:.1f}-{t1:.1f} s ({dur:.1f} s), {len(sfx_cues)} sfx cues, langs {langs}')

    # ---------------- voice
    nfull = int(round(full * SR)) + SR
    vo = voice_tracks(tl, A.vo_en, A.vo_ru, nfull, langs)
    vstats = {}
    for k in vo:
        v = vo[k][i0:i0 + N]; v = np.pad(v, (0, N - len(v)))
        vo[k], vstats[k] = voice_chain(v, A.voice_plr)
    log('voice chain:', vstats)
    key = vo['en'] if 'en' in vo else vo[langs[0]]

    # ---------------- SFX
    SX.reset()
    buses = {b: np.zeros((N, 2), np.float32) for b in ('beds', 'events', 'hits')}
    hit_times = []; counts = {'hits': 0, 'events': 0, 'beds': 0}; skipped = []
    order = sorted(range(len(sfx_cues)), key=lambda k: (sfx_cues[k]['t'], k))
    tsfx = time.time()
    for rank, k in enumerate(order):
        c = sfx_cues[k]; name = c['name']
        if name not in SX.RECIPES:
            skipped.append(name); continue
        params = dict(c.get('params') or {})
        space = c.get('space') or params.pop('space', None)
        params.pop('space', None)
        dur_hint = float(params.get('dur', 0) or 0)
        tt = float(c['t']) - t0
        if dur_hint and tt + dur_hint > dur + 2 and name in SX.BEDS:      # window renders: no need for the rest
            params['dur'] = max(1.0, min(dur_hint, dur + 2 - tt))
        if tt > dur + 0.5 or tt + max(dur_hint, 30.0) < 0:
            continue
        try:
            y, pre = SX.render_event(name, seed=int(c.get('seed', rank)), space=space, **params)
        except Exception as e:
            log('SFX failed', name, repr(e)[:160]); skipped.append(name); continue
        y = y * 10 ** (float(c.get('gain_db', 0.0)) / 20)
        if c.get('pan'):
            y = SX.pan(y, float(c['pan']))
        b = 'hits' if name in SX.HITS else 'beds' if name in SX.BEDS else 'events'
        SX.place(buses[b], y, int(round((tt - pre) * SR)))
        if 0 <= tt <= dur:
            counts[b] += 1
            if name in SX.HITS or name == 'knock_door':
                hit_times.append(tt)
    log(f'sfx rendered in {time.time() - tsfx:.1f} s: {counts}' + (f', skipped {sorted(set(skipped))}' if skipped else ''))

    # ---------------- music
    # windowed renders: the score starts at a pre-roll (up to 30 s before t0) so swells and tails that began before
    # the window are there, and only events at t >= 0 are passed; the pre-roll is cut off afterwards
    ts = max(0.0, t0 - 30.0) if t0 > 0 else 0.0
    sdur = t1 - ts; npre = int(round((t0 - ts) * SR))
    mc = dict(mcues)
    mc['duration'] = sdur
    if mcues.get('intensity'):
        iv = np.array(mcues['intensity'], float)
        mc['intensity'] = [[0.0, float(np.interp(ts, iv[:, 0], iv[:, 1]))]] + \
                          [[p[0] - ts, p[1]] for p in mcues['intensity'] if 0 < p[0] - ts < sdur] + \
                          [[sdur, float(np.interp(t1, iv[:, 0], iv[:, 1]))]]
    mc['events'] = [dict(e, t=e['t'] - ts) for e in mcues.get('events', []) if 0 <= e['t'] - ts < sdur]
    tm = time.time()
    stems, score_src = score_stems(mc, sdur, A.fallback)
    stem_names = list(stems)
    music = np.zeros((N, 2), np.float32); mhits = np.zeros((N, 2), np.float32)
    for k in list(stems):
        s = fit(stems.pop(k), npre + N)[npre:]
        if k == 'hits':
            mhits += s                       # music hits: never ducked or EQ'd
        else:
            music += s
        del s
    del stems
    mc['events'] = [dict(e, t=e['t'] - (t0 - ts)) for e in mc['events']]   # back to window time
    log(f'music ({score_src}) in {time.time() - tm:.1f} s, stems {stem_names}')

    # ---------------- bed automation shared by both languages
    # score.py already applies silences and pre-hit ducks for its own events; the placeholder does silences only.
    # So: music gets pre-hit dips for SFX-cue hits; SFX beds get silences + dips for every hit.
    sil = [(e['t'], e['t'] + float(e.get('len', 1.7)), -9.0, 0.08, 0.4) for e in mc['events'] if e['type'] == 'silence']
    mus_hits = [e['t'] for e in mc['events'] if e['type'] in ('hit', 'stinger', 'braam', 'sub_drop', 'rule')]
    dip = lambda ts: [(h - 0.05, h, -8.0, 0.4, 0.6) for h in ts]
    autom = gain_env(N, dip(hit_times))
    autom_b = gain_env(N, sil + dip(hit_times + mus_hits))
    # score bus: corrective EQ toward the AUDIO_SPEC octave tilt (less 100-160 Hz mud), moderate width, leveler
    music, tilt = match_tilt(music, probe=dyn_cut(music, voice_activity(key), 5.0))
    log('score tilt EQ (dB):', tilt)
    music = SX.width(music, A.music_width); mhits = SX.width(mhits, min(1.0, A.music_width + 0.2))
    music, lev = level_music(music, [(a, b) for a, b, *_ in sil])
    log(f'music leveler: gain p5/p50/p95 {np.percentile(lev, 5):+.1f} / {np.percentile(lev, 50):+.1f} / {np.percentile(lev, 95):+.1f} dB')
    n_sil = sum(1 for e in mc['events'] if e['type'] == 'silence' and 0 <= e['t'] <= dur)

    def bed_for(act, gm):
        dm = (10 ** (-3.0 * act / 20)).astype(np.float32)
        m = dyn_cut(music, act, 5.0); m *= (dm * autom * np.float32(gm))[:, None]
        m += mhits * np.float32(gm)
        s = dyn_cut(buses['beds'], act, 5.0); s *= (dm * autom_b)[:, None]; del dm
        e = dyn_cut(buses['events'], act, 2.0); e *= (10 ** (-1.5 * act / 20)).astype(np.float32)[:, None]
        s += e; del e
        s += buses['hits']
        bed, gr, gg = glue(m + s)
        m *= gg[:, None]; s *= gg[:, None]
        return bed, m, s, gr

    # ---------------- solve the music gain on the EN key so the bed sits at voice + bed_rel
    # Target: the bed's typical level, its 3 s short-term median, at voice + bed_p50 (-16 LU: the three references
    # re-measured with true per-channel K-weighting give -15.3 / -16.1 / -16.5; AUDIO_SPEC's short-term numbers come
    # from analysis/measure.py, whose kweight() filters across channels, so they read about 4 dB hot), while the
    # integrated bed stays at or under voice + bed_rel + 1.5 (references: -12.5 / -12.8 / -13.4).
    act_key = voice_activity(key)
    Lv = SX.lufs_int(key)
    def bstat(b):
        st3 = -0.691 + 10 * np.log10(SX._blocks(b, 3.0, 1.0) + 1e-20)
        return SX.lufs_int(b) - Lv, float(np.median(st3[st3 > -70])) - Lv if (st3 > -70).any() else -70.0
    Lm0 = SX.lufs_int(music + mhits)
    gm = 10 ** ((Lv + A.bed_rel - 1.0 - Lm0) / 20) if Lm0 > -70 else 1.0
    for it in range(5):
        bed, _m, _s, gr = bed_for(act_key, gm); del _m, _s
        Li, P50 = bstat(bed); del bed
        err = min(A.bed_p50 - P50, (A.bed_rel + 1.5) - Li)
        log(f'  music gain iter {it}: music {20 * np.log10(gm):+.1f} dB, bed integrated {Li:+.2f} LU, p50 {P50:+.2f} LU rel voice')
        if abs(err) < 0.2:
            break
        gm *= 10 ** (err * 1.1 / 20)
    # keep the music clearly present: music alone within voice -17 .. -10 LU
    Lm = SX.lufs_int((music + mhits) * gm) - Lv
    if Lm < -17: gm *= 10 ** ((-17 - Lm) / 20)
    if Lm > -10: gm *= 10 ** ((-10 - Lm) / 20)

    report = {'window': [t0, t1], 'score': score_src, 'music_gain_db': round(20 * np.log10(gm), 2),
              'sfx_counts': counts, 'silences': n_sil, 'langs': {}}
    stem_dir = os.path.join(A.out, 'stems'); os.makedirs(stem_dir, exist_ok=True)
    for lang in langs:
        v = vo[lang]
        act = act_key if lang == langs[0] and lang == 'en' else voice_activity(v)
        bed, m_out, s_out, gr = bed_for(act, gm)
        vst = np.stack([v, v], 1)
        mix = vst + bed
        gdb = TARGET - SX.lufs_int(mix); ceiling = -1.7; y = None
        for it in range(6):
            y = None
            y, lim_db, lim_frac = tp_limit(mix * np.float32(10 ** (gdb / 20)), ceiling)
            Lo = SX.lufs_int(y); tp = true_peak(y)
            if tp > -1.5 and it < 5:
                ceiling -= (tp + 1.5) + 0.05; continue
            if abs(Lo - TARGET) <= 0.1 or it == 5:
                break
            gdb += TARGET - Lo
        del mix
        g = np.float32(10 ** (gdb / 20))
        sf.write(os.path.join(A.out, f'mix_{lang}.wav'), y, SR, subtype='PCM_24'); del y
        # loudness is measured unscaled and shifted by the master gain (no full-length temporaries)
        Lv0 = SX.lufs_int(vst); Lvv = Lv0 + gdb
        vb = short_term_rel(vst, Lv0); bb = short_term_rel(bed, Lv0)
        speech = vb > -20
        st3 = short_term_rel(bed, Lv0, 3.0, 0.1)
        r = {'mix_lufs': round(Lo, 2), 'true_peak_dbtp': round(tp, 2), 'voice_lufs': round(Lvv, 2),
             'voice_rel_mix': round(Lvv - Lo, 2), 'bed_rel_voice': round(SX.lufs_int(bed) - Lv0, 2),
             'music_rel_voice': round(SX.lufs_int(m_out) - Lv0, 2),
             'sfx_rel_voice': round(SX.lufs_int(s_out) - Lv0, 2),
             'bed_speech_median': round(float(np.median(bb[speech])), 1) if speech.any() else None,
             'bed_gap_median': round(float(np.median(bb[~speech])), 1) if (~speech).any() else None,
             'bed_st3s_p10_p50_p90_K': [round(float(np.percentile(st3, q)), 1) for q in (10, 50, 90)],
             'bed_lra_K': round(float(np.percentile(st3[st3 > -60], 95) - np.percentile(st3[st3 > -60], 10)), 1),
             'music_present_pct': round(100 * float((short_term_rel(m_out, Lv0) > -20).mean()), 1),
             'glue_gr_p95_db': round(gr, 2), 'limiter_max_gr_db': round(lim_db, 2),
             'limiter_over_1dB_pct': round(100 * lim_frac, 2), 'master_gain_db': round(float(gdb), 2)}
        del bed
        report['langs'][lang] = r
        log(lang, json.dumps(r))
        if not A.no_stems:
            vst *= g; sf.write(os.path.join(stem_dir, f'voice_{lang}.wav'), vst, SR, subtype='FLOAT')
            if lang == langs[0]:
                m_out *= g; sf.write(os.path.join(stem_dir, 'music.wav'), m_out, SR, subtype='FLOAT')
                s_out *= g; sf.write(os.path.join(stem_dir, 'sfx.wav'), s_out, SR, subtype='FLOAT')
        del vst, m_out, s_out
    mins = dur / 60
    report['per_min'] = {'hits': round((counts['hits'] + sum(1 for e in mc['events'] if e['type'] in ('hit', 'stinger', 'braam')
                                                              and 0 <= e['t'] <= dur)) / mins, 2),
                         'sfx_events': round(counts['events'] / mins, 2), 'silences': round(n_sil / mins, 2)}
    report['seconds'] = round(time.time() - T0, 1)
    import resource
    report['peak_rss_mb'] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    json.dump(report, open(os.path.join(A.out, 'mix_report.json'), 'w'), indent=1)
    log('done in %.1f s, peak RSS %d MB' % (report['seconds'], report['peak_rss_mb']))


if __name__ == '__main__':
    main()
