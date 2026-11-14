"""shorts/finalize.py: the deliverable for one Short, from the assembler's picture and the mixer's master.

    python3 shorts/finalize.py --short 1|2|3 [--in DIR] [--final DIR]

Reads  <in>/picture.mp4 (1080x1920, 60 fps, H.264 high, CRF 16: shorts/assemble.py), <in>/mix.wav (-14 LUFS, <= -1 dBTP:
       shorts/mix_short.py), <in>/timing.json, <in>/mix_report.json. <in> defaults to $S/pov2/shorts/S<n>.
Writes <final>/Short<n>_<Title>.mp4   picture (stream copy) + AAC-LC 320 kb/s 48 kHz stereo, +faststart
       <final>/Short<n>_<Title>_cover.png      1080x1920 cover frame (the Short's strongest image, see COVER)
       <final>/Short<n>_<Title>_sheet.jpg      contact sheet: one frame per second, time-stamped
       <final>/Short<n>_<Title>_verify.json    measured: duration, fps, codec/profile, size, loudness (ebur128 on the
                                               delivered AAC), true peak, LRA, silences > 0.3 s at -40 dB, key times
If the AAC encode pushes the true peak over -1.0 dBTP, the master is trimmed by the overshoot and encoded again.
"""
import argparse, json, os, re, subprocess, sys
import numpy as np
import cv2

S = '/home/user/claude-todo-demo/Vox test/Police Officer Video/v2/_work'
NAMES = {1: 'Short1_The_Other_Gentleman', 2: 'Short2_Your_Voice_On_The_Radio', 3: 'Short3_Never_Correct_Him'}
COVER = {1: ('slam', "DON'T PROVE\nYOU LIVE THERE", 0.72), 2: ('slam', 'NOW YOUR\nNAME.'), 3: ('tag', 'RULE #5', 1.55)}   # event that makes the cover frame (+ seconds after it, default 0.12)


def sh(cmd, **k):
    return subprocess.run(cmd, capture_output=True, text=True, **k)


def ebur128(path):
    r = sh(['ffmpeg', '-nostats', '-hide_banner', '-i', path, '-map', '0:a', '-filter_complex', 'ebur128=peak=true', '-f', 'null', '-']).stderr
    s = r[r.rfind('Summary:'):]
    g = lambda pat: float(re.search(pat, s, re.S).group(1))
    return dict(integrated_lufs=g(r'I:\s+(-?[\d.]+) LUFS'), lra_lu=g(r'LRA:\s+(-?[\d.]+) LU'),
                true_peak_dbtp=g(r'True peak:.*?Peak:\s+(-?[\d.]+) dBFS'))


def silences(path, db=-40, d=0.3):
    r = sh(['ffmpeg', '-nostats', '-hide_banner', '-i', path, '-map', '0:a', '-af', 'silencedetect=n=%ddB:d=%.2f' % (db, d), '-f', 'null', '-']).stderr
    st = [float(x) for x in re.findall(r'silence_start: (-?[\d.]+)', r)]
    en = [float(x) for x in re.findall(r'silence_end: (-?[\d.]+)', r)]
    return [[round(a, 2), round(b, 2)] for a, b in zip(st, en)]


def probe(path):
    j = json.loads(sh(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', path]).stdout)
    v = [s for s in j['streams'] if s['codec_type'] == 'video'][0]
    a = [s for s in j['streams'] if s['codec_type'] == 'audio'][0]
    num, den = v['r_frame_rate'].split('/')
    return dict(duration=round(float(j['format']['duration']), 3), size_mb=round(int(j['format']['size']) / 1e6, 1),
                width=v['width'], height=v['height'], fps=round(float(num) / float(den), 3), vcodec=v['codec_name'],
                profile=v.get('profile'), pix_fmt=v.get('pix_fmt'), frames=int(v.get('nb_frames', 0) or 0),
                acodec=a['codec_name'], abitrate_k=round(int(a.get('bit_rate', 0) or 0) / 1000), asr=int(a['sample_rate']),
                channels=a['channels'])


def masking(ind):
    """Share of speech frames (100 ms, 300 Hz-5 kHz) where music + SFX sit within 3 dB of the voice (stems at master gain)."""
    import soundfile as sf
    from scipy import signal
    st = os.path.join(ind, 'stems')
    try:
        v, sr = sf.read(os.path.join(st, 'voice.wav'), dtype='float32')
        m, _ = sf.read(os.path.join(st, 'music.wav'), dtype='float32')
        x, _ = sf.read(os.path.join(st, 'sfx.wav'), dtype='float32')
    except Exception:
        return None
    mono = lambda y: y.mean(1) if y.ndim > 1 else y
    sos = signal.butter(4, [300, 5000], 'bandpass', fs=sr, output='sos')
    vb = signal.sosfilt(sos, mono(v)); bb = signal.sosfilt(sos, mono(m) + mono(x))
    n = int(0.1 * sr); k = min(len(vb), len(bb)) // n
    e = lambda y: 10 * np.log10(np.mean(y[:k * n].reshape(k, n) ** 2, axis=1) + 1e-12)
    ev, eb = e(vb), e(bb)
    spk = ev > ev.max() - 30
    d = (ev - eb)[spk]
    return dict(speech_frames=int(spk.sum()), within_3db_pct=round(100 * float(np.mean(d < 3)), 1), median_db=round(float(np.median(d)), 1))


def mux(pic, wav, dst, gain_db=0.0):
    af = ['-af', 'volume=%.2fdB' % gain_db] if gain_db else []
    r = sh(['ffmpeg', '-v', 'error', '-y', '-i', pic, '-i', wav, '-map', '0:v', '-map', '1:a', '-c:v', 'copy'] + af +
           ['-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-ac', '2', '-shortest', '-movflags', '+faststart', dst])
    if r.returncode: sys.exit(r.stderr)


def frame_at(cap, t, fps):
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(t * fps)))
    ok, img = cap.read()
    return img if ok else None


def sheet(path, out, dur, fps, cols=9, tw=160):
    cap = cv2.VideoCapture(path)
    th = int(round(tw * 16 / 9))
    ts = list(np.arange(0.5, dur, 1.0))
    rows = (len(ts) + cols - 1) // cols
    img = np.zeros((rows * (th + 4), cols * (tw + 4), 3), np.uint8)
    for k, t in enumerate(ts):
        f = frame_at(cap, t, fps)
        if f is None: continue
        f = cv2.resize(f, (tw, th), interpolation=cv2.INTER_AREA)
        cv2.putText(f, '%.1f' % t, (4, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)
        r, c = divmod(k, cols)
        img[r * (th + 4):r * (th + 4) + th, c * (tw + 4):c * (tw + 4) + tw] = f
    cv2.imwrite(out, img, [cv2.IMWRITE_JPEG_QUALITY, 82])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--short', type=int, required=True, choices=[1, 2, 3])
    ap.add_argument('--in', dest='ind', default=None)
    ap.add_argument('--final', default=os.path.join(S, 'pov2', 'shorts', 'final'))
    A = ap.parse_args()
    ind = A.ind or os.path.join(S, 'pov2', 'shorts', 'S%d' % A.short)
    os.makedirs(A.final, exist_ok=True)
    base = os.path.join(A.final, NAMES[A.short])
    pic, wav = os.path.join(ind, 'picture.mp4'), os.path.join(ind, 'mix.wav')
    T = json.load(open(os.path.join(ind, 'timing.json')))
    rep = json.load(open(os.path.join(ind, 'mix_report.json')))
    dst = base + '.mp4'
    mux(pic, wav, dst)
    eb = ebur128(dst)
    trim = 0.0
    if eb['true_peak_dbtp'] > -1.0:                       # AAC overshoot: trim and encode again
        trim = -(eb['true_peak_dbtp'] + 1.05)
        mux(pic, wav, dst, trim); eb = ebur128(dst)
    pr = probe(dst)
    # cover: 0.12 s after the cover event lands (the slam has settled), else the twist
    kind, txt, *off = COVER[A.short]
    ev = [e for e in T['events'] if e['type'] == kind and e.get('text') == txt]
    tc = (ev[0]['t'] + (off[0] if off else 0.12)) if ev else (rep.get('twist_t') or 1.0)
    cap = cv2.VideoCapture(pic)
    f = frame_at(cap, tc, pr['fps'])
    cv2.imwrite(base + '_cover.png', f)
    sheet(dst, base + '_sheet.jpg', pr['duration'], pr['fps'])
    dur = pr['duration']
    v = dict(file=dst, probe=pr, loudness=eb, aac_trim_db=round(trim, 2), silences_over_0_3s_at_minus40=silences(dst),
             subscribe_t=rep.get('subscribe_t'), twist_t=rep.get('twist_t'), end_card_t=rep.get('end_card_t'),
             rewind_t=rep.get('rewind_t'), tension_gap=rep.get('tension_gap'),
             pct=dict(subscribe=round(100 * (rep.get('subscribe_t') or 0) / dur, 1), twist=round(100 * (rep.get('twist_t') or 0) / dur, 1),
                      end_card=round(100 * (rep.get('end_card_t') or 0) / dur, 1)),
             new_lines=[c.get('src') for c in T['clips'] if c.get('wav')], cover_t=round(tc, 3), masking=masking(ind))
    ok = (48 <= dur <= 56 and abs(pr['fps'] - 60) < 0.01 and abs(eb['integrated_lufs'] + 14) <= 0.5 and eb['true_peak_dbtp'] <= -1.0
          and pr['size_mb'] < 200 and pr['width'] == 1080 and pr['height'] == 1920)
    v['pass'] = bool(ok)
    json.dump(v, open(base + '_verify.json', 'w'), indent=1)
    print('[finalize] %s  %.2f s  %dx%d @ %.0f fps  %s/%s  %.1f MB  I %.1f LUFS  TP %.1f dBTP  LRA %.1f  sub %.1f%%  twist %.1f%%  mask %s  %s'
          % (os.path.basename(dst), dur, pr['width'], pr['height'], pr['fps'], pr['vcodec'], pr['profile'], pr['size_mb'],
             eb['integrated_lufs'], eb['true_peak_dbtp'], eb['lra_lu'], v['pct']['subscribe'], v['pct']['twist'],
             (v['masking'] or {}).get('within_3db_pct'), 'PASS' if ok else 'CHECK'))


if __name__ == '__main__':
    main()
