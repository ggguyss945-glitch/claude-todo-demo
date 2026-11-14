# Shorts: build and rebuild

Three vertical Shorts (1080x1920, 60 fps, 48-56 s) cut from the long video "If A Police Officer Knocks At Midnight...
DON'T PROVE YOU LIVE THERE". The contract is `SHORTS_PLAN.md`, `shorts_spec.json` and `SHORTS_ANALYSIS.md`. All voice is
the owner's narration (`_work/pov2/align/vo_en.wav`), cut as whole lines or word slices.

## One command

```bash
cd "v2"                                   # this folder's parent
bash shorts/build_final.sh                # all three Shorts, one after the other (about 15 min each on 4 cores)
bash shorts/build_final.sh 2              # one Short
```

`build_final.sh N` runs these three steps, which can also be run by hand:

```bash
python3 shorts/assemble.py --short N                                   # picture.mp4, voice.wav, timing.json, cue sheets
python3 shorts/mix_short.py --short N --in _work/pov2/shorts/SN        # mix.wav (-14 LUFS, <= -1 dBTP), stems, report
python3 shorts/finalize.py --short N                                   # final mp4 + cover + contact sheet + checks
```

Outputs go to `_work/pov2/shorts/final/`:

| File | What it is |
|---|---|
| `Short1_The_Other_Gentleman.mp4`, `Short2_Your_Voice_On_The_Radio.mp4`, `Short3_Never_Correct_Him.mp4` | H.264 high, CRF 16, 60 fps, AAC-LC 320 kb/s |
| `*_cover.png` | 1080x1920 cover frame (S1: IT'S YOURS, S2: IT'S A RECORDING, S3: HIM) |
| `*_sheet.jpg` | contact sheet, one frame per second |
| `*_verify.json` | measured duration, fps, codec, size, loudness, true peak, LRA, silences, CTA times, masking |

Work files (picture, voice, cues, mix, stems, reports) stay in `_work/pov2/shorts/S1`, `S2` and `S3`.

## The owner's new recordings (optional)

The finals are built without new recordings: the subscribe call and the end call are on screen only, while the existing
narration continues underneath. To add the spoken calls, put the WAV files (any sample rate, mono or stereo) here:

```
_work/pov2/shorts_vo/S1-N2.wav   "Everyone who subscribes gets to keep their own face."
_work/pov2/shorts_vo/S1-N3.wav   "Seven rules keep you alive. The full video is on the channel."
_work/pov2/shorts_vo/S2-N1.wav   "Everyone who subscribes gets to keep their own voice."
_work/pov2/shorts_vo/S2-N2.wav   "Where's your mother? Find out in the full video on the channel."
_work/pov2/shorts_vo/S3-N1.wav   "Everyone who subscribes knows which one is real."
_work/pov2/shorts_vo/S3-N2.wav   "Does she open the door? Watch the full video on the channel."
```

Then run `bash shorts/build_final.sh N` again. `assemble.py` picks the files up automatically as soon as any of that
Short's files exist (`--with-new-lines` forces it, `--no-new-lines` ignores them). The re-timing makes room for each
line. Check the new `*_verify.json`: the subscribe should stay at 43-50 % and the Short at 48-56 s.

## What each Short does (no new recordings)

- **Short 1, The Other Gentleman.** Hook: line 0 sliced to "...knocks on your door after midnight" plus line 1. The
  "DON'T PROVE YOU LIVE THERE" slam lands after "...belongs to you." Line 42 sets up "the same missing piece", and the
  chipped corner is circled on both cards. The SUBSCRIBE press is his palm slapping the car window (49.6 %). The twist
  "It's yours." comes at 70 %. The end card WHICH ONE OF YOU BELONGS HERE? sits over the grinning officer, who knocks
  again (frame 1's sound), then REWIND.
- **Short 2, Your Voice On The Radio.** Frame 1 is the officer's grin at the door with the radio held up. The SUBSCRIBE
  press is his thumb keying the radio to record you (49 %). From 37 to 43 s the shots cut between your mother's face,
  the cough, the waveforms and your face. The twist "a quiet click" comes at 82 %. The end card WHERE IS YOUR MOTHER?
  sits over her house, then the radio click and REWIND.
- **Short 3, Never Correct Him.** The premise is on screen by 2 s: WHO REALLY LIVES HERE?, then the double labelled HIM
  (SAYS HE'S YOU) on "Green,". RULE #5 plays over the officer and HIM at the door. The SUBSCRIBE press is the officer's
  finger turning off his bodycam (49 %). The silence comes right before "She tells you he called earlier" (twist at
  71 %). The end card DOES SHE OPEN THE DOOR? sits over her door, then knocking, the pen click and REWIND.

## Code map

- `timing.py`: cuts the narration. Clip edges come from the energy envelope (-40 dBFS). The head starts at most 40 ms
  before the first word and never inside the previous word. The tail keeps the decay plus 30 ms and stops at least
  20 ms before the next word. Connected speech is cut in the deepest valley. Fades are 8-12 ms in and 20 ms out, on
  zero crossings. `retime()` places the clips.
- `edit.py`: beats, shots, overlay events, HUD and sound cues. It also adds the finishing passes: keyword punches,
  hard re-frame cuts about every 1.0 s on long shots, filler punches, caption chunks of at least 0.25 s, and
  readability floors (tags at least 62 px and 1.0 s).
- `s1.py`, `s2.py`, `s3.py`: each Short's voice decisions and staging.
- `stage.py`: vertical rendering from the long film's builders. `overlay.py` and `vfx.py`: captions, HUD, slams, the
  SUBSCRIBE button, the end card, callouts and REWIND. A slam hides a caption chunk that shows the same words.
- `cues.py`: the SFX and music cue sheets. `mix_short.py`: the mix. Hits that land on speech are lowered (stingers by
  8 dB, impacts by 4 dB). A voice-keyed 1-4.5 kHz cut runs on every bus. S1's music sits 13 dB under the voice with a
  mid scoop.
- `finalize.py`: the mux, cover, contact sheet and checks. `build_final.sh` runs everything in order.
