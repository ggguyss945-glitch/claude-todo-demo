#!/bin/bash
# Render ONE chunk of render_encode_chain.sh in N parts at the same time, encode each part to HEVC, join the parts
# (stream copy) into the chunk's segment and mark it OK. Use it when a single heavy chunk is the last thing left and
# cores are idle (run from film/):
#   S=_work/deliver/segments_v3 N=2 bash tools/split_chunk.sh 19
# The chunk's frame range comes from $S/ranges.txt (frames k*NT//K .. (k+1)*NT//K), so the result is identical in
# length to what render_encode_chain.sh would make. Never run it on a chunk that another run is rendering.
# Parts split ONLY at shot cuts (the cut nearest each even split point): a shot without tex_seed gets its grain /
# stain / frost textures from a per-process seed, so a shot rendered by two processes would jump at the split.
set -e
cd "$(dirname "$0")/.."
k=$1; S=${S:-_work/deliver/segments_crf20}; N=${N:-2}; C=_work/picture/chunks
export RC=${RC:--crf 20}
[ -f "$S/s$k/OK" ] && { echo "== chunk $k already done"; exit 0; }
cnt() { ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 "$1"; }
read t0 t1 n < <(awk -v k="$k" '$1 == k {print $2, $3, $4}' "$S/ranges.txt")
[ -n "$n" ] || { echo "== no chunk $k in $S/ranges.txt"; exit 1; }
# relative part boundaries: 0, the shot cut nearest each i*n/N, n
B=$(python3 - "$t0" "$n" "$N" <<'EOF' 2>/dev/null
import sys, json
sys.path.insert(0, '.')
from engine.core import set_render_size
set_render_size(640, 360)
from film import Film
t0, n, N = float(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
f = Film(json.load(open('_work/align/timeline.json')))
idx = [f.shot_at(t0 + i / 60).idx for i in range(n)]
cuts = [i for i in range(1, n) if idx[i] != idx[i - 1]]
b = [0]
for p in range(1, N):
    want = p * n // N
    c = min((c for c in cuts if c > b[-1]), key=lambda c: abs(c - want), default=None)
    if c is not None and c not in b: b.append(c)
print(' '.join(map(str, b + [n])))
EOF
)
set -- $B; [ "$#" -ge 2 ] || { echo "== could not find the part boundaries"; exit 1; }
echo "== chunk $k: $t0..$t1 s ($n frames), parts at relative frames $B, start $(date -u +%H:%M)"
[ -n "$DRY" ] && exit 0     # DRY=1: only print the part boundaries
d=$C/c${k}_split; rm -rf "$d"; mkdir -p "$d"
bs=($B); pids=(); np=$((${#bs[@]} - 1))
for p in $(seq 0 $((np - 1))); do
  a=${bs[$p]}; b=${bs[$((p + 1))]}
  A=$(python3 -c "print(f'{$t0 + $a / 60:.10f}')"); Z=$(python3 -c "print(f'{$t0 + $b / 60:.10f}')")
  mkdir -p "$d/p$p"; echo "$((b - a))" > "$d/p$p/frames"
  python3 render.py --workers 1 --from_ "$A" --to "$Z" --out "$d/p$p" > "$d/p$p/log.txt" 2>&1 &
  pids+=($!)
done
for pid in "${pids[@]}"; do wait "$pid" || { echo "== a part of chunk $k FAILED (see $d/p*/log.txt)"; exit 1; }; done
: > "$d/list.txt"
for p in $(seq 0 $((np - 1))); do
  m=$(cat "$d/p$p/frames"); got=$(cnt "$d/p$p/picture.mp4")
  [ "$got" = "$m" ] || { echo "== part $p has $got frames, wanted $m"; exit 1; }
  bash tools/enc_seg.sh "$d/p$p/picture.mp4" "$d/h$p" 0 "$m"
  rm -rf "$d/p$p"
  echo "file '$(realpath "$d/h$p/seg.mp4")'" >> "$d/list.txt"
done
rm -rf "$S/s$k"; mkdir -p "$S/s$k"
ffmpeg -v error -nostdin -y -f concat -safe 0 -i "$d/list.txt" -c copy -video_track_timescale 15360 "$S/s$k/seg.tmp.mp4"
got=$(cnt "$S/s$k/seg.tmp.mp4")
[ "$got" = "$n" ] || { echo "== joined chunk $k has $got frames, wanted $n"; exit 1; }
mv "$S/s$k/seg.tmp.mp4" "$S/s$k/seg.mp4"; touch "$S/s$k/OK"
rm -rf "$d"
echo "== chunk $k done $(date -u +%H:%M)"
