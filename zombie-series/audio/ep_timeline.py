# Episode timeline: the cold open (the approved 60 s test) followed by every script item, laid end to end.
# Gaps between items are scaled together so the episode lands on the target length.
# Shots, sounds and pauses come from the script itself; the voice file only supplies durations and word times,
# so pictures and sound can be re-cut without re-voicing.
# usage: python3 -I ep_timeline.py <cold_timeline.json> <ep_voice.json> <out.json> [target_s=915] [script=ep1_script]
import sys, os, json, re, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

COLD, VOICE, OUT = sys.argv[1:4]
TARGET = float(sys.argv[4]) if len(sys.argv) > 4 else 915.0
SC = importlib.import_module(sys.argv[5] if len(sys.argv) > 5 else 'ep1_script')
C = json.load(open(COLD)); V = json.load(open(VOICE))
voiced = {it['id']: it for it in V['items']}
items = []
for it in SC.ITEMS:
    v = voiced[it['id']]
    if it['who'] != 'BEAT' and v.get('text') != ' '.join(p for p, _ in it['phrases']):
        sys.exit(f"{it['id']}: the script changed since it was voiced; run ep_voice.py first")
    items.append(dict(it, **{k: v[k] for k in ('dur', 'words', 'text') if k in v}))

# cold open: keep its shots and lines, swap the test's title card (it fades over the whole test) for the episode one
shots = [dict(s) for s in C['shots']]
for s in shots:
    s['cold'] = s['name'] != 'title'
    if s['name'] == 'title': s['name'] = 'ep_title'
lines = [dict(L, who='N') for L in C['voice']['lines']]
EP0 = C['dur'] + 0.25

def length(scale):
    t = EP0
    for it in items: t += it['dur'] + it['gap'] * scale
    return t + 0.2
fixed, gaps = length(0), sum(it['gap'] for it in items)
scale = max(0.7, min(1.5, (TARGET - fixed) / gaps))

def word_t(it, word):
    w = word.lower().strip("'")
    for x in it.get('words', []):
        if x['w'].lower().strip(".,!?'") == w: return x['t']
    raise KeyError(f"{it['id']}: no word '{word}' in {[x['w'] for x in it.get('words', [])]}")

def anchor(it, start, a):
    """Seconds (absolute) for an anchor inside an item: number, '@word', '$' (end), '$-0.4'."""
    if isinstance(a, (int, float)): return start + a
    if a.startswith('@'): return start + word_t(it, a[1:])
    if a.startswith('$'): return start + it['dur'] + (float(a[1:]) if len(a) > 1 else 0.0)
    raise ValueError(a)

ep_shots, sfx, music, amb, caps, spans = [], [], [], [], [], {}
t = EP0
for it in items:
    start, end = t, t + it['dur']
    it['start'] = round(start, 3); spans[it['id']] = [round(start, 3), round(end, 3)]
    def local_params(p, s0):
        q = {}
        for k, v in (p or {}).items():
            q[k] = round(anchor(it, start, v) - s0, 3) if isinstance(v, str) and v.startswith('@') and k in ('blackout',) else v
        return q
    if it.get('shot'):
        tm, p = it['shot']; ep_shots.append({'name': tm, 'start': round(start, 3), 'p': local_params(p, start)})
    for off, tm, p in it.get('shots', []):
        s0 = anchor(it, start, off); ep_shots.append({'name': tm, 'start': round(s0, 3), 'p': local_params(p, s0)})
    for off, name, p in it.get('sfx', []):
        sfx.append({'t': round(anchor(it, start, off), 3), 'name': name, 'p': p, 'item': it['id']})
    if it.get('music'): music.append({'t': round(start, 3), 'cue': it['music'][0], 'p': it['music'][1], 'item': it['id']})
    if it.get('amb'): amb.append({'t': round(start, 3), 'bed': it['amb']})
    for c0, c1, txt in it.get('caps', []): caps.append([round(start + c0, 3), round(start + c1, 3), txt])
    if it['who'] != 'BEAT':
        lines.append({'id': it['id'], 'who': it['who'], 'start': round(start, 3), 'dur': it['dur'], 'words': it['words'], 'text': it['text'], 'echo': it.get('echo', False)})
    t = end + it['gap'] * scale
DUR = round(t + 0.2, 3)

ep_shots.sort(key=lambda s: s['start'])
allshots = shots + ep_shots
for i, s in enumerate(allshots):
    s['end'] = allshots[i + 1]['start'] if i + 1 < len(allshots) else DUR
    if s['end'] - s['start'] < 0.05: print('  WARNING: very short shot', s)
T = {'dur': DUR, 'ep_start': EP0, 'cold_dur': C['dur'], 'gap_scale': round(scale, 3), 'shots': allshots, 'events': C['events'],
     'voice': {'lines': lines, 'pa': C['voice']['pa']}, 'caps': caps, 'sfx': sfx, 'music': music, 'amb': amb, 'items': spans}
json.dump(T, open(OUT, 'w'), indent=1)
m, s = divmod(DUR, 60)
print(f'episode {int(m)}:{s:05.2f} ({DUR:.1f} s) | gap scale {scale:.3f} | shots {len(allshots)} (episode {len(ep_shots)}) | sfx {len(sfx)} | music cues {len(music)} | caps {len(caps)}')
from collections import Counter
print('templates:', dict(Counter(s['name'] for s in ep_shots)))
