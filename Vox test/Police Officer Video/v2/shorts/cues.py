"""shorts.cues: the cue lists a Short hands to the mixer (format of film.py's sfx_cues.json / music_cues.json plus a
`kind` per cue: 'hit' (strong: slams, stamps, twists, knocks, the press), 'transient' (whooshes on cuts and punches, UI pops,
clicks), 'diegetic' (story sounds from the re-used long-video staging: footsteps, radio, paper...), 'bed' (continuous),
and `why` (what on screen it belongs to).

    sfx, music = build(E, spec_short)        E: a finished shorts.edit.Edit (shots bound to a Renderer for diegetic events)
    stats(sfx, duration) -> per-10-s counts of hits and transients (playbook: 3-6 hits, 12-16 transients per 10 s)
"""
import json, os
from stage import LongSrc, CustomSrc, SplitSrc

DIEGETIC_SKIP = {'whoosh', 'impact_hit', 'glitch', 'ui_pop', 'typing', 'riser', 'braam', 'stinger', 'sub_drop', 'ambience_night',
                 'room_tone', 'heartbeat', 'tinnitus'}
HIT_NAMES = {'impact_hit', 'braam', 'sub_drop', 'stinger', 'knock_door'}
CATALOG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'audio', 'catalog_epidemic.json')


def _e(t, name, gain_db=0.0, ckind='transient', why='', pan=0.0, space=None, **params):
    e = dict(t=round(float(t), 3), name=name, gain_db=round(float(gain_db), 1), pan=round(float(pan), 2), kind=ckind, why=why)
    if space: e['space'] = space
    if params: e['params'] = params
    return e


def diegetic(E, R):
    """Story sounds of the re-used staging (acting events: knocks, steps, radio, beeps, paper, car doors ...)."""
    out = []
    for vs in E.shots:
        srcs = [vs.src.top, vs.src.bot] if isinstance(vs.src, SplitSrc) else [vs.src]
        for k, src in enumerate(srcs):
            if not isinstance(src, (LongSrc, CustomSrc)) or src.T0 is None: continue
            T0 = src.tmap(vs.t0); T1 = src.tmap(vs.t1)
            if isinstance(src, CustomSrc):
                shots = [src.shot(T0)]
            else:
                shots = [s for s in R.F.shots if s.t1 > T0 and s.t0 < T1]
            for sh in shots:
                try:
                    R.build(sh)
                except Exception:
                    continue
                for c in sh.sfx:
                    if c['name'] in DIEGETIC_SKIP: continue
                    if not (T0 - 0.02 <= c['t'] <= T1): continue
                    t = vs.t0 + (c['t'] - T0) / src.speed
                    e = _e(t, c['name'], c.get('gain_db', 0.0) - (3 if k else 0), 'diegetic', 'story: %s shot' % sh.kind, c.get('pan', 0.0),
                           c.get('space'), **(c.get('params') or {}))
                    if c['name'] == 'knock_door': e['kind'] = 'hit'
                    out.append(e)
    return out


def build(E, sp, R=None):
    sfx = []
    dur = E.dur
    # ---- cuts and punches
    starts = [s.t0 for s in E.shots]
    hit_ts = [e['t'] for e in E.events if e['type'] in ('slam', 'stamp', 'flash')] + [c['t'] for c in E.cues if c['name'] in HIT_NAMES]
    for k, s in enumerate(E.shots):
        if k == 0 or s.fx.get('rewind'): continue
        if any(abs(s.t0 - h) < 0.06 for h in hit_ts): continue
        hard = s.fx.get('hard_cut', False)
        sfx.append(_e(s.t0 - (0.05 if hard else 0.0), 'whoosh', -6 if hard else -12, 'transient', 'cut', kind_='hard' if hard else 'soft'))
        for (tc, *_r) in getattr(s, 'cuts', []):
            sfx.append(_e(tc - 0.03, 'whoosh', -15, 'transient', 'cut', kind_='soft'))
        for (tp, lev) in s.punches:
            key = any(abs(c.get('kt', -9) - tp) < 0.02 for c in E.chunks)
            if key: sfx.append(_e(tp, 'impact_hit', -9, 'transient', 'keyword zoom punch', size=0.55))
            else: sfx.append(_e(tp - 0.04, 'whoosh', -16, 'transient', 'zoom punch', kind_='soft'))
    # ---- overlay events
    for e in E.events:
        t, typ = e['t'], e['type']
        if typ == 'slam':
            sfx.append(_e(t, 'impact_hit', e.get('gain', 0), 'hit', 'text slam ' + e['text'].replace('\n', ' '), size=e.get('size_sfx', 1.1)))
            if e.get('big'): sfx.append(_e(t, 'stinger', -3, 'hit', 'big slam'))
        elif typ == 'stamp':
            sfx.append(_e(t, 'impact_hit', -3, 'hit', 'stamp ' + e['text'], size=0.8))
        elif typ in ('tag', 'bubble', 'label', 'loop'):
            sfx.append(_e(t, 'ui_pop', -6, 'transient', '%s %s' % (typ, e.get('text', ''))))
        elif typ == 'glitch':
            sfx.append(_e(t, 'glitch', -6, 'transient', 'glitch', dur=round(e.get('dur', 0.15) + 0.1, 2), amount=0.8))
        elif typ == 'subscribe':
            lead = max(0.12, min(0.5, e.get('lead', 0.5)))
            sfx.append(_e(t - lead, 'ui_pop', -4, 'transient', 'SUBSCRIBE button pops in'))
            sfx.append(_e(t - lead, 'whoosh', -10, 'transient', 'SUBSCRIBE button flies in', kind_='soft'))
            sfx.append(_e(t, 'pen_click', 0, 'hit', 'SUBSCRIBE press (click)', n=1))
            sfx.append(_e(t, 'impact_hit', -8, 'hit', 'SUBSCRIBE press (body)', size=0.6))
            sfx.append(_e(t + 0.06, 'ui_pop', -2, 'transient', 'SUBSCRIBED + bell', kind_='bell'))
            sfx.append(_e(t + 1.55, 'whoosh', -14, 'transient', 'button out', kind_='soft'))
        elif typ == 'endcard':
            sfx.append(_e(t - 0.06, 'whoosh', -6, 'transient', 'end card in', kind_='hard'))
            for k, h in enumerate(e.get('hits', [])[:4]):   # card + FULL VIDEO, then one per question line (the tail
                sfx.append(_e(h, 'impact_hit', -1 if k == 0 else -3, 'hit', 'end card line', size=1.2 if k == 0 else 1.0))
        elif typ == 'comments':
            sfx.append(_e(t, 'ui_pop', -5, 'transient', 'comments panel'))
            sfx.append(_e(t + 0.3, 'typing', -10, 'transient', 'comment typed', dur=0.5, cps=12))
        elif typ == 'notebook':
            sfx.append(_e(t, 'paper', -6, 'transient', 'notebook page', dur=0.5))
            for x in e.get('ticks', []):
                sfx.append(_e(x - 0.35, 'paper', -10, 'transient', 'handwriting', dur=0.3))
                sfx.append(_e(x, 'pen_click', -6, 'transient', 'tick'))
        elif typ == 'complaint':
            sfx.append(_e(t, 'paper', -4, 'transient', 'complaint form', dur=0.6))
            for r, x in e.get('hl', {}).items():
                sfx.append(_e(x, 'ui_pop', -8, 'transient', 'highlight'))
        elif typ == 'phone':
            for (tt, st) in e['states']:
                if st == 'calling': sfx.append(_e(tt + 0.2, 'phone_ring', -4, 'diegetic', 'phone calling', space='phone', kind_='ringback', dur=1.6))
                elif st == 'busy': sfx.append(_e(tt, 'phone_busy', -3, 'diegetic', 'phone busy', space='phone', dur=2.2))
                elif st == 'connected': sfx.append(_e(tt, 'phone_pickup', -2, 'diegetic', 'phone connected', space='close'))
                sfx.append(_e(tt, 'ui_pop', -8, 'transient', 'phone state'))
        elif typ == 'wave':
            sfx.append(_e(t, 'ui_pop', -7, 'transient', 'waveform panel'))
        elif typ == 'rule':
            sfx.append(_e(t, 'ui_pop', 0, 'hit', 'rule card'))
            sfx.append(_e(t + 0.4, 'typing', -8, 'transient', 'rule typed', dur=1.6, cps=14))
        elif typ == 'rewind':
            sfx.append(_e(t, 'glitch', -2, 'transient', 'REWIND', dur=0.25, amount=1.0))
            sfx.append(_e(t, 'whoosh', -4, 'transient', 'REWIND whip', kind_='hard'))
    # ---- HUD ticks
    for (t, st) in E.huds:
        if st.get('pop', True) and t > 0.05:
            sfx.append(_e(t, 'ui_pop', -7, 'transient', 'HUD %s' % st.get('value', st.get('clock', ''))))
    # ---- explicit staging cues
    for c in E.cues:
        c = dict(c); c.setdefault('why', 'staging')
        sfx.append(c)
    # ---- diegetic from the long-video staging
    if R is not None:
        sfx.extend(diegetic(E, R))
    # ---- beds
    sfx.append(_e(0.0, 'ambience_night', -24, 'bed', 'night bed under everything', dur=round(dur, 2)))
    tg = [b for b in E.T['beats'] if b.get('tension')]
    if tg:
        b = tg[0]; g0 = b['voice_off'] + 0.05; g1 = b['t1']
        sfx.append(_e(g0, 'tinnitus', -14, 'bed', 'tension gap', dur=round(g1 - g0 + 0.3, 2)))
        sfx.append(_e(g0, 'room_tone', -18, 'bed', 'tension gap', dur=round(g1 - g0 + 0.2, 2)))
        hb0 = max(0.0, g0 - 12.0)
        sfx.append(_e(hb0, 'heartbeat', -12, 'bed', 'heartbeat 70 -> 90 bpm into the gap', bpm=70, bpm_end=90, dur=round(g1 - hb0, 2)))
    for c in sfx:
        if 'params' in c and 'kind_' in c['params']:
            c['params']['kind'] = c['params'].pop('kind_')
    sfx = [c for c in sfx if 0 <= c['t'] <= dur + 0.01]
    sfx = thin(sfx, dur)
    sfx.sort(key=lambda c: (c['t'], c['name']))
    return sfx, music(E, sp)


def prio(c):
    w = c.get('why', '')
    if c['kind'] == 'bed': return 99
    if c['kind'] == 'hit': return 50 if c['name'] in ('braam', 'sub_drop', 'knock_door', 'pen_click', 'radio_click') else 40
    if c['kind'] == 'diegetic': return 20 if c['name'] not in ('footsteps_porch', 'footsteps_wood_inside') else 12
    if w == 'staging': return 18
    if w.startswith('keyword'): return 15
    if w == 'cut': return 14
    if w.startswith(('tag', 'bubble', 'label', 'SUBSCRIBE', 'end card', 'comments', 'phone', 'REWIND', 'rule', 'stamp')): return 13
    if w.startswith('HUD'): return 9
    if w == 'zoom punch': return 6
    return 10


def thin(sfx, dur, max_tr=16, max_hit=6):
    """Keep the playbook density: <= 6 strong hits and <= 16 transients (hits included) per 10 s window. Extra hits are
    demoted to transients (gain -4 dB); then the lowest-priority transients are dropped (filler-punch whooshes first,
    then HUD pops, footsteps ...). Beds are never touched."""
    for k in range(int(dur // 10) + 1):
        a, b = 10 * k, min(dur + 0.01, 10 * k + 10)
        if b - a < 0.5: break
        sc = (b - a) / 10.0
        mh, mt = max(2, int(round(max_hit * sc))), max(4, int(round(max_tr * sc)))
        hits = sorted([c for c in sfx if a <= c['t'] < b and c['kind'] == 'hit'], key=prio)
        while len(hits) > mh:
            c = hits.pop(0); c['kind'] = 'transient'; c['gain_db'] = round(c['gain_db'] - 4, 1); c['why'] += ' (demoted)'
        mn = max(1, int(round(3 * sc)))
        if len(hits) < mn:                       # too few strong hits: promote keyword impacts / glitches / clicks, then cuts
            cand = sorted([c for c in sfx if a <= c['t'] < b and c['kind'] in ('transient', 'diegetic')
                           and c['name'] in ('impact_hit', 'stinger', 'glitch', 'radio_click', 'pen_click', 'mail_slot', 'bodycam_beep')],
                          key=lambda c: -prio(c))
            for c in cand:
                if len(hits) >= mn: break
                c['kind'] = 'hit'; c['gain_db'] = round(c['gain_db'] + 4, 1); c['why'] += ' (promoted to hit)'; hits.append(c)
            cuts = [c for c in sfx if a <= c['t'] < b and c.get('why') == 'cut']
            for c in cuts[::2]:
                if len(hits) >= mn: break
                e = _e(c['t'] + 0.05, 'impact_hit', -4, 'hit', 'cut accent (added)', size=0.8); sfx.append(e); hits.append(e)
        tr = sorted([c for c in sfx if a <= c['t'] < b and c['kind'] in ('hit', 'transient', 'diegetic')], key=prio)
        drop = set()
        n = len(tr)
        for c in tr:
            if n <= mt: break
            if c['kind'] == 'hit': break
            drop.add(id(c)); n -= 1
        sfx = [c for c in sfx if id(c) not in drop]
    for c in sfx: c['prio'] = prio(c)
    return sfx


def music(E, sp):
    dur = E.dur
    b_by = {b['n']: b for b in E.T['beats']}
    tg = [b for b in E.T['beats'] if b.get('tension')]
    twist = E.flags.get('twist_t')
    sub = E.flags.get('subscribe_t')
    endc = E.flags.get('end_t')
    ev = []
    for e in E.events:
        if e['type'] == 'slam': ev.append(dict(t=round(e['t'], 3), type='hit', level=0.85 if e.get('big') else 0.7))
        if e['type'] == 'endcard':
            ev.append(dict(t=round(e['t'], 3), type='stinger', level=0.8))
            for h in e.get('hits', []): ev.append(dict(t=round(h, 3), type='hit', level=0.8))
    if tg:
        g0 = tg[0]['voice_off'] + 0.05; g1 = tg[0]['t1']
        ev.append(dict(t=round(g0, 3), type='silence', level=0.0, len=round(g1 - g0, 3)))
        ev.append(dict(t=round(g1, 3), type='riser', level=0.6, len=3.0))
    if twist:
        ev.append(dict(t=round(twist, 3), type='braam', level=1.0))
        ev.append(dict(t=round(twist, 3), type='sub_drop', level=0.9))
    ev.extend(E.music)
    ev.append(dict(t=round(dur - 0.15, 3), type='end', level=0.6))
    ev.sort(key=lambda e: e['t'])
    # intensity: builds to the subscribe, swells into the gap, out for the gap, peaks on the twist, holds through the CTA
    pts = [[0.0, 0.5], [2.0, 0.55]]
    if sub: pts += [[sub - 1.0, 0.65], [sub + 1.5, 0.6]]
    if tg:
        pts += [[tg[0]['voice_off'] - 1.0, 0.85], [tg[0]['voice_off'] + 0.05, 0.0], [tg[0]['t1'] - 0.02, 0.0]]
    if twist: pts += [[twist, 1.0], [twist + 3.0, 0.85]]
    if endc: pts += [[endc, 0.9]]
    pts += [[dur, 0.8]]
    pts = sorted(pts, key=lambda p: p[0])
    m = sp['music']
    track, base = m['track'], m['start_in_track']
    start = base
    align = E.flags.get('music_align')               # (short time, track time): slip the track so that section lands there
    if align: start = max(0.0, align[1] - align[0])
    try:
        cat = json.load(open(CATALOG))
        mus = cat.get('music') or {}
        info = mus.get(track) if isinstance(mus, dict) else None
    except Exception:
        info = None
    return dict(duration=round(dur, 3), track=track, start_in_track=round(start, 2), track_note=m.get('note'),
                alternate=E.flags.get('alt_track'), intensity=[[round(a, 3), round(b, 2)] for a, b in pts], events=ev,
                tension_gap=[round(tg[0]['voice_off'] + 0.05, 3), round(tg[0]['t1'], 3)] if tg else None,
                subscribe_t=sub, twist_t=twist, end_card_t=endc, loop='the last cue must be the same sound as frame 1')


def stats(sfx, dur):
    out = []
    for k in range(int(dur // 10) + 1):
        a, b = k * 10, min(dur, k * 10 + 10)
        if b - a < 3: break
        hits = sum(1 for c in sfx if a <= c['t'] < b and c['kind'] == 'hit')
        tr = sum(1 for c in sfx if a <= c['t'] < b and c['kind'] in ('hit', 'transient', 'diegetic'))
        out.append((a, round(hits * 10 / (b - a), 1), round(tr * 10 / (b - a), 1)))
    return out
