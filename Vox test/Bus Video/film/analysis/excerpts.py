"""Cut typical bed excerpts from separated references and measure each for numeric comparison.

Usage: python3 excerpts.py <sep_dir> <metrics_dir> <out_dir>
Reads <metrics_dir>/metrics_<v>.json (from measure.py, with _asr) and <sep_dir>/<v>_bed.wav.
Writes <out_dir>/<v>_<kind>_<t>.wav (48 kHz stereo 24-bit, <= 20 s) and <out_dir>/excerpts.json:
  [{file, video, kind, t, len, lufs, LU_rel_voice, peak_dbfs, bands_pct{low,mid,high}, onsets_per_min}]
Kinds: tension_build, scare_hit, quiet_dread, rule_card.
compare(wav_path, ref_entry) -> dict of differences, for the mix/score agents to check their own beds.
"""
import json, os, sys
import numpy as np, soundfile as sf, pyloudnorm as pyln, librosa
from scipy.signal import welch, resample_poly


def stats(x, sr, I_voice=None):
    m = pyln.Meter(sr)
    L = m.integrated_loudness(x) if len(x) > sr * 0.5 else -70
    f, P = welch(x.mean(1), sr, nperseg=4096)
    tot = P[(f >= 20)].sum() + 1e-20
    b = {"low": round(100 * P[(f >= 20) & (f < 250)].sum() / tot, 1),
         "mid": round(100 * P[(f >= 250) & (f < 4000)].sum() / tot, 1),
         "high": round(100 * P[f >= 4000].sum() / tot, 1)}
    y = librosa.resample(x.mean(1), orig_sr=sr, target_sr=22050)
    on = librosa.onset.onset_detect(y=y, sr=22050, units="time", delta=0.25, wait=4)
    r = {"lufs": round(L, 1), "peak_dbfs": round(float(20 * np.log10(np.abs(x).max() + 1e-9)), 1),
         "bands_pct": b, "onsets_per_min": round(len(on) / (len(x) / sr) * 60, 1)}
    if I_voice is not None: r["LU_rel_voice"] = round(L - I_voice, 1)
    return r


def compare(path, ref):
    x, sr = sf.read(path, dtype="float32", always_2d=True)
    s = stats(x, sr)
    return {"d_lufs": round(s["lufs"] - ref["lufs"], 1),
            "d_bands": {k: round(s["bands_pct"][k] - ref["bands_pct"][k], 1) for k in s["bands_pct"]},
            "d_onsets_per_min": round(s["onsets_per_min"] - ref["onsets_per_min"], 1)}


def pick(R):
    out = []
    dur = R["duration_s"]
    if R["rises_>=8LU"]:
        r = max(R["rises_>=8LU"], key=lambda r: r["gain_LU"] + 0.2 * min(r["to"] - r["from"], 20))
        a = max(0, r["to"] - 18); out.append(("tension_build", a, min(20, r["to"] + 2 - a)))
    if R["_hits"]:
        h = max(R["_hits"], key=lambda h: h[1] + 0.5 * h[2])
        out.append(("scare_hit", max(0, h[0] - 10), 14))
    arc = np.array(R["arc_bed_ST_mean_rel_voice_10s"])
    # quiet dread: quietest 10 s block that is still audible (> -40 LU rel voice), skipping the first 20 s
    cand = [(v, i) for i, v in enumerate(arc) if v > -40 and i >= 2]
    if cand:
        v, i = min(cand); out.append(("quiet_dread", i * 10.0, 15))
    for s in R.get("_asr", []):
        tx = s["text"].lower()
        i = tx.find("rule number")
        if i >= 0:
            # place the excerpt around the announcement, interpolating its position in the segment
            tr = s["t"] + (s.get("end", s["t"]) - s["t"]) * i / max(1, len(tx))
            if tr > 25:
                out.append(("rule_card", max(0, tr - 4), 12)); break
    return [(k, round(a, 1), round(min(l, dur - a), 1)) for k, a, l in out]


def main(sep, mdir, out):
    os.makedirs(out, exist_ok=True)
    res = []
    for v in ("fire", "hotel", "class"):
        p = f"{mdir}/metrics_{v}.json"
        if not os.path.exists(p): continue
        R = json.load(open(p))
        bed, sr = sf.read(f"{sep}/{v}_bed.wav", dtype="float32", always_2d=True)
        for kind, a, l in pick(R):
            seg = bed[int(a * sr):int((a + l) * sr)]
            seg48 = resample_poly(seg, 160, 147, axis=0).astype(np.float32)
            fn = f"{v}_{kind}_{int(a)}.wav"
            sf.write(f"{out}/{fn}", seg48, 48000, subtype="PCM_24")
            e = {"file": fn, "video": v, "kind": kind, "t": a, "len": l}
            e.update(stats(seg, sr, R["_I_voice"]))
            res.append(e)
    json.dump(res, open(f"{out}/excerpts.json", "w"), indent=1, default=float)
    for e in res: print(json.dumps(e, default=float))


if __name__ == "__main__":
    main(*sys.argv[1:4])
