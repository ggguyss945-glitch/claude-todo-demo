"""plan/validate.py (v2): check plan/shots.json and plan/sound_plan.json against the timeline and DIRECTION_V2's targets.

    python3 plan/validate.py           # prints the target table; exit code 1 on any hard error or missed target

Hard errors: gaps or overlaps between shots, first shot not at 0, last shot not at the film end, a narration line not covered,
a shot shorter than 0.3 s, camera keys outside their shot, rule cards moved (DIRECTION_V2 5.3 table, +-0.05 s) or not 0.42-0.48 s
before "Rule" / not cut 0.1-0.2 s after the sentence, a caption under a rule card, a hold missing or not covering its brief time,
an error number 1-33 with no shot, an SFX name not declared, a cue outside the film, a shot without world / look / class /
energy, a bad Queen stage, a travelling shot (cam3) on a set that has no 3D room.
Targets: FLOW OVER CUT COUNT (the owner's v2 verdict; critic round 1). The old cut-rate targets (36-40 cuts/min, shot p50
1.4-1.6 s, flash and punch-in rates) are gone: they are printed for information only. The checks are continuity checks:
jump cuts (adjacent shots on the same set and view) <= 3 % of the cuts unless flagged match_action; world switches <= 6 in
any 60 s outside the flagged parallel-action blocks (the porch / THEIRS cross-cut 500-537 s and the hook's teaser burst);
no more than 2 consecutive close-ups on the bokeh plate; memory runs >= 2.5 s; snap punch-ins <= 3 in the film. Printed as a
table with PASS / MISS; any MISS also fails the run.
Warnings: acting / HUD / SFX times outside their own shot, the left-hand fist rule (323.65-649 s), the Queen ladder order.
"""
import json, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
D = json.load(open(os.path.join(HERE, 'shots.json')))
SP = json.load(open(os.path.join(HERE, 'sound_plan.json')))
TL = json.load(open(os.path.join(FILM, '_work', 'align', 'timeline.json')))
shots, meta = D['shots'], D['meta']
END = meta['duration']
MIN = END / 60
err, warn, rows = [], [], []


def q(xs, p):
    xs = sorted(xs)
    k = (len(xs) - 1) * p
    i = int(k)
    return xs[i] if i + 1 >= len(xs) else xs[i] + (xs[i + 1] - xs[i]) * (k - i)


def target(name, value, lo, hi, fmt='%.1f', note=''):
    ok = (lo is None or value >= lo - 1e-9) and (hi is None or value <= hi + 1e-9)
    rng = ('%s-%s' % (fmt % lo, fmt % hi)) if lo is not None and hi is not None else (('>= ' + fmt % lo) if lo is not None else ('<= ' + fmt % hi))
    rows.append((name, fmt % value, rng, 'PASS' if ok else 'MISS', note))
    return ok


# ---------------------------------------------------------------- continuity
if abs(shots[0]['t0']) > 1e-6: err.append('first shot starts at %.3f' % shots[0]['t0'])
if abs(shots[-1]['t1'] - END) > 1e-6: err.append('last shot ends at %.3f, film end %.3f' % (shots[-1]['t1'], END))
for a, b in zip(shots, shots[1:]):
    if abs(a['t1'] - b['t0']) > 1e-6: err.append('%s -> %s: gap/overlap %.3f' % (a['id'], b['id'], b['t0'] - a['t1']))
    if b['t0'] < a['t0']: err.append('%s starts before %s' % (b['id'], a['id']))
STAGES = {'S0', 'S1', 'S2', 'S3a', 'S3b', 'S3c', 'OFF', 'S4', None}
for s in shots:
    if s['dur'] < 0.3: err.append('%s too short (%.2f s)' % (s['id'], s['dur']))
    k = s['cam']['keys']
    if (k[0][0] < s['t0'] - 1e-3 or k[-1][0] > s['t1'] + 1e-3) and s['cam'].get('move') != 'path':   # a path spans its group
        err.append('%s camera keys outside the shot' % s['id'])
    for f in ('energy', 'world', 'look', 'cls'):
        if not s.get(f): err.append('%s has no %s' % (s['id'], f))
    if s['dur'] > 14.0 + 1e-6 and s['type'] != 'CARD':
        warn.append('%s is %.2f s long' % (s['id'], s['dur']))
    if s.get('cam3') and s['set'] not in ('cabin_now', 'cabin_dawn', 'stairs', 'mirror'):
        err.append('%s travels (cam3) on %s, which has no 3D room' % (s['id'], s['set']))
    if s.get('queen') and s['queen'].get('stage') not in STAGES: err.append('%s queen stage %r' % (s['id'], s['queen']['stage']))
    for c in s['chars']:
        if c['who'] == 'queen' and c.get('stage') not in STAGES: err.append('%s queen char stage %r' % (s['id'], c.get('stage')))

# ---------------------------------------------------------------- line coverage
covered = set()
for s in shots: covered.update(s['lines'])
missing = [L['i'] for L in TL['lines'] if L['i'] not in covered]
if missing: err.append('lines not covered: %s' % missing)

# ---------------------------------------------------------------- rule cards (times unchanged)
BRIEF_CARDS = {1: (129.80, 133.56), 2: (203.53, 208.32), 3: (269.24, 273.35), 4: (350.38, 353.53), 5: (446.33, 449.74), 6: (542.03, 545.22), 7: (609.48, 614.71)}
cards = D['rule_cards']
if [c['n'] for c in cards] != list(range(1, 8)): err.append('rule cards: %s' % [c['n'] for c in cards])
for c in cards:
    a, b = BRIEF_CARDS[c['n']]
    if abs(c['appear'] - a) > 0.05 or abs(c['cut'] - b) > 0.05: err.append('rule %d at %.2f-%.2f, brief %.2f-%.2f' % (c['n'], c['appear'], c['cut'], a, b))
    if not (0.42 - 1e-3 <= c['lead'] <= 0.48 + 1e-3): err.append('rule %d appears %.3f s before "Rule"' % (c['n'], c['lead']))
    tail = c['cut'] - c['sentence_end']
    if not (0.1 - 1e-3 <= tail <= 0.2 + 1e-3): err.append('rule %d cut %.3f s after the sentence' % (c['n'], tail))
card_rng = [(c['appear'], c['cut']) for c in cards]
for cap in D['captions']:
    for a, b in card_rng:
        if cap['t0'] < b - 1e-3 and cap['t1'] > a + 1e-3: err.append('caption under rule card: %s' % cap['text'])

# ---------------------------------------------------------------- holds
for h in D['holds']:
    if not h['shot']: err.append('hold %s has no shot' % h['id']); continue
    a, b, ln = h['brief']
    if h['t0'] > a + 0.25 or h['t1'] < b - 0.25:            # a hold may now sit inside a longer continuous shot
        err.append('hold %s at %.2f-%.2f (%.2f s) does not cover its brief %.1f-%.1f (%.1f s)' % (h['id'], h['t0'], h['t1'], h['dur'], a, b, ln))
held = [s for s in shots if s.get('hold')]
if len(held) != 10: err.append('%d hold shots, want 10' % len(held))

# ---------------------------------------------------------------- errors 1-33
for n, v in D['errors'].items():
    if not v['shots']: err.append('error %s (%s) has no fixing shot' % (n, v['error']))

# ---------------------------------------------------------------- inner timing warnings, the fist rule, the ladder
for s in shots:
    for ch in s['chars']:
        for at, clip, p in ch['acts']:
            if isinstance(at, (int, float)) and not (s['t0'] - 2.5 <= at <= s['t1'] + 0.5):
                warn.append('%s %s %s at %.2f outside shot %.2f-%.2f' % (s['id'], ch['who'], clip, at, s['t0'], s['t1']))
            if ch['who'] == 'you' and clip in ('open_fist', 'open_hand') and at < 649.0 and ch.get('hand') == 'left':
                warn.append('%s: your left hand opens at %.2f (the fist holds to 649 s)' % (s['id'], at))
        if ch['who'] == 'you' and ch.get('mode') == 'hands' and 323.65 <= s['t0'] < 648.9 and ch.get('hand') == 'left' and not ch.get('fist'):
            warn.append('%s: your left hand shown without the candy fist (323.65-649 s)' % s['id'])
    for h in s['hud']:
        if not (s['t0'] - 0.05 <= h['t'] <= s['t1'] + 0.05) and h['type'] not in ('rule_card',):
            warn.append('%s hud %s at %.2f outside shot' % (s['id'], h['type'], h['t']))
ORDER = {'S0': 0, 'S1': 1, 'S2': 2, 'S3a': 3, 'S3b': 4, 'S3c': 5, 'OFF': 5, 'S4': 6}
top = 0
for s in shots:
    qd = s.get('queen')
    if not qd or s.get('teaser') or s['type'] == 'CARD' or s.get('past') or not qd.get('stage'): continue
    o = ORDER[qd['stage']]
    if o < top and qd['stage'] != 'S3c': warn.append('%s queen at %s after %s was reached' % (s['id'], qd['stage'], [k for k, v in ORDER.items() if v == top][0]))
    top = max(top, o)

# ---------------------------------------------------------------- sound
names = set(SP['names']['existing']) | set(SP['names']['new'])
for c in SP['sfx']:
    if c['name'] not in names: err.append('sfx name %s not declared' % c['name'])
    if not (0 <= c['t'] <= END): err.append('sfx %s at %.2f outside the film' % (c['name'], c['t']))
for s in shots:
    for c in s['sfx']:
        if not (s['t0'] - 0.6 <= c['t'] <= s['t1'] + 0.6): warn.append('%s sfx %s at %.2f outside shot' % (s['id'], c['name'], c['t']))

# ================================================================ the numbers
real = [s for s in shots if s['type'] not in ('CARD', 'BLACK')]
durs = [s['dur'] for s in shots if s['type'] != 'BLACK']
cuts = len(shots) - 1
clause = [s for s in shots[1:] if s['cut_on_clause']]
leads = [-s['clause_offset'] for s in clause]
cls = {}
for s in real: cls[s['cls']] = cls.get(s['cls'], 0) + 1
n = len(real)
first30 = len([s for s in shots[1:] if s['t0'] < 30.0])
def cpm(a, b):
    ss = [s for s in shots if a <= s['t0'] < b]
    return len(ss) / ((b - a) / 60)
push = [s['cam']['rate_pct_s'] for s in real if s['cam']['rate_pct_s'] >= 0.5]
pulls = [s for s in real if s['cam']['rate_pct_s'] <= -0.5]
static = [s for s in real if abs(s['cam']['rate_pct_s']) < 0.5 and s['cam']['pan_px_s'] < 8 and s['cam'].get('shake', 0) < 10]
flash = len([s for s in shots[1:] if s['tr'] in ('white', 'glitch', 'rewind', 'pixelsort') and s['type'] != 'CARD'])
flash += len([f for s in shots for f in (s.get('fx_post') or []) if f.get('white', 0) >= 0.5 or f.get('glitch', 0) >= 0.5 or f.get('rewind')])
punch = len([s for s in shots if s['cam'].get('snap')])
glints = len([s for s in shots if s.get('glint')])
devices = len([s for s in shots if s.get('device')])
reuse_x = len([s for s in real if s.get('reuse')])
reuse_angle = len([s for s in real if s.get('setup_reused') and s['cls'] in ('wide', 'mid')])
over3 = [s for s in shots if s['dur'] > 3.0]
caps = D['captions']
cw = [len(c['text'].split()) for c in caps]
cd = [c['t1'] - c['t0'] for c in caps]
oncut = len([c for c in caps if c.get('on_cut')])
# re-establishing wides after the cards and the side switches
after_card = [shots[i + 1] for i, s in enumerate(shots[:-1]) if s['type'] == 'CARD']
card_wide = len([s for s in after_card if s['cls'] == 'wide'])
blocks, cur, prevfam = [], None, None
for s in shots:
    f = s.get('family')
    if not f: continue
    if f != prevfam:
        cur = [s]; blocks.append(cur); prevfam = f
    else:
        cur.append(s)
switch_blocks = [b for b in blocks[1:] if sum(x['dur'] for x in b) >= 2.0 and len(b) >= 2]
switch_wide = len([b for b in switch_blocks if any(x['cls'] == 'wide' for x in b[:2])])
xs = sum(1 for s in shots for h in s['hud'] if h['type'] == 'red_x')
tags = sum(1 for s in shots for h in s['hud'] if h['type'] == 'tag')
labels = sum(1 for s in shots for h in s['hud'] if h['type'] == 'label')
faces = [s for s in real if s['cls'] == 'face']

# ---------------------------------------------------------------- continuity measures (the new direction)
def wfam(s):
    if s['type'] in ('CARD', 'BLACK'): return None
    if s['world'] in ('theirs', 'theirs_break') or (s['world'] == 'climax' and s['side'] == 'theirs'): return 'theirs'
    if s['world'] == 'memory': return 'memory'
    if s['world'] == 'stairs' and s['set'] == 'stairs': return 'stairs'
    return 'ours'
PARALLEL = [(500.0, 537.5), (0.0, 16.06)]        # the porch / THEIRS cross-cut; the hook's flash-forward burst
def parallel(tt): return any(a_ <= tt < b_ for a_, b_ in PARALLEL) or False
switches, prevf = [], None
for s in shots:
    f = wfam(s)
    if f is None: continue
    if prevf is not None and f != prevf and not parallel(s['t0']) and not s.get('parallel') and not s.get('teaser'): switches.append(s['t0'])
    prevf = f
worst60, worst_at = 0, 0.0
for t_ in switches:
    nn = len([x for x in switches if t_ <= x < t_ + 60.0])
    if nn > worst60: worst60, worst_at = nn, t_
def subj(s):
    return {c['who'] for c in s['chars'] if c.get('mode', 'body') in ('body', 'bust', 'legs', 'silhouette') and not c.get('reflection')}
# a jump cut: the same set and view and the same people (or nobody) on both sides; a cut to the other person on the same
# plate is a reverse (shot / reverse shot), not a jump; UI screens are excluded
jumps = [(a_['id'], b_['id']) for a_, b_ in zip(shots, shots[1:]) if (a_['set'], a_['view']) == (b_['set'], b_['view'])
         and a_['type'] not in ('CARD', 'BLACK') and not b_.get('match_action') and a_['set'] not in ('ui',)
         and (subj(a_) & subj(b_) or not (subj(a_) or subj(b_)))]
bok, run_, worst_bok, worst_bok_at = 0, 0, 0, ''
for s in shots:
    if s['view'] == 'bokeh' and s['cls'] == 'face':
        run_ += 0 if s.get('resumes') else 1          # a close-up resuming its own move after a reaction is the same shot
        if run_ > worst_bok: worst_bok, worst_bok_at = run_, s['id']
    else: run_ = 0
mem_runs, cur_ = [], None
for s in shots:
    if s['world'] == 'memory':
        if cur_ is None: cur_ = [s['t0'], s['t1'], s['id']]
        else: cur_[1] = s['t1']
    else:
        if cur_ is not None: mem_runs.append(cur_); cur_ = None
short_mem = [(m[2], round(m[1] - m[0], 2)) for m in mem_runs if m[1] - m[0] < 2.5 - 1e-6]
travelling = [s for s in shots if s.get('cam3')]
merged = [s for s in shots if s.get('merged') and len(s['merged']) > 1]
flows = [s for s in shots if s['tr'] == 'flow']

print('TARGETS (flow over cut count)  %d shots, %.2f min' % (len(shots), MIN))
target('jump cuts: adjacent shots on the same set and view (% of cuts)', 100 * len(jumps) / max(1, cuts), None, 3.0, '%.1f',
       ', '.join('%s>%s' % j for j in jumps[:8]))
target('world switches per minute (outside the parallel blocks)', len(switches) / MIN, None, 6.0, '%.1f',
       'worst 60 s: %d from %.1f s' % (worst60, worst_at))
target('consecutive close-ups on the bokeh plate (max)', worst_bok, None, 2, '%d', 'ending at %s' % worst_bok_at)
target('memory runs shorter than 2.5 s', len(short_mem), None, 0, '%d', ', '.join('%s %.2f' % m for m in short_mem[:8]))
target('snap punch-ins in the film', punch, None, 3, '%d', 'eased push accelerations on the other word beats')
target('rule cards in place', len(cards), 7, 7, '%d')
target('holds (H1-H10)', len(held), 10, 10, '%d')
target('red X', xs, 4, 4, '%d')
target('command tags', tags, 6, 6, '%d')
target('errors 1-33 mapped to shots', len([1 for v in D['errors'].values() if v['shots']]), 33, 33, '%d')
target('lines covered', len(covered & {L['i'] for L in TL['lines']}), len(TL['lines']), len(TL['lines']), '%d')
target('CU/ECU on a bokeh plate (%)', 100 * len([s for s in faces if s.get('bokeh')]) / max(1, len(faces)), 90, None, '%.0f', 'shots[].bokeh')
print('INFO   cuts %d (%.1f /min), shot p10/p50/p90 %.2f / %.2f / %.2f s, merged shots %d (from %d), travelling shots (cam3) %d, '
      'flow joins %d, world switches %d (%.1f /min), captions %d' % (
          cuts, cuts / MIN, q(durs, .1), statistics.median(durs), q(durs, .9), len(merged), sum(len(s['merged']) for s in merged),
          len(travelling), len(flows), len(switches), len(switches) / MIN, len(caps)))
w = max(len(r[0]) for r in rows)
for name, val, rng, ok, note in rows:
    print('  %-*s  %9s   %-13s %s  %s' % (w, name, val, rng, ok, note))
st = SP['stats']
print('SOUND  %d cues (%.1f /min; v1 %d, v2 shots %d, devices %d), %d hit events (%.1f /min), silences %d, swells %d, risers %d, names %d (%d new v2)' % (
    st['cues'], st['per_min'], st['from_v1'], st['from_v2_shots'], st['from_devices'], st['hits'], st['hits_per_min'], st['silences'], st['rises'],
    st['risers'], st['names_used'], st['new_v2_names_used']))
dev = {}
for c in SP['sfx']:
    if c.get('origin') == 'device': dev[c['name']] = dev.get(c['name'], 0) + 1
print('       device cues: ' + ', '.join('%s %d' % kv for kv in sorted(dev.items(), key=lambda kv: -kv[1])))
print('RULES  ' + '  '.join('#%d %s %.2f-%.2f' % (c['n'], c['shot'], c['appear'], c['cut']) for c in cards))
print('HOLDS  ' + '  '.join('%s %s %.2f-%.2f (%.2f)' % (h['id'], h['shot'], h['t0'], h['t1'], h['dur']) for h in D['holds']))
if warn:
    print('WARN   %d' % len(warn))
    for x in warn[:40]: print('   ', x)
miss = [r for r in rows if r[3] == 'MISS']
if err or miss:
    if err:
        print('ERRORS %d' % len(err))
        for x in err[:60]: print('   ', x)
    if miss: print('MISSED TARGETS %d: %s' % (len(miss), ', '.join(r[0] for r in miss)))
    sys.exit(1)
print('OK: every target met')
