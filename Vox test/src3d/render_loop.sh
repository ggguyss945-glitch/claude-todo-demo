#!/bin/bash
# Re-launches render.js until it finishes; render.js exits with 75 when it
# restarts itself to release memory (finished chunks are kept and skipped).
while true; do
  node --expose-gc "$(dirname "$0")/render.js" "$@"
  code=$?
  [ $code -eq 75 ] && continue
  exit $code
done
