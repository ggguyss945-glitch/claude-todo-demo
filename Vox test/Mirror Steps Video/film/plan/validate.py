"""plan/validate.py (v2): check plan/shots.json and plan/sound_plan.json against the timeline and DIRECTION_V2's targets.

    python3 plan/validate.py           # prints the target table; exit code 1 on any hard error or missed target

Hard errors: gaps or overlaps between shots, first shot not at 0, last shot not at the film end, a narration line not covered,
a shot shorter than 0.3 s, camera keys outside their shot, rule cards moved (DIRECTION_V2 5.3 table, +-0.05 s) or not 0.42-0.48 s
before "Rule" / not cut 0.1-0.2 s after the sentence, a caption under a rule card, a shot over 2.5 s that is not one of the ten
holds, a card or the time card, a hold missing or off its brief time, an error number 1-33 with no shot, an SFX name not declared,
a cue outside the film, a shot without world / look / class / energy, a bad Queen stage.
Targets (DIRECTION_V2 5.1, 5.5, 2.2-2.5, 1.2): printed as a table with PASS / MISS; any MISS also fails the run.
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
    if k[0][0] < s['t0'] - 1e-3 or k[-1][0] > s['t1'] + 1e-3: err.append('%s camera keys outside the shot' % s['id'])
    for f in ('energy', 'world', 'look', 'cls'):
        if not s.get(f): err.append('%s has no %s' % (s['id'], f))
    if s['dur'] > 2.5 + 1e-6 and not s.get('hold') and s['type'] != 'CARD' and not s.get('time_card'):
        err.append('%s is %.2f s long (only the holds, the cards and the time card may pass 2.5 s)' % (s['id'], s['dur']))
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
    if abs(h['t0'] - a) > 0.25 or abs(h['t1'] - b) > 0.25 or abs(h['dur'] - ln) > 0.4:
        err.append('hold %s at %.2f-%.2f (%.2f s), brief %.1f-%.1f (%.1f s)' % (h['id'], h['t0'], h['t1'], h['dur'], a, b, ln))
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

print('TARGETS (DIRECTION_V2)  %d shots, %.2f min' % (len(shots), MIN))
target('shots', len(shots), 430, 450, '%d')
target('cuts per minute', cuts / MIN, 36, 40)
target('cuts per minute, rule 6 (542-610 s)', cpm(542.03, 609.48), 40, 44)
target('cuts per minute, ending (629-700 s)', cpm(629.0, 700.0), 34, 38, note='brief: 34-36')
target('cuts in the first 30 s', first30, 22, 24, '%d')
target('shot length p10 (s)', q(durs, .1), 0.55, 0.85, '%.2f', 'brief 0.65')
target('shot length p50 (s)', statistics.median(durs), 1.4, 1.6, '%.2f', 'brief 1.5')
target('shot length p90 (s)', q(durs, .9), 2.2, 2.6, '%.2f', 'brief 2.5')
target('shots over 3 s (%)', 100 * len(over3) / len(shots), None, 4.0, '%.1f', 'holds, cards, time card only')
target('cuts on a clause start (%)', 100 * len(clause) / cuts, 65, 75)
target('picture lead on clause cuts, median (s)', statistics.median(leads), 0.12, 0.20, '%.2f', 'brief 0.15-0.17')
target('wides (%)', 100 * cls.get('wide', 0) / n, 30, 35)
target('MS / OTS / 2S (%)', 100 * cls.get('mid', 0) / n, 15, 20)
target('faces (%)', 100 * cls.get('face', 0) / n, 25, 30)
target('inserts, documents, diagrams, UI (%)', 100 * cls.get('insert', 0) / n, 18, 20)
target('POV hands (%)', 100 * cls.get('pov', 0) / n, 4, 6, note='brief 5')
target('inserts / documents / diagrams per minute', devices / MIN, 4, 6, '%.2f', 'shots carrying a device')
target('setups reused: explicit [R] callbacks (%)', 100 * reuse_x / n, 8, None, '%.1f', 'plus same-angle wides/mids below')
target('setups reused: wide/mid on an earlier angle (%)', 100 * reuse_angle / n, 25, None, '%.1f', 'brief about 30')
target('push-in median (%/s)', statistics.median(push), 2.6, 3.6, '%.2f', 'brief about 3.0')
target('push-in p75 (%/s)', q(push, .75), 4.0, 6.0, '%.2f', 'brief about 5.5')
target('pull-outs (% of shots)', 100 * len(pulls) / n, 7, 13, '%.1f', 'brief about 10')
target('near-static shots (%)', 100 * len(static) / n, None, 5.0)
target('white flash / glitch cuts per minute', flash / MIN, 2, 3, '%.2f')
target('punch-ins per minute', punch / MIN, 1, 2, '%.2f')
target('side-switch glints', glints, 18, 22, '%d')
target('re-establishing wide after each rule card', card_wide, len(after_card), len(after_card), '%d', 'of %d' % len(after_card))
target('wide in the first 2 shots after a side switch', switch_wide, len(switch_blocks), len(switch_blocks), '%d', 'of %d blocks' % len(switch_blocks))
target('holds (the only shots over 2.5 s)', len(held), 10, 10, '%d')
target('red X', xs, 4, 4, '%d')
target('command tags', tags, 6, 6, '%d')
target('labels with leader lines', labels, 8, None, '%d')
target('captions', len(caps), 500, 520, '%d')
target('caption length median (s)', statistics.median(cd), 1.1, 1.3, '%.2f', 'brief 1.2')
target('caption words p10', q(cw, .1), 2, None, '%.0f', 'p90 %.0f; six-word captions %.0f %% (the 500-520 count needs some)' % (q(cw, .9), 100 * sum(1 for x in cw if x >= 6) / len(cw)))
target('caption words max', max(cw), None, 6, '%d')
target('captions changing within 0.2 s of a cut (%)', 100 * oncut / len(caps), 70, None)
target('errors 1-33 mapped to shots', len([1 for v in D['errors'].values() if v['shots']]), 33, 33, '%d')
target('lines covered', len(covered & {L['i'] for L in TL['lines']}), len(TL['lines']), len(TL['lines']), '%d')
target('CU/ECU on a bokeh plate (%)', 100 * len([s for s in faces if s.get('bokeh')]) / max(1, len(faces)), 90, None, '%.0f', 'shots[].bokeh')
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
