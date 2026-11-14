#!/bin/bash
# Encode the rendered lossless chunks + final mix into the deliverables.
#   src/encode.sh <segment dir> <mix.wav> <out dir>
set -euo pipefail
SEG=$1; MIX=$2; OUT=$3
mkdir -p "$OUT/masters"
LIST=$(mktemp)
for f in $(ls "$SEG"/c*.mkv | sort); do echo "file '$f'" >> "$LIST"; done
COL="-colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv"
VF="scale=out_color_matrix=bt709:out_range=tv,format=yuv420p"
P=/tmp/ps_pass_$$
# 1) git-sized final (two-pass ~9 Mbps)
ffmpeg -v error -stats -y -f concat -safe 0 -i "$LIST" -vf "$VF" -c:v libx264 -preset slow -b:v 8800k -pass 1 -passlogfile $P \
  -profile:v high -tune film $COL -an -f mp4 /dev/null
ffmpeg -v error -stats -y -f concat -safe 0 -i "$LIST" -i "$MIX" -map 0:v -map 1:a -vf "$VF" -c:v libx264 -preset slow -b:v 8800k \
  -maxrate 14000k -bufsize 14000k -pass 2 -passlogfile $P -profile:v high -tune film $COL \
  -c:a aac -b:a 320k -ar 48000 -shortest -movflags +faststart "$OUT/Perfect_Score_V1_final.mp4"
rm -f $P*
# 2) high-bitrate master (CRF 14), split into <95 MB parts for git
ffmpeg -v error -stats -y -f concat -safe 0 -i "$LIST" -i "$MIX" -map 0:v -map 1:a -vf "$VF" -c:v libx264 -preset slow -crf 14 \
  -profile:v high -tune film -x264-params aq-mode=3 $COL -c:a aac -b:a 320k -ar 48000 -shortest -movflags +faststart \
  "$OUT/masters/Perfect_Score_V1_master.mp4"
# 3) 1080p preview for quick sharing (two-pass ~3.3 Mbps)
ffmpeg -v error -stats -y -f concat -safe 0 -i "$LIST" -vf "scale=1080:1920:flags=lanczos,$VF" -c:v libx264 -preset slow -b:v 3300k \
  -pass 1 -passlogfile $P -profile:v high $COL -an -f mp4 /dev/null
ffmpeg -v error -stats -y -f concat -safe 0 -i "$LIST" -i "$MIX" -map 0:v -map 1:a -vf "scale=1080:1920:flags=lanczos,$VF" -c:v libx264 \
  -preset slow -b:v 3300k -maxrate 6000k -bufsize 6000k -pass 2 -passlogfile $P -profile:v high $COL -c:a aac -b:a 192k -ar 48000 \
  -shortest -movflags +faststart "$OUT/Perfect_Score_V1_1080p_preview.mp4"
rm -f $P* "$LIST"
ls -la "$OUT" "$OUT/masters"
