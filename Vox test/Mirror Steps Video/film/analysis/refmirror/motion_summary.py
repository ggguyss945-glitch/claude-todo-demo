"""Camera / subject motion and tone-arc summary from motion_<name>.json (6 fps, 320x180) and cuts30_<name>.json.

Usage: python3 -I motion_summary.py <data_dir> <name> [<name> ...]
Pixel speeds are reported at 1280 px width (x4 from 320) to compare with VISUAL_SPEC.md (police refs);
multiply by 2 for 2560 output. Writes <data_dir>/motion_summary_<name>.json.
"""
import sys, json, numpy as np

d = sys.argv[1]
for name in sys.argv[2:]:
    R = json.load(open(f"{d}/motion_{name}.json")); n = len(R)
    C = json.load(open(f"{d}/cuts30_{name}.json"))
    cuts = np.array([c["t"] for c in C["cuts"]]); dur = C["duration"]
    t = np.array([r["t"] for r in R])
    g = lambda k: np.array([r.get(k, np.nan) for r in R])
    near = np.zeros(n, bool)
    for c in cuts: near |= np.abs(t - c) < 0.35
    zoom_raw = g("zoom"); ok = ~near & ~np.isnan(zoom_raw)
    zoom = zoom_raw[ok] * 6 * 100
    tx = g("tx")[ok] * 4 * 6; ty = g("ty")[ok] * 4 * 6
    sp = np.hypot(tx, ty); res = g("resid90")[ok] * 4 * 6
    moving = (np.abs(zoom) > 0.8) | (sp > 8)
    S = {"name": name}
    S["cam_moving_share"] = round(float(moving.mean()), 2)
    S["zoom_in_share"] = round(float((zoom > 0.8).mean()), 2); S["zoom_out_share"] = round(float((zoom < -0.8).mean()), 2)
    S["pan_share"] = round(float((sp > 8).mean()), 2)
    S["push_in_pct_per_s_p25_50_75_90"] = np.round(np.percentile(zoom[zoom > 0.8], [25, 50, 75, 90]), 2).tolist()
    zo = -zoom[zoom < -0.8]
    S["pull_out_pct_per_s_p50_90"] = np.round(np.percentile(zo, [50, 90]), 2).tolist() if len(zo) else None
    S["pan_px_s_1280_p25_50_75_90"] = np.round(np.percentile(sp[sp > 8], [25, 50, 75, 90]), 1).tolist()
    txr = g("tx") * 24; hp = txr - np.convolve(np.nan_to_num(txr), np.ones(7) / 7, "same")
    S["shake_hp_tx_std_px_s_1280"] = round(float(np.nanstd(hp[ok])), 2)
    S["subject_resid90_px_s_1280_p50_75_90"] = np.round(np.percentile(res, [50, 75, 90]), 1).tolist()
    S["subject_moving_share(>30px/s)"] = round(float((res > 30).mean()), 2)
    # shot lengths
    sl = np.diff(np.r_[0, cuts, dur])
    S["n_cuts"] = int(len(cuts)); S["cuts_per_min"] = round(len(cuts) / dur * 60, 1)
    S["shot_len_p10_25_50_75_90"] = np.round(np.percentile(sl, [10, 25, 50, 75, 90]), 2).tolist()
    S["shot_len_mean_max"] = [round(float(sl.mean()), 2), round(float(sl.max()), 1)]
    S["shot_len_hist_(<1,1-2,2-3,3-4,4-6,>6)"] = [int(((sl >= a) & (sl < b)).sum()) for a, b in
                                                  [(0, 1), (1, 2), (2, 3), (3, 4), (4, 6), (6, 99)]]
    kinds = [c["kind"] for c in C["cuts"]]
    S["transition_mix"] = {k: round(kinds.count(k) / len(kinds), 3) for k in ("hard", "soft")}
    # per-shot camera move class
    z = np.nan_to_num(zoom_raw); txa = np.nan_to_num(g("tx")) * 4; tya = np.nan_to_num(g("ty")) * 4
    edges = np.r_[0, (cuts * 6).astype(int), n]
    tot, kinds2, prof = [], {"push": 0, "pull": 0, "pan": 0, "static": 0, "push+pan": 0}, []
    for a, b in zip(edges[:-1], edges[1:]):
        a2, b2 = a + 2, b - 1
        if b2 - a2 < 6: continue
        zz = np.clip(z[a2:b2], -0.05, 0.05); Z = np.exp(np.sum(np.log1p(zz))) - 1
        P = np.hypot(txa[a2:b2].sum(), tya[a2:b2].sum()); du = (b2 - a2) / 6
        push = abs(Z) * 100 / du > 0.8; pan = P / du > 8
        k = "push+pan" if (push and pan) else "push" if (push and Z > 0) else "pull" if push else "pan" if pan else "static"
        kinds2[k] += 1; tot.append(Z * 100)
        if Z > 0.04 and b2 - a2 >= 15:
            c = np.cumsum(zz); c /= c[-1] if c[-1] != 0 else 1
            prof.append(np.interp(np.linspace(0, 1, 6), np.linspace(0, 1, len(c)), c))
    N = len(tot)
    S["shots>=1.5s"] = N
    S["shot_move_mix"] = {k: round(v / N, 2) for k, v in kinds2.items()}
    S["total_zoom_per_shot_pct_p25_50_75_90_max"] = np.round(np.percentile(tot, [25, 50, 75, 90, 100]), 1).tolist()
    S["push_profile_0_.2_.4_.6_.8_1"] = np.round(np.mean(prof, 0), 2).tolist() if prof else None
    # tone arc in tenths
    bins = np.linspace(0, dur, 11); L, Sa, Rd, Bl = g("luma"), g("sat"), g("red"), g("blue")
    arc = []
    for a, b in zip(bins[:-1], bins[1:]):
        m = (t >= a) & (t < b); mm = m & ~np.isnan(zoom_raw) & ~near
        arc.append({"luma": round(float(L[m].mean())), "sat": round(float(Sa[m].mean())),
                    "red%": round(100 * float(Rd[m].mean()), 1), "blue%": round(100 * float(Bl[m].mean()), 1),
                    "cuts/min": round(float(((cuts >= a) & (cuts < b)).sum()) / ((b - a) / 60), 1),
                    "|zoom|%/s": round(float(np.mean(np.abs(zoom_raw[mm]) * 600)), 2),
                    "subj_p90": round(float(np.nanmean(g("resid90")[mm] * 24)), 1)})
    S["arc_tenths"] = arc
    json.dump(S, open(f"{d}/motion_summary_{name}.json", "w"), indent=1)
    for k, v in S.items():
        if k != "arc_tenths": print(k, v)
    for i, a in enumerate(arc): print("  tenth", i + 1, a)
