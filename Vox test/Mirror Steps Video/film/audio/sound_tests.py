"""Render the mirror film's trickiest sounds to _work/mix/tests/ (house levels: absolute for a -14 LUFS narration).

    python3 audio/sound_tests.py [out_dir]          (run from film/)

Writes 8 WAVs (48 kHz 24-bit), tests.json (description, duration, peak, momentary max, event times) and a
spectrogram contact sheet tests_sheet.png.
"""
import os, sys, json
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sfx as SX                      # noqa: E402
import mix as MX                      # noqa: E402

SR = SX.SR
FILM = os.path.normpath(os.path.join(HERE, '..'))


def R(name, space=None, seed=1, **p):
    return SX.render_event(name, seed=seed, space=space, **p)


def seq(items, total=None, bed=None):
    """items: [(t, name, space, gain_db, params, seed)] placed like mix.py (audio starts at t - pre)."""
    ev = []; times = []; memo = {}
    for t, name, space, g, p, sd in items:
        k = (name, space, json.dumps(p, sort_keys=True), sd) if p.get('loop_id') else None
        y, pre = memo[k] if k in memo else R(name, space, sd, **p)
        if k:
            memo[k] = (y, pre)
        ev.append((max(0.0, t - pre), y * 10 ** (g / 20))); times.append([round(t, 3), name])
    out = SX._seq(ev, 0.5)
    if total:
        out = out[:int(total * SR)] if len(out) > total * SR else np.pad(out, ((0, int(total * SR) - len(out)), (0, 0)))
    if bed is not None:
        b = bed[:len(out)]; out[:len(b)] += b
    return out, times


def main(out):
    os.makedirs(out, exist_ok=True)
    T = []

    def save(fn, desc, y, times):
        y = np.asarray(y, np.float32)
        pk = SX.peak(y)
        if pk > 10 ** (-1 / 20):                       # test files only: keep them unclipped (the mix limits)
            y = y * np.float32(10 ** (-1 / 20) / pk)
        sf.write(os.path.join(out, fn), y, SR, subtype='PCM_24')
        T.append(dict(file=fn, desc=desc, dur=round(len(y) / SR, 2), peak_dbfs=round(float(SX.db(SX.peak(y))), 1),
                      mom_max_lufs=round(SX.mom_max(y), 1), events=times))
        print(f'{fn:40s} {len(y) / SR:5.1f}s pk {SX.db(SX.peak(y)):5.1f} Mmax {SX.mom_max(y):5.1f} | {desc}')

    # 1 the bells
    y, tt = seq([(0.3, 'bell_cracked', 'close', 0, {'strike': 'clapper'}, 1),
                 (4.5, 'bell_clean', 'far', -2, {}, 1),
                 (12.0, 'bell_cracked', 'close', 2, {'strike': 'padlock'}, 2),
                 (16.0, 'bell_cracked', 'memory', -6, {'strike': 'drop'}, 3)], 20.0)
    save('01_bells_real_fake_padlock.wav', 'the REAL cracked bell (clean D6 note, then the crack buzz and spoon-like '
         'clinks) / the FAKE bell (same partials, perfect, long church tail) / padlock strike on the real bell (535.36) / '
         'the memory version (65.92)', y, tt)
    # 2 the nail click (identical twice, the second over the camp-night room)
    y, tt = seq([(0.4, 'nail_click_glass', 'close', 0, {'loop_id': 'nail'}, 1),
                 (0.4, 'glass_resonance', 'close', -8, {}, 1),
                 (3.0, 'nail_click_glass', 'close', 0, {'loop_id': 'nail'}, 1),
                 (3.0, 'glass_resonance', 'close', -6, {}, 2)], 6.0)
    save('02_nail_click_identical.wav', 'the signature: ONE crisp nail click on clean glass + thin ring, then the '
         'identical buffer again (143.29 and 690.19)', y, tt)
    # 3 lipstick steps and the eighth line
    items = [(0.3 + 0.32 * k, 'lipstick_draw', 'close', -4, {}, 10 + k) for k in range(7)]
    items += [(3.2, 'lipstick_draw', 'close', -8, {'clean': True}, 1), (3.2, 'glass_resonance', 'close', -10, {}, 3),
              (5.0, 'lipstick_smear', 'close', -2, {}, 1), (5.9, 'lipstick_smear', 'close', -4, {}, 2),
              (6.6, 'lipstick_smear', 'close', -16, {'kind': 'crumb'}, 3)]
    y, tt = seq(items, 8.0)
    save('03_lipstick_steps_eighth_line.wav', 'seven waxy lipstick steps on the glass, the eighth line drawing itself '
         '(thin, glassy, too clean), then a finger smearing the steps and the crumbly rub', y, tt)
    # 4 towel throw, fingers through the cloth, drop, then the top-down wipe
    y, tt = seq([(0.3, 'towel_cloth', 'close', -3, {'kind': 'snatch'}, 1),
                 (1.0, 'towel_cloth', 'close', -2, {'kind': 'flap'}, 2),
                 (2.2, 'cloth_press', 'close', -2, {'kind': 'stretch'}, 3),
                 (3.1, 'cloth_press', 'close', -6, {'kind': 'stretch'}, 4),
                 (4.6, 'towel_drop', 'close', -3, {}, 5),
                 (6.0, 'glass_wipe', 'close', 0, {}, 6), (6.64, 'glass_wipe', 'close', 0, {}, 7),
                 (6.96, 'glass_wipe', 'close', -1, {}, 8), (8.2, 'glass_wipe', 'close', -3, {}, 9)], 10.0)
    save('04_towel_throw_press_drop_wipe.wav', 'towel snatched and thrown over the glass (249.67-250.87), fingers pressing '
         'through the cloth, the towel dropping straight down, then the rule-7 wipes from the top down (618.73-620.89)', y, tt)
    # 5 the sprinkler loop (two passes, the spits identical)
    one = [(0.3, 'sprinkler_spit', 'outside', -8, {}, 1), (0.7, 'sprinkler_spit', 'outside', -4, {'loop_id': 'A'}, 1),
           (1.1, 'sprinkler_spit', 'outside', -4, {'loop_id': 'B'}, 1), (1.82, 'sprinkler_spit', 'outside', -12, {'kind': 'die'}, 1)]
    y, tt = seq(one + [(4.0, 'sprinkler_spit', 'outside', -4, {'loop_id': 'A'}, 1),
                       (4.48, 'sprinkler_spit', 'outside', -4, {'loop_id': 'B'}, 1)], 6.5)
    save('05_sprinkler_spits_loop.wav', 'valve hiss, two spits, gurgle and die (298.47-299.99); later the SAME two spits '
         'come round again (415.75/416.23: the loop)', y, tt)
    # 6 the drop that hangs and repeats + the clock jerking backward
    y, tt = seq([(0.3, 'water_drip', 'close', -6, {'loop_id': 'drip'}, 1), (1.26, 'water_drip', 'close', -7, {}, 2),
                 (2.2, 'drop_reverse', 'close', -4, {}, 1), (2.9, 'tinnitus', 'dry', -6, {'dur': 2.5}, 1),
                 (5.4, 'water_drip', 'close', -3, {'loop_id': 'drip'}, 1),
                 (7.0, 'clock_tick', 'inside', -6, {'dur': 2.78}, 1),
                 (9.8, 'clock_tick_backward', 'inside', -2, {'n': 4}, 1)], 13.5)
    save('06_drop_hangs_clock_backward.wav', 'drips, the drop rising and hanging (stopped-time tone), the SAME drip sample '
         'falling again (332.37 -> 346.83); then the cabin clock ticking and the second hand jerking backward (281.69)', y, tt)
    # 7 foley pack
    y, tt = seq([(0.3, 'crate_break', 'close', -2, {}, 1), (0.78, 'crate_break', 'close', -2, {}, 2),
                 (1.18, 'crate_break', 'close', 0, {}, 3), (1.48, 'bell_cracked', 'close', -14, {'strike': 'roll'}, 4),
                 (3.4, 'bed_creak', 'close', -4, {}, 5), (4.2, 'bed_creak', 'close', -6, {'kind': 'pat'}, 6),
                 (5.0, 'wood_thud', 'close', -2, {}, 7),
                 (6.2, 'candy_wrapper', 'close', -6, {}, 8), (7.0, 'candy_wrapper', 'close', -8, {}, 9),
                 (8.0, 'footsteps_run', 'far', -6, {'dur': 1.8, 'approach': -1}, 10),
                 (10.3, 'bare_foot_step', 'close', -6, {}, 11), (11.0, 'wet_footstep', 'mirror', -6, {'bare': True}, 12),
                 (11.5, 'wet_footstep', 'mirror', -6, {'bare': False}, 13)], 13.0)
    save('07_foley_crate_bunk_wrapper_run.wav', 'the crate kicked apart (3 kicks) and the bell rolling on the boards, bunk '
         'creak, mattress pat, shoulder into the bunk, candy wrapper, Tess running off, a bare foot, wet prints through '
         'the glass', y, tt)
    # 8 the queen: her line with the queen FX over the mirror room, presence, the bare foot below
    tl = json.load(open(os.path.join(FILM, '_work', 'align', 'timeline.json')))
    l = tl['lines'][97]; l2 = tl['lines'][249]
    vo, _ = sf.read(os.path.join(FILM, '_work', 'align', 'vo_en.wav'), dtype='float32')
    vo = vo if vo.ndim == 1 else vo.mean(1)
    a = vo[int((l['t'] - 0.3) * SR):int((l['end'] + 0.3) * SR)]
    b = vo[int((l2['t'] - 0.3) * SR):int((l2['end'] + 0.3) * SR)]
    v1 = MX.apply_line_fx(np.pad(a, (0, SR * 2)), [(0.3, 0.3 + l['end'] - l['t'], 'queen')])
    v2 = MX.apply_line_fx(np.pad(b, (0, SR * 2)), [(0.3, 0.3 + l2['end'] - l2['t'], 'queen_child')])
    def lev(v):
        return v * 10 ** ((-14 - SX.lufs_int(v)) / 20)
    bed = SX.render('ambience_mirror', 1, 'mirror', dur=11.0)
    y, tt = seq([(0.2, 'queen_presence', 'mirror', -4, {'dur': 1.8}, 1), (4.6, 'queen_presence', 'mirror', -4, {'dur': 2.6}, 2),
                 (8.4, 'bare_foot_step', 'mirror', -4, {}, 3), (9.4, 'bare_foot_step', 'close', -2, {}, 4)], 11.0, bed)
    v = np.zeros(len(y), np.float32)
    v1 = lev(v1); v2 = lev(v2)
    v[int(0.55 * SR):int(0.55 * SR) + len(v1)] += v1[:len(v) - int(0.55 * SR)]
    v[int(4.95 * SR):int(4.95 * SR) + len(v2)] += v2[:len(v) - int(4.95 * SR)]
    y = y + np.stack([v, v], 1)
    save('08_queen_voice_presence_foot.wav', 'the queen: "You have it." (dry + whisper + octave-down whisper + glass '
         'reverb) and "Wait, he forgot his shoe." (Noah\'s voice from her mouth) over the mirror room tone, her presence '
         '(whispers, reversed breath, slowed time shimmer), and her bare foot on the step', y, tt + [[0.85, 'line 97'], [5.25, 'line 249']])
    json.dump(T, open(os.path.join(out, 'tests.json'), 'w'), indent=1)
    with open(os.path.join(out, 'README.txt'), 'w') as f:
        for t in T:
            f.write(f"{t['file']}: {t['desc']}\n")
    sheet(out, T)


def sheet(out, T):
    """Spectrogram contact sheet (log frequency 60 Hz - 16 kHz) with event markers."""
    from PIL import Image, ImageDraw
    import librosa
    W, H = 1600, 150
    im = Image.new('RGB', (W, len(T) * (H + 18)), (0, 0, 0)); d = ImageDraw.Draw(im)
    for k, t in enumerate(T):
        y, sr = sf.read(os.path.join(out, t['file']), dtype='float32'); m = y.mean(1)
        S = np.abs(librosa.cqt(m, sr=sr, hop_length=256, fmin=60, n_bins=96, bins_per_octave=12)) ** 2
        S = 10 * np.log10(S + 1e-12); S = np.clip((S - S.max() + 75) / 75, 0, 1)[::-1]
        rgb = np.stack([S ** 0.8 * 255, S ** 2 * 210, (S ** 0.5) * 110 * (1 - S) + S * 50], -1).astype(np.uint8)
        dur = len(m) / sr; pps = (W - 10) / 20.0
        tile = Image.fromarray(rgb).resize((max(1, int(dur * pps)), H))
        y0 = k * (H + 18) + 18; im.paste(tile, (0, y0))
        for tt, nm in t['events']:
            x = int(tt * pps); d.line([(x, y0), (x, y0 + 8)], fill=(0, 255, 255), width=2)
        d.text((4, y0 - 15), f"{t['file']}  pk {t['peak_dbfs']} dBFS  Mmax {t['mom_max_lufs']}", fill=(255, 255, 255))
    im.save(os.path.join(out, 'tests_sheet.png'))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(FILM, '_work', 'mix', 'tests'))
