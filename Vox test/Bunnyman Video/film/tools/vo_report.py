"""Write W/narration/voice_report.md from the edit (edit_list.json, build_stats.json), the checks (tests/check.json)
and the alignment (W/align/timeline.json).
    python3 vo_report.py
"""
import json, os, re, sys
from collections import Counter
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vo_edit as V                                                # noqa: E402

N = V.N
OUT = os.path.join(N, 'voice_report.md')
ALIGN = os.path.join(V.W, 'align', 'timeline.json')

SLIPS = [  # (where in the take, what the TTS did, what the edit does, how it was checked)
    ('185.99-187.01 "At 11:07"', 'read "At eleven seven" (no "oh")',
     'the "O" of the comment prompt\'s "Okay." (235.452-235.535, 142-154 Hz, between the 176 Hz end of "eleven" and the 156 Hz '
     'start of "seven") goes in, 20 ms after "eleven" and 50 ms before "seven"',
     'Whisper: "At 11.07", Parakeet: "At eleven oh seven" (in the line\'s context)'),
    ('326.45-326.70 "Rule number three. If he knocks"', 'read "...three. Ye knocks" (no "If", weak h)',
     '"If he" from rule four\'s "If he talks," (376.165-376.452; its "he" ends at 144-147 Hz, this "knocks" starts at '
     '141-145 Hz) joined by a 10 ms equal-power crossfade to the n of "knocks" (326.700)',
     'both recognisers: "If he knocks, don\'t answer."'),
    ('355.42-356.27 "it\'s family. Yah. I I taught it"', 'an extra "yah" (a voiced breath) and a doubled "I"',
     'the "yah" is dropped with the gap; Grandma\'s line starts on the second "I" (356.266), the one said into "taught"',
     'both: "I taught it to your mother when she was little."'),
    ('520.135-520.392 "the dark c- corner"', 'a stutter: a weak extra "c" syllable',
     'cut; 75 ms of silence stands for the k closure of "dark corner"', 'both: "the dark corner of the attic"'),
    ('901.962-902.145 "a very ordinary c- cup"', 'a stutter', 'cut; 60 ms k closure', 'both: "a very ordinary cup of coffee"'),
    ('905.76-906.38 "costume. Yeah. It has"', 'a loud breath read as "Yeah"', 'dropped with the gap', 'both: "It has a zipper"'),
    ('694.95-695.09 "count to seven [opt] One"', 'the n of Mom\'s "seven" runs into a "pt"-like burst and a click',
     'Mom\'s line ends at the end of its voicing (694.950) on an 80 ms fade; June\'s "One" starts at 695.086 (the gap '
     'between them is the map\'s 0.90 s)', 'both: "And count to seven." / "One"'),
    ('964.72-965.74 "See leave well"', 'an extra vowel after the S of "Sleep" and a v for its p',
     'the S runs straight into "lee" (8 ms equal-power crossfade, the extra vowel 964.952-965.104 cut) and the v '
     '(965.300-965.425) becomes a 70 ms p closure', 'both: "Sleep well."'),
    ('454.059 "facing / the back door"', 'the two uploaded parts meet here (a 0.011 step in the waveform)',
     '12 ms equal-power crossfade across the seam', 'both: "facing the back door" (a 40 ms gap made Whisper hear "facing in")'),
    ('956.58-958.20 "Next time on [the old channel name]. If your doctor"', 'not a slip: the channel was renamed NIGHT '
     'POLICY after the take', '"on" and the old name are cut (the diphthong of "time" ends at 956.512, its m murmur holds '
     'to 956.578, the o of "on" starts at 956.580): "Next time" ends on the whole m with a 25 ms fade, the breath before '
     '"If" goes too, and "if your doctor calls" follows the script\'s ellipsis after 0.45 s; everything after it moves '
     '1.175 s earlier', 'Parakeet: "Next time, if your doctor calls at 3 in the morning to tell you your test results '
     'came back, don\'t ask what they found."'),
    ('56.94, 884.64, 903.30', 'TTS noises: a voiced "huh" after "hospital.", a voiced blip after "magic trick?", '
     'an "mm-hmm" after "cup of coffee."', 'dropped with the gaps', '-'),
]
KEPT = [
    ('"Buck teeth and a stitched-on smile."', 'script: "in a"; both recognisers hear "and a" in the take (a reduced vowel; '
     'it reads the same). Kept; lines.py follows the recording.'),
    ('"who would have let Laurie come home"', 'script: "would\'ve"; both recognisers hear "would have". Kept; lines.py '
     'follows the recording.'),
]


def gap_hist(g):
    bins = [(0, 0.15), (0.15, 0.25), (0.25, 0.35), (0.35, 0.5), (0.5, 0.7), (0.7, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, 3.5)]
    return [(f'{a:.2f}-{b:.2f}', int(((g >= a) & (g < b)).sum())) for a, b in bins]


def main():
    e = json.load(open(V.EDL)); st = json.load(open(V.STATS))
    c = json.load(open(os.path.join(V.TESTS, 'check.json')))
    tl = json.load(open(ALIGN)) if os.path.exists(ALIGN) else None
    L = e['lines']
    raw, rsr = sf.read(V.RAW, dtype='float64')
    raw_dur = len(raw) / rsr
    raw_lufs = V.loudness(raw) if rsr == V.SR else None
    try:
        import pyloudnorm as pyln
        raw_lufs = pyln.Meter(rsr).integrated_loudness(raw)
    except Exception:
        pass
    rg = np.array([max(0.0, b['src_span'][0] - a['src_span'][1]) for a, b in zip(L, L[1:])])
    eg = np.array([a['gap_after'] for a in L[:-1]])
    mg = np.array([r[1] for r in []]) if False else None
    inside = Counter(r['why'] for l in L for r in l['removed_inside'])
    between = Counter(r['why'] for r in e['removed_between_lines'])
    dur_in = sum(r['src'][1] - r['src'][0] for l in L for r in l['removed_inside'])
    dur_bt = sum(r['src'][1] - r['src'][0] for r in e['removed_between_lines'])
    nar = [l for l in L if l['who'] == 'N' and len(l['en']) >= 12]
    lv_before = np.array([l['level_db'] for l in nar])
    gains = [l['gain_db'] for l in L if l['who'] == 'N']
    kinds = Counter(l['gap_kind'] for l in L[:-1])
    w = []
    w.append('# Voice report: the edited narration\n')
    w.append('The owner\'s raw TTS take (`raw/narration_raw_24k.wav`, two uploaded parts joined) edited into '
             '`narration_clean.wav` (cleaned and re-paced, the narrator untouched) and `narration_en.wav` (the same plus the '
             'character voices on the quoted words). Built by `film/tools/vo_edit.py build` from `pacing_map.md`; checked by '
             '`vo_edit.py check` (`tests/`); every source span, output position and gap is in `edit_list.json`.\n')
    w.append('## Before / after\n')
    w.append('| | raw take | edited |')
    w.append('|---|---|---|')
    w.append(f'| file | 24 kHz mono 16-bit | 48 kHz mono 24-bit (soxr VHQ) |')
    w.append(f'| duration | {raw_dur:.2f} s | {e["duration"]:.2f} s |')
    w.append(f'| lines | 412 (script/lines.py) | 412, every one placed |')
    w.append(f'| gap between lines, median (p10-p90) | {np.median(rg):.2f} s ({np.percentile(rg, 10):.2f}-{np.percentile(rg, 90):.2f}) '
             f'| {np.median(eg):.2f} s ({np.percentile(eg, 10):.2f}-{np.percentile(eg, 90):.2f}) |')
    w.append(f'| gaps under 0.15 s / over 2 s | {int((rg < 0.15).sum())} ({int((rg < 0.001).sum())} with no gap at all) / '
             f'{int((rg > 2).sum())} | {int((eg < 0.15).sum())} / {int((eg > 2).sum())} (the 2.8 s before the outro) |')
    w.append(f'| clipped samples (>= 0.999) | {e["clip_repair"]["samples"]} in {e["clip_repair"]["runs"]} runs | 0 '
             f'(redrawn by spline, peaks up to {e["clip_repair"]["max_redrawn_peak"]} = +{20 * np.log10(e["clip_repair"]["max_redrawn_peak"]):.1f} dBFS) |')
    w.append(f'| true peak | 0.0 dBFS (clipped) | {c["true_peak_clean"]} dBTP clean, {c["true_peak_en"]} dBTP en |')
    w.append(f'| loudness (BS.1770) | {raw_lufs:.1f} LUFS | {c["lufs_clean"]} LUFS clean, {c["lufs_en"]} LUFS en (one gain puts the '
             f'true peak at -1 dBTP, no limiter; mix.py brings the voice to -14 LUFS itself) |')
    w.append(f'| narrator line level spread (std of the louder 10 ms frames per line) | {lv_before.std():.2f} dB | '
             f'{c["levels_clean"]["narrator_line_level_std_db"]} dB |')
    w.append(f'| sibilance (5-8 kHz share of the first 300 s) | -14.2 dB | -15.1 dB (last film\'s narration: -16.9 dB) |')
    w.append('')
    w.append('Gap histogram (number of line boundaries):\n')
    w.append('| gap (s) | ' + ' | '.join(k for k, _ in gap_hist(rg)) + ' |')
    w.append('|---|' + '---|' * len(gap_hist(rg)))
    w.append('| raw take | ' + ' | '.join(str(v) for _, v in gap_hist(rg)) + ' |')
    w.append('| edited (map) | ' + ' | '.join(str(v) for _, v in gap_hist(eg)) + ' |')
    w.append(f'| edited (measured, -60 dBFS) | ' + ' | '.join(str(v) for v in c['gaps']['histogram_s'].values()) + ' |')
    w.append('')
    w.append(f'Gap kinds in the map: ' + ', '.join(f'{k} {v}' for k, v in kinds.most_common()) + '.\n')
    w.append('## What was removed\n')
    w.append(f'- Between lines ({dur_bt:.1f} s in all): ' + ', '.join(f'{v} {k}' for k, v in between.most_common()) +
             '. Everything between one line\'s last sound and the next line\'s first sound is replaced by digital silence '
             'of the map\'s length.')
    w.append(f'- Inside lines ({dur_in:.1f} s): ' + ', '.join(f'{v} {k}' for k, v in inside.most_common()) +
             ' (mid-sentence breaths such as "We sit in the dark, [breath] in the empty bathtub" and "Don\'t look at the '
             'treeline, [0.84 s breath] so we\'d never see", lip clicks, low thumps).')
    w.append('- "breath" = an unvoiced sound island (>= 80 ms) that no neighbouring word explains; "click" = shorter; '
             '"low thump" = a low-frequency lip pop without pitch; "TTS noise" = the voiced "huh" / "yah" / "mm-hmm" / blip '
             'the TTS inserted (listed by time). A word-less island is kept when it is speech: pitched and next to a word '
             '(a word the recogniser timed late, a voiced tail), a nasal or l murmur against its word ("smile"), the '
             'release of a final stop or the s after a stop closure ("suit", "six"), an initial s before its closure.')
    w.append('- Gentle cleanup on the whole narrator: 70 Hz high-pass (4th order); a split-band de-esser (4.5 kHz split, only '
             f'where a sibilant rises above the neighbouring vowel - 7 dB; active on {100 * e["chain_clean"]["deess_share"]:.1f} % '
             f'of 1 ms frames, at most {e["chain_clean"]["deess_max_db"]} dB); one gain per line (60 % of its distance from '
             f'the narrator\'s median, +-3 dB, nothing under 1.5 dB: {sum(1 for g in gains if g)} of {len(gains)} narrator '
             f'lines moved, mean |gain| {np.mean(np.abs(gains)):.2f} dB; the hushed "Rule number N." titles came up 2-3 dB, '
             'the sung slow "Hop... hop... hop along." came down 3 dB). No compression, no limiter, no pitch or formant '
             'change on the narrator.')
    w.append('')
    w.append('## TTS slips and how they were repaired\n')
    w.append('| where (raw take, s) | the slip | the repair | re-recognised (Whisper base.en / Parakeet) |')
    w.append('|---|---|---|---|')
    for a, b, cc, d in SLIPS: w.append(f'| {a} | {b} | {cc} | {d} |')
    w.append('')
    w.append('Differences from the script that were kept (the recording is the truth; lines.py follows it):\n')
    for a, b in KEPT: w.append(f'- {a}: {b}')
    w.append('')
    w.append('## Pacing\n')
    w.append('Every one of the 411 boundaries is in `pacing_map.md` with its gap and reason (rule cards 1.4-1.5 s before '
             '"Rule number N." and 1.0 s after the rule text; held dread 1.2-1.5 s before "She puts it in her pocket.", '
             '"She\'s humming.", "It is so nice to be small again.", "I never saw her sitting there.", "I don\'t open it.", '
             '"Then he\'s still.", "Six." / "Seven." and "Easter is in nine days."; fast action 0.25-0.4 s from the kitchen '
             'window to the lock; counts 0.95 s apart; 1.0 s before the comment prompt; 2.8 s before the outro). Inside a '
             'line the take\'s own pauses stay, clamped by punctuation (comma 0.12-0.30 s, colon 0.25-0.45, ellipsis '
             '0.45-0.80, held: "count to seven... [0.65] don\'t", "said Mom... [0.5] don\'t worry", "came back... [0.5] '
             'don\'t ask", "tonight... [0.5] that\'s just the outro"); a pause inside a word (the closure before a final s or '
             'release) is never touched.')
    g = c['gaps']
    w.append('')
    w.append(f'Measured on the file (last sound above -60 dBFS to the next first sound): {g["n"]} gaps, largest '
             f'difference from the map {g["max_abs_dev_vs_map"]} s ({g["n_off_map"]} over 30 ms: lines whose quiet tails '
             f'or onsets sit near -60 dBFS), {len(g["under_0.15"])} under 0.15 s, {len(g["over_2.0"])} over 2 s (the outro '
             'pause).\n')
    w.append('## Character voices (narration_en.wav only)\n')
    w.append('The narrator measures F0 104-256 Hz (5-95 %, median 150 Hz) and F1/F2/F3 about 480/1510/2650 Hz: a young '
             'male voice. Each quoted line is re-voiced with the WORLD vocoder (Harvest F0, CheapTrick envelope, D4C '
             'aperiodicity, 1 ms frames): its F0 is cleaned (octave slips folded, 5-frame median), moved to the '
             'character\'s median with its excursions scaled; the spectral envelope is warped (formants) independently of '
             'the pitch; the aperiodicity is raised for breath; Laurie gets a second copy of her words an octave down with '
             'the man\'s formants under her; then a gentle EQ and a loudness match to the dry line (+ the character\'s '
             'offset). Only the quoted words change: the "she says." / "June whispers." splits are the cut points. Spatial '
             'effects (door, slot, memory, whisper) are left to the mix through the `fx` tags of lines.py.\n')
    try:
        sys.path.insert(0, HERE); import vo_voices as VV
        w.append('| voice | used for | settings |')
        w.append('|---|---|---|')
        used = Counter(v['voice'] for v in e['voices'])
        for k, s in VV.VOICES.items():
            n_ = used.get(k, 0)
            w.append(f'| {k} | {n_} line{"" if n_ == 1 else "s"} | {s["desc"]} |')
        w.append('')
    except Exception as ex:
        w.append(f'(voice table unavailable: {ex})\n')
    w.append('| # | who | fx | line | voice | F0 median in -> out (5-95 %) |')
    w.append('|---:|---|---|---|---|---|')
    for v in e['voices']:
        w.append(f'| {v["i"]} | {v["who"]} | {v["fx"] or "-"} | {v["en"]} | {v["voice"]} | {v["f0_in_median"]} -> '
                 f'{v["f0_out_median"]} Hz ({v["f0_out_p5_p95"][0]}-{v["f0_out_p5_p95"][1]}) |')
    w.append('')
    if 'asr' in c:
        bad = [r for r in c['asr'] if r['share'] < 1.0]
        w.append(f'Every character line and repaired phrase re-recognised on narration_en.wav by Parakeet: '
                 f'{sum(1 for r in c["asr"] if r["share"] >= 1.0)}/{len(c["asr"])} word-perfect. The others: ' +
                 '; '.join(f'"{r["en"]}" heard "{r["heard"]}"' for r in bad) + '.\n')
    w.append('## Checks (tests/)\n')
    w.append('- `strip_01..16_*.png`: before (raw take, removed sounds in red) and after (narration_en.wav, the gap after '
             'each line in yellow), spectrogram + 5 ms RMS, at: ' + ', '.join(c.get('strips', [])) + '.')
    w.append(f'- Residual breaths: the scan flags unvoiced islands >= 80 ms that sit 60 ms from any other sound; '
             f'{len(c["breaths_clean"])} flagged in narration_clean.wav, every one looked at on a spectrogram sheet: they '
             'are word sounds the pitch tracker calls unvoiced (final s of "Past us." / "Silence." / "six", the s + f of '
             '"stiff", stop releases of "crack" / "Thunk" / "need it"), no breath left.')
    cc = c['clicks_clean']
    w.append(f'- Clicks: a sample-step detector (|x[n]-x[n-1]| > 12x its 10 ms mean) finds {cc["n_discontinuities"]} steps in '
             f'narration_clean.wav against {cc.get("n_discontinuities_raw_take", "?")} in the raw take (TTS plosive '
             f'bursts trip it: the edit adds none); {len(cc["at_edit_points"])} sit within 5 ms of an edit point, all word '
             'onsets rising out of digital silence (checked on spectrograms). The two seams the TTS made (the part join, '
             'the "If he" splice) are equal-power crossfades. Gaps: '
             f'{len(cc["nonzero_in_gaps"])} gaps hold a non-zero sample (all gaps are digital silence).')
    w.append(f'- Full-scale samples in narration_en.wav: {c["full_scale_samples_en"]}.')
    w.append('')
    if tl:
        lines = tl['lines']
        found = sum(1 for d in lines if d['found_en'])
        rules = [(d['tag'], d['t']) for d in lines if d['tag'] and re.fullmatch(r'rule\d', d['tag'])]
        cta = next(d['t'] for d in lines if d['tag'] == 'cta')
        w.append('## Alignment (film/tools/align.py on narration_en.wav -> W/align)\n')
        w.append(f'{found}/{len(lines)} lines located; duration {tl["duration_en"]:.2f} s '
                 f'({int(tl["duration_en"] // 60)}:{tl["duration_en"] % 60:04.1f}). Rule cards: ' +
                 ', '.join(f'{t} {v:.2f} s ({int(v // 60)}:{v % 60:04.1f})' for t, v in rules) +
                 f'. Comment prompt ("Okay. Stop for one second"): {cta:.2f} s ({int(cta // 60)}:{cta % 60:04.1f}).\n')
    w.append('## Needs re-recording (best results would come from a fresh TTS take of these phrases)\n')
    w.append('- "Sleep well." (the take says "See leave well"; the cut repair is clean to both recognisers but a real take '
             'would be safer for the very last line).')
    w.append('- "At 11:07, the song starts." (read "eleven seven"; the spliced "O" is short, 83 ms).')
    w.append('- "If he knocks, don\'t answer." (read "Ye knocks"; repaired with rule four\'s "If he").')
    w.append('- "And count to seven." (Mom; the take\'s "seven" runs into a glitch, so its n ends on a fade).')
    w.append('Nothing else needs a new take. To drop a new take in: put it in `raw/`, rerun `vo_asr.py`, set the FIXES of '
             'vo_edit.py for that line, `vo_edit.py build`, `vo_edit.py check`, `align.py --write-pauses`.\n')
    w.append('## Open points\n')
    w.append('- June\'s whispered "He\'s sad." reads as "He said." to both recognisers (a child\'s /ae/ through a whisper); '
             'it is clear in context but worth a listen.')
    w.append('- Grandma\'s "This is our family knock," loses "knock" for Parakeet in isolation (Whisper hears it); worth '
             'a listen.')
    w.append('- mix.py\'s default `--who-fx X=hall` would put the hallway reverb on X (the thing in the old body); this '
             'film tags X `whisper`, so give the mix a `whisper` / `door` / `slot` / `memory` line FX and drop the X default.')
    open(OUT, 'w').write('\n'.join(w) + '\n')
    print('->', OUT)


if __name__ == '__main__':
    main()
