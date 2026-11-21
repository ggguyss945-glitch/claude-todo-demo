#!/bin/bash
# Rebuild the final mix after picture changes ("If The School Bus Stops At Midnight... DON'T GET ON"), from any directory:
#   bash "Vox test/Bus Video/film/audio/final_mix.sh"            cues -> mix -> measure -> preview_mix.mp4
# Prepared once (sound prep, already done; re-run only when the owner's packs change):
#   python3 audio/epidemic_catalog.py --bus         audio/catalog_epidemic_bus.json (the bus set first, then the others)
#   python3 audio/jingle_bus.py                     the Ride Right jingle's versions -> _work/mix/jingle_bus (checks)
#   python3 audio/music_plan.py --table             the music map (word-anchored on _work/align/timeline.json)
#   python3 audio/sfx_tests.py                      8 test windows -> _work/mix/tests (re-run after a new voice edit)
#   ... final_mix.sh --no-preview                                        skip the preview mux
# Steps (each one is also fine to run by hand from film/):
#   1. python3 film.py --cues                       cue sheets from the picture -> _work/cues/{sfx,music}_cues.json
#   2. python3 audio/mix.py ... _work/mix/final      the police mix (about 14 min, peaks at 12 GB: no render running);
#                        W lines get mix.py's default --who-fx W=his and TAG_FX places (door, loudspeaker, radio, ...)
#        --plan full     the score follows audio/music_plan.py (word-anchored tension events, snapped to the picture's
#                        hit frames; film.py's own music events are replaced) and audio/sfx_plan.py refines the
#                        picture's SFX sheet (PICTURE: film.py's names onto this film's recipes, the identity layer's
#                        hums / jingles / count thumps dropped from the SFX sheet; EDIT: re-levels; ADD: off-screen and
#                        foley additions, deduplicated by sound family); both sheets as mixed go to
#                        _work/mix/final/cues_used/
#        --bed-p50 -14   the Bus film's bed target (sound prep tests: at -16 the music was present only 42-85 %
#                        of each window; at -14, 70-73 % with the bed integrated -11.7..-13.7 LU)
#        --hits-db 6     the score's hits stem +6 dB (fix round 1: +4 -> +6) (voice-keyed 1-4.5 kHz cut on the hits keeps the next words)
#        --voice-ride 1  a slow 4:1 ride on the narration's loudest phrases (> +1 LU; fix round 1: at 2 / 3:1 the
#                        narration's loudest lines still reached +5 LU momentary over the mix), so the scares top the film
#   3. mix.wav = hard link of mix_en.wav            (render.py / deliver.sh read mix_en.wav, the job names mix.wav)
#   4. python3 audio/measure_mix.py _work/mix/final  loudness, voice clarity, music presence, every SFX cue re-checked
#   5. python3 audio/mix_scenes.py _work/mix/final   one sheet per scene (spectrogram, cues, score events, stem levels)
#                                                    -> _work/mix/final/scenes/NN_name.png
#   6. ffmpeg: the mix onto the low-res preview     -> _work/preview/preview_mix.mp4 (re-render the preview first when the
#                                                    picture changed: README, Sound: the final mix)
set -euo pipefail
FILM="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$FILM"
W=_work; OUT=$W/mix/final
mkdir -p "$OUT"
python3 film.py --cues
( cd audio && python3 mix.py ../$W/align/timeline.json ../$W/align/vo_en.wav - ../$W/cues ../$OUT --langs en --plan full --hits-db 6 --voice-ride 1.0 --bed-p50 -14 ) 2>&1 | tee "$OUT/mix.log"
ln -f "$OUT/mix_en.wav" "$OUT/mix.wav"
python3 audio/measure_mix.py "$OUT" --plot | tee "$OUT/measure.txt"
python3 audio/mix_scenes.py "$OUT" > "$OUT/scenes.log"
if [ "${1:-}" != "--no-preview" ] && [ -f "$W/preview/preview.mp4" ]; then
  ffmpeg -v error -y -i "$W/preview/preview.mp4" -i "$OUT/mix.wav" -map 0:v -map 1:a -c:v copy \
    -c:a aac -b:a 320k -ar 48000 -af apad -shortest -movflags +faststart "$W/preview/preview_mix.mp4"
  echo "preview: $FILM/$W/preview/preview_mix.mp4"
fi
