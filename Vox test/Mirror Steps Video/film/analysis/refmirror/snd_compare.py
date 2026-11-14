"""snd_compare.py: our mixes against the five references, one table (sound v3).

    python3 analysis/refmirror/snd_compare.py ENV1.npz [ENV2.npz ...] [--json OUT.json]

ENVn: snd_env.py envelopes of our mixes (--stems). The references come from _work/review/snd_v3/env_mix/*.npz (whole
mixes: loudness, LRA, mix punctuation) and _work/review/snd_v3/env_win/*.npz (separated stretches: the bed), pooled:
rates weighted by duration, levels as the median over the stretches. Mix punctuation = momentary peaks >= +4.5 LU over
the integrated loudness that rise >= 5 LU within 0.5 s (8 s apart); "mix drop-outs" = the critic's measure (momentary
< -12 LU for >= 0.4 s). Prints a markdown table.
"""
import argparse, glob, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import snd_study as ST  # noqa: E402

W = ST.W
REFS = ('stadium', 'teacher_dog', 'sibling_stitched', 'vet_dog', 'hazmat720')


def mix_extra(d):
    M = d['mix_M'].astype(float); I = float(d['I_mix']); R = M - I; n = len(R)
    pk = []
    for i in np.argsort(-R):
        if R[i] < 4.5:
            break
        if 90 < i < n - 90 and R[i] - R[i - 5:i].min() >= 5 and all(abs(i - j) > 80 for j in pk):
            pk.append(i)
    run = 0; drops = 0
    for v in R:
        if v < -12:
            run += 1
        else:
            drops += run >= 4; run = 0
    mins = n / 600
    return dict(punct_per_min=round(len(pk) / mins, 2), mix_drops_per_min=round(drops / mins, 2))


def row(d, name):
    R, _ = ST.study(d, name)
    R.update(mix_extra(d))
    return R


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('envs', nargs='+'); ap.add_argument('--json')
    A = ap.parse_args()
    refmix = {n: row(dict(np.load(os.path.join(W, 'review', 'snd_v3', 'env_mix', n + '.npz'))), n) for n in REFS}
    wins = {}
    for p in sorted(glob.glob(os.path.join(W, 'review', 'snd_v3', 'env_win', '*.npz'))):
        n = os.path.basename(p)[:-4]
        wins[n] = row(dict(np.load(p)), n + '_win')
    ours = {os.path.basename(p)[:-4]: row(dict(np.load(p)), 'ours') for p in A.envs}
    dur = {n: v['dur'] for n, v in wins.items()}

    def pooled(k):
        xs = [(v[k], dur[n]) for n, v in wins.items() if v.get(k) is not None]
        return round(sum(a * b for a, b in xs) / sum(b for a, b in xs), 2) if xs else None

    def med(k, j=None):
        xs = [v[k] if j is None else v[k][j] for v in wins.values() if v.get(k) is not None]
        return round(float(np.median(xs)), 1) if xs else None

    def rng(k):
        xs = [v[k] for v in refmix.values()]
        return '%s .. %s' % (min(xs), max(xs))
    T = [('mix integrated (LUFS)', lambda v: v['I_mix'], rng('I_mix')),
         ('mix LRA (LU, EBU-style)', lambda v: v['LRA'], rng('LRA')),
         ('mix momentary max over I (LU)', lambda v: v['mom_max_over_I'], rng('mom_max_over_I')),
         ('mix short-term p10 / p90 over I', lambda v: '%s / %s' % (v['st_p10_50_90_over_I'][0], v['st_p10_50_90_over_I'][2]),
          '%s .. %s / %s .. %s' % (min(v['st_p10_50_90_over_I'][0] for v in refmix.values()), max(v['st_p10_50_90_over_I'][0] for v in refmix.values()),
                                   min(v['st_p10_50_90_over_I'][2] for v in refmix.values()), max(v['st_p10_50_90_over_I'][2] for v in refmix.values()))),
         ('mix punctuation peaks / min', lambda v: v['punct_per_min'], rng('punct_per_min')),
         ('mix drop-outs / min (critic)', lambda v: v['mix_drops_per_min'], rng('mix_drops_per_min')),
         ('bed integrated, LU rel voice', lambda v: v['bed_rel_voice'], med('bed_rel_voice')),
         ('bed short-term p10 / p50 / p90', lambda v: '/'.join(str(x) for x in v['bed_st_p10_50_90']),
          '/'.join(str(med('bed_st_p10_50_90', j)) for j in range(3))),
         ('bed loudness range (LU)', lambda v: v['bed_LRA'], med('bed_LRA')),
         ('bed under speech / in pauses p50', lambda v: '%s / %s' % (v['bed_speech_p50'], v['bed_gap_p50']),
          '%s / %s' % (med('bed_speech_p50'), med('bed_gap_p50'))),
         ('bed swells / min', lambda v: v['swells_per_min'], pooled('swells_per_min')),
         ('bed hits / min', lambda v: v['hits_per_min'], pooled('hits_per_min')),
         ('bed hit peak p50, LU rel voice', lambda v: (v.get('hit_peak_rel_voice_p50_max') or [None])[0],
          round(float(np.median([v['hit_peak_rel_voice_p50_max'][0] for v in wins.values() if v.get('hit_peak_rel_voice_p50_max')])), 1)),
         ('pre-hit suck-out p50 (dB)', lambda v: v.get('pre_hit_suck_db_p50'), med('pre_hit_suck_db_p50')),
         ('bed drop-outs / min, length p50 (s)', lambda v: '%s, %s' % (v['dropouts_per_min'], (v.get('dropout_len_p50_max') or [None])[0]),
          '%s, %s' % (pooled('dropouts_per_min'), round(float(np.median([v['dropout_len_p50_max'][0] for v in wins.values() if v.get('dropout_len_p50_max')])), 2))),
         ('bed onsets / min (strong)', lambda v: '%s (%s)' % (v['bed_onsets_per_min'], v['bed_strong_onsets_per_min']),
          '%s (%s)' % (pooled('bed_onsets_per_min'), pooled('bed_strong_onsets_per_min'))),
         ('bed share under 250 Hz (%)', lambda v: v['bed_low_share_pct'], med('bed_low_share_pct')),
         ('voice over bed at 1-4 kHz in speech p10 / p50 (dB)', lambda v: '%s / %s' % tuple(v.get('voice_over_bed_1_4k_speech_p10_p50') or (None, None)),
          '%s / %s' % (med('voice_over_bed_1_4k_speech_p10_p50', 0), med('voice_over_bed_1_4k_speech_p10_p50', 1))),
         ('bed sub / bass dB over 250 Hz-1 kHz', lambda v: '%s / %s' % tuple(v['bed_band_db_rel_mid'][:2]),
          '%s / %s' % (med('bed_band_db_rel_mid', 0), med('bed_band_db_rel_mid', 1)))]
    names = list(ours)
    print('| measure | ' + ' | '.join(names) + ' | references |')
    print('|---|' + '---|' * len(names) + '---|')
    for lab, f, ref in T:
        print('| %s | %s | %s |' % (lab, ' | '.join(str(f(ours[n])) for n in names), ref))
    # rule card profile (mix, LU over I) and bed profile
    print()
    for n in names:
        print(n, 'rule-card bed profile', ours[n].get('rule_bed_profile'))
    if A.json:
        json.dump(dict(ours=ours, refs_mix=refmix, refs_win=wins), open(A.json, 'w'), indent=1, default=float)


if __name__ == '__main__':
    main()
