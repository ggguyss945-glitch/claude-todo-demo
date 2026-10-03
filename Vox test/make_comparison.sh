#!/bin/bash
# Side-by-side comparison of V1, V2 and V3 playing in sync.
#   ./make_comparison.sh 4k     -> 3840x2160 master, ~44 Mbps
#   ./make_comparison.sh 1440p  -> 2560x1440, ~9.5 Mbps (fits in git)
# Each portrait 1440x2560 version is scaled under a label bar. The audio comes from V3
# (all three share the original voice-over track).
set -euo pipefail
cd "$(dirname "$0")"
MODE=${1:-4k}
V1=${V1:-V1_transcript_edit.mp4}
V2=${V2:-V2_recreation.mp4}
V3=${V3:-V3_final.mp4}
FONT=src3d/app/fonts/LiberationSans-Bold.ttf
FONT2=src3d/app/fonts/LiberationSans-Regular.ttf

if [ "$MODE" = "4k" ]; then
  K=3; OUT=${OUT:-masters/Comparison_V1_V2_V3_4K.mp4}; RATE=44000k; MAXR=70000k
else
  K=2; OUT=${OUT:-Comparison_V1_V2_V3_1440p.mp4}; RATE=9500k; MAXR=15000k
fi
# layout in 1/3-of-4K units so both sizes share one design
s() { echo $(( $1 * K / 3 / 2 * 2 )); }
FW=$(s 3840); FH=$(s 2160); PW=$(s 1148); PH=$(s 2040); BAR=$(s 120)
X1=$(s 114); X2=$(s 1346); X3=$(s 2578); T1=$(s 58); T2=$(s 34); Y1=$(s 22); Y2=$(s 86)

label() { # $1 title, $2 subtitle
  echo "drawtext=fontfile=$FONT:text='$1':fontcolor=white:fontsize=$T1:x=(w-text_w)/2:y=$Y1,drawtext=fontfile=$FONT2:text='$2':fontcolor=0xB8B8B8:fontsize=$T2:x=(w-text_w)/2:y=$Y2"
}
panel() { echo "scale=$PW:$PH:flags=lanczos,setsar=1,pad=$PW:$FH:0:$BAR:color=0x0B0B0D,$(label "$1" "$2")"; }

FILTER="color=c=0x0B0B0D:s=${FW}x${FH}:r=30:d=79[bg];
  [0:v]$(panel 'V1' 'transcript-only edit')[a];
  [1:v]$(panel 'V2' '1-to-1 recreation from the frames')[b];
  [2:v]$(panel 'V3' 'detailed final')[c];
  [bg][a]overlay=x=$X1:y=0:shortest=1[t1];
  [t1][b]overlay=x=$X2:y=0:shortest=1[t2];
  [t2][c]overlay=x=$X3:y=0:shortest=1,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[v]"
COL="-colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv"
P=/tmp/cmp_pass_$$
mkdir -p "$(dirname "$OUT")"
ffmpeg -y -v error -stats -i "$V1" -i "$V2" -i "$V3" -filter_complex "$FILTER" -map "[v]" \
  -c:v libx264 -preset slow -b:v $RATE -pass 1 -passlogfile $P -profile:v high -tune film $COL -an -f mp4 /dev/null
ffmpeg -y -v error -stats -i "$V1" -i "$V2" -i "$V3" -filter_complex "$FILTER" -map "[v]" -map 2:a:0 \
  -c:v libx264 -preset slow -b:v $RATE -maxrate $MAXR -bufsize $MAXR -pass 2 -passlogfile $P -profile:v high -tune film $COL \
  -c:a aac -b:a 320k -movflags +faststart -shortest "$OUT"
rm -f $P*
echo "wrote $OUT"
