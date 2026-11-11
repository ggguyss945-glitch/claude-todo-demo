"""cues.py: the mirror film's cue sheets for audio/mix.py, from the director's plan and (later) from the picture.

    python3 audio/cues.py [--plan plan] [--events _work/align/film_events.json] [--out _work/cues]   (run from film/)

Reads plan/sound_plan.json (400 SFX cues, 104 bed ranges, the music events and intensity curve, voice FX) and
plan/shots.json (shot times), plus _work/align/timeline.json (line times). With --events, the assembler's
film_events.json (format below) retimes and overrides the plan. Writes to --out:

    sfx_cues.json     [{id, t, name, gain_db, pan, space, params, hit, seed, shot, note}]  one-shots, plus bed streams:
                      params.stream = key of a continuous bed rendered ONCE for the whole film and gated per range
                      (params: dur, lp, loop = seamless loop period, phase0 = loop phase origin s, fade)
    music_cues.json   {duration, intensity, events, arrangement (the music map), options (score.py layers), bed_dips}
    voice_fx.json     [{line, t, end, fx}]  per-line voice processing (below, queen, queen_child, far, far_outside,
                      phone, phone_child); mix.py applies it
    cues_report.json  counts per name, hits per minute, silences, the arrangement with fitted offsets

film_events.json (written by film.py; every key optional):
    {"version": 1, "duration": 700.0,
     "shots": [{"id": "S001", "t0": 0.0, "t1": 1.23}, ...],   actual cut times: every plan cue and music event of a shot
                                                              keeps its offset from the shot start (bed ranges follow)
     "sfx":   [{"id": "S003:impact_hit:1", "t": 3.93, ...}],  override any field of the plan cue with that id
              [{"t": 12.40, "name": "bed_creak", "space": "close", "params": {}, "gain_db": -6, "hit": false}]
                                                              no id (or an unknown id): a new cue from the picture
     "drop":  ["S010:paper:0"],                               plan cues the picture no longer has
     "music": [{"t": 129.80, "type": "rule", "level": 0.95}], extra music events; {"id": "...", ...} overrides one
     "hits":  [605.21, ...]}                                  picture hit times: nearest plan hit within 0.25 s snaps
Cue ids are "<shot>:<name>:<k>" (k = order of that name inside the shot); music event ids "<shot>:<type>:<k>".

The music map (MUSIC_MAP) puts one of the owner's ten Epidemic tracks on each section by mood; score.py fits the
start offset to the intensity curve (loudness + brightness) unless `off` is given, crossfades at scene changes,
switches inside silences, and adds only the score layers asked for in LAYERS.

Mix settings for this film (MIX_ARGS, measured on the draft): see audio/mix.py's docstring for the command.
"""
import argparse, json, os, re, sys, hashlib, collections

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.normpath(os.path.join(HERE, '..'))

# ------------------------------------------------------------------------------------------------- the music map
# section (film s) -> track (mood). off None: fitted by score.py (near = preferred start in the track, s).
MUSIC_MAP = [
    dict(s0=0.0, s1=19.18, slug='don_t_look_belladonna_strings', near=0,
         why='hook: cold sustained horror strings (Eb->D), one huge hit, then grief'),
    dict(s0=19.18, s1=88.66, slug='midnight_wanderer_luella_gren', near=0, gain_db=8.0,
         why='arrival, the porch, sneaking past the caretaker: nocturnal walk (E->D), uneasy, light pulse'),
    dict(s0=88.66, s1=129.8, slug='irene_kevin_dailey', off=6.0, gain_db=4.0,
         why='the steps and the game: Irene builds from silence (D minor) into the rule-1 card'),
    dict(s0=129.8, s1=203.53, slug='annihilated_blue_saga', near=20,
         why='rule 1, inside the glass: dark D ambient; its D-major middle under the too-normal reflection'),
    dict(s0=203.53, s1=269.24, slug='come_closer_belladonna_strings', near=40,
         why='rule 2: the hand, the wish, "You have it": horror strings with stabs and drop-outs (Eb->D)'),
    dict(s0=269.24, s1=289.74, slug='irene_kevin_dailey', near=100,
         why='rule 3: the clock runs back, the queen\'s face: Irene\'s dense plateau'),
    dict(s0=289.74, s1=350.38, slug='when_the_sun_sets_anna_landstrom', near=0, cut='hard', gain_db=6.0,
         why='the crossing (picture travel) into the too-normal dawn: warm unpulsed D major (C#->D), still and clean'),
    # v2 review (critic M4): one cue per act, changed only on a card or on picture travel; the mid-scene swaps at 398.9,
    # 481.4 / 499.9 and 677.4 are gone (the lullaby carries rule 4 to its card, Impossible Theory carries rule 5 to the
    # bell as one build, the brothers' theme carries the ending with the drones rising under it from 677.4)
    dict(s0=350.38, s1=446.33, slug='sleep_forever_luella_gren', near=10,
         why='rule 4, the loop, "a little while" and the morning he vanished: the lullaby figure (G#->A) to the card'),
    dict(s0=446.33, s1=542.03, slug='impossible_theory_rachel_sandy', near=14,
         why='rule 5: Tess runs, the countdown, the crate, the fake bell, the deepest silence, the real bell: one build'),
    dict(s0=542.03, s1=628.7, slug='escalation_jon_bjork', off=0.0, cut='hard',
         why='rule 6 + 7 climax: pulsed build (C->D, 121 bpm) whose natural end lands as the glass goes dark'),
    dict(s0=628.7, s1=700.0, slug='end_of_rain_beyza', near=100, gain_db=5.0,
         why='relief and grief: the brothers\' theme, "Hi, Mom"; the drones rise under it to the phone; hard out at 698.62'),
]
# the silences that stay real silences (critic M1: 23 scripted bed-outs, one every 30 s, became a formula); every other
# plan silence becomes a -6 dB thinned dip of the score under the line and the hit rises out of the bed
KEEP_SILENCES = (533.18, 603.91, 628.7, 661.64, 698.6)
SIL_DIP_DB = -6.0
# risers into the two biggest hits (critic M4): into the deepest silence before the real bell (535.36) and into the H7
# silence before her foot (605.21)
EXTRA_MUSIC = [dict(t=526.4, type='riser', level=0.85, len=6.7, note='into the bell (via the 533.18 silence)'),
               dict(t=598.3, type='riser', level=0.9, len=5.55, note='into her foot (via the 603.91 silence)')]
# score.py's own layers (dB curves per bus, piecewise-linear): only where they help the tracks
DAWN = (290.6, 350.38); MEMORY = (398.86, 446.33); WARM_END = (628.7, 677.39)
# v2 review (critic M2): the v2 mix was squashed (LRA 2.4 against 4.2-5.4, limiter 6.1 dB) and the bed sat too low under the
# narration (-14.3 against sibling -11.9): delivered at -16 LUFS (references -15.7 to -17.9) with the glue and limiter
# eased, hits free to reach +8 LU, the bed 2-3 dB up and ducked less under the voice so it carries across the cuts
MIX_ARGS = ['--langs', 'en', '--out-name', 'mix.wav', '--bed-rel', '-9.5', '--bed-p50', '-12', '--music-lo', '-10.5',
            '--music-hi', '-9', '--hit-duck', '3', '--hit-dip', '9', '--score-hits-db', '6', '--lev-lo', '-3',
            '--lev-hi', '9', '--tilt', 'mirror', '--sub-boost', '3', '--master-lufs', '-16', '--duck', '2.5', '--glue-max', '1.5',
            '--voice-plr', '13']


def _gate(base, spans, depth, ramp=0.6):
    """[[t, dB]] at `base` dB with `depth` dB inside each (t0, t1) span (ramped)."""
    pts = [[0.0, base]]
    for a, b in spans:
        pts += [[a - ramp, base], [a, depth], [b, depth], [b + ramp, base]]
    return pts + [[720.0, base]]


LAYERS = {
    'drones': _gate(-5.0, [DAWN, MEMORY, WARM_END], -45.0),
    'strings_bed': _gate(-12.0, [DAWN, MEMORY, WARM_END, (19.18, 88.66)], -45.0),
    'strings_fx': _gate(-5.0, [DAWN, MEMORY], -16.0),
    'melodic': [[0, -2.0], [720, -2.0]],
    # critic M4: the bed builds steadily to its peak in the 70-80 % tenth (sibling) instead of peaking late and falling:
    # the tracks ramp continuously from rule 5's card to the bell, hold through the climax and ease into the ending
    'tracks': [[0.0, -1.0], [88.66, 0.0], [446.33, -2.0], [533.0, 2.5], [536.0, 2.5], [542.03, 1.0], [604.0, 2.5],
               [628.7, 0.0], [677.39, 0.0], [698.0, 1.0], [720.0, 1.0]],
}
END_T = 698.62                     # hard cut to black: everything but the hit tails out (the faint bell is an SFX)
PULSE_KEEP = (283.0, 291.0)        # the only score pulse: the queen's face (the tracks carry the other pulses)

# bed tokens in sound_plan.beds -> (name, space, gain dB, lp Hz, stream key suffix, extra params)
VOICE_FX_KIND = {'below', 'queen', 'queen_child', 'far', 'far_outside', 'phone', 'phone_child'}
LOOP_LINKS = [('water_drip', 332.37, 'drip'), ('water_drip', 346.83, 'drip'),
              ('nail_click_glass', 143.29, 'nail'), ('nail_click_glass', 690.19, 'nail')]
DAWN_LOOP = 19.48
DAWN_PHASE0 = 297.59               # the other side's loop clock (header: 06:59:40 + ((t - 297.59) mod 19.48))


def h32(s):
    return int(hashlib.md5(s.encode()).hexdigest()[:7], 16)


def parse_bed(tok):
    m = re.match(r'^([a-z_]+)(?:\((.*)\))?(.*)$', tok.strip())
    name, mod, rest = m.group(1), (m.group(2) or ''), m.group(3).strip()
    g = re.search(r'(-?\d+(?:\.\d+)?)\s*dB', mod); gain = float(g.group(1)) if g else 0.0
    l = re.search(r'LP\s*(\d+(?:\.\d+)?)\s*kHz', mod); lp = float(l.group(1)) * 1000 if l else None
    p = {}; key = name
    if 'muffled' in mod:
        key += '|muffled'
    if 'through the doorway' in mod:
        key += '|door'; lp = lp or 3200
    if 'through glass' in mod:
        key += '|glass'; lp = lp or 3800
    if name == 'ambience_dawn':
        p['loop'] = DAWN_LOOP; p['phase0'] = DAWN_PHASE0
    if 'stutters' in rest:
        key += '|stutter'; p['stutter'] = 0.6
    return name, gain, lp, key, p


DEFAULT_BED_SPACE = {'ambience_camp_night': 'outside', 'room_tone': 'inside', 'ambience_mirror': 'mirror',
                     'ambience_memory': 'memory', 'ambience_dawn': 'inside', 'lantern_hum': 'close',
                     'wind_chimes': 'outside', 'tv_through_wall': 'outside'}


def bed_streams(beds, dur):
    """sound_plan.beds ranges -> stream cues (contiguous ranges of one stream merged) + rule-card bed dips."""
    runs = collections.OrderedDict(); dips = []
    for r in beds:
        toks = list(r['beds'])
        if 'card_dip' in toks:
            dips.append([r['t0'], r['t1'], -7.0]); continue
        st = [t for t in toks if 'stutters' in t]
        if st:                                         # "detunes and stutters" replaces the plain loop in the range
            toks = [t for t in toks if not t.startswith('ambience_dawn(loop')]
        for tok in toks:
            name, gain, lp, key, p = parse_bed(tok)
            runs.setdefault(key, []).append([r['t0'], r['t1'], name, gain, lp, p])
    out = []
    for key, rr in runs.items():
        rr.sort(key=lambda x: x[0]); merged = [rr[0][:]]
        for x in rr[1:]:
            if abs(x[0] - merged[-1][1]) < 0.02 and x[3] == merged[-1][3]:
                merged[-1][1] = x[1]
            else:
                merged.append(x[:])
        for t0, t1, name, gain, lp, p in merged:
            prm = dict(stream=key, dur=round(t1 - t0, 3), fade=0.04, **p)
            if lp:
                prm['lp'] = lp
            out.append(dict(id=f'bed:{key}:{t0:.2f}', t=round(t0, 3), name=name, gain_db=gain, pan=0.0,
                            space=DEFAULT_BED_SPACE.get(name, 'inside'), params=prm, hit=False,
                            seed=h32('stream:' + key), shot=None, note='bed stream'))
    return out, dips


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plan', default=os.path.join(FILM, 'plan'))
    ap.add_argument('--timeline', default=os.path.join(FILM, '_work', 'align', 'timeline.json'))
    ap.add_argument('--events', default=None, help='film_events.json from film.py (optional)')
    ap.add_argument('--out', default=os.path.join(FILM, '_work', 'cues'))
    A = ap.parse_args()
    sp = json.load(open(os.path.join(A.plan, 'sound_plan.json')))
    shots = json.load(open(os.path.join(A.plan, 'shots.json')))
    tl = json.load(open(A.timeline))
    FE = json.load(open(A.events)) if A.events and os.path.exists(A.events) else {}
    dur = float(FE.get('duration') or sp['meta']['duration'])
    plan_shot = {s['id']: (s['t0'], s['t1']) for s in shots['shots']}
    new_shot = {s['id']: (float(s['t0']), float(s['t1'])) for s in FE.get('shots', [])}

    def retime(t, shot):
        if shot in new_shot and shot in plan_shot:
            return round(new_shot[shot][0] + (t - plan_shot[shot][0]), 4)
        return t

    # ---------------- SFX one-shots
    cues = []; kcount = collections.Counter()
    for c in sp['sfx']:
        k = kcount[(c['shot'], c['name'])]; kcount[(c['shot'], c['name'])] += 1
        cid = f"{c['shot']}:{c['name']}:{k}"
        p = dict(c.get('params') or {})
        for nm, tt, lid in LOOP_LINKS:
            if c['name'] == nm and abs(c['t'] - tt) < 0.03:
                p['loop_id'] = lid
        cues.append(dict(id=cid, t=retime(c['t'], c['shot']), name=c['name'], gain_db=c.get('gain_db', 0),
                         pan=c.get('pan', 0.0), space=c.get('space'), params=p, hit=bool(c.get('hit')),
                         seed=h32(cid), shot=c['shot'], note=c.get('note', ''), origin=c.get('origin')))
    # the film's biggest scares: densified and lifted in mix.py (params.punch)
    for c in cues:
        if c['name'] in ('impact_hit', 'braam', 'stinger', 'sub_drop') and c['gain_db'] >= -1 and c['hit']:
            c['params']['punch'] = 1.0 if c['gain_db'] >= 0 else 0.6
    # the queen's presence under her lines and her full faces (sound_plan: "the queen's presence")
    L = tl['lines']
    for i, fx in sp['voice_fx'].items():
        if fx['fx'] in ('queen', 'queen_child'):
            l = L[int(i)]
            cues.append(dict(id=f'queen:line{i}', t=round(l['t'] - 0.35, 3), name='queen_presence', gain_db=-4,
                             pan=0.0, space='mirror', params={'dur': round(l['end'] - l['t'] + 0.8, 2)}, hit=False,
                             seed=h32(f'queen{i}'), shot=None, note='queen presence under her line'))
    for t in (283.77, 478.28, 696.91):
        cues.append(dict(id=f'queen:face{t}', t=t - 0.6, name='queen_presence', gain_db=-2, pan=0.0, space='mirror',
                         params={'dur': 2.2}, hit=False, seed=h32(f'face{t}'), shot=None, note='queen full face'))
    # picture overrides
    byid = {c['id']: c for c in cues}
    for e in FE.get('sfx', []):
        if e.get('id') in byid:
            byid[e['id']].update({k: v for k, v in e.items() if k != 'id'})
        else:
            n = dict(gain_db=0, pan=0.0, space=None, params={}, hit=False, shot=None, note='from the picture')
            n.update(e); n.setdefault('id', f"film:{e['name']}:{e['t']:.3f}"); n.setdefault('seed', h32(n['id']))
            cues.append(n)
    drop = set(FE.get('drop', []))
    cues = [c for c in cues if c['id'] not in drop]
    cues, n_cut = declutter(cues, shots)
    for ht in FE.get('hits', []):
        near = [c for c in cues if c.get('hit') and abs(c['t'] - ht) <= 0.25]
        for c in near:
            c['t'] = float(ht)
    # ---------------- beds
    beds = sp['beds']
    if new_shot:
        st0 = {round(v[0], 3): k for k, v in plan_shot.items()}
        def rt(x):
            k = st0.get(round(x, 3)); return new_shot[k][0] if k in new_shot else x
        beds = [dict(b, t0=rt(b['t0']), t1=rt(b['t1'])) for b in beds]
    streams, dips = bed_streams(beds, dur)
    cues = sorted(cues + streams, key=lambda c: (c['t'], c['id']))

    # ---------------- music
    M = sp['music']
    ev = []; kc = collections.Counter()
    for e in M['events']:
        k = kc[(e.get('shot'), e['type'])]; kc[(e.get('shot'), e['type'])] += 1
        d = dict(e, id=f"{e.get('shot')}:{e['type']}:{k}", t=retime(e['t'], e.get('shot')))
        ev.append(d)
    byid = {e['id']: e for e in ev}
    for e in FE.get('music', []):
        if e.get('id') in byid:
            byid[e['id']].update(e)
        else:
            ev.append(dict(e))
    for ht in FE.get('hits', []):                       # picture hit times snap the music hits too
        for e in ev:
            if e['type'] in ('hit', 'stinger', 'braam', 'sub_drop') and abs(e['t'] - ht) <= 0.25:
                e['t'] = float(ht)
    layers = {k: [list(p) for p in v] for k, v in LAYERS.items()}
    keep = []
    ev = ev + [dict(m, id='v2r1:%s:%.2f' % (m['type'], m['t'])) for m in EXTRA_MUSIC]
    n_sil_dip = 0
    for e in ev:
        ty = e['type']
        if ty == 'silence' and not any(abs(e['t'] - k) < 0.6 for k in KEEP_SILENCES):
            a, b = e['t'], e['t'] + float(e.get('len', 1.2))       # a thinned dip, not a drop-out
            for bus in ('tracks', 'drones', 'strings_bed', 'strings_fx', 'melodic'):
                layers.setdefault(bus, [[0, 0.0], [720, 0.0]])
                layers[bus] = _merge_dip(layers[bus], a, b, SIL_DIP_DB, ramp_in=0.35, ramp_out=0.6)
            n_sil_dip += 1
            continue
        if ty in ('pulse_on', 'pulse_off') and not (PULSE_KEEP[0] <= e['t'] <= PULSE_KEEP[1]):
            continue
        if ty == 'dip':                               # bed dips: a gain curve on the score's sustained buses
            depth = -(2.0 + 20.0 * (0.5 - float(e.get('level', 0.3))))
            a, b = e['t'], e['t'] + float(e.get('len', 4.0))
            for bus in ('tracks', 'drones', 'strings_bed', 'strings_fx'):
                layers.setdefault(bus, [[0, 0.0], [720, 0.0]])
                layers[bus] = _merge_dip(layers[bus], a, b, depth)
            continue
        if ty in ('drone', 'end'):
            continue
        keep.append(e)
    for bus in ('tracks', 'drones', 'pulse', 'melodic', 'strings_bed', 'strings_fx'):    # hard cut to black
        layers.setdefault(bus, [[0, 0.0], [720, 0.0]])
        layers[bus] = _merge_dip(layers[bus], END_T, 720.0, -80.0, ramp_in=0.06, ramp_out=0.0)
    keep.sort(key=lambda e: e['t'])
    arrangement = [{k: v for k, v in m.items() if k != 'why'} for m in MUSIC_MAP]
    for a in arrangement:
        a.setdefault('off', None)
    mc = dict(duration=dur, intensity=M['intensity'], events=keep, arrangement=arrangement,
              options={'lament': False, 'layers': layers, 'slope': 16.0, 'swell_db': 9.0, 'reentry_db': 7.0}, bed_dips=dips,
              music_map=MUSIC_MAP)
    # ---------------- voice FX
    vfx = []
    for i, fx in sorted(sp['voice_fx'].items(), key=lambda x: int(x[0])):
        l = L[int(i)]
        vfx.append(dict(line=int(i), t=l['t'], end=l['end'], fx=fx['fx'], text=fx.get('line', l['en'])))
    have = {v['line'] for v in vfx}
    for l in L:
        if l.get('fx') and l['i'] not in have:
            vfx.append(dict(line=l['i'], t=l['t'], end=l['end'], fx=l['fx'], text=l['en']))
    # ---------------- write
    os.makedirs(A.out, exist_ok=True)
    json.dump(cues, open(os.path.join(A.out, 'sfx_cues.json'), 'w'), indent=0)
    json.dump(mc, open(os.path.join(A.out, 'music_cues.json'), 'w'), indent=0)
    json.dump(vfx, open(os.path.join(A.out, 'voice_fx.json'), 'w'), indent=1)
    one = [c for c in cues if not c['params'].get('stream')]
    rep = dict(source='film_events.json' if FE else 'plan', duration=dur, sfx_cues=len(one), bed_streams=len(streams),
               stream_keys=sorted({c['params']['stream'] for c in streams}), hits=sum(1 for c in one if c['hit']),
               hits_per_min=round(sum(1 for c in one if c['hit']) / dur * 60, 2),
               music_events=collections.Counter(e['type'] for e in keep),
               silences_per_min=round(sum(1 for e in keep if e['type'] == 'silence') / dur * 60, 2),
               names=collections.Counter(c['name'] for c in one), voice_fx=len(vfx), bed_dips=len(dips),
               ui_sounds_cut=n_cut, silences_to_dips=n_sil_dip, kept_silences=list(KEEP_SILENCES))
    json.dump(rep, open(os.path.join(A.out, 'cues_report.json'), 'w'), indent=1)
    print(f"cues: {rep['sfx_cues']} one-shots ({len(rep['names'])} names, {rep['hits']} hits = {rep['hits_per_min']}/min), "
          f"{len(streams)} bed ranges in {len(rep['stream_keys'])} streams, {len(keep)} music events, "
          f"{len(vfx)} voice FX lines -> {A.out}")


# critic M3: 776 one-shots (66.5 /min), about 220 of them UI and edit ticks (ring_tick 61, diagram_pop 48, ui_pop 25,
# glitch 24, glass_wipe 24, flash_hit 21, glint_whoosh 20): bright 1-5 kHz clicks over the voice. The story foley stays.
UI_NAMES = ('ring_tick', 'diagram_pop', 'ui_pop', 'glitch', 'glass_wipe', 'flash_hit', 'glint_whoosh', 'chalk_draw',
            'pixel_glitch', 'tape_rewind', 'whoosh')
REAL_HITS = (3.93, 143.29, 535.36, 605.21, 690.19)


def declutter(cues, shots):
    """Thin the UI / transition sounds (about 60 % go): no sound on glint cuts; ring_tick only on the giant-number beats;
    one soft gesture per diagram; flash_hit only on the real hits; glitch only on the kept glitch cuts (the hook's
    flash-forwards); card write-on wipes once per card; the rest of the UI pops thinned to one per shot, 4 dB softer.
    Story foley (towels, glass, steps, bells, cloth, the phone, the lipstick) is never touched."""
    giants = sorted(h['t'] for s in shots['shots'] for h in s['hud'] if h['type'] == 'giant_number')
    diagrams = sorted(h['t'] for s in shots['shots'] for h in s['hud'] if h['type'] in ('diagram', 'dials', 'eye_line', 'sound_rings', 'map'))
    out, seen, cut = [], set(), 0
    for c in sorted(cues, key=lambda c: c['t']):
        nm = c['name']
        dev = c.get('origin') == 'device' or nm in ('glint_whoosh', 'ring_tick', 'diagram_pop', 'ui_pop', 'flash_hit')
        if nm not in UI_NAMES or not dev:
            out.append(c); continue
        t = c['t']; keep = True
        if nm == 'glint_whoosh': keep = False
        elif nm == 'ring_tick': keep = any(abs(t - g) < 0.35 for g in giants)
        elif nm in ('diagram_pop', 'chalk_draw'):
            d = min(diagrams, key=lambda x: abs(x - t)) if diagrams else None
            k = ('diag', round(d, 2) if d is not None and abs(d - t) < 3.0 else int(t / 4.0))
            keep = k not in seen and (d is not None and abs(d - t) < 3.0 or ('w', int(t / 4.0)) not in seen)
            seen.add(k); seen.add(('w', int(t / 4.0)))
            if keep: c['gain_db'] = round(float(c.get('gain_db', 0)) - 4.0, 1)
        elif nm == 'flash_hit': keep = any(abs(t - h) < 0.2 for h in REAL_HITS)
        elif nm in ('glitch', 'pixel_glitch'): keep = t < 13.0 or any(abs(t - h) < 0.2 for h in REAL_HITS)
        elif nm == 'glass_wipe':
            k = ('wipe', c.get('shot')); keep = k not in seen; seen.add(k)
        else:
            k = (nm, c.get('shot')); kw = (nm, int(t / 4.0)); keep = k not in seen and kw not in seen; seen.add(k); seen.add(kw)
            if keep: c['gain_db'] = round(float(c.get('gain_db', 0)) - 4.0, 1)
        if keep: out.append(c)
        else: cut += 1
    return out, cut


def _merge_dip(pts, a, b, depth, ramp_in=0.4, ramp_out=1.0):
    """Add a dip (dB) over a..b to a piecewise-linear curve [[t, dB]] (dB values add)."""
    import numpy as np
    grid = sorted({p[0] for p in pts} | {a - ramp_in, a, b, b + ramp_out})
    base = np.interp(grid, [p[0] for p in pts], [p[1] for p in pts])
    dip = np.interp(grid, [a - ramp_in, a, b, b + ramp_out], [0, depth, depth, 0], left=0, right=0)
    return [[round(float(t), 3), round(float(v + d), 2)] for t, v, d in zip(grid, base, dip)]


if __name__ == '__main__':
    main()
