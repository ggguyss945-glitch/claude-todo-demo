#!/usr/bin/env bash
# Emit one line per progress change of a running render: "done total rate last finished".
# Usage: tools/watch_render.sh <frames_dir> [interval_s=25]
P="$1/progress.json"; prev=""
while true; do
  if [ -f "$P" ]; then
    cur=$(python3 -I -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["done"], d["total"], d["rate"], d["last"], d["finished"])' "$P" 2>/dev/null || true)
    if [ -n "$cur" ] && [ "$cur" != "$prev" ]; then echo "$cur"; prev="$cur"; fi
    case "$cur" in *True) exit 0;; esac
  fi
  pgrep -f render_anim.js >/dev/null || { [ -f "$P" ] || { echo "render not running"; exit 1; }; }
  sleep "${2:-25}"
done
