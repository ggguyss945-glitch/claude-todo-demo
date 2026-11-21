"""Checks for the edited narration (run as `python3 vo_edit.py check`, or directly).
    python3 vo_check.py [--no-strips] [--no-asr]
Writes into W/narration/tests/:
  strip_XX_<name>.png   before / after: the raw take (top) and the edit (bottom) of the same lines, spectrogram + 5 ms
                        RMS (dBFS) + line labels; 16 spots (rule transitions, reveal beats, the knocks, every character,
                        the counts, the comment prompt, the outro, the repaired slips)
  check.json            the scans below, read by voice_report.md
Scans of narration_en.wav / narration_clean.wav:
  gaps      the silence between every two lines measured on the file (last sound above -60 dBFS to the next first
            sound), against pacing_map.md; plus every silence < 0.15 s or > 2 s between sentences
  breaths   residual breath-like events: sound islands (> -60 dBFS) that are unvoiced (pitch < 20 % of frames), last
            >= 80 ms and sit >= 60 ms away from any voiced sound
  clicks    sample discontinuities: |x[n] - x[n-1]| more than 12x the local 99th percentile of the step size within
            +-5 ms, in sound; plus any non-zero sample inside the gaps (the gaps must be digital silence)
  edits     the waveform step at every piece edge of edit_list.json (each edge must be faded: step < 1e-3)
  peaks     samples at or above full scale, true peak, loudness, the spread of the narrator's line levels
  asr       every character line and every repaired phrase re-recognised (Parakeet) on narration_en.wav: share of
            the script words heard
"""
import json, os, re, sys
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vo_edit as V                                                # noqa: E402

SR = V.SR
SPOTS = [  # (name, first tag, last tag, why)
    ('rule1', 'fridge', 'rule1_song', 'a rule transition: 1.4 s before "Rule number one.", the card text'),
    ('pocket_rule3', 'no_fire', 'rule3_seven', 'reveal beat (held 1.3 s before "She puts it in her pocket.") into rule 3; '
                                              'the "If he" splice'),
    ('knocks', 'knock', 'thats_him', 'the knock fragments, spaced for the knocks'),
    ('grandma', 'grandma', 'after_woods', 'Grandma (G) and the narrator\'s "she said."'),
    ('slot', 'small_scared', 'come_home', 'the little-girl voice through the slot (L)'),
    ('june_mom', 'june_slot', 'is_she_humming', 'June (J) and the whispered "Is she humming?" (L)'),
    ('bedtime_humming', 'slot_close', 'rule5', 'Mom (M) then held dread before "She\'s humming."'),
    ('rule6_action', 'window', 'bathtub', 'fast action: 0.25-0.3 s gaps'),
    ('fight', 'never_heard', 'heavy_crack', 'Mom\'s shout (M) and the girl\'s scream (L) through the door'),
    ('dying', 'lips_move', 'still', 'the dying man\'s "Mama." (D), 1.4 s before "Then he\'s still."'),
    ('trick_counts', 'happy_easter', 'count_3', 'Mom dark (M), June\'s whispered counts (J), spaced like counting'),
    ('six_seven', 'easiest', 'myself', 'held 1.3 s, "Six." "Seven." 0.95 s apart'),
    ('cta', 'smiling', 'cta_question', 'Mom\'s line, about 1 s, then the comment prompt'),
    ('x_end', 'car', 'breathe', 'the old body (X), 1.5 s, "Easter is in nine days.", 2.8 s, the outro'),
    ('song_1107', 'from_woods', 'curtains', '"At 11:07" (an "O" spliced in), the slow song'),
    ('sleep_well', 'next', 'end', 'the rebuilt "Sleep well." and the last line'),
]


def load():
    edl = json.load(open(V.EDL))
    en, _ = sf.read(V.OUT, dtype='float64')
    cl, _ = sf.read(V.OUT_CLEAN, dtype='float64')
    raw, sr = sf.read(V.RAW, dtype='float64')
    return edl, en, cl, raw, sr


def tag_index(edl):
    return {l['tag']: l['i'] for l in edl['lines'] if l['tag']}


# ============================================================================ strips
def strip(name, a_tag, b_tag, why, edl, en, raw, raw_sr, k):
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from scipy import signal
    ti = tag_index(edl); L = edl['lines']
    i0, i1 = ti[a_tag], ti[b_tag]
    sel = L[i0:i1 + 1]
    s0 = min(l['src_span'][0] for l in sel) - 0.3; s1 = max(l['src_span'][1] for l in sel) + 0.3
    o0 = sel[0]['out'][0] - 0.3; o1 = sel[-1]['out'][1] + 0.3
    fig, axs = plt.subplots(2, 1, figsize=(22, 8.6))
    for ax, (x, sr, t0, t1, title, src) in zip(axs, [(raw, raw_sr, s0, s1, 'BEFORE: raw take %.2f-%.2f s' % (s0, s1), True),
                                                     (en, SR, o0, o1, 'AFTER: narration_en.wav %.2f-%.2f s' % (o0, o1), False)]):
        y = x[max(0, int(t0 * sr)):int(t1 * sr)]
        nper = int(0.02 * sr); hop = int(0.004 * sr)
        f, t, S = signal.spectrogram(y, fs=sr, nperseg=nper, noverlap=nper - hop, window='hann')
        S = 10 * np.log10(S + 1e-14)
        ax.pcolormesh(t + t0, f, S, vmin=S.max() - 95, vmax=S.max(), shading='auto', cmap='magma')
        ax.set_ylim(0, 12000); ax.set_xlim(t0, t1)
        w = int(0.005 * sr); h = int(0.001 * sr); m = max(0, (len(y) - w) // h)
        cs = np.concatenate([[0.0], np.cumsum(y * y)]); idx = np.arange(m) * h
        db = 10 * np.log10((cs[idx + w] - cs[idx]) / w + 1e-14)
        ax2 = ax.twinx(); ax2.plot(t0 + (idx + w / 2) / sr, db, color='cyan', lw=0.7); ax2.set_ylim(-100, 0)
        ax2.axhline(-60, color='cyan', lw=0.4, ls=':')
        ax2.set_ylabel('dBFS (5 ms RMS)')
        for l in sel:
            a, b = (l['src_span'] if src else l['out'])
            ax.axvspan(a, b, ymin=0.96, ymax=1.0, color='w' if l['who'] == 'N' else 'lime', alpha=0.8)
            ax.text(a, 11300, ('%s: ' % l['who'] if l['who'] != 'N' else '') + l['en'][:38], color='w', fontsize=7.5,
                    va='top', clip_on=True)
            if not src and l['i'] < i1:
                ax.text(b + 0.02, 600, '%.2f' % l['gap_after'], color='yellow', fontsize=8)
        if src:
            for l in sel:
                for r in l['removed_inside']:
                    ax.axvspan(r['src'][0], r['src'][1], color='red', alpha=0.25)
            for r in edl['removed_between_lines']:
                if s0 <= r['src'][0] <= s1: ax.axvspan(r['src'][0], r['src'][1], color='red', alpha=0.25)
        ax.set_title(title, fontsize=10, loc='left')
    fig.suptitle(f'{name}: {why}   (red: removed from the take; yellow: the gap after each line, s)', fontsize=11, x=0.01, ha='left')
    plt.tight_layout()
    out = os.path.join(V.TESTS, 'strip_%02d_%s.png' % (k, name))
    plt.savefig(out, dpi=50); plt.close()
    return out


# ============================================================================ scans
def islands_of(x, thr=-60.0):
    db = V.envelope(x)
    return db, V.islands(db, thr)


def scan_gaps(edl, x):
    """Measured silence between lines vs the map."""
    db = V.envelope(x)
    def first_sound(t):
        k = int(t * 1000)
        while k < len(db) and db[k] <= -60: k += 1
        return k / 1000
    def last_sound(t):
        k = int(t * 1000)
        while k > 0 and db[k] <= -60: k -= 1
        return k / 1000 + 0.005
    rows, bad = [], []
    L = edl['lines']
    for a, b in zip(L, L[1:]):
        e = last_sound(a['out'][1] + 0.02); s = first_sound(b['out'][0] - 0.02)
        g = round(s - e, 3)
        rows.append((a['i'], g, a['gap_after']))
        dev = g - a['gap_after']
        if abs(dev) > 0.03: bad.append({'i': a['i'], 'measured': g, 'map': a['gap_after'], 'en': a['en'][:50]})
    gaps = np.array([r[1] for r in rows])
    return {'n': len(rows), 'max_abs_dev_vs_map': round(float(np.max(np.abs(gaps - np.array([r[2] for r in rows])))), 3),
            'off_map_over_30ms': bad[:40], 'n_off_map': len(bad),
            'under_0.15': [r for r in rows if r[1] < 0.149], 'over_2.0': [r for r in rows if r[1] > 2.0],
            'histogram_s': {f'{lo:.2f}-{hi:.2f}': int(((gaps >= lo) & (gaps < hi)).sum())
                            for lo, hi in [(0, 0.15), (0.15, 0.25), (0.25, 0.35), (0.35, 0.5), (0.5, 0.7), (0.7, 1.0),
                                           (1.0, 1.5), (1.5, 2.0), (2.0, 3.5)]}}


def scan_breaths(x):
    """Isolated unvoiced sound islands >= 80 ms in the edited file (what a breath looks like)."""
    import parselmouth
    db = V.envelope(x)
    isl = V.islands(db)
    x24 = x[::2]
    p = parselmouth.Sound(x24, sampling_frequency=24000).to_pitch_ac(time_step=0.005, pitch_floor=70, pitch_ceiling=600)
    f0 = p.selected_array['frequency']; tp = p.xs()
    voiced = np.zeros(len(db), bool)
    for t, f in zip(tp, f0):
        if f > 0: voiced[max(0, int(t * 1000) - 3):int(t * 1000) + 3] = True
    out = []
    for j, (a, b) in enumerate(isl):
        if b - a < 0.08: continue
        vf = voiced[int(a * 1000):int(b * 1000)].mean()
        if vf >= 0.2: continue
        gp = a - isl[j - 1][1] if j else 9; gn = isl[j + 1][0] - b if j + 1 < len(isl) else 9
        if min(gp, gn) < 0.06: continue
        out.append({'t': [round(a, 3), round(b, 3)], 'peak_db': round(float(db[int(a * 1000):int(b * 1000)].max()), 1),
                    'gap_before': round(gp, 3), 'gap_after': round(gn, 3)})
    return out


def step_clicks(x):
    """Sample discontinuities: |x[n] - x[n-1]| above 12x its 10 ms moving mean, in sound (one hit per 20 ms)."""
    from scipy.ndimage import uniform_filter1d
    d = np.abs(np.diff(x))
    ref = uniform_filter1d(d, size=int(0.010 * SR) + 1, mode='nearest')
    loud = np.abs(x[1:]) > 10 ** (-60 / 20)
    cand = np.where((d > 12 * ref + 1e-4) & loud)[0]
    out, last = [], -10 * SR
    for k in cand:
        if k - last < int(0.02 * SR): continue
        out.append(k); last = k
    return np.array(out, dtype=np.int64)


def scan_clicks(x, edl, raw48=None):
    """Discontinuities in the edit vs the same detector on the raw take (TTS plosive bursts trip it too: what matters
    is that the edit adds none), the ones within 5 ms of an edit point, and non-zero samples inside the gaps."""
    hits = step_clicks(x)
    edges = np.array(sorted(int(round(t * SR)) for l in edl['lines'] for pc in l['pieces'] for t in pc['out']))
    near = []
    if len(hits) and len(edges):
        pos = np.searchsorted(edges, hits)
        for h, p_ in zip(hits, pos):
            dmin = min(abs(h - edges[min(p_, len(edges) - 1)]), abs(h - edges[max(p_ - 1, 0)]))
            if dmin <= int(0.005 * SR): near.append(round(h / SR, 4))
    nz = []
    L = edl['lines']
    for a, b in zip(L, L[1:]):
        g0, g1 = int((a['out'][1] + 0.040) * SR), int((b['out'][0] - 0.025) * SR)
        if g1 > g0 and np.abs(x[g0:g1]).max() > 0:
            nz.append({'i': a['i'], 'max_dbfs': round(float(20 * np.log10(np.abs(x[g0:g1]).max())), 1)})
    r = {'n_discontinuities': int(len(hits)), 'at_edit_points': near, 'nonzero_in_gaps': nz}
    if raw48 is not None:
        r['n_discontinuities_raw_take'] = int(len(step_clicks(raw48)))
    return r


def scan_levels(x, edl):
    lv = []
    for l in edl['lines']:
        if l['who'] != 'N' or len(l['en']) < 12: continue
        a, b = l['out']
        lv.append(V.speech_level(x[int(a * SR):int(b * SR)]))
    lv = np.array(lv)
    return {'narrator_line_level_p5_p50_p95_db': [round(float(np.percentile(lv, q)), 2) for q in (5, 50, 95)],
            'narrator_line_level_std_db': round(float(lv.std()), 2)}


def asr_check(edl, x):
    """Re-recognise the character lines and the repaired phrases on the edited file."""
    import sherpa_onnx, soxr
    PK = os.path.join(V.os.path.dirname(V.os.path.abspath(__file__)), '')  # noqa
    MODELS = '/tmp/claude-0/-home-user-claude-todo-demo/aa250ae7-a0b4-594f-9bc6-bd18b596cf27/scratchpad/models'
    PK = os.environ.get('PARAKEET_DIR', os.path.join(MODELS, 'sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8'))
    pk = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f'{PK}/encoder.int8.onnx', decoder=f'{PK}/decoder.int8.onnx',
                                                       joiner=f'{PK}/joiner.int8.onnx', tokens=f'{PK}/tokens.txt',
                                                       model_type='nemo_transducer', num_threads=2)
    import difflib
    rows = []
    fixed = set(V.FIXES)
    for l in edl['lines']:
        if l['who'] == 'N' and l['tag'] not in fixed: continue
        a, b = l['out']
        y = x[max(0, int((a - 0.15) * SR)):int((b + 0.15) * SR)]
        y16 = soxr.resample(np.concatenate([np.zeros(SR // 4), y, np.zeros(SR // 4)]), SR, 16000).astype(np.float32)
        st = pk.create_stream(); st.accept_waveform(16000, y16); pk.decode_stream(st)
        heard = st.result.text.strip()
        A, B = V.toks(l['en']), V.toks(heard)
        sm = difflib.SequenceMatcher(None, A, B, autojunk=False)
        share = sum(bl.size for bl in sm.get_matching_blocks()) / max(1, len(A))
        rows.append({'i': l['i'], 'who': l['who'], 'tag': l['tag'], 'en': l['en'], 'heard': heard, 'share': round(share, 2)})
    return rows


def main():
    os.makedirs(V.TESTS, exist_ok=True)
    edl, en, cl, raw, raw_sr = load()
    res = {}
    if '--no-strips' not in sys.argv:
        res['strips'] = [os.path.basename(strip(n, a, b, w, edl, en, raw, raw_sr, k + 1)) for k, (n, a, b, w) in enumerate(SPOTS)]
    res['gaps'] = scan_gaps(edl, en)
    res['breaths_en'] = scan_breaths(en)
    res['breaths_clean'] = scan_breaths(cl)
    import soxr
    raw48 = soxr.resample(raw, raw_sr, SR, quality='VHQ')
    res['clicks_en'] = scan_clicks(en, edl)
    res['clicks_clean'] = scan_clicks(cl, edl, raw48)
    res['levels_clean'] = scan_levels(cl, edl)
    res['full_scale_samples_en'] = int((np.abs(en) >= 0.999).sum())
    res['true_peak_en'] = round(V.true_peak(en), 2); res['lufs_en'] = round(V.loudness(en), 2)
    res['true_peak_clean'] = round(V.true_peak(cl), 2); res['lufs_clean'] = round(V.loudness(cl), 2)
    if '--no-asr' not in sys.argv:
        res['asr'] = asr_check(edl, en)
    json.dump(res, open(os.path.join(V.TESTS, 'check.json'), 'w'), indent=1)
    g = res['gaps']
    print(f"gaps: {g['n']} boundaries, max |measured - map| {g['max_abs_dev_vs_map']} s, {g['n_off_map']} off by > 30 ms, "
          f"{len(g['under_0.15'])} under 0.15 s, {len(g['over_2.0'])} over 2 s; histogram {g['histogram_s']}")
    print(f"breath-like islands: en {len(res['breaths_en'])}, clean {len(res['breaths_clean'])}")
    for b in res['breaths_en'][:20]: print('   ', b)
    for k in ('clicks_en', 'clicks_clean'):
        c = res[k]
        print(f"{k}: {c['n_discontinuities']} step detections (raw take: {c.get('n_discontinuities_raw_take', '-')}), "
              f"{len(c['at_edit_points'])} within 5 ms of an edit point {c['at_edit_points'][:10]}, "
              f"non-zero samples in {len(c['nonzero_in_gaps'])} gaps")
    print('levels', res['levels_clean'], 'full-scale samples', res['full_scale_samples_en'],
          'TP en/clean', res['true_peak_en'], res['true_peak_clean'], 'LUFS en/clean', res['lufs_en'], res['lufs_clean'])
    if 'asr' in res:
        for r in res['asr']:
            print('   asr %-2s %4.2f  %-48s | %s' % (r['who'], r['share'], r['en'][:48], r['heard']))


if __name__ == '__main__':
    main()
