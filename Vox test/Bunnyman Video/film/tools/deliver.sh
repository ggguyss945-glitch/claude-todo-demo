#!/bin/bash
# Final deliverable for the Bunnyman film from the rendered picture and the final mix (English only, no dub):
#   <out>/If_The_Bunnyman_Asks_You_To_Close_Your_Eyes_EN_1440p60_HEVC.mp4   one HEVC file (~550 MB for the 18 min film) for upload / transfer
# The near-lossless master is the rendered picture itself (W/picture/picture.mp4, H.264 CRF 16) + mix_en.wav; no MOV copy
# or split parts are made here, to save disk (they are three more copies of a ~4-5 GB file).
# usage: deliver.sh <picture.mp4> <mix dir with mix_en.wav> <out dir>
set -e
PIC=$(realpath "$1"); MIX=$(realpath "$2"); OUT=$(realpath -m "$3")
mkdir -p "$OUT"
B=If_The_Bunnyman_Asks_You_To_Close_Your_Eyes
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$PIC")
# HEVC keeps the film grain best at this size; the AAC gets a -3 dBFS sample limiter (AAC overshoots at -1.7 dBTP)
ffmpeg -v error -stats -y -i "$PIC" -i "$MIX/mix_en.wav" -map 0:v -map 1:a -c:v libx265 -preset faster -b:v 4000k \
  -x265-params log-level=error:vbv-maxrate=8000:vbv-bufsize=16000:keyint=120 -pix_fmt yuv420p -tag:v hvc1 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -af alimiter=limit=0.708:attack=1:release=60:level=false -c:a aac -b:a 160k -ar 48000 \
  -metadata:s:a:0 language=eng -metadata title="If The Bunnyman Asks You To Close Your Eyes... DON'T COUNT TO SEVEN" \
  -t "$DUR" -movflags +faststart "$OUT/${B}_EN_1440p60_HEVC.mp4"
ls -la "$OUT"
