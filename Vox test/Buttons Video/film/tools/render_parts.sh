#!/bin/bash
# Resumable rendering of heavy chunks in parts split at shot cuts (run from film/; a container restart loses only the
# part in flight, finished parts stay):
#   S=_work/deliver/segments PARTS="37:0,369,556,922 38:0,317,549,861" P=3 bash tools/render_parts.sh
# The part boundaries are relative frames of the chunk, from `DRY=1 N=3 bash tools/split_chunk.sh <k>` (shot cuts only:
# a shot rendered by two processes can jump in texture). Each part: render.py -> picture.mp4 -> HEVC part (enc_seg)
# -> the parts are joined by stream copy into $S/s<k>/seg.mp4 with an OK marker.
set -e
cd "$(dirname "$0")/.."
S=${S:-_work/deliver/segments}; P=${P:-3}; D=_work/picture/parts
export RC=${RC:--crf 20} S D
mkdir -p "$D"
cnt() { ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 "$1"; }
export -f cnt
jobs=""
for spec in $PARTS; do
  k=${spec%%:*}; IFS=, read -ra b <<< "${spec#*:}"
  [ -f "$S/s$k/OK" ] && continue
  t0=$(awk -v k="$k" '$1 == k {print $2}' "$S/ranges.txt")
  for ((p = 0; p < ${#b[@]} - 1; p++)); do
    jobs+="$k $p $(python3 -c "print(f'{$t0 + ${b[$p]} / 60:.10f}', f'{$t0 + ${b[$((p + 1))]} / 60:.10f}', ${b[$((p + 1))]} - ${b[$p]})")"$'\n'
  done
done
printf '%s' "$jobs" | xargs -P "$P" -L 1 bash -c '
  k=$0; p=$1; a=$2; z=$3; n=$4; d=$D/c${k}_p$p
  [ -f $d/seg/OK ] && exit 0
  if [ ! -f $d/picture.mp4 ] || [ "$(cnt $d/picture.mp4)" != "$n" ]; then
    rm -rf $d; mkdir -p $d
    python3 render.py --workers 1 --from_ $a --to $z --out $d > $d/log.txt 2>&1 || { echo "== part $k/$p FAILED"; exit 1; }
  fi
  [ "$(cnt $d/picture.mp4)" = "$n" ] || { echo "== part $k/$p has the wrong frame count"; exit 1; }
  bash tools/enc_seg.sh $d/picture.mp4 $d/seg 0 $n && rm -f $d/picture.mp4 $d/slice_00.mp4
  echo "== part $k/$p done $(date -u +%H:%M)"'
for spec in $PARTS; do
  k=${spec%%:*}; IFS=, read -ra b <<< "${spec#*:}"; np=$((${#b[@]} - 1))
  [ -f "$S/s$k/OK" ] && continue
  n=$(awk -v k="$k" '$1 == k {print $4}' "$S/ranges.txt"); ok=1; : > "$D/list_$k.txt"
  for ((p = 0; p < np; p++)); do
    [ -f "$D/c${k}_p$p/seg/OK" ] || ok=0
    echo "file '$(realpath "$D/c${k}_p$p/seg/seg.mp4")'" >> "$D/list_$k.txt"
  done
  [ $ok = 1 ] || { echo "== chunk $k: parts missing, run again"; continue; }
  rm -rf "$S/s$k"; mkdir -p "$S/s$k"
  ffmpeg -v error -nostdin -y -f concat -safe 0 -i "$D/list_$k.txt" -c copy -video_track_timescale 15360 "$S/s$k/seg.tmp.mp4"
  [ "$(cnt "$S/s$k/seg.tmp.mp4")" = "$n" ] || { echo "== chunk $k joined with the wrong frame count"; exit 1; }
  mv "$S/s$k/seg.tmp.mp4" "$S/s$k/seg.mp4"; touch "$S/s$k/OK"; rm -rf "$D"/c${k}_p*
  echo "== chunk $k done from $np parts $(date -u +%H:%M)"
done
