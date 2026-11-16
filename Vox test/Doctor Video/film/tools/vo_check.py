"""Checks for the edited narration (run as `python3 vo_edit.py check`, or directly).
    python3 vo_check.py [--no-strips] [--no-asr]
Writes into W/narration/tests/:
  strip_XX_<name>.png   before / after: the raw take (top) and the edit (bottom) of the same lines, spectrogram + 5 ms
                        RMS (dBFS) + line labels; 27 spots (rule transitions, reveal beats, every character voice, the counts,
                        the comment prompt, the outro, every repaired slip)
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
    ('cold_open', 'open_room', 'open_dont_sit', 'the hook: the spliced "and he", the Waiting Man (W) "Take a seat. It can '
                                                'wait." (the "Takes" hiss cut), held 1.2 s'),
    ('recording', 'open_dont_sit', 'seven_rules', 'the phone-system recording (R), 1.0 s in and out'),
    ('g1979', 'voice_line', 'still_waiting', '"Calm. Patient. Kind." staccato, the 1979 voice (W, phone), the held '
                                             '"Still waiting."'),
    ('nurses', 'mom_noticed', 'halverson', 'the rebuilt "Nurses always notice." (Nurse + the "is" of "his pulse")'),
    ('promise', 'blood', 'shift', 'Doctor Halverson (H) split from "she said." where the sh starts'),
    ('rule1', 'nobody_sick', 'call', 'Grandma (G), 1.4 s before "Rule number one.", 1.0 s after the rule text, room '
                                     'for the ring'),
    ('call_3am', 'running_crying', 'hung_up', 'Doctor Halverson on the 3 AM call (H_call: rough, out of breath), '
                                              'Grandma cuts her off (G_sharp)'),
    ('cta', 'other_one', 'cta_forty', '1.0 s before the comment prompt and its rhythm'),
    ('rule2_ever', 'rule2', 'rang_anyway', '"Ever." split from "The phone cord" (the take ran them together), 1.0 s '
                                           'after the rule'),
    ('chair_rule3', 'rooms_living', 'rule3_listening', '0.9 s before "From Grandpa\'s chair.", the "chair / Rule" split '
                                                       'in their shared r, the rebuilt "Rule"'),
    ('milo', 'eyes_big', 'pen_click', 'Milo (K: a child\'s whisper), Grandma hushing (G_hush), 1.0 s for the pen click'),
    ('door', 'car_driveway', 'didnt_open', 'Doctor Halverson through the door (H_door), Grandma (G), the repaired '
                                           '"said Doctor Halverson."'),
    ('note_signs', 'marker', 'burn', 'the warning signs on the note, read as a list (0.4 s apart)'),
    ('bench', 'bus_stop', 'rule5_text', '"Knees above his head. / Waiting. / Rule number five." (one run in the take): '
                                        'held 1.3 s, 1.4 s before the rule'),
    ('told_1979', 'g_wait2', 'stopped_rocking', 'Grandma rocking (G_soft), the narrator, the "in 1979" double cut'),
    ('rows', 'waiting_room', 'tv', 'the rebuilt "Rows of plastic chairs"'),
    ('grandpa_him', 'last_row', 'him', 'held 1.5 s before "Grandpa." and 1.3 s after it'),
    ('take_a_seat', 'ticket_milo', 'rule7', 'the Waiting Man (W) in the waiting room, 1.4 s before rule 7'),
    ('counts', 'began_count', 'one_thing', 'the counts (W_count) spaced like slow counting, slowing (1.0-1.3 s)'),
    ('car', 'clicking_car', 'h_mirror', 'the Waiting Man in the back seat (W), "he said."'),
    ('nurse_er', 'nurse', 'empty_chair', 'the ER nurse (U)'),
    ('mom_call', 'dialed', 'grandma_fine', 'Mom (M)'),
    ('twist', 'burned', 'pediatrician', 'held 1.0 s before and after "Not as a patient."'),
    ('office', 'work_nights', 'nineteen_hours', 'the "I\'m s- I\'m sitting" repair'),
    ('outro', 'very_patient', 'light_on', '1.3 s before "So are we.", 2.8 s before "Okay. Breathe."'),
    ('voice_in_head', 'little_real', 'very_very_patient', 'the voice in your head (W_whisper)'),
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


def scan_breaths(x, edl=None):
    """Isolated unvoiced sound islands >= 80 ms in the edited file (what a breath looks like): sound islands (> -60 dBFS)
    that sit >= 60 ms from any other sound and whose own pitch track (Praat, on the island +-20 ms alone, so a quiet
    passage is not judged against the loudest one) is voiced in under 20 % of its frames. With the edit list, each is
    classed: 'final consonant' (it ends its line and the line's last word ends in a stop / fricative / affricate: the
    release or the s the take spells out after a closure), 'the whole line' (an unvoiced line, "Shh."), or 'check'."""
    import parselmouth
    db = V.envelope(x)
    isl = V.islands(db)
    out = []
    for j, (a, b) in enumerate(isl):
        if b - a < 0.08: continue
        gp = a - isl[j - 1][1] if j else 9; gn = isl[j + 1][0] - b if j + 1 < len(isl) else 9
        if min(gp, gn) < 0.06: continue
        seg = x[max(0, int((a - 0.02) * SR)):int((b + 0.02) * SR)]
        p = parselmouth.Sound(seg, sampling_frequency=SR).to_pitch_ac(time_step=0.005, pitch_floor=70, pitch_ceiling=600)
        f0 = p.selected_array['frequency']
        if len(f0) and (f0 > 0).mean() >= 0.2: continue
        r = {'t': [round(a, 3), round(b, 3)], 'peak_db': round(float(db[int(a * 1000):int(b * 1000)].max()), 1),
             'gap_before': round(gp, 3), 'gap_after': round(gn, 3), 'kind': 'check'}
        if edl:
            l = next((l for l in edl['lines'] if l['out'][0] - 0.05 <= a <= l['out'][1] + 0.05), None)
            if l:
                r['line'] = l['i']
                lw = re.sub(r'[^a-z]', '', l['en'].split()[-1].lower())
                if b - a > 0.5 * (l['out'][1] - l['out'][0]): r['kind'] = 'the whole line'
                elif b >= l['out'][1] - 0.06 and re.search(r'(s|z|t|k|p|c|ch|sh|f|th|d|g|x|ce|se|te|ke)$', lw):
                    r['kind'] = 'final consonant'
        out.append(r)
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
    edges = np.array(sorted(int(round(t * SR)) for l in edl['lines'] if 'stretch' not in l
                            for pc in l['pieces'] for t in pc['out']))
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
    res['breaths_en'] = scan_breaths(en, edl)
    res['breaths_clean'] = scan_breaths(cl, edl)
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
    for b in res['breaths_en']:
        if b['kind'] == 'check': print('   check:', b)
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
