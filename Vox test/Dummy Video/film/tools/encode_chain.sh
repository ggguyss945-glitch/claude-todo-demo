#!/bin/bash
# Resumable HEVC delivery for the dummy film, from the finished picture and the final mix (run from film/):
#   P=2 bash tools/encode_chain.sh > _work/logs/encode_chain.log 2>&1
# Same x265 settings as tools/deliver.sh except rate control (capped CRF 17, see tools/enc_seg.sh), but the picture is encoded as K frame-exact segments with OK markers, so a
# container restart only loses the segments in flight: re-running skips every finished segment. The segments are joined
# with a stream copy, the AAC (with the -3 dBFS limiter) is muxed on, and the result is checked frame by frame.
# Run it as a harness-tracked background task, never with nohup, and never edit it while it runs.
set -e
cd "$(dirname "$0")/.."
W=_work; PIC=$(realpath $W/picture/picture.mp4); MIX=$W/mix/final/mix_en.wav
S=${S:-$W/deliver/segments_crf}; K=${K:-24}; P=${P:-2}
B=If_Your_Grandpas_Dummy_Tells_A_Joke; H=$W/deliver/${B}_EN_1440p60_HEVC.mp4
mkdir -p "$S"
NT=$(ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 "$PIC")
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$PIC")
echo "== encode start $(date -u +%H:%M) picture $NT frames $DUR s, $K segments, $P at a time, rate control: ${RC:--crf 17}"
python3 -c "
NT, K = $NT, $K
for k in range(K):
    f0, f1 = k * NT // K, (k + 1) * NT // K
    print(f'{k:02d} {f0} {f1 - f0}')" > "$S/ranges.txt"
export PIC S
awk '{print $1, $2, $3}' "$S/ranges.txt" | xargs -P "$P" -L 1 bash -c '
  [ -f $S/s$0/OK ] && exit 0
  bash tools/enc_seg.sh "$PIC" "$S/s$0" "$1" "$2" || { echo "== segment $0 FAILED"; exit 1; }
  echo "== segment $0 done $(date -u +%H:%M)"'
n_ok=$(ls "$S"/s*/OK 2>/dev/null | wc -l)
[ "$n_ok" -eq "$K" ] || { echo "== only $n_ok of $K segments done"; exit 1; }
echo "== segments done $(date -u +%H:%M)"
for k in $(awk '{print $1}' "$S/ranges.txt"); do echo "file '$(realpath "$S/s$k/seg.mp4")'"; done > "$S/list.txt"
ffmpeg -v error -nostdin -y -i "$MIX" -af alimiter=limit=0.708:attack=1:release=60:level=false \
  -c:a aac -b:a 160k -ar 48000 "$S/audio.m4a"
ffmpeg -v error -nostdin -y -f concat -safe 0 -i "$S/list.txt" -i "$S/audio.m4a" -map 0:v -map 1:a -c copy \
  -tag:v hvc1 -metadata:s:a:0 language=eng \
  -metadata title="If Your Grandpa's Ventriloquist Dummy Tells You A Joke... DON'T LAUGH" \
  -t "$DUR" -movflags +faststart "$H.tmp.mp4"
mv "$H.tmp.mp4" "$H"
echo "== joined $(date -u +%H:%M)"
ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate -of compact "$H"
NF=$(ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 "$H")
echo "== HEVC frames $NF (picture $NT)"
[ "$NF" -eq "$NT" ] || { echo "== HEVC FRAME COUNT WRONG"; exit 2; }
echo "== full decode check $(date -u +%H:%M)"
ERR=$(ffmpeg -v error -nostdin -i "$H" -map 0:v -f null - 2>&1 | head -5)
[ -z "$ERR" ] && echo "== decode clean" || { echo "== DECODE ERRORS: $ERR"; exit 3; }
ffmpeg -nostats -nostdin -i "$H" -map 0:a -af ebur128=peak=true -f null - 2>&1 | grep -A12 Summary | grep -E "I:|Peak:|LRA:"
echo "== ALL DONE $(date -u +%H:%M)"
