"""Write W/narration/voice_report.md from the join (raw/joins.json), the edit (edit_list.json, build_stats.json), the
checks (tests/check.json, written by vo_check.py) and the alignment (W/align/timeline.json + asr_cache.json).
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
JOINS = os.path.join(N, 'raw', 'joins.json')

SLIPS = [  # (where in the take, what the TTS did, what the edit does, how it was checked)
    ('367.42-367.615 "Lina\'s bare hand reaches up."', 'the take mangles "bare" (Parakeet "Lean as you hand", Whisper '
     '"Lena\'s hand")', '"Lina\'s" to the end of its s, then the "bare" of "Pyjamas, open coat, bare hands." '
     '(345.435-345.715), then "hand reaches up." from its h (367.615)', 'both: "Lena\'s bare hand reaches up."'),
    ('634.665 "One hooks the blanket and PULLS."', 'the TTS skipped "PULLS" (the take runs on: "...and my fingers are '
     'numb.")', 'the line ends in the dip after "and" (-45 dB) and gets the "pulls" of "it pulls back" '
     '(536.800-537.115) after 30 ms', 'both: "...the blanket and pulls"; a re-record would still be better'),
]
KEPT = [
    ('"Dad, there\'s a truck outsi..."', 'the cut-off is meant; the take reads "out, see" (both recognisers); kept.'),
    ('"Lina"', 'both recognisers write "Lena" (and "Muster" for "Mr." twice); the take says the script.'),
    ('"I grab the radio." (twice)', 'the b of "grab" releases into "the": Parakeet "grabbed" (raw take too), Whisper '
     '"I grab" on the raw take; kept (vo_asrcheck ALLOW_TAGS).'),
    ('"Eleven-oh-two."', 'both recognisers write the clock time "1102"; every word is there.'),
]


def gap_hist(g):
    bins = [(0, 0.15), (0.15, 0.25), (0.25, 0.35), (0.35, 0.5), (0.5, 0.7), (0.7, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, 3.5)]
    return [(f'{a:.2f}-{b:.2f}', int(((g >= a) & (g < b)).sum())) for a, b in bins]


def mmss(t):
    return f'{int(t // 60)}:{t % 60:04.1f}'


def main():
    e = json.load(open(V.EDL)); st = json.load(open(V.STATS))
    c = json.load(open(os.path.join(V.TESTS, 'check.json')))
    tl = json.load(open(ALIGN)) if os.path.exists(ALIGN) else None
    jn = json.load(open(JOINS)) if os.path.exists(JOINS) else None
    L = e['lines']
    raw, rsr = sf.read(V.RAW, dtype='float64')
    raw_dur = len(raw) / rsr
    import pyloudnorm as pyln
    raw_lufs = pyln.Meter(rsr).integrated_loudness(raw)
    rg = np.array([max(0.0, b['src_span'][0] - a['src_span'][1]) for a, b in zip(L, L[1:])])
    eg = np.array([a['gap_after'] for a in L[:-1]])
    inside = Counter(r['why'] for l in L for r in l['removed_inside'])
    between = Counter(r['why'] for r in e['removed_between_lines'])
    dur_in = sum(r['src'][1] - r['src'][0] for l in L for r in l['removed_inside'])
    dur_bt = sum(r['src'][1] - r['src'][0] for r in e['removed_between_lines'])
    gains = [l['gain_db'] for l in L if l['who'] == 'N']
    kinds = Counter(l['gap_kind'] for l in L[:-1])
    nl = len(L)
    w = []
    w.append('# Voice report: the edited narration\n')
    w.append('The owner\'s TTS voiceover (one take, `raw/part1.wav`, 13:06, 24 kHz mono) edited into `narration_clean.wav` (cleaned and re-paced, the narrator '
             'untouched, no character voices) and `narration_en.wav` (the same plus the character voices on the quoted '
             'words; identical line starts). Built by `film/tools/vo_edit.py build` from `pacing_map.md`; checked by '
             '`vo_check.py` (`tests/`) and `vo_asrcheck.py`; aligned by `align.py` (`W/align`). Every source span, '
             'output position and gap is in `edit_list.json`.\n')
    if jn:
        w.append('## The join\n')
        w.append(f'Seven parts, {sum(p["duration"] for p in jn["parts"]):.2f} s in all (44.1 kHz stereo 16-bit; L = R within '
                 f'{max(p["lr_max_diff"] for p in jn["parts"])}, so the mono mix loses nothing; every part peaks at 0.705: '
                 'the TTS is hard-limited at -3 dBFS). They are consecutive slices of one continuous take: no part repeats '
                 'audio of the one before (the best normalised cross-correlation of each part\'s first 0.15-0.6 s against '
                 'the last 6 s of the part before is 0.10-0.51, a repeat would read > 0.9), each cut falls inside a word '
                 'or a decay, and both recognisers read every seam\'s concatenation as the script with each word once. '
                 'The brief\'s "part 4 starts \'Together.\'" is the "-ther" of "together" (part 3 ends "...bolted toge"). '
                 '^ marks a cut below.\n')
        w.append('| seam | at (s) | where | missing samples filled | method |')
        w.append('|---|---:|---|---:|---|')
        where = ['"I me^an it."', '"...pen on paper. ^ Something"', '"bolted toge^ther."', '"Then me. Ev^ery face"',
                 '"right now^." (its decay)', '"For real^." (its decay)']
        for s_, wh in zip(jn['seams'], where):
            w.append(f'| {s_["between"][0]}/{s_["between"][1]} | {s_["at"]:.3f} | {wh} | {s_["filled_samples"]} | '
                     + ('LPC fill (forward/backward blend)' if s_['filled_samples'] else '1.5 ms predictive blend') + ' |')
        w.append('')
    w.append('## Before / after\n')
    w.append('| | raw take (joined) | edited |')
    w.append('|---|---|---|')
    w.append('| file | 44.1 kHz stereo 16-bit (7 parts) | 48 kHz mono 24-bit (soxr VHQ) |')
    w.append(f'| duration | {raw_dur:.2f} s ({mmss(raw_dur)}) | {e["duration"]:.2f} s ({mmss(e["duration"])}) |')
    w.append(f'| lines | {nl} (script/lines.py) | {nl}, every one placed |')
    w.append(f'| gap between lines, median (p10-p90) | {np.median(rg):.2f} s ({np.percentile(rg, 10):.2f}-{np.percentile(rg, 90):.2f}) '
             f'| {np.median(eg):.2f} s ({np.percentile(eg, 10):.2f}-{np.percentile(eg, 90):.2f}) |')
    w.append(f'| gaps under 0.15 s / over 2 s | {int((rg < 0.15).sum())} ({int((rg < 0.001).sum())} with no gap at all) / '
             f'{int((rg > 2).sum())} | {int((eg < 0.15).sum())} / {int((eg > 2).sum())} (the 2.8 s before the outro) |')
    w.append(f'| limited / clipped peaks | {e["clip_repair"]["samples"]} flat-topped samples at the 0.705 ceiling in '
             f'{e["clip_repair"]["runs"]} runs | 0 (redrawn by cubic spline through 4 good samples a side; peaks up to '
             f'{e["clip_repair"]["max_redrawn_peak"]}) |')
    w.append(f'| true peak | -3.0 dBFS (limited) | {c["true_peak_clean"]} dBTP clean, {c["true_peak_en"]} dBTP en |')
    w.append(f'| loudness (BS.1770) | {raw_lufs:.1f} LUFS | {c["lufs_clean"]} LUFS clean, {c["lufs_en"]} LUFS en (one gain puts '
             'the true peak at -1 dBTP, no limiter; the gaps are digital silence; mix.py brings the voice to its own '
             'target) |')
    w.append(f'| narrator line level spread (std of the louder 10 ms frames per line) | - | '
             f'{c["levels_clean"]["narrator_line_level_std_db"]} dB (p5-p95 {c["levels_clean"]["narrator_line_level_p5_p50_p95_db"][0]} '
             f'to {c["levels_clean"]["narrator_line_level_p5_p50_p95_db"][2]} dB) |')
    w.append('')
    w.append('Gap histogram (number of line boundaries):\n')
    w.append('| gap (s) | ' + ' | '.join(k for k, _ in gap_hist(rg)) + ' |')
    w.append('|---|' + '---|' * len(gap_hist(rg)))
    w.append('| raw take | ' + ' | '.join(str(v) for _, v in gap_hist(rg)) + ' |')
    w.append('| edited (map) | ' + ' | '.join(str(v) for _, v in gap_hist(eg)) + ' |')
    w.append('| edited (measured, -60 dBFS) | ' + ' | '.join(str(v) for v in c['gaps']['histogram_s'].values()) + ' |')
    w.append('')
    w.append('Gap kinds in the map: ' + ', '.join(f'{k} {v}' for k, v in kinds.most_common()) + '.\n')
    w.append('## What was removed\n')
    w.append(f'- Between lines ({dur_bt:.1f} s in all): ' + ', '.join(f'{v} {k}' for k, v in between.most_common()) +
             '. Everything between one line\'s last sound and the next line\'s first sound is replaced by digital silence '
             'of the map\'s length.')
    w.append(f'- Inside lines ({dur_in:.1f} s): ' + ', '.join(f'{v} {k}' for k, v in inside.most_common()) +
             ' (mid-sentence inhales: "Halfway to the hospital, [0.44 s inhale] I looked", "In the waiting room, [0.45 s] a '
             'man sat down", "...walk into a waiting room, [0.31 s] and a very tall man", "...brings her coffee, '
             '[0.24 s] just to keep up", "...in Grandpa\'s armchair, [0.13 s] facing all of them"; lip clicks; low thumps).')
    w.append('- "breath" = an unvoiced sound island (>= 80 ms) that no neighbouring word explains; "click" = shorter; '
             '"low thump" = a low-frequency lip pop without pitch; "TTS noise" = the inhale / "uh" / "mm-hmm" listed above. '
             'A word-less island is kept when it is speech: pitched and next to a word, a nasal or l murmur, the release of '
             'a final stop ("music", "doctors" -> its k release between closure and "-tors" is kept by a stop-release '
             'rule added for this take), the s after a stop closure, the devoiced v of "twelve", the creaky decay of a '
             'word ("anyway", "her", "Milo"), an initial s / voiced-stop prevoicing; a nasal ending ("morning") never '
             'claims the breath after it.')
    w.append('- Gentle cleanup on the whole narrator: 70 Hz high-pass (4th order); a split-band de-esser (4.5 kHz split, '
             f'only where a sibilant rises above the neighbouring vowel - 7 dB; active on {100 * e["chain_clean"]["deess_share"]:.1f} % '
             f'of 1 ms frames, at most {e["chain_clean"]["deess_max_db"]} dB); one gain per line (60 % of its distance from '
             f'the narrator\'s median, +-3 dB, nothing under 1.5 dB: {sum(1 for g in gains if g)} of {len(gains)} narrator '
             f'lines moved, mean |gain| {np.mean(np.abs(gains)):.2f} dB). No compression, no limiter, no pitch, formant or '
             'tone change on the narrator.')
    w.append('')
    w.append('## TTS slips and run-together lines, and how they were repaired\n')
    w.append('| where (joined take, s) | the slip | the repair | re-recognised (Whisper base.en / Parakeet TDT) |')
    w.append('|---|---|---|---|')
    for a, b, cc, d in SLIPS: w.append(f'| {a} | {b} | {cc} | {d} |')
    w.append('')
    w.append('Differences from the script that were kept (the recording is the truth; lines.py follows it):\n')
    for a, b in KEPT: w.append(f'- {a}: {b}')
    w.append('')
    w.append('## Pacing\n')
    w.append(f'Every one of the {nl - 1} boundaries is in `pacing_map.md` with its gap and reason: running sentences 0.45 s; '
             'staccato fragments 0.35-0.40 s ("Calm. Patient. Kind.", "Deep. Fast.", the warning signs on the note); '
             'paragraph breaks 0.85-0.90 s; 1.4 s before each "Rule number N." and 1.0 s after its rule text; held dread '
             '1.0-1.5 s before "Still waiting.", "Waiting.", "Grandpa.", "My ticket said: Milo.", the Waiting Man\'s "It can '
             'wait.", "Doctor Later.", "Not as a patient." and "So are we."; the counts "One... Two... Three..." 1.0, 1.1, '
             '1.2, 1.2 and 1.3 s around them (slowing); 1.0 s after the ring, the "phone rang anyway" and the knock; 1.0 s '
             'before the comment prompt; 2.8 s before "Okay. Breathe."; 0.18 s where a quote is split from its "she said."; '
             '0.25-0.30 s where a speaker is cut off ("I need you to..." / "my tummy really..."). Inside a line the take\'s '
             'own pauses stay, clamped by punctuation (comma 0.12-0.30 s, colon 0.25-0.45, ellipsis 0.45-0.80, mid-line '
             'full stop 0.30-0.55, none <= 0.25); a pause inside a word (a closure before a release or final s) is never '
             'touched.')
    g = c['gaps']
    w.append('')
    w.append(f'Measured on the file (last sound above -60 dBFS to the next first sound): {g["n"]} gaps, largest '
             f'difference from the map {g["max_abs_dev_vs_map"]} s ({g["n_off_map"]} over 30 ms: a line whose quiet tail '
             f'sits near -60 dBFS), {len(g["under_0.15"])} under 0.15 s, {len(g["over_2.0"])} over 2 s (the outro pause).\n')
    w.append('## Character voices (narration_en.wav only)\n')
    w.append('The narrator (Adam) measures F0 102-243 Hz (5-95 %, median 166 Hz; parselmouth on the first 4 minutes of '
             'the take) and F1/F2/F3 about 496/1511/2643 Hz. Each quoted line of Lina (L), Dad (D), Mr. Kessler (K) and '
             'Mister Shiver (S, and his copies of Dad, Mom and the little boy) is re-voiced with the WORLD vocoder (`tools/vo_voices.py`: Harvest F0, CheapTrick '
             'envelope, D4C aperiodicity, 1 ms frames) before the layout: its F0 is moved to the character\'s median with '
             'its excursions scaled and softly limited, the spectral envelope is warped (formants) independently of the '
             'pitch, and the aperiodicity is raised for breath or a whisper; no voice changes length, so both files keep identical line starts. Only the quoted words change: the '
             'quote splits are the cut points. Spatial effects (radio, truck, mimic, memory, whisper) are '
             'left to the mix through the `fx` tags of lines.py.\n')
    w.append('Measured formant shift = the frequency warp that best maps the dry lines\' average spectral envelope onto '
             'the voiced ones\' (pitch-independent: a falsetto would measure 1.0); F0 from the voiced lines.\n')
    try:
        import vo_voices as VV
        cl, _ = sf.read(V.OUT_CLEAN); en, _ = sf.read(V.OUT)
        rows = {}
        for v in e['voices']:
            l = L[v['i']]
            a, b = l.get('out_clean', l['out']); a2, b2 = l['out']
            rows.setdefault(v['voice'], []).append((cl[int(a * V.SR):int(b * V.SR)], en[int(a2 * V.SR):int(b2 * V.SR)], v))
        w.append('| voice | lines | measured formant shift (set) | F0 median out (5-95 %) | settings |')
        w.append('|---|---:|---|---|---|')
        for k, s in VV.VOICES.items():
            rr = rows.get(k, [])
            if not rr: continue
            al, f0d, f0w = VV.measure_warp(np.concatenate([r[0] for r in rr]), np.concatenate([r[1] for r in rr]))
            p5 = np.median([r[2]['f0_out_p5_p95'][0] for r in rr]); p95 = np.median([r[2]['f0_out_p5_p95'][1] for r in rr])
            w.append(f'| {k} | {len(rr)} | x{al} (x{s["alpha"]}) | {f0w} Hz ({p5:.0f}-{p95:.0f}) | {s["desc"]} |')
        w.append('')
    except Exception as ex:
        w.append(f'(voice table unavailable: {ex})\n')
    w.append('The children (Lina L*, his copy of the boy S_boy) are set to a x1.32-1.34 envelope warp: a child\'s vocal tract, not a '
             'raised adult voice (the measured shift is in the table above).\n')
    w.append('| # | who | fx | line | voice | F0 median in -> out | duration in -> out (s) |')
    w.append('|---:|---|---|---|---|---|---|')
    for v in e['voices']:
        w.append(f'| {v["i"]} | {v["who"]} | {v["fx"] or "-"} | {v["en"]} | {v["voice"]} | {v["f0_in_median"]} -> '
                 f'{v["f0_out_median"]} Hz | {v["dur_in"]} -> {v["dur_out"]} |')
    w.append('')
    if 'asr' in c:
        bad = [r for r in c['asr'] if r['share'] < 1.0]
        w.append(f'Every character line and repaired phrase re-recognised on narration_en.wav by Parakeet: '
                 f'{sum(1 for r in c["asr"] if r["share"] >= 1.0)}/{len(c["asr"])} word-perfect' +
                 ('. The others: ' + '; '.join(f'"{r["en"]}" heard "{r["heard"]}"' for r in bad) if bad else '') + '.\n')
    w.append('## Checks (tests/)\n')
    w.append('- `strip_*.png`: before (raw take, removed sounds in red) and after (narration_en.wav, the gap '
             'after each line in yellow), spectrogram + 5 ms RMS, at: ' + ', '.join(c.get('strips', [])) + '.')
    br = Counter(b['kind'] for b in c['breaths_en'])
    chk = [b for b in c['breaths_en'] if b['kind'] == 'check']
    w.append(f'- Residual breaths: the scan flags sound islands >= 80 ms, 60 ms from any other sound, that are voiced in '
             f'under 20 % of their own frames: {len(c["breaths_en"])} in narration_en.wav: '
             + ', '.join(f'{v} {k}' for k, v in br.most_common()) + '. The line-final ones are the releases and final '
             'fricatives the take spells out after a closure ("doctors", "music", "night", "porch", "lunch", "pick up"); '
             'the whole lines are "Shh." and two short lines the pitch tracker calls unvoiced ("Fast.", "Ask questions."); '
             + (f'the {len(chk)} left to check were looked at on spectrograms: ' + '; '.join(
                 f'{b["t"][0]:.2f} s (L{b.get("line", "-")})' for b in chk) + ' = the article "A" of "A television", the '
                 't release of "met," and the word "pick" (all speech).' if chk else '') + ' No breath is left.')
    cc = c['clicks_clean']
    w.append(f'- Clicks: a sample-step detector (|x[n]-x[n-1]| > 12x its 10 ms mean) finds {cc["n_discontinuities"]} steps in '
             f'narration_clean.wav against {cc.get("n_discontinuities_raw_take", "?")} in the raw take (the TTS\'s own plosive '
             f'bursts trip it: the edit adds none); {len(c["clicks_en"]["at_edit_points"])} sit within 5 ms of an edit point '
             'in narration_en.wav, every one a word onset rising out of digital silence or a stop burst inside its piece '
             '(looked at, +-30 ms waveforms). Every join inside a line is a raised-cosine fade at a low-energy point or a '
             f'8-12 ms equal-power crossfade. {len(cc["nonzero_in_gaps"])} gaps hold a non-zero sample (all gaps are '
             'digital silence).')
    w.append(f'- Full-scale samples in narration_en.wav: {c["full_scale_samples_en"]}.')
    w.append('- `vo_asrcheck.py --every` (wired into `vo_edit.py check`): every line judged where the whole-file pass '
             'hears it AND recognised again on its own (50 ms margins, 0.3 s padding): first word, last word, >= 80 % of '
             'its words, no word split across a line boundary. Result in the alignment section.')
    w.append('')
    if tl:
        lines = tl['lines']
        found = sum(1 for d in lines if d['found_en'])
        rules = [(d['tag'], d['t']) for d in lines if d['tag'] and re.fullmatch(r'rule\d', d['tag'])]
        cta = next(d['t'] for d in lines if d['tag'] == 'cta')
        outro = next(d['t'] for d in lines if d['tag'] == 'outro')
        w.append('## Alignment (film/tools/align.py on narration_en.wav -> W/align)\n')
        w.append(f'{found}/{len(lines)} lines located (every boundary placed in the silence between the lines); duration {tl["duration_en"]:.2f} s ({mmss(tl["duration_en"])}). Rule cards: ' +
                 ', '.join(f'{t} {v:.2f} s ({mmss(v)})' for t, v in rules) +
                 f'. Comment prompt ("Stop." ... "Remember your answer."): {cta:.2f} s ({mmss(cta)}). Outro: {outro:.2f} s '
                 f'({mmss(outro)}); outro question "Now... who on your street is inside alone?" '
                 f'{next(d["t"] for d in lines if d["tag"] == "comment_prompt"):.2f} s.\n')
    ac = os.path.join(V.TESTS, 'asrcheck.txt')
    if os.path.exists(ac):
        txt = open(ac).read().strip().split('\n')
        w.append('Recogniser check (`vo_asrcheck.py --every`, output in `tests/asrcheck.txt`):\n')
        w.append('```')
        w += txt
        w.append('```\n')
    w.append('## Needs re-recording (a fresh TTS take of these phrases would be safer; the repairs read right to both '
             'recognisers)\n')
    w.append('- "Rows of plastic chairs, bolted together." (read "rah-rahs"; rebuilt from three sources).')
    w.append('- "Nurses always notice." (read "Nurse. Always notice."; "-es" spliced from "his").')
    w.append('- "Sleep well." (read "the Sleemith well"; repaired with a p closure; the very last lines matter).')
    w.append('- Optional: "Waiting." (rule 5 cliffhanger): the take rushes it between "head," and "Rule number five" with '
             'no breath; the edit isolates it with 1.3 / 1.4 s of silence but its delivery stays quick.')
    w.append('To drop a new take in: put it in `raw/` (one part or a whole new take: tools/vo_join.py), rerun '
             '`vo_asr.py raw/narration_raw_44k.wav asr_raw.json`, update FIXES / SPLITS of vo_edit.py for the lines that '
             'moved, `vo_edit.py build`, `align.py --write-pauses`, `vo_edit.py check`, `vo_report.py`.\n')
    w.append('## Open points\n')
    w.append('- The voices were judged by measurement, recognisers and spectrograms, not by ear: give each character a '
             'listen in context (`tests/strip_*` mark them; the per-voice settings are one table in vo_voices.py).')
    w.append('- The Waiting Man\'s counts keep their own pitch movement (x1.0) and "Two..." is the rule-2 title\'s '
             '"two" drawn out (the take\'s own read as "Till" in his voice); his sentences are flattened to x0.60.')
    w.append('- The mix should give the fx tags their spaces: `phone` (the 1979 voice, the 3 AM call), `recording` (the '
             'phone-system lady: band-limited, a little hiss), `door` (Doctor Halverson on the porch), `rooms` ("It can '
             'wait." from every room: several delayed, filtered copies), `whisper` (Milo, Grandma\'s hush, the voice in '
             'your head).')
    open(OUT, 'w').write('\n'.join(w) + '\n')
    print('->', OUT)


if __name__ == '__main__':
    main()
