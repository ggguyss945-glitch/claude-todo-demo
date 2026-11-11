#!/bin/sh
# Decode a reference video into the frame sets the refmirror scripts read.
# Usage: sh extract.sh <ref_dir> <name>   (reads <ref_dir>/<name>.mp4, writes <ref_dir>/data/<name>/)
#   f1/fNNNN.jpg  1 fps 854x480     (sheets, look, grids)
#   small6.rgb    6 fps 320x180 rgb (measure_motion.py, tags.py)
#   gray30.raw    30 fps 160x90 gray (cuts30.py, still_share.py, punchins.py)
#   mix.wav       44.1 kHz stereo   (separate_ref.py -> voice.wav, bed.wav)
set -e
R="$1"; N="$2"; O="$R/data/$N"
mkdir -p "$O/f1"
ffmpeg -v error -y -i "$R/$N.mp4" -vn -ac 2 -ar 44100 "$O/mix.wav"
ffmpeg -v error -y -i "$R/$N.mp4" -an -filter_complex \
  "[0:v]split=3[a][b][c];[a]fps=1,scale=854:480[o1];[b]fps=6,scale=320:180:flags=area,format=rgb24[o2];[c]scale=160:90:flags=area,format=gray[o3]" \
  -map "[o1]" -q:v 2 -start_number 0 "$O/f1/f%04d.jpg" -map "[o2]" -f rawvideo "$O/small6.rgb" -map "[o3]" -f rawvideo "$O/gray30.raw"
