#!/bin/bash
# One-shot status of the delivery film pipeline: workflow journal, running processes, render/mix logs, disk.
J=/root/.claude/projects/-home-user-claude-todo-demo/aa250ae7-a0b4-594f-9bc6-bd18b596cf27/subagents/workflows/wf_85214f76-679/journal.jsonl
F="/home/user/claude-todo-demo/Vox test/Dummy Video/film/_work"
date '+now %H:%M'
python3 - "$J" <<'PY'
import json, sys, os, time
labels = {}; started = {}; done = []; errs = []
for l in open(sys.argv[1]):
    e = json.loads(l)
    k = e.get('key'); t = e.get('type')
    if t == 'started': labels[k] = e.get('label'); started[k] = e.get('label')
    elif t == 'result': done.append(labels.get(k)); started.pop(k, None)
    elif t in ('error', 'failed'): errs.append((labels.get(k), str(e.get('error', ''))[:160]))
print('done:', done)
print('running:', list(started.values()))
print('errors:', errs[-3:])
d = os.path.dirname(sys.argv[1])
ag = sorted([os.path.join(d, f) for f in os.listdir(d) if f.startswith('agent-') and f.endswith('.jsonl')], key=os.path.getmtime)
if ag: print('newest agent file age: %d min' % ((time.time() - os.path.getmtime(ag[-1])) / 60))
PY
ps -eo etimes,args | grep -E 'render.py|mix.py|film.py|ffmpeg|final_chain|deliver' | grep -v grep | cut -c1-120 | head -5
L="$F/logs/final_chain.log"; [ -f "$L" ] && { echo "-- final chain (log age $(( ($(date +%s) - $(stat -c %Y "$L")) / 60 )) min):"; grep -E '^==' "$L" | tail -4; grep -E 'Error|Traceback|Killed|TOO SHORT' "$L" | tail -3; }
echo "chunks done: $(ls "$F"/picture/chunks/c*/OK 2>/dev/null | wc -l) of $(wc -l < "$F/picture/chunks/ranges.txt" 2>/dev/null || echo '?')"
for P in "$F"/picture/chunks/c*/progress_*.json; do [ -f "$P" ] && [ ! -f "$(dirname "$P")/OK" ] && echo "$(basename "$(dirname "$P")") $(cat "$P")"; done
pgrep -f "bash tools/final_chain[.]sh" >/dev/null && echo "final chain: RUNNING" || echo "final chain: not running"
free -g | awk 'NR==2{print "mem used", $3, "GB of", $2}'
df -h /home | tail -1 | awk '{print "disk free", $4}'
