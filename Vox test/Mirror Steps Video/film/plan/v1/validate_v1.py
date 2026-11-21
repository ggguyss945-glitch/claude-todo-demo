"""plan/validate.py: check plan/shots.json and plan/sound_plan.json against the timeline and the reference targets.

    python3 plan/validate.py           # prints the numbers; exit code 1 on any hard error

Hard errors: gaps or overlaps between shots, first shot not at 0, last shot not at the film end, a narration line not
covered, a shot shorter than 0.3 s, camera keys outside their shot, rule cards not 0.42-0.48 s before "Rule" or not cut
0.1-0.2 s after the sentence, a caption under a rule card, an SFX cue outside the film, an SFX name not declared.
Warnings: acting / HUD / SFX times that fall outside their own shot (they may be deliberate tails).
"""
import json, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
D = json.load(open(os.path.join(HERE, 'shots.json')))
SP = json.load(open(os.path.join(HERE, 'sound_plan.json')))
TL = json.load(open(os.path.join(FILM, '_work', 'align', 'timeline.json')))
shots, meta = D['shots'], D['meta']
END = meta['duration']
err, warn = [], []


def q(xs, p):
    xs = sorted(xs)
    k = (len(xs) - 1) * p
    i = int(k)
    return xs[i] if i + 1 >= len(xs) else xs[i] + (xs[i + 1] - xs[i]) * (k - i)


# ---------------------------------------------------------------- continuity
if abs(shots[0]['t0']) > 1e-6: err.append('first shot starts at %.3f' % shots[0]['t0'])
if abs(shots[-1]['t1'] - END) > 1e-6: err.append('last shot ends at %.3f, film end %.3f' % (shots[-1]['t1'], END))
for a, b in zip(shots, shots[1:]):
    if abs(a['t1'] - b['t0']) > 1e-6: err.append('%s -> %s: gap/overlap %.3f' % (a['id'], b['id'], b['t0'] - a['t1']))
    if b['t0'] < a['t0']: err.append('%s starts before %s' % (b['id'], a['id']))
for s in shots:
    if s['dur'] < 0.3: err.append('%s too short (%.2f s)' % (s['id'], s['dur']))
    k = s['cam']['keys']
    if k[0][0] < s['t0'] - 1e-3 or k[-1][0] > s['t1'] + 1e-3: err.append('%s camera keys outside the shot' % s['id'])
    if not s.get('energy'): err.append('%s has no energy note' % s['id'])

# ---------------------------------------------------------------- line coverage
covered = set()
for s in shots: covered.update(s['lines'])
missing = [L['i'] for L in TL['lines'] if L['i'] not in covered]
if missing: err.append('lines not covered: %s' % missing)
for L in TL['lines']:
    if L['end'] > END + 1e-6: err.append('line %d ends after the film' % L['i'])

# ---------------------------------------------------------------- rule cards
cards = D['rule_cards']
if [c['n'] for c in cards] != list(range(1, 8)): err.append('rule cards: %s' % [c['n'] for c in cards])
for c in cards:
    if not (0.42 - 1e-3 <= c['lead'] <= 0.48 + 1e-3): err.append('rule %d appears %.3f s before "Rule"' % (c['n'], c['lead']))
    tail = c['cut'] - c['sentence_end']
    if not (0.1 - 1e-3 <= tail <= 0.2 + 1e-3): err.append('rule %d cut %.3f s after the sentence' % (c['n'], tail))
card_rng = [(c['appear'], c['cut']) for c in cards]
for cap in D['captions']:
    for a, b in card_rng:
        if cap['t0'] < b - 1e-3 and cap['t1'] > a + 1e-3: err.append('caption under rule card: %s' % cap['text'])

# ---------------------------------------------------------------- inner timing warnings
for s in shots:
    for ch in s['chars']:
        for at, clip, p in ch['acts']:
            if isinstance(at, (int, float)) and not (s['t0'] - 2.5 <= at <= s['t1'] + 0.5):
                warn.append('%s %s %s at %.2f outside shot %.2f-%.2f' % (s['id'], ch['who'], clip, at, s['t0'], s['t1']))
    for h in s['hud']:
        if not (s['t0'] - 0.05 <= h['t'] <= s['t1'] + 0.05): warn.append('%s hud %s at %.2f outside shot' % (s['id'], h['type'], h['t']))
    for c in s['sfx']:
        if not (s['t0'] - 0.6 <= c['t'] <= s['t1'] + 0.6): warn.append('%s sfx %s at %.2f outside shot %.2f-%.2f' % (s['id'], c['name'], c['t'], s['t0'], s['t1']))

# ---------------------------------------------------------------- sound
names = set(SP['names']['existing']) | set(SP['names']['new'])
for c in SP['sfx']:
    if c['name'] not in names: err.append('sfx name %s not declared' % c['name'])
    if not (0 <= c['t'] <= END): err.append('sfx %s at %.2f outside the film' % (c['name'], c['t']))

# ---------------------------------------------------------------- numbers
real = [s for s in shots if s['side'] != 'black']
durs = [s['dur'] for s in real]
mins = END / 60
cuts = len(shots) - 1
moving = [s for s in real if abs(s['cam']['rate_pct_s']) >= 0.5 or s['cam']['pan_px_s'] >= 8 or s['cam'].get('shake', 0) >= 10]
push_t = sum(s['dur'] for s in real if s['cam']['rate_pct_s'] >= 0.5)
pull_t = sum(s['dur'] for s in real if s['cam']['rate_pct_s'] <= -0.5)
move_t = sum(s['dur'] for s in moving)
push_rates = [s['cam']['rate_pct_s'] for s in real if s['cam']['rate_pct_s'] > 0.5]
clause = [s for s in shots[1:] if s['cut_on_clause']]
hard = [s for s in shots[1:] if s['tr'] in ('cut', 'glitch', 'black', 'white')]
soft = [s for s in shots[1:] if s['tr'] in ('dissolve',)]
tags = sum(1 for s in shots for h in s['hud'] if h['type'] == 'tag')
xs = sum(1 for s in shots for h in s['hud'] if h['type'] == 'red_x')
labels = sum(1 for s in shots for h in s['hud'] if h['type'] == 'label')
inserts = sum(1 for s in shots if s['type'] in ('INSERT', 'UI'))
types = {}
for s in real: types[s['type']] = types.get(s['type'], 0) + 1
sides = {}
for s in real: sides[s['side']] = round(sides.get(s['side'], 0) + s['dur'], 1)
caps = D['captions']
cw = [len(c['text'].split()) for c in caps]
cd = [c['t1'] - c['t0'] for c in caps]
st = SP['stats']

print('SHOTS  %d shots (%d cuts) over %.2f s = %.1f cuts/min' % (len(shots), cuts, END, cuts / mins))
print('       length mean %.2f median %.2f  p10 %.2f p25 %.2f p75 %.2f p90 %.2f  min %.2f max %.2f' % (
    statistics.mean(durs), statistics.median(durs), q(durs, .1), q(durs, .25), q(durs, .75), q(durs, .9), min(durs), max(durs)))
print('       < 1 s %.0f %%   > 4 s %.0f %%   > 6 s %.0f %%' % (100 * sum(d < 1 for d in durs) / len(durs), 100 * sum(d > 4 for d in durs) / len(durs),
                                                           100 * sum(d > 6 for d in durs) / len(durs)))
print('CUTS   on a clause start (-0.35..+0.15 s): %.0f %%   hard %.0f %%  soft %.0f %%' % (100 * len(clause) / cuts, 100 * len(hard) / cuts, 100 * len(soft) / cuts))
print('MOTION camera moving %.0f %% of the time; push %.0f %%, pull %.0f %% of moving time; push rate median %.1f %%/s p90 %.1f' % (
    100 * move_t / sum(durs), 100 * push_t / move_t, 100 * pull_t / move_t, statistics.median(push_rates), q(push_rates, .9)))
print('TYPES  %s' % ', '.join('%s %d' % kv for kv in sorted(types.items(), key=lambda kv: -kv[1])))
print('SIDES  seconds: %s' % sides)
print('HUD    command tags %d, red X %d, labels %d (%.1f /min together); inserts + UI %d (%.1f /min)' % (tags, xs, labels, (tags + xs) / mins, inserts, inserts / mins))
print('CAPS   %d captions, words median %d (p10 %d p90 %d), length median %.2f s (p10 %.2f p90 %.2f)' % (
    len(caps), statistics.median(cw), q(cw, .1), q(cw, .9), statistics.median(cd), q(cd, .1), q(cd, .9)))
print('RULES  ' + '  '.join('#%d %s %.2f-%.2f (lead %.2f, tail %.2f)' % (c['n'], c['shot'], c['appear'], c['cut'], c['lead'], c['cut'] - c['sentence_end']) for c in cards))
print('SOUND  %d cues (%.1f /min), %d hit events (%.1f /min, %d hit cues), one-shots %.1f /min, silences %d (%.2f /min, median %.2f s)' % (
    st['cues'], st['per_min'], st['hits'], st['hits_per_min'], st['hit_cues'], st['one_shots_per_min'], st['silences'], st['silences_per_min'], st['silence_len_median']))
print('       swells %d (%.2f /min, median %.1f s), rule risers %d, names used %d (%d new)' % (st['rises'], st['rises_per_min'], st['rise_len_median'],
    st['risers'], st['names_used'], st['new_names_used']))
print('LINES  %d of %d covered' % (len(covered & {L['i'] for L in TL['lines']}), len(TL['lines'])))
if warn:
    print('WARN   %d' % len(warn))
    for x in warn[:40]: print('   ', x)
if err:
    print('ERRORS %d' % len(err))
    for x in err[:60]: print('   ', x)
    sys.exit(1)
print('OK')
