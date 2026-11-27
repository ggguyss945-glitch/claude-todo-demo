"""The owner's per-event check on every SFX cue as mixed: python3 audio/mk_events.py <cues_used/sfx_cues.json> <events.json>
then measure_mix.py --events <events.json> (same order and seeds as the mix's cue pass; planned hits flagged scare)."""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure_mix as MM
cues = json.load(open(sys.argv[1]))
cues = cues if isinstance(cues, list) else cues.get('cues', cues)
order = sorted(range(len(cues)), key=lambda k: (cues[k]['t'], k))
ev = []
for rank, k in enumerate(order):
    c = cues[k]; p = dict(c.get('params') or {})
    ev.append(dict(t=c['t'], name=c['name'], params=p, space=c.get('space'), gain_db=c.get('gain_db', 0.0),
                   seed=int(c.get('seed', rank)), scare=(c['name'] in MM.HIT_NAMES and not (c['name'] == 'door_slam' and p.get('soft'))) or bool(c.get('scare')) or bool(p.get('boost')),
                   hard_end=bool(c.get('hard_end') or p.get('hard_end')), label=f"{c['name']}@{c['t']:.2f}"))
json.dump(ev, open(sys.argv[2], 'w'), indent=0)
print(len(ev), 'events,', sum(e['scare'] for e in ev), 'scare')
