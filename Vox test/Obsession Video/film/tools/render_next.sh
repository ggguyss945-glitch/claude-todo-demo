#!/bin/bash
# Render and encode the next batch of chunks that have no segment yet (run from film/, as a background task; each
# background task has a 2 h limit, so one batch = N chunks, about an hour of work):
#   N=6 P=3 bash tools/render_next.sh > _work/logs/render_next.log 2>&1
# K must stay the same for the whole film (48 here). When every segment is done it says so; then run join_chain.sh.
cd "$(dirname "$0")/.."
export K=${K:-48} P=${P:-3} S=${S:-_work/deliver/segments}
N=${N:-6}
mkdir -p "$S" _work/logs
if [ ! -s "$S/ranges.txt" ]; then RANGES_ONLY=1 bash tools/render_encode_chain.sh || exit 1; fi
todo=$(awk '{print $1}' "$S/ranges.txt" | while read k; do [ -f "$S/s$k/OK" ] || echo "$k"; done | head -n "$N" | tr '\n' ' ')
[ -z "$todo" ] && { echo "== all $K segments done; next: S=$S K=$K bash tools/join_chain.sh"; exit 0; }
echo "== batch: $todo ($(date -u +%H:%M))"
ONLY="$todo" bash tools/render_encode_chain.sh
echo "== segments done: $(ls "$S"/s*/OK 2>/dev/null | wc -l) of $K ($(date -u +%H:%M))"
