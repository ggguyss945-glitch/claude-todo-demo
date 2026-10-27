#!/usr/bin/env bash
# assemble_ep.sh <work_dir> <mix.wav> <out.mp4> — join the render's video segments in frame order (no re-encode)
# and add the mixed soundtrack as AAC, YouTube-ready.
set -euo pipefail
W=$1; MIX=$2; OUT=$3
ls "$W"/seg_*.mp4 | grep -v '\.part\.' | sort | sed "s/^/file '/; s/\$/'/" > "$W/segments.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$W/segments.txt" -c copy "$W/video.mp4"
ffmpeg -v error -y -i "$W/video.mp4" -i "$MIX" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -ar 48000 -movflags +faststart -shortest "$OUT"
ffprobe -v error -show_entries format=duration,size,bit_rate -of compact "$OUT"
