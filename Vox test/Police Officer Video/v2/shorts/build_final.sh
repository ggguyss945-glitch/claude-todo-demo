#!/bin/bash
# Build the final Shorts in one go: picture (1080x1920, 60 fps) + voice + cues -> mix -> deliverable + cover + sheet + checks.
#   bash shorts/build_final.sh            # all three, one after the other (each render uses 3 worker processes)
#   bash shorts/build_final.sh 2          # just Short 2
# The owner's new recordings in _work/pov2/shorts_vo/<ID>.wav are picked up automatically by assemble.py.
set -euo pipefail
cd "$(dirname "$0")/.."
S="$(pwd)/_work/pov2/shorts"
for N in "${@:-1 2 3}"; do
  for n in $N; do
    echo "=== Short $n: assemble (picture + voice + cues)"
    python3 shorts/assemble.py --short "$n"
    echo "=== Short $n: mix"
    python3 shorts/mix_short.py --short "$n" --in "$S/S$n"
    echo "=== Short $n: finalize (mux, cover, contact sheet, verify)"
    python3 shorts/finalize.py --short "$n"
  done
done
