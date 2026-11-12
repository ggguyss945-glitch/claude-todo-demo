"""Measure a mix of this film (mix.py output dir; the dummy film, built on the delivery film's) against the final-mix
targets and list misfires.

    python3 audio/measure_mix.py _work/mix/final [--cues _work/cues] [--mix mix.wav] [--no-cues] [--plot]   (from film/)

Reads <dir>/<mix> (mix.wav, else mix_en.wav), <dir>/stems/{voice_en,music,sfx}.wav (float, final gain, before the
limiter; mix.py writes them unless --no-stems), <dir>/mix_report.json and the cue sheets. Loudness is BS.1770 with
per-channel K-weighting (sfx.py helpers). "rel voice" = relative to the voice stem's integrated loudness.
Writes <dir>/measure.json and prints a summary.

Targets (the job, ARCHITECTURE.md, analysis/AUDIO_SPEC.md)
    master        -14 LUFS integrated (+-0.3), true peak <= -1.0 dBTP (mix.py aims at -1.5)
    voice clear   during speech the bed (music + SFX) stays under the voice: per 400 ms block, voice minus bed;
                  also the same margin in the 1-4 kHz intelligibility band. Weak spots are listed with times.
    music         under the voice the whole time except the authored silences (+ 4 s re-entry) and the last 2 s:
                  music holes = >= 1.5 s with the music under voice - 32 LU (400 ms, 1 s smoothed) are listed
    SFX           every one-shot cue is re-rendered exactly as mix.py renders it (same order, seeds, resolve,
                  spaces) and checked: renders silent, transient off the cue (> 40 ms, slow-onset names excepted),
                  masked (cue more than 18 LU under the voice + music at its loudest moment, in 400 ms and in 100 ms
                  windows: a click is flagged only when it is buried in both), over the voice (a
                  non-hit cue within 1 LU of the narration's integrated loudness while it speaks), thin on a phone (< -15 dB of its
                  loudness above 300 Hz). Flags go to measure.json 'cue_flags'.
    events        hits / silences / one-shot cues per minute, hit peak over the voice, silence depth
"""
import argparse, json, os, sys, time
import numpy as np, soundfile as sf
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sfx as SX                                  # noqa: E402
import mix as MX                                  # noqa: E402

SR = 48000
HOP = 0.05
SLOW_ONSET = ('breath', 'mom_breath', 'mom_sob', 'phone_vibrate', 'curtain_flutter', 'cloth_rustle', 'tinnitus', 'riser',
              'whoosh', 'door_creak', 'box_creak', 'box_scrape', 'van_pull_away', 'window_slide', 'heartbeat', 'car_pass',
              'typing', 'stylus_scribble', 'clock_tick', 'chain_lock', 'van_door_slide', 'glitch', 'footsteps_porch',
              'footsteps_wood_inside', 'footsteps_stairs', 'footsteps_hall', 'paper', 'crowd_whisper', 'siren_far',
              # the dummy film: swells, slides, waves and creaks have no single transient
              'wood_creak', 'velvet', 'spoon_stir', 'hand_slot', 'studio_laugh', 'applause', 'owen_cry', 'owen_giggle',
              'tv_on', 'vcr', 'lamp_flicker', 'paper_slide', 'case_lid', 'glove_lift', 'sip', 'snort', 'heart_monitor',
              'tape_glitch', 'winks_laugh', 'tiny_steps', 'keys_jangle', 'hand_squeeze', 'mom_scream', 'tv_voice',
              'clock_chime', 'rule_lie', 'monitor_flatline', 'tape_hiss', 'old_clock')
HIT_NAMES = ('impact_hit', 'stinger', 'braam', 'sub_drop', 'goodnight_hit')


def lev(x, win=0.4, hop=HOP):
    return -0.691 + 10 * np.log10(SX._blocks(x, win, hop) + 1e-20)


def pw(L):
    return 10 ** (np.asarray(L) / 10)


def runs(mask, hop, min_len):
    """[(t0, t1)] of True runs at least min_len s long."""
    out = []; i = 0; n = len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]: j += 1
            if (j - i) * hop >= min_len: out.append((round(i * hop, 2), round(j * hop, 2)))
            i = j
        else:
            i += 1
    return out


def band_db(x, lo, hi, win=0.4, hop=HOP):
    sos = signal.butter(4, [lo, hi], 'bandpass', fs=SR, output='sos')
    y = signal.sosfilt(sos, x.mean(1) if x.ndim > 1 else x).astype(np.float64) ** 2
    k, h = int(win * SR), int(hop * SR)
    c = np.concatenate([[0.0], np.cumsum(y)])
    i = np.arange(0, len(y) - k + 1, h)
    return 10 * np.log10((c[i + k] - c[i]) / k + 1e-20)


def cue_pass(sfx_cues, voice_m, mus_m, sfx_m, Lv, gdb, n_blocks, line_spans, short=None):
    """Re-render every cue as mix.py does; return per-cue checks and flags."""
    SX.reset()
    order = sorted(range(len(sfx_cues)), key=lambda k: (sfx_cues[k]['t'], k))
    rows, flags = [], []
    g = 10 ** (gdb / 10)                              # power gain of the master on the stems' calibration
    for rank, k in enumerate(order):
        c = sfx_cues[k]; name0 = c.get('name', '?')
        name, params, note = SX.resolve(name0, c.get('params') or {})
        if name is None:
            flags.append(dict(t=c['t'], name=name0, why='unknown name: skipped by the mix')); continue
        space = c.get('space') or params.pop('space', None); params.pop('space', None)
        if space is not None: space = SX.resolve_space(space, name)
        if name in SX.TIMED: params.setdefault('cue_t', float(c['t']))
        bed = name in SX.BED_BUS or (name in SX.DUR_BEDS and params.get('dur'))
        if bed:
            continue
        try:
            y, pre = SX.render_event(name, seed=int(c.get('seed', rank)), space=space, **params)
        except Exception as e:
            flags.append(dict(t=c['t'], name=name, why=f'render failed: {e!r}'[:120])); continue
        y = y * 10 ** (float(c.get('gain_db', 0.0)) / 20)
        t = float(c['t'])
        pk = float(np.abs(y).max()) if len(y) else 0.0
        row = dict(t=round(t, 3), name=name, space=space, gain_db=c.get('gain_db', 0.0))
        if pk < 10 ** (-60 / 20):
            row['silent'] = True; rows.append(row)
            flags.append(dict(t=t, name=name, why=f'renders silent (peak {20 * np.log10(pk + 1e-12):.0f} dBFS)')); continue
        b = lev(y)                                       # the cue's own 400 ms blocks
        kmax = int(np.argmax(b)); Lc = float(b[kmax]) + gdb
        tl = t - pre + kmax * HOP                        # film time of the cue's loudest block
        j = int(round(tl / HOP))
        if not (0 <= j < n_blocks):
            continue
        Lvh = float(voice_m[j]); Lmh = float(mus_m[j])
        Lmask = 10 * np.log10(pw(Lvh) + pw(Lmh) + 1e-20)
        vs_mask = Lc - Lmask
        if short is not None:                            # clicks / taps: the same in 100 ms windows (a tap just
            vs_, ms_ = short                             # before a line stands out of the gap, not of the line)
            b1 = lev(y, 0.1); k1 = int(np.argmax(b1)); j1 = int(round((t - pre + k1 * HOP) / HOP))
            if 0 <= j1 < len(vs_):
                m1 = 10 * np.log10(pw(vs_[j1]) + pw(ms_[j1]) + 1e-20)
                vs_mask = max(vs_mask, float(b1[k1]) + gdb - m1)
        on = SX.onset_s(y, -12) - pre
        ph = SX.mom_max(SX.hp(SX.hp(y, 300, 2), 300, 2)) - SX.mom_max(y)
        speaking = any(a - 0.05 <= tl <= e_ + 0.05 for a, e_ in line_spans)
        row.update(L_rel_voice=round(Lc - Lv, 1), voice_here=round(Lvh - Lv, 1), music_here=round(Lmh - Lv, 1),
                   vs_mask=round(vs_mask, 1), onset_ms=round(1000 * on), phone_db=round(ph, 1), speaking=speaking)
        rows.append(row)
        why = []
        if abs(on) > 0.04 and name not in SLOW_ONSET and not (params.get('dur') or 0) > 1.0 \
                and not params.get('jingle'):                # keys_drop jingle=True: the hand jingle comes first
            why.append(f'transient {1000 * on:+.0f} ms off the cue')
        if vs_mask < -18:
            why.append(f'masked: {vs_mask:.1f} LU under voice + music there')
        if speaking and name not in HIT_NAMES and Lc - Lv > -1.0:
            why.append(f'{Lc - Lv:+.1f} LU rel the narration (integrated) while it speaks')
        if ph < -15 and name != 'sub_drop':              # a sub drop is sub by design (its impact carries the phone)
            why.append(f'thin on a phone ({ph:.1f} dB above 300 Hz)')
        if why:
            flags.append(dict(t=round(t, 3), name=name, space=space, gain_db=c.get('gain_db', 0.0), why='; '.join(why)))
    return rows, flags


def plot(path, dur, Lv, vm, mm, sm, sil, hits, rules, row_s=110.0):
    """Loudness map (cv2): one row per row_s seconds; voice white, music blue, SFX orange (400 ms momentary, LU rel the
    voice's integrated level, -40..+10), authored silences shaded red, hits as yellow ticks, rule cards as green ticks."""
    import cv2
    W_, H_ = 1800, 150; rows = int(np.ceil(dur / row_s))
    img = np.full((rows * H_ + 30, W_ + 60, 3), 18, np.uint8)
    y_of = lambda L: int(np.clip((10 - L) / 50.0, 0, 1) * (H_ - 20)) + 10
    for r in range(rows):
        oy = 30 + r * H_; t0 = r * row_s
        x_of = lambda t: 50 + int((t - t0) / row_s * W_)
        for a, b in sil:
            if b > t0 and a < t0 + row_s:
                cv2.rectangle(img, (x_of(max(a, t0)), oy + 10), (x_of(min(b, t0 + row_s)), oy + H_ - 10), (40, 30, 90), -1)
        for L, c in ((0, (90, 90, 90)), (-13, (60, 60, 60)), (-32, (60, 60, 60))):
            cv2.line(img, (50, oy + y_of(L)), (50 + W_, oy + y_of(L)), c, 1)
        for x_, c in ((hits, (0, 220, 255)), (rules, (60, 220, 60))):
            for h in x_:
                if t0 <= h < t0 + row_s:
                    cv2.line(img, (x_of(h), oy + 8), (x_of(h), oy + 22), c, 2)
        for arr, c in ((mm, (255, 150, 60)), (sm, (40, 140, 255)), (vm, (235, 235, 235))):
            i0, i1 = int(t0 / HOP), min(len(arr), int((t0 + row_s) / HOP))
            if i1 <= i0: continue
            pts = np.array([[x_of(i * HOP), oy + y_of(arr[i] - Lv)] for i in range(i0, i1)], np.int32)
            cv2.polylines(img, [pts], False, c, 1, cv2.LINE_AA)
        cv2.putText(img, f'{int(t0)}s', (4, oy + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    cv2.putText(img, 'voice white / music blue / SFX orange (LU rel voice, +10..-40; lines at 0, -13, -32); silences red; '
                'hits yellow; rule cards green', (50, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1)
    cv2.imwrite(path, img)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dir'); ap.add_argument('--cues', default=None); ap.add_argument('--mix', default=None)
    ap.add_argument('--timeline', default=None); ap.add_argument('--no-cues', action='store_true')
    ap.add_argument('--plot', action='store_true', help='also write <dir>/measure_plot.png (loudness map)')
    A = ap.parse_args()
    T0 = time.time()
    W = os.path.normpath(os.path.join(HERE, '..', '_work'))
    cues_dir = A.cues or os.path.join(W, 'cues')
    tl = json.load(open(A.timeline or os.path.join(W, 'align', 'timeline.json')))
    mixname = A.mix or ('mix.wav' if os.path.exists(os.path.join(A.dir, 'mix.wav')) else 'mix_en.wav')
    rd = lambda p: sf.read(p, dtype='float32', always_2d=True)[0]
    mix = rd(os.path.join(A.dir, mixname))
    v = rd(os.path.join(A.dir, 'stems', 'voice_en.wav')); m = rd(os.path.join(A.dir, 'stems', 'music.wav'))
    s = rd(os.path.join(A.dir, 'stems', 'sfx.wav'))
    rep = json.load(open(os.path.join(A.dir, 'mix_report.json')))
    gdb = float(rep['langs']['en']['master_gain_db'])
    n = min(len(mix), len(v), len(m), len(s)); mix, v, m, s = mix[:n], v[:n], m[:n], s[:n]
    bed = m + s
    dur = n / SR; mins = dur / 60
    Lv = SX.lufs_int(v); Lmix = SX.lufs_int(mix)
    R = {'file': os.path.join(A.dir, mixname), 'duration_s': round(dur, 2),
         'mix_lufs': round(Lmix, 2), 'true_peak_dbtp': round(MX.true_peak(mix), 2),
         'sample_peak_dbfs': round(float(20 * np.log10(np.abs(mix).max() + 1e-12)), 2),
         'voice_rel_mix': round(Lv - Lmix, 2), 'music_rel_voice': round(SX.lufs_int(m) - Lv, 2),
         'sfx_rel_voice': round(SX.lufs_int(s) - Lv, 2), 'bed_rel_voice': round(SX.lufs_int(bed) - Lv, 2),
         'cues_sha1_match': rep.get('cues_sha1') == MX.cue_hashes(cues_dir)}
    st3 = lev(mix, 3.0, 1.0); st3 = st3[st3 > -70]
    R['mix_lra_lu'] = round(float(np.percentile(st3, 95) - np.percentile(st3, 10)), 1)
    mi = lev(mix) - Lmix
    R['mix_momentary_max_over_int'] = round(float(mi.max()), 1)
    R['mix_momentary_max_at_s'] = round(float(np.argmax(mi) * HOP), 2)

    # ---------------- voice clarity: per 400 ms block during speech, voice minus bed
    vm, mm, sm, bm = lev(v), lev(m), lev(s), lev(bed)
    nb = min(len(vm), len(mm), len(sm), len(bm)); vm, mm, sm, bm = vm[:nb], mm[:nb], sm[:nb], bm[:nb]
    tb = np.arange(nb) * HOP + 0.2
    lines = [(l['t'], l['end']) for l in tl['lines']]
    inline = np.zeros(nb, bool)
    for a, e in lines:
        inline |= (tb >= a + 0.1) & (tb <= e - 0.1)
    speech = inline & (vm > Lv - 18)
    marg = vm - bm
    R['narration_share_pct'] = round(100 * float(speech.mean()), 1)
    R['voice_minus_bed_speech_LU'] = {'p1': round(float(np.percentile(marg[speech], 1)), 1),
                                      'p5': round(float(np.percentile(marg[speech], 5)), 1),
                                      'p50': round(float(np.median(marg[speech])), 1),
                                      'under_6LU_pct': round(100 * float((marg[speech] < 6).mean()), 2),
                                      'under_3LU_pct': round(100 * float((marg[speech] < 3).mean()), 2),
                                      'under_0LU_pct': round(100 * float((marg[speech] < 0).mean()), 2)}
    vb, bb = band_db(v, 1000, 4000), band_db(bed, 1000, 4000)
    k = min(len(vb), nb); mb = (vb[:k] - bb[:k])[speech[:k]]
    R['voice_minus_bed_1k4k_speech_dB'] = {'p1': round(float(np.percentile(mb, 1)), 1), 'p5': round(float(np.percentile(mb, 5)), 1),
                                           'p50': round(float(np.median(mb)), 1), 'under_6dB_pct': round(100 * float((mb < 6).mean()), 2)}
    weak = runs(speech & (marg < 4), HOP, 0.15)
    wk = []
    for a, b in weak:
        i0, i1 = int(a / HOP), int(b / HOP)
        who = 'music' if np.max(mm[i0:i1]) >= np.max(sm[i0:i1]) else 'sfx'
        wk.append({'t0': a + 0.2, 't1': b + 0.2, 'min_margin_LU': round(float(marg[i0:i1].min()), 1), 'louder_part': who})
    R['voice_weak_spots'] = sorted(wk, key=lambda x: x['min_margin_LU'])[:25]

    # ---------------- music presence outside the authored silences
    mc = json.load(open(os.path.join(cues_dir, 'music_cues.json')))
    sil = [e for e in mc['events'] if e['type'] == 'silence']
    insil = np.zeros(nb, bool)
    for e in sil:
        insil |= (tb >= e['t'] - 0.2) & (tb <= e['t'] + float(e.get('len', 1.4)) + 4.0)
    tail = tb > dur - 2.5
    ms = np.convolve(mm, np.ones(20) / 20, 'same') - Lv           # 1 s smoothed
    out_ = ~insil & ~tail & (tb > 0.5)
    for thr in (-26, -32, -38):
        R[f'music_over_{-thr}LU_under_voice_pct_outside_silences'] = round(100 * float((ms[out_] > thr).mean()), 1)
    holes = runs(out_ & (ms < -32), HOP, 1.5)
    R['music_holes'] = [{'t0': a + 0.2, 't1': b + 0.2,
                         'music_min_rel_voice': round(float(ms[int(a / HOP):int(b / HOP)].min()), 1)} for a, b in holes]
    R['music_present_pct_K400'] = {f'>{r}LU': round(100 * float((ms > r).mean()), 1) for r in (-20, -26, -32)}
    # silences: music depth vs the 1.5 s before
    dep = []
    for e in sil:
        a, b = int(e['t'] / HOP), int((e['t'] + float(e.get('len', 1.4))) / HOP)
        if a > 40 and b > a + 4 and b < nb:
            dep.append(round(float(np.mean(mm[a - 35:a - 5]) - np.mean(mm[a + 2:b])), 1))
    R['silences'] = {'n': len(sil), 'per_min': round(len(sil) / mins, 2),
                     'depth_db_p50': round(float(np.median(dep)), 1) if dep else None,
                     'shallow_lt8dB': [round(e['t'], 2) for e, d_ in zip(sil, dep) if d_ < 8]}

    # ---------------- bed shape
    b3 = lev(bed, 3.0, 1.0) - Lv; live = b3[b3 > -60]
    R['bed_st3_p10_p50_p90'] = [round(float(np.percentile(live, q)), 1) for q in (10, 50, 90)]
    R['bed_lra'] = round(float(np.percentile(live, 95) - np.percentile(live, 10)), 1)
    q = n // 4
    R['music_by_quarter_rel_voice'] = [round(SX.lufs_int(m[i * q:(i + 1) * q]) - Lv, 1) for i in range(4)]
    R['bed_by_quarter_rel_voice'] = [round(SX.lufs_int(bed[i * q:(i + 1) * q]) - Lv, 1) for i in range(4)]
    R['loudest_10s_bed_at_s'] = int(np.argmax(lev(bed, 10.0, 1.0)))
    x = bed.mean(1)[::2]
    f, P = signal.welch(x, SR / 2, nperseg=8192); tot = P.sum()
    R['bed_spectrum_pct'] = {'<250': round(100 * P[f < 250].sum() / tot, 1),
                             '250-4k': round(100 * P[(f >= 250) & (f < 4000)].sum() / tot, 1),
                             '>4k': round(100 * P[f >= 4000].sum() / tot, 1)}
    try:
        import music_plan as MP
        tm = MP.track_map(tl['lines'])
        secs = []
        for i_, x_ in enumerate(tm):
            a = float(x_['t0']); b = float(tm[i_ + 1]['t0']) if i_ + 1 < len(tm) else dur
            ia, ib = int(a * SR), int(min(dur, b) * SR)
            secs.append([round(a, 1), round(b, 1), str(x_.get('slug', x_.get('track', '?')))[:24],
                         round(SX.lufs_int(m[ia:ib]) - Lv, 1), round(SX.lufs_int(bed[ia:ib]) - Lv, 1)])
        R['sections_music_bed_rel_voice'] = secs
    except Exception as e:
        R['sections_music_bed_rel_voice'] = repr(e)[:120]

    # ---------------- events
    sc = json.load(open(os.path.join(cues_dir, 'sfx_cues.json')))
    hits = sorted({round(c['t'], 2) for c in sc if c['name'] in HIT_NAMES} |
                  {round(e['t'], 2) for e in mc['events'] if e['type'] in ('hit', 'stinger', 'braam', 'sub_drop')})
    hp_ = []
    for h in hits:
        i = int(h / HOP)
        if i + 12 < nb:
            hp_.append(float(bm[i:i + 12].max() - Lv))
    R['events'] = {'hits_per_min': round(len(hits) / mins, 2),
                   'hit_peak_rel_voice_p50_max': [round(float(np.median(hp_)), 1), round(float(np.max(hp_)), 1)] if hp_ else None,
                   'one_shot_cues_per_min': round(sum(1 for c in sc if c['name'] not in SX.BED_BUS) / mins, 1),
                   'rule_stings': sum(1 for e in mc['events'] if e['type'] == 'rule')}

    # ---------------- every SFX cue, re-rendered as mix.py renders it
    if not A.no_cues:
        tc = time.time()
        rows, flags = cue_pass(sc, vm, mm, sm, Lv, gdb, nb, lines, short=(lev(v, 0.1), lev(m, 0.1)))
        R['cues_checked'] = len(rows)
        R['cue_flags'] = flags
        R['cue_seconds'] = round(time.time() - tc, 1)
        json.dump(rows, open(os.path.join(A.dir, 'measure_cues.json'), 'w'), indent=0)
    if A.plot:
        plot(os.path.join(A.dir, 'measure_plot.png'), dur, Lv, vm, mm, sm,
             [(e['t'], e['t'] + float(e.get('len', 1.4))) for e in sil], hits,
             [e['t'] for e in mc['events'] if e['type'] == 'rule'])
    R['seconds'] = round(time.time() - T0, 1)
    json.dump(R, open(os.path.join(A.dir, 'measure.json'), 'w'), indent=1, default=float)
    for k_, v_ in R.items():
        if k_ in ('cue_flags', 'voice_weak_spots', 'sections_music_bed_rel_voice', 'music_holes'):
            continue
        print(f'{k_:44s} {v_}')
    print('music holes (>= 1.5 s under voice - 32 LU, outside silences):', R['music_holes'] or 'none')
    print('voice weak spots (bed within 4 LU of the voice during speech), worst first:')
    for w_ in R['voice_weak_spots'][:12]:
        print('   ', w_)
    print('sections [t0, t1, track, music, bed] rel voice:')
    for r in R['sections_music_bed_rel_voice'] if isinstance(R['sections_music_bed_rel_voice'], list) else []:
        print('   ', r)
    if not A.no_cues:
        print(f'cue flags ({len(R["cue_flags"])} of {R["cues_checked"]} one-shot cues):')
        for f_ in R['cue_flags']:
            print('   ', f_)


if __name__ == '__main__':
    main()
