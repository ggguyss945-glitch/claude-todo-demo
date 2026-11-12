#!/bin/bash
# Final render + delivery + checks for the delivery film, in one chain (run from film/):
#   bash tools/final_chain.sh > _work/logs/final_chain.log 2>&1
# In a cloud session run it as a harness-tracked background task, not with nohup: the container is reclaimed about
# 5 minutes after the session goes idle, and that kills detached processes.
# The picture is rendered as K short chunks (frame-exact boundaries), 3 at a time, so a container restart only loses
# the chunks in flight: re-running skips every chunk with an OK marker. Then the chunks are joined (stream copy) into
# _work/picture/picture.mp4, checked, and tools/deliver.sh makes _work/deliver/If_A_Delivery_Driver_Rings_EN_1440p60_HEVC.mp4.
set -e
cd "$(dirname "$0")/.."
W=_work; C=$W/picture/chunks; K=${K:-24}; P=${P:-3}
mkdir -p "$C"
echo "== render start $(date -u +%H:%M)"
if [ ! -s $W/picture/picture.mp4 ]; then
  # frame-exact chunk ranges from the film's own length
  python3 - "$K" > "$C/ranges.txt" <<'EOF'
import sys, json
sys.path.insert(0, '.')
from engine.core import set_render_size
set_render_size(640, 360)
from film import Film
f = Film(json.load(open('_work/align/timeline.json')))
NT = int(round(float(f.duration) * 60)); K = int(sys.argv[1])
for k in range(K):
    f0, f1 = k * NT // K, (k + 1) * NT // K
    print(f'{k:02d} {f0 / 60:.10f} {f1 / 60:.10f} {f1 - f0}')
EOF
  echo "== $(wc -l < "$C/ranges.txt") chunks, $(awk '{s+=$4} END {print s}' "$C/ranges.txt") frames"
  export C
  awk '{print $1, $2, $3}' "$C/ranges.txt" | xargs -P "$P" -L 1 bash -c '
    k=$0; a=$1; b=$2; d=$C/c$k
    [ -f $d/OK ] && exit 0
    rm -rf $d; mkdir -p $d
    python3 render.py --workers 1 --from_ $a --to $b --out $d > $d/log.txt 2>&1 || { echo "== chunk $k FAILED"; exit 1; }
    rm -f $d/slice_00.mp4; touch $d/OK; echo "== chunk $k done $(date -u +%H:%M)"'
  n_ok=$(ls "$C"/c*/OK 2>/dev/null | wc -l)
  [ "$n_ok" -eq "$K" ] || { echo "== only $n_ok of $K chunks done"; exit 1; }
  for k in $(awk '{print $1}' "$C/ranges.txt"); do echo "file '$(realpath "$C/c$k/picture.mp4")'"; done > "$C/list.txt"
  ffmpeg -v error -y -f concat -safe 0 -i "$C/list.txt" -c copy -movflags +faststart $W/picture/picture.tmp.mp4
  mv $W/picture/picture.tmp.mp4 $W/picture/picture.mp4
fi
echo "== render done $(date -u +%H:%M)"
NF=$(ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 $W/picture/picture.mp4)
PD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $W/picture/picture.mp4)
MD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $W/mix/final/mix_en.wav)
EXP=$(awk '{s+=$4} END {print s}' "$C/ranges.txt" 2>/dev/null || echo 0)
echo "== picture frames $NF (expected $EXP) duration $PD (mix $MD)"
if [ "$EXP" -gt 0 ] && [ "$NF" -ne "$EXP" ]; then echo "== PICTURE FRAME COUNT WRONG"; exit 2; fi
rm -rf "$C"/c*/
echo "== deliver start $(date -u +%H:%M)"
bash tools/deliver.sh $W/picture/picture.mp4 $W/mix/final $W/deliver
H=$W/deliver/If_A_Delivery_Driver_Rings_EN_1440p60_HEVC.mp4
echo "== deliver done $(date -u +%H:%M)"
ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate -of compact "$H"
echo "== HEVC frames $(ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 "$H")"
ffmpeg -nostats -i "$H" -map 0:a -af ebur128=peak=true -f null - 2>&1 | grep -A12 Summary | grep -E "I:|Peak:|LRA:"
echo "== ALL DONE $(date -u +%H:%M)"
