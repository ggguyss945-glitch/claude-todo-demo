# AUDIO_SPEC: measured reference soundscape and targets for v2

Source: the three reference "rules" videos (`$S/ref2/fire.mp4`, `hotel.mp4`, `class.mp4`; 8.3, 9.0, 10.5 min).
Narration was separated from the music+SFX bed with sherpa-onnx UVR MDX-NET Voc_FT (`analysis/separate.py`,
bed = mix - voice). Numbers come from `analysis/measure.py` (BS.1770 K-weighted; "LU rel voice" = bed loudness
minus the integrated loudness of the voice stem). Rule announcements were located with whisper base.en
(`analysis/asr.py`). Raw metrics: `$S/pov2/refaudio/metrics_{fire,hotel,class}.json`.

## 1. Loudness

| | fire | hotel | class | **target** |
|---|---|---|---|---|
| Mix integrated (LUFS) | -14.4 | -14.6 | -14.5 | **-14.0** (ARCHITECTURE) |
| Mix sample peak (dBFS) | -1.3 | -0.8 | -0.9 | **≤ -1.5 dBTP** |
| Voice integrated (LUFS) | -14.7 | -14.9 | -14.8 | voice ≈ mix - 0.3 LU |
| Bed integrated (LUFS) | -27.2 | -27.7 | -28.1 | |
| Bed integrated, LU rel voice | -12.5 | -12.8 | -13.4 | **-13 ± 1** |
| Bed during speech, power mean / median (LU rel voice) | -8.5 / -13.5 | -8.6 / -13.6 | -9.4 / -13.6 | **-9 / -13.5** |
| Bed in speech gaps, power mean / median | -5.6 / -9.9 | -7.0 / -11.3 | -4.8 / -11.1 | **-6 / -10.5** |
| Bed in gaps ≥ 1 s (power mean) | -3.4 | n/a | -3.4 | **-3.5** |
| Bed short-term p10 / p50 / p90 (rel voice) | -16.1/-11.4/-3.9 | -16.7/-11.9/-4.1 | -16.9/-12.5/-5.0 | **-16.5 / -12 / -4.5** |
| Bed loudness range (LRA, LU) | 13.8 | 13.9 | 13.7 | **13-14** |
| Mix momentary max (LU over integrated) | +8.4 | +11.1 | +9.4 | **+9 to +11** at the biggest scare |
| Mix short-term p95 (LU over integrated) | +4.0 | +4.3 | +3.9 | **+4** |

Reading: the music sits about 13.5 LU under the voice most of the time, and its peaks (swells, hits) push it to
within 4 LU of the voice. Ducking is shallow: the bed only comes up about 2.5 LU in the short breath gaps (19-21 per
minute, almost none ≥ 1 s), so the "gap" level is reached by rising underneath rather than by the voice stopping.
Narration covers 81-83% of the runtime.

## 2. Music presence, events, spectrum

| | fire | hotel | class | **target** |
|---|---|---|---|---|
| Time with tonal music present (bed > voice-20 LU) | 95.8% | 94.0% | 98.3% | **≥ 95%** (bed never stops) |
| Bed above voice-40 LU | 100% | 100% | 99.8% | 100%, no dead air (mix dead-air events: 0/0/1) |
| All bed onsets / min | 19.4 | 15.4 | 11.1 | **15** |
| Hits / impacts per min (high-energy onsets) | 3.7 | 3.8 | 1.3 | **3** (≈ 1 per 20 s) |
| Small foley per min | 7.0 | 4.8 | 3.7 | **5** |
| Hit peak, momentary LU rel voice (p50 / max) | +3.7 / +9.6 | +1.4 / +9.7 | +0.3 / +5.3 | **+2 / +9** |
| Hit contrast over local bed (dB, p50) | 15.8 | 14.4 | 14.6 | **≥ 15 dB** (cut the bed before the hit) |
| Hits that land under narration | 71% | 76% | 64% | ~70% (do not wait for a gap) |
| Bed energy < 250 Hz | 77.9% | 72.6% | 60.1% | **70%** |
| Bed energy 250 Hz-4 kHz | 21.4% | 27.0% | 39.5% | **29%** |
| Bed energy > 4 kHz | 0.7% | 0.4% | 0.3% | **≤ 2%** (see caveat) |
| 5-band: sub 20-60 / bass 60-250 / low-mid 250-2k / hi-mid 2-6k / air 6k+ | 32/46/20/1.4/0.4 | 25/47/26/0.8/0.2 | 28/32/39/0.9/0.2 | **28 / 42 / 28 / 1.5 / 0.5** |
| Octave levels dB rel 1 kHz (63, 125, 250, 500, 1k, 2k, 4k, 8k) | +12 +6 +6 +5 0 -6 -4 -9 | +7 +2 +1 +1 0 -9 -14 -17 | +7 +2 +4 +5 0 -6 -12 -16 | **+8 +3 +4 +4 0 -7 -10 -14** |
| Bed spectral centroid (median Hz) | 1026 | 1038 | 1075 | ~1050 |

The bed is dark and bass-heavy and stays out of the voice's 2-6 kHz presence band (voice centroid 1.0-1.1 kHz).
Caveat: UVR leaves most >4 kHz content in the voice stem, so the high-band share is underestimated; treat
"≤ 2%" as "no bright layers competing with the voice", not a hard ceiling on cymbal or glass hits at scares.

## 3. Dynamic arc

| | fire | hotel | class | **target** |
|---|---|---|---|---|
| Rises ≥ 8 LU per min | 2.8 | 2.4 | 2.1 | **2.5** |
| Rise length (median s) / gain (median LU) | 13.0 / 12.4 | 15.2 / 12.4 | 14.2 / 12.9 | **14 s / +12 LU** |
| Rises peaking within 4 s of a "Rule number N" line | 6/23 | 6/22 | 7/22 | about 1 in 3 rises pays off on a rule card |
| Bed mean rel voice by quarter of the video (LU) | -9.0 -10.8 -8.4 -9.7 | -10.1 -10.9 -9.2 -8.9 | -9.9 -11.3 -12.2 -8.2 | dip in Q2, loudest in the last quarter |
| Loudest 10 s of the bed | 490 s (end) | 450 s (final rule) | 610 s (end) | **climax in the final 60 s** |

Shape: the bed breathes in 13-15 s swells of about +12 LU, roughly one swell per rule section of 50-70 s split in two
(build-up and payoff), then falls back. The second quarter is the calmest; the last minute is the loudest.

## 4. Silences (bed drops ≥ 10 dB for ≥ 0.5 s)

| | fire | hotel | class | **target** |
|---|---|---|---|---|
| Count / per min | 14 / 1.7 | 10 / 1.1 | 17 / 1.6 | **1.5 / min** |
| Length median / max (s) | 1.76 / 2.68 | 1.78 / 2.44 | 1.54 / 3.36 | **1.7 s, max 3.5 s** |
| Depth median (dB) | 15.1 | 16.9 | 13.0 | **15 dB** |
| Narration continues over it | 93% | 100% | 94% | yes: the drop sits under a line |
| Followed by a hit | 14% | 30% | 6% | ~1 in 6 |
| Ends on a scene cut | 0% | 40% | 41% | ~1 in 3 |
| Bed after vs before the drop (LU, median) | -15 | -13 | -10 | the music comes back much quieter |

So silences are music drop-outs under the narration, not dead air: the bed falls away for about 1.7 s on an ominous
line ("...that station closed years ago."), and either a hit lands, a cut lands, or a sparse quiet layer returns.

## 5. Sound and picture

- Hits vs cuts: with 14-18 cuts per min (hotel, class), 24% and 50% of hits fall within ±0.3 s of a cut (chance
  is 18% and 14%); fire (3 cuts/min, mostly held shots) has 40% of cuts carrying a transient (chance 4%). Overall,
  hits are aimed at cuts at about 2-3x chance, but most cuts carry no sound event (only 3-8% have a real hit).
- Whooshes or risers into a cut are rare (6-8% of cuts). Hard cuts mostly pass with a small bed step (median 0.5-2.3
  dB; 4-14% jump ≥ 6 dB).
- Targets: every scare cut or reveal gets a hit within -0.05..+0.10 s of the frame; ordinary B-roll cuts get no
  event; at most 1 whoosh per minute; a ≥ 6 dB bed change on about 1 cut in 10 (scene or location change).

## 6. Music style

- Pulse: none. Pulse clarity 0.04-0.07 in every 30 s window (the 123 BPM tracker reading is identical across all three
  and is a default-prior artefact). Target: unpulsed drones and swells; any ostinato stays rare and low in the mix.
- Tonal centre: **D minor** in all three (key correlation 0.62-0.67). Strongest pitch classes **D, A, D#/Eb**: a D-A
  fifth drone with the flat second (Phrygian dread). Per minute the centre stays on D, sometimes shifting to A
  (fire, class). Target: D drone with fifth, Eb rubs, A as the second centre.
- Drone vs melodic: harmonic share 0.96-0.97, spectral flatness 0.0008 (strongly tonal, sustained). Pitch-class
  changes run about 90-115 per min, so slow low-register figures move over the drone (piano or low-string notes).
- Instrumentation guesses: sub-bass drone (sub within 10 dB of mids 77% of the time in fire, 35-37% in the other two);
  dark synth pad or low strings in 60-500 Hz; sparse low piano; sub booms or braams for hits. Bright high strings
  are almost absent (high harmonics within 15 dB of the mids 2-5% of the time).

## 7. Reverb and space

| | fire | hotel | class | **target** |
|---|---|---|---|---|
| Hit decay T60 estimate (median s) | 2.2 | 3.3 | 0.8 | **2-3 s** on hits and stingers |
| Voice tail T60 (median s) | 0.37 | 0.42 | 0.39 | dry voice, ≤ 0.4 s |
| Bed side-minus-mid (dB) / L-R correlation | -11.0 / 0.85 | -10.9 / 0.85 | -9.8 / 0.81 | **-10 dB / 0.83**: moderately wide |
| Voice side-minus-mid / correlation | -43 / 1.0 | -42 / 1.0 | -44 / 1.0 | mono, centred |

Dry, close narration in front of a big, dark, moderately wide room for music and hits.

## 8. Target list for the v2 mix (`audio/mix.py`, `audio/score.py`, `audio/sfx.py`)

1. Mix -14 LUFS integrated, true peak ≤ -1.5 dBTP, voice integrated within 0.5 LU of the mix.
2. Bed (music + SFX) integrated at **voice - 13 LU**. During speech: median -13.5 LU, power mean -9 LU. In breath gaps
   it comes up to -10.5 LU (median); in gaps ≥ 1 s it reaches -3.5 LU. Sidechain duck depth about 3 dB, never more than 6.
3. Music audible 95% or more of the runtime; no dead air.
4. About 2.5 swells per minute of +12 LU over about 14 s, about 1 in 3 peaking into a "Rule number N" card.
   Bed LRA 13-14 LU; Q2 the calmest, the final minute the loudest (mix momentary max +9 to +11 LU over integrated there).
5. Events per minute: about 3 hits, 5 small foley, 15 bed onsets in all. Hit peak median +2 LU over the voice
   integrated level, max +9; ≥ 15 dB contrast over the bed just before the hit; about 70% of hits under narration.
6. Silences: 1.5 per minute, 1.7 s median (max 3.5 s), 15 dB deep, under a narration line; about 1 in 6 followed by
   a hit, about 1 in 3 ending on a cut; the music comes back 10-15 dB quieter than before the drop.
7. Spectrum of the bed: about 70% below 250 Hz, 29% in 250 Hz-4 kHz, ≤ 2% above 4 kHz; octave tilt about
   +8/+3/+4/+4/0/-7/-10/-14 dB (63 Hz to 8 kHz, rel 1 kHz). Keep 2-6 kHz clear for the voice.
8. Score: unpulsed, D minor (D-A drone, Eb rub, A as second centre), sub drone, low pad or strings, sparse low piano,
   sub booms or braams; hits with 2-3 s reverb tails; bed side about -10 dB rel mid; dry mono voice.
9. Picture sync: hits on scare cuts or reveals (−0.05..+0.10 s); no sound on routine cuts; ≤ 1 whoosh/min.

## 9. Reference excerpts (for numeric comparison)

`$S/pov2/refaudio/excerpts/` (48 kHz, 24-bit stereo, separated bed only), with stats in `excerpts.json`.
`analysis/excerpts.py:compare(wav_path, ref_entry)` returns the differences between one of our beds and a reference entry.

| file | kind | len s | LUFS | LU rel voice | peak dBFS | low/mid/high % | onsets/min |
|---|---|---|---|---|---|---|---|
| fire_tension_build_477 | tension build | 20 | -23.9 | -9.2 | -5.1 | 91/9/0 | 66 |
| hotel_tension_build_49 | tension build | 20 | -28.1 | -13.1 | -11.2 | 91/9/0 | 36 |
| class_tension_build_501 | tension build | 20 | -24.9 | -10.1 | -7.7 | 94/5/0 | 33 |
| fire_scare_hit_82 | scare hit | 14 | -27.9 | -13.2 | -6.9 | 84/16/0 | 4 |
| hotel_scare_hit_443 | scare hit | 14 | -22.2 | -7.3 | -3.7 | 93/7/0 | 43 |
| class_scare_hit_587 | scare hit | 14 | -21.5 | -6.7 | -6.0 | 4/96/0 | 17 |
| fire_quiet_dread_120 | quiet dread | 15 | -35.1 | -20.4 | -11.7 | 61/38/1 | 8 |
| hotel_quiet_dread_170 | quiet dread | 15 | -36.2 | -21.3 | -22.5 | 61/39/0 | 76 |
| class_quiet_dread_420 | quiet dread | 15 | -36.7 | -21.9 | -17.5 | 61/39/1 | 112 |
| fire_rule_card_61 | rule card | 12 | -25.9 | -11.2 | -8.6 | 86/13/1 | 100 |
| hotel_rule_card_95 | rule card | 12 | -22.5 | -7.6 | -6.4 | 69/30/1 | 25 |
| class_rule_card_70 | rule card | 12 | -28.5 | -13.7 | -8.8 | 68/31/1 | 75 |

## Known limits

- The separation is a model, not the stems: some voice leaks into the bed (and the reverse), so "bed in speech"
  levels are slightly inflated and the high band is underestimated.
- The fire cuts file lists only 25 cuts (mostly held shots), so its cut-sync rates are not directly comparable.
- Rule-card times come from interpolating within whisper segments (±2 s).
- Hits vs foley are split by energy and contrast only; no event classifier (door knock vs boom).
