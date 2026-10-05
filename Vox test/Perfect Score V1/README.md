# Perfect Score — V1 final

An 81-second vertical short (1440×2560, 30 fps), written and produced from scratch in the low-poly visual
style of the *Eye in the Sky* / *Monte Carlo* / *Outsmarted the industry* references. That means simple
blocky 3D characters with photo-style painted faces, warm sunlit interiors, bloom, a sharpened grade and
burned-in white captions.

> **Imagine you scored a perfect hundred on every single exam. This is how fast it would take for your
> school to accuse you of cheating.**

The film runs from the first unnoticed 100, through a desk moved next to the teacher's, the unsolved
bonus question, the search and camera replay, "Cheater.", and a retake under three teachers' eyes. It
ends on "One hundred.", the wall of honor, and the desk moved to the very back so nobody can copy you.
There is no gambling and nothing haram; the moral is honesty and hard work.

| File | What it is |
|------|------------|
| `Perfect_Score_V1_final.mp4` | The final video with narration, score and SFX. About 9 Mbps, sized to fit in git. |
| `masters/` | A high-bitrate master in parts under 95 MB. Run `./join.sh` to rebuild it, with a sha256 check. |
| `ANALYSIS.md` | How the five reference scripts are built on the retention curve, the measured voice, music and SFX numbers, and how this script maps onto them. |
| `script/script.json` | The script, by beat (Hook / Rising / Conflict / Dip / Rising / Payoff), with pacing per line. |
| `script/VO_DIRECTION.md` | Line-by-line timing, tone and emphasis for re-recording the narration with a human voice. |

## How it was made

Everything is generated from code. No footage, images or samples are used.

* **Picture** (`app/`): three.js running in headless Chromium.
  * `chars.js` is the character rig:
    * pole-vector two-bone arm IK with hand orientation
    * a gait solved by leg IK, so planted feet don't slide
    * gaze and expressions
    * uniforms and hijab
  * `faces.js` paints every face from parameters.
  * `world.js` builds the five sets: classroom, corridor, principal's office, living room and bedrooms.
  * `props.js` builds the props, and `paper.js` the exam papers, whose pen strokes are real paths.
  * `stage.js` and `shots.js` hold the 51 shots, timed to the narration's word timings.
  * Every held object drives the hand that holds it, so props never float or pop.
  * The desk's position follows story time, so continuity holds across shots.
  * Adaptive motion blur kicks in on fast camera and object moves.
* **Narration** (`src/vo.py`): Kokoro-82M via sherpa-onnx.
  * The voice is a *new* synthetic voice, a 62/38 blend of two stock male styles. It is not a clone of anyone.
  * Each line is generated separately with its own pacing, then assembled with breaths.
  * It is mastered in `src/mix.py`: EQ, presence, de-essing, two-stage compression and a short room.
* **Score** (`src/music.py`): an original score in B minor at 120 BPM, written note by note against the
  timeline. It is rendered with FluidSynth (MuseScore General) as eight stems, and the hits land on the
  slam, the stand-up, CANCELLED, "Cheater." and "One hundred."
* **SFX** (`src/sfx.py`, `src/mix.py`): about 190 synthesized foley events.
  * Footsteps fall on the walk-cycle phases.
  * Marker squeaks follow the strokes being drawn.
  * Desk scrapes follow the desk's speed.
  * The hallway whispers are synthetic voices turned into real whispers (`src/whispers.py`).
* **Mix:** −14 LUFS integrated with a true peak of −1 dBTP. The voice sits 4.6 LU above the music+SFX bed,
  matching the *Eye in the Sky* reference (4.7 LU).

### Rebuild

```bash
npm install three@0.170.0 playwright             # or reuse ../src3d/node_modules
python3 src/vo.py <kokoro-multi-lang-v1_0> vo/   # narration -> vo/vo_raw.wav
python3 src/music.py music/                      # score stems
python3 src/whispers.py <kokoro dir> whispers/
python3 src/mix.py vo/vo_raw.wav music/ whispers/ mix.wav
./render_loop.sh --app app --version v3 --gl egl --chunk 30 --video out.mp4 --audio mix.wav
# quick review stills: node render.js --app app --gl egl --scale 0.4 --stills 0.9,23.5,64.9
```

### Note on the voice

The brief asked for a real human narrator. A human voice can't be recorded in this environment, so the
narration is synthetic. It was tuned to match the reference narrator's measured pitch, pacing and mic
sound. `script/VO_DIRECTION.md` has everything a voice actor needs to re-record it to the same timing.
Running `src/mix.py` with that recording rebuilds the soundtrack.
