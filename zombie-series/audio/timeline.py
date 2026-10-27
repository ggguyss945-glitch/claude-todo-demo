# Master timeline for the 60 s test, derived from voice.json so picture and sound stay in sync.
# usage: python3 -I timeline.py <voice.json> <out timeline.json>
import json, sys

V = json.load(open(sys.argv[1]))
L = {l['id']: l for l in V['lines']}
s = lambda i: L[i]['start']
e = lambda i: L[i]['start'] + L[i]['dur']
w = lambda i, word: L[i]['start'] + next(x['t'] for x in L[i]['words'] if x['w'].lower().strip("'") == word)

DUR = 60.0
PA_START, PA_CUT = 2.8, 5.95            # PA voice is cut off by the switch
SWITCH = PA_CUT
RING = w('L12', 'ring')                 # alarm clock starts exactly on the word
TITLE = e('L13') + 0.55

shots = [
    ('pov_open',        0.0,              9.55),
    ('aisle_frozen',    9.55,             s('L3') - 0.2),
    ('zombies_turn',    s('L3') - 0.2,    s('L3') + 2.3),
    ('hero_where',      s('L3') + 2.3,    s('L4') - 0.25),
    ('exterior',        s('L4') - 0.25,   s('L5') - 0.1),
    ('shutter_hands',   s('L5') - 0.1,    s('L6') - 0.22),
    ('gary',            s('L6') - 0.22,   s('L7') - 0.15),
    ('hero_deadpan',    s('L7') - 0.15,   s('L8') - 0.25),
    ('counting',        s('L8') - 0.25,   s('L9a') - 0.2),
    ('inventory',       s('L9a') - 0.2,   s('L11') - 0.28),
    ('rule',            s('L11') - 0.28,  s('L12') - 0.25),
    ('aisle_alarm',     s('L12') - 0.25,  RING + 0.05),
    ('zombies_snap',    RING + 0.05,      s('L13') - 0.02),
    ('hero_alarm',      s('L13') - 0.02,  TITLE),
    ('title',           TITLE,            DUR),
]
shots = [{'name': n, 'start': round(a, 3), 'end': round(b, 3)} for n, a, b in shots]

events = {
    'pa_start': PA_START, 'pa_cut': PA_CUT, 'switch': SWITCH,
    'steps_start': 3.5, 'steps_stop': 8.2, 'last_step': 8.75,
    'boom_where': w('L3', 'are') + 0.05,
    'hud_in': s('L4') + 0.2,
    'gary_silence': e('L6') + 0.05, 'pizz_sting': e('L7') + 0.12,
    'count_tick': w('L8', 'count'),
    'item_cans': w('L9a', 'cans'), 'item_water': w('L9b', 'water'), 'item_batt': w('L9c', 'batteries'),
    'problem_hit': s('L10') + 0.1,
    'rule_slam': s('L11') + 0.05,
    'heart_start': s('L11') + 0.4,
    'ring': RING, 'flicker1': s('L13') + 0.55, 'flicker2': s('L13') + 1.05,
    'title': TITLE, 'silence': DUR - 1.2,
}
json.dump({'dur': DUR, 'shots': shots, 'events': {k: round(v, 3) for k, v in events.items()}, 'voice': V}, open(sys.argv[2], 'w'), indent=1)
for sh in shots: print(f"{sh['name']:15s} {sh['start']:6.2f} - {sh['end']:6.2f}  ({sh['end']-sh['start']:.2f}s)")
print({k: round(v, 2) for k, v in events.items()})
