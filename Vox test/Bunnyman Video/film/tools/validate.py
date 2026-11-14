"""tools/validate.py: the staging validator for the Bunnyman film's shot list (film.py).

    python3 tools/validate.py                      # every check on every shot; exit code 1 on any ERROR
    python3 tools/validate.py --shots 100-140      # a range (the cut / state checks still look at the neighbours)
    python3 tools/validate.py --json W/tests/polish/validate.json --fps 10

It reads the plan the way the renderer builds it (Film(timeline) -> shots -> builders: sets with their anchors, floors and
furniture footprints, actors with their clips, props) and checks what can be checked without looking at pixels:

  ANCHOR  set anchors: every staging point lies on a floor of its level (a point anchor with its plan y and its height
          swapped once put the bathroom keyhole in the downstairs hall at attic height)
  FLOOR   a figure's feet are inside a room's floor and clear of furniture footprints (sets' walkable()); a seated figure
          sits on a seat anchor; nobody stands on a couch, a bed or a table
  LEVEL   a figure's feet are at the floor height of where it stands (stairs: the tread's height); paths too, key by key
  OVERLAP two figures closer than 0.32 m on the plan (bodies inside each other)
  REACH   reach / hand-over / point contacts that miss their target at full weight (Acting.misses, > 20 design px)
  PROP    props: a PropTrack that jumps when it changes state (picked up from somewhere else than its hand), a prop held by
          two hands at once, a prop drawn by the set AND held by an actor in the same shot (doubled)
  CUTPOS  continuity across cuts: the same person on the same plan (the house and its yard / the woods / the hospital)
          in consecutive set shots, or with only close-ups / inserts between them (< 8 s), stands > 0.8 m from where the
          last shot left them, with no walk to explain it
  STATE   the story's states shot by shot: the living-room curtains (open until 11:07, then shut), the back porch light
          (off at night, now), the mail-slot flap (open from 1:40 until Mom shuts it), the front door (a crack at
          midnight), the kitchen window and the back door (whole until 4:30, then smashed / open), the bathroom door
          (locked from 4:30 until the key), Mom's arms (scratched from dawn), the light under the bathroom door
  CAM     camera: a move (> 10 % magnification or > 120 design px of pan) that lasts > 4.2 s; a set shot > 3 s whose
          camera moves while nobody in it acts (only the camera moves over still figures); an empty set held > 5 s
          under a moving camera
  LEN     shot lengths (< 0.6 s outside flashes / blacks; > 7 s outside rule cards, cards and the VHS pause) + the
          median / cuts per minute against the police film's pace
  LIP     lips move only on the actor's own lines (film.lip_check), except the allowed ones (the masked Bunnyman)
Severity: ERROR (a visible mistake: fix it), WARN (look at it on the strips), INFO. Allowed exceptions are listed in ALLOW
with the reason. The result table goes to stdout and --json.
"""
import argparse, json, math, os, sys, time
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
os.chdir(HERE)
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('--shots', default=None)
ap.add_argument('--fps', type=float, default=8.0, help='sampling rate of the acting checks')
ap.add_argument('--json', default=os.path.join(HERE, '_work', 'tests', 'polish', 'validate.json'))
ap.add_argument('--quiet', action='store_true')
ap.add_argument('--no-lip', action='store_true')
a = ap.parse_args()

from engine.core import set_render_size
set_render_size(960, 540)
import film as FM
import characters as CH
import sets as ST

t_start = time.time()
F = FM.Film(json.load(open(os.path.join(FM.ALIGN, 'timeline.json'))))
SH = F.shots
N = len(SH)


def sel():
    if not a.shots: return list(range(N))
    out = []
    for part in a.shots.split(','):
        if '-' in part:
            x, y = part.split('-'); out += list(range(int(x), int(y) + 1))
        else: out.append(int(part))
    return [k for k in out if 0 <= k < N]


KS = sel()
issues = []


def add(sev, k, check, msg, t=None):
    issues.append(dict(sev=sev, shot=k, t=None if t is None else round(float(t), 2), check=check, msg=msg,
                       t0=round(SH[k].t0, 2) if k is not None else None))


# ---------------------------------------------------------------------------------------------------- allowed exceptions
# (check, shot predicate, reason): an exception is written down here with the reason, never silently skipped
def _line_shot(i):
    return lambda s: s.t0 <= F.t(i) < s.t1


def _masked(s, who):
    """The Bunnyman's girl's-voice lines (L): the mask has no mouth."""
    if who != 'bunny': return False
    ls = F.lines_in(s.t0, s.t1)
    return any(l['who'] == 'L' for l in ls) and not any(l['who'] == 'D' for l in ls)


ALLOW = [
    ('LIP', _masked, "the Bunnyman's mask has no mouth: the girl's voice comes from inside it (he tilts / sobs instead)"),
]

# ---------------------------------------------------------------------------------------------------- build helpers
HOUSE = ('living', 'hall', 'up', 'june', 'bath', 'attic', 'kitchen', 'yard', 'front')
PLAN_OF = {r: 'house' for r in HOUSE}
PLAN_OF.update(woods='woods', hosp='hosp', parade='parade')
LEVELS = {'living': 0.0, 'hall': 0.0, 'kitchen': 0.0, 'upstairs': 2.85, 'june': 2.85, 'bath': 2.85, 'attic': 5.45}
STAIR = dict(x0=0.5, x1=1.15, y0=0.9, y1=4.85)


def stair_Y(x, y):
    """The tread height under (x, y) on the hall flight (None: not on the stairs)."""
    if not (STAIR['x0'] <= x <= STAIR['x1'] and STAIR['y0'] <= y <= STAIR['y1']): return None
    k = int(math.floor((y - 0.9) / 0.26)) + 1
    return max(0.0, min(15, k)) * 0.19


def in_poly(pt, q, pad=0.0):
    if pad:
        xs = [p[0] for p in q]; ys = [p[1] for p in q]
        if not (min(xs) - pad <= pt[0] <= max(xs) + pad and min(ys) - pad <= pt[1] <= max(ys) + pad): return False
        # a padded axis-aligned test is enough for the house's rectangular rooms
        return True
    return ST.sets_bunny._in_poly(pt, q) if hasattr(ST, 'sets_bunny') else _in_poly(pt, q)


def _in_poly(pt, q):
    x, y = pt; ins = False; n = len(q)
    for i in range(n):
        x1, y1 = q[i]; x2, y2 = q[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / ((y2 - y1) or 1e-12)
            if x < xi: ins = not ins
    return ins


def floor_level(sp, x, y, Y):
    """Expected floor height at plan (x, y) for a figure whose feet are at Y: the stairs' tread, else the level of a room
    containing the point that is closest to Y (the hall and the upstairs corridor overlap on the plan)."""
    s = stair_Y(x, y)
    if s is not None and sp.room in ('hall', 'up', None) and abs(Y - s) < 0.6: return s
    rooms = (sp.info.get('rooms') or {})
    best = None
    for nm, q in rooms.items():
        if nm not in LEVELS: continue
        if _in_poly((x, y), q):
            L = LEVELS[nm]
            if best is None or abs(L - Y) < abs(best - Y): best = L
    return best


def plan_pos(sp, q, t):
    """(X, Yp, Y) of a P entry at time t (static spot or the path's linear interpolation)."""
    path = q.get('path')
    if not path:
        s = FM.spot_of(sp, q['at'], kind=q.get('kind'))
        return (s.X, s.Yp, s.Y)
    keys = []
    for (tk, at) in path:
        s = FM.spot_of(sp, at); keys.append((float(tk), s.X, s.Yp, s.Y))
    if t <= keys[0][0]: return keys[0][1:]
    if t >= keys[-1][0]: return keys[-1][1:]
    for ka, kb in zip(keys, keys[1:]):
        if ka[0] <= t <= kb[0]:
            u = (t - ka[0]) / max(1e-6, kb[0] - ka[0])
            return tuple(ka[j] + (kb[j] - ka[j]) * u for j in (1, 2, 3))
    return keys[-1][1:]


def figure_kind(sp, q):
    s0 = FM.spot_of(sp, q['at'] if q.get('at') is not None else q['path'][0][1], kind=q.get('kind'))
    return q.get('kind') or {'seat': 'seat', 'kneel': 'kneel', 'lie': 'lie'}.get(s0.kind, 'stand'), s0


def cam_mag(cs):
    return cs.zoom * cs.fz * cs.pz


# ---------------------------------------------------------------------------------------------------- ANCHOR: the sets' staging points
seen_sets = set()


def check_anchors(k, sp):
    key = (sp.name, sp.room)
    if key in seen_sets: return
    seen_sets.add(key)
    rooms = sp.info.get('rooms') or {}
    if not rooms or not any(nm in LEVELS for nm in rooms): return
    for nm, s in sp.anchors.items():
        if '.' in nm: continue
        if s.kind not in ('point', 'stand', 'kneel', 'surface'): continue
        ok = False; cands = []
        for rn, q in rooms.items():
            if rn not in LEVELS: continue
            if in_poly((s.X, s.Yp), q, pad=0.2):
                L = LEVELS[rn]; cands.append(rn)
                st = stair_Y(s.X, s.Yp)
                lo, hi = L - 0.3, L + 2.75
                if st is not None and rn == 'hall': hi = 2.85 + 2.75
                if lo <= s.Y <= hi: ok = True
        if cands and not ok:
            add('ERROR', k, 'ANCHOR', 'set %s anchor %r at plan (%.2f, %.2f) height %.2f m is not on the floor level of %s (y and height swapped?)'
                % (sp.name, nm, s.X, s.Yp, s.Y, '/'.join(cands)))


# ---------------------------------------------------------------------------------------------------- per-shot checks
SAMPLE = {}


def sample_times(sh, fps=None):
    fps = fps or a.fps
    n = max(3, int(sh.d * fps))
    return [sh.t0 + 0.02 + (sh.d - 0.04) * j / (n - 1) for j in range(n)]


PARTS = ('head', 'hand_l', 'hand_r', 'foot_l', 'foot_r')
POSEK = ('turn', 'h_turn', 'h_nod', 'look_x', 'look_y', 'smile', 'm_open', 'lean', 'crouch', 'kneel', 'sit', 'walk_amt', 'blink_x')


def acting_amount(acts, ts):
    """How much the actors act over the shot (0 = statues): body parts move (fraction of the figure's height) + pose
    parameters change (turns, looks, mouths, sits)."""
    best = 0.0
    for act in acts:
        if not hasattr(act, 'x0'): continue
        h = max(1.0, getattr(act, 'height', 700.0))
        pts = {p: [] for p in PARTS}; pv = {p: [] for p in POSEK}
        for t in ts:
            P = act.at(t)
            for p in PARTS:
                try: pts[p].append(act.where(t, p))
                except Exception: pass
            for p in POSEK:
                pv[p].append(float(getattr(P, p, 0.0) or 0.0))
        m = 0.0
        for p, xs in pts.items():
            if len(xs) < 2: continue
            arr = np.array(xs)
            m = max(m, float(np.max(np.linalg.norm(arr - arr[0], axis=1))) / h)
        par = max([max(v) - min(v) for v in pv.values() if v] + [0.0])
        best = max(best, m * 4.0, par)
    return best


def check_shot(k):
    sh = SH[k]
    p = sh.p
    spec = F._build(sh)
    ts = sample_times(sh)
    # ---- camera
    try:
        c0 = spec.cam.at(sh.t0 + 0.01); c1 = spec.cam.at(sh.t1 - 0.01)
        mag = abs(math.log(max(1e-6, cam_mag(c1)) / max(1e-6, cam_mag(c0))))
        pan = math.hypot((c1.x + c1.px) - (c0.x + c0.px), (c1.y + c1.py) - (c0.y + c0.py))
    except Exception:
        mag, pan = 0.0, 0.0
    moving = mag > 0.10 or pan > 120.0
    if moving and sh.d > 4.2 and sh.kind in ('set', 'bust', 'ins'):
        add('WARN', k, 'CAM', 'a camera move of %.0f %% zoom / %.0f px over %.1f s (keep moves under ~4 s)' % (mag * 100, pan, sh.d))
    acts = list(getattr(sh, 'actors', []) or [])
    if sh.kind == 'set':
        amt = acting_amount(acts, ts) if acts else 0.0
        if acts and sh.d > 3.0 and (mag > 0.05 or pan > 60) and amt < 0.08:
            add('ERROR', k, 'CAM', 'only the camera moves: %.0f %% zoom over %.1f s while nobody in frame acts (acting %.3f)' % (mag * 100, sh.d, amt))
        if not acts and sh.d > 5.0 and (mag > 0.06 or pan > 80):
            add('WARN', k, 'CAM', 'an empty set held %.1f s under a moving camera (%.0f %% zoom)' % (sh.d, mag * 100))
        SAMPLE[k] = dict(amt=round(amt, 3), mag=round(mag, 3), pan=round(pan, 1))
    # ---- staging on the plan
    if sh.kind == 'set':
        sp = sh.sp
        check_anchors(k, sp)
        ppl = p.get('ppl', [])
        pos_end = {}
        for j, q in enumerate(ppl):
            who = q['who']; ident = q.get('id', who)
            kind, s0 = figure_kind(sp, q)
            room_ok = PLAN_OF.get(p['room']) == 'house'
            for t in ([sh.t0 + 0.01, (sh.t0 + sh.t1) / 2, sh.t1 - 0.01] if q.get('path') else [sh.t0 + 0.01]):
                X, Yp, Y = plan_pos(sp, q, t)
                outdoors = p['room'] in ('living', 'hall', 'up', 'june', 'bath', 'attic', 'kitchen') and (Yp > 10.05 or Yp < -0.05)
                if kind in ('stand', 'kneel', 'floor') and not q.get('sil') and q.get('check', True) and not outdoors:
                    ok, why = sp.walkable(X, Yp)
                    if not ok and (sp.info.get('floors')):
                        add('ERROR', k, 'FLOOR', '%s at plan (%.2f, %.2f): %s' % (who, X, Yp, why), t)
                    if room_ok:
                        L = floor_level(sp, X, Yp, Y)
                        tol = 0.2 if stair_Y(X, Yp) is not None else 0.12          # a ramp up the treads is within a riser
                        if L is not None and abs(L - Y) > tol:
                            add('ERROR', k, 'LEVEL', '%s feet at %.2f m, the floor there is at %.2f m (plan %.2f, %.2f)' % (who, Y, L, X, Yp), t)
            if kind == 'seat':
                at = q.get('at')
                if not (isinstance(at, str) and sp.anchors.get(at) is not None and sp.anchors[at].kind == 'seat'):
                    if not q.get('seat_ok'):
                        add('WARN', k, 'FLOOR', '%s sits at a plan point %r, not on a seat anchor (check there is a seat under them)' % (who, at))
            if kind == 'stand' and isinstance(q.get('at'), str) and sp.anchors.get(q['at']) is not None and sp.anchors[q['at']].kind == 'seat':
                add('ERROR', k, 'FLOOR', '%s STANDS on the seat anchor %r (on the furniture)' % (who, q['at']))
            pos_end[ident] = (plan_pos(sp, q, sh.t0 + 0.01), plan_pos(sp, q, sh.t1 - 0.01), bool(q.get('path')))
        # overlaps
        ids = list(pos_end)
        for i1 in range(len(ids)):
            for i2 in range(i1 + 1, len(ids)):
                for w_ in (0, 1):
                    A_, B_ = pos_end[ids[i1]][w_], pos_end[ids[i2]][w_]
                    if abs(A_[2] - B_[2]) < 0.5 and math.hypot(A_[0] - B_[0], A_[1] - B_[1]) < 0.32:
                        add('ERROR', k, 'OVERLAP', '%s and %s stand %.2f m apart on the plan (inside each other)' % (ids[i1], ids[i2], math.hypot(A_[0] - B_[0], A_[1] - B_[1])))
                        break
        sh._plan_pos = pos_end
    # ---- contact (reach misses) and props
    for act in acts:
        act.misses = []
    for t in ts:
        for act in acts:
            try: act.at(t)
            except Exception as ex_: add('ERROR', k, 'REACH', '%s pose failed at %.2f: %r' % (act.who, t, ex_), t)
    for act in acts:
        bad = [m for m in (getattr(act, 'misses', None) or []) if m[2] > 20.0 and sh.t0 <= m[0] <= sh.t1]
        if bad:
            worst = max(bad, key=lambda m: m[2])
            add('ERROR' if worst[2] > 45 else 'WARN', k, 'REACH', '%s: %d samples miss their contact target (worst %.0f design px at %.2f s, %s hand)'
                % (act.who, len(bad), worst[2], worst[0], 'left' if worst[1] > 0 else 'right'), worst[0])
    # props held by actors, props drawn by the set
    held = {}
    for act in acts:
        for t in ts:
            P = act.at(t)
            for side, pre in ((1, 'hl_'), (-1, 'hr_')):
                pr = getattr(P, pre + 'prop', None)
                if pr: held.setdefault(pr, set()).add((act.who, side))
    for pr, holders in held.items():
        if len(holders) > 1 and pr not in ('basket',):
            # two holders over a shot is fine when it changes hands (give); check the same instant
            for t in ts:
                now = [(act.who, side) for act in acts for side, pre in ((1, 'hl_'), (-1, 'hr_')) if getattr(act.at(t), pre + 'prop', None) == pr]
                if len(now) > 1:
                    add('ERROR', k, 'PROP', '%s is held by %s at the same time' % (pr, ' and '.join('%s %s hand' % (w, 'left' if s > 0 else 'right') for w, s in now)), t)
                    break
    st = p.get('set', {}) or {}
    if sh.kind == 'set':
        if st.get('egg') and any(pr.startswith('egg') for pr in held):
            add('ERROR', k, 'PROP', 'the egg is drawn by the set (egg=True) AND held by %s' % ', '.join(sorted(w for pr in held if pr.startswith('egg') for w, _ in held[pr])))
        if p['room'] == 'june' and st.get('dress', True) and 'dress_new' in held:
            add('ERROR', k, 'PROP', 'the new yellow dress is on the closet door AND in a hand')
    # PropTracks inside acts: jumps at state changes are checked through their keys
    for tr in getattr(sh, '_tracks', []) or []:
        prev = None
        for (tk, stt) in tr.keys[1:]:
            if not (sh.t0 - 0.5 <= tk <= sh.t1): continue
            try:
                before = tr.pos(tk - 1.0 / 60); after = tr.pos(tk + 1.0 / 60)
            except Exception:
                continue
            if before[0] > -1e5 and after[0] > -1e5:
                d = math.hypot(after[0] - before[0], after[1] - before[1])
                if d > 40: add('ERROR', k, 'PROP', '%s jumps %.0f design px when it changes state (%s) at %.2f s' % (tr.name, d, stt[0], tk), tk)
    # ---- length
    if sh.d < 0.6 and sh.kind not in ('black',) and not p.get('flash'):
        add('WARN', k, 'LEN', 'a %.2f s shot (too short to read?)' % sh.d)
    lim = 10.5 if sh.kind in ('rule', 'card', 'pause') else 7.0
    if sh.d > lim and not p.get('long_ok'):
        add('WARN', k, 'LEN', 'a %.2f s %s shot (long: does it keep acting?)' % (sh.d, sh.kind))


# ---------------------------------------------------------------------------------------------------- across cuts
def check_cuts():
    last = {}                           # ident -> (shot k, t1, plan, (X, Yp, Y), era)
    for k in range(N):
        sh = SH[k]
        pos = getattr(sh, '_plan_pos', None)
        if sh.kind == 'set' and pos is not None:
            plan = PLAN_OF.get(sh.p['room'])
            era = sh.p.get('era', 'now')
            for ident, (p0, p1, walks) in pos.items():
                if ident in last:
                    k0, t1, plan0, pp, era0 = last[ident]
                    gap = sh.t0 - t1
                    entering = any(q.get('enter') and q.get('id', q['who']) == ident for q in sh.p.get('ppl', []))
                    if plan0 == plan and era0 == era and gap < 8.0 and era not in ('recall',) and not sh.p.get('cut') in ('static', 'white') \
                            and not entering and not sh.p.get('montage') and sh.p.get('room') != 'parade':
                        d = math.hypot(p0[0] - pp[0], p0[1] - pp[1])
                        dY = abs(p0[2] - pp[2])
                        if (d > 0.8 or dY > 0.5) and k in KS:
                            sev = 'ERROR' if gap < 0.05 else 'WARN'
                            add(sev, k, 'CUTPOS', '%s jumps %.2f m (%.2f m up/down) across the cut from shot %d (plan (%.2f, %.2f) -> (%.2f, %.2f), %.1f s between)'
                                % (ident, d, dY, k0, pp[0], pp[1], p0[0], p0[1], gap))
                last[ident] = (k, sh.t1, plan, p1, era)
        # a long stretch of other places resets the memory
        if sh.kind == 'set':
            plan = PLAN_OF.get(sh.p['room'])
            for ident in list(last):
                if last[ident][2] != plan and sh.t0 - last[ident][1] > 3.0: last.pop(ident, None)


# ---------------------------------------------------------------------------------------------------- the story's states
def T(i): return F.t(i)


def states():
    t_curt = F.w(69, 'close') + 1.8                       # the curtains shut at 11:07
    t_smash = F.w(236, 'explodes')
    t_crash = F.w(237, 'crashes')
    t_flap0 = F.w(164, 'creaks') + 1.3
    t_flap1 = F.t(192) + 0.3
    t_lock0 = F.t(243) + 0.2
    t_key = F.t(297) + 0.25                               # the lock turns by itself (then the key, then the door opens)
    t_dawn = F.t(300) - 0.2
    t_swap = F.t(359)
    for k in KS:
        sh = SH[k]; p = sh.p; st = p.get('set', {}) or {}
        era = p.get('era', 'now')
        room = p.get('room') or ((p.get('bg') or [None])[0])
        live = era in ('now', None) and sh.t0 < 993.0
        if not live: continue
        if room == 'living' and sh.t0 > t_curt:
            v = st.get('curtains', 1.0)
            if not callable(v) and v > 0.2 and not p.get('curtains_fn'):
                add('ERROR', k, 'STATE', 'living room: the front curtains are open (curtains=%s) after the narrator shut them at 11:07' % v)
        if room == 'yard' and 187.0 < sh.t0 < 993.0:
            v = st.get('back_light', 0.0)
            if not callable(v) and not isinstance(v, dict) and v > 0.2 and st.get('tod', 'night') == 'night':
                add('ERROR', k, 'STATE', "yard: Grandma's porch light is on (Mom switches it off every Easter)")
        if room == 'hall' and t_flap0 < sh.t0 < t_flap1 and p.get('view') in ('door', 'slot', 'in') or (sh.kind == 'bust' and room == 'hall' and t_flap0 < sh.t0 < t_flap1):
            v = st.get('flap', 0.0)
            if not callable(v) and v < 0.5:
                add('WARN' if sh.kind == 'bust' else 'ERROR', k, 'STATE', 'the mail-slot flap is shut (flap=%s) between 1:40 and Mom shutting it' % v)
        if room == 'kitchen' and sh.t0 > t_smash + 0.5 and sh.t0 < t_dawn + 200:
            if not (st.get('smash') or st.get('smash_t')) and p.get('view') in ('back', 'window', 'table', 'fridge'):
                add('ERROR', k, 'STATE', 'kitchen: the window is whole after it exploded at 4:30')
        if room == 'kitchen' and sh.t0 > t_crash + 0.5 and sh.t0 < t_dawn + 200:
            if not (st.get('back_door') or st.get('crash_t')) and p.get('view') in ('door', 'back'):
                add('WARN', k, 'STATE', 'kitchen: the back door is shut after it crashed open at 4:30')
        if room == 'bath' and t_lock0 < sh.t0 < t_key:
            v = st.get('lock', 1.0)
            if not callable(v) and v < 0.5:
                add('ERROR', k, 'STATE', 'the bathroom door is unlocked before the key turns')
            if st.get('door', 0.0) and not callable(st.get('door')):
                add('ERROR', k, 'STATE', 'the bathroom door is open before 6:12')
        if room == 'bath' and sh.t0 > t_key + 1.0 and sh.t0 < t_swap:
            v = st.get('door', 0.0)
            if not callable(v) and v < 20:
                add('WARN', k, 'STATE', 'the bathroom door is shut after Mom opened it')
        if room == 'up' and t_lock0 < sh.t0 < t_key:
            v = st.get('bath_door', 0.0)
            if not callable(v) and v > 5:
                add('ERROR', k, 'STATE', 'upstairs: the bathroom door stands open (%s) while the kids are locked in' % v)
        if room in ('up', 'hall') and sh.t0 > t_key and sh.t0 < t_swap + 60 and p.get('view') in ('west', 'hall', 'bottom', 'foot') and era == 'now':
            if sh.t0 > t_dawn and not st.get('wrecked') and room == 'up':
                add('WARN', k, 'STATE', 'upstairs at dawn: the corridor is not wrecked (wrecked=1.0)')
        # Mom's arms
        if sh.t0 > t_dawn and sh.t0 < 993.0:
            for act in (getattr(sh, 'actors', []) or []):
                if act.who == 'mom':
                    P = act.at(sh.t0 + 0.1)
                    if float(getattr(P, 'scratch', 0.0) or 0.0) < 0.5:
                        add('ERROR', k, 'STATE', "Mom's arms are clean after the fight (scratch=1.0 from dawn)")


# ---------------------------------------------------------------------------------------------------- lips
def check_lips():
    rows = FM.lip_check(F)
    for r in rows:
        if r['shot'] not in KS: continue
        bad = r['move_off'] > 0.35 or (r['lines'] and r['move_on'] < 0.4)
        if not bad: continue
        sh = SH[r['shot']]
        why = None
        for (chk, pred, reason) in ALLOW:
            if chk == 'LIP':
                try:
                    if pred(sh, r['who']): why = reason
                except Exception:
                    pass
        if why:
            add('INFO', r['shot'], 'LIP', '%s: on %.2f off %.2f (allowed: %s)' % (r['who'], r['move_on'], r['move_off'], why))
        else:
            add('ERROR', r['shot'], 'LIP', '%s: mouth moves %.2f/s on its lines, %.2f/s off them (lips only on character lines)' % (r['who'], r['move_on'], r['move_off']))


# ---------------------------------------------------------------------------------------------------- run
for k in KS:
    try:
        check_shot(k)
    except Exception as ex_:
        import traceback; traceback.print_exc(limit=-3)
        add('ERROR', k, 'BUILD', 'the check failed: %r' % ex_)
    F._built.clear()
check_cuts()
states()
if not a.no_lip: check_lips()

ds = np.array([s.d for s in SH])
summary = dict(shots=N, median=round(float(np.median(ds)), 2), p10=round(float(np.percentile(ds, 10)), 2), p90=round(float(np.percentile(ds, 90)), 2),
               cuts_per_min=round(N / F.duration * 60, 1), duration=round(F.duration, 2))
if not (2.0 <= summary['median'] <= 3.0): add('WARN', None if not KS else KS[0], 'LEN', 'median shot %.2f s (target 2-3 s)' % summary['median'])
order = {'ERROR': 0, 'WARN': 1, 'INFO': 2}
issues.sort(key=lambda d: (order[d['sev']], d['check'], d['shot'] if d['shot'] is not None else -1))
cnt = {s: sum(1 for d in issues if d['sev'] == s) for s in order}
by = {}
for d in issues: by.setdefault((d['sev'], d['check']), 0); by[(d['sev'], d['check'])] += 1
if not a.quiet:
    for d in issues:
        if d['sev'] == 'INFO': continue
        print('%-5s %-7s #%-4s %7s  %s' % (d['sev'], d['check'], d['shot'], ('%.2f' % d['t0']) if d['t0'] is not None else '', d['msg']))
print('summary: %s' % json.dumps(summary))
print('by check: %s' % ', '.join('%s %s %d' % (s, c, n) for (s, c), n in sorted(by.items(), key=lambda x: (order[x[0][0]], x[0][1]))))
print('ERROR %d  WARN %d  INFO %d  (%d shots checked in %.0f s)' % (cnt['ERROR'], cnt['WARN'], cnt['INFO'], len(KS), time.time() - t_start))
os.makedirs(os.path.dirname(a.json), exist_ok=True)
json.dump(dict(summary=summary, counts=cnt, issues=issues, camera=SAMPLE), open(a.json, 'w'), indent=1)
sys.exit(1 if cnt['ERROR'] else 0)
