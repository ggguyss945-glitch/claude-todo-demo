"""Measured checks of the edited voice track (run as `python3 tools/vo_edit.py check`, or directly).
    python3 tools/vo_check.py        -> prints, writes W/narration/check.json; exit 1 on a failure
Scans narration_en.wav against edit_list.json:
  gaps      the silence between every two lines on the file (last sound above -60 dBFS to the next first sound) vs
            the planned pause (+-30 ms; a staged line's fx tail may run into its gap)
  edges     every line's first and last 4 ms: more than 20 dB under the line's speech level (or a forced split with its
            8 ms fade): no word clipped at a cut; every join inside a line likewise
  breaths   residual breath-like events: sound islands (> -60 dBFS) that are unvoiced (pitch on < 15 % of frames),
            last >= 80 ms, sit >= 60 ms from voiced sound, have a breath's spectrum (centroid < 3.5 kHz: a t / k / s
            release is higher) and no recognised word starting within 0.7 s before them (whispered and devoiced
            words are listed, not failed); two within 0.5 s = a double breath
  clicks    a step between neighbouring samples > 12x the local RMS step, in sound (> -50 dBFS)
  levels    each line's speech level on the file vs the narrator's median (median per voice; a line > 6 dB off fails,
            4-6 dB is listed: the narrator's own whispers)
  peaks     true peak (<= -0.9 dBTP), total length
"""
import json, os, sys
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vo_edit as V                                                 # noqa: E402

SR = V.SR


# lines whose one unvoiced island was measured to be a word's consonant, not a breath (tag: evidence)
KNOWN_UNVOICED = {'blank_one_for_warm': 'the "th" of "three" in her sung line: raw take 60.80-60.90 s is noise above '
                                        '2.5 kHz only (-52..-58 dB, nothing under 800 Hz), voicing from 60.94 s'}


def main():
    y, sr = sf.read(V.OUT, dtype='float64'); assert sr == SR
    d = json.load(open(V.EDL)); el = d['lines']
    e = V.envelope(y)
    res, fails = {}, []
    # gaps
    gaps = []
    for a, b in zip(el[:-1], el[1:]):
        lo, hi = int(a['out'][1] * 1000) - 150, int(b['out'][0] * 1000) + 150
        seg = e[lo:hi] > -60
        idx = np.where(seg)[0]
        # last sound of a / first sound of b around the planned edges
        mid = int((a['out'][1] + min(a.get('fx_tail', 0), max(0.0, a['pause'] - 0.10)) + b['out'][0]) * 500) - lo
        s_end = (lo + idx[idx < mid].max()) / 1000 + 0.005 if (idx < mid).any() else a['out'][1]
        s_beg = (lo + idx[idx >= mid].min()) / 1000 if (idx >= mid).any() else b['out'][0]
        g = s_beg - s_end
        err = g - a['pause']
        soft = 0.06 if (a.get('fx') or b.get('fx') or a.get('voice') or b.get('voice')) else 0.0   # a processed
        tail = min(a.get('fx_tail', 0), max(0.0, a['pause'] - 0.10))          # an fx decay runs into its gap
        if err < -0.03 - soft - tail or err > 0.045 + a.get('fx_tail', 0) + soft:   # (a decay under -60 dBFS reads as gap)         # line's quiet onset / decay
            gaps.append([a['i'], a['tag'], round(a['pause'], 3), round(g, 3)])
    res['gaps_off'] = gaps
    # edges and joins
    edges = []
    for x in el:
        a, b = int(x['out'][0] * SR), int(x['out'][1] * SR)
        z = y[a:b]
        lvl = V.speech_level(z)
        n = int(0.004 * SR)
        for where, w, forced in (('start', z[:n], x['forced'][0]), ('end', z[-n:], x['forced'][1])):
            l = 10 * np.log10(np.mean(w ** 2) + 1e-20)
            if l > lvl - 20 and not forced and not x.get('fx'):
                edges.append([x['i'], x['tag'], where, round(l - lvl, 1)])
    res['edges_loud'] = edges
    # breaths (on the dry narration path the voicing tracker is reliable; whispered lines are listed)
    import parselmouth
    p = parselmouth.Sound(y, sampling_frequency=SR).to_pitch_ac(time_step=0.005, pitch_floor=65, pitch_ceiling=600,
                                                                 voicing_threshold=0.45)
    v = np.zeros(len(e), bool)
    for t, f in zip(p.xs(), p.selected_array['frequency']):
        if f > 0: k = int(t * 1000); v[max(0, k - 3):k + 3] = True
    vi = np.where(v)[0] / 1000.0
    words = json.load(open(os.path.join(V.W, 'align', 'asr_cache.json')))['en_words'] if os.path.exists(
        os.path.join(V.W, 'align', 'asr_cache.json')) else []
    wt = np.array([w[1] for w in words]) if words else np.zeros(0)
    br, whisper = [], []
    for s, t in V.islands(e):
        i0, i1 = int(s * 1000), int(t * 1000)
        if t - s < 0.08 or v[i0:i1].mean() >= 0.15: continue
        near = np.abs(vi - s).min() if len(vi) else 9
        near = min(near, np.abs(vi - t).min() if len(vi) else 9)
        if near < 0.06: continue
        line = next((x for x in el if x['out'][0] - 0.01 <= s <= x['out'][1] + 0.01), None)
        has_word = (len(wt) and ((wt >= s - 0.7) & (wt <= t + 0.05)).any()) or V.centroid(y[int(s * SR):int(t * SR)]) >= 3500
        row = [round(s, 3), round(t - s, 3), line['tag'] if line else None]
        (whisper if has_word else br).append(row)
    known = [r for r in br if r[2] in KNOWN_UNVOICED]               # measured by hand: a word's own consonant
    br = [r for r in br if r[2] not in KNOWN_UNVOICED]; whisper += known
    res['breaths'] = br; res['unvoiced_words'] = whisper
    res['double_breaths'] = [[a, b] for a, b in zip(br, br[1:]) if b[0] - (a[0] + a[1]) < 0.5]
    # clicks
    dy = np.abs(np.diff(y))
    w = int(0.002 * SR)
    loc = np.sqrt(np.convolve(dy ** 2, np.ones(w) / w, mode='same')) + 1e-9
    k = np.where((dy > 12 * loc) & (np.abs(y[1:]) > 10 ** (-50 / 20)))[0]
    res['clicks'] = sorted(set(round(i / SR, 2) for i in k))[:50]
    # levels
    nar = d['narrator_median_db']
    lv = {}
    for x in el:
        a, b = int(x['out'][0] * SR), int(x['out'][1] * SR)
        lv.setdefault(x['who'], []).append((x['i'], x['tag'], V.speech_level(y[a:b]) - d['final_gain_db']))
    res['level_median_vs_narrator_db'] = {k: round(float(np.median([r[2] for r in r_])) - nar, 2) for k, r_ in lv.items()}
    res['level_off'] = [[i, t, round(l - nar, 1)] for r_ in lv.values() for i, t, l in r_ if abs(l - nar) > 6.0]
    res['level_note'] = [[i, t, round(l - nar, 1)] for r_ in lv.values() for i, t, l in r_ if 4.0 < abs(l - nar) <= 6.0]
    # peaks, length
    res['true_peak_dbtp'] = round(20 * np.log10(V.true_peak(y)), 2)
    res['duration'] = round(len(y) / SR, 3)
    m, s = divmod(res['duration'], 60)
    print('length %d:%05.2f, true peak %.2f dBTP' % (m, s, res['true_peak_dbtp']))
    print('gaps off plan: %d %s' % (len(gaps), gaps[:8]))
    print('loud line edges (clipped word?): %d %s' % (len(edges), edges[:8]))
    print('residual breaths: %d %s | double: %d' % (len(br), br[:8], len(res['double_breaths'])))
    print('unvoiced islands holding words (whispers, listed): %d' % len(whisper))
    print('clicks: %d %s' % (len(res['clicks']), res['clicks'][:10]))
    print('level vs narrator median (dB):', res['level_median_vs_narrator_db'], '| lines > 6 dB off:', res['level_off'],
          '| 4-6 dB (listed):', res['level_note'])
    fails = gaps or edges or br or res['clicks'] or res['level_off'] or res['true_peak_dbtp'] > -0.9
    res['pass'] = not fails
    json.dump(res, open(os.path.join(V.N, 'check.json'), 'w'), indent=1)
    print('check:', 'PASS' if not fails else 'FAIL')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
