"""Epidemic Sound library API for the "What If Real Life Had a SETTINGS MENU?" mixer.

    import sys; sys.path.insert(0, '/home/user/claude-todo-demo/whatif-settings/audio')
    import lib
    x = lib.load_sfx('ui_tap', 2)              # float32 (n, 2) @ 48 kHz, trimmed take, gain to REF applied
    m = lib.load_music('power_pulse', 12.0, 27.5)   # float32 (n, 2) @ 48 kHz slice, no gain
    lib.info('whoosh_short')                   # map entry + library metadata (durations, transient ms ...)

Data files next to this module:
  library.json   every Epidemic file (metadata, loudness, takes), paths point into the scratch raw/ folder
  sfx_map.json   semantic SFX name -> variants [{file, take, t0, t1, gain_db, dur_ms, onset_ms, peak_ms, ...}]
  music_map.json 20 tracks: tempo, beat grid, key, loudness curve, sections, hits, loops, picks per slot

Decoding always goes through ffmpeg (same decoder the analysis used, so analysed times match sample
positions). Trimmed SFX are cached as 24-bit WAV in CACHE (pre-gain, native channels); music is decoded on demand and
kept in a small in-process LRU (full tracks are ~50 MB each as float32, too big for the disk budget).
Clips longer than CACHE_MAX_S (ambience beds) are likewise sliced from an in-process decode, not cached on disk.
The source files are untrusted data: they are only ever decoded, never executed.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections import OrderedDict
from pathlib import Path

import numpy as np

SR = 48000
HERE = Path(__file__).resolve().parent
LIB_JSON = HERE / 'library.json'
SFX_MAP = HERE / 'sfx_map.json'
MUSIC_MAP = HERE / 'music_map.json'
CACHE = Path(os.environ.get(
    'WHATIF_EPIDEMIC_CACHE',
    '/tmp/claude-0/-home-user-claude-todo-demo/353ac1d9-152b-55bb-bdf1-0625e0fc6a83/scratchpad/settings/epidemic/cache'))
REF_LUFS = -18.0          # common reference loudness used by sfx_map gain_db (see _meta in sfx_map.json)
PEAK_CEIL_DB = -1.0       # gain_db never pushes a take's true peak above this

_json_cache: dict = {}
_music_lru: OrderedDict = OrderedDict()
_MUSIC_LRU_MAX = 3


# ---------------------------------------------------------------- data files
def _load_json(p: Path):
    st = p.stat().st_mtime
    hit = _json_cache.get(p)
    if hit and hit[0] == st:
        return hit[1]
    d = json.loads(p.read_text())
    _json_cache[p] = (st, d)
    return d


def library() -> dict:
    """key -> library entry (see library.json)."""
    return _load_json(LIB_JSON)['files']


def sfx_map() -> dict:
    return {k: v for k, v in _load_json(SFX_MAP).items() if not k.startswith('_')}


def music_map() -> dict:
    return _load_json(MUSIC_MAP)['tracks']


def sfx_names() -> list:
    return sorted(sfx_map())


def variants(name: str) -> list:
    return sfx_map()[name]['variants']


# ---------------------------------------------------------------- decode / measure
def decode(path, sr: int = SR) -> np.ndarray:
    """Decode any audio file with ffmpeg to float32 (n, channels) at `sr`, native channel count."""
    path = str(path)
    ch = int(subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=channels',
         '-of', 'csv=p=0', path], capture_output=True, text=True, check=True).stdout.strip().split('\n')[0])
    raw = subprocess.run(
        ['ffmpeg', '-v', 'error', '-nostdin', '-i', path, '-map', '0:a:0', '-f', 'f32le', '-acodec', 'pcm_f32le',
         '-ar', str(sr), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).copy()


def to_stereo(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, np.float32)
    if x.ndim == 1:
        x = x[:, None]
    if x.shape[1] == 1:
        return np.repeat(x, 2, axis=1)
    return x[:, :2]


def _kweight(x: np.ndarray, sr: int = SR) -> np.ndarray:
    from scipy.signal import lfilter
    assert sr == 48000, 'K-weighting coefficients are for 48 kHz'
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    return lfilter(b2, a2, lfilter(b1, a1, np.asarray(x, np.float64), axis=0), axis=0)


def _ms_to_lufs(ms):
    return -0.691 + 10 * np.log10(np.maximum(ms, 1e-20))


def loudness(x: np.ndarray, sr: int = SR) -> dict:
    """BS.1770-4 loudness. Returns dict(i=integrated (gated; ungated if <0.4 s), m_max=max momentary 400 ms,
    w200_max=max over 200 ms windows, ungated=whole-signal ungated)."""
    x = np.asarray(x, np.float64)
    if x.ndim == 1:
        x = x[:, None]
    y = _kweight(x, sr) ** 2
    p = y.sum(1)                      # channel weights 1.0 (L, R / mono)
    if x.shape[1] == 1:
        p = p * 1.0
    n = len(p)
    cs = np.concatenate([[0.0], np.cumsum(p)])

    def blocks(win, hop):
        w, h = int(win * sr), int(hop * sr)
        if n < w:
            return np.array([cs[-1] / max(n, 1)])
        st = np.arange(0, n - w + 1, h)
        return (cs[st + w] - cs[st]) / w

    ung = float(_ms_to_lufs(cs[-1] / max(n, 1)))
    b400 = blocks(0.4, 0.1)
    if n < int(0.4 * sr):
        li = ung
    else:
        l400 = _ms_to_lufs(b400)
        g = b400[l400 > -70]
        if len(g) == 0:
            li = -70.0
        else:
            rel = _ms_to_lufs(g.mean()) - 10
            g2 = g[_ms_to_lufs(g) > rel]
            li = float(_ms_to_lufs(g2.mean())) if len(g2) else -70.0
    return dict(i=round(li, 2), m_max=round(float(_ms_to_lufs(b400.max())), 2),
                w200_max=round(float(_ms_to_lufs(blocks(0.2, 0.01).max())), 2), ungated=round(ung, 2))


def true_peak_db(x: np.ndarray) -> float:
    """4x oversampled true peak in dBTP (chunked so long beds stay cheap)."""
    from scipy.signal import resample_poly
    x = np.asarray(x, np.float32)
    if x.ndim == 1:
        x = x[:, None]
    pk, step, pad = 0.0, SR * 10, 64
    for s in range(0, len(x), step):
        seg = x[max(0, s - pad): s + step + pad]
        if len(seg) < 4:
            pk = max(pk, float(np.abs(seg).max(initial=0)))
            continue
        pk = max(pk, float(np.abs(resample_poly(seg, 4, 1, axis=0)).max()))
    return round(20 * np.log10(max(pk, 1e-9)), 2)


def peak_db(x: np.ndarray) -> float:
    return round(float(20 * np.log10(max(float(np.abs(x).max(initial=0)), 1e-9))), 2)


def _fade(x: np.ndarray, fi_ms: float, fo_ms: float) -> np.ndarray:
    x = x.copy()
    n = len(x)
    fi, fo = min(int(fi_ms * SR / 1000), n // 2), min(int(fo_ms * SR / 1000), n // 2)
    if fi > 1:
        x[:fi] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fi)))[:, None].astype(np.float32)
    if fo > 1:
        x[n - fo:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, fo)))[:, None].astype(np.float32)
    return x


# ---------------------------------------------------------------- public API
def _file_path(key: str) -> str:
    e = library()[key]
    return e['path']


def _variant(name: str, variant: int) -> dict:
    m = sfx_map()
    if name not in m:
        raise KeyError(f'unknown sfx {name!r}; known: {", ".join(sorted(m))}')
    vs = m[name]['variants']
    return vs[variant % len(vs)]


CACHE_MAX_S = 12.0        # clips longer than this (beds) are not written to disk, only memoised in-process
_decode_lru: OrderedDict = OrderedDict()
_DECODE_LRU_MAX = 4


def _decoded(path: str) -> np.ndarray:
    """Full decode at native channel count, memoised (small LRU)."""
    if path in _decode_lru:
        x = _decode_lru.pop(path)
    else:
        x = decode(path)
    _decode_lru[path] = x
    while len(_decode_lru) > _DECODE_LRU_MAX:
        _decode_lru.popitem(last=False)
    return x


def _cache_path(path: str, t0: float, t1: float) -> Path:
    st = os.stat(path)
    h = hashlib.sha1(f'{path}|{st.st_size}|{st.st_mtime_ns}|{t0:.6f}|{t1:.6f}'.encode()).hexdigest()[:16]
    return CACHE / 'sfx' / f'{Path(path).stem[3:50].replace(" ", "_").replace(",", "")}__{h}.wav'


def _cached_segment(path: str, t0: float, t1: float) -> np.ndarray:
    """Source samples [t0, t1) as float32 (n, 2). Clips <= CACHE_MAX_S are cached as 24-bit WAV at the source's
    native channel count (MP3 decode noise sits far below 24-bit resolution); longer beds are sliced from a
    memoised full decode instead, to keep the cache small."""
    import soundfile as sf
    i0 = max(0, int(round(t0 * SR)))
    i1 = int(round(t1 * SR))
    if (t1 - t0) > CACHE_MAX_S:
        x = _decoded(path)
        return to_stereo(np.ascontiguousarray(x[i0:min(len(x), i1)]))
    cp = _cache_path(path, t0, t1)
    if cp.exists():
        try:
            y, sr = sf.read(str(cp), dtype='float32', always_2d=True)
            if sr == SR and len(y) == i1 - i0:
                return to_stereo(y)
        except Exception:  # noqa: BLE001  (corrupt cache file: re-decode)
            pass
    x = _decoded(path)
    y = np.ascontiguousarray(x[i0:min(len(x), i1)])
    cp.parent.mkdir(parents=True, exist_ok=True)
    tmp = cp.with_name(cp.stem + '.tmp.wav')
    sf.write(str(tmp), y, SR, subtype='PCM_24')
    os.replace(tmp, cp)
    return to_stereo(y)


def prune_cache() -> int:
    """Delete cached clips that no sfx_map variant references any more. Returns the number removed."""
    keep = set()
    lib_ = library()
    for e in sfx_map().values():
        for v in e['variants']:
            if v['t1'] - v['t0'] <= CACHE_MAX_S:
                keep.add(_cache_path(lib_[v['file']]['path'], float(v['t0']), float(v['t1'])).name)
    n = 0
    for f in (CACHE / 'sfx').glob('*.wav'):
        if f.name not in keep:
            f.unlink()
            n += 1
    return n


def load_sfx(name: str, variant: int = 0, apply_gain: bool = True) -> np.ndarray:
    """Trimmed take of semantic SFX `name` as float32 (n, 2) at 48 kHz.
    `variant` is taken modulo the number of variants (so callers can cycle i = 0, 1, 2 ... per repeat).
    With apply_gain the map's gain_db is applied, bringing the take to REF_LUFS (one-shots: loudest 200 ms
    window; beds/loops: integrated), capped so its true peak stays <= PEAK_CEIL_DB.
    Short raised-cosine fades (fade_in_ms / fade_out_ms from the entry) remove edit clicks."""
    v = _variant(name, variant)
    y = _cached_segment(_file_path(v['file']), float(v['t0']), float(v['t1']))
    y = _fade(y, v.get('fade_in_ms', 1.5), v.get('fade_out_ms', 12.0))
    if apply_gain:
        y = y * np.float32(10 ** (v['gain_db'] / 20))
    return y.astype(np.float32, copy=False)


def load_music(track_key: str, t0: float | None = None, t1: float | None = None, fade_ms: float = 0.0) -> np.ndarray:
    """Music track (music_map key, e.g. 'power_pulse') as float32 (n, 2) at 48 kHz, optionally sliced
    [t0, t1) in seconds of the original file (times in music_map.json use the same clock). No gain applied:
    use music_map[track]['lufs_i'] / loudness curve to set levels. fade_ms adds raised-cosine edge fades.
    Note: several masters are loud (-9..-10 LUFS) and decode with inter-sample overs up to +1.3 dBFS (|x| > 1.0
    in float, no flat-top clipping); apply the music gain before any clip/limit stage."""
    mm = music_map()
    if track_key not in mm:
        raise KeyError(f'unknown track {track_key!r}; known: {", ".join(sorted(mm))}')
    path = _file_path(mm[track_key]['file'])
    if path in _music_lru:
        x = _music_lru.pop(path)
    else:
        x = to_stereo(decode(path))
    _music_lru[path] = x
    while len(_music_lru) > _MUSIC_LRU_MAX:
        _music_lru.popitem(last=False)
    i0 = 0 if t0 is None else max(0, int(round(t0 * SR)))
    i1 = len(x) if t1 is None else min(len(x), int(round(t1 * SR)))
    y = np.ascontiguousarray(x[i0:i1])
    if fade_ms:
        y = _fade(y, fade_ms, fade_ms)
    return y


def info(name: str) -> dict:
    """SFX map entry (with each variant's library metadata under 'src'), or a music_map track."""
    m = sfx_map()
    if name in m:
        e = json.loads(json.dumps(m[name]))
        lib_ = library()
        for v in e['variants']:
            f = lib_[v['file']]
            v['src'] = {k: f.get(k) for k in ('name', 'category', 'descriptors', 'duration_s', 'channels',
                                              'lufs_i', 'true_peak_dbtp', 'n_takes', 'cls', 'path')}
        return e
    mm = music_map()
    if name in mm:
        return mm[name]
    lib_ = library()
    if name in lib_:
        return lib_[name]
    raise KeyError(name)


def selftest(verbose: bool = True) -> dict:
    """Decode every map variant and every music track; check not silent, not clipped, lengths match."""
    res = dict(sfx_ok=0, sfx_fail=[], music_ok=0, music_fail=[])
    for name in sfx_names():
        for i, v in enumerate(variants(name)):
            try:
                y = load_sfx(name, i)
                want = int(round(v['t1'] * SR)) - int(round(v['t0'] * SR))
                lv = loudness(y)
                tp = true_peak_db(y)
                prob = []
                if y.shape[1] != 2 or y.dtype != np.float32:
                    prob.append('shape/dtype')
                if abs(len(y) - want) > 1:
                    prob.append(f'len {len(y)} != {want}')
                if lv['w200_max'] < -45:
                    prob.append(f'near-silent ({lv["w200_max"]} LUFS)')
                if tp > PEAK_CEIL_DB + 0.3:
                    prob.append(f'true peak {tp} dBTP')
                if np.abs(y).max() >= 0.999:
                    prob.append('sample clip')
                if not np.isfinite(y).all():
                    prob.append('non-finite')
                if prob:
                    res['sfx_fail'].append((name, i, prob))
                else:
                    res['sfx_ok'] += 1
                if verbose:
                    print(f'{name:22s} v{i}  {len(y)/SR*1000:7.0f} ms  w200 {lv["w200_max"]:6.1f}  '
                          f'TP {tp:6.1f}  {"OK" if not prob else prob}')
            except Exception as ex:  # noqa: BLE001
                res['sfx_fail'].append((name, i, [repr(ex)]))
    for k, t in music_map().items():
        try:
            y = load_music(k)
            want = library()[t['file']]['n_samples']
            prob = []
            if abs(len(y) - want) > 1:
                prob.append(f'len {len(y)} != {want}')
            a = np.abs(y)
            pk = float(a.max())
            if pk < 0.05:
                prob.append('near-silent')
            # MP3 inter-sample overs decode to |x| > 1.0 in float and are harmless once gain is applied;
            # real clipping shows as flat tops (>= 4 consecutive samples pinned at the channel maximum)
            flat = 0
            for c in range(a.shape[1]):
                m = a[:, c].max()
                f = ((a[:, c] >= m - 1e-4) & (a[:, c] >= 0.98)).astype(np.int8)
                d = np.diff(np.concatenate([[0], f, [0]]))
                flat += int(((np.where(d == -1)[0] - np.where(d == 1)[0]) >= 4).sum())
            if flat:
                prob.append(f'{flat} flat-top (clipped) runs')
            if prob:
                res['music_fail'].append((k, prob))
            else:
                res['music_ok'] += 1
            if verbose:
                print(f'music {k:28s} {len(y)/SR:7.2f} s  peak {20*np.log10(pk):6.2f} dBFS  overs>1.0 {int((a > 1).sum()):5d}  '
                      f'{"OK" if not prob else prob}')
        except Exception as ex:  # noqa: BLE001
            res['music_fail'].append((k, [repr(ex)]))
    return res


if __name__ == '__main__':
    r = selftest()
    print(json.dumps({k: (v if not isinstance(v, list) else len(v)) for k, v in r.items()}))
    for f in r['sfx_fail'] + r['music_fail']:
        print('FAIL', f)
