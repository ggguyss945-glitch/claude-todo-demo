#!/bin/bash
# Rebuild the final mix after picture changes (the dummy film), from any directory:
#   bash "Vox test/Dummy Video/film/audio/final_mix.sh"            cues -> mix -> measure -> preview_mix.mp4
#   ... final_mix.sh --no-preview                                        skip the preview mux
# Steps (each one is also fine to run by hand from film/):
#   1. python3 film.py --cues                       cue sheets from the picture -> _work/cues/{sfx,music}_cues.json
#   2. python3 audio/mix.py ... _work/mix/final      the police mix (about 5 min, peaks at 7 GB: no render running)
#   3. mix.wav = hard link of mix_en.wav            (render.py / deliver.sh read mix_en.wav, the job names mix.wav)
#   4. python3 audio/measure_mix.py _work/mix/final  loudness, voice clarity, music presence, every SFX cue re-checked
#   5. ffmpeg: the mix onto the low-res preview     -> _work/preview/preview_mix.mp4
set -euo pipefail
FILM="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$FILM"
W=_work; OUT=$W/mix/final
mkdir -p "$OUT"
python3 film.py --cues
( cd audio && python3 mix.py ../$W/align/timeline.json ../$W/align/vo_en.wav - ../$W/cues ../$OUT --langs en ) 2>&1 | tee "$OUT/mix.log"
ln -f "$OUT/mix_en.wav" "$OUT/mix.wav"
python3 audio/measure_mix.py "$OUT" --plot | tee "$OUT/measure.txt"
if [ "${1:-}" != "--no-preview" ] && [ -f "$W/preview/preview.mp4" ]; then
  ffmpeg -v error -y -i "$W/preview/preview.mp4" -i "$OUT/mix.wav" -map 0:v -map 1:a -c:v copy \
    -c:a aac -b:a 320k -ar 48000 -af apad -shortest -movflags +faststart "$W/preview/preview_mix.mp4"
  echo "preview: $FILM/$W/preview/preview_mix.mp4"
fi
