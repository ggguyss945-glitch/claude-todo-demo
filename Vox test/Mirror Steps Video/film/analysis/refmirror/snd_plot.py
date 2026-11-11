"""snd_plot.py: level curves + bed spectrogram of one window, ours or a reference (sound v3 study and checks).

    python3 analysis/refmirror/snd_plot.py OUT.png T0 T1 ours[:_work/mix/final_v2] [--cues _work/cues] [--label TXT]
    python3 analysis/refmirror/snd_plot.py OUT.png T0 T1 ref:sibling_stitched [--label TXT]

Ours: voice / music / sfx stems of the mix dir (bed = music + sfx), the one-shot cues (green ticks, red = hit), the
music events (orange: silence span, riser end, hit) and the narration lines. References: the separated bed / voice of
_work/review/snd_v3/ref/sep_<name>/ and the ASR words. Curves are 400 ms K-weighted momentary loudness relative to the
voice stem's integrated loudness (0 = the narration's level); 400 ms windows, 50 ms hop.
"""
import argparse, json, os, sys
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.normpath(os.path.join(HERE, '..', '..'))
W = os.path.join(FILM, '_work')
sys.path.insert(0, os.path.join(FILM, 'audio'))
import sfx as SX  # noqa: E402


def rd(p, a, b):
    with sf.SoundFile(p) as f:
        sr = f.samplerate
        f.seek(max(0, int(a * sr)))
        y = f.read(int((b - a) * sr), dtype='float32', always_2d=True)
    if sr != 48000:
        import soxr
        y = soxr.resample(y, sr, 48000).astype(np.float32)
    return y


def lev(y):
    pad = int(0.2 * 48000)
    return -0.691 + 10 * np.log10(SX._blocks(np.pad(y, ((pad, pad), (0, 0))), 0.4, 0.05) + 1e-20)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('t0', type=float); ap.add_argument('t1', type=float); ap.add_argument('src')
    ap.add_argument('--cues', default=os.path.join(W, 'cues')); ap.add_argument('--label', default='')
    A = ap.parse_args()
    t0, t1 = A.t0, A.t1
    ours = A.src.startswith('ours')
    if ours:
        md = A.src.split(':', 1)[1] if ':' in A.src else os.path.join(W, 'mix', 'final_v2')
        if not os.path.isabs(md):
            md = os.path.join(FILM, md)
        sd = os.path.join(md, 'stems')
        v = rd(os.path.join(sd, 'voice_en.wav'), t0, t1); m = rd(os.path.join(sd, 'music.wav'), t0, t1)
        s = rd(os.path.join(sd, 'sfx.wav'), t0, t1); bed = m + s
        Iv = json.load(open(os.path.join(md, 'mix_report.json')))['langs']['en']['voice_lufs']
        tracks = [(v, (150, 200, 255), 'voice', 1), (m, (240, 150, 60), 'music', 1), (s, (100, 220, 100), 'sfx', 1),
                  (bed, (255, 255, 255), 'bed', 2)]
    else:
        nm = A.src.split(':', 1)[1]
        sd = os.path.join(W, 'review', 'snd_v3', 'ref', 'sep_' + nm)
        v = rd(os.path.join(sd, 'voice.wav'), t0, t1); bed = rd(os.path.join(sd, 'bed.wav'), t0, t1)
        Iv = float(np.load(os.path.join(W, 'review', 'snd_v3', 'env', nm + '.npz'))['I_voice'])
        tracks = [(v, (150, 200, 255), 'voice', 1), (bed, (255, 255, 255), 'bed', 2)]
    PW, LH, SH, TH = 1600, 280, 260, 70
    img = Image.new('RGB', (PW + 60, LH + SH + TH + 50), (20, 20, 24)); d = ImageDraw.Draw(img)
    F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)
    X = lambda t: 50 + (t - t0) / (t1 - t0) * PW
    Y = lambda db: 20 + (10 - max(-45, min(10, db))) / 55 * LH
    for db in (10, 0, -10, -20, -30, -40):
        d.line([(50, Y(db)), (50 + PW, Y(db))], fill=(60, 60, 60)); d.text((5, Y(db) - 7), f'{db}', font=F, fill=(150, 150, 150))
    step = 1 if t1 - t0 <= 40 else 5 if t1 - t0 <= 200 else 10
    for t in range(int(t0), int(t1) + 1):
        if t % step == 0:
            d.line([(X(t), 20), (X(t), LH + SH + 30)], fill=(45, 45, 45))
            d.text((X(t) + 2, LH + SH + 32), str(t), font=F, fill=(160, 160, 160))
    for x, col, n, w in tracks:
        L = lev(x) - Iv; tt = t0 + np.arange(len(L)) * 0.05
        d.line([(X(a), Y(b)) for a, b in zip(tt, L) if a <= t1], fill=col, width=w)
    y0 = LH + 25
    b = bed.mean(1)[::3]
    f, tq, Z = signal.spectrogram(b, 16000, nperseg=2048, noverlap=1536)
    Z = 10 * np.log10(Z + 1e-14); Z = np.clip((Z + 110) / 70, 0, 1)
    rows = np.geomspace(30, 7900, SH)[::-1]
    A_ = Z[np.searchsorted(f, rows).clip(0, len(f) - 1)]
    A_ = np.array(Image.fromarray((A_ * 255).astype(np.uint8)).resize((PW, SH)))
    rgb = np.stack([np.clip(A_ * 1.6, 0, 255), np.clip((A_ - 90) * 1.5, 0, 255), np.clip((A_ - 170) * 3, 0, 255)], -1).astype(np.uint8)
    img.paste(Image.fromarray(rgb), (50, y0))
    for hz in (50, 100, 250, 500, 1000, 2000, 4000):
        yy = y0 + SH * (1 - np.log(hz / 30) / np.log(7900 / 30)); d.text((5, yy - 7), f'{hz}', font=F, fill=(150, 150, 150))
    ty = LH + SH + 48
    if ours:
        cues = json.load(open(os.path.join(A.cues, 'sfx_cues.json')))
        n1 = 0
        for c in cues:
            if t0 <= c['t'] <= t1 and not c['params'].get('stream'):
                n1 += 1
                d.line([(X(c['t']), 20), (X(c['t']), 34)], fill=(255, 60, 60) if c.get('hit') else (80, 255, 80), width=2)
        mc = json.load(open(os.path.join(A.cues, 'music_cues.json')))
        for e in mc['events']:
            if t0 - 8 <= e['t'] <= t1:
                if e['type'] == 'silence':
                    d.rectangle([X(e['t']), 36, X(e['t'] + e.get('len', 1.7)), 42], fill=(255, 160, 40))
                elif e['type'] == 'riser':
                    d.line([(X(e['t'] - e.get('len', 6)), 46), (X(e['t']), 38)], fill=(255, 160, 40), width=2)
                elif e['type'] in ('hit', 'stinger', 'braam', 'rule', 'sub_drop'):
                    d.polygon([(X(e['t']) - 4, 36), (X(e['t']) + 4, 36), (X(e['t']), 46)], fill=(255, 160, 40))
        tl = json.load(open(os.path.join(W, 'align', 'timeline.json')))
        k = 0
        for l in tl['lines']:
            if l['end'] >= t0 and l['t'] <= t1:
                d.text((X(max(t0, l['t'])), ty + 14 * (k % 4)), l['en'][:60], font=F, fill=(170, 190, 230)); k += 1
        A.label += f'  | {n1} one-shots ({n1 / (t1 - t0) * 60:.0f}/min) green=sfx red=hit, orange=music events | white=bed orange=music green=sfx blue=voice, LU rel voice'
    else:
        asr = json.load(open(os.path.join(W, 'ref2', 'data', f'asr_{nm}.json')))
        k = 0
        for seg in asr:
            if seg['t1'] >= t0 and seg['t0'] <= t1:
                d.text((X(max(t0, seg['t0'])), ty + 14 * (k % 4)), seg['text'][:70], font=F, fill=(170, 190, 230)); k += 1
        A.label += '  | white=bed (separated), blue=voice; LU rel voice integrated'
    d.text((50, 2), A.label, font=F, fill=(255, 220, 120))
    img.save(A.out); print(A.out)


if __name__ == '__main__':
    main()
