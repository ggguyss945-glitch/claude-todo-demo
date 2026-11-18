#!/bin/bash
# Encode one frame-exact segment of the finished picture to HEVC (video only), for tools/encode_chain.sh.
#   usage: enc_seg.sh <picture.mp4> <segment dir> <first frame> <frame count>
# Writes <dir>/seg.mp4 and an OK marker. The seek point is half a frame before the first frame, so float rounding can
# never drop or add a frame; timestamps are then rebuilt as N/60 from zero, so every segment starts clean.
# Rate control comes from RC (default capped CRF 17). Do not use a bitrate target (-b:v) here: x265's ABR starts every
# segment cautiously, so quality drops ~12 dB for the first ~0.3 s after each join (a visible softness pulse every 30 s).
# Capped CRF 17 holds a flat ~50 dB from the first frame and matches the steady quality of the old 4000k ABR encode.
set -e
PIC=$1; D=$2; F0=$3; N=$4; RC=${RC:--crf 17}
[ -f "$D/OK" ] && exit 0
rm -rf "$D"; mkdir -p "$D"
SS=$(python3 -c "print(f'{($F0 - 0.5) / 60:.6f}' if $F0 > 0 else '0')")
ffmpeg -v error -nostdin -y -ss "$SS" -i "$PIC" -frames:v "$N" -an -vf "setpts=N/(60*TB)" -r 60 \
  -c:v libx265 -preset faster $RC \
  -x265-params log-level=error:vbv-maxrate=8000:vbv-bufsize=16000:keyint=120 -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -video_track_timescale 15360 "$D/seg.tmp.mp4"
GOT=$(ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 "$D/seg.tmp.mp4")
[ "$GOT" -eq "$N" ] || { echo "segment $D has $GOT frames, wanted $N"; exit 1; }
mv "$D/seg.tmp.mp4" "$D/seg.mp4"; touch "$D/OK"
