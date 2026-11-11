"""plan/doc_v2.py: regenerate the data tables of PLAN_V2.md from plan/shots.json and plan/sound_plan.json.

    python3 plan/make_plan.py && python3 plan/validate.py && python3 plan/doc_v2.py

Everything between the markers <!-- AUTO:BEGIN --> and <!-- AUTO:END --> in PLAN_V2.md is rewritten; the rest is hand-written.
"""
import collections, json, os, statistics, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
DOC = os.path.join(FILM, 'PLAN_V2.md')
D = json.load(open(os.path.join(HERE, 'shots.json')))
SP = json.load(open(os.path.join(HERE, 'sound_plan.json')))
sh = D['shots']
byid = {s['id']: s for s in sh}


def fmt_t(x): return '%.2f' % x


def table(head, rows):
    out = ['| ' + ' | '.join(head) + ' |', '|' + '|'.join('---' for _ in head) + '|']
    for r in rows: out.append('| ' + ' | '.join(str(c).replace('|', '/') for c in r) + ' |')
    return '\n'.join(out)


parts = []
# ---------------------------------------------------------------- targets
res = subprocess.run([sys.executable, os.path.join(HERE, 'validate.py')], capture_output=True, text=True)
lines = [l for l in res.stdout.splitlines() if l.startswith('  ')]
parts.append('### A1. The target table (`python3 plan/validate.py`)\n\n```\n' + '\n'.join(l[2:] for l in lines) + '\n```\n'
             + ('\n' + res.stdout.splitlines()[-1] + '\n'))

# ---------------------------------------------------------------- sections
rows = []
for sec in D['sections']:
    ss = [s for s in sh if s['section'] == sec['name']]
    c = collections.Counter(s['cls'] for s in ss)
    n = len([s for s in ss if s['cls'] not in ('card', 'black')]) or 1
    rows.append([sec['name'], '%s-%s' % (fmt_t(sec['t0']), fmt_t(sec['t1'])), sec['title'], len(ss), sec['cuts_per_min'],
                 '%d/%d/%d/%d/%d' % (c['wide'], c['mid'], c['face'], c['insert'], c['pov']),
                 '%.2f' % statistics.median(s['dur'] for s in ss), ', '.join(s['hold'] for s in ss if s.get('hold')) or '-',
                 '%s-%s' % (ss[0]['id'], ss[-1]['id'])])
parts.append('### A2. Shot table summary by section\n\nClass counts are wide / MS-OTS-2S / faces / inserts-docs-diagrams-UI / POV.\n\n' +
             table(['section', 't (s)', 'what', 'shots', 'cuts/min', 'classes', 'median s', 'holds', 'ids'], rows) + '\n')

# ---------------------------------------------------------------- holds, cards
rows = [[h['id'], h['shot'], '%s-%s' % (fmt_t(h['t0']), fmt_t(h['t1'])), '%.2f' % h['dur'], '%.1f-%.1f (%.1f)' % tuple(h['brief']), h['what']] for h in D['holds']]
parts.append('### A3. The ten holds (the only shots over 2.5 s besides the cards and the time card)\n\n' +
             table(['hold', 'shot', 'plan t', 's', 'brief', 'what changes on camera'], rows) + '\n')
rows = [[c['n'], c['shot'], '%s-%s' % (fmt_t(c['appear']), fmt_t(c['cut'])), c['command'], '%d %% %s' % (c['reflection']['size'] * 100, c['reflection']['pose']),
         c['glass'], byid[sh[sh.index(byid[c['shot']]) + 1]['id']]['frame'][:70]] for c in D['rule_cards']]
parts.append('### A4. Rule cards (times unchanged) and the re-establishing wide after each\n\n' +
             table(['n', 'shot', 't', 'command (lipstick red)', 'her reflection', 'glass', 'the wide after it'], rows) + '\n')

# ---------------------------------------------------------------- Queen ladder
rows = []
for q in D['queen_ladder']:
    s = byid[q['shot']]
    rows.append([q['shot'], fmt_t(q['t0']), q.get('stage') or '-', q.get('step') if q.get('step') is not None else '-',
                 ('%d %%' % round(q['size'] * 100)) if isinstance(q.get('size'), (int, float)) else '-',
                 (q.get('where') or '')[:44], (q.get('framing') or s['type']), (q.get('wrong') or '')[:50]])
parts.append('### A5. The Queen ladder: every appearance with stage, step and size\n\n'
             'Stage S0..S4 and OFF are the brief\'s 3.3 stages; step is the tread she stands on in mirror shots (8 = the bottom); size '
             'is her height (or face height for CUs) as a fraction of the frame height. Teasers (0-12.7 s) are flash-forwards.\n\n' +
             table(['shot', 't0', 'stage', 'step', 'size', 'where', 'framing', 'new wrong thing'], rows) + '\n')

# ---------------------------------------------------------------- devices
rows = []
for d in D['devices']:
    s = byid[d['shot']]
    hud = [h for h in s['hud'] if h['type'] in ('diagram', 'doc', 'typebeat', 'stamp', 'highlight', 'map', 'count_pop', 'sound_rings', 'dials', 'eye_line', 'level_guide', 'phone')]
    rows.append([d['shot'], fmt_t(d['t0']), s['type'], d['kind'], d['id'], d['what'][:70], ', '.join(sorted({h['type'] for h in hud})) or '-'])
parts.append('### A6. Inserts, documents and diagrams (the per-minute device count)\n\n' +
             table(['shot', 't0', 'type', 'kind', 'id', 'what it teaches', 'HUD entries'], rows) + '\n')

# ---------------------------------------------------------------- error map
rows = []
for n, v in D['errors'].items():
    rows.append([n, v['error'], ', '.join('%s (%.1f)' % (i, byid[i]['t0']) for i in v['shots']),
                 byid[v['shots'][0]]['frame'][:90] if v['shots'] else ''])
parts.append('### A7. Error-to-shot map (DIRECTION_V2 section 6: 1-27 from the critique, 28-33 new)\n\n' +
             table(['#', 'v1 error', 'fixed by (shot, t0)', 'how (first fixing shot)'], rows) + '\n')

# ---------------------------------------------------------------- views
vc = collections.defaultdict(list)
for s in sh:
    vc[(s['set'], s['view'])].append(s)
rows = []
for (st, vw), ss in sorted(vc.items()):
    f = ss[0]['v1']
    vars_ = sorted({s['var'] for s in ss})
    rows.append(['%s/%s' % (st, vw), len(ss), ', '.join(vars_), ', '.join(sorted({s['type'] for s in ss})), '%s/%s' % (f['set'], f['view']),
                 ss[0]['frame'][:60]])
parts.append('### A8. Set / view vocabulary (what sets.py must build) with the v1 fallback\n\n'
             'shots[].v1 = {set, view, var, grade} names a view the v1 sets.py renders today, so film.py can preview every shot before '
             'the v2 view lands (`build_shot(dict(shot, **shot["v1"]))`).\n\n' +
             table(['set/view', 'shots', 'vars', 'types', 'v1 fallback', 'first use'], rows) + '\n')

# ---------------------------------------------------------------- acting clips
clips = collections.defaultdict(set)
for s in sh:
    for c in s['chars']:
        for a in c['acts']: clips[a[1]].add(c['who'])
src = open(os.path.join(FILM, 'characters.py')).read()
import re
defs = set(re.findall(r"def ([a-z_0-9]+)\(", src)) | set(re.findall(r"['\"]([a-z_0-9]+)['\"]\s*:", src)) | \
       {'expr', 'talk', 'look', 'walk', 'run', 'hold_up', 'freeze', 'sit', 'point', 'turn', 'snap_turn', 'tremble', 'head_down', 'head_tilt',
        'lean_in', 'stare', 'hand_on_glass', 'nervous_glance', 'phone_to_ear', 'blink', 'flinch', 'hand_to_mouth'}
missing = sorted(k for k in clips if k not in defs)
parts.append('### A9. Acting clips the plan calls that characters.py does not define yet\n\n'
             'characters.py ignores an unknown clip (no crash, no motion). %d clips are used in all; these %d need a method '
             '(or a rename in the shot list):\n\n' % (len(clips), len(missing)) +
             table(['clip', 'who'], [[k, ', '.join(sorted(clips[k]))] for k in missing]) + '\n')

# ---------------------------------------------------------------- sound
st = SP['stats']
dev = collections.Counter(c['name'] for c in SP['sfx'] if c.get('origin') == 'device')
newn = {k: v for k, v in SP['names']['new'].items() if v.get('v2')}
rows = [[k, dev.get(k, 0), v['desc'][:80], '%s %s' % (v['fallback']['name'], v['fallback']['params'] or '')] for k, v in sorted(newn.items())]
parts.append('### A10. Sound plan summary\n\n'
             '%d cues (%.1f per minute): %d carried from v1 at their film times, re-homed to the v2 shots (%d v1 cues left out: the old counter '
             'ticks and card cues, regenerated as device cues, and SFX_DROP; SFX_MOVE re-timed 17), '
             '%d new picture beats (shotlist.py V2_SFX), %d device cues. %d hit events (%.1f per minute), %d silences, %d swells, %d risers '
             '(music events unchanged from v1, re-homed). New names for the v2 devices (each with a fallback existing name until it is built):\n\n'
             % (st['cues'], st['per_min'], st['from_v1'], len(json.load(open(os.path.join(HERE, 'v1', 'sound_plan_v1.json')))['sfx']) - st['from_v1'],
                st['from_v2_shots'], st['from_devices'],
                st['hits'], st['hits_per_min'], st['silences'], st['rises'], st['risers']) +
             table(['name', 'cues', 'what', 'fallback'], rows) + '\n\nDevice cues by name: ' +
             ', '.join('%s %d' % kv for kv in dev.most_common()) + '.\n')

body = '\n'.join(parts)
doc = open(DOC).read()
a, b = doc.index('<!-- AUTO:BEGIN -->'), doc.index('<!-- AUTO:END -->')
doc = doc[:a] + '<!-- AUTO:BEGIN -->\n<!-- generated by plan/doc_v2.py from plan/shots.json; do not edit by hand -->\n\n' + body + '\n' + doc[b:]
open(DOC, 'w').write(doc)
print('PLAN_V2.md tables rewritten (%d chars)' % len(body))
