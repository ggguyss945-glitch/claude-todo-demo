#!/usr/bin/env bash
# encode.sh <frames_dir> <mix.wav> <out.mp4> [fps=30] — H.264 High + AAC at the frames' own size, YouTube-ready
set -euo pipefail
ffmpeg -v error -y -framerate "${4:-30}" -i "$1/f_%05d.jpg" -i "$2" \
  -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -profile:v high -movflags +faststart \
  -c:a aac -b:a 320k -ar 48000 -shortest "$3"
ffprobe -v error -show_entries format=duration,size,bit_rate -of compact "$3"
