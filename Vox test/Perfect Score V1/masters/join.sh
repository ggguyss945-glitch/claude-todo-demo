#!/bin/bash
# Rebuild the high-bitrate masters from their <100 MB parts (GitHub's file limit).
cd "$(dirname "$0")"
for f in $(ls *.part-00 2>/dev/null | sed 's/\.part-00$//'); do
  cat "$f".part-* > "$f" && echo "rebuilt $f"
  [ -f "$f.sha256" ] && sha256sum -c "$f.sha256"
done
