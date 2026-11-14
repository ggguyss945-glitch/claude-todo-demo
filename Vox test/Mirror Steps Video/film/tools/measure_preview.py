"""Measure a low-res preview against DIRECTION_V2 2.1 / 5.1 with the analysis/refmirror scripts (the critique's method).

    python3 tools/measure_preview.py [_work/preview_v2/preview.mp4] [--keep]

Decodes the video with analysis/refmirror/extract.sh into <dir>/data/<name>/ (1 fps 854x480 jpgs, 6 fps 320x180 rgb,
30 fps 160x90 gray), then runs cuts30.py, still_share.py, punchins.py, measure_motion.py + motion_summary.py and
cut_vs_text.py (clause starts from _work/align/timeline.json's words), computes the look statistics of
tools/sets_v2_stills.look() on the 1 fps frames (640x360, caption band dropped) per tenth and for the whole film, prints
one table against the brief's targets and writes <dir>/measure_<name>.json. The decoded frames are deleted afterwards
unless --keep.
"""
import os, sys, json, subprocess, shutil, glob
HERE = os.path.dirname(os.path.abspath(__file__)); FILM = os.path.dirname(HERE)
REF = os.path.join(FILM, 'analysis', 'refmirror')
import numpy as np
import cv2


def look(bgr):
    im = cv2.resize(bgr, (640, 360), interpolation=cv2.INTER_AREA)[:310]
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    b, gg, r = [im[..., k].astype(np.float32) for k in range(3)]
    rg = r - gg; yb = 0.5 * (r + gg) - b
    colorful = float(np.hypot(rg.std(), yb.std()) + 0.3 * np.hypot(rg.mean(), yb.mean()))
    e = cv2.Canny(im, 60, 160)
    red = float(((r > 110) & (r > gg + 50) & (r > b + 40)).mean())
    sat = hsv[..., 1]
    return dict(luma=float(g.mean()), p5=float(np.percentile(g, 5)), p50=float(np.median(g)), p95=float(np.percentile(g, 95)),
                std=float(g.std()), sat=float(sat.mean()), colorful=colorful, edges=float((e > 0).mean()), red=red)


def run(cmd, **kw):
    print('$', ' '.join(cmd), flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0: print(r.stdout[-2000:], r.stderr[-2000:])
    return r.stdout


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    keep = '--keep' in sys.argv
    video = os.path.abspath(args[0] if args else os.path.join(FILM, '_work', 'preview_v2', 'preview.mp4'))
    d, name = os.path.dirname(video), os.path.splitext(os.path.basename(video))[0]
    data = os.path.join(d, 'data')
    if not os.path.exists(os.path.join(data, name, 'gray30.raw')):
        run(['sh', os.path.join(REF, 'extract.sh'), d, name])
    py = [sys.executable, '-I']
    run(py + [os.path.join(REF, 'cuts30.py'), data, name])
    out_still = run(py + [os.path.join(REF, 'still_share.py'), data, name])
    run(py + [os.path.join(REF, 'punchins.py'), data, name])
    run([sys.executable, os.path.join(FILM, 'analysis', 'measure_motion.py'), data, name, os.path.join(data, 'motion_%s.json' % name)])
    run(py + [os.path.join(REF, 'motion_summary.py'), data, name])
    # clause starts from the narration timeline (the ASR the script expects)
    tl = json.load(open(os.path.join(FILM, '_work', 'align', 'timeline.json')))
    asr = []
    for ln in tl.get('lines', []):
        ws = ln.get('words') or []
        W = []
        for w in ws:
            if isinstance(w, dict): W.append([float(w.get('t0', w.get('start', 0.0))), str(w.get('w', w.get('word', w.get('text', ''))))])
            elif isinstance(w[0], (int, float)): W.append([float(w[0]), str(w[-1])])
            elif w[1] is not None: W.append([float(w[1]), str(w[0])])
        if W: asr.append({'t0': W[0][0], 't1': W[-1][0], 'text': ' '.join(x[1] for x in W), 'words': W})
    json.dump(asr, open(os.path.join(data, 'asr_%s.json' % name), 'w'))
    out_cvt = run(py + [os.path.join(REF, 'cut_vs_text.py'), data, name])
    C = json.load(open(os.path.join(data, 'cuts30_%s.json' % name)))
    M = json.load(open(os.path.join(data, 'motion_summary_%s.json' % name)))
    P = json.load(open(os.path.join(data, 'punch_%s.json' % name))) if os.path.exists(os.path.join(data, 'punch_%s.json' % name)) else []
    dur = C['duration']
    cuts = np.array([c['t'] for c in C['cuts']])
    flashes = C.get('flashes', [])
    sl = np.diff(np.r_[0, cuts, dur])
    # looks from the 1 fps frames
    fr = sorted(glob.glob(os.path.join(data, name, 'f1', 'f*.jpg')))
    L = []
    for f in fr:
        k = int(os.path.basename(f)[1:5])
        m = look(cv2.imread(f)); m['t'] = k; L.append(m)
    lum = np.array([m['luma'] for m in L])
    tenths = []
    for k in range(10):
        S = [m for m in L if k * 70 <= m['t'] < (k + 1) * 70]
        if not S: continue
        tenths.append(dict(t='%d-%d' % (k * 70, k * 70 + 70), p50=round(float(np.median([m['p50'] for m in S])), 1),
                           mean=round(float(np.mean([m['luma'] for m in S])), 1), red=round(100 * float(np.mean([m['red'] for m in S])), 2),
                           sat=round(float(np.mean([m['sat'] for m in S])), 1)))
    # still share / frame energy from still_share.py's printout
    R = dict(
        cuts=int(len(cuts)), cuts_per_min=round(len(cuts) / dur * 60, 1), cuts_first_30s=int((cuts < 30).sum()),
        shot_p10_p50_p90=np.round(np.percentile(sl, [10, 50, 90]), 2).tolist(), shots_over_3s_pct=round(100 * float((sl > 3.0).mean()), 1),
        flashes=len(flashes), flashes_per_min=round(len(flashes) / dur * 60, 2),
        punch_ins=sum(1 for p in P if p.get('kind') == 'punch-in'),
        luma_lt60_pct=round(100 * float((lum < 60).mean()), 1), luma_lt40_pct=round(100 * float((lum < 40).mean()), 1),
        colourfulness_p50=round(float(np.median([m['colorful'] for m in L])), 1),
        contrast_p95_p5_p50=round(float(np.median([m['p95'] - m['p5'] for m in L])), 1),
        luma_std_p50=round(float(np.median([m['std'] for m in L])), 1), edges_p50=round(float(np.median([m['edges'] for m in L])), 4),
        sat_mean=round(float(np.mean([m['sat'] for m in L])), 1), tenths=tenths,
        subject_moving_share=M.get('subject_moving_share(>30px/s)'), push_p25_50_75_90=M.get('push_in_pct_per_s_p25_50_75_90'),
        cam_moving_share=M.get('cam_moving_share'), shot_move_mix=M.get('shot_move_mix'), still_share=out_still.strip(),
        cut_vs_text=out_cvt.strip())
    json.dump(R, open(os.path.join(d, 'measure_%s.json' % name), 'w'), indent=1)
    for k, v in R.items():
        if k != 'tenths': print('%-26s %s' % (k, v))
    print('tenth      luma p50  mean   red%   sat')
    for t in tenths: print('%-9s %8.0f %6.0f %6.2f %5.0f' % (t['t'], t['p50'], t['mean'], t['red'], t['sat']))
    if not keep:
        shutil.rmtree(os.path.join(data, name), ignore_errors=True)
        print('deleted', os.path.join(data, name))


if __name__ == '__main__':
    main()
