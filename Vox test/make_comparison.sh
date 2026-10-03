#!/bin/bash
# Side-by-side comparison of V1, V2 and V3 in one 3840x2160 (4K UHD) video.
# Each 1440x2560 portrait version is scaled to 1148x2040 under a label bar;
# audio is taken from V3 (all three share the original voice-over track).
set -euo pipefail
cd "$(dirname "$0")"
V1=${V1:-V1_transcript_edit.mp4}
V2=${V2:-V2_recreation.mp4}
V3=${V3:-V3_final.mp4}
OUT=${OUT:-Comparison_V1_V2_V3.mp4}
FONT=src3d/app/fonts/LiberationSans-Bold.ttf
FONT2=src3d/app/fonts/LiberationSans-Regular.ttf

label() { # $1 title, $2 subtitle
  echo "drawtext=fontfile=$FONT:text='$1':fontcolor=white:fontsize=58:x=(w-text_w)/2:y=22,drawtext=fontfile=$FONT2:text='$2':fontcolor=0xB8B8B8:fontsize=34:x=(w-text_w)/2:y=86"
}

ffmpeg -y -v error -stats -i "$V1" -i "$V2" -i "$V3" -filter_complex "
  color=c=0x0B0B0D:s=3840x2160:r=30:d=79[bg];
  [0:v]scale=1148:2040:flags=lanczos,setsar=1,pad=1148:2160:0:120:color=0x0B0B0D,$(label 'V1' 'transcript-only edit')[a];
  [1:v]scale=1148:2040:flags=lanczos,setsar=1,pad=1148:2160:0:120:color=0x0B0B0D,$(label 'V2' '1-to-1 recreation from the frames')[b];
  [2:v]scale=1148:2040:flags=lanczos,setsar=1,pad=1148:2160:0:120:color=0x0B0B0D,$(label 'V3' 'detailed final')[c];
  [bg][a]overlay=x=114:y=0:shortest=1[t1];
  [t1][b]overlay=x=1346:y=0:shortest=1[t2];
  [t2][c]overlay=x=2578:y=0:shortest=1,format=yuv420p[v]" \
  -map "[v]" -map 2:a:0 -c:v libx264 -preset slow -crf 16 -profile:v high -tune film \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
  -c:a aac -b:a 320k -movflags +faststart -shortest "$OUT"
echo "wrote $OUT"
