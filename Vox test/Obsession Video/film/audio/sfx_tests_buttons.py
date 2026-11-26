"""sfx_tests_buttons.py: the Buttons film's 8 test sounds -> W/mix/tests (+ tests.json), then the owner's per-event
check on them (audio/measure_mix.py events_main: first / last 10 ms against the peak, momentary loudness against the
voice at its film time) -> tests_measure.json. Two listening previews put a test under its voice line.

    1 motif_box        the clean music box of the chat ("Our song.", 118.2 s)
    2 motif_winddown   the stolen box winding down in the closet at 3 a.m. (231.7 s)
    3 motif_detuned    the climax box bent onto the Blank's sung words, stopping one note short (541.2 s)
    4 motif_chime      the son's tablet chime down the hall, in the gap before "Down the hall" (695.0 s)
    5 tik_a / tik_b / tik_c   three of the script's tik beats (beats.json): the same sound, varied
    6 ping             the first chat ping (beats.json)
    7 scare_hit        a planned scare hit at +8 LU over the voice, smooth release ("Like somebody was inside it.")
    8 bed_helpline     the kitchen-table bed under Mom's "Thank you for calling. I'm listening."
    previews: bed_under_voice.wav (8 + the voice), climax_preview.wav (3 + coat_buttons + the voice)

CLI: python3 audio/sfx_tests_buttons.py        (from film/; about a minute)
"""
import json, os, sys
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sfx as SX                                        # noqa: E402
import motif_buttons as M                               # noqa: E402
import music_plan as MP                                 # noqa: E402
import beats as BT                                      # noqa: E402
import measure_mix as MM                                # noqa: E402

SR = SX.SR
OUT = os.path.join(SX.W, 'mix', 'tests')
VO = os.path.join(SX.W, 'narration', 'narration_en.wav')
MOTIF_REL = {'box': -12.0, 'winddown': -9.0, 'detuned': -8.0, 'chime': -12.0}   # momentary max, LU re the voice


def _voice_gain():
    v = sf.read(VO, dtype='float32', always_2d=True)[0].mean(1)
    return float(10 ** ((SX.REF - SX.lufs_int(SX.st(v))) / 20))


def voice(t0, t1, g):
    v = sf.read(VO, start=int(t0 * SR), stop=int(t1 * SR), dtype='float32', always_2d=True)[0].mean(1)
    return SX.st(v * g)


def motif_event(ev):
    """A plan identity event rendered as score.py renders it: anchors relative to the event, cropped to its len,
    eased in by its fade and out over 0.8 s."""
    kw = {k: ev[k] for k in ('phrases', 'n', 'loops', 'tempo', 'amount') if k in ev}
    if ev.get('anchors'):
        kw['anchors'] = [(float(b), float(x) - ev['t']) for b, x in ev['anchors']]
    y, info = M.render(ev['version'], seed=3, **kw)
    n = int(float(ev.get('len', len(y) / SR)) * SR)
    y = np.array(y[:n], np.float32)
    a, b = max(1, int(float(ev.get('fade', 0.03)) * SR)), min(len(y) // 2, int(0.8 * SR))
    y[:a] *= np.sin(np.linspace(0, np.pi / 2, a))[:, None] ** 2
    if len(y) >= n:
        y[-b:] *= np.cos(np.linspace(0, np.pi / 2, b))[:, None] ** 2
    if ev.get('space'):
        y = SX.st(SX.space(y, ev['space'], 3))
    return SX.st(y) * np.float32(10 ** ((SX.REF + MOTIF_REL.get(ev['version'], -10.0) - SX.mom_max(y)) / 20)), info


def main():
    os.makedirs(OUT, exist_ok=True)
    L, _ = MP.load_lines()
    g = _voice_gain()
    rows, ident = [], {e['version']: e for e in MP.identity_events(L)}

    def put(label, y, t, pre=0.0, scare=False):
        sf.write(os.path.join(OUT, label + '.wav'), y, SR, subtype='FLOAT')
        rows.append({'t': round(float(t), 3), 'file': label + '.wav', 'pre': pre, 'scare': scare, 'label': label})
        return y

    for v in ('box', 'winddown', 'detuned', 'chime'):
        y, info = motif_event(ident[v])
        put('motif_' + v, y, ident[v]['t'])
        print(f"motif_{v}: {len(y) / SR:.2f} s, notes heard {len([n for n in info['notes'] if n[0] < len(y) / SR])}")
    bc = BT.cues()
    for lab, k in (('tik_a', 0), ('tik_b', 2), ('tik_c', 14), ('ping', 1)):
        c = bc[k]
        y, pre = SX.render_event(c['name'], seed=c['seed'], space=c['space'], **c['params'])
        put(lab, y, c['t'], pre)
        m = SX.mono(y); P = np.abs(np.fft.rfft(m)) ** 2; f = np.fft.rfftfreq(len(m), 1 / SR)
        print(f"{lab}: {c['tag']} {len(y) / SR:.2f} s, centroid {int((f * P).sum() / P.sum())} Hz, "
              f"Mmax {SX.mom_max(y):.1f}, share > 8 kHz {100 * P[f > 8000].sum() / P.sum():.1f} %")
    th = MP.resolve('end:Like somebody was inside it +0.05', L)
    y, pre = SX.render_event('impact_hit', seed=5)
    y = y * np.float32(10 ** ((SX.REF + 8.0 - SX.mom_max(y)) / 20))
    put('scare_hit', y, th, pre, scare=True)
    tb = MP.resolve('Mom worked twelve-hour help-line shifts', L)
    y, _ = SX.render_event('helpline_kitchen', seed=1, dur=12.0)
    put('bed_helpline', y, tb)
    v = voice(tb, tb + 12.0, g)
    sf.write(os.path.join(OUT, 'bed_under_voice.wav'), (v + y[:len(v)]) * 0.7, SR, subtype='PCM_16')
    ev = ident['detuned']
    yb, _ = SX.render_event('coat_buttons', seed=2, times=[0.0, 0.72, 1.68, 2.32, 3.36, 4.88])
    ym, _ = motif_event(ev)
    v = voice(ev['t'] - 5.0, ev['t'] + 10.0, g)
    mix = v.copy(); i = int(5.0 * SR)
    mix[i:i + len(ym)] += ym[:len(mix) - i]
    j = int((MP.resolve('warm two for snug#One', L) - ev['t'] + 5.0) * SR)
    mix[j:j + len(yb)] += yb[:len(mix) - j]
    sf.write(os.path.join(OUT, 'climax_preview.wav'), mix * 0.7, SR, subtype='PCM_16')
    pj = os.path.join(OUT, 'tests.json')
    json.dump(rows, open(pj, 'w'), indent=1)
    MM.events_main(pj)


if __name__ == '__main__':
    main()
