"""EP01 sound QA sheets (1080x1920 JPEG "stills" of sound): every cue in its mix context, the reference comparisons,
the 5-second test null and an episode overview.

    python3 -I qa.py STEMS_DIR OUT_DIR [--test TEST5_MIX.wav] [--refs REF60_DIR] [--stems STEMS_DIR2]

STEMS_DIR holds a mix.py run (ep01_voice/sfx/beds/mix.wav + ep01_mix_report.json), ideally `--profile full` so every
cue is drawn. Panels: log-frequency spectrogram of the full mix (voice + SFX + bed) from 0.8 s before to 2.2 s after
the cue, with the voice (white), SFX (cyan) and bed (orange) 10 ms envelopes and the picture event (lime) / cuts (grey).
"""
import os, sys, json, argparse, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import soundfile as sf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import spectrogram

SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(os.path.join(os.path.dirname(HERE), 'timeline.json')))
CUTS = [s['start'] for s in TL['shots']]


def env_db(x, w=0.01):
    k = int(w * SR); c = np.concatenate([[0], np.cumsum(x ** 2)])
    e = (c[k:] - c[:-k]) / k
    return 20 * np.log10(np.sqrt(np.maximum(e, 0)) + 1e-9)


def spec_panel(ax, x, t0, title, events=(), extra=None, vmin=-115, vmax=-25):
    f, tt, S_ = spectrogram(x.mean(1) if x.ndim == 2 else x, SR, nperseg=1024, noverlap=896)
    ax.pcolormesh(tt + t0, f / 1000, 10 * np.log10(S_ + 1e-14), vmin=vmin, vmax=vmax, shading='auto', cmap='magma')
    ax.set_yscale('symlog', linthresh=1); ax.set_ylim(0.03, 20)
    ax.set_yticks([0.05, 0.1, 0.25, 0.5, 1, 2, 4, 8, 16]); ax.set_yticklabels(['50', '100', '250', '500', '1k', '2k', '4k', '8k', '16k'], fontsize=6)
    ax.tick_params(labelsize=6); ax.set_title(title, fontsize=7.5, loc='left')
    t1 = t0 + len(x) / SR
    ax.set_xlim(t0, t1)
    for c in CUTS:
        if t0 < c < t1: ax.axvline(c, color='#bbbbbb', lw=0.8, ls=':')
    for e in events: ax.axvline(e, color='lime', lw=0.9)
    if extra:
        ax2 = ax.twinx(); ax2.set_ylim(-70, 0); ax2.tick_params(labelsize=6)
        for y, col in extra:
            e = env_db(y.mean(1) if y.ndim == 2 else y)
            ax2.set_xlim(t0, t1); ax2.plot(t0 + np.arange(len(e)) / SR, e, color=col, lw=0.6)


def cue_sheets(stems, out):
    rep = json.load(open(os.path.join(stems, 'ep01_mix_report.json')))
    v, _ = sf.read(os.path.join(stems, 'ep01_voice.wav')); s, _ = sf.read(os.path.join(stems, 'ep01_sfx.wav'))
    b, _ = sf.read(os.path.join(stems, 'ep01_beds.wav')); m = v + s + b
    cues = rep['cues']
    per = 7; files = []
    for k in range(0, len(cues), per):
        fig, axs = plt.subplots(per, 1, figsize=(10.8, 19.2), dpi=100)
        for ax, q in zip(axs, cues[k:k + per]):
            a = max(0.0, q['t'] - 0.8); z = min(TL['duration'], q['t'] + 2.2)
            i0, i1 = int(a * SR), int(z * SR)
            ev = q['times'] or [q['t']]
            title = (f"{q['cue']}  t={q['t']:.3f} s  {q['shot']}  p{q['prio']}{'  layer of ' + q['layer_of'] if q['layer_of'] else ''}"
                     f"  gain {q['gain_db']:+.1f} dB  clip {q['start']:.2f}-{q['end']:.2f}")
            spec_panel(ax, m[i0:i1], a, title, ev, [(v[i0:i1], 'white'), (s[i0:i1], 'cyan'), (b[i0:i1], 'orange')])
        for ax in axs[len(cues[k:k + per]):]: ax.axis('off')
        fig.suptitle(f'EP01 SFX in context ({rep["profile"]} profile): mix spectrogram, voice white / SFX cyan / bed orange (dBFS, right), '
                     'event lime, cuts grey', fontsize=8)
        plt.tight_layout(rect=(0, 0, 1, 0.985))
        p = os.path.join(out, f'qa_cues_{k // per + 1:02d}.jpg'); plt.savefig(p, pil_kwargs={'quality': 72}); plt.close(fig); files.append(p)
    return files


def load_ref(path, a, b, stream_mono=True):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(a), '-t', str(b - a), '-i', path, '-vn', '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)


def ref_sheet(stems, refs, stemdir, out):
    """Signature hits against the references (TF/CG/AW mixes or their instrumental stems)."""
    v, _ = sf.read(os.path.join(stems, 'ep01_voice.wav')); s, _ = sf.read(os.path.join(stems, 'ep01_sfx.wav'))
    b, _ = sf.read(os.path.join(stems, 'ep01_beds.wav')); m = v + s + b
    ours = lambda a, z: m[int(a * SR):int(z * SR)]
    aw_inst = os.path.join(stemdir, 'aw_full_(Instrumental)_UVR-MDX-NET-Inst_HQ_3.flac')
    cg_inst = os.path.join(stemdir, 'cg_full_(Instrumental)_UVR-MDX-NET-Inst_HQ_3.flac')
    rows = [
        ('OURS SUBBOOM 36.5-40.5 ("the lawn MOVED": whoosh + sub-boom + rumble)', ours(36.5, 40.5), 36.5, [37.28]),
        ('REF TF 39.9-43.9 mix (swarm whoosh + sub-boom 40.85, rumble < 120 Hz to 43.7)', load_ref(os.path.join(refs, 'tooth_fairies.mp4'), 39.9, 43.9), 39.9, [40.85]),
        ('REF CG 71.5-75.5 instrumental stem (sub-boom 72.24, +55 dB 25-110 Hz)', sf.read(cg_inst, start=int(71.5 * 44100), stop=int(75.5 * 44100))[0], 71.5, [72.24]),
        ('OURS FWOOM 86.4-89.4 (whoosh + warm shimmer, second pulse on "flared")', ours(86.4, 89.4), 86.4, [86.86, 87.92]),
        ('REF TF 110.3-113.3 mix (rising whoosh into bright shimmer 111.0-112.6)', load_ref(os.path.join(refs, 'tooth_fairies.mp4'), 110.3, 113.3), 110.3, [111.0]),
        ('OURS TINK_WHOOSH + FIP 41.4-43.4, TINKS 44.4-46.4 (music-box tines, E pentatonic)', np.concatenate([ours(41.4, 43.4), ours(44.4, 46.4)]), 41.4, [41.76]),
        ('REF AW 37.0-39.0 + 72.9-74.9 instrumental ("Tink, tink" music-box tines 1.7-1.9 kHz)', np.concatenate([sf.read(aw_inst, start=int(37.0 * 44100), stop=int(39.0 * 44100))[0], sf.read(aw_inst, start=int(72.9 * 44100), stop=int(74.9 * 44100))[0]]), 37.0, []),
        ('OURS GRIND 66.3-68.3 (stepped stone grind, 20 Hz jerks) + TIK_SLOW 83.5-84.5', np.concatenate([ours(66.3, 68.3), ours(83.5, 84.5)]), 66.3, [66.55]),
        ('REF AW 90.9-93.9 instrumental (door creak: dense periodic clicks)', sf.read(aw_inst, start=int(90.9 * 44100), stop=int(93.9 * 44100))[0], 90.9, []),
    ]
    fig, axs = plt.subplots(len(rows), 1, figsize=(10.8, 19.2), dpi=100)
    for ax, (title, x, t0, ev) in zip(axs, rows):
        if x.ndim == 1: x = np.stack([x, x], 1)
        spec_panel(ax, x, t0, title, ev)
    fig.suptitle('EP01 signature SFX vs the references (same colour scale; refs at 44.1 kHz shown on the 48 kHz axis)', fontsize=8)
    plt.tight_layout(rect=(0, 0, 1, 0.985))
    p = os.path.join(out, 'qa_refs.jpg'); plt.savefig(p, pil_kwargs={'quality': 72}); plt.close(fig)
    return p


def test_sheet(stems, test, out):
    m, _ = sf.read(os.path.join(stems, 'ep01_mix.wav'), frames=5 * SR)
    r, _ = sf.read(test)
    n = min(len(m), len(r)); d = m[:n] - r[:n]
    fig, axs = plt.subplots(4, 1, figsize=(10.8, 19.2), dpi=100, gridspec_kw=dict(height_ratios=[3, 3, 3, 2]))
    spec_panel(axs[0], r, 0.0, 'APPROVED TEST test5_mix.wav 0-5 s', [0.0, 2.2333])
    spec_panel(axs[1], m, 0.0, 'EPISODE ep01_mix.wav 0-5 s (identical to 3.40 s; then "First, your grandma gets shorter" and the room bed from the 3.567 cut)', [0.0, 2.2333])
    spec_panel(axs[2], d, 0.0, 'DIFFERENCE episode - test (same colour scale)', [3.40])
    t = np.arange(n) / SR
    ed = env_db(d.mean(1)); er = env_db(r[:n].mean(1))
    axs[3].plot(t[:len(er)], er, lw=0.6, label='test mix'); axs[3].plot(t[:len(ed)], ed, lw=0.6, label='difference')
    axs[3].axvline(3.40, color='k', lw=0.8, ls='--'); axs[3].set_ylim(-140, 0); axs[3].legend(fontsize=7); axs[3].tick_params(labelsize=7)
    axs[3].set_title('10 ms envelopes (dBFS): the difference stays at the 24-bit floor until 3.40 s', fontsize=8, loc='left')
    plt.tight_layout()
    p = os.path.join(out, 'qa_test5_vs_episode.jpg'); plt.savefig(p, pil_kwargs={'quality': 72}); plt.close(fig)
    return p


def overview(stems, out):
    import catalog as C
    rep = json.load(open(os.path.join(stems, 'ep01_mix_report.json')))
    v, _ = sf.read(os.path.join(stems, 'ep01_voice.wav')); s, _ = sf.read(os.path.join(stems, 'ep01_sfx.wav'))
    b, _ = sf.read(os.path.join(stems, 'ep01_beds.wav')); m, _ = sf.read(os.path.join(stems, 'ep01_mix.wav'))
    fig, axs = plt.subplots(5, 1, figsize=(10.8, 19.2), dpi=100, sharex=False)
    segs = [(0, 23), (23, 46), (46, 69), (69, 92), (92, 113.3)]
    for ax, (a, z) in zip(axs, segs):
        sl = slice(int(a * SR), int(z * SR))
        for x, col, lab in [(v[sl], 'k', 'voice (3 s short-term)'), (s[sl], 'tab:cyan', 'SFX (400 ms)'), (b[sl], 'tab:orange', 'bed (400 ms)'), (m[sl], 'tab:red', 'mix (3 s)')]:
            w = 3.0 if lab.startswith(('voice', 'mix')) else 0.4
            L, tt = C.momentary(x, win=w, hop=0.05)
            ax.plot(a + tt + w / 2, L, color=col, lw=0.8 if col != 'k' else 1.0, label=lab)
        for c in CUTS:
            if a <= c < z: ax.axvline(c, color='#cccccc', lw=0.5)
        for q in rep['cues']:
            if a <= q['t'] < z:
                ax.axvline(q['t'], color='g' if q['prio'] == 1 else 'b', lw=0.8, ls='--')
                ax.text(q['t'], -12.5, q['cue'], rotation=90, fontsize=5.5, va='top', ha='right')
        for pz in rep['pauses']:
            if pz['planned'] and a <= pz['t0'] < z: ax.axvspan(pz['t0'], pz['t1'], color='y', alpha=0.3)
        ax.axhline(-16, color='k', lw=0.5, ls=':'); ax.set_ylim(-60, -10); ax.set_xlim(a, z); ax.tick_params(labelsize=7)
    axs[0].legend(fontsize=6, loc='lower right', ncol=4)
    axs[0].set_title(f"EP01 mix overview ({rep['profile']}): integrated {rep['mix_integrated']} LUFS, LRA {rep['mix_lra']}, TP {rep['true_peak_after_db']} dBTP, "
                     f"{rep['events_per_min']} events/min; green = primary cue, blue = sweetener, yellow = planned pause, grey = cuts", fontsize=7.5, loc='left')
    plt.tight_layout()
    p = os.path.join(out, 'qa_overview.jpg'); plt.savefig(p, pil_kwargs={'quality': 75}); plt.close(fig)
    return p


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('stems'); ap.add_argument('out')
    ap.add_argument('--test', default=None); ap.add_argument('--refs', default=None); ap.add_argument('--refstems', default=None)
    ap.add_argument('--overview-stems', default=None)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    fs = cue_sheets(a.stems, a.out)
    if a.refs: fs.append(ref_sheet(a.stems, a.refs, a.refstems, a.out))
    if a.test: fs.append(test_sheet(a.overview_stems or a.stems, a.test, a.out))
    fs.append(overview(a.overview_stems or a.stems, a.out))
    print('\n'.join(fs))
