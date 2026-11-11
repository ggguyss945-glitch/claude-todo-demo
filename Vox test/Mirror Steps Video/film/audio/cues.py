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

Sound v3 (the owner: "the SFX and music need some rework, taking inspiration from how the references build tension";
measured in analysis/refmirror/snd_study.py, README.md section 3): sfx_v3() keeps every story action and thins the rest
(SFX_DROP, THIN, the card's whip / hit / stamp only); music_v3() keeps nine true silences (KEEP_SILENCES), turns the
plan's other silences into 0.5 s holes right before their hit (DROP_LEN, DROP_DB) or thinned dips, cuts a hole before
each rule card (CARD_GAP), fixes the risers' end times (RISER_FIX) and adds risers into the reveals (EXTRA_MUSIC), keeps
the swells that build (SWELL_*); music_cues.json carries the act shape (ARC, steered by mix.py --steer), the holes, the
score options (slope 9, swell_db 5, sub_db SUB_DB, preduck PRE_DUCK) and MIX_ARGS deliver at -14 LUFS / -1 dBTP.
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
# ------------------------------------------------------------------------------------------------ sound v3: tension
# Measured on the five references (voice and bed separated; analysis/refmirror/snd_env.py + snd_study.py, numbers in
# README.md section 3): the bed is CONTINUOUS and steady under the narration (3 s short-term p10/50/90 about -17 / -13 /
# -9 LU rel voice, bed loudness range 8-10 LU; v2 r1: -20.5 / -14.4 / -5.1, range 17.7), it rises in the narration's
# pauses (-4 to -14; v2 r1 stayed at -15), it is dark and heavy (31-63 Hz +11 to +13 dB over 1 kHz; v2 r1 -1 to +3), its
# drop-outs are short (0.4-0.6 s, 0-2 a minute; v2 r1 1.3 s, 2.8 a minute) and its hits are punctuation (2-5 a minute,
# 2-7 LU under the voice, decaying in about 1.7 s) on a running bed, not after a hole. Tension is built by what plays
# (drones, density, the hit on the turn), not by chopping the bed. So: one long breath per act (ARC below, steered by
# mix.py), short drop-outs right before the turns, true silences only for the deepest moments, risers into the
# reveals, and the rule card's shape (a hole just before it, the card's hit, the stamp, the new act's music).
#
# true silences (score out, room tone only), kept at their plan length: the click, time stopping, the deepest silence
# before the real bell, the silence before her foot, the foot hanging, Mom's pause, the last click
KEEP_SILENCES = (142.09, 341.53, 533.18, 603.91, 625.86, 628.7, 661.64, 688.05, 698.6)
RESHAPE_SILENCE = {625.86: (626.4, 1.78)}   # the foot hangs: the whole "for a second", into "the glass goes dark"
DROP_LEN = 0.5                     # every other plan silence that ends in a hit: the score dips DROP_DB for the 0.5 s
DROP_DB = -10.0                    # right before the hit (with the score's own pre-hit duck: a 14-18 dB hole)
DROP_AT = {181.58: 182.78, 397.51: 398.86}  # silences with no hit that end on a turn: the boy's voice, the memory cut
SIL_DIP_DB = -5.0                  # the rest: a thinned dip of the score under the line (as review round 1)
CARD_GAP = 0.6                     # rule cards: the riser stops this long before the card, the score dips DROP_DB, the
                                   # card's hit (references: the bed 7 dB down 1-1.5 s before "Rule number", then the hit)
CARD_RISER = 0.6                   # the cards' risers peak about 6-8 dB under the voice (v2 r1: 1 dB under, at level 0.9)
PRE_DUCK = 0.7                     # score.py's pre-hit duck scaled (the references' hits land on a running bed: median
                                   # suck-out 0.3-6.5 dB; the plan's 6-16 dB over 0.35-1 s before every hit chopped the bed)
# risers: into the two biggest hits (critic M4: the real bell 535.36 via the 533.18 silence, her foot 605.21 via the
# 603.91 silence) and, v3, into the reveals the references build to (the head turn, "You have it", her face, her offer)
EXTRA_MUSIC = [dict(t=533.18, type='riser', level=0.75, len=6.7, note='into the bell (via the 533.18 silence)'),
               dict(t=603.91, type='riser', level=0.75, len=5.55, note='into her foot (via the 603.91 silence)'),
               dict(t=696.91, type='riser', level=0.8, len=5.5, note='v3: the phone\'s voice -> the last sting (696.91)'),
               dict(t=197.65, type='riser', level=0.6, len=4.5, note='v3: lean closer -> the head turn (198.15)'),
               dict(t=247.72, type='riser', level=0.65, len=5.0, note='v3: the wish -> "You have it" (248.22)'),
               dict(t=283.27, type='riser', level=0.6, len=4.0, note='v3: "The queen says" -> her face (283.77)'),
               dict(t=477.78, type='riser', level=0.55, len=4.5, note='v3: she pats the mattress -> her face (478.28)'),
               dict(t=477.6, type='silence', level=0.0, len=0.5, note='v3: the hole before her face (478.28)')]
# plan silences that became holes before weaker hits: plain dips (she sits 466.52 lands on the running bed)
NO_HOLE = (465.32,)
# a riser ENDS at t (score.py); these plan risers were written with t = their start: (end, len)
# (review round 1's two risers ended 5-7 s before their silences for the same reason; fixed above)
RISER_FIX = {122.97: (129.2, 6.2), 677.39: (688.05, 10.6)}
# swells: the references breathe about 1.8 times a minute (+8.5 LU over about 14 s); the plan had 44 (3.8 a minute,
# +12 LU). Kept: the authored builds (level >= 0.55), not the card decays, at least 9 s apart
SWELL_MIN_LEVEL = 0.55
SWELL_GAP = 9.0
# the act-by-act breath of the bed: music as heard under the narration (3 s short-term, LU rel the voice's integrated
# loudness), steered by mix.py (--steer). References: -13 to -16 under speech; quiet passages are the dawn, the memory
# and the ending, the loudest the climax (70-80 % of the film, as in the references' light and sound)
# review round 2 (critic M19): the climb is a real crescendo (-12.5 at 576 s, Noah grown and shaking, to -8.5 at her foot, 4 LU
# over 27 s, the references' long builds); the builds into card 1 (112-128.5), card 3 (230-262) and the bell (503.5-531) were
# already 3-3.5 LU
ARC = [(0.0, -11.0), (12.4, -11.0), (13.2, -14.0), (19.0, -14.0), (22.0, -17.0), (66.0, -17.0), (71.0, -16.0),
       (88.0, -15.0), (92.0, -16.5), (112.0, -15.0), (128.5, -11.5), (131.0, -13.0), (136.0, -14.5), (160.0, -14.5),
       (181.0, -13.5), (196.5, -12.0), (204.5, -12.5), (230.0, -13.5), (245.0, -11.5), (262.0, -10.5), (268.5, -10.5),
       (288.5, -10.0), (292.0, -18.0), (330.0, -18.0), (340.0, -15.0), (350.0, -13.0), (356.0, -12.5), (372.0, -13.0),
       (380.0, -15.0), (397.0, -15.0), (400.0, -19.5), (440.0, -18.5), (446.5, -12.0), (464.0, -12.0), (470.0, -11.0),
       (480.0, -10.0), (484.5, -16.0), (500.0, -16.0), (503.5, -13.0), (531.0, -10.0), (542.5, -11.0), (560.0, -12.0),
       (576.0, -12.5), (603.0, -8.5), (611.0, -8.5), (625.0, -9.5), (631.0, -18.0), (676.0, -17.0), (690.0, -13.5), (698.6, -11.5),
       (700.0, -11.5)]
# score.py's own layers (dB curves per bus, piecewise-linear): only where they help the tracks
DAWN = (290.6, 350.38); MEMORY = (398.86, 446.33); WARM_END = (628.7, 677.39)
# v2 review (critic M2) delivered at -16 LUFS with the glue and limiter eased. Sound v3: back to -14 LUFS (true peak
# <= -1 dBTP) with the act shape steered (--steer, the ARC above, replaces the two-way leveler that flattened it), the
# bed up under the voice and rising in the pauses (--duck 4 with the arc 4 dB over it), a bass-weighted score bus
# (--tilt v3: the references' 31-125 Hz weight, a cut at 500 Hz-1 kHz), the hits as punctuation (pre-hit suck-out 6 dB
# on the hits that keep it); the voice chain's own true-peak limiter back to v2's PLR range (12 dB; r1's 13 was set for
# -16 LUFS and at -14 left every plosive to the master limiter, 1174 near-ceiling blocks against 71); the ambience
# beds -3 dB and the foley -1.5 dB under the music (their chirps and rustles were half of the bed's 44 onsets a minute
# against the references' 18); the bed bus limited to -4 dBTP before the voice joins (the hits' peaks had the master
# limiter taking up to 6 dB, and the narration with them)
MIX_ARGS = ['--langs', 'en', '--out-name', 'mix.wav', '--master-lufs', '-14', '--tp-max', '-1.0', '--steer', '0.85',
            '--duck', '4', '--bed-rel', '-10.5', '--bed-p50', '-12.5', '--music-lo', '-15', '--music-hi', '-8',
            '--hit-duck', '3', '--hit-dip', '6', '--score-hits-db', '2', '--tilt', 'v3', '--sub-boost', '4',
            '--glue-max', '1.5', '--voice-plr', '12', '--beds-db', '-3', '--events-db', '-1.5', '--bed-ceiling', '-4']


def _gate(base, spans, depth, ramp=0.6):
    """[[t, dB]] at `base` dB with `depth` dB inside each (t0, t1) span (ramped)."""
    pts = [[0.0, base]]
    for a, b in spans:
        pts += [[a - ramp, base], [a, depth], [b, depth], [b + ramp, base]]
    return pts + [[720.0, base]]


LAYERS = {
    # v3: the drones (the synth sub on the key root, contrabass and celli sustains) are the bed's floor under every act
    # but the too-normal dawn, the bleached memory and the warm first half of the ending (references: 31-63 Hz +11 to
    # +13 dB over 1 kHz in every window measured)
    'drones': _gate(0.0, [DAWN, MEMORY, WARM_END], -45.0),
    'strings_bed': _gate(-12.0, [DAWN, MEMORY, WARM_END, (19.18, 88.66)], -45.0),
    'strings_fx': _gate(-5.0, [DAWN, MEMORY], -16.0),
    'melodic': [[0, -2.0], [720, -2.0]],
    # the act shape is mix.py's arc steering (ARC); the tracks bus only keeps the r1 lift into the bell and the climax
    'tracks': [[0.0, 0.0], [520.0, 0.0], [533.0, 1.5], [542.03, 1.0], [604.0, 1.5], [628.7, 0.0], [720.0, 0.0]],
}
SUB_DB = 4.0                       # v3: the synth sub drone (score.render_sub) 4 dB up: the references' sub weight
                                   # (+6 with the tilt's +6 at 63 Hz kept the master limiter working all through the film)
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
    for ht in FE.get('hits', []):
        near = [c for c in cues if c.get('hit') and abs(c['t'] - ht) <= 0.25]
        for c in near:
            c['t'] = float(ht)
    n_in = sum(1 for c in cues if not (c.get('params') or {}).get('stream'))
    cues, n_cut, sfx_stat = sfx_v3(cues)
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
    ev = ev + [dict(m, id='v3:%s:%.2f' % (m['type'], m['t'])) for m in EXTRA_MUSIC]
    keep, mstat, holes = music_v3(ev, layers, cues)
    for bus in ('tracks', 'drones', 'pulse', 'melodic', 'strings_bed', 'strings_fx'):    # hard cut to black
        layers.setdefault(bus, [[0, 0.0], [720, 0.0]])
        layers[bus] = _merge_dip(layers[bus], END_T, 720.0, -80.0, ramp_in=0.06, ramp_out=0.0)
    keep.sort(key=lambda e: e['t'])
    arrangement = [{k: v for k, v in m.items() if k != 'why'} for m in MUSIC_MAP]
    for a in arrangement:
        a.setdefault('off', None)
    # v3: the score's own intensity slope halved (16 -> 9 dB: the bed's range was 17.7 LU against the references' 8-10;
    # the act shape is the ARC, steered in mix.py), swells lift the tracks 5 dB (was 9), the sub drone SUB_DB up
    mc = dict(duration=dur, intensity=M['intensity'], events=keep, arrangement=arrangement,
              options={'lament': False, 'layers': layers, 'slope': 9.0, 'swell_db': 5.0, 'reentry_db': 6.0,
                       'sub_db': SUB_DB, 'preduck': PRE_DUCK}, bed_dips=dips, music_map=MUSIC_MAP, arc=[list(p) for p in ARC],
              holes=holes)
    n_sil_dip = mstat['dip']
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
               sfx_cut=n_cut, one_shots_in=n_in, sfx_v3=sfx_stat, music_v3=mstat, silences_to_dips=n_sil_dip,
               kept_silences=list(KEEP_SILENCES))
    json.dump(rep, open(os.path.join(A.out, 'cues_report.json'), 'w'), indent=1)
    print(f"cues: {rep['sfx_cues']} one-shots ({len(rep['names'])} names, {rep['hits']} hits = {rep['hits_per_min']}/min), "
          f"{len(streams)} bed ranges in {len(rep['stream_keys'])} streams, {len(keep)} music events, "
          f"{len(vfx)} voice FX lines -> {A.out}")


# ------------------------------------------------------------------------------------------- sound v3: the SFX
# The references' bed has 18-29 onsets a minute and 0-2 strong ones; v2 r1 had 38 and 5.7 (618 one-shots, 53 a minute;
# critic M3 had cut v2's 776). Every action the story turns on stays on its frame; a repeated gesture keeps one sound
# per gesture (the louder of a close pair); the HUD and the edit are left to the picture; the rule card keeps the
# towel's whip in, the card's hit and the numeral's stamp (the lipstick write-ons, the settle thud, the cursor and the
# statement squeaks go).
SFX_DROP = {'ui_pop', 'diagram_pop', 'chalk_draw', 'glint_whoosh', 'pixel_glitch', 'flash_hit', 'highlighter_squeak',
            'typing', 'glass_thud'}
# name: (minimum spacing s between kept sounds of that name, quietest gain kept dB)
THIN = {'lace_pull': (2.5, -99), 'candy_wrapper': (3.0, -99), 'tape_peel': (0.6, -99), 'glass_tap': (0.45, -99),
        'cloth_press': (1.5, -12), 'cloth_grab': (1.0, -14), 'bed_creak': (1.0, -14), 'jacket_cloth': (1.5, -99),
        'towel_cloth': (0.4, -15), 'flashlight_click': (10.0, -99), 'tape_rewind': (8.0, -99), 'glitch': (0.6, -99),
        'whoosh': (3.0, -9), 'breath': (1.0, -99), 'water_drip': (0.3, -99), 'kids_far': (3.0, -99)}
BREATH_KEEP = ('shh', 'held', 'gasp', 'shaky', 'panting', 'on glass')
GLITCH_KEEP = (367.79, 589.65, 698.0)            # after the hook: the face swap, "Wait", the last frame (picture glitches)
CARD_DEVICE = ('lipstick_draw', 'glass_wipe')    # device write-ons (the cards' RULE and statement, the tags)


def sfx_v3(cues):
    """The v3 SFX budget (rules above). Returns (cues, n dropped, {reason: n})."""
    st = collections.Counter(); out = []; last = {}       # last[name] = (time, index in out) of the last kept
    for c in sorted(cues, key=lambda c: (c['t'], -float(c.get('gain_db', 0)))):
        nm = c['name']; t = c['t']; g = float(c.get('gain_db', 0)); p = c.get('params') or {}
        if p.get('stream'):
            out.append(c); continue
        note = (c.get('note') or '').lower(); dev = c.get('origin') == 'device'
        why = None
        if nm in SFX_DROP:
            why = 'ui'
        elif nm in CARD_DEVICE and dev and t > 13.0:
            why = 'card write-on'
        elif nm == 'ring_tick' and dev and g < -6 and 'giant' not in note and 'calls' not in note:
            why = 'ui'
        elif nm == 'glitch' and t > 13.0 and not any(abs(t - k) < 0.3 for k in GLITCH_KEEP):
            why = 'edit'
        elif nm == 'breath' and g < -10 and not any(k in note for k in BREATH_KEEP):
            why = 'faint'
        elif nm in THIN:
            gap, gmin = THIN[nm]
            if g < gmin and not c.get('hit'):
                why = 'faint'
            elif nm in last and t - last[nm][0] < gap and not c.get('hit'):
                k = last[nm][1]                        # a close pair: the clearly louder one stays
                if g >= float(out[k].get('gain_db', 0)) + 3.0 and not out[k].get('hit'):
                    out[k] = c; last[nm] = (t, k)
                why = 'thinned'
        if why:
            st[why] += 1; continue
        if nm == 'lipstick_stamp':                     # the card's stamp: the references' +3-5 LU 1-2 s after the card
            c['gain_db'] = round(g + 2.0, 1)
        elif nm == 'towel_whip':                       # the card's whoosh in, under the hole before it
            c['gain_db'] = round(g - 2.0, 1)
        elif nm == 'tape_rewind':                      # the loop resets: a device, softer
            c['gain_db'] = round(g - 3.0, 1)
        # the pre-hit suck-out (mix.py) only for the real hits: the HITS names, the card's hit, the story's struck sounds
        if c.get('hit') and nm in ('lipstick_stamp', 'number_thump', 'rubber_stamp', 'ui_pop', 'cloth_grab', 'cloth_press',
                                   'bed_creak', 'bare_foot_step', 'water_drip', 'crate_creak', 'wood_thud'):
            c['hit'] = False; c.setdefault('params', {})['punct'] = True; st['hit flag off'] += 1
        last[nm] = (t, len(out))
        out.append(c)
    n_cut = sum(v for k, v in st.items() if k != 'hit flag off')
    return out, n_cut, dict(st)


def music_v3(ev, layers, sfx):
    """The v3 music events (rules at the top: KEEP_SILENCES, DROP_LEN, DROP_AT, SIL_DIP_DB, CARD_GAP, swells).
    Returns (kept events, counts, holes [[t0, t1]]: the drop-outs and card holes, for mix.py's arc steering)."""
    st = collections.Counter(); holes = []
    hit_t = sorted({e['t'] for e in ev if e['type'] in ('hit', 'stinger', 'braam', 'sub_drop')} |
                   {c['t'] for c in sfx if c.get('hit') and not (c.get('params') or {}).get('stream')
                    and float(c.get('gain_db', 0)) >= -6})
    cards = sorted(e['t'] for e in ev if e['type'] == 'rule')
    keep, last_swell = [], -99.0
    for e in sorted(ev, key=lambda e: e['t']):
        ty = e['type']; t = e['t']; note = e.get('note') or ''
        if ty == 'silence':
            ln = float(e.get('len', 1.2))
            k = next((k for k in KEEP_SILENCES if abs(t - k) < 0.6), None)
            if k is not None:
                t, ln = RESHAPE_SILENCE.get(k, (t, ln))
                keep.append(dict(e, t=t, len=ln, level=0.0)); st['silence'] += 1; continue
            nh = [h for h in hit_t if t < h <= t + ln + 1.5 and not any(abs(t - x) < 0.6 for x in NO_HOLE)]
            end = nh[0] if nh else next((v for kk, v in DROP_AT.items() if abs(t - kk) < 0.6), None)
            if end is not None:                        # a short sharp hole right before the turn (score buses, not the
                a, b, depth = end - DROP_LEN, end, DROP_DB  # reverb tails), the hit lands on the returning bed
                st['drop-out'] += 1; holes.append([round(a, 3), round(b, 3)])
            else:
                a, b, depth = t, t + ln, SIL_DIP_DB    # a thinned dip under the line
                st['dip'] += 1
            for bus in ('tracks', 'drones', 'strings_bed', 'strings_fx', 'melodic', 'pulse'):
                layers.setdefault(bus, [[0, 0.0], [720, 0.0]])
                layers[bus] = _merge_dip(layers[bus], a, b, depth, ramp_in=0.12 if end else 0.35,
                                         ramp_out=0.05 if end else 0.6)
            continue
        if ty == 'riser' and any(abs(t - k) < 0.05 for k in RISER_FIX):
            t1, ln = RISER_FIX[min(RISER_FIX, key=lambda k: abs(t - k))]
            keep.append(dict(e, t=t1, len=ln, note='v3: ends at %.2f' % t1)); st['riser end fixed'] += 1; continue
        if ty == 'riser' and any(abs(t - c) < 0.05 for c in cards):
            c = min(cards, key=lambda c: abs(t - c))   # the card's riser stops CARD_GAP early; the hole; the card's hit
            keep.append(dict(e, t=round(c - CARD_GAP, 3), level=min(float(e.get('level', 0.7)), CARD_RISER),
                             note='v3: stops before the card'))
            for bus in ('tracks', 'drones', 'strings_bed', 'strings_fx', 'melodic', 'pulse'):
                layers.setdefault(bus, [[0, 0.0], [720, 0.0]])
                layers[bus] = _merge_dip(layers[bus], c - CARD_GAP, c - 0.02, DROP_DB, ramp_in=0.15, ramp_out=0.05)
            st['card hole'] += 1; holes.append([round(c - CARD_GAP, 3), round(c, 3)]); continue
        if ty == 'swell':
            if 'decay under the card' in note or float(e.get('level', 0.7)) < SWELL_MIN_LEVEL or t - last_swell < SWELL_GAP:
                st['swell cut'] += 1; continue
            last_swell = t
        if ty in ('pulse_on', 'pulse_off') and not (PULSE_KEEP[0] <= t <= PULSE_KEEP[1]):
            continue
        if ty == 'dip':                               # bed dips: a gain curve on the score's sustained buses
            depth = -(2.0 + 20.0 * (0.5 - float(e.get('level', 0.3))))
            a, b = t, t + float(e.get('len', 4.0))
            for bus in ('tracks', 'drones', 'strings_bed', 'strings_fx'):
                layers.setdefault(bus, [[0, 0.0], [720, 0.0]])
                layers[bus] = _merge_dip(layers[bus], a, b, depth)
            continue
        if ty in ('drone', 'end'):
            continue
        keep.append(e)
    st['swells kept'] = sum(1 for e in keep if e['type'] == 'swell')
    ch = [(c - CARD_GAP - 0.05, c - 0.02) for c in cards]   # nothing hits inside a card's hole (the 203.10 braam filled it)
    n0 = len(keep)
    keep = [e for e in keep if not (e['type'] in ('hit', 'braam', 'stinger', 'sub_drop') and any(a < e['t'] < b for a, b in ch))]
    st['hits in card holes'] = n0 - len(keep)
    for c in sfx:
        if c['name'] in ('braam', 'impact_hit', 'stinger', 'sub_drop') and any(a < c['t'] < b for a, b in ch):
            c['gain_db'] = -60.0; c['hit'] = False; c['note'] = 'v3: muted (inside a card hole) ' + (c.get('note') or '')
            st['sfx hits in card holes'] += 1
    return keep, dict(st), holes


def _merge_dip(pts, a, b, depth, ramp_in=0.4, ramp_out=1.0):
    """Add a dip (dB) over a..b to a piecewise-linear curve [[t, dB]] (dB values add)."""
    import numpy as np
    grid = sorted({p[0] for p in pts} | {a - ramp_in, a, b, b + ramp_out})
    base = np.interp(grid, [p[0] for p in pts], [p[1] for p in pts])
    dip = np.interp(grid, [a - ramp_in, a, b, b + ramp_out], [0, depth, depth, 0], left=0, right=0)
    return [[round(float(t), 3), round(float(v + d), 2)] for t, v, d in zip(grid, base, dip)]


if __name__ == '__main__':
    main()
