#!/bin/bash
# Join the HEVC segments made by tools/render_encode_chain.sh and mux the final mix on (run from film/):
#   bash tools/join_chain.sh > _work/logs/join_chain.log 2>&1
# Same delivery audio and checks as tools/encode_chain.sh: frame count, a full decode, loudness of the decoded file.
set -e
cd "$(dirname "$0")/.."
W=_work; S=${S:-$W/deliver/segments}; K=${K:-48}; MIX=${MIX:-$W/mix/final/mix_en.flac}
B=If_Your_Moms_Eyes_Turn_Into_Buttons; H=${H:-$W/deliver/${B}_EN_1440p60_HEVC.mp4}
n_ok=$(ls "$S"/s*/OK 2>/dev/null | wc -l)
[ "$n_ok" -eq "$K" ] || { echo "== only $n_ok of $K segments done"; exit 1; }
NT=$(awk '{s+=$4} END {print s}' "$S/ranges.txt")
DUR=$(python3 -c "print(f'{$NT / 60:.6f}')")
echo "== join start $(date -u +%H:%M): $NT frames, $DUR s; mix $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$MIX") s"
for k in $(awk '{print $1}' "$S/ranges.txt"); do echo "file '$(realpath "$S/s$k/seg.mp4")'"; done > "$S/list.txt"
# Delivery audio, as in encode_chain.sh: 16.5 kHz low-pass, 4x-oversampled limiter at 0.66, 192k AAC
ffmpeg -v error -nostdin -y -i "$MIX" -af lowpass=f=16500:poles=2,aresample=192000,alimiter=limit=0.66:attack=1:release=60:level=false,aresample=48000 \
  -c:a aac -b:a 192k -cutoff 18000 -ar 48000 "${A:-$S/audio.m4a}"
ffmpeg -v error -nostdin -y -f concat -safe 0 -i "$S/list.txt" -i "${A:-$S/audio.m4a}" -map 0:v -map 1:a -c copy \
  -tag:v hvc1 -metadata:s:a:0 language=eng \
  -metadata title="If Your Mom's Eyes Turn Into Buttons... DON'T KEEP HER SECRET" \
  -t "$DUR" -movflags +faststart "$H.tmp.mp4"
mv "$H.tmp.mp4" "$H"
echo "== joined $(date -u +%H:%M)"
ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate -of compact "$H"
NF=$(ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 "$H")
echo "== HEVC frames $NF (expected $NT)"
[ "$NF" -eq "$NT" ] || { echo "== HEVC FRAME COUNT WRONG"; exit 2; }
echo "== full decode check $(date -u +%H:%M)"
ERR=$(ffmpeg -v error -nostdin -i "$H" -map 0:v -f null - 2>&1 | head -5)
[ -z "$ERR" ] && echo "== decode clean" || { echo "== DECODE ERRORS: $ERR"; exit 3; }
ffmpeg -nostats -nostdin -i "$H" -map 0:a -af ebur128=peak=true -f null - 2>&1 | grep -A12 Summary | grep -E "I:|Peak:|LRA:"
echo "== ALL DONE $(date -u +%H:%M)"
