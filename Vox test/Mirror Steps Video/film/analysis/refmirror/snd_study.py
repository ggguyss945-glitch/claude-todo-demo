"""snd_study.py: the sound study's numbers from snd_env.py envelopes (references and our mixes).

    python3 analysis/refmirror/snd_study.py ENV_DIR [names...] [--json OUT.json] [--profiles OUT.png]

For every NAME.npz in ENV_DIR (default: all): loudness (integrated, EBU-style LRA from the 3 s short-term, momentary
max and short-term p95 over the integrated), the bed relative to the voice (integrated, short-term p10/50/90, bed LRA),
bed swells (rises >= 8 LU inside 20 s), hits (bed jumps >= 8 dB in 0.3 s to within 8 LU of the voice), drop-outs
(bed >= 10 dB under its last 3 s for >= 0.4 s), the suck-out before hits, risers into hits, bed onsets per minute
(spectral flux peaks: the SFX / note activity), the low share of the bed, and the bed profile around the rule cards
(references: the ASR's "Rule number"; ours: the narration timeline). Times in the npz are k / 10 s.
"""
import argparse, glob, json, os, re
import numpy as np

W = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '_work'))
HOP = 0.1


def rule_times(name):
    """Times of "Rule number" (references: ASR words; ours: timeline lines)."""
    if name.startswith('ours'):
        tl = json.load(open(os.path.join(W, 'align', 'timeline.json')))
        return [l['t'] for l in tl['lines'] if l['en'].lower().startswith('rule number')]
    p = os.path.join(W, 'ref2', 'data', f'asr_{name}.json')
    if not os.path.exists(p):
        return []
    out = []
    for seg in json.load(open(p)):
        w = seg['words']
        for i in range(len(w) - 1):
            if re.sub(r'\W', '', w[i][1].lower()) == 'rule' and re.sub(r'\W', '', w[i + 1][1].lower()) == 'number':
                if not out or w[i][0] - out[-1] > 20:
                    out.append(w[i][0])
    return out


def pct(x, q):
    return round(float(np.percentile(x, q)), 1)


def lra(S):
    s = S[S > -70]
    if not len(s):
        return 0.0
    g = 10 * np.log10(np.mean(10 ** (s / 10))) - 20
    s = s[s > g]
    return round(float(np.percentile(s, 95) - np.percentile(s, 10)), 1)


def study(d, name):
    I = float(d['I_mix']); M = d['mix_M']; S = d['mix_S']; n = len(M); mins = n * HOP / 60
    R = dict(name=name, dur=round(n * HOP, 1), I_mix=round(I, 2), LRA=lra(S),
             mom_max_over_I=round(float(M.max() - I), 1), st_p95_over_I=round(float(np.percentile(S[S > -70], 95) - I), 1),
             st_p10_50_90_over_I=[pct(S[S > -70] - I, q) for q in (10, 50, 90)])
    if 'bed_M' not in d:
        return R, None
    Iv = float(d['I_voice']); B = d['bed_M'].astype(float) - Iv; BS = d['bed_S'].astype(float) - Iv
    V = d['voice_M'].astype(float) - Iv
    m = min(len(B), len(V), n); B, BS, V = B[:m], BS[:m], V[:m]
    speech = V > -20
    R.update(I_voice=round(Iv, 2), bed_rel_voice=round(float(d['I_bed']) - Iv, 1),
             bed_st_p10_50_90=[pct(BS[BS > -60], q) for q in (10, 50, 90)], bed_LRA=lra(BS + Iv),
             bed_speech_p50=pct(B[speech], 50), bed_gap_p50=pct(B[~speech], 50) if (~speech).any() else None,
             narration_pct=round(100 * float(speech.mean()), 1))
    # swells: from a local minimum to the max in the next 20 s, >= 8 LU (short-term), counted once per 10 s
    sw = []; i = 0
    while i < m - 30:
        j = i + int(20 / HOP)
        k = i + int(np.argmax(BS[i:j]))
        if BS[k] - BS[i] >= 8 and BS[i] <= BS[max(0, i - 30):i + 1].min() + 0.5:
            sw.append((i * HOP, k * HOP, float(BS[k] - BS[i]))); i = k + 50
        else:
            i += 5
    R['swells_per_min'] = round(len(sw) / mins, 2)
    R['swell_len_gain_p50'] = [round(float(np.median([b - a for a, b, g in sw])), 1), round(float(np.median([g for a, b, g in sw])), 1)] if sw else None
    # hits: momentary jump >= 8 dB within 0.3 s, peak within 8 LU of the voice, >= 1.5 s apart
    hits = []
    for i in range(5, m - 5):
        if B[i] > -8 and B[i] - B[i - 3] >= 8 and B[i] >= B[i - 1] and B[i] >= B[i + 1] - 0.3:
            if not hits or (i - hits[-1]) * HOP > 1.5:
                hits.append(i)
    R['hits_per_min'] = round(len(hits) / mins, 2)
    if hits:
        pre = [float(np.mean(B[max(0, h - 15):h - 3])) for h in hits if h > 40]
        far = [float(np.mean(B[h - 40:h - 20])) for h in hits if h > 40]
        R['hit_peak_rel_voice_p50_max'] = [pct(B[hits], 50), round(float(B[hits].max()), 1)]
        R['hit_contrast_p50'] = round(float(np.median([B[h] - p for h, p in zip([h for h in hits if h > 40], pre)])), 1)
        R['pre_hit_suck_db_p50'] = round(float(np.median(np.array(far) - np.array(pre))), 1)   # (-4..-2 s) - (-1.5..-0.3 s)
        R['hits_under_speech_pct'] = round(100 * float(np.mean([V[h - 2:h + 3].max() > -20 for h in hits])), 0)
        # risers: short-term rising >= 5 LU over the 6 s before the hit's suck-out
        ris = 0
        for h in hits:
            if h > 80:
                a = BS[h - 80:h - 10]
                if a[-10:].mean() - a[:10].mean() >= 5:
                    ris += 1
        R['hits_after_rise_pct'] = round(100 * ris / max(1, sum(1 for h in hits if h > 80)), 0)
        # decay: time from the hit peak until the bed is 10 dB down
        dec = []
        for h in hits:
            k = np.flatnonzero(B[h:h + 80] < B[h] - 10)
            dec.append(k[0] * HOP if len(k) else 8.0)
        R['hit_decay10_s_p50'] = round(float(np.median(dec)), 2)
    # drop-outs: bed >= 10 dB under the median of the 3 s before, for >= 0.4 s
    drops = []; run = 0
    for i in range(30, m):
        ref = np.median(B[i - 30:i - 4]) if run == 0 else ref
        if B[i] < ref - 10:
            run += 1
        else:
            if run >= 4:
                drops.append((i - run, run, float(ref - np.mean(B[i - run:i]))))
            run = 0
    R['dropouts_per_min'] = round(len(drops) / mins, 2)
    if drops:
        R['dropout_len_p50_max'] = [round(float(np.median([r for _, r, _ in drops])) * HOP, 2), round(max(r for _, r, _ in drops) * HOP, 2)]
        R['dropout_depth_p50'] = round(float(np.median([dd for _, _, dd in drops])), 1)
        R['dropout_then_hit_pct'] = round(100 * float(np.mean([any(0 <= (h - (a + r)) * HOP <= 1.2 for h in hits) for a, r, _ in drops])), 0)
        R['dropout_under_speech_pct'] = round(100 * float(np.mean([V[a:a + r].max() > -20 for a, r, _ in drops])), 0)
    # quiet stretches: share of time the bed is under voice - 25 (momentary, 1 s smoothed)
    Bs = np.convolve(B, np.ones(10) / 10, 'same')
    R['bed_under_25_pct'] = round(100 * float((Bs < -25).mean()), 1)
    R['bed_over_10_pct'] = round(100 * float((Bs > -10).mean()), 1)
    # onsets: spectral flux peaks above a running median (bed activity), per minute, and strong ones
    F = d['bed_F'].astype(float)
    med = np.convolve(F, np.ones(150) / 150, 'same')
    pk = [i for i in range(2, len(F) - 2) if F[i] == F[i - 2:i + 3].max() and F[i] > 2.0 * med[i] + 0.02]
    pk2 = []
    for i in pk:
        if not pk2 or i - pk2[-1] > 8:
            pk2.append(i)
    R['bed_onsets_per_min'] = round(len(pk2) / mins, 1)
    strong = [i for i in pk2 if F[i] > 4 * med[i] + 0.05]
    R['bed_strong_onsets_per_min'] = round(len(strong) / mins, 1)
    # spectrum: share of the bed's power under 250 Hz (bands 20-60, 60-250) over time
    Bb = d['bed_B'].astype(float)
    P = 10 ** (Bb / 10)
    R['bed_low_share_pct'] = round(100 * float(P[:2].sum() / P.sum()), 1)
    R['bed_band_db_rel_mid'] = [round(float(10 * np.log10(P[k].mean() / P[2].mean())), 1) for k in range(len(P))]
    if 'voice_B' in d:                                 # clarity: voice over bed in 1-4 kHz while the narration runs
        vb = d['voice_B'].astype(float); k = min(vb.shape[1], Bb.shape[1], len(speech))
        R['voice_over_bed_1_4k_speech_p10_p50'] = [pct((vb[3, :k] - Bb[3, :k])[speech[:k]], q) for q in (10, 50)]
    # rule cards: bed profile around "Rule number"
    rt = rule_times(name)
    dts = [-10, -6, -3, -1.5, -0.5, 0, 0.5, 1, 2, 3, 5, 8]
    prof = []
    for t in rt:
        row = [float(np.mean(B[int((t + dt) / HOP) - 2:int((t + dt) / HOP) + 3])) if 0 < int((t + dt) / HOP) < m - 3 else np.nan
               for dt in dts]
        prof.append(row)
    if prof:
        R['rule_cards'] = len(rt)
        R['rule_bed_profile'] = dict(dt=dts, median=[round(float(np.nanmedian([r[j] for r in prof])), 1) for j in range(len(dts))])
    # by tenth: bed level and mix short-term
    R['bed_by_tenth'] = [round(float(10 * np.log10(np.mean(10 ** (B[k * m // 10:(k + 1) * m // 10] / 10)))), 1) for k in range(10)]
    R['mix_by_tenth_over_I'] = [round(float(10 * np.log10(np.mean(10 ** (M[k * m // 10:(k + 1) * m // 10] / 10))) - I), 1) for k in range(10)]
    return R, dict(hits=[h * HOP for h in hits], drops=[(a * HOP, r * HOP, dd) for a, r, dd in drops], swells=sw, rules=rt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dir'); ap.add_argument('names', nargs='*'); ap.add_argument('--json'); ap.add_argument('--events')
    A = ap.parse_args()
    names = A.names or sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(A.dir, '*.npz')))
    out = {}; ev = {}
    for nm in names:
        d = dict(np.load(os.path.join(A.dir, nm + '.npz')))
        R, E = study(d, nm)
        out[nm] = R; ev[nm] = E
        print(json.dumps(R))
    if A.json:
        json.dump(out, open(A.json, 'w'), indent=1)
    if A.events:
        json.dump(ev, open(A.events, 'w'), indent=0, default=float)


if __name__ == '__main__':
    main()
