"""Scene sheets of a finished mix (the Bunnyman film): one PNG per scene window, so a mix can be checked by eye against
the picture and the narration.

    python3 audio/mix_scenes.py [_work/mix/final] [--scenes name,name] [--out DIR]       (from film/)

Each sheet: the mix's spectrogram (0-8 kHz) with the narration's lines (grey bars + their first words), every SFX cue
as mixed (cues_used/sfx_cues.json: orange ticks + names), the score's events (hits / stingers / braams / sub drops
red, silences shaded blue, risers and swells green) and the identity layer (the jingle's versions, magenta bars);
under it the 100 ms levels of the voice (white), the music (blue) and the SFX (orange) stems, LU relative to the voice
stem's integrated loudness, with the 0 / -10 / -20 LU lines. Reads <dir>/mix_en.wav (or mix.wav), <dir>/stems/*.wav,
<dir>/cues_used/*.json, W/align/timeline.json. Writes <dir>/scenes/NN_name.png.
"""
import argparse, json, os, sys
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SR = 48000
W = os.path.normpath(os.path.join(HERE, '..', '_work'))

# (name, t0, t1): the film's scenes, narration seconds (W/align/timeline.json, 1077.99 s edit: the channel rename cut
# 1.175 s from line 409, so only the last window moved)
SCENES = [
    ('cold_open', 0.0, 34.0), ('hospital_rules', 33.0, 66.0), ('parade_1987', 65.0, 99.0),
    ('woods_sunrise', 98.0, 137.0), ('house_dad', 136.0, 172.0), ('june_dress', 170.0, 201.0),
    ('song_woods', 199.0, 232.0), ('treeline_mom', 230.0, 260.0), ('comment_vhs', 256.0, 288.0),
    ('egg_peephole', 286.0, 317.0), ('rattle_ring', 316.0, 345.0), ('ring_pocket', 343.0, 371.0),
    ('knocks', 368.0, 390.0), ('grandma_knock', 386.0, 418.0), ('slot_open', 424.0, 446.0),
    ('slot_june', 444.0, 478.0), ('girl_cry', 476.0, 500.0), ('wake_attic', 502.0, 538.0),
    ('diary', 536.0, 576.0), ('attic_corner', 572.0, 602.0), ('window_door', 598.0, 628.0),
    ('hatchet_knob', 614.0, 642.0), ('drawing_fight', 660.0, 688.0), ('dont_open', 685.0, 712.0),
    ('sunrise_key', 708.0, 740.0), ('body_face', 737.0, 772.0), ('trick_count', 768.0, 800.0),
    ('reveal', 788.0, 830.0), ('recap', 850.0, 892.0), ('swap_seven', 888.0, 920.0),
    ('scream_police', 912.0, 952.0), ('hospital_visits', 950.0, 980.0), ('ending', 970.0, 1000.0),
    ('outro_a', 993.0, 1030.0), ('outro_b', 1026.0, 1063.0), ('outro_end', 1058.0, 1088.0),
]
HIT_T = ('hit', 'stinger', 'braam', 'sub_drop', 'rule')


def lev(x, win=0.1, hop=0.05):
    m = (x.astype(np.float64) ** 2).mean(1) if x.ndim == 2 else x.astype(np.float64) ** 2
    k, h = int(win * SR), int(hop * SR)
    c = np.concatenate([[0.0], np.cumsum(m)])
    i = np.arange(0, max(1, len(m) - k), h)
    return -0.691 + 10 * np.log10((c[i + k] - c[i]) / k + 1e-20)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dir', nargs='?', default=os.path.join(W, 'mix', 'final'))
    ap.add_argument('--scenes', default=None); ap.add_argument('--out', default=None)
    A = ap.parse_args()
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import sfx as SX
    d = A.dir
    mixp = os.path.join(d, 'mix_en.wav') if os.path.exists(os.path.join(d, 'mix_en.wav')) else os.path.join(d, 'mix.wav')
    mix = sf.read(mixp, dtype='float32', always_2d=True)[0]
    st = {k: sf.read(os.path.join(d, 'stems', f'{k}.wav'), dtype='float32', always_2d=True)[0]
          for k in ('voice_en', 'music', 'sfx')}
    Lv = SX.lufs_int(st['voice_en'])
    tl = json.load(open(os.path.join(W, 'align', 'timeline.json')))['lines']
    used = os.path.join(d, 'cues_used')
    sc = json.load(open(os.path.join(used, 'sfx_cues.json')))
    mc = json.load(open(os.path.join(used, 'music_cues.json')))
    out = A.out or os.path.join(d, 'scenes'); os.makedirs(out, exist_ok=True)
    want = set(A.scenes.split(',')) if A.scenes else None
    for k, (name, t0, t1) in enumerate(SCENES):
        if want and name not in want:
            continue
        a, b = int(t0 * SR), min(len(mix), int(t1 * SR))
        if b <= a:
            continue
        fig = plt.figure(figsize=(18, 7.5))
        ax = fig.add_axes([0.04, 0.42, 0.95, 0.53]); ax2 = fig.add_axes([0.04, 0.07, 0.95, 0.3], sharex=ax)
        x = mix[a:b].mean(1)
        ax.specgram(x + 1e-9, NFFT=2048, Fs=SR, noverlap=1536, cmap='magma', vmin=-130, vmax=-35,
                    xextent=(t0, t0 + len(x) / SR))
        ax.set_ylim(0, 8000); ax.set_xlim(t0, t1)
        for l in tl:
            if l['end'] > t0 and l['t'] < t1:
                ax.add_patch(plt.Rectangle((l['t'], 7400), l['end'] - l['t'], 450, color='#cccccc', alpha=0.55))
                ax.text(max(l['t'], t0) + 0.05, 7550, f"{l.get('who', 'N')}: {l['en'][:34]}", fontsize=6.5, color='black')
        yb = 6800
        for c in sc:
            try:
                tc = float(c['t'])
            except (KeyError, TypeError, ValueError):
                continue
            if t0 <= tc <= t1:
                ax.axvline(tc, ymin=0.0, ymax=0.82, color='orange', lw=0.8, alpha=0.8)
                yb = 6600 if yb < 3000 else yb - 520
                ax.text(tc + 0.03, yb, str(c.get('name'))[:16] + f" {float(c.get('gain_db', 0) or 0):+.0f}", fontsize=6,
                        color='orange', rotation=0)
        for e in mc.get('events', []):
            te = float(e.get('t', -1))
            ln = float(e.get('len') or 0)
            if te > t1 or te + max(ln, 0.1) < t0:
                continue
            ty = e.get('type')
            if ty == 'silence':
                ax.axvspan(te, te + ln, ymin=0, ymax=0.05, color='#3399ff', alpha=0.9)
                ax2.axvspan(te, te + ln, color='#3399ff', alpha=0.12)
            elif ty in HIT_T:
                ax.axvline(te, color='red', lw=1.6, alpha=0.9)
                ax.text(te + 0.03, 300, f"{ty}{' B' + str(e.get('boost')) if e.get('boost') else ''}", fontsize=7,
                        color='red')
            elif ty in ('riser', 'swell'):
                s0 = te - ln if ty == 'riser' else te
                ax.axvspan(s0, s0 + ln, ymin=0.05, ymax=0.09, color='#33cc33', alpha=0.8)
            elif ty in ('jingle', 'show'):
                ax.axvspan(te, te + (ln or 4.0), ymin=0.09, ymax=0.13, color='magenta', alpha=0.8)
                ax.text(te + 0.05, 1150, f"{ty}:{e.get('version', e.get('slug', ''))}"[:24], fontsize=7, color='magenta')
        ax.set_title(f'{k:02d} {name}  {t0:.0f}-{t1:.0f} s   (orange SFX cues as mixed, red score hits, blue silences, '
                     f'green risers/swells, magenta the jingle / tunes)', fontsize=9)
        ax.tick_params(labelsize=7)
        tt = t0 + np.arange(len(lev(st['voice_en'][a:b]))) * 0.05 + 0.05
        for key, col in (('music', '#4da6ff'), ('sfx', 'orange'), ('voice_en', 'white')):
            L = lev(st[key][a:b]) - Lv
            ax2.plot(tt[:len(L)], L[:len(tt)], color=col, lw=0.9, label=key)
        Lm = lev(mix[a:b]) - Lv
        ax2.plot(tt[:len(Lm)], Lm[:len(tt)], color='#888888', lw=0.6, label='mix')
        for y0 in (0, -10, -20):
            ax2.axhline(y0, color='#666666', lw=0.6)
        ax2.set_facecolor('#151515'); ax2.set_ylim(-45, 12); ax2.legend(loc='upper right', fontsize=7)
        ax2.tick_params(labelsize=7); ax2.set_ylabel('LU rel voice', fontsize=7)
        fig.savefig(os.path.join(out, f'{k:02d}_{name}.png'), dpi=70)
        plt.close(fig)
        print('scene', k, name)


if __name__ == '__main__':
    main()
