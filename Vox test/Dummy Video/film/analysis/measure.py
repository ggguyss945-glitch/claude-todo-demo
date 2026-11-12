"""Measure a reference video's sound design from its separated stems.

Usage: python3 -I measure.py <name> <mix.wav> <voice.wav> <bed.wav> <cuts.txt> <out.json> [asr.json]

Public API (importable):
  measure(name, mix_path, voice_path, bed_path, cuts_path, asr=None) -> dict
  helpers: kweight(x, sr), momentary(xk, sr, win, hop) -> LUFS per block,
           speech_mask(voice, sr) -> bool per 20 ms frame.
All loudness numbers are BS.1770 (K-weighted); "LU rel voice" = bed loudness minus the
integrated loudness of the voice stem. Times in seconds.
"""
import json, sys
import numpy as np, soundfile as sf, pyloudnorm as pyln, librosa
from scipy.signal import welch

HOP = 0.02  # frame grid for masks / envelopes (s)


def kweight(x, sr):
    m = pyln.Meter(sr)
    y = x.copy()
    for f in m._filters.values():
        y = f.apply_filter(y)
    return y


def momentary(xk, sr, win=0.4, hop=HOP):
    """K-weighted loudness of sliding blocks (centred), one value per hop."""
    p = (xk ** 2).sum(1)
    c = np.concatenate([[0.0], np.cumsum(p)])
    n = len(p); h = int(hop * sr); w = int(win * sr)
    centres = np.arange(0, n, h)
    a = np.clip(centres - w // 2, 0, n); b = np.clip(centres + w // 2, 0, n)
    e = (c[b] - c[a]) / np.maximum(b - a, 1)
    return -0.691 + 10 * np.log10(e + 1e-12)


def power_lufs(vals):
    vals = vals[vals > -70]
    if len(vals) == 0: return -70.0
    return float(10 * np.log10(np.mean(10 ** (vals / 10))))


def gated_lufs(vals):
    """BS.1770 style: absolute -70 gate then relative -10 gate."""
    v = vals[vals > -70]
    if len(v) == 0: return -70.0
    rel = power_lufs(v) - 10
    return power_lufs(v[v > rel])


def close_open(mask, close_n, open_n):
    m = mask.copy()
    # close short gaps
    idx = np.flatnonzero(np.diff(np.r_[0, m.astype(int), 0]))
    runs = idx.reshape(-1, 2)
    for i in range(len(runs) - 1):
        if runs[i + 1, 0] - runs[i, 1] <= close_n:
            m[runs[i, 1]:runs[i + 1, 0]] = True
    idx = np.flatnonzero(np.diff(np.r_[0, m.astype(int), 0])).reshape(-1, 2)
    for a, b in idx:
        if b - a < open_n: m[a:b] = False
    return m


def runs_of(mask):
    return np.flatnonzero(np.diff(np.r_[0, mask.astype(int), 0])).reshape(-1, 2)


def speech_mask(vm):
    """vm: voice momentary loudness at HOP (use win 0.1). Threshold from the voice's own level."""
    act = vm[vm > -70]
    ref = np.percentile(act, 90)
    thr = ref - 20
    m = vm > thr
    return close_open(m, int(0.15 / HOP), int(0.15 / HOP)), thr


def mono(x):
    return x.mean(1)


def measure(name, mix_p, voice_p, bed_p, cuts_p, asr=None):
    mix, sr = sf.read(mix_p, dtype="float32", always_2d=True)
    voice, _ = sf.read(voice_p, dtype="float32", always_2d=True)
    bed, _ = sf.read(bed_p, dtype="float32", always_2d=True)
    n = min(len(mix), len(voice), len(bed)); mix, voice, bed = mix[:n], voice[:n], bed[:n]
    dur = n / sr
    cuts = np.array([float(l) for l in open(cuts_p) if l.strip()])
    meter = pyln.Meter(sr)
    R = {"name": name, "duration_s": round(dur, 1), "n_cuts": int(len(cuts)),
         "cuts_per_min": round(len(cuts) / dur * 60, 1)}
    I_mix = meter.integrated_loudness(mix); I_voice = meter.integrated_loudness(voice)
    I_bed = meter.integrated_loudness(bed)
    R["lufs_mix"] = round(I_mix, 1); R["lufs_voice"] = round(I_voice, 1); R["lufs_bed"] = round(I_bed, 1)
    R["bed_minus_voice_integrated_LU"] = round(I_bed - I_voice, 1)
    R["mix_sample_peak_dbfs"] = round(float(20 * np.log10(np.abs(mix).max() + 1e-9)), 1)
    R["voice_lra_LU"] = None
    mk = kweight(mix, sr); vk = kweight(voice, sr); bk = kweight(bed, sr)
    mm = momentary(mk, sr); bm = momentary(bk, sr); vm_fast = momentary(vk, sr, win=0.1)
    vm = momentary(vk, sr)
    bst = momentary(bk, sr, win=3.0)  # short-term bed
    mst = momentary(mk, sr, win=3.0)
    L = len(bm); t = np.arange(L) * HOP
    sp, thr = speech_mask(vm_fast[:L])
    R["speech_share"] = round(float(sp.mean()), 3)
    # bed during speech vs gaps (gaps: non-speech frames >= 0.15 s from speech, so voice tails excluded)
    dist = np.convolve(sp.astype(float), np.ones(int(0.3 / HOP)), "same") > 0
    gap = ~dist
    longgap = gap.copy()
    for a, b in runs_of(gap):
        if (b - a) * HOP < 1.0: longgap[a:b] = False
    R["gap_share"] = round(float(gap.mean()), 3)
    R["gaps_per_min"] = round(len(runs_of(gap)) / (dur / 60), 1)
    R["long_gaps(>=1s)_per_min"] = round(len(runs_of(longgap)) / (dur / 60), 2)
    R["bed_in_speech_LU_rel_voice"] = round(power_lufs(bm[sp]) - I_voice, 1)
    R["bed_in_gaps_LU_rel_voice"] = round(power_lufs(bm[gap]) - I_voice, 1)
    R["bed_in_long_gaps_LU_rel_voice"] = round(power_lufs(bm[longgap]) - I_voice, 1) if longgap.any() else None
    R["voice_in_speech_lufs"] = round(power_lufs(vm[sp]), 1)
    R["bed_in_speech_median_LU_rel_voice"] = round(float(np.median(bm[sp])) - I_voice, 1)
    R["bed_in_gaps_median_LU_rel_voice"] = round(float(np.median(bm[gap])) - I_voice, 1)
    R["mix_momentary_max_LU_rel_integrated"] = round(float(mm.max()) - I_mix, 1)
    R["mix_shortterm_p95_LU_rel_integrated"] = round(float(np.percentile(mst, 95)) - I_mix, 1)
    R["bed_shortterm_p10_p50_p90_rel_voice"] = [round(float(np.percentile(bst, q)) - I_voice, 1) for q in (10, 50, 90)]
    R["bed_LRA_LU"] = round(float(np.percentile(bst[bst > -70], 95) - np.percentile(bst[bst > -70], 10)), 1)

    # ---- spectra
    bmono = mono(bed)
    f, P = welch(bmono, sr, nperseg=8192)
    def band(lo, hi): return float(P[(f >= lo) & (f < hi)].sum())
    tot = band(20, 20000)
    R["bed_bands_pct"] = {k: round(100 * band(lo, hi) / tot, 1) for k, (lo, hi) in {
        "low_<250": (20, 250), "mid_250-4k": (250, 4000), "high_>4k": (4000, 20000)}.items()}
    R["bed_bands5_pct"] = {k: round(100 * band(lo, hi) / tot, 1) for k, (lo, hi) in {
        "sub_20-60": (20, 60), "bass_60-250": (60, 250), "lowmid_250-2k": (250, 2000),
        "highmid_2k-6k": (2000, 6000), "air_6k+": (6000, 20000)}.items()}
    # octave-band tilt (dB per octave, 63 Hz..8 kHz), K-free power
    cent = [63, 125, 250, 500, 1000, 2000, 4000, 8000]
    ob = [10 * np.log10(band(c / 2 ** .5, c * 2 ** .5) + 1e-20) for c in cent]
    R["bed_octave_db_rel_1k"] = {str(c): round(v - ob[4], 1) for c, v in zip(cent, ob)}
    vf, VP = welch(mono(voice), sr, nperseg=8192)
    R["voice_centroid_hz"] = round(float((vf * VP).sum() / VP.sum()))

    # ---- librosa features on 22.05k mono bed
    y = librosa.resample(bmono, orig_sr=sr, target_sr=22050); s2 = 22050
    hop = 512
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
    H, Pc = librosa.decompose.hpss(S, margin=2.0)
    th = np.arange(H.shape[1]) * hop / s2
    hdb = 10 * np.log10((H ** 2).sum(0) + 1e-12); pdb = 10 * np.log10((Pc ** 2).sum(0) + 1e-12)
    # map to HOP grid
    def to_grid(v, tv): return np.interp(t, tv, v)
    hg = to_grid(hdb, th)
    # harmonic level relative to the bed's own loudest harmonic content -> calibrate using bed momentary
    # music present: harmonic energy dominates and bed is above (voice - 35 LU)
    ratio = to_grid(hdb - pdb, th)
    # smooth 1 s
    k = np.ones(int(1 / HOP)) / int(1 / HOP)
    ratio_s = np.convolve(ratio, k, "same"); bm_s = np.convolve(bm, k, "same")
    R["music_present_share"] = {}
    for rel in (-20, -25, -30):
        pres = (bm_s > I_voice + rel) & (ratio_s > 0)
        R["music_present_share"][f"bed>voice{rel}LU_and_tonal"] = round(float(pres.mean()), 3)
    R["bed_any_above_voice-40LU_share"] = round(float((bm_s > I_voice - 40).mean()), 3)
    flat = librosa.feature.spectral_flatness(S=S)[0]
    cen = librosa.feature.spectral_centroid(S=S, sr=s2)[0]
    R["bed_flatness_median"] = round(float(np.median(flat)), 4)
    R["bed_centroid_median_hz"] = round(float(np.median(cen)))

    # onsets / transients on percussive part
    Pmel = librosa.feature.melspectrogram(S=Pc ** 2, sr=s2)
    oenv = librosa.onset.onset_strength(S=librosa.power_to_db(Pmel), sr=s2, hop_length=hop)
    ons = librosa.onset.onset_detect(onset_envelope=oenv, sr=s2, hop_length=hop, units="time",
                                     delta=0.25, wait=4)
    # per-onset level: bed peak 50 ms momentary in [t, t+0.2] vs median in [t-2, t-0.1]
    bfast = momentary(bk, sr, win=0.05)[:L]
    lowk = momentary(kweight(bed, sr), sr, win=0.05)[:L]
    ev = []
    for o in ons:
        i = int(o / HOP)
        a = max(0, i - int(2 / HOP)); b = max(a + 1, i - 5)
        pk = float(bfast[i:i + 10].max()) if i < L else -70
        base = float(np.median(bfast[a:b]))
        ev.append((o, pk, pk - base))
    ev = np.array(ev) if ev else np.zeros((0, 3))
    # hit = loud & big jump; foley = clear but small
    hits = ev[(ev[:, 2] >= 10) & (ev[:, 1] >= I_voice - 6)] if len(ev) else ev
    small = ev[(ev[:, 2] >= 4) & ~((ev[:, 2] >= 10) & (ev[:, 1] >= I_voice - 6))] if len(ev) else ev
    mins = dur / 60
    R["onsets_all_per_min"] = round(len(ev) / mins, 1)
    R["transients_contrast>=4dB_per_min"] = round(float((ev[:, 2] >= 4).sum()) / mins, 1)
    R["hits_per_min"] = round(len(hits) / mins, 2)
    R["small_foley_per_min"] = round(len(small) / mins, 1)
    R["hit_peak_LU_rel_voice_p50_max"] = ([round(float(np.median(hits[:, 1])) - I_voice, 1),
                                           round(float(hits[:, 1].max()) - I_voice, 1)] if len(hits) else None)
    R["hit_contrast_db_p50"] = round(float(np.median(hits[:, 2])), 1) if len(hits) else None
    R["mix_momentary_at_hits_LU_rel_integrated_p50"] = (round(float(np.median([mm[min(L - 1, int(h / HOP) + 5)] for h in hits[:, 0]])) - I_mix, 1)
                                                         if len(hits) else None)
    # hits in speech vs gaps
    if len(hits):
        hi = np.minimum((hits[:, 0] / HOP).astype(int), L - 1)
        R["hits_share_during_speech"] = round(float(sp[hi].mean()), 2)

    # ---- cut alignment
    def aligned(times, evt, lo=-0.25, hi=0.15):
        if len(evt) == 0 or len(times) == 0: return 0.0
        return float(np.mean([np.any((evt - c >= lo) & (evt - c <= hi)) for c in times]))
    tr = ev[ev[:, 2] >= 6, 0] if len(ev) else np.array([])
    rng = np.random.default_rng(0)
    base = np.mean([aligned(rng.uniform(1, dur - 1, len(cuts)), tr) for _ in range(20)])
    R["cuts_with_transient(>=6dB)_within_-0.25..+0.15s"] = round(aligned(cuts, tr), 2)
    R["chance_rate_same_window"] = round(float(base), 2)
    R["cuts_with_hit_within_window"] = round(aligned(cuts, hits[:, 0] if len(hits) else np.array([])), 2)
    R["hits_on_a_cut_share(+-0.3s)"] = (round(float(np.mean([np.any(np.abs(cuts - h) <= 0.3) for h in hits[:, 0]])), 2)
                                       if len(hits) and len(cuts) else None)
    # whoosh/swell into cut: bed level slope in 0.8 s before cut, and level jump across cut
    pre, jump = [], []
    for c in cuts:
        i = int(c / HOP)
        if i - 40 < 0 or i + 25 >= L: continue
        pre.append(bm[i - 2] - bm[i - 40]); jump.append(np.mean(bm[i:i + 25]) - np.mean(bm[i - 25:i]))
    pre, jump = np.array(pre), np.array(jump)
    if len(pre):
        R["cuts_with_rise>=6dB_in_0.8s_before(whoosh/riser)"] = round(float((pre >= 6).mean()), 2)
        R["cut_bed_jump_db_p50"] = round(float(np.median(jump)), 1)
        R["cuts_with_bed_jump>=6dB"] = round(float((np.abs(jump) >= 6).mean()), 2)

    # ---- silences: bed drop >= 10 dB below preceding 3 s median, >= 0.5 s
    ref = np.array([np.median(bst[max(0, i - int(3 / HOP)):max(1, i - int(0.2 / HOP))]) for i in range(L)])
    drop = bm < ref - 10
    drop = close_open(drop, int(0.1 / HOP), int(0.5 / HOP))
    sil = []
    ev_t = ev[:, 0] if len(ev) else np.array([])
    for a, b in runs_of(drop):
        ta, tb = a * HOP, b * HOP
        nxt = ev[(ev_t >= tb - 0.2) & (ev_t <= tb + 1.5)] if len(ev) else ev
        big = nxt[nxt[:, 2] >= 10] if len(nxt) else nxt
        after = float(np.mean(bm[b:b + int(1 / HOP)])) if b < L else -70
        sil.append({"t": round(ta, 2), "len": round(tb - ta, 2),
                    "depth_db": round(float(ref[a] - np.median(bm[a:b])), 1),
                    "voice_during": bool(sp[a:b].mean() > 0.3),
                    "hit_after": bool(len(big)), "bed_after_LU_rel_before": round(after - float(ref[a]), 1),
                    "cut_within_0.5s_of_end": bool(np.any(np.abs(cuts - tb) <= 0.5)) if len(cuts) else False,
                    "speech_starts_within_1s_after": bool(sp[b:b + int(1 / HOP)].any() and not sp[max(0, b - 5):b].any())})
    R["silences_n"] = len(sil); R["silences_per_min"] = round(len(sil) / mins, 2)
    if sil:
        ls = np.array([s["len"] for s in sil])
        R["silence_len_p50_max"] = [round(float(np.median(ls)), 2), round(float(ls.max()), 2)]
        R["silence_depth_db_p50"] = round(float(np.median([s["depth_db"] for s in sil])), 1)
        R["silences_followed_by_hit_share"] = round(float(np.mean([s["hit_after"] for s in sil])), 2)
        R["silences_with_voice_during_share"] = round(float(np.mean([s["voice_during"] for s in sil])), 2)
        R["silences_ending_at_cut_share"] = round(float(np.mean([s["cut_within_0.5s_of_end"] for s in sil])), 2)
    R["silences"] = sil
    # full-mix dead air (mix < -50 LUFS momentary for >= 0.3 s)
    dead = close_open(mm < -50, 0, int(0.3 / HOP))
    R["mix_dead_air_n"] = int(len(runs_of(dead)))

    # ---- arc: bed short-term every 10 s, rel voice
    R["arc_bed_ST_rel_voice_10s"] = [round(float(np.max(bst[int(s / HOP):int((s + 10) / HOP)])) - I_voice, 1)
                                     for s in np.arange(0, dur - 1, 10)]
    R["arc_bed_ST_mean_rel_voice_10s"] = [round(power_lufs(bst[int(s / HOP):int((s + 10) / HOP)]) - I_voice, 1)
                                          for s in np.arange(0, dur - 1, 10)]
    # rises: >= 8 LU increase of ST loudness within <= 20 s, ending at a local max
    st1 = bst[::int(0.5 / HOP)]
    rises = []
    j = 0
    while j < len(st1):
        win = st1[j:j + 40]
        if len(win) < 4: break
        lo_i = j + int(np.argmin(win[:20])); seg = st1[lo_i:lo_i + 40]
        hi_i = lo_i + int(np.argmax(seg))
        if st1[hi_i] - st1[lo_i] >= 8 and st1[lo_i] > -70:
            rises.append({"from": round(lo_i * 0.5, 1), "to": round(hi_i * 0.5, 1),
                          "gain_LU": round(float(st1[hi_i] - st1[lo_i]), 1)})
            j = hi_i + 1
        else:
            j += 20
    R["rises_>=8LU"] = rises; R["rises_per_min"] = round(len(rises) / mins, 2)
    R["rise_len_p50_s"] = round(float(np.median([r["to"] - r["from"] for r in rises])), 1) if rises else None

    # ---- tempo / pulse
    oenv_all = librosa.onset.onset_strength(y=y, sr=s2, hop_length=hop)
    tempo = librosa.feature.tempo(onset_envelope=oenv_all, sr=s2, hop_length=hop, aggregate=None)
    seg = int(30 * s2 / hop)
    tseg = []
    for a in range(0, len(oenv_all) - seg, seg):
        tg = librosa.feature.tempo(onset_envelope=oenv_all[a:a + seg], sr=s2, hop_length=hop)[0]
        ac = librosa.autocorrelate(oenv_all[a:a + seg] - oenv_all[a:a + seg].mean())
        lag = int(round(60 / tg * s2 / hop))
        clar = float(ac[lag] / (ac[0] + 1e-9)) if lag < len(ac) else 0
        tseg.append((round(float(tg)), round(clar, 2)))
    R["tempo_global_bpm"] = round(float(np.median(tempo)))
    R["tempo_per_30s_(bpm,pulse_clarity)"] = tseg
    R["pulse_clarity_median"] = round(float(np.median([c for _, c in tseg])), 2) if tseg else None

    # ---- tonality
    yh = librosa.istft(H * np.exp(1j * np.angle(librosa.stft(y, n_fft=2048, hop_length=hop))), hop_length=hop, length=len(y))
    ch = librosa.feature.chroma_cqt(y=yh, sr=s2, hop_length=2048)
    cm = ch.mean(1)
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    maj = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    mnr = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
    best = max(((np.corrcoef(np.roll(p, k), cm)[0, 1], names[k] + q) for p, q in ((maj, " maj"), (mnr, " min")) for k in range(12)))
    R["key_guess"] = best[1]; R["key_corr"] = round(float(best[0]), 2)
    R["chroma_top3"] = [names[i] for i in np.argsort(cm)[::-1][:3]]
    R["chroma_profile"] = {names[i]: round(float(cm[i] / cm.max()), 2) for i in range(12)}
    # per-minute tonal centre
    fpm = int(60 * s2 / 2048)
    R["tonal_centre_per_min"] = [names[int(np.argmax(ch[:, a:a + fpm].mean(1)))] for a in range(0, ch.shape[1], fpm)]
    # drone vs melodic: chroma argmax changes per minute (smoothed 0.5 s) and frame-to-frame chroma flux
    chs = librosa.decompose.nn_filter(ch, aggregate=np.median, metric="cosine") if ch.shape[1] > 20 else ch
    am = np.argmax(chs, 0)
    changes = int(np.sum(am[1:] != am[:-1]))
    R["chroma_pitch_changes_per_min"] = round(changes / mins, 1)
    R["chroma_dominant_pc_share"] = round(float(np.max(np.bincount(am, minlength=12)) / len(am)), 2)
    # sustained-ness: harmonic share of bed energy
    R["harmonic_energy_share"] = round(float((H ** 2).sum() / ((H ** 2).sum() + (Pc ** 2).sum())), 2)
    # instrumentation hints: sub drone share of time (energy <60 Hz within 15 dB of bed's band max)
    fr = librosa.fft_frequencies(sr=s2, n_fft=2048)
    sub = 10 * np.log10((S[(fr >= 25) & (fr < 60)] ** 2).sum(0) + 1e-12)
    mid = 10 * np.log10((S[(fr >= 250) & (fr < 2000)] ** 2).sum(0) + 1e-12)
    hi_ = 10 * np.log10((H[(fr >= 2000) & (fr < 8000)] ** 2).sum(0) + 1e-12)
    R["sub_within_10dB_of_mids_share"] = round(float(np.mean(sub > mid - 10)), 2)
    R["high_harmonic_(strings/tone)_within_15dB_of_mids_share"] = round(float(np.mean(hi_ > mid - 15)), 2)

    # ---- space: decay after isolated hits and phrase ends, stereo
    def t60(env_db, i0):
        seg = env_db[i0:i0 + int(1.5 / HOP)]
        if len(seg) < 10: return None
        pk = seg[:5].max()
        a = np.argmax(seg < pk - 5); b = np.argmax(seg < pk - 20)
        if a == 0 or b <= a: return None
        sl = (seg[b] - seg[a]) / ((b - a) * HOP)
        return float(-60 / sl) if sl < 0 else None
    dec = []
    for h in (hits[:, 0] if len(hits) else []):
        if np.any((ev_t > h + 0.05) & (ev_t < h + 1.5)): continue
        v = t60(bfast, int(h / HOP)); dec.append(v) if v else None
    R["hit_decay_T60_est_s_p50"] = round(float(np.median(dec)), 2) if dec else None
    vdec = []
    for a, b in runs_of(sp):
        if b + 75 < L and (b - a) * HOP > 0.6:
            sgm = vm_fast[b - 10:b + 75]
            pk = sgm[:10].max(); i5 = np.argmax(sgm < pk - 5); i25 = np.argmax(sgm < pk - 25)
            if i5 and i25 > i5: vdec.append(-60 / ((sgm[i25] - sgm[i5]) / ((i25 - i5) * HOP)))
    R["voice_tail_T60_est_s_p50"] = round(float(np.median(vdec)), 2) if vdec else None
    def width(x):
        m_ = (x[:, 0] + x[:, 1]) / 2; s_ = (x[:, 0] - x[:, 1]) / 2
        return round(float(10 * np.log10((s_ ** 2).mean() / ((m_ ** 2).mean() + 1e-12) + 1e-12)), 1), \
               round(float(np.corrcoef(x[:, 0], x[:, 1])[0, 1]), 2)
    R["bed_side_minus_mid_db, LR_corr"] = width(bed[::4])
    R["voice_side_minus_mid_db, LR_corr"] = width(voice[::4])
    # keep raw event list for excerpts (not printed)
    R["_hits"] = [[round(float(a), 2), round(float(b), 1), round(float(c), 1)] for a, b, c in hits]
    R["_I_voice"] = I_voice
    if asr:
        R["_asr"] = asr
    return R


if __name__ == "__main__":
    a = sys.argv[1:]
    R = measure(*a[:5], asr=json.load(open(a[6])) if len(a) > 6 else None)
    json.dump(R, open(a[5], "w"), indent=1)
    keys = [k for k in R if not k.startswith("_") and k not in ("silences", "rises_>=8LU", "arc_bed_ST_rel_voice_10s",
            "arc_bed_ST_mean_rel_voice_10s", "tempo_per_30s_(bpm,pulse_clarity)", "chroma_profile", "tonal_centre_per_min")]
    for k in keys: print(k, R[k])
