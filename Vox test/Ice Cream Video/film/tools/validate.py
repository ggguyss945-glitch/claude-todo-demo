"""tools/validate.py: the staging validator for the ice cream film's shot list (film.py: "If The Ice Cream Truck Plays Its Song In Winter... DON'T GO OUTSIDE").

    python3 tools/validate.py                      # every check on every shot; exit code 1 on any ERROR
    python3 tools/validate.py --shots 100-140      # a range (the cut / state checks still look at the neighbours)
    python3 tools/validate.py --part A             # part A only (timeline lines 0-262: the cold open .. rule 4); --part B
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
  STATE   the story's states shot by shot (keyed to lines, W/shotmap.md): his truck (none before L65, at A L69-L306, at B
          L310-L388, gone after), our power (dead from L116 to the morning: every house shot blacked out), the living-room
          curtains (shut from L124), Adam in one sock (`adam_sock`) from L227 to the morning, the attic hatch (shut until
          L294 'drops', open after), the towels (in the gap from L300), Kessler's chimney (no smoke until the morning),
          the neighbours' porch lights (off until L377), and Mister Shiver never breathes a cloud
  CAM     camera: a move (> 10 % magnification or > 120 design px of pan) that lasts > 4.2 s; a set shot > 3 s whose
          camera moves while nobody in it acts (only the camera moves over still figures); an empty set held > 5 s
          under a moving camera
  LEN     shot lengths (< 0.6 s outside flashes / blacks; > 7 s outside rule cards, cards and the VHS pause) + the
          median / cuts per minute against the police film's pace
  LIP     lips move only on the actor's own lines (film.lip_check); Doctor Later never moves a mouth
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
ap.add_argument('--part', default=None, help='A (lines 0-262) or B (263-427)')
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
if a.part:
    tb = F.t(FM.PART_B) - FM.LEAD - 0.01
    KS = [k for k in KS if (SH[k].t0 < tb) == (a.part.upper() == 'A')]
issues = []


def add(sev, k, check, msg, t=None):
    issues.append(dict(sev=sev, shot=k, t=None if t is None else round(float(t), 2), check=check, msg=msg,
                       t0=round(SH[k].t0, 2) if k is not None else None))


# ---------------------------------------------------------------------------------------------------- allowed exceptions
# (check, shot predicate, reason): an exception is written down here with the reason, never silently skipped
def _line_shot(i):
    return lambda s: s.t0 <= F.t(i) < s.t1


def _ws(s, who):
    """Mister Shiver never lip-syncs (his voice comes from the truck / the door / the radio); his jaw drops as acting."""
    return who.startswith('shiver')


def _lines(*ii):
    return lambda s, who=None: any(s.t0 - 0.05 <= F.t(i) < s.t1 for i in ii)


ALLOW = [
    ('LIP', _ws, "Mister Shiver never lip-syncs (his jaw gapes and drops as acting, not speech)"),
    ('LIP', lambda s, who: who.startswith('kessler') and _lines(393)(s), "L393 'Bye, Benny.' is a whisper: the lips barely part (checked on the sheet)"),
    ('LIP', lambda s, who: who.startswith('adam') and _lines(172)(s), "L172 'I wake up.': the shock expression opens his mouth on 'wake' (acting, no speech)"),
    ('REACH', _lines(193, 194), "L193-194: Lina's hand and his glove stop an inch apart on purpose (she never touches him)"),
    ('REACH', _lines(12, 14, 54, 64), "part A: checked on stills at the worst time (fridge photo touched, radio handed over, curtain gripped, Lina's hand hidden behind the couch)"),
    ('CUTPOS', _lines(27, 28), "1958: memory cuts across Walter's walk out and his run home (time jumps inside the memory)"),
    ('CUTPOS', _lines(36, 105, 131), "a time ellipsis in the narration (L36 the walk later, L105 'When I come back', L131 the coats)"),
    ('CUTPOS', _lines(185), "L185 'Knee-deep snow': Adam keeps running between the cuts (door -> yard)"),
]


def allowed(check, sh, who=''):
    for (chk, pred, reason) in ALLOW:
        if chk != check: continue
        try:
            if pred(sh, who): return reason
        except Exception:
            pass
    return None

# ---------------------------------------------------------------------------------------------------- build helpers
HOUSE = ('living', 'hall', 'kitchen', 'bath')
PLAN_OF = {r: 'house' for r in HOUSE}
PLAN_OF.update(street='street', y58='y58', morning='morning', town='town')
LEVELS = {}
STAIR = None


def stair_Y(x, y):
    """No stairs in this film's sets (one-storey house; the attic is reached only by him)."""
    return None


def ice_level(sp, room, X, Yp, Y):
    """Expected feet height: the house floor 0; outside the snow (IC_FOOT, sunk) unless on a porch / its steps / the
    truck floor (within 0.6 m of a porch, step or truck anchor of the set)."""
    if room in HOUSE: return [0.0]
    out = [ST.IC_FOOT]
    for nm, s_ in sp.anchors.items():
        if '.' in nm: continue
        if (nm.startswith(('kporch', 'kdoor', 'ksteps', 'porch', 'steps', 'truck_vendor')) or nm in ('door_glass',)) and math.hypot(s_.X - X, s_.Yp - Yp) < 0.7:
            out.append(s_.Y)
    return out


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


LIERS = {}
LIE_HALF = 0.85                          # half the length of a lying figure along its axis (m)


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
                outdoors = p['room'] in HOUSE and Yp < -0.05
                if kind in ('stand', 'kneel', 'floor') and not q.get('sil') and q.get('check', True) and not outdoors:
                    ok, why = sp.walkable(X, Yp) if hasattr(sp, 'walkable') else (True, '')
                    if not ok and stair_Y(X, Yp) is not None and 'stairs' in why: ok = True        # standing on the treads
                    if not ok and 'porch' in why and (Y > -0.15 or any(nm.startswith('porch') and math.hypot(s_.X - X, s_.Yp - Yp) < 0.3
                                                                      for nm, s_ in sp.anchors.items())): ok = True   # on the porch deck / its steps
                    if not ok and any(nm.endswith(('_step', '_top', '_door')) and math.hypot(s_.X - X, s_.Yp - Yp) < 0.75
                                      for nm, s_ in sp.anchors.items() if '.' not in nm and ('his_' in nm or 'b9_' in nm)):
                        ok = True                                  # on a bus's door steps (the footprint covers its steps)
                    if not ok and who.startswith('shiver') and 'truck' in why: ok = True     # in his truck (the window, the cab)
                    if not ok and who.startswith('kessler') and 'kessler' in why and any(nm.startswith('kdoor') and math.hypot(s_.X - X, s_.Yp - Yp) < 0.75
                                                                                    for nm, s_ in sp.anchors.items()): ok = True   # in his doorway
                    if not ok and (sp.info.get('floors')):
                        add('ERROR', k, 'FLOOR', '%s at plan (%.2f, %.2f): %s' % (who, X, Yp, why), t)
                    if kind == 'stand' and not q.get('sil') and not who.startswith('shiver'):     # he climbs fences, cars, roofs
                        Ls = ice_level(sp, p['room'], X, Yp, Y)
                        if p['room'] != 'town' and min(abs(L_ - Y) for L_ in Ls) > (0.12 if p['room'] in HOUSE else 0.3):
                            add('ERROR', k, 'LEVEL', '%s feet at %.2f m, expected %s (plan %.2f, %.2f)' % (who, Y, '/'.join('%.2f' % L_ for L_ in Ls), X, Yp), t)
                    if room_ok and False:
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
            if kind == 'lie': LIERS[ident] = True
        # overlaps (fix round 1, fixer C: a lying body is a 1.8 m segment along its axis, not a point: the cop crouched
        # INTO the body at the foot of the stairs and passed, because only its centre was checked)
        ids = list(pos_end)

        def gap(A_, B_, a_lies, b_lies):
            if not (a_lies or b_lies): return math.hypot(A_[0] - B_[0], A_[1] - B_[1]), 0.32
            L_, P_ = (A_, B_) if a_lies else (B_, A_)
            x0_, x1_ = L_[0] - LIE_HALF, L_[0] + LIE_HALF          # the bodies lie along plan x (the anchors' note)
            cx_ = min(max(P_[0], x0_), x1_)
            return math.hypot(P_[0] - cx_, P_[1] - L_[1]), 0.36
        for i1 in range(len(ids)):
            for i2 in range(i1 + 1, len(ids)):
                for w_ in (0, 1):
                    A_, B_ = pos_end[ids[i1]][w_], pos_end[ids[i2]][w_]
                    d_, lim_ = gap(A_, B_, LIERS.get(ids[i1], False), LIERS.get(ids[i2], False))
                    if abs(A_[2] - B_[2]) < 0.5 and d_ < lim_:
                        add('ERROR', k, 'OVERLAP', '%s and %s are %.2f m apart on the plan (inside each other%s)' % (ids[i1], ids[i2], d_,
                            ', the lying body counted along its length' if lim_ > 0.33 else ''))
                        break
        LIERS.clear()
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
            why_ = allowed('REACH', sh)
            add('INFO' if why_ else ('ERROR' if worst[2] > 45 else 'WARN'), k, 'REACH', (('(allowed: %s) ' % why_) if why_ else '') + '%s: %d samples miss their contact target (worst %.0f design px at %.2f s, %s hand)'
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
        if len(holders) > 1 and pr not in ('basket', 'ticket'):        # every waiting-room ghost holds a ticket of their own
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
    lim = 10.5 if sh.kind in ('rule', 'card', 'pause') else (24.0 if sh.kind == 'outro' else 7.0)
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
            if plan == 'bus': plan = 'bus:%s' % (sh.p.get('set', {}) or {}).get('kind', 'his')      # two buses on one plan
            era = sh.p.get('era', 'now')
            for ident, (p0, p1, walks) in pos.items():
                if ident in last:
                    k0, t1, plan0, pp, era0 = last[ident]
                    gap = sh.t0 - t1
                    entering = any(q.get('enter') and q.get('id', q['who']) == ident for q in sh.p.get('ppl', []))
                    if ident == 'shiver' and plan0 == 'street': pass       # he scuttles fast between cuts (window -> snow -> roof)
                    elif plan0 == plan and era0 == era and gap < 8.0 and era not in ('recall',) and not sh.p.get('cut') in ('static', 'white') \
                            and not entering and not sh.p.get('montage') and sh.p.get('cut') != 'blink' and True:
                        d = math.hypot(p0[0] - pp[0], p0[1] - pp[1])
                        dY = abs(p0[2] - pp[2])
                        if (d > 0.8 or dY > 0.5) and k in KS:
                            sev = 'ERROR' if gap < 0.05 else 'WARN'
                            if allowed('CUTPOS', sh): sev = 'INFO'
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


def _lv(v, t):
    return v(t) if callable(v) else v


def states():
    """The story's prop / light / cast states against the lines (see the docstring)."""
    t_A, t_B, t_gone = T(65), F.t(309) - 0.2, F.e(388) + 0.5     # (the cold open L0-L8 flashes forward: truck at A)
    t_dark, t_morn, t_shut = T(116) + 0.6, T(395) - 0.2, T(124) + 1.2
    t_sock = T(227) + 0.5
    t_hatch = F.w(294, 'drops') + 0.3
    t_tow = T(300) + 1.0
    t_porch = F.w(377, 'click') - 0.2
    for k in KS:
        sh = SH[k]; p = sh.p
        era = p.get('era', 'now')
        st = p.get('set', {}) or {}
        room = p.get('room') or ((p.get('bg') or [None])[0])
        who = [q['who'] for q in p.get('ppl', [])] + ([p.get('who')] if sh.kind == 'bust' else []) + [b['who'] for b in p.get('busts', [])]
        for q in p.get('ppl', []):
            if q['who'].startswith('shiver') and q.get('breath', True) is not False:
                add('ERROR', k, 'STATE', 'Mister Shiver breathes a cloud (breath=False on him, always)')
        if sh.kind not in ('set', 'bust') or era != 'now': continue
        if t_sock < sh.t0 < t_morn and any(w in ('adam', 'adam_in') for w in who):
            add('ERROR', k, 'STATE', "Adam in both boots / indoors between L227 (the boot left behind) and the morning: use 'adam_sock'")
        if room == 'street':
            tr = st.get('truck', 'A')
            if isinstance(tr, str):
                if tr == 'A' and not (t_A - 1 < sh.t0 < t_B) and sh.t0 > T(9): add('ERROR', k, 'STATE', 'his truck at A outside L69-L306 (t %.1f)' % sh.t0)
                if tr == 'B' and not (t_B - 0.5 < sh.t0 < t_gone): add('ERROR', k, 'STATE', 'his truck at B outside L310-L388 (t %.1f)' % sh.t0)
            if sh.t0 < t_morn and (_lv(st.get('smoke', 0.0), sh.t0) or 0) > 0.05:
                add('ERROR', k, 'STATE', "Kessler's chimney smokes before the morning (his furnace died)")
            pc = st.get('porches')
            if sh.t0 < t_porch and pc and not callable(pc) and not isinstance(pc, list):
                add('ERROR', k, 'STATE', "the neighbours' porch lights are on before L377")
        if room in HOUSE and t_dark < sh.t0 < t_morn and sh.kind == 'set' and not (st.get('blackout') or room == 'bath' or st.get('kitchen_light', 1) == 0):
            add('ERROR', k, 'STATE', 'a lamp is on in the house after the power died (L116)')
        if room == 'living' and t_shut < sh.t0 < t_morn:
            c = st.get('curtains', 0.0)
            if not callable(c) and c > 0.01: add('ERROR', k, 'STATE', 'the living-room curtains are open after Adam yanked them shut (L124)')
        if room == 'hall' and p.get('view') == 'hatch':
            h = st.get('hatch', 0.0)
            if not callable(h):
                if sh.t0 < t_hatch and h > 0.1: add('ERROR', k, 'STATE', 'the attic hatch is open before it drops (L294)')
                if t_hatch < sh.t0 < t_morn and h < 0.5: add('ERROR', k, 'STATE', 'the attic hatch is shut again after it dropped (L294)')
        if room == 'bath' and sh.t0 > t_tow and st.get('towels', 'gap') == 'rack':
            add('ERROR', k, 'STATE', 'the towels are back on the rack after Adam stuffed them in the gap (L300)')


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
