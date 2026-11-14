#!/bin/bash
# Rebuild the final mix after picture changes (the Bunnyman film), from any directory:
#   bash "Vox test/Bunnyman Video/film/audio/final_mix.sh"         cues -> mix -> measure -> preview_mix.mp4
#   ... final_mix.sh --no-preview                                        skip the preview mux
# Steps (each one is also fine to run by hand from film/):
#   1. python3 film.py --cues                       cue sheets from the picture -> _work/cues/{sfx,music}_cues.json
#   2. python3 audio/mix.py ... _work/mix/final      the police mix (about 14 min, peaks at 12 GB: no render running)
#        --plan full     the score follows audio/music_plan.py (word-anchored tension events, snapped to the picture's
#                        hit frames; film.py's own music events are replaced) and audio/sfx_plan.py refines the
#                        picture's SFX sheet (PICTURE: film.py's names onto this film's recipes, the identity layer's
#                        hums / jingles / count thumps dropped from the SFX sheet; EDIT: re-levels; ADD: off-screen and
#                        foley additions, deduplicated by sound family); both sheets as mixed go to
#                        _work/mix/final/cues_used/
#        --hits-db 4     the score's hits stem +4 dB (voice-keyed 1-4.5 kHz cut on the hits keeps the next words)
#        --voice-ride 2  a slow 3:1 ride on the narration's loudest phrases (> +2 LU), so the scares top the film
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
( cd audio && python3 mix.py ../$W/align/timeline.json ../$W/align/vo_en.wav - ../$W/cues ../$OUT --langs en --plan full --hits-db 4 --voice-ride 2.0 ) 2>&1 | tee "$OUT/mix.log"
ln -f "$OUT/mix_en.wav" "$OUT/mix.wav"
python3 audio/measure_mix.py "$OUT" --plot | tee "$OUT/measure.txt"
python3 audio/mix_scenes.py "$OUT" > "$OUT/scenes.log"
if [ "${1:-}" != "--no-preview" ] && [ -f "$W/preview/preview.mp4" ]; then
  ffmpeg -v error -y -i "$W/preview/preview.mp4" -i "$OUT/mix.wav" -map 0:v -map 1:a -c:v copy \
    -c:a aac -b:a 320k -ar 48000 -af apad -shortest -movflags +faststart "$W/preview/preview_mix.mp4"
  echo "preview: $FILM/$W/preview/preview_mix.mp4"
fi
