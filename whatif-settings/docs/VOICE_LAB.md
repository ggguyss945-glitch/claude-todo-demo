# Voice lab: acted hook voices from stock TTS

The owner asked: *"for voiceovers can you try yourself doing it, exact same quality and emotions as the reference video author did, you can use Fish Audio or any TTS"*.
Fish Audio and Hugging Face are blocked by this container's network policy, so everything here runs locally from stock voices of
commercially usable engines. Nobody can listen inside the container, so every decision below comes from measurements.

RESULTS_PLACEHOLDER

## 1. Targets: what the reference narrator does (measured)

Measured on the reference's vocal stem (UVR separation, Parakeet ASR sentence units, pYIN 65-520 Hz), file
`study/audio/voice_units.json` in the scratch dir. Same pitch-sd definition as ours: standard deviation of
12·log2(F0/median) over the voiced frames of one line.

| voice / register | units | F0 median | within-line pitch sd (median, IQR) | words/s inside units |
|---|---|---|---|---|
| Narrator HYPE (unit median >= 175 Hz) | 56 | 233 Hz | 3.62 st (2.60-4.94) | 2.96 (178 wpm) |
| Narrator DEADPAN (< 145 Hz) | 62 | 120 Hz | 1.95 st (1.33-3.34) | 2.71 (163 wpm) |
| Narrator, all | 130 | 148 Hz | 2.93 st | 2.83 |
| KID | 31 | 328 Hz | 2.08 st | 2.13 |
| DAD | 11 | 140 Hz (bimodal: 111-143 deadpan, 306-376 shocked) | 2.25 st | 3.02 |
| SYSTEM (band-passed, robotic) | 5 | - | 0.40 st | 3.23 |

Whole-video narration: 133 wpm overall, 156 wpm over voiced time, 174 wpm inside sentences; gaps median 0.44 s, none over 1.46 s.
The two-register narrator is the core of the comedy: hype set-ups sit about an octave above the deadpan tags.

## 2. What we tried

Every hook line (S00-L001..S00-L023 and S01-L001; 24 lines, 4 roles) was built with every approach below and scored by the
same measurements (section 3).

| id | approach | what it is |
|---|---|---|
| a1 | Kokoro, plain | role voice (stock pack or blend), speed set from a target rate, text shaping (caps lowered because espeak spells capitals as letters, hype lines end on "!", "..." kept for pauses, respellings like "No un-do.") |
| a2 | Kokoro, phrase split | phrases rendered apart and re-joined with designed pauses (only lines with "..." or two sentences) |
| b_psola | a1 + Praat PSOLA | the line's direction (below) imposed afterwards: PitchTier from the designed F0, DurationTier for lengthening and beats |
| b_world | a1 + WORLD | the same direction, re-synthesised with pyworld (harvest / cheaptrick / d4c, frame time-warp) |
| c_pocket | Pocket TTS zero-shot | Kyutai Pocket TTS (sherpa-onnx export) prompted with our own e_mid takes of the same role, to see whether it transfers the acted style more naturally. Experiment only (licence note in section 7) |
| e_mild / e_mid / e_strong | Kokoro native prosody | the direction rendered by Kokoro's own decoder (below), at 0.85x / 1x / 1.18x contour and 0.75x / 1x / 1.3x accents |
| e_alt | e_mid with the casting runner-up voice | voice check per role, not eligible for the final pick |

### The main idea: "native prosody" (approach e)

Kokoro (StyleTTS2 family, 82 M parameters, Apache-2.0) predicts, for each phoneme, a duration, then an F0 curve (80 frames/s, in Hz)
and an energy curve, and its iSTFTNet decoder renders audio from them. Plain Kokoro sounds flat because those curves are
average: our measurements show every stock male voice reads hype lines at 105-155 Hz, inside the reference's *deadpan* band.

`audio/voice_lab.py` edits the ONNX graph in memory (the model file is untouched):
1. a per-phoneme duration multiplier goes in before the duration rounding (`/encoder/Round`);
2. the F0 and energy tensors (`/encoder/Reshape_output_0`, `/encoder/Reshape_1_output_0`) become outputs of one session and
   replaceable inputs of a second one.

A per-line **direction** (register preset, stressed words with accent sizes, lengthened words, beats after words, final contour)
is turned into new durations and a new F0 curve, and Kokoro's own decoder renders them, so the harmonics stay natural instead of
being bent afterwards. The F0 design, per line:
- keep the predicted intonation's shape, smoothed (30 ms), re-centred on the register's target median and scaled by k around it
  (hype k = 1.45, deadpan k = 0.55), with the fine micro-prosody kept;
- lift creaky dips more than 5 st under the target (Kokoro male voices fry at phrase ends, which inflates pitch sd without sounding lively);
- pitch accents: a raised-cosine peak on the stressed vowel of each stressed word (CAPS words get 4-5 st) with a small dip before it;
- final contour: question rise, exclamation (high then falling), statement fall, suspended "...", a small rise-fall ("Ish"),
  a yawn glide ("Prove it.");
- deadpan: 1.5 st declination over the line and a 2 st final fall; nervous Sam: a 6.5 Hz, 0.25 st tremor;
- loudness accents (+2 dB hype, +3 dB shout) on stressed words after rendering; softer words where the direction says so.

Speed is solved per line from a target rate (hype 172 wpm voiced, deadpan 156, Sam nervous 182, yawn 105...), then beats are set
in frames: "..." 0.42-0.48 s, sentence breaks 0.30-0.36 s, commas 0.16-0.20 s, or the value the direction gives.

### Engine findings worth keeping (each was a measured failure first)
- **Voicing threshold.** The decoder's source treats F0 > 10 Hz as voiced (sines, little noise) and <= 10 Hz as unvoiced (noise).
  Scaling near-zero frames across that line switches a fricative's noise off. The F0 transform keeps every frame's voicing state.
- **Pauses live in the last consonant.** Kokoro parks a pause inside the phoneme before the punctuation (a 0.6 s "s" or "n").
  We clip it to a normal length so the pause sits in the punctuation tokens, where we set it. A raised F0 on a parked final "n" turned
  "SUN?!" into "sun and".
- **Line endings render late.** The last consonant is partly rendered in the frames of the final punctuation token: shortening
  those frames, or even a 3 % F0 change, made ASR hear "planet" for "planet's". Line-final obstruents keep their length and get
  +1.0 log-energy ("crisp consonants"); sibilants get +0.3 everywhere.
- **Pre-voicing.** Before an unvoiced first phoneme ("Who") Kokoro may pre-voice the leading pad; raised to shout pitch it became
  "Oh, who turned on the sun?". The pad before an unvoiced onset is now forced unvoiced.
- **Short lines.** "Ish." and "Prove it." read badly alone (odd style row, stray onset vowel: "I approve it", "Yes, sure").
  They are rendered after a carrier ("Well...", "Okay...") and a 0.6 s beat, and the carrier is cut inside the beat.
- **espeak quirks.** Capitals are spelt as letters (SUN -> "S-U-N"), so caps are lowered and kept only as stress marks; a lone "a" is
  read as the letter name when phonemised alone; "No undo." was heard as "No one do" until respelt "No un-do.".
- **Style halves.** A Kokoro voice vector is 256 numbers: the first 128 drive the decoder (timbre), the last 128 the prosody predictor.
  We can mix them apart (Sam: timbre from a female and a male pack, prosody from the female pack).

RECIPE_PLACEHOLDER

## 6. Files and how to use them

| file | what |
|---|---|
| `audio/voice_lab.py` | the lab and the regenerator. `--hook`, `--ids S00-L006,...`, `--scene S01` regenerate lines with the chosen recipe; `--lab` builds and scores every approach; `--finalize` writes the lab-chosen takes; `--plots`, `--reel` make QA files; `--say "..." --role N --tag HYPE --out x.wav` for an ad-hoc line |
| `audio/voice_ingest.py` | measures, conforms and registers any WAV/MP3 (ours or a Fish take): `python3 -I audio/voice_ingest.py take.wav --id S00-L006 --role SAM --tag nervous --text "In my defense... I only changed ONE thing." --update` |
| `audio/voice_lines.json` | one entry per line: `{id, role, tag, text, file, dur, words:[{w,t,d}], visemes:[[t,name]], metrics, approach}`; times in seconds from the file start |
| `<scratch>/settings/voice/<ID>_<ROLE>.wav` | final takes: 48 kHz mono 24-bit, 30 ms handles, peak <= -1 dBFS, every role at -20 LUFS integrated (dry stems; the mix sets the balance) |
| `<scratch>/settings/voice/lab/` | every candidate (24 kHz) and `lab.json` with all metrics and scores |
| `<scratch>/settings/voice/qa/` | `lab_table.md` (every candidate), `lab_summary.md` (per approach), pitch-contour plots, `hook_voice_reel.wav` (+ cues) |

`<scratch>` = `/tmp/claude-0/-home-user-claude-todo-demo/353ac1d9-152b-55bb-bdf1-0625e0fc6a83/scratchpad`.

**Words.** Parakeet-TDT (sherpa-onnx) token times, aligned to the script words with a sequence match; digits in the ASR output are
spelt out first ("412" -> four hundred twelve); unmatched script words are interpolated; edges are refined on a 10 ms energy mask
(a start never sits in silence, an end never runs into a pause). TDT time steps are 80 ms, so word edges are good to about +-40 ms.
`w` is the script spelling without punctuation.

**Visemes** (production bible 3.2, names from `engine/face.js` VISEMES). RMS at 60 fps and the spectral centroid (80 Hz-5 kHz),
judged as if the line sat at -20 LUFS: below -40 dBFS `v_closed`, -40 to -28 `v_small`, louder with centroid over 1.8 kHz `v_E`,
under 1.15 kHz `v_O`, otherwise `v_A`; the centroid thresholds scale with the speaker's formant spacing (a child's are higher).
Only inside word windows (windows closer than 0.12 s are merged); every shape is held 3-8 frames (short runs merge into the longer
neighbour, long runs alternate with a partner shape: A/O, E/small). Only change points are listed. **`null` means "leave the word
window": fall back to the beat's expression mouth.** The list always ends with `null`.

**Metrics** in each entry: `asr`, `word_acc`, `f0_med`, `f0_p10/p90`, `std_st`, `range_st` (p90-p10), `move_st` (sd of 200 ms
medians), `tail_st` (final slope), `wpm_voiced`, `wpm_span`, `pauses`, `lufs`, `peak_dbfs`, `clipped`, `click_frames`, `hnr_db`,
`jitter_pct`, `shimmer_pct`, `F1-F4`, `formant_dF`, `dnsmos_*`, `spk_sim_role` (mean cosine to the role's other lines, WeSpeaker
ResNet34), `spk_sim_reg` (same register), plus `lab_score` (the selection score) and `lab_alternatives` (every candidate's score).

**Replacing a line with a Fish Audio take** needs nothing else: run `voice_ingest.py <file> --id <ID> --role <ROLE> --tag <tag> --text "<script text>" --update`.
It writes `<scratch>/settings/voice/<ID>_<ROLE>.wav` (conformed the same way) and replaces the entry in `voice_lines.json`; the
animation reads words and visemes from there. Check `word_acc` and `spk_sim_role` in the printout.

LIMITS_PLACEHOLDER
