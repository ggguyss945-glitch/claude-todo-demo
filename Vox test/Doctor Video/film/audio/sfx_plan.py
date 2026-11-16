"""sfx_plan.py: the final mix's sound-design pass over the picture's SFX cue sheet ("If Your Doctor Calls At 3 AM...
DON'T ASK WHAT THEY FOUND").

film.py writes W/cues/sfx_cues.json from the picture: every drawn action at its frame. That sheet stays the source
and its timings are never moved (they are the picture's sync). This pass, applied by mix.py with `--plan full`
(audio/final_mix.sh), only
  0. maps the picture's names onto this film's recipes (PICTURE / picture_pass: film.py names some sounds the recipes
     know by other names or not at all: phone_ring -> the old landline's bell (one ring per cue), phone_pickup /
     phone_hangup -> receiver_up / receiver_down, cabinet_open -> medicine_cabinet, typing -> the typewriter of the
     rule cards, room_tone kinds -> house_night / er_bustle, the fluorescent bed -> waiting_room from the door's
     opening, breath_fast runs -> one breathing bed per run, tape_peel -> one strip per question (q 1..4)); drops
     what another layer carries (the pulse count: one ADD event with its three counts; the car's rain: drive_rain),
  1. re-levels picture cues that measure buried or too busy in the full-length checks (EDIT),
  2. adds the sounds the picture does not draw (ADD): the waiting room under the cold open, the 1979 rotary dial and
     the coffee at sunrise, the line hiss under Halverson's call, the receiver laid down like a sleeping baby, the
     streetlight at the bus stop, the NOW SERVING sign, the clipboard, the pulse count, the carry, Halverson's car
     idling and the drive in the rain, the ER, the dawn at Grandma's, the 3 AM office of the final twist, the
     outro's instantly connected call.
     An ADD row is skipped when the picture's sheet already has a cue of the same sound within 2 s of it (the same
     recipe after resolving, or the same FAMILY; the picture wins: no doubled sounds). A row with 'snap': name moves
     onto the picture's nearest cue of that name (within 1.2 s).
Every added cue is anchored to the narration (music_plan.resolve: 'sN' / 'eN' / 'wN:word' +- s, or seconds), so it
follows the recording, not a shot list, and survives picture changes.

    apply(cues, lines) -> (cues, log)      cues: the picture's list (not modified); log: what changed, one line each
    python3 sfx_plan.py [--cues W/cues]     prints the pass (dry run)
"""
import copy, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import music_plan as MP                                   # noqa: E402

# --------------------------------------------------------------------------------------------- EDIT (picture cues)
# (name, t0, t1, match params (subset), change, why). t0 / t1: anchors or seconds (the window the cue's t falls in).
# change: {'add_db': x} | {'gain_db': x} | {'min_db': x} | {'params': {...}} | {'space': s} | {'drop': True}
EDIT = [
    # first full mix (measure_mix.py): buried picture cues raised
    ('er_doors', 's348-1.0', 's348+2.0', {}, {'add_db': 7.0}, 'the ER doors opening (20.9 LU under)'),
    ('whoosh', 's295-0.5', 'e295', {}, {'add_db': 6.0}, '"I pulled my wrist free." (21.7 LU under)'),
    ('lamp_flicker', 's219-0.5', 'e219', {}, {'add_db': 4.0}, 'a dying tube (18 LU under)'),
    ('footsteps_porch', 's150-1.0', 'e150+2.0', {}, {'add_db': 4.0}, 'Halverson on the porch (18.7 LU under)'),
    ('paper', 's0', 'e455', {'dur': 0.6}, {'add_db': 4.0}, 'the rule cards\' paper (18-22 LU under)'),
]
THIN_MIN_GAP = 0.26                                       # (the dummy film's jaw ticks: no such cues in this film)
THIN_GAIN = {'tv': -13.0, None: -10.0}
THIN_QUIET = []

# --------------------------------------------------------------------------------------------- ADD
# (anchor, name, gain_db, space, params, why). params 'dur': 'until:<anchor>' -> seconds to that anchor.
ADD = [
    # ---- cold open
    ('s2+1.0', 'waiting_room', -2.0, 'waiting', {'dur': 'until:e6+0.6', 'flicker': 0.5, 'tv': 0.0, 'buzz': 0.6},
     'the waiting room under the very tall man'),
    ('w2:folded+0.2', 'sit_down', -6.0, 'waiting', {'kind': 'plastic'}, 'folded into one of those little chairs'),
    # ---- 1979
    ('e18-1.4', 'rotary_dial', -4.0, 'inside', {'digits': 3}, 'Grandma dials that place (1979)'),
    ('w29:coffee+0.3', 'mug_set', -4.0, 'close', {'kind': 'down'}, 'the cup of coffee at sunrise'),
    ('s29', 'ambience_dawn', -8.0, 'window', {'dur': 'until:s32', 'birds': 0.5}, 'sunrise, 1979: quiet birds'),
    # ---- rule 1
    ('s78-0.5', 'line_hiss', -8.0, None, {'dur': 'until:e80+0.6'}, 'Halverson on the line'),
    # ---- rule 2
    ('w117:set+0.3', 'receiver_down', -2.0, 'close', {'kind': 'set'}, 'set down on the counter like a sleeping baby'),
    # ---- rule 4
    ('s187', 'streetlight', -6.0, 'outside', {'dur': 'until:e191+1.0', 'flicker': 0.7}, 'the bus stop\'s light'),
    # ---- rule 6
    ('s223-0.25', 'now_serving', 0.0, 'waiting', {'sour': 0.7}, '"Now serving: 1979."'),
    ('w243:clipboard+0.3', 'clipboard', -4.0, 'waiting', {}, 'his clipboard'),
    # ---- rule 7: one pulse event, the picture's per-count cues dropped (picture_pass)
    ('w258:one', 'pulse_count', 0.0, 'tight', {'dur': 'until:w270:what-0.05', 'counts': 'gaps:w258:one,w260:two,w267:three',
     'bpm': [62, 48, 36, 27], 'clock': 0.7}, 'the count: the heartbeat and the clock slow with every number'),
    # ---- the rescue
    ('s303+0.2', 'carry_child', -4.0, 'inside', {}, 'I picked Milo up off the kitchen floor'),
    ('s306+0.6', 'rain_house', -2.0, 'porch', {'dur': 'until:s308+0.1'}, 'the front door open: the rain outside'),
    ('s308', 'halverson_car', -6.0, 'car', {'dur': 'until:w318:going+0.3', 'rain': 0.8}, 'parked: the engine running'),
    ('w318:going+0.2', 'drive_rain', 0.0, 'car', {'dur': 'until:s348-0.2', 'speed': 'fast'}, 'the drive in the rain'),
    ('s348+0.2', 'er_bustle', 0.0, 'er', {'dur': 'until:s362', 'monitors': 0.7, 'gurney': 0.5}, 'the ER, alive'),
    # ---- after
    ('s365', 'ambience_dawn', -8.0, 'window', {'dur': 'until:s372', 'birds': 0.6}, 'home at sunrise'),
    ('s379', 'office_3am', 0.0, 'office', {'dur': 'until:e400+0.6'}, 'a little office at Larkfield General, 3 AM'),
    # ---- outro
    ('w450:call-0.4', 'phone_connect', -6.0, 'close', {}, 'the one call that never puts you on hold'),
]
DEDUP_S = 2.0                                             # an ADD row yields to a picture cue of its sound this close

# picture name -> (recipe, extra params, gain or None, why); None drops the cue
PICTURE = {
    'phone_pickup': ('receiver_up', {}, -2.0, 'the old receiver lifted'),
    'phone_hangup': ('receiver_down', {'kind': 'hang'}, -2.0, 'hung up'),
    'cabinet_open': ('medicine_cabinet', {'action': 'open'}, -4.0, 'the mirror swung aside'),
    'typing': ('typewriter', {}, -8.0, 'the rules typed on a typewriter (the rule cards)'),
    'card_tap': ('touch_tap', {}, -8.0, 'a fingertip on the yellow card'),
    'key_press': ('touch_tap', {}, -6.0, 'a key'),
    'paper_flutter': ('paper', {'dur': 0.6}, -12.0, 'the rule card'),
    'paper_rustle': ('paper', {'dur': 0.9}, -10.0, 'the note'),
    'paper_slide': ('paper_under_door', {'dur': 1.3}, -2.0, 'the paper under the door'),
    'peephole_cover': ('peephole', {}, -6.0, 'the peephole cover'),
    'door_open': ('doorknob', {}, -6.0, 'the front door opened'),
    'door_knob': ('doorknob', {}, -8.0, 'the knob'),
    'hand_slap_soft': ('cloth_rustle', {'kind': 'grab', 'dur': 0.6}, -4.0, 'a hand over his mouth'),
    'flinch': ('cloth_rustle', {'dur': 0.5}, -12.0, 'his coat as he flinches'),
    'marker_write': ('pen_scratch', {'dur': 0.7}, -8.0, 'Ruth writing on hold (1979)'),
    'chair_creak': ('chair_rock', {'dur': 3.5}, -4.0, 'the empty chair still rocking'),
    'car_idle': ('halverson_car', {'rain': 0.0}, -14.0, 'her car in the driveway, engine running'),
    'monitor_beep': ('heart_monitor', {}, None, 'the monitor'),
    'wheelchair_roll': ('wheelchair', {}, None, 'Mom with the wheelchair'),
    'fluorescent_flicker': ('lamp_flicker', {}, None, 'a dying tube'),
    'lamp_click': ('light_switch', {}, None, 'turn a light on'),
    'ui_pop': ('ui_pop', {}, -9.0, 'card pops, under the voice'),
    'hold_click': None,                                   # the hold music itself (music_plan IDENTITY) starts there
    'cold_breath': None,                                  # nothing fits a cold touch; the wrist insert plays dry
    'car_drive': None,                                    # drive_rain (ADD) is the drive
    'car_accelerate': None,                               # "she drove faster": the score's riser carries it
}
WHO_HUM = {}
FAMILY = {'receiver_up': 'receiver', 'phone_pickup': 'receiver', 'receiver_down': 'hang', 'medicine_cabinet': 'cabinet',
          'paper_slide': 'paper_door', 'paper_under_door': 'paper_door', 'footsteps_wood_inside': 'steps',
          'footsteps_porch': 'steps', 'footsteps_hall': 'steps', 'doorknob': 'knob', 'light_switch': 'switch',
          'rain_house': 'rain', 'drive_rain': 'car', 'halverson_car': 'car', 'er_bustle': 'er',
          'waiting_room': 'waiting', 'ambience_dawn': 'dawn', 'office_3am': 'office', 'phone_connect': 'connect'}


def _t(a, lines):
    return float(a) if isinstance(a, (int, float)) else MP.resolve(a, lines)


def _match(c, name, a, b, sub):
    if c.get('name') != name:
        return False
    try:
        t = float(c['t'])
    except (KeyError, TypeError, ValueError):
        return False
    if not (a - 1e-3 <= t <= b + 1e-3):
        return False
    p = c.get('params') if isinstance(c.get('params'), dict) else {}
    return all(p.get(k) == v for k, v in sub.items())


def _canon(name, params=None):
    """The recipe a cue name plays (sfx.resolve; the name itself when sfx.py cannot be imported)."""
    try:
        import sfx as SX
        cn, _p, _n = SX.resolve(str(name), params if isinstance(params, dict) else {})
        return cn or str(name)
    except Exception:
        return str(name)


def _span(cn, params):
    """How long a cue's sound lasts on the picture, for the overlap test (steps: n treads at rate; else ~0)."""
    p = params if isinstance(params, dict) else {}
    try:
        if cn in ('footsteps_wood_inside', 'footsteps_stairs', 'footsteps_porch', 'footsteps_hall', 'footsteps_grass',
                  'hatchet_step'):
            n = float(p.get('n') or (4 if cn == 'hatchet_step' else 1))
            r = float(p.get('rate') or (0.75 if cn == 'hatchet_step' else 1.8))
            return max(0.0, (n - 1) / r + (0.3 if cn == 'hatchet_step' else 0.0))
        if p.get('dur') and cn in ('struggle', 'wet_drag', 'paper_under_door', 'ambience_woods', 'ambience_dawn',
                                   'ambience_night', 'room_tone', 'room_tone_house', 'burn_barrel', 'bulb', 'dogs_search',
                                   'crowd_parade', 'hospital_room', 'hospital_corridor', 'house_creaks', 'old_clock',
                                   'house_night', 'waiting_room', 'drive_rain', 'halverson_car', 'er_bustle',
                                   'office_3am', 'rain_house', 'streetlight', 'breath', 'line_hiss'):
            return float(p['dur'])
    except (TypeError, ValueError):
        pass
    return 0.0


ROOM = {'house_night': ('house_night', {'fridge': 0.6, 'clock': 0.6, 'creaks': 0.3}, 0.0),
        'house_1979': ('house_night', {'fridge': 0.3, 'clock': 0.7, 'creaks': 0.2}, -4.0),
        'house_evening': ('house_night', {'fridge': 0.5, 'clock': 0.3, 'creaks': 0.2}, -4.0),
        'warm_room': ('house_night', {'fridge': 0.4, 'clock': 0.3, 'creaks': 0.1}, -4.0),
        'er_busy': ('er_bustle', {'monitors': 0.7, 'gurney': 0.5}, 0.0)}


def picture_pass(out, lines, log):
    """PICTURE: film.py's names onto this film's recipes; what another layer carries is dropped."""
    def at(a, default=None):
        try:
            return MP.resolve(a, lines)
        except Exception:
            return default
    res, n0 = [], len(out)
    pulse = (at('s256', 0.0) - 0.5, at('w270:what', 0.0) + 0.3)      # the ADD pulse event carries counts and clock
    door6 = at('s216', 0.0)                                           # the living-room door opens on the waiting room
    office = at('s379', 1e9)
    rings = sorted(float(c['t']) for c in out if c.get('name') == 'phone_ring')
    runs, last = [], None                                              # breath_fast runs -> one breathing bed each
    for c in sorted([c for c in out if c.get('name') == 'breath_fast'], key=lambda c: float(c['t'])):
        t = float(c['t'])
        if runs and t - last < 1.6:
            runs[-1][1] = t
        else:
            runs.append([t, t, c.get('space')])
        last = t
    gulp_n = 0; dial_seen = False; peel_q = 0
    for c in out:
        nm = c.get('name'); p = dict(c.get('params') or {}) if isinstance(c.get('params'), dict) else {}
        try:
            t = float(c['t'])
        except (KeyError, TypeError, ValueError):
            res.append(c); continue
        why = None
        if nm == 'breath_fast':
            run = next((r for r in runs if abs(r[0] - t) < 1e-6), None)
            if run is None:
                continue                                  # inside a run: the run's bed plays it
            d = round(run[1] - run[0] + 1.0, 2)
            g = -18.0 if run[2] == 'car' else (-14.0 if 820 < t < 870 else -12.0)
            c = dict(c, name='breath', params={'kind': 'panting', 'dur': d}, gain_db=g,
                     space='inside' if run[2] in (None, 'car') else run[2] if run[2] != 'close' else 'inside')
            why = f'Milo breathing fast and deep: one bed of {d} s'
        elif nm == 'phone_ring':
            if t >= office - 30.0:                        # the narrator's phone now: the modern ring stays
                res.append(c); continue
            nxt = [x for x in rings if x > t + 0.05]
            gap = (min(nxt) - t) if nxt else 2.0
            on = round(max(0.3, min(1.2, gap - 0.12)), 2)
            c = dict(c, name='landline_ring', params={'n': 1, 'on': on}); why = f'the old landline\'s bell, one ring ({on} s)'
        elif nm == 'room_tone' and p.get('kind') in ROOM:
            rn, extra, g = ROOM[p['kind']]
            q = dict(extra); q['dur'] = p.get('dur', 10.0)
            if p['kind'] == 'warm_room':                  # home after the ER; the final twist is the office (ADD)
                q['dur'] = round(max(1.0, office - t), 2)
            c = dict(c, name=rn, params=q, gain_db=g); why = f'room tone {p["kind"]} -> {rn}'
        elif nm == 'fluorescent_buzz':
            d = float(p.get('dur') or 2.0)
            if d < 5.0:
                c = dict(c, name='lamp_flicker', params={'dur': d}, gain_db=-6.0); why = 'the tubes stutter on'
            else:                                         # the bed starts when the door opens on it
                t1 = t + d; t0 = max(t, door6 + 1.2)
                c = dict(c, t=round(t0, 3), name='waiting_room', params={'dur': round(t1 - t0, 2), 'flicker': 0.6,
                         'tv': 0.5, 'buzz': 0.7}, gain_db=0.0, space='waiting')
                why = f'the waiting room from the door ({t0:.2f}) on'
        elif nm == 'pulse_count' or (nm == 'clock_tick' and pulse[0] <= t <= pulse[1]):
            log.append(f'PIC  {nm:18s} {t:7.2f} dropped: the ADD pulse_count carries the counts and the clock'); continue
        elif nm == 'rain' and p.get('inside_car'):
            log.append(f'PIC  rain(car)          {t:7.2f} dropped: halverson_car / drive_rain (ADD) carry the car\'s rain')
            continue
        elif nm == 'tape_peel':
            peel_q = min(4, peel_q + 1)
            c = dict(c, params={'q': peel_q}, space='tight', gain_db=0.0); why = f'strip {peel_q}'
        elif nm == 'gulp':
            gulp_n += 1
            if gulp_n % 2 == 0:
                continue
            c = dict(c, name='sip', params={}, gain_db=-8.0, space='close'); why = 'a swallow of water'
        elif nm == 'dial_beep':
            if dial_seen:
                continue
            dial_seen = True
            c = dict(c, name='phone_connect', params={}, gain_db=-4.0, space='close'); why = 'Mom dials, it connects'
        elif nm in PICTURE:
            m = PICTURE[nm]
            if m is None:
                log.append(f'PIC  {nm:18s} {t:7.2f} dropped'); continue
            rn, extra, g, why = m
            q = dict(p); q.update(extra)
            c = dict(c, name=rn, params=q)
            if g is not None:
                c['gain_db'] = g
        if why:
            log.append(f'PIC  {nm:18s} {t:7.2f} -> {c["name"]} {c.get("params")} {c.get("gain_db", 0):+.1f} dB  ({why})')
        res.append(c)
    log.append(f'PICTURE: {n0} picture cues -> {len(res)}')
    return res


def apply(cues, lines):
    """The picture's cue list -> the mixed cue list (a new list) and a log of every change."""
    out = [copy.deepcopy(c) for c in cues if isinstance(c, dict)]
    log = []
    out = picture_pass(out, lines, log)
    # EDIT
    for name, a, b, sub, ch, why in EDIT:
        try:
            ta, tb = _t(a, lines), _t(b, lines)
        except Exception as e:
            log.append(f'EDIT {name} {a}..{b}: bad anchor ({e!r}): skipped'); continue
        hit = [c for c in out if _match(c, name, ta, tb, sub)]
        for c in hit:
            g0 = float(c.get('gain_db', 0.0) or 0.0)
            if ch.get('drop'):
                c['_drop'] = True
            if 'add_db' in ch:
                c['gain_db'] = round(g0 + ch['add_db'], 2)
            if 'gain_db' in ch:
                c['gain_db'] = ch['gain_db']
            if 'min_db' in ch:
                c['gain_db'] = max(g0, ch['min_db'])
            if 'params' in ch:
                c['params'] = dict(c.get('params') or {}, **ch['params'])
            if 'space' in ch:
                c['space'] = ch['space']
        log.append(f'EDIT {name:18s} {ta:7.2f}-{tb:7.2f} {sub or ""} {ch}: {len(hit)} cue(s)  ({why[:70]})')
    out = [c for c in out if not c.get('_drop')]
    # THIN the speech ticks
    quiet = []
    for a, b, g in THIN_QUIET:
        try:
            quiet.append((_t(a, lines), _t(b, lines) + 0.3, g))
        except Exception:
            pass
    sp = sorted([c for c in out if c.get('name') == 'dummy_clack' and (c.get('params') or {}).get('kind') == 'speech'],
                key=lambda c: float(c['t']))
    keep, last, n0 = [], -9.0, len(sp)
    for c in sp:
        t = float(c['t'])
        if t - last < THIN_MIN_GAP:
            c['_drop'] = True; continue
        last = t
        g = THIN_GAIN.get(c.get('space') if c.get('space') == 'tv' else None)
        for a, b, gq in quiet:
            if a <= t <= b:
                g = gq
        c['gain_db'] = min(float(c.get('gain_db', 0.0) or 0.0), g)
        keep.append(c)
    out = [c for c in out if not c.get('_drop')]
    log.append(f'THIN dummy_clack speech: {n0} -> {len(keep)} ticks (>= {THIN_MIN_GAP} s apart, -10 room / -13 TV / '
               f'-15 under the tape cry)')
    # ADD
    have, fam = {}, {}
    for c in out:
        try:
            tc = float(c['t'])
        except (KeyError, TypeError, ValueError):
            continue
        cn = _canon(c.get('name'), c.get('params'))
        span = _span(cn, c.get('params'))
        for k in {str(c.get('name')), cn}:
            have.setdefault(k, []).append((tc, tc + span))
        if cn in FAMILY:
            fam.setdefault(FAMILY[cn], []).append((tc, tc + span))
    for a, name, g, space, params, why in ADD:
        try:
            t = _t(a, lines)
            p = dict(params)
            if isinstance(p.get('dur'), str) and p['dur'].startswith('until:'):
                p['dur'] = round(max(0.3, _t(p['dur'][6:], lines) - t), 2)
            for k_ in ('groups', 'counts'):           # 'gaps:a,b,c' -> seconds from the first anchor
                if isinstance(p.get(k_), str) and p[k_].startswith('gaps:'):
                    gs = [_t(x, lines) for x in p[k_][5:].split(',')]
                    p[k_] = [round(x - gs[0], 3) for x in gs]
        except Exception as e:
            log.append(f'ADD {name} at {a}: bad anchor ({e!r}): skipped'); continue
        cn = _canon(name, p)
        a0, a1 = t, t + _span(cn, p)
        if a1 - a0 > 4.0:                                 # a bed yields only to a picture bed covering half of it
            near = lambda iv: sum(max(0.0, min(a1, y) - max(a0, x)) for x, y in iv) >= 0.5 * (a1 - a0)
        else:
            near = lambda iv: any(a0 - DEDUP_S < y and x < a1 + DEDUP_S for x, y in iv)
        if p.pop('keep', False):
            pass
        elif near(have.get(name, [])) or near(have.get(cn, [])) or (cn in FAMILY and near(fam.get(FAMILY[cn], []))):
            log.append(f'ADD  {name:18s} {t:7.2f} skipped: the picture already has it ({FAMILY.get(cn, cn)})'); continue
        sn = p.pop('snap', None)
        if sn:
            cand = [x for x, _y in have.get(sn, []) if abs(x - t) <= 1.2]
            if cand:
                t0_ = t; t = min(cand, key=lambda x: abs(x - t0_))
                log.append(f'SNAP {name:18s} {t0_:7.2f} -> {t:7.2f} (the picture\'s {sn})')
        c = {'t': round(t, 3), 'name': name, 'gain_db': g, 'pan': 0.0, 'params': p, 'plan': 'sfx_plan'}
        if space:
            c['space'] = space
        out.append(c)
        log.append(f'ADD  {name:18s} {t:7.2f} {g:+5.1f} dB {space or "-":9s} {p}  ({why[:70]})')
    out.sort(key=lambda c: float(c.get('t', 0.0)) if isinstance(c.get('t'), (int, float)) else 1e9)
    return out, log


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--cues', default=os.path.join(MP.W, 'cues'))
    A = ap.parse_args()
    L, _d = MP.load_lines()
    sc = json.load(open(os.path.join(A.cues, 'sfx_cues.json')))
    new, lg = apply(sc, L)
    print('\n'.join(lg))
    print(f'{len(sc)} picture cues -> {len(new)} mixed cues')
