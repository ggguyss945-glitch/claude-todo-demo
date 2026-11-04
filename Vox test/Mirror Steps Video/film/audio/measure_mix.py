"""Measure a mirror-film mix against the targets (REF_MIRROR.md sec. 7, AUDIO_SPEC.md), from mix.py's output dir.

    python3 audio/measure_mix.py _work/mix/draft [--cues _work/cues] [--mix mix.wav]      (run from film/)

Reads <dir>/<mix>, <dir>/stems/{voice_en,music,sfx}.wav (float, final gain, before the limiter) and the cue sheets.
Loudness is true BS.1770 (per-channel K-weighting, sfx.py helpers). "rel voice" = relative to the voice stem's
integrated loudness. Writes <dir>/measure.json and prints a table.
"""
import argparse, json, os, sys
import numpy as np, soundfile as sf
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sfx as SX                                  # noqa: E402
import mix as MX                                  # noqa: E402

SR = 48000


def lev(x, win, hop):
    return -0.691 + 10 * np.log10(SX._blocks(x, win, hop) + 1e-20)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dir'); ap.add_argument('--cues', default=None); ap.add_argument('--mix', default='mix.wav')
    A = ap.parse_args()
    cues_dir = A.cues or os.path.join(os.path.dirname(os.path.abspath(A.dir)), '..', 'cues')
    rd = lambda p: sf.read(p, dtype='float32', always_2d=True)[0]
    mix = rd(os.path.join(A.dir, A.mix))
    v = rd(os.path.join(A.dir, 'stems', 'voice_en.wav')); m = rd(os.path.join(A.dir, 'stems', 'music.wav'))
    s = rd(os.path.join(A.dir, 'stems', 'sfx.wav'))
    n = min(len(mix), len(v), len(m), len(s)); mix, v, m, s = mix[:n], v[:n], m[:n], s[:n]
    bed = m + s
    Lv = SX.lufs_int(v)
    R = {'duration_s': round(n / SR, 3), 'mix_lufs': round(SX.lufs_int(mix), 2), 'true_peak_dbtp': round(MX.true_peak(mix), 2),
         'voice_rel_mix': round(Lv - SX.lufs_int(mix), 2), 'music_rel_voice': round(SX.lufs_int(m) - Lv, 2),
         'sfx_rel_voice': round(SX.lufs_int(s) - Lv, 2), 'bed_rel_voice': round(SX.lufs_int(bed) - Lv, 2)}
    # presence: 400 ms momentary, smoothed over 1 s (as analysis/measure.py), relative to the voice integrated
    hop = 0.1
    k = np.ones(10) / 10
    mm = np.convolve(lev(m, 0.4, hop), k, 'same') - Lv; bm = np.convolve(lev(bed, 0.4, hop), k, 'same') - Lv
    vm = lev(v, 0.4, hop) - Lv
    R['music_present_pct'] = {f'>{r}LU': round(100 * float((mm > r).mean()), 1) for r in (-20, -25, -30)}
    R['bed_present_pct'] = {f'>{r}LU': round(100 * float((bm > r).mean()), 1) for r in (-20, -25, -40)}
    st3 = lev(bed, 3.0, 1.0) - Lv
    live = st3[st3 > -60]
    R['bed_short_term_p10_p50_p90'] = [round(float(np.percentile(live, q)), 1) for q in (10, 50, 90)]
    R['bed_lra'] = round(float(np.percentile(live, 95) - np.percentile(live, 10)), 1)
    speech = vm > -20
    R['bed_speech_median'] = round(float(np.median((bm)[speech])), 1)
    R['bed_gap_median'] = round(float(np.median((bm)[~speech])), 1) if (~speech).any() else None
    R['narration_share_pct'] = round(100 * float(speech.mean()), 1)
    mi = lev(mix, 0.4, hop) - SX.lufs_int(mix); s3 = lev(mix, 3.0, 1.0) - SX.lufs_int(mix)
    R['mix_momentary_max_over_int'] = round(float(mi.max()), 1)
    R['mix_short_term_p95_over_int'] = round(float(np.percentile(s3, 95)), 1)
    # spectrum of the bed
    x = bed.mean(1)[::2]
    f, P = signal.welch(x, SR / 2, nperseg=8192)
    tot = P.sum()
    R['bed_spectrum_pct'] = {'<250': round(100 * P[f < 250].sum() / tot, 1), '250-4k': round(100 * P[(f >= 250) & (f < 4000)].sum() / tot, 1),
                             '>4k': round(100 * P[f >= 4000].sum() / tot, 1)}
    band = lambda c: 10 * np.log10(P[(f >= c / 1.414) & (f < c * 1.414)].sum() + 1e-30)
    R['bed_octaves_rel_1k'] = {c: round(band(c) - band(1000), 1) for c in (63, 125, 250, 500, 2000, 4000, 8000)}
    # events from the cues
    sc = json.load(open(os.path.join(cues_dir, 'sfx_cues.json'))); mc = json.load(open(os.path.join(cues_dir, 'music_cues.json')))
    mins = n / SR / 60
    hits = sorted({round(c['t'], 2) for c in sc if c.get('hit') and not c['params'].get('stream')} |
                  {round(e['t'], 2) for e in mc['events'] if e['type'] in ('hit', 'stinger', 'braam')})
    sil = [e for e in mc['events'] if e['type'] == 'silence']
    R['hit_events_per_min'] = round(len(hits) / mins, 2)
    R['silences_per_min'] = round(len(sil) / mins, 2)
    R['one_shot_cues_per_min'] = round(sum(1 for c in sc if not c['params'].get('stream')) / mins, 1)
    # measured transients >= 4 dB (50 ms bed level jumps over the previous 0.5 s mean)
    b50 = lev(bed, 0.05, 0.05)
    base = np.convolve(b50, np.ones(10) / 10, 'full')[:len(b50)]
    jump = b50[10:] - base[9:-1]
    on = np.flatnonzero((jump[1:] >= 4) & (jump[:-1] < 4))
    R['bed_transients_4dB_per_min'] = round(len(on) / mins, 1)
    # hit contrast: bed peak in [0, +0.4] s vs the mean over [-1.5, -0.3] s (dB)
    bt = lev(bed, 0.05, 0.05)
    con = []
    for h in hits:
        i = int(h / 0.05)
        if i - 30 < 0 or i + 8 >= len(bt):
            continue
        pre = 10 * np.log10(np.mean(10 ** (bt[i - 30:i - 6] / 10)))
        con.append(float(bt[i:i + 8].max() - pre))
    R['hit_contrast_db_p50'] = round(float(np.median(con)), 1) if con else None
    hp_ = [float(lev(bed[int(h * SR):int((h + 0.6) * SR)], 0.4, 0.1).max() - Lv) for h in hits if h + 0.6 < n / SR]
    R['hit_peak_rel_voice_p50_max'] = [round(float(np.median(hp_)), 1), round(float(np.max(hp_)), 1)] if hp_ else None
    # silences: depth of the music during each authored silence vs the 1.5 s before
    mt = lev(m, 0.1, 0.05)
    dep = []
    for e in sil:
        a, b = int(e['t'] / 0.05), int((e['t'] + e.get('len', 1.2)) / 0.05)
        if a > 40 and b > a + 2:
            dep.append(float(np.mean(mt[a - 35:a - 5]) - np.mean(mt[a + 2:b])))
    R['silence_depth_db_p50'] = round(float(np.median(dep)), 1) if dep else None
    # rule cards: bed level (3 s short-term... 400 ms) aligned on the card
    cards = [e['t'] for e in mc['events'] if e['type'] == 'rule']
    prof = []
    for c in cards:
        row = []
        for dt in (-7, -5, -3, -1, 0, 0.5, 2, 4):
            i = int((c + dt) / hop)
            row.append(round(float(bm[i]), 1) if 0 <= i < len(bm) else None)
        prof.append(row)
    R['rule_card_bed_profile'] = {'dt': [-7, -5, -3, -1, 0, 0.5, 2, 4], 'median': [
        round(float(np.median([r[j] for r in prof if r[j] is not None])), 1) for j in range(8)]}
    # loudness by music-map section and by quarter
    secs = []
    for sct in mc.get('music_map', []):
        a, b = int(sct['s0'] * SR), int(min(n / SR, sct['s1']) * SR)
        secs.append([sct['s0'], sct['s1'], sct['slug'][:26], round(SX.lufs_int(m[a:b]) - Lv, 1),
                     round(SX.lufs_int(bed[a:b]) - Lv, 1)])
    R['sections_music_bed_rel_voice'] = secs
    q = n // 4
    R['bed_by_quarter'] = [round(SX.lufs_int(bed[i * q:(i + 1) * q]) - Lv, 1) for i in range(4)]
    loud = lev(bed, 10.0, 1.0); R['loudest_10s_bed_at_s'] = int(np.argmax(loud))
    json.dump(R, open(os.path.join(A.dir, 'measure.json'), 'w'), indent=1, default=float)
    for k_, v_ in R.items():
        if k_ != 'sections_music_bed_rel_voice':
            print(f'{k_:32s} {v_}')
    for r in secs:
        print('   ', r)


if __name__ == '__main__':
    main()
