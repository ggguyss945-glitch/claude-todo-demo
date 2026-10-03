#!/bin/bash
# Re-launches render.js until it finishes. render.js exits with 75 when it restarts
# itself to release memory; any other failure (e.g. a renderer killed by the OOM
# killer) is retried too. Finished chunks are kept and skipped.
fails=0
while true; do
  node --expose-gc "$(dirname "$0")/render.js" "$@"
  code=$?
  [ $code -eq 0 ] && exit 0
  [ $code -ne 75 ] && fails=$((fails + 1))
  [ $fails -gt 20 ] && exit $code
  sleep 2
done
