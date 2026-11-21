"""Query and load the recorded sample library (free CC0/CC-BY files + the owner's Epidemic files).

Built by audio/build_library.py; the catalogue is audio/catalog.json, the audio lives under $S/pov2/samples/.

Public API
    entries(**filters) -> list[dict]       filter by any of: category (exact or prefix ending in '/'), serves (a required
                                           SFX name), tag, source, licence, policy, free_only=True, no_lossy=True,
                                           clean=True (drop files flagged clip_runs_n / noise_floor_high / peak_0dBFS)
    get(id_or_entry) -> dict               one catalogue entry by id
    load(id_or_entry, stereo=True) -> np.ndarray float32 [n, 2] (or [n, ch] with stereo=False) at 48 kHz
    note(category, midi, vel=None, rr=None) -> (entry, semitones)   nearest sampled note of an instrument category
                                           (uses the filename note `midi`, else the measured `midi_est`) and the
                                           pitch shift still needed; vel picks the closest velocity layer
    pick(serves=None, category=None, n=1, seed=0, **filters) -> list[dict]   deterministic random choice (variations)
    coverage() -> dict                     the coverage table (required SFX names, score layers)
    ROOT, SR

Entry fields: id, path (relative to ROOT), category, tags, serves, source, licence, source_url, upstream_url, author,
attribution (CC-BY credit line or None), dur, sr, channels, bit_depth, peak_db, lufs, rms_db, floor_db, snr_db, qc
(e.g. lossy_source, noise_floor_high), policy (oneshot/inst/loop/ir/as_supplied), and for instrument notes midi,
midi_est, f0_hz, vel, rr. IRs: category 'ir', field room.
"""
import json, os, random
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
_CAT = None
_BY_ID = None


def _cat():
    global _CAT, _BY_ID
    if _CAT is None:
        _CAT = json.load(open(os.path.join(HERE, 'catalog.json')))
        _BY_ID = {e['id']: e for e in _CAT['samples']}
    return _CAT


ROOT = '/home/user/claude-todo-demo/Vox test/Police Officer Video/v2/_work/pov2/samples'


def entries(category=None, serves=None, tag=None, source=None, licence=None, policy=None, free_only=False, no_lossy=False,
            clean=False):
    out = []
    for e in _cat()['samples']:
        if category and not (e['category'] == category or (category.endswith('/') and e['category'].startswith(category))):
            continue
        if serves and serves not in e.get('serves', []):
            continue
        if tag and tag not in e.get('tags', []):
            continue
        if source and e['source'] != source:
            continue
        if licence and e.get('licence') != licence:
            continue
        if policy and e.get('policy') != policy:
            continue
        if free_only and e['source'] == 'epidemic':
            continue
        if no_lossy and 'lossy_source' in e.get('qc', []):
            continue
        if clean and any(q.startswith('clip') or q in ('noise_floor_high', 'peak_0dBFS') for q in e.get('qc', [])):
            continue
        out.append(e)
    return out


def get(x):
    _cat()
    return x if isinstance(x, dict) else _BY_ID[x]


def load(x, stereo=True):
    e = get(x)
    p = e['path'] if os.path.isabs(e['path']) else os.path.join(ROOT, e['path'])
    y, sr = sf.read(p, dtype='float32', always_2d=True)
    if sr != SR:
        import soxr
        y = soxr.resample(y, sr, SR, quality='VHQ').astype(np.float32)
    if stereo:
        y = np.repeat(y, 2, axis=1) if y.shape[1] == 1 else y[:, :2]
    return y


def note(category, midi, vel=None, rr=None):
    c = [e for e in entries(category=category) if e.get('midi') is not None or e.get('midi_est') is not None]
    if not c:
        raise KeyError(f'no pitched samples in {category}')
    m = lambda e: e['midi'] if e.get('midi') is not None else e['midi_est']
    best = min(abs(m(e) - midi) for e in c)
    c = [e for e in c if abs(m(e) - midi) <= best + 1e-6]
    if vel is not None and any('vel' in e for e in c):
        bv = min(abs(e.get('vel', 0) - vel) for e in c)
        c = [e for e in c if abs(e.get('vel', 0) - vel) == bv]
    if rr is not None and len(c) > 1:
        c = [c[rr % len(c)]]
    e = c[0]
    return e, float(midi - m(e))


def pick(serves=None, category=None, n=1, seed=0, **kw):
    c = entries(category=category, serves=serves, **kw)
    if not c:
        return []
    r = random.Random(seed)
    return [c[r.randrange(len(c))] for _ in range(n)]


def coverage():
    return _cat()['coverage']
