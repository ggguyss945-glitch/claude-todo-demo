"""EP01 mixer: the owner's voice on top + SFX at the timeline's cue times + ambience beds -> 48 kHz stereo WAV.

    python3 -I mix.py [--profile primary|bible|standard|full] [--range T0 T1] [--out DIR] [--compare REF.wav]
                      [--music MUSIC.wav] [--cap N] [--no-stems]

Profiles: bible (default) = the board's primary cues + the layers that belong to them (13 events/min, the bible's
6-12/min ceiling region); standard = + p2 sweeteners while no sweetener has more than --cap events within +-15 s;
full = every cue in the catalog; primary = primary cues only.

Reads (as data): episodes/ep01/timeline.json (shots, events, sfx strings), episodes/ep01/word_onsets.json (sentence
starts), sound/sfx_map.json (catalog gains; rebuild with catalog.py), the owner's VO (timeline.audio.voice) and the
extracted Epidemic files. Writes into --out (default <scratch>/out): ep01_mix.wav (master, 24-bit), stems
ep01_voice.wav / ep01_sfx.wav / ep01_beds.wav (pre-limiter, same gain staging), ep01_mix_report.json; and into this
folder: cue_sheet.json (every resolved placement), cue_times.json (multi-hit times for the picture),
music_cues.json (the voice pauses where the owner's music should drop).

Voice: 24 kHz -> 48 kHz (exact 2x polyphase), HPF 60 Hz, dual-mono; a phrase leveler sets every phrase group
(sentences merged to >= 2.5 s) to -16 LUFS (BS.1770, gated), within +-3 dB of the whole-take gain, changing gain only
in the gaps between groups; group 0 is measured on the approved test's window (0.20-3.42 s), so 0-3.40 s is the test.
SFX: placed at event + offset - sync with the catalog gain; the non-approved SFX bus is ducked (200 Hz-5 kHz only) when its
300-4000 Hz band comes within 12 dB of the voice's (attack 10 ms, release 150 ms, max 10 dB): the voice is never masked.
Beds: one per shot (rules in bed_for_shot), 30 ms crossfades on the cuts, continuous source position.
Master: sum, 10 ms end fade, true-peak limiter at -1.2 dBTP (the test's). Music: none (the owner adds it, about 8 LU
under the voice); --music lays a file in at -24 LUFS with the planned drops for a preview only.
"""
import os, sys, re, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import soundfile as sf
import pyloudnorm as pyln
from scipy.signal import resample_poly, butter, sosfilt, sosfiltfilt
from scipy.ndimage import minimum_filter1d, maximum_filter1d
import catalog as C
import synth as S

SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))
EP = os.path.dirname(HERE)                                # episodes/ep01
TIMELINE = os.path.join(EP, 'timeline.json')
WORDS = os.path.join(EP, 'word_onsets.json')
meter = pyln.Meter(SR)
VOICE_TARGET = -16.0
APPROVED_WIN = (0.20, 3.42)                              # the test's voice calibration window (test5 mix_test5_v3.py)


def fade_w(n):
    return 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, n))


# ================================================================================================ voice
def sentences(words, env_t, env_db):
    """Sentences from word_onsets (punctuation), each with its onset and the end of its voice energy (> -45 dB)."""
    out, cur = [], []
    for w in words:
        cur.append(w)
        if w['w'].rstrip('"\'').endswith(('.', '!', '?')): out.append(cur); cur = []
    if cur: out.append(cur)
    res = []
    for i, s in enumerate(out):
        t0 = s[0]['onset']; t1 = out[i + 1][0]['onset'] if i + 1 < len(out) else env_t[-1]
        m = (env_t >= t0) & (env_t < t1) & (env_db > -45)
        te = env_t[m][-1] + 0.01 if m.any() else t1
        res.append(dict(t0=t0, t1=te, next=t1, text=' '.join(w['w'] for w in s)))
    return res


def voice_track(path, words, n_total):
    v24, vsr = sf.read(path)
    if v24.ndim == 2: v24 = v24.mean(1)
    assert vsr == 24000, vsr
    v = resample_poly(v24, 2, 1)
    v = sosfilt(butter(2, 60, 'hp', fs=SR, output='sos'), v)
    v = np.pad(v, (0, max(0, n_total - len(v))))[:n_total]
    st = np.stack([v, v], 1)
    hop = SR // 100; k = len(v) // hop
    env = 20 * np.log10(np.sqrt((v[:k * hop].reshape(k, hop) ** 2).mean(1)) + 1e-9)
    et = np.arange(k) / 100.0
    sents = sentences(words, et, env)
    L_all = meter.integrated_loudness(st)
    g_base = VOICE_TARGET - L_all
    groups, cur = [], None
    for s in sents:
        if cur is None: cur = dict(t0=s['t0'], t1=s['t1'], next=s['next'], text=s['text'])
        else: cur.update(t1=s['t1'], next=s['next'], text=cur['text'] + ' ' + s['text'])
        if cur['t1'] - cur['t0'] >= 2.5: groups.append(cur); cur = None
    if cur:
        if groups and cur['t1'] - cur['t0'] < 1.0: groups[-1].update(t1=cur['t1'], next=cur['next'], text=groups[-1]['text'] + ' ' + cur['text'])
        else: groups.append(cur)
    for i, g in enumerate(groups):
        a, b = (APPROVED_WIN if i == 0 and g['t0'] <= APPROVED_WIN[0] + 0.15 else (g['t0'], g['t1']))
        L = meter.integrated_loudness(st[int(a * SR):int(b * SR)])
        g.update(win=[round(a, 3), round(b, 3)], lufs_raw=round(L, 2),
                 gain_db=round(float(np.clip(VOICE_TARGET - L, g_base - 3, g_base + 3)), 3))
    # gain curve: constant per group, ramps only between a group's last voice and the next group's first word
    gc = np.full(n_total, groups[0]['gain_db'])
    for i in range(1, len(groups)):
        a, b = groups[i - 1]['t1'], groups[i]['t0'] - 0.005
        if b - a < 0.03: m = 0.5 * (a + b); a, b = m - 0.015, m + 0.015
        i0, i1 = int(a * SR), int(b * SR)
        gc[i0:i1] = groups[i - 1]['gain_db'] + (groups[i]['gain_db'] - groups[i - 1]['gain_db']) * fade_w(i1 - i0)
        gc[i1:] = groups[i]['gain_db']
    out = st * (10 ** (gc / 20))[:, None]
    info = dict(raw_integrated=round(L_all, 2), base_gain_db=round(g_base, 2), groups=groups)
    return out, info, sents


# ================================================================================================ cues
TOK = re.compile(r'\b([A-Z][A-Z0-9_]+)\b(\s*\((soft|distant)\))?')


def parse_tokens(s):
    out = []
    if not s: return out
    if 'distant rumble' in s: out.append('RUMBLE_FAR')
    for m in TOK.finditer(s):
        cid = m.group(1) + ({'soft': '_SOFT', 'distant': '_FAR'}[m.group(3)] if m.group(3) else '')
        if cid in C.CUES and cid not in out: out.append(cid)
    return out


def layer_parent(cid, shot):
    lo = C.CUES[cid].get('layer_of')
    if isinstance(lo, dict): return lo.get(shot)
    return lo


def resolve_cues(tl, profile='bible', cap_per_30s=9, override_times=None):
    """Timeline -> placements [{cue, t, times, shot, word, prio, layer_of, rank, why}]."""
    shots = tl['shots']; P = []
    placed = lambda cid, t: any(p['cue'] == cid and abs(p['t'] - t) < 6.0 for p in P)
    for si, s in enumerate(shots):
        p = s['params']; sid = p['id']; st, en = s['start'], s['end']
        evs = sorted(p.get('events') or [], key=lambda e: e['t'])
        from_events = set()
        for e in evs:
            for cid in parse_tokens(e.get('sfx')):
                from_events.add(cid)
                P.append(dict(cue=cid, t=e['t'], shot=sid, word=e.get('word'), why='event: ' + e['what'][:70], ev=e, shot_obj=s, si=si))
        for cid in parse_tokens(' '.join(p.get('sfx_cues') or [])):
            if cid in from_events or placed(cid, st): continue
            kind = (C.CUES[cid].get('rule') or {}).get('kind')
            if kind == 'shot_start': t = st + C.CUES[cid]['rule'].get('after', 0.0)
            elif kind == 'shot_at':
                m = re.search(r'at (\d+\.\d+)', ' '.join(p.get('sfx_cues') or [])); t = float(m.group(1)) if m else st
            elif kind == 'hops':
                bonk = [e['t'] for e in evs if 'BONK' in (e.get('sfx') or '')]; tb = bonk[0] if bonk else en
                t = tb - 0.18 - 0.22 * 4
            else:
                t = evs[0]['t'] if evs else st + 0.1
            P.append(dict(cue=cid, t=t, shot=sid, word=None, why='shot cue: ' + ', '.join(p.get('sfx_cues') or [])[:70], ev=None, shot_obj=s, si=si))
        for cid, c in C.CUES.items():
            ex = c.get('extra')
            if ex and ex['shot'] == sid:
                for e in evs:
                    if (e.get('word') or '').lower() == ex['word']:
                        P.append(dict(cue=cid, t=e['t'], shot=sid, word=e.get('word'), why='extra event: ' + e['what'][:70], ev=e, shot_obj=s, si=si))
    # multi-time rules
    for q in P:
        c = C.CUES[q['cue']]; rule = c.get('rule') or {}; kind = rule.get('kind'); s = q['shot_obj']; p = s['params']
        evs = sorted(p.get('events') or [], key=lambda e: e['t'])
        q['times'] = None
        if kind == 'shot_events':
            q['times'] = [e['t'] for e in evs if e['t'] >= q['t'] - 1e-6]
        elif kind == 'cascade':
            lit = [e['t'] for e in evs if e['t'] > q['t'] and (e.get('word') or '').lower() == 'lit']
            t1 = lit[0] if lit else q['t'] + 0.6
            k = max(1, int(round((t1 - q['t']) / 0.225)))
            r = S.rng('tinks-gaps'); gaps = r.uniform(0.15, 0.3, k); gaps *= (t1 - q['t']) / gaps.sum()
            q['times'] = [round(q['t'] + x, 4) for x in np.concatenate([[0], np.cumsum(gaps)])]
        elif kind == 'feet':
            if 'plant' in ((q['ev'] or {}).get('what') or ''):
                q['variant'] = 'feet_plant'
            else:
                ts, t = [], q['t']
                while t < s['end'] - 0.1: ts.append(round(t, 4)); t += 0.25
                q['times'] = ts
        elif kind == 'steps':
            stop = None
            for s2 in tl['shots'][q['si'] + 1:q['si'] + 4]:
                if any('STEP_WET stops' in x for x in (s2['params'].get('sfx_cues') or [])):
                    se = [e['t'] for e in (s2['params'].get('events') or []) if 'stop' in e['what'].lower()]
                    stop = se[0] if se else s2['start'] + 0.4
            if stop:
                ts, t = [], q['t']
                while t < stop - 0.2: ts.append(round(t, 4)); t += 0.44
                ts.append(round(stop, 4)); q['times'] = ts
            else:
                q['times'] = [q['t']]
        elif kind == 'deflate':
            n = rule.get('n', 6); gap = rule.get('gap', 0.15)
            while n > 1 and q['t'] + gap * (n - 1) > s['end'] - 0.05: n -= 1
            q['times'] = [round(q['t'] + gap * i, 4) for i in range(n)]; q['n'] = n
        elif kind == 'hops':
            q['times'] = [round(q['t'] + 0.22 * i, 4) for i in range(5)]
        if override_times and q['cue'] in override_times:
            q['times'] = override_times[q['cue']]['times']; q['t'] = q['times'][0]
        q['prio'] = c['prio']; q['rank'] = c.get('rank', 99); q['layer_of'] = layer_parent(q['cue'], q['shot'])
    # profile + density cap (events = non-layer placements; a multi-hit cue is one event)
    # profiles: 'primary' = the board's primary cues only; 'bible' (default) = primary + the layers that belong to a
    # primary event (no extra events: the bible's 6-12 events/min, the board's ~20 primary events); 'standard' = bible +
    # p2 sweeteners by rank while no sweetener has more than `cap` events within +-15 s; 'full' = every cue.
    parents = {q['cue'] for q in P if q['prio'] == 1}
    keep, dropped = [], []
    for q in P:
        if profile == 'full': keep.append(q); continue
        if q['prio'] == 1: keep.append(q); continue
        if profile == 'primary': dropped.append(q); continue
        if q['layer_of'] and q['layer_of'] in parents and q['prio'] == 2: keep.append(q); continue
        if profile == 'standard' and q['prio'] == 2: continue      # candidates, below
        dropped.append(q)
    if profile == 'standard':
        cands = sorted([q for q in P if q['prio'] == 2 and not (q['layer_of'] and q['layer_of'] in parents)], key=lambda q: (q['rank'], q['t']))
        for q in cands:
            ts = np.array([x['t'] for x in keep if not x['layer_of']])
            if (np.abs(ts - q['t']) < 15).sum() + 1 <= cap_per_30s: keep.append(q)
            else: dropped.append(q)
    keep.sort(key=lambda q: q['t'])
    return keep, dropped


def place_cue(bus, q, gmap, t_lo, t_hi):
    """Render placement q and add it to bus (which covers episode time [t_lo, t_hi))."""
    clip, sync, c = C.render_cue(q['cue'], q.get('times'), q['shot'])
    if q.get('variant') == 'feet_plant':
        clip = C._fades(C._filt(S.to_st(C.design('feet_plant')), c.get('hp'), c.get('lp')), c.get('fin'), c.get('fout'))
    g = gmap[q['cue']]['gain_db']
    start = (q['times'][0] if q.get('times') else q['t']) + c.get('offset', 0.0) - sync
    q['start'] = round(start, 4); q['end'] = round(start + len(clip) / SR, 4); q['gain_db'] = g
    i = int(round((start - t_lo) * SR))
    x = clip * 10 ** (g / 20)
    if i < 0: x = x[-i:]; i = 0
    j = min(len(bus), i + len(x))
    if j > i: bus[i:j] += x[:j - i]


# ================================================================================================ beds
OVERRIDE_BED = {'s26': 'A_HALL', 's48': 'A_NIGHT_CAB', 's66': 'A_ROOM_OLD', 's67': 'A_ROOM_OLD', 's93': 'A_DUSK'}


def bed_for_shot(p):
    sid = p['id']; tod = (p.get('tod') or '').lower(); loc = p.get('loc') or ''
    if sid in OVERRIDE_BED: return OVERRIDE_BED[sid]
    if 'blue hour' in tod: return 'A_DUSK>A_NIGHT'
    if 'interior' in tod or loc in ('grandma_room', 'hero_room', 'hall'):
        if 'sepia' in tod or 'b&w' in tod: return 'A_ROOM_OLD'
        return 'A_ROOM_DAY' if 'day' in tod else 'A_ROOM'
    if 'b&w' in tod: return 'A_NIGHT_BW'
    if 'sepia' in tod: return 'A_NIGHT_OLD'
    if 'dawn' in tod: return 'A_DAWN'
    if 'dusk' in tod: return 'A_DUSK'
    if 'day' in tod: return 'A_DAY'
    return 'A_NIGHT'


def bed_envelopes(tl, n, t_lo):
    """Per-bed gain envelopes over [t_lo, t_lo + n/SR): 1 inside its shots, 30 ms raised-cosine crossfades at the cuts,
    plus the automation the board asks for (s27 silence beat, s97 dusk -> night into the loop)."""
    env = {}; sched = []
    t = t_lo + np.arange(n) / SR
    X = 0.015
    for s in tl['shots']:
        b = bed_for_shot(s['params']); sched.append((s['params']['id'], s['start'], s['end'], b))
    def ramp(t, a, b):   # 0 before a, 1 after b
        return np.clip(0.5 - 0.5 * np.cos(np.pi * np.clip((t - a) / max(b - a, 1e-6), 0, 1)), 0, 1)
    runs = []            # contiguous shots with the same bed are one run (no crossfade inside a run)
    for sid, a, b, name in sched:
        if runs and runs[-1][3] == name and '>' not in name and abs(runs[-1][2] - a) < 1e-6:
            runs[-1] = (runs[-1][0], runs[-1][1], b, name)
        else:
            runs.append((sid, a, b, name))
    for sid, a, b, name in runs:
        parts = [name] if '>' not in name else name.split('>')
        for k, nm in enumerate(parts):
            e = env.setdefault(nm, np.zeros(n))
            lo = ramp(t, a - X, a + X) if a > 0 else ramp(t, 0.0, 0.06)
            hi = 1 - ramp(t, b - X, b + X) if b < tl['duration'] - 1e-6 else np.ones(n)
            w = lo * hi
            if '>' in name:   # s97: dusk fades out over the shot, the night fades in and holds to the last frame
                w = w * ((1 - ramp(t, a + 0.1, b - 0.4)) if k == 0 else ramp(t, a, a + 0.8))
            env[nm] = np.maximum(e, w)
    # s27 silence beat: the night drops ~14 dB from the pause after "empty" until the door bangs (the s28 cut)
    for s in tl['shots']:
        cues = ' '.join(s['params'].get('sfx_cues') or [])
        m = re.search(r'near-silence from (\d+\.\d+)', cues)
        if m and 'A_NIGHT' in env:
            a = float(m.group(1)); b = s['end']
            dip = 1 - (1 - 10 ** (-14 / 20)) * ramp(t, a, a + 0.3) * (1 - ramp(t, b - 0.02, b))
            env['A_NIGHT'] *= dip
    return env, sched


# ================================================================================================ dynamics
def band_env(x, lo=300, hi=4000, win=0.03, hop=0.005):
    y = sosfilt(butter(2, [lo, hi], 'bandpass', fs=SR, output='sos'), x)
    w, h = int(win * SR), int(hop * SR)
    c = np.concatenate([[0], np.cumsum(y ** 2)])
    idx = np.arange(0, max(1, len(y) - w), h)
    return 10 * np.log10((c[idx + w] - c[idx]) / w + 1e-14), (idx + w // 2) / SR


def duck(sfx, voice, margin=12.0, max_gr=10.0, att=0.010, rel=0.150):
    """Voice-keyed SFX ducker on 200 Hz-5 kHz only, so the SFX speech band never comes within `margin` dB of the voice band."""
    ev, tt = band_env(voice.mean(1)); es, _ = band_env(sfx.mean(1))
    ev = maximum_filter1d(ev, size=31)                          # 150 ms hold: follow phrases, not syllables
    active = ev > -38
    over = np.clip(es - (ev - margin), 0, max_gr) * active
    over = maximum_filter1d(over, size=3, origin=-1)              # 10 ms look-ahead
    g = np.zeros_like(over); cur = 0.0; h = 0.005
    aa, ar = np.exp(-h / att), np.exp(-h / rel)
    for i, o in enumerate(over):
        cur = o + (cur - o) * (aa if o > cur else ar); g[i] = cur
    gr = np.interp(np.arange(len(sfx)) / SR, tt, g, left=0, right=0)
    low = sosfiltfilt(butter(2, 200, 'lp', fs=SR, output='sos'), sfx, axis=0)       # sub/body: untouched
    air = sosfiltfilt(butter(2, 5000, 'hp', fs=SR, output='sos'), sfx, axis=0)      # sparkle/air: untouched
    out = low + air + (sfx - low - air) * (10 ** (-gr / 20))[:, None]              # only 200 Hz-5 kHz is ducked
    return out, dict(max_gr_db=round(float(g.max()), 2), pct_time_gr_over_1db=round(float((g > 1).mean() * 100), 2))


def true_peak_db(x, chunk=SR * 4):
    m = 0.0
    for i in range(0, len(x), chunk):
        seg = x[max(0, i - 64):i + chunk + 64]
        m = max(m, np.abs(resample_poly(seg, 4, 1, axis=0)).max())
    return 20 * np.log10(m + 1e-12)


def limiter(x, ceiling_db=-1.2, look=0.004, release=0.08):
    """The test's true-peak limiter (instant attack via look-ahead minimum, exponential release), chunked."""
    pk = np.empty(len(x))
    for i in range(0, len(x), SR * 4):
        seg = x[i:i + SR * 4]
        up = np.abs(resample_poly(seg, 4, 1, axis=0)).max(1)
        up = up[:len(seg) * 4].reshape(-1, 4).max(1)
        pk[i:i + len(seg)] = np.maximum(up[:len(seg)], np.abs(seg).max(1))
    c = 10 ** (ceiling_db / 20)
    need = np.minimum(1.0, c / np.maximum(pk, 1e-12))
    L = int(look * SR)
    need = minimum_filter1d(need, size=2 * L + 1, mode='nearest')
    g = np.ones_like(need)
    idx = np.where(need < 1.0)[0]
    if len(idx):
        a = np.exp(-1 / (release * SR)); cur = 1.0
        i0 = idx[0]; i1 = min(len(need), idx[-1] + int(release * 12 * SR))
        g[:i0] = 1.0
        for i in range(i0, i1):
            cur = need[i] if need[i] < cur else need[i] + (cur - need[i]) * a
            g[i] = cur
        k = int(0.002 * SR)
        g = np.convolve(np.pad(g, (k, k), mode='edge'), np.ones(k) / k, 'same')[k:-k]
        g = np.minimum(g, need)
    return x * g[:, None], 20 * np.log10(g.min())


def short_term_series(x, mask=None, win=3.0, hop=0.1):
    m, t = C.momentary(x, win=win, hop=hop)
    return m, t + win / 2


def lra(x):
    m, _ = C.momentary(x, win=3.0, hop=0.1)
    m = m[m > -70]
    if not len(m): return 0.0
    rel = 10 * np.log10(np.mean(10 ** (m / 10))) - 20
    m = m[m > rel]
    return float(np.percentile(m, 95) - np.percentile(m, 10))


# ================================================================================================ main
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--profile', default='bible', choices=['primary', 'bible', 'standard', 'full'])
    ap.add_argument('--range', nargs=2, type=float, default=None)
    ap.add_argument('--out', default=os.path.join(S.SCRATCH, 'out'))
    ap.add_argument('--compare', default=None)
    ap.add_argument('--music', default=None)
    ap.add_argument('--cap', type=int, default=9, help='standard profile: max events within +-15 s of a sweetener')
    ap.add_argument('--no-stems', action='store_true')
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    tl = json.load(open(TIMELINE)); words = json.load(open(WORDS))['words']
    gmap = json.load(open(C.MAP_PATH))['cues']
    DUR = tl['duration']; N = int(round(DUR * SR))
    t_lo, t_hi = (a.range if a.range else (0.0, DUR))
    n = int(round((t_hi - t_lo) * SR))
    tag = '' if not a.range else f'_{t_lo:g}-{t_hi:g}'

    # ---- voice (full length for the leveler, then cut)
    voice_full, vinfo, sents = voice_track(tl['audio']['voice'], words, N)
    voice = voice_full[int(t_lo * SR):int(t_lo * SR) + n]

    # ---- cues
    ovr = os.path.join(HERE, 'cue_times_override.json')
    ovr = json.load(open(ovr)) if os.path.isfile(ovr) else None
    P, dropped = resolve_cues(tl, a.profile, a.cap, ovr)
    sfx_app = np.zeros((n, 2)); sfx = np.zeros((n, 2))
    for q in P:
        clip_len_guess = 4.0
        if q['t'] + 4.0 < t_lo or q['t'] - 1.0 > t_hi: continue
        place_cue(sfx_app if gmap[q['cue']].get('approved_test') else sfx, q, gmap, t_lo, t_hi)
    sfx, dk = duck(sfx, voice)
    sfx_all = sfx + sfx_app

    # ---- beds
    env, sched = bed_envelopes(tl, n, t_lo)
    beds = np.zeros((n, 2))
    for name, e in env.items():
        nz = np.where(e > 0)[0]
        if not len(nz): continue
        i0, i1 = nz[0], nz[-1] + 1
        y = C.bed(name, t_lo + i0 / SR, t_lo + i1 / SR)
        m = min(len(y), i1 - i0)
        beds[i0:i0 + m] += y[:m] * e[i0:i0 + m, None]

    # ---- music preview (optional): -24 LUFS, drops in the planned pauses
    pauses = music_pauses(sents)
    music = np.zeros((n, 2))
    if a.music:
        mu, msr = sf.read(a.music, always_2d=True)
        if msr != SR: mu = resample_poly(mu, SR, msr, axis=0)
        mu = np.resize(mu, (N, mu.shape[1]))[:, :2] if mu.shape[1] >= 2 else np.repeat(np.resize(mu, (N, 1)), 2, 1)
        mu *= 10 ** ((-24.0 - meter.integrated_loudness(mu)) / 20)
        for pz in pauses:
            if pz['planned']:
                i0, i1 = int(pz['t0'] * SR), int(pz['t1'] * SR); k = int(0.04 * SR)
                w = np.ones(N); w[i0:i1] = 0.1; w[i0 - k:i0] = np.linspace(1, 0.1, k); w[i1:i1 + k] = np.linspace(0.1, 1, k)
                mu *= w[:, None]
        music = mu[int(t_lo * SR):int(t_lo * SR) + n]

    # ---- master
    mix = voice + sfx_all + beds + music
    if not a.range or t_hi >= DUR - 1e-6:
        k = int(0.010 * SR); mix[-k:] *= fade_w(k)[::-1][:, None]
    tp0 = true_peak_db(mix)
    mix_l, gr = limiter(mix)
    tp1 = true_peak_db(mix_l)
    sf.write(os.path.join(a.out, f'ep01_mix{tag}.wav'), mix_l.astype(np.float32), SR, subtype='PCM_24')
    if not a.no_stems:
        sf.write(os.path.join(a.out, f'ep01_voice{tag}.wav'), voice.astype(np.float32), SR, subtype='PCM_24')
        sf.write(os.path.join(a.out, f'ep01_sfx{tag}.wav'), sfx_all.astype(np.float32), SR, subtype='PCM_24')
        sf.write(os.path.join(a.out, f'ep01_beds{tag}.wav'), beds.astype(np.float32), SR, subtype='PCM_24')

    # ---- report
    rep = report(a, tl, P, dropped, vinfo, voice, sfx_all, beds, mix_l, tp0, tp1, gr, dk, t_lo, t_hi, pauses, sched)
    json.dump(rep, open(os.path.join(a.out, f'ep01_mix_report{tag}.json'), 'w'), indent=1)
    if not a.range:
        P_all, _ = resolve_cues(tl, 'full', a.cap, ovr)       # cue_times.json lists every multi-hit cue, any profile
        write_sidecars(P, dropped, pauses, a.profile, P_all)
    if a.compare:
        rep['compare'] = compare(mix_l, a.compare, t_lo, os.path.join(a.out, f'ep01_vs_test{tag}.json'))
    print(json.dumps({k: v for k, v in rep.items() if k not in ('cues', 'voice_groups', 'dropped', 'bed_schedule', 'pauses')}, indent=1))
    return rep


def music_pauses(sents):
    """Voice pauses >= 0.25 s; the 4 planned ones (after 'empty', 'fence', 'flower bed', before 'Every spring')."""
    out = []
    planned_words = ['empty', 'fence.', 'bed.', 'one.']
    for i in range(len(sents) - 1):
        g0, g1 = sents[i]['t1'], sents[i + 1]['t0']
        last = sents[i]['text'].split()[-1].lower()
        text = sents[i]['text'].lower()
        planned = (('empty' in text and 'ran' in text) or last in ('fence.',) or text.endswith('flower bed.') or
                   (last == 'one.' and 'except' in text))
        if 'empty' in text and 'ran' in text:   # the ASR merged "...empty" + "So I ran"; the pause sits after "empty"
            g0, g1 = 28.87, 29.72
        if g1 - g0 >= 0.25 or planned:
            out.append(dict(t0=round(g0, 3), t1=round(g1, 3), dur=round(g1 - g0, 3), after=sents[i]['text'][-40:], planned=bool(planned)))
    return out


def write_sidecars(P, dropped, pauses, profile, P_all=None):
    sheet = [dict(cue=q['cue'], t=round(q['t'], 4), times=q.get('times'), start=q.get('start'), end=q.get('end'), shot=q['shot'],
                  word=q.get('word'), prio=q['prio'], layer_of=q.get('layer_of'), gain_db=q.get('gain_db'), why=q['why'])
             for q in P]
    json.dump(dict(profile=profile, note='Resolved SFX placements (mix.py). t = picture event (s), start/end = clip span.',
                   cues=sheet, dropped_by_profile=[dict(cue=q['cue'], t=q['t'], shot=q['shot']) for q in dropped]),
              open(os.path.join(HERE, 'cue_sheet.json'), 'w'), indent=1)
    PA = P_all or P
    multi = {q['cue'] + ('' if list(x['cue'] for x in PA).count(q['cue']) == 1 else '@' + q['shot']):
             dict(shot=q['shot'], times=q['times'], in_profile=any(x['cue'] == q['cue'] and x['shot'] == q['shot'] for x in P))
             for q in PA if q.get('times') and len(q['times']) > 1}
    json.dump(dict(note='Multi-hit SFX times (episode s) the picture should match (or copy into cue_times_override.json '
                        '{CUE: {times: [...]}} to move the sound to the picture).', cues=multi),
              open(os.path.join(HERE, 'cue_times.json'), 'w'), indent=1)
    json.dump(dict(note="Voice pauses (s). planned=true: the board's 4 planned pauses; drop the owner's music bed there "
                        '(about 8 LU under the voice elsewhere, no ducking).', pauses=pauses),
              open(os.path.join(HERE, 'music_cues.json'), 'w'), indent=1)


def report(a, tl, P, dropped, vinfo, voice, sfx, beds, mix, tp0, tp1, gr, dk, t_lo, t_hi, pauses, sched):
    dur = t_hi - t_lo
    vm, vt = short_term_series(voice)
    ev_band, et = band_env(voice.mean(1)); fx_band, _ = band_env((sfx + beds).mean(1))
    act = ev_band > np.percentile(ev_band[ev_band > -45], 50) - 10    # inside words (within 10 dB of the median speech level)
    margin = (ev_band - fx_band)[act]
    vbar = vm[(vm > -30)]
    events = [q for q in P if not q.get('layer_of') and t_lo <= q['t'] < t_hi]
    rep = dict(
        profile=a.profile, range=[t_lo, t_hi], sr=SR, channels=2,
        voice_integrated=round(meter.integrated_loudness(voice), 2),
        voice_short_term_lufs_p5_p50_p95=[round(float(np.percentile(vbar, q)), 2) for q in (5, 50, 95)] if len(vbar) else None,
        voice_raw_integrated=vinfo['raw_integrated'], voice_base_gain_db=vinfo['base_gain_db'],
        mix_integrated=round(meter.integrated_loudness(mix), 2), mix_lra=round(lra(mix), 2),
        true_peak_before_db=round(tp0, 2), true_peak_after_db=round(tp1, 2), limiter_max_gr_db=round(gr, 2),
        sfx_integrated=round(meter.integrated_loudness(sfx), 2) if np.abs(sfx).max() > 0 else None,
        beds_integrated=round(meter.integrated_loudness(beds), 2) if np.abs(beds).max() > 0 else None,
        voice_over_sfx_beds_band_db=dict(median=round(float(np.median(margin)), 1), p5=round(float(np.percentile(margin, 5)), 1),
                                         min=round(float(margin.min()), 1), pct_under_10db=round(float((margin < 10).mean() * 100), 2)),
        ducker=dk,
        events=len(events), events_per_min=round(len(events) / dur * 60, 1),
        placements=len([q for q in P if t_lo <= q['t'] < t_hi]),
        last_voice_s=round(max(s['t1'] for s in vinfo['groups']), 3), episode_end_s=tl['duration'],
        headroom_note='Voice at -16 LUFS; SFX/beds under it; limiter ceiling -1.2 dBTP. Adding the owner\'s music at -24 LUFS raises the '
                      'integrated level by ~0.6 LU: re-limit at the final mux.',
        voice_groups=[dict(t0=g['t0'], t1=g['t1'], win=g['win'], lufs_raw=g['lufs_raw'], gain_db=g['gain_db'], text=g['text'][:60]) for g in vinfo['groups']],
        cues=[dict(cue=q['cue'], t=round(q['t'], 3), start=q.get('start'), end=q.get('end'), shot=q['shot'], prio=q['prio'],
                   layer_of=q.get('layer_of'), gain_db=q.get('gain_db'), times=q.get('times')) for q in P if t_lo - 4 <= q['t'] < t_hi],
        dropped=[dict(cue=q['cue'], t=q['t'], shot=q['shot']) for q in dropped],
        bed_schedule=[dict(shot=s, t0=round(x, 3), t1=round(y, 3), bed=b) for s, x, y, b in sched if y > t_lo and x < t_hi],
        pauses=pauses,
    )
    return rep


def compare(mix, ref_path, t_lo, out_json):
    """Null test and per-window loudness vs the approved test mix (both 48 kHz stereo)."""
    ref, rsr = sf.read(ref_path, always_2d=True)
    assert rsr == SR
    i0 = int(round(t_lo * SR)); n = min(len(mix), len(ref) - i0)
    m, r = mix[:n], ref[i0:i0 + n]
    res = {}
    for a, b, lab in [(0.0, 3.40, 'identical part (the approved line, before the episode continues)'),
                      (0.0, 0.5, 'W1 whoosh'), (2.0, 2.6, 'snap: P1 + M1'), (3.40, 5.0, 'after the test diverges')]:
        if b <= t_lo: continue
        x0, x1 = int((a - t_lo) * SR), int((b - t_lo) * SR)
        d = m[x0:x1] - r[x0:x1]
        e_ref = np.sqrt((r[x0:x1] ** 2).mean()) + 1e-12
        L = lambda y: meter.integrated_loudness(y) if len(y) >= int(0.4 * SR) else float('nan')
        res[f'{a:.2f}-{b:.2f}'] = dict(what=lab, residual_db_rel_ref=round(20 * np.log10(np.sqrt((d ** 2).mean()) / e_ref + 1e-12), 1),
                                       max_abs_diff=round(float(np.abs(d).max()), 5), lufs_episode=round(L(m[x0:x1]), 2), lufs_test=round(L(r[x0:x1]), 2))
    json.dump(res, open(out_json, 'w'), indent=1)
    return res


if __name__ == '__main__':
    main()
