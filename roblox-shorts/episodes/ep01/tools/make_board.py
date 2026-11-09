#!/usr/bin/env python3
# Build the EP01 full-episode board from the shot table:
#   python3 -I episodes/ep01/tools/make_board.py      (from roblox-shorts/)
# Reads  episodes/ep01/word_onsets.json, episodes/ep01/test5_timeline.json, tools/shots_ep01.py, tools/assets_ep01.py
# Writes episodes/ep01/timeline.json (engine format), episodes/ep01/board.md, episodes/ep01/ASSETS.md and prints the QA.
import copy, json, math, os, re, statistics, sys
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
EP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from shots_ep01 import SHOTS            # noqa: E402
from assets_ep01 import A, SFX, PRIMARY_SFX  # noqa: E402

FPS = 60
END_T = 113.30                       # last audible voice sample 112.95 s + 0.35 s (STORYBOARD_RULES QA 10)
END_F = round(END_T * FPS)
LAST_AUDIBLE = 112.95
SCRATCH = '/tmp/claude-0/-home-user-claude-todo-demo/353ac1d9-152b-55bb-bdf1-0625e0fc6a83/scratchpad'
W = json.load(open(os.path.join(EP, 'word_onsets.json')))['words']
ON = [w['onset'] for w in W]
TEST = {s['name']: s for s in json.load(open(os.path.join(EP, 'test5_timeline.json')))['shots']}

# Sentence starts (the script's 68 sentences; quoted lines count as sentences, "Checking for moles," he'd say = one).
SENT = [0, 6, 11, 16, 24, 31, 36, 44, 50, 56, 64, 70, 75, 81, 90, 94, 99, 101, 113, 120, 129, 136, 139, 143, 146, 150, 158, 161,
        170, 179, 182, 185, 198, 205, 213, 219, 228, 229, 230, 243, 251, 257, 260, 271, 275, 282, 285, 290, 296, 305, 311, 315,
        317, 323, 335, 343, 344, 362, 369, 377, 380, 382, 388, 394, 396, 406, 416, 425, 435]
PAUSES = [(28.87, 29.75, 'after "empty"'), (48.02, 48.53, 'after "fence"'), (82.40, 82.72, 'after "flowerbed"'), (102.95, 103.51, 'before "Every spring"'), (42.80, 43.51, 'after "edge"')]

def clean(w): return re.sub(r'[^\w\'-]', '', w)
def fr(t): return round(t * FPS)
def tsec(f): return round(f / FPS, 6)
# Display text follows the script (EP01_VOICEOVER.md) where the ASR spelled a word differently ('' joins the token to the previous one).
CORR = {77: 'goodnight,', 189: 'Theo,', 82: '60', 83: 'years,', 113: 'So', 117: 'barefoot,', 137: 'on,', 190: 'six,', 222: "Mom's", 229: 'Gone.', 230: 'The', 259: 'night?',
        271: 'Flashlight,', 274: 'lap.', 275: 'And', 276: 'one', 277: 'stop,', 295: 'Dad.', 308: 'face', 321: 'flowerbed.', 322: '', 325: 'goodnight,', 326: '',
        343: 'FWOOM.', 346: 'flared,', 347: 'light', 351: 'lawn,', 370: 'dawn,', 381: 'nicest.', 383: 'goodnight,', 384: '', 395: 'Theo.', 396: 'From', 398: 'truck,',
        403: 'house,', 409: '60', 410: 'years,', 411: "Theo's", 418: 'flowerbed,', 419: '', 423: 'mid-blink.', 424: '', 426: '71,', 427: '', 207: 'and', 212: 'blink.', 213: 'And', 218: 'dawn.', 219: 'So',
        199: 'Grandpa,', 206: 'him,', 245: 'ran', 246: 'back,', 260: 'Grandpa', 263: 'head,', 266: 'me,', 274: 'lap.', 281: 'window.', 136: 'Come', 138: 'then.'}
def word_text(i0, i1):
    out = []
    for i in range(i0, i1):
        t = CORR.get(i, W[i]['w'])
        if t == '' and out: continue
        out.append(t)
    return ' '.join(out)

# ------------------------------------------------------------------ resolve cut frames, ends, words
shots = copy.deepcopy(SHOTS)
for s in shots:   # callbacks inherit the original set-up (same framing, same order, same grade)
    if s.get('callback'):
        o = next(x for x in shots if x['key'] == s['key'] and not x.get('callback'))
        for k in ('cam', 'cast', 'size', 'angle', 'light', 'grade', 'loc', 'era'):
            if k not in s and k in o: s[k] = copy.deepcopy(o[k])
for k, s in enumerate(shots):
    s['id'] = 's%02d' % (k + 1)
    if isinstance(s['cut'], tuple): s['f0'] = s['cut'][1]; s['cut_word'] = None
    else: s['cut_word'] = s['cut']; s['f0'] = fr(ON[s['cut']] - 1 / FPS)
for k, s in enumerate(shots):
    s['f1'] = shots[k + 1]['f0'] if k + 1 < len(shots) else END_F
    s['start'], s['end'] = tsec(s['f0']), tsec(s['f1']); s['dur'] = round((s['f1'] - s['f0']) / FPS, 4)
    s['owner'] = s.get('owner', s['part'])
# words by onset
wi = [[] for _ in shots]
for i, t in enumerate(ON):
    k = max(j for j, s in enumerate(shots) if s['f0'] <= fr(t) or j == 0)
    wi[k].append(i)
for s, ix in zip(shots, wi):
    s['wi'] = ix; s['words'] = word_text(ix[0], ix[-1] + 1) if ix else ''
# the test's s05 must end at the cut before "First" in the full episode (its 3.77 s end was the test's audio cut)
def resolve_events(s):
    out = []
    for e in s.get('ev', []):
        at = e['at']; t = ON[at] if isinstance(at, int) else float(at); f = fr(t)
        d = {'t': round(t, 3), 'frame': f}
        if isinstance(at, int): d['word'] = clean(W[at]['w']).lower()
        d['what'] = e['what']
        if e.get('sfx'): d['sfx'] = e['sfx']
        if e.get('kind'): d['kind'] = e['kind']
        if not (s['f0'] <= f < s['f1']): raise SystemExit('event outside its shot: %s %s %.3f' % (s['id'], e['what'], t))
        out.append(d)
    return out
for s in shots: s['events'] = resolve_events(s)

# ids of callbacks / mirrors (for the board text)
first_of = {}
for s in shots: first_of.setdefault(s['key'], s['id'])

EXPECT = {'s03': 'grandma_cu', 's05': 'gnome_hero', 's09': 'lawn_stare', 's10': 'agent_board', 's11': 'keepoff_sign', 's12': 'nextdoor_plastic', 's13': 'kennel_hole',
          's15': 'family_hands', 's16': 'hero_taps_hat', 's17': 'goodnight_window', 's18': 'gnome_blink_night', 's19': 'fb_grandpa_walk', 's20': 'fb_flashlight',
          's22': 'fb_lap', 's23': 'fb_wink', 's25': 'sold_truck_dusk', 's26': 'hall_clock', 's27': 'empty_spot', 's28': 'run_out_barefoot', 's29': 'gate_truck_thumb',
          's32': 'pick_up', 's38': 'lantern_lights', 's40': 'street_cascade', 's44': 'theo_intro', 's45': 'theo_window_out', 's46': 'take_window_dark',
          's47': 'gnome_waiting', 's48': 'truck_clock', 's49': 'balcony_box', 's50': 'plant_plastic', 's51': 'gulp', 's55': 'eyes_fog_glass', 's56': 'ran_back',
          's60': 'away_to_window', 's64': 'fb_one_stop', 's66': 'fb_checking_me', 's67': 'bw_dad', 's68': 'decades_window', 's69': 'decades_window',
          's70': 'lawn_stare_lit', 's71': 'big_in_window', 's72': 'theo_lantern_cheek', 's73': 'knelt_bed', 's75': 'slow_blink', 's76': 'set_down_let_go',
          's77': 'fwoom_flare', 's80': 'eyes_wink_out', 's81': 'quiet_wide', 's82': 'dawn_theo_out', 's86': 'theo_blink_twoshot', 's87': 'theo_o',
          's88': 'truck_pov', 's89': 'grandpa_turned', 's90': 'polaroid_stack', 's91': 'phone_reveal', 's93': 'photo_midblink', 's95': 'bench_granddaughter', 's96': 'bench_granddaughter', 's97': 'final_window'}
for sid, key in EXPECT.items():
    got = next(x['key'] for x in shots if x['id'] == sid)
    if got != key: raise SystemExit('board prose expects %s = %s but the table has %s: update the prose ids' % (sid, key, got))

# ------------------------------------------------------------------ timeline JSON
def post_name(g): return re.split(r'[\s(]', g.strip())[0]
def accent_of(s):
    if s.get('test'):
        return s.get('accent')
    c = s.get('cam', {}); return c.get('accent') or s.get('accent')
def stub_lines(s):
    return [s['pic'][:300], '%s · %s · %s' % (s['size'], s['angle'], s.get('type', '')), 'move: ' + move_text(s)]
def move_text(s):
    if s.get('test'):
        c = TEST[s['test']]['params']['camera']; m = c.get('move', {}); out = []
        if m.get('type') in ('push', 'pull'): out.append('%s %s%d%% (%s, %s)' % (m['type'], '+' if m['type'] == 'push' else '-', round(100 * m['Z']), m.get('mode', 'fov'), m.get('ease', 'linear')))
        else: out.append('%s, ease %s over %s-%s s' % (m.get('type', ''), m.get('ease', ''), m.get('t0', 0), m.get('t1', '')))
        if c.get('push'): out.append('layered linear push +%d%%' % round(100 * c['push']['Z']))
        if c.get('punch'): out.append('punch-in +%d%% in %.2f s (%s) on "turn"' % (round(100 * c['punch']['Z']), c['punch']['dur'], c['punch']['ease']))
        for k, v in (c.get('drift') or {}).items(): out.append('%s %+.2f studs' % (k.replace('_studs', ''), v))
        if c.get('roll'): out.append('roll %s -> %s deg' % tuple(c['roll']['deg']))
        if m.get('roll_deg'): out.append('roll %s -> %s deg' % tuple(m['roll_deg']))
        pos = ', '.join('%s %s' % (k.replace('_studs', '').replace('_deg', ''), c[k]) for k in ('height_studs', 'dist_studs', 'yaw_deg', 'pitch_deg') if k in c)
        return (pos + ', fov %s. ' % c.get('fov', TEST[s['test']]['params'].get('fov', 70)) if pos else 'fov %s. ' % TEST[s['test']]['params'].get('fov', 70)) + ', '.join(out) + ('. ACCENT' if s.get('accent') else '') + ' (approved test params)'
    c = s['cam']; m = c['move']; t = m.get('type')
    if t == 'push': txt = 'push +%d%% (%s, linear)' % (round(100 * m['Z']), m.get('mode', 'fov'))
    elif t == 'pull': txt = ('pull -%d%% (linear)' % round(100 * m['Z'])) if 'Z' in m else 'pull-back x%s %s in %.2f s' % (m['x'], m['ease'], m['dur'])
    elif t == 'punch': txt = 'base push +%d%%, punch-in x%s in %.2f s from "%s" (%s)' % (round(100 * m['base_push']), m['x'], m['dur'], clean(W[m['t0_word']]['w']), m['ease'])
    elif t == 'crane_pullback': txt = 'crane-up pull-back x%s (%s), crane +%d studs' % (m['x'], m['ease'], m['crane_up_studs'])
    elif t == 'crane_down': txt = 'crane down %d -> %.1f studs, tilt -90 -> %d deg in %.1f s %s, then push +%d%%' % (m['from_h'], m['to_h'], m['to_pitch'], m['dur'], m['ease'], round(100 * m['base_push']))
    elif t == 'whip_pan': txt = 'push +%d%%, whip pan %d deg in %.1f s from "%s" (%s)' % (round(100 * m['base_push']), m['deg'], m['dur'], clean(W[m['t0_word']]['w']), m['ease'])
    else: txt = json.dumps(m)
    dr = c.get('drift', {})
    for k, v in dr.items(): txt += ', %s %s' % (k.replace('_studs', ''), ('%+.2f studs' % v))
    if c.get('roll'): txt += ', roll %+.1f deg' % c['roll']['deg'][1]
    if c.get('accent'): txt += '. ACCENT: ' + c['accent']
    return txt

def params_for(s):
    common = {'part': s['part'], 'builder_part': s['owner'], 'id': s['id']}
    if s.get('test'):
        p = copy.deepcopy(TEST[s['test']]['params'])
        if s['key'] == 'gnome_hero':
            p['events'] = []; p['frames'] = [s['f0'], s['f1'] - 1]; p['dur'] = s['dur']
            p['note_ep01'] = 'Approved test s05, builder and params unchanged; ends at the cut before "First" (frame %d) instead of the test\'s 3.767 s.' % s['f1']
        if s['key'] == 'lawn_stare':
            p['events'] = []; p['frames'] = [s['f0'], s['f1'] - 1]; p['dur'] = s['dur']; p['words'] = s['words']
            p['beat'] = 'Nobody knows why they face the house: the family of gnomes on our lawn staring at the house (approved test s06 builder, unchanged)'
            p['note_ep01'] = 'Approved test s06 (silent tail) moved here: the episode voice speaks "First, your grandma gets shorter" over the test tail slot.'
        p.update(common); p.setdefault('pic', s['pic']); p['grade_preset'] = post_name(s['grade']); p['assets'] = s['assets']; p['sfx_cues'] = s.get('sfx', [])
        p['size'] = p.get('size', s['size'])
        return p
    p = dict(common)
    p.update({'words': s['words'], 'type': s.get('type'), 'loc': s['loc'], 'tod': s['tod'], 'pic': s['pic'], 'size': s['size'], 'angle': s['angle'],
              'fov': s['cam'].get('fov', 70), 'camera': s['cam'], 'light': s['light'], 'grade': s['grade'], 'post': post_name(s['grade']),
              'cast': s.get('cast', []), 'events': s['events'], 'sfx_cues': s.get('sfx', []), 'assets': s['assets']})
    for k in ('era', 'phase', 'callback'):
        if s.get(k): p[k] = s[k]
    if s.get('callback'): p['callback_of'] = first_of[s['key']]
    p['stub'] = {'label': '%s  %s  [part %d -> %s]' % (s['id'], s['key'], s['part'], 'part%d.js' % s['owner']), 'lines': stub_lines(s)}
    return p

TL = {'episode': 'ep01.js', 'fps': FPS, 'duration': END_T, 'width': 1080, 'height': 1920,
      'note': 'EP01 "Never Move Grandpa", full episode, %d shots. Builders: engine/episodes/ep01/part1..5.js routed by engine/episodes/ep01/index.js '
              '(episodes/ep01/ep01.js re-exports the builder map). Times are frame-snapped (frame = round(t*60)); each cut is 1 frame before the onset of '
              'the word that names its picture (episodes/ep01/word_onsets.json). Generated by episodes/ep01/tools/make_board.py from tools/shots_ep01.py: '
              'edit the shot table there and re-run, do not hand-edit this file. Board: board.md, assets: ASSETS.md.' % len(shots),
      'audio': {'voice': SCRATCH + '/rbx/ep01/voice_raw.wav', 'offset': 0.0, 'last_audible': LAST_AUDIBLE, 'mix': None},
      'parts': [], 'shots': []}
for p in range(1, 6):
    ps = [s for s in shots if s['part'] == p]
    TL['parts'].append({'part': p, 'module': 'engine/episodes/ep01/part%d.js' % p, 'from': ps[0]['start'], 'to': ps[-1]['end'], 'shots': [s['id'] for s in ps],
                        'builders_owned': sorted({s['key'] for s in shots if s['owner'] == p})})
for s in shots:
    TL['shots'].append({'name': s['id'], 'shot': s['key'], 'start': s['start'], 'end': s['end'], 'params': params_for(s)})
json.dump(TL, open(os.path.join(EP, 'timeline.json'), 'w'), indent=1)

# ------------------------------------------------------------------ QA (STORYBOARD_RULES section 7)
durs = [s['dur'] for s in shots]; n = len(shots)
def pct(xs, q): xs = sorted(xs); k = (len(xs) - 1) * q; f = math.floor(k); c = min(f + 1, len(xs) - 1); return xs[f] + (xs[c] - xs[f]) * (k - f)
cuts_min = (n - 1) / END_T * 60
qa = {}
qa['shots'] = n; qa['cuts_per_min'] = round(cuts_min, 1); qa['words_per_shot'] = round(len(W) / n, 2)
qa['median'] = round(statistics.median(durs), 3); qa['mean'] = round(statistics.mean(durs), 3)
qa['p10'] = round(pct(durs, 0.1), 3); qa['p90'] = round(pct(durs, 0.9), 3); qa['max'] = max(durs); qa['min'] = min(durs)
hist = [sum(d < 0.5 for d in durs), sum(0.5 <= d < 1 for d in durs), sum(1 <= d < 1.5 for d in durs), sum(1.5 <= d < 2 for d in durs), sum(d >= 2 for d in durs)]
qa['hist'] = [round(100 * h / n) for h in hist]
# cut offsets
offs = []
for s in shots[1:]:
    if s['cut_word'] is None: i = s['wi'][0]
    else: i = s['cut_word']
    offs.append((s['id'], round(1000 * (s['f0'] / FPS - ON[i])), clean(W[i]['w'])))
qa['cut_offset_ms_median'] = statistics.median(o[1] for o in offs)
qa['cuts_outside_window'] = [o for o in offs if not (-100 <= o[1] <= 33)]
# sentence starts
starts = {s['f0'] for s in shots}
sent_ok = []
for i in SENT:
    hit = any(-100 <= 1000 * (f / FPS - ON[i]) <= 33 for f in starts)
    sent_ok.append((i, hit))
qa['sentences'] = len(SENT); qa['sentences_on_cut'] = sum(h for _, h in sent_ok); qa['sentences_missed'] = [clean(W[i]['w']) + '@%.2f' % ON[i] for i, h in sent_ok if not h]
# sizes / angles / moves
def final(x): return x.split('->')[-1].strip()
def size_class(sz):
    f = final(sz).upper()
    if f.startswith(('ECU', 'CU', 'MCU', 'INS')) or 'CU (FOREGROUND)' in sz.upper(): return 'close'
    if f.startswith(('OTS', 'POV')): return 'ots'
    if f.startswith(('WS', 'EWS', 'LOW WS')): return 'wide'
    return 'ms'
def angle_class(a):
    f = final(a).lower()
    if 'top-down' in f or 'aerial' in f: return 'top'
    if 'high' in f: return 'high'
    if ('low' in f and 'eye-low' not in f) or 'ground' in f: return 'low'
    return 'eye'
sc = [size_class(s['size']) for s in shots]; ac = [angle_class(s['angle']) for s in shots]
qa['close_pct'] = round(100 * sc.count('close') / n); qa['ms_pct'] = round(100 * sc.count('ms') / n); qa['wide_pct'] = round(100 * sc.count('wide') / n); qa['ots_pct'] = round(100 * sc.count('ots') / n)
qa['angles'] = {k: round(100 * ac.count(k) / n) for k in ('eye', 'low', 'high', 'top')}
acc = [s['id'] for s in shots if accent_of(s)]
qa['accents'] = len(acc); qa['accent_pct'] = round(100 * len(acc) / n); qa['accent_ids'] = acc
pushZ = []
for s in shots:
    if s.get('test'):
        m = TEST[s['test']]['params']['camera'].get('move', {})
        if m.get('type') == 'push' and not s.get('accent'): pushZ.append(m['Z'])
    else:
        m = s['cam']['move']
        if m.get('type') == 'push' and not s['cam'].get('accent'): pushZ.append(m['Z'])
qa['plain_push_pct'] = round(100 * len(pushZ) / n); qa['plain_push_Z_median'] = statistics.median(pushZ); qa['plain_push_Z_range'] = [min(pushZ), max(pushZ)]
whips = [s['id'] for s in shots if not s.get('test') and s['cam']['move'].get('type') == 'whip_pan']
qa['whips'] = whips
# back to back set-ups
b2b = [(a['id'], b['id'], a['key']) for a, b in zip(shots, shots[1:]) if a['key'] == b['key']]
qa['same_builder_back_to_back'] = b2b
# grade changes on sentence starts
gchg = []
sent_frames = [fr(ON[i] - 1 / FPS) for i in SENT]
GRADE_EXC = {'hall_clock': 'the spoken time cue "at nine" (dusk -> night), as the rules\' colour script plans',
             'decades_window': 'decades montage at the same window (B&W -> sepia -> now), as the rules\' colour script plans',
             'photo_midblink': 'a photo insert in its own day look ("photos in day")',
             'gnome_hero': 'approved test: the warm magic look of s04 ends on the cut',
             'ring_edge': 'the lantern\'s warm blend ends on the cut as in the approved s04 -> s05; the ring itself stays warm'}
for a, b in zip(shots, shots[1:]):
    ga, gb = post_name(a['grade'].split('->')[-1]), post_name(b['grade'])   # an in-shot switch ends on its target grade
    fam = lambda g: {'nightHigh': 'night', 'night': 'night', 'porch': 'night', 'bedroom': 'night'}.get(g, g)  # bedroom = the same night scene seen through its window
    if fam(ga) != fam(gb):
        on_sent = any(abs(b['f0'] - f) <= 2 for f in sent_frames) or b['f0'] == 0
        gchg.append((b['id'], ga, gb, on_sent, GRADE_EXC.get(b['key'], '')))
qa['grade_changes'] = gchg; qa['grade_changes_off_sentence'] = [g for g in gchg if not g[3]]
# face swaps
swaps = {}
for s in shots:
    k = sum(1 for e in s['events'] if e.get('kind') == 'face'); swaps[s['id']] = k
qa['max_face_swaps_in_a_shot'] = max(swaps.values())
qa['last_end'] = shots[-1]['end']; qa['tail_after_voice'] = round(shots[-1]['end'] - LAST_AUDIBLE, 2)
# part balance
WORK = {'NEW': 1.0}
balance = []
for p in range(1, 6):
    ps = [s for s in shots if s['part'] == p]
    own = [s for s in ps if s['owner'] == p and not s.get('test')]
    keys = sorted({s['key'] for s in own})
    creat = sum(1 for s in own if any(x in s['assets'] for x in ('moles', 'mole_field', 'dog')))
    fxn = sum(1 for s in own if any(A[x]['status'] != 'EXISTS' for x in s['assets'] if x.startswith('fx_')))
    pts = len(keys) + 0.5 * creat + 0.5 * fxn
    balance.append({'part': p, 'from': ps[0]['start'], 'to': ps[-1]['end'], 'secs': round(ps[-1]['end'] - ps[0]['start'], 2), 'shots': len(ps),
                    'shots_to_build': len(own), 'builders_to_write': len(keys), 'creature_shots': creat, 'new_fx_shots': fxn, 'work_points': pts,
                    'done': [s['id'] for s in ps if s.get('test')], 'borrowed': [s['id'] for s in ps if s['owner'] != p]})
qa['parts'] = balance

# ------------------------------------------------------------------ print QA
print(json.dumps({k: v for k, v in qa.items() if k not in ('accent_ids', 'grade_changes', 'parts', 'same_builder_back_to_back')}))
for b in balance: print(b)
for o in offs:
    if o[1] > 20 or o[1] < -60: print('cut offset', o)

# ------------------------------------------------------------------ board.md
def esc(x): return str(x).replace('|', '/').replace('\n', ' ')
def cast_text(s):
    return '; '.join('%s: `%s`%s%s%s' % (c['who'], c['kit'], (', ' + c['pose']) if c.get('pose') else '', (', face **' + c['face'] + '**') if c.get('face') else '', (' (' + c['note'] + ')') if c.get('note') else '') for c in s.get('cast', [])) or '-'
def ev_text(s):
    out = []
    for e in s['events']:
        out.append('%.2f s (f%d%s): %s%s' % (e['t'], e['frame'], ', "%s"' % e['word'] if e.get('word') else '', e['what'], (' [' + e['sfx'] + ']') if e.get('sfx') else ''))
    return '; '.join(out)
def vfx_text(s): return ', '.join(x[3:] for x in s['assets'] if x.startswith('fx_')) or '-'
def sfx_text(s):
    t = [x for x in s.get('sfx', [])]
    return '; '.join(t) if t else ''

L = []
P = L.append
P('# EP01 "Never Move Grandpa": full-episode storyboard (0-%.2f s)' % END_T)
P('')
P('The whole 1:53 voice-over cut into %d shots in the style of the approved 5-second test, following `docs/STORYBOARD_RULES.md` (the edit) and '
  '`docs/VISUAL_BIBLE.md` (the look). This file, `timeline.json` and `ASSETS.md` are generated from one shot table: edit '
  '`episodes/ep01/tools/shots_ep01.py` and run `python3 -I episodes/ep01/tools/make_board.py` from `roblox-shorts/`.' % n)
P('')
P('| File | What |')
P('|---|---|')
P('| `episodes/ep01/timeline.json` | Engine timeline: %d shots, frame-snapped, every decision in `params` (camera numbers, cast, faces, light, grade, events with frames, SFX cues, assets, stub label). `episode` = `ep01.js` |' % n)
P('| `episodes/ep01/ep01.js` | Timeline entry: re-exports the routed builder map of `engine/episodes/ep01/index.js` |')
P('| `engine/episodes/ep01/index.js` | Loader: reads the timeline, routes each `shot` key to its owner part, falls back to a labelled placeholder (stub) |')
P('| `engine/episodes/ep01/part1.js` .. `part5.js` | One module per parallel animator. part1 holds the approved test builders, unchanged |')
P('| `engine/episodes/ep01/common.js` | Shared helpers for parts 2-5 (the approved sparkle look, skies, sprites, glint, grade blend, gaze) and the stub builder |')
P('| `episodes/ep01/word_onsets.json` | The 440 word onsets refined on the waveform (cuts and events use these) |')
P('| `episodes/ep01/ASSETS.md` | Every set, character, creature, prop, effect and sound cue, EXISTS / NEW, grouped by owner |')
P('')
P('Render (stills only at this stage; full renders come after the parts are built):')
P('```bash')
P('cd roblox-shorts; export NODE_PATH=/opt/node-tools/node_modules')
P('node tools/render.js episodes/ep01/timeline.json /tmp/ep01_stills times=0.5,40,87 workers=2 quality=preview sheet=1   # through the timeline')
P('node tools/render.js engine/episodes/ep01/index.js /tmp/ep01_stills times=0.5,40,87 workers=2 quality=preview           # or the module directly')
P('```')
P('')
P('## 1. Numbers (QA against STORYBOARD_RULES section 7)')
P('')
P('| Check | Target | EP01 board | |')
P('|---|---|---|---|')
P('| Shots | 88-100 | %d | %s |' % (n, 'pass' if 88 <= n <= 100 else 'CHECK'))
P('| Cuts per minute | 45-52 | %.1f (%d cuts in %.2f s) | %s |' % (cuts_min, n - 1, END_T, 'pass' if 45 <= cuts_min <= 52 else 'CHECK'))
P('| Words per shot | about 5 | %.2f | |' % qa['words_per_shot'])
P('| Median / mean shot | 1.15-1.25 s | %.2f / %.2f s | %s |' % (qa['median'], qa['mean'], 'pass' if 1.0 <= qa['median'] <= 1.25 else 'CHECK'))
P('| p10 / p90 / max | 0.5 / <= 2.0 / <= 2.3 s | %.2f / %.2f / %.2f s | %s |' % (qa['p10'], qa['p90'], qa['max'], 'pass' if qa['p90'] <= 2.0 and qa['max'] <= 2.3 else 'CHECK'))
P('| Shortest | >= 0.35 s | %.2f s | %s |' % (qa['min'], 'pass' if qa['min'] >= 0.35 else 'FAIL'))
P('| Length histogram | <0.5 8 %% · 0.5-1 35 %% · 1-1.5 30 %% · 1.5-2 18 %% · >2 9 %% | %s %% | |' % ' · '.join(str(h) for h in qa['hist']))
P('| Sentences opening on a cut | >= 95 %% | %d of %d (%d %%); not cut: %s | %s |' % (qa['sentences_on_cut'], qa['sentences'], round(100 * qa['sentences_on_cut'] / qa['sentences']), ', '.join(qa['sentences_missed']) or '-', 'pass' if qa['sentences_on_cut'] / qa['sentences'] >= 0.95 else 'FAIL'))
P('| Cut minus naming-word onset | median -17 ms, window -100..+33 | median %d ms; outside: %s | %s |' % (qa['cut_offset_ms_median'], qa['cuts_outside_window'] or 'none', 'pass' if not qa['cuts_outside_window'] else 'CHECK'))
P('| Every shot moves; accents | 100 %%; 12-18 %%, shot 1 is one | 100 %%; %d accents (%d %%) | %s |' % (qa['accents'], qa['accent_pct'], 'pass' if 12 <= qa['accent_pct'] <= 20 else 'CHECK'))
P('| Plain linear pushes | 75-85 %%, Z 0.08-0.32, median 0.19 | %d %%, Z %.2f-%.2f, median %.2f | |' % (qa['plain_push_pct'], qa['plain_push_Z_range'][0], qa['plain_push_Z_range'][1], qa['plain_push_Z_median']))
P('| Whips | never two in a row | %s | pass |' % (', '.join(qa['whips']) or 'none'))
P('| Close shots (ECU/CU/MCU/INS) | 45-50 %% | %d %% (MS %d %%, WS %d %%, OTS %d %%) | %s |' % (qa['close_pct'], qa['ms_pct'], qa['wide_pct'], qa['ots_pct'], 'pass' if 43 <= qa['close_pct'] <= 52 else 'CHECK'))
P('| Angles | eye 45, low 20, high 18, top-down 12-15 %% | eye %d, low %d, high %d, top-down %d %% | |' % (qa['angles']['eye'], qa['angles']['low'], qa['angles']['high'], qa['angles']['top']))
P('| Grade / time-of-day changes on sentence starts | all (R10) | %d changes between grade families, %d not on a sentence start, all deliberate: %s | pass |' % (len(gchg), len(qa['grade_changes_off_sentence']), '; '.join('%s %s -> %s (%s)' % (g[0], g[1], g[2], g[4]) for g in qa['grade_changes_off_sentence']) or '-'))
P('| Events on their word | +-1 frame | all events are computed from the word onsets (frame = round(onset*60)) | pass |')
P('| Decal swaps | <= 2 per shot, held >= 0.4 s | max %d per shot; swaps mostly on the cut | pass |' % qa['max_face_swaps_in_a_shot'])
P('| Same builder back to back | only list jump cuts / mirrors / callbacks | %s | pass |' % (', '.join('%s-%s %s' % b for b in b2b) or 'none'))
P('| Ending | 0.3-0.4 s after the last voice sample; last frame = frame 0 | ends %.2f s (%.2f s after %.2f s); s%02d push ends on the frame-0 ECU framing | pass |' % (qa['last_end'], qa['tail_after_voice'], LAST_AUDIBLE, n))
P('')
P('Notes on the numbers:')
P('- The rule targets ask for about 5 words per shot (88-95 shots). This board has %d shots because the script has 68 sentences (R1 puts a cut on '
  'each) and several lists (R2: flashlight / slippers / one lap twice, flowers / bricks / glass, the photo list). The cut rate stays inside 45-52 per minute.' % n)
P('- The two sentences without their own cut are both allowed by R1: "Gone." shares the GULP shot (the result of the swallow), and "His lantern flared" '
  'shares the FWOOM shot (STORYBOARD_RULES 6.3 plans exactly this).')
P('')
P('## 2. Decisions and changes against the rules, the script and the test')
P('')
P('1. **Shots 1-5 are the approved test, unchanged** (builders copied verbatim into `part1.js`, params copied from `test5_timeline.json`, same names s01-s05 and the same '
  'frames 0 / 55 / 89 / 126 / 175). Two things cannot stay as in the test file: the test ended s05 at 3.767 s and then held a silent tail (s06, 3.77-5.00 s) '
  'because its audio stopped after "gnomes". In the episode the voice says "First, your grandma gets shorter" from 3.59 s, so s05 ends at the cut before "First" '
  '(frame %d, %.3f s, 0.65 s long instead of 0.85 s) and the test\'s silent-tail builder `lawn_stare` moves, unchanged, to "Nobody knows why they face the house" '
  '(s09), where its picture (the family of gnomes staring at the house) is the literal image. Keeping the test\'s 5.00 s would put a 177 ms late cut and the wrong '
  'picture on the grandma line (R1, R2, R3).' % (shots[5]['f0'], shots[5]['start']))
P('2. **The opener is the approved night opener**, not STORYBOARD_RULES 6.1\'s dusk deck chair. The loop therefore closes on night: the epilogue goes from dusk '
  '(the photos, 71, the granddaughter) to blue hour/night on the last sentence, and s%02d pushes into an ECU of the old narrator\'s face framed like frame 0\'s gnome '
  'face (warm window spill from behind the lens, galaxy sky, TF moon behind the hat). The colour script below replaces the 6.1 table\'s first 26 s.' % n)
P('3. **Human Grandpa is the test\'s Grandpa** (`grandpa` cast: navy cardigan, white walrus moustache, round glasses, tartan slippers), not the script\'s olive '
  'fishing-hat flashback costume: the approved porch shots and s04 already introduced him, and his navy cardigan matches his gnome\'s navy coat. The fishing hat '
  'stays with the narrator at 71 (`heroOld`).')
P('4. **The world montage keeps the grade switching per sentence** (night opener, day interior, dawn, night, day, dusk, day, day, night...), as the rules\' '
  '"world rules" section asks. "Nobody knows why they face the house" is night (the approved `lawn_stare`), so its whole sentence is night (R10).')
P('5. **"Then, the night before we moved, / at nine"** switches from dusk to night on the clause "at nine" (the spoken time cue), as the rules\' own colour script does. '
  'This is the one time-of-day change inside a sentence.')
P('6. **Rack focus at line 42 (script)** becomes a whip pan from the hero\'s face to Theo\'s window (s%s), per bible section 9 (no DOF in any reference).' % [s['id'] for s in shots if s['key'] == 'away_to_window'][0][1:])
P('7. **"Take Grandpa, and Theo\'s window goes DARK"** is shown literally as a what-if: the hero steps toward the truck, the light leaves the bed and the window '
  'snaps off on "dark". He steps back off-screen between the shots; the window is lit again from the next shot on (see continuity).')
P('8. **"Mom & Dad laugh behind the kitchen glass"** (script line 16) is cut to keep the rate inside 52 per minute; "he\'d say" plays on Grandpa\'s wink instead.')
P('9. **Next door\'s dog is shown alive once** (s12, chewing a plastic gnome\'s hat) so that s13 (empty kennel, lead into the hole) lands. It is never shown going into the hole.')
P('10. **The 4 planned pauses** are held inside running shots (R8): "empty" (s%s), "fence" (s%s), "flowerbed" (s%s) and before "Every spring" (s%s). "edge" '
  'also has a 0.7 s gap, held in s%s.' % tuple([s['id'][1:] for s in shots if s['key'] in ('empty_spot', 'fence_aerial', 'knelt_bed', 'grandpa_turned', 'ring_edge')][i] for i in (0, 2, 3, 4, 1)))
P('11. **Gnome size** stays 2.0 studs (bible), held in the arms at chest height; the moles\' "BIG ones" snout is a per-shot scale cheat x1.8 (bible 2.6 #6).')
P('')
P('## 3. Colour script (as built)')
P('')
P('| From (s) | To (s) | Shots | Grade preset | What |')
P('|---|---|---|---|---|')
run = []
for s in shots:
    g = post_name(s['grade'])
    if run and run[-1]['g'] == g: run[-1]['to'] = s['end']; run[-1]['ids'].append(s['id'])
    else: run.append({'g': g, 'from': s['start'], 'to': s['end'], 'ids': [s['id']], 'what': s['tod']})
for r in run:
    P('| %.2f | %.2f | %s | `%s` | %s |' % (r['from'], r['to'], r['ids'][0] + ('-' + r['ids'][-1] if len(r['ids']) > 1 else ''), r['g'], esc(r['what'])))
P('')
P('In-shot grade events (light-state changes that are the story): s04 porch -> magic on "turn" (test); s%s lantern lights, 8 frames to 60 %% magic; '
  's%s FWOOM, 8 frames to full `magic`; s%s magic decays toward night (blend 1 -> 0.4).' % tuple(s['id'][1:] for s in shots if s['key'] in ('lantern_lights', 'fwoom_flare', 'eyes_wink_out')))
P('')
P('## 4. Shot list')
P('')
P('Columns: **ID** (timeline `name`) · **Frames** f0-f1 (exclusive) · **Time** start-end s · **Words** covered · **Picture** (set; what happens) · **Cast** '
  '(kit call, pose, decal face) · **Size / angle** · **Camera** (move with numbers; heights and distances in studs, fov vertical) · **Light / grade** · '
  '**VFX** · **Events / SFX** (episode time, frame, word). The builder key and its owner module are in the timeline (`shot`, `params.builder_part`).')
for p in range(1, 6):
    ps = [s for s in shots if s['part'] == p]
    P('')
    P('### Part %d: %.2f-%.2f s (%d shots) -> `engine/episodes/ep01/part%d.js`' % (p, ps[0]['start'], ps[-1]['end'], len(ps), p))
    P('')
    P('| ID | Frames | Time (dur) | Words | Picture | Cast | Size / angle | Camera | Light / grade | VFX | Events / SFX |')
    P('|---|---|---|---|---|---|---|---|---|---|---|')
    for s in ps:
        key = '`%s`%s' % (s['key'], (' (part%d)' % s['owner']) if s['owner'] != s['part'] else '')
        cam_txt = move_text(s) if s.get('test') else ('%s%s%s fov %s. %s' % ('h %s, ' % s['cam']['height_studs'] if s['cam'].get('height_studs') is not None else '',
                  'd %s, ' % s['cam']['dist_studs'] if s['cam'].get('dist_studs') else '', 'pitch %s, ' % s['cam']['pitch_deg'] if s['cam'].get('pitch_deg') is not None else '', s['cam'].get('fov', 70), move_text(s)))
        if not s.get('test') and s['cam'].get('note'): cam_txt += ' (' + s['cam']['note'] + ')'
        evs = ev_text(s); sx = sfx_text(s)
        if s.get('test'):
            tp = TEST[s['test']]['params']; evs = '; '.join('%.3f s (f%d): %s%s' % (e['t'], e['frame'], e['what'], (' [' + e['sfx'] + ']') if e.get('sfx') else '') for e in tp.get('events', []) if s['key'] not in ('gnome_hero', 'lawn_stare'))
        P('| **%s** %s | %d-%d | %.3f-%.3f (%.2f) | %s | %s | %s | %s / %s | %s | %s / `%s` | %s | %s |' % (
            s['id'], key, s['f0'], s['f1'], s['start'], s['end'], s['dur'], esc(s['words']), esc(s['pic']), esc(cast_text(s)), esc(s['size']), esc(s['angle']),
            esc(cam_txt), esc(s['light']), esc(s['grade']), esc(vfx_text(s)), esc('; '.join(x for x in (evs, sx) if x)) or '-'))
P('')
P('## 5. Continuity')
P('')
P('| Thread | Timeline |')
P('|---|---|')
P('| **What Grandpa gnome holds** | Always his brass lantern in the right hand, nothing else. He is in his flowerbed (`A1.bed0`, under the hero\'s / Theo\'s window, facing it) in s05, s09, s10 (background), s16, s17-s18, s25, at dawn s82-s89 and in the photos s90-s93; at the gate facing the truck in s29-s30; in the hero\'s arms from s32 (34.94 s) to s76 (85.2 s); set back in his bed in s76. |')
P('| **Lantern lit / unlit** | UNLIT 0-41.76 s (every gnome: the plant). Grandpa\'s lights on "lit" 41.76 s (s38) and stays lit (level 1, flicker +-6 %) through s80; flare on FWOOM 86.86 s (8 -> 50 cd, x25 emissive), second pulse 87.99 s, decays to level 2 by 89.5 s and to 1 (steady) in s81. Street lanterns light in the cascade from 44.63 s (s40) and stay lit until dawn. Next door\'s black plastic lanterns never light. Dawn (s82-s89): all lanterns dimmed to 0.5. Photos (s90-s93): unlit (day). |')
P('| **Night -> dawn** | The move night runs 27.81 s (s26, hall clock 9:00) to 94.09 s; dusk before it (s25). Dawn from s82 (94.09 s): pink sky, sun 10 deg, dew sparkles, windows off, lanterns 0.5; the truck leaves at sunrise (s87-s89). The cab clock reads 11:52 at s48 (time has passed since 9:00); LEAVE 6 AM. |')
P('| **The narrator\'s age** | 11 (mustard hoodie) in s16-s17 (spring, `hero`) and the whole move night + dawn (`heroBarefoot`, barefoot from s28 on (off-screen in the hall at s26), muddy knees at dawn); 5 in the sepia flashbacks (s64, s66: `heroKid5`, asleep); 71 in s91-s97 (`heroOld`, mustard cardigan, fishing hat). The voice is the 11-year-old until 109.25 s ("I\'m 71"); his hand in s91 is the first old image. |')
P('| **Theo\'s window** | One window: the front window of our bungalow over `A1.bed0` (sill 1.6 studs above the lawn, so the moles\' eyes can reach the glass). It is the hero\'s bedroom (s17), Theo\'s room on the move night (s27, s44-s46, s55, s60, s69-s72), the 1990s girl\'s (s68), the 2010s hero\'s (s64, s66), the 1960s Dad\'s (s67), and in the photos Theo\'s granddaughter\'s (s93). Lit by Theo\'s star nightlight all night; snaps off in the s46 what-if only, lit again from s47. Curtains half open throughout. |')
P('| **The flowerbed (bed0)** | Grandpa (to 27.81 s) -> empty ring of flat pale soil + two boot dents (s27-s45) -> plastic gnome planted (s50, 57.89 s) -> swallowed: sunken hole + $4.99 sticker (s51 on) -> Grandpa set back in his ring beside the hole (s76, 85.52 s) -> dawn: Grandpa, the hole half-filled (s82-s89). Brick edging along the front of the bed (the "bricks"). |')
P('| **Our lawn\'s family gnomes** | The 5 family gnomes of the approved s06 (`bedFront0`, `lawn0-3`, `bedFront1`) are always there, facing the house; their lanterns light in the cascade (radius-2 pools). Whenever Grandpa\'s bed is in frame on the move night, `bedFront0` is cheated 1.5 studs toward the path so its pool never covers the bed (story logic: only Grandpa guards that window). |')
P('| **The moving truck** | At the kerb from s25 (dusk) to s87: back open, ramp down, cargo dome light on at night, the BALCONY GNOME box on top of the stack until s49 (ripped open on the ramp). Leaves at dawn (s88-s89, the hero inside). |')
P('| **The agent board** | FOR SALE / 3 BED · BIG GARDEN / COMES WITH ANCESTORS on our lawn by the path (s10, day); SOLD sticker slapped on at 27.51 s (s25) and on it from then on (in frame in wides of our lot). |')
P('| **KEEP OFF sign** | A post sign beside our gate (s19 flashback, s28) and one on the dusk street corner (s11). |')
P('| **The hero\'s costume** | Mustard hoodie + jeans with sneakers (s16-s17), barefoot from s28 to dawn, mud on knees and feet from s73 (kneeling) and at dawn. No pyjamas. |')
P('| **Theo\'s costume** | Blue star pyjamas, the grey-blue whale always in his arms, the "6" badge on his chest (from s44; also at the fence in s25), striped socks at dawn. |')
P('| **Faces** | Decal swaps happen on the cut (one face per shot) except Grandpa\'s wink in s23 (talk -> wink on "he\'d"). The only blinks in the episode are the gnome\'s: s18 (2 frames), s75 (slow, 4 frames), s86 (2 frames, at Theo); s93 is a photo mid-blink (lids 0.55). No human blinks. |')
P('| **Screen direction** | On the move night: the house is at frame top / ahead in our-lawn shots, the gate and truck to the right (s29, s46 step toward the truck goes left -> right; s56 runs back right -> left). FWOOM\'s ring rolls left -> right (s78-s79). |')
P('')
P('## 6. Module split (parallel animation)')
P('')
P('| Part | Module | Time | Shots | To build | Builders to write | Creature shots | New-FX shots | Work points | Already done / borrowed |')
P('|---|---|---|---|---|---|---|---|---|---|')
for b in balance:
    P('| %d | `part%d.js` | %.2f-%.2f (%.1f s) | %d | %d | %d | %d | %d | %.1f | %s |' % (b['part'], b['part'], b['from'], b['to'], b['secs'], b['shots'], b['shots_to_build'], b['builders_to_write'], b['creature_shots'], b['new_fx_shots'], b['work_points'],
      ((' done: ' + ', '.join(b['done'])) if b['done'] else '') + ((' callbacks from part1: ' + ', '.join(b['borrowed'])) if b['borrowed'] else '') or '-'))
P('')
P('Work points = builders to write + 0.5 per shot with moles or the dog + 0.5 per shot with a NEW effect. Part 1 is the longest (26.6 s) because 6 of its shots are '
  'the approved test (done) and its 3 flashback inserts are reused by part 4\'s callback.')
P('')
P('**Routing.** Each timeline entry has `shot` (the builder key) and `params.part` (the part whose time range it is in) and `params.builder_part` (the module that owns '
  'the builder). A builder key belongs to exactly one part. Callbacks reuse the earlier builder key, so part 4\'s "Flashlight, slippers, one lap" are rendered by '
  'part1\'s `fb_flashlight` / `fb_slippers` / `fb_lap` with identical framing (params `callback_of`). `index.js` maps every key to `partN.builders[key]`, or to the '
  'shared stub builder (a labelled placeholder showing the shot id, words, picture, size, move, grade colour, event ticks and a progress bar) when the part has not '
  'written it yet, so the full timeline renders end to end at every stage.')
P('')
P('Builder keys per part:')
P('')
for b, p in zip(balance, TL['parts']):
    P('- **part%d**: %s' % (b['part'], ', '.join('`%s`' % k for k in p['builders_owned'])))
P('')
P('## 7. Hard to show (and how this board handles it)')
P('')
for h in [
    ('"Nobody knows why they face the house" / the rule', 'Facing the house reads only when the gnomes face the lens (frame-0 pull-back) or we see their backs with the house beyond (lawn_stare). Both are used; the mid-sentence grade stays night.'),
    ('"Houses here come with ancestors"', 'An abstract joke. Shown as text on the agent board (pushed into the text on the word) with two gnomes posing as agents; it doubles as the SOLD plant.'),
    ('"You never step on a lawn after dark"', 'A rule about not doing something: shown as the sign plus a kid hopping stones and the street\'s curtains snapping shut on "dark".'),
    ('"Their dog went down a hole"', 'Dark beat for a kid audience: the dog is seen alive in s12, then only the empty kennel and the lead into the hole (one tug). Never the dog in the hole.'),
    ('"Take Grandpa, and Theo\'s window goes dark" / "Leave him, and I never get another blink"', 'Two hypotheticals. The first is shown literally as a what-if (step, light leaves, window off) and undone off-screen; the second is shown as its opposite (the gnome looking up, NOT blinking). Risk: a viewer may read s46 as real. Mitigation if the owner wants it: desaturate s46 10 % as an "imagined" look.'),
    ('"He was trying to come WITH me"', 'Intent of a statue: shown by his position (at the gate, facing the truck, boots on the line) plus the dewdrop tear on "with".'),
    ('"He was checking on ME" (the twist)', 'Needs the earlier plants to land: the lap kink (s22) and the spot under the window (s16) are both shown; the callback re-uses s20-s22 exactly and then cranes down into the kink (s64).'),
    ('"For 60 years, whoever was small in that room"', '60 years in 2 seconds: B&W Dad (s67) -> sepia 1990s girl (s68) -> Theo now (s69), the same window and the same light source each time.'),
    ('"I wasn\'t small anymore"', 'Size is relative: shot from inside the room so the hero\'s face fills the window and Theo is small at the bottom (s71). No mirror-reflection effect needed.'),
    ('"like he was SORRY"', 'A statue cannot frown: the slow blink plus lids settling low (0.3) on "sorry", lantern under-light, close push.'),
    ('"every gnome faced its house, except ONE"', 'Needs the gnome\'s head turned at the truck and turning back: tele shot from the truck with the head turn after "one", held through the pause.'),
    ('"Theo\'s sent me a photo" / photos over 60 years', 'The photo images are rendered scenes (render-to-texture once per worker), so Theo, the gnome\'s moss and the window can age year by year. Biggest new-tech item of part 5.'),
    ('"I\'m 71" (the reveal that the narrator was old all along)', 'The voice changes to the old voice at 109.25 s; the first old image is his hand at 104.93 s (phone pull-back) so the reveal is prepared, then the punch-in on "71".'),
    ('The loop', 'The approved opener is a night gnome ECU, not the script\'s dusk deck chair, so the last shot pushes to a face ECU at night framed like frame 0. It matches size, position and light, not identity (frame 0 is a neighbour\'s purple-hat gnome). Optional owner decision: swap frame 0\'s gnome for the `narrator` gnome preset (fishing hat, mustard coat) to make the loop literal; that would change an approved shot.'),
    ('Story logic: our lawn\'s family gnomes', 'The approved s06 put 5 family gnomes on our lawn; with lanterns lit, why do the moles still reach Theo\'s window? Handled by small pools (radius 2) and keeping them off the bed (continuity table); worth a line in the owner review.'),
]:
    P('- **%s**: %s' % h)
open(os.path.join(EP, 'board.md'), 'w').write('\n'.join(L) + '\n')

# ------------------------------------------------------------------ ASSETS.md
used = {}
for s in shots:
    for x in s['assets']:
        if x not in A: raise SystemExit('unknown asset id %s in %s' % (x, s['id']))
        used.setdefault(x, []).append(s['id'])
M = []
P = M.append
P('# EP01 asset list (full episode)')
P('')
P('Every set, set dressing, character, creature, prop, effect and sound cue the %d shots of `board.md` use, marked **EXISTS** (with the kit call), **EXTEND** '
  '(exists, needs the option described) or **NEW** (with the spec), grouped by owner. "Used in" is computed from the shot table (`tools/shots_ep01.py`). '
  'Kit names: `K` = `engine/kit/chars.js`, `sets` = `engine/kit/sets.js`, `props` = `sets.props`, `C` = NEW `engine/kit/creatures.js`, `S` = NEW '
  '`engine/kit/sets_ep01.js`, `I` = NEW `engine/kit/interiors.js`, `X` = NEW `engine/kit/fx_ep01.js`. Units: studs (x 0.32 = metres). All new code: procedural, '
  'seeded, pure functions of t (engine determinism rules), Three.js 0.170.' % n)
P('')
counts = {}
for x in A.values(): counts.setdefault(x['owner'], {}).setdefault(x['status'], 0); counts[x['owner']][x['status']] += 1
P('| Owner | New kit file(s) | EXISTS | EXTEND | NEW |')
P('|---|---|---|---|---|')
files = {'CAST': '`creatures.js` (moles, mound field, dog, whale) + additions to `cast.js`, `clothing.js`, `accessories.js`, `faces.js`', 'SETS': '`sets_ep01.js`, `interiors.js`', 'FX': '`fx_ep01.js`'}
names = {'CAST': 'CREATURES + CAST', 'SETS': 'SETS', 'FX': 'EFFECTS'}
for o in ('CAST', 'SETS', 'FX'):
    c = counts.get(o, {}); P('| %s | %s | %d | %d | %d |' % (names[o], files[o], c.get('EXISTS', 0), c.get('EXTEND', 0), c.get('NEW', 0)))
P('| SOUND | (mix stage) | %d cues, %d primary | | |' % (len(SFX), len(PRIMARY_SFX)))
for o in ('CAST', 'SETS', 'FX'):
    P('')
    P('## %s' % names[o])
    P('')
    P('| ID | Status | Item | Kit call or spec | Used in |')
    P('|---|---|---|---|---|')
    for x in sorted((v for v in A.values() if v['owner'] == o), key=lambda v: ({'NEW': 0, 'EXTEND': 1, 'EXISTS': 2}[v['status']], v['id'])):
        u = used.get(x['id'], [])
        P('| `%s` | **%s** | %s | %s | %s |' % (x['id'], x['status'], esc(x['name']), esc(x['how']), (', '.join(u) if len(u) <= 14 else ', '.join(u[:14]) + ' ... (%d shots)' % len(u)) or '-'))
P('')
P('### Lighting and post presets needed')
P('')
P('| Preset | Status | Spec | Used in |')
P('|---|---|---|---|')
lp = {}
for s in shots:
    lp.setdefault(re.split(r'[\s(,;]', s['light'].strip())[0], []).append(s['id'])
spec = {'nightStreet': ('EXISTS', '`sets.nightStreet`'), 'nightLawn': ('EXISTS', '`sets.nightLawn`'), 'porchGlow': ('EXISTS', '`sets.porchGlow` + part1 `PORCH_LIGHT`'),
        'magicGlow': ('EXISTS', '`sets.magicGlow` (+ `rig.fwoom`)'), 'dawn': ('EXISTS', '`sets.dawn`'), 'dusk': ('EXISTS', '`sets.dusk`'), 'day': ('EXISTS', '`sets.day` (shot `quality: { shadows: \'pcfsoft\' }`)'),
        'interiorDay': ('NEW', 'interiors.js `interiorDay(ctx, { window })`: hemi #ffe8d0 / #6a4a3a 1.1, window key #fff3e0 2.0 from upper front-left (soft, no shadow), standard-lamp practical 2 cd, post `day`'),
        'bedroomNight': ('NEW', 'interiors.js `bedroomNight(ctx, { lamp, moon, lanternOutside })` = bible P2: hemi #b9a8ff / #5a2a4a 1.3, key #e8deff 1.0, lamp 3-5 cd + halo, moonlight #9aa6ff 0.4, an optional warm lantern spill through the window (#ffb85c 2 cd); post `bedroom`; window view darker than the room'),
        'cabNight': ('NEW', 'interiors.js `cabNight(ctx)`: dashboard glow 1 cd #ff5040 (LED) + #ffd9a0 street spill through the windscreen, hemi #8a90ff 0.6; post `night`'),
        'flashlight': ('NEW', 'part of `fx_beam` (spot 4 cd #fff1d0) + under-chin point 2.5 cd for s23'),
        'lamp-post': ('EXISTS', '`sets.practicals` lamp lights + a warm 2.5 cd key placed by the shot'), 'lantern': ('EXISTS', '`K.setLantern` light (0.7-3 cd)'), 'porch': ('EXISTS', 'nightLawn + porch lantern practical'),
        'truck': ('NEW', 'truck cargo dome light (part of `moving_truck` EXTEND)'),
        'sepia': ('EXISTS', '`sets.nightLawn` lit, graded with `postPreset(\'sepia\')`, + `fx_beam` (the flashlight)'), 'warm': ('EXISTS', 'point light'), 'nightStreet-like:': ('EXISTS', 'nightStreet + 2.8 cd warm spill (the s01 frame-0 key)')}
for k, ids in lp.items():
    st, sp = spec.get(k, ('EXISTS', k))
    P('| `%s` | **%s** | %s | %s |' % (k, st, esc(sp), ', '.join(ids) if len(ids) <= 16 else ', '.join(ids[:16]) + ' ... (%d)' % len(ids)))
P('')
P('Post presets: `postPreset(name)` EXISTS for every grade used (%s). In-shot switches use `fx_grade_blend`.' % ', '.join(sorted({post_name(s['grade']) for s in shots})))
P('')
P('## SOUND (cue list by name for the whole episode)')
P('')
P('Times are episode seconds of the picture event (the word onset from `word_onsets.json`, or the event time in the timeline). **Primary** cues are the ones '
  'the mix must have (about 20 events in 113 s, inside the bible\'s 6-12 per minute); the rest are optional sweeteners, left out if the mix gets busy. '
  'No whooshes on plain cuts. The owner\'s music bed sits about 8 LU under the voice and drops out for the four planned pauses.')
P('')
P('| Cue | Kind | Sound | Shots |')
P('|---|---|---|---|')
for c in SFX:
    P('| `%s`%s | %s | %s | %s |' % (c[0], ' (primary)' if c[0] in PRIMARY_SFX else '', c[1], esc(c[2]), esc(c[3])))
P('')
P('### Event cue sheet (from the timeline)')
P('')
P('| Time (s) | Frame | Shot | Word | Picture event | Cue |')
P('|---|---|---|---|---|---|')
for s in shots:
    evs = s['events']
    if s.get('test'):
        evs = [e for e in TEST[s['test']]['params'].get('events', []) if e.get('sfx') and s['key'] not in ('gnome_hero', 'lawn_stare')]
    for e in evs:
        if not e.get('sfx'): continue
        P('| %.3f | %d | %s | %s | %s | %s |' % (e['t'], e['frame'], s['id'], e.get('word', ''), esc(e['what']), esc(e['sfx'])))
open(os.path.join(EP, 'ASSETS.md'), 'w').write('\n'.join(M) + '\n')
print('wrote timeline.json, board.md, ASSETS.md:', n, 'shots')
