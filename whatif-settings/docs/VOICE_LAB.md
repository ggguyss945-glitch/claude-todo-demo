# Voice lab: acted hook voices from stock TTS

The owner asked: *"for voiceovers can you try yourself doing it, exact same quality and emotions as the reference video author did, you can use Fish Audio or any TTS"*.
Fish Audio and Hugging Face are blocked by this container's network policy, so everything here runs locally from stock voices of
commercially usable engines. Nobody can listen inside the container, so every decision below comes from measurements.

## Result

All 24 hook lines (S00-L001..S00-L023 and S01-L001; N, SYS, SAM, DAD) are rendered, scored and delivered as
`<scratch>/settings/voice/<ID>_<ROLE>.wav` with words, visemes and metrics in `audio/voice_lines.json`.
Every line passes the checks we can run without ears:
- ASR heard every line word for word. The 1- and 2-word lines pass a robust check: at least half of 6 perturbed decodes are word-perfect. The final "Ish." passes 6 of 6.
- No hype line is under the 2-semitone gate.
- No take clips. Every take has 30 ms handles, a peak ≤ -1 dBFS and every role sits at -20 LUFS (±0.5).
- No F0 discontinuities (pitch jumps of 2.5 st or more between frames, octave errors excluded): 0 in all 24 takes.

**Chosen takes vs plain Kokoro vs the reference** (reference = the reference video's vocal stem measured with the same pitch function, section 1):

| voice | lines | F0 median: plain a1 / ours / reference | pitch sd st: plain / ours / reference | range st: ours / ref | wpm voiced (ours, 3+ word lines) | spk sim within role | DNSMOS ours (plain) | approaches chosen |
|---|---|---|---|---|---|---|---|---|
| N HYPE | 11 | 121 / **213** / 233 | 2.69 / **3.70** / 3.54 | 10.5 / 9.1 | 173 | 0.76 | 2.94 (3.21) | b_psola 3, e_mid 4, e_mild 2, e_strong 2 |
| N DEADPAN | 6 | 120 / **115** / 121 | 2.91 / **2.08** / 2.00 | 5.5 / 4.9 | 153 | 0.71 | 3.15 (3.25) | b_psola 1, e_mid 2, e_mild 3 |
| SYS  | 3 | 167 / **209** / 369 | 2.94 / **1.80** / 1.75 | 4.4 / 4.8 | 167 | 0.83 | 3.31 (3.32) | e_mild 2, e_strong 1 |
| SAM  | 3 | 161 / **283** / 330 | 3.72 / **4.94** / 2.20 | 12.9 / 5.5 | 156 | 0.69 | 2.48 (2.90) | b_psola 1, b_world 1, e_strong 1 |
| DAD  | 1 | 155 / **263** / 140 | 3.82 / **4.15** / 2.42 | 10.2 / 6.3 | 135 | - | 2.66 (2.91) | e_mid 1 |

Pace over the whole hook: 103 words in 38.9 s of speech = **159 wpm over speech** (narrator alone 164) and **151 wpm over
line spans** (first to last voiced frame, so the designed "..." beats count; narrator alone 156). The reference is 156 wpm
"while voiced" (its VAD segments include short in-sentence pauses, so it sits between our two measures) and 174 inside
sentences. Target 150-160: met.

The two-register narrator works by numbers. Hype lines moved from 121 Hz and 2.7 st (plain Kokoro reads them in the reference's
*deadpan* band) to 213 Hz and 3.7 st (reference hype: 233 Hz, 3.54 st). Deadpan lines now sit at 115 Hz and 2.1 st (reference
121 Hz, 2.0 st), so the octave drop the comedy depends on is there. `qa/narrator_register_vs_reference.png` puts every line on
top of the reference's 130 sentence units.

What this does **not** prove: that the takes sound acted to a human. The measures say the melody, register, rate and
intelligibility are where the reference's are. Kokoro's timbre and some PSOLA texture are still synthetic (section 7). Audition
file: `qa/hook_voice_reel.wav` (all 24 takes in script order, cue sheet `qa/hook_voice_reel_cues.txt`).

## 1. Targets: what the reference narrator does (measured)

Measured on the reference's vocal stem (UVR separation, Parakeet ASR sentence units), re-measured with our own pitch function
(`voice_ingest.pitch`: pYIN, 10 ms, gated at -30 dB), so the numbers compare directly with our lines. Pitch sd is the
standard deviation of 12·log2(F0/median) over the voiced frames of one unit; range is p90-p10. Files: `study/audio/voice_units.json`
and `settings/voice/work/ref_units_ourmetric.json` in the scratch dir.

| voice / register | units | F0 median | within-unit pitch sd: median (IQR) | range p90-p10 | words/min inside units | formant spacing dF |
|---|---|---|---|---|---|---|
| Narrator HYPE (unit median >= 175 Hz) | 56 | 233 Hz | 3.54 st (2.56-4.59) | 9.1 st | 178 | 1180 Hz (all narrator) |
| Narrator DEADPAN (< 145 Hz) | 57 | 121 Hz | 2.00 st (1.37-2.87) | 4.9 st | 163 | |
| Narrator, all | 126 | 152 Hz | 2.74 st (mean 2.86) | 7.2 st | 172 | |
| KID | 30 | 330 Hz | 2.20 st (1.63-2.78) | 5.5 st | 129 | 1392 Hz |
| DAD | 10 | 140 Hz (bimodal: deadpan 111-143, shocked 306-376) | 2.42 st | 6.3 st | 177 | 1067 Hz |
| SYSTEM (band-passed, robotic; pitch unreliable) | 4 | 369 Hz | 1.75 st | 4.8 st | 202 | |

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
| c_pocket | Pocket TTS zero-shot | Kyutai Pocket TTS (sherpa-onnx export) prompted with our own e_mid takes of the same role, to see whether it transfers the acted style more naturally. Experiment only (licence note in section 8) |
| e_mild / e_mid / e_strong | Kokoro native prosody | the direction rendered by Kokoro's own decoder (below), at 0.85x / 1x / 1.18x contour and 0.75x / 1x / 1.3x accents |
| e_alt | e_mid with the casting runner-up voice | voice check per role, not eligible for the final pick |

The lab ran twice. The second pass, after the fixes listed below, rebuilt every candidate of every line: 3 parallel runs, then
PSOLA and all of Sam's lines again with the seeded Praat. Section 4 has its numbers. The earlier pass's logs are in
`settings/voice/work/oldlogs/`.

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
  They are rendered after a carrier ("Um..." for "Ish.", "Okay..." for "Prove it.") and a 0.6 s beat, and the carrier is cut inside the beat.
- **espeak quirks.** Capitals are spelt as letters (SUN -> "S-U-N"), so caps are lowered and kept only as stress marks; a lone "a" is
  read as the letter name when phonemised alone; "No undo." was heard as "No one do" until respelt "No un-do.".
- **Style halves.** A Kokoro voice vector is 256 numbers: the first 128 drive the decoder (timbre), the last 128 the prosody predictor.
  We can mix them apart (Sam: timbre from a female and a male pack, prosody from the female pack).

### Findings added in the second lab pass (each one was a measured failure first)
- **Parked pause in the length mark.** In "I AGREE." Kokoro parked a 0.62 s pause inside the 'ː' after the vowel. The pause clip now treats 'ː' as part of the vowel. Before, a held "agreeeee" fell into a 100 Hz creak (19 frames).
- **Line-end fry.** After the last vowel, Kokoro often renders a creaky ~100 Hz hum: 0.3 s of it inside the final 't' of "Prove it.". ASR heard it as an extra syllable ("Prove *of* it"), and it pushed the line's pitch sd to 7.6 st, which looked like acting but was an artefact. Fix: after the last vowel, any voiced frame under 0.62 × the line median is made unvoiced and 4 log-units quieter. Inside a voiceless fricative it is only unvoiced, because that noise is the consonant. A new metric, `fry_tail` (half-pitch frames at the end of the line), is scored as a penalty from 9 frames up.
- **Carrier lines and the register.** For "Ish." and "Prove it." the register was centred on the whole render, carrier phrase included, and "Ish" sat 4 st under Sam's register. The median is now taken over the line's own words only.
- **Plain take of a carrier line.** The plain a1 take was cut at the designed time and lost the word. It is now cut on its own durations.
- **One-word ASR is a coin flip.** A single Parakeet decode of "Ish." changed with 30 ms of extra lead silence ("Ish", "Is", "Yes", "This", or nothing). For 1-2 word lines, intelligibility is now `asr_hits`: the share of 6 decodes (lead 0.1/0.25/0.5 s × gain 0/-6 dB) that are word-perfect, measured on the *conformed* audio. "Ish." is the hardest word in the hook. With the carrier "Um..." and the vowel lengthened ×1.5, the b_psola take gets 6/6. Every e take of "Ish" gets 0/6, for every carrier, length and contour we tried.
- **Reproducibility.** Praat places PSOLA pulses in unvoiced stretches at random, so two renders of the same line differed by up to 0.3 in amplitude (correlation 0.96-0.98). `praat_seed()` now fixes Praat's generator before each PSOLA and 'Change gender' call. Separately, onnxruntime with 4 threads sums in a different order than with 1, which can flip Kokoro's duration rounding. The engine now defaults to `VOICE_THREADS=1`. With both, `--hook` reproduces all chosen takes sample for sample (checked on 7 lines; the maximum difference is the 16-bit step).

## 3. How a take is scored

Every candidate is measured by `voice_ingest.measure` (Parakeet-TDT ASR, pYIN pitch, VAD rate, DNSMOS P.835, Praat HNR,
jitter and shimmer, spectral-click count, F0 jumps, formants, a WeSpeaker ResNet34 speaker embedding), then scored by
`voice_lab.score`. Each sub-score runs from 0 to 1:
- **register** = exp(-(d/3)²), where d is the distance in semitones from the line median to the register target (narrator hype 205 Hz, deadpan 112 Hz, SYS 200/238 Hz, Sam 250-295 Hz, Dad shout 265 Hz).
- **movement** depends on the register:
  - hype-like lines: min(1, sd/3.54), where 3.54 st is the reference hype median; it decays above 6.5 st (over-acted or tracking trouble);
  - deadpan: peaks at sd 2.0 st (the reference deadpan), width 1.3;
  - calm SYS: peaks at 1.6 st.
- **rate** = exp(-((wpm - target)/(0.22·target))²). It is used only for lines of 3 or more words.
- **quality** = (DNSMOS overall - 2.4)/1.0, clipped to 0..1.
- **intel** = 1 if ASR is word-perfect, else accuracy - 0.3. For 1-2 word lines it is `asr_hits` instead.
- **consistency** = (cos - 0.55)/0.35, clipped, where cos is the cosine to the role/register centroid of the e_mid takes.

**total** = 0.35 · (0.55 register + 0.45 movement) + 0.30 quality + 0.15 rate + 0.20 intel + 0.10 consistency - penalties.

**Penalties** are all relative to the plain take of the same line:
- 0.04 per extra F0 jump;
- 0.03 per extra click frame beyond 2;
- 0.08 per dB of HNR lost beyond 1.5 dB (roughness from PSOLA or WORLD);
- 0.5 for any clipping;
- 0.015 per fry-tail frame beyond 8.

**Gates** subtract 1.0: a hype-like line (narrator hype, cheerful, nervous, shouting) of 3 or more words under 2.0 st pitch sd, or ASR accuracy under 0.75 (under 0.5 hits for 1-2 word lines).

**Pick**: the best licence-clean candidate. c_pocket (licence) and e_alt (a different voice) are measured but never picked.
Because DNSMOS and pYIN are noisy at about the 0.05 level and the native render is the regenerable house recipe, a post-processed
or plain take must beat the best e take by more than 0.05 to win.

## 4. Results per approach

The rows in bold are the reference measured with the same functions. "Wpm span" includes the designed pauses. Mean score is
over the group's lines. "Chosen" counts how many lines each approach won.

| group | approach | lines | F0 median Hz | pitch sd st (median) | range p90-p10 st | wpm voiced (median) | wpm span | ASR word-perfect | DNSMOS | HNR dB | fry tail frames (mean) | mean score | chosen |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **N/HYPE** | reference narrator, hype units | 56 | 233 | 3.54 | 9.1 | - | 178 | - | - | - | - | - | - |
| N/HYPE | a1 | 11 | 121 | 2.69 | 7.1 | 167 | 167 | 10/11 | 3.21 | 10.1 | 0.0 | 0.66 | 0 |
| N/HYPE | a2 | 2 | 121 | 2.58 | 7.1 | 150 | 136 | 1/2 | 3.02 | 11.1 | 0.0 | 0.04 | 0 |
| N/HYPE | b_psola | 11 | 210 | 3.77 | 10.4 | 168 | 164 | 10/11 | 3.04 | 13.6 | 3.8 | 0.84 | 3 |
| N/HYPE | b_world | 11 | 215 | 4.07 | 10.4 | 165 | 163 | 10/11 | 3.02 | 14.6 | 3.2 | 0.86 | 0 |
| N/HYPE | c_pocket | 11 | 173 | 3.87 | 10.4 | 192 | 191 | 7/11 | 2.83 | 14.0 | 2.5 | 0.55 | 0 |
| N/HYPE | e_mild | 11 | 216 | 2.99 | 7.5 | 177 | 172 | 11/11 | 2.99 | 13.0 | 0.6 | 0.90 | 2 |
| N/HYPE | e_mid | 11 | 219 | 3.50 | 8.8 | 177 | 173 | 11/11 | 3.03 | 13.2 | 1.6 | 0.92 | 4 |
| N/HYPE | e_strong | 11 | 219 | 4.11 | 10.7 | 176 | 172 | 11/11 | 2.98 | 13.2 | 2.3 | 0.90 | 2 |
| N/HYPE | e_alt | 11 | 213 | 4.92 | 13.3 | 158 | 155 | 11/11 | 3.01 | 14.0 | 2.8 | 0.88 | 0 |
| **N/DEADPAN** | reference narrator, deadpan units | 57 | 121 | 2.00 | 4.9 | - | 163 | - | - | - | - | - | - |
| N/DEADPAN | a1 | 6 | 120 | 2.91 | 7.2 | 152 | 148 | 6/6 | 3.25 | 11.1 | 1.5 | 0.94 | 0 |
| N/DEADPAN | a2 | 2 | 129 | 3.00 | 7.7 | 150 | 114 | 2/2 | 3.16 | 10.7 | 0.0 | 0.83 | 0 |
| N/DEADPAN | b_psola | 6 | 113 | 2.23 | 5.5 | 144 | 140 | 4/6 | 3.19 | 11.2 | 0.8 | 0.60 | 1 |
| N/DEADPAN | b_world | 6 | 116 | 2.22 | 4.9 | 144 | 140 | 5/6 | 3.18 | 12.9 | 0.8 | 0.74 | 0 |
| N/DEADPAN | c_pocket | 6 | 109 | 2.38 | 6.3 | 182 | 170 | 4/6 | 3.02 | 9.4 | 0.0 | 0.55 | 0 |
| N/DEADPAN | e_mild | 6 | 116 | 2.12 | 5.3 | 159 | 145 | 6/6 | 3.18 | 10.6 | 0.7 | 0.98 | 3 |
| N/DEADPAN | e_mid | 6 | 115 | 2.19 | 6.0 | 159 | 145 | 6/6 | 3.13 | 10.9 | 0.3 | 0.96 | 2 |
| N/DEADPAN | e_strong | 6 | 117 | 2.38 | 6.2 | 160 | 145 | 6/6 | 3.16 | 10.7 | 0.3 | 0.94 | 0 |
| N/DEADPAN | e_alt | 6 | 116 | 2.62 | 7.2 | 152 | 141 | 6/6 | 3.19 | 11.6 | 0.0 | 0.86 | 0 |
| **SYS/*** | reference system voice | 4 | 369 | 1.75 | 4.8 | - | 202 | - | - | - | - | - | - |
| SYS/* | a1 | 3 | 167 | 2.94 | 8.0 | 161 | 161 | 3/3 | 3.32 | 16.4 | 0.0 | 0.80 | 0 |
| SYS/* | b_psola | 3 | 211 | 1.83 | 5.0 | 164 | 161 | 3/3 | 3.30 | 19.4 | 0.0 | 1.04 | 0 |
| SYS/* | b_world | 3 | 210 | 2.09 | 5.1 | 161 | 161 | 3/3 | 3.19 | 19.8 | 0.0 | 1.01 | 0 |
| SYS/* | c_pocket | 3 | 203 | 3.33 | 9.0 | 170 | 170 | 2/3 | 2.99 | 21.4 | 0.0 | 0.75 | 0 |
| SYS/* | e_mild | 3 | 209 | 1.77 | 4.5 | 166 | 160 | 3/3 | 3.32 | 19.2 | 1.0 | 1.05 | 2 |
| SYS/* | e_mid | 3 | 211 | 2.07 | 5.2 | 166 | 160 | 3/3 | 3.32 | 19.0 | 1.3 | 1.04 | 0 |
| SYS/* | e_strong | 3 | 213 | 2.37 | 6.0 | 166 | 160 | 3/3 | 3.39 | 18.8 | 1.0 | 1.04 | 1 |
| SYS/* | e_alt | 3 | 209 | 2.45 | 5.7 | 160 | 154 | 3/3 | 3.17 | 17.4 | 6.0 | 0.86 | 0 |
| **SAM/*** | reference kid | 30 | 330 | 2.20 | 5.5 | - | 129 | - | - | - | - | - | - |
| SAM/* | a1 | 3 | 161 | 3.72 | 9.5 | 156 | 147 | 2/3 | 2.90 | 11.4 | 0.0 | 0.24 | 0 |
| SAM/* | a2 | 1 | 172 | 3.64 | 9.1 | 125 | 110 | 1/1 | 3.26 | 13.7 | 0.0 | 0.68 | 0 |
| SAM/* | b_psola | 3 | 232 | 5.00 | 13.2 | 157 | 142 | 3/3 | 2.72 | 15.4 | 3.0 | 0.77 | 1 |
| SAM/* | b_world | 3 | 251 | 4.87 | 12.6 | 156 | 141 | 3/3 | 2.58 | 17.1 | 0.0 | 0.72 | 1 |
| SAM/* | c_pocket | 3 | 317 | 2.36 | 6.5 | 142 | 121 | 1/3 | 2.66 | 13.0 | 0.0 | -0.52 | 0 |
| SAM/* | e_mild | 3 | 265 | 2.64 | 7.9 | 163 | 143 | 2/3 | 2.80 | 13.8 | 0.0 | 0.43 | 0 |
| SAM/* | e_mid | 3 | 259 | 2.80 | 8.4 | 163 | 143 | 2/3 | 2.70 | 13.3 | 0.0 | 0.40 | 0 |
| SAM/* | e_strong | 3 | 262 | 2.69 | 7.3 | 163 | 143 | 2/3 | 2.70 | 13.4 | 0.0 | 0.40 | 1 |
| SAM/* | e_alt | 3 | 257 | 4.38 | 9.4 | 163 | 143 | 2/3 | 2.72 | 13.3 | 2.7 | 0.41 | 0 |
| **DAD/*** | reference dad | 10 | 140 | 2.42 | 6.3 | - | 177 | - | - | - | - | - | - |
| DAD/* | a1 | 1 | 155 | 3.82 | 10.0 | 117 | 117 | 0/1 | 2.91 | 15.4 | 0.0 | -0.51 | 0 |
| DAD/* | b_psola | 1 | 259 | 4.93 | 12.0 | 118 | 118 | 1/1 | 3.07 | 14.8 | 7.0 | 0.91 | 0 |
| DAD/* | b_world | 1 | 272 | 4.85 | 10.8 | 118 | 118 | 1/1 | 2.93 | 15.8 | 4.0 | 0.86 | 0 |
| DAD/* | c_pocket | 1 | 240 | 1.79 | 4.7 | 178 | 178 | 0/1 | 2.14 | 16.4 | 0.0 | -0.55 | 0 |
| DAD/* | e_mild | 1 | 265 | 4.20 | 10.2 | 135 | 135 | 1/1 | 3.03 | 13.3 | 11.0 | 0.86 | 0 |
| DAD/* | e_mid | 1 | 268 | 3.78 | 9.1 | 135 | 135 | 1/1 | 3.01 | 13.1 | 8.0 | 0.89 | 1 |
| DAD/* | e_strong | 1 | 266 | 3.76 | 8.7 | 135 | 135 | 1/1 | 2.90 | 12.7 | 7.0 | 0.83 | 0 |
| DAD/* | e_alt | 1 | 263 | 3.47 | 9.6 | 137 | 137 | 1/1 | 3.04 | 12.3 | 0.0 | 0.76 | 0 |

What the table says:
- **Plain Kokoro (a1) cannot act.** Its hype and deadpan lines are the same voice at the same pitch (121 Hz vs 120 Hz). It gets its 2.7 st from creak and micro-prosody, not intonation.
- **Phrase splitting (a2) makes things worse.** The joins drop the line's melody, and ASR fails on 1 of 2 hype lines.
- **Post-processing (b) is the most expressive per line.** PSOLA won 5 lines: the long hype lines with big accents ("half a SECOND", "I AGREE", "PHONE's"), the deadpan "scroll back...", and Sam's "Ish". WORLD won Sam's nervous line. The costs: lower HNR in places, more fry tails (3.2-3.8 frames on average) and 2 ASR misses on deadpan lines ("Bedtime s supposedly": the time-warp smears the pause). On deadpan lines b scores clearly below e.
- **Native prosody (e) is the most reliable.** Every narrator and SYS line is word-perfect in all three variants, speaker consistency is the highest (cosine 0.93 to the register centroid), and the hype gate passes 11/11. It is the default for new lines.
- **Pocket TTS (c) is worse on every axis.** It was prompted with our own e takes as voice and style reference. The style does transfer (hype sd 3.9 st), but the register halves (173 Hz) and ASR word-perfect drops to 7/11. It paraphrased ("In my defence, darling, ..." and "in my defence" twice) and Sam's lines collapsed. It is also CC-BY-4.0 with an unclear voice-prompt provenance chain, so it was an experiment only.
- **e_alt** (the casting runner-up voice, am_echo/am_michael for N) has the most pitch movement but lower consistency with the cast voice. That confirms the casting rather than replacing it.

## 5. Chosen recipe per role

`RECIPE` in `audio/voice_lab.py` holds the defaults per role and register (the best mean score in the lab) and the lab's pick
for each hook line. `--hook` re-renders exactly these takes.

| role | voice (stock Kokoro packs, Apache-2.0) | register preset | default approach | character processing |
|---|---|---|---|---|
| N hype | blend am_michael 0.5 + am_puck 0.5 | 205 Hz, contour ×1.45, accents 3.5 st (CAPS 4-5 st), 172 wpm voiced, beats ... 0.42 s / . 0.30 s / , 0.16 s | e_mid (b_psola where it wins by > 0.05) | 'bright' EQ (+2.5 dB at 3.2 kHz), +2 dB loudness accents |
| N deadpan | same voice | 112 Hz, contour ×0.55, accents 0.8 st, 1.5 st declination, 2 st final fall, 156 wpm, beats 0.48/0.36/0.20 s | e_mild | 'warm' EQ |
| SYS | af_nova | calm 200 Hz ×0.60; cheerful 238 Hz ×1.25 with 2.5 st accents | e_mild (calm), e_strong (cheerful) | 'clean' EQ, delivered dry; chime and digital filter in the mix |
| SAM | decoder (timbre) 0.7 af_sky + 0.3 am_puck, predictor (prosody) af_sky | nervous 295 Hz ×1.5, 4 st accents, 6.5 Hz / 0.25 st tremor; guilty 250 Hz ×0.8; yawning 260 Hz ×0.7 with a glide | b_psola | Praat 'Change gender' formants ×1.12 (pitch kept), 'kid' EQ |
| DAD | am_eric | shouting 265 Hz ×1.3, 4 st accents (SUN 5 st, ×1.7 length) | e_mid | 'shout' EQ + strain (band-limited saturation, 35 % mix) |

Per line (final takes, measured after conforming):

| line | role, tag | text | chosen | F0 med | pitch sd | range | wpm voiced | dur s | DNSMOS | ASR heard | spk sim role | score (runner-up) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S00-L001 | N HYPE | What if real life had a SETTINGS menu? | e_mid | 213.8 | 3.7 | 9.0 | 161.1 | 3.07 | 3.16 | What if real life had a settings menu? | 0.754 | 1.06 (e_mild 1.05) |
| S00-L002 | N HYPE | One app. | e_mild | 206.5 | 3.21 | 9.24 | 181.8 | 0.76 | 2.57 | One app. | 0.749 | 0.89 (e_alt 0.91) |
| S00-L003 | N HYPE | Total control. | e_mild | 212.6 | 4.87 | 11.98 | 153.8 | 0.86 | 2.92 | Total control. | 0.739 | 1.05 (b_psola 1.07) |
| S00-L004 | N DEADPAN | No undo. | e_mild | 116.2 | 1.92 | 5.09 | 181.8 | 0.76 | 2.81 | No undo. | 0.665 | 0.98 (b_psola 1.01) |
| S00-L005 | SYS calm | Factory reset in one minute. | e_mild | 208.9 | 1.8 | 4.06 | 166.7 | 1.90 | 3.22 | Factory reset in one minute. | 0.845 | 1.05 (e_mid 1.03) |
| S00-L006 | SAM nervous | In my defense... I only changed ONE thing. | b_world | 293.8 | 5.01 | 13.46 | 155.8 | 3.48 | 2.8 | In my defense, I only changed one thing. | 0.667 | 0.93 (b_psola 0.91) |
| S00-L007 | SYS calm | Changes made by you: four hundred and twelve. | e_mild | 203.0 | 1.59 | 4.4 | 172.7 | 3.48 | 3.47 | Changes made by you, four hundred and twelve. | 0.839 | 1.09 (b_psola 1.10) |
| S00-L008 | SAM guilty | ...Ish. | b_psola | 191.0 | 2.04 | 4.7 | 96.8 | 0.71 | 1.98 | Ish. | 0.667 | 0.50 (b_world 0.48) |
| S00-L009 | N DEADPAN | Let's scroll back... seven days. | b_psola | 113.9 | 2.04 | 4.74 | 144.9 | 2.40 | 3.08 | Let's scroll back seven days. | 0.778 | 1.04 (a1 1.01) |
| S00-L010 | N DEADPAN | Bedtime. Supposedly. | e_mid | 117.3 | 2.13 | 5.82 | 117.6 | 1.44 | 3.23 | Bedtime, supposedly. | 0.7 | 0.99 (e_mild 0.99) |
| S00-L011 | N HYPE | An app you never downloaded. | e_mid | 211.4 | 3.68 | 10.47 | 170.5 | 1.85 | 3.0 | An app you never downloaded. | 0.758 | 0.99 (e_strong 0.97) |
| S00-L012 | N DEADPAN | First, the terms and conditions. | e_mid | 113.6 | 2.67 | 6.32 | 164.8 | 2.15 | 3.14 | First, the terms and conditions. | 0.715 | 0.97 (a1 0.98) |
| S00-L013 | N DEADPAN | Four thousand, eight hundred and twelve pages. | e_mild | 112.6 | 1.7 | 4.05 | 160.3 | 2.94 | 3.27 | four thousand eight hundred and twelve pages. | 0.723 | 1.03 (b_world 1.04) |
| S00-L014 | N HYPE | So you read every word... | e_strong | 222.6 | 3.6 | 9.38 | 156.2 | 2.13 | 3.05 | So you read every word. | 0.785 | 0.94 (e_alt 0.97) |
| S00-L015 | N HYPE | ...in half a second. | b_psola | 213.2 | 5.04 | 14.55 | 180.5 | 1.44 | 3.24 | in half a second. | 0.753 | 1.04 (e_mid 0.94) |
| S00-L016 | N HYPE | ...and press I AGREE. | b_psola | 203.0 | 4.92 | 14.6 | 160.0 | 1.60 | 2.82 | And press I agree. | 0.774 | 0.98 (b_world 0.94) |
| S00-L017 | SYS cheerful | Welcome to Reality Settings! | e_strong | 254.3 | 5.02 | 14.34 | 160.0 | 1.70 | 3.23 | Welcome to Reality Settings. | 0.815 | 1.06 (b_psola 1.05) |
| S00-L018 | SAM yawning | Prove it. | e_strong | 283.0 | 4.94 | 12.86 | 90.2 | 1.75 | 2.66 | Prove it. | 0.74 | 0.88 (b_psola 0.90) |
| S00-L019 | N HYPE | You open Brightness. | e_mid | 210.8 | 2.85 | 7.04 | 174.8 | 1.10 | 2.9 | You open brightness. | 0.737 | 1.01 (e_strong 0.98) |
| S00-L020 | N HYPE | Slide it up. Just a little. | e_mid | 205.3 | 4.33 | 10.74 | 192.5 | 2.27 | 3.2 | Slide it up just a little. | 0.79 | 0.89 (e_strong 0.87) |
| S00-L021 | DAD shouting | Who turned on the SUN?! | e_mid | 263.2 | 4.15 | 10.2 | 135.1 | 2.33 | 2.66 | Who turned on the sun? | None | 0.89 (b_psola 0.91) |
| S00-L022 | N HYPE | That's not the PHONE's brightness. | b_psola | 231.8 | 4.69 | 14.48 | 176.5 | 1.79 | 2.77 | That's not the phone's brightness. | 0.757 | 0.86 (a1 0.83) |
| S00-L023 | N DEADPAN | That's the planet's. | e_mild | 116.9 | 2.48 | 6.74 | 144.0 | 1.43 | 3.4 | That's the planets. | 0.704 | 0.99 (e_mid 0.98) |
| S01-L001 | N HYPE | Day one. | e_strong | 218.8 | 3.22 | 8.68 | 190.5 | 0.72 | 2.75 | Day one | 0.766 | 0.86 (b_psola 0.90) |

**Sam's formant shift (×1.12), measured.** The reference kid's formant spacing is 1392 Hz (narrator 1180). Our Sam blend
measured 1180-1190 Hz on the nervous line. The table below shows Sam's lines at formant 1.0 (first lab pass) and 1.12 (second
pass, which also raised the nervous and yawning register targets, so the F0 column moves for both reasons):

| line | approach | F0 median Hz (1.0 / 1.12) | formant spacing dF Hz (1.0 / 1.12) | DNSMOS (1.0 / 1.12) | HNR dB (1.0 / 1.12) | ASR (1.0 / 1.12) |
|---|---|---|---|---|---|---|
| S00-L006 | b_psola | 282.1 / 292.9 | 1180 / 1277 | 3.24 / 2.98 | 16.52 / 16.37 | ok / ok |
| S00-L006 | b_world | 285.4 / 302.4 | 1188 / 1311 | 2.66 / 3.01 | 18.41 / 16.78 | ok / ok |
| S00-L006 | e_mid | 295.5 / 258.7 | 1191 / 1312 | 3.01 / 2.68 | 11.52 / 10.02 | ok / ok |
| S00-L006 | e_strong | 268.6 / 262.5 | 1189 / 1320 | 2.5 / 2.79 | 11.28 / 9.38 | ok / ok |
| S00-L018 | b_psola | 212.0 / 231.8 | 1070 / 1053 | 2.8 / 3.03 | 15.1 / 17.2 | ok / ok |
| S00-L018 | b_world | 194.9 / 250.7 | 1070 / 1225 | 2.35 / 2.42 | 13.77 / 17.19 | ok / ok |
| S00-L018 | e_mid | 219.5 / 274.1 | 1069 / 1248 | 2.72 / 2.67 | 16.61 / 16.77 | ok / ok |
| S00-L018 | e_strong | 227.9 / 282.1 | 1070 / 1255 | 2.61 / 2.78 | 16.44 / 16.78 | ok / ok |

×1.12 moves the spacing to 1225-1320 Hz on 7 of the 8 renders, toward the reference kid, with no ASR loss. One L018 PSOLA render measured 1053 Hz; formant tracking on a 2-word line is noisy. DNSMOS moves either way
by up to 0.3, inside its noise. The exception is "Ish.": every shifted render lost the word in ASR at ×1.06 and ×1.12, so that one
line keeps formant 1.0 (`DIRECTION['S00-L008']['formant']`). It also sits low (191 Hz). The higher-pitched native renders of "Ish"
were never heard as "Ish" (0/6), so this is a trade of register for intelligibility on a muttered one-syllable line.

**Pitch contours** of three hype lines, plain Kokoro vs the chosen take, with the reference's hype and deadpan bands:
`qa/pitch_S00-L001.png` (question, e_mid), `qa/pitch_S00-L016.png` ("I AGREE", b_psola), `qa/pitch_S00-L022.png`
("PHONE's", b_psola). The accents land on the stressed vowels (WHAT, REAL, SET-tings; PRESS, I-a-GREE; NOT, PHONE's), and the
plain reads sit in the deadpan band. One miss is visible: the question rise on "menu?" did not render (the end stays flat
at ~190 Hz). For a "what if" question a fall is natural, so we left it.

## 6. Files and how to use them

| file | what |
|---|---|
| `audio/voice_lab.py` | the lab and the regenerator. `--hook`, `--ids S00-L006,...`, `--scene S01` regenerate lines with the chosen recipe; `--lab` builds and scores every approach; `--finalize` writes the lab-chosen takes; `--plots`, `--reel` make QA files; `--say "..." --role N --tag HYPE --out x.wav` for an ad-hoc line |
| `audio/voice_ingest.py` | measures, conforms and registers any WAV/MP3 (ours or a Fish take): `python3 -I audio/voice_ingest.py take.wav --id S00-L006 --role SAM --tag nervous --text "In my defense... I only changed ONE thing." --update` |
| `audio/voice_lines.json` | one entry per line: `{id, role, tag, text, file, dur, words:[{w,t,d}], visemes:[[t,name]], metrics, approach}`; times in seconds from the file start |
| `<scratch>/settings/voice/<ID>_<ROLE>.wav` | final takes: 48 kHz mono 24-bit, 30 ms handles, peak <= -1 dBFS, every role at -20 LUFS integrated (dry stems; the mix sets the balance) |
| `<scratch>/settings/voice/lab/` | every candidate (24 kHz), `lab.json` (merged; all metrics, scores and picks), the per-run files `lab_A/B/C/A2/B2/S.json` with `run_*.log`, and `lab_C_sam_formant1.0.json` (Sam at formant 1.0, the A/B in section 5) |
| `<scratch>/settings/voice/qa/` | `lab_table.md` (every candidate), `lab_summary.md` (per approach), pitch-contour plots, `hook_voice_reel.wav` (+ cues) |

Determinism: `VOICE_THREADS=1` (the default) and the fixed Praat seed make every recipe bit-reproducible; a lab run of new lines can
use more threads, but then keep that count for the re-render. To re-run the lab in parallel: `--lab --lab-json <file> --ids ...`
per process, then `--merge a.json,b.json,...` (later files override earlier ones per candidate) re-scores and re-picks everything,
and `--finalize` writes the picks.

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

## 7. Honest limits: what still sounds synthetic

The checks below are all measurements. Nobody has listened to these takes, so treat every "sounds" as a prediction from the
numbers.
- **Timbre.**
  - Every voice is a Kokoro stock pack or a blend of them. DNSMOS overall of the final takes is 1.98-3.47 (median 3.05).
  - Against the plain reads, our edits cost 0-0.4 per role on average: N hype -0.27, deadpan -0.10, SYS 0, Dad -0.25, Sam -0.42.
  - Clean read speech typically scores about 3.3-3.5 on this model, so the takes are intelligible and clean but will read as "good TTS", not as a performer.
- **Acting is melody, not voice quality.** The edits change pitch, timing and loudness. They do not change breathiness, vocal effort, smile or laughter, so:
  - The excited narrator is a higher, more melodic version of the same voice, not a voice that sounds thrilled.
  - Dad's shout is a high, strained-EQ'd read at 263 Hz with saturation, not a real yell: no pressed phonation, no breath intake, no cracking.
  - Sam's yawn "Prove it." is a slow glide (90 wpm), not a yawn sound. A real yawn layer would have to come from SFX.
- **PSOLA texture.** 5 of 24 takes are PSOLA (b_psola). PSOLA at shifts up to about an octave (hype lines are raised about 10 st from Kokoro's 121 Hz read) adds a faint "phasey", buzzy quality in long vowels. Our proxies (HNR, clicks, F0 jumps) do not flag it, so it is the first thing to check by ear.
- **Sam is not a real child.**
  - The register is right: nervous 294 Hz, yawning 283 Hz.
  - The formants are raised (×1.12), but the base is an adult female/male decoder blend, so the timbre is "small adult", not 12 years old.
  - "Ish." sits at 191 Hz with the unshifted timbre (section 5). The 3 Sam lines are the least consistent role (cosine 0.69 vs 0.71-0.83 for the others).
- **Pitch sd overshoots in places.** Sam (4.9 st) and SYS cheerful (5.0 st) move more than the reference voices (2.2 and 1.75 st). The reference system voice is flatter and band-passed, so our SYS cheerful line is the most "over-acted" against the reference. If it sounds sing-song, re-render with `--variant mild`.
- **Word timings** come from Parakeet-TDT token times (80 ms steps, refined on the energy envelope), good to about ±40 ms. Visemes are inside word windows, but windows less than 0.12 s apart are merged, so a consonant closure between two words can carry v_small instead of v_closed.
- **What we did not run.**
  - Supertonic (MIT code, OpenRAIL-M weights): like the other sherpa-onnx engines it takes only text, a voice and a speed, so it could only enter as another plain read.
  - Piper libritts_r (CC BY 4.0, 904 speakers): kept for crowd filler, not for acted lines.
  - ZipVoice: trained on Emilia (CC BY-NC), excluded from final takes.

## 8. Licences of what is in the takes

| part | licence | use |
|---|---|---|
| Kokoro v1.0 weights and voice packs (af_nova, af_sky, am_michael, am_puck, am_eric) | Apache-2.0 | every final take (blends and edited prosody are our derivative work) |
| Praat (parselmouth), WORLD (pyworld) | GPL-3 / BSD-type, used as tools | post-processing; no model weights |
| Parakeet-TDT 0.6B v2 (ASR), WeSpeaker ResNet34 (speaker embedding), DNSMOS (quality) | various | measurement only; nothing of them is in the audio |
| Pocket TTS (Kyutai, CC-BY-4.0) | measured as c_pocket, not used in any final take | |

No reference audio was used as a voice prompt or training data anywhere. The reference video was only measured, for pitch,
rate and formant targets. Pocket TTS was prompted only with our own Kokoro takes.

## 9. What a Fish Audio take would still improve

- **Voice quality as emotion.** Breath, smile, effort, a real shout for Dad (pressed voice and a crack on "SUN"), a real yawn on "Prove it.", and a mumbled, guilty "Ish." that is both high and intelligible. None of these can be made by editing pitch and timing.
- **A child voice.** Use a Fish voice designed as a 12-year-old (not a clone). Our Sam is the weakest role by every measure: DNSMOS 2.48, consistency 0.69.
- **Naturalness at high pitch.** A performer who reads hype at 230 Hz natively avoids the PSOLA texture of our raised takes, and lets the narrator reach the reference's 233 Hz hype median (ours 213 Hz: we stopped at 205 Hz targets because quality fell above that).
- **Micro-timing.** Anticipation before punchlines, rushing on lists, a laugh in "Supposedly." Our beats are designed per punctuation mark, so they are regular.

What a Fish take still needs from us: the same targets. Run `voice_ingest.py` on each file and compare it with this table. A
hype line under 2 st, or a deadpan line above about 140 Hz, would be a retake even from a human-sounding voice. The two
registers are the joke.
