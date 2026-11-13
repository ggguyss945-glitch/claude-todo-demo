#!/bin/bash
# Encode one frame-exact segment of the finished picture to HEVC (video only), for tools/encode_chain.sh.
#   usage: enc_seg.sh <picture.mp4> <segment dir> <first frame> <frame count>
# Writes <dir>/seg.mp4 and an OK marker. The seek point is half a frame before the first frame, so float rounding can
# never drop or add a frame; timestamps are then rebuilt as N/60 from zero, so every segment starts clean.
set -e
PIC=$1; D=$2; F0=$3; N=$4
[ -f "$D/OK" ] && exit 0
rm -rf "$D"; mkdir -p "$D"
SS=$(python3 -c "print(f'{($F0 - 0.5) / 60:.6f}' if $F0 > 0 else '0')")
ffmpeg -v error -nostdin -y -ss "$SS" -i "$PIC" -frames:v "$N" -an -vf "setpts=N/(60*TB)" -r 60 \
  -c:v libx265 -preset faster -b:v 4000k \
  -x265-params log-level=error:vbv-maxrate=8000:vbv-bufsize=16000:keyint=120 -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -video_track_timescale 15360 "$D/seg.tmp.mp4"
GOT=$(ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 "$D/seg.tmp.mp4")
[ "$GOT" -eq "$N" ] || { echo "segment $D has $GOT frames, wanted $N"; exit 1; }
mv "$D/seg.tmp.mp4" "$D/seg.mp4"; touch "$D/OK"
