"""sfx_doctor_check.py: render every DOCTOR_NAMES sound once (beds 8 s), measure it and draw one spectrogram sheet:
W/mix/sfx_doctor/<name>.wav, check.json, sheet.jpg.   python3 sfx_doctor_check.py [names...]"""
import json, os, sys, traceback
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sfx as S
OUT = os.path.join(S.W, 'mix', 'sfx_doctor')
EXTRA = {'landline_ring': dict(n=2), 'pulse_count': dict(dur=12.0), 'hold_music': dict(dur=8.0),
         'tape_peel': dict(q=3), 'receiver_down': dict(kind='hang'), 'wall_clock': dict(dur=8.0, bpm_end=30, sag=3)}


def main():
    os.makedirs(OUT, exist_ok=True)
    names = [a for a in sys.argv[1:]] or list(S.DOCTOR_NAMES) + ['pen_click']
    res = {}
    for nm in names:
        kw = dict(EXTRA.get(nm, {}))
        if (nm in S.BEDS or nm in S.DUR_BEDS) and 'dur' not in kw:
            kw['dur'] = 8.0
        try:
            y, pre = S.render_event(nm, 1, **kw)
            sf.write(os.path.join(OUT, nm + '.wav'), y, S.SR, subtype='PCM_24')
            P = np.abs(np.fft.rfft(S.mono(y))) ** 2; f = np.fft.rfftfreq(len(y), 1 / S.SR); tot = P.sum() + 1e-20
            res[nm] = {'dur': round(len(y) / S.SR, 2), 'pre': round(pre, 3), 'Mmax': round(S.mom_max(y), 1),
                       'lufs': round(S.lufs_int(y), 1), 'peak': round(float(S.db(S.peak(y))), 1),
                       'lo_mid_hi': [round(100 * float(P[f < 250].sum() / tot)), round(100 * float(P[(f >= 250) & (f < 4000)].sum() / tot)),
                                     round(100 * float(P[f >= 4000].sum() / tot))]}
        except Exception as e:
            res[nm] = {'error': repr(e)[:200]}; traceback.print_exc(limit=2)
        print(nm, res[nm], flush=True)
    pj = os.path.join(OUT, 'check.json')
    old = json.load(open(pj)) if os.path.exists(pj) else {}
    old.update(res); json.dump(old, open(pj, 'w'), indent=1)
    sheet(sorted(old))


def sheet(names):
    from PIL import Image, ImageDraw
    from scipy import signal
    cols, tw, th = 5, 256, 96
    names = [n for n in names if os.path.exists(os.path.join(OUT, n + '.wav'))]
    im = Image.new('RGB', (cols * tw, ((len(names) + cols - 1) // cols) * th), (14, 14, 16)); dr = ImageDraw.Draw(im)
    for k, nm in enumerate(names):
        x = sf.read(os.path.join(OUT, nm + '.wav'), dtype='float32', always_2d=True)[0].mean(1)
        fr, t, Sg = signal.spectrogram(x, S.SR, nperseg=1024, noverlap=512)
        Sg = 10 * np.log10(Sg + 1e-14); vm = np.percentile(Sg, 99.5)
        rows = np.unique(np.geomspace(1, len(fr) - 1, 70).astype(int))
        a = np.clip((Sg[rows] - vm + 70) / 70, 0, 1)[::-1]
        r, c = divmod(k, cols)
        im.paste(Image.fromarray((a * 255).astype(np.uint8)).resize((tw - 4, th - 18)).convert('RGB'), (c * tw + 2, r * th + 16))
        dr.text((c * tw + 3, r * th + 2), f'{nm} {len(x) / S.SR:.1f}s', fill=(230, 220, 120))
    im.save(os.path.join(OUT, 'sheet.jpg'), quality=86)


if __name__ == '__main__':
    main()
