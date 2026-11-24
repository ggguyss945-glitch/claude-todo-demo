#!/bin/bash
# Final picture for the Buttons film, rendered AND encoded chunk by chunk (run from film/):
#   P=3 bash tools/render_encode_chain.sh > _work/logs/render_encode.log 2>&1
# Then, once the final mix exists:  bash tools/join_chain.sh > _work/logs/join_chain.log 2>&1
#
# Disk-lean variant of final_chain.sh + encode_chain.sh (this machine had about 2 GB free). The film is cut into K
# frame-exact chunks; each chunk is rendered at 2560x1440 / 60 fps (render.py, x264 CRF 16 intermediate), encoded
# straight to its HEVC segment (capped CRF 20, tools/enc_seg.sh) and its intermediate is deleted at once, so the
# full-size intermediate never exists in one piece, and encoding overlaps rendering.
# Resumable: a chunk whose segment has an OK marker is skipped, so a container restart only loses the chunks in flight.
# Redo part of the film after a picture fix: delete $S/sNN for the chunks covering the changed times (ranges.txt lists
# each chunk's start and end in seconds) and run this again. If the film's LENGTH changes, delete $S entirely.
# Run it as a harness-tracked background task, never with nohup.
set -e
cd "$(dirname "$0")/.."
W=_work; C=$W/picture/chunks; S=${S:-$W/deliver/segments}; K=${K:-24}; P=${P:-3}
export RC=${RC:--crf 20}
mkdir -p "$C" "$S" $W/logs
echo "== start $(date -u +%H:%M), $K chunks, $P at a time, rate control: $RC"
# frame-exact chunk ranges from the film's own length: k, start s, end s, frames
python3 - "$K" > "$S/ranges.now" <<'EOF'
import sys, json
sys.path.insert(0, '.')
from engine.core import set_render_size
set_render_size(640, 360)
from film import Film
f = Film(json.load(open('_work/align/timeline.json')))
NT = int(round(float(f.duration) * 60)); K = int(sys.argv[1])
# chunk joins snap to the nearest shot cut (within 1.5 s): a shot rendered by two processes can jump in texture at
# the join (tex() seeds per process), so no shot is ever split between chunks
def sid(F): return id(f.shot_at(F / 60))
B = [0]
for k in range(1, K):
    t = k * NT // K
    cuts = [F for F in range(max(B[-1] + 60, t - 90), min(NT - 60, t + 91)) if sid(F - 1) != sid(F)]
    B.append(min(cuts, key=lambda F: abs(F - t)) if cuts else t)
B.append(NT)
for k in range(K):
    f0, f1 = B[k], B[k + 1]
    print(f'{k:02d} {f0 / 60:.10f} {f1 / 60:.10f} {f1 - f0}')
EOF
if [ -s "$S/ranges.txt" ] && ! cmp -s "$S/ranges.txt" "$S/ranges.now"; then
  echo "== the film's length or K changed since the segments were made: delete $S and run again"; exit 2
fi
mv "$S/ranges.now" "$S/ranges.txt"
echo "== $(wc -l < "$S/ranges.txt") chunks, $(awk '{s+=$4} END {print s}' "$S/ranges.txt") frames"
[ -n "$RANGES_ONLY" ] && exit 0        # RANGES_ONLY=1: only write the chunk ranges
export C S
set +e
# ONLY="00 03 17" limits this run to those chunks (a background task has a 2 h limit: split long runs).
# Parallelism can be changed while it runs: kill -USR1 <xargs pid> adds a lane, kill -USR2 removes one.
awk -v only="$ONLY" '{ if (only == "" || index(" " only " ", " " $1 " ")) print $1, $2, $3, $4 }' "$S/ranges.txt" | xargs -P "$P" -L 1 bash -c '
  k=$0; a=$1; b=$2; n=$3; d=$C/c$k
  [ -f $S/s$k/OK ] && exit 0
  if [ ! -f $d/OK ]; then
    rm -rf $d; mkdir -p $d
    python3 render.py --workers 1 --from_ $a --to $b --out $d > $d/log.txt 2>&1 || { echo "== chunk $k render FAILED (see $d/log.txt)"; exit 1; }
    rm -f $d/slice_00.mp4; touch $d/OK
  fi
  got=$(ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 $d/picture.mp4)
  [ "$got" = "$n" ] || { echo "== chunk $k rendered $got frames, wanted $n"; rm -f $d/OK; exit 1; }
  bash tools/enc_seg.sh "$d/picture.mp4" "$S/s$k" 0 "$n" || { echo "== chunk $k encode FAILED"; exit 1; }
  rm -rf $d
  echo "== chunk $k done $(date -u +%H:%M)"'
set -e
n_ok=$(ls "$S"/s*/OK 2>/dev/null | wc -l)
[ "$n_ok" -eq "$K" ] || { echo "== only $n_ok of $K segments done: run again"; exit 1; }
echo "== all $K segments done $(date -u +%H:%M); next: bash tools/join_chain.sh (needs the final mix)"
